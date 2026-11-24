"""Verify one external agent adapter against one real command, and keep the evidence.

This tool exists because every vendor adapter ships as ``NOT_VERIFIED``: the framework
must never claim an adapter works without an observed run. The tool runs a single minimal
smoke task through the configured argument vector, records exactly what happened, and
writes ``adapter_verification.json``.

The verdict is deliberately narrow:

``VERIFIED``
    The process exited 0 and produced non-empty, parseable output. This proves the wiring
    worked once, on this machine, with this command.
``FAILED``
    The process ran but exited non-zero, timed out, was cancelled, or produced nothing.
``NOT_RUN``
    Nothing was exercised: no command was configured, or the executable was not found.

A ``VERIFIED`` verdict is evidence about a command, not a claim about model quality,
output correctness, or support for other environments.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from adapters.agent import ADAPTER_CLASS_PATHS

VERIFIED = "VERIFIED"
FAILED = "FAILED"
NOT_RUN = "NOT_RUN"

EXIT_CODES = {VERIFIED: 0, FAILED: 1, NOT_RUN: 2}

SCHEMA_VERSION = "1.0.0"

# Best-effort masking of credential-shaped strings before any excerpt is written to disk.
# It is not a guarantee; output is also truncated, and users should not point adapters at
# secrets in the first place.
_CREDENTIAL_PATTERNS = (
    re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\b(sk-|ghp_|gho_|ghu_|ghs_|xox[baprs]-|AKIA)[A-Za-z0-9_-]{8,}"),
)

EXCERPT_LIMIT = 800

# A single-turn probe with no tools and no state: the cheapest possible proof that the
# adapter can build an argument vector, spawn the process, and read something back.
SMOKE_TASK: dict[str, Any] = {
    "task_id": "adapter-smoke",
    "version": "1.0.0",
    "description": "Minimal single-turn probe used only to verify adapter wiring.",
    "modalities": ["text"],
    "metadata": {"synthetic": True, "result_classification": "NOT_RUN"},
    "turns": [
        {
            "turn_index": 1,
            "input": 'Reply with the JSON object {"status":"ok"} and nothing else.',
            "mock_output": "",
            "tool_calls": [],
            "state_writes": {},
            "state_probes": [],
        }
    ],
    "assertions": [],
}


def _mask(text: str) -> str:
    """Mask credential-shaped substrings and truncate to the excerpt limit."""
    masked = text
    for pattern in _CREDENTIAL_PATTERNS:
        masked = pattern.sub(lambda match: f"{match.group(1) if match.groups() else ''}<MASKED>", masked)
    if len(masked) > EXCERPT_LIMIT:
        return masked[:EXCERPT_LIMIT] + f"...[{len(masked) - EXCERPT_LIMIT} chars truncated]"
    return masked


def command_fingerprint(command: Sequence[str]) -> str:
    """Hash the argument template so evidence is reproducible without storing the argv."""
    digest = hashlib.sha256("\x00".join(command).encode("utf-8")).hexdigest()
    return digest


def build_adapter(agent_type: str, command: Sequence[str], timeout_seconds: float, workspace: str | None = None):
    """Instantiate the configured adapter class and apply the supplied command."""
    key = agent_type.lower().replace("-", "_")
    if key not in ADAPTER_CLASS_PATHS:
        raise ValueError(f"Unknown agent adapter: {agent_type}")
    module_name, class_name = ADAPTER_CLASS_PATHS[key]
    module = __import__(module_name, fromlist=[class_name])
    adapter = getattr(module, class_name)()
    config: dict[str, Any] = {"command": list(command), "timeout_seconds": timeout_seconds}
    if workspace:
        config["workspace"] = workspace
    adapter.initialize(config)
    return adapter


def verify(
    agent_type: str,
    command: Sequence[str],
    timeout_seconds: float = 60.0,
    workspace: str | None = None,
    health_only: bool = False,
) -> dict[str, Any]:
    """Run the smoke task and return an evidence record; never raises for adapter failure."""
    started_at = datetime.now(timezone.utc).isoformat()
    evidence: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": started_at,
        "adapter_type": agent_type,
        "adapter_id": None,
        "verification_status": NOT_RUN,
        "reason": None,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "command": {
            "executable": list(command)[0] if command else None,
            "argument_count": len(command),
            "template_sha256": command_fingerprint(command) if command else None,
            "note": "The argument template is hashed rather than stored, so credentials in it are not duplicated to disk.",
        },
        "timeout_seconds": timeout_seconds,
        "health_check": None,
        "run": None,
        "verdict_scope": "One command, one machine, one smoke task. Does not establish output correctness, model quality, or support for other environments.",
        "does_not_establish": [
            "Model output quality or task correctness",
            "Token usage or cost (external CLIs do not report them here)",
            "That the adapter works with other flags, tasks, or environments",
        ],
    }

    if not command:
        evidence["reason"] = "COMMAND_NOT_CONFIGURED"
        return evidence

    try:
        adapter = build_adapter(agent_type, command, timeout_seconds, workspace)
    except (ImportError, AttributeError, ValueError) as exc:
        evidence["reason"] = f"ADAPTER_UNAVAILABLE: {exc}"
        return evidence

    evidence["adapter_id"] = getattr(adapter, "adapter_id", agent_type)
    health = adapter.health_check()
    evidence["health_check"] = {
        "status": health.get("status"),
        "executable": health.get("executable"),
        "executable_path": health.get("executable_path"),
        "scope": health.get("scope"),
    }
    if health.get("status") != "PASS":
        evidence["reason"] = "EXECUTABLE_NOT_FOUND"
        return evidence
    if health_only:
        evidence["reason"] = "HEALTH_CHECK_ONLY"
        return evidence

    try:
        result = adapter.run(dict(SMOKE_TASK), {"run_id": "adapter-smoke", "workspace": workspace})
    except Exception as exc:  # noqa: BLE001 - an unexpected adapter crash is itself the finding
        evidence["verification_status"] = FAILED
        evidence["reason"] = f"ADAPTER_RAISED: {type(exc).__name__}: {exc}"
        return evidence
    finally:
        try:
            adapter.close()
        except Exception:  # noqa: BLE001 - cleanup failure must not mask the verdict
            pass

    status = result.get("status")
    output = result.get("output")
    stdout = result.get("stdout") or ""
    output_present = bool(output) if not isinstance(output, str) else bool(output.strip())
    parseable = _looks_parseable(output, stdout)

    evidence["run"] = {
        "status": status,
        "failure_class": result.get("failure_class"),
        "return_code": result.get("return_code"),
        "latency_ms": result.get("latency_ms"),
        "parsed_event_count": len(result.get("events") or []),
        "output_present": output_present,
        "output_parseable": parseable,
        "stdout_excerpt": _mask(stdout),
        "stderr_excerpt": _mask(result.get("stderr") or ""),
        "error": result.get("error"),
    }

    if status == "SUCCESS" and output_present and parseable:
        evidence["verification_status"] = VERIFIED
        evidence["reason"] = "EXIT_ZERO_WITH_PARSEABLE_OUTPUT"
    elif status == "SUCCESS" and not output_present:
        evidence["verification_status"] = FAILED
        evidence["reason"] = "EMPTY_OUTPUT"
    elif status == "SUCCESS":
        evidence["verification_status"] = FAILED
        evidence["reason"] = "UNPARSEABLE_OUTPUT"
    elif status == "TIMED_OUT":
        evidence["verification_status"] = FAILED
        evidence["reason"] = "TIMEOUT"
    else:
        evidence["verification_status"] = FAILED
        evidence["reason"] = f"RUN_ENDED_{status}"
    return evidence


def _looks_parseable(output: Any, stdout: str) -> bool:
    """Accept structured output or at least one JSON object on stdout."""
    if isinstance(output, (dict, list)):
        return bool(output)
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            json.loads(stripped)
            return True
        except json.JSONDecodeError:
            continue
    return False


def write_evidence(evidence: dict[str, Any], output_path: str | Path) -> Path:
    """Persist the evidence record, creating parent directories as needed."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verify_adapter",
        description=(
            "Run one smoke task through an external agent adapter and record the evidence. "
            "Pass the adapter's own argument vector after a standalone '--' so flags such as -c are not "
            "parsed by this tool, or supply it verbatim with --command-json."
        ),
        epilog=(
            "Example: python -m tools.verify_adapter --agent codex --timeout 120 -- "
            "codex exec --json {task_file}"
        ),
    )
    parser.add_argument("--agent", required=True, help="Adapter type: codex, claude_code, opencode, deepseek_harness, zcode, generic_cli")
    parser.add_argument("--command-json", default=None, help='JSON array of arguments, e.g. \'["codex","exec","--json","{task_file}"]\'')
    parser.add_argument("--timeout", type=float, default=60.0, help="Seconds before the CLI is killed (default 60)")
    parser.add_argument("--workspace", default=None, help="Working directory for the CLI (default: current directory)")
    parser.add_argument("--output", default="artifacts/adapter_verification.json", help="Evidence output path")
    parser.add_argument("--health-only", action="store_true", help="Only check the executable; do not run the smoke task")
    return parser


def _resolve_command(args: argparse.Namespace, passthrough: list[str] | None) -> list[str]:
    """Prefer the post-'--' vector, then --command-json; reject ambiguous combinations."""
    if passthrough and args.command_json:
        raise ValueError("Supply the command either after '--' or via --command-json, not both")
    if passthrough:
        return passthrough
    if args.command_json:
        decoded = json.loads(args.command_json)
        if not isinstance(decoded, list) or not all(isinstance(part, str) for part in decoded):
            raise ValueError("--command-json must decode to an array of strings")
        return decoded
    return []


def main(argv: Sequence[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    passthrough: list[str] | None = None
    head = raw
    if "--" in raw:
        split_at = raw.index("--")
        head, passthrough = raw[:split_at], raw[split_at + 1:]
    args = build_parser().parse_args(head)
    try:
        command = _resolve_command(args, passthrough)
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": "INVALID_COMMAND", "message": str(exc)}, ensure_ascii=False, indent=2))
        return EXIT_CODES[NOT_RUN]
    evidence = verify(
        agent_type=args.agent,
        command=command,
        timeout_seconds=args.timeout,
        workspace=args.workspace,
        health_only=args.health_only,
    )
    path = write_evidence(evidence, args.output)
    payload = {
        "adapter_type": evidence["adapter_type"],
        "verification_status": evidence["verification_status"],
        "reason": evidence["reason"],
        "evidence_path": str(path),
        "scope": evidence["verdict_scope"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return EXIT_CODES.get(evidence["verification_status"], 2)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    sys.exit(main())

# FILE END: tools/verify_adapter.py
