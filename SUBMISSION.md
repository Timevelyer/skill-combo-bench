# Submission notes — how this repo is meant to be consumed

This file answers the two points raised in the review of PR #834 (`davepoon/buildwithclaude`):
the project's size/scope and the unverified adapters. It also states the exact manifest
entries needed to consume the project as an external plugin.

## 1. Size and scope — accepted, shipped as an external plugin

The project is a benchmark harness (code, JSON Schemas, task sets, tests, design notes),
not a drop-in prompt. Bundling it into an all-skills package would ship ~100 files to every
user, so it is **not** proposed for inclusion there.

The repository now carries a plugin manifest and a self-hosted marketplace:

```
.claude-plugin/plugin.json        # plugin identity: name, version, description, author, license
.claude-plugin/marketplace.json   # single-plugin marketplace, source: "./"
SKILL.md                          # concise skill entry (single-skill plugin: no skills/ dir)
```

`plugin.json` declares only documented fields (`name` is the only required key; `version`,
`description`, `author`, `homepage`, `repository`, `license`, `keywords` are the
recommended ones). The root `SKILL.md` is the skill entry because the plugin has no
`skills/` directory — that is the documented single-skill layout, not an improvised one.

## 2. Adapters are `NOT_VERIFIED` — now verifiable, still honest

The five vendor adapters (`codex`, `claude_code`, `opencode`, `deepseek_harness`, `zcode`)
extend one `GenericCLIAgent`: they declare an `adapter_id` and an `executable`, run with
`shell=False` from a user-supplied argument vector, and infer no proprietary flags.

Verification used to be a manual claim. It is now a tool that produces evidence:

```bash
python -m tools.verify_adapter --agent codex --timeout 120 \
  --output artifacts/adapter_verification.json -- \
  codex exec --json "{task_file}"
```

The adapter's own flags go after a standalone `--` so `-c`-style arguments are never parsed
by this tool. `--command-json '["codex","exec","--json","{task_file}"]'` is available for
scripted use.

The tool runs one minimal single-turn task and writes `adapter_verification.json`:

| Verdict | Condition | Exit |
|---|---|---|
| `VERIFIED` | exit 0 **and** non-empty, parseable output | 0 |
| `FAILED` | non-zero exit, timeout, cancellation, empty or unparseable output | 1 |
| `NOT_RUN` | no command configured, or executable not found, or `--health-only` | 2 |

The evidence file stores the platform, a SHA-256 of the argument template (the template is
hashed rather than stored, so credentials are not duplicated to disk), the exit code,
latency, masked stdout/stderr excerpts, and an explicit `does_not_establish` list. A
`VERIFIED` verdict is evidence about one command on one machine; it is not a claim about
output quality, cost, or support for other environments.

Nothing is upgraded to `VERIFIED` in the shipped repository: the adapters remain
`NOT_VERIFIED` until a user runs the command above against a real CLI, and the default
end-to-end path remains the mock agent (`MOCK_ONLY`).

## 3. Consuming it as an external plugin

### Option A — entry in an existing marketplace (pinned to a commit)

Add to the marketplace's `plugins` array:

```json
{
  "name": "skill-combo-bench",
  "source": {
    "source": "github",
    "repo": "Timevelyer/skill-combo-bench",
    "ref": "v6.1.1",
    "sha": "<40-character lowercase commit SHA>"
  },
  "description": "Offline-first, auditable benchmark for how skill combinations change agent behaviour",
  "category": "testing",
  "tags": ["benchmark", "evaluation", "skills", "agents", "reproducibility"]
}
```

- `sha` is the documented field for pinning; when both `ref` and `sha` are present, the
  commit in `sha` is checked out.
- Do **not** add `version` to the entry: `plugin.json` already sets `6.1.1`, and a
  conflicting entry version produces a warning.
- Resolve the SHA with `gh api repos/Timevelyer/skill-combo-bench/commits/main --jq .sha`.
  The `v6.1.1` tag points at the commit that carries the plugin manifests, the shortened
  `SKILL.md`, `docs/skill-reference.md` and `tools/verify_adapter.py`; the review-remediation
  commit before it is `39572c8629f3ae73ad7f1f3306274a4f27708b61`.

### Option B — users add this repository as a marketplace

```bash
/plugin marketplace add Timevelyer/skill-combo-bench
/plugin install skill-combo-bench@skill-combo-bench-marketplace
```

Because `.claude-plugin/marketplace.json` uses `"source": "./"`, this repository serves as
both the marketplace and the plugin.

## 4. Validate before merging

```bash
claude plugin validate .                      # manifest and component paths
python -m tools.bench_runner validate         # schemas, tasks, manifests
python -m unittest discover -s tests/unit -p "test_*.py"   # 56 unit tests
```

## 5. What changed relative to the initial PR snapshot

| Change | Reason |
|---|---|
| Added `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` | Consumable as an external plugin pinned to a commit |
| `SKILL.md` shortened (130 → 61 lines), detailed contracts moved to `docs/skill-reference.md` | The skill should describe *when to use* the bench and point at the repo, not re-document it |
| Added `tools/verify_adapter.py` (+ 15 unit tests) and `tests/unit/test_plugin_manifest.py` (+ 13 manifest tests) | Turns `NOT_VERIFIED` into a reproducible, evidence-producing procedure |
| Shared `ADAPTER_CLASS_PATHS` registry in `adapters/agent/__init__.py` | Engine and verifier resolve adapters from one mapping |
| Fixed test-count claim (`26` → `56` unit tests, plus 9 integration, 1 e2e) | Documentation accuracy |
| Added `docs/`, `.claude-plugin/` to the layout docs | Keep the documented tree truthful |
| Bumped the package version `6.0.0` → `6.1.1` in `pyproject.toml`, `plugin.json` and `marketplace.json` | `v6.0.0` is already released with the pre-plugin layout; the plugin packaging needs its own tag |
| Fixed the `verify_adapter` example in `docs/skill-reference.md` (`--command` was never a real flag; the argv goes after `--`) | A copy-pasteable example must actually run |

<!-- FILE END: SUBMISSION.md -->
