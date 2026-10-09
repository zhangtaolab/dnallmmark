# Phase 2: Data Contracts & Test Harness - Research

**Researched:** 2026-10-09
**Domain:** JSON Schema contracts over the data chain; pytest/node:test harness; Makefile/uv tooling
**Confidence:** HIGH

## Summary

This phase is buildable with three small additions to the existing uv substrate — `jsonschema`, `pytest`, `ruff` in the `dev` dependency group — plus the built-in Node test runner and a Makefile. Every load-bearing mechanism was **verified live in this session** against the real committed data and the real library versions: an all-strict draft-2020-12 schema (with `additionalProperties: false`, every field required, and the exact closed enums surveyed from the data) validated all 42 `model_performance` files with **zero errors in 0.21s**; `@pytest.mark.xfail(strict=True)` on pytest 9.1.1 turns an unexpected XPASS into a suite failure (exit 1); the synthetic-fixture chain (3 fake models with an exact tie and a missing metric) runs through both Python scripts under `chdir` and produces hand-verifiable rankings; and the CommonJS index generator is testable with zero production changes by copying it into a `<tmp>/inner/` + `<tmp>/dnallm-mark/data/task_performance/` fixture layout.

The data shape is **perfectly uniform** across all 94 committed files (live survey): every model file has exactly `{info: 11 keys, performance: {dataset: 8 keys, parameters: 9 keys, performance: 14 keys}}`; every one of the 4 `models_comparison` files has the same 7-key model block and 15-key performance block; every `tasks.json` entry has 9 keys. The D-02 metric enum is exactly `{"f1", "mcc", "spearmanr", "AUPRC"}` (mixed case — `AUPRC` is uppercase in data) and dataset species is exactly `{"Animals", "Plants", "Microbe"}`. Strict schemas will not need a single exception beyond the documented `""`-means-missing convention, which is expressible as `anyOf: [{type: number}, {const: ""}]`.

The three known-defect xfail tests are all CPU-only feasible: the species bug (AUD-01-P0) is a **one-line source fact** at `pipeline/dnallmmark_pipeline.py:1229` (`"species": model_row.get("species", "unknown"),` — every sibling field reads from `row`), so the least-coupled test is an AST-based producer-contract check, not a pipeline import (torch/dnallm are unavailable CPU-side). WR-03's NaN poisoning was reproduced live (`get_float('nan')` returns `nan`, passes the presence gate, and zeroes an entire task's MinMax). WR-02's silent bool/int pass-through is confirmed by code reading at `baseline/compare.py:90-106`.

**Primary recommendation:** Add `pytest`, `jsonschema`, `ruff` to a `dev` group; author 4 all-strict draft-2020-12 schemas in `schemas/` reusing shared `$defs`; test the Python scripts by importing `script/` modules via `sys.path` (pure functions) and driving `main()` under `monkeypatch.chdir(tmp_path)` (chain tests); test the JS generator by copying it into a fixture tree; pin threads in `conftest.py` before any numpy import; use explicit `uv run --group dev` in the Makefile because `default-groups = ["data"]` **replaces** uv's `["dev"]` default.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** All four schemas are FULLY STRICT — `additionalProperties: false` plus every field required. Any shape drift fails validation; adding a field anywhere requires a schema change first (forced versioning, reviewer-friendly). — **Reversibility:** costly — once published, loosening a strict schema breaks the contract's meaning for every consumer that started relying on drift-detection; tightening later is cheap but loosening reads as a regression.
- **D-02:** `metric` / primary-metric fields use a CLOSED ENUM of metric names extracted from the current 50 datasets (f1, accuracy, mcc, auprc, …). New datasets with new metrics require a schema update; typos fail immediately. Self-check: a unit test asserts the enum ≡ the set of metric values actually present in committed data, so enum and data cannot silently diverge.
- **D-03:** The species-as-dataset bug (AUD-01-P0) is captured as `xfail(strict=True)`: the test asserts the CORRECT behavior (a dataset entry's `species` must be the arena category Animals/Plants/Microbe, never the model's organism). Today it fails → xfail. `strict=True` means an unexpected XPASS fails the suite, forcing the Phase 4 fixer to explicitly remove the marker and confirm the fix — a fix can never land silently. The same mechanism is used for WR-02/WR-03 (D-07).
- **D-04:** WR-02 (compare.py treats equal-value bool/int cross-type pairs as identical — live risk over the 47 pinned files carrying bf16/fp16 booleans) and WR-03 (non-finite metric values pass the presence gate and NaN-poison a whole task's normalization) become xfail(strict) tests THIS phase — defect semantics locked test-first, fixed in Phase 4. No production-code change in Phase 2.
- **D-05:** Routing of the remaining five: WR-01 → Phase 5; IN-01 → Phase 4; IN-02 → milestone backlog.
- **D-06:** These dispositions are recorded in the phase 01 disposition ledger; the planner should treat D-04/D-05 as scope input, not re-derive routing.
- **D-07:** (folded into D-03/D-04 — species bug + WR-02 + WR-03 all use xfail(strict=True).)
- **D-08:** Two zero-risk micro-fixes land in-phase alongside the harness (no code semantics, no numbers touched): IN-03 — README "Output fields" list gains `avg_PFLOPs`; IN-04 — `.gitignore` gains `.planning/tmp/`.
- **D-09:** Golden-file tests run over a SYNTHETIC fixture tree (hand-crafted minimal model set, ~3-5 fake models × several datasets, engineered to cover exact ties, missing/empty metric values, boundary shapes) — fast, stable, decoupled from real-data drift.
- **D-10:** The determinism regression runs over the REAL committed tree: run the full chain twice, assert byte-identical outputs, and assert regeneration == committed tree. ~40s per chain run; local-run acceptable, CI wiring deferred to Phase 5 TEST-07.

### Claude's Discretion
- Schemas live in `schemas/` (four files, JSON Schema draft 2020-12, with `$id`).
- Tests live in `tests/` (pytest); pytest config and the dev dependency group go into the existing `pyproject.toml` (PEP 735 group, consistent with the Phase 1 substrate).
- `make data` / `make test` / `make lint` invoke through `uv run` (no activation step), replacing the CWD-sensitive 3-step procedure (REL-04). `make data` must work from repo root.
- The JS index generator gets a minimal `node:test` unit suite (it is part of the data chain; the real-tree determinism test also exercises it end-to-end).
- Thread pinning (`OMP/OPENBLAS/MKL_NUM_THREADS=1`) and `pytest.approx` tolerances live in `conftest.py` per TEST-02.
- xfail markers carry the finding ID in the reason string (e.g. `reason="AUD-01-P0 species-as-dataset — Phase 4 fix"`).

### Deferred Ideas (OUT OF SCOPE)
- WR-01 gitleaks token-prefix pinning — Phase 5 (with CI gitleaks wiring)
- IN-01 comparator diff-label accuracy (pure-int → FLOAT_BIG) — Phase 4 (next comparator modification)
- IN-02 index-generator missing-dir crash robustness — milestone backlog
- CI enforcement of schemas/determinism (TEST-04/05/07), post-fix recomputation + changelog (DATA-01/02/06) — Phase 5
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REL-04 | Single-command data-regeneration chain (`make data`) replacing the undocumented 3-step CWD-sensitive procedure | Both Python scripts resolve `model_performance`/outputs against CWD at call time (verified: paths are used inside `main()`, not at import) — `make data` wraps them with `cd dnallm-mark/data && uv run ...`; the JS generator is `__dirname`-relative and runs from anywhere. Makefile pattern + uv group invocation verified. |
| TEST-01 | Unit tests for data-script pure functions (rank/MinMax/z-score/robust aggregation, pivot logic) using synthetic fixtures, CPU-only | `summarize_comparison.py` exposes 4 importable pure functions (verified live); pivot logic lives inside `main()` of `get_task_performance.py` — tested by `monkeypatch.chdir(tmp_path)` + calling `main()` (mechanism verified live with a 3-model fixture incl. exact tie + missing metric). |
| TEST-02 | Float-tolerance policy and thread pinning at scaffold time (`pytest.approx`; `OMP/OPENBLAS/MKL_NUM_THREADS=1` in conftest) | numpy scalars leak from `calculate_dataset_stats` (verified: returns `np.float64`), so approx is mandatory for float assertions; conftest-top `os.environ.setdefault` runs before test-module numpy imports. |
| TEST-03 | Golden-file tests over synthetic fixture trees plus a determinism regression test | Synthetic chain output verified hand-computable (tie → shared rank, both score N−1; missing metric → model excluded); determinism = run chain twice + regeneration==committed (Phase 1 behavioral precedent; byte-identical proven same-machine post-FIX-05). |
| TEST-06 | JSON Schema contract validation — 4 schemas enforced over every committed JSON (local suite form; CI is Phase 5) | All 94 files surveyed: key sets perfectly uniform; all-strict schema validated 42 model files in 0.21s with 0 errors (live probe); error objects expose `.json_path`/`.validator`/`.message` for readable failures. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech stack locked:** vanilla ES-module JS (no build step, no framework) + Python; public release must not change architecture
- **Hosting:** static files only — no backend/API
- **CI feasibility:** GitHub Actions must not require GPU or the external `dnallm` package — test scope limited to stdlib/numpy/pandas scripts and static checks (this phase: local suite only; no CI yet)
- **Fix discipline:** surgical fixes only; no opportunistic refactors that widen review surface (D-04: NO production-code change in Phase 2 except the two README/.gitignore micro-fixes)
- **Python conventions:** module docstrings, Google-style docstrings, `main()` with `# ===== Configuration =====` block, `if __name__ == "__main__": main()`, `json.dump(..., indent=4, ensure_ascii=False)` (chain scripts now add `sort_keys=True`)
- **Missing-value convention:** missing metrics are empty strings `""`, never `null` or `0` — every consumer must use `get_float()`-style coercion (schemas must encode this)
- **GSD workflow enforcement:** file changes go through GSD entry points; commits via the gsd seam
- **Comments bilingual English/Chinese acceptable** — match the surrounding file

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Schema authoring + validation | Offline toolchain (`schemas/` + pytest) | — | Contracts guard the data chain; validation runs in the local suite (CI activation is Phase 5) |
| Aggregation unit tests (rank/MinMax/z/robust) | pytest over `script/summarize_comparison.py` pure functions | — | Functions are importable and side-effect-free (verified) |
| Pivot tests | pytest driving `get_task_performance.main()` under chdir | — | Logic is inside `main()`; chdir-to-fixture is the only surgical access (verified) |
| JS index-generator tests | `node:test` (builtin) subprocess over fixture tree | — | CJS script with import-time side effect; copy-into-fixture-tree trick verified |
| Known-defect locking (xfail strict) | pytest markers | AST source check for the pipeline bug | Pipeline not importable CPU-side (torch/dnallm at `pipeline/dnallmmark_pipeline.py:16-18`) |
| Golden/determinism regression | pytest over synthetic (golden) and real (determinism) trees | `baseline/compare.py` `walk()` reuse | Phase 1 comparator is the canonical diff vocabulary |
| Single-command entry | Makefile → `uv run` | — | uv manages the venv; make is locked by ROADMAP |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| jsonschema | 4.26.0 | Draft 2020-12 validation of the 4 schemas over 94 committed files | The canonical Python implementation; full 2020-12 support; `validator_for`/`Draft202012Validator`/`iter_errors` API verified; 42 files validated in 0.21s [VERIFIED: PyPI registry + live probe] |
| pytest | 9.1.1 | Test runner for the whole Python suite | De-facto standard; xfail(strict), approx, pyproject config all verified live on 9.1.1 [VERIFIED: PyPI registry + live probe] |
| ruff | 0.16.10 | `make lint` (Python lint) | Canonical Astral linter; already the ecosystem default; pyproject comment reserves its slot [VERIFIED: PyPI registry] |
| node:test (builtin) | Node ≥ 20 (stable) | JS index-generator unit suite | Zero dependencies — matches the no-npm constraint; stable since Node 20; present Node is v26.10.0 [CITED: nodejs.org/api/test.html; verified live] |
| GNU Make | 4.3 (local) | `make data` / `make test` / `make lint` | Locked by ROADMAP; verified present locally [VERIFIED: local `make --version`] |
| uv | 0.12.23 (local) | Environment + `uv run --group dev` invocation | Existing Phase 1 substrate; `--group` flag verified on installed version [VERIFIED: local `uv run --help`] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| referencing / jsonschema-specifications / rpds-py / attrs | (pulled transitively by jsonschema 4.26.0) | Draft-2020-12 spec resources | Automatic — do not pin explicitly [VERIFIED: PyPI requires_dist] |
| numpy / pandas | 2.5.3 / 2.3.3 (locked, `data` group) | Under test via `summarize_comparison` | Already installed; tests import them transitively |

**Installation:**
```bash
uv add --group dev pytest jsonschema ruff
```
(Updates `pyproject.toml` `[dependency-groups] dev` + `uv.lock`. Note: `uv add --group dev` does NOT change `default-groups`; the Makefile must pass `--group dev` explicitly — see Pitfall 2.)

**Version verification (this session):** jsonschema 4.26.0 (PyPI, published 2026-01-07, requires-python >=3.10, classifiers list 3.13 & 3.14), pytest 9.1.1 (PyPI, 2026-06-19), ruff 0.16.10 (PyPI, requires >=3.7), referencing 0.37.0. All install-tested live on Python 3.13.16.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| jsonschema 4.26.0 | fastjsonschema | ~10-50x faster compilation/validation — irrelevant at 94 files / <1s; but error messages are markedly worse (no `.json_path`, terse strings) and draft-2020-12 support is less rigorously spec-tracked. Not worth it. [ASSUMED performance ratio] |
| jsonschema | pydantic | Wrong tool: schemas must be shareable JSON documents (D-01 forced-versioning contract), not Python classes |
| pytest markers per test | `xfail_strict = true` ini global | Global flips EVERY xfail strict — heavier than needed; per-marker `strict=True` is surgical and self-documenting next to the reason string |
| Makefile | justfile / taskfile | Rejected: Makefile locked by ROADMAP; GNU Make 4.3 verified present |

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| jsonschema | PyPI | ~10 yrs (4.26.0 published 2026-01-07) | unknown (stats endpoint unavailable in sandbox) | github.com/python-jsonschema/jsonschema | SUS* | Approved — *flagged solely for "unknown-downloads"; canonical repo, canonical name, metadata verified via PyPI JSON API |
| pytest | PyPI | ~12 yrs (9.1.1 published 2026-06-19) | unknown (stats endpoint unavailable in sandbox) | github.com/pytest-dev/pytest | SUS* | Approved — same basis as above |
| ruff | PyPI | ~4 yrs (0.16.10) | unknown (stats endpoint unavailable in sandbox) | docs.astral.sh/ruff (Astral) | SUS* | Approved — same basis as above |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none genuinely — all three verdicts carry reason `unknown-downloads` only, an artifact of the sandbox lacking the download-stats signal (verified against the PyPI JSON API directly: correct canonical repos, non-deprecated, standard metadata). If the planner wants belt-and-braces, a `checkpoint:human-verify` before `uv add` costs nothing; my assessment is these three are the most-installed packages in the Python ecosystem and the flag is a missing-signal false positive.

*No JS packages are installed — the JS suite uses only Node builtins (`node:test`, `node:assert`, `node:fs`).*

## Architecture Patterns

### System Architecture Diagram

```
                    make data / make test / make lint  (repo root)
                              │
                    uv run --group dev …  (auto-syncs .venv from uv.lock)
                              │
        ┌─────────────────────┼──────────────────────────────┐
        ▼                     ▼                              ▼
   [data chain]         [pytest suite]                  [node --test]
        │                     │                              │
        │  cd dnallm-mark/data│ (conftest pins threads,       │ copy trick:
        │  1. get_task_performance.py   sys.path→script/)     │  <tmp>/inner/gen.js +
        │     model_performance/ ──► task_performance/        │  <tmp>/dnallm-mark/data/
        │  2. summarize_comparison.py                         │   task_performance/
        │     └─► models_comparison{,_animal,_plant,_microbe} │        │
        │  3. node scripts/generate-tasks-index.js            ▼        ▼
        │     └─► tasks.json                            fixture tasks.json
        │                                                    asserted
        ▼
   pytest tests consume:
   ├─ tests/test_schemas.py ──► schemas/*.json ──► 94 committed JSON files
   │      └─ enum self-check: schema enum ≡ metric values found in data
   ├─ tests/test_aggregation.py ──► summarize_comparison pure functions
   │      └─ synthetic fixtures: exact ties, missing "" metrics, boundaries
   ├─ tests/test_pivot.py ──► get_task_performance.main() under chdir(tmp)
   ├─ tests/test_golden.py ──► synthetic tree → committed goldens (compare.py walk)
   ├─ tests/test_determinism.py ──► REAL tree: chain ×2 byte-identical
   │      └─ regeneration == committed (tmp-copy, compare per file)
   └─ tests/test_known_defects.py ──► xfail(strict=True): AUD-01-P0 (AST check
          of pipeline:1229), WR-02 (compare.py bool/int), WR-03 (get_float NaN)
```

### Recommended Project Structure
```
schemas/
├── model_performance.json      # $id …/model_performance.json — strict, $defs shared
├── task_performance.json       # $ref reuse of dataset/parameters/performance defs
├── models_comparison.json      # one schema covers all 4 files (identical shape)
└── tasks_index.json            # tasks.json entries
tests/
├── conftest.py                 # thread pinning BEFORE numpy import; sys.path setup; fixtures
├── fixtures/
│   ├── synthetic_models/       # 3-5 fake {alias}_performance.json (tie pair, missing metric,
│   │                           #   boundary shapes) — source of golden regeneration
│   └── golden/                 # committed expected outputs (task_performance/, models_comparison*.json, tasks.json)
├── test_schemas.py             # 94-file validation (parametrized by file) + enum≡data self-check
├── test_aggregation.py         # rank/MinMax/z-score/robust + aggregate_models + get_float + to_singular_species
├── test_pivot.py               # pivot via main() under chdir
├── test_golden.py              # synthetic chain → goldens (value-compare, ULP-tolerant)
├── test_determinism.py         # @pytest.mark.slow — real tree, chain ×2 + regen==committed
├── test_known_defects.py       # xfail(strict=True): AUD-01-P0 / WR-02 / WR-03
└── js/
    └── generate-tasks-index.test.js   # node:test CJS — copy-script-into-fixture-tree
Makefile                        # data / test / test-fast / lint (.PHONY)
```

### Pattern 1: All-strict schema with shared `$defs` (D-01/D-02)
**What:** Each schema declares `$schema: "https://json-schema.org/draft/2020-12/schema"`, an `$id`, `additionalProperties: false` at every object level, `required` listing every property, and closed enums for vocabulary fields.
**When to use:** All four schemas — verified feasible with zero exceptions (live probe: 42/42 files pass).
**Example** (verified live against all 42 committed files — adapt, don't invent):
```jsonc
// schemas/model_performance.json — the master pattern (live-validated fragment)
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://raw.githubusercontent.com/zhangtaolab/dnallmmark/main/schemas/model_performance.json",
  "type": "object",
  "additionalProperties": false,
  "required": ["info", "performance"],
  "properties": {
    "info": {
      "type": "object", "additionalProperties": false,
      "required": ["architecture", "context_len (bp)", "huggingface", "mean_token_len",
                   "modelscope", "name", "series", "size (M)", "species", "tokenizer", "type"],
      "properties": {
        "architecture": {"type": "string"}, "huggingface": {"type": "string"},
        "modelscope": {"type": "string"}, "name": {"type": "string"},
        "series": {"type": "string"}, "species": {"type": "string"},
        "tokenizer": {"type": "string"}, "type": {"type": "string"},
        "context_len (bp)": {"type": "integer"},
        "mean_token_len": {"type": "integer"},
        "size (M)": {"type": "integer"}
      }
    },
    "performance": {
      "type": "object",
      "additionalProperties": {"$ref": "#/$defs/datasetEntry"}
    }
  },
  "$defs": {
    "datasetEntry": {
      "type": "object", "additionalProperties": false,
      "required": ["dataset", "parameters", "performance"],
      "properties": {
        "dataset": {
          "type": "object", "additionalProperties": false,
          "required": ["dev", "labels", "length", "metric", "species", "test", "train", "type"],
          "properties": {
            "dev": {"type": "integer"}, "labels": {"type": "integer"},
            "length": {"type": "integer"}, "test": {"type": "integer"},
            "train": {"type": "integer"},
            "metric": {"enum": ["f1", "mcc", "spearmanr", "AUPRC"]},
            "species": {"enum": ["Animals", "Plants", "Microbe"]},
            "type": {"enum": ["binary", "multiclass", "regression", "multilabel"]}
          }
        },
        "parameters": {
          "type": "object", "additionalProperties": false,
          "required": ["batch_size", "bf16", "epochs", "fp16", "gradient_accumulation_steps",
                       "learning_rate", "lr_scheduler_type", "steps", "warmup"],
          "properties": {
            "batch_size": {"anyOf": [{"type": "integer"}, {"const": ""}]},
            "bf16": {"type": "boolean"}, "fp16": {"type": "boolean"},
            "epochs": {"type": "integer"},
            "gradient_accumulation_steps": {"type": "integer"},
            "steps": {"type": "integer"},
            "learning_rate": {"type": "number"}, "warmup": {"type": "number"},
            "lr_scheduler_type": {"type": "string"}
          }
        },
        "performance": {
          "type": "object", "additionalProperties": false,
          "required": ["FLOPs", "accuracy", "auprc", "auroc", "f1", "loss", "mcc",
                       "mse", "pearson_r", "precision", "r2", "recall", "runtime", "spearman_r"],
          "properties": {
            "FLOPs": {"type": "number"},
            "runtime": {"anyOf": [{"type": "number"}, {"const": ""}]},
            "loss":     {"anyOf": [{"type": "number"}, {"const": ""}]},
            "accuracy": {"anyOf": [{"type": "number"}, {"const": ""}]},
            "mse":      {"anyOf": [{"type": "number"}, {"const": ""}]}
            // … precision, recall, f1, mcc, auroc, auprc, pearson_r, spearman_r, r2: same anyOf
          }
        }
      }
    }
  }
}
```
**Verified survey facts baked into the example** (all 94 files, live counts): metric enum values are exactly `f1` (1554), `mcc` (252), `spearmanr` (126), `AUPRC` (42) — `AUPRC` uppercase, everything else lowercase; species enum exactly `Animals` (924) / `Plants` (504) / `Microbe` (546); type enum exactly `binary` / `multiclass` / `regression` / `multilabel`; `batch_size` is `""` in 9 GENERanno/PlantCaduceus entries (missing-value convention), integer elsewhere; metric fields are float-or-`""`.

**Cross-schema `$defs` reuse:** `task_performance.json` re-uses the same `datasetEntry` (as its top-level `info`), model card (11-key `info`), `parameters`, and per-model `performance` blocks via `$ref` to a shared def file or by duplication — draft 2020-12 allows `$ref: "model_performance.json#/$defs/datasetEntry"` between sibling files when validated with a `referencing` Registry (jsonschema's default registry handles relative `$id` refs; absolute-URL `$id`s make refs unambiguous). Duplication is also defensible (4 files, forced versioning is the point) — planner's call.

### Pattern 2: `xfail(strict=True)` known-defect locking (D-03/D-04/D-07)
**What:** The test asserts CORRECT behavior; it fails today; `strict=True` makes the eventual Phase 4 fix an XPASS **failure** until the marker is removed deliberately.
**Verified live on pytest 9.1.1:** failing body → `XFAIL` (green, reason shown); unexpectedly passing body → `FAILED … [XPASS(strict)]`, exit code 1.
```python
# tests/test_known_defects.py
import ast
from pathlib import Path
import pytest

PIPELINE = Path(__file__).parents[2] / "pipeline" / "dnallmmark_pipeline.py"

@pytest.mark.xfail(strict=True, reason="AUD-01-P0 species-as-dataset — Phase 4 fix")
def test_producer_writes_dataset_species_not_model_organism():
    """The dataset entry constructed at pipeline:1227 must source `species` from the
    DATASET row (`row`), like every sibling field — never from `model_row`."""
    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        # assignment target: master_performance_dict["performance"][dataset_name] = {...}
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Subscript)
                and isinstance(node.value, ast.Dict)):
            ds = next((v for k, v in zip(node.value.keys, node.value.values)
                       if isinstance(k, ast.Constant) and k.value == "dataset"), None)
            if isinstance(ds, ast.Dict):
                sp = next((v for k, v in zip(ds.keys, ds.values)
                           if isinstance(k, ast.Constant) and k.value == "species"), None)
                # Correct: row.get("species", …). Buggy (today): model_row.get("species", …)
                assert isinstance(sp, ast.Call) and isinstance(sp.func, ast.Attribute) \
                    and sp.func.attr == "get" and isinstance(sp.func.value, ast.Name) \
                    and sp.func.value.id == "row", \
                    "dataset.species must be read from the dataset row, not the model row"
                return
    pytest.fail("dataset-entry construction site not found — pipeline structure changed")
```
**Why AST not import:** `pipeline/dnallmmark_pipeline.py:16-18` does `import torch` / `from dnallm import …` at module level — unimportable CPU-side. **Why AST not regex:** robust to reformatting; anchors on structure (the unique assignment whose dict literal contains a `"dataset"` sub-dict). The one-line source fact this locks, quoted verbatim [VERIFIED: pipeline/dnallmmark_pipeline.py:1229]:
```python
                        "species": model_row.get("species", "unknown"),
```
— while every sibling field reads `row.get(...)` (lines 1230-1236: `"type": row.get("type", "")`, `"labels": row.get("labels", 0)`, …). Note for the planner: `pipeline/datasets_info.json` has **0 of 50 entries carrying a `species` key** [VERIFIED: live jq-equivalent survey] — the Phase 4 fix adds species per dataset; the Phase 2 test correctly asserts provenance (`row`), which is the part that can be checked CPU-side today.

WR-02 and WR-03 xfail forms (both verified against current code behavior):
```python
@pytest.mark.xfail(strict=True, reason="WR-02 equal-value bool/int cross-type pairs must be reported — Phase 4 fix")
def test_compare_reports_equal_value_bool_int_cross_type():
    diffs = []
    walk(True, 1, "", diffs)          # committed bf16:true vs regenerated 1 — must NOT be silent
    assert diffs, "bool/int cross-type pair with equal value must produce a BOOL diff"

@pytest.mark.parametrize("bad", ["nan", "inf", "-inf"])
@pytest.mark.xfail(strict=True, reason="WR-03 non-finite metrics must be excluded by the presence gate — Phase 4 fix")
def test_nonfinite_metric_excluded_from_ranking(bad):
    assert get_float(bad, default=None) is None  # today: returns nan/inf (verified live)
```

### Pattern 3: Synthetic-fixture chain tests (chdir, not refactor)
**What:** Drive the scripts' `main()` functions under `monkeypatch.chdir(tmp_path)` with a hand-built `model_performance/` tree — zero production-code changes (D-04).
**Verified live** (3 fake models; alpha+beta tie at 0.9 on `FakeDS__tie_task`, gamma missing `spearman_r` on `FakeDS__missing_task`):
```python
def test_pivot_and_aggregation(tmp_path, monkeypatch):
    (tmp_path / "model_performance").mkdir()
    for alias, doc in SYNTHETIC_MODELS.items():
        (tmp_path / "model_performance" / f"{alias}_performance.json").write_text(json.dumps(doc))
    monkeypatch.chdir(tmp_path)
    import get_task_performance, summarize_comparison   # via sys.path setup in conftest
    get_task_performance.main()
    summarize_comparison.main()
    comp = json.loads((tmp_path / "models_comparison.json").read_text())
    # Tie: method='min' → alpha & beta both rank 1 on tie_task → both score N-1 = 2; gamma scores 0
    # Missing metric: gamma excluded from missing_task entirely (samples=1, not 2)
    assert comp["fake-beta"]["performance"]["rank"] == 1   # 2 (tie) + 1 (wins missing_task)
    assert comp["fake-alpha"]["performance"]["rank"] == 2   # 2 (tie) + 0
    assert comp["fake-gamma"]["performance"]["samples"] == 1
```
Live-verified output of exactly this mechanism: `fake-alpha: rank=2 rank_score=2.0 samples=2`, `fake-beta: rank=1 rank_score=3.0 samples=2`, `fake-gamma: rank=3 rank_score=0.0 samples=1` — hand-computable expectations, deterministic, CPU-only, <1s.
**CWD-sensitivity note:** both scripts resolve `model_performance` / output paths against CWD **at call time** (paths are locals inside `main()`) [VERIFIED: script/get_task_performance.py:78-82, script/summarize_comparison.py:274-277] — chdir works; import order is irrelevant.

### Pattern 4: JS generator test — copy-into-fixture-tree (zero production change)
**What:** `scripts/generate-tasks-index.js` is CommonJS (`require('fs')`, `__dirname`), runs `generateTaskIndex()` unconditionally at module load (line 78), and resolves paths `__dirname/../dnallm-mark/data/...` — importable only at the cost of executing it, and CWD cannot redirect it.
**Verified live:** copy the script to `<tmp>/inner/gen.js`, build `<tmp>/dnallm-mark/data/task_performance/` with fixture files, run `node <tmp>/inner/gen.js` → reads fixtures, writes `<tmp>/dnallm-mark/data/tasks.json`. Assert its content (id/displayName collapse `/_+/g`, species/type/labels/length/metric projection, count, version).
```js
// tests/js/generate-tasks-index.test.js (CommonJS — no package.json, .js defaults to CJS)
const { test } = require('node:test');
const assert = require('node:assert');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

test('index projects fixture task files', (t) => {
  const tmp = fs.mkdtempSync('/tmp/dnallmmark-js-');
  fs.mkdirSync(path.join(tmp, 'inner'));
  fs.mkdirSync(path.join(tmp, 'dnallm-mark', 'data', 'task_performance'), { recursive: true });
  fs.copyFileSync(path.join(__dirname, '..', '..', 'scripts', 'generate-tasks-index.js'),
                  path.join(tmp, 'inner', 'gen.js'));
  fs.writeFileSync(path.join(tmp, 'dnallm-mark', 'data', 'task_performance',
                             'Fake__one_task_performance.json'),
    JSON.stringify({ info: { species: 'Microbe', type: 'binary', labels: 2, length: 500, metric: 'f1' } }));
  execFileSync(process.execPath, [path.join(tmp, 'inner', 'gen.js')]);
  const index = JSON.parse(fs.readFileSync(path.join(tmp, 'dnallm-mark', 'data', 'tasks.json'), 'utf8'));
  assert.strictEqual(index.count, 1);
  assert.strictEqual(index.version, '1.0.0');
  assert.strictEqual(index.tasks[0].displayName, 'Fake one');  // underscore runs collapse
});
```
Default `node --test` discovery patterns include `**/*.test.{cjs,mjs,js}` and `**/test/**/*` [CITED: nodejs.org/api/test.html] — `make test` can invoke `node --test tests/js/` explicitly to avoid scanning the whole repo.

### Pattern 5: conftest thread pinning + import roots (TEST-02)
```python
# tests/conftest.py — MUST set env before any numpy import happens (test modules import it)
import os
import sys
from pathlib import Path

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "1")            # pin: stable reductions, no oversubscription

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "script"))   # import summarize_comparison, get_task_performance
sys.path.insert(0, str(REPO_ROOT / "baseline")) # import compare (walk) for reuse
```
conftest.py is imported by pytest before collecting/importing test modules, so the pin lands first. (Alternative: pytest's `pythonpath` ini option does the same for import roots; env pinning still needs conftest top-level code.)
**Float policy (TEST-02):** every float assertion goes through `pytest.approx` — `calculate_dataset_stats` returns `np.float64` scalars (verified live) and sums derive from numpy reductions; exact `==` on floats is forbidden in reviews.

### Pattern 6: Makefile over uv (REL-04)
```make
# Makefile — repo root
.PHONY: data test test-fast lint

UV := ~/.local/bin/uv
DATA_DIR := dnallm-mark/data

data:
	cd $(DATA_DIR) && $(UV) run --group data python ../../script/get_task_performance.py
	cd $(DATA_DIR) && $(UV) run --group data python ../../script/summarize_comparison.py
	node scripts/generate-tasks-index.js   # __dirname-relative: works from repo root as-is

test:
	$(UV) run --group dev pytest
	node --test tests/js/

test-fast:
	$(UV) run --group dev pytest -m "not slow"

lint:
	$(UV) run --group dev ruff check script/ baseline/ tests/
```
Notes (verified): `uv run` auto-syncs lock+env before invoking [CITED: docs.astral.sh/uv]; `--group dev` is REQUIRED because `default-groups = ["data"]` in pyproject **replaced** uv's `["dev"]` default (verified against uv docs + installed 0.12.23 `--group` flag). The JS step runs plain `node` (no Python env needed). `.PHONY` discipline since targets are not files.

### Anti-Patterns to Avoid
- **Loosening a schema after publication** — D-01 reversibility note: tighten cheaply, never loosen; schema changes must precede data changes (forced versioning)
- **Byte-equality on golden floats across machines** — same-machine byte-identical is proven (FIX-05); cross-machine float noise (SIMD-path differences, e.g. aarch64 GB10 vs x86 CI) is explicitly NOT claimed by PIN-VALIDATION — goldens should value-compare via `baseline/compare.py` `walk()` with FLOAT_ULP tolerated; reserve byte-assertions for the same-machine determinism run
- **`xfail` without `strict=True`** — a silent XPASS would let a fix land without removing the defect lock, defeating D-03
- **Importing the pipeline module in tests** — torch/dnallm unavailable CPU-side; use the AST source-contract check
- **Refactoring scripts for testability** — D-04: no production-code change; chdir + import gives full coverage without touching them

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON diff / drift vocabulary | Custom recursive comparator for goldens/determinism | `baseline/compare.py` `walk()` (importable, stdlib-only) | It IS the canonical D-06 vocabulary (TYPE/FLOAT_ULP/FLOAT_BIG/BOOL/…); a second comparator would fork the semantics [VERIFIED: baseline/compare.py:60-114] |
| JSON validation | Regex/key-set checks per file | jsonschema draft 2020-12 with `additionalProperties:false` | Enum semantics, `anyOf` number-or-`""`, `$ref` reuse, CI-friendly error paths — all free; 94 files < 1s (verified) |
| Test runner (JS) | Ad-hoc assert script | `node --test` builtin | Zero deps (no package.json — architectural constraint), stable since Node 20 |
| Known-failure mechanism | `try/except pass` smoke checks or comments | `pytest.mark.xfail(strict=True, reason="<ID> …")` | XPASS-fails forces explicit marker removal at fix time (verified live) |
| Enum maintenance | Hand-updated enum + hope | D-02 self-check test: enum ≡ metric values present in committed data | Enum and data cannot silently diverge; new metric → red test → schema update |

**Key insight:** every piece of this harness has a canonical, verified implementation path; the only genuinely novel code is the 4 schema documents and the AST contract check — both small, both reviewable.

## Common Pitfalls

### Pitfall 1: pytest 9 rejects unused parametrize argnames
**What goes wrong:** `@pytest.mark.parametrize("val,note", [...])` on a test taking only `val` → collection ERROR: `function uses no argument 'note'` — the whole module fails to collect.
**Why it happens:** pytest 9 tightened parametrize validation (hit live during this research).
**How to avoid:** every argname appears in the signature; use `pytest.param(..., id="...")` for readable ids instead of dummy columns.
**Warning signs:** `collected 0 items / 1 error`.

### Pitfall 2: `default-groups = ["data"]` silently excludes the dev group
**What goes wrong:** `uv run pytest` → pytest not found, because the repo's `default-groups = ["data"]` **replaced** uv's default `["dev"]` — setting the option overrides, not extends [CITED: docs.astral.sh/uv].
**How to avoid:** Makefile passes `--group dev` explicitly (or extend to `default-groups = ["data", "dev"]` — one-line pyproject change; explicit flags are more surgical and keep `uv sync` minimal for data-chain users).
**Warning signs:** `command not found: pytest` / `ModuleNotFoundError: pytest` under `uv run`.

### Pitfall 3: JS generator cannot be CWD-redirected and executes on import
**What goes wrong:** running `node scripts/generate-tasks-index.js` from a tmp CWD still reads/writes the REAL repo tree (`__dirname`-relative paths, lines 11-12); importing it from a test runs the generation immediately (line 78). Also IN-02: missing `task_performance/` dir → raw `readdirSync` ENOENT stack trace (verified live — backlog item, do NOT fix).
**How to avoid:** copy-script-into-fixture-tree trick (Pattern 4, verified live); the real-tree determinism test exercises it in place.

### Pitfall 4: numpy scalars leak into assertions
**What goes wrong:** `calculate_dataset_stats` returns `np.float64` values (verified live: `minmax: {'a': np.float64(0.0), …}`) — exact `==` comparisons on derived floats flake across numpy builds.
**How to avoid:** `pytest.approx` for every float assertion (TEST-02); ints (rank, samples, counts) may use `==`.

### Pitfall 5: byte-equality assumptions beyond the same machine
**What goes wrong:** PIN-VALIDATION explicitly does NOT claim cross-machine byte stability for float sums (`sum_zscore` ULP ≤ 2.41e-14 observed); aarch64 vs x86 SIMD paths can differ.
**How to avoid:** goldens compare by VALUE (compare.py `walk()`, tolerate FLOAT_ULP — or `pytest.approx` per key); the byte-identical assertion stays inside the same-machine determinism run (D-10's exact scope). Phase 5's CI drift job will need this distinction.
**Warning signs:** golden tests passing locally, failing in a different-arch environment.

### Pitfall 6: an xfail passing for the WRONG reason
**What goes wrong:** an `xfail(strict=True)` test that fails due to an import error or a broken fixture reports XFAIL even though the defect assertion never ran — a false lock.
**How to avoid:** keep each xfail body minimal and independently exercised: the WR-03 body calls `get_float` directly (the same function green tests cover); the AST test fails with `pytest.fail("construction site not found")` if the pipeline restructures, which still XPASSes-to-failure after Phase 4 — acceptable, and the message explains it.

### Pitfall 7: strict schemas vs the `""`-missing convention
**What goes wrong:** declaring metric fields `"type": "number"` fails 135+ committed entries where the value is `""`; declaring `"type": ["number", "string"]` is too loose (any string passes).
**How to avoid:** `anyOf: [{type: number}, {const: ""}]` — strictly the two legal states (verified pattern, 0 errors across all files). Same for `batch_size` (`integer` or `""` — 9 entries).

### Pitfall 8: `make data` recipe lines run in separate shells
**What goes wrong:** `cd dnallm-mark/data` on one recipe line does not affect the next line — each line is its own shell.
**How to avoid:** `cd $(DATA_DIR) && uv run …` on ONE line per script (Pattern 6), or `@cd` with backslash continuations carefully.

## Code Examples

### Schema validation test over every committed file (verified mechanism)
```python
# tests/test_schemas.py
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "dnallm-mark" / "data"

SCHEMA_FILES = {
    "model_performance": (REPO / "schemas" / "model_performance.json",
                          sorted((DATA / "model_performance").glob("*.json"))),
    "task_performance":  (REPO / "schemas" / "task_performance.json",
                          sorted((DATA / "task_performance").glob("*.json"))),
    "models_comparison": (REPO / "schemas" / "models_comparison.json",
                          [DATA / f for f in ("models_comparison.json", "models_comparison_animal.json",
                                              "models_comparison_plant.json", "models_comparison_microbe.json")]),
    "tasks_index":       (REPO / "schemas" / "tasks_index.json", [DATA / "tasks.json"]),
}

@pytest.fixture(scope="session")
def validators():
    return {name: Draft202012Validator(json.loads(p.read_text()))
            for name, (p, _) in SCHEMA_FILES.items()}

@pytest.mark.parametrize("schema_name,path",
    [(name, p) for name, (_, paths) in SCHEMA_FILES.items() for p in paths],
    ids=lambda v: getattr(v, "name", v))
def test_committed_file_matches_schema(validators, schema_name, path):
    errors = list(validators[schema_name].iter_errors(json.loads(path.read_text(encoding="utf-8"))))
    assert not errors, "\n".join(
        f"{path.name} {e.json_path} [{e.validator}]: {e.message}" for e in errors[:10])
```
Verified error-object shape (live probe): `err.json_path` → `$.performance.GUE__emp_H3.dataset.metric`, `err.validator` → `enum`, `err.message` → `'F1' is not one of ['f1', 'mcc', 'spearmanr', 'AUPRC']`.

### D-02 enum self-check test
```python
def test_metric_enum_matches_committed_data(validators):
    observed = set()
    for path in SCHEMA_FILES["model_performance"][1]:
        doc = json.loads(path.read_text(encoding="utf-8"))
        observed |= {e["dataset"]["metric"] for e in doc["performance"].values()}
    schema_enum = set(validators["model_performance"].schema["properties"]["performance"]
                      ["additionalProperties"]["properties"]["dataset"]["properties"]["metric"]["enum"])
    assert schema_enum == observed == {"f1", "mcc", "spearmanr", "AUPRC"}
```
(Exact observed set verified live: `{'f1': 1554, 'mcc': 252, 'spearmanr': 126, 'AUPRC': 42}`.)

### Determinism test skeleton (D-10)
```python
@pytest.mark.slow
def test_chain_is_deterministic_and_matches_committed(tmp_path_factory):
    """Run the full chain twice in a tmp copy of the real inputs; bytes must be
    identical between runs AND identical to the committed tree (same machine)."""
    work = tmp_path_factory.mktemp("det")
    shutil.copytree(DATA / "model_performance", work / "model_performance")
    outs = []
    for _ in range(2):
        for script in ("script/get_task_performance.py", "script/summarize_comparison.py"):
            subprocess.run([sys.executable, str(REPO / script)], cwd=work, check=True)
        # JS: copy-script trick (Pattern 4) writing into work/dnallm-mark/data/tasks.json
        outs.append({p.name: p.read_bytes() for p in work.rglob("*.json")})
    assert outs[0] == outs[1], "chain is not byte-deterministic across runs"
    for name, blob in outs[0].items():
        committed = (DATA / name)  # map regenerated names back to committed locations
        assert committed.read_bytes() == blob, f"{name} drifted from committed tree"
```
Register `slow` in `[tool.pytest.ini_options]` `markers`. Expected wall time ≈ 2 chain runs (~40s each per CONTEXT D-10) + JS — `make test-fast` excludes it.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Draft 7 schemas | Draft 2020-12 (`$defs`, `$dynamicRef`, `prefixItems`) | 2020-12 spec; jsonschema full support | Use `$defs` (not `definitions`); write `$schema: "https://json-schema.org/draft/2020-12/schema"` explicitly so `validator_for` resolves deterministically [CITED: python-jsonschema docs] |
| requirements.txt + pip | PEP 621 pyproject + PEP 735 `[dependency-groups]` + uv | uv-era | Already the Phase 1 substrate; add `dev` group, no new manifests |
| `pytest.ini` / `setup.cfg` | `[tool.pytest.ini_options]` in pyproject.toml | pytest ≥ 6.0 | One config file; keep pyproject `[project]` table intact |

**Deprecated/outdated:**
- `jsonschema.__version__` attribute access — emits DeprecationWarning in 4.26 (observed live); use `importlib.metadata.version("jsonschema")`

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | fastjsonschema is ~10-50x faster than jsonschema but with worse errors | Standard Stack/Alternatives | Low — irrelevant at 94 files/<1s either way |
| A2 | Thread-pinning env vars (`OMP/OPENBLAS/MKL/NUMEXPR/VECLIB`) suffice to stabilize numpy reductions in the test env | Pattern 5 | Low-Med — reductions here (mean/std/percentile over ≤42-element arrays) are single-threaded anyway; pinning is belt-and-braces + CI hygiene (TEST-02 mandates it regardless) |
| A3 | `$ref` across sibling schema files resolves via jsonschema's default Registry when `$id`s are absolute URLs | Pattern 1 | Low — if cross-file refs prove awkward, duplicate the `$defs` (4 small files; strictness unaffected). Executor should validate refs with `check_schema` + a smoke instance |
| A4 | `subprocess.run([sys.executable, …])` under `uv run pytest` resolves to the venv python | Pattern 3/determinism | Low — `uv run` puts the venv first on PATH and `sys.executable` IS the venv python; alternative `uv run --group data python …` from the Makefile only |
| A5 | Chain run ≈ 40s (CONTEXT D-10 figure; not independently re-timed this session) | Determinism | Low — only affects `make test` wall-clock expectations |

## Open Questions (RESOLVED)

All three questions below are resolved by the phase plans; each carries an inline RESOLVED note citing the plan/task that owns the resolution.

1. **`$defs` sharing across the 4 schema files — one shared file vs duplication?**
   - What we know: draft 2020-12 supports cross-file `$ref`; jsonschema's default registry handles it with absolute `$id`s; shapes overlap heavily (dataset entry, model card, parameters, metric block).
   - What's unclear: whether cross-file refs resolve smoothly in all validator invocations without a custom `referencing.Registry`.
   - Recommendation: start with duplication inside each file (strictness is per-file self-contained, forced versioning is the goal); consolidate only if drift becomes annoying. If sharing: `check_schema` + one smoke validation per file in Wave 0.
   - **RESOLVED — plan 02-01 (Tasks 1-2):** duplication. Every schema file is self-contained with its own `$defs` and no cross-file `$ref`; 02-01's acceptance criteria encode this explicitly ("self-contained defs, no cross-file $ref").

2. **Should `make test` include the ~80-90s determinism run, or gate it behind `make test-fast`?**
   - What we know: success criterion 1 says `make test` runs "the full local suite"; D-10 accepts ~40s/chain locally.
   - Recommendation: `make test` = full suite including slow; `make test-fast` = `-m "not slow"` for the inner loop. (Planner's call; both trivially expressible.)
   - **RESOLVED — plan 02-01 Task 1 (Makefile + pytest config), consumed by 02-03:** both lanes exist. `make test` runs with no marker filter (slow lane included); `make test-fast` runs `-m "not slow"`; the `slow` marker is registered in 02-01's `[tool.pytest.ini_options]` and applied by 02-03's determinism test.

3. **AST contract test anchor fragility across Phase 3 (dnallm dev adaptation)?**
   - What we know: Phase 3 adapts the pipeline to dnallm 0.7.1 — the construction site at 1227 may move or be restructured before Phase 4's fix.
   - Recommendation: the test's fallback `pytest.fail("construction site not found")` keeps it honest; if Phase 3 moves the site, the test needs a one-line anchor update — flag this coupling in the plan so Phase 3's executor knows the test exists and must be kept compiling.
   - **RESOLVED — plan 02-03 Task 2:** the coupling is flagged, not avoided. The AST lock keeps the honest `pytest.fail("construction site not found")` fallback, the test docstring documents the Phase 3 dnallm-dev coupling, and 02-03's artifacts_produced records the Phase 3 caution (a moved construction site gets a deliberate one-line anchor update, never a silent xfail).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (repo venv) | pytest suite, scripts under test | ✓ | 3.13.16 (`.venv`, uv-managed) | — |
| pandas / numpy | scripts under test | ✓ | 2.3.3 / 2.5.3 (locked) | — |
| pytest | test runner | ✗ (not yet installed — dev group is a Phase 2 deliverable) | 9.1.1 on PyPI | `uv add --group dev pytest` |
| jsonschema | schema validation | ✗ (same) | 4.26.0 on PyPI | `uv add --group dev jsonschema` |
| ruff | `make lint` | ✗ (same) | 0.16.10 on PyPI | `uv add --group dev ruff` |
| Node | JS generator + node:test | ✓ | v26.10.0 (node:test stable since 20) | — |
| GNU Make | entry points | ✓ | 4.3 | — |
| uv | env/lock management | ✓ | 0.12.23 (`~/.local/bin/uv`) | — |
| Network | CDN libs (Chart.js/xlsx) | not needed this phase | — | — |

**Missing dependencies with no fallback:** none — the three PyPI packages are the phase's own deliverables via the dev group.
**Missing dependencies with fallback:** none.

## Security Domain

> `security_enforcement: true`, ASVS level 1, block_on high. This phase adds offline tooling and test artifacts only — no new user-facing surface, no network calls, no secrets.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (static site, offline scripts) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | The four JSON Schemas ARE the input-validation control for the data contract (TEST-06): `additionalProperties: false` + closed enums reject malformed/shape-drifted data files; pytest enforces locally, CI in Phase 5 |
| V6 Cryptography | no | — |
| V8 Data Protection | no | No PII processed; committed benchmark metrics only |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Typosquatting/malicious dev dependency | Tampering/Elevation | Package Legitimacy Audit above (canonical repos verified); pins via committed `uv.lock`; no JS packages installed at all |
| Supply-chain via postinstall scripts | Tampering | N/A for PyPI wheels here; `uv.lock` pins exact versions+hashes |
| Fixture/golden poisoning (crafted JSON in tests) | Tampering | Fixtures are repo-committed and reviewed like code; tests parse with stdlib `json` (no eval); schemas validate real data |
| Test-time code execution from untrusted paths | Elevation | All fixture trees live under pytest `tmp_path`; no downloaded archives involved |

## Sources

### Primary (HIGH confidence — live probes in this session)
- Live probe, jsonschema 4.26.0 on Python 3.13.16: all-strict draft-2020-12 schema validated 42/42 committed `model_performance` files, 0 errors, 0.21s; error objects expose `json_path`/`validator`/`message`
- Live probe, pytest 9.1.1: `xfail(strict=True)` XFAIL-green / XPASS-fails-exit-1; `pytest.approx`; unused-parametrize collection error discovered
- Live probe, Node v26.10.0: `node --test` CJS smoke; copy-script-into-fixture-tree trick for `generate-tasks-index.js`
- Live probe, repo venv: synthetic 3-model chain (tie + missing metric) through both Python scripts under chdir — hand-verified rank expectations; `get_float('nan')` poisoning reproduced; import of `script/` pure functions verified
- Live survey, all 94 committed JSON files: exact key sets, value enums (`f1/mcc/spearmanr/AUPRC`; `Animals/Plants/Microbe`; `binary/multiclass/regression/multilabel`), field types, 9 string `batch_size` entries
- In-repo reads: `pipeline/dnallmmark_pipeline.py:1227-1268` (producer contract + species bug), `script/summarize_comparison.py` (full), `script/get_task_performance.py` (full), `scripts/generate-tasks-index.js` (full), `baseline/compare.py` (full), `baseline/PIN-VALIDATION.md`, `AUDIT.md` (AUD-01/02/07/08 rows), `pyproject.toml`, `.gitignore`, `README.md:250-261`

### Secondary (MEDIUM confidence)
- [python-jsonschema.readthedocs.io](https://python-jsonschema.readthedocs.io/en/latest/api/jsonschema/validators/) — `validator_for` signature/default-draft behavior, `Draft202012Validator`, `iter_errors`/`evolve`/`check_schema`
- [docs.pytest.org](https://docs.pytest.org/en/stable/how-to/skipping.html) — xfail marker syntax, strict semantics, `xfail_strict` ini
- [nodejs.org/api/test.html](https://nodejs.org/api/test.html) — `node --test` patterns, CJS `require('node:test')`, stability since v20
- [docs.astral.sh/uv](https://docs.astral.sh/uv/concepts/projects/sync/) + settings reference — `default-groups` default `["dev"]`, replacement semantics, `uv run` auto-sync, `--group` flag
- PyPI JSON API — jsonschema 4.26.0 / pytest 9.1.1 / ruff 0.16.10 / referencing 0.37.0 metadata (versions, requires_python, deps, classifiers, publish dates, repo URLs)

### Tertiary (LOW confidence)
- fastjsonschema performance ratio (A1) — training knowledge, not verified; decision-insensitive at this scale

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified on PyPI; every mechanism probed live on the exact versions
- Architecture: HIGH — patterns verified against the real repo + real data; no speculative machinery
- Pitfalls: HIGH — five of eight pitfalls discovered or reproduced live during this research

**Research date:** 2026-10-09
**Valid until:** 2026-11-08 (30 days — pinned via uv.lock, so library drift is a non-issue; the volatile item is only the PyPI version column)
