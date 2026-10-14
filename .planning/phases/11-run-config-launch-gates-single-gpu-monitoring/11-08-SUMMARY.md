---
phase: 11-run-config-launch-gates-single-gpu-monitoring
plan: "08"
subsystem: ui
tags: [gap-closure, cr-01-attach-path, wr-01-registry-basis, wr-02-rerun-seeds, wr-03-confirm-estimate, wr-04-tee-collision, wr-05-multi-root-exit, monitor, launcher, tdd, phase-11-gaps]
status: complete
requires:
  - phase: 11-04
    provides: the pure scanner (cells_view/failures_view/is_sweep_root/add_manual_root — the real-scanner CR-01 fixture's substrate)
  - phase: 11-03
    provides: SweepLauncher._spawn/launch_spec/launch_argv (the registry-key and tee seams WR-01/WR-04 harden)
  - phase: 11-06
    provides: the CR-02 live-root pre-check site + RunConfigServiceProtocol.resolve_dirs (the seam the WR-01 screen fix reads)
  - phase: 11-07
    provides: MonitorScreen.attach/request_rerun/_run_rerun_launch, app.action_quit/ExitModal, the Pilot fake idioms this plan extends
  - phase: 11-05
    provides: the strings single home + the bidirectional inventory tripwire (the same-change registration precedent)
provides:
  - CR-01 closed — MonitorScreen.attach() stores Path(str(root)).expanduser().resolve() (validation and attach agree on ONE path basis); Pilot-pinned by a ~ -spelled [a] case over the REAL MonitorBackend/scanner (temp HOME/state, DEFAULT_OUTPUT_ROOTS pinned empty)
  - WR-01 closed — launch_spec threads rc.resolve_dirs(spec).output_root_abs into _spawn (the argv's REPO_ROOT basis) and the slot-4 CR-02 pre-check reads the same seam; service-pinned from a non-repo CWD (registry key == argv --output-root == live_sweeps())
  - WR-02/WR-03 closed — ONE pure derive_rerun_seeds(failures, cell_rows) (distinct FailureRow.seed first, cell-row seeds fallback, else empty) used by BOTH the confirm estimate and the launch worker; an empty derivation posts RerunFailed(MON_RERUN_NO_SEEDS) with the launcher provably uncalled; MON_RERUN_CONFIRM amended in place to the pairs × seeds = n planned-cell estimate
  - WR-04 closed — the tee opens mode "x" (O_EXCL) with a numeric-suffix fallback (_1.._99; an exhausted cap rides the OSError refusal branch); same-second same-basename spawns get distinct files with the first log's content intact, non-colliding names byte-identical
  - WR-05 closed — ExitModal carries EVERY live root (a bare str normalizes to a one-root tuple); [k] kills and [enter] detaches ALL roots then exits; LNC_EXIT_MESSAGE_MULTI (count + full resolved paths, done/total dropped) when len(roots) > 1; the single-root form byte-identical
  - strings inventory — MON_RERUN_NO_SEEDS + LNC_EXIT_MESSAGE_MULTI registered in EXPECTED_MON_/EXPECTED_LNC_ in the same changes (the bidirectional lock stays green)
affects: [Phase 11 re-verification (this SUMMARY is the per-gap before/after record), MON-02/MON-03/MON-04/CFG-02/LNC-02 evidence]

actuals:
  tokens: 12143   # chars/4 over the realized diff (48572 chars, 9 files; plan estimate 78000 — over-estimated)
  tasks: 3
  commits: 8      # measured: git rev-list --count 7d4c03b..HEAD (the docs commit follows)
plan_head_before: 7d4c03b45c264ad6bf50a68eb6cb1ff36a50a8f1
plan_head_after: 320cb97

tech-stack:
  added: []   # zero packages, zero new modules (the surgical-fix prohibition held)
  patterns:
    - "one-path-basis attach: the screen-tier attach applies the SAME expanduser().resolve() the validation service applied — every downstream key comparison (◆ marker, ExitModal, frontier target) sees the resolved root; an already-absolute resolved key passes through as identity"
    - "one-derivation authorization: a pure module-level derive_rerun_seeds consumed by BOTH the confirm-side estimate and the launch worker — the confirmed GPU spend and the executed GPU spend cannot drift; empty derivation refuses loudly (RerunFailed), never a default"
    - "filesystem-level tee uniqueness: mode 'x' (O_EXCL) + numeric-suffix retry — unique per spawn across processes, sessions, AND the same-process race (a pid suffix would not disambiguate two spawns from one TUI process)"

key-files:
  created: []
  modified:
    - tui/screens/monitor.py
    - tui/services/sweep_launcher.py
    - tui/screens/run_config.py
    - tui/app.py
    - tui/strings.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_services_sweep_launcher.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_strings_phase11.py

key-decisions:
  - "attach() owns the resolution; the three call sites stay untouched (note_launch's pre-resolution kept as a documented no-op; the discovered-table enter passes already-resolved keys — identity; action_attach_path keeps passing the raw modal value)"
  - "WR-04 chose O_EXCL + numeric suffix over a pid/registry-counter suffix: uniqueness at the filesystem level is robust across processes and sessions, and a pid suffix would NOT disambiguate the stated slot-4-vs-monitor-[r] race (both spawns from the same TUI process); a same-second same-root reclaim now appends a suffix instead of truncating the killed sweep's audit log — strictly better"
  - "MON_RERUN_CONFIRM amended IN PLACE (name unchanged, inventory entry stands; the 11-05 ENV_VERDICT amendment precedent) — the WR-03 estimate needed new format fields (pairs/seeds/n), not a second constant"
  - "LNC_EXIT_MESSAGE_MULTI drops the done/total fields: per-root counts from ONE attached root would mix sources (the review's finding); the count + full resolved paths carry the multi-root truth"
  - "The CR-01 Pilot pin monkeypatches sweep_monitor.DEFAULT_OUTPUT_ROOTS to () — the backend/scanner stay REAL while discovery stays hermetic (the repo default roots include the live smoke's pipeline/finetuned, read-only territory the lane never walks)"

---

# Phase 11 Plan 08: Gap Closure (CR-01 attach resolve + WR-01..05 operator-safety hardening) Summary

**One-liner:** The six stale-refresh gaps closed on the monitor/launcher seam — a `~`-spelled attach now monitors the resolved root over the real scanner, the registry key rides the argv's REPO_ROOT basis, re-run seeds derive from failure rows through one shared derivation with a pairs × seeds confirm, the tee opens O_EXCL, and the exit modal kills/detaches every live root.

**Plan:** 11-08 | **Tasks:** 3/3 | **Duration:** ~32 min

All three tasks executed TDD (RED reproduction committed first, then the fix; the two verifier-reproduced gaps landed their deterministic REDs exactly as the verification pass staged them).

## Per-Gap Before/After (the re-verification record)

| Gap | Before (the reproduction) | After (the pin) | Commits |
|-----|---------------------------|-----------------|---------|
| **#1 CR-01** (blocker) | `attach()` stored `Path(str(root))` — a `~/sweeps/run1` root VALIDATED (add_manual_root resolves internally), toasted success, then every reader read the literal nonexistent path. RED (over the REAL MonitorBackend/scanner, temp HOME/state): `_attached_root == '~/sweeps/run1'`, empty cells region | attach stores `Path(str(root)).expanduser().resolve()`; `test_attach_tilde_spelled_monitors_resolved_root_real_scanner` — modal dismisses, stored root == resolved, ◆ renders on the discovered row, the run_record's (model, task) row renders in cells; every absolute-path attach test passes byte-unmodified | 40faee0 / aca912e |
| **#2 WR-01** | launch_spec passed RAW `spec.output_root` to `_spawn` (CWD-based key) while compose_argv threads REPO_ROOT. RED (service, CWD != repo): `outcome.root == {tmp}/finetuned` vs argv `{repo}/finetuned`; screen pre-check slipped past to the confirm (`_GateConfirmModal` not `ProblemsModal`) | launch_spec threads `rc.resolve_dirs(spec).output_root_abs`; the slot-4 pre-check reads the same Protocol seam. `test_launch_spec_registry_key_rides_repo_root_basis_from_any_cwd` (registry key == argv root == live_sweeps()) + `test_gate_live_root_precheck_reads_repo_root_basis_any_cwd` (the gate FIRES naming the REPO_ROOT key); the existing repo-CWD lane green unmodified; RunConfigDouble gains resolve_dirs | 40faee0 / aca912e |
| **#3 WR-02** | `_run_rerun_launch` derived seeds from `_cell_rows or [42]` — empty cell table → silent `[42]`. RED: empty cells + a seed-43 failure row → launch received `(42,)`; the staged empty worker re-read → the re-run LAUNCHED (no refusal) | ONE pure `derive_rerun_seeds(failures, cell_rows)`; the worker re-derives over its own failures_view re-read. `test_rerun_seeds_derive_from_failure_rows_not_a_default` (launch receives `(43,)`) + `test_rerun_underivable_seeds_refuses_loudly_never_launches` (the MON_RERUN_NO_SEEDS toast fires under LNC_LAUNCH_FAILED_TOAST's ✗ prefix; `rerun_calls == []`); the E2' re-prompt path re-invokes and re-derives identically | 4adb526 / 1c69cba |
| **#4 WR-03** | the confirm named `len(failures)` ENTRIES while the launch enumerates pairs × seeds (~3x understated). RED: 2 pairs × 2 seeds rendered "重跑 2 个失败 cell" then launched 4 cells | `request_rerun` computes pairs × seeds over the shared derivation; MON_RERUN_CONFIRM amended in place ("重跑 {pairs} 个失败组合 × 种子 {seeds} = {n} 个 cell…"). `test_rerun_confirm_names_pairs_times_seeds_estimate` — the confirm copy carries pairs=2/seeds="42, 43"/n=4 AND the launch receives `(42, 43)` (confirm and launch provably share ONE derivation) | 4adb526 / 1c69cba |
| **#5 WR-04** | tee opened mode `"w"` — two same-basename roots spawned in one second shared ONE file. RED: both spawns returned the IDENTICAL tee path and the sentinel written into the first log was lost to the second's truncating open | mode `"x"` (O_EXCL) + `_1.._99` suffix fallback (TEE_COLLISION_SUFFIX_CAP; exhausted cap rides the OSError refusal). `test_spawn_same_second_same_basename_never_shares_tee_file` — first name byte-identical (`sweep_20261013_083005_finetuned.log`), second suffixed (`_1`), the sentinel SURVIVES, both entries live; the existing FixedClock name pins and the same-root reclaim test green unmodified | 88186ff / 7e5af59 |
| **#6 WR-05** | action_quit built ExitModal around `roots[0]`; `[k]`/`[enter]` acted on one root. RED: two live roots → the single-root message (done/total + "finetuned") and `detach_calls == [root_a]` only | ExitModal carries every root (str → one-root tuple); kill/detach loop ALL then exit; LNC_EXIT_MESSAGE_MULTI (n + full resolved paths joined, done/total dropped) when `len(roots) > 1`. `test_exit_modal_multi_root_kills_every_live_sweep` + `test_exit_modal_multi_root_enter_detaches_every_live_sweep`; the four single-root exit-triple tests byte-unmodified; the attached-running-only path unchanged | 88186ff / 7e5af59 |

## TDD Gate Compliance

Every task's RED evidence is the real command's target-assertion failure (gsd_run's classifier is unavailable on this box — the raw reproductions are preserved in the commit messages and the table above):

- Task 1 RED: 3 failed — `'~/sweeps/run1' == '/tmp/…/home/sweeps/run1'` (CR-01); `{tmp}/finetuned != {repo}/finetuned` (WR-01 service); `_GateConfirmModal` ≠ `ProblemsModal` (WR-01 screen).
- Task 2 RED: 4 failed — `(42, 43) != (42,)` (the sanctioned pin); `(42,) != (43,)` (the silent default); the re-run LAUNCHED where refusal was demanded; "重跑 2 …" rendered where "重跑 4 …" (pairs × seeds) was named.
- Task 3 RED: 3 failed — identical tee paths (the shared-file collision); the single-root message under two live roots; `['/repo/a/finetuned'] != ['/repo/a/finetuned', '/repo/b/finetuned']`.

## Sanctioned Pin Change

`test_rerun_confirm_routes_launch_from_failures_and_attaches` seeds assertion **(42, 43) → (42,)** — with cells `{42: FAILED, 43: QUEUED}` but the single failure row at seed 42, the launch now receives the failure-referenced seed set. Documented semantics change (WR-02): alias seeds whose cells never failed are no longer silently re-attempted, and the confirm names exactly what will run. The assertion's rationale comment was updated in the same change.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] app.py docstring violated the i18n lock**
- **Found during:** plan-level gate 4 (the first full-suite run: 8 failed — one ABOVE baseline)
- **Issue:** the WR-05 ExitModal docstring quoted the [k] key's Chinese label (终止后退出) verbatim; `test_app_module_carries_zero_chinese_literals` scans source text including docstrings
- **Fix:** reworded to the key description ("kill-and-quit") — operator-facing copy lives in tui/strings.py only (commit 320cb97); the re-run full suite returned to the exact 7-failure baseline
- **Files modified:** tui/app.py

**2. [Rule 1 - Bug] ruff findings on the new pins**
- **Found during:** plan-level gate 1 (make lint)
- **Issue:** UP032 (a join→f-string in the WR-05 message assertion) + F841 (an unused state-dir variable in the WR-04 pin)
- **Fix:** commit d6241ab (the pins' behavior untouched)
- **Files modified:** tests/tui/test_pilot_run_config.py, tests/tui/test_services_sweep_launcher.py

Otherwise: none — the fixes landed exactly as the plan's action elements specified. FakeMonitorService was extended with the plan-sanctioned per-call failures staging (a LIST value = a sequence of reads; a TUPLE stays one sticky read — every pre-existing fixture shape unmodified).

## Verification Evidence

| Gate | Command | Result |
|------|---------|--------|
| lint | `make lint` | All checks passed (after d6241ab) |
| typecheck | `make typecheck` (ty, --group dev --group tui) | All checks passed |
| Task lanes | per-task `-q` runs | 137 / 43 / 110 passed |
| Targeted gap lanes | pytest test_pilot_monitor + test_pilot_run_config + test_services_sweep_launcher + test_strings_phase11 + test_services_sweep_monitor + test_import_lock | **198 passed** |
| Full suite | `uv run --group dev --group tui pytest -q` | **7 failed / 1743 passed / 9 xfailed** = the box baseline failure class (7) + 9 new passing tests; zero new failures |
| Snapshots | `git status tests/tui/__snapshots__/` after the full suite | clean — byte-untouched |
| Live smoke | `git status pipeline/` + the sweep process alive | clean / running (undisturbed; smoke-2x2-261014 + pipeline/logs read-only throughout) |

The 7 baseline failures are the known box class: `test_determinism` + 5 × `test_schemas` (pre-existing data-side failures — those test files import zero tui code and the plan range touches only `tui/` + `tests/tui/`, proven by `git diff --name-only 7d4c03b..HEAD`) and `test_storage_overview_defaults_mirror_real_consumers` (the documented env-only failure: `pipeline/logs` exists because the live smoke runs).

## Known Stubs

None — no stubs, no skipped tests, no unrun verifies.

## Threat Flags

None — all five threat-register mitigations (T-11-08-01..05) implemented exactly as planned; no new security surface beyond the plan's model.

## Requirements

CFG-02, LNC-02, MON-02, MON-03, MON-04 — the gap-closure evidence above closes the logged gaps against each (MON-02's attach seam, MON-03's re-run authorization honesty, MON-04's tee integrity, CFG-02/LNC-02's exit-triple and root-basis discipline).

## Self-Check: PASSED

All 10 created/modified files exist; all 8 plan commits are ancestors of HEAD (verified via `git merge-base --is-ancestor`).
