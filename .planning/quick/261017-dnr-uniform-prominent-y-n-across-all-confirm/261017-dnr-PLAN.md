---
phase: quick-261017-dnr
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/strings.py
  - tui/screens/selection.py
  - tui/screens/monitor.py
  - tui/screens/run_config.py
  - tui/app.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_pilot_monitor.py
  - .planning/STATE.md
  - .planning/quick/261017-dnr-uniform-prominent-y-n-across-all-confirm/261017-dnr-SUMMARY.md
autonomous: true
requirements: [DNR-1, DNR-2, DNR-3, DNR-4, DNR-5, DNR-6]

user_setup: []

estimate:
  tokens: 42000
  raw_tokens: 22000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "DNR-1 (launch confirms prominent Y/N — gate + every LaunchConfirmModal): the slot-4 gate (_GateConfirmModal, run_config.py:834) and the shared base LaunchConfirmModal (selection.py:1223, which serves the monitor [f] re-run push at monitor.py:1310) render their message Static as a rich Text with a style='bold' span over every [Y]/[y]/[N]/[n] token (Text.highlight_words — in-place, returns int, NEVER chained, the cdr-probed rich seam); the y and n bindings carried by LaunchConfirmModal (selection.py:1240-1243) flip to show=True with descriptions S.LNC_GATE_CONFIRM_YES (new constant, zh 启动 / en Launch — no identical pair exists in the registry) and S.LNC_EXIT_CONFIRM_NO (reuse: its 取消/Cancel pair is exactly what n means); enter stays show=False (the EHC-2 inert no-op is never advertised — EHC-2 semantics byte-unchanged: y the ONLY key that launches, enter lands on the documented no-op, n/esc dismiss); the plain message values (LNC_GATE_CONFIRM, MON_RERUN_CONFIRM) are byte-unchanged so every existing _plain()/str() content assertion keeps passing; ConfirmModal itself and every non-launch consumer (preset overwrite selection.py:2236, queue cancels data_manager.py:1243, wizard cancel wizard.py:1495) are byte-untouched."
    - "DNR-2 (kill confirm prominent Y/N): KillConfirmModal (monitor.py:536) gets the same compose override (Text + bold tokens, id='confirm-box' and the message-Static-first layout preserved — on_mount queries #confirm-box for the border title and tests query the first Static) and its y/n bindings (monitor.py:549-553) flip to show=True with descriptions S.MON_KILL_KEYCAP (reuse: 停止/Kill is exactly what y does) and S.LNC_EXIT_CONFIRM_NO; MON_KILL_CONFIRM value byte-unchanged; y remains the ONLY key that stops a training (enter no-op, n/esc cancel — vxr semantics untouched)."
    - "DNR-3 (E2 y-ready bold copy): E2PhraseModal's matched indicator (run_config.py:730) updates to a rich Text of S.LNC_E2_MATCH_OK with bold spans over [Y]/[N] — the mismatch branch (733-734) stays a plain string; the y/n bindings (run_config.py:693-698) STAY show=False by design (they only arm after the matched-enter blur — a visible y keycap while the Input holds focus would advertise a key that types into the Input; the armed-state copy carries the affordance, per the 261017 brief's simplicity ruling); every existing _plain(indicator.content) == LNC_E2_MATCH_OK assertion keeps passing (.plain of the styled Text equals the constant)."
    - "DNR-4 (ExitModal affordances — scope addition): ExitModal's enter (detach_quit) and k (kill_quit) bindings (app.py:187-190) flip to show=True with new bilingual keycaps LNC_EXIT_DETACH_KEYCAP (zh 分离退出 / en detach & exit) and LNC_EXIT_KILL_KEYCAP (zh 终止后退出 / en kill & exit) — the three-key Footer (enter/k/esc) matches the copy that already names them; the message Static (app.py:206) becomes a rich Text with bold spans over the [enter]/[k]/[esc] tokens in BOTH LNC_EXIT_MESSAGE and LNC_EXIT_MESSAGE_MULTI renders; key/action semantics byte-unchanged (enter STILL detaches-and-exits as the Phase-11 default — visibility only, per the coordinator's keep-semantics ruling)."
    - "DNR-5 (full modal audit table — scope addition): the SUMMARY carries a per-modal audit table covering ALL 27 ModalScreen subclasses in tui/ (app.py 3, selection.py 6, run_config.py 8 incl. the _PickerReturnModal base, monitor.py 5, data_manager.py 1, matrix.py 1, env_check.py 1, wizard.py 2) x the six criteria (esc labeled / action-key visibility / enter-copy honesty / focus landing / bilingual labels / ExitModal triple), each row stating what changed or what needs a maintainer ruling; report-only findings land in the table, NOT in code: WizardModal (all six bindings show=False at wizard.py:564-576; f/o are step-1-only and u landed-state-only — unconditional keycaps would MISLEAD; step-aware visibility is a redesign) and FailuresModal enter (drill is DataTable-native; the modal binding is the fallback — low priority)."
    - "DNR-6 (gates, goldens, discipline): make lint + make typecheck green; full pytest at EXACTLY the 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1) with zero new failures and every new test passing; node lane green; the snapshot suite passes against the committed SVGs with ZERO regeneration (make snapshot-update is NEVER run — if any snapshot test fails the executor STOPS and reports the D-03 path); sha256 of every tests/tui/__snapshots__/*.svg recorded before Task 1 edits and re-verified identical at the gates; the three new constants join EXPECTED_LNC_CONSTANTS (closed bidirectional inventory, both injectivity tripwires green — identical-pair reuse follows the WIZ_BACK precedent); commits are PLAIN (zero attribution trailers); the executor does NOT push."
  artifacts:
    - tui/strings.py
    - tui/screens/selection.py
    - tui/screens/monitor.py
    - tui/screens/run_config.py
    - tui/app.py
    - tests/tui/test_strings_phase11.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_monitor.py
    - .planning/quick/261017-dnr-uniform-prominent-y-n-across-all-confirm/261017-dnr-SUMMARY.md
  key_links:
    - "LaunchConfirmModal.BINDINGS (selection.py) -> _GateConfirmModal (run_config.py MRO) and the monitor [f] re-run push (monitor.py:1310) — ONE binding edit surfaces keycaps on both launch surfaces"
    - "tui/strings.py new constants -> tests/tui/test_strings_phase11.py EXPECTED_LNC_CONSTANTS (the bidirectional inventory lock) -> remap_binding_descriptions (app.py:429, the L-toggle re-derives every new keycap via the sys.modules screens sweep)"
    - "KillConfirmModal compose override -> monitor.py:561 on_mount #confirm-box query and tests/tui/test_pilot_monitor.py:2307-2310 assertions (id and first-Static order preserved)"
---

<objective>
Uniform prominent Y/N across every confirm modal, plus the maintainer's 2026-10-17 09:50 scope addition: an affordance audit of ALL modals with surgical visibility/styling fixes where the cdr pattern fits.

The maintainer's live-session finding (2026-10-17 09:49): 确认启动的时候没有提示 Y/N — cdr's CDR-3 bolded the quit confirm only; the launch confirm, the stop confirm, and the E2 y-ready state were left plain. This plan replicates the proven cdr pattern (commit 0980956, QuitConfirmModal at tui/app.py:230-286) across the remaining confirm family (DNR-1/2/3), makes the ExitModal triple's affordances explicit (DNR-4), and delivers the all-modals audit table (DNR-5).

Purpose: every confirmation the operator faces shows its answer keys at a glance — bold bracket tokens in the copy plus footer keycaps — with zero semantic changes (keys, actions, and enter behavior byte-identical) and zero golden interaction.
Output: styled/visible confirm modals in tui/, three new strings constants, new keycap/bold-span tests, and the per-modal audit table in the SUMMARY.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

The reference implementation is LIVE in the tree (cdr, commit 0980956):
- tui/app.py:230-286 — QuitConfirmModal: Static(Text) two-step compose + y/n bindings show=True with zh-labeled constants; read it first and copy the pattern, do not redesign.
- tests/tui/test_pilot_run_config.py:2028-2101 — the cdr test twins (keycap-visibility shape at 2028, bold-span shape at 2066); the new tests mirror these.
- tui/app.py:429-466 — remap_binding_descriptions: the L-toggle rebuilds Binding descriptions in place over every screen class (selection/monitor/run_config modals are swept automatically via sys.modules; zero registry edits needed for the new keycaps).

Live target sites (verified at HEAD b33e657):
- tui/screens/selection.py:1194-1215 ConfirmModal.compose (base — DO NOT touch: non-launch consumers stay byte-identical); :1223-1253 LaunchConfirmModal (BINDINGS at 1240-1243, inherits the base compose).
- tui/screens/run_config.py:811-846 _GateConfirmModal (own compose; message Static at 834); :677-765 E2PhraseModal (matched indicator update at 730; y/n bindings at 693-698 stay hidden).
- tui/screens/monitor.py:536-573 KillConfirmModal (BINDINGS 549-553; on_mount queries #confirm-box at 561); :1310 the [f] re-run pushes a plain LaunchConfirmModal (inherits the base binding/keycap edit).
- tui/app.py:173-227 ExitModal (BINDINGS 187-190; message Static at 206).
- tui/strings.py:1481-1483 LNC_GATE_CONFIRM; :1571-1574 LNC_EXIT_CONFIRM_YES/NO (the reuse source for NO); :1778 MON_KILL_KEYCAP (the reuse source for kill-y).
- tests/tui/test_strings_phase11.py:72-87 EXPECTED_LNC_CONSTANTS (the closed bidirectional inventory).
</context>

<tasks>

<task type="auto">
  <name>Task 1: Confirm family prominent Y/N — gate, launch base, kill, E2 y-ready</name>
  <files>tui/strings.py, tui/screens/selection.py, tui/screens/monitor.py, tui/screens/run_config.py, tests/tui/test_strings_phase11.py, tests/tui/test_pilot_run_config.py, tests/tui/test_pilot_monitor.py</files>
  <precondition>Working tree clean at b33e657 (the 261017-cdr + windows follow-ups state); record `sha256sum tests/tui/__snapshots__/*.svg` output into the working notes BEFORE the first edit (the DNR-6 golden insurance — compare at Task 3).</precondition>
  <action>
BEFORE any edit: run the sha256sum snapshot record per the precondition.

1. tui/strings.py — add ONE new constant beside LNC_GATE_CONFIRM (after line 1483): LNC_GATE_CONFIRM_YES = _t("LNC_GATE_CONFIRM_YES", "启动", "Launch") with a comment citing 261017-dnr DNR-1 (verified: NO existing 启动/Launch exact pair exists — new pair, both injectivity tripwires stay green; the NO side reuses LNC_EXIT_CONFIRM_NO whose 取消/Cancel pair is exact — the WIZ_BACK identical-pair precedent, zero new constant for n).

2. tui/screens/selection.py LaunchConfirmModal (per DNR-1): add a compose() override mirroring ConfirmModal.compose (same Vertical id="confirm-box", classes="modal-box", Footer) except the message is built cdr-style: message = Text(self._message); message.highlight_words(("[Y]", "[y]", "[N]", "[n]"), style="bold"); yield Static(message). The lowercase [y] matters: the monitor re-run message MON_RERUN_CONFIRM (pushed through THIS base at monitor.py:1310) carries "[y] 重跑 / Esc 取消" (strings.py:1736-1741) while LNC_GATE_CONFIRM carries uppercase — the 4-token tuple bolds both. highlight_words mutates in place and returns an int (cdr-probed rich seam) — never chain it, two-step only; docstring the override with the 261017-dnr ruling. Flip BINDINGS (1240-1243): Binding("y", "confirm_launch", S.LNC_GATE_CONFIRM_YES, show=True) and Binding("n", "dismiss", S.LNC_EXIT_CONFIRM_NO, show=True) — keys, actions, and the inherited enter->no-op stay byte-identical (EHC-2 untouched).

3. tui/screens/monitor.py KillConfirmModal (per DNR-2): same compose() override shape (CRITICAL: keep id="confirm-box" and the message Static as the first child — on_mount at 561 queries #confirm-box for the border title and tests query the first Static). Flip BINDINGS (549-553): y -> show=True with S.MON_KILL_KEYCAP (停止/Kill — exact reuse), n -> show=True with S.LNC_EXIT_CONFIRM_NO. Comment cites 261017-dnr DNR-2 and the reuse rationale.

4. tui/screens/run_config.py _GateConfirmModal compose (per DNR-1): at line 834 wrap the existing message — build the Text, highlight_words the same 4-token tuple, yield Static(message, id="cfg-gate-message") (keep the id). The pair-list RichLog, cap logic, and on_mount stay untouched.

5. tui/screens/run_config.py E2PhraseModal matched branch (per DNR-3): in on_input_changed (729-731), build Text(S.LNC_E2_MATCH_OK), highlight_words(("[Y]", "[N]"), style="bold"), indicator.update(that_text) — the mismatch branch (733-734) and the y/n bindings (693-698, stay show=False) are untouched; comment records WHY the keycaps stay hidden (armed-after-blur semantics — a visible y while the Input holds focus would advertise a key that types into the Input).

6. tests/tui/test_strings_phase11.py — add "LNC_GATE_CONFIRM_YES" to EXPECTED_LNC_CONSTANTS (the bidirectional lock demands it; comment cites DNR-1).

7. New tests mirroring the cdr twins (test_pilot_run_config.py for gate + E2; test_pilot_monitor.py for kill):
   - keycap test (shape of test_pilot_run_config.py:2028): for LaunchConfirmModal.BINDINGS assert entries y/n show is True with descriptions == the live constants and enter show is False (the base class entries — covers _GateConfirmModal and the re-run by inheritance); same for KillConfirmModal.BINDINGS (y description == MON_KILL_KEYCAP, n == LNC_EXIT_CONFIRM_NO).
   - bold-span test (shape of test_pilot_run_config.py:2066): open the slot-4 gate (enter on the picker, the existing test at 960-990 shows the fixture) and assert the message Static content is a Text whose every [Y]/[N] occurrence carries a bold span while .plain still contains LNC_GATE_CONFIRM; a kill-modal twin in test_pilot_monitor.py over MON_KILL_CONFIRM (open with k per the 2291 fixture); an E2 twin asserting the MATCHED indicator content is a Text with bold [Y]/[N] and _plain == LNC_E2_MATCH_OK (type the exact phrase per the 1236-1238 fixture), plus an assertion the y/n bindings of E2PhraseModal remain show=False (the DNR-3 pin).
  Existing assertions need NO edits — verified live: the gate test reads str(app.screen._message) (977-982), kill/rerun/E2 tests read _plain(...) or str(content) (monitor 1250-1252, 2307; run_config 1238/1435) — all survive Text spans because rich Text.__str__/.plain return the unstyled text.
  <verify>
    <automated>uv run pytest tests/tui/test_strings_phase11.py tests/tui/test_pilot_run_config.py tests/tui/test_pilot_monitor.py -q 2>&1 | tail -3</automated>
  </verify>
  <done>The three confirm surfaces render bold bracket tokens and y/n footer keycaps; LNC_GATE_CONFIRM_YES is the only new constant and it is inventory-registered; the three test modules pass with zero edits to existing assertions; the snapshot sha256 record exists in the working notes.</done>
</task>

<task type="auto">
  <name>Task 2: ExitModal affordances — visible enter/k keycaps + bold triple</name>
  <files>tui/strings.py, tui/app.py, tests/tui/test_strings_phase11.py, tests/tui/test_pilot_run_config.py</files>
  <action>
Per DNR-4 (the coordinator's highest-stakes ruling — visibility ONLY, the Phase-11 semantics stay: enter remains the detach-and-exit default):

1. tui/strings.py — add TWO constants after LNC_EXIT_CONFIRM_NO (line 1574), in the cdr comment family: LNC_EXIT_DETACH_KEYCAP = _t("LNC_EXIT_DETACH_KEYCAP", "分离退出", "detach & exit") and LNC_EXIT_KILL_KEYCAP = _t("LNC_EXIT_KILL_KEYCAP", "终止后退出", "kill & exit") — zh/en wording lifted from the LNC_EXIT_MESSAGE copy so the keycaps say exactly what the message says (verified: no identical pairs exist; terminology already approved in the message constants).

2. tui/app.py ExitModal BINDINGS (187-190): enter -> Binding("enter", "detach_quit", S.LNC_EXIT_DETACH_KEYCAP, show=True); k -> Binding("k", "kill_quit", S.LNC_EXIT_KILL_KEYCAP, show=True); escape unchanged. Compose (206): cdr two-step — message = Text(self._message); message.highlight_words(("[enter]", "[k]", "[esc]"), style="bold"); yield Static(message). Update the class docstring's binding note with the 261017-dnr ruling (the footer now advertises the triple the copy names; enter's default fire is by-design from Phase 11).

3. tests/tui/test_strings_phase11.py — add both names to EXPECTED_LNC_CONSTANTS.

4. tests/tui/test_pilot_run_config.py — one keycap test + one bold-span test in the cdr shapes, over the live-sweep ExitModal (fixture pattern at 1660-1675: FakeLauncherService(live=...) then q): assert enter/k show is True with the new descriptions, escape shows, and every [enter]/[k]/[esc] occurrence in the message Static carries a bold span with .plain still containing the formatted LNC_EXIT_MESSAGE. The existing detach/kill behavior tests (1678-1690, 2231-2275) need NO edits — they read str(self._message) and _plain(content), both span-safe.
  <verify>
    <automated>uv run pytest tests/tui/test_strings_phase11.py tests/tui/test_pilot_run_config.py -q 2>&1 | tail -3</automated>
  </verify>
  <done>ExitModal renders enter/k/esc keycaps and bolded bracket tokens in the message; detach/kill behavior tests pass untouched; both new constants are inventory-registered.</done>
</task>

<task type="auto">
  <name>Task 3: All-modals audit table + full gates</name>
  <files>.planning/quick/261017-dnr-uniform-prominent-y-n-across-all-confirm/261017-dnr-SUMMARY.md, .planning/STATE.md</files>
  <action>
Per DNR-5/DNR-6. NO production code in this task.

1. Walk ALL 27 ModalScreen subclasses in tui/ (live list: app.py HelpModal/ExitModal/QuitConfirmModal; selection.py PresetModal/TemplateMenuModal/PathInputModal/ConfirmModal/LaunchConfirmModal/RowDetailModal; run_config.py _PickerReturnModal(base)/PreviewModal/ProblemsModal/EnvBlockModal/E2PhraseModal/ChoiceModal/_GateConfirmModal/DirPickerModal; monitor.py FailureDetailModal/FailuresModal/KillConfirmModal/LogTailModal/CellDetailModal; data_manager.py QueueDetailModal; matrix.py MatrixKeyModal; env_check.py EnvDetailModal; wizard.py _PathPromptModal/WizardModal) against the six criteria: (1) esc works and carries APP_MODAL_BACK_LABEL, (2) action keys the modal depends on are visible (show=True keycaps), (3) enter's copy/footers do not misrepresent its behavior, (4) input-bearing modals focus the Input on mount, (5) every newly-shown binding label is a bilingual registry constant, (6) the ExitModal triple. Verify each row against the LIVE code (post-Task-1/2 state), not this plan's citations. Planner pre-findings to confirm and carry into the table: all read-only drill-downs (Help/RowDetail/Preview/Problems/EnvBlock/FailureDetail/LogTail/CellDetail/QueueDetail/MatrixKey/EnvDetail) pass on esc-labeled + no hidden essentials; the widget-native pickers (PresetModal/TemplateMenuModal/ChoiceModal first-press, PathInputModal/_PathPromptModal/DirPickerModal input/tree focus) pass criteria 3/4; ConfirmModal-base enter-confirms BY DESIGN for non-launch consumers (EHC-2 covers launch/kill only) — record as a design note; FailuresModal enter is DataTable-native with the modal binding as fallback — report-only finding (low); WizardModal needs a MAINTAINER RULING (all six bindings hidden at wizard.py:564-576; f/o are step-1-only no-ops and u is landed-state-only, so unconditional keycaps would mislead — step-aware visibility is a redesign, out of scope). The table is the audit deliverable: modal x criteria x changed/OK/needs-ruling.

2. Full gates per DNR-6: make lint; make typecheck; make test (full pytest + node lane). The pytest result MUST be the exact 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1) with every new test passing — read the actual counts, do not assume. Re-run sha256sum tests/tui/__snapshots__/*.svg and diff against the Task 1 record — byte-identical required; if ANY snapshot test fails, STOP (never run make snapshot-update) and report the D-03 path per the session ruling.

3. Write the SUMMARY (audit table + change inventory + gate outputs), append the STATE.md Quick Tasks Completed row, and commit PLAIN (no attribution trailers, never push).
  <verify>
    <automated>make lint && make typecheck && make test 2>&1 | tail -5 && sha256sum tests/tui/__snapshots__/*.svg | sha256sum</automated>
  </verify>
  <done>The audit table covers all 27 modal classes with per-criteria verdicts and the two report-only rulings; lint/typecheck green; full suite at the exact 7F baseline with new tests green; snapshot shas identical to the Task 1 record; SUMMARY + STATE row committed plain.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| static registry copy -> rendered modal | strings.py constants flow into the bold-span rendering path of five modals |
| class BINDINGS tables -> Footer renderer | the visibility flips ride the same frozen-Binding rebuild seam the L-toggle remap already owns |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-261017dnr-01 | Tampering | highlight_words call sites (selection/monitor/run_config/app) | medium | mitigate | Two-step discipline only: highlight_words mutates the Text IN PLACE and returns an int (cdr-probed rich text.py:639) — chaining its return would silently drop the Static's content to an int; every site builds Text(constant) first, highlights second, yields third; pinned by the bold-span tests asserting isinstance(content, Text). |
| T-261017dnr-02 | Tampering | BINDINGS visibility flips (LaunchConfirmModal/KillConfirmModal/ExitModal) | medium | mitigate | Only show/description move; keys, actions, priority, and the enter no-op pins stay byte-identical — the existing EHC-2 enter-refusal tests (run_config 984-990, monitor 2312-2318) and the ExitModal detach/kill tests run unedited as the semantic regression net. |
| T-261017dnr-03 | Repudiation | ExitModal advertised default (enter = detach & exit) | low | mitigate | The keycap says exactly what the copy says (wording lifted from LNC_EXIT_MESSAGE) — visibility makes the stray-enter default MORE explicit, never less; semantics untouched per the coordinator ruling. |
| T-261017dnr-04 | Repudiation | E2 armed-state affordance | low | accept | The y keycap stays hidden while the Input holds focus because y TYPES there; the bold [Y]/[N] in the matched copy carries the affordance only once arming is real — recorded as the DNR-3 simplicity ruling. |
| T-261017dnr-SC | Tampering | package installs | high | mitigate | Zero package installs — tui/ + tests/ only, zero dependency/lockfile changes; no [ASSUMED]/[SUS] packages introduced. |
</threat_model>

<verification>
- Task 1/2 targeted: the three touched test modules green, zero edits to existing assertions (span-safe styles verified live).
- Task 3 full: make lint + make typecheck + make test; pytest at the exact 7F baseline membership; node lane green; snapshot SVGs byte-identical to the pre-edit sha256 record (zero regeneration — a snapshot failure is a STOP, not a regen).
</verification>

<success_criteria>
- All four remaining confirm surfaces (gate, re-run launch, kill, E2 y-ready) plus the ExitModal triple show bold bracket tokens; gate/re-run/kill also show y/n footer keycaps with bilingual labels.
- Zero semantic changes: EHC-2 enter pins, y-only confirms, and the ExitModal detach-default all pass on their unedited tests.
- Three new constants (LNC_GATE_CONFIRM_YES, LNC_EXIT_DETACH_KEYCAP, LNC_EXIT_KILL_KEYCAP) registered in the closed EXPECTED_LNC_CONSTANTS inventory; reuses (LNC_EXIT_CONFIRM_NO, MON_KILL_KEYCAP) carry identical pairs — both injectivity tripwires green.
- The 27-modal audit table delivered in the SUMMARY with the WizardModal and FailuresModal rulings flagged for the maintainer.
</success_criteria>

<output>
Create `.planning/quick/261017-dnr-uniform-prominent-y-n-across-all-confirm/261017-dnr-SUMMARY.md` when done
</output>
