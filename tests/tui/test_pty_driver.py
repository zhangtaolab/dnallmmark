"""
test_pty_driver.py — the permanent real-pty regression lane
(261018-08g, SOAK batch).

WHY this lane exists: three findings from the 2026-10-18 00:09 human-
simulation soak report (``.planning/quick/261018-08g-.../SOAK-REPORT.md``)
reproduce ONLY under a real pty driver and are structurally invisible to
every in-process Pilot test (``run_test`` drives the app in-process, so
textual's driver/render layer — the exact component that broke — never
runs):

- F1 dead-5: after ONE visit to slot 5, every later press of 5 switched
  the screen stack but the render layer NEVER repainted (textual 8.2.8
  ``switch_screen`` -> ``_replace_screen`` awaits ``remove()`` on the
  outgoing cached instance; re-registering a removed instance never
  repaints). Pilot could not see it; a real pty reproduced it 3/3.
- F3 quit traps: uppercase Y/N on the confirm modals left the process
  alive with the modal up (the displayed copy advertises [Y]/[N]).
- F5 gate visibility: the slot-4 Enter refusal renders within ~1.5s in
  a clean session (the soak's "blank screen" observation did NOT
  reproduce; this lane pins the honest render).
- 261018-rze (the cadence flicker): the maintainer's live 2026-10-18
  19:57 report — clicking a running card flashed repeatedly before the
  RunCellsModal popped, and the instrumented probe
  (``/tmp/tui-flicker/events.log``) measured ~3 whole-region repaints
  (~4.9K chars each) on EVERY 2s frontier tick, ~7.6K x3 per tick
  beneath an open modal, and 2 full-screen writes (6216 chars, 49ms
  apart) on the click path. Five verified root causes (unconditional
  tab Label updates with layout=True, the per-tick scan-note update,
  the full ListView clear+re-append, the unconditional post-scan
  ``.focus()``, no modal suppression) are gated in
  ``tui/screens/monitor.py``; the two pins below hold the
  terminal-byte contract: byte-silence across 2+ steady ticks and the
  click -> RunCellsModal landing.

Design (probe-pinned at planning time): each test spawns the REAL
console (``sys.executable -m tui``) on an OS pty via pexpect —
pexpect-only, NO pyte, NO new dependencies (pexpect has been an
approved dev-group member since 261017-eea). Assertions read NEW bytes
from the read pointer via ``child.expect`` (it only matches output
arriving after the prior consume — exactly the dead-5 signature: on the
bug, the second visit emits no monitor bytes and the expect times out).
Hermeticity (the 10-07 queue-lane idiom): DNALLMMARK_TUI_STATE_DIR and
DNALLMMARK_TUI_CONFIG_DIR point at per-test tmp dirs — the spawned
console can never touch the maintainer's real state, queue, or
run_config.json (T-08g-02). The spawned console defaults to ENGLISH
(the committed strings default; a fresh tmp state dir carries no
persisted language file), so every marker below is the en copy.

Runtime budget: EIGHT spawns at roughly 8-10s each (the 08g trio, the
kvj tab pair, and the 261018-rze flicker pair — the byte-silence pin
alone spends ~9s of bounded windows) — acceptable next to the slow
lane's ~80s member; every read is bounded by an explicit timeout and
``close(force=True)`` in a finally so a wedged child can never hang
``make test`` (T-08g-01). CI-safe: plain pexpect over a pty, no
display, no GPU, no dnallm.
"""

import json
import os
import sys
import time
from pathlib import Path

import pytest

pexpect = pytest.importorskip("pexpect")
pytest.importorskip("pty", reason="no OS pty support on this platform")

REPO_ROOT = Path(__file__).resolve().parents[2]

# Rendered markers (the en copies the spawned console paints).
_MONITOR_MARKER = "Scan: frontier"        # MON_SCAN_NOTE (title bar)
_ENV_MARKER = "version pins"             # env-check row 0
_RUNCONFIG_MARKER = "Run Config"         # slot-4 screen title
_QUIT_MARKER = "Quit the console?"       # LNC_EXIT_CONFIRM
_GATE_REFUSAL_MARKER = "preview validation failed"  # CFG_PREVIEW_PROBLEMS

# 261018-kvj markers (the two-tab monitor): the History tab's ACTIVE
# content — the designed empty copy when no run ever finished, else the
# table's output-root column header (only the active tab's content
# region renders; the tab header always paints both TITLES, so the
# marker must be content, never the title word) — and the Running
# tab's actionable empty copy.
_HISTORY_TAB_MARKERS = ["No past runs yet", "output root"]
_RUNNING_EMPTY_MARKER = "No running tasks"   # MON_RUNNING_EMPTY (en)
_ARROW_RIGHT = "\x1b[C"
_ARROW_LEFT = "\x1b[D"

# 261018-rze markers: the fabricated running root's card name (the
# card name label paints Path(base).name) and the RunCellsModal's
# border title — the en copy of MON_RUN_CELLS_TITLE ("cells — {root}",
# the em dash U+2014 verified verbatim against tui/strings.py) with
# the fabricated root's name.
_CARD_NAME_MARKER = "root1"
_RUN_CELLS_MARKER = "cells — root1"

# 261018-toe markers (the slot-5 History row actions, en copies): the
# delete confirm's border title (MON_DELETE_TITLE), the success toast
# (MON_DELETE_TOAST), the resume confirm's distinctive substring
# (MON_RESUME_CONFIRM), and the finished-root History row name.
_DELETE_MODAL_MARKER = "Delete run —"
_DELETED_TOAST_MARKER = "✓ deleted:"
_RESUME_CONFIRM_MARKER = "incomplete pairs"
_FINISHED_ROOT_NAME = "done-run"
_INTERRUPTED_ROOT_NAME = "dead-run"

# Bounded windows (generous over the probe-pinned timings: boot ~0.25s,
# nav repaints 0.05-0.16s, quit exit 0.30s, gate refusal ~1.5s).
_BOOT_TIMEOUT = 45.0
_NAV_TIMEOUT = 12.0
_QUIT_TIMEOUT = 15.0
_GATE_TIMEOUT = 12.0


def _spawn_tui(tmp_path, timeout=_BOOT_TIMEOUT, manual_roots=()):
    """Spawn the real console on a fresh pty over per-test tmp roots.

    The child runs ``sys.executable -m tui`` (the venv python of the
    running test lane — textual is installed there via --group tui)
    from the repo root; state/config land under the tmp dir so the
    maintainer's real state never receives a write (T-08g-02).

    ``manual_roots`` (261018-rze, the drive.py probe recipe): optional
    sweep roots registered through the state dir's monitor_roots.json
    BEFORE the spawn — the spawned console discovers them through the
    service's own ``manual_roots()`` read (schema_version 1, resolved
    entries); existing call sites unchanged by the empty default.
    """
    state_dir = tmp_path / "tui-state"
    config_dir = tmp_path / "tui-config"
    state_dir.mkdir()
    config_dir.mkdir()
    if manual_roots:
        (state_dir / "monitor_roots.json").write_text(
            json.dumps({"schema_version": 1,
                        "roots": [str(root) for root in manual_roots]}),
            encoding="utf-8")
    env = dict(os.environ)
    env["DNALLMMARK_TUI_STATE_DIR"] = str(state_dir)
    env["DNALLMMARK_TUI_CONFIG_DIR"] = str(config_dir)
    return pexpect.spawn(
        sys.executable, ["-m", "tui"],
        cwd=str(REPO_ROOT), env=env,
        dimensions=(40, 120),
        encoding="utf-8", codec_errors="replace",
        timeout=timeout,
    )


def _fabricate_running_root(tmp_path) -> Path:
    """One fabricated RUNNING sweep root under the test's tmp_path (the
    drive.py probe recipe): a model/task/seed/checkpoint tree whose
    fresh mtimes classify the root running through the no-manifest
    branch (newest mtime within STALE_GRACE_SECONDS). NO churn thread:
    the static tree keeps every 2s tick's rendered content identical,
    so a quiet cadence must be byte-silent.

    261019-f0x: a SECOND task's checkpoint joins the tree (fresh
    mtimes too) so the card's matrix carries TWO groups — the
    arrow-precedence pin's fixture. The classification branch is
    unchanged (newest mtime within the grace window); the byte-silence
    and click members ride the same richer STATIC tree."""
    root = tmp_path / "runs" / "root1"
    checkpoint = (root / "plant-dnabert-6mer" / "GUE__virus_species_4"
                  / "seed_9527" / "checkpoint-120")
    checkpoint.mkdir(parents=True)
    (checkpoint / "trainer_state.json").write_text(
        '{"global_step": 120}', encoding="utf-8")
    second = (root / "plant-dnabert-6mer" / "GUE__emp_H3"
              / "seed_9527" / "checkpoint-121")
    second.mkdir(parents=True)
    (second / "trainer_state.json").write_text(
        '{"global_step": 121}', encoding="utf-8")
    return root


def _fabricate_finished_root(tmp_path) -> Path:
    """One fabricated FINISHED history root (261018-toe): a
    sweep_manifest.json with two planned cells — one completed, one
    failed — under the test's tmp_path, registered through the manual
    roots so the spawned console's History tab lists it (manifest
    present => finished; the mtimes are irrelevant to that branch)."""
    root = tmp_path / "runs" / "done-run"
    root.mkdir(parents=True)
    cells = []
    for seed, status in ((9527, "completed"), (9528, "failed")):
        cells.append({
            "model": "plant-dnabert-6mer",
            "task": "GUE__virus_species_4",
            "seed": seed,
            "status": status,
            "output_dir": str(root / "plant-dnabert-6mer"
                              / "GUE__virus_species_4" / f"seed_{seed}"),
        })
    (root / "sweep_manifest.json").write_text(json.dumps({
        "matrix": {
            "models": ["plant-dnabert-6mer"],
            "tasks": ["GUE__virus_species_4"],
            "seeds": [9527, 9528],
            "output_root": str(root),
        },
        "cells": cells,
    }), encoding="utf-8")
    return root


def _fabricate_interrupted_root(tmp_path) -> Path:
    """One fabricated INTERRUPTED history root (261018-toe): checkpoint
    residue (the kill-left shape) with every mtime pushed ~2000s into
    the past via os.utime and NO manifest — the scanner classifies it
    artifacts_only (interrupted) and its cell derives interrupted under
    the dead-root strict-miss live-pair leg, so [e] has something to
    resume."""
    root = tmp_path / "runs" / "dead-run"
    checkpoint = (root / "plant-dnabert-6mer" / "GUE__virus_species_4"
                  / "seed_9527" / "checkpoint-120")
    checkpoint.mkdir(parents=True)
    trainer_state = checkpoint / "trainer_state.json"
    trainer_state.write_text('{"global_step": 120}', encoding="utf-8")
    stale = time.time() - 2000.0
    for path in sorted(root.rglob("*")):
        os.utime(path, (stale, stale))
    os.utime(root, (stale, stale))
    return root


def _boot(child):
    """Wait for the env-check shell's first paint (the soak probe's
    boot marker — the table header arrives within ~0.25s locally; the
    generous bound covers a cold CI venv)."""
    child.expect(["State", "Check"], timeout=_BOOT_TIMEOUT)
    return child


def test_monitor_renav_renders_every_visit(tmp_path):
    """SOAK-1/F1 — the dead-5 signature, pinned forever: visit slot 5,
    leave, come back — the monitor MUST repaint every time (the exact
    sequence that froze the maintainer's console three sessions
    running). Planning-time baseline: on HEAD (902c60e) the second
    visit emitted zero monitor bytes for 6+ seconds (40/40 presses
    dead); on the fresh-build tree the revisit renders in 0.02s."""
    child = _spawn_tui(tmp_path)
    try:
        _boot(child)
        # first visit: the monitor title bar paints
        child.send("5")
        child.expect(_MONITOR_MARKER, timeout=_NAV_TIMEOUT)
        # leave: the env screen paints
        child.send("1")
        child.expect(_ENV_MARKER, timeout=_NAV_TIMEOUT)
        # THE regression: come back — the monitor must repaint
        child.send("5")
        child.expect(_MONITOR_MARKER, timeout=_NAV_TIMEOUT)
        # rapid double-cycle stress (the soak's 20x rapid loop shrank
        # to two more cycles — enough to catch a flaky-remove miss)
        child.send("1")
        child.expect(_ENV_MARKER, timeout=_NAV_TIMEOUT)
        child.send("5")
        child.expect(_MONITOR_MARKER, timeout=_NAV_TIMEOUT)
        child.send("1")
        child.expect(_ENV_MARKER, timeout=_NAV_TIMEOUT)
        child.send("5")
        child.expect(_MONITOR_MARKER, timeout=_NAV_TIMEOUT)
    finally:
        child.close(force=True)


def test_quit_confirm_uppercase_y_exits(tmp_path):
    """SOAK-2/F3 — the uppercase quit trap: the quit modal advertises
    [Y] quit / [N] cancel; uppercase Y must exit exactly like lowercase
    y did (0.30s in the soak). On HEAD the process stayed alive with
    the modal up — read as a dead console."""
    child = _spawn_tui(tmp_path)
    try:
        _boot(child)
        child.send("q")
        child.expect(_QUIT_MARKER, timeout=_NAV_TIMEOUT)
        child.send("Y")
        child.expect(pexpect.EOF, timeout=_QUIT_TIMEOUT)
    finally:
        child.close(force=True)


def test_quit_confirm_esc_dismisses_within_bounded_window(tmp_path):
    """SOAK-2/F3, the Esc leg — textual 8.2.8's parser holds a lone ESC
    for ESCDELAY before flushing it as the escape key. Measured at
    execution time (2026-10-18, clean 40x120 pty, quit modal): dismissal
    repaint in 0.16-0.26s at the DEFAULT ESCDELAY, IDENTICAL at 30ms and
    10ms — ESCDELAY has no measurable effect on the dismissal latency in
    a clean session, so no env mitigation landed (the WINDOWS disposition
    records the soak's 1.5-4s observation as non-reproducing, plausibly
    the same degraded-render family as F1). This test pins the honest
    behavior with a GENEROUS window (the 12s nav bound): a lone ESC
    dismisses the modal and the screen beneath repaints."""
    child = _spawn_tui(tmp_path)
    try:
        _boot(child)
        child.send("q")
        child.expect(_QUIT_MARKER, timeout=_NAV_TIMEOUT)
        child.send("\x1b")  # a lone ESC
        # the dismissal repaint: the env screen's rows come back
        child.expect(_ENV_MARKER, timeout=_NAV_TIMEOUT)
    finally:
        child.close(force=True)


def test_slot4_gate_refusal_is_visible(tmp_path):
    """SOAK-5 — the gate reachability leg: marking one model with no
    task and pressing enter must surface the refusal copy within a
    bounded window (the planning probe pinned ~1.5s in a clean session;
    the soak's blank-screen-for-seconds observation did NOT reproduce
    and is dispositioned in WINDOWS)."""
    child = _spawn_tui(tmp_path)
    try:
        _boot(child)
        child.send("4")
        child.expect(_RUNCONFIG_MARKER, timeout=_NAV_TIMEOUT)
        child.send(" ")     # mark the first model (picker is focused)
        child.send("\r")    # enter opens the launch gate
        child.expect(_GATE_REFUSAL_MARKER, timeout=_GATE_TIMEOUT)
    finally:
        child.close(force=True)


def test_monitor_tab_switch_paints_history(tmp_path):
    """261018-kvj — the two-tab switching, pinned under the REAL pty:
    the right arrow flips the monitor to the History tab (its content
    region paints — the empty copy or the table header, whichever the
    machine's history holds), the left arrow flips back to the Running
    tab's own content, and the tab key flips again. The arrows ride
    the DECLARED priority seam over the focused card list — exactly
    the render-layer surface the in-process Pilot lane cannot see."""
    child = _spawn_tui(tmp_path)
    try:
        _boot(child)
        child.send("5")
        child.expect(_MONITOR_MARKER, timeout=_NAV_TIMEOUT)
        # the Running tab's content paints first (the default landing):
        # the actionable empty copy when nothing runs
        child.expect(_RUNNING_EMPTY_MARKER, timeout=_NAV_TIMEOUT)
        # right: the History tab's content region replaces it
        child.send(_ARROW_RIGHT)
        child.expect(_HISTORY_TAB_MARKERS, timeout=_NAV_TIMEOUT)
        # left: the Running tab's content paints again
        child.send(_ARROW_LEFT)
        child.expect(_RUNNING_EMPTY_MARKER, timeout=_NAV_TIMEOUT)
        # the tab key flips too (the priority binding owns it over the
        # focused list)
        child.send("\t")
        child.expect(_HISTORY_TAB_MARKERS, timeout=_NAV_TIMEOUT)
    finally:
        child.close(force=True)


def test_monitor_running_empty_enter_routes_slot4(tmp_path):
    """261018-kvj — the empty-state route under the REAL pty: with no
    live run, the Running tab renders the actionable empty copy and a
    bare enter navigates to slot 4 (the ONLY launch gate — slot 5
    never duplicates it)."""
    child = _spawn_tui(tmp_path)
    try:
        _boot(child)
        child.send("5")
        child.expect(_RUNNING_EMPTY_MARKER, timeout=_NAV_TIMEOUT)
        child.send("\r")
        child.expect(_RUNCONFIG_MARKER, timeout=_NAV_TIMEOUT)
    finally:
        child.close(force=True)


def test_monitor_quiet_cadence_is_byte_silent(tmp_path):
    """261018-rze — the flicker pin: over a fabricated running root
    (fresh mtimes, static tree, no churn thread), a steady frontier
    cadence writes ZERO terminal bytes. Pre-fix the instrumented probe
    measured ~3 whole-region repaints (~4.9K chars each) arriving every
    2s tick (events.log, the maintainer's 2026-10-18 19:57 live
    report); the assertion window spans 2+ ticks (5.5s over the 2s
    interval) after a bounded drain of the initial paint.

    pexpect semantics (probe-pinned): ``expect(TIMEOUT)`` reports a
    CUMULATIVE ``before`` since the last real match — the buffer only
    resets on a match/EOF — so the window asserts ``before`` is
    byte-IDENTICAL to the drain's snapshot (any new byte, length or
    content, is cadence traffic)."""
    root = _fabricate_running_root(tmp_path)
    child = _spawn_tui(tmp_path, manual_roots=(root,))
    try:
        _boot(child)
        child.send("5")
        child.expect(_CARD_NAME_MARKER, timeout=_NAV_TIMEOUT)
        # drain the initial paint (the mount kick + first scan renders)
        child.expect(pexpect.TIMEOUT, timeout=3.0)
        drained = child.before
        # THE assertion window: 2+ frontier ticks must add ZERO bytes
        child.expect(pexpect.TIMEOUT, timeout=5.5)
        assert child.before == drained, (
            f"the quiet cadence wrote {len(child.before) - len(drained)} "
            "new bytes across 2+ steady ticks — the flicker is back")
    finally:
        child.close(force=True)


def test_click_running_card_opens_run_cells_modal(tmp_path):
    """261018-rze — the click-path pin (the maintainer's live report):
    a REAL SGR mouse click on the running card — press + release at
    col 8 row 5 (SGR encodes button;col;row), the probe-calibrated
    card-name row at 40x120 — opens the RunCellsModal, whose border
    title names the run (the en MON_RUN_CELLS_TITLE glyph, em dash).

    261019-f0x recalibration note: the card's FIRST line became the
    summary strip (same screen row the old name line occupied), so the
    probe-calibrated row 5 still lands inside the first card — the
    coordinates stay as calibrated."""
    root = _fabricate_running_root(tmp_path)
    child = _spawn_tui(tmp_path, manual_roots=(root,))
    try:
        _boot(child)
        child.send("5")
        child.expect(_CARD_NAME_MARKER, timeout=_NAV_TIMEOUT)
        child.expect(pexpect.TIMEOUT, timeout=2.0)  # short settle drain
        child.send("\x1b[<0;8;5M")   # SGR press (button 0, col 8, row 5)
        child.send("\x1b[<0;8;5m")   # SGR release
        child.expect(_RUN_CELLS_MARKER, timeout=_NAV_TIMEOUT)
    finally:
        child.close(force=True)


def test_monitor_matrix_arrows_focus_and_tab_switch(tmp_path):
    """261019-f0x — the arrow-precedence pin under the REAL pty, over a
    fabricated running root with TWO tasks (two matrix groups): RIGHT
    moves the focused column (the right pane's detail header repaints
    with the second task's key — the strong observable; the highlight
    itself is style-only) and does NOT switch tabs; TAB switches with
    cards present; LEFT on History switches back; LEFT again on Running
    WITH groups moves the focus (col 1 -> 0) and MUST NOT switch (the
    bounded drain proves the History markers never arrived). With the
    landed [w]: w paints the wide table's header cells, w again
    restores the matrix. ONE spawn, ~12s budget."""
    root = _fabricate_running_root(tmp_path)
    child = _spawn_tui(tmp_path, manual_roots=(root,))
    try:
        _boot(child)
        child.send("5")
        child.expect(_CARD_NAME_MARKER, timeout=_NAV_TIMEOUT)
        # drain the initial paint (the mount kick + first scan renders)
        child.expect(pexpect.TIMEOUT, timeout=3.0)
        # RIGHT: the focused column moves 0 -> 1 — the pane's detail
        # header repaints with the SECOND task's key (the pane-width
        # truncated form "× GUE__virus_species…"; the matrix head
        # truncates the key to its narrow column, so the ×-prefixed
        # pane form is the unique fresh-bytes observable)
        child.send(_ARROW_RIGHT)
        child.expect("× GUE__virus_species…", timeout=_NAV_TIMEOUT)
        # TAB still switches with cards present
        child.send("\t")
        child.expect(_HISTORY_TAB_MARKERS, timeout=_NAV_TIMEOUT)
        # LEFT on History switches back — the card strip repaints
        child.send(_ARROW_LEFT)
        child.expect(_CARD_NAME_MARKER, timeout=_NAV_TIMEOUT)
        # LEFT once more on Running WITH groups: col 1 -> 0, and the
        # tab MUST NOT switch — a bounded drain with the History
        # markers ABSENT from the arriving bytes
        child.send(_ARROW_LEFT)
        child.expect(pexpect.TIMEOUT, timeout=3.0)
        drained = child.before
        for marker in _HISTORY_TAB_MARKERS:
            assert marker not in drained, (
                "left on a grouped Running card moved the matrix focus — "
                "the tab-switch bytes must never arrive"
            )
        # TAB -> the History markers return (the switch itself works)
        child.send("\t")
        child.expect(_HISTORY_TAB_MARKERS, timeout=_NAV_TIMEOUT)
        # back to Running, then the [w] round trip: the wide table's
        # header cells paint, and w again restores the matrix strip
        child.send("\t")
        child.expect(_CARD_NAME_MARKER, timeout=_NAV_TIMEOUT)
        child.expect(pexpect.TIMEOUT, timeout=2.0)  # short settle drain
        child.send("w")
        child.expect("State", timeout=_NAV_TIMEOUT)
        child.expect("Progress", timeout=_NAV_TIMEOUT)
        child.send("w")
        child.expect(_CARD_NAME_MARKER, timeout=_NAV_TIMEOUT)
    finally:
        child.close(force=True)


def test_history_row_delete_flow_end_to_end(tmp_path):
    """261018-toe — the [d] delete flow under the REAL pty, from a real
    keypress to the row's disappearance: over a fabricated finished
    history root, switching to the History tab paints the [d]/[e]
    keycaps in the bottom bar, ``d`` opens the strong confirm naming
    the run, ``y`` deletes (a DELETE confirm, never a launch — the
    safety rail's launch-family exclusion does not apply), the success
    toast lands, and the post-delete rescan repaints the History region
    WITHOUT the deleted row (the either-marker accepts the designed
    empty copy on a clean machine OR the table header when the host's
    real default roots also list — the row's ABSENCE is the pin)."""
    root = _fabricate_finished_root(tmp_path)
    child = _spawn_tui(tmp_path, manual_roots=(root,))
    try:
        _boot(child)
        child.send("5")
        child.expect(_MONITOR_MARKER, timeout=_NAV_TIMEOUT)
        child.expect(_RUNNING_EMPTY_MARKER, timeout=_NAV_TIMEOUT)
        child.send(_ARROW_RIGHT)
        child.expect(_FINISHED_ROOT_NAME, timeout=_NAV_TIMEOUT)
        # the per-tab footer: the History row actions' keycaps paint
        child.expect("Delete", timeout=_NAV_TIMEOUT)
        child.expect("Resume", timeout=_NAV_TIMEOUT)
        # a REAL keypress opens the strong confirm (non-vacuity pin)
        child.send("d")
        child.expect(_DELETE_MODAL_MARKER, timeout=_NAV_TIMEOUT)
        # y confirms the deletion of the tmp run root
        child.send("y")
        child.expect(_DELETED_TOAST_MARKER, timeout=_NAV_TIMEOUT)
        # the immediate rescan repaints the History region (empty copy
        # on a clean machine, table header when the host's real default
        # roots also list — the row's disappearance is proven on disk)
        child.expect(_HISTORY_TAB_MARKERS, timeout=_NAV_TIMEOUT)
        assert not root.exists(), (
            "the confirmed y removed the run's output root from disk")
        manual_roots_file = (tmp_path / "tui-state" / "monitor_roots.json")
        assert _FINISHED_ROOT_NAME not in manual_roots_file.read_text(
            encoding="utf-8"), (
            "the delete worker's manual-root hygiene unregistered the "
            "root — the next boots never rescan the deleted run")
    finally:
        child.close(force=True)


def test_history_row_resume_confirm_and_cancel(tmp_path):
    """261018-toe — the [e] resume confirm under the REAL pty: over a
    fabricated INTERRUPTED history root (checkpoint residue pushed
    ~2000s stale, no manifest), ``e`` derives the incomplete pair and
    opens the honest resume confirm (the en copy's distinctive
    "incomplete pairs" segment); ``n`` cancels and the history row
    still paints. NEVER presses y — no lane ever performs a real
    launch (the standing pty safety rail)."""
    root = _fabricate_interrupted_root(tmp_path)
    child = _spawn_tui(tmp_path, manual_roots=(root,))
    try:
        _boot(child)
        child.send("5")
        child.expect(_MONITOR_MARKER, timeout=_NAV_TIMEOUT)
        child.expect(_RUNNING_EMPTY_MARKER, timeout=_NAV_TIMEOUT)
        child.send(_ARROW_RIGHT)
        child.expect(_INTERRUPTED_ROOT_NAME, timeout=_NAV_TIMEOUT)
        # e derives off-loop and opens the honest confirm
        child.send("e")
        child.expect(_RESUME_CONFIRM_MARKER, timeout=_NAV_TIMEOUT)
        # n cancels — the row survives, nothing ever launches
        child.send("n")
        child.expect(_INTERRUPTED_ROOT_NAME, timeout=_NAV_TIMEOUT)
        assert root.exists(), (
            "a cancelled resume touches nothing on disk"
        )
    finally:
        child.close(force=True)
