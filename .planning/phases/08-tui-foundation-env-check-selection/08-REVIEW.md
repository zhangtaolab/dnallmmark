---
phase: 08-tui-foundation-env-check-selection
reviewed: 2026-10-16T00:00:00Z
depth: quick
files_reviewed: 15
files_reviewed_list:
  - tui/__main__.py
  - tui/app.py
  - tui/screens/about.py
  - tui/screens/data_manager.py
  - tui/screens/env_check.py
  - tui/screens/matrix.py
  - tui/screens/monitor.py
  - tui/screens/nav.py
  - tui/screens/run_config.py
  - tui/screens/selection.py
  - tui/screens/wizard.py
  - tui/services/download_queue.py
  - tui/services/registries.py
  - tui/services/selection.py
  - tui/services/sweep_launcher.py
findings:
  critical: 1
  warning: 3
  info: 3
  total: 7
status: issues_found
---

# Phase 8 (scoped re-review): Code Review Report

**Reviewed:** 2026-10-16
**Depth:** quick (pattern scan + targeted read of all 15 listed files, with the 261015-c4j / 261015-ehc deltas traced cross-module; env_check WR-01..04/IN-01 cluster excluded per instructions — already fixed under 07-REVIEW)
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Scoped incremental review of the TUI delta since `2341f1c`: the c4j slot-2 live model-download overlay / slot-3 dataset-only split / slot-5 entries list, and the ehc bilingual strings registry, L live toggle, y-confirm launch gates, single-GPU serialization guard, and download-speed surfaces.

The c4j presentation split is implemented cleanly (kind filters on both slot-3 render paths and both app-forwarded handlers; the shared queue mechanism untouched). The ehc y-confirm gates and the EHC-3 single-GPU guard hold on every launch path I could trace — the service-level stage-0 backstop (`sweep_launcher.py:670-674`, `822-826`) catches the confirm-race window the screen pre-checks (`run_config.py:1871-1880`, `monitor.py:1217-1226`) can miss, and the raw `launch_argv` seam is documented-ungated by design.

The one BLOCKER is in the ehc i18n machinery itself: the L toggle (and a persisted-zh boot) leaves every module-frozen copy value — all DataTable column headers, the three state-cell vocabularies, the monitor's [f]/[t] keycaps, the wizard's step/field/quirk labels, and the run-config dir-field map — in the import-time language while the rest of the console flips. The zh-pinned test conftest imports everything under zh, so the suite and a zh-import visual pass both see a consistent UI and structurally cannot catch this. Two supporting registry collisions make `translate_value`'s documented well-definedness false in the en→zh direction.

## Structural Findings (fallow)

None provided for this review.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: The L language toggle / persisted-zh boot renders a mixed-language UI — module-frozen copy never re-resolves

**File:** `tui/screens/data_manager.py:151-170,188-194`; `tui/screens/selection.py:863-871,893-897`; `tui/screens/monitor.py:108-109,113-126`; `tui/screens/wizard.py:186-265`; `tui/screens/run_config.py:1749-1755`
**Issue:** `_t()` returns the active-language value exactly once at import; `set_language()` rebinds only the `tui/strings.py` globals. Every copy value captured into a consuming module's module-level tuple/dict/ClassVar at import is frozen forever in the boot language (`DEFAULT_LANGUAGE` = `"en"` in production, since `tui/__main__.py:45-47` imports the whole screen tree before `load_persisted_language()` runs). Affected frozen sites, all verified to carry language-divergent values (`QUEUE_COL_TASK` = `任务`/`Task`, `MON_STATE_RUNNING_SWEEP` = `● 运行中`/`● running`, `QUEUE_STATE_DOWNLOADING` = `⠋ 下载中`/`⠋ downloading`, …):

- `data_manager._QUEUE_COLUMNS` / `_MISSING_COLUMNS` / `_FULL_COLUMNS` (column headers re-added from the frozen tuples in `on_mount` and `_render_missing`) and `_STATE_CELLS` (state-cell words read at render in `_state_cell` / `_render_presence_view`)
- `selection._MODEL_COLUMNS` (headers re-added in every `_rebuild_rows`) and `_QUEUE_STATE_CELLS` (the C4J-1 live-overlay state words)
- `monitor._SWEEP_STATE_CELLS` / `_CELL_STATE_CELLS` (discovered-row and entries-row state words) and `_FAILURES_KEYCAP` / `_LOG_KEYCAP` — the latter two are worse: they are `split()`-substrings of registered values (`monitor.py:108-109`), so they are not byte-equal to any registry entry and `translate_value` returns them unchanged; even the nav-style remount re-translation cannot fix them
- `wizard.QUIRK_FIELDS`, `MODEL_STEPS`/`DATASET_STEPS` (step names via `S.WIZM_STEPS[i]` at module top), and `KINDS` (`S.WIZM_FIELD_LABELS`/`WIZD_FIELD_LABELS` captured as `KindSpec.labels`) — every wizard label and step name stays in the boot language
- `run_config._DIR_INPUT_FIELDS` (ClassVar; the ctrl+o dir-picker modal title shows the boot-language field label)

`action_toggle_language` (`app.py:1041-1042`) recomposes each screen and re-invokes its `on_mount` via `_rerender_screen` — but those on_mount bodies re-add columns/cells *from the frozen tuples*, so the recompose actively re-renders the stale language. `nav.py:83,178-194` (`_NAV_SLOTS_LANGUAGE` + re-translate at every mount) proves this bug class was known and handled — for the top bar only. With a persisted zh boot the *first* render is already mixed (zh titles/footers/help via remapped BINDINGS, en column headers/state words/keycaps/wizard labels); with an en boot the L toggle produces the same mix. The conftest zh pin makes every test import zh — the suite and a zh-import visual pass both see one consistent language and structurally miss the production en-boot path.
**Fix:** Re-derive copy at render time (the pattern `env_check.py:427-431` and `matrix.py` already follow — they read `S.*` inside `on_mount`/`compose`), converting the frozen tables to functions, e.g.:

```python
# data_manager.py — module tuple -> function; call sites unchanged in shape
def _queue_columns() -> tuple[tuple[str, str, int], ...]:
    return (
        ("task", S.QUEUE_COL_TASK, _TASK_W),
        ("state", S.QUEUE_COL_STATE, _STATE_W),
        ("progress", S.QUEUE_COL_PROGRESS, _PROGRESS_W),
        ("reconcile", S.QUEUE_COL_RECONCILE, 0),
    )
```

and likewise for `_STATE_CELLS`-style lookups (read `S.QUEUE_STATE_*` inside `_state_cell`), the wizard's `KINDS` label maps, and `run_config._DIR_INPUT_FIELDS`. For the monitor keycaps, register dedicated constants instead of splitting titles:

```python
MON_FAILURES_KEYCAP = _t("MON_FAILURES_KEYCAP", "失败清单", "Failures")
MON_LOG_KEYCAP = _t("MON_LOG_KEYCAP", "日志尾随", "Log tail")
```

(also fixes the width coupling: today the keycap silently changes if the title's `" ("` separator is ever reworded).

## Warnings

### WR-01: `translate_value` en→zh collisions — the documented well-definedness invariant is false in one direction, and the wizard's `b` label is already mistranslated

**File:** `tui/strings.py:119-140` (collisions at `APP_MODAL_BACK_LABEL`/`WIZ_BACK_LABEL` and `ENV_STATE_PENDING`/`QUEUE_STATE_PENDING`)
**Issue:** The registry contains two shared-en-value pairs with *different* zh values (verified by scanning `S._REGISTRY`): `"Back"` → `返回` (APP_MODAL_BACK_LABEL) vs `上一步` (WIZ_BACK_LABEL), and `"◌ pending"` → `◌ 待检` (ENV_STATE_PENDING) vs `◌ 待下载` (QUEUE_STATE_PENDING). `translate_value` matches by byte equality and returns the *first* hit, so en→zh is deterministic but wrong for the later-registered constants. `remap_binding_descriptions` (`app.py:346-383`) rebuilds the wizard's `b` Binding description with `返回` (the esc-back wording) instead of `上一步` on every en→zh toggle — currently invisible only because that binding is `show=False`; the docstring's claim ("Well-defined because the registry-consistency tripwire holds: every distinct zh value carried by more than one constant implies ONE en value") covers only the zh→en direction and does not protect this one.
**Fix:** Make the colliding en values distinct so byte-equality is injective in both directions, e.g. `WIZ_BACK_LABEL = _t("WIZ_BACK_LABEL", "上一步", "Back a step")` and `QUEUE_STATE_PENDING = _t("QUEUE_STATE_PENDING", "◌ 待下载", "◌ queued")` — or extend the registry tripwire test to assert injectivity en→zh too.

### WR-02: `enqueue_zenodo` ignores persist failure — the WR-04 rollback/`persist_failed` contract is missing on the bundle lane (pre-delta, verified also at 2341f1c)

**File:** `tui/services/download_queue.py:1579`
**Issue:** `enqueue` (lines 1520-1523) and `enqueue_model` (1650-1653) check `_persist_locked()`, roll back the append, and return `ACTION_PERSIST_FAILED` on an unwritable state rail; `enqueue_zenodo` discards the return value. On a read-only state root / full disk the data-manager screen toasts the bundle as enqueued (`data_manager.py:1280-1286`) while nothing was persisted — a ghost in-memory row that a restart silently drops, and the driver later hits the claim-refusal stall path instead. The screen's else-branch also renders the `already_queued` toast for any non-`enqueued` action, which would mislabel a future `persist_failed` (dead branch today only because the service never returns it). Predates this delta but remains a live correctness gap in a listed file, and this review's WR-04-fail-closed theme makes it squarely relevant.
**Fix:** Apply the sibling lanes' discipline:

```python
if self._persist_locked() is not None:
    self._entries.pop()
    return EnqueueOutcome(action=ACTION_PERSIST_FAILED, key=ZENODO_BUNDLE_KEY)
```

and give the screen a `persist_failed` toast branch (mirror `_toast_enqueue_outcome`).

### WR-03: Pressing L while an env check is in flight restarts the whole kernel run from zero

**File:** `tui/app.py:989-1010,1041-1042`; `tui/screens/env_check.py:441-449`
**Issue:** `_rerender_screen`'s docstring claims "every base screen's on_mount is population-only over instance state behind exclusive workers (re-running is idempotent)". `EnvCheckScreen.on_mount` is not population-only on its cache-miss path: it consults `cached_results()` and, on a miss, calls `run_full_check()` — so an L toggle pressed while the first check of the day is still running (state file not yet persisted) *cancels* the exclusive worker and re-executes every kernel — including the GPU matmul smoke — from scratch, resetting all rows to pending. The operator asked only for a language change and got unexpected GPU work and a restarted check. (The same-day cache-hit path is fine, which is why this survives casual use.)
**Fix:** Make the re-mount path population-only: if `self._results` already covers the kernel set (or a run is in flight), re-apply the existing results instead of consulting the cache/kernels — e.g. guard the tail of `on_mount` with `if not self._results and not <run in flight>` before choosing cache-miss → `run_full_check()`, and otherwise re-render rows from `self._results` + the last outcome.

## Info

### IN-01: `data_manager.apply_queue_progress` stores live percent/speed for KIND_MODEL keys before the ignore check — and `apply_queue_event` never pops them

**File:** `tui/screens/data_manager.py:799-800` (store) and `771-772` (early return before the pop)
**Issue:** C4J-1's contract says model ticks are "IGNORED entirely", but `self._live_percents[key] = percent` / `self._live_speeds[key] = speed` execute before the kind check, and `apply_queue_event` returns on `event.kind == KIND_MODEL` *before* the `pop()` calls — so model keys accumulate in both dicts for the session. No render effect today (render paths filter by entry kind; queue keys are unique), but it is contract drift and a latent trap if a future render path reads the dicts unconditionally.
**Fix:** Move the two stores below the `entry is None or entry.kind == KIND_MODEL or entry.state != "downloading"` guard.

### IN-02: The persisted-language filename is duplicated as an inline literal

**File:** `tui/app.py:1032` vs `tui/__main__.py:50`
**Issue:** `__main__.LANGUAGE_FILE_NAME = "language.json"` is the constant, but `action_toggle_language` writes `settings.state_dir() / "language.json"` with a bare literal. A rename in one place silently breaks the boot read (the toggle would persist a file the boot never loads — falling back to English with no error).
**Fix:** Import and use the constant in `app.py` (or move it next to `settings.state_dir()`).

### IN-03: Slot-3's present-row enqueue toast reuses a slot-2 (SEL_) constant

**File:** `tui/screens/data_manager.py:1171`
**Issue:** `action_enqueue_cursor`'s present-row guard notifies with `S.SEL_ENQUEUE_PRESENT_TOAST` — a selection-screen-prefix constant — for a data-manager interaction. I18N-01's prefix grouping exists so copy lives with its surface; if the SEL copy is later reworded for slot 2's model context, slot 3's dataset wording drifts silently.
**Fix:** Register a `DL_`-prefixed twin (or a shared neutral name) and consume it here.

---

_Reviewed: 2026-10-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
