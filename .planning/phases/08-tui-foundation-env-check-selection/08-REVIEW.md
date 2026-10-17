---
phase: 08-tui-foundation-env-check-selection
reviewed: 2026-10-17T00:00:00Z
depth: quick
files_reviewed: 12
files_reviewed_list:
  - tui/__main__.py
  - tui/app.py
  - tui/screens/data_manager.py
  - tui/screens/env_check.py
  - tui/screens/monitor.py
  - tui/screens/run_config.py
  - tui/screens/selection.py
  - tui/screens/wizard.py
  - tui/services/download_queue.py
  - tui/services/run_config.py
  - tui/services/settings.py
  - tui/services/sweep_launcher.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 8: Code Review Report (incremental — live-feedback round 601aa51..HEAD)

**Reviewed:** 2026-10-17
**Depth:** quick (pattern scans + per-file read, with targeted deep-dive on the ctrl+c/Q interception seams, kill channel, ETA gates, and i18n registry per the round's scope brief)
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Scoped incremental review of the maintainer live-feedback commits since `601aa51`
(hhx i18n re-derivation + registry injectivity + zenodo rollback; poa slot-4
cursor/scroll anchor + launch-confirmation task list; v0z quit-confirm chain;
vxr entry ETA + slot-5 kill; cdr ctrl+c any-focus exit + modal-stacking guard;
dnr Y/N prominence). The on-disk state is current; the diff was the primary
scope.

No BLOCKER found. The high-risk seams the round touched were verified against
the installed textual 8.2.8 and came back CORRECT (details below): the
`on_event` ctrl+c intercept's modal-chain inertness map, the CDR-4 stacking
guard, the ctrl+q priority mirror, the zenodo persist rollback, the ETA
validity gates, and the i18n keycap registry. Three warnings and three info
items survive — all in the cross-module interaction class the round's
test-first gates would not catch.

Previously reviewed and fixed in this round (NOT re-derived here): the CR-01
frozen-copy family, prior WR-01..04 / IN-01..03, the env_smoke cluster.

## Warnings

### WR-01: The ctrl+c intercept silently kills the focused-Input copy binding on every base screen

**File:** `tui/app.py:1144-1149`
**Issue:** The 261017-cdr `on_event` intercept consumes `ctrl+c` at the App
level whenever the top screen is non-modal — before `super().on_event` forwards
the key to the focused widget. Textual 8.2.8's `Input` binds
`ctrl+c,super+c -> copy` (verified: `.venv/.../textual/widgets/_input.py:139`),
so with a base-screen Input focused (the slot-2 filter, the slot-4 filter /
params / dir inputs) a ctrl+c with selected text now opens the quit confirm
instead of copying. The on_event docstring documents the q/Q typing semantics
and the inherited `help_quit` default but never mentions the Input copy
binding it shadows. It is also inconsistent by surface: inside modals
(`E2PhraseModal`'s input, `PathInputModal`, the wizard's inputs) the key
delegates and copy still works — the loss is base-screen-only, i.e. exactly
the surfaces where the maintainer asked for any-focus exit, so the feature
itself is right; the collateral is undocumented and asymmetric.
**Fix:** Either delegate when the focused widget is an `Input` with a
non-empty selection (`if isinstance(self.focused, Input) and
self.focused.selection: await super().on_event(event)` before the intercept
consumes), or record the deviation in the `on_event` docstring and the
`APP_CTRLC_LABEL` help copy so the behavior is designed, not accidental.

### WR-02: ExitModal `[k]` runs `kill_sweep` serially on the event loop — up to kill_grace × N roots of frozen UI

**File:** `tui/app.py:250-254` (with `tui/services/sweep_launcher.py:900-907`)
**Issue:** `ExitModal.action_kill_quit` calls `self._launcher.kill_sweep(root)`
for every live root directly in the modal action — on the event loop. Each
call SIGTERMs, then polls every 50 ms up to `DEFAULT_KILL_GRACE_SECONDS = 2.0`
before SIGKILL; with the WR-05 multi-root form the freezes stack serially
(N live roots that ignore SIGTERM → N × 2 s of an unresponsive console before
exit). The monitor's own `[k]` channel — added in the same vxr round and
landing the same launcher call — deliberately enshrines the opposite
discipline (`monitor.py:1530-1540`: "blocks up to the kill grace polling the
process group — NEVER on the event loop", dispatched through the exclusive
`mon-kill` worker). 261017-dnr then makes the `[k]` keycap `show=True`,
advertising the path more prominently than before. Impact is bounded (the app
exits immediately after), but it is a frozen frame on the exact surface the
round made more visible, and it contradicts the kill-channel discipline
documented ten lines away in the sibling screen.
**Fix:** Dispatch the kill fan-out through a one-shot thread worker (or
`asyncio.to_thread`) and call `self.app.exit()` in its completion handler; or
pass a reduced grace on the exit path (`kill_grace` is already injectable per
call site via the service seam).

### WR-03: Mixed live-root exit drops the attached CLI-launched sweep from the ExitModal

**File:** `tui/app.py:1097-1109`
**Issue:** `action_quit` enters the live-sweep branch on `roots or
attached_running`, but the single-root form selects `root = roots[0] if roots
else attached_root`. When the launcher holds exactly ONE live TUI-spawned root
AND the monitor's attached root is a DIFFERENT running sweep (CLI-launched —
the exact case `attached_running` exists to catch), the attached root is
silently discarded: the ExitModal names and acts on only the TUI root, so
`[k] kill & exit` leaves the CLI sweep running with no notice, and `[enter]
detach & exit` exits while an unnamed sweep keeps occupying the GPU. The
rewritten v0z/cdr docstring codifies the WR-05 guarantee ("the modal carries
EVERY live root … no sweep survives a kill-and-quit the operator believed
terminal"), which this corner violates. The line predates the diff, but this
round rewrote the legs and the contract text around it, making the gap
load-bearing.
**Fix:** In the single-root form, when `attached_running and attached_root not
in roots`, use the multi-root form (or append the attached root) so the modal
names and acts on both:
```python
if len(roots) > 1 or (attached_running and roots and attached_root not in roots):
    combined = tuple(roots) + ((attached_root,) if attached_running and attached_root not in roots else ())
    self.push_screen(ExitModal(roots=combined, ... MULTI-form ...))
```

## Info

### IN-01: `selection.apply_queue_progress` still stores before the kind guard — the asymmetric twin of this round's IN-01 slot-3 fix

**File:** `tui/screens/selection.py:1607-1612`
**Issue:** The same round moved slot-3's live-dict pops/stores around the
KIND_MODEL ignore guard (`data_manager.py:789-826`, IN-01 quick-261016-hhx),
but slot-2's twin still does `self._live_percents[key] = percent;
self._live_speeds[key] = speed` BEFORE the KIND_MODEL/state check, so dataset
download ticks accumulate dataset keys in the slot-2 dicts (bounded by the
~60-key registry; values are never read for non-model keys and are popped at
the next event for the key — hygiene residue, not a render bug).
**Fix:** Mirror the slot-3 ordering: perform the `_live_model_entries()` /
state check first and store only for passing (model, downloading) ticks.

### IN-02: `GateWorkerError` staleness filter collides across the `_gate_stage_id` / `_gate_launch_id` number spaces

**File:** `tui/screens/run_config.py:2131-2135` (pre-existing handler, unchanged by the diff)
**Issue:** A gate worker's late error is dropped only when its id differs from
BOTH counters. A superseded gate-stage error whose id numerically equals the
CURRENT `_gate_launch_id` (both counters increment independently from 1)
passes the filter and surfaces a spurious "launch failed" toast right after a
successful launch, and resets `_gate_active = False` (harmless today — the
flag is already released pre-modal).
**Fix:** Tag `GateWorkerError` with which counter it belongs to (or use one
monotonic id space for the whole pipeline) and compare against that counter
only.

### IN-03: env_check remount can transiently render the stale pre-refresh cache outcome

**File:** `tui/screens/env_check.py:477-487` + `env_check.py:523`
**Issue:** `action_refresh` clears `_results` synchronously but
`_check_in_flight = True` is set inside the worker body (worker thread). An
L-toggle remount landing in that window sees `_results` empty and the flag
still False, consults the same-day cache, and renders the pre-refresh outcome
until the fresh run's completion overwrites it. Self-healing, no kernel
restart (the worker's run-id-tagged posts land on the rebuilt rows) — a
transient stale verdict line only.
**Fix:** Set `_check_in_flight = True` synchronously in `action_refresh`
(before dispatching `run_full_check`), mirroring the app's
`kick_download_queue` busy-flag discipline.

## Verified-correct (adversarial checks that came back clean)

- **Modal-chain inertness map (cdr)** — verified against the installed
  textual 8.2.8: `Screen._modal_binding_chain`
  (`.venv/.../textual/screen.py:449-456`) cuts the chain AT the modal, so
  plain `q` and the inherited non-priority `ctrl+c -> help_quit`
  (`.venv/.../textual/app.py:463`) are unreachable under every modal; the
  priority `ctrl+q` path (`App.on_event` → `_check_bindings(priority=True)`
  over the full `_binding_chain`) does fire over modals, which is exactly
  what the CDR-4 `isinstance(self.screen, (ExitModal, QuitConfirmModal))`
  guard absorbs. No stacking path found; `ctrl+c` under modals is inert as
  documented.
- **No dead Q paths from the withdrawn vxr intercept** — grep over
  `tui/` finds only docstring mentions; no `key == "Q"` handling, no
  `APP_Q_LABEL` remnant.
- **Zenodo persist rollback (hhx WR-02)** — `enqueue_zenodo`
  (`download_queue.py:1585-1590`) mirrors the dataset lane exactly: under
  `self._lock`, `_persist_locked()` returns `str | None` (None = success),
  `self._entries.pop()` removes the just-appended (last) entry. Correct.
- **ETA validity gates (vxr VXR-1)** — `_eta_from_checkpoint_pair`
  (`sweep_monitor.py`): mtime ties (`mtime_new <= mtime_old`), checkpoint
  step ties (`step_old >= step`), non-positive deltas, and `max_steps <=
  step` all degrade to None; both mtimes come from the same filesystem (no
  cross-clock skew source); the two-newest checkpoint tracking handles
  out-of-order suffixes. The monitor's `_entry_progress_cell` renders
  `format_eta` output (single leading `≈`) with `.lstrip("≈")` on the
  stats-line path only — no double-marker shapes.
- **i18n inventory** — all 350 distinct `S.*` references across the 12
  in-scope files resolve in `tui/strings.py` (scripted check); the new
  keycap constants (`LNC_EXIT_DETACH/KILL_KEYCAP`, `MON_KILL_KEYCAP`,
  `MON_FAILURES/LOG_KEYCAP`, `LNC_EXIT_CONFIRM_YES/NO`,
  `LNC_GATE_CONFIRM_YES`) are registry entries, so the L-toggle remap and
  the persisted-zh boot remap translate them; `QuitConfirmModal` is in
  `_APP_LOCAL_BINDING_SCREENS`; the bolded `[Y]/[N]/[y]/[n]/[enter]/[k]/[esc]`
  tokens exist in both language forms of every message that highlights them
  (including `LNC_EXIT_MESSAGE_MULTI` and the lowercase-`[y]`
  `MON_RERUN_CONFIRM`).
- **Kill-channel keying** — monitor `k` verifies `str(attached_root)` against
  `live_sweeps()` (both sides `Path(...).resolve()`-based; `note_launch` and
  `_spawn` share the `resolve_dirs().output_root_abs` basis), and `kill_sweep`
  drops the registry entry so a second `k` correctly reads
  `MON_KILL_UNAVAILABLE`.
- **Quick-mode pattern scans** — no hardcoded secrets, no
  eval/exec/shell=True, no debug artifacts, no new silent bare-except blocks
  beyond the documented blind-except seams; all 12 files byte-compile.

---

_Reviewed: 2026-10-17T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
