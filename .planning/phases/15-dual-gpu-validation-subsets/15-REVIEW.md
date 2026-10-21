---
phase: 15-dual-gpu-validation-subsets
reviewed: 2026-10-21T01:33:08Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - pipeline/run_finetune.py
  - pipeline/dispatch_core.py
  - script/make_subset_datasets.py
  - tests/test_subset_datasets.py
  - tests/test_run_finetune_contracts.py
  - tests/test_dispatch_core.py
  - docs/multi-gpu.md
  - Makefile
findings:
  critical: 0
  warning: 0
  info: 5
  total: 5
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-10-21T01:33:08Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found (0 Critical, 0 Warning, 5 Info — 4 carried, 1 new hardening note)

## Summary

Iteration 3 of 3 (final) of the `--auto` loop. Scope unchanged: the
Phase 15 surface — the deterministic stratified subset generator
(`script/make_subset_datasets.py`), the 15-04 dispatch run_record
producer (`pipeline/dispatch_core.py`), the 15-05 evaluate-merge
producer fix (`pipeline/run_finetune.py`), the three test suites,
`docs/multi-gpu.md`, and the `Makefile` lint wiring.

**Verdict: all previously fixed findings hold; the three iteration-3
fix commits (`bbdac40`, `2047ed3`, `55c8788`) are surgical and
introduced no new defects. No Critical and no Warning findings this
iteration.** Everything below is Info: four carried items (by
instruction, carry only — never re-raise) and one new hardening note
from this pass.

### Fix verification (by source read AND test execution)

1. **WR-02 holds — evaluate-failure v1-metrics delete
   (`bbdac40`).** `pipeline/run_finetune.py:1726-1731` wraps
   `trainer.evaluate()` in its own `except Exception:` whose handler
   has rank 0 `os.remove(outdir + "final_metrics.json")` BEFORE the
   bare `raise`. Full ordering verified in source: v1 write (`:1656`)
   < flops write (`:1701`) < evaluate (`:1727`) < except (`:1728`) <
   rank-0 delete (`:1729-1730`) < bare raise (`:1731`) < merged
   re-write (`:1749`) < marker copy (`:1763`). The bare re-raise is
   caught by the D-08 blind-except at `:1769-1776` (log + `continue`),
   so the child still exits 0 with NO metrics and NO marker — exactly
   the CR-02 existence-only failure signal dispatch reads. The delete
   is rank-0-guarded, matching the rank-0-guarded v1 write. Two pins
   pass:
   - static source-contract pin
     `tests/test_run_finetune_contracts.py:2772-2841`
     (`test_evaluate_failure_deletes_v1_metrics_before_reraise`),
     which also pins the handler clause as the bare `except Exception:`
     form (distinct from the three D-08 `as e` sites) and the delete's
     rank-0 guard;
   - dispatch e2e pin
     `tests/test_dispatch_core.py:3845-3938`
     (`test_dispatch_eval_failure_deletes_metrics_claim_failed_requeue`),
     which models the post-fix producer shape (v1 written, then
     evaluate fails, then the delete), asserts the claim ends FAILED
     with the CR-02 error text and a failed record with null metrics,
     and — the load-bearing half — asserts a RELAUNCH requeues the cell
     (the pre-fix completed claim skip-locked it forever) and the new
     attempt's record replaces the stale FAILED one.
2. **WR-03 holds — `csv.Error` routes to `TaskSkip`
   (`2047ed3`).** `script/make_subset_datasets.py:375` now catches
   `except (OSError, csv.Error)`; `csv.Error` inherits directly from
   `Exception` (not `OSError`), so the explicit catch is required and
   an oversized-field CSV (over the 131,072-char
   `csv.field_size_limit` default — a real possibility for the
   long-sequence dataset family) now skips only that task instead of
   aborting `main()`'s loop with earlier subsets on disk and no
   registry. Edge checked: the header-is-None `TaskSkip` raised
   INSIDE the `try` (`:370-373`) is not intercepted by the broader
   except (TaskSkip is neither OSError nor csv.Error), so its specific
   "empty (no header line)" diagnostic survives. Pin
   `tests/test_subset_datasets.py:533-580`
   (`test_oversized_field_skips_task_not_whole_run`) passes: 131,073-char
   field → `[Skip]` + "cannot read" + "field larger than field limit",
   sibling task's subset still written, registry carries exactly the
   completed task, non-zero exit.
3. **IN-03 docs citation refresh is correct (`55c8788`).**
   `docs/multi-gpu.md:22` now cites `pipeline/run_finetune.py:1450`
   for the `WORLD_SIZE` read and `:1635` for `LOCAL_RANK` — both
   verified against the actual source lines (`:1450` is
   `num_gpus = int(os.environ.get("WORLD_SIZE", "1"))`; `:1635` is
   `local_rank = int(os.environ.get("LOCAL_RANK", "0"))`). These are
   the only `file.py:line` citations in the document. Note for the
   record: iteration-2's companion claim that `run_sweep.py:1614`
   should read `:1616` was itself wrong — `:1614` was and remains the
   correct citation; the fixer was right to reject that part.

### Regression and invariant verification

- **All tests pass**: 214 across the three in-scope suites
  (`tests/test_subset_datasets.py` +
  `tests/test_run_finetune_contracts.py` = 106;
  `tests/test_dispatch_core.py` = 108), including the D15-15
  real-artifact checks (12-cell r2 sweep `eval_f1` present in all
  final_metrics — runtime evidence the 15-05 producer fix is active on
  real output), up from 209 at iteration 2 by exactly the new fix pins.
- **Frozen surfaces hold**: `pipeline/run_sweep.py` and
  `pipeline/run_sweep_shard.py` are diff-empty against the phase base
  `f3b4fb1`; `.github/workflows/ci.yml` blob hash is
  `33d2252eb594e0faecece9e8015a332d8d6479ef` at BOTH the base commit
  and HEAD (working tree identical).
- **Fix-commit hygiene**: the three commits touch only the files they
  claim (`bbdac40`: run_finetune.py + the two test files;
  `2047ed3`: generator + its suite; `55c8788`: one docs line). No
  collateral edits.
- **Re-verified standing invariants** (unchanged from prior
  iterations): the evaluate merge is additive-only with training keys
  winning collisions (`merged = {**eval_results, **metrics}`,
  `pipeline/run_finetune.py:1748`); `trainer.evaluate()` stays outside
  the rank guard (DDP semantics) with all writes rank-0; the
  `trainer_state.json` marker copy remains the success block's final
  write; dispatch queue order is `enumerate_matrix`'s sorted() order
  with stable priority permutation; the subset generator remains
  byte-deterministic (run-twice pin green); the generator's
  registry/output isolation refusals fire before any file is opened.
- `py_compile` clean on all three modified production files.

## Narrative Findings (AI reviewer)

## Info

### IN-01: (carried) Subset-consuming workflow still undocumented outside `.planning/` — generator "See also" mis-points

**File:** `script/make_subset_datasets.py:98-100`; `docs/multi-gpu.md:232`
**Issue:** The generator's docstring points at `docs/multi-gpu.md` for
"the dispatch-mode smoke procedure that consumes these subsets via
`--dataset_root`", but the doc's smoke explicitly uses FULL data
("全量 2110/234/2344 行——冒烟不依赖任何子集机制"), and still nothing
under `docs/` mentions `make_subset_datasets`, `datasets-smoke/`, or
`registry-smoke/` (re-grepped this iteration). The subset-consuming
12-cell sweep procedure exists only in phase artifacts — the repo's own
documented anti-pattern ("data regeneration is implicit tribal
knowledge") for a public-release milestone.
**Fix:** Add a short "subset smoke" subsection to `docs/multi-gpu.md`
carrying the real generator + dispatch commands with distinct
`--dataset-root` / `--output-root` / `--registry-dir`, and repoint the
"See also".

### IN-03: (carried, remainder) Line-anchored citations in docs/multi-gpu.md are correct today but fragile

**File:** `docs/multi-gpu.md:22`
**Issue:** The refreshed `:1450`/`:1635` citations are verified exact
against the current source (this review). They had already drifted
once as `run_finetune.py` changed shape across phases; any future
insertion above the dataset loop re-drifts them silently. (Historical
note: the sub-claim that `run_sweep.py:1614` needed renumbering was
wrong and was correctly rejected; `:1614` is right.)
**Fix:** Prefer anchor-style citations ("the `WORLD_SIZE` read in the
dataset loop") that survive edits, or accept the drift risk knowingly.

### IN-04: (carried) Success banner printed before the all-refused error exit

**File:** `script/make_subset_datasets.py:621-627`
**Issue:** When every task is refused, `main()` first prints
"✅ 0 subset dataset(s) written under ... ; registry: ..." and only
then raises `SystemExit("[Error] N task(s) refused ...")" — the success
emoji + completed-registry phrasing (no registry is written when
`subset_entries` is empty) followed by an error is confusing operator
output.
**Fix:** Move the banner inside the `if subset_entries:` block (or gate
it on `not failed`).

### IN-05: (carried, pre-existing) Duplicate `gpu_memory_override` assignment

**File:** `pipeline/run_finetune.py:763-764`
**Issue:** `gpu_memory_override = args.gpu_memory` appears twice in
immediate succession in the `__main__` unpack block — dead duplication
(no behavior effect), pre-existing before this phase.
**Fix:** Delete one line.

### IN-06: (new this iteration, hardening — not re-opening WR-02) CR-02's existence-only check still trusts a stale v1 metrics file for failures OUTSIDE the evaluate window

**File:** `pipeline/run_finetune.py:1701-1708, 1749-1750, 1769-1776`; consumer at `pipeline/dispatch_core.py:1087-1096`
**Issue:** The WR-02 delete covers exactly the `trainer.evaluate()`
window — the adjudicated, most OOM-prone step. Two narrower windows
remain where a rank-0 exception lands in the D-08 except-continue
(`:1769`) and the child exits 0 WITH `final_metrics.json` present, so
dispatch's CR-02 existence-only check completes the claim:
(a) a failure in the `flops_report.json` write (`:1701-1708`) leaves
the v1 (training-keys-only) file → a completed claim AND completed
record whose metrics carry no `eval_*` keys (the WINDOWS #45
empty-score shape) that relaunch skip-locks (completed claim) and
`--rerun-failed` ignores; (b) a failure during the merged re-write
(`:1749-1750`) can leave a torn file → completed claim with a WR-11
failed record — also skip-locked. Recorded as Info, not Warning,
because the probability class is different from the adjudicated
evaluate window: these are small local JSON writes on a file path the
same process just wrote successfully seconds earlier, and a disk full
enough to fail them would very likely have failed the earlier v1 write
first — which lands in the designed no-metrics failure signal. Traced
in source, not observed in practice.
**Fix (optional hardening):** generalize the WR-02 cleanup — e.g. set a
`v1_written` sentinel after the `:1656` write and, in the D-08 handler,
when the marker was never copied, unlink `final_metrics.json`
(tolerating `FileNotFoundError`) so "no final_metrics.json" becomes the
failure signal for the WHOLE post-train success block, not just the
evaluate window.

---

_Reviewed: 2026-10-21T01:33:08Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
