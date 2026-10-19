# Phase 9: Custom Model & Dataset Onboarding (自定义接入向导) - Context

**Gathered:** 2026-10-12
**Status:** Ready for planning
**Mode:** autonomous smart discuss(4 灰区,维护者逐区裁定;Area 4 经菜单命名多轮迭代定案)

<domain>
## Phase Boundary

操作者完全从控制台把自己的模型与数据集带入基准,官方注册表可证明零触碰——向导引导录入完整条目入用户自有的自定义注册表,防呆校验一次性收集全部字段问题(fail-fast collect-all,`_validate_filters` 同纪律),条目仅在通过真实 gauntlet(dry-run 预检 + audit 对账)后落盘,失败即不落盘;落地条目带 custom 标记、可停用、注册表文件即分享单元。

四件事:
1. **CUST-01 模型向导**:模型卡片引导录入(名称/架构/tokenizer/物种/规模/HF+ModelScope 地址/本地路径)+ quirk 清单可选勾选 → `~/.config/dnallmmark/custom_models.json`
2. **CUST-02 数据集向导**:键名/路径/train-dev-test 文件/标签列/主指标/Task_type/溯源列 → `custom_datasets.json`
3. **CUST-03 防呆检测**:字段级 collect-all 校验(必填/类型/枚举/键冲突官方+既有自定义/路径存在/split 可解析/行数>0/标签列/指标名在度量注册表)
4. **CUST-04 错误检测 + CUST-06 标记/停用/导出**:dry-run 预检 + audit 对账;custom 徽标;loader 级停用;注册表文件即分享单元

同时落地**导航壳**(维护者 Phase 9 定案的顶部主菜单方案)。官方 `pipeline/{models,datasets}_info.json` 绝不写(约束 11);管线侧唯一加性改动 = `registry_loader` 对 `enabled:false` 条目的跳过。

</domain>

<decisions>
## Implementation Decisions

### 向导形态与 quirk 处理
- **D-01:** 多步模态向导(3-4 步,每步一组字段,enter 下一步 / esc 取消),复用 Phase 8 ModalScreen 模式
- **D-02:** 模型 quirk 清单(safetensors/fp32/特殊头)记录于条目字段 + 校验警示;执行侧 quirk→CLI 旗标映射是 Phase 11 run-config 的职责(管线硬编码 quirk 表不可扩——约束 6;TUI never-computes)
- **D-03:** 类型感知控件:枚举字段用 SelectionList(物种/架构/Task_type/主指标——指标名从度量注册表取),路径用 Input + 存在性即时校验,数字字段类型校验
- **D-04:** 本相位引入导航壳(详见 D-13..16)

### 校验与 gauntlet 机制
- **D-05:** collect-all 校验为服务层纯函数(tier-1 可测,数据源注入)——一次全列,不逐字段打断
- **D-06:** dry-run 预检 = 子进程 `run_sweep.py --dry-run`(overlay 自动生效,subset=新条目)——CLI parity 正面运用;CPU 纯规划零训练,无需 GPU 授权
- **D-07:** audit 对账 = 子进程调 audit 脚本内核(新数据集行数/非 ACGT/子集存活)——复用既有实现,TUI 零计算
- **D-08:** **gauntlet 全过才落盘**——失败=条目从未写入,天然零回滚风险;成功后另有会话内 undo 撤销刚落盘条目

### 停用语义与 custom 标记
- **D-09:** loader 级真停用:自定义条目带 `enabled` 字段,`registry_loader` 跳过 `enabled:false`(加性改动——官方条目无此字段,缺席仍逐字节一致,现有测试零改动)
- **D-10:** custom 标记 = 列内徽标(颜色+字形双通道)+ 计数行区分(官方 62/50 · 自定义 N/M)
- **D-11:** 导出 = custom 注册表文件本身复制到操作者指定路径;导入 = 向导内"从文件导入"入口(校验后合并,冲突一次性列出)
- **D-12:** 本相位条目只增不编辑(编辑 = 删除 + 重录,完整编辑表单留后续相位)

### 导航壳(维护者 2026-10-12 定案)
- **D-13:** 顶部主菜单(资源名词命名):`1环境检查 2模型·数据集 3数据管理 4运行配置 5任务监控 6关于`——3/4/5 占位显示"未开放"(按相应相位实装),**`6关于` 本相位实装**(版本信息屏:软件版本/数据版本/milestone 阶段/依赖版本等只读信息)
- **D-14:** 向导从列表屏 `w` 键进入(选中行预填该列表上下文);菜单无向导项(向导是动作不是屏)
- **D-15:** 底部子菜单:左段当前屏上下文命令(现 Footer 键帽迁移),右段恒定 `?` `q`
- **D-16:** 低于 80×24 时 min-size 守卫全屏接管,顶/底菜单隐藏(现状不变);菜单栏各占 1 行计入内容区预算

### Claude's Discretion
- 向导步序划分(模型向导与数据集向导各自 3-4 步怎么分组)
- enabled 字段的确切 schema 位置与默认值语义(缺席 = 启用)
- 徽标字形/颜色的具体选择(UI-SPEC 阶段细化)
- 关于屏的具体信息条目集合与布局
- gauntlet 结果的呈现形态(逐项 ✓/✗ 面板)
- dry-run/audit 子进程的超时与输出解析容错(artifact_loader 容错契约复用)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 计划权威
- `.planning/ROADMAP.md` §"Phase 9"(目标 + 5 条成功判据)+ 绑定约束 5/6/11(TUI never-computes、surgical pipeline surface、custom/official 分离绝对)
- `.planning/REQUIREMENTS.md` §Custom Entries(CUST-01..04、CUST-06;CUST-05 已于 Phase 7 完成)
- `.planning/PROJECT.md` §Key Decisions + §Context

### 前相决策(直接依赖)
- `.planning/phases/07-*/07-CONTEXT.md` D-06/D-07/D-08(overlay 自动探测、XDG 路径解析、env 整目录覆盖)——本相位消费其 loader 并加 enabled 跳过
- `.planning/phases/08-*/08-CONTEXT.md` D-04(XDG config 根,与 presets.json 同根)、D-07(schema 纪律)
- `.planning/phases/08-*/08-UI-SPEC.md`(现行设计契约——本相位导航壳是其演进,新 UI-SPEC 将继承其 Terminal Contract/80×24/NO_COLOR 条款)

### 复用源码
- `pipeline/registry_loader.py` —— overlay 加载 + 冲突 fail-fast(enabled 跳过的落点;`DNALLMMARK_CUSTOM_REGISTRY_DIR` 注入先例)
- `pipeline/run_sweep.py` —— `--dry-run` 纯规划路径 + subset 校验(D-06 子进程目标)
- `script/audit_n_frequencies.py` —— 行数/非 ACGT 内核(D-07 子进程目标)+ `dnallm-mark/data/n_audit.json` 产物形状
- `tui/services/settings.py`(XDG config 落盘 + atomic_write)、`tui/services/registries.py`(canonical entries)、`tui/screens/selection.py`(w 键入口 + 列形态)、`tui/app.py`(组合根 + SCREENS;导航壳落点)
- `schemas/flops_report.json` / `schemas/run_template.json` —— custom registry schema 纪律先例(additionalProperties false、schema_version、$comment 溯源)
- 度量注册表(主指标枚举源):`script/summarize_comparison.py` metric_key_map 与 REQUIREMENTS 度量注册表节

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **ModalScreen 模式族**(Phase 8):PresetModal/ConfirmModal/RowDetailModal/HelpModal——多步向导的直接模板;`getters.app` TYPE_CHECKING 模式(WR-06 修复引入)
- **服务层 Protocol 注入 + tier-1/tier-2 双层测试**——向导服务(校验/gauntlet 编排)同一纪律
- **run-id 消息标记模式**(WR-02 修复)——gauntlet 子进程异步结果回填防串
- **artifact_loader 容错读取**——子进程输出/临时文件解析
- **min-size 守卫 + below_minimum_grid 属性**(WR-01/WR-06 修复后形态)——导航壳共存的行为基准(已有回归测试)

### Established Patterns
- services 零 textual(AST import-lock 测试锁定)——向导服务同规
- 子进程 argv LIST + 绝对路径 + 容错读取(Phase 7 sweep 先例)——dry-run/audit 调用复用
- fail-fast collect-all(`_validate_filters`/subset 预校验/D-07 模板校验)——D-05 同纪律第四实例
- 缺席=逐字节一致——enabled 字段必须保持(官方条目无字段,加载路径不变即不变)

### Integration Points
- `tui/app.py` 组合根:顶部菜单栏/底部子菜单挂载点;SCREENS 注册(关于屏);`w` 绑定下发到 selection 屏
- `tui/strings.py`:全部新中文文案的唯一家(菜单项/向导步骤/校验问题/gauntlet 结果/关于屏)
- `pipeline/registry_loader.py`:enabled 跳过(本相位唯一管线加性改动,现有测试零改动)
- `~/.config/dnallmmark/custom_{models,datasets}.json`:落盘目标(与 presets.json 同根)

</code_context>

<specifics>
## Specific Ideas

- 维护者菜单命名迭代轨迹(定案前):`选择/数据`混淆 → 挑选/下载(动词)→ 状态/基准(二字名词)→ **四字资源名词 + 模型·数据集变体**(定案)——后续菜单命名沿用"资源名词、不限字数"的品味
- 维护者实测过 `make tui` 并保存过真实预设(`d1`:hyenadna-large-1m-seqlen-hf + plant-dnabert-6mer × iPro-WAEL_datasets__Promoter_R_capsulatus)——UAT 反馈键列加宽已修(2b61e60),教训:**真实内容要放得下**,向导字段宽度同理
- `关于` 屏是维护者主动添加的("可以显示软件版本等信息")

</specifics>

<deferred>
## Deferred Ideas

- quirk → CLI 旗标映射(执行侧)→ Phase 11 run-config
- 条目完整编辑表单(本相位只增不编辑)→ 后续相位
- export_runs.py 改走 overlay(Phase 7 验证器 W1 建议)→ Phase 11 数据流或单独小任务
- 自定义条目的启用/停用批量操作 → 后续(按需)

</deferred>

---

*Phase: 9-Custom Model & Dataset Onboarding (自定义接入向导)*
*Context gathered: 2026-10-12*
