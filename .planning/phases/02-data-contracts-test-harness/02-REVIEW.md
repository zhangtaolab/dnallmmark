---
phase: 02-data-contracts-test-harness
reviewed: 2026-10-09T05:08:13Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - Makefile
  - tests/conftest.py
  - tests/test_determinism.py
  - tests/test_known_defects.py
  - tests/test_schemas.py
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 02: Code Review Report (Fix-Round Delta)

**Reviewed:** 2026-10-09T05:08:13Z
**Depth:** standard
**Files Reviewed:** 5 (Makefile, tests/conftest.py, tests/test_determinism.py, tests/test_known_defects.py, tests/test_schemas.py)
**Base:** diff since 61308cc (fix round for WR-01..WR-05, IN-02, IN-04)
**Status:** issues_found

## Summary

Incremental re-review of the Phase 2 fix round. All seven applied fixes were
re-verified independently against the sources they reference — every fix
implements its intent correctly; two of them (both under IN-04, the node
dependency guard) leave the guard's goal only half-achieved, producing the two
warnings below. Finding IDs continue the prior review's sequence (WR-06+,
IN-05) so recorded dispositions in 02-REVIEW-DISPOSITION.md are not displaced.

### Fix verification (all independently confirmed)

| Fix | Verdict | Evidence |
|-----|---------|----------|
| WR-01 unmarked anchor companion | Correct | AST walk over `pipeline/dnallmmark_pipeline.py` matches exactly 1 site (line 1227); companion is unmarked, so anchor loss goes red outside the `xfail`; lock's `sites[0]` selection is safe under the companion's uniqueness assert. One hardening gap remains (IN-05). |
| WR-02 `UV ?= uv` | Correct | Overridable PATH-lookup default; `command -v uv` resolves on this machine; comment documents the CI threat. |
| WR-03 bucket-count canary | Correct | Pins verified live: 42 model_performance, 47 task_performance, 4 comparison, 1 tasks.json globbed under `dnallm-mark/data/`. Canary asserts non-empty AND exact count, closing the vacuous-pass channel. |
| WR-04 inter-run cleanup | Correct | `_run_chain_once` removes `task_performance/`, all `models_comparison*.json` (verified: summarize writes exactly those names at CWD root), and the generated `tasks.json` before each run — a run-2 file-set shrink can no longer inherit run-1 bytes. Inputs under `model_performance/` untouched. |
| WR-05 force-assign pinning | Correct | Assignment at conftest import precedes every test-module numpy import; `test_aggregation.py:309-313` (`== "1"` hard assert) now cannot go red from a hostile preset. |
| IN-02 widened enum self-check | Correct | All three `ENUM_LOCATIONS` paths resolve; schema enums for metric/species/type are identical across the three schemas and exactly equal the observed value sets in all three data forms (verified by independent extraction); models_comparison model-card species/type carry no `enum`, matching the boundary assertion. |
| IN-04 check-node guard | Partial | Guard exists and is wired to `test` only — see WR-06/WR-07. |

Suite state independently reproduced: `uv run --group dev pytest -q` →
`136 passed, 5 xfailed in 1.39s`; `node --test tests/js/` → 2 pass / 0 fail;
`git status --porcelain` over `dnallm-mark/data/`, `tests/`, `Makefile`,
`schemas/` clean. The 5 xfails are the three defect locks (AUD-01 anchor,
bool/int comparator silence at `baseline/compare.py:74`, non-finite
`get_float` pass-through) — each lock's failure semantics re-verified against
source, not just trusted from the green run.

## Critical Issues

None.

## Warnings

### WR-06: check-node's remediation message points to a node-free lane that does not exist — `make test-fast` hard-requires node via `test_golden.py`

**File:** `Makefile:40` (and `tests/test_golden.py:87`)
**Issue:** The guard's failure message is `node >=18 required for the JS test
lane — install Node or run make test-fast`. But `make test-fast` runs
`pytest -m "not slow"`, which collects all three `tests/test_golden.py` tests
(verified: none is slow-marked; `--collect-only -m "not slow"` shows all
three). Their shared `chain_result` fixture invokes
`subprocess.run(["node", str(inner / "gen.js")], check=True, ...)` at
`tests/test_golden.py:87`. On a node-less machine the operator follows the
message's advice and lands on exactly the raw-tracepoint failure mode IN-04
was filed against: `FileNotFoundError` inside pytest, 3 test errors. The
escape hatch the message promises is broken, so the guard converts one
confusing failure into a wrong direction plus the same failure.
**Fix:** Correct the message AND make it true. Minimal: guard the golden lane
on node presence —

```python
# tests/test_golden.py (module level, after imports)
pytestmark = pytest.mark.skipif(
    shutil.which("node") is None,
    reason="tasks.json golden requires the Node index generator",
)
```

— and change the Makefile message to `node >=18 required (JS test lane and
the tasks.json goldens) — install Node` (drop the false alternative), or
document `make test-fast` as node-free only once the skipif lands.

### WR-07: `make data` invokes node with no check-node guard — the raw exit-127 failure IN-04 fixed for `test` persists in the other node-dependent target

**File:** `Makefile:31`
**Issue:** The fix round added `check-node` as a prerequisite of `test` only,
but the `data` target's third recipe line runs
`node scripts/generate-tasks-index.js` directly. On a node-less machine
`make data` dies with `/bin/sh: node: not found` and make `Error 127` — the
identical unguarded, non-actionable failure class IN-04 was filed against,
one target over. (The slow determinism lane also shells out to node at
`tests/test_determinism.py:142`, but it is excluded from `make test-fast` and
covered once WR-06's message stops advertising a node-free lane; `data` has
no such exclusion.)
**Fix:** Promote the guard to cover both node-dependent targets:

```make
data: check-node
	cd $(DATA_DIR) && $(UV) run --group data python ../../script/get_task_performance.py
	...
```

(the message in `check-node` should then say "test/data lanes", per WR-06).

## Info

### IN-05: AUD-01 companion guards findability and uniqueness but not key-presence — one silent-degradation path remains open

**File:** `tests/test_known_defects.py:93-114`
**Issue:** The companion asserts the anchor matches ≥1 site and exactly 1
site. If a future pipeline restructure keeps a unique dataset-entry
construction site but moves or renames the `"species"` key out of its
`"dataset"` sub-dict, the lock's `next(...)` yields `None`, `is_row_get` is
`False`, the assert fails *inside* `xfail(strict=True)` — reported XFAIL,
suite green — while the companion stays green too. The lock is then vacuous
and nothing is red, which is the exact silent-degradation class WR-01 was
filed against (narrower trigger, same failure shape).
**Fix:** One extra assert in the companion (outside the marker), e.g.:

```python
assert any(
    isinstance(k, ast.Constant) and k.value == "species"
    for k in sites[0].keys
), "matched construction site no longer contains a 'species' key — update the anchor deliberately"
```

---

_Reviewed: 2026-10-09T05:08:13Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
