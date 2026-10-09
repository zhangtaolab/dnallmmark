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
  string recorded and an entry in the failures manifest; a pre-existing
  ``trainer_state.json`` yields status ``skipped`` with NO executor
  invocation — and the skip is seed-scoped (seed 43 still runs when seed
  42's marker exists in the sibling dir);
- **subprocess contract** — the real launch path (captured argv, never
  executed) passes --target_model/--target_dataset/--seed/--output_dir as
  separate argv elements of a LIST with cwd set to this repo's pipeline
  directory — never a shell string;
- **registry-derived defaults** — default enumeration derives the matrix
  from ``models_info.json`` keys x truthy-``Train`` ``datasets_info.json``
  entries (the unified D-10 registries), honoring --models/--tasks filters.

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
    assert list(disk["metrics"]) == list(SUITE_NATIVE_METRICS), (
        "key ORDER and identity must be verbatim (sort_keys only sorts the "
        "serialized form — no key renaming may occur)"
    )
    manifest = json.loads(
        (out_root / "sweep_manifest.json").read_text(encoding="utf-8"))
    assert manifest["cells"][0]["status"] == "completed"
    assert not (out_root / "sweep_failures.json").exists(), (
        "no failures manifest when every cell succeeds"
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
