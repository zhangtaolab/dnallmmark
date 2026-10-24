---
phase: quick-261022-tah
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/live/record_tui_live_svg.py
  - .gitignore
  - docs/live/fhs/IN-FLIGHT.md
autonomous: true
requirements: ["LIVE-tui-fhs-full-sweep-svg-report"]
user_setup: []

estimate:
  tokens: 54000
  raw_tokens: 36000
  tasks: 2
  confidence: low

must_haves:
  truths:
    - "The committed driver (scripts/live/record_tui_live_svg.py, extended surgically) drives the REAL app through the FULL production journey in operation order: boot env check -> slot-2 model download (cursor on FungiHelixSeek, press d -> real KIND_MODEL queue lane) -> slot-3 dataset enqueue-all (press a -> every missing downloadable dataset) -> interval captures of the download queue until it settles -> queue detail modal drill-down -> slot-4 wizard (FungiHelixSeek marked + EVERY present dataset marked) -> params (seeds typed 42,43,44; workers 2; gpus 0,1; fresh root pipeline/finetuned-fhs-full; epochs NOT touched — YAML default 3 governs and the record states it) -> [p] argv preview (asserting --num_train_epochs ABSENT) -> Y/N gate (dispatch-plan line 0,1) -> y -> real dual-GPU dispatch -> multi-day monitor interval captures -> automatic REPORT.md generation on completion. pa6's existing modes (--dry-run/--no-launch/defaults) stay byte-intact in behavior."
    - "The run REALLY downloads then REALLY trains: the model lane spawns the fixed python -I child (dnallm download_model + modelscope snapshot_download, zhangtaolab/FungiHelixSeek per the committed compat map); the dataset lane runs the modelscope CLI serially per key; the sweep runs as run_sweep_shard --mode dispatch --workers 2 --gpus 0,1 with seeds 42,43,44 over the DOWNLOADED-present dataset set — the matrix is the honest present set (every failed/skipped download lands in the ledger with its reason; zero downloadable datasets halts honestly)."
    - "EVERY stage and screen is captured as an ordered design-grid SVG under docs/live/fhs/svg/ (the 001..999 scheme below), with stage names and timestamps recorded in docs/live/fhs/evidence.json exactly like pa6; the evidence sidecar is written INCREMENTALLY (a heartbeat per interval) so progress is checkable from outside at any moment of the multi-day run."
    - "The driver runs DETACHED (the executor launches it via nohup/setsid and never kills it) and chains the whole journey autonomously; on completion it auto-generates docs/live/fhs/REPORT.md from the run's own artifacts (download ledger, per-dataset x seed metric/runtime/FLOPs table, failure ledger, GPU snapshots, stage timings, honest notes, re-attach). On stall (configurable hours with zero liveness signal) it records honestly and keeps watching by default; on failure/timeout it exports the failure capture and exits nonzero — the sweep is NEVER killed."
    - "The driver NEVER edits tui/ source; anchors derive from tui/strings.py constants resolved at runtime or language-neutral data (registry keys, counts, paths, the GPU tuple 0,1); a FRESH DNALLMMARK_TUI_STATE_DIR under /root/autodl-tmp holds the queue state file (download_queue.json), the queue logs, and the sweep tee log (disk policy); HF_HUB_OFFLINE=1 is asserted in preflight and inherited by every child; no CI or make-test surface changes; pipeline/finetuned-fhs-full/ is gitignored."
    - "The quick task closes HONESTLY in-flight: the executor verifies the detached driver reached a healthy start (preflight green, model+datasets enqueued, download phase advancing, first SVGs + heartbeat landing), commits docs/live/fhs/IN-FLIGHT.md (launch time, PID, log paths, expected matrix, honest ETA with its basis, how to check progress, where REPORT.md lands), and the SUMMARY states that the final evidence commit is a follow-up when the driver exits."
  artifacts:
    - "scripts/live/record_tui_live_svg.py — extended with --mode full: the download-journey phase (slot-2 d enqueue + slot-3 a enqueue-all + interval captures until the queue state file settles), the multi-day run posture (interval captures, incremental evidence heartbeat, stall detector, --timeout 0 default), the multi-cell completion predicate (per-seed artifact counts == dataset_count x 3), and automatic REPORT.md + download_ledger.json generation — all additive; --mode pa6 (the default) keeps the committed pa6 behavior reproducible"
    - ".gitignore — one added line pipeline/finetuned-fhs-full/ (the fresh sweep root, finetuned-smoke family discipline)"
    - "docs/live/fhs/svg/*.svg — the ordered stage captures from the real journey (001_boot_env_check, 002_model_row_missing, 003_model_enqueued, 004_data_presence_before, 005_data_enqueue_all, 006_download_running_NNN, 007_download_settled_queue, 008_download_presence_final, 009_queue_detail_modal, 010_wizard_model_marked, 011_wizard_datasets_marked, 012_run_config_params, 013_run_config_preview, 014_run_config_confirm, 015_monitor_running_NNN, 999_monitor_done; 997_monitor_stall / 998_monitor_failure on the honest degradation paths)"
    - "docs/live/fhs/evidence.json — the incrementally-written meta sidecar (stage timestamps, queue digests, per-interval nvidia-smi snapshots, artifact counts, heartbeat)"
    - "docs/live/fhs/download_ledger.json — at queue settle: per-key outcome (state, attempts, problems, log path, timings) plus the not-enqueued keys with reasons and the derived present-set matrix (written by the driver, on disk; committed by the completion follow-up)"
    - "docs/live/fhs/REPORT.md — the auto-generated final report (written by the driver on completion; committed by the completion follow-up)"
    - "docs/live/fhs/IN-FLIGHT.md — the committed launch-time handoff record (the only docs/live/fhs file committed in-session)"
  key_links:
    - "slot-2 d -> model lane: SelectionScreen action_download_model (screens/selection.py:1979) -> SelectionQueueBackend.enqueue_model -> app.kick_download_queue -> app.run_download_queue worker -> DownloadQueueService.run_task KIND_MODEL branch (services/download_queue.py:1947 — python -I -c MODEL_DOWNLOAD_PROGRAM landing repo_id, dnallm + modelscope snapshot_download, env dict(os.environ) so HF_HUB_OFFLINE rides through); landing under the directories.json model_root (/root/autodl-tmp/dnallmmark-data) via _normalize_model_landing + the config.json done gate"
    - "slot-3 a -> dataset lane: DataManagerScreen action_enqueue_all -> enqueue_all_missing (every missing key whose resolve_channel is downloadable; modelscope-mirror URL wins per _winning_url, shape-table repos only) -> the serial claim_next/run_task loop -> modelscope CLI children landing under the directories.json dataset_root; per-key done = landed AND reconcile pass (D-09/D-11 — presence flips on the merged view)"
    - "queue settle -> matrix: the driver reads {state_dir}/download_queue.json (no pending/downloading entries, stable across two reads) -> download_ledger.json -> present set derived through the SAME chain the picker renders (merge_presence over reconciled_rows + registries.presence_for) -> expected cells = len(present) x 3 seeds"
    - "wizard -> launch -> completion: filter-mark idiom (pa6-proven, cursor-walk for prefix-sharing families) -> params typed -> preview line 1 x N x 3 = 3N cells -> [p] argv tokens (--mode dispatch --workers 2 --gpus 0,1 --models FungiHelixSeek --tasks <comma-joined present set> --seeds 42,43,44 + root; --num_train_epochs ABSENT) -> gate y -> compose_dispatch_argv -> SweepLauncher._spawn (start_new_session, tee under the state dir) -> dispatch_state.json -> per-interval counts of *seed_{42,43,44}/final_metrics.json and flops_report.json == N each and probe_cli_sweeps() absent -> REPORT.md"
    - "screenshot seam: App.run_test(size=(120, 40)) + App.export_screenshot() with cursor blink disabled before every export (the pa6 lane, probe-verified byte-deterministic)"
---

<objective>
Run the production-scale FungiHelixSeek sweep ENTIRELY through the real TUI — download the model + all datasets via the download queue, select FungiHelixSeek x ALL present datasets x seeds 42,43,44 in the wizard, launch a real dual-GPU dispatch run, monitor it for its full multi-day duration, and auto-generate a final report — recording EVERY stage and screen as ordered SVG captures plus an honest operation record.

Combo (orchestrator-verified): model FungiHelixSeek (263M, modelscope zhangtaolab/FungiHelixSeek, compat-adapted, NOT on disk today); all 50 registry datasets (2 present on disk, 48 missing, every entry carries download_url + modelscope alternates); seeds typed "42,43,44" (user directive; also the schema default); workers=2, gpus=0,1; epochs NOT overridden (finetune_config.yaml default 3 governs — the record must state this); dedicated fresh output root pipeline/finetuned-fhs-full (gitignored).

Scale honesty the plan carries throughout: 50 datasets x 3 seeds = up to 150 cells at 263M params x 3 epochs. The pa6 actuals (4 cells, ~90M models, 1 epoch, 55 min wall) project an optimistic floor of ~3 days and a realistic 5-10+ days (BEND-class cells dominate). The executor CANNOT babysit this: the driver runs detached and chains the whole journey; the executor verifies a healthy start and closes the quick task honestly in-flight.

Purpose: an evidence-grade record of the full TUI-driven production journey — every number and frame from the actually-run execution (user rule), on the 2x RTX 5090 box, under the PIPE-02 smoke sanction for executed tasks on this host.

Output: the surgically-extended driver, the gitignored sweep root holding the run, the on-disk evidence home docs/live/fhs/ (svg/, evidence.json, download_ledger.json at settle, REPORT.md at completion), the committed IN-FLIGHT.md handoff, and zero changes to tui/, CI, or make test.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/quick/261022-pa6-tui-2-2-svg/261022-pa6-PLAN.md
@scripts/live/record_tui_live_svg.py
@tui/screens/data_manager.py
@tui/screens/selection.py
@tui/services/download_queue.py
@tui/services/sweep_launcher.py
@tests/tui/test_pilot_data_manager.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: extend the driver with the full journey (--mode full) + zero-GPU rehearsal green</name>
  <files>scripts/live/record_tui_live_svg.py, .gitignore</files>
  <action>
    ONE commit at the end; run everything from the repo root under `uv run --group tui --group gpu`. The extension is SURGICAL and ADDITIVE: every pa6 code path (constants MODELS/TASKS/SEEDS_TEXT="42"/EPOCHS_TEXT="1", the pa6 journey, its defaults --root pipeline/finetuned-tui-pa6 --interval 180 --timeout 5400 --svg-dir docs/live/svg --record docs/live/RECORD.md --evidence docs/live/evidence.json) keeps its exact behavior; the committed pa6 evidence must stay reproducible. The driver still NEVER edits tui/ source and enters no CI lane.

    1. .gitignore: add the single line `pipeline/finetuned-fhs-full/` beside the finetuned-tui-pa6 line (fresh-root discipline).

    2. THE EXTENSION (`--mode {pa6,full}`, default pa6). Full-mode constants: MODEL = "FungiHelixSeek"; SEEDS = ("42", "43", "44") typed as the literal text "42,43,44"; WORKERS_TEXT "2"; GPUS_TEXT "0,1"; NO epochs text (the epochs input is never touched — num_train_epochs None = YAML governs, run_config.py:1276 proves the argv token is absent). Full-mode flag defaults: --root pipeline/finetuned-fhs-full, --svg-dir docs/live/fhs/svg, --evidence docs/live/fhs/evidence.json, --report docs/live/fhs/REPORT.md, --ledger docs/live/fhs/download_ledger.json, --dl-interval 600.0 (download-phase capture cadence), --interval 1800.0 (run-phase cadence — hundreds of ~30 KB frames are fine, keep them all), --stall-hours 6.0, --exit-on-stall (default off: keep watching), --timeout 0.0 (NO hard deadline; the stall detector governs). Existing pa6 flags keep their pa6 defaults; explicit flags always win.

    3. FULL-MODE PREFLIGHT (spawned modes; halts exit 2 naming the leg): every pa6 live leg (import dnallm — print the memory rule on failure; HF_HUB_OFFLINE == "1"; exactly 2 GPUs and ZERO compute apps; fresh root; writable svg/report/evidence/ledger paths) PLUS: resolve_modelscope_cli() returns a path (both queue lanes gate on it — it doubles as the modelscope-package proxy); FungiHelixSeek exists in pipeline/models_info.json with a Model_path AND an adapted dnallm_compat.json slot (registries.load_dnllm_compat) carrying a modelscope repo id; pipeline/datasets_info.json parses; >= 200 GiB free on the mount holding --state-base (df -BG); record the model's on-disk presence — expected MISSING today, and if it is somehow present, note it honestly and skip the slot-2 enqueue leg (the gate outcome is recorded either way).

    4. THE FULL JOURNEY (async, App.run_test(size=(120, 40)), zero injected services, fresh mkdtemp DNALLMMARK_TUI_STATE_DIR under --state-base with the PINNED prefix "tui-live-fhs-" — every recording (rehearsal or live) gets its OWN fresh dir under that prefix, and the Task 2 gates glob the prefix and match the live run's file — set BEFORE app construction and KEPT on every path). Reuse pa6's helpers verbatim (export/wait_until/settle/_filter_mark/_type_into/_gpu_snapshot/_count_seed_artifacts — generalize _count_seed_artifacts to a seed set). Add `_queue_state_path()` = state_dir/"download_queue.json" and a read-only `_read_queue_entries()`; write evidence.json INCREMENTALLY after every stage and every interval (atomic write; include heartbeat {at, phase, interval_index}) — this is the external progress surface. Stage captures use the 3-digit ordered scheme:
    a. 001_boot_env_check — pa6's env-verdict wait, unchanged.
    b. MODEL LEG (skipped in rehearsal): press "2"; wait the selection table populated (poll #selection-table row count > 0 over the real registry); filter idiom with the selection screen's own widgets ("/" focuses #selection-filter, type the key, then cursor-walk #selection-table — read the row key via coordinate_to_cell_key like _cursor_key does — onto the exact FungiHelixSeek row; a bare filter legitimately matches prefix-sharing siblings). Export 002_model_row_missing. Press "d"; wait the queue state file contains a KIND_MODEL entry for FungiHelixSeek in pending/downloading (the honest machine check — the toast is not the assertion); export 003_model_enqueued. If enqueue refused (cli_unavailable / unknown reason), halt honestly exit 1 with the reason recorded.
    c. DATASET LEG: press "3"; wait the snapshot (poll #dl-missing row count > 0); export 004_data_presence_before (the PRIMARY full view — present/missing glyphs over all 50). Press "a"; wait the queue state file holds the missing downloadable entries as pending (record the count; enqueue_all skips disabled/unknown keys silently — that is the service's honest behavior); export 005_data_enqueue_all.
    d. DOWNLOAD WATCH: every --dl-interval seconds capture 006_download_running_NNN (3-digit NNN, monotonic), appending to evidence a queue digest (per-state entry counts) + the newest log size under state_dir/logs. SETTLE predicate: the queue state file holds NO pending/downloading entries on two reads spaced >= 60 s AND the model entry reached done/failed. Then export 007_download_settled_queue, the v-toggled missing view (one capture, then v back), and 008_download_presence_final. Focus #dl-queue, cursor onto a representative row (a done dataset), press enter, wait QueueDetailModal (#dl-detail-log), export 009_queue_detail_modal, escape. DOWNLOAD STALL: no queue-state-file change AND no log mtime/size change under state_dir/logs for --stall-hours -> honest note + 997 capture; keep watching unless --exit-on-stall.
    e. LEDGER + MATRIX at settle: write download_ledger.json — per queue key {key, kind, final state, attempts, problems, log_path, enqueued/started/finished}; the not-enqueued official keys with resolve_channel reasons (read-only derivation); the already-present-before keys. Derive the PRESENT SET through the same chain the picker renders (download_queue.merge_presence over reconciled_rows(state file) + registries.load_n_audit + registries.presence_for — pure reads). expected_cells = len(present) x 3. If present is empty: halt honestly (exit 1, ledger + draft report record why).
    f. WIZARD: pa6 steps c-h re-targeted — press "4", wait #cfg-picker populated; _filter_mark FungiHelixSeek; assert picker.selected == {MODEL}; export 010_wizard_model_marked; "m" flip (S.CFG_PICKER_DATASETS prefix wait); _filter_mark EVERY present-set key (the pa6 cursor-walk handles the GUE__emp_H3K* prefix families); assert set(picker.selected) == {MODEL} | present; export 011_wizard_datasets_marked. Params via _type_into: #cfg-input-seeds <- "42,43,44", #cfg-input-workers <- "2", #cfg-input-gpus <- "0,1", #cfg-input-output-root <- pipeline/finetuned-fhs-full (clear-by-length idiom; never assume the prefill); NEVER touch #cfg-input-epochs — instead READ it and record its value. Assert the preview line == S.CFG_PREVIEW_LINE.format(models=1, tasks=len(present), seeds=3, cells=expected); export 012_run_config_params. Press "p"; assert argv tokens: --mode dispatch, --workers 2, --gpus 0,1, --models FungiHelixSeek, --tasks <comma-joined present set>, --seeds 42,43,44, the resolved root — and assert "--num_train_epochs" is ABSENT (the epochs-governed-by-YAML proof); export 013_run_config_preview; escape. Enter -> the gate (pa6 refusal-halt rule intact); assert S.LNC_GATE_CONFIRM + the #cfg-gate-dispatch line carries "0,1"; export 014_run_config_confirm.
    g. FULL-MODE REHEARSAL (--no-launch): run a, the slot-2 LOCATE only (002-leg without pressing d — zero network), the slot-3 render (004-leg without pressing a), then e/f over TODAY's present set (the two on-disk datasets) through the gate, press n, exit 0. This rehearses every widget interaction the live run uses with zero network and zero GPU work; the download legs are service-driven, not choreography.
    h. LIVE LAUNCH: y -> monitor auto-switch (belt-and-braces "5") -> the pa6 card-wait + [a]-attach fallback -> dispatch_state.json present -> tee path recorded. First run-phase capture 015_monitor_running_001.
    i. RUN WATCH: every --interval seconds — gpu snapshot + dispatch_state digest + per-seed artifact counts into evidence, capture 015_monitor_running_NNN. COMPLETION: probe_cli_sweeps() absent for the root AND final_metrics counts == len(present) under seed_42 AND seed_43 AND seed_44 AND the same for flops_report. Then wait for the terminal tail (dispatch_state status terminal + trainer_state counts reach expected — the pa6 ~80 s tail lesson: quiesce-poll up to 10 min), export 999_monitor_done. RUN STALL: no dispatch_state mtime change AND no artifact-count change AND no file-mtime change under the root AND no tee growth for --stall-hours -> note + 997 capture; keep watching unless --exit-on-stall. FAILURE END: probe absent + dispatch_state terminal-bad or sweep_failures.json present with counts below expected -> 998_monitor_failure + honest exit 1. The sweep is NEVER killed on any path.
    j. AUTO-REPORT: on completion (and best-effort draft on every failure/stall-exit path), generate the --report file from the run's own artifacts ONLY: Overview (what/when/host/GPUs/mode; seeds 42,43,44; epochs 3 from the YAML default — stated explicitly since no override was typed); Download ledger table (from download_ledger.json: per key channel-outcome, state, attempts, problems, duration where timestamps exist); Run matrix summary (1 model x N present datasets x 3 seeds = 3N expected cells; the failed/skipped download list); Per-dataset x seed results table (walk the root's {model}/{task}/seed_{s}/final_metrics.json for the eval-merged primary metrics + train_runtime, flops_report.json for total FLOPs + gpu_device — every cell from an actually-run execution); Failure/skip ledger (downloads + cells, with reasons from the dispatch ledger / sweep_failures.json when present); GPU utilization summary (from the interval snapshots — honest about queue-tail idle GPUs); Stage timings (from evidence); Honest notes (stalls, degradations, the in-flight close-out, re-attach instructions). Style: pa6's _render_record discipline, ruff-clean, English.
    5. --dry-run in full mode prints the full stage timeline + resolved targets (registry dataset count, seeds text, root, interval/stall knobs, the honest scale projection) with zero spawn — alongside the pa6 timeline for --mode pa6.
    6. COMMIT only scripts/live/record_tui_live_svg.py + .gitignore: message `feat(quick-261022-tah): full-journey TUI SVG driver — download phase, multi-day watch, auto-report`; plain message, no Co-Authored-By trailers, LOCAL commit only (no push — the v1.3 ruling). Never stage the pre-existing dirty tree (.planning/** or tests/tui/__snapshots__*).
  </action>
  <verify>
    <automated>.venv/bin/ruff check scripts/live/record_tui_live_svg.py && .venv/bin/ty check scripts/live/record_tui_live_svg.py && uv run --group tui --group gpu python scripts/live/record_tui_live_svg.py --mode pa6 --dry-run && uv run --group tui --group gpu python scripts/live/record_tui_live_svg.py --mode full --dry-run && uv run --group tui --group gpu python scripts/live/record_tui_live_svg.py --mode full --no-launch && grep -c "finetuned-fhs-full" .gitignore</automated>
  </verify>
  <done>Driver ruff+ty clean; --mode pa6 --dry-run still prints the pa6 timeline (regression guard); --mode full --dry-run prints the full timeline with zero spawn; the full-mode rehearsal drives the REAL app (boot verdict, slot-2 locate, slot-3 render, wizard marks over today's present set, params with seeds 42,43,44 and the untouched epochs input, the no---num_train_epochs argv assertion, the Y-gate reached and dismissed with n) with zero network enqueue and zero GPU work, exit 0; .gitignore carries the fresh-root line; the commit lands with exactly the two files; no tui/, CI, or Makefile change.</done>
</task>

<task type="auto">
  <name>Task 2: detached live launch + healthy-start verification + honest in-flight close-out</name>
  <files>docs/live/fhs/IN-FLIGHT.md</files>
  <precondition>Both GPUs idle (nvidia-smi zero compute apps), dnallm + modelscope importable in the uv env, FungiHelixSeek absent on disk, ~2.0T free on /root/autodl-tmp — the driver's full-mode preflight asserts every leg and halts otherwise; the executor fixes only the named environmental cause (e.g. the dnallm editable reinstall) and restarts.</precondition>
  <action>
    ONE commit at the end. The journey runs for DAYS — the driver is launched DETACHED and never babysat in the foreground; every foreground Bash call stays under 2 minutes.

    1. Launch-day sanity: re-run `uv run --group tui --group gpu python scripts/live/record_tui_live_svg.py --mode full --no-launch` once (Task 1 proved it; this catches env drift in minutes) — must exit 0.
    2. LAUNCH DETACHED from the repo root via run_in_background (survives this session; nothing ever kills it): setsid nohup uv run --group tui --group gpu python scripts/live/record_tui_live_svg.py --mode full with stdout/stderr teed to /root/autodl-tmp/dnallmmark-data/tui-live/fhs-driver-<timestamp>.log (OUTSIDE the repo — the disk policy; the log path is recorded in IN-FLIGHT.md).
    3. HEALTHY-START VERIFICATION (bounded polling of the driver log, docs/live/fhs/evidence.json, docs/live/fhs/svg/, and the queue state file under the fresh state dir — short foreground reads only): (a) the log shows preflight green and the boot stage; (b) the model entry enqueued and claimed (queue state file holds the KIND_MODEL entry past pending) and the dataset entries enqueued (the count recorded); (c) >= 5 stage SVGs exist (001..005 family) with the "<svg" prologue; (d) progress is REAL — the queue state digest or the newest log size advanced between two polls spaced a few minutes apart, and the evidence heartbeat timestamp advanced; (e) the tee/driver logs are growing. If the driver halted in preflight: fix the named cause and restart ONCE; never hand-drive the app, the queue, or the sweep.
    4. Write docs/live/fhs/IN-FLIGHT.md from the live evidence (the committed handoff): launched-at UTC + driver PID + the driver log path; the state dir (queue state + queue logs + tee log) and the fresh root; the recorded dataset enqueue count + the matrix expectation (present-set x 3 seeds, finalized by the driver at settle); the honest ETA with its basis (pa6 actuals: 4 cells/55 min at ~90M x 1 epoch -> this run up to 150 cells at 263M x 3 epochs: optimistic floor ~3 days, realistic 5-10+ days, BEND-class cells dominate; the per-interval artifact counts in evidence.json refine it); how to check progress (evidence.json heartbeat + stage table; tail the driver log; tail the sweep tee; TUI slot-5 [a]-attach the root; nvidia-smi); what lands automatically (007-009 at download settle, download_ledger.json, 010-015 + 999 + REPORT.md at completion); the follow-up: when the driver exits, commit the docs/live/fhs evidence (and update IN-FLIGHT.md or replace it with the REPORT pointer) in a follow-up session — plus reboot/recovery honesty (the sweep is resume-safe via trainer_state markers + the dispatch ledger; a reboot kills only the driver).
    5. Repo cleanliness: git status confined to docs/live/fhs/** (untracked driver outputs stay untracked until the follow-up) + this task's bookkeeping; pipeline/finetuned-fhs-full MUST NOT appear (gitignored); never stage the pre-existing dirty tree.
    6. COMMIT docs/live/fhs/IN-FLIGHT.md only: message `docs(quick-261022-tah): launch detached FungiHelixSeek full sweep — in-flight handoff record`; plain message, no Co-Authored-By trailers, LOCAL commit only (no push).
    7. If healthy-start verification FAILS irrecoverably (the driver exited nonzero before the download phase stabilized): preserve the honest evidence (log + whatever SVGs/evidence landed), write the failure into IN-FLIGHT.md instead of the in-flight record, commit it, and surface the failure plainly in the SUMMARY (the same-truth rule).
  </action>
  <verify>
    <automated>grep -q '"mode": "full"' docs/live/fhs/evidence.json && test $(ls docs/live/fhs/svg/*.svg 2>/dev/null | wc -l) -ge 5 && ls /root/autodl-tmp/dnallmmark-data/tui-live/tui-live-fhs-*/download_queue.json >/dev/null && grep -q "FungiHelixSeek" /root/autodl-tmp/dnallmmark-data/tui-live/tui-live-fhs-*/download_queue.json && grep -c "finetuned-fhs-full" docs/live/fhs/IN-FLIGHT.md && git check-ignore -q pipeline/finetuned-fhs-full && git log -1 --name-only --pretty=format: | grep -c "docs/live/fhs/IN-FLIGHT.md"</automated>
  </verify>
  <done>evidence.json records mode full with advancing heartbeat; >= 5 ordered stage SVGs on disk; the queue state file exists and carries the FungiHelixSeek model entry plus the dataset entries (download verifiably running); IN-FLIGHT.md names the root, PID, log paths, matrix expectation, honest ETA + basis, progress-check instructions, and where/how REPORT.md lands; the root is gitignored; exactly one local commit carrying only IN-FLIGHT.md, no push; the SUMMARY closes the task honestly in-flight (the report verification is explicitly future work — the driver auto-generates it).</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| driver -> real app | the driver drives the REAL DnallmMarkTui in-process (Pilot lane) and presses real keys; it never mutates app/service state behind the UI |
| app -> download subprocesses | the queue worker spawns real modelscope CLI children (datasets) and the fixed python -I model child over days; env is exactly dict(os.environ) per child |
| download channels -> box | modelscope.cn (and only modelscope — _winning_url discards non-mirror URLs) fetches external data onto the data disk; everything landed is DATA, never executed |
| app -> GPU subprocess tree | the y-confirm spawns a real run_sweep_shard --mode dispatch tree (start_new_session) that trains for days and writes under the fresh root |
| detached driver -> session | the driver outlives the executor session (setsid/nohup); its only surfaces are the log, the SVGs, and the incrementally-written evidence.json |
| /proc reads | completion polling reuses the repo's DISPLAY-ONLY probe; no signals, ever |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-tah-01 | Tampering | the day-long environment (HF_HUB_OFFLINE lost, caches drifting to the system disk) | medium | mitigate | preflight asserts HF_HUB_OFFLINE == "1" and >= 200 GiB on the data-disk mount; every spawn chain (queue CLI children, the -I model child, the dispatch tree) inherits dict(os.environ) so the flag provably rides into every subtree; the state dir + tee + driver log all live under /root/autodl-tmp (disk policy) |
| T-tah-02 | DoS | double-launch over a busy GPU or a reused root (marker-skip masking a partial run) | medium | mitigate | preflight refuses unless 2 GPUs and ZERO compute apps and the root does not exist; the launcher's CR-02 live-root refusal is the structural backstop; the gitignored fresh root prevents trainer_state marker-skip fakery |
| T-tah-03 | Repudiation | committed claims not tied to the real multi-day run | high | mitigate | evidence.json is written incrementally by the driver from its own observations (stage timestamps, queue digests, per-interval GPU snapshots, artifact counts); IN-FLIGHT.md is generated from the live evidence at launch time and states what is still in flight; REPORT.md is generated from on-disk artifacts only (final_metrics/flops per cell, queue ledger, dispatch state); failure/stall paths record honestly and exit nonzero — no fabricated success, ever |
| T-tah-04 | Information Disclosure | /proc cmdline probing reads other processes' argv | low | accept | reuse of the repo's own reviewed read-only probe (probe_cli_sweeps): host-local, DISPLAY-ONLY, raw argv never rendered — only the launched root's presence is checked |
| T-tah-05 | Tampering | untrusted downloaded data (model snapshot + dataset files) | medium | mitigate | downloads are DATA: they land under the directories.json data-disk roots and are never executed during download; the model child is the FIXED module-level -I program (only landing dir + repo id cross as argv data); channel resolution accepts only modelscope.cn hosts validated against the committed shape tables (T-10-01-01 allowlist); training later reads them as data through the standard pipeline |
| T-tah-SC | Tampering | package installs (npm/pip/cargo) | high | mitigate | zero package installs — the driver reuses the committed uv environment (uv run --group tui --group gpu, modelscope + dnallm already importable, verified); no new dependencies, so no legitimacy checkpoint is required |
</threat_model>

<verification>
- Task 1 gate: ruff + ty clean; BOTH dry-runs print their timelines (pa6 regression + full timeline); the full-mode rehearsal drives the real app to the Y-gate over today's present set and dismisses with n (exit 0, ordered stage SVGs, zero network enqueue, zero GPU work); the no---num_train_epochs argv assertion proves the epochs discipline; the gitignore line present; the commit carries exactly the driver + .gitignore.
- Task 2 gate: the detached driver verifiably in flight (mode full in evidence.json, heartbeat advancing, model + dataset entries in the queue state file, >= 5 ordered SVGs with the svg prologue, download progress real between two polls); IN-FLIGHT.md committed alone; the sweep root gitignored; one local commit, no push.
- Live-tree respect: the driver never signals any process (read-only /proc probe), never edits tui/, and never kills the sweep or itself on stall by default — the honest record always says how to reach the run.
</verification>

<success_criteria>
- The real TUI downloaded FungiHelixSeek + every downloadable dataset through the real queue lanes, then launched the real dual-GPU dispatch run (FungiHelixSeek x the honest present set x seeds 42,43,44, workers 2, gpus 0,1, epochs from the YAML default) through the actual gate — the whole journey driven by one detached driver, recorded as ordered SVG stages + incremental evidence.
- The quick task closes honestly in-flight with a committed handoff record (IN-FLIGHT.md): ETA basis, progress-check paths, and the auto-report landing site; the final evidence commit is explicitly future work when the driver exits.
- The tool stays reusable (pa6 mode intact; full mode with dry-run / rehearsal / live / stall knobs), never enters CI, and leaves the repo clean apart from docs/live/fhs/**.
- Any failure, stall, or partial download would be recorded honestly (ledger + failure captures + nonzero exit) instead of fabricated success — the run matrix is always the actually-downloaded present set.
</success_criteria>

<output>
Create `.planning/quick/261022-tah-tui-fungihelixseek-seeds-42-43-44-svg/261022-tah-SUMMARY.md` when done
</output>
