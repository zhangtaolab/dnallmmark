---
status: testing
phase: 09-custom-model-dataset-onboarding
source: [09-VERIFICATION.md]
started: 2026-10-12T11:15:00Z
updated: 2026-10-12T11:15:00Z
---

## Current Test

number: 1
name: Live console wizard loop (w → 录入 → 校验 → gauntlet → 落盘 → u 撤销 → e 停用)
expected: |
  make tui → 2模型·数据集: w on the model table opens the model wizard (4 steps, type-aware controls);
  submit with a broken field → collect-all numbered problem list, nothing written, values preserved;
  fix → gauntlet panel rows run ◌→⠋→✓/✗ → all-✓ lands → ◇ badge + count segment updates;
  u undoes the just-landed entry; e toggles a custom entry with toast + loader-skip visibility;
  same for the dataset table (w there opens the dataset wizard). esc mid-flow cancels cleanly.
awaiting: user response

## Tests

### 1. Live console wizard loop (both kinds, broken-field recovery, gauntlet, land, undo, toggle)
expected: w from both tables; collect-all report on bad input; gauntlet all-✓→land→◇ badge→counts; u undo; e toggle; esc-cancel.
result: [pending]

### 2. Cross-machine share-unit round trip (CUST-06)
expected: export (o) the custom registry on this machine to a file; copy it elsewhere (or simulate another machine's HOME via DNALLMMARK_TUI_CONFIG_DIR); import (f) it there; per-entry gauntlet runs; entry lands. The flagged planner assumption — surfaced in 09-06-SUMMARY.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
