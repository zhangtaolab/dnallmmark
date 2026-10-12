---
phase: 09-custom-model-dataset-onboarding
reviewed: 2026-10-12T11:03:51Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - tui/services/gauntlet.py
  - tui/screens/wizard.py
  - tests/tui/test_services_gauntlet.py
  - tests/tui/test_pilot_wizard.py
  - pipeline/registry_loader.py
  - tui/services/custom_entries.py
  - tui/services/custom_validation.py
findings:
  critical: 0
  warning: 0
  info: 8
  total: 8
status: clean
---

# Phase 9: Code Review Report (Re-review, iteration 3 — FINAL)

**Reviewed:** 2026-10-12T11:03:51Z
**Depth:** standard
**Files Reviewed:** 7 (the iteration-3 scope — the two fix diffs' four files, plus the three iteration-1 fix sites re-confirmed at HEAD)
**Status:** clean — 0 Critical, 0 Warning; the 8 iteration-2 Info findings persist (not escalated, per the iteration contract)

## Summary

Final re-review of the two iteration-2 warnings. **Both are verified fixed
against source, pinned Textual behavior, and red→green reproduction tests.**
No new Critical or Warning was found in either fix diff. All six iteration-1
fixes were re-confirmed at HEAD. Verification runs this iteration: 160 tests
green across the six fix-pinned test files (`tests/tui/test_services_gauntlet.py`,
`tests/tui/test_pilot_wizard.py`, `tests/test_registry_loader.py`,
`tests/tui/test_services_custom_validation_import.py`,
`tests/tui/test_services_about.py`, `tests/tui/test_services_custom_entries.py`).

### Fix-by-fix verification

1. **WR-06 — VERIFIED.** `tui/services/gauntlet.py:522-529`:
   the absorb tuple is now `(OSError, json.JSONDecodeError,
   UnicodeDecodeError)` with the correct sibling-not-subclass reasoning in the
   comment. The failed-item path is complete: `_dry_run_counterpart` returns
   `(None, repr(exc))`, and `dry_run_precheck` (`gauntlet.py:214-229`) converts
   it into the `official_registry_unreadable` failed item with the diagnostic
   as `raw_output` — nothing launched. The GBK sibling test is present and
   passing (`tests/tui/test_services_gauntlet.py:247-272`:
   `'{"k": "自定义"}'.encode("gbk")` written as the official datasets
   registry, asserting `details[0] == "official_registry_unreadable"` and
   `runner.calls == []`). The service-boundary asymmetry (JSON-corrupt → item,
   GBK → crash) is closed.
2. **WR-07 — VERIFIED.** All four sub-checks hold at
   `tui/screens/wizard.py`:
   - **Generation capture ordering** (`wizard.py:500-501` → `:504`):
     `on_input_submitted` increments `self._generation` ON the event loop and
     passes the value as a worker ARGUMENT — `_validate_in_worker(value,
     self._generation)` binds the generation at call time, before any thread
     I/O; the worker never reads `self._generation` from its thread. This is
     the iteration-2 suggested shape, strictly stronger (parameter binding
     instead of a cross-thread attribute read).
   - **Liveness guard** (`wizard.py:529-530`): `if self.app.screen is not
     self: return` — the ExportStateReady discipline (`wizard.py:1581`),
     closing the esc-during-validation double-dismiss (the second
     `pop_screen()` popping the wizard) and the cancelled-accept landing.
   - **Stash generation keying** (`wizard.py:671, 1611-1614, 1621`):
     `_pending_import` is a per-generation dict; the worker writes
     `_pending_import[generation]` BEFORE `post_message` (happens-before via
     the message queue), and `_accept_import_path` pops only its own
     generation. Cross-modal collisions are safe: a reopened prompt restarts
     generations at 1, but its worker always overwrites the slot before its
     own accept can pop it, and a stale modal's accept is dropped by the
     liveness guard; the read-error path pops the slot.
   - **No new dead-path**: the FIRST submit's verdict always lands —
     generation 0→1 matches, and the modal is the top screen. Proven by the
     passing WR-04 test (`test_import_validation_runs_off_the_event_loop` —
     first submit's problems report renders, modal stays open) and by the
     superseded-submission test asserting the CURRENT submission's clean
     verdict dismisses exactly once and accepts into the gauntlet.
   - Reproduction tests are real pilot tests with deterministically gated
     worker threads (no sleeps):
     `test_esc_during_slow_validation_drops_stale_verdict` (esc mid-read →
     stale verdict dropped; wizard stays live, phase stays `form`) and
     `test_superseded_submission_is_dropped_current_one_accepts` (both reads
     gated in flight; asserts exactly one dismiss, gauntlet queue `["ds-b"]`
     — the current submission's own document).
3. **No new Critical/Warning from the two fix diffs.** The WR-06 diff adds
   one exception class to an existing tuple plus its test. The WR-07 diff's
   signature change (`validate(path, generation)` / `accept(path,
   generation)`) is carried by both seam implementations and both prompt call
   sites (`wizard.py:1536-1542, 1586-1592`); the only `Validated`
   constructor and handler are inside `_PathPromptModal`; the export lane
   documents its unused generation parameter as the shared seam shape. No
   other caller of the changed seams exists (verified by grep).
4. **The six iteration-1 fixes hold at HEAD** (re-confirmed this iteration):
   - **CR-01**: `pipeline/registry_loader.py:132` tuple + fail-loud
     `SystemExit`; GBK regression test in `tests/test_registry_loader.py`
     (passing).
   - **WR-01**: `_env_aware_config_root` (`custom_entries.py:108`) with read
     and write routed through `custom_registry_path` (`:167, :195`).
   - **WR-02**: superseded by WR-06 (verified above).
   - **WR-03**: the import lane runs `_check_enum` on model `type` and
     dataset `metric` (`custom_validation.py:228-285`); parity tests passing.
   - **WR-04**: superseded by WR-07 (verified above).
   - **WR-05**: independent whole-tier scan this iteration found zero CJK
     across all `tui/services/*.py` modules.
5. **Phase invariants hold**: no fix commit touched `schemas/` or `.github/`
   (last commits there are 517f821 / 4146d15, pre-dating the review fixes —
   CI byte-untouched, schemas frozen); the gauntlet still stages only into
   `TemporaryDirectory` overlays and never writes user-owned registries; the
   services tier stays import-clean of textual (zero-CJK scan above).

## Info

The 8 iteration-2 Info findings persist unchanged (recorded, not escalated,
per the iteration contract):

- **IN-01**: Dead None-guard on a raising API — `tui/screens/wizard.py:917`
  (`query(...).first(Static)` raises `NoMatches` on empty; use
  `_first_or_none`).
- **IN-02**: Private textual API `_push_result_callback` in the
  composition root (`tui/screens/selection.py`).
- **IN-03**: `action_undo_landed` toasts success unconditionally without
  checking the `_undo` return (`tui/screens/wizard.py:1428-1430`).
- **IN-04**: Import-mode group heads always styled `_ROW_STYLE_PASS`
  regardless of group outcome (`tui/screens/wizard.py:1119-1124`).
- **IN-05**: Nondeterministic metric-enumeration order in
  `WIZ_PROBLEM_ENUM` messages (`tui/services/custom_validation.py:356-358`;
  `sorted(allowed)`).
- **IN-06**: Version-pinned literal `"0.7.1"` in
  `tests/tui/test_services_about.py:307`.
- **IN-07**: Second app block indented inside the first scenario in the
  stale-run test (`tests/tui/test_pilot_wizard.py`) — readability only.
- **IN-08**: WR-01 residual — a `DNALLMMARK_TUI_CONFIG_DIR`-only pin splits
  the TUI store from the pipeline overlay view
  (`tui/services/custom_entries.py:108-131`; documented in the docstring).

---

_Reviewed: 2026-10-12T11:03:51Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (re-review, iteration 3 — FINAL; fix commits 8b11702 + 6a578d3 verified, iteration-1 fixes re-confirmed at HEAD)_
