---
status: passed
phase: 08-tui-foundation-env-check-selection
source: [08-VERIFICATION.md]
started: 2026-10-12T02:13:00Z
updated: 2026-10-12T02:13:00Z
---

## Current Test

number: 1
name: Interactive `make tui` on GB10 over SSH/tmux — real kernels
expected: |
  Startup runs the full environment check with REAL kernels (CUDA/matmul on this GB10 GPU):
  rows fill asynchronously 待检 → 检查中… → ✓/✗ in main() kernel order; the 上次检查: YYYY-MM-DD HH:MM
  line shows after persist; enter on a row opens the verbatim drill-down modal; r (refresh) re-runs
  the check live; s opens the selection screen (k9s filter /, spacebar mark, m model/dataset toggle,
  p presets, v matrix read-only view); q quits cleanly (exit 0).
awaiting: (none — maintainer validated 2026-10-12: 全过)

## Tests

### 1. Interactive make tui on GB10 (real CUDA/matmul kernels, async fill, cache line, drill-down, refresh, clean quit)
expected: make tui boots the console; env-check rows fill one by one with real kernel results; a second launch same-day reads the cache instantly (上次检查 line, no kernel run); drill-down shows verbatim detail; refresh re-runs; q exits cleanly.
result: pass

### 2. CJK/glyph legibility on the operator's real terminal
expected: ✓/✗/⚠ glyphs, Chinese labels (环境检查, 已标记, 上次检查), and the footer keycaps render legibly over the operator's actual SSH/tmux terminal (assumption A2 — exotic-terminal glyph coverage explicitly out of CI scope per the UI-SPEC resolution).
result: pass

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
