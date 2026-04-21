"""
Pivot model-centric benchmark results into task-centric (dataset-centric) JSON files.

DNALLM-Mark evaluates DNA language models (e.g. DNABERT, Caduceus, HyenaDNA,
GPN, Enformer, etc.) across dozens of genomic prediction tasks such as promoter
prediction, histone modification, splice site detection, and gene expression
regression.

After the fine-tuning pipeline completes, it writes one ``{model}_performance.json``
per model into ``dnallm-mark/data/model_performance/``, where each file records
that model's metrics across **all** benchmark datasets.

This script performs a dimensional pivot:

- **Input**  — ``model_performance/``: one JSON per model → many datasets inside.
- **Output** — ``task_performance/``: one JSON per dataset → many models inside.

The resulting per-task files are consumed by the DNALLM-Mark web leaderboard
(``finetuning.html``) to render side-by-side model comparisons on individual
benchmark tasks such as ``GUE__emp_H3``, ``PDLLMs_datasets__plant-multi-species-core-promoters``,
``NT_downstream_tasks__splice_sites_donors``, etc.

Usage (run from ``dnallm-mark/data/``)::

    cd dnallm-mark/data
    python ../../script/get_task_performance.py

Input JSON structure (per model)::

    {
        "info": {                          # model card (name, architecture, species …)
            "name": "PlantDNABERT-6mer",
            "size (M)": 89,
            "architecture": "Bert",
            "tokenizer": "6-mer",
            "context_len (bp)": 2000,
            "species": "plants",
            ...
        },
        "performance": {
            "<dataset_name>": {
                "dataset": { ... },        # dataset metadata (species, type, labels, metric …)
                "parameters": { ... },     # fine-tuning hyper-parameters (epochs, lr …)
                "performance": { ... }     # evaluation metrics (f1, auroc, auprc, FLOPs …)
            },
            ...
        }
    }

Output JSON structure (per dataset)::

    {
        "info": { ... },                   # dataset metadata (same as input "dataset" field)
        "performance": {
            "<model_name_key>": {
                "model": { ... },          # model card
                "parameters": { ... },     # fine-tuning hyper-parameters used
                "performance": { ... }     # evaluation metrics on this dataset
            },
            ...
        }
    }

See also:
    - ``script/summarize_comparison.py``  — produces the leaderboard summary files
      (``models_comparison.json`` and per-species variants) used on the main page.
    - ``pipeline/dnallmmark_pipeline.py`` — the fine-tuning pipeline that generates
      the per-model input files.
"""

import os
import json


def main():
    # ========================= Configuration =========================
    # Source directory: one ``{model_name}_performance.json`` per evaluated DNA LLM.
    input_dir = "model_performance"

    # Target directory: one ``{dataset_name}_task_performance.json`` per benchmark
    # task/dataset, aggregating all models that were evaluated on that task.
    output_dir = "task_performance"
    # =================================================================

    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        return

    os.makedirs(output_dir, exist_ok=True)

    # Accumulator keyed by dataset name (e.g. "GUE__emp_H3",
    # "PDLLMs_datasets__plant-multi-species-core-promoters").
    # Each value holds the dataset's metadata under "info" and a dict of
    # per-model results under "performance".
    datasets_data: dict = {}

    print(f"Reading model data from '{input_dir}/', pivoting by dataset...")

    file_count = 0
    for filename in os.listdir(input_dir):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(input_dir, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                model_data = json.load(f)
        except Exception as e:
            print(f"  [Skip] Failed to read file {filename}: {e}")
            continue

        file_count += 1

        # Extract the model card (architecture, size, tokenizer, species, etc.)
        model_info = model_data.get("info", {})

        # Derive a stable model key from the filename.
        # e.g. "plant-dnabert-6mer_performance.json" -> "plant-dnabert-6mer"
        model_name_key = filename.replace("_performance.json", "")
        model_performance = model_data.get("performance", {})

        # Re-organise: move each (dataset -> metrics) pair out of the model
        # entry and into a dataset-centric entry.
        for dataset_name, ds_content in model_performance.items():
            if dataset_name not in datasets_data:
                # First model encountered on this dataset: initialise the
                # top-level structure with dataset metadata (species, task
                # type, label count, train/test/dev sizes, primary metric …).
                datasets_data[dataset_name] = {
                    "info": ds_content.get("dataset", {}),
                    "performance": {},
                }

            # Mount this model's results under the dataset entry.
            # Keeps model card, fine-tuning parameters, and evaluation
            # metrics (f1, auroc, auprc, accuracy, FLOPs, etc.) together
            # so the leaderboard can render per-task model comparisons.
            datasets_data[dataset_name]["performance"][model_name_key] = {
                "model": model_info,
                "parameters": ds_content.get("parameters", {}),
                "performance": ds_content.get("performance", {}),
            }

    print(
        f"Read {file_count} model file(s), "
        f"found {len(datasets_data)} unique benchmark dataset(s) after aggregation."
    )
    print("Generating task-level performance reports...")

    # ========================= Write output ==========================
    saved_count = 0
    for dataset_name, ds_data in datasets_data.items():
        # Sanitise the dataset name for use as a filename.
        # e.g. "GUE/emp_H3" -> "GUE_emp_H3"
        safe_dataset_name = str(dataset_name).replace("/", "_").replace("\\", "_")

        out_file = os.path.join(output_dir, f"{safe_dataset_name}_task_performance.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(ds_data, f, indent=4, ensure_ascii=False)
        saved_count += 1

    print("\n✅ Dimension conversion completed!")
    print(f"✅ Successfully generated {saved_count} task-level JSON file(s).")
    print(f"✅ Output directory: {output_dir}/")


if __name__ == "__main__":
    main()
