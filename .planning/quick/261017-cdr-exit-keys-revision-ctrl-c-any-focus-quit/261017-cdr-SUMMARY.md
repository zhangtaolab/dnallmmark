---
phase: quick-261017-cdr
plan: 01
subsystem: tui
tags: [tui, exit-keys, ctrl-c, quit-confirm, bindings, i18n, tests]
requires:
  - "261016-v0z action_quit three-leg confirm chain + QuitConfirmModal (the unchanged exit surface)"
  - "261016-vxr on_event intercept seam (P10-P14 probe facts) + the P9 stacking finding"
provides:
  - "ctrl+c the any-focus primary exit (on_event intercept through the v0z confirm chain, inert under modals, no help_quit notify anywhere)"
  - "capital Q restored as a plain typing letter (intercept/row/constant fully withdrawn)"
  - "action_quit exit-family stacking guard (ExitModal/QuitConfirmModal top -> immediate return)"
  - "QuitConfirmModal prominence: bold [Y]/[N] tokens + visible y/n Footer keycaps (LNC_EXIT_CONFIRM_YES/NO)"
affects:
  - "tui/app.py (QuitConfirmModal, action_quit, on_event, _binding_rows, module docstring)"
  - "tui/strings.py (APP_ chrome block, LNC exit family)"
key-files:
  created:
    - .planning/quick/261017-cdr-exit-keys-revision-ctrl-c-any-focus-quit/RED-EVIDENCE.json
    - .planning/quick/261017-cdr-exit-keys-revision-ctrl-c-any-focus-quit/261017-cdr-SUMMARY.md
  modified:
    - tui/app.py
    - tui/strings.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_strings_phase11.py
decisions:
  - "CDR-2 seam = the on_event intercept (the vxr-proven shape with the key swapped), NOT a declared priority binding — the priority path walks the full binding chain and would stack exit modals over NON-exit modals (the P9 mechanism the maintainer flagged); the intercept delivers the same base-screen focused-Input reach with base-screen-only semantics"
  - "NO replacement ctrl+c Binding declared — a non-priority one could never fire (shadowed on base screens by the intercept, chain-cut under modals): dead code; the on_event docstring documents the shadowing instead (the honest form of the v0z drift-proofing rationale)"
  - "CDR-4 guard coverage EXACTLY (ExitModal, QuitConfirmModal) — KillConfirmModal/E2PhraseModal deliberately out: kill != exit (the vxr VXR-2 ruling), a quit over them is new legitimate intent that stacks and esc-peels back"
  - "Text.highlight_words mutates IN PLACE and returns int (installed rich text.py:639) — the two-step form, never chained; styling via the Text API only (Text content is never markup-parsed, bracket tokens stay literal)"
metrics:
  duration: 18 min
  completed: 2026-10-17
status: complete
requirements: [CDR-1, CDR-2, CDR-3, CDR-4, CDR-5]
actuals:
  tokens: 11621
  tasks: 3
  commits: 2
plan_head_before: 88f4642
plan_head_after: 0980956
---

# Quick Task 261017-cdr: exit-keys revision — ctrl+c any-focus quit, Q restored, P9 guard, prominent Y/N confirm

The maintainer's 2026-10-17 08:54 revision batch over last night's v0z/vxr exit keys: (1) the uppercase-Q interception withdrawn — Q is a plain typing letter again; (2) ctrl+c is the any-focus primary exit, routed through the v0z confirmation chain and overriding textual 8.2.8's notify-only help_quit default; (3) QuitConfirmModal's Y/N prompts made prominent — bold [Y]/[N] tokens plus visible y/n Footer keycaps; (4) the P9 modal-stacking defect closed with an action_quit early-return guard when an exit-family modal is already top.

## CDR-1 — Q withdrawal (file:line)

- `tui/app.py:1086` — `DnallmMarkTui.on_event` no longer matches key `"Q"`: the intercept is rewritten to `ctrl+c` (CDR-2); NOTHING Q-specific remains anywhere.
- `tui/app.py:1159` — the `("Q", S.APP_Q_LABEL)` help-row append is deleted from `_binding_rows` (the block comment now records the retirement).
- `tui/strings.py:167-170` — `APP_Q_LABEL` and its comment block are deleted; the rewritten block comment documents the withdrawal.
- Pinned: `test_q_uppercase_is_a_plain_typing_letter_again` — a capital Q over the focused seeds Input TYPES (value `"Q"`, the select_on_focus replace semantics), the screen stays RunConfigScreen, no modal anywhere in the stack, no exit; the modal-Input leg (`test_ctrlc_inert_under_modals_never_stacks` leg d) pins Q typing inside PathInputModal. Lowercase q semantics byte-unchanged (`test_q_lowercase_still_types_into_inputs`, untouched).

## CDR-2 — ctrl+c the any-focus primary exit (file:line)

**Seam decision (the load-bearing one).** A declared priority `Binding("ctrl+c", ...)` would deliver the focused-Input reach (ctrl combos are never consumed by an Input — vxr P3/P8) but the priority path walks the FULL `_binding_chain`, so it would also fire under EVERY open modal (P9) and stack exit modals over the wizard, the E2' phrase modal, or a picker. The `on_event` intercept with the `not self.screen.is_modal` guard delivers the same base-screen reach with base-screen-only semantics — precisely the any-focus exit scoped to where the filter-input focus trap lives. Under modals the key delegates to `super().on_event` -> the modal-cut binding chain; the inherited textual 8.2.8 default `Binding("ctrl+c", "help_quit", show=False, system=True)` (verified at `.venv .../textual/app.py:463`) is NON-priority, so it is chain-cut under modals -> inert, no notify. On base screens the intercept consumes the key before the machinery, so help_quit never fires anywhere — the v0z notify-only audit disappears WITHOUT a declared replacement binding (a non-priority one could never fire: shadowed on base screens, chain-cut under modals — dead code; the docstring documents the shadowing instead). Below-min-grid: MinSizeScreen is a plain non-modal Screen, so the intercept routes into action_quit whose leg 1 returns — same behavior as q. zellij's default config passes ctrl+c through to the pane program (maintainer assertion, noted in the docstring).

**Landed:** `tui/app.py:1086-1123` — the rewritten intercept (key `"ctrl+c"`, mounted non-modal top screen, routes to the UNMODIFIED v0z chain, consumed without `super()`); `tui/strings.py:169-170` — `APP_CTRLC_LABEL` amended to `退出（任意焦点生效） / Quit (works at any focus)` (the retired APP_Q_LABEL wording verbatim — the retired-Q 抢输入 conflict solved); the help row itself lives at `tui/app.py:1159`.

**Dispatch probe result:** the RED suite doubled as the ctrl+c-over-Input probe — today's failure showed the ctrl+c Key event is NOT swallowed by the focused Input (it reached the machinery and fired the inherited binding), and the GREEN flip on the first run proved `App.on_event` sees it first. No seam re-probe needed; the mechanism was never swapped.

## CDR-3 — prominent Y/N confirm (file:line)

- `tui/app.py:261-262` — the `y`/`n` bindings gain `show=True` with descriptions `S.LNC_EXIT_CONFIRM_YES` / `S.LNC_EXIT_CONFIRM_NO`, so the modal's Footer renders the y/n keycaps beside esc; enter stays `show=False` (the inert no-op is never advertised); QuitConfirmModal is already in `_APP_LOCAL_BINDING_SCREENS` so the L toggle re-derives the keycaps.
- `tui/app.py:271-284` — compose builds `Text(self._message)` then `highlight_words(("[Y]", "[N]"), style="bold")` and yields the Text to the modal's Static. `highlight_words` MUTATES in place and returns int (installed rich `text.py:639`) — the two-step form, never chained (ty caught the chained form as `Static(int)`; fixed inline). Text content is never markup-parsed (the HelpModal literal-keycap precedent), so the bracket tokens stay literal — no markup-string ambiguity; `bold` is a Rich core style, no `$token` MissingStyle hazard.
- `tui/strings.py:1571-1574` — `LNC_EXIT_CONFIRM_YES` (`退出 / Quit`) and `LNC_EXIT_CONFIRM_NO` (`取消 / Cancel`) beside `LNC_EXIT_CONFIRM` (whose plain value is byte-unchanged, so every existing content assertion kept passing). Identical registry pairs already exist (`APP_QUIT_LABEL`/`LNC_EXIT_TITLE`, `WIZ_CANCEL_LABEL`/`DL_CANCEL_LABEL`) — both bidirectional injectivity tripwires stay green.
- `tests/tui/test_strings_phase11.py:82-86` — both names join `EXPECTED_LNC_CONSTANTS` (closed bidirectional inventory).

## CDR-4 — the P9 stacking guard (file:line)

- `tui/app.py:1048-1057` — `action_quit`'s FIRST statement: `if isinstance(self.screen, (ExitModal, QuitConfirmModal)): return` — before the below-min-grid leg (docstring leg (0) added). A second exit-family push can never stack over an open one.
- **Coverage set exactly (ExitModal, QuitConfirmModal), justified:** the guard prevents DUPLICATE pushes of the same exit surface (the P9 defect: priority ctrl+q re-entering action_quit while its own modal is top — live-proven at RED with stack count 2). `KillConfirmModal` deliberately OUT: kill != exit (the vxr VXR-2 distinct-acts ruling) — a quit issued while a kill confirm is open is new legitimate intent; the exit modal stacks over it and esc peels back, and its y-only confirm still guards the kill. `E2PhraseModal` and every launch-side/selection modal OUT for the same reason. After CDR-2, ctrl+c can never reach action_quit under ANY modal (intercept guard), so the guard's only live trigger is ctrl+q under an exit-family modal — still required, because ctrl+q stays a priority binding.
- `tui/app.py:230-258` — the QuitConfirmModal docstring's stale "q/ctrl+q are inert under the modal" claim corrected to the two-mechanism truth: plain q chain-cut per Pitfall 11; ctrl+q fires but the action_quit guard closes it; ctrl+c delegates to the modal-cut chain and is likewise inert.

## RED evidence summary

`.planning/quick/261017-cdr-exit-keys-revision-ctrl-c-any-focus-quit/RED-EVIDENCE.json` — **12 failed / 213 passed** at the exact planned split, committed at `77fe61d`:
- RED: the two ctrl+c chain legs (no modal opens today — and the failure shape proves the ctrl+c Key event reaches the app machinery over a focused Input); the Q-plain-letter inversion (value stays `42,43,44`); the P9 stack pins (assert 2 == 1, live-proven); the keycap pin (ImportError — constants absent) and the bold pin (content is a plain str); the inventory pair; the four help-row pins (three row mismatches + the monitor negative pin).
- GREEN regression pins: `test_ctrlc_inert_under_modals_never_stacks` (all four legs), `test_ctrlc_below_min_grid_never_exits`, `test_q_lowercase_still_types_into_inputs`, every kept v0z exit test, and the whole ExitModal triple + multi-root family.
- Deleted: the v0z audit pin `test_ctrlc_never_exits_or_opens_modal` (its no-screen/no-exit assertions are false after the revision; its no-sweep truth is absorbed into the primary-leg test).

## Final gate numbers (read at execution time)

- `make lint` (ruff): **All checks passed**
- `make typecheck` (ty): **All checks passed**
- full pytest: **7 failed / 1845 passed** at EXACTLY the 7F baseline membership (`test_determinism` 1, `test_schemas` 5, `test_services_run_config` 1 — the machine-local pipeline/logs member), zero new failures, every 261017-cdr test passing (vxr baseline before the change: 7F/1842P; +3 net tests)
- node lane: **26/26** (tests 26, pass 26, fail 0)
- `tests/tui/test_snapshots.py`: **11/11 green against the on-disk SVGs**

## Golden-integrity proof (the D-03 discipline)

```
$ git status --porcelain tests/tui/__snapshots__/
 M tests/tui/__snapshots__/monitor_empty.svg
 M tests/tui/__snapshots__/monitor_running.svg
 M tests/tui/__snapshots__/run_config.svg
$ sha256sum (Task 3 gates)  ==  the Task-1 record, all three:
  monitor_empty.svg    3bcc4dca3c7ed747fcd73ddd053b566039f88d8feaa50ab3f7e846ce53192473
  monitor_running.svg  e4e803e8bbb8b3a2e6524bf8cb05347485765f27ef69303ebda20deb6531eaf1
  run_config.svg       afa89e7e5452e15aebd4ac11584d794a9dd29d002ab9bc8d8b1e92d39ced8ef2
```

Byte-identical to the Task-1 sha256 record — ZERO golden interaction, as argued in-plan: the Q help row lives only in the help modal (never golden-pinned), ctrl+c changes no base-screen bar (no new Binding; the manual help row only), no golden renders QuitConfirmModal (the corpus pins the five base screens + wizard + two selection views + two data-manager views + run-config). `make snapshot-update` was NEVER run; the three modifications are EXACTLY the pre-existing uncommitted D-03-pending artifacts (maintainer-owned), untouched by this task.

## Deviations from Plan

**1. [Rule 1 - the plan's chained highlight_words form would not typecheck]**
- **Found during:** Task 2 (make typecheck)
- **Issue:** the plan's key_link sketched `Text(message).highlight_words(...)` chained into Static — the installed rich's `highlight_words` returns `int` (the highlight count; `.venv .../rich/text.py:639`), mutating the Text in place, so the chained form passes an int to Static.
- **Fix:** the two-step form (`message = Text(...)` then `message.highlight_words(...)`) with a comment pinning the probe fact — identical span behavior, ty green.
- **Files:** tui/app.py
- **Commit:** 0980956

**2. [Rule 3 - ty union narrowing in the keycap test]**
- **Found during:** Task 2 (make typecheck)
- **Issue:** the `entries` dict comprehension over `QuitConfirmModal.BINDINGS` tripped ty's union type (`Binding | tuple[...]`).
- **Fix:** `isinstance(binding, Binding)` narrowing in the comprehension (function-local import).
- **Files:** tests/tui/test_pilot_run_config.py
- **Commit:** 0980956

## Threat-model dispositions (all mitigate/accept as planned)

- **T-261017cdr-01 (event tampering)** — mitigated: the intercept matches ONLY `events.Key` with key exactly `"ctrl+c"` under a mounted non-modal screen; every other event delegates to `super()` unchanged (the vxr-proven seam with the key string swapped).
- **T-261017cdr-02 (DoS via the guard)** — mitigated: the guard only short-circuits DUPLICATE exit-surface pushes; every actual exit still requires the explicit y confirm or the ExitModal triple — pinned by the stack-depth and no-exit tests.
- **T-261017cdr-03 (rendering tampering)** — mitigated: styling via the Rich Text API over the static registry constant — Text content is never markup-parsed, no bracket-injection surface.
- **T-261017cdr-04 (help-row repudiation)** — accepted: the ctrl+c row resolves live from the amended constant, pinned by four help-row tests.
- **T-261017cdr-SC (package installs)** — mitigated: zero package installs, zero dependency/lockfile changes.

## Known Stubs

None — no stub patterns introduced; every surface is wired to real behavior or its designed honest degradation.

## Self-Check: PASSED

All eight key files exist on disk; both task commits (77fe61d RED, 0980956 GREEN) are ancestors of HEAD; the three D-03 SVGs remain uncommitted and byte-identical to the Task-1 record; nothing was pushed.
