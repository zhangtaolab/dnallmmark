"""
Unit tests for ``pipeline/run_sweep.py`` (F2 / REV-02).

Every behavior bullet of the plan's Task 2 is pinned here:

- **dry-run enumeration** — explicit --models/--tasks/--seeds with --dry-run
  writes ONLY ``sweep_manifest.json``: exactly the planned cells in sorted
  order, each with its planned seed-isolated outdir; no subprocess launched,
  no seed directory created under the output root;
- **manifest determinism** — two consecutive dry-runs over the same inputs
  produce byte-identical ``sweep_manifest.json`` files (sorted iteration,
  ``sort_keys=True, indent=4, ensure_ascii=False``);
- **record semantics via the injectable fake executor** — a fake that writes
  ``final_metrics.json`` into the cell dir yields status ``completed`` with
  metrics copied VERBATIM (suite-native keys untouched — translation is
  REV-03's job); a fake that raises yields status ``failed`` with the error
  string recorded and an entry in the failures manifest; a fake that exits
  0 WITHOUT writing ``final_metrics.json`` is likewise ``failed`` with a
  missing-metrics error and a failures entry (CR-02:
  run_finetune.py's blind-except isolation makes training failures exit
  0, so the missing file is the failure signal); a fake that writes a
  TRUNCATED ``final_metrics.json`` fails only that cell — the sweep
  continues, the remaining cells still run, and the manifest is still
  written (WR-11: child-data corruption is a failed cell, not a driver
  bug that aborts the sweep); a pre-existing
  ``trainer_state.json`` yields status ``skipped`` with NO executor
  invocation — and the skip is seed-scoped (seed 43 still runs when seed
  42's marker exists in the sibling dir) and never overwrites the
  skipped cell's existing run_record.json (WR-12: the previous run's
  record is the provenance; the manifest reports this run's view);
- **subprocess contract** — the real launch path (captured argv, never
  executed) passes --target_model/--target_dataset/--seed/--output_dir as
  separate argv elements of a LIST with cwd set to this repo's pipeline
  directory — never a shell string;
- **registry-derived defaults** — default enumeration derives the matrix
  from ``models_info.json`` keys x truthy-``Train`` ``datasets_info.json``
  entries (the unified D-10 registries), honoring --models/--tasks filters;
- **filter validation** — a --models/--tasks name absent from the
  registries (or a requested task with falsy ``Train``) exits non-zero
  listing the names instead of silently enumerating an empty matrix that
  reports a successful 0-cell sweep (WR-07);
- **degenerate flag values** — a PROVIDED --models/--tasks/--seeds whose
  value contains only separators/whitespace (``--models ,``, ``--models ""``,
  ``--seeds ,``) exits non-zero naming the flag and its raw value instead of
  degrading: an empty filter list is falsy, which both _validate_filters'
  early return and enumerate_matrix's ``if models_filter:`` treat as "no
  filter" (silently enumerating the FULL registry matrix), and an empty seed
  set runs 0 cells and exits 0 (WR-14); an ABSENT --models/--tasks keeps
  full-matrix semantics.
- **priority ordering (05-04, E2' degradation order)** — with NO
  --priority-file the enumeration order is byte-identical to the sorted()
  default (a frozen expected list); with a priorities file the ranked
  (model, task) cells enumerate FIRST (tier index, then entry specificity,
  as the primary sort key composed over the sorted() fallback — seeds stay
  adjacent within a cell), the committed ``pipeline/sweep_priorities.json``
  drives the PIPE-03 E2E pair first and the maintainer-curated tier-2 arena
  representatives second over a registry holding the real names, and
  run_matrix executes cells in the GIVEN order (the fake executor's
  invocation order preserves the full degradation order: tier 1, then every
  cell of the tier-2 representatives, then the sorted() fallback);
- **failures-manifest re-run (05-04)** — ``--from-failures`` enumerates
  exactly the failed (model, task) pairs' cells across ALL requested seeds;
  a clean manifest yields an EXPLICIT zero-cell run with a clear message
  (never a silent full sweep);
- **from-failures x peft (MED-01, phase-06 review)** — failure entries
  record the BASE registry name (``base_model``) beside the alias cell
  identity, so a ``--peft`` sweep's own manifest feeds back through
  ``--from-failures``: with the same ``--peft`` mode the failed ALIAS
  cells re-enumerate (the join runs on base names, the alias re-derives
  from the re-run's mode); legacy alias-only entries recover via a known
  suffix strip, and a name still unknown after the strip fails loudly;
- **operator-input validation (T-05-09)** — unknown model/task names,
  wrong JSON structure, or an unreadable/unparseable --priority-file /
  --from-failures file exits non-zero with ALL problems listed
  (the _validate_filters discipline), before any cell is enumerated.
- **--curve fraction expansion (06-05, SC-6/REV-08 F8)** — a comma
  fraction list in (0, 1] validates fail-fast collect-all (parse errors
  and bounds listed together, duplicates collapse, sorted ascending);
  each (model, task, seed) cell expands to one 4-tuple cell per fraction
  with output dirs {root}/{model}/{task}/seed_{seed}/frac_{f}/ — frac
  dirs nest UNDER the seed dir, NEVER beside it (the no-sibling layout
  lock: the trainer_state.json resume marker is fraction-scoped); each
  cell's argv appends --train_fraction <f> as a separate LIST element;
  run_record.json gains a train_fraction field (float for curve cells,
  null otherwise); --curve composes with --peft (alias cells expand
  across fractions) and --dry-run manifests enumerate frac cells
  byte-deterministically; extract_curve_points() harvests the (step,
  eval-metrics) learning-curve points from a trainer_state.json
  log_history (pure, CPU-side, synthetic-fixture tested).

The runner is stdlib-only and never imports torch/dnallm; no test executes
the real subprocess (the argv test monkeypatches ``subprocess.run``).

See also:
    ``pipeline/run_sweep.py`` — the driver under test.
    ``tests/test_run_finetune_contracts.py`` — the seed-isolated layout
    contract both sides of this seam must agree on.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import run_sweep  # conftest puts pipeline/ on sys.path

SUITE_NATIVE_METRICS = {
    "eval_AUROC": 0.9123,
    "eval_pearsonr": 0.5,
    "eval_loss": 0.234,
}


def write_registry(root, models, datasets):
    """Materialize unified-registry fixtures under ``root``."""
    (root / "models_info.json").write_text(
        json.dumps(models), encoding="utf-8")
    (root / "datasets_info.json").write_text(
        json.dumps(datasets), encoding="utf-8")


def make_registry(tmp_path):
    """Build a 3-model x 3-task registry fixture (task-y has Train=0)."""
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    write_registry(
        registry_dir,
        models={
            "model-a": {"Model_name": "model-a", "Model_path": "models/a"},
            "model-b": {"Model_name": "model-b", "Model_path": "models/b"},
            "model-c": {"Model_name": "model-c", "Model_path": "models/c"},
        },
        datasets={
            "task-x": {"Dataset_name": "task-x", "Train": 100, "Dev": 10},
            "task-y": {"Dataset_name": "task-y", "Train": 0, "Dev": 0},
            "task-z": {"Dataset_name": "task-z", "Train": 50, "Dev": 5},
        },
    )
    return registry_dir


def run_cli(monkeypatch, argv):
    """Invoke ``run_sweep.main()`` with a patched argv; return the argv."""
    full_argv = ["run_sweep.py", *argv]
    monkeypatch.setattr(sys, "argv", full_argv)
    run_sweep.main()
    return full_argv


def flag_value(argv, flag):
    """Return the argv element immediately following ``flag``."""
    assert flag in argv, f"{flag} missing from argv: {argv!r}"
    return argv[argv.index(flag) + 1]


def test_enumerate_matrix_derives_from_registries_and_filters(tmp_path):
    """Default enumeration = models_info keys x truthy-Train dataset
    entries, sorted; --models/--tasks comma filters narrow it."""
    registry_dir = make_registry(tmp_path)
    assert run_sweep.enumerate_matrix(None, None, [42], registry_dir) == [
        ("model-a", "task-x", 42), ("model-a", "task-z", 42),
        ("model-b", "task-x", 42), ("model-b", "task-z", 42),
        ("model-c", "task-x", 42), ("model-c", "task-z", 42),
    ]
    assert run_sweep.enumerate_matrix(
        ["model-a", "model-c"], ["task-x"], [42], registry_dir
    ) == [
        ("model-a", "task-x", 42),
        ("model-c", "task-x", 42),
    ]


def test_dry_run_writes_only_the_planned_manifest(tmp_path, monkeypatch):
    """--dry-run enumerates the matrix and writes ONLY sweep_manifest.json:
    4 planned cells in sorted order with seed-isolated outdirs, no seed
    directories, no run records, no failures manifest."""
    registry_dir = make_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    run_cli(monkeypatch, [
        "--models", "model-a,model-b",
        "--tasks", "task-x",
        "--seeds", "42,43",
        "--dry-run",
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ])
    manifest_path = out_root / "sweep_manifest.json"
    assert manifest_path.is_file(), "dry-run must write sweep_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [(c["model"], c["task"], c["seed"]) for c in manifest["cells"]] == [
        ("model-a", "task-x", 42), ("model-a", "task-x", 43),
        ("model-b", "task-x", 42), ("model-b", "task-x", 43),
    ]
    assert all(c["status"] == "planned" for c in manifest["cells"])
    assert "seed_42" in manifest["cells"][0]["output_dir"]
    assert "seed_43" in manifest["cells"][1]["output_dir"]
    # the manifest is the ONLY artifact: no cell dirs, no records
    assert not list(out_root.rglob("seed_*")), (
        "dry-run must not create seed directories"
    )
    assert not list(out_root.rglob("run_record.json"))
    assert not list(out_root.rglob("sweep_failures.json"))


def test_dry_run_manifest_is_byte_deterministic(tmp_path, monkeypatch):
    """Two consecutive dry-runs over the same inputs produce byte-identical
    sweep_manifest.json files (sorted iteration, sort_keys serialization)."""
    registry_dir = make_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    argv = [
        "--models", "model-a",
        "--tasks", "task-x,task-z",
        "--seeds", "42,43",
        "--dry-run",
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ]
    run_cli(monkeypatch, argv)
    first = (out_root / "sweep_manifest.json").read_bytes()
    run_cli(monkeypatch, argv)
    second = (out_root / "sweep_manifest.json").read_bytes()
    assert first == second, (
        "two dry-runs over the same inputs must produce byte-identical "
        "manifests — timestamps/git state must never enter the manifest"
    )


def test_run_matrix_completed_copies_metrics_verbatim(tmp_path):
    """A fake executor that writes final_metrics.json into the cell dir
    yields status completed with metrics copied VERBATIM — suite-native
    keys, no translation (eval_auroc->eval_AUROC mapping is REV-03's)."""
    out_root = tmp_path / "sweep-out"

    def fake_executor(model, task, seed, output_root, train_fraction=None):
        cell_dir = Path(output_root) / model / task / f"seed_{seed}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        (cell_dir / "final_metrics.json").write_text(
            json.dumps(SUITE_NATIVE_METRICS, indent=4), encoding="utf-8")

    records = run_sweep.run_matrix(
        [("model-a", "task-x", 42)], out_root, executor=fake_executor)
    assert len(records) == 1
    assert records[0]["status"] == "completed"
    assert records[0]["metrics"] == SUITE_NATIVE_METRICS, (
        "metrics must equal final_metrics.json keys verbatim"
    )
    disk = json.loads(
        (out_root / "model-a" / "task-x" / "seed_42" / "run_record.json")
        .read_text(encoding="utf-8"))
    assert disk["status"] == "completed"
    assert disk["metrics"] == SUITE_NATIVE_METRICS
    assert sorted(disk["metrics"]) == sorted(SUITE_NATIVE_METRICS), (
        "key identity must be verbatim — same key set, no renaming "
        "(on-disk order is sorted by the sort_keys write discipline; the "
        "in-memory record above preserves the final_metrics source order)"
    )
    manifest = json.loads(
        (out_root / "sweep_manifest.json").read_text(encoding="utf-8"))
    assert manifest["cells"][0]["status"] == "completed"
    failures = json.loads(
        (out_root / "sweep_failures.json").read_text(encoding="utf-8"))
    assert failures == [], (
        "the failures manifest is written on every run — an EMPTY list "
        "when every cell succeeds, never a stale file from a previous "
        "sweep over the same root (WR-06)"
    )


def test_run_matrix_failed_records_error_and_failures_manifest(tmp_path):
    """A fake executor that raises (the default executor raises
    subprocess.CalledProcessError under check=True) yields status failed,
    the error string recorded, and an entry in sweep_failures.json."""
    out_root = tmp_path / "sweep-out"

    def failing_executor(model, task, seed, output_root, train_fraction=None):
        raise subprocess.CalledProcessError(
            returncode=1, cmd="run_finetune.py",
            output="RuntimeError: CUDA out of memory")

    records = run_sweep.run_matrix(
        [("model-a", "task-x", 42)], out_root, executor=failing_executor)
    assert records[0]["status"] == "failed"
    assert records[0]["error"], "the error string must be recorded"
    assert "CalledProcessError" in records[0]["error"]
    failures = json.loads(
        (out_root / "sweep_failures.json").read_text(encoding="utf-8"))
    assert len(failures) == 1
    assert failures[0]["model"] == "model-a"
    assert failures[0]["task"] == "task-x"
    assert failures[0]["seed"] == 42
    assert failures[0]["error"] == records[0]["error"]
    disk = json.loads(
        (out_root / "model-a" / "task-x" / "seed_42" / "run_record.json")
        .read_text(encoding="utf-8"))
    assert disk["status"] == "failed"
    manifest = json.loads(
        (out_root / "sweep_manifest.json").read_text(encoding="utf-8"))
    assert manifest["cells"][0]["status"] == "failed"


def test_run_matrix_exit0_without_metrics_is_failure(tmp_path):
    """CR-02: a fake executor that returns normally but writes NO
    final_metrics.json (run_finetune.py's blind-except isolation swallows
    a training failure and still exits 0) is recorded failed with a
    missing-metrics error and a sweep_failures.json entry — never
    completed with null metrics."""
    out_root = tmp_path / "sweep-out"

    def silent_failure_executor(model, task, seed, output_root, train_fraction=None):
        # Exits 0, writes nothing — the dominant real-world failure mode
        # as seen from the driver side of the subprocess seam.
        return None

    records = run_sweep.run_matrix(
        [("model-a", "task-x", 42)], out_root, executor=silent_failure_executor)
    assert records[0]["status"] == "failed", (
        "an executor that exits 0 without writing final_metrics.json is a "
        "failed cell, not a completed one with null metrics"
    )
    assert records[0]["metrics"] is None
    assert "final_metrics.json is missing" in records[0]["error"]
    failures = json.loads(
        (out_root / "sweep_failures.json").read_text(encoding="utf-8"))
    assert len(failures) == 1
    assert failures[0]["model"] == "model-a"
    assert failures[0]["error"] == records[0]["error"]
    disk = json.loads(
        (out_root / "model-a" / "task-x" / "seed_42" / "run_record.json")
        .read_text(encoding="utf-8"))
    assert disk["status"] == "failed"
    manifest = json.loads(
        (out_root / "sweep_manifest.json").read_text(encoding="utf-8"))
    assert manifest["cells"][0]["status"] == "failed"


def test_run_matrix_corrupt_metrics_file_fails_cell_not_sweep(tmp_path):
    """WR-11: a final_metrics.json that is present but not valid JSON (the
    child writes it inside its blind-except scope, so a mid-write death —
    e.g. disk full — can leave a truncated file with the child still
    exiting 0) fails only THAT cell, recorded failed with a corrupt-file
    error and a failures-manifest entry; the sweep CONTINUES — the
    remaining cells still run and the manifest is still written — instead
    of an uncaught JSONDecodeError aborting the entire sweep."""
    out_root = tmp_path / "sweep-out"

    def corrupting_executor(model, task, seed, output_root, train_fraction=None):
        cell_dir = Path(output_root) / model / task / f"seed_{seed}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        if seed == 42:
            # Truncated JSON — exactly what a mid-write death leaves on
            # disk: present, non-empty, and not parseable.
            (cell_dir / "final_metrics.json").write_text(
                '{"eval_AUROC": 0.91', encoding="utf-8")
        else:
            (cell_dir / "final_metrics.json").write_text(
                json.dumps(SUITE_NATIVE_METRICS, indent=4), encoding="utf-8")

    records = run_sweep.run_matrix(
        [("model-a", "task-x", 42), ("model-a", "task-x", 43)],
        out_root, executor=corrupting_executor)
    statuses = {record["seed"]: record["status"] for record in records}
    assert statuses[42] == "failed", (
        "a corrupt final_metrics.json is a failed cell — child-data "
        "corruption, not a driver/executor bug that aborts the sweep"
    )
    assert statuses[43] == "completed", (
        "the sweep must continue past the corrupt cell — the remaining "
        "cells still run"
    )
    assert records[0]["metrics"] is None
    assert "corrupt" in records[0]["error"], (
        "the error must say the metrics file is corrupt, not attribute "
        "the failure to a swallowed training failure (the file exists)"
    )
    failures = json.loads(
        (out_root / "sweep_failures.json").read_text(encoding="utf-8"))
    assert len(failures) == 1
    assert failures[0]["seed"] == 42
    assert failures[0]["error"] == records[0]["error"]
    manifest = json.loads(
        (out_root / "sweep_manifest.json").read_text(encoding="utf-8"))
    assert [c["status"] for c in manifest["cells"]] == [
        "failed", "completed"], (
        "the manifest must be written even when a cell's metrics file is "
        "corrupt — pre-fix, the JSONDecodeError aborted the sweep before "
        "the manifest existed"
    )


def test_run_matrix_resume_marker_is_seed_scoped(tmp_path):
    """A pre-existing trainer_state.json marks exactly its own (model, task,
    seed) cell skipped with NO executor invocation — seed 43 still runs
    when seed 42's marker exists in the sibling dir (the G1 layout)."""
    out_root = tmp_path / "sweep-out"
    cell_42 = out_root / "model-a" / "task-x" / "seed_42"
    cell_42.mkdir(parents=True)
    (cell_42 / "trainer_state.json").write_text("{}", encoding="utf-8")

    invoked = []

    def fake_executor(model, task, seed, output_root, train_fraction=None):
        invoked.append((model, task, seed))
        cell_dir = Path(output_root) / model / task / f"seed_{seed}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        (cell_dir / "final_metrics.json").write_text("{}", encoding="utf-8")

    records = run_sweep.run_matrix(
        [("model-a", "task-x", 42), ("model-a", "task-x", 43)],
        out_root, executor=fake_executor)
    statuses = {record["seed"]: record["status"] for record in records}
    assert statuses[42] == "skipped"
    assert statuses[43] == "completed", (
        "the resume marker is seed-scoped — a different seed must never be "
        "skipped by a sibling seed's trainer_state.json (G1)"
    )
    assert invoked == [("model-a", "task-x", 43)], (
        "the executor must never be invoked for a cell whose "
        "trainer_state.json already exists"
    )
    skipped = json.loads(
        (cell_42 / "run_record.json").read_text(encoding="utf-8"))
    assert skipped["status"] == "skipped"


def test_resume_never_overwrites_existing_run_record(tmp_path):
    """WR-12: a resumed sweep's skipped cell NEVER overwrites the existing
    run_record.json — the record of the run that actually trained the cell
    (status completed, verbatim metrics, git commit, wall-clock times) is
    the provenance, "recorded once at observation time, never
    regenerated"; this run's skipped view is reported by the manifest
    only. A skipped cell with NO record yet (the seed-scoped test above:
    marker but no record) still gets a fresh one."""
    out_root = tmp_path / "sweep-out"

    def fake_executor(model, task, seed, output_root, train_fraction=None):
        # Mimic run_finetune.py's success artifacts: final_metrics.json
        # PLUS the trainer_state.json resume marker (written last — the
        # WR-13 ordering), without which run 2 below would have no
        # marker to skip on.
        cell_dir = Path(output_root) / model / task / f"seed_{seed}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        (cell_dir / "final_metrics.json").write_text(
            json.dumps(SUITE_NATIVE_METRICS, indent=4), encoding="utf-8")
        (cell_dir / "trainer_state.json").write_text("{}", encoding="utf-8")

    # Run 1: the cell trains and its completed record lands on disk.
    first = run_sweep.run_matrix(
        [("model-a", "task-x", 42)], out_root, executor=fake_executor)
    assert first[0]["status"] == "completed"
    record_path = (
        out_root / "model-a" / "task-x" / "seed_42" / "run_record.json")
    completed_record = json.loads(record_path.read_text(encoding="utf-8"))
    assert completed_record["status"] == "completed"
    assert completed_record["metrics"] == SUITE_NATIVE_METRICS
    assert completed_record["started_at"]
    assert completed_record["finished_at"]

    # Run 2 (resume): the trainer_state.json marker now exists, so the
    # cell is skipped — the executor must never run, and the on-disk
    # record must still be run 1's completed record, verbatim.
    invoked = []

    def never_executor(model, task, seed, output_root, train_fraction=None):
        invoked.append((model, task, seed))

    second = run_sweep.run_matrix(
        [("model-a", "task-x", 42)], out_root, executor=never_executor)
    assert invoked == [], "a skipped cell must never invoke the executor"
    assert second[0]["status"] == "skipped", (
        "the manifest reports THIS run's view of the cell: skipped"
    )
    assert json.loads(record_path.read_text(encoding="utf-8")) == (
        completed_record
    ), (
        "a skipped cell's existing run_record.json must be preserved "
        "verbatim — overwriting it with a skipped/metrics-null record "
        "destroys the only provenance linking the cell's metrics to the "
        "git commit and wall-clock times of the run that produced them "
        "(WR-12)"
    )
    manifest = json.loads(
        (out_root / "sweep_manifest.json").read_text(encoding="utf-8"))
    assert manifest["cells"][0]["status"] == "skipped", (
        "the manifest reflects this run's skipped view while the per-cell "
        "record keeps the original run's completed view — the two "
        "artifacts answer different questions"
    )


def test_launch_subprocess_builds_argv_list_with_pinned_cwd(monkeypatch):
    """The real launch path passes target_model/target_dataset/seed/
    output_dir as separate argv elements of a LIST (never a shell string)
    with cwd pinned to this repo's pipeline directory."""
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, returncode=0)

    monkeypatch.setattr(run_sweep.subprocess, "run", fake_run)
    run_sweep.launch_subprocess("model-a", "task-x", 42, "/tmp/sweep-root")
    argv = captured["argv"]
    assert isinstance(argv, list), (
        "the subprocess must be launched from an argv LIST, never a shell "
        "string (T-03-10: registry values must not pass through a shell)"
    )
    assert all(isinstance(element, str) for element in argv)
    assert flag_value(argv, "--target_model") == "model-a"
    assert flag_value(argv, "--target_dataset") == "task-x"
    assert flag_value(argv, "--seed") == "42"
    assert flag_value(argv, "--output_dir") == "/tmp/sweep-root"
    assert "run_finetune.py" in argv[1], (
        "the launch target is run_finetune.py itself"
    )
    assert captured["kwargs"]["cwd"] == run_sweep.PIPELINE_DIR, (
        "cwd must be pinned to the pipeline directory — "
        "finetune_config.yaml and the ./finetuned default are "
        "CWD-relative in run_finetune.py (research Pitfall 3)"
    )
    assert not captured["kwargs"].get("shell"), "shell=True is forbidden"


def test_cli_exits_nonzero_on_unknown_filter_names(tmp_path, monkeypatch):
    """WR-07: a typo'd --models/--tasks name exits non-zero listing the
    unmatched names instead of enumerating an empty matrix that writes a
    manifest and reports a successful 0-cell sweep."""
    registry_dir = make_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--models", "model-a,pant-dnamamba-6mer",
            "--tasks", "task-x,task-typo",
            "--seeds", "42",
            "--output-root", str(out_root),
            "--registry-dir", str(registry_dir),
        ])
    message = str(excinfo.value)
    assert "pant-dnamamba-6mer" in message, (
        "the unknown model name must be listed in the error"
    )
    assert "task-typo" in message, (
        "the unknown task name must be listed in the error"
    )
    assert not out_root.exists(), (
        "an unknown filter must abort before any output is written"
    )


def test_cli_exits_nonzero_on_requested_task_without_train_split(
        tmp_path, monkeypatch):
    """WR-07: a task explicitly requested via --tasks that has Train=0 is
    refused with a named error — the matrix can never run it, so dropping
    it silently would be a no-op reported as success."""
    registry_dir = make_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--tasks", "task-y",
            "--seeds", "42",
            "--output-root", str(out_root),
            "--registry-dir", str(registry_dir),
        ])
    message = str(excinfo.value)
    assert "task-y" in message, (
        "the untrainable task name must be listed in the error"
    )
    assert "Train" in message, (
        "the error must say WHY the task was refused (falsy Train)"
    )
    assert not out_root.exists(), (
        "the refusal must abort before any output is written"
    )


@pytest.mark.parametrize("flag,raw_value", [
    ("--models", ","),
    ("--models", ""),
    ("--tasks", ","),
    ("--tasks", ""),
])
def test_cli_exits_nonzero_on_provided_but_empty_filter_values(
        tmp_path, monkeypatch, flag, raw_value):
    """WR-14: a PROVIDED --models/--tasks whose value contains only
    separators/whitespace — e.g. --models , after shell indirection
    collapses --models "$A,$B" with both variables empty — exits non-zero
    naming the flag and its raw value. The stripped list is falsy, which
    _validate_filters' early return and enumerate_matrix's
    ``if models_filter:`` both treat as "no filter", so pre-fix the
    driver silently enumerated the FULL registry matrix (62 models x 50
    tasks = 3100 cells on the real registries) while the operator
    believed the run was scoped."""
    registry_dir = make_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            flag, raw_value,
            "--seeds", "42",
            "--dry-run",
            "--output-root", str(out_root),
            "--registry-dir", str(registry_dir),
        ])
    message = str(excinfo.value)
    assert flag in message, (
        "the error must name the offending flag so the operator knows "
        "which value to fix"
    )
    assert repr(raw_value) in message, (
        "the error must echo the flag's raw value"
    )
    assert not out_root.exists(), (
        "a provided-but-empty filter must abort before any output is "
        "written — never fall through to the full-registry matrix"
    )


@pytest.mark.parametrize("raw_seeds", ["", ","])
def test_cli_exits_nonzero_on_provided_but_empty_seed_values(
        tmp_path, monkeypatch, raw_seeds):
    """WR-14: --seeds is argparse-required, but any PRESENT value
    satisfies required=True — including "" or "," — which strips to an
    empty seed set. Pre-fix, run_matrix([]) wrote a manifest, printed
    "Sweep finished: 0 cell(s)", and exited 0: exactly the
    silently-successful no-op the WR-07 fail-fast was written to prevent.
    Provided-but-empty must exit non-zero naming the flag and its raw
    value."""
    registry_dir = make_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--models", "model-a",
            "--tasks", "task-x",
            "--seeds", raw_seeds,
            "--dry-run",
            "--output-root", str(out_root),
            "--registry-dir", str(registry_dir),
        ])
    message = str(excinfo.value)
    assert "--seeds" in message, (
        "the error must name the offending flag so the operator knows "
        "which value to fix"
    )
    assert repr(raw_seeds) in message, (
        "the error must echo the flag's raw value"
    )
    assert not out_root.exists(), (
        "an empty seed set must abort before any output is written — "
        "never write a 0-cell manifest and exit 0"
    )


def test_cli_absent_filters_keep_full_matrix_semantics(tmp_path, monkeypatch):
    """WR-14 guard-rail: OMITTING --models/--tasks keeps full-matrix
    semantics — only explicitly-provided-but-empty values fail fast. The
    default sweep must still enumerate every models_info.json key x
    truthy-Train datasets_info.json entry (task-y excluded: Train=0)."""
    registry_dir = make_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    run_cli(monkeypatch, [
        "--seeds", "42",
        "--dry-run",
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ])
    manifest = json.loads(
        (out_root / "sweep_manifest.json").read_text(encoding="utf-8"))
    assert [(c["model"], c["task"], c["seed"]) for c in manifest["cells"]] == [
        ("model-a", "task-x", 42), ("model-a", "task-z", 42),
        ("model-b", "task-x", 42), ("model-b", "task-z", 42),
        ("model-c", "task-x", 42), ("model-c", "task-z", 42),
    ], (
        "an absent --models/--tasks means ALL registry entries — the "
        "WR-14 fail-fast must fire only on provided-but-empty values, "
        "never on absent flags"
    )


# =====================================================================
# Priority ordering + failures-manifest re-run (05-04, REV-09 / E2')
# =====================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_PRIORITIES = REPO_ROOT / "pipeline" / "sweep_priorities.json"
# The PIPE-03 E2E task's unified-registry key (D-10 single source — the
# plan prose's "PlantCAD2__cross_species_leaf_on_off_translation" is the
# REQUIREMENTS shorthand; the registry key is what validation accepts).
E2E_TASK = "PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation"

# The maintainer-curated tier-2 arena representatives (Task 4 gate,
# 2026-10-10): one representative per arena — animal
# GENERanno-eukaryote-0.5b-base, plant PlantCAD2-Small-l24-d0768, microbe
# Omni-DNA-700M — chosen from the committed weighted_score arena leaders
# excluding the tier-1 pair (animal 0.799 / plant 1.000 / microbe 1.056).
# NEVER agent-invented (D-17/OQ4): this list mirrors the maintainer's
# declaration order; execution order within the tier is the sorted()
# fallback (bare names in one tier share a rank).
TIER2_REPRESENTATIVES = [
    "GENERanno-eukaryote-0.5b-base",
    "PlantCAD2-Small-l24-d0768",
    "Omni-DNA-700M",
]

# The frozen default order over the standard 3x2 fixture (both seeds): the
# sorted() enumeration that MUST stay byte-identical when no --priority-file
# is given (backward compatibility, determinism).
FROZEN_DEFAULT_ORDER = [
    ("model-a", "task-x", 42), ("model-a", "task-x", 43),
    ("model-a", "task-z", 42), ("model-a", "task-z", 43),
    ("model-b", "task-x", 42), ("model-b", "task-x", 43),
    ("model-b", "task-z", 42), ("model-b", "task-z", 43),
    ("model-c", "task-x", 42), ("model-c", "task-x", 43),
    ("model-c", "task-z", 42), ("model-c", "task-z", 43),
]


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=4), encoding="utf-8")
    return path


def _manifest_cells(out_root):
    manifest = json.loads(
        (out_root / "sweep_manifest.json").read_text(encoding="utf-8"))
    return [(c["model"], c["task"], c["seed"]) for c in manifest["cells"]]


def make_e2e_registry(tmp_path):
    """A registry holding the REAL E2E pair names, the three REAL tier-2
    arena-representative names, a bystander model, and a second task, so
    the committed priorities file validates and its tier-1-first,
    tier-2-second effect is observable against names that are not
    alphabetically convenient."""
    registry_dir = tmp_path / "registry-e2e"
    registry_dir.mkdir()
    write_registry(
        registry_dir,
        models={
            "plant-dnamamba-6mer": {
                "Model_name": "plant-dnamamba-6mer",
                "Model_path": "models/plant-dnamamba-6mer"},
            "PlantHelixSeek": {
                "Model_name": "PlantHelixSeek",
                "Model_path": "models/PlantHelixSeek"},
            "bystander-model": {
                "Model_name": "bystander-model",
                "Model_path": "models/bystander"},
            **{
                model: {"Model_name": model, "Model_path": f"models/{model}"}
                for model in TIER2_REPRESENTATIVES
            },
        },
        datasets={
            E2E_TASK: {"Dataset_name": E2E_TASK, "Train": 21894, "Dev": 10},
            "other__task": {"Dataset_name": "other__task", "Train": 50, "Dev": 5},
        },
    )
    return registry_dir


def test_default_enumeration_order_is_frozen_without_priority_file(
        tmp_path, monkeypatch):
    """With NO --priority-file the enumerated cell order is byte-identical
    to today's sorted() default — the frozen list below is the compatibility
    contract; priority ordering composes OVER it, never replaces it."""
    registry_dir = make_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    run_cli(monkeypatch, [
        "--seeds", "42,43",
        "--dry-run",
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ])
    assert _manifest_cells(out_root) == FROZEN_DEFAULT_ORDER, (
        "the no-priority-file enumeration order changed — backward "
        "compatibility is a hard contract"
    )


def test_priority_file_orders_ranked_cells_first_seeds_adjacent(
        tmp_path, monkeypatch):
    """A priorities file reorders the enumerated matrix: tier-1 cells (the
    {model, task} spec, then the bare model's other tasks) enumerate before
    everything else, seeds stay adjacent within a cell, and the remaining
    cells keep the sorted() fallback order. Tier 2 here is EMPTY (an empty
    tier is a valid file form — it ranks nothing)."""
    registry_dir = make_registry(tmp_path)
    priority_file = _write_json(tmp_path / "priorities.json", [
        [
            {"model": "model-c", "task": "task-z"},
            "model-b",
        ],
        [],
    ])
    out_root = tmp_path / "sweep-out"
    run_cli(monkeypatch, [
        "--seeds", "42,43",
        "--dry-run",
        "--priority-file", str(priority_file),
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ])
    assert _manifest_cells(out_root) == [
        # tier 1, entry 1: the {model, task} spec's cells, seeds adjacent
        ("model-c", "task-z", 42), ("model-c", "task-z", 43),
        # tier 1, entry 2: the bare model-b's cells (sorted fallback within
        # the same rank: task-x before task-z), seeds adjacent
        ("model-b", "task-x", 42), ("model-b", "task-x", 43),
        ("model-b", "task-z", 42), ("model-b", "task-z", 43),
        # unmatched (incl. model-c's OTHER task): the sorted() fallback order
        ("model-a", "task-x", 42), ("model-a", "task-x", 43),
        ("model-a", "task-z", 42), ("model-a", "task-z", 43),
        ("model-c", "task-x", 42), ("model-c", "task-x", 43),
    ], "priority tiers must enumerate before every other cell, seeds adjacent"


def test_priority_specificity_spec_before_bare_model_within_tier(
        tmp_path, monkeypatch):
    """Entry specificity is the intra-tier tiebreak: a {model, task} spec
    outranks the same tier's bare model name, so the spec's cells enumerate
    before the bare entry's other cells."""
    registry_dir = make_registry(tmp_path)
    priority_file = _write_json(tmp_path / "priorities.json", [
        ["model-b", {"model": "model-b", "task": "task-z"}],
    ])
    out_root = tmp_path / "sweep-out"
    run_cli(monkeypatch, [
        "--seeds", "42",
        "--dry-run",
        "--priority-file", str(priority_file),
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ])
    cells = _manifest_cells(out_root)
    model_b = [cell for cell in cells if cell[0] == "model-b"]
    assert model_b == [
        ("model-b", "task-z", 42),  # the spec: more specific, first
        ("model-b", "task-x", 42),  # the bare entry's other task
    ], "within one tier the {model, task} spec outranks the bare model name"
    # the bystander cells still enumerate after every ranked cell
    assert cells[-2:] == [("model-c", "task-x", 42), ("model-c", "task-z", 42)]


def test_committed_priorities_file_drives_e2e_pair_first(
        tmp_path, monkeypatch):
    """The committed pipeline/sweep_priorities.json validates against a
    registry holding the REAL E2E pair and tier-2 names and drives the full
    degradation order: the PIPE-03 pair's cells (both models x the E2E
    task, all seeds) before every other cell, then EVERY cell of the three
    tier-2 arena representatives, then the remaining cells in the sorted()
    fallback order."""
    registry_dir = make_e2e_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    run_cli(monkeypatch, [
        "--seeds", "42,43",
        "--dry-run",
        "--priority-file", str(COMMITTED_PRIORITIES),
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ])
    cells = _manifest_cells(out_root)
    assert len(cells) == 24  # 6 models x 2 tasks x 2 seeds
    # Tier 1 first: the E2E pair's four cells (both models, both seeds) —
    # in sorted fallback order within the tier, seeds adjacent.
    assert cells[:4] == [
        ("PlantHelixSeek", E2E_TASK, 42), ("PlantHelixSeek", E2E_TASK, 43),
        ("plant-dnamamba-6mer", E2E_TASK, 42),
        ("plant-dnamamba-6mer", E2E_TASK, 43),
    ]
    # Tier 2 second: EVERY cell of the three arena representatives (bare
    # names cover all tasks), seeds adjacent, sorted fallback order within
    # the shared tier rank.
    assert cells[4:16] == [
        (model, task, seed)
        for model in sorted(TIER2_REPRESENTATIVES)
        for task in [E2E_TASK, "other__task"]
        for seed in [42, 43]
    ]
    # Every remaining cell (the bystander's + the E2E models' other__task
    # cells) follows in the sorted() fallback order.
    assert set(cells[16:]) == {
        ("PlantHelixSeek", "other__task", 42), ("PlantHelixSeek", "other__task", 43),
        ("bystander-model", E2E_TASK, 42), ("bystander-model", E2E_TASK, 43),
        ("bystander-model", "other__task", 42),
        ("bystander-model", "other__task", 43),
        ("plant-dnamamba-6mer", "other__task", 42),
        ("plant-dnamamba-6mer", "other__task", 43),
    }
    assert cells[16:] == sorted(cells[16:])


def test_committed_priorities_file_content():
    """pipeline/sweep_priorities.json: tier 1 names exactly the pre-decided
    PIPE-03 E2E pair ({model, task} specs on the E2E task); tier 2 carries
    exactly the three maintainer-curated arena representatives (Task 4
    gate, 2026-10-10 — one per arena, in the maintainer's declaration
    order; never agent-invented, D-17/OQ4)."""
    tiers = json.loads(COMMITTED_PRIORITIES.read_text(encoding="utf-8"))
    assert isinstance(tiers, list) and len(tiers) == 2
    tier1, tier2 = tiers
    assert tier1 == [
        {"model": "plant-dnamamba-6mer", "task": E2E_TASK},
        {"model": "PlantHelixSeek", "task": E2E_TASK},
    ]
    assert tier2 == TIER2_REPRESENTATIVES, (
        "tier 2 is the maintainer's curated list — exactly one "
        "representative per arena (animal/plant/microbe), no additions, no "
        "reordering of tier 1"
    )


def test_tier2_representatives_are_real_registry_keys():
    """Every committed tier-2 name is an exact pipeline/models_info.json
    key — the fail-fast gate-disposition condition (a typo'd name would
    abort the real sweep at --priority-file validation, launch day)."""
    registry = json.loads(
        (REPO_ROOT / "pipeline" / "models_info.json").read_text(
            encoding="utf-8"))
    for model in TIER2_REPRESENTATIVES:
        assert model in registry, (
            f"tier-2 representative {model!r} is not a models_info.json "
            "key — the committed priorities file must name registry keys"
        )


def test_committed_priorities_degradation_order_fake_executor(tmp_path):
    """The committed priorities file drives the full E2' degradation order
    through run_matrix under a fake executor (the D-05 discipline — no real
    subprocess is ever launched): tier-1 E2E pair cells first, then EVERY
    cell of the three tier-2 arena representatives across both tasks (seeds
    adjacent), then the remaining cells in the sorted() fallback order.
    This is the degradation contract the maintainer's curation purchased:
    if the revision window degrades, the sweep has already produced the
    E2E pair, then one strong representative per arena."""
    registry_dir = make_e2e_registry(tmp_path)
    tiers = run_sweep.load_priority_tiers(
        str(COMMITTED_PRIORITIES), registry_dir)
    cells = run_sweep.enumerate_matrix(None, None, [42, 43], registry_dir)
    ordered = run_sweep.apply_priority_order(cells, tiers)
    out_root = tmp_path / "sweep-out"
    invoked = []

    def recording_executor(model, task, seed, output_root, train_fraction=None):
        invoked.append((model, task, seed))
        cell_dir = Path(output_root) / model / task / f"seed_{seed}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        (cell_dir / "final_metrics.json").write_text("{}", encoding="utf-8")

    run_sweep.run_matrix(ordered, out_root, executor=recording_executor)
    assert len(invoked) == 24, "6 models x 2 tasks x 2 seeds, every cell run"
    assert invoked == [
        # tier 1 — the PIPE-03 E2E pair ({model, task} specs, sorted
        # fallback within the rank), seeds adjacent within each cell
        ("PlantHelixSeek", E2E_TASK, 42),
        ("PlantHelixSeek", E2E_TASK, 43),
        ("plant-dnamamba-6mer", E2E_TASK, 42),
        ("plant-dnamamba-6mer", E2E_TASK, 43),
        # tier 2 — the three arena representatives as bare names: EVERY
        # cell of each model (both tasks), seeds adjacent, sorted()
        # fallback order within the shared tier rank
        ("GENERanno-eukaryote-0.5b-base", E2E_TASK, 42),
        ("GENERanno-eukaryote-0.5b-base", E2E_TASK, 43),
        ("GENERanno-eukaryote-0.5b-base", "other__task", 42),
        ("GENERanno-eukaryote-0.5b-base", "other__task", 43),
        ("Omni-DNA-700M", E2E_TASK, 42),
        ("Omni-DNA-700M", E2E_TASK, 43),
        ("Omni-DNA-700M", "other__task", 42),
        ("Omni-DNA-700M", "other__task", 43),
        ("PlantCAD2-Small-l24-d0768", E2E_TASK, 42),
        ("PlantCAD2-Small-l24-d0768", E2E_TASK, 43),
        ("PlantCAD2-Small-l24-d0768", "other__task", 42),
        ("PlantCAD2-Small-l24-d0768", "other__task", 43),
        # the remaining cells — the sorted() fallback order
        ("PlantHelixSeek", "other__task", 42),
        ("PlantHelixSeek", "other__task", 43),
        ("bystander-model", E2E_TASK, 42),
        ("bystander-model", E2E_TASK, 43),
        ("bystander-model", "other__task", 42),
        ("bystander-model", "other__task", 43),
        ("plant-dnamamba-6mer", "other__task", 42),
        ("plant-dnamamba-6mer", "other__task", 43),
    ], (
        "the executor invocation order must be the full degradation "
        "order: tier-1 E2E pair, then every tier-2 representative cell, "
        "then the sorted() fallback"
    )


def test_run_matrix_preserves_given_cell_order(tmp_path):
    """run_matrix executes cells in the GIVEN order (a priority-ordered
    list stays priority-ordered) instead of re-sorting — the fake executor's
    invocation order is the proof; nothing in this test launches a real
    subprocess (D-05)."""
    out_root = tmp_path / "sweep-out"
    invoked = []

    def recording_executor(model, task, seed, output_root, train_fraction=None):
        invoked.append((model, task, seed))
        cell_dir = Path(output_root) / model / task / f"seed_{seed}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        (cell_dir / "final_metrics.json").write_text("{}", encoding="utf-8")

    cells = [
        ("model-c", "task-x", 42),
        ("model-a", "task-z", 42),
        ("model-c", "task-z", 42),
    ]  # deliberately NOT sorted — a priority-ordered slice
    run_sweep.run_matrix(cells, out_root, executor=recording_executor)
    assert invoked == cells, (
        "run_matrix must preserve the caller's cell order — re-sorting "
        "here would destroy the --priority-file ordering"
    )


def _failures_manifest(tmp_path, entries):
    return _write_json(tmp_path / "sweep_failures.json", entries)


def test_from_failures_enumerates_exactly_failed_pairs_all_seeds(
        tmp_path, monkeypatch):
    """--from-failures with a manifest naming two failed (model, task)
    pairs enumerates exactly those pairs' cells across ALL requested seeds
    (the seed-scoped resume marker already skips completed cells; the
    filter exists to avoid re-enumerating ~9,300 cells and to guard against
    typo'd manual re-run filters)."""
    registry_dir = make_registry(tmp_path)
    failures = _failures_manifest(tmp_path, [
        {"model": "model-a", "task": "task-x", "seed": 42,
         "output_dir": "x", "error": "boom"},
        {"model": "model-c", "task": "task-z", "seed": 43,
         "output_dir": "y", "error": "boom"},
    ])
    out_root = tmp_path / "sweep-out"
    run_cli(monkeypatch, [
        "--seeds", "42,43",
        "--dry-run",
        "--from-failures", str(failures),
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ])
    assert _manifest_cells(out_root) == [
        ("model-a", "task-x", 42), ("model-a", "task-x", 43),
        ("model-c", "task-z", 42), ("model-c", "task-z", 43),
    ], "exactly the failed pairs' cells, every requested seed"


def test_from_failures_clean_manifest_yields_explicit_zero_cell_run(
        tmp_path, monkeypatch, capsys):
    """A CLEAN failures manifest (empty list — WR-06 writes one every run)
    yields an EXPLICIT zero-cell run with a clear message: the operator
    sees why zero cells enumerated; the driver must NEVER fall through to
    the full matrix (the silent-full-sweep hazard)."""
    registry_dir = make_registry(tmp_path)
    failures = _failures_manifest(tmp_path, [])
    out_root = tmp_path / "sweep-out"
    run_cli(monkeypatch, [
        "--seeds", "42,43",
        "--dry-run",
        "--from-failures", str(failures),
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ])
    assert _manifest_cells(out_root) == []
    captured = capsys.readouterr().out
    assert "clean" in captured, (
        "the zero-cell run must carry a clear message naming the clean "
        f"manifest — got: {captured!r}"
    )
    assert "0" in captured


def test_from_failures_unknown_keys_exit_nonzero_listing_all_problems(
        tmp_path, monkeypatch):
    """Unknown model/task names in a failures manifest exit non-zero with
    EVERY problem listed (the _validate_filters discipline) — a typo'd
    re-run filter must not silently enumerate the wrong (or full) matrix."""
    registry_dir = make_registry(tmp_path)
    failures = _failures_manifest(tmp_path, [
        {"model": "model-a", "task": "task-x", "seed": 42,
         "output_dir": "x", "error": "boom"},
        {"model": "ghost-model", "task": "task-x", "seed": 42,
         "output_dir": "x", "error": "boom"},
        {"model": "model-a", "task": "ghost-task", "seed": 42,
         "output_dir": "x", "error": "boom"},
    ])
    out_root = tmp_path / "sweep-out"
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--from-failures", str(failures),
            "--output-root", str(out_root),
            "--registry-dir", str(registry_dir),
        ])
    message = str(excinfo.value)
    assert "ghost-model" in message
    assert "ghost-task" in message
    assert not out_root.exists(), (
        "an invalid manifest must abort before any output is written"
    )


def test_from_failures_task_without_train_split_exits_nonzero(
        tmp_path, monkeypatch):
    """WR-02 (05 review): a failures manifest naming a task with falsy
    ``Train`` (task-y in the fixture) exits non-zero with a named error —
    the matrix can never run it, so accepting the pair would silently
    enumerate nothing for it while the operator believes it is re-run
    (the same refusal _validate_filters applies to --tasks)."""
    registry_dir = make_registry(tmp_path)
    failures = _failures_manifest(tmp_path, [
        {"model": "model-a", "task": "task-y", "seed": 42,
         "output_dir": "x", "error": "boom"},
    ])
    out_root = tmp_path / "sweep-out"
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--from-failures", str(failures),
            "--output-root", str(out_root),
            "--registry-dir", str(registry_dir),
        ])
    message = str(excinfo.value)
    assert "task-y" in message, (
        "the untrainable task name must be listed in the error"
    )
    assert "Train" in message, (
        "the error must say WHY the task was refused (falsy Train)"
    )
    assert not out_root.exists(), (
        "an invalid manifest must abort before any output is written"
    )


@pytest.mark.parametrize("payload", [
    {"model": "model-a", "task": "task-x", "seed": 42},   # not a list
    ["not-an-object"],
    [{"task": "task-x", "seed": 42}],                     # missing model
    [{"model": "model-a", "seed": 42}],                   # missing task
])
def test_from_failures_structure_errors_exit_nonzero(
        tmp_path, monkeypatch, payload):
    """A failures manifest with the wrong structure (not a list of objects
    carrying string model/task keys) exits non-zero instead of being
    misread."""
    registry_dir = make_registry(tmp_path)
    failures = _write_json(tmp_path / "sweep_failures.json", payload)
    with pytest.raises(SystemExit):
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--from-failures", str(failures),
            "--output-root", str(tmp_path / "out"),
            "--registry-dir", str(registry_dir),
        ])


@pytest.mark.parametrize("content", ["{not json", ""])
def test_from_failures_unreadable_or_unparseable_file_exits_nonzero(
        tmp_path, monkeypatch, content):
    """An unreadable (missing) or unparseable --from-failures file exits
    non-zero naming the file."""
    registry_dir = make_registry(tmp_path)
    with pytest.raises(SystemExit) as missing_info:
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--from-failures", str(tmp_path / "does-not-exist.json"),
            "--output-root", str(tmp_path / "out"),
            "--registry-dir", str(registry_dir),
        ])
    assert "does-not-exist.json" in str(missing_info.value)
    bad = tmp_path / "bad.json"
    bad.write_text(content, encoding="utf-8")
    with pytest.raises(SystemExit) as bad_info:
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--from-failures", str(bad),
            "--output-root", str(tmp_path / "out"),
            "--registry-dir", str(registry_dir),
        ])
    assert "bad.json" in str(bad_info.value)


# ===== from-failures x peft composition (MED-01, phase-06 review) =====

def test_peft_failure_entries_record_base_model_beside_alias(tmp_path):
    """A --peft sweep's sweep_failures.json entries carry BOTH the cell
    identity (the ALIAS — matches the cell dir and run_record) and the
    BASE registry name under ``base_model`` (MED-01: --from-failures
    validates against registry KEYS, so an alias-only entry is rejected
    as not-in-registry and a peft sweep could not be recovered)."""
    out_root = tmp_path / "sweep-out"

    def failing_executor(model, task, seed, output_root, train_fraction=None):
        raise subprocess.CalledProcessError(
            returncode=1, cmd="run_finetune.py", output="boom")

    records = run_sweep.run_matrix(
        [("model-a+lora", "task-x", 42), ("model-b+lora", "task-z", 42)],
        out_root, executor=failing_executor, peft="lora")
    assert all(r["status"] == "failed" for r in records)
    failures = json.loads(
        (out_root / "sweep_failures.json").read_text(encoding="utf-8"))
    assert [(f["model"], f["base_model"]) for f in failures] == [
        ("model-a+lora", "model-a"), ("model-b+lora", "model-b"),
    ], (
        "every failure entry must record the alias cell identity AND the "
        "base registry name (MED-01)"
    )


def test_from_failures_recovers_peft_sweep_alias_cells(tmp_path, monkeypatch):
    """The phase-06 MED-01 reproduction, fixed: feeding a --peft sweep's
    own sweep_failures.json back through --from-failures WITH the same
    --peft mode re-enumerates exactly the failed ALIAS cells (validation
    and the join run on base names; the alias re-derives from the re-run's
    --peft via enumerate_matrix) — previously this exited non-zero with
    \"model not in registry: 'model-a+lora'\"."""
    registry_dir = make_registry(tmp_path)
    failures = _failures_manifest(tmp_path, [
        {"model": "model-a+lora", "base_model": "model-a",
         "task": "task-x", "seed": 42, "output_dir": "x",
         "error": "boom"},
        {"model": "model-b+lora", "base_model": "model-b",
         "task": "task-z", "seed": 43, "output_dir": "y",
         "error": "boom"},
    ])
    out_root = tmp_path / "sweep-out"
    run_cli(monkeypatch, [
        "--seeds", "42,43",
        "--dry-run",
        "--peft", "lora",
        "--from-failures", str(failures),
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ])
    assert _manifest_cells(out_root) == [
        ("model-a+lora", "task-x", 42), ("model-a+lora", "task-x", 43),
        ("model-b+lora", "task-z", 42), ("model-b+lora", "task-z", 43),
    ], (
        "a lora manifest recovered with --peft lora must re-enumerate "
        "exactly the failed alias cells across every requested seed "
        "(MED-01)"
    )


def test_from_failures_legacy_alias_entry_recovers_via_suffix_strip(
        tmp_path, monkeypatch):
    """A legacy alias-only failure entry (no ``base_model`` — manifests
    written before the MED-01 fix) still recovers: the validator strips a
    known adapter suffix from ``model`` before refusing, mirroring
    build_argv's strip."""
    registry_dir = make_registry(tmp_path)
    failures = _failures_manifest(tmp_path, [
        {"model": "model-a+lora", "task": "task-x", "seed": 42,
         "output_dir": "x", "error": "boom"},
    ])
    out_root = tmp_path / "sweep-out"
    run_cli(monkeypatch, [
        "--seeds", "42",
        "--dry-run",
        "--from-failures", str(failures),
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ])
    # Without --peft on the re-run, the pairs enumerate as BASE cells —
    # the mode in play governs the alias re-derivation.
    assert _manifest_cells(out_root) == [("model-a", "task-x", 42)]
    # The stripped form is not a blanket accept: a name that stays
    # unknown after the strip still fails loudly.
    ghost = _failures_manifest(tmp_path, [
        {"model": "ghost+lora", "task": "task-x", "seed": 42,
         "output_dir": "x", "error": "boom"},
    ])
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--from-failures", str(ghost),
            "--output-root", str(tmp_path / "out2"),
            "--registry-dir", str(registry_dir),
        ])
    assert "ghost" in str(excinfo.value)


def test_from_failures_rejects_non_string_base_model(
        tmp_path, monkeypatch):
    """A structurally bad ``base_model`` (non-string) is a named problem,
    not a silent fall-through to the alias."""
    registry_dir = make_registry(tmp_path)
    failures = _failures_manifest(tmp_path, [
        {"model": "model-a+lora", "base_model": 7, "task": "task-x",
         "seed": 42, "output_dir": "x", "error": "boom"},
    ])
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--from-failures", str(failures),
            "--output-root", str(tmp_path / "out"),
            "--registry-dir", str(registry_dir),
        ])
    assert "base_model" in str(excinfo.value)


def test_priority_file_unknown_names_exit_nonzero_listing_all_problems(
        tmp_path, monkeypatch):
    """Unknown model/task names in a priorities file exit non-zero with
    every problem listed (registry-join key validation, T-05-09) — the file
    steers multi-day GPU execution order, so a typo must fail fast."""
    registry_dir = make_registry(tmp_path)
    priority_file = _write_json(tmp_path / "priorities.json", [
        ["ghost-model", {"model": "model-a", "task": "ghost-task"}],
    ])
    out_root = tmp_path / "sweep-out"
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--priority-file", str(priority_file),
            "--output-root", str(out_root),
            "--registry-dir", str(registry_dir),
        ])
    message = str(excinfo.value)
    assert "ghost-model" in message
    assert "ghost-task" in message
    assert not out_root.exists(), (
        "an invalid priorities file must abort before any output is written"
    )


def test_priority_file_task_without_train_split_exits_nonzero(
        tmp_path, monkeypatch):
    """WR-02 (05 review): a priority entry naming a task with falsy
    ``Train`` (task-y in the fixture) exits non-zero with a named error —
    the cell would never enumerate, so the maintainer would believe a
    cell is prioritized that can never run (silently inert; the same
    refusal _validate_filters applies to --tasks)."""
    registry_dir = make_registry(tmp_path)
    priority_file = _write_json(tmp_path / "priorities.json", [
        ["model-a", {"model": "model-b", "task": "task-y"}],
    ])
    out_root = tmp_path / "sweep-out"
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--priority-file", str(priority_file),
            "--output-root", str(out_root),
            "--registry-dir", str(registry_dir),
        ])
    message = str(excinfo.value)
    assert "task-y" in message, (
        "the untrainable task name must be listed in the error"
    )
    assert "Train" in message, (
        "the error must say WHY the task was refused (falsy Train)"
    )
    assert not out_root.exists(), (
        "an invalid priorities file must abort before any output is written"
    )


@pytest.mark.parametrize("payload,marker", [
    ({"tiers": []}, "list of tiers"),                       # not a list
    ([["model-a"], "model-b"], "tier 1"),                   # tier not a list
    ([[42]], "entry"),                                      # not str/dict
    ([[{"task": "task-x"}]], "model"),                      # spec missing model
    ([[{"model": "model-a", "task": "task-x", "why": "x"}]], "unknown key"),
    ([[{"model": "model-a", "task": 7}]], "task"),           # non-string task
])
def test_priority_file_structure_errors_exit_nonzero(
        tmp_path, monkeypatch, payload, marker):
    """A priorities file with the wrong structure exits non-zero — the JSON
    must be an ordered list of tiers, each a list of bare model names or
    {model, task} specs."""
    registry_dir = make_registry(tmp_path)
    priority_file = _write_json(tmp_path / "priorities.json", payload)
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--priority-file", str(priority_file),
            "--output-root", str(tmp_path / "out"),
            "--registry-dir", str(registry_dir),
        ])
    assert marker in str(excinfo.value), (
        f"the error must describe the structural problem ({marker}): "
        f"{excinfo.value}"
    )


@pytest.mark.parametrize("content", ["{not json", ""])
def test_priority_file_unparseable_json_exits_nonzero(
        tmp_path, monkeypatch, content):
    """An unparseable --priority-file exits non-zero naming the file."""
    registry_dir = make_registry(tmp_path)
    bad = tmp_path / "bad-priorities.json"
    bad.write_text(content, encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        run_cli(monkeypatch, [
            "--seeds", "42",
            "--dry-run",
            "--priority-file", str(bad),
            "--output-root", str(tmp_path / "out"),
            "--registry-dir", str(registry_dir),
        ])
    assert "bad-priorities.json" in str(excinfo.value)


# =====================================================================
# --peft threading (06-02, SC-6/REV-05 adapter lanes)
# =====================================================================

def test_peft_none_default_is_byte_identical_to_today(tmp_path):
    """--peft none (the default) changes nothing: enumerate_matrix emits
    base-name cells (the peft kwarg absent OR explicit 'none'), build_argv
    carries NO --peft/--save_model_name elements, and _new_record's peft
    field reads 'none' — a none-mode run is byte-for-byte the current
    behavior."""
    registry_dir = make_registry(tmp_path)
    default_cells = run_sweep.enumerate_matrix(
        ["model-a"], ["task-x"], [42], registry_dir)
    assert default_cells == [("model-a", "task-x", 42)]
    explicit_none = run_sweep.enumerate_matrix(
        ["model-a"], ["task-x"], [42], registry_dir, peft="none")
    assert explicit_none == default_cells, (
        "peft='none' must enumerate exactly the default (base-name) cells"
    )
    argv_default = run_sweep.build_argv("model-a", "task-x", 42, "/tmp/root")
    argv_none = run_sweep.build_argv(
        "model-a", "task-x", 42, "/tmp/root", "none")
    assert argv_default == argv_none
    assert "--peft" not in argv_none, (
        "the none-mode argv must carry no --peft element — a default-mode "
        "run must be byte-identical to today's subprocess"
    )
    assert "--save_model_name" not in argv_none, (
        "the none-mode argv must carry no --save_model_name element (the "
        "child's default save name is the base model name already)"
    )
    record = run_sweep._new_record(
        "model-a", "task-x", 42, Path("/tmp/root"), "testshash")
    assert record["peft"] == "none", (
        "the run_record peft field must default to 'none'"
    )


def test_enumerate_matrix_emits_alias_cells_under_peft(tmp_path):
    """--peft lora/ia3: cells enumerate under the ALIAS model name
    {model}+{mode} (the output-dir / resume-marker identity) while the
    registry and the --models filter join stays on BASE names — an alias
    filter value finds nothing, proving the join was never aliased."""
    registry_dir = make_registry(tmp_path)
    lora = run_sweep.enumerate_matrix(
        ["model-a", "model-b"], ["task-x"], [42, 43], registry_dir,
        peft="lora")
    assert lora == [
        ("model-a+lora", "task-x", 42), ("model-a+lora", "task-x", 43),
        ("model-b+lora", "task-x", 42), ("model-b+lora", "task-x", 43),
    ], "peft=lora must enumerate sorted alias cells"
    ia3 = run_sweep.enumerate_matrix(
        ["model-b"], ["task-x"], [42], registry_dir, peft="ia3")
    assert ia3 == [("model-b+ia3", "task-x", 42)]
    # The --models join stays on BASE names: an alias-typed filter is
    # simply unknown to the registry (fail-fast via _validate_filters in
    # the CLI path; here the enumeration itself yields nothing).
    aliased_filter = run_sweep.enumerate_matrix(
        ["model-a+lora"], ["task-x"], [42], registry_dir, peft="lora")
    assert aliased_filter == [], (
        "registry filtering must join on base names — an alias filter "
        "value must not match (argv targeting re-derives the base itself)"
    )


def test_build_argv_targets_base_and_saves_alias_as_list_elements():
    """Under peft, build_argv emits --target_model <BASE> (suffix-stripped)
    plus --save_model_name <alias> and --peft <mode> — every flag and value
    a separate LIST element (T-03-10 continuity)."""
    argv = run_sweep.build_argv(
        "model-a+lora", "task-x", 42, "/tmp/root", "lora")
    assert isinstance(argv, list), (
        "the subprocess must be launched from an argv LIST, never a shell "
        "string (T-03-10: registry values must not pass through a shell)"
    )
    assert all(isinstance(element, str) for element in argv)
    assert flag_value(argv, "--target_model") == "model-a", (
        "--target_model must carry the BASE registry name — the alias is "
        "not a registry key and would break the child's model filtering"
    )
    assert flag_value(argv, "--target_dataset") == "task-x"
    assert flag_value(argv, "--seed") == "42"
    assert flag_value(argv, "--output_dir") == "/tmp/root"
    assert flag_value(argv, "--save_model_name") == "model-a+lora", (
        "--save_model_name must carry the ALIAS so the child writes the "
        "alias dir (name isolation end-to-end)"
    )
    assert flag_value(argv, "--peft") == "lora"
    ia3 = run_sweep.build_argv(
        "model-b+ia3", "task-z", 7, "/tmp/root", "ia3")
    assert flag_value(ia3, "--target_model") == "model-b"
    assert flag_value(ia3, "--save_model_name") == "model-b+ia3"
    assert flag_value(ia3, "--peft") == "ia3"


def test_launch_subprocess_threads_peft_into_argv(monkeypatch):
    """The real launch path (captured argv, never executed) carries the
    peft composition: base target, alias save name, mode flag."""
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        return subprocess.CompletedProcess(argv, returncode=0)

    monkeypatch.setattr(run_sweep.subprocess, "run", fake_run)
    run_sweep.launch_subprocess(
        "model-a+lora", "task-x", 42, "/tmp/sweep-root", peft="lora")
    argv = captured["argv"]
    assert flag_value(argv, "--target_model") == "model-a"
    assert flag_value(argv, "--save_model_name") == "model-a+lora"
    assert flag_value(argv, "--peft") == "lora"


def test_run_matrix_writes_peft_record_inside_alias_cell_dir(tmp_path):
    """run_matrix with a fake executor over alias cells writes
    run_record.json carrying the peft field INSIDE the alias cell dir —
    the exporter walk treats the alias as just another model dir."""
    out_root = tmp_path / "sweep-out"

    def fake_executor(model, task, seed, output_root, train_fraction=None):
        cell_dir = Path(output_root) / model / task / f"seed_{seed}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        (cell_dir / "final_metrics.json").write_text(
            json.dumps(SUITE_NATIVE_METRICS, indent=4), encoding="utf-8")

    registry_dir = make_registry(tmp_path)
    cells = run_sweep.enumerate_matrix(
        ["model-a"], ["task-x"], [42], registry_dir, peft="lora")
    records = run_sweep.run_matrix(
        cells, out_root, executor=fake_executor, peft="lora")
    assert records[0]["model"] == "model-a+lora"
    assert records[0]["peft"] == "lora"
    record_path = (
        out_root / "model-a+lora" / "task-x" / "seed_42" / "run_record.json")
    disk = json.loads(record_path.read_text(encoding="utf-8"))
    assert disk["peft"] == "lora", (
        "the on-disk run_record must carry the peft field — the frontier "
        "row derivation reads it"
    )
    assert disk["model"] == "model-a+lora"
    assert disk["status"] == "completed"
    assert disk["metrics"] == SUITE_NATIVE_METRICS


def test_default_executor_receives_peft(tmp_path, monkeypatch):
    """run_matrix's DEFAULT executor path threads peft through to the real
    launcher: with no executor injected, the (captured, never-executed)
    subprocess argv carries the peft composition."""
    captured = {}

    def fake_run(argv, **kwargs):
        # _git_commit() also rides subprocess.run — give it a stdout.
        if argv[:1] == ["git"]:
            return subprocess.CompletedProcess(
                argv, returncode=0, stdout="fakehash\n")
        captured["argv"] = argv
        return subprocess.CompletedProcess(argv, returncode=0)

    monkeypatch.setattr(run_sweep.subprocess, "run", fake_run)
    # The fake run writes no final_metrics.json, so the cell is recorded
    # failed (CR-02) — the point here is the argv the default executor
    # built, not the status.
    records = run_sweep.run_matrix(
        [("model-a+lora", "task-x", 42)], tmp_path / "out", peft="lora")
    assert flag_value(captured["argv"], "--peft") == "lora"
    assert flag_value(captured["argv"], "--save_model_name") == "model-a+lora"
    assert flag_value(captured["argv"], "--target_model") == "model-a"
    assert records[0]["peft"] == "lora"


def test_alias_marker_does_not_skip_base_cell(tmp_path):
    """The resume-marker skip stays scoped to the (alias, task, seed) cell:
    a trainer_state.json under model-a+lora never skips the BASE model-a
    cell (the alias gives a distinct model-level dir and marker)."""
    out_root = tmp_path / "sweep-out"
    alias_cell = out_root / "model-a+lora" / "task-x" / "seed_42"
    alias_cell.mkdir(parents=True)
    (alias_cell / "trainer_state.json").write_text("{}", encoding="utf-8")

    invoked = []

    def fake_executor(model, task, seed, output_root, train_fraction=None):
        invoked.append((model, task, seed))
        cell_dir = Path(output_root) / model / task / f"seed_{seed}"
        cell_dir.mkdir(parents=True, exist_ok=True)
        (cell_dir / "final_metrics.json").write_text(
            json.dumps(SUITE_NATIVE_METRICS, indent=4), encoding="utf-8")

    records = run_sweep.run_matrix(
        [("model-a+lora", "task-x", 42), ("model-a", "task-x", 42)],
        out_root, executor=fake_executor)
    statuses = {record["model"]: record["status"] for record in records}
    assert statuses["model-a+lora"] == "skipped"
    assert statuses["model-a"] == "completed", (
        "an alias cell's resume marker must never skip the base cell — "
        "name isolation is the whole point of the alias (Pitfall 3)"
    )
    assert invoked == [("model-a", "task-x", 42)]


def test_dry_run_peft_manifest_lists_alias_cells_only(tmp_path, monkeypatch):
    """--dry-run with --peft lora writes sweep_manifest.json listing ONLY
    alias cells (no base-name cells, no execution, no cell dirs) — and the
    same matrix + --peft produces byte-identical manifests across two
    runs."""
    registry_dir = make_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    argv = [
        "--models", "model-a,model-b",
        "--tasks", "task-x",
        "--seeds", "42",
        "--dry-run",
        "--peft", "lora",
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ]
    run_cli(monkeypatch, argv)
    manifest_path = out_root / "sweep_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert {c["model"] for c in manifest["cells"]} == {
        "model-a+lora", "model-b+lora"}, (
        "the --peft dry-run manifest must list ONLY alias cells"
    )
    assert manifest["matrix"]["models"] == [
        "model-a+lora", "model-b+lora"]
    assert all("+lora" in c["output_dir"] for c in manifest["cells"]), (
        "every planned outdir must live under the alias model dir"
    )
    assert not list(out_root.rglob("seed_*")), (
        "dry-run must not create cell directories"
    )
    first = manifest_path.read_bytes()
    run_cli(monkeypatch, argv)
    assert manifest_path.read_bytes() == first, (
        "two --peft dry-runs over the same inputs must produce "
        "byte-identical manifests"
    )


# =====================================================================
# --curve expansion (06-05, SC-6 / REV-08 F8 learning curves)
# =====================================================================

def test_curve_flag_declared_in_parse_args(monkeypatch):
    """--curve exists, is a plain string flag, and defaults to None (no
    fraction expansion — the byte-identical default enumeration)."""
    monkeypatch.setattr(
        sys, "argv", ["run_sweep.py", "--seeds", "42"])
    args = run_sweep.parse_args()
    assert args.curve is None


def test_parse_curve_fractions_valid_sorted_deduped():
    """A valid comma list parses to sorted unique floats — duplicates
    collapse (two identical fractions map to one identical output dir)
    and the ascending order makes the enumeration deterministic."""
    assert run_sweep.parse_curve_fractions("0.5,0.25,0.25,1.0") == [
        0.25, 0.5, 1.0]
    assert run_sweep.parse_curve_fractions("1.0") == [1.0]


def test_curve_validation_collects_all_problems_together():
    """Parse errors and bounds violations are ALL listed in one fail-fast
    exit (the _validate_filters discipline) — a bad fraction list steers
    multi-day GPU execution, so every problem must be named at once."""
    with pytest.raises(SystemExit) as excinfo:
        run_sweep.parse_curve_fractions("0,abc,1.5")
    message = str(excinfo.value)
    assert "[Error] --curve" in message
    assert "'abc'" in message, "the non-numeric element must be named"
    assert "'0'" in message, "the f <= 0 element must be named"
    assert "'1.5'" in message, "the f > 1 element must be named"


def test_curve_validation_refuses_empty_elements_and_empty_lists():
    """An empty comma element and a list that parses to nothing both
    refuse — never silently enumerate a zero-fraction curve."""
    with pytest.raises(SystemExit) as empty_elem:
        run_sweep.parse_curve_fractions("0.5,,1.0")
    assert "empty fraction element" in str(empty_elem.value)
    with pytest.raises(SystemExit) as nothing:
        run_sweep.parse_curve_fractions(" , ")
    assert "--curve" in str(nothing.value)


def test_enumerate_matrix_expands_fraction_cells_sorted(tmp_path):
    """--curve fractions expand each (model, task, seed) cell into one
    4-tuple cell per fraction, sorted (model, task, seed, fraction); with
    no fractions the enumeration is EXACTLY today's 3-tuple form."""
    registry_dir = make_registry(tmp_path)
    cells = run_sweep.enumerate_matrix(
        ["model-a"], ["task-x"], [42], registry_dir,
        fractions=[1.0, 0.25, 0.5])
    assert cells == [
        ("model-a", "task-x", 42, 0.25),
        ("model-a", "task-x", 42, 0.5),
        ("model-a", "task-x", 42, 1.0),
    ], "fraction cells must enumerate in sorted fraction order"
    default = run_sweep.enumerate_matrix(
        ["model-a"], ["task-x"], [42], registry_dir)
    assert default == [("model-a", "task-x", 42)], (
        "no fractions must keep the exact 3-tuple default enumeration "
        "(byte-identical cells)"
    )


def test_curve_composes_with_peft_enumeration(tmp_path):
    """--curve composes with --peft: alias cells expand across fractions
    exactly like base cells."""
    registry_dir = make_registry(tmp_path)
    cells = run_sweep.enumerate_matrix(
        ["model-a"], ["task-x"], [42], registry_dir,
        peft="lora", fractions=[1.0, 0.25])
    assert cells == [
        ("model-a+lora", "task-x", 42, 0.25),
        ("model-a+lora", "task-x", 42, 1.0),
    ]


def test_curve_dry_run_manifest_lists_frac_cells_nested_under_seed(
        tmp_path, monkeypatch):
    """--curve + --dry-run writes planned frac cells whose output dirs
    nest frac_{f} UNDER the seed dir — the no-sibling regression lock
    (T-06-15): a frac_ directory may NEVER appear as a direct child of a
    task dir, or the trainer_state.json resume marker scoping and the
    exporter walk break. The manifest is byte-identical across two runs
    and the frac cells enumerate in sorted fraction order."""
    registry_dir = make_registry(tmp_path)
    out_root = tmp_path / "sweep-out"
    argv = [
        "--models", "model-a",
        "--tasks", "task-x",
        "--seeds", "42,43",
        "--dry-run",
        "--curve", "1.0,0.25",
        "--output-root", str(out_root),
        "--registry-dir", str(registry_dir),
    ]
    run_cli(monkeypatch, argv)
    manifest_path = out_root / "sweep_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cells = [(c["model"], c["task"], c["seed"]) for c in manifest["cells"]]
    assert cells == [
        ("model-a", "task-x", 42), ("model-a", "task-x", 42),
        ("model-a", "task-x", 43), ("model-a", "task-x", 43),
    ]
    # The no-sibling layout lock: every frac_ path component sits
    # DIRECTLY under a seed_ component — never a direct child of the
    # task dir.
    for entry in manifest["cells"]:
        parts = Path(entry["output_dir"]).parts
        frac_positions = [
            i for i, part in enumerate(parts) if part.startswith("frac_")
        ]
        assert frac_positions, (
            f"curve cell output_dir lacks a frac_ segment: "
            f"{entry['output_dir']}"
        )
        for i in frac_positions:
            assert parts[i - 1].startswith("seed_"), (
                f"frac_ dir {parts[i]} is NOT nested under a seed_ dir — "
                f"a sibling frac layout corrupts the resume-marker "
                f"scoping and the exporter walk (T-06-15): "
                f"{entry['output_dir']}"
            )
    # sorted fraction order within each (model, task, seed) cell
    dirs = [c["output_dir"] for c in manifest["cells"]]
    assert dirs == sorted(dirs)
    assert "frac_0.25" in dirs[0] and "frac_1.0" in dirs[1]
    # byte determinism
    first = manifest_path.read_bytes()
    run_cli(monkeypatch, argv)
    assert manifest_path.read_bytes() == first, (
        "two --curve dry-runs over the same inputs must produce "
        "byte-identical manifests"
    )
    assert not list(out_root.rglob("seed_*")), (
        "dry-run must not create cell directories"
    )


def test_build_argv_appends_train_fraction_as_list_element():
    """build_argv appends --train_fraction <f> as separate LIST elements
    (T-03-10 continuity), composes with the peft alias composition, and
    omits the elements entirely when no fraction is given."""
    argv = run_sweep.build_argv(
        "model-a", "task-x", 42, "/tmp/root", train_fraction=0.25)
    assert isinstance(argv, list)
    assert all(isinstance(element, str) for element in argv)
    assert flag_value(argv, "--train_fraction") == "0.25"
    assert flag_value(argv, "--target_model") == "model-a"
    combined = run_sweep.build_argv(
        "model-a+lora", "task-x", 42, "/tmp/root", "lora", 0.5)
    assert flag_value(combined, "--target_model") == "model-a"
    assert flag_value(combined, "--save_model_name") == "model-a+lora"
    assert flag_value(combined, "--peft") == "lora"
    assert flag_value(combined, "--train_fraction") == "0.5"
    plain = run_sweep.build_argv("model-a", "task-x", 42, "/tmp/root")
    assert "--train_fraction" not in plain


def test_new_record_train_fraction_field():
    """_new_record gains a train_fraction field: float for curve cells,
    null otherwise (JSON null via None)."""
    plain = run_sweep._new_record(
        "model-a", "task-x", 42, Path("/tmp/root"), "hash")
    assert plain["train_fraction"] is None
    curve = run_sweep._new_record(
        "model-a", "task-x", 42, Path("/tmp/root"), "hash",
        train_fraction=0.25)
    assert curve["train_fraction"] == 0.25


def test_run_matrix_curve_cell_record_and_frac_scoped_resume(tmp_path):
    """run_matrix over curve cells writes run_record.json carrying the
    train_fraction INSIDE the frac-nested cell dir, and the resume marker
    is (model, task, seed, fraction)-scoped: a marker in frac_0.25 never
    skips the frac_1.0 cell of the same seed."""
    out_root = tmp_path / "sweep-out"

    def fake_executor(model, task, seed, output_root, train_fraction=None):
        cell_dir = run_sweep.cell_dir_for(
            output_root, model, task, seed, train_fraction)
        cell_dir.mkdir(parents=True, exist_ok=True)
        (cell_dir / "final_metrics.json").write_text(
            json.dumps(SUITE_NATIVE_METRICS, indent=4), encoding="utf-8")

    # Pre-existing marker in frac_0.25 only.
    done = run_sweep.cell_dir_for(out_root, "model-a", "task-x", 42, 0.25)
    done.mkdir(parents=True)
    (done / "trainer_state.json").write_text("{}", encoding="utf-8")

    records = run_sweep.run_matrix(
        [("model-a", "task-x", 42, 0.25), ("model-a", "task-x", 42, 1.0)],
        out_root, executor=fake_executor)
    statuses = {r["train_fraction"]: r["status"] for r in records}
    assert statuses[0.25] == "skipped"
    assert statuses[1.0] == "completed", (
        "a frac_0.25 resume marker must never skip the frac_1.0 cell — "
        "the marker is fraction-scoped (T-06-15 nesting invariant)"
    )
    record_path = run_sweep.cell_dir_for(
        out_root, "model-a", "task-x", 42, 1.0) / "run_record.json"
    disk = json.loads(record_path.read_text(encoding="utf-8"))
    assert disk["train_fraction"] == 1.0
    assert disk["status"] == "completed"
    assert disk["metrics"] == SUITE_NATIVE_METRICS


def test_default_executor_receives_train_fraction(tmp_path, monkeypatch):
    """run_matrix's DEFAULT executor path threads the fraction through to
    the real launcher: the captured (never-executed) subprocess argv
    carries --train_fraction <f>."""
    captured = {}

    def fake_run(argv, **kwargs):
        if argv[:1] == ["git"]:
            return subprocess.CompletedProcess(
                argv, returncode=0, stdout="fakehash\n")
        captured["argv"] = argv
        return subprocess.CompletedProcess(argv, returncode=0)

    monkeypatch.setattr(run_sweep.subprocess, "run", fake_run)
    run_sweep.run_matrix(
        [("model-a", "task-x", 42, 0.25)], tmp_path / "out")
    assert flag_value(captured["argv"], "--train_fraction") == "0.25"


# =====================================================================
# extract_curve_points (06-05, SC-6 / REV-08 F8 offline harvesting)
# =====================================================================

def test_extract_curve_points_sorts_and_filters_log_history():
    """Only log_history entries carrying eval_ keys are curve points;
    points return SORTED by step (out-of-order input handled); non-eval
    keys on an eval entry are excluded from the metrics dict."""
    state = {
        "log_history": [
            {"loss": 0.5, "step": 1, "epoch": 0.01},
            {"eval_loss": 0.4, "eval_AUROC": 0.7, "step": 100},
            {"loss": 0.3, "step": 100},  # no eval keys -> skipped
            {"eval_loss": 0.2, "step": 50},  # out of order -> sorted
            {"eval_loss": 0.1, "eval_AUROC": 0.75, "step": 300,
             "epoch": 1.0},
        ],
    }
    points = run_sweep.extract_curve_points(state)
    assert [step for step, _ in points] == [50, 100, 300], (
        "points must be sorted by step regardless of log order"
    )
    assert points[0][1] == {"eval_loss": 0.2}
    assert points[1][1] == {"eval_loss": 0.4, "eval_AUROC": 0.7}, (
        "non-eval keys (loss/epoch) must not leak into the metrics dict"
    )
    assert points[2][1] == {"eval_loss": 0.1, "eval_AUROC": 0.75}


def test_extract_curve_points_empty_or_absent_history():
    """An absent log_history, an empty one, a None trainer_state, and a
    history with no eval-carrying entries all yield [] — the reader is
    total over trainer_state shapes, never raising."""
    assert run_sweep.extract_curve_points({}) == []
    assert run_sweep.extract_curve_points(None) == []
    assert run_sweep.extract_curve_points({"log_history": []}) == []
    assert run_sweep.extract_curve_points(
        {"log_history": [{"loss": 1.0, "step": 5}]}
    ) == [], "a pure-loss history carries no curve points"


def test_extract_curve_points_skips_unusable_entries():
    """A non-dict entry and an eval entry without a usable step are
    skipped — a point that cannot be placed on the curve is not a
    point."""
    state = {
        "log_history": [
            "garbage-entry",
            {"eval_loss": 0.3},  # no step
            {"eval_loss": 0.25, "step": 200},
        ],
    }
    points = run_sweep.extract_curve_points(state)
    assert points == [(200, {"eval_loss": 0.25})]
