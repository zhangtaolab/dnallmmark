---
phase: 04-correctness-methodology-core
reviewed: 2026-10-10T06:36:46Z
depth: standard
files_reviewed: 37
files_reviewed_list:
  - Makefile
  - baseline/compare.py
  - dnallm-mark/data/models_comparison_animal.json
  - dnallm-mark/data/models_comparison_microbe.json
  - dnallm-mark/datasets.html
  - dnallm-mark/finetuning.html
  - dnallm-mark/index.html
  - dnallm-mark/js/data.js
  - dnallm-mark/js/datasets.js
  - dnallm-mark/js/finetuning.js
  - dnallm-mark/js/main.js
  - dnallm-mark/js/models.js
  - dnallm-mark/js/navbar.js
  - dnallm-mark/js/submit.js
  - dnallm-mark/js/task.js
  - dnallm-mark/models.html
  - dnallm-mark/submit.html
  - dnallm-mark/task.html
  - pipeline/models_info.json
  - pipeline/run_finetune.py
  - pyproject.toml
  - script/export_runs.py
  - script/freeze_snapshot.py
  - script/summarize_comparison.py
  - tests/conftest.py
  - tests/fixtures/export_chain/defect_species_performance.json
  - tests/fixtures/synthetic_datasets_info.json
  - tests/js/data-escape.test.js
  - tests/js/main-topn-filter.test.js
  - tests/test_aggregation.py
  - tests/test_export_runs.py
  - tests/test_freeze_snapshot.py
  - tests/test_golden.py
  - tests/test_known_defects.py
  - tests/test_model_registry.py
  - tests/test_registry_unification.py
  - tests/test_run_finetune_contracts.py
  - tests/test_vendored_stats.py
findings:
  critical: 0
  warning: 0
  info: 1
  total: 1
status: clean
---

# Phase 4: Code Review Report (Iteration 2 — Convergence Check)

**Reviewed:** 2026-10-10T06:36:46Z
**Depth:** standard
**Files Reviewed:** 37
**Status:** clean

## Summary

This iteration re-verified all six iteration-1 fixes at source level (current tree, not just the diffs), hunted regressions inside the six fix diffs (`383f33c`, `b36b119`, `daf5dc4`, `3cd090d`, `d8956a4`, `00c19a2`), and ran a standard pass for new actionable findings outside the standing dispositions. **All six fixes are correct and complete; no regressions found; no new Critical or Warning findings.** Zero Critical/Warning remain — convergence is clean per the iteration's criteria (Info-only).

Evidence gathered independently during this review:

- **Suite state independently reproduced:** `uv run --group dev pytest` → **232 passed** in 7.78s (0 xfailed); `node --test tests/js/` → **8/8 pass**; `ruff check` over the full lint scope → all checks passed; `ty check` → all checks passed. Matches the claimed state exactly.
- **Working tree clean** over the 37-file review scope (no uncommitted source drift; only untracked `.planning/` artifacts).

### Fix-by-fix verification

**CR-01 — Top-N slice-after-sort (`dnallm-mark/js/main.js:103-139`, commit `383f33c`) — CORRECT.** `filterAndSortModels` now sorts by the active field first (`main.js:106-122`), slices top-20/top-10 at lines 127-132, then assigns `displayRank = index + 1` over the *filtered* list (lines 134-136). Verified against committed data: `models_comparison.json` `rank` ordering equals `rank_score`-descending ordering across all 42 models (no tie divergence), so the default view's display ranks agree with the authoritative `rank` field. The new behavioral test (`tests/js/main-topn-filter.test.js`) genuinely discriminates: the ranked top 10 deliberately includes the alphabetical tail (`model-k`..`model-o`), so a slice-before-sort regression cannot pass, and a third test explicitly pins the "Top-N follows the active sort" semantics as design. `displayRank` semantics (1..N display position, not the JSON `rank` field) match the fix prescribed in iteration 1 and are test-pinned; every consumer (`renderModelRow`, task-page rows) renders only freshly ranked `filteredModels`, so no stale-rank path exists.

**WR-01 — submit preview escaping (`dnallm-mark/js/submit.js:136-158`, commit `b36b119`) — COMPLETE.** All seven file-sourced preview cells (species/type/labels, train/test/dev, accuracy/f1/auroc) are now wrapped in `DataAPI.escapeHTML(String(...))`; the `String()` coercion is necessary and correct because `escapeHTML` passes non-strings through unchanged (`data.js:173-174`), and the numeric/`'N/A'` defaults stay outside the escape as intended. Remaining interpolations in the file are either user-entered-and-escaped (summary block, PR instructions), regex-sanitized (`branchName`/`alias`, `submit.js:226-228`), or numeric (`datasetCount`). No unescaped file-sourced interpolation remains on this page.

**WR-02 — exporter zero-completed skip (`script/export_runs.py:728-734`, commit `daf5dc4`) — COMPLETE.** The `continue` fires when `performance` is empty after the model loop and skips all three effects the docstring contract requires: the task file write, the stats-artifact write, and the `emitted.append(task)`. The regression test (`tests/test_export_runs.py::test_zero_completed_task_emits_nothing`) asserts all three non-existence properties plus the `emitted == ["FakeDS__task"]` exclusion, and passed in this review's run. Downstream consumers (index generator, goldens) are file-scan-based, so fewer emitted files is safe; the unregistered-dataset hard-fail (`datasets_info[task]`) still applies to dead tasks, consistent with the hard-fail design.

**WR-03 — navbar before first await (commit `3cd090d`) — COMPLETE in all 5.** Verified in the current tree: `main.js:40-41`, `task.js:135-137`, `datasets.js:33-34`, `models.js:33-34`, `finetuning.js:34-35` each call `renderNavbar()` as the first statement inside `setup()`'s `try`, before `await this.loadData()` / `await this.loader.initialize()`. `submit.js:32` was already synchronous. `renderNavbar` is null-guarded and reads no fetched data, so the early call cannot fail on data grounds; a failed fetch on any page now still leaves full navigation.

**WR-04 — relative nav URLs + suffix active-link (commit `d8956a4`) — COMPLETE and CORRECT.** The dead `/about` and `/blog` footer links are gone from `index.html` and `task.html`; grep confirms no root-absolute or dead links remain on any of the six real pages (only `task-mockup.html` retains them — standing disposition: dev artifact intentionally untouched). `CONFIG.NAV_LINKS` is fully `./`-relative (`config.js:52-59`) and every target file exists. The suffix-based active-link derivation (`navbar.js:25-27,35`) was simulated across five representative pathnames — `/`, `/index.html`, `/task.html`, subpath directory `/dnallm-mark/`, subpath file `/dnallm-mark/task.html` — and selects the correct active link in every case; `location.pathname` excludes query/hash so those cannot perturb it.

**WR-05 — arena-switch rejection handler (`dnallm-mark/js/main.js:470-486`, commit `00c19a2`) — CORRECT.** The `.catch` logs and renders an inline error state into `.leaderboard-container` using the existing `.empty-state` CSS classes (verified present in `css/components.css:354-375`); the interpolated arena id is escaped (defense-in-depth — the value originates from `CONFIG.ARENAS` anyway). The comment's retry claim holds: the click handler has no same-arena early-return guard, so clicking the failed arena button re-runs `loadData`. The delegated sort-header listener on the container survives the `innerHTML` replacement (it is bound to the container element), so no listener is orphaned by the error state.

### Regression hunt on the six diffs

No regressions found. Specific interactions checked and cleared: the `displayRank` mutation only touches filtered models and every render path re-runs `filterAndSortModels` first; the JS comparator is stable and treats missing metrics as `0`; moving `renderNavbar()` earlier introduces no data dependency; the exporter skip does not bypass the unregistered-dataset/`FLOPs` hard-fails; the navbar suffix comparison handles root, file, and subpath-hosting pathnames; the arena-switch error state does not break the persistent delegated listeners.

## Info

### IN-09: After a failed arena switch, `state.currentArena` points at the failed arena while the page keeps rendering the previous arena

**File:** `dnallm-mark/js/main.js:463-486`
**Issue:** The arena handler sets `this.state.currentArena` before `loadData()` and the new catch does not roll it back. After a failure the visible page remains internally consistent (old arena's chart + leaderboard error state + old-arena nav highlight, and the error message correctly names the failed arena), but the stale pointer means a subsequent filter-button click (`main.js:491-499`) re-renders the previous arena's models over the error message while state claims the new arena. This is error-path-only (requires a mid-session fetch failure), the displayed numbers are never mislabeled, and the pre-fix behavior was identical minus the error state — so it is a residual of the fix's declared scope, not a regression. Recording it so the state-rollback option is on file if arena switching is ever revisited.
**Fix (optional):** Snapshot `const prevArena = this.state.currentArena` before the assignment and restore it in the `.catch`.

---

### Standing dispositions honored (not re-reported)

Per the iteration context, the following remain documented-open and were excluded from this convergence pass: IN-01..IN-08 from iteration 1; empty-string card values as documented convention; residual escaping outside the touched renderers (`finetuning.js`, `datasets.js`, `models.js` tables, task-page dropdown) as documented acceptance; the formerly-locked defects fixed-by-design this phase; `task-mockup.html` dev artifact intentionally untouched.

---

_Reviewed: 2026-10-10T06:36:46Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (iteration 2 — convergence check)_
