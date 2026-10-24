---
status: complete
task: 261019-n0w
title: "slot-5 fix batch: click=select, transparent card fill, D pane lines"
date: 2026-10-19
---

# quick-261019-n0w: slot-5 fix batch from the maintainer's live test — summary

The maintainer's three live-test defects on the just-landed f0x Running
tab are fixed in one atomic commit: a mouse click on a matrix card now
SELECTS and focuses it (never drills — Enter stays the only drill
trigger), the highlighted card renders as content instead of a
full-pane block-cursor fill, and the right pane carries the approved
D composition's two data lines (20-cell progress bar + percent + derived
rate; step/max + point-ETA with wall clock) over service-honest fields
only. Every landed continuity contract stays green: the rze
lines-signature gate covers the new lines (steady ticks zero-write),
the pty lane is 11/11 with the click member reworked to the
click=select contract, and the two monitor goldens are regenerated
exactly once and left UNCOMMITTED under the still-open WINDOWS #42.

## Task 1 — the three fixes + the re-pinned contracts (commit 3da03a6)

**Landed:**
- **Click suppression:** `MatrixCardsList(ListView)` swapped in at the
  `#mon-cards` compose site; `_on_list_item__child_clicked` is the
  stock textual 8.2.8 body minus the `Selected` post. Every
  `query_one("#mon-cards", ListView)` call site byte-unchanged (the
  subclass IS a ListView); `on_list_view_selected` byte-unchanged (now
  purely the Enter path). Module docstring updated (the ListView
  bullet + one 261019-n0w contract note in the execution-recorded
  block).
- **The transparent fill:** `#mon-cards > ListItem.-highlight
  { background: transparent; text-style: none; color: $text; }` in the
  monitor styles block — the app-level ID rule outranks both ListView
  DEFAULT_CSS `-highlight` variants; the DEFAULT_CSS `-hovered` rule
  untouched (subtle hover survives).
- **The D pane lines:** `_right_detail_lines` inserts, when the
  already-resolved progress carries `percent is not None`, (a) the
  20-cell bar line (`█`/`░` at `_BAR_WIDTH`, the
  `_entry_progress_cell` rounding idiom, accent/dim styles, percent,
  then `MON_STRIP_RATE` or the dim dash) and (b) the step/ETA line
  (`MON_DETAIL_STEPS` when step+max present; the strip's point-ETA
  grammar with the wall clock over the module `time` —
  golden-freezable; the dim dash when `eta_seconds` is None; the range
  leg can never occur — one CellProgress resolves). Absent progress
  renders NEITHER line (T-f0x-02 held). `+MON_DETAIL_STEPS` in
  strings.py (zh == en, the data-forward MON_COL_SEED/MON_STRIP_RATE
  precedent); the tripwire `EXPECTED_MON_CONSTANTS` +1 in the same
  edit.
- **Pilot pins:** NEW `test_click_selects_card_without_drill_then_enter_drills`
  (index moves, focus lands, no modal; Enter then opens it) + NEW
  `test_highlighted_card_renders_without_block_cursor_fill`
  (`-highlight` class present; effective `styles.background.a == 0`,
  text-style neither bold nor reverse). EXTENDED: the detail-fields pin
  now asserts both new lines + their order (header -> bar -> step ->
  first seed line, with the ETA regex paren-shaped for either active
  language); the focus-move pin proves the lines follow the FOCUSED
  group (absent on the progress-less task-2); the tail-sig steady leg
  also spies `#mon-detail` `update` at zero calls (inside a new
  `_frozen_pane_clock` window — the new wall clock would otherwise
  flip the lines signature on a minute boundary).
- **Pty rework:** `test_click_running_card_opens_run_cells_modal` ->
  `test_click_selects_card_enter_still_drills`: spawn/boot/click
  coordinates byte-as-is (col 8 row 5); after the SGR press+release a
  bounded 2s TIMEOUT window asserts the modal-title marker ABSENT from
  `child.before`, then `\r` re-expects the marker (Enter still
  drills). The module docstring's contract phrase updated; the other
  10 members byte-untouched.

**Test evidence:** the plan's Task 1 verify —
`.venv/bin/python -m pytest tests/tui/test_pilot_monitor.py
tests/tui/test_strings_phase11.py tests/tui/test_pty_driver.py -q` ->
**117 passed** (pilot 94 with the 2 new pins + 3 extensions, strings
12, pty 11). ruff + ty clean via the venv (touched files + repo-wide
`ty check`). No service-layer file touched.

**Deviations (auto-fixed, all same-truth):**
- **[Rule 1 — plan mechanism defect] `event.stop()` alone does NOT
  suppress the stock handler.** Textual 8.2.8's
  `_get_dispatch_methods` walks the FULL MRO and invokes the
  naming-convention handler from EVERY class, so the stock
  `_on_list_item__child_clicked` ran AFTER the override on the first
  cut and still posted `Selected` (probe-verified with a post_message
  spy + traceback: the modal opened despite the override running).
  Fix: `event.prevent_default()` — textual's own flag that breaks the
  MRO walk before the base class yields its handler (message.py
  `prevent_default`: "prevent handlers in any base classes from being
  called"). Both flags now set; probe-verified the Selected post never
  fires and Enter still drills. Documented in the class docstring.
- **[Sanctioned fallback used] pilot click targeting misfires at this
  grid:** the second card sits below the fold (the first card's
  ListItem stretches across the visible list, Region y=39 at 120x40),
  so a positional `pilot.click` cannot land on it (returns False,
  index unmoved). The test posts `ListItem._ChildClicked(item)`
  directly — the exact message the mouse path produces — per the
  plan's sanctioned fallback; the REAL SGR mouse path stays
  pty-pinned.
- **[Rule 1 — test robustness] the steady-leg zero-write pin needed a
  frozen clock:** the new step line carries the ETA wall clock, so a
  minute boundary between the initial render and the steady tick
  would legitimately rewrite `#mon-detail` and flake the new zero-call
  assertion. `_frozen_pane_clock` (the golden drives'
  `_frozen_mon_clock` idiom, pinning monitor.py's module `time`) wraps
  the test window.
- **[Rule 1 — test correctness] the pane renders in the ACTIVE
  language:** the pilot app boots zh, so the en-shaped ETA regex
  (`(HH:MM)` half-width parens) failed against `（HH:MM）` full-width.
  The regex now accepts either paren shape (the data segments
  themselves are language-neutral).

## Task 2 — golden regeneration (once, uncommitted) + full gates

**Landed:** baseline sha256 recorded FIRST (all 9), then
`.venv/bin/python tests/tui/test_snapshots.py --regenerate` ran
EXACTLY ONCE. Versus the committed tree: exactly
`monitor_running.svg` + `monitor_empty.svg` changed; the other 7
byte-identical (`run_config.svg` among them — never touched). Versus
the f0x worktree bytes the regen superseded: `monitor_running.svg`
changed (the CSS fill fix — the highlighted card no longer painted in
the block-cursor fill; strip/matrix/pane/footer composition reviewed
intact as SVG text: the strip row, the three matrix rows, the pane's
detail header + seed line + the round-bordered no-tee log region, the
[w] footer keycap, the frozen clock holds) while `monitor_empty.svg`
came out byte-IDENTICAL to the f0x bytes — the empty screen has no
highlighted card and no progress, so the n0w deltas are invisible
there and the f0x B+D composition delta vs HEAD stands unchanged.
BOTH SVGs LEFT UNCOMMITTED — WINDOWS #42 remains the open window
(`.planning/WINDOWS.md` is orchestrator-owned and untouched; #42's
pending bytes are now the n0w composition, superseding the f0x
bytes).

**Known observation for the maintainer's D-03 review round (per the
plan):** the golden service fake carries no `entries_progress` (the
tolerant seam reads {}), so the two new detail lines honestly do NOT
render in `monitor_running.svg` — the pane goes header -> seed line
directly. The fixture was deliberately NOT extended to chase the new
lines; the SVG delta is the CSS fix only.

**Test evidence:** the plan's Task 2 verify —
`.venv/bin/python -m pytest tests/tui/test_snapshots.py
tests/tui/test_pty_driver.py -q` -> **22 passed** (snapshot lane 11/11
in the worktree; pty lane 11/11). Full suite
`.venv/bin/python -m pytest tests/tui -q` -> **1263 passed, 1 failed**:
exactly the documented environmental
`test_storage_overview_defaults_mirror_real_consumers`
(`pipeline/logs/` exists — the maintainer's live run; pre-existing,
out of scope). No slot-4 flake this round (it TIMEOUTed once under the
three-lane run earlier and passed standalone in 0.57s — the f0x
record's intermittent, untouched slot-4 territory). ruff + ty clean
via the venv (repo-wide `ty check` = the `make typecheck` scope; the
Makefile's own targets use `uv run` and were NOT invoked).
`git status --porcelain` confined to the 2 UNCOMMITTED SVGs + the
orchestrator's .planning bookkeeping; no Co-Authored-By trailers; no
file deletions.

## Commits

- `3da03a6` — fix(quick-261019-n0w): slot-5 click=select, transparent
  card fill, D pane bar/step lines (the single Task 1 atomic commit —
  all three fixes + every pin rework; Task 2 is worktree-only by
  design).

## Self-Check: PASSED

Commit 3da03a6 is an ancestor of HEAD; the six Task-1 files landed in
it; the two regenerated monitor SVGs are present in the worktree and
UNCOMMITTED; the other 7 goldens sha-identical to HEAD; zero real GPU
launches; the maintainer's live sweep (finetuned-smoke) never touched
(all pty tests on isolated tmp roots).
