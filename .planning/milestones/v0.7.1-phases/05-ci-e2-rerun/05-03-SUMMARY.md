---
phase: 05-ci-e2-rerun
plan: 03
subsystem: data-chain
tags: [n-frequency-audit, eval-subsets, untrusted-data, fairness, subset-file, json-schema, determinism]

# Dependency graph
requires:
  - phase: 05-ci-e2-rerun (05-02)
  provides: green gates (make test 253, lint/typecheck clean, drift no-op) the audit artifacts must not disturb
provides:
  - script/audit_n_frequencies.py — parse-only N/non-ACGT census over the on-disk split CSVs + unified eval-subset computation + emission (n_audit.json/csv, eval_subsets.json, generated DATA.md)
  - The published F7 census — 50 registry rows (43 present / 7 missing GUE as explicit WARNING rows), 16/43 tasks carry rows strict-charset models drop (e.g. CpG 106224 vs 106227) — the fairness gap F7 closes, now measured and published
  - pipeline/eval_subsets.json — the unified task -> row-ID map (43 tasks, 582,927 IDs, every ID strict-filter-surviving by construction), byte-deterministic
  - schemas/n_audit.json strict draft-2020-12 contract + n_audit bucket in the schema suite
  - pipeline/run_finetune.py --subset_file — fail-fast collect-all-problems validation (registry join, int type, [0, Test) range) + the test-split-only select seam between load_local_data and validate_sequences; absent flag = identical code path
affects: [05-ci-e2-rerun (05-04 E2' readiness consumes eval_subsets at launch), E2' itself, public DATA.md]

# Actuals (#2632) — measured from the plan ledger (base 5e4cbe2)
actuals:
  tokens: 838579   # chars/4 over the realized diff (3354317 chars — ~3.3MB is the COMMITTED audit artifacts: n_audit.json/csv + the 582,927-ID eval_subsets.json; authored code/tests/docs are ~90k chars) — plan estimate 45000 (code-scale; artifact bytes dominate the measured diff)
  tasks: 2         # Task 1 (audit + artifacts) + Task 2 (TDD RED+GREEN on --subset_file)
  commits: 3       # MEASURED: git rev-list --count 5e4cbe2..HEAD (0fb4b37, ad4a316, 6c15103)
plan_head_before: 5e4cbe20ebd8b25ebe686b6ffc3d80d25fb9000f
plan_head_after: 6c151030e32266de7bb93bc6ef6c3e019d1c0c88

# Tech tracking
tech-stack:
  added: []        # stdlib-only audit script; zero installs
  patterns:
    - "Filter-semantics mirroring: the audit's survivor checks reproduce suite check_sequence @483a35c literally (set(seq.upper()) membership, 0<=len<=10010) — the gc=(0,1) range can never reject (calc_gc_content in [0,1] always) and is documented away, not re-implemented"
    - "C-level counting under untrusted-data discipline: str.translate keeps exactly the non-ACGT chars (one pass), Counter.update over the remainder, set(seq) for charset membership — parse-only, per-row [Skip], bounded csv field sizes"
    - "Pure validator + thin exit wiring: validate_subset_file returns every problem; the __main__ block exits — the _validate_filters discipline stays CPU-testable"

key-files:
  created:
    - script/audit_n_frequencies.py
    - tests/test_audit_n.py
    - schemas/n_audit.json
    - DATA.md
    - dnallm-mark/data/n_audit.json
    - dnallm-mark/data/n_audit.csv
    - pipeline/eval_subsets.json
    - .planning/phases/05-ci-e2-rerun/05-03-RED-EVIDENCE.json
  modified:
    - pipeline/run_finetune.py
    - tests/test_run_finetune_contracts.py
    - tests/test_schemas.py
    - Makefile

key-decisions:
  - "Dataset_path resolution: registry values carry the datasets/ prefix resolved against pipeline/ by the driver; --datasets-root (default pipeline/datasets) strips exactly that prefix — both conventions documented in the script"
  - "eval_subsets.json omits the 7 missing tasks (no on-disk data -> no IDs; the --subset_file contract is keys subseteq registry, so omission is clean) — never an empty list that would select zero rows"
  - "DATA.md is generated WHOLESALE by the audit (prose + table, byte-stable) — the census is published from code, not hand-counted; regeneration overwrites cleanly"
  - "Bool rejected as a non-integer ID (JSON true/false are not ints in the contract sense) alongside strings/floats"
  - "by_char census is case-sensitive raw counting (N and n distinct) while the filter uppercases per suite semantics — both documented in the module docstring"

patterns-established:
  - "Real-artifact CPU-side proof: exec-extract the pipeline's pure functions and run them against the committed artifact + real registry (43 tasks / 582,927 IDs / zero problems) without ever importing torch"

requirements-completed: [REV-07]

coverage:
  - id: D1
    description: "N-frequency/non-ACGT audit script + published DATA.md appendix + downloadable n_audit.json/csv artifacts (50 rows: 43 present, 7 missing GUE explicit)"
    requirement: REV-07
    verification:
      - kind: unit
        ref: "tests/test_audit_n.py (12 tests: census, charset classes, length boundary, malformed-row skip, missing-dir warning, min-over-classes, ID survival, CSV header, subsets shape, schema validation, DATA.md rows, byte-determinism)"
        status: pass
      - kind: integration
        ref: "make test (277 passed) + make lint + make typecheck + audit re-run git diff --exit-code byte-identical"
        status: pass
    human_judgment: false
  - id: D2
    description: "Unified eval-subset ID map (pipeline/eval_subsets.json) — first N strict-passing test-row indices per task, every ID survives the common filter"
    requirement: REV-07
    verification:
      - kind: unit
        ref: "tests/test_audit_n.py::test_emitted_ids_survive_common_filter_and_are_first_n + test_subsets_json_shape"
        status: pass
      - kind: integration
        ref: "plan verify: 50 tasks / 43 present / 7 missing / all subset lists sorted — python assertion run green"
        status: pass
    human_judgment: false
  - id: D3
    description: "schemas/n_audit.json strict draft-2020-12 contract registered in the committed-data validation suite"
    requirement: REV-07
    verification:
      - kind: unit
        ref: "tests/test_schemas.py (n_audit bucket parametrize + pinned count; 113 schema-lane tests green)"
        status: pass
    human_judgment: false
  - id: D4
    description: "run_finetune --subset_file: fail-fast collect-all-problems validation + test-split-only select seam; absent flag byte-identical"
    requirement: REV-07
    verification:
      - kind: unit
        ref: "tests/test_run_finetune_contracts.py (11 subset tests: valid file, every malformed class named, non-object/unreadable/non-list, test-only select, absent-flag zero calls, seam ordering, [Error] wiring)"
        status: pass
      - kind: integration
        ref: "CPU-side real-artifact proof: pipeline/eval_subsets.json validates against pipeline/datasets_info.json with zero problems (43 tasks, 582,927 IDs)"
        status: pass
    human_judgment: false

# Metrics
duration: 17 min
completed: 2026-10-10
status: complete
---

# Phase 05 Plan 03: N-Frequency Audit + Unified Eval Subsets (--subset_file) Summary

**Parse-only N/non-ACGT census over all 50 registry tasks (43 present / 7 missing GUE honestly warned) with deterministic published artifacts, plus the fail-fast run_finetune --subset_file seam that makes identical-sample-count evaluation provable at E2'**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-10T11:03:00Z
- **Completed:** 2026-10-10T11:20:06Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- The F7 reviewer census is published from code: DATA.md appendix (one row per registry task), downloadable n_audit.json/csv on the site, schema-validated by the suite — regenerated byte-identically over unchanged inputs
- The fairness gap is now MEASURED: 16 of 43 present tasks carry test rows that strict-charset models drop today (BEND CpG 106224/106227; D.melanogaster 54185/54200; human_vs_worm 24355/25000) — exactly the cross-model divergence the unified subsets close
- run_finetune consumes pipeline/eval_subsets.json at E2': validated fail-fast (every malformed class named, [Error] exit before any model load), applied to the TEST split only between load_local_data and validate_sequences, train/dev untouched; absent flag = no select anywhere
- The real audit run committed as artifacts (18 s wall, 3.8M rows, 4 GB tree, stdlib-only)

## Task Commits

Each task was committed atomically:

1. **Task 1: N-frequency audit script + published tables + subset ID lists** — `0fb4b37` (feat)
2. **Task 2: run_finetune --subset_file (TDD)** — RED `ad4a316` (test), GREEN `6c15103` (feat)

**Plan metadata:** (docs commit follows this SUMMARY)

## TDD Record (Task 2, tdd="true")

- **RED** (`ad4a316`): 11 contract tests added over the planned surface — exec-extracted pure functions driven through a recording `.select` stub, validator unit tests over tmp_path JSON fixtures covering every behavior row, and three source-wiring contracts. Run: `pytest tests/test_run_finetune_contracts.py -v` → **11 failed / 12 passed**, every failure an AssertionError on the planned missing behavior (missing functions / flag / wiring), zero import/collection/fixture errors. Evidence record: `.planning/phases/05-ci-e2-rerun/05-03-RED-EVIDENCE.json` (machine classifier not enforced — `workflow.tdd_mode: false` — the record is the honest RED evidence; semantic assessment inside).
- **GREEN** (`6c15103`): `validate_subset_file` (pure, collect-all-problems) + `apply_eval_subset` (test-split-only injectable seam) + `--subset_file` argparse + the two wiring sites. All 23 contract tests pass; full suite 277.
- **REFACTOR:** none needed — the GREEN implementation is already minimal (two pure functions, one flag, two wiring sites); no commit.

## Files Created/Modified
- `script/audit_n_frequencies.py` — the audit (stdlib-only; REPO_ROOT-relative CLI; untrusted-data discipline)
- `tests/test_audit_n.py` — 12 fixture-driven behavior contracts
- `schemas/n_audit.json` + `tests/test_schemas.py` — strict contract + committed-artifact bucket
- `DATA.md` — generated appendix (whole file code-produced)
- `dnallm-mark/data/n_audit.json` / `n_audit.csv` — downloadable artifacts (committed)
- `pipeline/eval_subsets.json` — the --subset_file input (43 tasks, 582,927 IDs)
- `pipeline/run_finetune.py` — --subset_file flag, validator, apply seam
- `tests/test_run_finetune_contracts.py` — 11 new subset contracts
- `Makefile` — audit script in the lint list (never in the make data chain)

## Decisions Made
See key-decisions in the frontmatter (prefix-strip resolution; missing tasks omitted from the subset map; wholesale-generated DATA.md; bool-as-non-integer; case-sensitive by_char vs uppercased filter).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `tests/test_determinism.py::test_chain_is_deterministic_and_matches_committed` red on the first full-suite run — a transient pre-commit state: the not-yet-committed n_audit artifacts appeared as untracked files in `dnallm-mark/data/` (assertion 3). Green immediately after the Task 1 commit; no code change needed.
- Ruff 0.16.10's default rule set is broader than the classic E/F defaults: 6 findings across the new files (FURB188, SIM115, ISC004 x3, PIE810) — all fixed properly in the touched files (removeprefix, with-open restructuring, parenthesized concatenations, tuple startswith); zero noqa added, zero suppression widening.
- Observed mid-run: the read-only DNALLM suite advanced upstream (maintainer commit `32d242a` "chore(release): bump version to 0.8.0" at 18:11 local). Verified zero uncommitted modifications in that repo and zero writes from this session — the read-only constraint held (the E2' dual gate re-checks suite stability at launch).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 05-04 (E2' readiness + data-v2 gate) can consume `pipeline/eval_subsets.json` at launch; the launch checklist should include re-running the audit after the 7 GUE re-extractions (regeneration is one command, byte-deterministic)
- The audit stays a LOCAL maintainer step (gitignored inputs; never in `make data`, never in CI, not drift-gated)
- DATA-01 remains BLOCKED on the shared-ID gate until 05-04 completes (expected)

## Self-Check: PASSED

All created files exist on disk; all three production commits are ancestors of HEAD; acceptance criteria for both tasks re-run green (see coverage block).
