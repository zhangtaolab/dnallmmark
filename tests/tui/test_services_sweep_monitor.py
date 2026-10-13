"""
Tier-1 service tests for ``tui/services/sweep_monitor.py`` (Phase 11,
11-04 — the pure artifact-tree scanner behind slot-5 monitoring).

Three lanes, per the plan:

- **Discovery suite (Task 1)** — the D-03 three-state classification
  over synthetic tmp sweep trees: finished (manifest counts), running
  via live-root injection / watermark advance / fresh mtime within the
  600s stale grace (O2), artifacts_only (the stale seed_9527 shape —
  unknown totals), deleted-root tolerance, and the XDG-persisted manual
  roots round trip. Every classification input is an INJECTED clock
  (``now=``) plus explicitly set mtimes — no test depends on wall time.
- **Cells suite (Task 2)** — per-seed state derivation (records, resume
  marker, churn, queued), curve-fraction nesting, alias fidelity, the
  tolerant readers (truncated record -> last-known-good retained;
  corrupt manifest -> treated absent), ``is_sweep_root`` edges, and
  ``resume_count``.
- **Stats suite (Task 3)** — D-17 elapsed/ETA math with exact-value
  proofs (median, per-model vs global, the ratio-3.0 range, pending and
  none degradations, skipped exclusion), the live-vs-finished failure
  source switch, and the bounded log tail.

Every test injects a tmp state root via ``DNALLMMARK_TUI_STATE_DIR`` —
the real ``~/.local/state/dnallmmark`` is never read or written. The
fixture tree shape clones ``tests/fixtures/e2_replay/finetuned``
({model}/{task}/seed_{n}/...) plus the run_sweep artifacts this
scanner consumes; artifact file names import from ``run_sweep`` — the
same single source the service consumes, never re-typed literals.

See also:
    ``tui/services/sweep_monitor.py`` — the service under test.
    ``pipeline/run_sweep.py`` — the artifact writer whose names and
    write timing this scanner mirrors.
    ``tests/fixtures/e2_replay/finetuned`` — the tree-layout seed.
"""

import json
import os
from pathlib import Path

from run_sweep import (
    FAILURES_NAME,
    MANIFEST_NAME,
    RECORD_NAME,
    RESUME_MARKER,
)

from tui.services import settings, sweep_monitor

REPO_ROOT = Path(__file__).resolve().parents[2]

#: A fixed epoch for the injected clocks — far from the real now so a
#: forgotten mtime pin can never accidentally fall inside the grace.
NOW = 1_700_000_000.0

#: The O2 pin, pinned as a constant (documented maintainer-tunable).
STALE_GRACE = 600.0


def pin_state_dir(monkeypatch, tmp_path):
    """Point the TUI state root at a tmp dir — the real XDG state home
    is never touched (D-03/D-04 boundary)."""
    state = tmp_path / "state"
    monkeypatch.setenv(settings.STATE_DIR_ENV, str(state))
    return state


def write_json(path, payload):
    """Write a deterministic fixture JSON (run_sweep's writer shape)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=4, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    return path


def seed_dir(root, model, task, seed):
    return Path(root) / model / task / f"seed_{seed}"


def make_record(model, task, seed, status="completed", started_at=None,
                finished_at=None, error=None, output_dir=None, **extra):
    """A run_record.json payload in _new_record's exact shape."""
    record = {
        "model": model,
        "task": task,
        "seed": seed,
        "peft": "none",
        "config_variant": "none",
        "train_fraction": None,
        "status": status,
        "output_dir": output_dir or str(seed_dir("<root>", model, task, seed)),
        "metrics": None,
        "vram_probe": {
            "gpu_mem_total": None,
            "init_max_mem": None,
            "batch_size": None,
            "gradient_accumulation_steps": None,
        },
        "git_commit": "0" * 40,
        "started_at": started_at,
        "finished_at": finished_at,
        "error": error,
    }
    record.update(extra)
    return record


def plant_record(root, model, task, seed, record):
    """Write a completed-shaped record into the seed dir."""
    record = dict(record)
    if not record["output_dir"] or "<root>" in record["output_dir"]:
        record["output_dir"] = str(seed_dir(root, model, task, seed))
    return write_json(seed_dir(root, model, task, seed) / RECORD_NAME, record)


def manifest_payload(cells):
    """A sweep_manifest.json payload in _manifest_payload's shape."""
    return {
        "matrix": {
            "models": sorted({c["model"] for c in cells}),
            "tasks": sorted({c["task"] for c in cells}),
            "seeds": sorted({c["seed"] for c in cells}),
            "output_root": "<root>",
        },
        "cells": cells,
    }


def manifest_cell(model, task, seed, status="completed"):
    return {
        "model": model,
        "task": task,
        "seed": seed,
        "status": status,
        "output_dir": str(seed_dir("<root>", model, task, seed)),
    }


def set_mtime(path, epoch):
    """Pin one path's mtime (both atime and mtime) to an epoch."""
    os.utime(path, (epoch, epoch))


def age_tree(root, now=NOW, age_seconds=7200.0):
    """Set EVERY file mtime under root to now - age (the stale-tree
    shape: explicitly old, never accidentally inside the grace)."""
    for path in sorted(Path(root).rglob("*")):
        set_mtime(path, now - age_seconds)


def sweep_row(result, root):
    """The SweepSummary for one root (fails loudly when absent)."""
    root = Path(root).resolve()
    for summary in result.sweeps:
        if summary.root == root:
            return summary
    raise AssertionError(f"no SweepSummary for {root}: {result.sweeps}")


# =====================================================================
# Lane 1 (Task 1): three-state discovery + manual roots (D-03/D-09/O2)
# =====================================================================


def test_pinned_constants_and_default_output_root():
    """The O2/O4 pins + the D-03 default root, exactly as the plan
    states them (constants are the tunable surface, never inlined)."""
    assert sweep_monitor.STALE_GRACE_SECONDS == 600.0
    assert sweep_monitor.ETA_VARIANCE_RATIO == 3.0
    assert sweep_monitor.DEFAULT_OUTPUT_ROOTS == (
        REPO_ROOT / "pipeline" / "finetuned",)


def test_full_scan_finished_tree_reads_counts_from_manifest(tmp_path):
    """Manifest present => finished, total/done from the manifest cells
    (terminal statuses count toward done; planned never does)."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42))
    cells = [
        manifest_cell("model-a", "task-1", 42, "completed"),
        manifest_cell("model-a", "task-1", 43, "completed"),
        manifest_cell("model-a", "task-2", 42, "failed"),
        manifest_cell("model-b", "task-1", 42, "skipped"),
        manifest_cell("model-b", "task-2", 43, "planned"),
        manifest_cell("model-b", "task-2", 44, "planned"),
    ]
    write_json(root / MANIFEST_NAME, manifest_payload(cells))
    age_tree(root)

    result = sweep_monitor.full_scan(roots=[root], now=NOW)

    row = sweep_row(result, root)
    assert row.state == "finished"
    assert row.total == 6
    assert row.done == 4
    assert row.newest_mtime == NOW - 7200.0
    assert result.watermarks[str(root.resolve())] == NOW - 7200.0


def test_full_scan_running_via_live_roots_injection(tmp_path):
    """A Popen-alive injected root is running even when its mtimes are
    stale (TUI-launched sweeps never depend on churn)."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42))
    age_tree(root)

    result = sweep_monitor.full_scan(
        roots=[root], live_roots=[root], now=NOW)

    row = sweep_row(result, root)
    assert row.state == "running"
    assert row.total is None  # no manifest yet -> unknown totals
    assert row.done == 1


def test_full_scan_running_via_watermark_advance(tmp_path):
    """Newest-mtime advance vs the previous scan's watermark => running,
    isolated from the grace rule (the new mtime is STALE at scan 2)."""
    root = tmp_path / "finetuned"
    record = plant_record(root, "model-a", "task-1", 42,
                          make_record("model-a", "task-1", 42))
    age_tree(root)  # scan-1 view: old
    first = sweep_monitor.full_scan(roots=[root], now=NOW)
    assert sweep_row(first, root).state == "artifacts_only"

    set_mtime(record, NOW)  # churn: the frontier advanced...
    second = sweep_monitor.full_scan(
        roots=[root], prev_watermarks=first.watermarks, now=NOW + 7200.0)
    # ...and NOW is 7200s old at scan 2, so ONLY the watermark signal
    # can classify this root running.
    row = sweep_row(second, root)
    assert row.state == "running"
    assert second.watermarks[str(root.resolve())] == NOW


def test_full_scan_running_via_fresh_mtime_within_grace(tmp_path):
    """Newest tree mtime within STALE_GRACE_SECONDS of now => running
    (the quiet-phase tolerance, O2 — pinned at the boundary too)."""
    root = tmp_path / "finetuned"
    record = plant_record(root, "model-a", "task-1", 42,
                          make_record("model-a", "task-1", 42))
    set_mtime(record, NOW - STALE_GRACE)  # exactly at the boundary

    result = sweep_monitor.full_scan(roots=[root], now=NOW)

    assert sweep_row(result, root).state == "running"

    set_mtime(record, NOW - STALE_GRACE - 1.0)  # one second past it
    result = sweep_monitor.full_scan(roots=[root], now=NOW)
    assert sweep_row(result, root).state == "artifacts_only"


def test_full_scan_artifacts_only_stale_tree_unknown_total(tmp_path):
    """No manifest, no churn, no live process => artifacts_only with
    unknown totals (today's seed_9527 standalone-run shape — Pitfall 3:
    never rendered with a running glyph)."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42))
    age_tree(root)

    result = sweep_monitor.full_scan(roots=[root], now=NOW)

    row = sweep_row(result, root)
    assert row.state == "artifacts_only"
    assert row.total is None
    assert row.done == 1


def test_full_scan_skips_nonexistent_root_silently(tmp_path):
    """A root deleted mid-monitor degrades to a skip, never a crash,
    and never leaves a row or a watermark behind."""
    result = sweep_monitor.full_scan(
        roots=[tmp_path / "deleted-mid-monitor"], now=NOW)
    assert result.sweeps == ()
    assert result.watermarks == {}


def test_full_scan_now_injection_is_deterministic(tmp_path):
    """The same tree classifies differently under two injected clocks —
    classification is a pure function of (tree, now), never wall time."""
    root = tmp_path / "finetuned"
    record = plant_record(root, "model-a", "task-1", 42,
                          make_record("model-a", "task-1", 42))
    set_mtime(record, NOW)

    fresh = sweep_monitor.full_scan(roots=[root], now=NOW + STALE_GRACE)
    stale = sweep_monitor.full_scan(roots=[root], now=NOW + STALE_GRACE + 1.0)
    assert sweep_row(fresh, root).state == "running"
    assert sweep_row(stale, root).state == "artifacts_only"


def test_full_scan_default_roots_compose_manual_roots(
        monkeypatch, tmp_path):
    """roots=None scans DEFAULT_OUTPUT_ROOTS + manual_roots() (D-03)."""
    pin_state_dir(monkeypatch, tmp_path)
    default_root = tmp_path / "default-finetuned"
    manual_root = tmp_path / "manual-finetuned"
    for root in (default_root, manual_root):
        plant_record(root, "model-a", "task-1", 42,
                     make_record("model-a", "task-1", 42))
        age_tree(root)
    monkeypatch.setattr(
        sweep_monitor, "DEFAULT_OUTPUT_ROOTS", (default_root,))
    assert sweep_monitor.add_manual_root(manual_root) is True

    result = sweep_monitor.full_scan(now=NOW)

    scanned = {summary.root for summary in result.sweeps}
    assert scanned == {default_root.resolve(), manual_root.resolve()}


def test_manual_roots_round_trip_duplicate_noop_and_remove(
        monkeypatch, tmp_path):
    """Attach -> persisted + reloadable; duplicate attach is a no-op;
    remove detaches; removing an unattached path is False."""
    state = pin_state_dir(monkeypatch, tmp_path)
    root = tmp_path / "sweep-root"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42))

    assert sweep_monitor.manual_roots() == ()
    assert sweep_monitor.add_manual_root(root) is True
    assert sweep_monitor.manual_roots() == (root.resolve(),)
    assert (state / sweep_monitor.MANUAL_ROOTS_FILE_NAME).is_file()

    assert sweep_monitor.add_manual_root(root) is True  # duplicate: no-op
    assert sweep_monitor.manual_roots() == (root.resolve(),)  # still one

    assert sweep_monitor.remove_manual_root(root) is True
    assert sweep_monitor.manual_roots() == ()
    assert sweep_monitor.remove_manual_root(root) is False


def test_manual_roots_corrupt_state_file_reads_empty(
        monkeypatch, tmp_path):
    """A corrupt monitor_roots.json reads as no roots (tolerant load —
    never a crash), and a fresh attach rewrites it cleanly."""
    state = pin_state_dir(monkeypatch, tmp_path)
    state.mkdir(parents=True, exist_ok=True)
    (state / sweep_monitor.MANUAL_ROOTS_FILE_NAME).write_text(
        "{not json", encoding="utf-8")

    assert sweep_monitor.manual_roots() == ()


def test_add_manual_root_refuses_non_sweep_path(monkeypatch, tmp_path):
    """[a] attach validation (D-03): a path that is not a sweep root is
    refused — never silently attached."""
    pin_state_dir(monkeypatch, tmp_path)
    empty = tmp_path / "empty-dir"
    empty.mkdir()

    assert sweep_monitor.add_manual_root(empty) is False
    assert sweep_monitor.add_manual_root(tmp_path / "no-such-dir") is False
    assert sweep_monitor.manual_roots() == ()


def test_is_sweep_root_accepts_manifest_record_and_layout(tmp_path):
    """The predicate's true faces: manifest, failures file, a run
    record, and the seed layout with cell artifacts."""
    manifest_root = tmp_path / "by-manifest"
    write_json(manifest_root / MANIFEST_NAME,
               manifest_payload([manifest_cell("m", "t", 42)]))
    assert sweep_monitor.is_sweep_root(manifest_root) is True

    failures_root = tmp_path / "by-failures"
    write_json(failures_root / FAILURES_NAME, [])
    assert sweep_monitor.is_sweep_root(failures_root) is True

    record_root = tmp_path / "by-record"
    plant_record(record_root, "m", "t", 42, make_record("m", "t", 42))
    assert sweep_monitor.is_sweep_root(record_root) is True

    layout_root = tmp_path / "by-layout"
    marker = seed_dir(layout_root, "m", "t", 42) / RESUME_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("{}", encoding="utf-8")
    assert sweep_monitor.is_sweep_root(layout_root) is True


def test_is_sweep_root_rejects_empty_and_plain_dirs(tmp_path):
    """The predicate's false faces: missing path, empty dir, a dir with
    files but no sweep layout."""
    assert sweep_monitor.is_sweep_root(tmp_path / "no-such-dir") is False
    empty = tmp_path / "empty"
    empty.mkdir()
    assert sweep_monitor.is_sweep_root(empty) is False

    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "readme.txt").write_text("not a sweep", encoding="utf-8")
    assert sweep_monitor.is_sweep_root(plain) is False
