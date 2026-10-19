---
phase: 11-run-config-launch-gates-single-gpu-monitoring
plan: "06"
subsystem: ui
tags: [run-config-screen, slot-4, pickers, params-pane, launch-gate, e2x-phrase, exit-modal, radioset, pilot, phase-11]

requires:
  - phase: 11-02
    provides: RunSpec/PreviewResult/DirPlan + preview/parse_params/resolve_dirs/persist/phrase_matches/compose_argv (consumed through the injected Protocol)
  - phase: 11-03
    provides: env_preflight/gate_confirm_data/launch_spec + LaunchOutcome/GateRefusal/GateSummary/EnvPreflight/live_sweeps/kill/detach (the three composable gate calls + the exit triple)
  - phase: 11-05
    provides: the 99 frozen CFG_/LNC_/MON_ constants (consumed by name; zero new constants — the tripwire stays green)
  - phase: 09-03
    provides: the nav shell (TopMenuBar/BottomBar/binding_row) + the digit-binding Pattern 2
  - phase: 10-04
    provides: the build_data_manager_screen factory rationale + the screen-frame/worker discipline
provides:
  - tui/screens/run_config.py — the slot-4 RunConfigScreen: own SelectionList pickers (marks live IN the spec, XDG round-trip through the exclusive preview worker), the CFG-01 params pane (choice rows + RadioSet modals + derived hint lines), the D-14 dirs advisories, the run-id-tagged same-source preview line, the [p] modal (verbatim argv + numbered problems), the full launch-gate pipeline as modal states (problems block, env block with verbatim reasons, non-E2' confirm, the E2' typed-phrase live-match modal, launch toasts), RunConfigServiceProtocol/LauncherServiceProtocol + the real Backends
  - the enter-key pin (UI-checker fix 2) — PickerList shadows the inherited OptionList enter with the gate action; every Input consumes its own Enter (Pilot-asserted)
  - app.py — the run_config/launcher constructor seams, the app-owned shared launcher, build_run_config_screen, the action_nav run_config branch, the async action_quit override + ExitModal (D-06 triple, default detach)
  - nav.py slot-4 promotion (NavSlot(4, ..., "run_config", None); NAV_PLACEHOLDER_SUFFIX loses its slot-4 consumer)
  - tests/tui/test_pilot_run_config.py — 32 Pilot tests over constructor-injected fakes (both grids, the gate's five paths, the exit triple, the choice flows, the CJK lock)
affects: [11-07 monitor screen (slot 5 promotion; the auto-nav half of D-13 lands there over the app-owned launcher; ExitModal predicate extends to attached running sweeps; the done/total fields thread the live counts), CFG-01..03/LNC-01..03]

actuals:
  tokens: 36282   # chars/4 over the realized diff (145130 chars, 7 files)
  tasks: 3
  commits: 5      # measured: git rev-list --count cce1b4a..HEAD
plan_head_before: cce1b4acd3111f3ff6deccfaee3b510081b19331
plan_head_after: 68c7810

tech-stack:
  added: []   # textual built-ins only (SelectionList/RadioSet/RadioButton/Checkbox/Input/RichLog); zero packages installed
  patterns:
    - "action-level widget chokepoints: private _on_* message handlers are MRO-dispatched on 8.2.8 (override+super double-fires) and unprefixed widget-binding actions do NOT resolve on the screen (they fall through to the screen's same-key binding) — both probe-pinned, both worked around at the action layer"
    - "native disabled= SelectionList rows are cursor-UNREACHABLE (OptionList navigation skips them) — disabled customs stay reachable rows and the toggle warns at the action_select chokepoint (keyboard AND mouse funnel through it)"
    - "marks live IN the frozen RunSpec (spec.models/spec.tasks) — no parallel mark sets; the exclusive preview worker does save+preview+advisories+probe-intersection in one run-id-tagged message (all XDG/registry I/O off the event loop)"

key-files:
  created:
    - tui/screens/run_config.py
    - tests/tui/test_pilot_run_config.py
  modified:
    - tui/app.py
    - tui/screens/nav.py
    - tui/styles.tcss
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_pilot_selection_custom.py

key-decisions:
  - "The enter-key pin wins the plan's internal conflict: Task 1's behavior bullet 'enter on a row opens the full-key detail' contradicts the must-have pin + Task 2 + the UI-SPEC keyboard map + UI-checker fix 2 (4 sources vs 1) — enter on the picker opens the gate; the full-key surface is the [p] modal's verbatim argv (every model/task key, full length) per the shows-the-argv house precedent"
  - "Disabled customs render as CURSOR-REACHABLE rows (native disabled rows are skipped by OptionList navigation — the warn interaction would be unreachable); the picker's action_select override warns at the chokepoint both interaction paths share"
  - "ExitModal formats done/total with CFG_VALUE_ABSENT (the launcher carries no progress; the monitor's live counts land in 11-07) — honest degradation, never a fabricated number"
  - "The RadioSet choice modal applies on the first press and closes (the PresetModal family semantics — 'the first toggle applies'); [p]'s keycap label renders CFG_PREVIEW_MODAL_TITLE (4 CJK chars, within the keycap budget — no standalone preview label constant exists in the frozen 99)"
  - "The dataset-root D-19 hint line is NOT rendered: no landed constant carries registry-side-resolution copy and the 99-constant tripwire freezes additions — recorded as a deferred copy item rather than breaking the inventory lock"

patterns-established:
  - "widget->screen action delegation: subclass bindings shadow inherited same-key bindings, and the action method delegates explicitly (self.screen.action_x via a getattr guard) — the 8.2.8 action boundary"
  - "gate-as-modal-states: every step recomputes fresh in its OWN worker group (cfg-gate-enum/env/confirm/launch), run-id-tagged, with below_minimum_grid checks on every async push (WR-06) and a pre-modal-only re-entrancy guard"

requirements-completed: [CFG-01, CFG-02, CFG-03, LNC-01, LNC-02, LNC-03]

coverage:
  - id: D1
    description: "Screen shell + pickers + params pane + dirs + preview worker + slot-4 promotion (Task 1)"
    requirement: CFG-01
    verification:
      - kind: integration
        ref: "tests/tui/test_pilot_run_config.py — 12 lane-1 tests: both-grid column compose (120x40/80x24), status counts, m flip, / filter + esc clear, space mark + XDG round-trip (fake reload), disabled-custom warn/never-mark, params defaults + 80-col label shortening, preview line update on mark, empty-selection problem copy, probe-hint hidden default, zero-Chinese lock"
        status: pass
      - kind: integration
        ref: "tests/tui/test_pilot_nav_shell.py — slot 4 renders bare (no suffix/class), digit 4 switches to RunConfigScreen with zero placeholder artifacts; tests/tui/test_pilot_selection_custom.py nav tuple extended (Rule 3)"
        status: pass
  - id: D2
    description: "The [p] modal + the launch-gate pipeline + launch toasts (Task 2)"
    requirement: LNC-03
    verification:
      - kind: integration
        ref: "lane-2 tests: [p] argv verbatim + numbered problems; happy path (confirm -> launch with spec, phrase None, LNC_LAUNCH_TOAST); problems-blocked (env never called, launch never called); env-block (ENV_QUICK_CHECK_FAIL header, reasons VERBATIM, [1] hint); E2' flow (mismatch enter no-op, live match flip, launch WITH phrase); 3-consecutive-mismatches; spawn-failure toast; 80x24 E2' backstop with a 46-char root; blocking-env responsiveness (m flips while the kernel blocks, T-11-06-04); min-grid push guard round-trip (T-11-06-06)"
        status: pass
  - id: D3
    description: "ExitModal + q intercept + choice modals + full gates (Task 3)"
    requirement: LNC-02
    verification:
      - kind: integration
        ref: "lane-3 tests: q-no-live quits directly (app._exit, no ExitModal); q-live pushes ExitModal (title + message with root name); enter detaches (recorded, no kill) + exits; k kills (root recorded, no detach) + exits; esc returns (nothing recorded); PEFT/variant RadioSet flows (row re-renders, spec persisted, alias/probe hints); subset toggle copy pair + persistence"
        status: pass
      - kind: other
        ref: "make test 1443 passed (11-03 baseline 1411 + 32) + JS lane 18/18; make lint All checks passed; make typecheck All checks passed"
        status: pass
  - id: D4
    description: "Threat mitigations T-11-06-01..07 + SC"
    requirement: LNC-03
    verification:
      - kind: integration
        ref: "T-01 (E2' live-enter reads phrase_matches per keystroke, mismatch no-op + 3-mismatch edge); T-02 (the gate's enumeration/env/confirm all recomputed fresh in workers — the preview line is never consulted); T-03 (run-id-tagged messages + handler drops, _settle-proven across the worker chains); T-04 (blocking-env responsiveness Pilot); T-05 (ConfirmModal/E2' gates precede every launch; problems/env blocks assert launch_calls == []); T-06 (below_minimum_grid on every async push + the resize round-trip test); T-07 (esc cancels q; k is the only kill path); SC vacuous — zero installs"
        status: pass

duration: 49min
completed: 2026-10-13
status: complete
---

# Phase 11 Plan 06: Run-Config Screen Summary

**The slot-4 运行配置 screen end-to-end over the frozen 11-02/11-03 services: own pickers whose marks live in the XDG-persisted spec, the full params pane with RadioSet choices and derived hints, D-14 dirs with advisories, the live same-source preview line, the [p] verbatim-argv modal, the terraform-style 启动门 as modal states (problems block -> env block -> confirm / E2' typed-phrase live-match -> launch toasts), and the app-level q-intercept ExitModal — proven by a 32-test Pilot suite, with slot 4 promoted in the nav shell**

## Performance

- **Duration:** 49 min (04:13:28Z - 05:02:13Z)
- **Tasks:** 3 (TDD lane 1 strictly RED->GREEN; lanes 2-3 pinned already-built behavior — see Deviations)
- **Files modified:** 7 (2 created, 5 edited)

## What Was Built

### Task 1 — the shell + promotion (commits a860554 RED, 8436858 GREEN)

- `RunConfigScreen` (NAV_SLOT 4): TopMenuBar -> title bar (CFG_SCREEN_TITLE + the CFG_STATUS_LINE counts right-aligned) -> the two-column split (#cfg-columns, border-top/bottom rules; the picker column 47% — ~56 cells at 120, ~38 at 80, re-derived on resize) -> the 1-row preview line -> BottomBar with the wireframe keycap order ([space]标记 [m]数据集 [/]过滤 [p]预览 [enter]启动门).
- The pickers: `PickerList(SelectionList)` — m flips the kind + title; `/` focuses the filter Input (the 08-05 grammar via the backend's parse/apply delegation, right-aligned (n/total) count, esc clears + refocuses); space marks — the marks live IN the RunSpec (D-01: slot-2 state never read; XDG round-trip through the preview worker's save_state). Model rows carry the ◇ badge + the （已停用） suffix for disabled customs with in-item truncation.
- The params pane: seeds/曲线档位/epochs/EBS Inputs, PEFT/变体 ChoiceRows (value + ▾), the 公平子集 Checkbox + value copy pair + path Input, the ── 目录 ── section, the three dir Inputs with WIZ_PATH_EXISTS/WIZ_PATH_MISSING_ADVISORY advisories and the CFG_CACHE_DEFAULT placeholder; derived dim hints (PEFT alias, variant alias, the head note, the probe ⚠ over the service-extracted frozen intersection); 80-col degradations (eff_batch_size + 目录 short labels, the narrow label column) below 100 cols.
- The preview worker (group cfg-preview): save + preview + dir states + probe intersection in one run-id-tagged message; the line renders CFG_PREVIEW_LINE[_CURVE] or the inline-truncated problems header.
- nav.py slot-4 promotion; app.py constructor seams (run_config_service/launcher_service; the launcher is the app-owned shared instance), build_run_config_screen (the shared-instance rationale comment), the action_nav branch.
- nav-shell suite edits (bare slot-4 text, placeholder loop narrowed to slot 5, digit-4 switch assertion, shell fakes).

### Task 2 — the [p] modal + the gate pipeline (commit 5194aaa)

- `PreviewModal` (border 干跑预览): the dimension summary, CFG_PREVIEW_NOTE, the composed LIST argv VERBATIM, the numbered problems.
- The gate as modal states, each step in its OWN worker group, every push below_minimum_grid-guarded: [enter] -> fresh enumeration (problems => ProblemsModal, nothing else opens) -> env preflight (FAIL => EnvBlockModal: the ENV_QUICK_CHECK_FAIL header, reasons VERBATIM in a bounded RichLog, the [1] hint row) -> gate_confirm_data => the ConfirmModal (LNC_GATE_SUMMARY + LNC_GATE_CONFIRM) or the `E2PhraseModal` (⚠ block, the type prompt with the dirname, a live indicator flipping LNC_E2_MISMATCH -> LNC_E2_MATCH_OK per keystroke through the SERVICE phrase_matches verdict, enter live only on exact match) -> the launch worker -> LNC_LAUNCH_TOAST / LNC_LAUNCH_FAILED_TOAST; a stage-"phrase" GateRefusal re-opens the modal (asserted path).
- The enter-key pin: PickerList shadows the inherited enter with the gate action; every Input consumes its own Enter — Pilot-asserted both ways.

### Task 3 — ExitModal + choices + full gates (commits 5158d23, 68c7810)

- `ExitModal` (app.py, ConfirmModal family): enter=detach-then-quit (default), k=kill_sweep-then-quit, esc=return; `action_quit` (async — the App base LSP) pushes it iff live_sweeps() non-empty and the grid is above minimum, else exits directly.
- The RadioSet choice modals: first press applies + closes; the row re-renders, the spec persists, the hints refresh (the probe hint names the frozen intersection).
- Full gates: make test **1443 passed** + JS 18/18; make lint clean; make typecheck clean (after the async-override/getattr-guard fixes).

## Verification Evidence

- `uv run --group dev --group tui pytest tests/tui/test_pilot_run_config.py -q` -> **32 passed**.
- `uv run --group dev --group tui pytest tests/tui/test_pilot_nav_shell.py -q` -> **15 passed** (slot-4 promotion assertions).
- `uv run --group dev --group tui pytest tests/tui -q` -> green (833 tests; one pre-existing nav assertion in test_pilot_selection_custom extended — Rule 3).
- `make test` -> **1443 passed** + node:test 18/18. `make lint` -> All checks passed. `make typecheck` -> All checks passed (transcript).
- TDD: lane 1 landed RED first (collection ImportError on the absent module — the 11-02 precedent), then GREEN. Lanes 2-3: see Deviations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Textual 8.2.8 semantics] Three widget-layer probe findings**
- **Found during:** Tasks 1-3 GREEN runs.
- **Issue:** (a) native `disabled=True` SelectionList rows are SKIPPED by OptionList cursor navigation — the disabled-custom warn interaction was unreachable; (b) private `_on_*` message handlers are MRO-dispatched (an override + `super()` call double-fires — the mark toggled twice per space); (c) unprefixed widget-binding actions do NOT resolve on the screen (the ChoiceRow's enter fell through to the screen's gate binding).
- **Fix:** (a) disabled customs stay reachable rows; `PickerList.action_select` warns at the chokepoint both keyboard and mouse share (OptionList._on_click routes through action_select); (b)+(c) the PickerList/ChoiceRow binding actions delegate explicitly to the screen's action (getattr-guarded for ty). All three probe-pinned in code comments.
- **Files modified:** tui/screens/run_config.py
- **Commits:** 8436858, 5158d23, 68c7810

**2. [Rule 3 - Promotion consequence] The nav-target vocabulary test**
- **Found during:** Task 1's tests/tui gate.
- **Issue:** tests/tui/test_pilot_selection_custom.py::test_the_menu_carries_no_wizard_item pins the allowed NAV_SLOTS targets — the slot-4 promotion added "run_config".
- **Fix:** the tuple extends with "run_config" (+ comment), exactly as the 10-04 slot-3 precedent inside that same test.
- **Files modified:** tests/tui/test_pilot_selection_custom.py
- **Commit:** 8436858

**3. [Rule 1 - Lint-caught] The head-variant hint rendered no copy**
- **Found during:** Task 2's scoped ruff run (F401 on CFG_VARIANT_HEAD_NOTE).
- **Issue:** `_render_hints` toggled the head hint's display without ever writing its text.
- **Fix:** the hint renders CFG_VARIANT_HEAD_NOTE under variant=head; pinned by the existing hint tests.
- **Files modified:** tui/screens/run_config.py
- **Commit:** 5194aaa

### Implementation Notes (within the plan's own discretion)

- **TDD lane shape:** the screen module landed as ONE write in Task 1's GREEN (the plan's Task 1 files list names the same module Tasks 2-3 edit), so lanes 2-3's RED phases were vacuous — the tests pin already-built behavior; each lane's first run surfaced only test-side defects. Documented here rather than reverting modals to manufacture a RED.
- **Picker enter vs row detail:** the plan's Task-1 bullet "enter on a row opens the full-key detail" conflicts with the enter-key pin (must_haves + Task 2 + the UI-SPEC keyboard map + UI-checker fix 2). The pin wins; full keys remain inspectable in the [p] modal's verbatim argv.
- **The dataset-root D-19 hint line:** no landed constant carries the registry-side-resolution copy and the 99-constant bidirectional tripwire (11-05) freezes additions — the row renders like the other dirs (Input + advisory) with no dedicated hint; recorded for the maintainer.
- **ExitModal done/total:** rendered as CFG_VALUE_ABSENT markers (the launcher exposes no progress; fabricating numbers violates the honesty rule) — 11-07 threads the monitor's live counts.
- **[p] keycap label:** CFG_PREVIEW_MODAL_TITLE (干跑预览) — no standalone 预览 constant exists; 4 CJK chars fit the keycap budget.

## Threat Flags

None — every register entry landed as planned: T-11-06-01 (the E2' widget holds no matching logic; the service verdict drives the live indicator + the enter gate), T-11-06-02 (every gate step recomputes fresh through service workers — the preview line's cache is never consulted), T-11-06-03 (run-id-tagged messages + handler drops across preview/load/gate chains), T-11-06-04 (the blocking-env responsiveness Pilot proof), T-11-06-05 (ConfirmModal/E2' gates precede every launch; problems/env-blocked paths assert zero launch calls), T-11-06-06 (below_minimum_grid checks on every async push + the resize round-trip test), T-11-06-07 (the ExitModal intercept; k is the only kill path), SC vacuous (zero installs).

## Known Stubs

None — no placeholder values, no unwired data paths; every surface is behavior-backed by the Pilot suite.

## What 11-07 Can Now Assume

The app owns ONE shared launcher instance (`app._launcher` — the fake-injectable seam; `build_run_config_screen` passes it in), so the monitor's [t] tail reads `tee_path_for(root)`, its scans take `live_sweeps()` as the live_roots source, and the ExitModal predicate extends by widening `action_quit`'s check to attached running sweeps (the done/total fields in `LNC_EXIT_MESSAGE` thread the monitor's live counts). D-13's auto-nav half is one line in `on_run_config_screen_launch_finished` (replace the comment with the slot-5 switch over the monitor screen's factory). The from-failures re-run is `launch_from_failures(...)` behind its own confirm; slot 5's promotion edits the same three nav/app sites slot 4 just did (NAV_SLOTS row, action_nav branch, factory) plus the selection-custom nav-tuple test.

## Self-Check: PASSED

- tui/screens/run_config.py, tests/tui/test_pilot_run_config.py — FOUND (created)
- a860554, 8436858, 5194aaa, 5158d23, 68c7810 — all ancestors of HEAD
- Deletion check: no tracked files deleted by any plan commit (diff --stat: 7 files, 3259 insertions, 20 deletions — the deletions are the nav-shell/selection-custom assertion lines this plan's edits replaced)
- Untracked scan: only the pre-existing .planning/.gsd-allow-shrink (present at spawn)
- Ledger: commits measured 5 (cce1b4a..68c7810), no uncommitted code changes

---
*Phase: 11-run-config-launch-gates-single-gpu-monitoring*
*Completed: 2026-10-13*
