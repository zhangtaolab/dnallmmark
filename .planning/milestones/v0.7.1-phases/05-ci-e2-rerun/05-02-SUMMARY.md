---
phase: 05-ci-e2-rerun
plan: 02
subsystem: data-chain
tags: [f6-aggregation, tie-rule, weighted-view, permutation-tests, schema-migration, changelog, manifest, view-toggle, stamped-footer]

# Dependency graph
requires:
  - phase: 05-ci-e2-rerun (05-01)
  provides: green drift gate (make data byte-identical no-op) so the F6 data movement is attributable from its first commit; ci marker lane; 236-test green suite
provides:
  - F6 statistics core — CI-overlap tie rule (optional ci_map on calculate_dataset_stats), weighted_score in aggregate_models, script/permutation_tests.py (10k shuffles, rng=42, BH, deterministic artifact)
  - THE migration commit 3c40de3 — schema 16-key block + two new strict schemas, 4 regenerated comparisons + permutation_tests.json (exactly 861 pairs) + manifest.json (data_version 1.1.0), re-chained goldens, baseline/f6-migration-inventory.json, CHANGELOG.md, Makefile wiring
  - script/run_migration_inventory.py — tree-level inventory orchestrator + --write-manifest sha256 mode (the data-v2 gate reuses it)
  - weighted-default dual-view frontend + stamped footer (live clock gone)
affects: [05-ci-e2-rerun (05-04 data-v2 gate reuses the inventory/manifest tooling; E2' tie rule activates on 3-seed data), public leaderboard numbers view]

# Actuals (#2632) — measured from the plan ledger (base 8f5d015)
actuals:
  tokens: 99292    # chars/4 over the realized diff (397170 chars incl. the committed 861-pair artifact) — plan estimate 65000
  tasks: 3         # Task 1 (TDD RED+GREEN) + Task 2 (THE migration commit) + Task 3 (frontend)
  commits: 4       # MEASURED: git rev-list --count 8f5d015..HEAD (c4b9821, 73006a0, 3c40de3, f1b9d28)
plan_head_before: 8f5d0159a61359ee726f34f773c494a216d6ca22
plan_head_after: f1b9d28339ea9ba5c60b52b8124f3860728a5f2e

# Tech tracking
tech-stack:
  added: []        # scipy 1.18.1 already pinned in [data] per D-15; zero installs
  patterns:
    - "Vendored-statistics consumption: intervals for the tie rule are produced by aggregate_seeds and CONSUMED by calculate_dataset_stats — one statistical vocabulary, never re-implemented"
    - "Migration inventory BEFORE tree movement: the committed side of the comparison must still hold pre-migration content when the orchestrator runs"
    - "Version constants in the Configuration block (DATA_VERSION/GENERATED_FROM/DATE) — never a live clock or live git call in the data path"

key-files:
  created:
    - script/permutation_tests.py
    - script/run_migration_inventory.py
    - schemas/permutation_tests.json
    - schemas/data_manifest.json
    - tests/test_permutation.py
    - tests/test_migration_inventory.py
    - tests/js/main-view-toggle.test.js
    - dnallm-mark/data/permutation_tests.json   # 861 pairs, 657 significant at BH FDR 0.05
    - dnallm-mark/data/manifest.json            # data_version 1.1.0
    - baseline/f6-migration-inventory.json
    - CHANGELOG.md
  modified:
    - script/summarize_comparison.py            # tie rule + weighted + manifest + load_model_inputs extraction
    - schemas/models_comparison.json            # 16-key performance block
    - tests/test_aggregation.py                 # +6 F6 tests
    - tests/test_schemas.py                     # +2 buckets
    - tests/fixtures/golden/                    # 4 comparison goldens re-chained (tasks.json golden byte-unchanged)
    - dnallm-mark/data/models_comparison{,_animal,_plant,_microbe}.json
    - Makefile                                  # data target += permutation line; lint scope += 2 scripts
    - dnallm-mark/js/main.js                    # view toggle, weighted default, stamped footer
    - dnallm-mark/js/config.js                  # VIEW_OPTIONS + viewYAxis
    - dnallm-mark/js/data.js                    # loadDataManifest()

key-decisions:
  - "permutation_type='samples' (the must_haves literal) is scipy's PAIRED permutation test — observations paired by task, null flips per-task difference signs; kept per three binding plan statements; tests pin exact hand-computed p-values (0.25/0.25/1.0 at 3 tasks, BH 0.375/0.375/1.0); significance resolution comes from the real 47-task vectors (2^47 configs under 10k resamples)"
  - "scipy vectorized statistic needs axis=-1: permutation_test defaults axis=0 but vectorized batches PREPEND a batch dimension — caught by the test's significance-direction assertion"
  - "load_model_inputs extracted verbatim from summarize main() as the single extraction reader shared with the permutation engine (one reader, never a duplicated loop); drift gate proves byte-identity"
  - "aggregate_models keeps the include_weighted gate (default False) with main() passing True — zero test churn, plan file list held exactly"
  - "The migration inventory ran BEFORE make data moved the tree (committed side = pre-migration content); inventory: 4 changed / 2 new / 1 identical, 168 EXTRA_IN_REGEN = 42 models x 4 files weighted_score keys, ZERO existing values moved"

patterns-established:
  - "Migration-inventory gate shape: scratch-chain regen -> compare.py walk over the derived surface -> per-category attribution -> CHANGELOG + committed artifact (data-v2 reuses verbatim)"

requirements-completed: [REV-04, DATA-01, DATA-02, DATA-06]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "CI-overlap tie rule: closed-interval overlap graph, connected components share component min rank, touch-point ties, None/partial ci_map byte-identical to exact-tie output; CpG replica (0.0021039 span) ties via vendored aggregate_seeds n=3 t-intervals (method 't', never bootstrap)"
    requirement: REV-04
    verification:
      - kind: unit
        ref: "uv run --group dev pytest tests/test_aggregation.py — 6 new F6 tests pass inside the 36-test module"
        status: pass
      - kind: unit
        ref: "tests/test_vendored_stats.py — 13 pass (the interval producer's parity pins)"
        status: pass
    human_judgment: false
  - id: D2
    description: "weighted_score dual view: sum_zscore / len(target_datasets) (uniform 1/N difficulty, F6 Q2), no imputation; emitted in the 4 comparisons; schema extended to the 16-key closed block in the SAME commit"
    requirement: REV-04
    verification:
      - kind: unit
        ref: "tests/test_aggregation.py::test_weighted_score_is_uniform_difficulty_normalized_zscore_sum"
        status: pass
      - kind: integration
        ref: "Task 2 verify: all('weighted_score' in v['performance']) over all 4 committed comparisons; test_schemas models_comparison bucket green"
        status: pass
    human_judgment: false
  - id: D3
    description: "Permutation family: exactly 861 pairs (C(42,2)), 10,000 shuffles, rng=42, BH at FDR 0.05, family/coverage/seed disclosed in info; deterministic artifact; zero/single-common-task pairs excluded and disclosed"
    requirement: REV-04
    verification:
      - kind: unit
        ref: "tests/test_permutation.py — hand-computed BH step-up + exact paired-test p-values + byte-determinism + exclusions (10 tests)"
        status: pass
      - kind: integration
        ref: "len(p['pairs'])==861 asserted over the committed artifact (Task 2 verify); double make data byte-stable"
        status: pass
    human_judgment: false
  - id: D4
    description: "THE migration commit: schema + emission + regenerated data + re-chained goldens + inventory + CHANGELOG + Makefile in exactly ONE commit (four-hash check)"
    requirement: DATA-01
    verification:
      - kind: other
        ref: "git log -1 --format=%H over data/code/schema/CHANGELOG paths — all 3c40de30b1f94218f4c9af5bea3546a4f1c2f9f6"
        status: pass
      - kind: other
        ref: "baseline/f6-migration-inventory.json: 168 EXTRA_IN_REGEN (42x4 weighted_score), 2 new files, tasks.json identical, 0 unattributable categories"
        status: pass
    human_judgment: false
  - id: D5
    description: "CHANGELOG.md per-version registry + manifest.json data_version 1.1.0 / generated_from pre-migration HEAD / date constants (no live clock, no live git in the data path; no intermediate tag per D-17/OQ3)"
    requirement: DATA-02
    verification:
      - kind: integration
        ref: "Task 2 verify python: manifest keys + stamps asserted; schemas/data_manifest.json validates the artifact; make data twice byte-stable"
        status: pass
    human_judgment: false
  - id: D6
    description: "Frontend: weighted default view, one-click raw-rank switch (sort field, scatter y accessor + axis title, metric column all view-derived), weighted value only READ from performance.weighted_score; footer stamped from manifest.json with hide-on-failure null-guard (live clock removed)"
    requirement: DATA-06
    verification:
      - kind: unit
        ref: "node --test tests/js/ — 15/15 incl. 7 new main-view-toggle tests"
        status: pass
      - kind: other
        ref: "grep -c toLocaleDateString dnallm-mark/js/main.js == 0; eslint + node --check clean; make data drift gate empty (number-neutral)"
        status: pass
      - kind: manual
        ref: "localhost visual confirmation (weighted default, toggle behavior, stamped footer) — DEFERRED to the phase-level UAT gate"
        status: deferred
    human_judgment: true
    rationale: "The visual localhost check is delegated to the phase UAT gate per the execution instruction; its behavioral seams are pinned by the node:test lane"

# Metrics
duration: 39 min
completed: 2026-10-10T10:49:47Z
status: complete
---

# Phase 5 Plan 2: F6 Aggregation Upgrade — ONE Migration Commit + Weighted-Default Frontend Summary

**CI-overlap tie rule on vendored statistics, z-score x uniform-difficulty weighted dual view, 861-pair BH permutation artifact, manifest/CHANGELOG stamping, and the weighted-default leaderboard — landed as one atomic, inventoried, drift-green migration commit with zero existing numbers moved**

## Performance

- **Duration:** 39 min (2026-10-10T10:10:22Z -> 10:49:47Z)
- **Tasks:** 3/3 (Task 1 TDD RED+GREEN; Task 2 THE migration commit; Task 3 frontend)
- **Files:** 27 changed (12 created, 15 modified)

## Task Commits (TDD: RED -> GREEN; migration: ONE atomic commit)

1. **Task 1 RED** — `c4b9821` (test): 10 failing tests (tie rule x5, weighted, permutation x4) + NotImplementedError skeleton; classifier verdict RED_EVIDENCE_OK (target test executed and failed on the missing kwarg)
2. **Task 1 GREEN** — `73006a0` (feat): tie rule + weighted + permutation engine, all unwired (drift gate proven no-op)
3. **Task 2 THE migration commit** — `3c40de3` (feat): 20 files — emission wiring + manifest constants, 3 schemas, regenerated 4 comparisons + 2 new artifacts, re-chained goldens, inventory, CHANGELOG, Makefile. Four-hash check: data/code/schema/CHANGELOG all last-touched by exactly this commit
4. **Task 3** — `f1b9d28` (feat): weighted-default dual view + stamped footer + 7 node tests

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] scipy vectorized statistic computed means over the wrong axis**
- **Found during:** Task 1 GREEN (the significance-direction test assertion failed)
- **Issue:** `permutation_test` defaults `axis=0`, but under `vectorized=True` the batch dimension is PREPENDED — the observation axis for 1-D samples is the last one; the statistic silently averaged the batch dimension instead.
- **Fix:** explicit `axis=-1` in the call (and the statistic honors the axis scipy passes).
- **Files modified:** script/permutation_tests.py
- **Verification:** all permutation tests pass; real-run artifact produced (would have published garbage p-values at Monte-Carlo scale).
- **Committed in:** 73006a0

**2. [Rule 2 - Missing critical] degenerate pairs (single common task) crashed the engine**
- **Found during:** Task 1 GREEN (ValueError: "each sample must contain two or more observations")
- **Issue:** scipy requires >= 2 observations per sample — a pair sharing exactly one task cannot be permuted (the statistic is fixed); the plan only specified zero-common-task exclusion.
- **Fix:** pairs with < 2 common tasks are excluded and disclosed (`reason: "single common task"` vs `"zero common tasks"`); coverage_rule text discloses both. Zero occurrences in the real 42-model data (0 excluded, 861/861 tested).
- **Files modified:** script/permutation_tests.py, tests/test_permutation.py
- **Committed in:** 73006a0

**3. [Rule 3 - Blocking] `from compare import walk` failed outside the pytest harness**
- **Found during:** Task 2 (first inventory run died with ModuleNotFoundError)
- **Issue:** baseline/compare.py is only importable because conftest puts `baseline/` on sys.path; run_migration_inventory.py runs as a CLI where that contract does not exist.
- **Fix:** explicit importlib file-path module load (no sys.path mutation, no E402) — the comparator itself remains untouched per D-17/OQ6.
- **Files modified:** script/run_migration_inventory.py
- **Verification:** inventory ran end-to-end (16s) and produced the committed artifact.
- **Committed in:** 3c40de3

**Total deviations:** 3 auto-fixed (1 bug, 1 missing-edge, 1 blocker). **Impact:** all three were required for correct, non-crashing behavior; no scope creep.

### Documented Interpretations (not deviations)

- **`permutation_type="samples"` semantics:** the must_haves literal is scipy's PAIRED permutation test (observations paired by task; null flips per-task difference signs) — kept per three binding plan statements (must_haves truth, action text, verified-signature example). The synthetic test pins exact hand-computable values (p = 0.25 at the 2/2^3 exact floor, BH 0.375) instead of a significance flag that is unreachable at 3 tasks; the production artifact's 47-task vectors have full resolution (657/861 significant).
- **Inventory execution order:** the plan numbers regeneration (step 4) before the inventory (step 6); operationally the inventory ran BEFORE `make data` moved the tree, so its committed side holds the pre-migration content (the disk-based comparator would otherwise diff new-vs-new). "Before committing" (the plan's own words) is what was honored.
- **Extraction refactor:** the ~100-line extraction loop moved verbatim from `main()` into `load_model_inputs()` so the permutation engine reuses the single reader (never a duplicated loop) — byte-identity proven by the drift gate, goldens, and determinism lane.

## Issues Encountered

None beyond the deviations above.

## Deferred to Phase UAT

- **Task 3 `<human-check>` (visual localhost confirmation):** run `bash start-server.sh` and open http://localhost:8080 — confirm the leaderboard opens on the Weighted view, the Raw Rank toggle re-sorts the table and re-labels the scatter y-axis in one click, and the footer shows the stamped date + data v1.1.0 (no today's-date behavior). Deferred to the phase-level UAT gate per the execution instruction; also recorded in the WINDOWS ledger (unrun-verify) so the ship gate sees it. Behavioral seams are pinned by tests/js/main-view-toggle.test.js (15/15 node lane).

## Known Stubs

None — no stub patterns exist in any file created or modified by this plan.

## Final Suite State

- `make test`: 253 passed, 0 failed (+ node lane 15/15) — up from 236 + 8 at plan start
- `make ci`: 69 passed (6 new ci-marked aggregation tests joined the pinned lane)
- `make lint` / `make typecheck`: clean (both new scripts in lint scope; ty over script/ include)
- Drift gate: `make data && git status --porcelain -- dnallm-mark/data/` empty — byte-identical no-op incl. manifest.json and permutation_tests.json
- 861-pair count asserted over the committed artifact; 657 significant at BH FDR 0.05; 0 pairs excluded
- No git tag created (data-v2 tag is the maintainer gate per D-17/OQ3)

## Next Phase Readiness

- 05-03 (N-frequency audit) proceeds independently.
- 05-04's data-v2 gate tooling reuses `run_migration_inventory.py --write-manifest` verbatim; the E2' chain activates the tie rule when seed data exists (aggregate_seeds intervals -> ci_map).

## Self-Check: PASSED

All 12 key files exist on disk; all four task commits (c4b9821, 73006a0, 3c40de3, f1b9d28) are ancestors of HEAD f1b9d28c98f17fdea3dbe145df5830522d085745.

---
*Phase: 05-ci-e2-rerun*
*Completed: 2026-10-10*
