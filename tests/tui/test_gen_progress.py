# =====================================================================
# tests/tui/test_gen_progress.py — golden-JSON tests for the offline
# web-mirror generator (12-02, WEB-01)
#
# Lives under tests/tui/ for the repo-root conftest (the ``tui``
# package-qualified import); ``gen_progress`` itself is importable via
# the script/ root the parent tests/conftest.py inserts.
#
# Pinned behaviors (the frozen 12-UI-SPEC data contract):
#   - scanner dataclass field names VERBATIM (SweepStats/SweepSummary/
#     CurrentCell/EtaEstimate/CellRow/CellSeed); newest_mtime ABSENT;
#   - state_counts = the five cell states derived from the cells pass;
#   - null total/current/elapsed pass through as null (honesty rules);
#   - fraction_states pairs pass through (curve cells);
#   - byte-stable regeneration under a pinned clock;
#   - generated_at follows the injected clock, ISO-8601 UTC, Z-suffixed;
#   - argv-order multi-root emission, root rendered as the final path
#     component (worker roots read ``finetuned-mgpu-w0``);
#   - per-root tolerance: empty/missing roots print one [Skip] line and
#     are absent from the JSON; a truncated record degrades (the
#     scanner's tolerant readers), main still exits 0;
#   - no positional roots -> the scanner's DEFAULT_OUTPUT_ROOTS.
#
# Clock determinism (every fixture tree is REAL, under tmp_path):
#   - full_scan/stats get the injected ``now``, pinned one minute AHEAD
#     of the real clock (whole seconds), so fresh fixtures classify
#     running and back-dated fixtures classify artifacts_only on any
#     host date;
#   - record started_at/finished_at stamps derive from the pinned now,
#     so elapsed/ETA values are exact floats;
#   - cells_view reads the real clock internally (no now= seam) — every
#     non-record cell is made mtime-deterministic instead (a runs/ churn
#     marker -> running; a back-dated empty dir -> queued).
# =====================================================================

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

import gen_progress

from tui.services import sweep_monitor

# ===== Fixture helpers =====


def _pinned_now() -> float:
    """One minute ahead of the real clock, whole seconds (exact float
    round-trips through the ISO stamps; +60s keeps freshly written
    fixtures INSIDE the scanner's 600s stale-grace — running — while
    the backdated ones stay outside — artifacts_only)."""
    return float(int(time.time() + 60))


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=UTC).isoformat()


def _write_json(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")


def _record(root: Path, model: str, task: str, seed: int, status: str,
            started: float, finished: float) -> Path:
    """Write one run_record.json cell; returns the seed dir."""
    seed_dir = root / model / task / f"seed_{seed}"
    _write_json(seed_dir / "run_record.json", {
        "model": model, "task": task, "seed": seed, "status": status,
        "started_at": _iso(started), "finished_at": _iso(finished),
    })
    return seed_dir


def _backdate(path: Path, age: float = 100000.0) -> None:
    """Push a path's mtime far outside the scanner's stale grace."""
    stamp = time.time() - age
    os.utime(path, (stamp, stamp))


def _finished_root(base: Path, now: float) -> Path:
    """A finished sweep: manifest + completed/failed/skipped records."""
    root = base / "finetuned-alpha"
    _record(root, "model-a", "GUE__emp_H3", 42, "completed",
            now - 7200, now - 6600)
    _record(root, "model-a", "GUE__emp_H3", 43, "failed",
            now - 6600, now - 6300)
    _record(root, "model-b", "mouse__DMS", 42, "skipped",
            now - 6000, now - 6000)
    _write_json(root / "sweep_manifest.json", {"cells": [
        {"model": "model-a", "task": "GUE__emp_H3", "seed": 42,
         "status": "completed"},
        {"model": "model-a", "task": "GUE__emp_H3", "seed": 43,
         "status": "failed"},
        {"model": "model-b", "task": "mouse__DMS", "seed": 42,
         "status": "skipped"},
    ]})
    return root


def _running_root(base: Path, now: float, name: str = "finetuned-mgpu-w0",
                  model: str = "model-c") -> Path:
    """A running sweep: one completed record + one churn-marked cell,
    no manifest (a CLI-launched worker root mid-sweep)."""
    root = base / name
    _record(root, model, "GUE__emp_H3", 42, "completed", now - 1800,
            now - 1200)
    (root / model / "GUE__emp_H3" / "seed_43" / "runs").mkdir(
        parents=True)
    return root


def _artifacts_root(base: Path, now: float) -> Path:
    """A prior-run artifacts root: records only, mtimes far stale."""
    root = base / "seed-9527-artifacts"
    seed_dir = _record(root, "model-d", "mouse__DMS", 42, "completed",
                       now - 3600, now - 3300)
    _backdate(seed_dir / "run_record.json")
    return root


def _run(roots, output: Path, now: float) -> dict:
    """main() over the fixture roots; returns the parsed output JSON."""
    argv = [str(root) for root in roots] + ["--output", str(output)]
    assert gen_progress.main(argv, now=now) == 0
    return json.loads(output.read_text(encoding="utf-8"))


# =====================================================================
# The golden contract
# =====================================================================


def test_golden_contract_over_three_root_kinds(tmp_path, capsys):
    """The exact parsed JSON over finished + running + artifacts roots —
    frozen field names, argv-order sweeps, dropped newest_mtime."""
    now = _pinned_now()
    running = _running_root(tmp_path, now)
    finished = _finished_root(tmp_path, now)
    artifacts = _artifacts_root(tmp_path, now)
    out = tmp_path / "sweep.json"

    doc = _run([running, finished, artifacts], out, now)

    assert doc == {
        "version": 1,
        "generated_at": gen_progress._utc_stamp(now),
        "sweeps": [
            {
                "root": "finetuned-mgpu-w0",
                "state": "running",
                "done": 1,
                "total": None,
                "elapsed_seconds": 1800.0,
                "current": {"model": "model-c", "task": "GUE__emp_H3",
                            "seed": 42},
                "eta": {"mode": "none", "point_seconds": None,
                        "lo_seconds": None, "hi_seconds": None},
                "state_counts": {"completed": 1, "failed": 0, "queued": 0,
                                 "running": 1, "skipped": 0},
                "cells": [{
                    "model": "model-c", "task": "GUE__emp_H3",
                    "seeds": [
                        {"seed": 42, "state": "completed",
                         "fraction_states": None},
                        {"seed": 43, "state": "running",
                         "fraction_states": None},
                    ],
                }],
            },
            {
                "root": "finetuned-alpha",
                "state": "finished",
                "done": 3,
                "total": 3,
                "elapsed_seconds": 7200.0,
                "current": {"model": "model-b", "task": "mouse__DMS",
                            "seed": 42},
                "eta": {"mode": "none", "point_seconds": None,
                        "lo_seconds": None, "hi_seconds": None},
                "state_counts": {"completed": 1, "failed": 1, "queued": 0,
                                 "running": 0, "skipped": 1},
                "cells": [
                    {
                        "model": "model-a", "task": "GUE__emp_H3",
                        "seeds": [
                            {"seed": 42, "state": "completed",
                             "fraction_states": None},
                            {"seed": 43, "state": "failed",
                             "fraction_states": None},
                        ],
                    },
                    {
                        "model": "model-b", "task": "mouse__DMS",
                        "seeds": [
                            {"seed": 42, "state": "skipped",
                             "fraction_states": None},
                        ],
                    },
                ],
            },
            {
                "root": "seed-9527-artifacts",
                "state": "artifacts_only",
                "done": 1,
                "total": None,
                "elapsed_seconds": 3600.0,
                "current": {"model": "model-d", "task": "mouse__DMS",
                            "seed": 42},
                "eta": {"mode": "none", "point_seconds": None,
                        "lo_seconds": None, "hi_seconds": None},
                "state_counts": {"completed": 1, "failed": 0, "queued": 0,
                                 "running": 0, "skipped": 0},
                "cells": [{
                    "model": "model-d", "task": "mouse__DMS",
                    "seeds": [
                        {"seed": 42, "state": "completed",
                         "fraction_states": None},
                    ],
                }],
            },
        ],
    }
    # The checker-ratified omission, pinned explicitly on the raw text.
    assert "newest_mtime" not in out.read_text(encoding="utf-8")
    assert "✅" in capsys.readouterr().out


# =====================================================================
# Determinism + the clock seam
# =====================================================================


def test_byte_stable_regeneration_under_pinned_clock(tmp_path):
    """Same roots + same pinned now -> byte-identical JSON."""
    now = _pinned_now()
    finished = _finished_root(tmp_path, now)
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"

    assert gen_progress.main([str(finished), "--output", str(first)],
                             now=now) == 0
    assert gen_progress.main([str(finished), "--output", str(second)],
                             now=now) == 0
    assert first.read_bytes() == second.read_bytes()


def test_generated_at_follows_injected_clock(tmp_path):
    """generated_at is the injected clock's ISO-8601 UTC stamp — never a
    live read when now is pinned (classification-independent: a finished
    root ignores the clock entirely)."""
    epoch = datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC).timestamp()
    finished = _finished_root(tmp_path, epoch)
    out = tmp_path / "sweep.json"

    doc = _run([finished], out, epoch)

    assert doc["generated_at"] == "2026-10-13T12:00:00Z"
    assert gen_progress._utc_stamp(0.0) == "1970-01-01T00:00:00Z"


# =====================================================================
# Multi-root + defaults + tolerance
# =====================================================================


def test_multi_worker_roots_render_final_component_in_argv_order(
        tmp_path):
    """One sweep entry per worker root, root = final path component,
    sweeps ordered by argv (not by the scanner's sorted output)."""
    now = _pinned_now()
    w0 = _running_root(tmp_path, now, name="finetuned-mgpu-w0",
                       model="model-c")
    w1 = _running_root(tmp_path, now, name="finetuned-mgpu-w1",
                       model="model-f")
    out = tmp_path / "sweep.json"

    doc = _run([w1, w0], out, now)  # argv order deliberately unsorted

    assert [sweep["root"] for sweep in doc["sweeps"]] == [
        "finetuned-mgpu-w1", "finetuned-mgpu-w0"]
    assert len(doc["sweeps"]) == 2


def test_no_positional_roots_default_to_scanner_defaults(
        tmp_path, monkeypatch):
    """No positional args -> sweep_monitor.DEFAULT_OUTPUT_ROOTS."""
    now = _pinned_now()
    default_root = tmp_path / "finetuned-default"
    _record(default_root, "model-z", "mouse__DMS", 7, "completed",
            now - 600, now - 300)
    monkeypatch.setattr(sweep_monitor, "DEFAULT_OUTPUT_ROOTS",
                        (default_root,))
    out = tmp_path / "sweep.json"

    doc = _run([], out, now)

    assert [sweep["root"] for sweep in doc["sweeps"]] == [
        "finetuned-default"]


def test_empty_and_missing_roots_are_skipped(tmp_path, capsys):
    """A root with no artifacts prints one [Skip] line and is absent
    from the JSON; the run still succeeds with an empty sweeps list."""
    now = _pinned_now()
    empty = tmp_path / "empty-root"
    empty.mkdir()
    missing = tmp_path / "does-not-exist"
    out = tmp_path / "sweep.json"

    assert gen_progress.main(
        [str(empty), str(missing), "--output", str(out)], now=now) == 0

    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["sweeps"] == []
    assert doc["version"] == 1
    captured = capsys.readouterr().out
    assert captured.count("[Skip]") == 2
    assert "empty-root" in captured
    assert "does-not-exist" in captured
    assert "✅" in captured


def test_truncated_record_degrades_never_crashes(tmp_path):
    """A damaged run_record in an otherwise-good root: the scanner's
    tolerant readers degrade, the good cells survive, main exits 0."""
    now = _pinned_now()
    root = tmp_path / "finetuned-damaged"
    _record(root, "model-x", "GUE__emp_H3", 1, "completed",
            now - 600, now - 300)
    damaged_dir = root / "model-x" / "GUE__emp_H3" / "seed_2"
    damaged_dir.mkdir(parents=True)
    (damaged_dir / "run_record.json").write_text(
        '{"status": "compl', encoding="utf-8")
    out = tmp_path / "sweep.json"

    doc = _run([root], out, now)

    assert len(doc["sweeps"]) == 1
    seeds = {seed["seed"]: seed["state"]
             for seed in doc["sweeps"][0]["cells"][0]["seeds"]}
    assert seeds[1] == "completed"


# =====================================================================
# Curve cells
# =====================================================================


def test_curve_seed_renders_fraction_states_pairs(tmp_path):
    """A seed dir with frac_* children carries fraction_states pairs and
    folds to the seed state (the scanner's fold rules)."""
    now = _pinned_now()
    root = tmp_path / "finetuned-curve"
    seed_dir = root / "model-e" / "GUE__emp_H3" / "seed_44"
    _write_json(seed_dir / "frac_0.5" / "run_record.json", {
        "model": "model-e", "task": "GUE__emp_H3", "seed": 44,
        "status": "completed",
        "started_at": _iso(now - 600), "finished_at": _iso(now - 300),
    })
    frac_rest = seed_dir / "frac_0.7"
    frac_rest.mkdir(parents=True)
    _backdate(frac_rest)  # queued: no record, no activity (stale mtime)
    _backdate(seed_dir)  # the plain seed below stays the frontier cell
    _record(root, "model-e", "GUE__emp_H3", 45, "completed",
            now - 600, now - 300)
    out = tmp_path / "sweep.json"

    doc = _run([root], out, now)

    row = doc["sweeps"][0]["cells"][0]
    assert row["model"] == "model-e"
    assert row["seeds"][0] == {
        "seed": 44, "state": "queued",
        "fraction_states": [["frac_0.5", "completed"],
                            ["frac_0.7", "queued"]],
    }
    assert row["seeds"][1]["seed"] == 45
    assert row["seeds"][1]["state"] == "completed"
    assert doc["sweeps"][0]["state_counts"]["queued"] == 1
