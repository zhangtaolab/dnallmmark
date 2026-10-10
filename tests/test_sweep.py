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
  drives the PIPE-03 E2E pair first over a registry holding the real pair
  names, and run_matrix executes cells in the GIVEN order (the fake
  executor's invocation order preserves the priority order);
- **failures-manifest re-run (05-04)** — ``--from-failures`` enumerates
  exactly the failed (model, task) pairs' cells across ALL requested seeds;
  a clean manifest yields an EXPLICIT zero-cell run with a clear message
  (never a silent full sweep);
- **operator-input validation (T-05-09)** — unknown model/task names,
  wrong JSON structure, or an unreadable/unparseable --priority-file /
  --from-failures file exits non-zero with ALL problems listed
  (the _validate_filters discipline), before any cell is enumerated.

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

    def fake_executor(model, task, seed, output_root):
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

    def failing_executor(model, task, seed, output_root):
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

    def silent_failure_executor(model, task, seed, output_root):
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

    def corrupting_executor(model, task, seed, output_root):
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

    def fake_executor(model, task, seed, output_root):
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

    def fake_executor(model, task, seed, output_root):
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

    def never_executor(model, task, seed, output_root):
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
    """A registry holding the REAL E2E pair names plus a bystander model
    and a second task, so the committed priorities file validates and its
    tier-1-first effect is observable against names that are not
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
    cells keep the sorted() fallback order. Tier 2 here is EMPTY (the
    maintainer-curation form)."""
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
    registry holding the REAL E2E pair names and drives exactly the PIPE-03
    pair's cells (both models x the E2E task, all seeds) before every other
    cell — the degradation order's tier 1."""
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
    assert len(cells) == 12  # 3 models x 2 tasks x 2 seeds
    # Tier 1 first: the E2E pair's four cells (both models, both seeds) —
    # in sorted fallback order within the tier, seeds adjacent.
    assert set(cells[:4]) == {
        ("PlantHelixSeek", E2E_TASK, 42), ("PlantHelixSeek", E2E_TASK, 43),
        ("plant-dnamamba-6mer", E2E_TASK, 42),
        ("plant-dnamamba-6mer", E2E_TASK, 43),
    }
    assert cells[0][0] == cells[1][0] and cells[0][1] == cells[1][1] == E2E_TASK, (
        "seeds must stay adjacent within a tier-1 cell"
    )
    # Every remaining cell (the bystander's + the E2E models' other__task
    # cells) follows in the sorted() fallback order.
    assert set(cells[4:]) == {
        ("PlantHelixSeek", "other__task", 42), ("PlantHelixSeek", "other__task", 43),
        ("bystander-model", E2E_TASK, 42), ("bystander-model", E2E_TASK, 43),
        ("bystander-model", "other__task", 42),
        ("bystander-model", "other__task", 43),
        ("plant-dnamamba-6mer", "other__task", 42),
        ("plant-dnamamba-6mer", "other__task", 43),
    }
    assert cells[4:] == sorted(cells[4:])


def test_committed_priorities_file_content():
    """pipeline/sweep_priorities.json: tier 1 names exactly the pre-decided
    PIPE-03 E2E pair ({model, task} specs on the E2E task); tier 2 is EMPTY
    awaiting the maintainer's Task-4 curation (never agent-invented)."""
    tiers = json.loads(COMMITTED_PRIORITIES.read_text(encoding="utf-8"))
    assert isinstance(tiers, list) and len(tiers) == 2
    tier1, tier2 = tiers
    assert tier1 == [
        {"model": "plant-dnamamba-6mer", "task": E2E_TASK},
        {"model": "PlantHelixSeek", "task": E2E_TASK},
    ]
    assert tier2 == [], "tier 2 is maintainer-curated — ships EMPTY"


def test_run_matrix_preserves_given_cell_order(tmp_path):
    """run_matrix executes cells in the GIVEN order (a priority-ordered
    list stays priority-ordered) instead of re-sorting — the fake executor's
    invocation order is the proof; nothing in this test launches a real
    subprocess (D-05)."""
    out_root = tmp_path / "sweep-out"
    invoked = []

    def recording_executor(model, task, seed, output_root):
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
