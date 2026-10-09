"""
Integration test for the model→task pivot (``script/get_task_performance.py``).

The pivot logic lives inside ``main()`` with CWD-relative config locals, so
the test drives it under ``monkeypatch.chdir(tmp_path)`` over a copy of the
committed synthetic fixture tree — zero production-code changes (D-04).

Asserted semantics:

- one output file per dataset, named ``{dataset}_task_performance.json``;
- each ``info`` block mirrors the input ``dataset`` block verbatim;
- the model with the missing metric (``""`` f1) IS still present in the
  pivoted performance map — the pivot carries every model's record; only
  ranking excludes missing metrics;
- per-model blocks keep the 11/9/14 (model/parameters/performance) key shape;
- dataset names containing ``/`` or ``\\`` are sanitized to ``_`` in filenames.

See also:
    - ``tests/test_aggregation.py`` — the aggregation pure functions.
"""

import json
import shutil
from pathlib import Path

import get_task_performance
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DIR = REPO_ROOT / "tests" / "fixtures" / "synthetic_models"

DATASETS = ("FakeDS__tie_task", "FakeDS__missing_task", "FakeDS__regress_task")


def _stage_synthetic_models(tmp_path):
    """Copy the committed synthetic tree into ``tmp_path/model_performance/``.

    Args:
        tmp_path: pytest tmp dir the pivot will run against.

    Returns:
        The staged ``model_performance`` directory.
    """
    staged = tmp_path / "model_performance"
    staged.mkdir()
    for fixture in sorted(SYNTHETIC_DIR.glob("*_performance.json")):
        shutil.copy(fixture, staged / fixture.name)
    return staged


def test_pivot_produces_task_files_with_verbatim_info(tmp_path, monkeypatch):
    """``main()`` under chdir pivots the 3-model tree into exactly three
    task files whose info mirrors the dataset blocks byte-for-byte."""
    _stage_synthetic_models(tmp_path)
    monkeypatch.chdir(tmp_path)

    get_task_performance.main()

    out_dir = tmp_path / "task_performance"
    produced = {p.name for p in out_dir.glob("*.json")}
    expected = {f"{ds}_task_performance.json" for ds in DATASETS}
    assert produced == expected, produced

    alpha_fixture = json.loads(
        (SYNTHETIC_DIR / "fake-alpha_performance.json").read_text(encoding="utf-8")
    )
    for ds in DATASETS:
        doc = json.loads((out_dir / f"{ds}_task_performance.json").read_text(encoding="utf-8"))

        # info mirrors the input dataset block verbatim.
        assert doc["info"] == alpha_fixture["performance"][ds]["dataset"]

        # All three aliases are pivoted — including the missing-metric model.
        assert set(doc["performance"]) == {"fake-alpha", "fake-beta", "fake-gamma"}
        for block in doc["performance"].values():
            assert len(block["model"]) == 11
            assert len(block["parameters"]) == 9
            assert len(block["performance"]) == 14


def test_pivot_keeps_missing_metric_model_with_empty_string(tmp_path, monkeypatch):
    """fake-gamma's empty-string f1 on FakeDS__missing_task survives the pivot
    unchanged: the model is present, its f1 is still ``""`` (only the ranking
    in summarize_comparison excludes it)."""
    _stage_synthetic_models(tmp_path)
    monkeypatch.chdir(tmp_path)

    get_task_performance.main()

    doc = json.loads(
        (tmp_path / "task_performance" / "FakeDS__missing_task_task_performance.json")
        .read_text(encoding="utf-8")
    )
    assert "fake-gamma" in doc["performance"]
    assert doc["performance"]["fake-gamma"]["performance"]["f1"] == ""
    # TEST-02 float policy: fixture literals are JSON round-trips, but every
    # float assertion still goes through pytest.approx.
    assert doc["performance"]["fake-alpha"]["performance"]["f1"] == pytest.approx(0.7)
    assert doc["performance"]["fake-beta"]["performance"]["f1"] == pytest.approx(0.8)


def test_pivot_sanitizes_slashes_in_dataset_filenames(tmp_path, monkeypatch):
    """Dataset names carrying ``/`` and ``\\`` are sanitized to ``_`` in output
    filenames while the in-document key stays the original name."""
    staged = _stage_synthetic_models(tmp_path)
    model_doc = {
        "info": {"name": "Slash Model"},
        "performance": {
            "Fake/Src__task": {
                "dataset": {"species": "Microbe", "type": "binary", "labels": 2,
                            "train": 1, "test": 1, "dev": 1, "length": 100,
                            "metric": "f1"},
                "parameters": {},
                "performance": {"f1": 0.5},
            },
            "Fake\\Src2__task": {
                "dataset": {"species": "Microbe", "type": "binary", "labels": 2,
                            "train": 1, "test": 1, "dev": 1, "length": 100,
                            "metric": "f1"},
                "parameters": {},
                "performance": {"f1": 0.6},
            },
        },
    }
    (staged / "slash-model_performance.json").write_text(
        json.dumps(model_doc), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    get_task_performance.main()

    out_dir = tmp_path / "task_performance"
    assert (out_dir / "Fake_Src__task_task_performance.json").exists()
    assert (out_dir / "Fake_Src2__task_task_performance.json").exists()
    doc = json.loads(
        (out_dir / "Fake_Src__task_task_performance.json").read_text(encoding="utf-8")
    )
    assert doc["performance"]["slash-model"]["performance"]["f1"] == pytest.approx(0.5)
