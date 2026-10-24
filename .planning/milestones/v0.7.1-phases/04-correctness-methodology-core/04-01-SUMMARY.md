---
phase: 04-correctness-methodology-core
plan: 01
subsystem: data-chain
tags: [species-grouping, registry-join, xfail-locks, json-diff-comparator, isfinite-guard, pytest]

# Dependency graph
requires:
  - phase: 03-pipeline-adaptation-registries
    provides: unified pipeline/datasets_info.json with the 50-row Category column (D-10) and the AUD-01 xfail lock + companion pair (D-03)
provides:
  - Registry-Category arena grouping in summarize_comparison (hard-fail join, monkeypatchable REGISTRY_PATH, MAJORITY_ARENA mapping) — the SC-1/FIX-02 fix vehicle
  - Maintainer-confirmed 50-row Category review record (04-CATEGORY-REVIEW.md) — the human-verification evidence
  - Regenerated models_comparison_animal.json / models_comparison_microbe.json under the confirmed grouping, with a fully-attributed diff inventory
  - All three Phase-2 xfail locks (AUD-01, WR-02, WR-03) unmarked to permanent green contracts (D-13)
  - Comparator vocabulary INT + BOOL_CROSS labels in baseline/compare.py (IN-01/WR-02)
  - get_float isfinite guard (WR-03) — number-neutral on committed data
  - Real-tree arena-membership guard + unregistered-dataset hard-fail pin in tests/test_known_defects.py
  - Lint scope grown to script/summarize_comparison.py + baseline/compare.py (D-08 discipline)
affects: [04-02 exporter species emission, 04-05 task-file species correction, E2' regeneration gates]

# Actuals (#2632) — pairs with the plan's estimate to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 29800     # 119,148 diff chars / 4 over base 89636b7..HEAD
  tasks: 4
  commits: 3        # MEASURED: git rev-list --count 89636b7..HEAD at SUMMARY time
plan_head_before: 89636b711ca911b499462203fddd722bf094d0ac
plan_head_after: b34f43ef8484df2cd2ec7681b96933f8ba8d0625

# Tech tracking
tech-stack:
  added: []          # no new dependencies (scipy belongs to 04-02)
  patterns:
    - "Hard-fail registry join for grouping (plain dict lookup, KeyError on unregistered — never a producer-value fallback)"
    - "Monkeypatchable module-level REGISTRY_PATH constant resolved from the script file's location, not CWD"
    - "Synthetic-registry fixture injection keeps goldens byte-identical across a grouping-source switch"
    - "Same-commit fix + fixture correction + marker removal enforced by strict xfail + unmarked companion"

key-files:
  created:
    - tests/fixtures/synthetic_datasets_info.json
    - .planning/phases/04-correctness-methodology-core/04-CATEGORY-REVIEW.md
  modified:
    - script/summarize_comparison.py
    - baseline/compare.py
    - tests/test_known_defects.py
    - tests/test_aggregation.py
    - tests/test_golden.py
    - tests/fixtures/export_chain/defect_species_performance.json
    - Makefile
    - dnallm-mark/data/models_comparison_animal.json
    - dnallm-mark/data/models_comparison_microbe.json

key-decisions:
  - "Multiple->Animals majority mapping confirmed by maintainer at the blocking-human gate (verbatim response: approved, 2026-10-10); recorded in 04-CATEGORY-REVIEW.md and pinned by tests"
  - "test_real_tree_arena_membership ties the committed comparison files to the join via the per-model samples ceiling (max samples == join-derived arena size) — the strongest membership check the comparison-file schema carries"
  - "Lock docstrings' stale 'today it xfails' phrasing corrected in the Task-3 commit (docs only) so the permanent green contracts describe their history accurately"

patterns-established:
  - "Registry-join grouping with fixture-injectable path (mirrors the Phase-3 fixture-injectable discipline)"
  - "Real-data guard tests over committed data files (not only synthetic fixtures) for data-chain fixes"

requirements-completed: [FIX-02, REV-03]

coverage:
  - id: D1
    description: "FIX-02: dataset arena grouping reads the maintainer-confirmed datasets_info.json Category via a monkeypatchable REGISTRY_PATH hard-fail join (KeyError on unregistered; Multiple->majority), never the result-file species string"
    requirement: FIX-02
    verification:
      - kind: unit
        ref: "tests/test_known_defects.py#test_real_tree_arena_membership"
        status: pass
      - kind: unit
        ref: "tests/test_known_defects.py#test_unregistered_dataset_aborts_grouping"
        status: pass
      - kind: integration
        ref: "make data over the real tree; goldens via tests/test_golden.py with the synthetic registry injection"
        status: pass
    human_judgment: false
  - id: D2
    description: "Regenerated leaderboard comparison files match the previewed diff inventory exactly: total+plant byte-identical, animal/microbe 42/42 changed via the one-membership-swap, 0 added, 0 dropped, counts 22/13 preserved"
    requirement: FIX-02
    verification:
      - kind: integration
        ref: "baseline/compare.py --summary-json HEAD-vs-regen per changed file (animal 376 diffs / 42 models / +0 / -0; microbe 380 / 42 / +0 / -0)"
        status: pass
      - kind: unit
        ref: "plan verify assertion: registry-grouping membership Animals=22 incl. GUE__EPI_GM12878, Microbe=13 incl. GUE__fungi_species_20"
        status: pass
      - kind: integration
        ref: "git diff over dnallm-mark/data/ at regeneration time: exactly the 2 inventoried files"
        status: pass
    human_judgment: false
  - id: D3
    description: "Maintainer Category review evidence: 04-CATEGORY-REVIEW.md with the verbatim 'approved' disposition, the full 50-row record (45 agree / 2 conflicts / 2 Multiple-origin zero-net-change / 3 inert), and the Multiple->Animals confirmation"
    requirement: FIX-02
    verification:
      - kind: unit
        ref: "tests/test_known_defects.py#test_real_tree_arena_membership pins the confirmed mapping's grouping outcome"
        status: pass
    human_judgment: true
    rationale: "The 50-row Category review and the Multiple->Animals mapping were verified by the maintainer at the blocking-human gate (response: approved, 2026-10-10) — the committed record documents that completed human judgment; tests pin the mapping's implementation, not the biological correctness of the rows themselves."
  - id: D4
    description: "AUD-01 lock unmarked to a permanent green contract in the same commit as the fix + fixture correction; companion stays and still guards fixture shape"
    requirement: FIX-02
    verification:
      - kind: unit
        ref: "tests/test_known_defects.py#test_aud01_species_matches_dataset_arena_category (PASSED, unmarked) + #test_aud01_contract_fixture_has_expected_shape (PASSED)"
        status: pass
    human_judgment: false
  - id: D5
    description: "WR-03: get_float returns the default for nan/inf/-inf after float() coercion (math.isfinite); aggregation pins flipped same-commit; lock unmarked; number-neutral on committed data"
    verification:
      - kind: unit
        ref: "tests/test_known_defects.py#test_nonfinite_metric_excluded_from_ranking (3 params PASSED, unmarked) + tests/test_aggregation.py (30 PASSED incl. flipped isfinite pins)"
        status: pass
      - kind: integration
        ref: "make data && git status --porcelain dnallm-mark/data/ empty (CLEAN) — no committed value is non-finite"
        status: pass
    human_judgment: false
  - id: D6
    description: "IN-01 INT label + WR-02 BOOL_CROSS in baseline/compare.py walk(): int-vs-int unequal pairs carry INT; equal-value bool/int cross-type pairs report as BOOL_CROSS; WR-02 lock unmarked"
    verification:
      - kind: unit
        ref: "tests/test_known_defects.py#test_compare_reports_equal_value_bool_int_cross_type (PASSED, unmarked), #test_compare_same_type_equal_values_stay_silent, #test_compare_labels_int_vs_int_mismatch_as_int"
        status: pass
      - kind: unit
        ref: "plan crafted-pair verify: walk({'a':3,'b':True,'c':5},{'a':4,'b':1,'c':5}) yields exactly [INT /a, BOOL_CROSS /b]"
        status: pass
    human_judgment: false
  - id: D7
    description: "Lint scope widened to script/summarize_comparison.py + baseline/compare.py with all arriving findings fixed (I001, SIM101); ruff + ty zero-diagnostics"
    verification:
      - kind: unit
        ref: "make lint (All checks passed) + make typecheck (All checks passed) over the widened scope"
        status: pass
    human_judgment: false

# Metrics
duration: 17 min
completed: 2026-10-10
status: complete
---

# Phase 4 Plan 01: Species Fix Tracer Summary

**Arena grouping switched from the producer's species string to the maintainer-confirmed registry Category (hard-fail join, Multiple→Animals), animal/microbe leaderboards regenerated with a fully-attributed 42/42 swap inventory, and all three Phase-2 xfail locks (AUD-01, WR-02, WR-03) unmarked to permanent green contracts + comparator INT/BOOL_CROSS labels**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-10T01:40:17Z
- **Completed:** 2026-10-10T01:57:09Z
- **Tasks:** 4/4
- **Files modified:** 11

## Accomplishments

- **FIX-02 end-to-end (SC-1 three-in-one):** `script/summarize_comparison.py` now groups datasets by `pipeline/datasets_info.json`'s Category column via `load_arena_map()` on a monkeypatchable `REGISTRY_PATH` (script-file-relative, not CWD), with `MAJORITY_ARENA = {"Multiple": "Animals"}` (maintainer-confirmed) and a plain-dict hard-fail join — an unregistered dataset aborts with `KeyError`, never a fallback to the file's species value. The result-JSON `dataset.species` string is no longer read on the grouping path.
- **Gate evidence:** the blocking-human Category review (CONTEXT species-Q2) was presented and approved before any code/regeneration (prior executor's STEP 0); the verbatim `approved` disposition and the full 50-row record (45 agree / 2 conflicts: GUE__EPI_GM12878 registry-Animals-vs-file-Microbe and GUE__fungi_species_20 registry-Microbe-vs-file-Animals / 2 Multiple-origin zero-net-change / 3 inert no-result rows) are committed as `04-CATEGORY-REVIEW.md`.
- **Regeneration matched the previewed inventory exactly** (see the record below).
- **AUD-01 unmarked permanently green** — marker removed (body intact), fixture defect entry corrected (`athaliana` → `Plants`, companion-guarded deliberate), same commit as the fix.
- **WR-03 discharged (D-13):** `get_float` isfinite guard (RED-proven pin flip in `test_aggregation.py`, module docstring documents the flip), 3 markers removed, number-neutrality proven (`make data` → CLEAN over committed data).
- **WR-02 + IN-01 discharged (D-13):** `walk()` reports equal-value bool/int cross-type pairs as `BOOL_CROSS` and int-vs-int unequal pairs as `INT` (not FLOAT_BIG); vocabulary table updated; WR-02 marker removed; crafted-pair verify exact.
- **Standing real-tree guards:** `test_real_tree_arena_membership` (join-derived 22/13 + swap, corroborated by the committed files' per-model samples ceiling) and `test_unregistered_dataset_aborts_grouping` (end-to-end KeyError pin).
- **Lint scope growth (D-08):** `script/summarize_comparison.py` + `baseline/compare.py` joined `make lint`; arriving findings fixed (I001 import sort, SIM101 isinstance merge).

## Aggregation-diff inventory (SC-1 gate evidence, reconciled against 04-RESEARCH Pattern 1)

| File | Diff | Attribution |
|------|------|-------------|
| `models_comparison.json` | **byte-identical** | total aggregation never reads the arena |
| `models_comparison_plant.json` | **byte-identical** | plant membership identical under both sources (12 present file-Plants = 12 present registry-Plants; 3 registry-Plants inert) |
| `models_comparison_animal.json` | **42/42 models changed, 0 added, 0 dropped** — 376 value diffs (321 FLOAT_BIG + 55 INT post-Task-3 labels) | membership swap: `GUE__fungi_species_20` leaves (file-Animals → registry-Microbe), `GUE__EPI_GM12878` enters (file-Microbe → registry-Animals); iDNA_ABF ×2 stay (Multiple→Animals = today's value, zero net change); **22 datasets before and after** |
| `models_comparison_microbe.json` | **42/42 changed, 0 added, 0 dropped** — 380 value diffs (321 FLOAT_BIG + 59 INT) | inverse swap (EPI_GM12878 leaves, fungi_species_20 enters); **13 datasets before and after** |

- Membership arithmetic: animal 22 = 19 agree-with-results + EPI_GM12878 in + 2 Multiple→Animals; microbe 13 = 12 agree + fungi_species_20 in. Verified by the plan's assertion command and by `test_real_tree_arena_membership`.
- Every per-model numeric delta is arithmetically attributable to removing one dataset's contribution and adding the other's (rank_score, sums, averages, top-K counters, samples unchanged per model); the final `rank` field may shift purely from reordering.
- Sample spot-check (matches the maintainer's verified dry-run): DNABERT-2-117M animal `avg_rank` 19.36→19.73, microbe 20.85→20.23.
- **Label caveat:** the Task-1 inventory was produced with pre-Task-3 labels (all 376/380 diffs reported FLOAT_BIG); after Task 3 the integer diffs decompose honestly as 55/59 INT + 321 FLOAT_BIG per file. Counts and membership (what the gate consumes) are label-independent.
- Maintainer review confirmation: `.planning/phases/04-correctness-methodology-core/04-CATEGORY-REVIEW.md` (response: `approved`, 2026-10-10).

## Task Commits

Each task was committed atomically:

1. **Task 1: TRACER — Category-based grouping end-to-end (gate → fix → regenerate → inventory → lock unmark)** — `6bb9364` (feat)
2. **Task 2: WR-03 get_float isfinite guard + pin flips + lock unmark** — `a0d254d` (fix)
3. **Task 3: IN-01 INT label + WR-02 BOOL_CROSS + lock unmark** — `b34f43e` (fix)
4. **Task 4: Post-fix reconciliation** — full-chain rerun evidence recorded in this SUMMARY; no code changes (gates: `make data` CLEAN, `make test` 202 passed + node 2, `make lint` clean, `make typecheck` clean, `uv lock --check` OK)

**Plan metadata:** (docs commit follows this SUMMARY)

## Files Created/Modified

- `script/summarize_comparison.py` — REGISTRY_PATH/MAJORITY_ARENA constants, `load_arena_map()` hard-fail join replacing the species read; `get_float` isfinite guard (Task 2); docstring updated to the arena source
- `baseline/compare.py` — BOOL_CROSS + INT labels in `walk()`, vocabulary table updated
- `tests/test_known_defects.py` — AUD-01/WR-02/WR-03 markers removed (bodies stay); NEW `test_real_tree_arena_membership`, `test_unregistered_dataset_aborts_grouping`, `test_compare_same_type_equal_values_stay_silent`, `test_compare_labels_int_vs_int_mismatch_as_int`; docstrings made honest for the all-green state
- `tests/test_aggregation.py` — WR-03 pins flipped to isfinite semantics; docstring documents the flip
- `tests/test_golden.py` — synthetic-registry injection (`REGISTRY_PATH` monkeypatch) so goldens stay identical under the switch
- `tests/fixtures/synthetic_datasets_info.json` — NEW: 3 FakeDS registry rows (Categories == fixture species values)
- `tests/fixtures/export_chain/defect_species_performance.json` — defect entry corrected to `"Plants"` (deliberate, companion-guarded)
- `.planning/phases/04-correctness-methodology-core/04-CATEGORY-REVIEW.md` — NEW: maintainer gate evidence
- `Makefile` — lint scope += summarize_comparison.py + compare.py
- `dnallm-mark/data/models_comparison_animal.json`, `dnallm-mark/data/models_comparison_microbe.json` — regenerated per the inventory

## Decisions Made

- Multiple→Animals mapping applied as confirmed at the gate (no row corrections → the previewed inventory stood verbatim).
- `test_real_tree_arena_membership` corroborates join-derived sizes via the committed files' max per-model `samples` (22/13) — the strongest membership tie the comparison-file schema supports (the files carry counts, not dataset name lists).
- The unregistered-dataset pin drives `main()` end-to-end in a tmp tree (stronger than a dict-lookup-only pin), using the existing fixture's dataset block as payload.
- PIN-VALIDATION.md checked for vocabulary consumers: its label mentions are historical observed-class records, not a vocabulary enumeration — no update needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Documentation accuracy] Lock docstrings corrected beyond the literal "body stays" instruction**
- **Found during:** Task 3 (after the last marker came off)
- **Issue:** The plan said "remove the marker (and only the marker — body stays)" for each lock; after all three unmarks, the lock docstrings' "Today the asserts fail … so the test xfails" phrasing was factually false on permanently green tests, and the module header still described the file as xfail locks.
- **Fix:** Minimal tense/history corrections (module header + 3 function docstrings) in the Task-3 commit; zero assertion changes.
- **Files modified:** tests/test_known_defects.py
- **Verification:** Full suite green (202 passed, 0 xfailed); docs now match state.
- **Committed in:** b34f43e

---

**Total deviations:** 1 auto-fixed (documentation accuracy)
**Impact on plan:** None on behavior or scope — assertion surfaces untouched; ruff findings fixed in-plan (I001/SIM101/F401 were anticipated by "fix any fresh ruff findings").

## Issues Encountered

None — the regeneration matched the previewed inventory byte-for-byte-class; no out-of-inventory observation occurred.

## User Setup Required

None - no external service configuration required.

## Authentication Gates

None — the plan's blocking-human Category-review gate was resolved by the maintainer BEFORE this continuation dispatch (response: `approved`, recorded verbatim in 04-CATEGORY-REVIEW.md).

## Next Phase Readiness

- Ready for 04-02 (unified exporter): the exporter must apply Multiple→majority before emission (schema enum rejects "Multiple") and joins the same registry; `MAJORITY_ARENA`/`REGISTRY_PATH` in summarize_comparison are the consumer-side precedent.
- Ready for 04-05: the 2 committed task_performance info.species values (EPI_GM12878, fungi_species_20) still carry file-side values — routed there per OQ4 disposition.
- REV-03 and FIX-02 remain open requirement IDs (shared with 04-02/04-04/04-05) — the species-from-human-verified-table slice landed here; the exporter itself is 04-02's deliverable.
- Suite baseline moved: 202 passed + 0 xfailed + node 2 (was 193 + 5 xfailed).

## Self-Check: PASSED

- Files verified on disk: 04-CATEGORY-REVIEW.md, synthetic_datasets_info.json, both regenerated comparison files — all FOUND
- Commits verified as ancestors of HEAD: 6bb9364, a0d254d, b34f43e — all FOUND
- evaluation-scope (commits-only): resolved with ≥1 commit on this branch
- All plan acceptance criteria re-run post-commit: PASS (per task sections above)

---
*Phase: 04-correctness-methodology-core*
*Completed: 2026-10-10*
