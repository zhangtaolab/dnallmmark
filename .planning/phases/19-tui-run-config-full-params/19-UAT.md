---
status: complete
phase: 19-tui-run-config-full-params
source: 19-01-SUMMARY.md, 19-02-SUMMARY.md, 19-03-SUMMARY.md
started: 2026-10-24T02:30:00Z
updated: 2026-10-24T02:55:00Z
---

## Current Test

[testing complete]

## Tests

### 1. run_config golden — two-tier structure
expected: 高级参数 section title + 展开高级 affordance + batch_size basic row visible
result: pass
evidence: "run_config.svg text contains 高级参数 title, 展开高级 affordance, batch_size row with —（默认: 按序列长度动态缩放）placeholder, collapsed section below the basic rows"

### 2. run_config golden — default placeholders + hint lines
expected: default-value placeholders on visible advanced rows; YAML-variance hint + EBS/GA 重算 hint render
result: pass
evidence: "两条提示逐字可见: 空 = YAML 默认；变体配置默认不同 / 设置 effective_batch_size 时 GA 仍由其重算; 默认: 占位语法 present"

### 3. run_config golden — basic rows intact
expected: seeds/epochs/workers/gpus/batch_size/EBS/输出根 rows unchanged above the advanced section
result: pass
evidence: "42,43,44 prefill, epochs 覆盖 row, effective_batch_size row, workers1, GPUs—（默认: GPU 0..workers-1), 目录（默认仓库… all render above 高级参数"

### 4. run_config_confirm golden — gate + dispatch-plan
expected: confirm gate copy + dispatch-plan line carrying 0,1 + params context
result: pass
evidence: "确认启动以上训练？— [Y] 启动 / [N] 取消 + 调度计划: 2 workers × GPUs 0,1 · 排队 6 + 1 任务 × 3 种子 = 6 训练项"

### 5. FHS journey ordered stage set (docs/live/fhs/svg)
expected: 001..015 stages present in operation order; 012 params shows batch typed; 013 argv preview carries --batch_size 32; 014 confirm gate
result: issue
resolved_by: "inline-fix-e39e290 (modal pre-wrap + 013b tail frame)"
reported: "013_run_config_preview 帧无法显示 --batch_size 32：31 个数据集的超长 argv 溢出 120×40 设计视口（--workers 2 --gpus 0,1 --models FungiHelixSeek、42,43,44 可见，batch_size 段被裁）。运行时断言走控件全文比对已通过且 evidence.json 留存 argv 段（['--batch_size','32']）——证据链完整，仅静态帧装不下"
severity: minor
evidence: "16 prefix stages in exact operation order (001→014 + 006×2/007×2 interval pairs); 012 shows batch 32; 014 carries 0,1; 003 model name visible"

### 6. FHS monitor frames advancing
expected: 015_monitor_running_NNN monotonic sequence with distinct content across intervals (heartbeat evidence)
result: pass
evidence: "80 frames, 80/80 distinct sha256 (no duplicated captures), last frame carries progress glyphs"

### 7. pa6 journey record intact (docs/live/svg)
expected: committed 25-frame 2×2 journey: 06 confirm gate + 99 done frame present
result: pass
evidence: "25 frames; 06_run_config_confirm.svg + 999.. (99_monitor_done) present"

## Summary

total: 7
passed: 6
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "013 argv 预览帧应显示 --batch_size 32"
  status: failed
  reason: "User directive check: 31-task argv exceeds the 120x40 viewport; the token falls outside the captured frame (runtime assertion + evidence argv segment both correct)"
  severity: minor
  test: 5
  root_cause: "The [p] preview modal renders the full argv in a scrollable log; export_screenshot captures the viewport only — no scroll-to-token before the 013 export"
  artifacts:
    - path: scripts/live/record_tui_live_svg.py
      issue: "013 capture does not scroll the preview modal to the argv tail before export"
  missing:
    - "Scroll the modal (or capture a second scrolled frame 013b) so --batch_size/--seeds tokens are visible for long task lists"
  debug_session: ""
  resolved_by: "inline-fix-e39e290"
  resolved_at: "2026-10-24"
