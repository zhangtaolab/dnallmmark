"""Unified exporter: F2 run records -> task_performance-compatible JSON (SC-2/REV-03).

Purpose
-------
Replace the deprecated per-model master-JSON assembly with a pure function
of run records + registries: read ``{root}/{model}/{task}/seed_{seed}/run_record.json``
cells (metrics = the cell's ``final_metrics.json`` keys VERBATIM, suite-native),
apply the exporter-owned metric-key mapping, join the unified registries,
aggregate over seeds with the suite's own statistics, and emit per-task files
that validate against ``schemas/task_performance.json`` (UNCHANGED schema,
CONTEXT exporter-Q2) plus a per-seed detail/statistics artifact per task
(the reviewer view).

Direction of truth
------------------
Run records (produced by the F2 sweep, ``pipeline/run_sweep.py``) +
``pipeline/models_info.json`` + ``pipeline/datasets_info.json`` (D-10
unified registries; the maintainer-confirmed Category column — see
04-CATEGORY-REVIEW.md — is the arena authority) +
``pipeline/finetune_config.yaml`` (the D-12 parametersBlock join source).
Every join is a hard-fail dict lookup: an unregistered model/dataset
aborts (KeyError, never a fallback join), and a completed record missing
its FLOPs source (``total_flos``) is an actionable hard error — emitting 0
or the empty string would falsify or invalidate the schema-required bare
number (T-04-04). ``schemas/task_performance.json`` is the output contract
and is NOT edited by this plan.

Behavior
--------
map -> join -> aggregate -> emit:

1. map      metric keys through the single mapping table
            (``SUITE_CANONICAL`` / ``CANONICAL_TO_EXPORT`` / ``PIPELINE_KEYS``
            / ``UNMAPPED`` — the IN-03 single owner; key-parity tested in
            both directions in ``tests/test_export_runs.py``);
2. join     the 8-key datasetBlock (Category -> species with Multiple
            resolved to the majority arena BEFORE emission, so the raw
            "Multiple" value can never reach output) and the 11-key
            modelCard per model;
3. aggregate the per-metric mean over finite-valued completed seeds
            (leaderboard view) plus the vendored ``aggregate_seeds``
            statistics block per metric (reviewer view, n_seeds disclosed
            per metric — never vacuous, D-14/SEED-01);
4. emit     with sorted iteration, ``sort_keys=True`` and no live clock —
            byte-stable: exporting the same tree twice produces
            byte-identical outputs.

Trainer-emitted bookkeeping keys that are neither pipeline-produced
(``eval_loss``/``train_runtime``/``total_flos``) nor resolvable through the
suite metric-registry rules (e.g. ``train_loss``, ``epoch``, ``eval_runtime``,
``*_per_second``) are not leaderboard metrics and are skipped by contract;
suite canonicals are never silently dropped (every one of the 28 is either
mapped or in the explicit ``UNMAPPED`` set).

Provenance
----------
The statistics function ``aggregate_seeds`` and its module constants are a
VERBATIM vendored copy from the DNALLM suite at revision 483a35c (see the
banner below). No ``dnallm`` import exists anywhere in this repo: the suite
package ``__init__`` pulls torch, which would break the CPU-only torch-free
dev discipline (CONTEXT exporter-Q1). Revisit when the suite offers a
torch-free import path.

Dependency provenance (D-15, 2026-10-10): ``scipy>=1.15.2`` (this module's
t-interval) and ``evaluate`` (HuggingFace — the metrics-layer cross-validation
dependency exercised by ``tests/test_export_runs.py``) joined the ``[data]``
group in the SAME dependency commit. The suite's metric implementations stay
authoritative for reported numbers; evaluate is the verification layer.

Concurrency: single-writer assumption — this is an offline maintainer tool;
two concurrent exports over the same output directory are out of contract
(flagged for the E2' gate rather than silently assumed safe).

Usage
-----
From the repo root (explicit REPO_ROOT-relative paths — the documented,
deliberate CWD-convention break; NOT run from ``dnallm-mark/data/``)::

    uv run --group data python script/export_runs.py \
        --input-root finetuned \
        --output-dir dnallm-mark/data/task_performance \
        --stats-dir dnallm-mark/data/seed_stats

See also:
    - ``script/summarize_comparison.py`` — downstream aggregation; 04-05
      deletes its METRIC_KEY_MAP mirror in favor of this table (IN-03).
    - ``script/freeze_snapshot.py`` — the tar + SHA256 snapshot primitive.
    - ``pipeline/run_sweep.py`` — the run_record.json producer.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy import stats

# =====================================================================
# Vendored suite statistics @483a35c — VERBATIM COPY, DO NOT EDIT
#
# Source: dnallm/finetune/sweep.py at suite revision 483a35c
# (git show 483a35c:dnallm/finetune/sweep.py, read-only checkout at
# /home/forrest/Github/DNALLM). Copied 2026-10-10. Behavioral edits are
# forbidden in this section: tests/test_vendored_stats.py pins this copy to
# the suite semantics (n-guards at 2/3/9/10, t-interval values recomputed
# from scipy.stats.t, bootstrap determinism, ValueError cases — threat
# T-04-03). Only the imports (np / stats / Sequence / Any) live in this
# module's header above; the constants and the function below are
# character-for-character identical to the source.
# =====================================================================

# Valid values for the small-n CI policy (mirrors SweepConfig.small_n_ci's
# pattern ^(t-interval|omit)$; validated here because aggregate_seeds is also
# callable directly, without going through the Pydantic boundary).
SMALL_N_CI_CHOICES = ("t-interval", "omit")

# Minimum seed count for ANY confidence interval (D-14): below this the
# statistics block reports method "none" and ci95 null.
CI_MIN_SEEDS = 3

# Minimum seed count for the percentile bootstrap: the resample space is too
# small to be meaningful below this (10 distinct resample multisets at n=3).
BOOTSTRAP_MIN_SEEDS = 10


def aggregate_seeds(
    values: Sequence[float],
    *,
    n_bootstrap: int,
    bootstrap_seed: int,
    small_n_ci: str,
) -> dict[str, Any]:
    """Aggregate per-seed metric values into the statistics block.

    Implements the n-guard (D-14): ``n < 3`` reports no interval
    (``method="none"``); ``3 <= n < 10`` reports a Student-t interval
    (``method="t"``) or omits it when ``small_n_ci="omit"``
    (``method="omitted"``); ``n >= 10`` reports a seeded percentile
    bootstrap (``method="bootstrap-percentile"``) regardless of
    ``small_n_ci`` (that policy only governs the small-n range).

    Args:
        values: Per-seed metric values (one per seed run).
        n_bootstrap: Number of bootstrap resamples (used only at
            ``n >= 10``).
        bootstrap_seed: Seed for the bootstrap RNG, so identical data and
            seed produce an identical interval (used only at ``n >= 10``).
        small_n_ci: Small-n interval policy, ``"t-interval"`` or
            ``"omit"`` (used only for ``3 <= n < 10``).

    Returns:
        The statistics block ``{"n_seeds", "mean", "sd", "ci95",
        "method"}`` per the module docstring spec.

    Raises:
        ValueError: If ``small_n_ci`` is not one of the valid policies, if
            ``values`` is empty, or if ``values`` is not a flat numeric
            sequence.
    """
    if small_n_ci not in SMALL_N_CI_CHOICES:
        raise ValueError(f"small_n_ci must be one of {SMALL_N_CI_CHOICES}, got {small_n_ci!r}.")
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError(
            f"aggregate_seeds expects a flat sequence of per-seed values, "
            f"got an array with shape {arr.shape}."
        )
    n = int(arr.size)
    if n < 1:
        raise ValueError("aggregate_seeds requires at least one per-seed value; got none.")
    out: dict[str, Any] = {
        "n_seeds": n,
        "mean": float(arr.mean()),
        "sd": float(arr.std(ddof=1)) if n > 1 else None,
    }
    if n < CI_MIN_SEEDS:
        # Never vacuous: no interval is emitted below three seeds.
        out["ci95"] = None
        out["method"] = "none"
    elif n < BOOTSTRAP_MIN_SEEDS and small_n_ci == "t-interval":
        sem = arr.std(ddof=1) / np.sqrt(n)
        tcrit = stats.t.ppf(0.975, n - 1)
        out["ci95"] = [
            float(arr.mean() - tcrit * sem),
            float(arr.mean() + tcrit * sem),
        ]
        out["method"] = "t"
    elif n >= BOOTSTRAP_MIN_SEEDS:
        rng = np.random.default_rng(bootstrap_seed)
        idx = rng.integers(0, n, size=(n_bootstrap, n))
        means = arr[idx].mean(axis=1)
        out["ci95"] = [
            float(np.percentile(means, 2.5)),
            float(np.percentile(means, 97.5)),
        ]
        out["method"] = "bootstrap-percentile"
    else:
        # 3 <= n < 10 with small_n_ci == "omit": point estimates only.
        out["ci95"] = None
        out["method"] = "omitted"
    return out

# ===== END vendored section @483a35c =====
