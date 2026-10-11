---
phase: 08-tui-foundation-env-check-selection
reviewed: 2026-10-11T17:52:00Z
depth: standard
files_reviewed: 34
files_reviewed_list:
  - Makefile
  - pipeline/env_smoke.py
  - pyproject.toml
  - schemas/run_template.json
  - tests/test_env_smoke_bytes.py
  - tests/tui/conftest.py
  - tests/tui/test_import_lock.py
  - tests/tui/test_pilot_boot.py
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_matrix.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_services_env_check.py
  - tests/tui/test_services_env_gate.py
  - tests/tui/test_services_quick_check.py
  - tests/tui/test_services_registries.py
  - tests/tui/test_services_selection.py
  - tests/tui/test_services_settings.py
  - tests/tui/test_services_templates.py
  - tui/__init__.py
  - tui/__main__.py
  - tui/app.py
  - tui/screens/__init__.py
  - tui/screens/env_check.py
  - tui/screens/matrix.py
  - tui/screens/selection.py
  - tui/services/__init__.py
  - tui/services/env_check.py
  - tui/services/env_gate.py
  - tui/services/quick_check.py
  - tui/services/registries.py
  - tui/services/selection.py
  - tui/services/settings.py
  - tui/services/templates.py
  - tui/strings.py
  - tui/styles.tcss
findings:
  critical: 0
  warning: 0
  info: 10
  total: 10
status: clean
---

# Phase 8 (TUI foundation — env check + selection): Code Review Report

**Reviewed:** 2026-10-11T17:52:00Z
**Depth:** standard
**Files Reviewed:** 34
**Status:** clean (zero Critical, zero Warning)

## Summary

Iteration-3 FINAL re-review (fix-loop `--auto`), at HEAD `3cc9fed` (the WR-06
fix commit). Verdict: **clean — zero Critical, zero Warning.** The 10 prior
Info findings (IN-01..IN-10) persist unchanged at Info per the loop contract
(out of scope, not escalated). The fix loop closes.

Method: the 17 files in the fix loop's blast radius (all `tui/` source, the
three Pilot suites, the two service suites in the required scope) were
re-read in full at HEAD; commit `3cc9fed` was diffed line-by-line against the
WR-06 prescription; the WR-06 stranding mechanism was independently
re-verified unreachable (below); every iteration-1 fix site was re-checked in
the current source; the phase invariants were re-verified; and the suite was
run. Suite state: `tests/tui` + `tests/test_env_smoke_bytes.py` — 180 passed;
full non-slow lane (`pytest -m "not slow"`) — **737 passed, 1 deselected**;
`ruff check tui/ tests/tui/` and `ty check tui/` — both clean.

### WR-06 — the fix holds (stranded-guard scenario verified gone)

`3cc9fed` implements exactly the iteration-2 prescription:

- **The property** (`tui/app.py:250-260`): `below_minimum_grid` is a pure
  read of `_min_size_screen` — no side effects, no new state.
- **The drop** (`tui/screens/selection.py:1173-1174`):
  `on_selection_screen_preset_menu_loaded` returns early while
  `self.app.below_minimum_grid`. The handler is fully synchronous (no await
  between the check and the push), and both resize handling and message
  handling run on the single event loop — there is no TOCTOU window in which
  the guard state could change between check and push.
- **`action_help`** (`tui/app.py:272`) now reads the property instead of the
  private attribute — behavior-identical (the property body IS the old
  expression).
- **The regression test**
  (`tests/tui/test_pilot_selection.py:750-810`,
  `test_preset_modal_never_opens_over_the_min_size_guard`) pins the full
  sequence and **passed**: `p` at full size (worker starts) → shrink to
  60x20 (guard active, selection screen beneath it still pumping) → the
  gated read completes while the guard is up → the message is DROPPED (no
  `PresetModal` anywhere in `app.screen_stack`) → grow back →
  `SelectionScreen` active with `_min_size_screen is None` → `p` again
  opens the modal. With the drop in place, the stack at grow time is
  `[env, selection, guard]` — the guard IS the top screen, so the WR-01
  restore pop fires. The stranding mechanism (modal over guard → pop
  suppressed → orphaned guard at full size) is structurally unreachable on
  this path.

### No new Critical/Warning introduced by `3cc9fed`

Every change in the diff was adversarially checked:

- **`getters.app` TYPE_CHECKING pattern** (`tui/screens/selection.py:66-71,
  804-810`): this is textual's own documented pattern (textual 8.2.8
  `getters.py`: "To keep the type checker happy you can add this property to
  get your specific App subclass"). At runtime the `if TYPE_CHECKING:`
  block is skipped, `self.app` resolves to `MessagePump.app`, and no runtime
  import of `tui.app` occurs (which would be circular — the composition
  root imports this screen). `ty check tui/` passes — the narrowing
  type-checks.
- **Message-drop semantics**: the drop fires only while below the minimum
  grid, where no chrome is permitted by the Terminal Contract; the menu data
  is not needed afterward (re-pressing `p` re-reads); the degraded behavior
  matches `action_help`'s already-documented precedent. No legitimate state
  is lost.
- **The only other async push path was investigated and is NOT a defect**:
  the deferred `ConfirmModal` push in `_submit_save`
  (`tui/screens/selection.py:1350-1356`, deferred via `call_after_refresh`
  after the modal's own pop) is the one remaining non-synchronous screen
  push after WR-06. It cannot land over the guard: `call_after_refresh`
  posts `InvokeLater` synchronously into the app's message queue from the
  key-handler's thread, while a concurrently arriving resize can only enter
  that queue via a loop callback (`post_message` from a foreign thread →
  `call_soon_threadsafe`; real SIGWINCH → `run_coroutine_threadsafe` task —
  both deferred until the loop regains control, i.e. after `InvokeLater`).
  FIFO ordering therefore always yields `[ConfirmModal, guard]` — the modal
  lands beneath the guard and survives the grow round trip (the documented
  WR-01 behavior). **Empirically confirmed** with a scratch Pilot repro
  (blocked `custom_names()` + resize posted mid-block): stack
  `[env, selection, ConfirmModal, guard]` → grow → `[env, selection,
  ConfirmModal]` → dismiss → `[env, selection]`. No stranding. Not a
  finding.

### All 8 iteration-1 fixes still hold (re-verified in current source)

- **CR-01** (`?` markup crash): `HelpModal.compose` renders every row as a
  `rich.text.Text` content object (`tui/app.py:90`); `_binding_row`
  filters `show=False` and description-less bindings (`tui/app.py:292-309`).
  Pinned by the selection-screen `?` Pilot test (literal `/` keycap).
- **CR-02** (OSError crash): `except OSError` in `_submit_export` /
  `_submit_tiers` (`tui/screens/selection.py:1278-1284, 1296-1300` —
  in-modal problem lines) and `_do_save` (`1366-1377` — warning toast); the
  backend test pins the real `/dev/null/x.json` failure as `OSError`.
- **CR-03** (matrix degraded crash): the `_grid_composed` property plus the
  `audit_available` / `models_load_error` empty states
  (`tui/screens/matrix.py:186-214`), `is_valid_coordinate` guards in
  `_current_task_key` (`253-258`) and the selection screen's
  `action_toggle_mark` / `action_show_detail`
  (`tui/screens/selection.py:1103-1112, 1404-1409`), cursor set only with
  both entries present (`matrix.py:243-244`), `action_show_key` no-op on
  empty states (`290-291`).
- **WR-01** (guard pops wrong screen): the restore pops only when the guard
  IS the top screen (`tui/app.py:245-248`); `action_help` suppressed below
  the minimum (now via the `below_minimum_grid` property, `272-273`). Both
  min-size Pilot tests pass.
- **WR-02** (refresh race): run ids on all three worker messages
  (`tui/screens/env_check.py:269-308`), handler drops
  (`412-413, 425-427, 433-434`), `action_refresh` increments `_run_id`
  (`502`), cancellation poll before persist (`397-401`); the
  stale-interleave Pilot test passes.
- **WR-03** (tier grammar): task-omitting tier-1 pairs accepted
  (`tui/services/selection.py:213-231`) and contribute the model only
  (`253-264`); unit test passes; the schema is byte-frozen (below).
- **WR-04** (event-loop preset load): `preset_menu()` in the exclusive
  `@work(exclusive=True, thread=True)` worker
  (`tui/screens/selection.py:916-923`) crossing via `PresetMenuLoaded`;
  the gated responsiveness Pilot test passes.
- **WR-05** (machine-dependent tests): the
  `DNALLMMARK_CUSTOM_REGISTRY_DIR` empty-overlay pins cover every
  data-pinning test in `tests/tui/test_services_registries.py` and the
  backend tests in `tests/tui/test_pilot_selection.py` (incl. the
  healthy-side `== 50` assertion).

### Phase invariants re-verified — all hold

- **Services zero textual imports**: no textual import (any depth) under
  `tui/services/` (grep — only docstring mentions); the AST import-lock test
  is green.
- **env_smoke byte contract**: `git diff 098fc48..HEAD -- pipeline/env_smoke.py`
  is empty — byte-identical through the whole fix range.
- **Schema frozen (D-07)**: `git diff 098fc48..HEAD -- schemas/run_template.json`
  is empty.
- **CI workflow byte-untouched**: `.github/workflows/ci.yml` last changed at
  `fb419f6` (Phase 5).
- **Chinese copy single home**: operator-facing Chinese copy exists only in
  `tui/strings.py` (per-screen i18n gates green); the
  `tui/services/quick_check.py` docstring quote remains the iteration-2
  disposition — a comment, not rendered copy, not a finding.
- **`[tui]` group membership**: `textual>=8.2,<9` + `platformdirs` +
  `jsonschema` exactly; no `textual-dev`/`textual-serve` anywhere in
  `uv.lock`; `default-groups = ["data"]`.

## Info

### Prior Info findings — persistence note (unchanged, not escalated)

IN-01 (import-lock cannot see dynamic textual imports), IN-02 (matrix
readout renders an empty task key on the fixed model column), IN-03
(`check_dataset_dirs` traceback on a malformed registry entry —
pre-existing), IN-04 (`atomic_write` fixed `.tmp` sibling name), IN-05
(Pilot tests reach into private textual APIs), IN-06 (operator-facing
diagnostic copy authored in the services layer), IN-07 (rapid double `p`
stacks two PresetModals — cancelled worker's posted message still
delivers), IN-08 (residual TOCTOU window in the WR-02 persist guard), IN-09
(WR-04's same-class adjacent reads remain on the event loop —
`custom_names`, `import_template`, the export writes), IN-10 (matrix
datasets-degraded state renders a 0-column grid, asymmetric with the
models-degraded empty copy) — all re-encountered in this iteration's
re-read, all still present at HEAD, all remaining at Info per the
iteration-3 loop contract (out of scope, no escalation). Full write-ups and
fix suggestions for IN-01..IN-06 are preserved in the committed iteration-1
report (git history, commit `0b446bc`); IN-07..IN-10 originated in the
iteration-2 pass and the records above preserve their ledger, with the
fixer's disposition detail in `08-REVIEW-FIX.md` in the phase directory.

---

_Reviewed: 2026-10-11T17:52:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Iteration: 3 (FINAL — re-review after fix commits 0b5405e..3cc9fed)_
