# Phase 8: TUI Foundation (Env Check & Selection) - Context

**Gathered:** 2026-10-11
**Status:** Ready for planning
**Mode:** `--auto`（全部灰区自动选定推荐项，决策留审计轨迹于 DISCUSSION-LOG.md）

<domain>
## Phase Boundary

控制台"静止时可信赖"（trustworthy at rest）。本相交付两块可见能力 + 全部不可回填架构：

1. **ENV-01..04 启动环境检查面板**：复用 `pipeline/env_smoke.py` 检查内核（版本 pin / dnallm 导入 / CUDA / 数据集目录 / numpy≥2 / peft），逐项 ✓/✗ + 详情下钻；结果持久化带检查日期（"上次检查: YYYY-MM-DD HH:MM"），同日重启读缓存、手动刷新强制重检；关键 FAIL 可见阻断（原因展示），缺数据项路由数据管理；轻量快检内核（启动所需子集重验）
2. **SEL-01..04 + I18N-01 k9s 式选择面**：模型/数据集列表独立浏览（62/50，关键卡片字段为列），arena/类型/物种/规模过滤 + 空格标记进稳定 row_key 集合；预设一键选择（tier-1 E2E 对、tier-2 arena 代表、全部、自定义保存）；运行配置模板 JSON 导入/导出（校验）与 `sweep_priorities.json` tier 互转；每行本地数据在场列（✓/✗ + n_audit 行数）；中文为主界面文案（constants 模块，术语保留英文）；只读矩阵总览为辅助视图
3. **非可回填地基**：textual-free 服务层（import 测试锁定）、`[tui]` 依赖组（textual `>=8.2,<9` + platformdirs）、`make tui` 入口、双层测试骨架（tier-1 无头服务测试 CI-safe + tier-2 Pilot）、容错 artifact loader 复用、constants 模块 i18n 约定 —— 后续相位加屏幕而非改架构

**不在本相**：数据下载/校验面板（Phase 10）、运行配置屏与实际启动流（Phase 11）、监控（Phase 11）、多卡（Phase 12）。E2' 全量 sweep 仍维护者双门；本相无任何管线执行。

</domain>

<decisions>
## Implementation Decisions

### CI textual 测试通道（约束 2 批准项）
- **D-01:** **批准 textual-the-library 进 CPU CI 测试通道**（library yes, display/GPU runtime no）：现有 CI test job 的 `uv sync` 增加安装 `[tui]` 组（textual + platformdirs），Pilot 测试以 headless driver 运行（无显示、无 GPU、无 dnallm）；**零新增 CI job**；data/gpu lane 永不见 textual。— **Reversibility:** reversible — CI 配置一处改动即可撤销。

### env_smoke 内核复用（ENV-01）
- **D-02:** **结构化返回重构**：将 `pipeline/env_smoke.py` 各检查内核（`check_numpy`/`check_version_pins`/`check_dnallm`/`check_peft`/`check_cuda`/`check_dataset_dirs`/`check_matmul`）重构为返回结构化结果（名称/状态/详情），`main()` 的 **PASS:/FAIL: 打印行与退出码契约逐字节保持**（E2' 双门的 greppable 契约，现有测试锁定不动）。TUI 服务层 **import 内核**（tui→pipeline 依赖方向），绝不子进程解析 stdout、绝不在 TUI 重写检查。— **Reversibility:** costly — env_smoke 的 PASS/FAIL 行是 E2' 门对外契约，重构后必须保持 CLI 输出不变，回退牵动内核结构。
- **D-03:** **检查执行绝不阻塞事件循环**：全量检查在 worker thread（`@work(thread=True)`）运行，逐项结果异步回填面板；同日缓存命中时即时呈现。GPU 触碰内核（CUDA/matmul）只在真机（GB10）上实际执行；CI 服务测试用注入 fake，不跑真内核。

### XDG 持久化布局（ENV-02 / SEL-02 / SEL-03）
- **D-04:** **state 与 config 分离**（platformdirs 双根）：环境检查结果（含时间戳、逐项状态）→ XDG **state** dir（Linux `~/.local/state/dnallmmark/env_check.json`）；用户保存的预设/模板/会话选择/设置 → `~/.config/dnallmmark/`（与 Phase 7 custom registries 同根，D-06/D-07 先例延续）。测试经 env-var 注入临时目录（沿用 `DNALLMMARK_CUSTOM_REGISTRY_DIR` 整目录覆盖先例；TUI 侧具体变量名 planner 定）。— **Reversibility:** reversible — 布局选择，未发布前可调。
- **D-05:** **缓存语义**：同日 = 日历日比较（"上次检查"日期可见）；手动刷新动作强制全量重检；部分失败也整体持久化（逐项状态带 FAIL 详情），下次启动直接呈现失败项。快检（ENV-04）不落盘为"全量结果"——它是启动前的轻量子集重验，结果即算即用。

### 预设与模板（SEL-02 / SEL-03）
- **D-06:** **预设从 `pipeline/sweep_priorities.json` 派生**（单一来源，零硬编码重复）：tier-1 E2E 对、tier-2 arena 代表由服务层读该文件派生；"全部" = overlay 合并注册表（`pipeline/registry_loader.py`，Phase 7 CUST-05）全量；"自定义保存" = 用户 XDG 文件。选择集以注册表键名为稳定 row_key。— **Reversibility:** reversible。
- **D-07:** **模板走 schemas/ 严格 JSON Schema 纪律**（Phase 2 先例）：运行配置模板（模型×任务×种子×PEFT×变体×GA 完整参数集）定义 `schemas/` 下 schema + 顶层 `schema_version` 字段；导入时 jsonschema 校验、失败一次性全列问题（fail-fast 全列纪律）；`sweep_priorities.json` tier 互转作为服务层纯函数。**Phase 11 run-config 屏消费同一 schema** —— 模板 schema 是跨相契约。— **Reversibility:** one-way — schema 一旦发布即为对外契约（模板文件会被分享/复用，字段名被 Phase 11 消费）。

### 在场列与数据路由（SEL-04）
- **D-08:** **在场列读已提交产物，TUI 零计算**：每行 ✓ 在场 / ✗ 缺失 + 行数来自 `dnallm-mark/data/n_audit.json`（`script/audit_n_frequencies.py` 的既定产物：每任务 train/dev/test 行数、缺失标记——TUI-REQUIREMENTS 资产盘点已列）；刷新走 audit 重跑（CLI 先例，Phase 10 数据管理器接管面板化）。启动时的**活体**目录检查用 env_smoke `check_dataset_dirs` 内核（D-02），浏览行的**静态**来源是 n_audit.json。缺数据项路由数据管理（Phase 8 呈现指引，面板本体 Phase 10）。— **Reversibility:** reversible。

### ENV-03/ENV-04 相边界
- **D-09:** **门判定现在落地，阻断钩子 Phase 11 接线**：Phase 8 交付 env-gate 判定服务（纯逻辑：哪些 FAIL 关键、何为可启动）+ 面板可见呈现（关键 FAIL 的醒目状态与原因、缺数据引导）+ 快检内核（launch-required 子集轻量重验，服务化）。实际"阻止进入启动流程"与"每次启动任务前快检"的调用点在 Phase 11 启动屏接线 —— 本相无启动流可阻断，不做空转交互。— **Reversibility:** reversible。

### 依赖与整合纪律
- **D-10:** **registry_loader 不做 platformdirs 整合**：保持 Phase 7 手写 env>XDG>home stdlib 解析器不动（pipeline 侧 stdlib 纯度 load-bearing：sweep 无头导入、data/gpu lane 零新依赖）；TUI settings 服务直接用 platformdirs。整合无收益只有审面 —— 记 Deferred。— **Reversibility:** reversible。

### Claude's Discretion
- `tui/` 包内部结构（`app.py` 组合根、`screens/`、`services/`、constants/strings 模块命名——research 建议的骨架为准）
- 选择屏具体 UI 形态（模型/数据集独立浏览的实现：单屏切换 vs tab；矩阵辅助视图入口）——k9s 心智模型为准（type-to-filter、空格标记、键盘优先）
- env-check 面板异步填充 UX（逐项 spinner、详情下钻呈现）
- i18n constants 模块具体结构与文案键组织
- TUI 侧测试 env-var 的具体变量名与 settings 服务 API 形状
- Pilot（tier-2）测试的具体断言集与 fake 注入形态
- tier 预设派生函数与模板互转函数的签名
- 实现期建议加载 `tui-design` skill（终端 UI 打磨规范）——执行 agent 的实现质量工具，非架构约束

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 计划权威（phase 定义与约束）
- `.planning/ROADMAP.md` §"v1.2 TUI任务 — Milestone Goal & Binding Constraints"（11 条绑定约束，尤其 2/4/5/9/10）+ §"Phase 8"（目标与 5 条成功判据，"UI hint: yes"）
- `.planning/REQUIREMENTS.md` §环境检查（ENV-01..04）+ §选择（SEL-01..04）+ §国际化（I18N-01）+ 覆盖矩阵（8 项全 Pending 归 Phase 8）
- `.planning/PROJECT.md` §Context（GB10 环境现状、autorun 分支流）+ §Key Decisions

### 团队需求收集（用户侧权威）
- `docs/TUI-REQUIREMENTS.md` — §2 现有资产盘点（n_audit.json/env_smoke/sweep_priorities 等复用清单）、§3.1 选择域、§3.6 环境与安全边界、§4 非功能（~/.config/dnallmmark/ 持久化、中文界面）、§5 开放问题 #7（GA 答复=auto-GA 语义，Phase 7 D-10 已落地）

### 研究结论（2026-10-11，HIGH 置信度）
- `.planning/research/SUMMARY.md` — 架构姿态（thin read-plan-launch-observe shell）、[tui] 组构成、双层测试（tier-1 headless / tier-2 Pilot + fakes）、5 行 import 测试锁服务层 textual-free、P1 不可回填决策清单
- `.planning/research/ARCHITECTURE.md` — tui/ 包骨架（app.py 组合根 / screens/ / services/ 各服务职责）、SSH/tmux 韧性模式

### 前相决策（直接依赖）
- `.planning/phases/07-pipeline-side-enablement-flopscounter-port-argv-threading-re/07-CONTEXT.md` — D-06/D-07（overlay 自动探测 + env 覆盖先例）、D-17..D-20（容错 loader 契约与 `pipeline/artifact_loader.py` 落点、tui→pipeline 依赖方向）

### 复用源码与产物
- `pipeline/env_smoke.py` — 检查内核（`check_numpy:174`/`check_version_pins:251`/`check_dnallm:279`/`check_peft:288`/`check_cuda:314`/`check_dataset_dirs:341`/`check_matmul:386`/`main:411`）；PASS:/FAIL: 打印契约 BINDING（E2' 门）
- `pipeline/sweep_priorities.json` — tier 结构（预设派生单一来源，list 形态）
- `pipeline/registry_loader.py` — overlay 合并视图（选择面读它，62 模型含 custom）
- `pipeline/artifact_loader.py` — 容错 JSON loader（tui/services 直接 import，D-19）
- `dnallm-mark/data/n_audit.json` + `script/audit_n_frequencies.py` — 在场列数据源（行数 + 缺失标记）
- `pipeline/models_info.json` / `pipeline/datasets_info.json` — 注册表本体（62 模型 11 键卡片 / 50 数据集含溯源列）
- `pyproject.toml` §[dependency-groups] — `[tui]` 组落点（现有 data/dev/gpu）
- `Makefile` — `make tui` 目标落点（现有 lint:130/typecheck:139/test:89 先例）
- `schemas/` — 严格 schema + 合成 fixture 纪律先例（模板 schema 对齐对象）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **env_smoke 检查内核**（`pipeline/env_smoke.py`）：7 项检查已是独立函数、pin 从 pyproject.toml 读取（零双写）——结构化返回重构的现成切面
- **`run_sweep.py` 纯函数**（`enumerate_matrix`/优先级序）：选择预览可导入复用（先例已立）
- **registry_loader 合并视图**：选择面 62 模型（官方+custom overlay）单一入口
- **artifact_loader 容错契约**：服务层读 JSON 的统一路径（D-19 落点已定）
- **n_audit.json 已提交产物**：SEL-04 在场列零成本数据源
- **uv 依赖组基建**：`[tui]` 组照 `[gpu]` 先例添加（floor 在 pyproject、精确 pin 在 uv.lock）

### Established Patterns
- **缺席=逐字节一致 + import 测试锁定**：服务层 textual-free 测试照 Phase 7 模式（5 行 import 测试）
- **fail-fast 全列问题**：unknown-filter/subset 预校验先例 → 模板导入校验沿用
- **严格 schema + schema_version + 合成 fixture**：Phase 2/flops_report 先例 → 模板 schema 沿用
- **env-var 整目录覆盖**（`DNALLMMARK_CUSTOM_REGISTRY_DIR`）→ TUI 测试注入沿用形态
- **Makefile 目标 + `uv run --group`**：`make tui` 照 `make test`/`make lint` 先例

### Integration Points
- `pyproject.toml` `[dependency-groups]` + `uv.lock`：textual `>=8.2,<9` + platformdirs 入 `[tui]`；`pytest-asyncio` 入 dev（research 结论）
- `Makefile`：`tui:` 目标（`uv run --group tui python -m tui`）；lint/typecheck 增覆盖 `tui/`
- CI workflow（现有 test job）：sync 增 `--group tui`（D-01）
- `.gitignore`：XDG 产物不涉及（用户主目录）；`tui/` 新包入仓库
- services → pipeline 导入边界：`artifact_loader`/`registry_loader`/env_smoke 内核（方向恒 tui→pipeline）

</code_context>

<specifics>
## Specific Ideas

- 维护者对 GA 参数的原话（开放问题 #7）：先定 16，小模型起始 batch size 超过 16（如 64）时 GA=1 —— 即 Phase 7 D-10 的 `GA = max(1, effective_batch // bs_new)` 乘积语义，模板 schema 的 GA 字段按此语义呈现
- TUI-REQUIREMENTS §3.1 已勾项："选择结果导出为 run_sweep 的 `--models`/`--tasks` 参数或 priorities 文件" —— Phase 8 的选择产物即 D-06/D-07 的预设/模板 JSON + priorities 互转；argv 物质化归 Phase 11 run-config
- "上次检查: YYYY-MM-DD HH:MM" 为 ENV-02 原文措辞（中文界面实例）
- 62 模型 = 41 官方注册表 + custom overlay 上限语义（roadmap 口径）；50 数据集固定

</specifics>

<deferred>
## Deferred Ideas

- **目录设置**（TUI-REQUIREMENTS §4 未勾项：项目根与存储根分离配置、显式覆盖时 TUI 传参给下游脚本）→ Phase 11 run-config/设置面；Phase 8 settings 服务设计不预设死路径假设
- **registry_loader platformdirs 整合**（STATE 遗留开放项）→ D-10 裁定不做；除非维护者提出否则永久搁置
- **前端展示训练平台（GPU 型号）列**（Phase 7 延续）→ 展示层工作，未来单独安排

</deferred>

---

*Phase: 8-TUI Foundation (Env Check & Selection)*
*Context gathered: 2026-10-11*
