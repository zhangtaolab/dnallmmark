---
phase: quick-261016-v0z
plan: 01
subsystem: tui
tags: [tui, exit-guard, quit-confirm, bindings, i18n, tests]
requires:
  - "11-06 ExitModal live-sweep triple (the unchanged live-sweep surface)"
  - "261015-ehc EHC-2 enter-inert idiom (LaunchConfirmModal)"
  - "261016-poa RED-first quick-task discipline"
provides:
  - "QuitConfirmModal — the no-sweep Y/N quit confirm (y-only, enter inert)"
  - "guarded action_quit — every exit path confirmed or refused"
  - "declared ctrl+q binding replacing the inherited App default"
  - "APP_CTRLQ_LABEL / APP_CTRLC_LABEL / LNC_EXIT_CONFIRM strings + inventory row"
affects:
  - "tui/app.py (modal family, BINDINGS, action_quit, _binding_rows, remap registry)"
  - "tui/strings.py (APP_ chrome block, LNC exit family)"
tech-stack:
  added: []
  patterns:
    - "y-only confirm modal with a documented-no-op enter binding (the LaunchConfirmModal EHC-2 idiom, applied to the exit surface)"
key-files:
  created:
    - .planning/quick/261016-v0z-guard-ctrl-q-exit-route-the-inherited-te/261016-v0z-SUMMARY.md
  modified:
    - tui/app.py
    - tui/strings.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_boot.py
    - tests/tui/test_pilot_matrix.py
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_strings_phase11.py
decisions:
  - "The inherited ctrl+q already dispatched to the overridden action_quit on 8.2.8 (probe P1) — the declared Binding makes the surface explicit, it does not change dispatch"
  - "APP_QUIT_LABEL value kept byte-identical (deviation): the plan-mandated wording renders in every golden-pinned bottom bar and golden regeneration is maintainer-only (D-03); the confirm step is surfaced by LNC_EXIT_CONFIRM + the ctrl+q/ctrl+c help rows"
  - "priority-binding prohibition amended to exempt modifier-combo keys — ctrl+q mirrors the framework default's own priority=True and cannot type into an Input"
metrics:
  duration: 34 min
  completed: 2026-10-16
status: complete
actuals:
  tokens: 31000
  tasks: 3
  commits: 4
---

# Phase quick-261016-v0z Plan 01: Guard ctrl+q / exit route — the inherited Textual exit keys + the always-confirm quit Summary

One-liner: QuitConfirmModal (y-only, enter-inert) + a restructured action_quit guard every q/ctrl+q exit path — no key kills the console unconfirmed, below-min-grid never exits, ctrl+q declared, ctrl+c audited into the help modal.

## What Landed

| Fix | File:Line | Content |
|-----|-----------|---------|
| QuitConfirmModal | `tui/app.py:226` | the no-sweep Y/N confirm: `y` -> `app.exit()`, `n`/`esc` dismiss, `enter` bound to a documented no-op (`action_enter_inert`, EHC-2), shared `LNC_EXIT_TITLE` border, `.modal-box` styling, joins `_APP_LOCAL_BINDING_SCREENS` (`tui/app.py:373`) so the L toggle remaps its esc label |
| action_quit restructure | `tui/app.py:986` | three ordered legs: (1) `below_minimum_grid` returns FIRST — no chrome over the guard, never an exit (closes the latent fall-through where a live sweep + below-min grid reached `self.exit()`); (2) live-sweep ExitModal pushes byte-identical (multi-root / single-root / attached-running); (3) the old bare `self.exit()` tail replaced by `push_screen(QuitConfirmModal(message=S.LNC_EXIT_CONFIRM))` |
| Declared ctrl+q binding | `tui/app.py:478` | `Binding("ctrl+q", "quit", show=False, priority=True, system=True)` immediately after the q entry — replaces the inherited App default per dom.py `_merge_bindings` reversed-MRO last-writer-wins (probe-pinned on 8.2.8), making the surface DECLARED and drift-proof with identical behavior |
| Help rows | `tui/app.py:1074-1075` | `_binding_rows` appends `("ctrl+q", S.APP_CTRLQ_LABEL)` and `("ctrl+c", S.APP_CTRLC_LABEL)` after the app BINDINGS rows, before the screen's — resolved live so the L toggle re-derives them |
| Strings | `tui/strings.py:162-165,1557` | `APP_CTRLQ_LABEL` (退出（同 q） / Quit (same as q)), `APP_CTRLC_LABEL` (提示退出键（不退出） / Quit-key hint (does not quit)), `LNC_EXIT_CONFIRM` (确认退出控制台？— [Y] 退出 / [N] 取消 / Quit the console? — [Y] quit / [N] cancel — the [Y]/[N] pair mirrors LNC_GATE_CONFIRM); `APP_QUIT_LABEL` value unchanged (see Deviations) |
| Inventory | `tests/tui/test_strings_phase11.py:82` | `EXPECTED_LNC_CONSTANTS` gains `LNC_EXIT_CONFIRM` — both directional tripwires cover it |
| RED suite | `tests/tui/test_pilot_run_config.py:1501-1684` | 6 app-level tests (confirm open/inert/y, n+esc cancel, ctrl+q live-sweep regression pin, ctrl+q no-sweep, below-min-grid never-exit, ctrl+c audit pin) + boot/matrix rewrites (q -> confirm, y -> return_code 0) + help-row pins x3 |

## The Corrected Root-Cause Narrative

The session-context framing ("ctrl+q bypasses the guard by dispatch") was mechanically wrong. Planning-time probes against the real `DnallmMarkTui` on textual 8.2.8 (throwaway, run from /tmp, never committed) established:

- **P1**: TODAY, ctrl+q + live sweep ALREADY opens the ExitModal — App-level bindings dispatch their action on the app namespace, so the inherited `ctrl+q -> quit` resolves to the OVERRIDDEN `action_quit`. No bypass existed.
- **P7**: dom.py `_merge_bindings` (~671) walks `reversed(cls.__mro__)` with per-key last-writer-wins — a derived-class same-key Binding REPLACES the base entry entirely. The declared entry is therefore behavior-preserving AND drift-proof.
- **P3/P4**: the explicit override behaves identically to the inherited default on both live-sweep and no-sweep paths; `system=True` matters only for key-panel exclusion, `show=False` keeps it out of footer/binding_row.
- **P5**: ctrl+c (`help_quit`, app.py:3990 on 8.2.8) scans `active_bindings` and notifies which key quits — it NEVER exits and opens NO screen. Preserved verbatim; documented in the help modal.
- **P2/P4 (the real defects)**: with NO live sweep, BOTH q and ctrl+q exited directly with no confirmation — the behavior the maintainer rejected (退出的时候要确认，不能一按q就直接退出了); and a latent fall-through let a live sweep + below-minimum grid reach `self.exit()` unguarded (RED-proven live in this task's Task 1: `assert not app._exit` failed with `app._exit == True`).

## The Maintainer Contract -> Code Map

| Ruling | action_quit leg |
|--------|-----------------|
| q ALWAYS confirms (no sweep) | leg 3 -> QuitConfirmModal (y-only; enter inert per EHC-2; n/esc cancel; q/ctrl+q inert under the modal — Pitfall 11) |
| q ALWAYS confirms (live sweep) | leg 2 -> ExitModal kill/detach/cancel triple, byte-unchanged, NO double-confirm (q inside ExitModal is inert — pinned) |
| ctrl+q behaves identically | declared binding -> the same `quit` action -> the same three legs |
| below-min grid | leg 1 returns before any chrome — never an exit, on any key |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] APP_QUIT_LABEL value amendment dropped (golden discipline wins)**
- **Found during:** Task 2 (whole-lane verification)
- **Issue:** the plan mandated amending APP_QUIT_LABEL to 退出确认 / Quit (confirm). The label renders in the bottom bar's right segment of EVERY golden-pinned screen — the plan's assertion "nothing in this task renders on a golden-pinned screen" is false. With the amended value, all 9 `tests/tui/test_snapshots.py` goldens fail (verified live; they pass at HEAD), plus the D-15 clip boundary displaced the tail [v] keycap at the 120-col design grid (2 more test failures). Green would require `make snapshot-update` — explicitly forbidden (D-03: maintainer-only regeneration; standing rule: goldens MUST stay untouched; test gate: zero new failures beyond the 7F baseline).
- **Fix:** APP_QUIT_LABEL keeps its byte-identical value (退出 / Quit, `tui/strings.py:154`); its comment documents the constraint. The confirm step is surfaced where it matters: LNC_EXIT_CONFIRM (the modal copy), the ctrl+q/ctrl+c help rows, and the guard behavior itself. The plan's RED tests reference the constant (auto-reflecting), so none needed rewriting.
- **Files modified:** tui/strings.py (comment only)
- **Commit:** a32d74a
- **Maintainer follow-up options:** accept the short footer label, or order a D-03 regeneration round that lands the amended label together with reviewed goldens.

**2. [Rule 3 - Blocking] priority-binding prohibition amended (modifier-combo exemption)**
- **Found during:** Task 2
- **Issue:** `test_no_priority_digit_binding_exists_anywhere` (tests/tui/test_pilot_nav_shell.py) grep-prohibited `priority=True` anywhere under tui/ — the plan-mandated `Binding("ctrl+q", "quit", ..., priority=True)` trips it.
- **Fix:** the prohibition now scopes to TYPING keys (any `priority=True` Binding whose key lacks a modifier): ctrl+q mirrors the framework default's own priority=True and cannot insert a character into a focused Input, so the typing hazard the prohibition guards cannot arise. Renamed to `test_no_priority_typing_key_binding_exists_anywhere`.
- **Files modified:** tests/tui/test_pilot_nav_shell.py
- **Commit:** a32d74a

**3. [Rule 2 - Correctness] QuitConfirmModal joined _APP_LOCAL_BINDING_SCREENS**
- **Found during:** Task 2
- **Issue:** the plan placed the modal "beside ExitModal, the app-local modal family" but did not name the L-toggle remap registry; without it the modal's esc label would stay in the old language after a toggle.
- **Fix:** added to `_APP_LOCAL_BINDING_SCREENS` (`tui/app.py:373`) — ExitModal/HelpModal precedent.
- **Commit:** a32d74a

## RED Evidence Summary

Task 1 committed the failing suite FIRST (b266e5d; evidence hash recorded in `RED-EVIDENCE.json` of this directory). Planned split achieved exactly: **11 failed / 177 passed** —

- RED: tests 1/2/4 (ImportError: QuitConfirmModal missing — the function-local-import RED-safe pattern), test 5 SEMANTIC (`app._exit` True below the min grid with a live sweep — the latent fall-through proven live), tests 7/8 (boot/matrix rewrites), test 9 x3 (missing APP_CTRLQ_LABEL/APP_CTRLC_LABEL), test 10 x2 (inventory: stale registration ['LNC_EXIT_CONFIRM']).
- GREEN (regression pins): test 3 (ctrl+q + live sweep opens the ExitModal TODAY — probe P1 confirmed live in-protocol) and test 6 (ctrl+c never exits/opens — probe P5), plus every unmodified live-sweep exit test (enter-detach / k-kill / esc-cancel / multi-root).

## Golden Integrity Proof

```
$ git status --porcelain tests/tui/__snapshots__/
 M tests/tui/__snapshots__/run_config.svg        # the pre-existing 261016-poa D-03 review artifact
$ sha256sum tests/tui/__snapshots__/run_config.svg
afa89e7e5452e15aebd4ac11584d794a9dd29d002ab9bc8d8b1e92d39ced8ef2  (== the Task-1 snapshot, byte-identical)
$ pytest tests/tui/test_snapshots.py -q
9 passed                                        # green against the on-disk SVGs
```

No `make snapshot-update` was run; no SVG was committed; the only worktree modification is the inherited run_config.svg, byte-identical to its state before this task began.

## Final Gate Numbers

- `make lint` (ruff): **All checks passed**
- `make typecheck` (ty): **All checks passed**
- full pytest: **7 failed / 1823 passed** — EXACTLY the 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1 — all verified pre-existing at HEAD), zero new failures, every test added by Tasks 1-2 passing
- node: **26/26 pass** (tests/js)
- tests/tui lane: 1125 passed / 1 pre-existing baseline member

## Auth Gates

None.

## Known Stubs

None — no stubs, no skipped tests, no unrun verify steps.

## Self-Check: PASSED

- Files: tui/app.py, tui/strings.py, 7 test files, SUMMARY (this file) — all present
- Commits b266e5d (RED), 6dff5a5 (evidence hash), a32d74a (GREEN) — all ancestors of HEAD
