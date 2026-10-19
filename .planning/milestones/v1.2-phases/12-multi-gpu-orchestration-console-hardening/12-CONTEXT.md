---
phase: 12-multi-gpu-orchestration-console-hardening
title: Multi-GPU Orchestration & Console Hardening
status: approved
created: 2026-10-13
---

# Phase 12 Context — Multi-GPU Orchestration & Console Hardening

<goal>
单卡已验证后吞吐扩展:CLI 可调用的静态模型分片 × CUDA_VISIBLE_DEVICES 多 worker 编排(每 worker 视图/产物合并/失败隔离重跑)+ DDP-vs-分片决策文档落地;控制台发布附加:只读 Web 进度镜像 + 维护者核验的快照金丝雀。
</goal>

<code_context>
### Established Seams
- pipeline/run_sweep.py: enumerate_matrix(纯规划)/build_argv/--from-failures/RESUME_MARKER(11 相后含变体别名轴)
- tui/services/sweep_monitor.py: 三态发现/容错读取/ETA——发现列表天然支持 N 根
- tui/services/sweep_launcher.py: 分离子进程/tee/killpg(复用于 worker 进程模式)
- dnallm-mark/ 静态站约定:ES 模块/页面控制器类/DATAAPI/data/*.json
- phase-11 UAT 建议(焦点陷阱等)——本相位加固候选
</code_context>

<decisions>
## Locked Decisions (D-01..D-12)

- **D-01 (维护者裁定 A):** 每 worker 监控视图复用槽 5——worker=独立输出根,发现列表天然 N 行,Enter 附加即视图;TUI 零新编排屏;CLI 是唯一编排入口(MGPU-01/SC2)
- **D-02 (维护者裁定 A):** Web 镜像并入现有静态站:dnallm-mark/progress.html + js/progress.js + data/progress/sweep.json + script/gen_progress.py 生成器;零后端,静态托管约束不变(WEB-01/SC4)
- **D-03 (维护者裁定 A):** 快照金丝雀 6 屏各 1-2 张关键态(~8 张 SVG:env/selection×2/data_manager/run_config/monitor/wizard);维护者过目后提交;CI CPU 侧像素对比,漂移即红(TEST-01/SC5)
- **D-04 (维护者裁定 A):** DDP-vs-分片决策 → docs/multi-gpu.md(决策矩阵+适用场景+CLI 示例+机器分工注记)+ README 一行链接(MGPU-03/SC3)
- **D-05 (维护者 2026-10-13):** 机器分工:多 GPU 开发在本机、**验证在他机**——MGPU 冒烟写成他机执行程序文档(E2' 同模式);本机仅 fake-executor/干跑枚举不相交性/单卡 CUDA_VISIBLE_DEVICES 语义证明;CI 与 GB10 不假设 N>1 设备
- **D-06:** marker-skip(trainer_state)是唯一并发守卫(SC1 锁定;分片不相交性为静态保证,守卫为兜底)
- **D-07:** 分片 CLI 形态由研究定(pipeline/run_sweep_shard.py 新入口 vs run_sweep.py 子命令扩展);判据:argv 面最小化 + 与既有 --models 过滤语义协同
- **D-08:** 失败 worker 隔离重跑 = 该 worker 分片单独 --from-failures 重跑,不触碰健康 worker 的根(SC2)
- **D-09:** 产物合并 = 合并工具把 N worker 根并至单一根;model×task×seed 目录天然不相交,合并非移动而是链接/复制+校验(研究定形)
- **D-10:** TUI 字符串面近零(D-01 零新屏);Web 文案在 progress.html/js 内(遵循站点既有 i18n 惯例);分片 CLI 帮助文本遵循 run_sweep 既有英文惯例
- **D-11:** 快照稳定性:固定终端尺寸、冻结时钟/动态内容(固定夹具数据)、快照测试不依赖网络/GPU
- **D-12:** 相位 11 UAT 建议清单为加固候选池(焦点陷阱修复优先级最高);按"建议级"处置,非本相位硬门
</decisions>

<requirements>
- MGPU-01 → D-06/D-07;MGPU-02 → D-01/D-08/D-09;MGPU-03 → D-04(硬依赖 11 相验证=已过)
- WEB-01 → D-02;TEST-01 → D-03/D-11
- SC1-5 见 ROADMAP(逐字锚)
</requirements>

<specifics>
- 相位是里程碑收官:后接 audit-milestone → complete → cleanup
- TUI 面改动最小化——本相位重心在管线侧 CLI + Web + 测试基建
</specifics>

<deferred>
- DDP 实装(torch-run 数据切分)→ 决策文档落地即交付,实装非本里程碑
- Web 镜像自动刷新(SSE/轮询)→ 静态约束下仅手动/CI 再生
</deferred>
