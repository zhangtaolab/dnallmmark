---
phase: 11-run-config-launch-gates-single-gpu-monitoring
plan: "07"
subsystem: ui
tags: [monitor-screen, slot-5, cadence-workers, attach, failures-rerun, log-tail, d-13-auto-nav, degradation-sweep, sc-ledger, gb10-smoke, phase-11-final]

requires:
  - phase: 11-04
    provides: the pure scanner (full_scan/frontier_scan/cells_view/stats/failures_view/read_log_tail/resume_count/is_sweep_root/add_manual_root + the SweepSummary/CellSeed/EtaEstimate vocabularies + format_hms/format_eta)
  - phase: 11-06
    provides: the app-owned shared launcher (live_sweeps/tee_path_for/launch_spec), the slot-4 launch-finished site, the nav promotion trio precedent, the Pilot fake idiom, EnvBlockModal/ConfirmModal/PathInputModal reuse
  - phase: 11-03
    provides: launch_from_failures (the same-seam re-run) + env_preflight over the frozen face
  - phase: 11-05
    provides: the 99 frozen MON_/LNC_/CFG_ constants (consumed by name; zero additions — the tripwire stays green)
  - phase: 09-03
    provides: the nav shell + the digit-binding Pattern 2 + the worker/run-id discipline lineage
provides:
  - tui/screens/monitor.py — the slot-5 screen: MonitorServiceProtocol + MonitorBackend (the 11-04 scanner with the launcher's live roots injected + the manifest scale read + the cell_record seam), the D-09 set_interval cadence over exclusive mon-frontier/mon-full workers, the discovered pane (three D-03 states, phase-10 progress grammar, D-17 ETA cells), the cell table (seed columns, five glyph states, curve mini-counts, the resume note), the stats-line variants, FailuresModal + the gated from-failures re-run (env preflight included), LogTailModal (tee/no-tee), CellDetailModal (records verbatim), [a] PathInputModal gating, [r] rescan, the tolerant-worker wrappers, the ever-discovered vanish rule
  - app.py — the monitor_service/monitor_launcher constructor seams, the ONE cached build_monitor_screen factory (attach state survives navigation), the action_nav monitor branch, the D-13 sweep_launched hook + MonitorSwitchRequested, the q-intercept predicate extended to attached running sweeps with live done/total threading into LNC_EXIT_MESSAGE
  - nav.py slot-5 promotion (NavSlot(5, ..., "monitor", None); the stale by-12 annotation removed; NAV_PLACEHOLDER_* retained with a zero-consumers note)
  - LauncherServiceProtocol/Backend gain launch_from_failures (the shared seam the [f] re-run routes through)
  - tests/tui/test_pilot_monitor.py — 27 Pilot tests over constructor-injected fakes (lanes 1-3: shell/interactions/degradation/responsiveness)
  - tests/tui/test_pilot_run_config.py — the D-13 auto-nav integration test
affects: [Phase 12 (single-GPU validation evidence: this SUMMARY + the smoke procedure are the hard-gate trail), CFG/LNC/MON constants (frozen, consumed only)]

actuals:
  tokens: 37055   # chars/4 over the realized diff (148222 chars, 9 files)
  tasks: 3
  commits: 4      # measured: git rev-list --count c190d07..HEAD
plan_head_before: c190d07ed20d3320f7ae3c9a538e83b16f7dfd5e
plan_head_after: ccc7c14

tech-stack:
  added: []   # textual built-ins only (DataTable/RichLog/ModalScreen/set_interval); zero packages installed
  patterns:
    - "set_interval cadence wrapper: each tick bumps its run id and dispatches @work(exclusive=True, thread=True, group=...) in SEPARATE groups (mon-frontier/mon-full — exclusivity cancels by (node, group)); the tick callback itself NEVER scans; mount runs its own immediate kick so the first rows never wait 60s"
    - "launch-injection threading: expected_total + fallback_start land on the screen at sweep_launched time and thread through service.stats(root, expected_total=, fallback_start=) — the 11-04 seams, never screen-side derivation"
    - "ever-discovered vanish rule: an attached root the scan HAS listed that later vanishes detaches (row drops, cells empty, no stale marker); a just-attached root survives until its first discovery pass"

key-files:
  created:
    - tui/screens/monitor.py
    - tests/tui/test_pilot_monitor.py
  modified:
    - tui/app.py
    - tui/screens/nav.py
    - tui/screens/run_config.py
    - tui/styles.tcss
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_selection_custom.py

key-decisions:
  - "NAV_PLACEHOLDER_SUFFIX/NAV_PLACEHOLDER_TOAST RETAINED with a zero-consumers annotation (the plan's executor's-choice row): deletion would touch strings.py + 4 test files for zero behavior change, and the defensive branches in nav.py/app.py still consume them syntactically — recorded here per the plan's requirement"
  - "The [f]/[t] keycap labels project from their landed modal-title constants (MON_FAILURES_TITLE.split(' (')[0] = 失败清单; MON_LOG_TITLE.split(' — {')[0] = 日志尾随) — the 11-06 keycap-budget precedent: no standalone 4-CJK constants exist in the frozen 99 and additions are tripwire-locked; the projection adds zero copy"
  - "The stats-line ETA field composes with the frozen ≈-carrying line constants by stripping format_eta's ≈ prefix for numeric forms and dropping the line's stray ≈ before the pending/none degradation copy (never a double marker, never new copy)"
  - "build_monitor_screen returns ONE cached instance (unlike the other rebuild-per-nav factories): attach state + the D-13 launch injections are session state — navigating away and back must never drop the attached sweep; re-mount re-composes from the surviving state"
  - "The [a]-invalid rendering rides PathInputModal's numbered-problem row with the MON_ATTACH_INVALID_TOAST copy (the never-silent contract); the manual-root grace rule distinguishes just-attached (survives) from ever-discovered-then-vanished (detaches)"
  - "Textual 8.2.8 probes pinned in code comments: a modal's self.screen IS the modal (the parent screen is passed into FailuresModal, never looked up); MessagePump._task clobbers a same-named field (renamed _task_key); a focused DataTable consumes its own enter (row_selected is the drill chokepoint — the data_manager idiom)"
  - "The re-run seeds fan out from the attached sweep's own discovered seed set (sorted union of cell rows, fallback [42]) at the sweep's own root with default peft/variant lanes — a from-failures enumeration is failure-pairs-only by construction (D-11), so no E2' gate applies"

patterns-established:
  - "tolerant cadence workers: the service calls inside the mon-full/mon-frontier workers are try/except-wrapped (BLE001 noqa, the app.py idiom) — a service that throws beyond the loader's tolerance renders the last-known-good, never crashes the console (T-11-07-02)"
  - "cadence proof without sleeps: the Pilot tests invoke the tick callbacks directly and assert the fake's call counters advanced (the interval wiring itself is Textual's tested set_interval); the responsiveness proof blocks a fake scan on a threading.Event and asserts presses still open chrome (T-11-07-04)"

requirements-completed: [MON-01, MON-02, MON-03, MON-04, MON-05, LNC-02]

coverage:
  - id: D1
    description: "Screen shell + discovered pane + cell table + stats line + cadence + slot-5 promotion (Task 1)"
    requirement: MON-01
    verification:
      - kind: integration
        ref: "tests/tui/test_pilot_monitor.py lane 1 (10 tests): both-grid compose incl. the 80-col scale-column drop; three D-03 states + counts; the progress-bar grammar (12/36 -> 3 filled cells) + the unknown-total copy; per-seed glyphs incl. ⊘ + curve mini-counts ⠋ 1/3; the three stats-line variants verbatim + the pending-ETA degradation; the resume note on the title row; the cadence proof (mount kick + tick callbacks + counters + timers armed + no zombie mon-* workers after unmount); zero-Chinese lock; tests/tui/test_pilot_nav_shell.py slot-5 assertions (bare 5 任务监控, digit-5 switch, no placeholder class anywhere); test_pilot_selection_custom nav tuple extended"
        status: pass
  - id: D2
    description: "Interactions — attach, cell detail, [f] + gated re-run, [t], [a], [r] (Task 2)"
    requirement: MON-03
    verification:
      - kind: integration
        ref: "lane 2 (11 tests): enter moves ◆ + rebinds (per-root fakes); invalid [a] keeps the modal with the toast row + never attaches; valid [a] adds + persists + attaches; cell detail (full keys, fraction lines, record fields VERBATIM incl. metrics dict); [f] rows + verbatim error drill + the empty copy; [r] rerun -> ConfirmModal -> env preflight -> launch_from_failures with root/sweep_failures.json + the sweep's own seeds -> toast + auto-attach; the env-block path renders the SAME EnvBlockModal with launch never called; [t] lines + dim tee line + esc stops the tail; no-tee renders MON_LOG_UNAVAILABLE with ZERO tail reads; [r] rescan toast with the count; the 68-char-key backstop (in-cell ellipsis, full key in detail)"
        status: pass
  - id: D3
    description: "D-13 integration + degradation sweep + responsiveness + full gates (Task 3)"
    requirement: MON-04
    verification:
      - kind: integration
        ref: "test_pilot_run_config.py::test_launch_success_auto_navigates_to_monitor_attached (the confirmed launch -> active screen IS MonitorScreen with the root attached + expected total 3 + fallback start; q -> ExitModal with live counts 完成 1/3); lane 3 (6 tests): corrupt-record throw -> last-known-good + no crash; manifest-mid-write stays running (no finished flip); artifacts-only never renders ●; attached-root-deleted round trip (row drops, cells empty, no stale ◆); min-size guard round trip with the open failures modal; responsiveness while a fake full scan blocks on an Event (a press still opens the PathInputModal)"
        status: pass
      - kind: command
        ref: "make test 1471 passed (11-06 baseline 1443 + 28 new) + node:test 18/18; make lint All checks passed; make typecheck All checks passed"
        status: pass

duration: 62min
completed: 2026-10-13
status: complete
---

# Phase 11 Plan 07: Monitor Screen Summary

**The slot-5 任务监控 screen end-to-end over the 11-04 scanner — the D-09 worker cadence (2s frontier / 60s full, never an inline scan), three-state discovery with attach, the seed-column cell table with the five glyph states and curve mini-counts, the D-17 stats/ETA variants, [f] failures with the confirm-gated from-failures re-run through the same env gate as slot 4, [t] tee tailing with the designed no-tee state, [a]/[r], the D-13 launch→auto-nav integration, the extended q-intercept with live counts, and the degradation + responsiveness sweep — closing the phase with the SC1-5 ledger and the maintainer-authorized GB10 smoke procedure**

## Performance

- **Duration:** 62 min (05:06:50Z - 06:09Z)
- **Tasks:** 3 (TDD lane 1 strictly RED→GREEN; lanes 2-3 pinned behavior built in the same module write — the 11-06 lane-shape precedent)
- **Files:** 9 (2 created, 7 edited)

## What Was Built

### Task 1 — the shell + cadence + promotion (commits 6b785a0 RED, 2a5ae8c GREEN)

- `MonitorScreen` (NAV_SLOT 5): TopMenuBar → title bar (MON_SCREEN_TITLE + the right-aligned MON_SCAN_NOTE cadence note — standing chrome) → the discovered region (fixed height 5: title + header + ~2 rows, scrolls) → full-width rule → the cell region (flex; MON_CELLS_TITLE + the right-aligned resume note on its title row) → the 1-row stats line → BottomBar (`[enter]详情 [f]失败清单 [t]日志尾随 [a]附加 [r]重扫` in wireframe order).
- Discovered rows: the three states glyph-first (● dim / ○ muted / ◌ muted), root name, 规模 (`{m}×{t}×{s}` from the manifest via the backend's sweep_scale; drops at 80), progress (`{done}/{total}` + the 10-cell █· bar on running rows only; unknown total ⇒ MON_TOTAL_UNKNOWN), ETA cell (running only: ≈point / ≈lo–hi / 估算中…; finished ⇒ —). The attached row carries the ◆ accent (state-cell prefix at 120; appended after ETA at 80 — Color amendment 13).
- Cell rows: `{model}__{task}` keys, seed columns (`s{n}`), per-seed glyph states ◌/⠋/✓/✗/⊘ (glyph+word in wide cells, glyph-only at 80), curve mini-counts `⠋ {done}/{total}`, in-cell truncation with full keys in detail.
- The cadence (the plan's no-analog piece): `set_interval(2.0/60.0)` ticks that ONLY bump run ids and dispatch `@work(exclusive=True, thread=True, group="mon-frontier"/"mon-full")` workers (separate groups — the data_manager group-discipline note); run-id-tagged messages with stale-drop handlers; the mount kick runs the first full scan immediately; timers stop on unmount (Pilot-proven: no zombie mon-* workers).
- `MonitorServiceProtocol` + `MonitorBackend` over the frozen 11-04 scanner with the shared launcher's `live_sweeps()` injected into every scan; constructor injection for Pilot fakes. app.py: the monitor seams, the ONE cached factory, the nav branch. nav.py: slot 5 promoted.

### Task 2 — the interactions (commit 0f3e259)

- Attach (enter on a discovered row): ◆ moves, cells/stats/failures/logs rebind, the frontier target updates. `[a]`: PathInputModal — `add_manual_root` validates; invalid renders the MON_ATTACH_INVALID_TOAST copy inside the modal's problem row (never silent, never attached); valid adds + persists + attaches + toasts.
- Cell detail (enter on a cell row): full model/task keys, per-seed states, `frac_{f}: {state}` lines, and the run_record fields VERBATIM through the new `cell_record` tolerant seam (worker-read).
- `[f]`: the border-titled failures modal (rows `MON_FAILURE_ROW`, enter drills the verbatim error in a wrapped RichLog, empty ⇒ ✓ 无失败 cell); its `r` opens the independent ConfirmModal; confirm routes `launcher.launch_from_failures(root/sweep_failures.json, seeds, root)` AFTER the env preflight — a FAIL renders the SAME EnvBlockModal as slot 4 (reuse) and the launch provably never happens; success toasts + auto-attaches the re-run.
- `[t]`: the bounded RichLog tail refreshed on the 2s cadence while open (its own mon-logtail worker), the dim tee line naming the file; no tee (CLI-launched) renders MON_LOG_UNAVAILABLE and schedules NO refresh; esc stops the tail. `[r]`: immediate full rescan + the count toast.
- Three 8.2.8 probe findings pinned (see key-decisions); `LauncherServiceProtocol`/`LauncherBackend` gained `launch_from_failures`.

### Task 3 — integration + degradation + gates (commit ccc7c14)

- D-13: `app.sweep_launched(root, cells)` (called by the slot-4 launch-finished site after the toast) records the plan (`note_launch` → expected_total + fallback_start, the 11-04 stats seams), attaches, and posts `MonitorSwitchRequested` (the queue-forward precedent) whose async handler switches to the cached monitor screen. The q-intercept predicate extends to `live_sweeps() OR the attached sweep running`; the ExitModal message threads the monitor's live done/total (absent markers when unknown).
- The degradation sweep (all Pilot-green): corrupt-record throw → last-known-good; manifest-mid-write stays running; artifacts-only never ●; attached-root-deleted → row drops + cells empty + no stale ◆ (the ever-discovered rule); the min-size guard round trip with an open modal; the responsiveness proof (a fake scan blocked on a threading.Event while presses still open chrome — T-11-07-04).

## Verification Evidence

- `uv run --group dev --group tui pytest tests/tui/test_pilot_monitor.py tests/tui/test_pilot_nav_shell.py -q` → **25 passed** (lane-1 point).
- `uv run --group dev --group tui pytest tests/tui -q` → **874 passed** (the Task-2 gate point; includes the nav-shell + selection-custom edits).
- `uv run --group dev --group tui pytest tests/tui/test_pilot_monitor.py tests/tui/test_pilot_run_config.py -q` → **60 passed** (27 + 33; the Task-3 point).
- **`make test` → 1471 passed** (11-06 baseline 1443 + 28 new) + node:test **18/18**; **`make lint` → All checks passed**; **`make typecheck` → All checks passed** (transcript).
- TDD: lane 1 landed RED first (collection ImportError on the absent module — the 11-02/11-06 precedent), then GREEN. Lanes 2-3: the module landed as ONE write in Task 1's GREEN (the plan's own files list names the same module all three tasks edit), so their RED phases were vacuous — each lane's first run surfaced test-side and 8.2.8-semantics defects only (the 11-06 documented lane shape).

## The SC1-5 Goal-Backward Checklist (the phase ledger)

| SC (ROADMAP verbatim anchor) | Proven by | Test evidence (exact names) |
|---|---|---|
| **SC1** — full parameter set (seeds default 42,43,44, PEFT + alias preview, head/probe/curve + PROBE_INELIGIBLE hints, curve tiers, fairness subset, epochs/batch overrides, auto-GA `--effective_batch_size`) + separated directories + same-source dry-run preview with enumerated cell counts | 11-01 (variant aliasing), 11-02 (RunSpec/preview/dirs/parse), 11-06 Task 1 (the params pane + preview line + dirs) | `tests/test_sweep.py` (variant aliasing suite); `tests/tui/test_services_run_config.py` (preview/parse/resolve/persist); `tests/tui/test_pilot_run_config.py::test_params_defaults_render`, `::test_params_labels_shorten_at_80_columns`, `::test_preview_line_renders_and_updates_on_mark`, `::test_preview_modal_renders_argv_and_problems` |
| **SC2** — terraform-style gate: env preflight blocks with the reason, preview precedes explicit confirm, the E2' three-seed sweep additionally requires a typed phrase, the TUI cannot bypass | 11-02 Task 2 (verdict/phrase, spawner-silent refusal), 11-03 Task 2 (structural gate), 11-06 Task 2 (the modal states), 11-07 (the re-run re-enters the same gate) | `tests/tui/test_services_sweep_launcher.py` (refusal-before-spawn proofs); `tests/tui/test_pilot_run_config.py::test_gate_env_block_renders_reasons_verbatim`, `::test_gate_e2x_phrase_flow`, `::test_gate_e2x_three_consecutive_mismatches_stay_mismatched`, `::test_gate_problems_blocked_launch_never_called`; `tests/tui/test_pilot_monitor.py::test_rerun_env_block_renders_the_same_modal` |
| **SC3** — execution always a `run_sweep.py` subprocess (LIST argv + PYTHONUNBUFFERED=1 + start_new_session); exit = kill/detach/cancel; detached sweeps resume-safe to re-attach | 11-03 Task 1 (spawn/tee/exit triple), 11-06 Task 3 (ExitModal), 11-07 (re-attach + the extended predicate + live counts) | `tests/tui/test_services_sweep_launcher.py` (kwargs/killpg/detach outcome tests); `tests/tui/test_pilot_run_config.py::test_exit_enter_detaches_then_exits`, `::test_exit_k_kills_then_exits`; `tests/tui/test_pilot_monitor.py::test_degradation_artifacts_only_never_running_glyph` + smoke step 6 (the ⊘ resume proof) |
| **SC4** — monitor dashboard: cell-level states (queued/running/done/failed/skipped, seed-adjacent) via 2s/60s tolerant scans, done/total + current + elapsed stats, attach for CLI-launched sweeps, live failure list + confirmation-gated `--from-failures` re-run, bounded log tail with tee persistence, resume recognition from `trainer_state.json` | 11-04 (the entire data layer), 11-07 Tasks 1-2 (the screen) | `tests/tui/test_services_sweep_monitor.py` (42 tier-1 tests); `tests/tui/test_pilot_monitor.py::test_cell_table_per_seed_glyphs_and_curve_minicounts`, `::test_cell_table_curve_seed_renders_mini_counts`, `::test_cadence_dispatches_workers_and_stops_on_unmount`, `::test_stats_line_variants`, `::test_attach_via_enter_moves_marker_and_rebinds`, `::test_attach_path_invalid_keeps_modal_never_attaches`, `::test_rerun_confirm_routes_launch_from_failures_and_attaches`, `::test_log_tail_renders_lines_and_tee_line`, `::test_log_tail_no_tee_is_designed_unavailable`, `::test_degradation_corrupt_record_renders_last_known_good`, `::test_console_stays_responsive_while_scan_blocks` |
| **SC5** — the maintainer-authorized bounded smoke (1×1×1, 1 epoch) runs launch → monitor → failure-re-run end-to-end on GB10 while E2' demonstrably blocks; every capability reachable headless via CLI | 11-07 Task 3 (the procedure below + the parity note) | **maintainer-executed** (NOT CI, NOT executed by the executor — D-15 bounds this host to dev/test; the GB10 smoke is the authorization boundary): the procedure's steps 2-8; the fake-proven halves: `test_launch_success_auto_navigates_to_monitor_attached` (the launch→monitor→ExitModal chain) + `test_gate_e2x_phrase_flow` (the gate demonstrably holds) |

**Verdict: every SC row carries task(s) + exact test-name evidence (SC5's execution half is by design maintainer-run; its fake-provable halves are test-named above). No evidence-less rows.**

## The GB10 Bounded Smoke Procedure (maintainer-authorized at the execution boundary — D-15)

> NOT a CI task; NOT executed by the executor. GPU + the dnallm env are
> the maintainer's authorization boundary. Record outcomes in the phase
> VERIFICATION/UAT artifacts.

1. `make tui` on the GB10 host; open slot 4 (运行配置).
2. Mark exactly `plant-dnabert-6mer` (the smallest LOCAL model, 89M — one of only 2 on disk) and `iDNA_ABF_datasets__5mC` (the smallest trainable task of all 50: 2110/234/2344 rows, present, n_audit clean — 11-RESEARCH Area 1, verified over `pipeline/datasets_info.json`); seeds `42`; epochs 覆盖 `1`; PEFT none; 变体 none; a dedicated output root such as `./finetuned-smoke` (isolates the discovery story; either root works).
3. `[p]` preview: `干跑: 1 模型 × 1 任务 × 1 种子 = 1 cell`, argv verbatim.
4. `[enter]` gate: env preflight passes (dnallm/torch/cuda on this host); summary confirm `启动 1 模型 × 1 任务 × 1 种子 = 1 cell → …/finetuned-smoke`.
5. Launch → toast → **auto-nav to slot 5 attached** (D-13 — the new sweep is ◆-marked with the cell ⠋ then ✓); elapsed accrues; ETA shows 估算中… then a point (prior real run of this exact pair: 65.04s train_runtime, ~2-3 min wall at 1 epoch).
6. `q` → ExitModal → detach → relaunch the TUI → slot 5 rediscovers the root (churn or finished) → `[t]` tail works; `trainer_state.json` markers mean a re-launch of the same cell skips (⊘ + the resume note) — the resume proof.
7. Failure-re-run leg (optional inside D-15's bound): add `GUE__virus_species_40` (+5000 rows ≈ +2-3 min) or poison one cell (rename a dataset dir temporarily), watch it fail live in `[f]`, then `r`重跑失败 → confirm → the re-run launches and completes.
8. E2'-blocks proof: compose 62 × 50 × 3 (mark all + all + seeds 42,43,44) → `[enter]` → the E2' typed-phrase modal appears and a WRONG dirname leaves 确认 dead — the gate demonstrably blocks (do NOT type the matching phrase; do NOT launch the full sweep from this host — full sweeps run on other machines, D-15).
9. Seed 42 never collides with the existing seed_9527 markers (seed-scoped resume — verified in research).

**Headless-CLI parity note (SC5):** every capability the two screens expose remains reachable without the TUI via `pipeline/run_sweep.py` flags — `--models` / `--tasks` / `--seeds` / `--peft` / `--config-variant` / `--curve` / `--subset_file` / `--num_train_epochs` / `--effective_batch_size` / `--cache_dir` / `--from-failures` / `--dry-run` — plus `run_finetune.py` for single cells; the tee files (D-10) and the artifact tree are the plain-text record of everything the screens render.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Textual 8.2.8 semantics] A modal's `self.screen` is the modal itself**
- **Found during:** Task 2 GREEN (the [f] re-run test).
- **Issue:** `FailuresModal.action_rerun_failures` looked up `self.screen` for the parent monitor — inside a pushed modal that returns the MODAL, so the confirm never pushed.
- **Fix:** the owning `MonitorScreen` is passed into the modal constructor (never looked up); probe-pinned in the code comment.
- **Files modified:** tui/screens/monitor.py
- **Commit:** 0f3e259

**2. [Rule 1 - 8.2.8] `MessagePump._task` clobbers a same-named field**
- **Found during:** Task 2 GREEN (the detail title rendered an asyncio Task).
- **Issue:** `CellDetailModal._task` was silently overwritten by the framework's own pump-task attribute on mount.
- **Fix:** renamed `_task_key`; probe-pinned in the comment.
- **Commit:** 0f3e259

**3. [Rule 3 - Protocol consequence] `LauncherServiceProtocol` lacked `launch_from_failures`**
- **Found during:** Task 2's ty gate.
- **Issue:** the app passes the shared launcher (typed `LauncherServiceProtocol`) into the monitor screen whose seam expects the re-run method; ty flagged the mismatch.
- **Fix:** the protocol + `LauncherBackend` gained the delegating `launch_from_failures` (the adapter over the app-owned `SweepLauncher`, which already had it); the three launcher fakes extended.
- **Files modified:** tui/screens/run_config.py, tests/tui/test_pilot_nav_shell.py, tests/tui/test_pilot_run_config.py
- **Commit:** 0f3e259

### Implementation Notes (within the plan's own discretion)

- **TDD lane shape:** the screen module landed as ONE write in Task 1's GREEN (the plan's files list names the same module in all three tasks), so lanes 2-3's RED phases were vacuous — tests pin already-built behavior; documented rather than reverting modals to manufacture a RED (the 11-06 precedent).
- **NAV_PLACEHOLDER_* retained** (the plan's executor's-choice row) with a zero-consumers annotation — see key-decisions.
- **[f]/[t] keycap labels** project from the landed modal-title constants — see key-decisions.
- **First `make test` run's pytest tail was lost to output truncation and the tree then changed by one dead test line** (removed for a ty diagnostic); the gate re-ran once at the final tree: 1471 passed + 18/18. Both runs exited 0.
- **The ExitModal `k` path on a CLI-launched attached sweep** is a documented noop outcome (the TUI owns no handle to kill) — honest; detach/return behave normally.

## Threat Flags

None — every register entry landed as planned: T-11-07-01 (ticks dispatch workers only; the mount kick + tick callbacks are worker-dispatching, never inline), T-11-07-02 (the degradation sweep incl. the throw path with tolerant wrappers + the ever-discovered vanish rule), T-11-07-03 (the [r] re-run routes through env preflight + ConfirmModal; the env-block test asserts zero rerun calls), T-11-07-04 (the blocked-scan responsiveness Pilot), T-11-07-05 (unknown totals / 估算中… / — / the no-tee state are test-pinned designed renderings), T-11-07-06 (is_sweep_root/add_manual_root refusal — never attached, never persisted), SC vacuous (zero installs).

## Known Stubs

None — no placeholder values, no unwired data paths; every surface is behavior-backed by the 27-test Pilot suite. The GB10 smoke (SC5's execution half) is maintainer-run by design, not a stub.

## Self-Check: PASSED

- tui/screens/monitor.py, tests/tui/test_pilot_monitor.py — FOUND (created)
- 6b785a0, 2a5ae8c, 0f3e259, ccc7c14 — all ancestors of HEAD
- Deletion check: no tracked files deleted (diff --stat: 9 files, 3209 insertions, 54 deletions — the deletions are the nav-shell/selection-custom assertion lines this plan's edits replaced)
- Untracked scan: only the pre-existing .planning/.gsd-allow-shrink (present at spawn)
- Ledger: commits measured 4 (c190d07..ccc7c14), no uncommitted code changes

---
*Phase: 11-run-config-launch-gates-single-gpu-monitoring*
*Completed: 2026-10-13*
