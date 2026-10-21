---
phase: 16-tui-multi-gpu-surface
plan: 1
subsystem: ui
tags: [textual, tui, nvidia-smi, gpu-monitoring, subprocess, render-gate]

requires:
  - phase: 15-dual-gpu-validation-subsets
    provides: the validated multi-GPU dispatch machinery (run_sweep_shard dispatch mode) the console now surfaces
provides:
  - tui/services/gpu_probe.py — the textual-free nvidia-smi CSV probe (fixed literal argv, injectable runner, frozen GpuRow rows, one absent outcome for every failure mode)
  - The standing #mon-gpu G GPU-lanes panel on MonitorScreen (both tabs, render-gated, ~2s-timeout probe on the 2s frontier cadence)
  - The GpuProbeProvider constructor-injection seam on MonitorScreen + DnallmMarkTui (16-05's fabricated golden fixtures)
  - The four MON_GPU_* strings constants riding the bilingual registry + EXPECTED_MON_CONSTANTS tripwire
  - The #mon-gpu TCSS block (separator + row tokens + the max-height 8 lane scroll bound)
affects: [16-tui-multi-gpu-surface (16-02 dispatch rows, 16-05 goldens), tui monitor surface]

actuals:
  tokens: 12888
  tasks: 2
  commits: 2
  plan_head_before: 02da0ac9d616f42de7676a476de51fc36d88fca6
  plan_head_after: c60e05c559eea931918f483867ae96615a6cf87e

tech-stack:
  added: []  # zero installs (D16-14): stdlib subprocess/dataclasses only
  patterns:
    - "injectable-runner subprocess probe: runner(argv, timeout) -> (returncode, stdout), canned outcomes in CI (the _default_spawner precedent)"
    - "unconditional pre-guard cadence dispatch: the mon-gpu worker fires at the TOP of _tick_frontier before the `if not self._live` early return (Pitfall 1)"
    - "per-region content-signature gate: (note, full formatted lane texts) — each region writes only on its own leg's change"

key-files:
  created:
    - tui/services/gpu_probe.py
    - tests/tui/test_services_gpu_probe.py
  modified:
    - tui/screens/monitor.py
    - tui/app.py
    - tui/strings.py
    - tui/styles.tcss
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_strings_phase11.py

key-decisions:
  - "The gpu probe rides the EXISTING frontier timer via a dedicated _tick_gpu dispatch at the top of _tick_frontier (before the live-root guard) — no second timer, an idle machine still probes (Pitfall 1, Open Q3 resolution (a): every frontier tick)"
  - "Absent outcome = None, zero GPUs = the EMPTY tuple, pre-first-probe = the _GPU_PENDING sentinel — three explicit states the render maps to absent-note / one MON_GPU_NONE row / header-only (the #41 optimistic-paint law)"
  - "The render gate writes each region only on its own leg's change: a lane value change never re-writes a healthy note; a pending->absent flip updates the note alone"
  - "_app() in the pilot suite defaults to an absent gpu fake — every pre-16-01 pilot test stays subprocess-free and cross-machine deterministic; only the pty lane drives the real probe (by design)"
  - "The lane bar splices after the `GPU {i}` head of the MON_GPU_ROW wording (registered verbatim per the UI-SPEC Copywriting table); floor allocation, cyan filled / dim open cells"

patterns-established:
  - "Pre-guard cadence dispatch for machine-level state (GPU state probes regardless of live runs)"
  - "Per-region signature gating inside one panel (note leg + lanes leg computed and compared separately)"

requirements-completed: [TUI-01]

coverage:
  - id: D1
    description: "The textual-free gpu_probe service: verified-live CSV shape -> frozen sorted GpuRow rows; fixed literal argv; every failure mode -> the same absent outcome"
    requirement: TUI-01
    verification:
      - kind: unit
        ref: "tests/tui/test_services_gpu_probe.py (14 tests: verified-live shape, sort, argv pin, zero-gpus, coercion, frozen, the four-mode degradation matrix + identity pin, import-lock glob pin)"
        status: pass
      - kind: unit
        ref: "tests/tui/test_import_lock.py (services textual-free glob collects gpu_probe.py)"
        status: pass
  - id: D2
    description: "The standing #mon-gpu panel wired end-to-end: fabricated rows render as lane rows on both tabs, absent -> note + zero lanes, zero GPUs -> one MON_GPU_NONE row, first paint header-only, render gate zero-write on steady ticks, on_mount reset on remount"
    requirement: TUI-01
    verification:
      - kind: automated_ui
        ref: "tests/tui/test_pilot_monitor.py (7 G-panel Pilot tests over the constructor-injected provider)"
        status: pass
      - kind: e2e
        ref: "tests/tui/test_pty_driver.py (15 passed — incl. test_monitor_quiet_cadence_is_byte_silent over the REAL app + REAL probe on the 2x5090 box)"
        status: pass
  - id: D3
    description: "The MON_GPU_* vocabulary + the #mon-gpu TCSS block + the app-composition-root provider threading"
    requirement: TUI-01
    verification:
      - kind: unit
        ref: "tests/tui/test_strings_phase11.py (bidirectional EXPECTED_MON_CONSTANTS inventory) + grep baselines (strings >= 4, tcss >= 1)"
        status: pass
      - kind: unit
        ref: "make lint && make typecheck && ci.yml hash-object == 33d2252eb594e0faecece9e8015a332d8d6479ef"
        status: pass

duration: 32min
completed: 2026-10-21
status: complete
---

# Phase 16 Plan 1: TUI-01 gpu_probe + G GPU-Lanes Panel Summary

**A textual-free nvidia-smi CSV probe (fixed argv, injectable runner, one honest absent outcome) feeding a render-gated standing G GPU-lanes panel on the slot-5 monitor, wired through the app composition root for 16-05's fabricated goldens.**

## Performance

- **Duration:** 32 min (plan estimate: 2 tasks; actual: 2 tasks, 2 commits)
- **Tokens (actuals, chars/4 over the diff):** 12,888 vs estimate 34,000 — the estimate priced the full 7-file tracer including all Task-2 pins; Task 1 landed the service + panel + both test families leaner than the estimate's ceiling
- **Commits:** 2 (4d7a8fb tracer, c60e05c Task-2 pins + gate fix), measured `git rev-list 02da0ac..c60e05c` = 2

## Tasks Completed

### Task 1 — gpu_probe service + G panel end-to-end on fabricated rows (tracer) — 4d7a8fb

- `tui/services/gpu_probe.py` (166 lines): `PROBE_ARGV` fixed literal list (T-16-01 — no operator input, never a shell string), `PROBE_TIMEOUT_SECONDS = 2.0` (D16-03), frozen `GpuRow`, `_default_runner` returning `(returncode, stdout)` together (16-RESEARCH Pattern 1), `probe()` with strict per-field int coercion — one malformed line degrades the WHOLE probe to `None` (D16-02), rows sorted by index (D16-04), zero GPUs -> `()`. Zero textual imports; stdlib only.
- `MonitorScreen`: `#mon-gpu` yielded between `#mon-content` and `BottomBar()` (both tabs, D16-05); header row (bold `MON_GPU_TITLE` left, 1fr right-aligned `$text-muted` note); `VerticalScroll` lane region (`can_focus = False` in on_mount, the `#mon-right-log` precedent); `_tick_gpu` dispatch at the TOP of `_tick_frontier` BEFORE the `if not self._live` guard (Pitfall 1); ONE `@work(exclusive=True, thread=True, group="mon-gpu", exit_on_error=False)` worker posting a run-tagged `GpuProbed` message (WR-02 idiom); `_render_gpu_panel` content-signature gate over (note, full formatted lane texts), modal suppression, on_mount sentinel reset; the 10-cell segmented utilization bar (floor allocation, cyan filled / dim `░` open — the `_strip_bar` grammar) spliced after the `GPU {i}` head.
- `GpuProbeProvider` constructor seam on `MonitorScreen.__init__` (None -> the real probe), threaded through `DnallmMarkTui.__init__` -> `build_monitor_screen` (the 261018-08g rebuild-per-navigation discipline).
- Four `MON_GPU_*` constants registered through `_t` (UI-SPEC Copywriting wording verbatim; `MON_GPU_ROW` data-forward identical both languages) + the four names in `EXPECTED_MON_CONSTANTS`.
- One `#mon-gpu` TCSS block (border-top separator, `height: 1` row tokens, `padding: 0 2`, `height: auto; max-height: 8` lane bound — theme tokens only, one Phase-16 comment block).
- Tests: 8 service tests (verified-live shape `0, 0, 2, 32607, 29` pins, sort, argv+timeout pin, zero-gpus, coercion, field count, frozen) + 2 Pilot tests (fabricated rows on both tabs — asserted on an IDLE machine to pin Pitfall 1; absent -> note + zero lanes + no crash). `_app()` gained the absent-by-default gpu fake so the entire existing pilot suite stays subprocess-free.
- Live sanity on this box: real probe returns both 5090s (`0, 0, 2, 32607, 28` x2); all five canned degradation shapes verified.

**Tracer feedback gate** (interactive mode, `human_verify_mode: end-of-phase`, automated-only `<verify>`): the full `<verify>` re-ran end-to-end green (129 tests + grep baselines + lint + typecheck) -> gate passed, execution continued.

### Task 2 — degradation matrix, render-gate byte-silence, both-tabs/empty states + CPU gates — c60e05c

- The four-mode degradation matrix as four self-describing service tests (`test_missing_binary_...`, `test_nonzero_exit_...`, `test_timeout_...`, `test_one_malformed_line_degrades_the_whole_probe_to_absent`) each asserting the absent outcome BY IDENTITY, plus `test_every_failure_mode_yields_the_identical_absent_outcome` and `test_module_is_covered_by_the_services_import_lock_glob` (D16-07 coverage proven).
- Pilot pins: zero GPUs -> exactly one `MON_GPU_NONE` row (and NO note); first paint header-row-only (blank note, zero lanes, `_gpu_run_id == 0`); probe renders with the History tab active; steady tick -> zero widget writes (note-update + remove_children spies, sentinel equality, lane widget identity) with a value-change leg; on_mount sentinel reset via the real `app._rerender_screen` recompose path.
- **RED -> GREEN (the plan's tdd="true" cycle earned its keep):** the value-change leg caught that the gate re-wrote the UNCHANGED note region on every lane change. Fixed in `_render_gpu_panel`: each region writes only on its own leg's change (`previous[0] != note` gates the note; `previous[1] == lane_texts` skips the lane rebuild) — Test 4's "writes exactly the changed region" now holds by construction.
- Guard lanes all green: 141 tests (gpu_probe + pilot + import-lock + strings), the full pty driver lane (15 — the byte-silence pin over the REAL probe on real idle 5090s), `make lint`, `make typecheck`, ci.yml hash pin `33d2252e...` byte-identical. NO push (v1.3 policy).

## Verification Results

- `pytest tests/tui/test_services_gpu_probe.py tests/tui/test_pilot_monitor.py tests/tui/test_import_lock.py tests/tui/test_strings_phase11.py -q` -> **141 passed**
- `pytest tests/tui/test_pty_driver.py -q` -> **15 passed** (quiet-cadence byte-silence over real hardware: green, no flake, no pin weakening)
- `make lint && make typecheck` -> **all checks passed**
- `git hash-object .github/workflows/ci.yml` -> **33d2252eb594e0faecece9e8015a332d8d6479ef** (unchanged)
- Grep baselines: `MON_GPU_*` in strings.py 8 >= 4; `mon-gpu` in styles.tcss 6 >= 1

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing `VerticalScroll` import in the pilot test file**
- **Found during:** Task 2 RED run
- **Issue:** The steady-tick test queried the lane region as VerticalScroll; the test file never imported it (NameError).
- **Fix:** Added the import. Files: tests/tui/test_pilot_monitor.py. Commit: c60e05c.

**2. [Rule 1 - Bug] The render gate re-wrote the unchanged note region on lane value changes**
- **Found during:** Task 2 RED run (the tdd="true" cycle)
- **Issue:** `_render_gpu_panel` wrote BOTH the note and the lanes whenever the combined signature changed — a utilization change fired a note `update("")` over an already-empty note (violates Test 4's "writes exactly the changed region" and adds churn the rze law forbids).
- **Fix:** Per-region gating — the note writes only when the note leg changes; the lane region rebuilds only when the lane-texts leg changes. Files: tui/screens/monitor.py. Commit: c60e05c.

### Notes (no rule needed)

- **tui/app.py is modified but absent from the plan's `files_modified` list** — the action text itself mandates it ("thread it from the app composition root honoring the rebuild-per-navigation MonitorScreen lifecycle"); the Pilot injection path requires it. Treated as a plan file-list omission, not a deviation.
- **Task 2's `<files>` lists only the two test files**, but the Task-4 RED legitimately required the monitor.py fix above (the tdd cycle's GREEN step). Documented here rather than skipped — the alternative (a test asserting behavior the code doesn't have) would have shipped a red pin.

## Known Stubs

None — every surface is wired end-to-end (probe -> worker -> message -> render gate -> panel).

## Handoff Notes (16-05 — goldens)

- `tests/tui/test_snapshots.py::test_monitor_empty_golden` and `::test_monitor_running_golden` are **RED on the committed tree by design**: the standing `#mon-gpu` panel is new chrome on both monitor faces. 16-05 regenerates under the D-03 discipline.
- `_golden_app` (test_snapshots.py:751) does NOT yet inject `gpu_probe_provider` -> the monitor goldens currently carry the REAL probe's outcome if a frontier tick fires mid-capture (machine-dependent bytes: live rows on this box, absent note on CI). 16-05 must thread a fabricated `GpuRow` fixture through the constructor seam built in this plan (the plan's own success criteria name it).
- WINDOWS ledger entry #46 records this red window.

## Threat Mitigations Landed

- **T-16-01 (Spoofing):** fixed literal argv — no operator input reaches the subprocess, never `shell=True` (pinned by `test_runner_receives_the_fixed_literal_argv_and_timeout`); one malformed line degrades the whole probe — never partial rows (the coercion tests).
- **T-16-02 (DoS):** ~2s per-call timeout + the exclusive `mon-gpu` worker with `exit_on_error=False` + the never-raise service and worker guards (the timeout matrix test; the worker's tolerant-provider catch).
- **T-16-SC (Tampering):** zero installs — stdlib subprocess/dataclasses only.

## Self-Check: PASSED

- tui/services/gpu_probe.py, tests/tui/test_services_gpu_probe.py exist
- Commits 4d7a8fb, c60e05c are ancestors of HEAD (c60e05c)
- All verify lanes re-run green after the final commit
