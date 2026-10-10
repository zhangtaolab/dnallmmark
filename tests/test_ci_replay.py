"""
Canned golden replay over the committed tests/fixtures/e2_replay fixture
(REV-06 Q1, subsuming TEST-04/TEST-05/TEST-07's CI lane contents).

Proves the phase's data chain end-to-end on CPU-only committed artifacts —
no real training ever runs here (CI feasibility constraint):

- **Export half:** ``export_runs.export_runs_tree()`` over the committed
  run-record tree emits a task file validating against
  ``schemas/task_performance.json``, and its ``seed_stats`` artifact reports
  ``n_seeds == 3`` with ``method == "t"`` and a two-float ``ci95`` — the
  vendored n-guard semantics (F6 correction: ``3 <= n < 10`` is a t-interval
  at df=2, NEVER bootstrap). The fixture's A/B pair is the deliberate input
  for 05-02's CI-overlap tie rule: their AUPRC means sit exactly the
  committed CpG top-10 span (0.0021) apart, so their n=3 t-intervals
  OVERLAP, while model C is clearly separated — pinned here so the fixture
  cannot silently drift away from that purpose.
- **Byte-stability (export):** exporting the same fixture twice produces
  byte-identical outputs (sorted iteration, sort_keys, no live clock).
- **Aggregate half:** ``summarize_comparison.main()`` over a tmp copy of
  ``tests/fixtures/synthetic_models/`` (synthetic registry slice injected
  the way ``tests/test_golden.py`` does it) emits ``models_comparison.json``
  validating against ``schemas/models_comparison.json``, byte-stable across
  two runs.

The whole module is marked ``pytest.mark.ci`` — the pinned CI lane
(``make ci``) selects it plus the three reused test classes: metric-key
parity (``tests/test_export_runs.py``), species-table spot checks
(``tests/test_known_defects.py``), and aggregation units
(``tests/test_aggregation.py``).

See also:
    - ``tests/test_export_runs.py`` — the ephemeral-tree builders this
      committed fixture transcribes, and the exporter contract tests.
    - ``tests/test_golden.py`` — the registry-slice injection pattern the
      aggregate half reuses.
    - ``.github/workflows/ci.yml`` — the workflow whose ``test`` job runs
      this lane (05-01 Task 3).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import export_runs  # conftest puts script/ on sys.path
import pytest
import summarize_comparison
from jsonschema import Draft202012Validator

# The pinned CI lane marker — see pyproject.toml [tool.pytest.ini_options].
pytestmark = pytest.mark.ci

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "e2_replay"
SYNTHETIC_DIR = REPO_ROOT / "tests" / "fixtures" / "synthetic_models"
SYNTHETIC_REGISTRY = REPO_ROOT / "tests" / "fixtures" / "synthetic_datasets_info.json"

TASK = "FakeCpG__methylation"
TASK_FILE = f"{TASK}_task_performance.json"
STATS_FILE = f"{TASK}_seed_stats.json"
REPLAY_MODELS = ("ReplayModel-A", "ReplayModel-B", "ReplayModel-C")

TASK_SCHEMA = Draft202012Validator(
    json.loads((REPO_ROOT / "schemas" / "task_performance.json").read_text(encoding="utf-8"))
)
COMPARISON_SCHEMA = Draft202012Validator(
    json.loads((REPO_ROOT / "schemas" / "models_comparison.json").read_text(encoding="utf-8"))
)

# The synthetic tree yields one comparison file per species group plus the
# all-tasks file (tests/test_golden.py's COMPARISON_FILES).
COMPARISON_FILES = (
    "models_comparison.json",
    "models_comparison_animal.json",
    "models_comparison_plant.json",
    "models_comparison_microbe.json",
)


def _export_fixture(out: Path, stats: Path) -> list[str]:
    """Run the export half over the committed replay fixture tree.

    Args:
        out: Task-file destination directory.
        stats: Statistics-artifact destination directory.

    Returns:
        The sorted list of exported task names.
    """
    return export_runs.export_runs_tree(
        FIXTURE_DIR / "finetuned",
        FIXTURE_DIR / "models_info.json",
        FIXTURE_DIR / "datasets_info.json",
        FIXTURE_DIR / "finetune_config.yaml",
        out,
        stats,
        n_bootstrap=2000,
        bootstrap_seed=42,
        small_n_ci="t-interval",
    )


def _run_aggregate_half(work: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the aggregate half inside ``work`` (test_golden.py's pattern).

    Stages a tmp copy of the committed synthetic model tree as
    ``model_performance/``, chdirs into ``work``, injects the synthetic
    registry slice, and calls ``summarize_comparison.main()`` (which reads
    and writes CWD-relative paths).
    """
    staged = work / "model_performance"
    staged.mkdir()
    for fixture in sorted(SYNTHETIC_DIR.glob("*_performance.json")):
        shutil.copy(fixture, staged / fixture.name)
    monkeypatch.chdir(work)
    monkeypatch.setattr(summarize_comparison, "REGISTRY_PATH", SYNTHETIC_REGISTRY)
    summarize_comparison.main()


# =====================================================================
# Export half: schema validity + vendored n-guard statistics
# =====================================================================

def test_export_half_emits_schema_valid_task_file_with_n3_t_intervals(tmp_path):
    """The committed replay fixture exports to a schema-valid task file whose
    seed_stats carry n_seeds=3 t-intervals with two-float ci95 bounds — the
    vendored n-guard semantics (3 <= n < 10 -> t at df=2; never bootstrap)."""
    out, stats_dir = tmp_path / "out", tmp_path / "stats"
    emitted = _export_fixture(out, stats_dir)
    assert emitted == [TASK]

    doc = json.loads((out / TASK_FILE).read_text(encoding="utf-8"))
    errors = list(TASK_SCHEMA.iter_errors(doc))
    assert not errors, "\n".join(f"- {'/'.join(map(str, e.path))}: {e.message}" for e in errors)

    stats = json.loads((stats_dir / STATS_FILE).read_text(encoding="utf-8"))
    assert set(stats) == set(REPLAY_MODELS)
    for model in REPLAY_MODELS:
        block = stats[model]["auprc"]["stats"]
        assert block["n_seeds"] == 3, model
        assert block["method"] == "t", model  # NOT "bootstrap-percentile", NOT "none"
        ci95 = block["ci95"]
        assert isinstance(ci95, list) and len(ci95) == 2, model
        assert all(isinstance(bound, float) for bound in ci95), model
        assert ci95[0] < ci95[1], model
    # Per-seed disclosure: the committed values round-trip verbatim.
    assert stats["ReplayModel-A"]["auprc"]["per_seed"] == {
        "42": 0.93, "43": 0.931, "44": 0.932,
    }


def test_replay_fixture_intervals_a_b_overlap_c_separates(tmp_path):
    """The fixture's deliberate tie-rule geometry (05-02's input): A and B
    sit exactly the committed CpG top-10 span (0.0021) apart, so their n=3
    t-intervals OVERLAP, while C's interval is clearly separated from A's."""
    stats_dir = tmp_path / "stats"
    _export_fixture(tmp_path / "out", stats_dir)
    stats = json.loads((stats_dir / STATS_FILE).read_text(encoding="utf-8"))

    ci = {
        model: stats[model]["auprc"]["stats"]["ci95"]
        for model in REPLAY_MODELS
    }
    mean = {
        model: stats[model]["auprc"]["stats"]["mean"]
        for model in REPLAY_MODELS
    }
    # The CpG top-10 span mirror: A's mean sits 0.0021 above B's.
    assert mean["ReplayModel-A"] - mean["ReplayModel-B"] == pytest.approx(0.0021)
    # Overlapping intervals (each interval's low bound is below the other's
    # high bound) — the CI-overlap tie rule's deliberate input pair.
    assert ci["ReplayModel-A"][0] < ci["ReplayModel-B"][1]
    assert ci["ReplayModel-B"][0] < ci["ReplayModel-A"][1]
    # Model C is clearly lower: its entire interval sits below A's low bound.
    assert ci["ReplayModel-C"][1] < ci["ReplayModel-A"][0]


def test_export_half_is_byte_stable_across_two_runs(tmp_path):
    """Two exports of the same committed fixture produce byte-identical
    task files and seed_stats artifacts (deterministic chain: sorted
    iteration, sort_keys, seeded statistics, no live clock)."""
    runs = []
    for run in (1, 2):
        out, stats_dir = tmp_path / f"out{run}", tmp_path / f"stats{run}"
        _export_fixture(out, stats_dir)
        runs.append((out, stats_dir))
    (out1, stats1), (out2, stats2) = runs
    for d1, d2 in ((out1, out2), (stats1, stats2)):
        names1 = sorted(p.name for p in d1.iterdir())
        names2 = sorted(p.name for p in d2.iterdir())
        assert names1 == names2
        for name in names1:
            assert (d1 / name).read_bytes() == (d2 / name).read_bytes(), (
                f"{name} not byte-stable across runs"
            )


# =====================================================================
# Aggregate half: schema validity + byte-stability
# =====================================================================

def test_aggregate_half_emits_schema_valid_byte_stable_comparison(tmp_path, monkeypatch):
    """``summarize_comparison.main()`` over a tmp copy of the committed
    synthetic model tree (registry slice injected, the test_golden.py
    pattern) emits models_comparison files validating against
    schemas/models_comparison.json, byte-identical across two runs."""
    outputs = []
    for run in (1, 2):
        work = tmp_path / f"work{run}"
        work.mkdir()
        _run_aggregate_half(work, monkeypatch)
        main_file = work / "models_comparison.json"
        assert main_file.exists(), "chain did not produce models_comparison.json"
        doc = json.loads(main_file.read_text(encoding="utf-8"))
        errors = list(COMPARISON_SCHEMA.iter_errors(doc))
        assert not errors, "\n".join(
            f"- {'/'.join(map(str, e.path))}: {e.message}" for e in errors
        )
        produced = sorted(p.name for p in work.glob("models_comparison*.json"))
        assert produced == sorted(COMPARISON_FILES)
        outputs.append({
            name: (work / name).read_bytes() for name in produced
        })
    assert outputs[0] == outputs[1], "aggregate half not byte-stable across runs"
