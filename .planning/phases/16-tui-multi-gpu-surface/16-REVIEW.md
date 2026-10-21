---
phase: 16-tui-multi-gpu-surface
reviewed: 2026-10-21T06:42:03Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - tui/services/gpu_probe.py
  - tui/services/dispatch_state.py
  - tui/services/run_config.py
  - tui/services/sweep_launcher.py
  - tui/screens/monitor.py
  - tui/screens/run_config.py
  - tui/app.py
  - tui/strings.py
  - tui/styles.tcss
  - tests/tui/test_services_gpu_probe.py
  - tests/tui/test_services_dispatch_state.py
  - tests/tui/test_services_run_config.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_snapshots.py
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 16: Code Review Report

**Reviewed:** 2026-10-21T06:42:03Z
**Depth:** standard
**Files Reviewed:** 16 (9 source + 7 test files as evidence)
**Status:** issues_found

## Summary

Phase 16's TUI-01..04 surface was reviewed at standard depth against the
diff base `ee1228e` (9 changed source files, ~1565 insertions), with the
review invariants cross-checked against the live pipeline modules the new
code contracts with (`pipeline/dispatch_core.py`, `pipeline/run_sweep_shard.py`,
`pipeline/artifact_loader.py`). The service-tier invariants hold: both new
services import zero textual (verified by reading imports and by the passing
`test_import_lock.py` glob), screens stay thin (every number the confirm
faces and dispatch rows render arrives service-side), the gate chain order
is byte-preserved with only the stage-0 predicate swapped, the E2'
typed-phrase mechanics are untouched, every amended
`LNC_SINGLE_GPU_BLOCKED` site (4 production + 5 test sites) formats with
the new `{roots}/{workers}/{n}` signature, both new dataclass families are
frozen, and the worker-guard holds at every call site (provider and reader
are each wrapped in `except Exception` inside their workers; no path raises
into the app). All 5 relevant unit suites pass locally (gpu_probe,
dispatch_state, run_config, sweep_launcher, strings, import lock).

Five warnings remain. The two most consequential are cross-module: (1) the
capacity predicate's per-root GPU-demand cache is never invalidated, so a
routine kill-then-relaunch at the same output root poisons the arithmetic
in **both** directions (over-refusal and over-admission) — reproduced
locally against the real service; (2) the 60s dispatch-state staleness
threshold sits far below the writer's actual write cadence (state is
written only at claim/finalize/containment/terminal transitions — no
heartbeat — while real training cells run for minutes-to-hours), so the
`MON_DISPATCH_STALE` marker will render almost permanently on healthy
runs. Two display-honesty defects follow (the `all(n)` GPUs claim
contradicts the child CLI's `0..workers-1` default; a malformed-but-fresh
view renders the stale copy with a self-contradictory age), plus one
timeout-bounding gap in the probe runner.

## Critical Issues

(None.)

## Warnings

### WR-01: `_demand_cache` is never invalidated — stale per-root GPU demand after kill/detach/prune + relaunch

**File:** `tui/services/sweep_launcher.py:766,912-925` (with `kill_sweep` 1298-1329, `detach` 1331-1349, `live_sweeps` 1353-1381, `_spawn` 770-884)
**Issue:** `_entry_demand(root)` caches each live root's parsed `--workers`
in `self._demand_cache` on first read ("argv is immutable per entry"), but
no code path — `kill_sweep`, `detach`, the `live_sweeps()` dead-entry
prune, or `_spawn`'s root re-claim — ever evicts the cached value when the
registry entry for that root is dropped. When the root is later re-claimed
by a NEW entry with a different argv, `_entry_demand` returns the dead
entry's demand. The docstring's "An unknown/dead root demands 1 (the
fail-safe)" is therefore not what the code does for a re-claimed root.

Reproduced against the real service (2-GPU pin): launch a 2-worker
dispatch sweep at root R (cache[R]=2), kill it, relaunch R with
`--workers 1`, then call `single_gpu_launch_blocked(requested_workers=1)`
— it returns a `GpuCapacityBlock` (refuses) although the true arithmetic
is 1 + 1 = 2 <= 2. The inverse ordering (kill a 1-worker run, relaunch
with `--workers 2`, then request another launch) under-counts and
**over-admits**, oversubscribing GPUs — the exact condition the 16-03
predicate exists to prevent. The over-refuse direction locks the operator
out of valid launches at that root until the TUI restarts (no in-app
recovery path), because the cache persists for the whole session.

**Fix:** Evict the cache entry whenever a root's registry entry is dropped
or re-claimed:

```python
# in kill_sweep / detach / live_sweeps-prune, after self._live.pop(root, None):
self._demand_cache.pop(root, None)

# in _spawn, after claiming a new entry (covers the dead-entry reclaim path):
self._live[root] = {"handle": proc, "meta": meta, "tee": tee_handle}
self._demand_cache.pop(root, None)   # a new argv re-parses on next read
```

(Alternatively key the cache by `(root, argv_tuple)` like `_plan_cache`
keys by argv — an immutable key cannot go stale.)

### WR-02: `DISPATCH_STALE_SECONDS = 60.0` is far below the writer's actual write cadence — the stale marker will false-positive on healthy runs

**File:** `tui/services/dispatch_state.py:66` (cross-module: `pipeline/dispatch_core.py:852-883,909,1036,1133,1186,1950,1967`)
**Issue:** D16-08's rationale ("a live orchestrator refreshes the file
continuously") does not match the writer. `dispatch_core._publish_state`
is called only at state transitions — pre-drain, claim, finalize/failure,
terminal — and the renderer docstring explicitly pins "no timer loop". A
worker's claim-to-finalize window is one full fine-tuning cell, i.e.
minutes-to-hours. So on any healthy dispatch run the state file's mtime
age exceeds 60s almost all of the time, and `read_dispatch_state` will
flag `stale=True` and the monitor will render
`⚠ dispatch state stale (…s >= 60s) — data may be outdated` as a
near-permanent fixture. A permanently-on warning destroys the signal it
was built for: when the dispatcher genuinely stalls, the marker is
indistinguishable from background. The module's own tunability note
("never below the longest expected transition gap") is violated by the
shipped default — one cell is the longest expected gap, and it is orders
of magnitude above 60s.

**Fix:** Either raise the default far above a cell duration (e.g.
`DISPATCH_STALE_SECONDS = 3600.0`+, documented against cell runtime), or
add a dispatcher-side heartbeat (a periodic `_publish_state` in the
drain loop) — the latter is a pipeline change and needs a maintainer
ruling; the TUI-side threshold fix is in scope for this phase.

### WR-03: "all detected GPUs" claim contradicts the child CLI — the empty `--gpus` default resolves to `0..workers-1`, not all detected GPUs

**File:** `tui/services/sweep_launcher.py:519-525` (`gpus_display = f"all({effective_gpu_count()})"`), `tui/strings.py:1499-1501` (`CFG_GPUS_DEFAULT`), `tui/services/run_config.py:242-247,1294-1303` (docstrings); child truth at `pipeline/dispatch_core.py:1796-1798`
**Issue:** The GPUs field placeholder ("— (default: all detected GPUs)"),
the confirm faces' dispatch-plan line ("GPUs all(n)" with n the detected
count), and three service docstrings all claim that an unset `--gpus`
resolves to every detected GPU at launch time. The child does something
else: `if gpus is None: gpus = [str(i) for i in range(workers)]` — the
first `workers` GPUs only. On the 2×5090 validation box with workers=2
the two coincide (all(2) == {0,1}), so tests and goldens cannot catch it;
on any machine with more detected GPUs than workers (e.g. 4 GPUs,
workers=2) the confirm gate asserts "GPUs all(4)" for a launch that will
bind GPUs 0 and 1. A confirm gate whose one job is honest pre-launch
truth over-claims GPU usage exactly in the multi-GPU-expansion case the
feature targets.

**Fix:** Render the resolution rule the child actually applies when
`spec.gpus` is None — e.g. `f"0..{workers-1}"` (or `first({workers})`) —
or make the child default match the copy (a pipeline change, needs a
ruling). At minimum, amend `CFG_GPUS_DEFAULT` and the
`GateSummary.gpus_display` docstrings so the displayed rule matches
`dispatch_core`'s documented "Default GPU assignment".

### WR-04: A malformed-but-fresh dispatch view renders the STALE copy with a self-contradictory age

**File:** `tui/screens/monitor.py:3757-3760` (with `tui/strings.py` `MON_DISPATCH_STALE`, and `_dispatch_structure_legs` at `monitor.py:2876`)
**Issue:** The warning row fires on `view.stale or view.malformed`, but
the copy is exclusively about staleness and interpolates
`view.stale_age_s`. For a view with `malformed=True, stale=False` (a
parseable snapshot violating the schema's snapshot invariant with a fresh
mtime), the render claims "dispatch state stale (5s >= 60s)" — an
internally false statement (5s is not >= 60s) that also mischaracterizes
the actual condition (an invariant violation, not outdated data). The
pilot test masks this: its malformed fixture carries `stale_age_s=120`,
so the wrong-copy case never renders in the suite. The condition is rare
(the writer maintains the invariant by construction), but it is exactly
the "honesty flag" case the reader was built to surface, and the render
is the only place an operator would ever see it.

**Fix:** Split the copy: render `MON_DISPATCH_STALE` only when
`view.stale`, and add a distinct constant (e.g. `MON_DISPATCH_MALFORMED`,
"⚠ dispatch counts inconsistent (snapshot invariant violated) — values
shown verbatim") for the malformed-only case; render both when both.

### WR-05: The probe timeout is not fully bounded — `subprocess.run`'s post-kill `wait()` can hang the worker on a D-state nvidia-smi

**File:** `tui/services/gpu_probe.py:107-110` (`_default_runner`)
**Issue:** D16-03 claims "the per-call timeout (~2s) bounds the call so a
hung nvidia-smi can never block the panel's worker". The timeout bounds
`communicate()`, but on `TimeoutExpired` CPython's POSIX path runs
`process.kill()` followed by an **unbounded** `process.wait()`. SIGKILL
cannot interrupt a process in uninterruptible (D) state, and a wedged
NVIDIA driver holding nvidia-smi in a driver ioctl is a real-world
failure mode on GPU boxes. In that state the worker thread blocks
forever; because `_run_gpu_probe` is `exclusive=True` per 2s tick, every
subsequent tick spawns a *new* probe (each spawning another nvidia-smi
that also wedges), accumulating stuck threads and processes until the
driver recovers. The panel survives (the app never crashes — the
worker-guard and exclusive-group discipline hold), but the "never block"
claim is not strictly true and the degradation accumulates.

**Fix:** Drop the raw `subprocess.run` for an explicitly reaped variant:
`Popen` + `communicate(timeout=...)`, and in the timeout path
`process.kill()` followed by `process.wait(timeout=PROBE_TIMEOUT_SECONDS)`
inside a `except subprocess.TimeoutExpired: process.wait()`-free
`try/except Exception: return None` — i.e. treat an un-reapable child as
the absent outcome and leak the (already-killed) handle rather than
blocking. Note the trade-off in the docstring (a rare zombie until the
driver recovers is strictly better than a stuck worker per tick).

## Info

### IN-01: `_parse_gpu_indices` accepts non-canonical int()-parseable tokens and threads them verbatim into `CUDA_VISIBLE_DEVICES`

**File:** `tui/services/run_config.py:374-389`
**Issue:** The mirror validates each token with `int(token)` (accepting
`+1`, `01`, `1_0`, and non-ASCII decimal digits) but appends the RAW
token to the tuple; `run_sweep_shard`/`dispatch_core` treat `--gpus`
values as operator-owned verbatim strings threaded straight into
`CUDA_VISIBLE_DEVICES` (run_sweep_shard.py:1766). A typo like `1_0`
parses as 10 here and at the CLI, so `--gpus 0,1_0` threads a token CUDA
cannot resolve, producing a worker with a broken GPU mask instead of a
parse refusal.
**Fix:** Accept only canonical decimal indices — `if not token.isdigit()
or not token.isascii(): return None`, or round-trip check
`str(int(token)) == token` — and append `str(int(token))`.

### IN-02: GPU indices normalize with a STRING sort — non-numeric order at >= 10 GPUs

**File:** `tui/services/run_config.py:277-279` (and `_parse_gpu_indices` at 389)
**Issue:** `RunSpec.__post_init__` sorts `gpus` lexicographically:
`("2", "10")` normalizes to `("10", "2")`. The set is unchanged (workers
are homogeneous, so per-worker assignment is immaterial today), but the
threaded `--gpus` order and the confirm-face display will disagree with
any numeric expectation once a machine has >= 10 GPUs.
**Fix:** Sort numerically when every token is a decimal index
(`sorted(set(...), key=int)`), or normalize tokens to `str(int(token))`
at parse time (see IN-01) so the string sort equals the numeric sort.

### IN-03: nvidia-smi "[N/A]" sensor values degrade the whole panel to the "not installed" copy

**File:** `tui/services/gpu_probe.py:143-157` (with `MON_GPU_ABSENT` copy in `tui/strings.py`)
**Issue:** Real nvidia-smi emits `[N/A]` / `[Not Supported]` for
individual sensor fields on some driver/GPU states (GPU initializing at
boot, MIG configurations). The pinned strict-int parse (D16-02, one bad
line degrades the whole probe) then renders the panel as
"◌ nvidia-smi not installed" — honest per the one-absent-shape rule, but
the copy misattributes a sensor-level degradation to a missing binary,
and healthy sibling GPUs' data is dropped. This is the documented design
tradeoff; flagging the real output class so the degradation shape is a
known quantity rather than a surprise.
**Fix:** If desired, widen the absent copy (e.g. "nvidia-smi unavailable
or unreadable") — a strings-only change; per-row tolerance would violate
D16-02 and is not suggested.

### IN-04: The GPUs field placeholder says empty = "all detected GPUs", but a cleared field keeps the last valid list

**File:** `tui/screens/run_config.py:1768-1795` (`_compose_spec`) with `CFG_GPUS_DEFAULT` (`tui/strings.py:1499-1501`)
**Issue:** After an operator types `0,1` (parsed once, so
`self._spec.gpus = ("0","1")`) and then clears the field, `_compose_spec`
threads no `gpus` partial and `replace(self._spec, ...)` keeps the old
tuple: the field displays the "default: all detected GPUs" placeholder
while the next launch pins `--gpus 0,1`. The preview modal and confirm
line do show the truth, and last-valid-governs is the established screen
idiom (epochs/curve/ebs behave identically) — but those fields carry no
placeholder that explicitly defines what "empty" means, so the copy is
more misleading here. Related to WR-03 (the claimed default is itself
inaccurate).
**Fix:** Either let an explicitly cleared GPUs field reset to None
(distinguishing "never typed" from "typed then cleared"), or drop the
definitive "default:" wording from the placeholder.

---

_Reviewed: 2026-10-21T06:42:03Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
