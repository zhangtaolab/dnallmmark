---
phase: quick-261015-c4j
plan: 01
subsystem: tui
tags: [tui, slot-2, slot-3, slot-5, download-queue, sweep-monitor]
requires:
  - 261014-mlc (the KIND_MODEL lane + the slot 2/3 split substrate)
provides:
  - C4J-1 slot-2 live model-download overlay (QUEUE_STATE_* words + parsed percents in the 下载 column)
  - C4J-1 slot-3 dataset-only queue presentation (KIND_MODEL invisible on slot 3)
  - C4J-2 slot-3 dominant dataset-list pane (2fr/1fr, 9+/12+ rows)
  - C4J-3 slot-5 model×dataset entries list with checkpoint training progress
affects:
  - tui/screens/selection.py, tui/screens/data_manager.py, tui/screens/monitor.py
  - tui/services/download_queue.py, tui/services/sweep_monitor.py
  - tui/strings.py, tui/styles.tcss, docs/TUI-GUIDE.md
tech-stack:
  added: []   # zero new dependencies; textual stays pinned 8.2.8
  patterns:
    - "tolerant getattr service seam (the additive-fake pattern — pre-C4J fakes conform by omission)"
    - "persisted-state-as-truth overlay re-derivation on every rebuild/event"
    - "kind-split presentation over ONE shared queue (no service mechanism change)"
key-files:
  created: []
  modified:
    - tui/services/download_queue.py
    - tui/screens/selection.py
    - tui/screens/data_manager.py
    - tui/services/sweep_monitor.py
    - tui/screens/monitor.py
    - tui/strings.py
    - tui/styles.tcss
    - tests/tui/test_services_download_queue.py
    - tests/tui/test_pilot_selection_custom.py
    - tests/tui/test_pilot_selection.py
    - tests/tui/test_pilot_data_manager.py
    - tests/tui/test_services_sweep_monitor.py
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_strings_phase11.py
    - docs/TUI-GUIDE.md
decisions:
  - "The download column widened 10 -> 15 so the live '下载中 NN%' word is legible (the plan's 'within the column budget' wording admitted no room at 10; the 80x24 budget pin updated faithfully 101 -> 106 — h-scroll behavior unchanged, min grid intact)"
  - "A successful d enqueue lands the pending word immediately (one overlay refresh after the toast) — the driver's claim tick follows within moments on the real path, and a blocked driver still shows the honest pending state"
  - "The running word's own ⠋ glyph carries the indeterminate contract on slot 2 (no appended ⠋… — glyph duplication rejected per the tui-design restraint principle)"
  - "entry_fold's done counts TERMINAL seeds (completed|failed|skipped) — the stats-line done convention, so '✗ 失败 3/3' reads all-seeds-finished"
metrics:
  duration: 48 min
  completed: 2026-10-15
actuals:
  tokens: 28251    # chars/4 over the realized diff (113007 chars); plan estimate 90000
  tasks: 3
  commits: 7       # MEASURED: git rev-list --count cbb1c29..HEAD
plan_head_before: cbb1c29860e5e0b5b22a5d87050c572a04f4cd2a
plan_head_after: 5b04b2398cd3ea5c7d16e975580ec6cfafebadab
status: complete
---

# Phase quick-261015-c4j Plan 01: TUI three-screen UX revision (slots 2/3/5) Summary

**One-liner:** Slot 2 renders live KIND_MODEL download state/percent in the 下载 column (progress_cb threaded into the dnallm -I child's stderr parse), slot 3's queue table filters to dataset-kind entries while its dataset list grows into the dominant 2fr pane, and slot 5 becomes a model×dataset entries list whose running rows carry steps/percent/bar parsed from the newest checkpoint trainer_state.json.

## What Was Built

### Task 1 — C4J-1: slot-2 live model-download surface + slot-3 dataset-only queue split
- **`tui/services/download_queue.py`**: `_run_model_download` accepts and threads `progress_cb` — its `on_stderr` pump runs the dataset lane's exact `parse_progress` extraction with the identical per-integer-percent dedupe closure; the last parsed percent rides the terminal `_finish` calls (None stays the honest indeterminate when nothing parses). Every other model-lane semantic byte-identical (argv, -I isolation, normalization, the config.json done gate, no reconcile leg).
- **`tui/screens/selection.py`**: the queue seam (`SelectionQueueServiceProtocol`/`SelectionQueueBackend`) gains `entries()`, read through a tolerant `getattr` fallback so every pre-C4J injected fake keeps conforming (the additive-fake pin proves it). A live non-done KIND_MODEL entry overlays its QUEUE_STATE_* word in the download column (vocabulary reused verbatim, styles mirrored from the queue table); `apply_queue_progress` (new) updates the row's cell in place (a parsed percent composes beside the 下载中 word; the claim tick's None keeps the word's ⠋ glyph); `apply_queue_event` extends to refresh the overlay on non-done model events (failed word lands; percent cache pops) while done keeps the `_load_data()` flip. The overlay re-derives from `entries()` on every rebuild — filter typing, the `t` pool toggle, and a fresh mount mid-download all show the live state.
- **`tui/screens/data_manager.py`**: the kind split — `_sorted_entries` filters KIND_MODEL (so the queue rows AND the title count exclude them), the full-list live-states join filters kind (a model-kind entry whose key collides with a presence row never overlays), the banners filter kind explicitly, and both `apply_queue_event`/`apply_queue_progress` early-return on model traffic. The Zenodo bundle row stays (the dataset lane's alternate). The shared `DownloadQueueService` mechanism is untouched — one queue, one driver, one state file.
- Column widened `_MODEL_DOWNLOAD_W` 10 → 15 (see Decisions).

### Task 2 — C4J-2: slot-3 dataset-list density
- **`tui/styles.tcss`**: `#dl-missing-region` grows from the fixed 5-cell strip to `2fr` (the dominant pane), `#dl-queue-region` takes `1fr`; both DataTables keep scrolling; every other rule in the block byte-identical; the block comment carries the C4J-2 rationale.
- **`tui/screens/data_manager.py`**: only the compose docstring's fixed-height sentence updated — zero logic changes (pure CSS).
- Pinned: 80x24 → missing region ≥ 11 (table ≥ 10 → ≥ 9 visible rows) with the queue region's ≥ 4 floor; 120x40 → table ≥ 13 (≥ 12 rows). The pre-existing 80x24 test passes unedited.

### Task 3 — C4J-3: slot-5 entries list with training progress
- **`tui/services/sweep_monitor.py`**: `CellProgress` (frozen; step/max_steps/percent, each int|None) + `cell_progress(seed_dir)` — scans the seed dir's `checkpoint-*` children (bounded by `_SCAN_DIR_ENTRY_CAP`), selects the NUMERICALLY largest suffix (checkpoint-1000 beats checkpoint-999 — pinned), tolerantly loads its `trainer_state.json` (`RESUME_MARKER` imported from run_sweep — D-05 same-source; `artifact_loader`; damage/absence → all-None), reads `global_step`/`max_steps` as non-bool ints, derives `percent = round(step/max*100)` clamped 0..100 only when `max_steps > 0`. `EntryView`/`entry_fold(row)` — any running → running, any failed → failed, all terminal → completed, else queued, plus done/total seed counts (done = terminal seeds). `entries_progress(root)` — one bounded `_iter_seed_dirs` walk, progress parsed ONLY for running seeds, max-step wins across a row's running seeds; `{}` when nothing runs.
- **`tui/screens/monitor.py`**: the cells table becomes the ENTRIES list (模型 / 任务 / 状态 / 进度): the folded state word + `MON_ENTRY_SEED_COUNTS` done/total segment, and the progress cell (`MON_PROGRESS_STEPS` steps/max + integer percent + the 10-cell bar with accent fill on running rows with parseable progress; `MON_PROGRESS_INDETERMINATE` on running rows without; the dim dash on non-running). Narrow grid drops the state word and the bar. The frontier worker refreshes `entries_progress` inside the existing exclusive `mon-frontier` thread (results ride the existing run-id-tagged `FrontierScanned`/`FullScanned` messages); the full-scan worker seeds the first read; a tolerant `getattr` seam keeps every pre-C4J fake conforming. Row keys, the WR-05 `_set_table_rows` diff discipline, and the empty state survive; per-seed/fraction detail stays in the enter drill-down (`CellDetailModal` untouched).
- **`tui/strings.py` + `tests/tui/test_strings_phase11.py`**: four new constants (`MON_COL_STATE`, `MON_PROGRESS_STEPS`, `MON_PROGRESS_INDETERMINATE`, `MON_ENTRY_SEED_COUNTS`) registered in the bidirectional inventory in the same change.
- **`docs/TUI-GUIDE.md`**: Screen 5 rewritten to the entries list (columns, progress semantics, honest degradation, drill-down); Screen 2/3 gained the 2026-10-15 revision sentences; the Screen 3 queue paragraph's "model downloads queue here too" wording corrected to name slot 2 as their render surface.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] Download column budget admitted no room for the percent word**
- **Found during:** Task 1
- **Issue:** The plan asked for the percent "beside/appended to the downloading word within the column budget", but the 下载中 word alone exactly fills the 10-cell column's 8-cell content budget — a two-digit percent would be invisible (clipped data, not honest progress).
- **Fix:** Widened `_MODEL_DOWNLOAD_W` 10 → 15 (content 13 = "⠋ 下载中 100%"); updated the width comment and the one 80x24 budget pin faithfully (101 → 106; h-scroll and the min grid unchanged).
- **Files modified:** tui/screens/selection.py, tests/tui/test_pilot_selection.py
- **Commit:** f7876b3

**2. [Test-fixture accommodation] The seeded-state-file test seeds pending, not downloading**
- **Found during:** Task 1
- **Issue:** The plan's seeded-state test described "one KIND_MODEL and one KIND_DATASET entry"; seeding `downloading` in the state file hits the D-06 restart downgrade (`load()` rewrites downloading → pending + interrupted), appending the restart note to the task cell.
- **Fix:** Seed both entries as `pending` (the honest persisted shape any mount actually reads); the kind-split assertions are identical.
- **Files modified:** tests/tui/test_pilot_data_manager.py
- **Commit:** f7876b3

Plus one additive decision within the plan's spirit: a successful `d` enqueue lands the pending word immediately (see Decisions).

## Authentication Gates

None — no auth-gated surfaces in this task.

## Verification Evidence

- Targeted suites (the plan's per-task `<verify>` commands): `tests/tui/test_services_download_queue.py`, `test_pilot_selection_custom.py`, `test_pilot_selection.py`, `test_pilot_data_manager.py`, `test_import_lock.py`, `test_services_sweep_monitor.py`, `test_pilot_monitor.py`, `test_strings_phase11.py`, `test_snapshots.py` — **421 passed, 9 xfailed** on the final tree.
- `make lint` + `make typecheck` green.
- Full `make test`: **exactly the 7 documented failures + 9 strict-xfail** (`test_determinism` + 5 × `test_schemas` + `test_storage_overview_over pipeline/logs`) — zero new failures; node lane 26 pass / 0 fail.
- `make test-fast`: the same set minus the slow-marked `test_determinism` (6 failures — the documented baseline for that lane).
- `tests/tui/__snapshots__/` byte-untouched (`git diff` over the dir is empty); no xfail marker changed.
- No test imports dnallm/modelscope, touches the network, or runs a GPU; the GB10 background smoke (`pipeline/finetuned/smoke-2x2-261014`) was never disturbed (read-only repo tree; the pipeline/ dir untouched — `git diff --name-only` proves it).

## Known Stubs

None — every rendered state reaches a real data source (queue entries / disk presence / checkpoint trainer_state), and every degradation renders an honest designed constant.

## D-03 Visual-Change Notes (for the maintainer's snapshot re-review)

All three screens changed visually; the goldens were NOT regenerated (the locked constraint — `make snapshot-update` is the maintainer's D-03 step). After the maintainer regenerates, expect these diffs:

1. **Slot 2 (selection goldens)**: the download column is 5 cells wider (15 vs 10) — the table's total budget is 106 at the pinned widths; the visible vocabulary is unchanged until a live queue entry exists (the goldens' static fixtures render the same four-state words).
2. **Slot 3 (data_manager goldens — already stale-xfail since 261014-mlc)**: the full-list pane now takes ~2/3 of the height (14-15 rows at 80x24, ~24 at 120x40) and the queue pane shrinks to the 1fr secondary share; the separator border position moves accordingly.
3. **Slot 5 (monitor goldens)**: the cells table's per-seed columns are GONE — replaced by the four-column entries layout (模型/任务/状态/进度) with folded state words + seed counts and (on running rows) the steps/percent/bar progress cell; the drill-down per-seed view is unchanged.

The known snapshot-determinism flake under load (261014-dcl deferred-items) remains pre-existing.

## Threat-Model Dispositions

- **T-c4j-01 (tampered trainer_state)**: mitigated — tolerant parse via artifact_loader, non-bool int checks, clamped percent, all-None degradation; test-pinned (`test_cell_progress_tolerant_damage_degrades_all_none`, `test_cell_progress_non_int_fields_and_bad_max_degrade`).
- **T-c4j-02 (malicious child stderr)**: mitigated — regex-only `parse_progress` reuse, no interpolation; the worst case is a wrong integer on one UI cell.
- **T-c4j-03 (cadence DoS)**: mitigated — bounded `_iter_seed_dirs` walk, running-seeds-only parse, inside the existing exclusive worker, never the event loop.
- **T-c4j-04 (repudiation)**: unchanged audit surfaces (queue state file, per-key logs, flip toasts).
- **T-c4j-SC (package installs)**: zero new packages — the uv.lock is untouched.

## Self-Check: PASSED

- Files: all 15 modified files exist on disk (`git diff --name-only` over the plan range).
- Commits: 3495dd6, f7876b3, e12e629, 6754034, a8deb27, 6a59178, 5b04b23 — all ancestors of HEAD (`git merge-base --is-ancestor` verified for each at write time via the ledger range listing).
- Full-suite baseline: 7F + 9XF exactly; goldens byte-untouched.
