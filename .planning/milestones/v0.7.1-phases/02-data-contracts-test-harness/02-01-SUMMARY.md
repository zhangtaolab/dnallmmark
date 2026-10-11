---
phase: 02-data-contracts-test-harness
plan: "01"
subsystem: testing
tags: [json-schema, draft-2020-12, pytest, jsonschema, uv, makefile, data-contracts]

# Dependency graph
requires:
  - phase: 01-audit-release-foundations
    provides: uv/pyproject substrate (pandas/numpy data group, uv.lock), deterministic data generators (FIX-05), baseline comparator + PIN-VALIDATION diff vocabulary
provides:
  - Four fully-strict draft-2020-12 JSON Schemas (model_performance, task_performance, models_comparison, tasks_index) governing all 94 committed leaderboard JSON files
  - tests/conftest.py scaffold — thread pinning (TEST-02) + sys.path import roots for script/ and baseline/ (consumed by plans 02-02/02-03)
  - pytest `slow` marker registration and testpaths config (consumed by 02-03's determinism test)
  - Makefile entry points make data / test / test-fast / lint over uv run (REL-04)
  - dev dependency group (pytest 9.1.1, jsonschema 4.26.0, ruff 0.16.10 — floors in pyproject, pins in uv.lock)
affects: [02-02, 02-03, 04-correctness-fixes, 05-ci-packaging]

actuals:
  tokens: 16300    # chars/4 over the realized diff (65145 chars across 11 files)
  tasks: 3
  commits: 3       # MEASURED: git rev-list --count 4fd682b..HEAD (#3968)
plan_head_before: 4fd682b423c03f3ef79f1280e5e69c24e85d9761
plan_head_after: 5c556a9eb0f4208208d3b966fe9c10fc90d5cdee

# Tech tracking
tech-stack:
  added: [pytest 9.1.1, jsonschema 4.26.0, ruff 0.16.10 (dev group, uv-locked)]
  patterns: [fully-strict draft-2020-12 schemas with closed enums (D-01/D-02), parametrized per-file schema validation, enum-equals-committed-data self-check, make-over-uv single-command chain]

key-files:
  created:
    - schemas/model_performance.json
    - schemas/task_performance.json
    - schemas/models_comparison.json
    - schemas/tasks_index.json
    - tests/conftest.py
    - tests/test_schemas.py
    - Makefile
  modified:
    - pyproject.toml
    - uv.lock
    - README.md
    - .gitignore

key-decisions:
  - "Self-contained schemas (duplication over cross-file $ref) per resolved Open Question 1 — strictness is per-file and forced versioning stays local"
  - "make test deliberately excludes node --test until tests/js/ exists in plan 02-02 — a node step against a missing directory would break the wave-1 suite"
  - "Lint scope is tests/ only this phase: D-04 forbids touching production code and ~21 pre-existing ruff findings exist in script/scripts/baseline/pipeline — widening is deferred, not silent"

patterns-established:
  - "Strict-schema pattern: additionalProperties:false at every object level, every surveyed field required, closed enums, anyOf number-or-\"\" for the missing-value convention"
  - "Per-file parametrized validation: one pytest item per committed file with readable json_path/validator/message failure lines"
  - "Enum self-check: schema enum asserted equal to the set of values actually present in committed data (D-02)"

requirements-completed: [REL-04, TEST-06, TEST-02]

# Coverage metadata (#1602) — one entry per shipped deliverable
coverage:
  - id: D1
    description: "Four fully-strict draft-2020-12 schemas; all 94 committed leaderboard JSON files validate with zero errors; injected-drift probes fail with additionalProperties/enum errors"
    requirement: TEST-06
    verification:
      - kind: unit
        ref: "tests/test_schemas.py#test_committed_file_matches_schema (94 parametrized items)"
        status: pass
      - kind: unit
        ref: "tests/test_schemas.py#test_schema_documents_are_wellformed"
        status: pass
      - kind: other
        ref: "probe: bogus info key -> additionalProperties error at $.info; F1-casing mutation -> enum error"
        status: pass
    human_judgment: false
  - id: D2
    description: "D-02 enum self-check: schema metric enum == observed committed-data enum == {f1, mcc, spearmanr, AUPRC}"
    requirement: TEST-06
    verification:
      - kind: unit
        ref: "tests/test_schemas.py#test_metric_enum_matches_committed_data"
        status: pass
    human_judgment: false
  - id: D3
    description: "make data from repo root regenerates 47 task_performance + 4 models_comparison + tasks.json with zero diff over dnallm-mark/data/ (REL-04)"
    requirement: REL-04
    verification:
      - kind: other
        ref: "command: make data && test -z \"$(git status --porcelain -- dnallm-mark/data/)\" — exit 0"
        status: pass
    human_judgment: false
  - id: D4
    description: "uv/pytest substrate: dev group (pytest/jsonschema/ruff) with uv lock --check green, default-groups untouched, make test/test-fast/lint through uv run --group dev, conftest thread pinning + slow marker + testpaths (TEST-02 scaffold)"
    requirement: TEST-02
    verification:
      - kind: other
        ref: "commands: uv lock --check (exit 0), make lint (exit 0), make test-fast (96 passed)"
        status: pass
    human_judgment: false
  - id: D5
    description: "D-08 micro-fixes: README Output fields gains avg_PFLOPs bullet (IN-03); .gitignore gains exactly one .planning/tmp/ line (IN-04)"
    verification:
      - kind: other
        ref: "commands: grep -n avg_PFLOPs README.md (line 259); git check-ignore .planning/tmp/ + grep count == 1"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-10-09
status: complete
---

# Phase 2 Plan 01: Data Contracts & Test Harness Summary

**Four fully-strict draft-2020-12 JSON Schemas validated by a 96-item pytest suite over all 94 committed leaderboard files, plus a uv-managed dev group and make data/test/test-fast/lint entry points — regeneration proven byte-identical.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-09T03:36:44Z
- **Completed:** 2026-10-09T03:43:41Z
- **Tasks:** 3
- **Files modified:** 11 (7 created, 4 modified)

## Accomplishments

- Four fully-strict draft-2020-12 schemas (`schemas/*.json`) with `$id`s under `raw.githubusercontent.com/zhangtaolab/dnallmmark/main/schemas/`, `additionalProperties: false` at every object level, every surveyed field required, and the three closed enums (metric `[f1, mcc, spearmanr, AUPRC]`, species `[Animals, Plants, Microbe]`, type `[binary, multiclass, regression, multilabel]` per D-02) — all 94 committed JSON files validate with zero errors
- The `""`-means-missing convention encoded as exactly two legal states (`anyOf [{type: number}, {const: ""}]` on the 13 non-FLOPs metric fields; `anyOf [{type: integer}, {const: ""}]` on batch_size) — behavioral probes confirm numeric 0 passes while `null`, `"0"`, and `"N/A"` all fail
- `tests/test_schemas.py`: parametrized per-file validation (94 items), schema well-formedness checks, and the D-02 enum self-check tying the metric enum to committed data
- `tests/conftest.py`: thread pinning (OMP/OPENBLAS/MKL/NUMEXPR/VECLIB=1) before any numpy import + `sys.path` roots for `script/` and `baseline/` (TEST-02 scaffold for plans 02-02/02-03)
- Makefile `data`/`test`/`test-fast`/`lint` over `uv run` — `make data` from repo root regenerates all 52 derived files with **zero diff** over `dnallm-mark/data/` (REL-04 proven behaviorally; FIX-05 determinism holding)
- Dev dependency group landed: pytest 9.1.1 / jsonschema 4.26.0 / ruff 0.16.10 (floors in pyproject, exact pins in uv.lock, `default-groups = ["data"]` untouched) with `[tool.pytest.ini_options]` registering the `slow` marker
- D-08 micro-fixes: README `avg_PFLOPs` output-field bullet (IN-03), `.planning/tmp/` gitignore line (IN-04)

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end contract slice (dev group, conftest, Makefile, model_performance schema, 42-file validation)** - `7b64a15` (feat)
2. **Task 2: Complete contract set (3 remaining schemas, 94-file parametrization, D-02 enum self-check)** - `5572785` (feat)
3. **Task 3: make data zero-diff proof + D-08 micro-fixes** - `5c556a9` (docs)

**Plan metadata:** (see final docs commit)

## Files Created/Modified

- `schemas/model_performance.json` - strict contract for the 42 producer files (info 11-key card + performance map of datasetEntry)
- `schemas/task_performance.json` - strict contract for the 47 task files (info = 8-key dataset block, performance = alias map)
- `schemas/models_comparison.json` - strict contract for all 4 comparison files (7-key subset model card, 15-key aggregate)
- `schemas/tasks_index.json` - strict contract for tasks.json (version/count/tasks, 9-key entries)
- `tests/conftest.py` - thread pinning + sys.path import roots
- `tests/test_schemas.py` - 94-file parametrized validation + well-formedness + enum self-check
- `Makefile` - data/test/test-fast/lint entry points over uv run
- `pyproject.toml` - dev group filled + [tool.pytest.ini_options] (testpaths, slow marker)
- `uv.lock` - exact dev-group pins
- `README.md` - avg_PFLOPs output-field bullet (IN-03)
- `.gitignore` - .planning/tmp/ (IN-04)

## Decisions Made

- Self-contained schema files (defs duplicated, no cross-file `$ref`) per resolved Open Question 1 — per-file strictness, local forced versioning
- `make test` excludes `node --test` until `tests/js/` exists in plan 02-02 (a node step against a missing directory would break the wave-1 suite)
- Lint scope = `tests/` only this phase, with the deferral recorded as a comment in the Makefile (D-04; ~21 pre-existing findings in production dirs)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stale dev-group comment left by `uv add`**
- **Found during:** Task 1 (dev group install)
- **Issue:** `uv add` rewrote the `dev = []` list but left the Phase 1 comment "Phase 2 adds pytest/ruff — keep Phase 1 minimal" dangling after the closing bracket — now factually wrong and misleading
- **Fix:** Replaced with an accurate comment documenting the floor-bounds-in-pyproject / pins-in-uv.lock split and the explicit `--group dev` invocation requirement (Pitfall 2)
- **Files modified:** pyproject.toml
- **Verification:** make test-fast / uv lock --check still green; comment matches repo's dated-provenance style
- **Committed in:** 7b64a15 (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Cosmetic-comment accuracy fix only; no semantic change, no scope creep.

## Issues Encountered

None.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for plan 02-02 (aggregation/pivot/golden tests): conftest import roots (`summarize_comparison`, `get_task_performance`, `compare`) and the `slow` marker are in place; `make test` gains the `node --test tests/js/` line when `tests/js/` exists
- Ready for plan 02-03 (determinism + known-defect locks): the `slow` marker is registered for the real-tree determinism test; the xfail tests will import `compare`/`get_float` via conftest roots
- Schema contract surface is published — Phase 3's pipeline adaptation (PIPE-03) validates its output against `schemas/model_performance.json`; any producer shape change now requires a schema edit first (D-01)

## Self-Check: PASSED

- All 11 plan files exist on disk (4 schemas, conftest, test module, Makefile, pyproject.toml, uv.lock, README.md, .gitignore)
- All 3 task commits (7b64a15, 5572785, 5c556a9) verified as ancestors of HEAD
- Measured commits from ledger: 3 (`git rev-list --count 4fd682b..HEAD`)

---
*Phase: 02-data-contracts-test-harness*
*Completed: 2026-10-09*
