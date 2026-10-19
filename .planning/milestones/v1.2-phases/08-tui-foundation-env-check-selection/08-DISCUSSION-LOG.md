# Phase 8: TUI Foundation (Env Check & Selection) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-11
**Phase:** 8 - TUI Foundation (Env Check & Selection)
**Mode:** `--auto` — no interactive prompts; every gray area auto-selected with the recommended option, per maintainer's standing `--auto` invocation. Choices logged here for audit; maintainer may override any D-number before/after planning.
**Areas discussed:** CI textual 通道批准, env_smoke 内核复用机制, XDG 持久化布局, 预设派生源, 在场列数据来源, registry_loader platformdirs 整合, 模板 schema 纪律, ENV-03/04 相边界

---

## CI textual 通道批准

| Option | Description | Selected |
|--------|-------------|----------|
| 批准——现有 job 扩 sync | 现有 CI test job 增装 [tui] 组，Pilot headless driver 跑（无显示/GPU/dnallm），零新 job | ✓ |
| 不进 CI 仅本地 | Pilot 只在本地跑，CI 只测 tier-1 服务层 | |
| 新增独立 CI job | 单独 textual 测试 job | |

**User's choice:** [auto] recommended default
**Notes:** 约束 2 明确把"textual-the-library 允许进 CPU 测试通道"留作 Phase 8 discuss 批准项 —— 本讨论即为批准记录（library yes, display/GPU runtime no）。"新增独立 CI job" 违反零新 job 约束，仅列为对照。

## env_smoke 内核复用机制

| Option | Description | Selected |
|--------|-------------|----------|
| 结构化返回重构 | 内核函数返回结构化结果，CLI PASS:/FAIL: 打印契约逐字节保持，TUI import 内核 | ✓ |
| 子进程解析 stdout | TUI 起 env_smoke 子进程并解析打印行 | |
| TUI 内重写检查 | 在 tui/services 重写检查逻辑 | |

**User's choice:** [auto] recommended default
**Notes:** env_smoke 的 PASS/FAIL 行是 E2' 双门的 greppable 对外契约（模块 docstring 自称 contract），重构必须保持 CLI 输出不变。子进程解析脆且丢结构化详情；重写违反"TUI orchestrates, never computes"。

## XDG 持久化布局

| Option | Description | Selected |
|--------|-------------|----------|
| state 与 config 分离 | 检查结果 → XDG state dir；用户预设/模板/设置 → ~/.config/dnallmmark/（与 custom registries 同根） | ✓ |
| 全部 ~/.config/dnallmmark/ | 简单但混入机器态数据 | |
| 仓库内 gitignored | 便携但多机/多用户不适 | |

**User's choice:** [auto] recommended default
**Notes:** platformdirs 双根；测试 env-var 整目录注入照 DNALLMMARK_CUSTOM_REGISTRY_DIR 先例。TUI-REQUIREMENTS §4 已勾 "~/.config/dnallmmark/？"

## 预设派生源

| Option | Description | Selected |
|--------|-------------|----------|
| sweep_priorities.json 派生 | tier-1/tier-2 由服务层读该文件派生；all = overlay 全量；custom = 用户 XDG | ✓ |
| tui/constants 硬编码 | tier 定义写死在 TUI 常量 | |

**User's choice:** [auto] recommended default
**Notes:** 单一来源避免双源漂移（sweep 执行侧同一文件消费优先级）。

## 在场列数据来源

| Option | Description | Selected |
|--------|-------------|----------|
| n_audit.json 产物 | 读已提交 dnallm-mark/data/n_audit.json（行数+缺失标记），刷新走 audit 重跑 | ✓ |
| TUI 现场扫描 | 浏览时扫 pipeline/datasets/ 即时统计行数 | |

**User's choice:** [auto] recommended default
**Notes:** TUI-REQUIREMENTS §2 资产盘点明确列 n_audit 为复用资产；现场统计重复实现 audit 语义（违反 never-computes）且有 50 行扫描成本。启动时活体检查仍用 env_smoke check_dataset_dirs 内核（静态浏览 vs 活体启动双路径）。

## registry_loader platformdirs 整合

| Option | Description | Selected |
|--------|-------------|----------|
| 不整合 | registry_loader 保持 stdlib 手写解析器；TUI settings 直接用 platformdirs | ✓ |
| Phase 8 顺手替换 | registry_loader 也换 platformdirs | |

**User's choice:** [auto] recommended default
**Notes:** STATE 遗留开放项（"Phase 8 may consolidate"）。pipeline 侧 stdlib 纯度 load-bearing（sweep 无头导入、lane 隔离约束）；替换无用户可见收益、扩大审面，违反 surgical 纪律。

## 模板 schema 纪律

| Option | Description | Selected |
|--------|-------------|----------|
| schemas/ 严格 schema | schemas/ 下 JSON Schema + schema_version + 合成 fixture；导入校验 fail-fast 全列；priorities 互转纯函数 | ✓ |
| 手写校验代码 | services 里手写字段检查 | |

**User's choice:** [auto] recommended default
**Notes:** Phase 2 / flops_report（D-27）双先例；Phase 11 run-config 屏消费同一 schema，跨相契约按 one-way 对待。

## ENV-03/04 相边界

| Option | Description | Selected |
|--------|-------------|----------|
| 服务+呈现现在，钩子 Phase 11 | env-gate 判定服务、面板可见呈现、快检内核现在落地；阻断调用点 Phase 11 启动屏接线 | ✓ |
| Phase 8 完整阻断交互 | 现在就做阻断流程 | |

**User's choice:** [auto] recommended default
**Notes:** 本相无启动流可阻断，空转交互无验证对象；判定逻辑与呈现先落地并 CPU 可测。

---

## Claude's Discretion

- tui/ 包内部结构（组合根/screens/services/constants 模块命名，research 骨架为准）
- 选择屏 UI 形态细节（k9s 心智模型：type-to-filter、空格标记、键盘优先）
- env 面板异步填充 UX、详情下钻呈现
- 测试 env-var 具体命名、settings 服务 API 形状
- Pilot 断言集与 fake 注入形态
- 预设派生/模板互转函数签名

## Deferred Ideas

- 目录设置（项目根/存储根分离配置 + 下游传参）→ Phase 11
- registry_loader platformdirs 整合 → 不做（除非维护者提出）
- 前端 GPU 平台列展示 → Phase 7 延续项
