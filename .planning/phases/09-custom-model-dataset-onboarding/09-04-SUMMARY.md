---
phase: 09-custom-model-dataset-onboarding
plan: 09-04
subsystem: tui/screens wizard (presentation tier over the 09-01 services)
tags: [tui, wizard, modal, forms, collect-all-report, prefill, textual]
requires:
  - 09-01 (validate_model_candidate/validate_dataset_candidate + METRIC_REGISTRY + WIZ_* strings — the validator seam this screen injects)
  - 09-03 (the nav shell the wizard mounts beneath; ConfirmModal from the Phase 8 modal family)
  - 08-02/08-07 (textual 8.2.8, the ModalScreen modal-family pattern, Pilot tier-2 discipline)
provides:
  - "WizardModal — the CUST-01/02 collection half: both four-step forms with D-03 type-aware controls, b/esc/enter semantics, the esc-confirm destructive gate, and the value-preservation contract"
  - "The CUST-03 report view: submit -> validator seam -> numbered collect-all list in a wrapping RichLog inside the same modal (nothing applied on failure)"
  - "The gauntlet phase slot (minimal pending view) + the on_valid/on_import/on_export callback seams 09-05 wires real views onto"
  - "The prefill seam (D-12: one-item {key: entry} map folds every field — the 09-06 w-key re-record aid)"
  - "WIZ_/WIZM_/WIZD_ wizard copy blocks complete in tui/strings.py (verbatim from the Copywriting table)"
affects:
  - tui/strings.py (additive WIZ chrome block; no existing constant touched)
  - tui/styles.tcss (additive wizard rules; theme tokens only)
actuals:
  tokens: 19147   # chars/4 over the realized diff (76587 diff chars, tui/+tests/)
  tasks: 3
  commits: 6      # MEASURED: git rev-list --count 3906acb..HEAD
plan_head_before: 3906acb8aaddc32089e4a27de85ea464fbd7f460
plan_head_after: 9217a0d39d6e33be168453d9b423ae3c45a29f35
tech-stack:
  added: []        # zero new packages (T-09-SC: textual 8.2.8 widgets only)
  patterns:
    - "declarative step tables (FieldSpec/StepSpec/KindSpec) driving one compose over the active phase view"
    - "single ModalScreen with _phase branching — report/gauntlet as views, never pushed screens (Pitfall 9 preservation contract)"
    - "deselect-by-value single-pick enforcement (programmatic deselect fires no re-toggle message)"
    - "code-applied min(100, w-4) modal width (TCSS has no min()/arithmetic — probe-pinned)"
key-files:
  created:
    - tui/screens/wizard.py
    - tests/tui/test_pilot_wizard.py
  modified:
    - tui/strings.py
    - tui/styles.tcss
key-decisions:
  - "ONE WizardModal over declarative step tables: compose renders only the active phase view (form step / report / gauntlet pending) and every value lives in self._values — re-compose can never lose data; the report and gauntlet are VIEWS inside the same modal so dismissing them returns to the same step with every value intact (Pitfall 9); only esc-confirm (ConfirmModal, the filled-step count named), a successful land, or a used undo clears the form"
  - "The dataset split-file Inputs collect FILE NAMES advisory-only: Train/Dev/Test never compose into the candidate (the 09-01 derive-at-composition decision — landed rows carry row counts the wizard never types); the split advisory probes <Dataset_path>/<name> via the injected file_exists seam; Task_type stores under the registry field name type (Auto-Default #11)"
  - "Candidate composition stamps NOTHING the services own (no Model_name/Dataset_name, no path relativization, no enabled) — numerics compose as int/float when parseable, unparseable text passes through raw so the collect-all flags it, optional strings compose as \"\" never None, quirks compose as the three-key dict (D-02; execution-side mapping is Phase 11's boundary, recorded in the step copy)"
  - "Enter-advance rides BOTH paths textual offers: Input.Submitted while an Input holds focus (the Input eats the key) and the screen-level enter binding when focus is elsewhere; b/f/o are plain bindings — a focused Input eats printables, so navigation keys never hijack typing (no priority bindings, grep-pinned by the 09-03 suite)"
  - "Probe-pinned textual 8.2.8 facts recorded in code: TCSS rejects min()/arithmetic (the width-100 amendment applies in code at min(100, w-4) with the tcss base width); border_title parses console markup at set time, so the step indicator's accent+bold span resolves app.current_theme.accent at chrome-apply time (the live theme's value — zero hardcoded hex); SelectionList deselect accepts the option VALUE directly and fires no re-toggle (the single-pick loop is impossible)"
patterns-established:
  - "The wizard seams (validator / on_valid / on_import / on_export / dir_exists / file_exists / vocabularies / prefill) are constructor-injected callables — 09-05 binds the real gauntlet panel + import/export views and 09-06 the w-key push without touching this module's shape"
  - "Advisory-vs-authoritative check split inside a screen: Input.Changed drives glyph lines that NEVER block advance; the injected validator owns every authoritative verdict (fool-proofing does not become blocking)"
requirements-completed: []
# NOTE: the plan frontmatter carries [CUST-01, CUST-02, CUST-03] but the
# wizard's WRITE half is 09-05's gauntlet (D-08: the gauntlet is the only
# write path; this plan's prohibition is explicit — submission validates
# only). CUST-01/02/03 stay Pending until 09-05 lands + wires real
# ValidationSources (the 09-03 precedent: complete only what the plan
# delivered).
coverage:
  - id: model-form-semantics
    description: "The four model steps render the exact UI-SPEC field sets/controls (quirks unchecked); enter advances with the submit keycap on the last step; b preserves values; esc confirms only with entered values (filled-step count named) and a blank form cancels silently; single-pick clears the previous pick; the advisory path/numeric lines flip per keystroke and never block"
    requirement: CUST-01 UI / must_haves truths 1-3
    verification:
      - kind: automated
        ref: "tests/tui/test_pilot_wizard.py (Task-1 suite: 9 tests incl. the zero-Chinese grep)"
        status: pass
    human_judgment: false
    rationale-when-true: "Pilot key-event drives over the real app with faked seams — pure mechanical assertions"
  - id: dataset-form-report
    description: "The four dataset steps with their controls; submit renders the numbered collect-all report in validator emission order inside the same modal; nothing applied on failure; esc from report AND gauntlet returns to the same step with values intact; clean pass fires on_valid once with the exact candidate payload (numerics as numbers, Task_type under registry 'type', optional strings as '', no Train/Dev/Test); the metric list offers the injected 28; a 68-char key wraps, never elides"
    requirement: CUST-02 UI + CUST-03 report / must_haves truths 4-5
    verification:
      - kind: automated
        ref: "tests/tui/test_pilot_wizard.py (Task-2 suite: 8 tests)"
        status: pass
    human_judgment: false
    rationale-when-true: "Pilot drives + joined-strip report text assertions (wrap-never-elide is strip-joinable by construction)"
  - id: prefill-seams-backstop
    description: "Prefill folds the one-item {key: entry} map across all steps (enums selected, quirks carried, split inputs documented blank); the unchanged key surfaces the collision report (D-12 self-enforcement); f/o fire only on step 1 and reach the seams; at 80x24 a 68-char key and a >100-char path stay enterable with the full echo across the wrap, modal width exactly 76, nothing elides"
    requirement: D-11/D-12 + the UI-Considerations long-text backstop
    verification:
      - kind: automated
        ref: "tests/tui/test_pilot_wizard.py (Task-3 suite: 5 tests incl. test_backstop_80x24_long_text_stays_enterable_and_readable)"
        status: pass
    human_judgment: false
    rationale-when-true: "cell-width arithmetic (region.width == 76) + Input buffer equality + joined-strip full-value membership"
  - id: prohibitions
    description: "The wizard writes no file anywhere (validation-only submission); no benchmark semantics (the split advisory is existence-only); no priority bindings; zero Chinese literals outside strings.py; modal isolation blocks the base-screen bindings"
    requirement: must_haves prohibitions 1-3 + I18N-01
    verification:
      - kind: automated
        ref: "grep gates (wizard.py zero-Chinese exit 1; the 09-03 no-priority grep over tui/ stays green) + the 344-test tests/tui lane"
        status: pass
    human_judgment: false
    rationale-when-true: "source greps + ModalScreen semantics (Phase 8 Pitfall 11, inherited)"
duration: 41 min
completed: 2026-10-12
status: complete
---

# Phase 09 Plan 4: Wizard Collection Half (模型/数据集向导 + CUST-03 报告视图) Summary

One-liner: The custom-onboarding wizard family's collection half landed — one ModalScreen over declarative step tables rendering both four-step forms with D-03 type-aware controls (single-pick SelectionLists, advisory path/numeric lines that never block), the b/esc/enter semantics with the esc-confirm destructive gate, the submit → numbered collect-all report view, the gauntlet-phase slot + f/o/on_valid seams for 09-05, and the D-12 prefill — with the 80×24 long-text backstop lifted as a passing Pilot pin.

## Performance

- 3/3 tasks, 6 commits (3 RED + 3 GREEN, all TDD), 41 min (estimate: 36000 tokens / 3 tasks; actual 19147 tokens over a 1811-insertion diff — estimate 47% high, the declarative-table design compressed the two forms into one screen).
- Verification: tests/tui 344 passed (22 new wizard tests), full repository suite 913 passed, `make lint` + `make typecheck` zero findings, wizard.py zero-Chinese grep exit 1, the 09-03 no-priority grep green with the new module on disk.
- RED evidence: `.planning/tdd-evidence/09-04-task{1,2,3}-red.json`, all RED_EVIDENCE_OK (targets: step-1 render assertion / report emission order / prefill fold).

## Accomplishments

- **tui/screens/wizard.py** — `WizardModal(ModalScreen)`: `_phase` (form|report|gauntlet) + `_step` + the one `_values` store; compose renders the active view; MODEL_STEPS/DATASET_STEPS declarative tables (FieldSpec field/wid/control/vocabulary/label_key) with the fixed enums imported from the 09-01 service and species/Tokenizer/metric vocabularies injected; enter advances (Input.Submitted + the screen binding), b goes back, esc branches by phase (report/gauntlet return; blank form dismisses; entered values confirm through ConfirmModal with the filled-step count); single-pick deselect-by-value; advisory lines via the injected dir_exists/file_exists probes (defaults resolve against the pipeline dir exactly like the 09-01 fs_root); the submit path composes the candidate (stamps nothing service-owned), runs the injected validator, renders the numbered report in a wrapping RichLog, and hands clean passes to the gauntlet slot + on_valid.
- **tui/strings.py** — the WIZ chrome block verbatim from the Copywriting Contract: border title, step names (WIZM_/WIZD_), quirk labels, path/numeric advisory lines, footer hints (next + submit variants), esc-confirm, report title/hint, gauntlet title + pending hint, import/export labels.
- **tui/styles.tcss** — the wizard family rules (theme tokens only): the width-100 amendment base (code caps to min(100, w-4)), modal padding, the advisory ok/bad/dim classes, the report log's wrap-scroll bound.
- **tests/tui/test_pilot_wizard.py** — 22 Pilot tests over the real app with every seam faked: step rendering, semantics, preservation, esc-confirm, single-pick, advisories, report ordering/wrap, on_valid payloads (both kinds), the 28-name metric vocabulary, prefill round-trips, the D-12 collision, f/o step-1 gating, and the 80×24 backstop.

## Task Commits

| Task | Commit | Type |
|------|--------|------|
| 1 RED — model-form Pilot suite + skeleton + WIZ chrome strings | 7869369 | test |
| 1 GREEN — wizard shell + model form (steps, controls, esc/b/enter) | ecdd035 | feat |
| 2 RED — dataset form + report suite + WIZD_ strings | 8b369f0 | test |
| 2 GREEN — dataset form + submit → collect-all report view | 8e97699 | feat |
| 3 RED — prefill + f/o + backstop suite + import/export labels | f8bd6bf | test |
| 3 GREEN — prefill (D-12) + f/o seams + 80×24 backstop lift | 9217a0d | feat |

## Files Created/Modified

Created: `tui/screens/wizard.py`, `tests/tui/test_pilot_wizard.py`. Modified: `tui/strings.py` (additive WIZ blocks), `tui/styles.tcss` (additive wizard rules).

## Decisions Made

See key-decisions (frontmatter). Highlights: the one-screen phase machine making preservation structural; split-file names as advisory-only collection with Train/Dev/Test never composing; the stamps-nothing candidate composition; the dual enter path; three probe-pinned 8.2.8 facts (TCSS min(), border_title markup, deselect-by-value).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Textual CSS cannot express the width amendment**
- **Found during:** Task 1 implementation.
- **Issue:** the Spacing amendment's `min(100, width−4)` cannot be written in TCSS — `min()` and cell arithmetic are parse errors on textual 8.2.8 (probe-pinned against the installed Stylesheet).
- **Fix:** styles.tcss carries the base `width: 100` + the token-only rules; `WizardModal._apply_chrome` applies the exact formula on mount and resize.
- **Files modified:** tui/screens/wizard.py, tui/styles.tcss
- **Commit:** ecdd035

**2. [Rule 1 - Bug] Source-scan greps are comment-blind — two docstring mentions tripped existing gates**
- **Found during:** Task 1 verification (the full tests/tui lane).
- **Issue:** the wizard docstring's literal mention of the prohibited priority-binding construct failed the 09-03 no-priority grep (regex over the whole source); the same class of issue defines the zero-Chinese gate.
- **Fix:** docstring reworded to describe the prohibition without the literal pattern; the module ships zero Chinese characters anywhere including comments.
- **Files modified:** tui/screens/wizard.py
- **Commit:** ecdd035

**3. [Rule 3 - Blocking] ty type-clean adaptations**
- **Found during:** Task 1/2 verification (`make typecheck`).
- **Issue:** heterogeneous kind dict, blind-except advisory query, Option-typed SelectionList iteration, and the ConfirmModal `()->None` callback vs `dismiss()`'s AwaitComplete return tripped diagnostics.
- **Fix:** KindSpec dataclass; `.first(Static)` advisory lookup; single-pick deselects BY VALUE (the API accepts values — also the cleaner loop); a `_abandon` None-returning wrapper for the confirm callback.
- **Files modified:** tui/screens/wizard.py
- **Commit:** ecdd035 / 8e97699

**4. [Test refinement] Two Task-2 Pilot harness bugs fixed at GREEN**
- The esc-preservation test pressed b once expecting step 4→1 (b is one step per press), and the clean-pass test typed a step-4 field while still on step 3. Both fixed in the tests; assertion strength unchanged (the values-intact assertions are exactly the planned ones).

## Issues Encountered

None open. No auth gates, no checkpoints (fully autonomous plan).

## User Setup Required

None. The wizard writes nothing (validation-only; D-08's gauntlet is 09-05's write path).

## Known Stubs

Intentional, plan-scoped functionality gaps (recorded in the broken-windows ledger, ids 17-19):

| Stub | File:line | Resolution |
|------|-----------|------------|
| Gauntlet phase renders a minimal pending view (title + the 待检 line) | tui/screens/wizard.py:419 | 09-05 wires the real subprocess panel over the on_valid seam |
| `f` binding routes to the on_import seam, no view behind it | tui/screens/wizard.py:708 | 09-05's file-import view (D-11; the seam is a plain callback) |
| `o` binding routes to the on_export seam, no view behind it | tui/screens/wizard.py:713 | 09-05's registry-export view (D-11) |

## Next Phase Readiness

- 09-05 (gauntlet + import/export views) consumes: `on_valid(candidate)` (the exact composed payload shape is Pilot-pinned), the gauntlet phase slot (replace the pending view's compose branch), `on_import`/`on_export`, and the 09-01 import/export services; it binds the REAL validator (pre-bound ValidationSources) into the constructor's validator seam.
- 09-06 (selection presentation) consumes: the `w`-key push with the cursor custom row's one-item `{key: entry}` prefill map and the injected vocabularies (species/tokenizer observed values, sorted METRIC_REGISTRY).
- The modal family's width amendment, advisory classes, and footer-hint pattern are reusable for the 09-05 gauntlet panel (same modal chrome).

## TDD Gate Compliance

All three tasks RED→GREEN with persisted, gate-validated evidence (INVALID_RED guarded):

- **Task 1 RED** (`RED_EVIDENCE_OK`, target `test_model_step_one_renders_ui_spec_fields_and_title`): 8 fail / 1 pass — the skeleton renders only the footer hint.
- **Task 2 RED** (`RED_EVIDENCE_OK`, target `test_submit_renders_the_numbered_report_in_field_order`): 8 fail / 9 pass — the dataset kind does not exist and step-4 enter does not route to a report.
- **Task 3 RED** (`RED_EVIDENCE_OK`, target `test_prefill_fills_every_model_field_across_all_steps`): 4 fail / 18 pass — the prefill seam stored but never folded; the 80×24 backstop pin passed on the Task-1/2 mechanics as expected (it pins, not introduces).
- Every GREEN commit ran the FULL wizard suite before the feat commit (and the full tests/tui lane at plan level); no test was weakened to pass — the two harness fixes (Deviation 4) kept every planned assertion.

## Self-Check: PASSED

All 2 created files exist on disk; all 6 task commits (7869369, ecdd035, 8b369f0, 8e97699, f8bd6bf, 9217a0d) are ancestors of HEAD; commits measured 6 via `git rev-list --count 3906acb..HEAD` (matches `actuals.commits`); tests/tui 344 passed, full suite 913 passed, lint + typecheck clean.
