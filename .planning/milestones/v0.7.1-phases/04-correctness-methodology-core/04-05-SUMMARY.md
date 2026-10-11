---
phase: 04-correctness-methodology-core
plan: 05
subsystem: data-chain
tags: [pivot-retirement, oq4-species-correction, in-03-single-mapping-authority, in-08-lint-scope, golden-rework, determinism-rescope]

# Dependency graph
requires:
  - phase: 04-correctness-methodology-core
    provides: 04-02's exporter core (mapping table, run-record reader, dual emitter) and 04-01's Category grouping + regenerated comparison files (make data already a no-op pre-plan)
provides:
  - SC-2 input-side retirement complete: script/get_task_performance.py + tests/test_pivot.py DELETED; the pivot semantics are owned and asserted by tests/test_export_runs.py over both the committed synthetic_task_performance fixture and the exporter's own emission
  - tests/fixtures/synthetic_task_performance/ — the pivot's own final deterministic output (byte-identical across two runs, FIX-05), committed as the golden/JS-generator input
  - Re-scoped golden + determinism lanes: chain = summarize + JS generator only; task_performance files are static committed inputs until E2' (nothing in the repo can overwrite them — T-04-11)
  - OQ4 discharged: the 2 committed task files' info.species corrected to the registry Category (EPI_GM12878 Microbe->Animals, fungi_species_20 Animals->Microbe) + tasks.json regenerated, exactly-3-file inventory in the commit message (T-04-12); no known-wrong species value remains in committed data
  - IN-03 resolved by removal: summarize_comparison's metric_key_map mirror DELETED; export_runs.resolve_dataset_metric() is the single authority over both key surfaces (suite canonicals + legacy dataset-metric spellings), parity-enumerated against the deleted mirror's exact slots (T-04-13)
  - Carryover Q4 discharged in one hygiene commit: convert_registry.py in make lint scope (IN-08, clean on arrival) + README exporter documentation
affects: [E2' regeneration (exporter is the only task_performance input path), Phase 5 permutation tests (single mapping authority), Phase 6 freeze/packaging]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 18626     # 74,504 diff chars / 4 over base bda6a8c..HEAD
  tasks: 2
  commits: 5        # MEASURED: git rev-list --count bda6a8c..HEAD at SUMMARY time
plan_head_before: bda6a8c789b3526fe32d2bd1a5e503dc817c6ab5
plan_head_after: 2a26a6600db3dc6cfac647bc5989f52c63b16a43

# Tech tracking
tech-stack:
  added: []          # no new dependencies (hard constraint held)
  patterns:
    - "Coverage fold on deletion: every pinned behavior of a deleted test file is enumerated into its successor (fold mapping table in the SUMMARY), with structurally-unreachable halves accounted rather than silently dropped"
    - "Chain-produced fixture as frozen input: the deleted generator's own deterministic final output becomes the committed fixture the successor tests assert against"
    - "Single translation function with the deleted mirror's identity fallback: unknown keys pass through unchanged, so consolidation provably moves no number (parity test + make data no-op)"

key-files:
  created:
    - tests/fixtures/synthetic_task_performance/   # 3 files — the pivot's final output
  modified:
    - tests/test_export_runs.py        # +5 folded pivot-shape tests, +3 IN-03 parity/authority tests
    - tests/test_golden.py             # chain re-scoped: summarize + JS gen over the committed fixture
    - tests/test_determinism.py        # chain re-scoped: task files are copied inputs; guard intact
    - tests/conftest.py                # sys.path comment (get_task_performance gone)
    - tests/test_aggregation.py        # minimal-copy mapping -> exporter import; values unchanged
    - Makefile                         # data target two-line chain + lint scope += convert_registry.py
    - script/export_runs.py            # +LEGACY_DATASET_METRIC +resolve_dataset_metric (IN-03)
    - script/summarize_comparison.py   # mirror deleted; translation imported; docstring updated
    - README.md                        # exporter section + regeneration docs made honest
    - dnallm-mark/data/task_performance/GUE__EPI_GM12878_task_performance.json   # 1 line
    - dnallm-mark/data/task_performance/GUE__fungi_species_20_task_performance.json  # 1 line
    - dnallm-mark/data/tasks.json      # 2 species entries regenerated
  deleted:
    - script/get_task_performance.py
    - tests/test_pivot.py

key-decisions:
  - "Fold split by reachability: the retired sanitizer test's '/' half is structurally unreachable through the exporter's F2 directory walk (a path component can never contain '/'), so the fold live-tests the backslash half through the real emission path and keeps '/' in the sanitizer as defense-in-depth — accounted here per the plan's fold-or-account prohibition"
  - "resolve_dataset_metric preserves the deleted mirror's identity fallback (unknown declarations pass through unchanged and simply miss in the performance block) — this is what makes the consolidation provably number-neutral on committed data (survey: f1/mcc/spearmanr/AUPRC only)"
  - "TDD split commits honored the task-level tdd='true': RED 9bb8491 (3 target tests failing with the module importing cleanly) -> GREEN d059f2c, per the reference's commit-scope contract; no refactor needed (GREEN landed in final form)"
  - "The OQ4 correction landed as its own commit immediately after the retirement commit (the plan's preferred alternative), so the 2-file + tasks.json inventory is attributable in isolation (T-04-12) and the retirement's make data no-op was proven BEFORE the data changed"

patterns-established:
  - "Delete-and-fold with a committed final-output fixture: the retiring producer's deterministic output is captured as the fixture its successor's tests assert against (golden continuity without keeping dead code)"
  - "Parity-enumerated mapping consolidation: the deleted table's full key surface is pinned test-first to identical outputs before the implementation lands"

requirements-completed: [REV-03, FIX-02]

coverage:
  - id: D1
    description: "SC-2/OQ6 pivot retirement: script/get_task_performance.py + tests/test_pivot.py deleted; every pinned pivot behavior folded into tests/test_export_runs.py over the committed synthetic_task_performance fixture AND the exporter's own emission; fixture chain-produced once (byte-identical across two runs) before deletion"
    requirement: REV-03
    verification:
      - kind: command
        ref: "test ! -e script/get_task_performance.py && test ! -e tests/test_pivot.py -> PIVOT_GONE"
        status: pass
      - kind: unit
        ref: "tests/test_export_runs.py#test_pivot_shape_committed_fixture_one_file_per_dataset, #test_pivot_shape_committed_fixture_info_mirrors_dataset_block, #test_pivot_shape_missing_metric_model_still_present, #test_pivot_shape_exporter_emission_owns_the_shape, #test_pivot_shape_exporter_sanitizes_task_filenames"
        status: pass
    human_judgment: false
  - id: D2
    description: "Golden + determinism lanes re-scoped, not weakened: golden compares the 4 comparison goldens + tasks.json golden over the new input set (synthetic models + committed fixture + registry slice); determinism runs summarize + JS generator twice over copied model_performance AND task_performance inputs, asserts run1==run2 AND outputs == committed 4 comparisons + tasks.json, trailing git-status guard intact"
    requirement: REV-03
    verification:
      - kind: unit
        ref: "tests/test_golden.py (3 tests) + tests/test_determinism.py#test_chain_is_deterministic_and_matches_committed — green in make test (231 passed)"
        status: pass
      - kind: integration
        ref: "make data && git status --porcelain dnallm-mark/data/ empty -> CLEAN (chain reproduces every committed derived file byte-identically from the new input set)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Makefile data target is the two-line chain (summarize from dnallm-mark/data/ + node scripts/generate-tasks-index.js) with the comment documenting task_performance/ as committed static data until E2' regenerates it via script/export_runs.py; conftest sys-path comment updated"
    requirement: REV-03
    verification:
      - kind: command
        ref: "make data -> CLEAN (byte-identical no-op over the committed tree, both before and after the OQ4 correction)"
        status: pass
    human_judgment: false
  - id: D4
    description: "OQ4 species correction: exactly the info.species line in each of the 2 named task files (EPI_GM12878 Microbe->Animals, fungi_species_20 Animals->Microbe) + tasks.json regenerated via the JS generator (its 2 species entries); schema-valid after the swap; inventory recorded in the commit message"
    requirement: FIX-02
    verification:
      - kind: command
        ref: "plan verify assertion over the 2 files + tasks.json entries -> SPECIES_CORRECT; git diff bda6a8c..HEAD -- dnallm-mark/data/ = exactly 3 files, 4 lines (2 one-line task edits + 2 tasks.json species entries)"
        status: pass
      - kind: unit
        ref: "schema validation over all committed JSON green in make test (tests/test_schemas.py within 231 passed)"
        status: pass
    human_judgment: false
  - id: D5
    description: "IN-03 by removal: metric_key_map gone from summarize_comparison.py; export_runs.resolve_dataset_metric() owns both key surfaces — the legacy dataset-metric aliases (F1/MCC/AUROC/AUPRC/MSE/MAE/R2/pearsonr/spearmanr) resolve to the deleted mirror's exact slots (parity-enumerated), test_aggregation imports the same function, every expected value unchanged"
    requirement: REV-03
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py#test_legacy_dataset_metric_alias_parity_with_deleted_mirror, #test_resolve_dataset_metric_identity_for_committed_surface, #test_single_mapping_authority_summarize_imports_exporter_table"
        status: pass
      - kind: command
        ref: "! grep -q metric_key_map script/summarize_comparison.py -> MIRROR_DELETED; plan legacy-surface verify -> RESOLVES; make data -> CLEAN (numbers did not move)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Carryover Q4 hygiene (one commit): script/convert_registry.py joins make lint scope (IN-08, ruff-clean on arrival); README gains the Export Runs to the Leaderboard section next to the Run Pipeline instructions with the E2' regeneration path + static-data status"
    requirement: REV-03
    verification:
      - kind: command
        ref: "make lint (convert_registry.py in scope) -> All checks passed; ruff I001 on the new import fixed in the same commit per the plan's fresh-findings clause"
        status: pass
    human_judgment: false

# Metrics
duration: 16 min
completed: 2026-10-10
status: complete
---

# Phase 4 Plan 05: Pivot Retirement + OQ4 Correction + IN-03 Single Mapping Authority Summary

**Legacy model->task pivot deleted with its coverage folded into the exporter's tests (one committed final-output fixture), the 2 known-wrong committed species values corrected with inventory, and the exporter's translation made the single metric-key authority over both key surfaces**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-10T05:34:19Z
- **Completed:** 2026-10-10T05:50:44Z
- **Tasks:** 2/2
- **Files:** 16 (1 fixture dir created, 2 deleted, 13 modified)

## Accomplishments

- **Pivot retired with zero coverage loss (Task 1):** `script/get_task_performance.py` and `tests/test_pivot.py` deleted; the fixture `tests/fixtures/synthetic_task_performance/` (3 files) was chain-produced by the pivot's own deterministic code immediately before deletion (run twice, byte-identical — FIX-05) and committed as the golden/JS-generator input. Every pinned pivot behavior is now owned by `tests/test_export_runs.py` (fold mapping below).
- **Golden + determinism re-scoped honestly (Task 1):** the chain is `summarize_comparison` + the JS index generator only. The golden lane drives summarize (synthetic registry slice injected) + the generator over the committed fixture — all 4 comparison goldens + the tasks.json golden stay value-identical with zero edits. The determinism lane copies `model_performance` AND `task_performance` as inputs, runs the chain twice, proves run1==run2 AND outputs == the committed files, and keeps the trailing git-status guard (the suite never writes the committed data).
- **OQ4 discharged the moment the pivot stopped existing to overwrite it (Task 1):** exactly one `info.species` line changed in each of the 2 conflicting task files (GUE__EPI_GM12878 Microbe->Animals, GUE__fungi_species_20 Animals->Microbe, per the maintainer-confirmed Category review); tasks.json regenerated (exactly its 2 species entries); the complete data diff is the 3 inventoried files / 4 lines, recorded verbatim in the commit message (T-04-12). The task page is immediately correct; no known-wrong species value remains anywhere in committed data.
- **IN-03 resolved by removal (Task 2, TDD):** `metric_key_map` deleted from `summarize_comparison.py`; `export_runs.resolve_dataset_metric()` — one function owning `LEGACY_DATASET_METRIC` (F1/MCC/MSE/MAE/R2 -> canonicals; AUROC/AUPRC and pearsonr/spearmanr need no entry) + `CANONICAL_TO_EXPORT` + the deleted mirror's identity fallback — is the single authority, imported by both `summarize_comparison.py` and `tests/test_aggregation.py`. RED (9bb8491) pinned the deleted mirror's 9-key surface to identical slots before the implementation (d059f2c) landed; every expected value and every committed number is unchanged (`make data` byte-identical no-op).
- **Carryover Q4 closed (Task 2):** `script/convert_registry.py` joins `make lint` (IN-08, clean on arrival); README gained the "Export Runs to the Leaderboard" section (run-record -> task_performance + seed statistics, the E2' path) and its regeneration docs were made honest about the two-line chain and the static-until-E2' status of `task_performance/`.
- **Gates:** suite 231 passed + 0 xfailed + node lane 5 (baseline 226: -3 pivot tests, +5 folded shape tests, +3 IN-03 tests); `make lint` + `make typecheck` zero-diagnostics over the widened scope; `make data` byte-identical no-op before AND after the data correction.

## Task Commits

Each task was committed atomically (Task 2 is tdd="true" and follows the RED -> GREEN commit-scope contract; no refactor was needed):

1. **Task 1 (retirement + rework):** `186794d` (refactor) — pivot deleted, fixture committed, fold, golden/determinism rework, Makefile/conftest
2. **Task 1 (OQ4 correction, immediately following):** `aa27ea3` (fix) — the 2 species lines + regenerated tasks.json, inventory in the message
3. **Task 2 (RED):** `9bb8491` (test) — 3 target tests failing with the module importing cleanly (AttributeError on the absent entry point + the still-present mirror)
4. **Task 2 (GREEN):** `d059f2c` (feat) — resolve_dataset_metric + mirror deletion + imports
5. **Task 2 (hygiene, carryover Q4):** `2a26a66` (chore) — IN-08 lint scope + README exporter docs + ruff I001 fix

**Plan metadata:** (docs commit follows this SUMMARY)

## Pivot Coverage Fold Mapping (tests/test_pivot.py -> tests/test_export_runs.py)

Per the plan's no-coverage-loss prohibition, the fold is enumerated:

| Retired test_pivot.py behavior | Folded into test_export_runs.py |
|---|---|
| One output file per dataset, named `{dataset}_task_performance.json` | `test_pivot_shape_committed_fixture_one_file_per_dataset` (fixture) + `test_pivot_shape_exporter_emission_owns_the_shape` (emitter naming) |
| `info` mirrors the input `dataset` block verbatim | `test_pivot_shape_committed_fixture_info_mirrors_dataset_block` (fixture) + the emitter's 8-key info equality with the registry join, already pinned in `test_end_to_end_emission_validates_against_unchanged_schema` |
| Per-model blocks keep the 11/9/14 (model/parameters/performance) key shape | Same two tests (key-count assertions on every block, both surfaces) |
| Missing-metric model still present, its metric still `""` (only ranking excludes it) | `test_pivot_shape_missing_metric_model_still_present` (fixture); the emitter's own `""`-emission was already pinned in `test_end_to_end_...` (`mse == ""`) |
| `/` and `\` sanitized to `_` in filenames | `test_pivot_shape_exporter_sanitizes_task_filenames` — the backslash half is live-tested through the exporter's real F2 walk (a legal POSIX path component); the `/` half is **structurally unreachable** through the exporter's directory-name-derived task names (a path component can never contain `/`) and stays in the sanitizer (`task.replace("/", "_").replace("\\", "_")`) as defense-in-depth at the emission boundary — accounted here, not folded, per the plan's fold-or-account rule |

## Files Created/Modified

- `tests/fixtures/synthetic_task_performance/` — 3 files: the pivot's own final output, committed as input
- `tests/test_export_runs.py` — +8 tests total (5 folded shape tests + 3 IN-03 tests)
- `tests/test_golden.py`, `tests/test_determinism.py` — chain re-scoped (docstrings document the static-until-E2' status)
- `tests/test_aggregation.py` — minimal-copy mapping replaced by the exporter import; expected values unchanged
- `tests/conftest.py` — import-roots comment updated
- `script/export_runs.py` — `LEGACY_DATASET_METRIC` + `resolve_dataset_metric` (docstring documents both surfaces + identity fallback)
- `script/summarize_comparison.py` — mirror deleted (:295-305), lookup imports the translation, docstring cross-references updated
- `Makefile` — data target (two-line chain + comment), lint scope (+convert_registry.py)
- `README.md` — exporter section, regeneration chain, structure block
- `dnallm-mark/data/task_performance/{GUE__EPI_GM12878,GUE__fungi_species_20}_task_performance.json`, `dnallm-mark/data/tasks.json` — the OQ4 correction
- DELETED: `script/get_task_performance.py`, `tests/test_pivot.py`

## Decisions Made

- Fold split by reachability (see fold mapping): the `/` sanitization half is accounted as structurally unreachable via the exporter's input surface rather than tested through an artificial path — folding it would have required fabricating an input the F2 layout cannot produce.
- `resolve_dataset_metric` keeps the deleted mirror's identity fallback so unknown metric declarations behave exactly as before (miss in the performance block) — the property that makes IN-03 provably number-neutral.
- The OQ4 correction landed as its own commit (the plan's sanctioned alternative to one-commit) so the retirement's `make data` no-op was proven over the pre-correction tree first, and the data inventory is attributable in isolation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Doc correctness] README regeneration docs referenced the deleted script**
- **Found during:** Task 2 (hygiene commit)
- **Issue:** Beyond the plan's exporter sentence, README carried three live instructions pointing at `get_task_performance.py` (the "Generate Task Performance Data" command block, the full-chain note, the project-structure entry) — after Task 1's deletion these instructed users to run a nonexistent script.
- **Fix:** Within the already-planned README edit: rewrote the section as "Task Performance Data (per-dataset files)" stating the static-until-E2' status, corrected the full-chain note to the two-line `make data` chain, and swapped the structure-block entry to `export_runs.py`.
- **Files modified:** README.md
- **Verification:** `grep get_task_performance README.md` -> 0 hits; docs consistent with the Makefile.
- **Committed in:** 2a26a66

**2. [Rule 3 - Lint blocker] ruff I001 on the new summarize import**
- **Found during:** Task 2 verify (`make lint`)
- **Issue:** `from export_runs import resolve_dataset_metric` placed in its own block after pandas — ruff's isort wants it inside the third-party block (export_runs is not detected as first-party).
- **Fix:** `ruff check --fix` merged it into the third-party block — exactly the plan's "fix any fresh ruff findings in convert_registry.py and the touched files" clause.
- **Files modified:** script/summarize_comparison.py
- **Verification:** `make lint` -> All checks passed (over the widened scope).
- **Committed in:** 2a26a66

---

**Total deviations:** 2 auto-fixed (doc correctness, lint blocker)
**Impact on plan:** None on the plan's truths — both fixes are within files the plan already touches; all acceptance criteria green.

## Issues Encountered

None beyond the deviations above. Two execution notes: (a) the determinism lane's git-status guard correctly tripped while the OQ4 edits were uncommitted (it fired on the pending working-tree changes, not on chain output — resolved by committing, exactly the guard's read-only-committed-data contract); (b) the plan's `make data ... CLEAN` verify was checked pre-commit as "make data introduces no additional diff over the corrected working tree" and post-commit as the literal empty-porcelain check — both held.

## User Setup Required

None - no external service configuration required.

## Authentication Gates

None encountered.

## Next Phase Readiness

- Phase 4 is complete (5/5 plans). The data chain is honest: `make data` = summarize + index generator; `task_performance/` is static until E2' regenerates it via `script/export_runs.py` (the only input path).
- Suite baseline for the next phase: 231 passed + 0 xfailed + node lane 5.
- Deferred (deferred-items.md): 3 dangling doc cross-references to the deleted script in `baseline/compare.py`, `script/convert_registry.py`, `scripts/generate-tasks-index.js`; stale `.claude/CLAUDE.md` profile references (regenerate at next profile refresh).

## Self-Check: PASSED

- Files verified on disk: tests/fixtures/synthetic_task_performance/ (3 files), script/export_runs.py, script/summarize_comparison.py, README.md, Makefile, the 3 corrected data files — all FOUND; script/get_task_performance.py and tests/test_pivot.py — confirmed ABSENT (PIVOT_GONE)
- Commits verified as ancestors of HEAD: 186794d, aa27ea3, 9bb8491, d059f2c, 2a26a66 — all FOUND
- Commits measured from ledger base bda6a8c: 5 (matches the task commits; docs commit follows)
- All plan acceptance criteria re-run post-commit: PASS (PIVOT_GONE; SPECIES_CORRECT; 3-file/4-line data diff exactly; make data CLEAN; MIRROR_DELETED; RESOLVES; 48/48 aggregation+exporter; make test 231 passed + node lane 5; lint + typecheck clean)

---
*Phase: 04-correctness-methodology-core*
*Completed: 2026-10-10*
