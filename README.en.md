# skill-combo-bench

[![CI](https://github.com/Timevelyer/skill-combo-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/Timevelyer/skill-combo-bench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-6.0.0-blue.svg)](https://github.com/Timevelyer/skill-combo-bench/releases)
[![GitHub stars](https://img.shields.io/github/stars/Timevelyer/skill-combo-bench?style=social)](https://github.com/Timevelyer/skill-combo-bench/stargazers)

English · [中文](README.md)

An **offline-first, auditable benchmark** for measuring how skill combinations change agent behaviour: rule compliance, task success, tool chaining, fault recovery, cost, and interaction effects.

It ships a vendor-neutral CLI adapter layer for Codex, Claude Code, OpenCode, DeepSeek Harness and Zcode, and runs a deterministic Mock Agent / Mock Tools loop by default so the harness itself can be validated without API keys.

> **Important:** the default mode is `LOCAL` with mocks. Any claim about real model capability requires real credentials, a pre-registered experiment, and recorded runs. Mock results are never presented as model results.

## Install

```bash
# two runtime dependencies
python -m pip install PyYAML jsonschema

# optional: install the CLI
pip install -e .
```

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

## Result classes

- `MOCK_ONLY`: validated offline only.
- `NOT_VERIFIED`: adapter implemented, no end-to-end verification.
- `NOT_RUN`: real models, cost, judge calibration and statistical inference not executed.

## Verification status (2026-11-23)

| Check | Status | Note |
|---|---|---|
| Unit tests | pass (28/28) | `python -m unittest discover -s tests/unit`, Python 3.11.17 |
| Integration tests | pass (9/9) | `tests/integration`, mock agent and tools |
| End-to-end test | pass (1/1) | `tests/e2e`, offline loop |
| Real model / provider | **not executed** | no credentials; any real claim needs a fresh pre-registered run |
| External agent adapters | **not verified** | all five hosts are `NOT_VERIFIED`; mock path is `MOCK_ONLY` |

These results cover the offline mock path only. They show the harness runs and replays deterministically; they say nothing about real model capability or about whether a specific skill combination helps. Details: [PHASE_STATUS.md](PHASE_STATUS.md).

## License

MIT
