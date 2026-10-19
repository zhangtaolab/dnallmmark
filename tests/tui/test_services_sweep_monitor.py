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
    """The O2/O4 pins + the D-03 default roots, exactly as the plan
    states them (constants are the tunable surface, never inlined).
    WR-06: BOTH homes of run_sweep's default ./finetuned — the TUI
    launch path (cwd pinned to pipeline/) and the documented repo-root
    CLI invocation."""
    assert sweep_monitor.STALE_GRACE_SECONDS == 600.0
    assert sweep_monitor.ETA_VARIANCE_RATIO == 3.0
    assert sweep_monitor.DEFAULT_OUTPUT_ROOTS == (
        REPO_ROOT / "pipeline" / "finetuned",
        REPO_ROOT / "finetuned",
    )


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


def test_full_scan_default_roots_cover_both_resolution_homes(
        monkeypatch, tmp_path):
    """WR-06 (phase-11 review): roots=None scans BOTH default homes of
    run_sweep's ./finetuned — the TUI launch path (cwd pinned to
    pipeline/) AND the documented repo-root CLI invocation. A
    manifest-bearing tree under each is discovered."""
    pin_state_dir(monkeypatch, tmp_path)
    tui_home = tmp_path / "repo" / "pipeline" / "finetuned"
    cli_home = tmp_path / "repo" / "finetuned"
    for home in (tui_home, cli_home):
        write_json(home / MANIFEST_NAME, manifest_payload(
            [manifest_cell("model-a", "task-1", 42, "completed")]))
    monkeypatch.setattr(
        sweep_monitor, "DEFAULT_OUTPUT_ROOTS", (tui_home, cli_home))

    result = sweep_monitor.full_scan(now=NOW)

    assert {str(summary.root) for summary in result.sweeps} == {
        str(tui_home), str(cli_home)}


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

    # 261017-uwr (UWR-4): cells_view fills newest_mtime (the row's max
    # seed-dir mtime; age_tree pinned every dir to NOW - 7200).
    aged = NOW - 7200.0
    assert rows == (
        sweep_monitor.CellRow(
            model="model-a", task="task-1",
            seeds=(
                sweep_monitor.CellSeed(42, "completed", None),
                sweep_monitor.CellSeed(43, "failed", None),
                sweep_monitor.CellSeed(44, "skipped", None),
            ),
            newest_mtime=aged),
        sweep_monitor.CellRow(
            model="model-a", task="task-2",
            seeds=(sweep_monitor.CellSeed(42, "skipped", None),),
            newest_mtime=aged),
        sweep_monitor.CellRow(
            model="model-b", task="task-1",
            seeds=(sweep_monitor.CellSeed(42, "running", None),),
            newest_mtime=aged),
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


# ===== WR-02: the re-run at a populated root (fallback_start scoping) =====


def test_stats_rerun_at_populated_root_scopes_to_current_run(tmp_path):
    """WR-02: a from-failures re-run at a root holding a FINISHED prior
    sweep — done/elapsed/current scope to THIS run's records
    (started_at >= the injected fallback start), the stale pre-run
    manifest supplies neither the total nor the per-model ETA plan, and
    the prior sweep's days-old records never fabricate the elapsed."""
    root = tmp_path / "finetuned"
    # the prior sweep: three completed records + its (now stale) manifest
    plant_record(root, "model-a", "task-1", 42,
                 completed("model-a", "task-1", 42, 0, 3600))
    plant_record(root, "model-a", "task-2", 42,
                 completed("model-a", "task-2", 42, 3600, 7200))
    plant_record(root, "model-b", "task-1", 42,
                 completed("model-b", "task-1", 42, 7200, 10800))
    stale_manifest = write_json(root / MANIFEST_NAME, manifest_payload([
        manifest_cell("model-a", "task-1", 42, "completed"),
        manifest_cell("model-a", "task-2", 42, "completed"),
        manifest_cell("model-b", "task-1", 42, "completed"),
    ]))
    rerun_start = EPOCH0 + 10_000_000.0        # ~115 days later
    set_mtime(stale_manifest, EPOCH0)          # landed before the re-run
    # the re-run's one record so far
    plant_record(root, "model-a", "task-1", 42,
                 completed("model-a", "task-1", 42,
                           10_000_000, 10_000_060))

    result = sweep_monitor.stats(
        root, fallback_start=rerun_start, now=EPOCH0 + 10_000_600.0)

    assert result.done == 1, "the prior sweep's records do not count"
    assert result.total is None, (
        "the stale manifest supplies no total — the honest unknown "
        "until the re-run's own manifest lands"
    )
    assert result.elapsed_seconds == 600.0, (
        "elapsed accrues from THIS run's first record, not the prior "
        "sweep's days-old earliest stamp"
    )
    assert result.current == sweep_monitor.CurrentCell(
        model="model-a", task="task-1", seed=42)
    assert result.eta.mode == "none", "no known total — no fabricated ETA"

    # the un-scoped finished view (no fallback injection) is unchanged:
    # every on-disk record counts (the re-run overwrote its cell's
    # record, so 2 prior + 1 re-run) and the manifest supplies the total
    finished_view = sweep_monitor.stats(root, now=EPOCH0 + 10_000_600.0)
    assert finished_view.done == 3
    assert finished_view.total == 3


def test_stats_rerun_adopts_its_own_manifest_once_it_lands(tmp_path):
    """Once the re-run's manifest lands (mtime >= the fallback start)
    it supplies the total and the per-model plan — the fresh manifest
    beats any stale injected expectation."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 completed("model-a", "task-1", 42,
                           10_000_000, 10_000_060))
    fresh_manifest = write_json(root / MANIFEST_NAME, manifest_payload([
        manifest_cell("model-a", "task-1", 42, "completed"),
        manifest_cell("model-a", "task-1", 43, "planned"),
    ]))
    rerun_start = EPOCH0 + 10_000_000.0
    set_mtime(fresh_manifest, EPOCH0 + 10_000_700.0)   # after the launch

    result = sweep_monitor.stats(
        root, expected_total=9300, fallback_start=rerun_start,
        now=EPOCH0 + 10_000_800.0)

    assert result.total == 9300, (
        "an explicit expected_total still wins (the injection contract)"
    )

    result_no_expected = sweep_monitor.stats(
        root, fallback_start=rerun_start, now=EPOCH0 + 10_000_800.0)
    assert result_no_expected.total == 2, (
        "the FRESH manifest's count is the total once it lands"
    )


def test_stats_rerun_records_without_parseable_start_are_excluded(
        tmp_path):
    """A record whose started_at cannot be parsed cannot be proven
    in-run — under a fallback-scoped view it drops (never crashes,
    never inflates this run's done)."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42, status="completed",
                             started_at="not-a-stamp",
                             finished_at=stamp(60)))

    result = sweep_monitor.stats(
        root, fallback_start=EPOCH0, now=EPOCH0 + 500.0)

    assert result.done == 0
    assert result.elapsed_seconds == 500.0   # the fallback carries elapsed


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


# =====================================================================
# Lane 4 (C4J-3, 261015-c4j): checkpoint training progress + the entry
# fold — the newest checkpoint-*/trainer_state.json under a RUNNING seed
# is the slot-5 entries list's progress source (RESUME_MARKER is the
# same artifact name as the completion marker, D-05 same-source; read
# from checkpoint dirs MID-RUN and from the seed root post-run)
# =====================================================================


def write_checkpoint(seed_path, number, payload=None):
    """Stage one checkpoint-<n>/trainer_state.json under a seed dir."""
    checkpoint = Path(seed_path) / f"checkpoint-{number}"
    checkpoint.mkdir(parents=True, exist_ok=True)
    state = {"global_step": 50, "max_steps": 200}
    if payload is not None:
        state.update(payload)
    return write_json(checkpoint / RESUME_MARKER, state)


def test_cell_progress_numeric_suffix_ordering_not_lexical(tmp_path):
    """checkpoint-1000 beats checkpoint-999 — the suffix parses as an
    INT (lexical sort is WRONG and this pins it)."""
    running = seed_dir(tmp_path, "m", "t", 42)
    running.mkdir(parents=True)
    write_checkpoint(running, 999, {"global_step": 999})
    write_checkpoint(running, 1000, {"global_step": 1000})

    progress = sweep_monitor.cell_progress(running)

    assert progress == sweep_monitor.CellProgress(
        step=1000, max_steps=200, percent=100), (
        "the NUMERICALLY largest checkpoint suffix wins"
    )


def test_cell_progress_percent_math_rounds_and_clamps(tmp_path):
    """percent = round(step/max*100) clamped 0..100 — a step beyond max
    clamps to 100, a mid-flight ratio rounds honestly."""
    running = seed_dir(tmp_path, "m", "t", 42)
    running.mkdir(parents=True)
    write_checkpoint(running, 10, {"global_step": 50, "max_steps": 200})

    assert sweep_monitor.cell_progress(running).percent == 25

    write_checkpoint(running, 11, {"global_step": 250, "max_steps": 200})
    assert sweep_monitor.cell_progress(running).percent == 100, (
        "step beyond max clamps to 100, never a fabricated >100"
    )

    write_checkpoint(running, 12, {"global_step": -5, "max_steps": 200})
    assert sweep_monitor.cell_progress(running).percent == 0, (
        "a negative step clamps to 0"
    )


def test_cell_progress_absent_checkpoints_degrade_all_none(tmp_path):
    """A seed dir with NO checkpoint-* children parses nothing — the
    all-None CellProgress (the screen's honest indeterminate)."""
    queued = seed_dir(tmp_path, "m", "t", 42)
    queued.mkdir(parents=True)

    assert sweep_monitor.cell_progress(queued) == sweep_monitor.CellProgress(
        step=None, max_steps=None, percent=None)
    # an absent dir degrades identically (never an exception)
    assert sweep_monitor.cell_progress(
        tmp_path / "no-such-seed").step is None


def test_cell_progress_tolerant_damage_degrades_all_none(tmp_path):
    """A damaged (unparseable) trainer_state.json in the newest
    checkpoint degrades to all-None — a poisoned checkpoint can never
    crash the cadence or fabricate a number (T-c4j-01)."""
    running = seed_dir(tmp_path, "m", "t", 42)
    running.mkdir(parents=True)
    write_checkpoint(running, 5, {"global_step": 10})
    write_checkpoint(running, 6, {"global_step": 20})
    (running / "checkpoint-6" / RESUME_MARKER).write_text(
        "{damaged json", encoding="utf-8")

    assert sweep_monitor.cell_progress(running) == (
        sweep_monitor.CellProgress(
            step=None, max_steps=None, percent=None)), (
        "damage in the newest checkpoint degrades honestly"
    )


def test_cell_progress_non_int_fields_and_bad_max_degrade(tmp_path):
    """global_step/max_steps must be non-bool INTS (bools excluded); a
    max_steps <= 0 yields percent None (the divide guard) even when the
    step parsed."""
    running = seed_dir(tmp_path, "m", "t", 42)
    running.mkdir(parents=True)
    write_checkpoint(running, 3, {"global_step": True, "max_steps": 100})
    assert sweep_monitor.cell_progress(running).step is None, (
        "a bool global_step is not an int (the repo's bool-exclusion)"
    )

    write_checkpoint(running, 4, {"global_step": 10, "max_steps": 0})
    progress = sweep_monitor.cell_progress(running)
    assert progress.max_steps == 0
    assert progress.percent is None, "max_steps <= 0 never divides"


def test_entry_fold_states_and_seed_counts():
    """The fold (the _fold_frac_states semantics at seed level): any
    running -> running, any failed -> failed, all terminal -> completed,
    else queued; done counts TERMINAL seeds (completed/failed/skipped —
    the stats-line done convention) over the row's total."""
    def row(seeds):
        return sweep_monitor.CellRow(
            model="m", task="t",
            seeds=tuple(sweep_monitor.CellSeed(
                seed=number, state=state, fraction_states=None)
                for number, state in seeds))

    fold = sweep_monitor.entry_fold(row([
        (42, sweep_monitor.CELL_RUNNING), (43, sweep_monitor.CELL_QUEUED)]))
    assert (fold.state, fold.done, fold.total) == (
        sweep_monitor.CELL_RUNNING, 0, 2)

    fold = sweep_monitor.entry_fold(row([
        (42, sweep_monitor.CELL_COMPLETED), (43, sweep_monitor.CELL_FAILED)]))
    assert (fold.state, fold.done, fold.total) == (
        sweep_monitor.CELL_FAILED, 2, 2)

    fold = sweep_monitor.entry_fold(row([
        (42, sweep_monitor.CELL_COMPLETED),
        (43, sweep_monitor.CELL_SKIPPED)]))
    assert (fold.state, fold.done, fold.total) == (
        sweep_monitor.CELL_COMPLETED, 2, 2)

    fold = sweep_monitor.entry_fold(row([(42, sweep_monitor.CELL_QUEUED)]))
    assert (fold.state, fold.done, fold.total) == (
        sweep_monitor.CELL_QUEUED, 0, 1)


def test_entries_progress_running_seed_yields_completed_only_empty(
        tmp_path):
    """entries_progress walks the seed dirs once: a RUNNING seed with a
    checkpoint yields its {(model, task): CellProgress}; a completed-only
    root yields {} (progress parses ONLY for running rows — the 2s
    cadence stays light)."""
    # the running cell: fresh mtime inside the grace + a checkpoint
    running = seed_dir(tmp_path, "m-a", "t-1", 42)
    running.mkdir(parents=True)
    write_checkpoint(running, 7, {"global_step": 100, "max_steps": 400})
    set_mtime(running, NOW_REAL() - 10)
    # the completed cell: a record wins over any churn signal
    plant_record(tmp_path, "m-b", "t-2", 42,
                 make_record("m-b", "t-2", 42, status="completed"))
    age_tree(tmp_path, now=NOW_REAL(), skip=(running,),
             age_seconds=7200.0)

    progress = sweep_monitor.entries_progress(tmp_path)

    assert set(progress) == {("m-a", "t-1")}, (
        "only the running row carries progress"
    )
    assert progress[("m-a", "t-1")] == sweep_monitor.CellProgress(
        step=100, max_steps=400, percent=25)


def test_entries_progress_max_step_wins_across_running_seeds(tmp_path):
    """Several running seeds under one row: the MAX-step progress wins
    (the serial driver makes this rare; mgpu worker roots are separate
    roots)."""
    fresh = NOW_REAL() - 10
    seed_42 = seed_dir(tmp_path, "m", "t", 42)
    seed_43 = seed_dir(tmp_path, "m", "t", 43)
    for path in (seed_42, seed_43):
        path.mkdir(parents=True)
        set_mtime(path, fresh)
    write_checkpoint(seed_42, 3, {"global_step": 90})
    write_checkpoint(seed_43, 9, {"global_step": 400})
    age_tree(tmp_path, now=NOW_REAL(), skip=(seed_42, seed_43),
             age_seconds=7200.0)
    # age everything under the seed dirs EXCEPT the dirs themselves (the
    # churn signal rides the seed dir mtimes above)
    for path in sorted(Path(tmp_path).rglob("checkpoint-*")):
        set_mtime(path, NOW_REAL() - 7200)

    progress = sweep_monitor.entries_progress(tmp_path)

    assert progress[("m", "t")].step == 400, "the max-step seed wins"


# =====================================================================
# 261016-vxr (VXR-1): the checkpoint-pair ETA — CellProgress.eta_seconds
# derived from the TWO NEWEST checkpoint-*/trainer_state.json files
# (rate = Δglobal_step / Δtrainer_state.json FILE mtime over the newest
# pair; trainer_state.json carries NO wall-clock field, so the file
# mtime IS the cadence source). Every underivable shape degrades to
# None — the screen's honest dim dash, never a fabricated estimate.
# =====================================================================


def _pin_trainer_state_mtime(trainer_state_path, epoch):
    """os.utime one checkpoint's trainer_state.json to a controlled
    mtime (the ETA's wall-clock source — real file mtimes, never a
    monkeypatched clock)."""
    set_mtime(trainer_state_path, epoch)


def test_cell_progress_eta_from_two_newest_checkpoint_pair(tmp_path):
    """VXR-1: two checkpoints with controlled steps + FILE mtimes ->
    rate = Δstep/Δmtime over the newest PAIR, eta_seconds = remaining /
    rate (1000->1500 = 500 steps over 100s = 5 steps/s; 500 steps
    remain of max 2000 -> eta 100.0s)."""
    running = seed_dir(tmp_path, "m", "t", 42)
    running.mkdir(parents=True)
    old_state = write_checkpoint(
        running, 1000, {"global_step": 1000, "max_steps": 2000})
    new_state = write_checkpoint(
        running, 1500, {"global_step": 1500, "max_steps": 2000})
    base = NOW_REAL()
    _pin_trainer_state_mtime(old_state, base)
    _pin_trainer_state_mtime(new_state, base + 100.0)

    progress = sweep_monitor.cell_progress(running)

    assert progress == sweep_monitor.CellProgress(
        step=1500, max_steps=2000, percent=75, eta_seconds=100.0), (
        "eta = (max_steps - step) / (Δstep / Δmtime) over the newest pair"
    )


def test_cell_progress_eta_none_with_only_one_checkpoint(tmp_path):
    """One checkpoint parses steps/percent but carries NO cadence pair —
    eta_seconds None (the honest underivable)."""
    running = seed_dir(tmp_path, "m", "t", 42)
    running.mkdir(parents=True)
    write_checkpoint(running, 500, {"global_step": 500, "max_steps": 2000})

    progress = sweep_monitor.cell_progress(running)

    assert (progress.step, progress.max_steps, progress.percent) == (
        500, 2000, 25)
    assert progress.eta_seconds is None, (
        "a single checkpoint never yields a rate — never a guess"
    )


def test_cell_progress_eta_none_when_deltas_vanish(tmp_path):
    """Identical trainer_state mtimes (steps differ) or equal steps
    (mtimes differ) — both zero-denominator shapes degrade to None."""
    running = seed_dir(tmp_path, "m", "t", 42)
    running.mkdir(parents=True)

    # shape A: identical mtimes
    old_state = write_checkpoint(
        running, 1000, {"global_step": 1000, "max_steps": 2000})
    new_state = write_checkpoint(
        running, 1500, {"global_step": 1500, "max_steps": 2000})
    same = NOW_REAL()
    _pin_trainer_state_mtime(old_state, same)
    _pin_trainer_state_mtime(new_state, same)
    assert sweep_monitor.cell_progress(running).eta_seconds is None, (
        "zero Δmtime never divides")

    # shape B: equal steps (a newer checkpoint written at the same step;
    # the mtimes DO advance so only the step gate blocks)
    newest_state = write_checkpoint(
        running, 1600, {"global_step": 1500, "max_steps": 2000})
    _pin_trainer_state_mtime(newest_state, same + 100.0)
    assert sweep_monitor.cell_progress(running).eta_seconds is None, (
        "zero Δstep never yields a rate"
    )


def test_cell_progress_eta_none_when_second_newest_damaged(tmp_path):
    """A damaged second-newest trainer_state degrades ONLY the eta —
    the newest checkpoint's steps/percent still parse (tolerance is
    per-input, never all-or-nothing)."""
    running = seed_dir(tmp_path, "m", "t", 42)
    running.mkdir(parents=True)
    old_state = write_checkpoint(
        running, 1000, {"global_step": 1000, "max_steps": 2000})
    new_state = write_checkpoint(
        running, 1500, {"global_step": 1500, "max_steps": 2000})
    base = NOW_REAL()
    _pin_trainer_state_mtime(old_state, base)
    _pin_trainer_state_mtime(new_state, base + 100.0)
    old_state.write_text("{damaged json", encoding="utf-8")

    progress = sweep_monitor.cell_progress(running)

    assert (progress.step, progress.max_steps, progress.percent) == (
        1500, 2000, 75), "the newest checkpoint still parses"
    assert progress.eta_seconds is None, (
        "a damaged pair member kills the eta, never the steps"
    )


def test_cell_progress_eta_none_at_or_past_max_steps(tmp_path):
    """The newest step at/past its max (a run at the very end): nothing
    remains to estimate — eta None, never a zero or negative."""
    running = seed_dir(tmp_path, "m", "t", 42)
    running.mkdir(parents=True)
    old_state = write_checkpoint(
        running, 1000, {"global_step": 1000, "max_steps": 2000})
    new_state = write_checkpoint(
        running, 2000, {"global_step": 2000, "max_steps": 2000})
    base = NOW_REAL()
    _pin_trainer_state_mtime(old_state, base)
    _pin_trainer_state_mtime(new_state, base + 100.0)

    progress = sweep_monitor.cell_progress(running)

    assert progress.percent == 100
    assert progress.eta_seconds is None, "at the end nothing remains"


def test_entries_progress_carries_the_checkpoint_pair_eta(tmp_path):
    """VXR-1 passthrough: entries_progress's best-by-step pick carries
    the running seed's eta_seconds — the field threads through the
    boundary with no re-derivation."""
    running = seed_dir(tmp_path, "m-a", "t-1", 42)
    running.mkdir(parents=True)
    old_state = write_checkpoint(
        running, 1000, {"global_step": 1000, "max_steps": 2000})
    new_state = write_checkpoint(
        running, 1500, {"global_step": 1500, "max_steps": 2000})
    base = NOW_REAL()
    _pin_trainer_state_mtime(old_state, base)
    _pin_trainer_state_mtime(new_state, base + 100.0)
    set_mtime(running, base + 1)   # the fresh-churn running signal

    progress = sweep_monitor.entries_progress(tmp_path)

    assert progress[("m-a", "t-1")].eta_seconds == 100.0, (
        "the running seed's eta rides the entries passthrough"
    )


# =====================================================================
# 261020-9vh — the stale-checkpoint guard: at a REUSED root a running
# pair's newest checkpoint whose trainer_state.json FILE mtime predates
# the live process's start belongs to the PREVIOUS run — its numbers
# are never rendered (the all-None CellProgress drops the pair from
# entries_progress exactly like an unparseable checkpoint). The param
# absent keeps today's parse (the C4J-3 tolerant-seam precedent); only
# the NUMBERS go unknown — the cell's STATE derivation is untouched.
# =====================================================================


def test_cell_progress_stale_before_degrades_all_none(tmp_path):
    """The guard's four legs, in the maintainer's live shape: a
    checkpoint-19968-payload (step 19968 / max 49911 -> 40%) whose FILE
    mtime predates stale_before parses NOTHING; the SAME checkpoint is
    fresh relative to an earlier start (mtime >= start parses); the
    param absent keeps today's 40% (the pre-existing-caller contract);
    the boundary stale_before == mtime PARSES (mtime strictly < start is
    the only stale predicate)."""
    running = seed_dir(tmp_path, "m", "t", 42)
    running.mkdir(parents=True)
    state = write_checkpoint(
        running, 50, {"global_step": 19968, "max_steps": 49911})
    mtime = NOW_REAL() - 3600.0
    _pin_trainer_state_mtime(state, mtime)

    # STALE vs the live start: all-None — never the previous run's 40%
    assert sweep_monitor.cell_progress(
        running, stale_before=NOW_REAL()) == (
        sweep_monitor.CellProgress(
            step=None, max_steps=None, percent=None)), (
        "a checkpoint that predates the live process's start belongs "
        "to the PREVIOUS run — its numbers never render"
    )

    # FRESH vs an earlier start: the 40% parses (the checkpoint is the
    # current run's own)
    assert sweep_monitor.cell_progress(
        running, stale_before=mtime - 7200.0).percent == 40, (
        "a checkpoint newer than the live start parses normally"
    )

    # the param ABSENT: today's parse for every pre-existing caller
    assert sweep_monitor.cell_progress(running).percent == 40, (
        "no stale_before = the legacy C4J-3 parse, byte-identical"
    )

    # the BOUNDARY: stale_before == mtime parses (strict < is stale)
    assert sweep_monitor.cell_progress(
        running, stale_before=mtime).percent == 40, (
        "mtime == start is NOT stale — the predicate is strictly <"
    )


def test_entries_progress_live_started_guards_stale_checkpoints(tmp_path):
    """live_started threading: a RUNNING pair whose checkpoint is stale
    vs the root's live start is ABSENT from the map (exactly like an
    unparseable checkpoint); a second RUNNING pair with a FRESH
    checkpoint stays present under BOTH calls (the guard is selective,
    never a blanket progress outage); live_started=None returns the
    40% entry (the fallback every pre-existing caller rides)."""
    stale_seed = seed_dir(tmp_path, "m-a", "t-1", 42)
    stale_seed.mkdir(parents=True)
    stale_state = write_checkpoint(
        stale_seed, 50, {"global_step": 19968, "max_steps": 49911})
    _pin_trainer_state_mtime(stale_state, NOW_REAL() - 3600.0)
    fresh_seed = seed_dir(tmp_path, "m-b", "t-2", 42)
    fresh_seed.mkdir(parents=True)
    write_checkpoint(fresh_seed, 60, {"global_step": 60, "max_steps": 300})
    live_pairs = frozenset({("m-a", "t-1"), ("m-b", "t-2")})
    # the live start sits BETWEEN the two writes: after the stale
    # checkpoint (a previous run's save) and before the fresh one (the
    # live run's own save — the reused-root shape, in miniature)
    live_started = NOW_REAL() - 10.0

    guarded = sweep_monitor.entries_progress(
        tmp_path, live_pairs=live_pairs, live_started=live_started)

    assert set(guarded) == {("m-b", "t-2")}, (
        "the stale pair's entry is dropped; the fresh pair survives"
    )
    assert guarded[("m-b", "t-2")].percent == 20, (
        "the fresh pair's parsed percent is untouched by the guard"
    )

    fallback = sweep_monitor.entries_progress(
        tmp_path, live_pairs=live_pairs, live_started=None)

    assert set(fallback) == {("m-a", "t-1"), ("m-b", "t-2")}, (
        "live_started None = today's parse for BOTH running pairs"
    )
    assert fallback[("m-a", "t-1")].percent == 40, (
        "without live-start evidence the 40% entry returns (fallback)"
    )


# =====================================================================
# 261017-uwr (UWR-1 Task 2): the three-state derivation — CELL_INTERRUPTED
# + live_pairs threading + CellRow.newest_mtime (closes WINDOWS #34)
# =====================================================================


def test_interrupted_when_pair_not_live_checkpoint_residue(tmp_path):
    """The #34 pin: kill-left checkpoint residue (no record, no resume
    marker) derives RUNNING today for as long as the dir stands. With
    live_pairs MISSING the pair it derives INTERRUPTED; with the pair
    live it stays RUNNING; with live_pairs None (no evidence data —
    every pre-existing caller and fake) it stays RUNNING (legacy,
    byte-identical)."""
    root = tmp_path / "finetuned"
    residue = seed_dir(root, "model-a", "task-1", 42)
    write_checkpoint(residue, 520)  # kill-left checkpoint-*/ residue
    age_tree(root, now=NOW, age_seconds=7200.0)  # residue is STALE

    pair = ("model-a", "task-1")
    rows = sweep_monitor.cells_view(root, live_pairs=frozenset())
    assert rows[0].seeds[0].state == sweep_monitor.CELL_INTERRUPTED, (
        "no live sweep plans the pair — the residue reads interrupted, "
        "never a phantom running glyph"
    )

    rows = sweep_monitor.cells_view(root, live_pairs=frozenset({pair}))
    assert rows[0].seeds[0].state == sweep_monitor.CELL_RUNNING, (
        "a live sweep plans the pair — the same residue is honest churn"
    )

    rows = sweep_monitor.cells_view(root)  # live_pairs=None: legacy
    assert rows[0].seeds[0].state == sweep_monitor.CELL_RUNNING


def test_queued_vs_interrupted_by_pair_live_empty_and_newest_dirs(
        tmp_path):
    """Pair live + an inert empty dir -> QUEUED (the sweep will come);
    pair MISSING + the same dir -> INTERRUPTED; pair MISSING + the
    root's frontier-NEWEST dir (today's unconditional early-running
    leg) -> INTERRUPTED too — the newest-dir leg is gated like every
    other activity signal."""
    root = tmp_path / "finetuned"
    inert = seed_dir(root, "model-a", "task-1", 42)
    inert.mkdir(parents=True)
    newest = seed_dir(root, "model-a", "task-2", 42)
    newest.mkdir(parents=True)
    set_mtime(inert, NOW - 7200)
    set_mtime(newest, NOW - 5)  # the newest seed dir, fresh mtime
    pair = ("model-a", "task-1")

    rows = {row.task: row for row in sweep_monitor.cells_view(
        root, live_pairs=frozenset({pair}))}
    assert rows["task-1"].seeds[0].state == sweep_monitor.CELL_QUEUED, (
        "the live sweep plans task-1's pair — its inert dir is queued"
    )
    assert rows["task-2"].seeds[0].state == sweep_monitor.CELL_INTERRUPTED, (
        "task-2's pair is NOT planned — even the freshest dir reads "
        "interrupted while the evidence matrix misses it"
    )

    rows = {row.task: row for row in sweep_monitor.cells_view(
        root, live_pairs=frozenset())}
    assert rows["task-1"].seeds[0].state == sweep_monitor.CELL_INTERRUPTED
    assert rows["task-2"].seeds[0].state == sweep_monitor.CELL_INTERRUPTED, (
        "the frontier-newest early-running leg is gated: no live pair "
        "means the newest dir reads interrupted, not running"
    )

    rows = {row.task: row for row in sweep_monitor.cells_view(root)}
    assert rows["task-1"].seeds[0].state == sweep_monitor.CELL_QUEUED, (
        "legacy (live_pairs=None): the stale inert dir stays queued"
    )
    assert rows["task-2"].seeds[0].state == sweep_monitor.CELL_RUNNING, (
        "legacy (live_pairs=None): the fresh newest dir stays running"
    )


def test_records_and_markers_win_over_live_pairs_every_combination(
        tmp_path):
    """Readable record statuses (verbatim, terminal family) and the
    RESUME_MARKER skipped leg are UNAFFECTED by live_pairs in every
    combination — records always win first."""
    root = tmp_path / "finetuned"
    plant_record(root, "m-done", "t", 42, make_record("m-done", "t", 42))
    plant_record(root, "m-fail", "t", 42,
                 make_record("m-fail", "t", 42, status="failed"))
    marker = seed_dir(root, "m-skip", "t", 42)
    marker.mkdir(parents=True)
    (marker / RESUME_MARKER).write_text("{}", encoding="utf-8")
    plant_record(root, "m-odd", "t", 42,
                 make_record("m-odd", "t", 42, status="planned"))
    age_tree(root, now=NOW)

    states = {row.model: row.seeds[0].state for row in sweep_monitor.cells_view(
        root, live_pairs=frozenset())}
    assert states == {
        "m-done": sweep_monitor.CELL_COMPLETED,
        "m-fail": sweep_monitor.CELL_FAILED,
        "m-skip": sweep_monitor.CELL_SKIPPED,
        "m-odd": "planned",  # unrecognized statuses render VERBATIM
    }
    states_none = {row.model: row.seeds[0].state
                   for row in sweep_monitor.cells_view(root)}
    assert states == states_none, "records are live-blind"


def test_entry_fold_interrupted_leg_precedence():
    """The fold order gains the interrupted leg: running > failed >
    interrupted > completed (all completed|skipped, non-empty) >
    queued."""
    def fold(states):
        return sweep_monitor.entry_fold(sweep_monitor.CellRow(
            model="m", task="t",
            seeds=tuple(sweep_monitor.CellSeed(
                seed=42 + index, state=state, fraction_states=None)
                for index, state in enumerate(states)))).state

    assert fold([sweep_monitor.CELL_INTERRUPTED,
                 sweep_monitor.CELL_COMPLETED]) == (
        sweep_monitor.CELL_INTERRUPTED)
    assert fold([sweep_monitor.CELL_RUNNING,
                 sweep_monitor.CELL_INTERRUPTED]) == (
        sweep_monitor.CELL_RUNNING)
    assert fold([sweep_monitor.CELL_FAILED,
                 sweep_monitor.CELL_INTERRUPTED]) == (
        sweep_monitor.CELL_FAILED)
    assert fold([sweep_monitor.CELL_COMPLETED,
                 sweep_monitor.CELL_COMPLETED]) == (
        sweep_monitor.CELL_COMPLETED)
    assert fold([sweep_monitor.CELL_QUEUED,
                 sweep_monitor.CELL_QUEUED]) == (
        sweep_monitor.CELL_QUEUED)
    assert fold([sweep_monitor.CELL_INTERRUPTED,
                 sweep_monitor.CELL_QUEUED]) == (
        sweep_monitor.CELL_INTERRUPTED)


def test_fold_frac_states_interrupted_leg():
    """The fraction fold carries the same interrupted leg (a curve
    seed's frac_* children fold interrupted when nothing runs/fails)."""
    assert sweep_monitor._fold_frac_states([
        sweep_monitor.CELL_COMPLETED, sweep_monitor.CELL_INTERRUPTED,
    ]) == sweep_monitor.CELL_INTERRUPTED
    assert sweep_monitor._fold_frac_states([
        sweep_monitor.CELL_RUNNING, sweep_monitor.CELL_INTERRUPTED,
    ]) == sweep_monitor.CELL_RUNNING
    assert sweep_monitor._fold_frac_states([
        sweep_monitor.CELL_INTERRUPTED]) == sweep_monitor.CELL_INTERRUPTED
    assert sweep_monitor._fold_frac_states([]) == sweep_monitor.CELL_QUEUED


def test_cells_view_maintainer_scenario_three_families(tmp_path):
    """The maintainer's finetuned-smoke shape over one tmp root: two
    pairs with completed records, ONE live pair (fresh checkpoint dir
    + mtime), two dead pairs (stale checkpoint residue) — live_pairs =
    the one live pair folds the table to 2 completed / 1 running /
    2 interrupted (the screen's header counts and live-on-top ordering
    derive from exactly these folds)."""
    root = tmp_path / "finetuned-smoke"
    live_pair = ("model-live", "task-live")
    for model, task in (("model-done-1", "task-a"), ("model-done-2", "task-b")):
        plant_record(root, model, task, 42, make_record(model, task, 42))
    live_dir = seed_dir(root, *live_pair, 42)
    write_checkpoint(live_dir, 100, {"global_step": 80, "max_steps": 200})
    set_mtime(live_dir, NOW_REAL() - 10)  # fresh churn inside the grace
    for model in ("model-dead-1", "model-dead-2"):
        write_checkpoint(seed_dir(root, model, "task-c", 42), 300)
    age_tree(root, now=NOW_REAL(), skip=(live_dir,), age_seconds=7200.0)

    rows = {row.model: sweep_monitor.entry_fold(row) for row in
            sweep_monitor.cells_view(root, live_pairs=frozenset({live_pair}))}

    assert rows["model-done-1"].state == sweep_monitor.CELL_COMPLETED
    assert rows["model-done-2"].state == sweep_monitor.CELL_COMPLETED
    assert rows["model-live"].state == sweep_monitor.CELL_RUNNING
    assert rows["model-dead-1"].state == sweep_monitor.CELL_INTERRUPTED
    assert rows["model-dead-2"].state == sweep_monitor.CELL_INTERRUPTED
    counts = {state: 0 for state in ("completed", "running", "interrupted")}
    for fold in rows.values():
        if fold.state in counts:
            counts[fold.state] += 1
    assert counts == {"completed": 2, "running": 1, "interrupted": 2}


def test_cellrow_newest_mtime_filled_from_seed_dirs(tmp_path):
    """CellRow.newest_mtime = the MAX seed-dir mtime over the row's
    discovered seeds (cells_view fills it — the group-0 sort key);
    manifest-only/expected-only rows (no discovered seed dirs) default
    None; the field is additive so every pre-existing fake constructs
    unchanged."""
    root = tmp_path / "finetuned"
    seed_42 = seed_dir(root, "m", "t", 42)
    seed_43 = seed_dir(root, "m", "t", 43)
    seed_42.mkdir(parents=True)
    seed_43.mkdir(parents=True)
    set_mtime(seed_42, 1000.0)
    set_mtime(seed_43, 2000.0)
    write_json(root / MANIFEST_NAME, manifest_payload([
        manifest_cell("m-plan", "t-plan", 42, "planned")]))

    rows = {row.model: row for row in sweep_monitor.cells_view(root)}

    assert rows["m"].newest_mtime == 2000.0, "max over the row's seeds"
    assert rows["m-plan"].newest_mtime is None, (
        "no discovered seed dirs -> the additive default"
    )
    # the additive-default contract: pre-change constructions unchanged
    assert sweep_monitor.CellRow(
        model="m", task="t", seeds=()).newest_mtime is None


def test_entries_progress_parses_only_live_running_seeds(tmp_path):
    """The 2s cadence stays light under the three-state derivation: a
    DEAD interrupted pair with parseable checkpoints contributes
    NOTHING (its state is interrupted, progress parses only for
    live-running seeds); the live pair's checkpoints parse."""
    root = tmp_path / "finetuned"
    live_pair = ("m-live", "t")
    dead_dir = seed_dir(root, "m-dead", "t", 42)
    write_checkpoint(dead_dir, 500, {"global_step": 490, "max_steps": 500})
    live_dir = seed_dir(root, *live_pair, 42)
    write_checkpoint(live_dir, 5, {"global_step": 50, "max_steps": 500})
    set_mtime(live_dir, NOW_REAL() - 10)
    age_tree(root, now=NOW_REAL(), skip=(live_dir,), age_seconds=7200.0)

    progress = sweep_monitor.entries_progress(
        root, live_pairs=frozenset({live_pair}))

    assert set(progress) == {live_pair}, (
        "the dead interrupted pair parses nothing even though its "
        "checkpoints are parseable"
    )
    assert progress[live_pair].step == 50


def test_frontier_scan_threads_live_pairs_states(tmp_path):
    """frontier_scan threads live_pairs into the per-seed states (the
    same three-state derivation on the 2s pass) while its ROOT-level
    classification keeps the D-03 three states."""
    root = tmp_path / "finetuned"
    residue = seed_dir(root, "model-a", "task-1", 42)
    write_checkpoint(residue, 100)
    age_tree(root, now=NOW, age_seconds=7200.0)

    snapshot = sweep_monitor.frontier_scan(
        root, live_roots=(), now=NOW, live_pairs=frozenset())
    assert snapshot.cell_states[("model-a", "task-1", 42)] == (
        sweep_monitor.CELL_INTERRUPTED)
    assert snapshot.state == sweep_monitor.SWEEP_ARTIFACTS_ONLY

    snapshot = sweep_monitor.frontier_scan(
        root, live_roots=(), now=NOW,
        live_pairs=frozenset({("model-a", "task-1")}))
    assert snapshot.cell_states[("model-a", "task-1", 42)] == (
        sweep_monitor.CELL_RUNNING)

    snapshot = sweep_monitor.frontier_scan(root, live_roots=(), now=NOW)
    assert snapshot.cell_states[("model-a", "task-1", 42)] == (
        sweep_monitor.CELL_RUNNING), "live_pairs=None: legacy"


def test_full_scan_live_root_with_stale_manifest_classifies_running(
        tmp_path):
    """261018-08g (SOAK-3/F2): live evidence WINS over a stale manifest
    — a re-run at a root that already holds a finished sweep_manifest
    classifies RUNNING (done from terminal records, total None) for the
    whole live run. The planning probe pinned the OLD answer (finished
    2/2 — the live re-run invisible at the sweep level); this test
    inverts it. Re-run-at-same-root is the default workflow
    (output_root persists in run_config.json)."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42))
    plant_record(root, "model-a", "task-1", 43,
                 make_record("model-a", "task-1", 43))
    cells = [
        manifest_cell("model-a", "task-1", 42, "completed"),
        manifest_cell("model-a", "task-1", 43, "completed"),
    ]
    write_json(root / MANIFEST_NAME, manifest_payload(cells))
    age_tree(root)

    result = sweep_monitor.full_scan(
        roots=[root], live_roots=[root], now=NOW)

    row = sweep_row(result, root)
    assert row.state == "running", (
        "a live re-run at a manifest-holding root must never read "
        "finished off the stale manifest (the soak FINDING 2)"
    )
    assert row.total is None, "the live re-run's total is unknown"
    assert row.done == 2, "terminal records carry the done count"
    # the watermark still records so the churn comparison stays armed
    assert result.watermarks[str(root.resolve())] == NOW - 7200.0


def test_full_scan_non_live_manifest_root_still_finished_verbatim(
        tmp_path):
    """The ordering regression's other leg: the SAME manifest-holding
    root WITHOUT live evidence keeps today's byte-identical finished
    classification with the manifest's own counts (the live-first rule
    must not leak into the non-live path)."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42))
    cells = [
        manifest_cell("model-a", "task-1", 42, "completed"),
        manifest_cell("model-a", "task-1", 43, "planned"),
    ]
    write_json(root / MANIFEST_NAME, manifest_payload(cells))
    age_tree(root)

    result = sweep_monitor.full_scan(roots=[root], now=NOW)

    row = sweep_row(result, root)
    assert row.state == "finished"
    assert row.total == 2
    assert row.done == 1, "planned never counts toward done"


def test_full_scan_live_root_with_churn_keeps_running_verdict(
        tmp_path):
    """Ordering guard: a live root that ALSO carries fresh churn (mtime
    within the grace window) keeps the running verdict — the live branch
    and the churn signal agree, and the hoist must never regress the
    churn path for live roots."""
    root = tmp_path / "finetuned"
    record = plant_record(root, "model-a", "task-1", 42,
                          make_record("model-a", "task-1", 42))
    set_mtime(record, NOW)  # churn: fresh mtime

    result = sweep_monitor.full_scan(
        roots=[root], live_roots=[root], now=NOW)

    row = sweep_row(result, root)
    assert row.state == "running"
    assert row.total is None


# =====================================================================
# 261018-toe (slot-5 [e] Task 1): the incomplete-pairs derivation +
# the rerun_lane alias-dir fallback leg — both pure, both fed by the
# live-evidence-threaded cells_view output the screen's service seam
# produces (the presentation-tier contract: the screen never reads the
# tree itself, so the derivation consumes the ROWS, never the root).
# =====================================================================


def test_incomplete_pairs_view_failed_and_interrupted_only(tmp_path):
    """The [e] derivation's core pin: over a dead root's folded cells,
    exactly the FAILED and INTERRUPTED rows contribute their (model,
    task) pairs — completed, skipped, queued, and running rows
    contribute nothing — sorted deterministically, distinct."""
    root = tmp_path / "finetuned"
    # failed: a readable record
    plant_record(root, "model-a", "task-1", 42,
                 make_record("model-a", "task-1", 42, status="failed"))
    # interrupted: kill-left checkpoint residue (no record, no marker)
    write_checkpoint(seed_dir(root, "model-b", "task-2", 42), 120)
    # completed + skipped: never re-run by [e]
    plant_record(root, "model-c", "task-3", 42,
                 make_record("model-c", "task-3", 42))
    marker = seed_dir(root, "model-d", "task-4", 42)
    marker.mkdir(parents=True)
    (marker / RESUME_MARKER).write_text("{}", encoding="utf-8")
    age_tree(root, age_seconds=2000.0)  # the whole tree is STALE

    # the dead-root read: the strict-miss empty live-pair set is what
    # derives interrupted for the residue (the uwr leg)
    cells = sweep_monitor.cells_view(root, live_pairs=frozenset())
    assert sweep_monitor.incomplete_pairs_view(cells) == (
        ("model-a", "task-1"), ("model-b", "task-2")), (
        "exactly the failed + interrupted pairs, sorted + distinct"
    )

    # the LIVE read over the same tree: the residue derives running and
    # contributes nothing — [e] never enumerates a running pair
    cells = sweep_monitor.cells_view(
        root, live_pairs=frozenset({("model-b", "task-2")}))
    assert sweep_monitor.incomplete_pairs_view(cells) == (
        ("model-a", "task-1"),), (
        "a pair a live sweep plans is running, never incomplete"
    )

    # the legacy read (live_pairs=None — no evidence data): the residue
    # derives running under the activity semantics; only the failed pair
    cells = sweep_monitor.cells_view(root)
    assert sweep_monitor.incomplete_pairs_view(cells) == (
        ("model-a", "task-1"),)


def test_incomplete_pairs_view_alias_names_and_distinct_sorted(tmp_path):
    """Model identity passes through VERBATIM (alias names included) and
    the pair set is distinct + sorted even when two seeds of one pair
    are separately incomplete."""
    root = tmp_path / "finetuned"
    plant_record(root, "model-a+lora", "task-1", 42,
                 make_record("model-a+lora", "task-1", 42, status="failed"))
    write_checkpoint(seed_dir(root, "model-a+lora", "task-1", 43), 120)
    write_checkpoint(seed_dir(root, "model-a+lora", "task-0", 43), 120)
    age_tree(root, age_seconds=2000.0)

    cells = sweep_monitor.cells_view(root, live_pairs=frozenset())
    assert sweep_monitor.incomplete_pairs_view(cells) == (
        ("model-a+lora", "task-0"), ("model-a+lora", "task-1")), (
        "the alias name verbatim; two seeds of one pair fold to ONE pair"
    )


def test_rerun_lane_alias_dir_fallback_for_interrupted_roots(tmp_path):
    """261018-toe: an INTERRUPTED root has no manifest and no failures
    file (both land only at sweep end), so the [e] lane recovers peft
    from the discovered model-dir names' +lora/+ia3 suffixes — the same
    two-suffix vocabulary run_sweep.load_failure_pairs strips; a plain
    root keeps the honest none/none."""
    lora_root = tmp_path / "lora-root"
    write_checkpoint(seed_dir(lora_root, "model-a+lora", "task-1", 42), 120)
    assert sweep_monitor.rerun_lane(lora_root) == ("lora", "none"), (
        "the alias dir name recovers the lane for an interrupted root"
    )

    ia3_root = tmp_path / "ia3-root"
    write_checkpoint(seed_dir(ia3_root, "model-b+ia3", "task-1", 42), 120)
    assert sweep_monitor.rerun_lane(ia3_root) == ("ia3", "none")

    plain_root = tmp_path / "plain-root"
    write_checkpoint(seed_dir(plain_root, "model-c", "task-1", 42), 120)
    assert sweep_monitor.rerun_lane(plain_root) == ("none", "none"), (
        "no suffix anywhere — the honest none lane (head/probe/curve are "
        "manifest-only, not dir-recoverable)"
    )


def test_rerun_lane_failures_speak_over_the_dir_fallback(tmp_path):
    """Source order: the failures entries' alias/base pair wins over the
    discovered dir names — every pre-existing manifest/failures branch
    stays byte-identical; the dir scan is only the LAST leg for
    interrupted roots (first match wins inside it)."""
    root = tmp_path / "finetuned"
    write_json(root / FAILURES_NAME, [
        {"model": "model-a+lora", "base_model": "model-a",
         "task": "task-1", "seed": 42, "output_dir": "/x",
         "error": "boom"},
    ])
    # a DIFFERENT suffix sits in the dir names — the failures spoke lora
    write_checkpoint(seed_dir(root, "model-a+ia3", "task-1", 42), 120)

    assert sweep_monitor.rerun_lane(root) == ("lora", "none"), (
        "the failures entry is the authoritative peft source; the dir "
        "fallback never overrides a branch that already spoke"
    )
