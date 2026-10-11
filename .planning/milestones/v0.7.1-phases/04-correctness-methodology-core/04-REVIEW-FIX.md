---
phase: 04-correctness-methodology-core
fixed_at: 2026-10-10T06:27:38Z
review_path: .planning/phases/04-correctness-methodology-core/04-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 4: Code Review Fix Report

**Fixed at:** 2026-10-10T06:27:38Z
**Source review:** .planning/phases/04-correctness-methodology-core/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope (critical + warning): 6
- Fixed: 6
- Skipped: 0

IN-01..IN-08 are documented-open and out of fix scope for this run (per the
review-fix hard constraints); the standing non-findings (unmarked locks,
empty card values) were not touched.

## Fixed Issues

### CR-01: "Top 10" / "Top 20" filters slice the model list BEFORE sorting

**Files modified:** `dnallm-mark/js/main.js`, `tests/js/main-topn-filter.test.js` (new)
**Commit:** 383f33c
**Applied fix:** `filterAndSortModels()` now sorts with the existing comparator first
(default `rank_score` descending — the leaderboard's own sort semantics) and slices the
Top-20/Top-10 filter from the SORTED list, then assigns `displayRank` over the filtered
view. Added a behavioral node:test (`tests/js/main-topn-filter.test.js`, 3 tests) that
imports the real `main.js` ES module under a minimal `document` stub and drives
`filterAndSortModels` through a prototype instance with a 15-model alphabetically-ordered
fixture whose ranked top 10 sits in the alphabetical tail — verified to FAIL on the
pre-fix code (1/3 fail) and PASS on the fixed code (3/3 pass).

### WR-01: Submit-page preview escapes the dataset NAME but not the file-sourced dataset VALUES

**Files modified:** `dnallm-mark/js/submit.js`
**Commit:** b36b119
**Applied fix:** All file-sourced preview-table interpolations are now wrapped in
`DataAPI.escapeHTML(String(...))`: species/type/labels (the three named cells), the
train/test/dev row, and accuracy/f1/auroc — the last three are the same untrusted-input
class (the uploaded JSON is the page's one fully untrusted input and `validateJSON` never
inspects string content), so the fix covers the whole table rather than only the three
named lines. `String()` coerces before escaping because `escapeHTML` passes non-strings
through unchanged; the `|| 0` / `|| 'N/A'` defaults keep their original semantics outside
the escape. The FIX-04 scope comment was updated to state the widened coverage.

### WR-02: Exporter emits task files for tasks with ZERO completed records

**Files modified:** `script/export_runs.py`, `tests/test_export_runs.py`
**Commit:** daf5dc4
**Applied fix:** Took the fix option that enforces the documented contract:
`export_runs_tree` now `continue`s (no task file, no seed-stats artifact, no `emitted`
entry) when the `performance` map is empty after the model loop, with a comment explaining
why (an empty performance map validates against the schema — no `minProperties` — and
would surface as a permanently empty leaderboard entry via `tasks.json`). The docstring's
"at least one completed record" wording already documents this and is unchanged. Added
`test_zero_completed_task_emits_nothing` pinning the behavior end-to-end over a fixture
task whose only record has `status: "failed"`.

### WR-03: Navbar renders only after the data load succeeds

**Files modified:** `dnallm-mark/js/main.js`, `dnallm-mark/js/task.js`, `dnallm-mark/js/datasets.js`, `dnallm-mark/js/models.js`, `dnallm-mark/js/finetuning.js`
**Commit:** 3cd090d
**Applied fix:** In all five data-driven pages, `renderNavbar()` is now the first
statement inside the `try` — before `await this.loadData()` (main/datasets/models/
finetuning) and before `await this.loader.initialize()` (task) — so a failed fetch leaves
the static navigation chrome usable. `submit.js` already rendered the navbar
synchronously and was not touched.

### WR-04: Footer links `/about` and `/blog` point at pages that do not exist; navbar uses root-absolute URLs

**Files modified:** `dnallm-mark/index.html`, `dnallm-mark/task.html`, `dnallm-mark/js/config.js`, `dnallm-mark/js/navbar.js`
**Commit:** d8956a4
**Applied fix:** (a) Removed the dead Methodology (`/about`) and Blog (`/blog`) footer
anchors from `index.html` and `task.html` (Discord remains). (b) `CONFIG.NAV_LINKS` now
uses `./`-relative URLs (`'./index.html'`, `'./task.html'`, ...) and the navbar logo links
`./index.html`; the active-link derivation compares the pathname's file suffix
(`'/''-terminated paths resolve to `index.html`) against the link URL, which works
unchanged under subpath hosting (GitHub Pages project-site layout). Note:
`task-mockup.html` (a dev mockup, unlinked from navigation and outside the finding's file
list) still carries the dead footer links deliberately.

### WR-05: Arena switch has no rejection handler

**Files modified:** `dnallm-mark/js/main.js`
**Commit:** 00c19a2
**Applied fix:** The arena-button handler's `loadData().then(...)` chain now has a
`.catch` that logs `Arena switch failed:` and renders a lightweight inline error state
into the leaderboard container using the existing `.empty-state` / `.empty-state-text` /
`.empty-state-hint` CSS components. On failure the page keeps the previous arena's
rendered content and category-nav highlight (`renderCategoryNav()` only runs on success),
so the user can retry by switching arenas again.

## Verification

**Where verification ran:** all gates ran inside the isolated review-fix worktree
(`gsd-reviewfix/04-454899`, since fast-forwarded into `autorun` and removed), invoking the
main checkout's uv-managed `.venv` binaries by absolute path (`pytest`, `ruff`, `ty`).
The suite numbers are therefore reproducible from the main checkout after the
fast-forward, where `make test` / `make lint` / `make typecheck` run the same commands;
the only worktree artifact was that bare `ty check` could not auto-discover the
environment (no local `.venv`) and needed `--python /home/forrest/Github/dnallmmark/.venv/bin/python`
— with it, ty is clean.

- Full pytest suite: **232 passed, 0 xfailed** (baseline 231 passed + 0 xfailed; +1 from
  the new WR-02 exporter test)
- node:test JS lane: **8 passed** (baseline 5; +3 from the new CR-01 test file)
- `ruff check` (the `make lint` scope): **All checks passed**
- `ty check`: **All checks passed** (with the venv interpreter, as noted above)
- CR-01 regression proof: new test run against the pre-fix `main.js` fails (1/3), against
  the fixed file passes (3/3)

## Skipped Issues

None — all six in-scope findings were fixed.

---

_Fixed: 2026-10-10T06:27:38Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
