---
phase: quick-261018-kvj
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tui/screens/monitor.py
  - tui/strings.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_pty_driver.py
  - tests/tui/test_snapshots.py
  - tests/tui/__snapshots__/monitor_running.svg
  - tests/tui/__snapshots__/monitor_empty.svg
  - .planning/WINDOWS.md
autonomous: true
requirements: ["WINDOWS-40", "WINDOWS-41", "UX-slot5-tabbed-redesign"]
user_setup: []

estimate:
  tokens: 110000
  raw_tokens: 55000
  tasks: 3
  confidence: med

must_haves:
  truths:
    - "Slot 5 opens on the 正在运行/Running tab (default) and ←/→ AND tab all switch to 历史/History and back; both keys appear in the footer/help vocabulary"
    - "Each live run renders as ONE card (one launch = one card): run name + 模型×数据 summary, total progress bar (done/total cells), current cell line (model×task×seed + per-cell progress/ETA); multi-GPU worker roots render as worker rows INSIDE one card"
    - "The 历史/History tab lists completed/interrupted runs reverse-chronologically with (n) tab count badges on both tabs; enter drills a run's per-cell results; [f] opens that run's failures"
    - "The Running empty state is actionable (暂无运行中任务 — 回车打开启动确认 family copy) and enter there routes to slot 4 (app.nav(4))"
    - "The screen paints the tab skeleton + 扫描中…/Scanning… note IMMEDIATELY on mount; the worker arrival fills it (no 3.5s blank)"
    - "A run finishing while the screen is up graduates: card leaves Running, a History row appears, and a toast announces it"
    - "A root with BOTH a live handle and historical cells shows its live card on Running AND its history row carries a 重跑进行中/re-run in progress badge"
    - "No user-facing string contains the machine vocabulary (发现的/发现/sweep 根); filenames like sweep_failures.json stay verbatim as data"
    - "The 08g F1 fix is preserved: fresh MonitorScreen per navigation + MonitorSession survival; the existing pty monitor-renav test passes UNMODIFIED"
    - "Service layer zero-change: sweep_monitor/sweep_launcher functions and MonitorBackend's service delegations are reused, not edited"
  artifacts:
    - "tui/screens/monitor.py restructured to the two-tab screen"
    - "tui/strings.py with the new bilingual MON_ tab/card/graduation constants and purged machine vocabulary"
    - "tests/tui/test_pty_driver.py extended with the tab-switch and empty-state-route tests"
    - "tests/tui/__snapshots__/monitor_running.svg + monitor_empty.svg regenerated UNCOMMITTED (the combined D-03 handoff)"
  key_links:
    - "Running tab card list <- MonitorBackend._live_evidence (launcher registry ∪ /proc probe) — the uwr pipeline, unchanged"
    - "Card total/current-cell lines <- sweep_monitor.stats + entries_progress (existing seams, per live root)"
    - "History rows <- full_scan sweeps minus live roots; sort by newest_mtime desc (UWR-4 precedent)"
    - "Graduation toast <- per-root state diff between consecutive on-screen scans"
    - "Empty-state enter -> app.nav(4) -> the slot-4 launch gate (one launch path, never duplicated)"
---

<objective>
Slot-5 人机逻辑重设计: replace the master-detail dual-table monitor with the maintainer-approved (2026-10-18 15:01) two-tab design — 「正在运行/Running」 (one card per live run, default landing) and 「历史/History」 (completed/interrupted runs, reverse-chronological, per-cell drill) — with human-first copy (machine vocabulary purged), optimistic first paint (#41), and the master-detail affordance problem (#40) closed by the redesign itself.

Purpose: the maintainer ruled the current slot-5 logic "怪怪的" and approved this tabbed contract verbatim; this is a presentation-layer reorganization over the already-done service seams (uwr three-state/live-evidence, 08g MonitorSession/F1 fix) — service layer zero-change.

Output: restructured monitor screen, bilingual strings, adapted Pilot suite, extended pty lane, regenerated uncommitted monitor goldens, closed WINDOWS #40/#41, updated D-03 ledger rows.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/WINDOWS.md
tui/screens/monitor.py          (the file being restructured — read fully first)
tui/strings.py                  (MON_ block, lines ~1612-1860)
tui/app.py                      (composition root: build_monitor_screen, MonitorSession injection, D-13 nav)
tui/services/sweep_monitor.py   (read-only reuse: full_scan/frontier_scan/cells_view/stats/entries_progress/entry_fold)
tests/tui/test_pilot_monitor.py (58 tests to adapt)
tests/tui/test_pty_driver.py    (the permanent pty lane — extend, never weaken)
tests/tui/test_snapshots.py     (golden fixtures incl. _running_monitor_service)
</context>

<assumption_delta_decision>
The presentation identity changes noun (detected: singular→plural-style transition, root-row → run-card). Decision: **promote** — the "run" (一次运行, one live handle or one discovered terminal root) is the new primary presentation unit; the sweep root demotes to a data key inside cards/rows and service arguments. Not add-alongside: the old master-detail root table is DELETED, not kept beside the tabs. Dual-presence (same root live + historical) is the honest consequence of run-identity and is surfaced with a badge rather than deduplicated away.
</assumption_delta_decision>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Two-tab screen restructure — Running cards + History table + scoped keys + human copy</name>
  <files>tui/screens/monitor.py, tui/strings.py, tests/tui/test_pilot_monitor.py, tests/tui/test_strings_phase11.py</files>
  <behavior>
    - Tab switch: ←, →, and tab each move focus between the two tabs from either tab's focused list; the active tab header re-accents and the tab counts (n)/(m) render.
    - Running card composition: a live root renders one card whose lines are run name, 模型×数据 summary (sweep_scale when readable, else honest unknown), done/total + 10-cell glyph bar, and the current cell line (stats.current model×task×seed + entries_progress percent/ETA via the existing _entry_progress_cell grammar); mgpu-w{i} sibling roots render as worker rows inside the SAME card.
    - History derivation: discovered roots with terminal/interrupted state and no live handle list reverse-chronologically (newest_mtime desc); the ⏸ interrupted leg keeps the muted channel.
    - Dual presence: a root with both live evidence and historical cells appears as its live card on Running AND its History row carries the 重跑进行中/re-run in progress badge.
    - Enter routing: focused run (either tab) opens the per-run cells drill (DataTable of model×task rows with fold state + progress; enter again opens the existing CellDetailModal); Running tab EMPTY state enter calls app.nav(4).
    - Scoped keys: k kills the focused running card's root (registry-only live_sweeps gate unchanged, y-only confirm unchanged); t opens the focused run's tee log (history roots hit the existing MON_LOG_UNAVAILABLE honest state); f opens the focused run's FailuresModal; a attaches a manual root (joins the correct tab on next scan); r rescans — all five refuse silently/honestly when the focused tab has no selection.
    - Cadence: the 2s frontier worker iterates ALL live roots (frontier_scan + stats + entries_progress per root) in the SAME exclusive mon-frontier group; full-scan worker unchanged.
    - Copy purge: no user-facing MON_ constant contains 发现/发现的/sweep 根; tab titles render 正在运行/Running and 历史/History; all new constants bilingual with inventory rows.
  </behavior>
  <action>
    Restructure tui/screens/monitor.py per the approved design contract (planning_context 设计契约, maintainer 2026-10-18 15:01):
    (1) REPLACE compose(): TopMenuBar; a one-row tab header (two Labels with (n) count badges, active tab accent via rich dim/theme-accent — the nav.py slot-marker precedent; do NOT adopt textual TabbedContent — unprobed chrome, and the screen needs custom key scoping); a content region that mounts EITHER the Running list OR the History table (single focus, single list — 单焦点单表); the title bar keeps the MON_SCAN_NOTE cadence note byte-unchanged (the pty lane's monitor marker depends on it); BottomBar.
    (2) Running tab: one focusable card per live run from MonitorBackend._live_evidence (the uwr registry ∪ /proc pipeline — reuse, do not edit). Render as a ListView of card widgets (the selection.py template-menu ListView precedent) OR a VerticalScroll of focusable card Verticals — pick ONE at execution after a quick probe of ListView cursor + custom-widget interplay on 8.2.8, and document the choice in the module docstring. Card body composes existing widgets only (Static/Label + the Text-assemble █/· 10-cell glyph bar already used by _progress_cell/_entry_progress_cell — do NOT introduce textual ProgressBar). Multi-GPU: group mgpu sibling roots (the {root}-mgpu-w{i} naming) under one card as worker rows — a root is a worker row when it matches a live sibling's mgpu pattern; probe the actual sibling naming in sweep_launcher before coding the predicate.
    (3) History tab: DataTable reusing _set_table_rows (WR-05 cursor identity survives cadence rebuilds) — columns: state glyph (✓/⏸ from the existing MON_STATE_* vocabulary), root name, done/total, newest-activity; sorted newest_mtime desc.
    (4) Enter drill: a RunCellsModal (ModalScreen, the FailuresModal pattern) reading cells_view + entries_progress ONCE via a @work thread worker (the LogTailModal read-once precedent — live refresh stays on the running card, the drill is a snapshot); rows rendered through the existing _entry_state_cell/_entry_progress_cell helpers (hoist them if needed); enter → the existing CellDetailModal path. The old always-visible cells DataTable, context header line, and discovered-title row are DELETED (the tabs replace them).
    (5) Keys: add ←/→/tab bindings (both arrows AND tab wired; if the focus system consumes plain tab, promote to a priority Binding — the 261017-mad f10 non-printable precedent; verify the pty lane still passes). Scope k/t/f to the focused tab's selection (focused card root or focused history row root); keep a and r screen-global. Keep the y-only kill confirm, E2'/rerun pipeline, attach validation, and all toast copy untouched except where machine words must go.
    (6) Cadence: _run_frontier loops the live roots (one exclusive mon-frontier worker per tick, per-root frontier_scan/stats/entries_progress, results cached in the existing _root_stats/_cell_progress dicts keyed by root); _run_full_scan unchanged except it no longer threads an attached root — it feeds both tabs.
    (7) MonitorSession: retire attached_root's UI role (drop the property or leave it unused-but-tested only if a test still needs it — prefer deleting and fixing tests); expected_totals/fallback_starts/ever_discovered survive for the stats seam and vanished-root degradation; note_launch keeps seeding stats seams but its auto-attach-for-display leg goes (no attachment concept remains). PRESERVE the 08g shape exactly: app.py builds a FRESH MonitorScreen per navigation and injects the shared session — do not touch build_monitor_screen's rebuild semantics (F1 is load-bearing; the pty monitor-renav test must stay green unmodified).
    (8) strings.py: add MON_TAB_RUNNING (正在运行/Running), MON_TAB_HISTORY (历史/History), tab-count badge format, MON_SCANNING (扫描中…/Scanning…), MON_RUNNING_EMPTY actionable copy (暂无运行中任务 — 回车打开启动确认 family; enter routes to slot 4 so the copy names the launch gate), card line constants (run summary, current cell, worker rows), MON_HISTORY_RERUN_BADGE, and keycap labels for the tab-switch keys shown in the footer. PURGE machine vocabulary from user-facing constants: MON_DISCOVERED_TITLE/MON_DISCOVERED_EMPTY/MON_CELLS_TITLE/MON_CELLS_EMPTY are replaced by the tab vocabulary (「一次运行」 phrasing per the contract); sweep_failures.json inside MON_FAILURES_TITLE is a filename (data) and stays; internal identifiers/comments may keep technical terms. Update the test_strings_phase11.py MON_ inventory mirror to the new constant set (the 10-03 W1-mirror discipline).
    (9) tests/tui/test_pilot_monitor.py: adapt the 58 tests to the tabbed surface over the SAME fakes (fake services unchanged — the screen's consumption changes); keep coverage parity for kill/log/failures/rerun/attach/gradation-degradation paths, now asserted through the tab scoping.
    TDD: write/adapt the failing behavioral tests first where practical (tab switch, card composition, history sort, dual-presence badge, scoped keys, enter routing), then implement.
  </action>
  <verify>
    <automated>cd /home/forrest/Github/dnallmmark && .venv/bin/python -m pytest tests/tui/test_pilot_monitor.py tests/tui/test_strings_phase11.py -x -q</automated>
  </verify>
  <done>Two-tab screen renders from the existing fakes; ←/→/tab switch; cards/history/badge/dual-presence asserted; scoped keys routed; machine vocabulary absent from every user-facing MON_ constant (grep-audited); full monitor Pilot suite green; ruff+ty clean on the touched files.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Optimistic first paint (#41) + graduation toast + empty-state slot-4 route</name>
  <files>tui/screens/monitor.py, tui/strings.py, tests/tui/test_pilot_monitor.py</files>
  <behavior>
    - Mount paints the tab skeleton + 扫描中…/Scanning… note IMMEDIATELY (zero scan round-trips); the note clears when the first FullScanned lands; the L-language recompose path stays idempotent (timers stop before re-arm — the EHC-1 rule).
    - A root transitioning running→finished or running→interrupted BETWEEN two on-screen scans fires the graduation toast (完成/中断 variant naming the run) and the next render moves it Running→History; a fresh screen's first scan fires NO toast (no prior observation).
    - Running-tab empty + enter navigates to slot 4 (the Run Config screen gains focus) — asserted at Pilot level.
  </behavior>
  <action>
    (1) #41 optimistic paint: compose() renders both tab headers + the focused tab's empty region + the MON_SCANNING note at mount; on_mount keeps its idempotent timer discipline and dispatches the mount kick as today; the first FullScanned (or FrontierScanned) handler clears the scanning note and renders real content. No data is fabricated during the scan window — skeleton + note only, the honesty-over-motion rule.
    (2) Graduation: keep a screen-local dict of root→state as of the last rendered scan; on each scan-derived render, diff it — a running→terminal/interrupted root fires app.notify with new bilingual constants MON_GRADUATED_DONE_TOAST / MON_GRADUATED_INTERRUPTED_TOAST (✓ 运行完成 — 已移入历史 family, run name via Path(root).name); then update the dict. Screen-local by design: transitions observed while watching; document that a finish while on another screen graduates silently on the next visit (honest, no stale toast).
    (3) Empty-state route: the Running tab's empty region is focusable/clickable-neutral; screen enter binding routes by focused region — empty Running region → self.app.nav(4) (slot 4 owns the ONLY launch gate; slot 5 never duplicates it); non-empty → the focused card's drill (Task 1). Assert the route at Pilot level (push/switch to the run-config screen).
    (4) Add the three new constants to strings.py + the inventory mirror; bilingual; no machine words.
  </action>
  <verify>
    <automated>cd /home/forrest/Github/dnallmmark && .venv/bin/python -m pytest tests/tui/test_pilot_monitor.py -q -k "scan or graduat or empty or tab"</automated>
  </verify>
  <done>Skeleton paints pre-scan (Pilot-asserted via a gated fake that delays its first post); graduation toast fires exactly on observed transitions and not on first paint; empty-state enter lands on slot 4; all new tests green.</done>
</task>

<task type="auto">
  <name>Task 3: pty-lane extensions + golden regeneration + full gates + WINDOWS bookkeeping</name>
  <files>tests/tui/test_pty_driver.py, tests/tui/test_snapshots.py, tests/tui/__snapshots__/monitor_running.svg, tests/tui/__snapshots__/monitor_empty.svg, .planning/WINDOWS.md</files>
  <precondition>The Task 1+2 monitor suite is green and the worktree still holds the uncommitted 08g run_config.svg (verify with git status before regenerating anything).</precondition>
  <action>
    (1) EXTEND tests/tui/test_pty_driver.py (never weaken — the lane is a first-class gate): add test_monitor_tab_switch_paints_history (spawn, boot, send 5, expect the monitor marker, send →, expect the HISTORY tab marker/copy paints within the nav window, send ←, expect the running tab copy again) and test_monitor_running_empty_enter_routes_slot4 (fresh tmp roots, send 5, expect the actionable empty copy, send \r, expect the Run Config marker). Use the existing helpers/_spawn_tui/_boot and English-copy markers; bounded timeouts in the file's established shape. The existing test_monitor_renav_renders_every_visit stays byte-UNMODIFIED (F1 load-bearing).
    (2) Golden regeneration: adapt tests/tui/test_snapshots.py monitor fixtures to the tabbed surface (the _running_monitor_service shape now feeds a Running card for finetuned-mgpu-w0 — with its mgpu-w sibling if the fixture models one — and a History row for finetuned-smoke; monitor_empty shows the actionable empty copy + scanning-free settled state). Run make snapshot-update; VERIFY with git status that ONLY monitor_running.svg + monitor_empty.svg changed — run_config.svg and every other golden byte-identical (sha256 before/after for run_config.svg specifically; the 08g WINDOWS #39 uncommitted version is the protected bytes). Leave both monitor SVGs UNCOMMITTED — they REPLACE the uwr uncommitted pair as ONE combined D-03 monitor-golden handoff (the run_config.svg #39 item stays separate on the tree). make snapshot must compare green in the worktree.
    (3) Full gates at repo root: make test (baseline 1F/1916P — the sole machine-local failure; ZERO new failing members; every NEW test passes; node lane 26/26 via check-node), make lint, make typecheck, and pytest tests/tui/test_pty_driver.py -q as an explicit run (roughly 5 spawns, bounded).
    (4) Bookkeeping: .planning/WINDOWS.md — close #40 and #41 IN PLACE per the one-obligation-one-row amendment discipline (status closed with this quick id; #41's skeleton note references the tab layout; #40 closes because the tabbed design replaces the master-detail view — cite the maintainer 2026-10-18 15:01 approval); amend the #35 (and #39-adjacent) D-03 rows to name the new combined uncommitted monitor-golden set. Plain commits, NO attribution trailers, do NOT push.
  </action>
  <verify>
    <automated>cd /home/forrest/Github/dnallmmark && make test && make lint && make typecheck && make snapshot && git status --porcelain tests/tui/__snapshots__/ | sort</automated>
  </verify>
  <done>pty lane extended with tab-switch + empty-route tests and all pty tests pass; monitor_running/monitor_empty regenerated uncommitted with run_config.svg sha-protected; full suite at 1F/1916P-plus-new with zero new failures; ruff/ty green; WINDOWS #40/#41 closed and D-03 rows updated; commits plain, nothing pushed.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| filesystem → TUI | scan/tee/record reads over operator-named paths (existing, unchanged seams) |
| child process → TUI | live-evidence /proc probe + launcher registry (unchanged) |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-kvj-01 | Tampering | pty-lane spawned console | low | mitigate | Per-test DNALLMMARK_TUI_STATE_DIR/CONFIG_DIR tmp roots stay on every new spawn (the 10-07 hermeticity idiom) — the new tests reuse _spawn_tui unchanged |
| T-kvj-02 | Denial of Service | graduation/diff render path | low | mitigate | Graduation diff is screen-local dict compare on already-arrived messages; cadence stays worker-off-loop (D-09 groups untouched); no new inline scans |
| T-kvj-03 | Information Disclosure | card/copy rendering | low | accept | Presentation-only change over validated service outputs; no new data sources, no network, no package installs |
| T-kvj-SC | Tampering | npm/pip/cargo installs | high | mitigate | Zero new dependencies (pexpect already a dev-group member; ListView/Static/DataTable are existing textual widgets) — no install tasks exist in this plan |
</threat_model>

<verification>
- make test — baseline 1F/1916P, zero new failing members, all new tests green, node 26/26
- make lint && make typecheck — ruff + ty green (the standing gate)
- make snapshot — goldens compare green in the worktree (monitor pair regenerated, run_config.svg + all others untouched)
- pytest tests/tui/test_pty_driver.py — extended lane green; test_monitor_renav_renders_every_visit byte-unmodified
- sha256sum tests/tui/__snapshots__/run_config.svg identical before/after the batch
- grep audit: no user-facing MON_ constant in tui/strings.py carries 发现/sweep 根 machine vocabulary
- git log — plain commit messages, no attribution trailers; nothing pushed
</verification>

<success_criteria>
- The approved two-tab contract is fully implemented: Running cards (one per run, worker rows for multi-GPU), History with per-cell drill and [f], count badges, ←/→+tab switching, actionable empty state routing to slot 4, graduation toast, dual-presence badge, optimistic paint.
- Service layer byte-untouched (sweep_monitor.py, sweep_launcher.py, MonitorBackend service delegations); 08g F1 semantics preserved (fresh screen per nav + session survival, pty renav test unmodified).
- WINDOWS #40/#41 closed; monitor goldens regenerated uncommitted as the single combined D-03 handoff.
</success_criteria>

<output>
Create `.planning/quick/261018-kvj-slot-5-human-logic-redesign-tabbed-runni/261018-kvj-SUMMARY.md` when done
</output>
