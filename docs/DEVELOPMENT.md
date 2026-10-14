<!-- generated-by: gsd-doc-writer -->
# Development

How to work on the DNALLM-Mark codebase: where a change goes, the loop for iterating on it, the gates it must pass, and the constraints that keep the project's core guarantee — every leaderboard number reproducible from committed code — intact. For environment and configuration reference, see [CONFIGURATION](CONFIGURATION.md); for how the numbers are computed, see [METHODOLOGY](METHODOLOGY.md); for system structure, see [ARCHITECTURE](ARCHITECTURE.md).

## Local setup

Prerequisites: **Python >= 3.13** (`.python-version` pins 3.13), **uv** (reads the committed `uv.lock`), and **Node >= 18** (a hard dependency of `make data` and `make test`; `make test-fast` is the pytest-only escape hatch when node is absent). No GPU is needed for any lane below.

```bash
git clone <repository-url>
cd dnallmmark
uv sync
```

`uv sync` installs only the `data` dependency group (`default-groups = ["data"]` in `pyproject.toml`). The dev tools (`pytest`, `ruff`, `ty`, `jsonschema`, `textual`) are pulled automatically on demand by the `make` targets via `uv run --group dev --group tui` — you never activate a venv or install dev tools by hand. If uv lives outside the default path: `make UV=/path/to/uv`.

GPU-only extras (never needed for CPU development): the `gpu` group (`uv sync --group gpu`) plus a manually installed `dnallm` package, plus model/dataset files under `pipeline/models/` and `pipeline/datasets/` (gitignored; see the README's pipeline section).

To work on the website: `bash start-server.sh` serves `dnallm-mark/` at `http://localhost:8080` (ES modules require an HTTP origin; `file://` breaks data loading). To work on the operator console: `make tui`.

## Where changes go

The project has four subsystems coupled only by committed JSON artifacts. Pick the subsystem that owns your change; the data contract (`schemas/*.json`) is the only thing that crosses boundaries.

| Change | Goes in | Covered by |
|--------|---------|-----------|
| Training, sweep driving, multi-GPU sharding, FLOPs hooks | `pipeline/` (`run_finetune.py`, `run_sweep.py`, `run_sweep_shard.py`, `flops_counter.py`, …) | `tests/test_sweep.py`, `tests/test_sweep_shard.py`, `tests/test_flops_counter.py`, `tests/test_run_finetune_contracts.py` |
| Aggregation, export, provenance, snapshot tooling | `script/` (Python) and `scripts/` (Node one-offs) | `tests/test_aggregation.py`, `tests/test_export_runs.py`, `tests/test_golden.py`, `tests/js/*.test.js` |
| Leaderboard pages and data-fetching | `dnallm-mark/js/*.js`, `dnallm-mark/css/*.css`, `dnallm-mark/*.html` | `make test` JS lane, CI `static-js` job (`node --check`, ESLint, html-validate) |
| Operator console | `tui/screens/` (presentation) and `tui/services/` (textual-free logic) | `tests/tui/` Pilot + service tests, the import lock, SVG goldens |
| Artifact shapes crossing a subsystem boundary | `schemas/*.json` | `tests/test_schemas.py` |

Two structural rules to know before touching anything:

- **`make data` output must be byte-identical on an unchanged tree.** Any edit to `script/` aggregation logic that changes committed data must be committed together with the regenerated data files (and documented before/after). CI's `drift` job runs `make data` then `git diff --exit-code -- dnallm-mark/data/` on every pull request.
- **The arena taxonomy (`all/animal/plant/microbe`) is fixed** and enforced at three points that must stay in sync: `CONFIG.ARENAS` in `dnallm-mark/js/config.js`, the arena→filename map in `dnallm-mark/js/data.js`, and the grouping authority in `script/summarize_comparison.py` (which reads the `Category` column of `pipeline/datasets_info.json`).

## Build commands

There is **no build step anywhere** — the web UI is vanilla ES modules served as-is, and Python runs from source. The Makefile is the entire command surface (run everything from the repo root):

| Command | Description |
|---------|-------------|
| `make data` | Regenerate the derived data chain: `summarize_comparison.py` (run with CWD = `dnallm-mark/data/`), `permutation_tests.py`, `build_provenance.py`, then `node scripts/generate-tasks-index.js` |
| `make test` | Full local gate: pytest (including the `slow` real-tree determinism lane) plus the node:test JS suite over `tests/js/` |
| `make test-fast` | pytest excluding `@slow` tests; JS lane does not run |
| `make ci` | The pinned CI selection (`pytest -m ci`): golden replay over `tests/fixtures/e2_replay/`, metric-key parity, species spot checks, aggregation units |
| `make lint` | `ruff check` over `tests/` plus the explicit fixed-findings file list (see the `lint` target in the Makefile) |
| `make typecheck` | `ty check` over `script/`, `baseline/`, `tests/`, `scripts/`, `pipeline/`, `tui/` |
| `make tui` | Launch the operator console (`python -m tui`) with the `tui` + `gpu` groups — display host only |
| `make snapshot` | Freeze the committed derived-data set into `baseline/snapshots/` (tar + SHA256 manifest) for deposition |
| `make snapshot-update` | Regenerate the TUI SVG goldens in `tests/tui/__snapshots__/` — maintainer-only, see TUI development below |

## The dev loop

While iterating, run the focused test module rather than the whole suite:

```bash
uv run --group dev --group tui pytest tests/test_aggregation.py -q
uv run --group dev --group tui pytest tests/tui/test_services_selection.py -k "preset" -q
node --test tests/js/data-api.test.js
```

Include `--group tui` whenever you invoke pytest manually: pytest imports every collected module (including `tests/tui/`, which imports `textual`) before marker filtering, so a dev-only environment fails collection. Two pytest markers exist (`pyproject.toml`): `slow` (real-tree determinism regressions, excluded by `make test-fast`) and `ci` (the pinned CI lane). `asyncio_mode = "auto"` means async Textual Pilot tests need no marker. `tests/conftest.py` pins BLAS/OpenMP threads to 1 for reproducible numpy reductions and puts `script/`, `baseline/`, and `pipeline/` on `sys.path` so test modules import them as top-level modules; `tests/tui/conftest.py` adds the repo root for package-qualified `tui` imports.

Before pushing, run the full local gate — all three must pass:

```bash
make test && make lint && make typecheck
```

- **ruff gate** (`make lint`): no `[tool.ruff]` config exists; scope is the explicit file list in the Makefile's `lint` target — `tests/`, the fixed-findings scripts in `script/` and `baseline/`, the pipeline modules, and every `tui/` Python file via a directory glob. Code you edit inside that list must stay clean; code outside it is deliberately not linted yet.
- **ty gate** (`make typecheck`): zero-diagnostics baseline; GPU-side imports (`torch`, `dnallm`, `transformers`, `peft`, `datasets`, `evaluate`, `torch_npu`) are substituted as `Any` via `[tool.ty]` in `pyproject.toml` because they are never installed CPU-side. `textual` is checked against real types (no substitution).
- If your change touches aggregation inputs or outputs, also verify the drift invariant: `make data` then `git status --porcelain dnallm-mark/data/ DATA.md` must show only your intended changes.

## Code style

No formatter is configured (no `.prettierrc`, no `biome.json`, no `[tool.ruff]` format settings) — style is hand-maintained, and the lint gate checks for correctness-class findings only. Match the surrounding files:

**Python (`script/`, `pipeline/`, `tui/`, `tests/`)**

- 4-space indent, roughly PEP 8; double quotes for strings in `script/` files.
- Large module docstring at the top: purpose, input/output JSON structures, usage command, `See also:` cross-references to sibling scripts.
- Google-style docstrings on every function (`Args:`, `Returns:`) with double-backtick markup.
- `main()` function with a `# ===== Configuration =====` block at the top holding input/output path constants; guard with `if __name__ == "__main__":`.
- Comments explain *why* (normalization rationale, skip conditions) and may be bilingual English/Chinese — either language is acceptable; match the surrounding file. Section banners use `# ===== ... =====`.
- Defensive parsing: metric coercion helpers treat `""` and `None` as missing; JSON I/O uses `open(path, "r", encoding="utf-8")` and `json.dump(..., indent=4, ensure_ascii=False)`.
- Naming: `snake_case` functions/variables, `UPPER_SNAKE_CASE` constants, private-ish methods prefixed `_` (e.g. the hook closure factories in `pipeline/flops_counter.py`).

**JavaScript (`dnallm-mark/js/`, `tests/js/`)**

- 2-space indent, single quotes, semicolons, trailing commas in multiline literals; `camelCase` functions/variables, `PascalCase` for the page-controller classes.
- JSDoc on every non-trivial public method (`@param`, `@returns`).
- Follow the page-controller pattern and `DataAPI`-only data access described in the frontend section below.
- Tests use the built-in `node:test` runner with zero npm dependencies.

**CSS (`dnallm-mark/css/`)**

- 2-space indent, one declaration per line, lowercase hex colors.
- Never hardcode hex values in components — use the custom properties from `css/variables.css` (`var(--color-primary)`, `var(--font-body)`, `var(--breakpoint-md)`, …).
- Flat hyphenated class names (`.arena-table`, `.btn-primary`), not strict BEM; responsive rules via `@media (max-width: var(--breakpoint-md))`; page-specific styles get their own file imported from `css/styles.css`.

## Regenerating derived data

The former three-step CWD-sensitive manual procedure is gone — everything runs from the repo root via `make data`, which handles the per-script working-directory requirements itself:

- `script/summarize_comparison.py` is CWD-sensitive (it resolves `model_performance/` and writes outputs against the current directory), so the Makefile runs it with `cd dnallm-mark/data/`. If you ever run it by hand, match that: `cd dnallm-mark/data && uv run --group data python ../../script/summarize_comparison.py`.
- `script/permutation_tests.py` and `script/build_provenance.py` are repo-root-relative; `scripts/generate-tasks-index.js` is `__dirname`-relative and runs from anywhere.

What the chain produces and consumes:

- **Inputs:** `dnallm-mark/data/model_performance/` (45 per-model files) and the committed `task_performance/` directory (47 files of committed static data — its regeneration path is `script/export_runs.py`, not `make data`).
- **Outputs:** `models_comparison.json` + the three arena subsets, `weighted_score` view, `manifest.json` (data-version stamp), `permutation_tests.json`, `provenance.{json,csv}`, `tasks.json`.
- On an unchanged tree, `make data` is a **byte-identical no-op** — this is the repository's core reproducibility guarantee, machine-checked by the CI `drift` job on every pull request. Other committed files in `dnallm-mark/data/` (e.g. `models_comparison_multi-species.json`, `n_audit.{json,csv}`) are maintainer-added artifacts outside the `make data` output set.

When a deliberate data revision lands (a fix that changes aggregated numbers): regenerate, verify the diff contains only the intended changes, document the before/after comparison, and re-freeze the snapshot (`make snapshot`) if a deposition archive is being updated. The frozen commit hash in `baseline/snapshots/` reads the committed `manifest.json` `generated_from` field, never a live git call.

## Adding a benchmark model or dataset

The full step-by-step checklists with expected outputs live in [ONBOARDING](ONBOARDING.md). The shape of the work:

**Model** — add one entry to `pipeline/models_info.json` keyed by the model's directory name under `pipeline/models/` (62 entries currently; the registry is the single source of truth). Each entry needs the 11-key card the leaderboard renders (`name`, `size (M)`, `type`, `tokenizer`, `mean_token_len`, `architecture`, `series`, `context_len (bp)`, `species`, `huggingface`, `modelscope` — unknown values stay empty, never invented) plus the operational fields (`Model_name`, `Model_path`, `Model_size`, `Tokenizer`, `Mean_token_length`), with `key == Model_name` enforced. If the model needs special handling, add its name to the relevant quirk list in `pipeline/run_finetune.py`'s `__main__` block (`model_not_use_safetensors`, `deeplearning_models`, `models_no_char_n`, `models_with_limited_length`, `models_only_support_fp32`, `special_models`). Then validate CPU-only: the registry round-trip via `script/convert_registry.py`, the registry contract tests (`tests/test_model_registry.py`, `tests/test_registry_unification.py`), and a `run_sweep.py --dry-run` that proves the matrix enumeration without launching training.

**Dataset** — never hand-edit `pipeline/datasets_info.json`; regenerate its CSV projection with `script/convert_registry.py --to-csv`, edit the row (all 17 columns, including the six provenance columns where unresolved values are the literal `Unspecified`, and `Category` = `Animals`/`Plants`/`Microbe`, which drives arena grouping), and re-ingest with `--to-json --merge-existing`. Place `train.csv`/`dev.csv`/`test.csv` under `pipeline/datasets/<group>/<task>/` — every task needs a non-empty dev split (`script/make_dev_splits.py --check` verifies; the pipeline refuses to run without one). The primary `metric` value must exist in the canonical metric-key map owned by `script/export_runs.py`; a genuinely new metric name turns the schema enum tests in `tests/test_schemas.py` red until every enum copy is updated together. Finish with `make data` (checking the drift diff) and the full local gate.

**The performance-data contract** — leaderboard results live in `dnallm-mark/data/model_performance/{model}_performance.json` (`{model}` = filename minus `_performance.json`): top-level `{ info, performance }`, where `info` mirrors the registry card and each `performance` cell is `{ dataset, parameters, performance }` keyed by `Source__task` dataset names. Missing metrics are empty strings `""`, never `null` or `0` — every consumer must coerce (`get_float()`-style in `script/`). The shape is machine-checked against `schemas/model_performance.json` by `tests/test_schemas.py`. The modern path to producing these files is `script/export_runs.py` (the exporter that maps suite-native metric keys, joins the registries, aggregates seeds, and emits both the per-model and task views); hand-edits are the legacy path and every edit must keep the files schema-clean.

## Frontend development (zero-build constraints)

The web UI is **vanilla ES-module JavaScript with no framework, no bundler, and no npm** — the public-release architecture forbids introducing any of these. Chart.js 4.4.0 and SheetJS 0.18.5 load as jsDelivr CDN `<script>` tags in each HTML head; Google Fonts load from `css/variables.css`. Zero npm packages are committed; frontend checks run via exact-version `npx` pins in CI (`eslint@10.12.0` over `dnallm-mark/js/*.js` using the dependency-free flat config `eslint.config.mjs`, and `html-validate@11.16.2` over the HTML shells per `.htmlvalidate.json`).

The conventions every frontend change follows:

- **Page-controller class pattern.** One class per page, instantiated once at module load: `DNALLMMark` (`js/main.js`), `TaskBenchmark` (`js/task.js`), `FineTuningPage`, `ModelsPage`, `DatasetsPage`, `SubmitPage`, `ProgressPage`. Shared lifecycle: `constructor()` → `init()` (waits for DOMContentLoaded) → `setup()` → `loadData()` → `render*()` → `bindEvents()`, with `setup()` wrapped in try/catch.
- **State is a single `this.state` object per class**; rendering builds HTML template strings and injects via `container.innerHTML`. Null-guard every container query (`if (!el) return;`).
- **Event delegation on `document`** with `e.target.closest('.selector')` for buttons that get re-rendered; optional chaining for one-off listeners (`document.getElementById('x')?.addEventListener(...)`).
- **All data access goes through `DataAPI`** (`js/data.js`) — the one fetch/memoize layer, which also owns the model color palette and arena normalization. The task page adds `TaskLoader` (`js/task-loader.js`, LRU + localStorage caching, exposed as `window.taskLoader` with the `window.DNALLMDebug` console API).
- **Charts destroy before re-render** (`if (this.state.chart) this.state.chart.destroy()`).
- **Constants live in `js/config.js`** (`CONFIG.ARENAS`, `CONFIG.NAV_LINKS`, sort/filter options), not inline; the shared navbar renderer is `js/navbar.js`.
- **CSS:** 2-space indent, one declaration per line, colors/fonts/spacing only via the custom properties in `css/variables.css` (`var(--color-*)`), flat hyphenated class names, new files `@import`ed in `css/styles.css`.

A new page means: one HTML shell with empty container divs, one page-controller module in `js/`, an entry in `CONFIG.NAV_LINKS`, and — where behavior is non-trivial — a `tests/js/*.test.js` behavior test (node:test, zero npm deps; existing examples test `DataAPI` memoization, HTML escaping, the tasks-index generator, and the top-N/view-toggle filters).

## TUI development

The console (`tui/`, launched with `make tui`) has a strict two-tier split:

- **`tui/screens/` is presentation only** — it may import textual freely, renders state held by services, posts user intent back, and runs GPU/IO work in `@work(thread=True)` workers. All operator-facing copy comes from `tui/strings.py` constants, never inline strings.
- **`tui/services/` is textual-free** — no textual import anywhere (directly or nested), so every CPU lane can import it headless. The invariant is locked by `tests/tui/test_import_lock.py`, which AST-walks every services file; an import hidden inside a function fails the lock exactly as hard as a top-level one.

The dependency direction is one-way, `tui → pipeline`: services import `env_smoke` / `registry_loader` / `artifact_loader` as top-level modules (`tui/__main__.py` bootstraps `sys.path` with the repo root and `pipeline/`). `tui/app.py` is the composition root only — every service is constructor-injectable (a Protocol-injection seam), which is what makes tier-2 testing possible:

- **Pilot tests** (`tests/tui/test_pilot_*.py`) boot the real `DnallmMarkTui` headlessly via `App.run_test(size=(120, 40))` against deterministic fakes — no GPU, display, or artifact tree. Discipline: `await pilot.pause()` before every assertion; async tests need no marker (`asyncio_mode = "auto"`).
- **Service tests** (`tests/tui/test_services_*.py`) test the textual-free layer directly, headless.
- **SVG goldens** (`tests/tui/__snapshots__/*.svg`, eight canonical screen states, produced by `tests/tui/test_snapshots.py`): plain UTF-8 string equality against committed SVG exports of `App.export_screenshot()`. `make test` compares and goes red on drift — it never rewrites the goldens, and `pytest --snapshot-update` does nothing here (no snapshot plugin is installed).

**`make snapshot-update` is the only regeneration path and is maintainer-only:** after any regeneration, review every changed SVG in a browser/editor, then commit the refreshed goldens together with the change that drifted the render. Golden determinism rules (enforced by the frozen fixtures in `test_snapshots.py`): one terminal size (120x40, the design grid) for every golden; zero wall-clock reads, filesystem scans, network, or GPU (constructor-injected fakes with pinned `checked_at` and scripted stats); cursor blink disabled on every Input before export; the static `⠋` glyph only, never spinner frames.

## Branch conventions

No branch-naming convention is documented in the repository. The default branch is `main`; day-to-day development happens on the standing `autorun` branch, which is synced to `main` deliberately rather than continuously. Keep topic-branch work based on `autorun` while it is ahead.

## PR process

There is no pull-request template; the de facto review gate is CI (`.github/workflows/ci.yml`, running on every pull request and push to `main`), which replays exactly the local lanes. Before opening a PR:

- Run the full local gate — `make test && make lint && make typecheck` — and, for anything touching the data chain, `make data` with a clean drift check.
- Commit regenerated data files together with the logic change that produced them; a PR where `make data` drifts the tree will fail the CI `drift` job.
- If your change altered a TUI screen render, regenerate the SVG goldens via `make snapshot-update`, review them, and commit them in the same PR.
- If your change alters an artifact shape crossing a subsystem boundary, update the corresponding `schemas/*.json` in the same change (the schema tests pin the enums).
- Every CI action is pinned by full commit SHA and no CI job uses secrets or installs GPU dependencies — keep it that way; GPU-only work stays on workstation lanes.
