---
phase: 13-dynamic-dispatch-core
reviewed: 2026-10-20T05:37:01Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - Makefile
  - pipeline/dispatch_core.py
  - pipeline/run_sweep_shard.py
  - tests/test_dispatch_core.py
findings:
  critical: 4
  warning: 2
  info: 3
  total: 9
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-10-20T05:37:01Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed the Phase 13 dynamic-dispatch surface: the new engine
(`pipeline/dispatch_core.py`), the `--mode {static,dispatch}` routing and
merge-refusal additions in `pipeline/run_sweep_shard.py`, the Makefile
lint slot, and the contract suite (`tests/test_dispatch_core.py`), with
cross-reference against `pipeline/run_sweep.py` (the composed
enumeration/argv/validation owner), `directories_config.py`, and
`registry_loader.py`.

Verified invariants that hold: the static launch path is
additions-only since `302a3df` (byte-identity of the legacy path
confirmed by diff — only the `--mode` flag, lazy dispatch routing, and
the pre-copy merge refusal were added); `dispatch_core.py` and its
import closure are stdlib-only (no torch/dnallm at module top); the
O_EXCL claim ledger genuinely refuses a second fresh claim on a cell;
the dispatch dry-run manifest is byte-identical across runs and equals
static-mode enumeration on the identity projection; the
dispatch-evidence merge refusal fires before any copy; the state file
precedes any claim/spawn; all 41 tests in the new suite pass and
`ruff` is clean over all three phase files.

However, four Critical defects were found, each confirmed by
executable reproduction against the real module (not just reading):
the singleton-lock create-to-write window lets two dispatchers
proceed on one root; the child pid is never persisted while a child
runs, defeating the documented orphan-recovery procedure and enabling
double-running a cell after a dispatcher kill; `--from-failures` is
silently ignored (a silent full-matrix fallback — the exact WR-07
hazard this phase refuses elsewhere); and an exception in a worker
thread outside the spawn seam silently drops the remaining queue
while the run reports `status: "done"` and exits 0.

## Critical Issues

### CR-01: `--from-failures` is silently ignored in dispatch mode — silent full-matrix fallback

**File:** `pipeline/dispatch_core.py:790-927` (cross-ref
`pipeline/run_sweep.py:1877-1907`, `pipeline/run_sweep.py:1001`)
**Issue:** `parse_sweep_remainder` re-parses the remainder through
`run_sweep.parse_args`, which accepts `--from-failures`
(`run_sweep.py:394-402`) — but `run_dispatch` never reads
`sweep_args.from_failures` (0 occurrences of `from_failures` or
`load_failure_pairs` in `dispatch_core.py`). Consequences, verified by
reproduction:

1. The failures manifest is never validated — a typo'd path or
   malformed file silently no-ops instead of the loud
   `load_failure_pairs` refusal every `run_sweep.main` launch
   performs.
2. The cell filter at `run_sweep.py:1903-1907` is never applied — a
   dispatch launch scoped by `--from-failures` runs the FULL
   `--models x --tasks x --seeds` matrix. A clean manifest, which
   `run_sweep` treats as "an explicit zero-cell run, NOT a full
   sweep", silently becomes a full dispatch sweep here.

This is precisely the hazard family the phase's own zero-cell
refusal (`dispatch_core.py:917-927`: "an empty filter intersection
never falls back to the full registry") exists to prevent, and it
steers multi-day GPU execution.

Reproduction: `--from-failures <1-pair manifest> --models model-a
--tasks task-x --seeds 42,43` spawned 2 cells (the full filter
matrix) with exit 0 and no diagnostic; the identical `run_sweep`
invocation enumerates exactly the failed pair's cells.

**Fix:** In `run_dispatch`, mirror `run_sweep.main`:

```python
failure_pairs = None
if sweep_args.from_failures is not None:
    failure_pairs = run_sweep.load_failure_pairs(
        sweep_args.from_failures, registry_dir)
...
if sweep_args.priority_file is not None:
    ...
if failure_pairs is not None:
    cells = [
        cell for cell in cells
        if (run_sweep.base_model_name(
                cell[0], sweep_args.peft, config_variant), cell[1])
        in failure_pairs
    ]
```

(or refuse `--from-failures` by name in dispatch mode if it is
deliberately out of scope — never accept-and-ignore).

### CR-02: dispatcher lock create-to-write window defeats the singleton guarantee (TOCTOU race)

**File:** `pipeline/dispatch_core.py:478-511`
**Issue:** `acquire_dispatcher_lock` performs an atomic
`os.open(O_CREAT | O_EXCL)` at line 485 but writes the holder payload
only afterwards (lines 509-510). Between the two, the lock file
exists but is EMPTY. A second dispatcher whose `_read_lock_holder`
(lines 427-442) reads in that window parses nothing, gets `None`, and
takes the reclaim branch at line 507 — atomically OVERWRITING the
first dispatcher's lock. Both dispatchers then run concurrently on
one root. The docstring's claim (line 449-451: "two dispatchers
racing on one root resolve to exactly one winner", T-13-02) does not
hold for this window. Verified: calling `acquire_dispatcher_lock`
against an empty lock file returns success (reclaim) rather than
refusing.

Downstream damage when hit: two writers race on
`dispatch_state.json` (counts become garbage); both launches share
the same second-resolution tee log names (mutual truncation); and —
the exactly-once break — a claim in state `claimed` written by
dispatcher A is classified STALE by dispatcher B's skip filter, so
B's `overwrite_claim` (line 631) replaces A's LIVE claim and B spawns
a second child for a cell whose A-child is still running: two
children writing the same cell dir. The entire reclaim-without-lease
design (D13-11) rests on this lock being truly singleton.

**Fix:** On `FileExistsError` with an unreadable/empty lock, do not
reclaim immediately — the empty file may be an in-flight writer. Age
or retry disambiguates dead writers from live ones:

```python
except FileExistsError:
    holder = _read_lock_holder(lock_path)
    if holder is None:
        try:
            age = time.time() - lock_path.stat().st_mtime
        except OSError:
            age = 0.0
        if age < _LOCK_WRITE_GRACE_SECONDS:  # e.g. 5.0
            sys.exit(
                f"[Error] dispatcher lock at {lock_path} was just "
                "created or is unwritten — another dispatcher may be "
                "starting; retry in a few seconds")
        _atomic_write_json(lock_path, payload)  # provably stale
        return lock_path
    ...
```

### CR-03: child pid is never persisted while the child runs — documented orphan recovery is impossible, relaunch double-runs the cell

**File:** `pipeline/dispatch_core.py:624-702` (claim write 627-635,
in-memory pid 680, persistence only at `finalize_claim` 702)
**Issue:** The claim file is written BEFORE the spawn with
`"child_pid": None` (`_claim_payload`, line 417). After
`context["spawner"](...)` returns, line 680 sets
`payload["child_pid"]` in the in-memory dict only — the on-disk claim
is not rewritten until `finalize_claim` at line 702, i.e. after
`proc.wait()` returns. For the entire lifetime of a training child
(hours), the on-disk claim says `"child_pid": null`. Verified with a
spy child that reads its own claim during `wait()`:
`{'state': 'claimed', 'child_pid': None}`.

This breaks the module's own crash-recovery contract (docstring
lines 66-73): "a SIGKILLed dispatcher leaves its children RUNNING ...
Before relaunching a root whose dispatcher was killed, KILL THE
ORPHANS first — each claim JSON records its child pid, which makes
them findable." The pids are NOT recorded on disk while the children
run — the exact window in which a dispatcher kill leaves orphans. The
operator cannot follow the documented procedure; the relaunch then
requeues the `claimed` cell and spawns a SECOND child while the
orphan still holds the GPU and writes the same cell dir — duplicated
execution and racing artifact writes, the P1 scenario.

**Fix:** Persist the pid immediately after spawn, before waiting:

```python
proc = context["spawner"](...)
payload["child_pid"] = getattr(proc, "pid", None)
_atomic_write_json(Path(claim_path), payload)  # pid durable pre-wait
code = proc.wait()
```

### CR-04: worker-thread exception silently drops the remaining queue; run reports `done` and exits 0

**File:** `pipeline/dispatch_core.py:610-717, 1123-1156`
**Issue:** Inside `_spawn_worker`, only the spawn/wait seam is
guarded (`except (subprocess.SubprocessError, OSError)` at 682-685).
An exception from `claim_cell`/`overwrite_claim` (os.open/write,
lines 296-303, 354-356), `finalize_claim`, or the final
`_write_state` (line 712) — e.g. ENOSPC/EACCES — propagates out of
the `while` loop and kills the worker THREAD. `thread.join()` at
1123-1124 does not re-raise; every cell still in `pending` is never
spawned and never recorded; `run_dispatch` then prints the verdict
table, writes `state["status"] = "done"` (line 1142), and — because
`counts["failed"] == 0` — returns WITHOUT `sys.exit(1)` (lines
1150-1156). Verified: injecting `OSError(28, "No space left on
device")` on the first finalize-time state write produced 1 of 4
cells spawned, `status='done'`,
`counts={'completed': 1, 'failed': 0, 'skipped': 0, 'total': 4}`, and
no `SystemExit` — process exit code 0 with 75% of the matrix silently
unrun.

For a platform whose stated core value is that every number is
correct and reproducible, a false-success exit on the orchestrator's
error path is unacceptable: automation sees success and never
relaunches.

**Fix:** (a) per-iteration containment in `_spawn_worker` so any
exception fails THAT cell and either continues or drains loudly; and
(b) an accounting assertion after join, before the success path:

```python
for thread in threads:
    thread.join()
...
drained = counts["completed"] + counts["failed"] + counts["skipped"]
if drained != counts["total"]:
    state["status"] = "incomplete"
    _write_state(state_path, state)
    sys.exit(
        f"[Error] dispatch accounting mismatch: {drained}/"
        f"{counts['total']} cells accounted for — a worker died "
        "unexpectedly; unrun cells remain queued in the ledger")
```

## Warnings

### WR-01: dispatch skips `run_sweep.main`'s startup `--subset_file` map validation (mirror gap)

**File:** `pipeline/dispatch_core.py:833-843` (cross-ref
`pipeline/run_sweep.py:1860-1869`)
**Issue:** The module docstring claims step 1 "mirrors collect-all"
of the whole `run_sweep.main` startup validation family, and the
in-code comment (lines 815-820) names the mirrored checks — but
`_validate_subset_file` (D-14) is not among them: dispatch only
checks the flag is non-empty, then threads it to every child. A bad
subset map (unreadable, non-object, unknown task keys, non-integer
IDs) that `run_sweep` refuses at startup here burns one child launch
per cell and is recorded as N cell failures instead of one named
collect-all refusal before anything touches the root. Not silent (the
child re-validates), hence WARNING not CRITICAL, but it is a
regression of the collect-all discipline the phase claims to mirror.
**Fix:** Next to `_validate_filters` (line 862), add:

```python
if subset_file_abs is not None:
    run_sweep._validate_subset_file(
        subset_file_abs,
        registry_loader.load_datasets_registry(registry_dir))
```

### WR-02: parseable lock with an out-of-range `pid` crashes with uncaught OverflowError

**File:** `pipeline/dispatch_core.py:489-504`
**Issue:** `_read_lock_holder` returns any dict, and
`isinstance(holder.get("pid"), int)` accepts arbitrarily large
integers; `os.kill(2**63, 0)` raises `OverflowError`, which is
neither `ProcessLookupError` nor `PermissionError`, so it escapes the
except clauses and crashes the launcher with a raw traceback.
Verified: `pid=2**63` in the lock JSON → `OverflowError: Python int
too large to convert to C long`. This contradicts the designed
tolerant-read contract ("malformed/unreadable lock ... is RECLAIMED",
line 458-460): a corrupt-but-parseable lock should never produce an
unhandled crash on the recovery path.
**Fix:** Add `OverflowError` to the dead-holder branch (a pid that
cannot exist is provably not a live holder):

```python
try:
    os.kill(holder_pid, 0)
except (ProcessLookupError, OverflowError):
    pass  # provably dead / impossible pid — fall through to reclaim
except PermissionError:
    ...
```

## Info

### IN-01: `_atomic_write_json` tmp path follows a planted symlink

**File:** `pipeline/dispatch_core.py:359-374`
**Issue:** `open(tmp, "w")` on `path.name + ".tmp"` follows a symlink
planted at that path (no `O_EXCL`/`O_NOFOLLOW`), so a local writer
can redirect the atomic-replace write of a claim, the lock, or the
state file to an arbitrary location with controlled JSON content.
Low severity (operator-owned output root, workstation threat model),
but inconsistent with the T-13-01 no-follow discipline used for the
claim/lock creates themselves.
**Fix:** Create the tmp with `os.open(tmp, os.O_CREAT | os.O_EXCL |
os.O_WRONLY, 0o644)` (retry with a unique suffix on EEXIST).

### IN-02: tee-log stamp has 1-second resolution — a sub-second relaunch truncates the prior crash log

**File:** `pipeline/dispatch_core.py:1041-1043, 1096-1108`
**Issue:** `WORKER_LOG_TIMESTAMP_FORMAT` (`%Y%m%d_%H%M%S`,
`run_sweep_shard.py:192`) gives the per-launch stamp only
second resolution. A dispatcher relaunch within the same second
(scripted supervisor / immediate restart loop, which is exactly the
crash-recovery scenario WR-02 targets) opens the prior launch's
`{base}-dispatch-w{i}-{stamp}.log` with mode `"w"` and truncates the
crash evidence the naming scheme exists to preserve.
**Fix:** Add `%f` (microseconds) or a short uuid fragment to the
dispatch stamp.

### IN-03: test-coverage gaps corresponding to the Critical findings

**File:** `tests/test_dispatch_core.py`
**Issue:** The 41-test suite is strong on the tested contracts
(SC1/SC2/SC3, dry-run goldens, static byte-identity pins, merge
refusals — all verified passing), but nothing pins: (a) the on-disk
claim's `child_pid` while the child runs (CR-03); (b) behavior when a
worker thread raises outside the spawn seam (CR-04); (c) the
empty/in-flight lock window (CR-02); (d) `--from-failures` handling
in dispatch mode (CR-01). Each invariant is currently unguarded, so
none of the four regressions would turn a test red.
**Fix:** After fixing CR-01..CR-04, add one test per: a spy child
asserting its claim's `child_pid` is non-null during `wait()`; a
spawner/state-write seam raising OSError asserting exit 1 and an
honest `status`; a pre-created empty lock with fresh mtime asserting
refusal; and a `--from-failures` dispatch enumerating exactly the
failed pairs (or refusing by name).

---

_Reviewed: 2026-10-20T05:37:01Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
