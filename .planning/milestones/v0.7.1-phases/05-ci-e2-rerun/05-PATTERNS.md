# Phase 5: CI & Three-Seed Full Re-Run (E2') - Pattern Map

**Mapped:** 2026-10-10
**Files analyzed:** 17 (new + modified)
**Analogs found:** 15 / 17 (2 greenfield: CI workflow, CHANGELOG/DATA docs)

> All analog paths below are git-tracked repo source (verified against the working
> tree at HEAD 77d33bf; none live under a gitignored mirror).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `script/summarize_comparison.py` (EDIT) | service (offline aggregation) | batch/transform | itself + `script/export_runs.py` vendored stats | exact |
| `script/export_runs.py` (EDIT — bridge per OQ1) | service (exporter) | batch/transform | itself; emitter sections | exact |
| `dnallm-mark/js/main.js` (EDIT — view toggle, footer stamp) | component (page controller) | request-response (fetch→render) | itself; existing `x-scale-toggle` idiom | exact |
| `dnallm-mark/js/config.js` (EDIT — view constants) | config | — | itself; `FILTER_OPTIONS` / `SCATTER_CONFIG` blocks | exact |
| `schemas/models_comparison.json` (EDIT — weighted-view fields) | config (contract) | — | itself; existing 15-key performance block | exact |
| `.github/workflows/ci.yml` (NEW) | config (CI) | batch | none in repo — use RESEARCH.md skeleton; command surface from `Makefile` | none (RESEARCH) |
| `eslint.config.mjs`, `.htmlvalidate.json` (NEW) | config | — | none in repo | none (RESEARCH) |
| `tests/test_ci_replay.py` (NEW) | test | batch/transform | `tests/test_export_runs.py` | exact |
| `tests/test_audit_n.py` (NEW) | test | file-I/O | `tests/test_export_runs.py` fixture style + `tests/test_dev_splits.py` CSV fixtures | role-match |
| `tests/fixtures/e2_replay/` (NEW) | test fixture | file-I/O | `tests/test_export_runs.py::_build_fixture_tree` / `_write_run_record` | exact |
| `script/audit_n_frequencies.py` (NEW) | service (audit) | file-I/O/batch | `script/export_runs.py` (docstring+CLI structure), `script/make_dev_splits.py` (CSV reading) | role-match |
| `pipeline/run_finetune.py` (EDIT — `--subset_file`) | service (pipeline) | batch | itself; existing argparse `parse_args()` + `_validate_filters`-style fail-fast (in run_sweep) | exact |
| `pipeline/run_sweep.py` (EDIT — priority + `--from-failures`) | service (sweep driver) | batch | itself; `enumerate_matrix` / `_validate_filters` / `sweep_failures.json` | exact |
| `pipeline/env_smoke.py` (NEW, never executed) | utility (gate check) | request-response (check→exit code) | `pipeline/run_sweep.py` module-banner + exit contract; `Makefile.check-node` guard style | partial |
| `script/run_migration_inventory.py` (NEW thin orchestrator) | utility | batch | `tests/test_golden.py` (loops `compare.py walk` / `--summary-json` over a file set — the plan-01-03 pattern) | role-match |
| `CHANGELOG.md` (NEW) + `DATA.md` (NEW) | docs | — | no in-repo analog; format defined by RESEARCH Pattern 7 | none (RESEARCH) |
| `Makefile` (EDIT — ci lane), `README.md` (EDIT — badge), `pyproject.toml` (EDIT — `ci` marker) | config | — | themselves | exact |

## Pattern Assignments

### `script/summarize_comparison.py` — tie rule + dual view (service, batch/transform)

**Analog:** the file itself; CI math imported from `script/export_runs.py`.

**Tie-rule seam** (`script/summarize_comparison.py:192-195`, verbatim):
```python
ranks = pd.Series(scores).rank(ascending=False, method='min').values
# Convert ranks to competitive points: rank 1 earns N-1, last earns 0.
task_rank_scores = N - ranks
```
`method='min'` already gives exact-tie sharing; the CI-overlap rule widens "tie" to interval overlap and must keep `task_rank_score = N - rank` coherent via min-rank over tie-groups.

**Weighted-view field emission** (`script/summarize_comparison.py:296-313`): the `aggregated_results[model_alias]["performance"]` dict literal is where the new weighted-view field(s) get added — mirror the `sum_zscore` line (`sum(s['zscore'] for s in model_m_stats)`); weighted = `sum_zscore / len(target_tasks_in_view)` per uniform 1/N_tasks weighting. Keep the no-imputation convention (comment at :291-293 "Tasks where the model did not run are implicitly zero").

**Statistical vocabulary — NEVER re-implement** (`script/export_runs.py:122-130, 133-208`): import `aggregate_seeds` (and `CI_MIN_SEEDS`, `BOOTSTRAP_MIN_SEEDS`) from `export_runs`. Semantics: `n<3 → ci95 None/method "none"`; `3<=n<10 → t-interval` (`stats.t.ppf(0.975, n-1)`); `n>=10 → seeded bootstrap`. E2' n=3 ⇒ t-interval df=2. `tests/test_vendored_stats.py` pins this.

**Script docstring/structure convention** (whole file): large module docstring → `main()` with `# ===== Configuration =====` block → relative-path `input_dir = 'model_performance'` (:333) — NOTE: the OQ1 bridge likely adds a task-centric input mode here; if so, follow `export_runs.py`'s REPO_ROOT-relative argparse style (:217 `REPO_ROOT = Path(__file__).resolve().parents[1]`, :76-82 usage block) rather than the CWD-sensitive convention.

### `script/export_runs.py` — data-chain bridge (service, batch/transform)

**Analog:** itself. The bridge (OQ1 Option B/C: per-model emitter) copies the existing per-task emitter's join/aggregate/emit structure: hard-fail registry lookups (docstring :21-23), sorted iteration + `sort_keys=True` + no live clock for byte-stability (:43-46), `--input-root/--output-dir/--stats-dir` CLI (:76-82). `run_finetune.py:899-910` marker-copy ordering and `export_runs.py:478-484` (missing `total_flos` hard error) govern what a replay fixture must contain.

### `dnallm-mark/js/main.js` + `js/config.js` — view toggle, weighted default, footer stamp

**Analog:** the existing toggle idiom in the same file.

**Toggle idiom** (`dnallm-mark/js/main.js:222-228` — x-scale toggle state sync, verbatim):
```javascript
const scaleSwitch = document.getElementById('x-scale-toggle');
if (scaleSwitch) {
  scaleSwitch.querySelectorAll('button').forEach(btn => {
    const isLog = btn.dataset.scale === 'log';
    btn.classList.toggle('active', isLog === this.state.xAxisLog);
  });
}
```
Add `this.state.currentView` ('weighted' | 'rank', default 'weighted') next to `currentSort: 'rank_score'` (:14-15 area) in the single `this.state` object; buttons rendered in `leaderboard-controls` exactly as `CONFIG.FILTER_OPTIONS` is mapped at :370-377 (`data-filter="${option.id}"`, `active` class); on switch → `filterAndSortModels` with view-derived sort field → `renderScatterChart` (y-axis currently `model.performance?.rank_score || 0` at :236 and y-title 'Rank Score (higher = better)' at :327 — both become view-derived) → `renderLeaderboard`. Chart destroy-first convention applies.

**Footer stamp (DATA-06)** — REPLACE, don't augment, `js/main.js:367`:
```javascript
<small>Updated: ${new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</small>
```
with a value stamped in the data artifacts (OQ2: `tasks.json` version field or `data/manifest.json`), never a live clock.

**Config constants** (`dnallm-mark/js/config.js:27-31, 85-101`): add view options as a `VIEW_OPTIONS` array mirroring `FILTER_OPTIONS`; scatter axis labels per view go in `SCATTER_CONFIG.HOME`.

### `schemas/models_comparison.json` — field extension (contract)

**Analog:** itself. Performance block is `additionalProperties: false` with a 15-key required set (:35-54). New weighted fields must be added to BOTH `required` and `properties` in the SAME commit as data + re-chained goldens (tests/test_golden.py:29-32 — "goldens are chain-produced, never hand-edited"). Follow the existing `{ "type": "number" }` property style.

### `tests/test_ci_replay.py` + `tests/fixtures/e2_replay/` (test, batch)

**Analog:** `tests/test_export_runs.py` — the fixture builders to commit-under-`tests/fixtures/` instead of tmp_path.

**Fixture builder pattern** (`tests/test_export_runs.py:89-114, 196-235`, condensed):
```python
def _write_run_record(root, model, task, seed, metrics, *, status="completed", ...):
    seed_dir = root / model / task / f"seed_{seed}"
    seed_dir.mkdir(parents=True)
    record = {"model": model, "task": task, "seed": seed, "status": status,
              "output_dir": str(seed_dir), "metrics": metrics, ...}
    (seed_dir / "run_record.json").write_text(json.dumps(record), encoding="utf-8")
    (seed_dir / "trainer_state.json").write_text(json.dumps({"global_step": global_step}), encoding="utf-8")
```
plus `_registry_files` (:126-152, registry slices incl. a `Multiple`-Category dataset) and `FINETUNE_CONFIG_YAML` (:155-169). The committed `tests/fixtures/e2_replay/` tree is exactly this shape (run_record + trainer_state + final_metrics + config slice + registry slices); the replay test calls `export_runs.export_runs_tree(root, models, datasets, config, out, stats, n_bootstrap=2000, bootstrap_seed=42, small_n_ci="t-interval")` (the `_export` helper, :226-236), then asserts schema validation and a deliberately-overlapping fixture pair ties.

**Golden-comparison idiom** (`tests/test_golden.py:46-47`): `from compare import walk` — value-compare regenerated files via `baseline/compare.py`'s vocabulary; assert `diffs == []`.

### `script/audit_n_frequencies.py` (NEW — N audit)

**Analog:** `script/export_runs.py` for module structure (banner docstring with Purpose/Direction-of-truth/Usage; REPO_ROOT-relative argparse; hard-fail registry joins), `script/make_dev_splits.py` for CSV reading of untrusted data (per-row skip, `[Skip]` messages). Registry read pattern: `json.load(open(registry_dir / "datasets_info.json", "r", encoding="utf-8"))` as in `run_sweep.enumerate_matrix` (:213-216). Missing-dataset dirs skip-with-warning (7 GUE dirs absent — RESEARCH Pitfall 8). Subset semantics MUST mirror `check_sequence`: charset `ACGTacgt|` + `|` separator, minl 0, maxl 10010 (see `run_finetune.py:832-839`).

### `pipeline/run_finetune.py` — `--subset_file` (service, batch)

**Analog:** its own argparse + the validated call site.

**Integration point** (`pipeline/run_finetune.py:795-839`, verbatim seam):
```python
dataset = DNADataset.load_local_data(
    data_dict, seq_col="sequence", label_col="label",
    multi_label_sep=multi_label_sep, max_length=max_length
)
# ... later:
dataset.validate_sequences(minl=0, maxl=10010, valid_chars=valid_chars)
```
Insert between them: `dataset.dataset["test"] = dataset.dataset["test"].select(subset_ids)` (HF `select` — same primitive as the suite's `sampling()`). Apply BEFORE `validate_sequences`.

**CLI flag pattern**: copy an existing `parser.add_argument(...)` block from `parse_args()` (:56-190); validate the JSON subset file fail-fast, mirroring `run_sweep._validate_filters` (:236-280): known task keys via registry join, integer IDs in range, `sys.exit("[Error] ...")` on problems. Absent flag = exact current behavior.

### `pipeline/run_sweep.py` — priority ordering + `--from-failures` (service, batch)

**Analog:** itself.

- Ordering seam: `pipeline/run_sweep.py:439` `for model, task, seed in sorted(cells):` — compose priority sort with `sorted()` as stable fallback inside/around `enumerate_matrix` (:197-233).
- Failures manifest: `FAILURES_NAME = "sweep_failures.json"` (:137), written every run (:533-538). `--from-failures <path>` = filter enumerated cells to manifest entries; validate manifest keys against registries exactly as `_validate_filters` does (:263-280).
- Tests: fake-executor discipline from `tests/test_sweep.py`.

### `pipeline/env_smoke.py` (NEW — PIPE-02 gate, never run by agents)

**Analog:** `run_sweep.py` module banner/comment discipline + `Makefile:53-54` guard's actionable-error + nonzero-exit contract. Checkable surface: assert pinned `torch.__version__`/`transformers.__version__` match `[gpu]` group (`pyproject.toml:33-36`), `import dnallm` resolves, `torch.cuda.is_available()` + device count, print PASS/FAIL lines, `sys.exit(1)` on failure. ty stays green via `replace-imports-with-any` (`pyproject.toml:64`); add the file to the Makefile `lint` list (:79-80).

### `script/run_migration_inventory.py` (NEW — data-v2 gate orchestrator)

**Analog:** `tests/test_golden.py`'s pattern of looping `compare.py` (`from compare import walk`) over a file set; `baseline/compare.py:34-42` `--summary-json` is the machine-readable diff contract (`{committed, regen, total, counts, diffs}`). SHA256 manifest line format: `<sha256>  <path>` (two spaces) per `baseline/data-v1.sha256` / `script/freeze_snapshot.py:6-10`. Thin orchestrator only — no comparator edits. Never creates the `data-v2` tag (maintainer gate).

### `Makefile` / `pyproject.toml` / `README.md` (config edits)

- **Makefile:** extend the `.PHONY` line (:24) and add a `ci` lane using the existing `$(UV) run --group dev ...` invocation style (:56-61); update the header comment block.
- **pyproject.toml `ci` marker** (`pyproject.toml:74-80`, verbatim shape):
```toml
markers = [
    "slow: long-running real-tree regression tests; excluded by make test-fast",
]
```
append `"ci: pinned CI lane — metric-key parity, species spot checks, aggregation units, golden replay"`.
- **README badge:** RESEARCH Code Examples gives the exact markdown (repo slug `zhangtaolab/dnallmmark`, verified via schemas `$id`).

## Shared Patterns

### Statistical vocabulary (one source)
**Source:** `script/export_runs.py:122-208` (`aggregate_seeds`, `CI_MIN_SEEDS`, `BOOTSTRAP_MIN_SEEDS`)
**Apply to:** tie rule in summarize_comparison, any CI emission, replay test assertions. Import, never re-implement. E2' n=3 → t-interval df=2, never bootstrap.

### One-commit migration discipline (schema/goldens/data)
**Source:** `tests/test_golden.py:29-32` + `schemas/models_comparison.json:35-54`
**Apply to:** the F6 aggregation change. Code + schema `required`/`properties` extension + regenerated 4 comparison files + re-chained goldens land together; `make data` must be a byte-identical no-op on the committed tree BEFORE the CI drift job goes live.

### Precomputed offline, rendered client-side
**Source:** the dead `recalculateComparison()` cautionary tale; rendering surfaces at `js/main.js:236, 327, 388`
**Apply to:** the weighted view — computed in `summarize_comparison.py`, selected (never computed) in `js/main.js`.

### Fail-fast filter validation
**Source:** `pipeline/run_sweep.py:236-280` (`_validate_filters`)
**Apply to:** `--subset_file`, `--priority-file`, `--from-failures` — registry-join key validation, integer range checks, `sys.exit("[Error] ...")` listing all problems.

### Untrusted-data parsing
**Source:** repo `[Skip]` convention (`script/get_task_performance.py:105-110` per CLAUDE.md); `run_finetune.py:832-839` charset/maxl semantics
**Apply to:** `audit_n_frequencies.py` CSV reading (per-row skip, no eval, bounded parsing) and the common-subset computation (charset `ACGTacgt|`, maxl 10010).

### GPU-side isolation in typecheck/lint
**Source:** `pyproject.toml:64` (`replace-imports-with-any`), `Makefile:79-80` (explicit lint file list)
**Apply to:** `pipeline/env_smoke.py` and any new pipeline file — ty handles torch/dnallm imports automatically; the file must be ADDED to the Makefile lint list.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.github/workflows/ci.yml` | config (CI) | batch | No `.github/` exists; use RESEARCH.md SHA-pinning skeleton + Makefile command surface |
| `CHANGELOG.md`, `DATA.md` | docs | — | No in-repo doc registry; format defined by RESEARCH Pattern 7 / CONTEXT DATA-Q2 |
| `eslint.config.mjs`, `.htmlvalidate.json` | config | — | Greenfield; flat-config guidance in RESEARCH SOTA table (inline browser globals, no `globals` npm package) |

## Metadata

**Analog search scope:** `script/`, `pipeline/`, `tests/`, `schemas/`, `baseline/`, `dnallm-mark/js/`, `Makefile`, `pyproject.toml`, `.planning/phases/03-*, 04-*`
**Files scanned:** ~25
**Pattern extraction date:** 2026-10-10
