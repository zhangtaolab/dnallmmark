---
last_mapped_commit: a44d3104b8ab1e04ddbebed75446772fc0ca3f1b
last_mapped_at: 2026-10-08
---
# Coding Conventions

**Analysis Date:** 2026-10-08

This repo has three distinct code areas with separate conventions:

1. **Frontend** — `dnallm-mark/`: static multi-page site, vanilla ES6-module JavaScript, no build step, no bundler, no package.json.
2. **Python data scripts** — `script/`: standalone JSON-processing scripts run manually from `dnallm-mark/data/`.
3. **ML pipeline** — `pipeline/dnallmmark_pipeline.py`: long-running fine-tuning driver importing the external `dnallm` package.

## Naming Patterns

**Files:**
- JS page modules: lowercase singular noun matching their page — `js/main.js`, `js/models.js`, `js/datasets.js`, `js/task.js`, `js/submit.js`, `js/finetuning.js`
- JS utility modules: lowercase role name — `js/config.js`, `js/data.js`, `js/task-loader.js`
- CSS: lowercase role name — `css/variables.css`, `css/layout.css`, `css/components.css`, `css/charts.css`, `css/reset.css`, `css/typography.css`, `css/loading.css`, `css/task.css`
- Python: `snake_case.py` — `script/summarize_comparison.py`, `script/get_task_performance.py`, `pipeline/dnallmmark_pipeline.py`
- HTML pages: lowercase flat files in `dnallm-mark/` root — `index.html`, `task.html`, `finetuning.html`, `models.html`, `datasets.html`

**Functions/Methods:**
- JavaScript: `camelCase` — `loadModelsComparisonByArena()`, `filterAndSortModels()`, `renderScatterChart()`, `bindEvents()`, `fetchWithRetry()`
- Private-ish methods prefixed `_` in Python classes — `_register_hooks()`, `_linear_hook()` in `pipeline/dnallmmark_pipeline.py`
- Python: `snake_case` — `calculate_dataset_stats()`, `aggregate_models()`, `to_singular_species()`, `determine_batch_size()`
- Render methods: `renderX()` (`renderHero()`, `renderNavbar()`, `renderLeaderboard()`); lifecycle: `init()`, `setup()`, `loadData()`

**Variables:**
- `camelCase` in JS (`currentArena`, `filteredModels`, `modelPerformance`)
- `snake_case` in Python (`dataset_stats_map`, `raw_dataset_flops`, `master_performance_dict`)
- Constants: `UPPER_SNAKE_CASE` in JS (`CONFIG.APP_NAME`, `CONFIG.NAV_LINKS`) and module-level `const` in Node (`TASK_PERFORMANCE_DIR` in `scripts/generate-tasks-index.js`)

**Classes:**
- `PascalCase` — `DNALLMMark` (`js/main.js`), `ModelsPage` (`js/models.js`), `DatasetsPage` (`js/datasets.js`), `FineTuningPage` (`js/finetuning.js`), `SubmitPage` (`js/submit.js`), `TaskLoader` + `LoadingController` (`js/task-loader.js`, `js/task.js`), `FlopsCounter` (`pipeline/dnallmmark_pipeline.py`)

**Types:**
- No TypeScript. JSDoc annotations on most JS methods provide the type documentation.
- Data "contracts" are the JSON schemas documented in `README.md` and script docstrings (`info` / `performance` / `dataset` / `parameters` keys), not code types.

## Code Style

**Formatting:**
- No formatter configured (no `.prettierrc`, no `biome.json`, no `pyproject.toml`, no `setup.cfg`). Style is hand-maintained.
- JS: 2-space indent, single quotes, semicolons, trailing commas in multiline literals.
- Python: 4-space indent, double quotes for strings in `script/` files, follows ~PEP 8 but not enforced.
- CSS: 2-space indent, one declaration per line, lowercase hex colors.

**Linting:**
- None. No `.eslintrc*`, `eslint.config.*`, ruff/flake8/pylint config. (`.gitignore` mentions `.ruff_cache/` and `.pytest_cache/` but these are inherited from the upstream dnallm project — no such config exists here.)

## Frontend Module Pattern (the core convention)

Every page follows the same class lifecycle. Replicate this exactly for new pages:

```javascript
// js/<page>.js
import CONFIG from './config.js';
import DataAPI from './data.js';

class XxxPage {
  constructor() {
    this.state = { /* all mutable page state in one object */ };
    this.init();
  }

  init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  async setup() {
    try {
      await this.loadData();
      this.renderNavbar();
      this.renderHero();
      this.renderXxx();
      this.bindEvents();
    } catch (error) {
      console.error('Failed to setup xxx page:', error);
    }
  }
}

const app = new XxxPage();   // instantiate at module load
export default XxxPage;
```

See `js/main.js:9-49`, `js/models.js`, `js/datasets.js`, `js/finetuning.js`, `js/submit.js:8-37` for working examples.

**Rendering:**
- Build HTML strings with template literals and inject via `container.innerHTML = html`.
- Each dynamic region has an empty container div in the HTML page (`.navbar-container`, `.hero-container`, `.leaderboard-container`, `.category-nav-container`) — `js/main.js:89-116`.
- Always null-guard the container: `const el = document.querySelector(...); if (!el) return;`

**Events:**
- Bind in a `bindEvents()` method at the end of setup.
- Use event delegation on `document` for buttons that get re-rendered: `document.addEventListener('click', (e) => { const btn = e.target.closest('button[data-filter]'); ... })` — `js/main.js:477-486`.
- Use `e.target.closest('.selector')` to find the clicked element.
- Optional-chaining listener binding: `document.getElementById('x')?.addEventListener(...)` — `js/main.js:453`, `js/submit.js:288`.

**State:**
- Single `this.state` object per class; never scatter properties on `this`.
- Data access always goes through `DataAPI` (`js/data.js`) which memoizes fetched JSON in `DataAPI.cache`.
- Default defensive reads: `model.performance?.rank_score || 0`, `data.model?.['size (M)'] || 0`.

**Exports (dual-module compatibility):**

```javascript
export default DataAPI;                                   // ES6
if (typeof module !== 'undefined' && module.exports) {    // CommonJS guard
  module.exports = DataAPI;
}
```

Used in `js/config.js:102-107` and `js/data.js:276-282`. Apply to shared utility modules; page classes just use `export default`.

## External Libraries (frontend)

- Loaded as CDN `<script>` tags in each HTML `<head>` — **no npm**:
  - Chart.js 4.4.0: `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js` (global `Chart`, used without import — `js/main.js:342`)
  - SheetJS 0.18.5: `https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js`
- Page module loaded at end of body: `<script type="module" src="./js/main.js"></script>`
- Google Fonts imported in CSS: `@import url('https://fonts.googleapis.com/...')` — `css/variables.css:6`

## CSS Conventions

- Entry file `css/styles.css` `@import`s the others in order: variables → reset → typography → layout → components → charts. Add new files there.
- All colors/fonts/spacing via CSS custom properties defined in `css/variables.css` (`--color-primary: #292C33`, `--color-accent-teal: #265354`, `--font-body`, `--breakpoint-md`, ...). Do not hardcode hex values in components; use `var(--color-*)`.
- Flat hyphenated class names (not strict BEM): `.arena-table`, `.model-info`, `.btn-primary`, `.modal-overlay`, `.empty-state-icon`, `.rank-badge`.
- Responsive rules use `@media (max-width: var(--breakpoint-md))`; print styles in `css/styles.css`.
- Page-specific styles get their own file (`css/task.css`, `css/loading.css`).

## Python Conventions (script/)

Follow `script/summarize_comparison.py` and `script/get_task_performance.py` as the reference style:

- Large module docstring at top: purpose, input/output JSON structures, usage command, `See also:` cross-references to sibling scripts.
- Google-style docstrings on every function (`Args:`, `Returns:`) with RST double-backtick markup.
- `main()` function with a `# ===== Configuration =====` block at the top holding `input_dir` / `output_dir` constants; guard `if __name__ == "__main__": main()`.
- Scripts are **CWD-sensitive**: run from `dnallm-mark/data/` (`python ../../script/summarize_comparison.py`). Relative paths like `model_performance` resolve against CWD, not the script location.
- JSON I/O: `open(path, 'r', encoding='utf-8')` / `json.dump(..., indent=4, ensure_ascii=False)`.
- Defensive metric parsing via helpers like `get_float(val, default=0.0)` (`script/summarize_comparison.py:80-96`) — treat `""` and `None` as missing.
- Per-file try/except with `print(f"  [Skip] Failed to read file {filename}: {e}"); continue` for malformed inputs (`script/get_task_performance.py:105-110`).
- Friendly console output with emoji markers: `print(f"✅ Global comparison results saved to: {output_total}")`.

## Python Conventions (pipeline/)

`pipeline/dnallmmark_pipeline.py` is a different, older style:

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

**Order (JS):**
1. Config/shared modules: `import CONFIG from './config.js';`
2. Data layer: `import DataAPI from './data.js';`
3. (Nothing else — pages import at most these two; `js/task.js` imports only `data.js`)

**Python:** stdlib (`os`, `json`, `argparse`, `datetime`, `math`, `shutil`, `glob`, `pathlib`) → third-party (`numpy`, `pandas`, `torch`) → external project package (`from dnallm import ...`). Note `pipeline/dnallmmark_pipeline.py:1-4` sets `os.environ` cache vars before other imports (commented out).

**Node utility** (`scripts/generate-tasks-index.js`): CommonJS `require('fs')` / `require('path')` — intentionally different from the ES6 frontend modules.

**Path Aliases:** None. JS uses relative paths (`./config.js`, `./data/task_performance/...`); all data fetches are relative to the served `dnallm-mark/` root.

## Error Handling

**Patterns:**
- Fetch wrapper (frontend standard): check `response.ok`, `throw new Error(\`Failed to load ${fileName}: ${response.status}\`)`, `catch` → `console.error` → re-throw — `js/data.js:39-50`.
- Retry with exponential backoff in `TaskLoader.fetchWithRetry()` (`js/task-loader.js:81-113`) — 3 attempts, linear delay multiplier.
- Page-level catch-all in `setup()` that logs and leaves the page partially rendered — `js/main.js:46-48`.
- Client-side form validation via Promise wrapper around `FileReader` with per-check rejection messages — `SubmitPage.validateJSON()` (`js/submit.js:171-206`).
- Python scripts: per-file skip-on-error loops; pipeline: log-and-continue per dataset, log-and-break per model.

## Logging

**Framework:** None — `console.*` (JS) and `print()` (Python).

**Patterns:**
- Lifecycle chatter: `console.log('Setting up DNALLM Mark...')` / '... setup complete!' in every page's `setup()`.
- Tagged prefix for subsystems: `` console.log(`[TaskLoader] Initialized with ${n} tasks`) `` — `js/task-loader.js`.
- Timestamped prefix in pipeline: `print(f"[{current_time}] Loading model: {model_name}")`.
- Browser debug API exposed as global `window.DNALLMDebug` (`cacheStats()`, `clearCache()`, `clearTask(id)`, `preload(id)`, `tasks()`) — `js/task-loader.js:353-413`. New cache/loading subsystems should expose similar console helpers.

## Comments

**When to Comment:**
- Section banners with `/* ===== */` or `# =====` blocks at file/section tops (every JS/CSS/Python file).
- JSDoc on every non-trivial public method (`@param {string} arena - 'all', 'animal'...`, `@returns {Promise<Object>}`) — `js/data.js`, `js/task-loader.js`.
- Python docstrings explain *why* (normalization rationale, skip conditions), including inline `#` comments for numeric formulas (rank score `N - rank`, FLOPs scaling, `pipeline/dnallmmark_pipeline.py:1063-1076`).
- Comments are **bilingual English/Chinese** — several file headers and inline notes are in Chinese (`js/submit.js:3` "数据提交页面", `css/variables.css:2` "精确提取自源码", `js/main.js:476` event-delegation note). Either language is acceptable; match the surrounding file.

**JSDoc/TSDoc:** JSDoc only, no type-checking configured.

## Function Design

**Size:** Methods typically 10-40 lines; render methods assemble one HTML block each; the two `main()` functions (`script/*.py`) are long procedural scripts with banner-commented phases (Step 1 / Step 2 / Step 3).

**Parameters:** Plain positional args; config objects only in `CONFIG` / registries. JS callbacks use arrow functions.

**Return Values:** Async data methods return parsed JSON objects; render methods return nothing (side-effect DOM injection); helpers return derived primitives (`calculateAxisLimits()` returns `{min, max}`).

## Module Design

**Exports:** Default export only (one class or one object per module). Named exports not used.

**Barrel Files:** None. Pages import `config.js` / `data.js` directly.

**Shared services:**
- `CONFIG` (`js/config.js`) — app-wide constants: arenas, nav links, sort/filter options, scatter-chart config. Add page constants here, not inline.
- `DataAPI` (`js/data.js`) — single data layer for all pages; cache-aware; also holds small pure helpers (`normalizeToArena()`, `getColorForModel()` with the 15-color palette at `js/data.js:173-177`).

## Data Conventions

- Model alias = filename without `_performance.json` (`plant-dnabert-6mer_performance.json` → `plant-dnabert-6mer`); derived consistently in `js/data.js:241`, `script/get_task_performance.py:119`, `script/summarize_comparison.py:319`.
- Missing metrics are empty strings `""`, not `null` or `0` — every consumer must use `get_float()`-style coercion (`script/summarize_comparison.py:351-361`).
- Filenames sanitized by replacing `/` and `\` with `_` (`script/get_task_performance.py:155`, `script/summarize_comparison.py:405`).
- Species labels normalized to singular lowercase for filenames (`to_singular_species()`, `script/summarize_comparison.py:164-184`).

---

*Convention analysis: 2026-10-08*
