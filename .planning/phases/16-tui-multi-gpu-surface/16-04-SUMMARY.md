---
phase: 16-tui-multi-gpu-surface
plan: 4
subsystem: ui
tags: [textual, tui, multi-gpu, slot-4, dispatch-preview, confirm-faces, gate-order, registry-only]

requires:
  - phase: 16-tui-multi-gpu-surface plan 16-03
    provides: RunSpec.workers/gpus + the three mirror codes with the structured (workers, n) detail + compose_dispatch_argv + GpuCapacityBlock + the gate slot already threading requested_workers
provides:
  - The 多 GPU 调度 params section in tui/screens/run_config.py (live workers value 1, empty GPUs field + placeholder, dim hint, narrow-grid short title) over the existing classes only — zero slot-4 TCSS
  - LNC_GATE_DISPATCH_LINE on BOTH confirm faces (_GateConfirmModal first log line above the pair list; E2PhraseModal directly above the warning block) with service-side numbers
  - GateSummary.workers + .gpus_display computed in gate_confirm_data (typed list or all(n) via effective_gpu_count at preview time)
  - The [p] verbatim-argv preview switched to compose_dispatch_argv (one composition source, zero preview/spawn drift)
  - The ten Phase-16 slot-4 strings + the extended EXPECTED_CFG_/LNC_ inventories and the extended pilot gate-order family (zero weakening)
affects: [16-tui-multi-gpu-surface (16-05 goldens: run_config regen + run_config_confirm NEW from this tree), tui slot-4 launch surface]

actuals:
  tokens: 13768   # chars/4 over the 8-file realized diff (vs estimate 25000)
  tasks: 2
  commits: 2       # MEASURED: git rev-list --count 782fee7..fe9a660
  plan_head_before: 782fee7b6ce4d5cc59be404295089a2090ee7aa3
  plan_head_after: fe9a660cd16c97aa7b210908f113d876223455f7

tech-stack:
  added: []  # zero installs (T-16-SC): additive fields + copy only
  patterns:
    - "dispatch-plan tuple projection: _dispatch_line_data(summary) -> (workers, gpus_display, cells); the modals render the formatted constant, never compute (the modal-renders-service-computes law extended to the new line)"
    - "registry-injectivity-forced rewords documented in-module: when the UI-SPEC copy table's exact zh/en pair collides with an existing en owner, the NEW constant rewords (MON_GPU_TITLE owns en 'GPUs'); zh sides stay verbatim"

key-files:
  created: []
  modified:
    - tui/screens/run_config.py
    - tui/services/sweep_launcher.py
    - tui/strings.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_services_sweep_launcher.py
    - tests/tui/test_strings_phase11.py
    - tests/tui/test_pilot_nav_shell.py   # Rule-3 lockstep (one method)
    - tests/tui/test_snapshots.py          # Rule-3 lockstep (one method)

key-decisions:
  - "Two registry-injectivity rewords (Rule 1): CFG_MGPU_TITLE_SHORT en 'GPUs'->'Multi-GPU' and CFG_FIELD_GPUS en 'GPUs'->'gpus' — MON_GPU_TITLE (16-01) owns the en value 'GPUs' with zh 'GPU 状态', and the same-en-implies-same-zh tripwire forbids a second zh; the field's en 'gpus' is the flag's own lowercase spelling (the CFG_FIELD_SEEDS 'seeds' precedent); BOTH zh sides stay the UI-SPEC table's verbatim"
  - "The dispatch line rides the confirm faces as a plain (workers, gpus_display, cells) tuple threaded from GateSummary; the E2' re-prompt site (launch-finished phrase refusal) threads message.summary when present, and the MONITOR's E2PhraseModal call passes none — its face stays byte-identical (Pitfall 3, monitor.py untouched)"
  - "gpus_display derives at preview time inside gate_confirm_data: typed list joined, else all(n) with n = effective_gpu_count() (module-global reference — monkeypatch-injectable in tests); never persisted anywhere (Pitfall 8)"
  - "Cleared-field semantics stay the screen's established last-valid-governs rule (identical to epochs/curve/ebs — Phase-11 semantics unchanged by 16-04); the Pitfall-8 pin holds at the DEFAULTS spec: a never-typed list persists gpus None (pinned)"
  - "The [p] argv assertion moved to the space-flat comparison — the real dispatch argv exceeds one RichLog line and wraps (the full-string pin would be wrap-fragile)"

patterns-established:
  - "Space-flat RichLog assertions: ''.join(line.text).replace(' ', '') for long wrapped lines (wrap-safe substring pins)"

requirements-completed: [TUI-02]

coverage:
  - id: D1
    description: "The section renders with live defaults (workers VALUE 1, GPUs placeholder-only), sits between the EBS row and the DIRS title, swaps the short title at the narrow grid, threads PARAM_WORKERS/PARAM_GPUS through the mirrors (invalid never persists, last-valid governs), and the three mirror problems render numbered lines with the UI-SPEC copy"
    requirement: TUI-02
    verification:
      - kind: unit
        ref: "tests/tui/test_pilot_run_config.py (6 new: section render + order pin, narrow title, spec threading + defaults leg, numbered mirrors, dispatch-argv [p] shape, capacity-stage threading/refusal); tests/tui/test_strings_phase11.py (+10 inventory names, both directions)"
        status: pass
  - id: D2
    description: "GateSummary carries workers/gpus_display computed service-side over the same single fresh preview call (counting spy); both confirm faces render the line at the UI-SPEC positions with byte-unchanged E2' phrase mechanics; the 14-row #cfg-gate-log bound re-verified (1+12+1); the gate-order chain proven by stage-sequence evidence with the launched spec carrying the typed workers"
    requirement: TUI-02
    verification:
      - kind: unit
        ref: "tests/tui/test_services_sweep_launcher.py (3 new GateSummary tests: typed list, all(n)/all(0) seam, fresh recompute); tests/tui/test_pilot_run_config.py (4 new: confirm face + bound, same-source cells + preview marker, E2' face + mechanics, stage-order walk both scopes)"
        status: pass
  - id: D3
    description: "Guard lanes: lint + typecheck green; ci.yml hash unchanged; zero slot-4 TCSS; the full tui suite green at the pre-golden tree modulo the documented baselines"
    requirement: TUI-02
    verification:
      - kind: unit
        ref: "make lint && make typecheck -> all checks passed; git hash-object .github/workflows/ci.yml == 33d2252eb594e0faecece9e8015a332d8d6479ef; git diff tui/styles.tcss empty; pytest tests/tui -q -> 1360 passed + 6 environmental root-chmod + 3 goldens (monitor pair WINDOWS #46 + run_config WINDOWS #48, both 16-05-owned)"
        status: pass

duration: 45min
completed: 2026-10-21
status: complete
---

# Phase 16 Plan 4: TUI-02 Slot-4 Screen — Multi-GPU Dispatch Summary

**The params pane 多 GPU 调度 section (live workers 1 / GPUs placeholder, zero new TCSS) threading the three mirror problems and the capacity stage's spec-workers, the [p] argv switched verbatim to compose_dispatch_argv, and LNC_GATE_DISPATCH_LINE on both confirm faces with GateSummary-computed workers / GPUs display / cells — the E2' phrase boundary byte-unchanged and the gate-order family extended with stage-sequence evidence.**

## Performance

- **Duration:** 45 min (plan estimate: 2 tasks; actual: 2 tasks, 2 commits)
- **Tokens (actuals, chars/4 over the diff):** 13,768 vs estimate 25,000 — the service fields, the section, and the two faces landed as mostly-additive blocks; the estimate's ceiling assumed heavier screen surgery
- **Commits:** 2 (c2f048d Task 1, fe9a660 Task 2), measured `git rev-list 782fee7..fe9a660` = 2

## Tasks Completed

### Task 1 — 多 GPU 调度 params section + spec threading + capacity-stage copy + problem mirrors — c2f048d

- **RED -> GREEN:** the 7 new/lockstep pilot tests + 2 inventory tests failed first on the planned gaps (`ImportError: cannot import name 'CFG_FIELD_GPUS'`, the widget/query absences, `unregistered: [the ten names]`) before the strings/screen landed.
- `tui/strings.py`: the ten slot-4 constants with the UI-SPEC Copywriting wording — two en-side rewords forced by the registry injectivity law (see Deviations 1), each documented in-module beside its constant.
- `tui/screens/run_config.py`: the section between the EBS row and the DIRS title (`.cfg-section-title` / `.cfg-param-row` / `.cfg-param-label` / `.cfg-param-input` / `.cfg-hint` verbatim; workers `Input(value="1", compact=True)`, GPUs `Input(value="", placeholder=CFG_GPUS_DEFAULT)`, the dim hint row); the short-title swap joins `_apply_width_mode`; seeding joins `on_run_config_screen_loaded`; `PARAM_WORKERS`/`PARAM_GPUS` join `_compose_spec`'s raw dict (empty GPUs field = absent = all-detected, the epochs idiom); `_problem_line` gains the three branches (`workers_exceeds_gpus` unpacks the structured pair via cast); `action_preview_modal` composes through the new `compose_dispatch_argv` protocol member.
- The gate's capacity stage itself needed ZERO edits — 16-03 already threads `requested_workers=spec.workers`; the new `_RecordingCapacityLauncher` test proves the typed workers reach the seam and both refusal/pass legs hold (chain order untouched; the 1047 seam-tolerance test untouched and green).
- Lockstep (Rule 1/3): the [p] argv test moved to the dispatch composer (space-flat); the SVG placeholder-count pin extended 3 -> 4 (the same `—（默认` grammar on the new row); `compose_dispatch_argv` on the protocol forced one-method additions in `_RunConfigShellFake` (nav_shell) and `_RunConfigGoldenService` (snapshots) — the two files beyond the plan's six-file list.

### Task 2 — dispatch-plan preview line on both confirm faces + GateSummary fields + gate-order extension — fe9a660

- **RED -> GREEN:** the 7 new tests failed first on `'GateSummary' object has no attribute 'workers'` before the service fields landed.
- `tui/services/sweep_launcher.py`: `GateSummary.workers: int = 1` + `gpus_display: str = ""` (defaulted — pre-16-04 fakes construct unchanged, the pairs precedent); `gate_confirm_data` computes both (tolerant getattr; typed list joined, else `all(n)` with `effective_gpu_count()` read at preview time — monkeypatch-injected in tests; `all(0)` honest for count-0).
- `tui/screens/run_config.py`: `_dispatch_line_data` projects a summary onto the tuple; `_GateConfirmModal` writes the line as the FIRST `#cfg-gate-log` row (1 + 12 + 1 == the 14-row bound, re-verified by a 15-pair fixture rendering exactly 14 lines); `E2PhraseModal` yields it directly above the warning block (plain Static, additive — the phrase input, expected-phrase copy, match indicator, advance/blur arming, and y-launch all byte-unchanged, D16-12); the monitor's E2' re-prompt call passes no tuple (Pitfall 3 — `monitor.py` untouched).
- Gate-order extension (zero weakening): `_StageOrderLauncher` records `capacity -> env -> confirm` in fire order on both scope legs; the full-scope leg walks to the E2' face and launches the typed-workers spec through the phrase; the subset leg walks to the Y/N confirm — both with the line present on the reached face.

## Verification Results

- `pytest tests/tui/test_pilot_run_config.py tests/tui/test_strings_phase11.py -q` -> **116 passed** (Task 1 leg)
- `pytest tests/tui/test_services_sweep_launcher.py tests/tui/test_pilot_run_config.py -q` -> **188 passed** (Task 2 leg, re-run green post-commit)
- `pytest tests/tui -q` -> **1360 passed, 9 failed** — the 9 decompose exactly: 6 environmental root-chmod baseline members (test_pilot_data_manager 1 + test_services_download_queue 5, untouched files) + the 2 monitor goldens (WINDOWS #46, 16-05 owns) + `test_run_config_golden` (WINDOWS #48, new — see Notes)
- `make lint` + `make typecheck` -> **all checks passed**; `git hash-object .github/workflows/ci.yml` -> **33d2252eb594e0faecece9e8015a332d8d6479ef** (unchanged)
- `git diff tui/styles.tcss` -> **empty** (zero slot-4 TCSS; the strings grep gate >= 9 OK)
- run_config golden delta extracted: **ADDED only** the section rows (title `多 GPU 调度`, separator, `workers` + value `1`, `GPUs` + placeholder, hint) — REMOVED empty; the screen is golden-ready for 16-05

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - plan-internal inconsistency] Two en-side rewords forced by the registry injectivity law**
- **Found during:** Task 1 GREEN — the inventory + injectivity tripwires failed with `same-en constants must share one zh value: {'GPUs': {'GPU 状态', 'GPUs'}}`
- **Issue:** the UI-SPEC Copywriting table's `CFG_FIELD_GPUS` ("GPUs"/"GPUs") and `CFG_MGPU_TITLE_SHORT` (zh 多卡 / en GPUs) collide with `MON_GPU_TITLE` (16-01: zh `GPU 状态` / en `GPUs`) — the plan demanded BOTH the verbatim wording AND the green bidirectional tripwires, which are mutually unsatisfiable.
- **Fix:** zh sides stay verbatim; `CFG_FIELD_GPUS` en = **"gpus"** (the `--gpus` flag's own lowercase spelling, the `CFG_FIELD_SEEDS` "seeds" precedent); `CFG_MGPU_TITLE_SHORT` en = **"Multi-GPU"** (the natural shortening of the 120-col "Multi-GPU dispatch", exactly how "Dirs" shortens the DIRS pair). Both documented in `tui/strings.py` beside their constants. Files: tui/strings.py. Commit: c2f048d.

**2. [Rule 3 - lockstep] The protocol addition touched two test files outside the plan's six-file list**
- **Found during:** Task 1 `make typecheck` — 2 diagnostics
- **Issue:** adding `compose_dispatch_argv` to `RunConfigServiceProtocol` structurally binds every conforming fake; `_RunConfigShellFake` (test_pilot_nav_shell.py) and `_RunConfigGoldenService` (test_snapshots.py) lacked it.
- **Fix:** one-method additions per fake (nav_shell raises like its `compose_argv`; snapshots delegates to the real module like the pilot fake). Files: tests/tui/test_pilot_nav_shell.py, tests/tui/test_snapshots.py. Commits: c2f048d (both files).

**3. [Rule 1 - lockstep] The [p] argv preview assertion moved to the dispatch composer**
- **Found during:** Task 1 RED (anticipated — the plan's key_links name the same-composer preview)
- **Fix:** `test_preview_modal_renders_argv_and_problems` now asserts `compose_dispatch_argv` output space-flat (the real argv wraps across RichLog lines); the SVG placeholder-count pin extended 3 -> 4 for the new GPUs row (same grammar). Files: tests/tui/test_pilot_run_config.py. Commit: c2f048d.

### Notes (no rule needed)

**4. Cleared-field semantics vs the plan's "empty = None" wording**
- The plan's Pitfall-8 truth reads as though CLEARING the GPUs field resets the spec to None; the landed screen (Phase-11 semantics, identical for epochs/curve/ebs/seeds) follows last-valid-governs — a cleared field keeps the last valid value in `self._spec`. 16-04 changes nothing there; the Pitfall-8 pin is held where the plan's verify demands it: the DEFAULTS spec (a never-typed list) composes argv WITHOUT `--gpus` and persists `gpus: null` (pinned in both the pilot defaults leg and 16-03's service pins).

**5. run_config golden joins the pre-regen red set (WINDOWS #48)**
- The plan's Task 2 full-tui leg treats a failing golden as drift; the reconciliation is in-plan: the params-pane section IS this plan's surface (must_haves truth #1), the delta is verified ADDED-only, and 16-05 owns the D-03 regen ("16-05 regenerates run_config + adds run_config_confirm from this tree" — the success criteria's own wording). Recorded as WINDOWS #48 beside #46.

## Known Stubs

None — the section, the mirrors, the capacity threading, the GateSummary fields, and both confirm-face lines are wired end-to-end; every number in the dispatch line travels service-side.

## Handoff Notes (16-05 — the golden plan)

- Regenerate `run_config.svg` from THIS tree (the delta base above is the expected ADDED-only diff); ADD `run_config_confirm.svg` (the `_GateConfirmModal` with the dispatch line + capped pairs — the deterministic spec fixture needs `GateSummary(workers=…, gpus_display=…)` or the line renders with the defaulted `1`/`""`).
- The 3-golden red set at this base: monitor pair (WINDOWS #46) + run_config (WINDOWS #48).
- `_RunConfigGoldenService` (test_snapshots.py) already carries the `compose_dispatch_argv` delegation — no further fake work needed for the golden lane.
- The snapshot lane's run_config golden build does not open the gate, so the dispatch line does not affect `run_config.svg` — only the params section does.

## Threat Mitigations Landed

- **T-16-07 (Elevation — mirrors presented as the authority):** the three mirrors render through the same numbered-problems vehicle; the shard CLI re-validates at spawn (defense in depth) and the service gate re-proves capacity/preview/phrase fresh (stage-order evidence extended, zero weakening).
- **T-16-SC (Tampering — package installs):** zero installs; additive fields/copy only.

## Self-Check: PASSED

- All eight modified files committed (none created); `git rev-list 782fee7..fe9a660` = 2; commits c2f048d + fe9a660 are ancestors of HEAD (fe9a660)
- All verify lanes re-run green after the final commit (188 pilot/launcher tests, lint, typecheck, hash + zero-TCSS gates; the full-tui failures decompose to the documented baselines)
