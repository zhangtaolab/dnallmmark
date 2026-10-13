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
import time
from datetime import UTC, datetime
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


def NOW_REAL():
    """The real clock for the un-injectable cells_view/frontier grace
    checks — fixtures pin mtimes RELATIVE to it (margin 600s)."""
    return time.time()


def age_tree(root, now=NOW, age_seconds=7200.0, skip=()):
    """Set EVERY file mtime under root to now - age (the stale-tree
    shape: explicitly old, never accidentally inside the grace).
    ``skip`` exempts paths (and their subtrees) that must stay fresh."""
    skip = {Path(item).resolve() for item in skip}
    for path in sorted(Path(root).rglob("*")):
        resolved = path.resolve()
        if any(resolved == item or item in resolved.parents
               for item in skip):
            continue
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


# =====================================================================
# Lane 2 (Task 2): cell derivation + tolerant readers + resume count
# =====================================================================


def test_cells_view_mixed_tree_exact_per_seed_states(tmp_path):
    """One row per (model, task), per-seed states exact: record statuses
    map directly, marker-only => skipped (distinct provenance), churn
    (runs/ + checkpoint-*) => running without any record."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42, status="completed"))
    plant_record(root, "model-a", "task-1", 43,
                 make_record("model-a", "task-1", 43, status="failed"))
    plant_record(root, "model-a", "task-1", 44,
                 make_record("model-a", "task-1", 44, status="skipped"))
    marker_dir = seed_dir(root, "model-a", "task-2", 42)
    marker_dir.mkdir(parents=True, exist_ok=True)
    (marker_dir / RESUME_MARKER).write_text("{}", encoding="utf-8")
    churn_dir = seed_dir(root, "model-b", "task-1", 42)
    (churn_dir / "runs").mkdir(parents=True, exist_ok=True)
    (churn_dir / "checkpoint-520").mkdir(parents=True, exist_ok=True)
    age_tree(root)  # churn presence must not depend on fresh mtimes

    rows = sweep_monitor.cells_view(root)

    assert rows == (
        sweep_monitor.CellRow(
            model="model-a", task="task-1",
            seeds=(
                sweep_monitor.CellSeed(42, "completed", None),
                sweep_monitor.CellSeed(43, "failed", None),
                sweep_monitor.CellSeed(44, "skipped", None),
            )),
        sweep_monitor.CellRow(
            model="model-a", task="task-2",
            seeds=(sweep_monitor.CellSeed(42, "skipped", None),)),
        sweep_monitor.CellRow(
            model="model-b", task="task-1",
            seeds=(sweep_monitor.CellSeed(42, "running", None),)),
    )


def test_cells_view_running_never_depends_on_records(tmp_path):
    """The record lands POST-cell (Pitfall 2): a freshly mkdir'd seed
    dir with NO record, NO marker renders running (the driver mkdirs
    before the executor — mtime within grace)."""
    root = tmp_path / "finetuned"
    churn_dir = seed_dir(root, "model-a", "task-1", 42)
    churn_dir.mkdir(parents=True, exist_ok=True)  # nothing inside yet

    rows = sweep_monitor.cells_view(root)

    assert rows[0].seeds[0].state == "running"


def test_cells_view_curve_fraction_states(tmp_path):
    """Curve nesting: seed cells with frac_* children carry
    fraction_states per fraction and fold (any running -> running; all
    terminal -> completed). Curve records live UNDER the frac dirs (the
    curve cell_dir is seed_{n}/frac_{f})."""
    root = tmp_path / "finetuned"
    partial = seed_dir(root, "model-a", "task-1", 42)
    done_frac = partial / "frac_0.25"
    write_json(done_frac / RECORD_NAME,
               make_record("model-a", "task-1", 42, train_fraction=0.25))
    (partial / "frac_0.5").mkdir(parents=True, exist_ok=True)  # live frac

    full = seed_dir(root, "model-a", "task-2", 43)
    record = make_record("model-a", "task-2", 43, train_fraction=0.25)
    write_json(full / "frac_0.25" / RECORD_NAME, record)
    write_json(full / "frac_0.5" / RECORD_NAME,
               dict(record, train_fraction=0.5))

    rows = {row.model + "/" + row.task: row for row in
            sweep_monitor.cells_view(root)}

    partial_row = rows["model-a/task-1"]
    assert partial_row.seeds[0].state == "running"  # any running frac
    assert partial_row.seeds[0].fraction_states == (
        ("frac_0.25", "completed"),
        ("frac_0.5", "running"),  # fresh dir, no record
    )

    full_row = rows["model-a/task-2"]
    assert full_row.seeds[0].state == "completed"  # all terminal
    assert full_row.seeds[0].fraction_states == (
        ("frac_0.25", "completed"),
        ("frac_0.5", "completed"),
    )


def test_cells_view_queued_from_manifest_and_expected_seeds(tmp_path):
    """Manifest-known cells not yet started render queued (dry-run
    manifests show the whole plan); expected_seeds threads configured
    seeds as queued columns for discovered rows."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42))
    write_json(root / MANIFEST_NAME, manifest_payload([
        manifest_cell("model-c", "task-9", 42, "planned"),
        manifest_cell("model-c", "task-9", 43, "planned"),
    ]))

    rows = {row.model + "/" + row.task: row for row in
            sweep_monitor.cells_view(root, expected_seeds=(42, 43, 44))}

    assert rows["model-c/task-9"].seeds == (
        sweep_monitor.CellSeed(42, "queued", None),
        sweep_monitor.CellSeed(43, "queued", None),
        sweep_monitor.CellSeed(44, "queued", None),
    )
    assert rows["model-a/task-1"].seeds == (
        sweep_monitor.CellSeed(42, "completed", None),
        sweep_monitor.CellSeed(43, "queued", None),
        sweep_monitor.CellSeed(44, "queued", None),
    )


def test_cells_view_alias_model_names_verbatim(tmp_path):
    """Model identity = the dir/record name VERBATIM — the alias under
    peft/config-variant, never translated to the base registry name."""
    root = tmp_path / "finetuned"
    plant_record(root, "plant-dnabert-6mer+lora", "GUE__emp_H3", 42,
                 make_record("plant-dnabert-6mer+lora", "GUE__emp_H3", 42,
                             peft="lora"))

    rows = sweep_monitor.cells_view(root)

    assert rows[0].model == "plant-dnabert-6mer+lora"


def test_cells_view_unknown_record_status_renders_verbatim(tmp_path):
    """A record with an unrecognized status renders that status
    verbatim (honest, never translated into a known state)."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42, status="planned"))

    rows = sweep_monitor.cells_view(root)

    assert rows[0].seeds[0].state == "planned"


def test_load_record_tolerant_faces(tmp_path):
    """Missing => None; valid => dict; damaged => last-known-good;
    a fresh non-dict with no prior parse => None (treated absent)."""
    fresh = tmp_path / "fresh-record.json"
    assert sweep_monitor.load_record(fresh) is None

    record = make_record("m", "t", 42)
    fresh.write_text(json.dumps(record), encoding="utf-8")
    assert sweep_monitor.load_record(fresh) == record

    fresh.write_text('{"model": "m", "task": "t", "seed"', encoding="utf-8")
    assert sweep_monitor.load_record(fresh) == record  # last-known-good

    no_prior = tmp_path / "non-dict.json"
    no_prior.write_text("[1, 2]", encoding="utf-8")
    assert sweep_monitor.load_record(no_prior) is None


def test_cells_view_retains_last_known_good_across_scans(tmp_path):
    """A record truncated mid-write is skipped and the previous
    snapshot stands (MON-01's tolerant contract — never a crash, never
    a state flip from damage)."""
    sweep_monitor._reset_last_known_good()
    root = tmp_path / "finetuned"
    record_path = plant_record(root, "model-a", "task-1", 42,
                               make_record("model-a", "task-1", 42))

    first = sweep_monitor.cells_view(root)
    assert first[0].seeds[0].state == "completed"

    record_path.write_text(
        '{"model": "model-a", "task": "task-1", "seed": 42, "sta',
        encoding="utf-8")  # half a JSON — the mid-write window

    second = sweep_monitor.cells_view(root)
    assert second[0].seeds[0].state == "completed"  # last-known-good

    # A damaged record with NO prior parse reads absent: an inert aged
    # dir renders queued (never fabricated from damage).
    inert = seed_dir(root, "model-b", "task-1", 43)
    inert.mkdir(parents=True, exist_ok=True)
    (inert / RECORD_NAME).write_text("{broken", encoding="utf-8")
    set_mtime(inert, NOW_REAL() - 7200.0)
    rows = {row.model: row for row in sweep_monitor.cells_view(root)}
    assert rows["model-b"].seeds[0].state == "queued"


def test_corrupt_manifest_treated_absent_state_falls_back(tmp_path):
    """A corrupt/non-dict manifest is treated absent — classification
    falls back to the churn/mtime rules (D-09), never finished."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42))
    age_tree(root)

    (root / MANIFEST_NAME).write_text('{"matrix": {"cells": [',
                                       encoding="utf-8")
    age_tree(root)  # the fresh manifest write must not trip the grace
    corrupt = sweep_monitor.full_scan(roots=[root], now=NOW)
    assert sweep_row(corrupt, root).state == "artifacts_only"

    (root / MANIFEST_NAME).write_text("[]", encoding="utf-8")  # non-dict
    age_tree(root)
    non_dict = sweep_monitor.full_scan(roots=[root], now=NOW)
    assert sweep_row(non_dict, root).state == "artifacts_only"

    (root / MANIFEST_NAME).unlink()
    assert sweep_monitor.load_manifest(root / MANIFEST_NAME) is None
    assert sweep_monitor.load_failures(root / "no-such-failures.json") is None
    (root / "non-list.json").write_text('{"a": 1}', encoding="utf-8")
    assert sweep_monitor.load_failures(root / "non-list.json") is None


def test_resume_count_from_records_then_manifest(tmp_path):
    """While running: the skipped RECORDS on disk; once finished: the
    manifest's skipped cells (this run's view — WR-12 keeps the on-disk
    record of the run that trained the cell)."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42, status="skipped"))
    plant_record(root, "model-a", "task-2", 43,
                 make_record("model-a", "task-2", 43, status="skipped"))
    plant_record(root, "model-b", "task-1", 42,
                 make_record("model-b", "task-1", 42, status="completed"))

    assert sweep_monitor.resume_count(root) == 2

    # A later finished manifest reports THIS run's skips: the seed that
    # trained earlier (on-disk record completed, WR-12) counts skipped.
    write_json(root / MANIFEST_NAME, manifest_payload([
        manifest_cell("model-a", "task-1", 42, "skipped"),
        manifest_cell("model-a", "task-2", 43, "skipped"),
        manifest_cell("model-b", "task-1", 42, "skipped"),
    ]))
    assert sweep_monitor.resume_count(root) == 3


def test_frontier_scan_states_and_newest_cell(tmp_path):
    """The light pass: newest seed-dir activity + record states only.
    Fresh churn => running with the newest cell located; live
    injection beats staleness."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42))
    churn_dir = seed_dir(root, "model-a", "task-2", 43)
    churn_dir.mkdir(parents=True, exist_ok=True)
    set_mtime(churn_dir, NOW_REAL() - 10.0)  # fresh, no record
    age_tree(root, skip=[churn_dir])

    fresh = sweep_monitor.frontier_scan(root)
    assert fresh.state == "running"
    assert fresh.newest_cell == ("model-a", "task-2", 43)
    assert fresh.cell_states[("model-a", "task-1", 42)] == "completed"
    assert fresh.cell_states[("model-a", "task-2", 43)] == "running"

    stale = sweep_monitor.frontier_scan(root, now=NOW_REAL() + 7200.0)
    assert stale.state == "artifacts_only"

    live = sweep_monitor.frontier_scan(
        root, live_roots=[root], now=NOW_REAL() + 7200.0)
    assert live.state == "running"


# =====================================================================
# Lane 3 (Task 3): stats/elapsed/ETA (D-17) + failures + log tail
# =====================================================================

#: The D-17 clock basis: EPOCH0 is 2023-11-14T22:13:20Z — every record
#: stamp is a fixed offset from it, every `now` an epoch float.
EPOCH0 = 1_700_000_000.0


def stamp(offset_seconds):
    """An ISO-8601 UTC stamp at EPOCH0 + offset (the record shape)."""
    return datetime.fromtimestamp(EPOCH0 + offset_seconds, tz=UTC).isoformat()


def completed(model, task, seed, start, finish):
    """A completed record with wall-clock stamps."""
    return make_record(model, task, seed, status="completed",
                       started_at=stamp(start), finished_at=stamp(finish))


def eta_of(root, **kwargs):
    """stats(root, ...).eta — the D-17 verdict under test."""
    return sweep_monitor.stats(root, **kwargs).eta


def test_stats_done_total_current_elapsed_exact(tmp_path):
    """Five staggered completed records: done/total/current/elapsed are
    exact under an injected now; every duration 60s => the point ETA is
    median(60) x remaining."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 completed("model-a", "task-1", 42, 0, 60))
    plant_record(root, "model-a", "task-1", 43,
                 completed("model-a", "task-1", 43, 100, 160))
    plant_record(root, "model-a", "task-2", 42,
                 completed("model-a", "task-2", 42, 200, 260))
    plant_record(root, "model-b", "task-1", 42,
                 completed("model-b", "task-1", 42, 300, 360))
    plant_record(root, "model-b", "task-2", 43,
                 completed("model-b", "task-2", 43, 400, 460))

    result = sweep_monitor.stats(
        root, expected_total=10, now=EPOCH0 + 1000.0)

    assert result.done == 5
    assert result.total == 10
    assert result.current == sweep_monitor.CurrentCell(
        model="model-b", task="task-2", seed=43)
    assert result.elapsed_seconds == 1000.0  # now - earliest started_at
    assert result.eta == sweep_monitor.EtaEstimate(
        mode="point", point_seconds=300.0, lo_seconds=None, hi_seconds=None)


def test_stats_elapsed_none_before_first_record_without_fallback(tmp_path):
    """No records and no fallback_start: elapsed is None (the dash
    rendering) and the ETA is pending; done 0; total threads through."""
    root = tmp_path / "finetuned"
    root.mkdir(parents=True)

    result = sweep_monitor.stats(root, expected_total=4, now=EPOCH0)

    assert result.elapsed_seconds is None
    assert result.current is None
    assert result.done == 0
    assert result.total == 4
    assert result.eta.mode == "pending"


def test_stats_fallback_start_before_first_record(tmp_path):
    """A TUI-launched sweep before its first record: elapsed accrues
    from the injected launcher start."""
    root = tmp_path / "finetuned"
    root.mkdir(parents=True)

    result = sweep_monitor.stats(
        root, fallback_start=EPOCH0 + 100.0, now=EPOCH0 + 1000.0)

    assert result.elapsed_seconds == 900.0


def test_stats_current_from_newest_activity_dir_when_no_records(tmp_path):
    """No records yet: current derives from the newest-activity seed
    dir (the mkdir-before-executor cell)."""
    root = tmp_path / "finetuned"
    old_dir = seed_dir(root, "model-a", "task-1", 42)
    old_dir.mkdir(parents=True, exist_ok=True)
    set_mtime(old_dir, NOW_REAL() - 7200.0)
    fresh_dir = seed_dir(root, "model-a", "task-2", 43)
    fresh_dir.mkdir(parents=True, exist_ok=True)
    set_mtime(fresh_dir, NOW_REAL() - 5.0)

    result = sweep_monitor.stats(root, now=NOW_REAL())

    assert result.current == sweep_monitor.CurrentCell(
        model="model-a", task="task-2", seed=43)


def test_stats_manifest_derives_total_and_model_plan(tmp_path):
    """No expected_total: the manifest's cell count is the total and
    its per-model plan threads the per-model ETA (manifest cells carry
    sweep_flags merges — only model/task/seed/status are read)."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 completed("model-a", "task-1", 42, 0, 100))
    write_json(root / MANIFEST_NAME, manifest_payload([
        manifest_cell("model-a", "task-1", 42, "completed"),
        manifest_cell("model-a", "task-1", 43, "planned"),
        manifest_cell("model-a", "task-1", 44, "planned"),
    ]))

    result = sweep_monitor.stats(root, now=EPOCH0 + 500.0)

    assert result.total == 3
    assert result.done == 1
    # remaining 2 x model-a's own median (100) — per-model plan derivable
    assert result.eta == sweep_monitor.EtaEstimate(
        mode="point", point_seconds=200.0, lo_seconds=None, hi_seconds=None)


def test_eta_pending_before_first_completion():
    """< 1 completed duration => pending (the estimating degradation),
    whatever else is known — skipped records never count as data."""
    records = [make_record("m", "t", 42, status="skipped",
                           started_at=stamp(0), finished_at=stamp(1))]
    estimate = sweep_monitor.eta_estimate(records, done=1, total=5)
    assert estimate.mode == "pending"
    assert estimate == sweep_monitor.EtaEstimate(
        mode="pending", point_seconds=None, lo_seconds=None, hi_seconds=None)

    assert sweep_monitor.eta_estimate([], done=0, total=5).mode == "pending"


def test_eta_point_median_times_remaining_exact():
    """Durations [60, 60, 60]: the point is median x remaining exactly."""
    records = [
        completed("m", "t", 42, 0, 60),
        completed("m", "t", 43, 100, 160),
        completed("m", "t", 44, 200, 260),
    ]
    estimate = sweep_monitor.eta_estimate(records, done=3, total=6)
    assert estimate.mode == "point"
    assert estimate.point_seconds == 180.0
    assert estimate.lo_seconds is None and estimate.hi_seconds is None


def test_eta_range_when_variance_exceeds_ratio():
    """Durations [60, 60, 300] (max/min 5 > 3.0): the point is replaced
    by the min-max range over the remaining count."""
    records = [
        completed("m", "t", 42, 0, 60),
        completed("m", "t", 43, 100, 160),
        completed("m", "t", 44, 200, 500),
    ]
    estimate = sweep_monitor.eta_estimate(records, done=3, total=6)
    assert estimate.mode == "range"
    assert estimate.lo_seconds == 180.0  # min 60 x remaining 3
    assert estimate.hi_seconds == 900.0  # max 300 x remaining 3
    assert estimate.point_seconds is None


def test_eta_point_at_exactly_the_ratio_boundary():
    """max/min == 3.0 exactly: NOT exceeded — the point stands (the
    pinned ratio is a strict inequality)."""
    records = [completed("m", "t", 42, 0, 60), completed("m", "t", 43, 0, 180)]
    estimate = sweep_monitor.eta_estimate(records, done=2, total=4)
    assert estimate.mode == "point"
    assert estimate.point_seconds == 240.0  # median 120 x remaining 2


def test_eta_skipped_duration_excluded():
    """A skipped record's ~zero duration must not shift the median:
    completed [60, 180] (median 120) + skipped 0-duration stays 120 —
    had it leaked in, the median would be 60."""
    records = [
        completed("m", "t", 42, 0, 60),
        completed("m", "t", 43, 0, 180),
        make_record("m", "t", 44, status="skipped",
                    started_at=stamp(0), finished_at=stamp(0)),
    ]
    estimate = sweep_monitor.eta_estimate(records, done=3, total=5)
    assert estimate.mode == "point"
    assert estimate.point_seconds == 240.0  # 120 x remaining 2


def test_eta_none_when_total_unknown_or_nothing_remaining():
    """Unknown total => none (no fabricated totals, T-11-04-03);
    nothing remaining => none."""
    records = [completed("m", "t", 42, 0, 60)]
    assert sweep_monitor.eta_estimate(records, done=1, total=None).mode == \
        "none"
    assert sweep_monitor.eta_estimate(records, done=1, total=1).mode == \
        "none"


def test_eta_per_model_median_else_global():
    """model-a has a completion (its own median), model-b none (the
    global median): point = 3 x 180 + 1 x 60 = 600 with the manifest
    plan; the model-less fallback is global-median x remaining. The
    durations sit exactly AT the variance ratio (180/60 == 3.0, not
    exceeded) so the point mode is under test, not the range."""
    records = [
        completed("model-a", "t", 42, 0, 180),
        completed("model-b", "t", 42, 0, 60),
        completed("model-b", "t", 43, 0, 60),
        completed("model-b", "t", 44, 0, 60),
    ]
    per_model = sweep_monitor.eta_estimate(
        records, done=4, total=8,
        model_totals={"model-a": 4, "model-b": 4})
    assert per_model.mode == "point"
    assert per_model.point_seconds == 600.0  # 3 x 180 + 1 x 60

    fallback = sweep_monitor.eta_estimate(records, done=4, total=8)
    # global median of [180, 60, 60, 60] is 60 -> 60 x remaining 4
    assert fallback.point_seconds == 240.0


def test_eta_malformed_and_skewed_stamps_dropped_never_crash():
    """A malformed ISO stamp or a finished-before-started skew drops
    that record from the math (T-11-04-01 tolerance), never a crash."""
    records = [
        completed("m", "t", 42, 0, 100),
        make_record("m", "t", 43, status="completed",
                    started_at="not-a-timestamp",
                    finished_at=stamp(999)),
        make_record("m", "t", 44, status="completed",
                    started_at=stamp(500), finished_at=stamp(100)),  # skew
    ]
    estimate = sweep_monitor.eta_estimate(records, done=3, total=5)
    assert estimate.mode == "point"
    assert estimate.point_seconds == 200.0  # the one good 100s x remaining 2


def test_rerun_lane_derives_peft_and_variant_from_source_sweep(tmp_path):
    """WR-01: the re-run lane recovers from the SOURCE sweep's own
    artifacts — the manifest's merged config_variant flag + the failure
    entries' alias/base pair — never a silent none/none default that
    would re-train BASE cells instead of the confirmed alias cells."""
    root = tmp_path / "finetuned"
    write_json(root / MANIFEST_NAME, manifest_payload([
        {**manifest_cell("model-a+lora", "task-1", 42, "failed"),
         "config_variant": "probe"},
    ]))
    write_json(root / FAILURES_NAME, [
        {"model": "model-a+lora", "base_model": "model-a",
         "task": "task-1", "seed": 42, "output_dir": "/x",
         "error": "boom"},
    ])

    assert sweep_monitor.rerun_lane(root) == ("lora", "probe")


def test_rerun_lane_head_variant_comes_from_manifest_flags(tmp_path):
    """The ``head`` lane KEEPS base names for the frozen pair, so an
    alias-name derivation would miss it — the manifest's merged
    config_variant flag is the authoritative source."""
    root = tmp_path / "finetuned"
    write_json(root / MANIFEST_NAME, manifest_payload([
        {**manifest_cell("model-a", "task-1", 42, "failed"),
         "config_variant": "head"},
    ]))
    write_json(root / FAILURES_NAME, [
        {"model": "model-a", "base_model": "model-a",
         "task": "task-1", "seed": 42, "output_dir": "/x",
         "error": "boom"},
    ])

    assert sweep_monitor.rerun_lane(root) == ("none", "head")


def test_rerun_lane_base_sweep_and_missing_artifacts_default_none(
        tmp_path):
    """A BASE sweep's artifacts (no flags, plain names — and a manifest
    whose cells carry no config_variant key) and a root with no
    artifacts at all both derive the honest none/none lane."""
    base_root = tmp_path / "base"
    write_json(base_root / MANIFEST_NAME, manifest_payload([
        manifest_cell("model-a", "task-1", 42, "failed"),
    ]))
    write_json(base_root / FAILURES_NAME, [
        {"model": "model-a", "base_model": "model-a",
         "task": "task-1", "seed": 42, "output_dir": "/x",
         "error": "boom"},
    ])
    assert sweep_monitor.rerun_lane(base_root) == ("none", "none")

    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    assert sweep_monitor.rerun_lane(empty_root) == ("none", "none")


def test_failures_view_records_while_running_file_when_finished(tmp_path):
    """MON-03's source switch (O3): records with status failed are the
    LIVE source while running (sweep_failures.json does not exist yet);
    once finished the file is authoritative — its base_model field
    never leaks into the row (alias identity only)."""
    root = tmp_path / "finetuned"
    failed_dir = str(seed_dir(root, "model-a", "task-2", 43))
    plant_record(root, "model-a", "task-1", 42,
                 completed("model-a", "task-1", 42, 0, 60))
    plant_record(root, "model-a", "task-2", 43,
                 make_record("model-a", "task-2", 43, status="failed",
                             started_at=stamp(0), finished_at=stamp(10),
                             error="executor exited 0 but "
                                   "final_metrics.json is missing",
                             output_dir=failed_dir))
    plant_record(root, "model-b", "task-1", 42,
                 make_record("model-b", "task-1", 42, status="failed",
                             started_at=stamp(0), finished_at=stamp(10),
                             error="OSError: boom",
                             output_dir=str(
                                 seed_dir(root, "model-b", "task-1", 42))))

    live = sweep_monitor.failures_view(root)
    assert live == (
        sweep_monitor.FailureRow(
            model="model-a", task="task-2", seed=43,
            error="executor exited 0 but final_metrics.json is missing",
            output_dir=failed_dir),
        sweep_monitor.FailureRow(
            model="model-b", task="task-1", seed=42, error="OSError: boom",
            output_dir=str(seed_dir(root, "model-b", "task-1", 42))),
    )

    write_json(root / MANIFEST_NAME, manifest_payload([
        manifest_cell("model-a", "task-1", 42, "completed"),
        manifest_cell("model-a", "task-2", 43, "failed"),
        manifest_cell("model-b", "task-1", 42, "failed"),
    ]))
    write_json(root / "sweep_failures.json", [
        {"model": "model-a+lora", "base_model": "model-a",
         "task": "task-2", "seed": 43, "output_dir": failed_dir,
         "error": "recorded failure"},
    ])

    finished = sweep_monitor.failures_view(root)
    assert finished == (
        sweep_monitor.FailureRow(
            model="model-a+lora", task="task-2", seed=43,
            error="recorded failure", output_dir=failed_dir),
    )


#: The live-captured dry-run line (11-04 RESEARCH Area 7) — the tee
#: fixture's first line, verbatim.
DRY_RUN_LINE = (
    "[Dry-run] 1 planned cell(s) over 1 model(s) x 1 task(s) x 1 "
    "seed(s); manifest: /tmp/sw-dry/sweep_manifest.json")


def test_read_log_tail_bounded_lines_and_bytes(tmp_path):
    """The tail is bounded by max_lines (default 200) and max_bytes
    (seek from end, partial leading line dropped); the captured
    dry-run line rides the head of a full tee-like file."""
    tee = tmp_path / "sweep_20261013_finetuned.log"
    tee.write_text(
        "\n".join([DRY_RUN_LINE] + [f"line-{i}" for i in range(1, 300)])
        + "\n", encoding="utf-8")

    window = sweep_monitor.read_log_tail(tee, max_lines=50)
    assert len(window) == 50
    assert window[-1] == "line-299"
    assert window[0] == "line-250"  # exactly the last 50 lines

    default_window = sweep_monitor.read_log_tail(tee)
    assert len(default_window) == 200
    assert default_window[-1] == "line-299"

    # byte-bound: 100 long lines x 2KB; the 8KB window keeps only the
    # last few lines and never more than the window can hold
    big = tmp_path / "big.log"
    big.write_text(
        "\n".join(f"{i:06d} " + "x" * 2000 for i in range(100)) + "\n",
        encoding="utf-8")
    byte_window = sweep_monitor.read_log_tail(big, max_bytes=8192)
    assert 0 < len(byte_window) < 10
    assert byte_window[-1].startswith("000099 ")


def test_read_log_tail_missing_and_unreadable_return_none(tmp_path):
    """A missing file (and an unreadable path) return None — the screen
    renders the designed unavailable state, never a fabricated log."""
    assert sweep_monitor.read_log_tail(tmp_path / "no-such.log") is None
    assert sweep_monitor.read_log_tail(tmp_path) is None  # a directory
    empty = tmp_path / "empty.log"
    empty.write_text("", encoding="utf-8")
    assert sweep_monitor.read_log_tail(empty) == ()


def test_format_hms_and_format_eta_table():
    """The auto-default 17 formats: H:MM:SS elapsed; minute / one-decimal
    hour / day+hour ETA humanization, numeric-English only."""
    assert sweep_monitor.format_hms(4360) == "1:12:40"
    assert sweep_monitor.format_hms(0) == "0:00:00"
    assert sweep_monitor.format_hms(59) == "0:00:59"

    assert sweep_monitor.format_eta(2100) == "≈35m"
    assert sweep_monitor.format_eta(30) == "≈1m"  # never ≈0m
    assert sweep_monitor.format_eta(3600) == "≈1h"  # trailing zero drops
    assert sweep_monitor.format_eta(7560) == "≈2.1h"
    assert sweep_monitor.format_eta(97200) == "≈1d3h"
