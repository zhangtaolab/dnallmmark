"""
dispatch_state — the tolerant frozen-v2 ``dispatch_state.json`` reader
(Phase 16, 16-02, TUI-03, D16-06/D16-07/D16-08).

The dispatch-half of the slot-5 scanner data sources: it reads the
run-level state file ``pipeline/dispatch_core.py`` writes atomically at
every state transition (mode evidence, skip filter, claim, finalize,
containment, terminal statuses) against the FROZEN v2 contract
(``schemas/dispatch_state.json``, D14-01/D14-04) and projects it into
frozen :class:`DispatchStateView` dataclasses. The screen owns cadence
and rendering — this module is a pure tolerant read (the scanner's
declaration).

Contract (locked decisions):

- D16-06: the view is a frozen-schema SUPERSET, missing-field
  TOLERANT — absent optional keys degrade to None, never a crash (the
  CONTEXT discretion ruling); field names map 1:1 to the schema.
- D16-07: ZERO textual imports (the services-tier invariant,
  ``tests/tui/test_import_lock.py`` — the glob covers this module
  automatically) and ZERO ``pipeline.dispatch_core`` imports — the
  schema FILE is the contract, never the writer module. Parsing is
  stdlib ``json`` only, through ``artifact_loader``'s None sentinel
  (the env_check/load_cached precedent — never ``eval``, never a
  re-implementation of the loader's tolerance).
- D16-08: :data:`DISPATCH_STALE_SECONDS` is THE single stale-threshold
  home — a pinned, documented-tunable module constant (the
  ``STALE_GRACE_SECONDS`` precedent); the view carries ``state_mtime``
  plus the reader-derived ``stale``/``stale_age_s`` so the screen
  renders the ``MON_DISPATCH_STALE`` marker over last-known-good rows.

NEVER-RECONCILE RULE (UI-SPEC B rule 6, the TUI-orchestrates-never-
computes law): the reader NEVER recomputes queue depth and never
repairs inconsistent counts. A parseable snapshot violating the
schema's documented SNAPSHOT INVARIANT (``completed + failed +
skipped + queue_depth + active workers == total``, the schema
``$comment``) simply carries ``malformed=True`` — the screen renders
the warning marker over the VERBATIM values.

Dependencies: stdlib ``json`` (via artifact_loader) / ``dataclasses``
/ ``pathlib`` / ``time`` only.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import artifact_loader  # top-level module (pipeline/ sys.path root, D-19)

#: The state file name — ONE naming authority: this is the file
#: ``pipeline/dispatch_core.py`` writes (``DISPATCH_STATE_NAME``, the
#: Phase-14 frozen naming); pinned here as a literal sibling constant
#: precisely so this reader imports ZERO dispatch_core (D16-07).
DISPATCH_STATE_FILE_NAME = "dispatch_state.json"

#: D16-08 pin — dispatch-state staleness grace in SECONDS, tuned to
#: CELL SCALE (WR-02, phase-16 review). The writer
#: (``dispatch_core._publish_state``) rewrites ``dispatch_state.json``
#: ONLY at state transitions — pre-drain, claim, finalize/failure,
#: containment, terminal — with NO heartbeat/timer loop, so a healthy
#: run's longest quiet window is ONE FULL FINE-TUNING CELL
#: (claim -> finalize: minutes to hours). A grace below cell scale
#: false-positives the MON_DISPATCH_STALE marker onto every healthy
#: run (the original 60.0 shipped exactly that defect — a near-
#: permanent warning destroys the signal it was built for); 3600.0
#: sits at the cell scale the writer actually writes at. A TERMINAL
#: file (done/incomplete) is never rewritten — its age grows by design
#: and eventually crosses the grace; the marker on a long-finished
#: run is cosmetic (the last-known-good rows stay verbatim).
#: MAINTAINER-TUNABLE (the STALE_GRACE_SECONDS = 600.0 precedent,
#: tui/services/sweep_monitor.py): raise it for slower cell mixes,
#: never below the longest expected claim-to-finalize window.
DISPATCH_STALE_SECONDS = 3600.0

#: The now seam's shape: ``() -> float`` (epoch seconds — time.time's
#: contract). Injectable so tests pin the freshness projection without
#: mutating file mtimes (the plan's Test-5 shape).
NowFn = Callable[[], float]


# ===== The view model (frozen — DATA, never screen copy) =====


@dataclass(frozen=True)
class DispatchCellKey:
    """One in-flight cell identity (the schema's ``$defs.cellKey``):
    ``fraction`` is None for plain (non-curve) cells."""

    model: "str | None"
    task: "str | None"
    seed: "int | None"
    fraction: "float | None"


@dataclass(frozen=True)
class DispatchCounts:
    """The run's counters (the schema's ``counts`` object) — VERBATIM
    values, never reconciled (the never-recompute rule)."""

    total: "int | None"
    completed: "int | None"
    failed: "int | None"
    skipped: "int | None"


@dataclass(frozen=True)
class DispatchWorker:
    """One dispatch worker lane (the schema's ``workers[]`` entries):
    ``in_flight`` is the claimed cellKey or None (idle)."""

    index: "int | None"
    gpu: "str | None"
    in_flight: "DispatchCellKey | None"
    cells: "int | None"
    completed: "int | None"
    failed: "int | None"


@dataclass(frozen=True)
class DispatchFailure:
    """One failed cell of the CURRENT run (the schema's bounded
    ``failures[]`` — fresh run_id per launch)."""

    model: "str | None"
    task: "str | None"
    seed: "int | None"
    fraction: "float | None"
    finished_at: "str | None"


@dataclass(frozen=True)
class DispatchStateView:
    """The tolerant frozen-v2 projection one dispatch root renders.

    Every value rides VERBATIM from the file (status passthrough
    included — unrecognized strings render raw downstream, never
    translated); ``state_mtime`` derives from the file; ``stale`` /
    ``stale_age_s`` are the reader's freshness projection at read time
    (D16-08); ``malformed`` is the snapshot-invariant honesty flag —
    set on mismatch, NEVER accompanied by a repaired value.
    """

    run_id: "str | None"
    status: "str | None"
    started_at: "str | None"
    updated_at: "str | None"
    counts: "DispatchCounts | None"
    queue_depth: "int | None"
    workers: "tuple[DispatchWorker, ...]" = ()
    failures: "tuple[DispatchFailure, ...]" = ()
    state_mtime: float = 0.0
    stale: bool = False
    malformed: bool = False
    stale_age_s: int = 0


# ===== per-field tolerance helpers (type-narrowing only) =====


def _as_int(value) -> "int | None":
    """int or None — bool is excluded (Python's bool-is-int trap)."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _as_str(value) -> "str | None":
    return value if isinstance(value, str) else None


def _as_float(value) -> "float | None":
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _parse_cell_key(doc) -> "DispatchCellKey | None":
    """One in_flight cellKey; a non-object value is unparseable (None
    rides the worker as its busy identity being absent — tolerant,
    never a crash)."""
    if not isinstance(doc, dict):
        return None
    return DispatchCellKey(
        model=_as_str(doc.get("model")),
        task=_as_str(doc.get("task")),
        seed=_as_int(doc.get("seed")),
        fraction=_as_float(doc.get("fraction")))


def _parse_worker(doc) -> "DispatchWorker | None":
    """One workers[] entry; non-object entries are skipped by the
    caller (tolerance — the worker count the screen renders is the
    count that parsed)."""
    if not isinstance(doc, dict):
        return None
    in_flight_doc = doc.get("in_flight")
    return DispatchWorker(
        index=_as_int(doc.get("index")),
        gpu=_as_str(doc.get("gpu")),
        in_flight=(None if in_flight_doc is None
                   else _parse_cell_key(in_flight_doc)),
        cells=_as_int(doc.get("cells")),
        completed=_as_int(doc.get("completed")),
        failed=_as_int(doc.get("failed")))


def _parse_failure(doc) -> "DispatchFailure | None":
    """One failures[] entry; non-object entries are skipped."""
    if not isinstance(doc, dict):
        return None
    return DispatchFailure(
        model=_as_str(doc.get("model")),
        task=_as_str(doc.get("task")),
        seed=_as_int(doc.get("seed")),
        fraction=_as_float(doc.get("fraction")),
        finished_at=_as_str(doc.get("finished_at")))


def _invariant_broken(counts: "DispatchCounts | None",
                      queue_depth: "int | None",
                      workers: "tuple[DispatchWorker, ...]") -> bool:
    """The schema's SNAPSHOT INVARIANT honesty check (schemas/
    dispatch_state.json ``$comment``): ``completed + failed + skipped +
    queue_depth + (workers with non-null in_flight) == total``.

    Returns True ONLY on a provable mismatch over complete legs — a
    missing leg is tolerance, not a violation (the reader never guesses
    a verdict it cannot evaluate), and a True NEVER triggers a repair:
    the counts ride the view verbatim either way.
    """
    if counts is None:
        return False
    total = counts.total
    completed = counts.completed
    failed = counts.failed
    skipped = counts.skipped
    if (total is None or completed is None or failed is None
            or skipped is None or queue_depth is None):
        return False
    active = sum(1 for worker in workers if worker.in_flight is not None)
    return completed + failed + skipped + queue_depth + active != total


def read_dispatch_state(root, now: "NowFn | None" = None
                        ) -> "DispatchStateView | None":
    """Tolerantly read one sweep root's dispatch state.

    Args:
        root: the sweep ROOT (str or os.PathLike) — the reader joins
            :data:`DISPATCH_STATE_FILE_NAME` itself (the file the
            dispatcher writes at the root; static/worker roots carry
            no such file).
        now: the freshness seam — ``() -> float`` epoch seconds; None
            means the real ``time.time`` (tests inject a fixed moment).

    Returns:
        The frozen :class:`DispatchStateView`, or None when the file
        is missing, unreadable, empty, truncated, or not valid JSON
        (the artifact_loader None sentinel — a cache miss, never a
        crash; the screen renders NO block). A parseable document
        carries its values VERBATIM — the snapshot invariant is CHECKED
        (``malformed``) but never repaired, and queue depth is never
        recomputed client-side.
    """
    if now is None:
        now = time.time
    path = Path(root) / DISPATCH_STATE_FILE_NAME
    doc = artifact_loader.load_json_artifact(path)
    if not isinstance(doc, dict):
        return None
    try:
        state_mtime = path.stat().st_mtime
    except OSError:
        # the file vanished between read and stat — treat as absent
        return None
    counts_doc = doc.get("counts")
    counts = (DispatchCounts(
        total=_as_int(counts_doc.get("total")),
        completed=_as_int(counts_doc.get("completed")),
        failed=_as_int(counts_doc.get("failed")),
        skipped=_as_int(counts_doc.get("skipped")))
        if isinstance(counts_doc, dict) else None)
    queue_depth = _as_int(doc.get("queue_depth"))
    workers_doc = doc.get("workers")
    workers = tuple(worker for worker in (
        _parse_worker(entry)
        for entry in (workers_doc if isinstance(workers_doc, list)
                      else ()))
        if worker is not None)
    failures_doc = doc.get("failures")
    failures = tuple(failure for failure in (
        _parse_failure(entry)
        for entry in (failures_doc if isinstance(failures_doc, list)
                      else ()))
        if failure is not None)
    moment = now()
    age_seconds = moment - state_mtime
    return DispatchStateView(
        run_id=_as_str(doc.get("run_id")),
        status=_as_str(doc.get("status")),
        started_at=_as_str(doc.get("started_at")),
        updated_at=_as_str(doc.get("updated_at")),
        counts=counts,
        queue_depth=queue_depth,
        workers=workers,
        failures=failures,
        state_mtime=state_mtime,
        stale=age_seconds >= DISPATCH_STALE_SECONDS,
        malformed=_invariant_broken(counts, queue_depth, workers),
        stale_age_s=max(0, int(age_seconds)))
