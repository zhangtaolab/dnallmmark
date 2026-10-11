# DNALLM-Mark TUI 需求信息收集 (Requirements Collection)

> **目的**：为下一个里程碑——dnallmmark TUI（终端操作台）——收集需求。本文档由当前仓库现状自动梳理生成，**请各位开发者直接补充**。
>
> **如何补充**：直接编辑本文档——在对应小节的表格加行、勾选复选框、在「开放问题」区提出新问题。保持中文为主、关键术语保留英文。PR 到 `autorun` 分支或直接 push 均可。

---

## 1. 背景与目标

为 dnallmmark 基准平台构建一个终端 TUI（Terminal UI），让操作者能够：

1. **选择**用什么数据集、跑什么模型（62 模型 × 50 数据集）
2. **查看**数据集是否在本地、缺失时从哪里下载
3. **配置**运行参数（种子数、PEFT 模式、变体、学习曲线等）
4. **启动**并在单卡上测试，成功后扩展到多卡
5. **监控**任务进度（cell/种子级状态、失败、断点续跑）

## 2. 现有资产盘点（TUI 直接复用，无需重做）

| 资产           | 位置/入口                                                              | 说明                                                                                                                              |
| -------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| 模型注册表     | `pipeline/models_info.json`                                          | 62 模型，11 键卡片（架构/规模/tokenizer/物种/HF+ModelScope 地址）                                                                 |
| 数据集注册表   | `pipeline/datasets_info.json`                                        | 50 数据集，含溯源列（source/citation/license/download_url/alternates）                                                            |
| 数据存在性审计 | `script/audit_n_frequencies.py` → `dnallm-mark/data/n_audit.json` | 每任务 train/dev/test 行数、非 ACGT 统计、缺失标记                                                                                |
| 统一评测子集   | `pipeline/eval_subsets.json`                                         | 公平性评测（`--subset_file`）                                                                                                   |
| 扫描驱动       | `pipeline/run_sweep.py`                                              | 优先级（tier-1/tier-2/其余）、失败清单重跑（`--from-failures`）、干跑（`--dry-run`）、PEFT（`--peft`）、曲线（`--curve`） |
| 单模型入口     | `pipeline/run_finetune.py`                                           | `--num_train_epochs`/`--config-variant`/`--train_fraction`/`--subset_file`                                                |
| 环境自检       | `pipeline/env_smoke.py`                                              | 版本 pin/dnallm 导入/CUDA/数据集目录/numpy≥2，PASS/FAIL 退出码                                                                   |
| 迁移/快照      | `make snapshot`、`script/freeze_snapshot.py`                       | 结果快照 + SHA-256 校验                                                                                                           |

**ModelScope 数据覆盖（2026-10-11 已达成 50/50）**：zhangtaolab 官方 9 ｜ lgq12697 镜像 34（GUE/NT/pgb/GB）｜ forrestzhang 7（Deep4mC/iDNA-ABF/iPro-WAEL/BEND，已上传+README）。下载通道：SDK/CLI（`modelscope download --dataset X`）、raw HTTP API（`/api/v1/datasets/{ns}/{name}/repo?FilePath=...`）、git clone。

## 3. 功能需求域

### 3.1 模型×数据集选择

- [X] 矩阵/列表视图：62×50，支持按 arena（animal/plant/microbe）、模型类型（MLM/CLM/DL）、物种、规模过滤
- [ ] 预设组一键选择：tier-1 E2E 对、tier-2 arena 代表、全部、自定义保存
- [ ] **模板导入**：运行配置模板（模型×任务×种子×PEFT×变体×GA 等完整参数集）以 JSON 文件导入/导出，可分享、可复用；与 `sweep_priorities.json` 的 tier 结构兼容或提供互转
- [X] 每行显示本地数据状态（✓ 在场 / ✗ 缺失 + 行数来自 n_audit）
- [x] 选择结果导出为 run_sweep 的 `--models`/`--tasks` 参数或 priorities 文件

- 补充：＿＿＿

### 3.2 数据管理（下载/校验）

- [X] 缺失数据集一键下载（ModelScope 通道，注册表 download_url 为唯一权威）
- [X] 下载进度显示；落地后行数对账（n_audit 基准）
- [ ] Zenodo 整包（record 19135551，公开后）作为备选整体入口
- [x] 7 个非 ModelScope 托管家族（已由 forrestzhang 补齐——若后续有新增数据源，此处维护映射）

- 补充：＿＿＿

### 3.3 运行配置

- [X] 种子选择（默认 42,43,44 = E2' 三种子）
- [X] PEFT 模式（none/lora/ia3）+ adapter 别名预览（{model}+lora 等）
- [X] config-variant（head/probe/curve）与 PROBE_INELIGIBLE 守卫提示
- [X] 学习曲线（--train_fraction 档位选择）
- [ ] 公平性子集开关（--subset_file eval_subsets.json）
- [X] epochs/batch 覆盖（smoke 用 1 epoch 快速通道）
- [X] 输出根目录选择 + 干跑预览（枚举出的 cell 数/预估）

- 补充：＿＿＿除了lora还要加上冻结backbone加上probe的微调办法，默认训练epoch和之前保持一致为3
  > 【核查 2026-10-11】probe+冻结骨干**机制已在仓库**（`run_finetune --config-variant probe`，frozen backbone + 不合格模型守卫，GB10 实测可训练参数 0.44%）——TUI 仅需露出该选项；epochs=3 与现行 `finetune_config.yaml` 默认一致。
- 如果自动化运行，需要解决batch_size和gradient_accumulation_steps的选择，以适配不同模型和数据集
  > 【核查】机制半在：动态 batch_size 缩放与 per-dataset grad_accum 重置已有；**新增工作 = `--effective-batch <N>` 自动 GA 旗标**（GA = max(1, N // batch_size)，对应开放问题 Q7 的 16/1 规则）。

### 3.4 执行模式（单卡 → 多卡）

- [X] **单卡优先**：本机 GB10 开发测试；TUI 内启动 = 与 smoke→E2' 同一入口
- [X] **启动即环境检查**（maintainer 2026-10-11）：TUI 一启动就检查本地运行环境是否完整——复用 env_smoke 检查内核（版本 pin/dnallm 导入/CUDA/数据集目录/numpy≥2/peft），以状态面板/横幅呈现（每项 ✓/✗ + 详情）；缺失项引导到数据管理/修复动作，关键 FAIL（无 GPU/依赖缺失）阻止进入启动流程；**检查结果持久化记录检查日期**（面板显示"上次检查：YYYY-MM-DD HH:MM"），提供**刷新动作随时重检**；结果过期（如同日多次启动）不强制重跑但可一键刷新
- [X] 启动前环境自检（env_smoke 集成，FAIL 则阻止并显示原因）
- [X] **E2' 边界**：全量三种子重跑仍需维护者显式授权——TUI 对全量启动给出确认门
- [X] **多卡（二期）**：按模型分片 × `CUDA_VISIBLE_DEVICES` 多 worker；worker 健康监控；产物合并；失败 worker 隔离重跑

- 补充：＿＿＿多卡可以使用torch run来实现
  > 【核查 2026-10-11】torch run（DDP 数据并行）与「按模型分片 × CUDA_VISIBLE_DEVICES」是**互补的两层**：DDP 加速单次大模型运行（切数据）；模型分片最大化 62 模型×独立任务的吞吐（切模型）。E2' 全量重跑更适合模型分片；单个 1B+ 大模型单任务加速才需要 DDP。里程碑 discuss 时需明确两层各自的适用场景与优先级。

### 3.5 任务监控

- [X] cell 级状态看板：排队/运行/完成/失败/跳过（seed 相邻显示）
- [X] 进度：已完成 cell 数/总数、当前模型×任务×种子、耗时统计
- [X] 失败清单实时显示（sweep_failures.json）+ 一键 `--from-failures` 重跑
- [X] 日志尾部跟随（当前 cell 的 stdout/stderr）
- [X] 断点续跑状态（trainer_state.json 标记识别）

- 补充：＿＿＿目前部分新架构以及混合架构 tensorboard默认计算的flops有些问题， 这部分需要额外加一个模块来评估flops？
  > 【核查 2026-10-11】是真实缺口：旧 `dnallmmark_pipeline.py` 的 FlopsCounter（20+ 架构前向钩子：Mamba/SSM/Hyena/BigBird/GQA…）未随 dev 重写移植到 `run_finetune.py`；HF Trainer 对混合架构的 total_flos 不可靠，而排行榜效率轴依赖它。**建议列为独立 work package**（受益方不止 TUI，含 E2' 的 FLOPs 采集正确性），置于 P3 前落地。

### 3.6 环境与安全边界

- [x] ruff + ty 双门保持；TUI 属新依赖需评审（框架选型见开放问题）
- [x] DNALLM 套件仓库只读；TUI 不写入
- [ ] CI 不引入 GPU/TUI 运行时

- 补充：＿＿＿

## 4. 非功能需求

- [x] 终端环境：SSH 终端宽度/颜色/鼠标
- [x] 框架候选：**Textual**（纯 Python、无构建步、组件丰富）
- [x] 配置持久化：会话选择/过滤器的保存位置（~/.config/dnallmmark/？）
- [ ] **目录设置**：项目目录与存储目录可配置——项目根（仓库位置：注册表/脚本解析基准）与存储根（输出/数据集/模型缓存：`run_sweep --output-root`、`pipeline/datasets/`、`pipeline/models/` 的落位）分离设置；默认沿用仓库内相对路径，显式覆盖时 TUI 负责把路径传给下游脚本（现有脚本多为 REPO_ROOT 相对假设，需统一传参而非改脚本假设）
- [x] 中文界面/双语？

- 补充：＿＿＿

## 5. 开放问题（请补充观点）

| # | 问题                                                                               | 你的观点                                                                                                                                                                                                                                                                            |
| - | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | TUI 框架选型：Textual vs rich vs urwid？（倾向 Textual：无构建步约束相容、文档好） | ＿                                                                                                                                                                                                                                                                                  |
| 2 | 监控刷新机制：轮询 sweep_failures/目录 mtime vs 进程内事件回调？                   | ＿                                                                                                                                                                                                                                                                                  |
| 3 | 多卡调度策略：静态模型分片 vs 动态任务队列（model 大小均衡）？                     | ＿如果多卡不切分模型，切分训练数据                                                                                                                                                                                                                                                  |
| 4 | 下载队列是否需要持久化/断点续传？                                                  | ＿需要                                                                                                                                                                                                                                                                              |
| 5 | TUI 是否也要包一层 Web UI 的远端只读视图（团队看进度）？                           | ＿可要可不要                                                                                                                                                                                                                                                                        |
| 6 | 权限模型：谁能启动全量 E2'？（建议：TUI 内二次确认 + 显式 flag）                   | ＿                                                                                                                                                                                                                                                                                  |
| 7 | ＿新增问题＿                                                                       | ＿运行需要加一个参数更新梯度步数 Gradient Accumulation*batch size为多少，现在训练脚本是根据模型来自动更新batch size的，所以可以动态调整Gradient Accumulation老保持不同模型尽可能一致，先定16（部分小模型起始batch size就大于16比如64，那么这种情况Gradient Accumulation就为1不管） |

## 6. 里程碑衔接

本收集文档完成后将作为 `/gsd-new-milestone` 讨论阶段的需求输入（草案骨架：P1 TUI 地基 → P2 数据管理器 → P3 单卡启动+监控 → P4 多卡编排，P4 硬依赖 P3 单卡验证）。

---

*文档生成于 2026-10-11，基于仓库 @ 当前 autorun HEAD（v0.7.1 收口阶段）。*
