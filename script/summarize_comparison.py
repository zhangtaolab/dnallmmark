"""
Generate leaderboard comparison summaries from per-model benchmark results.

DNALLM-Mark evaluates dozens of DNA language models (DNABERT, Caduceus, HyenaDNA,
GPN, Enformer, GenomeOcean, etc.) across genomic prediction tasks such as promoter
prediction, histone modification classification, splice site detection, and gene
expression regression.

After ``get_task_performance.py`` pivots the raw data into task-centric files, this
script goes further: for every model it computes **aggregated ranking statistics**
across all benchmark tasks (or a species-specific subset), producing the JSON files
that power the DNALLM-Mark interactive leaderboard (``index.html``).

Normalization strategy
----------------------
On each individual task, every model receives four normalised scores:

1. **Rank Score** — ``N - rank`` where *N* is the number of models evaluated on
   that task.  Rank 1 scores ``N-1`` points; last place scores 0.
2. **MinMax** — ``(score - min) / (max - min)`` scaled to [0, 1].
3. **Z-Score** — ``(score - mean) / std`` standardised around 0.
4. **Robust** — ``(score - median) / IQR``, resistant to outliers.

These per-task scores are then **summed** across tasks for each model to produce
overall aggregate metrics (``rank_score``, ``sum_minmax``, ``sum_zscore``,
``sum_robust``).  Models that were not evaluated on a given task simply receive no
points for that task — there is no imputation.

Output files
------------
All outputs are written to ``dnallm-mark/data/``:

- ``models_comparison.json``           — all tasks, all models.
- ``models_comparison_animals.json``   — only tasks whose dataset species is "animal".
- ``models_comparison_plants.json``    — only tasks whose dataset species is "plant".
- ``models_comparison_microbe.json``   — only tasks whose dataset species is "microbe".

Each file contains a dict keyed by model alias, sorted by ``rank_score`` descending::

    {
        "plant-dnabert-6mer": {
            "model": { "name": "...", "size (M)": ..., "type": "...", ... },
            "performance": {
                "samples": 47,
                "rank_score": 120.0,
                "sum_minmax": 38.5,
                "sum_zscore": 12.3,
                "sum_robust": 8.1,
                "avg_raw": 0.82,
                "avg_rank": 3.2,
                "top1_count": 5,
                "top3_count": 12,
                "top5_count": 18,
                "top8_count": 25,
                "top10_count": 30,
                "sum_PFLOPs": 2.4,
                "avg_PFLOPs": 0.051,
                "rank": 1
            }
        },
        ...
    }

Usage (run from ``dnallm-mark/data/``)::

    cd dnallm-mark/data
    python ../../script/summarize_comparison.py

See also:
    - ``script/get_task_performance.py`` — produces the per-task JSON files used
      by the finetuning results page.
"""

import os
import json
import numpy as np
import pandas as pd


def get_float(val, default=0.0):
    """Safely coerce a metric value to ``float``.

    Many evaluation metrics may be missing (empty string or ``None``) when a
    model fails or the metric is not applicable to the task type (e.g. ``r2``
    for a classification task).  This helper returns ``default`` in those cases.

    Args:
        val:    Raw metric value — may be a number, ``""``, or ``None``.
        default: Fallback value when conversion fails (default ``0.0``).
    """
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def calculate_dataset_stats(dataset_records):
    """Compute normalised scores and rank-based points for one benchmark task.

    Given a flat mapping of ``{model_alias: raw_metric_score}`` for a single
    dataset, this function produces four normalised scores per model that are
    later summed across tasks by :func:`aggregate_models`.

    Normalisation methods:

    - **Rank** — competition-style ranking (``method='min'`` so tied scores
      share the same rank).  Rank score = ``N - rank``.
    - **MinMax** — rescales raw scores to [0, 1].
    - **Z-Score** — standardises using mean / std of the score distribution.
    - **Robust** — uses median / IQR, making it resistant to outlier scores.

    Args:
        dataset_records: ``{model_alias: raw_score}`` for one task/dataset.

    Returns:
        ``{model_alias: {raw, rank, task_rank_score, minmax, zscore, robust}}``
        or an empty dict if no scores are available.
    """
    models = list(dataset_records.keys())
    scores = np.array(list(dataset_records.values()))

    # Total number of models that were successfully evaluated on this task
    N = len(scores)

    if N == 0:
        return {}

    # 1. Rank (higher raw score → lower rank number, i.e. rank 1 is best).
    #    method='min' assigns the best (smallest) rank to all tied scores,
    #    e.g. scores [0.9, 0.9, 0.8] → ranks [1, 1, 3].
    ranks = pd.Series(scores).rank(ascending=False, method='min').values

    # Convert ranks to competitive points: rank 1 earns N-1, last earns 0.
    task_rank_scores = N - ranks

    # 2. MinMax normalisation → [0, 1].  All zeros when min == max.
    min_s, max_s = np.min(scores), np.max(scores)
    minmax = (scores - min_s) / (max_s - min_s) if max_s > min_s else np.zeros_like(scores)

    # 3. Z-Score standardisation.  All zeros when std == 0.
    mean_s, std_s = np.mean(scores), np.std(scores)
    zscore = (scores - mean_s) / std_s if std_s > 0 else np.zeros_like(scores)

    # 4. Robust normalisation using median and IQR.  All zeros when IQR == 0.
    q25, q50, q75 = np.percentile(scores, [25, 50, 75])
    iqr = q75 - q25
    robust = (scores - q50) / iqr if iqr > 0 else np.zeros_like(scores)

    stats = {}
    for i, m in enumerate(models):
        stats[m] = {
            'raw': scores[i],
            'rank': ranks[i],                        # true rank (used for Top-K counts)
            'task_rank_score': task_rank_scores[i],  # competitive points for this task
            'minmax': minmax[i],
            'zscore': zscore[i],
            'robust': robust[i],
        }
    return stats


def to_singular_species(name):
    """Normalise a species label to its singular form for filenames.

    Benchmark datasets are annotated with a species category (e.g. "Animal",
    "Plant", "Microbe").  Some upstream data uses the plural form ("plants"),
    so this helper ensures consistent filenames like
    ``models_comparison_plant.json``.

    Args:
        name: Species label — may be singular or plural (case-insensitive).

    Returns:
        Lowercased singular form (e.g. ``"plant"``).
    """
    name_lower = name.lower()
    plural_to_singular = {
        'animals': 'animal',
        'plants': 'plant',
        'microbes': 'microbe',
    }
    return plural_to_singular.get(name_lower, name_lower)


def aggregate_models(models_info, dataset_stats_map, dataset_flops_map, target_datasets):
    """Aggregate per-task normalised scores into overall model rankings.

    For each model, this function sums its normalised scores (rank score,
    MinMax, Z-Score, robust) across all datasets in *target_datasets*, counts
    how many tasks the model appeared in (``samples``), and records Top-K
    placement counts.  Models not evaluated on a given task simply receive no
    contribution for that task.

    After aggregation, models are assigned a final overall ``rank`` based on
    ``rank_score`` in descending order.

    Args:
        models_info:         ``{model_alias: {name, size (M), type, …}}``
        dataset_stats_map:   ``{dataset_name: {model_alias: {raw, rank, …}}}``
                             as returned by :func:`calculate_dataset_stats`.
        dataset_flops_map:   ``{dataset_name: {model_alias: FLOPs}}``
        target_datasets:     List of dataset names to include in this aggregation
                             (e.g. all datasets, or only plant-specific ones).

    Returns:
        ``{model_alias: {model: …, performance: …}}`` sorted by ``rank_score``
        descending, with ``rank`` assigned to each model.
    """
    aggregated_results = {}

    for model_alias, info in models_info.items():
        # Collect the model's per-task stats and FLOPs across target datasets
        model_m_stats = []
        model_flops = []

        for ds in target_datasets:
            if ds in dataset_stats_map and model_alias in dataset_stats_map[ds]:
                model_m_stats.append(dataset_stats_map[ds][model_alias])
            if ds in dataset_flops_map and model_alias in dataset_flops_map[ds]:
                # Convert FLOPs → PFLOPs (PetaFLOPs, ÷ 10^15) for readability
                f_val = dataset_flops_map[ds][model_alias]
                if f_val > 0:
                    model_flops.append(f_val / 1e15)

        samples = len(model_m_stats)
        if samples == 0:
            # Model was not evaluated on any of the target datasets — skip it
            continue

        # Sum normalised scores across tasks.  Tasks where the model did not
        # run are implicitly zero (no entry in model_m_stats), so models with
        # broader task coverage are not penalised for missing tasks.
        total_rank_score = sum(s['task_rank_score'] for s in model_m_stats)

        aggregated_results[model_alias] = {
            "model": info,
            "performance": {
                "samples": samples,
                "rank_score": total_rank_score,
                "sum_minmax": sum(s['minmax'] for s in model_m_stats),
                "sum_zscore": sum(s['zscore'] for s in model_m_stats),
                "sum_robust": sum(s['robust'] for s in model_m_stats),
                "avg_raw": sum(s['raw'] for s in model_m_stats) / samples,
                "avg_rank": sum(s['rank'] for s in model_m_stats) / samples,
                "top1_count": sum(1 for s in model_m_stats if s['rank'] <= 1),
                "top3_count": sum(1 for s in model_m_stats if s['rank'] <= 3),
                "top5_count": sum(1 for s in model_m_stats if s['rank'] <= 5),
                "top8_count": sum(1 for s in model_m_stats if s['rank'] <= 8),
                "top10_count": sum(1 for s in model_m_stats if s['rank'] <= 10),
                "sum_PFLOPs": sum(model_flops),
                "avg_PFLOPs": sum(model_flops) / len(model_flops) if model_flops else 0.0,
            },
        }

    # Assign overall rank based on rank_score (descending).  The model with
    # the highest cumulative rank_score is ranked #1.
    sorted_models = sorted(
        aggregated_results.items(),
        key=lambda x: x[1]['performance']['rank_score'],
        reverse=True,
    )
    for final_rank, (alias, data) in enumerate(sorted_models, 1):
        data['performance']['rank'] = final_rank

    return {alias: aggregated_results[alias] for alias, _ in sorted_models}


def main():
    # ========================= Configuration =========================
    # Directory containing per-model JSON files produced by the fine-tuning
    # pipeline (e.g. "plant-dnabert-6mer_performance.json").
    input_dir = 'model_performance'

    # Output filename for the all-tasks comparison (written to CWD).
    output_total = 'models_comparison.json'
    # =================================================================

    if not os.path.exists(input_dir):
        print(f"Error: Could not find input directory '{input_dir}'")
        return

    # -------------------- Global accumulators ------------------------
    models_info = {}               # {model_alias: {name, size (M), type, tokenizer, …}}
    raw_dataset_scores = {}        # {dataset_name: {model_alias: raw_primary_metric}}
    raw_dataset_flops = {}         # {dataset_name: {model_alias: FLOPs}}
    dataset_species_map = {}       # {dataset_name: species_label}

    # Mapping from the "metric" field in dataset metadata (e.g. "F1", "AUROC")
    # to the corresponding key inside the "performance" dict (e.g. "f1", "auroc").
    # This allows each task to declare its primary evaluation metric, which may
    # differ: classification tasks use F1/AUROC/AUPRC, regression tasks use
    # Pearson r / Spearman r / R² / MSE.
    metric_key_map = {
        "F1": "f1",
        "MCC": "mcc",
        "AUROC": "auroc",
        "AUPRC": "auprc",
        "MSE": "mse",
        "MAE": "mae",
        "pearsonr": "pearson_r",
        "spearmanr": "spearman_r",
        "R2": "r2",
    }

    # -------------------- Read per-model JSON files ------------------
    print("Reading model data and extracting metrics...")
    for filename in os.listdir(input_dir):
        if not filename.endswith('.json'):
            continue

        file_path = os.path.join(input_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)

        # Derive model alias from filename:
        # e.g. "plant-dnabert-6mer_performance.json" -> "plant-dnabert-6mer"
        model_name = filename.replace("_performance.json", "")
        model_alias = model_name

        # Retain only the leaderboard-relevant model card fields
        models_info[model_alias] = {
            k: v for k, v in model_data.get("info", {}).items()
            if k in [
                "name", "size (M)", "type",
                "tokenizer", "context_len (bp)", "species",
            ]
        }

        perf_data = model_data.get("performance", {})
        cnt = 0
        for dataset_name, ds_content in perf_data.items():
            ds_meta = ds_content.get("dataset", {})
            species = str(ds_meta.get("species", "Unknown")).strip()

            # Record the species category of this dataset (Animal / Plant / Microbe)
            if species:
                dataset_species_map[dataset_name] = species

            # Determine the primary metric declared by this dataset (e.g. "f1",
            # "auroc", "pearson_r").  Fall back to "accuracy" if unspecified.
            metric_key = ds_meta.get("metric", "accuracy")
            if not metric_key:
                metric_key = "accuracy"
            if metric_key in metric_key_map:
                metric_key = metric_key_map[metric_key]

            # Extract the model's raw score and FLOPs for this task
            raw_score = get_float(ds_content.get("performance", {}).get(metric_key, ""))
            flops = get_float(ds_content.get("performance", {}).get("FLOPs", ""))

            # Only include in ranking if the metric value is present (non-empty).
            # Models that failed or were not evaluated on a task will have an
            # empty string for the metric and are excluded from comparison for
            # that specific dataset.
            if ds_content.get("performance", {}).get(metric_key, "") != "":
                if dataset_name not in raw_dataset_scores:
                    raw_dataset_scores[dataset_name] = {}
                raw_dataset_scores[dataset_name][model_alias] = raw_score

            if dataset_name not in raw_dataset_flops:
                raw_dataset_flops[dataset_name] = {}
            raw_dataset_flops[dataset_name][model_alias] = flops
            cnt += 1

    # ---------- Step 1: Per-task normalisation and ranking -----------
    print("Calculating normalised scores and ranks at the dataset level...")
    dataset_stats_map = {}
    for ds_name, scores in raw_dataset_scores.items():
        dataset_stats_map[ds_name] = calculate_dataset_stats(scores)

    # ---------- Step 2: Aggregate across ALL tasks ------------------
    all_datasets = list(raw_dataset_scores.keys())
    total_comparison = aggregate_models(
        models_info, dataset_stats_map, raw_dataset_flops, all_datasets,
    )

    with open(output_total, "w", encoding='utf-8') as f:
        json.dump(total_comparison, f, indent=4, ensure_ascii=False)
    print(f"✅ Global comparison results saved to: {output_total}")

    # ---------- Step 3: Per-species aggregate comparisons ------------
    # Group datasets by their species label (e.g. "Animal", "Plant", "Microbe")
    # and produce a separate comparison file for each group.
    species_groups = {}
    for ds_name, sp in dataset_species_map.items():
        if sp not in species_groups:
            species_groups[sp] = []
        species_groups[sp].append(ds_name)

    for species, ds_list in species_groups.items():
        if species == "Unknown" or not species:
            continue

        species_comparison = aggregate_models(
            models_info, dataset_stats_map, raw_dataset_flops, ds_list,
        )

        if species_comparison:
            # Normalise species name to singular lowercase for the filename,
            # e.g. "Plants" -> "plant" -> "models_comparison_plant.json"
            singular_species = to_singular_species(species)
            safe_species_name = singular_species.replace("/", "_").replace("\\", "_").lower()
            out_file = f'models_comparison_{safe_species_name}.json'
            with open(out_file, "w", encoding='utf-8') as f:
                json.dump(species_comparison, f, indent=4, ensure_ascii=False)
            print(
                f"✅ Species [{species}] comparison saved to: {out_file} "
                f"(contains {len(ds_list)} dataset(s))"
            )

    print("🎉 All statistical comparisons generated successfully!")


if __name__ == "__main__":
    main()
