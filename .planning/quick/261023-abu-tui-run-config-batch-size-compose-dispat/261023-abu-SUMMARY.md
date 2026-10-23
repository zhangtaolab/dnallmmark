---
phase: quick-261023-abu
plan: 01
subsystem: pipeline-dispatch + tui-run-config
tags: [batch-size, passthrough, dispatch-lane, run-config, goldens, live-restart]
requires:
  - "run_sweep passthrough family (07-03 PIPE-02)"
  - "dispatch_core lane records + _RERUN_LANE_TOKENS (13/14)"
  - "TUI run-config params pane (Phase 11/16)"
provides:
  - "--batch_size as a first-class passthrough family member end-to-end (CLI, dispatch lane, TUI param, manifest/claim provenance)"
  - "journey-driver --batch-text full-mode flag"
affects:
  - "pipeline/run_sweep.py, pipeline/dispatch_core.py (lane threading)"
  - "tui run-config screen params pane (one new row)"
  - "the in-flight FHS sweep (restarted at batch 32 per maintainer order)"
tech-stack:
  added: []
  patterns:
    - "PARAM_EPOCHS verbatim mirror (empty=governs-elsewhere, present=threaded, machine problem on invalid)"
    - "present-only two-element argv append immediately after the --effective_batch_size append (the two batch knobs adjacent everywhere)"
key-files:
  created:
    - tests/tui/__snapshots__/run_config_confirm.svg
  modified:
    - pipeline/run_sweep.py
    - pipeline/dispatch_core.py
    - tui/services/run_config.py
    - tui/strings.py
    - tui/screens/run_config.py
    - tests/test_sweep.py
    - tests/test_dispatch_core.py
    - tests/tui/test_services_run_config.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_strings_phase11.py
    - tests/tui/__snapshots__/run_config.svg
    - scripts/live/record_tui_live_svg.py
    - .gitignore
    - docs/live/fhs/IN-FLIGHT.md
decisions:
  - "batch_size threads as the STARTING per-device batch — the child's determine_batch_size owns all scaling (the threaded value is not a guarantee); documented-not-conflated beside effective_batch_size"
  - "run_sweep_shard.py + run_finetune.py byte-untouched (parse_known_args remainder + existing scaling semantics are the whole mechanism)"
  - "argv_plan/_ARGV_VALUE_FLAGS deliberately untouched — the pair-scan is position-independent, a skipped --batch_size value can never misalign the models/tasks/seeds reads"
  - "restart fresh-root deviation: the dead root (0 completed, 2 stale claims) moved to pipeline/finetuned-fhs-full-b4-superseded (gitignored, Phase-15 superseded-evidence precedent) so the journey driver could relaunch at the SAME path"
metrics:
  duration: 74 min
  completed: 2026-10-23
estimate:
  tokens: 58000
status: complete
actuals:
  tokens: 41000
  tasks: 3
  commits: 5
commits: 5
plan_head_before: 9455b594b76d4588173d1a48da33a29f2ba3695a
plan_head_after: 16b4b20
---

# Phase quick-261023-abu Plan 01: TUI run-config batch_size — compose/dispatch passthrough Summary

One-liner: --batch_size is now a first-class passthrough family member — an editable, validated, persisted TUI param threading the STARTING per-device batch through compose_argv/compose_dispatch_argv into the dispatch lane (claim-recorded, rerun-replayed) to every run_finetune child, proven live by restarting the in-flight FHS sweep at batch 32 through the TUI journey driver.

## What Was Built

### Task 1 — pipeline passthrough (commit 8ea81fa)

- `pipeline/run_sweep.py`: `--batch_size` argparse flag (plain valued int, the --num_train_epochs shape — no bare-flag const), `>= 1` collect-all startup guard beside the EBS guard, `sweep_flags["batch_size"]` present-only (manifest-cell merge + run_matrix launch_kwargs partial), `build_argv`/`launch_subprocess` thread `["--batch_size", str(N)]` present-only IMMEDIATELY after the --effective_batch_size append; module docstring interplay note.
- `pipeline/dispatch_core.py`: `--batch_size` in `_RERUN_LANE_TOKENS`; the `run_dispatch` flag_problems mirror; ordinary `lane_values` (`sweep_args.batch_size`) + rerun `lane_values` (`agreed_lane.get` — tolerant, pre-change claims replay absent); worker `context["batch_size"]` + the spawn `build_argv` threading; dry-run `sweep_flags`; `_claim_payload`/`_launch_and_drain` docstring lane lists.
- `run_sweep_shard.py` and `run_finetune.py` byte-untouched.
- Tests: parse pins (absent → None; `--batch_size 8` → 8), build_argv threading + pinned adjacency, absent-flags zero-elements loop, zero-abort parametrize, CLI captured-argv pin, manifest-merge keys, run_record-untouched; dispatch lane-token refusal, claim-lane replay (lane carrying 32 replays `--batch_size 32` verbatim; stale lane replays absent), ordinary-lane threading + claim lane record, zero-refusal mirror.

### Task 2 — TUI param chain (commit c9cf047)

- `tui/services/run_config.py`: `PARAM_BATCH_SIZE`/`PROBLEM_BATCH_SIZE_INVALID`, `RunSpec.batch_size: int | None`, the epochs-shaped `parse_params` block, `_persist_payload` params key, `_spec_from_doc` absent-key tolerant read (`_optional_int_at_least_one`), both composers append present-only right after `--effective_batch_size`; docstrings' pinned-order lists updated.
- `tui/strings.py`: `CFG_FIELD_BATCH_SIZE` (flag vocabulary verbatim zh/en) + `CFG_BATCH_SIZE_DEFAULT` (the CFG_GPUS_DEFAULT "—（…）" prompt-hint grammar).
- `tui/screens/run_config.py`: one cfg-param-row after the EBS row (existing classes, compact input, placeholder hint; zero new CSS), Loaded prefill pair ("" when None), `_compose_spec` raw entry; NO `_problem_line` mapping — `batch_size_invalid` renders through the generic code+detail fallback exactly like epochs/ebs.
- Tests: 21 extended/new pins across services (defaults, happy path, invalid parametrize, empty/absent, collect-all, both element-for-element argv pins, absent-flags parametrize with the 10-element lock, persistence round-trips incl. `doc["params"]["batch_size"]`, pre-change-doc → None, shape-drift `{"batch_size": 0}`), pilot (defaults render + placeholder, typing pin threading `--batch_size 8` through the real dispatch composer + the `batch_size_invalid: 0` generic-fallback surface), strings inventory tripwire.

### Additional deliverable — journey driver `--batch-text` (commit d42ec36)

`scripts/live/record_tui_live_svg.py` full mode: `--batch-text N` types N into `#cfg-input-batch-size` via the `_type_into` idiom and the [p] argv assertion REQUIRES `--batch_size N`; default `""` never touches the batch input and asserts `--batch_size` ABSENT (the epochs-today discipline); pa6 mode refuses the flag (byte-intact lane); non-positive values refuse at parse; `batch_input_value` rides the evidence meta. Dry-run validated on all three paths.

### Task 3 — goldens (commit dfbbfae)

`make snapshot-update` regenerated all ten; the monitors reproduced their pre-task dirty bytes exactly (restored from backup anyway, sha256-verified OK); the other six byte-identical to HEAD; exactly `run_config.svg` + `run_config_confirm.svg` committed. D-03 review: run_config.svg delta = the new `batch_size` label row + the `—（默认: 按序列长度动态缩放）` placeholder at line 11, immediately after the EBS row (all other diff lines are the one-row y-shift + the content-derived terminal-id change); run_config_confirm.svg delta = exactly ONE new text fragment (the placeholder tail visible past the gate modal edge) — the modal content itself byte-unchanged.

### The restart (user order, commits 16b4b20 + IN-FLIGHT.md)

Executed per the documented procedure after all gates + ruff/ty green and committed: kill orchestrator (826884) first, 3 s, killpg-TERM trainers (826888/826889), zero-procs verified, watcher 733194 untouched; journey driver relaunched detached with `--batch-text 32` (offline env discipline exported — first attempt halted at preflight without it); the walk asserted the argv (`argv_preview_asserted`), pressed y, and the sweep relaunched. **New PIDs: orchestrator 870039, trainers 870043 (GPU 0) / 870044 (GPU 1)** — both trainer argv verified `--batch_size 32` via /proc. Worker log: `Base batch size: 32 | Dynamic starting batch size: 16 for max_len 514` (determine_batch_size governs).

**Measured post-restart (honest, two-sided):**

| Metric | Before (batch 4) | After (TUI-set 32) |
|---|---|---|
| BEND (514-tok) tier | 2.14–2.38 it/s, GPU 16–19 %, ~70 h/cell | **CUDA OOM at tier 16** — all 3 seeds failed (31.05 GiB in use, 2.02 GiB wanted, 32 GB cards) |
| Deep4mC (43-tok) tier | n/a (never reached) | **7.9–8.9 it/s sustained at batch 32**, GPU 31–40 %, first cell COMPLETED (seed 42, final_metrics.json) in ~19 min wall |

The launch-bound cure worked for the short-sequence tier (~4× step rate vs the 2.2 it/s baseline on a different, longer tier — stated as such); the >512-token tier does not fit batch-32-derived micro-batches on this hardware. State at close: 1 completed / 3 failed / 93 total, running. The driver itself exited at `998_monitor_failure` (its monitor-attach UI leg failed 60 s after y — the launch succeeded; the attach watcher 733194 owns the ongoing evidence heartbeat). Full ops record: `docs/live/fhs/IN-FLIGHT.md` "Ops change 2026-10-23 (later)"; ledger entry WINDOWS #51.

## Before/After Argv Evidence

- **ABSENT (D-12 parity):** a defaults spec composes exactly the 10 base elements with `--batch_size` not in argv (pinned: `test_compose_argv_defaults_exactly_ten_base_elements` + the absent-flags parametrize, len unchanged at 10); `run_sweep.build_argv` with no batch_size appends zero elements; `compose_dispatch_argv` threads zero; a pre-change `run_config.json` (no key) loads `batch_size None` and launches byte-identically (the `_PRE_CHANGE_DOC` pin).
- **PRESENT (full chain):** typed 8 → `compose_argv`/`compose_dispatch_argv` carry `["--effective_batch_size", "16"]` then `["--batch_size", "8"]` (element-for-element pins); CLI `--batch_size 8` reaches a child's captured argv; a claim lane carrying `batch_size: 32` replays `--batch_size 32` verbatim under `--rerun-failed`. Live proof: the running dispatch orchestrator (870039) and BOTH trainers (870043/870044) carry `--batch_size 32` in /proc cmdline; `evidence.json` records `batch_input_value: 32` + the `['--batch_size', '32']` argv segment.

## Verification Evidence

- Task 1: `pytest tests/test_sweep.py tests/test_dispatch_core.py tests/test_sweep_shard.py` — **315 passed**; ruff clean over the four files; `make typecheck` (ty) clean.
- Task 2: `pytest tests/tui/test_services_run_config.py tests/tui/test_pilot_run_config.py tests/tui/test_strings_phase11.py tests/tui/test_import_lock.py` — **304 passed**; ruff clean over tui/ + the touched tests + the driver; ty clean.
- Task 3 compare lane + full touched surface: `pytest tests/tui/test_snapshots.py tests/test_sweep.py tests/test_dispatch_core.py tests/tui/test_services_run_config.py tests/tui/test_pilot_run_config.py tests/tui/test_strings_phase11.py tests/tui/test_import_lock.py` — **569 passed**.
- Dirt audit: `git status tests/tui/__snapshots__/` shows ONLY the two committed run-config goldens differing from pre-task; monitor goldens sha256-match their pre-task bytes.
- In-flight safety: the pre-restart sweep was touched exactly by the documented restart procedure; the watcher survived every step.

## Pre-existing Snapshot Dirt (Task 3 step 10 — maintainer adjudication at milestone close)

- `monitor_empty.svg` + `monitor_running.svg`: carried PRE-EXISTING uncommitted modifications (WINDOWS #50, the deliberately uncommitted 16-05 golden batch) — left byte-untouched by this task (sha256-verified).
- `run_config.svg` was already modified and `run_config_confirm.svg` already untracked BEFORE this task (same #50 batch); their committed content here includes that prior 16-05 work plus the new batch row. #50 stays open for the still-uncommitted monitor pair + the D-03 review of the monitor content.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - test pin] Pilot export placeholder-count pin updated 4 → 5**
- **Found during:** Task 2
- **Issue:** `test_params_input_values_render_in_export` pins `svg.count("—（默认") == 4`; the new batch placeholder uses the same prefix, making the count 5.
- **Fix:** Updated the pin to 5 with the comment naming the batch-size row (the plan's pilot-test extension implied this surface).
- **Files modified:** tests/tui/test_pilot_run_config.py
- **Commit:** c9cf047

**2. [Rule 3 - blocking] Journey-driver fresh-root guard vs the same-root restart order**
- **Found during:** the restart step
- **Issue:** the driver's preflight refuses ANY existing output root (not only live roots, as the ops note assumed), blocking the ordered same-root relaunch.
- **Fix:** the dead root (0 completed cells, 2 stale claims, 112K) moved to `pipeline/finetuned-fhs-full-b4-superseded/` (gitignored — the Phase-15 superseded-evidence precedent + 15-05 gitignore-adjacency precedent); the driver relaunched into a fresh root at the SAME path, keeping the attach watcher's target valid.
- **Files modified:** .gitignore (adjacency line, committed with IN-FLIGHT.md)
- **Commit:** 16b4b20

**3. [Rule 3 - environmental] Driver relaunch needed the offline env discipline**
- **Found during:** the restart step
- **Issue:** first launch attempt halted at preflight (`HF_HUB_OFFLINE != '1'`) — each executor shell is fresh from the profile.
- **Fix:** relaunched with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME MODELSCOPE_CACHE` exported, replicating the watcher's environment.
- **Files modified:** none (launch-time env)

## Restart Anomalies (recorded exactly as observed — WINDOWS #51)

1. **All 3 BEND__CpG_methylation seeds CUDA-OOM at tier-16** (31.05 GiB in use / 2.02 GiB wanted / 32 GB cards). Failed cells recorded in the ledger, never requeued in-run. A `--rerun-failed` replay would carry the batch-32 lane VERBATIM and OOM again — a smaller-batch re-run needs a fresh launch lane. Maintainer decision pending.
2. **Driver `998_monitor_failure`**: the monitor-attach UI leg failed 60 s after y (the card did not appear within its timeout); the LAUNCH itself succeeded and the sweep runs — the attach watcher (733194) continues the evidence heartbeat.
3. Open risk noted in IN-FLIGHT.md: ≤512-token cells (GUE class) run at FULL batch 32 — the child's VRAM estimator is the remaining backstop; watch the failures list.

## Auth Gates

None.

## Known Stubs

None — every chain hop is test-pinned and the full chain is proven live on the running sweep.

## Self-Check: PASSED

All created/modified files exist on disk; all five commits (8ea81fa, c9cf047, d42ec36, dfbbfae, 16b4b20) verified as ancestors of HEAD.
