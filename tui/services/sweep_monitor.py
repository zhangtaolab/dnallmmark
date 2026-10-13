"""
sweep_monitor — the pure artifact-tree scanner behind slot-5 monitoring
(Phase 11, 11-04; MON-01..05's data half).

Everything the monitor SCREEN renders about sweeps derives from the pure
functions in this module:

- three-state root discovery — ``finished`` / ``running`` /
  ``artifacts_only`` — over the default output root plus XDG-persisted
  manual roots (D-03);
- tolerant ``run_record.json`` / ``sweep_manifest.json`` /
  ``sweep_failures.json`` readers with last-known-good retention for
  records damaged mid-write (D-09 — the artifact_loader None-sentinel
  contract, never a crash);
- per-(model, task, seed) cell-state derivation with resume-marker
  recognition and curve-fraction nesting (MON-01/MON-05);
- elapsed / ETA math (D-17): rolling median of completed-cell durations
  (skipped excluded), per-model median where derivable else global, the
  pinned variance-ratio range, and the honest pending/none degradations;
- the live failure list (MON-03): records while running, the failures
  file once finished (it lands only at sweep end);
- bounded seek-from-end log tails (MON-04).

PURE SCANNER declaration (plan prohibition, 11-04): no timers, no
threads, no subprocesses, zero textual imports. This module READS sweep
output trees; it never launches anything, never writes inside a sweep
tree, and never touches pipeline state. The scanning cadence (2s
frontier / 60s full, D-09) is owned by the screen, which calls these
functions from workers.

Artifact names are NEVER re-typed here: they import from ``run_sweep``
(D-05 same-source — the driver's own constants at pipeline/run_sweep.py,
stdlib-only and headless-importable). Write-timing truths this scanner
is built on (11-04 RESEARCH Area 4, source-verified): the record lands
POST-cell, the manifest and failures file land only at sweep END, and
the driver mkdirs the cell dir BEFORE the executor runs — so running
detection never depends on records.

Clock discipline: every wall-clock input is injectable (``now=`` epoch
seconds); with no injection the real clock is read once per call.
"""

import statistics
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)
from run_sweep import (  # D-05 same-source: the driver's own names
    FAILURES_NAME,
    MANIFEST_NAME,
    METRICS_NAME,
    RECORD_NAME,
    RESUME_MARKER,
)

from tui.services import settings

# ===== Locations + pinned constants =====

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The default output roots scanned when ``full_scan`` gets none (D-03 —
#: run_sweep's default ``./finetuned`` resolves to pipeline/finetuned
#: from the repo root).
DEFAULT_OUTPUT_ROOTS: tuple[Path, ...] = (
    REPO_ROOT / "pipeline" / "finetuned",
)

#: O2 pin — quiet-phase tolerance for the fresh-mtime running signal: a
#: running CLI sweep in a long model-load or eval phase shows NO churn,
#: and 600s covers the small-cell load/eval gaps observed on this D-15
#: dev host. MAINTAINER-TUNABLE: raise it for long quiet phases, never
#: below a cell's longest checkpoint save.
STALE_GRACE_SECONDS = 600.0

#: O4 pin — when the completed-cell durations' max/min exceeds this
#: ratio the ETA degrades from a point to a min-max range (D-17).
ETA_VARIANCE_RATIO = 3.0

#: Manual-roots persistence (D-03): operator-attached output roots under
#: the XDG STATE root, tolerant load + atomic save (T-08-03).
MANUAL_ROOTS_FILE_NAME = "monitor_roots.json"
MANUAL_ROOTS_SCHEMA_VERSION = 1

#: Full-scan watermark walk depth guard (files only): the sweep layout is
#: root/{model}/{task}/seed_{n}/{files | runs/ | checkpoint-*/ | frac_*},
#: so depth 5 sees checkpoint/tensorboard event files without ever
#: walking an unbounded tree (T-11-04-04).
_MAX_FULL_WALK_DEPTH = 5

#: Per-directory iteration cap on the bounded walks — a hostile/giant
#: directory degrades to a partial view, never a hang (T-11-04-04).
_SCAN_DIR_ENTRY_CAP = 512

# ===== State vocabularies (machine strings the screen maps to glyphs) =====

SWEEP_FINISHED = "finished"
SWEEP_RUNNING = "running"
SWEEP_ARTIFACTS_ONLY = "artifacts_only"

#: Cell states the screen renders: completed -> ``✓``, failed -> ``✗``,
#: skipped -> ``⊘`` (resume marker — distinct provenance), running ->
#: ``⠋``, queued -> ``◌``. A record with an unrecognized status renders
#: that status verbatim (honest, never translated).
CELL_COMPLETED = "completed"
CELL_FAILED = "failed"
CELL_SKIPPED = "skipped"
CELL_RUNNING = "running"
CELL_QUEUED = "queued"

#: Record statuses that end a cell's life for THIS sweep — progress
#: (``done``) and ETA remaining share this set so a failed or resumed
#: cell never inflates the remaining count.
TERMINAL_RECORD_STATUSES = frozenset(
    {CELL_COMPLETED, CELL_FAILED, CELL_SKIPPED})

#: EtaEstimate modes: ``pending`` (< 1 completed cell — 估算中),
#: ``point`` (median-based), ``range`` (high variance, min-max),
#: ``none`` (unknown total or nothing remaining — 总数未知/—).
ETA_PENDING = "pending"
ETA_POINT = "point"
ETA_RANGE = "range"
ETA_NONE = "none"

# ===== Data model (frozen — DATA, never screen copy) =====


@dataclass(frozen=True)
class SweepSummary:
    """One discovered sweep root and its three-state classification."""

    root: Path
    state: str
    done: int | None
    total: int | None  # None -> the unknown-total rendering (总数未知)
    newest_mtime: float | None


@dataclass(frozen=True)
class ScanResult:
    """A full scan's output: the sweep rows + the next scan's watermarks."""

    sweeps: tuple[SweepSummary, ...]
    #: newest file mtime per root (keyed by str(resolved root)) — feed
    #: back as ``prev_watermarks`` to make churn detectable.
    watermarks: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class CellSeed:
    """One seed column of a cell row.

    ``fraction_states`` is None for a plain cell; for a curve cell it
    carries one ``(frac_dir_name, state)`` pair per fraction (the seed
    cell's mini-count done/total basis and the detail modal's rows).
    """

    seed: int
    state: str
    fraction_states: tuple[tuple[str, str], ...] | None


@dataclass(frozen=True)
class CellRow:
    """One (model, task) row: the cell-table unit (MON-01).

    ``model`` is the dir/record identity VERBATIM — the alias under
    peft/config-variant, never translated to the base registry name.
    """

    model: str
    task: str
    seeds: tuple[CellSeed, ...]


@dataclass(frozen=True)
class FrontierSnapshot:
    """The light 2s pass over ONE root (D-09): newest activity + record
    states only — no manifest re-read, no walk beyond
    ``{model}/{task}/seed_*`` plus the seed dirs' direct children."""

    root: Path
    state: str
    newest_mtime: float | None
    newest_cell: tuple[str, str, int] | None  # (model, task, seed)
    cell_states: dict[tuple[str, str, int], str] = field(default_factory=dict)


@dataclass(frozen=True)
class CurrentCell:
    """The (model, task, seed) the sweep is working on right now."""

    model: str
    task: str
    seed: int


@dataclass(frozen=True)
class EtaEstimate:
    """D-17's ETA verdict — exactly one of the four modes is meaningful
    per instance (point in point mode, lo/hi in range mode, all None in
    pending/none)."""

    mode: str
    point_seconds: float | None
    lo_seconds: float | None
    hi_seconds: float | None


@dataclass(frozen=True)
class SweepStats:
    """The stats-line data (MON-02/D-17): done/total, current cell,
    elapsed seconds (None before the first record without a fallback
    start), and the ETA estimate."""

    done: int
    total: int | None
    current: CurrentCell | None
    elapsed_seconds: float | None
    eta: EtaEstimate


@dataclass(frozen=True)
class FailureRow:
    """One failed cell (MON-03): alias model identity verbatim."""

    model: str
    task: str
    seed: int
    error: str
    output_dir: str


# =====================================================================
# Task 1: discovery scan + three-state classification + manual roots
# =====================================================================


def _utc_now_epoch() -> float:
    """The real-clock fallback (tests always inject ``now``)."""
    return time.time()


def _now_epoch(now: float | None) -> float:
    return _utc_now_epoch() if now is None else float(now)


def manual_roots() -> tuple[Path, ...]:
    """The XDG-persisted operator-attached roots (D-03), resolved
    absolute and deduped in attach order; a corrupt file reads empty."""
    raise NotImplementedError


def add_manual_root(path) -> bool:
    """Attach an operator path as a monitored root.

    Refused (False, nothing persisted) unless the path passes the
    attach-validation predicate ``is_sweep_root`` — an invalid path is
    never silently added. Adding an already-attached root is a no-op
    returning True.
    """
    raise NotImplementedError


def remove_manual_root(path) -> bool:
    """Detach a manual root; True when it was attached, False when not."""
    raise NotImplementedError


def is_sweep_root(path) -> bool:
    """The [a] attach-validation predicate (D-03): a directory holding
    a sweep manifest / failures manifest, at least one run record
    (bounded depth-guarded scan), or the {model}/{task}/seed_* layout
    with cell artifacts (resume marker / metrics / runs dir)."""
    raise NotImplementedError


def full_scan(roots=None, live_roots=(), prev_watermarks=None, now=None):
    """Classify every root into exactly three states (D-03).

    Roots default to ``DEFAULT_OUTPUT_ROOTS + manual_roots()``; a
    nonexistent/unreadable root is skipped silently (the deleted-mid-
    monitor edge — degrade, never crash). Classification, first match
    wins: manifest present -> finished (counts from the manifest cells);
    root in live_roots -> running; newest-mtime watermark advanced vs
    ``prev_watermarks[root]`` -> running; newest mtime within
    STALE_GRACE_SECONDS of now -> running; else artifacts_only (prior
    standalone-run artifacts — unknown totals, never a running glyph).

    Returns ScanResult(sweeps sorted by root, watermarks for the next
    scan's churn comparison).
    """
    raise NotImplementedError


def frontier_scan(root, live_roots=(), now=None):
    """The light 2s pass (D-09): re-derive ONLY this root's newest
    seed-dir activity + record states — no manifest read, no walk
    beyond {model}/{task}/seed_* and the seed dirs' direct children."""
    raise NotImplementedError


# =====================================================================
# Task 2: tolerant readers + cell table derivation + resume recognition
# =====================================================================

#: Last-known-good parsed records, keyed by record-file path (D-09): a
#: file damaged mid-write falls back to its previous good parse; a file
#: that is missing (not damaged) reads as absent — deleting a record
#: never resurrects a stale view. Never cleared in production; tests
#: reset via ``_reset_last_known_good``.
_LAST_GOOD_RECORDS: dict[str, dict] = {}


def _reset_last_known_good() -> None:
    """Test seam: drop the last-known-good record cache."""
    _LAST_GOOD_RECORDS.clear()


def load_record(path):
    """Tolerantly load one run_record.json (D-09): None when absent or
    shape-invalid (non-dict); a damaged (present-but-unparseable) file
    returns its LAST-KNOWN-GOOD parse when one exists — the previous
    view stands, never a crash."""
    raise NotImplementedError


def load_manifest(path):
    """Tolerantly load a sweep_manifest.json: the parsed dict, or None
    when absent/unparseable/non-dict (corrupt = treated absent — the
    classification falls back to the churn/mtime rules)."""
    raise NotImplementedError


def load_failures(path):
    """Tolerantly load sweep_failures.json: the parsed list, or None
    when absent/unparseable/not a list."""
    raise NotImplementedError


def cells_view(root, expected_seeds=None) -> tuple[CellRow, ...]:
    """Derive the cell table (MON-01): one row per (model, task)
    discovered from seed dirs and/or manifest cells, per-seed states in
    seed order. ``expected_seeds`` threads the configured seed set —
    configured-but-not-yet-started seeds render queued (the ◌ columns).

    Per-seed state derivation, first match wins: a readable record's
    status (completed/failed/skipped map directly; an unrecognized
    status renders VERBATIM); no record + RESUME_MARKER -> skipped
    (resumed from a previous run); activity (runs/ or checkpoint-*
    present, or the seed dir mtime within the stale grace) -> running
    (running detection NEVER depends on records — the record lands
    post-cell); manifest-known -> queued.

    Curve nesting: seed cells with frac_* children carry
    ``fraction_states`` per fraction and fold to a seed state (any
    running -> running, any failed -> failed, all terminal ->
    completed, else queued).
    """
    raise NotImplementedError


def resume_count(root) -> int:
    """Cells skipped THIS run by the resume marker (the ⊘ note number,
    MON-05): the manifest's skipped cells once finished (this run's
    view — WR-12 keeps the on-disk record of the run that trained),
    else the skipped records on disk."""
    raise NotImplementedError


# =====================================================================
# Task 3: stats/elapsed/ETA (D-17) + live failures + log tail
# =====================================================================


def stats(root, expected_total=None, fallback_start=None, now=None):
    """The stats line (MON-02/D-17) over one root.

    ``total``: expected_total (the TUI-launched injected plan) or the
    manifest's cell count or None (CLI-launched, honestly unknown).
    ``current``: the newest-started record's (model, task, seed), else
    the newest-activity seed dir. ``elapsed_seconds``: now minus the
    earliest record started_at, else now minus fallback_start (a
    TUI-launched sweep before its first record), else None.
    """
    raise NotImplementedError


def eta_estimate(records, done, total, now=None, model_totals=None):
    """D-17's ETA math, pure over parsed records.

    Durations = completed records' finished_at - started_at wall-clock
    (skipped EXCLUDED — their ~zero duration biases the median;
    malformed stamps drop that record from the math, never crash).
    < 1 completed duration -> pending; total None or remaining <= 0 ->
    none. Point = sum(per-model remaining x that model's median) when
    the per-model plan (``model_totals`` from the manifest) is
    derivable — a model with no completion uses the GLOBAL median —
    else global median x remaining. >= 2 durations with max/min >
    ETA_VARIANCE_RATIO -> range (min x remaining, max x remaining).

    ``now`` is part of the pinned signature (the screen threads one
    injected clock through every call); the median-x-remaining math
    itself needs no wall clock.
    """
    raise NotImplementedError


def format_hms(seconds) -> str:
    """Elapsed rendering (UI-SPEC auto-default 17): ``H:MM:SS``."""
    raise NotImplementedError


def format_eta(seconds) -> str:
    """ETA humanization (auto-default 17): ``≈{m}m`` under an hour,
    ``≈{h}h`` (one decimal, trailing zero dropped) under a day,
    ``≈{d}d{h}h`` beyond. Numeric/English only — services stay
    CJK-free; the SCREEN prefixes the copy."""
    raise NotImplementedError


def failures_view(root) -> tuple[FailureRow, ...]:
    """The failure list (MON-03): sweep_failures.json once the manifest
    is present (authoritative — the file lands at sweep end), else the
    records with status failed (the LIVE source while running: each
    lands as its cell fails — O3)."""
    raise NotImplementedError


def read_log_tail(path, max_lines=200, max_bytes=65536):
    """Bounded seek-from-end tail (MON-04): the last ``max_lines`` lines
    of the final ``max_bytes`` window, decode errors replaced, the
    window's leading partial line dropped; None when the file is
    absent/unreadable (the screen renders the designed unavailable
    state, never a fabricated empty log)."""
    raise NotImplementedError
