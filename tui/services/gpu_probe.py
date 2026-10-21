"""
gpu_probe — the read-only nvidia-smi CSV probe (Phase 16, 16-01, TUI-01).

The service half of the monitor's G GPU-lanes panel: it probes
``nvidia-smi`` once per call through the FIXED literal query argv and
returns frozen :class:`GpuRow` rows. The screen owns cadence and
rendering (D16-03 — this module is a pure callable, no timers, no
resident poller thread); it never raises into the console and never
fabricates data (D16-02).

Contract (locked decisions):

- D16-01: the probe argv is the FIXED literal list
  ``nvidia-smi --query-gpu=index,utilization.gpu,memory.used,
  memory.total,temperature.gpu --format=csv,noheader,nounits`` — a LIST
  of str, never a shell string (the ``_default_spawner`` discipline);
  NO operator input ever reaches the subprocess (T-16-01). Units are
  FIXED by the query (%, MiB, °C) — the dataclass field names carry
  them; there is no runtime unit parsing. pynvml is out of scope.
- D16-02: ONE absent outcome for EVERY failure mode — missing binary,
  non-zero exit, timeout, unparseable output. ONE malformed CSV line
  degrades the WHOLE probe (the deps-tolerance per-package rule):
  never partial rows from a partial parse, never an exception.
- D16-03: the per-call timeout (~2s) bounds the call so a hung
  nvidia-smi can never block the panel's worker. WR-05 (phase-16
  review) closes the residual gap: the POST-KILL reap carries the SAME
  finite budget — an un-reapable D-state child degrades to the absent
  outcome with one logged warning instead of blocking the exclusive
  worker forever (a rare zombie until the driver recovers is the
  accepted trade-off).
- D16-04: rows sort by index ascending; a successful probe with zero
  GPUs returns the EMPTY tuple (the explicit empty state, distinct
  from the absent outcome).

Injection seam (D16-14 — CI zero-GPU): the runner is parameter-
injectable (the EnvCheckServiceProtocol pattern); it receives the argv
and the timeout and returns ``(returncode, stdout)`` together, so
tests inject canned outcomes without any nvidia-smi subprocess
(16-RESEARCH Pattern 1).

ZERO textual imports (the services-tier invariant,
``tests/tui/test_import_lock.py`` — the glob covers this module
automatically). Dependencies: stdlib ``subprocess``/``dataclasses``/
``logging`` only (the logger is the tier's first and only diagnostic;
every NORMAL path stays silent).
"""

import logging
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

#: The FIXED literal probe argv (D16-01 / T-16-01) — the verified-live
#: query on the 2x5090 validation box (2026-10-21): each GPU renders one
#: CSV line like ``0, 0, 2, 32607, 29`` (no header, no units).
PROBE_ARGV: tuple[str, ...] = (
    "nvidia-smi",
    (
        "--query-gpu=index,utilization.gpu,memory.used,memory.total,"
        "temperature.gpu"
    ),
    "--format=csv,noheader,nounits",
)

#: The per-call timeout in seconds (D16-03) — short so the panel's
#: worker never blocks the cadence; a probe that exceeds it degrades to
#: the absent outcome like every other failure.
PROBE_TIMEOUT_SECONDS: float = 2.0

#: The runner seam's shape: ``(argv, timeout) -> (returncode, stdout)``.
Runner = Callable[..., "tuple[int, str]"]

#: The CSV column count (index, utilization, memory.used, memory.total,
#: temperature) — a line carrying any other count is malformed.
_FIELD_COUNT = 5

#: The module logger (WR-05): the services tier is silent on every
#: NORMAL path; the ONE diagnostic — an un-reapable post-SIGKILL child
#: (a wedged nvidia-smi in D state) — warns here so a wedged driver is
#: diagnosable from a configured log sink without ever blocking (no
#: handler is installed; an unconfigured run keeps the absent-outcome
#: degradation as the only user-visible signal).
_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class GpuRow:
    """One GPU's probe reading — frozen, machine-truth data only.

    The units are FIXED by the query (the field names carry them: %,
    MiB, °C); there is no runtime unit parsing and no fabricated value
    (D16-01). Frozen so pilot/golden fixtures fabricate rows safely
    (UI-SPEC Goldens: plain frozen dataclasses are trivially fakeable).
    """

    index: int
    utilization_pct: int
    memory_used_mib: int
    memory_total_mib: int
    temperature_c: int


def _default_runner(argv: "tuple[str, ...]", timeout: float) -> "tuple[int, str]":
    """The real subprocess seam (the injectable default — the
    ``_default_spawner`` precedent): run the FIXED argv under the
    timeout and return ``(returncode, stdout)`` TOGETHER so the probe's
    degradation matrix never needs a second channel.

    WR-05 (phase-16 review): the post-kill reap is BOUNDED by the SAME
    budget as the call — ``communicate(timeout=...)``, then on
    TimeoutExpired ``kill()`` + ``wait(timeout=timeout)``. CPython's
    ``subprocess.run`` timeout path kills and then waits WITHOUT a
    timeout, and SIGKILL cannot interrupt a process in uninterruptible
    (D) state — a wedged NVIDIA driver holding nvidia-smi in an ioctl
    would block the panel's exclusive worker FOREVER (one stuck thread
    + one zombie nvidia-smi per 2s tick). A SECOND TimeoutExpired
    treats the child as the absent outcome (the caller's degradation)
    and leaks the ALREADY-KILLED handle — a rare zombie until the
    driver recovers is strictly better than a stuck worker — with one
    warning on the module logger.

    Args:
        argv: the literal argv (always :data:`PROBE_ARGV` at runtime —
            no caller-supplied element ever reaches the process).
        timeout: the per-call timeout in seconds (D16-03) — also the
            post-kill reap budget.

    Returns:
        ``(returncode, stdout)`` — the captured stdout as text.

    Raises:
        FileNotFoundError / TimeoutExpired / SubprocessError: the three
        runner-side failure modes (a timeout whose child also survives
        its bounded reap re-raises the ORIGINAL TimeoutExpired after
        the warning); :func:`probe` degrades them all to the absent
        outcome (never raises onward).
    """
    process = subprocess.Popen(
        list(argv), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True)
    try:
        stdout, _stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # the child is un-reapable even after SIGKILL (a D-state
            # driver wedge): degrade + warn once + leak the killed
            # handle — never block the exclusive worker on the reap
            _LOG.warning(
                "nvidia-smi (pid %s) un-reapable %ss after SIGKILL — "
                "driver wedge suspected; leaking the killed handle, "
                "probe degrades to the absent outcome",
                process.pid, timeout)
        raise
    return process.returncode, stdout


def probe(runner: "Runner | None" = None,
          timeout: float = PROBE_TIMEOUT_SECONDS) -> "tuple[GpuRow, ...] | None":
    """Probe every GPU through nvidia-smi (the module entry point).

    Args:
        runner: the subprocess seam — ``runner(argv, timeout)`` returns
            ``(returncode, stdout)``. None means the REAL
            ``subprocess.run`` seam (tests inject canned outcomes; CI
            never spawns nvidia-smi, D16-14).
        timeout: the per-call timeout in seconds (D16-03, ~2s).

    Returns:
        The frozen :class:`GpuRow` rows sorted by index ascending
        (D16-04); the EMPTY tuple when the probe succeeds with zero
        GPUs (the explicit empty state); or ``None`` — the ONE absent
        outcome shared by every failure mode (missing binary, non-zero
        exit, timeout, unparseable output — D16-02): never raises,
        never partial rows from a partial parse (one malformed line
        degrades the whole probe).
    """
    if runner is None:
        runner = _default_runner
    try:
        returncode, stdout = runner(PROBE_ARGV, timeout)
    except (OSError, subprocess.SubprocessError):
        # FileNotFoundError (missing binary) and TimeoutExpired are
        # both covered here — the absent outcome, never a crash.
        return None
    except Exception:  # noqa: BLE001 — the never-raise contract (D16-02)
        return None
    if returncode != 0:
        return None
    rows: list[GpuRow] = []
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != _FIELD_COUNT:
            return None  # one malformed line degrades the WHOLE probe
        try:
            values = [int(field) for field in fields]
        except ValueError:
            return None  # strict per-field int coercion — no partial parse
        rows.append(GpuRow(*values))
    rows.sort(key=lambda row: row.index)
    return tuple(rows)
