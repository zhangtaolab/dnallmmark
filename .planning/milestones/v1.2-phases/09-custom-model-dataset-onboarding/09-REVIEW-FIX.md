---
phase: 09-custom-model-dataset-onboarding
fixed_at: 2026-10-12T18:57:02+08:00
review_path: .planning/phases/09-custom-model-dataset-onboarding/09-REVIEW.md
iteration: 2
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 9: Code Review Fix Report

**Fixed at:** 2026-10-12T18:57:02+08:00 (iteration 2; iteration 1 fixed at 2026-10-12T18:30:00+08:00)
**Source review:** .planning/phases/09-custom-model-dataset-onboarding/09-REVIEW.md
**Iteration:** 2 (cumulative — this report covers BOTH iterations)

**Summary:**
- Findings in scope: 8 across both iterations (1 Critical + 7 Warnings; the 8 Info findings stay out of scope per fix_scope=critical_warning)
- Fixed: 8 (6 in iteration 1 + WR-06 and WR-07 in iteration 2)
- Skipped: 0

All fixes carry targeted regression tests. Every fix was
reproduce-verified first (red test on the pre-fix code, green after
the fix) per the established discipline — iteration 2's WR-06 and
WR-07 included (details below).

## Fixed Issues

### CR-01: Non-UTF-8 custom registry file raises uncaught UnicodeDecodeError (iteration 1)

**Files modified:** `pipeline/registry_loader.py`, `tests/test_registry_loader.py`
**Commit:** ad7213a
**Applied fix:** Added `UnicodeDecodeError` to the EXISTING except tuple in
`_load_registry` (additive — registry_loader stays the only pipeline change).
A GBK-encoded custom file now converts to the contracted named `SystemExit`
("not readable JSON: ..."), which the selection-screen tolerant seam
(`_load_entries`, degrading on `OSError`/`SystemExit`) already handles.
Regression test `test_non_utf8_custom_file_fails_loud_naming_file` mirrors
the malformed-JSON test with `path.write_bytes('{"k": "自定义"}'.encode("gbk"))`.
Reproduce-verified: raw `UnicodeDecodeError` traceback pre-fix, SystemExit
naming the file post-fix. Module suite 24/24 green. VERIFIED COMPLETE by the
iteration-2 re-review.

### WR-01: Read side honors DNALLMMARK_CUSTOM_REGISTRY_DIR but the write seam does not (iteration 1)

**Files modified:** `tui/services/custom_entries.py`, `tests/tui/test_services_custom_entries.py`, `tests/tui/test_services_about.py`
**Commit:** 9d6bd75
**Applied fix:** Routed the write rail through the same env-aware root
resolution the read side uses: new `_env_aware_config_root()` resolves
`DNALLMMARK_CUSTOM_REGISTRY_DIR` (whole-dir override) first, falling back to
`settings.config_dir()`. `custom_registry_path`'s default base is now this
root, so `land`/`undo`/`set_enabled`/`export_registry` and the default read
all describe ONE file; the explicit `registry_dir` injection (the 09-06
selection backend) still wins. Reproduce-verified with
`test_single_overlay_pin_routes_writes_to_the_pinned_root`. Also updated
`_pin_config_roots` in test_services_about.py. Wizard/selection-custom
Pilot suites re-run green (52/52). VERIFIED COMPLETE by the iteration-2
re-review (one documented residual divergence recorded as IN-08, Info).

### WR-02: Missing official registry raises OSError across the gauntlet service boundary (iteration 1)

**Files modified:** `tui/services/gauntlet.py`, `tests/tui/test_services_gauntlet.py`
**Commit:** 569654e
**Applied fix:** `_dry_run_counterpart` absorbs the official-registry read
(`OSError`/`json.JSONDecodeError`) and returns `(None, diagnostic)`;
`dry_run_precheck` converts that into the `official_registry_unreadable`
failed item. Regression test
`test_missing_official_registry_yields_failed_item_not_exception`
reproduce-verified: FileNotFoundError escaped pre-fix; failed item
post-fix, nothing launched. The iteration-2 re-review found the tuple
still missed `UnicodeDecodeError` — closed by WR-06 below.

### WR-03: Import lane accepts metrics and model types the wizard lane rejects (iteration 1)

**Files modified:** `tui/services/custom_validation.py`, `tests/tui/test_services_custom_validation_import.py`
**Commit:** b0e2812
**Applied fix:** Schema stayed frozen (byte-untouched) — the fix is in the
Python validation layer: `validate_import_document` runs the SAME
vocabulary checks the wizard lane runs, over the same `_check_enum` seam —
model `type` against `MODEL_TYPE_VALUES`, dataset `metric` against the
injected `sources.metric_registry`. Three regression tests, all confirmed
failing pre-fix; 68/68 green across both validation modules post-fix.
VERIFIED COMPLETE by the iteration-2 re-review.

### WR-04: Import/export file I/O runs on the event loop (iteration 1)

**Files modified:** `tui/screens/wizard.py`, `tests/tui/test_pilot_wizard.py`
**Commit:** a056f90
**Applied fix:** Moved the f/o I/O into exclusive thread workers per D-03
(the PresetMenuLoaded pattern). `_PathPromptModal` runs the injected
`validate` seam in `@work(exclusive=True, thread=True)` and posts a
`Validated` message back; `action_do_export`'s empty-state probe moved into
`_check_export_state` posting `ExportStateReady`, guarded by the
live-screen staleness check. Pilot helpers `_submit_path`/
`_press_step_one_key` settle the workers; gated test
`test_import_validation_runs_off_the_event_loop` proves the console stays
responsive while the read is in flight. The iteration-2 re-review verified
the I/O offload but found the `Validated` handler unguarded against
multi-event interleavings — closed by WR-07 below.

### WR-05: tui/services/about.py carries Chinese literals and no i18n lock covers it (iteration 1)

**Files modified:** `tui/services/about.py`, `tui/services/quick_check.py`, `tests/tui/test_services_about.py`
**Commit:** d38ca1a
**Applied fix:** Anglicized every Chinese literal in about.py and
quick_check.py docstrings/comments; operator-facing copy stays only in
`tui/strings.py`. Extended the lock: new
`test_every_services_module_carries_zero_chinese_source` scans EVERY
`tui/services/*.py`. about suite 21/21 green. VERIFIED COMPLETE by the
iteration-2 re-review (independent whole-tier scan: zero CJK).

### WR-06: WR-02 absorption tuple misses UnicodeDecodeError — official-registry read can still raise across the gauntlet service boundary (iteration 2)

**Files modified:** `tui/services/gauntlet.py`, `tests/tui/test_services_gauntlet.py`
**Commit:** 8b11702
**Applied fix:** Added `UnicodeDecodeError` to the existing except tuple in
`_dry_run_counterpart` (`except (OSError, json.JSONDecodeError,
UnicodeDecodeError)`) with a comment recording the sibling-not-subclass
reasoning — mirroring CR-01's loader-seam fix one-for-one; the tuple entry
is the ONLY change (services tier stays zero-textual). A non-UTF-8 official
registry now degrades to the same `official_registry_unreadable` failed
item instead of killing the wizard's gauntlet worker. Reproduce-verified:
new sibling test `test_gbk_official_registry_yields_failed_item_not_exception`
stages a `repo_root` whose official datasets registry is
`'{"k": "自定义"}'.encode("gbk")` — pre-fix the raw `UnicodeDecodeError`
traceback escaped through `_official_registry`/`json.load` (observed red);
post-fix the failed item posts and nothing launches. Gauntlet suite green.

### WR-07: WR-04's Validated handler lacks the module's own liveness/generation discipline (iteration 2)

**Files modified:** `tui/screens/wizard.py`, `tests/tui/test_pilot_wizard.py`
**Commit:** 6a578d3
**Applied fix:** `_PathPromptModal` now carries the module's async-message
discipline end to end:
- `Validated` carries a `generation` tag; every submit bumps the modal's
  generation counter and passes it into the worker, so the tag is captured
  on the event loop BEFORE the I/O (superseded submits are distinguishable
  even though `exclusive=True` cancels only the worker object while its
  thread runs to completion and posts).
- `on_path_prompt_validated` drops a superseded verdict
  (`generation != current`) and drops a verdict on a non-live modal
  (`self.app.screen is not self` — the same ExportStateReady discipline),
  eliminating the double-`dismiss()` (which popped the wizard beneath the
  already-popped modal via `pop_screen()`'s unconditional stack-top pop)
  and the cancelled/superseded accept landing an import on the detached
  wizard (u-undo unreachable).
- The wizard-side `_pending_import` stash is keyed by generation (written
  by `validate(path, generation)`, popped by `accept(path, generation)`),
  closing the last-writer-wins cross-consumption race; the export seams
  take the same `(path, generation)` shape and ignore the tag.
Reproduce-verified with deterministic gated Pilot tests BEFORE the fix:
`test_superseded_submission_is_dropped_current_one_accepts` (two
per-path-gated overlapping submissions) failed 4/4 pre-fix with exactly
the reviewer's signature — `_phase == "gauntlet"` (an accept fired and
landed) while `app.screen` was `EnvCheckScreen` (the wizard itself was
popped off the stack by the second dismiss: double-dismiss + cancelled
accept on the detached wizard in one run). Post-fix it is green 12/12
consecutive runs; settling uses a bounded poll on the observable end
state rather than `wait_for_complete()` (which raises `WorkerCancelled`
on the deliberately-cancelled superseded worker node).
`test_esc_during_slow_validation_drops_stale_verdict` (esc during a gated
read; the worker posts after the pop) asserts the wizard stays the top
screen and no import lands — it passed even pre-fix in this interleaving
(that run's pump had closed before the post), so it stands as the
regression guard for the esc window the reviewer verified from the pinned
Textual source; the superseded-submission test carries the
reproduce-verified burden.
**Note:** fixed: requires human verification — the guard logic
(generation capture ordering, liveness check placement before the
dismiss branch, generation-keyed stash pop) is logic-shaped; the Pilot
tests pin the two named failure modes but cannot exhaust the interleaving
space.

## Verification

**Iteration 2 gates (all green, run in the isolated worktree
`.claude/worktrees/rf-09-52584-1791801604` on branch
`gsd-reviewfix/09-52584`, using the main checkout's `.venv` binaries —
the worktree has no venv of its own, so these numbers are reproducible
from the main checkout only after the fast-forward):**

- `make lint` equivalent (ruff over the exact Makefile file list, main
  `.venv` binary): All checks passed
- `make typecheck` equivalent (`ty check --python <main .venv>/bin/python`):
  All checks passed
- `make test` equivalent: pytest 954 passed (166s, up from 951 — the three
  new regression tests); `node --test tests/js/*.test.js` all pass,
  0 fail

**Iteration 1 gates:** ruff All checks passed; ty All checks passed;
pytest 951 passed (163s); node tests 18 pass / 0 fail.

**Invariants re-verified (iteration 2):** zero `textual` imports across
`tui/services/` (the WR-06 change is the except tuple + comment only);
`.github/workflows/ci.yml`, `pipeline/env_smoke.py`, and `schemas/`
byte-untouched (`git diff d38ca1a..HEAD` empty for all three); zero CJK
in both touched source files; official registries never written; the
superseded-worker `WorkerCancelled` flake was eliminated from the new
test (12/12 stable runs).

---

_Fixed: 2026-10-12T18:57:02+08:00_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2 (cumulative: iterations 1 + 2)_
