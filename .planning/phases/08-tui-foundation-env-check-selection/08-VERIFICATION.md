---
phase: 08-tui-foundation-env-check-selection
verified: 2026-10-12T09:12:00Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - .planning/phases/08-tui-foundation-env-check-selection/08-01-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-01-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-02-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-02-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-03-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-03-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-04-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-04-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-05-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-05-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-06-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-06-SUMMARY.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-07-PLAN.md
  - .planning/phases/08-tui-foundation-env-check-selection/08-07-SUMMARY.md
  - Makefile
  - pipeline/env_smoke.py
  - pyproject.toml
  - schemas/run_template.json
  - tests/test_env_smoke_bytes.py
  - tests/tui/conftest.py
  - tests/tui/test_import_lock.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_env_check.py
  - tests/tui/test_services_env_gate.py
  - tests/tui/test_services_quick_check.py
  - tests/tui/test_services_registries.py
  - tests/tui/test_services_selection.py
  - tests/tui/test_services_settings.py
  - tests/tui/test_services_templates.py
  - tui/__init__.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/__init__.py
  - tui/screens/env_check.py
  - tui/screens/matrix.py
  - tui/screens/selection.py
  - tui/services/__init__.py
  - tui/services/env_check.py
  - tui/services/env_gate.py
  - tui/services/quick_check.py
  - tui/services/registries.py
  - tui/services/selection.py
  - tui/services/settings.py
  - tui/services/templates.py
  - tui/strings.py
  - tui/styles.tcss
  - uv.lock
covered_digest: "v3:sha256:ef777da553c4bfb13804fb01a5091ae267f1a64b39321c2b4068304d4029ac94"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 5/5
  gaps_closed:
    - "Stale fingerprint (#4682): Phase 9 commits (b69d07b and 69 prior) touched 9 covered files — fresh digest regenerated at HEAD; the five Phase 8 success criteria re-confirmed at HEAD"
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "Critical FAILs block entry into the launch flow (ENV-03) and the quick-check re-validates before each task launch (ENV-04) — the launch-flow wiring itself"
    addressed_in: "Phase 11"
    evidence: "Phase 11 Success Criterion 2: 'The launch gate is terraform-style: env_smoke preflight blocks on FAIL with the reason, preview precedes explicit confirmation...' — the D-09 recorded decision (08-CONTEXT) lands the pure judgment (env_gate.gate_verdict, unchanged since initial verification) and quick-check service NOW and defers the blocking hook to the Phase 11 launch screen"
---

# Phase 8: TUI Foundation (Env Check & Selection) Verification Report

**Phase Goal:** The console exists and is trustworthy at rest — `make tui` opens a Textual app whose startup shows a persisted full environment-check panel, and operators build model×dataset selections k9s-style with presets, templates, and presence columns — with every non-retrofittable decision (textual-free services layer, `[tui]` dependency group, Pilot test harness, tolerant artifact loader, constants-module i18n convention) landed so later phases add screens, not architecture
**Verified:** 2026-10-12T09:12:00Z
**Status:** passed
**Re-verification:** Yes — stale-fingerprint re-run (#4682) after Phase 9 landed changes in 9 covered files

## Re-Verification Scope

This report supersedes the 2026-10-12T00:42:16Z verification (itself a re-run after UAT closure 2/2). Since that report (HEAD a8dba7c), 70 commits landed — the entire Phase 9 execution (nav shell per D-13..16, wizard/about/gauntlet screens and services, WR-01..07 review fixes). Of the covered files, exactly 9 drifted:

- `tui/app.py` (+77/−) — nav-shell composition, footer migration
- `tui/screens/env_check.py` (+44/−) — nav-bar integration, WR-02 refresh-generation guard
- `tui/screens/selection.py` (+508/−) — badges, Phase 9 integration
- `tui/services/quick_check.py` (4 lines) — WR-05 docstring anglicization only (diff inspected: zero behavior change)
- `tui/strings.py` (+244) — Phase 9 strings added
- `tui/styles.tcss` (+127) — nav shell + badge styles
- `tests/tui/test_pilot_env_check.py`, `test_pilot_matrix.py`, `test_pilot_selection.py` — adapted to the nav shell

All other covered files are byte-identical to the prior verification (verified via `git diff --name-only a8dba7c..HEAD` over the covered set). Per the re-verification evidence gate (#3304), full-depth checks were applied to the drifted files; the rest are regression-confirmed. No carried-forward gaps existed (prior report: passed, empty gaps).

### Delta Analysis: Phase 9 vs the Phase 8 contracts

| Contract | Verdict | Evidence at HEAD (b69d07b) |
| -------- | ------- | -------- |
| SC1 "startup shows a persisted full environment-check panel" under the nav shell | ✓ HONORED | `tui/app.py:191-193` — `get_default_screen()` still returns `EnvCheckScreen(env_check_service=...)`; `test_pilot_boot.py::test_boots_on_env_check_screen_quits_on_q` green at HEAD; `test_pilot_env_check.py::test_app_boots_with_nav_bars_visible_on_env_check` pins that the nav shell wraps WITHOUT displacing the env-check default |
| Terminal Contract min grid 80×24 | ✓ HONORED | `tui/app.py:65-66` `MIN_WIDTH=80`/`MIN_HEIGHT=24`; `MinSizeScreen` swap + `on_resize` re-check intact (`tui/app.py:100,257-276`); both selection backstop tests green at HEAD |
| NO_COLOR legibility | ✓ HONORED | styles.tcss documents the weight/glyph redundancy channels (`tui/styles.tcss:10,22,254,321`); glyph-carries-meaning idiom present in selection/wizard/about screens |
| Digit routing to the SAME selection screen | ✓ HONORED | `tui/screens/nav.py:83` — `NavSlot(2, NAV_LABEL_SELECTION, "selection", None)`; `tui/app.py:195-210` `build_selection_screen()` constructs the same `SelectionScreen` (k9s filter /, spacebar marks, presets, presence columns — all present in the drifted file, re-checked) |
| i18n single home (constants module) | ✓ HONORED | CJK grep over `tui/screens/` (incl. new nav/wizard/about) + `tui/app.py`: 0 hits; `tui/strings.py` is the sole home (grew +244 for Phase 9 strings) |
| Services textual-free | ✓ HONORED | textual-import grep over `tui/services/` (incl. new about/custom_entries/custom_validation/gauntlet): 0 imports; import-lock test green in suite |
| `[tui]` group isolation | ✓ HONORED | `pyproject.toml:54-62` — textual>=8.2,<9 + platformdirs + jsonschema; data/gpu lanes unchanged; `make tui` recipe intact (`Makefile:30-31`) |
| Byte-frozen artifacts | ✓ UNTOUCHED | `git diff 098fc48..HEAD -- pipeline/env_smoke.py schemas/run_template.json .github/workflows/` empty |

## Goal Achievement

### Observable Truths

The five ROADMAP success criteria are the yardstick. Truths 1-5 were each re-confirmed at HEAD on the drifted files; full-depth evidence from the prior report (initial + UAT-closed re-run) remains the substrate and no covered file outside the nine drifted.

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | SC1: `make tui` opens the console; startup runs the full env check reusing env_smoke kernels; per-item ✓/✗ status with drill-down | ✓ VERIFIED | `get_default_screen()` → EnvCheckScreen at HEAD; `make tui` recipe + `python -m tui` bootstrap unchanged; `test_boots_on_env_check_screen_quits_on_q` and nav-bar boot test green in the 384-test suite; kernel imports and drill-down preserved (env_check.py delta is nav integration + WR-02 generation guard only). UAT test 1 (real GB10 kernels) passed 2026-10-12 |
| 2 | SC2: Check results persist with visible 上次检查 date; same-day restarts read the cache; manual refresh re-checks | ✓ VERIFIED | `tui/screens/env_check.py:477` — `ENV_LAST_CHECK_LINE.format(checked_at=...)`; `Binding("r", "refresh")` at :279 with `action_refresh` re-run semantics (:509-510); same-day cache service (env_check.py service) unchanged; cache tests green in suite |
| 3 | SC3: Critical FAILs visibly block launch with reason; missing-dataset routes to data management; quick-check re-validates launch-required subset | ✓ VERIFIED | `tui/services/env_gate.py` NOT in the drift set (byte-identical to prior verification); `quick_check.py` delta is docstring-only (diff inspected); advisory verdict rendering intact; launch-flow blocking hook remains the D-09 recorded Phase-11 deferral (see Deferred Items) |
| 4 | SC4: Model/dataset lists are first-class selectable surfaces with card-field columns; k9s filter; spacebar marks on stable row_keys; presets; read-only matrix auxiliary view | ✓ VERIFIED | Full-depth re-check of the +508-line drifted `selection.py`: k9s filter, mark sets, preset/template modals, presence columns, RowDetailModal all present; `build_selection_screen()` seam unchanged; digit 2 routes to this same screen (`nav.py:83`); both geometry backstop tests (`test_backstop_longest_task_key_at_80x24`, `test_backstop_longest_task_key_fits_in_full_at_160`) green at HEAD; matrix read-only gate green in suite |
| 5 | SC5: Presence columns (✓/✗ + n_audit rows); templates round-trip as validated JSON with sweep_priorities tier interop; Chinese-primary i18n through constants module; foundation invariants (services textual-free, `[tui]` isolation, Pilot green CPU-side) | ✓ VERIFIED | Presence glyphs + templates schema byte-frozen (diff empty); i18n gate 0 CJK literals across all screens + app.py at HEAD; services 0 textual imports (incl. Phase 9 additions); pyproject `[tui]` group intact; full tui suite 384 passed CPU-side |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | ENV-03/ENV-04 launch-flow wiring: the env-gate verdict blocking entry into the launch flow, and the quick-check invoked before each task launch | Phase 11 | Phase 11 SC2 (terraform-style gate). D-09 (08-CONTEXT) records the boundary: judgment landed in Phase 8 (`gate_verdict` + `quick_check` services, both verified at HEAD — the latter unchanged since the initial verification), hook is Phase 11 additive wiring. Carried forward unchanged from the prior report |

### Required Artifacts

All artifacts VERIFIED. The 9 drifted files were re-checked at full depth at HEAD; the remaining covered files are byte-identical to the prior passed verification (git-confirmed) and inherit its full-depth evidence.

| Artifact | Expected | Status | Details |
| -------- | --------- | ------ | ------- |
| `tui/app.py` | Composition root: default env-check screen, min-size guard, screen seams | ✓ VERIFIED | Drifted, full re-check: MIN 80×24 + MinSizeScreen + on_resize guard intact; get_default_screen → EnvCheckScreen; build_selection_screen seam intact; nav-shell composition additive |
| `tui/screens/env_check.py` | Full env panel: worker, cache line, verdict, drill-down | ✓ VERIFIED | Drifted, full re-check: 上次检查 line + r refresh + drill-down intact; WR-02 refresh-generation guard is additive correctness (stale-refresh race) |
| `tui/screens/selection.py` | k9s selection surface: tables, filter, marks, preset/template modals, presence | ✓ VERIFIED | Drifted (+508, Phase 9 badges/integration), full re-check: all Phase 8 semantics present; key-width constants and h-scroll geometry preserved; backstop tests green |
| `tui/services/quick_check.py` | Launch-required subset, injectable, never persisted | ✓ VERIFIED | 4-line docstring-only delta (WR-05) — behavior identical |
| `tui/strings.py` | Constants-module i18n single home | ✓ VERIFIED | Grew for Phase 9; still the sole CJK home (grep gate 0 in screens/app) |
| `tui/styles.tcss` | Design tokens, NO_COLOR-legible channels | ✓ VERIFIED | +127 nav/badge styles; NO_COLOR redundancy documentation intact |
| `tests/tui/test_pilot_{env_check,matrix,selection}.py` | Phase 8 Pilot suites | ✓ VERIFIED | Adapted to the nav shell; all Phase 8 test names (backstop, boot, cache) present and green within 384 passed |
| `tui/services/{env_check,env_gate,registries,selection,settings,templates}.py`, `tui/screens/matrix.py`, `pipeline/env_smoke.py`, `schemas/run_template.json`, `tests/test_env_smoke_bytes.py`, remaining spine files, `Makefile`/`pyproject.toml`/`uv.lock` | The rest of the covered set | ✓ VERIFIED | Byte-identical since the prior passed verification (git diff over covered set); evidence inherited; gates re-run green at HEAD |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `make tui` | `tui.app` | `uv run --group tui --group gpu python -m tui` → bootstrap → `DnallmMarkTui` | ✓ WIRED | Recipe unchanged; boot Pilot test green at HEAD |
| Nav shell digit 2 | `SelectionScreen` | `NavSlot(2, NAV_LABEL_SELECTION, "selection")` → app routing | ✓ WIRED | `tui/screens/nav.py:83`; nav-bar boot test green |
| `tui/screens/env_check.py` | `pipeline/env_smoke` | imported kernels returning CheckResult | ✓ WIRED | Unchanged; test-pinned, green in suite |
| Services layer | textual | (must NOT import) | ✓ WIRED (negative) | 0 imports incl. Phase 9 service additions; AST lock test green |
| `tui/strings.py` | all screens | constants import; no inline CJK | ✓ WIRED | grep gate 0 across screens + app.py |
| Remaining links (registries→loader+n_audit, schema→templates, selection→sweep_priorities+XDG, conftest→REPO_ROOT) | — | — | ✓ WIRED | All in the byte-identical set; inherited evidence + suite green |

### Data-Flow Trace (Level 4)

Unchanged from the prior verification for all byte-identical files. For the drifted files, no production data path changed hands: app.py's deltas are composition/routing (same service injection), env_check.py's delta is a generation guard on refresh (same persisted-state read path, 上次检查 from the same timestamp), selection.py's Phase 9 additions render badge/status computed from the same registries and env state, quick_check.py is docstring-only. All flows remain ✓ FLOWING; no static returns or HOLLOW props introduced.

### Behavioral Spot-Checks

All commands run at HEAD (b69d07b) during this re-verification.

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Whole tui suite (tier-1 + tier-2, headless, incl. all Phase 8 tests) | `uv run --group dev --group tui pytest tests/tui -q` | 384 passed in 151.96s | ✓ PASS |
| Golden byte suite + grep-lock contract trio | `uv run --group dev pytest tests/test_env_smoke_bytes.py tests/test_run_finetune_contracts.py -q` | 68 passed in 0.10s | ✓ PASS |
| Phase 8 key test names survive Phase 9 | `pytest tests/tui --collect-only -q \| grep -E "backstop\|boot"` | boot-on-env-check + both selection backstops + nav-bar boot present | ✓ PASS |
| Lint gate | `make lint` | All checks passed! | ✓ PASS |
| Typecheck gate | `make typecheck` | All checks passed! | ✓ PASS |
| i18n single-home gate | CJK grep over `tui/screens/` + `tui/app.py` | 0 hits | ✓ PASS |
| Services textual-free | textual-import grep over `tui/services/` | 0 imports | ✓ PASS |
| Byte-freeze invariants | `git diff 098fc48..HEAD -- pipeline/env_smoke.py schemas/run_template.json .github/workflows/` | empty | ✓ PASS |
| Covered-file drift scope | `git diff --name-only a8dba7c..HEAD -- <covered set>` | exactly the 9 declared files | ✓ CONFIRMED |

### Probe Execution

No probes declared for this phase — not applicable (unchanged).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| ENV-01 | 08-01, 08-03, 08-04, 08-06 | Startup full env check, per-item ✓/✗ + detail | ✓ SATISFIED | Truth 1 at HEAD; UAT test 1 pass |
| ENV-02 | 08-04, 08-06 | Persisted results + check date + refresh; same-day cache | ✓ SATISFIED | Truth 2 at HEAD (cache line + refresh binding re-inspected) |
| ENV-03 | 08-04, 08-06 | Critical FAIL blocks launch flow; missing data routes to data management | ✓ SATISFIED | Truth 3; env_gate.py byte-identical; blocking hook = D-09 Phase-11 deferral |
| ENV-04 | 08-04, 08-06 | Quick-check re-validation of launch-required subset | ✓ SATISFIED | Truth 3; quick_check.py docstring-only delta; invocation point = Phase-11 wiring (deferred) |
| SEL-01 | 08-07 | Browsable model/dataset lists (62/50), k9s filter + mark sets, read-only matrix | ✓ SATISFIED | Truth 4 at HEAD; digit-2 routing to the same screen confirmed |
| SEL-02 | 08-05, 08-07 | Presets: tier-1 pair, tier-2 representatives, all, saved customs | ✓ SATISFIED | Truth 4; selection.py full-depth re-check; suite green |
| SEL-03 | 08-05, 08-07 | Template import/export with validation; sweep_priorities tier interop | ✓ SATISFIED | Truth 5; schema byte-frozen; suite green |
| SEL-04 | 08-04, 08-07 | Per-row local data presence (✓/✗ + n_audit rows) | ✓ SATISFIED | Truth 5 at HEAD; presence column present, backstop tests green |
| I18N-01 | 08-02, 08-03, 08-06, 08-07 | Chinese-primary copy via constants module, technical terms English | ✓ SATISFIED | Truth 5 at HEAD; grep gate 0 including the new Phase 9 screens; UAT test 2 pass |

No orphaned requirements: REQUIREMENTS.md maps exactly ENV-01..04, SEL-01..04, I18N-01 to Phase 8.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | No debt markers, stubs, or empty implementations introduced by the delta in the 9 drifted covered files | — | — |

### Human Verification Required

None outstanding. The two prior human items (interactive GB10 session; CJK glyph legibility) passed UAT 2/2 on 2026-10-12 (08-UAT.md: status passed, maintainer validated). The Phase 9 delta wraps the same screens in the nav shell without changing their verified semantics; headless Pilot tests pin the boot-on-env-check and selection-routing behavior at HEAD.

### Gaps Summary

No gaps. This stale-fingerprint re-run (#4682) regenerated the coverage digest at HEAD b69d07b after Phase 9's commits touched 9 of the covered files. Full-depth re-checks of every drifted file confirm the five Phase 8 success criteria hold under the Phase 9 nav shell: the app still boots on the env-check screen (test-pinned), the 上次检查 cache line and refresh survive (source + tests), the env-gate and quick-check judgments are unchanged (env_gate byte-identical; quick_check docstring-only), digit 2 routes to the same k9s SelectionScreen with all filter/mark/preset/presence semantics intact, and the i18n constants-module single home holds across all screens including Phase 9's additions. Foundation invariants re-verified: services textual-free (0 imports), `[tui]` group isolation intact, byte-frozen artifacts untouched, full tui suite 384 passed, golden-byte trio 68 passed, lint and typecheck clean. The phase goal — the trustworthy console at rest with every non-retrofittable decision landed — remains achieved at HEAD; later phases add screens, not architecture.

---

_Verified: 2026-10-12T09:12:00Z_
_Verifier: Claude (gsd-verifier)_
