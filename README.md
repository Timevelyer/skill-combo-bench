# skill-combo-bench V6.0

[![CI](https://github.com/Timevelyer/skill-combo-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/Timevelyer/skill-combo-bench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-6.0.0-blue.svg)](https://github.com/Timevelyer/skill-combo-bench/releases)
[![GitHub stars](https://img.shields.io/github/stars/Timevelyer/skill-combo-bench?style=social)](https://github.com/Timevelyer/skill-combo-bench/stargazers)

**中文** · [English](README.en.md)

> An offline-first, auditable benchmark for measuring how skill combinations change agent behaviour — rule compliance, task success, tool chaining, fault recovery, cost and interaction effects — across Codex, Claude Code, OpenCode, DeepSeek Harness and Zcode.

一个**离线优先、可审计**的 skill 组合评测框架。量化「单个 skill vs. skill 组合」在智能体行为上的差异，覆盖规则遵循（RC）、任务成功、工具链完整性（TI）、交互效应（SS）、成本效率（CE）、单次成功成本（CPS）与故障恢复（RS）。

支持 Codex、Claude Code、OpenCode、DeepSeek Harness、Zcode 等外部 Agent，通过**无厂商假设**的可配置 CLI 适配层接入。

> **重要**：本项目默认运行在 `LOCAL` 模式，使用确定性 Mock Agent / Mock Tools 做软件闭环验证。任何真实模型结论都必须先完成真实凭据接入与预注册实验，绝不把离线 Mock 结果包装成真实模型能力。

## 安装

```bash
# 仅需两个运行时依赖
python -m pip install PyYAML jsonschema

# 可选：安装为命令行工具
pip install -e .
```

## 快速开始

```bash
python -m tools.bench_runner validate      # 校验配置/schema/任务/manifest
python -m tools.bench_runner dry-run       # 估算工作量与成本（不执行）
python -m tools.bench_runner run           # 运行离线 Mock 实验
python -m tools.bench_runner report --run-id <EXPERIMENT_ID>
python -m tools.bench_runner replay --run-id <EXPERIMENT_ID>   # 确定性复现
```

## 多 Agent 适配

外部 Agent 通过通用 CLI 适配器接入，框架**不推断任何厂商专有参数**：

| Agent | adapter type | executable | 状态 |
|---|---|---|---|
| Codex | `codex` | `codex` | NOT_VERIFIED |
| Claude Code | `claude_code` | `claude` | NOT_VERIFIED |
| OpenCode | `opencode` | `opencode` | NOT_VERIFIED |
| DeepSeek Harness | `deepseek_harness` | `deepseek` | NOT_VERIFIED |
| Zcode | `zcode` | `zcode` | NOT_VERIFIED |
| Generic CLI | `generic_cli` | 用户配置 | 配置驱动 |
| Mock | `mock` / `mock_agent` | 无 | MOCK_ONLY |

接入示例（在 config 中覆盖）：

```yaml
agent:
  type: codex
  command: ["codex", "exec", "--json", "{task_file}"]  # 由用户显式提供
  timeout_seconds: 120
```

`{task_file}` / `{workspace}` / `{run_id}` 占位符由框架填充；`shell=False`；健康检查仅探测可执行文件。

## 六项指标

| 指标 | 含义 |
|---|---|
| RC | Rule Compliance，加权规则遵循 |
| TI | Tool Integrity，工具调用完整性 |
| SS | Skill Synergy，交互效应 |
| CE | Cost Efficiency，成本效率 |
| CPS | Cost Per Success，单次成功成本 |
| RS | Robustness Score，故障恢复 |

统计单位固定为**完整 run**，配对交互使用 `task × repeat`，**不得把轮次当作独立样本**。

## 测试

```bash
python -m unittest discover -s tests/unit -p "test_*.py" -v
```

## 结果分类

- `MOCK_ONLY`：仅离线 Mock 验证。
- `NOT_VERIFIED`：适配器已实现但未端到端验证。
- `NOT_RUN`：真实模型、费用、Judge 校准、统计推断等未执行。

详细协议见 `engine/` 目录下的 `experimental_design.md`、`theoretical_basis.md`、`evaluation_rubric.md`、`probe_protocol.md`，以及 `SKILL.md` 中的跨 Agent 入口说明。

## 验证状态（2026-11-23）

| 检查 | 状态 | 说明 |
|---|---|---|
| 单元测试 | 通过（28/28） | `python -m unittest discover -s tests/unit`，Python 3.11.17 |
| 集成测试 | 通过（9/9） | `tests/integration`，Mock Agent 与 Mock Tools |
| 端到端测试 | 通过（1/1） | `tests/e2e`，离线闭环 |
| 真实模型 / Provider | **未执行** | 无真实凭据；任何真实结论都必须重新预注册实验 |
| 外部 Agent 适配 | **未验证** | 五个宿主的 adapter 均为 `NOT_VERIFIED`；Mock 路径为 `MOCK_ONLY` |

以上测试全部运行在离线 Mock 路径上，只证明评测流水线自身可运行、可复现，**不构成任何真实模型能力或 skill 组合效果的结论**。详细记录见 [PHASE_STATUS.md](PHASE_STATUS.md)。

## License

MIT

<!-- FILE END: README.md -->
