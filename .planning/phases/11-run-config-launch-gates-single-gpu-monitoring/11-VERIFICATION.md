---
phase: 11-run-config-launch-gates-single-gpu-monitoring
verified: 2026-10-16T07:39:44Z
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
covered_digest: "v3:sha256:eee3f54611f6bddb1140cee9bcf2868947e6838fe64b7a9f19a1b3320ce2e5ac"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  previous_verified: 2026-10-14T17:17:48Z
  gaps_closed: []
  gaps_remaining: []
  regressions: []
---

# Phase 11: Run Config, Launch Gates & Single-GPU Monitoring — Refresh Re-Verification

**Phase Goal:** The operator's core loop is closed and safe — compose a complete run spec, preview it from the same pure planning functions execution uses, pass the env + confirmation gates, launch `run_sweep.py` as a detached subprocess, and monitor/recover the sweep from the same console — proven end-to-end by a maintainer-authorized bounded smoke on GB10, with E2' provably still maintainer-gated
**Verified:** 2026-10-16T07:39:44Z (HEAD `8aacc58`, branch `autorun`, working tree clean)
**Status:** passed
**Re-verification:** Yes — covered-set REFRESH (not gap closure). The prior passed report (`2026-10-14T17:17:48Z`, HEAD `bdacbae`, 5/5) went stale: quicks c4j / ehc / h8i / pex / a4f / hhx landed a substantial TUI delta after it (43 files, +6662/−2885 over `tui/` + `tests/`), including every phase-11 surface — the y-confirm launch gates (EHC-2), the single-GPU serialization guard (EHC-3) on both launch paths, the bilingual strings registry with the L live toggle, and the hhx render-time i18n conversion of the monitor's frozen structures. This pass re-verified all five SCs against the CURRENT codebase, re-ran the phase's behavioral pins as named tests, and regenerated the fingerprint. The delta itself was code-reviewed by the scoped incremental review at `.planning/phases/08-tui-foundation-env-check-selection/08-REVIEW.md` (superset diff over the exact files); its findings are dispositioned fixed (7/8; IN-04 info-tier open) via a4f + hhx per 08-REVIEW-DISPOSITION.md.

## Goal Achievement

### Observable Truths (SC1-5, ROADMAP verbatim anchor)

| # | Truth | Status | Evidence (this pass, HEAD `8aacc58`) |
|---|-------|--------|----------|
| 1 | **SC1** full parameter set + separated dirs + same-source dry-run preview with enumerated cell counts | ✓ VERIFIED | Same-source seam UNCHANGED by the delta: `tui/services/run_config.py:115` module-level `import run_sweep`, `:907` `run_sweep.enumerate_matrix(...)` verbatim (zero re-implemented enumeration; the file is untouched by the delta quicks). Screen surface intact through hhx (`_dir_input_fields()` at `run_config.py:1748` is the render-time i18n CONVERSION of the same fields — same labels, now re-derived per language). Strings tripwire green this pass (bidirectional inventory over the bilingual registry — CFG/LNC/MON complete incl. the new keycap names). Full-suite gates on this exact tree documented green (1808 passed at the pinned 7F baseline) |
| 2 | **SC2** terraform-style gate: env preflight blocks with reason, preview precedes explicit confirm, E2' typed phrase unbypassable | ✓ VERIFIED — **strengthened by the delta** | Refusal chain at HEAD (`sweep_launcher.py:666-695`), every stage BEFORE the spawner: stage 0 EHC-3 single-GPU guard → fresh preview problems → official-keys diagnostic (fail-closed) → E2' exact-phrase → `_spawn(compose_argv, resolve_dirs(spec).output_root_abs)`. EHC-2 y-confirm (`selection.py:1223` `LaunchConfirmModal`): `y` launches, `esc` cancels, `enter` lands on a documented no-op — the explicit confirm is MORE explicit than the prior pass verified ("a stray double-enter is structurally inert"; copy names the [y] keycap). The [r] re-run path retired its "never full matrix by construction" premise: `launch_from_failures` now recomputes the effective matrix (failure pairs × seeds via the driver's own `load_failure_pairs`) and demands the typed phrase for E2'-class re-runs (`:761-838`). Named tests green THIS pass: `test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent`, `test_launch_from_failures_complete_manifest_three_seeds_demands_phrase`, `test_single_gpu_busy_refuses_launch_spec_before_every_stage`, `test_gate_happy_path_confirms_and_launches` (y-confirm), `test_enter_key_pin_inputs_never_launch` |
| 3 | **SC3** execution always a `run_sweep.py` subprocess (LIST argv + PYTHONUNBUFFERED=1 + start_new_session); exit kill/detach/cancel; detached sweeps resume-safe to re-attach | ✓ VERIFIED | `_spawn` pins unchanged at `:574-581`: `list(argv)`, `start_new_session=True`, `cwd=str(PIPELINE_DIR)`, `env={**os.environ, "PYTHONUNBUFFERED": "1"}`, stdout→tee, stderr=STDOUT — `test_spawn_pins_list_argv_session_cwd_env_tee` green this pass. WR-05 multi-root exit intact (`app.py:913-948`: predicate `live_sweeps()`, `LNC_EXIT_MESSAGE_MULTI` when >1 root; kill/detach loop every root) — `test_exit_modal_multi_root_kills_every_live_sweep` green this pass. Resume-safety grounded on disk: `finetuned-smoke/plant-dnabert-6mer/iDNA_ABF_datasets__5mC/seed_42/trainer_state.json` + full artifact set (the UAT round-trip's ⊘ proof) |
| 4 | **SC4** monitor dashboard: cell states via 2s/60s tolerant scans, stats/ETA, attach for CLI sweeps, gated re-run, bounded tail + tee, ⊘ resume | ✓ VERIFIED | All six 11-08 hardening fixes SURVIVE the delta: attach resolution (`monitor.py:1177` `Path(str(root)).expanduser().resolve()`) — `test_attach_tilde_spelled_monitors_resolved_root_real_scanner` green this pass; `derive_rerun_seeds` (:711-745, one shared derivation, failures-first/cell-fallback/else-empty) — `test_rerun_confirm_names_pairs_times_seeds_estimate` green this pass; O_EXCL tee (`sweep_launcher.py:536-570`, TEE_COLLISION_SUFFIX_CAP=99) — `test_spawn_same_second_same_basename_never_shares_tee_file` green this pass; scanner contract after its +190-line delta — 5 named tier-1 tests green this pass (full_scan/cells_view/stats/failures_view/read_log_tail). hhx render-time i18n verified in code: `_sweep_state_cells()`/`_cell_state_cells()` re-derived at call time (:113/:125); MON_FAILURES_KEYCAP/MON_LOG_KEYCAP are registry constants (strings.py:1641/:1678) registered in EXPECTED_MON_CONSTANTS (test_strings_phase11.py:109). Goldens byte-untouched through hhx (snapshots last modified at `d5cb44b`, the pre-delta D-03-approved golden refresh) |
| 5 | **SC5** bounded smoke runs launch→monitor→failure-re-run E2E on GB10 while E2' demonstrably blocks; every capability headless via CLI | ✓ VERIFIED | The prior adjudication STANDS and is further corroborated: 11-UAT.md `status: passed` — the 9-step procedure executed LIVE 2026-10-13 under maintainer authorization ("跑" 16:29), incl. the E2'-blocks proof (wrong dirname → 确认 dead, zero processes launched). Artifacts re-read on disk THIS pass: `finetuned-smoke/` (manifest = 1 model × 2 tasks × seed 42 — the 5mC cell AND the failure-leg GUE__virus_species_40 cell, each with final_metrics/flops_report/trainer_state) + `pipeline/finetuned/smoke-2x2-261014/` (dnabert half complete). NEW post-delta live corroboration: quick-261015-pex recorded the launch-through-y-gate → monitor → kill chain on camera (`docs/demo/gifs/launch-monitor-kill-{en,zh}.gif`, re-recorded post-hhx per commit `c76c315`), incl. the single-GPU guard's stage-0 refusal of a second launch while a sweep is live (TUI-DEMO.md:194) — the ehc behaviors that live in this phase's SCs, exercised for real. CLI parity re-proven this pass: all 13 flags present in `run_sweep.py --help` (models/tasks/seeds/peft/config-variant/curve/subset_file/num_train_epochs/effective_batch_size/cache_dir/from-failures/output-root/dry-run) |

**Score:** 5/5 truths verified (zero behavior-unverified)

### Delta Review Provenance (why no re-review gap exists)

The phase's own 11-REVIEW predates the delta by design. The delta on these exact files was reviewed by the scoped incremental review at `.planning/phases/08-tui-foundation-env-check-selection/08-REVIEW.md` (15 files, superset of the stale covered set): CR-01 (module-frozen copy never re-resolving under the L toggle) + WR-01..03 + IN-01..03 — **dispositioned fixed** (7/8) via a4f + hhx per 08-REVIEW-DISPOSITION.md (commit `190d1c4`/`f9528e3`); IN-04 (filter-grammar degenerate tokens) open at info tier, phase-8 surface. This pass independently confirmed the hhx fixes in code: the monitor's state vocabularies and `run_config._DIR_INPUT_FIELDS` are call-time functions; the keycaps are registered constants; both keycap names are in the bidirectional inventory.

### Advisory (carry-forward; re-verification ran)

No NEW advisory findings this pass (zero debt markers across all delta files, goldens byte-untouched, gates documented green on this exact tree). Directed carry-forwards and prior items:

| # | Finding | Assessment this pass |
|---|---------|----------------------|
| WINDOWS #26 | Post-second-launch console input death (pex rehearsals; recorded open 2026-10-15) | **Advisory, not an SC breach**: no SC promises two in-session gated launches — the EHC-3 guard structurally refuses a concurrent second launch on this single-GPU box, and the goal's operator loop (one launch → monitor → recover) is demonstrably complete (UAT + post-hhx demo casts). Sequencing-UX defect in `app.py`; open in the ledger |
| WINDOWS #27 | Monitor stalls ~60s post-launch at the first-cell completion burst (stats cadence + keys pause) | **Advisory, not an SC breach**: transient latency degradation, not a capability loss — the launch→monitor→kill chain completes on camera post-hhx, and every SC4 capability (cell states, cadence, tail, kill) was exercised live. Responsiveness defect in `monitor.py`; open in the ledger |
| WINDOWS #20 ledger row | Table row status column still reads "open" while the ledger's own note (WINDOWS.md:415) records "entry #20 resolved" (2026-10-13, the executed UAT) | Info-tier bookkeeping discrepancy — the note is the authoritative closure record (smoke executed live); the row was evidently never flipped via the CLI tool |
| 08-REVIEW IN-04 | Filter grammar accepts degenerate tokens that render oddly | Open info-tier, phase-8 surface; not SC-relevant |
| IN-01 (prior) | LNC_E2_WARNING hardcodes 59×50×8850 copy (strings.py:1452-1455; gate predicate computes fresh) | Unchanged through the bilingual conversion — still copy-drift risk only, not a gate defect |
| IN-02..05 (prior) | stale NAV comment / dead expected_seeds param / curve records unread / `__` join key | Unchanged info-tier polish items; not gaps |
| env-only test | `test_storage_overview_defaults_mirror_real_consumers` — one of the 7 pre-existing baseline failures (test_determinism 1 + test_schemas 5 + this), re-verified pre-existing at base | Known box baseline; production behavior correct; zero new failures at HEAD |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pipeline/run_sweep.py` + `tests/test_sweep.py` | D-18 variant aliasing + parity suite (11-01) | ✓ VERIFIED | Untouched by the delta; suite green in the documented full run |
| `tui/services/run_config.py` + tier-1 suite | Same-source service (11-02) | ✓ VERIFIED | `import run_sweep` / enumerate verbatim re-confirmed at :115/:907 |
| `tui/services/sweep_launcher.py` + suite | Gated launch lifecycle (11-03, hardened 11-08 + ehc + 08-review) | ✓ VERIFIED | 4-stage refusal chain + CR-01 from-failures gate + EHC-3 stage 0 + O_EXCL tee + REPO_ROOT basis — 5 named tests green this pass |
| `tui/services/sweep_monitor.py` + suite | Pure scanner (11-04; +190-line c4j delta) | ✓ VERIFIED | 5 named contract tests green this pass |
| `tui/strings.py` + `tests/tui/test_strings_phase11.py` | Copy contract + bidirectional tripwire (11-05; bilingual since ehc; keycaps since hhx) | ✓ VERIFIED | Full tripwire file green this pass (both keycap names registered :109) |
| `tui/screens/run_config.py` | Slot-4 screen + gates (11-06; y-confirm + dir-picker since delta) | ✓ VERIFIED | Gate/enter-pin/exit tests green this pass |
| `tui/screens/monitor.py` | Slot-5 screen (11-07; entries list since c4j; render-time i18n since hhx) | ✓ VERIFIED | attach/rerun tests green this pass |
| `tui/app.py`, `tui/screens/nav.py`, `tui/styles.tcss` | App wiring, ExitModal, promotion | ✓ VERIFIED | Multi-root exit + quit predicate re-read; goldens byte-stable |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| run_config service | run_sweep planning functions | module-level import, enumerate/build_argv/base_model_name | ✓ WIRED | :115/:907 re-read this pass |
| launch gate | spawner | refusal chain ordered before `_spawn` | ✓ WIRED | :666-695; spawner-silent phrase pin green this pass; + stage-0 guard (both paths) green |
| [a] PathInputModal | every monitor reader | attach → expanduser().resolve() | ✓ WIRED | monitor.py:1177; real-scanner tilde pin green this pass |
| FailuresModal [r] | launch_from_failures | request_rerun → derive_rerun_seeds → _run_rerun_launch | ✓ WIRED | One shared derivation re-read; pairs × seeds pin green; + E2'-class re-run phrase gate (new) |
| action_quit | ExitModal → kill/detach per root | live_sweeps() predicate | ✓ WIRED | app.py:913-948; multi-root kill pin green this pass |
| slot-4 launch success | slot-5 auto-attach (D-13) | app.sweep_launched → MonitorSwitchRequested | ✓ WIRED | `test_gate_happy_path_confirms_and_launches` + `test_launch_success_auto_navigates_to_monitor_attached` in the documented green full run |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| preview line / [p] modal | PreviewResult.cells | run_sweep.enumerate_matrix over the real registries | Yes (imported function verbatim) | ✓ FLOWING |
| monitor cell table | cells_view(root) | run_record.json / manifest on disk (resolved root) | Yes — smoke trees on disk read through this chain live | ✓ FLOWING |
| re-run confirm copy | pairs/seeds/n | FailureRow.seed via derive_rerun_seeds | Yes — pin asserts copy and launch agree | ✓ FLOWING |
| log tail | read_log_tail(tee_path_for(root)) | XDG logs tee file | Yes — UAT recorded live tqdm/VRAM lines | ✓ FLOWING |

### Behavioral Spot-Checks (run this pass at HEAD `8aacc58`)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Strings bidirectional inventory (incl. both keycap names) | pytest tests/tui/test_strings_phase11.py (full file) | 9 passed | ✓ PASS |
| E2' phrase refusal, spawner-silent (SC2 core) | pytest ::test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent | passed | ✓ PASS |
| E2'-class from-failures re-run demands phrase (new CR-01 gate) | pytest ::test_launch_from_failures_complete_manifest_three_seeds_demands_phrase | passed | ✓ PASS |
| Single-GPU serialization guard, stage 0 before everything | pytest ::test_single_gpu_busy_refuses_launch_spec_before_every_stage | passed | ✓ PASS |
| O_EXCL tee same-second collision (WR-04) | pytest ::test_spawn_same_second_same_basename_never_shares_tee_file | passed | ✓ PASS |
| Spawn pins: LIST argv / session / cwd / env / tee (SC3) | pytest ::test_spawn_pins_list_argv_session_cwd_env_tee | passed | ✓ PASS |
| ~-spelled attach monitors resolved root (SC4/CR-01) | pytest ::test_attach_tilde_spelled_monitors_resolved_root_real_scanner | passed | ✓ PASS |
| Re-run confirm names pairs × seeds (WR-03) | pytest ::test_rerun_confirm_names_pairs_times_seeds_estimate | passed | ✓ PASS |
| y-confirm gate happy path (EHC-2) | pytest ::test_gate_happy_path_confirms_and_launches | passed | ✓ PASS |
| Multi-root exit kills every live sweep (WR-05) | pytest ::test_exit_modal_multi_root_kills_every_live_sweep | passed | ✓ PASS |
| Enter-key pin: Inputs never launch | pytest ::test_enter_key_pin_inputs_never_launch | passed | ✓ PASS |
| Scanner contract after +190-line delta (SC4 data layer) | pytest 5 named ::tests in test_services_sweep_monitor.py | 5 passed | ✓ PASS |
| CLI headless parity (SC5) | `run_sweep.py --help` flag scan | all 13 flags present | ✓ PASS |
| Smoke artifacts on disk (SC5) | read finetuned-smoke/ + smoke-2x2-261014 trees | manifests + per-cell artifacts present, real values | ✓ PASS |
| Full suite / lint / typecheck / goldens on this exact tree | documented gates (refresh context; source unchanged since — tree clean at HEAD) | 1808 passed at the pinned 7F baseline; node 26/26; ruff+ty green; 9 goldens green unmodified | ✓ PASS (documented; not re-run per refresh instructions) |

**Total this pass: 25 named tests + 2 CLI/artifact scans, all green.**

### Probe Execution

N/A — no phase-declared or conventional probe scripts; this phase's evidence vehicles are the pytest Pilot/tier-1 harness, the executed GB10 UAT, and the post-delta demo recordings.

### Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| CFG-01 | 11-01/02/05/06 | ✓ SATISFIED | SC1 evidence; REQUIREMENTS.md [x] + traceability Complete |
| CFG-02 | 11-02/06/08 | ✓ SATISFIED | resolve_dirs basis; WR-01 pin green in the documented full run |
| CFG-03 | 11-02/06 | ✓ SATISFIED | same-source preview re-read this pass |
| LNC-01 | 11-05/06 | ✓ SATISFIED | tripwire green this pass (bilingual registry, both directions) |
| LNC-02 | 11-01/03/06/07/08 | ✓ SATISFIED | spawn pins + multi-root exit green this pass |
| LNC-03 | 11-02/03/06/07 | ✓ SATISFIED — strengthened | E2' phrase refusal green this pass on BOTH paths (spec + from-failures complete-manifest) |
| MON-01 | 11-04/05/07 | ✓ SATISFIED | scanner contract green this pass |
| MON-02 | 11-04/05/07/08 | ✓ SATISFIED | tilde attach pin green this pass |
| MON-03 | 11-04/05/07/08 | ✓ SATISFIED — strengthened | pairs × seeds pin green; + E2'-class re-run gate |
| MON-04 | 11-03/04/05/07/08 | ✓ SATISFIED | O_EXCL tee pin green this pass |
| MON-05 | 11-04/05/07 | ✓ SATISFIED | trainer_state markers on disk + UAT ⊘ proof |

REQUIREMENTS.md: all 11 phase requirements [x]; traceability rows Complete; zero orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | Zero TBD/FIXME/XXX/TODO/HACK across all 20 covered implementation files incl. the delta files; no stub patterns; the strings PLACEHOLDER-family hits are input-hint constants by design | — | — |

### Human Verification Required

None. SC5's human half (the maintainer-run GB10 smoke) was closed by the executed live UAT (2026-10-13, 11-UAT.md `status: passed`) and is further corroborated post-delta by the re-recorded launch-monitor-kill demo casts. No behavior-unverified truths remain — every behavior-dependent SC claim was exercised this pass by named passing tests, the documented full-suite gates on this exact tree, or live recorded execution.

### Gaps Summary

None. The refresh re-verification confirms the phase goal still holds at HEAD `8aacc58` after the c4j/ehc/h8i/pex/a4f/hhx delta: all five SCs verified against current code with 25 named behavioral tests green this pass, the same-source preview seam untouched, the launch gates strictly STRONGER than at the prior pass (y-confirm makes enter structurally inert on launch confirms; the E2'-class from-failures re-run now demands the typed phrase; the single-GPU serialization guard refuses at stage 0 on both launch paths), all six 11-08 hardening fixes surviving intact, the strings tripwire extended and green over the bilingual registry, goldens byte-untouched, and SC5 grounded by the executed UAT plus on-disk artifacts plus post-delta on-camera corroboration. The three WINDOWS items (#26, #27, #20's status column) are carried as advisories per the ledger — none breaches an SC.

---

_Verified: 2026-10-16T07:39:44Z_
_Verifier: Claude (gsd-verifier)_
