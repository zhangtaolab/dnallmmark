---
status: passed
phase: 10-data-manager-downloads-verification
source: [10-VERIFICATION.md]
started: 2026-10-13T04:31:00Z
updated: 2026-10-13T04:45:00Z
---

## Current Test

number: 1
name: Live download loop (d → 真下载 → 落地对账 → 三面翻转)
expected: |
  make tui → 3数据管理: missing pane lists committed-baseline missing keys;
  cursor on a missing row → d → enqueued toast + queue row ◌→⠋ with live progress;
  real modelscope download lands → landing check → real audit reconcile →
  queue row ✓ 完成 100% + ✓ N 行一致; missing pane drops the key (缺失 n-1, 在场 n+1);
  2模型·数据集 (m 数据集视图): the row flips ✗→✓ with measured split rows;
  1环境检查 [r]: re-run green.
awaiting: (none — verified 2026-10-13 by orchestrator-driven live-app testing per maintainer delegation "你用 SKILL 自己测试")

## Tests

### 1. Live download loop (real network, real subprocess, three surfaces)
expected: d → download → reconcile → missing-pane drop + selection flip + env green.
result: pass

### 2. `g` re-audit four-artifact write-back (R-03)
expected: real audit subprocess with default outputs → git status shows EXACTLY the four artifacts; semantic diff = the missing→present flips; worktree restored pending maintainer baseline ruling.
result: pass

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Evidence (2026-10-13, live app via tmux 140x45 + real service call)

**Item 1 — live loop** (real GB10 network + real modelscope CLI + real audit leg):
boot → `3` → 数据管理: 在场 43/50 · 缺失 7 (7 GUE keys, baseline rows shown) → cursor to `GUE__virus_species_40` (5,000) → `d` → toast "✓ 已入队: GUE__virus_species_40" + queue row ⠋ 下载中 with animating progress bar → ~40s real download → queue row `✓ 完成 100% · ✓ 5000 行一致`; missing pane `缺失 7→6`, `在场 43→44` (CR-01 fix live-proven on the real service path); `2` → `m` (数据集视图) → filter → `GUE__virus_species_40 ✓ 4,000/500/500` (presence overlay + measured split rows through the app event forward); `1` → `r` → 环境就绪 (dataset dir scan green). Landed files verified: train 4001/dev 501/test 501 lines (header-inclusive) == 4,000/500/500 rows == declared. Zenodo line live: `[z] Zenodo 整包 · 未公开（探测于 04:32）` (real 404 probe).

**Item 2 — `g` four-artifact check** (service tier, same subprocess/argv the g binding drives):
`reaudit_baseline('uat-reaudit-1')` → ok, 23.9s, `git status` = EXACTLY DATA.md + dnallm-mark/data/n_audit.csv + dnallm-mark/data/n_audit.json + pipeline/eval_subsets.json. Semantic diff: exactly the 7 keys missing→False. **Discovery: the refreshed baseline reads 50/50 present, 0 missing — the committed baseline is stale: the other 6 "missing" GUE keys already have complete CSVs on disk (downloaded outside the TUI at some point).** Worktree restored per R-03 (maintainer commits the new baseline); the refresh is reproducible any time via `g`-on-mismatch / the service call.

**Advisory observations (non-blocking)**: (a) `g` correctly no-ops when the queue has no mismatch row (binding is live on mismatch rows only — observed live; documented behavior); (b) with the filter Input focused on slot 2, plain keys are consumed by the filter (typed `m` appended to the filter text) — standard Textual focus semantics, Esc clears; not a defect.

## Gaps

- Pre-activation gate (carried from review): before Zenodo record 19135551 publishes, maintainer must rule bundle overwrite/cap/staging (IN-06) and land per-chunk cancel (IN-10).
- Baseline decision: refreshed n_audit (50/50 on disk) awaits maintainer commit ruling.
