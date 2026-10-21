---
phase: 17-web-multiseed-error-bars
plan: 1
subsystem: data-chain
tags: [jsonschema, numpy, zero-drift, population-std, additive-optional-fields, export-runs, summarize-comparison]

# Dependency graph
requires:
  - phase: 05-data-chain-f6 (D-16 dual-view exporter)
    provides: export_runs_tree single-pass dual-view emission + the vendored aggregate_seeds banner (edit-forbidden) the ddof=0 helper sits beside
  - phase: 15-dual-gpu-validation-subsets (E2'/e2_replay fixtures)
    provides: tests/fixtures/e2_replay 3-seed run-record fixture + the chain staging patterns the additive gate reuses
provides:
  - population_std(values) ddof=0 helper in script/export_runs.py (outside the vendored banner) — the single display-side std authority
  - Optional entry-level mean/std/n_seeds trio in BOTH export views ({task}_task_performance.json + {model}_performance.json), gated on the declared primary metric with >= 2 completed seeds
  - dataset_seed_stats extraction (5-tuple load_model_inputs) + conditional per-model std/n_seeds in aggregate_models — all four models_comparison*.json views inherit uniformly
  - Strict-schema optional-field additions in schemas/task_performance.json, schemas/model_performance.json, schemas/models_comparison.json (properties-only, required/additionalProperties unchanged)
  - The additive-case zero-drift gate extension (test_trio_is_additive_over_trio_stripped_inputs) + the export-side degenerate/multi-seed trio pins + aggregate_models propagation unit pins
  - docs/METHODOLOGY.md appendix fixing sd (ddof=1, reviewer view) vs std (ddof=0, display whiskers) once, with the display-only declaration
affects: [17-02 (JS error-bar rendering reads these fields), 17-03 (full phase gates), maintainer post-milestone regeneration]

# Actuals (#2632) — pairs with the plan's estimate (tokens 23000, tasks 3, confidence high).
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 11000
  tasks: 3
  commits: 3
  plan_head_before: 62c0fcec3ddb8304cf4740a144f5f61ab8a16e0a
  plan_head_after: e218ee967be72124b7d9588fa2cd7a90b56f89b5

# Tech tracking
tech-stack:
  added: []  # zero installs — stdlib/numpy arithmetic only over locked groups (T-17-SC held)
  patterns:
    - "Additive-only JSON emission behind a presence gate, proven per direction (absent case = unmodified test_determinism over committed bytes; additive case = trio-stripped only-new-keys equivalence)"
    - "ddof discipline: two named std conventions with separate owners (vendored sd ddof=1 reviewer view vs population_std ddof=0 display view), pinned distinct by test"
    - "Optional schema fields land properties-only in the SAME commit as producers + tests (D-01/D17-04)"

key-files:
  created: []
  modified:
    - script/export_runs.py
    - script/summarize_comparison.py
    - script/permutation_tests.py
    - schemas/task_performance.json
    - schemas/model_performance.json
    - schemas/models_comparison.json
    - tests/test_export_runs.py
    - tests/test_ci_replay.py
    - tests/test_aggregation.py
    - docs/METHODOLOGY.md

key-decisions:
  - "population_std lives DIRECTLY after the END-vendored marker, never inside the banner; nothing between banner start and END changed (test_vendored_stats green unmodified)"
  - "The trio gates on resolve_dataset_metric(datasetRow.metric) resolved once per task; mean reuses the identical float(np.mean(ordered)) expression so it is bit-equal to the emitted primary-metric slot"
  - "Emission gate = n_seeds >= 2 (Q2 ruling); std is never derived from sd and never sd/sqrt(n)"
  - "Per-model propagation (Q1 ruling): std = mean of per-task population stds over tasks carrying std, n_seeds = min per-task count — emitted INSIDE aggregate_models (the include_weighted conditional shape) so all four arena files inherit uniformly; ranking math untouched"
  - "The new multi-seed export test declares the fixture metric 'AUROC' (resolves to the auroc slot its metrics carry) because the committed schema enum surface has no AUROC dataset — schema-VALIDATED trio emission is proven over e2_replay (enum-legit AUPRC + eval_AUPRC values)"

patterns-established:
  - "Presence-gated optional-field extraction in load_model_inputs (dataset_seed_stats): only absence is absent — a genuine 0.0 std IS recorded, never get_float-with-default-0"
  - "Required-key sets derived in tests from the raw schema JSON via json.loads (ty-clean; the validator's .schema attribute is Mapping|bool and not subscriptable)"

requirements-completed: [WEB-01]

# Coverage metadata (#1602) — one entry per shipped deliverable.
coverage:
  - id: D1
    description: "population_std (ddof=0) helper + entry-level mean/std/n_seeds trio emitted in BOTH export views, gated on the declared primary metric with >= 2 completed seeds; 1-seed/absent cells emit nothing"
    requirement: WEB-01
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py#test_multi_seed_cell_emits_population_std_trio"
        status: pass
      - kind: unit
        ref: "tests/test_export_runs.py#test_one_seed_cell_emits_degenerate_statistics"
        status: pass
      - kind: unit
        ref: "tests/test_vendored_stats.py (green unmodified — the banner pin)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Strict-schema optional-field additions (mean/std/n_seeds + per-model std/n_seeds) in properties ONLY across task_performance, model_performance, models_comparison — required arrays and additionalProperties:false unchanged"
    requirement: WEB-01
    verification:
      - kind: unit
        ref: "tests/test_schemas.py (all committed files revalidate; 145 passed alongside determinism/aggregation)"
        status: pass
      - kind: integration
        ref: "tests/test_ci_replay.py#test_export_half_emits_schema_valid_task_file_with_n3_t_intervals + test_full_d16_chain_emits_both_views_then_aggregates_over_model_view (trio-carrying files validate against the updated schemas)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Per-model std/n_seeds propagation through summarize (5-tuple load_model_inputs, aggregate_models conditional emission) into all four comparison views, with the zero-drift gate split proven: absent case via UNMODIFIED test_determinism over the committed tree, additive case via the new trio-stripped equivalence test"
    requirement: WEB-01
    verification:
      - kind: integration
        ref: "tests/test_ci_replay.py#test_trio_is_additive_over_trio_stripped_inputs"
        status: pass
      - kind: integration
        ref: "tests/test_determinism.py (passes UNMODIFIED — regenerated bytes byte-identical to committed over the real single-run tree)"
        status: pass
      - kind: unit
        ref: "tests/test_aggregation.py#test_seed_stats_propagation_mean_of_stds_and_min_n + test_seed_stats_absent_model_emits_no_keys + test_seed_stats_none_and_empty_maps_emit_nothing_anywhere"
        status: pass
    human_judgment: false
  - id: D4
    description: "docs/METHODOLOGY.md appendix fixing sd (ddof=1, reviewer seed_stats) vs std (ddof=0, display whiskers) once, the n>=2 gate, the per-model mean-of-stds + min-n semantics, and the display-only declaration (no ranking/methodology/data version change)"
    requirement: WEB-01
    verification:
      - kind: other
        ref: "test \"$(grep -c ddof docs/METHODOLOGY.md)\" -ge 2 (returned 2; baseline was 0)"
        status: pass
    human_judgment: false

# Metrics
duration: 16min
completed: 2026-10-21
status: complete
---

# Phase 17 Plan 1: Data-Chain Tracer (WEB-01) Summary

**Additive multi-seed trio (mean/std/n_seeds, population ddof=0) threaded end-to-end through export_runs dual views and summarize per-model propagation — with test_determinism.py green UNMODIFIED over the committed tree as the crown absent-case proof**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-21T09:26:34Z
- **Completed:** 2026-10-21T09:42:29Z
- **Tasks:** 3/3
- **Files modified:** 10 (exactly the declared files_modified set)

## Accomplishments

- Task 1 (tracer): `population_std` helper (ddof=0) directly after the END-vendored marker; `export_runs_tree` resolves the dataset's primary metric slot once per task and captures the trio inside the metric_block loop (`mean` = the identical `float(np.mean(ordered))` expression, bit-equal to the metric slot), attaching it at ENTRY level to BOTH the task-view and model-view entries — one emission covers both D-16 views; 1-seed/absent cells attach nothing
- Both strict schemas gained the optional trio properties-only, same commit as producers; the vendored pin (test_vendored_stats) and every committed-data check stayed green; the export suite gained the degenerate-absence pin (n=1 on the declared primary metric emits nothing in either view) and the multi-seed pin (mean bit-equality, ddof=0 value 0.016330 on the fixture, std != sd conflation guard, failed-seed exclusion, both-view agreement)
- Task 2: `load_model_inputs` 5-tuple with presence-gated `dataset_seed_stats`; `aggregate_models` keyword-only propagation in the exact `include_weighted` conditional shape (per-model std = mean of per-task population stds, n_seeds = min), threaded by `main()` into both aggregation calls so all four arena files inherit uniformly; the one other caller (permutation_tests.py:230) gained the fifth underscore; models_comparison schema gained std/n_seeds properties-only
- The zero-drift gate split landed: additive case via `test_trio_is_additive_over_trio_stripped_inputs` (a trio-stripped copy of the emitted model view aggregates byte-equal on every pre-existing key — only std/n_seeds differ) plus chain-test key-set pins (datasetEntries exactly base+trio; comparison performance exactly 16+{std, n_seeds}; ReplayModel-A std ≈ 0.00081650 = population std of auprc seeds 0.93/0.931/0.932, n_seeds == 3); absent case proven by tests/test_determinism.py and the synthetic single-run golden passing UNMODIFIED
- Task 3: METHODOLOGY appendix naming sd (ddof=1) and std (ddof=0) distinctly with the display-only declaration and Q1/Q2 rulings; three aggregate_models unit pins (mixed-task presence, absent model, None/empty maps); close-out gates green — ddof grep = 2, 145 passed (aggregation + determinism + schemas), `make lint` and `make typecheck` clean, pinned CI lane 85 passed, `git status --porcelain dnallm-mark/data/` empty (no regeneration — deferred to the maintainer per the plan prohibition)

## Task Commits

Each task was committed atomically:

1. **Task 1: TRACER — schemas + population_std helper + export trio emission in both views** - `59ec1f4` (feat)
2. **Task 2: summarize per-model std/n_seeds propagation + additive-case zero-drift gate** - `e122c59` (feat)
3. **Task 3: METHODOLOGY appendix + aggregation unit pins + close-out gates** - `e218ee9` (docs)

**Plan metadata:** (see final docs commit below)

## Files Created/Modified

- `script/export_runs.py` - population_std helper + trio emission in the shared metric_block/task_entry/model_entry path (vendored banner untouched)
- `script/summarize_comparison.py` - 5-tuple load_model_inputs + dataset_seed_stats kwarg on aggregate_models + main() threading
- `script/permutation_tests.py` - the single destructure fix (fifth underscore)
- `schemas/task_performance.json` - modelEntry optional mean/std/n_seeds + Phase-17 $comment
- `schemas/model_performance.json` - datasetEntry optional mean/std/n_seeds + Phase-17 $comment
- `schemas/models_comparison.json` - performance optional std/n_seeds + Phase-17 $comment
- `tests/test_export_runs.py` - degenerate trio-absence pin + test_multi_seed_cell_emits_population_std_trio
- `tests/test_ci_replay.py` - chain trio key-set/value pins + test_trio_is_additive_over_trio_stripped_inputs + REQUIRED_PERF_KEYS from raw schema JSON
- `tests/test_aggregation.py` - three aggregate_models propagation unit pins
- `docs/METHODOLOGY.md` - "Appendix: Display error bars (multi-seed std)"

## Decisions Made

- population_std placed directly after the END-vendored marker as a NEW sibling — the banner stayed byte-identical (test_vendored_stats green unmodified proves it)
- The new multi-seed export test declares the fixture metric "AUROC" (resolves to the auroc slot the fixture's eval_AUROC metrics carry): the committed schema enum surface has no AUROC dataset, so that test pins VALUES without schema validation while schema-VALIDATED trio emission is proven over e2_replay (enum-legit "AUPRC" + eval_AUPRC) — both halves covered, neither weakened
- The degenerate test now plants a genuine 1-seed value on the DECLARED primary metric (eval_AUPRC added to FakeModel-B's lone seed), so the n>=2 emission gate itself — not key absence — is what the absence assertion pins
- dataset_seed_stats uses isinstance guards + math.isfinite (bool excluded, matching export_runs._finite) rather than get_float-with-default — a genuine 0.0 std IS recorded; only absence is absent

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ty not-subscriptable on the validator's .schema attribute**
- **Found during:** Task 3 (make typecheck gate)
- **Issue:** REQUIRED_PERF_KEYS was derived via `COMPARISON_SCHEMA.schema["$defs"]...` — jsonschema types `.schema` as `Mapping | bool` (a schema may be a bare boolean), so ty rejects subscripting it and `make typecheck` exited 1
- **Fix:** Derive the key set from the raw schema JSON via `json.loads` (the same idiom the module uses to build the validators); json.loads yields Any so the subscript is clean
- **Files modified:** tests/test_ci_replay.py
- **Verification:** `make typecheck` → "All checks passed!"; tests/test_ci_replay.py 6 passed
- **Committed in:** e218ee9 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Gate-level fix in new test code only; zero production-code impact, zero scope creep.

## Issues Encountered

None beyond the auto-fix above. All verify lanes passed on first run after each task's edits.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 17-02 (JS error-bar rendering) can read the optional fields: entry-level trio in `{task}_task_performance.json` (bar chart via TaskLoader) and per-model `performance.std`/`n_seeds` in `models_comparison*.json` (scatter via DataAPI) — tolerant reads per D17-08
- The committed `dnallm-mark/data/` tree is byte-identical to HEAD (regeneration deferred to the maintainer post-milestone, per plan prohibition) — 17-02's Node fixtures come from the r2/archived artifacts, not from regeneration
- Full phase gates run in 17-03 after the JS legs land
- No blockers

## Self-Check: PASSED

All 11 files (SUMMARY + 10 modified) exist on disk; all 3 task commits (59ec1f4, e122c59, e218ee9) are ancestors of HEAD.

---
*Phase: 17-web-multiseed-error-bars*
*Completed: 2026-10-21*
