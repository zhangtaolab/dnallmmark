---
phase: 13-dynamic-dispatch-core
fixed_at: 2026-10-20T14:35:00Z
review_path: .planning/phases/13-dynamic-dispatch-core/13-REVIEW.md
iteration: 2
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 13: Code Review Fix Report

**Fixed at:** 2026-10-20T14:35:00Z
**Source review:** .planning/phases/13-dynamic-dispatch-core/13-REVIEW.md
**Iteration:** 2

**Summary:**
- Findings in scope: 1 (WR-03; fix_scope=`critical_warning`, so the 4 Info items IN-01..IN-04 are out of scope — recorded below as skipped-info, not fixed)
- Fixed: 1
- Skipped: 0 (in scope)

**Scope discipline (binding constraints honored):**
- Commit `095dd74` touches exactly `pipeline/dispatch_core.py` + `tests/test_dispatch_core.py` (`git show --stat` confirms); `run_sweep.py` / `run_sweep_shard.py` untouched by this iteration, so the frozen contracts and static-mode byte-identity hold trivially.
- `dispatch_core.py` stays stdlib-only — the fix adds zero imports (it only restructures the existing containment handler).
- The reviewer's verified fix direction was applied as specified: gate the containment's claim re-finalize on `not accounted`.

## Fixed Issues

### WR-03: containment re-finalizes an already-truthful claim as `failed` when only the state write fails

**Files modified:** `pipeline/dispatch_core.py`, `tests/test_dispatch_core.py`
**Commit:** 095dd74
**Applied fix:** In `_spawn_worker`'s per-cell containment handler (the CR-04 boundary), the unconditional claim rewrite (`state: failed`, `exit_code: null`, `error: "dispatcher-side failure: ..."`) is now nested INSIDE the existing `if not accounted:` guard — the same flag that already gated the failed-count increment. `accounted=True` means `finalize_claim` already persisted the cell's truthful terminal state and the count was already incremented; the only operation after that point is the `dispatch_state.json` write, so a worker-thread-only failure there (ENOSPC/EACCES on the state file while the ledger dir stays writable) no longer overwrites completed claims. An already-accounted cell keeps its truthful claim; the end-of-run main-thread state write persists the truthful counts, exactly as the in-code comment always claimed. The un-accounted path (failure before/at `finalize_claim`) is unchanged: claim rewritten to `failed` with the dispatcher-side error, count incremented, exit-1 path drives.
**Regression test:** `test_worker_state_write_failure_keeps_truthful_claims` — mirrors `_worker_state_writes_always_fail` (worker-thread-only ENOSPC on `_write_state`; `finalize_claim` untouched): 4/4 cells drain, run exits 0 with `status: "done"` and honest counts (`completed: 4, failed: 0`), and EVERY final claim asserts `state == "completed"`, `exit_code == 0`, `error is None`.
**Fix verification (mutation probe):** with the fix temporarily reverted (`git checkout` of `pipeline/dispatch_core.py`), the new test FAILS in exactly the reviewer's reproduction — the run prints `4/4 cell(s) completed` and exits 0 while the on-disk claim flips to `state: failed`. Fix re-applied; test passes. The pin is real, not vacuous.

**Logic-bug classification note:** REVIEW.md classifies WR-03 as error-path ledger integrity (a lying claim, not a false-success exit). The exit code, counts, and P1 exactly-once property were already honest and remain so; per the verification-tier discipline this fix is commit-verified plus lane-verified below, and the mutation probe demonstrates the behavioral contract directly.

## Verification (where the gates ran)

All gates ran in the ISOLATED WORKTREE (`.claude/worktrees/rf-13-92832-1792476480`, branch `gsd-reviewfix/13-92832`, since merged to `autorun`), using the MAIN CHECKOUT's `.venv` interpreters — the worktree has no `.venv` by design, so the numbers are reproducible from the main checkout after the fast-forward brought the commits over:

- `.venv/bin/python -m pytest tests/test_dispatch_core.py tests/test_sweep_shard.py -q` — **101 passed** (100 pre-existing + 1 new WR-03 pin; was 51 + 49 in the review).
- Lint lane: the exact `make lint` ruff invocation (full expanded Makefile file list, including `pipeline/dispatch_core.py` via PHASE13_MODULES and `tests/`) run with the main venv's `ruff` — **All checks passed!**
- Typecheck lane: `ty check --python .venv/bin/python` from the worktree (the `--python` pin is required there: without it ty resolves the ambient brew site-packages and emits 199 bogus `unresolved-import` diagnostics unrelated to this change) — **All checks passed!** (zero-diagnostics baseline holds).

## Skipped Issues (Info — out of `critical_warning` fix scope)

Per the iteration-2 binding scope, the 4 Info findings are recorded, not fixed:

### IN-01: `_atomic_write_json` tmp path follows a planted symlink (carried from iteration 1)

**File:** `pipeline/dispatch_core.py:370-385`
**Reason:** skipped-info (out of fix_scope)
**Original issue:** `open(tmp, "w")` on `path.name + ".tmp"` follows a symlink planted at that path; low severity (operator-owned output root, workstation threat model), inconsistent with the T-13-01 no-follow discipline.

### IN-02: tee-log stamp has 1-second resolution — a sub-second relaunch truncates the prior crash log (carried from iteration 1)

**File:** `pipeline/dispatch_core.py:1201-1203, 1256-1268`
**Reason:** skipped-info (out of fix_scope)
**Original issue:** a relaunch within the same second opens the prior launch's `{base}-dispatch-w{i}-{stamp}.log` with mode `"w"` and truncates crash evidence.

### IN-03: terminal state writes happen after the lock is released — a fast relaunch's fresh state can be clobbered

**File:** `pipeline/dispatch_core.py:1285-1325`
**Reason:** skipped-info (out of fix_scope)
**Original issue:** the `finally` releases the dispatcher lock before both the `incomplete`-status and final `done`-status writes; a fast supervisor relaunch's fresh `running` state can be briefly overwritten. Transient and self-correcting.

### IN-04: a failed CR-03 pid-persist write abandons an already-spawned child without waiting it

**File:** `pipeline/dispatch_core.py:727-753`
**Reason:** skipped-info (out of fix_scope)
**Original issue:** if the pid-persist `_atomic_write_json` raises, the spawned child is never `wait()`ed and the worker immediately spawns the next cell on the same GPU — transient contention under an already-degrading disk. Exactly-once survives.

---

_Fixed: 2026-10-20T14:35:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2_
