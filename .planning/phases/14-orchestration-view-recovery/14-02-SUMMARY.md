---
phase: 14-orchestration-view-recovery
plan: 02
subsystem: pipeline
tags: [cleanup, verify, dry-run, subprocess-seam, typed-gate, mgpu]

requires:
  - phase: 12-multi-gpu-static-sharding
    provides: "run_sweep_shard.py worker_root() naming authority + run_merge SHA256-verify copy + the merge test fixtures (make_worker_pair, run_merge_cli)"
  - phase: 14-orchestration-view-recovery
    provides: "wave-1 dispatch evidence markers (_root_has_dispatch_evidence reads dispatch_state.json / dispatch_ledger)"
provides:
  - "script/export_runs.py --dry-run — walk+count+print, zero writes (the D14-10 verification seam; loud FileNotFoundError on a missing root)"
  - "run_sweep_shard.py --cleanup / --yes — the fourth sibling mode: dispatch-evidence refusal, export dry-run subprocess leg, manifest cell-set equality leg, typed-phrase gate, scoped worker-root+log removal"
  - "the injectable runner/confirm_input seams for the export subprocess and the gate reader"
affects: [docs/multi-gpu.md runbook (manual rm -rf step now has a tested command — doc update itself is later scope), 15-validation (VAL-03 uses cleanup post-merge)]

actuals:
  tokens: 10651   # 42607 diff chars / 4 over script/export_runs.py, pipeline/run_sweep_shard.py, tests/ (estimate: 15000)
  tasks: 2
  commits: 4      # measured b928af7..0e88452 — the TDD RED/GREEN shape (2+2)

plan_head_before: b928af707c2c5548326cb4da0de8f9991ad84c49
plan_head_after: 0e88452b2fe6b2ae37b0f8f4a5e6889e02faa76e

tech-stack:
  added: []        # stdlib glob + existing subprocess only (T-14-SC: zero installs)
  patterns:
    - "dual-truth verification: the exporter walks the FILE tree while the manifest check compares PLANNED (model, task, seed) sets — both legs green before removal is offered (Pitfall 6 false-green)"
    - "typed-phrase gate = exact string equality against the RESOLVED --output-root (Q4); --yes carries it non-interactively, injected confirm_input drives it in tests, non-interactive-without---yes refuses"
    - "equals-form subprocess argument (--input-root=<path>) so a leading-dash root path can never re-parse as a flag (T-14-05)"

key-files:
  created: []
  modified: [script/export_runs.py, pipeline/run_sweep_shard.py, tests/test_export_runs.py, tests/test_sweep_shard.py]

key-decisions:
  - "Removal scope per Q5 ruling: exactly the worker_root()-named roots plus their {base}-mgpu-w{i}-*.log per-launch logs (the full manual recipe, docs/multi-gpu.md:157-160); the merged root is structurally never a target (T-14-03)"
  - "Gate mechanics per Q4 ruling: phrase = str(resolved root); --yes PHRASE compares non-interactively; interactive stdin prompts ONCE via the injectable confirm_input seam (default input); EOF/mismatch/non-interactive-without---yes all refuse non-zero with nothing removed"
  - "export_runs reached ONLY through [sys.executable, export_runs.py, --dry-run, --input-root=<R>] via the injectable runner seam (default subprocess.run, capture_output=True, text=True) — NEVER an import (numpy/yaml/scipy at its module top; stdlib-headless held, D14-16)"
  - "Leg B is SET equality over (model, task, seed) identity tuples (the _IDENTITY_CELL_KEYS projection minus status/output_dir) with sorted text-form diagnostics — never order-sensitive; a missing MERGED manifest refuses (nothing verified) while an empty-but-equal 0==0 set passes and removes the empty roots"
  - "Dispatch-evidence refusal reuses _root_has_dispatch_evidence verbatim for the base root AND every worker root (defense-in-depth, the run_merge precedent) and fires BEFORE the runner is invoked"

patterns-established:
  - "TDD RED/GREEN pair per task in an execute-type plan: RED commit pins the failing behavior (unrecognized flag / missing attribute), GREEN lands the minimal implementation — 4 commits, each revertable"
  - "The race-tolerant removal loop: re-check existence at removal time, note+skip absent paths, post-check every listed path is gone before reporting success"

requirements-completed: [MGPU-05]

coverage:
  - id: D1
    description: "--dry-run walks, counts, prints one line, writes nothing"
    requirement: MGPU-05
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py#test_dry_run_walks_counts_prints_and_writes_nothing"
        status: pass
      - kind: unit
        ref: "tests/test_export_runs.py#test_cli_export_without_dry_run_still_writes (control: flag gates only the dry path)"
        status: pass
  - id: D2
    description: "Missing root keeps the loud FileNotFoundError (the cleanup refusal signal)"
    requirement: MGPU-05
    verification:
      - kind: unit
        ref: "tests/test_export_runs.py#test_dry_run_missing_input_root_raises_filenotfound"
        status: pass
      - kind: other
        ref: "CLI probe: script/export_runs.py --dry-run --input-root /nonexistent-root -> exit 1 with FileNotFoundError traceback"
        status: pass
  - id: D3
    description: "Dispatch-evidence roots (base OR any worker root) refuse with the named needs-no-cleanup error before any verification"
    requirement: MGPU-05
    verification:
      - kind: unit
        ref: "tests/test_sweep_shard.py#test_cleanup_refuses_dispatch_roots_before_any_verification (runner asserted never invoked)"
        status: pass
  - id: D4
    description: "Both verification legs gate removal: export rc != 0 refuses naming returncode+tail; manifest set inequality refuses naming sorted cells"
    requirement: MGPU-05
    verification:
      - kind: unit
        ref: "tests/test_sweep_shard.py#test_cleanup_refuses_when_export_leg_fails"
        status: pass
      - kind: unit
        ref: "tests/test_sweep_shard.py#test_cleanup_refuses_on_manifest_cell_mismatch"
        status: pass
  - id: D5
    description: "Typed gate refusals: wrong --yes, EOF at prompt, mismatched line, non-interactive without --yes — all refuse with nothing removed"
    requirement: MGPU-05
    verification:
      - kind: unit
        ref: "tests/test_sweep_shard.py#test_cleanup_wrong_yes_phrase_refuses / #test_cleanup_eof_at_prompt_refuses / #test_cleanup_mismatched_typed_line_refuses / #test_cleanup_noninteractive_without_yes_refuses"
        status: pass
  - id: D6
    description: "Removal removes exactly the listed worker roots and logs; merged root intact; out-of-set logs untouched; combo refusals fire from main()"
    requirement: MGPU-05
    verification:
      - kind: unit
        ref: "tests/test_sweep_shard.py#test_cleanup_happy_path_removes_roots_and_logs_keeps_merged"
        status: pass
      - kind: unit
        ref: "tests/test_sweep_shard.py#test_cleanup_combo_refusals (merge/dispatch/dry-run/models/passthrough)"
        status: pass
      - kind: integration
        ref: "tests/test_sweep_shard.py#test_cleanup_real_subprocess_seam_verifies_and_removes (real subprocess.run seam end-to-end)"
        status: pass
  - id: D7
    description: "EDGE boundaries: empty-but-equal 0==0 passes both legs; missing merged manifest refuses; absent-at-removal skipped with a note; diagnostics set-based sorted"
    requirement: MGPU-05
    verification:
      - kind: unit
        ref: "tests/test_sweep_shard.py#test_cleanup_empty_but_equal_manifests_pass_both_legs / #test_cleanup_refuses_merged_root_without_manifest / #test_cleanup_worker_root_absent_at_removal_is_skipped_not_crash"
        status: pass
  - id: D8
    description: "Static mode byte-identical; zero CI/Makefile changes (D14-16)"
    requirement: MGPU-05
    verification:
      - kind: unit
        ref: "tests/test_dispatch_core.py static pins (-k static: 4 passed)"
        status: pass
      - kind: other
        ref: "make lint && make typecheck (All checks passed); git hash-object .github/workflows/ci.yml == 33d2252eb594e0faecece9e8015a332d8d6479ef; git status --porcelain Makefile empty"
        status: pass

metrics:
  duration: 37 min wall (includes ~10 min diagnosing the pre-existing offline d15 hang)
  completed: 2026-10-20

status: complete
---

# Phase 14 Plan 02: Post-merge verify + cleanup helper Summary

Landed the MGPU-05 verify-then-cleanup surface as a TDD RED/GREEN pair per task: `export_runs.py --dry-run` (the D14-10 verification seam — walk, count, print, zero writes) and `run_sweep_shard.py --cleanup/--yes` (the fourth sibling mode — dispatch-evidence refusal, export dry-run subprocess leg, manifest cell-set equality leg, exact typed-phrase gate, then removal of exactly the `worker_root()`-named roots plus their per-launch logs).

## Commits

| Task | Commit | Files |
| ---- | ------ | ----- |
| Task 1 RED: failing --dry-run tests | a141fa5 | tests/test_export_runs.py |
| Task 1 GREEN: --dry-run walk+count, zero writes | 8f7fedf | script/export_runs.py |
| Task 2 RED: failing --cleanup test matrix | 3b36404 | tests/test_sweep_shard.py |
| Task 2 GREEN: run_cleanup mode | 0e88452 | pipeline/run_sweep_shard.py, tests/test_sweep_shard.py |

## What Was Built

### Task 1 — export_runs.py --dry-run (tracer, TDD)

- RED: `test_dry_run_walks_counts_prints_and_writes_nothing` failed with
  `SystemExit: 2 — unrecognized arguments: --dry-run` (the flag did not
  exist; the control test passed — existing behavior pinned first).
- GREEN: a `store_true` flag on `main()` short-circuits BEFORE any
  write: `load_run_records(args.input_root)` (the same walk authority
  `export_runs_tree` uses) → one
  `[Dry-run] {records} run record(s) across {models} model(s) / {tasks} task(s) under {root}`
  line → `return 0`. No refactor of `export_runs_tree` (the surgical
  preference). Missing root keeps the loud `FileNotFoundError`
  (CLI-exit-1 verified by probe — that non-zero exit is the cleanup's
  leg-A refusal signal).
- Tracer feedback gate: full lane re-run end-to-end + acceptance greps
  (flag literal count 1, CLI exit 1) before expanding to Task 2.

### Task 2 — run_cleanup mode (TDD)

- RED: 13 tests failing on the missing feature
  (`AttributeError: no attribute 'run_cleanup'`; `--cleanup`
  unrecognized into the passthrough).
- Parser: `--cleanup` (store_true) + `--yes PHRASE` as additive entries
  (the `--mode` precedent — the static passthrough stays
  byte-identical; the 49-test shard baseline and the 4 dispatch static
  pins all green untouched).
- `main()` routing after the A6 block: `--cleanup` x `--merge` /
  `--mode dispatch` / `--dry-run` / `--models` / non-empty passthrough
  each refuses with a named `[Error]` before any mode runs.
- `run_cleanup(args, passthrough, runner=None, confirm_input=None)`:
  1. `--workers >= 1`; base root resolved absolute as the launch path
     resolves it.
  2. Dispatch-evidence refusal via `_root_has_dispatch_evidence` for
     the base root AND every worker root (the `_dispatch_merge_refusal`
     wording family: "needs no cleanup") — BEFORE the runner is invoked
     (asserted by test).
  3. Leg A: `[sys.executable, <repo>/script/export_runs.py, "--dry-run",
     f"--input-root={R}"]` through the injectable `runner` seam (default
     `subprocess.run`, `capture_output=True, text=True`; equals-form
     argument per T-14-05); rc != 0 refuses naming the returncode and
     the captured output tail; the counts line is echoed.
  4. Leg B: merged `sweep_manifest.json` cell SET over
     `(model, task, seed)` must EQUAL the union of worker manifest sets
     (missing merged manifest refuses "nothing has been verified";
     missing worker manifest refuses naming the root); discrepancies
     list sorted missing/extra cells in `{model}/{task}/seed_{seed}`
     text form.
  5. Removal plan printed first: every EXISTING `worker_root(R, i)`
     path (absent ones noted) and every `{base}-mgpu-w{i}-*.log` via
     `glob.escape` over the `worker_root()`-derived prefix (Q5: roots
     AND logs).
  6. Gate: phrase = `str(resolved root)`; `--yes` compares
     non-interactively; an injected `confirm_input` (or interactive
     stdin, `isatty`-gated) prompts once; EOF/mismatch/
     non-interactive-without-`--yes` refuse non-zero naming the phrase.
  7. Removal: rmtree/unlink only listed paths, existence re-checked at
     removal time (absent → note + skip, never a crash), post-check all
     gone, removed summary printed. The merged root is never a target.

## Verification Evidence

- `.venv/bin/python -m pytest tests/test_sweep_shard.py -q` → **62
  passed** (49 baseline + 13 new).
- `.venv/bin/python -m pytest tests/test_export_runs.py -q -k "not d15"`
  → **28 passed** (25 baseline-without-d15 + 3 new; the d15 exclusion is
  the environmental deviation below).
- `.venv/bin/python -m pytest tests/test_dispatch_core.py -q` → **66
  passed** (routing-change insurance; static pins included).
- `make lint` / `make typecheck` → All checks passed.
- `git hash-object .github/workflows/ci.yml` →
  `33d2252eb594e0faecece9e8015a332d8d6479ef` (byte-identical);
  `git status --porcelain Makefile` → empty.
- Acceptance greps: `run_cleanup` x2, `"--cleanup"` x1 in
  pipeline/run_sweep_shard.py; `"--dry-run"` x1 in script/export_runs.py;
  CLI probe over a missing root exits 1 with the FileNotFoundError
  traceback.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - test bug] RED test asserted the wrong leg ordering**
- **Found during:** Task 2 GREEN
- **Issue:** `test_cleanup_refuses_merged_root_without_manifest` asserted
  the runner was never invoked, but the designed flow runs leg A (export
  dry-run) BEFORE leg B's missing-manifest refusal — the test intent
  contradicted the dual-leg design.
- **Fix:** Assertion now pins "leg A ran exactly once, then leg B
  refused — removal never became possible".
- **Files modified:** tests/test_sweep_shard.py
- **Commit:** 0e88452

**2. [Rule 3 - blocking] ty rejected the None-variant set operations**
- **Found during:** Task 2 `make typecheck`
- **Issue:** ty could not trace the collect-all invariant
  (`_manifest_cell_identities` returning None always coincides with a
  problems append), so `worker_ids - merged_ids` and `len(merged_ids)`
  failed the gate on `None | set`.
- **Fix:** Structural narrowing — exit immediately when the merged
  manifest or its identity set is None (same behavior, ty-provable).
  Also simplified the test race wrapper's `rmtree` forwarding (a
  `**kwargs` forward trips ty's deprecated-`onerror` warning;
  `run_cleanup` calls `rmtree(path)` with one arg).
- **Files modified:** pipeline/run_sweep_shard.py, tests/test_sweep_shard.py
- **Commit:** 0e88452

### Environmental deviation (pre-existing, out of scope — not fixed)

`tests/test_export_runs.py::test_d15_evaluate_cross_validates_suite_mapped_metric_conventions`
hangs indefinitely in this offline sandbox: `evaluate.load("pearsonr")`
performs a blocking `requests` HTTP HEAD inside evaluate's own loader
(`evaluate/utils/file_utils.py:_request_with_retry`), and the host has
no network (`Network is unreachable`; it hangs even with the metric
cached and `HF_HUB_OFFLINE=1`). The test never touches `main()` — it is
unrelated to this plan's change and passed in prior networked runs. The
targeted lane is therefore the suite with `-k "not d15"`; the D-15
leg's verify obligation is recorded in the WINDOWS ledger.

## Auth Gates

None.

## Known Stubs

None — every refusal path and both verification legs are real (the one
real-subprocess test proves the seam outside the fakes; no mocks beyond
the injected runner/confirm_input seams the plan specifies).

## Threat Flags

None — no surface beyond the plan's threat model. T-14-03 (wrong-tree
deletion) mitigated structurally (worker_root()-only naming + log glob,
plan-printed paths, exact typed phrase, refusal tests); T-14-04
(false-green) mitigated by the dual-truth legs (export walks the tree,
manifest compares planned sets; both pinned); T-14-05 (argv injection)
mitigated by the equals-form single-argv subprocess, no shell;
T-14-SC held — zero installs.

## Self-Check: PASSED

- Files exist: script/export_runs.py, pipeline/run_sweep_shard.py,
  tests/test_export_runs.py, tests/test_sweep_shard.py — FOUND
- Commits are ancestors of HEAD: a141fa5, 8f7fedf, 3b36404, 0e88452 — FOUND
