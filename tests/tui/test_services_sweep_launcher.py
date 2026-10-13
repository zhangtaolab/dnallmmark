"""
Tier-1 service tests for ``tui/services/sweep_launcher.py`` (Phase 11,
11-03 — LNC-01/02/03 + MON-04).

Three lanes, per the plan:

- **Launch mechanics suite** (Task 1) — the injectable Popen seam over a
  fake spawner: LIST argv recorded, ``start_new_session=True``, cwd
  pinned to the repo's ``pipeline/``, env EXACTLY
  ``{**os.environ, "PYTHONUNBUFFERED": "1"}`` (Pitfall 4 — the tee must
  see each line promptly), stdout+stderr tee'd to ONE file under
  ``settings.state_dir()/logs/`` named
  ``sweep_{YYYYmmdd_HHMMSS}_{rootname}.log`` over an injected fixed
  clock (D-10 single persistence root), the OSError path (nothing
  launched leaves no log), and the kill/detach/live-registry outcome
  vocabulary over a fake Popen with a monkeypatched ``os.killpg`` (D-06
  process-group discipline).
- **Gate suite** (Task 2) — env preflight over injected fake kernels
  through the FROZEN phase-8 face (zero edits to quick_check/env_gate),
  ``gate_confirm_data``'s fresh-preview recompute (spy-proven), and
  ``launch_spec``'s structural E2' phrase enforcement: the refusal
  happens BEFORE the spawner, proven by call counts, not return shapes.
- **From-failures suite** (Task 3) — the [r] re-run path composes via
  ``run_config.compose_from_failures_argv`` and launches through the
  shared seam; the raw ``launch_argv`` never consults the phrase gate
  (never-full-matrix by construction, D-11).

Every test injects a tmp state root via ``DNALLMMARK_TUI_STATE_DIR`` —
the real ``~/.local/state/dnallmmark`` is never read or written. Every
subprocess is a fake spawner; no GPU, no network, no real child.

See also:
    ``tui/services/sweep_launcher.py`` — the service under test.
    ``tui/services/download_queue.py`` — the phase-10 spawner/killpg
    seams this launcher copies verbatim.
    ``tests/tui/test_services_download_queue.py`` — the tier-1 idioms.
"""

import os
import signal
import subprocess
from datetime import datetime
from pathlib import Path

from tui.services import settings, sweep_launcher

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The pinned launch moment: tee filename
#: ``sweep_20261013_083005_{rootname}.log`` (deterministic under the
#: injected clock).
CLOCK_MOMENT = datetime(2026, 10, 13, 8, 30, 5)


def pin_state_dir(monkeypatch, tmp_path):
    """Point the TUI state root at a tmp dir — the real XDG state home
    is never touched (the settings contract)."""
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    return state


class FixedClock:
    """An injectable clock pinned to one datetime (deterministic tee
    filenames + started_at stamps)."""

    def __init__(self, moment):
        self.moment = moment

    def __call__(self):
        return self.moment


class FakeSweepPopen:
    """A Popen-shaped double with controllable poll sequencing.

    ``poll_returns`` is consumed left-to-right and the LAST element is
    sticky (an exhausted queue repeats it): ``[0]`` = already dead,
    ``[None]`` = never dies, ``[None, 0]`` = dies after one grace poll.
    """

    def __init__(self, poll_returns=(0,)):
        self.pid = 90210
        self.poll_returns = list(poll_returns)

    def poll(self):
        if len(self.poll_returns) > 1:
            return self.poll_returns.pop(0)
        return self.poll_returns[0]


class FakeSpawner:
    """The injectable Popen seam recording every spawn (the
    tests/tui/test_services_download_queue.py idiom)."""

    def __init__(self, popen=None, exc=None):
        self.popen = popen if popen is not None else FakeSweepPopen()
        self.exc = exc
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append({"argv": list(argv), "kwargs": dict(kwargs)})
        if self.exc is not None:
            raise self.exc
        return self.popen


class KillpgRecorder:
    """Records every ``os.killpg`` signal over an identity
    ``os.getpgid`` monkeypatch (the fake pid needs no real process
    group); optionally raises ``exc`` per call to simulate the
    already-dead race."""

    def __init__(self, monkeypatch, exc=None):
        self.calls = []
        self.exc = exc
        monkeypatch.setattr(os, "getpgid", lambda pid: pid)
        monkeypatch.setattr(os, "killpg", self)

    def __call__(self, pgid, sig):
        self.calls.append((pgid, sig))
        if self.exc is not None:
            raise self.exc


def single_call(spawner):
    """The one recorded spawn call as ``(argv, kwargs)``."""
    (call,) = spawner.calls
    return call["argv"], call["kwargs"]


# =====================================================================
# Lane 1 — spawner seam + tee launch + live-sweep registry (Task 1)
# =====================================================================


def test_spawn_pins_list_argv_session_cwd_env_tee(monkeypatch, tmp_path):
    """The D-06 launch contract: LIST argv, detached session, pinned
    cwd, PYTHONUNBUFFERED env, stdout+stderr merged into the tee file
    under the D-10 single root."""
    state = pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner(FakeSweepPopen())
    launcher = sweep_launcher.SweepLauncher()
    out_root = tmp_path / "out"

    outcome = launcher._spawn(
        ["py", "run_sweep.py", "--models", "m"], out_root,
        spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True
    assert outcome.error is None
    assert outcome.root == str(out_root.resolve())
    expected_tee = state / "logs" / "sweep_20261013_083005_out.log"
    assert outcome.tee_path == str(expected_tee)
    assert expected_tee.is_file()

    argv, kwargs = single_call(spawner)
    assert isinstance(argv, list)              # never a shell string
    assert argv == ["py", "run_sweep.py", "--models", "m"]
    assert kwargs["start_new_session"] is True
    assert kwargs["cwd"] == str(REPO_ROOT / "pipeline")
    assert kwargs["env"] == {**os.environ, "PYTHONUNBUFFERED": "1"}
    assert kwargs["env"]["PYTHONUNBUFFERED"] == "1"
    assert kwargs["stdout"].name == str(expected_tee)
    assert kwargs["stderr"] == subprocess.STDOUT


def test_spawn_tee_name_uses_rootname_of_resolved_root(
        monkeypatch, tmp_path):
    """``{rootname}`` is the RESOLVED output root's final path
    component — the E2' phrase identity, making the log
    self-describing."""
    state = pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner(FakeSweepPopen())
    launcher = sweep_launcher.SweepLauncher()
    out_root = tmp_path / "nested" / "rerun-dir"

    outcome = launcher._spawn(
        ["py"], out_root, spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.tee_path == str(
        state / "logs" / "sweep_20261013_083005_rerun-dir.log")


def test_spawn_registers_live_sweep_roundtrip(monkeypatch, tmp_path):
    """A successful spawn claims the registry entry: live_sweeps lists
    the resolved root; tee_path_for round-trips both root forms."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()
    out_root = tmp_path / "out"

    outcome = launcher._spawn(
        ["py"], out_root, spawner=FakeSpawner(FakeSweepPopen()),
        clock=FixedClock(CLOCK_MOMENT))

    assert launcher.live_sweeps() == (str(out_root.resolve()),)
    assert launcher.tee_path_for(out_root) == outcome.tee_path
    assert launcher.tee_path_for(str(out_root.resolve())) == outcome.tee_path


def test_spawn_oserror_failed_outcome_no_log_empty_registry(
        monkeypatch, tmp_path):
    """A refused spawn (OSError from the seam) returns the failed
    outcome, unlinks the empty tee file, and leaves the registry
    empty — nothing launched leaves no log."""
    state = pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner(exc=OSError("spawn boom"))
    launcher = sweep_launcher.SweepLauncher()

    outcome = launcher._spawn(
        ["py"], tmp_path / "out", spawner=spawner,
        clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is False
    assert "spawn boom" in outcome.error
    assert outcome.tee_path is None
    assert outcome.root == str((tmp_path / "out").resolve())
    assert list((state / "logs").glob("*")) == []
    assert launcher.live_sweeps() == ()
    assert len(spawner.calls) == 1   # the seam WAS attempted (recorded)


def test_kill_sweep_sigterm_with_clean_exit(monkeypatch, tmp_path):
    """SIGTERM to the process group; the poll converges inside the
    grace window; NO SIGKILL; the registry entry drops."""
    pin_state_dir(monkeypatch, tmp_path)
    recorder = KillpgRecorder(monkeypatch)
    popen = FakeSweepPopen(poll_returns=[None, None, 0])
    launcher = sweep_launcher.SweepLauncher(
        kill_grace=1.0, kill_interval=0.01)
    launcher._spawn(["py"], tmp_path / "out", spawner=FakeSpawner(popen),
                    clock=FixedClock(CLOCK_MOMENT))

    assert launcher.kill_sweep(tmp_path / "out") == "signalled"
    assert recorder.calls == [(90210, signal.SIGTERM)]
    assert launcher.live_sweeps() == ()


def test_kill_sweep_escalates_to_sigkill_when_poll_stays_none(
        monkeypatch, tmp_path):
    """A process that ignores SIGTERM through the grace window gets the
    SIGKILL escalation (the phase-10 discipline)."""
    pin_state_dir(monkeypatch, tmp_path)
    recorder = KillpgRecorder(monkeypatch)
    popen = FakeSweepPopen(poll_returns=[None])
    launcher = sweep_launcher.SweepLauncher(
        kill_grace=0.0, kill_interval=0.01)
    launcher._spawn(["py"], tmp_path / "out", spawner=FakeSpawner(popen),
                    clock=FixedClock(CLOCK_MOMENT))

    assert launcher.kill_sweep(tmp_path / "out") == "signalled"
    assert recorder.calls == [
        (90210, signal.SIGTERM), (90210, signal.SIGKILL)]
    assert launcher.live_sweeps() == ()


def test_kill_sweep_already_dead_never_signals(monkeypatch, tmp_path):
    """A process already reaped by the time of the kill call yields
    ``already_dead`` with zero signals; the entry still drops."""
    pin_state_dir(monkeypatch, tmp_path)
    recorder = KillpgRecorder(monkeypatch)
    popen = FakeSweepPopen(poll_returns=[0])
    launcher = sweep_launcher.SweepLauncher()
    launcher._spawn(["py"], tmp_path / "out", spawner=FakeSpawner(popen),
                    clock=FixedClock(CLOCK_MOMENT))

    assert launcher.kill_sweep(tmp_path / "out") == "already_dead"
    assert recorder.calls == []
    assert launcher.live_sweeps() == ()


def test_kill_sweep_absorbs_already_dead_signal_race(
        monkeypatch, tmp_path):
    """killpg raising ProcessLookupError (the process died between the
    poll and the signal) is absorbed — the reap owns the outcome, never
    an exception to the caller."""
    pin_state_dir(monkeypatch, tmp_path)
    recorder = KillpgRecorder(monkeypatch, exc=ProcessLookupError())
    popen = FakeSweepPopen(poll_returns=[None, 0])
    launcher = sweep_launcher.SweepLauncher(
        kill_grace=1.0, kill_interval=0.01)
    launcher._spawn(["py"], tmp_path / "out", spawner=FakeSpawner(popen),
                    clock=FixedClock(CLOCK_MOMENT))

    assert launcher.kill_sweep(tmp_path / "out") == "signalled"
    assert recorder.calls == [(90210, signal.SIGTERM)]


def test_kill_sweep_unknown_root_is_noop(monkeypatch, tmp_path):
    pin_state_dir(monkeypatch, tmp_path)
    recorder = KillpgRecorder(monkeypatch)
    launcher = sweep_launcher.SweepLauncher()

    assert launcher.kill_sweep(tmp_path / "nope") == "noop"
    assert recorder.calls == []


def test_detach_drops_without_signal_or_wait(monkeypatch, tmp_path):
    """Detach drops the handle with NO wait and NO kill: zero signals,
    the registry forgets the root, and the fake handle stays
    conceptually alive (poll None) — the orphaned session leader."""
    pin_state_dir(monkeypatch, tmp_path)
    recorder = KillpgRecorder(monkeypatch)
    popen = FakeSweepPopen(poll_returns=[None])
    launcher = sweep_launcher.SweepLauncher()
    launcher._spawn(["py"], tmp_path / "out", spawner=FakeSpawner(popen),
                    clock=FixedClock(CLOCK_MOMENT))
    assert launcher.live_sweeps() != ()

    assert launcher.detach(tmp_path / "out") == "detached"

    assert launcher.live_sweeps() == ()
    assert launcher.tee_path_for(tmp_path / "out") is None
    assert recorder.calls == []
    assert popen.poll() is None    # never waited, never killed


def test_detach_unknown_root_is_noop(monkeypatch, tmp_path):
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()

    assert launcher.detach(tmp_path / "nope") == "noop"


def test_tee_path_for_unknown_root_is_none(monkeypatch, tmp_path):
    """The [t] modal's unavailable state: an unregistered root (e.g. a
    CLI-launched sweep) has no tee path."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()

    assert launcher.tee_path_for(tmp_path / "nope") is None
