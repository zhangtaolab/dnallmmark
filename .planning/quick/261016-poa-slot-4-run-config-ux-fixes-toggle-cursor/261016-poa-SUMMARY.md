---
phase: quick-261016-poa
plan: 01
subsystem: tui
tags: [tui, run-config, ux, launch-confirmation, goldens]
requires: [phase-11, phase-12, quick-261015-ehc]
provides: [ux1-toggle-anchor, ux2-marked-row-contrast, ux3-launch-confirmation-term, ux4-entry-hint, ux5-pair-task-list, ux6-yn-cancel]
affects: [tui/screens/run_config.py, tui/screens/selection.py, tui/services/sweep_launcher.py, tui/strings.py, tui/styles.tcss, docs/TUI-GUIDE.md, docs/TUI-DEMO.md]
status: complete
actuals:
  tasks: 3
  commits: 5
  tokens: 41000
commits:
  - 5729d36 "test(261016-poa): RED — picker toggle anchor + contrast-scope pins"
  - 6b14a0f "feat(261016-poa): picker toggle keeps cursor + scroll anchor; marked-row contrast"
  - 36e60e7 "test(261016-poa): RED — launch-confirmation task list, Y/N cancel, entry hint pins"
  - cf6335c "feat(261016-poa): launch confirmation — pair task list, N cancel, entry hint, terminology"
  - 14944f9 "docs(261016-poa): launch-confirmation terminology sweep + new-affordance docs"
key_files:
  created:
    - .planning/quick/261016-poa-slot-4-run-config-ux-fixes-toggle-cursor/261016-poa-SUMMARY.md
    - .planning/quick/261016-poa-slot-4-run-config-ux-fixes-toggle-cursor/RED-EVIDENCE.json
  modified:
    - tui/screens/run_config.py
    - tui/screens/selection.py
    - tui/services/run_config.py
    - tui/services/sweep_launcher.py
    - tui/strings.py
    - tui/styles.tcss
    - tests/tui/test_pilot_run_config.py
    - tests/tui/test_services_sweep_launcher.py
    - tests/tui/test_strings_phase11.py
    - tests/tui/test_pilot_env_check.py
    - tests/tui/test_pilot_monitor.py
    - docs/TUI-GUIDE.md
    - docs/TUI-DEMO.md
    - docs/ARCHITECTURE.md
    - README.md
    - .planning/STATE.md
---

# Quick Task 261016-poa: Slot-4 Run-Config UX Fix Batch — Summary

Slot 4 (run config) live-feedback batch from the maintainer's 2026-10-16
hands-on round plus the original-design alignment: toggle anchor
preservation, marked-row contrast, 启动门→启动确认 terminology, the
enter/Y/N entry hint, the service-derived planned-pair task list in the
confirm modal, and Y/N confirmation on every launch confirm.

## ⚠ D-03 HAND-OFF — regenerated run_config.svg is UNCOMMITTED, awaiting maintainer review

`make snapshot-update` regenerated `tests/tui/__snapshots__/run_config.svg`
(the ONLY regen path). The file sits in the working tree, deliberately
NOT committed — the D-03 review goes through the orchestrator to the
maintainer. The local suite compares against the on-disk file and is
green. One-line open command:

    git diff tests/tui/__snapshots__/run_config.svg

Expected delta — exactly three causes (everything else is the SVG
terminal-class hash rename + one-row layout shift churn):

1. **Footer label** (UX-3): the enter binding label reads 启动确认
   (was 启动门) — `LNC_GATE_TITLE` (`tui/strings.py:1453`).
2. **New hint row** (UX-4): `回车 打开启动确认 · Y 启动 / N 取消`
   (`CFG_GATE_HINT`, `tui/strings.py:1432`) renders directly below the
   preview line (`tui/screens/run_config.py:1280`); the picker column
   and `#cfg-columns` shrink one row to fit.
3. **Marked-row contrast** (UX-2): model-a/model-b rows (the fixture's
   marks) render `#8ad4a1` (text-success) with `font-weight: bold` over
   a new `#2f2f2f` background class ($boost) — the PickerList-scoped
   rule at `tui/styles.tcss:568-571`.

After maintainer sign-off, commit the SVG together with this round (the
queued follow-up); the eight other goldens rewrote byte-identical and
need nothing.

## Per-item what/where

| Item | What landed | Where |
|------|-------------|-------|
| UX-1 toggle anchor | `set_rows(anchor_key=...)`: capture `scroll_offset.y` before `clear_options`, restore `highlighted` by KEY, then `scroll_to(y=prev_y)` + a `call_after_refresh` re-assert — final authority over the 8.2.8 `watch_highlighted` edge-snap; threaded `_render_picker(anchor_key)` → `_apply_spec_change(picker_anchor=...)` (consumed before the spec replace, never a spec field); both toggle paths pass the key, all other call sites stay anchor-less (index clamp unchanged) | `tui/screens/run_config.py:440-484` (set_rows), `:1469` (_render_picker), `:2120-2132` (_apply_spec_change), `:1658-1678` (SelectionToggled), `:1719-1741` (action_toggle_mark) |
| UX-2 marked-row contrast | `PickerList > .selection-list--button-selected[-highlighted]` override: `background: $boost; text-style: bold` (8.2.8 default was color $text-success on $panel); scoped to the PickerList TYPE selector ONLY — the selection preset picker + wizard enum lists keep the default, their goldens byte-identical | `tui/styles.tcss:559-571` |
| UX-3 terminology | `LNC_GATE_TITLE` zh 启动确认 / en Launch Confirmation; `ENV_VERDICT_CRITICAL_FAIL` zh/en reworded; LNC section comment renamed; living code prose swept (`run_config.py` screen+service, `selection.py`, test docstrings); docs swept (TUI-GUIDE 8 sites, TUI-DEMO 6 + anchor, README 1, ARCHITECTURE 1 — a living-prose site the plan's enumeration missed) | `tui/strings.py:276-279, 1428-1470`; docs per Task 3 |
| UX-4 entry hint | `CFG_GATE_HINT` (zh+en) rendered as the dim `#cfg-gate-hint` row (existing `.cfg-hint` class) immediately after `#cfg-preview-line` | `tui/strings.py:1432-1434`; `tui/screens/run_config.py:1278-1281` |
| UX-5 pair task list | `GateSummary.pairs` (defaulted trailing field): service-side ordered first-occurrence (model, task) dedupe over the FRESH preview cells in `gate_confirm_data` — seeds stay in the counts formula, 3-tuple and curve 4-tuple cells project identically; `_GateConfirmModal(pairs=...)` renders the message + bounded `#cfg-gate-log` (max-height 14) + footer, first 12 pairs then `LNC_GATE_PAIRS_MORE` total (`_GATE_PAIR_CAP = 12`); mount passes `pairs=summary.pairs`; UI renders, never computes | `tui/services/sweep_launcher.py:258-291, 413-453`; `tui/screens/run_config.py:808-847, 2025`; `tui/styles.tcss:666-673, 636-644` |
| UX-6 Y/N | `LNC_GATE_CONFIRM` zh 确认启动以上训练？— [Y] 启动 / [N] 取消 (en counterpart); `LNC_E2_MATCH_OK` synced to the [Y]/[N] pair; hidden `n`=dismiss on `LaunchConfirmModal` BASE (slot-4 gate + monitor [f] re-run inherit; ConfirmModal and non-launch consumers untouched) and on `E2PhraseModal` (armed only after the y-ready blur — while the Input holds focus n types); enter stays the documented no-op everywhere (EHC-2 preserved — existing enter-noop / y-launch assertions pass unmodified) | `tui/strings.py:1459-1462, 1484-1486`; `tui/screens/selection.py:1223-1249`; `tui/screens/run_config.py:693-697` |

## RED-first evidence (UX-1)

Command (RED commit 5729d36):

    uv run --group dev --group tui pytest tests/tui/test_pilot_run_config.py \
      -q -k "toggle_deep_row or screen_space_toggle or contrast or clamp"
    → 3 failed, 1 passed

- `test_space_toggle_deep_row_keeps_cursor_key_and_scroll_offset`: failed
  `assert picker.scroll_offset.y == before_y` — **was 6, is 3**: the
  8.2.8 rebuild snap (clear_options scroll reset + watch_highlighted
  force-scroll) re-landed the cursor row on the viewport's bottom edge;
  the failure delta equals exactly the 3 up-steps of the fixture. The
  KEY assertion already passed pre-fix (the index clamp preserved the
  row) — the scroll was the bug, and the test pinned it.
- `test_screen_space_toggle_...`: same failure on the screen-level path.
- `test_styles_carry_picker_scoped_selected_contrast_rule`: failed the
  presence pin (no rule existed).
- `test_filter_and_kind_flip_rebuilds_keep_index_clamp`: PASSED pre-fix
  by design (regression pin of today's behavior).
- Full record (command/output/expected/actual/semantic assessment) in
  `RED-EVIDENCE.json` in this directory. `gsd_run check tdd-red-evidence`
  could not run (gsd_run absent on this machine); the manual semantic
  assessment is recorded there instead.

Task 2 RED (commit 36e60e7): the four UI tests failed on the planned
behavior (pair log missing, n left the modals up, hint row missing);
the service pairs tests were written against the already-landed service
contract per the plan's strings/service-first sequencing.

## Golden scope verification (D-03)

    $ make snapshot-update
    → 9 goldens regenerated
    $ git status --porcelain tests/tui/__snapshots__/
     M tests/tui/__snapshots__/run_config.svg

Eight of nine byte-identical (env_check, selection_models,
selection_datasets, data_manager, data_manager_presence,
monitor_running, monitor_empty, wizard); exactly ONE drift:
run_config.svg — the designed 8-identical/1-drift state, UNCOMMITTED
for the maintainer review (see the hand-off block above). The golden
suite passes against the regenerated on-disk file.

## Deliberate exclusions

- **`docs/demo/casts/*.cast`, `docs/demo/gifs/*`, `docs/demo/RECORDED.md`
  untouched** — point-in-time recordings of the old build; the queued
  demo re-record task regenerates them, and editing recordings would
  falsify them. TUI-DEMO's keymap table marks the n row + pair list as
  postdating the recording.
- **`pipeline/env_smoke.py` "(the E2' launch gate)" kernel-output
  phrase untouched** (with its byte-pinned quotes in
  `tests/test_env_smoke_bytes.py`, `tests/tui/test_pilot_env_check.py:153,368`,
  `tests/tui/test_pilot_data_manager.py:2489`): env_smoke is the frozen
  08-01 byte-golden face — outside the plan's file scope; changing its
  output would break the frozen-face contract. These are the only
  remaining "launch gate" occurrences outside `docs/demo/` and
  `.planning/` history, and they are frozen DATA, not living prose.

## Final gate numbers

- `make lint` — green; `make typecheck` — green.
- `make test` — pytest **7 failed / 1818 passed** at EXACTLY the 7F
  baseline membership (test_determinism 1, test_schemas 5,
  test_services_run_config 1 — identical to the pre-change baseline of
  7F/1808P; the +10 passed are this round's new tests, zero new
  failures); node --test **26/26**.
- i18n: every strings change carries zh+en; the three new constants
  (CFG_GATE_HINT, LNC_GATE_PAIR_LINE, LNC_GATE_PAIRS_MORE) registered
  in the bidirectional inventory; zh/en injectivity holds (registry
  tripwires green).
- Terminology: `grep 启动门 tui/ tests/` clean; `grep "launch gate"
  TUI-GUIDE TUI-DEMO README ARCHITECTURE` clean (exclusions above).
- Commits: plain, zero attribution trailers; nothing pushed; the
  regenerated run_config.svg NOT among the commits.
