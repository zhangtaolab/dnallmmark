---
phase: 15
fixed_at: 2026-10-21T01:23:30Z
review_path: .planning/phases/15-dual-gpu-validation-subsets/15-REVIEW.md
iteration: 2
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 15: Code Review Fix Report (iteration 2)

**Fixed at:** 2026-10-21T01:23:30Z
**Source review:** .planning/phases/15-dual-gpu-validation-subsets/15-REVIEW.md
**Iteration:** 2

**Summary:**
- Findings in scope (fix_scope=critical_warning): 2 (WR-02, WR-03; 0 Critical)
- Fixed: 2
- Skipped: 0
- Info items IN-01..IN-05: out of scope per iteration-2 instructions (recorded
  as skipped-info below), except the authorized IN-03 line-citation fold-in —
  applied where verified correct, rejected where the review's drift claim was
  itself wrong (details under "Fixed Issues" / "Skipped Issues")

## Fixed Issues

### WR-02: A failed `trainer.evaluate()` yields a falsely-completed dispatch cell with no eval keys

**Files modified:** `pipeline/run_finetune.py`, `tests/test_dispatch_core.py`, `tests/test_run_finetune_contracts.py`
**Commit:** bbdac40
**Applied fix:** Producer-side, exactly the reviewer's "most surgical"
direction. The `eval_results = trainer.evaluate()` call is now wrapped in its
own `try/except Exception:` whose handler, BEFORE the bare re-raise into the
D-08 except-continue, has rank 0 (`if local_rank == 0:`) run
`os.remove(outdir + "final_metrics.json")` — deleting the stale v1
(training-keys-only) metrics file written earlier in the success block. The
exception still propagates exactly as today (D-08 logs and continues, child
exits 0), but the cell dir now ends with NO metrics and NO marker:
dispatch's CR-02 existence-only check records the claim **failed** (recovery
via relaunch requeue / `--rerun-failed`) instead of a permanently green,
score-less cell. The now-false invariant comment at the marker copy
(previously `:1736-1739`, claiming "a failed evaluate hits the D-08
except-continue with no marker (also a re-run, never a falsely-done cell)")
was reworded to state the actual WR-02 contract. **Narrowness:** argv surface,
the `merged = {**eval_results, **metrics}` literal, and the
flops-write < evaluate < merged-rewrite < marker-copy ordering are all
untouched (the pre-existing WINDOWS #45 / WR-13 / D-05 pins still pass);
dispatch_core.py untouched (producer-side fix only).

Two regression pins added:
- `test_dispatch_eval_failure_deletes_metrics_claim_failed_requeue`
  (`tests/test_dispatch_core.py`) — a fake child modeling the post-fix
  producer shape on an evaluate exception (writes v1 metrics + flops report,
  deletes final_metrics.json per the WR-02 handler, exits 0 — the evaluate
  exception never escapes run_finetune, which is exactly why the delete is
  load-bearing): CR-02 fails the claim with the exact
  `"child exited 0 but final_metrics.json is missing
  (run_finetune.py swallowed a training failure)"` error, the run_record
  reports failed with metrics null, no marker lands, and a RELAUNCH over the
  same root re-dispatches exactly that cell (failed claim requeues) whose new
  attempt completes and replaces the stale failed record — the pre-fix
  completed claim was skip-locked forever.
- `test_evaluate_failure_deletes_v1_metrics_before_reraise`
  (`tests/test_run_finetune_contracts.py`, the source-analysis idiom) — pins
  the delete-before-reraise ordering in strict source order: v1 write <
  evaluate < `except Exception:` < rank-0 `os.remove` < bare `raise` < marker
  copy, plus the `local_rank == 0` guard around the delete.

### WR-03: `csv.Error` is uncaught in `read_csv_rows` — an oversized-field CSV crashes the whole generator run

**Files modified:** `script/make_subset_datasets.py`, `tests/test_subset_datasets.py`
**Commit:** 2047ed3
**Applied fix:** The except clause routing to `TaskSkip` widened from
`except OSError` to `except (OSError, csv.Error)` (the reviewer's exact
shape; `csv.Error` inherits directly from `Exception`, not `OSError`, so it
must be named explicitly), with an inline comment stating why; the
docstring's `Raises:` section now names the `csv.Error` case (field over the
131,072-char `csv.field_size_limit` default). Regression pin
`test_oversized_field_skips_task_not_whole_run`
(`tests/test_subset_datasets.py`): a two-task tree where `GUE__emp_H3`'s
train.csv carries a 131,073-char field (the subprocess is a fresh
interpreter, so the CPython default limit always applies) — the run exits
non-zero with the `[Skip] GUE__emp_H3: cannot read …: field larger than
field limit (131072)` line, the good `iDNA_ABF_datasets__5mC` task still
completes, its subset CSVs land, the registry is written carrying exactly
the completed task, and the bad task writes nothing (reads precede writes).
Pre-fix, the uncaught `csv.Error` aborted `main()`'s loop mid-run: earlier
subsets on disk, no registry at all.

### IN-03 (authorized fold-in): stale line citations — docs only

**Files modified:** `docs/multi-gpu.md`
**Commit:** 55c8788
**Applied fix:** `docs/multi-gpu.md:22` citations refreshed to the verified
current lines: `pipeline/run_finetune.py:1450` (`num_gpus = int(os.environ.get
("WORLD_SIZE", "1"))`, was cited `:1436`) and `:1635` (`local_rank =
int(os.environ.get("LOCAL_RANK", "0"))`, was cited `:1621`) — both verified
by reading the actual lines, and both unaffected by the WR-02 insertion
(which sits after `:1731`). The review's OTHER drift claim — "dispatch_core
cites `run_sweep.py:1614` for the write predicate; it sits at
`run_sweep.py:1616`" — was verified **false**: the predicate
`if record["status"] != "skipped" or not record_path.exists():` IS at
`run_sweep.py:1614` (checked in both the worktree and the main checkout;
`:1616` is `records.append(record)`). The existing `run_sweep.py:1614`
citations in `pipeline/dispatch_core.py` (`:1264`, `:1349`) and
`tests/test_dispatch_core.py` (`test_dispatch_replaces_stale_failed_record`
docstring) are therefore correct as written and were left untouched —
"correcting" them to `:1616` would have introduced the very drift IN-03
exists to remove. (An initial edit that followed the review's claim was
reverted before commit for this reason.)

## Skipped Issues

### IN-01: Subset workflow undocumented outside `.planning/` — dangling See-also

**File:** `script/make_subset_datasets.py:98-100`; `docs/multi-gpu.md`
**Reason:** skipped-info (out of iteration-2 scope per instructions)
**Original issue:** The generator's `See also:` points at
`docs/multi-gpu.md` content that affirmatively states the smoke does NOT use
subsets; fix belongs to the Phase 18 DOCS-01 documentation pass.

### IN-03 (remainder): prefer line-stable anchors in citations

**File:** `docs/multi-gpu.md:22`; `pipeline/dispatch_core.py:1263-1264`, `:1349`
**Reason:** skipped-info except the authorized one-line corrections — the
verified-real docs drift was applied (see Fixed Issues); the
`run_sweep.py:1614 -> 1616` "correction" was rejected as factually wrong;
the broader "prefer symbols over line numbers" rework is documentation
policy, out of iteration-2 scope.
**Original issue:** Stale line citations drift as code moves.

### IN-04: Success banner prints before the refused-exit raise

**File:** `script/make_subset_datasets.py:612-618`
**Reason:** skipped-info (out of iteration-2 scope per instructions)
**Original issue:** "✅ N subset dataset(s) written" banner prints
immediately before `raise SystemExit` when tasks were refused; misleading
output ordering only.

### IN-05: Duplicate dead assignment of `gpu_memory_override`

**File:** `pipeline/run_finetune.py:763-764`
**Reason:** skipped-info (out of iteration-2 scope per instructions;
pre-existing at diff-base, not introduced by this phase). Also deliberately
NOT folded into the WR-02 commit: the iteration-2 binding constraint keeps
the run_finetune.py change evaluate-failure-only.
**Original issue:** `gpu_memory_override = args.gpu_memory` appears twice in
immediate succession; harmless dead line.

## Verification

Per-fix: Tier 1 (re-read of every modified region) + Tier 2
(`ast.parse` on every modified Python file) after each edit, plus the new
pins run immediately after their finding's edit. Post-commit gates (run in
the ISOLATED WORKTREE `.claude/worktrees/rf-15-302457-1792544720`, using the
main checkout's `.venv` binaries — pytest 9.1.1, ruff 0.16.10, ty 0.0.85;
`HF_ENDPOINT=https://hf-mirror.com` exported):

- `pytest tests/test_subset_datasets.py tests/test_dispatch_core.py
  tests/test_run_finetune_contracts.py -q` — **208 passed, 6 skipped**
  (was 211 passed at iteration-2 review + 3 new pins = 214 collected; the 6
  skips are the D15-15 real-artifact `skipif` lanes whose gitignored GPU
  runtime roots exist only in the main checkout, not the worktree — they
  pass on the validation box and skip in any clean tree)
- `ruff check` over the exact `make lint` file list — **All checks passed**
  (one iteration: ruff RUF100 correctly rejected an unused `# noqa: BLE001`
  on the new re-raising except — ruff's blind-except rule does not fire when
  the handler re-raises — the comment was removed and the WR-02 commit
  rebuilt cleanly before any of the three commits were finalized)
- `ty check` — **All checks passed**

Commit history (this iteration, on `autorun`):

- `bbdac40` fix(15): WR-02 delete v1 final_metrics on evaluate failure
  before re-raise (CR-02 fails the cell)
- `2047ed3` fix(15): WR-03 catch csv.Error in read_csv_rows routing to
  TaskSkip (oversized-field CSV skips task, not run)
- `55c8788` fix(15): IN-03 refresh stale line citations in
  docs/multi-gpu.md (run_finetune.py:1450/:1635)

---

_Fixed: 2026-10-21T01:23:30Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2_
