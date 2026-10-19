---
phase: 09-custom-model-dataset-onboarding
plan: 09-06
subsystem: tui/screens selection custom-entry presentation (CUST-06 + the CUST-01/02 entry point)
tags: [tui, selection, custom-entries, badge, enable-disable, prefill, count-line, i18n, phase-close]
requires:
  - 09-01 (custom_entries store read/land/undo/set_enabled + custom_validation ValidationSources/METRIC_REGISTRY)
  - 09-02 (GauntletService per-leg entry points + the D-09 loader skip)
  - 09-03 (the nav shell bars + NAV_SLOTS the w/e chrome joins)
  - 09-04/09-05 (WizardModal constructor seams — validator/gauntlet/land/undo/import/export/prefill/vocabularies)
  - 08-07 (the selection screen, SelectionData/SelectionBackend, the bottom-bar declaration-order contract)
provides:
  - "The w binding (D-14): the wizard entry for the ACTIVE table's kind with the D-12 prefill from the cursor's custom row — the menu carries no wizard item"
  - "The e binding (D-09): the atomic enable/disable toggle with the state-pair toasts and the honest official-row no-op"
  - "The D-10 presentation: the diamond badge on both tables' key cells (bold+accent enabled / dim + the disabled suffix), the conditional count segment (官方 o/o · 自定义 c/c, both states counted), and the disabled-mark block with the warning toast"
  - "CustomOnboardingBackend: the w/e service seam composing the real validator sources + observed vocabularies + the 28-metric registry + GauntletService + the 09-01 store seams into one WizardModal (the composition root wiring that makes the wizard operator-reachable)"
  - "The management second read composed into SelectionBackend (Pitfall 7): disabled customs appended after the overlay-merged entries, custom_status recording the custom/official + enabled truth"
  - "The full-loop integration story (both kinds) + the i18n grep locks over wizard.py/about.py + green phase gates (lint/typecheck/test 943 + node 18/0)"
affects:
  - tui/services/custom_entries.py (additive registry_dir read param — the two-views-one-file invariant)
  - Phase 9 closes: CUST-01/02/03/06 all complete; ROADMAP criteria 1-5 evidenced
actuals:
  tokens: 24895   # chars/4 over the realized diff (99582 diff chars)
  tasks: 3
  commits: 5      # MEASURED: git rev-list --count 1f4bde1..HEAD
plan_head_before: 1f4bde1c187c3d920b364ff7ce158706cb0880cf
plan_head_after: 34f5d175b2f55d764d89770df2b54775379aac3b
tech-stack:
  added: []        # zero new packages (T-09-SC: textual 8.2.8 + the in-repo services only)
  patterns:
    - "optional screen-constructor service injection with real defaults (custom_service) — Phase 8 fakes conform unchanged, no protocol widening"
    - "lazy cross-module import inside the composition method (wizard imports ConfirmModal from selection — the cycle broken at call time, never import time)"
    - "overlay-root-honoring management read (read_entries(registry_dir=...)): the merged view and the management view always describe ONE file"
    - "resolved-live-theme span styling (rich spans cannot carry $token styles — the 09-03 probe re-encountered in DataTable cells)"
key-files:
  created:
    - tests/tui/test_pilot_selection_custom.py
  modified:
    - tui/screens/selection.py
    - tui/strings.py
    - tui/services/custom_entries.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_env_check.py
key-decisions:
  - "The w/e seams are an optional SelectionScreen constructor injection (custom_service: CustomOnboardingBackend by default) rather than SelectionServiceProtocol widening — the Phase 8 fakes and the protocol stay byte-unchanged (the additive-conformance truth); the backend composes the real validator (ValidationSources with official = merged minus landed customs, exact under the loader's collision fail-fast), the registry-observed species/tokenizer vocabularies, sorted METRIC_REGISTRY, GauntletService, and the 09-01 store seams, with every land/undo firing the screen's exclusive data-refresh worker"
  - "WizardModal is imported lazily inside build_wizard: wizard.py imports ConfirmModal from selection.py, so a module-top import would be circular — the composition runs on a w press, long after both modules load"
  - "The management second read honors DNALLMMARK_CUSTOM_REGISTRY_DIR through the additive read_entries(registry_dir=None) param: the overlay-merged view and the management view always describe ONE file (Pitfall 7's never-disagree truth), and the Phase 8 backend tests stay machine-independent (without it, the composition would merge a pinned-empty overlay against the real home's landed customs the day the maintainer lands one — a 62/50-count landmine)"
  - "Disabled-entry semantics are blocked at every mark entry, not just the spacebar: _deliverable_keys excludes disabled customs from the preset/template known-key sets, so a preset referencing one rides the Phase 8 unknown-key loud skip (warned, skipped) — T-09-13's 'blocked at entry, never discovered at launch' applied to the bulk-replace paths"
  - "Probe re-encounter (the 09-03 nav-bar fact): rich Text SPANS styled with $token strings crash rendering (MissingStyle) — whole-text styles resolve tokens but spans do not; the badge span carries the caller-resolved live theme accent (f\"bold {app.current_theme.accent}\", the nav.py precedent) and the disabled spans use rich-native dim"
  - "The count segment derives BOTH sides from the management-read custom_status map (visible = counted): custom counts = entries whose key is in the map, official = the remainder; zero customs renders the byte-identical Phase 8 line (pinned by test)"
patterns-established:
  - "The per-screen custom-action service seam (one injected namespace over store + wizard composition) — the pattern for later screens that need both real defaults and Pilot-fake injection without touching the shared protocol"
  - "The two-view registry composition idiom (merged view + management read union, keyed against official keys, de-duplicated) — the reference for any future surface that must show what the pipeline hides"
requirements-completed: [CUST-01, CUST-02, CUST-03, CUST-06]
# CUST-01/02/06 are this plan's declared set; CUST-03 closes here too —
# its pieces (the 09-01 validator + the 09-04 report view) were held
# Pending until the composition root bound the REAL validator into the
# wizard (the 09-04 summary's explicit hand-forward), which is exactly
# what CustomOnboardingBackend.build_wizard does.
coverage:
  - id: WE-BINDINGS
    description: "w opens the wizard for the active table's kind with the D-12 prefill from the cursor's custom row (blank from every other cursor state; both cursor states and both kinds Pilot-asserted; no menu wizard item); e flips custom rows through the atomic store seam with the state-pair toasts (disable carrying the loader-level note) and the honest official no-op toast; the bottom bar declares w/e before the auxiliary actions"
    requirement: CUST-01/CUST-02 entry point + D-09/D-14
    verification:
      - kind: automated
        ref: "tests/tui/test_pilot_selection_custom.py (Task-1 suite: 8 tests incl. the menu pin)"
      - kind: automated
        ref: "the loader-skip visibility test: real SelectionBackend + real store + real registry_loader on tmp roots — the disabled key stays in the snapshot (63) while the merged registry drops it (62), official bytes pinned unchanged"
    human_judgment: false
    rationale-when-true: "Pilot key-event drives + real-seam file assertions over monkeypatched tmp roots"
  - id: CUST06-PRESENTATION
    description: "The D-10 contract: the diamond badge on both tables' key cells (bold+accent enabled, dim+suffix disabled, official rows spanless — the adjacency edge), the conditional count segment counting landed entries of both states from the management read (zero customs = the byte-identical Phase 8 line), the disabled-mark block with the warning toast (shared set unchanged), and the preset loud-skip over a disabled key"
    requirement: CUST-06 / D-10 / T-09-13
    verification:
      - kind: automated
        ref: "tests/tui/test_pilot_selection_custom.py (Task-2 suite: the landed+disabled one-table-state fixture + the zero-customs pin + the real-backend both-view counts)"
    human_judgment: false
    rationale-when-true: "rendered-cell plain text + span-style assertions + byte-comparable status-line equality"
  - id: FULL-LOOP
    description: "One operator story over one user-owned file, both kinds: w -> fake-clean validation -> all-pass gauntlet (dry-run only for models; both legs for datasets) -> real-store land -> dismiss -> the badge + the custom count segment in the refreshed table -> e -> the suffix + the real-loader exclusion while the row stays visible; official registry bytes pinned unchanged across every write"
    requirement: CUST-01/CUST-02/CUST-06 (ROADMAP criteria 1, 2, 4, 5 in one executable story)
    verification:
      - kind: automated
        ref: "tests/tui/test_pilot_selection_custom.py (Task-3 suite: test_full_loop_models_... + test_full_loop_datasets_...)"
    human_judgment: false
    rationale-when-true: "the real SelectionBackend + the real 09-01 store under both pinned env roots; only the validator and the gauntlet legs are fakes (their own tier-1/tier-2 suites own the real paths)"
  - id: I18N-GREP
    description: "The zero-Chinese-literals grep locks extend to tui/screens/wizard.py and tui/screens/about.py in both carrier files (module-list tuples only, assertion logic unchanged) and pass; selection.py stays zero-Chinese"
    requirement: I18N-01 close-out
    verification:
      - kind: automated
        ref: "grep -rn '[一-鿿]' tui/screens/wizard.py tui/screens/about.py -> exit 1; test_pilot_selection.py + test_pilot_env_check.py grep-lock tests green"
    human_judgment: false
    rationale-when-true: "source greps"
duration: 91 min
completed: 2026-10-12
status: complete
---

# Phase 09 Plan 06: Selection Integration + Phase Close (CUST-06 + w/e 接入/停用) Summary

One-liner: The selection surface closed Phase 9 — w opens the kind-routed wizard with the D-12 prefill (the real validator/gauntlet/store wired at a new composition seam), e toggles custom entries through the atomic store with honest toasts, the ◇ badge + （已停用） + the 官方/自定义 count line render from the Pitfall-7 management second read, disabled-marking and preset references to disabled keys are blocked at entry, and the full w→gauntlet→land→badge→e→loader-exclusion loop is pinned green for both kinds with every phase gate clean.

## Performance

- 3/3 tasks, 5 commits (2 RED + 2 GREEN + 1 integration/gates), 91 min (estimate: 24000 tokens / 3 tasks; actual 24895 tokens over a 1482-insertion diff — on target).
- Verification: tests/tui 374 passed (13 new tests in the new module), full repository suite **943 passed** (`make test`, slow lane + node:test 18 pass / 0 fail), `make test-fast` 942 passed, `make lint` + `make typecheck` zero findings, the wizard/about zero-Chinese grep exit 1.
- RED evidence: `.planning/tdd-evidence/09-06-task{1,2}-red.json`, both RED_EVIDENCE_OK (targets: the w-routing test — SelectionData lacked custom_status; the landed+disabled fixture — the badge assertion).

## Accomplishments

- **w/e bindings (Task 1):** the migration-table declaration order (after the mark/preset bindings, before the auxiliary v); `action_open_wizard` resolves the active view's kind + the cursor key, prefills from the management read when the row is custom, and pushes the composed wizard with the land-completion callback wired to the existing exclusive refresh worker; `action_toggle_enabled` flips through the injected atomic seam with the state-pair toasts, the official no-op toast, and a refresh-to-truth on a vanished entry.
- **CustomOnboardingBackend (Task 1):** the w/e service seam — real `ValidationSources` (official = merged minus landed customs), registry-observed species/tokenizer vocabularies, sorted METRIC_REGISTRY, GauntletService, and land/undo/import/export/empty-state seams pre-bound into one WizardModal; the lazy import breaks the wizard→selection module cycle.
- **Backend truth (Task 1):** `SelectionData.custom_status` (additive, default {}) + `load_selection_data` composing the overlay-merged entries with the management second read (disabled customs appended after the merged view, keyed against official keys, de-duplicated) — both reads resolve ONE file through the overlay-root-honoring `read_entries(registry_dir=...)`.
- **D-10 presentation (Task 2):** the `_key_cell` badge renderer (bold+accent / dim+suffix; official rows spanless), the conditional dim count segment (counts from the management map, both states; zero customs byte-identical Phase 8), the disabled-mark block (warning toast, shared set unchanged), and `_deliverable_keys` putting disabled customs outside the preset/template known-key sets (the Phase 8 unknown-key loud skip).
- **Full loop + close-out (Task 3):** both-kind integration stories over one user-owned tmp file (real backend + real store; fake-clean validator + all-pass gauntlet legs), the i18n grep locks extended to wizard.py/about.py, and the phase gates recorded above.

## Task Commits

| Task | Commit | Type |
|------|--------|------|
| 1 RED — w/e binding suite + SEL_ copy | f9b4d24 | test(09-06) |
| 1 GREEN — w wizard entry + e toggle + loader-skip visibility | 9b83965 | feat(09-06) |
| 2 RED — D-10 presentation suite | 5ee8659 | test(09-06) |
| 2 GREEN — badge + suffix + count segment + mark block | 1689c65 | feat(09-06) |
| 3 — full-loop story + i18n grep close-out + phase gates | 34f5d17 | test(09-06) |

## Files Created/Modified

Created: `tests/tui/test_pilot_selection_custom.py`. Modified: `tui/screens/selection.py` (bindings, actions, seam, backend composition, badge/count/mark-block), `tui/strings.py` (the SEL_ custom block, verbatim from the Copywriting Contract), `tui/services/custom_entries.py` (additive `registry_dir` read param), `tests/tui/test_pilot_selection.py` + `tests/tui/test_pilot_env_check.py` (the grep-lock module lists + the help-modal chrome pin).

## Decisions Made

See key-decisions (frontmatter). Highlights: the optional-injection seam over protocol widening; the lazy wizard import; the two-views-one-file management read; entry-blocking for disabled keys across every mark path; the resolved-accent span styling.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The Phase 8 help-modal test pins the exact binding row list**
- **Found during:** Task 1 verification (the full tests/tui lane).
- **Issue:** the `?` help modal auto-reflects the screen's declared bindings (the UI-SPEC's discoverability backstop), so the new w/e rows extended the pinned row list and `test_help_modal_opens_on_the_selection_screen` failed.
- **Fix:** the pinned list gained the two rows at their declaration position — the same chrome-pin-update class as 09-03's retired-chrome assertions; no assertion logic changed. Task 2's "zero edits to any Phase 8 test file" criterion held at its point in time; this edit landed with Task 1's GREEN (before Task 2's RED).
- **Files modified:** tests/tui/test_pilot_selection.py
- **Commit:** 9b83965

**2. [Rule 2 - Missing-critical] The management read needed the overlay-root override**
- **Found during:** Task 1 design (before implementation).
- **Issue:** `custom_entries.read_entries` hard-resolves the TUI config root; with only `DNALLMMARK_CUSTOM_REGISTRY_DIR` pinned (the Phase 8 backend tests' pattern), the composition would merge a pinned-empty overlay against the real home's landed customs — machine-dependent test counts (62→63 the day the maintainer lands a custom) and two views that can disagree about which keys exist (the exact Pitfall 7 invariant the plan locks).
- **Fix:** the additive optional `registry_dir` param on `read_entries`/`custom_registry_path` (None = the unchanged config root; the write side never honors it); the backend passes the overlay env root. `tui/services/custom_entries.py` is outside the plan's files_modified — the change is additive, every existing caller unchanged, the tier-1 suite green unmodified.
- **Files modified:** tui/services/custom_entries.py, tui/screens/selection.py
- **Commit:** 9b83965

**3. [Rule 1 - Bug] Rich spans cannot carry `$token` styles**
- **Found during:** Task 2 GREEN (first run — MissingStyle on the badge cells).
- **Issue:** the badge/suffix/count-segment spans styled with `$accent`/`$text-muted` crashed the DataTable render path — whole-text styles resolve tokens, spans do not (the 09-03 nav-bar probe, re-encountered).
- **Fix:** the badge span carries the caller-resolved live theme accent (the nav.py precedent); the disabled spans and the count segment use rich-native `dim`.
- **Files modified:** tui/screens/selection.py
- **Commit:** 1689c65

**4. [Test refinements] Harness fixes (assertion strength unchanged)**
- The e-toggle RED test originally chained disable→enable in one run and raced the async DataLoaded refresh (the second press read the pre-refresh snapshot); split into two deterministic tests (disable / re-enable). The span assertions assert the resolved `f"bold {app.current_theme.accent}"` (matching Deviation 3's mechanism), not a literal `$accent` string.

## Issues Encountered

None open. No auth gates, no checkpoints (fully autonomous plan).

**Flagged planner assumption (surfaced, not silently resolved — the plan's own flag):** CUST-06's 导出分享 gloss assumes the receiving operator consumes an exported custom-registry file through THIS console's import path (same schema, same gauntlet). Cross-machine/cross-version consumption of the share unit is NOT verified this phase and stays open for UAT; no code path is blocked on it.

## User Setup Required

None. Every test runs over monkeypatched tmp roots or fakes; the user-owned registries are written only under test-pinned temporary directories; official registry files are byte-pinned untouched across every write path.

## Known Stubs

None.

## Next Phase Readiness

- **Phase 9 is complete** (6/6 plans): all five ROADMAP success criteria evidenced — criteria 1/2/4/5 by this plan's full-loop stories (plus the 09-05 never-land/rollback pins for criterion 4), criterion 3 by the 09-01 validator + 09-04 report now bound at the composition root.
- Phase 10 (data manager, menu slot 3) consumes: the `custom_status`/management-read composition if its views need custom-dataset visibility; the top-menu placeholder toast flips to the delivered phase per D-13; the NAV_SLOTS 3/4/5 entries carry the delivering phases.
- The `custom_service` seam pattern (optional injection, real defaults) is the reference for the Phase 11 run-config screen's service wiring.

## TDD Gate Compliance

Both tdd-marked tasks followed RED → GREEN with persisted, gate-validated evidence (INVALID_RED guarded):

- **Task 1 RED** (`RED_EVIDENCE_OK`, target `test_w_routes_by_active_table_and_prefills_from_the_custom_row`): 6 fail / 1 pass — every behavioral test failed on the absent seams (`SelectionData` lacked `custom_status`, the screen lacked the `custom_service` kwarg); the no-menu-item pin passed on the existing NAV_SLOTS as expected (it pins, not introduces).
- **Task 2 RED** (`RED_EVIDENCE_OK`, target `test_landed_and_disabled_fixture_renders_the_full_custom_contract`): 1 fail / 10 pass — the badge assertion (`'my-custom-dna-lm' == '◇ my-custom-dna-lm'`); the zero-customs and real-backend-counts companions pin Task 1's mechanics (the 09-04 Task-3 pin precedent).
- Every GREEN commit ran the full suite lane before the feat commit; no test was weakened to pass — the Deviation-4 harness fixes kept every planned assertion.

## Self-Check: PASSED

All 6 artifact files exist on disk; all 5 task commits (f9b4d24, 9b83965, 5ee8659, 1689c65, 34f5d17) are ancestors of HEAD; commits measured 5 via `git rev-list --count 1f4bde1..HEAD` (matches `actuals.commits`); tests/tui 374 passed, `make test` 943 + node 18/0, lint + typecheck clean, official registries git-clean.
