---
phase: quick-261018-rze
plan: 01
status: complete
subsystem: tui-monitor
tags: [monitor, render-gates, flicker, pty-lane, pilot]
commits:
  - c121f1d
  - 2498540
  - 18fd8db
  - d43bfa9
files:
  - tui/screens/monitor.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pty_driver.py
goldens_untouched:
  monitor_running_svg: 65e0e62bc52fd5636427c139caa0e95242866111dc7b84f1700412039aee899c
  monitor_empty_svg: 5ce81ea23240aadc3ee3007a94a37d6f5508f6d4179cd6eb8d96a45c87f4c6d9
  run_config_svg: c7e144589480e7fd7e7ae2cac00598906657849d68316238764e4a32f50da2d3
---

# quick-261018-rze: slot-5 monitor cadence flicker fix — summary

The Monitor's 2s cadence is now render-gated end to end: a steady tick
over unchanged data writes ZERO terminal bytes (pty-pinned), a changed
progress paints only the affected card's Labels in place, the base
surface stays still under modals, focus churn is gated, and a card
click opens the RunCellsModal. All pre-existing tests pass unmodified;
the service layer, strings, modals, and goldens are untouched.

## Task 1 — the render gates in tui/screens/monitor.py

**Landed (commit c121f1d):** the five gates exactly as planned —
(a) `_render_tabs` content-gate on `(running_count, history_count,
_active_tab)` with `layout=False` updates; (b) `_render_scan_note`
state-flip gate (`_scan_note_shown`); (c) `_card_content` extracted as
the ONE shared `(classes, Text)` builder, `_card_widget` the thin
constructor, `_render_cards` gated on the structure signature
(roots identity/order, base_live, resume-note presence — never
progress/scale text) with the in-place Label refresh path and the
defensive label-count fallback to the rebuild path; (d) `_focus_active`
no-ops when the target already holds focus (both branches); (e)
`_render_all` early-returns while `app.screen is not self`; (f)
`on_mount` resets all sentinels so the L-toggle recompose fully
repaints in the active language. Module docstring documents the gates.

**Test evidence:** baseline precondition green before the edit
(`77 passed in 48.22s` over test_pilot_monitor + test_snapshots +
test_pty_driver); post-edit Task 1 verify `77 passed in 47.51s`;
ruff clean on the file; both monitor golden sha256s byte-identical to
the pre-task recording.

## Task 2 — the four Pilot unit pins

**Landed (commit 2498540):** `test_steady_tick_performs_zero_widget_writes`
(clear/tab-update/scan-note/card-label/focus spies all zero, ListItem
identity preserved), `test_progress_change_updates_card_labels_in_place`
(fake stats advanced done 3→4/10, driven through the real
`_tick_frontier` worker→message→render chain; "4/10" paints, clear spy
0, index untouched), `test_render_all_inert_under_modal_and_resumes_after`
(dummy ModalScreen stacked; every spy zero; post-dismiss tick lands
"5/10"), `test_focus_active_noops_when_target_already_focused` (both
branches; re-apply after `set_focus(None)` preserved).

**Test evidence:** `64 passed in 37.84s` (60 prior unmodified + 4 new);
ruff clean.

## Deviation fix — the sixth gate (commit 18fd8db)

The plan's Task 1 premise "DataTable.update_cell already early-returns
on equal values" does NOT hold on textual 8.2.8 — `update_cell` calls
`self.refresh()` unconditionally, so the display-gated History table
was dirtied 8x per steady tick and the compositor repainted the WHOLE
card region anyway (~4.9K chars per tick, confirmed by an instrumented
probe logging `Widget.refresh`/`LinuxDriver.write`/`os.write` against a
fabricated static running root). Minimal adjustment, same file, same
design language: `_render_history` now gates on a rendered-rows
signature (root, state, badge, done/total, mtime — every input the
cells render) with the same `on_mount` reset; an unchanged history
performs zero table work. `_set_table_rows` itself is untouched.

## Task 3 — the pty-lane pins + full gates

**Landed (commit d43bfa9):** `_spawn_tui(manual_roots=...)` writes
`monitor_roots.json` into the per-test state dir (the drive.py
recipe); `_fabricate_running_root` builds the static
model/task/seed/checkpoint tree (no-manifest branch classifies
SWEEP_RUNNING via fresh mtimes, no churn thread);
`test_monitor_quiet_cadence_is_byte_silent` and
`test_click_running_card_opens_run_cells_modal` (real SGR press+release
at col 8 row 5; expects the "cells — root1" border title, em dash
verified against `MON_RUN_CELLS_TITLE`). Module docstring carries the
261018-rze finding entry and the updated 8-spawn runtime budget.
`test_monitor_renav_renders_every_visit` and every other existing
member are byte-unmodified.

**Non-vacuity proof:** with the pre-fix `monitor.py` (ff78622) swapped
in, the byte-silence pin FAILS (`1 failed in 9.19s`); with the gates it
passes.

**Test evidence:**
- `.venv/bin/python -m pytest tests/tui/test_pty_driver.py -q` →
  `8 passed in 16.83s`
- `.venv/bin/python -m pytest tests/tui -q` →
  `1 failed, 1221 passed in 307.56s (0:05:07)` — the ONLY failure is
  `tests/tui/test_services_run_config.py::test_storage_overview_
  defaults_mirror_real_consumers`, the DOCUMENTED environment
  collateral (the maintainer's live GPU run is writing `pipeline/logs/`
  right now; the test asserts a no-logs premise). Out of scope per the
  standing constraint — not fixed, not touched.
- ruff (tests/ + tui/, superset of the changed files) →
  `All checks passed!`; `ty check` → `All checks passed!`
  (run via `.venv/bin` directly — `uv run` is forbidden on this box,
  it strips the editable dnallm install).
- Golden byte-identity: `monitor_running.svg`
  `65e0e62b...aee899c`, `monitor_empty.svg`
  `5ce81ea2...87f4c6d9` — identical to the pre-task recording;
  `run_config.svg` `c7e14458...f50da2d3` untouched. `make
  snapshot-update` was never run; the three SVGs remain in their
  pre-existing modified-uncommitted D-03 handoff state.
- `git status`: the task diff is confined to `tui/screens/monitor.py`,
  `tests/tui/test_pilot_monitor.py`, `tests/tui/test_pty_driver.py`.

## Deviations from plan

1. **[Rule 1 — bug in a planning premise] The sixth gate (history
   rows signature).** Found during Task 3's pty verification: textual
   8.2.8's `DataTable.update_cell` refreshes unconditionally, so the
   plan's "no `_render_history` changes needed" was unsound — the
   hidden table's 8 refreshes/tick repainted the whole card region.
   Fix: signature gate in `_render_history` (commit 18fd8db), still
   monitor.py-only, documented in the module docstring.
2. **[Test-semantics adjustment] The byte-silence assertion.** The
   plan's literal `assert not child.before` after
   `expect(pexpect.TIMEOUT)` can never hold: pexpect's `_before`
   buffer resets only on a real match/EOF, so consecutive TIMEOUT
   expects report CUMULATIVE data since the last match (verified
   against pexpect's `expect.py`, and empirically — raw OS-level
   reads during the window return 0 new bytes while `before` still
   holds the initial paint). The pin asserts `before` is
   byte-IDENTICAL to the drain snapshot — same intent, zero new
   bytes — and its failure on pre-fix code proves it bites.
3. **[Minor] Task 1 carries `tdd="true"` but the plan's own structure
   places every test in Tasks 2-3** (Task 1's verify explicitly runs
   the existing suites UNMODIFIED). Executed per the plan's task
   order; the pins landed one task later than the implementation.
4. **[Minor] The focus pin needed `await pilot.pause()`** after the
   re-apply `_focus_active()` call — `Widget.focus()` lands via
   `app.call_later` (textual 8.2.8), so `screen.focused` asserts only
   after an event-loop turn.

## Known stubs

None. No skipped tests, no unrun verifies, no TODOs left behind.

## Self-Check: PASSED

- Files: `tui/screens/monitor.py`, `tests/tui/test_pilot_monitor.py`,
  `tests/tui/test_pty_driver.py` — all present and committed.
- Commits c121f1d, 2498540, 18fd8db, d43bfa9 — all ancestors of HEAD
  on `autorun`; no attribution trailers on any of them.
- Working tree carries only the three pre-existing modified-uncommitted
  SVGs (the D-03 handoff, byte-identical) and the orchestrator-owned
  `.planning/` artifacts.
