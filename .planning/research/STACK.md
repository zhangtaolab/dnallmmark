# Stack Research

**Domain:** Public-release hardening toolchain for a research benchmark repo (offline Python/Node data scripts, GPU PyTorch pipeline, vanilla no-build JS MPA)
**Researched:** 2026-10-08
**Confidence:** HIGH — every version below was verified against primary sources on the research date (PyPI JSON API, npm registry API, GitHub Releases API, official tool docs). No version comes from training data. Practice-level recommendations are tagged individually.

**Repo facts this stack is fitted to** (from PROJECT.md + spot-check, not re-research): no manifests exist today (no `package.json`, `pyproject.toml`, `requirements.txt`); `script/get_task_performance.py` is stdlib-only; `script/summarize_comparison.py` needs numpy+pandas; `scripts/generate-tasks-index.js` is plain Node; pipeline needs `torch`+`dnallm` (GPU-only, excluded from CI by constraint); frontend is a hard no-build vanilla ES-module constraint; local dev machine runs Python 3.14.7 / Node 26.10.0.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pyproject.toml (PEP 621 + PEP 735 `[dependency-groups]`) | PEP 621 / PEP 735 (standard) | Single dependency manifest for a **non-package** repo | The 2025+ standard home for deps even when you ship no library. Mark it non-package with `[tool.uv] package = false` (uv docs: virtual projects are "not built or installed", only deps install). Groups (`data`, `dev`, `pipeline`) let CI install just the GPU-less subset — exactly the split this repo needs. **Confidence: HIGH** (PEP 735 support verified in uv and pip docs) |
| uv + uv.lock | 0.12.23 | Dependency resolution + lockfile; `uv sync` / `uv run` | One fast tool for venv+install+lock. `uv.lock` pins exact versions and only changes via explicit `uv lock --upgrade` — a reproducibility guarantee for a repo whose core value is "every number is reproducible". Verified: uv uses PEP 735 `[dependency-groups]` natively; `astral-sh/setup-uv` GitHub action is first-class (v10.2.0). **Confidence: HIGH** |
| pytest | 9.1.1 | Unit tests for `script/` data scripts | The uncontested Python test standard. 9.x (9.0.0 released 2025-11-05) requires Python >=3.10, supports config directly in `pyproject.toml`, and turns old deprecation warnings into errors by default — good for a fresh suite. Parametrize + `tmp_path` fixtures fit JSON-in/JSON-out script testing perfectly. **Confidence: HIGH** |
| Node.js `node:test` (built-in test runner) | Node 24 LTS (runner stable since Node 20) | Tests for `scripts/generate-tasks-index.js` | Zero new dependencies — the runner ships with Node. Verified Stability: 2 (Stable) since v20.0.0; `node --test` auto-discovers `**/*.test.js`; ESM `import test from 'node:test'` works. Nothing to configure, no runner dependency to rot. **Confidence: HIGH** |
| ruff | 0.16.10 | Python lint + format (one tool) | Replaces flake8+isort+pyupgrade+black with one Rust binary and one config in `pyproject.toml`. The ecosystem default for new Python setups; official `astral-sh/ruff-pre-commit` hook tracks the same version tag (v0.16.10 verified). For a review/hardening milestone, its lint pass doubles as a free static audit of the data scripts. **Confidence: HIGH** |
| ESLint (flat config) | 10.12.0 + `globals` 17.13.0 | Lint for the vanilla no-build JS MPA (`dnallm-mark/js/*.js`) | ESLint 10 is flat-config-only (`eslint.config.mjs`, eslintrc removed — verified against eslint.org migration guide). It lints plain browser-JS source files directly with **no bundler/build step** — `@eslint/js` recommended rules + `languageOptions.globals: {...globals.browser}` is all a no-framework MPA needs. Dev-only `package.json`; site files stay raw. **Confidence: HIGH** |
| html-validate | 11.16.2 | Offline HTML5 sanity check of the MPA in CI, no browser | Verified: an offline validator with CLI included in the npm package, rule-configurable via `.html-validate.json`. Catches the class of bug this repo already has (dead-on-load pages from missing/renamed DOM targets are adjacent to what element-presence rules catch; it will catch malformed/unclosed HTML and missing required elements). Runs in milliseconds, fits CI, needs no browser farm. **Confidence: HIGH for capability; MEDIUM for fit vs alternatives** |
| jsonschema (Python) | 4.26.0 | Validate leaderboard JSON data files in pytest | Keeps ONE test runner for the whole repo (Python data chain) — schema tests live next to the script tests as `test_data_integrity.py`. The repo's worst failure mode is silently-wrong derived JSON shipped to the leaderboard; schema tests make stale/corrupt derived files a CI failure. **Confidence: MEDIUM** (capability verified; the "prefer over ajv-cli" call is judgment, see Alternatives) |
| GitHub Actions | `actions/checkout@v7.0.1`, `actions/setup-python@v7.0.0`, `actions/setup-node@v7.1.0` — pinned to SHAs (below) | CI: tests + lint, GPU-less | Free for public repos on standard runners (official billing docs: usage is "free … for public repositories that use standard GitHub-hosted runners"). `setup-python` supports pip caching; v7 majors released July–Oct 2026 (verified via GitHub Releases API). **Confidence: HIGH** |
| pre-commit | 4.6.2 | Local developer gate (hygiene + ruff) | Standard hook manager; 4.x requires Python >=3.10. Keeps trivial defects (whitespace, merge markers, large files, bad JSON) out of review entirely. **Confidence: HIGH** |

**Action SHAs for pinning** (fetched 2026-10-08 from the repos' tag objects; GitHub's security guide: "Pinning an action to a full-length commit SHA is currently the only way to use an action as an immutable release"):

| Action | Tag | Full-length SHA |
|--------|-----|-----------------|
| actions/checkout | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| actions/setup-python | v7.0.0 | `5fda3b95a4ea91299a34e894583c3862153e4b97` |
| actions/setup-node | v7.1.0 | `949feb2413d6458794dcd2491c4babbbce0c15c1` |

### Dependency pins that protect the leaderboard numbers

| Package | Pin | Why |
|---------|-----|-----|
| pandas | `>=2.2,<3.0` (latest 2.x = 2.3.3) | **pandas 3.0.0 shipped 2026-01-21 with breaking changes** (default string dtype, copy-on-write default, microsecond datetime resolution, groupby unobserved-group changes). Unpinned installs now get 3.0.6 and can silently change aggregation outputs — the exact class of bug this milestone exists to prevent. Official pandas guidance is migrate via warning-free 2.3 first. A 3.x migration is a *post-release* task, not part of surgical fixes. **Confidence: HIGH** (official whatsnew verified) |
| numpy | `>=2.0,<3` (current line 2.5.3) | numpy 2.x is the stable ABI era; 2.5.3 requires Python >=3.12, so keep the floor where the known-good env sits. **Confidence: HIGH for versions; pin source below is the real rule** |
| Exact pins | **Export from the known-good data-generation environment** (`uv pip freeze` / `pip freeze`) | The authoritative pin is whatever produced the current leaderboard JSON on the maintainer's machine (system Python here has no pandas — the real env is elsewhere). Freeze that env into `uv.lock` / `requirements.txt`; do not adopt latest-for-latest's-sake during a correctness milestone. **Confidence: HIGH (process rule), version floor MEDIUM until env exported** |
| torch / dnallm | Group `pipeline`, NOT installed in CI | GPU-only, out of CI scope by constraint. Document in a `[dependency-groups]` group (or separate `requirements-pipeline.txt`) so the manifest still describes the full system. **Confidence: HIGH** |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-cov | 7.1.0 | Coverage reporting for `script/` | Optional; add to the CI pytest invocation only if coverage numbers would drive review decisions. Don't gate a milestone on a coverage threshold. |
| ajv-cli | 5.0.0 | JSON-schema validation, Node-side | ONLY if the repo publishes a submitter-facing JSON schema for the leaderboard submission flow. Otherwise keep validation in pytest (one runner). |
| @eslint/js | current (bundled with eslint install) | Recommended rule preset for flat config | Always — base of `eslint.config.mjs`. |
| pre-commit-hooks (repo `pre-commit/pre-commit-hooks`) | current | `trailing-whitespace`, `end-of-file-fixer`, `check-json`, `check-yaml`, `check-merge-conflict`, `check-added-large-files` | Always — cheap hygiene, and `check-json` catches corrupt derived JSON before commit. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| ruff via `astral-sh/ruff-pre-commit` | Lint+format hook | Pin hook rev to `v0.16.10` to match the CLI; hooks: `ruff` (lint, `--fix` optional) and `ruff-format`. |
| ESLint via npm script | `npx eslint dnallm-mark/js/` in CI | Flat config `eslint.config.mjs` at repo root; `ignores` for vendored/minified files if any. |
| html-validate via npm script | `npx html-validate dnallm-mark/**/*.html` in CI | Config `.html-validate.json`; start permissive (errors-only rules) and tighten — don't block release on stylistic HTML rules. |
| Internal-link check (custom `node:test` file) | Verify nav targets exist (the repo's 3-dead-pages bug class) | ~30-line test that parses `<a href>` targets and asserts a matching file/element — cheaper than any browser tooling and directly targets the known failure mode. **Confidence: MEDIUM (judgment)** |
| `uv pip freeze` export | Keep a `requirements.txt` for pip-only contributors | Regenerate on lockfile change; label it "generated — edit pyproject.toml". |

## Installation

```bash
# Python side (uv manages venv + deps from pyproject.toml)
pip install uv==0.12.23        # or: curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --group data --group dev

# JS side (dev-only tooling; no build step introduced)
npm install --save-dev eslint@10.12.0 globals@17.13.0 html-validate@11.16.2

# Local gate
pre-commit install

# Run checks
uv run pytest                                  # Python data-script tests + JSON schema tests
node --test                                    # Node data-script tests (generate-tasks-index)
npx eslint dnallm-mark/js/                     # MPA JS lint
npx html-validate "dnallm-mark/**/*.html"      # MPA HTML sanity
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| pyproject.toml + uv.lock | requirements.txt only (pip-tools `pip-compile`) | If maintainers firmly refuse new tooling: `requirements.in` → `pip-compile` still gives a lock; keep a `requirements.txt` export regardless for pip-only users. uv is faster and gives the cross-platform lockfile pip-tools can't. |
| pytest | stdlib `unittest` | Only under a zero-dependency constraint that doesn't apply here (CI already installs numpy/pandas). |
| ruff | black + flake8 + isort (separate) | Never for a new setup in 2026 — three configs/tools where one suffices. |
| `node:test` | vitest / jest | If the frontend ever gains a framework/build step (explicitly out of scope). vitest/jest add ~200+ deps of toolchain to lint three dozen vanilla ES modules — poor trade. |
| ESLint 10 | oxlint / Biome | Biome shines in TS/monorepo settings; oxlint is fast but smaller rule/plugin ecosystem. ESLint remains the interoperable default and matches the "boring, public-scrutiny-proof" goal. Revisit only if lint runtime ever matters. |
| html-validate | W3C NU Checker (`vnu.jar` / validator.w3.org/nu) | vnu is the reference validator and zero-config, but JVM startup is slow in CI and rule behavior is not configurable. Use vnu for a one-time conformance audit during review; html-validate for the recurring CI gate. **MEDIUM** |
| jsonschema-in-pytest | ajv-cli (npm) | If a schema must be published for the client-side submit flow / external submitters — then one schema serves CI and submitters via ajv. |
| Run pre-commit directly in CI job | `pre-commit/action` | Never prefer: its latest release is v3.0.1 from Feb 2024 (stale). `pip install pre-commit && pre-commit run --all-files` in the job is one fewer third-party action to pin. |
| SHA-pinned actions | Tag-pinned (`@v7`) | Only when SHA churn demonstrably hurts; GitHub's own security guidance says SHAs are the only immutable pin form. For a repo under public scrutiny post-release, SHA-pin. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Playwright/E2E browser tests | Explicitly out of scope by milestone decision; heavy to maintain for a static MPA; wrong layer for data-correctness risks | html-validate + jsonschema tests + internal-link `node:test` |
| jest / vitest / mocha for this repo | Heavyweight runners for ~4 vanilla ES-module files; contradict the no-build constraint's spirit; `node:test` is stable and built-in | `node --test` |
| JSHint | Effectively unmaintained (2.13.6, dormant for years); no modern ECMAScript coverage | ESLint 10 |
| `setup.py` / making the repo a pip package | It's an application/benchmark, not a library; packaging would demand layout changes (src/, build backend) violating surgical-fix discipline | `[tool.uv] package = false` virtual project |
| conda `environment.yml` | Fragments tooling (two package managers); nothing here needs conda-only binaries (torch env lives on the GPU machine) | pyproject + uv; document GPU env separately |
| tox / nox | Overkill for one Linux CI job with a straightforward matrix | GitHub Actions matrix directly |
| Unpinned pandas / unpinned deps in CI | pandas 3.0 (Jan 2026) silently changes aggregation semantics — numbers drift with no code change | `pandas>=2.2,<3.0` + lockfile |
| Floating action tags (`actions/checkout@v7`) | Tags are mutable; not an immutable release per GitHub security docs | Full-length SHA pins (table above) |
| black + flake8 + isort | Three tools, three configs, slower; ruff covers all in one | ruff 0.16.10 |

## Stack Patterns by Variant

**If the maintainer's known-good env turns out to run pandas 1.x or numpy 1.x:**
- Pin to the known-good line first, fix bugs, release; schedule version bumps as post-release maintenance with before/after data comparison (the milestone's reproducibility rule).

**If the leaderboard submission flow needs public validation rules:**
- Author ONE JSON Schema; wire ajv-cli into CI and reference it from `submit.js` — schema-as-single-source beats duplicated Python/JS validation (the repo already has a divergent-duplication bug in `js/data.js`).

**If CI minutes ever matter (they won't — public repo = free):**
- Drop the matrix to a single Python version; keep Node job (it's seconds).

## Version Compatibility

| Component | Requires / Notes |
|-----------|------------------|
| pytest 9.1.1 | Python >=3.10; config may live in pyproject.toml |
| pre-commit 4.6.2 | Python >=3.10 |
| uv 0.12.23 | Python >=3.8 (manages any 3.9+ runtime) |
| numpy 2.5.3 | **Python >=3.12**; use numpy 2.4.x line if CI must include 3.11 |
| pandas 2.3.3 | Python >=3.9 (last 2.x; safe pin target). pandas 3.0.6 needs >=3.11 — do not adopt this milestone |
| jsonschema 4.26.0 | Python >=3.10 |
| ESLint 10.12.0 | Node ^20.19.0 OR ^22.13.0 OR >=24 |
| html-validate 11.16.2 | Node ^22.22.0 OR >=24.8.0 |
| Node 24 (LTS "Krypton") | Active LTS now (maintenance phase starts 2026-10-20); Node 26 becomes LTS 2026-10-28; Node 22 EOL 2027-04-30. **Pin CI to Node 24** — satisfies every tool above |
| Recommended CI matrix | Python `["3.12", "3.13"]` on `ubuntu-latest` + one Node 24 job. (3.14 wheels for pinned pandas 2.3.x unverified — check before adding.) |

## Suggested CI Shape (for the roadmap, not prescriptive detail)

Two jobs, both on `ubuntu-latest`, workflow `permissions: contents: read`, SHA-pinned actions, `concurrency` group to cancel superseded runs:

1. **python**: setup-python (3.12/3.13 matrix) → install `data`+`dev` groups → `ruff check` → `pytest` (script unit tests + JSON-schema integrity tests).
2. **node**: setup-node 24 → `npm ci` (dev deps only) → `node --test` (generate-tasks-index + internal-link check) → `npx eslint dnallm-mark/js/` → `npx html-validate "dnallm-mark/**/*.html"`.

Public repo ⇒ standard runners are free (verified: GitHub billing docs). GPU pipeline and `dnallm` never enter CI.

## Release-adjacent decisions this stack assumes (flagged for roadmap)

- **LICENSE**: required pre-release. Recommend **Apache-2.0** (explicit patent grant; used by HELM/BIG-bench-style benchmark platforms) or MIT if maximal simplicity is preferred; if datasets are redistributed, pair code license with CC-BY-4.0 for data. **Confidence: MEDIUM — community-practice judgment, decide in planning.**
- **CITATION.cff**: GitHub renders it and gives "Cite this repository" — cheap win for a paper-linked benchmark. **Confidence: HIGH (stable GitHub feature).**

## Sources

- PyPI JSON API (pypi.org/pypi/{pytest,ruff,uv,pre-commit,pytest-cov,pandas,numpy,jsonschema,pip-tools,pip}/json) — latest versions + requires_python, fetched 2026-10-08 — **HIGH (primary registry)**
- npm registry (registry.npmjs.org/{eslint,html-validate,ajv-cli,globals,prettier,jshint,stylelint}/latest) — versions + engines — **HIGH (primary registry)**
- GitHub Releases/tag API — actions/checkout v7.0.1, setup-python v7.0.0, setup-node v7.1.0, cache v6.1.0, astral-sh/setup-uv v10.2.0, pre-commit/action v3.0.1 + full-length SHAs — **HIGH (primary)**
- pandas 3.0.0 whatsnew (pandas.pydata.org/docs/whatsnew/v3.0.0.html) — breaking changes, release date, 2.3-first migration path — **HIGH (official)**
- Node.js docs (nodejs.org/api/test.html) — node:test Stability: 2 since v20 — **HIGH (official)**
- nodejs/release schedule — Node 24 Active LTS, Node 26 LTS on 2026-10-28, Node 22 EOL 2027-04-30 — **HIGH (official)**
- docs.github.com — security-hardening (SHA pinning quote), billing (public repos free) — **HIGH (official)**
- eslint.org migration guide — flat config only, globals package pattern — **HIGH (official)**
- docs.astral.sh/uv — init (--no-package/--bare), dependency-groups (PEP 735), settings (`package = false`), lockfile behavior — **HIGH (official)**
- pip.pypa.io — `pip install --group` (PEP 735) documented in current pip (26.2.1) — **HIGH (official)**
- docs.pytest.org changelog — pytest 9.0.0 released 2025-11-05, Python >=3.10 — **HIGH (official)**
- html-validate.org usage — offline CLI validation — **HIGH (official capability claims); comparison vs vnu.jar is MEDIUM judgment**

---
*Stack research for: DNALLM-Mark public-release hardening*
*Researched: 2026-10-08*
