# Phase 2: Data Contracts & Test Harness - Pattern Map

**Mapped:** 2026-10-09
**Files analyzed:** 16 (new + modified)
**Analogs found:** 8 / 16 (the test harness, schemas, and Makefile have NO existing in-repo analogs — this repo has zero tests today; for those, RESEARCH.md's live-verified patterns are the source of truth)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `schemas/model_performance.json` | config (contract) | n/a (declarative) | RESEARCH.md Pattern 1 (live-validated against all 42 files) | none in repo |
| `schemas/task_performance.json` | config (contract) | n/a | RESEARCH.md Pattern 1 (`$defs` reuse) | none in repo |
| `schemas/models_comparison.json` | config (contract) | n/a | RESEARCH.md Pattern 1 (7-key model block, 15-key performance block) | none in repo |
| `schemas/tasks_index.json` | config (contract) | n/a | `scripts/generate-tasks-index.js:45-62` (the 9-key entry shape it encodes) | producer-as-spec |
| `tests/conftest.py` | test infrastructure | n/a | RESEARCH.md Pattern 5 (thread pinning + sys.path) | none in repo |
| `tests/test_schemas.py` | test | batch (94-file validation) | RESEARCH.md Code Examples (parametrized validator) | none in repo |
| `tests/test_aggregation.py` | test (unit) | transform | Code under test: `script/summarize_comparison.py` pure functions | exact target |
| `tests/test_pivot.py` | test (integration) | batch (chdir + main()) | `script/get_task_performance.py:75-165` | exact target |
| `tests/test_golden.py` | test (golden) | batch | `baseline/compare.py` `walk()` (reuse, don't re-implement) | exact tool |
| `tests/test_determinism.py` | test (slow/regression) | batch | `baseline/compare.py` + RESEARCH.md determinism skeleton | exact tool |
| `tests/test_known_defects.py` | test (xfail locks) | n/a | `baseline/compare.py:90-106` (WR-02 site), `script/summarize_comparison.py:80-96` (WR-03 site), `pipeline/dnallmmark_pipeline.py:1229` (AUD-01 site, AST check) | exact targets |
| `tests/fixtures/synthetic_models/` + `tests/fixtures/golden/` | test fixture | n/a | `dnallm-mark/data/model_performance/*.json` (one real file as shape template) | shape template |
| `tests/js/generate-tasks-index.test.js` | test (node:test) | batch | RESEARCH.md Pattern 4 (copy-into-fixture-tree, verified live) | none in repo |
| `Makefile` | build/config | n/a | RESEARCH.md Pattern 6 (uv invocation, verified) | none in repo |
| `pyproject.toml` (modify) | config | n/a | itself (`pyproject.toml:10-25` — extend dev group + add `[tool.pytest.ini_options]`) | exact |
| `README.md` (modify, IN-03) / `.gitignore` (modify, IN-04) | docs/config | n/a | themselves | exact |

## Pattern Assignments

### `tests/test_aggregation.py` — code under test: `script/summarize_comparison.py`

The four importable pure functions (verified side-effect-free; import via `sys.path.insert(0, REPO/"script")` in conftest):

**`get_float(val, default=0.0)`** (`script/summarize_comparison.py:80-96`) — the WR-03 xfail target. Note: `float('nan')` succeeds, so non-finite values return `nan` today:

```python
def get_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(val)
    except (ValueError, TypeError):
        return default
```

**`calculate_dataset_stats(dataset_records)`** (`:99-161`) — rank/MinMax/z-score/robust. Returns `np.float64` scalars → every float assertion must use `pytest.approx` (TEST-02). Tie semantics anchor (`:133-136`):

```python
ranks = pd.Series(scores).rank(ascending=False, method='min').values
task_rank_scores = N - ranks
```

**`to_singular_species(name)`** (`:164-184`) — pure mapping; trivially unit-testable.

**`aggregate_models(...)`** (`:187-267`) — sums per-task stats; missing task = no contribution (`:218-230`); final rank by `rank_score` desc (`:259-267`). `avg_PFLOPs` computed at `:253`.

**`main()` config block** (`:270-278`) — CWD-relative `input_dir = 'model_performance'` resolved at call time inside `main()`, which is what makes the `monkeypatch.chdir(tmp_path)` chain tests work.

### `tests/test_pivot.py` — code under test: `script/get_task_performance.py`

Drive `main()` under `monkeypatch.chdir(tmp_path)`. Config block at `:75-89` (`input_dir`/`output_dir` are locals → chdir-safe). Per-file skip pattern (`:105-110`), filename→model-key derivation (`:119`), pivot loop (`:124-142`), sanitized output filenames (`:155`) with `json.dump(..., indent=4, ensure_ascii=False, sort_keys=True)` (`:159`). Synthetic fixtures must follow the model alias convention: file `{alias}_performance.json` → key `{alias}`.

### `tests/test_golden.py` + `tests/test_determinism.py` — REUSE `baseline/compare.py`, never re-implement comparison

**`walk(a, b, path, diffs)`** (`baseline/compare.py:60-114`) — the canonical order-insensitive comparator and the D-06 diff vocabulary (TYPE / MISSING_IN_REGEN / EXTRA_IN_REGEN / LEN / BOOL / FLOAT_ULP / FLOAT_BIG / VALUE). Import as `from compare import walk` with `sys.path` entry for `baseline/`. Goldens compare by VALUE (tolerate FLOAT_ULP); byte-identical assertions are reserved for the same-machine determinism run only. Exit-code contract (`:40-43`): 0 identical / 1 diffs / 2 load error — reuse in the determinism test rather than parsing stdout.

Key excerpt (the diff classification the golden tests rely on):

```python
if a == b:
    if isinstance(a, float) != isinstance(b, float):
        diffs.append(("TYPE", path, f"{type(a).__name__} vs {type(b).__name__}"))
    return
rel = abs(a - b) / max(abs(a), abs(b), 1e-300)
if rel < 1e-12:
    diffs.append(("FLOAT_ULP", path, f"{a!r} vs {b!r} rel={rel:.2e}"))
else:
    diffs.append(("FLOAT_BIG", path, f"{a!r} vs {b!r} rel={rel:.2e}"))
```

### `tests/test_known_defects.py` — xfail(strict=True) locks (house style per D-03/D-07)

All three defect sites are read-only targets this phase (no production change):

- **WR-02** — `baseline/compare.py:90-94`: equal-value bool/int cross-type pairs take the BOOL branch and stay silent when equal (`if a != b` → no diff for `True` vs `1`). Test: `walk(True, 1, "", diffs); assert diffs`.
- **WR-03** — `script/summarize_comparison.py:94` (`return float(val)`) passes NaN/inf through the presence gate. Test: `get_float('nan', default=None) is None`.
- **AUD-01-P0** — `pipeline/dnallmmark_pipeline.py:1229` reads `"species": model_row.get("species", "unknown"),` while every sibling field (`:1230-1236`) reads `row.get(...)`. Test via AST parse of the source (pipeline is unimportable CPU-side: torch/dnallm at `:16-18`); full verified AST test body is in RESEARCH.md Pattern 2.

Marker convention (D-decision): `@pytest.mark.xfail(strict=True, reason="AUD-01-P0 species-as-dataset — Phase 4 fix")` — finding ID in the reason string, always `strict=True`.

### `tests/js/generate-tasks-index.test.js` — target: `scripts/generate-tasks-index.js`

CJS, executes `generateTaskIndex()` at module load (`:78`), paths are `__dirname`-relative (`:11-12`) → NOT CWD-redirectable, NOT importable without side effects. The verified test mechanism is copy-script-into-fixture-tree (RESEARCH.md Pattern 4). Behaviors to assert, per source: filename filter `.endsWith('_task_performance.json')` + `.sort()` (`:18-20`); per-file `[Skip]` on malformed JSON (`:27-36`); taskId strip (`:39`); displayName `/_+/g` collapse (`:43`); defensive projections `data.info?.species || 'Unknown'` etc. (`:49-54`); output `{version, count, tasks}` with `JSON.stringify(index, null, 2)` (`:58-65`).

### `pyproject.toml` (modify)

Extend existing structure (`pyproject.toml:10-25`): fill `dev = []` with `pytest`/`jsonschema`/`ruff` via `uv add --group dev`; add `[tool.pytest.ini_options]` with the `slow` marker registered and testpaths. Do NOT touch `default-groups = ["data"]` (`:25`) — the Makefile must pass `--group dev` explicitly (RESEARCH.md Pitfall 2). Keep the header comment style (dated provenance notes).

### Fixture shape template — `dnallm-mark/data/model_performance/*.json`

Synthetic `{alias}_performance.json` fixtures must replicate the exact uniform shape (live survey, 42 files): `info` 11 keys, per-dataset `performance` 3 sub-objects (`dataset` 8 keys / `parameters` 9 keys / `performance` 14 keys). Missing metrics are `""` (never null/0); include one exact-tie pair and one missing-metric model (D-09). Read one committed file (e.g. the first in `sorted()`) as the literal shape reference when authoring fixtures.

## Shared Patterns

### xfail(strict=True) known-defect locking
**Source:** RESEARCH.md Pattern 2 (verified live on pytest 9.1.1)
**Apply to:** `tests/test_known_defects.py` only — every marker carries the finding ID and `strict=True`; no bare `xfail` anywhere in the suite.

### Float tolerance policy (TEST-02)
**Apply to:** every float assertion in all Python tests — `pytest.approx` mandatory (functions return `np.float64`); plain `==` allowed only for ints (rank, samples, counts). Thread pinning env vars set in `conftest.py` top-level before any test-module numpy import.

### Test-file Python conventions (match repo style)
**Apply to:** all files under `tests/` — module docstring header, Google-style docstrings with `Args:`/`Returns:` and RST double backticks, `# =====` section banners, 4-space indent. Mirror `script/summarize_comparison.py:1-72` and `baseline/compare.py:1-51` docstring style. English only is fine; bilingual acceptable.

### JSON I/O convention
**Apply to:** any test code that reads/writes fixture or output JSON — `open(path, encoding="utf-8")` / `json.dump(..., indent=4, ensure_ascii=False, sort_keys=True)` (see `script/get_task_performance.py:158-159`).

### Makefile / node invocation (RESEARCH.md Pattern 6, verified)
`uv run --group dev` (explicit — Pitfall 2); one `cd $(DATA_DIR) && …` per recipe line (Pitfall 8); JS step runs plain `node` from repo root (`__dirname`-relative); `node --test tests/js/` explicit path; `.PHONY` targets.

## No Analog Found

| File | Role | Reason |
|------|------|--------|
| `schemas/*.json` (all 4) | contract | No schemas exist in repo; use RESEARCH.md Pattern 1 (live-validated strict fragment) — it IS the pattern |
| `tests/conftest.py` | test infra | First pytest suite in repo; RESEARCH.md Pattern 5 is the verified template |
| `Makefile` | build | No makefile exists; RESEARCH.md Pattern 6 is the verified template |
| All `tests/test_*.py` | test | No test files exist anywhere in the repo (CLAUDE.md: "Not detected"); RESEARCH.md Code Examples are verified templates |
| `tests/js/generate-tasks-index.test.js` | test | First JS test; RESEARCH.md Pattern 4 is the verified template |

For every "no analog" file above, the RESEARCH.md patterns were themselves verified live against the real repo/data in the research session — treat them as the concrete patterns to copy, not abstractions.

## Metadata

**Analog search scope:** repo root, `script/`, `scripts/`, `baseline/`, `pipeline/`, `dnallm-mark/data/` (confirmed: no tests, no schemas, no Makefile, no CI config exist)
**Files scanned:** 8 relevant sources read in full/targeted
**Tracked-source check:** all named analogs (`script/summarize_comparison.py`, `script/get_task_performance.py`, `baseline/compare.py`, `scripts/generate-tasks-index.js`, `pipeline/dnallmmark_pipeline.py`, `pyproject.toml`) are tracked source in the main worktree.
**Pattern extraction date:** 2026-10-09
