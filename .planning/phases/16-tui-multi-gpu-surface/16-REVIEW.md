---
phase: 16-tui-multi-gpu-surface
reviewed: 2026-10-21T07:33:38Z
depth: standard
files_reviewed: 9
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
findings:
  critical: 0
  warning: 0
  info: 5
  total: 5
status: issues_found
---

# Phase 16: Code Review Report (iteration 2 — post-fix re-review)

**Reviewed:** 2026-10-21T07:33:38Z (HEAD `258cb3d`, review base `ee1228e`)
**Depth:** standard
**Files Reviewed:** 9 (plus the 5 pinned test suites as evidence)
**Status:** issues_found (0 critical, 0 warnings, 4 carried Info + 1 new Info)

## Summary

Re-review after the iteration-1 fix batch. All five iteration-1 Warnings are
**verified fixed at source, with regression tests that pin each fix**:

- **WR-01 (960435f) — VERIFIED.** `_demand_cache` is now evicted at every
  registry drop/re-claim site: `kill_sweep` (`tui/services/sweep_launcher.py:1339-1345`),
  `detach` (`:1373-1380`), the `live_sweeps()` dead-entry prune (`:1405-1416`),
  `_spawn`'s dead-entry reclaim (`:829-834`), and the `_spawn` claim itself
  (`:898-904`, the belt-and-braces site). The over-refusal direction, the
  over-admission direction, and the detach/prune/reclaim sites each carry a
  dedicated regression test
  (`tests/tui/test_services_sweep_launcher.py`, WR-01 block) — all pass.
- **WR-02 (a8c4965) — VERIFIED.** `DISPATCH_STALE_SECONDS = 3600.0`
  (`tui/services/dispatch_state.py:74`) with the cell-scale rationale and the
  raise-only maintainer-tunability clause documented at the constant;
  `MON_DISPATCH_STALE` now interpolates `{grace}` (`tui/strings.py:2064-2066`)
  and the monitor formats `grace=int(dispatch_state.DISPATCH_STALE_SECONDS)`
  (`tui/screens/monitor.py:3770-3772`). Tests pin 120s fresh (inside one cell
  window), 3700s stale, and the constant value.
- **WR-03 (e0f4523) — VERIFIED.** `GateSummary.gpus_display` derives from the
  spec alone: the comma-joined typed list or `f"0..{workers - 1}"`
  (`tui/services/sweep_launcher.py:528-533`) — dispatch_core's
  `range(workers)` first-workers rule, never "all detected". The
  `CFG_GPUS_DEFAULT` placeholder (`tui/strings.py:1518-1520`), the `RunSpec`
  docstring, and the `GateSummary` docstring all match. Tests pin `0..0`,
  `0..1`, `0..3`, and the no-detection-at-preview property. One residual doc
  drift found — see IN-05.
- **WR-04 (aab7d69) — VERIFIED.** Stale and malformed are separate honesty
  rows, stale first (`tui/screens/monitor.py:3768-3776`), with the distinct
  `MON_DISPATCH_MALFORMED` constant (`tui/strings.py:2069-2072`); the
  structure leg is now the warning-ROW count `int(view.stale) +
  int(view.malformed)` (`monitor.py:2878-2879`) so the 1→2 row flip forces a
  rebuild. Pilot tests pin stale-only, malformed-fresh (at age 5, where a
  borrowed staleness copy would assert a false age claim), and both-flags
  ordering (`tests/tui/test_pilot_monitor.py:6328-6390`).
- **WR-05 (258cb3d) — VERIFIED.** `_default_runner` is rewritten to
  `Popen` + `communicate(timeout=...)`, then on `TimeoutExpired` `kill()` +
  `wait(timeout=timeout)`; a second `TimeoutExpired` warns once on the module
  logger, leaks the already-killed handle (documented trade-off), and
  re-raises the ORIGINAL `TimeoutExpired`, which `probe()` degrades to the
  absent outcome (`tui/services/gpu_probe.py:138-157`). Tests pin the wedged
  shape (asserting the wait is bounded), the clean-reap path, and the happy
  path over a real `sys.executable` subprocess.

**Nothing new was introduced by the fix batch**: no debug artifacts in the
diff; the G panel compose placement, dispatch-block render, gate threading,
and argv composers re-checked at standard depth with no new behavioral
defects. Full pinned suites pass at HEAD in the working tree:
`test_services_gpu_probe.py` + `test_services_dispatch_state.py` +
`test_services_sweep_launcher.py` (110 passed), `test_pilot_monitor.py` +
`test_pilot_run_config.py` (232 passed), `test_services_run_config.py` +
`test_import_lock.py` + `test_strings_phase11.py` (188 passed), and
`test_snapshots.py` (12 passed — the 4 golden SVGs are present uncommitted in
the working tree per WINDOWS #50 D-03; the committed tree failing exactly
those 4 is the documented pattern and is not a finding).

## Narrative Findings (AI reviewer)

No Critical issues. No Warnings.

## Info

### IN-01: `_parse_gpu_indices` accepts non-canonical integer tokens (carried, iteration 1)

**File:** `tui/services/run_config.py:376-391`
**Issue:** `int(token)` accepts `"007"`, `"+1"`, and Unicode decimal digits
(e.g. full-width `"１"`); the VERBATIM token (not the canonical int) rides the
tuple into `--gpus` and persistence. The shard CLI re-validates (Pattern 7),
so this is a cosmetic/determinism nit, not a correctness break.
**Fix (optional):** normalize via `indices.append(str(number))` after the
bounds check so the canonical decimal form persists.

### IN-02: GPU list sorts lexicographically at >= 10 GPUs (carried, iteration 1)

**File:** `tui/services/run_config.py:391` and `:279-281`
**Issue:** `tuple(sorted(set(indices)))` sorts strings, so at 10+ GPUs
`"10"` sorts before `"2"` (display order and the `--gpus` element order
permute vs the typed order). The house sorted-dedupe discipline is the
documented reason; the CLI stays the authority.
**Fix (optional):** `sorted(set(indices), key=int)` at both sites if the
permutation ever matters to dispatch_core's positional GPU assignment.

### IN-03: every probe failure mode renders the "nvidia-smi not installed" copy (carried, design-pinned)

**File:** `tui/services/gpu_probe.py:160-206`; `tui/strings.py:2028-2031`
**Issue:** D16-02 pins ONE absent outcome for missing binary / non-zero exit /
timeout / unparseable output, and `MON_GPU_ABSENT` says "not installed" — a
wedged driver renders the same copy. Design-pinned (one degradation shape,
never a fabricated diagnosis); listed for the record only.
**Fix:** none (a maintainer ruling would be needed to split the copy).

### IN-04: clearing the workers/GPUs field keeps the last-valid spec value, not the placeholder's promised default (carried, iteration 1)

**File:** `tui/screens/run_config.py:1760-1795` (`_compose_spec`)
**Issue:** an empty field contributes no partial, so `replace(self._spec, ...)`
retains the last-valid parsed value while the placeholder ("default: GPUs
0..workers-1") suggests the child default. The epochs/EBS idiom, deliberately
consistent; documented here for the record.
**Fix:** none short of a per-field "explicitly cleared" channel (rejected as
out of proportion in iteration 1).

### IN-05: stale `LNC_GATE_DISPATCH_LINE` comment still asserts the retired WR-03 semantics (NEW this iteration)

**File:** `tui/strings.py:1576-1589`
**Issue:** the comment block above `LNC_GATE_DISPATCH_LINE` still reads
"{gpus} is the typed list or the all({n}) resolution rule with the detected
count at preview time (auto-default #8 — the default resolves at LAUNCH, the
preview names the rule + live count, never a guess in place of data)". WR-03
(e0f4523) removed exactly that behavior — `gpus_display` is now `0..{workers-1}`
derived from the spec's workers alone, with no detection and no live count at
preview time (the fix updated `CFG_GPUS_DEFAULT`, the `RunSpec`/`GateSummary`
docstrings, and the tests, but missed this comment). The rendered copy itself
is correct (no `{n}` field exists in the constant); this is doc drift that
would mislead a maintainer editing the constant.
**Fix:**
```python
# ... {gpus} is the typed list or the child's OWN default
# resolution rule "0..{workers-1}" (dispatch_core binds the FIRST
# ``workers`` GPU indices, range(workers) — WR-03, phase-16 review);
# the default derives from the SPEC's workers alone, resolves at
# LAUNCH inside the child, and is never a resolved list in place of
# data (Pitfall 8) ...
```

---

_Reviewed: 2026-10-21T07:33:38Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (iteration 2 --auto re-review)_
