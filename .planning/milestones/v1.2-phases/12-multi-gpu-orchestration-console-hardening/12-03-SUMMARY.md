---
phase: 12-multi-gpu-orchestration-console-hardening
plan: "03"
subsystem: testing
tags: [textual, tui, svg-goldens, snapshot-testing, focus-management, pilot-tests]

requires:
  - phase: 12-multi-gpu-orchestration-console-hardening (12-01)
    provides: the Makefile PHASE12 lint extension this plan's snapshot-update target joins
provides:
  - the slot-4 modal focus-trap fix (delta B) — one shared dismiss() override, B1-B5 Pilot-proven
  - the 8-SVG TUI golden corpus on the fallback lane (run_test + export_screenshot + UTF-8 string equality) with determinism + sensitivity proof
  - make snapshot-update — the ONLY golden regeneration path (maintainer-only, D-03 review gate)
  - the params Input empty-bar fix (compact=True) — the live 11-UAT advisory #2 root cause
affects: [12-04, 12-05, phase-12-verification, gsd-verify-work]

actuals:
  tokens: 104000   # chars/4 over the realized diff (a66ef75..HEAD; the 8 SVGs are ~350KB of it)
  tasks: 2
  commits: 9       # measured git rev-list a66ef75..HEAD (6 plan commits + 3 pause-work chore(handoff) commits that landed inside the window)

tech-stack:
  added: []          # zero new dependencies (T-12-03-SC held; plugin REMOVED by resolver conflict)
  patterns:
    - "Fallback-lane snapshot goldens: App.run_test(size=(120,40)) + App.export_screenshot() + plain UTF-8 string equality vs committed SVGs — no syrupy/jinja2/cairosvg, zero pyproject/uv.lock change"
    - "Regeneration contract: `make snapshot-update` (module --regenerate entry under the test lane env) is the ONLY regen path; CI compares and goes red on drift (Pitfall 4)"
    - "Dismiss-time refocus: ONE shared _PickerReturnModal.dismiss() override routing all 10 slot-4 dismiss paths back to #cfg-picker (probe-verified Screen.action_dismiss routing)"

key-files:
  created:
    - tests/tui/test_snapshots.py
    - tests/tui/__snapshots__/{env_check,selection_models,selection_datasets,data_manager,run_config,monitor_running,monitor_empty,wizard}.svg
  modified:
    - tui/screens/run_config.py
    - tests/tui/test_pilot_run_config.py
    - Makefile

key-decisions:
  - "Delta B landed as ONE shared _PickerReturnModal.dismiss() override (super().dismiss then call_after_refresh refocus of #cfg-picker on the screen below) — 5 modal re-parents + a local _GateConfirmModal at the :1621 push site; selection.py/strings.py/styles.tcss byte-identical"
  - "Goldens ride the FALLBACK lane (plugin verdict: pytest-textual-snapshot 1.1.0 pins syrupy==4.8.0 -> pytest<9, resolver-conflicting the committed pytest>=9.1.1 floor); string equality on SVG text IS the compare, honestly documented as pixel-compare at SVG fidelity"
  - "[Rule 1 deviation] compact=True on the 8 height-1-row Inputs (filter + 7 params rows): a default bordered Input is height 3 and the height-1 row clips it to its top border — the VALUE row rendered invisible (the live 11-UAT 'seeds empty bar' phenomenon, phase-11 UAT advisory #2 root cause); the #selection-filter precedent; E2' modal input (auto-height box) and the display=False subset input untouched"
  - "make snapshot-update is maintainer-only (D-03 review gate): regenerated SVGs are reviewed then committed WITH the drifting change; CI never regenerates"

patterns-established:
  - "Golden determinism discipline: frozen fixtures + injected now= + cursor_blink=False on every Input before export + newest_mtime=None — fix the fixture, never the compare"
  - "RED evidence records must EMBED the report (junit XML in `output`), not reference it by path — the classifier rejects path-only records (both inherited 12-03 records were repaired/re-captured)"

requirements-completed: [TEST-01]

coverage:
  - id: D1
    description: "Delta B — the slot-4 modal focus trap fixed at the one sanctioned site (shared dismiss() override) with B1-B5 Pilot proof (10 dismiss paths -> picker focus, digit nav live, filter-Enter precedent intact, defensive edges)"
    requirement: TEST-01
    verification:
      - kind: unit
        ref: "tests/tui/test_pilot_run_config.py#test_b1_* .. test_b4_*"
        status: pass
    human_judgment: false
  - id: D2
    description: "The 8-SVG golden corpus on the fallback lane (env_check, selection_models, selection_datasets, data_manager, run_config, monitor_running, monitor_empty, wizard) with determinism + sensitivity tests and the make snapshot-update maintainer path"
    requirement: TEST-01
    verification:
      - kind: unit
        ref: "tests/tui/test_snapshots.py#test_env_check_golden .. test_wizard_golden + test_golden_export_is_deterministic_across_instances + test_golden_compare_is_sensitive_to_fixture_state"
        status: pass
    human_judgment: true
    rationale: "D-03 maintainer review gate: the 8 committed SVGs must be eyeballed in a browser/editor against the UI-SPEC corpus table before the corpus is trusted (end-of-phase human gate; automation proves byte-stability, not visual rightness)"
  - id: D3
    description: "Params Input values render (Rule-1 deviation: compact=True on the 8 clipped Inputs — the 11-UAT empty-bar root cause)"
    verification:
      - kind: unit
        ref: "tests/tui/test_pilot_run_config.py#test_params_input_values_render_in_export"
        status: pass
    human_judgment: false

duration: 65min
completed: 2026-10-13
status: complete
plan_head_before: a66ef753818e816665da08137a15624e1adfa48d
plan_head_after: 1ec42d3
---

# Phase 12 Plan 03: Slot-4 Focus Fix + TUI Snapshot Goldens Summary

**One shared dismiss() override killed the slot-4 modal focus trap (B1-B5 Pilot-proven), plus an 8-SVG golden corpus on the plugin-free fallback lane — and, en route, the compact=True fix that makes params Input values render at all (the live 11-UAT empty-bar bug)**

## Performance

- **Duration:** ~65 min end-to-end (resumed mid-plan after a prior executor stall; Task 1 committed by the prior run, Task 2 + the rendering fix completed by the resume)
- **Started:** 2026-10-13T12:01Z (prior executor dispatch)
- **Completed:** 2026-10-13T13:06Z
- **Tasks:** 2 (plus 1 Rule-1 deviation with its own RED/GREEN)
- **Files modified:** 12 (code+tests+goldens)

## Accomplishments

- **Delta B (Task 1, prior executor):** `_PickerReturnModal(ModalScreen)` in `tui/screens/run_config.py` overrides `dismiss()` — captures the screen below, calls `super().dismiss(result)`, then `call_after_refresh`-refocuses `#cfg-picker`; the five run_config modals re-parent onto it and the ConfirmModal push site uses a local `_GateConfirmModal`. All 10 slot-4 dismiss paths land focus on the picker; digits navigate immediately (the phase-11 UAT deadlock is dead); selection.py / strings.py / styles.tcss byte-identical.
- **The golden corpus (Task 2):** `tests/tui/test_snapshots.py` boots each canonical screen over frozen constructor-injected fakes at 120x40, exports via `App.export_screenshot()`, and string-compares against the 8 committed SVGs. Determinism (independent app instances -> byte-identical) and sensitivity (running vs empty monitor -> distinct SVGs) prove the compare non-vacuous. `make snapshot-update` is the ONLY regeneration path, maintainer-only per D-03.
- **The rendering fix (Rule-1 deviation, this resume):** the params-column Inputs (and the slot-4 filter) were default bordered height-3 widgets clipped inside height-1 rows — only the top border rendered; the seeds value `42,43,44` was IN the widget but invisible on screen. `compact=True` on the 8 clipped sites (the `#selection-filter` precedent) makes the values render; the run_config golden pins them.
- **RED evidence hardening:** both inherited evidence records were classifier-invalid (JUnit XML referenced by /tmp path, not embedded). Task 1's original XML survived and was embedded (genuine original run output); Task 2's RED was re-captured faithfully (goldens parked aside -> the same planned missing-golden failures) — all three records now `RED_EVIDENCE_OK`.

## Task Commits

1. **Task 1 RED — B1-B5 Pilot tests** - `c415ec1` (test) — prior executor
2. **Task 1 GREEN — the shared dismiss() override (delta B)** - `88ce24c` (feat) — prior executor
3. **Task 2 RED — the fallback-lane snapshot harness** - `bde769a` (test) — 8 goldens missing, determinism+sensitivity already green
4. **Fix RED — params Input values invisible in the export** - `ef30511` (test) — + evidence records embedded/repaired
5. **Fix GREEN — compact=True on the 8 clipped Inputs** - `536da03` (fix) — + lint repair on Task-1-committed lines (UP037/RUF012/S110)
6. **Task 2 GREEN — the 8-SVG corpus + make snapshot-update** - `1ec42d3` (feat)

*(Three `chore(handoff)` commits inside the measurement window are pause-work session snapshots, not plan work.)*

**Plan metadata:** (this commit)

## Files Created/Modified

- `tui/screens/run_config.py` — delta B base class + re-parents (Task 1); compact=True on the 8 clipped Inputs (Task 2 deviation)
- `tests/tui/test_pilot_run_config.py` — B1-B5 Pilot tests (Task 1); test_params_input_values_render_in_export (deviation); lint fixes
- `tests/tui/test_snapshots.py` — the fallback-lane harness: fakes, factories, 8 drives, golden tests, determinism/sensitivity, --regenerate entry
- `tests/tui/__snapshots__/*.svg` (8) — the frozen corpus; monitor_running is delta A's proof golden (finetuned-mgpu-w0 + five glyphs + ⊘续跑 + ETA)
- `Makefile` — `snapshot-update` target (+ .PHONY), maintainer-only recipe comment

## Decisions Made

- The stall breadcrumb's diagnosis is confirmed and fixed in-scope: **not** a width/styling problem in styles.tcss but the default-Input-height-vs-height-1-row clip; the fix is the `compact=True` constructor flag (zero styles.tcss/strings change, the selection-screen precedent). This supersedes the UI-SPEC amendment-table row "run_config.py — delta B the ONLY change" for this file per the resume dispatch's explicit authorization; D-10/D-01 discipline otherwise held (zero new strings, zero styles.tcss edits, monitor.py untouched).
- The E2' phrase-modal input and the display=False subset-path input stay NON-compact: both live in auto-height containers where the full bordered Input renders correctly (the wizard-golden-proved pattern); the fix is scoped to the 8 actually-clipped sites only.
- Phase-11 UAT advisory #2 (params fields show empty bars) is resolved by this plan — its root cause was the clip, not data binding (the widget `.value` held the right strings all along; no Pilot test asserted the RENDER, which is why it slipped through — now pinned by both the visibility test and the golden).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Params Input values rendered invisible (the 11-UAT empty-bar phenomenon)**
- **Found during:** Task 2 (golden generation; the prior executor's stall breadcrumb named the symptom)
- **Issue:** Default Textual Inputs are `height: 3` + `border: tall`; inside the `height: 1` `.cfg-param-row` / `#cfg-filter-bar` containers only the top border rendered — the value row was clipped away. Live users saw empty bars for seeds/曲线档位/epochs/ebs/输出根/数据集根 (phase-11 UAT advisory #2).
- **Fix:** `compact=True` on the 8 clipped sites (`-textual-compact`: border none, height 1, padding 0 — the `#selection-filter` precedent, selection.py:1303). RED: `test_params_input_values_render_in_export` (evidence `12-03-fix-red.json`, RED_EVIDENCE_OK). GREEN: `536da03`.
- **Files modified:** tui/screens/run_config.py, tests/tui/test_pilot_run_config.py
- **Verification:** 47/47 run_config Pilot tests; the regenerated run_config golden carries `42,43,44` / `./finetuned` / `./datasets` as visible text.
- **Committed in:** `ef30511` (RED) + `536da03` (GREEN)

**2. [Rule 3 - Blocking] Plan-end lint gate failed on Task-1-committed lines**
- **Found during:** the plan-end `make lint` (the SPEED DIRECTIVE defers the gate to plan end — Task 1's commits never saw it)
- **Issue:** 3x UP037 (quoted `threading.Event | None` annotations), 1x RUF012 (mutable `BINDINGS` class attribute), 1x S110 (the delta B blind-except `try/except/pass`).
- **Fix:** unquoted annotations, `ClassVar[list[Binding]]` (the 08-03 idiom), S110 added to the existing BLE001 per-line noqa (the run_finetune.py justified-noqa precedent).
- **Files modified:** tests/tui/test_pilot_run_config.py, tui/screens/run_config.py
- **Verification:** `make lint` all checks passed.
- **Committed in:** `536da03`

**3. [Rule 3 - Blocking] Inherited RED evidence records were classifier-invalid**
- **Found during:** resume (validation of the prior executor's evidence before continuing Task 2's GREEN)
- **Issue:** Both records referenced their JUnit XML by /tmp path without embedding the report — `INVALID_RED/invalid_record` (the tdd.md contract requires the complete report in `output`).
- **Fix:** Task 1's original XML survived on disk and was embedded into the repaired record (genuine original-run output; mtime matches its 12:09Z run start); Task 2's RED was re-captured by parking the goldens aside and re-running the identical missing-golden failure mode. Both now RED_EVIDENCE_OK.
- **Files modified:** .planning/phases/12-.../evidence/12-03-task{1,2}-red.json
- **Verification:** `gsd_run check tdd-red-evidence` → passed for all three records.
- **Committed in:** `ef30511`

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** Deviation 1 is the resume dispatch's explicitly-requested diagnosis outcome — the golden now pins the CORRECT render instead of the broken one, and a live UAT advisory is closed. No scope creep beyond run_config.py (in files_modified).

## Issues Encountered

- The prior executor stalled mid-Task-2 investigating the Input-rendering symptom; its untracked harness + SVG drafts were continued (not rewritten) after lint/ty cleanup (17 unused-noqa RUF100s, 1 DTZ001, 2 ty ModuleType-assignment diagnostics fixed via the repo's setattr/B010 precedent).
- The 20:22 draft SVGs regenerated slightly smaller across ALL screens — they had been exported from the stalled executor's experimental tree state; the committed corpus comes from clean HEAD via the new `make snapshot-update` (verified byte-identical across two consecutive regenerations).

## TDD Gate Compliance

| Gate | Commit | Evidence |
|------|--------|----------|
| Task 1 RED | `c415ec1` | `evidence/12-03-task1-red.json` (RED_EVIDENCE_OK after record repair — original run's XML embedded) |
| Task 1 GREEN | `88ce24c` | 47/47 module suite (prior executor's run + re-verified this resume) |
| Task 2 RED | `bde769a` | `evidence/12-03-task2-red.json` (RED_EVIDENCE_OK; re-captured missing-golden RED, same harness) |
| Task 2 GREEN | `1ec42d3` | 10/10 snapshot module |
| Deviation RED/GREEN | `ef30511`/`536da03` | `evidence/12-03-fix-red.json` (RED_EVIDENCE_OK) |

No gate violations. All three RED records embed complete JUnit XML reports.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 12-04 (merge + docs) and 12-05 (integration close-out) unblocked; `make snapshot-update` is documented in the module docstring and Makefile.
- **Pending human gate (D-03):** the maintainer reviews the 8 committed SVGs in a browser/editor against the UI-SPEC corpus table (人工待办 #2 in .continue-here.md); any adjustment = fix the fixture, re-run `make snapshot-update`, re-review.
- The corpus will go red on ANY future render change (including 12-04/12-05 if they touch screens — by design; regenerate + review then).

## Self-Check: PASSED

All 15 created/modified files exist on disk; all 6 task commits are ancestors of HEAD; the zero-diff guard set (styles.tcss, strings.py, selection.py, monitor.py) shows zero changes across the plan window (a66ef75..HEAD).

---
*Phase: 12-multi-gpu-orchestration-console-hardening*
*Completed: 2026-10-13*
