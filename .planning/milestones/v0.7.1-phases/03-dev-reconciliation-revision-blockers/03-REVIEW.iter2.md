---
phase: 03-dev-reconciliation-revision-blockers
reviewed: 2026-10-10T00:00:00Z
depth: standard
files_reviewed: 19
files_reviewed_list:
  - Makefile
  - README.md
  - pipeline/datasets_info.json
  - pipeline/dnallmmark_pipeline.py
  - pipeline/models_info.json
  - pipeline/run_finetune.py
  - pipeline/run_sweep.py
  - pyproject.toml
  - script/convert_registry.py
  - script/make_dev_splits.py
  - tests/conftest.py
  - tests/fixtures/export_chain/defect_species_performance.json
  - tests/test_convert_registry.py
  - tests/test_dev_splits.py
  - tests/test_known_defects.py
  - tests/test_model_registry.py
  - tests/test_registry_unification.py
  - tests/test_run_finetune_contracts.py
  - tests/test_sweep.py
findings:
  critical: 2
  warning: 10
  info: 6
  total: 18
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-10-10
**Depth:** standard
**Files Reviewed:** 19 (uv.lock excluded per scope rules — generated lockfile, spot-checked for consistency with pyproject only)
**Status:** issues_found

## Summary

The phase's core deliverables are largely solid and verifiably green: I re-ran
`pytest -m "not slow"` (177 passed + 5 xfailed, matching the claimed 178 full-lane),
`ruff check` and `ty check` over the declared scopes — both clean. The unified
registries verify exactly against their pinned contracts (62 models / 50 datasets,
`key == Model_name`/`Dataset_name` everywhere, operational fields complete, all
Train/Dev/Test/Index/length/labels are ints > 0, and both files byte-roundtrip under
the `indent=4, sort_keys=True, ensure_ascii=False` + trailing-newline discipline).
The registry unification (D-10), dev-split carving policy (F1), seed-isolated
outdirs (G1), and the sweep driver's argv/cwd subprocess contract all hold up under
direct inspection. Two of the phase's flagged sensitivities are confirmed as real
latent defects (grad_accum snapshot placement; special-model handling lost in the
active pipeline), and the sweep's failure accounting has a gap that mislabels failed
trainings as `completed`.

The two central problems, both worth fixing before any real sweep runs:

1. **The active entry point lost model-quirk handling that this same phase
   re-affirmed in the deprecated file.** The phase commit added the three CrossDNA
   models to the *deprecated* pipeline's `models_only_support_fp32` list, while
   `run_finetune.py` — the file the sweep actually launches — has no fp32 handling
   at all and the global config sets `bf16: True` (CR-01), plus three more
   unported/diverged quirk registries (WR-03, WR-04).
2. **`run_sweep.py` records `completed` for cells whose training actually failed**,
   because `run_finetune.py`'s designed blind-except isolation makes the subprocess
   exit 0 after a training failure (CR-02).

Known, deliberately-locked defects (AUD-01 species-as-dataset at
`pipeline/dnallmmark_pipeline.py:1248`, WR-02 bool/int comparator silence, WR-03
non-finite `get_float` pass-through) are pinned by `xfail(strict=True)` locks in
`tests/test_known_defects.py` and routed to Phase 4 — they are not re-reported here
as new findings.

## Critical Issues

### CR-01: fp32-only model handling absent from the active entry point while the same phase added CrossDNA to the deprecated file's fp32 list

**File:** `pipeline/run_finetune.py:383-397` (special-case lists), `pipeline/finetune_config.yaml:53` (`bf16: True`); contrast `pipeline/dnallmmark_pipeline.py:881-883` and `pipeline/dnallmmark_pipeline.py:1355-1360`
**Issue:** The legacy pipeline forces `configs["finetune"].fp16 = False; configs["finetune"].bf16 = False` for `models_only_support_fp32` — and this phase's own commit added `CrossDNA_8.1M`, `CrossDNA_71.6M`, `CrossDNA_519M` to that list (alongside `Jamba-DNA-v1-114M-hg38`), asserting these four registry models cannot train in reduced precision. `run_finetune.py` — the benchmark entry point the sweep driver launches — carries no fp32 handling whatsoever, and `finetune_config.yaml` sets `bf16: True` globally. When `run_sweep.py` enumerates the full 62-model matrix, these four models train under bf16: either the run fails (swallowed by the blind except at `run_finetune.py:760`, compounding CR-02) or it produces numerically degraded results that would flow toward the leaderboard — against the project's core value that every published number is correct.
**Fix:** Port the override into `run_finetune.py`'s dataset loop (near the safetensors block at line 549):

```python
models_only_support_fp32 = [
    "Jamba-DNA-v1-114M-hg38",
    "CrossDNA_8.1M", "CrossDNA_71.6M", "CrossDNA_519M",
]
# ...inside the dataset loop, before DNATrainer construction:
if model_name in models_only_support_fp32:
    configs["finetune"].fp16 = False
    configs["finetune"].bf16 = False
```

### CR-02: run_sweep records `completed` for cells whose training failed (exit-0 failure swallowing; missing final_metrics.json not distinguished)

**File:** `pipeline/run_sweep.py:372-378`; interacts with `pipeline/run_finetune.py:745-767`
**Issue:** `run_finetune.py`'s designed isolation (D-08 sanctioned blind except at lines 760-767) logs a training failure and `continue`s — the process still exits 0. `run_finetune.py` then never writes `final_metrics.json` for that dataset. On the driver side, `run_matrix` sets `record["status"] = "completed"` as soon as the executor returns, and the subsequent `if metrics_path.exists()` silently leaves `metrics: null` when the file is absent. Net effect: the dominant real-world failure mode (a training error) produces a cell recorded `completed` with null metrics, no `sweep_failures.json` entry, and — because `run_record.json` is the per-cell audit artifact — a manifest that lies about a multi-day sweep's outcome. Only launch-seam exceptions (`SubprocessError`/`OSError`) are treated as failures.
**Fix:** Treat a successful executor with no `final_metrics.json` as a failure:

```python
executor(model, task, seed, str(output_root))
metrics_path = cell_dir / METRICS_NAME
if not metrics_path.exists():
    record["status"] = "failed"
    record["error"] = ("executor exited 0 but final_metrics.json is missing "
                       "(run_finetune.py swallowed a training failure)")
    failures.append({...})
else:
    record["status"] = "completed"
    with open(metrics_path, "r", encoding="utf-8") as f:
        record["metrics"] = json.load(f)
```

## Warnings

### WR-01: grad_accum default snapshotted from the base YAML before the custom-head config replacement (D-07/D-11 interaction)

**File:** `pipeline/run_finetune.py:414-431, 444`
**Issue:** `default_grad_accum = configs["finetune"].gradient_accumulation_steps` (line 419) is taken from the freshly loaded base config, but for `evo2_1b_base`/`megaDNA_updated` `configs` is then REPLACED by `finetune_config_with_head.yaml` (lines 430-432). The per-dataset reset (line 444) therefore forces the base YAML's grad_accum onto head models, ignoring whatever the with_head YAML specifies. Both YAMLs currently carry `gradient_accumulation_steps: 1`, so there is no divergence today — but the snapshot is taken from the wrong config for exactly the two models whose config is swapped, and any future with_head grad_accum change is silently clobbered. This is one of the phase's own flagged sensitivities.
**Fix:** Move the snapshot after the custom-head reload (inside the `error_log` block, after line 432), so it captures whichever config is actually active for that model.

### WR-02: dataset loading/statistics sit outside all error isolation — one unlocatable dataset aborts the rest of the run

**File:** `pipeline/run_finetune.py:654-666` (contrast `pipeline/dnallmmark_pipeline.py:870-872`)
**Issue:** `DNADataset.load_local_data(...)` (line 658) and `dataset.statistics()` (line 666) execute before the encode-phase `try` (line 689) with no presence check on `dataset_path`. The legacy pipeline checked `os.path.exists(dataset_path)` and skipped; the new path raises an uncaught exception that propagates through the model loop and kills the whole process. This matters because an unlocatable dataset directory is a documented, expected state — `run_sweep.py:90-95` records the suite double-nesting unzip quirk deferred to the E2E gate. A manual `python run_finetune.py --target_model X` run (README's documented usage) hitting a misplaced dataset dies mid-loop with a raw traceback, silently skipping every later dataset, with nothing in the error log.
**Fix:** Mirror the legacy guard (skip + log + `continue` when `dataset_path` is not a directory), or wrap the load/statistics block in the same log-and-continue isolation used for encode and train.

### WR-03: sequence validation alphabet hardcoded to ACGT-only for every model — training-set divergence from the runs behind the committed numbers

**File:** `pipeline/run_finetune.py:691`; contrast `pipeline/dnallmmark_pipeline.py:1054-1057`
**Issue:** The legacy pipeline chose `valid_chars` per model: `"ACGTacgt|"` only for the `models_no_char_n` list, `"ACGTNacgtn|"` (N allowed) for everything else. `run_finetune.py` hardcodes `valid_chars="ACGTacgt|"` for all 62 models and drops `models_no_char_n` entirely. Depending on dnallm's `validate_sequences` semantics, N-containing rows are now dropped or error for every model — changing the effective training set relative to every historical run that produced the committed leaderboard data, with no documented disposition of the change. Reproducibility of published numbers is the project's stated core value.
**Fix:** Either restore the per-model conditional (port `models_no_char_n`) or document the deliberate switch to strict-ACGT for all models (with the expected count impact) in the registry-quirk block where the other lists live.

### WR-04: three more model-quirk registries not ported or silently diverged between the deprecated reference and the active entry point

**File:** `pipeline/run_finetune.py:383-397, 579-592`; contrast `pipeline/dnallmmark_pipeline.py:983-993, 1322-1333, 1351-1354`
**Issue:**
- `models_with_limited_length` (`prokbert-mini`: 1027, `plant-dnabert-6mer`: 512) has no counterpart in `run_finetune.py` — the context-length cap is unenforced in the active path; both models are in the 62-model registry.
- `model_not_use_safetensors` membership diverges: the legacy list includes `plant-dnamamba-6mer` (and not `PlantGFM`); the new list includes `PlantGFM` (and not `plant-dnamamba-6mer`) — both models are in the registry. One of the two lists is wrong, and nothing records which.
- The legacy max_length tier rounding (`len_ranges`, rounding non-singlebase max_length up to 32-step tiers) is not ported, changing padding lengths vs historical runs.

The deprecation banner positions `dnallmmark_pipeline.py` as the behavioral reference (historical attribution, FLOPs reference), yet the quirk lists contradict the active file. Each unported quirk is a future wrong-run for the affected registry models.
**Fix:** Port or explicitly disposition each list in `run_finetune.py` (a short comment block naming the deliberately-dropped quirks is acceptable; silence is not).

### WR-05: make_dev_splits docstring promises interrupted-run self-healing that the count guard makes impossible in the train-write → registry-write window

**File:** `script/make_dev_splits.py:260-264` (docstring), `332-334` (write order), `453` (registry persisted in main)
**Issue:** The docstring claims "an interrupted run self-healing on re-run: the deterministic carve overwrites any half-written dev.csv ... before train.csv and the registry are updated." That holds for an interruption between the dev.csv and train.csv writes, but NOT for an interruption after the train.csv rewrite (line 333) and before `write_registry` (main, line 453): the registry still carries the pre-carve `Train` count, so a re-run reaches the count guard (line 320-326) and hard-exits with "registry/disk mismatch", requiring manual reconciliation (or the Zenodo re-download). The documented recovery story and the enforced behavior contradict each other.
**Fix:** Either narrow the docstring claim, or heal the recognizable interrupted state: when `dev.csv` exists, registry `Dev == 0`, and `len(train_rows) + len(dev_rows) == registry Train`, update only the registry instead of aborting.

### WR-06: stale sweep_failures.json never cleared on a clean re-run

**File:** `pipeline/run_sweep.py:400-401`
**Issue:** The failures manifest is written only `if failures:`. Re-running a sweep over the same output root after the failures are fixed leaves the previous run's `sweep_failures.json` in place next to a fresh `sweep_manifest.json` showing all cells completed/skipped — contradictory audit artifacts for the same root.
**Fix:** Always write the manifest (empty list when no failures) or explicitly remove/overwrite a stale `sweep_failures.json` at the start of `run_matrix`.

### WR-07: filter typos silently enumerate an empty matrix and exit 0

**File:** `pipeline/run_sweep.py:203-212`
**Issue:** `--models`/`--tasks` filters are intersected with registry keys with no unknown-name detection: `--models pant-dnamamba-6mer` (typo) yields 0 cells, writes a manifest, prints "Sweep finished: 0 cell(s) — 0 completed, 0 skipped, 0 failed", and exits 0. A task requested via `--tasks` that has `Train=0` is likewise silently dropped before the filter applies. For a driver meant to launch multi-day GPU sweeps, a typo'd no-op that reports success is an operational hazard.
**Fix:** After filtering, compare requested names against registry keys and exit non-zero listing unmatched names (e.g. `sys.exit(f"[Error] --models names not in registry: {sorted(unknown)}")`).

### WR-08: README Run Pipeline section omits the required CWD and documents the pre-F2 output layout

**File:** `README.md:151-155, 200`
**Issue:** The quick-start shows `python run_finetune.py --target_model ... --seed 9527` with no `cd pipeline` first. `run_finetune.py` resolves `./finetune_config.yaml` (line 414), `./logs/` (line 426), and the `./finetuned` default CWD-relatively — `run_sweep.py`'s own docstring documents this as research Pitfall 3 and pins its subprocess cwd for exactly this reason. Run from the repo root per the README, the invocation dies on the first model with a raw `FileNotFoundError` traceback. Line 200 also documents `finetuned/{model_name}/{dataset_name}/`, but the F2/G1 layout this phase shipped appends `/seed_{seed}/` (`run_finetune.py:560`).
**Fix:** Add `cd pipeline` to the README command block and update the documented output layout to include the seed segment; document `run_sweep.py` as the matrix entry point.

### WR-09: deprecation banner claims the legacy pipeline is retained "read-only ... exact code" in the same phase that functionally edited it

**File:** `pipeline/dnallmmark_pipeline.py:1-21` (banner) vs `:1277-1280, 1355-1360` (this phase's edits)
**Issue:** The new banner states the file is "retained read-only, never deleted" so "its exact code stays available for reproducibility review" of the committed numbers. The same phase renamed its metric extraction keys (`eval_auroc`→`eval_AUROC`, `eval_pearson_r`→`eval_pearsonr`, etc.) and added the CrossDNA models to `models_only_support_fp32`. The retained file therefore no longer reproduces the committed historical outputs it is kept for — anyone using it "for reproducibility" per the banner gets different JSON than what is committed under `dnallm-mark/data/`.
**Fix:** Record the deliberate post-hoc edits in the banner (what changed, when, why — alignment with the current dnallm suite's metric keys), or move the key alignment into the active path only and leave the legacy file byte-frozen.

### WR-10: --mem_ratio silently ignored in the length-scaling batch estimator, which also contains a dead branch

**File:** `pipeline/run_finetune.py:210-231, 615-622`
**Issue:** The call site at line 615-622 passes `gpu_mem_total` but not `target_mem_ratio`, so `estimate_batch_size` uses its 0.4 default while the documented `--mem_ratio` (default 0.70) only reaches `estimate_batch_size_by_model_params`. Operators tuning `--mem_ratio` get a different ratio than requested whenever the second estimator fires (longer sequences than the first dataset). Additionally, inside `estimate_batch_size` both branches of the `if predicted_mem >= gpu_mem_total * threshold:` compute the identical expression (`threshold` IS `target_mem_ratio`) — the if/else is dead logic that only misleads.
**Fix:** Pass `target_mem_ratio=mem_ratio` at the call site; delete the dead branch (or make the two branches genuinely differ, e.g. an aggression factor for the headroom case).

## Info

### IN-01: duplicated assignment

**File:** `pipeline/run_finetune.py:340-341`
**Issue:** `gpu_memory_override = args.gpu_memory` appears twice consecutively.
**Fix:** Delete one.

### IN-02: split_task reimplements carve_stratified_dev inline

**File:** `script/make_dev_splits.py:328-330`
**Issue:** `split_task` inlines `select_dev_indices` + row-splitting instead of calling the tested `carve_stratified_dev` (which exists precisely for this and is what the tests pin). The two copies can drift (e.g. a future seed-parameter change applied to one but not the other).
**Fix:** `dev_rows, train_rows = carve_stratified_dev(rows)` — the inline copy is byte-equivalent today.

### IN-03: --target_dataset elements not stripped

**File:** `pipeline/run_finetune.py:448-450`
**Issue:** `target_dataset.split(",")` keeps whitespace: `--target_dataset "A, B"` matches nothing and the run silently processes zero datasets. `run_sweep.py` strips its filter elements (lines 413-419) — inconsistent handling of the same convention.
**Fix:** `target_datasets = [t.strip() for t in target_dataset.split(",")]`.

### IN-04: converter's --to-csv / --map / --numeric / --columns / --crlf directions have no test coverage

**File:** `tests/test_convert_registry.py` (coverage gap); `script/convert_registry.py:341-363`
**Issue:** All eight tests exercise the `--to-json` direction only. The CSV projection direction — which the single-source contract calls "the sanctioned on-demand projection" and which the docstring's own round-trip recipe depends on — is untested; a regression in `to_csv` (column ordering, name-column prepending, CRLF mode) would ship unnoticed.
**Fix:** Add a round-trip pin: `to_csv` then `to_json` over a fixture registry reproduces the operational columns (`Index`/`Train`/etc. as ints, `Model_size` verbatim).

### IN-05: README project-structure annotations incorrect

**File:** `README.md:338, 348`
**Issue:** Line 348 describes pyproject.toml as "Dependency groups (data / dev / pipeline)" — the third group is named `gpu`. Line 338 labels `finetune_config.yaml` "Training script" — it is a configuration file.
**Fix:** Correct both labels.

### IN-06: live Zenodo preview JWT committed in README (documented decision — no action this phase)

**File:** `README.md:123`; `.gitleaks.toml` (rule-scoped allowlist)
**Issue:** The dataset download link carries a record-scoped preview token (flagged by the injection scanner during this review as `MD-LINK-TOKEN-IN-QUERY`). This is a documented, deliberate maintainer decision (D-08, AUDIT.md, `.gitleaks.toml` allowlist correctly scoped to rule + anchored path + record regex, Phase 6 retirement tracked for when the record publishes). Recorded so the review is complete; the only action item is the already-tracked one: the allowlist must be updated in the same commit as any link change, and both dropped at publication.
**Fix:** None this phase; keep the existing tracking.

---

_Reviewed: 2026-10-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
