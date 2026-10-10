---
phase: 04-correctness-methodology-core
reviewed: 2026-10-10T06:13:00Z
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
  critical: 1
  warning: 5
  info: 8
  total: 14
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-10-10T06:13:00Z
**Depth:** standard
**Files Reviewed:** 37
**Status:** issues_found

## Summary

Phase 4's data-correctness core holds up under adversarial re-verification. Independently re-run evidence gathered during this review:

- **The data chain is reproducible and matches the committed bytes.** `summarize_comparison.py` re-executed over the 42 real `model_performance` files in a scratch CWD reproduced all four `models_comparison*.json` files **byte-identical** (registry-Category join, `Multiple`→Animals, 22/13 arena counts all confirmed live).
- **The vendored `aggregate_seeds` is faithful.** Code-level diff (comments stripped) against `git show 483a35c:dnallm/finetune/sweep.py` in the read-only DNALLM checkout: **zero diff lines**; all three constants match.
- **The 42/42-changed claim for the regenerated animal file is true** (all 42 models' performance blocks differ vs the pre-fix commit `6bb9364^`; diff classes FLOAT_BIG 321 + INT 55, consistent with the pre-IN-01 labeling note in the commit message).
- **Suite state verified:** 230 fast + 1 slow pytest passed, 5/5 node:test passed, zero xfail markers remain in `test_known_defects.py` (the three D-13 unmarks are real, not marker-drift).
- **Single-navbar-source invariant holds:** exactly one `.navbar-container` on each of the 6 real pages, no static `<nav>` outside the dev mockups; all 6 page modules import and call `renderNavbar()`.
- **IN-03 single authority confirmed:** `summarize_comparison.py` carries no local metric map and imports `resolve_dataset_metric` from the exporter (source-asserted by test and verified by grep).

The findings below are concentrated in the static-site frontend (one genuine leaderboard correctness bug) and in edge/doc mismatches at the exporter boundary. None of them invalidate the Phase 4 data fixes.

## Critical Issues

### CR-01: "Top 10" / "Top 20" filters slice the model list BEFORE sorting — they display an alphabetical subset, not the ranked top N

**File:** `dnallm-mark/js/main.js:101-135` (`filterAndSortModels`)
**Issue:** The filter step runs first: `if (this.state.currentFilter === 'top-20') { models = models.slice(0, 20); }` — slicing `this.state.models`, whose order is the JSON key order of `models_comparison*.json`. Those files are written with `sort_keys=True`, so the list is **alphabetical**, not ranked. The subsequent sort then orders the wrong subset.

Verified against the committed data: with the "Top 10" filter the leaderboard shows `DNABERT-2-117M … ModernBERT-DNA-v1-37M-hg38` (first 10 alphabetically), while the actual top 10 by `rank_score` are `PlantHelixSeek, nucleotide-transformer-v2-500m-multi-species, agro-nucleotide-transformer-1b, …`. The "All Models" view is correct; only the Top-N filters are wrong. This is exactly the class of public-leaderboard incorrectness the milestone exists to prevent, and it sits in the function this phase rewrote for AUD-11 (the sort half was fixed; the ordering vs the slice was not). Pre-existing ordering, but unaddressed and undocumented in a touched function.

**Fix:** Sort first, then slice:
```js
filterAndSortModels() {
  let models = [...this.state.models];
  const sortField = this.state.currentSort;
  const ascending = this.state.sortAscending;
  models.sort((a, b) => { /* existing comparator unchanged */ });
  if (this.state.currentFilter === 'top-20') models = models.slice(0, 20);
  else if (this.state.currentFilter === 'top-10') models = models.slice(0, 10);
  models.forEach((model, index) => { model.displayRank = index + 1; });
  this.state.filteredModels = models;
}
```

## Warnings

### WR-01: Submit-page preview escapes the dataset NAME but not the file-sourced dataset VALUES — contradicts the fix's own stated scope

**File:** `dnallm-mark/js/submit.js:130-153` (`renderPreview`)
**Issue:** The FIX-04 comment (line 130-132) claims "every user-entered string (and file-sourced dataset names) rendered on this page is escaped", and `firstDatasetName` is indeed escaped (line 143). But the same preview table interpolates the uploaded JSON's `firstDataset.dataset?.species`, `.type`, `.labels` (lines 146-148) directly into `innerHTML` unescaped. The uploaded file is the one fully untrusted input on this page (`validateJSON` only checks object presence, never string content), so a crafted submission file executes script in the preview. Mostly self-XSS on a static site, but it is an escaping gap inside the very renderer the fix claims to have covered, and the page is newly re-added to the public nav this phase.
**Fix:** Wrap the four file-sourced interpolations in `DataAPI.escapeHTML(...)` like the neighboring fields (species/type/labels are free strings; keep the numeric `|| 0` defaults outside the escape).

### WR-02: Exporter emits task files for tasks with ZERO completed records, contradicting its contract docstring

**File:** `script/export_runs.py:629-734` (`export_runs_tree`)
**Issue:** The docstring states "For every task (sorted) with at least one completed record, emits ``{safe_task}_task_performance.json``", but the code emits for every task present in the run-record tree. Empirically confirmed during this review: a task whose only `run_record.json` has `status: "failed"` produces `D__task_task_performance.json` with `"performance": {}` and an empty seed-stats doc, and `D__task` is returned in `emitted`. Such a file validates against the schema (the performance map has no `minProperties`), is picked up by `scripts/generate-tasks-index.js` into `tasks.json`, and surfaces in the task-page dropdown as a permanently empty leaderboard.
**Fix:** Skip emission (and do not append to `emitted`) when `performance` is empty after the model loop — or amend the docstring and add a deliberate test pinning the empty-task behavior.

### WR-03: Navbar renders only after the data load succeeds — a fetch failure leaves 5 of 6 pages with no navigation at all

**File:** `dnallm-mark/js/main.js:34-51`, `dnallm-mark/js/task.js:129-154`, `dnallm-mark/js/datasets.js:27-41`, `dnallm-mark/js/models.js:27-41`, `dnallm-mark/js/finetuning.js:28-44`
**Issue:** Every restored page calls `renderNavbar()` after its first `await` (e.g. `await this.loadData(); renderNavbar();`). The setup `catch` only logs, so when the JSON fetch fails (404, CDN/offline hiccup, server not started), the page renders with hero/content containers empty AND no navbar — the user has no way to navigate away. `submit.js` is the only page that renders the navbar synchronously before any I/O. The navbar is static chrome; making it data-dependent is an avoidable robustness regression in the newly restored navigation.
**Fix:** Move `renderNavbar()` to the first line inside the `try` (before `await this.loadData()` / `await this.loader.initialize()`) in the five data-driven pages.

### WR-04: Footer links `/about` and `/blog` point at pages that do not exist; navbar uses root-absolute URLs while every other asset is relative

**File:** `dnallm-mark/index.html:65-66`, `dnallm-mark/task.html:161-162`, `dnallm-mark/js/config.js:50-57`
**Issue:** (a) The footer "Methodology" (`/about`) and "Blog" (`/blog`) links 404 — no `about.html`/`blog.html` exists in the repo; these are user-visible dead links on the public site. (b) `CONFIG.NAV_LINKS` uses root-absolute URLs (`/task.html`, `/finetuning.html`, …) and `navbar.js`'s logo links `/`, while every stylesheet/script/data reference in the same pages is `./`-relative. Under subpath hosting (the common GitHub Pages project-site layout, the documented "GitHub Pages-style" model), every navbar link and the active-state derivation (`currentPage === '/'`) break.
**Fix:** Remove or stub the `/about` + `/blog` footer links; change `NAV_LINKS` to relative URLs (`'./index.html'`, `'./task.html'`, …) and derive the active state from `location.pathname` suffix matching, mirroring the `./` convention the rest of the pages already use.

### WR-05: Arena switch has no rejection handler — `loadData().then(...)` silently no-ops on fetch failure

**File:** `dnallm-mark/js/main.js:456-468` (`bindEvents`)
**Issue:** The arena-button handler is `this.loadData().then(() => { ...re-render... })` with no `.catch`. `DataAPI.loadModelsComparisonByArena` rethrows after logging, so a failed arena file (e.g. `models_comparison_microbe.json` missing or 5xx) produces an unhandled promise rejection and the page stays on the previous arena with zero user feedback — no console-visible error path beyond the DataAPI log, no UI state.
**Fix:** Add `.catch((error) => console.error('Arena switch failed:', error))` and surface a lightweight inline error state (or reuse the leaderboard container with an empty-state message).

## Info

### IN-01: Duplicated assignment `gpu_memory_override = args.gpu_memory`

**File:** `pipeline/run_finetune.py:368-369`
**Issue:** The line appears twice back-to-back; the second is dead. Harmless but noise in a file whose lint scope this project curates deliberately.
**Fix:** Delete line 369.

### IN-02: Stale See-also pointing at the deleted `script/get_task_performance.py`

**File:** `baseline/compare.py:55`
**Issue:** The module docstring's See-also still cites `script/get_task_performance.py` as the "script-skeleton conventions" reference; that file was deleted in 04-05. (Same stale comment also exists in `scripts/generate-tasks-index.js:31` and `script/convert_registry.py:71`, both outside this review's file list.)
**Fix:** Point the See-also at `script/summarize_comparison.py` or `script/export_runs.py`.

### IN-03: Dead frontend aggregation helper and a producer/consumer key mismatch (Models-page Links column can never render)

**File:** `dnallm-mark/js/data.js:204-290`, `dnallm-mark/js/models.js:57-58,119-122`, `script/summarize_comparison.py:370-377`
**Issue:** (a) `DataAPI.recalculateComparison` is referenced by no page and contains knowingly bogus logic (hardcoded `rank = 1`, top-N counts derived from absolute `avgRaw` thresholds) — a live copy of the "duplicate frontend aggregation" anti-pattern. `normalizeToArena` is likewise unused (arena grouping is server-side now). (b) `models.js` renders HuggingFace/ModelScope link columns from `data.model?.huggingface`/`modelscope`, but `summarize_comparison.py` filters the model card to 7 keys that exclude both — the Links column always renders `-` for all 42 models.
**Fix:** Delete `recalculateComparison`/`normalizeToArena` from `data.js`; either add `"huggingface", "modelscope"` to the retained card keys in `summarize_comparison.py` (then regenerate via `make data`) or drop the dead link columns from `models.js`.

### IN-04: SheetJS (xlsx) CDN script loaded on three pages but used by nothing

**File:** `dnallm-mark/index.html:21`, `dnallm-mark/task.html:23`, `dnallm-mark/finetuning.html:13`
**Issue:** `grep` over all page JS finds zero references to `XLSX`/SheetJS — no spreadsheet export exists. The 0.18.5 CDN tag costs load time and adds a third-party script surface (and an offline-breakage dependency) for nothing; the project docs still describe it as "used for spreadsheet export".
**Fix:** Remove the three `<script src="...xlsx.full.min.js">` tags (or implement the export they were loaded for).

### IN-05: Metric dropdown can end up with no selected option while `state.currentMetric` points at the missing metric

**File:** `dnallm-mark/js/task.js:215-231` (`populateMetricDropdown`)
**Issue:** If a dataset's declared primary metric (mapped via AUD-20's `metricMap`) has no non-empty value in any model, `defaultMetric` matches no `availableMetrics` entry: the browser shows the first option as selected while `this.state.currentMetric` is the absent metric, and the leaderboard renders empty even though the visible dropdown suggests otherwise. Requires all 42 models to miss the primary metric, so unlikely on committed data — but the new code makes no attempt to fall back to the first available metric.
**Fix:** `const finalDefault = availableMetrics.includes(defaultMetric) ? defaultMetric : availableMetrics[0];` and use `finalDefault` for both the `selected` attribute and the state assignment.

### IN-06: `submit.js` validation mirrors only 2 of the schema's 3 required-key levels while its docstring claims a structural mirror of the schema

**File:** `dnallm-mark/js/submit.js:159-209`
**Issue:** `validateJSON` checks the top-level `{info, performance}` shape and the per-dataset `dataset/parameters/performance` sub-objects, but not the 11 required `info` card keys (the schema's strictest level). The docstring's "Structural mirror of the schema's required keys" overstates the coverage; a submission with `info: {}` passes client validation.
**Fix:** Either extend the loop to check the 11 info keys, or reword the docstring to "partial structural pre-check; the committed schema remains the gate".

### IN-07: Missing null guards on hero/leaderboard container writes in touched renderers (project convention)

**File:** `dnallm-mark/js/main.js:81,401`, `dnallm-mark/js/datasets.js:73`, `dnallm-mark/js/models.js:69`, `dnallm-mark/js/finetuning.js:59`, `dnallm-mark/js/submit.js:47`
**Issue:** The project convention (CLAUDE.md, and the guarded `renderDatasetsTable`/`renderModelsTable` in the same files) is to null-guard every container query before `innerHTML`. The `renderHero`/`renderLeaderboard` writers query and write without a guard. Benign on the current shells (the elements exist), but inconsistent with the pattern applied two functions below in the same files.
**Fix:** Add the standard `const el = document.querySelector(...); if (!el) return;` guard.

### IN-08: `summarize_comparison.py` docstring claims rank-sorted output files and a bare-`python` invocation that no longer holds

**File:** `script/summarize_comparison.py:45,71-74`
**Issue:** (a) "Each file contains a dict keyed by model alias, sorted by ``rank_score`` descending" — files are serialized with `sort_keys=True`, so key order is alphabetical; ordering lives only in the `rank` field. (b) The Usage block still shows `python ../../script/summarize_comparison.py`, but the script now imports `export_runs` (which imports `scipy` and `yaml` transitively) — the sanctioned `make data` path provides these via the `data` group; a bare interpreter following the docstring can fail at import.
**Fix:** Reword (a) to "each entry carries a `rank` field ordered by `rank_score` descending"; point the Usage block at `make data` (or note the dependency-group requirement).

---

_Reviewed: 2026-10-10T06:13:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
