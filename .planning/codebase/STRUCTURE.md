---
last_mapped_commit: a44d3104b8ab1e04ddbebed75446772fc0ca3f1b
last_mapped_at: 2026-10-08
---
# Codebase Structure

**Analysis Date:** 2026-10-08

## Directory Layout

```
dnallmmark/                       # Repository root
├── README.md                     # Main docs: setup, pipeline usage, data format, project structure
├── start-server.sh               # Executable launcher: serves dnallm-mark/ on http://localhost:8080
├── .gitignore                    # Ignores pipeline/datasets, pipeline/models, pipeline/finetuned, .planning/, etc.
├── pyproject.toml                # PEP 621 + PEP 735 dependency groups (data/dev/pipeline) — plan 01-01
├── uv.lock                       # Committed uv lockfile (exact resolution, single numpy/pandas pin)
├── requirements.txt              # Generated: uv export of the data group (exact pins + hashes)
├── .python-version               # Single line "3.13" — contributor interpreter pin (D-07)
├── baseline/                     # Pre-fix data baseline tooling (plan 01-01)
│   ├── compare.py                # Order-insensitive JSON value comparator (--summary-json machine mode)
│   ├── data-v1.sha256            # SHA256 manifest of the 52 derived outputs at tag data-v1
│   └── PIN-VALIDATION.md         # Empirical pin-validation evidence (D-05/D-06)
├── benchmark/
│   └── demo.png                  # Leaderboard screenshot used in README
├── dnallm-mark/                  # Static web leaderboard (the deployable site)
│   ├── README.md                 # Frontend-local notes (design system origin, feature checklist)
│   ├── index.html                # Main leaderboard page (scatter + table)
│   ├── task.html                 # Per-task benchmark page (bar chart + table + loading overlay)
│   ├── finetuning.html           # Fine-tuning results table page
│   ├── models.html               # Model cards table page
│   ├── datasets.html             # Dataset catalog table page
│   ├── task-mockup.html          # Dev mockup for task page (standalone, not linked)
│   ├── test.html                 # Dev test page (standalone)
│   ├── verify-chart.html         # Dev chart verification page (standalone)
│   ├── css/                      # Stylesheets (styles.css is the @import entry)
│   ├── js/                       # ES modules, one controller per page + shared modules
│   └── data/                     # Committed JSON consumed by the UI
│       ├── model_performance/    # INPUT (42 files): {model}_performance.json
│       ├── task_performance/     # GENERATED (47 files): {dataset}_task_performance.json
│       ├── models_comparison.json            # GENERATED: overall leaderboard
│       ├── models_comparison_{animal,plant,microbe}.json  # GENERATED: per-species arenas
│       └── tasks.json            # GENERATED: lightweight task index (id, species, metric, fileName)
├── pipeline/                     # Fine-tuning pipeline (Python, GPU)
│   ├── dnallmmark_pipeline.py    # Main script (1341 lines): FlopsCounter + model×dataset loop
│   ├── finetune_config.yaml      # Default training config (HF TrainingArguments subset)
│   ├── finetune_config_with_head.yaml  # Config with custom head (MLP/CNN/LSTM/U-Net options)
│   ├── models_info.json          # Registry of 41 models (41 entries: name, size, tokenizer, links)
│   ├── datasets_info.json        # Registry of 50 datasets (path, splits, type, labels, length, metric)
│   ├── models/                   # NOT COMMITED (gitignored) — pretrained model weights
│   ├── datasets/                 # NOT COMMITED (gitignored) — benchmark datasets (download from Zenodo)
│   ├── finetuned/                # NOT COMMITED (gitignored) — outputs incl. {model}_performance.json
│   └── logs/                     # NOT COMMITED (gitignored) — {model}_error_log.txt
├── script/                       # Python data-processing scripts (singular "script")
│   ├── summarize_comparison.py   # model_performance/ → models_comparison*.json
│   └── get_task_performance.py   # model_performance/ → task_performance/
└── scripts/                      # Node data-processing scripts (plural "scripts" — inconsistent with script/)
    └── generate-tasks-index.js   # task_performance/ → tasks.json
```

## Directory Purposes

**`dnallm-mark/`:**
- Purpose: The complete deployable website; pure HTML/CSS/JS with zero build step
- Contains: 5 production HTML pages, 3 dev/mockup HTML pages, `css/`, `js/`, `data/`
- Key files: `index.html`, `task.html`, `js/main.js`, `js/task.js`, `js/task-loader.js`, `js/data.js`, `js/config.js`

**`dnallm-mark/js/`:**
- Purpose: One ES-module page controller per page plus two shared modules
- Contains: `config.js` (constants), `data.js` (DataAPI fetch/cache), `main.js`, `task.js`, `task-loader.js`, `finetuning.js`, `models.js`, `datasets.js`, `submit.js` (orphaned — no `submit.html`)
- Shared modules: always import `CONFIG` from `./config.js` and `DataAPI` from `./data.js`; do not duplicate config constants inside page modules

**`dnallm-mark/css/`:**
- Purpose: Layered stylesheet system
- Contains: `styles.css` (entry — `@import`s the rest), `variables.css` (design tokens + Google Fonts import), `reset.css`, `typography.css`, `layout.css`, `components.css` (largest, 770 lines), `charts.css`, `task.css` + `loading.css` (task-page only)
- Key files: new page styles belong in a new `{page}.css` imported from the page's HTML (like `task.html` does), not appended to `components.css`

**`dnallm-mark/data/`:**
- Purpose: The only data source for the UI; committed to git
- Contains: `model_performance/` (input layer), `task_performance/`, `tasks.json`, `models_comparison*.json` (all generated)
- Key files: adding a model means adding `model_performance/{model}_performance.json` then regenerating the derived files

**`pipeline/`:**
- Purpose: GPU fine-tuning benchmark runner
- Contains: main script, two YAML configs, two JSON registries; `models/`, `datasets/`, `finetuned/`, `logs/` exist only at runtime (gitignored)
- Key files: `dnallmmark_pipeline.py`, `models_info.json`, `datasets_info.json`

**`script/` and `scripts/`:**
- Purpose: Offline JSON transformation scripts (Python in `script/`, Node in `scripts/`)
- Note the inconsistent naming (singular vs plural) — both exist; Python scripts go in `script/`, Node scripts in `scripts/` to match current convention

**`baseline/`:**
- Purpose: Pre-fix derived-data baseline tooling (plan 01-01, AUDIT-02/REL-02) — comparator, SHA256 manifest, pin-validation evidence
- Contains: `compare.py` (order-insensitive JSON value comparator; exit 0/1/2; `--summary-json` emits the complete untruncated diff inventory consumed by the plan 01-03 migration gate), `data-v1.sha256` (52 entries), `PIN-VALIDATION.md`
- Key relation: annotated git tag `data-v1` freezes the byte state; recover any file via `git show data-v1:<path>` and verify with the manifest

## Key File Locations

**Entry Points:**
- `dnallm-mark/index.html`: main leaderboard (default page)
- `pipeline/dnallmmark_pipeline.py`: benchmark CLI (`python dnallmmark_pipeline.py --target_model X --batch_size N`, run from `pipeline/`)
- `start-server.sh`: local dev server (port 8080)
- `script/summarize_comparison.py`, `script/get_task_performance.py`: run with CWD = `dnallm-mark/data/`
- `scripts/generate-tasks-index.js`: path-independent (resolves from `__dirname`)

**Configuration:**
- `dnallm-mark/js/config.js`: app constants — arenas, filters, nav links, scatter axes
- `pipeline/finetune_config.yaml`: default training hyperparameters (epochs 3, lr 2e-5, bf16 True, tensorboard reporting)
- `pipeline/finetune_config_with_head.yaml`: same, plus `task.head_config` for custom heads (used for `evo2_1b_base`, `megaDNA_updated`)
- `pipeline/models_info.json`: model registry — required fields: `name`, `size (M)`, `type`, `tokenizer`, `mean_token_len`, `architecture`, `series`, `context_len (bp)`, `species`, `huggingface`, `modelscope`
- `pipeline/datasets_info.json`: dataset registry — fields: `Dataset_path`, `Train`, `Test`, `Dev`, `type`, `labels`, `length`, `metric`

**Core Logic:**
- `pipeline/dnallmmark_pipeline.py`: `FlopsCounter` (lines 24-689), `determine_batch_size` (772), `main()` model×dataset loop (798-1291), model whitelists (1303-1339)
- `dnallm-mark/js/main.js`: scatter chart + leaderboard rendering
- `dnallm-mark/js/task-loader.js`: two-tier task cache with retry/preload
- `script/summarize_comparison.py`: `calculate_dataset_stats` (rank/minmax/zscore/robust), `aggregate_models`, `to_singular_species`

**Testing:**
- No automated test suite. Closest artifacts are manual dev pages: `dnallm-mark/test.html`, `dnallm-mark/verify-chart.html`, `dnallm-mark/task-mockup.html`, and the `window.DNALLMDebug` console API (`js/task-loader.js:364-405`)

## Naming Conventions

**Files:**
- HTML pages: lowercase, hyphenated, page-purpose names — `index.html`, `task.html`, `task-mockup.html`
- JS modules: lowercase, hyphenated, matching their page — `task.html` ↔ `js/task.js`, `task-loader.js`; shared modules are single words (`config.js`, `data.js`)
- CSS: single lowercase word per concern — `variables.css`, `layout.css`, `charts.css`
- Data (model layer): `{model_name}_performance.json`, model names lowercase-hyphenated or with underscores from upstream HF ids (e.g. `caduceus-ph_seqlen-131k_d_model-256_n_layer-16_performance.json`)
- Data (task layer): `{DatasetName}_task_performance.json`, dataset names use `Source__task` double-underscore convention (e.g. `GUE__emp_H3`, `PDLLMs_datasets__plant-multi-species-core-promoters`)
- Comparison outputs: `models_comparison.json`, `models_comparison_{species-singular}.json`
- Pipeline logs: `{model_name}_error_log.txt`

**Directories:**
- All lowercase; frontend plurals for asset dirs (`css/`, `js/`, `data/`); note `script/` vs `scripts/` split by language

**Code identifiers:**
- JS: classes in PascalCase with per-page suffix (`DNALLMMark`, `TaskBenchmark`, `FineTuningPage`, `ModelsPage`, `DatasetsPage`, `SubmitPage`, `TaskLoader`, `LoadingController`); methods camelCase following the `render*` / `bindEvents` / `handle*Change` / `loadData` / `setup` vocabulary
- Python: module-level functions snake_case (`parse_args`, `set_seed`, `determine_batch_size`, `calculate_dataset_stats`); class `FlopsCounter` PascalCase
- JSON keys: lowercase snake_case for metrics (`rank_score`, `sum_PFLOPs`, `top3_count`); model-card keys keep human-readable forms with units in parentheses (`size (M)`, `context_len (bp)`) — preserve these exact keys; the UI reads them literally

## Where to Add New Code

**New leaderboard page (e.g. an "about" page):**
- HTML shell: `dnallm-mark/{page}.html` — copy `datasets.html` as the template: static `<nav class="navbar">`, `<div class="hero-container">`, one content container (e.g. `.about-container`), `<script type="module" src="./js/{page}.js">`
- Controller: `dnallm-mark/js/{page}.js` — follow the class pattern (`constructor` → `init` → `setup` → `loadData` → `render*` → `bindEvents`), import `CONFIG` and/or `DataAPI`, instantiate once at the bottom
- Navigation: add `{ name, url }` to `CONFIG.NAV_LINKS` in `js/config.js` — and update the static navbar in every existing HTML page (navbars are hardcoded per page, not rendered from CONFIG; see ARCHITECTURE.md anti-patterns)
- Styles: new `css/{page}.css` linked from the page HTML; use tokens from `css/variables.css`

**New benchmark model:**
- Add an entry to `pipeline/models_info.json` (all fields; unknown values may be blank)
- Place weights under `pipeline/models/{model_name}/`
- If the model has quirks (fp32-only, no safetensors, character-set restrictions, custom head), add its name to the relevant whitelist in `pipeline/dnallmmark_pipeline.py:1303-1339`
- Run the pipeline; copy `finetuned/{model}/{model}_performance.json` into `dnallm-mark/data/model_performance/`
- Regenerate derived data (from `dnallm-mark/data/`): `python ../../script/get_task_performance.py`, `python ../../script/summarize_comparison.py`, `node ../../scripts/generate-tasks-index.js`

**New benchmark dataset:**
- Add an entry to `pipeline/datasets_info.json` (`Dataset_path` relative to `pipeline/`, plus `Train`/`Test`/`Dev` counts, `type`, `labels`, `length`, `metric`); data must be `train.csv`/`dev.csv`/`test.csv` with `sequence` and `label` columns (see `pipeline/dnallmmark_pipeline.py:948-954, 1021-1027`)
- Rerun pipeline for target models and regenerate derived data as above

**New metric or aggregation change:**
- Aggregation: `script/summarize_comparison.py` (`calculate_dataset_stats`, `aggregate_models`, `metric_key_map`)
- Metric display names/labels: `formatMetricName` map in `dnallm-mark/js/task.js:226-244`
- Ascending (lower-is-better) metric set: `ascendingMetrics` in `js/task.js:109-111`
- Scatter axes constants: `CONFIG.SCATTER_CONFIG` in `js/config.js:83-98`

**Utilities:**
- Shared frontend helpers (colors, species mapping, fetching): `dnallm-mark/js/data.js`
- Shared constants: `dnallm-mark/js/config.js`
- Offline JSON transforms: `script/` (Python) or `scripts/` (Node)

## Special Directories

**`dnallm-mark/data/model_performance/`:**
- Purpose: Hand-maintained input layer of the whole data pipeline; each file is one model's results across all datasets
- Generated: No (source of truth; produced by the pipeline, then copied in)
- Committed: Yes

**`dnallm-mark/data/task_performance/`, `tasks.json`, `models_comparison*.json`:**
- Purpose: Derived views for the task page and leaderboards
- Generated: Yes — by `script/get_task_performance.py`, `scripts/generate-tasks-index.js`, `script/summarize_comparison.py`
- Committed: Yes (regenerate after any `model_performance/` change)

**`pipeline/models/`, `pipeline/datasets/`, `pipeline/finetuned/`, `pipeline/logs/`:**
- Purpose: Pipeline runtime inputs (weights, datasets from Zenodo) and outputs (checkpoints, metrics, master performance JSON, error logs)
- Generated: Yes (populated by downloads/training)
- Committed: No (gitignored via `models/`, `datasets/`, `finetuned/`, `logs/` patterns in `.gitignore`)

**`.planning/`:**
- Purpose: GSD planning artifacts including these codebase docs
- Generated: Yes
- Committed: No (gitignored)

---

*Structure analysis: 2026-10-08*
