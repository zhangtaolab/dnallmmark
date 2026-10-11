# Requirements: DNALLM-Mark v1.2 TUI任务

**Defined:** 2026-10-11
**Core Value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust. (v1.2 extension: operators drive the platform confidently from one terminal console without losing CLI parity.)

## v1.2 Requirements

### Environment Check (启动体检)

- [ ] **ENV-01**: TUI 启动即运行完整环境检查（复用 env_smoke 检查内核：版本 pin/dnallm 导入/CUDA/数据集目录/numpy≥2/peft），以状态面板呈现每项 ✓/✗ + 详情
- [ ] **ENV-02**: 检查结果持久化并显示检查日期（"上次检查：YYYY-MM-DD HH:MM"）；提供刷新动作随时重检；同日重复启动读缓存不强制重跑
- [ ] **ENV-03**: 关键 FAIL（无 GPU/依赖缺失）阻止进入启动流程；缺数据项引导至数据管理面板
- [ ] **ENV-04**: 每次启动任务前的快检（轻量重验启动所需子集）

### Selection (选择)

- [ ] **SEL-01**: 模型列表与数据集列表分别呈现可浏览选择（62 模型 / 50 数据集，含关键卡片字段列）；k9s 式过滤+标记集（arena/类型/物种/规模）+ 空格键标记 + 稳定 row_key 集合；只读矩阵总览作为辅助视图（非编辑界面）
- [ ] **SEL-02**: 预设组一键选择：tier-1 E2E 对、tier-2 arena 代表、全部、自定义保存
- [ ] **SEL-03**: 模板导入/导出：运行配置模板（模型×任务×种子×PEFT×变体×GA 完整参数集）JSON 文件，导入时校验；与 sweep_priorities.json tier 结构兼容或提供互转
- [ ] **SEL-04**: 每行显示本地数据状态（✓ 在场 / ✗ 缺失 + n_audit 行数）

### Custom Entries (自定义模型/数据集接入 — 用户自维护，与官方注册表分离)

- [ ] **CUST-01**: 自定义模型接入向导：TUI 引导录入模型卡片（名称/架构/tokenizer/物种/规模/HF+ModelScope 地址/本地路径），**存入用户自维护的自定义注册表（如 `~/.config/dnallmmark/custom_models.json`），绝不写入官方 `pipeline/models_info.json`**——官方文件由官方维护，自定义由用户维护，互不冲突；quirk 清单（safetensors/fp32/特殊头等）可选勾选
- [ ] **CUST-02**: 自定义数据集接入向导：TUI 引导录入数据集条目（键名/路径/train-dev-test 文件/标签列/主指标/Task_type/溯源列），**同样存入用户自定义注册表（`custom_datasets.json`），不动官方 `datasets_info.json`**
- [ ] **CUST-03**: **防呆检测**：字段级校验（必填/类型/枚举/**键名与官方及既有自定义不冲突**/路径存在/split 文件可解析/行数>0/标签列合法/指标名在度量注册表），提交前逐项列出全部问题（fail-fast 收集式，与 _validate_filters 同纪律）
- [ ] **CUST-04**: **错误检测**：接入后自动 dry-run 预检 + audit 对账（行数/非 ACGT/子集存活）；失败时醒目报告并支持撤销（自定义注册表条目级回滚，官方文件零风险）
- [ ] **CUST-05**: **注册表叠加层（overlay）**：管线工具（run_sweep/run_finetune/audit/export）在官方注册表之上加载自定义 overlay（custom 键不得与官方冲突，冲突 fail-fast）；无自定义文件时行为与今天**逐字节一致**（向后兼容，现有测试零改动）
- [ ] **CUST-06**: 自定义项在列表中带 custom 标记（与官方 62/50 区分），可单独启用/停用/导出分享（自定义注册表即分享单元）

### Data Management (数据管理)

- [ ] **DATA-01**: 缺失数据集一键下载（ModelScope 通道，注册表 download_url 为唯一权威）
- [ ] **DATA-02**: 下载队列持久化 + 断点续传（崩溃/重启后续跑）
- [ ] **DATA-03**: 下载落地后行数对账（n_audit 基准）；不一致醒目报告
- [ ] **DATA-04**: Zenodo 整包（record 19135551 公开后）作为备选整体入口

### Run Configuration (运行配置)

- [ ] **CFG-01**: 全参数面：种子（默认 42,43,44）、PEFT 模式+别名预览、config-variant（head/probe/curve+PROBE_INELIGIBLE 提示）、学习曲线档位、公平性子集开关、epochs/batch 覆盖
- [ ] **CFG-02**: 项目目录与存储目录分离设置（输出根/数据集/模型缓存），默认仓库相对路径，显式覆盖时 TUI 统一传绝对路径参数
- [ ] **CFG-03**: 干跑预览：枚举 cell 数/预估（导入纯规划函数计算，与执行同源）

### Launch (启动)

- [ ] **LNC-01**: 启动门：env_smoke 前置（FAIL 阻止+原因显示）+ terraform 式确认（预览 → 显式批准；全量 E2' 需输入确认短语）
- [ ] **LNC-02**: 执行恒为 `run_sweep.py` 子进程（LIST argv + PYTHONUNBUFFERED=1 + start_new_session 分离）；TUI 退出提示 kill/detach/cancel，detach 断点安全
- [ ] **LNC-03**: E2' 全量三种子保持维护者显式授权边界（TUI 只呈现确认门，不绕过）

### Monitoring (监控)

- [ ] **MON-01**: poll-and-attach 看板：cell 级状态（排队/运行/完成/失败/跳过，种子相邻），2s 前沿扫描 + 60s 全扫，容错 artifact-loader（部分写跳拍）
- [ ] **MON-02**: 进度统计：完成/总数、当前 cell、耗时；对外部（CLI）启动的 sweep 同样可附加监控
- [ ] **MON-03**: 失败清单实时显示 + 一键 `--from-failures` 重跑（确认门）
- [ ] **MON-04**: 日志尾部跟随（RichLog 有界视图）+ **tee 落盘持久化**（~/.config/dnallmmark/logs/ 或任务输出目录）
- [ ] **MON-05**: 断点续跑状态识别（trainer_state.json 标记）

### Pipeline-side (管线侧配套)

- [ ] **PIPE-01**: FlopsCounter 移植：旧 dnallmmark_pipeline.py 的 20+ 架构前向钩子移植到 run_finetune.py（早于监控阶段；喂 E2' FLOPs 正确性与排行榜效率轴）
- [ ] **PIPE-02**: run_sweep argv 透传四项：--subset_file（E2' 公平性，补已知缺口）、--effective-batch（auto-GA：GA=max(1, N//batch_size)，默认 16）、--num_train_epochs、--cache_dir（可选）
- [ ] **PIPE-03**: FlopsCounter 与监控共用容错 loader 的 JSON 输出契约

### Multi-GPU (多卡编排)

- [ ] **MGPU-01**: 按模型分片 × CUDA_VISIBLE_DEVICES 多 worker 静态编排（CLI 可调用的模式，非 TUI 专属）
- [ ] **MGPU-02**: 每 worker 监控视图 + 产物合并 + 失败 worker 隔离重跑
- [ ] **MGPU-03**: DDP（torch run 切数据）与模型分片两层的适用场景决策落地（单大模型加速 vs 多模型吞吐）；硬依赖单卡验证通过

### Localization & Extras (本地化与附加)

- [ ] **I18N-01**: 中文为主的界面文案（constants 模块约定，术语保留英文）
- [ ] **WEB-01**: 只读 Web 进度镜像（团队看进度；静态产物，不引入后端——符合静态托管约束）
- [ ] **TEST-01**: Textual 官方快照测试（canonical screens 的 SVG 金标准，维护者验证后提交）

## v1.2 Out of Scope

| Feature | Reason |
|---------|--------|
| 可编辑 62×50 矩阵作为主 UI | 终端不友好；k9s 式标记集 + 只读总览替代（研究反特性表） |
| TUI 内 YAML 编辑器 | suspend-to-$EDITOR 模式替代 |
| Optuna 式分析图表 | 超出操作台定位；排行榜网站已有分析面 |
| 自动重试循环 | 失败重跑保持显式确认门（研究反特性） |
| TUI 内实现基准语义（分数计算等客户端复算） | 反 scope-creep 铁律：TUI 读 artifact/编排，不重算 |
| Windows Terminal 支持矩阵 | 操作环境为 SSH/Linux GB10；Windows 运维成真再验 |
| textual-serve / textual-dev 进 committed 组 | 研究明确不添加 |
| E2' 全量重跑自动触发 | 恒为维护者显式授权（双门） |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENV-01 | Phase 8 | Pending |
| ENV-02 | Phase 8 | Pending |
| ENV-03 | Phase 8 | Pending |
| ENV-04 | Phase 8 | Pending |
| SEL-01 | Phase 8 | Pending |
| SEL-02 | Phase 8 | Pending |
| SEL-03 | Phase 8 | Pending |
| SEL-04 | Phase 8 | Pending |
| DATA-01 | Phase 9 | Pending |
| DATA-02 | Phase 9 | Pending |
| DATA-03 | Phase 9 | Pending |
| DATA-04 | Phase 9 | Pending |
| CFG-01 | Phase 10 | Pending |
| CFG-02 | Phase 10 | Pending |
| CFG-03 | Phase 10 | Pending |
| LNC-01 | Phase 10 | Pending |
| LNC-02 | Phase 10 | Pending |
| LNC-03 | Phase 10 | Pending |
| MON-01 | Phase 10 | Pending |
| MON-02 | Phase 10 | Pending |
| MON-03 | Phase 10 | Pending |
| MON-04 | Phase 10 | Pending |
| MON-05 | Phase 10 | Pending |
| PIPE-01 | Phase 7 | Pending |
| PIPE-02 | Phase 7 | Pending |
| PIPE-03 | Phase 7 | Pending |
| MGPU-01 | Phase 11 | Pending |
| MGPU-02 | Phase 11 | Pending |
| MGPU-03 | Phase 11 | Pending |
| I18N-01 | Phase 8 | Pending |
| WEB-01 | Phase 11 | Pending |
| TEST-01 | Phase 11 | Pending |

**Coverage:**
- v1.2 requirements: 32 total *(corrected 2026-10-11 — the previously stated "28 total" was a stale count predating team supplementation; the file defines 32 checkbox requirements)*
- Mapped to phases: 32/32 (Phase 7: 3 · Phase 8: 9 · Phase 9: 4 · Phase 10: 11 · Phase 11: 5)
- Unmapped: 0
- Orphaned/duplicated: 0

---
*Requirements defined: 2026-10-11*
*Last updated: 2026-10-11 — roadmap traceability filled (32/32 mapped, Phases 7-11)*
