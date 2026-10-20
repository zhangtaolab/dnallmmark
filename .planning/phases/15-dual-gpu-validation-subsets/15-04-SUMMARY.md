---
phase: 15-dual-gpu-validation-subsets
plan: 4
subsystem: multi-gpu-dispatch-validation
tags: [dispatch, run_record, gap-closure, val-01, a3-supersession]
requires:
  - "Phase 13/14 frozen dispatch engine (dispatch_core.py, 98-test pinned)"
  - "run_sweep._new_record as the frozen record schema authority"
provides:
  - "dispatch_core writes run_record.json for every cell it RUNS (completed or failed) at claim finalize — run_sweep shape parity, WR-12 no-overwrite, CR-04 failure routing"
  - "Export dry-run consumer visibility test (subprocess, D14-10) — the 15-01 Task 3 consumption gate is now meetable by a fresh smoke re-run"
  - "Corrected 15-03-PLAN.md premises (producer mechanism + depends_on 15-04)"
affects:
  - "15-01 continuation (fresh 2-cell smoke re-run becomes the D15-02 criterion-3 evidence)"
  - "15-03-PLAN.md (consumption proof now rests on a true premise)"
  - "Phase 18 DOCS-01 dispatch-first docs (producer-side gap closed)"
tech-stack:
  added: []
  patterns:
    - "run_sweep._new_record reuse at dispatch finalize — the schema authority stays single, the writer composes from the cell's own artifacts + the claim-time lane"
    - "record write ordered AFTER the CR-02 artifact check, BEFORE finalize_claim — every failure mode rides the existing CR-04 containment with accounted=False"
key-files:
  created:
    - .planning/phases/15-dual-gpu-validation-subsets/15-04-SUMMARY.md
  modified:
    - pipeline/dispatch_core.py
    - tests/test_dispatch_core.py
    - .planning/phases/15-dual-gpu-validation-subsets/15-03-PLAN.md
decisions:
  - "A3 supersession: dispatch_core writes run_record at claim finalize (15-01-SUMMARY Option 1 ruling, 2026-10-20) — supersedes Phase 13 A3 exactly where its Phase 14/15 handoff was to land (13-01-PLAN.md:121-124)"
  - "Cell-dir mkdir parity: the writer mkdirs the cell dir before writing (run_matrix always has the dir; a dispatch child that dies before creating anything must still get its failed record without stacking a second failure mode on the cell's own verdict)"
  - "Refusal-predicate reading of unparseable existing records: only a record that PARSES with status completed is refusal-protected; unparseable provenance is unprovable and therefore replaceable"
metrics:
  duration: 51 min
  completed: 2026-10-20
  tasks: 2 of 2
  commits: 2
  plan_head_before: 98d72796ac09a07c6605d5cdf6d0e3cdeb9c9d73
  plan_head_after: 8c5e8b9f0759f5c3f0de0487c621d3bf22c4c9ec
status: complete
actuals:
  tokens: 8045   # chars/4 over the realized diff (582 insertions / 2 deletions)
  tasks: 2       # tasks completed
  commits: 2     # MEASURED: git rev-list --count 98d7279..HEAD
---

# Phase 15 Plan 4: Dispatch run_record Gap Closure Summary

**One-liner:** dispatch_core now writes run_record.json for every cell it runs — composed at claim finalize from the cell's own final_metrics.json plus the claim-time lane through run_sweep's own `_new_record` (WR-12 no-overwrite, WR-11 corrupt-metrics honesty, CR-04-routed failures) — closing the Phase 13 A3 gap that halted 15-01 and unblocking both the 15-01 consumption criterion and 15-03 wholesale.

## Status: COMPLETE (2/2 tasks, both committed)

This is the ruled remediation (15-01-SUMMARY Option 1, maintainer decision
2026-10-20). It supersedes Phase 13 decision A3 at EXACTLY the handoff
point A3 deferred (13-01-PLAN.md:121-124: "Phase 13 dispatch roots carry
child artifacts + the ledger + dispatch_state.json but NOT
sweep_manifest.json/run_record.json ... the documented Phase 14/15
handoff"). Phase 14 never landed that handoff; this plan is it.

## What Was Executed

### Task 1 — dispatch_core writes run_record at claim finalize (tdd)

Implemented in `pipeline/dispatch_core.py` (run_sweep.py and
run_finetune.py byte-untouched — verified empty porcelain):

1. **`write_cell_run_record(cell, cell_dir, payload, git_commit)`**
   (module-level, dense docstring documenting the ordering contract and
   the A3 supersession): skeleton built by calling
   `run_sweep._new_record(model, task, seed, cell_dir, git_commit,
   lane peft or "none", train_fraction from the lane, config_variant or
   "none")` — the exact call `run_matrix` makes for the same cell, so
   cell-identity fields are identical by construction. Metrics
   `json.load`-ed VERBATIM from the cell's own final_metrics.json for
   completed claims only; on `json.JSONDecodeError` the RECORD flips to
   failed with run_sweep's WR-11 error text while metrics stays null.
   Failed claims yield failed records carrying the claim's own error
   text. `started_at` = the claim's `claimed_at`, `finished_at` = the
   claim's `finished_at`; `vram_probe` stays the skeleton's four nulls.
2. **WR-12 write predicate** (the run_sweep.py:1614 parity adapted to
   dispatch): an existing record that parses with status `completed`
   raises a named `FileExistsError` naming the record path and stating
   completed provenance is never overwritten — the refusal fails the
   cell through the existing CR-04 containment; any other existing
   record (stale FAILED, or unparseable/unprovable) is replaced
   atomically via `_atomic_write_json`.
3. **Insertion point, pinned:** in `_spawn_worker` between the payload
   terminal-state assignment and `finalize_claim` — the record lands
   AFTER the CR-02 artifact check and BEFORE the claim rewrite, so any
   OSError/FileExistsError flows to CR-04 with `accounted=False` (claim
   rewritten failed dispatcher-side, counts.failed, exit 1; a finalized
   completed claim can never be rewritten — WR-03 invariant intact). No
   swallow around the helper.
4. **One git-commit observation per run:** `_launch_and_drain` computes
   `run_sweep._git_commit()` once next to run_id/started_at and threads
   it through the context (`context["git_commit"]`) — the run_matrix
   parity (never per cell).
5. **No other write sites:** pre-drain skip filter, dry-run branch
   (manifest-only), state writes, static mode untouched; skipped cells
   never synthesize records.

TDD evidence: RED first — 7 new tests appended to
`tests/test_dispatch_core.py` failing against the unwritten feature
(6 hard failures + the skip-pin's implementation-dependent half), then
GREEN after implementation. The 7 contract tests:

- shape parity vs a REAL `run_sweep.run_matrix` run over the SAME root
  (12 cells; model/task/seed/peft/config_variant/train_fraction/
  output_dir/status/metrics/vram_probe/error compared field by field;
  started_at/finished_at non-empty; ONE git_commit across all 12)
- failed cells get failed records (child exited 1; CR-02 exit-0-
  without-metrics carrying the claim's error text; metrics null)
- WR-11 corrupt final_metrics: claim stays COMPLETED (engine
  semantics untouched, counts completed) while the RECORD reports
  failed with run_sweep's corrupt-metrics error text
- no-overwrite refusal: pre-placed COMPLETED record → that cell fails
  loudly through CR-04 (claim failed naming the FileExistsError +
  record path, counts.failed, exit 1), pre-existing record
  byte-unchanged, sibling cell completes normally
- failed-record replacement: pre-placed FAILED record (marker-less) →
  the new successful attempt's completed record replaces it atomically
- lane fidelity: `--peft lora --num_train_epochs 1 --cache_dir
  --dataset_root` launch → record peft/config_variant/train_fraction
  equal the claim's lane values (record keyed by the ALIAS identity)
- skip divergence pin: marker-only cell skipped pre-drain → still no
  run_record.json afterward (dispatch_state counts report the skip)

### Task 2 — Export dry-run consumer visibility + 15-03 corrections + gates

1. **Consumer-visibility test**
   (`test_dispatch_root_export_dry_run_visibility`): fake-children
   12-cell dispatch root (3 models x 2 tasks x 2 seeds) + dispatch_ledger/
   + logs/ at the root, then
   `subprocess.run([sys.executable, export_runs.py, "--dry-run",
   "--input-root", root])` asserts exit 0 and the exact substring
   `[Dry-run] 12 run record(s) across 3 model(s) / 2 task(s)`. The
   "3 model(s)" count IS the no-phantom-model assertion (pinned by
   count, not absence-of-path). Subprocess form mandatory (D14-10).
2. **15-03-PLAN.md corrections** (scoped edits only): key_links via-text
   rewritten to the true producer mechanism (dispatch children are
   run_finetune.py invoked directly; run_record.json written per cell by
   dispatch_core at claim finalize per 15-04, composed via run_sweep's
   _new_record with WR-12 no-overwrite); `depends_on` gains "15-04";
   zero occurrences of the stale "run_sweep.py invocations" claim remain
   (grep = 0); the per-cell artifact lists including run_record.json are
   now TRUE and stay.
3. **Gates:** make lint + make typecheck green (one ruff fix in the new
   test: explicit `check=False` on the subprocess.run, repo idiom);
   ci.yml hash pin unchanged (33d2252eb594e0faecece9e8015a332d8d6479ef).

## Verification Evidence

- `pytest tests/test_dispatch_core.py tests/test_sweep.py
  tests/test_sweep_shard.py -q` → **305 passed** (98 prior dispatch +
  7 new contract tests + sweep + shard suites; the shard byte-identity
  tripwire green — static mode untouched)
- `pytest tests/test_dispatch_core.py tests/test_export_runs.py -q` →
  **135 passed** (includes the new dry-run test and the full export
  suite)
- `grep -c "run_record" pipeline/dispatch_core.py` = 7 (baseline 0)
- `git status --porcelain` over pipeline/run_sweep.py,
  pipeline/run_finetune.py, AND script/ → empty (schema authority +
  data chain untouched; D15-11 intact — the fix is producer-side only)
- `grep -c "run_sweep.py invocations" 15-03-PLAN.md` = 0;
  `grep -c "15-04" 15-03-PLAN.md` = 5 (>= 2)
- `git hash-object .github/workflows/ci.yml` =
  33d2252eb594e0faecece9e8015a332d8d6479ef (baseline match)
- Zero GPU in every test (fake children, stdlib+jsonschema pure);
  export_runs reached only as a sys.executable subprocess

## Deviations from Plan

### 1. [Rule 1 - Bug] Cell-dir mkdir parity in the record writer

- **Found during:** Task 1 GREEN run (2 failures:
  `test_exit_zero_without_metrics_fails_cell` — an existing pinned test —
  and the new CR-02 record test).
- **Issue:** a child that dies before creating anything (the CR-02
  swallow shape) leaves NO cell dir; the record write then raised
  FileNotFoundError, and CR-04 rewrote the claim with a dispatcher-side
  error — clobbering the cell's own truthful CR-02 verdict
  (`exit_code` None instead of 0, wrong error text).
- **Fix:** `write_cell_run_record` does `cell_dir.mkdir(parents=True,
  exist_ok=True)` before writing — the run_matrix parity (run_matrix
  mkdirs the cell dir before its executor runs). The cell's own verdict
  now survives; the failed record lands.
- **Files modified:** pipeline/dispatch_core.py
- **Commit:** 9c22787 (inside Task 1's commit — found and fixed before
  the task's commit; both affected tests green)

### 2. [Rule 3 - Blocking] Ruff subprocess-run-check on the new test

- **Found during:** Task 2 `make lint` gate.
- **Issue:** the new dry-run test's `subprocess.run` without an explicit
  `check=` failed the repo ruff lane (implicit check).
- **Fix:** explicit `check=False` (semantics unchanged — returncode is
  asserted manually; matches the 1272 idiom's explicit-check form).
- **Files modified:** tests/test_dispatch_core.py
- **Commit:** 8c5e8b9

### 3. [Environment, not a code deviation] D-15 export test network hang

- **Found during:** Task 2 verify (`pytest tests/test_export_runs.py`
  hung >9 min at HEAD, untouched by this plan).
- **Root cause:** the pre-existing
  `test_d15_evaluate_cross_validates_suite_mapped_metric_conventions`
  calls `evaluate.load("pearsonr"/"spearmanr")` which HEADs
  huggingface.co for an etag BEFORE falling back to the local cache;
  huggingface.co TCP connects are DROPPED on this AutoDL box, so each
  HEAD blocks to the OS TCP timeout instead of failing fast.
- **Action:** out of scope (pre-existing, unrelated file) — logged to
  `deferred-items.md`; the verify lane ran with
  `HF_ENDPOINT=https://hf-mirror.com` (reachable; metrics then load in
  ~17 s; suite 29/29 green). No code change.

## Auth Gates

None.

## Known Stubs

None. (No stubs introduced; every code path is test-covered.)

## Threat Flags

None — no security-relevant surface beyond the plan's threat model.
T-15-07 (record composed exclusively from the cell's own artifacts +
claim-time lane; completed provenance refusal-protected; lane-fidelity
pinned) and T-15-08 (every write failure rides CR-04 — the silent-
invisibility gap structurally impossible) both verified green above.
T-15-SC held: zero installs.

## A3 Supersession Note (exact deltas)

- **Superseded:** Phase 13 decision A3 (13-01-PLAN.md:121-124) —
  "dispatch roots carry child artifacts + the ledger +
  dispatch_state.json but NOT sweep_manifest.json/run_record.json ...
  the documented Phase 14/15 handoff".
- **By:** 15-01-SUMMARY remediation Option 1 (maintainer decision
  2026-10-20), landed here at exactly the deferred handoff point.
- **Delta:** dispatch roots now carry per-cell run_record.json for
  every cell a worker RUNS (completed or failed), written at claim
  finalize. Deliberately UNCHANGED from A3: no sweep_manifest.json on
  real dispatch roots (the dry-run plan artifact remains the only
  manifest), no synthesized skipped-cell records (dispatch_state
  counts report skips), claim semantics and the skip filter untouched.
- **Consequence:** the 15-01 D15-02 consumption criterion
  ("[Dry-run] 2 run record(s)") is meetable by a fresh 2-cell smoke
  re-run (the 15-01 continuation, NOT this plan — no GPU was run
  here); 15-03's consumption proof now rests on a true premise.

## Self-Check: PASSED

- Created/modified files FOUND: pipeline/dispatch_core.py (writer
  present, called from _spawn_worker between terminal-state assignment
  and finalize_claim), tests/test_dispatch_core.py (8 new tests),
  15-03-PLAN.md (corrected via-text + depends_on), deferred-items.md,
  this SUMMARY.
- Commits FOUND and are ancestors of HEAD: 9c22787 (Task 1),
  8c5e8b9 (Task 2); ledger gsd-plan-head-before-15-04 = 98d7279,
  measured commits since base = 2 (matches frontmatter).
- frozen-file porcelain over pipeline/run_sweep.py +
  pipeline/run_finetune.py + script/ = empty.
- VAL-01 deliberately NOT marked complete in REQUIREMENTS.md: its
  D15-02 criterion-3 evidence requires the fresh 2-cell smoke re-run
  owned by the 15-01 continuation.
