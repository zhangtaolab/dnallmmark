"""Contract tests for the exporter core (SC-2/REV-03, IN-03, D-12, D-15).

Covers, in order:

- Metric-key mapping parity in BOTH directions over the 28-name vendored
  suite surface (@483a35c): every suite canonical maps to a declared export
  slot or is explicitly unmapped (""), and every one of the 14 metricBlock
  keys traces back to a suite canonical or a declared pipeline-produced key
  (no silent drops in either direction — IN-03's single-owner table).
- Alias resolution mirroring the suite registry exactly (one-directional:
  ``eval_AUROC``/``eval_auroc`` both resolve to the AUROC canonical; the
  historical ``eval_pearson_r``/``eval_spearman_r`` spellings resolve;
  resolution never emits an alias).
- End-to-end emission over a synthetic F2 fixture tree (2 models x 1 task
  x 3 seeds + a failed sibling), validating the emitted task file against
  the UNCHANGED ``schemas/task_performance.json`` (jsonschema), pinning
  the D-12 parametersBlock join (vram_probe override AND YAML fallback
  paths), the Multiple->majority species mapping, the failed-record
  exclusion, and the per-seed statistics artifact (t-interval block).
- Hard edges: missing ``total_flos`` (actionable hard error naming the
  record path), unregistered dataset/model (KeyError — never a fallback
  join), 1-seed degenerate cells (sd/ci95 None, method "none").
- Byte-stability: exporting the same fixture tree twice produces
  byte-identical outputs (sorted iteration, sort_keys, no live clock).
- Pivot-shape ownership (04-05, folded from the retired tests/test_pivot.py
  when script/get_task_performance.py was deleted): one file per dataset
  named ``{dataset}_task_performance.json``, ``info`` mirroring the dataset
  block, the 11/9/14 (model/parameters/performance) key shape, sanitized
  filenames, and the missing-metric model still present — asserted over BOTH
  the committed synthetic_task_performance fixture (the pivot's own final
  output) and the exporter's own emission.
- D-15: HuggingFace evaluate cross-validates the metric conventions on
  golden vectors (evaluate's standard implementations vs independently
  derived expected values, tolerance-asserted).

The exporter input contract (run_record.json) is pinned with fixtures that
reuse the SUITE_NATIVE_METRICS convention from tests/test_sweep.py; the
suite itself is never imported (CONTEXT exporter-Q1).

See also:
    - ``tests/test_vendored_stats.py`` — the vendored statistics parity.
    - ``tests/test_freeze_snapshot.py`` — the snapshot primitive.
"""

from __future__ import annotations

import json
from pathlib import Path

import export_runs  # conftest puts script/ on sys.path
import jsonschema
import numpy as np
import pytest
import summarize_comparison  # 04-01's consumer-side join (arena parity)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((REPO_ROOT / "schemas" / "task_performance.json").read_text(encoding="utf-8"))

# The 28 suite canonical names @483a35c — written out independently here so
# the test (not the module) is the parity oracle's cross-check.
EXPECTED_SUITE_CANONICAL = frozenset({
    "accuracy", "precision", "recall", "f1", "f1_micro", "f1_weighted",
    "f1_samples", "precision_micro", "precision_weighted", "precision_samples",
    "recall_micro", "recall_weighted", "recall_samples", "mcc",
    "matthews_correlation", "AUROC", "AUPRC", "AUROC_ovr", "AUROC_ovo",
    "TPR", "TNR", "FPR", "FNR", "mse", "mae", "r2", "pearsonr", "spearmanr",
})


# =====================================================================
# Fixture-tree builders (F2 layout; SUITE_NATIVE_METRICS convention)
# =====================================================================

def _suite_native_metrics(auroc: float, *, pearson=0.5, loss=0.234,
                          flos=1.0e15, runtime=100.0, extra=None):
    """A run-record metrics payload in suite-native keys (test_sweep.py:68)."""
    metrics = {
        "eval_AUROC": auroc,
        "eval_pearsonr": pearson,
        "eval_loss": loss,
        "total_flos": flos,
        "train_runtime": runtime,
    }
    if extra:
        metrics.update(extra)
    return metrics


def _write_run_record(root, model, task, seed, metrics, *, status="completed",
                      vram=None, global_step=2229285):
    """Materialize one {root}/{model}/{task}/seed_{seed}/ cell."""
    seed_dir = root / model / task / f"seed_{seed}"
    seed_dir.mkdir(parents=True)
    record = {
        "model": model,
        "task": task,
        "seed": seed,
        "status": status,
        "output_dir": str(seed_dir),
        "metrics": metrics,
        "vram_probe": vram if vram is not None else {
            "gpu_mem_total": None, "init_max_mem": None,
            "batch_size": None, "gradient_accumulation_steps": None,
        },
        "git_commit": "testshash",
        "started_at": "2026-10-10T00:00:00Z",
        "finished_at": "2026-10-10T01:00:00Z",
        "error": None,
    }
    (seed_dir / "run_record.json").write_text(json.dumps(record), encoding="utf-8")
    (seed_dir / "trainer_state.json").write_text(
        json.dumps({"global_step": global_step}), encoding="utf-8"
    )
    return seed_dir


MODEL_CARD = {
    "architecture": "Bert", "context_len (bp)": 10000,
    "huggingface": "org/FakeModel", "mean_token_len": 6,
    "modelscope": "org/FakeModel", "name": "FakeModel", "series": "Fake",
    "size (M)": 117, "species": "multi-species", "tokenizer": "BPE",
    "type": "MLM",
}


def _registry_files(tmp_path):
    """Fixture registry slices: 2 models + 1 Multiple-Category dataset."""
    models = {
        "FakeModel-A": {
            "Model_name": "FakeModel-A", "Model_path": "models/FakeModel-A",
            "Model_size": "117M", "Tokenizer": "BPE", "Mean_token_length": 6,
            **MODEL_CARD,
        },
        "FakeModel-B": {
            "Model_name": "FakeModel-B", "Model_path": "models/FakeModel-B",
            "Model_size": "117M", "Tokenizer": "BPE", "Mean_token_length": 6,
            **MODEL_CARD, "name": "FakeModel", "huggingface": "org/FakeModel-B",
        },
    }
    datasets = {
        "FakeDS__task": {
            "Category": "Multiple",  # must NEVER reach output as-is
            "Dataset_name": "FakeDS__task", "Dataset_path": "datasets/FakeDS/task",
            "Dev": 100, "Test": 200, "Train": 300, "Index": 1,
            "labels": 2, "length": 500, "metric": "AUPRC", "type": "binary",
        },
    }
    models_path = tmp_path / "models_info.json"
    datasets_path = tmp_path / "datasets_info.json"
    models_path.write_text(json.dumps(models), encoding="utf-8")
    datasets_path.write_text(json.dumps(datasets), encoding="utf-8")
    return models_path, datasets_path


FINETUNE_CONFIG_YAML = """\
task:
    task_type: "binary"
    num_labels: 2
finetune:
    num_train_epochs: 3
    per_device_train_batch_size: 8
    gradient_accumulation_steps: 1
    max_steps: -1
    learning_rate: 2e-5
    warmup_ratio: 0.1
    lr_scheduler_type: "linear"
    bf16: True
    fp16: False
"""

EXPECTED_PARAMS_A = {
    "batch_size": 149,        # vram_probe override (non-null)
    "bf16": True,
    "epochs": 3,
    "fp16": False,
    "gradient_accumulation_steps": 1,  # vram_probe null -> YAML base
    "learning_rate": 2e-5,
    "lr_scheduler_type": "linear",
    "steps": 2229285,         # trainer_state.json global_step
    "warmup": 0.1,
}

EXPECTED_PARAMS_B = {
    "batch_size": 8,          # vram_probe null -> YAML base
    "bf16": True,
    "epochs": 3,
    "fp16": False,
    "gradient_accumulation_steps": 1,
    "learning_rate": 2e-5,
    "lr_scheduler_type": "linear",
    "steps": 2229285,
    "warmup": 0.1,
}


def _build_fixture_tree(tmp_path, *, include_failed=True):
    """2 models x 1 task x 3 seeds (+ a failed sibling), Multiple-Category dataset."""
    root = tmp_path / "finetuned"
    # FakeModel-A: seeds 42/43/44; seed 42 carries the vram_probe override.
    _write_run_record(
        root, "FakeModel-A", "FakeDS__task", 42,
        _suite_native_metrics(0.91),
        vram={"gpu_mem_total": None, "init_max_mem": None,
              "batch_size": 149, "gradient_accumulation_steps": None},
    )
    _write_run_record(root, "FakeModel-A", "FakeDS__task", 43, _suite_native_metrics(0.93))
    _write_run_record(root, "FakeModel-A", "FakeDS__task", 44, _suite_native_metrics(0.95))
    # FakeModel-B: 3 completed seeds (one carrying an unmapped canonical so
    # the stats artifact discloses it) + 1 failed sibling whose full metric
    # payload must contribute NOTHING.
    extra = {"eval_TPR": 0.8}
    _write_run_record(root, "FakeModel-B", "FakeDS__task", 7, _suite_native_metrics(0.70, extra=extra))
    _write_run_record(root, "FakeModel-B", "FakeDS__task", 8, _suite_native_metrics(0.80, extra=extra))
    _write_run_record(root, "FakeModel-B", "FakeDS__task", 9, _suite_native_metrics(0.90, extra=extra))
    if include_failed:
        _write_run_record(
            root, "FakeModel-B", "FakeDS__task", 99,
            _suite_native_metrics(0.0), status="failed",
        )
    models_path, datasets_path = _registry_files(tmp_path)
    config_path = tmp_path / "finetune_config.yaml"
    config_path.write_text(FINETUNE_CONFIG_YAML, encoding="utf-8")
    return root, models_path, datasets_path, config_path


def _export(tmp_path, **overrides):
    """Run the full export over the standard fixture tree; return paths."""
    root, models_path, datasets_path, config_path = _build_fixture_tree(tmp_path)
    out = tmp_path / "out"
    stats = tmp_path / "stats"
    export_runs.export_runs_tree(
        root, models_path, datasets_path, config_path, out, stats,
        n_bootstrap=2000, bootstrap_seed=42, small_n_ci="t-interval",
        **overrides,
    )
    return out, stats


# =====================================================================
# Mapping-surface parity (both directions) + alias rules
# =====================================================================

def test_suite_canonical_surface_is_the_28_name_vendored_set():
    """SUITE_CANONICAL is exactly the 28-name surface @483a35c, and the
    mapping is total: mapped | unmapped == canonical, disjoint."""
    assert export_runs.SUITE_CANONICAL == EXPECTED_SUITE_CANONICAL
    assert len(EXPECTED_SUITE_CANONICAL) == 28
    assert set(export_runs.CANONICAL_TO_EXPORT) | set(export_runs.UNMAPPED) == export_runs.SUITE_CANONICAL
    assert not set(export_runs.CANONICAL_TO_EXPORT) & set(export_runs.UNMAPPED)


def test_key_parity_suite_to_export_no_silent_drops():
    """Every one of the 28 canonicals resolves to a declared slot or the
    deliberate empty-string marker (never None, never an alias)."""
    for name in sorted(EXPECTED_SUITE_CANONICAL):
        slot = export_runs.resolve_metric_key(name)
        assert slot is not None, f"{name} silently dropped"
        assert not slot.startswith("eval_"), f"{name} emitted an alias"
        if name in export_runs.CANONICAL_TO_EXPORT:
            assert slot == export_runs.CANONICAL_TO_EXPORT[name]
        else:
            assert name in export_runs.UNMAPPED
            assert slot == "", f"unmapped {name} must emit the empty string"


def test_key_parity_export_to_suite_every_key_traces():
    """Every metricBlock key traces to a suite canonical or a pipeline key,
    and the 14-key surface equals the schema's metricBlock requirement."""
    assert export_runs.EXPORT_METRIC_KEYS == set(
        export_runs.CANONICAL_TO_EXPORT.values()
    ) | set(export_runs.PIPELINE_KEYS.values())
    assert export_runs.PIPELINE_KEYS == {
        "eval_loss": "loss", "train_runtime": "runtime", "total_flos": "FLOPs",
    }
    schema_required = set(SCHEMA["$defs"]["metricBlock"]["required"])
    assert export_runs.EXPORT_METRIC_KEYS == schema_required, (
        "mapping surface drifted from the UNCHANGED schema contract"
    )


def test_alias_resolution_mirrors_suite_registry_one_directionally():
    """eval_-prefixed spellings resolve to canonicals; the historical
    *_r spellings resolve; unknown/bookkeeping keys are None by contract."""
    assert export_runs.resolve_metric_key("eval_AUROC") == "auroc"
    assert export_runs.resolve_metric_key("eval_auroc") == "auroc"
    assert export_runs.resolve_metric_key("AUROC") == "auroc"
    assert export_runs.resolve_metric_key("eval_AUPRC") == "auprc"
    assert export_runs.resolve_metric_key("eval_pearsonr") == "pearson_r"
    assert export_runs.resolve_metric_key("eval_pearson_r") == "pearson_r"
    assert export_runs.resolve_metric_key("eval_spearman_r") == "spearman_r"
    # Unmapped canonicals resolve (to the "" marker), they do not vanish.
    assert export_runs.resolve_metric_key("TPR") == ""
    assert export_runs.resolve_metric_key("eval_mae") == ""
    # Pipeline-produced keys are not registry metrics.
    assert export_runs.resolve_metric_key("eval_loss") == "loss"
    assert export_runs.resolve_metric_key("train_runtime") == "runtime"
    assert export_runs.resolve_metric_key("total_flos") == "FLOPs"
    # Trainer bookkeeping: not leaderboard metrics, skipped by contract.
    assert export_runs.resolve_metric_key("train_loss") is None
    assert export_runs.resolve_metric_key("epoch") is None
    assert export_runs.resolve_metric_key("eval_runtime") is None
    assert export_runs.resolve_metric_key("train_samples_per_second") is None
    # No resolution EVER emits an alias spelling.
    for name in EXPECTED_SUITE_CANONICAL:
        slot = export_runs.resolve_metric_key(name)
        assert slot is not None
        assert not slot.startswith("eval_")


def test_majority_arena_parity_with_summarize_comparison():
    """The exporter's Multiple->majority constant equals 04-01's maintainer-
    confirmed mapping (same value, one constant each side)."""
    assert export_runs.MAJORITY_ARENA == {"Multiple": "Animals"}
    assert export_runs.MAJORITY_ARENA == summarize_comparison.MAJORITY_ARENA


# =====================================================================
# End-to-end emission
# =====================================================================

def test_end_to_end_emission_validates_against_unchanged_schema(tmp_path):
    out, stats_dir = _export(tmp_path)
    task_file = out / "FakeDS__task_task_performance.json"
    assert task_file.exists()
    doc = json.loads(task_file.read_text(encoding="utf-8"))
    jsonschema.validate(instance=doc, schema=SCHEMA)

    # datasetBlock: Multiple resolved to the majority arena BEFORE emission.
    assert doc["info"]["species"] == "Animals"
    assert doc["info"]["metric"] == "AUPRC"  # casing NOT normalized
    assert doc["info"] == {
        "dev": 100, "labels": 2, "length": 500, "metric": "AUPRC",
        "species": "Animals", "test": 200, "train": 300, "type": "binary",
    }

    a = doc["performance"]["FakeModel-A"]
    b = doc["performance"]["FakeModel-B"]

    # metricBlock: per-metric 3-seed means over completed records only
    # (the failed sibling's 0.0 payload must contribute nothing).
    assert a["performance"]["auroc"] == pytest.approx((0.91 + 0.93 + 0.95) / 3)
    assert a["performance"]["loss"] == pytest.approx(0.234)
    assert a["performance"]["FLOPs"] == pytest.approx(1.0e15)
    assert a["performance"]["runtime"] == pytest.approx(100.0)
    assert b["performance"]["auroc"] == pytest.approx((0.70 + 0.80 + 0.90) / 3)
    assert b["performance"]["mse"] == ""  # no seed carried it
    assert a["performance"]["mse"] == ""

    # modelCard: the 11-key join from the registry.
    assert a["model"] == {
        "architecture": "Bert", "context_len (bp)": 10000,
        "huggingface": "org/FakeModel", "mean_token_len": 6,
        "modelscope": "org/FakeModel", "name": "FakeModel", "series": "Fake",
        "size (M)": 117, "species": "multi-species", "tokenizer": "BPE",
        "type": "MLM",
    }

    # parametersBlock: the D-12 join, both provenance paths pinned.
    assert a["parameters"] == EXPECTED_PARAMS_A  # vram_probe batch override
    assert b["parameters"] == EXPECTED_PARAMS_B  # YAML fallback

    # Per-seed statistics artifact (the reviewer view): t-interval over 3
    # seeds; the unmapped TPR canonical is disclosed, not silently dropped.
    stats = json.loads(
        (stats_dir / "FakeDS__task_seed_stats.json").read_text(encoding="utf-8")
    )
    block = stats["FakeModel-A"]["auroc"]["stats"]
    assert block["n_seeds"] == 3
    assert block["sd"] is not None
    assert block["ci95"] is not None
    assert block["method"] == "t"
    assert stats["FakeModel-A"]["auroc"]["per_seed"] == {"42": 0.91, "43": 0.93, "44": 0.95}
    assert stats["FakeModel-B"]["TPR"]["stats"]["n_seeds"] == 3
    assert stats["FakeModel-B"]["auroc"]["stats"]["n_seeds"] == 3  # failed seed excluded


# =====================================================================
# Pivot-shape ownership (04-05 — folded from the retired tests/test_pivot.py)
#
# script/get_task_performance.py is deleted (SC-2/OQ6: its model_performance
# input side no longer exists); the pivot semantics the old test pinned are
# owned HERE, asserted over both the committed synthetic_task_performance
# fixture (the pivot's own final deterministic output, produced one last
# time before its deletion) and the exporter's own emission. The schema +
# these tests are the reference now.
# =====================================================================

SYNTHETIC_MODELS_DIR = REPO_ROOT / "tests" / "fixtures" / "synthetic_models"
SYNTHETIC_TASKS_DIR = REPO_ROOT / "tests" / "fixtures" / "synthetic_task_performance"
SYNTHETIC_DATASETS = ("FakeDS__tie_task", "FakeDS__missing_task", "FakeDS__regress_task")
SYNTHETIC_ALIASES = {"fake-alpha", "fake-beta", "fake-gamma"}


def test_pivot_shape_committed_fixture_one_file_per_dataset():
    """The committed synthetic pivot output carries exactly one
    ``{dataset}_task_performance.json`` per synthetic dataset — the naming
    contract the exporter owns going forward."""
    produced = {p.name for p in SYNTHETIC_TASKS_DIR.glob("*.json")}
    assert produced == {f"{ds}_task_performance.json" for ds in SYNTHETIC_DATASETS}


def test_pivot_shape_committed_fixture_info_mirrors_dataset_block():
    """Each committed fixture ``info`` block mirrors the input dataset block
    verbatim (the pivot copied it; the exporter joins the registry's
    datasetBlock) and every per-model block keeps the 11/9/14
    (model/parameters/performance) key shape."""
    alpha = json.loads(
        (SYNTHETIC_MODELS_DIR / "fake-alpha_performance.json").read_text(encoding="utf-8")
    )
    for ds in SYNTHETIC_DATASETS:
        doc = json.loads(
            (SYNTHETIC_TASKS_DIR / f"{ds}_task_performance.json").read_text(encoding="utf-8")
        )
        assert doc["info"] == alpha["performance"][ds]["dataset"]
        assert set(doc["performance"]) == SYNTHETIC_ALIASES
        for block in doc["performance"].values():
            assert len(block["model"]) == 11
            assert len(block["parameters"]) == 9
            assert len(block["performance"]) == 14


def test_pivot_shape_missing_metric_model_still_present():
    """The missing-metric model survives with its empty-string metric: the
    model IS present in the task file and its f1 is still ``""`` — only the
    ranking in summarize_comparison excludes missing metrics."""
    doc = json.loads(
        (SYNTHETIC_TASKS_DIR / "FakeDS__missing_task_task_performance.json")
        .read_text(encoding="utf-8")
    )
    assert "fake-gamma" in doc["performance"]
    assert doc["performance"]["fake-gamma"]["performance"]["f1"] == ""
    # TEST-02 float policy: every float assertion goes through pytest.approx.
    assert doc["performance"]["fake-alpha"]["performance"]["f1"] == pytest.approx(0.7)
    assert doc["performance"]["fake-beta"]["performance"]["f1"] == pytest.approx(0.8)


def test_pivot_shape_exporter_emission_owns_the_shape(tmp_path):
    """The exporter's own emission carries the same pivot shape: one file
    per dataset named ``{task}_task_performance.json``, an 8-key info block,
    and the 11/9/14 (model/parameters/performance) key sets per model."""
    out, _ = _export(tmp_path)
    assert sorted(p.name for p in out.iterdir()) == [
        "FakeDS__task_task_performance.json",
    ]
    doc = json.loads((out / "FakeDS__task_task_performance.json").read_text(encoding="utf-8"))
    assert set(doc["info"]) == {
        "dev", "labels", "length", "metric", "species", "test", "train", "type",
    }
    assert set(doc["performance"]) == {"FakeModel-A", "FakeModel-B"}
    for block in doc["performance"].values():
        assert len(block["model"]) == 11
        assert len(block["parameters"]) == 9
        assert len(block["performance"]) == 14


def test_pivot_shape_exporter_sanitizes_task_filenames(tmp_path):
    """Task names carrying ``\\\\`` are sanitized to ``_`` in emitted
    filenames (a legal path component on POSIX, so it reaches the live
    emission path). The ``/`` half of the retired pivot test's surface is
    structurally unreachable through the exporter's F2 directory walk — a
    path component can never contain ``/`` — and stays in the sanitizer as
    defense-in-depth at the emission boundary."""
    root, models_path, datasets_path, config_path = _build_fixture_tree(tmp_path)
    datasets = json.loads(datasets_path.read_text(encoding="utf-8"))
    raw_task = "Fake\\Src__task"
    datasets[raw_task] = dict(datasets["FakeDS__task"], Dataset_name=raw_task)
    datasets_path.write_text(json.dumps(datasets), encoding="utf-8")
    _write_run_record(root, "FakeModel-A", raw_task, 42, _suite_native_metrics(0.9))
    out = tmp_path / "out"
    stats = tmp_path / "stats"
    export_runs.export_runs_tree(
        root, models_path, datasets_path, config_path, out, stats,
        n_bootstrap=100, bootstrap_seed=42, small_n_ci="t-interval",
    )
    sanitized = out / "Fake_Src__task_task_performance.json"
    assert sanitized.exists()
    doc = json.loads(sanitized.read_text(encoding="utf-8"))
    assert doc["performance"]["FakeModel-A"]["performance"]["auroc"] == pytest.approx(0.9)


def test_hard_edges_missing_flops_unregistered_one_seed(tmp_path):
    root, models_path, datasets_path, config_path = _build_fixture_tree(tmp_path)

    # 1. A completed record missing total_flos: actionable hard error naming
    #    the key and the record path (never 0, never "").
    bad = root / "FakeModel-A" / "FakeDS__task" / "seed_42" / "run_record.json"
    record = json.loads(bad.read_text(encoding="utf-8"))
    original_flos = record["metrics"]["total_flos"]
    del record["metrics"]["total_flos"]
    bad.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(RuntimeError, match=r"total_flos.*seed_42/run_record\.json"):
        export_runs.export_runs_tree(
            root, models_path, datasets_path, config_path,
            tmp_path / "o1", tmp_path / "s1",
            n_bootstrap=100, bootstrap_seed=42, small_n_ci="t-interval",
        )
    # Restore the record so the later edges exercise THEIR failure mode.
    record["metrics"]["total_flos"] = original_flos
    bad.write_text(json.dumps(record), encoding="utf-8")

    # 2. Unregistered dataset: KeyError hard fail (no fallback join).
    _write_run_record(root, "FakeModel-A", "NotInRegistry__x", 42, _suite_native_metrics(0.9))
    with pytest.raises(KeyError, match="NotInRegistry__x"):
        export_runs.export_runs_tree(
            root, models_path, datasets_path, config_path,
            tmp_path / "o2", tmp_path / "s2",
            n_bootstrap=100, bootstrap_seed=42, small_n_ci="t-interval",
        )

    # 3. Unregistered model: KeyError hard fail.
    _write_run_record(root, "GhostModel", "FakeDS__task", 42, _suite_native_metrics(0.9))
    with pytest.raises(KeyError, match="GhostModel"):
        export_runs.export_runs_tree(
            root, models_path, datasets_path, config_path,
            tmp_path / "o3", tmp_path / "s3",
            n_bootstrap=100, bootstrap_seed=42, small_n_ci="t-interval",
        )


def test_one_seed_cell_emits_degenerate_statistics(tmp_path):
    root, models_path, datasets_path, config_path = _build_fixture_tree(
        tmp_path, include_failed=False
    )
    # Drop FakeModel-B to a single completed seed.
    import shutil
    shutil.rmtree(root / "FakeModel-B" / "FakeDS__task" / "seed_8")
    shutil.rmtree(root / "FakeModel-B" / "FakeDS__task" / "seed_9")
    out = tmp_path / "out"
    stats_dir = tmp_path / "stats"
    export_runs.export_runs_tree(
        root, models_path, datasets_path, config_path, out, stats_dir,
        n_bootstrap=100, bootstrap_seed=42, small_n_ci="t-interval",
    )
    doc = json.loads((out / "FakeDS__task_task_performance.json").read_text(encoding="utf-8"))
    jsonschema.validate(instance=doc, schema=SCHEMA)
    assert doc["performance"]["FakeModel-B"]["performance"]["auroc"] == pytest.approx(0.70)
    stats = json.loads((stats_dir / "FakeDS__task_seed_stats.json").read_text(encoding="utf-8"))
    block = stats["FakeModel-B"]["auroc"]["stats"]
    assert block == {
        "n_seeds": 1, "mean": 0.70, "sd": None, "ci95": None, "method": "none",
    }


def test_export_is_byte_stable_across_runs(tmp_path):
    """Two exports of the same tree produce byte-identical files."""
    outs = []
    for run in (1, 2):
        root, models_path, datasets_path, config_path = _build_fixture_tree(tmp_path / f"tree{run}")
        out = tmp_path / f"out{run}"
        stats = tmp_path / f"stats{run}"
        export_runs.export_runs_tree(
            root, models_path, datasets_path, config_path, out, stats,
            n_bootstrap=2000, bootstrap_seed=42, small_n_ci="t-interval",
        )
        outs.append((out, stats))
    (out1, stats1), (out2, stats2) = outs
    files1 = sorted(p.name for p in out1.iterdir()) + sorted(p.name for p in stats1.iterdir())
    files2 = sorted(p.name for p in out2.iterdir()) + sorted(p.name for p in stats2.iterdir())
    assert files1 == files2
    for name in files1:
        for d1, d2 in ((out1, out2), (stats1, stats2)):
            p1, p2 = d1 / name, d2 / name
            if p1.exists() and p2.exists():
                assert p1.read_bytes() == p2.read_bytes(), f"{name} not byte-stable"


# =====================================================================
# D-15: HuggingFace evaluate cross-validation (metrics layer)
# =====================================================================

def test_d15_evaluate_cross_validates_suite_mapped_metric_conventions():
    """D-15: evaluate's standard implementations agree with independently
    derived expected values on golden vectors, for metrics the exporter's
    mapping surface covers (pearsonr -> pearson_r, spearmanr -> spearman_r).

    evaluate's accuracy/f1/mcc modules import scikit-learn, which is outside
    the sanctioned D-15 dependency pair (scipy + evaluate); extending the
    cross-check to count metrics requires a maintainer-approved
    scikit-learn addition (deferred — noted, not built).
    """
    import evaluate

    def pearson_formula(xs, ys):
        """r = cov(x, y) / (sd(x) * sd(y)), ddof=1 — derived here, not imported."""
        x = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
        cov = float(((x - x.mean()) * (y - y.mean())).sum() / (len(x) - 1))
        return cov / (float(x.std(ddof=1)) * float(y.std(ddof=1)))

    def ranks(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        out = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            for k in range(i, j + 1):
                out[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return out

    y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
    y_pred = [1.1, 2.2, 2.8, 4.4, 4.9]      # near-perfect linear
    y_pred2 = [1.1, 4.4, 2.8, 2.2, 4.9]     # non-monotone permutation

    got_pearson = evaluate.load("pearsonr").compute(
        predictions=y_pred, references=y_true
    )["pearsonr"]
    # evaluate's pearsonr wraps scipy.stats.pearsonr but buffers inputs
    # through its Arrow metric pipeline, which perturbs the last digits at
    # a characterized ~3.3e-9 scale on this golden case (its spearmanr is
    # bit-exact). 1e-8 stays orders below any real convention drift (a
    # wrong formula errs at O(1e-2)), so the cross-check remains a red-on-
    # drift trip wire.
    assert got_pearson == pytest.approx(pearson_formula(y_true, y_pred), abs=1e-8)

    got_pearson2 = evaluate.load("pearsonr").compute(
        predictions=y_pred2, references=y_true
    )["pearsonr"]
    assert got_pearson2 == pytest.approx(pearson_formula(y_true, y_pred2), abs=1e-8)

    got_spearman = evaluate.load("spearmanr").compute(
        predictions=y_pred2, references=y_true
    )["spearmanr"]
    expected_spearman = pearson_formula(ranks(y_true), ranks(y_pred2))
    assert got_spearman == pytest.approx(expected_spearman, abs=1e-9)

    # The cross-checked metrics are exactly the suite-mapped export slots —
    # the evaluate layer verifies the conventions the mapping carries.
    assert export_runs.resolve_metric_key("pearsonr") == "pearson_r"
    assert export_runs.resolve_metric_key("spearmanr") == "spearman_r"
