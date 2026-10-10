"""
Generate leaderboard comparison summaries from per-model benchmark results.

DNALLM-Mark evaluates dozens of DNA language models (DNABERT, Caduceus, HyenaDNA,
GPN, Enformer, GenomeOcean, etc.) across genomic prediction tasks such as promoter
prediction, histone modification classification, splice site detection, and gene
expression regression.

This script reads the per-model benchmark results directly (the model-centric
``{model}_performance.json`` files) and computes **aggregated ranking
statistics** across all benchmark tasks (or a species-specific subset) for
every model, producing the JSON files that power the DNALLM-Mark interactive
leaderboard (``index.html``).

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
- ``models_comparison_animal.json``     — only tasks in the Animals arena.
- ``models_comparison_plant.json``      — only tasks in the Plants arena.
- ``models_comparison_microbe.json``   — only tasks in the Microbe arena.
- ``manifest.json``                     — the data-version stamp (data_version,
  generated_from, date — constants from the Configuration block; DATA-02).

Arena grouping (FIX-02) is driven by the human-verified ``Category`` column of
``pipeline/datasets_info.json`` (the maintainer-confirmed 50-row review in
``.planning/phases/04-correctness-methodology-core/04-CATEGORY-REVIEW.md``),
never by the result JSON's ``dataset.species`` producer string;
"Multiple"-origin datasets classify into their majority arena.

Each file contains a dict keyed by model alias, sorted by ``rank_score`` descending::

    {
        "plant-dnabert-6mer": {
            "model": { "name": "...", "size (M)": ..., "type": "...", ... },
            "performance": {
                "samples": 47,
                "rank_score": 120.0,
                "sum_minmax": 38.5,
                "sum_zscore": 12.3,
                "weighted_score": 0.2617,
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
    - ``script/export_runs.py`` — owns the metric-key mapping this script
      imports (IN-03 single authority) and, at E2', regenerates the per-task
      JSON files used by the finetuning results page.
    - ``script/permutation_tests.py`` — the pairwise permutation family over
      this script's zscores (F6 Q3); imports ``load_model_inputs`` here.
"""

import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from export_runs import resolve_dataset_metric

# ---------------------------------------------------------------------------
# Arena grouping source (FIX-02): every dataset's arena comes from the
# human-verified ``Category`` column of ``pipeline/datasets_info.json`` —
# never from the result JSON's ``dataset.species`` producer string.
# ``REGISTRY_PATH`` is resolved relative to this script file's location (the
# script runs with ``cwd = dnallm-mark/data/`` via ``make data``) and is a
# plain module attribute so tests can monkeypatch a synthetic registry onto
# it.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "pipeline" / "datasets_info.json"

# "Multiple"-origin datasets (cross-species composition, e.g. iDNA_ABF
# 5mC/6mA) classify into their majority-species arena (CONTEXT species-Q4).
# Confirmed as ``Animals`` at the maintainer review gate
# (04-CATEGORY-REVIEW.md); confirmed values produce zero net grouping change.
MAJORITY_ARENA = {"Multiple": "Animals"}


def load_arena_map():
    """Load ``{Dataset_name: arena}`` from the unified dataset registry.

    The arena is each registry entry's ``Category`` value with
    "Multiple"-origin rows resolved to their majority arena via
    ``MAJORITY_ARENA``. Keys are the ``Source__task``-form dataset names —
    the same form the result-JSON ``performance`` dict uses — so the
    grouping join is a plain dict lookup: a dataset with no registry row
    raises ``KeyError`` (hard abort), never a silent fallback to the result
    file's own ``species`` value.

    Returns:
        dict[str, str]: dataset/task name -> arena (Animals/Plants/Microbe).
    """
    with REGISTRY_PATH.open("r", encoding="utf-8") as fh:
        registry = json.load(fh)
    return {
        name: MAJORITY_ARENA.get(entry["Category"], entry["Category"])
        for name, entry in registry.items()
    }


def get_float(val, default=0.0):
    """Safely coerce a metric value to a finite ``float``.

    Many evaluation metrics may be missing (empty string or ``None``) when a
    model fails or the metric is not applicable to the task type (e.g. ``r2``
    for a classification task).  This helper returns ``default`` in those
    cases.  A value that coerces successfully but is non-finite (``nan``,
    ``inf``, ``-inf`` — WR-03, fixed Phase 4) is also treated as missing:
    returning it would pass the presence gate as a real score and poison a
    whole task's normalisation arithmetic.

    Args:
        val:    Raw metric value — may be a number, ``""``, or ``None``.
        default: Fallback value when conversion fails (default ``0.0``).
    """
    try:
        if val is None or str(val).strip() == "":
            return default
        result = float(val)
    except (ValueError, TypeError):
        return default
    if not math.isfinite(result):
        return default
    return result


def _closed_intervals_intersect(a, b):
    """Closed-interval intersection test (REV-04 boundary truth).

    Intervals ``[lo_a, hi_a]`` and ``[lo_b, hi_b]`` intersect when
    ``lo_a <= hi_b and lo_b <= hi_a`` — touching at exactly one point
    (``lo_a == hi_b``) counts as a tie.

    Args:
        a: First interval ``(lo, hi)``.
        b: Second interval ``(lo, hi)``.

    Returns:
        bool: True when the closed intervals intersect.
    """
    return a[0] <= b[1] and b[0] <= a[1]


def calculate_dataset_stats(dataset_records, ci_map=None):
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

    F6 CI-overlap tie rule (REV-04): when ``ci_map`` supplies a closed 95%
    interval for a model, "tie" is widened from exact score equality to
    closed-interval overlap — models whose intervals intersect form connected
    components of the overlap graph (A~B and B~C tie all three even when A
    and C do not overlap) and every member receives the component's MINIMUM
    rank per the ``method='min'`` convention, so ``task_rank_score = N -
    rank`` stays coherent. The intervals are CONSUMED here, never computed:
    the single sanctioned producer is the vendored ``aggregate_seeds`` in
    ``script/export_runs.py`` (n<3 -> ci95 null/method "none"; 3<=n<10 ->
    t-interval; n>=10 -> seeded bootstrap — the F6 statistical-semantics
    correction). Models with no interval entry (``ci_map=None``, a ``None``
    entry, or an absent key) keep pure score ranking, so pre-E2' single-run
    data — which has no CI source — reproduces the exact-tie output
    byte-identically.

    Args:
        dataset_records: ``{model_alias: raw_score}`` for one task/dataset.
        ci_map: Optional ``{model_alias: (lo, hi) | None}`` of closed 95%
            intervals (e.g. built from the vendored ``aggregate_seeds``
            output). Only models with a non-``None`` entry join the overlap
            graph.

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

    # 1b. F6 CI-overlap tie rule: re-assign each overlap-graph connected
    #     component its minimum rank (see docstring). With no ci_map — or no
    #     interval entries — this block is a no-op and the exact-tie ranks
    #     above flow through unchanged.
    if ci_map is not None:
        interval_models = [m for m in models if ci_map.get(m) is not None]
        if len(interval_models) > 1:
            rank_of = {m: ranks[i] for i, m in enumerate(models)}
            # Union-find over the closed-interval overlap graph.
            parent = {m: m for m in interval_models}

            def find(x):
                root = x
                while parent[root] != root:
                    root = parent[root]
                while parent[x] != root:  # path compression
                    parent[x], x = root, parent[x]
                return root

            for i, model_a in enumerate(interval_models):
                for model_b in interval_models[i + 1:]:
                    if _closed_intervals_intersect(ci_map[model_a], ci_map[model_b]):
                        parent[find(model_a)] = find(model_b)
            component_min = {}
            for m in interval_models:
                root = find(m)
                component_min[root] = min(component_min.get(root, N + 1), rank_of[m])
            for i, m in enumerate(models):
                if m in parent:
                    ranks[i] = component_min[find(m)]

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


def aggregate_models(models_info, dataset_stats_map, dataset_flops_map, target_datasets,
                     *, include_weighted=False):
    """Aggregate per-task normalised scores into overall model rankings.

    For each model, this function sums its normalised scores (rank score,
    MinMax, Z-Score, robust) across all datasets in *target_datasets*, counts
    how many tasks the model appeared in (``samples``), and records Top-K
    placement counts.  Models not evaluated on a given task simply receive no
    contribution for that task.

    After aggregation, models are assigned a final overall ``rank`` based on
    ``rank_score`` in descending order.

    F6 weighted view (REV-04/F6 Q2): with ``include_weighted=True`` each
    performance block also carries ``weighted_score`` — the sum of per-task
    zscores divided by ``len(target_datasets)``, the aggregation view's FULL
    task count as a uniform ``1/N`` difficulty weight. It follows the same
    no-imputation convention as ``sum_zscore``: a model missing tasks
    contributes nothing for them (numerator) while the denominator still
    counts the view's tasks. ``main()`` emits it (schema-required since the
    F6 migration); direct calls default to the pure 15-key block.

    Args:
        models_info:         ``{model_alias: {name, size (M), type, …}}``
        dataset_stats_map:   ``{dataset_name: {model_alias: {raw, rank, …}}}``
                             as returned by :func:`calculate_dataset_stats`.
        dataset_flops_map:   ``{dataset_name: {model_alias: FLOPs}}``
        target_datasets:     List of dataset names to include in this aggregation
                             (e.g. all datasets, or only plant-specific ones).
        include_weighted:    Emit ``weighted_score`` (F6 weighted view). Off by
                             default for pure-function callers; ``main()`` sets
                             it True.

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

        # F6 weighted view (uniform 1/N difficulty weight over the view's
        # tasks): sum_zscore / len(target_datasets), same no-imputation
        # convention as the sums above. main() emits it (schema-required
        # since the F6 migration); pure-function callers keep the 15-key
        # block by default.
        if include_weighted:
            aggregated_results[model_alias]["performance"]["weighted_score"] = (
                sum(s['zscore'] for s in model_m_stats) / len(target_datasets)
            )

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


def load_model_inputs(input_dir):
    """Read the per-model result files and extract the aggregation inputs.

    The extraction half of :func:`main` (moved verbatim, 05-02): iterates the
    per-model JSON files, retains the 7-key leaderboard card subset, joins
    each dataset's arena through the registry ``Category`` map (FIX-02), and
    extracts the raw primary-metric score and FLOPs per model per task with
    the ``get_float(default=None)`` presence gate. Also the single extraction
    source for the permutation-test engine (``script/permutation_tests.py``)
    — one reader over the model-centric inputs, never a duplicated loop.

    Args:
        input_dir: Directory containing ``{alias}_performance.json`` files.

    Returns:
        Tuple ``(models_info, raw_dataset_scores, raw_dataset_flops,
        dataset_species_map)`` — the leaderboard card subset map, per-task
        raw primary-metric scores (presence-gated), per-task FLOPs (recorded
        regardless of metric presence), and the per-dataset arena labels.
    """
    models_info = {}               # {model_alias: {name, size (M), type, tokenizer, …}}
    raw_dataset_scores = {}        # {dataset_name: {model_alias: raw_primary_metric}}
    raw_dataset_flops = {}         # {dataset_name: {model_alias: FLOPs}}
    dataset_species_map = {}       # {dataset_name: species_label}

    # Arena grouping map (FIX-02): {dataset_name: arena} from the registry's
    # maintainer-confirmed Category column, Multiple resolved to majority
    # arena. Loaded once — the dataset loop below joins via plain lookup.
    arena_map = load_arena_map()

    print("Reading model data and extracting metrics...")
    for filename in sorted(os.listdir(input_dir)):
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
                "tokenizer", "series",
                "context_len (bp)", "species",
            ]
        }

        perf_data = model_data.get("performance", {})
        for dataset_name, ds_content in perf_data.items():
            ds_meta = ds_content.get("dataset", {})

            # Record the dataset's arena (Animal / Plant / Microbe). FIX-02:
            # the arena comes from the registry Category join (see
            # load_arena_map) — a plain dict lookup, so a dataset with no
            # registry row aborts the run (KeyError). The result JSON's
            # dataset.species producer string is never read for grouping.
            dataset_species_map[dataset_name] = arena_map[dataset_name]

            # Determine the primary metric declared by this dataset (e.g. "f1",
            # "auroc", "pearson_r").  Fall back to "accuracy" if unspecified.
            # IN-03 (04-05): the legacy/uppercase spellings ("F1", "AUROC", …)
            # resolve through the exporter-owned translation — the single
            # authority over both key surfaces; the local mirror is deleted.
            metric_key = ds_meta.get("metric", "accuracy")
            if not metric_key:
                metric_key = "accuracy"
            metric_key = resolve_dataset_metric(metric_key)

            # Extract the model's raw score and FLOPs for this task. raw_score
            # is None exactly when the metric is missing under the semantics
            # get_float documents (None, "", or whitespace-only strings).
            raw_score = get_float(ds_content.get("performance", {}).get(metric_key, ""), default=None)
            flops = get_float(ds_content.get("performance", {}).get("FLOPs", ""))

            # Only include in ranking if the metric value is present. Presence
            # is derived from get_float itself so a null or whitespace-only
            # metric can never enter the ranking as a real 0.0 score (which
            # would drag every other model's rank on that task). Models that
            # failed or were not evaluated on a task are excluded from
            # comparison for that specific dataset.
            if raw_score is not None:
                if dataset_name not in raw_dataset_scores:
                    raw_dataset_scores[dataset_name] = {}
                raw_dataset_scores[dataset_name][model_alias] = raw_score

            if dataset_name not in raw_dataset_flops:
                raw_dataset_flops[dataset_name] = {}
            raw_dataset_flops[dataset_name][model_alias] = flops

    return models_info, raw_dataset_scores, raw_dataset_flops, dataset_species_map


def main():
    # ========================= Configuration =========================
    # Directory containing per-model JSON files produced by the fine-tuning
    # pipeline (e.g. "plant-dnabert-6mer_performance.json").
    input_dir = 'model_performance'

    # Output filename for the all-tasks comparison (written to CWD).
    output_total = 'models_comparison.json'

    # F6 data-version stamp (DATA-02, D-17/OQ2): manifest.json constants —
    # CONSTANTS ONLY, never a live clock or a live git call in this
    # regeneration path (the drift job must stay a byte-identical no-op).
    # Bumped EXCLUSIVELY in migration commits, alongside CHANGELOG.md and
    # the migration inventory.
    DATA_VERSION = "1.1.0"
    GENERATED_FROM = "991804613c4874bfa3f32d318340b5d7b4118ffe"  # pre-D-18-rename HEAD
    DATE = "2026-10-10"
    # =================================================================

    if not os.path.exists(input_dir):
        print(f"Error: Could not find input directory '{input_dir}'")
        return

    # -------------------- Read per-model JSON files ------------------
    # (extraction lives in load_model_inputs — the single reader shared with
    # script/permutation_tests.py; verbatim move, output unchanged)
    models_info, raw_dataset_scores, raw_dataset_flops, dataset_species_map = (
        load_model_inputs(input_dir)
    )

    # ---------- Step 1: Per-task normalisation and ranking -----------
    print("Calculating normalised scores and ranks at the dataset level...")
    dataset_stats_map = {}
    for ds_name, scores in raw_dataset_scores.items():
        dataset_stats_map[ds_name] = calculate_dataset_stats(scores)

    # ---------- Step 2: Aggregate across ALL tasks ------------------
    all_datasets = list(raw_dataset_scores.keys())
    total_comparison = aggregate_models(
        models_info, dataset_stats_map, raw_dataset_flops, all_datasets,
        include_weighted=True,
    )

    with open(output_total, "w", encoding='utf-8') as f:
        json.dump(total_comparison, f, indent=4, ensure_ascii=False, sort_keys=True)
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
            include_weighted=True,
        )

        if species_comparison:
            # Normalise species name to singular lowercase for the filename,
            # e.g. "Plants" -> "plant" -> "models_comparison_plant.json"
            singular_species = to_singular_species(species)
            safe_species_name = singular_species.replace("/", "_").replace("\\", "_").lower()
            out_file = f'models_comparison_{safe_species_name}.json'
            with open(out_file, "w", encoding='utf-8') as f:
                json.dump(species_comparison, f, indent=4, ensure_ascii=False, sort_keys=True)
            print(
                f"✅ Species [{species}] comparison saved to: {out_file} "
                f"(contains {len(ds_list)} dataset(s))"
            )

    # ---------- Step 4: Data-version manifest (DATA-02, D-17/OQ2) ----
    # The stamped identity the leaderboard footer reads (the live clock is
    # gone, DATA-06): data_version + the pre-migration commit this data was
    # regenerated from + the migration date — all constants declared in the
    # Configuration block above, byte-stable under regeneration.
    with open('manifest.json', 'w', encoding='utf-8') as f:
        json.dump(
            {
                "data_version": DATA_VERSION,
                "generated_from": GENERATED_FROM,
                "date": DATE,
            },
            f, indent=4, ensure_ascii=False, sort_keys=True,
        )
    print(f"✅ Data manifest saved to: manifest.json (data_version {DATA_VERSION})")

    print("🎉 All statistical comparisons generated successfully!")


if __name__ == "__main__":
    main()
