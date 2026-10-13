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

import json
import time
from dataclasses import dataclass, field
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

#: EtaEstimate modes: ``pending`` (< 1 completed cell — the estimating
#: degradation), ``point`` (median-based), ``range`` (high variance,
#: min-max), ``none`` (unknown total or nothing remaining — the
#: unknown-total / dash renderings).
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
    total: int | None  # None -> the unknown-total rendering
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

_SEED_DIR_PREFIX = "seed_"
_FRAC_DIR_PREFIX = "frac_"


def _utc_now_epoch() -> float:
    """The real-clock fallback (tests always inject ``now``)."""
    return time.time()


def _now_epoch(now: float | None) -> float:
    return _utc_now_epoch() if now is None else float(now)


def _sorted_children(path: Path) -> list[Path]:
    """Sorted child entries; an unreadable dir reads empty (D-09 —
    degrade, never crash)."""
    try:
        return sorted(path.iterdir())
    except OSError:
        return []


def _is_dir(path: Path) -> bool:
    try:
        return path.is_dir()
    except OSError:
        return False


def _is_file(path: Path) -> bool:
    try:
        return path.is_file()
    except OSError:
        return False


def _seed_number(name: str) -> int | None:
    """seed_42 -> 42; anything else -> None."""
    if name.startswith(_SEED_DIR_PREFIX):
        digits = name[len(_SEED_DIR_PREFIX):]
        if digits.isdigit():
            return int(digits)
    return None


def _iter_files_bounded(root: Path, max_depth: int):
    """Yield files under root up to ``max_depth`` directory levels below
    it (files only, per the watermark contract) — the depth guard that
    keeps a full scan off unbounded trees (T-11-04-04)."""
    stack: list[tuple[Path, int]] = [(Path(root), 0)]
    while stack:
        directory, depth = stack.pop()
        for entry in _sorted_children(directory)[:_SCAN_DIR_ENTRY_CAP]:
            if _is_file(entry):
                yield entry
            elif depth + 1 <= max_depth and _is_dir(entry):
                stack.append((entry, depth + 1))


def _newest_file_mtime(
        root: Path, max_depth: int = _MAX_FULL_WALK_DEPTH) -> float | None:
    """The mtime watermark: max st_mtime over the bounded files-only
    walk (None for an empty/unreadable tree)."""
    newest: float | None = None
    for file_path in _iter_files_bounded(root, max_depth):
        try:
            mtime = file_path.stat().st_mtime
        except OSError:
            continue
        if newest is None or mtime > newest:
            newest = mtime
    return newest


def _iter_seed_dirs(root: Path):
    """Yield (model, task, seed, seed_dir) over the bounded
    {model}/{task}/seed_{n} walk (the frontier's depth bound); an
    unreadable or absent root yields nothing."""
    root = Path(root)
    for model_dir in _sorted_children(root)[:_SCAN_DIR_ENTRY_CAP]:
        if not _is_dir(model_dir):
            continue
        for task_dir in _sorted_children(model_dir)[:_SCAN_DIR_ENTRY_CAP]:
            if not _is_dir(task_dir):
                continue
            for entry in _sorted_children(task_dir)[:_SCAN_DIR_ENTRY_CAP]:
                seed = _seed_number(entry.name)
                if seed is None or not _is_dir(entry):
                    continue
                yield model_dir.name, task_dir.name, seed, entry


def _manual_roots_path() -> Path:
    return settings.state_dir() / MANUAL_ROOTS_FILE_NAME


def _save_manual_roots(roots: list[Path]) -> None:
    settings.atomic_write(
        _manual_roots_path(),
        json.dumps(
            {
                "schema_version": MANUAL_ROOTS_SCHEMA_VERSION,
                "roots": [str(path) for path in roots],
            },
            indent=4,
            ensure_ascii=False,
            sort_keys=True,
        ),
    )


def manual_roots() -> tuple[Path, ...]:
    """The XDG-persisted operator-attached roots (D-03), resolved
    absolute and deduped in attach order; a corrupt file reads empty."""
    data = artifact_loader.load_json_artifact(_manual_roots_path())
    if not isinstance(data, dict):
        return ()
    entries = data.get("roots")
    if not isinstance(entries, list):
        return ()
    resolved: dict[Path, None] = {}
    for entry in entries:
        if not isinstance(entry, str) or not entry.strip():
            continue
        resolved.setdefault(Path(entry).expanduser().resolve())
    return tuple(resolved)


def add_manual_root(path) -> bool:
    """Attach an operator path as a monitored root.

    Refused (False, nothing persisted) unless the path passes the
    attach-validation predicate ``is_sweep_root`` — an invalid path is
    never silently added. Adding an already-attached root is a no-op
    returning True.
    """
    resolved = Path(path).expanduser().resolve()
    if not is_sweep_root(resolved):
        return False
    roots = list(manual_roots())
    if resolved in roots:
        return True
    roots.append(resolved)
    _save_manual_roots(roots)
    return True


def remove_manual_root(path) -> bool:
    """Detach a manual root; True when it was attached, False when not."""
    resolved = Path(path).expanduser().resolve()
    roots = list(manual_roots())
    if resolved not in roots:
        return False
    roots.remove(resolved)
    _save_manual_roots(roots)
    return True


def is_sweep_root(path) -> bool:
    """The [a] attach-validation predicate (D-03): a directory holding
    a sweep manifest / failures manifest, at least one run record
    (bounded depth-guarded scan), or the {model}/{task}/seed_* layout
    with cell artifacts (resume marker / metrics / runs dir)."""
    root = Path(path)
    if not _is_dir(root):
        return False
    if _is_file(root / MANIFEST_NAME) or _is_file(root / FAILURES_NAME):
        return True
    for _model, _task, _seed, seed_dir in _iter_seed_dirs(root):
        if _is_file(seed_dir / RECORD_NAME):
            return True
        if _is_file(seed_dir / RESUME_MARKER):
            return True
        if _is_file(seed_dir / METRICS_NAME):
            return True
        if _is_dir(seed_dir / "runs"):
            return True
    return False


def _completed_and_terminal_counts(root: Path) -> tuple[int, int]:
    """(completed, terminal) record counts over the bounded seed walk —
    SweepSummary.done for non-finished roots (records are the only
    source while no manifest exists)."""
    completed = 0
    terminal = 0
    for record in _collect_records(root):
        status = record.get("status")
        if status == CELL_COMPLETED:
            completed += 1
        if status in TERMINAL_RECORD_STATUSES:
            terminal += 1
    return completed, terminal


def _manifest_cells(manifest: dict | None) -> list[dict]:
    """The manifest's cells list, shape-checked (non-lists read
    empty)."""
    if not isinstance(manifest, dict):
        return []
    cells = manifest.get("cells")
    return cells if isinstance(cells, list) else []


def _count_terminal_cells(cells: list) -> int:
    """Terminal-status cells over a manifest cells list (planned never
    counts — a dry-run manifest is 0 done over N total)."""
    return sum(
        1
        for cell in cells
        if isinstance(cell, dict)
        and cell.get("status") in TERMINAL_RECORD_STATUSES
    )


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

    Known edge (accepted, plan-pinned predicate order): a re-run at a
    root that already holds a finished manifest classifies finished
    until the new run's own manifest lands — the manifest is written
    only at sweep end, so the stale file wins over the churn signals.

    Returns ScanResult(sweeps sorted by root, watermarks for the next
    scan's churn comparison).
    """
    now = _now_epoch(now)
    if roots is None:
        roots = DEFAULT_OUTPUT_ROOTS + manual_roots()
    live = {Path(root).expanduser().resolve() for root in live_roots}
    previous: dict[str, float] = {
        str(key): float(value)
        for key, value in (prev_watermarks or {}).items()
    }
    sweeps: list[SweepSummary] = []
    watermarks: dict[str, float] = {}
    for root in roots:
        resolved = Path(root).expanduser().resolve()
        manifest = load_manifest(resolved / MANIFEST_NAME)
        if manifest is not None:
            cells = _manifest_cells(manifest)
            newest = _newest_file_mtime(resolved)
            if newest is not None:
                watermarks[str(resolved)] = newest
            sweeps.append(SweepSummary(
                root=resolved,
                state=SWEEP_FINISHED,
                done=_count_terminal_cells(cells),
                total=len(cells),
                newest_mtime=newest,
            ))
            continue
        if not _is_dir(resolved):
            continue  # nonexistent/unreadable: skipped silently
        newest = _newest_file_mtime(resolved)
        if newest is not None:
            watermarks[str(resolved)] = newest
        running = (
            resolved in live
            or (
                str(resolved) in previous
                and newest is not None
                and newest > previous[str(resolved)]
            )
            or (newest is not None and (now - newest) <= STALE_GRACE_SECONDS)
        )
        _completed, terminal = _completed_and_terminal_counts(resolved)
        sweeps.append(SweepSummary(
            root=resolved,
            state=SWEEP_RUNNING if running else SWEEP_ARTIFACTS_ONLY,
            done=terminal,
            total=None,
            newest_mtime=newest,
        ))
    return ScanResult(
        sweeps=tuple(sorted(sweeps, key=lambda summary: str(summary.root))),
        watermarks=watermarks,
    )


def _seed_dir_mtime(seed_dir: Path) -> float | None:
    try:
        return seed_dir.stat().st_mtime
    except OSError:
        return None


def frontier_scan(root, live_roots=(), now=None):
    """The light 2s pass (D-09): re-derive ONLY this root's newest
    seed-dir activity + record states — no manifest read, no walk
    beyond {model}/{task}/seed_* and the seed dirs' direct children
    (runs/, checkpoint-*/, frac_*/, records — never a recursive walk
    into checkpoint contents)."""
    resolved = Path(root).expanduser().resolve()
    now = _now_epoch(now)
    live = {Path(item).expanduser().resolve() for item in live_roots}

    newest_cell: tuple[str, str, int] | None = None
    newest_seed_dir: Path | None = None
    newest_seed_mtime: float | None = None
    seed_dirs: list[tuple[str, str, int, Path]] = []
    for model, task, seed, seed_dir in _iter_seed_dirs(resolved):
        seed_dirs.append((model, task, seed, seed_dir))
        mtime = _seed_dir_mtime(seed_dir)
        if mtime is not None and (
                newest_seed_mtime is None or mtime >= newest_seed_mtime):
            newest_seed_mtime = mtime
            newest_cell = (model, task, seed)
            newest_seed_dir = seed_dir

    cell_states: dict[tuple[str, str, int], str] = {}
    newest_child_mtime: float | None = newest_seed_mtime
    for model, task, seed, seed_dir in seed_dirs:
        state, _fraction_states = _seed_state_from_dir(
            seed_dir, now=now, frontier_newest=(seed_dir == newest_seed_dir))
        cell_states[(model, task, seed)] = state
        for child in _sorted_children(seed_dir)[:_SCAN_DIR_ENTRY_CAP]:
            try:
                mtime = child.stat().st_mtime
            except OSError:
                continue
            if newest_child_mtime is None or mtime > newest_child_mtime:
                newest_child_mtime = mtime

    running = resolved in live or (
        newest_child_mtime is not None
        and (now - newest_child_mtime) <= STALE_GRACE_SECONDS
    )
    return FrontierSnapshot(
        root=resolved,
        state=SWEEP_RUNNING if running else SWEEP_ARTIFACTS_ONLY,
        newest_mtime=newest_child_mtime,
        newest_cell=newest_cell,
        cell_states=cell_states,
    )


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
    view stands, never a crash. A MISSING file (not damaged) reads as
    absent — deleting a record never resurrects a stale view."""
    file_path = Path(path)
    if not _is_file(file_path):
        return None
    data = artifact_loader.load_json_artifact(file_path)
    if isinstance(data, dict):
        _LAST_GOOD_RECORDS[str(file_path)] = data
        return data
    return _LAST_GOOD_RECORDS.get(str(file_path))


def load_manifest(path):
    """Tolerantly load a sweep_manifest.json: the parsed dict, or None
    when absent/unparseable/non-dict (corrupt = treated absent — the
    classification falls back to the churn/mtime rules)."""
    data = artifact_loader.load_json_artifact(Path(path))
    return data if isinstance(data, dict) else None


def load_failures(path):
    """Tolerantly load sweep_failures.json: the parsed list, or None
    when absent/unparseable/not a list."""
    data = artifact_loader.load_json_artifact(Path(path))
    return data if isinstance(data, list) else None


def _frac_children(seed_dir: Path) -> list[Path]:
    """The seed dir's frac_* child dirs, name-sorted."""
    return [
        child
        for child in _sorted_children(seed_dir)[:_SCAN_DIR_ENTRY_CAP]
        if child.name.startswith(_FRAC_DIR_PREFIX) and _is_dir(child)
    ]


def _dir_shows_activity(directory: Path, now: float) -> bool:
    """The churn signals inside one cell dir (11-04 RESEARCH Area 4):
    a runs/ or checkpoint-* child, or the dir mtime within the stale
    grace (mkdir-before-executor + tensorboard/checkpoint appearance)."""
    for child in _sorted_children(directory)[:_SCAN_DIR_ENTRY_CAP]:
        if child.name == "runs" and _is_dir(child):
            return True
        if child.name.startswith("checkpoint-") and _is_dir(child):
            return True
    mtime = _seed_dir_mtime(directory)
    return mtime is not None and (now - mtime) <= STALE_GRACE_SECONDS


def _cell_state_from_dir(cell_dir: Path, now: float) -> str:
    """First-match state for ONE cell dir (seed or fraction level):
    record status (unrecognized statuses render VERBATIM — honest,
    never translated) -> resume marker -> activity -> queued (an inert
    dir never started). Running detection NEVER depends on records
    (the record lands post-cell — Pitfall 2)."""
    record = load_record(cell_dir / RECORD_NAME)
    if record is not None:
        status = record.get("status")
        if isinstance(status, str) and status:
            return status
    if _is_file(cell_dir / RESUME_MARKER):
        return CELL_SKIPPED
    if _dir_shows_activity(cell_dir, now):
        return CELL_RUNNING
    return CELL_QUEUED


def _fold_frac_states(states) -> str:
    """Fold fraction states into the seed cell's state: any running ->
    running, any failed -> failed, all terminal -> completed, else
    queued."""
    states = list(states)
    if any(state == CELL_RUNNING for state in states):
        return CELL_RUNNING
    if any(state == CELL_FAILED for state in states):
        return CELL_FAILED
    if states and all(
            state in (CELL_COMPLETED, CELL_SKIPPED) for state in states):
        return CELL_COMPLETED
    return CELL_QUEUED


def _seed_state_from_dir(
        seed_dir: Path, now: float,
        frontier_newest: bool = False) -> tuple[str, tuple[tuple[str, str], ...] | None]:
    """Derive (state, fraction_states) for one seed dir. Curve cells
    carry one (frac_name, state) pair per fraction and fold; the
    frontier's newest seed dir renders running even before its first
    artifact lands (the driver mkdirs before the executor runs)."""
    fracs = _frac_children(seed_dir)
    if fracs:
        fraction_states = tuple(
            (frac.name, _cell_state_from_dir(frac, now)) for frac in fracs)
        state = _fold_frac_states(
            [state for _name, state in fraction_states])
        if frontier_newest and state == CELL_QUEUED:
            return CELL_RUNNING, fraction_states
        return state, fraction_states
    if frontier_newest:
        record = load_record(seed_dir / RECORD_NAME)
        status = (record or {}).get("status")
        if not (isinstance(status, str) and status) and not _is_file(
                seed_dir / RESUME_MARKER):
            return CELL_RUNNING, None
    return _cell_state_from_dir(seed_dir, now), None


def _collect_records(root: Path) -> list[dict]:
    """Every parsed run_record.json over the bounded seed/frac walk,
    iteration-ordered deterministically (model, task, seed, frac)."""
    records: list[dict] = []
    for _model, _task, _seed, seed_dir in _iter_seed_dirs(root):
        for cell_dir in [seed_dir, *_frac_children(seed_dir)]:
            record = load_record(cell_dir / RECORD_NAME)
            if record is not None:
                records.append(record)
    return records


def cells_view(root, expected_seeds=None) -> tuple[CellRow, ...]:
    """Derive the cell table (MON-01): one row per (model, task)
    discovered from seed dirs and/or manifest cells, per-seed states in
    seed order. ``expected_seeds`` threads the configured seed set —
    configured-but-not-yet-started seeds render queued (the queued
    columns).

    Per-seed state derivation, first match wins: a readable record's
    status (completed/failed/skipped map directly; an unrecognized
    status renders VERBATIM); no record + RESUME_MARKER -> skipped
    (resumed from a previous run); activity (runs/ or checkpoint-*
    present, or the seed dir mtime within the stale grace, or the
    root's newest seed dir) -> running (running detection NEVER depends
    on records — the record lands post-cell); manifest-known ->
    queued.

    Curve nesting: seed cells with frac_* children carry
    ``fraction_states`` per fraction and fold to a seed state (any
    running -> running, any failed -> failed, all terminal ->
    completed, else queued). The mtime-grace leg reads the real clock
    (the screen's cadence owns time); tests pin mtimes relative to it.
    """
    root_path = Path(root)
    now = _utc_now_epoch()

    manifest_cells: dict[tuple[str, str], set[int]] = {}
    for cell in _manifest_cells(load_manifest(root_path / MANIFEST_NAME)):
        if not isinstance(cell, dict):
            continue
        model, task, seed = (
            cell.get("model"), cell.get("task"), cell.get("seed"))
        if (isinstance(model, str) and isinstance(task, str)
                and isinstance(seed, int)):
            manifest_cells.setdefault((model, task), set()).add(seed)

    discovered: dict[tuple[str, str], dict[int, Path]] = {}
    newest_seed_dir: Path | None = None
    newest_seed_mtime: float | None = None
    for model, task, seed, seed_dir in _iter_seed_dirs(root_path):
        discovered.setdefault((model, task), {})[seed] = seed_dir
        mtime = _seed_dir_mtime(seed_dir)
        if mtime is not None and (
                newest_seed_mtime is None or mtime >= newest_seed_mtime):
            newest_seed_mtime = mtime
            newest_seed_dir = seed_dir

    rows: list[CellRow] = []
    for model, task in sorted(set(discovered) | set(manifest_cells)):
        seeds: dict[int, CellSeed] = {}
        for seed, seed_dir in discovered.get((model, task), {}).items():
            state, fraction_states = _seed_state_from_dir(
                seed_dir, now=now,
                frontier_newest=(seed_dir == newest_seed_dir))
            seeds[seed] = CellSeed(
                seed=seed, state=state, fraction_states=fraction_states)
        for seed in manifest_cells.get((model, task), set()):
            seeds.setdefault(
                seed, CellSeed(seed=seed, state=CELL_QUEUED,
                               fraction_states=None))
        for seed in expected_seeds or ():
            if isinstance(seed, int):
                seeds.setdefault(
                    seed, CellSeed(seed=seed, state=CELL_QUEUED,
                                   fraction_states=None))
        rows.append(CellRow(
            model=model, task=task,
            seeds=tuple(seeds[seed] for seed in sorted(seeds))))
    return tuple(rows)


def resume_count(root) -> int:
    """Cells skipped THIS run by the resume marker (the resume note
    number, MON-05): the manifest's skipped cells once finished (this
    run's view — WR-12 keeps the on-disk record of the run that
    trained), else the skipped records on disk."""
    root_path = Path(root)
    manifest = load_manifest(root_path / MANIFEST_NAME)
    if manifest is not None:
        return sum(
            1
            for cell in _manifest_cells(manifest)
            if isinstance(cell, dict) and cell.get("status") == CELL_SKIPPED
        )
    return sum(
        1
        for record in _collect_records(root_path)
        if record.get("status") == CELL_SKIPPED
    )


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
