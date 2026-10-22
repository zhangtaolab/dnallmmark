# IN-FLIGHT — TUI-driven FungiHelixSeek full sweep (quick-261022-tah)

This is the launch-time handoff record. The multi-day run is IN FLIGHT and
this quick task is closed in-flight; the final evidence commit is the
follow-up when the watcher driver exits. Every fact below comes from the
run's own artifacts (`docs/live/fhs/evidence.json`, the queue state file,
`dispatch_state.json`, the SVG captures) — evidence from the actually-run
execution.

## What is running

- **The sweep**: `run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1
  --models FungiHelixSeek --output-root
  /root/autodl-tmp/Github/dnallmmark/pipeline/finetuned-fhs-full --tasks
  <31 comma-joined present-set keys> --seeds 42,43,44` — launched through
  the REAL TUI gate (the [p] argv asserted `--num_train_epochs` ABSENT;
  epochs 3 comes from the `pipeline/finetune_config.yaml` default, no
  override typed). Orchestrator PID 728305; workers 728309 (gpu 0) /
  728310 (gpu 1), own sessions — NEVER killed by anything the drivers do.
- **Matrix**: 1 model x 31 present datasets x 3 seeds = **93 expected
  cells** (`dispatch_state.json` counts: total=93). The present set is the
  honest downloaded-present set: 2 already on disk (GUE__emp_H3,
  iDNA_ABF_datasets__5mC) + 29 downloaded and reconcile-passed through the
  real queue. 14 downloads failed reconcile (honest per-key reasons in
  `download_ledger.json`, e.g. GUE__EPI_GM12878's two-sequence CSV shape),
  1 mismatch, 4 shape-D keys were never enqueued (disabled-by-design).
- **The watcher driver** (PID 733194, detached): `record_tui_live_svg.py
  --mode full --attach-root pipeline/finetuned-fhs-full` — captures
  `015_monitor_running_NNN` every 1800 s + gpu snapshots + per-seed
  artifact counts, writes the incremental evidence heartbeat, and
  auto-generates `docs/live/fhs/REPORT.md` when the 93rd cell lands
  (terminal tail + `999_monitor_done`). Stall detector: 6 h with zero
  liveness signal -> honest note + 997 capture, keeps watching.

## Timeline (UTC, 2026-10-22)

- 14:32:02 — the journey driver launched detached (log:
  `/root/autodl-tmp/dnallmmark-data/tui-live/fhs-driver-20261022T143202Z.log`,
  PID was 719297).
- 14:32-14:33 — boot env check, slot-2 `d` press: the real KIND_MODEL lane
  downloaded zhangtaolab/FungiHelixSeek (~90 s, done gate config.json).
- 14:32-14:43 — slot-3 `a` press: 44 datasets enqueued; the serial queue
  drained them (29 done / 14 failed / 1 mismatch); settle at 14:53:31Z
  UTC+8 22:53 — see evidence `download.settle`.
- 14:56-15:01 — the wizard: FungiHelixSeek + all 31 present keys marked,
  seeds `42,43,44`, workers 2, gpus `0,1`, root `pipeline/finetuned-fhs-full`,
  epochs input NEVER touched (read back as `''`); preview line
  `1 x 31 x 3 = 93 cells`; the gate confirmed; **y** at ~15:01Z.
- 15:01 — the real dual-GPU dispatch spawned (tee:
  `/root/autodl-tmp/dnallmmark-data/tui-live/tui-live-fhs-6setv194/logs/sweep_20261022_225559_finetuned-fhs-full.log`).
- 15:01-15:02 — the journey driver hit TWO of its own choreography bugs
  post-launch (see Honest notes) and exited 1 WITHOUT touching the sweep.
- 15:11:06 — the watcher driver launched detached (log:
  `/root/autodl-tmp/dnllmmark-data/tui-live/fhs-watch-20261022T151106Z.log`),
  attached to the live root, first run-phase capture
  `015_monitor_running_001` + heartbeat at 15:12:16Z.

## Honest notes (read these)

- **The journey driver exited 1 at 15:02** — its monitor-attach choreography
  typed the root path into the attach modal before the input had focus (the
  path arrived truncated, validation refused). The sweep was already
  spawned in its own session and was NEVER affected. Both bugs (an
  earlier `wait_for_complete` that blocked the journey on the download
  drain, and this one) are fixed in commits `219ff37` (settle) and the
  attach-fix commit; the watcher (`--attach-root`, additive) carries the
  fixed choreography and CONTINUES the same `evidence.json` (the journey
  driver's exit is recorded in its notes — one sidecar, nothing
  overwritten).
- **The n_audit baseline was re-audited before launch** (the committed
  `dnallm-mark/data/n_audit.json` described the data-rich original machine
  — all 50 present — while this box held 2; the slot-3 missing-set derives
  from that artifact, so the download journey was impossible without the
  refresh). `python script/audit_n_frequencies.py --datasets-root
  /root/autodl-tmp/dnallmmark-data/datasets` refreshed the four
  maintainer-reviewable artifacts IN THE WORKTREE (uncommitted, never
  staged — R-03 design; before-snapshot at
  `/root/autodl-tmp/dnallmmark-data/tui-live/reaudit-record-261022/`).
  Before: 50/50 present per audit. After: 2 present / 48 missing (44
  downloadable + 4 shape-D) — which the journey then really downloaded.
- Evidence degradation from the settle bug: `005_data_enqueue_all` and the
  `dataset_enqueue` record landed at drain time (~11 min late) and exactly
  ONE `006_download_running` capture exists (the drain outpaced the 600 s
  cadence). Everything else is in stage order.

## How to check progress

- Heartbeat + stage table: `python3 -m json.tool
  docs/live/fhs/evidence.json | tail -40` (the `heartbeat` object + the
  per-interval `completion` block with per-seed final_metrics/flops counts).
- Sweep state: `cat pipeline/finetuned-fhs-full/dispatch_state.json`
  (status + counts out of 93).
- Orchestrator render: `tail -f
  /root/autodl-tmp/dnllmmark-data/tui-live/tui-live-fhs-6setv194/logs/sweep_20261022_225559_finetuned-fhs-full.log`.
- Watcher log: `tail -f
  /root/autodl-tmp/dnllmmark-data/tui-live/fhs-watch-20261022T151106Z.log`.
- TUI: slot 5 (the card for `finetuned-fhs-full`), or `a` + the root path.
- Live GPUs: `nvidia-smi` (both 5090s carry one worker each).

## Honest ETA (with its basis)

pa6 actuals: 4 cells (two ~90M models, 1 epoch) took 55 min wall on this
box -> ~14 min/cell. This run: 93 cells at 263M params x 3 epochs over 31
datasets (BEND__CpG_methylation-class cells dominate; the first two cells
started ~15:01Z). Projection: optimistic floor ~3 days; realistic 5-10+
days. The per-interval artifact counts in `evidence.json` refine this after
the first cells land (first `final_metrics.json` writes give the true
per-cell wall time).

## What lands automatically (and the follow-up)

- Every 1800 s: `015_monitor_running_NNN.svg` + gpu snapshot + counts +
  heartbeat (until 93/93).
- At completion: the terminal tail (<=600 s quiesce), `999_monitor_done`,
  and `docs/live/fhs/REPORT.md` (auto-generated from the run's own
  artifacts: download ledger, per-dataset x seed metrics/FLOPs table,
  failure ledger, GPU summary, stage timings, re-attach instructions).
- **Follow-up session** (when the watcher exits): commit the
  `docs/live/fhs/` evidence (SVGs + evidence.json + download_ledger.json +
  REPORT.md), replace or amend this file with the REPORT pointer.
- Reboot/recovery honesty: the sweep is resume-safe (trainer_state markers
  + the dispatch ledger — relaunch `run_sweep_shard --mode dispatch` with
  the same argv skips completed cells); a reboot kills only the watcher
  driver — relaunch it with the same `--attach-root` command (it continues
  the same evidence.json; if the orchestrator already finished, read
  `dispatch_state.json` + the ledger directly).

## Ops change 2026-10-23 — dataloader parallelism (maintainer directive "A")

The launch-day diagnosis (worker tqdm: 557,322 steps @ ~2.2 it/s for one BEND
cell at dynamic batch 4; GPU util ~20% with 49 of 50 CPUs idle) prompted a
three-lever review. The maintainer chose **A only** — `dataloader_num_workers:
12` in `pipeline/finetune_config.yaml` (pure I/O parallelism; batch, epochs,
lr, eval/save cadence UNTOUCHED — protocol comparability preserved; expected
2-4x on CPU-bound steps). The dispatch was restarted (killpg recipe on the
workers + orchestrator per the run_sweep_shard docstring; the two
replacement-spawned orphan cells were cleared first to avoid double-claims;
relaunched 2026-10-23 ~00:20 UTC+8 with the identical argv, orchestrator PID
819971, log `tui-live/fhs-dispatch-restart-20261023.log`; stale claims requeued
per dispatch_core's no-lease requeue design, 0 cells lost). The watcher
(PID 733194) survived the restart untouched and continues the same
`evidence.json`. Honest note: with A only, the full 93-cell matrix remains
multi-week (BEND-class eval cadence dominates); levers B (batch 32) and C
(eval_steps 5000) were declined to preserve protocol comparability.

## Commit map (this task, local only, no push)

- `dfb820e` feat(quick-261022-tah): full-journey TUI SVG driver — download
  phase, multi-day watch, auto-report (driver + .gitignore)
- `219ff37` fix(quick-261022-tah): drop the worker-settle from the slot-3
  enqueue leg
- (attach-fix commit) fix(quick-261022-tah): the focused attach typing +
  the `--attach-root` watch-only recovery lane
- This file: `docs(quick-261022-tah): launch detached FungiHelixSeek full
  sweep — in-flight handoff record`

The sweep root `pipeline/finetuned-fhs-full/` is gitignored
(fresh-root discipline; the evidence is this directory, never the run
tree).
