---
phase: 13-dynamic-dispatch-core
reviewed: 2026-10-20T06:21:31Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - Makefile
  - pipeline/dispatch_core.py
  - pipeline/run_sweep_shard.py
  - tests/test_dispatch_core.py
findings:
  critical: 0
  warning: 0
  info: 5
  total: 5
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-10-20T06:21:31Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found (0 Critical, 0 Warning — 4 carried Info + 1 new Info observation; no fix iteration required under the `critical_warning` scope)

## Summary

Iteration-3 re-review (final iteration of the `--auto` loop), centered on
the WR-03 fix (commit `095dd74`) and a fresh adversarial sweep for
anything that fix or the earlier fix commits introduced.

**WR-03 fix verification — HOLDS, mutation-proven.** The fix nests BOTH
the containment handler's claim rewrite AND the failed-count increment
under `if not accounted:` (`pipeline/dispatch_core.py:794-830`; before
the fix only the count was gated while the rewrite was unconditional).
Tracing every reachable exception window in `_spawn_worker`:

- Exception AFTER `accounted = True` (the only raiser after that point
  is the `_write_state` call — the code between the count increment and
  the flag assignment is dict/int mutation that cannot raise): the
  handler no-ops, the drain continues, the on-disk claim keeps its
  truthful terminal state (`completed` + the child's real `exit_code`
  + `error: null`), no double count, and the end-of-run main-thread
  state write persists honest counts. Exactly the designed WR-03
  behavior.
- Exception BEFORE finalize/count (claim create/overwrite, argv build,
  the spawn seam, `finalize_claim`): rewrite to `failed` with the
  dispatcher-side error, counted failed once, exit-1 path drives — the
  CR-04 containment, unchanged by the fix.
- The containment's OWN state write failing (un-accounted path): the
  exception escapes the handler, kills the worker thread, and the
  post-join accounting assertion (`dispatch_core.py:1311-1321`) refuses
  loudly with `status: "incomplete"` — no false success.

**Mutation probe (isolated `/tmp` copy; the repo was never modified):**
reverting the gate (making the rewrite unconditional again, the
pre-`095dd74` behavior) makes exactly
`test_worker_state_write_failure_keeps_truthful_claims` FAIL
(1 failed / 51 passed) — the regression pin is real, not vacuous. The
fix is also pinned from the other side: removing only the count gate
would double-count and trip the accounting assertion, failing the same
test via `SystemExit`. With the fix in place: 52/52 dispatch tests pass,
101/101 including the static `test_sweep_shard.py` byte-identity
tripwire, and `ruff check tests/ pipeline/dispatch_core.py
pipeline/run_sweep_shard.py` is clean.

**Prior fixes re-confirmed holding in the current tree:** CR-01
(`--from-failures` validated + cell filter, `dispatch_core.py:1061-1085`),
CR-02 (lock create-to-write grace window, `:516-524`), CR-03 (pid
persisted to the claim before `wait()`, `:739-748`), CR-04 (per-cell
containment + post-join accounting assertion, `:782-830`, `:1311-1321`),
WR-01 (`_validate_subset_file` startup mirror — verified verbatim against
`run_sweep.py:1866-1870`, same registry view, `:1028-1031`), WR-02
(`OverflowError` treated as provably dead, `:530-537`). The dispatch
dry-run `sweep_flags` construction (`:1119-1137`) mirrors
`run_sweep.py:1826-1856` key-for-key plus the single documented
`orchestrator_mode` marker.

**Scope discipline verified:** `git diff --name-only 302a3df..HEAD` over
source paths is exactly `Makefile`, `pipeline/dispatch_core.py`,
`pipeline/run_sweep_shard.py`, `tests/test_dispatch_core.py`;
`pipeline/run_sweep.py` and `pipeline/run_finetune.py` have ZERO diff
lines vs the baseline; the `run_sweep_shard.py` delta is additions-only
(`--mode` flag, lazy dispatch routing, the evidence-based pre-copy merge
refusal — the static launch path body is unchanged); `dispatch_core.py`
and its import closure remain stdlib-only.

**New findings this iteration:** no new Critical or Warning issues. The
four known Info items (IN-01..IN-04) were re-examined and none was made
materially worse by the WR-03 fix — the fix only alters the accounted
branch, which sits downstream of all four windows; they are carried
below as recorded in `13-REVIEW-FIX.md`. One new Info-tier observation
(IN-05) is recorded with an explicit defer-to-owner note.

## Info

### IN-01: `_atomic_write_json` tmp path follows a planted symlink (carried, iteration 1)

**File:** `pipeline/dispatch_core.py:370-385`
**Issue:** `open(tmp, "w")` on `path.name + ".tmp"` follows a symlink
planted at that path, so a local writer can redirect the atomic-replace
write of a claim, the lock, or the state file. Low severity
(operator-owned output root, workstation threat model); inconsistent
with the T-13-01 no-follow discipline used for the claim/lock creates.
**Fix:** Create the tmp with `os.open(tmp, os.O_CREAT | os.O_EXCL |
os.O_WRONLY, 0o644)` (retry with a unique suffix on EEXIST). Recorded
as out-of-scope in `13-REVIEW-FIX.md`; unchanged by the WR-03 fix.

### IN-02: tee-log stamp has 1-second resolution — a sub-second relaunch truncates the prior crash log (carried, iteration 1)

**File:** `pipeline/dispatch_core.py:1210-1212, 1265-1277`
**Issue:** `WORKER_LOG_TIMESTAMP_FORMAT` (`%Y%m%d_%H%M%S`,
`run_sweep_shard.py:192`) gives the per-launch stamp only second
resolution; a relaunch within the same second opens the prior launch's
`{base}-dispatch-w{i}-{stamp}.log` with mode `"w"` and truncates the
crash evidence the naming scheme exists to preserve.
**Fix:** Add `%f` (microseconds) or a short uuid fragment to the
dispatch stamp. Recorded as out-of-scope; unchanged by the WR-03 fix.

### IN-03: terminal state writes happen after the lock is released — a fast relaunch's fresh state can be briefly clobbered (carried, iteration 2)

**File:** `pipeline/dispatch_core.py:1294-1300` (release) vs `:1314-1316`
and `:1332-1334` (post-join `incomplete`/`done` writes)
**Issue:** the `finally` releases the dispatcher lock before both the
`incomplete`-status and final `done`-status writes; a fast supervisor
relaunch's fresh `running` state can be briefly overwritten. Transient
and self-correcting; the counts themselves are always main-thread
authoritative at the moment of the final write.
**Fix:** Move the terminal state writes before the lock release (or
re-order the finally). Recorded as out-of-scope; unchanged by the WR-03
fix.

### IN-04: a failed CR-03 pid-persist write abandons an already-spawned child without waiting it (carried, iteration 2)

**File:** `pipeline/dispatch_core.py:727-753`
**Issue:** if the pid-persist `_atomic_write_json` raises, the spawned
child is never `wait()`ed and the worker immediately proceeds to the
next cell on the same GPU — transient contention under an
already-degrading disk. Exactly-once survives (the claim is marked
failed; the child is resume-safe via the marker).
**Fix:** On pid-persist failure, best-effort `proc.wait()` before
continuing. Recorded as out-of-scope; NOT worsened by the WR-03 fix
(this window precedes the accounted branch entirely — the un-accounted
handler behavior there is byte-identical to pre-fix).

### IN-05: a non-integer `--seeds` token crashes with a raw ValueError traceback instead of a named collect-all refusal (new observation, defer to owner)

**File:** `pipeline/dispatch_core.py:913-915`
**Issue:** `seeds = sorted({int(s.strip()) for s in
sweep_args.seeds.split(",") if s.strip()})` raises an uncaught
`ValueError` on a typo'd token (e.g. `--seeds 4o`), producing a raw
traceback rather than the named collect-all refusal this module
practices for every other flag (empty `--models`/`--tasks`, arity
mismatch, variant x peft). HOWEVER: this byte-mirrors the composed flag
owner `run_sweep.main` (`run_sweep.py:1682`, identical expression), so
both modes fail identically and a dispatch-side divergence would itself
violate D-07 (run_sweep stays the single flag owner). The static path
has carried the same shape since before this phase.
**Fix:** Belongs in `run_sweep.parse_args`/`main` (wrap the seed parse
in the collect-all problem list), then mirror here — NOT a
dispatch-only change. Defer to the flag owner's routing; do not fix in
this phase (scope discipline forbids touching `run_sweep.py`).

---

_Reviewed: 2026-10-20T06:21:31Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Iteration: 3 of 3 (--auto loop); prior iterations: 13-REVIEW.iter2.md (4 Critical + 2 Warning, all fixed), WR-03 fixed in 095dd74_
