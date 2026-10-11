# DNALLM-Mark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/zhangtaolab/dnallmmark/actions/workflows/ci.yml/badge.svg)](https://github.com/zhangtaolab/dnallmmark/actions/workflows/ci.yml)

DNALLM-Mark is a comprehensive benchmark platform for evaluating DNA Large Language Models (LLMs) across various genomic prediction tasks. It provides standardized evaluation metrics, interactive leaderboards, and reproducible benchmarks to advance DNA language model research.

![DNALLM-Mark Leaderboard](benchmark/demo.png)

## 🧬 Overview

DNALLM-Mark is a centralized evaluation system designed to assess and compare the performance of DNA-based language models on critical genomic tasks. Built upon the foundation of the [DNALLM](https://github.com/zhangtaolab/DNALLM) framework, this platform enables researchers to:

- **Compare Models**: Evaluate different DNA LLM architectures (GPT-based, Mamba-based, Hyena, etc.) side-by-side
- **Standardize Benchmarks**: Access curated datasets and evaluation protocols
- **Track Performance**: Monitor model performance across multiple genomic prediction tasks with interactive visualizations
- **Reproduce Results**: Use standardized training and evaluation pipelines
- **Explore by Species**: Filter results by animal, plant, or microbe genomes

## ✨ Key Features

### 🏆 Interactive Leaderboards

- **Real-time Rankings**: View model performance sorted by Sum Rank, Score, or efficiency metrics
- **Scatter Plot Visualization**: Explore the relationship between model efficiency (FLOPs) and performance
- **Arena Categories**: Browse models by species type (All, Animal, Plant, Microbe)
- **Detailed Metrics**: Access AUROC, AUPRC, F1, Accuracy, and computational cost for each model

### 🏗️ Supported Model Architectures

- **Transformer-based**: DNABERT series, PlantDNA series, MistralDNA, OmniNA
- **Mamba/SSM-based**: PlantDNA Mamba series, Caduceus, HyenaDNA
- **CNN-based**: GPN, SPACE, DeepSEA derivatives
- **Hybrid Architectures**: Borzoi, Enformer, GenomeOcean, PlantHelixSeek

[SEE ALL MODELS](#supported-model-architectures)

### 🎯 Benchmark Tasks

#### 1. **Core Promoter Prediction**
- **Task Type**: Binary classification
- **Classes**: "Not promoter" vs "Core promoter"
- **Application**: Transcription start site identification
- **Dataset**: Multi-species plant promoter sequences

#### 2. **Histone Modification Prediction**
- **Task Type**: Multi-label classification
- **Application**: Chromatin state prediction
- **Dataset**: ChIP-seq derived histone marks

#### 3. **Gene Expression Prediction**
- **Task Type**: Regression
- **Application**: Predict gene expression levels from sequence
- **Dataset**: RNA-seq based expression quantification

#### 4. **Splice Site Prediction**
- **Task Type**: Binary/Multi-class classification
- **Application**: Alternative splicing analysis
- **Dataset**: Annotated splice junction data

#### [SEE ALL TASKS](#benchmark-tasks)

### 📊 Evaluation Metrics

#### Classification Tasks
- Accuracy, Precision, Recall, F1-score
- Matthews Correlation Coefficient (MCC)
- AUROC and AUPRC
- Confusion matrix analysis

#### Regression Tasks
- R² score
- Pearson and Spearman correlation
- Mean Squared Error (MSE)
- Mean Absolute Error (MAE)

### 🚀 Efficiency Metrics

- **FLOPs**: Computational cost measurement
- **Sum PFLOPs**: Aggregate floating-point operations
- **Rank Score**: Combined ranking across all tasks (higher = better)
- **Sum MinMax**: Normalized performance score

## 📦 Installation

### Prerequisites

- Python 3.13+ (data toolchain — see `.python-version`; the GPU pipeline has its own requirements)
- Node.js 18+ (only for the task-index generator `scripts/generate-tasks-index.js` and the optional `npx http-server` fallback — the web interface itself is static and needs no Node)
- Git

### Clone the Repository

```bash
git clone https://github.com/zhangtaolab/dnallmmark.git
cd dnallmmark
```

## 🎮 Quick Start

### View Leaderboards (Web UI)

```bash
# Start local server
cd dnallm-mark
python3 -m http.server 8080

# Open in browser
open http://localhost:8080
```

## 🔁 Reproducing the Leaderboard

Every command below is literal copy-paste, run from the repository root of
a fresh clone. Each step shows its expected output, so a failed step is
immediately visible. How the numbers are computed is documented in one
place — [docs/METHODOLOGY.md](docs/METHODOLOGY.md); extending the
benchmark (new model or dataset) is documented in
[docs/ONBOARDING.md](docs/ONBOARDING.md).

### 1. Install the data toolchain

```bash
uv sync
```

`uv sync` installs only the `data` dependency group — `default-groups =
["data"]` in `pyproject.toml` deliberately replaces uv's `["dev"]` default
(see the comment there). The dev tools (`pytest`, `ruff`, `ty`,
`jsonschema`) are pulled automatically on demand by the `make` targets
below via `uv run --group dev`. Expected output ends with lines like:

```
Resolved N packages, installed M packages in S
```

(Prerequisites: Python 3.13+ [see `.python-version`], Node.js 18+, and
[uv](https://docs.astral.sh/uv/). No GPU is needed for anything in this
section.)

### 2. Verify the derived data is byte-stable (the drift invariant)

```bash
make data
git status --porcelain dnallm-mark/data/ DATA.md
```

`make data` regenerates the entire derived-data chain from the committed
inputs (aggregation → permutation family → provenance → task index). On
an untouched clone it is a **byte-identical no-op** — the `git status`
line must print nothing. Expected command output:

```
✅ Global comparison results saved to: models_comparison.json
✅ Species [Microbe] comparison saved to: models_comparison_microbe.json (contains 13 dataset(s))
✅ Species [Animals] comparison saved to: models_comparison_animal.json (contains 22 dataset(s))
✅ Species [Plants] comparison saved to: models_comparison_plant.json (contains 12 dataset(s))
✅ Data manifest saved to: manifest.json (data_version 1.1.0)
🎉 All statistical comparisons generated successfully!
✅ Permutation tests: 861 pair(s) (0 excluded) saved to: .../dnallm-mark/data/permutation_tests.json (657 significant at BH FDR 0.05)
✅ Provenance artifacts (50 datasets):
Found 47 task files
✓ Generated tasks.json with 47 tasks
```

This is the repository's core reproducibility guarantee: CI's drift job
runs exactly this check on every pull request and fails on any byte of
drift.

### 3. Run the test suite (both lanes)

```bash
make test
```

Runs the Python lane (`uv run --group dev pytest`) and the Node lane
(`node --test tests/js/`, zero npm deps). Expected output (counts grow as
the suite grows):

```
============================= 389 passed in ~10s =============================   # Python lane
ℹ pass 18                                                                     # Node lane summary
```

### 4. Serve the leaderboard

```bash
bash start-server.sh
```

Expected output, then open <http://localhost:8080> (the ES-module UI needs
an HTTP origin — `file://` does not work):

```
Starting DNALLM Mark server...
Server URL: http://localhost:8080
Press Ctrl+C to stop the server
```

### Fresh-clone proof

The [CI badge](https://github.com/zhangtaolab/dnallmmark/actions/workflows/ci.yml)
at the top of this page replays exactly this chain on every push and pull
request: the pinned CI lane (`make ci`) replays the golden export →
aggregate chain over a committed fixture (`tests/fixtures/e2_replay/`),
and the drift job asserts step 2's no-op invariant — so a green badge is
machine-checked evidence that a fresh clone reproduces the committed
leaderboard data.

### Results snapshots (tamper-evident archives)

The derived-data set (everything in `dnallm-mark/data/` except the
`model_performance/` input) can be frozen into a tar + SHA-256 manifest
for deposition (e.g. Zenodo supplementary information):

```bash
make snapshot
cd baseline/snapshots && sha256sum -c snapshot-*.sha256   # re-verify: every line OK
```

The frozen commit hash is read from the committed
`dnallm-mark/data/manifest.json` (`generated_from`) — never from a live
`git` call — so the lane also works from a tarball-exported tree. The
`.tar` is gitignored (a deposition artifact); only the `.sha256` manifest
is committed as tamper-evidence (`baseline/snapshots/`).

**Re-freeze procedure** (after a future data revision lands, e.g. the
post-recomputation data-v2):

```bash
make data                                   # regenerate from the new inputs
git status --porcelain dnallm-mark/data/ DATA.md   # must be empty BEFORE freezing
make snapshot                               # freeze; verify the new .sha256
git add baseline/snapshots/snapshot-<hash>.sha256 && git commit   # commit the manifest
```

## 📊 Benchmark Pipeline

### Datasets and Models Preparation

<!-- Load-bearing link (do not rotate or strip casually): the Zenodo URL below
     carries an intentional, record-scoped, read-only preview token — maintainer
     decision D-08, see AUDIT.md "Secret-scan evidence". The .gitleaks.toml
     allowlist exists solely to suppress this one link; any change here must
     update that allowlist in the same commit. When Zenodo record 19135551 is
     published, replace this with the public record DOI/URL and drop the
     allowlist rule (tracked as a Phase 6 release item in .planning/ROADMAP.md). -->
Before starting benchmark models on different tasks, users should first download the preseted datasets from [Zenodo](https://zenodo.org/records/19135551?preview=1&token=eyJhbGciOiJIUzUxMiJ9.eyJpZCI6ImVhYzE2MTJmLWQzZDMtNDMxZC04ZTc3LTkyNzk1MTQzMmIxOCIsImRhdGEiOnt9LCJyYW5kb20iOiJhZTc1OTk5N2FjNzA3MjczNzJiYzE4MGM5NDA2ZDg5YiJ9.Btz9VeF52JLK1fzuMXcBJ8ZtD1aR9sHWwNSyc20eahZjgidmlWaRZ6lImsA5Pnw8Ei9vjyGpdXCeY8JdhlntlQ), then extract the datasets to `pipeline/datasets/` directory.

Detailed datasets information are listed in the `datasets_info.json` file, which is used for running the pipeline.

Users should also prepare a model for finetuning, the target model should be put into the `pipeline/models/` directory. Besides, a model information need to be provided in the `models_info.json` file, uncertained information can leave blank:

```json
{
    "model_original_name": {
        "name": "model_short_name",
        "size (M)": "model size",
        "type": "modelling type",
        "tokenizer": "tokenizer type",
        "mean_token_len": "mean length of tokens",
        "architecture": "model architecture",
        "series": "model series",
        "context_len (bp)": "pretrained context length",
        "species": "pretrained datasets species",
        "huggingface": "",
        "modelscope": ""
    },
}
```

Finetuning parameters can be adjusted in the `finetune_config.yaml` configuration file. The pipeline will run all finetuning with the parameters provide in the configuration file.

### Run Pipeline

After preparation of datasets and models, users can directly run the pipeline with the follow script (run from the `pipeline/` directory — `run_finetune.py` resolves `finetune_config.yaml`, its `./logs/` error-log directory, and its `./finetuned` output default against its working directory):

```bash
cd pipeline
python run_finetune.py --target_model model_name --target_dataset dataset_name --seed 9527
```

To drive the full model x task x seed matrix, use the sweep driver instead (launched from the repo root; it launches one `run_finetune.py` subprocess per cell and pins each subprocess to `pipeline/` internally):

```bash
python pipeline/run_sweep.py --seeds 42,43 --output-root ./finetuned --dry-run  # enumerate only, launches nothing
python pipeline/run_sweep.py --seeds 42,43 --output-root ./finetuned           # launch the sweep
```

The detailed arguments are shown below:
```bash
  --target_model TARGET_MODEL
                        Name of the target model for training
  --target_dataset TARGET_DATASET
                        Name of the target dataset for training
  --batch_size BATCH_SIZE
                        Manual batch size
  --max_token_len MAX_TOKEN_LEN
                        Manual max token length in case model with singlebase tokenizer processing extra-long sequences
  --remove_pt           If set, remove .pt files in checkpoints
  --remove_checkpoints  If set, remove the all checkpoints directory except the last one
  --category CATEGORY   Filter datasets by category, supports multiple categories separated by comma (e.g., Plants,Animals,Microbe)
  --task_index TASK_INDEX
                        Filter datasets by index number from datasets_info.json, supports multiple indices separated by comma (e.g., 1,2,7,10)
  --auto_batch_size     If set, automatically adjust batch size based on model size
  --gradient_checkpointing
                        If set, enable HF gradient checkpointing to trade compute for memory
  --ddp_find_unused_parameters
                        If set, force DDP find_unused_parameters=True. Required for MoE models under torchrun
  --cache_dir CACHE_DIR
                        Cache directory for HF_HOME and MS_CACHE_HOME. Overrides env vars. Default: ../../cache relative to this script (or HF_HOME env if set).
  --seed SEED           Random seed
  --gpu_memory GPU_MEMORY
                        Override GPU memory in GB (useful for multi-GPU or incorrect detection)
  --mem_ratio MEM_RATIO
                        Target GPU memory usage ratio (0.0-1.0, default 0.70 for 70%)
  --effective_batch_size EFFECTIVE_BATCH_SIZE
                        Target effective batch size (batch_size * gradient_accumulation_steps). If set, gradient_accumulation will be adjusted to achieve this product.
  --output_dir OUTPUT_DIR
                        Custom output directory for saving finetuned models (default: ./finetuned)
  --save_model_name SAVE_MODEL_NAME
                        Custom model name used in output path (default: use Model_name from models_info.json)
```

Users need to specify a target model with `--target_model` for benchmarking, otherwise all the models defined in the `models_info.json` and existed in the `models/` directory will be processed.

`--target_dataset` can be used for finetuning model on specific datasets (multiple datasets are separated by comma). When finetuning model for all the tasks at one time, an appropariate/optimal `--batch_size` should be manual set as an initial batch size, and `--auto_batch_size` can be set to automatically adjust the batch size based on model size and sequence length.

`--max_token_len` is used for hard cut tokenized sequence if the length is longer than the max_token_len.

`remove_pt` and `remove_checkpoints` are used for saving disk space.

When the pipeline finished, the finetuned models will be stored at `finetuned/{model_name}/{dataset_name}/seed_{seed}/` directories (one seed-isolated output per `--seed`; the sweep driver additionally writes a per-cell `run_record.json` plus `sweep_manifest.json` and `sweep_failures.json` at the output root). Error logs wiil be saved at `logs/` directory. All the finetuned metrics can be visualized via *tensorboard* by setting the log dir to the output foloder:

```bash
tensorboard --logdir=finetuned/
```

Run records land under `finetuned/{model_name}/{task}/seed_{seed}/` (metrics, parameters, resume markers). The per-model leaderboard files (`{model_name}_performance.json`) are NOT written by the training run itself — they are produced by the unified exporter in the next section.

### Export Runs to the Leaderboard

The unified exporter (`script/export_runs.py`) turns finished sweep runs into the leaderboard's task-centric data: it reads the per-cell `run_record.json` files (F2 layout, `finetuned/{model}/{task}/seed_{seed}/`), applies the exporter-owned metric-key mapping, joins `models_info.json` / `datasets_info.json` and `finetune_config.yaml` (the training-parameter block), aggregates over seeds, and writes one `{dataset}_task_performance.json` per task plus a per-seed statistics artifact:

```bash
uv run --group data python script/export_runs.py --input-root ./finetuned
```

This is the regeneration path for `dnallm-mark/data/task_performance/`. Until the benchmark recomputation (E2') produces real run records, the committed `task_performance/` files are **static data** — `make data` does not refresh them (its chain is `summarize_comparison.py` + the task index generator only).


## 🔧 Data Processing

### Input Data Format

Model performance data should be placed in `dnallm-mark/data/model_performance/` directory. Each model should have a separate JSON file named `{model_name}_performance.json`:

```json
{
    "info": {
        "name": "ModelName",
        "size (M)": 37,
        "type": "Transformer",
        "tokenizer": "6mer",
        "context_len (bp)": 1024,
        "species": "plant"
    },
    "performance": {
        "Dataset1": {
            "dataset": {
                "species": "plant",
                "type": "promoter",
                "labels": 2,
                "train": 10000,
                "test": 2000,
                "dev": 2000,
                "length": 200,
                "metric": "F1"
            },
            "parameters": {
                "epochs": 10,
                "batch_size": 32,
                "learning_rate": 1e-4
            },
            "performance": {
                "f1": 0.85,
                "accuracy": 0.82,
                "auroc": 0.91,
                "FLOPs": 1234567890
            }
        }
    }
}
```

### Generate Summary Data

Run the summarization script to generate comparison data from individual model performance files:

```bash
cd dnallm-mark/data

# Generate models_comparison.json (all tasks) and models_comparison_{species}.json (per species)
python ../../script/summarize_comparison.py
```

This will generate:
- `models_comparison.json` - Overall comparison across all tasks with Rank Score, Sum MinMax, Top counts, and efficiency metrics
- `models_comparison_animal.json` - Comparison filtered by animal species
- `models_comparison_plant.json` - Comparison filtered by plant species
- `models_comparison_microbe.json` - Comparison filtered by microbe species

**Output fields:**
- `rank_score` - Sum of rank-based scores across all tasks (higher = better)
- `sum_minmax` - Sum of MinMax normalized scores
- `sum_zscore` - Sum of Z-scores
- `sum_robust` - Sum of robust normalized scores
- `avg_raw` - Average raw metric value across tasks
- `avg_rank` - Average rank across tasks
- `avg_PFLOPs` - Average computational cost in PetaFLOPs per task
- `top1_count`, `top3_count`, `top5_count`, `top8_count`, `top10_count` - Number of tasks in top positions
- `sum_PFLOPs` - Total computational cost in PetaFLOPs
- `rank` - Overall ranking position

### Task Performance Data (per-dataset files)

`dnallm-mark/data/task_performance/` holds one `{dataset}_task_performance.json` per dataset, containing:
- `info` - Dataset metadata (species, type, labels, train/test/dev sizes, etc.)
- `performance` - Per-model performance metrics for this specific dataset/task

These files are **committed static data** until the benchmark recomputation (E2') regenerates them with the unified exporter (see [Export Runs to the Leaderboard](#export-runs-to-the-leaderboard)) — the legacy offline pivot from `model_performance/` was removed; there is no script that regenerates them today.

### Generate Task Index

Regenerate the lightweight task index (`dnallm-mark/data/tasks.json`) consumed by the task benchmark page. Unlike the Python generator above, this one is **not** CWD-sensitive — it resolves paths relative to its own location, so run it from the repo root:

```bash
node scripts/generate-tasks-index.js
```

This rewrites `tasks.json` from the `task_performance/` files. Regenerate it whenever `task_performance/` changes — otherwise the task page serves a stale index (missing or outdated task entries).

> **Note:** the full regeneration chain (`make data`) is: (1) `cd dnallm-mark/data && python ../../script/summarize_comparison.py`, (2) `node scripts/generate-tasks-index.js` (repo root). Shipping only a partial chain leaves derived files inconsistent with `model_performance/`. The `task_performance/` files are inputs to step (2), not outputs of the chain — until E2' regenerates them via `script/export_runs.py`.

## 📁 Project Structure

```
dnallmmark/
├── dnallm-mark/              # Web leaderboard interface
│   ├── index.html            # Main leaderboard page (scatter plot + leaderboard)
│   ├── finetuning.html       # Fine-tuning results (table view)
│   ├── js/                   # JavaScript modules
│   │   ├── config.js         # Configuration (arenas, filters, nav links)
│   │   ├── data.js           # Data loading utilities
│   │   └── main.js           # Main UI logic (rendering, events)
│   ├── css/                  # Stylesheets
│   │   ├── layout.css        # Layout and responsive styles
│   │   ├── charts.css        # Chart and legend styles
│   │   └── components.css    # UI component styles
│   └── data/                 # Data directory
│       ├── model_performance/  # Input: per-model JSON files
│       ├── task_performance/   # Per-dataset JSON files (committed static data until E2')
│       ├── tasks.json          # Generated: task index (scripts/generate-tasks-index.js)
│       └── models_comparison*.json  # Generated: summary comparison files
├── pipeline/                 # Fine-tuning pipeline
│   ├── datasets/             # Datasets directory
│   ├── models/               # Pretrained models directory
│   ├── finetuned/            # Finetuned models directory
│   ├── logs/                 # Finetuning logs directory
│   ├── datasets_info.json    # Datasets information
│   ├── models_info.json      # Models information
│   ├── run_finetune.py         # Training script (benchmark entry point)
│   ├── dnallmmark_pipeline.py  # DEPRECATED legacy pipeline (retained read-only for historical-run attribution)
│   ├── finetune_config.yaml  # Training script
│   └── finetune_config_with_head.yaml  # Configuration file with specific head
├── script/                   # Data processing scripts (Python — repo-root-runnable via make/uv)
│   ├── summarize_comparison.py  # Generate summary comparison data
│   ├── export_runs.py           # Unified exporter (run records -> task_performance; E2' path)
│   ├── convert_registry.py      # Bidirectional registry JSON<->CSV (provenance correction path)
│   ├── audit_n_frequencies.py   # N-frequency + non-ACGT census + eval-subset emission
│   ├── make_dev_splits.py       # Stratified dev-split carving
│   ├── freeze_snapshot.py       # Results snapshot tar + SHA-256 manifest (make snapshot)
│   ├── run_migration_inventory.py  # Data-migration diff inventory + write-manifest
│   ├── permutation_tests.py     # Pairwise permutation tests (861-family, BH-corrected)
│   ├── build_frontier.py        # Cost-accuracy frontier table generator
│   ├── zero_shot_vep.py         # Zero-shot VEP registry batch driver
│   └── doi_swap.py              # Zenodo DOI swap preparation (maintainer-executed)
├── scripts/                  # One-off generators (Node — run from repo root)
│   └── generate-tasks-index.js  # Regenerate data/tasks.json task index
├── baseline/                 # Reproducibility baseline (JSON comparator + SHA256 manifests + pin-validation evidence)
├── AUDIT.md                  # Published audit report (findings, migration records, secret-scan evidence)
├── LICENSE                   # MIT license (code)
├── pyproject.toml            # Dependency groups (data / dev / pipeline)
├── uv.lock                   # Committed lockfile for the data chain
├── requirements.txt          # pip export of the data group
├── .python-version           # Interpreter pin (3.13)
├── .gitleaks.toml            # Secret-scan config (narrow allowlist for the intentional sharing link)
└── README.md
```

## 📞 Contact

- **Issues**: [GitHub Issues](https://github.com/zhangtaolab/dnallmmark/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zhangtaolab/dnallmmark/discussions)
- **Discord**: [Join our community](https://discord.com/invite/Bw9Ajcb3pR)

## 📄 License

- **Code** in this repository is licensed under the [MIT License](LICENSE) (see the badge at the top of this page).
- **Derived leaderboard aggregates** produced by this repository (`dnallm-mark/data/model_performance/`, `dnallm-mark/data/task_performance/`, `models_comparison*.json`, and `tasks.json`) are offered under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
- **Upstream datasets are not redistributed by this repository.** The benchmark datasets are downloaded from the Zenodo record linked in the [Datasets and Models Preparation](#datasets-and-models-preparation) section (the repository tracks only JSON metadata and derived aggregate results) and remain under their original terms; the CC BY 4.0 statement above covers only the repository-produced aggregates.

## 📖 Citation

If you use DNALLM-Mark in your research, please cite:

```bibtex
@misc{dnallmmark_2026,
  title={DNALLM-Mark: A Comprehensive Benchmark Platform for DNA Large Language Models},
  author={Zhang Tao Lab},
  year={2026},
  howpublished={\url{https://github.com/zhangtaolab/dnallmmark}}
}
```

---

**Note**: This repository is under active development. Features and APIs may evolve as we incorporate community feedback.
