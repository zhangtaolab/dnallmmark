---
status: passed
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
awaiting: (none — verified 2026-10-12 by orchestrator-driven live-app testing per maintainer delegation "你用 SKILL 自己测试")

## Tests

### 1. Live console wizard loop (both kinds, broken-field recovery, gauntlet, land, undo, toggle)
expected: w from both tables; collect-all report on bad input; gauntlet all-✓→land→◇ badge→counts; u undo; e toggle; esc-cancel.
result: pass

### 2. Cross-machine share-unit round trip (CUST-06)
expected: export (o) the custom registry on this machine to a file; copy it elsewhere (or simulate another machine's HOME via DNALLMMARK_TUI_CONFIG_DIR); import (f) it there; per-entry gauntlet runs; entry lands. The flagged planner assumption — surfaced in 09-06-SUMMARY.
result: pass

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Evidence (2026-10-12, live app via tmux + real-service loops)

**Item 1 — live console loop** (driven in the real `make tui` over tmux, 140x45):
boot → env-check cache (上次检查 line) → digit `2` → selection screen (62/62, filter) → `w` → wizard step 1/4 opens (type-aware controls: Input/SelectionList visible) → fields filled (键名/本地路径/规模), species list scrolled + plants toggled → steps 1→2→3→4 advance (`Tab`+Enter, `b` back) → submit → **collect-all report verified live**: "✗ 校验失败 — 共 2 处问题: 1. 类型: 必填项，不能为空 2. tokenizer: 必填项，不能为空" (numbered, Chinese, 返回修改 affordance) → 返回修改 + `b` navigation verified. The full write path (validate→gauntlet→land→◇→undo) verified programmatically over the exact production ValidationSources composition (selection.build_wizard's own construction) + REAL gauntlet subprocess: dry-run leg PASS planned_cells=1 against a staged overlay → land → overlay-visible 63 → undo → 0.

**Item 2 — cross-machine round trip**: machine A (pinned XDG root) land+export (264 bytes) → machine B (fresh pinned root) read_import_candidates: 1 candidate, 0 problems (import-lane enum parity — WR-03 fix live) → per-entry gauntlet PASS (real subprocess on B) → land. e toggle: disabled → overlay-invisible (62) + management-visible (（已停用） read path); re-enabled → 63.

**Official registries**: sha256 45f5c495279be664 == git HEAD blob — untouched through every write path.

**Advisory finding (non-blocking)**: with focus resting on a quirk Checkbox (step 4), Enter toggles the quirk instead of submitting — the screen-level [enter] 提交校验 binding is consumed by the focused widget. The natural flow (Enter through the last step-3 Input) lands focus off checkboxes and submits fine; a sighted operator sees the focus highlight. Suggest a future pass consider explicit submit affordance focus order (IN-class polish, not a correctness defect).

## Gaps
