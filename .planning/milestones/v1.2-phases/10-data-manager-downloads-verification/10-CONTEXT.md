# Phase 10: Data Manager (Downloads & Verification) - Context

**Gathered:** 2026-10-12
**Status:** Ready for planning
**Mode:** autonomous smart discuss(4 灰区,维护者逐区全收)

<domain>
## Phase Boundary

数据集缺口在启动前于会话内可关闭——注册表 `download_url` 为唯一权威的一键 ModelScope 下载、跨重启的持久化可续传队列、落地后对 n_audit 基线的行数对账,使 env-check 的 presence FAIL 总是可诊断、可修复。菜单槽 3(数据管理)本相位实装。

四件事:
1. **DATA-01 一键下载**:presence ✗ 行 `d` 键入队 → modelscope CLI 子进程下载(队列服务管理,串行)
2. **DATA-02 持久化队列**:XDG state dir 任务级状态机(pending/downloading/done/failed/mismatch),重启自动重排 pending+failed,通道自身续传
3. **DATA-03 行数对账**:落地后自动 audit 行数内核(子进程),mismatch 醒目报告不自动删;对账 pass → selection/env-check 双屏 presence 翻 ✓
4. **DATA-04 Zenodo 整包**:屏内整包入口,记录 19135551 公开探测;未公开禁用+说明(路线图注记:设计于本相位、公开后激活)

</domain>

<decisions>
## Implementation Decisions

### 下载通道与执行机制
- **D-01:** `modelscope` CLI 子进程通道(CLI parity;进度/失败输出可解析;凭据由 CLI 自取 `~/.modelscope`,TUI 零接触零存储零回显——SC5)
- **D-02:** 队列服务 + 每任务独立子进程;worker 线程(@work(thread=True))只管 spawn/收割/解析,绝不进程内下载(D-03 纪律延续)
- **D-03:** 队列屏逐项进度行(解析 CLI 进度输出);失败项 verbatim 日志下钻(env-check 同款模式)
- **D-04:** 串行队列(单任务执行,磁盘/带宽友好,对账有序)

### 队列持久化与恢复
- **D-05:** 队列状态入 XDG state dir(`~/.local/state/dnallmmark/download_queue.json`,与 env_check 状态同根——Phase 8 D-04 先例;`DNALLMMARK_TUI_STATE_DIR` 注入)
- **D-06:** 通道自身续传 + 任务级状态机;TUI 重启后 pending+failed 自动重排(downloading 视为中断转 pending)
- **D-07:** 落地但对账 mismatch:醒目报告、不自动删除(操作者决定;audit 重跑可刷新);"重新审计"动作刷新 n_audit 基线
- **D-08:** 队列条目 = 数据集键级(每缺失数据集一任务,对账同粒度)

### 对账与 Zenodo 入口
- **D-09:** 落地后自动对账:audit 行数内核子进程(Phase 9 gauntlet 同款纪律:LIST argv、临时输出、制品判据);结果进队列行 + mismatch 横幅
- **D-10:** 已提交 `dnallm-mark/data/n_audit.json` 为基线;屏内"重新审计"动作刷新基线(audit 脚本子进程)
- **D-11:** 对账 pass → selection 屏 presence ✗→✓ + env-check 数据集目录项同步(重读 n_audit 服务;SC1 后半)
- **D-12:** Zenodo 整包入口:记录 19135551 公开探测(URL HEAD/GET 检查);**未公开时按钮禁用 + 说明文案**;公开后激活为整包下载(单任务入队)

### 屏与导航整合
- **D-13:** 菜单槽 3(数据管理)变实屏:顶部缺失数据集清单(n_audit missing 集,可入队)+ 队列表(任务/状态/进度/行数对账列)
- **D-14:** 入队入口:selection 屏 presence ✗ 行 `d` 键;env-check FAIL 数据项路由跳槽 3(ENV-03 路由本相位落地)
- **D-15:** 底部子菜单:`d` 入队 / `r` 重试 / `x` 取消 / `a` 全部缺失入队 / `enter` 详情(verbatim 日志);右段恒定 `?` `q`
- **D-16:** 09-UI-SPEC 继承演进(同 Phase 9 模式);ui-researcher 加载 `tui-design` skill

### Claude's Discretion
- 队列文件 schema 具体形状(schema_version + 任务数组字段命名)
- CLI 进度输出的具体解析正则(以实测为准——研究阶段探针)
- 缺失清单与队列表的布局比例、列宽
- 公开探测的缓存时长与失败文案
- 取消语义细节(杀子进程 vs 等待落地后丢弃)
- audit 对账内核的复用形态(Phase 9 GauntletService 的 audit 腿 vs 直接子进程)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 计划权威
- `.planning/ROADMAP.md` §Phase 10(目标 + 5 条成功判据)+ 绑定约束 2/4/5(CI、CLI parity、TUI never-computes)
- `.planning/REQUIREMENTS.md` §Data Manager(DATA-01..04)
- `.planning/PROJECT.md` §Context(ModelScope 覆盖 50/50、SDK token 已存 ~/.modelscope)

### 前相决策(直接依赖)
- `.planning/phases/09-*/09-CONTEXT.md` D-13..16(导航壳契约——槽 3 本相位实装)+ D-02/D-03(子进程纪律)
- `.planning/phases/08-*/08-CONTEXT.md` D-04(XDG state 根)+ D-08(n_audit 在场源)
- `.planning/phases/09-*/09-RESEARCH.md`(audit 内核接口、staged 临时输出防串写——对账腿直接复用)

### 复用源码
- `pipeline/datasets_info.json` 的 `download_url` 列(唯一权威)+ 溯源列
- `script/audit_n_frequencies.py` + `dnallm-mark/data/n_audit.json`(对账基线与刷新)
- `tui/services/gauntlet.py`(子进程纪律、临时输出旗标、run-id 模式——下载/对账腿同款)
- `tui/services/custom_entries.py` 的 `_env_aware_config_root` 模式(队列 state 根同款)
- `tui/screens/nav.py`(槽位注册——占位变实屏)
- `tui/screens/env_check.py`(FAIL 项路由;worker/消息模式)
- `tui/screens/selection.py`(presence 列、`d` 键挂点)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- GauntletService 的 `_invoke`(LIST argv + env + timeout + 容错收割)——下载/对账子进程的模板
- n_audit 服务(tui/services/registries 的 presence_for)——缺失清单与 presence 翻转的既有读取面
- nav.py 槽位表:槽 3 从"未开放"占位换实屏注册
- run-id 消息防串(WR-02/WR-07 模式)——多任务队列事件流必备

### Established Patterns
- services 零 textual + AST 锁;tier-1 纯函数 + tier-2 Pilot 注入 fake
- 子进程纪律:LIST argv、绝对路径、临时输出、制品判据不信退出码
- XDG state 原子写(tmp+os.replace);env 整目录注入测试
- i18n 单一家 tui/strings.py

### Integration Points
- `tui/app.py` SCREENS/导航:槽 3 实屏注册
- `tui/screens/selection.py`:presence 列 ✗ 行 `d` 绑定
- `tui/screens/env_check.py`:数据集 FAIL 项的路由动作(跳槽 3)
- XDG state dir:新 download_queue.json(与 env_check.json 同根)

</code_context>

<specifics>
## Specific Ideas

- ModelScope 三通道(SDK/CLI、raw HTTP、git clone)已在 TUI-REQUIREMENTS 盘点;本相位走 CLI(维护者裁定)
- STATE 阻断注记:ModelScope CLI 旗标/进度解析细节 MEDIUM 置信——研究阶段实测确认(narrow in-phase 项)
- Zenodo 记录 19135551 未公开——入口设计+禁用态本相位,公开后激活(无需后续相位)

</specifics>

<deferred>
## Deferred Ideas

- N 并发下载(本相位串行)→ 按需后续
- 下载带宽限速/镜像选择 → 后续按需
- 模型权重下载(本相位仅数据集)→ Phase 11+ 若需要

</deferred>


## Research-Phase Rulings (maintainer-approved 2026-10-12)

- **R-01（细化 D-01 权威字段）:** 下载通道 URL 解析 = `download_url` 主字段优先，非 modelscope 则取 `download_url_alternates` 的 modelscope 镜像；注册表零改动（实测 18/50 主字段为 modelscope，并集 50/50 全覆盖）
- **R-02（覆盖范围）:** 46 可下 + 4 禁用 —— 38 shape-A + 5 shape-B 一键落地；3 shape-C 由下载 worker 落地后自动重命名至注册表目录名；4 shape-D（Genomic_Benchmarks parquet ×3、open-chromatin 全量/迷你）UI 禁用 + 原因说明
- **R-03（细化 D-10 重审计写回）:** `g` 重新审计 = audit 脚本默认输出（全量写 4 个仓库工件、含 git 跟踪的 n_audit.json，落工作区待维护者审查后提交为新基准）；不做 temp+replace 窄写


---

*Phase: 10-Data Manager (Downloads & Verification)*
*Context gathered: 2026-10-12*
