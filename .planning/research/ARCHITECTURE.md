# Architecture Research

**Domain:** Test/CI/release-quality infrastructure layered onto an existing static-MPA + offline-data-pipeline benchmark repo (brownfield hardening)
**Researched:** 2026-10-08
**Confidence:** HIGH for codebase facts (verified by direct inspection of this repo at `a44d310`), MEDIUM for ecosystem patterns (cross-verified web/official-docs sources)

## Standard Architecture

The quality layer does not sit beside the three existing subsystems — it **wraps** them. Tests point at code and data that already exist; CI points at the repo; the task runner points at the regeneration chain. Nothing in the existing runtime architecture (browser → static JSON → offline scripts → pipeline) changes; the new components are all read-only observers except the gated regeneration path.

### System Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                     QUALITY / VERIFICATION LAYER (new)                    │
│                                                                          │
│  ┌────────────────────────┐  ┌───────────────────┐  ┌────────────────┐   │
│  │ GitHub Actions CI      │  │ Makefile          │  │ schemas/       │   │
│  │ .github/workflows/     │  │ (entry points:    │  │ JSON Schema    │   │
│  │  lint → test →         │  │  data, test,      │  │ data contracts │   │
│  │  verify-data jobs      │  │  lint, check)     │  │                │   │
│  └──────────┬─────────────┘  └─────────┬─────────┘  └───────┬────────┘   │
│             │ calls make targets       │ shells into        │ validates  │
│  ┌──────────┴──────────────────────────┴─────────────────────┴────────┐   │
│  │                      tests/ (pytest)                               │   │
│  │   unit tests (pure functions)  ·  golden-file tests (synthetic     │   │
│  │   fixture trees in tmp_path)   ·  data-contract tests (schema-     │   │
│  │   validate every committed JSON)  ·  determinism test              │   │
│  └──────────┬───────────────────────────────┬─────────────────────────┘   │
├─────────────┼───────────────────────────────┼─────────────────────────────┤
│             ▼ imports (guarded modules)     ▼ reads/writes via scratch   │
│  ┌──────────────────────────┐  ┌─────────────────────────────────────┐   │
│  │ Offline data scripts     │  │ Committed JSON data                 │   │
│  │ script/*.py (2)          │→ │ dnallm-mark/data/                   │   │
│  │ scripts/generate-*.js    │  │  model_performance/   (source of     │   │
│  └──────────────────────────┘  │  truth, ~42 files, ~2.1 MB)          │   │
│                                │  task_performance/ + tasks.json +    │   │
│                                │  models_comparison*.json (DERIVED)   │   │
│                                └─────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ Fine-tuning pipeline (pipeline/) — OUT OF TEST SCOPE              │    │
│  │ CI never imports it; guarded by "no torch/dnallm in CI deps"      │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

Key boundary rule: **tests and CI never write to committed data.** The only writer of `dnallm-mark/data/` derived files is a maintainer (or CI scratch dir) running the regeneration chain through the Makefile. Derived-data freshness is *proven*, not assumed, by regenerating into a scratch copy and diffing.

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Unit tests | Verify aggregation math in pure functions (`get_float`, `calculate_dataset_stats`, `to_singular_species`, `aggregate_models` in `script/summarize_comparison.py:80-268`) | pytest, plain-dict fixtures mirroring the performance-JSON shape |
| Golden-file tests | Verify whole-script I/O: synthetic `model_performance/` tree → run script `main()` → byte/parse-compare outputs against committed goldens | pytest + `monkeypatch.chdir(tmp_path)`; goldens in `tests/data/golden/` |
| Data-contract tests | Validate every committed JSON against a schema encoding the documented contract | pytest + `jsonschema`, parametrized over `dnallm-mark/data/**.json` (alternative: `check-jsonschema` CLI / pre-commit) |
| Determinism test | Run the chain twice (and/or with shuffled directory order), assert byte-identical output | pytest + `tmp_path`, two runs |
| Task runner | Single discoverable entry point for the regeneration chain and all checks; encodes the CWD contract (`cd dnallm-mark/data`) | `Makefile` with `.PHONY` targets (`data`, `verify-data`, `test`, `lint`, `check`) |
| CI workflow | Fail PRs on lint errors, test failures, schema violations, or stale derived data — without GPU/dnallm | GitHub Actions: `lint` + `test` + `verify-data` jobs, path filters, `permissions: contents: read` |
| JSON Schemas | Machine-readable statement of the pipeline→scripts→UI data contract; reusable for external submitters | JSON Schema draft 2020-12 files in `schemas/` |
| Static frontend checks | Syntax-level safety net for the no-build MPA: parse every ES module, lint every HTML page | `node --check` loop over `git ls-files '*.js'` (needs `"type":"module"` in `package.json`), `htmlhint` |

## Recommended Project Structure

```text
dnallmmark/
├── Makefile                        # canonical entry points (see Pattern 5)
├── pyproject.toml                  # numpy/pandas bounds + pytest config + ruff config
│                                   #   (single manifest; requirements.txt only if generated)
├── package.json                    # {"type":"module"} + devDependencies: htmlhint
│                                   #   minimal — enables ESM parsing, adds NO build step
├── schemas/
│   ├── model_performance.schema.json    # contract for the ~42 source files
│   ├── task_performance.schema.json     # contract for the ~47 pivot outputs
│   ├── models_comparison.schema.json    # contract for leaderboard files (incl. _animal/_plant/_microbe)
│   └── tasks_index.schema.json          # contract for tasks.json
├── tests/
│   ├── conftest.py                 # fixture-tree factory, real-data path helpers
│   ├── test_summarize_comparison.py # unit: 4 pure functions + main() golden
│   ├── test_get_task_performance.py # golden-file pivot test on synthetic tree
│   ├── test_tasks_index.py          # subprocess node → assert tasks.json content
│   ├── test_data_contracts.py       # schema-validate every committed JSON file
│   ├── test_determinism.py          # chain twice → byte-identical
│   └── data/
│       ├── model_performance/       # 2-3 handcrafted minimal model files
│       │                            #   (must include edge cases: empty metric, "" value, missing field)
│       └── golden/                  # expected outputs of the chain over the synthetic tree
├── .github/
│   └── workflows/
│       └── ci.yml                   # lint → test → verify-data (path-filtered)
├── script/                          # existing (plus ~4-line determinism fixes)
├── scripts/                         # existing
├── pipeline/                        # existing — untouched by CI
└── dnallm-mark/                     # existing MPA + committed data
```

### Structure Rationale

- **`tests/` at repo root (not inside `script/`):** pytest's recommended layout for script-style repos — tests outside the code under test, one runner for Python + Node-invoked + schema checks. The codebase map's suggestion of `script/test_*.py` colocated tests is viable but scatters the suite and couples test discovery to the scripts' CWD quirk; a root `tests/` with `pythonpath = ["script"]` in pyproject keeps imports clean (`import summarize_comparison`).
- **`tests/data/` synthetic fixtures are separate from `dnallm-mark/data/` real data:** unit/golden tests need *small, explainable* inputs with deliberate edge cases (empty strings for metrics — which `get_float` coerces to `0.0`; species pluralization variants for `to_singular_species`). The real 2.1 MB corpus serves as the integration corpus for contract tests and the CI diff — never duplicated into `tests/`.
- **`schemas/` at root, not under `script/`:** the schema is a contract between *three* parties (pipeline emits, scripts consume/produce, UI consumes, plus external submitters). Root placement signals it governs the repo, not one script.
- **`package.json` at root with only `"type": "module"` + htmlhint:** this is *not* a build step. It exists because `node --check` follows Node's module-detection rules — a `.js` file using `import`/`export` fails `--check` with "Cannot use import statement outside a module" unless the nearest `package.json` declares `"type": "module"`. The frontend stays exactly as-is.

## Architectural Patterns

### Pattern 1: Two-tier fixtures — synthetic trees for unit/golden, committed real data for integration

**What:** Handcrafted 2-3-model fixture trees in `tests/data/model_performance/` drive unit and golden-file tests (fast, debuggable, edge-case-loaded). The real committed corpus in `dnallm-mark/data/` drives contract tests and the CI regenerate-and-diff — it is its own golden master.
**When to use:** Always in this repo. The synthetic tier catches logic bugs; the real-data tier catches drift and contract violations at scale (42 files, 47 task files).
**Trade-offs:** Synthetic fixtures can silently diverge from the real schema shape — mitigated by validating fixtures against the same JSON Schemas in a test.

**Example:**
```python
# tests/conftest.py
import json, os, pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "data")

@pytest.fixture
def synthetic_data_tree(tmp_path, monkeypatch):
    """Materialize the synthetic model_performance/ tree into tmp_path and chdir."""
    src = os.path.join(FIXTURES, "model_performance")
    dst = tmp_path / "model_performance"
    dst.mkdir()
    for f in os.listdir(src):
        (dst / f).write_text((Path(src) / f).read_text())
    monkeypatch.chdir(tmp_path)   # scripts resolve inputs/outputs from CWD
    return tmp_path
```

### Pattern 2: Golden-file testing via regenerate-and-diff

**What:** The canonical CI recipe for committed derived artifacts: regenerate into a scratch location, then `git diff --exit-code`. Any diff means the committed files are stale (or the generator changed without recomputing) → fail the build showing the diff. At unit level, the same idea runs one script against a synthetic tree and compares to committed goldens in `tests/data/golden/`.
**When to use:** For any generated file that is committed to git — here: `task_performance/*.json`, `models_comparison*.json`, `tasks.json`.
**Trade-offs:** Goldens go stale-by-design when a bug fix intentionally changes output (exactly this milestone's species-grouping fix). Provide an explicit, boring update path (`make update-golden`, `make data`) and document before/after. Merge commits of golden files can be textually "clean" but semantically wrong — regenerate after merges rather than trusting conflict resolution.

**Example (repo-level — the heart of "detectable/verifiable"):**
```make
# Makefile
DATA_DIR := dnallm-mark/data

.PHONY: data verify-data
data:  ## Regenerate all derived JSON in-place (run from repo root)
	cd $(DATA_DIR) && python ../../script/get_task_performance.py
	cd $(DATA_DIR) && python ../../script/summarize_comparison.py
	node scripts/generate-tasks-index.js

verify-data:  ## Prove committed derived files match the source data — fail loudly if not
	git stash --quiet --include-untracked -- $(DATA_DIR) 2>/dev/null || true
	$(MAKE) data
	git diff --exit-code -- $(DATA_DIR) || (echo "❌ Derived data is stale. Run 'make data' and commit the result."; exit 1)
```
(In CI, prefer regenerating into a `cp -r` scratch copy over stashing — no mutation of the checked-out tree, no stash-failure edge cases.)

### Pattern 3: JSON Schema as data-contract tests

**What:** The performance-JSON shape is already documented in prose (README "Input Data Format" + docstrings at `script/get_task_performance.py:28-62`, `script/summarize_comparison.py:29-62`). Encode it as JSON Schema files; a parametrized pytest validates **every** committed instance file. This turns the pipeline→scripts→UI seam into an executable contract.
**When to use:** Before regenerating data after correctness fixes — the schema locks the contract so recomputed files can't silently change shape. Also directly reusable by `js/submit.js`'s client-side validation for external submitters.
**Trade-offs:** Schema maintenance burden — keep schemas permissive on optional metadata (model-card fields evolve) and strict only on load-bearing structure (`info`, `performance.{dataset}.performance`, metric keys). Overly strict schemas make every new model a CI failure.

**Example:**
```python
# tests/test_data_contracts.py
import json, pathlib, pytest
from jsonschema import validate

DATA = pathlib.Path("dnallm-mark/data")
SCHEMAS = pathlib.Path("schemas")

def instances(pattern, schema):
    return [pytest.param(p, schema, id=p.name)
            for p in sorted(DATA.glob(pattern))]

@pytest.mark.parametrize("path,schema", 
    instances("model_performance/*.json", "model_performance.schema.json"))
def test_model_file_contract(path, schema):
    validate(json.loads(path.read_text()),
             json.loads((SCHEMAS / schema).read_text()))
```

### Pattern 4: Deterministic serialization is a *prerequisite*, not an enhancement

**What:** Verified in this repo — none of the three generators produce filesystem-independent output:
- `script/summarize_comparison.py:309` iterates `os.listdir(input_dir)` **unsorted** → both summation order (float sum order changes last-ulp results) and output key order depend on filesystem directory order (differs between ext4/tmpfs/macOS/CI runners).
- All three writers serialize without `sort_keys` (`json.dump(..., indent=4, ensure_ascii=False)` at `summarize_comparison.py:381,408`, `get_task_performance.py:159`; `JSON.stringify(index, null, 2)` in `generate-tasks-index.js:56` with unsorted `readdirSync` at line 18).

Any regenerate-and-diff check built on top of this will produce **false failures on some filesystem** and the team will disable it — the failure mode that kills reproducibility gates.
**When to use:** First, before any diff-based CI. The fix is surgical (~4 lines): `sorted(os.listdir(...))` (both Python scripts), `fs.readdirSync(...).sort()` (Node), and `sort_keys=True` on every `json.dump`. Note: adding `sort_keys=True` rewrites the byte layout of all derived files once — do it as its own commit, then recompute.
**Trade-offs:** None of substance; key order in output is not consumed semantically by the UI (`DataAPI` indexes by key).

### Pattern 5: Makefile as the single discoverable entry point

**What:** A root `Makefile` with conventional targets (`make data`, `make test`, `make lint`, `make verify-data`, `make check` = all of them) that shells into the scripts and **encodes the CWD contract** (`cd dnallm-mark/data`) inside the recipes. `make check` is the long-standard convention for "run the test suite"; benchmark/research repos increasingly adopt "clone → install → `make all`" as the reproducibility acceptance test.
**When to use:** Here, immediately — the #1 maintainability finding ("regeneration is tribal knowledge documented only in README") is solved by making the chain *executable and discoverable* (`make` with no args prints targets; recipes are self-documenting).
**Trade-offs:** vs `just`: just has nicer syntax (no tabs/.PHONY) but adds a tool install for every contributor/reviewer — for a public research repo, zero-extra-dependency Make wins. vs npm scripts: no ecosystem-endorsed canonical entry point, cross-platform shell quoting issues, and would force Node ownership of Python steps. Make's timestamp-based incremental re-runs are irrelevant here (targets are phony) so its classic determinism liability doesn't apply.

### Pattern 6: GPU-less CI — lint / test / verify-data job separation

**What:** The heavy pipeline cannot run in CI (GPU + external `dnallm`), so CI covers everything *except* it: a fast lint job, a test job (pytest), and a verify-data reproducibility job — the pattern used by EleutherAI's lm-evaluation-harness (separate linters job via pre-commit/ruff; CPU unit-test matrix; path-filtered task-validation workflow; a `DummyLM` mock so the full eval path runs without GPU). DNALLM-Mark's equivalent of DummyLM is the synthetic fixture tree: the full aggregation chain runs on CPU in seconds (~2.1 MB input).
**When to use:** Always in this milestone. Guard the boundary explicitly: CI installs only `numpy`, `pandas`, `pytest`, `jsonschema`, `ruff` (+ Node for one script) — the install list *is* the enforcement that pipeline/ stays out of scope.
**Trade-offs:** Job fan-out costs runner startup (~30s each) but gives isolated, parallel failure signals. One deliberate restriction: the **verify-data job must run on pinned dependency versions** (see Anti-Pattern 4) — a version matrix and a byte-diff check are incompatible in the same job.

**Example:**
```yaml
# .github/workflows/ci.yml (shape, not verbatim)
name: CI
on: [push, pull_request]
permissions: { contents: read }
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  lint:        # ~1 min: ruff check, node --check loop, htmlhint
  test:        # pytest, pinned python + numpy/pandas (cache: pip)
  verify-data: # cp -r dnallm-mark/data scratch → regenerate → git diff --exit-code
```

## Data Flow

### Verification Flow (the new flow this milestone adds)

```text
MAINTAINER PATH (writes committed data — the only writer)
  edit model_performance/*.json (or fix a script)
      ↓
  make data            (3-script chain, CWD contract inside Makefile)
      ↓
  git commit  (derived JSON changes land in the SAME commit as their cause)

CI PATH (read-only over the repo, writes only to scratch)
  PR/push
      ↓
  ┌─ lint job ──────── ruff · node --check (all *.js) · htmlhint (all *.html)
  ├─ test job ──────── pytest:
  │      unit        : synthetic dict fixtures → pure functions → assertions
  │      golden      : tests/data/model_performance → main() in tmp_path
  │                     → compare vs tests/data/golden/*
  │      contract    : every dnallm-mark/data/**/*.json → JSON Schema → pass/fail per file
  │      determinism : chain ×2 in tmp_path → byte-identical
  └─ verify-data job : cp -r dnallm-mark/data → scratch/
                       run chain in scratch/ → diff vs committed derived files
                       git diff --exit-code  ⇒  clean = proven fresh
                                              dirty = fail with the diff shown
```

### Key Data Flows

1. **Unit/golden flow:** `tests/data/model_performance/` (handcrafted) → imported script module (`summarize_comparison`, `get_task_performance` — both have `if __name__ == "__main__"` guards, verified) → `tmp_path` outputs → compare against `tests/data/golden/`. Never touches committed data.
2. **Contract flow:** committed JSON files (read-only) → schema validation → per-file pass/fail with filename in the test id. Direction: schemas describe data; data never changes to satisfy a test.
3. **Reproducibility flow (the milestone's core deliverable):** committed `model_performance/` (source of truth) → regeneration chain → derived files; the *diff between regenerated and committed derived files* is the freshness proof. Direction is one-way: source data determines derived data; a dirty diff is a defect, never auto-committed by CI.
4. **CI → repo flow:** CI invokes `make` targets (not raw ad-hoc commands) so local and CI verification are the same commands — the Makefile is the single source of procedural truth; the workflow file is only orchestration.

## Component Boundaries

| Boundary | Communication | Rules / Considerations |
|----------|---------------|------------------------|
| tests → `script/*.py` | Python import (`pythonpath = ["script"]` in pyproject) | Only guarded modules are importable; module-level `import numpy/pandas` in `summarize_comparison.py:76-77` means CI must install them (already required) |
| tests → `scripts/generate-tasks-index.js` | subprocess (`node`), parse stdout/JSON | Script is already `__dirname`-relative (location-independent) — no chdir gymnastics needed; asserting file content beats asserting exit code |
| tests → committed `dnallm-mark/data/` | read-only filesystem access | Contract tests + verify-data only; a test that mutates committed data is a defect |
| tests → `pipeline/` | **none — forbidden** | Importing it would drag torch/dnallm into CI; enforced by dependency list, optionally by a lint rule (`ruff` import blacklist) |
| Makefile → scripts | shell recipes with explicit `cd` | Encodes the CWD contract once; humans and CI stop memorizing it |
| CI → Makefile | `run: make <target>` | One procedural source of truth; workflow changes are orchestration-only |
| schemas ↔ `dnallm-mark/data/` | validation relationship | Schema changes are contract changes → require recomputation review; validate the schemas themselves once (metaschema check) |
| `js/submit.js` ↔ `schemas/` | future alignment (optional) | Client-side submission validation should mirror the schema; out of strict scope but the schemas make it possible |

## Suggested Build Order

Dependency-ordered; each step unblocks the next and nothing later depends on undone earlier work:

1. **Determinism fixes in the three generators first** (sorted listing + `sort_keys`, ~4 lines total). Everything diff-based (goldens, verify-data) is built on byte-stable output; doing it later invalidates every golden committed before. Lands as its own commit with a one-time reformat of derived JSON (recompute via `make data` once it exists — or manually this first time).
2. **Dependency manifests** (`pyproject.toml` with bounded `numpy`/`pandas`; minimal `package.json` with `"type": "module"`). Tests cannot even be installed in CI before this; `package.json` unblocks `node --check`.
3. **JSON Schemas + contract tests.** Lock the data contract *before* the correctness fixes change the numbers — then recomputed files are automatically validated, and before/after comparisons have a shape anchor.
4. **Unit tests for the 4 pure functions** in `summarize_comparison.py` (cheap, no I/O) — these will directly pin down correct behavior *before* fixing the species-grouping bug, i.e., write the failing test first where practical.
5. **Golden-file tests on the synthetic tree** (pivot script + aggregation `main()`). Requires 1 (byte stability) and 2 (runner config).
6. **Makefile** (`data`, `test`, `lint`, `verify-data`, `check`). Requires nothing upstream but is most useful once tests exist to wire into `check`.
7. **CI workflow** (`lint` → `test` → `verify-data`). Requires 2, 5, 6. Path filters keep it fast.
8. **Recompute leaderboard data after correctness fixes, with before/after notes.** Last, so it happens under full CI protection: the verify-data job then *proves* the recomputation is complete and committed.

## Anti-Patterns

### Anti-Pattern 1: Regenerate-and-diff without determinism fixes

**What people do:** Wire `git diff --exit-code` into CI while the generators iterate `os.listdir()` unsorted and serialize without `sort_keys` (this repo's current state, verified).
**Why it's wrong:** Directory order and float-summation order vary across filesystems; the check false-fails on some runner, someone disables it, and the gate is dead.
**Do this instead:** Pattern 4 first; add a determinism test (run twice, byte-compare) so regressions are caught at test time, not in a red CI job at 2 a.m.

### Anti-Pattern 2: Duplicating the real corpus as test fixtures

**What people do:** Copy `dnallm-mark/data/` into `tests/fixtures/` to "test with real data."
**Why it's wrong:** Two copies of 2.1 MB of derived data that drift; tests that fail for data reasons look like code failures.
**Do this instead:** Synthetic mini-tree for logic; the committed corpus itself is the integration corpus (contract tests + scratch-dir diff). It is already in git — use it in place.

### Anti-Pattern 3: Fighting the scripts' CWD coupling with refactors

**What people do:** "Fix" `input_dir = "model_performance"` by refactoring both scripts to take `--data-dir` flags.
**Why it's wrong:** Contradicts this milestone's surgical-fix discipline and widens review surface for zero verified correctness gain.
**Do this instead:** Accommodate the contract: `monkeypatch.chdir(tmp_path)` in tests, `cd $(DATA_DIR)` in Makefile recipes, scratch-dir copies in CI. (If a later milestone modularizes, flags come then.)

### Anti-Pattern 4: Version matrix in the same job as the byte-diff check

**What people do:** A CI matrix over Python/pandas versions for the whole test suite including verify-data.
**Why it's wrong:** pandas float formatting and dtype coercion differ across versions — the diff check would fail on every version but the pinned one (spurious red). The 100%-vs-10% reproducibility disagreement in the Node literature traces to exactly this ambiguity.
**Do this instead:** verify-data on one pinned env; if drift monitoring is wanted, a separate *advisory* (non-blocking) job with loose bounds.

### Anti-Pattern 5: CI auto-commits regenerated data

**What people do:** A workflow bot commits regenerated derived files on red verify-data.
**Why it's wrong:** Surprise commits bypass review — precisely what external reviewers of a benchmark must not see; it can also mask a script regression as a "data update."
**Do this instead:** Fail with instructions ("run `make data` and commit"). Human reviews every number change with before/after notes (a stated milestone requirement).

### Anti-Pattern 6: Letting quality tooling mutate the frontend

**What people do:** Adopt prettier/eslint --fix or a bundler "while adding CI," rewriting the vanilla ES-module MPA.
**Why it's wrong:** Violates the hard no-build/no-framework constraint and balloons the diff under review.
**Do this instead:** Read-only checks only: `node --check` (syntax), `htmlhint` (structure). If more frontend checking is ever wanted, it is a new decision, not a side effect.

### Anti-Pattern 7: One mega CI job

**What people do:** A single job running lint + tests + regen + diff sequentially.
**Why it's wrong:** Slow feedback (lint failure blocks test signal), confusing reds, cache invalidation of everything on any change.
**Do this instead:** Three small jobs with path filters (docs-only pushes skip everything); each fails fast and independently.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Current (42 models, 50 datasets, ~2.1 MB) | Full-chain regen in CI in seconds; verify-data on every PR; schema validation linear over ~95 files — no adjustments needed |
| ~2× (new models/datasets land) | Still trivial. Consider path-filtered verify-data (only run when `model_performance/**`, `script/**`, or `scripts/**` change) to keep PR-only pushes fast |
| 100+ model files | Regen stays cheap (aggregation is O(files) pandas ops); golden *review* gets noisy — elide regenerated JSON from PR diffs via `.gitattributes` (`*-database` style diff suppression is not applicable; instead rely on verify-data as the equivalence proof and consider linguist-generated attributes) and keep the before/after discipline in release notes |

### Scaling Priorities

1. **First bottleneck: golden-file PR noise.** Derived JSON diffs are large and review-hostile — the verify-data job is the equivalence proof humans should read instead; document that reviewers may skim derived-file hunks.
2. **Second bottleneck: dependency drift over the repo's lifetime.** Bounded pandas/numpy ranges + a lockfile-for-CI keep the diff check meaningful years out (quant-reproducibility pattern: pinned env is part of the published claim).

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| GitHub Actions | 3 jobs, `permissions: contents: read`, `concurrency` with `cancel-in-progress` on PRs, `timeout-minutes` per job, `setup-python cache: pip` keyed on the lock/manifest | Keep action pins at major tags (`@v4`/`@v5`); SHA-pin only if the org requires it |
| pre-commit (optional) | `check-jsonschema` hooks (`files: ^dnallm-mark/data/.*\.json$`, `--schemafile schemas/...`) + `--check-metaschema` | Runs the same contracts locally pre-push; pytest contract tests remain the CI authority — do not force contributors to install pre-commit to pass CI |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CI ⇄ pipeline/ | none (exclusion) | Enforced by CI dependency list; optional ruff import-forbidden rule documents it in code |
| Makefile ⇄ README | README shows `make` commands only | Kills the drift between documented steps and actual steps — the README documents the *chain concept*, the Makefile is the *chain implementation* |

## Sources

Codebase facts (HIGH — direct inspection at commit `a44d310`): `script/summarize_comparison.py:76-77,274,309,381,408`; `script/get_task_performance.py` (CWD-relative dirs, `__main__` guard, single `main()`); `scripts/generate-tasks-index.js:11-12,18,56` (`__dirname`-relative, unsorted `readdirSync`); `dnallm-mark/data/` layout and sizes; `.planning/codebase/{ARCHITECTURE,TESTING}.md`.

Ecosystem patterns (MEDIUM — cross-verified web sources, 2026-10-08):

- Golden-file / regenerate-and-diff: [MongoDB SERVER-100324 (merge hazards)](https://jira.mongodb.org/browse/SERVER-100324), [Dart pub testdata README (golden regen workflow)](https://dart.googlesource.com/pub.git/+show/c5541b337765b3dd53be089a09951dcfc893b166/test/testdata/README.md), [agent-eval-kit test_golden.py (--check mode + staleness)](https://github.com/portable-genai/agent-eval-kit/blob/main/tests/test_golden.py)
- JSON Schema contract testing: [check-jsonschema pre-commit usage](https://check-jsonschema.readthedocs.io/en/latest/precommit_usage.html), [check-jsonschema repo](https://github.com/python-jsonschema/check-jsonschema), [COSAI hook-validations example](https://raw.githubusercontent.com/cosai-oasis/secure-ai-tooling/refs/heads/main/scripts/docs/hook-validations.md)
- Task runners / reproducibility: [make-all quant paper pattern](https://faketut.github.io/2026/06/07/qmj-04-make-all-under-a-minute/), [task-runner comparison](https://nihilok.github.io/why-i-built-another-task-runner), [make check convention (Milan handout)](http://homes.di.unimi.it/~sisop/lucidi1718/svigruppo11-handout.pdf), [npm scripts reproducibility ambiguity (arXiv 2503.21705)](https://export-test.arxiv.org/pdf/2503.21705)
- Determinism: [deterministic output best practices](https://github.com/mcorbett51090/RavenClaude/blob/main/plugins/team-portfolio/best-practices/deterministic-output-makes-diffs-and-caching-trustworthy.md), [JSONCANON canonicalization](https://www.zenodo.org/records/20819570/files/json_canon.pdf?download=1), [replicate/cog nondeterministic-output incident](https://app.semanticdiff.com/gh/replicate/cog/commit/de3af597615018482cfbaed4a63a7efa703d90f4), [Debian reproducible-builds pandas notes](https://tests.reproducible-builds.org/debian/notes/pandas_note.html)
- Benchmark-repo CI: [lm-evaluation-harness unit_tests workflow](https://huggingface.co/chen459664/quantization2/blob/4f918cc1f91637c5defdf3800e9e4365fe12b306/lm-evaluation-harness/.github/workflows/unit_tests.yml), [new_tasks path-filtered workflow](https://github.com/EleutherAI/lm-evaluation-harness/blob/1dd93108/.github/workflows/new_tasks.yml), [testing infrastructure overview](https://deepwiki.com/EleutherAI/lm-evaluation-harness/8.1-testing-infrastructure)
- Dependency pinning: [pylock.toml / lockfile-vs-metadata split (Stack Overflow)](https://stackoverflow.com/revisions/76548420/5), [pandas version pinning guidance](https://theneuralbase.com/pandas-for-ml/learn/advanced/pandas-version-pinning/), [Copernicus EOPF dependency design](https://cpm.pages.eopf.cpm.eopf.copernicus.eu/eopf-cpm/3.0.0/djf.html)
- pytest layout: [pytest good integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)

Node `--check` / htmlhint specifics (LOW — single-source model knowledge, standard well-established tool behavior; verify exact flag behavior when implementing): treat the `"type": "module"` requirement for `node --check` and the `xargs -n1` loop shape as hypotheses to confirm in the first lint-job run.

---
*Architecture research for: test/CI/release hardening of DNALLM-Mark*
*Researched: 2026-10-08*
