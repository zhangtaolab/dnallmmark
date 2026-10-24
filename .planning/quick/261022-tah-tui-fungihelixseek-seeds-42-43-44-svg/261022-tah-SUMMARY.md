---
phase: quick-261022-tah
plan: 01
subsystem: tui-live-evidence
tags: [tui, dual-gpu, dispatch, download-queue, multi-day, svg-recording, evidence]
requires:
  - "the pa6 live-recording driver + its proven idioms (filter/cursor-walk, comma-joined argv shape, [a]-attach, the ~80 s terminal tail)"
  - "the Phase 13/14 dispatch engine + the Phase 10 download queue lanes (KIND_MODEL + modelscope datasets)"
provides:
  - "scripts/live/record_tui_live_svg.py --mode full — the full-journey profile (download phase, multi-day watch, auto-report, --attach-root recovery lane) with pa6 mode behavior intact"
  - "docs/live/fhs/ — the in-flight evidence home (ordered SVG stages, incremental evidence.json, download_ledger.json at settle, REPORT.md at completion) + the committed IN-FLIGHT.md handoff"
affects: []
tech-stack:
  added: []
  patterns:
    - "queue-state-file-as-assertion: every enqueue/settle/completion check reads the persisted machine state (download_queue.json / dispatch_state.json / artifact counts), never toasts or rendered text"
    - "evidence continuation: the --attach-root watcher adopts and continues the journey driver's evidence.json sidecar (one sidecar contract, prior exits recorded as honest notes)"
    - "no-settle-in-long-worker-land: pilot.pause rounds whenever a @work worker may outlive the stage (wait_for_complete blocks on the multi-day queue drain)"
key-files:
  created:
    - docs/live/fhs/IN-FLIGHT.md
    - docs/live/fhs/svg/001..015 + 998 captures (on disk; committed by the completion follow-up)
    - docs/live/fhs/evidence.json (incremental, on disk)
    - docs/live/fhs/download_ledger.json (on disk)
  modified:
    - scripts/live/record_tui_live_svg.py
    - .gitignore
decisions:
  - "the committed n_audit.json described the data-rich original machine (50/50 present) while this box held 2 datasets — the slot-3 missing-set derives from that artifact, so the plan's download journey was impossible without the app's own designed remedy: the CLI re-audit (R-03, schema-test refresh-stable by design) run once with --datasets-root /root/autodl-tmp/dnallmmark-data/datasets, artifacts left UNCOMMITTED for maintainer review (Rule 3; before/after recorded)"
  - "the wizard dataset assert is the exact per-view set (PickerList.selected is scoped to the current kind's rendered rows — the plan's union assert is unsatisfiable as written); the union is proven by the preview line 1x31x3=93"
  - "the journey driver's two post-launch choreography bugs (worker-settle block, attach-input focus race) were fixed in-driver and recovered WITHOUT touching the sweep via the additive --attach-root watch-only lane that continues the same evidence sidecar"
  - "probe_cli_sweeps matches only run_sweep.py (pre-shard constant) — the shard-era dispatch run is invisible to it (same in pa6); the watcher's completion detection is artifact-count-based (31/seed x both artifacts) + dispatch terminal tail, so the blindness is cosmetic"
metrics:
  duration: 135 min
  completed: 2026-10-22
  tasks: 2
status: complete
actuals:
  tokens: 29300  # chars/4 over git diff edc6f38..HEAD (117335 chars: driver + .gitignore + IN-FLIGHT.md)
  tasks: 2
  commits: 4
  plan_head_before: edc6f3839b150c8682ada3857cc6f0212d6e1dff
  plan_head_after: e2bc87d
---

# Phase quick-261022-tah Plan 01: TUI FungiHelixSeek full sweep, seeds 42/43/44, SVG record Summary

The REAL TUI downloaded FungiHelixSeek + every downloadable dataset through the real queue lanes, then launched a REAL dual-GPU dispatch (FungiHelixSeek x 31-dataset honest present set x seeds 42,43,44 — 93 cells, workers 2, gpus 0,1, epochs 3 from the YAML default with the argv proving no override) through the actual gate; the multi-day run is verifiably IN FLIGHT under a detached watcher that records ordered SVG stages + an incrementally-written evidence sidecar and will auto-generate REPORT.md on completion.

## What Ran (ground truth)

- **The journey** (detached driver, launched 2026-10-22T14:32:02Z): boot env verdict (48-dataset route line) -> slot-2 filter+cursor-walk onto FungiHelixSeek, `d` -> the real KIND_MODEL lane (zhangtaolab/FungiHelixSeek via the fixed `python -I` child; done gate config.json; ~90 s) -> slot-3 PRIMARY presence view, `a` -> **44 datasets enqueued** (48 missing = 44 downloadable + 4 shape-D disabled; 2 already present) -> the serial queue drained them (29 done + 14 reconcile-failed + 1 mismatch — every outcome in download_ledger.json with per-key reasons, e.g. GUE__EPI_GM12878's two-sequence CSV shape) -> settle captures (007 settled queue + v-toggled missing view + 008 final presence + 009 queue-detail drill-down) -> ledger + matrix: **present set 31, expected 93** -> the wizard (model marked, all 31 present keys marked via the pa6 cursor-walk filter idiom, seeds typed 42,43,44, workers 2, gpus 0,1, fresh root, **epochs input never touched — read back ''**; preview line 1x31x3=93 asserted; [p] argv asserted incl. `--num_train_epochs` ABSENT) -> the Y/N gate -> **y at ~15:01Z**.
- **The run**: `run_sweep_shard.py --mode dispatch --workers 2 --gpus 0,1 --models FungiHelixSeek --tasks <31 keys> --seeds 42,43,44` over `pipeline/finetuned-fhs-full/` (gitignored fresh root); dispatch_state total=93; both RTX 5090s training one cell each since 15:01Z (w0 seed_42 / w1 seed_43 of the first dataset); orchestrator + workers in their own sessions — never signaled by anything the drivers did.
- **The watcher** (detached, PID 733194, launched 15:11:06Z after the journey driver's honest exit): `--mode full --attach-root pipeline/finetuned-fhs-full` — monitor card attached (it needed the fixed [a]-attach fallback), first run-phase capture + heartbeat at 15:12:16Z, second interval at 15:42:17Z with per-seed artifact counts (0/31 each — first cells still training at close-out); it captures 015_monitor_running_NNN every 1800 s and will write 999_monitor_done + REPORT.md at 93/93 (stall detector 6 h, no hard timeout, sweep never killed).
- 17+ ordered SVGs on disk with the `<svg` prologue; evidence.json incremental with advancing heartbeat; tee log preserved under the journey state dir (`tui-live-fhs-6setv194/logs/sweep_20261022_225559_finetuned-fhs-full.log`).

## Tasks Completed

| Task | Name | Commit | Key files |
|---|---|---|---|
| 1 | driver extension (--mode full) + zero-GPU rehearsal green | `dfb820e` (+ fixes `219ff37`, `552fb3c`) | scripts/live/record_tui_live_svg.py, .gitignore |
| 2 | detached live launch + healthy-start verification + in-flight close-out | `e2bc87d` | docs/live/fhs/IN-FLIGHT.md |

## Task 1 gate (all green)

- ruff + ty clean over the driver; BOTH dry-runs print their timelines (pa6 regression + the 17-stage full timeline with the honest scale projection); the full-mode rehearsal drove the REAL app over today's present set (boot, slot-2 LOCATE only, slot-3 render only, ledger 2x3=6, wizard marks, params with seeds 42,43,44 and the untouched epochs input, the no-`--num_train_epochs` argv assertion, the Y-gate reached and dismissed with n) — exit 0, zero network enqueue, zero GPU work; `.gitignore` carries the `pipeline/finetuned-fhs-full/` line; each commit carries exactly its planned files; no tui/, CI, or Makefile change.
- EXTRA regression proof (beyond the verify chain): a full pa6-mode rehearsal re-run against scratch outputs — exit 0, the exact pa6 stage chain 01..06 + gate_dismissed_n, the exact pa6 argv — the pa6 code path is behaviorally intact after the extension.

## Task 2 gate (all green, closed in-flight per the plan)

- evidence.json records mode full with the heartbeat advancing (start 14:32 -> download 14:43 -> run 15:12 -> 15:42); 17 ordered stage SVGs with the svg prologue; the queue state file under `tui-live-fhs-6setv194/` carries the FungiHelixSeek model entry (done) + the 44 dataset entries; download progress was real between polls (45 queue logs streamed in ~11 min; both GPUs training across three polls); IN-FLIGHT.md names the root, PIDs, log paths, the 31x3=93 matrix expectation, the honest ETA with its basis, progress-check instructions, and where/how REPORT.md lands; the root is gitignored; commits local only, no push.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking environmental issue] the committed n_audit.json did not describe this box**
- **Found during:** Task 1 pre-implementation verification
- **Issue:** the slot-3 missing-set derives from the committed `dnallm-mark/data/n_audit.json` (merge_presence chain), which reported all 50 datasets PRESENT (the artifact of the data-rich original machine) while this box's disk held 2. As-planned: press-`a` would enqueue 0, the derived present set would be 50, and the launched 150-cell sweep would be 96% cells referencing missing dataset dirs — defeating the plan's core purpose.
- **Fix:** the app's own designed remedy (the boot screen's directive): `python script/audit_n_frequencies.py --datasets-root /root/autodl-tmp/dnallmmark-data/datasets` — once, before launch. Before: 50/50 present per audit. After: 2 present / 48 missing (44 downloadable + 4 shape-D). The four refreshed artifacts (n_audit.json, n_audit.csv, eval_subsets.json, DATA.md) stay UNCOMMITTED worktree changes for maintainer review (the R-03 contract; never staged by this task); before-snapshot preserved at `/root/autodl-tmp/dnallmmark-data/tui-live/reaudit-record-261022/`.
- **Files:** worktree-only (see above); documented in IN-FLIGHT.md
- **Commit:** none (deliberately uncommitted)

**2. [Rule 1 - Bug] `wait_for_complete` blocked the journey on the multi-day queue drain**
- **Found during:** Task 2 healthy-start watch (first live launch)
- **Issue:** the slot-3 leg's `settle()` call awaited `app.workers.wait_for_complete()` while the queue drain worker ran the whole download phase — the 005 stage + the dataset_enqueue record landed ~11 min late (post-drain), and exactly ONE 006 interval capture exists (the drain outpaced the 600 s cadence anyway).
- **Fix:** three pilot pauses instead of the worker settle (commit `219ff37`); the in-flight run completed honestly on the pre-fix code.
- **Files:** scripts/live/record_tui_live_svg.py

**3. [Rule 1 - Bug] the attach-modal typing raced the input focus (driver died post-launch)**
- **Found during:** Task 2 healthy-start watch (first live launch)
- **Issue:** after the y-launch, the monitor card did not appear within 60 s and the [a]-attach fallback typed the root path before the modal's input had focus — the path arrived truncated, validation refused, and the driver exited 1 at the modal-dismiss timeout. The already-spawned sweep was never affected.
- **Fix:** wait for real input focus, type + verify the value, clear + retry once, surface the modal's problem text on refusal; plus the additive `--attach-root` watch-only lane (requires --mode full; attaches to a live root, adopts + continues the same evidence.json, never spawns anything) — commit `552fb3c`. The watcher (launched 15:11:06Z) used the fixed choreography (its own card wait needed the fallback too, and it worked).
- **Files:** scripts/live/record_tui_live_svg.py

**4. [Rule 1 - Plan-text slip] the wizard union assert was unsatisfiable**
- **Found during:** Task 1 full rehearsal (first run)
- **Issue:** `PickerList.selected` is scoped to the current kind's rendered rows (SelectionList semantics) — after the m-flip it holds dataset marks only, so `selected == {MODEL} | present` can never hold.
- **Fix:** the exact per-view set asserts (model on the models view at 010, datasets on the datasets view at 011); the union is proven by the preview line (1x31x3=93) and the argv tokens.
- **Files:** scripts/live/record_tui_live_svg.py; Commit `dfb820e`

### Honest observations recorded (not deviations)

- 14 dataset downloads failed the reconcile gate and 1 mismatched (per-key reasons in the ledger — e.g. the GUE EPI two-sequence CSV shapes the audit kernel cannot reconcile); 4 shape-D keys were never enqueued (disabled-by-design). The matrix is the honest 31-key present set, exactly as the plan's honest-matrix rule demands.
- `probe_cli_sweeps` matches only `run_sweep.py` argv names — the shard-era dispatch run is invisible to it (pre-existing, same in pa6; not this task's file to fix). The watcher's completion predicate is therefore artifact-count-based (31/seed for BOTH artifacts) + the dispatch terminal tail — exact and unaffected.
- ty 0.0.85 resolves `from tui.services import registries` to a partial module view when download_queue is imported alongside (drops `load_dnllm_compat`); the driver avoids the member entirely by routing the model-channel preflight through the queue's own `resolve_model_channel` (the one authority the lane uses).
- This box's filesystem (docker overlay + xfs data disk) returns transiently inconsistent directory views across reads of concurrently-written files; the drivers' own incremental artifacts (evidence.json, the queue state file) are the authoritative surfaces.

## Known Stubs

None — every driver surface is wired to real machine state.

## What is still in flight (the honest close-out)

The sweep (93 cells) and the watcher (PID 733194) are RUNNING as this task closes; 0/93 cells at close-out (first cells ~45 min in). When the watcher exits: commit the docs/live/fhs evidence (SVGs + evidence.json + download_ledger.json + REPORT.md) in the follow-up session per IN-FLIGHT.md. IN-FLIGHT.md carries the full handoff (ETA basis, progress checks, re-attach, reboot recovery).

## Self-Check: PASSED

- Commits `dfb820e`, `219ff37`, `552fb3c`, `e2bc87d` are ancestors of HEAD (rev-list count 4 from plan_head_before edc6f38).
- scripts/live/record_tui_live_svg.py, .gitignore line, docs/live/fhs/IN-FLIGHT.md, docs/live/fhs/evidence.json, download_ledger.json, and the SVG set exist on disk.
- Both task verify chains re-run green; the sweep root is gitignored; the pre-existing dirty tree (.planning/**, tests/tui/__snapshots__*) was never staged; local commits only, no push.
