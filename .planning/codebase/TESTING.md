---
last_mapped_commit: a44d3104b8ab1e04ddbebed75446772fc0ca3f1b
last_mapped_at: 2026-10-08
---
# Testing Patterns

**Analysis Date:** 2026-10-08

## Test Framework

**Runner:**
- **None.** No automated test framework exists anywhere in this repository. No `jest.config.*`, `vitest.config.*`, `playwright.config.*`, `conftest.py`, `pytest.ini`, or `pyproject.toml`.
- No `package.json` — the frontend cannot even declare test dependencies.
- `.gitignore` ignores `.pytest_cache/`, `.coverage`, `htmlcov/`, and `tests/inference/pdf/` paths, but these are leftovers inherited from the upstream [DNALLM](https://github.com/zhangtaolab/DNALLM) project; no such directories or configs exist here.

**Assertion Library:**
- None.

**Run Commands:**

```bash

# There are no test commands. The closest equivalents are:

./start-server.sh                     # Serve frontend at http://localhost:8080 for manual checks
python3 -m http.server 8080           # (same, from dnallm-mark/)

cd dnallm-mark/data
python ../../script/get_task_performance.py       # Regenerate task_performance/ from model_performance/
python ../../script/summarize_comparison.py       # Regenerate models_comparison*.json

node scripts/generate-tasks-index.js              # Regenerate dnallm-mark/data/tasks.json
```

## Test File Organization

**Location:**
- Not applicable — no test files.

**Naming:**
- No `*.test.*` / `*.spec.*` files exist.

**Structure:**

```
(no test directories)

# Informal verification artifacts that exist instead:

dnallm-mark/
├── test.html            # Static, hand-authored "test report" page (Chinese) — checklist of implemented features
├── verify-chart.html    # Static scatter-chart implementation "verification report" (Chinese)
└── task-mockup.html     # Standalone static mockup of the task benchmark page (design prototype)
```

## Test Structure

**Suite Organization:**
Not applicable. The informal equivalents:

1. **Static HTML checklists** — `dnallm-mark/test.html` and `dnallm-mark/verify-chart.html` are hand-written success/warning report pages (`.test-result.success` / `.error` / `.warning` blocks) that document which features were visually confirmed. They are documentation, not executable tests.
2. **Browser console debug API** — `dnallm-mark/js/task-loader.js:353-413` exposes `window.DNALLMDebug` for live manual testing:
   ```javascript
   DNALLMDebug.cacheStats()   // cache statistics
   DNALLMDebug.clearCache()   // clear all caches
   DNALLMDebug.clearTask(id)  // clear one task cache
   DNALLMDebug.preload(id)    // manually preload a task
   DNALLMDebug.tasks()        // console.table of all tasks
   ```
3. **Data-regeneration as verification** — re-running the `script/*.py` generators over `dnallm-mark/data/model_performance/*.json` and confirming the output JSON files load in the UI is the de facto integration check.

**Patterns:**
- Setup: manual — start local server, open page, use browser devtools console.
- Teardown: `DNALLMDebug.clearCache()` for cache-related work.
- Assertion: human visual inspection of leaderboard tables / scatter chart.

## Mocking

**Framework:** None.

**Patterns:**
- No mocks, stubs, or fixtures exist.
- The nearest thing to a fixture is the committed real dataset: `dnallm-mark/data/model_performance/*_performance.json` (~60 files) and generated `models_comparison*.json`, which double as test input for the frontend and the Python scripts.

**What to Mock:**
- No guidance exists. If tests are introduced, mock `fetch()` for `DataAPI` (`js/data.js`) and `TaskLoader` (`js/task-loader.js`) network paths; mock `localStorage` for cache tests.

**What NOT to Mock:**
- The pure aggregation logic in `script/summarize_comparison.py` (`calculate_dataset_stats()`, `aggregate_models()`) and pure helpers in `js/data.js` (`normalizeToArena()`, `getColorForModel()`) take plain dicts/args and are directly unit-testable without mocks.

## Fixtures and Factories

**Test Data:**

```json
// Real example (committed): dnallm-mark/data/model_performance/DNABERT-2-117M_performance.json
{
    "info": { "name": "...", "size (M)": 117, "type": "...", "species": "..." },
    "performance": {
        "<dataset_name>": {
            "dataset": { "species": "plant", "type": "promoter", "labels": 2, "metric": "F1" },
            "parameters": { "epochs": 3, "batch_size": 8 },
            "performance": { "f1": 0.85, "auroc": 0.91, "FLOPs": 1234567890, "loss": "" }
        }
    }
}
```

The schema is documented in `README.md` ("Input Data Format") and in the docstrings of `script/get_task_performance.py:28-62` and `script/summarize_comparison.py:29-62`.

**Location:**
- `dnallm-mark/data/model_performance/` — per-model inputs (committed).
- `dnallm-mark/data/task_performance/` — generated per-dataset pivot files (committed).
- `dnallm-mark/data/tasks.json` — generated index (committed).

## Coverage

**Requirements:** None enforced. No coverage tooling configured.

**View Coverage:**

```bash

# Not available

```

## Test Types

**Unit Tests:**
- None. Best candidates if added: `calculate_dataset_stats()` / `aggregate_models()` / `get_float()` / `to_singular_species()` in `script/summarize_comparison.py`; `normalizeToArena()` / `getColorForModel()` in `js/data.js`; `determine_batch_size()` in `pipeline/dnallmmark_pipeline.py:775-791`.

**Integration Tests:**
- None automated. The data pipeline flow (model_performance JSON → `get_task_performance.py` → task_performance/ → `summarize_comparison.py` → models_comparison*.json → frontend render) is verified only manually by regenerating and reloading pages.

**E2E Tests:**
- None. Manual only: `./start-server.sh` → browse `index.html`, `task.html`, `finetuning.html`, `models.html`, `datasets.html`.

**Pipeline "testing" (ML):**
- `pipeline/dnallmmark_pipeline.py` has no tests; correctness is inferred from `final_metrics.json` / `test_metrics.json` / `{model}_performance.json` outputs written to `finetuned/{model}/{dataset}/` (`pipeline/dnallmmark_pipeline.py:1180-1265`) and TensorBoard logs.
- Resume safety relies on the `trainer_state.json` existence check rather than tests.

## Common Patterns

**Async Testing:**

```javascript
// No examples exist. The codebase's async style that tests would target:
async loadModelsComparisonByArena(arena) {
  const response = await fetch(`./data/${fileName}`);
  if (!response.ok) throw new Error(`Failed to load ${fileName}: ${response.status}`);
  ...
}
```

(`js/data.js:22-51` — retry-with-backoff variant in `js/task-loader.js:81-113`.)

**Error Testing:**

```javascript
// Client-side validation pattern a test would exercise — js/submit.js:171-206
reject(new Error(`Dataset "${key}" missing required fields (dataset, performance)`));
```

```python

# Python skip-on-error pattern — script/get_task_performance.py:105-110

except Exception as e:
    print(f"  [Skip] Failed to read file {filename}: {e}")
    continue
```

## Recommendations for New Tests (prescriptive)

When introducing tests, follow these placements to match repo layout:

- Python data-script tests: `script/test_summarize_comparison.py` (pytest, small dict fixtures mirroring the JSON schema above); run from `dnallm-mark/data/` to match the scripts' CWD-relative paths, or refactor paths to be script-relative first.
- Frontend tests: requires adding a `package.json` at repo root; place alongside modules as `dnallm-mark/js/data.test.js` (vitest) and mock `fetch`/`localStorage`.
- A fast smoke test worth writing first: `node scripts/generate-tasks-index.js` after regenerating `task_performance/`, asserting `tasks.json` count matches the number of `*_task_performance.json` files.

---

*Testing analysis: 2026-10-08*
