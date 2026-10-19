# Phase 7: Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-11
**Phase:** 7-Pipeline-Side Enablement (FlopsCounter Port, argv Threading & Registry Overlay)
**Areas discussed:** FLOPs 启用与输出契约, Overlay 激活机制, effective-batch 语义, Phase 7 验证深度, 容错 loader 语义边界, 其余三旗标语义, smoke 产物处置 + flops_report schema 契约

---

## FLOPs 启用与输出契约

| Option | Description | Selected |
|--------|-------------|----------|
| Always-on（推荐） | 每个 run 自动挂钩并写报告，与旧管线行为一致；E2' 无需记得加旗标；无额外旗标面 | ✓ |
| --flops 旗标 opt-in | 默认不测量，显式传旗标才挂钩；E2' 忘传旗标就丢 FLOPs 数据 | |
| 默认开 + --no-flops | 默认测、可关；多一个旗标面 | |

**User's choice:** Always-on（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 独立 flops_report.json（推荐） | 沿用 legacy 文件名与 schema，落在 run 输出目录；不动 run_record 契约；monitor/容错 loader 直读 | ✓ |
| 并入 run_record.json | 单一 artifact 好聚合，但需改现有 schema/测试契约 | |
| 两者都要 | 双写一致性多一套 | |

**User's choice:** 独立 flops_report.json（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 响亮报告 uncovered（推荐） | 未命中层归为 uncovered 显式列出，超阈值 WARNING；宁可噪声不可静默少计 | ✓ |
| 沉默（legacy 保真） | 未命中不计不报告；静默少计风险延续到 62 模型注册表 | |
| 覆盖审计 + 补钩 | 先盘点 62 模型架构 vs 钩子覆盖，未覆盖的本 phase 补齐 | |

**User's choice:** 响亮报告 uncovered（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 删除（推荐） | Phase 3 已废弃，git 历史即参考；缩小审查面 | ✓ |
| 保留 deprecated | 零风险但公开仓库多一个 1200+ 行死文件 | |

**User's choice:** 删除（推荐）

**[维护者中途补充]** 训练时间统计 + 训练平台（GPU 型号：5090/RTX6000/4090/5090D/4090D 等）：

| Option | Description | Selected |
|--------|-------------|----------|
| 进 flops_report（推荐） | hardware/runtime 节（gpu_device/train_time/max_mem_gb）；run_record 契约零改动 | ✓ |
| 进 final_metrics/run_record | 经现有通道流入 run_record.metrics，但触碰现有契约 | |
| 两者都要 | 双写 | |

**User's choice:** 进 flops_report（推荐）；范围 = 仅管线侧（推荐），前端展示 deferred。

---

## Overlay 激活机制

| Option | Description | Selected |
|--------|-------------|----------|
| 自动探测（推荐） | 文件存在即加载，缺失 = 逐字节今日行为；零记忆负担 | ✓ |
| 显式旗标 opt-in | 行为最可控，但向导落地后多一步记忆 | |
| 自动 + 关闭开关 | 默认自动、可 --no-custom-registry 关闭；多旗标面 | |

**User's choice:** 自动探测（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 单目录 env var（推荐） | DNALLMMARK_CUSTOM_REGISTRY_DIR 覆盖整个目录；测试 tmp_path 注入 | ✓ |
| 每文件 env var | 两个独立 var，可只覆盖一边；面大一点 | |
| 仅参数注入 | loader 函数显式参数、CLI 写死默认；最少对外接口但换路径要改代码 | |

**User's choice:** 单目录 env var（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 共享 loader 模块（推荐） | pipeline/registry_loader.py，全部加载点改走它；单源（D-10 先例） | ✓ |
| 各点就地微改 | 不动调用结构，但四处重复逻辑易漏接 | |

**User's choice:** 共享 loader 模块（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 不动 export（推荐） | 已核实 export_runs.py 运行时不读注册表；自定义条目经 run 自然流入 | ✓ |
| export 也加加载 | 增加面，需另行论证 | |

**User's choice:** 不动 export（推荐）

---

## effective-batch 语义

| Option | Description | Selected |
|--------|-------------|----------|
| 乘积语义（推荐） | GA = max(1, effective_batch // bs_new)，与现有 --effective_batch_size 完全一致；"默认 16" 自然成立 | ✓ |
| 覆盖全训练集语义 | GA = N_train // batch，每 epoch ≈ 一次优化器步；与现有实现冲突且"默认 16"无意义 | |

**User's choice:** 乘积语义（推荐）—— 研究 open Q7 就此关闭

| Option | Description | Selected |
|--------|-------------|----------|
| 沿用下划线名（推荐） | --effective_batch_size，与仓库旗标风格一致，零别名映射 | ✓ |
| 连字符名+映射 | --effective-batch 透传时映射；文档好看但多一层记忆 | |

**User's choice:** 沿用下划线名（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 裸旗标=16，缺席=不改（推荐） | nargs='?' const=16；完全缺席 = 不透传 = 逐字节今日行为 | ✓ |
| 必带值 | 更严格但"默认 16"只剩 TUI 预填含义 | |

**User's choice:** 裸旗标=16，缺席=不改（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 在场才记（推荐） | 旗标在场时 cell 增记字段；缺席时字段不出现，字节确定性保持 | ✓ |
| 都不记 | manifest 不变但事后难复原旗标配置 | |

**User's choice:** 在场才记（推荐）

---

## Phase 7 验证深度

| Option | Description | Selected |
|--------|-------------|----------|
| CPU + 授权 smoke（推荐） | Phase 7 内维护者授权一次 GB10 FLOPs smoke；风险最早暴露 | ✓（用户以自由文本升级） |
| 搭 Phase 11 顺带 | 真机验证搭 Phase 11 bounded smoke；零管线执行但 bug 晚两 phase | |
| 仅 CPU-stub | 无任何真机验证点 | |

**User's choice:** 自由文本："现在可以用GPU，不用再code-only 了，code-only 限制取消" —— **code-only 限制整体取消**（超出选项语义的纪律变更）：有界 GPU 运行作为普通计划步骤；E2' 全量仍双门；CI 仍无 GPU。长期记忆已更新。

| Option | Description | Selected |
|--------|-------------|----------|
| 单常规架构（推荐） | 注册表最小 BERT 系模型 ×1 任务；exotic 靠 stub 单测 | ✓ |
| 常规 + exotic 各一 | 真机验证两条钩子路径 | |
| 执行时再定 | planner/executor 提案再确认 | |

**User's choice:** 单常规架构（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 发射+合理性（推荐） | 落盘 + 主层命中 + uncovered 低于阈值 + 数量级 sane；无 legacy 逐位对账 | ✓ |
| 加 legacy 对账 | 证据最强但旧值可比性存疑 | |

**User's choice:** 发射+合理性（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| executor 跑（推荐） | Phase 6 先例；计划里显式标注 GPU 步骤 | ✓ |
| 维护者手跑 | 控制直接但反馈回路长 | |

**User's choice:** executor 跑（推荐）

---

## 容错 loader 语义边界

| Option | Description | Selected |
|--------|-------------|----------|
| 解析级容错（推荐） | OSError/JSONDecodeError/空文件；缺字段不算损坏 | ✓ |
| 解析+键级 | 必键缺失也当损坏；把 schema 知识烧进 loader | |

**User's choice:** 解析级容错（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 无状态+哨兵（推荐） | loader 返回 None/特定异常，调用方保 last-good | ✓ |
| loader 内置缓存 | 调用方零代码但隐藏状态多进程易错 | |

**User's choice:** 无状态+哨兵（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| pipeline/ 下（推荐） | pipeline/artifact_loader.py；Phase 8 tui/services import 它 | ✓ |
| 顶层共享包 | 超前（Phase 7 只有一个消费者） | |

**User's choice:** pipeline/ 下（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 仅 flops_report（推荐） | 契约测试锁定；sweep 现有读取不动（surgical） | ✓ |
| 连同 sweep 读取 | 统一纪律但扩大改动面 | |

**User's choice:** 仅 flops_report（推荐）

---

## 其余三旗标语义

| Option | Description | Selected |
|--------|-------------|----------|
| sweep 层预验（推荐） | 启动前校验 subset 文件，问题全列 exit 非零；与 unknown-filter 纪律一致 | ✓ |
| 放给子进程 | 零新增代码但问题暴露晚、逐 cell 撞错 | |

**User's choice:** sweep 层预验（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 转绝对路径（推荐） | 与 --output_dir 纪律一致；子进程 cwd 钉 pipeline/ | ✓ |
| 原样透传 | 调用方 cwd 不同时行为漂移 | |

**User's choice:** 转绝对路径（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 确认现有语义（推荐） | 旗标覆盖 config（run_finetune:950 已文档化）；sweep 纯透传 | ✓ |
| variant 优先 | 需改子进程逻辑，风险面大 | |

**User's choice:** 确认现有语义（推荐）

---

## smoke 产物处置 + flops_report schema 契约

| Option | Description | Selected |
|--------|-------------|----------|
| 计划内步骤（推荐） | 命令+预期写进 PLAN，执行后贴实录；不做 make 目标 | ✓ |
| 加 make 目标 | 方便反复手验但多维护入口 | |

**User's choice:** 计划内步骤（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 合成 fixture+摘要留证（推荐） | 测试 CPU 合成 fixture；真跑产物不入库，记录贴摘要 | ✓ |
| 脱敏真件入库 | 真实形状作金样但数值随环境漂移 | |

**User's choice:** 合成 fixture+摘要留证（推荐）

| Option | Description | Selected |
|--------|-------------|----------|
| 严格 schema+v1（推荐） | schemas/flops_report.json + schema_version: 1 + fixture 校验；Phase 2 纪律对齐 | ✓ |
| 仅测试断言 | 轻量但与四 schema 纪律不一致 | |
| schema 无版本 | YAGNI 但破坏性演进无迁移锄头 | |

**User's choice:** 严格 schema+v1（推荐）

---

## Claude's Discretion

- FlopsCounter 新模块文件名与内部结构（torch 延迟导入/stub 可测前提）
- registry_loader / artifact_loader 函数签名与异常类型
- uncovered 阈值具体数值（从 legacy 行为推导）
- 删除旧文件时残留引用清理范围
- smoke 具体模型选择（最小可跑 + 分钟级原则）

## Deferred Ideas

- 榜单/前端展示训练平台（GPU 型号）列与训练时间列 —— 展示层工作（牵动 leaderboard schema/goldens/前端多页面），另行安排
