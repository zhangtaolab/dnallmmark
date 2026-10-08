---
last_mapped_commit: a44d3104b8ab1e04ddbebed75446772fc0ca3f1b
last_mapped_at: 2026-10-08
---
<!-- refreshed: 2026-10-08 -->

# Architecture

**Analysis Date:** 2026-10-08

## System Overview

DNALLM-Mark is a DNA LLM benchmark platform composed of three decoupled subsystems that communicate **only through committed JSON data files** — there is no runtime backend, no API, and no build step.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                 Static Web Leaderboard (MPA, no build step)            │
│   index.html   task.html   finetuning.html   models.html  datasets.html│
├────────────────┬────────────────┬───────────────────┬──────────────────┤
│  Leaderboard   │  Task          │  Fine-tuning      │  Models /        │
│  controller    │  controller    │  controller       │  Datasets ctrl   │
│  js/main.js    │  js/task.js    │  js/finetuning.js │  js/models.js    │
│                │  + js/task-    │                   │  js/datasets.js  │
│                │    loader.js   │                   │                  │
├────────────────┴────────────────┴───────────────────┴──────────────────┤
│        Data Access Layer (fetch + cache)                               │
│        js/data.js (DataAPI singleton)   js/task-loader.js (TaskLoader) │
├────────────────────────────────────────────────────────────────────────┤
│        Static JSON Data Layer — dnallm-mark/data/  (committed)         │
│        model_performance/   task_performance/   tasks.json             │
│        models_comparison.json + models_comparison_{species}.json       │
└──────────────────────────────▲─────────────────────────────────────────┘
                               │  offline regeneration (manual, by maintainer)
┌──────────────────────────────┴─────────────────────────────────────────┐
│              Offline Data Scripts (run from dnallm-mark/data/)         │
│  script/summarize_comparison.py     → models_comparison*.json          │
│  script/get_task_performance.py     → task_performance/*.json          │
│  scripts/generate-tasks-index.js    → tasks.json                       │
└──────────────────────────────▲─────────────────────────────────────────┘
                               │  manual copy of {model}_performance.json
┌──────────────────────────────┴─────────────────────────────────────────┐
│      Fine-tuning Pipeline — pipeline/dnallmmark_pipeline.py (CLI)      │
│      PyTorch + dnallm framework + FlopsCounter hooks                   │
│      Inputs : pipeline/models_info.json, pipeline/datasets_info.json,  │
│               pipeline/models/, pipeline/datasets/ (gitignored)        │
│      Outputs: pipeline/finetuned/{model}/{model}_performance.json      │
│               + flops_report.json, test_metrics.json per dataset       │
└────────────────────────────────────────────────────────────────────────┘
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

**Overall:** Static multi-page app (MPA) with vanilla ES-module classes, backed by a batch offline data pipeline.

**Key Characteristics:**
- **No build system, no framework, no bundler.** HTML pages load `type="module"` scripts directly; Chart.js 4.4.0 and SheetJS 0.18.5 come from jsdelivr CDN (`dnallm-mark/index.html:18-21`).
- **Page-controller class pattern.** Each page script defines one class, instantiated once at module load (`const app = new DNALLMMark()` at `js/main.js:504`; same in `task.js:590`, `finetuning.js:265`, `models.js:163`, `datasets.js:164`).
- **Shared lifecycle:** `constructor()` → `init()` (waits for DOMContentLoaded) → `setup()` → `loadData()` → `render*()` → `bindEvents()`.
- **Rendering via innerHTML template literals.** No virtual DOM, no templating engine. Event listeners on dynamically rendered content use event delegation bound to `document` (`js/main.js:477-486`).
- **Data as committed static files.** All leaderboard data is fetched from `dnallm-mark/data/`; regeneration is a manual maintainer step, not part of serving.
- **Pipeline is a single monolithic script** with a nested model×dataset loop, module-level config globals, and per-dataset try/except-continue error isolation.

## Layers

**Presentation (HTML/CSS):**
- Purpose: Static page shells (navbar, hero container, empty content containers) + styles
- Location: `dnallm-mark/*.html`, `dnallm-mark/css/`
- Contains: One HTML file per page; CSS entry `css/styles.css` imports `variables.css`, `reset.css`, `typography.css`, `layout.css`, `components.css`, `charts.css`; task page adds `css/task.css` + `css/loading.css`
- Depends on: Design tokens in `css/variables.css` (`--color-primary: #292C33` etc.), Google Fonts CDN
- Used by: Page controller scripts that fill `.hero-container`, `.leaderboard-container`, `.models-container`, `.datasets-container`

**Page Controllers (JS classes):**
- Purpose: Page-specific state, data loading, rendering, and event handling
- Location: `dnallm-mark/js/`
- Contains: One class per page plus shared `config.js` and `data.js`
- Depends on: `data.js`, `config.js`, global `Chart` (CDN), `window.taskLoader` / `window.loadingController` on the task page
- Used by: HTML module script tags

**Data Access (fetch + cache):**
- Purpose: Load and cache JSON; derive colors and arena categories
- Location: `dnallm-mark/js/data.js` (DataAPI), `dnallm-mark/js/task-loader.js` (TaskLoader)
- Contains: `DataAPI.loadModelsComparisonByArena/ loadModelsComparison / loadModelPerformance / loadAllModelPerformance`, `TaskLoader.initialize / loadTask / fetchWithRetry / preloadNeighbors`
- Depends on: static files under `dnallm-mark/data/`
- Used by: all page controllers

**Static JSON Data:**
- Purpose: The single source of truth the UI renders
- Location: `dnallm-mark/data/`
- Contains: `model_performance/` (42 per-model files, hand/pipeline-maintained input), generated `task_performance/` (47 files), generated `tasks.json`, generated `models_comparison{,_animal,_plant,_microbe}.json`
- Depends on: produced offline by `script/` + `scripts/`
- Used by: DataAPI/TaskLoader fetch calls

**Offline Data Scripts (Python + Node):**
- Purpose: Regenerate derived JSON from `model_performance/`
- Location: `script/` (Python), `scripts/` (Node)
- Depends on: `model_performance/` input; numpy + pandas for `summarize_comparison.py`
- Used by: maintainers, run manually from `dnallm-mark/data/`

**Fine-tuning Pipeline (Python):**
- Purpose: Produce `{model}_performance.json` by fine-tuning each model on each dataset
- Location: `pipeline/dnallmmark_pipeline.py` + `finetune_config.yaml`, `finetune_config_with_head.yaml`, `models_info.json`, `datasets_info.json`
- Depends on: external `dnallm` package (`DNADataset`, `load_config`, `load_model_and_tokenizer`, `DNATrainer` — imported at `pipeline/dnallmmark_pipeline.py:18`), `torch`, `transformers`, local `pipeline/models/` and `pipeline/datasets/` (gitignored, downloaded from Zenodo per `README.md`)
- Used by: benchmark maintainers via CLI

## Data Flow

### Primary Request Path (Main Leaderboard)

1. Browser loads `dnallm-mark/index.html`; static navbar + empty containers render; Chart.js/SheetJS load from CDN (`dnallm-mark/index.html:18-21`)
2. `js/main.js` module executes → `new DNALLMMark()` → `setup()` (`js/main.js:33`)
3. `loadData()` calls `DataAPI.loadModelsComparisonByArena('all')` → `fetch('./data/models_comparison.json')` with in-memory cache (`js/data.js:22-51`)
4. `renderScatterChart()` destroys previous Chart instance and builds a Chart.js scatter: x = `sum_PFLOPs` (linear/log10 toggle), y = `rank_score` (`js/main.js:195-346`)
5. `renderLeaderboard()` writes the sortable table HTML into `.leaderboard-container` (`js/main.js:363-408`)
6. Arena tab click (all/animal/plant/microbe) → `loadData()` refetches `models_comparison_{arena}.json` and re-renders (`js/main.js:462-474`)

### Task Benchmark Flow

1. `task.html` loads two module scripts in order: `js/task-loader.js` then `js/task.js` (`dnallm-mark/task.html:176-177`)
2. `task-loader.js` creates global `window.taskLoader` (`js/task-loader.js:350`) and `window.DNALLMDebug` console API (`js/task-loader.js:364`); `task.js` creates `window.loadingController` (`js/task.js:94`)
3. `TaskBenchmark.setup()` → `loader.initialize()` fetches lightweight `data/tasks.json` (~5KB index of 47 tasks) (`js/task-loader.js:23-40`)
4. Task selection → `handleTaskChange()` → `loadTask()`: memory LRU cache (max 10) → localStorage cache (24h TTL, prefix `dnallm_task_`) → `fetchWithRetry()` (3 attempts, exponential backoff) fetches `data/task_performance/{fileName}` (`js/task-loader.js:48-113`)
5. Idle-time preload of 2 adjacent tasks via `requestIdleCallback` (`js/task-loader.js:172-224`)
6. `populateMetricDropdown()` derives available metrics from first model's performance keys; default metric comes from `taskData.info.metric` with `pearsonr→pearson_r` style remapping (`js/task.js:181-224`)
7. `renderBarChart()` (horizontal Chart.js bar) + `renderLeaderboard()` (table) re-render on metric/sort changes

### Benchmark Production Flow (Offline)

1. Maintainer runs `python dnallmmark_pipeline.py --target_model NAME --batch_size N` from `pipeline/` with models in `pipeline/models/` and datasets in `pipeline/datasets/`
2. Module-level loads: `datasets_info.json` (50 datasets), `models_info.json` (41 models) plus hardcoded model whitelists (`pipeline/dnallmmark_pipeline.py:1295-1339`)
3. Per model×dataset: dynamic batch-size scaling by sequence length (`determine_batch_size`, line 772-795), `DNADataset.load_local_data`, sequence validation/encoding, token-length derivation from tokenizer type
4. `FlopsCounter` registers per-architecture forward hooks and runs one forward pass → writes `finetuned/{model}/{dataset}/flops_report.json` (lines 1053-1138)
5. `DNATrainer.train()` + `evaluate()` → `trainer_state.json`, `final_metrics.json`, `test_metrics.json`
6. Master JSON `finetuned/{model}/{model_name}_performance.json` is created/updated with the dataset entry (dataset info, training parameters, all metrics + runtime + FLOPs) (lines 1195-1268)
7. `{model}_performance.json` is copied into `dnallm-mark/data/model_performance/`

### Data Regeneration Flow (Offline)

1. `cd dnallm-mark/data && python ../../script/get_task_performance.py` — pivots model-centric → `task_performance/{dataset}_task_performance.json` (`script/get_task_performance.py:75-164`)
2. `python ../../script/summarize_comparison.py` — per-task normalization (rank score = N−rank, MinMax, Z-score, robust median/IQR), sums per model, assigns overall rank, writes `models_comparison.json` + per-species variants (`script/summarize_comparison.py:270-414`)
3. `node ../../scripts/generate-tasks-index.js` — scans `task_performance/` and writes `tasks.json` (`scripts/generate-tasks-index.js:14-67`)

**State Management:**
- Each page controller keeps a plain `this.state` object; no shared client state, no router — navigation is full page loads, so state does not survive navigation
- Chart re-render always destroys first: `if (this.state.chart) this.state.chart.destroy()` (`js/main.js:199-201`, `js/task.js:330-332`)
- Cross-module state on the task page uses window globals (`window.taskLoader`, `window.loadingController`) because the two scripts are separate ES modules that cannot import each other's instances
- Pipeline state: `configs` object mutated in-place per dataset (num_labels, batch size, output_dir) and reloaded from YAML per model

## Key Abstractions

**Page Controller Class:**
- Purpose: Encapsulate one page's state + rendering + events
- Examples: `DNALLMMark` (`js/main.js:9`), `TaskBenchmark` (`js/task.js:96`), `FineTuningPage` (`js/finetuning.js:9`), `ModelsPage` (`js/models.js:9`), `DatasetsPage` (`js/datasets.js:9`), `SubmitPage` (`js/submit.js:8`)
- Pattern: constructor sets `this.state`, calls `init()`; `setup()` runs `loadData → render* → bindEvents` inside try/catch

**DataAPI singleton:**
- Purpose: Single fetch/cache layer + shared presentation helpers (model color palette at `js/data.js:172-179`, species→arena normalization at `js/data.js:149-164`)
- Examples: `dnallm-mark/js/data.js`
- Pattern: plain object literal with module-level `cache` object; default export with CommonJS fallback

**TaskLoader (two-tier cache):**
- Purpose: Fast task switching without refetching; LRU Map (size 10) + versioned localStorage entries with 24h expiry
- Examples: `dnallm-mark/js/task-loader.js:6`
- Pattern: class instantiated once and exposed as `window.taskLoader`; debug API exposed as `window.DNALLMDebug`

**FlopsCounter:**
- Purpose: Architecture-aware FLOPs accounting via PyTorch forward hooks
- Examples: `pipeline/dnallmmark_pipeline.py:24`
- Pattern: `_register_hooks()` dispatches on module class name across ~20 attention/SSM variants (HF self-attention, flash attention, GQA, BigBird sparse, ModernBERT windowed, Hyena FFT, Mamba/Mamba2 SSD, Caduceus, Borzoi, Enformer, megaDNA); `save_to_json()` extrapolates per-token FLOPs to the full training run

**Performance JSON contract (the integration seam):**
- Purpose: The schema that couples pipeline → scripts → UI
- Examples: `dnallm-mark/data/model_performance/*_performance.json`
- Pattern: `{ info: {model card}, performance: { {dataset}: { dataset: {...}, parameters: {...}, performance: {metrics incl. FLOPs, runtime} } } }`; dataset names use `Source__task` convention (e.g. `GUE__emp_H3`); primary metric per dataset declared as `dataset.metric` and mapped via `metric_key_map` in `script/summarize_comparison.py:295-305`

## Entry Points

**Web pages (HTTP server required, port 8080):**
- `dnallm-mark/index.html` — main leaderboard; module script `js/main.js`
- `dnallm-mark/task.html` — task benchmark; module scripts `js/task-loader.js` + `js/task.js`
- `dnallm-mark/finetuning.html` — fine-tuning results; `js/finetuning.js`
- `dnallm-mark/models.html` — model cards; `js/models.js`
- `dnallm-mark/datasets.html` — dataset catalog; `js/datasets.js`
- `dnallm-mark/task-mockup.html`, `test.html`, `verify-chart.html` — standalone dev/mockup artifacts, not linked from navigation

**Pipeline CLI (run from `pipeline/`):**
- Location: `pipeline/dnallmmark_pipeline.py`
- Triggers: `python dnallmmark_pipeline.py [--target_model M] [--target_dataset D1,D2] [--batch_size N] [--fix_token_len L] [--max_token_len L] [--remove_pt] [--remove_checkpoints] [--seed S]`
- Responsibilities: fine-tune, evaluate, count FLOPs, emit master performance JSON

**Data scripts:**
- `script/get_task_performance.py` and `script/summarize_comparison.py` — run with CWD = `dnallm-mark/data/` (they use relative paths `model_performance/`, output to CWD)
- `scripts/generate-tasks-index.js` — run from anywhere; resolves paths relative to `__dirname`

**Server launcher:**
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

**What happens:** `finetuning.js`, `models.js`, `datasets.js`, and `submit.js` each call `this.renderNavbar()` inside `setup()`, and `renderNavbar()` does `document.querySelector('.navbar-container').innerHTML = ...` (`js/finetuning.js:65`, `js/models.js:75`, `js/datasets.js:79`, `js/submit.js:52`). No HTML page defines `.navbar-container` — every page has a hardcoded static `<nav class="navbar">`. The assignment throws a TypeError on `null`, which the `setup()` try/catch swallows, aborting the remaining render steps on those pages.
**Why it's wrong:** A dead render call placed before live render calls turns into a page-breaking bug that fails silently (console.error only).
**Do this instead:** Either remove the `renderNavbar()` calls (pages already have static navbars), or add the `.navbar-container` div to the pages and delete the duplicated static navbar. Note `main.js` also defines `renderNavbar` (`js/main.js:72-90`) but never calls it.

### Orphaned submit page

**What happens:** `CONFIG.NAV_LINKS` and mockup navigation reference `/submit.html` (`js/config.js:56`), and `js/submit.js` (300 lines) is fully implemented, but `dnallm-mark/submit.html` does not exist.
**Why it's wrong:** Nav links from any rendered navbar 404; the submission feature is unreachable.
**Do this instead:** Create `dnallm-mark/submit.html` following the `datasets.html` shell pattern (static navbar + `.hero-container` + `.submit-container` + `js/submit.js` module script), or remove the nav entry and `submit.js`.

### Duplicate frontend aggregation logic

**What happens:** `DataAPI.recalculateComparison()` (`js/data.js:187-273`) reimplements leaderboard aggregation in the browser, but returns placeholder values (`rank = 1`, `sumRank = 0`, threshold-based top-N counts). The real aggregation lives in `script/summarize_comparison.py`.
**Why it's wrong:** Two divergent implementations of the scoring contract; the JS one is wrong and currently uncalled.
**Do this instead:** Treat `models_comparison*.json` as authoritative (generated by `script/summarize_comparison.py`) and delete the frontend reimplementation when touching `data.js`.

### Committed dev artifacts

**What happens:** `dnallm-mark/task-mockup.html` (429 lines), `test.html`, and `verify-chart.html` are standalone mockup/verification pages committed alongside production pages.
**Why it's wrong:** They drift from real pages (mockup navbar links differ from live pages) and confuse navigation expectations.
**Do this instead:** Keep new experiment pages out of `dnallm-mark/` root or clearly named with a `-mockup`/`-test` suffix and never linked from `CONFIG.NAV_LINKS`.

### Data regeneration is implicit tribal knowledge

**What happens:** The three-step regeneration chain (`get_task_performance.py` → `summarize_comparison.py` → `generate-tasks-index.js`, run from `dnallm-mark/data/`) is documented only in `README.md`; nothing detects stale derived files when a `model_performance/*.json` changes.
**Why it's wrong:** Adding a model file without rerunning all three steps leaves leaderboards and task pages inconsistent.
**Do this instead:** When adding/changing any `model_performance/*.json`, run all three scripts in order from `dnallm-mark/data/` before committing.

## Error Handling

**Strategy:** Isolated, per-item failure with logging; never abort the whole run/render.

**Patterns:**
- Frontend: every `setup()` wraps load+render in try/catch and logs to console (`js/main.js:36-48`); DataAPI rethrows fetch errors after `console.error`; `TaskLoader.fetchWithRetry` retries 3× with linear-exponential backoff and surfaces a user-facing error overlay with a Retry button (`js/task.js:76-82`, `js/task-loader.js:81-113`)
- Pipeline: per-model error log file `pipeline/logs/{model}_error_log.txt`; per-dataset exceptions print + log + `continue` to the next dataset; model-load failure `break`s to the next model (`pipeline/dnallmmark_pipeline.py:899-909, 1042-1051, 1270-1279`); completed datasets are skipped via `trainer_state.json` existence check (line 1013-1014)
- Data scripts: unreadable JSON files are skipped with a `[Skip]` message (`script/get_task_performance.py:105-110`); missing/empty metric values coerce to `0.0` via `get_float` and are excluded from ranking (`script/summarize_comparison.py:80-97, 351-365`)

## Cross-Cutting Concerns

**Logging:** `console.log`/`console.warn`/`console.error` only; TaskLoader prefixes messages `[TaskLoader]`; pipeline prints timestamped `[YYYY-MM-DD HH:MM:SS]` lines to stdout. No structured logging or error tracking.

**Validation:** Client-side submission JSON validation checks object shape and required `dataset`/`performance` fields (`js/submit.js:171-206`); pipeline validates sequence characters per model (`dataset.validate_sequences` with model-specific `valid_chars`, `pipeline/dnallmmark_pipeline.py:1034-1041`).

**Authentication:** None. The site is fully public static content; submissions happen via git PR (instructions generated client-side in `js/submit.js:208-262`), not via an API.

**Styling:** CSS custom properties in `css/variables.css` are the design token source; use `var(--color-*)`, `var(--font-*)`, `var(--breakpoint-*)` instead of hardcoded values.

---

*Architecture analysis: 2026-10-08*
