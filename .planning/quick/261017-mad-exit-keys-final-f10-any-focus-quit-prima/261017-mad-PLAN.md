---
phase: quick-261017-mad
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/app.py
  - tui/strings.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_monitor.py
  - .planning/STATE.md
  - .planning/quick/261017-mad-exit-keys-final-f10-any-focus-quit-prima/261017-mad-SUMMARY.md
autonomous: true
requirements: [MAD-1, MAD-2, MAD-3, MAD-4]

user_setup: []

estimate:
  tokens: 48000
  raw_tokens: 24000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "MAD-1 (F10 any-focus exit): a DECLARED app-level priority binding f10 -> quit routes through the existing v0z confirm chain from ANY base-screen focus — including a focused Input with or without a selection (planning-time probe on the locked textual 8.2.8: the priority check runs on the App BEFORE the focused-widget forward, and non-printable f10 passes the consume-key filter that strips printable priority bindings) and over open modals (the ctrl+q P9 mechanism). No live sweep -> QuitConfirmModal (y-only, enter inert); live sweep -> ExitModal; below the min grid -> nothing (WR-06). No path exits on F10 alone; under an exit-family modal top the CDR-4 guard in action_quit returns immediately (exactly one exit modal, never a stack). Binding flags: show=False (every Footer/bottom bar byte-unchanged — golden discipline), priority=True, system=True (the ctrl+q mirror precedent), NO description (the help row is manual and live-language-resolved)."
    - "MAD-2 (ctrl+c withdrawal): the cdr on_event ctrl+c intercept AND the klw WR-01 Input-selection delegation branch are deleted TOGETHER with the whole on_event override (the delegation existed only to rescue the copy binding the intercept ambushed); ctrl+c returns to textual 8.2.8's native semantics everywhere — a selection-holding focused Input copies through the Input's OWN ctrl+c,super+c -> copy binding (probed: clipboard receives the selection, zero app code involved); every other base-screen press hits the inherited notify-only help_quit default (probe-pinned: the notify text names ctrl+q, no modal, no exit — accepted as harmless per the maintainer ruling); under modals the non-priority default is chain-cut (inert). ctrl+c never opens any exit surface anywhere and never exits."
    - "MAD-3 (q / ctrl+q unchanged): plain q keeps its Input typing semantics and its chain-cut-under-modals behavior; the declared ctrl+q mirror binding (show=False, priority, system) and its behavior are byte-unchanged; the capital-Q plain-letter state is untouched. Every existing q/ctrl+q/ExitModal/QuitConfirmModal test stays green unmodified."
    - "MAD-4 (help modal sync, bilingual): _binding_rows lists the manual F10 row FIRST among the manual exit rows as ('f10', APP_F10_LABEL) — zh 退出（任意焦点） / en Quit (any focus), registered through _t beside the APP_CTRLQ/APP_CTRLC block (single-home, injectivity-safe unique pair); APP_CTRLC_LABEL is REWORDED to the one-line anti-misreading explanation zh 终端复制/中断（非退出） / en Terminal copy/interrupt (not quit) — the row is KEPT per the ruling's stated preference, constant name and key string unchanged; APP_QUIT_LABEL and APP_CTRLQ_LABEL values stay BYTE-IDENTICAL (APP_QUIT_LABEL renders in every golden-pinned bottom bar — the 261016-v0z deviation discipline); the L toggle re-derives both manual rows (no description on the F10 binding, so remap skips it by design — the ctrl+q idiom)."
    - "GATES: make lint and make typecheck green; make test at EXACTLY the pre-task baseline membership — 1 failed (tests/tui/test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers, machine-local pipeline/logs state) / 1867 passed before this task's new tests, every NEW test green, zero new failures (read the actual counts at execution time; the 1F MEMBERSHIP is the invariant); node lane 26/26 (inside make test); tests/tui/test_snapshots.py goldens green — on any unexpected golden red STOP and report the D-03 path, NEVER make snapshot-update; commits PLAIN (zero attribution trailers), executor does NOT push."
  artifacts:
    - tui/app.py
    - tui/strings.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_pilot_nav_shell.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_monitor.py
    - .planning/quick/261017-mad-exit-keys-final-f10-any-focus-quit-prima/261017-mad-SUMMARY.md
  key_links:
    - "F10 keystroke (any focus) -> App priority binding check (precedes the focused-widget forward) -> action_quit -> CDR-4 exit-family guard | WR-06 min-grid guard | ExitModal (live sweep) | QuitConfirmModal (y-only) — the v0z chain byte-unchanged (MAD-1)"
    - "F10 under exit-family modal -> priority fires (P9 full-chain walk) -> action_quit early-return -> exactly one exit modal (MAD-1)"
    - "selection-holding focused Input + ctrl+c (NO app seam) -> Input's own ctrl+c,super+c -> copy binding (_input.py:139) -> app.clipboard receives the selection (MAD-2)"
    - "bare ctrl+c elsewhere -> inherited App help_quit default (non-priority, system) -> notify only, never a modal, never an exit; chain-cut under modals (MAD-2)"
    - "_binding_rows -> ('f10', S.APP_F10_LABEL) manual row before ctrl+q -> HelpModal rows -> the three exact-list help-row pins (env_check / nav_shell / selection) (MAD-4)"
    - "L toggle -> set_language + remap_binding_descriptions (F10 has no description, skipped) -> help modal re-derives f10/ctrl+q/ctrl+c rows on next open (MAD-4)"
---

<objective>
The maintainer's 2026-10-17 16:02 exit-key final ruling (根据你建议来 — the F10 plan is accepted). Background: ctrl+c as the any-focus exit collides byte-level with the terminal copy family — an unscoped ctrl+shift+c passthrough is an indistinguishable 0x03, so with no terminal selection the copy gesture hit the cdr intercept's exit-confirm modal (maintainer reproduced it live); ctrl+q is dead under zellij and capital Q steals typing — the F-key family is the only one clean on all three sides.

Purpose: F10 becomes the any-focus primary exit through the existing guarded confirm chain; the ctrl+c interception is fully withdrawn so terminal-native copy/interrupt semantics hold with zero app-level ambushing; q/ctrl+q keep their unchanged roles; the help modal names all of it bilingually.
Output: one declared priority binding + manual help row in tui/app.py, the whole on_event override deleted from tui/app.py, two constants touched in tui/strings.py (one added, one reworded), the ctrl+c/exit test battery rewritten to F10-equivalents and deletion-semantics pins across five test files, full gates at the exact 1F/1867P baseline membership, plain commits, no push.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Planning-time probe evidence (locked textual 8.2.8 via uv run --group tui, 2026-10-17, throwaway scripts never committed — record verbatim in the SUMMARY):
- LEG1: an App priority Binding("f10", ..., priority=True) with a focused Input (select_on_focus active selection) — pressing f10 FIRED the action. Non-printable priority bindings pass the consume-key filter that strips printable priority bindings over focused Inputs. THE DECLARATIVE SEAM IS CONFIRMED; the on_event fallback is not needed.
- LEG2: the same priority f10 fired over an open ModalScreen (the ctrl+q P9 mechanism — expected; the CDR-4 guard owns exit-family stacking).
- LEG3: bare f10 with no app binding is inert on a bare App (f10 is not a textual framework default; nothing to shadow).
- POST-DELETION ctrl+c (no app on_event override): a selection-holding focused Input copies natively (clipboard receives the selection, no notify); an empty-selection Input or no Input focus fires the inherited help_quit notify naming ctrl+q (no modal, no exit); a modal top chain-cuts it (inert).

Live source anchors (verified at planning time on HEAD c1f2567 — re-locate by the quoted code, line numbers drift):
- tui/app.py:76 — from textual.widgets import Footer, Input, Static (Input drops out with the override)
- tui/app.py:117-147 — HelpModal (rows arrive pre-built; unaffected)
- tui/app.py:275-347 — QuitConfirmModal (docstring carries the ctrl+c inertness-map paragraph to update; bindings/actions untouched)
- tui/app.py:546-568 — DnallmMarkTui.BINDINGS (q / ctrl+q mirror / ? / L — the F10 entry lands after the ctrl+q mirror)
- tui/app.py:1072-1152 — action_quit (the guarded chain + CDR-4 early return + WR-06 leg — REUSED byte-unchanged; only the docstring's any-focus-trigger sentence updates)
- tui/app.py:1154-1212 — the on_event override to DELETE in full (cdr ctrl+c intercept + klw WR-01 delegation + the vxr-era structural residue — one method)
- tui/app.py:1275-1302 — _binding_rows (the manual ctrl+q/ctrl+c rows; the F10 row inserts before ctrl+q)
- tui/strings.py:145-170 — the APP_QUIT/CTRLQ/CTRLC block (APP_QUIT_LABEL golden-frozen byte-identical; APP_F10_LABEL lands here; APP_CTRLC_LABEL reworded; note at :194 — no APP_ inventory tripwire exists, so no inventory churn beyond the unique new pair)
- tests/tui/test_pilot_run_config.py:240-312 — FakeLauncherService (live knob reused); :1933-2010 — the klw WR-01 copy/delegation test; :2138-2400 — the cdr CDR-1/2 exit battery (Q-plain-letter, ctrl+c series, ctrl+q stacking, min-grid, y/n keycaps)
- tests/tui/test_pilot_env_check.py:905-925, tests/tui/test_pilot_nav_shell.py:663-690, tests/tui/test_pilot_selection.py:1195-1225 — the three exact-list help-row pins
- tests/tui/test_pilot_monitor.py:2629-2654 — the monitor help test (comment-only touch; its no-[Q]-row assertion stays true)
- tests/tui/test_work_site_hardening.py — AST pin over @work sites; on_event is not a @work site, zero edits expected
- tests/tui/__snapshots__/*.svg — nine goldens; the help modal is not among them; bottom bars render only described bindings (F10 carries none) — goldens stay green
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: F10 declarative any-focus exit — priority binding, manual help row, RED-first F10 battery</name>
  <files>tui/app.py, tui/strings.py, tests/tui/test_pilot_run_config.py, tests/tui/test_pilot_env_check.py, tests/tui/test_pilot_nav_shell.py, tests/tui/test_pilot_selection.py</files>
  <behavior>
    - RED 1 (the live seam re-probe): run-config screen mounted, the seeds Input focused with its auto-selection collapsed — press f10 — the QuitConfirmModal must be top, the Input value unchanged, no exit; then y confirms the exit. Against pre-task code this fails (f10 is inert today).
    - RED 2: same shape with FakeLauncherService(live=("/repo/finetuned",)) — f10 routes to the ExitModal; Input unchanged; no exit.
    - RED 3: f10 pressed while the QuitConfirmModal is top (opened via q) — exactly ONE quit confirm in the stack, never an exit; the ExitModal twin with a live sweep — exactly one, never an exit.
    - RED 4: terminal resized below 80x24 (guard top) — f10 exits nothing and opens nothing; the guard stays the top screen.
    - GREEN: all four pass once the priority binding lands; the three exact-list help-row pins pass with the F10 row present.
  </behavior>
  <action>
    Write the four RED tests into the exit battery section of tests/tui/test_pilot_run_config.py (reuse the local idioms: _app(), _open_run_config, FakeLauncherService; collapse the select_on_focus auto-selection with an end press before each f10 — mirror the WR-01 tests' selection-driving discipline; for RED 3 count modal instances over app.screen_stack; for RED 4 mirror the existing below-min-grid test's resize shape), run them, confirm each fails for the cited reason (f10 inert — no modal opens), THEN implement:

    1. tui/app.py BINDINGS — immediately after the ctrl+q mirror entry add the F10 entry: key f10, action quit, show=False, priority=True, system=True, no description. The comment records: the 2026-10-17 16:02 maintainer ruling (F10 = the any-focus primary exit; the F-key family is the only one clean against terminal copy passthrough, zellij, and typing); the probe evidence (priority f10 fires over a focused Input — non-printables pass the consume-key filter that strips printable priority bindings — and over open modals, the ctrl+q P9 mechanism); show=False keeps every Footer/bottom bar byte-unchanged (the golden discipline); system=True keeps the ctrl+p key panel clean (the ctrl+q precedent); no description because the help row is manual and therefore live-language-resolved (the ctrl+q idiom — remap skips description-less entries by design).

    2. tui/app.py _binding_rows — insert the manual F10 row as a (key, label) pair of the literal f10 and S.APP_F10_LABEL, placed BEFORE the ctrl+q manual row (F10 is the primary; q/ctrl+q are same-role alternates); update the section comment to name F10 as the any-focus primary since this task.

    3. tui/strings.py — beside the APP_CTRLQ_LABEL/APP_CTRLC_LABEL block: add APP_F10_LABEL = _t("APP_F10_LABEL", "退出（任意焦点）", "Quit (any focus)") and extend the block comment with the ruling sentence. Do NOT touch APP_QUIT_LABEL or APP_CTRLQ_LABEL values (APP_QUIT_LABEL renders in every golden-pinned bottom bar — the recorded 261016-v0z deviation keeps it byte-identical).

    4. The three exact-list help-row pins — insert the F10 row (key f10, label APP_F10_LABEL, same APP_HELP_ROW format) BETWEEN the L row and the ctrl+q row, extend each file's local from-import with APP_F10_LABEL, and update the surrounding comments (F10 = the any-focus primary per this task; positions: env_check ~:917-924, nav_shell ~:678-685, selection ~:1215-1222).

    If RED 1 does NOT go green after the binding lands (the priority-over-Input seam somehow absent in the execution environment), STOP and report — the fallback seam is an override keyed on f10 with the same non-modal-top guard shape the deleted ctrl+c one used; do not improvise.
  </action>
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_pilot_run_config.py tests/tui/test_pilot_env_check.py tests/tui/test_pilot_nav_shell.py tests/tui/test_pilot_selection.py -q && make lint && make typecheck</automated>
  </verify>
  <done>The four new F10 tests green with RED evidence recorded; the three help-row pins green with the F10 row; every existing exit test (q/ctrl+q routing, the ctrl+c battery, ExitModal triple, quit-confirm keycaps) green UNMODIFIED — the intercept still lives until Task 2; ruff and ty green. Commit this task's code+tests as one PLAIN commit (no attribution trailers), no push.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: ctrl+c interception withdrawn — on_event deleted, terminal-native semantics restored, battery rewritten</name>
  <files>tui/app.py, tui/strings.py, tests/tui/test_pilot_run_config.py, tests/tui/test_pilot_monitor.py</files>
  <behavior>
    - RED 1 (native copy pin): run-config screen, the seeds Input focused, real text typed, a REAL selection driven by key presses (home then shift+end) — press ctrl+c — the app clipboard holds the selection, the base screen stays top, no quit surface anywhere in the stack, no exit. Contrast leg (selection collapsed with an end press): ctrl+c opens NO exit surface and exits nothing (the inherited notify-only default is accepted and not pinned).
    - RED 2 (the ambush scenario pin): base screen with NO Input focus — press ctrl+c — no modal anywhere in the stack, no exit (an unscoped terminal ctrl+shift+c passthrough lands here as a harmless notify, never the exit confirm).
    - RED 3 (modal semantics): under the QuitConfirmModal ctrl+c keeps exactly one modal and never exits (natively chain-cut now); under an Input-bearing modal (PathInputModal) ctrl+c pushes no exit surface and never types; f10 there stacks the QuitConfirmModal OVER the PathInputModal (new legitimate intent — the ctrl+q family semantics) and esc peels back to the PathInputModal; the ExitModal twin (live sweep) — ctrl+c exactly one, never exits; a capital Q still types inside the modal Input.
    - RED 4 (min grid): below 80x24 both f10 and ctrl+c exit nothing and open nothing; the guard stays top.
  </behavior>
  <action>
    Write the rewrites into tests/tui/test_pilot_run_config.py first (the current intercept makes RED 1's contrast leg, RED 2, and RED 3's inertness legs fail today — record the RED evidence), THEN withdraw the interception:

    1. Delete the ENTIRE event-handler override in tui/app.py (the async method spanning ~:1154-1212 — the cdr ctrl+c intercept AND the klw WR-01 Input-selection delegation branch ride out together; the delegation existed only to rescue the copy binding the intercept was ambushing). Remove Input from the widgets import at :76 (the only remaining consumer was that branch; ruff flags the unused import otherwise). The events import stays (the resize handler still uses it). Every other event path reverts to the inherited base-class behavior — identical for all non-ctrl+c events.

    2. Update the five prose sites that document the intercept, semantics untouched elsewhere: the module docstring's binding paragraph (~:18-28 — F10 is the any-focus exit per this task; ctrl+c returns to textual's terminal-native default), the BINDINGS comment block (~:538-545 — drop the ctrl+c revision sentence, name F10), action_quit's docstring head (~:1072-1076 — F10 is the any-focus trigger; q/ctrl+q unchanged), QuitConfirmModal's inertness-map paragraph (~:282-288 — ctrl+c under the modal is natively chain-cut like every non-priority app binding; f10/ctrl+q fire through the priority chain and hit the stacking guard), and the _binding_rows comment.

    3. tui/strings.py — reword APP_CTRLC_LABEL (zh 终端复制/中断（非退出）, en Terminal copy/interrupt (not quit)) and rewrite its comment block (~:155-166): ctrl+c is no longer an exit key in this console; the row stays as the one-line anti-misreading note (the ruling's stated preference to keep one explanation line — planner decision recorded for the maintainer in the SUMMARY). Constant name and the literal ctrl+c key string stay (the three help-row pins import the constant and auto-derive).

    4. Test rewrites in tests/tui/test_pilot_run_config.py: rewrite the WR-01 copy test to the native-copy pin + collapsed-contrast (RED 1); add the no-focus ambush pin (RED 2); rewrite the modal-inertness test to the native semantics + the f10-over-PathInputModal stack-and-peel-back leg + keep the capital-Q-types leg (RED 3); rewrite the below-min-grid test to cover both keys (RED 4); DELETE the two ctrl+c routing tests whose F10 twins landed in Task 1 (the no-sweep confirm-over-Input one and the live-sweep ExitModal one); touch the Q-plain-letter test's docstring only (F10 took the any-focus role). The ctrl+q stacking test, the y/n keycap test, the q typing tests, and every ExitModal/kill-worker test stay byte-unchanged.

    5. tests/tui/test_pilot_monitor.py — comment-only touch in the monitor help test (~:2629-2654): the any-focus exit is F10 now; its assertions are already true.

    Structural proof to record: a grep for the delegation attribute over tui/app.py counts zero, and a grep for the modal-top guard flag over tui/app.py counts zero (both were single-site tokens of the deleted method).
  </action>
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_pilot_run_config.py tests/tui/test_pilot_monitor.py tests/tui/test_work_site_hardening.py -q && make lint && make typecheck</automated>
  </verify>
  <done>The whole rewritten battery green with RED evidence recorded; the F10 battery from Task 1 green; the work-site hardening pin green with zero edits; grep proof recorded (delegation attribute and modal-top guard flag both count zero over tui/app.py); ruff and ty green. Commit as one PLAIN commit, no push.</done>
</task>

<task type="auto">
  <name>Task 3: Full gates at the baseline membership + records</name>
  <files>.planning/STATE.md, .planning/quick/261017-mad-exit-keys-final-f10-any-focus-quit-prima/261017-mad-SUMMARY.md</files>
  <action>
    Run the full gate battery from the repo root and read the actual counts: make lint; make typecheck; make test (pytest must land at EXACTLY the 1F baseline membership — the sole failure is the machine-local storage-overview test, the passed count equals 1867 plus this task's new tests and nothing else; the node lane inside make test reads 26/26); the golden replay (the snapshots module) green — on any unexpected golden red STOP and report the D-03 path to the maintainer, regeneration is maintainer-only; confirm the strings diff is exactly the two-constant edit (one added, one reworded, plus comments) with APP_QUIT_LABEL and APP_CTRLQ_LABEL byte-identical.

    Then write the records: the SUMMARY carries (a) the probe evidence verbatim (the three F10 legs and the two post-deletion ctrl+c legs), (b) the RED evidence for both tasks, (c) the planner decisions taken under the ruling's delegated discretion — the APP_CTRLC_LABEL row kept and reworded rather than removed, the F10 manual row placed first among the exit rows, APP_QUIT_LABEL/APP_CTRLQ_LABEL left untouched (golden discipline), (d) the gate counts. Update .planning/STATE.md per the house pattern: the quick-task completed row and the decision-delta lines (F10 declarative seam probe-confirmed; ctrl+c interception withdrawn with native terminal semantics restored; help-modal-only string churn, goldens untouched). Commit the records as one PLAIN docs commit, no push.
  </action>
  <verify>
    <automated>make lint && make typecheck && make test && uv run --group dev --group tui pytest tests/tui/test_snapshots.py -q</automated>
  </verify>
  <done>All gates green at the exact baseline membership (sole machine-local failure unchanged, zero new failures, node 26/26, goldens green); SUMMARY and STATE.md updated and committed; nothing pushed.</done>
</task>

<non_goals>
- q and ctrl+q behavior, the ExitModal/QuitConfirmModal internals, the exit-kill worker, and the y/n keycap surfaces — byte-unchanged (MAD-3 regression pins only).
- No golden regeneration under any circumstance (the D-03 maintainer-only path; APP_QUIT_LABEL's bottom-bar freeze is the reason its value is untouched).
- No docs churn: docs/TUI-DEMO.md and the README carry no ctrl+c/F10 exit references (verified at planning time — the demo scenarios use q and k).
- No WizardModal changes (its keycap ruling stays with the maintainer), no i18n inventory edits beyond the two constants, no new services or dependencies, no pipeline changes, no E2'/GPU activity.
</non_goals>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| operator keystroke → app exit channel | f10/q/ctrl+q routing decides console exit and sweep kills; ctrl+c now crosses to the terminal-native layer |
| terminal passthrough (0x03) → app | unscoped terminal copy gestures deliver an indistinguishable ctrl+c byte into the app |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-mad-01 | Tampering | f10 priority binding reach (MAD-1) | medium | mitigate | The priority reach is confirm-gated end to end: the v0z chain (y-only confirm / ExitModal triple) is reused byte-unchanged, the CDR-4 guard blocks stacking under exit-family modals, and the WR-06 leg blocks everything below the min grid — no path exits on f10 alone. |
| T-mad-02 | Tampering | ctrl+c withdrawal (MAD-2) | low | mitigate | Removing the interception ELIMINATES the ambush surface (an unscoped terminal copy passthrough can no longer reach any exit surface); what remains is textual's notify-only default — pinned by the new no-exit-anywhere tests. |
| T-mad-03 | Tampering | native Input copy path (MAD-2) | low | accept | The copy-on-selection behavior is textual 8.2.8's own widget binding with zero app seam — pinned by a test driving a selection; nothing app-level can divert it. |
| T-mad-SC | Tampering | package installs | n/a | accept | No package installs in this task — no supply-chain surface (pyproject/uv.lock untouched). |
</threat_model>

<verification>
Full gates from the repo root, in order:
1. `make lint` — ruff green (tui/ rides the wildcard lane; the widgets-import trim keeps it clean).
2. `make typecheck` — ty green (the deleted override removes code; the new binding adds none to check beyond the declaration).
3. `make test` — pytest at EXACTLY the 1F baseline membership (the sole failure is the machine-local storage-overview test; the passed count is 1867 + this task's new tests; zero new failures) and the node lane 26/26.
4. `uv run --group dev --group tui pytest tests/tui/test_snapshots.py -q` — goldens green; on any unexpected red STOP and report the D-03 path, never regenerate.
5. `git diff c1f2567 -- tui/strings.py` — exactly the APP_F10_LABEL addition + APP_CTRLC_LABEL reword + comments; APP_QUIT_LABEL/APP_CTRLQ_LABEL byte-identical; bottom bars unchanged (the F10 binding carries no description, so no bar renders it).
</verification>

<success_criteria>
- The declarative F10 seam landed exactly as probed (priority over focused Input confirmed live by the RED 1 test itself); the on_event fallback never needed.
- The interception withdrawal is total (the override deleted; both single-site guard tokens count zero over tui/app.py) and the native terminal semantics are pinned by tests.
- Both code tasks carry RED evidence in the SUMMARY; the planner-discretion decisions are recorded for the maintainer.
- Full gates at the exact baseline membership; goldens untouched; three PLAIN commits (two code, one records), zero attribution trailers, nothing pushed; STATE.md quick-task row + decision deltas written.
</success_criteria>

<output>
Create .planning/quick/261017-mad-exit-keys-final-f10-any-focus-quit-prima/261017-mad-SUMMARY.md when done; update .planning/STATE.md (quick-task row + decision-delta lines per the house pattern).
</output>
