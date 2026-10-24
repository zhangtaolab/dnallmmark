---
phase: quick-261018-rze
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/screens/monitor.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pty_driver.py
autonomous: true
requirements: ["UX-slot5-cadence-stability", "REGRESSION-pty-lane"]
user_setup: []

estimate:
  tokens: 60000
  raw_tokens: 40000
  tasks: 3
  confidence: med

must_haves:
  truths:
    - "A steady 2s frontier tick over unchanged scan data performs ZERO widget writes: no ListView rebuild, no tab Label updates, no scan-note update, no focus call — the terminal stays byte-silent (the maintainer's 2026-10-18 19:57 flicker report is gone)"
    - "A tick with CHANGED progress updates ONLY the affected card's Label content in place (same ListItem objects, list_view.index untouched — the operator's cursor identity survives every steady tick)"
    - "Clicking a running card still opens the RunCellsModal (cells — {root} title) with no full-screen pre-modal writes"
    - "While any modal (or the min-size guard) is stacked above the monitor screen, cadence ticks render nothing beneath it; the next tick after dismissal refreshes"
    - "Graduation toasts still fire on observed running→terminal transitions (they run in on_monitor_screen_full_scanned BEFORE _render_all and precede the modal gate)"
    - "on_mount, revisit, tab switch, resize, and the L-language recompose still fully repaint (screen IS self on those paths; the recompose resets the render gates so the fresh widget tree repaints in the active language)"
    - "tests/tui/__snapshots__/monitor_running.svg and monitor_empty.svg remain byte-identical (content unchanged — this fix is traffic only); run_config.svg untouched; NEVER run make snapshot-update"
    - "Service layer zero-change: tui/services/sweep_monitor.py, sweep_launcher.py, and MonitorBackend's delegations are untouched"
  artifacts:
    - "tui/screens/monitor.py carrying the five render gates: (a) tabs content-gate + layout=False, (b) scan-note state-flip gate, (c) cards structure-signature gate + in-place Label updates over a shared _card_content builder, (d) _focus_active no-op when the target already holds focus, (e) _render_all early-return while another screen is stacked above"
    - "tests/tui/test_pilot_monitor.py extended with the four idempotence/suppression/focus unit pins"
    - "tests/tui/test_pty_driver.py extended with the quiet-cadence byte-silence pin and the click→RunCellsModal pin (fabricated running root via DNALLMMARK_TUI_STATE_DIR + monitor_roots.json)"
  key_links:
    - "_render_cards structure sig ← card roots identity/order + base_live + resume-note presence ONLY (never progress/scale text — a progress change must never trigger a rebuild)"
    - "_card_content ← the ONE content definition shared by the rebuild path (ListItem construction) and the in-place path (Label update), so the two paths can never drift"
    - "pty byte-silence pin ← all five gates together (any one missing re-admits the ~4.9K-char whole-region bursts every 2s)"
    - "modal gate ← app.screen identity check; graduation toasts and the _pending_rescan toast fire in the message handlers independent of _render_all"
    - "on_mount sentinel reset ← the L-toggle _rerender_screen mechanism (recompose rebuilds the widget tree, then re-invokes on_mount — stale sigs would leave fresh Labels empty)"
---

<objective>
Slot-5 monitor cadence flicker fix: eliminate the whole-region render churn on every 2s frontier tick and the click-path double full-screen write, surgically, in tui/screens/monitor.py only.

Maintainer live report 2026-10-18 19:57: clicking a running card in the Monitor's Running tab causes visible repeated flashing, then the RunCellsModal pops. Instrumented pty reproduction (40x120): every 2s tick performs ~3 full-region repaints (~4.9K chars each); while a modal is open the base screen keeps repainting under it (~7.6K chars x3 per tick); on click, 2 full-screen writes (6216 chars, 49ms apart) before the modal lands. The drill read is fast (20ms) and the modal logic is correct — the defect is pure render churn from five verified root causes (unconditional tab Label updates with textual 8.2.8's default layout=True, per-tick scan-note update, full ListView clear+re-append, unconditional .focus() after every scan render, and no modal suppression).

Purpose: the monitor must be visually still when the data is still — steady-state cadence ticks are byte-silent; changes paint only where they changed.

Output: gated render path in tui/screens/monitor.py (five gates + the shared _card_content extraction), four Pilot unit pins, two pty-lane pins (quiet-cadence byte-silence + click→modal), goldens untouched.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.claude/CLAUDE.md

# The fix surface and the test lanes
@tui/screens/monitor.py
@tests/tui/test_pilot_monitor.py
@tests/tui/test_pty_driver.py
@tests/tui/test_snapshots.py

# Probe evidence (read-only agent scratch, NOT repo files — cite, never import)
/tmp/tui-flicker/events.log       # the instrumented write log (the ~4.9K x3 bursts, the 6216-char click pair, the under-modal 7.6K churn)
/tmp/tui-flicker/drive.py         # the PROVEN pty recipe: fabricated root + monitor_roots.json + SGR click \x1b[<0;8;5M/\x1b[<0;8;5m at row 5 col 8 (40x120)

# Marker source
@tui/strings.py                   # MON_RUN_CELLS_TITLE en copy is the click-test's modal marker

Key probe-pinned facts (textual 8.2.8, verified in .venv):
- Static.update(content, *, layout=True) — layout=False is blessed in the docstring ("set to False if you are certain the size won't change"); single-line fixed-height Labels qualify.
- Static.content is the content read API (no .renderable — the 08-06 pin).
- app._rerender_screen (the L toggle): screen.recompose() rebuilds the compose tree (FRESH Labels, empty content) then re-invokes on_mount — see tui/app.py:1355.
- A no-manifest root with fresh file mtimes classifies SWEEP_RUNNING (newest mtime within STALE_GRACE_SECONDS=600) — tui/services/sweep_monitor.py full_scan branch; monitor_roots.json under the state dir ({"schema_version": 1, "roots": [abs]}) is the registration seam (manual_roots()).
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: The five render gates in tui/screens/monitor.py (tabs, scan-note, cards sig+in-place, focus no-op, modal suppression)</name>
  <files>tui/screens/monitor.py</files>
  <behavior>
    - Steady tick idempotence: a frontier/full render over unchanged card set, counts, and scanning state performs zero widget writes (tab Labels, scan note, card Labels, ListView structure, focus all gated).
    - Content-only change: a progress/stats/scale text change updates the affected card's existing Labels in place with layout=False; the ListItem objects and list_view.index are untouched.
    - Structural change (card set/order/base_live/resume-presence change): the existing clear+append+clamped-index-repin rebuild path runs verbatim.
    - Modal suppression: _render_all early-returns while app.screen is not self; graduation toasts (fired in on_monitor_screen_full_scanned before _render_all) still work; the next tick after dismissal refreshes.
    - Focus no-op: _focus_active skips .focus() when the intended target (ListView or DataTable) already holds focus.
    - Recompose safety: the L-toggle recompose (fresh widget tree + on_mount re-invocation) fully repaints in the active language — test_language_toggle_recompose_keeps_cadence_idempotent stays green unmodified.
    - Painted content is byte-identical to HEAD: test_snapshots.py monitor goldens compare green with zero SVG edits.
  </behavior>
  <precondition>Baseline green before the edit: .venv/bin/python -m pytest tests/tui/test_pilot_monitor.py tests/tui/test_snapshots.py tests/tui/test_pty_driver.py -q passes at HEAD (the two monitor SVGs are uncommitted worktree state pending maintainer D-03 review — they must pass as-is). Record sha256sum tests/tui/__snapshots__/monitor_running.svg tests/tui/__snapshots__/monitor_empty.svg now for the Task 3 identity check.</precondition>
  <action>
    Implement the five gates from the planning_context required fix (a)-(e) in tui/screens/monitor.py — SURGICAL: no service-layer edits, no _render_history/_set_table_rows changes (the History DataTable is display-gated on the Running tab and DataTable.update_cell already early-returns on equal values), no strings.py changes, no new imports beyond what the gates need:

    (a) _render_tabs (~1744): add a screen-local sentinel self._tabs_sig (init None in __init__ alongside the other render state). Sig = (running_count, history_count, self._active_tab). When the sig is unchanged, return WITHOUT touching either tab Label. When it changed, build both Texts exactly as today (accent/dim logic byte-identical) and pass layout=False to each Label.update — single-line labels of fixed height, the textual-blessed case. Store the sig after updating.

    (b) _render_scan_note (~1734): track self._scan_note_shown (init None). Update the note ONLY on a state flip: the False→True flip calls note.update(S.MON_SCANNING, layout=False) then display=True; the True→False flip only sets display=False (as today). Repeated renders at the same _scanning value perform no update call. The .display assignments stay as-is (textual already change-guards display).

    (c) _render_cards (~1833) + the shared content builder:
    - Extract _card_widget's body into _card_content(self, card) -> "list[tuple[str, Text]]" returning the ORDERED (css-classes, Text) pairs the card renders today: name, scale, then — only when base_live — total bar, current-cell line, and (only when resume > 0) the resume note, then the worker rows. _card_widget becomes the thin constructor: ListItem(Vertical(*[Label(text, classes=cls) for cls, text in self._card_content(card)], classes="mon-card")) — the rebuild path's widget tree stays byte-identical (the goldens depend on it).
    - Structure signature in _render_cards: sig = tuple((tuple(card.roots), card.roots[0] == card.base, self._resumes.get(card.roots[0], 0) > 0) for card in cards) — STRUCTURE ONLY (roots identity and order, base_live, resume-note presence — the three things that change the LABEL COUNT); NEVER progress/scale text (scale presence changes content, not label count). Store self._cards_sig (init None).
    - Unchanged sig path (in-place refresh): do not touch the ListView structure or its index. For each card position i, walk the existing ListItem's Label children in DOM order (list_view.children[i].query(Label)); rebuild content = self._card_content(card); when the label count matches (a mismatch means a sig bug — fall back to the rebuild path defensively rather than crash), update ONLY the labels whose content changed: compare str(fresh_text) against str(label.content) (Static.content, the probe-pinned read API) and call label.update(fresh_text, layout=False) solely on inequality — a steady tick with unchanged data performs ZERO widget writes. Refresh self._card_order in place.
    - Structural-change path: the EXISTING clear + append-per-card + clamped index re-pin behavior verbatim, then store the new sig.

    (d) _focus_active (~1910): in BOTH branches, fetch the target widget and skip .focus() when it already holds focus — the ListView branch: lv = query_one("#mon-cards", ListView); if lv is not self.focused: lv.focus() (guarded by the existing _card_order condition). The DataTable branch: dt = query_one("#mon-history", DataTable); if dt is not self.focused: dt.focus(). The set_focus(None) empty-tab degradations keep their existing elif self.focused is not None shape.

    (e) _render_all (~1721): after the existing `if not self.is_running: return` guard, add `if self.app.screen is not self: return` — a modal or the min-size guard is stacked above; the base pass is suppressed (graduation toasts fire in on_monitor_screen_full_scanned BEFORE _render_all and are unaffected; the next 2s tick after dismissal refreshes — accepted per the required fix).

    (f) LOAD-BEARING interplay — reset the sentinels in on_mount: set self._tabs_sig = None, self._scan_note_shown = None, self._cards_sig = None at the top of on_mount (before self._render_all()). WHY: the L-language toggle's _rerender_screen (tui/app.py:1355) calls screen.recompose() — which rebuilds the compose tree with FRESH empty Labels — then re-invokes on_mount; without the reset, the unchanged sigs would gate away the updates and the recomposed tabs/cards would render empty/stale-language (test_language_toggle_recompose_keeps_cadence_idempotent pins this).

    Keep the module docstring's design-choice section current: add a short paragraph documenting the five cadence gates (261018-rze) in the file's established bilingual-comment style. Do NOT modify the MON_ constants, the cadence workers, the message handlers' state updates, or any modal.
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest tests/tui/test_pilot_monitor.py tests/tui/test_snapshots.py tests/tui/test_pty_driver.py -q</automated>
  </verify>
  <done>All five gates landed in tui/screens/monitor.py; the full existing monitor Pilot suite (58+ tests incl. the L-toggle recompose and min-size-modal round trip), the snapshot goldens, and all 6 existing pty tests pass UNMODIFIED; sha256 of both monitor SVGs unchanged from the pre-task recording; ruff clean on the file (uv run --group dev ruff check tui/screens/monitor.py).</done>
</task>

<task type="auto">
  <name>Task 2: Pilot-lane unit pins — steady-tick idempotence, in-place content update, modal suppression, focus no-op</name>
  <files>tests/tui/test_pilot_monitor.py</files>
  <action>
    Extend tests/tui/test_pilot_monitor.py with four async tests over the EXISTING FakeMonitorService/_summary/_stats/_row fixtures (asyncio auto mode; follow the file's docstring/naming/bilingual-comment conventions; cite 261018-rze in the module docstring's pin list):

    (1) Steady-tick idempotence: one running root fixture (scripted scan + stats + progress), open the monitor, wait for the card. Capture the ListView's ListItem identity (list_view.children[0]) and install counting spies (unittest.mock.patch.object(..., wraps=...) or equivalent instance wrappers) on the ListView's clear method and on BOTH tab Labels' update methods. Drive a repeat render (call screen._render_all() directly — the cadence handlers land there; a second call after no state change is exactly the steady tick). Assert: the clear spy count is 0, both tab update spy counts are 0, and the ListItem object identity is unchanged.

    (2) In-place content update on progress change: same fixture; mutate the fake's scripted stats (e.g. done 3→4 with total 10, or a changed CellProgress percent), call screen._render_all(); assert the card's visible label text contains the NEW fraction (e.g. "4/10") and the ListItem identity is still the captured object (the clear spy stays at 0 — content changed, structure did not).

    (3) Modal-open suppression: push a dummy ModalScreen (define a minimal local ModalScreen in the test, or reuse an existing lightweight one), spy the ListView clear + tab Label updates + the card Labels' updates, call screen._render_all() — assert every spy count is 0. Pop the modal, change the fake's stats, call screen._render_all() again — assert the update lands (rendering resumed; the card text reflects the change).

    (4) Focus no-op when already focused: focus #mon-cards, wrap its focus method with a spy, call screen._focus_active() — assert not called. Then screen.set_focus(None) and call again — assert focus IS re-applied (the existing steal-back behavior preserved). Mirror both assertions for the DataTable branch with the History tab active and a populated history fixture.
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest tests/tui/test_pilot_monitor.py -q</automated>
  </verify>
  <done>Four new Pilot pins green: steady tick performs zero structural/tab writes with identity preserved; changed progress updates card label content in place; _render_all is inert under a stacked modal and resumes after dismissal; _focus_active no-ops when the target already holds focus (both branches); the pre-existing 58+ monitor tests stay green unmodified.</done>
</task>

<task type="auto">
  <name>Task 3: pty-lane pins — quiet-cadence byte-silence + click→RunCellsModal — plus full gates and golden byte-identity</name>
  <files>tests/tui/test_pty_driver.py</files>
  <precondition>Tasks 1-2 green. The fabricated-root recipe is PROVEN at /tmp/tui-flicker/drive.py (read it before coding); the click coordinates row 5 col 8 are calibrated to the 40x120 _spawn_tui dimensions (the card name paints at row 5 per events.log).</precondition>
  <action>
    Extend tests/tui/test_pty_driver.py with two tests and one helper param (never weaken existing members — test_monitor_renav_renders_every_visit stays byte-UNMODIFIED, F1 load-bearing):

    (0) Helper: extend _spawn_tui with an optional manual_roots=() parameter — when non-empty, write monitor_roots.json ({"schema_version": 1, "roots": [str, ...]}) into the per-test state dir AFTER its mkdir and BEFORE pexpect.spawn (the drive.py recipe; manual_roots() resolves entries expanduser().resolve()). Existing call sites unchanged by the default.

    (1) test_monitor_quiet_cadence_is_byte_silent (the flicker pin): fabricate a running root under tmp_path — {tmp}/runs/root1/plant-dnabert-6mer/GUE__virus_species_4/seed_9527/checkpoint-120/trainer_state.json with body {"global_step": 120} and fresh mtimes (the no-churn-thread design: the no-manifest branch classifies the root SWEEP_RUNNING via newest-mtime within STALE_GRACE_SECONDS=600, and the static tree keeps every tick's content identical). Spawn via the extended helper with that root. Boot, send "5", expect the card marker (the root dir name "root1" — the card name label paints Path(base).name). Drain: expect pexpect.TIMEOUT over ~3s to consume the initial paint. THEN the assertion window: child.expect(pexpect.TIMEOUT, timeout=5.5) — covering 2+ frontier ticks — and assert not child.before (STRICT byte-silence: zero new terminal bytes across the window). Pre-fix this fails: the ~3x4.9K-char bursts arrive every 2s (events.log evidence). finally: child.close(force=True) per lane convention.

    (2) test_click_running_card_opens_run_cells_modal (the click-path pin): same fabricated-root setup; after the card paints and a short drain, send the SGR mouse pair — child.send("\x1b[<0;8;5M") then child.send("\x1b[<0;8;5m") (press + release at col 8 row 5 — SGR encodes button;col;row — the first card row at 40x120, the proven drive.py coordinates). Expect the RunCellsModal title marker within the nav timeout: the en copy of MON_RUN_CELLS_TITLE rendered as the border title, i.e. the literal "cells — root1" (verify the em-dash glyph against tui/strings.py MON_RUN_CELLS_TITLE and add the marker constant at the module top beside the other en markers). finally: child.close(force=True).

    Extend the module docstring's finding list with the 261018-rze entry (maintainer live report; the five verified root causes; the byte-silence + click pins) and note the runtime budget (~2 spawns x ~9s, in line with the lane's members).

    Then run the full gates at repo root: .venv/bin/python -m pytest tests/tui -q (KNOWN environment collateral: test_storage_overview_defaults_mirror_real_consumers fails ONLY when pipeline/logs exists because the maintainer's live run is writing it — document in the SUMMARY, do NOT fix here), make lint, make typecheck, and the golden byte-identity proof: sha256sum tests/tui/__snapshots__/monitor_running.svg tests/tui/__snapshots__/monitor_empty.svg matches the Task 1 pre-task recording EXACTLY (never run make snapshot-update — the pair is the uncommitted D-03 handoff; run_config.svg likewise untouched). git status must show ONLY tui/screens/monitor.py + the two test files as this task's diff (plus whatever the orchestrator's bookkeeping adds).
  </action>
  <verify>
    <automated>.venv/bin/python -m pytest tests/tui/test_pty_driver.py -q && make lint && make typecheck && sha256sum tests/tui/__snapshots__/monitor_running.svg tests/tui/__snapshots__/monitor_empty.svg</automated>
  </verify>
  <done>pty lane at 8 members green (6 existing unmodified + quiet-cadence byte-silence + click→RunCellsModal); full tests/tui suite passes except the documented pipeline/logs environment-collateral member only; ruff + ty green; both monitor golden sha256s identical to the pre-task recording; git diff confined to tui/screens/monitor.py and the two test files.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| filesystem → TUI | scan/tee/record reads over operator-named paths (existing seams, untouched) |
| pty test child → host | the pty lane spawns the real console on OS ptys with per-test tmp state roots (existing discipline) |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-rze-01 | Tampering | pty-lane fabricated root | low | mitigate | The fabricated running root lives under pytest tmp_path and registers through DNALLMMARK_TUI_STATE_DIR/monitor_roots.json — the spawned console never touches the maintainer's real state or roots (the 10-07 hermeticity idiom, reused verbatim) |
| T-rze-02 | Denial of Service | gated render path | low | mitigate | Gates are pure in-memory comparisons on already-arrived messages; the cadence stays worker-off-loop (D-09 groups untouched); the defensive label-count fallback routes any sig bug to the proven rebuild path, never a crash |
| T-rze-03 | Information Disclosure | render gating | low | accept | Presentation-only change over validated service outputs; no new data sources, no network, no persistence changes |
| T-rze-SC | Tampering | npm/pip/cargo installs | high | mitigate | Zero new dependencies (pexpect is an existing dev-group member; Label/Static/ListView/DataTable are existing textual widgets) — no install tasks exist in this plan |
</threat_model>

<verification>
- .venv/bin/python -m pytest tests/tui -q — every member green EXCEPT test_storage_overview_defaults_mirror_real_consumers when pipeline/logs exists (environment collateral from the maintainer's live run — documented, not fixed here)
- .venv/bin/python -m pytest tests/tui/test_pty_driver.py -q — 8 members: the 6 existing pins byte-unmodified (renav/tab-switch/empty-route among them) + the 2 new pins
- make lint && make typecheck — the standing ruff + ty gates green
- sha256sum tests/tui/__snapshots__/monitor_running.svg tests/tui/__snapshots__/monitor_empty.svg — byte-identical to the pre-task recording (the fix is traffic only; the uncommitted D-03 pair is preserved exactly); run_config.svg untouched
- git status --porcelain — the task diff is confined to tui/screens/monitor.py, tests/tui/test_pilot_monitor.py, tests/tui/test_pty_driver.py
</verification>

<success_criteria>
- The flicker is gone at the terminal-byte level: a steady frontier tick over unchanged data writes zero bytes (pty-pinned), a click opens the RunCellsModal without pre-modal full-screen writes (pty-pinned), and the base screen stays still under an open modal.
- Content-change ticks paint only the changed labels in place; structural changes take the proven rebuild path with cursor re-pin; focus churn is gated.
- Every pre-existing test (Pilot, pty, snapshots) passes unmodified; the service layer and strings are untouched; goldens byte-identical; ruff + ty green.
</success_criteria>

<output>
Create `.planning/quick/261018-rze-slot-5-monitor-cadence-flicker-fix-every/261018-rze-SUMMARY.md` when done
</output>
