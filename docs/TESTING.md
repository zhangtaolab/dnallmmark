<!-- generated-by: gsd-doc-writer -->
# Testing

## Test framework and setup

The Python suite runs on **pytest** (floor `pytest>=9.1.1`, exact pin in `uv.lock`) with **pytest-asyncio** (`>=1.4,<2`) for the async Textual Pilot tests, and **jsonschema** (`>=4.26.0`) for schema-validation tests. All three live in the `dev` dependency group; Textual itself (`textual>=8.2,<9`) comes from the `tui` group. Configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`:

- `testpaths = ["tests"]` — plain `pytest` from the repo root collects the whole suite (`tests/` plus `tests/tui/`).
- `asyncio_mode = "auto"` — async tests (`App.run_test()` Pilot tests) need no per-test marker; sync tests are unaffected.
- Registered markers: `slow` and `ci` (see below).

Always invoke through `uv` with both groups — `uv`'s `default-groups` is `["data"]`, so a bare `uv run pytest` would lack pytest and textual:

```bash
uv run --group dev --group tui pytest
```

The JavaScript lane runs on Node's **built-in `node:test` runner** — zero npm dependencies, no `package.json`, no install step. It needs **Node.js >= 18** on PATH.

Two `conftest.py` files bootstrap the suite before any test module imports:

- `tests/conftest.py` — (1) pins BLAS/OpenMP thread pools to 1 (`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`) so numpy reductions are reproducible; (2) inserts `script/`, `baseline/`, and `pipeline/` on `sys.path` so modules like `summarize_comparison`, `compare`, and `run_sweep` import without packages.
- `tests/tui/conftest.py` — additionally inserts the repo root so the `tui` package imports package-qualified under plain pytest.

## Test lanes

All lanes are Makefile targets (run from the repo root; see `Makefile`):

| Command | What it runs |
|---|---|
| `make test` | Full suite: `uv run --group dev --group tui pytest` (slow lane included) **plus** `node --test tests/js/*.test.js` |
| `make test-fast` | `uv run --group dev --group tui pytest -m "not slow"` — the inner-loop lane; excludes the real-tree determinism regression |
| `make ci` | `uv run --group dev --group tui pytest -m ci` — exactly the pinned CI lane (a marker-selected subset of the same suite; no duplicated tests) |
| `make snapshot-update` | Maintainer-only regeneration of the TUI SVG goldens (see the snapshot contract below) |

`make test` and `make ci` are guarded by the **`check-node`** target: if `node` is missing, they fail immediately with an actionable message instead of a raw `Error 127`, because node is a hard dependency of both the JS test lane and the `tasks.json` golden tests. `make test-fast` needs no guard: `tests/test_golden.py` skips its node-dependent tests via `pytest.mark.skipif(shutil.which("node") is None, ...)`, so the fast lane is genuinely pytest-only on a node-less machine.

To run a subset directly:

```bash
# One Python module / one test
uv run --group dev --group tui pytest tests/test_aggregation.py
uv run --group dev --group tui pytest tests/test_sweep.py -k dry_run

# The JS lane, one file
node --test tests/js/data-api.test.js
```

## Pytest markers

| Marker | Meaning | Where it applies |
|---|---|---|
| `slow` | Long-running real-tree determinism regression; excluded by `make test-fast`, included by `make test` and plain `pytest` | `tests/test_determinism.py` |
| `ci` | The pinned CI lane: golden replay + metric-key parity + species spot checks + aggregation units | `tests/test_ci_replay.py`, `tests/test_export_runs.py`, `tests/test_known_defects.py`, `tests/test_aggregation.py` (module-level `pytestmark = pytest.mark.ci`) |

`tests/test_determinism.py` (the only `slow`-marked test) copies the 45 committed `model_performance` inputs plus the 47 committed `task_performance` files into a tmp tree, runs the regeneration chain (`script/summarize_comparison.py` + `scripts/generate-tasks-index.js`) twice as subprocesses, and asserts: the two runs are byte-identical, every regenerated output is byte-identical to its committed counterpart under `dnallm-mark/data/`, and the committed tree itself is untouched (`git status --porcelain` empty). Byte equality is claimed same-machine only.

## Test inventory

The Python suite collects **1,584 tests** (at time of writing) across three areas.

### Data-chain suites (`tests/test_*.py`, 27 modules)

CPU-only tests over the offline scripts and the committed data. Highlights:

- **Golden replay** — `tests/test_golden.py` runs the chain over the synthetic fixture tree (`tests/fixtures/synthetic_models/`, `tests/fixtures/synthetic_task_performance/`) and value-compares against committed goldens in `tests/fixtures/golden/` using `baseline/compare.py`'s `walk()`. `tests/test_ci_replay.py` replays the full export → aggregate chain end-to-end over the committed `tests/fixtures/e2_replay/` run-record fixture (3 models × 1 task × 3 seeds), asserting schema validity and byte-stability across repeated runs.
- **Determinism** — `tests/test_determinism.py` (the `slow` lane, described above).
- **Known-defect locks** — `tests/test_known_defects.py`: defects are pinned test-first as `xfail(strict=True)` tests (an unexpected XPASS fails the suite), and a defect's fix lands only together with the deliberate marker removal in the same commit. The three original locks (species-as-dataset, non-finite float pass-through in `get_float`, bool/int cross-type comparison in `compare.py`) have since been fixed and unmarked into permanent green contracts; the module now carries the species-table spot checks over the committed data.
- **Per-script unit suites** — aggregation units (`test_aggregation.py`), exporter contracts (`test_export_runs.py`), permutation engine (`test_permutation.py`), provenance emitter (`test_build_provenance.py`), dev splits (`test_dev_splits.py`), sweep driver and multi-GPU sharding (`test_sweep.py`, `test_sweep_shard.py`), registry converters and loaders (`test_convert_registry.py`, `test_registry_loader.py`, `test_registry_unification.py`, `test_model_registry.py`), snapshot primitive (`test_freeze_snapshot.py`), migration inventory (`test_migration_inventory.py`), frontier/VEP scripts (`test_frontier.py`, `test_zero_shot_vep.py`), committed-data schema validation (`test_schemas.py`), and vendored statistics parity (`test_vendored_stats.py`).
- **Pipeline modules without a GPU** — `tests/test_run_finetune_contracts.py` reads `pipeline/run_finetune.py` **as source text** (never imports it — `torch`/`dnallm` are unavailable CPU-side); `tests/test_flops_counter.py` tests `FlopsCounter` against CPU stub modules; `tests/test_env_smoke_bytes.py` and `tests/test_artifact_loader.py` pin their targets' byte/JSON contracts.

### TUI suites (`tests/tui/`)

- **Tier 1 — services** (`test_services_*.py`): pure-Python unit tests for the textual-free `tui/services/` layer (env check/gate/quick check, selection, templates, settings, registries, custom entries/validation, download queue, zenodo bundle, run config, sweep launcher, sweep monitor, gauntlet, about). `test_import_lock.py` enforces the layer invariant: no module under `tui/services/` imports `textual`.
- **Tier 2 — Pilot** (`test_pilot_*.py`): headless Textual `App.run_test()` suites that boot the real `DnallmMarkTui` with constructor-injected deterministic fakes (no filesystem, no clock, no network, no GPU) — boot, nav shell, selection (+ custom entries), matrix, data manager, run config, monitor, env check, wizard.
- **Snapshots** — `test_snapshots.py`: the SVG golden corpus (below).
- Plus `test_gen_progress.py` (web-mirror generator goldens) and `test_strings_phase11.py` (string-inventory tripwire).

### JavaScript lane (`tests/js/`, 6 files, zero npm deps)

`node:test` suites over the frontend modules, loaded via `require(esm)`: `data-api.test.js` (DataAPI surface + memoization), `data-escape.test.js` (`escapeHTML`), `generate-tasks-index.test.js` (the tasks.json index generator), `main-topn-filter.test.js` and `main-view-toggle.test.js` (`dnallm-mark/js/main.js` behavior), `progress-page.test.js` (the sweep-progress web mirror, DOM-less).

## The TUI snapshot contract

`tests/tui/test_snapshots.py` compares eight committed SVG screenshots of the console screens against live headless exports using Textual core's `App.run_test(size=(120, 40))` + `App.export_screenshot()` and plain UTF-8 string equality. The plugin-based alternative (`pytest-textual-snapshot`) is resolver-blocked against this repo's `pytest>=9.1.1` floor, so no snapshot plugin is installed — `pytest --snapshot-update` does **nothing** here.

The eight committed goldens in `tests/tui/__snapshots__/`: `env_check`, `selection_models`, `selection_datasets`, `data_manager`, `run_config`, `monitor_running`, `monitor_empty`, `wizard`.

Rules of the contract:

- **`make snapshot-update` is the ONLY regeneration path** (it runs `python tests/tui/test_snapshots.py --regenerate` under `uv run --group dev --group tui`). It is **maintainer-only**: after any regeneration, review every changed SVG in a browser/editor and commit the refreshed files together with the change that drifted the render.
- **CI compares, never regenerates** — `make test` goes red on drift; the test lane's environment has no write path to the goldens.
- Every golden exports at the single design-grid size 120×40, from frozen fixtures (pinned timestamps, scripted stats, cursor blink disabled, static spinner glyph) so the export is byte-deterministic.
- Two non-vacuousness tests keep the compare honest: `test_golden_export_is_deterministic_across_instances` (two independent app instances export byte-identical SVGs) and `test_golden_compare_is_sensitive_to_fixture_state` (different fixture states export distinct SVGs).

## Writing new tests

- **File naming**: `tests/test_*.py` (data chain), `tests/tui/test_*.py` (TUI — tier-1 service suites named `test_services_*.py`, tier-2 Pilot suites `test_pilot_*.py`), `tests/js/*.test.js` (JS). No `__init__.py` anywhere under `tests/`.
- **Imports**: `script/`, `baseline/`, `pipeline/`, and the repo root are already on `sys.path` via the two conftest files — import siblings directly (`import summarize_comparison`, `from tui.app import DnallmMarkTui`). Do not add per-module path hacks.
- **Pipeline modules**: never import `pipeline/run_finetune.py` (its module level pulls `torch`/`dnallm`). Read it as source text (the `test_run_finetune_contracts.py` pattern) or test CPU-importable siblings (`flops_counter.py`, `registry_loader.py`, `artifact_loader.py`, `run_sweep.py`, `env_smoke.py`).
- **TUI tests**: follow the constructor-injection seam — build the real app/screen with deterministic fakes for every service; no wall-clock reads, filesystem scans, network, or GPU inside a test. Async Pilot tests run without markers under `asyncio_mode = "auto"`.
- **Defect pinning**: new confirmed defects get `xfail(strict=True)` with the finding ID in the reason string; the fix must land in the same commit that removes the marker.
- **JS tests**: plain `node:test` + `node:assert`, `require(esm)` for the ES modules, no npm dependencies. `make test` picks up new `tests/js/*.test.js` automatically via the glob.
- **New lanes**: lint scope for new Python files is an explicit list in the `Makefile` `lint` target — new pipeline/tui files join via the existence-guard variables (`PHASE6_SCRIPTS`, `PHASE7_MODULES`, `PHASE8_TUI`, `PHASE12_MODULES`) or an explicit path; ty scope is `[tool.ty.src]` in `pyproject.toml`.

## Coverage

No coverage threshold configured. There is no coverage tooling in any dependency group; the project's integrity gate is the CI **data drift job** (below), which enforces byte-identical regeneration of the committed data tree rather than a coverage percentage.

## CI integration

CI lives in `.github/workflows/ci.yml` (workflow name **CI**), triggered on `push` to `main` and on every `pull_request`, with top-level `permissions: contents: read` and a 14-minute timeout per job. Four jobs:

| Job | What it runs |
|---|---|
| `lint-typecheck` | `make lint` (ruff) + `make typecheck` (ty) |
| `test` | `make test` on a Python matrix — **3.13** (the required floor, `requires-python >= 3.13`) and **3.14** (forward-compat probe, `continue-on-error` so it cannot block); Node 24 is installed because `make test` includes the JS lane |
| `static-js` | `node --test tests/js/*.test.js`; `node --check` on every `dnallm-mark/js/*.js` and `scripts/*.js`; exact-version pinned `npx --yes eslint@10.12.0` (flat config `eslint.config.mjs`) over `dnallm-mark/js/*.js`; `npx --yes html-validate@11.16.2` (`.htmlvalidate.json`) over the six real HTML shells |
| `drift` | `make data` (regenerates the derived data chain) then `git diff --exit-code -- dnallm-mark/data/` — regeneration must be a **byte-identical no-op** on a clean checkout |

The `test` job runs the full `make test` (including the `slow` lane), not the `make ci` subset; `make ci` exists as the locally reproducible pinned-lane equivalent for pre-push verification.

## What is deliberately not tested in CI

- **The GPU fine-tuning pipeline.** The `gpu` dependency group (`torch==2.11.0`, `transformers==5.17.0`, resolved from the cu130 index) is never installed in CI, and no CI job runs training. Pipeline code is covered CPU-side via source-contract tests, CPU stubs, and the stdlib-only sweep drivers.
- **The external `dnallm` package.** It is deliberately absent from every dependency group (installed from a local dev clone only when GPU runs resume). Tests that would need it import nothing from it — pipeline modules with GPU imports are read as text or exercised through CPU-importable siblings.
- **The Textual display runtime.** `make tui` (the interactive console) is a local display lane; CI knows textual only as a library inside `make test`'s headless Pilot tests.

See [docs/ARCHITECTURE.md](ARCHITECTURE.md) for the subsystem map and [docs/CONFIGURATION.md](CONFIGURATION.md) for environment, group, and Makefile-target details.
