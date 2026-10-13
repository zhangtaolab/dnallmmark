---
status: passed
phase: 11-run-config-launch-gates-single-gpu-monitoring
source: [11-VERIFICATION.md]
started: 2026-10-13T16:45:00Z
updated: 2026-10-13T17:30:00Z
---

## Current Test

number: 1
name: GB10 有界冒烟(9 步程序实机代跑,maintainer 授权 "跑" 2026-10-13 16:29)
expected: |
  槽 4 组合 plant-dnabert-6mer × iDNA_ABF__5mC × seed 42 × 1 epoch → ./finetuned-smoke;
  [p] 同源预览+逐字 argv → [enter] 启动门(env 预检→摘要确认) → 启动 toast + D-13 自动跳监控;
  cell ⠋→✓(~1:21);detach/重挂/再发现;⊘ 断点续跑;失败腿(毒化→[f]→恢复→r 确认门重跑→真训完成);
  E2' 全量 62×50×3 阻断证明(错目录名✗死锁,零进程)。
awaiting: (none — executed live by orchestrator per maintainer authorization "跑")

## Tests

### 1. GB10 bounded smoke (launch → monitor → detach → resume → failure-re-run → E2' blocks)
expected: the 9-step procedure end-to-end on the real host, real GPU, real subprocesses.
result: pass

## Summary

total: 1
passed: 1
issues: 0
pending: 0
skipped: 0
blocked: 0

## Evidence (2026-10-13 16:45–17:30, live tmux 140x45 + real GPU)

**Launch & monitor**: 槽 4 (62-model picker/params/dirs/preview line 1 cell) → [p] modal: 同源 enumerate_matrix 注记 + 逐字 LIST argv(绝对路径) → [enter] 启动门 → env 预检静默通过 → terraform 摘要确认("1 模型 × 1 任务 × 1 种子 = 1 cell → ./finetuned-smoke / 启动以上 sweep?") → Enter → toast "✓ sweep 已启动(分离)" + **D-13 自动跳槽 5**(attached ◆) → cell ⠋ 运行 → **✓ 完成 @ 已用时 1:21**(train_runtime 与既往真跑 65s 同级);统计行/已用时/D-17 预估位实机渲染;2s/60s 节奏注记。盘上:finetuned-smoke/{sweep_manifest,sweep_failures}.json + seed_42/{trainer_state,run_record,flops_report,config}.json 全落。

**Rediscovery & resume**: [t] 日志尾随实况(tqdm/显存 1.56GB/"Sweep finished: 1 cell — 1 completed"/tee 落盘路径 XDG state/logs) → TUI 退出重启 → [a] 手动附加 ./finetuned-smoke(D-03;根持久化跨重启) → ○ 已结束 1/1 → **同 spec 二次启动: tee 尾行 "Sweep finished: 1 cell(s) — 0 completed, 1 skipped, 0 failed" = trainer_state ⊘ 断点跳过**;监控标题行 "⊘ 续跑: 1 cell 因 trainer_state 标记跳过"(MON-05 实机)。

**Failure leg**: 毒化(数据集目录临时改名)+ 加 GUE__virus_species_40 → 启动(摘要 2 cell)→ tee "Dataset dir not found … skipping" → sweep_failures.json 精确诊断("executor exited 0 but final_metrics.json is missing (run_finetune.py swallowed a training failure)") → 恢复目录 → 槽 5 ✗ 失败渲染 → [f] 失败清单(1) → r → **独立确认门**("重跑 1 个失败 cell(--from-failures)?") → Enter → toast "✓ 失败重跑已启动" + 真进程 + **统计按新 run 作用域清零(WR-02 修复实机)** → **q → ExitModal(分离退出(默认)/终止后退出/返回) → Enter detach: 应用退出、run_sweep 存活(PID 1252674)、tee 持续记录** → 分离中真训 3000 步 → "1 cell(s) — 1 completed, 0 skipped, 0 failed" → 重启再发现全 ✓(2 cell ✓ 完成)。

**E2' blocks (step 8)**: spec 组 62×50×3=9300 → 启动门直接升 E2' 模态:"⚠ 全量 E2' sweep — 62 模型 × 50 数据集 × 3 种子 = 9300 cell / 需维护者显式授权(LNC-03;判定与短语校验不可绕过) / 输入本次输出目录名以确认: finetuned-smoke" → **空回车 ✗ fail-closed;错目录名 wrong-dirname-123 + Enter → ✗ 持续、门不关、run_sweep 进程数不变(仅分离冒烟 1 个)** — 未输入正确短语,全量未启动(遵守 D-15)。

## Advisory findings (non-blocking, 建议后续 UX 修复道)

1. **槽 4 模态关闭后焦点陷阱**: 启动门/预览模态关闭后焦点落入参数 Input;Escape 仅清过滤器不清参数输入焦点;导航数字(1-6)被 Input 吃掉无法换屏;恢复 = 重启 TUI 或不确定的 Tab 链。建议:模态 dismiss 时焦点归还 picker(过滤器 Enter 已有此行为)。
2. **参数输入键盘可达性**: 从 picker 经 Tab 到达 seeds 等输入的链路不可复现(某次 '42' 意外落入 seeds 并持久化);建议明确 Tab 序或参数区专用快捷键。
3. **完成 2/1 分子分母作用域缝**: 重跑填充根上,分子数 root records(2)、分母数 launch-note 当前 run(1) — WR-02 已知残留同类(评审 disposition 已记);显示建议改为双作用域一致。
4. **发现列表/cell 表焦点切换** (Tab) 对盲操作者不直观(Enter 落点易误);底栏键提示可注明当前焦点区。
5. **q 无活 sweep 直接退出**(设计如此—ExitModal 仅活 sweep 时拦截);文案可在底栏注明。

## Gaps

- 分离 sweep 的 CLI 重挂: 已由 tee+manifest+重启再发现覆盖;Windows ledger #20 (GB10 smoke) 可关闭。
