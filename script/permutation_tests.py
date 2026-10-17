"""Pairwise permutation tests over the aggregate leaderboard view (F6 Q3, REV-04).

Purpose
-------
Publish, as a committed offline artifact, the pairwise model-comparison
evidence behind the leaderboard: for every model pair in the all-arena
aggregate view, a two-sided permutation test on the per-task zscore vectors
(``permutation_type="samples"`` — scipy's PAIRED permutation test: the two
models' observations are paired by task, and the null distribution flips the
sign of each per-task difference; D-17/OQ5's aggregate-view axis), 10,000
shuffles, ``rng``-seeded, BH-corrected over the pair family (C(42,2)=861
pre-E2'; C(62,2)=1891 post-E2') with the family size disclosed in the
artifact's ``info`` block. Runs offline at regeneration time (``make
data``), never at page render.

Direction of truth
------------------
The same inputs and the same normalization that produce
``models_comparison.json``: ``summarize_comparison.load_model_inputs`` (the
single extraction reader, 05-02) plus
``summarize_comparison.calculate_dataset_stats`` — imported, never
re-implemented. The statistics engine is scipy's
``stats.permutation_test`` (``permutation_type="samples"``, vectorized,
batched) and ``stats.false_discovery_control(method="bh")`` — never a
hand-rolled shuffle or BH loop (Don't Hand-Roll). Every RNG path is seeded
(``rng=42`` per pair, fresh per call so p-values are independent of pair
order; threat T-05-05 — reproducibility is the integrity control), and the
emitted JSON is canonical (sorted iteration, ``sort_keys=True``): the same
inputs regenerate a byte-identical artifact (tests/test_permutation.py).

Behavior
--------
map -> align -> permute -> correct -> emit:

1. map      per-model per-task zscores over the all-arena view (tasks where
            a model has no score are simply absent from its vector — the
            no-imputation convention);
2. align    each pair on its COMMON task set; a pair with zero common tasks
            is excluded from the family and disclosed under
            ``info.excluded_pairs``;
3. permute  scipy permutation_test, two-sided mean difference, 10,000
            shuffles, batch 100, rng 42;
4. correct  BH (Benjamini-Hochberg) over the tested-pair family;
            ``significant`` flags ``p_adj <= 0.05``;
5. emit     ``dnallm-mark/data/permutation_tests.json`` — an ``info`` block
            (family size, coverage rule, n_resamples, seed, batch, FDR
            method/level, exclusions) plus one row per tested pair.

Usage
-----
From the repo root (explicit REPO_ROOT-relative paths, mirroring
``script/export_runs.py`` — the documented CWD-convention break)::

    uv run --group data python script/permutation_tests.py

See also:
    - ``script/summarize_comparison.py`` — the aggregate view's producer and
      the source of the zscore vectors consumed here.
    - ``tests/test_permutation.py`` — the synthetic-matrix unit lane.
    - ``schemas/permutation_tests.json`` — the published artifact's contract.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats
from summarize_comparison import calculate_dataset_stats, load_model_inputs

REPO_ROOT = Path(__file__).resolve().parents[1]

# Disclosed methodology constants (T-05-05): every value is recorded in the
# artifact's info block; bumping any of them is a migration-commit act.
N_RESAMPLES = 10_000  # F6 Q3: 10,000 shuffles
SEED = 42             # rng seed, fresh per pair — p-values independent of order
BATCH = 100           # vectorized batch size (Pitfall 7: cost control)
FDR_LEVEL = 0.05      # BH significance threshold


def _mean_diff(x, y, axis=-1):
    """Two-sided mean-difference statistic (vectorized along ``axis``).

    Args:
        x: First sample's scores (or a batch of them along ``axis``).
        y: Second sample's scores (same shape along ``axis``).
        axis: The observation axis (``-1`` under ``vectorized=True``).

    Returns:
        ``mean(x) - mean(y)`` along ``axis``.
    """
    return np.mean(x, axis=axis) - np.mean(y, axis=axis)


def pair_p_value(a_scores, b_scores, *, n_resamples=N_RESAMPLES, seed=SEED,
                 batch=BATCH):
    """One pairwise permutation test: two-sided mean difference over the pair's
    common-task zscore vectors under ``permutation_type="samples"`` — scipy's
    paired permutation test (observations paired by task; the null flips the
    sign of each per-task difference; D-17/OQ5's aggregate-view axis).

    Args:
        a_scores: Model A's per-task zscores (common-task aligned).
        b_scores: Model B's per-task zscores (same tasks, same order).
        n_resamples: Shuffle count.
        seed: RNG seed (deterministic p-values).
        batch: Vectorized batch size.

    Returns:
        float: The two-sided permutation p-value.
    """
    result = stats.permutation_test(
        (np.asarray(a_scores, dtype=float), np.asarray(b_scores, dtype=float)),
        _mean_diff,
        permutation_type="samples",
        n_resamples=n_resamples,
        vectorized=True,
        batch=batch,
        alternative="two-sided",
        axis=-1,  # observations on the last axis (vectorized batches prepend a batch dim)
        rng=seed,
    )
    return float(result.pvalue)


def build_artifact(zscore_matrix, *, n_resamples=N_RESAMPLES, seed=SEED,
                   batch=BATCH):
    """Run the full pairwise family over a per-model per-task zscore matrix.

    Args:
        zscore_matrix: ``{model_alias: {task_name: zscore}}`` (tasks a model
            did not run are simply absent — no imputation).
        n_resamples: Shuffle count per pair.
        seed: RNG seed per pair.
        batch: Vectorized batch size.

    Returns:
        The artifact dict ``{"info": …, "pairs": […]}`` — info disclosing the
        family size, coverage rule, resample/seed/FDR methodology and the
        excluded zero-common-task pairs; one row per tested pair carrying
        ``model_a``/``model_b``/``n_common_tasks``/``p_value``/``p_adj``/
        ``significant``.
    """
    models = sorted(zscore_matrix)
    pairs = []
    excluded = []
    for i, model_a in enumerate(models):
        for model_b in models[i + 1:]:
            common = sorted(set(zscore_matrix[model_a]) & set(zscore_matrix[model_b]))
            if not common:
                excluded.append(
                    {"model_a": model_a, "model_b": model_b,
                     "reason": "zero common tasks"}
                )
                continue
            if len(common) < 2:
                # scipy's permutation_test requires >= 2 observations per
                # sample: a single shared task fixes the statistic (nothing
                # to permute), so the pair is excluded and disclosed rather
                # than crashed on.
                excluded.append(
                    {"model_a": model_a, "model_b": model_b,
                     "reason": "single common task"}
                )
                continue
            p_value = pair_p_value(
                [zscore_matrix[model_a][t] for t in common],
                [zscore_matrix[model_b][t] for t in common],
                n_resamples=n_resamples, seed=seed, batch=batch,
            )
            pairs.append({
                "model_a": model_a,
                "model_b": model_b,
                "n_common_tasks": len(common),
                "p_value": p_value,
            })

    adjusted = (
        stats.false_discovery_control([p["p_value"] for p in pairs], method="bh")
        if pairs else []
    )
    for entry, p_adj in zip(pairs, adjusted):
        entry["p_adj"] = float(p_adj)
        entry["significant"] = bool(entry["p_adj"] <= FDR_LEVEL)

    return {
        "info": {
            "axis": (
                "per-task zscore, aggregate view; paired permutation test "
                "(scipy permutation_type='samples') — per-task difference "
                "signs flipped under the null"
            ),
            "coverage_rule": (
                "pairs aligned on their common task set; pairs with fewer than "
                "two common tasks are excluded and disclosed (a single shared "
                "task fixes the statistic)"
            ),
            "family_size": len(pairs),
            "n_models": len(models),
            "n_resamples": n_resamples,
            "seed": seed,
            "batch": batch,
            "fdr_method": "bh",
            "fdr_level": FDR_LEVEL,
            "excluded_pairs": excluded,
        },
        "pairs": pairs,
    }


def load_zscore_matrix(input_dir):
    """Per-model per-task zscores over the all-arena aggregate view.

    Reuses summarize_comparison's own extraction and per-task normalization —
    the exact scores whose sums produce ``models_comparison.json``'s
    ``sum_zscore`` — so the permutation family and the leaderboard are
    provably the same view (one reader, one normalization; never a
    re-implementation).

    Args:
        input_dir: Directory containing ``{alias}_performance.json`` files.

    Returns:
        ``{model_alias: {task_name: zscore}}``.
    """
    _, raw_dataset_scores, _, _ = load_model_inputs(input_dir)
    matrix: dict[str, dict[str, float]] = {}
    for ds_name, scores in raw_dataset_scores.items():
        for model, stat in calculate_dataset_stats(scores).items():
            matrix.setdefault(model, {})[ds_name] = float(stat["zscore"])
    return matrix


def write_artifact(doc: dict[str, Any], path: Path) -> None:
    """Deterministic JSON write: sort_keys, indent 4, no live clock (the
    chain's byte convention — byte-stability across regenerations)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=4, ensure_ascii=False, sort_keys=True)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI: repo-root-runnable with REPO_ROOT-relative defaults (mirrors
    ``script/export_runs.py`` — the documented CWD-convention break)."""
    parser = argparse.ArgumentParser(
        prog="permutation_tests",
        description=(
            "Pairwise permutation tests over the aggregate leaderboard view "
            "(F6 Q3, REV-04): 10k shuffles, BH-corrected, seeded, deterministic."
        ),
    )
    parser.add_argument("--input-dir", type=Path,
                        default=REPO_ROOT / "dnallm-mark" / "data" / "model_performance",
                        help="per-model result directory (default: %(default)s)")
    parser.add_argument("--output", type=Path,
                        default=REPO_ROOT / "dnallm-mark" / "data" / "permutation_tests.json",
                        help="artifact destination (default: %(default)s)")
    args = parser.parse_args(argv)

    matrix = load_zscore_matrix(args.input_dir)
    if not matrix:
        print(f"Error: no scored models found under '{args.input_dir}'")
        return 1

    doc = build_artifact(matrix)
    write_artifact(doc, args.output)
    n_sig = sum(1 for p in doc["pairs"] if p["significant"])
    print(
        f"✅ Permutation tests: {doc['info']['family_size']} pair(s) "
        f"({len(doc['info']['excluded_pairs'])} excluded) saved to: {args.output} "
        f"({n_sig} significant at BH FDR {FDR_LEVEL})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
