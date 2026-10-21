"""
The gpu_probe service unit suite (Phase 16, 16-01, TUI-01).

Pins the nvidia-smi CSV probe contract (D16-01..D16-04) over the
INJECTED runner seam — ZERO nvidia-smi subprocess in any test lane (CI
zero-GPU, D16-14): the verified-live CSV shape parses to frozen sorted
``GpuRow`` rows, the runner receives the FIXED literal argv, and every
malformed output degrades the WHOLE probe to the absent outcome —
never an exception, never partial rows from a partial parse (D16-02).

The full four-mode degradation matrix (missing binary / non-zero exit /
timeout / one unparseable line — each asserting the SAME absent
outcome) and the panel render lane live in the same file's matrix
block and ``tests/tui/test_pilot_monitor.py`` (16-01 Task 2).

See also:
    ``tui/services/gpu_probe.py`` — the service under test.
    ``tests/tui/test_import_lock.py`` — the textual-free lock (the
    services glob covers gpu_probe.py automatically).
"""

from dataclasses import FrozenInstanceError

import pytest

from tui.services import gpu_probe
from tui.services.gpu_probe import PROBE_ARGV, GpuRow

#: The verified-live CSV shape (16-RESEARCH, probed on the 2x5090
#: validation box 2026-10-21): two GPUs, one line each — the exact
#: bytes the real query returns on an idle machine.
_LIVE_STDOUT = "0, 0, 2, 32607, 29\n1, 0, 2, 32607, 28\n"


def _recording_runner(returncode=0, stdout=""):
    """A canned runner that records the (argv, timeout) it saw."""
    calls: list = []

    def call(argv, timeout):
        calls.append((tuple(argv), timeout))
        return returncode, stdout

    return call, calls


# ===== the parse contract (D16-01 / D16-04) =====


def test_verified_live_csv_shape_parses_to_two_exact_rows():
    """The contract pin: the verified-live two-GPU CSV parses to two
    frozen GpuRow rows carrying those EXACT int fields — the fixed
    units ride the field names (no runtime unit parsing)."""
    runner, _calls = _recording_runner(stdout=_LIVE_STDOUT)
    rows = gpu_probe.probe(runner=runner)
    assert rows == (
        GpuRow(index=0, utilization_pct=0, memory_used_mib=2,
               memory_total_mib=32607, temperature_c=29),
        GpuRow(index=1, utilization_pct=0, memory_used_mib=2,
               memory_total_mib=32607, temperature_c=28),
    )
    assert all(isinstance(field, int) for row in rows
               for field in (
                   row.index, row.utilization_pct, row.memory_used_mib,
                   row.memory_total_mib, row.temperature_c))


def test_rows_sort_by_index_ascending():
    """D16-04: a runner returning indices out of order yields rows
    sorted by index ascending."""
    runner, _calls = _recording_runner(
        stdout="2, 5, 100, 1000, 40\n0, 1, 2, 3, 4\n1, 0, 0, 0, 0\n")
    rows = gpu_probe.probe(runner=runner)
    assert rows is not None
    assert [row.index for row in rows] == [0, 1, 2]


def test_runner_receives_the_fixed_literal_argv_and_timeout():
    """T-16-01: no operator input ever reaches the subprocess — the
    runner sees EXACTLY the fixed literal argv (never a shell string)
    and the per-call timeout threads through (D16-03)."""
    runner, calls = _recording_runner(stdout=_LIVE_STDOUT)
    gpu_probe.probe(runner=runner, timeout=1.5)
    assert calls == [(PROBE_ARGV, 1.5)]
    assert all(isinstance(element, str) for element in calls[0][0])
    assert calls[0][0].count("nvidia-smi") == 1


def test_zero_gpus_is_the_empty_tuple_not_the_absent_outcome():
    """D16-04: exit 0 with zero data lines parses to the EMPTY tuple —
    the explicit empty state, distinct from the absent outcome."""
    runner, _calls = _recording_runner(stdout="")
    assert gpu_probe.probe(runner=runner) == ()
    runner_blank, _calls2 = _recording_runner(stdout="\n \n")
    assert gpu_probe.probe(runner=runner_blank) == ()


# ===== the coercion discipline (D16-02 — one bad line degrades ALL) =====


def test_non_integer_field_degrades_the_whole_probe():
    """Strict per-field int coercion: one float (or non-numeric) field
    on ONE line degrades the WHOLE probe — the other line's good data
    never leaks as partial rows."""
    for malformed in ("0, 0.5, 2, 32607, 29\n",
                      "0, 0, 2, 32607, 29\n1, N/A, 2, 32607, 28\n",
                      "0, 0, 2, 32607, 29\nx, 0, 2, 32607, 28\n"):
        runner, _calls = _recording_runner(stdout=malformed)
        assert gpu_probe.probe(runner=runner) is None, malformed


def test_wrong_field_count_degrades_the_whole_probe():
    """A line with fewer or more than the five query columns is
    malformed — the whole probe degrades, never a partial parse."""
    for malformed in ("0, 0, 2, 32607\n",
                      "0, 0, 2, 32607, 29, 99\n",
                      "0, 0, 2, 32607, 29\n1, 0, 2, 32607\n"):
        runner, _calls = _recording_runner(stdout=malformed)
        assert gpu_probe.probe(runner=runner) is None, malformed


def test_gpu_rows_are_frozen():
    """The dataclass is frozen — pilot/golden fixtures fabricate rows
    that no render path can mutate (UI-SPEC Goldens)."""
    row = GpuRow(index=0, utilization_pct=47, memory_used_mib=15340,
                 memory_total_mib=32607, temperature_c=61)
    # setattr (not attribute assignment): ty correctly reads frozen
    # dataclass properties as read-only — the env_gate 08-01
    # ty-vs-intent precedent; the noqa covers ruff's inverse B010.
    with pytest.raises(FrozenInstanceError):
        setattr(row, "utilization_pct", 100)  # noqa: B010
