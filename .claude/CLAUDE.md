<!-- GSD:project-start source:PROJECT.md -->

## Project

**DNALLM-Mark**

DNALLM-Mark is a DNA language-model benchmark platform: a PyTorch fine-tuning pipeline that evaluates 41 DNA LLMs across 50 datasets (with custom FLOPs instrumentation), offline Python/Node scripts that aggregate results, and a static multi-page leaderboard website. The current milestone is a **systematic review and hardening pass** over the existing codebase to prepare it for public release: audit all three subsystems, fix confirmed issues, and add regression prevention (data-script tests + CI).

**Core Value:** Every number on the public leaderboard is correct and reproducible from code that external reviewers can trust.

### Constraints

- **Tech stack**: Keep vanilla ES-module JS (no build step, no framework) and Python — public release must not change the architecture
- **Hosting model**: Static files only — no backend or API may be introduced
- **Reproducibility**: Fixes may change aggregated numbers (e.g. species-grouping fix); recomputation is allowed and expected, each change documented with before/after comparison
- **CI feasibility**: GitHub Actions must not require GPU or the external `dnallm` package — test scope limited to stdlib/numpy/pandas scripts and static checks
- **Fix discipline**: Surgical fixes only; no opportunistic refactors that widen review surface

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.11+ - Fine-tuning pipeline (`pipeline/dnallmmark_pipeline.py`) and data-processing scripts (`script/summarize_comparison.py`, `script/get_task_performance.py`)
- JavaScript (ES6 modules, no framework, no build step) - Web leaderboard UI (`dnallm-mark/js/*.js`)
- HTML/CSS - Static pages (`dnallm-mark/*.html`, `dnallm-mark/css/*.css`)
- Bash - Local server launcher (`start-server.sh`)
- YAML - Training configuration (`pipeline/finetune_config.yaml`, `pipeline/finetune_config_with_head.yaml`)
- Node.js (plain `fs`/`path`, no deps) - One-off index generator (`scripts/generate-tasks-index.js`)

## Runtime

- Python 3.11+ required (per `README.md` badge); GPU with CUDA expected for pipeline training (`torch.cuda.manual_seed_all` at `pipeline/dnallmmark_pipeline.py:752`, bf16 autocast at `pipeline/dnallmmark_pipeline.py:1095`)
- Node.js 18+ optional (only needed for `npx http-server` fallback in `start-server.sh:20-22`)
- None declared. No `requirements.txt`, `pyproject.toml`, `package.json`, or lockfiles exist in the repo. Install `dnallm`, `torch`, `transformers`, `numpy`, `pandas` manually.

## Frameworks

- None for the web UI — pure HTML/CSS/ES-module JavaScript, served as static files (no React/Vue/bundler)
- DNALLM (external, https://github.com/zhangtaolab/DNALLM) - DNA LLM finetuning framework wrapping Hugging Face; imported at `pipeline/dnallmmark_pipeline.py:18` as `from dnallm import DNADataset, load_config, load_model_and_tokenizer, DNATrainer`
- PyTorch (`torch`, `torch.nn`) - model training, FLOPs instrumentation via forward hooks (`pipeline/dnallmmark_pipeline.py:16-17`, `FlopsCounter` at line 24)
- Hugging Face Transformers - lazy fallback loader (`AutoConfig`/`AutoModelForSequenceClassification`/`AutoTokenizer` with `trust_remote_code=True`, `pipeline/dnallmmark_pipeline.py:880-898`); training args follow the `transformers.TrainingArguments` schema
- Not detected. No test framework, no test files anywhere in the repo.
- No build step. Development server: `bash start-server.sh` (runs `python3 -m http.server 8080` from `dnallm-mark/`, `start-server.sh:13-22`)
- TensorBoard for training metrics: `report_to: "tensorboard"` in both YAML configs; view via `tensorboard --logdir=finetuned/` (per `README.md:179`)

## Key Dependencies

- `dnallm` - external framework providing `DNADataset`, `DNATrainer`, `load_config`, `load_model_and_tokenizer`; the entire training loop is delegated to it (`pipeline/dnallmmark_pipeline.py:1144-1193`)
- `torch` - model loading, seeding, autocast, FLOPs hooks, device handling
- `transformers` - fallback model loading; safetensors toggling (`pipeline/dnallmmark_pipeline.py:941-945`)
- `numpy` - used in both `pipeline/dnallmmark_pipeline.py` and `script/summarize_comparison.py`
- `pandas` - used only in `script/summarize_comparison.py:77`
- `script/get_task_performance.py` is stdlib-only (`os`, `json`)
- Chart.js 4.4.0 via jsDelivr CDN (`https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`, loaded in `dnallm-mark/index.html:18`, `task.html:20`, `task-mockup.html:13`) — scatter chart in `dnallm-mark/js/main.js:342`, bar chart in `dnallm-mark/js/task.js:413`
- SheetJS (xlsx) 0.18.5 via jsDelivr CDN (`https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js`, loaded in `index.html:21`, `task.html:23`, `finetuning.html:13`) — used for spreadsheet export
- None. No database, no message queue, no container runtime, no CI config detected.

## Configuration

- No `.env` files. Optional cache-location env vars exist but are commented out: `HF_HOME`, `MS_CACHE_HOME` (`pipeline/dnallmmark_pipeline.py:3-5`)
- All runtime configuration is file-based:
- No build configs (no `tsconfig.json`, no bundler, no lint/format configs detected)
- `--target_model`, `--target_dataset` (comma-separated), `--batch_size`, `--fix_token_len`, `--max_token_len`, `--remove_pt`, `--remove_checkpoints`, `--seed` (default 9527)
- `pipeline/finetune_config.yaml` - default TrainingArguments-style config (3 epochs, lr 2e-5, bf16, tensorboard)
- `pipeline/finetune_config_with_head.yaml` - variant adding `task.head_config` (MLP/CNN/LSTM/U-Net custom heads) for `special_models` = `["evo2_1b_base", "megaDNA_updated"]` (`pipeline/dnallmmark_pipeline.py:1339`)

## Platform Requirements

- Python 3.11+ with `dnallm`, `torch`, `transformers`, `numpy`, `pandas` installed manually
- Any static file server for the web UI (`python3 -m http.server` or `npx http-server`)
- Internet access at runtime for CDN scripts (Chart.js, xlsx) — the UI breaks offline
- None configured. Static hosting for `dnallm-mark/` is implied (GitHub Pages-style); the fine-tuning pipeline targets a single CUDA GPU workstation with models in `pipeline/models/` and datasets in `pipeline/datasets/` (both gitignored, downloaded externally)

## Notable Implementation Details

- **FLOPs measurement is custom**: `FlopsCounter` (`pipeline/dnallmmark_pipeline.py:24-150`) registers per-layer forward hooks with class-name dispatch for many attention/SSM architectures (Bert, Mistral, Llama/Gemma GQA, BigBird, Hyena, Mamba/Mamba2, Caduceus, Enformer, Borzoi, MegaDNA); results saved to `flops_report.json` per run
- **Dynamic batch sizing**: `determine_batch_size()` scales the initial batch size down by sequence-length tier (`pipeline/dnallmmark_pipeline.py:772-795`)
- **Model special-case lists** are hardcoded at the bottom of the pipeline (`pipeline/dnallmmark_pipeline.py:1303-1339`): `model_not_use_safetensors`, `deeplearning_models`, `models_no_char_n`, `models_with_limited_length`, `models_only_support_fp32`, `special_models`
- **Resume behavior**: a dataset run is skipped if `trainer_state.json` already exists in the output dir (`pipeline/dnallmmark_pipeline.py:1013-1014`)

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- JS page modules: lowercase singular noun matching their page — `js/main.js`, `js/models.js`, `js/datasets.js`, `js/task.js`, `js/submit.js`, `js/finetuning.js`
- JS utility modules: lowercase role name — `js/config.js`, `js/data.js`, `js/task-loader.js`
- CSS: lowercase role name — `css/variables.css`, `css/layout.css`, `css/components.css`, `css/charts.css`, `css/reset.css`, `css/typography.css`, `css/loading.css`, `css/task.css`
- Python: `snake_case.py` — `script/summarize_comparison.py`, `script/get_task_performance.py`, `pipeline/dnallmmark_pipeline.py`
- HTML pages: lowercase flat files in `dnallm-mark/` root — `index.html`, `task.html`, `finetuning.html`, `models.html`, `datasets.html`
- JavaScript: `camelCase` — `loadModelsComparisonByArena()`, `filterAndSortModels()`, `renderScatterChart()`, `bindEvents()`, `fetchWithRetry()`
- Private-ish methods prefixed `_` in Python classes — `_register_hooks()`, `_linear_hook()` in `pipeline/dnallmmark_pipeline.py`
- Python: `snake_case` — `calculate_dataset_stats()`, `aggregate_models()`, `to_singular_species()`, `determine_batch_size()`
- Render methods: `renderX()` (`renderHero()`, `renderNavbar()`, `renderLeaderboard()`); lifecycle: `init()`, `setup()`, `loadData()`
- `camelCase` in JS (`currentArena`, `filteredModels`, `modelPerformance`)
- `snake_case` in Python (`dataset_stats_map`, `raw_dataset_flops`, `master_performance_dict`)
- Constants: `UPPER_SNAKE_CASE` in JS (`CONFIG.APP_NAME`, `CONFIG.NAV_LINKS`) and module-level `const` in Node (`TASK_PERFORMANCE_DIR` in `scripts/generate-tasks-index.js`)
- `PascalCase` — `DNALLMMark` (`js/main.js`), `ModelsPage` (`js/models.js`), `DatasetsPage` (`js/datasets.js`), `FineTuningPage` (`js/finetuning.js`), `SubmitPage` (`js/submit.js`), `TaskLoader` + `LoadingController` (`js/task-loader.js`, `js/task.js`), `FlopsCounter` (`pipeline/dnallmmark_pipeline.py`)
- No TypeScript. JSDoc annotations on most JS methods provide the type documentation.
- Data "contracts" are the JSON schemas documented in `README.md` and script docstrings (`info` / `performance` / `dataset` / `parameters` keys), not code types.

## Code Style

- No formatter configured (no `.prettierrc`, no `biome.json`, no `pyproject.toml`, no `setup.cfg`). Style is hand-maintained.
- JS: 2-space indent, single quotes, semicolons, trailing commas in multiline literals.
- Python: 4-space indent, double quotes for strings in `script/` files, follows ~PEP 8 but not enforced.
- CSS: 2-space indent, one declaration per line, lowercase hex colors.
- None. No `.eslintrc*`, `eslint.config.*`, ruff/flake8/pylint config. (`.gitignore` mentions `.ruff_cache/` and `.pytest_cache/` but these are inherited from the upstream dnallm project — no such config exists here.)

## Frontend Module Pattern (the core convention)

- Build HTML strings with template literals and inject via `container.innerHTML = html`.
- Each dynamic region has an empty container div in the HTML page (`.navbar-container`, `.hero-container`, `.leaderboard-container`, `.category-nav-container`) — `js/main.js:89-116`.
- Always null-guard the container: `const el = document.querySelector(...); if (!el) return;`
- Bind in a `bindEvents()` method at the end of setup.
- Use event delegation on `document` for buttons that get re-rendered: `document.addEventListener('click', (e) => { const btn = e.target.closest('button[data-filter]'); ... })` — `js/main.js:477-486`.
- Use `e.target.closest('.selector')` to find the clicked element.
- Optional-chaining listener binding: `document.getElementById('x')?.addEventListener(...)` — `js/main.js:453`, `js/submit.js:288`.
- Single `this.state` object per class; never scatter properties on `this`.
- Data access always goes through `DataAPI` (`js/data.js`) which memoizes fetched JSON in `DataAPI.cache`.
- Default defensive reads: `model.performance?.rank_score || 0`, `data.model?.['size (M)'] || 0`.

## External Libraries (frontend)

- Loaded as CDN `<script>` tags in each HTML `<head>` — **no npm**:
- Page module loaded at end of body: `<script type="module" src="./js/main.js"></script>`
- Google Fonts imported in CSS: `@import url('https://fonts.googleapis.com/...')` — `css/variables.css:6`

## CSS Conventions

- Entry file `css/styles.css` `@import`s the others in order: variables → reset → typography → layout → components → charts. Add new files there.
- All colors/fonts/spacing via CSS custom properties defined in `css/variables.css` (`--color-primary: #292C33`, `--color-accent-teal: #265354`, `--font-body`, `--breakpoint-md`, ...). Do not hardcode hex values in components; use `var(--color-*)`.
- Flat hyphenated class names (not strict BEM): `.arena-table`, `.model-info`, `.btn-primary`, `.modal-overlay`, `.empty-state-icon`, `.rank-badge`.
- Responsive rules use `@media (max-width: var(--breakpoint-md))`; print styles in `css/styles.css`.
- Page-specific styles get their own file (`css/task.css`, `css/loading.css`).

## Python Conventions (script/)

- Large module docstring at top: purpose, input/output JSON structures, usage command, `See also:` cross-references to sibling scripts.
- Google-style docstrings on every function (`Args:`, `Returns:`) with RST double-backtick markup.
- `main()` function with a `# ===== Configuration =====` block at the top holding `input_dir` / `output_dir` constants; guard `if __name__ == "__main__": main()`.
- Scripts are **CWD-sensitive**: run from `dnallm-mark/data/` (`python ../../script/summarize_comparison.py`). Relative paths like `model_performance` resolve against CWD, not the script location.
- JSON I/O: `open(path, 'r', encoding='utf-8')` / `json.dump(..., indent=4, ensure_ascii=False)`.
- Defensive metric parsing via helpers like `get_float(val, default=0.0)` (`script/summarize_comparison.py:80-96`) — treat `""` and `None` as missing.
- Per-file try/except with `print(f"  [Skip] Failed to read file {filename}: {e}"); continue` for malformed inputs (`script/get_task_performance.py:105-110`).
- Friendly console output with emoji markers: `print(f"✅ Global comparison results saved to: {output_total}")`.

## Python Conventions (pipeline/)

- `FlopsCounter` class registers PyTorch forward hooks; each `_xxx_hook(name)` method is a **closure factory** returning `def hook(module, inputs, outputs)` (`pipeline/dnallmmark_pipeline.py:170-181`).
- Architecture-specific dispatch via classname string lists and `model_path` substring checks (`pipeline/dnallmmark_pipeline.py:61-150`).
- CLI via `argparse` (`parse_args()`, line 707): `--target_model`, `--target_dataset`, `--batch_size`, `--fix_token_len`, `--max_token_len`, `--remove_pt`, `--remove_checkpoints`, `--seed`.
- Logging: plain `print()` prefixed with `[YYYY-MM-DD HH:MM:SS]` from `get_current_time()` (line 767); errors additionally written to `./logs/{model_name}_error_log.txt` via `print(..., file=error_log)`.
- Error strategy in the model/dataset loops: `try/except Exception` → log to console + error log file → `continue` to next dataset / `break` out of model (`pipeline/dnallmmark_pipeline.py:884-901`, `1287-1294`).
- Model-behavior registries (plain lists/dicts keyed by model name: `special_models`, `deeplearning_models`, `models_only_support_fp32`, `model_not_use_safetensors`) are defined **inside the `if __name__ == "__main__":` block** (lines 1294-1339) along with `base_dir = "./"` and loading of `datasets_info.json` / `models_info.json`. New model quirks get added to these lists.
- Config-driven: hyperparameters live in `pipeline/finetune_config.yaml` (and `finetune_config_with_head.yaml` for custom-head models), loaded via `load_config()` from the `dnallm` package.
- Resume-safe by convention: `if os.path.exists(outdir + "trainer_state.json"): continue` (line ~1002).
- Output contract: writes `finetuned/{model}/{model}_performance.json` with the exact `info` / `performance.{dataset}.{dataset,parameters,performance}` schema consumed by the frontend and `script/` tools (`pipeline/dnallmmark_pipeline.py:1195-1265`).

## Import Organization

## Error Handling

- Fetch wrapper (frontend standard): check `response.ok`, `throw new Error(\`Failed to load ${fileName}: ${response.status}\`)`, `catch` → `console.error` → re-throw — `js/data.js:39-50`.
- Retry with exponential backoff in `TaskLoader.fetchWithRetry()` (`js/task-loader.js:81-113`) — 3 attempts, linear delay multiplier.
- Page-level catch-all in `setup()` that logs and leaves the page partially rendered — `js/main.js:46-48`.
- Client-side form validation via Promise wrapper around `FileReader` with per-check rejection messages — `SubmitPage.validateJSON()` (`js/submit.js:171-206`).
- Python scripts: per-file skip-on-error loops; pipeline: log-and-continue per dataset, log-and-break per model.

## Logging

- Lifecycle chatter: `console.log('Setting up DNALLM Mark...')` / '... setup complete!' in every page's `setup()`.
- Tagged prefix for subsystems: `` console.log(`[TaskLoader] Initialized with ${n} tasks`) `` — `js/task-loader.js`.
- Timestamped prefix in pipeline: `print(f"[{current_time}] Loading model: {model_name}")`.
- Browser debug API exposed as global `window.DNALLMDebug` (`cacheStats()`, `clearCache()`, `clearTask(id)`, `preload(id)`, `tasks()`) — `js/task-loader.js:353-413`. New cache/loading subsystems should expose similar console helpers.

## Comments

- Section banners with `/* ===== */` or `# =====` blocks at file/section tops (every JS/CSS/Python file).
- JSDoc on every non-trivial public method (`@param {string} arena - 'all', 'animal'...`, `@returns {Promise<Object>}`) — `js/data.js`, `js/task-loader.js`.
- Python docstrings explain *why* (normalization rationale, skip conditions), including inline `#` comments for numeric formulas (rank score `N - rank`, FLOPs scaling, `pipeline/dnallmmark_pipeline.py:1063-1076`).
- Comments are **bilingual English/Chinese** — several file headers and inline notes are in Chinese (`js/submit.js:3` "数据提交页面", `css/variables.css:2` "精确提取自源码", `js/main.js:476` event-delegation note). Either language is acceptable; match the surrounding file.

## Function Design

## Module Design

- `CONFIG` (`js/config.js`) — app-wide constants: arenas, nav links, sort/filter options, scatter-chart config. Add page constants here, not inline.
- `DataAPI` (`js/data.js`) — single data layer for all pages; cache-aware; also holds small pure helpers (`normalizeToArena()`, `getColorForModel()` with the 15-color palette at `js/data.js:173-177`).

## Data Conventions

- Model alias = filename without `_performance.json` (`plant-dnabert-6mer_performance.json` → `plant-dnabert-6mer`); derived consistently in `js/data.js:241`, `script/get_task_performance.py:119`, `script/summarize_comparison.py:319`.
- Missing metrics are empty strings `""`, not `null` or `0` — every consumer must use `get_float()`-style coercion (`script/summarize_comparison.py:351-361`).
- Filenames sanitized by replacing `/` and `\` with `_` (`script/get_task_performance.py:155`, `script/summarize_comparison.py:405`).
- Species labels normalized to singular lowercase for filenames (`to_singular_species()`, `script/summarize_comparison.py:164-184`).

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Main leaderboard page | Scatter chart (FLOPs vs Rank Score) + sortable leaderboard table, arena switching | `dnallm-mark/js/main.js` |
| Task benchmark page | Per-task model ranking, metric dropdown, bar chart, loading overlay | `dnallm-mark/js/task.js` |
| Task data loader | LRU memory + localStorage caching, retry with backoff, idle preloading of adjacent tasks | `dnallm-mark/js/task-loader.js` |
| Fine-tuning results page | Model×dataset results table, per-row training-parameter modal | `dnallm-mark/js/finetuning.js` |
| Models page | Model card table (size, tokenizer, architecture, links) | `dnallm-mark/js/models.js` |
| Datasets page | Dataset metadata table aggregated from all model files | `dnallm-mark/js/datasets.js` |
| Submit page (orphaned) | Client-side JSON validation + git PR instruction generator; `submit.html` does not exist | `dnallm-mark/js/submit.js` |
| App configuration | Arena ids, filter options, nav links, chart config constants | `dnallm-mark/js/config.js` |
| Data access | fetch + in-memory cache for comparison/performance JSON, color palette, species→arena mapping | `dnallm-mark/js/data.js` |
| Fine-tuning pipeline | Iterates models×datasets, fine-tunes, measures FLOPs, writes master performance JSON | `pipeline/dnallmmark_pipeline.py` |
| FLOPs measurement | Per-architecture forward-pass hooks (Linear, attention variants, Mamba/SSM, Hyena, Enformer/Borzoi) | `pipeline/dnallmmark_pipeline.py:24-689` (`FlopsCounter`) |
| Comparison aggregation | Per-task rank/minmax/zscore/robust normalization → per-model sums → overall + per-species files | `script/summarize_comparison.py` |
| Task pivot | Model-centric → dataset-centric JSON reorganization | `script/get_task_performance.py` |
| Task index generation | Scans `task_performance/` → lightweight `tasks.json` index | `scripts/generate-tasks-index.js` |
| Local server launcher | `python3 -m http.server 8080` from `dnallm-mark/` (ES modules fail on `file://`) | `start-server.sh` |

## Pattern Overview

- **No build system, no framework, no bundler.** HTML pages load `type="module"` scripts directly; Chart.js 4.4.0 and SheetJS 0.18.5 come from jsdelivr CDN (`dnallm-mark/index.html:18-21`).
- **Page-controller class pattern.** Each page script defines one class, instantiated once at module load (`const app = new DNALLMMark()` at `js/main.js:504`; same in `task.js:590`, `finetuning.js:265`, `models.js:163`, `datasets.js:164`).
- **Shared lifecycle:** `constructor()` → `init()` (waits for DOMContentLoaded) → `setup()` → `loadData()` → `render*()` → `bindEvents()`.
- **Rendering via innerHTML template literals.** No virtual DOM, no templating engine. Event listeners on dynamically rendered content use event delegation bound to `document` (`js/main.js:477-486`).
- **Data as committed static files.** All leaderboard data is fetched from `dnallm-mark/data/`; regeneration is a manual maintainer step, not part of serving.
- **Pipeline is a single monolithic script** with a nested model×dataset loop, module-level config globals, and per-dataset try/except-continue error isolation.

## Layers

- Purpose: Static page shells (navbar, hero container, empty content containers) + styles
- Location: `dnallm-mark/*.html`, `dnallm-mark/css/`
- Contains: One HTML file per page; CSS entry `css/styles.css` imports `variables.css`, `reset.css`, `typography.css`, `layout.css`, `components.css`, `charts.css`; task page adds `css/task.css` + `css/loading.css`
- Depends on: Design tokens in `css/variables.css` (`--color-primary: #292C33` etc.), Google Fonts CDN
- Used by: Page controller scripts that fill `.hero-container`, `.leaderboard-container`, `.models-container`, `.datasets-container`
- Purpose: Page-specific state, data loading, rendering, and event handling
- Location: `dnallm-mark/js/`
- Contains: One class per page plus shared `config.js` and `data.js`
- Depends on: `data.js`, `config.js`, global `Chart` (CDN), `window.taskLoader` / `window.loadingController` on the task page
- Used by: HTML module script tags
- Purpose: Load and cache JSON; derive colors and arena categories
- Location: `dnallm-mark/js/data.js` (DataAPI), `dnallm-mark/js/task-loader.js` (TaskLoader)
- Contains: `DataAPI.loadModelsComparisonByArena/ loadModelsComparison / loadModelPerformance / loadAllModelPerformance`, `TaskLoader.initialize / loadTask / fetchWithRetry / preloadNeighbors`
- Depends on: static files under `dnallm-mark/data/`
- Used by: all page controllers
- Purpose: The single source of truth the UI renders
- Location: `dnallm-mark/data/`
- Contains: `model_performance/` (42 per-model files, hand/pipeline-maintained input), generated `task_performance/` (47 files), generated `tasks.json`, generated `models_comparison{,_animal,_plant,_microbe}.json`
- Depends on: produced offline by `script/` + `scripts/`
- Used by: DataAPI/TaskLoader fetch calls
- Purpose: Regenerate derived JSON from `model_performance/`
- Location: `script/` (Python), `scripts/` (Node)
- Depends on: `model_performance/` input; numpy + pandas for `summarize_comparison.py`
- Used by: maintainers, run manually from `dnallm-mark/data/`
- Purpose: Produce `{model}_performance.json` by fine-tuning each model on each dataset
- Location: `pipeline/dnallmmark_pipeline.py` + `finetune_config.yaml`, `finetune_config_with_head.yaml`, `models_info.json`, `datasets_info.json`
- Depends on: external `dnallm` package (`DNADataset`, `load_config`, `load_model_and_tokenizer`, `DNATrainer` — imported at `pipeline/dnallmmark_pipeline.py:18`), `torch`, `transformers`, local `pipeline/models/` and `pipeline/datasets/` (gitignored, downloaded from Zenodo per `README.md`)
- Used by: benchmark maintainers via CLI

## Data Flow

### Primary Request Path (Main Leaderboard)

### Task Benchmark Flow

### Benchmark Production Flow (Offline)

### Data Regeneration Flow (Offline)

- Each page controller keeps a plain `this.state` object; no shared client state, no router — navigation is full page loads, so state does not survive navigation
- Chart re-render always destroys first: `if (this.state.chart) this.state.chart.destroy()` (`js/main.js:199-201`, `js/task.js:330-332`)
- Cross-module state on the task page uses window globals (`window.taskLoader`, `window.loadingController`) because the two scripts are separate ES modules that cannot import each other's instances
- Pipeline state: `configs` object mutated in-place per dataset (num_labels, batch size, output_dir) and reloaded from YAML per model

## Key Abstractions

- Purpose: Encapsulate one page's state + rendering + events
- Examples: `DNALLMMark` (`js/main.js:9`), `TaskBenchmark` (`js/task.js:96`), `FineTuningPage` (`js/finetuning.js:9`), `ModelsPage` (`js/models.js:9`), `DatasetsPage` (`js/datasets.js:9`), `SubmitPage` (`js/submit.js:8`)
- Pattern: constructor sets `this.state`, calls `init()`; `setup()` runs `loadData → render* → bindEvents` inside try/catch
- Purpose: Single fetch/cache layer + shared presentation helpers (model color palette at `js/data.js:172-179`, species→arena normalization at `js/data.js:149-164`)
- Examples: `dnallm-mark/js/data.js`
- Pattern: plain object literal with module-level `cache` object; default export with CommonJS fallback
- Purpose: Fast task switching without refetching; LRU Map (size 10) + versioned localStorage entries with 24h expiry
- Examples: `dnallm-mark/js/task-loader.js:6`
- Pattern: class instantiated once and exposed as `window.taskLoader`; debug API exposed as `window.DNALLMDebug`
- Purpose: Architecture-aware FLOPs accounting via PyTorch forward hooks
- Examples: `pipeline/dnallmmark_pipeline.py:24`
- Pattern: `_register_hooks()` dispatches on module class name across ~20 attention/SSM variants (HF self-attention, flash attention, GQA, BigBird sparse, ModernBERT windowed, Hyena FFT, Mamba/Mamba2 SSD, Caduceus, Borzoi, Enformer, megaDNA); `save_to_json()` extrapolates per-token FLOPs to the full training run
- Purpose: The schema that couples pipeline → scripts → UI
- Examples: `dnallm-mark/data/model_performance/*_performance.json`
- Pattern: `{ info: {model card}, performance: { {dataset}: { dataset: {...}, parameters: {...}, performance: {metrics incl. FLOPs, runtime} } } }`; dataset names use `Source__task` convention (e.g. `GUE__emp_H3`); primary metric per dataset declared as `dataset.metric` and mapped via `metric_key_map` in `script/summarize_comparison.py:295-305`

## Entry Points

- `dnallm-mark/index.html` — main leaderboard; module script `js/main.js`
- `dnallm-mark/task.html` — task benchmark; module scripts `js/task-loader.js` + `js/task.js`
- `dnallm-mark/finetuning.html` — fine-tuning results; `js/finetuning.js`
- `dnallm-mark/models.html` — model cards; `js/models.js`
- `dnallm-mark/datasets.html` — dataset catalog; `js/datasets.js`
- `dnallm-mark/task-mockup.html`, `test.html`, `verify-chart.html` — standalone dev/mockup artifacts, not linked from navigation
- Location: `pipeline/dnallmmark_pipeline.py`
- Triggers: `python dnallmmark_pipeline.py [--target_model M] [--target_dataset D1,D2] [--batch_size N] [--fix_token_len L] [--max_token_len L] [--remove_pt] [--remove_checkpoints] [--seed S]`
- Responsibilities: fine-tune, evaluate, count FLOPs, emit master performance JSON
- `script/get_task_performance.py` and `script/summarize_comparison.py` — run with CWD = `dnallm-mark/data/` (they use relative paths `model_performance/`, output to CWD)
- `scripts/generate-tasks-index.js` — run from anywhere; resolves paths relative to `__dirname`
- `start-server.sh` — cd into `dnallm-mark/`, serve on `http://localhost:8080` via python3 http.server (falls back to `python`, then `npx http-server`)

## Architectural Constraints

- **Threading:** Browser JS is single-threaded; preloading is cooperative via `requestIdleCallback` with `setTimeout` fallback (`js/task-loader.js:175-181`). The pipeline is a single synchronous process; parallelism comes from PyTorch GPU execution only.
- **Global state:** `window.taskLoader` and `window.DNALLMDebug` (`js/task-loader.js:350,364`), `window.loadingController` (`js/task.js:94`) — required because `task.html` loads `task-loader.js` and `task.js` as sibling modules. `DataAPI.cache` is module-level mutable state.
- **Circular imports:** None. JS module graph is a DAG: `config.js` and `data.js` are leaves imported by page modules; `task-loader.js` imports nothing local.
- **Serving requirement:** ES modules + `fetch('./data/...')` require an HTTP origin; opening HTML via `file://` breaks data loading (hence `start-server.sh`).
- **CDN dependency:** Chart.js and SheetJS load from jsdelivr at page render; Google Fonts load in `css/variables.css` — offline usage degrades.
- **Relative-path scripts:** The two Python scripts must be run from `dnallm-mark/data/` or they write outputs to the wrong directory.
- **Hardcoded model whitelists in the pipeline** (`pipeline/dnallmmark_pipeline.py:1303-1339`): `model_not_use_safetensors`, `deeplearning_models`, `models_no_char_n`, `models_with_limited_length`, `models_only_support_fp32`, `special_models` — new models with quirks must be added there.
- **Arena taxonomy is fixed:** `all/animal/plant/microbe` is enforced in three places that must stay in sync — `CONFIG.ARENAS` (`js/config.js:11-16`), the arena→filename map (`js/data.js:23-28`), and the species grouping/filenames in `script/summarize_comparison.py:384-412`.

## Anti-Patterns

### renderNavbar writes to a nonexistent container

### Orphaned submit page

### Duplicate frontend aggregation logic

### Committed dev artifacts

### Data regeneration is implicit tribal knowledge

## Error Handling

- Frontend: every `setup()` wraps load+render in try/catch and logs to console (`js/main.js:36-48`); DataAPI rethrows fetch errors after `console.error`; `TaskLoader.fetchWithRetry` retries 3× with linear-exponential backoff and surfaces a user-facing error overlay with a Retry button (`js/task.js:76-82`, `js/task-loader.js:81-113`)
- Pipeline: per-model error log file `pipeline/logs/{model}_error_log.txt`; per-dataset exceptions print + log + `continue` to the next dataset; model-load failure `break`s to the next model (`pipeline/dnallmmark_pipeline.py:899-909, 1042-1051, 1270-1279`); completed datasets are skipped via `trainer_state.json` existence check (line 1013-1014)
- Data scripts: unreadable JSON files are skipped with a `[Skip]` message (`script/get_task_performance.py:105-110`); missing/empty metric values coerce to `0.0` via `get_float` and are excluded from ranking (`script/summarize_comparison.py:80-97, 351-365`)

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-fast` for a trivial task inline, with no subagents and no PLAN.md
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
