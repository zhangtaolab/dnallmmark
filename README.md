# DNALLM-Mark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

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
- **Hybrid Architectures**: Borzoi, Enformer, GenomeOcean

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

- Python 3.11+
- Node.js 18+ (for web interface)
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

## 📊 Benchmark Pipeline

### Datasets and Models Preparation

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

After preparation of datasets and models, users can directly run the pipeline with the follow script:

```bash
python dnallmmark_pipeline.py --target_model model_name --batch_size initial_batch_size --remove_pt
```

The detailed arguments are shown below:
```bash
  --target_model TARGET_MODEL
                        Name of the target model for training
  --target_dataset TARGET_DATASET
                        Name of the target dataset for training
  --batch_size BATCH_SIZE
                        Manual batch size
  --fix_token_len FIX_TOKEN_LEN
                        Manual set max token length
  --max_token_len MAX_TOKEN_LEN
                        Manual max token length in case model with singlebase tokenizer processing extra-long sequences
  --remove_pt           If set, remove .pt files in checkpoints
  --remove_checkpoints  If set, remove the all checkpoints directory except the last one
  --seed SEED           Random seed
```

Users need to specify a target model with `--target_model` for benchmarking, otherwise all the models defined in the `models_info.json` and existed in the `models/` directory will be processed.

`--target_dataset` can be used for finetuning model on specific datasets (multiple datasets are separated by comma). When finetuning model for all the tasks at one time, an appropariate/optimal `--batch_size` should be manual set as an initial batch_size, since this script will automatically adjust batch size for each dataset according to the sequence length.

`--fix_token_len` is used if users want to fix the tokenized sequence length, `--max_token_len` is used for hard cut tokenized sequence if the length is longer than the max_token_len.

`remove_pt` and `remove_checkpoints` are used for saving disk space.

When the pipeline finished, the finetuned models will be stored at `finetuned/{model_name}/{dataset_name}/` directories. Error logs wiil be saved at `logs/` directory. All the finetuned metrics can be visualized via *tensorboard* by setting the log dir to the output foloder:

```bash
tensorboard --logdir=finetuned/
```

The pipeline will also generate a summarized performance result for the target model named `{model_name}_performance.json` in the `finetuned/{model_name}/` directory. This file can be further used for visualized and comparison in the DNALLM-Mark, please see the next section for detailed usage.


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
- `models_comparison_animals.json` - Comparison filtered by animal species
- `models_comparison_plants.json` - Comparison filtered by plant species
- `models_comparison_microbe.json` - Comparison filtered by microbe species

**Output fields:**
- `rank_score` - Sum of rank-based scores across all tasks (higher = better)
- `sum_minmax` - Sum of MinMax normalized scores
- `sum_zscore` - Sum of Z-scores
- `sum_robust` - Sum of robust normalized scores
- `avg_raw` - Average raw metric value across tasks
- `avg_rank` - Average rank across tasks
- `top1_count`, `top3_count`, `top5_count`, `top10_count` - Number of tasks in top positions
- `sum_PFLOPs` - Total computational cost in PetaFLOPs
- `rank` - Overall ranking position

### Generate Task Performance Data

Run the task performance script to reorganize data by dataset/task for fine-tuning results page:

```bash
cd dnallm-mark/data

# Generate task_performance/ directory with per-dataset JSON files
python ../../script/get_task_performance.py
```

This will generate `task_performance/{dataset_name}_task_performance.json` for each dataset, containing:
- `info` - Dataset metadata (species, type, labels, train/test/dev sizes, etc.)
- `performance` - Per-model performance metrics for this specific dataset/task

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
│       ├── task_performance/   # Generated: per-dataset JSON files
│       └── models_comparison*.json  # Generated: summary comparison files
├── pipeline/                 # Fine-tuning pipeline
│   ├── datasets/             # Datasets directory
│   ├── models/               # Pretrained models directory
│   ├── finetuned/            # Finetuned models directory
│   ├── logs/                 # Finetuning logs directory
│   ├── datasets_info.json    # Datasets information
│   ├── models_info.json      # Models information
│   ├── dnallmmark_pipeline.py  # Training script
│   ├── finetune_config.yaml  # Training script
│   └── finetune_config_with_head.yaml  # Configuration file with specific head
├── script/                   # Data processing scripts
│   ├── summarize_comparison.py  # Generate summary comparison data
│   └── get_task_performance.py  # Generate per-dataset performance data
└── README.md
```

## 📞 Contact

- **Issues**: [GitHub Issues](https://github.com/zhangtaolab/dnallmmark/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zhangtaolab/dnallmmark/discussions)
- **Discord**: [Join our community](https://discord.com/invite/Bw9Ajcb3pR)

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
