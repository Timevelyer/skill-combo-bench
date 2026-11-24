"""Adapter verification tool: three-state verdicts, evidence shape, and masking."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from tools.verify_adapter import (
    EXIT_CODES,
    FAILED,
    NOT_RUN,
    SMOKE_TASK,
    VERIFIED,
    command_fingerprint,
    main,
    verify,
    write_evidence,
)

PY = sys.executable
MISSING_EXECUTABLE = "definitely-not-a-real-executable-9f3c"


def _json_cli() -> list[str]:
    return [PY, "-c", "import json; print(json.dumps({'status': 'ok'}))"]


class VerdictTests(unittest.TestCase):
    def test_exit_zero_with_parseable_output_is_verified(self) -> None:
        evidence = verify("generic_cli", _json_cli(), timeout_seconds=20)
        self.assertEqual(evidence["verification_status"], VERIFIED)
        self.assertEqual(evidence["reason"], "EXIT_ZERO_WITH_PARSEABLE_OUTPUT")
        self.assertEqual(evidence["run"]["return_code"], 0)
        self.assertTrue(evidence["run"]["output_parseable"])

    def test_nonzero_exit_is_failed(self) -> None:
        evidence = verify("generic_cli", [PY, "-c", "import sys; sys.exit(3)"], timeout_seconds=20)
        self.assertEqual(evidence["verification_status"], FAILED)
        self.assertEqual(evidence["run"]["return_code"], 3)

    def test_empty_output_is_failed(self) -> None:
        evidence = verify("generic_cli", [PY, "-c", "pass"], timeout_seconds=20)
        self.assertEqual(evidence["verification_status"], FAILED)
        self.assertEqual(evidence["reason"], "EMPTY_OUTPUT")

    def test_non_json_output_is_failed(self) -> None:
        evidence = verify("generic_cli", [PY, "-c", "print('plain text only')"], timeout_seconds=20)
        self.assertEqual(evidence["verification_status"], FAILED)
        self.assertEqual(evidence["reason"], "UNPARSEABLE_OUTPUT")

    def test_missing_executable_is_not_run(self) -> None:
        evidence = verify("generic_cli", [MISSING_EXECUTABLE, "--help"], timeout_seconds=10)
        self.assertEqual(evidence["verification_status"], NOT_RUN)
        self.assertEqual(evidence["reason"], "EXECUTABLE_NOT_FOUND")
        self.assertIsNone(evidence["run"])

    def test_no_command_is_not_run(self) -> None:
        evidence = verify("codex", [], timeout_seconds=10)
        self.assertEqual(evidence["verification_status"], NOT_RUN)
        self.assertEqual(evidence["reason"], "COMMAND_NOT_CONFIGURED")

    def test_vendor_adapter_uses_shared_registry(self) -> None:
        evidence = verify("codex", _json_cli(), timeout_seconds=20)
        self.assertEqual(evidence["adapter_id"], "codex")
        self.assertEqual(evidence["verification_status"], VERIFIED)

    def test_health_only_never_claims_verified(self) -> None:
        evidence = verify("generic_cli", _json_cli(), timeout_seconds=20, health_only=True)
        self.assertEqual(evidence["verification_status"], NOT_RUN)
        self.assertEqual(evidence["reason"], "HEALTH_CHECK_ONLY")
        self.assertEqual(evidence["health_check"]["status"], "PASS")
        self.assertIsNone(evidence["run"])

    def test_unknown_adapter_is_not_run(self) -> None:
        evidence = verify("no_such_agent", _json_cli(), timeout_seconds=10)
        self.assertEqual(evidence["verification_status"], NOT_RUN)
        self.assertIn("ADAPTER_UNAVAILABLE", evidence["reason"])


class EvidenceTests(unittest.TestCase):
    def test_evidence_records_scope_and_hashes_command(self) -> None:
        command = _json_cli()
        evidence = verify("generic_cli", command, timeout_seconds=20)
        self.assertEqual(evidence["command"]["template_sha256"], command_fingerprint(command))
        self.assertEqual(evidence["command"]["argument_count"], len(command))
        self.assertNotIn(command[-1], json.dumps(evidence["command"], ensure_ascii=False))
        self.assertTrue(evidence["does_not_establish"])
        self.assertIn("schema_version", evidence)
        self.assertEqual(SMOKE_TASK["assertions"], [])

    def test_evidence_file_is_written(self) -> None:
        evidence = verify("generic_cli", _json_cli(), timeout_seconds=20)
        with tempfile.TemporaryDirectory() as tmp:
            path = write_evidence(evidence, Path(tmp) / "nested" / "adapter_verification.json")
            self.assertTrue(path.exists())
            reloaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(reloaded["verification_status"], VERIFIED)

    def test_credential_shaped_output_is_masked(self) -> None:
        command = [PY, "-c", "print('Authorization: Bearer abcdefgh12345678'); print('{\"status\":\"ok\"}')"]
        evidence = verify("generic_cli", command, timeout_seconds=20)
        excerpt = evidence["run"]["stdout_excerpt"]
        self.assertNotIn("abcdefgh12345678", excerpt)
        self.assertIn("<MASKED>", excerpt)

    def test_cli_exit_codes_match_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp) / "evidence.json")
            ok = ["--agent", "generic_cli", "--output", out, "--",
                  PY, "-c", "import json; print(json.dumps({'status':'ok'}))"]
            bad = ["--agent", "generic_cli", "--output", out, "--", PY, "-c", "import sys; sys.exit(1)"]
            missing = ["--agent", "generic_cli", "--output", out, "--", MISSING_EXECUTABLE]
            self.assertEqual(main(ok), 0)
            self.assertEqual(main(bad), 1)
            self.assertEqual(main(missing), 2)
        self.assertEqual(EXIT_CODES, {VERIFIED: 0, FAILED: 1, NOT_RUN: 2})

    def test_cli_accepts_command_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp) / "evidence.json")
            code = "import json; print(json.dumps({'status':'ok'}))"
            argv = ["--agent", "generic_cli", "--output", out, "--command-json", json.dumps([PY, "-c", code])]
            self.assertEqual(main(argv), 0)

    def test_cli_rejects_both_command_forms(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp) / "evidence.json")
            argv = ["--agent", "generic_cli", "--output", out, "--command-json", json.dumps([PY, "-c", "pass"]), "--", PY]
            self.assertEqual(main(argv), 2)


if __name__ == "__main__":
    unittest.main()

# FILE END: tests/unit/test_adapter_verification.py
