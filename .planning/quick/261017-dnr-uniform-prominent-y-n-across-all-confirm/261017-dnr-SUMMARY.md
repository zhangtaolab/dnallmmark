---
phase: quick-261017-dnr
plan: 01
subsystem: tui
tags: [tui, confirm-modals, y-n-keycaps, bold-tokens, bindings, i18n, audit, tests]
requires:
  - "261017-cdr QuitConfirmModal prominence pattern (commit 0980956) — the two-step highlight_words compose + show=True keycap bindings this task replicates"
  - "261015-ehc EHC-2 enter-refusal pins (LaunchConfirmModal y-only) and the L-toggle remap sweep (app.py remap_binding_descriptions)"
  - "261016-vxr KillConfirmModal EHC-2 extension (y the only key that stops a training)"
provides:
  - "Prominent Y/N on every remaining confirm surface: slot-4 gate, monitor [f] re-run launch, slot-5 kill confirm, E2 y-ready matched indicator (bold bracket tokens + y/n Footer keycaps where the keys are live)"
  - "ExitModal affordance triple visible: enter/k Footer keycaps (wording verbatim from LNC_EXIT_MESSAGE) + bold [enter]/[k]/[esc] message tokens — enter stays the Phase-11 detach default (visibility only)"
  - "Three new registry constants (LNC_GATE_CONFIRM_YES, LNC_EXIT_DETACH_KEYCAP, LNC_EXIT_KILL_KEYCAP) with two exact-identical-pair reuses (LNC_EXIT_CONFIRM_NO, MON_KILL_KEYCAP) — both injectivity tripwires green"
  - "The 27-modal audit table (all ModalScreen subclasses in tui/ × six criteria) with the WizardModal NEEDS-RULING and FailuresModal low-priority findings"
affects:
  - "tui/screens/selection.py (LaunchConfirmModal compose override + y/n binding visibility)"
  - "tui/screens/monitor.py (KillConfirmModal compose override + y/n binding visibility)"
  - "tui/screens/run_config.py (_GateConfirmModal message wrap, E2PhraseModal matched indicator)"
  - "tui/app.py (ExitModal bindings + compose + docstring)"
  - "tui/strings.py (LNC_ family: one + two new constants)"
key-files:
  created:
    - .planning/quick/261017-dnr-uniform-prominent-y-n-across-all-confirm/261017-dnr-SUMMARY.md
  modified:
    - tui/strings.py
    - tui/screens/selection.py
    - tui/screens/monitor.py
    - tui/screens/run_config.py
    - tui/app.py
    - tests/tui/test_strings_phase11.py
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_pilot_monitor.py
decisions:
  - "The 4-token bold tuple (\"[Y]\", \"[y]\", \"[N]\", \"[n]\") on LaunchConfirmModal/KillConfirmModal/_GateConfirmModal: the monitor re-run message MON_RERUN_CONFIRM carries lowercase [y] while LNC_GATE_CONFIRM carries uppercase — the tuple bolds both surfaces through ONE base"
  - "y keycap = LNC_GATE_CONFIRM_YES (启动/Launch, a NEW pair — none existed); n keycap = LNC_EXIT_CONFIRM_NO reuse (取消/Cancel exact — the WIZ_BACK identical-pair precedent); kill-y = MON_KILL_KEYCAP reuse (停止/Kill exact) — exactly ONE new constant for the confirm family"
  - "E2PhraseModal y/n bindings STAY show=False (DNR-3 pin, test-enforced): they only arm after the matched-enter blur — a visible y keycap while the Input holds focus would advertise a key that types into the Input; the bold matched copy carries the affordance"
  - "ExitModal keycaps lift wording VERBATIM from LNC_EXIT_MESSAGE (分离退出/detach & exit, 终止后退出/kill & exit) — the keycap says exactly what the copy says; enter's default fire is by-design Phase 11, made MORE explicit never less (T-261017dnr-03)"
  - "highlight_words two-step discipline everywhere (T-261017dnr-01): build Text(constant) first, highlight second, yield third — the installed rich returns int; every bold-span test pins isinstance(content, Text)"
metrics:
  duration: 12 min
  completed: 2026-10-17
status: complete
requirements: [DNR-1, DNR-2, DNR-3, DNR-4, DNR-5, DNR-6]
actuals:
  tokens: 8083        # chars/4 over the realized tui/+tests/ diff (32332 chars)
  tasks: 3
  commits: 2          # code commits on the plan file set (8c995da, b270920); +1 docs commit landing this file
plan_head_before: b33e657496ebe3ee1e7b3f00d07ef4d485aadc2b
---

# Quick Task 261017-dnr: Uniform Prominent Y/N Across All Confirm Modals Summary

One-liner: the cdr prominence pattern (bold bracket tokens + visible y/n keycaps) replicated across the launch/kill/E2 confirm family and the ExitModal triple — visibility only, zero semantic changes, zero golden interaction.

## What Changed

### Task 1 — Confirm family (commit 8c995da)

| Surface | File | Change |
|---------|------|--------|
| `LaunchConfirmModal` (serves slot-4 gate + monitor [f] re-run) | `tui/screens/selection.py` | `compose()` override: `Text(self._message)` + `highlight_words(("[Y]","[y]","[N]","[n]"), style="bold")` (two-step, cdr pattern); layout mirrors `ConfirmModal.compose` exactly (`#confirm-box` Vertical, message Static FIRST, Footer). `y`/`n` bindings flip to `show=True` with `S.LNC_GATE_CONFIRM_YES` / `S.LNC_EXIT_CONFIRM_NO`. Keys/actions/inherited enter->no-op byte-unchanged (EHC-2). |
| `KillConfirmModal` | `tui/screens/monitor.py` | Same `compose()` override shape (id=`confirm-box` kept — `on_mount` queries it; message Static first — tests query the first Static). `y`->`show=True` with `S.MON_KILL_KEYCAP` (exact reuse), `n`->`show=True` with `S.LNC_EXIT_CONFIRM_NO`. `MON_KILL_CONFIRM` value byte-unchanged; y stays the ONLY key that stops a training. |
| `_GateConfirmModal` | `tui/screens/run_config.py` | Its own compose wraps the message Static in the bold-token Text; `#cfg-gate-message` id kept; pair-list RichLog/cap/on_mount untouched. |
| `E2PhraseModal` matched branch | `tui/screens/run_config.py` | Indicator updates to `Text(S.LNC_E2_MATCH_OK)` with bold `[Y]/[N]`; mismatch branch stays a plain string; y/n bindings stay `show=False` BY DESIGN (armed-after-blur — a visible y while the Input holds focus would advertise a key that types). |
| `ConfirmModal` base + non-launch consumers | — | Byte-untouched (preset overwrite, queue cancels, wizard cancel keep enter-confirms). |

### Task 2 — ExitModal affordances (commit b270920)

- `enter` -> `show=True` with `S.LNC_EXIT_DETACH_KEYCAP` (分离退出 / detach & exit); `k` -> `show=True` with `S.LNC_EXIT_KILL_KEYCAP` (终止后退出 / kill & exit); escape unchanged. Keycaps lift the wording verbatim from `LNC_EXIT_MESSAGE`; enter remains the Phase-11 detach-and-exit default (visibility only — the coordinator's keep-semantics ruling).
- Message Static becomes `Text` + `highlight_words(("[enter]","[k]","[esc]"), style="bold")` — one tuple covers BOTH `LNC_EXIT_MESSAGE` and `LNC_EXIT_MESSAGE_MULTI` (same triple tokens).
- Class docstring records the affordance ruling.

### Constants (exactly three new; both reuses verified identical-pair)

| Constant | zh / en | Kind |
|----------|---------|------|
| `LNC_GATE_CONFIRM_YES` | 启动 / Launch | NEW pair (none existed; both injectivity tripwires green) |
| `LNC_EXIT_DETACH_KEYCAP` | 分离退出 / detach & exit | NEW pair (wording verbatim from LNC_EXIT_MESSAGE) |
| `LNC_EXIT_KILL_KEYCAP` | 终止后退出 / kill & exit | NEW pair (wording verbatim from LNC_EXIT_MESSAGE) |
| `LNC_EXIT_CONFIRM_NO` (reuse, n keycap) | 取消 / Cancel | identical pair exists x3 (WIZ_CANCEL_LABEL et al.) — WIZ_BACK precedent |
| `MON_KILL_KEYCAP` (reuse, kill-y keycap) | 停止 / Kill | exact reuse — it is what y does |

All three new names joined `EXPECTED_LNC_CONSTANTS` (closed bidirectional inventory; `test_cfg_lnc_mon_inventory_complete_no_unlisted_constants` + `test_registry_consistency_same_zh_implies_same_en` / `same_en_implies_same_zh` all green).

### Tests (7 new; zero edits to existing assertions)

Keycap twins (binding-table shape) + bold-span twins (Pilot-opened modal, `isinstance(content, Text)` + per-occurrence bold-span coverage + `.plain`/`str()` content preserved):

- `test_launch_confirm_footer_shows_y_n_keycaps` + `test_gate_confirm_message_bolds_y_n_tokens` + `test_e2_matched_indicator_bolds_tokens_keycaps_stay_hidden` (test_pilot_run_config.py — the last also PINS the E2 y/n `show=False` design)
- `test_kill_confirm_footer_shows_y_n_keycaps` + `test_kill_confirm_message_bolds_y_n_tokens` (test_pilot_monitor.py)
- `test_exit_modal_footer_shows_enter_k_keycaps` (also asserts `action == "detach_quit"/"kill_quit"` — the visibility-only proof) + `test_exit_modal_message_bolds_triple_tokens` (test_pilot_run_config.py)

## The 27-Modal Audit Table (DNR-5)

Verified against the LIVE post-Task-1/2 code. Criteria: (1) esc labeled `APP_MODAL_BACK_LABEL`, (2) action keys visible, (3) enter copy honest, (4) Input focused on mount, (5) shown labels are bilingual registry constants, (6) ExitModal triple. Verdicts: **OK** / **CHANGED** (this task) / **DESIGN** (by-design note) / **FINDING** (report-only) / **RULING** (maintainer decision needed).

| # | Modal (file) | 1 esc | 2 keys visible | 3 enter honest | 4 input focus | 5 registry labels | 6 exit triple | Verdict |
|---|--------------|-------|----------------|----------------|---------------|-------------------|---------------|---------|
| 1 | HelpModal (app.py) | OK | OK (no action keys) | OK (no enter binding) | n/a | OK | n/a | OK, unchanged |
| 2 | ExitModal (app.py) | OK | CHANGED (enter/k now show) | CHANGED (keycap = copy wording; enter detach default now advertised AND real) | n/a (no Input) | CHANGED (2 new constants) | CHANGED (bold triple + keycaps) | CHANGED Task 2 |
| 3 | QuitConfirmModal (app.py) | OK | OK (cdr: y/n show=True) | OK (inert enter never advertised) | n/a | OK | n/a (no-sweep surface) | OK, unchanged (cdr baseline) |
| 4 | PresetModal (selection.py) | OK | OK (SelectionList-native toggle) | OK (native select; no enter claim) | n/a | OK | n/a | OK, unchanged |
| 5 | TemplateMenuModal (selection.py) | OK | OK (ListView-native) | OK (native select) | n/a | OK | n/a | OK, unchanged |
| 6 | PathInputModal (selection.py) | OK | OK (Input-native submit) | OK (native submit) | OK (`#path-input` focused on_mount) | OK | n/a | OK, unchanged |
| 7 | ConfirmModal (selection.py, base) | OK | DESIGN (enter show=False — enter-confirms IS the base contract) | DESIGN (copy carries the Enter/Esc hints) | n/a | OK | n/a | DESIGN — enter-confirms by design for non-launch consumers (preset overwrite, queue cancels, wizard cancel); EHC-2 covers launch/kill only. Base byte-untouched. |
| 8 | LaunchConfirmModal (selection.py) | OK (inherited) | CHANGED (y/n show=True; enter stays hidden) | CHANGED (bold [Y]/[y]/[N]/[n]; inert enter never advertised) | n/a | CHANGED (1 new + 1 reuse constant) | n/a | CHANGED Task 1 |
| 9 | RowDetailModal (selection.py) | OK | OK (read-only) | OK | n/a | OK | n/a | OK, unchanged |
| 10 | _PickerReturnModal (run_config.py, base) | n/a (no own bindings; subclass esc) | n/a | n/a | OK (dismiss returns focus to `#cfg-picker` — the delta-B hook) | n/a | n/a | OK, unchanged |
| 11 | PreviewModal (run_config.py) | OK | OK (read-only) | OK (no enter) | n/a | OK | n/a | OK, unchanged |
| 12 | ProblemsModal (run_config.py) | OK | OK (read-only) | OK (no enter) | n/a | OK | n/a | OK, unchanged |
| 13 | EnvBlockModal (run_config.py) | OK | OK (the `[1]` hint is copy naming the SCREEN slot-1 binding — valid after esc) | OK (no enter) | n/a | OK | n/a | OK, unchanged |
| 14 | E2PhraseModal (run_config.py) | OK | DESIGN (y/n stay hidden — armed-after-blur; enter hidden, never launches) | CHANGED (bold matched [Y]/[N] carries the affordance; mismatch stays plain) | OK (`#cfg-e2-input` focused on_mount) | OK (no newly-shown labels) | n/a | CHANGED Task 1 (indicator only; keycaps hidden BY DESIGN, test-pinned) |
| 15 | ChoiceModal (run_config.py) | OK | OK (RadioSet-native first-press) | OK (native select) | OK (RadioSet focused on_mount) | OK | n/a | OK, unchanged |
| 16 | _GateConfirmModal (run_config.py) | OK (inherited) | CHANGED (inherits flipped y/n; enter hidden) | CHANGED (bold confirm line; inert enter never advertised) | n/a (RichLog pair list takes no focus-stealing measures — Pilot-pinned fallthrough) | CHANGED (inherited constants) | n/a | CHANGED Task 1 |
| 17 | DirPickerModal (run_config.py) | OK | OK (f select-dir shows `CFG_DIR_PICKER_SELECT_LABEL`; tree-native enter) | OK (tree-native expand-or-select, prevent_default-pinned) | OK (tree focused on_mount; dismiss returns focus to the origin Input) | OK | n/a | OK, unchanged |
| 18 | FailureDetailModal (monitor.py) | OK | OK (read-only) | OK | n/a | OK | n/a | OK, unchanged |
| 19 | FailuresModal (monitor.py) | OK | OK (r shows `MON_RERUN_LABEL`) | FINDING (enter hidden but DataTable-NATIVE RowSelected fires the drill — the modal binding is the unfocused fallback) | OK (table focused on_mount) | OK | n/a | OK with FINDING (low, report-only — see below) |
| 20 | KillConfirmModal (monitor.py) | OK (inherited) | CHANGED (y/n show=True; enter hidden) | CHANGED (bold [Y]/[N]; y the only stop key) | n/a | CHANGED (2 reuse constants) | n/a | CHANGED Task 1 |
| 21 | LogTailModal (monitor.py) | OK | OK (read-only auto-refresh) | OK | n/a | OK | n/a | OK, unchanged |
| 22 | CellDetailModal (monitor.py) | OK | OK (read-only) | OK | n/a | OK | n/a | OK, unchanged |
| 23 | QueueDetailModal (data_manager.py) | OK | OK (read-only) | OK | n/a | OK | n/a | OK, unchanged |
| 24 | MatrixKeyModal (matrix.py) | OK | OK (read-only) | OK | n/a | OK (data labels are data, not copy — I18N-01) | n/a | OK, unchanged |
| 25 | EnvDetailModal (env_check.py) | OK | OK (read-only) | OK | n/a | OK | n/a | OK, unchanged |
| 26 | _PathPromptModal (wizard.py) | OK | OK (Input-native submit) | OK (native submit) | OK (`#wizard-path-input` focused on_mount) | OK | n/a | OK, unchanged |
| 27 | WizardModal (wizard.py) | RULING (esc hidden too — cancel affordance lives in the step-view copy) | RULING (ALL six bindings show=False at wizard.py:564-576) | OK (enter advance hidden; step copy carries hints) | n/a (per-step Inputs) | OK (all six carry registry constants — visibility, not wording, is the question) | n/a | **NEEDS MAINTAINER RULING** — see below |

Read-only drill-down family (Help/RowDetail/Preview/Problems/EnvBlock/FailureDetail/LogTail/CellDetail/QueueDetail/MatrixKey/EnvDetail): all pass on esc-labeled + no hidden essentials — confirmed. Widget-native pickers (Preset/TemplateMenu/Choice first-press, PathInput/_PathPrompt/DirPicker input-or-tree focus): pass criteria 3/4 — confirmed.

## Report-Only Findings (maintainer items — NOT changed)

**1. WizardModal step-aware keycap visibility — NEEDS RULING (the planner's pre-seeded finding, confirmed against live code).**
All six bindings (`escape`/`enter`/`b`/`f`/`o`/`u` at wizard.py:564-576) are `show=False`. Turning them on unconditionally would MISLEAD: `f`/`o` are step-1-only (the actions no-op outside step 1) and `u` is landed-state-only (the action guards; single use per session). Honest keycaps require step-aware visibility — rebuilding the shown set per step view — which is a redesign of the wizard's binding surface, out of this task's visibility-only scope. The step-view copy currently carries the affordances. Decision needed: (a) leave as-is (copy carries it), (b) fund a step-aware keycap redesign, or (c) show only the always-valid subset (e.g. `b` on non-first steps) — each has UX trade-offs only the maintainer can rank.

**2. FailuresModal enter — LOW, report-only.**
The enter drill is DataTable-native (`on_data_table_row_selected` fires `action_drill_cursor`; the table is focused on_mount so the native event is the always-path); the hidden modal `enter` binding (`show=False`) is the unfocused fallback. No misrepresentation exists (nothing advertises enter), and the native event covers the real case — recorded for completeness; no change recommended.

**3. ConfirmModal base enter-confirms — DESIGN NOTE (not a finding).**
The plain base's enter-confirms is the designed contract for its non-launch consumers (preset overwrite selection.py:2236, queue cancels data_manager.py:1243, wizard cancel wizard.py:1495); EHC-2 (enter-refusal) deliberately covers only the launch/kill/E2 family. Byte-untouched by this task.

## Gates (DNR-6)

| Gate | Result |
|------|--------|
| `make lint` (ruff) | green — All checks passed |
| `make typecheck` (ty, `--group dev --group tui`) | green — All checks passed |
| Full pytest | **1852 passed, 7 failed — EXACTLY the 7F baseline membership**: `test_determinism` 1 (`test_chain_is_deterministic_and_matches_committed`), `test_schemas` 5 (3x `model_performance-path*`, `test_schema_bucket_counts_are_pinned`, `test_dataset_enums_match_committed_data_across_all_schemas`), `test_services_run_config` 1 (`test_storage_overview_defaults_mirror_real_consumers`). Zero new failures; all 7 new tests green. (The data-chain re-sync is the queued CI-fix batch, deliberately after this task.) |
| Node lane (`node --test tests/js/*.test.js`) | 26/26 pass |
| Snapshot goldens | sha256 of all 9 `tests/tui/__snapshots__/*.svg` BYTE-IDENTICAL to the pre-Task-1 record (combined digest `dd7b60ab12999efe…`); zero regeneration, `make snapshot-update` never run |
| Targeted (Task 1) | `test_strings_phase11.py + test_pilot_run_config.py + test_pilot_monitor.py`: 144 passed |
| Targeted (Task 2) | `test_strings_phase11.py + test_pilot_run_config.py`: 97 passed |
| Commits | PLAIN (zero attribution trailers); not pushed |

## Deviations from Plan

**1. [Rule 1 - Bug] Chinese characters in screen-file comments tripped the zero-Chinese-literals lock**
- **Found during:** Task 1 verification
- **Issue:** My DNR-1/DNR-2 reuse-rationale comments in `selection.py`/`monitor.py` quoted the zh words (启动/取消/停止/重跑) of the reused pairs; `test_monitor_module_carries_zero_chinese_literals` scans the whole module source and failed with 4 offenders.
- **Fix:** Reworded the comments to name the constants' English sides only (e.g. "MON_KILL_KEYCAP (the Kill word)"); Chinese stays in `strings.py` alone (I18N-01 single home). No code/test-semantic change.
- **Files modified:** tui/screens/selection.py, tui/screens/monitor.py
- **Commit:** 8c995da (fixed within the Task 1 commit before it landed)

Otherwise the plan executed exactly as written. `make test` stops at the pytest step on any failure, so the node lane was run separately for the Task 3 gate (same commands `make test` chains) — the lane is green 26/26.

## Self-Check: PASSED

- Commits 8c995da, b270920 are ancestors of HEAD on `autorun`.
- All 8 modified files exist and carry the changes (`git diff b33e657..HEAD --stat`: 8 files, +484/-10).
- Snapshot digest matches the pre-edit record.
