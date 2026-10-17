---
phase: 03-dev-reconciliation-revision-blockers
fixed_at: 2026-10-10T00:00:00Z
review_path: .planning/phases/03-dev-reconciliation-revision-blockers/03-REVIEW.md
iteration: 1
findings_in_scope: 12
fixed: 9
skipped: 3
status: partial
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-10-10
**Source review:** `.planning/phases/03-dev-reconciliation-revision-blockers/03-REVIEW.md`
**Iteration:** 1
**Scope:** critical_warning (CR-* + WR-*; IN-* findings out of scope per config)

**Summary:**
- Findings in scope: 12 (2 Critical, 10 Warning)
- Fixed: 9 (both Criticals genuinely fixed, as required)
- Skipped: 3 (2 maintainer-sanctioned deferrals to Phase 4, 1 false-positive premise)

## Fixed Issues

### CR-01: fp32-only model handling absent from the active entry point

**Files modified:** `pipeline/run_finetune.py`, `tests/test_run_finetune_contracts.py`
**Commit:** `7c703a7`
**Applied fix:** Ported `models_only_support_fp32` (Jamba-DNA-v1-114M-hg38, CrossDNA_8.1M/71.6M/519M — all verified present in the 62-model registry) into `run_finetune.py`'s quirk-list block, with the `fp16 = False` / `bf16 = False` override in the dataset loop immediately before the safetensors block and ahead of `DNATrainer` construction, so the global `bf16: True` in `finetune_config.yaml` never reaches these models. Added a cross-file parity contract test (`test_fp32_only_models_forced_to_full_precision`) pinning that the active list matches the deprecated pipeline's membership and that the override precedes trainer construction. **Attribution note:** the review's claim that "this phase's own commit" added CrossDNA to the legacy list is contradicted by git history — those additions (and the metric-key alignment) landed in commit `808d61e` "Add CrossDNA models" (2026-09-29), before Phase 3; the substance of the finding (active path has no fp32 handling under a global `bf16: True`) stands and is fixed.

### CR-02: run_sweep records `completed` for cells whose training failed

**Files modified:** `pipeline/run_sweep.py`, `tests/test_sweep.py`
**Commit:** `9932727`
**Applied fix:** `run_matrix` now treats an executor that exits 0 but leaves no `final_metrics.json` as a **failed** cell: `status = "failed"`, a missing-metrics error string, and a `sweep_failures.json` entry — never `completed` with null metrics. Rationale documented at the site and in the module's "Failure boundary" docstring section (the missing file, not the exit status, is the training-failure signal from `run_finetune.py`'s D-08 blind-except isolation). New test `test_run_matrix_exit0_without_metrics_is_failure` pins the behavior.

### WR-01: grad_accum default snapshotted from the base YAML before the custom-head config replacement

**Files modified:** `pipeline/run_finetune.py`, `tests/test_run_finetune_contracts.py`
**Commit:** `725782b`
**Applied fix:** Moved the `default_grad_accum` snapshot to after the custom-head reload (inside the `error_log` block), so `evo2_1b_base`/`megaDNA_updated` snapshot the with_head YAML's default. Extended `test_grad_accum_reset_per_dataset` to pin snapshot-after-with_head-reload ordering.

### WR-02: dataset loading/statistics sit outside all error isolation

**Files modified:** `pipeline/run_finetune.py`, `tests/test_run_finetune_contracts.py`
**Commit:** `8cd586d`
**Applied fix:** Ported the legacy presence guard: `if not os.path.isdir(dataset_path)` → log to console + error log + `continue`, placed after the Dev-refusal guard and before any model load / task config, so an unlocatable dataset dir (the documented double-nesting unzip quirk state) skips one dataset instead of killing the model loop. Added contract test `test_dataset_presence_guard_precedes_dataset_load`.

### WR-05: make_dev_splits docstring promises interrupted-run self-healing the count guard makes impossible

**Files modified:** `script/make_dev_splits.py`
**Commit:** `db46c4e`
**Applied fix:** Narrowed the `split_task` docstring: self-healing holds only for interruptions before the train.csv rewrite; the train.csv-rewrite → registry-persist window leaves a registry/disk mismatch the count guard deliberately refuses (manual reconciliation) and does NOT self-heal. Chose the docstring-narrowing option over healing logic — a registry-rewriting heal widens surgical scope and touches tested count-guard semantics.

### WR-06: stale sweep_failures.json never cleared on a clean re-run

**Files modified:** `pipeline/run_sweep.py`, `tests/test_sweep.py`
**Commit:** `52b0b3a`
**Applied fix:** `run_matrix` now always writes `sweep_failures.json` (empty list when no cell failed), so a stale failures manifest can never sit next to a fresh all-clean `sweep_manifest.json`. Dry-run still writes only the manifest. Updated `test_run_matrix_completed_copies_metrics_verbatim` to pin empty-list-not-absent.

### WR-07: filter typos silently enumerate an empty matrix and exit 0

**Files modified:** `pipeline/run_sweep.py`, `tests/test_sweep.py`
**Commits:** `0352311` (fix), `a00ae96` (I001 import-order style follow-up)
**Applied fix:** New `_validate_filters(models_filter, tasks_filter, registry_dir)` runs in `main()` before enumeration (both real and dry-run paths) and exits non-zero listing (a) `--models` names absent from `models_info.json`, (b) `--tasks` names absent from `datasets_info.json`, and (c) requested tasks with falsy `Train` (the matrix can never run them). Aborts before any output is written. Two new CLI tests cover the typo and untrainable-task cases.

### WR-08: README Run Pipeline section omits the required CWD and documents the pre-F2 output layout

**Files modified:** `README.md`
**Commit:** `af12068`
**Applied fix:** Quick-start now shows `cd pipeline` with the CWD-relative resolution explained; added `run_sweep.py` as the documented matrix entry point (repo-root invocation, `--dry-run` enumerate-only vs real launch); output layout updated to `finetuned/{model_name}/{dataset_name}/seed_{seed}/` with the sweep driver's audit artifacts named.

### WR-10: --mem_ratio silently ignored in the length-scaling batch estimator, which also contains a dead branch

**Files modified:** `pipeline/run_finetune.py`
**Commit:** `f820423`
**Applied fix:** The `estimate_batch_size` call site now passes `target_mem_ratio=mem_ratio` (operators get the ratio they asked for in both estimators), and the dead if/else — both branches computed the identical expression — was collapsed to the single expression with a comment recording why.

## Skipped Issues

### WR-03: sequence validation alphabet hardcoded to ACGT-only for every model

**File:** `pipeline/run_finetune.py:691` (current: ~line 713)
**Reason:** skipped: deferred to Phase 4 (REV-03/exporter + quirk-parity surface) per the maintainer's binding deferral allowance ("full legacy-parity port of model-quirk registries widens Phase 3's surgical scope"). Porting `models_no_char_n` piecemeal — without the `len_ranges` tier rounding and `models_with_limited_length` caps it travels with — recreates exactly the partial-port incoherence WR-04 flags, and it changes effective training-set composition for ~49 models, which needs Phase 4's parity tests and the Phase 5 E2E gate rather than a Phase 3 code-only pass. Interim exposure is bounded: real sweep runs are gated by the Phase 5 E2E gate.
**Original issue:** legacy chose `valid_chars` per model (`"ACGTacgt|"` only for `models_no_char_n`, `"ACGTNacgtn|"` otherwise); the active path hardcodes strict ACGT for all 62 models, diverging from the runs behind the committed numbers.

### WR-04: three more model-quirk registries not ported or silently diverged

**File:** `pipeline/run_finetune.py:383-397, 579-592`
**Reason:** skipped: deferred to Phase 4 (quirk-parity surface) — the same maintainer-sanctioned deferral as WR-03. The three sub-items (`models_with_limited_length` caps, `model_not_use_safetensors` membership divergence incl. plant-dnamamba-6mer vs PlantGFM, legacy `len_ranges` tier rounding) are one coherent port with shared parity tests; a comment-only "deliberately dropped" disposition would be false (the drops were accidental, not decisions), and a piecemeal port risks new wrong-runs. Phase 4 owns the deliberate disposition record for each list.
**Original issue:** unported/diverged quirk registries between the deprecated reference and the active entry point; each unported quirk is a future wrong-run for affected registry models.

### WR-09: deprecation banner claims the legacy pipeline is retained "read-only ... exact code" in the same phase that functionally edited it

**File:** `pipeline/dnallmmark_pipeline.py:1-21`
**Reason:** skipped: code context differs from review — the premise is contradicted by git history. The metric-key alignment (`eval_auroc`→`eval_AUROC`, `eval_pearson_r`→`eval_pearsonr`, `eval_spearman_r`→`eval_spearmanr`) and the CrossDNA additions to `models_only_support_fp32` both landed in commit `808d61e` "Add CrossDNA models" (2026-09-29) — eleven days BEFORE the deprecation banner (commit `1b74037`, 2026-10-10, which touched this file with +19 banner-only lines and zero deletions). The deprecated file has been byte-stable since the banner landed, so "retained read-only" holds for the entire post-deprecation period and there is no phase edit to record in the banner. (If the maintainer nonetheless wants a pre-deprecation-history note in the banner — the pre-808d61e revision is what produced the oldest committed numbers — that is a docs decision, not this finding's defect.)
**Original issue:** banner allegedly falsified by same-phase edits to the retained file.

## Verification

**Where the gates ran:** per-fix verification (syntax + targeted pytest per touched test file) ran inside the isolated worktree using the main checkout's `.venv` interpreters (the worktree deliberately has no virtualenv — `ty` there required `--python .venv/bin/python` to resolve the project environment); the authoritative full-gate run below ran in the **main checkout** after the fixes were fast-forwarded onto `autorun`, so the numbers are reproducible from the tree as merged.

- `make test` — pytest: **183 passed + 5 xfailed** (baseline 178 + 5, plus the 5 new tests added by CR-01/CR-02/WR-02/WR-07); node lane: **2 pass / 0 fail**
- `make lint` (ruff over tests/ + the Phase-3-authored files) — **All checks passed**
- `make typecheck` (ty) — **All checks passed**

No model runs, no GPU work, no installs (uv auto-sync was a no-op; no dependency files touched). The `xfail(strict=True)` locks in `tests/test_known_defects.py` (AUD-01 species, comparator bool/int, non-finite get_float) were not touched, per the out-of-scope directive. `/home/forrest/Github/DNALLM` was never written to.

## Commit Index

| Commit | Finding | Subject |
|---|---|---|
| `7c703a7` | CR-01 | port fp32-only model override into run_finetune.py |
| `9932727` | CR-02 | record exit-0-without-metrics sweep cells as failed |
| `725782b` | WR-01 | snapshot grad_accum from the active (post-head-reload) config |
| `8cd586d` | WR-02 | skip unlocatable dataset dirs instead of aborting the loop |
| `db46c4e` | WR-05 | narrow make_dev_splits self-healing docstring to the healable window |
| `52b0b3a` | WR-06 | always write sweep_failures.json so stale manifests cannot linger |
| `0352311` | WR-07 | exit non-zero on unknown or untrainable sweep filters |
| `af12068` | WR-08 | document pipeline CWD, seed-segment output layout, run_sweep entry point |
| `f820423` | WR-10 | pass mem_ratio to the length-scaling estimator and drop its dead branch |
| `a00ae96` | — | style: fix import order in sweep test (I001 self-finding) |

---

_Fixed: 2026-10-10_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
