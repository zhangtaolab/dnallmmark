---
phase: 11-run-config-launch-gates-single-gpu-monitoring
verified: 2026-10-17T07:42:47Z
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
covered_digest: "v3:sha256:b86dad995dfe1565fdaf066d4d02ed564a2e5c4455fee3ef12d5122d0ff98123"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  previous_verified: 2026-10-17T05:19:32Z
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "08-REVIEW-DISPOSITION.md ledger rows WR-01/02/03 + IN-01/02/03 still read `open` (recorded 2026-10-17T04:43Z, BEFORE the fixes landed 07:20-07:27Z) — the code resolution is verified this pass, but the disposition ledger awaits its gate re-run to flip the six rows to fixed"
    category: other
    reason: "Ledger formality on the phase-8 artifact, not a code or SC concern; the fix commits (06d2679/0d02e18) and their RED-first evidence are in history. Resolves by re-running the disposition gate over 08-REVIEW.md"
    evidence_status: "resolved-in-code, ledger pending"
  - finding: "run_finetune.py sibling hard-index sites (:849 probe-branch Model_name enumeration, :1077 row['Dataset_name'], :1322 row['length']) remain bare subscripts — recorded in the klw SUMMARY as deliberately outside the ruling's seven findings; a schema-legal minimal custom entry hitting those paths still raises KeyError"
    category: other
    reason: "Maintainer-ruled scope boundary (only the two model-loop reads were sanctioned); phase-7 surface, no phase-11 SC or requirement touches those paths; queued for a future ruled batch with its own AST pin"
    evidence_status: "none provided"
  - finding: "WizardModal keycap visibility still NEEDS A MAINTAINER RULING (all six bindings show=False — step-aware visibility would be a redesign); carried from 261017-dnr and re-raised by the klw batch's non-goals"
    category: other
    reason: "Phase-9 surface; showing them unconditionally would mislead (f/o step-1-only, u landed-state-only); the step-view copy carries the affordances; no phase-11 SC involved"
    evidence_status: "none provided"
  - finding: "WINDOWS #26 / #27 — post-second-launch console input death; monitor ~60s stall at first-cell burst"
    category: other
    reason: "Carried ledger advisories (unchanged by this batch); no SC promises two in-session gated launches (EHC-3 refuses the second on single-GPU) and the launch→monitor→kill chain completed on camera"
    evidence_status: "none provided"
---

# Phase 11: Run Config, Launch Gates & Single-GPU Monitoring — Micro Refresh Re-Verification (Round 3, post-klw)

**Phase Goal:** The operator's core loop is closed and safe — compose a complete run spec, preview it from the same pure planning functions execution uses, pass the env + confirmation gates, launch `run_sweep.py` as a detached subprocess, and monitor/recover the sweep from the same console — proven end-to-end by a maintainer-authorized bounded smoke on GB10, with E2' provably still maintainer-gated
**Verified:** 2026-10-17T07:42:47Z (HEAD `855202e` — code-identical to `1cb8512`; the interleaved commit is the docs-only phase-7 round-3 refresh; branch `autorun`, working tree clean except an untracked `.planning/` state file)
**Status:** passed
**Re-verification:** Yes — THIRD refresh (micro). Round 2 passed 5/5 at `ba0c8d6` (verified 2026-10-17T05:19:32Z). The delta on this phase's covered set since: quick-261017-klw — the maintainer's pre-closeout 08-review fix batch (`06d2679` exit-channel trio WR-01/02/03, `0d02e18` screen-hygiene trio IN-01/02/03, `6e331d3` 07-CR-01 guarded model-loop reads), all RED-first with the evidence table in the klw SUMMARY. Scope of this pass per the refresh instructions: verify the fix sites directly, re-check the SC standings through the fix-shaped surfaces (kill path now off-loop, mixed-root exit form, ctrl+c selection-delegation corner), confirm the EHC ruling tests intact, and adjudicate the round-2 advisories' resolution state. The full suite was NOT re-run (documented gates at this HEAD: 1F/1867P, the sole F being this phase's machine-local `test_storage_overview_defaults_mirror_real_consumers` member — re-run individually this pass and confirmed environment-conditional: it asserts `pipeline/logs` absent as on a fresh checkout, but this GB10 machine carries live-run logs; the service's `exists=True` is the honest read of a path that genuinely exists here; node 26/26; ruff+ty green).

## Goal Achievement

### Observable Truths (SC1-5, ROADMAP verbatim anchor)

| # | Truth | Status | Evidence (this pass, HEAD `855202e`) |
|---|-------|--------|----------|
| 1 | **SC1** full parameter set + separated dirs + same-source dry-run preview with enumerated cell counts | ✓ VERIFIED | The same-source seam is OUTSIDE the klw delta (`git diff --name-status ba0c8d6..1cb8512` over code: `tui/services/*` and `pipeline/run_sweep.py` untouched — the delta is exactly app.py, screens/{env_check,run_config,selection}.py, run_finetune.py + 4 test files) and re-read this pass: `tui/services/run_config.py:115` module-level `import run_sweep`, `:907` `run_sweep.enumerate_matrix` verbatim. Screen param surface untouched by the batch; strings.py zero-diff (`git diff ba0c8d6..1cb8512 -- tui/strings.py` = 0 lines — zero new strings, as the batch claims). Strings tripwire green this pass (10 passed). Goldens green (snapshot suite 11 passed; `tests/tui/__snapshots__/` zero-diff — zero SVG interaction) |
| 2 | **SC2** terraform-style gate: env preflight blocks with reason, preview precedes explicit confirm, E2' typed phrase unbypassable | ✓ VERIFIED — **IN-02 strengthens the gate's error hygiene** | The refusal chain in the LAUNCHER service is outside the delta and re-pinned green this pass: `test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent`, `test_single_gpu_busy_refuses_launch_spec_before_every_stage`, `test_spawn_pins_list_argv_session_cwd_env_tee`, `test_spawn_same_second_same_basename_never_shares_tee_file` (4 passed). The screen gate chain (`tui/screens/run_config.py`) was touched ONLY by IN-02: `GateWorkerError` gains `scope` (:1117-1143) and the four posting sites tag 'stage' (:1950/:2014/:2042) vs 'launch' (:2092); the staleness filter (:2151-2169) compares run_id against EXACTLY ONE counter per scope — a superseded stage error can no longer surface as a spurious launch-failed toast after a successful launch. No gate stage, modal order, or confirmation semantics changed. The ruling set re-pinned green this pass: `test_enter_key_pin_inputs_never_launch` (enter-inert), `test_gate_happy_path_confirms_and_launches`, `test_gate_confirm_modal_lists_planned_pairs_capped`, `test_n_cancels_gate_confirm_without_launch` (20-test batch, all green) |
| 3 | **SC3** execution always a `run_sweep.py` subprocess (LIST argv + PYTHONUNBUFFERED=1 + start_new_session); exit kill/detach/cancel; detached sweeps resume-safe to re-attach | ✓ VERIFIED — **STRENGTHENED by the WR-01/02/03 exit-channel fixes** | Spawn pins green (above). The exit surface was the WR trio's target; every fix site re-read at HEAD: **WR-01** `on_event` (app.py:1201-1212) delegates ctrl+c through `super().on_event` ONLY for `isinstance(focused, Input) and focused.selected_text` on a non-modal top screen — empty selection / non-Input / modals keep the CDR-2 routing, so the any-focus exit ruling survives with copy parity restored (the round-2 WR-01 advisory). **WR-02** `ExitModal.action_kill_quit` (:261-272) now delegates to `request_kill_and_exit` (:1216) → `_exit_kill_worker` (:1231-1255, `@work(exclusive=True, thread=True, group="exit-kill", exit_on_error=False)`) with a per-root broad guard and UNCONDITIONAL `ExitKillsDone` → `on_exit_kills_done` → `self.exit()` (:1257-1261) — the kill polling is OFF the event loop (the monitor mon-kill discipline, the round-2 WR-02 advisory). **WR-03** `action_quit` (:1131-1144) computes `attached_extra = attached_running and attached_root not in roots`; the MULTI form fires on `len(roots) > 1 or (roots and attached_extra)` with `combined = tuple(roots) + ((attached_root,) if attached_extra else ())` — a TUI-launched + attached-CLI root pair now names and acts on BOTH (the round-2 WR-03 advisory). Named tests green this pass: `test_ctrlc_copies_when_input_holds_a_real_selection`, `test_exit_k_kills_every_root_then_exits_on_completion`, `test_exit_k_raising_kill_still_attempts_every_root_and_exits`, `test_mixed_roots_exit_names_and_kills_both_tui_and_attached`, `test_mixed_roots_exit_enter_detaches_both`, `test_exit_modal_multi_root_kills_every_live_sweep`, `test_exit_modal_multi_root_enter_detaches_every_live_sweep`, the two adapted CDR-2 pins (`test_ctrlc_no_sweep_opens_quit_confirm_over_focused_input`, `test_ctrlc_live_sweep_routes_to_exit_modal_over_focused_input` — now `press("end")`-collapsed to pin the empty-selection corner they were written for), plus `tests/tui/test_work_site_hardening.py` green with ZERO edits (the new @work site carries exit_on_error=False AND the internal broad guard). The unmodified ruling set green: every-exit-confirms (q/ctrl+q no-sweep → QuitConfirm; n/esc cancel; below-min-grid never), y-only keycap/bold pins, ctrl+c inert-under-modals (P9), ctrl+q stacking guard, Q-plain-letter / q-types pins (20-test batch) |
| 4 | **SC4** monitor dashboard: cell states via tolerant scans, stats/ETA, attach for CLI sweeps, gated re-run, bounded tail + tee, ⊘ resume | ✓ VERIFIED | Monitor surface outside the klw delta (`tui/screens/monitor.py`, `tui/services/sweep_monitor.py` untouched since round 2) and re-pinned green this pass: `test_k_opens_kill_confirm_y_kills_without_exiting` (the off-loop `_run_kill` @work thread group="mon-kill" re-read at monitor.py:1530-1532, `MON_KILL_UNAVAILABLE` honest refusal :1503-1513), `test_attach_tilde_spelled_monitors_resolved_root_real_scanner`, `test_rerun_confirm_names_pairs_times_seeds_estimate`, `test_kill_confirm_footer_shows_y_n_keycaps`, `test_kill_confirm_message_bolds_y_n_tokens` (5 passed). Selection-side IN-01 fix (`selection.apply_queue_progress` :1614-1619 — the `_live_percents`/`_live_speeds` stores now sit BELOW the `(entry is None or state != "downloading")` guard, the slot-3 twin's ordering) re-read and `test_dataset_kind_tick_stores_no_live_dict_residue` green; env-side IN-03 fix (`env_check.action_refresh` sets `_check_in_flight = True` synchronously at :719-720 before `run_full_check()`) re-read and `test_refresh_sets_in_flight_flag_synchronously` green |
| 5 | **SC5** bounded smoke runs launch→monitor→failure-re-run E2E on GB10 while E2' demonstrably blocks; every capability headless via CLI | ✓ VERIFIED | Unchanged this round (SC5's evidence is the executed 2026-10-13 UAT + the 2026-10-16 live PlantHelixSeek launch through the current gate) and the artifacts re-read on disk THIS pass: `finetuned-smoke/` (repo root) with `plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42/trainer_state.json` (+ the full per-cell artifact set), `plant-dnamamba-6mer/`, `PlantHelixSeek/PDLLMs_datasets__plant-multi-species-H3K27ac/seed_42/`, `sweep_manifest.json` + `sweep_failures.json`, and `pipeline/finetuned/smoke-2x2-261014/`. 11-UAT.md `status: passed` (round-2, unmodified). CLI parity surface (`pipeline/run_sweep.py`) byte-untouched by the delta. The 07-CR-01 fix in `pipeline/run_finetune.py` (guarded `model_row.get("Model_name", ix)` :1015 / `.get("Mean_token_length", 1)` :1035) only widens which registry entries the child tolerates — pinned by the new AST source-contract test `test_minimal_custom_entry_reads_are_guarded` (green this pass); no SC5 behavior altered |

**Score:** 5/5 truths verified (zero behavior-unverified — every behavior-dependent claim in this round's delta is exercised by a passing named test: the WR-01 delegation routing, the WR-02 exit-lands-only-on-completion + every-root-attempted fan-out, the WR-03 mixed-root naming/acting, the IN-01 store gating, the IN-02 scope-split id spaces, the IN-03 synchronous flag, the CR-01 guarded reads)

### Round-2 Advisory Adjudication (the round-3 core question)

The klw batch claims to resolve the round-2 report's WR-01/02/03 + IN-01/02/03 advisories. Adjudicated against the code and tests this pass:

| Round-2 advisory | Fix commit | Resolution state (this pass) |
|------------------|-----------|------------------------------|
| WR-01 — ctrl+c intercept killed Input copy on base screens | `06d2679` | **RESOLVED** — delegation verified at app.py:1201-1212 (Input + truthy `selected_text` + non-modal only); `test_ctrlc_copies_when_input_holds_a_real_selection` green; the two CDR-2 over-focused-Input tests adapted (documented Rule-1 deviation: textual 8.2.8 `select_on_focus` auto-selects, so `press("end")` collapses to the empty-selection corner the tests were written for — every original assertion preserved, and BOTH corners now pinned) |
| WR-02 — ExitModal kill ran synchronously on the event loop | `06d2679` | **RESOLVED** — off-loop `@work(exclusive, thread, group="exit-kill", exit_on_error=False)` worker with per-root broad guard + unconditional `ExitKillsDone` verified at app.py:1216-1261; `test_exit_k_kills_every_root_then_exits_on_completion` + `test_exit_k_raising_kill_still_attempts_every_root_and_exits` green (the raising-run's broad-guard prints observed in this pass's output); `test_work_site_hardening.py` green with zero edits |
| WR-03 — attached-CLI-root exit advertised a noop kill / dropped the CLI sweep | `06d2679` | **RESOLVED** — mixed one-TUI-root + one-attached-CLI-root now joins the MULTI form naming and acting on BOTH (app.py:1131-1144); `test_mixed_roots_exit_names_and_kills_both_tui_and_attached` + `test_mixed_roots_exit_enter_detaches_both` green; the three pre-existing forms byte-unchanged (single-root, >1-TUI-roots, attached-only — the latter keeps the documented launcher-noop kill, and the monitor's own [k] still refuses honestly with MON_KILL_UNAVAILABLE) |
| IN-01 — GateWorkerError either-counter id collision (spurious launch-failed toast) | `0d02e18` | **RESOLVED** — scope-tagged single-counter filter verified (run_config.py:1117-1143 posting sites, :2151-2169 filter); `test_gate_worker_error_scope_tags_split_the_id_spaces` green (collision case + three controls) |
| IN-02 — round-2 info tier: slot-2 selection live-dict residue (08-REVIEW IN-01) | `0d02e18` | **RESOLVED** — stores below the guard (selection.py:1614-1619); `test_dataset_kind_tick_stores_no_live_dict_residue` green |
| IN-03 — round-2 info tier: env remount stale-cache window (08-REVIEW IN-03) | `0d02e18` | **RESOLVED** — synchronous `_check_in_flight` set (env_check.py:719-720); `test_refresh_sets_in_flight_flag_synchronously` green |
| Golden-refresh supersession (D-03) note | — | **STANDS** — no SVG interaction this round (`git diff` over snapshots = 0 lines); suite green (11 passed) |
| WINDOWS #26/#27 | — | **CARRIED** — unchanged ledger advisories (frontmatter) |

Ledger note: `08-REVIEW-DISPOSITION.md` still shows the six rows `open` (recorded 04:43Z, before the 07:20Z fixes); the rows await the disposition-gate re-run — code resolution is verified here (frontmatter advisory #1).

### Advisory (New Scope, Unevidenced; re-verification ran)

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| 1 | 08-REVIEW-DISPOSITION ledger rows not yet flipped to fixed | other | Ledger formality; code resolution verified this pass |
| 2 | run_finetune sibling hard-index sites (:849/:1077/:1322) | other | Outside the maintainer's ruling scope; phase-7 surface, queued future batch |
| 3 | WizardModal keycap ruling needed | other | Carried maintainer decision item; phase-9 surface |
| 4 | WINDOWS #26/#27 ledger rows | other | Carried; no SC breach |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/run_sweep.py` + `tests/test_sweep.py` | D-18 variant aliasing + parity suite (11-01) | ✓ VERIFIED | Byte-untouched by the klw delta (git-diff verified ba0c8d6..1cb8512) |
| `tui/services/run_config.py` + tier-1 suite | Same-source service (11-02) | ✓ VERIFIED | Untouched by the delta; `import run_sweep`/enumerate re-read (:115/:907); the file's sole full-suite failure member is machine-local (pipeline/logs exists on this dev box — re-run individually this pass, failure text confirms the fresh-checkout assertion, not a code defect) |
| `tui/services/sweep_launcher.py` + suite | Gated launch lifecycle (11-03, hardened 11-08) | ✓ VERIFIED | Untouched by the delta; 4 core pins green this pass (phrase-silent refusal, stage-0 guard, spawn pins, O_EXCL tee) |
| `tui/services/sweep_monitor.py` + suite | Pure scanner (11-04) | ✓ VERIFIED | Untouched by the delta; standing green per round 2, monitor Pilot pins green this pass |
| `tui/strings.py` + `tests/tui/test_strings_phase11.py` | Copy contract + tripwire (11-05) | ✓ VERIFIED | Zero-diff this round (zero new strings claim holds); tripwire 10 passed |
| `tui/screens/run_config.py` | Slot-4 screen + gates (11-06) | ✓ VERIFIED | Touched only by IN-02 (scope tags on worker errors — error hygiene, no gate semantics); 27 of its Pilot tests green this pass across the WR/IN/ruling batches |
| `tui/screens/monitor.py` | Slot-5 screen (11-07) | ✓ VERIFIED | Untouched; 5 monitor pins green this pass |
| `tui/app.py` (+ nav/styles) | App wiring, ExitModal/QuitConfirm, ctrl+c intercept (11-06/07 + cdr/klw) | ✓ VERIFIED | The WR trio's target — all three fix sites re-read; exit/ruling batches green (30+ tests) |
| `tui/screens/selection.py` / `tui/screens/env_check.py` | IN-01/IN-03 hygiene fixes (klw) | ✓ VERIFIED | Fix sites re-read; both named tests green |
| `pipeline/run_finetune.py` + `tests/test_run_finetune_contracts.py` | 07-CR-01 guarded reads + AST pin (klw Task 3) | ✓ VERIFIED | Guarded `.get` shapes re-read (:1015/:1035); AST contract test green |
| `tests/tui/__snapshots__/{monitor_empty,monitor_running,run_config}.svg` | Goldens (D-03 k-keycap set) | ✓ VERIFIED | Zero-diff; suite 11 passed |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_config service | run_sweep planning functions | module-level import, enumerate verbatim | ✓ WIRED | :115/:907 re-read; file untouched by delta |
| launch gate | spawner | refusal chain ordered before `_spawn` | ✓ WIRED | Launcher untouched; 4 refusal/spawn pins green this pass |
| ExitModal [k] | app exit-kill worker | `action_kill_quit` → `request_kill_and_exit` → `_exit_kill_worker` → `ExitKillsDone` → `exit()` | ✓ WIRED | app.py:261-272 → :1216-1261 re-read; completion + raising-fan-out tests green |
| action_quit | MULTI ExitModal over mixed roots | `attached_extra` → `combined` tuple → LNC_EXIT_MESSAGE_MULTI | ✓ WIRED | :1131-1144 re-read; both mixed-root tests green |
| ctrl+c (base screen) | Input copy binding / action_quit | `on_event` delegation guard | ✓ WIRED | :1201-1212 re-read; delegation + both adapted routing pins green |
| GateWorkerError posting sites | single-scope staleness filter | `scope="stage"/"launch"` tags → one-counter comparison | ✓ WIRED | :1950/:2014/:2042/:2092 → :2151-2169 re-read; scope-split test green |
| slot-5 [k] | launcher kill channel (off-loop) | KillConfirmModal y → `_run_kill` @work thread | ✓ WIRED | monitor.py:1528-1532 re-read; y-kills-without-exiting pin green |
| selection live ticks | live dicts | store-below-guard ordering | ✓ WIRED | selection.py:1614-1619 re-read; residue pin green |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| preview line / [p] modal | PreviewResult.cells | run_sweep.enumerate_matrix over the real registries | Yes (imported function verbatim; seam untouched) | ✓ FLOWING |
| gate confirm pair list | GateSummary.pairs | FRESH preview recompute at gate time | Yes (pair-cap pin green) | ✓ FLOWING |
| monitor cell table / entries | cells_view / entries_progress(root) | run_record.json / manifest / checkpoint trainer_state on disk | Yes (smoke trees re-read on disk this pass) | ✓ FLOWING |
| ExitModal root list | live_sweeps() + attached_running_counts() | launcher registry + monitor attachment | Yes — now INCLUDING the attached-CLI root (WR-03) | ✓ FLOWING |
| exit-kill fan-out | kill_sweep(root) per root | launcher process-group kill | Yes (raising-root case logged, fan-out continues) | ✓ FLOWING |

### Behavioral Spot-Checks (run this pass at HEAD `855202e`)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| WR-01 ctrl+c copy delegation (selection-holding Input) | pytest `::test_ctrlc_copies_when_input_holds_a_real_selection` | passed | ✓ PASS |
| WR-01 adapted CDR-2 corners (empty-selection routing) | pytest `::test_ctrlc_no_sweep_opens_quit_confirm_over_focused_input` + `::test_ctrlc_live_sweep_routes_to_exit_modal_over_focused_input` | 2 passed | ✓ PASS |
| WR-02 exit lands on completion; every root attempted | pytest `::test_exit_k_kills_every_root_then_exits_on_completion` + `::test_exit_k_raising_kill_still_attempts_every_root_and_exits` | 2 passed | ✓ PASS |
| WR-02 structural @work-site hardening | pytest `tests/tui/test_work_site_hardening.py` (full file) | passed | ✓ PASS |
| WR-03 mixed TUI+CLI roots named and acted on | pytest `::test_mixed_roots_exit_names_and_kills_both_tui_and_attached` + `::test_mixed_roots_exit_enter_detaches_both` | 2 passed | ✓ PASS |
| WR-05 multi-root exit (regression) | pytest `::test_exit_modal_multi_root_kills_every_live_sweep` + `::test_exit_modal_multi_root_enter_detaches_every_live_sweep` | 2 passed | ✓ PASS |
| IN-01 dataset-tick live-dict residue | pytest `tests/tui/test_pilot_selection_custom.py::test_dataset_kind_tick_stores_no_live_dict_residue` | passed | ✓ PASS |
| IN-02 scope-split id spaces | pytest `::test_gate_worker_error_scope_tags_split_the_id_spaces` | passed | ✓ PASS |
| IN-03 synchronous in-flight flag | pytest `tests/tui/test_pilot_env_check.py::test_refresh_sets_in_flight_flag_synchronously` | passed | ✓ PASS |
| 07-CR-01 guarded reads AST contract | pytest `tests/test_run_finetune_contracts.py::test_minimal_custom_entry_reads_are_guarded` | passed | ✓ PASS |
| EHC rulings intact: enter-inert, y-only, every-exit-confirms, ctrl+c any-focus, P9 guards, keycaps | pytest 20-test ruling batch (enter-key pin, gate happy path, pair-list cap, n-cancel, q/ctrl+q routing, quit-confirm n/esc, below-min-grid, ctrl+c inert-under-modals, ctrl+q no-second-stack, keycap/bold pins, Q/q typing pins) | 20 passed | ✓ PASS |
| SC2/SC3 launcher refusal + spawn pins | pytest launcher `-k` selection (phrase-silent, stage-0, spawn pins, O_EXCL) | 4 passed | ✓ PASS |
| SC4 monitor pins (k-kill off-loop, tilde attach, rerun pairs×seeds, keycaps) | pytest monitor `-k` selection | 5 passed | ✓ PASS |
| Strings tripwire + goldens | pytest `test_strings_phase11.py` + `test_snapshots.py` (full files) | 21 passed | ✓ PASS |
| Machine-local 1F member characterized | pytest `::test_storage_overview_defaults_mirror_real_consumers` | failed — asserts `pipeline/logs` absent (fresh-checkout expectation); the dir exists on this GB10 box with live-run logs | ✓ PASS (environment-conditional; matches the documented 1F/1867P baseline membership exactly) |
| Zero new strings / zero SVG interaction | `git diff ba0c8d6..1cb8512 -- tui/strings.py tests/tui/__snapshots__/` | 0 lines | ✓ PASS |
| ruff (repo) | `uv run --group dev --group tui ruff check .` | All checks passed | ✓ PASS |
| ty (tui + pipeline) | `uv run --group dev --group tui ty check tui pipeline` | All checks passed | ✓ PASS |
| SC5 smoke artifacts on disk | read `finetuned-smoke/` + `pipeline/finetuned/smoke-2x2-261014` | all trees + trainer_state markers present | ✓ PASS |
| Full suite / node lane | documented gates (NOT re-run per refresh instructions) | 1F/1867P (sole F machine-local, characterized above); node 26/26 | ✓ PASS (documented) |

**Total this pass: 61 named/selected tests across 6 batches, all green, plus both lint/typecheck gates re-run live, git-delta discipline checks, and artifact scans.**

### Probe Execution

N/A — no phase-declared or conventional probe scripts; this micro refresh's evidence vehicles are the named pytest Pilot/tier-1 tests above (run in their own process this pass), plus the standing SC5 evidence (executed 2026-10-13 UAT, on-disk smoke trees, 2026-10-16 live run).

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| CFG-01 | 11-01/02/05/06 | ✓ SATISFIED | SC1 evidence; service + screen surface untouched by the delta; tripwire green |
| CFG-02 | 11-02/06/08 | ✓ SATISFIED | resolve_dirs basis outside the delta; standing green |
| CFG-03 | 11-02/06 | ✓ SATISFIED | same-source seam re-read (:115/:907); untouched |
| LNC-01 | 11-05/06 | ✓ SATISFIED | gate chain unchanged in semantics; happy-path + env pins green |
| LNC-02 | 11-01/03/06/07/08 | ✓ SATISFIED — strengthened | spawn pins green; the exit kill is now off-loop and names every live root incl. attached-CLI |
| LNC-03 | 11-02/03/06/07 | ✓ SATISFIED | phrase-silent refusal green; gate posting sites re-verified (IN-02 touches only error surfacing, not the verdict chain) |
| MON-01 | 11-04/05/07 | ✓ SATISFIED | scanner untouched; standing green |
| MON-02 | 11-04/05/07/08 | ✓ SATISFIED | tilde attach pin green; IN-03 improves the env panel's remount freshness |
| MON-03 | 11-04/05/07/08 | ✓ SATISFIED | rerun pairs×seeds pin green; k-kill channel green |
| MON-04 | 11-03/04/05/07/08 | ✓ SATISFIED | O_EXCL tee pin green |
| MON-05 | 11-04/05/07 | ✓ SATISFIED | trainer_state markers re-read on disk (finetuned-smoke trees) |

REQUIREMENTS.md: all 11 phase requirements [x]; traceability rows Complete; coverage block re-read — 0 unmapped, 0 orphaned.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | Zero TBD/FIXME/XXX/TODO/HACK across the 10 klw-delta files and the phase surface; the `PLACEHOLDER` grep hits are Input placeholder-text constants by design (SEL_FILTER_PLACEHOLDER etc.) — verified in context | — | — |

### Human Verification Required

None. This round's delta (the seven klw fixes) is entirely machine-verified: every fix site re-read at HEAD and every behavior-dependent claim exercised by a named passing test run this pass (delegation routing, completion-gated exit, every-root fan-out, mixed-root naming, store gating, scope-split filtering, synchronous flag, guarded reads). SC5's human half remains closed by the executed live UAT (2026-10-13) and the 2026-10-16 live launch through the current gate — unchanged by this batch.

### Gaps Summary

None. The round-3 micro refresh confirms the phase goal holds at HEAD `855202e` (code-identical to `1cb8512`) after the quick-261017-klw fix batch: all five SCs re-verified — SC1/SC4/SC5 through their untouched seams (git-diff-verified exclusion from the delta plus re-reads and green pins), SC2/SC3 through the fix-shaped surfaces. The klw changes only STRENGTHEN the SC3/SC2 contracts: the exit kill moved off the event loop behind a completion message with an every-root broad guard, the mixed TUI+CLI live-root case now joins the names-every-root MULTI form, base-screen Inputs regained ctrl+c copy parity with modals, the gate's worker-error staleness filter lost its either-counter collision, and the slot-2/slot-1 hygiene fixes closed three residue/staleness seams. All seven findings were RED-first with tests green this pass; the EHC ruling set (enter-inert, y-only, every-exit-confirms, ctrl+c any-focus, P9 stacking guards) passed unmodified except the two documented CDR-2 adaptations that now pin both selection corners. Zero new strings, zero SVG interaction, ruff+ty green live this pass. The four frontmatter advisories are ledger/maintainer-decision items on other phases' surfaces — none breaches a phase-11 SC.

---

_Verified: 2026-10-17T07:42:47Z_
_Verifier: Claude (gsd-verifier)_
