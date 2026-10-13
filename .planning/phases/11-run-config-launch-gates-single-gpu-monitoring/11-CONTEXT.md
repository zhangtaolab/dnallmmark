---
phase: 11-run-config-launch-gates-single-gpu-monitoring
title: Run Config, Launch Gates & Single-GPU Monitoring
status: approved
created: 2026-10-13
---

# Phase 11 Context — Run Config, Launch Gates & Single-GPU Monitoring

<goal>
操作者核心闭环:组合完整 run spec → 同源干跑预览 → env+确认门 → 分离式 run_sweep.py 子进程 → 同控制台监控与恢复。E2' 全量保持维护者授权边界。GB10 有界冒烟(1×1×1×1epoch)端到端证明。
</goal>

<code_context>
### Established Seams
- pipeline/run_sweep.py: `enumerate_matrix`(纯规划) `build_argv` `launch_subprocess` `--dry-run` `--from-failures` `RESUME_MARKER="trainer_state.json"` priority tiers/failure pairs
- tui/services/env_gate.py + quick_check.py(相位 8 字节冻结面,D-09 前置消费)
- tui/services/settings.py XDG state/原子写;selection/templates 预设先例
- tui/services/registries.py 官方+custom overlay 键集(选择器数据源)
- nav.py 槽 4/5 占位 → 本相位双实屏晋级(D-13..16 既有裁定)
- tui/strings.py 单一家;前缀先例 DL_/QUEUE_ → 本相位 CFG_/LNC_/MON_
- 10 相 download_queue 的 Popen 纪律(start_new_session/killpg/runner 注入缝)为执行子进程直接复用模式
</code_context>

<decisions>
## Locked Decisions (D-01..D-16)

- **D-01 (维护者裁定 B):** 槽 4 自带完整模型/数据集选择器,独立于槽 2 标记组合;选择状态 XDG 持久化;预览与启动只读本屏选择
- **D-02 (维护者裁定 A):** E2' 判定 = 干跑枚举比对全量(62 模型×50 数据集×3 种子);确认 = 完整输入本次输出目录名
- **D-03 (维护者裁定 A):** 监控附加 = 自动扫描默认输出根(finetuned/ 等,含 CLI 启动) + 手动输入输出路径
- **D-04 (维护者裁定 A):** SC5 冒烟选型由研究阶段实测定(最小模型×最小任务),写入计划供计划评审过目
- **D-05:** 干跑预览同源——导入 pipeline.run_sweep 纯规划函数(enumerate_matrix 等),绝不复制枚举逻辑;services 经 sys.path 根导入(pipeline/ 在路径),零 textual
- **D-06:** 执行恒为 run_sweep.py 子进程:LIST argv + PYTHONUNBUFFERED=1 + start_new_session 分离;TUI 退出三选 kill/detach/cancel,默认 detach;断点安全(trainer_state 标记天然恢复)
- **D-07:** E2' 三种子授权边界不可绕过:确认门在 TUI 呈现,但判定与短语校验使 UI 内部无法静默跳过(LNC-03)
- **D-08:** env_smoke 前置:FAIL 阻止启动并显示原因(消费相位 8 env_gate 冻结面,零改动)
- **D-09:** 监控节奏:2s 前沿扫描 + 60s 全扫;artifact-loader 容错(部分写跳拍,MON-01)
- **D-10:** 日志 tee 落盘:单一家 XDG logs 目录(与 state/config 一致);planner 可依实现细节微调但不得引入第二持久化根
- **D-11:** 失败重跑走 `--from-failures <sweep_failures.json>`,独立确认门;trainer_state.json 识别断点续跑(MON-03/05)
- **D-12:** 字符串前缀 CFG_/LNC_/MON_ 单一家 strings.py;CJK 锁与清单双向锁自动覆盖
- **D-13:** 槽 4→槽 5 启动后自动跳转:启动成功 toast + 自动导航监控屏(设计默认,计划评审确认)
- **D-14:** 项目/存储目录分离(CFG-02):输出根/数据集根/模型缓存三设置,默认仓库相对,显式覆盖传绝对路径
- **D-15:** 机器分工约束(维护者 2026-10-13):本机仅开发测试——冒烟上限 1-2 模型×3-4 数据集部分数据;全量 sweep 由其他机器执行,E2' 双重门控不变
- **D-16:** 9 相导航壳裁定延续:槽 4(运行配置)/槽 5(任务监控)本相位由占位变实屏;底栏左上下文命令右恒定 ? q
- **D-17 (维护者追加 2026-10-13):** 监控面板显示已用时 + 预估结束时间(ETA):已用时自 sweep 起点连续累计;ETA 依据已完成 cell 耗时的滚动中位数×剩余数(有分模型数据用分模型,否则全局),数据不足(<1 个完成 cell)诚实降级为"估算中…";显示带 ≈ 并在方差大时给出区间;出现在监控统计行与发现列表行
- **D-18 (2026-10-13):** 变体穿线:run_sweep 增加 `--config-variant` 直通旗标(PIPE-02 式增量管线改动,argv 奇偶校验钉死)——SC1 承诺变体控件全功能+执行恒为 run_sweep 的直接推论;UI-SPEC 开放问题 1 定案
- **D-19 (2026-10-13):** 数据集根混合方案:设置驱动 UI presence 检查+注册表侧绝对路径解析;本相位不加直通旗标(研究证实真实需要再议)——UI-SPEC 开放问题 2 定案;开放问题 3/4 归计划阶段(冒烟选型/ETA 方差常数)
</decisions>

<requirements>
- CFG-01 全参数面 → 槽 4 参数区(种子 42/43/44 默认、PEFT+别名预览、变体 head/probe/curve+PROBE_INELIGIBLE、曲线档位、公平子集、epochs/batch、--effective_batch_size 自动 GA)
- CFG-02 目录分离 → D-14
- CFG-03 同源预览 → D-05,枚举 cell 数
- LNC-01/02/03 → D-06/07/08 + D-02
- MON-01..05 → 槽 5 看板 + D-03/09/10/11
- SC1-5 见 ROADMAP(逐字目标回溯锚)
</requirements>

<specifics>
- 相位边界:单 GPU 单 sweep;多 GPU 编排/分片属相位 12(hard gate:本相位验证通过)
- attach 模式对 CLI 启动 sweep 同效(D-03 扫描发现)
- 日志尾随 RichLog 有界;tee 落盘(D-10)
</specifics>

<deferred>
- 多 sweep 并行监控视图 → 相位 12 按需
- Web 进度镜像 → 相位 12 (WEB-01)
- 快照金丝雀 → 相位 12 (TEST-01)
</deferred>
