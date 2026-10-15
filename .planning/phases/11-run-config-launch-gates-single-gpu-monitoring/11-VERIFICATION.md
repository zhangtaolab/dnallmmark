---
phase: 11-run-config-launch-gates-single-gpu-monitoring
verified: 2026-10-14T17:17:48Z
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
covered_digest: "v3:sha256:b955133b985ca1f9bb2198bcdde6f539f7f03288e7f5f3817faf3f9b9e791385"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 4/5
  previous_verified: 2026-10-14T16:21:56Z
  gaps_closed:
    - "CR-01 (gap #1, blocker) — attach() stores Path(str(root)).expanduser().resolve(); a ~-spelled [a] attach now monitors the resolved root (independently reproduced by this pass over the real services + Pilot-pinned over the real scanner)"
    - "WR-01 (gap #2) — launch_spec registry key, tee rootname basis, and the CR-02 live-root pre-check all ride rc.resolve_dirs(spec).output_root_abs (independently reproduced this pass from a non-repo CWD: registry key == argv --output-root == live_sweeps())"
    - "WR-02 (gap #3) — ONE pure derive_rerun_seeds (failure seeds first, cell-row fallback, else empty) shared by the confirm and the launch worker; empty derivation refuses loudly (RerunFailed/MON_RERUN_NO_SEEDS) with the launcher provably uncalled; the silent [42] default is gone from tui/"
    - "WR-03 (gap #4) — the re-run confirm names pairs × seeds = n (the exact enumeration), pinned green alongside the launch receiving the same fan-out"
    - "WR-04 (gap #5) — the tee opens mode 'x' (O_EXCL) with a _1.._99 numeric-suffix fallback; the same-second same-basename pin proves the first log's sentinel survives and both registry entries stay live"
    - "WR-05 (gap #6) — ExitModal carries EVERY live root; [k] kills and [enter] detaches ALL before exit; LNC_EXIT_MESSAGE_MULTI (count + full resolved paths, done/total dropped); the single-root form byte-identical"
  gaps_remaining: []
  regressions: []
---

# Phase 11: Run Config, Launch Gates & Single-GPU Monitoring — Gap-Closure Re-Verification (Round 2)

**Phase Goal:** The operator's core loop is closed and safe — compose a complete run spec, preview it from the same pure planning functions execution uses, pass the env + confirmation gates, launch `run_sweep.py` as a detached subprocess, and monitor/recover the sweep from the same console — proven end-to-end by a maintainer-authorized bounded smoke on GB10, with E2' provably still maintainer-gated
**Verified:** 2026-10-14T17:17:48Z (HEAD `bdacbae`, branch `autorun`; working tree code-clean; the maintainer-authorized dnamamba subset smoke was RUNNING throughout — read-only)
**Status:** passed
**Re-verification:** Yes — round 2 after gap plan 11-08 (commits `0ea6ad7..bdacbae`, 9 commits). All six prior gaps flip-checked this pass; the two deterministic reproductions (CR-01, WR-01) re-executed by this verifier with standalone scripts, the four warning-class gaps confirmed behaviorally via their committed pins plus code reads.

## Goal Achievement

### Observable Truths (SC1-5, ROADMAP verbatim anchor)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **SC1** run-config screen: full parameter set + separated dirs + same-source dry-run preview with enumerated cell counts | ✓ VERIFIED | Re-confirmed at HEAD: `tui/services/run_config.py:115` module-level `import run_sweep`, `:907` `run_sweep.enumerate_matrix(...)` (zero re-implemented enumeration); `compose_argv` REPO_ROOT threading unchanged. Named lanes green this pass: `test_params_defaults_render`, `test_preview_line_renders_and_updates_on_mark`, `test_preview_modal_renders_argv_and_problems`, `test_importing_service_leaves_gpu_stack_absent` |
| 2 | **SC2** terraform-style launch gate: env preflight blocks with reason, preview precedes explicit confirm, E2' typed phrase unbypassable | ✓ VERIFIED | Refusal chain intact at HEAD (`sweep_launcher.py:596-613`): fresh preview → official-keys fail-closed → E2' exact phrase, each BEFORE the spawner; `launch_spec` now threads `rc.resolve_dirs(spec).output_root_abs` into `_spawn` (:611-613 — the WR-01 fix, verified below). Named lanes green this pass: `test_launch_from_failures_complete_manifest_three_seeds_demands_phrase`, `test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent` |
| 3 | **SC3** execution always a `run_sweep.py` subprocess (LIST argv + PYTHONUNBUFFERED=1 + start_new_session); exit kill/detach/cancel; detached sweeps resume-safe to re-attach | ✓ VERIFIED | `_spawn` pins unchanged: `list(argv)`, `start_new_session=True`, cwd=pipeline/, env PYTHONUNBUFFERED=1, stdout→tee/stderr→STDOUT (:521-530); `test_spawn_pins_list_argv_session_cwd_env_tee` green this pass. Exit triple now handles EVERY live root (WR-05 closed — exit lane 6/6 incl. the 4 original single-root tests byte-unmodified). LIVE grounding (read-only): detached parent `run_sweep.py --models plant-dnamamba-6mer --tasks PDLLMs…,plant-genomic-benchmark__gene_exp…` (PID 2750297) spawning child `run_finetune.py --target_model plant-dnamamba-6mer …` (PID 2750300) through this exact chain right now |
| 4 | **SC4** monitor dashboard: cell states via 2s/60s tolerant scans, stats/ETA, attach for CLI sweeps, gated re-run, bounded tail + tee, ⊘ resume | ✓ VERIFIED (was FAILED — CR-01 closed) | **CR-01 flip-checked by independent reproduction** (verifier script, temp HOME/state, REAL services): `add_manual_root('~/sweeps/run1')=True`; service still reads the literal (`cells_view(raw)=0`, `cells_view(resolved)=1` — the prior pass's shapes); `MonitorScreen.attach('~/sweeps/run1')` now stores the RESOLVED root (monitor.py:1184 `Path(str(root)).expanduser().resolve()`), `cells_view(stored)=1`, `attached_running_counts` returns the resolved string, identity attach stays identity. Committed Pilot pin `test_attach_tilde_spelled_monitors_resolved_root_real_scanner` (real MonitorBackend, `~` typed through the [a] modal, ◆ renders, cells row renders) green this pass. WR-02/03/04 rerun+tee hardening all pinned green (below). Full monitor/launcher/run_config/strings suites green in the full-suite run |
| 5 | **SC5** bounded smoke runs launch→monitor→failure-re-run E2E on GB10 while E2' demonstrably blocks; every capability headless via CLI | ✓ VERIFIED | The 2026-10-13 live 1×1×1 smoke stands (11-UAT.md status **passed**, maintainer-authorized; WINDOWS.md #20 closed). ADDITIONAL live grounding tonight: the 2×2 GB10 smoke's **dnabert half is COMPLETE with full artifacts** — `pipeline/finetuned/smoke-2x2-261014/plant-dnabert-6mer/{PDLLMs_datasets__plant-multi-species-open-chromatin, plant-genomic-benchmark__gene_exp.arabidopsis_thaliana}/seed_42/{final_metrics.json, flops_report.json}` (real values: train_runtime 1405s, total_flos 6.77e15, GB10 hardware block) — and the **dnamamba subset (5% fraction) is RUNNING detached** through this phase's chain (log `pipeline/logs/smoke-2x2-261014-dnamamba-subset.log` growing, cell 1 at 24%). E2'-blocks re-proven this pass (2 named gate tests green). CLI parity: all driver flags present in `run_sweep.py --help` (models/tasks/seeds/output/from/num_train_epochs/peft/config/curve/subset_file/train_fraction/effective_batch_size/priority/dry/registry/log_dir/model_root/dataset_root) |

**Score:** 5/5 truths verified (SC4 flipped FAILED → VERIFIED; zero behavior-unverified)

### Gap Flip-Check Detail (the six prior gaps)

| Gap | Flip-check method (this pass) | Result |
|-----|-------------------------------|--------|
| **#1 CR-01** attach stores raw path (blocker) | Verifier-owned standalone reproduction (temp HOME, real `sweep_monitor` + `MonitorScreen`): service-level shapes re-established identical to the failing pass (validation True / raw 0 rows / resolved 1 row), then `attach()` stores resolved, monitors 1 row, ExitModal seam sees resolved, identity preserved. Plus committed Pilot pin over the REAL scanner (`~` typed through the [a] modal; DEFAULT_OUTPUT_ROOTS pinned empty — hermetic) | ✓ CLOSED |
| **#2 WR-01** registry key CWD-basis | Verifier-owned standalone reproduction: CWD=temp dir, `spec.output_root="finetuned"`, fake spawner → `outcome.root == argv --output-root == live_sweeps() == {repo}/finetuned` (pre-fix: `{tmp}/finetuned` vs argv `{repo}/finetuned`). Screen pre-check reads `resolve_dirs(spec).output_root_abs` (run_config.py:1910). Pins `test_launch_spec_registry_key_rides_repo_root_basis_from_any_cwd` + `test_gate_live_root_precheck_reads_repo_root_basis_any_cwd` green | ✓ CLOSED |
| **#3 WR-02** silent `[42]` seed default | `derive_rerun_seeds` (monitor.py:768-798): failures-first, cell-rows fallback, else `()`; consumed by BOTH `request_rerun` (:1222) and the worker's own `failures_view` re-read (:1298); empty → `RerunFailed(MON_RERUN_NO_SEEDS)` + return BEFORE the launcher (:1299-1302); E2' re-prompt re-invokes and re-derives identically (:1336). `grep 'or [42]' tui/` → zero code hits. Pins: seeds `(43,)` from failure rows with EMPTY cells; refuse-loudly with `rerun_calls == []` — both green | ✓ CLOSED |
| **#4 WR-03** confirm understates spend | `request_rerun` computes `pairs = len({(row.model, row.task)})` and formats `n = pairs × len(seeds)` (:1223-1228) over the SAME derivation the worker uses; MON_RERUN_CONFIRM amended in place (strings.py:1011-1014). Pin: 2 pairs × 2 seeds → copy carries `pairs=2, seeds="42, 43", n=4` AND the launch receives `(42, 43)` — green | ✓ CLOSED |
| **#5 WR-04** tee same-second collision | `_spawn` opens the tee mode `"x"` (O_EXCL) with `_1.._99` suffix retry (TEE_COLLISION_SUFFIX_CAP=99; exhausted cap rides the OSError refusal — sweep_launcher.py:496-520). Pin: two same-basename roots at one FixedClock moment → first name byte-identical (`sweep_20261013_083005_finetuned.log`), second `_1`-suffixed, the first log's SENTINEL survives, both registry entries live — green; existing FixedClock name pins unmodified | ✓ CLOSED |
| **#6 WR-05** ExitModal single-root | ExitModal normalizes `roots` to a tuple (:203-207); `action_detach_quit`/`action_kill_quit` loop over EVERY root then `app.exit()` (:220-232); `action_quit` uses `LNC_EXIT_MESSAGE_MULTI` (count + full resolved paths, done/total dropped) when `len(roots) > 1`, byte-identical `LNC_EXIT_MESSAGE` otherwise (app.py:859-876). Pins: multi-root `[k]` kills both / `[enter]` detaches both — green; exit lane 6/6 (4 original single-root tests byte-unmodified) | ✓ CLOSED |

**Sanctioned pin change audited:** `test_rerun_confirm_routes_launch_from_failures_and_attaches` seeds assertion `(42, 43) → (42,)` is exactly the documented WR-02 semantics change (failure-referenced seed set only; confirm names what will run); the rationale comment was updated in the same change — matches 11-08-SUMMARY's record.

### Advisory (carry-forward; re-verification ran)

No NEW advisory findings this pass (zero debt markers, zero stubs, lint/typecheck clean). Prior info-tier advisories carried forward unchanged, still open in 11-REVIEW-DISPOSITION.md as non-goal-breaking polish:

| # | Finding | Status this pass |
|---|---------|------------------|
| IN-01 | LNC_E2_WARNING hardcodes 59×50×8850 (copy-drift risk; gate predicate computes fresh) | Unchanged (info-tier; not a gap) |
| IN-02..05 | stale NAV comment / dead expected_seeds param / curve records unread / `__` join key | Unchanged (info-tier; not gaps) |
| env-only test | `test_storage_overview_defaults_mirror_real_consumers` fails while the live smoke runs (`pipeline/logs` exists vs fresh-checkout assertion; production behavior correct) | Reproduced in this pass's baseline run — still one of the known 7 |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tui/screens/monitor.py` | attach resolution; shared seed derivation; confirm estimate | ✓ VERIFIED | :1184 expanduser().resolve(); :768 derive_rerun_seeds; :1222/:1298 both consumers; refuse-loudly :1299-1302 |
| `tui/services/sweep_launcher.py` | REPO_ROOT-basis root threading; O_EXCL tee | ✓ VERIFIED | :611-613 resolve_dirs(spec).output_root_abs; :496-520 mode "x" + suffix fallback |
| `tui/screens/run_config.py` | CR-02 pre-check on the resolve_dirs basis | ✓ VERIFIED | :1910 (Protocol seam :238/:322) |
| `tui/app.py` | ExitModal multi-root kill/detach + multi message | ✓ VERIFIED | :203-232 loop-all; :868-876 multi/single fork |
| `tui/strings.py` | MON_RERUN_NO_SEEDS + LNC_EXIT_MESSAGE_MULTI; MON_RERUN_CONFIRM amended | ✓ VERIFIED | :926, :1011, :1019; registered in EXPECTED_LNC_/EXPECTED_MON_ (test_strings_phase11.py:74,95) |
| `tests/tui/*` (4 pin files) | The six gaps pinned | ✓ VERIFIED | 9 named gap pins all green this pass |
| `pipeline/run_sweep.py`, remaining phase files | Unchanged contract | ✓ VERIFIED | Full suite green at baseline; snapshots byte-untouched |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| [a] PathInputModal on_submit | attach → expanduser().resolve() → every reader | ✓ WIRED | Verifier reproduction + Pilot pin (◆ matches the discovered-table key; cells/failures/stats read a real path) |
| launch_spec | rc.resolve_dirs(spec).output_root_abs → _spawn registry key == argv basis == auto-attach key | ✓ WIRED | Verifier reproduction: one basis across outcome.root / argv --output-root / live_sweeps() |
| FailuresModal [r] | request_rerun → shared derivation → _run_rerun_launch → launch_from_failures | ✓ WIRED | Confirm estimate and launch provably share ONE derivation (pin asserts both) |
| action_quit (multi-root) | ExitModal(roots) → kill/detach per root → app.exit() | ✓ WIRED | Pins: kill_calls/detach_calls == [root_a, root_b] |
| run_config service → run_sweep; launcher → env_gate/quick_check; monitor → run_sweep artifact names | unchanged seams | ✓ WIRED | Re-confirmed via named lanes + full suite |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| monitor cell table | cells_view at the attached root | run_record.json/manifest on disk | Yes — now through the RESOLVED root (CR-01 closed; reproduction shows 1 row) | ✓ FLOWING |
| live smoke chain | child argv + artifacts | parent run_sweep argv → per-cell outputs | Yes — dnabert final_metrics/flops_report on disk with real values; dnamamba subset mid-training | ✓ FLOWING |
| re-run confirm copy | pairs/seeds/n | FailureRow.seed via derive_rerun_seeds | Yes — pin asserts copy and launch agree | ✓ FLOWING |

### Behavioral Spot-Checks (all run this pass at HEAD `bdacbae`)

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| CR-01 flip (verifier-owned reproduction) | standalone script, temp HOME/state, real services | attach stores resolved; cells_view(stored)=1; counts root resolved; identity preserved | ✓ PASS |
| WR-01 flip (verifier-owned reproduction) | standalone script, non-repo CWD, fake spawner | outcome.root == argv root == live_sweeps() == {repo}/finetuned | ✓ PASS |
| The 9 gap pins (CR-01 Pilot, WR-01 ×2, WR-02 ×2, WR-03, WR-04, WR-05 ×2) | pytest named tests | 4 + 5 passed | ✓ PASS |
| SC1/SC2/SC3 named lanes + strings inventory | 12 named tests (incl. full test_strings_phase11.py) | 12 passed | ✓ PASS |
| Exit-triple regression lane | `pytest tests/tui/test_pilot_run_config.py -k exit` | 6 passed (4 original single-root byte-unmodified + 2 multi-root) | ✓ PASS |
| Full suite vs box baseline | `uv run --group dev --group tui pytest -q` | **7 failed / 1743 passed / 9 xfailed in 276s** — exactly the baseline: test_determinism + 5×test_schemas (pre-existing data-side) + the documented env-only storage_overview failure; ZERO new failures | ✓ PASS |
| lint / typecheck | `make lint` / `make typecheck` | All checks passed (both) | ✓ PASS |
| Live smoke evidence (read-only) | ps + artifact reads | dnabert half complete (2 cells × final_metrics + flops_report, real values); dnamamba subset detached + training (24% cell 1); log growing | ✓ PASS |
| Goldens + live-smoke paths untouched | `git status tests/tui/__snapshots__/ pipeline/ tui/ tests/` | clean (byte-untouched) | ✓ PASS |

### Probe Execution

N/A — no phase-declared or conventional probe scripts; this phase's evidence vehicles are the pytest Pilot/tier-1 harness, the verifier reproductions, and the maintainer-run smokes.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CFG-01 | 11-01/02/05/06 | Full parameter surface | ✓ SATISFIED | SC1 evidence; lanes green |
| CFG-02 | 11-02/06/08 | Dirs separation (D-14) | ✓ SATISFIED | compose_argv REPO_ROOT threading + WR-01 closed (registry key now the same basis from ANY CWD) |
| CFG-03 | 11-02/06 | Same-source preview | ✓ SATISFIED | D-05 wiring + purity test green |
| LNC-01 | 11-05/06 | Gate copy + presentation | ✓ SATISFIED | strings tripwire green (incl. the two new names) |
| LNC-02 | 11-01/03/06/08 | Subprocess discipline + exit triple | ✓ SATISFIED | SC3 evidence; WR-05 closed (exit triple correct under multi-sweep state) |
| LNC-03 | 11-02/03/06/07 | E2' unbypassable | ✓ SATISFIED | SC2 gate tests green |
| MON-01 | 11-04/05/07 | Cell states, 2s/60s tolerant scans | ✓ SATISFIED | suites green |
| MON-02 | 11-04/05/07/08 | Stats + CLI-sweep attach | ✓ SATISFIED (was NOT) | CR-01 closed — attach validates AND monitors one path basis |
| MON-03 | 11-04/05/07/08 | Live failures + confirm-gated re-run | ✓ SATISFIED | WR-02/03 closed — failure-derived seeds, honest pairs × seeds confirm, loud refusal |
| MON-04 | 11-04/05/07/08 | Log tail + tee persistence | ✓ SATISFIED | WR-04 closed — O_EXCL uniqueness; tee/tail lanes green |
| MON-05 | 11-04/05/07 | ⊘ resume recognition | ✓ SATISFIED | tests + live UAT round trip |

REQUIREMENTS.md: all 11 phase requirements [x]; zero unchecked; no orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | Zero TBD/FIXME/XXX across all phase files; PLACEHOLDER grep hits are UI input-hint constants (MON_ATTACH_PLACEHOLDER, SEL_FILTER_PLACEHOLDER, NAV_PLACEHOLDER_TOAST), not stubs | — | — |

### Human Verification Required

None. The prior pass's single human item (GB10 smoke execution) was closed by the live 2026-10-13 UAT; tonight's running smoke provides additional live grounding (read-only). No behavior-unverified truths remain — every behavior-dependent gap claim was exercised by a passing behavioral test or a verifier-executed reproduction this pass.

### Gaps Summary

None. All six prior gaps closed and flip-checked at HEAD `bdacbae`: the CR-01 blocker and WR-01 were re-reproduced independently by this verifier and now exhibit the fixed behavior (one path basis from validation through every reader; one REPO_ROOT basis across argv/registry/pre-check/auto-attach), and WR-02..05 are pinned green with the exact adversarial shapes the gaps described (failure-derived seeds with loud refusal, pairs × seeds confirm, O_EXCL tee with sentinel survival, all-roots exit). Full suite at the exact box baseline (7 failed / 1743 passed / 9 xfailed, zero new), lint/typecheck clean, goldens and live-smoke paths byte-untouched, and the phase's end-to-end proof is grounded by the live GB10 smoke running through this chain right now (dnabert half complete with full artifacts; dnamamba subset in flight).

---

_Verified: 2026-10-14T17:17:48Z_
_Verifier: Claude (gsd-verifier)_
