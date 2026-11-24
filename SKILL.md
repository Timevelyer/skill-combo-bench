---
name: skill-combo-bench
description: Runs an offline, auditable benchmark of how skill combinations (single skill vs. A, B, A+B) change agent behaviour. Use when a user asks to benchmark, compare, or measure skill combinations across agents such as Codex, Claude Code, OpenCode, DeepSeek Harness, or Zcode; to run a reproducible offline mock experiment; to validate a skill-combination dataset; or to produce a report with RC/TI/SS/CE/CPS/RS metrics. Do not use it to claim real model performance without credentials and a pre-registered run.
---

# Skill Combo Bench

Measure how skill combinations change agent behaviour — rule compliance (RC), tool
integrity (TI), synergy (SS), cost (CE, CPS) and fault recovery (RS) — with a
deterministic, offline-first harness you can audit.

**Repository:** <https://github.com/Timevelyer/skill-combo-bench> · **License:** MIT
**Full metrics contracts:** `docs/skill-reference.md` · **Design notes:** `engine/*.md`

## When to use

- Comparing a single skill against a combination (A, B, A+B) on the same task set.
- Checking that an evaluation pipeline is reproducible before spending money on models.
- Validating a task set / manifest / trace against the shipped JSON Schemas.
- Producing a paired-design report with effect sizes, CIs and Holm correction.

## Quick start

```bash
python -m pip install PyYAML jsonschema        # only two runtime dependencies
python -m tools.bench_runner validate          # schemas + tasks + manifests
python -m tools.bench_runner dry-run           # estimate runs and cost, execute nothing
python -m tools.bench_runner run               # deterministic offline mock experiment
python -m tools.bench_runner report --run-id <EXPERIMENT_ID>
```

`run` completes in well under a minute and needs no network, no API key and no agent CLI.

## Honesty rules (non-negotiable)

Every artefact is labelled; do not upgrade a label without new evidence.

| Label | Meaning |
|---|---|
| `MOCK_ONLY` | Deterministic mock agent/tools only — proves the pipeline runs, says nothing about model quality. |
| `NOT_VERIFIED` | A vendor CLI adapter exists but was never exercised end to end. |
| `NOT_RUN` | Real models, real cost, judge calibration or inference were not executed. |

- Statistical unit is one **complete run**; pairing is `task × repeat`. Never treat a turn as an independent sample.
- Do not report a judge as "calibrated" from a single correlation coefficient.
- Do not present mock results as model capability. State `n`, effect size, 95% CI, test and correction.

## Adapters

Five vendor adapters (Codex, Claude Code, OpenCode, DeepSeek Harness, Zcode) extend one
`GenericCLIAgent`: they declare an `adapter_id` and `executable`, run with `shell=False`
from a user-supplied argument vector, and are marked `NOT_VERIFIED` until someone runs
`python -m tools.verify_adapter`. No proprietary flag, prompt or auth argument is inferred.

## Scope

This is a benchmark project, not a drop-in prompt: it ships code, schemas, tasks, tests
and design notes. Install it as an external plugin or run it from a clone; do not bundle
it into an all-skills package.

<!-- FILE END: SKILL.md -->
