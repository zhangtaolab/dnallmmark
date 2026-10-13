---
phase: 11-run-config-launch-gates-single-gpu-monitoring
verified: 2026-10-13T16:20:00Z
status: human_needed
score: 4/5 must-haves verified
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
  - pipeline/run_sweep.py
  - tests/test_sweep.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_services_run_config.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_services_sweep_monitor.py
  - tests/tui/test_strings_phase11.py
  - tui/app.py
  - tui/screens/monitor.py
  - tui/screens/nav.py
  - tui/screens/run_config.py
  - tui/services/run_config.py
  - tui/services/sweep_launcher.py
  - tui/services/sweep_monitor.py
  - tui/strings.py
  - tui/styles.tcss
covered_digest: "v3:sha256:7fb9e7d2841f3588fbc87feb041f4d78dfc4b9dc46947bdc306193e4de4cff2a"
behavior_unverified: 1
behavior_unverified_items:
  - truth: "SC5 — a maintainer-authorized bounded smoke (1 model × 1 task × 1 seed, 1 epoch) runs launch → monitor → failure-re-run end-to-end on GB10"
    test: "Execute the 9-step GB10 smoke procedure (steps 2-8): mark plant-dnabert-6mer × iDNA_ABF_datasets__5mC, seeds 42, epochs 1, output root ./finetuned-smoke; preview → gate → launch → auto-nav to slot 5 → detach → relaunch TUI → rediscover + [t] tail + ⊘ resume → optional failure-re-run leg"
    expected: "The sweep launches from slot 4, auto-navigates to the attached monitor, cells flip ⠋→✓; after detach+relaunch the root is rediscovered, the tee tail reads, a re-launch of the same cell skips with ⊘ + the resume note; the failure-re-run leg completes"
    why_human: "GPU + the dnallm env are the maintainer's authorization boundary (D-15: this host is dev/test only; the smoke is by design NOT executor- or verifier-executable). Recorded as open broken-windows ledger entry #20"
human_verification:
  - test: "Run the GB10 bounded smoke (SC5 execution half) per the 9-step procedure"
    expected: "All procedure outcomes hold: preview 1 cell + verbatim argv; env preflight passes; launch → toast → slot-5 auto-nav attached; elapsed accrues, ETA degrades honestly; detach → TUI relaunch → rediscovery + tee tail + ⊘ resume; optional failure-re-run leg (GUE__virus_species_40 or a poisoned cell) completes through [f]→r"
    why_human: "Requires GPU + dnallm runtime under maintainer authorization (D-15 / binding constraint 1). Procedure location: .planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-07-SUMMARY.md, section 'The GB10 Bounded Smoke Procedure' (steps 1-9). Pending entry recorded in .planning/WINDOWS.md #20"
  - test: "Procedure step 8 — E2'-blocks-demonstrably on the live console: compose 62 × 50 × 3 (mark all + seeds 42,43,44) and press [enter]"
    expected: "The E2' typed-phrase modal appears; a WRONG dirname leaves 确认 dead; do NOT type the matching phrase and do NOT launch (full sweeps run on other machines, D-15)"
    why_human: "The live-modal presentation is the maintainer's visual confirmation; the gate's blocking behavior itself is already CI-fake-proven (see Behavioral Spot-Checks rows 1-3). Human confirmation closes the loop on the real console at full selection scale"
---

# Phase 11: Run Config, Launch Gates & Single-GPU Monitoring — Verification Report

**Phase Goal:** The operator's core loop is closed and safe — compose a complete run spec, preview it from the same pure planning functions execution uses, pass the env + confirmation gates, launch `run_sweep.py` as a detached subprocess, and monitor/recover the sweep from the same console — proven end-to-end by a maintainer-authorized bounded smoke on GB10, with E2' provably still maintainer-gated
**Verified:** 2026-10-13T16:20:00Z (HEAD `bc8e52c`, branch `autorun`; phase base `986c2a8`)
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (SC1-5, ROADMAP verbatim anchor)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **SC1** run-config screen exposes the full parameter set + separated directories + same-source dry-run preview with enumerated cell counts | ✓ VERIFIED | Live TUI drive (tmux 140x45, `make tui`): slot 4 renders the 62-model picker, the full params pane (seeds default `42,43,44`, PEFT `none ▾`, 变体 `none ▾`, 曲线档位, 公平子集 `关（pipeline/eval_subsets.json）`, epochs 覆盖, effective_batch_size), the 目录 section (输出根 `./finetuned` + ✓ 路径存在 advisory, 数据集根, 模型缓存). Marking 1 model × 1 task flipped the live preview line to `干跑: 1 模型 × 1 任务 × 3 种子 = 3 cell`; `[p]` modal showed `同源: pipeline.run_sweep.enumerate_matrix（零复制…）` + the verbatim LIST argv (`python run_sweep.py --models … --tasks … --output-root <abs>`). D-05 same-source confirmed in code (`tui/services/run_config.py:95` module-level `import run_sweep`; `:786` `run_sweep.enumerate_matrix(...)`) and behaviorally (direct call over the real committed registries: 1×1×seed-42 → `cells_count: 1`, cell tuple verbatim; import purity: torch/dnallm/transformers absent after import). Tests run green at HEAD: `test_params_defaults_render`, `test_preview_line_renders_and_updates_on_mark`, `test_preview_modal_renders_argv_and_problems`, `test_importing_service_leaves_gpu_stack_absent` (fresh `python -I` subprocess probe) |
| 2 | **SC2** terraform-style launch gate: env preflight blocks with reason, preview precedes explicit confirm, E2' requires a typed phrase the TUI cannot bypass | ✓ VERIFIED | Code: `launch_spec` refusal chain each stage BEFORE the spawner (`sweep_launcher.py:503-558`: preview problems → official-keys fail-closed → E2' exact phrase); CR-01 fix `_from_failures_refusal` (`:587-642`) recomputes the effective matrix via the REAL `run_sweep.load_failure_pairs` + `is_full_e2x` (zero copied matrix logic); WR-07 fail-closed `phrase_matches` (`run_config.py:944-963`, `bool(expected) and typed == expected`) + `output_root_invalid` problem. Frozen face consumed with ZERO edits: `git diff 986c2a8..HEAD --stat -- tui/services/env_gate.py tui/services/quick_check.py` = **empty**. Tests run green at HEAD: `test_launch_from_failures_complete_manifest_three_seeds_demands_phrase` (real 62×50 official registries, complete failures manifest × 3 seeds → `GateRefusal stage=phrase`, `spawner.calls == []`), `test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent`, `test_phrase_matches_never_matches_an_empty_expected_phrase`, `test_validate_composition_refuses_filesystem_root_output_root`, Pilot `test_gate_e2x_phrase_flow` / `test_gate_env_block_renders_reasons_verbatim` / `test_gate_problems_blocked_launch_never_called` / `test_rerun_env_block_renders_the_same_modal` |
| 3 | **SC3** execution always a `run_sweep.py` subprocess (LIST argv + PYTHONUNBUFFERED=1 + start_new_session); exit kill/detach/cancel; detached sweeps resume-safe to re-attach | ✓ VERIFIED | Code: `_spawn` (`sweep_launcher.py:415-499`) — `list(argv)`, `start_new_session=True`, `cwd=pipeline/`, `env={**os.environ, "PYTHONUNBUFFERED": "1"}`, stdout→tee/stderr→STDOUT; CR-02 duplicate-root guard (`:448-462`); `kill_sweep` SIGTERM→killpg→SIGKILL escalation (`:711-742`); `detach` drops handle no-signal (`:744-762`); WR-04 `live_sweeps()` prunes exited Popens (`:766-794`); IN-05 `_tee_history` fallback (`:796-819`). app.py `action_quit` ExitModal (default detach) + q-intercept. Tests run green at HEAD: `test_spawn_pins_list_argv_session_cwd_env_tee`, 10 kill/detach/prune/duplicate service tests (`-k "kill or detach or duplicate or live_sweeps or prune"`), Pilot `test_exit_enter_detaches_then_exits`, `test_exit_k_kills_then_exits`, monitor re-attach suite. Resume-safety substrate: `RESUME_MARKER` skip is run_sweep's own pinned contract (98 sweep tests); the live detach→relaunch→⊘ round trip is smoke step 6 (folded into the human item) |
| 4 | **SC4** monitor dashboard: cell states via 2s/60s tolerant scans, stats/ETA, attach for CLI sweeps, gated `--from-failures` re-run, bounded log tail + tee, ⊘ resume recognition | ✓ VERIFIED | Code: `monitor.py` `FRONTIER_INTERVAL_SECONDS=2.0` / `FULL_INTERVAL_SECONDS=60.0` (`:141-142`), `set_interval` at `:932-934`, exclusive `mon-frontier`/`mon-full` thread workers (`:960/:999`), `_set_table_rows` diff-preserving updates (`:705`, WR-05 fix); scanner `sweep_monitor.py` imports the driver's own artifact constants (`:51-57`, D-05). Full monitor Pilot suite run green at HEAD: **33 passed** (`test_cadence_dispatches_workers_and_stops_on_unmount` — mount kick + tick callbacks + fake counter proofs + no zombie workers; `test_stats_line_variants`, `test_attach_via_enter_moves_marker_and_rebinds`, `test_attach_path_invalid_keeps_modal_never_attaches`, `test_rerun_confirm_routes_launch_from_failures_and_attaches`, `test_rerun_e2x_phrase_refusal_reprompts_then_launches`, `test_log_tail_renders_lines_and_tee_line`, `test_log_tail_no_tee_is_designed_unavailable`, `test_degradation_corrupt_record_renders_last_known_good`, `test_console_stays_responsive_while_scan_blocks`, `test_table_updates_preserve_cursor_across_ticks`, …) |
| 5 | **SC5** bounded smoke runs launch→monitor→failure-re-run end-to-end on GB10 while E2' demonstrably blocks; every capability headless via CLI | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | **Fake-provable halves VERIFIED at HEAD:** the E2'-blocks proof is CI-pinned by three tests — `test_launch_from_failures_complete_manifest_three_seeds_demands_phrase` (a full-matrix attempt refused spawner-silent at stage `phrase`), `test_gate_e2x_phrase_flow` (Pilot: mismatch enter no-op, live-match flip, launch only with phrase), `test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent`; the launch→monitor chain by `test_launch_success_auto_navigates_to_monitor_attached`. **Headless parity VERIFIED:** all 13 CLI flags present in `run_sweep.py --help` (--models/--tasks/--seeds/--peft/--config-variant/--curve/--subset_file/--num_train_epochs/--effective_batch_size/--cache_dir/--from-failures/--dry-run/--output-root). **9-step GB10 procedure DOCUMENTED** (11-07-SUMMARY "The GB10 Bounded Smoke Procedure": plant-dnabert-6mer × iDNA_ABF_datasets__5mC × seed 42 × 1 epoch, `./finetuned-smoke`) + pending entry in `.planning/WINDOWS.md` #20. **The execution half is by design maintainer-run** (D-15: GPU + dnallm env are the authorization boundary; NOT executor- or verifier-executable) — routed to human verification, not a gap |

**Score:** 4/5 truths verified (1 present, behavior-unverified — the GB10 smoke execution half, a designed maintainer authorization boundary)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tui/services/run_config.py` | RunSpec/preview/dirs/phrase/argv service | ✓ VERIFIED | 1076 lines; imports run_sweep (D-05); 73 tests green |
| `tui/services/sweep_launcher.py` | Spawn/tee/kill/detach/gate service | ✓ VERIFIED | 819 lines; CR-01/CR-02/WR-04/IN-05 fixes in place; 44 tests green |
| `tui/services/sweep_monitor.py` | Scanner: discovery/cells/stats/ETA/tail | ✓ VERIFIED | 1228 lines; driver artifact constants imported; 49 tests green |
| `tui/screens/run_config.py` | Slot-4 screen | ✓ VERIFIED | 1734 lines; live-rendered in tmux; 36 Pilot tests green |
| `tui/screens/monitor.py` | Slot-5 screen | ✓ VERIFIED | 1537 lines; 33 Pilot tests green |
| `tui/app.py` | Factories/seams/ExitModal/D-13 hook | ✓ VERIFIED | `build_run_config_screen`/`build_monitor_screen`/`sweep_launched`+`MonitorSwitchRequested`/`action_quit` present (`:460-:539`, `:732-:747`, `:817-:840`) |
| `tui/screens/nav.py` | Slots 4+5 promoted | ✓ VERIFIED | `NavSlot(4, …, "run_config", None)`, `NavSlot(5, …, "monitor", None)` (`:89-90`); live: `◆ 4运行配置` rendered, digit-4 switch worked |
| `tui/strings.py` | 99 CFG_/LNC_/MON_ constants, single home | ✓ VERIFIED | bidirectional tripwire green (5 tests); no raw CJK in screens (CJK locks in Pilot suites green) |
| `pipeline/run_sweep.py` | `--config-variant` aliasing (D-18 errata) | ✓ VERIFIED | 20-test aliasing suite in the 98 sweep tests; HEAD_KEEP_BASE_NAMES read-source parity pinned |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_config screen | run_config + launcher services | constructor-injected Protocols | ✓ WIRED | app.py factories pass backends; Pilot suites exercise the real screen over fakes; live screen rendered |
| run_config service | `pipeline/run_sweep` | module-level import (`:95`) | ✓ WIRED | `enumerate_matrix` called at `:786`; direct call produced real cells |
| sweep_launcher | env_gate + quick_check (frozen face) | direct import (`:90`) | ✓ WIRED | zero edits since 986c2a8 (git diff empty) |
| sweep_monitor | run_sweep artifact names + artifact_loader | direct imports (`:50-57`) | ✓ WIRED | MANIFEST/FAILURES/RECORD/RESUME_MARKER single-sourced |
| monitor screen | launcher (tee/live_sweeps/from-failures) | MonitorBackend injection | ✓ WIRED | `[t]`/`[f]→[r]`/ExitModal Pilot-tested |
| app.py | nav slots 4/5 | digit bindings + factories | ✓ WIRED | live digit-4 switch verified in tmux |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| run_config preview | `cells` / `cells_count` | `run_sweep.enumerate_matrix` over committed registries | Yes — live call returned `(('plant-dnabert-6mer','iDNA_ABF_datasets__5mC',42),)` | ✓ FLOWING |
| [p] modal argv | `compose_argv(spec)` | real interpreter path + run_sweep.py | Yes — live modal showed the real absolute argv | ✓ FLOWING |
| monitor cell table | `cells_view` records | `run_record.json` / manifest / trainer_state markers on disk | Yes — synthetic-tree tests + tolerant readers (LKG) | ✓ FLOWING |
| slot-4 pickers | registry keys | `pipeline/{models,datasets}_info.json` via overlay-free official_keys | Yes — live: 62 models / 50 tasks rendered | ✓ FLOWING |

### Behavioral Spot-Checks (all run at HEAD `bc8e52c`)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| E2' gate blocks a full-matrix re-run attempt (spawner-silent) | `pytest …::test_launch_from_failures_complete_manifest_three_seeds_demands_phrase` | PASSED (also verbose-run with partial-manifest + two-seeds controls) | ✓ PASS |
| E2' phrase wrong/absent → spawner never called | `pytest …::test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent` | PASSED | ✓ PASS |
| "/" output root fails closed (WR-07) | `pytest …::test_phrase_matches_never_matches_an_empty_expected_phrase` + `::test_validate_composition_refuses_filesystem_root_output_root` | 4 passed (both lanes batched) | ✓ PASS |
| Import purity (D-05) | `pytest …::test_importing_service_leaves_gpu_stack_absent` + direct `python -I` service call | PASSED; live probe printed `IMPORT PURE: torch/dnallm/transformers absent`, `cells_count: 1` | ✓ PASS |
| SC1/SC3/SC5 Pilot lanes (10 named tests) | `pytest test_pilot_run_config.py::<9 named> + launcher spawn-pins` | 10 passed | ✓ PASS |
| SC4 monitor Pilot suite (full file) | `pytest tests/tui/test_pilot_monitor.py -q` | 33 passed | ✓ PASS |
| SC3 kill/detach/prune/duplicate service lanes | `pytest … -k "kill or detach or duplicate or live_sweeps or prune"` | 10 passed | ✓ PASS |
| Strings tripwire + services import lock | `pytest tests/tui/test_strings_phase11.py tests/tui/test_import_lock.py` | 6 passed | ✓ PASS |
| Slot-4 live render + preview line + [p] modal | `make tui` in tmux 140x45; mark 1×1; press p | Screen renders all panes; preview line `1 模型 × 1 任务 × 3 种子 = 3 cell`; modal shows same-source note + verbatim argv; XDG spec persisted (D-01) | ✓ PASS |
| CLI parity flags | `python3 pipeline/run_sweep.py --help` | all 13 parity flags present | ✓ PASS |

**Full-suite baseline:** 1501 pytest + 18/18 node:test at `40cb0bd` (11-REVIEW-FIX.md final gates; ruff + ty clean). HEAD `bc8e52c` differs from `40cb0bd` by docs-only commits (`git diff 40cb0bd..HEAD --stat -- tui/ tests/ pipeline/ scripts/` = empty), so the gate result stands for HEAD's code state. Fresh confirmation this pass: 67 tests re-run green across the six load-bearing files.

### Probe Execution

N/A — no phase-declared or conventional probe scripts (`scripts/*/tests/probe-*.sh`); this phase's evidence vehicle is the pytest Pilot/tier-1 harness.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CFG-01 | 11-01/02/05/06 | Full parameter surface | ✓ SATISFIED | Live render + params-defaults Pilot + 73 service tests |
| CFG-02 | 11-02/06 | Dirs separation (D-14) | ✓ SATISFIED | DirPlan + live 目录 pane + advisory tests |
| CFG-03 | 11-02/06 | Same-source preview | ✓ SATISFIED | D-05 code+live+tests (above) |
| LNC-01 | 11-05/06 | Launch gate copy + presentation | ✓ SATISFIED | LNC_ constants tripwire + gate modal Pilot lanes |
| LNC-02 | 11-01/03/06 | Subprocess discipline + exit triple | ✓ SATISFIED | SC3 evidence |
| LNC-03 | 11-02/03/06/07 | E2' unbypassable | ✓ SATISFIED | SC2 evidence incl. CR-01 re-run gate + WR-07 fail-closed |
| MON-01..05 | 11-04/05/07 | Monitor dashboard + re-run + tee + resume | ✓ SATISFIED | SC4 evidence (33 Pilot + 49 scanner tests) |

REQUIREMENTS.md: all 11 phase requirements marked [x]. No orphaned requirements (grep Phase 11 → CFG/LNC/MON set exactly).

### Decision Coverage

`check.decision-coverage-verify`: 20/20 honored, 0 not honored — all trackable CONTEXT.md decisions (D-01..D-19 incl. D-18 errata) appear in shipped artifacts.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| tui/screens/monitor.py, run_config.py | 77/1531; 150/926 | `*_PLACEHOLDER` identifiers | ℹ️ Info | UI Input placeholder text constants from strings.py (wired copy, not stubs) — verified rendered and consumed |

Zero `TBD`/`FIXME`/`XXX` markers across all 8 phase code files. Zero `NotImplementedError`. Working tree clean (only pre-existing `.planning/.gsd-allow-shrink` untracked).

### Constraint Checklist (binding milestone constraints)

| Constraint | Evidence | Status |
|-----------|----------|--------|
| Pipeline surface: only run_sweep.py + tests/test_sweep.py | `git diff 986c2a8..HEAD --stat -- pipeline/` → 1 file (run_sweep.py, +181/−34); full diff tree = 37 files, pipeline-side exactly those two | ✓ |
| Official registries untouched | `git diff 986c2a8..HEAD --stat -- pipeline/{models,datasets}_info.json` = empty | ✓ |
| Frozen phase-8 face consumed zero-edit (D-08) | `git diff 986c2a8..HEAD --stat -- tui/services/env_gate.py tui/services/quick_check.py` = empty | ✓ |
| Services zero-textual | `tests/tui/test_import_lock.py` green (glob auto-extends); services import only stdlib + seams | ✓ |
| Strings single-home, tripwire over CFG_/LNC_/MON_ | `tests/tui/test_strings_phase11.py` 5 tests green (bidirectional inventory) | ✓ |
| Import purity — no torch/dnallm/transformers in the TUI service chain | purity test green + live `python -I` probe (absent after import) | ✓ |
| CI GPU/network-free, zero new jobs | `git diff 986c2a8..HEAD --stat -- .github/` = empty | ✓ |
| TUI orchestrates, never computes (D-05) | preview/argv/E2' verdict all through imported run_sweep functions or file reads; zero re-implemented enumeration | ✓ |
| E2' maintainer dual-gate (D-07/D-15) | SC2 evidence; the smoke itself deferred to the maintainer per design | ✓ |
| 1501-test baseline + lint/typecheck | 11-REVIEW-FIX.md final gates at 40cb0bd (= HEAD code state); 67 fresh green re-runs this pass | ✓ |

### Human Verification Required

1. **Run the GB10 bounded smoke (SC5 execution half).** Procedure: `.planning/phases/11-run-config-launch-gates-single-gpu-monitoring/11-07-SUMMARY.md` → "The GB10 Bounded Smoke Procedure" (9 steps; plant-dnabert-6mer × iDNA_ABF_datasets__5mC × seed 42 × 1 epoch, output root `./finetuned-smoke`). Expected: launch → auto-nav → monitor → detach/reattach with ⊘ resume → optional failure-re-run leg. Tracked as `.planning/WINDOWS.md` entry #20. Why human: GPU + dnallm runtime under maintainer authorization (D-15).
2. **E2'-blocks live confirmation (procedure step 8).** Compose 62×50×3 on slot 4, press [enter], confirm the typed-phrase modal appears and a wrong dirname leaves 确认 dead; do NOT type the matching phrase. Why human: live-console confirmation at full-selection scale (the blocking behavior is already CI-fake-proven — three named tests above).

### Gaps Summary

No failed truths, no missing/stub artifacts, no unwired links, no debt markers. The single open item is the GB10 smoke's execution half — by design a maintainer-authorization boundary (D-15), not an implementation gap; it is documented (9-step procedure), tracked (WINDOWS.md #20), and routed to human verification above.

### Risks (known-accepted, from the phase review record)

- **IN-02** (kept open, policy): custom registry keys shaped `+lora/+ia3/+head/+probe/+curve` can collide with derived alias dirs — requires a hand-named custom entry (no official key contains `+`); routed to Phase 12 hardening / maintainer ruling.
- **IN-03** (kept open, watch-at-smoke): the 2s stats leg re-reads all records per tick — correctness unaffected; watch at the GB10 smoke, fix shape pre-named.
- **IN-04** (kept open, polish): `sweep_scale` inline on the event loop — bounded (one manifest read per finished root per 60s).
- **IN-06** (introduced, cosmetic): diff-preserving tables append new rows at the bottom — display order drifts from sorted contract over a session; row keys/data/cursor pin all correct.
- **WR-02 residuals** (documented by the fixer): mid-run `resume_count` reads the prior manifest's skip count at a populated root; the pre-clear re-run toast may quote the prior sweep's cell count. Fresh-root launches (the common path) unaffected.

**VERDICT: PHASE_GOAL_ACHIEVED** — contingent on the recorded human items: every code-level, test-level, and live-console check passes at HEAD; the sole outstanding obligation is the maintainer-run GB10 smoke that the phase's own authorization boundary (D-15) reserves for the human, with its fake-provable halves (launch→monitor chain, E2'-blocks) already CI-proven.

---

_Verified: 2026-10-13T16:20:00Z_
_Verifier: Claude (gsd-verifier)_
