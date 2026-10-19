# Phase 7: Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay) - Context

**Gathered:** 2026-10-11
**Status:** Ready for planning

<domain>
## Phase Boundary

让管线本身可被外部工具完整驱动、测量、扩展 —— 全部 CLI-first、CPU 可测、不用时逐字节一致。四件事：

1. **PIPE-01** FlopsCounter（20+ 架构前向钩子）从已废弃的 `pipeline/dnallmmark_pipeline.py` 移植进 `run_finetune.py`（always-on 测量 + 训练时间/GPU 平台记录）
2. **PIPE-02** `run_sweep.py` 透传四旗标（`--subset_file` / `--effective_batch_size` / `--num_train_epochs` / `--cache_dir`）—— **四旗标在 run_finetune.py 已全部存在**（`:138/:167/:188/:211`），本相是 sweep 侧纯透传工程 + 预校验
3. **CUST-05** 官方+自定义注册表 overlay 缝隙（共享 loader 模块，自动探测，冲突 fail-fast，缺席逐字节一致）
4. **PIPE-03** 容错 JSON loader 契约（`pipeline/artifact_loader.py`，Phase 11 monitor 与 Phase 8 tui/services 复用）

含一次维护者已解禁的 GB10 FLOPs smoke（code-only 限制已取消）。

</domain>

<decisions>
## Implementation Decisions

### FLOPs 启用与输出契约（PIPE-01）
- **D-01:** FlopsCounter **always-on** —— 每个 run 自动挂钩并写报告，与旧管线行为一致，无额外旗标面（不设 `--flops`/`--no-flops`）。
- **D-02:** 输出走**独立 `flops_report.json`**，沿用 legacy 文件名与 schema（逐层明细 + `save_to_json` 外推总训练 FLOPs），落在每个 run 输出目录；**不动 `run_record.json` 现有测试契约**。
- **D-03:** **uncovered 架构层响亮报告**：钩子分派未命中的层归为 uncovered 并在报告中显式列出；uncovered 占比超阈值时控制台 WARNING。宁可噪声不可静默少计（正确性品牌纪律）。
- **D-04:** 移植完成后**删除 `pipeline/dnallmmark_pipeline.py`**（Phase 3 已废弃，git 历史即参考）。删除前需检查仓库内残留引用（docs/测试/注释）。
- **D-05（维护者 2026-10-11 中途补充）:** flops_report.json 新增 **hardware/runtime 节**：`gpu_device`（如 5090 / RTX6000 / 4090 / 5090D / 4090D，取 `torch.cuda.get_device_name()` 实报字符串，不做枚举映射）、`train_time`（训练时长）、`max_mem_gb`（显存峰值，现有 print 改落盘）。仅管线侧捕获；前端展示记 Deferred。— **Reversibility:** costly — flops_report schema 对外发布后，hardware 节字段名成为下游（monitor/排行榜）依赖契约。

### Overlay 激活机制（CUST-05）
- **D-06:** **自动探测**：`~/.config/dnallmmark/custom_models.json` / `custom_datasets.json` 存在即加载；缺失 = 逐字节今日行为。不设显式开关旗标。
- **D-07:** 路径解析：默认 platformdirs（`~/.config/dnallmmark/`）；提供 **`DNALLMMARK_CUSTOM_REGISTRY_DIR` 单一 env var** 覆盖整个目录（测试注入 tmp_path + 非标准 home 环境）。
- **D-08:** **共享 loader 模块**（如 `pipeline/registry_loader.py`）：合并视图 + 官方键冲突 fail-fast（清晰报错）。run_finetune 模块级加载（`:674-679`）改走它但**导入时序不变**；run_sweep 三处（`:368/:474/:514`）与 audit（`script/audit_n_frequencies.py:599`）全部改走它（D-10 单源先例）。
- **D-09:** **不动 `script/export_runs.py`**（已核实运行时不加载注册表，只读 run artifacts；自定义条目经 run 自然流入导出）。Phase 7 overlay 触点 = run_sweep ×3 + run_finetune ×1（两文件一次加载）+ audit ×1。

### argv 透传语义（PIPE-02）
- **D-10（open Q7 裁决）:** auto-GA = **乘积语义**：`GA = max(1, effective_batch // bs_new)`，与现有 `run_finetune.py --effective_batch_size`（`:167/:1300-1310`）完全一致；`bs_new` 为动态缩放后的实际 per-device batch。**不是**"覆盖全训练集"语义（N//batch 的 N 指有效批量目标值，非训练行数）。
- **D-11:** sweep 层旗标**沿用下划线名 `--effective_batch_size`**（与仓库 `--target_model`/`--train_fraction` 风格一致，零别名映射）。
- **D-12:** **裸旗标=16、缺席=不改**：argparse `nargs='?'` `const=16`；完全缺席 = 不透传给子进程 = 逐字节今日行为（YAML GA 生效）。"默认 16" 由此落地。
- **D-13:** `sweep_manifest.json` cell **在场才记**：四旗标在场时增记对应字段（如 `effective_batch_size: 16`）；缺席时字段不出现，保持字节确定性（现有 manifest 字节确定性测试不动）。
- **D-14:** `--subset_file` 在 **sweep 层预校验**：启动前校验（键在注册表内、结构合法），问题一次性全列出后 exit 非零（与 unknown-filter fail-fast 纪律一致）；不是放给子进程逐 cell 报错。
- **D-15:** `--cache_dir` / `--subset_file` sweep 层**先转绝对路径再透传**（与 `--output_dir` 绝对路径纪律一致；子进程 cwd 钉在 pipeline/）。
- **D-16:** `--num_train_epochs` 优先级**确认现有语义**：旗标覆盖 config（`run_finetune.py:950` 已文档化）；sweep 纯透传不重复裁决。

### 容错 loader 契约（PIPE-03）
- **D-17:** **解析级容错**：覆盖 OSError（缺失/不可读）、`json.JSONDecodeError`、空文件；结构有效但缺字段的 JSON **不算损坏**（键级检查归调用方）。
- **D-18:** **无状态 + 哨兵**：loader 损坏时返回 None（或抛特定异常），调用方保留自己的 last-known-good；loader 不内置缓存（可测性、多进程安全）。
- **D-19:** 落点 **`pipeline/artifact_loader.py`**（纯函数、零重依赖）；Phase 8 `tui/services/` import 它（依赖方向 tui→pipeline，与研究结论一致）。
- **D-20:** Phase 7 loader **仅覆盖 flops_report.json 读取**（契约测试锁定）；run_sweep 现有两处容错读取（`:537-540`/`:1107-1109`）**不动**（surgical 纪律，WR-11 测试已锁）；Phase 11 monitor 接入时再评估替换。

### 验证深度（含纪律变更）
- **D-21（维护者 2026-10-11 裁定）:** **code-only 限制取消，现在可以用 GPU** —— 有界 GPU 运行/smoke 作为普通计划步骤无需中途再授权；**E2' 全量三种子 sweep 仍维护者双门**；CI 仍无 GPU/dnallm。长期记忆已更新。
- **D-22:** Phase 7 含 **GB10 FLOPs smoke**：单常规架构模型（BERT 系最小最快）×1 任务×1 种子×1 epoch；exotic 架构（Mamba/Hyena/evo2 等）靠 CPU stub 单测锁分派逻辑。
- **D-23:** smoke 过门判定 = **发射+合理性**：flops_report.json 成功落盘、主层钩子命中、uncovered 低于阈值、FLOPs 数量级 sane（与参数量×token 数粗估同阶）；**无 legacy 逐位对账**（架构/配置链已漂移，对账含义有限）。
- **D-24:** **executor 执行** smoke（本机即 GB10，[gpu] venv + dnallm 1.2.1 已就绪并经 Phase 6 四次 smoke 验证）；计划里显式标注 GPU 步骤。

### smoke 产物与 schema 契约
- **D-25:** smoke 为**计划内步骤**（命令+预期输出写进 PLAN，执行后贴实录留证）；不做常驻 make 目标。
- **D-26:** 测试用**合成 flops_report fixture**（CPU 确定性生成）；真跑产物**不入库**（机器相关），计划执行记录贴关键字段摘要。
- **D-27:** `flops_report.json` 上**严格 JSON Schema**（`schemas/flops_report.json`，与 Phase 2 既有 schema 纪律对齐）+ 顶层 **`schema_version: 1`** 字段留演进余地 + 合成 fixture 校验测试；hardware 节为可选节。— **Reversibility:** one-way — schema 一旦发布即为对外契约（v1 字段名与结构被 monitor/排行榜消费）。

### Claude's Discretion
- FlopsCounter 新模块的具体文件名与内部结构（前提：torch 延迟导入/stub 可测、run_finetune 集成点最小侵入）
- registry_loader / artifact_loader 的函数签名与异常类型设计
- uncovered 阈值的具体数值（建议从 legacy 行为推导，给 planner 留白）
- D-04 删除旧文件时对残留引用的清理范围（docs/注释同步更新）
- smoke 具体选哪个注册表模型（"最小可跑 + 分钟级"原则）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 计划权威（phase 定义与约束）
- `.planning/ROADMAP.md` §"v1.2 TUI任务 — Milestone Goal & Binding Constraints"（11 条绑定约束，尤其 6/9/11）+ §"Phase 7"（目标与 5 条成功判据）
- `.planning/REQUIREMENTS.md` §Pipeline-side（PIPE-01/02/03）+ §Custom Entries（CUST-05）
- `.planning/PROJECT.md` §Key Decisions（auto-GA 政策、v1.2 范围决策）+ §Context（GB10 环境现状）

### 研究结论（2026-10-11，HIGH 置信度架构/栈事实）
- `.planning/research/SUMMARY.md` — WP-A FlopsCounter 移植序、P2.5 旗标先落、Gaps 节（open Q7 已由本 CONTEXT D-10 裁决关闭）
- `.planning/research/ARCHITECTURE.md` §构建序（WP-A→…）+ 文件系统即 API 三锚点

### 移植源与目标文件
- `pipeline/dnallmmark_pipeline.py` — legacy `FlopsCounter`（`:43` 类、`:66` `_register_hooks`、`:676` `save_to_json`）与 20+ 钩子闭包工厂（移植源；移植后删除）
- `pipeline/run_finetune.py` — 移植目标；四旗标已存在（`--cache_dir:138`/`--effective_batch_size:167`/`--subset_file:188`/`--num_train_epochs:211`）；模块级注册表加载 `:674-679`；`_peek_cache_dir:5`；动态批量 `:537`
- `pipeline/run_sweep.py` — 透传目标；`build_argv:810`（LIST argv 纪律）；三处注册表加载 `:368/:474/:514`；容错读取先例 `:537-540/:1107-1109`
- `script/audit_n_frequencies.py:599` — audit 侧注册表加载点（overlay 触点）

### 测试与契约先例
- `tests/test_sweep.py` — argv-parity 测试形态（`test_launch_subprocess_builds_argv_list_with_pinned_cwd`、absent-filter 字节一致性、manifest 字节确定性）
- `tests/test_run_finetune_contracts.py` — run_record 契约（FLOPs 不得扰动）
- `schemas/` — Phase 2 严格 schema 先例（flops_report schema 对齐对象）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **legacy `FlopsCounter`**（`pipeline/dnallmmark_pipeline.py:24-689`）：20+ 架构钩子分派（Bert/Mistral/Llama-Gemma GQA/BigBird/Hyena/Mamba-Mamba2/Caduceus/Enformer/Borzoi/megaDNA…），闭包工厂模式 `_xxx_hook(name)`，`save_to_json` 按 per-token FLOPs 外推全训练 —— 逐段移植源
- **`run_sweep.py` 纯函数**（`enumerate_matrix:333`）：可导入预览的既有先例（tui→pipeline 依赖方向）
- **`run_finetune.py` 既有机制**：`determine_batch_size:537`（WR-04 层级批量）、`--effective_batch_size` GA 调整 `:1300-1310`、`_peek_cache_dir:5`（HF_HOME 先于 import 设置）、`validate_subset_file:276`
- **容错读取先例**：`run_sweep.py:537-540`（OSError/JSONDecodeError）与 `:1107-1109`（损坏 metrics 只 fail cell 不炸 sweep，WR-11 测试锁定）
- **`tests/test_sweep.py` argv 断言形态**：LIST argv 逐元素断言 + 缺席旗标字节一致 —— 四旗标 parity 测试直接套用

### Established Patterns
- **缺席=逐字节一致**：所有新增面（四旗标、overlay、hardware 节除外——FLOPs 是 always-on 新产物）以"不传即零 argv 元素/零行为变化"为纪律，测试锁定
- **LIST argv + 绝对路径**：子进程 argv 恒为 list；路径类旗标 sweep 层转绝对（cwd 钉 pipeline/）
- **fail-fast 全列问题**：unknown-filter / from-failures 校验先例 —— subset 预校验沿用
- **模块级单源**：D-10 registry JSON 单源先例 → 共享 loader 模块
- **严格 schema + 合成 fixture**：Phase 2 纪律 → flops_report schema 对齐

### Integration Points
- `run_finetune.py` 训练循环（DNATrainer 构造 `:1444` 前后）：FlopsCounter 挂钩点 + hardware/runtime 采集点 + flops_report.json 写入点（final_metrics 写入窗口附近）
- `run_sweep.py:build_argv:810`：四旗标追加元素落点（peft/train_fraction 追加先例）
- `run_sweep.py` manifest cell 构造（`:960-975`）：在场才记字段落点
- 五处注册表加载点：overlay loader 接入
- `schemas/` + `tests/`：flops_report schema 与 fixture 落点

</code_context>

<specifics>
## Specific Ideas

- 维护者示例的 GPU 平台记录值："5090，RTX6000, 4090, 5090D, 4090D等" —— 捕获即 `torch.cuda.get_device_name()` 实报字符串（含中国特供型号 5090D/4090D），不做规范化映射
- 维护者原话（纪律变更）："现在可以用GPU，不用再再code-only 了，code-only 限制取消"
- "宁可噪声不可静默少计"：uncovered 报告的指导原则（与正确性品牌一致）

</specifics>

<deferred>
## Deferred Ideas

- **榜单/前端展示训练平台（GPU 型号）列与训练时间列** —— 展示层工作，牵动 leaderboard schema/goldens/前端多页面，超出 Phase 7 边界；未来单独安排（届时 flops_report/数据链的 hardware 数据已就位）

None — discussion stayed within phase scope (除上条维护者补充的展示侧延伸)

</deferred>

---

*Phase: 7-Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay)*
*Context gathered: 2026-10-11*
