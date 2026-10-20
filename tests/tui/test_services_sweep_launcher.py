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

import json
import os
import signal
import subprocess
import sys
import types
from datetime import UTC, datetime
from pathlib import Path

import run_sweep  # top-level module (pipeline/ sys.path root) — the 261017-uwr enumerate spy
from env_smoke import CheckResult  # top-level module (pipeline/ sys.path root)

from tui.services import (
    env_gate,
    quick_check,
    run_config,
    settings,
    sweep_launcher,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The pinned launch moment: tee filename
#: ``sweep_20261013_083005_{rootname}.log`` (deterministic under the
#: injected clock).
CLOCK_MOMENT = datetime(
    2026, 10, 13, 8, 30, 5, tzinfo=UTC)


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
        ["py"], out_root,
        spawner=FakeSpawner(FakeSweepPopen(poll_returns=[None])),
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


def test_spawn_refuses_second_live_sweep_at_same_root(
        monkeypatch, tmp_path):
    """CR-02: launching a second sweep into a LIVE root is refused —
    the first registry entry survives (its Popen stays killable, its
    tee handle stays owned), the second spawner is never called, and
    the diagnostic names the live root (two run_sweep processes would
    otherwise race the identical cell dirs and corrupt run artifacts)."""
    pin_state_dir(monkeypatch, tmp_path)
    first_spawner = FakeSpawner(FakeSweepPopen(poll_returns=[None]))
    launcher = sweep_launcher.SweepLauncher()
    out_root = tmp_path / "out"

    first = launcher._spawn(
        ["py"], out_root, spawner=first_spawner, clock=FixedClock(CLOCK_MOMENT))
    assert first.spawned is True

    second_spawner = FakeSpawner(FakeSweepPopen(poll_returns=[None]))
    second = launcher._spawn(
        ["py"], out_root, spawner=second_spawner,
        clock=FixedClock(CLOCK_MOMENT))

    root_key = str(out_root.resolve())
    assert second.spawned is False
    assert root_key in second.error, "the diagnostic names the live root"
    assert second.tee_path is None
    assert second_spawner.calls == [], "the seam was never consulted"
    assert launcher.live_sweeps() == (root_key,), "the first entry stands"
    assert launcher.tee_path_for(out_root) == first.tee_path


def test_spawn_reclaims_root_after_prior_sweep_exited(
        monkeypatch, tmp_path):
    """CR-02 self-heal: a registered entry whose Popen has exited is
    pruned (its tee handle closed) and the root is claimable again —
    a dead sweep never wedges its output root forever."""
    pin_state_dir(monkeypatch, tmp_path)
    dead = FakeSweepPopen(poll_returns=[0])
    launcher = sweep_launcher.SweepLauncher()
    out_root = tmp_path / "out"

    first = launcher._spawn(
        ["py"], out_root, spawner=FakeSpawner(dead),
        clock=FixedClock(CLOCK_MOMENT))
    assert first.spawned is True

    second = launcher._spawn(
        ["py"], out_root,
        spawner=FakeSpawner(FakeSweepPopen(poll_returns=[None])),
        clock=FixedClock(CLOCK_MOMENT))

    assert second.spawned is True
    assert launcher.live_sweeps() == (str(out_root.resolve()),)
    assert launcher.tee_path_for(out_root) == second.tee_path


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
    conceptually alive (poll None) — the orphaned session leader. The
    tee PATH stays answerable via the launch history (IN-05: the file
    itself still stands under state/logs)."""
    pin_state_dir(monkeypatch, tmp_path)
    recorder = KillpgRecorder(monkeypatch)
    popen = FakeSweepPopen(poll_returns=[None])
    launcher = sweep_launcher.SweepLauncher()
    outcome = launcher._spawn(["py"], tmp_path / "out",
                             spawner=FakeSpawner(popen),
                             clock=FixedClock(CLOCK_MOMENT))
    assert launcher.live_sweeps() != ()

    assert launcher.detach(tmp_path / "out") == "detached"

    assert launcher.live_sweeps() == ()
    assert launcher.tee_path_for(tmp_path / "out") == outcome.tee_path
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


def test_tee_path_survives_detach_via_history(monkeypatch, tmp_path):
    """IN-05 (phase-11 review): after the exit modal's DEFAULT detach
    the tee FILE still exists under state/logs (the child owns its own
    descriptor) — tee_path_for falls back to the launch history, so a
    sweep THIS TUI launched never renders the false 'CLI-launched, no
    tee' copy on [t]."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()
    out_root = tmp_path / "out"

    first = launcher._spawn(
        ["py"], out_root,
        spawner=FakeSpawner(FakeSweepPopen(poll_returns=[None])),
        clock=FixedClock(CLOCK_MOMENT))
    assert launcher.detach(out_root) == "detached"

    assert launcher.tee_path_for(out_root) == first.tee_path, (
        "the detached root's tee path survives via the launch history"
    )
    assert Path(first.tee_path).is_file(), "the tee file itself stands"


def test_tee_path_history_newest_launch_wins(monkeypatch, tmp_path):
    """A relaunch at a reclaimed root overwrites the history entry —
    [t] always tails the CURRENT launch's tee, never a superseded
    one."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()
    out_root = tmp_path / "out"
    launcher._spawn(
        ["py"], out_root, spawner=FakeSpawner(FakeSweepPopen()),
        clock=FixedClock(CLOCK_MOMENT))
    second_moment = datetime(2026, 10, 13, 9, 0, 0, tzinfo=UTC)
    second = launcher._spawn(
        ["py"], out_root, spawner=FakeSpawner(FakeSweepPopen()),
        clock=FixedClock(second_moment))

    assert launcher.tee_path_for(out_root) == second.tee_path


def test_tee_path_restart_discovery_finds_fresh_disk_tee(
        monkeypatch, tmp_path):
    """2026-10-19 restart-reattach: after a console restart the
    registry AND the in-memory history are empty, but the surviving
    detached child keeps appending its inherited tee descriptor under
    state/logs — tee_path_for discovers the root's NEWEST tee file on
    disk when its mtime sits inside the fresh-append grace (the
    STALE_GRACE_SECONDS quiet-phase precedent), so [t] tails the live
    run's own log instead of the false unavailable copy."""
    import os

    pin_state_dir(monkeypatch, tmp_path)
    logs_dir = (
        tmp_path / "state" / sweep_launcher.TEE_DIR_NAME)
    logs_dir.mkdir(parents=True)
    root = tmp_path / "sweeps" / "detached"
    stale = logs_dir / "sweep_20261017_120000_detached.log"
    fresh = logs_dir / "sweep_20261019_100936_detached.log"
    import time
    stale.write_text("old run\n", encoding="utf-8")
    fresh.write_text("live run\n", encoding="utf-8")
    now = time.time()
    os.utime(stale, (now - 7200.0, now - 7200.0))  # 2h: long stale
    os.utime(fresh, (now - 30.0, now - 30.0))      # 30s: fresh append

    launcher = sweep_launcher.SweepLauncher()

    assert launcher.tee_path_for(root) == str(fresh), (
        "the registry-empty restart still resolves the LIVE launch's "
        "tee from disk (newest fresh file wins over the stale one)"
    )


def test_tee_path_restart_discovery_stale_only_stays_none(
        monkeypatch, tmp_path):
    """The honest-unavailable guard: a root whose only tee files are
    OLD (nothing has appended within the grace window) reads None —
    an old run's log must never dress as the live tail."""
    import os
    import time

    pin_state_dir(monkeypatch, tmp_path)
    logs_dir = (
        tmp_path / "state" / sweep_launcher.TEE_DIR_NAME)
    logs_dir.mkdir(parents=True)
    root = tmp_path / "sweeps" / "finished-long-ago"
    tee = logs_dir / "sweep_20261017_120000_finished-long-ago.log"
    tee.write_text("done\n", encoding="utf-8")
    now = time.time()
    os.utime(tee, (now - 86400.0, now - 86400.0))

    launcher = sweep_launcher.SweepLauncher()

    assert launcher.tee_path_for(root) is None


def test_live_sweeps_prunes_exited_process_and_closes_tee(
        monkeypatch, tmp_path):
    """WR-04: a registered sweep whose Popen exited (OOM-kill, external
    SIGKILL, driver crash — no manifest ever lands) is pruned at read
    time: live_sweeps stops listing it, its parent-side tee handle
    closes, and the root is claimable again (the scanner's mtime/
    artifacts classification takes over — never a false running state
    for the rest of the session)."""
    pin_state_dir(monkeypatch, tmp_path)
    popen = FakeSweepPopen(poll_returns=[None])
    spawner = FakeSpawner(popen)
    launcher = sweep_launcher.SweepLauncher()
    out_root = tmp_path / "out"
    launcher._spawn(["py"], out_root, spawner=spawner,
                    clock=FixedClock(CLOCK_MOMENT))
    root_key = str(out_root.resolve())
    assert launcher.live_sweeps() == (root_key,)

    popen.poll_returns = [0]   # the sweep died without detach/kill
    assert launcher.live_sweeps() == ()
    assert spawner.calls[0]["kwargs"]["stdout"].closed is True, (
        "the pruned entry's parent-side tee handle is closed"
    )

    # the root is claimable again (the dead entry no longer blocks)
    respawn = launcher._spawn(
        ["py"], out_root, spawner=FakeSpawner(FakeSweepPopen()),
        clock=FixedClock(CLOCK_MOMENT))
    assert respawn.spawned is True


def test_live_sweeps_keeps_live_entries_across_reads(
        monkeypatch, tmp_path):
    """The prune is read-time only: a still-running sweep stays listed
    across repeated reads (no accidental eviction)."""
    pin_state_dir(monkeypatch, tmp_path)
    popen = FakeSweepPopen(poll_returns=[None])
    launcher = sweep_launcher.SweepLauncher()
    launcher._spawn(["py"], tmp_path / "out", spawner=FakeSpawner(popen),
                    clock=FixedClock(CLOCK_MOMENT))

    for _ in range(3):
        assert launcher.live_sweeps() == (
            str((tmp_path / "out").resolve()),)


def test_spawn_same_second_same_basename_never_shares_tee_file(
        monkeypatch, tmp_path):
    """WR-04 (gap #5): two DIFFERENT roots sharing the basename
    ``finetuned`` (the common default) spawned within the SAME second —
    a slot-4 gate confirm racing a monitor [r], both from this TUI
    process — never share a tee file: the tee opens EXCLUSIVE (O_EXCL)
    with a numeric-suffix fallback. The FIRST keeps today's exact name
    shape; the SECOND gets a ``_1`` suffix; the first log's content is
    never reopened for write (the sentinel survives); both registry
    entries stay live."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()
    root_a = tmp_path / "a" / "finetuned"
    root_b = tmp_path / "b" / "finetuned"
    clock = FixedClock(CLOCK_MOMENT)   # the SAME second for both spawns

    first = launcher.launch_argv(
        ["py", "run_sweep.py", "--models", "a"], root_a,
        spawner=FakeSpawner(FakeSweepPopen(poll_returns=[None])),
        clock=clock)
    assert first.spawned is True
    first_tee = Path(first.tee_path)
    # a sentinel rides the FIRST sweep's audit log: the second spawn
    # must never reopen this file for write
    with first_tee.open("a", encoding="utf-8") as handle:
        handle.write("SENTINEL-first-sweep-audit-log\n")

    second = launcher.launch_argv(
        ["py", "run_sweep.py", "--models", "b"], root_b,
        spawner=FakeSpawner(FakeSweepPopen(poll_returns=[None])),
        clock=clock)

    assert second.spawned is True
    assert second.tee_path != first.tee_path, (
        "the same-second same-basename spawn gets its OWN tee file"
    )
    assert first_tee.name == "sweep_20261013_083005_finetuned.log", (
        "the non-colliding first name keeps today's exact shape"
    )
    assert Path(second.tee_path).name == (
        "sweep_20261013_083005_finetuned_1.log")
    assert "SENTINEL-first-sweep-audit-log" in first_tee.read_text(
        encoding="utf-8"), (
        "the first sweep's audit log is never truncated or interleaved"
    )
    assert launcher.live_sweeps() == (
        str(root_a.resolve()), str(root_b.resolve())), (
        "both registry entries stay live and killable"
    )


# =====================================================================
# Lane 2 — the gate: env preflight + fresh recompute + E2' phrase
# (Task 2)
# =====================================================================


def kernel(name, ok=True, lines=()):
    """One fake ``env_smoke`` kernel: a zero-arg callable returning a
    ``CheckResult`` (the ``run_quick_check`` injectable-kernel shape)."""
    result = CheckResult(name=name, ok=ok, lines=tuple(lines))
    return lambda: result


class RunConfigDouble:
    """A ``run_config`` seam double for controlled verdicts.

    The REAL verdict logic is 11-02's tested code — this double only
    conforms to the consumed function seam (``preview`` /
    ``official_keys`` / ``is_full_e2x`` / ``expected_phrase`` /
    ``phrase_matches`` / ``compose_argv``) with configurable outcomes
    and call counters (the fresh-recompute spy). The phrase functions
    delegate to the REAL run_config implementations so the launcher's
    orchestration is proven against the exact-match semantics.
    """

    def __init__(self, preview_result=None, official=None, full_e2x=False,
                 argv=None):
        self.preview_result = (
            preview_result if preview_result is not None
            else run_config.PreviewResult(
                models_count=1, tasks_count=1, seeds_count=1,
                fractions_count=None, cells_count=1,
                cells=(("m", "t", 42),), problems=()))
        self.official = (
            official if official is not None
            else run_config.OfficialKeys(
                frozenset({"m"}), frozenset({"t"}), None))
        self.full_e2x = full_e2x
        self.argv = argv if argv is not None else ["py", "run_sweep.py"]
        self.preview_calls = 0
        self.official_calls = 0
        self.e2x_calls = 0
        self.compose_calls = 0

    def preview(self, spec, registry_dir=None):
        self.preview_calls += 1
        return self.preview_result

    def official_keys(self, registry_dir=None):
        self.official_calls += 1
        return self.official

    def is_full_e2x(self, spec, official):
        self.e2x_calls += 1
        return self.full_e2x

    def expected_phrase(self, output_root):
        return run_config.expected_phrase(output_root)

    def phrase_matches(self, typed, output_root):
        return run_config.phrase_matches(typed, output_root)

    def resolve_dirs(self, spec):
        # WR-01: launch_spec threads the argv's root basis through this
        # seam — the double delegates to the REAL resolver like the
        # other grammar legs.
        return run_config.resolve_dirs(spec)

    def compose_argv(self, spec):
        self.compose_calls += 1
        return list(self.argv)


def gate_spec(tmp_path, **kwargs):
    """A minimal well-formed spec over a tmp output root."""
    return run_config.RunSpec(
        models=("m",), tasks=("t",),
        output_root=str(tmp_path / "out"), **kwargs)


# ===== env preflight (D-08 — the frozen face, zero edits) =====


def test_env_preflight_all_ok_kernels_can_launch():
    pre = sweep_launcher.env_preflight([
        kernel("version_pins"),
        kernel("cuda"),
        kernel("dataset_dirs"),
    ])
    assert pre.can_launch is True
    assert pre.reasons == ()
    assert pre.failed_kernels == ()


def test_env_preflight_critical_failure_blocks_with_details():
    pre = sweep_launcher.env_preflight([
        kernel("version_pins"),
        kernel("cuda", ok=False,
               lines=("CUDA driver mismatch: need >=560",)),
    ])
    assert pre.can_launch is False
    assert pre.reasons == ("CUDA driver mismatch: need >=560",)
    assert pre.failed_kernels == ("cuda",)


def test_env_preflight_routing_failure_alone_stays_launchable():
    """``dataset_dirs`` is ROUTING (advisory): a missing-data machine
    can still launch a dry-run-shaped sweep — only CRITICAL blocks."""
    pre = sweep_launcher.env_preflight([
        kernel("cuda"),
        kernel("dataset_dirs", ok=False, lines=("missing GUE",)),
    ])
    assert pre.can_launch is True
    assert pre.failed_kernels == ()


def test_env_preflight_multiple_critical_failures_in_input_order():
    pre = sweep_launcher.env_preflight([
        kernel("dnallm", ok=False, lines=("dnallm absent",)),
        kernel("peft"),
        kernel("cuda", ok=False, lines=("no CUDA device", "driver old")),
    ])
    assert pre.can_launch is False
    assert pre.failed_kernels == ("dnallm", "cuda")
    assert pre.reasons == ("dnallm absent", "no CUDA device", "driver old")


def test_env_preflight_unknown_kernel_failure_is_ignored():
    """Forward tolerance: a future kernel id failing cannot crash the
    preflight (env_gate ignores it; so does the derived list)."""
    pre = sweep_launcher.env_preflight([
        kernel("cuda"),
        kernel("some_future_kernel", ok=False, lines=("??",)),
    ])
    assert pre.can_launch is True
    assert pre.failed_kernels == ()


def test_env_preflight_delegates_to_the_frozen_face_verbatim(
        monkeypatch, tmp_path):
    """The preflight COMPOSES quick_check.run_quick_check ->
    env_gate.gate_verdict — both frozen (D-08); the spies prove the
    delegation happens through those exact functions, never a local
    re-implementation."""
    pin_state_dir(monkeypatch, tmp_path)
    qc_calls = []
    real_qc = quick_check.run_quick_check

    def qc_spy(kernels=None):
        qc_calls.append(kernels)
        return real_qc(kernels)

    gate_calls = []
    real_gate = env_gate.gate_verdict

    def gate_spy(results):
        gate_calls.append(results)
        return real_gate(results)

    monkeypatch.setattr(quick_check, "run_quick_check", qc_spy)
    monkeypatch.setattr(env_gate, "gate_verdict", gate_spy)

    kernels = [kernel("cuda", ok=False, lines=("no CUDA device",))]
    pre = sweep_launcher.env_preflight(kernels)

    assert qc_calls == [kernels]
    assert gate_calls == [real_qc(kernels)]
    assert pre.can_launch is False


# ===== gate_confirm_data (the fresh-preview summary) =====


def test_gate_confirm_data_recomputes_preview_and_summarizes(tmp_path):
    spec = gate_spec(tmp_path)
    double = RunConfigDouble(full_e2x=True)

    summary = sweep_launcher.gate_confirm_data(spec, double)

    assert double.preview_calls == 1      # FRESH — never a cached screen value
    assert double.official_calls == 1
    assert double.e2x_calls == 1
    assert summary.models == 1
    assert summary.tasks == 1
    assert summary.seeds == 1
    assert summary.cells == 1
    assert summary.output_root == spec.output_root
    assert summary.is_e2x is True
    assert summary.expected_phrase == "out"


def test_gate_confirm_data_non_e2x_over_real_module(tmp_path):
    spec = run_config.RunSpec(
        models=("plant-dnabert-6mer",), tasks=("GUE__emp_H3",),
        seeds=(42,), output_root=str(tmp_path / "out"))

    summary = sweep_launcher.gate_confirm_data(spec)

    assert summary.is_e2x is False       # 1 model x 1 task x 1 seed
    assert summary.models == 1
    assert summary.cells == 1
    assert summary.expected_phrase == "out"


def test_gate_confirm_data_pairs_first_occurrence_seeds_collapsed(
        tmp_path):
    """UX-5 (261016-poa): the confirm summary carries the planned
    (model, task) pairs — an ordered FIRST-OCCURRENCE dedupe of the
    FRESH preview cells over the REAL module. A 2x2x3 spec enumerates
    12 cells but exactly 4 pairs (seeds stay collapsed in the counts
    formula, never per-row); the order is the cells' own (sorted
    model-major) order, service-derived — the UI never computes."""
    spec = run_config.RunSpec(
        models=("DNABERT-2-117M", "plant-dnabert-6mer"),
        tasks=("GUE__emp_H3", "BEND__CpG_methylation"),
        seeds=(42, 43, 44), output_root=str(tmp_path / "out"))

    summary = sweep_launcher.gate_confirm_data(spec)

    assert summary.cells == 12
    assert list(summary.pairs) == [
        ("DNABERT-2-117M", "BEND__CpG_methylation"),
        ("DNABERT-2-117M", "GUE__emp_H3"),
        ("plant-dnabert-6mer", "BEND__CpG_methylation"),
        ("plant-dnabert-6mer", "GUE__emp_H3"),
    ]


def test_gate_confirm_data_pairs_curve_fractions_4tuples(tmp_path):
    """The same pairs derive under curve fractions — the 4-tuple cells
    (model, task, seed, fraction) project to the IDENTICAL pair list
    (cell[0], cell[1] is shape-agnostic)."""
    spec = run_config.RunSpec(
        models=("DNABERT-2-117M", "plant-dnabert-6mer"),
        tasks=("GUE__emp_H3", "BEND__CpG_methylation"),
        seeds=(42,), curve_fractions=(0.25, 0.5),
        output_root=str(tmp_path / "out"))

    summary = sweep_launcher.gate_confirm_data(spec)

    assert summary.cells == 8            # 2 x 2 x 1 x 2 fractions
    assert list(summary.pairs) == [
        ("DNABERT-2-117M", "BEND__CpG_methylation"),
        ("DNABERT-2-117M", "GUE__emp_H3"),
        ("plant-dnabert-6mer", "BEND__CpG_methylation"),
        ("plant-dnabert-6mer", "GUE__emp_H3"),
    ]


# ===== launch_spec (the structural gate — D-07 / LNC-03) =====


def test_launch_spec_problems_refuse_before_spawn(monkeypatch, tmp_path):
    pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()
    spec = run_config.RunSpec(
        models=(), tasks=(), output_root=str(tmp_path / "out"))

    result = launcher.launch_spec(spec, spawner=spawner)

    assert isinstance(result, sweep_launcher.GateRefusal)
    assert result.stage == "problems"
    assert ("empty_selection", None) in result.problems
    assert spawner.calls == []           # the spawner-silent proof


def test_launch_spec_official_keys_diagnostic_refuses(monkeypatch,
                                                      tmp_path):
    """The fail-closed reference (T-11-02-02): unreadable official
    registries must BLOCK — never compare against silently-empty sets
    that a full-matrix spec would trivially satisfy."""
    pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()
    diagnostic = "unreadable or shape-invalid: pipeline/models_info.json"
    double = RunConfigDouble(official=run_config.OfficialKeys(
        frozenset(), frozenset(), diagnostic))

    result = launcher.launch_spec(
        gate_spec(tmp_path), run_config_service=double, spawner=spawner)

    assert isinstance(result, sweep_launcher.GateRefusal)
    assert result.stage == "problems"
    assert ("official_keys", diagnostic) in result.problems
    assert spawner.calls == []


def test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent(
        monkeypatch, tmp_path):
    """THE LNC-03 structural proof: an E2' verdict with a wrong phrase
    refuses with ZERO spawner calls (call-count evidence, not return
    shape — T-11-03-01)."""
    pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()
    double = RunConfigDouble(full_e2x=True)

    result = launcher.launch_spec(
        gate_spec(tmp_path), phrase="wrong", run_config_service=double,
        spawner=spawner)

    assert isinstance(result, sweep_launcher.GateRefusal)
    assert result.stage == "phrase"
    assert result.expected == "out"
    assert spawner.calls == []
    assert double.e2x_calls == 1          # the verdict was recomputed FRESH


def test_launch_spec_e2x_absent_phrase_refuses(monkeypatch, tmp_path):
    pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()
    double = RunConfigDouble(full_e2x=True)

    result = launcher.launch_spec(
        gate_spec(tmp_path), run_config_service=double, spawner=spawner)

    assert isinstance(result, sweep_launcher.GateRefusal)
    assert result.stage == "phrase"
    assert result.expected == "out"
    assert spawner.calls == []


def test_launch_spec_e2x_phrase_match_is_exact(monkeypatch, tmp_path):
    """No normalization sneaks past the gate: case-mismatched,
    whitespace-padded, and prefix phrases all refuse (the exact-match
    service check re-proven at the launch tier)."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()
    double = RunConfigDouble(full_e2x=True)
    for typed in ("OUT", " out ", "ou"):
        spawner = FakeSpawner()
        result = launcher.launch_spec(
            gate_spec(tmp_path), phrase=typed, run_config_service=double,
            spawner=spawner)
        assert isinstance(result, sweep_launcher.GateRefusal), typed
        assert result.stage == "phrase"
        assert spawner.calls == [], typed


def test_launch_spec_e2x_matching_phrase_spawns(monkeypatch, tmp_path):
    pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()
    double = RunConfigDouble(full_e2x=True, argv=["py", "run_sweep.py",
                                                  "--models", "m"])

    outcome = launcher.launch_spec(
        gate_spec(tmp_path), phrase="out", run_config_service=double,
        spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True
    assert double.compose_calls == 1
    argv, kwargs = single_call(spawner)
    assert argv == ["py", "run_sweep.py", "--models", "m"]
    assert kwargs["start_new_session"] is True


def test_launch_spec_non_e2x_without_phrase_spawns_over_real_module(
        monkeypatch, tmp_path):
    """A small non-E2' spec needs NO phrase and launches over the REAL
    run_config verdict chain (preview -> official_keys -> is_full_e2x
    -> compose_argv)."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()
    spec = run_config.RunSpec(
        models=("plant-dnabert-6mer",), tasks=("GUE__emp_H3",),
        seeds=(42,), output_root=str(tmp_path / "out"))
    spawner = FakeSpawner(FakeSweepPopen(poll_returns=[None]))

    outcome = launcher.launch_spec(
        spec, spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True
    argv, kwargs = single_call(spawner)
    assert argv == run_config.compose_argv(spec)   # consumed VERBATIM
    assert kwargs["cwd"] == str(REPO_ROOT / "pipeline")
    assert launcher.live_sweeps() == (str((tmp_path / "out").resolve()),)


def test_launch_spec_recomputes_despite_screen_preview(monkeypatch,
                                                       tmp_path):
    """T-11-03-02: the gate NEVER trusts the screen's cached preview —
    launch_spec re-runs preview/official_keys/is_full_e2x even though
    gate_confirm_data already did (the spy counter delta)."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()
    spec = gate_spec(tmp_path)
    double = RunConfigDouble(full_e2x=False)

    sweep_launcher.gate_confirm_data(spec, double)   # the screen's preview
    assert double.preview_calls == 1

    outcome = launcher.launch_spec(
        spec, run_config_service=double, spawner=FakeSpawner())

    assert outcome.spawned is True
    assert double.preview_calls == 2
    assert double.official_calls == 2
    assert double.e2x_calls == 2


def test_launch_spec_registry_key_rides_repo_root_basis_from_any_cwd(
        monkeypatch, tmp_path):
    """WR-01 (gap #2): with the TUI process CWD OUTSIDE the repo and a
    relative ``spec.output_root``, launch_spec registers the
    REPO_ROOT-resolved root — the SAME basis ``compose_argv`` threads
    (``rc.resolve_dirs(spec).output_root_abs``, D-14) — so the registry
    key, the argv ``--output-root`` element, and ``live_sweeps()`` all
    agree; no phantom ``{cwd}``-rooted control-plane key. Pre-fix
    reproduction (from the verification pass): ``outcome.root`` was
    ``{tmp}/finetuned`` while the argv said ``{repo}/finetuned``."""
    pin_state_dir(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)   # CWD != REPO_ROOT at launch time
    launcher = sweep_launcher.SweepLauncher()
    spec = run_config.RunSpec(
        models=("plant-dnabert-6mer",), tasks=("GUE__emp_H3",),
        seeds=(42,), output_root="finetuned")
    spawner = FakeSpawner(FakeSweepPopen(poll_returns=[None]))

    outcome = launcher.launch_spec(
        spec, spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True
    repo_key = str((REPO_ROOT / "finetuned").resolve())
    assert outcome.root == repo_key, (
        "the registry key rides the argv's REPO_ROOT basis — never the "
        "TUI process CWD"
    )
    argv, _kwargs = single_call(spawner)
    assert argv[argv.index("--output-root") + 1] == repo_key, (
        "the registry key and the argv --output-root are ONE basis"
    )
    assert launcher.live_sweeps() == (repo_key,)


# ===== launch_argv (the raw pre-composed seam) =====


def test_launch_argv_spawns_precomposed_argv(monkeypatch, tmp_path):
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()
    spawner = FakeSpawner(FakeSweepPopen(poll_returns=[None]))

    outcome = launcher.launch_argv(
        ["py", "run_sweep.py", "--from-failures", "f.json"],
        tmp_path / "out", spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True
    argv, kwargs = single_call(spawner)
    assert argv == ["py", "run_sweep.py", "--from-failures", "f.json"]
    assert kwargs["start_new_session"] is True
    assert launcher.live_sweeps() == (str((tmp_path / "out").resolve()),)


# =====================================================================
# Lane 3 — the from-failures re-run path + the raw seam's no-gate
# proof (Task 3, D-11)
# =====================================================================


def test_launch_from_failures_composes_and_spawns(monkeypatch, tmp_path):
    """The [r] re-run composes via run_config.compose_from_failures_argv
    and launches through the SAME seam: resolved failures path, seeds,
    ABSOLUTE output root — and the tee names after the re-run root."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher()
    failures = tmp_path / "sweep_failures.json"
    failures.write_text("[]", encoding="utf-8")
    out_root = tmp_path / "rerun"
    spawner = FakeSpawner(FakeSweepPopen(poll_returns=[None]))

    outcome = launcher.launch_from_failures(
        failures, (42, 43), out_root, spawner=spawner,
        clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True
    argv, kwargs = single_call(spawner)
    assert argv[:3] == [
        sys.executable, str(run_config.RUN_SWEEP_SCRIPT), "--from-failures"]
    assert argv[argv.index("--from-failures") + 1] == str(failures.resolve())
    assert argv[argv.index("--seeds") + 1] == "42,43"
    assert argv[argv.index("--output-root") + 1] == str(out_root.resolve())
    assert kwargs["start_new_session"] is True
    assert kwargs["cwd"] == str(REPO_ROOT / "pipeline")
    assert outcome.tee_path.endswith("sweep_20261013_083005_rerun.log")
    assert launcher.live_sweeps() == (str(out_root.resolve()),)


def test_launch_from_failures_threads_alias_flags(monkeypatch, tmp_path):
    pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()
    failures = tmp_path / "sweep_failures.json"
    failures.write_text("[]", encoding="utf-8")

    outcome = launcher.launch_from_failures(
        failures, (42,), tmp_path / "rerun", peft="lora",
        config_variant="head", spawner=spawner,
        clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True
    argv, _ = single_call(spawner)
    assert argv[argv.index("--peft") + 1] == "lora"
    assert argv[argv.index("--config-variant") + 1] == "head"


def test_launch_argv_e2x_shaped_matrix_argv_is_not_phrase_gated(
        monkeypatch, tmp_path):
    """The RAW ``launch_argv`` seam contract (unchanged by CR-01): it
    takes no spec and never consults the phrase seam — pinned here so
    the composed path's new gate (below) is provably a
    ``launch_from_failures`` concern, never a raw-seam behavior change.
    The COMPOSED UI path ([f]→[r]) is gated in ``launch_from_failures``
    (CR-01: a complete failures manifest over 3 seeds IS the full
    matrix); full-matrix spec launches go through ``launch_spec``
    (lane 2's spawner-silent proof)."""
    pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()
    official = run_config.official_keys()
    assert official.diagnostic is None      # the reference loads
    argv = [
        "py", "run_sweep.py",
        "--models", ",".join(sorted(official.models)),
        "--tasks", ",".join(sorted(official.tasks)),
        "--seeds", "42,43,44",
        "--output-root", str(tmp_path / "out"),
    ]

    outcome = launcher.launch_argv(
        argv, tmp_path / "out", spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True          # no gate consulted
    assert len(spawner.calls) == 1


# ===== the CR-01 gate: a from-failures re-run CAN be the full matrix =====


def complete_failures_manifest(tmp_path, official):
    """A GENUINE driver-written complete failures manifest: every
    official (model, task) pair failed once — exactly what run_sweep
    writes when a full sweep fails every cell (repo/env fault that
    passes preflight, disk-full hitting each cell, a bad --subset_file).
    The CR-01 shape: un-hand-edited, yet the [f]→[r] re-run's effective
    matrix over 3 seeds IS the full E2' matrix."""
    entries = [
        {
            "model": model,
            "base_model": model,
            "task": task,
            "seed": 42,
            "output_dir": f"/root/{model}/{task}/seed_42",
            "error": "boom",
        }
        for model in sorted(official.models)
        for task in sorted(official.tasks)
    ]
    path = tmp_path / "sweep_failures.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def test_launch_from_failures_complete_manifest_three_seeds_demands_phrase(
        monkeypatch, tmp_path):
    """CR-01: a complete failures manifest re-run over the sweep's 3
    seeds is the full 8850-cell matrix — the E2' typed gate applies
    exactly as ``launch_spec`` applies it (refusal BEFORE the spawner)."""
    pin_state_dir(monkeypatch, tmp_path)
    official = run_config.official_keys()
    assert official.diagnostic is None
    failures = complete_failures_manifest(tmp_path, official)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()

    result = launcher.launch_from_failures(
        failures, (42, 43, 44), tmp_path / "rerun", spawner=spawner)

    assert isinstance(result, sweep_launcher.GateRefusal)
    assert result.stage == sweep_launcher.REFUSAL_STAGE_PHRASE
    assert result.expected == "rerun"
    assert spawner.calls == []           # the spawner-silent proof


def test_launch_from_failures_complete_manifest_matching_phrase_spawns(
        monkeypatch, tmp_path):
    """The matching phrase passes the same gate — the re-run is never
    refused outright, only phrase-escalated."""
    pin_state_dir(monkeypatch, tmp_path)
    official = run_config.official_keys()
    failures = complete_failures_manifest(tmp_path, official)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()

    outcome = launcher.launch_from_failures(
        failures, (42, 43, 44), tmp_path / "rerun", phrase="rerun",
        spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True
    argv, _ = single_call(spawner)
    assert "--from-failures" in argv


def test_launch_from_failures_partial_manifest_never_phrase_gated(
        monkeypatch, tmp_path):
    """The ordinary re-run shape (a partial failures manifest) stays
    ungated — the gate escalates ONLY on the E2'-class effective
    matrix."""
    pin_state_dir(monkeypatch, tmp_path)
    partial = tmp_path / "sweep_failures.json"
    partial.write_text(json.dumps([
        {"model": "plant-dnabert-6mer", "base_model": "plant-dnabert-6mer",
         "task": "GUE__emp_H3", "seed": 42, "error": "boom"},
    ]), encoding="utf-8")
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()

    outcome = launcher.launch_from_failures(
        partial, (42, 43, 44), tmp_path / "rerun",
        spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True       # no phrase demanded


def test_launch_from_failures_complete_manifest_two_seeds_below_boundary(
        monkeypatch, tmp_path):
    """Two seeds are below the three-seed authorization boundary (D-02):
    even a complete manifest re-run stays on the generic confirm."""
    pin_state_dir(monkeypatch, tmp_path)
    official = run_config.official_keys()
    failures = complete_failures_manifest(tmp_path, official)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()

    outcome = launcher.launch_from_failures(
        failures, (42, 43), tmp_path / "rerun",
        spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True


def test_launch_from_failures_official_keys_diagnostic_refuses(
        monkeypatch, tmp_path):
    """Fail-closed (the launch_spec twin): unreadable official registries
    must BLOCK the re-run at the problems stage — never compare against
    silently-empty sets."""
    pin_state_dir(monkeypatch, tmp_path)
    partial = tmp_path / "sweep_failures.json"
    partial.write_text("[]", encoding="utf-8")
    diagnostic = "unreadable or shape-invalid: pipeline/models_info.json"
    double = RunConfigDouble(official=run_config.OfficialKeys(
        frozenset(), frozenset(), diagnostic))
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()

    result = launcher.launch_from_failures(
        partial, (42,), tmp_path / "rerun",
        run_config_service=double, spawner=spawner)

    assert isinstance(result, sweep_launcher.GateRefusal)
    assert result.stage == sweep_launcher.REFUSAL_STAGE_PROBLEMS
    assert ("official_keys", diagnostic) in result.problems
    assert spawner.calls == []


def test_launch_from_failures_unreadable_manifest_refuses_fail_closed(
        monkeypatch, tmp_path):
    """A manifest the gate cannot evaluate (missing/unparseable/invalid
    entries — load_failure_pairs exits) refuses at the problems stage:
    the child would fail-fast too, and an unevaluatable matrix is never
    launched ungated."""
    pin_state_dir(monkeypatch, tmp_path)
    missing = tmp_path / "nope" / "sweep_failures.json"
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher()

    result = launcher.launch_from_failures(
        missing, (42,), tmp_path / "rerun", spawner=spawner)

    assert isinstance(result, sweep_launcher.GateRefusal)
    assert result.stage == sweep_launcher.REFUSAL_STAGE_PROBLEMS
    code, detail = result.problems[0]
    assert code == "failures_manifest"
    assert "nope" in str(detail)
    assert spawner.calls == []


# =====================================================================
# EHC-3 (261015-ehc ruling 3) — the single-GPU serialization guard
# =====================================================================


def test_effective_gpu_count_world_size_wins_never_imports_torch():
    """EHC-3: WORLD_SIZE parses as the effective count (>= 1 wins) and
    torch is NEVER imported on that path — proven in a fresh ``-I``
    subprocess (the dev venv holds torch, so an in-process
    sys.modules assert proves nothing — the 11-02 discipline)."""
    import subprocess as sp

    repo = Path(__file__).resolve().parents[2]
    probe = (
        "import os, sys; os.environ['WORLD_SIZE'] = '4'; "
        f"sys.path.insert(0, {str(repo / 'pipeline')!r}); "
        f"sys.path.insert(0, {str(repo)!r}); "
        "from tui.services import sweep_launcher; "
        "assert sweep_launcher.effective_gpu_count() == 4; "
        "assert 'torch' not in sys.modules; print('OK')"
    )
    result = sp.run(
        [sys.executable, "-I", "-c", probe],
        capture_output=True, text=True, timeout=60, check=False)
    assert result.returncode == 0 and "OK" in result.stdout, (
        f"probe failed: {result.stderr}")


def test_effective_gpu_count_torch_absent_is_zero(monkeypatch):
    """A torch-free machine reads 0 (unrestricted per the ruling's
    letter) — never an import error."""
    monkeypatch.delenv("WORLD_SIZE", raising=False)
    monkeypatch.setitem(sys.modules, "torch", None)  # import -> ImportError
    assert sweep_launcher.effective_gpu_count() == 0


def test_effective_gpu_count_tolerant_of_every_exception(monkeypatch):
    """T-ehc-04: a raising torch probe (broken CUDA, exotic import
    faults) degrades to 0 — the function never raises."""

    class _Boom:
        @staticmethod
        def is_available():
            raise RuntimeError("cuda init exploded")

    fake_torch = types.ModuleType("torch")
    fake_torch.cuda = _Boom()  # ty: ignore[unresolved-attribute]
    monkeypatch.delenv("WORLD_SIZE", raising=False)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    assert sweep_launcher.effective_gpu_count() == 0


def test_effective_gpu_count_lazy_torch_reads_device_count(monkeypatch):
    """The lazy torch path: cuda available -> torch.cuda.device_count()
    (which honors CUDA_VISIBLE_DEVICES — the device-count reading IS the
    serialization signal on a masked box)."""

    class _Cuda:
        @staticmethod
        def is_available():
            return True

        @staticmethod
        def device_count():
            return 1

    fake_torch = types.ModuleType("torch")
    fake_torch.cuda = _Cuda()  # ty: ignore[unresolved-attribute]
    monkeypatch.delenv("WORLD_SIZE", raising=False)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    assert sweep_launcher.effective_gpu_count() == 1


def _live_single_gpu_launcher(monkeypatch, tmp_path, gpu_count=1):
    """A launcher pinned at ``gpu_count`` with ONE live registry entry
    (a never-dying fake Popen over a tmp output root)."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher(gpu_count=gpu_count)
    seeded = FakeSpawner(FakeSweepPopen(poll_returns=(None,)))
    root = tmp_path / "live-out"
    outcome = launcher._spawn(["py", "run_sweep.py"], root, spawner=seeded)
    assert outcome.spawned is True
    return launcher, str(root.resolve())


def test_single_gpu_busy_refuses_launch_spec_before_every_stage(
        monkeypatch, tmp_path):
    """EHC-3 call-count proof (the LNC-03 evidence style): on
    gpu_count == 1 with a live sweep, launch_spec refuses at the
    single_gpu stage BEFORE any preview/official-keys/phrase stage —
    the run_config double's counters stay ZERO and the spawner is
    provably never called."""
    launcher, root = _live_single_gpu_launcher(monkeypatch, tmp_path)
    double = RunConfigDouble()
    spawner = FakeSpawner()

    result = launcher.launch_spec(
        gate_spec(tmp_path), phrase=None,
        run_config_service=double, spawner=spawner)

    assert isinstance(result, sweep_launcher.GateRefusal)
    assert result.stage == sweep_launcher.REFUSAL_STAGE_SINGLE_GPU
    code, detail = result.problems[0]
    assert code == sweep_launcher.PROBLEM_SINGLE_GPU
    assert root in str(detail), "the refusal names the running root"
    assert double.preview_calls == 0, "refused BEFORE the preview stage"
    assert double.official_calls == 0, "refused BEFORE the keys stage"
    assert double.e2x_calls == 0, "refused BEFORE the E2' predicate"
    assert double.compose_calls == 0
    assert spawner.calls == [], "the spawner is provably never called"


def test_single_gpu_busy_refuses_launch_from_failures_first(
        monkeypatch, tmp_path):
    """The EHC-3 twin on the re-run path: a busy single-GPU machine
    refuses launch_from_failures BEFORE any manifest evaluation —
    the spawner is never called."""
    launcher, root = _live_single_gpu_launcher(monkeypatch, tmp_path)
    spawner = FakeSpawner()
    failures = tmp_path / "sweep_failures.json"
    failures.write_text("[]", encoding="utf-8")

    result = launcher.launch_from_failures(
        failures, (42,), tmp_path / "rerun", spawner=spawner)

    assert isinstance(result, sweep_launcher.GateRefusal)
    assert result.stage == sweep_launcher.REFUSAL_STAGE_SINGLE_GPU
    assert root in str(result.problems[0][1])
    assert spawner.calls == []


def test_multi_gpu_machine_launches_normally(monkeypatch, tmp_path):
    """gpu_count >= 2 is unrestricted: a live sweep does NOT block the
    launch (the spawner runs)."""
    launcher, _root = _live_single_gpu_launcher(
        monkeypatch, tmp_path, gpu_count=2)
    spawner = FakeSpawner()
    double = RunConfigDouble()

    result = launcher.launch_spec(
        gate_spec(tmp_path), run_config_service=double, spawner=spawner)

    assert isinstance(result, sweep_launcher.LaunchOutcome)
    assert result.spawned is True
    assert len(spawner.calls) == 1


def test_count_zero_machine_unrestricted(monkeypatch, tmp_path):
    """gpu_count == 0 (torch/CUDA unavailable) is unrestricted per the
    ruling's letter — a live registry entry does not block."""
    launcher, _root = _live_single_gpu_launcher(
        monkeypatch, tmp_path, gpu_count=0)
    spawner = FakeSpawner()

    result = launcher.launch_spec(
        gate_spec(tmp_path), spawner=spawner)

    assert isinstance(result, sweep_launcher.LaunchOutcome)
    assert result.spawned is True


def test_single_gpu_idle_machine_launches_normally(monkeypatch, tmp_path):
    """gpu_count == 1 with NO live entry is unrestricted — the guard
    serializes contention, not the machine."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher(gpu_count=1)
    spawner = FakeSpawner()

    assert launcher.single_gpu_launch_blocked() is None
    result = launcher.launch_spec(gate_spec(tmp_path), spawner=spawner)

    assert isinstance(result, sweep_launcher.LaunchOutcome)
    assert result.spawned is True


# =====================================================================
# 261017-uwr — live-sweep matrix evidence (UWR-2 Task 1): the /proc
# CLI probe + live_sweep_matrices (registry handles UNION probed roots,
# behind the per-argv matrix cache; the kill face stays registry-only)
# =====================================================================


def _write_cmdline(pid_dir, argv_elements):
    """One fake /proc/<pid>/cmdline: NUL-separated argv bytes."""
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / "cmdline").write_bytes(
        b"\0".join(element.encode("utf-8") for element in argv_elements)
        + b"\0")


def _write_pid_stat(pid_dir, starttime_ticks):
    """One fake /proc/<pid>/stat (261020-9vh): the FULL paren shape
    ``"<pid> (python) S <fields> {ticks} 0"`` so index 19 of the
    post-paren fields is field 22, starttime (the /proc man page's
    1-based field numbering against the 0-based split)."""
    pid_dir.mkdir(parents=True, exist_ok=True)
    (pid_dir / "stat").write_text(
        "4001 (python) S 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 0 "
        f"{starttime_ticks} 0\n", encoding="utf-8")


def _write_proc_btime(proc_root, btime):
    """One fake /proc/stat carrying the boot-time line (261020-9vh)."""
    proc_root.mkdir(parents=True, exist_ok=True)
    (proc_root / "stat").write_text(
        "cpu  100 0 100 1000 0 0 0 0 0 0\n"
        f"btime {btime}\n"
        "cpu0 100 0 100 1000 0 0 0 0 0 0\n", encoding="utf-8")


def _probe_argv(models="plant-dnabert-6mer", output_root=None,
               driver=None, extra=(), tasks="GUE__emp_H3", seeds="42"):
    """One parseable run_sweep argv (the compose_argv shape). 261020-blt:
    ``tasks``/``seeds`` join ADDITIVELY (defaults keep every existing
    call site's argv byte-identical)."""
    return [
        sys.executable,
        str(driver if driver is not None
            else REPO_ROOT / "pipeline" / "run_sweep.py"),
        "--models", models,
        "--tasks", tasks,
        "--seeds", seeds,
        "--output-root",
        str(output_root if output_root is not None else "/tmp/uwr-probe"),
        *extra,
    ]


def test_probe_cli_sweeps_maps_run_sweep_processes_to_resolved_roots(
        tmp_path):
    """The bounded /proc probe over a FAKE proc root: one run_sweep.py
    process maps {resolved --output-root: argv}; an unrelated python
    process is ignored; an unreadable pid dir (a cmdline that cannot be
    opened) is skipped; an absent proc root reads {} (non-Linux
    degrades to no CLI evidence — honest)."""
    proc = tmp_path / "proc"
    sweep_argv = _probe_argv(output_root=tmp_path / "out" / "sweep-a")
    _write_cmdline(proc / "1001", sweep_argv)
    _write_cmdline(proc / "1002", [
        sys.executable, "-m", "http.server", "8080"])
    # an unreadable pid: cmdline is a DIRECTORY -> open raises OSError
    (proc / "1003" / "cmdline").mkdir(parents=True)
    (proc / "notapid").mkdir()

    probed = sweep_launcher.probe_cli_sweeps(proc)

    assert probed == {
        str((tmp_path / "out" / "sweep-a").resolve()): tuple(sweep_argv)}
    assert sweep_launcher.probe_cli_sweeps(tmp_path / "absent-proc") == {}


def test_probe_cli_sweeps_relative_root_resolves_against_proc_cwd(
        tmp_path):
    """A RELATIVE --output-root resolves against the process's own cwd
    (os.readlink(<pid>/cwd), best-effort): the CLI hand-run edge —
    compose_argv threads absolute roots by contract, but a bare
    ``python run_sweep.py --output-root rel/...`` launched from a shell
    writes relative to ITS cwd."""
    proc = tmp_path / "proc"
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    _write_cmdline(proc / "2001", _probe_argv(output_root="rel/out"))
    (proc / "2001" / "cwd").symlink_to(workdir, target_is_directory=True)

    probed = sweep_launcher.probe_cli_sweeps(proc)

    assert probed == {
        str((workdir / "rel" / "out").resolve()): tuple(
            _probe_argv(output_root="rel/out"))}


def test_probe_cli_sweeps_sweep_without_output_root_is_ignored(tmp_path):
    """A run_sweep.py process with no readable --output-root maps
    nothing (no root key, never a guessed one)."""
    proc = tmp_path / "proc"
    argv = [
        sys.executable, str(REPO_ROOT / "pipeline" / "run_sweep.py"),
        "--models", "plant-dnabert-6mer", "--seeds", "42"]
    _write_cmdline(proc / "3001", argv)

    assert sweep_launcher.probe_cli_sweeps(proc) == {}


def test_probe_cli_sweep_starts_reads_stat_and_btime(tmp_path):
    """261020-9vh — the start-time probe over the SAME walk: pid 4001
    holds a run_sweep.py cmdline plus a stat whose post-paren field 22
    is 65268188 ticks, and <proc>/stat carries ``btime 1791798278`` ->
    the resolved root maps to btime + ticks / SC_CLK_TCK (the
    maintainer's live arithmetic). A run_sweep pid whose stat file is
    ABSENT contributes nothing (tolerant); a tree without btime reads
    {} (no start evidence, never a crash — the honest degradation)."""
    proc = tmp_path / "proc"
    root_a = tmp_path / "out" / "sweep-a"
    _write_cmdline(proc / "4001", _probe_argv(output_root=root_a))
    _write_pid_stat(proc / "4001", 65268188)
    # a run_sweep pid with NO stat file (a dying process mid-read):
    # tolerated, contributes no start, never a raise
    _write_cmdline(proc / "4002", _probe_argv(
        models="plant-dnagpt-BPE", output_root=tmp_path / "out" / "b"))
    _write_proc_btime(proc, 1791798278)

    starts = sweep_launcher.probe_cli_sweep_starts(proc)

    ticks = os.sysconf("SC_CLK_TCK")
    assert starts == {
        str(root_a.resolve()): 1791798278 + 65268188 / ticks}, (
        "start = btime + field-22 ticks / SC_CLK_TCK (the verified "
        "live arithmetic: 1791798278 + 65268188/100)"
    )

    # no btime line: NO start evidence at all — {} (non-Linux degrades
    # to the same honest vocabulary as the argv probe)
    bare = tmp_path / "bare-proc"
    _write_cmdline(bare / "5001", _probe_argv(output_root=tmp_path / "x"))
    _write_pid_stat(bare / "5001", 65268188)
    assert sweep_launcher.probe_cli_sweep_starts(bare) == {}


def _register_live_sweep(monkeypatch, tmp_path, argv, root, clock=None):
    """One launcher with a LIVE registry entry (a never-dying fake
    Popen) spawned at ``root`` with ``argv`` — the registry half of the
    evidence union. ``clock`` (261020-9vh) pins the spawn moment for an
    exact ``started_at`` epoch; None uses the real clock."""
    pin_state_dir(monkeypatch, tmp_path)
    launcher = sweep_launcher.SweepLauncher(
        spawner=FakeSpawner(popen=FakeSweepPopen(poll_returns=(None,))))
    outcome = launcher.launch_argv(
        list(argv), root, spawner=FakeSpawner(
            popen=FakeSweepPopen(poll_returns=(None,))),
        clock=clock)
    assert outcome.spawned is True, outcome.error
    return launcher


def test_live_sweep_started_merges_registry_iso_and_probe(
        monkeypatch, tmp_path):
    """261020-9vh — the start-evidence merge: a registry entry spawned
    through launch_argv with the INJECTABLE clock pinned to a fixed
    tz-aware datetime maps its root to that EXACT epoch (the registry's
    spawn moment is authoritative — the tz-aware ISO round-trips); a
    monkeypatched probe_cli_sweep_starts supplies a second (CLI) root
    AND a duplicate of the registry root with a DIFFERENT value —
    setdefault keeps the registry's (the live_sweep_matrices
    precedence). The probe is monkeypatched at the MODULE level so the
    test never walks the dev box's REAL /proc (the maintainer's live
    sweep runs there)."""
    fixed = datetime(2026, 10, 20, 7, 2, 39, tzinfo=UTC)
    registry_root = tmp_path / "reg" / "root"
    launcher = _register_live_sweep(
        monkeypatch, tmp_path, _probe_argv(output_root=registry_root),
        registry_root, clock=lambda: fixed)

    cli_root = tmp_path / "cli" / "root"
    monkeypatch.setattr(sweep_launcher, "probe_cli_sweep_starts", lambda: {
        str(cli_root.resolve()): 1000.0,
        # the duplicate: the probe's value must LOSE to the registry's
        str(registry_root.resolve()): 999.0,
    })

    started = launcher.live_sweep_started()

    assert started == {
        str(registry_root.resolve()): fixed.timestamp(),
        str(cli_root.resolve()): 1000.0,
    }, (
        "registry started_at is authoritative per root; the probe "
        "union fills the roots the registry does not hold"
    )


def test_live_sweep_matrices_merges_registry_and_probe_behind_cache(
        monkeypatch, tmp_path):
    """live_sweep_matrices(): the registry entry's meta.argv matrix
    UNION the probed CLI roots; an unparseable argv maps its root to
    None (live-but-unknown — legacy rendering for that root, never a
    false interrupt); repeated calls with the same argv hit the
    per-argv matrix cache (enumerate_matrix counted ONCE via a spy)."""
    registry_argv = _probe_argv(models="plant-dnabert-6mer")
    launcher = _register_live_sweep(
        monkeypatch, tmp_path, registry_argv, tmp_path / "reg" / "root")

    probe_argv = _probe_argv(models="plant-dnagpt-BPE")
    probed_root = tmp_path / "cli" / "root"
    broken_argv = [
        sys.executable, str(REPO_ROOT / "pipeline" / "run_sweep.py"),
        "--models", "plant-dnabert-6mer",
        "--output-root", str(tmp_path / "cli" / "broken")]
    monkeypatch.setattr(sweep_launcher, "probe_cli_sweeps", lambda: {
        str(probed_root.resolve()): tuple(probe_argv),
        str((tmp_path / "cli" / "broken").resolve()): tuple(broken_argv),
    })

    real_enumerate = run_sweep.enumerate_matrix
    calls = []

    def spy(*args, **kwargs):
        calls.append(1)
        return real_enumerate(*args, **kwargs)

    monkeypatch.setattr(run_sweep, "enumerate_matrix", spy)

    matrices = launcher.live_sweep_matrices()

    assert set(matrices) == {
        str((tmp_path / "reg" / "root").resolve()),
        str(probed_root.resolve()),
        str((tmp_path / "cli" / "broken").resolve())}
    assert matrices[str((tmp_path / "reg" / "root").resolve())] == (
        frozenset({("plant-dnabert-6mer", "GUE__emp_H3")}))
    assert matrices[str(probed_root.resolve())] == (
        frozenset({("plant-dnagpt-BPE", "GUE__emp_H3")}))
    assert matrices[str((tmp_path / "cli" / "broken").resolve())] is None, (
        "an unparseable argv is live-but-unknown (None), never a matrix")

    assert len(calls) == 2, "two DISTINCT argvs enumerate twice"
    again = launcher.live_sweep_matrices()
    assert again == matrices
    assert len(calls) == 2, "the per-argv cache: no re-enumeration"


def test_live_sweep_plans_carries_pairs_and_seeds(monkeypatch, tmp_path):
    """261020-blt — live_sweep_plans(): the planned CELLS per root — a
    registry entry spawned with the multi-model 2x2 argv maps its root
    to (the 4-pair frozenset, (42, 43, 44)); a monkeypatched probe root
    joins behind the shared per-argv cache; a broken (no---seeds) argv
    maps None (live-but-unknown — that root keeps the legacy render,
    never a false queue). live_sweep_matrices over the SAME launcher
    returns exactly the leg-0 projection / None (the delegation proof),
    and the enumerate_matrix spy counts ONCE per distinct argv across
    BOTH methods (the per-argv plan cache)."""
    registry_argv = _probe_argv(
        models="plant-dnabert-6mer,plant-dnamamba-6mer",
        tasks="GUE__emp_H3,GUE__prom_300_all", seeds="42,43,44")
    launcher = _register_live_sweep(
        monkeypatch, tmp_path, registry_argv, tmp_path / "reg" / "root")

    probed_root = tmp_path / "cli" / "root"
    broken_argv = [
        sys.executable, str(REPO_ROOT / "pipeline" / "run_sweep.py"),
        "--models", "plant-dnabert-6mer",
        "--output-root", str(tmp_path / "cli" / "broken")]
    monkeypatch.setattr(sweep_launcher, "probe_cli_sweeps", lambda: {
        str(probed_root.resolve()): tuple(
            _probe_argv(models="plant-dnagpt-BPE", output_root=probed_root)),
        str((tmp_path / "cli" / "broken").resolve()): tuple(broken_argv),
    })

    real_enumerate = run_sweep.enumerate_matrix
    calls = []

    def spy(*args, **kwargs):
        calls.append(1)
        return real_enumerate(*args, **kwargs)

    monkeypatch.setattr(run_sweep, "enumerate_matrix", spy)

    plans = launcher.live_sweep_plans()

    registry_root = str((tmp_path / "reg" / "root").resolve())
    four_pairs = frozenset({
        ("plant-dnabert-6mer", "GUE__emp_H3"),
        ("plant-dnabert-6mer", "GUE__prom_300_all"),
        ("plant-dnamamba-6mer", "GUE__emp_H3"),
        ("plant-dnamamba-6mer", "GUE__prom_300_all"),
    })
    assert plans[registry_root] == (four_pairs, (42, 43, 44)), (
        "the registry's exact launch argv carries the 4-pair plan AND "
        "the seed fan-out"
    )
    assert plans[str(probed_root.resolve())] == (
        frozenset({("plant-dnagpt-BPE", "GUE__emp_H3")}), (42,))
    assert plans[str((tmp_path / "cli" / "broken").resolve())] is None, (
        "an unparseable argv is live-but-unknown (None), never a plan"
    )

    # the delegation proof: the matrices projection over the SAME
    # launcher reads leg 0 / None (the registry argv authoritative)
    matrices = launcher.live_sweep_matrices()
    assert matrices[registry_root] == four_pairs
    assert matrices[str(probed_root.resolve())] == frozenset(
        {("plant-dnagpt-BPE", "GUE__emp_H3")})
    assert matrices[str((tmp_path / "cli" / "broken").resolve())] is None

    # the per-argv cache is shared across BOTH methods: two parseable
    # argvs enumerated exactly twice (the broken argv never enumerates),
    # and the repeat calls re-read the cache
    assert len(calls) == 2, "two DISTINCT parseable argvs enumerate twice"
    assert launcher.live_sweep_plans() == plans
    assert launcher.live_sweep_matrices() == matrices
    assert len(calls) == 2, "the shared per-argv plan cache: no re-enumeration"


def test_live_sweep_matrices_probe_root_absent_from_registry_only(
        monkeypatch, tmp_path):
    """The merge precedence: a root BOTH sources report keeps the
    REGISTRY's argv (the exact launch argv is authoritative); the
    probe's duplicate never overwrites it."""
    registry_argv = _probe_argv(models="plant-dnabert-6mer")
    launcher = _register_live_sweep(
        monkeypatch, tmp_path, registry_argv, tmp_path / "shared" / "root")
    other_argv = _probe_argv(models="plant-dnagpt-BPE")
    monkeypatch.setattr(sweep_launcher, "probe_cli_sweeps", lambda: {
        str((tmp_path / "shared" / "root").resolve()): tuple(other_argv)})

    matrices = launcher.live_sweep_matrices()

    assert matrices[str((tmp_path / "shared" / "root").resolve())] == (
        frozenset({("plant-dnabert-6mer", "GUE__emp_H3")}))


def test_live_sweep_matrices_kill_face_stays_registry_only(
        monkeypatch, tmp_path):
    """UWR-2's kill pin: a probed CLI root joins the EVIDENCE (its
    cells render running) but NEVER the kill face — live_sweeps()
    lists registry handles only and kill_sweep() on a probe root is the
    documented noop (a probed sweep has no Popen handle in this
    process; [k] refuses with MON_KILL_UNAVAILABLE upstream)."""
    launcher = sweep_launcher.SweepLauncher()
    probe_argv = _probe_argv()
    probed_root = str((tmp_path / "cli" / "root").resolve())
    monkeypatch.setattr(sweep_launcher, "probe_cli_sweeps", lambda: {
        probed_root: tuple(probe_argv)})

    assert probed_root in launcher.live_sweep_matrices()
    assert probed_root not in launcher.live_sweeps(), (
        "the kill face is registry-only — a probe root never enters it")
    assert launcher.kill_sweep(probed_root) == (
        sweep_launcher.OUTCOME_NOOP)


# =====================================================================
# 261018-toe (slot-5 [e] Task 1): launch_from_pairs — the materialize-
# and-delegate seam. In-memory incomplete pairs derived by the screen
# land as a failures-shaped pairs file under the XDG STATE root, then
# the EXISTING launch_from_failures runs verbatim (single-GPU stage-0,
# official-keys, the E2' phrase gate over the pairs×seeds effective
# matrix, composition, spawn — zero duplicated gate logic).
# =====================================================================


def test_launch_from_pairs_materializes_state_dir_file_and_delegates(
        monkeypatch, tmp_path):
    """The seam's happy path: the pairs file lands under
    ``state_dir()/resume/resume_pairs_{rootname}.json`` as the driver's
    own failures-entry shape (alias verbatim + ``base_model`` with the
    stripped base only for suffixed names), and the child's
    ``--from-failures`` argv names THAT file with the threaded lane."""
    state = pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner(FakeSweepPopen(poll_returns=(None,)))
    launcher = sweep_launcher.SweepLauncher(spawner=spawner)
    out_root = tmp_path / "finetuned"

    outcome = launcher.launch_from_pairs(
        (("plant-dnabert-6mer+lora", "GUE__emp_H3"),
         ("DNABERT-2-117M", "BEND__CpG_methylation")),
        (42,), out_root, peft="lora",
        spawner=spawner, clock=FixedClock(CLOCK_MOMENT))

    assert outcome.spawned is True
    pairs_path = state / "resume" / "resume_pairs_finetuned.json"
    entries = json.loads(pairs_path.read_text(encoding="utf-8"))
    assert entries == [
        {"model": "plant-dnabert-6mer+lora", "task": "GUE__emp_H3",
         "base_model": "plant-dnabert-6mer"},
        {"model": "DNABERT-2-117M", "task": "BEND__CpG_methylation"},
    ], ("the driver's own failures-entry shape in the caller's (sorted) "
        "pair order — base_model only when the name carries a "
        "+lora/+ia3 suffix")
    argv, _ = single_call(spawner)
    assert argv[argv.index("--from-failures") + 1] == str(
        pairs_path.resolve()), "the child reads the materialized file"
    assert argv[argv.index("--peft") + 1] == "lora", (
        "the threaded lane rides the delegation verbatim")
    assert argv[argv.index("--seeds") + 1] == "42"


def test_launch_from_pairs_full_matrix_demands_phrase_spawner_silent(
        monkeypatch, tmp_path):
    """A full-matrix incomplete set over >= 3 seeds refuses at the
    phrase stage exactly like a complete failures manifest — the gate is
    the DELEGATED launch_from_failures' own (spawner call-count proof),
    and a same-shape call with the matching phrase spawns with the
    state-dir file."""
    pin_state_dir(monkeypatch, tmp_path)
    official = run_config.official_keys()
    assert official.diagnostic is None
    pairs = tuple(
        (model, task)
        for model in sorted(official.models)
        for task in sorted(official.tasks))
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher(spawner=spawner)

    refusal = launcher.launch_from_pairs(
        pairs, (42, 43, 44), tmp_path / "rerun", spawner=spawner)

    assert isinstance(refusal, sweep_launcher.GateRefusal)
    assert refusal.stage == sweep_launcher.REFUSAL_STAGE_PHRASE
    assert refusal.expected == "rerun"
    assert spawner.calls == [], (
        "the spawner is provably never called for a refused launch")

    outcome = launcher.launch_from_pairs(
        pairs, (42, 43, 44), tmp_path / "rerun", phrase="rerun",
        spawner=spawner, clock=FixedClock(CLOCK_MOMENT))
    assert outcome.spawned is True, (
        "the matching phrase passes the same gate")
    argv, _ = single_call(spawner)
    assert "resume_pairs_rerun.json" in argv[
        argv.index("--from-failures") + 1]


def test_launch_from_pairs_single_gpu_busy_refuses_first(
        monkeypatch, tmp_path):
    """EHC-3 order through the seam: a busy single-GPU machine refuses
    at stage-0 — the delegated guard runs BEFORE any manifest
    evaluation or phrase (the launch_from_failures twin)."""
    state = pin_state_dir(monkeypatch, tmp_path)
    spawner = FakeSpawner()
    launcher = sweep_launcher.SweepLauncher(
        spawner=spawner, gpu_count=1)
    assert launcher.launch_argv(
        ["py", "run_sweep.py", "--output-root",
         str(tmp_path / "busy")],
        tmp_path / "busy", spawner=FakeSpawner(
            popen=FakeSweepPopen(poll_returns=(None,)))).spawned is True

    refusal = launcher.launch_from_pairs(
        (("plant-dnabert-6mer", "GUE__emp_H3"),),
        (42,), tmp_path / "rerun", spawner=spawner)

    assert isinstance(refusal, sweep_launcher.GateRefusal)
    assert refusal.stage == sweep_launcher.REFUSAL_STAGE_SINGLE_GPU
    assert spawner.calls == []
    # the file is written BEFORE delegation (the child reads it at
    # startup) — it stands even under the stage-0 refusal
    assert (state / "resume" / "resume_pairs_rerun.json").exists()
