---
phase: quick-261019-pe0
plan: 01
status: complete
subsystem: tui-monitor
tags: [monitor, running-tab, tree, three-state-cycle, auto-fallback, nav-contract, click-law, gate-law, pilot, pty-lane, goldens]
commits:
  - e9027ee
  - 29d5fda
files:
  - tui/screens/monitor.py
  - tui/styles.tcss
  - tui/strings.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_strings_phase11.py
  - tests/tui/test_pty_driver.py
goldens_regenerated_uncommitted:
  monitor_running_svg: d468d33791cb75877b6232c3bdd461fb832aacb76f513dd36e2c7e5f56017289
  monitor_empty_svg: 258ab609191b89ff6ffae7cbca91537bbb69a2445391c812dc5e845344e2d000
goldens_baseline_worktree:
  monitor_running_svg: 69552bed83c246c2da12e994f7bde8a56292afcf7e1e2474630329132b465947
  monitor_empty_svg: c532af61750779e26a324121ef2ba6993f461ba95ef03e2d589540e5cf09557b
goldens_untouched:
  run_config_svg: c7e144589480e7fd7e7ae2cac00598906657849d68316238764e4a32f50da2d3
windows_entry: "42 (still open, .planning/WINDOWS.md — orchestrator-owned; NO new entry; the two monitor SVGs remain uncommitted, now the pe0 footer-keycap composition)"
---

# quick-261019-pe0: slot-5 tree mode — the left pane's third state — summary

The Running tab's left pane is now a THREE-STATE cycle over [w]
(matrix -> tree -> wide -> matrix): each card renders a Textual
`RunCardTree` under its strip (model nodes: name + the o8e filtered
done/total; task leaves: the key + the per-seed glyph cluster with the
compact inline percent + derived rate on parsed running seeds), the
pane DEFAULTS to tree when any card's matrix exceeds the width budget
(a pure derivation; a manual choice holds until the next structural
change), the maintainer-LOCKED navigation contract and the click law
hold verbatim, and the rze/f0x/n0w/o8e gate-law family extends to the
new widget (structure sig + screen-side expansion/cursor caches
surviving ListItem rebuilds, in-place set_label diffs, steady
zero-write). Zero service-tier changes; the 12 prior pty members green
with the arrows member re-pinned to the cycle + one new tree member.

## Task 1 — the tree state + the mode machine + the six pilot pins (commit e9027ee)

**Landed (tui/screens/monitor.py):**
- `RunCardTree(Tree)` beside `MatrixCardsList`: `auto_expand=False` +
  `show_root=False` (ATTRIBUTE assignments — see deviations),
  `_on_click` override = the n0w law extended (`event.stop()` +
  `event.prevent_default()`, the MRO-walk lesson; toggle-icon branch
  native; label branch = focus + cursor + ONE `CardPicked` post,
  NEVER `NodeSelected`); `TreeMounted` notification so the screen can
  focus the fresh tree after the asynchronous mount.
- The mode machine (`_left_mode` / `_left_mode_user` /
  `_left_mode_struct_sig` + the `_tree_sigs`/`_tree_expand`/
  `_tree_cursor` caches): the `_wide` READ-property keeps every
  pre-existing `_wide` read byte-unchanged; both `_wide` assignments
  deleted; on_mount resets every sentinel (the L-toggle recompose
  lands auto-mode).
- `_matrix_width_budget` (DOM read CAPPED by the screen arithmetic —
  the first-layout race, probed) + `_card_matrix_overflows` (narrow
  never overflows — the count-row matrix has no task columns) +
  `_derive_left_mode` (user-or-auto; "wide" only via the manual cycle;
  pure function of task sets + width).
- `_render_cards`: the structural hold-check at the top, the mode
  re-derive, the early-return converted to if/else so the per-card
  tree pass runs on BOTH paths; `_cards_signature` gains the mode leg;
  `_cards_struct_legs` extracted (the hold-check's tuple).
- `_card_content` tree branch (strip + resume only) /
  `_card_widget` appends a POPULATED tree at construction (the
  same-pass query impossibility — probed); `_build_card_tree` = the
  one build path (expansion from the cache, fresh defaults
  all-expanded; cursor re-pin capture > focused group > first node,
  with a hidden-task -> model fallback); `_render_card_tree` = the
  label pass with the f0x plain+spans in-place compare;
  `_tree_model_label` / `_tree_task_label` (the compact `30%` +
  `1.0 it/s` cyan-bold on parsed running seeds, glyph-only otherwise).
- `action_cycle_left` (replacing `action_toggle_wide`) with the focus
  unification: leaving wide derives `_focus_pos` from the wide cursor
  row (+ the card index follows — the coordinate is card-relative);
  entering tree pins the cursor onto the focused group's task node;
  entering wide lands the cursor on the focused group's row.
- The locked arrow contract: `_tree_arrow_horizontal`
  (expand-or-into / collapse-or-parent, the invisible root never a
  target, task no-op) + the vertical delegation to the tree's NATIVE
  clamped cursor actions (no card crossing in tree state);
  `action_tree_toggle_all` ([*] expand/collapse-ALL across every card
  with the cursor salvage to its model node); `on_tree_node_selected`
  (model = toggle NEVER a modal; task = `_open_run_drill` with the
  pinned key); `on_tree_node_highlighted` (writes the shared
  `_focus_pos`, `_normalize_focus`, the exact `_repaint_focus_move`
  tail; wrong-card highlights ignored — the build-pin storm);
  `on_run_card_tree_card_picked` (the ListView index follows);
  `on_tree_node_expanded/collapsed` (the expansion cache sync);
  `_focus_active` tree branch (the focused card's tree holds focus so
  its OWN enter binding owns Enter).
- BINDINGS: `w` -> `cycle_left` (keycap byte-identical) + `*` ->
  `tree_toggle_all` (+MON_TREE_TOGGLE_KEYCAP, zh "± 全部" / en
  "± all"); `_RUNNING_SCOPED_FOOTER_KEYS` gains `*`.
- styles.tcss: `.mon-card-tree { height: auto; }` (probe-verified: the
  tree sizes to its content inside the ListItem, the ListView
  scrolls); strings tripwire +1 in the same commit; the 261019-pe0
  module-docstring contract bullet.

**Pins (tests/tui/test_pilot_monitor.py):** SIX new —
`test_tree_state_renders_model_and_task_nodes` (the o8e reused-root
fixture + progress: 0/3 filtered basis, no residue node, s42 ⏵ 30%
1.0 it/s + s43/s44 glyphs, the w-w-w cycle),
`test_tree_navigation_contract` (every locked leg driven with real
keys; up-at-the-first-node clamps with NO card crossing; Enter
model=toggle-no-modal / task=drill-pinned; `*` collapse-all ->
expand-all; Tab switches), `test_tree_click_selects_node_without_drill`
(the synthetic `events.Click` with `Style.from_meta` — the n0w
sanctioned fallback; cursor + card index + tree focus, no modal,
Enter still drills), `test_matrix_overflow_defaults_to_tree_and_
manual_holds` (the eight-20-char-key fixture renders TREE at (120,40)
with no press; two w's reach matrix and HOLD across a frontier tick;
a new task via `_tick_full` resets to auto TREE; the narrow boot
derives matrix — count rows), `test_tree_steady_tick_zero_write_and_
rebuild_preserves_state` (zero clear/set_label/Label writes on the
steady tick; the new-task rebuild preserves the collapsed model +
the cursor data key + presents the new node),
`test_tree_focus_unification_feeds_right_pane` (matrix (0,1) -> tree
cursor on that task node + the pane names it; down-down feeds the
pane; entering wide lands the group's row; leaving wide repaints the
matrix highlight on the same group). THREE sanctioned re-pins: the
wide-toggle, wide-arrows, and o8e live-pair members press w TWICE to
reach wide (the returns stay ONE w — wide -> matrix directly); the
wide-toggle member's final assert now names the tree pass-through.

**Test evidence:** pilot suite **104 passed** (98 prior incl. the
re-pins + 6 new); strings tripwire 12; ruff + `ty check tui/
tests/` clean (one textual-library annotation split handled by a
documented `cast`); no service-layer file touched.

## Task 2 — the pty tree pin + the arrows re-pin + goldens + full gates (commit 29d5fda)

**Landed (tests/tui/test_pty_driver.py):** the arrows member's final
[w] round trip re-pinned to THREE presses (the fresh tree marker
`0/2` -> the wide `State`/`Progress` headers -> the matrix
`_CARD_NAME_MARKER`); every arrow/tab assertion above byte-untouched
(the fixture's 2 tasks fit the 120-col budget — auto matrix). NEW
member `test_monitor_tree_state_navigates_and_drills` (~12s): w ->
`0/2` + `0/1` markers, `*` collapse-all (the cursor salvage onto the
model node), Enter-on-model = a bounded 2s `_RUN_CELLS_MARKER`
ABSENCE (toggle, never a modal), a REAL SGR click at col 8 row 6 (the
first model node under the strip — the click member's calibration) =
another bounded absence, then down + Enter = the marker RETURNS
(Enter is the only drill trigger). The Task-2 commit also carries the
pilot click pin's `Style.from_meta` refinement (ty-clean).

**Goldens:** baseline sha256 recorded FIRST (the WORKTREE bytes — the
o8e-recorded values above). The snapshot lane ran RED on exactly the
two monitor members — the sanctioned cause: the Running-tab footer
gains the `[*]± 全部` keycap (the plan's "expected NO delta" held only
for the MODE — the fixture's 2 tasks fit the budget, auto = matrix).
Regenerated EXACTLY ONCE via `.venv/bin/python
tests/tui/test_snapshots.py --regenerate`; the SVG text reviewed:
ZERO tree guides (└──/├── absent — the tree never rendered), the
matrix rows/strip/pane composition intact, the delta is the
`[*]± 全部` keycap after `[w]宽表` in BOTH monitor SVGs. The other 7
goldens byte-identical (`run_config.svg` c7e14458… never touched).
BOTH MONITOR SVGs LEFT UNCOMMITTED — WINDOWS #42 stays the open
window (no new entry; .planning is orchestrator-owned).

**Test evidence:** pty lane **13/13** (12 prior members green and
byte-stable + the new member); snapshot lane **11/11** post-regen;
the full suite `.venv/bin/python -m pytest tests/tui -q --deselect
tests/tui/test_services_run_config.py::test_storage_overview_
defaults_mirror_real_consumers` -> **1275 passed, 1 deselected**; the
deselected member re-run standalone confirms the documented
environmental cause (`pipeline/logs/` exists — the maintainer's LIVE
sweep writes there; never touched). No slot-4 pty flake this round.
ruff + `ty check tui/ tests/` clean via the venv. `git status
--porcelain` confined to the plan's files (committed) + the 2
uncommitted monitor SVGs + the orchestrator's .planning bookkeeping;
no Co-Authored-By trailers; zero real GPU launches; all pty tests on
isolated tmp roots; the maintainer's live sweep never touched.

## Deviations (auto-fixed / plan-wording, all same-truth)

1. **[Rule 1 — plan mechanism] `Tree.__init__` takes NO
   `auto_expand`/`show_root` kwargs** (probed textual 8.2.8 — the
   plan's constructor spec would TypeError): they are attribute
   assignments after `super().__init__("", ...)` (`show_root`'s
   reactive watcher resets the cursor — harmless pre-mount).
2. **[Rule 1 — probe finding] a same-pass `query_one` on a freshly
   appended ListItem FAILS** (textual defers the mount): the tree is
   POPULATED AT CONSTRUCTION in `_card_widget` (one shared
   `_build_card_tree` path), `_render_card_tree` no-ops on fresh
   items, and the post-switch FOCUS move rides the tree's own
   `TreeMounted` message (`call_after_refresh` proved unreliable in
   Pilot — probed; explicit `_focus_active()` worked, the deferred
   copy never fired).
3. **[Rule 1 — probe finding] the naive DOM budget read RACED the
   first layout**: at the first scan paint `#mon-left`'s
   `container_size` still reflects the pane-hidden stretch (~120
   cells), admitting a matrix that overflows the moment the layout
   catches up (a 118-cell fixture derived matrix; probe-pinned).
   `_matrix_width_budget` CAPS the DOM read by the screen-width
   arithmetic (`min(dom, width-40)` wide / full width narrow).
4. **[Plan-wording imprecision] one-w-to-matrix**: the overflow pin's
   text says "press 'w' -> matrix"; the LOCKED cycle (matrix -> tree
   -> wide -> matrix) needs TWO presses from auto-tree (tree ->
   wide -> matrix). The truths' cycle wins; the pin drives two.
5. **[Plan-wording imprecision] the pty residue marker**: the plan
   claimed the interrupted seed "is terminal" (`1/1`); the LOCKED o8e
   basis (done = completed+failed+skipped) counts interrupted in the
   TOTAL only (`0/1`). The truths' arithmetic wins (the same basis
   the strip and the pilot pins already assert).
6. **[Rule 1 — pty drive restructure]** the plan's
   up-up-after-modal-escape drive proved timing-fragile over the real
   console (the pexpect drain-consume semantics + the modal-escape
   interleave made the absence windows unreliable — probe-pinned);
   the member reorders so EVERY marker-absence window runs BEFORE the
   first modal byte enters the buffer, using `*`'s cursor salvage to
   land on the model node instead of up-up. Every locked leg is still
   pinned; the tree-up leg stays pilot-pinned.
7. **[Plan wording] the verify line listed `tui/styles.tcss` under
   ruff** (ruff is Python-only) — ruff ran over the Python files.
8. **[Card-index follow] `_leave_wide_derive_focus`** also sets the
   ListView index to the wide cursor row's card (the plan named only
   `_focus_pos`; without the index the clamp resolves against the
   wrong card — the coordinate is card-relative). Documented in the
   docstring; pinned by the focus-unification test.
9. **[`_on_click` ordering]** `CardPicked` posts BEFORE the
   `cursor_line` write (the plan's order was cursor-then-post), so
   the NodeHighlighted sync resolves against the CLICKED card (the
   index is the card-focus authority). Cross-card clicks pinned.
10. **[Narrow leg]** `_card_matrix_overflows` returns False when
    narrow (the narrow matrix is per-model count rows — no task
    columns; the tree solves a column-count problem); documented and
    pinned by the overflow test's narrow-boot leg.

## Maintainer-review flags (per the dispatch)

- **No card-crossing on tree up/down**: pinned pilot-side
  (`test_tree_navigation_contract`: up at the first visible node
  keeps the cursor AND `cards.index == 0`); the pty side rides the
  native clamped-cursor delegation.
- **Task-node compact percent form**: `30%` (cyan bold) + the derived
  `1.0 it/s`, glyph-only without parsed progress, no steps/bar
  grammar — pinned in `test_tree_state_renders_model_and_task_nodes`
  and pty-visible in the `s9527 ⏵` renders.

## Verification-gate cross-check

- Plan per-task verify green (Task 1: pilot + strings + ruff + ty;
  Task 2: pty + snapshots + full suite + ruff + ty).
- Pilot 104+ green; pty 13/13; strings tripwire green.
- Full suite green except the documented collateral (pipeline/logs;
  no slot-4 flake this round).
- ruff + ty clean via `.venv/bin/python`; `git status --porcelain`
  confined to the plan files + the 2 uncommitted monitor SVGs +
  orchestrator bookkeeping.

## Self-Check: PASSED

Commits e9027ee and 29d5fda are ancestors of HEAD (autorun); the six
plan files landed across them; the two regenerated monitor SVGs are
present in the worktree and UNCOMMITTED; the other 7 goldens
sha-identical to the pre-task recording; no attribution trailers; the
service tier untouched; zero real GPU launches.
