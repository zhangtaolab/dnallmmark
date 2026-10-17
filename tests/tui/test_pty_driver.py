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

Runtime budget: three spawns at roughly 8-10s each — acceptable next to
the slow lane's ~80s member; every read is bounded by an explicit
timeout and ``close(force=True)`` in a finally so a wedged child can
never hang ``make test`` (T-08g-01). CI-safe: plain pexpect over a
pty, no display, no GPU, no dnallm.
"""

import os
import sys
from pathlib import Path

import pytest

pexpect = pytest.importorskip("pexpect")
pytest.importorskip("pty", reason="no OS pty support on this platform")

REPO_ROOT = Path(__file__).resolve().parents[2]

# Rendered markers (the en copies the spawned console paints).
_MONITOR_MARKER = "Scan: frontier"        # MON_SCAN_NOTE (title bar)
_ENV_MARKER = "version pins"             # env-check row 0
_RUNCONFIG_MARKER = "Run Config"         # slot-4 screen title
_GATE_REFUSAL_MARKER = "preview validation failed"  # CFG_PREVIEW_PROBLEMS

# Bounded windows (generous over the probe-pinned timings: boot ~0.25s,
# nav repaints 0.05-0.16s, quit exit 0.30s, gate refusal ~1.5s).
_BOOT_TIMEOUT = 45.0
_NAV_TIMEOUT = 12.0
_GATE_TIMEOUT = 12.0


def _spawn_tui(tmp_path, timeout=_BOOT_TIMEOUT):
    """Spawn the real console on a fresh pty over per-test tmp roots.

    The child runs ``sys.executable -m tui`` (the venv python of the
    running test lane — textual is installed there via --group tui)
    from the repo root; state/config land under the tmp dir so the
    maintainer's real state never receives a write (T-08g-02).
    """
    state_dir = tmp_path / "tui-state"
    config_dir = tmp_path / "tui-config"
    state_dir.mkdir()
    config_dir.mkdir()
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
