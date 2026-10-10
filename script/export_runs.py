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
(the reviewer view) — and, per D-16 Option C (05-04), the per-model view:
one ``{model}_performance.json`` per model with at least one completed
record, validating against ``schemas/model_performance.json`` (UNCHANGED
schema). One emitter, both views, one reader per view downstream
(``summarize_comparison`` keeps its model_performance reader untouched).

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
            byte-identical outputs. BOTH views come from the same single
            pass over the joined per-cell payloads (D-16): the task view
            (``{safe_task}_task_performance.json`` keyed task->model) and
            the per-model view (``{model}_performance.json`` keyed
            model->task, shaped per ``schemas/model_performance.json`` —
            the contract the submit flow and the finetuning page consume).
            The per-model view's destination defaults to a SIBLING of the
            input root (``{input_root}/model_performance``) — never
            ``dnallm-mark/data/model_performance`` — so committed data is
            never silently overwritten before the maintainer migration
            gate (the D-18 discipline: data moves only in inventoried,
            changelogged commits).

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
        --stats-dir dnallm-mark/data/seed_stats \
        --model-output-dir finetuned/model_performance

See also:
    - ``script/summarize_comparison.py`` — downstream aggregation; 04-05
      deletes its METRIC_KEY_MAP mirror in favor of this table (IN-03).
    - ``script/freeze_snapshot.py`` — the tar + SHA256 snapshot primitive.
    - ``pipeline/run_sweep.py`` — the run_record.json producer.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import yaml
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


# =====================================================================
# Exporter-owned metric-key mapping (IN-03 single owner)
# =====================================================================

REPO_ROOT = Path(__file__).resolve().parents[1]

# Suite canonical metric names @483a35c — the vendored parity surface.
# Source: dnallm/tasks/metric_registry.py _RAW_REGISTRY keys, read-only at
# suite revision 483a35c (the live registry cannot be imported CPU-side:
# dnallm/__init__ pulls torch — CONTEXT exporter-Q1). The alias table below
# mirrors the registry's alias column exactly; recognition is strictly
# one-directional — aliases are NEVER emitted.
SUITE_CANONICAL = frozenset({
    "accuracy", "precision", "recall", "f1", "f1_micro", "f1_weighted",
    "f1_samples", "precision_micro", "precision_weighted", "precision_samples",
    "recall_micro", "recall_weighted", "recall_samples", "mcc",
    "matthews_correlation", "AUROC", "AUPRC", "AUROC_ovr", "AUROC_ovo",
    "TPR", "TNR", "FPR", "FNR", "mse", "mae", "r2", "pearsonr", "spearmanr",
})

_SUITE_ALIASES: dict[str, tuple[str, ...]] = {
    "accuracy": ("eval_accuracy",),
    "precision": ("eval_precision",),
    "recall": ("eval_recall",),
    "f1": ("eval_f1",),
    "f1_micro": ("eval_f1_micro",),
    "f1_weighted": ("eval_f1_weighted",),
    "f1_samples": ("eval_f1_samples",),
    "precision_micro": ("eval_precision_micro",),
    "precision_weighted": ("eval_precision_weighted",),
    "precision_samples": ("eval_precision_samples",),
    "recall_micro": ("eval_recall_micro",),
    "recall_weighted": ("eval_recall_weighted",),
    "recall_samples": ("eval_recall_samples",),
    "mcc": ("eval_mcc",),
    "matthews_correlation": ("eval_matthews_correlation",),
    "AUROC": ("eval_AUROC", "eval_auroc"),
    "AUPRC": ("eval_AUPRC", "eval_auprc"),
    "AUROC_ovr": ("eval_AUROC_ovr",),
    "AUROC_ovo": ("eval_AUROC_ovo",),
    "TPR": ("eval_TPR",),
    "TNR": ("eval_TNR",),
    "FPR": ("eval_FPR",),
    "FNR": ("eval_FNR",),
    "mse": ("eval_mse",),
    "mae": ("eval_mae",),
    "r2": ("eval_r2",),
    "pearsonr": ("eval_pearsonr", "eval_pearson_r"),
    "spearmanr": ("eval_spearmanr", "eval_spearman_r"),
}
_ALIAS_TO_CANONICAL: dict[str, str] = {
    alias: canonical
    for canonical, aliases in _SUITE_ALIASES.items()
    for alias in aliases
}

# Canonical -> export metricBlock slot. The legacy producer's hardcoded
# semantics (pipeline/dnallmmark_pipeline.py:1273-1285), formalized as the
# single mapping table.
CANONICAL_TO_EXPORT: dict[str, str] = {
    "accuracy": "accuracy",
    "precision": "precision",
    "recall": "recall",
    "f1": "f1",
    "mcc": "mcc",
    "AUROC": "auroc",
    "AUPRC": "auprc",
    "mse": "mse",
    "r2": "r2",
    "pearsonr": "pearson_r",
    "spearmanr": "spearman_r",
}

# The deliberate non-mappings (A6): suite canonicals with no slot in the
# 14-key metricBlock contract. They emit the empty string (the contract's
# missing-value convention) and are disclosed under their canonical names
# in the per-seed statistics artifact. Extending the closed enum instead is
# the SC-6 same-commit path (schema + data + self-check together), NOT
# taken this phase.
UNMAPPED = frozenset(SUITE_CANONICAL - set(CANONICAL_TO_EXPORT))

# Pipeline-produced (non-registry) keys with export slots: the HF Trainer
# output keys the sweep records verbatim, plus the FLOPs instrumentation
# source (a bare number in the schema — its absence is a hard error).
PIPELINE_KEYS: dict[str, str] = {
    "eval_loss": "loss",
    "train_runtime": "runtime",
    "total_flos": "FLOPs",
}

# The 14-key metricBlock surface — equals schemas/task_performance.json's
# metricBlock required set (pinned by tests/test_export_runs.py).
EXPORT_METRIC_KEYS = frozenset(CANONICAL_TO_EXPORT.values()) | frozenset(PIPELINE_KEYS.values())

# Multiple-Category rows classify into their majority-species arena before
# emission (maintainer-confirmed 2026-10-10 — 04-CATEGORY-REVIEW.md; the
# raw "Multiple" value must never reach output: the schema enum rejects
# it). The consumer-side twin is summarize_comparison.MAJORITY_ARENA
# (04-01); the two constants are pinned equal by test.
MAJORITY_ARENA = {"Multiple": "Animals"}

# The 11 model-card keys every unified registry entry carries
# (== tests/test_registry_unification.py CARD_KEYS; 62/62 complete since
# the 04-04 fills). A missing key aborts — never a partial card.
CARD_KEYS = frozenset({
    "architecture", "context_len (bp)", "huggingface", "mean_token_len",
    "modelscope", "name", "series", "size (M)", "species", "tokenizer",
    "type",
})

_SEED_DIR_PATTERN = re.compile(r"^seed_(\d+)$")


def resolve_metric_key(key: str) -> str | None:
    """Map one run-record metric key to its export metricBlock slot.

    Pipeline-produced keys win first (``eval_loss``/``train_runtime``/
    ``total_flos`` are not registry metrics). Registry resolution then
    mirrors the suite rules exactly: a canonical name resolves to itself, a
    registered alias resolves one-directionally to its canonical. A mapped
    canonical yields its export slot; an unmapped canonical yields ``""``
    (the deliberate empty-string marker, A6); a key that is neither —
    Trainer bookkeeping such as ``train_loss``, ``epoch``, ``eval_runtime``
    or ``*_per_second`` — yields ``None`` (not a leaderboard metric,
    skipped by the documented contract). This function never returns an
    alias spelling.

    Args:
        key: A metric key from a run record's ``metrics`` block.

    Returns:
        The export slot, ``""`` for a deliberately unmapped canonical, or
        ``None`` for a non-metric key.
    """
    if key in PIPELINE_KEYS:
        return PIPELINE_KEYS[key]
    if key in SUITE_CANONICAL:
        return CANONICAL_TO_EXPORT.get(key, "")
    if key in _ALIAS_TO_CANONICAL:
        return CANONICAL_TO_EXPORT.get(_ALIAS_TO_CANONICAL[key], "")
    return None


def _canonical_of(key: str) -> str:
    """The canonical name for a known canonical-or-alias key."""
    return key if key in SUITE_CANONICAL else _ALIAS_TO_CANONICAL[key]


# Legacy dataset-metric strings (04-05, IN-03 by removal): committed dataset
# blocks declare their primary metric in mixed producer spellings — the
# uppercase forms below lived in summarize_comparison's deleted local
# metric_key_map mirror and are now this table's custody too (one owner,
# both key surfaces). They resolve to suite canonicals first, then to
# export slots. AUROC/AUPRC need no entry (already suite canonicals), and
# pearsonr/spearmanr are canonicals as-is.
LEGACY_DATASET_METRIC: dict[str, str] = {
    "F1": "f1",
    "MCC": "mcc",
    "MSE": "mse",
    "MAE": "mae",
    "R2": "r2",
}


def resolve_dataset_metric(metric: str) -> str:
    """Translate a dataset block's ``metric`` declaration to its export slot.

    The single authority over BOTH key surfaces (IN-03): legacy/uppercase
    producer spellings resolve through ``LEGACY_DATASET_METRIC`` to suite
    canonicals, and suite canonicals map through ``CANONICAL_TO_EXPORT`` to
    the performance-block slots. A declaration that resolves to neither
    surface passes through unchanged — the identity fallback the deleted
    mirror had, so an unlisted metric key simply misses in the performance
    block exactly as before (numbers never move; T-04-13).

    Args:
        metric: The ``dataset.metric`` value from a committed result file
            (e.g. ``"F1"``, ``"AUPRC"``, ``"spearmanr"``).

    Returns:
        The performance-block slot the value lives under (e.g. ``"f1"``,
        ``"auprc"``, ``"spearman_r"``).
    """
    canonical = LEGACY_DATASET_METRIC.get(metric, metric)
    return CANONICAL_TO_EXPORT.get(canonical, canonical)


# =====================================================================
# Run-record reader (F2 layout)
# =====================================================================

def load_run_records(root: Path) -> dict[str, dict[str, dict[int, dict[str, Any]]]]:
    """Read the F2 run-record tree: ``{model: {task: {seed: record}}}``.

    Walks ``{root}/{model}/{task}/seed_{n}/run_record.json`` — models and
    tasks in sorted order, seed directories sorted numerically. A seed
    directory without a run_record.json is skipped (a partially-written
    cell); a malformed record aborts loudly (offline tool over the sweep's
    own output).

    Args:
        root: The sweep output root (default ``finetuned/``).

    Returns:
        The nested record tree, records verbatim.
    """
    if not root.is_dir():
        raise FileNotFoundError(f"input root does not exist: {root}")
    tree: dict[str, dict[str, dict[int, dict[str, Any]]]] = {}
    for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for task_dir in sorted(p for p in model_dir.iterdir() if p.is_dir()):
            seed_dirs: list[tuple[int, Path]] = []
            for path in task_dir.iterdir():
                match = _SEED_DIR_PATTERN.match(path.name)
                if match and path.is_dir():
                    seed_dirs.append((int(match.group(1)), path))
            for seed, seed_dir in sorted(seed_dirs):
                record_path = seed_dir / "run_record.json"
                if not record_path.exists():
                    continue
                record = json.loads(record_path.read_text(encoding="utf-8"))
                tree.setdefault(model_dir.name, {}).setdefault(task_dir.name, {})[seed] = record
    return tree


def _finite(value: Any) -> float | None:
    """Coerce to a finite float, or ``None`` (WR-03: non-finite = missing)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _record_path(root: Path, model: str, task: str, seed: int) -> Path:
    return root / model / task / f"seed_{seed}" / "run_record.json"


def _collect_cell_values(
    records: Mapping[int, Mapping[str, Any]], root: Path, model: str, task: str
) -> dict[str, dict[int, float]]:
    """Per-metric seed values over a cell's COMPLETED records, finite only.

    Keys are export slots for mapped canonicals and pipeline-produced keys;
    deliberately unmapped canonicals are kept under their canonical names
    so the statistics artifact discloses them (no silent drops). Records
    with status failed/skipped contribute nothing. A completed record
    missing ``total_flos`` is a hard error naming the record path (the
    schema requires a bare number — 0 or ``""`` would falsify or
    invalidate; T-04-04).

    Args:
        records: ``{seed: record}`` for one model/task cell.
        root: The input root (for actionable error paths).
        model: Model name (path component).
        task: Task name (path component).

    Returns:
        ``{stats key: {seed: finite value}}``.
    """
    per_metric: dict[str, dict[int, float]] = {}
    for seed in sorted(records):
        record = records[seed]
        if record.get("status") != "completed":
            continue
        metrics = record.get("metrics") or {}
        if "total_flos" not in metrics:
            raise RuntimeError(
                f"completed run record is missing the pipeline-produced FLOPs "
                f"source 'total_flos' (schemas/task_performance.json requires "
                f"a bare number — emitting 0 or '' would falsify or "
                f"invalidate): {_record_path(root, model, task, seed)}"
            )
        for key, raw in metrics.items():
            slot = resolve_metric_key(key)
            if slot is None:
                continue  # Trainer bookkeeping — documented skip contract
            value = _finite(raw)
            if value is None:
                continue
            stats_key = slot if slot else _canonical_of(key)
            per_metric.setdefault(stats_key, {})[seed] = value
    if "FLOPs" not in per_metric:
        completed = [s for s in sorted(records) if records[s].get("status") == "completed"]
        raise RuntimeError(
            f"no finite 'total_flos' across the completed seeds of {model}/{task} "
            f"(seeds {completed}) — FLOPs is a required bare number, refusing "
            f"to emit a fabricated value"
        )
    return per_metric


# =====================================================================
# D-12 parametersBlock join (config YAML + actually-effective overrides)
# =====================================================================

def load_parameters_block(
    record: Mapping[str, Any], seed_dir: Path, finetune_cfg: Mapping[str, Any], config_path: Path
) -> dict[str, Any]:
    """The 9-key parametersBlock per D-12 — the config-YAML join, NOT a
    run_record contract extension.

    ``batch_size``/``gradient_accumulation_steps`` come from the record's
    ``vram_probe`` when non-null (the actually-effective overrides), else
    from the YAML base (``per_device_train_batch_size`` /
    ``gradient_accumulation_steps``). ``epochs``/``learning_rate``/
    ``lr_scheduler_type``/``warmup`` (from ``warmup_ratio``)/``bf16``/
    ``fp16`` come from the YAML. ``steps`` comes from the seed dir's
    ``trainer_state.json`` ``global_step`` (present in every completed cell
    by the WR-13 write ordering), falling back to the YAML ``max_steps``
    ONLY when it is positive — otherwise an actionable hard error.

    Provenance: ``record``/``seed_dir`` are the FIRST completed seed of the
    cell in sorted order (per-cell training params are config-derived and
    seed-invariant).

    Args:
        record: The anchor (first completed) run record.
        seed_dir: That seed's directory (holds trainer_state.json).
        finetune_cfg: The config YAML's ``finetune`` block.
        config_path: Config path (for the actionable error message).

    Returns:
        The parametersBlock dict (schema: 9 required keys).
    """
    vram = record.get("vram_probe") or {}
    probe_batch = vram.get("batch_size")
    probe_accum = vram.get("gradient_accumulation_steps")
    state_path = seed_dir / "trainer_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        steps = int(state["global_step"])
    else:
        max_steps = int(finetune_cfg.get("max_steps", -1))
        if max_steps > 0:
            steps = max_steps
        else:
            raise RuntimeError(
                f"cannot source 'steps' for the parameters block: no "
                f"trainer_state.json in {seed_dir} and the config max_steps "
                f"is not positive ({max_steps}, {config_path}) — refusing to "
                f"emit a fabricated step count"
            )
    return {
        "batch_size": (
            int(probe_batch)
            if probe_batch is not None
            else int(finetune_cfg["per_device_train_batch_size"])
        ),
        "bf16": bool(finetune_cfg["bf16"]),
        "epochs": int(finetune_cfg["num_train_epochs"]),
        "fp16": bool(finetune_cfg["fp16"]),
        "gradient_accumulation_steps": (
            int(probe_accum)
            if probe_accum is not None
            else int(finetune_cfg["gradient_accumulation_steps"])
        ),
        "learning_rate": float(finetune_cfg["learning_rate"]),
        "lr_scheduler_type": str(finetune_cfg["lr_scheduler_type"]),
        "steps": steps,
        "warmup": float(finetune_cfg["warmup_ratio"]),
    }


# =====================================================================
# Registry joins + emitter
# =====================================================================

def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _load_finetune_config(path: Path) -> dict[str, Any]:
    """The ``finetune`` block of the config YAML (the D-12 join source).

    PyYAML is not a direct dependency of this repo: it arrives transitively
    via evaluate -> huggingface-hub (D-15). A missing block aborts loudly.
    """
    with path.open("r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh) or {}
    cfg = doc.get("finetune") if isinstance(doc, dict) else None
    if cfg is None:
        raise RuntimeError(f"config YAML has no 'finetune' block: {path}")
    if not isinstance(cfg, dict):
        raise TypeError(f"config 'finetune' block is not a mapping: {path}")
    return cfg


def _model_card(row: Mapping[str, Any]) -> dict[str, Any]:
    """The 11-key card join — a missing key aborts (never a partial card)."""
    return {key: row[key] for key in sorted(CARD_KEYS)}


def _dataset_info_block(row: Mapping[str, Any]) -> dict[str, Any]:
    """The 8-key datasetBlock; Category -> species with Multiple resolved to
    the majority arena BEFORE emission (the raw value never reaches output)."""
    return {
        "dev": row["Dev"],
        "labels": row["labels"],
        "length": row["length"],
        "metric": row["metric"],  # verbatim — casing NOT normalized (Pitfall 7)
        "species": MAJORITY_ARENA.get(row["Category"], row["Category"]),
        "test": row["Test"],
        "train": row["Train"],
        "type": row["type"],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Deterministic JSON write: sort_keys, indent 4, no trailing newline
    (the pivot script's byte convention — byte-stability is a truth)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=4, ensure_ascii=False, sort_keys=True)


def export_runs_tree(
    input_root: Path,
    models_info_path: Path,
    datasets_info_path: Path,
    config_path: Path,
    output_dir: Path,
    stats_dir: Path,
    model_output_dir: Path | None = None,
    *,
    n_bootstrap: int,
    bootstrap_seed: int,
    small_n_ci: str,
) -> list[str]:
    """Run the full export over an F2 run-record tree — BOTH views (D-16).

    For every task (sorted) with at least one completed record, emits
    ``{safe_task}_task_performance.json`` into ``output_dir`` (validating
    shape: schemas/task_performance.json) and ``{safe_task}_seed_stats.json``
    into ``stats_dir`` (the per-seed detail + vendored-statistics reviewer
    view). In the SAME single pass over the joined per-cell payloads, also
    accumulates the per-model view and, for every model (sorted) with at
    least one completed record, emits ``{model}_performance.json`` into
    ``model_output_dir`` — ``info`` = the full 11-key registry card join,
    ``performance`` = per completed task ``{dataset, parameters,
    performance}`` blocks IDENTICAL to the task view's (one computation,
    two keyings — the two views agree on every shared cell by
    construction). A model with zero completed records emits NO file (the
    WR-02 discipline applied to the model axis). Registry joins are
    hard-fail dict lookups; iteration is sorted and serialization is
    sort_keys — the whole export is byte-stable in both views.

    Args:
        input_root: Sweep output root (``{model}/{task}/seed_{n}/``).
        models_info_path: Unified models registry (modelCard join).
        datasets_info_path: Unified datasets registry (datasetBlock join).
        config_path: finetune config YAML (D-12 parametersBlock join).
        output_dir: Task-file destination.
        stats_dir: Statistics-artifact destination.
        model_output_dir: Per-model view destination. ``None`` derives
            ``input_root / "model_performance"`` — a sibling of the input
            root, NEVER ``dnallm-mark/data/model_performance`` (committed
            data moves only through inventoried migration commits).
        n_bootstrap: Bootstrap resample count (n >= 10 seeds only).
        bootstrap_seed: Bootstrap RNG seed (deterministic intervals).
        small_n_ci: ``"t-interval"`` or ``"omit"`` for 3 <= n < 10.

    Returns:
        The sorted list of exported task names.
    """
    models_info = _load_json(models_info_path)
    datasets_info = _load_json(datasets_info_path)
    finetune_cfg = _load_finetune_config(config_path)
    tree = load_run_records(input_root)
    if model_output_dir is None:
        model_output_dir = input_root / "model_performance"

    tasks = sorted({task for per_model in tree.values() for task in per_model})
    emitted: list[str] = []
    # D-16 per-model view accumulators: the SAME joined blocks the task view
    # emits, keyed model->task (one pass, two keyings). A model enters these
    # maps only through a completed cell, so zero-completed models emit no
    # file without a special case.
    model_cards: dict[str, dict[str, Any]] = {}
    model_view: dict[str, dict[str, dict[str, Any]]] = {}
    for task in tasks:
        dataset_row = datasets_info[task]  # KeyError: unregistered dataset — hard fail
        performance: dict[str, dict[str, Any]] = {}
        stats_doc: dict[str, dict[str, Any]] = {}
        for model in sorted(tree):
            records = tree[model].get(task)
            if not records:
                continue
            completed = {
                seed: record
                for seed, record in sorted(records.items())
                if record.get("status") == "completed"
            }
            if not completed:
                continue  # a cell with no completed seeds contributes nothing
            model_row = models_info[model]  # KeyError: unregistered model — hard fail
            per_metric = _collect_cell_values(records, input_root, model, task)
            anchor_seed = min(completed)
            parameters = load_parameters_block(
                completed[anchor_seed],
                input_root / model / task / f"seed_{anchor_seed}",
                finetune_cfg,
                config_path,
            )
            metric_block: dict[str, Any] = {}
            for key in sorted(EXPORT_METRIC_KEYS):
                values = per_metric.get(key)
                if values:
                    ordered = [values[seed] for seed in sorted(values)]
                    metric_block[key] = float(np.mean(ordered))
                elif key == "FLOPs":
                    raise RuntimeError(  # pragma: no cover — guarded in _collect_cell_values
                        f"FLOPs missing for {model}/{task}"
                    )
                else:
                    metric_block[key] = ""
            performance[model] = {
                "model": _model_card(model_row),
                "parameters": parameters,
                "performance": metric_block,
            }
            model_cards[model] = performance[model]["model"]
            model_view.setdefault(model, {})[task] = {
                "dataset": _dataset_info_block(dataset_row),
                "parameters": parameters,
                "performance": metric_block,
            }
            stats_doc[model] = {
                key: {
                    "per_seed": {
                        str(seed): per_metric[key][seed]
                        for seed in sorted(per_metric[key])
                    },
                    "stats": aggregate_seeds(
                        [per_metric[key][seed] for seed in sorted(per_metric[key])],
                        n_bootstrap=n_bootstrap,
                        bootstrap_seed=bootstrap_seed,
                        small_n_ci=small_n_ci,
                    ),
                }
                for key in sorted(per_metric)
            }
        safe_task = task.replace("/", "_").replace("\\", "_")
        if not performance:
            # WR-02: zero completed records anywhere -> no file, no stats
            # artifact, no ``emitted`` entry (the docstring's "at least one
            # completed record" contract). An empty performance map would
            # still validate against the schema (no ``minProperties``) and
            # surface as a permanently empty leaderboard entry in tasks.json.
            continue
        _write_json(output_dir / f"{safe_task}_task_performance.json", {
            "info": _dataset_info_block(dataset_row),
            "performance": performance,
        })
        _write_json(stats_dir / f"{safe_task}_seed_stats.json", stats_doc)
        emitted.append(task)
    # D-16 per-model emission: one {model}_performance.json per model with at
    # least one completed record. The filename alias is EXACTLY the registry
    # key (the key==name contract, D-10/D-18) — the same alias the task view
    # keys its performance map by, so the leaderboard, the submit flow, and
    # the finetuning page see one identity per model.
    for model in sorted(model_view):
        _write_json(model_output_dir / f"{model}_performance.json", {
            "info": model_cards[model],
            "performance": model_view[model],
        })
    return emitted


def main(argv: Sequence[str] | None = None) -> int:
    """CLI: repo-root-runnable with explicit REPO_ROOT-relative defaults
    (the documented, deliberate CWD-convention break — Pitfall 3)."""
    parser = argparse.ArgumentParser(
        prog="export_runs",
        description=(
            "Unified exporter: F2 run records -> task_performance-compatible "
            "JSON + per-seed statistics artifacts (SC-2/REV-03)."
        ),
    )
    parser.add_argument("--input-root", type=Path, default=REPO_ROOT / "finetuned",
                        help="sweep output root (default: %(default)s)")
    parser.add_argument("--models-info", type=Path,
                        default=REPO_ROOT / "pipeline" / "models_info.json",
                        help="unified models registry (default: %(default)s)")
    parser.add_argument("--datasets-info", type=Path,
                        default=REPO_ROOT / "pipeline" / "datasets_info.json",
                        help="unified datasets registry (default: %(default)s)")
    parser.add_argument("--config", type=Path,
                        default=REPO_ROOT / "pipeline" / "finetune_config.yaml",
                        help="finetune config YAML, the D-12 join source (default: %(default)s)")
    parser.add_argument("--output-dir", type=Path,
                        default=REPO_ROOT / "dnallm-mark" / "data" / "task_performance",
                        help="task-file destination (default: %(default)s)")
    parser.add_argument("--stats-dir", type=Path,
                        default=REPO_ROOT / "dnallm-mark" / "data" / "seed_stats",
                        help="per-seed statistics destination (default: %(default)s)")
    parser.add_argument("--model-output-dir", type=Path, default=None,
                        help="per-model view destination (D-16; default: derived as "
                             "{input-root}/model_performance — a sibling of the sweep "
                             "output, NEVER dnallm-mark/data/model_performance, so "
                             "committed data moves only through inventoried "
                             "migration commits)")
    parser.add_argument("--n-bootstrap", type=int, default=2000,
                        help="bootstrap resamples, n>=10 seeds only (default: %(default)s)")
    parser.add_argument("--bootstrap-seed", type=int, default=42,
                        help="bootstrap RNG seed (default: %(default)s)")
    parser.add_argument("--small-n-ci", choices=list(SMALL_N_CI_CHOICES),
                        default="t-interval",
                        help="small-n (3<=n<10) interval policy (default: %(default)s)")
    args = parser.parse_args(argv)
    model_output_dir = (
        args.model_output_dir
        if args.model_output_dir is not None
        else args.input_root / "model_performance"
    )
    emitted = export_runs_tree(
        args.input_root, args.models_info, args.datasets_info, args.config,
        args.output_dir, args.stats_dir, model_output_dir,
        n_bootstrap=args.n_bootstrap,
        bootstrap_seed=args.bootstrap_seed,
        small_n_ci=args.small_n_ci,
    )
    model_files = sorted(model_output_dir.glob("*_performance.json"))
    print(f"Exported {len(emitted)} task(s) to {args.output_dir} "
          f"(statistics artifacts in {args.stats_dir})")
    print(f"Exported {len(model_files)} per-model file(s) to {model_output_dir}")
    for name in emitted:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
