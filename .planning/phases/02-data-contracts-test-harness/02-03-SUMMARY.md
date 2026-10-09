---
phase: 02-data-contracts-test-harness
plan: "03"
subsystem: testing
tags: [pytest, determinism, byte-identical-regression, xfail-strict, ast-contract, known-defect-locks]

# Dependency graph
requires:
  - phase: 02-data-contracts-test-harness plan 01
    provides: conftest thread pinning + sys.path roots, registered `slow` marker, make test/test-fast lanes
  - phase: 02-data-contracts-test-harness plan 02
    provides: get_float non-finite pass-through plain pins in tests/test_aggregation.py (the fact the WR-03 lock asserts against), JS copy-trick precedent
provides:
  - tests/test_determinism.py — slow-marked real-tree chain regression: run x2 byte-identical AND byte-identical to the committed tree (47 task_performance + 4 models_comparison + tasks.json), with a trailing git-status guard proving dnallm-mark/data/ is never written
  - tests/test_known_defects.py — three xfail(strict=True) defect locks (AUD-01-P0 AST source-contract, WR-02 comparator bool/int silence, WR-03 non-finite get_float parametrized nan/inf/-inf), reason-tagged, false-lock-guarded via --runxfail
  - The Phase 4 fix procedure contract: fix + remove matching marker in the same commit; an unexpected XPASS fails the suite
affects: [04-correctness-fixes, 05-ci-packaging]

actuals:
  tokens: 4058     # chars/4 over the realized diff (16233 chars, two new test files)
  tasks: 2
  commits: 2       # MEASURED: git rev-list --count 5271f53..HEAD (#3968)
plan_head_before: 5271f539a446131e6de439b1d003ef0685d9fb51
plan_head_after: 89c71f2dbaa573faf12aec6e288ea5d65882dfaf

# Tech tracking
tech-stack:
  added: []    # nothing new — pytest 9.1.1 landed in 02-01; node is a builtin runner
  patterns:
    - real-tree determinism via subprocess chain x2 in a pytest tmp copy of the committed inputs, outputs snapshotted as {relative-posix-path: bytes} and compared run-vs-run and run-vs-committed
    - AST source-contract locking for unimportable production code (pipeline read as text, anchored on the unique Assign/Subscript+dataset-dict shape, honest pytest.fail on restructuring)
    - xfail(strict=True) house style with finding-ID + "Phase 4 fix" reason strings and a --runxfail false-lock probe in the verify battery

key-files:
  created:
    - tests/test_determinism.py
    - tests/test_known_defects.py
  modified: []

key-decisions:
  - "D-10's ~40s/chain-run estimate was a never-re-timed planning figure: measured ~0.3s per run on the dev machine (warm cache, GB10) — the docstring records measured reality; the slow marker stays because the lane is qualitatively heavier than the unit lane, not because of measured cost"
  - "AST anchor corrected from the research snippet's parents[2] to parents[1]: the snippet's path resolved outside the repo and would have produced a FileNotFoundError XFAIL — a false lock (Pitfall 6), caught at authoring time and disproven by the --runxfail probe"
  - "Markers formatted so the first physical line carries xfail(strict=True (the plan's literal grep verify) while long reason strings wrap onto continuation lines"

patterns-established:
  - "Determinism-regression pattern: copytree inputs → subprocess chain (sys.executable, cwd=tmp, env-pinned via conftest inheritance) → JS copy trick with per-run rebuild of the JS-visible task_performance dir → byte snapshots keyed by relative posix path"
  - "Defect-lock pattern: minimal independently-exercised xfail bodies, strict=True + finding ID + 'Phase 4 fix' in every reason, --runxfail probe as a standing verify step, honest pytest.fail when an AST anchor disappears"

requirements-completed: [TEST-03, TEST-02]  # verbatim from plan frontmatter

# Coverage metadata (#1602) — one entry per shipped deliverable
coverage:
  - id: D1
    description: "Real-tree determinism regression (TEST-03 real half): two full chain runs over a tmp copy of the 42 committed inputs are byte-identical to each other and to the committed derived tree (47 task_performance + 4 models_comparison + tasks.json), with file-set exactness and a git-status guard proving the committed tree untouched"
    requirement: TEST-03
    verification:
      - kind: unit
        ref: "tests/test_determinism.py#test_chain_is_deterministic_and_matches_committed (pytest -m slow: 1 passed)"
        status: pass
      - kind: other
        ref: "command: pytest -m 'not slow' -> 1 deselected (lane segregation); default run -> 1 passed; git status --porcelain -- dnallm-mark/data/ empty after runs"
        status: pass
    human_judgment: false
  - id: D2
    description: "Three known-defect locks as xfail(strict=True) tests: AUD-01-P0 species-as-dataset (AST source-contract, pipeline never imported), WR-02 equal-value bool/int comparator silence (walk driven directly), WR-03 non-finite get_float pass-through (parametrized nan/inf/-inf) — 5 xfailed items, zero XPASS"
    verification:
      - kind: unit
        ref: "tests/test_known_defects.py (pytest -q: 5 xfailed; --runxfail probe: 5 failed on defect assertions — no false locks)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Slow-lane segregation proven within this plan's scope (TEST-02 scope-proof half): -m slow runs the determinism test, -m 'not slow' deselects it, make test-fast stays green without it"
    requirement: TEST-02
    verification:
      - kind: other
        ref: "commands: pytest -m slow -> 1 passed; pytest -m 'not slow' -> 1 deselected; make test-fast -> 132 passed + 5 xfailed + 1 deselected"
        status: pass
    human_judgment: false

# Metrics
duration: 7min
completed: 2026-10-09
status: complete
---

# Phase 2 Plan 03: Determinism Regression & Known-Defect Locks Summary

**Real-tree chain determinism regression (chain x2 byte-identical and committed-tree-equal via subprocess + JS copy trick) plus three xfail(strict=True) defect locks — AUD-01-P0 AST species check, WR-02 comparator bool/int silence, WR-03 NaN/inf get_float pass-through — all proven green-and-genuinely-red in one 1-passed + 5-xfailed run.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-09T04:08:59Z
- **Completed:** 2026-10-09T04:16:04Z
- **Tasks:** 2
- **Files modified:** 2 (2 created, 0 modified)

## Accomplishments

- `tests/test_determinism.py` (TEST-03 real half, D-10): the one `@pytest.mark.slow` test copies the 42 real committed inputs into a pytest tmp tree, runs `get_task_performance.py` + `summarize_comparison.py` as `sys.executable` subprocesses with `cwd=tmp` (inheriting conftest's thread pinning), then the JS generator via the copy-into-fixture-tree trick with the JS-visible `task_performance/` dir rebuilt per run so run 2 sees only run-2 outputs — and asserts (1) run1 == run2 bytes, (2) file-set exactness + every output byte-identical to its committed counterpart with a per-file drift message, (3) `git status --porcelain -- dnallm-mark/data/` empty (the committed tree is read-only to the suite; T-02-05)
- `tests/test_known_defects.py` (D-03/D-04/D-07): three `xfail(strict=True)` locks, every reason string carrying its finding ID and "Phase 4 fix" — AUD-01-P0 via an AST source-contract check of the unique dataset-entry construction site (species must come from `row.get`, today `model_row.get` at pipeline:1229; pipeline read as source text, never imported; honest `pytest.fail` if the site restructures; Phase 3 dnallm-dev coupling documented in the docstring), WR-02 by driving `compare.walk(True, 1, ...)` directly, WR-03 parametrized over nan/inf/-inf against `get_float(bad, default=None) is None`
- False-lock guard proven: `--runxfail` makes all 5 items FAIL on their defect assertions (e.g. `assert -inf is None ... get_float('-inf', default=None)`), not on collection/import errors — the exact adjacency hazard TEST-06 warns about
- Lane segregation proven: `-m slow` → 1 passed; `-m "not slow"` → 1 deselected; `make test-fast` → 132 passed + 5 xfailed + 1 deselected; combined own-modules run → **1 passed + 5 xfailed, 0 failed**
- Zero production-file changes (D-04): `git diff 5271f53..HEAD -- script/ scripts/ baseline/ pipeline/ dnallm-mark/ schemas/` is empty
- Supplementary (not this plan's formal claim — the execute-phase post-merge gate owns it): the full `make test` on the already-merged main tree is green (pytest slow lane included + node:test 2 pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Determinism regression over the real committed tree** - `2f7ea37` (test)
2. **Task 2: xfail(strict=True) defect locks — AUD-01-P0, WR-02, WR-03** - `89c71f2` (test)

**Plan metadata:** (final docs commit below)

## Files Created/Modified

- `tests/test_determinism.py` - slow-marked real-tree chain regression: subprocess chain x2 + JS copy trick, byte snapshots keyed by relative posix path, committed-counterpart mapping, git-status tampering guard
- `tests/test_known_defects.py` - three strict xfail defect locks (AST pipeline contract, comparator walk, get_float non-finite) with finding-ID reason strings and false-lock-safe minimal bodies

## Decisions Made

- Measured wall time replaces D-10's estimate in the docstring: ~0.3s per chain run on the dev machine (the ~40s figure was never re-timed); the `slow` marker stays because the lane is qualitatively heavier than the unit lane, not because of measured cost — `make test-fast` excludes it by marker
- AST anchor uses `Path(__file__).resolve().parents[1]` (repo root), correcting the research snippet's `parents[2]` which resolved outside the repo and would have locked nothing (see Deviations #1)
- Marker decorators formatted so the first physical line contains `xfail(strict=True` — the plan's literal grep verify — with long reasons wrapped onto continuation lines
- The `dnallm-mark/data/task_performance` JS-visible copies are rebuilt (`rmtree` + `copytree`) per run rather than overwritten in place, guaranteeing run 2 sees only run-2 outputs even if the file set were ever to differ

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Research Pattern 2's AST-test path anchor resolves outside the repo**
- **Found during:** Task 2 (authoring the AUD-01-P0 lock)
- **Issue:** The research-verified test body opens the pipeline with `Path(__file__).parents[2] / "pipeline" / ...` — from `tests/test_known_defects.py`, `parents[2]` is one level ABOVE the repo, so `read_text` would raise `FileNotFoundError` and the test would XFAIL for the wrong reason: a false lock (exactly Pitfall 6 / TEST-06 adjacency)
- **Fix:** Anchor corrected to `parents[1]` (repo root); construction-site uniqueness re-probed live before writing (exactly one matching Assign in the pipeline)
- **Files modified:** tests/test_known_defects.py
- **Verification:** `--runxfail` probe shows the test failing on the actual species assertion (`model_row` vs `row`), not on a file error; `5 xfailed / 5 runxfail-failed` as required
- **Committed in:** 89c71f2 (Task 2 commit)

**2. [Rule 1 - Bug] Plan's ~80s wall-time expectation is wrong for this machine**
- **Found during:** Task 1 verify (test passed in 0.61s)
- **Issue:** The plan's action text prescribes a docstring documenting "~80s expected wall time (two chain runs, D-10's ~40s each)" — D-10's figure was a planning estimate never re-timed (research A5); measured cost is ~0.3s per chain run, so the prescribed docstring would have stated a falsehood
- **Fix:** Docstring documents measured reality (2026-10-09, ~0.3s/run warm cache) alongside D-10's conservative figure, and states the slow marker's real rationale (qualitative weight + marker-based exclusion, not measured cost)
- **Files modified:** tests/test_determinism.py
- **Verification:** Manual out-of-pytest chain timing probe (pivot 0.063s, summarize 0.206s, outputs byte-identical to committed) confirmed the measurement before the docstring was written
- **Committed in:** 2f7ea37 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 research/plan-text accuracy bugs — no production code touched, no semantic test change)
**Impact on plan:** None on scope or must_haves truths — every truth is asserted exactly as written; both fixes make documentation and lock-anchoring honest rather than changing what is proven.

## Issues Encountered

- Ruff (PLW1510) flagged the intentional bare `subprocess.run` in the determinism helper; resolved with an explicit `check=False` plus comment (failure is handled below with the captured output). Routine hygiene, no semantic change.
- `pytest -m "not slow"` on the isolated module exits 5 ("no tests collected") because the module's single item is deselected — the documented pytest behavior for a fully-deselected selection, and within the plan verify's allowed outcomes ("deselected", no collected/failed items). `make test-fast` over the whole suite exits 0.

## Authentication Gates

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 2 is complete (3/3 plans): schemas + harness (02-01), synthetic corpus + goldens + JS lane (02-02), real-tree determinism + defect locks (02-03)
- The Phase 4 executor's contract is mechanical: fix the defect, remove the matching marker in the same commit, suite green — an unexpected XPASS fails the suite (strict=True), and IN-01 (comparator pure-int labeling) lands in Phase 4 alongside the WR-02 fix when the comparator is next modified
- Phase 3 caution (recorded in the AUD-01 lock's docstring): if the dnallm-dev pipeline adaptation moves the dataset-entry construction site, the AST anchor gets a deliberate one-line update — never a silent xfail
- Phase 5 CI can run `make test` verbatim (slow lane included, ~1s on comparable hardware) and reuse the `--runxfail` probe as a lock-integrity job
- Supplementary observation for the post-merge gate: full `make test` already green on the main tree (133 pytest items incl. slow + 5 xfailed; node:test 2 pass)

## Self-Check: PASSED

- Both plan files exist on disk (tests/test_determinism.py, tests/test_known_defects.py)
- Both task commits (2f7ea37, 89c71f2) verified as ancestors of HEAD
- Measured commits from ledger: 2 (`git rev-list --count 5271f53..HEAD`)
- Plan verification re-run green: slow lane 1 passed + tree clean; known defects 5 xfailed / runxfail 5 failed; combined 1 passed + 5 xfailed; make test-fast 132 passed + 5 xfailed; zero production-file diff

---
*Phase: 02-data-contracts-test-harness*
*Completed: 2026-10-09*
