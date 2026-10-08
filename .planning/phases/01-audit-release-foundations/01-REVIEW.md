---
phase: 01-audit-release-foundations
reviewed: 2026-10-08T15:09:36Z
depth: standard
files_reviewed: 67
files_reviewed_list:
  - AUDIT.md
  - baseline/compare.py
  - baseline/data-v1.sha256
  - baseline/PIN-VALIDATION.md
  - dnallm-mark/data/models_comparison.json
  - dnallm-mark/data/models_comparison_animal.json
  - dnallm-mark/data/models_comparison_microbe.json
  - dnallm-mark/data/models_comparison_plant.json
  - dnallm-mark/data/tasks.json
  - dnallm-mark/data/task_performance/BEND__CpG_methylation_task_performance.json
  - dnallm-mark/data/task_performance/Deep4mC_datasets__C.elegans_4mC_task_performance.json
  - dnallm-mark/data/task_performance/Deep4mC_datasets__D.melanogaster_4mC_task_performance.json
  - dnallm-mark/data/task_performance/Deep4mC_datasets__E.coli_4mC_task_performance.json
  - dnallm-mark/data/task_performance/Genomic_Benchmarks__coding_task_performance.json
  - dnallm-mark/data/task_performance/Genomic_Benchmarks__human_vs_worm_task_performance.json
  - dnallm-mark/data/task_performance/Genomic_Benchmarks__regulatory_region_type_task_performance.json
  - dnallm-mark/data/task_performance/GUE__emp_H3K14ac_task_performance.json
  - dnallm-mark/data/task_performance/GUE__emp_H3K36me3_task_performance.json
  - dnallm-mark/data/task_performance/GUE__emp_H3K4me1_task_performance.json
  - dnallm-mark/data/task_performance/GUE__emp_H3K79me3_task_performance.json
  - dnallm-mark/data/task_performance/GUE__emp_H3K9ac_task_performance.json
  - dnallm-mark/data/task_performance/GUE__emp_H3_task_performance.json
  - dnallm-mark/data/task_performance/GUE__emp_H4ac_task_performance.json
  - dnallm-mark/data/task_performance/GUE__emp_H4_task_performance.json
  - dnallm-mark/data/task_performance/GUE__EPI_GM12878_task_performance.json
  - dnallm-mark/data/task_performance/GUE__fungi_species_20_task_performance.json
  - dnallm-mark/data/task_performance/GUE__human_tf_0_task_performance.json
  - dnallm-mark/data/task_performance/GUE__mouse_1_task_performance.json
  - dnallm-mark/data/task_performance/GUE__mouse_4_task_performance.json
  - dnallm-mark/data/task_performance/GUE__prom_300_all_task_performance.json
  - dnallm-mark/data/task_performance/GUE__prom_core_all_task_performance.json
  - dnallm-mark/data/task_performance/GUE__virus_covid_task_performance.json
  - dnallm-mark/data/task_performance/GUE__virus_species_40_task_performance.json
  - dnallm-mark/data/task_performance/iDNA_ABF_datasets__5mC_task_performance.json
  - dnallm-mark/data/task_performance/iDNA_ABF_datasets__6mA_task_performance.json
  - dnallm-mark/data/task_performance/iPro-WAEL_datasets__Promoter_R_capsulatus_task_performance.json
  - dnallm-mark/data/task_performance/NT_downstream_tasks__enhancers_task_performance.json
  - dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27ac_task_performance.json
  - dnallm-mark/data/task_performance/NT_downstream_tasks__H3K27me3_task_performance.json
  - dnallm-mark/data/task_performance/NT_downstream_tasks__H3K4me2_task_performance.json
  - dnallm-mark/data/task_performance/NT_downstream_tasks__H3K9me3_task_performance.json
  - dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_acceptors_task_performance.json
  - dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_all_task_performance.json
  - dnallm-mark/data/task_performance/NT_downstream_tasks__splice_sites_donors_task_performance.json
  - dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-core-promoters_task_performance.json
  - dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27ac_task_performance.json
  - dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K27me3_task_performance.json
  - dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-H3K4me3_task_performance.json
  - dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-lncRNAs_task_performance.json
  - dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-open-chromatin_task_performance.json
  - dnallm-mark/data/task_performance/PDLLMs_datasets__plant-multi-species-sequence-conservation_task_performance.json
  - dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_absolute_translation_task_performance.json
  - dnallm-mark/data/task_performance/PlantCAD2_fine_tuning_tasks__cross_species_leaf_on_off_translation_task_performance.json
  - dnallm-mark/data/task_performance/plant-genomic-benchmark__poly_a.arabidopsis_thaliana_task_performance.json
  - dnallm-mark/data/task_performance/plant-genomic-benchmark__promoter_strength.leaf_task_performance.json
  - dnallm-mark/data/task_performance/plant-genomic-benchmark__terminator_strength.leaf_task_performance.json
  - .gitignore
  - .gitleaks.toml
  - LICENSE
  - pyproject.toml
  - .python-version
  - README.md
  - requirements.txt
  - script/get_task_performance.py
  - scripts/generate-tasks-index.js
  - script/summarize_comparison.py
  - uv.lock
findings:
  critical: 0
  warning: 9
  info: 6
  total: 15
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-10-08T15:09:36Z
**Depth:** standard
**Files Reviewed:** 67
**Status:** issues_found

## Summary

Reviewed the phase 01-03 deliverables: the FIX-05 deterministic generators (`script/summarize_comparison.py`, `script/get_task_performance.py`, `scripts/generate-tasks-index.js`), the 52 migrated derived data files, the reproducibility substrate (`baseline/compare.py`, `baseline/data-v1.sha256`, `baseline/PIN-VALIDATION.md`), the release-hygiene files (`LICENSE`, `pyproject.toml`, `uv.lock`, `requirements.txt`, `.python-version`, `.gitleaks.toml`, `.gitignore`, `README.md`), and `AUDIT.md`. The 47 `task_performance/*.json` files and 4 `models_comparison*.json` + `tasks.json` were reviewed structurally (per workflow scoping), not line-by-line.

**Independent verification performed (adversarial cross-checks, not re-validation of the audit's claims):**

- Full independent recompute of the aggregation math from the 42 raw `model_performance` files (pure-Python competition ranking, `method='min'`): all 42 `rank_score` and `samples` values in `models_comparison.json` **and** in all three arena files reproduce exactly (0 mismatches). Rank ordinals are unique 1..42 and monotone in `rank_score`.
- All documented exact-tie states match AUDIT.md's post-fix migration record (microbe 448.0 flipped to alphabetical, plant 116.0 flipped, both global pairs unchanged).
- All 47 task files are structurally valid (`{info, performance}` with the 8 documented info keys; 42 model entries each with `{model, parameters, performance}`); `tasks.json` `fileName` set matches the directory exactly; count 47.
- Dataset species agrees across all 42 input files (0 disagreements — AUD-18's assumption holds today).
- `baseline/data-v1.sha256` covers exactly the 52 derived files, all present, and all 52 hashes differ from the current tree (correct pre-fix frozen baseline).
- `uv.lock` holds exactly one `numpy` and one `pandas` package block (60 packages total), consistent with PIN-VALIDATION.md.
- Input data is clean of `null`/whitespace/non-numeric primary-metric values and of NaN/Infinity.

**Assessment:** the phase's core work (determinism migration, pins, license, secret scan) is sound and verified. The findings below are residual defects: two doc/config contradictions introduced or left standing by this phase (Python version, generator filenames), two blind spots in the migration-gate comparator itself, a semantic inconsistency in the shipped efficiency metrics (`sum_PFLOPs` counted from unranked tasks), two input-data species labels that contradict the dataset's own identity, breadth in the gitleaks allowlist, and the documented-but-live Zenodo token. No BLOCKER-class defect was found.

## Warnings

### WR-01: Live Zenodo preview JWT committed in public README — residual risk untracked

**File:** `README.md:116`
**Issue:** The datasets download link embeds a full JWT preview token (`?preview=1&token=eyJ...`). AUDIT.md records this as intentional (maintainer decision D-08, read-only, record-scoped, no revocation) and the `.gitleaks.toml` allowlist exists solely to suppress it — so this is a documented decision, not an unnoticed leak. The residual defects that remain: (a) the token is a live bearer credential that will grant draft-record access to every repo visitor indefinitely, with no expiry, no rotation path, and no tracking task to revisit it; (b) when the Zenodo record is eventually published, the token becomes unnecessary but will stay in the README and in full git history unless someone remembers to swap it; (c) any future rotation breaks both this link and the `.gitleaks.toml` allowlist regex in lockstep, which is easy to get wrong.
**Fix:** Keep the D-08 decision, but add an explicit follow-up item (Phase 4 or release checklist): "replace `README.md:116` with the published record DOI/URL once record 19135551 is published, and update the `.gitleaks.toml` allowlist (or delete the rule) in the same commit." Consider a code comment next to the link pointing at AUDIT.md D-08 so editors know it is load-bearing.

### WR-02: README says Python 3.11+ while the repo pins >=3.13

**File:** `README.md:4`, `README.md:88` (vs `pyproject.toml:7`, `.python-version:1`)
**Issue:** The badge and Prerequisites section claim "Python 3.11+", but this phase committed `requires-python = ">=3.13"` (`pyproject.toml:7`) and `.python-version` = 3.13, and PIN-VALIDATION.md validated the data chain only on CPython 3.13.16. A user on 3.11/3.12 who follows the README and then runs `uv sync` (or installs the project) gets a resolver refusal, or — worse — runs the scripts under an interpreter the pins were never validated on, which is exactly the reproducibility gap the pin work exists to close.
**Fix:** Update `README.md:4` and `:88` to "Python 3.13+ (data toolchain — see `.python-version`; the GPU pipeline has its own requirements)".

### WR-03: `baseline/compare.py` diff ordering is nondeterministic across processes

**File:** `baseline/compare.py:71-76`
**Issue:** `walk()` iterates `set(a) - set(b)`, `set(b) - set(a)`, and `set(a) & set(b)` directly. String-hash randomization (`PYTHONHASHSEED`, on by default) makes set iteration order vary between Python processes, so the order of `MISSING_IN_REGEN`/`EXTRA_IN_REGEN` diffs and the recursion order over common keys vary run-to-run. `counts`, `total`, and membership are stable, but the tool's own contract says diffs are "in walk order", the human report's 8-line cap can show a different subset of diffs on each run, and any consumer diffing two `--summary-json` outputs (e.g., comparing migration inventories, or a CI golden file) gets spurious ordering noise. A determinism-validation tool whose own output is not byte-deterministic undermines its purpose.
**Fix:**
```python
for k in sorted(set(a) - set(b)):
    diffs.append(("MISSING_IN_REGEN", path + "/" + str(k), "key only in committed"))
for k in sorted(set(b) - set(a)):
    diffs.append(("EXTRA_IN_REGEN", path + "/" + str(k), "key only in regen"))
for k in sorted(set(a) & set(b)):
    walk(a[k], b[k], path + "/" + str(k), diffs)
```

### WR-04: `baseline/compare.py` cannot detect int↔float type drift and false-positives on NaN

**File:** `baseline/compare.py:67`, `baseline/compare.py:83-94`
**Issue:** Two blind spots in the numeric branch of the migration gate: (a) because line 67 exempts int/float cross-type pairs and line 88 returns early on `a == b`, a committed `5` versus regenerated `5.0` (or `47` vs `47.0`) produces **no diff at all** — yet it is a real JSON-type/byte change (e.g., a refactor leaking `numpy.float64` into count fields like `samples`/`top1_count`, which serialize as floats), which is precisely the drift class this comparator exists to catch for the D-06 gate; (b) `json.load` accepts `NaN` literals, `NaN == NaN` is False, and `rel` evaluates to NaN, which fails `rel < 1e-12` — so a NaN on **both** sides is reported as `FLOAT_BIG` (false positive). No NaN exists in the current data (verified), so (b) is latent; (a) is live risk for any future regeneration.
**Fix:** Inside the numeric branch, before the equality check, flag int/float type asymmetry (excluding the bool case already handled):
```python
if isinstance(a, bool) or isinstance(b, bool):
    ...
if a != b or isinstance(a, float) != isinstance(b, float):
    # treat equal-value int/float asymmetry as TYPE; NaN/NaN as identical
```
(or explicitly: `if a != b or (isinstance(a, int) != isinstance(b, int)): ...`, plus `if math.isnan(a) and math.isnan(b): return`).

### WR-05: `sum_PFLOPs`/`avg_PFLOPs` include FLOPs from tasks the model is not ranked on

**File:** `script/summarize_comparison.py:221-225`, `script/summarize_comparison.py:363-365`
**Issue:** FLOPs are recorded unconditionally for every model×dataset entry (lines 363-365) and accumulated whenever the model appears in the FLOPs map (lines 221-225), while ranking inclusion requires a non-empty primary metric (line 358). The two inclusion rules diverge on real data: 9 model×dataset pairs (GENERanno-eukaryote-0.5b-base ×4, GENERanno-prokaryote-0.5b-base ×4, PlantCaduceus_l32 ×1 — all `GUE__EPI_GM12878`, `GUE__fungi_species_20`, `GUE__virus_species_40`, `PDLLMs_datasets__plant-multi-species-open-chromatin`) have `FLOPs > 0` with an empty metric. Consequence in the shipped file: `GENERanno-eukaryote-0.5b-base` carries `samples: 43` (`models_comparison.json:46`) while its `avg_PFLOPs: 379.0…` is averaged over 47 tasks and `sum_PFLOPs: 17813.4…` includes ~3001 PFLOPs of compute from the 4 unranked tasks (verified by independent recompute). The public scatter chart plots these efficiency metrics against rank-derived scores, so the two axes silently use different task sets for 3 of 42 models. "Total compute spent" is a defensible semantic, but it is undocumented and inconsistent with the `samples`/`avg_raw` denominator shown next to it.
**Fix:** Either gate FLOPs accumulation on the same metric-presence check used for ranking (`if ds in dataset_stats_map and model_alias in dataset_stats_map[ds]`), or document the "compute spent including failed evaluations" semantics in the module docstring and README output-fields list, and state that `avg_PFLOPs` divides by a denominator that may exceed `samples`. Changing the gate is a number-changing fix — recompute and document before/after per the milestone's fix discipline.

### WR-06: Dataset species labels contradict the datasets' own identity (fungi → Animals, human cell line → Microbe)

**File:** `dnallm-mark/data/tasks.json:50-58` (`GUE__EPI_GM12878` → `"Microbe"`), `dnallm-mark/data/tasks.json:149` (`GUE__fungi_species_20` → `"Animals"`), and the same values in all 42 `model_performance` inputs and the arena files
**Issue:** The species label is identical across all 42 input files (verified — no AUD-18 disagreement), so the derived data is a faithful projection, but the input labels themselves contradict the dataset names: `GUE__fungi_species_20` (20-way fungi species classification) is grouped into the **animal** arena, and `GUE__EPI_GM12878` (GM12878 is a human lymphoblastoid cell line) into the **microbe** arena. These drive the public arena files (`models_comparison_animal.json` includes a fungi task's ranks; `models_comparison_microbe.json` includes a human task's ranks) and the frontend arena navigation. `GUE__emp_*` (→ Microbe) warrants the same verification while there. This is input-data provenance, pre-empted by AUD-01's Phase 4 species work — recorded here so the Phase 4 fix covers label correctness, not just the pipeline's species source.
**Fix:** During Phase 4 (AUD-01), audit all 47 dataset species values against dataset identity (fungi → Microbe or a decision record for its own bucket; EPI_GM12878 → Animals; verify `emp_*`), correct `datasets_info.json`/the model_performance inputs, and regenerate. Any change alters arena numbers — document before/after per fix discipline.

### WR-07: Documented output filenames are plural; the generator writes singular (AUD-19 persists in reviewed files)

**File:** `README.md:241-242`, `script/summarize_comparison.py:34-36`
**Issue:** Both the README's "This will generate" list and the module docstring name `models_comparison_animals.json` / `models_comparison_plants.json`, while the script writes `models_comparison_animal.json` / `models_comparison_plant.json` via `to_singular_species()` (`summarize_comparison.py:404-406`). A user following either document hits file-not-found. Pre-documented as AUD-19 (milestone backlog) but both files were in this phase's review scope and still carry the wrong names; the microbe line (`README.md:243`) is already singular, making the doc internally inconsistent too.
**Fix:** `README.md:241-242` and docstring lines 34-36: `models_comparison_animal.json`, `models_comparison_plant.json`. One-line changes, safe to fold into any Phase 2+ doc pass.

### WR-08: gitleaks allowlist path regex is unanchored — broader than the documented intent

**File:** `.gitleaks.toml:27`
**Issue:** `paths = ['''README\.md''']` is a substring match against the file path, so it also matches `docs/README.md`, `pipeline/README.md`, `README.md.bak`, etc. The audit's canary verified "a 19135551-shaped link in another file is caught", but not in *another README.md at a nested path*. Combined with the content regex `zenodo\.org/records/19135551\?preview=1&token=` (which matches any token value), a present or future record-19135551 preview link in any nested README would be silently suppressed by a scanner config whose stated purpose is to suppress "the one intentional sharing link" in the top-level README. Low probability, but this is a secret-scanner allowlist being wider than its documented contract.
**Fix:** Anchor the path: `paths = ['''^README\.md$''']` (Go regexp anchors work in gitleaks `paths`), then re-run the canary pair from AUDIT.md's secret-scan evidence to confirm both directions still hold.

### WR-09: README's data-regeneration docs omit the third generator entirely

**File:** `README.md:184-269` (Data Processing section), `README.md:271-312` (Project Structure)
**Issue:** The reproducibility story documented in README covers `summarize_comparison.py` and `get_task_performance.py` but never mentions `scripts/generate-tasks-index.js` or `tasks.json` regeneration — the Node step does not appear in Prerequisites, Data Processing, or the Project Structure tree (which lists `script/` but not `scripts/`). A maintainer following README regenerates the Python outputs and ships a stale `tasks.json` (exactly the AUD-07 failure mode this phase fixed). Relatedly, `README.md:89` attributes "Node.js 18+ (for web interface)" to the wrong consumer — the web interface is static and needs no Node; Node is needed for the index generator (and the optional `npx http-server` fallback).
**Fix:** Add a "Generate Task Index" subsection: `node scripts/generate-tasks-index.js` (run from repo root; resolves paths via `__dirname`), note the two Python scripts' CWD requirement (`cd dnallm-mark/data`) in the same place, add `scripts/` to the Project Structure tree, and correct the Node prerequisite wording.

## Info

### IN-01: Dead counter variable

**File:** `script/summarize_comparison.py:333`, `script/summarize_comparison.py:366`
**Issue:** `cnt = 0` / `cnt += 1` accumulates per-file dataset count but is never read or printed.
**Fix:** Delete both lines, or print it in the per-file progress line if a count was intended.

### IN-02: Metric-presence check is narrower than `get_float`'s missing-value semantics

**File:** `script/summarize_comparison.py:351-361`
**Issue:** Inclusion in ranking tests `value != ""` while `get_float` (the documented coercion contract) treats `None` and whitespace-only strings as missing too. A `null` or `" "` metric value would pass the gate and be ranked as a real `0.0` score, dragging every other model's rank on that task. Latent only — current data has 0 null/whitespace metric values (verified across all 42 files).
**Fix:** Derive presence from the same helper, e.g. `raw_score = get_float(..., default=None)` and gate on `raw_score is not None`, or use a shared `is_missing(val)` predicate in both places.

### IN-03: No per-file error handling in the index generator

**File:** `scripts/generate-tasks-index.js:26-27`
**Issue:** `fs.readFileSync` + `JSON.parse` run per task file with no try/catch; one malformed file aborts the whole index build with a raw stack trace. Both Python generators follow the project convention of per-file `[Skip]` + continue.
**Fix:** Wrap the per-file body in try/catch, log `` `[Skip] Failed to read ${file}: ${e.message}` ``, and continue — or at minimum document that a crash on malformed input is intended fail-loud behavior.

### IN-04: Double spaces in generated task display names

**File:** `scripts/generate-tasks-index.js:33`
**Issue:** `taskId.replace(/_/g, ' ')` converts each underscore to a space, so `BEND__CpG_methylation` becomes `"BEND  CpG methylation"` (double space from `__`); visible in the public task dropdown for every `Source__task` id.
**Fix:** Collapse runs: `taskId.replace(/_+/g, ' ').trim()` and regenerate `tasks.json`.

### IN-05: `top8_count` missing from README's documented output fields

**File:** `README.md:252`
**Issue:** The output-fields list names `top1/3/5/10_count` but the generator and all four shipped comparison files also carry `top8_count`.
**Fix:** Add `top8_count` to the documented field list.

### IN-06: `.gitignore` carries upstream-dnallm rules for paths that do not exist here

**File:** `.gitignore:85-125`
**Issue:** ~40 lines reference directories absent from this repo (`dnallm/models/downloads/`, `dnallm/data/cache/`, `dnallm/ui/tmp/`, `example/notebooks/`, `example/marimo/`, `tests/inference/pdf/`, Mkdocs `site`, `Arena/`, `instruct/`), plus duplicated `.DS_Store` (lines 77/123) and `.ipynb_checkpoints` (lines 40/90) entries. Inherited from the upstream dnallm project; noise that misleads contributors about the repo's layout in a public-release hygiene pass.
**Fix:** Trim to rules that apply to this repo (keep `datasets/`, `models/`, `finetuned/`, `logs/`, Python/venv/IDE/OS blocks); dedupe the repeats.

---

_Reviewed: 2026-10-08T15:09:36Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
