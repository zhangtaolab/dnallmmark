---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
reviewed: 2026-10-15T16:14:13Z
depth: quick
files_reviewed: 4
files_reviewed_list:
  - pipeline/env_smoke.py
  - tests/test_env_smoke_bytes.py
  - tests/tui/test_pilot_env_check.py
  - tui/screens/env_check.py
findings:
  critical: 0
  warning: 4
  info: 1
  total: 5
status: issues_found
---

# Phase 07: Code Review Report (scoped incremental — commit 16e21b5)

**Reviewed:** 2026-10-15T16:14:13Z
**Depth:** quick
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Scoped incremental review of commit 16e21b5 ("fix(08-08): WR-01 — fail-closed
env_smoke registry reads + the guarded env-screen worker"), the complete
four-file diff of `16e21b5^..16e21b5`. The commit does what it claims on its
primary paths: corrupt/absent/non-UTF-8 registries now convert into one named
ok=False `CheckResult` (verified by reading `_read_registry` and the tests),
the per-kernel and `kernels()`-enumeration guards in the TUI worker are
correctly shaped, run-id staleness dropping is preserved, and the two test
fixes are themselves correct — the `"Expecting property name"` assertion was
empirically verified against real `json` behavior (`json.loads('{ not json')`
raises "Expecting property name enclosed in double quotes", so the pre-commit
assertion `"Expecting value"` was wrong and this commit fixes it).

However, the fail-closed guard is **incomplete for its own stated contract**,
and the diff introduces two new reachable states with operator-facing
defects. All findings below were verified by *executing* the kernels against
synthetic corrupt registries, not by reading alone. Note: the on-disk files
also carry one later cosmetic commit (ec1447d, strings-import consolidation to
`S.`-qualified names) that does not change any logic reviewed here.

No security findings: no secrets, no `eval`/`exec`, no injection surface; all
paths come from repo-local registries and maintainer-run CLI/TUI contexts.

## Critical Issues

None. The E2' gate's fail direction is preserved in every scenario found
(exit code is non-zero even on the traceback path below).

## Warnings

### WR-01: `_read_registry` still tracebacks on valid-JSON-but-non-dict registries — the fail-closed contract is incomplete

**File:** `pipeline/env_smoke.py:458-469` (crash sites `502-504` and `565-567`)
**Issue:** `_read_registry` catches only `(OSError, json.JSONDecodeError,
UnicodeDecodeError)`. A registry that is *readable, valid JSON, but the wrong
top-level shape* (a list, string, number, or `null` — a plausible hand-edit or
bad-merge state of a "broken checkout") parses successfully and then crashes
with an uncaught `TypeError` in the kernels. Empirically reproduced:

- `[{"Model_path": "models/a/b"}]` → `TypeError: list indices must be
  integers or slices, not dict` (in `sorted(models_info)` at line 502)
- `["x"]` → `TypeError: list indices must be integers or slices, not str`
- `null` → `TypeError: 'NoneType' object is not iterable`

This violates the contract this very commit establishes ("the E2' gate exits 1
deterministically on exactly the broken-checkout state it exists to diagnose,
**never a traceback**"): the traceback goes to stderr, the kernel renders no
`FAIL:` line, and the `=== SMOKE RESULT: ... ===` trailer never prints — the
greppable contract the golden suite exists to protect is broken. The gate
still exits non-zero (uncaught exception), so this is Warning, not Critical.
The TUI path is incidentally safe (the per-kernel `except Exception` guard
converts the `TypeError` into a degraded row), but the CLI — the E2' dual-gate
half — is not.
**Fix:** Validate the top-level shape inside `_read_registry` so the single
reader owns it:

```python
try:
    with open(path, "r", encoding="utf-8") as fh:
        parsed = json.load(fh)
except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
    return None, _registry_read_failure(path, kernel_name, exc)
if not isinstance(parsed, dict):
    return None, CheckResult(
        name=kernel_name, ok=False,
        lines=(f"FAIL: read registry {path} — not a JSON object "
               f"(top-level {type(parsed).__name__})",),
    )
return parsed, None
```

and extend the new test to cover a top-level list and `null` for both kernels.

### WR-02: empty-string `Model_path` counts as PRESENT (false gate PASS) — asymmetric with the sibling kernel fixed in the same commit

**File:** `pipeline/env_smoke.py:504-506` (contrast `567-570`)
**Issue:** `check_dataset_dirs` gained `if not isinstance(value, str) or not
value:` — treating an empty `Dataset_path` as missing. `check_model_dirs`,
which the docstring says "mirrors `check_dataset_dirs` exactly", did NOT get
the `not value` guard. Empirically reproduced: a registry
`{"m1": {"Model_path": ""}}` renders `PASS: all 1 registry model dir(s)
present on disk` — because `base + ""` is the base directory itself, which
exists. An empty path is a broken entry per the commit's own docstring
("a broken entry shape ... counts as MISSING — cannot-verify reads as
missing"), yet the model kernel emits a false all-present PASS for it. The
two kernels now disagree on the identical broken-entry shape.
**Fix:**

```python
value = entry.get("Model_path") if isinstance(entry, dict) else None
if not isinstance(value, str) or not value \
        or not Path(base + value).is_dir():
    missing.append(name)
```

### WR-03: `run_full_check` persist/completion tail is unguarded — a raising `persist` strands the run with no verdict and no last-check line

**File:** `tui/screens/env_check.py:459-467`
**Issue:** The WR-01 guards cover exactly two of the three raise sites in the
worker. `checked_at = self._service.persist(results)` (line 464) is outside
both guards. The real backend's persist does an atomic write to
`settings.state_dir()` — a read-only or unwritable state directory (a classic
broken-checkout state) raises `OSError` there. With the newly added
`exit_on_error=False` the app survives, but `CheckRunComplete` never posts:
all rows sit in their final glyphs, the verdict block never renders, the
last-check line stays empty, nothing is persisted, and the error is silently
swallowed by the worker machinery. The commit's own test for the enumeration
guard asserts "the last-check line rendered — the run completed, not
stranded"; the persist site strands the run in exactly that sense. Every
run-path must route through "the same persist + completion tail" per the
docstring — this one can skip it.
**Fix:** Wrap the tail so a persist failure still reaches a completion render
(e.g. post a degraded completion carrying the results with a placeholder
checked_at, or a dedicated message the handler renders as a fail-verdict
line):

```python
try:
    checked_at = self._service.persist(results)
except Exception as exc:  # WR-01 tail guard — never strand the run
    self.post_message(self.CheckRunComplete(
        _degraded_persist_marker(exc), tuple(results), run_id))
    return
self.post_message(
    self.CheckRunComplete(checked_at, tuple(results), run_id))
```

with the handler treating the marker as a degraded outcome (verdict from
results; last-check line showing the persist failure).

### WR-04: registry read-failure result renders a misleading "0 dirs missing" routing line

**File:** `tui/screens/env_check.py:537-556` (with `_missing_count` at `243-253`)
**Issue:** The read-failure `CheckResult` introduced by this diff carries one
`FAIL: read registry ...` line and no `  - name` listing lines. When it flows
into the (pre-existing) per-kernel routing block — reachable directly, since
`tui/services/env_check.py:209,212` call these kernels — `_missing_count`
returns 0 and the screen renders `⚠ 0 model dirs missing — ...` / `⚠ 0
dataset dirs missing — ...` while the actual state is "the registry cannot
even be read" (count unknowable, not zero). This is operator-facing
misinformation during exactly the broken-checkout scenario the commit
targets; the row summary and drill-down do carry the true FAIL line, but the
verdict block's count contradicts it.
**Fix:** In `_render_check_outcome`, route on the result shape: when a
directory kernel failed with no listing lines, render the kernel's own first
line (or dedicated unreadable-registry wording) instead of the count-based
`ENV_ROUTE_MISSING_*` line:

```python
if model_dirs is not None and not model_dirs.ok:
    listing = _missing_count(model_dirs)
    line = (S.ENV_ROUTE_MISSING_MODELS.format(n=listing)
            if listing or _has_listing_shape(model_dirs)
            else model_dirs.lines[0])
    box.mount(Static(line, classes="verdict-route"))
```

(Or add a count-free unreadable-registry constant to `tui/strings.py`.)

## Info

### IN-01: `_degraded_result` annotation promises `BaseException` but both call sites catch `Exception` only

**File:** `tui/screens/env_check.py:256-273` (call sites `443`, `455`)
**Issue:** The signature is `exc: BaseException`, but the only producers are
`except Exception` blocks — `KeyboardInterrupt`/`SystemExit`/`GeneratorExit`
can never reach it (which is the correct behavior; they should propagate).
The annotation overstates the contract and invites a future caller to widen a
catch site.
**Fix:** Narrow the annotation to `exc: Exception` (the deliberate exclusion
of `BaseException` is worth encoding, and matches the noqa'd catch sites).

---

_Reviewed: 2026-10-15T16:14:13Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick (scoped incremental review of commit 16e21b5; findings verified
by executing the kernels against synthetic corrupt registries)_
