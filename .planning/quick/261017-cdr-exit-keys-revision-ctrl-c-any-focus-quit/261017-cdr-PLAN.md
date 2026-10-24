---
phase: quick-261017-cdr
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_strings_phase11.py
  - tui/app.py
  - tui/strings.py
  - .planning/STATE.md
  - .planning/quick/261017-cdr-exit-keys-revision-ctrl-c-any-focus-quit/261017-cdr-SUMMARY.md
autonomous: true
requirements: [CDR-1, CDR-2, CDR-3, CDR-4, CDR-5]

user_setup: []

estimate:
  tokens: 40000
  raw_tokens: 21000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "CDR-1 (Q withdrawal): the 261016-vxr uppercase-Q intercept is FULLY retired — App.on_event no longer matches key 'Q' (the intercept is rewritten to ctrl+c per CDR-2, nothing Q-specific remains), the ('Q', APP_Q_LABEL) help row is gone from _binding_rows, APP_Q_LABEL is deleted from tui/strings.py, and a capital Q is a PLAIN TYPING LETTER again everywhere: over a focused base-screen Input it TYPES (select_on_focus replace semantics, value 'Q') and opens NO modal, inside modal Inputs it types (existing modal behavior, kept pinned); lowercase q semantics are byte-unchanged."
    - "CDR-2 (ctrl+c = the any-focus primary exit): DnallmMarkTui.on_event intercepts events.Key with key == 'ctrl+c' when a screen is mounted and its top screen is NOT modal, routes to the UNMODIFIED v0z action_quit chain (below-min-grid -> nothing; live sweep -> ExitModal; neither -> QuitConfirmModal), and consumes the key WITHOUT super(); ctrl+c fires over a focused base-screen Input with the Input value unchanged (ctrl combos never type); ctrl+c under ANY modal is inert (no exit, no modal push — the intercept's not-modal guard); the inherited textual 8.2.8 ctrl+c help_quit default (non-priority, .venv textual/app.py:463) is thereby shadowed on base screens AND chain-cut under modals, so the notify-only audit disappears everywhere without a declared replacement binding; the help-modal ctrl+c row (APP_CTRLC_LABEL) now reads the exit semantics (values '退出（任意焦点生效）' / 'Quit (works at any focus)', the retired APP_Q_LABEL wording)."
    - "CDR-3 (prominent Y/N confirm): QuitConfirmModal's message Static is built as a rich Text from LNC_EXIT_CONFIRM with every '[Y]' and '[N]' token covered by a style='bold' span (Text.highlight_words — Text content is never markup-parsed, the bracket tokens stay literal, no markup-string ambiguity; 'bold' is a Rich core style, not a $token, so no MissingStyle hazard); the modal's y and n bindings carry show=True with descriptions LNC_EXIT_CONFIRM_YES ('退出'/'Quit') and LNC_EXIT_CONFIRM_NO ('取消'/'Cancel') so the modal's Footer renders y/n/esc keycaps (enter stays show=False — the inert no-op is never advertised); the L toggle re-derives the new keycaps automatically (QuitConfirmModal is in _APP_LOCAL_BINDING_SCREENS); both new constants are bilingual via _t and join EXPECTED_LNC_CONSTANTS (closed bidirectional inventory); the plain-text message value LNC_EXIT_CONFIRM is byte-unchanged so every existing content assertion keeps passing."
    - "CDR-4 (P9 stacking guard): action_quit returns IMMEDIATELY (before the below-min-grid leg) when the top screen is an ExitModal or QuitConfirmModal — a second exit-family push can never stack over an open one; the only live trigger after CDR-2 is ctrl+q (priority binding, fires over modals — probe P9) pressed while an exit-family modal is top, and it now does nothing (stack depth stays 1, no exit); the guard's coverage set is EXACTLY (ExitModal, QuitConfirmModal) — KillConfirmModal is deliberately OUT (kill != exit: a quit issued over a kill confirm is a new legitimate intent; the exit modal stacks over it and esc peels back), and every launch-side/selection modal (E2PhraseModal, wizard, pickers) is OUT for the same reason; the QuitConfirmModal docstring's stale 'q/ctrl+q are inert under the modal' claim is corrected to the two-mechanism truth (plain q chain-cut per Pitfall 11; ctrl+q fires but is closed by the guard)."
    - "CDR-5 (gates, goldens, discipline): make lint + make typecheck green; full pytest at EXACTLY the 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1) with zero new failures and every new/rewritten test passing (read the actual counts at execution time — the 7F MEMBERSHIP is the invariant); node lane 26/26; tests/tui/test_snapshots.py 11/11 against the on-disk SVGs; the three uncommitted D-03 SVGs (monitor_empty, monitor_running, run_config) are byte-preserved — sha256 recorded before Task 1 and re-verified at the gates; make snapshot-update is NEVER run, and if any snapshot test fails after GREEN the executor STOPS (no regeneration) and reports the D-03 path; commits are PLAIN (zero attribution trailers); the executor does NOT push."
  artifacts:
    - tui/app.py
    - tui/strings.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_strings_phase11.py
    - .planning/quick/261017-cdr-exit-keys-revision-ctrl-c-any-focus-quit/RED-EVIDENCE.json
    - .planning/quick/261017-cdr-exit-keys-revision-ctrl-c-any-focus-quit/261017-cdr-SUMMARY.md
  key_links:
    - "terminal ctrl+c -> DnallmMarkTui.on_event (key=='ctrl+c', screen mounted, not modal) -> action_quit guard (CDR-4 early return | below-min-grid return | ExitModal | QuitConfirmModal) — consumed, no super() (CDR-2/CDR-4)"
    - "ctrl+q (priority Binding) over an exit-family modal -> action_quit -> isinstance guard -> return, stack depth unchanged (CDR-4)"
    - "LNC_EXIT_CONFIRM string -> Text(message).highlight_words(('[Y]','[N]'), 'bold') -> QuitConfirmModal Static -> bold keycap tokens in the rendered modal (CDR-3)"
    - "LNC_EXIT_CONFIRM_YES/NO _t registrations <-> QuitConfirmModal y/n Binding descriptions (show=True) <-> modal Footer keycaps <-> EXPECTED_LNC_CONSTANTS closed inventory (CDR-3/CDR-5)"
    - "APP_CTRLC_LABEL amended value <-> ('ctrl+c', APP_CTRLC_LABEL) help row in _binding_rows <-> the four help-row pin tests (auto-amending via the constant) (CDR-1/CDR-2)"
---

<objective>
The maintainer's 2026-10-17 08:54 revision batch over last night's v0z/vxr exit keys (按照这个方案修订): (1) withdraw the uppercase-Q interception — Q returns to being a plain typable letter; (2) ctrl+c becomes the any-focus primary exit, routed through the v0z confirmation chain and overriding Textual 8.2.8's notify-only help_quit default; (3) make QuitConfirmModal's Y/N prompts prominent — bold [Y]/[N] tokens plus visible y/n Footer keycaps; (4) close the P9 modal-stacking defect with an action_quit early-return guard when an exit-family modal is already top.

Purpose: the operator gets a quit key that works from any focus WITHOUT sacrificing a typing letter (Q抢输入冲突 solved), a confirm dialog whose answer keys are visible at a glance (弹框没有显眼的Y/N提示 solved), and no way to stack exit modals over exit modals.
Output: rewritten on_event intercept (Q -> ctrl+c), P9 guard in action_quit, bolded QuitConfirmModal with Footer keycaps, APP_Q_LABEL retired / APP_CTRLC_LABEL amended / two new LNC keycap constants, RED-first test suite, full gates at the exact 7F baseline with zero golden interaction.
</objective>

<required_reading>
/home/forrest/Github/dnallmmark/.planning/STATE.md
/home/forrest/Github/dnallmmark/.planning/quick/261017-cdr-exit-keys-revision-ctrl-c-any-focus-quit/PLANNER-CONTRIBUTIONS.md
/home/forrest/Github/dnallmmark/.planning/quick/261016-vxr-slot-5-monitor-batch-eta-remaining-time-/261016-vxr-SUMMARY.md
/home/forrest/Github/dnallmmark/.planning/quick/261016-v0z-guard-ctrl-q-exit-route-the-inherited-te/261016-v0z-SUMMARY.md
/home/forrest/Github/dnallmmark/tui/app.py
/home/forrest/Github/dnallmmark/tui/strings.py
/home/forrest/Github/dnallmmark/tests/tui/test_pilot_run_config.py
</required_reading>

<context>
All line numbers below are live at planning time (HEAD = 88f4642, post-vxr). Re-read each site before editing and re-anchor if drifted.

## The four seams being revised (live coordinates)

- `tui/app.py:1042-1080` — `DnallmMarkTui.on_event`, the vxr Q intercept (routes Q -> action_quit, consumes without super). REWRITTEN in place: key 'Q' -> 'ctrl+c', docstring replaced (CDR-1/CDR-2).
- `tui/app.py:986-1040` — `action_quit`, the v0z three-leg chain. GAINS the CDR-4 guard as its first statement.
- `tui/app.py:226-274` — `QuitConfirmModal` (v0z): bindings y/n show=False, `Static(self._message)` at :254, docstring :227-239 carries the stale "q/ctrl+q inert under the modal" claim.
- `tui/app.py:1094-1123` — `_binding_rows`: manual rows ctrl+q (:1114), ctrl+c (:1115), Q (:1119 — DELETED).
- `tui/strings.py:159-175` — APP_ chrome block: the ctrl+c audit comment (:159-161), `APP_CTRLQ_LABEL` (:162-163), `APP_CTRLC_LABEL` (:164-165, value amended), `APP_Q_LABEL` (:166-175 block, DELETED).
- `tui/strings.py:1567-1569` — `LNC_EXIT_CONFIRM`; the two new keycap constants land beside it in the LNC_ block.

## CDR-2 seam decision — on_event intercept, NOT a declared priority binding (the load-bearing planning decision)

The maintainer left the seam to planning with the P9 caveat. Decision: **the on_event intercept**, mirroring the proven Q shape (P10-P14). Grounding:

- A declared `Binding("ctrl+c", "quit", priority=True)` (the ctrl+q shape) WOULD deliver any-focus reach — ctrl combos are never consumed by `Input.check_consume_key` (vxr P3/P8) — but the priority path walks the FULL `_binding_chain`, so it also fires under EVERY open modal (P9 mechanism): ctrl+c inside the wizard, the E2' phrase modal, or a picker would push an exit modal over it. That is the P9-class stacking the maintainer flagged.
- The on_event intercept with the `not self.screen.is_modal` guard delivers the SAME base-screen any-focus reach (it sees the Key event before any Input/binding machinery — vxr P10) with base-screen-only semantics: inert under every modal (P12 analog). This is precisely "撤 Q 后的 any-focus 主退出" scoped to base screens, where the filter-input focus trap lives.
- Under modals the key delegates to `super().on_event` -> the modal-cut binding chain. The inherited textual 8.2.8 default `Binding("ctrl+c", "help_quit", show=False, system=True)` is **non-priority** (verified at `.venv/lib/python3.13/site-packages/textual/app.py:463`), so it is chain-cut under modals -> inert, no notify. On base screens the intercept consumes the key before the machinery, so help_quit never fires anywhere. Consequence: DO NOT declare a replacement ctrl+c Binding — a non-priority one could never fire (intercept shadows base screens, modal chain blocks modals) and would be dead code; the on_event docstring documents the shadowing instead (the honest form of the v0z drift-proofing rationale).
- Below-min-grid consistency: MinSizeScreen is a plain Screen (non-modal), so the intercept routes to action_quit, whose leg 1 returns — same behavior as q today. No special case needed.
- The RED suite IS the dispatch probe: the ctrl+c-over-focused-Input tests prove end-to-end that App.on_event sees the ctrl+c Key event first. If those tests fail at GREEN, re-run a throwaway vxr-style Pilot probe on ctrl+c dispatch order BEFORE touching the seam — do not silently switch to a priority binding (that reintroduces the P9 stacking the maintainer ruled against).
- zellij: the maintainer asserts default zellij passes ctrl+c through to the pane program — no action; note it in the docstring/SUMMARY only.

Probe facts on record (reusable, from v0z/vxr — do NOT re-probe): P1 printable priority bindings do not fire over focused Input; P3/P8 ctrl-combos do fire over focused Input; P9 priority bindings fire over open modals; P10-P14 on_event interception delivers base-screen-only semantics with Input-focus coverage and consumption. Rich markup square brackets in Static str content render VERBATIM — styling goes through the Text API, never markup strings.

## CDR-4 guard coverage — exactly (ExitModal, QuitConfirmModal), justified

The guard prevents DUPLICATE pushes of the same exit surface (the P9 defect: priority ctrl+q re-entering action_quit while its own modal is top). Out of the set, deliberately:

- `KillConfirmModal` (monitor.py:536): kill != exit (the vxr VXR-2 distinct-acts ruling). A quit issued while a kill confirm is open is a NEW legitimate intent — the ExitModal/QuitConfirmModal stacks over it, esc peels back to the kill confirm, and its y-only confirm still guards the kill. Guarding it would erase the act distinction.
- `E2PhraseModal` and every launch-side/selection modal: not exit surfaces; same reasoning (the E2' typed-phrase gate is a launch escalation, not an exit).
- Note: after CDR-2 lands, ctrl+c can never reach action_quit under ANY modal (intercept guard), so the guard's only live trigger is ctrl+q under an exit-family modal — still required, because ctrl+q stays a priority binding.

## CDR-3 styling mechanics — Text API, not markup

- `rich.text.Text.highlight_words` is verified present in the installed rich (`.venv .../rich/text.py:633`): build `Text(message)` then `highlight_words(("[Y]", "[N]"), style="bold")`, pass the Text object to Static. Text content is never markup-parsed (the HelpModal literal-keycap precedent, app.py:130-136), so the bracket tokens stay literal and no `[b]...[/b]` escaping games are needed. `bold` is a Rich core style — the 09-03/09-06 MissingStyle hazard applies only to $token spans.
- The `_plain` helper (tests/tui/test_pilot_run_config.py:499) reads `.plain` for Text content, so the existing `LNC_EXIT_CONFIRM in message` assertion (:1520) survives the str->Text switch unchanged.
- Registry safety for the new values: ("退出","Quit") already exists as an identical pair (APP_QUIT_LABEL, LNC_EXIT_TITLE) and ("取消","Cancel") as (WIZ_CANCEL_LABEL, DL_CANCEL_LABEL) — identical pairs are registry-legal (the WIZ_BACK precedent); the same-zh<->same-en bidirectional injectivity tripwires (tests/tui/test_strings_phase11.py:240-280) stay green. Use these EXACT value pairs.

## Discipline constraints (hard)

- tui/app.py carries a zero-Chinese-literals lock (tests/tui/test_pilot_env_check.py:819) — the rewritten on_event/action_quit/QuitConfirmModal docstrings stay English-only (the vxr 方案 deviation lesson).
- The priority-typing-binding grep lock (tests/tui/test_pilot_nav_shell.py, `test_no_priority_typing_key_binding_exists_anywhere`) flags any line with `priority=True` plus a modifier-less Binding key — this batch adds NO Binding entries at all; keep the literal `priority=True` out of new docstring lines entirely.
- Fix discipline: surgical edits only at the named seams; no refactor of action_quit's legs, ExitModal, KillConfirmModal, or nav bars. Non-goals (deliberate): KillConfirmModal does NOT get the bold/keycap treatment (the ruling names QuitConfirmModal only); ctrl+q over NON-exit modals keeps stacking (pre-existing v0z behavior, outside this ruling); APP_QUIT_LABEL stays byte-identical (golden-pinned bottom bars).
- Golden state NOW: `tests/tui/__snapshots__/` carries THREE uncommitted D-03-pending SVGs (monitor_empty, monitor_running, run_config). Record their sha256 at Task 1 start; they must be byte-identical at the gates. This batch is designed for ZERO golden interaction: the Q help row lives only in the help modal (not golden-pinned), ctrl+c changes no base-screen bar (no new Binding, the manual help row only), and no golden renders QuitConfirmModal (test_snapshots pins base screens + the wizard — verify by reading tests/tui/test_snapshots.py if any snapshot fails).

<assumption_delta_decision>
Advisory checkpoint (contribution fragment: assumption-delta). Signal: the reserved any-focus exit key transitions Q -> ctrl+c. Decision: **promote-and-replace** — ctrl+c takes over the on_event seam, the help row, and the any-focus label wording, and Q is FULLY withdrawn (intercept, row, constant, tests). Keeping Q alongside ctrl+c would recreate the typing sacrifice the maintainer rejected (two reserved keys, one of them a printable letter). The P9 guard introduces a coverage set of two modal types over the EXISTING exit-modal family — not a pluralization of a primary key; no identity-model change. Suggested invariant test (accepted, lands as the stack-depth pins in Task 1): "no key combination can push a second exit-family modal while one is top."
</assumption_delta_decision>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: RED — the 261017-cdr test suite (rewrite the Q legs, add the ctrl+c/P9/prominence pins)</name>
  <files>tests/tui/test_pilot_run_config.py, tests/tui/test_pilot_env_check.py, tests/tui/test_pilot_nav_shell.py, tests/tui/test_pilot_selection.py, tests/tui/test_pilot_monitor.py, tests/tui/test_strings_phase11.py, .planning/quick/261017-cdr-exit-keys-revision-ctrl-c-any-focus-quit/RED-EVIDENCE.json</files>
  <behavior>
    New/rewritten contract tests in tests/tui/test_pilot_run_config.py (the app-level exit-test home; reuse `_app`, `FakeLauncherService`, `_open_run_config`, `_plain`):
    - CDR-2 primary leg (NEW `test_ctrlc_no_sweep_opens_quit_confirm_over_focused_input`): base screen, `#cfg-input-seeds` focused, press ctrl+c -> QuitConfirmModal is top, `not app._exit`, input value unchanged (never typed), then y -> `app._exit` (the quit the ctrl+c opened confirms).
    - CDR-2 live-sweep leg (REWRITE of `test_q_uppercase_live_sweep_routes_to_exit_modal` -> `test_ctrlc_live_sweep_routes_to_exit_modal_over_focused_input`): FakeLauncherService(live=...) + focused Input + ctrl+c -> ExitModal top, value unchanged, no exit.
    - CDR-1 plain-letter restoration (REWRITE of `test_q_uppercase_quits_from_focused_input_never_types` -> `test_q_uppercase_is_a_plain_typing_letter_again`): focused seeds Input, press Q -> value == "Q" (the select_on_focus replace-typing semantics documented in the existing lowercase-q test), screen still RunConfigScreen, no modal anywhere in the stack, `not app._exit`.
    - CDR-2 modal inertness (REWRITE of `test_q_uppercase_inert_under_modals_types_in_modal_inputs` -> `test_ctrlc_inert_under_modals_never_stacks`): (a) under QuitConfirmModal (q, no sweep) press ctrl+c -> exactly ONE QuitConfirmModal in the stack, no exit; (b) with a live sweep, under ExitModal press ctrl+c -> exactly ONE ExitModal, no exit; (c) under PathInputModal (Input-bearing) press ctrl+c -> no exit-family modal pushed, no exit, input value unchanged; (d) in the same PathInputModal leg press Q -> value == "Q" (a capital Q stays typeable in modal Inputs — the E2' phrase rationale, now true by default and pinned).
    - CDR-4 P9 guard (NEW `test_ctrlq_under_exit_modal_never_stacks_second`): live sweep, q -> ExitModal, press ctrl+q -> still exactly one ExitModal in the stack, `not app._exit`; then (fresh app, no sweep) q -> QuitConfirmModal, press ctrl+q -> still exactly one QuitConfirmModal, no exit.
    - CDR-2 below-grid leg (REWRITE of `test_q_uppercase_below_min_grid_never_exits` -> `test_ctrlc_below_min_grid_never_exits`): resize to (60,20), ctrl+c -> no exit, no ExitModal anywhere, MinSizeScreen stays top (regression pin — passes before AND after).
    - CDR-3 Footer keycaps (NEW `test_quit_confirm_footer_shows_y_n_keycaps`): open QuitConfirmModal (q, no sweep); assert the class BINDINGS carry a y entry and an n entry with show=True whose descriptions resolve to the live-language `LNC_EXIT_CONFIRM_YES` / `LNC_EXIT_CONFIRM_NO`, the enter binding stays show=False, and the modal composes a Footer.
    - CDR-3 bold tokens (NEW `test_quit_confirm_message_bolds_y_n_tokens`): open QuitConfirmModal; the message Static's content is a rich Text; its `.plain` contains LNC_EXIT_CONFIRM; every "[Y]" and "[N]" occurrence in `.plain` is covered by at least one span with style "bold" (locate offsets via `.plain.index`).
    - KEEP byte-untouched: `test_q_lowercase_still_types_into_inputs`, every v0z test except the ctrl+c audit pin, and all ExitModal triple tests (enter-detach/k-kill/esc/multi-root).
    - REWRITE the v0z audit pin `test_ctrlc_never_exits_or_opens_modal` (:1657-1675) into the live-sweep leg above (delete the old test; its no-screen/no-exit assertions are now false) — its no-sweep truth survives inside the new primary-leg test.
    Help-row pins (4 files): drop the `APP_HELP_ROW.format(key="Q", label=APP_Q_LABEL)` row from the expected lists and the `APP_Q_LABEL` imports; update the adjacent comments to the 261017-cdr map (q, ?, L, ctrl+q, ctrl+c — Q retired, ctrl+c now the any-focus exit). Sites: tests/tui/test_pilot_env_check.py:865-884, tests/tui/test_pilot_nav_shell.py:670-689, tests/tui/test_pilot_selection.py:1203-1222, tests/tui/test_pilot_monitor.py:2542-2556.
    Inventory (tests/tui/test_strings_phase11.py): EXPECTED_LNC_CONSTANTS gains "LNC_EXIT_CONFIRM_YES", "LNC_EXIT_CONFIRM_NO" beside "LNC_EXIT_CONFIRM" (:82).
  </behavior>
  <action>First record the golden baseline: sha256sum of tests/tui/__snapshots__/monitor_empty.svg, monitor_running.svg, run_config.svg into RED-EVIDENCE.json. Then author the suite above (RED against current HEAD). Run the touched lanes and record the exact planned split in RED-EVIDENCE.json (expected RED: the two ctrl+c chain legs, the Q-plain-letter inversion, the P9 stack pins, the keycap/bold pins, the inventory pair, and the four help-row pins via row mismatch; expected GREEN regression pins: the below-grid leg, the modal-inertness legs under modals where ctrl+c is already inert today, and every untouched exit test). Commit RED: `test(261017-cdr): RED — ctrl+c any-focus exit, Q restored, P9 guard, confirm keycaps` (PLAIN, no trailers) including RED-EVIDENCE.json.</action>
  <verify>
    <automated>uv run pytest tests/tui/test_pilot_run_config.py tests/tui/test_strings_phase11.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_nav_shell.py tests/tui/test_pilot_selection.py tests/tui/test_pilot_monitor.py -q 2>&1 | tail -5</automated>
  </verify>
  <done>The RED commit is at HEAD with RED-EVIDENCE.json recording the exact fail/pass split and the three golden sha256s; every new/rewritten contract test fails for the planned reason (behavior absent) and every designated regression pin passes.</done>
</task>

<task type="auto">
  <name>Task 2: GREEN — the four amendments in tui/app.py + tui/strings.py</name>
  <files>tui/app.py, tui/strings.py</files>
  <action>
    tui/app.py (re-read each site first; re-anchor on drift):
    1. on_event (:1042-1080): change the matched key 'Q' -> 'ctrl+c'; REWRITE the docstring per the CDR-2 seam decision (261017-cdr: ctrl+c the any-focus primary exit through the v0z confirm chain; why on_event and not a declared priority binding — the P9 full-chain walk would stack exit modals over non-exit modals; the intercept delivers base-screen-only semantics with the same reach; the inherited help_quit default is non-priority so the modal-cut chain leaves ctrl+c inert under modals — no notify anywhere; below-min-grid routes into action_quit leg 1 like q; zellij passes ctrl+c through by default). English-only docstring; no `priority=True` literal; keep the consume-without-super shape.
    2. action_quit (:986): insert the CDR-4 guard as the FIRST statement — when the top screen is an ExitModal or QuitConfirmModal instance, return immediately (comment: the P9/vxr finding — priority ctrl+q fires over open modals and re-entered here; KillConfirmModal/E2PhraseModal deliberately unguarded: quit over them is new legitimate intent). Add one docstring sentence for the guard leg (0).
    3. QuitConfirmModal (:226-274): bindings — y gains show=True + description S.LNC_EXIT_CONFIRM_YES, n gains show=True + description S.LNC_EXIT_CONFIRM_NO (enter stays show=False, escape unchanged); compose — build Text(self._message).highlight_words(("[Y]", "[N]"), style="bold") and yield Static over it; docstring — correct the stale q/ctrl+q inertness claim (plain q chain-cut per Pitfall 11; ctrl+q fires but the action_quit guard closes it) and note the Y/N prominence (bold spans via the Text API because markup strings cannot carry the literal brackets safely; visible y/n Footer keycaps).
    4. _binding_rows (:1094-1123): delete the Q row append (:1116-1119); update the block comment (ctrl+c row now the any-focus exit per 261017-cdr; Q row retired with the intercept).
    5. Module docstring (:18-24): amend the app-level bindings paragraph — 261017-cdr: ctrl+c exits from any base-screen focus through the confirm chain (Q restored to a plain letter).
    tui/strings.py:
    6. Delete APP_Q_LABEL and its comment block (:166-175); amend APP_CTRLC_LABEL (:164-165) to _t("APP_CTRLC_LABEL", "退出（任意焦点生效）", "Quit (works at any focus)") — the retired APP_Q_LABEL wording verbatim — and rewrite the block comment (:159-173): ctrl+c is now the any-focus primary exit (on_event intercept, confirm chain), the notify-only audit retired; APP_Q_LABEL withdrawn with the vxr intercept.
    7. Add beside LNC_EXIT_CONFIRM (:1567-1569): LNC_EXIT_CONFIRM_YES = _t(..., "退出", "Quit") and LNC_EXIT_CONFIRM_NO = _t(..., "取消", "Cancel") with a comment (the QuitConfirmModal Footer keycaps, mirroring the message's [Y]/[N] words; identical registry pairs already exist — injectivity-safe).
    Then run the touched lanes to green (only the RED tests flip; if a ctrl+c-over-Input test still fails, probe ctrl+c dispatch order per the context section BEFORE considering any seam change). Then the quick static lanes: make lint + make typecheck. Commit GREEN: `feat(261017-cdr): ctrl+c any-focus exit via on_event, P9 guard, prominent Y/N confirm` (PLAIN).
  </action>
  <verify>
    <automated>make lint && make typecheck && uv run pytest tests/tui/test_pilot_run_config.py tests/tui/test_strings_phase11.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_nav_shell.py tests/tui/test_pilot_selection.py tests/tui/test_pilot_monitor.py -q 2>&1 | tail -3</automated>
  </verify>
  <done>The six touched test lanes are fully green (zero failures in them), ruff and ty pass, and the GREEN commit is at HEAD.</done>
</task>

<task type="auto">
  <name>Task 3: Full gates, golden-integrity proof, SUMMARY + STATE row</name>
  <files>.planning/quick/261017-cdr-exit-keys-revision-ctrl-c-any-focus-quit/261017-cdr-SUMMARY.md, .planning/STATE.md</files>
  <action>
    Full gates (read the actual numbers; the 7F MEMBERSHIP is the invariant): full pytest suite exactly 7 failed / all others passed with the known membership (test_determinism 1, test_schemas 5, test_services_run_config 1) and zero new failures; node lane 26/26; `uv run pytest tests/tui/test_snapshots.py -q` -> 11/11 against the on-disk SVGs. Golden integrity: re-run sha256sum on the three D-03 SVGs and compare to the Task-1 record (must be byte-identical); `git status --porcelain tests/tui/__snapshots__/` shows EXACTLY the three pre-existing M entries. make snapshot-update is NEVER run — if any snapshot test fails, STOP, leave the tree clean of regeneration, and report the D-03 path in the SUMMARY (the ruling's stop condition). Write 261017-cdr-SUMMARY.md (frontmatter per the vxr SUMMARY shape: file:line landings for all four amendments, the seam-decision rationale, the guard-coverage justification, RED evidence summary, gate numbers, golden-integrity proof, deviations, threat dispositions; note the golden non-interaction argument: Q row help-modal-only, ctrl+c touches no base-screen bar, no golden renders QuitConfirmModal). Append the Quick Tasks Completed row in .planning/STATE.md. Commit docs: `docs(261017-cdr): quick-task summary + STATE row` (PLAIN). Do NOT push.
  </action>
  <verify>
    <automated>uv run pytest tests/ -q 2>&1 | tail -3 && uv run pytest tests/tui/test_snapshots.py -q 2>&1 | tail -2 && git status --porcelain tests/tui/__snapshots__/ && git log --oneline -3</automated>
  </verify>
  <done>Full suite at exactly the 7F baseline membership with zero new failures; node 26/26; snapshots 11/11; the three D-03 SVGs byte-preserved (sha256 match); three PLAIN commits (RED, GREEN, docs) at HEAD, nothing pushed; SUMMARY and STATE row committed.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| terminal -> App.on_event | raw key events cross into the intercept that can consume them |
| static registry copy -> rendered modal | strings.py constants flow into the bold-span rendering path |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-261017cdr-01 | Tampering | DnallmMarkTui.on_event (app.py) | medium | mitigate | The intercept matches ONLY events.Key with key exactly 'ctrl+c' under a mounted non-modal screen; every other event delegates to super() unchanged — no broad event swallowing (a wider match would break Input typing and screen bindings); the shape is the vxr-proven seam with the key string swapped. |
| T-261017cdr-02 | DoS | action_quit guard (app.py) | low | mitigate | The guard only short-circuits DUPLICATE exit-surface pushes; every actual exit still requires the explicit y confirm (EHC-2) or the ExitModal triple — pinned by the stack-depth and no-exit tests. |
| T-261017cdr-03 | Tampering | QuitConfirmModal bold rendering (app.py) | low | mitigate | Styling via the Rich Text API over the static LNC_EXIT_CONFIRM registry constant — Text content is never markup-parsed, so no bracket-injection surface exists; no operator-influenced string enters the styling path. |
| T-261017cdr-04 | Repudiation | exit-key semantics (help rows) | low | accept | The help modal's ctrl+c row is resolved live from the amended constant and pinned by four help-row tests; operator confusion risk is bounded by the visible confirm chain itself. |
| T-261017cdr-SC | Tampering | package installs | high | mitigate | Zero package installs — tui/ + tests/ only, zero dependency/lockfile changes; no [ASSUMED]/[SUS] packages introduced. |
</threat_model>

<verification>
- make lint (ruff) and make typecheck (ty) green.
- Full pytest at EXACTLY the 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1), zero new failures, every 261017-cdr test passing.
- Node lane 26/26.
- tests/tui/test_snapshots.py 11/11 against the on-disk SVGs; the three uncommitted D-03 SVGs byte-identical to the Task-1 sha256 record; zero other worktree changes under tests/tui/__snapshots__/.
- Manual sanity (optional, no commit): `uv run python -m tui` on a base screen — ctrl+c opens the Y/N confirm with bold [Y]/[N] and visible y/n footer keycaps; a capital Q types into the selection filter; ctrl+q inside the open confirm does nothing.
</verification>

<success_criteria>
- CDR-1: no Q-specific code, label, help row, or test obligation remains; Q types as a plain letter (pinned).
- CDR-2: ctrl+c reaches the v0z confirm chain from any base-screen focus including focused Inputs, is inert under every modal, and never triggers the help_quit notify; the help row carries the new semantics.
- CDR-3: QuitConfirmModal renders bold [Y]/[N] tokens and y/n Footer keycaps in both languages (L toggle re-derives them).
- CDR-4: no key combination can push a second exit-family modal while one is top (stack-depth pinned for ctrl+q under both exit modals).
- CDR-5: all gates green at the exact 7F membership; goldens untouched; three PLAIN commits, nothing pushed.
</success_criteria>

<output>
Create `.planning/quick/261017-cdr-exit-keys-revision-ctrl-c-any-focus-quit/261017-cdr-SUMMARY.md` when done
</output>
