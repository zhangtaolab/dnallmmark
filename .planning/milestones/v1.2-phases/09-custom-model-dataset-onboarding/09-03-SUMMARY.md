---
phase: 09-custom-model-dataset-onboarding
plan: 03
subsystem: tui
tags: [tui, nav-shell, about-screen, textual, i18n]
requires:
  - 09-01 (custom_entries store read for the 自定义 counts)
  - 08-04/08-06 (registries service, env-check screen patterns, min-size guard)
  - 08-07 (selection screen BINDINGS, _binding_row, help modal)
provides:
  - "The D-13 top menu bar (six verbatim slots, digit access, ◆ triple-channel active marker, placeholder toast) — the chassis every Phase 9-12 surface mounts in"
  - "The D-15 bottom submenu bar (declaration-order keycaps with the 80-col clip policy, constant ?/q right segment) over the single BINDINGS key-map authority"
  - "The 关于 screen (D-13 slot 6) over a tolerant textual-free derivation service (tui/services/about.py)"
  - "Digit navigation 1-6 on the three base screens (plain per-screen bindings, never priority)"
  - "The Header/Footer retirement on base screens with the env s alias superseded by menu slot 2"
affects:
  - tui/app.py (SCREENS about slot, action_nav, boot-screen shim, binding_row moved to nav)
  - tui/screens/env_check.py + tui/screens/selection.py (bars + digits; Header/Footer retired; env s removed)
  - tui/strings.py (NAV_/ABOUT_ blocks; SEL_OPEN_LABEL deleted)
  - tui/styles.tcss (height-1 bar rules, about rows)
actuals:
  tokens: 24758   # chars/4 over the realized diff (99034 diff chars)
  tasks: 3
  commits: 6      # MEASURED: git rev-list --count bdcc012..HEAD
  plan_head_before: bdcc0128f4f075b861fbdf34f6d82700c921569d
  plan_head_after: 9421534
tech-stack:
  added: []        # zero new packages (constraint 2/10 — display layer over Phase 8-locked deps)
  patterns:
    - "screens-tier shared chrome module (tui/screens/nav.py) breaking the app↔screens import cycle"
    - "binding_row as the single key-map projection shared by the help modal and the bottom bar"
    - "rich-span styling resolved from app.current_theme (probe-pinned: $token styles fail on the Static render path)"
    - "boot-screen result-callback shim enabling switch_screen away from the opening screen (probe-pinned 8.2.8)"
key-files:
  created:
    - tui/screens/nav.py
    - tui/screens/about.py
    - tui/services/about.py
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_services_about.py
  modified:
    - tui/app.py
    - tui/screens/env_check.py
    - tui/screens/selection.py
    - tui/strings.py
    - tui/styles.tcss
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_matrix.py
key-decisions:
  - "Top-bar slot format is the D-13 verbatim digit+label attachment (1环境检查, 未开放 attached without parens/space) — the ONLY formulation of the fixed vocabulary that fits 80 columns with the ◆ prefix (78 cells, Pilot-asserted); the UI-SPEC mockup's padded rendering is the 120-col design grid"
  - "Digit bindings carry show=False: the top bar itself renders the digit labels, so listing digits again in the bottom bar/help modal would duplicate the menu (matches the D-15 mockups and the migration table's 'left segment = current-screen commands')"
  - "tui/screens/nav.py is a NEW screens-tier module (12th file, over the deliberate 11-file budget): bar classes cannot live in tui/app.py because the screens must import them and app.py imports the screens — a cycle; the shared module keeps the import direction clean (matrix.py precedent for screens importing screens-tier modules)"
  - "official counts read the committed registry files directly through artifact_loader (tolerant, official-only): the Phase 7 loader's merged view would count customs into the 官方 row (62/50 must stay official — the 自定义 segment counts them separately)"
  - "About deps tolerance is per-package: derive_about_data wraps EACH package probe, so one exploding package degrades to 未安装 without blanking its neighbors (the plan's aggregate-empty expectation refined to the per-package wording)"
  - "The 里程碑阶段 row is the one static milestone constant (ABOUT_MILESTONE_STAGE in strings.py): milestone metadata is not machine-derivable (Auto-Default #13 honesty cuts both ways — a derived-looking hardcoded string would be worse)"
patterns-established:
  - "NAV_SLOTS as the fixed slot vocabulary + app.action_nav routing (placeholder → toast, live → switch_screen; stack depth never grows under digit nav)"
  - "KeycapsStatic: re-clip on resize against self.size.width (the D-15 clip policy as a widget behavior, not a render-time hack)"
  - "AST-scoped compose checks where a literal grep cannot separate base screens from same-file modals (the migration table keeps modal Footer hints)"
requirements-completed: []
# NOTE: the plan frontmatter carries [CUST-01, CUST-02] because the
# maintainer's phase boundary includes the shell those wizards mount in
# (09-CONTEXT D-04) — this plan lands the SHELL, not wizard
# functionality; CUST-01/02 stay Pending until 09-04/09-05 land the
# wizards (the 09-02 precedent: complete only what the plan delivered).
coverage:
  - id: nav-shell-slots
    description: "Six verbatim slots fit 80 cols with the ◆ triple-channel active marker and dim placeholders"
    requirement: D-13 / must_haves truth 1
    verification: "Pilot test_pilot_nav_shell.test_top_bar_six_verbatim_slots_fit_80_triple_channel at 80x24 (cell count + region edge asserted)"
    human_judgment: false
    rationale-when-true: "cell-width arithmetic over the fixed vocabulary is fully mechanical"
  - id: placeholder-never-silent
    description: "Digits 3/4/5 fire the Phase 10/11/12 toast and never switch"
    requirement: must_haves truth 2
    verification: "Pilot test_placeholder_digits_fire_phase_toast_never_switch"
    human_judgment: false
    rationale-when-true: "toast text + screen-type assertions"
  - id: bottom-bar-clip-backstop
    description: "Left segment clips in declaration order with trailing … at 80 cols on selection; the ? modal stays complete; full map at 120"
    requirement: D-15 / must_haves truth 3
    verification: "Pilot test_bottom_bar_clips_at_80_help_modal_stays_complete (both sizes)"
    human_judgment: false
    rationale-when-true: "deterministic keycap arithmetic + help-row walk"
  - id: input-eats-digits
    description: "Typing 1 into the selection filter types 1, never navigates; after Input blur the digit navigates"
    requirement: Interaction #1 / must_haves truth 4
    verification: "Pilot test_focused_input_eats_digits_no_screen_switch"
    human_judgment: false
    rationale-when-true: "Pilot-proven textual 8.2.8 Input semantics"
  - id: env-s-retirement-reflection
    description: "The ? modal on env lists no s row (rows derive from BINDINGS)"
    requirement: must_haves truth 5 / checker note
    verification: "Pilot test_env_help_modal_reflects_the_s_removal + the updated env-suite help test"
    human_judgment: false
    rationale-when-true: "exact expected-row list"
  - id: guard-interplay
    description: "Below 80x24 the guard alone renders (no bars); grow restores screen + bars, zero guard-code changes"
    requirement: D-16 / must_haves truth 6
    verification: "Pilot test_bars_hidden_below_minimum_grid_guard_takes_over; existing guard tests green unmodified"
    human_judgment: false
    rationale-when-true: "screen-type + query assertions over the untouched guard"
  - id: about-screen
    description: "Five fixed rows, values wrap never elide, absent deps render 未安装 dim, only nav digits + ?/q bound, zero-arg SCREENS slot"
    requirement: must_haves truths 7-8
    verification: "Pilot test_about_screen_renders_five_rows_with_tolerant_values + test_about_values_wrap_never_elide; tier-1 test_services_about.py (20 tests)"
    human_judgment: false
    rationale-when-true: "fake-injected snapshot assertions + wrap height check"
  - id: about-honest-values
    description: "Official 62/50 official-only, 自定义 via the 09-01 store, n_audit 在场 signal, no derivation raises into compose"
    requirement: must_haves truth 8 / T-09-08
    verification: "tier-1 official-stays-official-with-overlay, custom-counts, n_audit, and never-raises tests"
    human_judgment: false
    rationale-when-true: "tmp-injected roots + monkeypatched raising probes"
duration: 44 min
completed: 2026-10-12
status: complete
---

# Phase 9 Plan 3: Navigation Shell + 关于 Screen Summary

One-liner: The ratified D-13..D-16 navigation shell landed — a six-slot top menu with digit access and never-silent placeholder toasts, a declaration-order bottom keycap bar with the 80-column clip policy, the tolerant read-only 关于 screen (slot 6), and the Header/Footer migration retiring the env `s` alias — all over the per-screen BINDINGS single key-map authority.

## Performance

- 3/3 tasks, 6 commits (3 RED + 3 GREEN, TDD), 44 min (estimate: 3 tasks/30k tokens; actuals: 24758 tokens over a 13-file diff).
- Verification: tests/tui 322 passed (36 new: 20 tier-1 + 16 tier-2), full tests/ 891 passed, `make lint` + `make typecheck` clean, priority-binding grep clean, services import-lock green (about.py joins the AST walk automatically).
- RED evidence: `.planning/tdd-evidence/09-03-task{1,2,3}-red.json`, all RED_EVIDENCE_OK.

## Accomplishments

- **tui/services/about.py** — textual-free tolerant derivations: pyproject version (tomllib), LIST-argv `git rev-parse --short HEAD` (3s timeout, omit-on-failure), importlib.metadata per-package probes (absent → None), OFFICIAL-only 62/50 counts (direct artifact_loader reads — customs never inflate the 官方 row), 自定义 counts via the 09-01 direct store read, n_audit presence via the 08-04 seam; `derive_about_data` wraps every probe so nothing ever raises into compose (T-09-08).
- **tui/screens/nav.py** — the shell chrome: `NAV_SLOTS` fixed vocabulary (verbatim D-13 nouns, placeholders → Phases 10/11/12), `binding_row` (the single key-map projection, moved from app.py — help modal and bottom bar share it), `keycaps_text` (budget clip with trailing …), `TopMenuBar` (◆+bold+accent active via CSS classes, dim placeholders, 78 cells at 80 cols), `BottomBar` (left segment re-clipped on resize; constant ?/q right pair).
- **tui/screens/about.py** — the read-only five-row screen over the Protocol seam (AboutBackend = thin delegation), exclusive thread worker for the derivation, digit bindings declared locally, absent deps render the constant dim.
- **tui/app.py** — `action_nav(slot)` (live → switch_screen with same-screen no-op; placeholder → phase toast), the zero-arg `about` SCREENS slot, the boot-screen result-callback shim, `action_open_selection` removed (superseded).
- **Migration** — env_check + selection retire Header/Footer (bars own the rows); the env `s` binding + `SEL_OPEN_LABEL` + `action_open_selection` deleted (slot 2 is *the* path); matrix/modals unchanged (matrix keeps its Header + hint line; modal Footer hints kept per the migration table); the `?` modal auto-reflects the s removal (Pilot-pinned).

## Task Commits

| Task | Commit | Type |
|------|--------|------|
| 1 RED — about service skeleton + tier-1 suite | 9089833 | test |
| 1 GREEN — About screen + tolerant service | 5cb3e36 | feat |
| 2 RED — nav shell Pilot suite | 29b2418 | test |
| 2 GREEN — nav shell bars + digit navigation | 97ec380 | feat |
| 3 RED — migration + reflection test edits | 6bb0d26 | test |
| 3 GREEN — Header/Footer migration + s retirement | 9421534 | feat |

## Files

Created: tui/screens/nav.py, tui/screens/about.py, tui/services/about.py, tests/tui/test_pilot_nav_shell.py, tests/tui/test_services_about.py.
Modified: tui/app.py, tui/screens/env_check.py, tui/screens/selection.py, tui/strings.py (NAV_/ABOUT_ blocks; SEL_OPEN_LABEL deleted), tui/styles.tcss (bar + about rules), tests/tui/test_pilot_env_check.py, tests/tui/test_pilot_selection.py, tests/tui/test_pilot_matrix.py.

## Decisions

See key-decisions (top-bar 78-cell format; show=False digits; the nav.py module; official-only counts; per-package deps tolerance; the static milestone row). Notable probe-pinned textual 8.2.8 facts recorded in code comments and here:

1. `switch_screen` away from the BOOT screen raises IndexError (the boot screen is stack-appended without push bookkeeping; `_pop_result_callback` pops an empty list) — one `_push_result_callback(self.screen, None)` registration in `App.on_mount` fixes it (scope: the 8.x pin).
2. Rich `Text` spans styled with Textual `$token` strings (`"$accent"`, `"$text-muted"`) crash the Static render path (`MissingStyle` — rich's console cannot parse them; DataTable cells resolve them through textual's own pipeline) — the bars resolve `app.current_theme.accent` at mount and use rich `dim` for labels.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] tui/screens/nav.py created (12th file over the deliberate 11-file budget)**
- Found during: Task 2 implementation.
- Issue: the plan places the bar widgets in tui/app.py, but the base screens must compose them and app.py imports the screens — a circular import (screens ← app ← screens).
- Fix: a screens-tier shared chrome module (nav.py) holding the bars, NAV_SLOTS, keycaps renderer, and the binding_row helper (app.py re-imports it — the help modal and the bar share the ONE projection). Import DAG stays clean; no second key-map authority exists.
- Commit: 29b2418 / 97ec380.

**2. [Rule 1 - Bug] the Task-3 literal Header/Footer grep cannot scope to base screens**
- Found during: Task 3 verification.
- Issue: the plan's grep (`grep "yield Header()\|yield Footer(" env_check.py selection.py about.py; test $? -eq 1`) also matches the modal-internal `Footer()` hints the migration table explicitly KEEPS (env drill-down, the five selection modals) — it would fail on the correct implementation.
- Fix: an AST-scoped check proving the three base screens' compose methods yield no Header/Footer, plus the Pilot query on the live screen (test_base_screens_retire_header_and_footer) — the stated intent, mechanically enforced.
- Commit: 9421534.

**3. [Rule 3 - Blocking] boot-screen switch shim (probe-pinned textual fact)**
- Found during: Task 2 probing.
- Issue: `switch_screen`/`pop_screen` from the default boot screen raises IndexError on textual 8.2.8 (missing result-callback bookkeeping for the mounted default screen) — digit nav from env (the boot screen) needs exactly that.
- Fix: one `_push_result_callback(self.screen, None)` registration in `App.on_mount`, documented as a probe-pinned fact.
- Commit: 97ec380.

**4. [Rule 1 - Bug] $token rich-span styles crash the Static render path**
- Found during: Task 2 GREEN (MissingStyle: '$accent').
- Fix: keycap key chars resolve `app.current_theme.accent` at bar mount (the live theme's value — never a hardcoded hex); labels and the absent-dep value use rich `dim`. Zero hex in styles.tcss rules (the acceptance grep stays green).
- Commit: 97ec380 / 9421534.

**5. [Scoped test edits beyond the two named suites] test_pilot_matrix.py**
- The plan's migration scope names test_pilot_env_check + test_pilot_selection, but test_pilot_matrix carries two tests pinning the retired env `s` key (`test_env_s_binding_opens_the_selection_screen`, the cross-screen integration flow).
- Fix: both migrated to digit 2 (the successor path); the shared-mark-set assertion preserved verbatim — the same sanctioned retired-key edit class.
- Commit: 9421534.

**6. [Test refinement] about deps tolerance is per-package, not aggregate-empty**
- The planned never-raises expectation (`deps == {}`) contradicted the plan's own "per-package tolerant" wording; the implementation degrades EACH package to None under an exploding probe.
- Fix: test expectation adjusted to `{name: None for name in PROBED_PACKAGES}` — one failing package never blanks its neighbors.
- Commit: 5cb3e36.

## Issues

None open. The selection screen's 9-keycap truth counts the Phase 9 `w 接入` / `e 停用` keycaps that land with the 09-04/09-05 wizard plans — the clip policy is already Pilot-asserted today with the current 7 keycaps (the clip fires at 80 columns: budget 61 < 65).

## User Setup

None. Optional manual smoke: `make tui` — bars render on 环境检查/选择/关于; digits 1/2/6 switch; 3/4/5 toast 该功能区于 Phase {10/11/12} 提供; below 80x24 the guard message alone.

## Next Phase Readiness

- 09-04/09-05 (the wizards) build against the FINAL chrome: modals push over the base screens with digit nav suppressed by ModalScreen semantics, the wizard Footer hints follow the kept modal-hint row, and the `w`/`e` bindings will append to selection's BINDINGS ahead of the auxiliary actions (the clip policy drops least-primary first — already asserted).
- The 09-06 selection custom-entry presentation consumes the same strings home (NAV_/ABOUT_ blocks landed; WIZ_/GAUNTLET_ already resident from 09-01).
- Placeholder slots 3/4/5 carry their delivering phases (10/11/12) in NAV_SLOTS — the Phase 10-12 plans replace the toast routing with real screens by flipping one NavSlot.

## TDD Gate Compliance

All three tasks RED→GREEN with validated evidence (`RED_EVIDENCE_OK` ×3, records under `.planning/tdd-evidence/09-03-task{1,2,3}-red.json`); every RED commit carries the failing tests + skeleton, every GREEN commit the passing implementation. No violations.

## Self-Check: PASSED

All 5 created files exist on disk; all 6 task commits (9089833, 5cb3e36, 29b2418, 97ec380, 6bb0d26, 9421534) are ancestors of HEAD; commits measured 6 via `git rev-list --count bdcc012..HEAD` (matches the `commits:` actual).
