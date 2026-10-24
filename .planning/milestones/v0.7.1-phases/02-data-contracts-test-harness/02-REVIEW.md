---
phase: 02-data-contracts-test-harness
reviewed: 2026-10-09T05:22:56Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - Makefile
  - tests/test_golden.py
  - tests/test_known_defects.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 02: Code Review Report (Fix-Round Delta 3 — Convergence)

**Reviewed:** 2026-10-09T05:22:56Z
**Depth:** standard
**Files Reviewed:** 3 (Makefile, tests/test_golden.py, tests/test_known_defects.py)
**Base:** diff since 20db676 (fix round for WR-06, WR-07, IN-05)
**Status:** clean

## Summary

Third delta over the Phase 2 fix rounds. The three changed files implement
exactly the prior delta's three prescriptions — WR-06 (module-level
`pytestmark` skipif on missing node in `tests/test_golden.py` plus a truthful
`check-node` message), WR-07 (`data: check-node` prerequisite), and IN-05
(companion assert for `"species"` key presence at the matched construction
site). Each fix was verified against the sources and behavior it references,
including live simulation of the node-less machine and AST mutation testing of
the IN-05 guard. All three implement their intent correctly; no new findings.
Finding-ID sequence stays at WR-07/IN-05 — nothing new to number.

All reviewed files meet quality standards. No issues found.

### Fix verification (all independently confirmed, not trusted from green runs)

| Fix | Verdict | Evidence |
|-----|---------|----------|
| WR-06 skipif + truthful message | Correct | `pytestmark = pytest.mark.skipif(shutil.which("node") is None, ...)` at `tests/test_golden.py:43-46`; `shutil` imported (line 29); all three module tests consume `chain_result` (whose fixture shells out to node at line 97), so module-wide scope is exact — no node-free test is over-skipped. **Live node-less simulation** (PATH stripped of node): `pytest tests/test_golden.py` → 3 SKIPPED with reason; full fast lane `pytest tests -m "not slow"` → `132 passed, 3 skipped, 1 deselected, 5 xfailed`, zero errors — the message's "fast lane skips node-dependent tests when node is absent" claim is now empirically true (goldens skip via skipif; the only other pytest-lane node call, `tests/test_determinism.py:142`, is `@pytest.mark.slow`-marked and deselected by `-m "not slow"`, verified). |
| WR-07 `data: check-node` + widened message | Correct | `Makefile:28` — `make -n data` shows `check-node` recipe running before the three data recipe lines; `check-node` is in `.PHONY` (line 17), prerequisite ordering is correct under parallel make. **Negative path exercised live**: `make check-node` with node absent from PATH prints the exact new message and exits non-zero. The message's enumeration (JS test lane, tasks.json goldens, `make data`) matches the actual node-dependent surfaces; the `test-fast` escape hatch is real (see WR-06 row). |
| IN-05 species key-presence assert | Correct | `tests/test_known_defects.py:121-127` — `sites[0]` indexing is safe (guarded by the preceding non-empty and uniqueness asserts); `ast.Dict.keys` can contain `None` entries for `**`-unpacking and the `isinstance(k, ast.Constant)` guard tolerates that without crashing. **AST-verified against live source**: exactly one anchor site at `pipeline/dnallmmark_pipeline.py` (~1227) whose `"dataset"` sub-dict carries `"species": model_row.get(...)`. **Mutation-verified** (read-only, over a /tmp copy): with the species key moved out of the sub-dict, the companion's key-presence verdict flips to False (RED outside the marker) while the lock alone would still report silent XFAIL — the exact WR-01 degradation class IN-05 targeted; with the hypothetical Phase 4 fix (`row.get`), the companion stays green and the lock XPASSes into the designed strict failure. No false-positive channel: the legitimate fix keeps the `"species"` key, so the companion never blocks it. |

### Suite state independently reproduced

- `make test-fast` → `135 passed, 1 deselected, 5 xfailed in 0.78s`
- `make test` → `136 passed, 5 xfailed` + `node --test tests/js/` 2 pass / 0 fail
- `make lint` → `ruff check tests/` all checks passed
- Simulated node-less fast lane → green (see WR-06 row)
- `git status --porcelain` over `Makefile`, `tests/`, `dnallm-mark/data/` clean
  after review activity (the determinism test's own committed-tree check also
  passed inside `make test`)

### Residual observation (not a finding — pre-existing, accepted semantics)

The `node >=18` texts (check-node message, skipif reason) are enforced as
presence-only checks (`command -v node` / `shutil.which("node")`), consistent
with the prior round's accepted prescription shape and the documented project
Node floor. On an ancient-node machine the guard passes and the JS lane then
fails loudly (`node --test` flag error) — a loud, actionable failure, not the
silent class the guards target. No action required this phase.

---

_Reviewed: 2026-10-09T05:22:56Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
