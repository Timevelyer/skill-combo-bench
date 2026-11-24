# Skill Combo Bench — Contract Reference

Detailed contracts behind `SKILL.md`. Read this before adding tasks, tools, faults or metrics.

## Project layout

```
skill-combo-bench/
├── SKILL.md                 # concise skill entry (single-skill plugin root)
├── .claude-plugin/          # plugin.json + marketplace.json
├── config/                  # YAML: default / modalities / sampling / providers / pricing
├── schemas/                 # JSON Schema: task / run_trace / judge_result / experiment / skill_manifest
├── engine/                  # state / validation / trace / scheduler / metrics / mutation / multimodal / experiment
├── adapters/
│   ├── agent/               # mock + external CLI adapters (Codex / Claude Code / OpenCode / DeepSeek Harness / Zcode)
│   ├── providers/           # mock_provider / openai_compatible
│   └── tools/               # deterministic mock tools + fault injector
├── tools/                   # CLI, statistics, judge calibration, cost estimate, trace export, dataset validation, adapter verification
├── datasets/                # offline tasks + multimodal synthetic assets + mutation set
├── prompts/                 # judge / task generation / adversarial generation prompts
├── templates/               # report and experiment card templates
└── tests/                   # unit + integration + e2e, mock_skills, golden_set
```

## Statistical unit

The unit is one **complete run** (a full multi-turn task execution). Paired interaction
uses `task × repeat`. **A single turn is never an independent sample.** Reports must state
n, effect size, 95% CI, the test used and Holm correction.

## Six metrics

| Metric | Definition |
|---|---|
| **RC** | Rule Compliance — weighted rule following; N/A items are excluded from the denominator |
| **TI** | Tool Integrity — tool-call completeness; external/safety failures excluded |
| **SS** | Skill Synergy — interaction effect; AB > A, B is *not* super-additivity |
| **CE** | Cost Efficiency |
| **CPS** | Cost Per Success |
| **RS** | Robustness Score — RECOVERED / GRACEFUL_DEGRADED / SAFE_STOP reported separately |

## Result classification

- `MOCK_ONLY` — offline mock verification only; says nothing about real model capability.
- `NOT_VERIFIED` — external agent / provider adapter implemented but not verified end to end.
- `NOT_RUN` — real models, real cost, judge calibration or statistical inference not executed.

## Task contract

Suggested task fields: `task_id`, `version`, `description`, `modalities`, `turns`,
`assertions`. Each turn carries `turn_index`, `input`, `mock_output`, `tool_calls`,
`state_writes`, `state_probes`. A tool call carries `call_id`, `name`, `arguments`,
`save_as`. An assertion carries `probe_id`, `skill_id`, `probe_family`, `turn_index`,
`type`, `expected`, `weight`, `evidence_source`.

## Tool argument conventions

| Tool | Arguments |
|---|---|
| `mock_calculator` | `expression` string — AST whitelist, never `eval` |
| `mock_database` | `operation: create\|get\|update\|assert` |
| `mock_weather` | `location` (`city` accepted as an alias) |
| `mock_file_store` | `operation` / `path` / `content` |
| `mock_search` | `query` |

Results saved via `save_as` are referenced as `${name.field}`.

## Fault injection

`adapters/tools/fault_injector.py` supports `TIMEOUT`, `INVALID_ARGUMENT`, `SERVER_ERROR`,
`INTERMITTENT`, `DUPLICATE_RESPONSE`, `STALE_STATE`, `PARTIAL_RESULT`, with `probability`,
`max_triggers`, `delay_seconds` and `seed`. Tasks declare faults per turn in a `faults`
array; the framework converts them into tool-level profiles.

## Multi-agent adaptation

External agents enter through a **no-shell-inference** configurable CLI adapter:

1. **No invented vendor flags.** Codex / Claude Code / OpenCode / DeepSeek Harness / Zcode
   subclasses only declare `adapter_id`, `executable` and `verification_status="NOT_VERIFIED"`
   and run through `GenericCLIAgent`.
2. **Config driven.** Set `agent.type` to `codex` / `claude_code` / `opencode` /
   `deepseek_harness` / `zcode` and supply a `command` argument array supporting the
   `{task_file}`, `{workspace}` and `{run_id}` placeholders.
3. **Health check is executable discovery only.** `health_check()` calls `shutil.which()`;
   it never invokes the CLI and never touches the network.
4. **Unconfigured means UNSUPPORTED.** Without a `command`, the adapter returns
   `UNSUPPORTED` rather than guessing a syntax.

```yaml
agent:
  type: codex            # or claude_code / opencode / deepseek_harness / zcode / generic_cli
  command: ["codex", "exec", "--json", "{task_file}"]  # supplied by the user, never inferred
  timeout_seconds: 120
```

To move an adapter past `NOT_VERIFIED`, run a real smoke check and keep the evidence:

```bash
python -m tools.verify_adapter --agent codex \
  --output artifacts/adapter_verification.json -- \
  codex exec --json "{task_file}"
```

The adapter's own flags go after a standalone `--`, so options such as `-c` are never parsed
by the verification tool; `--command-json '["codex","exec","--json","{task_file}"]'` is the
scripted equivalent.

The command writes `VERIFIED` only when the process exits 0 **and** emits parseable output;
otherwise it records `FAILED` with the observed exit code and stderr excerpt. Evidence is
per-machine and per-command, so it never generalises to "the adapter works for everyone".

## Reporting and honesty constraints

- Reports must separate `MOCK_ONLY` / `NOT_VERIFIED` / `NOT_RUN` and list every unexecuted,
  blocked or mock-only item explicitly.
- Judge calibration must report agreement, error and confidence intervals separately;
  **never claim "calibrated" from a single correlation coefficient**.
- Paired designs must declare a stopping boundary; insufficient samples are marked `UNDERPOWERED`.
- Real experiments must pre-register the null hypothesis and SESOI.

Protocols: `engine/experimental_design.md`, `engine/theoretical_basis.md`,
`engine/evaluation_rubric.md`, `engine/probe_protocol.md`.

## Tests

```bash
python -m unittest discover -s tests/unit -p "test_*.py" -v
python -m unittest discover -s tests/integration -p "test_*.py" -v
python -m unittest discover -s tests/e2e -p "test_*.py" -v
```

58 unit, 9 integration and 1 end-to-end test cover metrics, mutation, state validation,
statistics, judge calibration, CLI wiring, fault injection, resume, the mock loop and
adapter verification verdicts.
