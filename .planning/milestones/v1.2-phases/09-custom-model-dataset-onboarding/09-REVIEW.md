---
phase: 09-custom-model-dataset-onboarding
reviewed: 2026-10-14T21:55:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - tests/tui/test_pilot_env_check.py
  - tests/tui/test_pilot_nav_shell.py
  - tests/tui/test_pilot_selection_custom.py
  - tests/tui/test_pilot_selection.py
  - tests/tui/test_pilot_wizard.py
  - tests/tui/test_services_about.py
  - tests/tui/test_services_custom_entries.py
  - tests/tui/test_services_gauntlet.py
  - tui/app.py
  - tui/screens/env_check.py
  - tui/screens/selection.py
  - tui/services/about.py
  - tui/services/gauntlet.py
  - tui/strings.py
  - tui/styles.tcss
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 09: Code Review Report (incremental — delta since aecf4011b9)

**Reviewed:** 2026-10-14T21:55:00Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Incremental adversarial review of the 16 in-scope Phase-09 deliverable files as changed since the converged base `aecf4011b9` (via phases 10-12, quick tasks 261014-l6h/mlc/dcl/f4w, and the 08-08/08-09 gap-closure rounds). The delta on this surface is substantial: `tui/app.py` gained the download-queue driver spine, monitor-switch wiring, and the D-06 exit modal; `tui/screens/selection.py` was reshaped to the models-only MLC-02 surface (compat/download columns, pool toggle, `d` model-download lane) plus the 08-08/08-09 card guards; `tui/screens/env_check.py` gained the model_dirs row, per-kernel routing, the WR-01 never-exit worker guards, `exit_on_error=False`, and the F4W-04 storage overview; `tui/services/gauntlet.py` adds `errors="replace"`; `tui/services/about.py` is a docs-only 62→59 count correction.

Verification evidence: all 218 tests across the eight in-scope suites pass (149.5s); `ruff check` and `ty check` pass on every in-scope source file. Cross-module facts verified directly against textual 8.2.8 source: the `@work(exclusive=True)` cancel scope is node-bound (`WorkerManager.add_worker` → `cancel_group(worker.node, ...)`), so the app-node driver and screen-node read workers cannot cancel each other — the shared default group is safe. The driver's WR-02 lost-wakeup guard (lock-scoped check-and-set in `kick_download_queue` vs release-and-recheck in the drain exit) was traced and is correct. The 08-09 card guards (type-tolerant vocabularies in `build_wizard`, `isinstance(card, dict)` in `_open_detail` and `_manual_landing_path`) are present and pinned by RED-then-GREEN tests.

Phase-07 verifier CR-01 seam assessment (as instructed): no in-scope delta touches the wizard→pipeline field contract. `WIZM_FIELD_LABELS`/`WIZD_FIELD_LABELS` are byte-identical to the base; `build_wizard`'s `ValidationSources` construction changed only in vocabulary tolerance (which fields are *required* is unchanged, living in the untouched `custom_validation.py`); `gauntlet.py` changed only its decode policy. The standing CR-01 (schema declares `Mean_token_length`/`length`/`Model_name` optional while `run_finetune.py` hard-indexes them — a candidate can pass the dry-run/audit gauntlet and still crash at first training step) remains open at the unchanged schema/validator seam and is unaffected by this delta; it stays flagged for the schema-side fix, not this phase's surface.

No Critical findings. Three Warnings (one operator-facing data inconsistency in the exit modal; two event-loop I/O sites in the new delta that violate the module's own D-03 worker discipline — the exact class the prior WR-04 round fixed for the preset menu) and three Info items.

## Warnings

### WR-01: ExitModal renders the attached sweep's progress counts under the launcher root's name

**File:** `tui/app.py:835-849`
**Issue:** `action_quit` prefers `root = roots[0] if roots else attached_root`, but `done`/`total` are unconditionally taken from `self._monitor_screen.attached_running_counts()` whenever a monitor screen exists. When the launcher registry has a live sweep at root A (TUI-launched) while the monitor is attached to a different root B (e.g. a CLI-launched sweep — the exact case the `attached_running` leg exists for), `LNC_EXIT_MESSAGE` names A but displays B's 完成 {done}/{total}. The same mixing occurs with a *finished* attached sweep: its stale counts label root A. The modal's `[k]` kill target is at least self-consistent with the displayed name (both use `root`), but the progress numbers shown next to a kill/detach decision describe a different running sweep — misleading data in a destructive-choice gate, and the maintainer's own workflow (monitor supports attaching multiple roots) makes the two-roots state routine.
**Fix:** Derive the counts from the same sweep that names the modal — when `roots` is non-empty, use absent markers for `done`/`total` (the launcher carries no progress, per the class docstring) instead of the attached sweep's:

```python
if roots:
    root = roots[0]
    done = CFG_VALUE_ABSENT
    total = CFG_VALUE_ABSENT
elif attached_running:
    root = attached_root
message = LNC_EXIT_MESSAGE.format(done=done, total=total, root=Path(root).name)
```

(Or surface both sweeps and let the modal name which one `[k]` targets.)

### WR-02: The slot-1 storage overview runs `load_state()` + five `Path.exists()` stats synchronously on the event loop — violating the module's own D-03 lock

**File:** `tui/screens/env_check.py:613-648` (called at `env_check.py:438` and `env_check.py:609`; real backend at `env_check.py:202-207`)
**Issue:** `_render_storage` calls `self._service.storage_rows()` directly inside `on_mount` and `action_refresh` — both event-loop contexts. The real `EnvCheckBackend.storage_rows` delegates to `run_config_service.storage_overview()`, which performs a `load_state()` JSON read (seeding reads `directories.json` + `run_config.json` under XDG) and five `Path.exists()` stats (confirmed in `tui/services/run_config.py::storage_overview`). The env-check module contract states "every file-reading service call … runs in an exclusive worker (… none ever blocks the event loop)" — this is the exact WR-04 class the prior rounds fixed for the selection screen's preset-menu read (`_load_preset_menu`). An operator with the model/dataset/output root on a network mount (a first-class scenario for a 40GB-per-model benchmark) gets a frozen console at boot and on every `[r]`.
**Fix:** Route the read through the existing exclusive-worker pattern (a `StorageRowsLoaded` message posted from a `@work(exclusive=True, thread=True)` worker; the cache-hit mount path can post the message immediately after starting the worker, keeping the loading state row-neutral), mirroring `PresetMenuLoaded`/`WR-04`.

### WR-03: `d`'s manual-placement toast path reads run-config state on the event loop (same D-03 class, delta-introduced)

**File:** `tui/screens/selection.py:1777-1781` (reached from `action_download_model`, `selection.py:1812-1816`)
**Issue:** `_manual_landing_path` — new in the 261014-mlc delta — calls `run_config_service.resolve_dirs(run_config_service.load_state())` synchronously inside the `d` key handler to compute the landing dir for the manual-placement toast. `load_state()` is a state-file JSON read; a cold/network-mounted state root stalls the event loop on an ordinary keypress. (Sibling pre-existing sites in the same file — `action_open_wizard`'s four registry reads in `build_wizard`, the synchronous `import_template` submit, and `set_enabled`'s write — predate the base and are noted here only as context; the manual-path read is the one the delta added.)
**Fix:** The loaded `SelectionData` snapshot could carry the already-resolved effective model root (`SelectionBackend.load_selection_data` already computes `dirs.model_root_abs` inside its worker at `selection.py:459-465`) — store it on the snapshot and have `_manual_landing_path` read it instead of re-loading state on the loop.

## Info

### IN-01: Dead SEL_ constants and stale dataset-table comments after the slot split

**File:** `tui/strings.py:218-240`
**Issue:** Since MLC-02 moved the dataset table to slot 3 (which uses the `DL_FULL_*` vocabulary), `SEL_COL_TASK`, `SEL_COL_CATEGORY`, `SEL_COL_METRIC`, `SEL_COL_PRESENCE`, `SEL_PRESENCE_PRESENT`, and `SEL_PRESENCE_MISSING` have zero consumers anywhere under `tui/` or `tests/` (grep-verified). Their comments still describe an active surface ("Dataset-table column headers …", "formatting happens only in the screen"), which will mislead the next editor. (`SEL_CLEAR_MARKS_CONFIRM` is also consumerless but is explicitly self-annotated as landed-for-the-record, and `SEL_SWITCH_LABEL` is legitimately consumed by `tui/screens/run_config.py:994`.) The CFG_/LNC_/MON_ inventory tripwire does not cover the SEL_ block, so these will not be caught mechanically.
**Fix:** Delete the six dead constants (or re-annotate them like `SEL_CLEAR_MARKS_CONFIRM` if retained deliberately), and correct the comment block to say the dataset-table vocabulary moved to slot 3.

### IN-02: Tests pin committed-data counts (36 adapted) that break on any compat-map data commit

**File:** `tests/tui/test_pilot_selection.py:1451-1455`; `tests/tui/test_pilot_selection_custom.py:895`
**Issue:** `test_backend_loads_the_committed_registries_and_presence` asserts `sum(... dnallm_adapted is True) == 36` and the full-loop test asserts `keys.index("loop-model-lm") == 36` (the row appended after the 36-adapted default pool). `pipeline/dnallm_compat.json` is maintainer-refreshable data — the adapted set has already evolved once (l6h's MODEL_INFO alignment) and will again as models get adapted. The repo's own R-03 follow-up rule (established after the 10-02 review) is to pin structure, never specific counts, against refreshable data. Any compat-map change turns these into red CI for a non-defect.
**Fix:** Derive the expected adapted count from the committed map in the test (`expected = sum(1 for v in json.loads((REPO_ROOT/'pipeline/dnallm_compat.json').read_text()).values() if v.get('dnallm_adapted') is True)`) and assert against it, keeping the structural assertions (key-set coverage, three-value vocabulary) exact.

### IN-03: Stale "seven kernel ids" comment in the env-check Pilot suite

**File:** `tests/tui/test_pilot_env_check.py:90`
**Issue:** `MAIN_KERNEL_ORDER`'s comment still says "The seven kernel ids in main() order" — the 261014-dcl `model_dirs` addition made it eight (the rest of the file, including the docstring and `_mixed_results`, was updated).
**Fix:** `# The eight kernel ids in main() order — the row-order contract.`

---

_Reviewed: 2026-10-14T21:55:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
