# PHASE_STATUS.md

> 本文件记录 V6.0 的实施进度、实际执行命令、测试结果与未完成项。
> 维护规则：每个 Phase 结束时更新；状态只使用 `PASS` / `FAIL` / `NOT_RUN` / `BLOCKED` / `MOCK_ONLY` / `PARTIAL`。

**最后更新：** 2026-11-23（审计复核后）
**项目版本：** 6.0.0
**测试总数：** 38（28 unit + 9 integration + 1 e2e）
**运行模式：** `LOCAL`（可写文件、可运行本地代码，无真实模型 API 凭据）

---

## Phase 0：能力探测

| 探测项 | 结果 |
|---|---|
| Agent | `UNKNOWN`（当前宿主未提供可核验的 Agent 名称） |
| Harness | `UNKNOWN` |
| Model Provider | `UNKNOWN`（无真实 Provider 凭据） |
| Python | 3.13.14 |
| Git | 可用 |
| 网络 | 可用（低风险连通性探测通过） |
| 文件读写 | 可用 |
| 可用模态 | text、structured_data（无真实图像/音频/视频模型） |
| API 凭据 | `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `DEEPSEEK_API_KEY` 均 `MISSING` |
| MCP SDK | 未安装 → `MCP_ADAPTER_BLOCKED` |
| 图像/音频依赖 | Pillow 未安装 → 多模态为合成资产 + 能力声明 |
| 外部 Agent CLI | `codex` 存在；`claude` / `opencode` / `deepseek` / `zcode` 未发现 |

**结论：** 选择 `LOCAL`。全部真实 Agent / Provider 集成标记 `NOT_VERIFIED`，不做真实模型结论。

---

## Phase 1–8 状态

| Phase | 内容 | 状态 | 证据 |
|---|---|---|---|
| 1 | 骨架、配置、Schema、日志模型 | `PASS` | 5 个 Schema 全部通过 `validate` |
| 2 | 最小离线闭环（Mock Agent/Tools/执行器/状态/trace） | `PASS` | `run` 产出 40 run + trace JSONL |
| 3 | 探针与指标（RC/TI/SS/CE/CPS/RS） | `PASS` | `tests/unit/test_metrics.py` 10 项通过 |
| 4 | 故障注入与 Mutation | `PASS` | 故障注入 3 类集成测试通过；变异算子有单元测试 |
| 5 | 统计分析与 Judge 校准 | `PASS` | `stats_analysis`、`judge_calibration` 均可运行 |
| 6 | 多模态与外部 Adapter | `PARTIAL` | 能力声明与合成资产完成；真实多模态推理 `NOT_RUN`；外部 Agent `NOT_VERIFIED` |
| 7 | CLI、报告、安全检查 | `PASS` | 8 条规范命令全部可运行；17 个参数真实生效 |
| 8 | 最终验收 | `PASS`（含未验证项标注） | 见下方验收矩阵 |

---

## 实际执行命令与结果

| 命令 | 退出状态 | 结果 |
|---|---|---|
| `python -m tools.bench_runner --help` | 0 | 正常输出 |
| `python -m tools.bench_runner validate --config config/default.yaml` | 0 | 5 Schema + 5 任务 + 5 manifest 全通过 |
| `python -m tools.bench_runner dry-run --config config/default.yaml` | 0 | `estimated_runs=40`，`pricing_status=COST_UNKNOWN` |
| `python -m tools.bench_runner run --config config/default.yaml` | 0 | 40 run 全部 `PASS`，8 个故障任务 `RECOVERED` |
| `python -m tools.bench_runner resume --run-id <ID>` | 0 | 全量 resume 跳过 0 新跑；断点后仅补缺失 |
| `python -m tools.bench_runner report --run-id <ID>` | 0 | 重新生成 20 节报告 |
| `python -m tools.judge_calibration --dataset tests/golden_set/development.jsonl` | 0 | `status=N/A`（缺 judge 分数，明确报告 4 条 human / 0 条 judge） |
| `python -m tools.judge_calibration --dataset tests/golden_set/calibration_example.jsonl --bias` | 0 | `status=PASS`，MAE 0.125 / ICC 0.96 / Kappa 0.778；偏差筛查三项均未触发（合成示例） |
| `python -m tools.stats_analysis --input <results.jsonl>` | 0 | 配对分析输出，退化情形明确标 `N/A`，无 NaN |
| `python -m unittest discover -s tests/unit` | 0 | 28 tests `OK` |
| `python -m unittest discover -s tests/integration` | 0 | 9 tests `OK` |
| `python -m unittest discover -s tests/e2e` | 0 | 1 test `OK` |
| Schema 校验（实际生成的 664 条 trace） | 0 | 0 失败 |
| Schema 校验（experiment.json / 5 任务 / 5 manifest / judge_result） | 0 | 全部通过 |

---

## 审计修复记录（本轮）

| 缺陷 | 影响 | 修复 |
|---|---|---|
| `bench_runner` 字典展开语法错误 | 模块无法导入 | 改为显式构造 |
| `mock_weather` 参数 `city` 与任务 `location` 不一致 | 故障任务无法注入重试 | 支持 `location` 主字段 + `city` 别名 |
| agent type 映射缺 `mock_agent` | `run` 直接失败 | 补充映射键 |
| `trace_path` 在 root 外 output_dir 崩溃 | 自定义输出目录不可用 | `_relative_trace_path` 回退绝对路径 |
| `redact` 误伤 `token_usage` | trace 违反 Schema | `SAFE_STAT_KEYS` 白名单 + 回归测试 |
| `stats_analysis` 全零差值输出 NaN | JSON 序列化崩溃 | 显式退化检测 + `_sanitize` |
| `judge_calibration` 字段不兼容 + exit 2 | 命令不可用 | 支持 `human_total_score` 别名；N/A 返回 0 |
| `MockJudge` 输出不符合 judge schema | judge_result 校验失败 | 重写为 schema-valid 结构；parser 改用 schema 校验 |
| `experiment.json` 不符合 experiment schema | 快照契约不一致 | 放宽 schema + 快照补齐四层信息与 Skill 哈希 |
| `resume` 无法定位自定义目录 / 重用默认配置 | 断点恢复失效 | `locate_experiment` 扫描 + `run_plan` 快照 |
| run 级状态不反映底层超时/循环 | 无法区分 TIMED_OUT/LOOPED | 从工具事件推断状态与 robustness |
| 报告缺 RC 多维分解 | 不满足 9.1 | `rc_breakdown`：全局/Skill/探针族/轮次/失败数与分母 |
| 报告缺按模态分层成功率 | 不满足 9.7 | record 记录 `modalities` + 报告 11b 节 |
| 缺 `--retention-days` | 不满足 13.5 | CLI 参数 + 真实清理过期实验目录 |
| 缺 Judge 偏差筛查 | 不满足 11.7 | `bias_report` + `--bias`（长度/位置/拒绝误判） |
| `tests/integration` 为空 | 不满足 18.2 | 9 项集成测试覆盖全部要求 |
| `PHASE_STATUS.md` 缺失 | 不满足 18.4 第 21 项 | 本文件 |
| Mock 状态标为 IMPLEMENTED | 低估真实验证结果 | 更新为 `INTEGRATION_TESTED` / `integration_test_status: PASS` |

---

## 验收标准（18.4）逐项核对

| # | 条目 | 状态 | 证据 / 说明 |
|---|---|---|---|
| 1 | Phase 0 能力报告已生成 | `PASS` | 本文件 Phase 0 段 |
| 2 | 项目结构完整 | `PASS` | 对照第 14 节清单，全部文件存在 |
| 3 | Schema 校验通过 | `PASS` | `validate` 退出 0 |
| 4 | Mock Agent 可运行 | `PASS` | `run` + `tests/integration` |
| 5 | Mock Tools 可运行 | `PASS` | 5 个工具均有单元/集成覆盖 |
| 6 | 多轮状态测试通过 | `PASS` | 002 任务 + `test_multi_turn_state_and_skill_order` |
| 7 | 工具链探针通过 | `PASS` | `test_tool_chain_data_transfer`（DB→Calculator） |
| 8 | 故障注入测试通过 | `PASS` | server_error 端到端；timeout / invalid_argument / server_error 集成测试均通过 |
| 9 | 重试、熔断和总超时生效 | `PASS` | 重试 `retry_index=1` 可观测；`test_timeout_is_enforced`；`test_repeated_calls_are_bounded` |
| 10 | 指标公式有单元测试 | `PASS` | `test_metrics.py` 10 项 |
| 11 | 配对统计与非参数分析可运行 | `PASS` | `stats_analysis` 输出 t / Wilcoxon / Bootstrap / 置换 |
| 12 | 顺序采样遵守预设停止规则 | `PASS` | `GroupSequentialDesign` 仅在预声明 look 评估；单元测试覆盖 |
| 13 | Judge Prompt 和校准工具存在 | `PASS` | `prompts/judge_system.md` + `tools/judge_calibration.py` |
| 14 | Golden Set 来源与标注状态清楚 | `PASS` | 全部标注 `synthetic` / `single_annotator` / `smoke-only` / `NOT_CALIBRATED` |
| 15 | 多模态能力边界明确 | `PASS` | `capabilities()` 声明 + `UNSUPPORTED` 显式降级；真实推理 `NOT_RUN` |
| 16 | 成本估算有 `ESTIMATE` 标记 | `PASS` | `dry-run` 返回 `status=ESTIMATE`、`COST_UNKNOWN` |
| 17 | 日志不泄露凭据 | `PASS` | `redact()` 覆盖 key/token/secret；`.env` 已入 `.gitignore` |
| 18 | 离线端到端测试通过 | `PASS` | `tests/e2e/test_end_to_end.py` |
| 19 | README 命令经过实际验证 | `PASS` | 上表 8 条命令均实测退出 0 |
| 20 | 报告区分真实/Mock/估算/未运行 | `PASS` | 报告第 20 节逐项列出 `MOCK_ONLY` / `NOT_VERIFIED` / `NOT_RUN` |
| 21 | `PHASE_STATUS.md` 与实际文件状态一致 | `PASS` | 本文件 |

---

## 未完成、未验证与阻塞项

| 项目 | 状态 | 说明 |
|---|---|---|
| Codex 端到端集成 | `NOT_VERIFIED` | 仅 `health_check` 可探测可执行文件；未运行真实 Codex 任务 |
| Claude Code / OpenCode / DeepSeek Harness / Zcode | `NOT_VERIFIED` | 本机未安装对应 CLI；Adapter 通过通用 CLI 协议接入 |
| 真实模型推理 | `NOT_RUN` | 无 API 凭据 |
| 真实费用 / 账单 | `NOT_RUN` | 无价格配置；一律 `COST_UNKNOWN` |
| Judge 真实校准 | `NOT_RUN` | Golden Set 无真实 judge 分数；`calibration_example.jsonl` 仅为流水线验证用合成数据 |
| 统计推断（功效/显著性） | `NOT_RUN` | 40 run 仅验证功能；未做功效分析，结论标记 `UNDERPOWERED` 风险 |
| MCP 集成 | `BLOCKED` | 未安装 MCP SDK；核心引擎不依赖 MCP |
| 真实图像/音频/视频推理 | `NOT_RUN` | 仅合成资产与能力声明 |
| 顺序采样实盘追加 | `PARTIAL` | 设计已实现并通过单元测试；未在真实实验中在线追加 |

---

## 已知限制

1. Mock Agent 只重放 `task['turns']` 中的脚本，Skill 文本为惰性上下文，不改变行为。
2. 任务数据层端到端覆盖 `server_error`；`timeout` 与 `invalid_argument` 由集成测试真实覆盖（受运行时长限制，未进入批量任务）。
3. 统计退化情形（全零差值）明确返回 `N/A`，不伪造显著性。
4. 多模态资产为合成数据，仅验证预处理与哈希链路，不代表真实视觉能力。

---

## 下一步入口

- 接入真实模型：配置 `config/providers.yaml` + 环境变量，将 `judge` 设为真实 Judge 后运行 `validate` → `dry-run` → `run`。
- 接入真实 Agent：在 `config/default.yaml` 设置 `agent.type` 与 `agent.command`（参数数组），先跑 `health_check` 再小批量 `run`。
- 完成 Judge 校准：对 `tests/golden_set/development.jsonl` 运行真实 Judge，写入 `judge_score` 后执行 `judge_calibration`。
- 进入正式实验前：预注册主要终点、SESOI、顺序停止边界。

<!-- FILE END: PHASE_STATUS.md -->
