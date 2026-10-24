---
phase: quick-261018-kvj
plan: 01
subsystem: tui-monitor
tags: [tui, monitor, tabs, ux, i18n, goldens, pty]
requires:
  - "261017-uwr live-evidence pipeline (launcher registry ∪ /proc probe -> full_scan states)"
  - "261018-08g fresh-MonitorScreen-per-nav + MonitorSession (F1 fix)"
provides:
  - "Slot-5 two-tab surface: Running cards (one per run, mgpu worker rows grouped) + History rows (newest-first, per-run drill)"
  - "MON_TAB_/MON_CARD_/graduation string vocabulary; machine vocabulary purged from zh copy"
  - "pty-lane tab-switch + empty-route regression tests"
  - "WINDOWS #40/#41 closed; combined D-03 monitor-golden handoff (uncommitted)"
affects:
  - "tests/tui/test_pilot_run_config.py (one D-13 test adapted off the retired _attached_root API)"
key-files:
  created:
    - ".planning/quick/261018-kvj-slot-5-human-logic-redesign-tabbed-runni/deferred-items.md"
  modified:
    - tui/screens/monitor.py
    - tui/strings.py
    - tui/styles.tcss
    - tests/tui/test_pilot_monitor.py
    - tests/tui/test_strings_phase11.py
    - tests/tui/test_pty_driver.py
    - tests/tui/test_snapshots.py
    - tests/tui/test_pilot_run_config.py
    - .planning/WINDOWS.md
decisions:
  - "Cards render in a ListView of ListItem cards (the selection.py template-menu precedent; cursor re-pin by clamped INDEX — WR-05's spirit for a positional-identity list)"
  - "Dual presence derives from resume_count(root) > 0 (resume markers = the on-disk evidence of prior completed work under the root; a fresh first run has none) — the badge surfaces run-identity, never deduplicates"
  - "mgpu grouping predicate = strip the -mgpu-w{digits} suffix (run_sweep_shard.worker_root's frozen naming); a pure worker group renders EVERY root as a worker row (no duplicate primary lines)"
  - "left/right/tab are DECLARED priority bindings (the f10 non-printable precedent; screen-level priority never fires under modals, so modal Inputs keep native tab)"
  - "attached_root retired everywhere (session field, screen property, attach()); the ExitModal seam attached_running_counts now reads the freshest RUNNING root from the last scan + its stats"
  - "The stats-line family (MON_STATS_LINE*/MON_ETA_PENDING/MON_ETA_RANGE) retired with the master-detail surface — the card's current-cell line carries per-cell progress/ETA; MON_TOTAL_UNKNOWN/MON_ETA_UNKNOWN survive as the honest degradations"
status: complete
actuals:
  tokens: 71200          # chars/4 over git diff effb5bf..HEAD (estimate was 110000)
  tasks: 3
  commits: 3
  plan_head_before: effb5bf87957e50bd61e45d0449ac74027d462cd
  plan_head_after: 007b385
metrics:
  duration: 43 min
  completed: 2026-10-18
---

# Quick Task 261018-kvj: Slot-5 Human-Logic Redesign (Tabbed Running/History) Summary

**One-liner:** The maintainer-approved two-tab monitor — Running cards (one per live run, mgpu worker rows grouped inside) + History rows (newest-first, dual-presence badge, per-run drill) — with human-first bilingual copy, optimistic first paint, graduation toasts, and the empty-state enter routing to slot 4.

## What Landed

### The two-tab screen (tui/screens/monitor.py, rewritten)

- **Running (default landing)**: a `ListView` of card widgets — run name (the mgpu-stripped base), manifest scale (honest unknown when unparseable), done/total + the 10-cell bar, the current-cell line (`stats.current` + the per-cell steps/percent/bar/eta grammar), the resume note; `{root}-mgpu-w{i}` sibling roots group INSIDE one card as worker rows with their own fractions. A pure worker group (base not live) renders every root as a worker row.
- **History**: a `DataTable` (WR-05 diff-preserving `_set_table_rows` survives) — ✓ finished / ⏸ interrupted state words (the cell vocabulary), root name, done/total fraction, newest-activity wall-clock; sorted newest mtime desc; enter drills the run.
- **Tabs**: left, right, AND tab flip (declared priority bindings — non-printables pass the focused-widget consume filter, the f10 probe pin); one-row tab header with (n)/(m) count badges; active tab on the live theme accent, inactive rich-dim (a `$text-muted` Text span crashes the Label render path — the 09-03 MissingStyle pin, re-encountered and documented).
- **Scoped keys**: k/t/f act on the focused tab's selection (the card's action root = the group primary; a History row's root); registry-only kill gate, honest `MON_LOG_UNAVAILABLE` for tee-less roots, honest pre-confirm `MON_KILL_UNAVAILABLE` refusal; silent without a selection. a/r stay screen-global.
- **RunCellsModal** (the FailuresModal pattern): enter drills a read-once snapshot (cells_view + entries_progress read ONCE via a `@work` worker, the LogTailModal read-once precedent) rendering through the hoisted `_entry_state_cell`/`_entry_progress_cell` helpers (UWR-4 live-on-top order + the 68-char-key truncation); enter again opens the existing CellDetailModal.
- **Cadence (D-09)**: one exclusive `mon-frontier` worker per tick iterates EVERY live root (frontier_scan + stats + entries_progress per root, per-root tolerant skip); the `mon-full` worker feeds both tabs (per-root stats/cells/progress/resume/scale for running roots); vanished-root caches drop (no stale cards).
- **#41 optimistic paint**: compose paints the tab skeleton + the `MON_SCANNING` note at mount (zero fabricated rows); the first scan message clears it and fills the tabs.
- **Graduation**: a screen-local root→state map diffs each scan; an OBSERVED running→finished/interrupted transition fires the bilingual toast naming the run and moves the card to History; a fresh screen's first scan fires nothing (honest, no stale toast).
- **Empty-state route**: enter on the empty Running tab navigates to slot 4 — the ONLY launch gate (async screen action awaits `app.action_nav(4)`).
- **08g F1 preserved exactly**: `build_monitor_screen` still builds a FRESH screen per navigation over the ONE shared `MonitorSession`; the pty renav test passes byte-unmodified. `attached_root` retired (session field, property, `attach()`); `expected_totals`/`fallback_starts`/`ever_discovered` survive; `note_launch` seeds the stats seams only; `attached_running_counts` (the ExitModal seam) now reads the freshest running root + its stats.
- **Service layer zero-change**: `sweep_monitor.py`, `sweep_launcher.py`, and `MonitorBackend` are byte-untouched (verified — the only service-adjacent line edits are none; `git diff effb5bf..HEAD -- tui/services/` is empty).

### Strings (tui/strings.py)

16 new constants (`MON_TAB_RUNNING/HISTORY/COUNT`, `MON_SCANNING`, `MON_RUNNING_EMPTY`, `MON_HISTORY_EMPTY`, `MON_TAB_SWITCH_KEYCAP`, `MON_CARD_SCALE/CURRENT/CURRENT_NONE`, `MON_SCALE_UNKNOWN`, `MON_HISTORY_RERUN_BADGE`, `MON_GRADUATED_DONE/INTERRUPTED_TOAST`, `MON_COL_ACTIVITY`, `MON_RUN_CELLS_TITLE`); the master-detail family deleted (`MON_DISCOVERED_*`, `MON_CELLS_TITLE/EMPTY`, `MON_CONTEXT_HEADER`, the sweep-state trio, `MON_COL_SCALE/ETA`, the stats-line + ETA pending/range family); `MON_ATTACH_INVALID_TOAST` zh reworded off the `发现` machine vocabulary (grep-audited: zero zh user-facing `发现`/`sweep 根`). The strings inventory mirror updated in both directions.

### Tests

- **test_pilot_monitor.py**: 60 tests over the SAME fakes — coverage parity held for kill/log/failures/rerun (all 9 rerun legs)/degradation/responsiveness, now asserted through the tab scoping; new pins for tab switching, card composition, history sort, dual-presence badge, mgpu grouping, scoped-key refusals, both drill paths, optimistic paint (gated fake), both graduation variants, the empty-route, the L-toggle recompose idempotence, and the cursor-identity reorder.
- **test_pty_driver.py**: +2 tests (`test_monitor_tab_switch_paints_history`, `test_monitor_running_empty_enter_routes_slot4`); the F1 renav test byte-unmodified and green; lane 6/6.
- **test_snapshots.py**: monitor fixtures/drives adapted (no attach call); `monitor_running`/`monitor_empty` regenerated UNCOMMITTED — the ONE combined D-03 handoff superseding the uwr pair; `run_config.svg` sha-protected (`c7e14458…` identical before/after); the other 7 goldens byte-identical; snapshot lane 11/11 green in the worktree.
- **test_strings_phase11.py**: inventory + glyph/context-header tests redirected to the new vocabulary (the two retired pins became the tabbed-surface equivalents rather than deletions).
- **test_pilot_run_config.py**: one D-13 test adapted off the retired `_attached_root` (the launch-injection + ExitModal-count assertions survive on the session seams).

### Gates

- Full suite `make test`: **2F/1919P** — exactly the pre-existing baseline membership (both members verified failing identically on clean HEAD via `git stash`; logged to deferred-items.md), **zero new failures**, every new test green.
- `make lint` + `make typecheck`: green. Node lane: 26/26. `make snapshot`: clean. `pytest tests/tui/test_pty_driver.py`: 6/6.

## Deviations from Plan

### Task 1 + Task 2 landed as one implementation commit

- **Found during:** execution sequencing
- **Issue:** The plan split the restructure (Task 1) from the optimistic paint/graduation/empty-route (Task 2), but the compose tree IS the optimistic skeleton and the scan handlers ARE the graduation surface — implementing Task 1 without them would have meant writing the old blank-mount screen first and rewriting it immediately after.
- **Fix:** One implementation commit (281ebea) carries both; Task 2's dedicated commit (2aef851) adds its remaining unpinned behavior (the L-toggle recompose idempotence over the new cadence) plus the language-agnostic boot-language handling. All Task 2 truths are test-pinned in the combined suite.

### Auto-fixed Issues

**1. [Rule 1 - Bug] `$text-muted` Text spans crash the ListView/Label render path**
- **Found during:** Task 1 test run (MissingStyle in the card render)
- **Issue:** The new card/tab labels passed `$text-muted`-styled rich Text into the Static render path — the 09-03 probe pin (rich cannot parse $token styles there; the old screen only ever fed $token Texts into DataTable cells).
- **Fix:** Card/tab paths use rich-native `dim`; DataTable cell paths keep the `$token` vocabulary (the old precedent). Documented in `_render_tabs`'s docstring.

**2. [Rule 1 - Bug] App AUTO_FOCUS grabbed the hidden empty card list**
- **Found during:** Task 2's empty-route Pilot test (enter never reached the screen binding)
- **Issue:** On screen push the app-level AUTO_FOCUS ("*") focused the (hidden, empty) `#mon-cards` ListView, which then consumed enter.
- **Fix:** The scan handlers re-run `_focus_active()`, which clears focus when the active tab has no selection (documented in the method).

**3. [Rule 3 - Blocking] Two collateral test breaks from the retired API**
- `test_pilot_run_config.py::test_launch_success_auto_navigates_to_monitor_attached` (asserted `_attached_root`) — adapted to the session seams per the plan's "prefer deleting and fixing tests".
- `test_work_site_hardening.py` AST pin flagged the new `_run_frontier` worker — `exit_on_error=False` added (the never-exit floor).

### Baseline membership drift (out of scope, logged)

The standing rule's "1F baseline" reads **2F at execution**: `test_services_about` version pin (stale since the post-08g v1.2.0 bump commits) and `test_services_run_config` storage (machine-local `pipeline/logs`). Both verified failing identically on clean HEAD; logged to `deferred-items.md` with removal guidance. Zero new failures from this task.

## Windows Ledger

- **#40 closed** (fixed): the tabbed redesign replaces the master-detail view entirely — no pane titles/selection echo remain to fix (maintainer 2026-10-18 15:01 approval cited in the row).
- **#41 closed** (fixed): skeleton + scanning note paint at mount; the note clears on the first scan message.
- **#35 amended** (markdown + JSON + counts synced): the uwr uncommitted monitor pair is superseded — the current uncommitted bytes are the ONE combined D-03 monitor-golden handoff (uwr + kvj); #39 (run_config.svg) stays separate on the tree.
- Counts: open 27 / fixed 14 / total 41.

## Auth Gates

None occurred.

## Known Stubs

None — every surface renders from live service seams; the uncommitted monitor goldens are the deliberate D-03 handoff (WINDOWS #35), not a stub.

## Self-Check: PASSED

All three task commits are ancestors of HEAD (281ebea, 2aef851, 007b385); every key file exists on disk; `git status` shows exactly the intended uncommitted set (monitor_running.svg, monitor_empty.svg, run_config.svg).
