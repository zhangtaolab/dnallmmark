<!-- generated-by: gsd-doc-writer -->
# Configuration

This document describes every configuration surface in DNALLM-Mark: the uv-managed Python environment and its dependency groups, the Makefile entry points, the pipeline YAML configs and CLI flags, environment variables, TUI XDG directories, and the CI workflow lanes. All configuration is file-based — the project uses no `.env` files and no secret manager; nothing in the repo requires credentials to run.

## Python environment

| File | Role |
|------|------|
| `pyproject.toml` | PEP 621 virtual project (`[tool.uv] package = false`) + PEP 735 `[dependency-groups]` + `pytest`/`ty` tool config |
| `.python-version` | Pins the data-chain Python to `3.13` (uv reads this for `uv venv`/`uv sync`) |
| `uv.lock` | Committed lockfile — exact pins for every group |
| `requirements.txt` | PIP-compatible export of the `data` group only (`uv export --group data --no-emit-project`) |

`requires-python = ">=3.13"` is the project floor; `3.13` is the pinned data-chain interpreter.

### Dependency groups

`[tool.uv] default-groups = ["data"]`, so a plain `uv sync` installs **only** the data chain. Nothing is installed unless a lane names its group.

| Group | Contents | Purpose |
|-------|----------|---------|
| `data` (default) | `pandas>=2.2,<3.0`, `numpy>=2.0,<3`, `scipy>=1.15.2`, `evaluate>=0.4.6` | Offline data scripts (`script/*.py`) and the aggregation/statistics layer |
| `dev` | `jsonschema>=4.26.0`, `pytest>=9.1.1`, `ruff>=0.16.10`, `ty>=0.0.85`, `pytest-asyncio>=1.4,<2` | Test harness, lint, and type check — never a runtime need |
| `gpu` | `torch==2.11.0`, `transformers==5.17.0` | Fine-tuning pipeline only; **never installed by `uv sync` defaults or in CI** |
| `tui` | `textual>=8.2,<9`, `platformdirs>=3.6,<5`, `jsonschema>=4.26.0` | The operator console (`python -m tui`) and its headless tests |

The external `dnallm` package is deliberately absent from every committed group. It is installed manually into the venv from a local dev clone (documented in `pyproject.toml` comments as `../DNALLM`, branch `revision`) when pipeline runs resume; the CI and data lanes never import it.

### Torch wheel index

`pyproject.toml` declares an explicit uv index so GPU torch resolves to CUDA 13.0 wheels:

```toml
[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
explicit = true
```

`explicit = true` confines this index to packages whose `[tool.uv.sources]` entry names it — only `torch` here (Linux/Windows markers). Everything else, including `transformers`, stays on PyPI.

### uv sync lanes

The Makefile is the single entry point; `uv run` auto-syncs `.venv` from `uv.lock` before invoking. The group combinations in use:

| Lane | Command under the hood | Groups installed |
|------|------------------------|------------------|
| `make data` | `uv run --group data python script/...` + `node scripts/generate-tasks-index.js` | `data` |
| `make test` | `uv run --group dev --group tui pytest` + `node --test tests/js/*.test.js` | `dev`, `tui` |
| `make test-fast` | `uv run --group dev --group tui pytest -m "not slow"` | `dev`, `tui` |
| `make ci` | `uv run --group dev --group tui pytest -m ci` | `dev`, `tui` |
| `make lint` | `uv run --group dev ruff check ...` | `dev` |
| `make typecheck` | `uv run --group dev --group tui ty check` | `dev`, `tui` |
| `make tui` | `uv run --group tui --group gpu python -m tui` | `tui`, `gpu` (display host only) |

`--group dev` is always explicit because `default-groups = ["data"]` replaces uv's built-in `["dev"]` default. The `UV` variable is overridable (`make UV=/path/to/uv`) for non-`~/.local/bin` installs.

## Makefile targets

| Target | What it does |
|--------|--------------|
| `make data` | Regenerates the derived data chain: `script/summarize_comparison.py` (run with CWD = `dnallm-mark/data/`), `script/permutation_tests.py` and `script/build_provenance.py` (repo-root-relative), then `node scripts/generate-tasks-index.js` |
| `make test` | Full suite: pytest including the `slow` lane, plus the `node:test` JS suite over `tests/js/` |
| `make test-fast` | pytest excluding `@slow` tests; the JS lane does not run |
| `make ci` | The pinned CI selection via the `ci` pytest marker (golden replay, metric-key parity, species spot checks, aggregation units) |
| `make lint` | `ruff check` over `tests/` plus the explicit fixed-findings file list (existence-guarded phase lists in the Makefile) |
| `make typecheck` | `ty check` over `script/`, `baseline/`, `tests/`, `scripts/`, `pipeline/`, `tui/` |
| `make snapshot` | Freeze the committed derived-data set into `baseline/snapshots/` (tar + SHA256 manifest); commit hash read from the committed `manifest.json` `generated_from` field, never a live git call |
| `make snapshot-update` | Regenerate the TUI SVG golden corpus (`tests/tui/__snapshots__/*.svg`); maintainer-only — the test lane compares against these files and must never rewrite them |
| `make tui` | Launch the operator console (`python -m tui`) with the `tui` + `gpu` groups |
| `make check-node` | Guard target: fails with an actionable message when `node` is absent (it is a hard dependency of `make data` and `make test`) |

Node >= 18 is required for `make data` and `make test` (the tasks.json index generator and the JS goldens); `make test-fast` is the pytest-only escape hatch and skips node-dependent tests.

## Pipeline configuration

### YAML config files

All pipeline hyperparameters live in `pipeline/` YAML files following the `transformers.TrainingArguments` schema under a `finetune:` key, plus a `task:` key and LoRA/IA3 sections. They are loaded via `load_config()` from the external `dnallm` package.

| File | Selected via | Differences from base |
|------|--------------|----------------------|
| `pipeline/finetune_config.yaml` | default (no flag) | Base config: `task_type: binary`, 3 epochs, `per_device_train_batch_size: 8`, lr `2e-5`, `bf16: True`, `report_to: "tensorboard"`, seed 42, logging/eval/save every 500 steps |
| `pipeline/finetune_config_with_head.yaml` | auto-reload for `special_models` (`evo2_1b_base`, `megaDNA_updated`) or `--config-variant head` | Adds `task.head_config` (custom head: `mlp`/CNN/LSTM/U-Net fields); batch size 48, `bf16: False`, logging 100 / save 200 steps, `save_total_limit: 20` |
| `pipeline/finetune_config_probe.yaml` | `--config-variant probe` | Frozen backbone (`head_config.frozen: true`) with a single-layer MLP head (`hidden_dims: [512]`); generic-path models only; save name defaults to `{model}+probe` |
| `pipeline/finetune_config_curve.yaml` | `--config-variant curve` | Dense checkpoint cadence for learning curves: logging 50 / eval 100 / save 100 steps; save name defaults to `{model}+curve` |

Every variant carries the same `lora:` and `ia3:` sections as the base config (suite-default values), because the `lora:` section is required whenever the trainer is built with `use_lora=True`. Model-behavior registries (`model_not_use_safetensors`, `deeplearning_models`, `models_no_char_n`, `models_with_limited_length`, `models_only_support_fp32`) are hardcoded lists inside the `__main__` block of `pipeline/run_finetune.py` — new model quirks are added there. The custom-head auto-reload is a separate inline membership check (`if model_name in ["evo2_1b_base", "megaDNA_updated"]:`) in the model loop.

### `run_finetune.py` CLI flags

Run from `pipeline/` (`python run_finetune.py ...`):

| Flag | Default | Purpose |
|------|---------|---------|
| `--target_model` | None | Single model to train (key from `models_info.json`) |
| `--target_dataset` | None | Dataset(s), comma-separated |
| `--batch_size` | 1 | Manual batch size |
| `--max_token_len` | None | Manual token-length cap for single-base tokenizers on extra-long sequences |
| `--auto_batch_size` | off | Adjust batch size automatically from model size |
| `--gradient_checkpointing` | off | HF gradient checkpointing (memory for compute) |
| `--ddp_find_unused_parameters` | off | Force DDP `find_unused_parameters=True` (MoE models under torchrun) |
| `--cache_dir` | None | Sets `HF_HOME`/`MS_CACHE_HOME`; overrides env vars; fallback default `../../cache` relative to the script |
| `--seed` | 9527 | Random seed (scopes the output directory: `seed_{seed}/`) |
| `--gpu_memory` | None | Override detected GPU memory in GB |
| `--mem_ratio` | 0.70 | Target GPU memory usage ratio (0.0–1.0) |
| `--effective_batch_size` | None | Target `batch_size * gradient_accumulation_steps`; GA adjusted child-side |
| `--output_dir` | `./finetuned` | Custom output root |
| `--save_model_name` | None | Override the model name used in the output path (how alias lanes write `{model}+lora` etc.) |
| `--num_train_epochs` | None | Epoch override (the YAML value governs when absent) |
| `--category` | None | Filter datasets by category, comma-separated (e.g. `Plants,Animals,Microbe`) |
| `--task_index` | None | Filter datasets by registry index, comma-separated |
| `--subset_file` | None | JSON mapping dataset names to test-split row IDs (e.g. `pipeline/eval_subsets.json`); restricts TEST to identical rows across models |
| `--remove_pt` | off | Remove `.pt` files in checkpoints |
| `--remove_checkpoints` | off | Remove all checkpoint dirs except the last |
| `--peft` | `none` | `lora` / `ia3` parameter-efficient lanes (choices: `none`, `lora`, `ia3`) |
| `--peft_dry_run` | off | Validate adapter config and exit — no training |
| `--config-variant` | None | `head` / `probe` / `curve` — selects the variant YAML above |
| `--train_fraction` | None | Restrict the TRAIN split to a fraction (0 < f <= 1), seed-governed shuffle-then-select; output nests under `seed_{seed}/frac_{f}/` |

A dataset run is skipped when `trainer_state.json` already exists in its output dir (resume-safe by convention).

### `run_sweep.py` CLI flags

Drives the model x task x seed matrix, one `run_finetune.py` subprocess per cell:

- `--seeds` — **required**; comma-separated integers, one seed-isolated outdir per seed
- `--models`, `--tasks` — comma-separated filters (default: all registry keys / all entries with truthy `Train`)
- `--output-root` (default `./finetuned`), `--registry-dir` (default: the script's own directory)
- `--dry-run`, `--priority-file` (ordered-tiers JSON, e.g. `pipeline/sweep_priorities.json`), `--from-failures` (re-run exactly a `sweep_failures.json` manifest)
- `--peft`, `--config-variant`, `--curve` (train fractions, e.g. `0.25,0.5,1.0`), `--subset_file`, `--effective_batch_size`, `--num_train_epochs`, `--cache_dir` — all threaded to every child; `--peft`/`--config-variant` lanes enumerate cells under alias model names (`{model}+lora`, `{model}+probe`, ...)

### `run_sweep_shard.py` multi-GPU flags

Orchestrates N `run_sweep.py` workers over disjoint model shards, one GPU each (`pipeline/run_sweep_shard.py`; see `docs/multi-gpu.md` for the full runbook):

| Flag | Default | Purpose |
|------|---------|---------|
| `--workers` | 1 | Number of parallel workers; models are LPT-sharded by registry size into exactly this many disjoint shards |
| `--gpus` | `0..workers-1` | Comma-separated GPU ids, one per worker (e.g. `"0,1"`); each value is passed verbatim as that worker's `CUDA_VISIBLE_DEVICES` — decimal index, GPU UUID, or MIG instance id; arity-validated only |
| `--models` | None | Comma-separated model names to shard (**required** in launch mode; must exist in the models registry) |
| `--output-root` | `./finetuned` | Worker i writes under the frozen sibling root `{base}-mgpu-w{i}` with a tee log at `{base}-mgpu-w{i}-{launch-stamp}.log`; shared roots are forbidden |
| `--dry-run` | off | Each worker writes only its planned `sweep_manifest.json` — the CPU-side disjointness proof |
| `--merge` | off | Merge mode: instead of launching, read the frozen worker roots `{output-root}-mgpu-w{0..N-1}` and merge them into `--output-root` (copy data artifacts with SHA256 verify; write the union manifests). Takes no sweep flags and no `--models` |
| `--include-checkpoints` | off | Merge-mode escape hatch: also copy `checkpoint-*/` trees and `runs/` verbatim |

Every unrecognized token on the command line is passed through verbatim to each worker's argv (`run_sweep.py` owns sweep-flag validation) — except in merge mode, where the remainder must be empty.

## Environment variables

No environment variable is required to start anything. All have code-level defaults or are pure overrides:

| Variable | Where | Default / behavior |
|----------|-------|--------------------|
| `HF_HOME` | `pipeline/run_finetune.py` (module top) | Set from `--cache_dir` argv pre-scan; else kept if already set; else defaulted to `../../cache` relative to the script. Must be set before `huggingface_hub` import |
| `MS_CACHE_HOME` | `pipeline/run_finetune.py` | Set alongside `HF_HOME` with the same value |
| `GPU_MEMORY_GB` | `pipeline/run_finetune.py` GPU/NPU memory detection | Overrides detected device memory when `--gpu_memory` is absent |
| `CUDA_VISIBLE_DEVICES` | set per worker by `run_sweep_shard.py` | One verbatim `--gpus` token per worker |
| `DNALLMMARK_CUSTOM_REGISTRY_DIR` | `pipeline/registry_loader.py` | Overrides the entire user custom-registry directory; empty value treated as unset |
| `XDG_CONFIG_HOME` | `pipeline/registry_loader.py` | When set, custom registries resolve to `{XDG_CONFIG_HOME}/dnallmmark`; else `~/.config/dnallmmark` |
| `DNALLMMARK_TUI_STATE_DIR` | `tui/services/settings.py` | Overrides the entire TUI state root (empty value = unset) |
| `DNALLMMARK_TUI_CONFIG_DIR` | `tui/services/settings.py` | Overrides the entire TUI config root (empty value = unset) |
| `WORLD_SIZE`, `LOCAL_RANK` | `pipeline/run_finetune.py` DDP scaffolding | Read with `"1"`/`"0"` defaults; consumed only by a future torch-run wrapper |

## TUI XDG state and config

The operator console (`make tui`, `python -m tui`) resolves every user-local read/write through `tui/services/settings.py` (the platformdirs library, app name `dnallmmark`). Two roots, never mixed:

| Root | Resolution | Contents |
|------|-----------|----------|
| XDG STATE — Linux `~/.local/state/dnallmmark` | `platformdirs.user_state_dir("dnallmmark")`, whole-dir overridable via `DNALLMMARK_TUI_STATE_DIR` | Regenerable machine state: `env_check.json` (environment check results), `run_config.json` (the run-config screen's own selection + params + dirs, schema_version 1) |
| XDG CONFIG — Linux `~/.config/dnallmmark` | `platformdirs.user_config_dir("dnallmmark")`, whole-dir overridable via `DNALLMMARK_TUI_CONFIG_DIR` | User-owned hand-authored files: `presets.json` (saved selection presets), `custom_models.json` / `custom_datasets.json` (the custom registry overlay — the same root `pipeline/registry_loader.py` reads) |

All persistence writes go through `settings.atomic_write()` (tmp sibling + `os.replace`), so readers never observe torn files; the roots are created on demand at first write.

## Tool configuration files

| File | Tool | Notes |
|------|------|-------|
| `[tool.pytest.ini_options]` in `pyproject.toml` | pytest | `testpaths = ["tests"]`, `asyncio_mode = "auto"`, markers `slow` (real-tree determinism regressions, excluded by `make test-fast`) and `ci` (the pinned `make ci` lane) |
| `[tool.ty.*]` in `pyproject.toml` | ty type checker | `python-version = "3.13"`, `extra-paths = ["script", "baseline", "pipeline", "."]`, `replace-imports-with-any` for GPU-side imports (`torch.**`, `dnallm.**`, `transformers.**`, `peft.**`, `datasets.**`, `torch_npu.**`, `evaluate.**`), src includes `script`, `baseline`, `tests`, `scripts`, `pipeline`, `tui` |
| (none) | ruff | No `[tool.ruff]` section exists — scope is the explicit file list in `make lint` |
| `eslint.config.mjs` | ESLint 10 (flat config, run via exact-version `npx` in CI) | Frontend JS checks; zero npm deps committed |
| `.htmlvalidate.json` | html-validate 11 (run via exact-version `npx` in CI) | The six real HTML shells |
| `.gitleaks.toml` | gitleaks | Secret-scanning allowlist config |
| `schemas/*.json` | jsonschema | Committed data contracts (`run_template.json`, `flops_report.json`, `model_performance.json`, `custom_registry.json`, and others) validated by the dev-group test suite |

## CI workflow lanes

`.github/workflows/ci.yml` — name `CI`, triggered on `push` to `main` and on `pull_request` (`pull_request_target` is forbidden). Top-level `permissions: contents: read`; every job carries `timeout-minutes: 14`; every `uses:` action is pinned by full 40-char commit SHA; no job references any secret.

| Job | Steps |
|-----|-------|
| `lint-typecheck` | checkout → `astral-sh/setup-uv` → `make lint` → `make typecheck` |
| `test` | matrix Python `3.13` (required floor) / `3.14` (forward-compat probe, `continue-on-error`); checkout → setup-uv (matrix python) → Node 24 → `make test` |
| `static-js` | checkout → Node 24 → `node --test tests/js/*.test.js` → `node --check` over every `dnallm-mark/js/*.js` and `scripts/*.js` → `npx --yes eslint@10.12.0` → `npx --yes html-validate@11.16.2` |
| `drift` | checkout → setup-uv → Node 24 → `make data` → `git diff --exit-code -- dnallm-mark/data/` (regeneration must be a byte-identical no-op on a clean checkout) |

The `gpu` group and the `dnallm` package are never installed in any CI job — GPU work stays on the workstation lanes only.

## Required vs optional summary

- **Hard requirements:** Python >= 3.13 (`.python-version` pins 3.13 for the data chain), uv (with the committed `uv.lock`), Node >= 18 for `make data`/`make test`.
- **Pipeline-only:** the `gpu` group plus a manually installed `dnallm` and a CUDA GPU; local `pipeline/models/` and `pipeline/datasets/` (gitignored, downloaded externally per `README.md`).
- **Everything else is optional with defaults:** every environment variable in the table above, every YAML value overridable via CLI flags, and every TUI XDG root auto-created on first write.
- **Per-environment overrides:** there are no `.env.development`/`.env.production` files and no `NODE_ENV`-style switching. Environment separation is achieved structurally — CI runs CPU-only lanes (`make ci`, `make lint`, `make typecheck`), the workstation runs `make tui`/pipeline lanes with the `gpu` group, and user-specific state is isolated in the XDG roots (overridable per machine via the `DNALLMMARK_*` environment variables).
