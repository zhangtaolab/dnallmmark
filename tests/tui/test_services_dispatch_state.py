"""
Unit suite for tui/services/dispatch_state.py (Phase 16, 16-02, TUI-03).

Pins the tolerant frozen-v2 reader over FIXTURE FILES (the
test_services_sweep_monitor fixture/tolerance family): every snapshot
is an inline-written JSON string under tmp_path, so the suite stays
machine-independent — the real preserved smoke artifact
``pipeline/finetuned-smoke-r2/dispatch_state.json`` was consulted as a
READ-ONLY shape reference while authoring the fixtures (its 2-worker
drained shape grounds the fresh fixture), never as a dependency.

Behaviors (the plan's eight):
1. fresh v2 snapshot -> a fully populated DispatchStateView (1:1);
2. absent file -> None (the artifact_loader None sentinel);
3. damaged JSON (truncated / empty) -> None — never an exception;
4. missing-field tolerance -> None defaults, never a crash;
5. stale mtime -> the reader's freshness projection flags it (the
   now seam is injectable);
6. a parseable snapshot breaking the schema's SNAPSHOT INVARIANT ->
   the malformed honesty flag, counts carried VERBATIM (never
   reconciled);
7. an unrecognized status string -> parsed verbatim (the passthrough
   rule);
8. import purity -> importing the module pulls in neither textual nor
   pipeline.dispatch_core (fresh -I subprocess, the D-05 discipline).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from tui.services.dispatch_state import (
    DISPATCH_STALE_SECONDS,
    DispatchCellKey,
    DispatchCounts,
    DispatchFailure,
    DispatchWorker,
    read_dispatch_state,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

#: The fresh fixture — the frozen v2 schema 1:1 (status running, one
#: busy worker with a curve-null cellKey, one idle worker, one failure).
#: INVARIANT holds by construction: 9 + 1 + 1 + 0 + 1 busy == 12 total.
_FRESH_SNAPSHOT = {
    "schema_version": 2,
    "mode": "dispatch",
    "run_id": "7759c2cc05364ebdacd2c6a5fa614bac",
    "status": "running",
    "started_at": "2026-10-20T15:20:00.599463+00:00",
    "updated_at": "2026-10-20T15:21:10.516265+00:00",
    "counts": {"total": 12, "completed": 9, "failed": 1, "skipped": 1},
    "queue_depth": 0,
    "workers": [
        {
            "index": 0,
            "gpu": "0",
            "in_flight": {
                "model": "plant-dnabert-6mer",
                "task": "iDNA_ABF_datasets__5mC",
                "seed": 42,
                "fraction": None,
            },
            "cells": 3,
            "completed": 2,
            "failed": 1,
        },
        {
            "index": 1,
            "gpu": "1",
            "in_flight": None,
            "cells": 3,
            "completed": 2,
            "failed": 0,
        },
    ],
    "failures": [
        {
            "model": "plant-dnamamba-6mer",
            "task": "GUE__emp_H3",
            "seed": 43,
            "fraction": None,
            "finished_at": "2026-10-20T15:21:00+00:00",
        }
    ],
}


def _write_root(tmp_path, doc, mtime=None, name="finetuned-dispatch"):
    """Write one fixture snapshot under a fresh sweep root; returns the
    root (the read entry point takes the ROOT, joining the state file
    name itself)."""
    root = tmp_path / name
    root.mkdir(parents=True)
    path = root / "dispatch_state.json"
    if isinstance(doc, str):
        path.write_text(doc, encoding="utf-8")
    else:
        path.write_text(json.dumps(doc, indent=4), encoding="utf-8")
    if mtime is not None:
        os.utime(path, (mtime, mtime))
    return root


# =====================================================================
# 1 — the fresh snapshot parses 1:1
# =====================================================================


def test_fresh_snapshot_parses_into_a_fully_populated_view(tmp_path):
    """A fixture matching the frozen v2 schema populates every field
    1:1 — run_id/status/timestamps, the counts sub-view, queue depth,
    both worker lanes (busy in_flight cellKey + idle null), the failure
    row, and state_mtime from the FILE's mtime — with stale and
    malformed both False (fresh mtime, invariant holds)."""
    mtime = 1790000000.0
    root = _write_root(tmp_path, _FRESH_SNAPSHOT, mtime=mtime)
    view = read_dispatch_state(root, now=lambda: mtime + 5.0)
    assert view is not None
    assert view.run_id == "7759c2cc05364ebdacd2c6a5fa614bac"
    assert view.status == "running"
    assert view.started_at == "2026-10-20T15:20:00.599463+00:00"
    assert view.updated_at == "2026-10-20T15:21:10.516265+00:00"
    assert view.counts == DispatchCounts(
        total=12, completed=9, failed=1, skipped=1)
    assert view.queue_depth == 0
    assert len(view.workers) == 2
    busy, idle = view.workers
    assert isinstance(busy, DispatchWorker)
    assert (busy.index, busy.gpu, busy.cells, busy.completed,
            busy.failed) == (0, "0", 3, 2, 1)
    assert busy.in_flight == DispatchCellKey(
        model="plant-dnabert-6mer", task="iDNA_ABF_datasets__5mC",
        seed=42, fraction=None)
    assert (idle.index, idle.gpu, idle.in_flight) == (1, "1", None)
    assert len(view.failures) == 1
    assert isinstance(view.failures[0], DispatchFailure)
    assert (view.failures[0].model, view.failures[0].seed,
            view.failures[0].finished_at) == (
        "plant-dnamamba-6mer", 43, "2026-10-20T15:21:00+00:00")
    assert view.state_mtime == mtime, "state_mtime derives from the file"
    assert view.stale is False
    assert view.malformed is False
    assert view.stale_age_s == 5


# =====================================================================
# 2/3 — absent and damaged both read None (the None sentinel)
# =====================================================================


def test_absent_state_file_reads_none(tmp_path):
    """A root WITHOUT dispatch_state.json reads None — no exception, no
    block downstream (the static/CLI sweep root and the -mgpu-w* worker
    root stay byte-identical, UI-SPEC B rule 5)."""
    root = tmp_path / "plain-static-root"
    root.mkdir()
    assert read_dispatch_state(root) is None


def test_damaged_state_file_reads_none(tmp_path):
    """A truncated file and an EMPTY file both read None (the
    artifact_loader None sentinel — a cache miss, never a crash)."""
    truncated = _write_root(
        tmp_path, '{"run_id": "abc", "counts": {"to', name="truncated")
    assert read_dispatch_state(truncated) is None
    empty = _write_root(tmp_path, "", name="empty")
    assert read_dispatch_state(empty) is None


def test_non_object_json_reads_none(tmp_path):
    """A parseable-but-non-object document (a bare list — worse than
    damaged: json.loads succeeds) also reads None: the reader builds
    views only from the frozen v2 OBJECT shape."""
    scalar = _write_root(tmp_path, json.dumps([1, 2, 3]), name="scalar")
    assert read_dispatch_state(scalar) is None


# =====================================================================
# 4 — missing-field tolerance (the CONTEXT discretion ruling)
# =====================================================================


def test_missing_optional_keys_parse_with_none_defaults(tmp_path):
    """A snapshot omitting ``failures`` entirely and carrying a worker
    without ``cells`` still parses — absent optional keys degrade to
    None/empty, NEVER a crash (the frozen-schema superset ruling)."""
    doc = json.loads(json.dumps(_FRESH_SNAPSHOT))
    del doc["failures"]
    del doc["workers"][1]["cells"]
    del doc["workers"][0]["completed"]
    root = _write_root(tmp_path, doc, mtime=1790000000.0)
    view = read_dispatch_state(root, now=lambda: 1790000000.5)
    assert view is not None
    assert view.failures == ()
    assert view.workers[1].cells is None
    assert view.workers[0].completed is None
    # the invariant stays evaluable over the legs that remain (the
    # worker counters are NOT invariant legs) — no false malformed
    assert view.malformed is False


# =====================================================================
# 5 — staleness (D16-08, the pinned cell-scale grace — WR-02)
# =====================================================================


def test_stale_mtime_is_flagged_by_the_injectable_now(tmp_path):
    """A file mtime older than DISPATCH_STALE_SECONDS flags stale, with
    the integer age riding the view; a fresh mtime does not — the
    freshness projection derives from the INJECTABLE now, never from a
    mutated wall clock. WR-02 (phase-16 review): the grace is pinned at
    CELL SCALE (3600s) because the writer publishes only at state
    transitions — one claim-to-finalize cell (minutes to hours) is the
    longest quiet window a HEALTHY run shows, and the original 60s
    false-positived the marker onto every healthy run (ages inside one
    cell therefore stay fresh)."""
    mtime = 1790000000.0
    root = _write_root(tmp_path, _FRESH_SNAPSHOT, mtime=mtime)
    stale_view = read_dispatch_state(root, now=lambda: mtime + 3700.0)
    assert stale_view is not None
    assert stale_view.stale is True
    assert stale_view.stale_age_s == 3700
    fresh_view = read_dispatch_state(root, now=lambda: mtime + 120.0)
    assert fresh_view is not None
    assert fresh_view.stale is False, (
        "120s sits INSIDE one healthy cell window — never stale at "
        "cell-scale grace (the WR-02 false-positive, pinned fresh)"
    )
    # the pinned constant is the single threshold home (D16-08/WR-02)
    assert DISPATCH_STALE_SECONDS == 3600.0


# =====================================================================
# 6 — the snapshot-invariant honesty check (never reconcile)
# =====================================================================


def test_invariant_violation_marks_malformed_without_repair(tmp_path):
    """A parseable snapshot whose counts break the schema's documented
    SNAPSHOT INVARIANT (completed + failed + skipped + queue_depth +
    active workers == total) carries malformed=True — while the counts
    ride the view VERBATIM (TUI orchestrates, never computes: the
    reader never recomputes queue depth or repairs a count)."""
    doc = json.loads(json.dumps(_FRESH_SNAPSHOT))
    doc["counts"]["completed"] = 8  # 8 + 1 + 1 + 0 + 1 == 11 != 12
    root = _write_root(tmp_path, doc, mtime=1790000000.0)
    view = read_dispatch_state(root, now=lambda: 1790000000.5)
    assert view is not None
    assert view.malformed is True
    assert view.counts == DispatchCounts(
        total=12, completed=8, failed=1, skipped=1), (
        "the counts ride verbatim — never reconciled")
    assert view.queue_depth == 0, "queue depth is NEVER recomputed"
    assert view.stale is False, "malformed is orthogonal to staleness"


def test_unevaluable_invariant_is_not_malformed(tmp_path):
    """An invariant whose legs are MISSING (no counts object) is
    tolerance, not a provable violation — malformed stays False (the
    honesty check never guesses a verdict it cannot evaluate)."""
    doc = json.loads(json.dumps(_FRESH_SNAPSHOT))
    del doc["counts"]
    root = _write_root(tmp_path, doc, mtime=1790000000.0)
    view = read_dispatch_state(root, now=lambda: 1790000000.5)
    assert view is not None
    assert view.counts is None
    assert view.malformed is False


# =====================================================================
# 7 — unrecognized status parses verbatim (the passthrough rule)
# =====================================================================


def test_unrecognized_status_string_parses_verbatim(tmp_path):
    """A status outside the schema enum (running/done/incomplete)
    parses into the view UNTRANSLATED — the screen renders the raw
    string (honest passthrough, never a fabricated vocabulary word)."""
    doc = json.loads(json.dumps(_FRESH_SNAPSHOT))
    doc["status"] = "pausing"
    root = _write_root(tmp_path, doc, mtime=1790000000.0)
    view = read_dispatch_state(root, now=lambda: 1790000000.5)
    assert view is not None
    assert view.status == "pausing"


def test_missing_status_degrades_to_none(tmp_path):
    """A snapshot without a status key degrades the field to None —
    the tolerance path again (the screen renders the honest dash)."""
    doc = json.loads(json.dumps(_FRESH_SNAPSHOT))
    del doc["status"]
    root = _write_root(tmp_path, doc, mtime=1790000000.0)
    view = read_dispatch_state(root, now=lambda: 1790000000.5)
    assert view is not None
    assert view.status is None


# =====================================================================
# 8 — import purity (D16-07 — the fresh -I subprocess discipline)
# =====================================================================


def test_importing_the_reader_pulls_in_neither_textual_nor_dispatch_core():
    """D16-07 in a FRESH interpreter: importing the reader leaves
    textual and pipeline.dispatch_core absent from sys.modules (the
    services-tier textual-free invariant + the zero-dispatch_core
    import rule — the subprocess is mandatory because the SUITE's own
    process legitimately holds both by this point)."""
    probe = (
        "import sys\n"
        f"sys.path.insert(0, {str(REPO_ROOT / 'pipeline')!r})\n"
        f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
        "import tui.services.dispatch_state\n"
        "assert 'artifact_loader' in sys.modules, 'the reuse ruling'\n"
        "for banned in ('textual', 'dispatch_core'):\n"
        "    assert banned not in sys.modules, banned\n"
        "print('pure')\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", probe],
        capture_output=True, text=True, cwd=REPO_ROOT, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "pure"
