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
from export_runs import aggregate_seeds, resolve_dataset_metric
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


# ===== F6 CI-overlap tie rule (05-02, REV-04) =====
#
# The intervals the tie rule CONSUMES are produced by the vendored
# ``aggregate_seeds`` (F6 statistical-semantics correction, binding): n<3 ->
# ci95 None / method "none"; 3<=n<10 -> t-interval (df = n-1); n>=10 ->
# seeded bootstrap. E2' 3-seed data therefore gets t-intervals (df=2), never
# bootstrap. Statistical tests below build every interval through the vendored
# function; the boundary/adjacency probes pass plain numeric intervals to pin
# the RULE's comparison semantics (closed intervals, connected components) —
# they are rule-semantics probes, not interval producers.


def _ci_map_from_seeds(per_model_seeds):
    """Build ``{model: (lo, hi) | None}`` via the vendored ``aggregate_seeds``.

    Args:
        per_model_seeds: ``{model: [per-seed metric values]}``.

    Returns:
        The ci_map consumable by :func:`calculate_dataset_stats`. A seed set
        with ``n < CI_MIN_SEEDS`` yields ``None`` (method "none") — the rule
        never fabricates an interval for it.
    """
    ci_map = {}
    for model, seeds in per_model_seeds.items():
        block = aggregate_seeds(
            seeds, n_bootstrap=2000, bootstrap_seed=42, small_n_ci="t-interval"
        )
        ci_map[model] = tuple(block["ci95"]) if block["ci95"] is not None else None
    return ci_map


def test_ci_overlap_intervals_share_min_rank():
    """Two models whose closed 95% intervals intersect share the group's
    minimum rank even though their raw scores differ — the CI-overlap rule
    widens "tie" from exact equality to interval overlap. A far-below model
    keeps its own rank, and ``task_rank_score = N - rank`` stays coherent."""
    seeds = {
        "top-a": [0.9300, 0.9310, 0.9320],  # mean .9310, sd .001 -> t-interval
        "top-b": [0.9279, 0.9289, 0.9299],  # mean .9289 — interval overlaps top-a
        "low-c": [0.8100, 0.8120, 0.8140],  # far below — no overlap with anyone
    }
    stats = calculate_dataset_stats(
        {"top-a": 0.9310, "top-b": 0.9289, "low-c": 0.8120},
        ci_map=_ci_map_from_seeds(seeds),
    )
    assert stats["top-a"]["rank"] == 1
    assert stats["top-b"]["rank"] == 1  # overlap with top-a -> shares the min rank
    assert stats["low-c"]["rank"] == 3
    assert stats["top-a"]["task_rank_score"] == 2
    assert stats["top-b"]["task_rank_score"] == 2
    assert stats["low-c"]["task_rank_score"] == 0


def test_closed_interval_touch_point_is_a_tie():
    """Boundary probe: intervals touching at exactly one point (``lo_a ==
    hi_b``) are a tie — the overlap test runs on CLOSED intervals."""
    stats = calculate_dataset_stats(
        {"a": 0.90, "b": 0.89, "c": 0.80},
        ci_map={"a": (0.89, 0.91), "b": (0.87, 0.89), "c": (0.79, 0.81)},
    )
    assert stats["a"]["rank"] == 1
    assert stats["b"]["rank"] == 1  # touching at 0.89 is a tie
    assert stats["c"]["rank"] == 3


def test_adjacent_overlaps_merge_into_one_tie_group():
    """Adjacency probe: A~B overlap and B~C overlap while A and C do NOT
    overlap — all three form ONE tie group (connected components of the
    overlap graph) and share the group's minimum rank."""
    stats = calculate_dataset_stats(
        {"a": 0.90, "b": 0.87, "c": 0.84},
        ci_map={"a": (0.885, 0.895), "b": (0.860, 0.890), "c": (0.835, 0.865)},
    )
    # A-B overlap (0.885 <= 0.890); B-C overlap (0.860 <= 0.865);
    # A-C gap (0.865 < 0.885) — yet all three tie via B.
    for model in ("a", "b", "c"):
        assert stats[model]["rank"] == 1
        assert stats[model]["task_rank_score"] == 2


def test_ci_map_none_and_missing_entries_reproduce_exact_tie_output():
    """Empty rule: ``ci_map=None``, all-``None`` entries, or a partial map
    (only interval-bearing models join the overlap graph) all reproduce the
    exact-tie output byte-identically — pre-E2' single-run data has no CI
    source and the rule is vacuous on it by design."""
    records = {"a": 0.9, "b": 0.9, "c": 0.8}
    plain = calculate_dataset_stats(records)
    assert calculate_dataset_stats(records, ci_map=None) == plain
    all_none = calculate_dataset_stats(
        records, ci_map={"a": None, "b": None, "c": None}
    )
    assert all_none == plain
    partial = calculate_dataset_stats(
        records, ci_map={"a": (0.89, 0.91), "b": None, "c": None}
    )
    assert partial == plain  # a's lone interval overlaps nobody -> base ranks


def test_cpg_replica_top_models_tie_under_n3_t_intervals():
    """The CpG case (BEND__CpG_methylation): the committed top-10 AUPRC values
    span 0.0021039 (0.9929629 - 0.9908590, verified live in committed data).
    With 3-seed data the vendored statistics report t-intervals (df=2) whose
    half-width (~t.ppf(0.975,2) * sd / sqrt(3) ~ 0.0025 at sd 0.001) exceeds
    that span — so the top models TIE under the CI-overlap rule. Every
    interval comes from the vendored ``aggregate_seeds`` at n=3 with method
    "t" — never bootstrap (F6 statistical-semantics correction)."""
    seeds = {
        # per-seed AUPRC replicas around the committed CpG top-10 anchors
        # (top-1 / top-2 / top-10 means; +/-0.001 per-seed spread, the
        # e2_replay fixture's magnitude)
        "cpg-top1": [0.9919629, 0.9929629, 0.9939629],
        "cpg-top2": [0.9914298, 0.9924298, 0.9934298],
        "cpg-top10": [0.9898590, 0.9908590, 0.9918590],
    }
    means = {m: sum(v) / len(v) for m, v in seeds.items()}
    span = max(means.values()) - min(means.values())
    assert span == pytest.approx(0.0021039, abs=1e-6)  # the CpG top-10 span

    ci_map = {}
    for model, vals in seeds.items():
        block = aggregate_seeds(
            vals, n_bootstrap=2000, bootstrap_seed=42, small_n_ci="t-interval"
        )
        assert block["n_seeds"] == 3
        assert block["method"] == "t"  # t-interval df=2 — never bootstrap at n=3
        ci_map[model] = tuple(block["ci95"])

    stats = calculate_dataset_stats(means, ci_map=ci_map)
    for model in seeds:
        assert stats[model]["rank"] == 1  # every top model ties at rank 1
        assert stats[model]["task_rank_score"] == 2
    # Without intervals the same means rank distinctly — the tie is the
    # rule's doing, not the scores'.
    plain = calculate_dataset_stats(means)
    assert sorted(s["rank"] for s in plain.values()) == [1, 2, 3]


# ===== F6 weighted score (05-02, REV-04/F6 Q2) =====


def test_weighted_score_is_uniform_difficulty_normalized_zscore_sum():
    """``weighted_score = sum of per-task zscore / len(target_datasets)`` —
    the aggregation view's task count as a uniform 1/N difficulty weight
    (F6 Q2). A model missing tasks contributes nothing for them (no
    imputation): the numerator excludes the missing task while the
    denominator still counts the view's full task set. The default call does
    NOT emit the key — the emission stays unwired until the migration commit."""
    models_info, stats_map, flops_map, datasets = _load_synthetic_inputs()
    n_view = len(datasets)

    result = aggregate_models(
        models_info, stats_map, flops_map, datasets, include_weighted=True
    )
    for entry in result.values():
        perf = entry["performance"]
        assert "weighted_score" in perf
        assert perf["weighted_score"] == pytest.approx(perf["sum_zscore"] / n_view)
    # fake-gamma misses FakeDS__missing_task: numerator covers 2 tasks, the
    # denominator still divides by the view's 3 — the no-imputation contract.
    assert result["fake-gamma"]["performance"]["samples"] == 2
    assert result["fake-gamma"]["performance"]["weighted_score"] == pytest.approx(
        result["fake-gamma"]["performance"]["sum_zscore"] / 3
    )

    default_result = aggregate_models(models_info, stats_map, flops_map, datasets)
    assert all(
        "weighted_score" not in e["performance"] for e in default_result.values()
    )


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
