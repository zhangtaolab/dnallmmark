import os
import json
import numpy as np
import pandas as pd


def get_float(val, default=0.0):
    """Safely convert value to float"""
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

def calculate_dataset_stats(dataset_records):
    """
    Input format: { model_alias: raw_score }
    Calculate normalized scores and rank points for all participating models on a dataset.
    """
    models = list(dataset_records.keys())
    scores = np.array(list(dataset_records.values()))

    # N represents the total number of models that ran successfully on this task
    N = len(scores)

    if N == 0:
        return {}

    # 1. Calculate Rank (higher score is better, lower rank number is better)
    # method='min' means if scores are the same, assign the highest tied rank (e.g., 1, 1, 3)
    ranks = pd.Series(scores).rank(ascending=False, method='min').values

    # Rank 1 scores N-1; Last rank (rank=N) scores 0
    task_rank_scores = N - ranks

    # 2. Calculate MinMax
    min_s, max_s = np.min(scores), np.max(scores)
    minmax = (scores - min_s) / (max_s - min_s) if max_s > min_s else np.zeros_like(scores)

    # 3. Calculate Z-Score
    mean_s, std_s = np.mean(scores), np.std(scores)
    zscore = (scores - mean_s) / std_s if std_s > 0 else np.zeros_like(scores)

    # 4. Calculate Robust
    q25, q50, q75 = np.percentile(scores, [25, 50, 75])
    iqr = q75 - q25
    robust = (scores - q50) / iqr if iqr > 0 else np.zeros_like(scores)

    # Summarize and return
    stats = {}
    for i, m in enumerate(models):
        stats[m] = {
            'raw': scores[i],
            'rank': ranks[i],                       # Keep true rank to calculate Top1/3/5
            'task_rank_score': task_rank_scores[i], # Competitive score for the current task
            'minmax': minmax[i],
            'zscore': zscore[i],
            'robust': robust[i]
        }
    return stats

def to_singular_species(name):
    """Convert species name to singular form for filename consistency.

    Maps common plural forms to singular:
    - animals -> animal
    - plants -> plant
    - microbes -> microbe

    Args:
        name: Species name (may be plural or singular)
    Returns:
        Species name in singular form
    """
    name_lower = name.lower()
    # Handle common plural mappings
    plural_to_singular = {
        'animals': 'animal',
        'plants': 'plant',
        'microbes': 'microbe',
    }
    return plural_to_singular.get(name_lower, name_lower)


def aggregate_models(models_info, dataset_stats_map, dataset_flops_map, target_datasets):
    """
    Aggregate model performance over a specified list of datasets
    """
    aggregated_results = {}

    # Iterate through all known models
    for model_alias, info in models_info.items():
        # Collect the model's scores in target datasets
        model_m_stats = []
        model_flops = []

        for ds in target_datasets:
            if ds in dataset_stats_map and model_alias in dataset_stats_map[ds]:
                model_m_stats.append(dataset_stats_map[ds][model_alias])
            if ds in dataset_flops_map and model_alias in dataset_flops_map[ds]:
                # Convert FLOPs to PFLOPs (divide by 10^15)
                f_val = dataset_flops_map[ds][model_alias]
                if f_val > 0:
                    model_flops.append(f_val / 1e15)

        samples = len(model_m_stats)
        if samples == 0:
            continue # Skip if it didn't run at all on this subset

        # Aggregate metrics: tasks that failed to run won't be added to model_m_stats, equating to a score of 0
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
                "avg_PFLOPs": sum(model_flops) / len(model_flops) if model_flops else 0.0
            }
        }

    # Calculate overall Rank for the final results, sorted by rank_score in descending order
    sorted_models = sorted(aggregated_results.items(), key=lambda x: x[1]['performance']['rank_score'], reverse=True)
    for final_rank, (alias, data) in enumerate(sorted_models, 1):
        data['performance']['rank'] = final_rank

    # Reconstruct into a dictionary sorted by rank_score
    return {alias: aggregated_results[alias] for alias, _ in sorted_models}


def main():
    # ================= Configuration =================
    input_dir = 'model_performance'  # Directory storing your independent model JSON files
    output_total = 'models_comparison.json'
    # ===============================================

    if not os.path.exists(input_dir):
        print(f"Error: Could not find input directory '{input_dir}'")
        return

    # Global data collection
    models_info = {}                   # { model_alias: info_dict }
    raw_dataset_scores = {}            # { dataset_name: { model_alias: score } }
    raw_dataset_flops = {}             # { dataset_name: { model_alias: flops } }
    dataset_species_map = {}           # { dataset_name: species }
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

    print("Reading model data and extracting metrics...")
    for filename in os.listdir(input_dir):
        if not filename.endswith('.json'):
            continue

        file_path = os.path.join(input_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)

        model_name = filename.replace("_performance.json", "")
        # model_alias = model_data.get("info", {}).get("name", filename.replace("_performance.json", ""))
        model_alias = model_name
        models_info[model_alias] = model_data.get("info", {})
        # keep only name, size, type, tokenizer, context_len and species
        models_info[model_alias] = {
            k: v for k, v in models_info[model_alias].items() 
            if k in [
                "name", "size (M)", "type",
                "tokenizer", "context_len (bp)", "species"
            ]
        }

        perf_data = model_data.get("performance", {})
        cnt = 0
        for dataset_name, ds_content in perf_data.items():
            ds_meta = ds_content.get("dataset", {})
            species = str(ds_meta.get("species", "Unknown")).strip()

            # Record which species this dataset belongs to
            if species:
                dataset_species_map[dataset_name] = species

            # Determine the evaluation metric to compare (fallback to accuracy)
            metric_key = ds_meta.get("metric", "accuracy")
            if not metric_key:
                metric_key = "accuracy"
            if metric_key in metric_key_map:
                metric_key = metric_key_map[metric_key]

            raw_score = get_float(ds_content.get("performance", {}).get(metric_key, ""))
            flops = get_float(ds_content.get("performance", {}).get("FLOPs", ""))

            # Only add to comparison queue if the score is valid (not empty), can be modified to >=0 if needed
            if ds_content.get("performance", {}).get(metric_key, "") != "":
                if dataset_name not in raw_dataset_scores:
                    raw_dataset_scores[dataset_name] = {}
                raw_dataset_scores[dataset_name][model_alias] = raw_score

            if dataset_name not in raw_dataset_flops:
                raw_dataset_flops[dataset_name] = {}
            raw_dataset_flops[dataset_name][model_alias] = flops
            cnt += 1

    # 1. Calculate horizontal comparison scores within each dataset (Rank, Zscore, etc.)
    print("Calculating horizontal scoring and normalization at the dataset level...")
    dataset_stats_map = {}
    for ds_name, scores in raw_dataset_scores.items():
        dataset_stats_map[ds_name] = calculate_dataset_stats(scores)

    # 2. Aggregate and generate global comparison results
    all_datasets = list(raw_dataset_scores.keys())
    total_comparison = aggregate_models(models_info, dataset_stats_map, raw_dataset_flops, all_datasets)

    with open(output_total, "w", encoding='utf-8') as f:
        json.dump(total_comparison, f, indent=4, ensure_ascii=False)
    print(f"✅ Global comparison results saved to: {output_total}")

    # 3. Split by Species and aggregate separately
    # First find out what species exist
    species_groups = {}
    for ds_name, sp in dataset_species_map.items():
        if sp not in species_groups:
            species_groups[sp] = []
        species_groups[sp].append(ds_name)

    for species, ds_list in species_groups.items():
        if species == "Unknown" or not species:
            continue

        species_comparison = aggregate_models(models_info, dataset_stats_map, raw_dataset_flops, ds_list)

        # Generate JSON only if there is data
        if species_comparison:
            # Convert species name to singular form for consistency
            singular_species = to_singular_species(species)
            safe_species_name = singular_species.replace("/", "_").replace("\\", "_").lower()
            out_file = f'models_comparison_{safe_species_name}.json'
            with open(out_file, "w", encoding='utf-8') as f:
                json.dump(species_comparison, f, indent=4, ensure_ascii=False)
            print(f"✅ Species [{species}] exclusive comparison results saved to: {out_file} (contains {len(ds_list)} datasets)")

    print("🎉 All statistical comparisons generated successfully!")


if __name__ == "__main__":
    main()