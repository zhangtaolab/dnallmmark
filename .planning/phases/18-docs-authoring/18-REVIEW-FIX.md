---
phase: 18-docs-authoring
fixed_at: 2026-10-22T08:03:16Z
review_path: .planning/phases/18-docs-authoring/18-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 2
status: all_fixed
---

# Phase 18: Code Review Fix Report

**Fixed at:** 2026-10-22T08:03:16Z
**Source review:** `.planning/phases/18-docs-authoring/18-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope (fix_scope=critical_warning): 3 (all Warnings)
- Fixed: 3
- Skipped: 2 (both Info — out of scope for iteration 1, recorded as skipped-info)

**Commit strategy:** one atomic commit per finding (three commits), as permitted by the task brief.

## Fixed Issues

### WR-01: multi-gpu.md still carries the pre-review 60 s stale-grace value the phase corrected everywhere else

**Files modified:** `docs/multi-gpu.md`
**Commit:** `06800cd`
**Applied fix:** The dispatch-mode "Watch" bullet (line ~291) now reads "stale-marked once its snapshot's age crosses the cell-scale grace (`DISPATCH_STALE_SECONDS` = 3600 s, maintainer-tunable)" — matching the shipped source (`tui/services/dispatch_state.py:74`, `DISPATCH_STALE_SECONDS = 3600.0`) and the three sibling surfaces. The reviewer's suggested snippet was adapted to preserve the surrounding sentence flow and line wrapping.
**Verification (grep):** zero `60 s` residue in `docs/multi-gpu.md`; 3600 s / `DISPATCH_STALE_SECONDS` now consistent across all four surfaces — `docs/multi-gpu.md:292`, `docs/TUI-GUIDE.md:177,199`, `docs/TUI-DEMO.md:203`, `docs/v1.3-test-report.html:337,443,455`.

### WR-02: The report-assets honesty ledger table is split by a blank line — 5 of 7 assets render outside the table

**Files modified:** `docs/report-assets/README.md`
**Commit:** `ae67b82`
**Applied fix:** Deleted the blank line (was line 14) between the `monitor_running.svg` row and the `shot-scatter-tooltip.png` row. The ledger is now one continuous GFM table: header (line 10) + delimiter (line 11) + 7 contiguous asset rows (lines 12-18).
**Verification (grep):** lines 10-18 of the file are 9 pipe-initial rows with 0 non-pipe lines inside the block; asset pipe-row count = 7 (`shot-scatter.png`, `monitor_running.svg`, `shot-scatter-tooltip.png`, `shot-bars.png`, `shot-bars-tooltip.png`, `run_config.svg`, `run_config_confirm.svg`).

### WR-03: TUI-DEMO now contradicts itself — the re-record section's collision guarantee is false under the Phase-16 semantics §11 documents

**Files modified:** `docs/TUI-DEMO.md`
**Commit:** `8c74b25`
**Applied fix:** Rewrote the "Re-recording any GIF" bullet (line 235) from the false "EHC-3 single-GPU guard … it can never stack onto your real run" guarantee to the Phase-16 capacity semantics: the gate refuses at stage 0 when the live registry's GPU demand plus the re-record's requested workers exceeds the machine's effective GPU count; within spare capacity a demo launch IS allowed to stack (live 1-worker sweep + 1-worker re-record fits the 2-GPU validation box), and an unset GPUs field defaults both launches onto GPUs `0..workers-1` so they contend on GPU 0 — operators are told to size `workers`/`GPUs` so the re-record cannot land on a GPU a live sweep occupies. Wording mirrors §11 (line 201) and TUI-GUIDE.md:165 (EHC-3 as amended by Phase 16).
**Verification (grep):** zero hits for "never stack" / "single-GPU guard" in `docs/TUI-DEMO.md`; corrected capacity-arithmetic sentence present at line 235. Line 108's demo-scene narration ("serialization guard" describing the recorded scene) was not flagged by the review and was left untouched per surgical-fix discipline.

## Skipped Issues

### IN-01: README's example suite count is 493 tests behind the v1.3 baseline the report cites

**File:** `README.md:185`
**Reason:** skipped-info — Info-tier finding, out of scope for iteration 1 (fix_scope=critical_warning).
**Original issue:** The `make test` example says "1743 passed in ~4.5m" while the v1.3 recorded baseline is "2236 passed / 3 skipped / 6 environmental" (17-VERIFICATION.md:121). Hedged as "counts grow", so informational.

### IN-02: Absolute machine paths quoted in the multi-gpu.md subset evidence block

**File:** `docs/multi-gpu.md:354-359`
**Reason:** skipped-info — Info-tier finding, out of scope for iteration 1 (fix_scope=critical_warning); reviewer's own fix line is "Optional".
**Original issue:** The subset-workflow "expected output" block quotes `/root/autodl-tmp/...` machine-local evidence paths verbatim in three places (deliberate verbatim quoting, report-HTML zero-absolute-paths gate was scoped to the report only).

## Verification

- Per-fix grep assertions (documented per finding above) all passed BEFORE each commit.
- Full gates `make lint` (ruff) and `make typecheck` (ty): **All checks passed** for both.
- **Gates ran in the MAIN checkout** (`/root/autodl-tmp/Github/dnallmmark`, branch `autorun`) AFTER the cleanup-tail fast-forward captured the three fix commits — the isolated worktree has no `.venv`, so its numbers would not have been reproducible from the main tree. Commits were authored in the isolated worktree `gsd-reviewfix/18-627285` and fast-forwarded to `autorun` (`f20e956..8c74b25`).
- No push performed — local commits only (milestone ruling 2026-10-20).

---

_Fixed: 2026-10-22T08:03:16Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
