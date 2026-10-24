# Phase 3: Dev-Branch Reconciliation & P0 Revision Blockers - Pattern Map

**Mapped:** 2026-10-09
**Files analyzed:** 11 (new/modified)
**Analogs found:** 11 / 11 (3 via `git show origin/dev:` — the target file itself is its own base)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pipeline/run_finetune.py` (merge + F1 guard + F2 seed fix + grad_accum fix + 16 ruff fixes) | pipeline script | batch | `pipeline/dnallmmark_pipeline.py` (old pipeline, structure/conventions); base content arrives via merge from `origin/dev` | exact (self, via git show) |
| `pipeline/run_sweep.py` (NEW, F2) | pipeline driver / orchestrator | batch | `Makefile` `data` target (multi-step driver) + `script/get_task_performance.py` (main()/config-block conventions) | role-match |
| `script/make_dev_splits.py` (NEW, F1) | data-prep utility | file-I/O / transform | `script/get_task_performance.py` | exact |
| `tests/test_dev_splits.py` (NEW) | test | transform | `tests/test_aggregation.py` / `tests/test_pivot.py` (pure-function unit tests over script modules) | exact |
| `tests/test_sweep.py` (NEW, incl. dry-run) | test | batch | `tests/test_pivot.py` (fixture-driven, no GPU imports) | role-match |
| `tests/test_known_defects.py` (D-03 pivot) | test | transform | itself — existing AUD-01 companion+xfail pattern at lines 93-127, 130-178 | exact |
| `tests/fixtures/…` (D-03 defect-bearing result JSON) | test fixture | file-I/O | `tests/fixtures/golden`, `tests/fixtures/synthetic_models` | exact |
| `pyproject.toml` (dev+=ty, `[pipeline]`→`[gpu]`, `[tool.ty]`) | config | n/a | existing `[dependency-groups]` + `[tool.pytest.ini_options]` blocks (pyproject.toml:10-40) | exact |
| `Makefile` (+`typecheck`) | config | n/a | existing `lint` target (Makefile:58-59) | exact |
| `pipeline/models_info.json` + `.txt` (merge + PlantHelixSeek) | data registry | file-I/O | dev's CrossDNA entries via `git show origin/dev:pipeline/models_info.json` | exact (self) |
| `pipeline/datasets_info.json` + `.txt` (Dev columns) | data registry | file-I/O | `pipeline/datasets_info.json` on HEAD (self) + `models_info` TSV read pattern | exact (self) |
| `pipeline/dnallmmark_pipeline.py` (deprecation header) + `README.md` | docs | n/a | module docstring style of `script/get_task_performance.py` / `tests/test_known_defects.py` | role-match |

**Tracked-source check:** all named analogs verified `git ls-files` tracked in this repo; the three dev-side sources are inspected read-only via `git show origin/dev:<path>` (they become tracked by the merge itself). No gitignored mirrors used.

## Pattern Assignments

### `pipeline/run_finetune.py` (merge + F1/F2 surgical edits)

**Analog:** the file itself at `origin/dev@c6b3137` — take as-is from the merge, then edit three sites (all verified verbatim this session).

**G1 seed-isolation site** (origin/dev lines 510-517):
```python
save_root = output_dir if output_dir else "./finetuned"
model_save_name = save_model_name if save_model_name else model_name
outdir = f"{save_root}/{model_save_name}/{dataset_name}/"   # ← add /seed_{seed}/ (seed in scope as args.seed, L334)
os.makedirs(outdir, exist_ok=True)
configs["finetune"].output_dir = outdir
if os.path.exists(outdir + "trainer_state.json"):
    continue
```

**G2-class grad_accum leak** (origin/dev lines 584-598): `configs["finetune"].gradient_accumulation_steps` mutated in place (both branches) and re-read next dataset — D-07 fixes here: snapshot the YAML-default grad_accum per model, reset per dataset.

**F1 refusal guard insertion point** (origin/dev lines 520-529, guard goes immediately before):
```python
data_dict = {}
if row["Train"]:
    train_path = dataset_path + "/train.csv"
    data_dict["train"] = train_path
if row["Dev"]:
    val_path = dataset_path + "/dev.csv"
    data_dict["dev"] = val_path
```
Guard shape (from RESEARCH Pattern 4): `if not row["Dev"]: raise SystemExit(f"[REFUSED] {dataset_name} has no dev split ...")`.

**Conventions to preserve:** module-level registry reads `base_dir = os.path.dirname(os.path.abspath(__file__)) + os.sep` then `pd.read_table(base_dir + "datasets_info.txt")` (script-relative), while `./finetune_config.yaml` and `./finetuned` are CWD-relative — the sweep runner must launch with `cwd=pipeline/`. Print-based logging with `get_current_time()` timestamps matches old-pipeline convention.

**Ruff fixes (D-08):** fix all 16 findings (3 BLE001, 2 SIM102, 2 F541, 2 PLW1508, 2 I001, 1 each DTZ005/PLR0402/SIM115/FURB192/F401) in-place; style target = existing clean files (e.g. `script/get_task_performance.py`, `tests/`).

---

### `pipeline/run_sweep.py` (NEW — F2 sweep runner)

**Analog:** `Makefile` `data` target (lines 28-31) for the driver/matrix discipline; `script/get_task_performance.py` for Python structure.

**Structure pattern** (from `script/get_task_performance.py:1-60` + CLAUDE.md script conventions):
- Large module docstring: purpose, input/output JSON structures, usage command, `See also:`
- `main()` with `# ===== Configuration =====` block; `if __name__ == "__main__": main()`
- Deterministic JSON writes: `json.dump(..., indent=4, ensure_ascii=False)` + `sort_keys=True` (Phase 2 discipline) for `run_record.json` / `sweep_manifest.json` / failures manifest
- Subprocess launches with `cwd=pipeline/` (CWD-relative config; RESEARCH Pitfall 3)
- `--dry-run` mode: matrix enumeration + record writing only, no subprocess — makes it CPU-testable under D-05

**run_record.json shape:** per RESEARCH Pattern 2 — suite-native (untranslated) metric keys, seed-isolated `output_dir`, `vram_probe` sub-dict, `status ∈ {completed, failed, skipped}`. Iteration order `sorted()`.

---

### `script/make_dev_splits.py` (NEW — F1 split generator)

**Analog:** `script/get_task_performance.py` (exact role match: stdlib/numpy data-prep script, same directory, same conventions).

**Docstring pattern** (`script/get_task_performance.py:1-32`): purpose → input/output structures as JSON/CSV blocks → `Usage (run from ...)::` block → `See also:`.

**Core conventions to copy:**
- `main()` + config block; script-relative or explicitly-documented paths (NOT CWD-sensitive — improvement over old scripts per REL-04)
- Defensive reads with per-file skip + loud `[Skip]` message for malformed CSV rows
- Count-verification guard: assert registry `Train` count == on-disk CSV rows; fail loudly on mismatch (RESEARCH A4)
- Deterministic split: `sklearn.model_selection.train_test_split(stratify=..., random_state=42)` OR numpy per-class sampler (planner decision); seed=42 fixed
- Registry writes: update `Train`/`Dev` columns in BOTH `pipeline/datasets_info.json` AND `pipeline/datasets_info.txt` — **preserve CRLF endings in the .txt** (RESEARCH Pitfall 4; verified `^M$` on every row)

---

### `tests/test_known_defects.py` (D-03 pivot)

**Analog:** itself — the existing AUD-01 lock + companion is the pattern to adapt. All excerpts below from `tests/test_known_defects.py` (tracked).

**Unmarked companion pattern** (lines 93-127) — adapt to assert the fixture's contract SHAPE (dataset entries present, `species` key per entry), so fixture edits deleting the defect go RED outside the marker:
```python
def test_aud01_construction_site_anchor_is_findable_and_unique():
    sites = _find_construction_sites()
    assert sites, ("... the xfail lock is vacuous until then")
```

**xfail lock pattern** (lines 130-131, 175-178) — adapt to the export-chain contract over a FIXTURE (no AST, no pipeline import):
```python
@pytest.mark.xfail(strict=True,
                   reason="AUD-01-P0 species-as-dataset — Phase 4 fix")
def test_producer_writes_dataset_species_not_model_organism():
    ...
    assert is_row_get, (
        "dataset.species must be read from the dataset row ..."
    )
```
New contract assertion: every `entry["dataset"]["species"]` == dataset's arena category (`Animals/Plants/Microbe/Multiple` from datasets_info `Category`); fixture MUST include a defect value (`"athaliana"` or `"human+mouse"` — real values in HEAD models_info.json) so the lock fails today (Pitfall 5: probe with `pytest --runxfail`). Module docstring documents the pivot + F10 retirement in the same commit (house rule, lines 5-11).

**Fixture placement:** `tests/fixtures/` (existing dirs `golden/`, `synthetic_models/` — add e.g. `tests/fixtures/export_chain/`).

---

### `tests/test_dev_splits.py` / `tests/test_sweep.py` (NEW)

**Analog:** `tests/test_aggregation.py` / `tests/test_pivot.py` — pure-function/fixture tests, import target modules via the conftest sys.path contract.

**Import contract** (`tests/conftest.py:33-35`):
```python
sys.path.insert(0, str(REPO_ROOT / "script"))   # summarize_comparison, get_task_performance
sys.path.insert(0, str(REPO_ROOT / "baseline")) # compare (walk) for reuse
```
New modules under `script/` import the same way; ty's `extra-paths` mirrors this (see pyproject below). Tests must never import torch/dnallm (mirrors why the old lock avoided import — `test_known_defects.py:52-55`). Determinism test: same input + seed → byte-identical dev split (sorted, sort_keys). Sweep dry-run test: run `run_sweep.py --dry-run` against a tmp fixture matrix, assert records/manifest.

---

### `pyproject.toml` (dev+=ty, `[pipeline]`→`[gpu]`, `[tool.ty]`)

**Analog:** existing blocks in `pyproject.toml` (lines 10-40).

**Dependency-group pattern** (lines 15-28) — add `"ty>=0.0.85"` to `dev` (exact pin via uv.lock, comment discipline); replace `pipeline` group with:
```toml
gpu = [
    # GPU-only, NEVER installed in CI (REL-02). Definition lands Phase 3; the BUILD
    # is deferred (D-05). dnallm stays deliberately absent — local clone when runs resume.
    "torch==2.11.0",
    "transformers==5.17.0",
]
[[tool.uv.index]]
name = "pytorch-cu130"
url = "https://download.pytorch.org/whl/cu130"
explicit = true
[tool.uv.sources]
torch = [{ index = "pytorch-cu130", marker = "sys_platform == 'linux' or sys_platform == 'win32'" }]
```

**Tool-config pattern** (lines 34-40, the `[tool.pytest.ini_options]` commented block) — add `[tool.ty.environment]` / `[tool.ty.analysis]` / `[tool.ty.src]` per RESEARCH Pattern 6 (`extra-paths=["script","baseline"]`, `replace-imports-with-any` for torch/dnallm/transformers/peft/datasets, python-version "3.13"). Run `uv lock` in the same commit (Pitfall 6).

---

### `Makefile` (+`typecheck`)

**Analog:** `lint` target (Makefile:58-59), including its scope-comment convention:
```makefile
lint:
	$(UV) run --group dev ruff check tests/
```
Add (per toolchain directive):
```makefile
typecheck:
	$(UV) run --group dev ty check
```
Update `.PHONY` (line 17) and the header comment block (lines 8-14). Note D-08 changes lint scope: run_finetune.py's 16 findings are fixed this phase, so scope widening (script/, pipeline/ new files) is a deliberate decision to record in the comment — mirroring how the existing comment documents the Phase 2 scope decision.

---

### `pipeline/models_info.json` + `.txt` (PlantHelixSeek entry)

**Analog:** dev's CrossDNA entries — inspect via `git show origin/dev:pipeline/models_info.json` (11-key shape: name, size (M), type, tokenizer, mean_token_len, architecture, series, context_len (bp), species, huggingface, modelscope). Field values from the ModelScope model card (D-09: https://modelscope.cn/models/zhangtaolab/PlantHelixSeek). Land BOTH registries (RESEARCH OQ-5 recommendation): `.txt` row follows the TSV column order of `models_info.txt`; `.json` entry follows the CrossDNA key set exactly.

### `pipeline/datasets_info.json` + `.txt` (Dev columns)

**Analog:** self on HEAD; TSV read pattern `pd.read_table(base_dir + "datasets_info.txt")` (run_finetune.py L316). Update `Train` (reduced) and `Dev` (new count) for exactly the 18 enumerated tasks (RESEARCH table). CRLF preservation mandatory in `.txt`.

### `pipeline/dnallmmark_pipeline.py` + `README.md` (F10)

**Analog for deprecation docstring:** the module docstring style of `tests/test_known_defects.py:1-42` / `script/get_task_performance.py` — explain WHY (superseded by run_finetune.py), what to run instead, and that the D-03 anchor lock retires with it (same commit). README edits: replace `dnallmmark_pipeline.py` references at L154 (usage) and L318 (structure tree) with `run_finetune.py`.

## Shared Patterns

### Deterministic JSON output (Phase 2 discipline)
**Apply to:** `run_sweep.py` records/manifests, `make_dev_splits.py` outputs.
`json.dump(obj, f, indent=4, ensure_ascii=False, sort_keys=True)`; iterate `sorted()`; timestamps in run records are runtime observations (never regenerated/diffed).

### Defensive external-data reads
**Source:** `script/get_task_performance.py:105-110` (`[Skip]` per-file continue pattern) + CLAUDE.md script conventions.
**Apply to:** `make_dev_splits.py` CSV handling (dataset CSVs are Zenodo-sourced external data — V5 input validation).

### No-GPU-import test invariant
**Source:** `tests/test_known_defects.py:52-55` (why the AST lock avoided import).
**Apply to:** all new test files — never `import run_finetune` at module level in tests unless a dry-run/seam allows it; prefer fixture/subprocess patterns. ty's `replace-imports-with-any` exists for the same reason on the pipeline side.

### xfail(strict=True) + finding-ID reason + unmarked companion
**Source:** `tests/test_known_defects.py:5-11, 93-127, 130-131`.
**Apply to:** the D-03 pivoted lock (and optional G1 pre-fix lock — planner decides; G1 is a straight fix).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | | | Every file has an analog; the two genuinely novel components (`run_sweep.py` dry-run orchestration, stratified split) are covered by RESEARCH.md Patterns 2/4 plus the driver conventions above |

## Metadata

**Analog search scope:** repo root (`tests/`, `script/`, `scripts/`, `Makefile`, `pyproject.toml`, `pipeline/` on HEAD), `origin/dev` via `git show` (read-only), `tests/fixtures/`
**Files scanned:** ~15
**Pattern extraction date:** 2026-10-09
**Constraints honored:** `/home/forrest/Github/DNALLM` read-only (only cited, never proposed for edit); no working-tree writes beyond this PATTERNS.md.
