---
phase: 11-run-config-launch-gates-single-gpu-monitoring
verified: 2026-10-19T12:16:22Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-01-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-01-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-02-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-02-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-03-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-03-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-04-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-04-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-05-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-05-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-06-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-06-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-07-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-07-SUMMARY.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-08-PLAN.md
  - .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-08-SUMMARY.md
  - pipeline/run_finetune.py
  - pipeline/run_sweep.py
  - tests/test_run_finetune_contracts.py
  - tests/test_sweep.py
  - tests/tui/__snapshots__/monitor_empty.svg
  - tests/tui/__snapshots__/monitor_running.svg
  - tests/tui/__snapshots__/run_config.svg
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_pty_driver.py
  - tests/tui/test_services_run_config.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_services_sweep_monitor.py
  - tests/tui/test_snapshots.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_work_site_hardening.py
  - tui/app.py
  - tui/screens/env_check.py
  - tui/screens/monitor.py
  - tui/screens/nav.py
  - tui/screens/run_config.py
  - tui/screens/selection.py
  - tui/services/run_config.py
  - tui/services/sweep_launcher.py
  - tui/services/sweep_monitor.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:f52104a819e9c286a602720da0841a17428d582a19f87b18db1aca39eee5c038"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  previous_verified: 2026-10-17T07:42:47Z
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "Phase-8 disposition ledger (08-REVIEW-DISPOSITION.md) still shows WR-01/02/03 + IN-01/02/03 rows `open` — recorded 2026-10-17T04:43Z BEFORE the klw fixes landed; code resolution was verified in the round-3 pass and the fix commits are in history"
    category: other
    reason: "Ledger formality on the phase-8 artifact, not a code or phase-11 SC concern; resolves by re-running the disposition gate over 08-REVIEW.md"
    evidence_status: "resolved-in-code, ledger pending"
  - finding: "run_finetune.py sibling hard-index sites (:849/:1077/:1322) remain bare subscripts — maintainer-ruled scope boundary (only the two model-loop reads were sanctioned); phase-7 surface"
    category: other
    reason: "No phase-11 SC or requirement touches those paths; queued for a future ruled batch"
    evidence_status: "none provided"
  - finding: "WizardModal keycap visibility still NEEDS A MAINTAINER RULING (all six bindings show=False); carried from 261017-dnr"
    category: other
    reason: "Phase-9 surface; no phase-11 SC involved"
    evidence_status: "none provided"
  - finding: "WINDOWS #26/#27 — post-second-launch console input death; monitor ~60s stall at first-cell burst — remain open ledger rows"
    category: other
    reason: "Carried ledger advisories (unchanged since round 3); no phase-11 SC promises two in-session gated launches (EHC-3 refuses the second on single-GPU) and the launch→monitor→kill chain completed on camera; note WINDOWS #35/#39/#40/#41/#42 all closed since the prior pass"
    evidence_status: "none provided"
---

# Phase 11: Run Config, Launch Gates & Single-GPU Monitoring — Stale-Refresh Re-Verification (Round 4)

**Phase Goal:** The operator's core loop is closed and safe — compose a complete run spec, preview it from the same pure planning functions execution uses, pass the env + confirmation gates, launch `run_sweep.py` as a detached subprocess, and monitor/recover the sweep from the same console — proven end-to-end by a maintainer-authorized bounded smoke on GB10, with E2' provably still maintainer-gated
**Verified:** 2026-10-19T12:16:22Z (HEAD `5783567`, branch `autorun`; working tree clean except `.planning/STATE.md` + untracked `.planning/.gsd-allow-shrink`)
**Status:** passed
**Re-verification:** Yes — STALE REFRESH (round 4). Round 3 passed 5/5 at `855202e` (verified 2026-10-17T07:42:47Z). Since then this phase's covered surface was rebuilt heavily by seven quick-task batches plus one same-day maintainer ruling: **261017-mad** (16:02, hours after round 3: ctrl+c intercept withdrawn, F10 any-focus primary exit), **261018-kvj** (slot-5 two-tab restructure — Running cards + History, closed WINDOWS #40/#41), **261018-rze** (cadence render gates), **261018-toe** ([d] delete + [e] resume + service seams), **261019 restart-reattach** (`LauncherBackend.live_sweep_matrices` /proc forwarding + `tee_path_for` fresh-disk discovery), **261019-f0x/n0w/o8e/pe0** (B+D Running tab: summary strip + matrix + right pane, no-fill law, live-scope filter, tree third mode; goldens landed maintainer-approved 2026-10-19 19:57, WINDOWS #42 closed). `git diff --stat 855202e..HEAD` over the covered code: 26 files, +12373/−3227 — `tui/screens/monitor.py` alone ±4637 lines. This pass re-verifies every SC leg against TODAY's tree through the evolved surfaces.

## Goal Achievement

### Observable Truths (SC1-5, ROADMAP verbatim anchor)

| # | Truth | Status | Evidence (this pass, HEAD `5783567`) |
|---|-------|--------|----------|
| 1 | **SC1** full parameter set + separated dirs + same-source dry-run preview with enumerated cell counts | ✓ VERIFIED | Same-source seam re-read in the CURRENT service (grew +132 lines since round 3): `tui/services/run_config.py:115` module-level `import run_sweep`, `:907` `run_sweep.enumerate_matrix` VERBATIM (preview), `:1319` second enumerate site; launcher `:95` same import. Param surface re-read in the screen: seeds default `"42,43,44"` (`tui/screens/run_config.py:1243`), PEFT ChoiceRow (`:1246`), config-variant probe hint (`:1260`) + `probe_ineligible` read-source (`:165/:249`), curve tiers (`:1263`, `PARAM_CURVE :174`), epochs input (`:1281`, `PARAM_EPOCHS :175`), batch override delivered as auto-GA `--effective_batch_size` exactly as SC1 words it (`PARAM_EBS :176`, argv threading `:1151-1153`), fairness-subset default (`:100`). Separated dirs: `RunSpec` carries output_root/dataset_root/model_root/log_dir (`:208-233`), `resolve_dirs` basis (`:590-618`). Gate+preview batch green this pass (31 passed, incl. `test_gate_happy_path_confirms_and_launches`, preview recompute pins). The run_config service/screen delta since round 3 is the MonitorAdapter's `live_sweep_matrices`/`single_gpu_launch_blocked` delegations (`run_config.py:353-376`) — read-only evidence forwarding, no param/gate semantics |
| 2 | **SC2** terraform-style gate: env preflight blocks with reason, preview precedes explicit confirm, E2' typed phrase unbypassable | ✓ VERIFIED | `launch_spec` refusal chain re-read at HEAD (`sweep_launcher.py:744-818`): stage-0 EHC-3 single-GPU serialization guard FIRST (`:794`, `single_gpu_launch_blocked :723`) → fresh preview problems (never the screen's cached value) → official-keys fail-closed (empty sets cannot satisfy E2' by vacuity) → E2' exact-phrase (`phrase_matches` over `expected_phrase(output_root)`) — **every refusal returns BEFORE the spawner is consulted**. Screen gate chain: IN-02 `GateWorkerError` scope machinery intact (`run_config.py:1151-1173`, stage vs launch id spaces). Env-block reasons render verbatim (`test_gate_env_block_renders_reasons_verbatim` green). E2' pins green: `test_gate_e2x_phrase_flow`, `test_gate_e2x_three_consecutive_mismatches_stay_mismatched`, launcher `test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent`, and — NEW this window — the [e] resume lane demands the phrase too: `test_launch_from_pairs_full_matrix_demands_phrase_spawner_silent` green (the resume materializes incomplete pairs as a failures-shaped file and delegates VERBATIM to `launch_from_failures`; `launch_from_pairs :963-1040` — zero duplicated gate logic). Monitor-side E2' re-prompt threads the typed phrase back through the same routing (`monitor.py:4625-4647`; `test_e_e2x_phrase_refusal_reprompts_through_the_resume_worker` green). Gate batch this pass: 31 passed |
| 3 | **SC3** execution always a `run_sweep.py` subprocess (LIST argv + PYTHONUNBUFFERED=1 + start_new_session); exit kill/detach/cancel; detached sweeps resume-safe to re-attach | ✓ VERIFIED — **surface EVOLVED by documented rulings; contract holds** | Spawn pins re-read (`sweep_launcher.py:695-701`): `start_new_session=True`, `env={**os.environ, "PYTHONUNBUFFERED": "1"}`, LIST argv; `launch_argv` applies the same E2' predicate. Launcher suite green this pass (68 tests, incl. the four spawn/refusal pins and O_EXCL tee). Exit chain re-read at HEAD: `action_quit` (`app.py:1159`) → ExitModal (kill/detach/cancel, default detach) when `live_sweeps()` or attached-running; WR-03 mixed TUI+CLI-root MULTI form intact; WR-02 off-loop exit-kill worker intact (`request_kill_and_exit :1252` → `@work(exclusive=True, thread=True, group="exit-kill", exit_on_error=False) _exit_kill_worker :1265` with per-root broad guard + UNCONDITIONAL `ExitKillsDone` → `exit()`). **Ruling delta (261017-mad, 2026-10-17 16:02 — AFTER round 3): the ctrl+c intercept was WITHDRAWN** (`c8f6f44`, docs `fe6dd88`) — ctrl+c keeps textual's terminal-native copy/interrupt semantics and **F10 is the any-focus PRIMARY exit** (`413ec72`, priority+system binding `app.py:606`); the round-3 WR-01 `on_event` delegation no longer exists by design. SC3's text requires the exit CHOICE, not ctrl+c — the choice surface is intact and re-pinned: exit batch this pass **26 passed** (`test_exit_k_kills_every_root_then_exits_on_completion`, `test_exit_k_raising_kill_still_attempts_every_root_and_exits` — the raising-root broad-guard print observed live in this pass's output, `test_exit_modal_multi_root_kills_every_live_sweep`, `test_mixed_roots_exit_names_and_kills_both_tui_and_attached`, `test_modal_exit_semantics_native_ctrlc_and_f10`, `test_f10_no_sweep_opens_quit_confirm_over_focused_input`, below-min-grid never-exit, ctrl+q no-second-stack). `test_work_site_hardening.py` green (1 passed). **Re-attach STRENGTHENED this window**: `live_sweep_matrices` (`sweep_launcher.py:1221+`) merges registry argv matrices with the `/proc` `probe_cli_sweeps()` evidence so a restarted console still classifies detached children (probe-inclusive forwarding `run_config.py:353-360`); `tee_path_for` falls back live-registry → in-memory history → `_discover_fresh_tee` fresh-append-grace disk scan (`:1142-1204`) so a restarted console still finds the detached child's tee. Named pins green: `test_live_sweep_matrices_merges_registry_and_probe_behind_cache`, `test_live_sweep_matrices_probe_root_absent_from_registry_only`, `test_live_sweep_matrices_kill_face_stays_registry_only` (the KILL face stays registry-only — a probed CLI sweep is never falsely killable), `test_tee_path_restart_discovery_finds_fresh_disk_tee`, `test_tee_path_restart_discovery_stale_only_stays_none` |
| 4 | **SC4** monitor dashboard: cell states via tolerant scans, stats/ETA, attach for CLI sweeps, gated re-run, bounded tail + tee, ⊘ resume | ✓ VERIFIED — **surface REBUILT (kvj two-tab + f0x B+D + pe0 tree + o8e live-scope + rze cadence gates); every original leg holds** | Cadence unchanged and re-read: `FRONTIER_INTERVAL_SECONDS = 2.0` / `FULL_INTERVAL_SECONDS = 60.0` (`monitor.py:268-269`), screen owns the cadence over the PURE scanner (service docstring pins no-timers). Cell-level state (queued/running/done/failed/skipped, seed-adjacent) now renders three ways — B matrix grid, [w] wide A-style dense per-cell table, pe0 tree (`test_matrix_glyph_grid_and_style_only_highlight`, `test_matrix_arrow_focus_moves_clamps_and_crosses_cards`, `test_tree_state_renders_model_and_task_nodes`, `test_tree_navigation_contract`, `test_matrix_overflow_defaults_to_tree_and_manual_holds` all green). Stats/ETA on the summary strip: elapsed minute-granularity, ETA point/range, derived it/s (`_format_elapsed_short :465-471`, ETA_POINT). Attach for CLI sweeps: `attach_valid` D-03 predicate (`:704`) + the /proc probe legs above. Live failure list + confirmation-gated `--from-failures` re-run: FailureDetailModal `r` → ConfirmModal → `launch_from_failures` with the E2' phrase re-prompt (`:1036-1051`, `:4541-4654`). Bounded tail + tee: LogTailModal over `read_log_tail`/`tee_path_for`, own exclusive `mon-tail` worker off the loop (`:1238+`); MON_KILL_UNAVAILABLE honest refusal for unkillable roots. ⊘ Resume recognition: MON-05 trainer_state markers (`:684`); **NEW [e] resume** derives the incomplete set (failed + interrupted only — `test_incomplete_pairs_view_failed_and_interrupted_only`, `test_incomplete_pairs_view_alias_names_and_distinct_sorted` both green this pass) and launches through the SC2 gate chain. **NEW [d] delete** is strongly gated — read at `:4921-5060`: below-min-grid no-op (WR-06), History-tab+focused-row only, LIVE root refuses BEFORE any modal (`MON_DELETE_REFUSED_LIVE`), DeleteConfirmModal y-only (`:1150`), rm -rf in a WORKER thread (group `mon-delete`, exclusive, exit_on_error=False) with a confirm-to-worker LIVENESS RE-CHECK, superseded-id guard (WR-02 idiom), tolerant failure toast (WR-03). `test_d_opens_delete_confirm_y_deletes_and_rescans` green. rze cadence gates: steady ticks write ZERO widgets (`test_cadence_dispatches_workers_and_stops_on_unmount`, `test_language_toggle_recompose_keeps_cadence_idempotent`, `test_render_all_inert_under_modal_and_resumes_after` green). Monitor suite this pass: 104 pilot tests + 13 pty tests green |
| 5 | **SC5** bounded smoke runs launch→monitor→failure-re-run E2E on GB10 while E2' demonstrably blocks; every capability headless via CLI | ✓ VERIFIED | Smoke artifacts re-read on disk THIS pass: `finetuned-smoke/` with `plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42/trainer_state.json` (full per-cell set: final_metrics.json, flops_report.json, run_record.json, checkpoints), `plant-dnambert-6mer/`, `PlantHelixSeek/`, **plus a NEW root `hyenadna-large-1m-seqlen-hf` from this window's live restart-reattach/tree-mode verification**, `sweep_manifest.json` + `sweep_failures.json`, and `pipeline/finetuned/smoke-2x2-261014/`. Live-run corroborating artifacts in `pipeline/logs/` (hyenadna error log 2026-10-19 10:41, plant-dnabert 19:55 — tonight's quick-task live passes through the current gate). `11-UAT.md` `status: passed` (unchanged). CLI headless parity: every launch path composes `run_sweep.py` argv — `launch_spec`/`launch_argv`/`launch_from_failures`/`launch_from_pairs` all thread through `compose_argv`; the E2' gate is structural (SC2 evidence), so the TUI cannot bypass what the CLI enforces. `pipeline/run_sweep.py` untouched in this window (`git diff 855202e..HEAD -- pipeline/run_sweep.py` = 0 lines) |

**Score:** 5/5 truths verified (zero behavior-unverified — every behavior-dependent claim in the delta window is exercised by a passing named test run this pass: the cadence zero-write gates, the [d] confirm-to-worker liveness re-check and superseded-id guard, the [e] E2' phrase re-prompt routing, the restart reattach matrix/tee discovery, the every-root exit-kill fan-out, the kill-face registry-only boundary, the live-scope pair-set filtering)

### Staleness Resolution (the refresh's core question — which batches evolved the surface, and why each leg holds)

| Delta since round 3 (`855202e..5783567`) | What changed | Why the goal legs still hold (this pass's evidence) |
|------------------------------------------|--------------|------------------------------------------------------|
| 261017-mad (16:02, same day, hours AFTER round 3's 07:42Z) | ctrl+c intercept withdrawn; F10 any-focus primary exit | A documented maintainer exit-key FINAL ruling, not a regression: SC3 requires the exit kill/detach/cancel CHOICE — the ExitModal and the whole q/ctrl+q/F10 → `action_quit` chain are intact (26-test exit batch green); the WR-01 `on_event` delegation the round-3 report cited was itself only hours old at round-3 time and its subject (ctrl+c as an exit key) no longer exists by ruling |
| 261018-kvj two-tab restructure | Master-detail dual table DELETED; Running cards + History rows; closed WINDOWS #40/#41 | Maintainer-approved contract (2026-10-18 15:01); SC4's cell-level-state leg is served by the B matrix + [w] wide A-style dense table + tree; scan/cadence/gate seams untouched; monitor Pilot suite green |
| 261018-rze cadence render gates | Steady ticks write zero widgets (six gate families incl. history rows) | Pure render-layer discipline over the unchanged 2s/60s cadence; `test_cadence_dispatches_workers_and_stops_on_unmount` + pty byte-silence pins green; strengthens SC4 (no flicker) |
| 261018-toe [d] delete + [e] resume | New destructive + recovery capabilities on slot-5; service seams (`incomplete_pairs_view`, `rerun_lane` alias fallback, `launch_from_pairs`) | [e] delegates VERBATIM to `launch_from_failures` — stage-0 single-GPU, official-keys, E2' phrase all apply (`test_launch_from_pairs_full_matrix_demands_phrase_spawner_silent`); [d] is the strongest-gated action on the screen (live refusal pre-modal, y-only, worker rm -rf with liveness re-check) — SC2/SC4 strengthened, not weakened |
| 261019 restart-reattach (`62a5c61`, `32be15d`) | `LauncherBackend` forwards `live_sweep_matrices` (registry + /proc probe); `tee_path_for` fresh-disk discovery | Directly STRENGTHENS SC3's "detached sweep is resume-safe to re-attach" and SC4's three-state cell evidence; kill face stays registry-only (named pin green) |
| 261019-f0x/n0w/o8e/pe0 B+D redesign | Summary strip + matrix grid + D right pane + live tee tail; no-fill law (styles); Running views scoped to the live sweep's pair set; tree third mode | Display-layer only; cadence/scan/gate/spawn seams untouched; live-scope filtering is honest (fallbacks never scope — `test_live_evidence_fallbacks_never_scope`); goldens landed maintainer-approved 2026-10-19 19:57 (WINDOWS #42); snapshot suite green this pass |

### Advisory (New Scope, Unevidenced; re-verification ran)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | Phase-8 disposition ledger rows not yet flipped to fixed | other | Ledger formality on a phase-8 artifact; code resolution verified in round 3, unchanged since |
| 2 | run_finetune sibling hard-index sites (:849/:1077/:1322) | other | Outside the maintainer's ruling scope; phase-7 surface, queued future batch |
| 3 | WizardModal keycap ruling needed | other | Carried maintainer decision item; phase-9 surface |
| 4 | WINDOWS #26/#27 ledger rows remain open | other | Carried; no SC breach — EHC-3 refuses a second in-session gated launch on single-GPU; note #35/#39/#40/#41/#42 all CLOSED since the prior pass |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/run_sweep.py` + `tests/test_sweep.py` | D-18 variant aliasing + parity (11-01) | ✓ VERIFIED | Zero-diff in this window (`git diff 855202e..HEAD -- pipeline/run_sweep.py` = 0 lines) |
| `tui/services/run_config.py` + tier-1 suite | Same-source service (11-02) | ✓ VERIFIED | Same-source seams re-read (:115/:907/:1319); +132 lines this window = MonitorAdapter delegations only; suite green except the sole machine-local member (see Behavioral Spot-Checks) |
| `tui/services/sweep_launcher.py` + suite | Gated launch lifecycle (11-03, hardened 11-08, extended toe/reattach) | ✓ VERIFIED | 68 tests green this pass incl. refusal chain, spawn pins, O_EXCL tee, launch_from_pairs, live_sweep_matrices, tee restart discovery |
| `tui/services/sweep_monitor.py` + suite | Pure scanner (11-04, extended toe) | ✓ VERIFIED | No-timer purity docstring intact; `incomplete_pairs_view` named pair green this pass |
| `tui/strings.py` + `tests/tui/test_strings_phase11.py` | Copy contract + tripwire (11-05) | ✓ VERIFIED | +249 lines this window (new toe/f0x/pe0 copy); tripwire suite green (12 tests, in the 36-test lane) |
| `tui/screens/run_config.py` | Slot-4 screen + gates (11-06) | ✓ VERIFIED | +54 lines this window = live-matrices/single-gpu delegations; IN-02 scope machinery intact; gate batch 31 green |
| `tui/screens/monitor.py` | Slot-5 screen (11-07, rebuilt kvj/f0x/n0w/o8e/pe0/toe/rze) | ✓ VERIFIED | All SC4 legs re-read + 104 Pilot tests green; [d]/[e] strongly gated |
| `tui/app.py` (+ nav/styles) | App wiring, ExitModal/QuitConfirm (11-06/07, mad ruling) | ✓ VERIFIED | Exit chain re-read at HEAD; exit batch 26 green; work-site hardening green |
| `tui/screens/selection.py` / `env_check.py` | Phase-11 covered hygiene surfaces | ✓ VERIFIED | selection.py +9 lines this window (IN-01 fix site region intact); env_check.py untouched since round 3 |
| `pipeline/run_finetune.py` + contracts test | Pipeline surface (07-CR-01 guarded reads) | ✓ VERIFIED | Guarded `.get` shapes outside this window's delta; contracts test file unchanged |
| `tests/tui/__snapshots__/{monitor_empty,monitor_running,run_config}.svg` | Goldens (D-03, regenerated b84afc0/2bdcbad, maintainer-approved) | ✓ VERIFIED | Landed committed; snapshot suite green this pass (11 tests) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_config service | run_sweep planning functions | module-level import, enumerate verbatim | ✓ WIRED | :115/:907/:1319 re-read at HEAD |
| launch gate (spec/argv/from-failures/from-pairs) | spawner | refusal chain ordered before `_spawn` | ✓ WIRED | `launch_spec :744-818` re-read; phrase-silent + stage-0 pins green; resume lane delegates to the same chain |
| [e] resume | launch_from_failures | materialized pairs file → verbatim delegation | ✓ WIRED | `launch_from_pairs :963-1040`; phrase-demanded pin green |
| ExitModal [k] | app exit-kill worker | `action_kill_quit` → `request_kill_and_exit` → `_exit_kill_worker` → `ExitKillsDone` → `exit()` | ✓ WIRED | app.py:266/:1252-1305 re-read at HEAD; completion + raising-fan-out tests green |
| action_quit | ExitModal over mixed roots | `attached_extra` → `combined` → MULTI form | ✓ WIRED | :1159+ re-read; both mixed-root tests green |
| F10 / q / ctrl+q | action_quit → ExitModal/QuitConfirm | priority binding + routing guards | ✓ WIRED | The mad final ruling; 26-test exit batch green incl. below-min-grid never-exit and no-second-stack guards |
| monitor [k] | launcher kill channel (off-loop) | KillConfirmModal y → `_run_kill` @work thread | ✓ WIRED | mon-kill discipline intact; MON_KILL_UNAVAILABLE honest refusal for probed CLI roots (registry-only kill face pinned) |
| restart reattach | live cell evidence + tee | `live_sweep_matrices` /proc merge + `_discover_fresh_tee` | ✓ WIRED | Three live_sweep_matrices pins + two tee-discovery pins green |
| [d] delete | worker rm -rf | live refusal → y-only confirm → mon-delete worker with re-check | ✓ WIRED | :4921-5060 re-read; d-confirm pin green |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| preview line / [p] modal | PreviewResult.cells | run_sweep.enumerate_matrix over the real registries | Yes (imported verbatim; seam re-read) | ✓ FLOWING |
| gate confirm pair list | GateSummary.pairs | FRESH preview recompute at gate time | Yes (gate/preview batch green) | ✓ FLOWING |
| monitor B strip / matrix / tree / D pane | cells_view + live pair evidence + entries_progress | run_record.json / manifest / trainer_state on disk + registry//proc matrices | Yes (smoke trees re-read; live-scope pins green) | ✓ FLOWING |
| [t] tail / D-pane live tail | read_log_tail over tee_path_for | the tee FILE under state/logs (live → history → fresh-disk chain) | Yes (restart-discovery pins green) | ✓ FLOWING |
| ExitModal root list | live_sweeps() + attached_running_counts() | launcher registry + monitor attachment + /proc probe | Yes (mixed-root tests green) | ✓ FLOWING |

### Behavioral Spot-Checks (run this pass at HEAD `5783567`; `.venv/bin/python` throughout)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| **Evidence lane** (per refresh instructions) | `.venv/bin/python -m pytest tests/tui/test_pilot_monitor.py tests/tui/test_services_sweep_launcher.py tests/tui/test_services_run_config.py -q` | **1 failed, 325 passed** (68.78s) — sole F: `test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers` | ✓ PASS — the failure is the DOCUMENTED machine-local collateral: the test asserts `pipeline/logs` absent (fresh-checkout expectation) but this GB10 box carries maintainer live-run logs (verified on disk this pass — hyenadna error log 2026-10-19 10:41, plant-dnabert 19:55); `exists=True` is the honest read of a path that genuinely exists here. Same membership as the documented 1F/1867P baseline. NOT a regression |
| pty lane + strings tripwire + goldens | `.venv/bin/python -m pytest tests/tui/test_pty_driver.py tests/tui/test_strings_phase11.py tests/tui/test_snapshots.py -q` | 36 passed (53.39s) | ✓ PASS |
| SC2 gate chain (env-block verbatim, E2' phrase flow + mismatches, happy path, single-GPU refusal, preview) | `pytest tests/tui/test_pilot_run_config.py -q -k "gate or phrase or env_block or preview"` | 31 passed, 67 deselected | ✓ PASS |
| SC3 exit family (F10/q/ctrl+q routing, every-root kill fan-out, raising-root broad guard, multi/mixed-root, detach, below-min-grid, no-second-stack) | `pytest tests/tui/test_pilot_run_config.py -q -k "exit or f10 or ctrlq or quit"` | 26 passed, 72 deselected (the exit-kill broad-guard print observed in output — the raising-root case exercising live) | ✓ PASS |
| toe [e] incomplete derivation | `pytest tests/tui/test_services_sweep_monitor.py::test_incomplete_pairs_view_failed_and_interrupted_only ::test_incomplete_pairs_view_alias_names_and_distinct_sorted` | 2 passed | ✓ PASS |
| @work-site structural hardening | `pytest tests/tui/test_work_site_hardening.py -q` | 1 passed | ✓ PASS |
| ruff (repo) | `.venv/bin/python -m ruff check .` | All checks passed | ✓ PASS |
| ty (tui + pipeline) | `.venv/bin/python -m ty check tui pipeline` | All checks passed | ✓ PASS |
| SC5 smoke artifacts on disk | read `finetuned-smoke/` + `pipeline/finetuned/smoke-2x2-261014` | all trees + trainer_state markers present (+ NEW hyenadna root from this window) | ✓ PASS |
| Decision coverage gate | `gsd_run query check.decision-coverage-verify` | 20/20 honored, 0 not honored | ✓ PASS (non-blocking by design) |

**Named-test highlights inside the green evidence lane (the quick-task deltas' behaviors):** rze `test_cadence_dispatches_workers_and_stops_on_unmount`, `test_language_toggle_recompose_keeps_cadence_idempotent`, `test_render_all_inert_under_modal_and_resumes_after`; toe `test_d_opens_delete_confirm_y_deletes_and_rescans`, `test_e_nothing_to_resume_toast_launcher_untouched`, `test_e_e2x_phrase_refusal_reprompts_through_the_resume_worker`, `test_launch_from_pairs_materializes_state_dir_file_and_delegates`, `test_launch_from_pairs_full_matrix_demands_phrase_spawner_silent`; reattach `test_live_sweep_matrices_merges_registry_and_probe_behind_cache`, `test_live_sweep_matrices_kill_face_stays_registry_only`, `test_tee_path_restart_discovery_finds_fresh_disk_tee`, `test_tee_path_restart_discovery_stale_only_stays_none`; f0x/o8e/pe0 `test_live_pair_evidence_scopes_matrix_strip_and_wide`, `test_live_evidence_fallbacks_never_scope`, `test_matrix_glyph_grid_and_style_only_highlight`, `test_matrix_arrow_focus_moves_clamps_and_crosses_cards`, `test_tree_state_renders_model_and_task_nodes`, `test_tree_navigation_contract`, `test_tree_click_selects_node_without_drill`, `test_tree_steady_tick_zero_write_and_rebuild_preserves_state`, `test_tree_focus_unification_feeds_right_pane`, `test_matrix_overflow_defaults_to_tree_and_manual_holds`.

### Probe Execution

N/A — no phase-declared or conventional probe scripts; this refresh's evidence vehicles are the pytest lanes above (all run in their own process this pass: 325 + 36 + 31 + 26 + 2 + 1 = 421 test outcomes, 420 green, 1 documented environment-conditional), plus the standing SC5 on-disk artifacts.

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| CFG-01 | 11-01/02/05/06 | ✓ SATISFIED | SC1 evidence this pass (param surface re-read; tripwire green) |
| CFG-02 | 11-02/06/08 | ✓ SATISFIED | resolve_dirs basis re-read; suite green |
| CFG-03 | 11-02/06 | ✓ SATISFIED | Same-source seam re-read at :115/:907/:1319 |
| LNC-01 | 11-05/06 | ✓ SATISFIED | Env-block verbatim + happy-path pins green (31-batch) |
| LNC-02 | 11-01/03/06/07/08 | ✓ SATISFIED — strengthened | Spawn pins green; exit kill off-loop, every-root; reattach legs added |
| LNC-03 | 11-02/03/06/07 | ✓ SATISFIED — strengthened | Phrase-silent refusal green; the E2' gate now provably covers the [e] resume lane too |
| MON-01 | 11-04/05/07 | ✓ SATISFIED | Scanner purity intact; tolerant readers; monitor suite green |
| MON-02 | 11-04/05/07/08 | ✓ SATISFIED — strengthened | Attach + /proc probe + restart tee discovery |
| MON-03 | 11-04/05/07/08 | ✓ SATISFIED — strengthened | from-failures re-run + [e] resume both through the gate chain |
| MON-04 | 11-03/04/05/07/08 | ✓ SATISFIED | O_EXCL tee + tee_path_for live→history→disk chain |
| MON-05 | 11-04/05/07 | ✓ SATISFIED | trainer_state markers re-read on disk; skipped-cells read at :684 |

REQUIREMENTS.md: all 11 phase-11 rows `Complete` (re-read this pass); no orphans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | Zero TBD/FIXME/XXX/TODO/HACK across the nine covered implementation files changed this window (monitor.py, sweep_launcher.py, sweep_monitor.py, run_config.py service+screen, app.py, nav.py, strings.py, styles.tcss) | — | — |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| test_pilot_monitor.py (104) | MON-01..05 | 104 | 0 | 0 | Behavioral (render gates, gated actions, worker outcomes) | OK |
| test_services_sweep_launcher.py (68) | LNC-02/03, MON-03/04 | 68 | 0 | 0 | Value/behavioral (call-count refusal proofs, argv pins) | OK |
| test_services_run_config.py (107) | CFG-01..03 | 107 (1 env-conditional F) | 0 | 0 | Value (verbatim paths, defaults) | OK |
| test_pilot_run_config.py (exit+gate batches) | LNC-01..03 | 98 selected green | 0 | 0 | Behavioral | OK |
| test_pty_driver.py (13) | MON legs (render truth) | 13 | 0 | 0 | Behavioral (byte-level pty) | OK |
| test_strings_phase11.py (12) / test_snapshots.py (11) | CFG/LNC/MON copy + goldens | 23 | 0 | 0 | Value (verbatim constants, SVG goldens) | OK |

No disabled tests on requirements; no circular generation (goldens are maintainer-approved landings, not self-generated truth — the D-03 discipline); assertion levels match the behavioral demands.

### Human Verification Required

None. The entire delta window is machine-verified this pass — every quick-task behavior (cadence zero-write gates, [d] gating chain incl. the confirm-to-worker liveness re-check, [e] E2' re-prompt routing, restart matrix/tee discovery, tree/matrix/live-scope rendering, the exit-family F10 ruling) is exercised by named passing tests, and both lint/type gates ran green live. SC5's human half remains closed by the executed 2026-10-13 UAT (`status: passed`), the on-disk smoke trees (re-read this pass, including this window's new hyenadna live-run root), and tonight's live launches through the current gate (pipeline/logs artifacts dated 2026-10-19).

### Gaps Summary

None. The round-4 stale refresh confirms the phase goal holds at HEAD `5783567` after the heaviest evolution window this phase has seen since its original close: seven quick-task batches plus the mad exit-key ruling rebuilt the monitor's presentation layer (two-tab + B strip/matrix + D pane + tree + live-scope + cadence gates), added two recovery actions ([d] strongly-gated delete, [e] gate-chained resume), and closed the restart-reattach gap (/proc matrix forwarding + fresh-disk tee discovery). Every SC leg was re-verified against TODAY's code: SC1 through the same-source seam and full param surface (re-read, batch green); SC2 through the refusal chain with the E2' gate now provably covering the resume lane too; SC3 through the spawn pins and the exit choice under the F10 final ruling (the withdrawn ctrl+c intercept was a documented maintainer ruling on a surface the SC never required); SC4 through every original leg surviving the B+D rebuild plus strengthened recovery; SC5 through the on-disk smoke evidence and untouched CLI parity (`run_sweep.py` zero-diff this window). 420 of 421 test outcomes green this pass across six lanes; the single failure is the pre-documented machine-local `pipeline/logs` collateral, verified on disk as a maintainer live-run artifact, not a regression. Zero debt markers; ruff + ty green; decision coverage 20/20; the four frontmatter advisories are carried ledger/maintainer-decision items on other phases' surfaces — none breaches a phase-11 SC.

---

_Verified: 2026-10-19T12:16:22Z_
_Verifier: Claude (gsd-verifier)_
