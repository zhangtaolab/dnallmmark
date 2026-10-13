---
phase: 11-run-config-launch-gates-single-gpu-monitoring
plan: 03
subsystem: tui-services
tags: [sweep-launcher, spawner-seam, detached-popen, tee, killpg, env-preflight, e2x-gate, typed-phrase, from-failures, lnc, mon]
requires:
  - phase: 11-02
    provides: compose_argv/compose_from_failures_argv (consumed VERBATIM), is_full_e2x/expected_phrase/phrase_matches re-proven pre-spawn, PreviewResult.problems + OfficialKeys.diagnostic block conditions, the exported machine vocabulary
  - phase: 10-01
    provides: the _default_spawner (698-712) + _signal_group (870-878) Popen/killpg discipline copied verbatim
  - phase: 08-04
    provides: quick_check.run_quick_check + env_gate.gate_verdict — the FROZEN face consumed with zero edits (D-08) — and settings.state_dir (the D-10 tee root's parent)
  - phase: 11-04
    provides: full_scan/frontier_scan live_roots injection — this plan's live_sweeps() is its Popen-alive source
provides:
  - tui/services/sweep_launcher.py — the launch lifecycle service: SweepLauncher (injectable-spawner detached Popen with the D-10 single-root tee, the root→{handle, meta, tee} live registry, kill_sweep SIGTERM/SIGKILL-escalation, detach, live_sweeps/tee_path_for), env_preflight over the frozen phase-8 face, gate_confirm_data fresh recompute, launch_spec (the structural E2' phrase gate — refusal stages ordered BEFORE the spawner), launch_argv (the raw from-failures-only seam), launch_from_failures (D-11)
  - the outcome/refusal vocabulary (LaunchOutcome/EnvPreflight/GateSummary/GateRefusal/LiveSweep frozen dataclasses + PROBLEM_OFFICIAL_KEYS) as the 11-06/11-07 screens' launch data contract
affects: [11-06 run-config screen (its [enter] launch gate calls env_preflight -> gate_confirm_data -> launch_spec; the toast/ExitModal consume LaunchOutcome/GateRefusal/live_sweeps), 11-07 monitor screen ([r] re-run calls launch_from_failures; [t] tail sources tee_path_for; the ExitModal kill/detach consumes kill_sweep/detach; live_sweeps feeds the monitor's Popen-alive scans)]

actuals:
  tokens: 14600   # chars/4 over the realized diff (58373 chars, 2 files)
  tasks: 3
  commits: 6      # measured: git rev-list --count fea8eac..HEAD
plan_head_before: fea8eac5d3ac148b2c4ef12deca8c5941399e53d
plan_head_after: 7a3430f

tech-stack:
  added: []   # stdlib + the existing settings/quick_check/env_gate/run_config seams only; zero packages installed
  patterns:
    - "verbatimum seam reuse: _default_spawner/_signal_group copied byte-for-byte from download_queue (the phase-10 process-group discipline, already proven)"
    - "refusal-before-spawn ordering proven by SPAWNER CALL COUNTS, not return shapes (the LNC-03 evidence style)"
    - "registry entry holds the tee file reference — the parent-side descriptor stays open for the child's lifetime; the launcher never pumps or closes it early (the monitor tails by path)"

key-files:
  created:
    - tui/services/sweep_launcher.py
    - tests/tui/test_services_sweep_launcher.py
  modified: []

key-decisions:
  - "launch_spec blocks on the official-keys diagnostic as a stage-problems refusal carrying an (official_keys, diagnostic) machine tuple — PROBLEM_OFFICIAL_KEYS extends run_config's vocabulary locally; fail-closed means an unreadable reference can never satisfy the E2' predicate by vacuity (the 11-02 handoff's block-on-diagnostic condition)"
  - "kill/detach release the parent-side tee descriptor on drop (_drop_entry) — closing the parent copy neither kills nor truncates: the child writes through its own inherited descriptor; keeping the reference in the registry entry (not a bare local) pins the fd open for the child's lifetime, honoring the never-close-early contract without leaking handles past detach"
  - "kill_grace/kill_interval are constructor-injectable (defaults 2.0s/0.05s): the poll-with-short-grace budget is real in production but tests must not sleep it — the escalation test runs at grace 0"
  - "requirements LNC-02/LNC-03/MON-04 left Pending (the 11-01 revert discipline): this plan delivers their load-bearing service tier (the subprocess mechanics + exit triple, the non-bypass structural gate, the D-10 tee persistence), but each requirement text names screen-visible surface (the TUI exit prompt, the typed-phrase modal presentation, the on-screen RichLog tail) landing in 11-06/11-07 — marking now would write a false Complete traceability row"
  - "the E2'-shaped-argv-not-refused proof is pinned over the REAL official registries (62x50 names in --models/--tasks through launch_argv) — the raw seam's no-gate property is documented in its docstring warning exactly as the plan-checker's obs 3 required"

patterns-established:
  - "the gate's refusal chain is ordered and each stage precedes the spawner: preview problems -> official-keys diagnostic -> E2' phrase — spawner-silence is asserted per stage"
  - "fake kernels are zero-arg callables returning CheckResult (the run_quick_check injectable contract), not CheckResult instances — the frozen face's seam shape is the test's to conform to, never the service's"

requirements-completed: []   # LNC-02/LNC-03/MON-04 service tier landed here; screen-visible surface lands 11-06/11-07 (see key-decisions)

coverage:
  - id: D1
    description: "Spawner seam + detached tee Popen + kill/detach registry (Task 1)"
    requirement: LNC-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_sweep_launcher.py (lane 1: 12 tests — LIST argv/start_new_session/pinned cwd/PYTHONUNBUFFERED env/stdout+stderr->tee pins, D-10 naming with injected clock + rootname, registry roundtrip, OSError no-log path, SIGTERM clean exit, SIGKILL escalation, already-dead + killpg race absorption, detach no-signal drop, tee_path_for unavailable state)"
        status: pass
      - kind: unit
        ref: "tests/tui/test_import_lock.py (glob auto-extends over the new module) — textual-free"
        status: pass
  - id: D2
    description: "Env preflight (frozen face) + fresh recompute + E2' phrase gate + launch_spec (Task 2)"
    requirement: LNC-03
    verification:
      - kind: unit
        ref: "lane 2: 17 tests — all-ok/critical-block/routing-advisory/multi-failure-order/unknown-kernel preflight over fake kernels, frozen-face delegation spies, gate_confirm_data fresh recompute + GateSummary, problems/diagnostic/phrase(absent, wrong, case-mismatched) refusals ALL with zero spawner calls, matching-phrase + non-E2'-real-module spawns with compose_argv verbatim, recompute-despite-screen-preview spy delta, launch_argv passthrough"
        status: pass
      - kind: unit
        ref: "tests/tui/test_services_env_gate.py + tests/tui/test_services_quick_check.py — the frozen-face consumers' suites green (zero regressions; the face itself edited zero bytes)"
        status: pass
  - id: D3
    description: "From-failures launch path + full gates (Task 3)"
    requirement: MON-03
    verification:
      - kind: unit
        ref: "lane 3: 3 tests — composed argv reaches the fake spawner (resolved failures path, seeds, absolute root, alias flags, tee named after the re-run root), the E2'-shaped --models/--tasks argv via launch_argv NOT refused (the D-11 construction proof)"
        status: pass
      - kind: other
        ref: "make test 1411 passed (running baseline + 32) + JS lane 18/18; make lint All checks passed; make typecheck All checks passed"
        status: pass
  - id: D4
    description: "Threat mitigations T-11-03-01..06"
    requirement: LNC-03
    verification:
      - kind: unit
        ref: "test_launch_spec_e2x_wrong_phrase_refuses_spawner_silent + test_launch_spec_e2x_absent_phrase_refuses + test_launch_spec_e2x_phrase_match_is_exact (T-01, zero spawner calls each); test_launch_spec_recomputes_despite_screen_preview (T-02); test_env_preflight_critical_failure_blocks_with_details (T-03); test_spawn_pins_list_argv_session_cwd_env_tee PYTHONUNBUFFERED pin (T-04); test_kill_sweep_* killpg/escalation/race (T-05); D-10 single-root tee pinned under state_dir()/logs with no second root (T-06); SC vacuous — zero installs"
        status: pass

---

# Phase 11 Plan 03: Sweep Launcher Summary

Landed `tui/services/sweep_launcher.py` — the execution tier of the operator loop: the injectable-spawner detached Popen with the D-10 single-root tee, the live-sweep registry with kill/detach semantics, the env preflight over the frozen phase-8 face, and the structurally-enforced E2' phrase gate — plus the D-11 from-failures launch path sharing the same seam. Proven by a 32-test tier-1 suite over fake spawners/fake kernels (TDD RED→GREEN per task, 6 commits); the spawner-silent refusal proofs are the LNC-03 structural evidence.

## What Was Built

### Task 1 — Spawner seam + tee launch + live-sweep registry (commits a8d1f39 RED, ea51363 GREEN)

- Module in the download_queue idiom: numbered-decision docstring (D-06/D-07/D-08/D-10/D-11), zero textual (the import-lock glob extends automatically), spawner-injectable declared.
- `_default_spawner(argv, **kwargs)` + `_signal_group(proc, sig)` copied VERBATIM from download_queue:698-712/870-878 — pure Popen forward; killpg with already-dead races absorbed.
- `SweepLauncher(spawner=None, kill_grace=2.0, kill_interval=0.05)`: instance registry `root -> {"handle", "meta", "tee"}` (the claimed-entry shape; the tee reference pins the parent-side fd open for the child's lifetime).
- `_spawn(argv, output_root, spawner=None, clock=None)` → `LaunchOutcome`: mkdir `state_dir()/logs`; tee `sweep_{YYYYmmdd_HHMMSS}_{rootname}.log` (`rootname` = the RESOLVED root's basename — the E2' phrase identity); `spawner(list(argv), start_new_session=True, cwd=str(REPO_ROOT/"pipeline"), env={**os.environ, "PYTHONUNBUFFERED": "1"}, stdout=tee, stderr=STDOUT)`; OSError → failed outcome with the diagnostic, tee closed+unlinked (nothing launched leaves no log), registry untouched.
- `kill_sweep(root)`: poll → "already_dead" (zero signals) | SIGTERM via killpg → poll-with-short-grace → SIGKILL escalation → "signalled"; entry dropped after. `detach(root)`: pop, no wait, no kill → "detached"/"noop". `live_sweeps()` sorted roots (the ExitModal predicate + 11-04's live_roots scans); `tee_path_for(root)` (None ⇒ the CLI-launched unavailable state).

### Task 2 — The gate (commits 6089336 RED, d8e63ed GREEN)

- `env_preflight(kernels=None)` → `EnvPreflight(can_launch, reasons, failed_kernels)`: `quick_check.run_quick_check(kernels)` → `env_gate.gate_verdict(results)` VERBATIM (zero edits to either frozen file — spy-proven); failed_kernels = CRITICAL failures in input order.
- `gate_confirm_data(spec, run_config_service=None)` → `GateSummary(models, tasks, seeds, cells, output_root, is_e2x, expected_phrase)`: FRESH preview/official/is_full_e2x recompute — the counting spy proves the screen's cached preview is never reused (T-11-03-02).
- `launch_spec(spec, phrase=None, run_config_service=None, spawner=None, clock=None)`: refusal chain, each stage BEFORE the spawner — preview problems → stage "problems"; official-keys diagnostic → stage "problems" as an `(official_keys, diagnostic)` tuple (fail-closed); E2' (recomputed fresh via `is_full_e2x(spec, official_keys())`) with a non-exact `phrase_matches(typed, spec.output_root)` → stage "phrase" with `expected`. Non-E2' ignores the phrase; spawn consumes `compose_argv(spec)` VERBATIM.
- `launch_argv(argv, output_root, ...)`: the raw pre-composed seam carrying the from-failures-only docstring warning (plan-checker obs 3).
- Test fixture fix (RED→GREEN): fake kernels are zero-arg callables returning CheckResult — the frozen face's injectable contract.

### Task 3 — From-failures path + full gates (commits 6515380 RED, 7a3430f GREEN)

- `launch_from_failures(failures_path, seeds, output_root, peft="none", config_variant="none", ...)`: composes via `run_config.compose_from_failures_argv` then routes through `launch_argv` — the SAME pipeline every launch source shares; the docstring records D-11 (env preflight is the screen's preceding step; failure-pairs-only enumeration can never be the full matrix, so the E2' typed gate cannot apply by construction).
- The construction proof pinned over the REAL official registries: an E2'-shaped `--models/--tasks` argv through `launch_argv` is NOT refused — the seam takes no spec and never consults the phrase gate; full-matrix launches must go through `launch_spec`.
- Full gates (the single wave-gate run): **make test 1411 passed** + JS 18/18; **make lint** All checks passed; **make typecheck** All checks passed.

## Verification Evidence

- `uv run --group dev --group tui pytest tests/tui/test_services_sweep_launcher.py -q` → **32 passed** (12 + 17 + 3 across the three lanes).
- `uv run --group dev --group tui pytest tests/tui/test_services_env_gate.py tests/tui/test_services_quick_check.py -q` → green (frozen-face consumers unregressed; both files edited ZERO bytes — `git diff --stat` over the plan range lists exactly 2 files).
- `make test` → **1411 passed** + node:test 18/18. `make lint` (ruff, PHASE8_TUI wildcard auto-extends) → All checks passed. `make typecheck` (ty) → All checks passed.
- TDD discipline: each lane landed RED first — Task 1: collection ImportError on the absent module (the 11-02 new-module precedent; all 12 target tests unrunnable because the feature does not exist); Task 2: 17 target-test failures, all `AttributeError` on the named missing API (env_preflight/launch_spec/GateRefusal — semantic assessment: each failed on the planned behavior being absent, not on fixtures); Task 3: 2 target-test `AttributeError`s on `launch_from_failures`. Then GREEN per task.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test-shape] Fake kernels conform to run_quick_check's injectable contract**
- **Found during:** Task 2 first GREEN run (TypeError: 'CheckResult' object is not callable)
- **Issue:** The suite's first fake kernels were CheckResult instances; the frozen face expects zero-arg callables each RETURNING a CheckResult.
- **Fix:** The `kernel()` helper returns `lambda: result`. The service was never at fault; the double conforms to the frozen seam (correct direction of conformance).
- **Files modified:** tests/tui/test_services_sweep_launcher.py
- **Commit:** d8e63ed

**2. [Rule 1 - Gate fixes] ruff DTZ001/UP017/SIM102/SIM115 findings**
- **Found during:** per-task lint runs.
- **Fix:** tz-aware `datetime(UTC)` for the fixed clock; `UTC` alias; the E2' refusal check combined into one `if ... and ...` (same call order — is_full_e2x still evaluates first); a justified `# noqa: SIM115` on the tee open (deliberately NOT a context manager — the handle lives for the child's lifetime, per the plan's own action note).
- **Files modified:** tui/services/sweep_launcher.py, tests/tui/test_services_sweep_launcher.py
- **Commits:** ea51363, d8e63ed

### Implementation Notes (within the plan's own discretion)

- `kill_grace`/`kill_interval` are constructor-injectable so the escalation test runs at grace 0 — the plan named `kill_sweep(root)` only; the injection follows the suite's injectable-spawner discipline without changing the production defaults (2.0s/0.05s).
- The registry entry holds the tee file reference and `_drop_entry` closes the parent copy on kill/detach — the child's inherited descriptor is unaffected, so "no pump, no early close" holds while handles never leak past a dropped root.
- `PROBLEM_OFFICIAL_KEYS = "official_keys"` is defined in sweep_launcher (not run_config) — the diagnostic-block condition came from the 11-02 handoff; the code lives with its only consumer.

## Threat Flags

None — every register entry landed as planned: T-11-03-01 (spawner-silent phrase refusal, call-count-proven), T-11-03-02 (fresh recompute, spy delta), T-11-03-03 (env FAIL blocks), T-11-03-04 (PYTHONUNBUFFERED pinned), T-11-03-05 (killpg + SIGKILL escalation + race absorption), T-11-03-06 (D-10 single-root tee pinned), T-11-03-SC vacuous (zero installs).

## Known Stubs

None — no placeholder values, no unwired data paths; every public surface is behavior-backed by the suite.

## What 11-06 Can Now Assume

The run-config screen's [enter] launch gate composes three service calls in order — `env_preflight(kernels)` (block + render `reasons` verbatim on `can_launch` False), `gate_confirm_data(spec)` (the confirm modal's models/tasks/seeds/cells/is_e2x/expected_phrase data, freshly recomputed so the screen never caches a verdict), then `launch_spec(spec, phrase)` — and branches on `GateRefusal.stage` ("problems" renders the problem list incl. the `official_keys` diagnostic; "phrase" renders the typed-phrase modal with `expected`) vs `LaunchOutcome` (spawned toast + D-13 auto-nav). The ExitModal consumes `live_sweeps()` / `kill_sweep(root)` / `detach(root)` outcome strings directly; the monitor's [t] tail reads `tee_path_for(root)` (None ⇒ the CLI-launched unavailable state) and 11-04's scans take `live_sweeps()` as `live_roots`. The [r] re-run is one call: `launch_from_failures(failures_path, seeds, output_root, ...)` behind its independent confirm.

## Self-Check: PASSED

- tui/services/sweep_launcher.py — FOUND
- tests/tui/test_services_sweep_launcher.py — FOUND
- a8d1f39, ea51363, 6089336, d8e63ed, 6515380, 7a3430f — all ancestors of HEAD
- Deletion check: no tracked files deleted by any plan commit (diff --stat: 2 files, 1449 insertions, 0 deletions)
- Untracked scan: only the pre-existing `.planning/.gsd-allow-shrink` (present at spawn)
- Ledger: commits measured 6 (`fea8eac..7a3430f`), no uncommitted code changes
