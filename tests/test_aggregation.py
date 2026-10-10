"""
Unit tests for the aggregation pure functions in ``script/summarize_comparison.py``.

Every function under test is importable and side-effect-free (conftest puts
``script/`` on ``sys.path``). The tests assert hand-computed expectations over
synthetic inputs, including the edge cases engineered into
``tests/fixtures/synthetic_models/`` (exact-tie pair, missing metric, constant
scores) — synthetic tests never substitute for real data (D-09); only the
02-03 determinism test touches the real tree.

Float policy (TEST-02): every float assertion goes through ``pytest.approx``
(``calculate_dataset_stats`` returns ``np.float64`` scalars); ints (rank,
samples, counts) use plain ``==``.

``get_float``'s non-finite handling was flipped in Phase 4 (D-13/WR-03,
plan 04-01 Task 2): ``'nan'``/``'inf'``/``'-inf'`` now return the default
via a ``math.isfinite`` guard applied after ``float()`` coercion — they
previously passed through the ``default=None`` presence gate as non-finite
floats (the 02-03 WR-03 ``xfail(strict=True)`` lock's defect, now unmarked
in the same commit). Finite coercion and the ``''``/``None``/garbage-string
semantics below are unchanged.

See also:
    - ``tests/test_export_runs.py`` — the pivot-shape owner + the metric-key
      mapping's single authority (IN-03 parity over both key surfaces).
    - ``tests/test_golden.py`` — full synthetic-chain golden comparison.
"""

import json
import os
from pathlib import Path

import pytest
from export_runs import resolve_dataset_metric
from summarize_comparison import (
    aggregate_models,
    calculate_dataset_stats,
    get_float,
    to_singular_species,
)

# Pinned CI lane (Phase 5, REV-06 Q2): `make ci` (`pytest -m ci`) selects
# this module's aggregation-unit tests alongside the golden replay — the
# marker adds lane membership only, no behavior change.
pytestmark = pytest.mark.ci

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DIR = REPO_ROOT / "tests" / "fixtures" / "synthetic_models"

# IN-03 (04-05): the metric-key translation is IMPORTED from the exporter —
# the single authority owns both key surfaces (suite canonicals + the legacy
# dataset-metric spellings). dataset metadata declares "spearmanr" while the
# performance block stores the value under "spearman_r"; the old local
# minimal-copy mapping was deleted with summarize_comparison's mirror.


def _load_synthetic_inputs():
    """Build aggregation inputs from the committed synthetic fixture tree.

    Mirrors ``summarize_comparison.main()``'s extraction exactly: the primary
    metric per dataset, the ``get_float(default=None)`` presence gate (a
    missing/empty metric excludes the model from that task's ranking but keeps
    its FLOPs), and the 7-key leaderboard model-card subset.

    Returns:
        Tuple ``(models_info, dataset_stats_map, raw_dataset_flops, datasets)``
        ready to pass to :func:`aggregate_models`.
    """
    models_info = {}
    raw_dataset_scores = {}
    raw_dataset_flops = {}

    for path in sorted(SYNTHETIC_DIR.glob("*_performance.json")):
        alias = path.name.replace("_performance.json", "")
        doc = json.loads(path.read_text(encoding="utf-8"))
        models_info[alias] = {
            k: v for k, v in doc["info"].items()
            if k in ["name", "size (M)", "type", "tokenizer", "series",
                     "context_len (bp)", "species"]
        }
        for ds_name, ds_content in doc["performance"].items():
            metric_key = resolve_dataset_metric(ds_content["dataset"]["metric"])
            raw_score = get_float(
                ds_content["performance"].get(metric_key, ""), default=None
            )
            if raw_score is not None:
                raw_dataset_scores.setdefault(ds_name, {})[alias] = raw_score
            raw_dataset_flops.setdefault(ds_name, {})[alias] = get_float(
                ds_content["performance"].get("FLOPs", "")
            )

    dataset_stats_map = {
        ds: calculate_dataset_stats(scores)
        for ds, scores in raw_dataset_scores.items()
    }
    return models_info, dataset_stats_map, raw_dataset_flops, list(raw_dataset_scores)


# ===== get_float =====


@pytest.mark.parametrize("bad", ["nan", "inf", "-inf"])
def test_get_float_nonfinite_returns_default(bad):
    """``'nan'``/``'inf'``/``'-inf'`` coerce successfully but the value is
    non-finite, so the isfinite guard (WR-03, flipped Phase 4) returns the
    default — a non-finite metric is excluded from ranking instead of
    passing the ``default=None`` presence gate and poisoning a whole
    task's MinMax/z-score normalization.
    """
    assert get_float(bad, default=None) is None
    assert get_float(bad, default=0.0) == 0.0


@pytest.mark.parametrize(
    "missing",
    ["", "   ", "\t\n", None, "abc", "not a number", "nan_adjacent_garbage"],
)
def test_get_float_missing_and_garbage_return_default(missing):
    """``''``, whitespace-only, ``None``, and non-numeric strings return the
    default (the presence-gate semantics that exclude a model from ranking)."""
    assert get_float(missing, default=0.0) == 0.0
    assert get_float(missing, default=None) is None


@pytest.mark.parametrize("val", ["1.5", "0.9", 2, 3, "2381648367043584.0"])
def test_get_float_numeric_values_coerce(val):
    """Numeric strings and ints coerce to ``float``."""
    assert get_float(val) == pytest.approx(float(val))


# ===== calculate_dataset_stats =====


def test_exact_tie_shares_min_rank():
    """The engineered tie pair: ``method='min'`` gives both 0.9 scores shared
    rank 1 (and ``N - rank`` = 2 each), 0.8 gets rank 3 and score 0."""
    stats = calculate_dataset_stats({"a": 0.9, "b": 0.9, "c": 0.8})
    assert stats["a"]["rank"] == 1
    assert stats["b"]["rank"] == 1
    assert stats["c"]["rank"] == 3
    assert stats["a"]["task_rank_score"] == 2
    assert stats["b"]["task_rank_score"] == 2
    assert stats["c"]["task_rank_score"] == 0
    assert stats["a"]["minmax"] == pytest.approx(1.0)
    assert stats["b"]["minmax"] == pytest.approx(1.0)
    assert stats["c"]["minmax"] == pytest.approx(0.0)


def test_one_step_off_the_tie_changes_rank_structure():
    """Boundary probe: one step below the tie (0.89) breaks the equality
    branch — ranks become distinct 1/2/3, proving the tie branch above is a
    genuine equality branch rather than a rounding artifact."""
    stats = calculate_dataset_stats({"a": 0.9, "b": 0.89, "c": 0.8})
    assert stats["a"]["rank"] == 1
    assert stats["b"]["rank"] == 2
    assert stats["c"]["rank"] == 3
    assert stats["a"]["task_rank_score"] == 2
    assert stats["b"]["task_rank_score"] == 1
    assert stats["c"]["task_rank_score"] == 0
    assert stats["b"]["minmax"] == pytest.approx(0.9)


def test_constant_scores_rank_all_first_and_normalize_to_zero():
    """Constant-score task: every model gets rank 1 and ``task_rank_score``
    ``N - 1``, and all three zero-variance guards (``min == max``, ``std ==
    0``, ``iqr == 0``) take their zero branches.

    The constant 0.5 is binary-exact: its 3-element mean round-trips exactly,
    so ``std`` is exactly 0.0 and the guard fires. (A decimal constant like
    0.7 does NOT trigger the guard — see
    :func:`test_constant_decimal_scores_do_not_fire_std_guard`.)
    """
    stats = calculate_dataset_stats({"a": 0.5, "b": 0.5, "c": 0.5})
    for model in ("a", "b", "c"):
        assert stats[model]["rank"] == 1
        assert stats[model]["task_rank_score"] == 2
        assert stats[model]["minmax"] == pytest.approx(0.0)
        assert stats[model]["zscore"] == pytest.approx(0.0)
        assert stats[model]["robust"] == pytest.approx(0.0)


def test_constant_decimal_scores_do_not_fire_std_guard():
    """Float-reality companion (found live while pinning the constant case):
    a NON-binary-exact constant such as 0.7 has a 3-element mean one ULP
    below the value, so ``std`` is one ULP above zero and the ``std > 0``
    guard does NOT take its zero branch — zscore degenerates to a constant
    (e.g. 1.0) instead of 0.0.

    The exact degenerate constant is ULP-level numpy behavior and is NOT
    pinned; the ranking-relevant invariant is that every model receives the
    SAME normalization value, so a constant-score task never distorts
    ordering. ``minmax`` and ``robust`` are unaffected (``min == max`` and
    ``iqr == 0`` compare exact values and do fire).
    """
    stats = calculate_dataset_stats({"a": 0.7, "b": 0.7, "c": 0.7})
    zscores = {stats[m]["zscore"] for m in ("a", "b", "c")}
    assert len(zscores) == 1, "constant scores must normalize identically for all models"
    for model in ("a", "b", "c"):
        assert stats[model]["rank"] == 1
        assert stats[model]["minmax"] == pytest.approx(0.0)
        assert stats[model]["robust"] == pytest.approx(0.0)


def test_empty_records_return_empty_dict():
    """A task with no scored models yields ``{}`` (no division-by-zero)."""
    assert calculate_dataset_stats({}) == {}


# ===== to_singular_species =====


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Animals", "animal"),   # committed plural form (mapping row)
        ("Plants", "plant"),     # committed plural form (mapping row)
        ("Microbes", "microbe"), # plural mapping row
        ("Microbe", "microbe"),  # committed singular enum value (lowercase passthrough)
        ("Mouse", "mouse"),      # unmapped label passes through lowercased
    ],
)
def test_to_singular_species(label, expected):
    """Species labels normalize to singular lowercase for filenames."""
    assert to_singular_species(label) == expected


# ===== aggregate_models (fixture-driven) =====


def test_aggregate_totals_and_final_rank_over_synthetic_tree():
    """Hand-computed totals over the synthetic scores.

    tie_task   (f1):        alpha .9 / beta .9 / gamma .8  → scores 2/2/0
    missing_task (f1):      alpha .7 / beta .8 (gamma excluded) → scores 0/1
    regress_task (spearman): alpha .5 / beta .6 / gamma .4  → scores 1/2/0

    Totals: beta 2+1+2 = 5, alpha 2+0+1 = 3, gamma 0+0 = 0 (gamma is rank 3
    of 3 on regress_task — the lowest spearmanr), giving final overall rank
    1/2/3 for beta/alpha/gamma.
    """
    models_info, stats_map, flops_map, datasets = _load_synthetic_inputs()
    result = aggregate_models(models_info, stats_map, flops_map, datasets)

    assert result["fake-beta"]["performance"]["rank_score"] == pytest.approx(5.0)
    assert result["fake-alpha"]["performance"]["rank_score"] == pytest.approx(3.0)
    assert result["fake-gamma"]["performance"]["rank_score"] == pytest.approx(0.0)
    assert result["fake-beta"]["performance"]["rank"] == 1
    assert result["fake-alpha"]["performance"]["rank"] == 2
    assert result["fake-gamma"]["performance"]["rank"] == 3
    # The leaderboard model-card subset flows through (7 keys of the 11).
    assert result["fake-beta"]["model"]["name"] == "Fake Beta"


def test_missing_metric_excludes_model_from_that_tasks_ranking():
    """``samples`` reflects only tasks the model was scored on: fake-gamma's
    empty-string f1 on FakeDS__missing_task excludes it from that task's
    ranking, and the remaining two models' N (and therefore scores) are
    unaffected — alpha/beta keep ``samples == 3``, gamma has ``samples == 2``."""
    models_info, stats_map, flops_map, datasets = _load_synthetic_inputs()

    # The excluded task's stats contain only the two present models.
    assert set(stats_map["FakeDS__missing_task"]) == {"fake-alpha", "fake-beta"}

    result = aggregate_models(models_info, stats_map, flops_map, datasets)
    assert result["fake-alpha"]["performance"]["samples"] == 3
    assert result["fake-beta"]["performance"]["samples"] == 3
    assert result["fake-gamma"]["performance"]["samples"] == 2


def test_topk_counts_follow_true_ranks():
    """Top-K counts derive from the true (``method='min'``) ranks: beta is
    rank 1 on all three tasks, alpha only on the tie task, gamma never."""
    models_info, stats_map, flops_map, datasets = _load_synthetic_inputs()
    result = aggregate_models(models_info, stats_map, flops_map, datasets)

    assert result["fake-beta"]["performance"]["top1_count"] == 3
    assert result["fake-alpha"]["performance"]["top1_count"] == 1
    assert result["fake-gamma"]["performance"]["top1_count"] == 0
    assert result["fake-alpha"]["performance"]["avg_rank"] == pytest.approx(5 / 3)


def test_flops_converted_to_pflops_even_when_metric_missing():
    """FLOPs are recorded regardless of metric presence, so fake-gamma's
    sum_PFLOPs covers all three tasks while its rank_score covers two."""
    models_info, stats_map, flops_map, datasets = _load_synthetic_inputs()
    result = aggregate_models(models_info, stats_map, flops_map, datasets)

    assert result["fake-beta"]["performance"]["sum_PFLOPs"] == pytest.approx(
        (1100.0 + 2100.0 + 3100.0) / 1e15
    )
    assert result["fake-gamma"]["performance"]["sum_PFLOPs"] == pytest.approx(
        (1200.0 + 2200.0 + 3200.0) / 1e15
    )
    assert result["fake-gamma"]["performance"]["avg_PFLOPs"] == pytest.approx(
        (1200.0 + 2200.0 + 3200.0) / 3 / 1e15
    )


# ===== TEST-02 thread pinning =====


def test_thread_pinning_is_active_at_test_time():
    """TEST-02: conftest pins BLAS/OpenMP thread counts to '1' before any
    numpy import, so reductions stay single-threaded and reproducible."""
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        assert os.environ[var] == "1", f"{var} not pinned to '1'"
