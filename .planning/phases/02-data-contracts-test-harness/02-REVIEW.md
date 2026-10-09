---
phase: 02-data-contracts-test-harness
reviewed: 2026-10-09T04:28:18Z
depth: standard
files_reviewed: 27
files_reviewed_list:
  - .gitignore
  - Makefile
  - README.md
  - pyproject.toml
  - schemas/model_performance.json
  - schemas/models_comparison.json
  - schemas/task_performance.json
  - schemas/tasks_index.json
  - tests/conftest.py
  - tests/js/generate-tasks-index.test.js
  - tests/test_aggregation.py
  - tests/test_determinism.py
  - tests/test_golden.py
  - tests/test_known_defects.py
  - tests/test_pivot.py
  - tests/test_schemas.py
  - tests/fixtures/synthetic_models/fake-alpha_performance.json
  - tests/fixtures/synthetic_models/fake-beta_performance.json
  - tests/fixtures/synthetic_models/fake-gamma_performance.json
  - tests/fixtures/golden/models_comparison.json
  - tests/fixtures/golden/models_comparison_animal.json
  - tests/fixtures/golden/models_comparison_plant.json
  - tests/fixtures/golden/models_comparison_microbe.json
  - tests/fixtures/golden/tasks.json
  - uv.lock
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
  status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-10-09T04:28:18Z
**Depth:** standard
**Files Reviewed:** 27
**Status:** issues_found

## Summary

Phase 2 delivers the data-contract schemas, the synthetic fixture corpus, the
Python/JS test harness, the real-tree determinism regression, and the three
`xfail(strict=True)` defect locks. The core contracts hold under adversarial
probing: all four schemas are genuinely strict (8/8 mutation probes against a
live committed file rejected — extra keys, `null`/`"0"` metrics, enum drift,
dropped required keys, type drift); the AUD-01 AST anchor is verified unique
against the actual pipeline source (single match, line 1227,
`model_row.get("species", ...)`, so the lock fails on the real defect, not an
import error); WR-02's silence was traced through `baseline/compare.py:walk()`
(`True == 1` exits the bool branch with no diff); WR-03's pass-through matches
`get_float`'s real code path. The full suite runs green live
(133 passed + 5 xfailed, JS lane 2/2, ruff clean), and the determinism test
left `dnallm-mark/data/` untouched (verified via `git status --porcelain`
after the run).

No Critical findings. Five Warnings: the most substantive is that the AUD-01
lock's "honest failure" guard is defeated by its own `xfail` marker
(empirically confirmed: `pytest.fail` inside `xfail(strict=True)` reports
XFAIL with exit 0, contradicting the docstring's guarantee). The others are
test-robustness and portability gaps (hardcoded uv path, vacuous-pass schema
buckets, a determinism blind spot, environment-sensitive thread-pinning
assertion).

Per the review brief, the intentionally-open items (WR-02/WR-03/AUD-01 defect
behaviors themselves — locked as xfail by design; WR-01/IN-01/IN-02 routed
elsewhere) were not re-flagged. The Zenodo preview-token link in README.md is
pre-existing and documented as intentional (D-08, `.gitleaks.toml` allowlist,
Phase 6 release item) — noted, not flagged.

## Warnings

### WR-01: AUD-01 lock's `pytest.fail` honesty guard is swallowed by its own `xfail` marker

**File:** `tests/test_known_defects.py:118` (docstring claim at lines 75-77)
**Issue:** The docstring states: "If the site disappears entirely, the
trailing `pytest.fail` makes the test fail honestly rather than lock nothing."
This is false. `@pytest.mark.xfail(strict=True)` (line 54) intercepts *all*
failures inside the test body, including explicit `pytest.fail()` — verified
empirically with the repo's own pytest 9.1.1: a `pytest.fail("...")` inside an
`xfail(strict=True)` test reports `1 xfailed` with exit code 0. `strict=True`
only converts XPASS into a failure; it never converts XFAIL into one. So if
Phase 3 moves or restructures the construction site (the exact scenario the
guard exists for, per the docstring's own "Phase 3 caution"), the lock
silently degrades to locking nothing while the suite stays green — a false
lock, the precise failure mode this plan set out to prevent.

**Fix:** Split findability from the defect lock so the guard lives outside the
marker:

```python
def _find_dataset_species_expr():
    """Return the AST species expr at the construction site, or None."""
    tree = ast.parse(PIPELINE_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        # ... existing matcher ...
        if isinstance(ds, ast.Dict):
            return _species_expr(ds)   # may be None
    return None


def test_pipeline_construction_site_anchor_findable():
    """Unmarked companion: goes RED (not XFAIL) when Phase 3 moves the site."""
    assert _find_dataset_species_expr() is not None, (
        "construction site not found — pipeline structure changed; "
        "update the AUD-01 anchor deliberately"
    )


@pytest.mark.xfail(strict=True, reason="AUD-01-P0 species-as-dataset — Phase 4 fix")
def test_producer_writes_dataset_species_not_model_organism():
    sp = _find_dataset_species_expr()
    assert sp is not None  # companion test already went red if None
    assert _is_row_get(sp), "..."
```

This keeps strict XPASS semantics (fix must land with marker removal in the
same commit) while making site-disappearance a loud failure.

### WR-02: Makefile hardcodes `~/.local/bin/uv` — all targets break wherever uv lives elsewhere

**File:** `Makefile:19`
**Issue:** `UV := ~/.local/bin/uv` is a hardcoded user-layout path. Verified:
with uv resolvable on `PATH` but not at `~/.local/bin`, `make test-fast` dies
with `/nonexistent/.local/bin/uv: not found ... Error 127`. This affects every
common non-default install — GitHub Actions `astral-sh/setup-uv` (installs
into the tool cache and prepends PATH), Homebrew (`/opt/homebrew/bin/uv`),
pipx, and corporate images. Since this milestone's stated goal is CI
feasibility over exactly these make targets, the hardcode is on the critical
path to Phase 2's downstream consumers. (`:=` also makes it non-overridable
from the environment.)

**Fix:**

```make
UV ?= uv   # PATH lookup; overridable via `make UV=/path/to/uv`
```

### WR-03: Schema-validation buckets built from glob with no non-emptiness guard — silent vacuous pass

**File:** `tests/test_schemas.py:25-50, 66-69`
**Issue:** `SCHEMA_FILES` collects `sorted((DATA / "model_performance").glob("*.json"))`
and the `task_performance` equivalent at module import. If the data tree is
absent or partial (shallow/sparse checkout, export tarball, a renamed
directory), the glob returns an empty list and the parametrize comprehension
produces **zero pytest items for that bucket** — the 42-file and 47-file
validation silently vanishes from the suite while `make test-fast` stays
green. The literal-path buckets (`models_comparison*`, `tasks.json`) would
fail loudly on missing files, but the two largest buckets — the actual
producer schema and its pivot — pass vacuously. Nothing asserts the expected
42/47/4/1 counts.

**Fix:** Add a canary test pinning the bucket sizes:

```python
def test_schema_buckets_are_nonempty():
    """Guard against vacuous passes when the committed data tree is missing."""
    expected = {"model_performance": 42, "task_performance": 47,
                "models_comparison": 4, "tasks_index": 1}
    for name, (path, paths) in SCHEMA_FILES.items():
        assert paths, f"{name}: no files found under {path.parent} — vacuous validation"
        assert len(paths) == expected[name], (
            f"{name}: {len(paths)} files, expected {expected[name]} "
            "(update this pin deliberately when the corpus grows)"
        )
```

### WR-04: Determinism run-to-run check masks a "run 2 wrote fewer files" flake

**File:** `tests/test_determinism.py:107-133` (claim at 110-112)
**Issue:** `_run_chain_once` never clears `work/task_performance/` or the
`work/models_comparison*.json` files between runs — only the JS-visible copy
is rebuilt (`shutil.rmtree(js_tasks, ...)` at line 129). Both Python steps
overwrite in place, so if run 2 were to omit an output file (the exact class
of nondeterminism this test exists to catch), run 1's leftover copy of that
file remains in `work/task_performance/`, enters `snapshot2` with run-1 bytes,
and all three checks pass: snapshots compare equal, the file set matches
committed, and the bytes match committed. The flake is fully masked. The
docstring's "no stale run-1 files can linger" is true only of the JS copy,
not of the Python outputs the determinism claim is about. (Content
nondeterminism in files written by both runs is still caught; the blind spot
is file-set shrinkage with a clean exit.)

**Fix:** Clean the Python outputs at the top of `_run_chain_once`:

```python
def _run_chain_once(work):
    # Remove run-1 outputs so a run-2 file-set shrink cannot be masked by
    # stale leftovers (inputs under model_performance/ are preserved).
    shutil.rmtree(work / "task_performance", ignore_errors=True)
    for stale in work.glob("models_comparison*.json"):
        stale.unlink()
    _run_checked([sys.executable, PIVOT_SCRIPT], cwd=work)
    ...
```

### WR-05: Thread-pinning pin uses `setdefault` while the test hard-asserts `"1"` — suite goes red on machines that preset thread vars

**File:** `tests/conftest.py:19-26` with `tests/test_aggregation.py:309-313`
**Issue:** conftest applies `os.environ.setdefault(_var, "1")`, so any
environment that already exports `OMP_NUM_THREADS` (HPC modules, some CI
images, developer shells — common in this project's GPU-adjacent domain)
keeps its value, the pin is silently not applied, and
`test_thread_pinning_is_active_at_test_time` then fails with a bare
`AssertionError: - 1 + 4` (verified live: `OMP_NUM_THREADS=4 pytest ...` → 1
failed). The failure is "honest" but is a false alarm about reproducibility
(an env-pinned stable thread count is itself deterministic), and the message
gives the user no path forward. Note the env-sensitivity only bites the
in-process numpy lane; the subprocess lane in test_determinism inherits
whatever was decided here, so the two lanes can disagree about pinning.

**Fix:** Either force the pin (conftest runs before any numpy import, so
assignment is effective): `os.environ[_var] = "1"`, or keep `setdefault` and
make the assertion tolerant with guidance:

```python
def test_thread_pinning_is_active_at_test_time():
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        assert os.environ.get(var) == "1", (
            f"{var}={os.environ.get(var)!r} — unset it or export {var}=1; "
            "conftest's setdefault will not override a preset value"
        )
```

Forcing is preferable given the determinism goal of TEST-02.

## Info

### IN-01: Generator fallback values violate the tasks_index closed enums the same phase asserts

**File:** `schemas/tasks_index.json:31-35` vs `scripts/generate-tasks-index.js:49-53` (pinned by `tests/js/generate-tasks-index.test.js:89`)
**Issue:** The schema closes `species` to `["Animals","Plants","Microbe"]`,
`type` to four task types, and `metric` to four values, but the generator's
defensive projections emit `'Unknown'` / `'unknown'` / `'accuracy'` / `0`
when a task file lacks those info fields — and the JS test explicitly pins
the `'Unknown'` fallback. Any real occurrence of a fallback in regenerated
`tasks.json` will fail `test_schemas` at commit time (loud, which is the
right failure mode), but the schema `$comment` documents only the empty-array
case, not that fallback outputs are outside the contract. Document the
tension in the `$comment` (or assert in the JS test that fallback values are
confined to synthetic fixtures).

### IN-02: Closed enums duplicated across three schema files; self-check covers only one

**File:** `schemas/model_performance.json:67`, `schemas/task_performance.json:33`, `schemas/tasks_index.json:31-35`; check at `tests/test_schemas.py:96-119`
**Issue:** `test_metric_enum_matches_committed_data` verifies the
`model_performance` metric enum against committed data, but the identical
enum copies in `task_performance.json` and `tasks_index.json` (and the
species/type enums everywhere) have no cross-file consistency check — one can
drift from the others with all suites green. Add a cheap equality test:

```python
def test_closed_enums_are_identical_across_schemas(validators):
    for other in ("task_performance", "tasks_index"):
        assert _metric_enum(validators[other]) == _metric_enum(validators["model_performance"])
```

### IN-03: `METRIC_KEY_MAP` in test_aggregation is a manual mirror of a production local

**File:** `tests/test_aggregation.py:44-54` mirroring `script/summarize_comparison.py:295-305`
**Issue:** The mirror is faithful today (verified key-by-key), but
`metric_key_map` is a local inside `main()` and unreachable from the test, so
a production edit renames or adds a mapping silently diverging the fixture
loader from real extraction (D-04 forbids the production refactor that would
expose it — acceptable, but the drift channel is real). Mitigate with a
source-contract assertion (same AST technique as the AUD-01 lock) or a
pointed comment naming the mirrored lines.

### IN-04: `node` is an undeclared hard dependency of `make test-fast` with a raw traceback on absence

**File:** `tests/test_golden.py:87` (also `tests/test_determinism.py:124,131`); comment at `Makefile:12-13`
**Issue:** `test_golden.py` is not `slow`-marked and spawns `node`; on a
node-less machine `make test-fast` fails with `FileNotFoundError` on
`subprocess.run(["node", ...])` rather than a clean skip, despite the
Makefile comment framing the JS dependency as belonging to the full lane.
Node 18+ is a documented README prerequisite, so this is minor; a
`pytest.mark.skipif(shutil.which("node") is None, reason="node not on PATH")`
would make the failure mode legible.

---

_Reviewed: 2026-10-09T04:28:18Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

_Verification evidence: `make test-fast` (132 passed, 1 deselected), `make test` (133 passed, 5 xfailed; JS 2/2), `make lint` clean; `git status --porcelain -- dnallm-mark/data/` empty after full suite; 8/8 schema mutation probes rejected; AUD-01 AST matcher unique (1 match, line 1227); `pytest.fail`-inside-`xfail(strict=True)` probe → `1 xfailed`, exit 0; `OMP_NUM_THREADS=4` probe → pinning test fails; `PATH`-only uv probe → `Error 127`._
