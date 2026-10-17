---
phase: quick-261017-mad
plan: 01
subsystem: tui-exit-keys
tags: [exit-keys, f10-any-focus-quit, ctrl-c-withdrawal, terminal-copy, help-modal, golden-discipline]
requires:
  - "The maintainer's 2026-10-17 16:02 exit-key final ruling (根据你建议来 — the F10 plan accepted)"
  - "261016-v0z guarded confirm chain (action_quit legs + QuitConfirmModal/ExitModal)"
  - "261017-cdr P9/CDR-4 exit-family stacking guard"
  - "261017-klw WR-01/WR-02 exit-channel work (the on_event override deleted here)"
provides:
  - "F10 any-focus primary exit: a DECLARED priority binding f10 -> quit through the v0z confirm chain (MAD-1)"
  - "ctrl+c interception fully withdrawn (the whole on_event override deleted) with textual 8.2.8 terminal-native semantics restored and pinned (MAD-2)"
  - "q / ctrl+q / ExitModal / QuitConfirmModal behavior byte-unchanged (MAD-3 regression pins)"
  - "Bilingual help-modal sync: APP_F10_LABEL new + APP_CTRLC_LABEL reworded; APP_QUIT_LABEL/APP_CTRLQ_LABEL byte-identical (MAD-4)"
affects:
  - tui/app.py (BINDINGS f10 entry, on_event deleted, 5 prose sites)
  - tui/strings.py (APP_F10_LABEL added, APP_CTRLC_LABEL reworded)
  - tests/tui/test_pilot_run_config.py (F10 battery + withdrawal battery)
  - tests/tui/test_pilot_env_check.py, test_pilot_nav_shell.py, test_pilot_selection.py (help-row pins)
  - tests/tui/test_pilot_monitor.py (comment-only)
tech-stack:
  added: []
  patterns:
    - "Non-printable priority binding over a focused Input (textual 8.2.8): the App priority check precedes the focused-widget forward and the consume-key filter strips only PRINTABLE priority bindings — f10 passes, so the declarative seam needs no on_event fallback"
    - "The priority-typing-key tripwire now derives printability from textual's own key_to_character + isprintable (the Key.is_printable predicate that gates Input insertion) instead of the no-'+' heuristic that misclassified function keys"
key-files:
  created:
    - .planning/quick/261017-mad-exit-keys-final-f10-any-focus-quit-prima/261017-mad-SUMMARY.md
  modified:
    - tui/app.py
    - tui/strings.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_monitor.py
decisions:
  - "APP_CTRLC_LABEL row KEPT and reworded (zh 终端复制/中断（非退出） / en Terminal copy/interrupt (not quit)) rather than removed — the ruling's stated preference for one explanation line; constant name and the literal ctrl+c key string unchanged so the three help-row pins auto-derive"
  - "The F10 manual help row placed FIRST among the manual exit rows (before ctrl+q) — F10 is the primary per the ruling; q/ctrl+q are same-role alternates"
  - "APP_QUIT_LABEL and APP_CTRLQ_LABEL left untouched — APP_QUIT_LABEL renders in every golden-pinned bottom bar and regeneration is maintainer-only (D-03); the F10 binding carries show=False + no description so no bar renders it at all"
  - "The below-min-grid tests merged into one both-keys test (test_exit_keys_below_min_grid_never_exit) — the Task-1 f10 standalone absorbed; the two ctrl+c routing tests deleted whose F10 twins landed in Task 1"
actuals:
  tokens: 12000    # chars/4 over the realized code diff (48144 chars, 7 files)
  tasks: 3
  commits: 2       # measured at SUMMARY write: git rev-list --count c1f2567..HEAD (the mandated records commit lands after, 3 total)
plan_head_before: c1f2567041b080a6748cf72068b7a3ccb4933448
plan_head_after: c8f6f44f92e2c07fc9c3909f8e6cf407bd91144d
status: complete
---

# Quick Task 261017-mad: exit keys final state — F10 any-focus quit, ctrl+c withdrawn Summary

**One-liner:** The maintainer's 2026-10-17 16:02 exit-key final ruling landed — F10 becomes the any-focus primary exit as a DECLARED priority binding (probe-confirmed seam: non-printable priority passes the focused-Input consume-key filter) through the byte-unchanged v0z confirm chain, the entire ctrl+c on_event override is deleted so terminal-native copy/interrupt semantics hold with zero app-level ambushing, and the help modal names all of it bilingually with golden-pinned strings untouched.

## What Was Built

### Task 1 — F10 declarative any-focus exit (commit 413ec72)

- `tui/app.py` BINDINGS: `Binding("f10", "quit", show=False, priority=True, system=True)` immediately after the ctrl+q mirror, with the full ruling/probe/golden-discipline comment. No description — the help row is manual and live-language-resolved (the ctrl+q idiom; `remap_binding_descriptions` skips description-less entries by design).
- `tui/app.py` `_binding_rows`: the manual `("f10", S.APP_F10_LABEL)` row inserted BEFORE the ctrl+q row.
- `tui/strings.py`: `APP_F10_LABEL = _t("APP_F10_LABEL", "退出（任意焦点）", "Quit (any focus)")` registered beside the APP_CTRLQ/CTRLC block (injectivity-safe unique pair — both registry tripwires green).
- The three exact-list help-row pins (env_check / nav_shell / selection) gained the f10 row between the L row and the ctrl+q row, with updated comments.
- The RED-first F10 battery landed in tests/tui/test_pilot_run_config.py (four tests; see RED evidence).

### Task 2 — ctrl+c interception withdrawn (commit c8f6f44)

- The ENTIRE `App.on_event` override deleted (the cdr ctrl+c intercept + the klw WR-01 Input-selection delegation + the vxr-era structural residue — one method, 55 lines). `Input` trimmed from the widgets import (the override was its only consumer); the `events` import stays (the resize handler uses it).
- Five prose sites updated (semantics untouched elsewhere): the module docstring's binding paragraph, the BINDINGS comment block, action_quit's docstring head, QuitConfirmModal's inertness-map paragraph, the `_binding_rows` comment.
- `tui/strings.py`: APP_CTRLC_LABEL reworded in place (constant name and key string unchanged) + its comment block rewritten for the withdrawal.
- The battery rewritten (see RED evidence): the WR-01 copy test became the native-copy pin + collapsed-contrast; the no-focus ambush pin added; the modal test rewritten to native chain-cut + the f10-over-PathInputModal stack-and-peel-back leg + the kept capital-Q-types leg; the below-min-grid tests merged into one both-keys test; the two ctrl+c routing tests deleted (F10 twins from Task 1); the Q-plain-letter docstring touched; the monitor help test comment-only (its membership assertions already true).
- Structural proof: `grep -c selected_text tui/app.py` → **0** and `grep -c is_modal tui/app.py` → **0** (both were single-site tokens of the deleted method, one docstring + one code occurrence each before deletion).

### Task 3 — gates + records (this commit)

Gates from the repo root (readings above in the Gates section).

## Planning-Time Probe Evidence (verbatim from the plan — recorded as required)

Locked textual 8.2.8 via `uv run --group tui`, 2026-10-17, throwaway scripts never committed:

- **LEG1:** an App priority `Binding("f10", ..., priority=True)` with a focused Input (select_on_focus active selection) — pressing f10 FIRED the action. Non-printable priority bindings pass the consume-key filter that strips printable priority bindings over focused Inputs. THE DECLARATIVE SEAM IS CONFIRMED; the on_event fallback is not needed.
- **LEG2:** the same priority f10 fired over an open ModalScreen (the ctrl+q P9 mechanism — expected; the CDR-4 guard owns exit-family stacking).
- **LEG3:** bare f10 with no app binding is inert on a bare App (f10 is not a textual framework default; nothing to shadow).
- **POST-DELETION ctrl+c** (no app on_event override): a selection-holding focused Input copies natively (clipboard receives the selection, no notify); an empty-selection Input or no Input focus fires the inherited help_quit notify naming ctrl+q (no modal, no exit); a modal top chain-cuts it (inert).

Executor re-confirmation: the RED 1 test itself is the live-seam proof (it failed with f10 inert pre-binding, went green on the declarative binding alone — no fallback ever written, so the plan's STOP-and-report branch never triggered).

## RED Evidence

### Task 1 (run against pre-task code, before the binding landed)

```
uv run --group dev --group tui pytest tests/tui/test_pilot_run_config.py -q -k "test_f10"
FAILED test_f10_no_sweep_opens_quit_confirm_over_focused_input
  → assert isinstance(app.screen, QuitConfirmModal) — screen stayed
    RunConfigScreen: f10 inert, no modal opens (the cited reason)
FAILED test_f10_live_sweep_routes_to_exit_modal_over_focused_input
  → assert isinstance(app.screen, ExitModal) — same inert press
PASSED test_f10_under_exit_modal_never_stacks_second  (before/after pin:
  with f10 inert nothing stacks; becomes a REAL P9/CDR-4 pin once the
  priority binding lands — green after)
PASSED test_f10_below_min_grid_never_exits  (before/after pin — the
  before-state twin of the CDR-2 below-min-grid pin; later absorbed
  into the merged both-keys test in Task 2)
2 failed, 2 passed
```

GREEN after the binding + help rows landed: all four green, the three help-row pins green, 184 passed over the four Task-1 files, ruff + ty green.

### Task 2 (run against the still-present intercept, before the deletion)

```
uv run --group dev --group tui pytest tests/tui/test_pilot_run_config.py \
  -q -k "ctrlc or exit_keys_below or q_uppercase"
FAILED test_ctrlc_copies_when_input_holds_a_real_selection
  → the collapsed-contrast leg: the intercept opened the QuitConfirmModal
    on the empty-selection press (assert not any(... ExitModal,
    QuitConfirmModal ...) over screen_stack failed)
FAILED test_ctrlc_without_input_focus_ambushes_nothing
  → the intercept routed the bare no-focus press into action_quit →
    QuitConfirmModal (the exact ambush scenario the withdrawal closes)
PASSED test_modal_exit_semantics_native_ctrlc_and_f10  (before/after
  pin: the intercept's not-modal guard was already inert under modals;
  the f10 stack-and-peel-back leg green since the Task-1 binding)
PASSED test_exit_keys_below_min_grid_never_exit  (before/after pin)
PASSED test_q_uppercase_is_a_plain_typing_letter_again  (docstring-only
  touch)
2 failed, 3 passed
```

GREEN after the withdrawal: 145 passed over the three Task-2 files (run_config + monitor + work-site hardening — the AST pin green with zero edits), the strings tripwires + three help-pin files 97 passed, ruff + ty green, grep proof zero/zero.

Note: the plan predicted RED 3's inertness legs would fail pre-deletion; empirically they passed — the intercept's `not is_modal` guard made ctrl+c inert under modals on day one, so those legs are before/after pins rather than hard REDs. The two hard REDs (the contrast leg and the ambush pin) are the exact behaviors the withdrawal changes; recorded as observed, not as predicted.

## Planner Discretion Decisions (recorded for the maintainer per the ruling's delegated discretion)

1. **APP_CTRLC_LABEL kept and reworded, not removed** — the ruling's stated preference to keep one explanation line. zh 终端复制/中断（非退出） / en Terminal copy/interrupt (not quit): the row now anti-misreads (says what the key DOES and that it is not quit). Constant name and the literal `ctrl+c` key string unchanged, so the three exact-list help-row pins auto-derive.
2. **The F10 manual row placed FIRST among the exit rows** (`f10`, then `ctrl+q`, then `ctrl+c`) — F10 is the primary per the ruling; q/ctrl+q are same-role alternates. The q row (from the BINDINGS projection) stays ahead of all manual rows as before.
3. **APP_QUIT_LABEL / APP_CTRLQ_LABEL left byte-identical** — APP_QUIT_LABEL renders in the bottom bar of every golden-pinned screen; regeneration is maintainer-only (D-03, the recorded 261016-v0z deviation discipline). The F10 binding carries `show=False` and no description, so `binding_row` skips it and no bar changes at all — the goldens prove it (11/11 green, zero SVG churn).

## Gates (Task 3, from the repo root)

| Gate | Reading |
|------|---------|
| `make lint` (ruff) | All checks passed |
| `make typecheck` (ty) | All checks passed |
| full pytest lane | `1 failed, 1869 passed` — EXACTLY the baseline membership: the sole failure is the machine-local `tests/tui/test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers` (unchanged), 1867 baseline + 2 net new tests (Task 1 +4, Task 2 −2 routing −1 absorbed +1 ambush), zero new failures |
| node lane (`node --test tests/js/*.test.js`) | 26/26 pass |
| `pytest tests/tui/test_snapshots.py -q` | 11/11 green — zero SVG interaction, `git diff c1f2567 -- tests/tui/__snapshots__/` empty |
| `git diff c1f2567 -- tui/strings.py` | exactly the APP_F10_LABEL addition + APP_CTRLC_LABEL reword + comments; APP_QUIT_LABEL / APP_CTRLQ_LABEL byte-identical |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The priority-typing-key tripwire misclassified function keys**
- **Found during:** Task 1 verify — `tests/tui/test_pilot_nav_shell.py::test_no_priority_typing_key_binding_exists_anywhere` failed against the plan-mandated priority f10 binding.
- **Issue:** the tripwire's heuristic treated every key without a `+` as a typing key; f10 (a function key) cannot insert text into an Input, so the test's own stated contract ("a priority binding ... breaks typing") was not actually violated — the heuristic was.
- **Fix:** the typing-key determination now uses textual's own `key_to_character` + `isprintable()` — the runtime `Key.is_printable` predicate that gates Input insertion. Modifier combos remain exempt by construction (the mapping returns None for them, the ctrl+q precedent documented in the docstring).
- **Files modified:** tests/tui/test_pilot_nav_shell.py
- **Commit:** 413ec72

**2. [Rule 3 - Blocking] The plan's Task-2 predicted-RED mapping did not match empirical RED**
- **Found during:** Task 2 RED run — RED 3's inertness legs and the ctrl+c below-min-grid leg PASS against the intercept (its `not is_modal` guard was already inert under modals), so they are before/after pins, not hard REDs.
- **Fix:** none needed — the plan's implementation steps were unaffected; the RED evidence above records the observed failure set (2 hard REDs: the contrast leg + the ambush pin) instead of the predicted one. No behavior difference; documentation-only deviation.

Otherwise the plan executed exactly as written.

## Known Stubs

None — no stubs, no placeholder copy, no unrun verify steps in this task.

## Threat Flags

None — no security-relevant surface beyond the plan's threat model. T-mad-01 (f10 reach is confirm-gated end to end via the byte-unchanged v0z chain + CDR-4 + WR-06) and T-mad-02 (withdrawal eliminates the ambush surface, pinned by the no-exit-anywhere tests) are both realized as planned; T-mad-03 accepted as planned.

## Deferred Issues (out of scope, recorded)

- `test_monitor_running_golden` load-timing flake — observed ONCE at the pre-task baseline full-suite run (before any edit; 2F/1866P), not reproduced on an identical rerun (1F/1867P) nor in isolation (11/11 twice). The SVG `terminal-<id>` is an adler32 hash over every rendered segment, so one segment differed under load; all golden-fixture data is frozen and this task never touched the monitor screen or snapshots. Recorded in `deferred-items.md` and `.planning/WINDOWS.md` (entry #32, kind deviation) for ship-time visibility. Details: `.planning/quick/261017-mad-exit-keys-final-f10-any-focus-quit-prima/deferred-items.md`

## Self-Check: PASSED

All created/modified files exist on disk; both code commits (413ec72, c8f6f44) are ancestors of HEAD; the SUMMARY/deferred-items/planning artifacts present; gates re-read at Task 3 (1F/1869P + node 26/26 + goldens 11/11 + lint/ty green).
