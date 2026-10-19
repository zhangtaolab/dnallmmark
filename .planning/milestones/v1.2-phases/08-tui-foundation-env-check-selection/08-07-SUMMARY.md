---
phase: 08-tui-foundation-env-check-selection
plan: 07
subsystem: tui (selection + matrix screens, app screen wiring)
tags: [tui, selection, matrix, pilot-tests, i18n, mark-set, presets, templates, presence, sel-01, sel-02, sel-03, sel-04, i18n-01]
requires:
  phase: []
provides: []
provides:
  - "tui/screens/selection.py — the k9s selection surface: SelectionServiceProtocol injection seam + real SelectionBackend (tolerant registry reads, D-06 preset derivation with customs, D-07 collect-all import + valid-by-construction export/tiers), one recomposed DataTable with the m toggle, the mark column updated in place over the shared app-state sets, the filter Input over the injected parse/apply pair, preset/template modals with REPLACING + fail-closed semantics, presence cells from the 08-04 sentinel shapes, the row-detail modal, loading/registry-failure/no-match states"
  - "tui/screens/matrix.py — the read-only 62x50 h-scroll presence grid: fixed 24-cell model column, 8-cell headers with the diamond mark prefixes, single presence glyphs, the live full-task-key cursor readout, the enter full-key modal, exactly the esc/enter bindings (read-only by absent bindings, source-gated)"
  - "tui/app.py additions — the shared app-state mark sets + build_selection_screen factory + action_open_selection: every selection/matrix screen reads the SAME live sets, so filter rebuilds, table switches, and screen pushes can never lose marks (screens are never zero-arg SCREENS slots)"
  - "tui/strings.py — the complete SEL_/MATRIX_ blocks (Copywriting Contract verbatim + the three documented gap-filler toasts/copy and the unsurfaced clear-marks confirm)"
  - "the two 80-column backstop Pilot tests + the cross-screen navigation integration test (env -> s -> filter -> mark -> preset -> v -> matrix -> esc -> q)"
affects:
  - tui/screens/selection.py
  - tui/screens/matrix.py
  - tui/app.py
  - tui/strings.py
  - tui/styles.tcss
  - tui/screens/env_check.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_env_check.py
  - pyproject.toml
  - uv.lock
actuals:
  tokens: 39851    # chars/4 over the realized code diff (159403 chars, tui/+tests/+pyproject/uv.lock); full realized diff incl. the two embedded JUnit RED-evidence records is 52315
  tasks: 3
  commits: 5       # measured: git rev-list --count cf183521..HEAD (2 test-RED + 2 feat-GREEN + 1 test backstops/integration)
plan_head_before: cf183521ce564e34a7d2cf9ea67c58fdee896a77
plan_head_after: 42c82a5da175524aa47bd5d8a951e9c28d36cba5
tech-stack:
  added: []         # zero new packages — jsonschema (>=4.26.0, the same locked range as dev) JOINED the existing [tui] group per the 08-05 handoff flag; textual 8.2.8 + platformdirs unchanged
  patterns:
    - "shared-set screen factories: marks live in app-state sets passed BY REFERENCE to every screen (never zero-arg SCREENS slots — a slot-built screen would carry fresh sets and silently lose the SEL-01 persistence guarantee)"
    - "the 80-column column budget as a testable invariant: sum(column widths) + 2*ncols (cell padding) + 2 (scrollbar) <= 80, pinned by the backstop over real registry keys"
    - "compact footer + show_command_palette=False on the dense selection screen — the 80-column binding-map budget (ctrl+p keeps working, only the hint hides)"
    - "TYPE_CHECKING-only cross-screen imports: matrix.py annotates SelectionData without importing it at runtime (selection imports MatrixScreen for the v push — the cycle breaks at type time)"
    - "ModalScreen.dismiss pops the TOP screen — a callback that pushes the next modal (the save-overwrite confirm) defers one refresh so the dismissal lands first"
key-files:
  created:
    - tui/screens/selection.py
    - tui/screens/matrix.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_matrix.py
    - .planning/tdd-evidence/08-07-task1-red.json
    - .planning/tdd-evidence/08-07-task2-red.json
  modified:
    - tui/strings.py
    - tui/app.py
    - tui/styles.tcss
    - tui/screens/env_check.py
    - tests/tui/test_pilot_env_check.py
    - pyproject.toml
    - uv.lock
key-decisions:
  - "Marks live in shared app-state sets constructed once on the composition root and passed BY REFERENCE through build_selection_screen / the v push — the SCREENS registry deliberately does NOT gain selection/matrix slots (a zero-arg slot-built screen would carry fresh sets and silently violate the SEL-01 persistence truth; the 08-06 'slot mechanism' comment is superseded by the mark-sharing requirement)"
  - "Model-table presence cells render the unknown copy (◌ 未知): models are not n_audit subjects — the real backend fills presence per DATASET key only. The UI-SPEC Screen 2 mockup's per-split counts on model rows were a hand-sketch error (the 08-06 'mockup summaries are sketches' precedent); the counts belong to dataset rows, where they render"
  - "Presence cells carry the FULL contract format (no pre-truncation) — the DataTable clips display at the column budget (no wrap, row height 1); pre-truncation is only for the long registry key column, where the ellipsis is the designed truncation"
  - "The selection footer is compact with the command-palette hint disabled: 9 binding labels + margins exceed 80 cells in the default style — ctrl+p keeps working, only the hint hides; the footer backstop walks the shown bindings and asserts each renders untruncated with no pairwise overlaps"
  - "Preset/import unknown keys are RECOMPUTED against the loaded registry in the screen (not read off the service's unknown_keys channel): stale saved customs warn too, never silently dropped — the same loud-skip discipline for every apply path"
  - "The env→selection s binding is declared on EnvCheckScreen (per-screen scoping per the keyboard map) targeting the app factory via the qualified 'app.open_selection' action — the action lives where the shared sets live"
  - "Gap-filler copy landed and documented: SEL_PRESENCE_UNKNOWN (the four-status vocabulary lacked render copy), SEL_PRESET_SAVED / SEL_TEMPLATE_IMPORTED (the truths pin 'a toast fires' but only the applied/exported toasts were worded), and SEL_CLEAR_MARKS_CONFIRM landed for the record with NO trigger ('if surfaced' — the keyboard map defines no clear binding)"
  - "jsonschema>=4.26.0 joined the [tui] group (the 08-05 handoff flag): the selection screen's backend imports tui.services.templates at module top, so the make tui display lane (--group tui --group gpu) needs it or the console ImportErrors at composition"
patterns-established:
  - "the tier-2 Pilot test shape over the SelectionServiceProtocol seam: FakeSelectionService delegates parse/apply to the REAL pure 08-05 functions over fake entries (the plan's 'apply_filter (fake entries)') while everything stateful is canned — the grammar is exercised genuinely, the IO never runs"
  - "backstop tests as layout invariants: rendered-strip assertions (render_lines) + row-height sets + the column-budget formula — no pixel goldens, no snapshot files (TEST-01 stays Phase 12)"
  - "source-level no-forbidden-binding gates in the suite: the matrix test greps its own module for the mark/filter/preset action vocabulary, making the out-of-scope ban permanent CI enforcement"
requirements-completed: [SEL-01, SEL-02, SEL-03, SEL-04, I18N-01]
coverage:
  - id: D1
    description: "SEL-01 selection surface — model/dataset tables browsed one at a time (m toggle, both column sets, rows keyed on stable registry keys, zebra stripes, the 80-column budget with ellipsis truncation and enter row detail); the k9s filter (type-to-filter over the injected parse/apply pair, live (N/total) readout, unknown-axis warning while valid terms apply, no-match row, esc clear+refocus); the spacebar mark-set in app state keyed on registry keys, updated in place via update_cell on a dedicated column, surviving filter rebuilds and table switches; loading/registry-failure empty states with the app alive"
    requirement: SEL-01
    verification:
      - kind: unit
        ref: "tests/tui/test_pilot_selection.py (23 tests): boot/toggle/marks-persist, mark+status zero-one-many, filter rebuild/marks-survive/no-match/unknown-axis, loading-row (Event-gated), registry-failure state, row detail, plus the 80x24 long-key backstop and the 80-col footer backstop"
        status: pass
      - kind: other
        ref: "Task 1 verify gates: pytest tests/tui/test_pilot_selection.py 23 passed; grep CJK on tui/screens/selection.py exits 1; the mark mechanism uses update_cell on the dedicated mark column — no table-internal selection APIs anywhere (Pitfall 1)"
        status: pass
    human_judgment: false
    rationale: "Row keys, cell formats, set membership, readouts, and state rows are all mechanically asserted against the strings constants and the fake fixtures; the budget and footer backstops assert rendered geometry."
  - id: D2
    description: "SEL-02 presets — the p modal (SelectionList) applies with REPLACING semantics: tier-1 marks pair models AND tasks, tier-2 models only, all every key in both lists, customs restore both sets as saved; unknown keys recomputed against the loaded registry are skipped with the loud warning listing them; the success toast fires; the menu order is tier-1, tier-2, all, customs sorted; the empty-customs entry renders with the save-flow hint; the save flow's overwrite confirm works both ways"
    requirement: SEL-02
    verification:
      - kind: unit
        ref: "test_preset_modal_replaces_both_mark_sets_with_toast; test_preset_unknown_keys_warn_loudly_and_skip; test_custom_preset_applies_from_the_menu; test_save_preset_overwrite_confirm_works_both_ways"
        status: pass
      - kind: unit
        ref: "backend sync: test_backend_preset_menu_over_the_committed_priorities (real priorities file, ids/unknowns/customs round-trip over a tmp config root)"
        status: pass
    human_judgment: false
    rationale: "Replacing semantics, warning content, toast copy, confirm behavior, and menu order are asserted as exact strings and set equalities over deterministic fakes and the committed priorities file."
  - id: D3
    description: "SEL-03 templates — the x menu (import/export/tier-convert): import validates collect-all through the service; failure renders the numbered problem list (header + numbered pointer lines) and applies NOTHING; success replaces the marks with the imported sets + toast; export and tier-convert write the operator-chosen path through the service with toasts; the tier conversion emits the priorities cross-product shape"
    requirement: SEL-03
    verification:
      - kind: unit
        ref: "test_template_import_failure_lists_problems_and_applies_nothing; test_template_import_success_applies_marks_with_toast; test_template_export_and_tiers_write_through_the_service"
        status: pass
      - kind: unit
        ref: "backend sync: test_backend_template_import_and_exports_round_trip (tmp files through the real load/validate/export/tiers — valid-by-construction exports re-import ok)"
        status: pass
    human_judgment: false
    rationale: "Fail-closed behavior, the numbered list content, applied sets, recorded service calls, and round-trip validity are all mechanically pinned."
  - id: D4
    description: "SEL-04 presence rendering — present cells render the pass glyph with thousands-separated exact train/dev/test counts (formatting only in the screen), missing cells the missing word, a present task with a zero-row split the exact 0, and the n_audit-absent column state the documented copy in every cell (both tables); the missing-flag decision stays service-side"
    requirement: SEL-04
    verification:
      - kind: unit
        ref: "test_presence_cell_formats_pin_the_contract (big/zero/missing/unknown cells); test_presence_column_renders_n_audit_missing_copy; the boot test's dataset-view count cell; the backend test pins the committed 62/50 + 7 missing GUE tasks"
        status: pass
    human_judgment: false
    rationale: "Cell formats are asserted as exact constant-formatted strings over Presence fixtures incl. the boundary cases; the committed-artifact shape is pinned by the real-backend test."
  - id: D5
    description: "SEL-01 auxiliary matrix — v pushes the read-only grid; esc pops back with marks intact; one row per model and one column per dataset keyed on registry keys, single presence glyphs, diamond prefixes on marked rows AND headers, headers truncated to 8 cells with the ellipsis, the full task key of the cursor column in the live readout, h-scroll exposes all columns at 80 with the fixed model column, enter opens the full-key modal, and NO mark/filter/preset binding exists (read-only by absent bindings, source-gated)"
    requirement: SEL-01
    verification:
      - kind: unit
        ref: "test_pilot_matrix.py (12 tests): push/pop marks-intact, grid/glyph/diamond render, unknown glyph, live readout, no-binding no-ops, h-scroll at 80, enter modal, n_audit-absent copy, env-s wiring, the zero-Chinese + no-forbidden-binding source gates, and the cross-screen integration"
        status: pass
      - kind: other
        ref: "Task 2 verify gates: pytest tests/tui/test_pilot_matrix.py 12 passed; grep -c Binding tui/screens/matrix.py = 6 (the esc/enter pair + modal escape); grep CJK exits 1"
        status: pass
    human_judgment: false
    rationale: "Grid geometry, glyphs, prefixes, readout content, scroll behavior, and the absent-binding no-ops are mechanically asserted; the out-of-scope ban is enforced by a permanent source gate."
  - id: D6
    description: "I18N-01 + the backstops + the composed app — every SEL_/MATRIX_ string lives in tui/strings.py (zero Chinese literals in selection.py, matrix.py, app.py — grep-gated); the 80x24 long-key backstop (no wrap-induced height change, presence column on-screen) and the 80-column footer backstop (every shown binding label untruncated, no overlaps) pass; the cross-screen integration (env -> s -> filter -> mark -> preset -> v -> matrix -> esc -> q) passes headless with fakes; the foundation invariants hold (services-textual-free import lock green, CI lane untouched, make test/lint/typecheck green)"
    requirement: I18N-01
    verification:
      - kind: unit
        ref: "test_backstop_longest_task_key_at_80x24; test_backstop_footer_renders_every_binding_label_at_80; test_cross_screen_navigation_integration; the zero-Chinese source gates in both new suites + the existing app/env gates"
        status: pass
      - kind: other
        ref: "plan-level gates: tests/tui 167 passed; make test 728 passed (Python slow lane + node JS lane); make lint 0; make typecheck 0; grep -rPn CJK over tui/screens/ + tui/app.py exits 1; .github/workflows byte-untouched"
        status: pass
    human_judgment: false
    rationale: "Single-home enforcement, backstop geometry, the composed flow, and every gate exit are machine-verified facts."
duration: 79 min
completed: 2026-10-11T16:00:24Z
status: complete
---

# Phase 08 Plan 07: Selection + Matrix Screens Summary

Landed the operator's daily selection surface — two k9s-style tables over the injected 08-04/08-05 services with a mark-set that survives every rebuild and switch, preset/template modals with replacing and fail-closed semantics, presence columns from n_audit — plus the read-only matrix overview and the full app wiring, closing Phase 8's SEL-01..04 and I18N-01 with 35 new Pilot tests including both 80-column backstops.

## Performance

- **Duration:** 79 min (14:41:01Z – 16:00:24Z, 2026-10-11)
- **Tasks completed:** 3 / 3 (Tasks 1-2 full TDD RED-GREEN cycles; Task 3 the backstops + integration + full gate lane)
- **Files changed:** 13 (6 created, 7 modified; +3846/−8 lines)
- **Commits:** 5 (measured from the persisted plan ledger `cf183521..HEAD`)
- **Estimate calibration:** code+tests ≈ 39851 tokens vs 20000 estimated (199% — the low-confidence estimate again undercounted the test surface: the two Pilot suites are 45% of the code diff, and the 23-test selection suite alone exceeds the whole estimate); full realized diff incl. the two embedded JUnit RED-evidence records is 52315 tokens

## Accomplishments

- **Task 1 — the selection screen (TDD):** RED landed the complete SEL_ strings block plus a full-layout skeleton (data shapes, the SelectionServiceProtocol seam, five ModalScreens, the column budget) against a 23-test suite — 21 failed on planned assertions, 0 errors, RED_EVIDENCE_OK. GREEN filled the behavior: the exclusive thread worker loads the snapshot and composes rows keyed on stable registry keys; the mark column updates in place via `update_cell` over the shared sets; the m toggle recomposes the table with the other column set while both mark sets live independently; the filter Input drives the injected parse/apply pair with the live (N/total) readout, the dim unknown-axis warning, the no-match row, and esc clear+refocus; the preset modal applies with REPLACING semantics and recomputed unknown-key warnings; the template menu is fail-closed (the numbered collect-all list, nothing applied) with export/tier-convert through the service; the save flow confirms overwrites; presence cells format the exact 08-04 counts; enter opens the never-elided row detail. The real SelectionBackend (tolerant registry reads naming the path, presence per dataset key, real-priorities preset derivation, strict-schema import/export) is covered by five sync tests over the committed artifacts and tmp roots.
- **Task 2 — the matrix + the wiring (TDD):** RED landed the matrix skeleton + an 11-test suite (9 failed on planned assertions, RED_EVIDENCE_OK). GREEN delivered the read-only grid — fixed 24-cell model column, one 8-cell glyph column per dataset with the diamond mark prefixes, the live full-task-key cursor readout, the enter full-key modal, esc pop — with exactly the esc/enter bindings and a permanent source gate banning the mark/filter/preset vocabulary from the module. The app wiring: `action_open_selection` (the env screen's s binding via the qualified app action), the selection v push over the loaded snapshot and the same live mark sets, and the env help-modal row.
- **Task 3 — backstops + integration + the full lane:** the 80x24 long-key backstop (the real 68-char registry key, 12-row fixture forcing the scrollbar: every row height 1, the budget formula fits, the presence column renders on-screen, the key truncates with the ellipsis) and the 80-column footer backstop (every shown binding label renders untruncated with no pairwise overlaps) both landed green, plus the composed navigation integration (env → s → filter → mark → preset → v → matrix → esc → q, quitting 0). Whole gates: tests/tui 167, make test 728 (Python slow lane + JS lane), make lint, make typecheck, and the i18n single-home grep — all green, CI workflow byte-untouched.
- **Proof, not inspection:** the full tests/tui tier is 167 green (130 prior + 37 new across the two suites); every verify command in the plan ran and exited clean; the two RED cycles were gate-validated (RED_EVIDENCE_OK) before each GREEN.

## Task Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 RED — selection suite + skeleton | `bfc477f` | test(08-07): add failing Pilot suite for the selection screen (RED) |
| 1 GREEN — the screen implementation | `dafcf94` | feat(08-07): implement the selection screen — tables, filter, marks, presets, templates, presence |
| 2 RED — matrix suite + skeleton | `6e7a4f1` | test(08-07): add failing Pilot suite for the matrix screen + wiring (RED) |
| 2 GREEN — matrix + wiring | `296118a` | feat(08-07): implement the read-only matrix screen + the app screen wiring |
| 3 — backstops + integration | `42c82a5` | test(08-07): 80-column backstops + the cross-screen navigation integration |
| plan metadata (docs) | (this commit) | docs(08-07): complete selection + matrix screens plan |

## Files Created/Modified

- **Created:** `tui/screens/selection.py`, `tui/screens/matrix.py`, `tests/tui/test_pilot_selection.py` (25 tests incl. the backstops), `tests/tui/test_pilot_matrix.py` (12 tests incl. the integration), `.planning/tdd-evidence/08-07-task{1,2}-red.json`
- **Modified:** `tui/strings.py` (the SEL_/MATRIX_ blocks), `tui/app.py` (the selection seam + shared sets + factory + action), `tui/styles.tcss` (selection/matrix/modal-box rules), `tui/screens/env_check.py` (the s binding), `tests/tui/test_pilot_env_check.py` (the help row), `pyproject.toml` + `uv.lock` (jsonschema joins `[tui]`)

## Decisions Made

- **Shared-set factories, not SCREENS slots:** marks live in app-state sets constructed once on the composition root and passed by reference; the SCREENS registry deliberately does not gain selection/matrix entries (a zero-arg slot-built screen would carry fresh sets and silently lose marks). The 08-06 "slot mechanism" comment is superseded — recorded in the updated app.py comment and the codebase STRUCTURE map.
- **Model presence = the unknown copy:** the real backend fills presence per DATASET key only (models are not n_audit subjects); the UI-SPEC mockup's counts on model rows were a hand-sketch error. Model rows render ◌ 未知 — honest, and Phase 10's data manager owns presence's future.
- **The 80-column budget as a formula:** sum(widths) + 2×ncols (cell padding) + 2 (scrollbar) ≤ 80 — validated empirically (probe + the backstop test) and encoded as the per-view width constants (66-cell sums).
- **Compact footer, palette hint off:** the nine shown binding labels exceed 80 cells in the default footer style; compact + `show_command_palette=False` fits with room (the backstop asserts no overlaps). ctrl+p still works — only the hint hides.
- **Unknown keys recomputed in the screen** for every apply path (presets AND imports) — stale saved customs warn too, never silently dropped.
- **jsonschema joined `[tui]`** (the 08-05 handoff flag): same locked range as dev; the display lane now carries what the screen's backend imports at module top.
- **Gap-filler copy, documented:** SEL_PRESENCE_UNKNOWN, SEL_PRESET_SAVED, SEL_TEMPLATE_IMPORTED (the truths pin the behavior but only some toasts were worded), and SEL_CLEAR_MARKS_CONFIRM landed unsurfaced per the contract's "if surfaced".
- **textual 8.2.8 facts pinned by probe:** `Input(compact=True)` for the 1-row filter field; `SelectionList` intercepts enter as a toggle (the preset modal applies on SelectionToggled); `from textual.coordinate import Coordinate` (not textual.geometry); `DataTable.cell_padding=1` drives the budget; `ModalScreen.dismiss` pops the TOP screen (deferred confirm pushes); `pilot.press` needs key names (`_character_to_key` for typing).

## Deviations from Plan

**1. [Rule 3 - file-list] app.py wiring landed in Task 1**
- **Found during:** Task 1 test design
- **Issue:** Task 1's `<files>` omits app.py, but its action requires "the app wires real defaults" and every Pilot test injects through `DnallmMarkTui(selection_service=...)`.
- **Fix:** Task 1 added the constructor seam + the shared mark sets + `build_selection_screen` (the 08-06 app.py precedent, verbatim).
- **Files:** tui/app.py — Commit: `bfc477f`

**2. [Rule 3 - file-list] styles.tcss landed in Task 1**
- **Issue:** Task 1's file list omits the stylesheet, but the screen's layout (title bar, filter bar, warning line, table, modal boxes) requires CSS rules and the UI-SPEC forbids inline styles.
- **Fix:** Task 1 GREEN landed the selection + shared modal-box rules; Task 2 added the matrix rules.
- **Files:** tui/styles.tcss — Commits: `dafcf94`, `296118a`

**3. [Rule 3 - dependency wiring] pyproject.toml + uv.lock in Task 1 GREEN**
- **Issue:** Not in any file list, but the 08-05 handoff flag (recorded in STATE decisions and the plan's own success criteria) requires jsonschema in `[tui]` the moment the selection screen wires template import — the backend imports `tui.services.templates` at module top.
- **Fix:** `jsonschema>=4.26.0` added to the `[tui]` group with a provenance comment; `uv lock` regenerated (2-line lock delta); the display-lane import verified.
- **Files:** pyproject.toml, uv.lock — Commit: `dafcf94`

**4. [Rule 3 - wiring scope] tui/screens/env_check.py + tests/tui/test_pilot_env_check.py in Task 2**
- **Issue:** Task 2's action wires "the selection screen registers the v binding" (touching selection.py — also not in its file list) and the env→selection `s` binding must live on EnvCheckScreen (per-screen scoping; the 08-06 summary explicitly deferred it to 08-07). The 08-06 help-modal test pins the binding rows and needed the new row.
- **Fix:** The s binding added to EnvCheckScreen (`app.open_selection` qualified action); selection.py's v push implemented; the help test gained the `[s] 选择` row.
- **Files:** tui/screens/env_check.py, tui/screens/selection.py, tests/tui/test_pilot_env_check.py — Commit: `296118a`

**5. [Rule 1 - implementation] presence-cell pre-truncation removed**
- **Found during:** Task 1 GREEN (the suite caught it)
- **Issue:** The first GREEN pre-truncated presence cells to the column width, corrupting the pinned contract formats (`✓ 743,095/109,717/106,227` and the n_audit copy) in stored cells.
- **Fix:** Presence cells carry the full format; the DataTable clips display at the budget (no wrap, height 1). Pre-truncation stays only for the long registry-key column, where the ellipsis is the designed truncation.
- **Files:** tui/screens/selection.py — Commit: `dafcf94`

**6. [Rule 1 - modal stack] the save-overwrite confirm push deferred one refresh**
- **Found during:** Task 1 GREEN (the save-flow test caught it)
- **Issue:** `ModalScreen.dismiss` pops the TOP screen — pushing the ConfirmModal inside the path modal's submit callback made the dismissal pop the confirm instead of the input modal.
- **Fix:** The confirm push goes through `app.call_after_refresh`, landing after the input modal's dismissal.
- **Files:** tui/screens/selection.py — Commit: `dafcf94`

**Total deviations:** 6 auto-fixed (4 Rule 3 file-list/wiring necessities the plan's own action text requires, 2 Rule 1 bugs the RED suite caught).
**Impact:** none on the plan's contracts — every truth and prohibition verified intact (shared-set persistence, replacing semantics, fail-closed import, read-only matrix by absent bindings, render-only presence, i18n single home, budget backstops).

## TDD Gate Compliance

Both TDD-flagged tasks completed full RED-GREEN cycles with gate-validated evidence:

| Task | RED commit | RED evidence | GREEN commit |
|------|-----------|--------------|--------------|
| 1 | `bfc477f` | RED_EVIDENCE_OK (23 tests, 21 failed, 0 errors; target `test_boot_columns_toggle_and_marks_persist_independently` failed inside its planned assertion — only the loading row renders) | `dafcf94` |
| 2 | `6e7a4f1` | RED_EVIDENCE_OK (11 tests, 9 failed, 0 errors; target `test_v_pushes_matrix_esc_pops_back_with_marks_intact` — action_open_matrix still the stub) | `296118a` |

RED method: full-layout skeletons with behavior absent (rows never compose past the loading row; actions no-op), so every target test executed and failed on its planned assertion — no collection, import, syntax, or fixture faults (JUnit `errors=0` in both records). The trivially-green tests against each skeleton are noted in the records' semantic assessments (Task 1: the zero-Chinese gate + the parse/apply delegation stub; Task 2: the two source gates pinning landed structure). Gate commits verified: 2 `test(08-07):` + 2 `feat(08-07):` + 1 `test(08-07):` (Task 3, not TDD-flagged) present in git log. No REFACTOR-phase commits — nothing warranted a post-GREEN refactor.

## Issues Encountered

- A circular import between selection.py and matrix.py surfaced at Task 2 GREEN (selection imports MatrixScreen for the v push; matrix imported SelectionData for annotations) — resolved with a TYPE_CHECKING-only import in matrix.py (annotation-only; the runtime data arrives structurally).
- Ruff's `--fix` on the RED skeletons removed then-unused imports (F401), which the GREEN behavior re-needed — restored with the GREEN commits; both commits are individually lint-clean.
- No auth gates, no package installs (jsonschema was already locked since Phase 2 — only its group membership changed), no pre-commit hook cycles, no checkpoints (all tasks type=auto).

## User Setup Required

None.

## Known Stubs

None — no placeholder patterns in the delivered files. The designed sentinels are specified behavior with tests: the loading/no-match/registry-failure/n_audit-absent states, the unknown-presence cell, the unsurfaced clear-marks confirm constant (landed per the Copywriting Contract's "if surfaced" wording — the keyboard map defines no clear binding in Phase 8; presets replace rather than clear), and the model-row unknown presence (the documented n_audit scope decision above).

## Next Phase Readiness

- **Phase 9 (custom onboarding wizards):** the selection screens are the declared entry-point surface — the shared-set/mark mechanism, the modal patterns (PathInputModal/ConfirmModal), the SelectionData snapshot, and the SelectionBackend's tolerant registry seam (which already reads the overlay-merged registries) are the wizard's integration points. The customs flow (save/load under the config root) is proven end-to-end by the preset tests.
- **Phase 10 (data manager):** presence reads flow through `SelectionData.presence` + `audit_available` — the manager's downloads flip presence by refreshing the snapshot; the `SEL_N_AUDIT_MISSING`/CLI-audit routing copy is already wired.
- **Phase 11 (run-config/launch):** the D-07 template import/export UI is proven; `ENV_QUICK_CHECK_*` and the gate verdict remain staged from 08-06; the mark sets are the run-spec seed.
- **Phase 12 (TEST-01):** snapshot goldens still deliberately absent — all Pilot assertions here are behavioral, per the plan prohibition.

## Self-Check: PASSED

- All plan artifacts — FOUND: `tui/screens/selection.py`, `tui/screens/matrix.py`, `tests/tui/test_pilot_selection.py`, `tests/tui/test_pilot_matrix.py` (committed across `bfc477f`/`dafcf94`/`6e7a4f1`/`296118a`/`42c82a5`)
- 2 tdd-evidence records — FOUND, both RED_EVIDENCE_OK-validated
- Task commits verified as ancestors of HEAD: `bfc477f`, `dafcf94`, `6e7a4f1`, `296118a`, `42c82a5`
- Commit count measured from the persisted ledger: 5 production commits (`git rev-list --count cf183521..HEAD`)
- TDD gate: 2 `test(08-07):` RED + 2 `feat(08-07):` GREEN + 1 `test(08-07):` backstops present (git log grep validated)
- Gates at plan close: tests/tui 167 passed; make test 728 passed (Python + JS lanes); make lint 0; make typecheck 0; i18n grep clean over tui/screens/ + tui/app.py; the two 80-column backstops + the cross-screen integration green
