---
phase: 08-tui-foundation-env-check-selection
plan: 06
subsystem: tui (env-check screen + composition root)
tags: [tui, env-check, pilot-tests, i18n, thread-worker, d-03, d-05, d-09, d-02, env-01, env-02, env-03, env-04, i18n-01]
requires:
  phase: []
provides: []
provides:
  - "tui/screens/env_check.py — the full env-check screen: seven-row DataTable keyed on kernel id (main() order), exclusive @work(thread=True) worker as the sole kernel execution site (D-03), per-row pending->checking->pass/fail fill via nested Messages, same-day cache-hit instant render (D-05), advisory gate verdict + routing block (D-09), ModalScreen+RichLog verbatim drill-down, refresh re-run"
  - "tui/strings.py — the complete APP_ shared block + ENV_ block verbatim from the UI-SPEC Copywriting Contract, including the Phase-11 quick-check strings and APP_MIN_SIZE_MESSAGE/APP_HELP_* chrome"
  - "tui/app.py — the full composition root: EnvCheckServiceProtocol injection seam (real EnvCheckBackend defaults), env-check opening screen, q/? app bindings, HelpModal, 80x24 min-size guard (mount+resize, push/pop, live dimension updates), SCREENS slot registry for 08-07"
  - "EnvCheckServiceProtocol — the structural service seam every tier-2 Pilot fake conforms to (the injection contract 08-07's selection screens reuse)"
  - "tui/styles.tcss — the complete stylesheet: theme variables only (zero hex), declared spacing tokens only, two weights, modal width-60 pattern, verdict/route color classes (the pattern 08-07's screens extend)"
affects:
  - tui/app.py
  - tui/strings.py
  - tui/styles.tcss
  - tui/screens/env_check.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_boot.py
actuals:
  tokens: 19988      # chars/4 over the realized code diff (79953 chars, tui/+tests/ only)
  tasks: 2
  commits: 3         # measured: git rev-list --count 1697b0c..HEAD (1 test + 2 feat)
plan_head_before: 1697b0c5991fdbf87c2962c6d9328fd664216edc
plan_head_after: 1c9d0a32ec6e6684c73849e7798bdf4d6d27873f
tech-stack:
  added: []          # consumes the 08-02 [tui] group (textual 8.2.8 + platformdirs); zero new packages
  patterns:
    - "Protocol-typed service injection: screens depend on a structural Protocol, not a concrete service — real adapter and Pilot fakes conform; the fakes' determinism comes from threading.Event gates, never timed sleeps"
    - "nested custom Message trio (CheckItemChecking/CheckItemDone/CheckRunComplete) posted from the exclusive thread worker; message handlers only mutate rows — the code-level T-08-07 gate (kernel() appears exactly once, inside the worker)"
    - "plain-Screen push/pop for the min-size guard (nothing beneath renders; modal stacks survive); ModalScreen for drill-down/help (app bindings blocked)"
    - "per-cell rich Text styles referencing theme variables ($success/$error/$text-muted) — DataTable cells are not DOM nodes; the glyph carries meaning under NO_COLOR, color is the redundant channel"
key-files:
  created:
    - tests/tui/test_pilot_env_check.py
    - .planning/tdd-evidence/08-06-task1-red.json
  modified:
    - tui/screens/env_check.py
    - tui/strings.py
    - tui/app.py
    - tui/styles.tcss
    - tests/tui/test_pilot_boot.py
key-decisions:
  - "EnvCheckServiceProtocol is the injection seam and the real EnvCheckBackend adapter lives in the screen module: the plan's files_modified list forbids new service files, and the adapter is thin delegation glue (cache pair + CheckResult rebuild + one-moment persist/display) over the already-tested 08-04 service — every semantic stays in tui/services"
  - "app.py gained the minimal constructor wiring in Task 1 (not Task 2): Task 1's own action text says 'real defaults wired in app.py' and every Pilot test injects through the app — the file list under-included it (Rule 3)"
  - "the summary column is the kernel's own first detail line with the PASS:/FAIL: prefix stripped — a mechanical derivation of the byte-stable D-02 text (the UI-SPEC mockup's summaries are hand-abbreviated sketches; the Copywriting Contract does not pin summary content)"
  - "the routing count {n} counts the dataset_dirs result's '  - ' listing lines — each missing dir is exactly one such line in the byte-locked contract, so counting the prefix reads the kernel's own list (never re-computed)"
  - "the checking state is posted BEFORE each kernel call (CheckItemChecking), making the pending->checking->done progression observable per row; the gated-fake test pins it mid-run and doubles as the T-08-07 UI-responsiveness proof (event loop processes while a kernel blocks)"
  - "enter routes through the focused DataTable's native RowSelected event (the table consumes the key — empirically verified); the screen-level enter Binding exists for the Footer hint and the unfocused path; both converge on one _open_detail, so no double-open is possible"
  - "APP_MODAL_BACK_LABEL unifies the esc-back wording (renamed from Task 1's ENV_DETAIL_BACK_LABEL once the help modal needed the same label — one Copywriting concept, one constant, APP_ prefix for shared chrome)"
  - "the xl 12-cell screen-edge token is not expressible: Textual CSS has no media queries (verified against the 8.2.8 parser) — the tokens are the allowed vocabulary, not a mandate to use every one; documented rather than approximated"
  - "the drill-down RichLog carries max-height 20: a height cap is not a spacing token (the UI-SPEC prohibition explicitly governs paddings); the bound exists so the log scrolls its own viewport instead of the box clipping content (wrap + scroll, never elide)"
  - "Static.content (not .renderable) is the textual 8.2.8 read API for Label/Static content — found by probe during RED (the older attribute does not exist in this version)"
patterns-established:
  - "the tier-2 Pilot test shape over the app seam: DnallmMarkTui(env_check_service=fake) boots the REAL app headlessly; completion awaits app.workers.wait_for_complete() + pilot.pause(); slow-kernel scenarios gate on threading.Event (deterministic, never sleeps)"
  - "modals compose Footer INSIDE the bordered box (the UI-SPEC modal mockup shape) with border_title carrying the title — the shared pattern for every later Phase 8 confirm/help surface"
  - "zero-Chinese source gates live in the test suite as permanent CI enforcement (screen module + composition root), mirroring the plan's bash verify gates"
requirements-completed: [ENV-01, ENV-02, ENV-03, ENV-04, I18N-01]
coverage:
  - id: D1
    description: "ENV-01 presentation — seven fixed rows in main() kernel order with pending->checking->pass/fail per-row fill over the exclusive thread worker; rows never render as a blank header-only table; cache-hit renders final states instantly with zero kernels"
    requirement: ENV-01
    verification:
      - kind: unit
        ref: "tests/tui/test_pilot_env_check.py::test_no_cache_fills_rows_async_and_persists_whole_list_once — final glyphs + summaries per row, kernel_calls == main() order, persist once"
        status: pass
      - kind: unit
        ref: "tests/tui/test_pilot_env_check.py::test_gated_kernel_shows_checking_progression_ui_stays_responsive — checking glyph on the in-flight row, rows 1-6 pending while kernel 0 blocks, event loop responsive (T-08-07)"
        status: pass
      - kind: unit
        ref: "code-level gate: kernel() appears exactly once in tui/screens/env_check.py, inside the @work(exclusive=True, thread=True) worker; every handler only mutates rows"
        status: pass
      - kind: unit
        ref: "tests/tui/test_pilot_boot.py — the REAL app boots on the env-check screen, 7 rows keyed on kernel ids in main() order, q quits 0"
        status: pass
    human_judgment: false
    rationale: "Row states, ordering, worker exclusivity, and responsiveness are all mechanically asserted (glyph strings, call order, pause-return liveness)."
  - id: D2
    description: "ENV-02 — the last-check line renders verbatim (上次检查: YYYY-MM-DD HH:MM, halfwidth colon) from the persisted checked_at; a same-local-day cache hit renders instantly starting zero kernels; the refresh key is the only re-run path"
    requirement: ENV-02
    verification:
      - kind: unit
        ref: "test_cache_hit_renders_final_states_and_last_check_without_worker — final states + line render, kernel_queries == 0"
        status: pass
      - kind: unit
        ref: "test_last_check_line_matches_persisted_checked_at_format_exactly — line == constant format, fullmatch the CHECKED_AT_FORMAT-derived regex"
        status: pass
      - kind: unit
        ref: "test_refresh_resets_rows_to_pending_and_reruns — rows reset to pending, kernel calls 7->14, persist 1->2"
        status: pass
      - kind: unit
        ref: "backend sync tests — same-day rebuild round-trip, yesterday/corrupt misses, persist display string == persisted value"
        status: pass
    human_judgment: false
    rationale: "Cache semantics, format exactness, and refresh exclusivity are machine-verified against constants and call counts."
  - id: D3
    description: "ENV-03 (D-09 advisory) — the verdict block renders the gate outcome: critical-fail line naming failing kernels with the Phase-11 note, missing-dataset routing line with the count and CLI audit command; all-pass renders the ready verdict"
    requirement: ENV-03
    verification:
      - kind: unit
        ref: "test_critical_fail_verdict_names_kernels_and_routes_missing_data — 'cuda, matmul' named in main() order, routing line with n=7 + the CLI command"
        status: pass
      - kind: unit
        ref: "test_all_pass_renders_ready_verdict_and_no_routing_line — exactly [✓ 环境就绪（可启动）]"
        status: pass
    human_judgment: false
    rationale: "Verdict lines are asserted as exact strings-constant formats over deterministic fake results."
  - id: D4
    description: "ENV-04 (D-09) — the quick-check pass/fail strings land in tui/strings.py now for Phase 11 consumption; no UI surface or call site built this phase"
    requirement: ENV-04
    verification:
      - kind: other
        ref: "tui/strings.py ENV_QUICK_CHECK_PASS/ENV_QUICK_CHECK_FAIL verbatim from the UI-SPEC Copywriting Contract; zero call sites (grep-verified: no tui module references them)"
        status: pass
    human_judgment: false
    rationale: "String presence and absence of call sites are greppable facts."
  - id: D5
    description: "I18N-01 — every operator-facing string on this surface lives in tui/strings.py as UPPER_SNAKE constants; the screen module and the composition root carry zero Chinese literals; kernel ids, column keys, and CLI commands stay English verbatim"
    requirement: I18N-01
    verification:
      - kind: unit
        ref: "test_screen_module_carries_zero_chinese_literals + test_app_module_carries_zero_chinese_literals (permanent CI gates mirroring the bash verify)"
        status: pass
      - kind: other
        ref: "verify gates: grep -rPn CJK on tui/screens/env_check.py and tui/app.py both exit 1"
        status: pass
    human_judgment: false
    rationale: "Single-home enforcement is a mechanical source scan."
  - id: D6
    description: "Composed-app resilience — min-size guard (below 80x24 only the message with current dims, re-checked on resize, restore on grow), NO_COLOR glyph redundancy, help modal with Chinese binding labels, styles contract (zero hex, declared spacing tokens only), Footer visible at the design grid"
    requirement: ENV-01
    verification:
      - kind: unit
        ref: "test_min_size_guard_swaps_updates_and_restores; test_no_color_scenario_keeps_distinct_glyphs; test_help_modal_lists_bindings_and_esc_closes; test_app_boots_with_footer_visible_on_env_check; test_styles_tcss_zero_hex_and_declared_spacing_tokens_only"
        status: pass
      - kind: other
        ref: "full gates: tests/tui 130 passed; make lint 0; make typecheck 0; make test-fast 690 passed; JS lane 18 passed"
        status: pass
    human_judgment: false
    rationale: "Guard behavior, glyph redundancy, help content, and the styles contract are all mechanically asserted; the gate exits are recorded."
duration: 43 min
completed: 2026-10-11T14:32:08Z
status: complete
---

# Phase 08 Plan 06: Env-Check Screen & Composition Root Summary

Built the visible env-check panel and the app composition root: a seven-row DataTable filled row-by-row over the exclusive thread worker (pending → checking → pass/fail glyphs), the same-day cache-hit instant render with the verbatim last-check line, the advisory gate verdict and missing-data routing block, the verbatim ModalScreen drill-down, the help modal, the 80x24 min-size guard, and the complete strings module — all Pilot-proven against constructor-injected deterministic fakes.

## Performance

- **Duration:** 43 min (13:48:59Z – 14:32:08Z, 2026-10-11)
- **Tasks completed:** 2 / 2 (Task 1 a full TDD RED-GREEN cycle)
- **Files changed:** 6 (1 created, 5 modified; +1573/−102 lines)
- **Commits:** 3 (measured from the persisted plan ledger)
- **Estimate calibration:** code diff ≈ 19988 tokens vs 18000 estimated (111%)

## Accomplishments

- **Task 1 — the env-check screen (TDD):** RED first — a 16-test tier-2 suite plus the complete strings constants landed against a behavior-absent skeleton (validated `RED_EVIDENCE_OK`: 12 failed on planned assertions, 0 errors). GREEN filled the shell: the exclusive `@work(exclusive=True, thread=True)` worker posts a nested Message per step (checking → result → run-complete), `on_mount` consults the injected service's same-day cache (hit = final states + last-check line, zero kernels; miss = worker), the verdict block renders `env_gate.gate_verdict` (ready / critical-fail naming failing kernels / dataset routing with count + CLI command), refresh resets all rows and re-runs, and enter opens the `ModalScreen` drill-down whose wrapping `RichLog` carries the kernel's lines byte-verbatim. The deliberately-slow gated fake (threading.Event) pins the checking-state progression mid-run AND the T-08-07 responsiveness claim (pauses keep returning while a kernel blocks). The real `EnvCheckBackend` adapter (delegation glue over the 08-04 service) is covered by five sync tests with tmp-path state files.
- **Task 2 — composition root, help, guard, styles:** `DnallmMarkTui` rebuilt as wiring-only: the injection seam (Protocol-typed), `q`/`?` app bindings, the `HelpModal` (every active binding as `[key] label` rows from strings, both BINDINGS declaration forms handled), and the min-size guard — below 80x24 a plain `MinSizeScreen` swaps in carrying ONLY the current-dimensions message (updates on further below-min resizes; pops on grow, restoring the exact stack). `styles.tcss` completed per the UI-SPEC: theme variables only (zero hex — the optional brand theme deliberately not landed), declared spacing tokens only (`1 4` modal padding, `0 2` status lines, 1-cell borders), two weights, the width-60 modal pattern, and verdict pass/fail/route color classes. Five new tests cover footer-visible boot, help modal (+q-blocked-through-modal), the guard cycle, NO_COLOR glyph redundancy, and the styles contract.
- **Proof, not inspection:** whole tests/tui 130 passed (tier-1 + tier-2, fakes only — zero real kernels, zero GPU, zero dnallm at call time); make lint + make typecheck clean; make test-fast 690 passed; JS lane 18 passed; zero-Chinese grep gates clean on both `tui/app.py` and `tui/screens/env_check.py`; the real-service wiring smoke constructs the default backend against the D-04 state path with the main()-order kernel sequence.

## Task Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 RED — failing Pilot suite + skeleton | `2ef436a` | test(08-06): add failing Pilot suite for env-check screen (RED) |
| 1 GREEN — the screen implementation | `74af5ef` | feat(08-06): implement env-check screen — async fill, cache line, verdict, drill-down |
| 2 — composition root + guard + styles | `1c9d0a3` | feat(08-06): composition root, help modal, min-size guard, styles |
| plan metadata (docs) | (this commit) | docs(08-06): complete env-check screen & composition root plan |

## Files Created/Modified

- **Created:** `tests/tui/test_pilot_env_check.py` (21 tests: 16 Pilot/screen + backend sync + source gates), `.planning/tdd-evidence/08-06-task1-red.json`
- **Modified:** `tui/screens/env_check.py` (full screen: Protocol seam, backend adapter, modal, worker, verdict), `tui/strings.py` (complete APP_/ENV_ block), `tui/app.py` (full composition root), `tui/styles.tcss` (complete stylesheet), `tests/tui/test_pilot_boot.py` (adapted to the rebuilt screen — see Deviations 1)

## Decisions Made

- **The adapter lives in the screen module:** the plan's `files_modified` list forbids new service files, so `EnvCheckBackend` (thin delegation glue over the tested 08-04 service) sits beside its consumer; the screen depends on `EnvCheckServiceProtocol`, so Pilot fakes conform structurally and the real service is the default.
- **Summary column = the kernel's own first line, prefix-stripped** — mechanical derivation of the byte-stable D-02 text (the UI-SPEC mockup's summaries are hand-abbreviated sketches; the Copywriting table does not pin summary content).
- **Routing count from the contract text:** `{n}` counts the dataset_dirs result's `  - ` listing lines — exactly the kernel's own missing-dir list, never a re-computation.
- **`CheckItemChecking` posted before each kernel call** — the three-state progression is observable per row and the gated-fake test doubles as the T-08-07 UI-responsiveness proof.
- **Enter routes through the DataTable's native `RowSelected`** (the focused table consumes the key — empirically verified); the screen-level Binding serves the Footer hint and the unfocused path; both converge on one `_open_detail`.
- **`APP_MODAL_BACK_LABEL`** unifies the esc-back wording across the drill-down and help modals (one Copywriting concept, one constant).
- **xl token skipped deliberately:** Textual CSS has no media queries (verified against 8.2.8) — the 12-cell screen-edge margin is not expressible; the tokens are the allowed vocabulary, not a mandate.
- **RichLog `max-height: 20`:** height caps are not spacing tokens (the UI-SPEC prohibition explicitly governs paddings); the bound keeps the log scrolling instead of clipping (wrap + scroll, never elide).
- **textual 8.2.8 API facts pinned by probe:** `Static.content` (no `.renderable`), `from textual import work` (no `textual.work` module — research A1's path was wrong), modal dismissal via `Binding("escape", "dismiss", ...)`, plain-Screen push/pop hides everything beneath.

## Deviations from Plan

**1. [Rule 3 - necessity] `tests/tui/test_pilot_boot.py` updated (not in the plan's file list)**
- **Found during:** Task 1 (the screen rebuild)
- **Issue:** The 08-03 boot test pinned the shell this plan explicitly replaces — 2-column rows and zero service calls. The new 3-column table and the on_mount service consult make the old assertions fail, and booting with no injected service would run REAL kernels in CI (D-03 violation).
- **Fix:** Updated to the rebuilt contract: an inline same-day cache-hit fake injected through the app seam (kernels()/persist() raise if called), 3-column row expectations, final-state + last-check assertions; the boot intent (real app class, opening screen, main() order, keyed rows, q quits 0) preserved.
- **Files modified:** tests/tui/test_pilot_boot.py
- **Verification:** green in every gate run (part of the 130-test tui suite).
- **Commit:** `2ef436a`

**2. [Rule 3 - file-list conflict] `tui/app.py` minimal wiring landed in Task 1**
- **Found during:** Task 1 test design
- **Issue:** Task 1's `<files>` list omits app.py, but its `<action>` requires "real defaults wired in app.py" and every Pilot test injects the fake through `DnallmMarkTui(env_check_service=...)` — without the Task-1 wiring the tests cannot run the real app class.
- **Fix:** Task 1 added only the constructor seam + `get_default_screen` pass-through (13 lines); Task 2 rebuilt the rest per its own file list.
- **Files modified:** tui/app.py
- **Commits:** `2ef436a`, `1c9d0a3`

**3. [Rule 1 - test-side API] RED-phase corrections to the test harness**
- **Found during:** Task 1 RED run
- **Issue:** Two harness bugs against textual 8.2.8: `Static.renderable` does not exist (the read API is `Static.content`), and the zero-Chinese gate caught a Chinese comment in my own modal code quoting the label.
- **Fix:** Helpers read `.content`; the modal comment references the constant instead of quoting the copy. Also fixed the `ty` union-narrowing findings (query typing, guard local, BINDINGS tuple form) before the gates.
- **Files modified:** tests/tui/test_pilot_env_check.py, tests/tui/test_pilot_boot.py, tui/app.py, tui/screens/env_check.py
- **Verification:** all gates green after each fix.
- **Commits:** `2ef436a`, `74af5ef`, `1c9d0a3`

**Total deviations:** 3 auto-fixed (2 Rule 3, 1 Rule 1).
**Impact:** None on the plan's contracts — every D-number truth is implemented as specified; the two file-list deviations are the minimal changes the plan's own action text required.

## TDD Gate Compliance

Task 1 carried `tdd="true"` and completed a full RED-GREEN cycle:

| Task | RED commit | RED evidence | GREEN commit |
|------|-----------|--------------|--------------|
| 1 | `2ef436a` | `RED_EVIDENCE_OK` (16 tests, 12 failed, 0 errors; target `test_cache_hit_renders_final_states_and_last_check_without_worker` failed inside its planned assertion — rows render pending because the skeleton never consults the cache) | `74af5ef` |

RED method: a full-layout skeleton with behavior absent (cache/worker/verdict/drill-down/refresh all missing; backend methods return None/empty), so every target test executed and failed on its planned assertion — no collection, import, or fixture faults (JUnit `errors=0`). The four trivially-green tests against the skeleton are noted in the evidence record's semantic assessment (two None-expected cache-miss cases, the landed-strings glyph test, the source gate). Gate commits verified: 1 `test(08-06):` + 2 `feat(08-06):` present in git log. Task 2 was not TDD-flagged; its five new tests landed with the implementation in `1c9d0a3`.

## Issues Encountered

- A concurrent GSD verifier process re-ran phase-07 verification during this execution (07-VERIFICATION.md modified in the worktree at 13:56Z) — not this plan's change; left unstaged for the workflow's own handling.
- No auth gates, no package installs, no pre-commit hook cycles.

## User Setup Required

None.

## Known Stubs

None — no placeholder patterns in the delivered files; the designed empty-`lines` torch-unavailable placeholders and the None cache-miss sentinel are documented 08-01/08-04 behavior with tests, not stubs.

## Next Phase Readiness

- **08-07 (selection/matrix screens):** the `SCREENS` registry is the declared slot mechanism (comment marks the 08-07 entries); `EnvCheckServiceProtocol` is the reusable injection pattern; the `s` binding (env → selection) is deliberately absent until the target screen exists (per-screen bindings, UI-SPEC keyboard map); styles.tcss carries the table/modal/verdict patterns to extend; the tier-2 Pilot shape (app-seam injection, `wait_for_complete`, Event-gated fakes) is established in `tests/tui/test_pilot_env_check.py`.
- **Phase 11 (launch):** `ENV_QUICK_CHECK_PASS/FAIL` are staged in strings; `gate_verdict` renders exactly what the launch screen will block on (D-09 — the persisted state file is never the gate authority; quick-check computes fresh).
- **Phase 12 (TEST-01):** snapshot goldens were deliberately NOT introduced (plan prohibition) — the Pilot assertions here are behavioral only, as specified.

## Self-Check: PASSED

- `tests/tui/test_pilot_env_check.py` — FOUND (created, committed in `2ef436a`/`74af5ef`/`1c9d0a3`)
- All five plan artifacts (tui/app.py, tui/strings.py, tui/styles.tcss, tui/screens/env_check.py, tests/tui/test_pilot_env_check.py) — FOUND, committed
- Task commits verified as ancestors of HEAD: `2ef436a`, `74af5ef`, `1c9d0a3`
- Commit count measured from the persisted ledger: 3 production commits (`git rev-list --count 1697b0c..HEAD`)
- TDD gate: 1 `test(08-06):` + 2 `feat(08-06):` commits present (git log grep validated)
- Gates at plan close: tests/tui 130 passed; make lint 0; make typecheck 0; make test-fast 690 passed; JS lane 18 passed; Chinese grep gates clean (app.py + env screen); real-service wiring smoke green
