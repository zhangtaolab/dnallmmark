---
phase: quick-261022-pa6
plan: 01
subsystem: tui-live-evidence
tags: [tui, dual-gpu, dispatch, svg-recording, evidence]
requires:
  - "the proven 2x2 combo on disk (plant-dnabert-6mer, plant-dnamamba-6mer x GUE__emp_H3, iDNA_ABF_datasets__5mC)"
  - "Phase 16 dispatch launch surface (compose_dispatch_argv, gate dispatch-plan line)"
provides:
  - "scripts/live/record_tui_live_svg.py — the reusable live SVG recording driver (dry-run / rehearsal / live modes)"
  - "docs/live/ — the committed evidence-grade operation record of the real 2x2 dual-GPU TUI journey"
affects: []
tech-stack:
  added: []
  patterns:
    - "Pilot-lane live recording: App.run_test(size=(120,40)) + export_screenshot over the REAL app with zero injected services, bounded poll loops with honest expiry"
    - "anchor authority: every asserted literal derives from tui/strings.py at runtime or language-neutral data (registry keys, counts, paths, the GPU tuple)"
key-files:
  created:
    - scripts/live/record_tui_live_svg.py
    - docs/live/RECORD.md
    - docs/live/evidence.json
    - docs/live/svg/01_boot_env_check.svg
    - docs/live/svg/02_picker_models.svg
    - docs/live/svg/03_picker_datasets.svg
    - docs/live/svg/04_run_config_params.svg
    - docs/live/svg/05_run_config_preview.svg
    - docs/live/svg/06_run_config_confirm.svg
    - docs/live/svg/07_monitor_running_01.svg .. 07_monitor_running_18.svg
    - docs/live/svg/99_monitor_done.svg
  modified:
    - .gitignore
decisions:
  - "cursor-walk filter idiom: a bare-substring picker filter legitimately matches prefix-sharing siblings (GUE__emp_H3 vs the GUE__emp_H3K* family — 6 rows), so the driver walks the cursor onto the exact target row instead of assuming a single-row filter; registry-order independent"
  - "committed the full docs/live/svg/ set (25 captures incl. all 18 interval monitors) per the plan's 'docs/live/svg/ only' commit instruction — the frontmatter's 07_monitor_running_01 entry is the minimal representative, the artifact truth names the NN family"
  - "the completion predicate is the plan's exact contract (probe absent + 4x final_metrics + 4x flops_report); the last cell's trainer_state marker copy and the orchestrator's final dispatch_state (done, 4/4) landed ~80 s later in the finalize tail — the RECORD documents the timing and the quiesced 4/4/4 verification"
metrics:
  duration: 83 min
  completed: 2026-10-22
  tasks: 2
status: complete
actuals:
  tokens: 18200  # chars/4 over the realized text diff (driver + .gitignore + RECORD.md + evidence.json; generated SVGs excluded)
  tasks: 2
  commits: 2
  plan_head_before: 15790a26ab73a8dd9cbf41929da35b4a968463f2
  plan_head_after: 105dd3c
---

# Phase quick-261022-pa6 Plan 01: TUI 2x2 dual-GPU live run with SVG record Summary

Real 2-model x 2-task dispatch run driven through the actual TUI gate (workers=2, GPUs 0,1, seed 42, 1 epoch, fresh root) and recorded as 25 design-grid SVG stage captures plus an operation record whose every number traces to the actually-run execution.

## What Ran (ground truth)

- **Journey through the REAL app** (zero injected services, fresh state dir under /root/autodl-tmp): boot env verdict -> slot-4 picker marks (2 models via the filter idiom) -> m-flip dataset marks -> params (seeds 42, epochs 1, workers 2, GPUs 0,1, root pipeline/finetuned-tui-pa6) -> preview line asserted exactly `2 models x 2 tasks x 1 seed = 4 cells` -> [p] dispatch argv asserted (`run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1`, comma-joined models/tasks, absolute root) -> Y/N gate (LNC_GATE_CONFIRM + dispatch-plan line carrying 0,1) -> **y** -> real spawn (start_new_session, cwd pipeline/, tee under the state dir) -> monitor auto-switch -> 18 interval captures -> done capture.
- **The run**: dispatch_state.json final `status=done`, 4/4 completed, 0 failed, 0 skipped; exact-path counts **4/4/4** for final_metrics / flops_report / trainer_state under `*seed_42/`; both GPUs busy simultaneously in the 11:30Z-11:42Z snapshots (one compute app each: 2354 MiB + 3584 MiB); per-cell spot checks carry eval_f1/eval_accuracy (0.862-0.971) and the verbatim `NVIDIA GeForce RTX 5090` gpu_device on all four flops reports.
- **Driver exit 0**; evidence.json committed as-is from the driver; the sweep was never signaled by anything the driver did (read-only /proc probe only).

## Tasks Completed

| Task | Name | Commit | Key files |
|---|---|---|---|
| 1 | live SVG recording driver + rehearsal green | `1be4cf9` | scripts/live/record_tui_live_svg.py, .gitignore |
| 2 | real dual-GPU run + evidence record commit | `105dd3c` | docs/live/RECORD.md, docs/live/evidence.json, docs/live/svg/ (25 captures) |

## Task 1 gate (all green)

- ruff + ty clean over the driver; `--dry-run` prints the 10-stage timeline with zero spawn/preflight; the `--no-launch` rehearsal drove the REAL app to the Y-gate (6 stage SVGs), pressed n, exit 0 with zero GPU work; `.gitignore` carries the `pipeline/finetuned-tui-pa6/` line (grep count 1); the commit carries exactly the two files; no tui/, CI, or Makefile change.

## Task 2 gate (all green)

- `evidence.json` exit_code 0; exact-path find counts 4/4/4; confirm + done SVGs carry the `<svg` prologue and are 37-112 KB; RECORD.md names the root and carries timings, both-GPUs-busy snapshots, the worker-log listing (`pipeline/finetuned-tui-pa6-dispatch-w{0,1}-20261022_192558.log`), the 4/4/4 verification outputs, and the per-cell spot checks; `git check-ignore` passes with zero porcelain lines under the root; one local commit, no push.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] filter idiom met the prefix-sharing GUE__emp_H3K* family**
- **Found during:** Task 1 rehearsal (first run)
- **Issue:** a bare-substring picker filter for `GUE__emp_H3` legitimately matches 6 dataset rows (`GUE__emp_H3K14ac`, `H3K36me3`, ...); the driver's assume-exactly-one-row check failed honestly.
- **Fix:** after filtering, walk the cursor down onto the exact target row (`picker.key_at(highlighted) == key`, bounded by the filtered row count) — registry-order independent, still the real filter+tab+space idiom.
- **Files modified:** scripts/live/record_tui_live_svg.py
- **Commit:** 1be4cf9

**2. [Rule 1 - Bug] dispatch argv assertion shape**
- **Found during:** Task 1 rehearsal (second run)
- **Issue:** `compose_dispatch_argv` threads comma-JOINED matrix filters (`--models a,b`), so per-key token assertions failed while the argv itself was correct.
- **Fix:** the expected-token list mirrors the pinned composer shape (comma-joined models/tasks).
- **Files modified:** scripts/live/record_tui_live_svg.py
- **Commit:** 1be4cf9

### Honest observations recorded (not deviations)

- The monitor card needed the plan's [a]-attach fallback (60 s): the launched root is a sibling of the scan defaults and a dispatch root holds no manifest until the first cell finalizes. The card then rendered for every capture.
- The completion poll fired on the plan's exact predicate while the last cell's trainer_state marker copy and the orchestrator's final `done` state landed ~80 s later in the finalize tail; the RECORD documents the timing and the quiesced 4/4/4 re-verification.
- GPU 0 idled from ~11:45Z (queue depth 1: the 3076 s plant-dnamamba-6mer/GUE__emp_H3 long runner on GPU 1) — the honest dispatch queue tail, documented in the RECORD.

## Verification Evidence

- Live run log (driver stdout): the stage prints were captured in `evidence.json` (the app context swallowed stdout in the live invocation — noted honestly in the RECORD); the dispatch tee log is preserved at `/root/autodl-tmp/dnallmmark-data/tui-live/tui-live-pa6-6rz8nhlz/logs/sweep_20261022_192558_finetuned-tui-pa6.log`.
- Corroborating independent GPU snapshots: `/root/autodl-tmp/dnallmmark-data/tui-live/watch-pa6.txt`.
- The run tree `pipeline/finetuned-tui-pa6/` stays on disk, gitignored (fresh-root discipline preserved for any re-record).

## Self-Check: PASSED

- Commits `1be4cf9` and `105dd3c` are ancestors of HEAD (merge-base verified).
- `scripts/live/record_tui_live_svg.py`, `docs/live/RECORD.md`, `docs/live/evidence.json`, and all 25 committed SVGs exist on disk.
- Task 1 + Task 2 automated verify chains re-run green; repo cleanliness confirmed (only pre-existing .planning/ and tests/tui/__snapshots__ dirt remains, untouched).
