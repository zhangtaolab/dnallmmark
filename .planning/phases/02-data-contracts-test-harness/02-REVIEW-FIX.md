---
phase: 02-data-contracts-test-harness
fixed_at: 2026-10-09T04:59:21Z
review_path: .planning/phases/02-data-contracts-test-harness/02-REVIEW.md
iteration: 1
findings_in_scope: 9
fixed: 7
deferred: 2
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-10-09T04:59:21Z
**Source review:** `.planning/phases/02-data-contracts-test-harness/02-REVIEW.md`
**Iteration:** 1
**Fix scope:** all 5 warnings + IN-02/IN-04; IN-01/IN-03 deferred (rationale below)
**Where verification ran:** the main checkout (branch `autorun`) — the orchestrator
directed main-tree work for this round, so every command and output below is
reproducible from this tree as-is.

**Summary:**
- Findings addressed: 9 (7 fixed, 2 deferred)
- Fixed: WR-01, WR-02, WR-03, WR-04, WR-05, IN-02, IN-04 — one atomic commit each
- Deferred: IN-01, IN-03 (D-04 forbids touching production code this phase)

**Final gates (all green, after all fixes):**
- `make test` — pytest lane `136 passed, 5 xfailed`, JS lane `2 pass / 0 fail`, exit 0
  (136 = 133 pre-fix + WR-01 companion + WR-03 canary + IN-02 widened check)
- `make lint` — `ruff check tests/` → `All checks passed!`
- `OMP_NUM_THREADS=4 ~/.local/bin/uv run --group dev pytest -q` — `136 passed, 5 xfailed`
  (the WR-05 proof; this exact command failed 1 test before the fix)
- `git status --porcelain -- dnallm-mark/data/ tests/ Makefile schemas/` — clean
  (the suite left the published data tree and all committed sources untouched)

All fixes stay within Phase-2-created files (tests/, Makefile); D-04 respected —
no changes to `script/`, `scripts/`, `baseline/`, `pipeline/`, `dnallm-mark/`,
and no changes to `schemas/` (the IN-02 check lives entirely in tests/).

## Fixed Issues

### WR-01: AUD-01 lock's `pytest.fail` honesty guard is swallowed by its own `xfail` marker

**Files modified:** `tests/test_known_defects.py`
**Commit:** `106ad13`
**What changed:**
- Extracted the AST anchor walk into `_find_construction_sites()`
  (`tests/test_known_defects.py:58`) returning ALL matching construction
  sites (empty list when the anchor matches nothing).
- Added the UNMARKED companion `test_aud01_construction_site_anchor_is_findable_and_unique`
  (`tests/test_known_defects.py:93`) — asserts the anchor is found AND
  unique (exactly 1 site). Because it carries no xfail marker, anchor loss
  goes RED, exposing the vacuous lock instead of hiding behind XFAIL.
- Refactored the xfail lock (`tests/test_known_defects.py:119`) to use the
  helper and corrected its docstring: the false "trailing `pytest.fail`
  makes the test fail honestly" claim is replaced by an accurate statement
  that findability is guarded by the companion OUTSIDE the marker.
- Module docstring AUD-01 bullet now names the companion (WR-01).

**Verified:**
- `pytest tests/test_known_defects.py -v` → companion `PASSED`, all 5 locks
  still `XFAIL` (1 passed, 5 xfailed) — lock semantics unchanged.
- Anchor-loss simulation (scratch copy in /tmp, deleted after): a
  syntactically-valid restructured pipeline (`= {` wrapped as `= dict({ })`,
  same runtime behavior but the Assign value becomes a Call so the
  structural anchor no longer matches), with the module's
  `PIPELINE_SOURCE` monkeypatched to it, produced
  `AssertionError: companion is supposed to FAIL here` / `assert []` —
  the companion fails loudly exactly where the old in-lock `pytest.fail`
  was swallowed as XFAIL (the review's own empirical finding).

### WR-02: Makefile hardcodes `~/.local/bin/uv`

**Files modified:** `Makefile`
**Commit:** `bc4eae4`
**What changed:** `Makefile:22` — `UV := ~/.local/bin/uv` → `UV ?= uv`
(PATH-lookup default; environment/command-line overridable via
`make UV=/path/to/uv`), with a comment naming the CI threat
(setup-uv/brew/pipx installs live outside `~/.local/bin`).

**Verified:**
- `make test-fast` via PATH uv → `133 passed, 1 deselected, 5 xfailed`.
- `UV=~/.local/bin/uv make test-fast` (override honored) → same, green.
- `make UV=/nonexistent/uv test-fast` → still fails loudly with
  `not found ... Error 127` (an explicit bad override is the operator's
  choice; the point of the fix is that the DEFAULT no longer encodes one
  user's install layout).

### WR-03: Schema-validation glob buckets have no non-emptiness guard

**Files modified:** `tests/test_schemas.py`
**Commit:** `7674ff0`
**What changed:** Added `EXPECTED_BUCKET_SIZES` (42/47/4/1) and the canary
`test_schema_bucket_counts_are_pinned` (`tests/test_schemas.py:100-127`)
— asserts every bucket is non-empty AND exactly its pinned count, so a
missing/partial data tree or an accidental bucket-list edit fails loudly
instead of parametrizing to zero vacuous items.

**Verified:**
- `pytest tests/test_schemas.py::test_schema_bucket_counts_are_pinned` →
  `1 passed` against the real tree (42/47/4/1 confirmed live before writing
  the pins).
- Scratch empty-tree simulation (copy of the test file under /tmp so
  `REPO` resolves to a tree with no `dnallm-mark/data`, deleted after):
  `AssertionError: model_performance: no committed data files found for
  schema model_performance.json — the dnallm-mark/data tree is missing or
  partial; this bucket's parametrized validation is vacuous` → `1 failed`.

### WR-04: Determinism run-to-run check masks a "run 2 wrote fewer files" flake

**Files modified:** `tests/test_determinism.py`
**Commit:** `ca3e3cf`
**What changed:** `_run_chain_once` (`tests/test_determinism.py:107`) now
removes ALL stale chain outputs at the top of every run —
`shutil.rmtree(work / "task_performance")` (line 127), every
`work.glob("models_comparison*.json")` unlinked (128-129), and the
generated `tasks.json` unlinked (130) — so each run must write its full
output set; a clean-exit run that omits a file can no longer inherit run
1's copy of it. Docstring updated to state the guarantee honestly. The
copied `model_performance/` inputs are untouched.

**Verified:**
- Real test: `pytest tests/test_determinism.py -q` → `1 passed in 0.53s`
  (and again inside the final `make test` gate).
- "Generator writes nothing" scratch simulation (in /tmp, deleted after),
  both runs over real inputs producing the full 99-file output set
  (47 pivot + 4 comparison + 1 tasks.json + 47 JS-visible copies), then
  every chain step swapped for clean-exit no-ops:
  - pre-fix helper replica: no-op run 2 compared byte-EQUAL via leftovers
    (`assert snap2 == snap1` PASSED) — the mask, reproduced;
  - post-fix helper: `assert snap2 == snap1` FAILED with
    `assert {} == {'dnallm-mark/...}` — snapshot 2 is empty, so the real
    test's run-to-run compare (`snapshot1 != snapshot2` → `pytest.fail`)
    and its file-set check both go red. Detection restored.

### WR-05: Thread pin uses `setdefault` while the test hard-asserts "1"

**Files modified:** `tests/conftest.py`
**Commit:** `20892f4`
**What changed:** `tests/conftest.py:19-36` — `os.environ.setdefault(_var, "1")`
→ `os.environ[_var] = "1"` (force-assign) for all five thread vars, with a
comment documenting why force-assign is safe: conftest runs before any
test-module numpy import, so the assignment is effective for this process
and inherited by every subprocess the suite spawns (the determinism lane);
the pins only affect this test process's BLAS/OpenMP pools, and
single-threaded reductions are the point of TEST-02 — an env-preset
nonzero count is not accepted. The existing
`test_thread_pinning_is_active_at_test_time` in test_aggregation.py is
unchanged and stays as the runtime verification.

**Verified:**
- `OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 uv run
  --group dev pytest -q` → `136 passed, 5 xfailed` (this exact scenario
  was `1 failed` before the fix, per the review's live probe).
- Plain run green: `pytest tests/test_aggregation.py -q` → `30 passed`.
- The orchestrator-mandated exact command
  `OMP_NUM_THREADS=4 ~/.local/bin/uv run --group dev pytest -q` rerun as a
  final gate → `136 passed, 5 xfailed`.

### IN-02: Closed enums duplicated across schema files; self-check covers only one

**Files modified:** `tests/test_schemas.py` (check only — schemas/ NOT touched)
**Commit:** `cdcd16a`
**What changed:** Added `ENUM_LOCATIONS` (`tests/test_schemas.py:165`, the
per-file path to the dataset-vocabulary properties in
model_performance/task_performance/tasks_index), the observed-data
collector `_observed_dataset_field_values()` (line 173), and
`test_dataset_enums_match_committed_data_across_all_schemas` (line 202):
for each of species/type/metric in each of the three enum-carrying
schemas, schema enum == observed committed-data set == the
model_performance reference copy (the same ≡ discipline the metric-only
check applied — that check is kept unchanged). The fourth schema is
covered by an explicit boundary assertion: models_comparison model-card
species/type are OPEN strings by design (D-02) and must stay enum-free —
closing them must be a deliberate act that widens this check. Schemas stay
self-contained (no dedup, no cross-file $ref) per the recorded RESEARCH Q1
decision — only the CHECK widened.

**Verified:**
- `pytest tests/test_schemas.py -q` → `98 passed`.
- Scratch enum-edit: temporarily added `"Viruses"` to the species enum in
  `schemas/tasks_index.json`, ran the new test →
  `AssertionError: tasks_index.species: schema enum ['Animals', 'Microbe',
  'Plants', 'Viruses'] != observed data ['Animals', 'Microbe', 'Plants']
  and/or != model_performance copy [...]` → `1 failed`; reverted via
  `git checkout -- schemas/tasks_index.json` (tree confirmed clean) and the
  test passes again. Observed value sets were probed live beforehand and
  are identical across all three data forms, exactly equal to the enums —
  the ≡ assertions are honest, not aspirational.

### IN-04: `node` is an undeclared hard dependency of the JS test lane

**Files modified:** `Makefile`
**Commit:** `03c0f01`
**What changed:** New `check-node` target (`Makefile:39`, silent when node
is present) as a prerequisite of `test` (`Makefile:42`). When node is
missing it prints exactly one actionable line — `node >=18 required for
the JS test lane — install Node or run make test-fast` — instead of the
raw `FileNotFoundError`/`sh: node: not found`. `.PHONY` updated. No
package.json, no npm, per the fix directive. (`test_golden.py`'s own node
usage is inside the pytest lane the review noted; the orchestrator scoped
this fix to the Makefile guard only.)

**Verified:**
- `make check-node` with node present → silent, exit 0.
- Simulation with `PATH` pointing at a node-free dir (this machine has
  node symlinked into /usr/bin, so an empty PATH was not sufficient —
  noted for reproducibility): `env PATH=/tmp/nodeless_bin make check-node`
  → prints the one-line message, make exits nonzero; the unguarded recipe
  line under the same PATH dies with `/bin/sh: 1: node: not found`
  (exit 127) — the before/after failure-mode contrast.
- Normal path unchanged: final `make test` ran guard → pytest →
  `node --test tests/js/` end to end, exit 0.

## Deferred Issues

### IN-01: Generator fallback values ('Unknown'/'unknown'/'accuracy') vs tasks_index closed enums

**File:** `schemas/tasks_index.json:31-35` vs `scripts/generate-tasks-index.js:49-53`
**Reason:** A genuine fix means changing generator behavior
(`scripts/generate-tasks-index.js` defensive projections) — production
code, forbidden this phase by D-04 (the same constraint the review itself
acknowledges by routing IN-01 elsewhere). Today the tension is already
loud where it matters: any fallback value that reached a regenerated
`tasks.json` fails `test_schemas` at commit time (closed enums reject
`'Unknown'`/`'unknown'`/`'accuracy'`), and the committed index is fallback-
free. Deferred to the Phase 4/5 review alongside the generator work.
**Original issue:** the schema closes species/type/metric but the
generator's defensive projections can emit values outside those enums; the
JS test pins the `'Unknown'` fallback.

### IN-03: `METRIC_KEY_MAP` in test_aggregation is a manual mirror of a production local

**File:** `tests/test_aggregation.py:44-54` mirroring `script/summarize_comparison.py:295-305`
**Reason:** The mirror is verified faithful today (key-by-key, per the
review). The real fix — extracting `metric_key_map` out of
`summarize_comparison.main()` so the test imports it instead of copying it
— is a production-code refactor in `script/`, forbidden this phase by
D-04. Deferred to Phase 4 together with the WR-03(P1)/IN-01(P1)
comparator work where the extraction lands naturally.
**Original issue:** a production edit to the map can silently diverge the
fixture loader from real extraction; the drift channel is real but
acceptable under D-04.

---

_Fixed: 2026-10-09T04:59:21Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
