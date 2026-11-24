# skill-combo-bench V6.0

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

### 作为 Claude Code 插件安装（推荐）

本仓库自带 `.claude-plugin/plugin.json` 与 `.claude-plugin/marketplace.json`，是一个**单技能插件**（根 `SKILL.md` 即技能入口）。在外部 marketplace 中按提交固定引用：

```json
{
  "name": "skill-combo-bench",
  "source": {
    "source": "github",
    "repo": "Timevelyer/skill-combo-bench",
    "ref": "main",
    "sha": "<40 位提交 SHA>"
  },
  "description": "Offline-first, auditable benchmark for skill combinations across agents",
  "category": "testing"
}
```

`sha` 必须是已审查提交的完整 40 位小写 SHA；省略 `ref` 时默认使用仓库默认分支。条目内不要再写 `version`，否则会与 `plugin.json` 冲突并触发告警（以 `plugin.json` 为准）。

### 为什么不并入 all-skills 包

本仓库是完整工程（代码、Schema、任务集、测试、设计文档），安装体积与更新频率均不适合作为 all-skills 的内置条目；应作为外部插件按提交固定引用，或直接 clone 运行。

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

### 把 `NOT_VERIFIED` 变成有证据的结论

```bash
python -m tools.verify_adapter --agent codex --timeout 120 \
  --output artifacts/adapter_verification.json -- \
  codex exec --json "{task_file}"
```

该工具跑一次最小 smoke 任务，写出 `adapter_verification.json`（平台、命令模板 SHA-256、exit code、延迟、脱敏输出、`does_not_establish` 清单）。裁定三态：`VERIFIED`（exit 0 且输出可解析）/ `FAILED` / `NOT_RUN`（未配置命令、可执行文件不存在或仅 `--health-only`）。`VERIFIED` 只证明"一次命令、一台机器、一个 smoke 任务"，不代表输出质量、成本或跨环境支持。CLI 自身参数放在 `--` 之后，避免 `-c` 之类选项被本工具解析。

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

详细协议见 `engine/` 目录下的 `experimental_design.md`、`theoretical_basis.md`、`evaluation_rubric.md`、`probe_protocol.md`，以及 `docs/skill-reference.md` 中的契约参考（任务契约、工具参数、故障注入、适配器验证流程）。

## License

MIT

<!-- FILE END: README.md -->
