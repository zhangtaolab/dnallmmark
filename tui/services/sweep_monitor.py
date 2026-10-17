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

C4J-3 (261015-c4j) — the training-progress parse: ``cell_progress``
reads the newest ``checkpoint-*/trainer_state.json`` under a RUNNING
seed dir (``RESUME_MARKER`` is the same artifact name as the completion
marker — read from checkpoint dirs MID-RUN and from the seed root
post-run). The parse is tolerant through ``artifact_loader``
(damage/absence degrade to the all-None CellProgress — never a crash,
never a fabricated number; percent = round(step/max*100) clamped 0..100
only when max_steps > 0), and ``entries_progress`` parses ONLY the
running seeds on the same bounded walk the frontier uses (the 2s
cadence stays light).

261016-vxr (VXR-1) — the checkpoint-pair ETA: ``cell_progress`` also
derives ``CellProgress.eta_seconds`` from the TWO NEWEST checkpoints
(rate = Δglobal_step / Δ trainer_state.json FILE mtime; probed:
trainer_state.json carries NO wall-clock field, so the file mtime IS
the cadence source — every launch mode, no tee-log coupling). Strict
validity gates; every underivable shape degrades to None (the screen's
honest dim dash) — never a fabricated estimate, never a raise.

Clock discipline: every wall-clock input is injectable (``now=`` epoch
seconds); with no injection the real clock is read once per call.
"""

import json
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

from tui.services import (
    run_config,  # the lane vocabularies (WR-01)
    settings,
)

# ===== Locations + pinned constants =====

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The default output roots scanned when ``full_scan`` gets none (D-03).
#: WR-06 (phase-11 review): BOTH resolution homes of run_sweep's
#: default ``./finetuned`` are covered — the TUI launcher pins the
#: subprocess cwd to ``pipeline/`` (so ``./finetuned`` resolves to
#: ``{repo}/pipeline/finetuned``), while run_sweep's own docstring
#: documents running from the REPO root (``python pipeline/run_sweep.py
#: ... --output-root ./finetuned``), which resolves against the CLI
#: process's CWD to ``{repo}/finetuned``. A nonexistent root is skipped
#: silently by the scan, so carrying both costs nothing on machines
#: that only ever use one.
DEFAULT_OUTPUT_ROOTS: tuple[Path, ...] = (
    REPO_ROOT / "pipeline" / "finetuned",
    REPO_ROOT / "finetuned",
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
#: ``⏵``, queued -> ``◌``, interrupted -> ``⏸`` (261017-uwr, UWR-1:
#: no record, no marker, and no live sweep plans the pair — historical
#: residue shown honestly, never a phantom running glyph). A record
#: with an unrecognized status renders that status verbatim (honest,
#: never translated).
CELL_COMPLETED = "completed"
CELL_FAILED = "failed"
CELL_SKIPPED = "skipped"
CELL_RUNNING = "running"
CELL_QUEUED = "queued"
CELL_INTERRUPTED = "interrupted"

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
    #: The row's newest seed-dir mtime (261017-uwr, UWR-4): the
    #: live-on-top group-0 sort key (freshest activity first). Filled
    #: by ``cells_view`` over the discovered seed dirs; the additive
    #: default (None) keeps every pre-existing constructor unchanged
    #: (frontier-merged rows carry None until the next full pass).
    newest_mtime: float | None = None


@dataclass(frozen=True)
class EntryView:
    """One (model, task) ENTRY's folded view over its seeds (C4J-3,
    261015-c4j — the slot-5 entries list's state cell; pure data, the
    screen renders).

    Attributes:
        state: the folded completion state — any seed running ->
            ``running``; any failed -> ``failed``; any interrupted ->
            ``interrupted`` (261017-uwr); all seeds terminal
            (completed|skipped, non-empty) -> ``completed``; else
            ``queued`` (the ``_fold_frac_states`` semantics at seed
            level).
        done: the count of TERMINAL seeds (completed|failed|skipped —
            the stats-line ``done`` convention).
        total: the row's seed count.
    """

    state: str
    done: int
    total: int


@dataclass(frozen=True)
class CellProgress:
    """One running seed's training progress parsed from its newest
    ``checkpoint-*/trainer_state.json`` (C4J-3; pure data, the screen
    renders — each field None when nothing parsed, never fabricated).

    Attributes:
        step: the parsed ``global_step`` (non-bool int; None when
            absent/damaged/non-numeric).
        max_steps: the parsed ``max_steps`` (same tolerance).
        percent: ``round(step/max_steps*100)`` clamped 0..100 — derived
            ONLY when both parsed and ``max_steps > 0`` (else None, the
            screen's honest indeterminate).
        eta_seconds: the checkpoint-pair step-cadence estimate
            (261016-vxr, VXR-1): ``rate = Δglobal_step /
            Δ(trainer_state.json file mtime)`` over the seed's TWO
            NEWEST checkpoints, ``eta = (max_steps − newest step) /
            rate``. ``trainer_state.json`` carries NO wall-clock field
            (probed), so the FILE mtime is the cadence source — works
            for every launch mode, no tee-log coupling. None whenever
            the pair is underivable (a single checkpoint, a damaged
            second, non-positive Δstep or Δmtime, max_steps at/past
            the current step) — the screen's honest dim dash, never a
            fabricated estimate.
    """

    step: int | None
    max_steps: int | None
    percent: int | None
    eta_seconds: float | None = None


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
    wins: root in live_roots -> running (LIVE EVIDENCE WINS,
    261018-08g — see below); manifest present -> finished (counts from
    the manifest cells); newest-mtime watermark advanced vs
    ``prev_watermarks[root]`` -> running; newest mtime within
    STALE_GRACE_SECONDS of now -> running; else artifacts_only (prior
    standalone-run artifacts — unknown totals, never a running glyph).

    Live evidence wins over a stale manifest (261018-08g, SOAK-3/F2 —
    supersedes the old accepted-edge predicate order): the live
    membership check runs BEFORE the manifest-present branch, so a
    re-run at a root that already holds a finished sweep_manifest.json
    classifies RUNNING (records-walk terminal count for done, total
    None) for the whole live run, never "finished" off the stale file.
    Rationale: the manifest lands only at sweep end, and re-run-at-
    same-root is the DEFAULT workflow (output_root persists in
    run_config.json), so before this rule a live re-run was invisible
    at the sweep level for its entire duration (the 2026-10-18 soak
    report FINDING 2). Live evidence = the launcher registry plus the
    /proc CLI probe, threaded by MonitorBackend.full_scan (261017-uwr);
    non-live roots classify byte-identically to the old order.

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
        if resolved in live:
            # LIVE WINS (261018-08g, SOAK-3): the running branch ahead
            # of the manifest read — a live re-run at a manifest-holding
            # root must show running (done from terminal records, total
            # None, watermark recorded), never the stale manifest's
            # finished counts.
            if not _is_dir(resolved):
                continue  # nonexistent/unreadable: skipped silently
            newest = _newest_file_mtime(resolved)
            if newest is not None:
                watermarks[str(resolved)] = newest
            _completed, terminal = _completed_and_terminal_counts(resolved)
            sweeps.append(SweepSummary(
                root=resolved,
                state=SWEEP_RUNNING,
                done=terminal,
                total=None,
                newest_mtime=newest,
            ))
            continue
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


def frontier_scan(root, live_roots=(), now=None, live_pairs=None):
    """The light 2s pass (D-09): re-derive ONLY this root's newest
    seed-dir activity + record states — no manifest read, no walk
    beyond {model}/{task}/seed_* and the seed dirs' direct children
    (runs/, checkpoint-*/, frac_*/, records — never a recursive walk
    into checkpoint contents).

    261017-uwr (UWR-1): ``live_pairs`` threads the live-sweep pair
    evidence into every per-seed state derivation (None = legacy
    activity semantics, byte-identical; a frozenset = the strict
    membership gate whose miss derives interrupted). The ROOT-level
    classification keeps the D-03 three states unchanged."""
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
        pair_live = (None if live_pairs is None
                     else (model, task) in live_pairs)
        state, _fraction_states = _seed_state_from_dir(
            seed_dir, now=now, frontier_newest=(seed_dir == newest_seed_dir),
            pair_live=pair_live)
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


def _cell_state_from_dir(cell_dir: Path, now: float,
                         pair_live: "bool | None" = None) -> str:
    """First-match state for ONE cell dir (seed or fraction level):
    record status (unrecognized statuses render VERBATIM — honest,
    never translated) -> resume marker -> INTERRUPTED (no live sweep
    plans the pair — kill-left/stale residue, 261017-uwr UWR-1) ->
    activity -> queued (an inert dir never started). Running detection
    NEVER depends on records (the record lands post-cell — Pitfall 2).

    ``pair_live`` semantics: None = NO EVIDENCE DATA (every
    pre-existing caller and fake — the legacy activity semantics,
    byte-identical); True = a live sweep plans this (model, task) pair
    (activity -> running, inert -> queued); False = nothing plans it
    (residue signals are moot — interrupted before any activity leg)."""
    record = load_record(cell_dir / RECORD_NAME)
    if record is not None:
        status = record.get("status")
        if isinstance(status, str) and status:
            return status
    if _is_file(cell_dir / RESUME_MARKER):
        return CELL_SKIPPED
    if pair_live is False:
        return CELL_INTERRUPTED
    if _dir_shows_activity(cell_dir, now):
        return CELL_RUNNING
    return CELL_QUEUED


def _fold_frac_states(states) -> str:
    """Fold fraction states into the seed cell's state: any running ->
    running, any failed -> failed, any interrupted -> interrupted, all
    terminal -> completed, else queued (261017-uwr: the interrupted
    leg between failed and completed)."""
    states = list(states)
    if any(state == CELL_RUNNING for state in states):
        return CELL_RUNNING
    if any(state == CELL_FAILED for state in states):
        return CELL_FAILED
    if any(state == CELL_INTERRUPTED for state in states):
        return CELL_INTERRUPTED
    if states and all(
            state in (CELL_COMPLETED, CELL_SKIPPED) for state in states):
        return CELL_COMPLETED
    return CELL_QUEUED


def _seed_state_from_dir(
        seed_dir: Path, now: float,
        frontier_newest: bool = False,
        pair_live: "bool | None" = None) -> tuple[str, tuple[tuple[str, str], ...] | None]:
    """Derive (state, fraction_states) for one seed dir. Curve cells
    carry one (frac_name, state) pair per fraction and fold; the
    frontier's newest seed dir renders running even before its first
    artifact lands (the driver mkdirs before the executor runs) —
    UWR-1 gates BOTH frontier legs on the pair evidence: no live pair
    means the newest dir reads interrupted, not running."""
    fracs = _frac_children(seed_dir)
    if fracs:
        fraction_states = tuple(
            (frac.name, _cell_state_from_dir(frac, now, pair_live=pair_live))
            for frac in fracs)
        state = _fold_frac_states(
            [state for _name, state in fraction_states])
        if frontier_newest and state == CELL_QUEUED:
            if pair_live is False:
                return CELL_INTERRUPTED, fraction_states
            return CELL_RUNNING, fraction_states
        return state, fraction_states
    if frontier_newest:
        record = load_record(seed_dir / RECORD_NAME)
        status = (record or {}).get("status")
        if not (isinstance(status, str) and status) and not _is_file(
                seed_dir / RESUME_MARKER):
            if pair_live is False:
                return CELL_INTERRUPTED, None
            return CELL_RUNNING, None
    return _cell_state_from_dir(seed_dir, now, pair_live=pair_live), None


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


def cells_view(root, expected_seeds=None, live_pairs=None) -> tuple[CellRow, ...]:
    """Derive the cell table (MON-01): one row per (model, task)
    discovered from seed dirs and/or manifest cells, per-seed states in
    seed order. ``expected_seeds`` threads the configured seed set —
    configured-but-not-yet-started seeds render queued (the queued
    columns).

    Per-seed state derivation, first match wins: a readable record's
    status (completed/failed/skipped map directly; an unrecognized
    status renders VERBATIM); no record + RESUME_MARKER -> skipped
    (resumed from a previous run); pair NOT live + no marker ->
    interrupted (261017-uwr, UWR-1: kill-left checkpoint residue, a
    stale dir, the root's newest dir — historical residue, never a
    phantom running glyph); activity (runs/ or checkpoint-* present, or
    the seed dir mtime within the stale grace) -> running (running
    detection NEVER depends on records — the record lands post-cell);
    manifest-known -> queued. ``live_pairs`` None = no evidence data =
    the legacy activity semantics for every pre-existing caller
    (byte-identical); a frozenset = the strict per-(model, task)
    membership gate over a live sweep's planned matrix.

    Curve nesting: seed cells with frac_* children carry
    ``fraction_states`` per fraction and fold to a seed state (any
    running -> running, any failed -> failed, any interrupted ->
    interrupted, all terminal -> completed, else queued). The
    mtime-grace leg reads the real clock (the screen's cadence owns
    time); tests pin mtimes relative to it.
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
        row_newest_mtime: float | None = None
        for seed, seed_dir in discovered.get((model, task), {}).items():
            pair_live = (None if live_pairs is None
                         else (model, task) in live_pairs)
            state, fraction_states = _seed_state_from_dir(
                seed_dir, now=now,
                frontier_newest=(seed_dir == newest_seed_dir),
                pair_live=pair_live)
            seeds[seed] = CellSeed(
                seed=seed, state=state, fraction_states=fraction_states)
            seed_mtime = _seed_dir_mtime(seed_dir)
            if seed_mtime is not None and (
                    row_newest_mtime is None
                    or seed_mtime > row_newest_mtime):
                row_newest_mtime = seed_mtime  # UWR-4: the row's max
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
            seeds=tuple(seeds[seed] for seed in sorted(seeds)),
            newest_mtime=row_newest_mtime))
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
# C4J-3 (261015-c4j): the entry fold + the checkpoint progress parse
# =====================================================================

#: The checkpoint dir prefix under a seed dir (HF Trainer's save shape).
_CHECKPOINT_PREFIX = "checkpoint-"


def _checkpoint_number(name: str) -> "int | None":
    """checkpoint-1000 -> 1000; anything else (no prefix, non-numeric
    suffix) -> None — the NUMERIC parse lexical sort gets wrong
    (checkpoint-999 < checkpoint-1000)."""
    if not name.startswith(_CHECKPOINT_PREFIX):
        return None
    digits = name[len(_CHECKPOINT_PREFIX):]
    try:
        return int(digits)
    except ValueError:
        return None


def _non_bool_int(value) -> "int | None":
    """A non-bool int or None (the repo's bool-exclusion convention)."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _trainer_state_mtime(checkpoint: Path) -> "float | None":
    """One checkpoint dir's trainer_state.json FILE mtime (None when the
    file is absent/unreadable — the ETA's wall-clock source, 261016-vxr;
    trainer_state.json itself carries no timestamp field)."""
    try:
        return (checkpoint / RESUME_MARKER).stat().st_mtime
    except OSError:
        return None


def _eta_from_checkpoint_pair(
        newest: "tuple[int, Path] | None",
        second: "tuple[int, Path] | None",
        step: "int | None",
        max_steps: "int | None") -> "float | None":
    """The checkpoint-pair ETA (261016-vxr, VXR-1): rate = Δstep / Δmtime
    over the two NEWEST checkpoints, eta = remaining / rate.

    Strict validity gates, EVERY failure -> None (the honest dash, never
    a guess): both checkpoint dirs known, the second's trainer_state
    parses as a dict, its ``global_step`` is a non-bool int strictly
    below the newest's, both trainer_state.json FILE mtimes read with
    mtime_new > mtime_old, and ``max_steps`` strictly above the newest
    step (at/past the end nothing remains to estimate). Tolerant end to
    end — never raises into the cadence. No clamping: a stalled run
    shows a large honest ETA, a resumed run's first interval is simply
    underivable.
    """
    if (newest is None or second is None
            or step is None or max_steps is None):
        return None
    if max_steps <= step:
        return None
    old_state = artifact_loader.load_json_artifact(
        second[1] / RESUME_MARKER)
    if not isinstance(old_state, dict):
        return None
    step_old = _non_bool_int(old_state.get("global_step"))
    if step_old is None or step_old >= step:
        return None
    mtime_new = _trainer_state_mtime(newest[1])
    mtime_old = _trainer_state_mtime(second[1])
    if mtime_new is None or mtime_old is None or mtime_new <= mtime_old:
        return None
    rate = (step - step_old) / (mtime_new - mtime_old)
    if rate <= 0:
        return None
    return (max_steps - step) / rate


def cell_progress(seed_dir) -> CellProgress:
    """Parse one seed dir's training progress (C4J-3) — the newest
    ``checkpoint-*/trainer_state.json`` (the LARGEST NUMERIC suffix;
    lexical order is wrong and pinned so), plus the checkpoint-pair
    step-cadence ETA over the two newest (261016-vxr).

    Tolerant end to end (T-c4j-01): absent checkpoints, an unreadable
    dir, or a damaged/unparseable trainer_state degrade to the all-None
    CellProgress; ``global_step``/``max_steps`` must be non-bool ints;
    ``percent`` derives ONLY when both parsed and ``max_steps > 0``,
    clamped 0..100 — a poisoned checkpoint can never crash the cadence
    or fabricate a number. Bounded by the module's per-dir entry cap.

    Args:
        seed_dir: the ``{root}/{model}/{task}/seed_{n}`` dir.

    Returns:
        CellProgress: the parsed (or all-None) progress.
    """
    seed_dir = Path(seed_dir)
    best: tuple[int, Path] | None = None
    second: tuple[int, Path] | None = None
    for child in _sorted_children(seed_dir)[:_SCAN_DIR_ENTRY_CAP]:
        number = _checkpoint_number(child.name)
        if number is None or not _is_dir(child):
            continue
        if best is None or number > best[0]:
            second = best
            best = (number, child)
        elif second is None or number > second[0]:
            second = (number, child)
    if best is None:
        return CellProgress(step=None, max_steps=None, percent=None)
    state = artifact_loader.load_json_artifact(best[1] / RESUME_MARKER)
    if not isinstance(state, dict):
        return CellProgress(step=None, max_steps=None, percent=None)
    step = _non_bool_int(state.get("global_step"))
    max_steps = _non_bool_int(state.get("max_steps"))
    percent = None
    if step is not None and max_steps is not None and max_steps > 0:
        percent = max(0, min(100, round(step / max_steps * 100)))
    eta_seconds = _eta_from_checkpoint_pair(
        best, second, step, max_steps)
    return CellProgress(
        step=step, max_steps=max_steps, percent=percent,
        eta_seconds=eta_seconds)


def entry_fold(row: CellRow) -> EntryView:
    """Fold one CellRow's per-seed states to the ENTRY state (C4J-3 —
    the ``_fold_frac_states`` semantics at seed level): any running ->
    running, any failed -> failed, any interrupted -> interrupted
    (261017-uwr), all terminal (completed|skipped, non-empty) ->
    completed, else queued. ``done`` counts TERMINAL seeds
    (completed|failed|skipped — the stats-line done convention;
    interrupted is NOT terminal) over the row's total.

    Args:
        row (CellRow): one (model, task) row.

    Returns:
        EntryView: the folded state + the done/total seed counts.
    """
    states = [cell_seed.state for cell_seed in row.seeds]
    if any(state == CELL_RUNNING for state in states):
        state = CELL_RUNNING
    elif any(state == CELL_FAILED for state in states):
        state = CELL_FAILED
    elif any(state == CELL_INTERRUPTED for state in states):
        state = CELL_INTERRUPTED
    elif states and all(
            state in (CELL_COMPLETED, CELL_SKIPPED) for state in states):
        state = CELL_COMPLETED
    else:
        state = CELL_QUEUED
    done = sum(1 for value in states
               if value in TERMINAL_RECORD_STATUSES)
    return EntryView(state=state, done=done, total=len(states))


def entries_progress(root, live_pairs=None) -> "dict[tuple[str, str], CellProgress]":
    """The slot-5 entries list's progress map (C4J-3): walk the seed
    dirs ONCE (the frontier's bounded ``_iter_seed_dirs`` discipline),
    derive each seed's state, and for every (model, task) row whose
    fold is RUNNING parse progress for its running seed(s) — taking the
    MAX-step progress when several run (the serial driver makes this
    rare; mgpu worker roots are separate roots). Non-running rows parse
    nothing (the 2s cadence stays light, T-c4j-03) — including
    INTERRUPTED rows whose checkpoints are perfectly parseable
    (261017-uwr: a dead pair's residue is never re-parsed per tick); a
    running seed whose checkpoints parse nothing contributes no entry
    (the screen's honest indeterminate). ``live_pairs`` threads the
    live-sweep pair evidence (None = legacy semantics).

    Args:
        root: the sweep output root.
        live_pairs: the live sweep's planned (model, task) pairs, or
            None for the legacy activity semantics.

    Returns:
        dict: ``{(model, task): CellProgress}`` — empty when nothing
        runs (or nothing parses).
    """
    now = _utc_now_epoch()
    states: dict[tuple[str, str], dict[int, str]] = {}
    seed_dirs: dict[tuple[str, str, int], Path] = {}
    for model, task, seed, seed_dir in _iter_seed_dirs(Path(root)):
        pair_live = (None if live_pairs is None
                     else (model, task) in live_pairs)
        state, _fraction_states = _seed_state_from_dir(
            seed_dir, now=now, pair_live=pair_live)
        states.setdefault((model, task), {})[seed] = state
        seed_dirs[(model, task, seed)] = seed_dir
    result: dict[tuple[str, str], CellProgress] = {}
    for (model, task), seeds in states.items():
        best: CellProgress | None = None
        for seed, state in seeds.items():
            if state != CELL_RUNNING:
                continue
            progress = cell_progress(seed_dirs[(model, task, seed)])
            if progress.step is None:
                continue
            if best is None or progress.step > (best.step or 0):
                best = progress
        if best is not None:
            result[(model, task)] = best
    return result


# =====================================================================
# Task 3: stats/elapsed/ETA (D-17) + live failures + log tail
# =====================================================================


def _parse_iso(value) -> datetime | None:
    """Tolerant ISO-8601 parse: a malformed stamp returns None (the
    caller drops that record from the math, never crashes); a naive
    stamp is assumed UTC (the driver stamps UTC)."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _model_plan(manifest: dict | None) -> dict[str, int] | None:
    """The per-model cell totals from the manifest's cells — the
    per-model ETA plan (None when there is no manifest)."""
    if manifest is None:
        return None
    plan: dict[str, int] = {}
    for cell in _manifest_cells(manifest):
        if isinstance(cell, dict) and isinstance(cell.get("model"), str):
            plan[cell["model"]] = plan.get(cell["model"], 0) + 1
    return plan


def _current_cell(
        root: Path,
        records: list[dict]) -> CurrentCell | None:
    """The newest-started record's (model, task, seed) — record fields
    verbatim — else the newest-activity seed dir (the mkdir-before-
    executor cell the records do not know about yet)."""
    newest_epoch: float | None = None
    newest_record: dict | None = None
    for record in records:
        started = _parse_iso(record.get("started_at"))
        if started is None:
            continue
        epoch = started.timestamp()
        if newest_epoch is None or epoch >= newest_epoch:
            newest_epoch = epoch
            newest_record = record
    if newest_record is not None:
        model = newest_record.get("model")
        task = newest_record.get("task")
        seed = newest_record.get("seed")
        if (isinstance(model, str) and isinstance(task, str)
                and isinstance(seed, int)):
            return CurrentCell(model=model, task=task, seed=seed)
    newest_seed_dir: Path | None = None
    newest_mtime: float | None = None
    newest_identity: tuple[str, str, int] | None = None
    for model, task, seed, seed_dir in _iter_seed_dirs(root):
        mtime = _seed_dir_mtime(seed_dir)
        if mtime is not None and (
                newest_mtime is None or mtime >= newest_mtime):
            newest_mtime = mtime
            newest_seed_dir = seed_dir
            newest_identity = (model, task, seed)
    if newest_seed_dir is None or newest_identity is None:
        return None
    model, task, seed = newest_identity
    return CurrentCell(model=model, task=task, seed=seed)


def _elapsed_seconds(
        records: list[dict],
        fallback_start: float | None,
        now_epoch: float) -> float | None:
    """now minus the earliest record started_at; else now minus the
    injected launcher start (a TUI-launched sweep before its first
    record); else None (the dash rendering)."""
    earliest: float | None = None
    for record in records:
        started = _parse_iso(record.get("started_at"))
        if started is None:
            continue
        epoch = started.timestamp()
        if earliest is None or epoch < earliest:
            earliest = epoch
    if earliest is not None:
        return now_epoch - earliest
    if fallback_start is not None:
        return now_epoch - float(fallback_start)
    return None


def _records_for_run(records, fallback_start):
    """WR-02 (phase-11 review): scope parsed records to ONE run.

    With a ``fallback_start`` (the launch-injection seam: the TUI noted
    a run at this root), only records whose ``started_at`` parses to >=
    the start belong to THIS run — records accumulate at a root across
    runs (WR-12 discipline keeps old records), so the unscoped view of
    a re-run at a populated root would count the prior sweep's records
    (done 3005/8850-style corruption). Records whose ``started_at``
    cannot be parsed cannot be proven in-run and drop (never crash).
    Without a fallback (a CLI-launched/finished view) every record
    counts — the unscoped behavior, unchanged.
    """
    if fallback_start is None:
        return records
    start_epoch = float(fallback_start)
    scoped = []
    for record in records:
        started = _parse_iso(record.get("started_at")
                             if isinstance(record, dict) else None)
        if started is not None and started.timestamp() >= start_epoch:
            scoped.append(record)
    return scoped


def _manifest_is_fresh(manifest_path: Path, fallback_start) -> bool:
    """WR-02: a manifest is FRESH for a fallback-scoped run when its
    mtime is >= the run's start — the driver writes the manifest only
    at sweep END, so anything older predates the run (the prior
    sweep's stale counts). Without a fallback the question is moot
    (True); an unstat-able manifest reads stale (tolerant)."""
    if fallback_start is None:
        return True
    try:
        return manifest_path.stat().st_mtime >= float(fallback_start)
    except OSError:
        return False


def stats(root, expected_total=None, fallback_start=None, now=None):
    """The stats line (MON-02/D-17) over one root.

    ``total``: expected_total (the TUI-launched injected plan) or the
    manifest's cell count or None (CLI-launched, honestly unknown).
    ``current``: the newest-started record's (model, task, seed), else
    the newest-activity seed dir. ``elapsed_seconds``: now minus the
    earliest record started_at, else now minus fallback_start (a
    TUI-launched sweep before its first record), else None.

    WR-02 (phase-11 review): with a ``fallback_start`` (a run the TUI
    noted at this root — the [f]->[r] re-run flow lands here), the
    records scope to THIS run (``started_at`` >= the start) and a
    manifest whose mtime predates the start is STALE — it supplies
    neither the total nor the per-model ETA plan until the run's own
    manifest lands at sweep end. Without the injection (a CLI-launched
    or finished view) every record counts and any manifest governs —
    the unscoped behavior, unchanged.
    """
    root_path = Path(root)
    now_epoch = _now_epoch(now)
    records = _records_for_run(
        _collect_records(root_path), fallback_start)
    done = sum(
        1
        for record in records
        if record.get("status") in TERMINAL_RECORD_STATUSES
    )
    manifest_path = root_path / MANIFEST_NAME
    manifest = load_manifest(manifest_path)
    manifest_usable = (
        manifest is not None
        and _manifest_is_fresh(manifest_path, fallback_start))
    total: int | None = expected_total
    if total is None and manifest_usable:
        total = len(_manifest_cells(manifest))
    return SweepStats(
        done=done,
        total=total,
        current=_current_cell(root_path, records),
        elapsed_seconds=_elapsed_seconds(records, fallback_start, now_epoch),
        eta=eta_estimate(
            records, done, total, now=now_epoch,
            model_totals=(
                _model_plan(manifest) if manifest_usable else None)),
    )


def eta_estimate(records, done, total, now=None, model_totals=None):
    """D-17's ETA math, pure over parsed records.

    Durations = completed records' finished_at - started_at wall-clock
    (skipped EXCLUDED — their ~zero duration biases the median;
    malformed stamps and clock-skew negatives drop that record from
    the math, never crash). < 1 completed duration -> pending; total
    None or remaining <= 0 -> none. Point = sum(per-model remaining x
    that model's median) when the per-model plan (``model_totals``
    from the manifest) is derivable — a model with no completion uses
    the GLOBAL median — else global median x remaining. >= 2 durations
    with max/min > ETA_VARIANCE_RATIO -> range (min x remaining,
    max x remaining) replacing the point.

    ``now`` is part of the pinned signature (the screen threads one
    injected clock through every call); the median-x-remaining math
    itself needs no wall clock.
    """
    durations_by_model: dict[str, list[float]] = {}
    all_durations: list[float] = []
    for record in records:
        if not isinstance(record, dict) or (
                record.get("status") != CELL_COMPLETED):
            continue
        started = _parse_iso(record.get("started_at"))
        finished = _parse_iso(record.get("finished_at"))
        if started is None or finished is None:
            continue
        duration = (finished - started).total_seconds()
        if duration < 0:
            continue  # clock skew: drop the record, never crash
        model = record.get("model")
        model = model if isinstance(model, str) else ""
        durations_by_model.setdefault(model, []).append(duration)
        all_durations.append(duration)

    if not all_durations:
        return EtaEstimate(ETA_PENDING, None, None, None)
    if total is None:
        return EtaEstimate(ETA_NONE, None, None, None)
    remaining = total - done
    if remaining <= 0:
        return EtaEstimate(ETA_NONE, None, None, None)

    shortest = min(all_durations)
    longest = max(all_durations)
    if (len(all_durations) >= 2 and shortest > 0
            and longest / shortest > ETA_VARIANCE_RATIO):
        return EtaEstimate(
            ETA_RANGE, None, shortest * remaining, longest * remaining)

    global_median = statistics.median(all_durations)
    if model_totals:
        done_by_model: dict[str, int] = {}
        for record in records:
            if (isinstance(record, dict)
                    and record.get("status") in TERMINAL_RECORD_STATUSES
                    and isinstance(record.get("model"), str)):
                model = record["model"]
                done_by_model[model] = done_by_model.get(model, 0) + 1
        point = 0.0
        for model, model_total in model_totals.items():
            model_remaining = model_total - done_by_model.get(model, 0)
            if model_remaining <= 0:
                continue
            median = (
                statistics.median(durations_by_model[model])
                if model in durations_by_model
                else global_median
            )
            point += model_remaining * median
        return EtaEstimate(ETA_POINT, point, None, None)
    return EtaEstimate(ETA_POINT, global_median * remaining, None, None)


def format_hms(seconds) -> str:
    """Elapsed rendering (UI-SPEC auto-default 17): ``H:MM:SS``."""
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def format_eta(seconds) -> str:
    """ETA humanization (auto-default 17): ``≈{m}m`` under an hour,
    ``≈{h}h`` (one decimal, trailing zero dropped) under a day,
    ``≈{d}d{h}h`` beyond. Numeric/English only — services stay
    CJK-free; the SCREEN prefixes the copy."""
    seconds = float(seconds)
    if seconds < 3600:
        return f"≈{max(1, round(seconds / 60))}m"
    if seconds < 86400:
        return f"≈{round(seconds / 3600, 1):g}h"
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    return f"≈{days}d{hours}h"


def _failure_row(entry: dict) -> FailureRow | None:
    """Coerce one failure-shaped dict (manifest entry or record) into a
    FailureRow; shape-invalid entries are skipped (tolerant), the alias
    model identity kept verbatim."""
    model = entry.get("model")
    task = entry.get("task")
    seed = entry.get("seed")
    if not (isinstance(model, str) and isinstance(task, str)
            and isinstance(seed, int)):
        return None
    error = entry.get("error")
    output_dir = entry.get("output_dir")
    return FailureRow(
        model=model,
        task=task,
        seed=seed,
        error=error if isinstance(error, str) else "",
        output_dir=output_dir if isinstance(output_dir, str) else "",
    )


def failures_view(root) -> tuple[FailureRow, ...]:
    """The failure list (MON-03): sweep_failures.json once the manifest
    is present (authoritative — the file lands at sweep end), else the
    records with status failed (the LIVE source while running: each
    lands as its cell fails — O3)."""
    root_path = Path(root)
    manifest = load_manifest(root_path / MANIFEST_NAME)
    rows: list[FailureRow] = []
    if manifest is not None:
        for entry in load_failures(root_path / FAILURES_NAME) or []:
            if isinstance(entry, dict):
                row = _failure_row(entry)
                if row is not None:
                    rows.append(row)
    else:
        for record in _collect_records(root_path):
            if record.get("status") != CELL_FAILED:
                continue
            row = _failure_row(record)
            if row is not None:
                rows.append(row)
    return tuple(sorted(rows, key=lambda row: (row.model, row.task, row.seed)))


def rerun_lane(root) -> tuple[str, str]:
    """WR-01 (phase-11 review): the ``(peft, config_variant)`` lane the
    [r] re-run must carry — recovered from the SOURCE sweep's own
    artifacts, never a silent none/none default (which would enumerate
    and re-train the BASE cells of the failed pairs while the confirmed
    alias cells are never re-attempted — a different experiment than
    the one the operator confirmed, landing in the same root).

    ``config_variant`` derives from the manifest's merged per-cell
    ``config_variant`` sweep flag (present exactly when the source
    sweep ran a variant — and the ONLY source that catches ``head``,
    which keeps BASE names for the frozen pair). ``peft`` derives from
    the failures entries' alias/base pair: the entry ``model`` equals
    ``base_model + "+{mode}"`` (legacy entries without ``base_model``
    fall back to the alias suffix alone). Tolerant throughout:
    unreadable/missing artifacts and shape-invalid values derive the
    honest ``("none", "none")``.

    Args:
        root: the source sweep's output root.

    Returns:
        tuple[str, str]: ``(peft, config_variant)`` over the
        ``run_config.PEFT_MODES`` / ``CONFIG_VARIANTS`` vocabularies.
    """
    root_path = Path(root)
    config_variant = "none"
    for cell in _manifest_cells(load_manifest(root_path / MANIFEST_NAME)):
        value = (
            cell.get("config_variant") if isinstance(cell, dict) else None)
        if (isinstance(value, str)
                and value in run_config.CONFIG_VARIANTS
                and value != "none"):
            config_variant = value
            break
    peft = "none"
    for entry in load_failures(root_path / FAILURES_NAME) or []:
        if not isinstance(entry, dict):
            continue
        model = entry.get("model")
        if not isinstance(model, str) or not model:
            continue
        base = entry.get("base_model")
        has_base = isinstance(base, str) and bool(base)
        reference = base if has_base else model
        for mode in run_config.PEFT_MODES:
            if mode == "none":
                continue
            suffixed = f"+{mode}"
            if model == reference + suffixed or (
                    not has_base and model.endswith(suffixed)):
                peft = mode
                break
        if peft != "none":
            break
    return (peft, config_variant)


def read_log_tail(path, max_lines=200, max_bytes=65536):
    """Bounded seek-from-end tail (MON-04): the last ``max_lines`` lines
    of the final ``max_bytes`` window, decode errors replaced, the
    window's leading partial line dropped; None when the file is
    absent/unreadable (the screen renders the designed unavailable
    state, never a fabricated empty log)."""
    file_path = Path(path)
    try:
        size = file_path.stat().st_size
        with file_path.open("rb") as handle:
            start = max(0, size - max_bytes)
            handle.seek(start)
            raw = handle.read(size - start)
    except OSError:
        return None
    lines = raw.decode("utf-8", errors="replace").splitlines()
    if start > 0 and lines:
        lines = lines[1:]  # the window's leading partial line
    return tuple(lines[-max_lines:])
