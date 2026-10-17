<!-- generated-by: gsd-doc-writer -->
# Contributing to DNALLM-Mark

DNALLM-Mark is a benchmark platform for evaluating DNA large language models across genomic prediction tasks — a PyTorch fine-tuning pipeline, offline data scripts, and a static leaderboard website. The core standard for every contribution: **each number on the public leaderboard is correct and reproducible from code an external reviewer can trust.** The rules below exist to protect that guarantee.

## Documentation map

| Doc | Covers |
|-----|-------|
| [README.md](README.md) | Overview, the fresh-clone reproduction chain, pipeline usage |
| [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) | Prerequisites and the shortest path to a running local leaderboard |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the three subsystems (web UI, data scripts, pipeline) fit together |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Local dev setup, `make` targets, code style, branch/PR conventions |
| [docs/TESTING.md](docs/TESTING.md) | The pytest and `node --test` lanes, test conventions, CI integration |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Dependency groups, configuration files, pipeline knobs |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | How leaderboard numbers are computed, from per-model results to Rank Score |
| [docs/ONBOARDING.md](docs/ONBOARDING.md) | Checklists for adding a new model or dataset to the benchmark |
| [docs/multi-gpu.md](docs/multi-gpu.md) | Multi-GPU sweep orchestration — sharding vs DDP decisions and the runbook |
| [docs/TUI-GUIDE.md](docs/TUI-GUIDE.md) | The `tui/` terminal console for driving benchmark runs |
| [DATA.md](DATA.md) | Generated dataset audit (N-frequency and non-ACGT census) |
| [AUDIT.md](AUDIT.md) | Published audit report (findings, migration records, secret-scan evidence) |

## Development environment

Prerequisites: **Python >= 3.13** (pinned by `.python-version` and `requires-python` in `pyproject.toml`), **Node.js >= 18** (a hard dependency of `make test` and `make data` — the Makefile guard prints the install hint if it is missing), [uv](https://docs.astral.sh/uv/), and Git. No GPU is needed for anything CI covers; `torch`/`transformers` live only in the `gpu` dependency group and are never installed in CI.

```bash
git clone https://github.com/zhangtaolab/dnallmmark.git
cd dnallmmark
uv sync
```

`uv sync` installs only the `data` dependency group (`pandas`, `numpy`, `scipy`, `evaluate` — exact pins in `uv.lock`). The dev tools (`pytest`, `ruff`, `ty`, `jsonschema`) are pulled automatically on demand: every `make` target invokes `uv run --group dev`, which auto-syncs the environment first. There is no activation step, and every target runs from the repository root.

See [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) for prerequisites and first-run instructions, and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for local development setup.

## Quality gates — required for every change

Each is a single command from the repo root. `make lint` and `make typecheck` must be **fully green**; for the test lane, run the suites relevant to your change and hold the full suite to the known-failure baseline below.

| Command | What it runs |
|---------|--------------|
| `make test` | Full suite: pytest (Python lane, slow tests included) plus `node --test tests/js/*.test.js` (JS lane, zero npm deps) |
| `make lint` | `ruff check` over `tests/` and the maintained source files in `script/`, `pipeline/`, `baseline/`, and `tui/` (ruff runs with default rules — there is no `[tool.ruff]` section in `pyproject.toml`) |
| `make typecheck` | `ty check` over `script/`, `baseline/`, `tests/`, `scripts/`, `pipeline/`, and `tui/` (config in `[tool.ty]` in `pyproject.toml`; GPU-side imports are type-checked as `Any` because they are never installed CPU-side) |

Useful variants:

- `make test-fast` — pytest excluding the `slow` marker (skips the long real-tree determinism run, and skips the Node-dependent golden tests when Node is absent).
- `make ci` — the pinned CI lane (`pytest -m ci`): golden replay, metric-key parity, species spot checks, aggregation units.

CI (`.github/workflows/ci.yml`) replays these on every pull request, plus two more lanes:

- **Static JS/HTML checks** — `node --check` on every JS file, `eslint@10.12.0` (flat config `eslint.config.mjs`, dependency-free exact-pin npx form: `npx --yes eslint@10.12.0 --config eslint.config.mjs "dnallm-mark/js/*.js"`), and `html-validate@11.16.2` over the six HTML shells.
- **Data drift** — see below.

### The known-failure baseline

The full suite currently carries a documented baseline of **7 known failures** on the reference machine — one `test_determinism` run, five `test_schemas` validations, and one `tests/tui/test_services_run_config.py` storage-overview check; several of these are machine/data-state dependent and may pass on a different box. They are pre-existing and tracked, and the bar for every pull request is **zero new failures**: if your run shows more failures than the baseline, the delta belongs to your change.

The nine TUI SVG goldens (`tests/tui/__snapshots__/`) are additionally pinned `xfail(strict=True)` pending maintainer regeneration, so they report as `xfailed` rather than failures — and an unexpected XPASS fails the suite. Do not regenerate the goldens or remove the markers in a PR; report render drift to the maintainers instead (see the TUI conventions below).

### The drift invariant

`make data` regenerates the entire derived-data chain (comparison aggregates, permutation tests, provenance, task index) from committed inputs. On an untouched tree it is a **byte-identical no-op**; the CI drift job runs `make data` and then `git diff --exit-code -- dnallm-mark/data/`, failing on any byte of drift. If your change intentionally alters derived data, regenerate and commit the full chain together with the input change:

```bash
make data
git status --porcelain dnallm-mark/data/ DATA.md   # must show only your intended changes
```

## Commit and PR expectations

- Pull requests target `main` (CI runs on pushes to `main` and on every PR). No branch-naming convention is enforced — keep branches short-lived and focused.
- Commit messages follow the conventional-commit style visible in the history: `type(scope): summary` with types `feat`, `fix`, `test`, `docs`, `chore`, where the scope names the area touched (e.g. `fix(tui): ...`, `feat(pipeline): ...`). Benchmark-data additions use an unscoped `data:` prefix (e.g. `data: add <model> model performance`).
- **Small, surgical diffs.** Fixes should not widen review surface with opportunistic refactors.
- `make lint` and `make typecheck` fully green, and the test lanes at the known-failure baseline (zero new failures), before opening the PR; CI must pass.
- Behavior changes come with tests. Regression prevention (data-script tests plus CI) is a core value of this repository — see [docs/TESTING.md](docs/TESTING.md) for conventions.
- **Data-affecting changes include a before/after comparison of the affected numbers in the PR description.** Recomputation of aggregated numbers is allowed and expected, but every change is documented with its delta.

## Adding a benchmark result

The leaderboard's source input is one JSON file per model at `dnallm-mark/data/model_performance/{model_name}_performance.json` — the filename minus `_performance.json` becomes the model's alias. Shape (full schema: `schemas/model_performance.json`, validated by `tests/test_schemas.py`):

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
        "Source__task": {
            "dataset": { "species": "plant", "type": "promoter", "labels": 2, "train": 10000, "test": 2000, "dev": 2000, "length": 200, "metric": "F1" },
            "parameters": { "epochs": 10, "batch_size": 32, "learning_rate": 1e-4 },
            "performance": { "f1": 0.85, "accuracy": 0.82, "auroc": 0.91, "FLOPs": 1234567890 }
        }
    }
}
```

Contract details that matter:

- Dataset keys use the `Source__task` convention (e.g. `GUE__emp_H3`).
- Missing metrics are **empty strings `""`**, never `null` or `0` — every consumer coerces defensively.
- The primary metric per dataset is declared as `dataset.metric` and resolved through the exporter-owned metric-key mapping (`script/export_runs.py`).

Then regenerate the derived data and commit input plus outputs together (a `data:` commit):

```bash
make data
git status --porcelain dnallm-mark/data/ DATA.md
```

Note: `dnallm-mark/data/task_performance/` is currently committed static data — `make data` does **not** refresh it; it is regenerated from run records by the unified exporter (`script/export_runs.py`).

Adding a new model or dataset to the pipeline registries (`pipeline/models_info.json`, `pipeline/datasets_info.json`) follows the CPU-only checklists in [docs/ONBOARDING.md](docs/ONBOARDING.md) — including the registry round-trip validation and the `run_sweep.py --dry-run` matrix check that prove the mechanics without launching any training.

**The DNALLM adaptation authority (registry rule).** Model downloads are ModelScope-first through the external [DNALLM](https://github.com/zhangtaolab/DNALLM) framework: its loader table (`MODEL_INFO`) is the single download authority, and the registry's default list may carry only **dnallm-adapted** models — models whose architecture dnallm has a registered loader for, with ModelScope IDs. A new model joins the default list only after dnallm itself carries its entry. Only dnallm-adapted models (currently 36 of the 59 registry entries) are downloadable through the operator console; the remaining entries are informational and still require manual weight placement into `pipeline/models/`. The verdicts live in the committed map `pipeline/dnallm_compat.json` — one entry per registry model: `dnllm_adapted`, the resolved ModelScope repo id, and the download channel. After any registry change, regenerate the map:

```bash
python script/audit_dnallm_compat.py   # reads a local read-only DNALLM clone (default ../DNALLM); runs from anywhere
```

The audit script is maintainer-executed — it needs the sibling DNALLM clone and never runs in CI — and `tests/test_dnallm_compat.py` pins the map's key set to the registry's, so a registry edit without a compat regen fails loudly.

## Web UI and TUI conventions

- **Web UI (`dnallm-mark/`)**: vanilla ES-module JavaScript — no build step, no framework, no npm dependencies. Chart.js and SheetJS load from CDN. One page-controller class per page, rendering via `innerHTML` template literals, all colors/fonts through CSS custom properties in `css/variables.css`. The UI must be served over an HTTP origin (`bash start-server.sh`); `file://` breaks ES-module loading. Architecture details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- **TUI (`tui/`)**: a Textual-based operator console launched with `make tui` (display-host runtime only — it needs the `gpu` group; never a CI lane). Six digit-keyed screens: slot 2 is the models screen (marks plus the committed dnallm-adaptation verdict and download-presence columns; the default list shows dnallm-adapted models only), slot 3 is the datasets screen with the persistent download queue. User-facing strings are centralized in `tui/strings.py` (UI copy is Chinese). The nine rendered-output goldens live in `tests/tui/__snapshots__/` and are compared by `make test` — currently under `xfail(strict=True)` pending maintainer regeneration; regenerating them (`make snapshot-update`, the only regeneration path) is a maintainer-only step, and the test lane must never rewrite goldens. See [docs/TUI-GUIDE.md](docs/TUI-GUIDE.md) and [docs/multi-gpu.md](docs/multi-gpu.md).

## Reporting issues

There are no issue templates yet. Open an issue at [GitHub Issues](https://github.com/zhangtaolab/dnallmmark/issues) and include:

1. Steps to reproduce (exact commands, run from the repository root where possible)
2. Expected behavior vs. actual behavior
3. Your environment: OS, Python and Node versions, and the relevant `make` output (`make test`, `make lint`, or `make typecheck`)

Questions and discussion: GitHub Discussions and the community Discord — links in the README's Contact section.

## License

- **Code** in this repository is licensed under the [MIT License](LICENSE) — Copyright (c) 2026 zhangtaolab and DNALLM-Mark contributors. By contributing code, you agree it will be licensed under MIT.
- **Derived leaderboard aggregates** produced by this repository (`dnallm-mark/data/model_performance/`, `dnallm-mark/data/task_performance/`, `models_comparison*.json`, `tasks.json`) are offered under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- **Upstream datasets are not redistributed.** They are downloaded from the Zenodo record linked in the README and remain under their original terms — do not commit dataset files.
