---
phase: 03-dev-reconciliation-revision-blockers
reviewed: 2026-10-10T03:30:00Z
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
  critical: 0
  warning: 3
  info: 8
  total: 11
status: issues_found
---

# Phase 3: Code Review Report (iteration 2)

**Reviewed:** 2026-10-10
**Depth:** standard
**Files Reviewed:** 19 (same scope as iteration 1)
**Status:** issues_found

## Summary

Iteration-2 re-review after fix iteration 1 (commits `7c703a7`, `9932727`,
`725782b`, `8cd586d`, `db46c4e`, `52b0b3a`, `0352311`, `af12068`, `f820423`,
`a00ae96`). All 9 in-scope fixes were verified **at the source level, not
merely as present** — each is correct and complete (details below). Gates
re-run and green: `make test-fast` **182 passed + 5 xfailed** (1 slow
deselected; matches the 183 full-lane), `make lint` **All checks passed**,
`make typecheck` **All checks passed**. Registry contracts re-verified
directly: 62 models / 50 datasets, `key == Model_name`/`Dataset_name`
everywhere, all operational counts positive ints, **all 50 tasks Dev > 0**
(the new Dev-refusal guard has no live trigger), and all four
`models_only_support_fp32` models present in the registry.

No regressions were introduced by the fix commits (each diff is surgical and
matches its stated scope; the WR-07 import-order follow-up `a00ae96` is
style-only). However, the standard-depth sweep — tracing the sweep driver's
resume and failure paths end-to-end against `run_finetune.py`'s write
ordering — found **three genuine defects the first pass missed** (WR-11,
WR-12, WR-13; two of them demonstrated with executable reproductions against
the real `run_sweep.run_matrix`). None were introduced by the fixes; all
predate them and are not on the deferred/locked/resolved lists.

Out-of-scope items honored and NOT re-reported: WR-03 (ACGT-only alphabet,
`run_finetune.py:732` unchanged) and WR-04 (unported quirk registries,
unchanged) remain maintainer-sanctioned Phase-4 deferrals — the deferrals
introduced no new defect; WR-09 stands resolved as false premise; the three
`xfail(strict=True)` locks in `tests/test_known_defects.py` (AUD-01 species,
comparator bool/int, non-finite `get_float`) are intact and routed to
Phase 4; the README `{model_name}_performance.json` sentence is logged in
`deferred-items.md` for Phase 4's REV-03 exporter.

### Iteration-1 fix verification

| Fix | Verdict | Evidence |
|---|---|---|
| CR-01 fp32 override | **Correct + complete** | Active list (`run_finetune.py:399-404`) is byte-identical in membership to the deprecated pipeline's list (`dnallmmark_pipeline.py:1355-1360`); all 4 models verified in the 62-model registry. Override at 581-583 sits inside the dataset loop and precedes the only consumer of `fp16`/`bf16` (`DNATrainer`, line 777); nothing reads those flags between config load and the override. Legacy applies the override before model load, active after — equivalent, since `load_model_and_tokenizer` receives only `configs["task"]`. Cross-file parity test pins membership and ordering. |
| CR-02 exit-0-no-metrics = failed | **Correct + complete** | `run_sweep.py:433-456`: missing `final_metrics.json` after a clean executor return → `failed` + missing-metrics error + failures entry; never `completed` with null metrics. Test fake (returns None, writes nothing) matches the documented child behavior; record skeleton already carries `metrics: None`/`error: None` so no key drift. |
| WR-01 grad_accum snapshot | **Correct** | Snapshot at `run_finetune.py:443` is inside the `error_log` block, AFTER the with_head reload (433); per-dataset reset (455) precedes the adjustment read (672). Ordering pinned by test. |
| WR-02 dataset-dir guard | **Correct** | `isdir` guard at 506-514, after the Dev-refusal guard, before task config and any model load — mirrors legacy placement (`dnallmmark_pipeline.py:870-872`); logs to console + error log, then `continue`. |
| WR-05 docstring narrowing | **Correct** | `make_dev_splits.py:261-268` now claims self-healing only before the train.csv rewrite and explicitly documents the non-healing window — matches the enforced count guard (322-331). |
| WR-06 failures manifest always written | **Correct** | `run_sweep.py:487` writes `sweep_failures.json` unconditionally (empty list when clean); test pins empty-list-not-absent. |
| WR-07 filter validation | **Correct** | `_validate_filters` (`run_sweep.py:226-270`) runs in `main()` before enumeration and before any output-dir creation; exits non-zero listing unknown models, unknown tasks, and requested-but-untrainable tasks. Both CLI tests assert abort-before-output. |
| WR-08 README | **Correct** | `cd pipeline` + CWD-resolution note (README:151-156), `run_sweep.py` documented as the matrix entry point with `--dry-run` (158-163), seed-segment layout + sweep artifacts documented (208). |
| WR-10 mem_ratio | **Correct** | `target_mem_ratio=mem_ratio` passed at the length-scaling call site (653-663); dead if/else collapsed to the single expression both branches computed (219-228) — behavior-preserving removal, comment records why. |

## Warnings

### WR-11: Corrupt/truncated final_metrics.json aborts the entire sweep instead of recording a failed cell

**File:** `pipeline/run_sweep.py:457-460` (exception boundary at 461); interacts with `pipeline/run_finetune.py:793-794, 801-808`
**Issue:** The CR-02 boundary catches `subprocess.SubprocessError`/`OSError` (launch seam) and missing `final_metrics.json` (swallowed training failure), but a *present-but-corrupt* metrics file raises `json.JSONDecodeError` (a `ValueError`) from `json.load` at line 460 — outside every catch — and the documented "any other exception is a driver/executor BUG" clause does not fit it: this is child-data corruption, not a driver bug. The state is reachable: `run_finetune.py` writes `final_metrics.json` via `json.dump` inside the D-08 blind-except scope, so an OSError mid-write (e.g. disk full) is swallowed at 801-808, the child exits 0, and a truncated JSON file remains on disk. Empirically confirmed against the real `run_matrix`: `CRASH: JSONDecodeError ... manifest written? False; cell2 record written? False` — the sweep dies mid-run, the remaining cells never run, and no manifest exists (the manifest is only written after the loop).
**Fix:** Treat an unreadable metrics file as a failed cell, not a driver bug:

```python
else:
    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            record["metrics"] = json.load(f)
        record["status"] = "completed"
    except json.JSONDecodeError as exc:
        record["status"] = "failed"
        record["error"] = (f"final_metrics.json is corrupt/unreadable "
                           f"({exc}); the child left a partial file")
        failures.append({...})
```

### WR-12: Resume skip overwrites a completed cell's run_record.json, destroying its provenance

**File:** `pipeline/run_sweep.py:425-428, 471-472`
**Issue:** `run_record.json` is the only artifact linking a cell's metrics to the git commit and wall-clock times that produced them — the module docstring (lines 51-56) states these runtime observations are "recorded once at observation time, never regenerated". But the per-cell write at 471-472 is unconditional, so on every resumed sweep (the resume marker's core use case) each previously-completed cell's record — status `completed`, verbatim metrics copy, `git_commit`, `started_at`/`finished_at` of the real run — is overwritten by a fresh `skipped`/`metrics: null` record. Empirically confirmed: run 1 record `completed | metrics: {...} | commit: a00ae96...`; run 2 (resume) record on disk `skipped | metrics: None`. This also compounds WR-13: a cell recorded `failed` in run 1 becomes an unexplained `skipped` after the next sweep, and the failure provenance is gone.
**Fix:** For a skipped cell, preserve the existing record: write `run_record.json` only when absent (or skip the write entirely for the `skipped` branch — the manifest already reports this run's view).

### WR-13: Resume marker written before final_metrics.json — a kill in the window permanently marks an incomplete cell as done

**File:** `pipeline/run_finetune.py:789-794` (marker consumers: `run_finetune.py:601`, `run_sweep.py:425`)
**Issue:** On success the child first copies `trainer_state.json` into the outdir (792) — the completion marker both `run_finetune.py:601` and `run_sweep.py:425` treat as "this cell is done, never re-run" — and only then writes `final_metrics.json` (793-794). A process death in that window (OOM killer, SIGKILL, power loss; Ctrl-C raises `KeyboardInterrupt`, which `except Exception` does not catch, so it also lands here) leaves a cell with a resume marker but no metrics: the driver records it `failed` (CR-02) on that run, but every subsequent sweep marks it `skipped` and never retrains it — a benchmark cell that silently never completes, with the failure record then overwritten per WR-12. For a platform whose core value is that every published number is complete and reproducible, the completion marker must be established only after the output it promises exists.
**Fix:** Swap the write order in the `local_rank == 0` block: write `final_metrics.json` first, then copy `trainer_state.json` last (the marker must be the final act of a successful cell).

## Info

### IN-07: CR-02 error string asserts one cause for a multi-cause condition

**File:** `pipeline/run_sweep.py:445-449`
**Issue:** The missing-metrics error says "run_finetune.py swallowed a training failure", but exit-0-without-metrics has other causes: the WR-02 dataset-dir skip (`run_finetune.py:506-514`), an encode-phase skip (744-751), or WR-13's kill window. The *status* is honest either way; the cause attribution can misdirect an operator debugging a multi-day sweep.
**Fix:** Neutral wording, e.g. "executor exited 0 but final_metrics.json is missing (training failure swallowed, dataset/encode-phase skip, or interrupted write — check the child's error log)".

### IN-08: convert_registry.py missing from `make lint` scope despite being a Phase-3-authored/edited file

**File:** `Makefile:58-68`
**Issue:** The lint target's comment defines the scope as "tests/ plus the explicit list of Phase-3-authored/edited files", naming `make_dev_splits.py` (03-02), `run_finetune.py`, `run_sweep.py` — but `script/convert_registry.py`, authored in the Phase-3 window (c3843d7) and edited by 03-02 (39146d2), is excluded and lumped into the "REMAINING script/ ... pre-existing" bucket it does not belong to. Verified currently clean (`ruff check script/convert_registry.py` → All checks passed), so the gap is latent — but future edits to it escape the gate.
**Fix:** Add `script/convert_registry.py` to the `lint` recipe and adjust the scope comment.

### IN-01 (carried, open since iteration 1): duplicated assignment

**File:** `pipeline/run_finetune.py:337-338`
**Issue:** `gpu_memory_override = args.gpu_memory` appears twice consecutively.
**Fix:** Delete one.

### IN-02 (carried, open since iteration 1): split_task reimplements carve_stratified_dev inline

**File:** `script/make_dev_splits.py:333-335`
**Issue:** `split_task` inlines `select_dev_indices` + row-splitting instead of calling the tested `carve_stratified_dev` (byte-equivalent today; the copies can drift).
**Fix:** `dev_rows, train_rows = carve_stratified_dev(rows)`.

### IN-03 (carried, open since iteration 1): --target_dataset elements not stripped

**File:** `pipeline/run_finetune.py:459`
**Issue:** `target_dataset.split(",")` keeps whitespace: `--target_dataset "A, B"` matches nothing and the run silently processes zero datasets (`run_sweep.py` strips its filters; `--task_index` at line 472 also strips).
**Fix:** `target_datasets = [t.strip() for t in target_dataset.split(",")]`.

### IN-04 (carried, open since iteration 1): converter's --to-csv direction has no test coverage

**File:** `tests/test_convert_registry.py` (all 9 tests exercise `--to-json` only); `script/convert_registry.py:341-363`
**Issue:** The CSV projection direction — the "sanctioned on-demand projection" per the single-source contract, and the direction the docstring's own round-trip recipe depends on — is untested; a regression in `to_csv` (column ordering, name-column prepending, CRLF mode) would ship unnoticed.
**Fix:** Add a round-trip pin: `to_csv` then `to_json` over a fixture registry reproduces the operational columns as ints with `Model_size` verbatim.

### IN-05 (carried, open since iteration 1): README project-structure annotations incorrect

**File:** `README.md:346, 356` (lines shifted +8 by the WR-08 fix)
**Issue:** Line 356 describes pyproject.toml as "Dependency groups (data / dev / pipeline)" — the third group is named `gpu`. Line 346 labels `finetune_config.yaml` "Training script" — it is a configuration file (the sibling `finetune_config_with_head.yaml` is labeled correctly).
**Fix:** Correct both labels.

### IN-06 (carried, documented decision — no action this phase): live Zenodo preview JWT in README

**File:** `README.md` dataset link; `.gitleaks.toml` (rule-scoped allowlist)
**Issue:** Record-scoped preview token in the download link; deliberate maintainer decision (D-08, AUDIT.md), allowlist correctly scoped, Phase 6 retirement tracked for when the record publishes. The tracking requirement stands: allowlist and link change in the same commit, both dropped at publication.
**Fix:** None this phase; keep the existing tracking.

---

_Reviewed: 2026-10-10_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Iteration: 2 (--auto re-review after fix iteration 1)_
