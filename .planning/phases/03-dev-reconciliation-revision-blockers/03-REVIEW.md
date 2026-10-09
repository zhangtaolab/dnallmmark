---
phase: 03-dev-reconciliation-revision-blockers
reviewed: 2026-10-09T18:25:47Z
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
  warning: 1
  info: 11
  total: 12
status: issues_found
---

# Phase 3: Code Review Report (iteration 3 — convergence check)

**Reviewed:** 2026-10-09
**Depth:** standard
**Files Reviewed:** 19 (same scope as iterations 1-2)
**Status:** issues_found

## Summary

Iteration-3 convergence re-review after fix iteration 2 (commits `062f72e`,
`43acfa8`, `dbabb8b` — WR-11 corrupt-metrics cell failure, WR-12 record
preservation on skip, WR-13 metrics-before-marker ordering). All three fixes
were verified **at the source level and at the behavior level** — each is
correct, complete against its stated scope, and regression-free (details
below). Gates re-run directly by this review, all green:

- `pytest` (full lane): **186 passed + 5 xfailed** (fast lane: 185 passed +
  1 slow deselected — the count delta vs iteration 2's 183 full-lane is
  exactly the three new regression tests, i.e. the test diffs are purely
  additive)
- `node --test tests/js/`: **fail 0**
- `ruff check tests/ script/make_dev_splits.py pipeline/run_finetune.py
  pipeline/run_sweep.py`: **All checks passed**
- `ty check script/ baseline/ tests/ scripts/ pipeline/run_sweep.py`:
  **All checks passed**

Since iteration 2's review, exactly three commits landed, touching
`pipeline/run_sweep.py`, `pipeline/run_finetune.py`, `tests/test_sweep.py`,
and `tests/test_run_finetune_contracts.py` — all four files were re-read in
full at current HEAD; the other 15 in-scope files are byte-identical to what
iterations 1-2 reviewed at standard depth.

The convergence hunt found **one new Warning**: the WR-07 fail-fast fix
established the invariant that a filter value which would run a surprising
matrix must abort, but degenerate all-empty-element values bypass it in both
directions — `--models ,`/`--tasks ,` silently invert to the FULL registry
matrix (empirically: 3100 cells), and `--seeds ""`/`--seeds ,` silently
enumerate 0 cells, write a manifest, and exit 0 (empirically confirmed).
Three new Info items were also recorded (IN-09..IN-11); none escalate a
documented-open item.

Out-of-scope items honored and NOT re-reported: WR-03/WR-04 (quirk-parity
surface) remain maintainer-sanctioned Phase-4 deferrals; WR-09 stands
resolved as false premise; the three `xfail(strict=True)` locks in
`tests/test_known_defects.py` (AUD-01 species, comparator bool/int,
non-finite `get_float`) are intact and routed to Phase 4; IN-01..IN-08 remain
documented-open Info findings (carried below, none escalated).

### Iteration-2 fix verification

| Fix | Verdict | Evidence |
|---|---|---|
| WR-11 corrupt final_metrics.json fails the cell, not the sweep | **Correct + complete** | `run_sweep.py:476-500`: `json.load` now sits inside its own `try`, and `status = "completed"` is assigned only AFTER a successful load (an ordering improvement over the suggested patch — a decode failure can no longer leave a completed status behind). The `except json.JSONDecodeError` branch records `failed` with a corrupt-file cause string distinct from the missing-metrics cause, appends to `failures`, and the sweep continues; the outer launch-seam handler (`subprocess.SubprocessError`/`OSError`, line 501) and the "any other exception is a driver BUG and aborts loudly" boundary are untouched. Test drives the real `run_matrix` with a truncating executor and pins: seed-42 failed / seed-43 completed, `metrics is None`, cause string, one failures entry, and manifest written with `[failed, completed]`. Residual narrow gap (non-UTF-8 corruption) → IN-09. |
| WR-12 never overwrite an existing run_record.json for a skipped cell | **Correct + complete** | `run_sweep.py:511-523`: the write is gated on `record["status"] != "skipped" or not record_path.exists()`. Non-skipped cells always write (behavior unchanged from pre-fix); a skipped cell with an existing record is preserved verbatim; a skipped cell with no record (standalone `run_finetune.py` left the marker but no record — the exact case the pre-existing seed-scoped test constructs) still gets one. The manifest still reports THIS run's skipped view because it is built from the in-memory `records` list, not from disk — test pins both artifacts side by side (on-disk record == run-1's completed record byte-for-byte; manifest cell == `skipped`), plus zero executor invocations on resume. `cell_dir` necessarily exists for a skipped cell (it contains the marker), so the no-record write cannot hit a missing parent. Interaction note → IN-10. |
| WR-13 final_metrics.json written before the trainer_state.json resume marker | **Correct + complete** | `run_finetune.py:801-803`: `json.dump(metrics, ...)` now precedes `shutil.copy(.../checkpoint-{last_step}/trainer_state.json", outdir)`. Both marker consumers read the copied file (`run_finetune.py:601` resume check, `run_sweep.py:443` skip check), so the marker is now genuinely the final act of a successful cell. The reorder is surgical: `checkpoints`/`last_step` computation, the `local_rank == 0` guard, the trailing `trainer.evaluate()` (whose result is discarded — unchanged position and semantics), and the D-08 blind-except scope are all untouched; if either write raises, the except continues with no marker, so the cell retrains. The textual ordering test is faithful despite being source-text-based: both anchor strings occur exactly once in the file (verified by grep), so the index comparison cannot be fooled by a distant second occurrence. Durability nuance → IN-11. |

**Regression hunt on the three fix diffs:** none found. Each diff matches its
stated scope exactly; no existing test was modified (only docstring bullets
added); the three new tests account for the full-lane count 183→186; the
`_validate_filters`/`enumerate_matrix`/dry-run paths, argv construction, and
`run_finetune.py`'s loop structure were re-traced end-to-end at HEAD with no
semantics drift beyond the intended fixes.

## Warnings

### WR-14: Degenerate all-empty filter/seed values bypass the WR-07 fail-fast — a separator-only filter silently enumerates the FULL matrix, an empty `--seeds` silently runs 0 cells and exits 0

**File:** `pipeline/run_sweep.py:549-557` (strip normalization in `main`), interacting with `_validate_filters` early-return at `:256-257` and `enumerate_matrix` falsy checks at `:219, :225`
**Issue:** WR-07's fix (verified in iteration 2) established the invariant that filter values the registry does not know must abort before enumeration, because "a silently successful no-op for a driver meant to launch multi-day GPU sweeps [is] an operational hazard." Two degenerate input classes bypass that invariant:

1. **All-empty-element filters invert to the FULL matrix.** `--models ,` (or `--tasks ,`) survives the strip-filter at lines 550-557 as `[]`, which is falsy — `_validate_filters` early-returns on falsy filters (line 256), and `enumerate_matrix`'s `if models_filter:` (line 219) treats `[]` the same as `None`, i.e. no filtering. Empirically confirmed against the real registries: `--models ,` enumerates **3100 cells (62 models x 50 tasks)**. An operator passing a filter that expands from shell indirection to separators only (e.g. `--models "$A,$B"` with both variables empty) launches the full multi-day sweep while believing the run was scoped — the worst-case mislaunch, not merely a no-op.
2. **An empty seed set runs 0 cells and exits 0.** `--seeds ""` or `--seeds ,` (argparse `required=True` is satisfied by any present value, including empty) yields an empty set at line 549; `run_matrix([])` then writes a manifest + empty failures manifest, `main` prints "Sweep finished: 0 cell(s) — 0 completed, 0 skipped, 0 failed", and the process exits 0. Empirically confirmed (manifest written, 0 records). This is exactly the terminal state the WR-07 fix's own docstring declares unacceptable.

**Fix:** After strip normalization, refuse empty results for explicitly-passed flags (fail fast, mirroring WR-07's `sys.exit` style):

```python
seeds = sorted({int(s.strip()) for s in args.seeds.split(",") if s.strip()})
if not seeds:
    sys.exit("[Error] --seeds produced no values after stripping empties")

models_filter = None
if args.models is not None:
    models_filter = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models_filter:
        sys.exit("[Error] --models produced no names after stripping empties "
                 "(refusing to silently enumerate the full registry)")
# same pattern for --tasks
```

Note the `args.models is not None` form also makes the (currently silent)
`--models ""` → full-matrix path an explicit error instead of
indistinguishable-from-absent.

## Info

### IN-09 (new): WR-11's catch is `json.JSONDecodeError` only — a non-UTF-8 `final_metrics.json` raises `UnicodeDecodeError` and still aborts the sweep

**File:** `pipeline/run_sweep.py:480`
**Issue:** `except json.JSONDecodeError` does not catch `UnicodeDecodeError` (verified: both are `ValueError` subclasses; neither derives from the other — a file containing invalid UTF-8 bytes raises `UnicodeDecodeError` from the text-mode `open`, escaping both the inner catch and the outer `subprocess.SubprocessError`/`OSError` handler, aborting the sweep with no manifest). The error message already says "corrupt/unreadable", but only the corrupt-and-parse-failing half of "unreadable" is handled. Reachability is negligible today — the child writes ASCII-only metric keys/values, and any truncation of ASCII text is still valid UTF-8, so the realistic mid-write-death artifact lands in the handled `JSONDecodeError` branch — hence Info, not Warning.
**Fix:** Catch the common base: `except ValueError as exc:` (covers both `JSONDecodeError` and `UnicodeDecodeError`; keep the same failed-cell handling).

### IN-10 (new): `_write_json` is non-atomic, and WR-12's never-overwrite now preserves a truncated `run_record.json` forever

**File:** `pipeline/run_sweep.py:350-353` (`_write_json`: plain `open(path, "w")` + `json.dump`, no temp+rename), interacting with the WR-12 guard at `:522`
**Issue:** A driver death mid-record-write truncates `run_record.json` on disk. Pre-WR-12, a resumed sweep would overwrite it with a fresh (skipped) record; post-WR-12 the guard refuses the overwrite, so the truncated record persists across all future resumes. Mitigating factors, hence Info: there is no programmatic consumer of `run_record.json` (writer, tests, and README only — verified by repo-wide grep), the training outputs and manifest remain intact, and a truncated JSON fails loudly (obvious parse error) rather than silently misleading.
**Fix:** Make `_write_json` atomic (write to `path.with_suffix(".tmp")`, then `os.replace`), or have the WR-12 guard preserve the existing record only when it parses (`json.loads` try/except) and rewrite it otherwise.

### IN-11 (new): WR-13's comment claims power-loss coverage that the write ordering alone does not deliver (no fsync)

**File:** `pipeline/run_finetune.py:792-803`
**Issue:** The new comment lists "power loss" among the covered kill windows, but without `f.flush()` + `os.fsync()`, the ordering guarantee holds for process death only (page-cache ordering); on power loss the two files' durability is unordered, so the marker-durable/metrics-lost inversion the fix targets remains physically possible. Probability is minute (sub-second window) and the fix's core value (process-death coverage: OOM killer / SIGKILL) is fully delivered.
**Fix:** Either soften the comment to "process death (OOM killer / SIGKILL)" or add `f.flush(); os.fsync(f.fileno())` after the `json.dump` (and fsync the copied marker's directory) if power-loss coverage is actually claimed.

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

**File:** `tests/test_convert_registry.py` (all tests exercise `--to-json` only); `script/convert_registry.py:341-363`
**Issue:** The CSV projection direction — the "sanctioned on-demand projection" per the single-source contract, and the direction the docstring's own round-trip recipe depends on — is untested; a regression in `to_csv` (column ordering, name-column prepending, CRLF mode) would ship unnoticed.
**Fix:** Add a round-trip pin: `to_csv` then `to_json` over a fixture registry reproduces the operational columns as ints with `Model_size` verbatim.

### IN-05 (carried, open since iteration 1): README project-structure annotations incorrect

**File:** `README.md:346, 356`
**Issue:** Line 356 describes pyproject.toml as "Dependency groups (data / dev / pipeline)" — the third group is named `gpu`. Line 346 labels `finetune_config.yaml` "Training script" — it is a configuration file.
**Fix:** Correct both labels.

### IN-06 (carried, documented decision — no action this phase): live Zenodo preview JWT in README

**File:** `README.md` dataset link; `.gitleaks.toml` (rule-scoped allowlist)
**Issue:** Record-scoped preview token in the download link; deliberate maintainer decision (D-08, AUDIT.md), allowlist correctly scoped, Phase 6 retirement tracked. The tracking requirement stands: allowlist and link change in the same commit, both dropped at publication.
**Fix:** None this phase; keep the existing tracking.

### IN-07 (carried, open since iteration 2): CR-02 error string asserts one cause for a multi-cause condition

**File:** `pipeline/run_sweep.py:463-467`
**Issue:** The missing-metrics error says "run_finetune.py swallowed a training failure", but exit-0-without-metrics has other causes: the WR-02 dataset-dir skip, an encode-phase skip, or the (now-closed) kill window. The *status* is honest either way; the cause attribution can misdirect an operator.
**Fix:** Neutral wording, e.g. "training failure swallowed, dataset/encode-phase skip, or interrupted write — check the child's error log".

### IN-08 (carried, open since iteration 2): convert_registry.py missing from `make lint` scope

**File:** `Makefile:58-68`
**Issue:** The lint target's comment defines the scope as "tests/ plus Phase-3-authored/edited files" but omits `script/convert_registry.py` (authored in the Phase-3 window, edited by 03-02). Currently clean; the gap is latent.
**Fix:** Add `script/convert_registry.py` to the `lint` recipe and adjust the scope comment.

---

_Reviewed: 2026-10-09_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Iteration: 3 (convergence check after fix iteration 2)_
