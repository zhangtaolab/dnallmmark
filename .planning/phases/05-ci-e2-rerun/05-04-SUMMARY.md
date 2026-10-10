---
phase: 05-ci-e2-rerun
plan: 04
subsystem: data-chain
tags: [e2e-readiness, sweep-priority, alias-normalization, env-smoke-gate, dual-gate, degradation-order, fake-executor, determinism]

# Dependency graph
requires:
  - phase: 05-ci-e2-rerun (05-01..05-03)
    provides: the CI lanes (make lint/typecheck/test/data) the new artifacts must keep green; eval_subsets.json the launch consumes; the drift gate the D-18 regeneration must satisfy
provides:
  - script/export_runs.py --model-output-dir — the D-16 per-model view emitted alongside the task view by ONE emitter (one reader per view; summarize's reader untouched)
  - The full D-16 chain proven on fixtures: export -> BOTH views -> summarize over the emitted per-model dir -> schema-valid, byte-stable comparison (tests/test_ci_replay.py)
  - D-18 alias normalization — dnallm-mark/data/model_performance/PlantDNAMamba2-BPE_performance.json under the unified-registry key, with baseline/d18-alias-inventory.json attributing every migration diff, CHANGELOG entry, GENERATED_FROM restamped (a full rehearsal of the data-v2 gate mechanics on a real migration)
  - pipeline/run_sweep.py --priority-file (tier ranks composed as the PRIMARY sort key over the sorted() fallback, fail-fast validated) + --from-failures (re-enumerate exactly the failed pairs, clean manifest = explicit zero-cell run)
  - pipeline/sweep_priorities.json — tier 1 = the PIPE-03 E2E pair, tier 2 = the maintainer-curated arena representatives (Task 4 gate resolved 2026-10-10)
  - pipeline/env_smoke.py — the PIPE-02 dual-gate half (PASS/FAIL lines, non-zero exit; version pins parsed from pyproject.toml, numpy>=2 gate + datasets/pyarrow diagnostic); written, linted, type-checked, NEVER agent-executed (py_compile only)
  - The fake-executor degradation-order proof: tier-1 E2E pair -> every cell of the three tier-2 representatives -> sorted() fallback
affects: [E2' launch (maintainer dual-gate), Phase 6 recompute lanes, public leaderboard data-v2]

# Actuals (#2632) — measured from the plan ledger (base 2b66fc9)
actuals:
  tokens: 56819    # chars/4 over the realized diff (227275 chars; ~149k of it is the D-18-regenerated comparison/permutation data files) — plan estimate 60000
  tasks: 4
  commits: 7       # MEASURED: git rev-list --count 2b66fc9..HEAD (9918046, dfb9a80, b2bb6ff, a864a95, 6a0d481, 12c2d3e, 6598e45)
plan_head_before: 2b66fc90b8571e37ff7c5b36f2ff9dfcf5c783b7
plan_head_after: 6598e4595c2682dce9aea2a733b768437f014101

# Tech tracking
tech-stack:
  added: []        # stdlib-only sweep driver extensions; zero installs this plan
  patterns:
    - "Rank composition over a stable fallback: (tier index, entry specificity) as the PRIMARY sort key with sorted() as the tiebreak — a {model, task} spec outranks a bare name within its tier; unmatched cells keep today's byte-identical order (determinism preserved when the file is absent)"
    - "One emitter, one reader per view: export_runs emits task-centric + per-model views in one pass; summarize_comparison's existing model_performance reader is NOT modified (D-16 Option C)"
    - "Committed-instance tests: the priorities file's own content is pinned by tests (tier 1 exact pair, tier 2 exact three names) so any edit that breaks the maintainer's curation fails CI, and its names are cross-checked against the real registry keys"

key-files:
  created:
    - pipeline/sweep_priorities.json
    - pipeline/env_smoke.py
    - baseline/d18-alias-inventory.json
    - dnallm-mark/data/model_performance/PlantDNAMamba2-BPE_performance.json
  modified:
    - script/export_runs.py
    - script/summarize_comparison.py
    - pipeline/run_sweep.py
    - tests/test_export_runs.py
    - tests/test_ci_replay.py
    - tests/test_sweep.py
    - Makefile
    - CHANGELOG.md
    - dnallm-mark/data/models_comparison.json
    - dnallm-mark/data/models_comparison_animal.json
    - dnallm-mark/data/models_comparison_plant.json
    - dnallm-mark/data/models_comparison_microbe.json
    - dnallm-mark/data/permutation_tests.json
    - dnallm-mark/data/manifest.json

key-decisions:
  - "Task 4 gate resolution (verbatim disposition): presented options were per-arena one representative / per-arena top-2 (5 models) / leave-empty; maintainer selected \"每 arena 一代表 (Recommended)\" — tier 2 = one representative per arena: animal GENERanno-eukaryote-0.5b-base, plant PlantCAD2-Small-l24-d0768, microbe Omni-DNA-700M (basis: committed weighted_score arena leaders excluding the tier-1 pair; animal 0.799 / plant 1.000 / microbe 1.056)"
  - "Tier-2 entries are BARE model names — each covers all that model's cells across tasks x seeds; entry order in the file records the maintainer's declaration order (animal/plant/microbe) but all bare names in one tier share a rank, so execution order within the tier is the sorted() fallback"
  - "All three tier-2 names registry-validated against pipeline/models_info.json keys BEFORE writing (exact-key matches), and pinned by test_tier2_representatives_are_real_registry_keys against future registry drift"
  - "The per-model emitter's default output dir is OUTSIDE dnallm-mark/data (sibling of the input root) — committed data is never silently overwritten before the maintainer gate"
  - "D-18 restamps GENERATED_FROM to the pre-rename HEAD (9918046) per the 05-02 convention; DATA_VERSION stays 1.1.0 (alias identity is not a data-version change)"
  - "env_smoke version pins are parsed from pyproject.toml ([gpu] group), never duplicated; numpy>=2 gate + datasets/pyarrow diagnostic added per the 2026-10-10 maintainer directive (dnallm 0.8.0)"

patterns-established:
  - "Gate-disposition recording: a resolved blocking-human checkpoint's verbatim selection (options presented + chosen option + curation basis) lands in the commit message, SUMMARY, and STATE decision log — the curation is maintainer property, the repo records its provenance"

requirements-completed: [REV-09, DATA-01, DATA-03]

# Coverage metadata — the plan's 7 must_haves truths -> evidence
coverage:
  - id: D1
    description: "E2' data chain closed end-to-end on fixtures: export_runs emits BOTH views from run records (task-centric + per-model per D-16 Option C); CI replay covers export -> both views -> aggregate -> schema (D-17/OQ7)"
    requirement: REV-09
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py (per-model schema validation, zero-record models emit no file, cross-view metric parity, byte-stability) + tests/test_ci_replay.py (full D-16 chain: export -> both views -> summarize over emitted per-model dir -> schema-valid comparison, byte-stable)"
        status: pass
      - kind: integration
        ref: "make test 307 passed; drift gate no-op"
        status: pass
    human_judgment: false
  - id: D2
    description: "One key per model everywhere: the committed results alias aligns to the unified registry key (D-18 — plant-dnamamba2-BPE -> PlantDNAMamba2-BPE in a dedicated, inventoried commit)"
    requirement: DATA-01
    verification:
      - kind: integration
        ref: "exactly one mamba2 results file under the registry-key name (git ls-files, icase-equivalent of the plan's verify glob); baseline/d18-alias-inventory.json attributes every one of the 2029 diffs; make data drift = no-op post-rename; CHANGELOG D-18 entry"
        status: pass
    human_judgment: false
  - id: D3
    description: "run_sweep executes cells in maintainer-declared priority order (tier 1 = the PIPE-03 E2E pair all-seeds; tier 2 = the three arena representatives) and re-runs exactly the failed cells from sweep_failures.json — all proven with fake executors + --dry-run, no GPU run ever executed"
    requirement: REV-09
    verification:
      - kind: unit
        ref: "tests/test_sweep.py (45 tests): frozen default order, tier-rank composition, seeds-adjacent, committed-file content pinned, degradation-order fake-executor test (tier 1 -> all tier-2 cells -> sorted fallback), --from-failures exact-pairs + clean-manifest zero-cell + fail-fast validation"
        status: pass
      - kind: integration
        ref: "real-registry --dry-run with the committed priorities file over 6 models x 2 tasks x 1 seed: tier-1 pair first, three representatives next, sorted fallback last"
        status: pass
    human_judgment: false
  - id: D4
    description: "The PIPE-02 env-smoke gate exists as a checkable exit-code script (version pins from pyproject, dnallm import, CUDA, all 50 dataset dirs, small-tensor matmul) — written, linted, type-checked, NEVER executed by any agent"
    requirement: REV-09
    verification:
      - kind: integration
        ref: "python3 -m py_compile pipeline/env_smoke.py (compile only); make lint + make typecheck green with the file in scope; no test imports or executes it"
        status: pass
    human_judgment: false
  - id: D5
    description: "E2' launch stays behind the dual gate + explicit maintainer authorization: nothing in this plan starts a sweep; tier 2 was maintainer-curated at the blocking-human checkpoint (never agent-invented)"
    requirement: REV-09
    verification:
      - kind: manual_procedural
        ref: "Task 4 gate resolution recorded verbatim (commit 6598e45 message + this SUMMARY + STATE decision log); only --dry-run forms executed anywhere in the plan's history"
        status: pass
    human_judgment: true
    rationale: "the gate's resolution IS the human judgment — the maintainer selected the tier-2 curation from the presented options; the executor's role was to record and implement it verbatim"
  - id: D6
    description: "Partial E2' completion is honest by construction: the exporter discloses n_seeds per metric and the vendored statistics never emit a vacuous CI below three seeds (n=3 -> t-interval df=2)"
    requirement: DATA-01
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py (n_seeds disclosure per metric in the per-model emission) over the 05-02-vendored statistics (already pinned: no CI below 3 seeds, t-interval df=2)"
        status: pass
    human_judgment: false
  - id: D7
    description: "The data-v2 gate is fully prepared but never executed automatically: the inventory orchestrator + SHA256-manifest convention cover the post-E2' migration; the data-v2 tag is created only by the maintainer after sign-off"
    requirement: DATA-03
    verification:
      - kind: integration
        ref: "baseline/d18-alias-inventory.json is a real-migration rehearsal of script/run_migration_inventory.py (the 05-02 gate tooling); only tag data-v1 exists (git tag); no agent created/moved/pushed any tag"
        status: pass
    human_judgment: false

# Metrics
duration: 55 min
completed: 2026-10-10
status: complete
---

# Phase 05 Plan 04: E2' Readiness (D-16 Bridge + D-18 Alias + Sweep Priority + env_smoke) Summary

**The code-only half of REV-09 landed: the E2' data chain is closed and replay-proven on fixtures, the alias/registry set-diff is closed with a full migration-gate rehearsal, the sweep driver is priority-ordered (tier 1 = the E2E pair, tier 2 = the maintainer-curated arena representatives) and failure-recoverable, and the env-smoke half of the dual gate exists — launch day runs only code CI has already exercised**

## Gate Resolution (Task 4, blocking-human — RESOLVED 2026-10-10)

Presented options: per-arena one representative / per-arena top-2 (5 models) / leave-empty.

**Maintainer selected: "每 arena 一代表 (Recommended)"** — tier 2 = one representative per arena:
- animal: `GENERanno-eukaryote-0.5b-base`
- plant: `PlantCAD2-Small-l24-d0768`
- microbe: `Omni-DNA-700M`

Basis: committed weighted_score arena leaders excluding the tier-1 pair; animal 0.799 / plant 1.000 / microbe 1.056.

Implemented verbatim (commit `6598e45`): the three names written into tier 2 of pipeline/sweep_priorities.json as BARE model names (each covers all that model's cells across tasks x seeds), registry-validated against pipeline/models_info.json keys before writing, pinned by a real-registry cross-check test, and proven by a fake-executor degradation-order test (tier-1 E2E pair cells first, then ALL cells of the three tier-2 models with seeds adjacent, then the remaining cells in the sorted() fallback order).

## Performance

- **Duration:** 55 min (two executor sessions: Tasks 1-3 by the prior executor, Task 4 + close-out by the continuation executor after the maintainer resolved the gate)
- **Completed:** 2026-10-10T12:35:00Z
- **Tasks:** 4 (3 auto + 1 blocking-human checkpoint)
- **Files modified:** 18 (11 code/test/docs + 7 regenerated/renamed data files)

## Task Commits

Each task was committed atomically:

1. **Task 1: D-16 bridge + D-18 alias normalization** — bridge code `9918046`, alias migration `dfb9a80` (two dedicated commits per the plan)
2. **Task 2: Sweep priority ordering + failures re-run (TDD)** — RED `b2bb6ff` (19 failures; evidence `.planning/tmp/tdd-red-05-04-task2.json`), GREEN `a864a95`
3. **Task 3: PIPE-02 env-smoke gate script** — `6a0d481`, plus maintainer-directed extension `12c2d3e` (numpy>=2 gate + datasets/pyarrow diagnostic)
4. **Task 4: Tier-2 arena representatives (gate resolution)** — `6598e45`

**Plan metadata:** (docs commit follows this SUMMARY)

## TDD Record (Task 2, tdd="true")

- **RED** (`b2bb6ff`): 19 failing tests over the planned surface (--priority-file ordering, --from-failures re-run, all fail-fast validation classes). Evidence: `.planning/tmp/tdd-red-05-04-task2.json` (command, exit 1, junit + output artifacts). Note (prior executor, deviation 6): 4 of 24 RED-phase tests were vacuously green via argparse exit — meaningful post-GREEN.
- **GREEN** (`a864a95`): `load_priority_tiers` + `apply_priority_order` + `load_failure_pairs` + the two flags + fail-fast wiring; pipeline/sweep_priorities.json shipped (tier 1 committed, tier 2 empty pending the gate). All tests green.
- **REFACTOR:** none needed.

## Accomplishments

- **D-16 (OQ7):** export_runs emits BOTH views in one pass — the per-model view validates against schemas/model_performance.json, defaults OUTSIDE dnallm-mark/data, and the CI replay proves records -> task view + per-model view -> summarize -> schema-valid byte-stable comparison
- **D-18:** exactly one results file per model under the registry key; the 2029 regeneration diffs fully attributed (alias-key MISSING/EXTRA pairs, ULP-scale score shifts, permutation identity/positional churn — zero p-value movement on unchanged-identity pairs); CHANGELOG + inventory + GENERATED_FROM restamp
- **REV-09 sweep surface:** tier-rank ordering composed over the frozen sorted() fallback, --from-failures exact re-enumeration with explicit zero-cell clean-manifest behavior, collect-all-problems fail-fast on every operator JSON
- **Tier 2 curated (this session):** the three maintainer-chosen arena representatives committed, registry-pinned, and proven through a fake-executor degradation-order test + a real-registry --dry-run
- **PIPE-02:** env_smoke.py with 5 checkable PASS/FAIL surfaces (pins parsed from pyproject, dnallm import, CUDA, 50 dataset dirs with the 7-GUE warning list, matmul) + the numpy>=2/datasets diagnostic — compile-verified, never executed by any agent
- Suite at close: **307 passed** (+ node lane 15 pass), `make lint` + `make typecheck` green, drift gate no-op, only tag data-v1 exists

## Files Created/Modified

See key-files in the frontmatter. Data files are the D-18-regenerated comparisons/permutation/manifest (drift-gated no-op on re-run) and the git-mv'd results file.

## Decisions Made

See key-decisions in the frontmatter (gate disposition verbatim; bare-name tier-2 semantics; registry pre-validation; per-model emitter default outside committed data; D-18 restamp convention; env_smoke pin parsing + the numpy>=2 diagnostic).

## Deviations from Plan

Deviations 1-6 are the prior executor's, reproduced faithfully; deviation 7 is this session's record.

### Auto-fixed / documented by the prior executor

**1. [Rule 3] Plan verify glob `*mamba2*` case mismatch**
- **Found during:** Task 1 (D-18 verify)
- **Issue:** the plan's verify glob `*mamba2*` (lowercase m) cannot match the target filename `PlantDNAMamba2-BPE` (capital M)
- **Fix:** the equivalent icase-pathspec check used, intent preserved (exactly one mamba2 results file, named exactly the registry key)
- **Commit:** `dfb9a80`

**2. [Rule 3] Task shorthand is not the D-10 registry key**
- **Found during:** Task 2 (sweep_priorities.json authoring)
- **Issue:** the plan prose's `PlantCAD2__cross_species_leaf_on_off_translation` is REQUIREMENTS shorthand; the registry key is `PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation`
- **Fix:** the committed file uses the registry key (what fail-fast validation accepts)
- **Commit:** `a864a95`

**3. [Rule 3, documented] D-18 inventory: 2029 diffs attributed across two classes**
- **Found during:** Task 1 (D-18 inventory gate)
- **Issue/detail:** FLOAT_ULP 296 (max rel 5.9e-15 — the documented Phase-1 float summation-order class, the alias sorts at a different position; rank/rank_score/samples/Top-K unchanged) + permutation churn 1724 (the renamed model's 41 pairs changing identity plus positional shifts in the sorted array; 820/861 unchanged-identity pairs byte-identical p-values — zero p-value movement)
- **Resolution:** full attribution in CHANGELOG + `dfb9a80`; nothing unattributed

**4. [Rule 1] env_smoke typo'd call caught by ruff F821 at the lint gate**
- **Found during:** Task 3
- **Fix:** corrected pre-commit (the lint gate did its job)
- **Commit:** `6a0d481`

**5. [Maintainer-directed 2026-10-10] env_smoke numpy>=2 gate + datasets/pyarrow diagnostic**
- **Detail:** maintainer-directed extension beyond the plan's five checks (dnallm 0.8.0 context)
- **Commit:** `12c2d3e`

**6. [TDD note] 4 of 24 RED-phase tests vacuously green via argparse exit**
- **Detail:** argparse's SystemExit satisfied `pytest.raises(SystemExit)` before the planned behavior existed; meaningful post-GREEN
- **Commit:** `b2bb6ff` (evidence record)

### This session (continuation executor)

**7. [Rule 1] Stale docs updated alongside the gate resolution**
- **Found during:** Task 4
- **Issue:** run_sweep.py's --priority-file docstring and two test docstrings still described tier 2 as "EMPTY pending maintainer curation" after the gate resolved
- **Fix:** updated in the same commit as the curation (`6598e45`); no behavior change
- **Files:** pipeline/run_sweep.py, tests/test_sweep.py

## Auth Gates / Human Checkpoints

- **Task 4 blocking-human gate** (tier-2 curation): RESOLVED by the maintainer 2026-10-10 — selection recorded verbatim above; the continuation executor implemented exactly the three chosen models (constraint: tier 2 contains EXACTLY the three, no additions, no tier-1 reordering — held).

## Issues Encountered

- None this session; all gates green on the first post-change run (45/45 sweep tests, 307 total, lint + typecheck clean, drift no-op, real-registry dry-run ordering exact).

## Known Stubs

None. The intentional never-executed surfaces (env_smoke.py, real sweep/fine-tune) are not stubs — they are the documented maintainer-only execution forms tracked in the WINDOWS ledger (entries 10, 12).

## Threat Flags

None — no new trust surface beyond the plan's threat model. T-05-09 (operator JSON steering) mitigated by the collect-all-problems registry-join validation, exercised by the new tier-2 tests; T-05-10 (no real subprocess) held — fake executors and --dry-run only.

## User Setup Required

None — E2' launch itself is the maintainer's dual-gate action (env_smoke on GB10 + explicit go), post-phase.

## Next Phase Readiness

- Phase 5 is COMPLETE (4/4 plans). E2' launch checklist for the maintainer: run pipeline/env_smoke.py on GB10 (expect the 7-GUE-dir warning list until re-extraction), then `python pipeline/run_sweep.py --seeds 42,43,44 --priority-file pipeline/sweep_priorities.json --output-root <root>` — tier 1 (E2E pair) first, tier 2 (the three representatives) next, sorted fallback after
- Phase 6 (recompute/packaging) inherits: the per-model emitter for the post-E2' regeneration, the data-v2 gate tooling (run_migration_inventory.py + --write-manifest) rehearsed on D-18, and the REV-03 key-mapping surface already pinned by parity tests

## Self-Check: PASSED

All created files exist on disk (pipeline/sweep_priorities.json, pipeline/env_smoke.py, baseline/d18-alias-inventory.json, dnallm-mark/data/model_performance/PlantDNAMamba2-BPE_performance.json); all seven production commits (9918046, dfb9a80, b2bb6ff, a864a95, 6a0d481, 12c2d3e, 6598e45) are ancestors of HEAD; gates re-run green post-Task-4 (307 passed, lint + typecheck clean, drift no-op).
