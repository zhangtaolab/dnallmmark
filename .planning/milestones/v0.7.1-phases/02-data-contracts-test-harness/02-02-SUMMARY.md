---
phase: 02-data-contracts-test-harness
plan: "02"
subsystem: testing
tags: [pytest, node-test, golden-files, synthetic-fixtures, pandas-rank, data-chain]

# Dependency graph
requires:
  - phase: 02-data-contracts-test-harness plan 01
    provides: conftest sys.path roots (summarize_comparison/get_task_performance/compare), thread pinning + slow marker, schemas/model_performance.json, Makefile test/test-fast lanes
provides:
  - Synthetic fixture tree (tests/fixtures/synthetic_models/, 3 models x 3 datasets) engineered for exact-tie / missing-metric / regression-metric / one-dataset-per-species edges, all schema-valid
  - Committed golden file set (tests/fixtures/golden/, 4 models_comparison* + tasks.json) chain-produced and value-compared via baseline/compare.py walk()
  - tests/test_aggregation.py (30 items), tests/test_pivot.py (3 items), tests/test_golden.py (3 items), tests/js/generate-tasks-index.test.js (node:test, 2 items)
  - make test now runs pytest plus node --test tests/js/ (the JS lane is never silently skipped)
  - get_float non-finite pass-through pinned as plain assertions (the fact 02-03's WR-03 xfail lock builds on)
affects: [02-03, 04-correctness-fixes, 05-ci-packaging]

actuals:
  tokens: 13358   # chars/4 over the realized diff (53433 diff chars across 13 files)
  tasks: 3
  commits: 3      # MEASURED: git rev-list --count ff37f5f..HEAD (#3968)
plan_head_before: ff37f5f047e4e6440b0683bf8fcd597d46d1a287
plan_head_after: ba2348f1efcda0236f199ea588c25a4bc83810b9

# Tech tracking
tech-stack:
  added: []    # nothing new — node:test is a Node builtin; pytest/jsonschema landed in 02-01
  patterns:
    - chain-produced goldens (never hand-authored) value-compared with the canonical compare.walk vocabulary, zero diffs of any class incl. FLOAT_ULP on the same machine
    - copy-into-fixture-tree JS testing (module executes at import and resolves __dirname-relative paths; copying into an OS-tmp tree is the only side-effect-free access)
    - approx-everywhere float policy in tests with plain == reserved for ints (rank/samples/counts); np.float64 leaks make exact float == forbidden
    - fixture-driven aggregate tests: a helper replicates main()'s presence-gate extraction so unit expectations and the committed fixtures stay one source

key-files:
  created:
    - tests/fixtures/synthetic_models/fake-alpha_performance.json
    - tests/fixtures/synthetic_models/fake-beta_performance.json
    - tests/fixtures/synthetic_models/fake-gamma_performance.json
    - tests/fixtures/golden/models_comparison.json
    - tests/fixtures/golden/models_comparison_animal.json
    - tests/fixtures/golden/models_comparison_plant.json
    - tests/fixtures/golden/models_comparison_microbe.json
    - tests/fixtures/golden/tasks.json
    - tests/test_aggregation.py
    - tests/test_pivot.py
    - tests/test_golden.py
    - tests/js/generate-tasks-index.test.js
  modified:
    - Makefile

key-decisions:
  - "Constant-score guard test uses binary-exact 0.5 (not the plan's 0.7): np.std([0.7]*3) is one ULP above zero, so the std==0 guard never fires for decimal constants — a companion test pins the all-models-equal invariant for 0.7 instead of the ULP-level degenerate value"
  - "Gamma's total rank_score asserted as 0 (the plan's '= 1' arithmetic slip): gamma is rank 3 of 3 on FakeDS__regress_task (0.4 < 0.5 < 0.6), so 0 + excluded + 0 = 0; the final-rank claim 1/2/3 beta/alpha/gamma is unaffected"
  - "Golden generation is one flow: the test itself produces tasks.json via the JS copy trick, and the committed goldens were byte-copied from an identical scratch chain run in the same task that proves zero-diff regeneration"

patterns-established:
  - "Golden-test pattern: chdir into tmp copy of fixtures, run main()s + JS copy trick, value-compare via from compare import walk with diffs == [] (FLOAT_ULP included on the same machine)"
  - "JS unit-lane pattern: node:test CommonJS, Node builtins only (zero npm per the architecture constraint), mkdtemp fixture trees always cleaned up in finally"
  - "Hand-computed expectation tables in test docstrings (per-dataset rank/score breakdown) so reviewers can verify the math without running anything"

requirements-completed: [TEST-01, TEST-02, TEST-03]  # verbatim from plan frontmatter; REQUIREMENTS.md checkbox gated on 02-03 for shared TEST-02/TEST-03

# Coverage metadata (#1602) — one entry per shipped deliverable
coverage:
  - id: D1
    description: "Synthetic fixture tree: 3 fake models in exact committed shape, schema-valid, engineered for exact-tie pair (0.9/0.9/0.8), missing-metric empty-string, spearmanr regression path, and one dataset per species group"
    requirement: TEST-01
    verification:
      - kind: other
        ref: "command: uv run --group dev Draft202012Validator over 3 fixtures -> 0 errors ('3 fixtures schema-valid')"
        status: pass
      - kind: other
        ref: "command: python edge-case assertions (tie exact, gamma f1 == '', shared dataset set, one species per dataset)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Aggregation unit tests: get_float contract (incl. non-finite pass-through pinned for the 02-03 WR-03 lock), calculate_dataset_stats tie/boundary/constant/empty, to_singular_species, aggregate_models over the fixtures (beta 5 / alpha 3 / gamma 0, ranks 1/2/3, gamma samples == 2), thread-pin assertion"
    requirement: TEST-01
    verification:
      - kind: unit
        ref: "tests/test_aggregation.py (30 collected items, all passing)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Pivot integration test under monkeypatch.chdir: three output files, verbatim info mirroring, all-three-aliases presence incl. missing-metric gamma with f1 still '', 11/9/14 key shape, slash-sanitized filenames"
    requirement: TEST-01
    verification:
      - kind: unit
        ref: "tests/test_pivot.py (3 tests, all passing)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Golden files (chain-produced) + golden test: full synthetic chain under chdir, walk()-based value comparison with zero diffs of any class, file-set exactness (4 comparison files + tasks.json)"
    requirement: TEST-03
    verification:
      - kind: unit
        ref: "tests/test_golden.py (3 tests, all passing; from compare import walk)"
        status: pass
    human_judgment: false
  - id: D5
    description: "node:test JS suite for the index generator (displayName collapse, Unknown fallback, count/version, malformed-JSON [Skip]) + make test wiring so the JS lane always runs"
    requirement: TEST-01
    verification:
      - kind: other
        ref: "command: node --test tests/js/ -> 2 pass, 0 fail"
        status: pass
      - kind: other
        ref: "command: make test -> 132 pytest passed + node 2 pass; make test-fast -> 132 passed"
        status: pass
    human_judgment: false

# Metrics
duration: 14min
completed: 2026-10-09
status: complete
---

# Phase 2 Plan 02: CPU-Only Test Corpus Summary

**Synthetic-fixture test corpus locking the data-chain math: 30 aggregation unit tests (exact-tie rank(method='min'), missing-metric presence gating, zero-variance guards), a chdir-driven pivot test, walk()-compared chain-produced goldens, and a zero-dependency node:test lane wired into make test.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-10-09T03:48:19Z
- **Completed:** 2026-10-09T04:01:58Z
- **Tasks:** 3
- **Files modified:** 13 (12 created, 1 modified)

## Accomplishments

- Synthetic fixture tree (3 models × 3 datasets) in the exact committed 11/8/9/14-key shape, all three schema-valid against `schemas/model_performance.json`: exact-tie pair alpha=beta=0.9 vs gamma=0.8 (f1, Animals/binary), fake-gamma f1="" missing-metric case (Plants/multiclass), spearmanr regression path (Microbe) exercising `metric_key_map`, one dataset per species so each species-comparison golden gets exactly one row source
- `tests/test_aggregation.py` (30 items): `get_float` coercion contract including the non-finite pass-through pinned as plain assertions (the fact 02-03's WR-03 `xfail(strict=True)` lock builds on); `calculate_dataset_stats` exact-tie (ranks 1/1/3, scores 2/2/0, minmax 1/1/0), one-step-off-the-tie boundary probe (distinct 1/2/3), constant-score zero-variance guards, empty-dict; `to_singular_species` mapping rows + passthrough; `aggregate_models` hand-computed totals (beta 2+1+2=5, alpha 2+0+1=3, gamma 0, final ranks 1/2/3, gamma samples==2) plus Top-K counts and PFLOPs conversion; thread-pin assertion proving OMP/OPENBLAS/MKL_NUM_THREADS=='1' at test time
- `tests/test_pivot.py`: `get_task_performance.main()` under `monkeypatch.chdir` — three output files with verbatim info mirroring, ALL THREE aliases pivoted on the missing-metric dataset (gamma present with f1 still ""), 11/9/14 per-model key shape, `/` and `\` filename sanitization
- `tests/fixtures/golden/` (4 models_comparison* + tasks.json) byte-copied from an identical scratch chain run — chain-produced, never hand-authored — and `tests/test_golden.py` proving zero-diff regeneration via `from compare import walk` (canonical D-06 vocabulary reused, FLOAT_ULP included on the same machine), with file-set exactness asserted
- `tests/js/generate-tasks-index.test.js`: node:test (Node builtins only, zero npm) via the copy-into-fixture-tree mechanism — displayName underscore-run collapse ("Fake one"), defensive Unknown fallback, count/version, malformed-JSON [Skip] path with the valid file still indexed; IN-02 (missing-dir crash) deliberately not covered (milestone backlog per D-05)
- Makefile `test` target now runs `pytest` + `node --test tests/js/`; `test-fast` stays pytest-only-minus-slow; `make test` = 132 pytest + 2 node green, `make lint` green

## Task Commits

Each task was committed atomically:

1. **Task 1: Synthetic fixture tree engineered for the edge cases** - `2d9e792` (feat)
2. **Task 2: Aggregation + pivot unit tests with tie/boundary/constant/empty edges** - `2285dd3` (test)
3. **Task 3: Golden files + node:test JS suite + make test completion** - `ba2348f` (test)

**Plan metadata:** (final docs commit below)

## Files Created/Modified

- `tests/fixtures/synthetic_models/fake-{alpha,beta,gamma}_performance.json` - engineered fixtures (tie pair, missing metric, regression metric, per-species coverage)
- `tests/fixtures/golden/models_comparison{,_animal,_plant,_microbe}.json` + `tasks.json` - chain-produced expected outputs (value-compared)
- `tests/test_aggregation.py` - pure-function unit tests + thread-pin assertion (TEST-01/TEST-02)
- `tests/test_pivot.py` - chdir-driven pivot integration test (TEST-01)
- `tests/test_golden.py` - walk()-based golden comparison over the full synthetic chain (TEST-03 synthetic half)
- `tests/js/generate-tasks-index.test.js` - node:test unit lane for the JS index generator (TEST-01 JS scope)
- `Makefile` - test target gains `node --test tests/js/`; header documents the Python+JS lanes

## Decisions Made

- Constant-score guard test uses binary-exact **0.5** instead of the plan's 0.7 — see Deviations #1; the ranking-relevant invariant (all models normalize identically) is pinned for 0.7 without pinning the ULP-level degenerate value
- Gamma's aggregate total asserted as **0**, not the plan's "= 1" — see Deviations #2
- One golden-generation flow: the golden test itself produces tasks.json via the JS copy trick, and the committed goldens came from the identical scratch run (no second generation path to drift)
- `make test-fast` deliberately stays pytest-only (plan wording: "pytest-only-minus-slow"); the JS lane lives in `make test` so it is never silently skipped

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan's constant-score expectation is wrong by one ULP**
- **Found during:** Task 2 (constant-case test)
- **Issue:** The plan asserts `{'a': 0.7, 'b': 0.7, 'c': 0.7}` yields zscore exactly 0.0 via the `std == 0` guard — but `np.mean([0.7]*3)` rounds one ULP below 0.7, so `np.std` is one ULP above zero, the `std > 0` branch is taken, and zscore degenerates to a constant (empirically 1.0), not 0.0. `minmax` (min==max) and `robust` (iqr==0) compare exact values and do fire.
- **Fix:** The guard-branch test uses binary-exact 0.5 (3-element mean round-trips exactly → std exactly 0.0 → all three guards fire, matching the plan's intent); a companion test pins the 0.7 reality as the all-models-equal invariant (the ranking-relevant property) without pinning the ULP-level degenerate constant
- **Files modified:** tests/test_aggregation.py
- **Verification:** 30/30 aggregation items pass, including both constant-case tests
- **Committed in:** 2285dd3 (Task 2 commit)

**2. [Rule 1 - Bug] Plan's aggregate arithmetic slip for gamma's total**
- **Found during:** Task 2 (aggregate_models expectations)
- **Issue:** The plan's action text computes "gamma = 0 + (excluded) + 1 = 1", but gamma is rank 3 of 3 on FakeDS__regress_task (spearman 0.4 < alpha 0.5 < beta 0.6), so its regress contribution is 0 and the correct total is 0. The plan's final-rank claim (1/2/3 beta/alpha/gamma) is unaffected either way.
- **Fix:** Asserted the first-principles computed value (gamma rank_score == 0); the docstring carries the correct per-dataset breakdown so the expectation table is self-verifying
- **Files modified:** tests/test_aggregation.py
- **Verification:** `test_aggregate_totals_and_final_rank_over_synthetic_tree` passes against the golden chain output (beta 5 / alpha 3 / gamma 0 confirmed in the committed goldens)
- **Committed in:** 2285dd3 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 plan-expectation bugs — both plan-text arithmetic/float errors corrected to computed semantics; no production code touched)
**Impact on plan:** None on scope or truths — the must_haves tie/presence/get_float truths are asserted exactly as written; only the two faulty derived numbers in the action prose were corrected.

## Issues Encountered

- Ruff (I001 import sorting, PERF102 `.values()`) flagged the new modules during authoring; fixed with `ruff --fix` plus one hand edit — `make lint` green. Routine hygiene, no semantic change.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for plan 02-03 (determinism + known-defect locks): the `slow` marker is registered, `compare`/`get_float` imports are proven through the conftest roots, and the get_float non-finite pass-through pin this plan landed is exactly the fact the WR-03 `xfail(strict=True)` lock asserts against
- Phase 5 CI can reuse `make test` verbatim (pytest + node lanes) and the `node --test tests/js/` invocation as-is; the golden test's FLOAT_ULP-included zero-diff assertion documents the same-machine distinction CI's drift job must preserve
- Zero production-file changes (D-04) — verified: `git diff ff37f5f..HEAD -- script/ scripts/ baseline/ pipeline/ dnallm-mark/` is empty

## Self-Check: PASSED

- All 13 plan files exist on disk (3 fixtures, 5 goldens, 3 Python test modules, 1 JS test module, Makefile)
- All 3 task commits (2d9e792, 2285dd3, ba2348f) verified as ancestors of HEAD
- Measured commits from ledger: 3 (`git rev-list --count ff37f5f..HEAD`)
- Plan verification re-run green: 36 passed across the three modules, node 2 pass, make test-fast 132 passed

---
*Phase: 02-data-contracts-test-harness*
*Completed: 2026-10-09*
