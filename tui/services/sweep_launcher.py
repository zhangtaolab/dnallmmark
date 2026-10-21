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
  empty tee file — nothing launched leaves no log. WR-04 (stale-
  refresh review): the tee opens with mode ``"x"`` (O_EXCL) with a
  numeric-suffix fallback (``_1``..``_99``) — two same-basename output
  roots spawned within the same second never share, truncate, or
  interleave a tee file (a pid suffix would not disambiguate two
  spawns from THIS process); an exhausted suffix cap refuses like
  OSError.
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
  SAME launch seam. The re-run's effective matrix is RECOMPUTED here
  (CR-01, phase-11 review): ``run_sweep.load_failure_pairs`` × the
  requested seeds is NOT "never the full matrix by construction" — a
  genuine complete failures manifest (a full sweep that failed every
  cell) re-run over the sweep's 3 seeds IS the full 8850-cell matrix,
  so the SAME ``is_full_e2x``-class predicate + typed-phrase gate apply
  (``launch_spec``'s refusal order: official-keys diagnostic, then the
  phrase). An unevaluatable manifest (unreadable/invalid — the child's
  own ``load_failure_pairs`` fail-fast) refuses at the problems stage.
  The raw ``launch_argv`` seam itself stays ungated by design (pinned
  by the tier-1 suite); the gate is the composed path's, never the
  seam's.

ZERO textual imports (the services-tier invariant declared in
``tui/services/__init__.py``; locked by ``tests/tui/test_import_lock.py``
— the glob extends over this module automatically). ZERO Chinese
literals (the WR-05 services i18n lock). Dependencies: stdlib + the
sibling ``settings`` (state root) / ``quick_check`` + ``env_gate`` (the
frozen phase-8 face) / ``run_config`` (the 11-02 verdict + argv
composition) services.
"""

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import run_sweep  # top-level module (pipeline/ sys.path root, D-05 same-source)

from tui.services import env_gate, quick_check, run_config, settings

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The sweep driver's working directory (D-06: pinned so the
#: subprocess's own CWD resolution can never diverge).
PIPELINE_DIR = REPO_ROOT / "pipeline"

#: The D-10 tee directory name under the XDG state root.
TEE_DIR_NAME = "logs"

#: 261018-toe (slot-5 [e]): the directory under the XDG state root where
#: ``launch_from_pairs`` materializes its failures-shaped pairs files
#: (``resume_pairs_{rootname}.json``) — the monitor_roots/tee precedent:
#: state-machine files live under the STATE root, NEVER inside a sweep
#: output root (``sweep_failures.json`` is the driver's own end-of-sweep
#: artifact; writing there would corrupt rerun_lane and WR-06
#: stale-manifest semantics).
RESUME_PAIRS_DIR_NAME = "resume"

#: One file per launch: ``{prefix}{timestamp}_{rootname}{suffix}``.
#: WR-04 (phase-11 stale-refresh review): the tee opens with mode
#: ``"x"`` (O_EXCL) — unique per spawn AT THE FILESYSTEM level; a
#: same-second same-basename collision retries with a numeric suffix
#: (``_1``, ``_2``, ... capped at ``_99`` via TEE_COLLISION_SUFFIX_CAP).
#: Non-colliding names keep today's exact shape.
TEE_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
TEE_FILENAME_FORMAT = "sweep_{ts}_{rootname}.log"

#: The numeric-suffix retry cap for a colliding tee filename (WR-04):
#: attempts ``_1``..``_99``; an exhausted cap rides the OSError refusal
#: branch (nothing launched leaves no log).
TEE_COLLISION_SUFFIX_CAP = 99

#: 2026-10-19 restart-reattach: a tee file discovered on disk counts as
#: the LIVE run's own log only while its mtime sits inside this grace
#: (the surviving child keeps appending its inherited descriptor; a
#: quiet model-load phase can stall writes for minutes). The
#: sweep_monitor.STALE_GRACE_SECONDS (600s) quiet-phase precedent, kept
#: as a local twin to avoid a services cross-import.
TEE_FRESH_GRACE_SECONDS = 600.0

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

#: CR-01 (phase-11 review): a from-failures manifest the gate cannot
#: evaluate (unreadable/not-JSON/invalid entries — the driver's own
#: ``load_failure_pairs`` fail-fast) surfaced as a problem tuple. An
#: unevaluatable matrix is never launched ungated.
PROBLEM_FAILURES_MANIFEST = "failures_manifest"

#: EHC-3 (261015-ehc ruling 3): a single-GPU machine with a live sweep
#: registered refuses further gated launches — surfaced as a problem
#: tuple whose detail is the running root(s) joined.
PROBLEM_SINGLE_GPU = "single_gpu_busy"

#: The GateRefusal stages (in refusal order: the single-GPU
#: serialization guard first, then problems, then phrase).
REFUSAL_STAGE_PROBLEMS = "problems"
REFUSAL_STAGE_PHRASE = "phrase"
REFUSAL_STAGE_SINGLE_GPU = "single_gpu"


def effective_gpu_count() -> int:
    """The machine's EFFECTIVE GPU count (EHC-3, 261015-ehc ruling 3).

    Resolution order:

    1. ``WORLD_SIZE`` parsed as an int — a value >= 1 wins outright
       (never imports torch: the multi-worker launcher sets it, and a
       torch-free CI lane stays torch-free).
    2. Otherwise a LAZY ``import torch`` inside a try/except (ImportError
       and EVERY exception -> 0, T-ehc-04 — never raises): guarded by
       ``torch.cuda.is_available()`` then ``torch.cuda.device_count()``
       — which honors ``CUDA_VISIBLE_DEVICES`` (a masked 4-GPU box
       reading 1 is correctly serialized). The lazy-import seam is the
       ``pipeline/flops_counter.py`` precedent — NO torch import at
       module top (CI lanes stay torch-free).

    Returns:
        int: the effective GPU count (0 when torch/CUDA is unavailable —
        count-0 machines are unrestricted per the ruling's letter).
    """
    world_size = os.environ.get("WORLD_SIZE", "")
    try:
        parsed = int(world_size)
    except ValueError:
        parsed = 0
    if parsed >= 1:
        return parsed
    try:
        # lazy seam (the flops_counter precedent — CI stays torch-free)
        import torch

        if not torch.cuda.is_available():
            return 0
        return int(torch.cuda.device_count())
    except Exception:  # noqa: BLE001 — never raises (T-ehc-04)
        return 0


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
class GpuCapacityBlock:
    """The multi-GPU capacity refusal's structured detail (16-03,
    D16-10 — resolves Pitfall 2's open question: the NUMBERS travel
    service-side and the screens only format).

    Returned by ``single_gpu_launch_blocked`` exactly when the launch
    must refuse; truthy by construction (the predicate returns None
    when it admits). Renders through the amended
    ``LNC_SINGLE_GPU_BLOCKED`` copy — the screens read these fields,
    never compute.

    Attributes:
        roots: the live registry roots in registry order (sorted).
        requested_workers: the launch's requested worker count.
        gpu_count: the machine's effective GPU count the arithmetic
            refused against.
    """

    roots: tuple[str, ...]
    requested_workers: int
    gpu_count: int


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
        pairs: the planned (model, task) pairs behind the counts
            formula — the confirm modal's task list (UX-5, 261016-poa).
            Derived SERVICE-SIDE from the fresh preview cells as an
            ordered first-occurrence dedupe (seeds stay collapsed in
            the counts formula, never per-row); defaulted so pre-UX-5
            fakes construct unchanged. The UI renders, never computes.
    """

    models: int
    tasks: int
    seeds: int
    cells: int
    output_root: str
    is_e2x: bool
    expected_phrase: str
    pairs: tuple[tuple[str, str], ...] = ()


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


def _iso_to_epoch(value):
    """One registry ``started_at`` ISO stamp as an epoch float
    (261020-9vh). The registry stamps TZ-AWARE local ISO
    (``_now_iso``), so ``fromisoformat`` round-trips it exactly — a
    naive parse here would mis-place the start by the local offset and
    fabricate staleness. Unparseable/non-string -> None (an honest no
    start, never a raise)."""
    try:
        return datetime.fromisoformat(value).timestamp()
    except (ValueError, TypeError, AttributeError):
        return None


def _exit_message(exc):
    """One caught exception's human-readable message — a ``SystemExit``
    carries its message in ``code`` (``str(SystemExit("m"))`` would
    render repr-quoted), everything else renders via ``str()``."""
    code = getattr(exc, "code", None)
    if isinstance(code, str):
        return code
    return str(exc)


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
        GateSummary: the fresh counts + verdict + expected phrase + the
        planned (model, task) pairs (the confirm modal's task list).
    """
    rc = _run_config_service(run_config_service)
    preview_result = rc.preview(spec)
    official = rc.official_keys()
    # UX-5 (261016-poa): the planned (model, task) pairs, service-side
    # — an ordered first-occurrence dedupe over the FRESH preview cells
    # ((model, task) = cell[0], cell[1]; both the 3-tuple and the
    # curve-fraction 4-tuple shapes project identically). Seeds stay in
    # the counts formula, never per-row; the modal renders this, it
    # never computes its own list.
    pairs: list[tuple[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for cell in preview_result.cells:
        pair = (str(cell[0]), str(cell[1]))
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            pairs.append(pair)
    return GateSummary(
        models=preview_result.models_count,
        tasks=preview_result.tasks_count,
        seeds=preview_result.seeds_count,
        cells=preview_result.cells_count,
        output_root=spec.output_root,
        is_e2x=rc.is_full_e2x(spec, official),
        expected_phrase=rc.expected_phrase(spec.output_root),
        pairs=tuple(pairs),
    )


# =====================================================================
# The launcher service (the registry owner)
# =====================================================================

#: The sweep driver's script name as it appears in a live process's
#: argv (the probe's membership test — a Path-name comparison, never a
#: substring, so ``not_run_sweep.py`` never matches).
_RUN_SWEEP_SCRIPT_NAME = "run_sweep.py"

#: The shard orchestrator's script name (16-03, D16-10): the capacity
#: predicate's demand parse keys on it — a live argv running
#: run_sweep_shard.py (either mode) demands its parsed --workers
#: integer; the same Path-name comparison discipline as above.
_RUN_SWEEP_SHARD_SCRIPT_NAME = "run_sweep_shard.py"


def _iter_cli_sweeps(proc_root="/proc"):
    """The shared /proc walk behind both CLI probes (261020-9vh — the
    ``probe_cli_sweeps`` body, extracted byte-identically): iterate the
    NUMERIC entries of ``proc_root`` (sorted; non-numeric skipped);
    read each ``<pid>/cmdline`` as NUL-separated bytes, decode
    utf-8/replace; a process whose argv holds an element whose Path
    NAME is exactly ``run_sweep.py`` yields ``(resolved --output-root,
    argv, pid_dir)``. Any OSError/ValueError skips the pid (a dying
    process's cmdline vanishes mid-read — the probe never crashes a
    cadence). A RELATIVE ``--output-root`` resolves against
    ``os.readlink(<pid>/cwd)`` best-effort (the CLI hand-run edge;
    compose_argv threads absolute roots by contract), falling back to a
    plain resolve. An absent/unlistable ``proc_root`` yields NOTHING
    (non-Linux degrades to NO CLI evidence — honest), and filesystem
    reads are ALL this generator ever does: no subprocess, no signal,
    EVER (a live sweep may be running on this box — the probes read
    its cmdline/stat and nothing else).
    """
    try:
        entries = sorted(Path(proc_root).iterdir())
    except OSError:
        return
    for pid_dir in entries:
        if not pid_dir.name.isdigit():
            continue
        try:
            raw = (pid_dir / "cmdline").read_bytes()
        except OSError:
            continue
        argv = tuple(
            part.decode("utf-8", "replace")
            for part in raw.split(b"\0") if part)
        if not any(Path(element).name == _RUN_SWEEP_SCRIPT_NAME
                   for element in argv):
            continue
        output_root = run_config._argv_flag_values(argv).get("--output-root")
        if not output_root:
            continue
        yield str(_resolve_probe_root(output_root, pid_dir)), argv, pid_dir


def probe_cli_sweeps(proc_root="/proc") -> dict:
    """Discover CLI-launched run_sweep processes by probing ``/proc``
    (261017-uwr, UWR-2 — the attached/discovered CLI evidence source).

    Bounded, read-only, total over the shared ``_iter_cli_sweeps``
    walk (261020-9vh — behavior byte-identical to the pre-extraction
    body): ``{resolved --output-root: argv}`` per matching process.

    DISPLAY-ONLY evidence (T-uwr-01): the output feeds glyph/header
    rendering through ``live_sweep_matrices``; it never gates a launch,
    a kill, or an exit, and raw argv is never rendered.

    Args:
        proc_root: the proc filesystem root (tests inject a fake tree).

    Returns:
        dict[str, tuple[str, ...]]: resolved output root -> the live
        process's argv (verbatim, never rendered).
    """
    return {root: argv for root, argv, _pid_dir in _iter_cli_sweeps(proc_root)}


def _boot_time(proc_root):
    """The kernel boot epoch from ``<proc_root>/stat``'s ``btime `` line
    (261020-9vh — /proc's own clock basis; the man page's field 1 basis
    for field-22 starttime ticks). Absent/unreadable/garbage -> None —
    no start evidence, never a crash (the argv probe's non-Linux
    degradation vocabulary)."""
    try:
        raw = (Path(proc_root) / "stat").read_text(
            encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in raw.splitlines():
        if line.startswith("btime "):
            try:
                return float(line[len("btime "):])
            except ValueError:
                return None
    return None


def _clock_ticks():
    """The kernel's clock-tick rate (``SC_CLK_TCK`` — the divisor that
    turns field-22 ticks into seconds); a ValueError (name unknown on
    this platform) -> None — no start evidence."""
    try:
        return float(os.sysconf("SC_CLK_TCK"))
    except ValueError:
        return None


def _proc_start_epoch(pid_dir, btime, ticks):
    """One pid's process-start epoch: ``<pid>/stat`` field 22
    (starttime ticks since boot) over the post-paren field split —
    ``raw.rpartition(")")`` drops the parenthesized comm (it may
    contain spaces), so index 19 IS field 22 against the /proc man
    page's 1-based numbering — then ``btime + ticks / SC_CLK_TCK``.
    Every OSError/ValueError/IndexError (a dying process's vanished
    stat, a truncated/garbage line) -> None."""
    try:
        raw = (Path(pid_dir) / "stat").read_bytes().decode(
            "utf-8", "replace")
        fields = raw.rpartition(")")[2].split()
        return btime + int(fields[19]) / ticks
    except (OSError, ValueError, IndexError):
        return None


def probe_cli_sweep_starts(proc_root="/proc") -> dict:
    """The CLI-launched run_sweep processes' START epochs by probing
    ``/proc`` (261020-9vh — the stale-progress guard's evidence leg
    over the SAME ``_iter_cli_sweeps`` walk ``probe_cli_sweeps`` uses).

    Per matching pid: ``<pid>/stat`` field 22 (starttime ticks) over
    the kernel's ``btime`` and ``SC_CLK_TCK`` -> the process-start
    epoch. A pid whose stat cannot be read/parsed contributes nothing
    (tolerant); a ``proc_root`` without a readable ``btime`` line, or a
    platform without ``SC_CLK_TCK``, reads ``{}`` — NO start evidence
    (the honest degradation, never a guessed start and never a raise).

    DISPLAY-ONLY like the argv probe (T-uwr-01 / T-9vh-03): reads
    cmdline/stat and NOTHING else — a live sweep may be running on
    this box (it is); the probe never signals it, and the output never
    gates a launch, a kill, or an exit.

    Args:
        proc_root: the proc filesystem root (tests inject a fake tree).

    Returns:
        dict[str, float]: resolved output root -> the live process's
        start epoch (seconds).
    """
    btime = _boot_time(proc_root)
    ticks = _clock_ticks()
    if btime is None or ticks is None:
        return {}
    starts: dict[str, float] = {}
    for root, _argv, pid_dir in _iter_cli_sweeps(proc_root):
        start = _proc_start_epoch(pid_dir, btime, ticks)
        if start is not None:
            starts[root] = start
    return starts


def _resolve_probe_root(value: str, pid_dir: Path) -> Path:
    """Resolve one probed ``--output-root`` value absolute: a relative
    value joins the process's OWN cwd (``os.readlink(<pid>/cwd)``,
    best-effort — the readlink of a dying/sandboxed process may fail,
    and the fallback is a plain resolve); an absolute value resolves
    straight through (symlinks normalized, the registry-key basis)."""
    candidate = Path(value)
    try:
        if not candidate.is_absolute():
            try:
                cwd = os.readlink(pid_dir / "cwd")
                return (Path(cwd) / candidate).resolve()
            except (OSError, ValueError):
                pass
        return candidate.resolve()
    except OSError:
        return candidate


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
        gpu_count: an injectable EFFECTIVE GPU count pin (EHC-3 —
            None probes live via ``effective_gpu_count()`` at each
            guarded call; an int pins it for tests).
    """

    def __init__(self, spawner=None,
                 kill_grace=DEFAULT_KILL_GRACE_SECONDS,
                 kill_interval=KILL_POLL_INTERVAL_SECONDS,
                 gpu_count=None):
        self._spawner = _default_spawner if spawner is None else spawner
        self._kill_grace = kill_grace
        self._kill_interval = kill_interval
        self._gpu_count = gpu_count
        self._live: dict[str, dict] = {}
        # IN-05 (phase-11 review): the last tee path spawned per root —
        # the [t] fallback after detach/kill drops the live entry (the
        # tee FILE still stands under state/logs; the child owns its
        # own descriptor).
        self._tee_history: dict[str, str] = {}
        # 261017-uwr (UWR-2) + 261020-blt: the per-argv planned-cells
        # cache behind live_sweep_plans (the pairs projection
        # live_sweep_matrices reads) — keyed by the argv tuple (see
        # _plan_for); dead entries' rows persist harmlessly.
        self._plan_cache: dict[tuple[str, ...], object] = {}
        # 16-03 (D16-10): the per-root GPU-demand cache behind the
        # capacity predicate (the _plan_cache per-argv precedent — a
        # live entry's argv is immutable, so one parse per root).
        self._demand_cache: dict[str, int] = {}

    # ===== The spawn core (D-06/D-10) =====

    def _spawn(self, argv, output_root, spawner=None, clock=None):
        """Spawn one sweep argv through the injectable seam with the
        full D-06 discipline and the D-10 tee.

        Never raises: a refused spawn (OSError from the seam) returns
        the failed outcome with the diagnostic and unlinks the empty
        tee file — nothing launched leaves no log. On success the
        registry claims the resolved root.

        CR-02 (phase-11 review): the spawn is REFUSED when the resolved
        root already holds a LIVE registry entry (``poll() is None``) —
        a second launch would silently overwrite the entry (orphaning
        the first Popen and leaking its tee fd) and leave two run_sweep
        processes racing the identical cell dirs into the identical
        output root: colliding checkpoints, double-written
        final_metrics/trainer_state/run_record, corrupted "completed"
        artifacts destined for the public leaderboard. A DEAD entry
        (poll() reaped) is pruned — handle dropped, tee closed — and
        the root stays claimable.

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
        prior = self._live.get(root)
        if prior is not None:
            if prior["handle"].poll() is None:
                return LaunchOutcome(
                    spawned=False, root=root, tee_path=None,
                    error=(
                        f"output root {root} already has a live sweep "
                        "registered — kill or detach it (the slot-5 exit "
                        "modal) or pick a different output root before "
                        "launching"))
            # the prior sweep exited without detach/kill: reclaim the
            # root (drop the dead entry + close its parent-side tee)
            self._live.pop(root, None)
            self._drop_entry(prior)
        logs_dir = settings.state_dir() / TEE_DIR_NAME
        logs_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now if clock is None else clock
        timestamp = now().strftime(TEE_TIMESTAMP_FORMAT)
        base_name = TEE_FILENAME_FORMAT.format(
            ts=timestamp, rootname=Path(root).name)
        # WR-04 (phase-11 stale-refresh review): the tee opens EXCLUSIVE
        # (mode "x" = O_EXCL) — unique per spawn AT THE FILESYSTEM
        # level, robust across processes, sessions, AND the
        # same-process race (a pid suffix would NOT disambiguate the
        # stated slot-4-confirm-races-monitor-[r] shape: both spawns
        # come from THIS TUI process). A collision retries the same
        # base name with a numeric suffix; a same-second RECLAIM at the
        # same root (kill then immediate relaunch) thereby APPENDS a
        # suffix instead of truncating the killed sweep's audit log —
        # strictly better. An exhausted cap refuses like OSError:
        # nothing launched leaves no log.
        stem, _dot, extension = base_name.rpartition(".")
        tee_handle = None
        tee_path = logs_dir / base_name
        for attempt in range(TEE_COLLISION_SUFFIX_CAP + 1):
            candidate = tee_path if attempt == 0 else logs_dir / (
                f"{stem}_{attempt}.{extension}")
            try:
                # Deliberately NOT a context manager (SIM115): the tee
                # handle stays open for the child's lifetime — closing
                # it here would detach the log's owner before the child
                # ever writes (the registry entry holds the reference;
                # _drop_entry closes it).
                tee_handle = open(  # noqa: SIM115
                    candidate, "x", encoding="utf-8")
                tee_path = candidate
                break
            except FileExistsError:
                continue
        if tee_handle is None:
            return LaunchOutcome(
                spawned=False, root=root, tee_path=None,
                error=(
                    f"tee log name collision exhausted ({base_name} "
                    f"through _{TEE_COLLISION_SUFFIX_CAP}) — refusing "
                    "to open a shared log for a second spawn"))
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
        self._tee_history[root] = str(tee_path)
        return LaunchOutcome(
            spawned=True, root=root, tee_path=str(tee_path), error=None)

    # ===== The gated launch paths (D-07 / D-11 / EHC-3 -> 16-03) =====

    def _entry_demand_for_argv(self, argv) -> int:
        """One argv's GPU DEMAND (16-03, D16-10 — registry-only
        arithmetic, Pitfall 4): an argv running run_sweep_shard.py
        (EITHER mode — static LPT workers and the dispatcher both pin
        one GPU per worker) demands the integer after ``--workers``
        (default 1 when the flag is absent — the CLI's own default;
        parse failures fail SAFE at demand 1, never a crash and never
        an over-admission through a fabricated count); every other
        argv (a plain run_sweep launch) demands 1.
        """
        elements = [str(element) for element in argv]
        if not any(Path(element).name == _RUN_SWEEP_SHARD_SCRIPT_NAME
                   for element in elements):
            return 1
        demand = 1
        for index in range(len(elements) - 1):
            if elements[index] == "--workers":
                try:
                    demand = int(elements[index + 1])
                except ValueError:
                    demand = 1
                break
        return max(demand, 1)

    def _entry_demand(self, root: str) -> int:
        """One LIVE registry entry's GPU demand — its verbatim
        ``LiveSweep.argv`` parsed through ``_entry_demand_for_argv``
        behind the per-root cache (argv is immutable per entry, the
        _plan_cache precedent). An unknown/dead root demands 1 (the
        fail-safe)."""
        entry = self._live.get(root)
        if entry is None:
            return 1
        cached = self._demand_cache.get(root)
        if cached is None:
            cached = self._entry_demand_for_argv(entry["meta"].argv)
            self._demand_cache[root] = cached
        return cached

    def single_gpu_launch_blocked(self, requested_workers: int = 1):
        """The multi-GPU capacity predicate (16-03, D16-10 — the EHC-3
        stage-0 semantics replaced in place; the NAME, the stage
        position, and the ZERO-ARG-CALLABLE signature are preserved,
        Pitfall 3).

        Registry-only arithmetic over the machine's EFFECTIVE GPU
        count (``self._gpu_count`` pin, else the UNCHANGED
        ``effective_gpu_count()`` — WORLD_SIZE > lazy torch > 0):

        - count == 0 (torch/CUDA unavailable) admits UNCONDITIONALLY
          — the EHC-3 letter carried over;
        - otherwise the launch refuses iff
          ``sum(per-entry demand) + requested_workers > count`` where
          a live entry's demand is its argv's parsed ``--workers``
          when it runs ``run_sweep_shard.py`` (either mode) else 1 —
          D16-10's sanctioned shape: N GPUs -> N concurrent cells. A
          live plain entry on a count-1 machine is SUBSUMED (1 + 1 >
          1) — the EHC-3 behavior preserved by the arithmetic; an idle
          registry admits whenever the request alone fits.

        BOUNDARY (Pitfall 4 / T-16-06): the predicate reads the
        launcher REGISTRY exclusively — ``live_sweeps()`` and the
        entries' stored argv. It NEVER reads /proc;
        ``probe_cli_sweeps`` stays pinned DISPLAY-ONLY (widening
        needs a maintainer ruling).

        Args:
            requested_workers: the launch's requested worker count
                (default 1 — the zero-arg tolerant-getattr pre-check
                sites read demand-only).

        Returns:
            GpuCapacityBlock | None: the structured refusal detail
            (roots, requested_workers, gpu_count) when the launch
            must refuse, else None.
        """
        count = (self._gpu_count if self._gpu_count is not None
                 else effective_gpu_count())
        if count == 0:
            return None
        live = self.live_sweeps()
        demand = sum(self._entry_demand(root) for root in live)
        if demand + requested_workers <= count:
            return None
        return GpuCapacityBlock(
            roots=live,
            requested_workers=requested_workers,
            gpu_count=count)

    def launch_spec(self, spec, phrase=None, run_config_service=None,
                    spawner=None, clock=None):
        """Launch one composed spec through the STRUCTURAL gate (D-07 /
        LNC-03; EHC-3 adds stage 0).

        Refusal order — each refusal returns BEFORE the spawner is ever
        consulted (proven by call counts in the tier-1 suite):

        0. the multi-GPU capacity guard (16-03, D16-10 — the EHC-3
           stage replaced in place; registry-only demand arithmetic
           over the spec's requested workers refuses FIRST — before
           the operator is asked for any preview or E2' phrase) at
           stage ``"single_gpu"``;
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

        WR-01 (phase-11 stale-refresh review) — the root-basis rule: the
        spawn is keyed on ``rc.resolve_dirs(spec).output_root_abs`` (the
        SAME REPO_ROOT basis ``compose_argv`` threads into
        ``--output-root``, D-14), never the raw ``spec.output_root`` —
        a TUI process running outside the repo with a relative root
        would otherwise register a phantom ``{cwd}``-rooted key while
        the sweep writes under ``{repo}`` (kill/detach/tee/auto-attach
        all keyed on a root that never exists).

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
        blocked = self.single_gpu_launch_blocked(
            requested_workers=getattr(spec, "workers", 1))
        if blocked is not None:
            return GateRefusal(
                stage=REFUSAL_STAGE_SINGLE_GPU,
                problems=((PROBLEM_SINGLE_GPU, blocked),))
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
        # 16-03 routing (UI-SPEC auto-default #9): every slot-4 launch
        # composes the frozen DISPATCH argv — run_sweep_shard.py
        # --mode dispatch --workers N; the spawn key still rides
        # rc.resolve_dirs(spec).output_root_abs (the WR-01 root-basis
        # rule, unchanged).
        return self._spawn(
            rc.compose_dispatch_argv(spec),
            rc.resolve_dirs(spec).output_root_abs,
            spawner=spawner, clock=clock)

    def launch_argv(self, argv, output_root, spawner=None, clock=None):
        """Launch a PRE-COMPOSED argv through the shared spawn seam.

        NOTE — the raw seam is intentionally UNGATED (pinned by the
        tier-1 suite): it takes no spec, so no predicate applies here.
        Its safety no longer rests on the retired "from-failures is
        never the full matrix" premise (CR-01, phase-11 review — a
        complete failures manifest IS a genuine full-matrix artifact):
        the COMPOSED UI path routes through ``launch_from_failures``,
        which recomputes the effective matrix and applies the same E2'
        predicate + typed-phrase gate as ``launch_spec``. Callers
        hand-composing a full-matrix argv around this seam bypass the
        gate by construction — that is the seam's contract, and the
        only production callers are gated composers.

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

    def _from_failures_refusal(self, rc, failures_path, seeds,
                               output_root, peft, config_variant,
                               phrase):
        """The CR-01 gate over one re-run's EFFECTIVE matrix.

        Recomputes what the child will enumerate — the failure pairs
        (``run_sweep.load_failure_pairs``, the driver's own parser)
        crossed with the requested seeds — and applies ``launch_spec``'s
        refusal order over it: the official-keys diagnostic (fail-closed)
        first, then the E2' predicate (pairs superset official AND >= 3
        seeds) demanding the exact typed phrase. The predicate itself is
        the REAL ``run_config.is_full_e2x`` over a synthetic RunSpec of
        the pair sets — zero copied matrix logic (D-05).

        Args:
            rc: the resolved run_config seam.
            failures_path: the prior sweep's ``sweep_failures.json``.
            seeds: the re-run seed fan-out.
            output_root: the re-run output root.
            peft: the re-run adapter mode (base-strip parity).
            config_variant: the re-run variant lane.
            phrase: the operator-typed phrase (None refuses an E2'-class
                re-run).

        Returns:
            GateRefusal | None: the refusal, or None when the re-run may
            spawn.
        """
        official = rc.official_keys()
        if official.diagnostic is not None:
            return GateRefusal(
                stage=REFUSAL_STAGE_PROBLEMS,
                problems=((PROBLEM_OFFICIAL_KEYS, official.diagnostic),))
        try:
            pairs = run_sweep.load_failure_pairs(
                str(Path(failures_path).resolve()),
                run_config.DEFAULT_REGISTRY_DIR)
        except (SystemExit, OSError, ValueError) as exc:
            # The child's own manifest validation would fail the same
            # way — refuse here, naming the file, never spawn ungated.
            return GateRefusal(
                stage=REFUSAL_STAGE_PROBLEMS,
                problems=((PROBLEM_FAILURES_MANIFEST, _exit_message(exc)),))
        effective = run_config.RunSpec(
            models=tuple(model for model, _task in pairs),
            tasks=tuple(task for _model, task in pairs),
            seeds=tuple(int(seed) for seed in seeds),
            peft=peft,
            config_variant=config_variant,
            output_root=str(output_root))
        if (rc.is_full_e2x(effective, official)
                and not rc.phrase_matches(phrase, output_root)):
            return GateRefusal(
                stage=REFUSAL_STAGE_PHRASE,
                expected=rc.expected_phrase(output_root))
        return None

    def launch_from_failures(self, failures_path, seeds, output_root,
                             peft="none", config_variant="none",
                             phrase=None, run_config_service=None,
                             spawner=None, clock=None):
        """The [r] failure re-run launch (D-11, CR-01-gated; EHC-3 adds
        the stage-0 guard).

        Composes via ``run_config.compose_from_failures_argv`` and
        routes through ``launch_argv`` — the SAME launch pipeline every
        launch source shares. CR-01 (phase-11 review) retired the
        "never the full matrix by construction" premise: the re-run's
        effective matrix (failure pairs × the requested seeds) is
        recomputed and gated BEFORE the composition — a complete
        failures manifest over the sweep's 3 seeds IS the full E2'
        matrix and demands the exact typed phrase (stage ``"phrase"``
        refusal, the ``launch_spec`` twin); an unevaluatable manifest or
        an official-keys diagnostic refuses at stage ``"problems"``.
        EHC-3 (261015-ehc): the single-GPU serialization guard runs
        FIRST — a busy single-GPU machine refuses before any
        manifest evaluation or phrase. The env preflight is the
        screen's PRECEDING step (the operator confirms the re-run
        independently); the child re-validates the failures manifest
        itself (``run_sweep.load_failure_pairs`` fail-fast).

        Args:
            failures_path: the prior sweep's
                ``sweep_failures.json`` path.
            seeds: the re-run seed fan-out.
            output_root: the re-run output root.
            peft: adapter mode (none = absent from argv).
            config_variant: variant lane (none = absent).
            phrase: the operator-typed E2' phrase; None/"" refuse an
                E2'-class re-run (ignored for an ordinary partial one).
            run_config_service: an injectable seam double; None uses
                the REAL run_config module.
            spawner: a per-call seam override; None uses the
                instance seam.
            clock: an injectable ``datetime.now``-shaped callable.

        Returns:
            LaunchOutcome | GateRefusal: the spawn outcome, or the
            refusal (the spawner provably never called).
        """
        blocked = self.single_gpu_launch_blocked()
        if blocked is not None:
            return GateRefusal(
                stage=REFUSAL_STAGE_SINGLE_GPU,
                problems=((PROBLEM_SINGLE_GPU, blocked),))
        rc = _run_config_service(run_config_service)
        refusal = self._from_failures_refusal(
            rc, failures_path, seeds, output_root,
            peft, config_variant, phrase)
        if refusal is not None:
            return refusal
        argv = run_config.compose_from_failures_argv(
            failures_path, seeds, output_root,
            peft=peft, config_variant=config_variant)
        return self.launch_argv(
            argv, output_root, spawner=spawner, clock=clock)

    def launch_from_pairs(self, pairs, seeds, output_root,
                          peft="none", config_variant="none",
                          phrase=None, run_config_service=None,
                          spawner=None, clock=None):
        """The [e] resume launch (261018-toe): materialize the
        screen-derived incomplete (model, task) pairs as a
        failures-shaped file, then delegate to ``launch_from_failures``
        VERBATIM — single-GPU stage-0, official-keys, the E2' phrase
        gate over the pairs×seeds effective matrix, composition, and
        spawn are all the delegated path's own, never duplicated here.

        Seam decision (the maintainer's investigate-and-document item,
        2026-10-18): option (a) — in-memory incomplete pairs MATERIALIZED
        as a pairs file routed through the existing from-failures
        machinery. Option (b) (re-launch the original matrix relying on
        resume-skip) is unimplementable-honestly: an interrupted root
        has NO manifest (it lands only at sweep end), so the "original
        matrix" is not recoverable from disk — only the discovered
        incomplete cells are. Option (a) matches the ruling's
        incomplete-set definition exactly (failed + interrupted pairs;
        completed cells inside those pairs skip via the existing
        trainer_state resume markers). Materializing to a file (not
        extending run_config to take pairs inline) keeps run_config
        untouched and reuses the driver's own ``--from-failures``
        validation in BOTH the gate (``_from_failures_refusal`` re-reads
        the file via run_sweep.load_failure_pairs) and the child — zero
        duplicated gate logic.

        The file lands under ``settings.state_dir()/resume/
        resume_pairs_{rootname}.json`` (NEVER inside the output root),
        written with ``settings.atomic_write`` BEFORE delegation and
        NEVER deleted after spawn (the child reads it at startup;
        per-root naming bounds growth; a same-root re-[e] is blocked by
        the live-root/single-GPU guards before it could overwrite a
        file a live child still reads).

        Args:
            pairs: the incomplete (model, task) pairs — model identity
                VERBATIM (alias names included); a "+lora"/"+ia3"
                suffix derives the entry's ``base_model`` the same way
                ``run_sweep.load_failure_pairs`` strips it.
            seeds: the resume seed fan-out.
            output_root: the resume output root (the dead run's own).
            peft: adapter mode (none = absent from argv).
            config_variant: variant lane (none = absent).
            phrase: the operator-typed E2' phrase; None/"" refuse an
                E2'-class resume (ignored for an ordinary partial one).
            run_config_service: an injectable seam double; None uses the
                REAL run_config module.
            spawner: a per-call seam override; None uses the instance
                seam.
            clock: an injectable ``datetime.now``-shaped callable.

        Returns:
            LaunchOutcome | GateRefusal: the delegated
            ``launch_from_failures`` outcome, or its refusal (the
            spawner provably never called).
        """
        resume_dir = settings.state_dir() / RESUME_PAIRS_DIR_NAME
        resume_dir.mkdir(parents=True, exist_ok=True)
        pairs_path = resume_dir / (
            f"resume_pairs_{Path(output_root).name}.json")
        entries = []
        for model, task in pairs:
            entry = {"model": model, "task": task}
            base = model.removesuffix("+lora").removesuffix("+ia3")
            if base != model:
                entry["base_model"] = base
            entries.append(entry)
        settings.atomic_write(
            pairs_path,
            json.dumps(entries, indent=4, ensure_ascii=False,
                      sort_keys=True))
        return self.launch_from_failures(
            pairs_path, seeds, output_root,
            peft=peft, config_variant=config_variant, phrase=phrase,
            run_config_service=run_config_service, spawner=spawner,
            clock=clock)

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

        WR-04 (phase-11 review): entries whose Popen has EXITED are
        pruned at read time (dropped, parent-side tee handle closed) —
        a TUI-launched run_sweep that died without writing a manifest
        (kernel OOM-kill, external SIGKILL, a CUDA crash taking down
        the driver) otherwise stays in live_roots for the whole session
        and the scanner classifies the root ``running`` unconditionally
        (live wins over every churn/mtime signal). Once pruned, the
        root degrades to the scanner's honest mtime/artifacts
        classification — dead-without-manifest reads artifacts-only,
        never a false running glyph or a killable corpse in the exit
        modal.

        Returns:
            tuple[str, ...]: the RESOLVED output roots whose registered
            process is still alive.
        """
        live: list[str] = []
        for root in sorted(self._live):
            entry = self._live[root]
            if entry["handle"].poll() is None:
                live.append(root)
            else:
                self._live.pop(root, None)
                self._drop_entry(entry)
        return tuple(live)

    def tee_path_for(self, root):
        """One root's tee log path (the [t] modal's source).

        The LIVE registry entry first. IN-05 (phase-11 review): a root
        whose entry was dropped by detach/kill falls back to the LAST
        tee path this launcher spawned for it — the tee FILE still
        stands under ``state/logs`` (the child owns its own inherited
        descriptor), so a sweep THIS TUI launched never renders the
        false "CLI-launched, no tee" copy after the exit modal's
        default detach. A relaunch overwrites the history entry (the
        newest launch's tee wins); a root this TUI never launched
        returns None — the honest unavailable state.

        Args:
            root: the output root as registered (resolved here).

        Returns:
            str | None: the tee path, or None for an unknown root.
        """
        root_key = str(Path(root).resolve())
        entry = self._live.get(root_key)
        if entry is not None:
            return entry["meta"].tee_path
        history = self._tee_history.get(root_key)
        if history is not None:
            return history
        return self._discover_fresh_tee(root_key)

    def _discover_fresh_tee(self, root_key):
        """The 2026-10-19 restart-reattach leg: after a console restart
        the registry AND the in-memory history are empty, but a
        detached child this console LAUNCHED keeps appending its
        inherited tee descriptor under ``state/logs`` — so the root's
        NEWEST on-disk tee whose mtime sits inside the fresh-append
        grace is that live run's own log. Read-only filesystem work,
        tolerant at every seam (an absent/unreadable logs dir reads
        None); a stale-only history reads None — an old run's log must
        never dress as the live tail. A root this TUI never launched
        (bare CLI, no tee at all) simply matches nothing here.
        """
        name = Path(root_key).name
        try:
            logs_dir = settings.state_dir() / TEE_DIR_NAME
            candidates = sorted(
                (candidate for candidate in logs_dir.iterdir()
                 if candidate.is_file()
                 and candidate.name.startswith("sweep_")
                 and candidate.name.endswith(".log")
                 and (candidate.name.endswith(f"_{name}.log")
                      or f"_{name}_" in candidate.name)),
                key=lambda candidate: candidate.stat().st_mtime,
                reverse=True)
        except OSError:
            return None
        now = time.time()
        for candidate in candidates:
            try:
                age = now - candidate.stat().st_mtime
            except OSError:
                continue
            if age <= TEE_FRESH_GRACE_SECONDS:
                return str(candidate)
            return None  # the newest is stale: nothing fresh exists
        return None

    # ===== The live-plan evidence (261017-uwr UWR-2 + 261020-blt) =====

    def _plan_for(self, argv) -> "object":
        """One argv's planned cells — (pairs frozenset, seeds tuple) —
        behind the instance cache (a full-matrix argv enumerates its
        ~8850 cells ONCE per session, not once per 2s tick). Keyed by
        the argv tuple — dead entries' cache rows are harmless (an argv
        that returns still maps to the same plan)."""
        argv_key = tuple(str(element) for element in argv)
        if argv_key not in self._plan_cache:
            self._plan_cache[argv_key] = run_config.argv_plan(
                list(argv_key))
        return self._plan_cache[argv_key]

    def live_sweep_plans(self) -> dict:
        """The live-sweep PLANNED CELLS per resolved root — (pairs
        frozenset, seeds tuple) — the 261020-blt planned-cell union's
        evidence source (the monitor's Running views synthesize QUEUED
        rows for planned-but-undiscovered pairs and complete discovered
        rows' planned-but-unstarted seeds off this map).

        Two evidence sources merged (the ``live_sweep_matrices``
        precedent):

        1. the REGISTRY's live handles (TUI-launched sweeps) — each
           entry's ``meta.argv`` (the verbatim launch argv) through
           ``run_config.argv_plan``;
        2. ``probe_cli_sweeps()`` — attached/discovered CLI-launched
           run_sweep processes found in /proc (a root the registry ALSO
           holds keeps the registry's argv — the exact launch argv is
           authoritative).

        An unparseable argv maps its root to None — live-but-unknown:
        that root keeps today's root-wide render, never a false queue.
        DISPLAY-ONLY evidence (the UWR-2 vocabulary): never gates a
        launch, a kill, or an exit.

        Returns:
            dict[str, tuple[frozenset[tuple[str, str]], tuple[int, ...]]
            | None]: resolved root -> the planned (pairs, seeds); None
            = live-but-unknown.
        """
        plans: dict[str, object] = {}
        for root in self.live_sweeps():
            entry = self._live.get(root)
            if entry is not None:
                plans[root] = self._plan_for(entry["meta"].argv)
        for root, argv in probe_cli_sweeps().items():
            if root not in plans:
                plans[root] = self._plan_for(argv)
        return plans

    def live_sweep_matrices(self) -> dict:
        """The live-sweep PLANNED pair matrices, per resolved root (the
        monitor's three-state cell evidence, 261017-uwr UWR-2).

        Two evidence sources merged:

        1. the REGISTRY's live handles (TUI-launched sweeps) — each
           entry's ``meta.argv`` (the verbatim launch argv) through
           ``run_config.argv_matrix``;
        2. ``probe_cli_sweeps()`` — attached/discovered CLI-launched
           run_sweep processes found in /proc (a root the registry ALSO
           holds keeps the registry's argv — the exact launch argv is
           authoritative).

        An unparseable argv maps its root to None — live-but-unknown:
        that root's cells keep the LEGACY activity semantics, never a
        false interrupt. DISPLAY-ONLY evidence: the kill face stays
        REGISTRY-ONLY (a probed CLI sweep has no Popen handle in this
        process; ``live_sweeps``/``kill_sweep`` are untouched and [k]
        keeps refusing it with MON_KILL_UNAVAILABLE).

        261020-blt: the leg-0 PROJECTION over ``live_sweep_plans``
        (the one parse + cache live there; this reader stays
        byte-compatible by construction).

        Returns:
            dict[str, frozenset[tuple[str, str]] | None]: resolved
            root -> the planned (model, task) pair matrix (None =
            live-but-unknown).
        """
        return {root: (plan[0] if plan is not None else None)
                for root, plan in self.live_sweep_plans().items()}

    def live_sweep_started(self) -> dict:
        """The live-sweep PROCESS-START epochs per resolved root (the
        261020-9vh stale-progress guard's evidence source).

        Two evidence sources merged (the ``live_sweep_matrices``
        precedent): the REGISTRY first — each live entry's
        ``meta.started_at`` (the launch moment, a tz-aware local ISO)
        through ``_iso_to_epoch``; then ``probe_cli_sweep_starts()``
        (attached/discovered CLI-launched run_sweep processes — the
        maintainer's exact case is CLI-launched) unioned via
        ``setdefault``: a root BOTH sources hold keeps the REGISTRY's
        spawn moment (authoritative — it is the launch this TUI
        performed).

        DISPLAY-ONLY evidence (UWR-2 vocabulary): never gates a
        launch, a kill, or an exit — the guard that consumes it only
        withholds a PREVIOUS run's parsed numbers at a reused root.

        Returns:
            dict[str, float]: resolved root -> the live process's
            start epoch (seconds); empty when no start evidence holds.
        """
        starts: dict[str, float] = {}
        for root in self.live_sweeps():
            entry = self._live.get(root)
            if entry is None:
                continue
            epoch = _iso_to_epoch(entry["meta"].started_at)
            if epoch is not None:
                starts[root] = epoch
        for root, start in probe_cli_sweep_starts().items():
            starts.setdefault(root, start)
        return starts
