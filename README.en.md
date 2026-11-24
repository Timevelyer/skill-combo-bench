# skill-combo-bench

[![CI](https://github.com/Timevelyer/skill-combo-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/Timevelyer/skill-combo-bench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-6.1.2-blue.svg)](https://github.com/Timevelyer/skill-combo-bench/releases)
[![GitHub stars](https://img.shields.io/github/stars/Timevelyer/skill-combo-bench?style=social)](https://github.com/Timevelyer/skill-combo-bench/stargazers)

English · [中文](README.md)

An **offline-first, auditable benchmark** for measuring how skill combinations change agent behaviour: rule compliance, task success, tool chaining, fault recovery, cost, and interaction effects.

It ships a vendor-neutral CLI adapter layer for Codex, Claude Code, OpenCode, DeepSeek Harness and Zcode, and runs a deterministic Mock Agent / Mock Tools loop by default so the harness itself can be validated without API keys.

> **Important:** the default mode is `LOCAL` with mocks. Any claim about real model capability requires real credentials, a pre-registered experiment, and recorded runs. Mock results are never presented as model results.

## Install

### As a Claude Code plugin (recommended)

The repository ships `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, so it is a **single-skill plugin**: the root `SKILL.md` is the skill entry.

```bash
/plugin marketplace add Timevelyer/skill-combo-bench
/plugin install skill-combo-bench@skill-combo-bench-marketplace
```

To list it from someone else's marketplace, pin the commit — `sha` must be the full 40-character lowercase SHA:

```json
{
  "name": "skill-combo-bench",
  "source": {
    "source": "github",
    "repo": "Timevelyer/skill-combo-bench",
    "ref": "v6.1.2",
    "sha": "<40-character commit SHA>"
  },
  "description": "Offline-first, auditable benchmark for skill combinations across agents",
  "category": "testing"
}
```

Do not add `version` to the entry: `plugin.json` already declares one, and a second declaration only produces a warning (`plugin.json` wins).

### From source

```bash
# two runtime dependencies
python -m pip install PyYAML jsonschema

# optional: install the CLI
pip install -e .
```

### Why this is not bundled into an all-skills package

This is a full engineering project — code, JSON Schemas, task sets, tests, design notes. Its size and update cadence do not belong inside an all-skills bundle; consume it as an external plugin pinned to a commit, or clone and run it.

## Quick start

```bash
python -m tools.bench_runner validate      # validate config / schemas / tasks / manifest
python -m tools.bench_runner dry-run       # estimate workload and cost, execute nothing
python -m tools.bench_runner run           # run the offline mock experiment
python -m tools.bench_runner report --run-id <EXPERIMENT_ID>
python -m tools.bench_runner replay --run-id <EXPERIMENT_ID>   # deterministic replay
```

## Metrics

| Metric | Meaning |
|---|---|
| RC | Rule Compliance, weighted |
| TI | Tool Integrity, tool-call chain completeness |
| SS | Skill Synergy, interaction effect |
| CE | Cost Efficiency |
| CPS | Cost Per Success |
| RS | Robustness Score, fault recovery |

The statistical unit is a **complete run**; paired interaction analysis uses `task × repeat`. Turns are never treated as independent samples.

## Agent adapters

| Agent | adapter type | executable | Status |
|---|---|---|---|
| Codex | `codex` | `codex` | NOT_VERIFIED |
| Claude Code | `claude_code` | `claude` | NOT_VERIFIED |
| OpenCode | `opencode` | `opencode` | NOT_VERIFIED |
| DeepSeek Harness | `deepseek_harness` | `deepseek` | NOT_VERIFIED |
| Zcode | `zcode` | `zcode` | NOT_VERIFIED |
| Generic CLI | `generic_cli` | user-configured | config-driven |
| Mock | `mock` / `mock_agent` | none | MOCK_ONLY |

Commands are user-supplied; the framework fills `{task_file}`, `{workspace}` and `{run_id}` and never assumes vendor-specific flags. `shell=False`. Health checks only probe whether the executable exists.

### Turning `NOT_VERIFIED` into evidence

```bash
python -m tools.verify_adapter --agent codex --timeout 120 \
  --output artifacts/adapter_verification.json -- \
  codex exec --json "{task_file}"
```

The tool runs one minimal smoke task and writes `adapter_verification.json`: platform, SHA-256 of the argument template, exit code, latency, masked output, and an explicit `does_not_establish` list. Three verdicts: `VERIFIED` (exit 0 with parseable output), `FAILED`, and `NOT_RUN` (no command, executable missing, or `--health-only`). A `VERIFIED` verdict covers one command, one machine and one smoke task — not output quality, cost, or other environments. The CLI's own flags go after a standalone `--` so options such as `-c` are never parsed by the tool.

## Result classes

- `MOCK_ONLY`: validated offline only.
- `NOT_VERIFIED`: adapter implemented, no end-to-end verification.
- `NOT_RUN`: real models, cost, judge calibration and statistical inference not executed.

## Verification status (2026-11-24)

| Check | Status | Note |
|---|---|---|
| Unit tests | pass (58/58) | `python -m unittest discover -s tests/unit`, Python 3.11.17 |
| Integration tests | pass (9/9) | `tests/integration`, mock agent and tools |
| End-to-end test | pass (1/1) | `tests/e2e`, offline loop |
| Config / schemas / tasks | pass | `python -m tools.bench_runner validate`, no errors |
| Plugin manifests | pass (static) | structural invariants of `.claude-plugin/plugin.json` and `marketplace.json` are asserted by unit tests |
| Real model / provider | **not executed** | no credentials; any real claim needs a fresh pre-registered run |
| External agent adapters | **not verified** | all five hosts are `NOT_VERIFIED`; mock path is `MOCK_ONLY` |

These results cover the offline mock path only. They show the harness runs and replays deterministically; they say nothing about real model capability or about whether a specific skill combination helps. Details: [PHASE_STATUS.md](PHASE_STATUS.md).

## License

MIT
