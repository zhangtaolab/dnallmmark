# Live 2x2 dual-GPU TUI run — operation record (quick-261022-pa6)

## Overview

- Date: `2026-10-22T11:25:30Z` (UTC) — mode: **live**
- Host: `autodl-container-75f44fb3e7-9b8d8ae4` — GPUs: `NVIDIA GeForce RTX 5090
NVIDIA GeForce RTX 5090`
- What ran: 2 models x 2 tasks x seed 42 x 1 epoch(s), workers=2, gpus=0,1 — 4 cells expected
- Models: plant-dnabert-6mer, plant-dnamamba-6mer
- Tasks: GUE__emp_H3, iDNA_ABF_datasets__5mC
- Output root: `/root/autodl-tmp/Github/dnallmmark/pipeline/finetuned-tui-pa6` (fresh — no trainer_state markers could skip cells)
- TUI state dir (kept; holds the tee log): `/root/autodl-tmp/dnallmmark-data/tui-live/tui-live-pa6-6rz8nhlz`
- Driver exit code: **0**

Every number in this record derives from the run's own meta (`docs/live/evidence.json`) and from commands run against the on-disk artifacts — evidence from the actually-run execution.

## Journey stage timings

| Stage | At (UTC) | Elapsed (s) |
|---|---|---|
| 01_boot_env_check | 2026-10-22T11:25:31Z | 0.7 |
| slot4_arrived | 2026-10-22T11:25:31Z | 1.1 |
| models_marked | 2026-10-22T11:25:37Z | 7.1 |
| 02_picker_models | 2026-10-22T11:25:37Z | 7.2 |
| datasets_marked | 2026-10-22T11:25:43Z | 12.8 |
| 03_picker_datasets | 2026-10-22T11:25:43Z | 12.9 |
| params_typed | 2026-10-22T11:25:57Z | 26.7 |
| preview_line_asserted | 2026-10-22T11:25:57Z | 26.7 |
| 04_run_config_params | 2026-10-22T11:25:57Z | 26.8 |
| argv_preview_asserted | 2026-10-22T11:25:57Z | 27.0 |
| 05_run_config_preview | 2026-10-22T11:25:57Z | 27.1 |
| gate_confirm_reached | 2026-10-22T11:25:57Z | 27.6 |
| 06_run_config_confirm | 2026-10-22T11:25:58Z | 27.6 |
| launch_y_pressed | 2026-10-22T11:25:58Z | 27.9 |
| monitor_switched | 2026-10-22T11:25:58Z | 27.9 |
| monitor_card_visible | 2026-10-22T11:27:06Z | 96.1 |
| dispatch_state_present | 2026-10-22T11:27:06Z | 96.1 |
| 07_monitor_running_01 | 2026-10-22T11:30:06Z | 276.4 |
| 07_monitor_running_02 | 2026-10-22T11:33:07Z | 456.7 |
| 07_monitor_running_03 | 2026-10-22T11:36:07Z | 637.0 |
| 07_monitor_running_04 | 2026-10-22T11:39:07Z | 817.3 |
| 07_monitor_running_05 | 2026-10-22T11:42:08Z | 997.6 |
| 07_monitor_running_06 | 2026-10-22T11:45:08Z | 1177.9 |
| 07_monitor_running_07 | 2026-10-22T11:48:08Z | 1358.2 |
| 07_monitor_running_08 | 2026-10-22T11:51:08Z | 1538.5 |
| 07_monitor_running_09 | 2026-10-22T11:54:09Z | 1718.8 |
| 07_monitor_running_10 | 2026-10-22T11:57:09Z | 1899.1 |
| 07_monitor_running_11 | 2026-10-22T12:00:09Z | 2079.5 |
| 07_monitor_running_12 | 2026-10-22T12:03:10Z | 2259.8 |
| 07_monitor_running_13 | 2026-10-22T12:06:10Z | 2440.0 |
| 07_monitor_running_14 | 2026-10-22T12:09:10Z | 2620.4 |
| 07_monitor_running_15 | 2026-10-22T12:12:11Z | 2800.6 |
| 07_monitor_running_16 | 2026-10-22T12:15:11Z | 2980.9 |
| 07_monitor_running_17 | 2026-10-22T12:18:11Z | 3161.2 |
| 07_monitor_running_18 | 2026-10-22T12:21:11Z | 3341.5 |
| 99_monitor_done | 2026-10-22T12:21:18Z | 3347.7 |

## Launch evidence

- The launch went through the REAL gate: the y key on the confirm face -> `LauncherBackend.launch_spec` -> `run_config.compose_dispatch_argv` -> `SweepLauncher._spawn` (start_new_session=True, cwd pinned to pipeline/, tee under the state dir's logs/).
- Dispatch argv (the [p] preview, verbatim):

  ```
  argv (LIST):/root/autodl-tmp/Github/dnallmmark/.venv/bin/python /root/autodl-tmp/Github/dnallmmark/pipeline/run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1 --models plant-dnabert-6mer,plant-dnamamba-6mer --output-root /root/autodl-tmp/Github/dnallmmark/pipeline/finetuned-tui-pa6 --tasks GUE__emp_H3,iDNA_ABF_datasets__5mC --seeds 42 --num_train_epochs 1 --cache_dir /root/autodl-tmp/.cache/hf --model_root /root/autodl-tmp/dnallmmark-data --dataset_root /root/autodl-tmp/dnallmmark-data --log_dir /root/autodl-tmp/dnallmmark-data/logs
  ```
- Tee log: `/root/autodl-tmp/dnallmmark-data/tui-live/tui-live-pa6-6rz8nhlz/logs/sweep_20261022_192558_finetuned-tui-pa6.log`
- dispatch_state.json at the completion poll: status=`running`, run_id=`6ac8db5bdaf0421fb523946c81780052` (the orchestrator's terminal write landed after the poll — final status `done`, 4/4, see Completion verification).

## GPU evidence (per-interval nvidia-smi snapshots)

- `2026-10-22T11:30:06Z` query-gpu: `0, 29 %, 2354 MiB, 40
1, 18 %, 3584 MiB, 39` — compute apps: `667772
668626`
- `2026-10-22T11:33:06Z` query-gpu: `0, 11 %, 2354 MiB, 39
1, 15 %, 3584 MiB, 37` — compute apps: `667772
668626`
- `2026-10-22T11:36:07Z` query-gpu: `0, 10 %, 2354 MiB, 39
1, 16 %, 3584 MiB, 38` — compute apps: `667772
668626`
- `2026-10-22T11:39:07Z` query-gpu: `0, 10 %, 2354 MiB, 38
1, 17 %, 3584 MiB, 39` — compute apps: `667772
668626`
- `2026-10-22T11:42:07Z` query-gpu: `0, 12 %, 2520 MiB, 38
1, 16 %, 3584 MiB, 37` — compute apps: `672077
668626`
- `2026-10-22T11:45:08Z` query-gpu: `0, 0 %, 4 MiB, 29
1, 16 %, 3584 MiB, 39` — compute apps: `668626`
- `2026-10-22T11:48:08Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 15 %, 3584 MiB, 37` — compute apps: `668626`
- `2026-10-22T11:51:08Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 16 %, 3584 MiB, 37` — compute apps: `668626`
- `2026-10-22T11:54:08Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 16 %, 3584 MiB, 39` — compute apps: `668626`
- `2026-10-22T11:57:09Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 16 %, 3584 MiB, 37` — compute apps: `668626`
- `2026-10-22T12:00:09Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 15 %, 3584 MiB, 38` — compute apps: `668626`
- `2026-10-22T12:03:09Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 17 %, 3584 MiB, 38` — compute apps: `668626`
- `2026-10-22T12:06:10Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 16 %, 3584 MiB, 37` — compute apps: `668626`
- `2026-10-22T12:09:10Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 16 %, 3584 MiB, 39` — compute apps: `668626`
- `2026-10-22T12:12:10Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 16 %, 3584 MiB, 37` — compute apps: `668626`
- `2026-10-22T12:15:11Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 15 %, 3584 MiB, 37` — compute apps: `668626`
- `2026-10-22T12:18:11Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 15 %, 3584 MiB, 37` — compute apps: `668626`
- `2026-10-22T12:21:11Z` query-gpu: `0, 0 %, 4 MiB, 28
1, 16 %, 3584 MiB, 37` — compute apps: `668626`

## Completion verification

- /proc probe (read-only `probe_cli_sweeps`) reports no live worker for the root: `True`
- The driver's completion poll fired at `2026-10-22T12:21:11Z` on exactly the
  plan's predicate (probe absent AND 4x final_metrics AND 4x flops_report).
  The very tail of the run was still landing: the last cell's
  `trainer_state.json` marker copy (`12:22:32Z`) and the orchestrator's
  FINAL `dispatch_state.json` (`status=done`, 4/4 completed, 0 failed,
  `updated_at=2026-10-22T12:22:33Z`) arrived ~80 s later — which is why the
  driver's own immediate count below read 3 trainer_state markers. The
  verification commands re-run against the quiesced tree count **4/4/4**:

  ```bash
  $ find pipeline/finetuned-tui-pa6 -path '*seed_42/final_metrics.json' | sort
  pipeline/finetuned-tui-pa6/plant-dnabert-6mer/GUE__emp_H3/seed_42/final_metrics.json
  pipeline/finetuned-tui-pa6/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42/final_metrics.json
  pipeline/finetuned-tui-pa6/plant-dnamamba-6mer/GUE__emp_H3/seed_42/final_metrics.json
  pipeline/finetuned-tui-pa6/plant-dnamamba-6mer/iDNA_ABF_datasets__5mC/seed_42/final_metrics.json

  $ find pipeline/finetuned-tui-pa6 -path '*seed_42/flops_report.json' | wc -l
  4

  $ find pipeline/finetuned-tui-pa6 -path '*seed_42/trainer_state.json' | wc -l
  4

  $ find pipeline/finetuned-tui-pa6 -path '*seed_42/trainer_state.json' | sort
  pipeline/finetuned-tui-pa6/plant-dnabert-6mer/GUE__emp_H3/seed_42/trainer_state.json
  pipeline/finetuned-tui-pa6/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42/trainer_state.json
  pipeline/finetuned-tui-pa6/plant-dnamamba-6mer/GUE__emp_H3/seed_42/trainer_state.json
  pipeline/finetuned-tui-pa6/plant-dnamamba-6mer/iDNA_ABF_datasets__5mC/seed_42/trainer_state.json
  ```

- Dispatch worker logs (the `{root}-dispatch-w{i}-{ts}.log` pair, written
  beside the root under `pipeline/`):

  ```bash
  $ ls pipeline/finetuned-tui-pa6-dispatch-w*
  pipeline/finetuned-tui-pa6-dispatch-w0-20261022_192558.log
  pipeline/finetuned-tui-pa6-dispatch-w1-20261022_192558.log
  ```

### Per-cell honesty spot-checks (read from the run's own artifacts)

| Cell | eval_f1 | eval_accuracy | train_time (s) | max_mem (GB) | flops gpu_device |
|---|---|---|---|---|---|
| plant-dnabert-6mer / GUE__emp_H3 | 0.8624338624338624 | 0.8610554442217769 | 803.4973 | 1.5942 | `NVIDIA GeForce RTX 5090` |
| plant-dnabert-6mer / iDNA_ABF_datasets__5mC | 0.9543568464730291 | 0.9529914529914529 | 138.2672 | 1.5594 | `NVIDIA GeForce RTX 5090` |
| plant-dnamamba-6mer / GUE__emp_H3 | 0.8909329829172142 | 0.8891115564462257 | 3076.1503 | 2.5079 | `NVIDIA GeForce RTX 5090` |
| plant-dnamamba-6mer / iDNA_ABF_datasets__5mC | 0.9707112970711297 | 0.9700854700854701 | 264.5869 | 1.6620 | `NVIDIA GeForce RTX 5090` |

Every cell's `final_metrics.json` carries the eval-merged metric family
(eval_f1 / eval_accuracy / eval_AUROC / ... — the 15-05 producer contract)
alongside the training fields; every `flops_report.json` carries the
verbatim `hardware.gpu_device` name above and an empty `uncovered_layers`.

## Honest notes

- The committed SVG stages 01-06 come from THIS launching run; the
  `--no-launch` rehearsal that de-risked the choreography ran earlier
  against the real app with zero GPU work and its captures were
  overwritten, never committed.
- The monitor card was NOT discovered within the first 60 s (the launched
  root is a sibling of the scan defaults, and the dispatch root holds no
  manifest until the first cell finalizes) — the driver drove the [a]
  attach modal with the resolved absolute path, the card rendered from the
  next scan on, and every 07 capture shows it.
- GPU 0 went idle from ~`11:45Z` onward: the queue had drained to its last
  cell (plant-dnamamba-6mer/GUE__emp_H3 — the 3076 s long runner on GPU 1),
  so one worker sat idle while the other finished. The 11:30Z-11:42Z
  snapshots show BOTH GPUs loaded (one compute app each) — the dual-GPU
  evidence; the later single-GPU snapshots are the honest queue tail, not
  a degraded run.
- The driver's stdout stage lines were swallowed by the app context's
  output capture in this invocation; every stage timestamp above comes
  from the meta sidecar (`evidence.json`), which is the authoritative
  record either way.
- Corroborating independent GPU snapshots (taken outside the repo during
  the run): `/root/autodl-tmp/dnallmmark-data/tui-live/watch-pa6.txt`.

## Re-attach instructions

The sweep is NEVER killed by the driver — if it is still alive it survives detached in its own session:

- TUI: slot 5, press `a`, type `/root/autodl-tmp/Github/dnallmmark/pipeline/finetuned-tui-pa6`
- CLI: `cat /root/autodl-tmp/Github/dnallmmark/pipeline/finetuned-tui-pa6/dispatch_state.json`
- Log tail: `tail -f /root/autodl-tmp/dnallmmark-data/tui-live/tui-live-pa6-6rz8nhlz/logs/sweep_20261022_192558_finetuned-tui-pa6.log`
- Live view: `nvidia-smi`
