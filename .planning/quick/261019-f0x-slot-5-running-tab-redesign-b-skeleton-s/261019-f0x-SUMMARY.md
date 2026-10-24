---
phase: quick-261019-f0x
plan: 01
status: complete
subsystem: tui-monitor
tags: [monitor, running-tab, matrix, right-pane, wide-toggle, pilot, pty-lane, goldens]
commits:
  - bea0e16
  - 0aa9436
  - 23e7f5c
  - f9023af
files:
  - tui/screens/monitor.py
  - tui/strings.py
  - tui/styles.tcss
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pty_driver.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_snapshots.py
goldens_regenerated_uncommitted:
  monitor_running_svg: worktree-only, pending D-03 review
  monitor_empty_svg: worktree-only, pending D-03 review
goldens_untouched:
  run_config_svg: c7e144589480e7fd7e7ae2cac00598906657849d68316238764e4a32f50da2d3
  wizard_svg: 4449097f376aab4f780df8e14f96f8875e90d522acff6204062ffee8a67a1c76
windows_entry: "42 (open, .planning/WINDOWS.md — uncommitted, orchestrator-owned)"
---

# quick-261019-f0x: slot-5 Running-tab redesign (B skeleton + D right pane) — summary

The Running tab now renders the maintainer-approved B+D composition:
per-card summary strip + all-cells matrix with arrow-driven group focus
on the left, the ~40-col right pane with honest focused-group detail and
the live tee tail beside it, and the [w] wide toggle — while every
landed continuity contract (rze byte-silence gates, kvj tab pins, toe
[d]/[e], click-to-drill, dead-5 renav, pty lane) stays green. Zero
service-tier changes; every number an existing service field or pure
arithmetic over them.

## Task 1 — the B-skeleton left pane (commit bea0e16)

**Landed:** the running card's old body (scale/total/current/worker
lines) is replaced by the summary strip (root name bold; per-category
seed counts with queued always; the done/total fraction over the stats
precedence aggregated across the card's roots with None-propagation;
the 20-cell segmented bar with floor+largest-remainder allocation,
deterministic category-order tiebreak; minute-granularity elapsed via
the new pure `_format_elapsed_short`; the ETA segment — point+wall
clock / multi-root min–max range / dash; the derived rate via
`_rate_of` = (max_steps−step)/eta_seconds) over the matrix (head +
one row per sorted model, per-task seed-glyph groups, column width
max(4, min(len(task)+1, 14)), name column 20 cells, rich-native glyph
styles, style-only reverse highlight, seed-overflow ellipsis backstop)
plus the surviving resume note. `_card_rows` is the ONE merged row map
(seed-merge priority running > failed > interrupted > completed/skipped
> queued) feeding strip/matrix/pane/wide. Bindings: left/right rebind
to `action_arrow_horizontal` (matrix focus on Running with groups; tab
switch preserved on empty/no-groups/History — kvj intact; Tab always
switches), up/down join the priority family (`action_arrow_vertical`:
matrix rows on Running with card crossing at the edges and the
ListView index following programmatically; delegated NATIVE
`action_cursor_up/down` on every table surface — probed present on
textual 8.2.8). `[enter]` drills through the RunCellsModal with the
ADDITIVE `focus_key` pinning the modal cursor to the focused group's
row (default None keeps every existing site source-compatible). The
rze gates extend: the cards sig carries narrow + the merged matrix
shape + the focus tuple + the focused card index (a focus move
repaints exactly the two affected matrix-row Labels in place via
`_repaint_focus_move`, zero ListView churn), the in-place Label
compare now covers SPANS (style-only changes repaint), and on_mount
resets every new sentinel. Strings: +MON_STRIP_ELAPSED/ETA/ETA_RANGE/
RATE, +MON_WIDE_KEYCAP; the four card-line constants deleted (the kvj
retirement precedent) with the bidirectional tripwire edit (+5/−4).

**Test evidence:** `tests/tui/test_pilot_monitor.py` 83 passed
(re-pinned + new pins); the pty lane 10/10 untouched-green;
`tests/tui/test_strings_phase11.py` 12 passed; the 7 non-monitor
goldens sha-identical to the pre-task recording; the 2 monitor golden
members red on the committed SVGs exactly by design (regeneration is
Task 4); ruff + ty clean.

**Deviations (auto-fixed / re-pinned, all same-truth):**
- [Rule 1 — bug] The first draft used `$text-muted` styles in
  Label-bound strip Texts — the $token-crash probe pin fired exactly as
  the plan warned (`MissingStyle: $text-muted`); fixed to rich-native
  `dim` in the strip's dash legs.
- [Rule 1 — bug] `_focused_group()` returns a fresh `_RunCard` wrapper
  per `_cards()` call, so the focused-card test compares ROOTS
  identity, never `is`.
- [Rule 1 — bug] the rebuild branch assigned the ListView index AFTER
  computing the cards sig (the sig carries the index) — the sig now
  recomputes after the pin, or the very next tick rebuilt again.
- [Rule 1 — bug] a carried focus column did not clamp to the crossed
  card's shape at write time — `_move_focus_row` now normalizes on
  crossing.
- [Sanctioned re-pin] `test_enter_drills_run_cells_then_cell_detail`:
  the modal cursor now opens on the FOCUSED group's row (sorted-first
  model = plant-dnabert), so the second enter drills that group — the
  designed additive focus_key behavior; the fixture gained the focused
  group's record and the assertions pin the same verbatim-fields truth
  against it.
- [Sanctioned re-pin] three tests pressed `right` to reach History over
  a card whose fixture scripts cells (now a grouped card: the arrow
  moves matrix focus by design) — they press `tab` instead (always
  switches); the refusal/cursor truths unchanged
  (`test_d_live_root_refuses_before_the_confirm`,
  `test_e_live_root_refuses_before_any_modal`,
  `test_focus_active_noops_when_target_already_focused`).

## Task 2 — the D right pane (commit 0aa9436)

**Landed:** `#mon-right` activates iff wide grid + Running tab + cards
(pane widgets display-only, RichLog `can_focus=False` — no focus
trap). `_render_right_detail` renders the focused group's header
(pane-width ellipsis), per-seed state lines (re-derived at call time),
and the running seed's steps/percent/eta over the shared
`_entry_progress_cell` grammar + the derived rate — existing service
data ONLY (no loss/lr/epoch/params line ever; test-pinned absent).
The `mon-tail` worker (own exclusive group, stage-id tagged, WR-02)
reads the focused card's tee (`tee_path_for` over roots, first
non-None) via the EXISTING `read_log_tail` seam (max_lines=30,
tolerant) on kicks from focus moves, tab switches, width crossings,
and every FrontierScanned/full scan while visible; the write handler
drops superseded stages, skips beneath a stacked modal (next tick
catches up), and gates on the tee+lines signature (unchanged tail =
zero RichLog calls); no-tee renders MON_LOG_UNAVAILABLE once and never
schedules a read. Both pane sigs reset in on_mount; the [t] modal
byte-unchanged.

**Test evidence:** pilot suite 89 passed with the new pins
(detail-fields + no-fabrication, focus-follow, tail sig-gate/rewrite,
no-tee no-reads, narrow-hide + [t], modal suppression with
post-dismissal catch-up); the pty lane 10/10 green; ruff + ty clean.

## Task 3 — the [w] wide toggle (commit 23e7f5c)

**Landed** (the droppable clause never triggered — every continuity
pin stayed green, so nothing was dropped): `[w]` swaps `#mon-cards`
for the `#mon-wide` DataTable on the Running tab (History: silent
no-op); one row per (root, model, task, seed) across ALL live cards,
columns state/model/task/seed/progress/rate (the root column only on
multi-card sweeps — the 120-col budget); rows diff through the
EXISTING `_set_table_rows` (WR-05 cursor identity) gated by a
rendered-content signature (the `_history_sig` precedent); `_wide`
resets in on_mount (the L-toggle recompose lands matrix-first); enter
on the wide table drills the row's OWN root with the drill cursor
pinned to its group (reverse lookup over the caches); wide-mode
arrows: left/right switch tabs, up/down delegate to the wide table's
native cursor actions; the [w] keycap renders Running-tab-only (the
d/e projection mirrored).

**Test evidence:** pilot suite 92 passed (dense rows + progress/rate,
enter drill pin, matrix restore with prior focus, footer scoping,
wide arrow delegation); the pty lane 10/10 green; ruff + ty clean.

## Task 4 — pty pin + goldens UNCOMMITTED + WINDOWS (commit f9023af)

**Landed:** `test_monitor_matrix_arrows_focus_and_tab_switch` (one
spawn, ~12s): RIGHT repaints the pane's detail header with the second
task's pane-truncated key `× GUE__virus_species…` (the unique
fresh-bytes observable — the matrix head truncates the key to its
narrow column) and never switches; TAB switches with cards present;
LEFT switches back; a second LEFT on the grouped Running card moves
focus col 1→0 with the History markers proven ABSENT from a bounded
3s drain; the [w] round trip paints the wide table's header cells and
restores the matrix. `_fabricate_running_root` gained the second
task's checkpoint (fresh mtimes; classification branch unchanged) —
the byte-silence and click members ride the same richer STATIC tree
and stayed green with UNCHANGED click coordinates (col 8 row 5 still
lands on the card's first line, now the strip — no recalibration
needed). The monitor golden drives wrap in `_frozen_mon_clock` (the
`_frozen_dm_clock` idiom pinning monitor.py's module `time`; without
it the ETA wall clock breaks
`test_golden_export_is_deterministic_across_instances` on the minute
boundary) and `_drive_monitor_running`'s docstring is refreshed.
`make snapshot-update` ran EXACTLY ONCE via the venv
(`.venv/bin/python tests/tui/test_snapshots.py --regenerate`): exactly
`monitor_running.svg` + `monitor_empty.svg` changed, the other 7
byte-identical (sha-verified against the pre-task recording); the two
SVGs are reviewed as SVG text (strip/counts/bar/elapsed/ETA, the
three matrix rows, the pane's detail header + seed line + the round-
bordered no-tee log region, the [w] footer keycap — all per the
approved variant-B/D composition) and LEFT UNCOMMITTED (WINDOWS #42
appended to `.planning/WINDOWS.md` and left uncommitted for the
orchestrator; the committed tree fails exactly the two monitor golden
members until the maintainer's D-03 review lands).

**Test evidence:** pty lane 11/11 green; snapshot lane 11/11 green in
the worktree (regenerated goldens present);
`.venv/bin/python -m pytest tests/tui -q` → 1260 passed with exactly
2 reds: `test_storage_overview_defaults_mirror_real_consumers` (the
documented pipeline/logs collateral — the maintainer's live run makes
`pipeline/logs` exist; out of scope) and one intermittent
`test_slot4_gate_refusal_is_visible` pty TIMEOUT under full-suite
machine load (7/8 recent runs green standalone; the test body is
byte-unmodified by this plan and exercises slot 4, untouched
territory — environmental, recorded here for visibility).
`make lint` / `make typecheck` equivalents via the venv (ruff +
`ty check` over tests/ + tui/, and repo-wide ty): all clean.
`git status --porcelain` confined to the plan's scoped files + the 2
UNCOMMITTED goldens + the orchestrator's .planning bookkeeping.

## Known observations for the maintainer's review round

- The strip's ETA wall clock + rate clip visually at the ~80-col left
  pane when the right pane is visible (the B+D split at the 120-col
  grid). The plan's narrow degradation (<100 cols, bar+rate dropped)
  is the only width degradation specified; the full strip content
  remains in the Text and is visible when the pane hides. Surfaced
  for the D-03 SVG review rather than silently re-designed.
- The fabricated-pty-root matrix renders ⏸ interrupted seed glyphs
  (the no-manifest strict-miss live-pair semantics — pre-existing
  honest behavior, unchanged by this plan; now visible in the matrix
  where the old card's lines never showed per-seed states).

## Environment collateral (out of scope, per the dispatch)

- `test_storage_overview_defaults_mirror_real_consumers` fails while
  `pipeline/logs/` exists (the maintainer's live run) — pre-existing,
  untouched.
- The maintainer's live sweep (finetuned-smoke) was never touched; all
  pty tests ran on isolated tmp roots only.

## Self-Check: PASSED

All four task commits are ancestors of HEAD (bea0e16, 0aa9436,
23e7f5c, f9023af); the SUMMARY exists on disk; the two regenerated
monitor SVGs are present in the worktree and UNCOMMITTED; the 7 other
goldens byte-identical; no Co-Authored-By trailers on any commit.
