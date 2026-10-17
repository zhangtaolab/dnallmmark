---
phase: quick-261016-poa
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/screens/run_config.py
  - tui/screens/selection.py
  - tui/services/sweep_launcher.py
  - tui/strings.py
  - tui/styles.tcss
  - tests/tui/test_pilot_run_config.py
  - tests/tui/test_services_sweep_launcher.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/__snapshots__/run_config.svg
  - docs/TUI-GUIDE.md
  - docs/TUI-DEMO.md
  - README.md
  - .planning/STATE.md
  - .planning/quick/261016-poa-slot-4-run-config-ux-fixes-toggle-cursor/261016-poa-SUMMARY.md
autonomous: true
requirements: [UX-1, UX-2, UX-3, UX-4, UX-5, UX-6]

estimate:
  tokens: 58000
  raw_tokens: 30000
  tasks: 3
  confidence: med

must_haves:
  truths:
    - "UX-1: toggling a mark with space anywhere in a scrollable slot-4 picker (keyboard path AND the screen-level space action) leaves the cursor on the SAME registry key and the picker scroll offset byte-stable — no jump to top, no bottom-edge snap; pinned by a Pilot test over a 40-model fixture that records scroll_offset.y + key_at(highlighted) before the toggle and asserts exact equality after"
    - "UX-2: the marked row in the slot-4 picker is visually distinct at higher contrast (token-based tcss override scoped to the PickerList type selector ONLY — textual 8.2.8 default is color $text-success on background $panel via the .selection-list--button-selected[-highlighted] component classes); the OTHER 8 golden SVGs stay byte-identical (a bare SelectionList rule would drift selection_models/selection_datasets — forbidden); run_config.svg regenerates through the D-03 path only"
    - "UX-3: the term 启动门 / Launch Gate is gone from all living prose and code — LNC_GATE_TITLE zh becomes 启动确认, en becomes Launch Confirmation; ENV_VERDICT_CRITICAL_FAIL zh/en wording follows; the strings.py LNC section comment, test docstrings, docs/TUI-GUIDE.md (incl. the renamed section + its anchor), docs/TUI-DEMO.md (incl. the TUI-GUIDE anchor link), README.md all read launch confirmation; the only remaining occurrences repo-wide are the point-in-time recordings under docs/demo/ (casts + RECORDED.md), untouched on purpose"
    - "UX-4: slot 4 renders a persistent dim hint line below the preview line (new CFG_GATE_HINT, zh 回车 打开启动确认 · Y 启动 / N 取消, en counterpart) so the hidden enter binding is discoverable"
    - "UX-5: the non-E2' launch-confirmation modal lists the actual plan under the counts formula — one 模型+数据集 pair per line from GateSummary.pairs, derived service-side in sweep_launcher.gate_confirm_data from the FRESH preview cells (first-occurrence order, seeds collapsed into the formula line, never per-row); the UI renders, never computes; the list rides a bounded RichLog (EnvBlockModal pattern) and large lists cap at the first 12 pairs plus the …共 {pairs} 组 total line (LNC_GATE_PAIRS_MORE); the E2PhraseModal escalation is untouched by this item"
    - "UX-6: Y/N confirmation — LNC_GATE_CONFIRM zh 确认启动以上训练？— [Y] 启动 / [N] 取消 (en counterpart), an n binding that dismisses (= Esc) on the LaunchConfirmModal BASE (slot-4 gate and the monitor [f] re-run both inherit it) and on E2PhraseModal (armed after the y-ready blur; while the phrase Input holds focus n still types), LNC_E2_MATCH_OK copy syncs to the [Y]/[N] pair; EHC-2 holds unchanged — enter stays the documented no-op on every launch confirm and the existing enter-noop / y-launch test assertions pass unmodified"
    - "Gates: make lint + make typecheck green; full make test lands at EXACTLY the 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1) with zero new failures and every new test passing; node --test 26/26; after make snapshot-update, git status over tests/tui/__snapshots__/ shows ONLY run_config.svg modified (the other 8 rewrite byte-identical — any other drift is a scope leak to fix before proceeding)"
    - "Discipline: i18n — every strings.py change carries BOTH zh and en values, the bidirectional inventory (EXPECTED_LNC_CONSTANTS / EXPECTED_CFG_CONSTANTS) gains the three new names in the same change, zh-value injectivity holds; commits are PLAIN (zero attribution trailers); the executor does NOT push; the regenerated run_config.svg is generated but NOT committed — it is reported to the orchestrator for the maintainer D-03 review (the local suite runs green against the regenerated file on disk)"
  artifacts:
    - tui/screens/run_config.py
    - tui/screens/selection.py
    - tui/services/sweep_launcher.py
    - tui/strings.py
    - tui/styles.tcss
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_services_sweep_launcher.py
  key_links:
    - "on_selection_list_selection_toggled / action_toggle_mark → _apply_spec_change(picker_anchor=key) → _render_picker(anchor_key=key) → PickerList.set_rows(..., anchor_key=...) restores highlighted + scroll offset (UX-1)"
    - "sweep_launcher.gate_confirm_data → preview cells → GateSummary.pairs → _GateConfirmModal(pairs=...) → bounded RichLog rows (UX-5)"
    - "strings.py LNC_GATE_TITLE value → run_config footer binding label + all four gate-family modal border titles + run_config.svg footer (UX-2/UX-3, the one golden that may drift)"
---

<objective>
Slot 4 (run config) UX fix batch from maintainer hands-on feedback (2026-10-16) plus the original-design alignment "list the task plan before launch, confirm with Y/N". Six fixes: (1) toggle no longer loses the picker cursor/scroll anchor; (2) marked-row contrast raised on the slot-4 picker; (3) terminology 启动门 → 启动确认 (en Launch Gate → Launch Confirmation) everywhere living; (4) an on-screen enter/Y/N hint line below the preview; (5) the launch-confirmation modal lists the actual model+dataset pairs it will run (service-derived, bounded, truncated with a total line); (6) Y/N confirmation wording plus an n cancel key on every launch confirm, with EHC-2 (inert enter) preserved.

Purpose: the maintainer is actively driving the console; these are the concrete frictions found on the real machine, and items 5/6 restore the originally designed pre-launch task-list confirmation.
Output: hardened slot-4 interaction + launch-confirmation flow, tests pinning every fix, terminology sweep, regenerated run_config.svg awaiting the maintainer D-03 review.
</objective>

<required_reading>
/home/forrest/Github/dnallmmark/.planning/quick/261016-poa-slot-4-run-config-ux-fixes-toggle-cursor/PLANNER-CONTRIBUTIONS.md
/home/forrest/Github/dnallmmark/tui/screens/run_config.py
/home/forrest/Github/dnallmmark/tui/screens/selection.py
/home/forrest/Github/dnallmmark/tui/services/sweep_launcher.py
/home/forrest/Github/dnallmmark/tui/strings.py
/home/forrest/Github/dnallmmark/tests/tui/test_pilot_run_config.py
</required_reading>

<context>
Planning-time line references (re-verify on disk before editing — #3786 mutable scope):
- tui/screens/run_config.py — PickerList.set_rows (~440), _PickerReturnModal (~527), EnvBlockModal (~616, the bounded RichLog pattern), E2PhraseModal (~647), _GateConfirmModal (~773), the enter binding labelled S.LNC_GATE_TITLE (~956), compose tail #cfg-preview-line → BottomBar (~1208), _render_picker (~1397), on_selection_list_selection_toggled (~1585), action_toggle_mark (~1644), the gate mount passing LNC_GATE_SUMMARY + LNC_GATE_CONFIRM (~1947), _apply_spec_change (~2042).
- tui/screens/selection.py — ConfirmModal (~1194), LaunchConfirmModal (~1223, the y binding + inert enter).
- tui/services/sweep_launcher.py — GateSummary (~259, frozen dataclass), gate_confirm_data (~406, the FRESH preview recompute).
- tui/services/run_config.py — preview() (~877) returns PreviewResult.cells as the verbatim run_sweep.enumerate_matrix tuples (3-tuples, 4-tuples under curve fractions).
- tui/strings.py — LNC section (~1428-1513), ENV_VERDICT_CRITICAL_FAIL (~274).
- tui/styles.tcss — .cfg-hint (~605), the modal align group (~632), #cfg-envblock-log bound (~647), .modal-box (~210).
- textual 8.2.8 facts probed at planning time: SelectionList DEFAULT_CSS styles the marked row through the .selection-list--button-selected and .selection-list--button-selected-highlighted component classes (color $text-success, background $panel — the contrast complaint); OptionList.watch_highlighted force-calls scroll_to_highlight → scroll_to_region(force=True) and clear_options resets the scroll — the rebuild after a toggle snaps the row to a viewport edge (the 跳底 symptom).
- Test baseline: exactly 7 failed / 1808 passed (membership: test_determinism 1, test_schemas 5, test_services_run_config 1); node 26/26. The 9 golden SVG tests are regular green tests (zh-pinned).
- Rulings that bind: EHC-2 (enter can never pass a launch gate — keep), D-01 (the picker owns its marks via the spec sets), D-03 (golden regen is maintainer-reviewed; make snapshot-update is the only regen path), the i18n single-home + bidirectional injectivity locks, plain commits / no push (the orchestrator pushes).
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Toggle anchor preservation (UX-1) + marked-row contrast (UX-2)</name>
  <files>tui/screens/run_config.py, tui/styles.tcss, tests/tui/test_pilot_run_config.py</files>
  <behavior>
    - Test 1 (RED first — write it before the fix and watch it fail): over a 40-model fake fixture, open slot 4, move the cursor deep into the list with down-arrow presses so the picker scrolls, record picker.scroll_offset.y and picker.key_at(picker.highlighted), press space, settle; assert the highlighted key is unchanged, scroll_offset.y is exactly unchanged, and the model got marked (spec round-trip through the fake's load_state).
    - Test 2: the same invariants hold through the screen-level space path (focus off the picker first, screen space action marks the cursor row).
    - Test 3: contrast pin — tui/styles.tcss contains a rule scoped to the PickerList type selector that targets the .selection-list--button-selected component class (presence pin; the visual truth is the run_config golden + D-03 review).
    - Test 4 (regression): the existing filter-typing and m-kind-flip picker rebuilds keep their current behavior (no anchor restore — index clamp as today).
  </behavior>
  <action>
    RED phase: add the Pilot anchor test to tests/tui/test_pilot_run_config.py with a 40-entry model fixture (FakeRunConfigService(entries=PickerEntries(model_entries=...40 keys..., dataset_entries=..., custom_status={}))); run it, confirm it fails on the current rebuild (scroll resets or edge-snaps), commit per the GSD quick flow.

    GREEN phase — anchor restore: extend PickerList.set_rows with an optional anchor_key parameter. Inside set_rows, BEFORE clear_options, capture the current scroll offset y (self.scroll_offset.y). After add_options: when anchor_key is present in the new keys, set self.highlighted to that key's index (which may force-scroll via the 8.2.8 watcher), then restore the captured offset with self.scroll_to(y=prev_y, animate=False, immediate=True) as the final authority — probe on 8.2.8 whether the immediate call lands after the option-height refresh or a call_after_refresh follow-up is needed; the Pilot test pins the final offset either way. When anchor_key is absent or missing from the new keys, keep today's index-clamp behavior exactly (no scroll restore). Document in the set_rows docstring WHY (the full rebuild loses the scroll anchor; the toggle path has an identical row set so the captured offset is exact).

    Thread the anchor: _render_picker gains an optional anchor_key parameter passed through to set_rows; _apply_spec_change gains a picker_anchor keyword (consumed before the spec replace — it is not a spec field); on_selection_list_selection_toggled and action_toggle_mark pass the toggled key as picker_anchor. All other _apply_spec_change call sites (params choice modals, load, resize) stay anchor-less.

    Contrast: in tui/styles.tcss add a rule scoped to the PickerList type selector overriding the two selected component classes (.selection-list--button-selected and .selection-list--button-selected-highlighted) with token-based values that make the marked row clearly readable against $panel — prefer a background token such as $boost plus text-style bold (and/or a stronger foreground token); zero hardcoded hex (the 08-06 zero-hex discipline). Scope is the PickerList selector ONLY: a bare SelectionList or OptionList rule would restyle the selection screens' own lists and drift their goldens — forbidden. Add a comment naming the 8.2.8 default ($text-success on $panel) and the scoping reason.
  </action>
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_pilot_run_config.py -q -k "anchor or contrast or toggle" && make lint && make typecheck</automated>
  </verify>
  <done>Space-toggling a deep row keeps cursor key and scroll offset exactly; screen-space path too; filter/kind-flip rebuilds unchanged; the contrast rule exists scoped to PickerList with tokens only; the touched modules pass ruff and ty.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Launch-confirmation flow — task list (UX-5), Y/N (UX-6), terminology (UX-3), entry hint (UX-4)</name>
  <files>tui/services/sweep_launcher.py, tui/screens/run_config.py, tui/screens/selection.py, tui/strings.py, tests/tui/test_services_sweep_launcher.py, tests/tui/test_pilot_run_config.py, tests/tui/test_strings_phase11.py, tests/tui/test_pilot_env_check.py</files>
  <behavior>
    - Test 1 (service): gate_confirm_data over a real 2-model x 2-task x 3-seed spec returns pairs as exactly the four (model, task) pairs in enumerate_matrix first-occurrence order — seeds collapsed, never expanded per row; a curve-fractions spec (4-tuple cells) derives the same pairs.
    - Test 2 (UI): the non-E2' gate modal renders the pair lines (LNC_GATE_PAIR_LINE formatted) from summary.pairs in its RichLog; with 20 scripted pairs the log shows the first 12, contains LNC_GATE_PAIRS_MORE formatted with the total, and does NOT contain the 13th pair; from that scrollable-list state, pressing y still launches (the log never eats the confirm keys).
    - Test 3: pressing n on the gate modal dismisses it and launcher.launch_calls stays empty; pressing n on E2PhraseModal after the matched-enter y-ready blur dismisses without launch, while n while the phrase Input holds focus still types the character.
    - Test 4: the existing gate happy-path assertions (LNC_GATE_SUMMARY formatted + LNC_GATE_CONFIRM in the message, enter-noop, y launches exactly once) pass UNMODIFIED — the constants carry the new wording.
    - Test 5: #cfg-gate-hint renders CFG_GATE_HINT below the preview line on slot 4.
    - Test 6: inventories — EXPECTED_LNC_CONSTANTS gains LNC_GATE_PAIR_LINE and LNC_GATE_PAIRS_MORE, EXPECTED_CFG_CONSTANTS gains CFG_GATE_HINT (the bidirectional lock fails until they are registered).
    - Test 7: the env-check zh verdict assertion literal follows the ENV_VERDICT_CRITICAL_FAIL rewording.
  </behavior>
  <action>
    Strings first (tests consume constants): in tui/strings.py — LNC_GATE_TITLE zh 启动确认 / en Launch Confirmation; LNC_GATE_CONFIRM zh 确认启动以上训练？— [Y] 启动 / [N] 取消 / en Launch these training runs? — [Y] launch / [N] cancel; LNC_E2_MATCH_OK zh/en sync to the [Y]-launch / [N]-cancel pair; ENV_VERDICT_CRITICAL_FAIL zh replaces the trailing 启动门 phrase with 启动确认 and en says run-config launch confirmation; the LNC section header comment renames 启动门/执行 to 启动确认/执行. Three new constants, each with BOTH values: CFG_GATE_HINT (zh 回车 打开启动确认 · Y 启动 / N 取消, en Enter opens launch confirmation · Y launch / N cancel), LNC_GATE_PAIR_LINE ({model} × {task}, language-neutral), LNC_GATE_PAIRS_MORE (zh …共 {pairs} 组, en … {pairs} pairs total). Register the new names in the two inventory tuples in tests/tui/test_strings_phase11.py and update that file's and test_pilot_run_config.py's 启动门 docstring mentions. Update the zh substring literal in tests/tui/test_pilot_env_check.py.

    Service: GateSummary gains a trailing field pairs: tuple[tuple[str, str], ...] = () (defaulted — the existing fakes and snapshot fakes construct without it); gate_confirm_data derives pairs service-side from the fresh preview_result.cells as ordered first-occurrence (cell[0], cell[1]) dedupe — the UI never computes; document the field in the GateSummary docstring.

    Gate modal: _GateConfirmModal gains a pairs constructor parameter (stored alongside the inherited message/on_confirm; keep the inherited _message attribute — an existing test reads it) and overrides compose: a Vertical(id="cfg-gate-box", classes="modal-box") holding Static(self._message, id="cfg-gate-message"), RichLog(wrap=True, id="cfg-gate-log"), Footer; on_mount sets the border title from S.LNC_GATE_TITLE and writes the pair lines — all pairs when within the cap, else the first 12 plus LNC_GATE_PAIRS_MORE with the total. The cap is a module-level documented constant (12). In tui/styles.tcss: add #cfg-gate-log with height auto and a max-height scroll bound (the EnvBlockModal inherited bound; 14 keeps formula + list + confirm inside the design grid) and add the modal's class name to the modal align group so the box centers like its siblings. The gate mount site passes pairs=summary.pairs. Follow the EnvBlockModal bounded pattern exactly; if probing shows the RichLog can steal focus on click and swallow y/n/esc, disable its focusability and say so in a comment.

    N key: add Binding("n", "dismiss", show=False) to LaunchConfirmModal in tui/screens/selection.py (the base — the slot-4 gate and the monitor [f] re-run both inherit; ConfirmModal itself and every non-launch consumer keep enter-confirm unchanged; update the class docstring: y starts, n/esc cancel, enter inert). Add the same n binding to E2PhraseModal in tui/screens/run_config.py (armed only once the phrase Input is blurred by the y-ready advance — while the Input holds focus, n types, which is correct) and sync its y-ready copy via the LNC_E2_MATCH_OK change. Enter stays the documented no-op on both (EHC-2) — do not touch action_confirm.

    Entry hint: in the RunConfigScreen compose, yield Label(S.CFG_GATE_HINT, id="cfg-gate-hint", classes="cfg-hint") immediately after the #cfg-preview-line label and before BottomBar (the existing .cfg-hint class carries the dim height-1 row styling — no new tcss needed for it).
  </action>
  <verify>
    <automated>uv run --group dev --group tui pytest tests/tui/test_services_sweep_launcher.py tests/tui/test_pilot_run_config.py tests/tui/test_strings_phase11.py tests/tui/test_pilot_env_check.py -q && make lint && make typecheck</automated>
  </verify>
  <done>The confirm modal lists the planned pairs service-derived with the 12+total truncation; n cancels every launch confirm; E2 y-ready copy names both keys; the terminology is 启动确认 / Launch Confirmation in strings + tests; the hint line renders below the preview; all touched suites green, ruff + ty green.</done>
</task>

<task type="auto">
  <name>Task 3: Docs terminology sweep, golden D-03 regeneration + report, full gates, bookkeeping</name>
  <files>docs/TUI-GUIDE.md, docs/TUI-DEMO.md, README.md, tests/tui/__snapshots__/run_config.svg, .planning/STATE.md, .planning/quick/261016-poa-slot-4-run-config-ux-fixes-toggle-cursor/261016-poa-SUMMARY.md</files>
  <action>
    Docs: replace the launch-gate terminology across living prose — docs/TUI-GUIDE.md (8 sites incl. the keymap row that says Open the launch gate, the section heading The launch gate and the E2' trust boundary, and both troubleshooting mentions), docs/TUI-DEMO.md (6 sites incl. its anchor link to the renamed TUI-GUIDE section — update the fragment to match the new heading slug), README.md (1 site). Read each site after replacing — the sentence must still parse. Extend the TUI-GUIDE gate section with the new affordances it now documents: the pair list under the counts formula (with the cap + total-line behavior), the n cancel key beside y/esc, and the new on-screen hint line; mirror the keymap-level facts in TUI-DEMO.md's tables. Do NOT touch docs/demo/casts/*.cast or docs/demo/RECORDED.md — they are point-in-time recordings of the old build; the queued demo re-record task regenerates them, and editing recordings would falsify them (note this exclusion in the SUMMARY).

    Goldens (D-03): run make snapshot-update (the ONLY regen path). Then verify scope: git status --porcelain over tests/tui/__snapshots__/ must list ONLY run_config.svg (the other eight rewrite byte-identical — the fakes are deterministic and no other screen's render changed; ANY other modified SVG is a scope leak: stop, find the leak — most likely the contrast rule losing its PickerList scoping — fix, regen again). The run_config.svg diff should reflect exactly three causes: the footer label 启动门→启动确认, the marked-row contrast, the new hint row. DO NOT COMMIT the regenerated run_config.svg — the executor generates and reports only; leave the file in the working tree (the local suite compares against the on-disk file and stays green) and hand the diff summary to the orchestrator for the maintainer D-03 review. Committing the SVG unilaterally is the one prohibited move in this task.

    Full gates: make lint, make typecheck, make test — the pytest lane must land at EXACTLY the 7F baseline membership (test_determinism 1, test_schemas 5, test_services_run_config 1) with zero new failures and every test added by Tasks 1-2 passing (this is why the golden regen precedes the suite run); node --test reports 26/26 via make test.

    Bookkeeping: append the 261016-poa row to the Quick Tasks Completed table in .planning/STATE.md (description: slot 4 运行配置 UX 修复批 — toggle 光标/滚动锚点、选中行对比度、启动确认术语、入口提示行、任务清单、Y/N 确认; date 2026-10-16; commit = the short hash of the last code commit from Task 2; directory = this task dir). Write 261016-poa-SUMMARY.md in this task directory covering: per-item what/where (file:line), the RED-first evidence for UX-1, the golden scope-verification output (the 8-identical/1-drift git status), the run_config.svg diff causes for the maintainer D-03 review, the docs/casts exclusion rationale, and the exact final gate numbers. Commits are plain (no attribution trailers); do NOT push — the orchestrator pushes after the maintainer sign-off on the SVG.
  </action>
  <verify>
    <automated>git status --porcelain tests/tui/__snapshots__/ | grep -v "run_config.svg" ; grep -rn "launch gate" docs/TUI-GUIDE.md docs/TUI-DEMO.md README.md ; grep -rn "启动门" tui/ tests/ --include="*.py" ; make test 2>&1 | tail -3</automated>
  </verify>
  <done>Living docs read launch confirmation (anchor link intact); demo recordings untouched; goldens regenerated with exactly one drift (run_config.svg, uncommitted, reported for D-03); full suite at the exact 7F baseline with all new tests green; node 26/26; STATE.md row and SUMMARY written; nothing pushed.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| operator keystrokes → TUI | the only input surface; no network, no filesystem writes outside XDG state, no subprocess in this change set |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-poa-01 | Tampering | launch-confirmation modal (UX-5/UX-6) | low | mitigate | the pair list shows the REAL planned matrix before y can launch (service-derived, never UI-computed), y stays the sole launch key, enter remains inert (EHC-2), and n adds an explicit cancel — all pinned by the Task-2 tests |
| T-poa-02 | Denial of Service | gate modal RichLog (UX-5) | low | mitigate | the pair list is bounded (max-height tcss) and content-capped at 12 rows + total line — a full-matrix 8850-cell plan can never grow the modal past the design grid |
</threat_model>

<verification>
- make lint && make typecheck — both green.
- make test — pytest at exactly the 7F baseline membership, zero new failures, every new test passing; node 26/26.
- git status --porcelain tests/tui/__snapshots__/ lists only run_config.svg after make snapshot-update (the other eight byte-identical).
- Repo grep: no 启动门 and no Launch Gate / launch gate in tui/, tests/, docs/TUI-GUIDE.md, docs/TUI-DEMO.md, README.md living prose — occurrences remain only inside docs/demo/ recordings, deliberately.
- i18n: every changed/new strings constant carries both zh and en; the bidirectional inventory tests pass with the three new names registered.
- EHC-2 preserved: existing enter-noop and y-launch assertions pass unmodified.
- Commit log: plain messages, zero attribution trailers; run_config.svg NOT among the commits; nothing pushed.
</verification>

<success_criteria>
All six maintainer fixes landed and test-pinned: toggle keeps cursor+viewport (Pilot exact-equality pin), marked-row contrast raised on the slot-4 picker only (8 goldens byte-identical), terminology renamed everywhere living with docs prose + anchor updated, hint line renders below the preview, the confirm modal lists the service-derived plan with 12+total truncation, and Y/N works on every launch confirm with enter still inert. Gates green at the exact baseline; run_config.svg regenerated and awaiting maintainer D-03 sign-off; STATE.md and SUMMARY written; no push.
</success_criteria>

<output>
Write .planning/quick/261016-poa-slot-4-run-config-ux-fixes-toggle-cursor/261016-poa-SUMMARY.md when done (include the D-03 hand-off block for the orchestrator → maintainer)
</output>
