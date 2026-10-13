"""
sweep_launcher — the launch lifecycle service (Phase 11, 11-03;
LNC-01/02/03 + MON-04).

The whole execution tier of the operator loop: the injectable Popen
seam with the detached tee launch, the live-sweep registry with
kill/detach semantics, the env preflight over the FROZEN phase-8 face,
and the structurally-enforced E2' phrase gate wrapping run_config's
verdicts. Every launch path — the screen's [enter] gate and the
monitor's [r] re-run — routes through THIS service's seam; screens
present, never execute (D-06/D-07).

Contract (locked decisions):

- D-06 (execution is ALWAYS a run_sweep.py subprocess): LIST argv,
  ``start_new_session=True`` (the whole child tree one process group),
  cwd pinned to the repo's ``pipeline/`` (the driver's documented
  run-from-repo contract), and env EXACTLY
  ``{**os.environ, "PYTHONUNBUFFERED": "1"}``. PYTHONUNBUFFERED is
  load-bearing (Pitfall 4): with a file destination Python
  block-buffers stdout, and the monitor's tee tail would starve. This
  module NEVER launches run_sweep in-process and NEVER launches
  run_finetune directly — every execution path goes through the
  Popen seam (``_default_spawner``, copied verbatim from the phase-10
  ``download_queue`` seam).
- D-10 (single persistence root): the tee file lands under
  ``settings.state_dir() / "logs"`` — the SAME XDG state root as the
  queue/env-check state — named
  ``sweep_{YYYYmmdd_HHMMSS}_{rootname}.log`` with ``{rootname}`` the
  RESOLVED output root's final path component (the E2' phrase identity,
  making the log self-describing). A second persistence root (e.g. the
  output dir) is prohibited. The tee handle stays open for the child's
  lifetime: the launcher does NOT pump or close it early; the monitor
  tails the file by path. A spawn that fails (OSError) unlinks the
  empty tee file — nothing launched leaves no log.
- D-06 exit triple: ``kill_sweep`` SIGTERMs the process group via
  ``os.killpg(os.getpgid(pid))`` with SIGKILL escalation (the
  ``download_queue._signal_group`` discipline, copied verbatim);
  ``detach`` drops the handle with NO wait and NO kill (the sweep
  survives as an orphaned session leader — resume-safe by the
  trainer_state marker contract); ``live_sweeps`` lists live roots for
  the ExitModal predicate and the monitor's Popen-alive injection.
- D-08 (env preflight over the frozen face): ``env_preflight`` composes
  ``quick_check.run_quick_check`` -> ``env_gate.gate_verdict`` VERBATIM
  — zero edits to either phase-8 service; the kernel list is injectable
  so CI runs fakes. failed_kernels names the CRITICAL kernel failures
  in input order (the same names env_gate classifies).
- D-07 (the E2' boundary is structural): ``launch_spec`` recomputes the
  preview and the ``is_full_e2x`` verdict FRESH — never trusting a
  cached screen value — blocks on any preview problem or official-keys
  diagnostic, and refuses (the spawner is PROVABLY never called) when
  the spec is E2' and the typed phrase does not exactly match
  ``run_config.expected_phrase``. No widget path can reach ``_spawn``
  for a full-matrix spec without this check passing (LNC-03,
  T-11-03-01/02).
- D-11 (the [r] re-run): ``launch_from_failures`` composes via
  ``run_config.compose_from_failures_argv`` and routes through the
  SAME launch seam. A from-failures enumeration is EXACTLY the failed
  (model, task) pairs of a prior sweep — never the full matrix by
  construction — so the E2' typed gate does not apply; the raw
  ``launch_argv`` seam is from-failures-only by construction (its
  docstring carries the warning).

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by ``tests/tui/test_import_lock.py``
— the glob extends over this module automatically). ZERO Chinese
literals (the WR-05 services i18n lock). Dependencies: stdlib + the
sibling ``settings`` (state root) / ``quick_check`` + ``env_gate`` (the
frozen phase-8 face) / ``run_config`` (the 11-02 verdict + argv
composition) services.
"""

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tui.services import env_gate, quick_check, run_config, settings

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The sweep driver's working directory (D-06: pinned so the
#: subprocess's own CWD resolution can never diverge).
PIPELINE_DIR = REPO_ROOT / "pipeline"

#: The D-10 tee directory name under the XDG state root.
TEE_DIR_NAME = "logs"

#: One file per launch: ``{prefix}{timestamp}_{rootname}{suffix}``.
TEE_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
TEE_FILENAME_FORMAT = "sweep_{ts}_{rootname}.log"

#: The kill path's poll-with-short-grace budget (seconds) before the
#: SIGKILL escalation, and the poll cadence inside it.
DEFAULT_KILL_GRACE_SECONDS = 2.0
KILL_POLL_INTERVAL_SECONDS = 0.05

#: The exit-triple outcome vocabulary (the download_queue cancel
#: outcomes).
OUTCOME_SIGNALLED = "signalled"
OUTCOME_ALREADY_DEAD = "already_dead"
OUTCOME_DETACHED = "detached"
OUTCOME_NOOP = "noop"

#: The launcher's extension of run_config's machine problem vocabulary:
#: the official-keys diagnostic surfaced as a problem tuple (the
#: fail-closed reference blocks the gate instead of comparing against
#: silently-empty sets — T-11-02-02).
PROBLEM_OFFICIAL_KEYS = "official_keys"

#: The GateRefusal stages (in refusal order: problems, then phrase).
REFUSAL_STAGE_PROBLEMS = "problems"
REFUSAL_STAGE_PHRASE = "phrase"


# =====================================================================
# Frozen outcome dataclasses (DATA, never screen copy)
# =====================================================================


@dataclass(frozen=True)
class LiveSweep:
    """One registered live sweep — the registry's bookkeeping meta.

    Attributes:
        root: the RESOLVED output root (the registry key).
        tee_path: the tee log path under ``state_dir()/logs`` (D-10).
        started_at: the launch moment as a local ISO-8601 string.
        argv: the launch argv, verbatim (a tuple of str).
    """

    root: str
    tee_path: str
    started_at: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class LaunchOutcome:
    """One spawn attempt's outcome — success or the refused-spawn
    diagnostic, never an exception to the caller.

    Attributes:
        spawned: True iff the child was handed to the spawner.
        root: the RESOLVED output root (the registry key on success).
        tee_path: the tee log path on success; None when nothing
            launched.
        error: the OSError diagnostic when the spawn was refused;
            None on success.
    """

    spawned: bool
    root: str
    tee_path: str | None
    error: str | None


@dataclass(frozen=True)
class EnvPreflight:
    """The D-08 env preflight verdict — the frozen phase-8 face
    composed, never re-judged.

    Attributes:
        can_launch: False when any CRITICAL kernel failed (the launch
            pipeline refuses; the screen shows the env-block modal).
        reasons: the failing CRITICAL kernels' detail lines, verbatim
            from ``env_gate.gate_verdict`` (rendered as-is, never
            translated).
        failed_kernels: the CRITICAL kernel names with ``ok=False``,
            in input (main() kernel) order — the same names env_gate
            classifies.
    """

    can_launch: bool
    reasons: tuple[str, ...]
    failed_kernels: tuple[str, ...]


@dataclass(frozen=True)
class GateSummary:
    """The confirm-gate's machine summary — every number recomputed
    FRESH by ``gate_confirm_data``, never read from screen state
    (T-11-03-02).

    Attributes:
        models: distinct model identities in the fresh preview's
            cells.
        tasks: distinct tasks in the cells.
        seeds: distinct seeds in the cells.
        cells: total enumerated cells.
        output_root: the spec's output root, verbatim.
        is_e2x: the fresh ``is_full_e2x`` verdict.
        expected_phrase: the phrase the E2' gate demands.
    """

    models: int
    tasks: int
    seeds: int
    cells: int
    output_root: str
    is_e2x: bool
    expected_phrase: str


@dataclass(frozen=True)
class GateRefusal:
    """A refused launch — the gate's answer BEFORE any spawn (the
    spawner is never called for a refused launch; the tier-1 suite
    proves it by call counts).

    Attributes:
        stage: ``"problems"`` (preview problems or the official-keys
            diagnostic) / ``"phrase"`` (an E2' spec whose typed phrase
            does not exactly match).
        problems: the machine problem tuples for a ``problems`` stage
            (empty otherwise).
        expected: the expected phrase for a ``phrase`` stage (None
            otherwise).
    """

    stage: str
    problems: tuple[tuple[str, object], ...] = ()
    expected: str | None = None


# =====================================================================
# The phase-10 subprocess seams (copied verbatim from download_queue)
# =====================================================================


def _default_spawner(argv, **kwargs):
    """The real Popen seam (the injectable default).

    The service itself passes the fixed kwargs on every call
    (``start_new_session=True``, the pinned ``cwd``, the exact ``env``,
    ``stdout``/``stderr`` merged into the tee file), so the default is
    a pure forward to ``subprocess.Popen``.

    Args:
        argv (list): the LIST argv (never a shell string).
        **kwargs: ``env``/``start_new_session``/``cwd``/``stdout``/
            ``stderr``.

    Returns:
        subprocess.Popen: the owned process handle.
    """
    return subprocess.Popen(argv, **kwargs)


def _signal_group(proc, sig):
    """Signal one owned process's WHOLE group (the phase-10 discipline,
    Pitfall 1). Absorbs the already-dead races — the reap/poll loop
    owns the outcome, never the signal call."""
    try:
        os.killpg(os.getpgid(proc.pid), sig)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _now_iso(moment):
    """One datetime as a local ISO-8601 string (the download_queue
    ``_now_iso`` idiom)."""
    return moment.astimezone().isoformat(timespec="seconds")


def _run_config_service(run_config_service):
    """Resolve the run_config seam: the injected double, or the REAL
    module (tests inject doubles conforming to the consumed function
    seam; the real verdict logic is 11-02's tested code)."""
    if run_config_service is None:
        return run_config
    return run_config_service


# =====================================================================
# The env preflight (D-08 — the frozen phase-8 face, zero edits)
# =====================================================================


def env_preflight(kernels=None):
    """The D-08 env preflight: compose the FROZEN phase-8 face verbatim.

    ``quick_check.run_quick_check(kernels)`` -> ``env_gate.gate_verdict``
    — neither is modified or re-judged here; this function owns only
    the derived kernel-name list. The kernel list is injectable so CI
    runs fakes; the real GPU-touching kernels execute only on the GB10
    host. A ``can_launch`` False answer is the screen's env-block modal
    and the launch pipeline's refusal (T-11-03-03: a doomed sweep
    never spawns).

    Args:
        kernels: an injectable kernel sequence (None = the
            ``quick_check`` default subset).

    Returns:
        EnvPreflight: the composed verdict (reasons verbatim from
        ``gate_verdict`` — they render as-is).
    """
    results = quick_check.run_quick_check(kernels)
    verdict = env_gate.gate_verdict(results)
    failed_kernels = tuple(
        result.name for result in results
        if not result.ok and result.name in env_gate.CRITICAL
    )
    return EnvPreflight(
        can_launch=verdict.can_launch,
        reasons=verdict.reasons,
        failed_kernels=failed_kernels,
    )


# =====================================================================
# The confirm-gate summary (the FRESH recompute — T-11-03-02)
# =====================================================================


def gate_confirm_data(spec, run_config_service=None):
    """The confirm-gate's summary over a FRESH preview recompute.

    Calls ``run_config.preview`` + ``official_keys`` + ``is_full_e2x``
    NOW — never a cached screen value (the tier-1 suite proves the
    recompute with a counting spy). The modal renders this data; it can
    never substitute its own counts.

    Args:
        spec (run_config.RunSpec): the composed spec.
        run_config_service: an injectable seam double; None uses the
            REAL run_config module.

    Returns:
        GateSummary: the fresh counts + verdict + expected phrase.
    """
    rc = _run_config_service(run_config_service)
    preview_result = rc.preview(spec)
    official = rc.official_keys()
    return GateSummary(
        models=preview_result.models_count,
        tasks=preview_result.tasks_count,
        seeds=preview_result.seeds_count,
        cells=preview_result.cells_count,
        output_root=spec.output_root,
        is_e2x=rc.is_full_e2x(spec, official),
        expected_phrase=rc.expected_phrase(spec.output_root),
    )


# =====================================================================
# The launcher service (the registry owner)
# =====================================================================


class SweepLauncher:
    """The launch lifecycle owner: spawn-with-tee, the live-sweep
    registry, and the kill/detach exit triple (D-06).

    The registry is a service-instance dict keyed by the RESOLVED
    output root (the claimed-entry bookkeeping shape): ``root ->
    {"handle": Popen, "meta": LiveSweep, "tee": file}``. Keeping the
    tee file reference in the entry pins the parent-side descriptor
    open for the child's lifetime — the launcher never pumps or closes
    it early (the monitor tails the file by path; the OS reaps the
    child's inherited descriptor when the child exits).

    Args:
        spawner: the injectable Popen seam (tests record kwargs; the
            default is the verbatim ``_default_spawner`` forward).
        kill_grace: seconds to poll after SIGTERM before the SIGKILL
            escalation (injectable so tests never wait the default).
        kill_interval: the poll cadence inside the grace window.
    """

    def __init__(self, spawner=None,
                 kill_grace=DEFAULT_KILL_GRACE_SECONDS,
                 kill_interval=KILL_POLL_INTERVAL_SECONDS):
        self._spawner = _default_spawner if spawner is None else spawner
        self._kill_grace = kill_grace
        self._kill_interval = kill_interval
        self._live: dict[str, dict] = {}

    # ===== The spawn core (D-06/D-10) =====

    def _spawn(self, argv, output_root, spawner=None, clock=None):
        """Spawn one sweep argv through the injectable seam with the
        full D-06 discipline and the D-10 tee.

        Never raises: a refused spawn (OSError from the seam) returns
        the failed outcome with the diagnostic and unlinks the empty
        tee file — nothing launched leaves no log. On success the
        registry claims the resolved root.

        Args:
            argv: the launch argv (LIST-shaped; threaded verbatim —
                composition is run_config's, never re-derived here).
            output_root: the sweep output root (resolved to the
                registry key and the tee ``{rootname}``).
            spawner: a per-call seam override; None uses the
                instance seam.
            clock: an injectable ``datetime.now``-shaped callable
                (tests pin deterministic tee filenames).

        Returns:
            LaunchOutcome: the spawn outcome.
        """
        root = str(Path(output_root).resolve())
        logs_dir = settings.state_dir() / TEE_DIR_NAME
        logs_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now if clock is None else clock
        timestamp = now().strftime(TEE_TIMESTAMP_FORMAT)
        tee_path = logs_dir / TEE_FILENAME_FORMAT.format(
            ts=timestamp, rootname=Path(root).name)
        # Deliberately NOT a context manager (SIM115): the tee handle
        # stays open for the child's lifetime — closing it here would
        # detach the log's owner before the child ever writes (the
        # registry entry holds the reference; _drop_entry closes it).
        tee_handle = open(  # noqa: SIM115
            tee_path, "w", encoding="utf-8")
        seam = self._spawner if spawner is None else spawner
        try:
            proc = seam(
                list(argv),
                start_new_session=True,
                cwd=str(PIPELINE_DIR),
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
                stdout=tee_handle,
                stderr=subprocess.STDOUT,
            )
        except OSError as exc:
            tee_handle.close()
            tee_path.unlink(missing_ok=True)
            return LaunchOutcome(
                spawned=False, root=root, tee_path=None, error=str(exc))
        meta = LiveSweep(
            root=root,
            tee_path=str(tee_path),
            started_at=_now_iso(now()),
            argv=tuple(str(element) for element in argv),
        )
        self._live[root] = {"handle": proc, "meta": meta, "tee": tee_handle}
        return LaunchOutcome(
            spawned=True, root=root, tee_path=str(tee_path), error=None)

    # ===== The gated launch paths (D-07 / D-11) =====

    def launch_spec(self, spec, phrase=None, run_config_service=None,
                    spawner=None, clock=None):
        """Launch one composed spec through the STRUCTURAL gate (D-07 /
        LNC-03).

        Refusal order — each refusal returns BEFORE the spawner is ever
        consulted (proven by call counts in the tier-1 suite):

        1. a FRESH preview recompute (never the screen's cached value —
           T-11-03-02); any problem refuses at stage ``"problems"``;
        2. the official-keys reference; a diagnostic (fail-closed)
           refuses at stage ``"problems"`` as an ``official_keys``
           problem tuple — empty sets must not satisfy the E2'
           predicate by vacuity;
        3. an E2' verdict (recomputed FRESH via
           ``is_full_e2x(spec, official_keys())``) whose typed phrase
           does not EXACTLY match ``run_config.expected_phrase``
           refuses at stage ``"phrase"`` — no widget path can reach
           ``_spawn`` for a full-matrix spec without this check
           passing (T-11-03-01).

        A non-E2' spec ignores the phrase argument entirely.

        Args:
            spec (run_config.RunSpec): the composed spec.
            phrase: the operator-typed E2' phrase (None/"" refuse an
                E2' spec; ignored otherwise).
            run_config_service: an injectable seam double; None uses
                the REAL run_config module.
            spawner: a per-call seam override; None uses the
                instance seam.
            clock: an injectable ``datetime.now``-shaped callable.

        Returns:
            LaunchOutcome | GateRefusal: the spawn outcome, or the
            refusal (the spawner provably never called).
        """
        rc = _run_config_service(run_config_service)
        preview_result = rc.preview(spec)
        if preview_result.problems:
            return GateRefusal(
                stage=REFUSAL_STAGE_PROBLEMS,
                problems=preview_result.problems)
        official = rc.official_keys()
        if official.diagnostic is not None:
            return GateRefusal(
                stage=REFUSAL_STAGE_PROBLEMS,
                problems=((PROBLEM_OFFICIAL_KEYS, official.diagnostic),))
        if (rc.is_full_e2x(spec, official)
                and not rc.phrase_matches(phrase, spec.output_root)):
            return GateRefusal(
                stage=REFUSAL_STAGE_PHRASE,
                expected=rc.expected_phrase(spec.output_root))
        return self._spawn(
            rc.compose_argv(spec), spec.output_root,
            spawner=spawner, clock=clock)

    def launch_argv(self, argv, output_root, spawner=None, clock=None):
        """Launch a PRE-COMPOSED argv through the shared spawn seam.

        WARNING — from-failures-only BY CONSTRUCTION (D-11): callers
        pass argv composed by
        ``run_config.compose_from_failures_argv``, whose enumeration is
        EXACTLY the failed (model, task) pairs of a prior sweep — it
        can never be the full matrix, so the E2' typed gate does not
        apply here and is NEVER consulted. This seam takes no spec, so
        no widget path can route a full-matrix spec through it
        unnoticed — full-matrix launches MUST go through
        ``launch_spec``, which re-proves the gate.

        Args:
            argv: the pre-composed launch argv (threaded verbatim).
            output_root: the sweep output root.
            spawner: a per-call seam override; None uses the
                instance seam.
            clock: an injectable ``datetime.now``-shaped callable.

        Returns:
            LaunchOutcome: the spawn outcome.
        """
        return self._spawn(argv, output_root, spawner=spawner, clock=clock)

    def launch_from_failures(self, failures_path, seeds, output_root,
                             peft="none", config_variant="none",
                             spawner=None, clock=None):
        """The [r] failure re-run launch (D-11).

        Composes via ``run_config.compose_from_failures_argv`` and
        routes through ``launch_argv`` — the SAME launch pipeline every
        launch source shares. D-11's design, recorded: the re-run
        re-enters the pipeline the screen gates (the env preflight is
        the screen's PRECEDING step — the operator confirms the re-run
        independently), and a from-failures enumeration is
        failure-pairs-only, so the E2' typed gate cannot apply by
        construction. The child re-validates the failures manifest
        itself (``run_sweep.load_failure_pairs`` fail-fast).

        Args:
            failures_path: the prior sweep's
                ``sweep_failures.json`` path.
            seeds: the re-run seed fan-out.
            output_root: the re-run output root.
            peft: adapter mode (none = absent from argv).
            config_variant: variant lane (none = absent).
            spawner: a per-call seam override; None uses the
                instance seam.
            clock: an injectable ``datetime.now``-shaped callable.

        Returns:
            LaunchOutcome: the spawn outcome.
        """
        argv = run_config.compose_from_failures_argv(
            failures_path, seeds, output_root,
            peft=peft, config_variant=config_variant)
        return self.launch_argv(
            argv, output_root, spawner=spawner, clock=clock)

    # ===== The exit triple (D-06) =====

    @staticmethod
    def _drop_entry(entry):
        """Release one dropped registry entry's parent-side tee handle
        (the child keeps its own inherited descriptor — closing the
        parent copy neither kills nor truncates anything)."""
        tee = entry.get("tee")
        if tee is None:
            return
        try:
            tee.close()
        except OSError:
            pass

    def kill_sweep(self, root):
        """Kill one live sweep's WHOLE process group (D-06).

        SIGTERM via ``os.killpg`` (absorbing already-dead races), then
        a poll-with-short-grace; a process still alive past the grace
        gets the SIGKILL escalation. The registry entry drops after
        the kill — a killed root is never listed live again.

        Args:
            root: the output root as registered (resolved here).

        Returns:
            str: ``signalled`` (the group was signalled — SIGTERM
            alone or with the SIGKILL escalation) / ``already_dead``
            (poll reaped it before any signal) / ``noop`` (unknown
            root).
        """
        entry = self._live.pop(str(Path(root).resolve()), None)
        if entry is None:
            return OUTCOME_NOOP
        proc = entry["handle"]
        if proc.poll() is not None:
            self._drop_entry(entry)
            return OUTCOME_ALREADY_DEAD
        _signal_group(proc, signal.SIGTERM)
        deadline = time.monotonic() + self._kill_grace
        while proc.poll() is None and time.monotonic() < deadline:
            time.sleep(self._kill_interval)
        if proc.poll() is None:
            _signal_group(proc, signal.SIGKILL)
        self._drop_entry(entry)
        return OUTCOME_SIGNALLED

    def detach(self, root):
        """Detach one live sweep: drop the handle, NO wait, NO kill
        (D-06).

        The sweep keeps running as an orphaned session leader;
        resume-safe by the trainer_state marker contract — the monitor
        re-discovers it via D-03 scanning and the manifest at end.

        Args:
            root: the output root as registered (resolved here).

        Returns:
            str: ``detached`` / ``noop`` (unknown root).
        """
        entry = self._live.pop(str(Path(root).resolve()), None)
        if entry is None:
            return OUTCOME_NOOP
        self._drop_entry(entry)
        return OUTCOME_DETACHED

    # ===== The live registry reads (ExitModal + monitor seams) =====

    def live_sweeps(self):
        """The live roots, sorted (the ExitModal predicate and the
        monitor's Popen-alive injection source).

        Returns:
            tuple[str, ...]: the RESOLVED output roots currently
            registered.
        """
        return tuple(sorted(self._live))

    def tee_path_for(self, root):
        """One live root's tee log path (the [t] modal's source).

        Args:
            root: the output root as registered (resolved here).

        Returns:
            str | None: the tee path, or None for an unregistered root
            (the CLI-launched unavailable state).
        """
        entry = self._live.get(str(Path(root).resolve()))
        if entry is None:
            return None
        return entry["meta"].tee_path
