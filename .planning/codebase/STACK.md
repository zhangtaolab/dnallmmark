---
last_mapped_commit: a44d3104b8ab1e04ddbebed75446772fc0ca3f1b
last_mapped_at: 2026-10-08
---
# Technology Stack

**Analysis Date:** 2026-10-08

## Languages

**Primary:**
- Python 3.11+ - Fine-tuning pipeline (`pipeline/dnallmmark_pipeline.py`) and data-processing scripts (`script/summarize_comparison.py`, `script/get_task_performance.py`)
- JavaScript (ES6 modules, no framework, no build step) - Web leaderboard UI (`dnallm-mark/js/*.js`)
- HTML/CSS - Static pages (`dnallm-mark/*.html`, `dnallm-mark/css/*.css`)

**Secondary:**
- Bash - Local server launcher (`start-server.sh`)
- YAML - Training configuration (`pipeline/finetune_config.yaml`, `pipeline/finetune_config_with_head.yaml`)
- Node.js (plain `fs`/`path`, no deps) - One-off index generator (`scripts/generate-tasks-index.js`)

## Runtime

**Environment:**
- Python 3.11+ required (per `README.md` badge); GPU with CUDA expected for pipeline training (`torch.cuda.manual_seed_all` at `pipeline/dnallmmark_pipeline.py:752`, bf16 autocast at `pipeline/dnallmmark_pipeline.py:1095`)
- Data chain pinned to Python 3.13 via `.python-version` (uv-managed; plan 01-01, D-07)
- Node.js 18+ optional (only needed for `npx http-server` fallback in `start-server.sh:20-22`)

**Package Manager:**
- uv 0.12.23 with committed lockfile (plan 01-01): `pyproject.toml` (PEP 621 + PEP 735 `[dependency-groups]`) + `uv.lock` + pip-compatible `requirements.txt` export (`uv export --group data --no-emit-project`)
- Groups: `data` (default; `pandas>=2.2,<3.0`, `numpy>=2.0,<3` — D-05 floor bounds, locked to pandas 2.3.3 / numpy 2.5.3), `dev` (empty until Phase 2), `pipeline` (GPU-only `torch>=2.0`, `transformers>=4.0` — never CI-installed; `dnallm` deliberately absent until Phase 3)
- Fresh install: `uv sync` (data group only); pin-validation evidence in `baseline/PIN-VALIDATION.md`

## Frameworks

**Core:**
- None for the web UI — pure HTML/CSS/ES-module JavaScript, served as static files (no React/Vue/bundler)
- DNALLM (external, https://github.com/zhangtaolab/DNALLM) - DNA LLM finetuning framework wrapping Hugging Face; imported at `pipeline/dnallmmark_pipeline.py:18` as `from dnallm import DNADataset, load_config, load_model_and_tokenizer, DNATrainer`
- PyTorch (`torch`, `torch.nn`) - model training, FLOPs instrumentation via forward hooks (`pipeline/dnallmmark_pipeline.py:16-17`, `FlopsCounter` at line 24)
- Hugging Face Transformers - lazy fallback loader (`AutoConfig`/`AutoModelForSequenceClassification`/`AutoTokenizer` with `trust_remote_code=True`, `pipeline/dnallmmark_pipeline.py:880-898`); training args follow the `transformers.TrainingArguments` schema

**Testing:**
- Not detected. No test framework, no test files anywhere in the repo.

**Build/Dev:**
- No build step. Development server: `bash start-server.sh` (runs `python3 -m http.server 8080` from `dnallm-mark/`, `start-server.sh:13-22`)
- TensorBoard for training metrics: `report_to: "tensorboard"` in both YAML configs; view via `tensorboard --logdir=finetuned/` (per `README.md:179`)

## Key Dependencies

**Critical (Python, pipeline):**
- `dnallm` - external framework providing `DNADataset`, `DNATrainer`, `load_config`, `load_model_and_tokenizer`; the entire training loop is delegated to it (`pipeline/dnallmmark_pipeline.py:1144-1193`)
- `torch` - model loading, seeding, autocast, FLOPs hooks, device handling
- `transformers` - fallback model loading; safetensors toggling (`pipeline/dnallmmark_pipeline.py:941-945`)

**Critical (Python, scripts):**
- `numpy` - used in both `pipeline/dnallmmark_pipeline.py` and `script/summarize_comparison.py`
- `pandas` - used only in `script/summarize_comparison.py:77`
- `script/get_task_performance.py` is stdlib-only (`os`, `json`)

**Critical (JavaScript, browser):**
- Chart.js 4.4.0 via jsDelivr CDN (`https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`, loaded in `dnallm-mark/index.html:18`, `task.html:20`, `task-mockup.html:13`) — scatter chart in `dnallm-mark/js/main.js:342`, bar chart in `dnallm-mark/js/task.js:413`
- SheetJS (xlsx) 0.18.5 via jsDelivr CDN (`https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js`, loaded in `index.html:21`, `task.html:23`, `finetuning.html:13`) — used for spreadsheet export

**Infrastructure:**
- None. No database, no message queue, no container runtime, no CI config detected.

## Configuration

**Environment:**
- No `.env` files. Optional cache-location env vars exist but are commented out: `HF_HOME`, `MS_CACHE_HOME` (`pipeline/dnallmmark_pipeline.py:3-5`)
- All runtime configuration is file-based:
  - `pipeline/models_info.json` - registry of 41 benchmarked models (name, size, tokenizer, architecture, HuggingFace/ModelScope IDs)
  - `pipeline/datasets_info.json` - registry of 50 benchmark datasets (path, split sizes, task type, metric)
  - `dnallm-mark/js/config.js` - frontend CONFIG object (arenas, nav links, table options, scatter axes, reserved `API.BASE_URL`)

**Build:**
- No build configs (no `tsconfig.json`, no bundler, no lint/format configs detected)

**Pipeline CLI arguments** (`pipeline/dnallmmark_pipeline.py:710-747`):
- `--target_model`, `--target_dataset` (comma-separated), `--batch_size`, `--fix_token_len`, `--max_token_len`, `--remove_pt`, `--remove_checkpoints`, `--seed` (default 9527)

**Training hyperparameters:**
- `pipeline/finetune_config.yaml` - default TrainingArguments-style config (3 epochs, lr 2e-5, bf16, tensorboard)
- `pipeline/finetune_config_with_head.yaml` - variant adding `task.head_config` (MLP/CNN/LSTM/U-Net custom heads) for `special_models` = `["evo2_1b_base", "megaDNA_updated"]` (`pipeline/dnallmmark_pipeline.py:1339`)

## Platform Requirements

**Development:**
- Data chain: `uv venv .venv --python 3.13 && uv sync` (repo-local venv; pandas/numpy from the committed lockfile)
- Pipeline: `dnallm`, `torch`, `transformers` installed manually (`uv sync --group pipeline` + dnallm from the local dev clone in Phase 3)
- Any static file server for the web UI (`python3 -m http.server` or `npx http-server`)
- Internet access at runtime for CDN scripts (Chart.js, xlsx) — the UI breaks offline

**Production:**
- None configured. Static hosting for `dnallm-mark/` is implied (GitHub Pages-style); the fine-tuning pipeline targets a single CUDA GPU workstation with models in `pipeline/models/` and datasets in `pipeline/datasets/` (both gitignored, downloaded externally)

## Notable Implementation Details

- **FLOPs measurement is custom**: `FlopsCounter` (`pipeline/dnallmmark_pipeline.py:24-150`) registers per-layer forward hooks with class-name dispatch for many attention/SSM architectures (Bert, Mistral, Llama/Gemma GQA, BigBird, Hyena, Mamba/Mamba2, Caduceus, Enformer, Borzoi, MegaDNA); results saved to `flops_report.json` per run
- **Dynamic batch sizing**: `determine_batch_size()` scales the initial batch size down by sequence-length tier (`pipeline/dnallmmark_pipeline.py:772-795`)
- **Model special-case lists** are hardcoded at the bottom of the pipeline (`pipeline/dnallmmark_pipeline.py:1303-1339`): `model_not_use_safetensors`, `deeplearning_models`, `models_no_char_n`, `models_with_limited_length`, `models_only_support_fp32`, `special_models`
- **Resume behavior**: a dataset run is skipped if `trainer_state.json` already exists in the output dir (`pipeline/dnallmmark_pipeline.py:1013-1014`)

---

*Stack analysis: 2026-10-08*
