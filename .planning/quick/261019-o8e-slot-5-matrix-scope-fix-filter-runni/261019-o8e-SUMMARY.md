---
phase: quick-261019-o8e
plan: 01
status: complete
subsystem: tui-monitor
tags: [monitor, running-tab, matrix, live-sweep-scope, strip, wide, fallback, pilot, pty-lane, goldens]
commits:
  - dfdd204
  - 0a3eee5
files:
  - tui/screens/monitor.py
  - tests/tui/test_pilot_monitor.py
  - tests/tui/test_pty_driver.py
goldens_no_delta:
  monitor_running_svg_worktree: 69552bed83c246c2da12e994f7bde8a56292afcf7e1e2474630329132b465947
  monitor_empty_svg_worktree: c532af61750779e26a324121ef2ba6993f461ba95ef03e2d589540e5cf09557b
goldens_untouched:
  run_config_svg: c7e144589480e7fd7e7ae2cac00598906657849d68316238764e4a32f50da2d3
windows_entry: "42 (still open, .planning/WINDOWS.md — orchestrator-owned; no new entry; the two monitor SVGs remain uncommitted, byte-identical to the n0w worktree state)"
---

# quick-261019-o8e: slot-5 matrix scope fix — the Running views filter to the live sweep — summary

The Running tab's current-sweep views (the matrix row set, the
strip's glyph counts + done/total, the [w] wide table) now scope to
the LIVE sweep's planned pair set — the launcher's
`live_sweep_matrices` evidence (registry argv + /proc probe), read
worker-side into BOTH cadence messages and stored before the render
that consumes it — so the maintainer's reused-root case (ONE launched
model beside three residue models from previous smoke runs) renders
exactly ONE row with its 3 seeds and done 0/3. Every evidence gap
(no method / absent root / None / empty set / raising call) keeps
today's root-wide render; the RunCellsModal drill and the History tab
keep the full-root truth; the rze/f0x gate law holds by construction
(no new signature legs); the service tier is untouched.

## Task 1 — the live-pair scoping seam + the four pilot pins (commit dfdd204)

**Landed (tui/screens/monitor.py, presentation-only):**
- `_read_live_matrices()` next to `_entries_progress_of` (the getattr
  precedent, WORKER-side): no method / raising call -> None = keep the
  previous cache; anything else -> a fresh dict copy (a dict, even
  `{}`, IS fresh evidence).
- `FullScanned` / `FrontierScanned` gain the ADDITIVE
  `matrices=None` leg (the focus_key precedent); `_run_full_scan`
  reads it BEFORE its try (an evidence failure can never mask a scan),
  `_run_frontier` reads it once at the top — BOTH messages carry it
  because the frontier tick early-returns while `_live` is empty and
  the mount-kick full scan is what first lands evidence on a fresh
  screen.
- `self._live_matrices` screen-local cache in `__init__`; BOTH
  handlers store it immediately after the run-id guard, BEFORE any
  state mutation/render, with the load-bearing-order comment (a
  store-after-render would flap one tick: sig root-wide, paint
  filtered).
- `_root_live_pairs(root)`: resolved-root key lookup (the
  `_live_pairs_for` idiom); returns the set ONLY when a non-empty
  frozenset — the docstring records the DELIBERATE divergence from
  `MonitorBackend._live_pairs_for` (service strict-miss EMPTY drives
  per-seed STATE derivation; screen None drives PRESENTATION scope).
- The ONE filter seam in `_card_rows`: `pairs = _root_live_pairs(root)`
  per root before the merge — every consumer (strip counts, matrix,
  pane, focus, wide basis, the cards sig's shape legs) follows for
  free through the ONE merged row map (the f0x contract).
- `_card_filter_active` + staticmethod `_card_filtered_done_total`
  (done = completed+failed+skipped, total = all filtered seeds — the
  stats-line terminal convention); `_card_content` computes rows +
  counts ONCE and threads `(done, total)` into the widened
  `_card_strip(card, counts, done, total)` (the internal stats-seam
  read deleted); elapsed/ETA/rate stay stats-seam-scope (surgical).
- `_render_wide` applies the same per-root skip (the wide content sig
  derives from the filtered row_map — automatic); `_wide_row_group`
  untouched; `_read_run_cells` and `_drill_focus_key` carry the
  full-root-snapshot contract comments.
- NO gate code and NO strings.py changes (the filtered models/tasks
  tuples already ARE `_cards_signature`'s shape legs); the module
  docstring gains the 261019-o8e contract note.

**Pins (tests/tui/test_pilot_monitor.py):** `FakeMonitorLauncher`
gains `live_matrices=None` (None = the method stays UNDEFINED,
pin-by-omission — every pre-existing fake keeps exercising the
fallback; dict = sticky; callable = per-read scripting). FOUR new
tests: `test_live_pair_evidence_scopes_matrix_strip_and_wide` (ONE
row, residue absent everywhere, `0/3` not `9/36`, glyph counts ⏵1/◌2
with ⏸ never rendering, wide = 3 live-model rows, drill modal = FOUR
models with the cursor pinned to the focused filtered group);
`test_live_evidence_fallbacks_never_scope` (four legs: no method /
None / empty frozenset / raising — all four models render, `9/36`
stats precedence stands); `test_live_pair_set_change_rebuilds_then_
steady_tick_silent` (root-absent first paint 4 rows -> holder gains
the pair -> REBUILD with ListItem identity changed -> steady tick
zero clear/zero Label writes, identity survives);
`test_focus_clamps_into_filtered_set_on_evidence_transition` (real
"down" onto a residue row -> evidence arrives -> `_focus_pos` clamps
to (0,0), the pane header names the live model, pane never empty).

**Test evidence:** `tests/tui/test_pilot_monitor.py` **98 passed**
(94 prior + 4 new); ruff clean over both files; `ty check tui/
tests/` clean; no service-layer file touched.

**Deviations (auto-fixed, same-truth):**
- [Rule 1 — test iteration detail] the first wide-table assertion
  iterated `wide.rows` with `str(row_key)` — textual RowKey's str is
  the repr, raising CellDoesNotExist; fixed to `row_key.value` (the
  key/value distinction the existing `_table_text` callers never hit
  because they pass known string keys).
- [Plan-wording imprecision, same-truth] the plan's action text
  parenthesized "(queued 3, done 0/3)" against its own fixture
  {42: running, 43/44: queued}; the pin asserts the actual filtered
  truth (⏵1 + ◌2 = the 3 filtered seeds, done 0/3) — the load-bearing
  assertion (filtered basis, never 9/36) is exactly the plan's.

## Task 2 — the pty fallback pin + goldens no-delta + full gates (commit 0a3eee5)

**Landed (tests/tui/test_pty_driver.py):**
`_fabricate_running_root` gains the residue model dir
(`plant-dnamamba-6mer/GUE__emp_H3/seed_9527/checkpoint-118`, the
whole subtree pushed ~2000s stale via os.utime — the
`_fabricate_interrupted_root` idiom; name sorts AFTER
plant-dnabert-6mer so every prior row position is unchanged; tree
stays static) + the docstring's 261019-o8e note. NEW member
`test_monitor_matrix_without_live_evidence_shows_residue_too`: the
real console has NO live evidence for a manual root (no registry
handle, no /proc run_sweep), so the root-wide fallback showing BOTH
models (`dnabert-6mer` and `dnamamba-6mer` in the drained initial
paint) is the honest render; the docstring records the justification
(the filtered path is pilot-only: no injection seam exists for the
registry-argv/proc evidence, and a real sweep in the pty lane breaks
the GPU-free CI law).

**Test evidence:** pty lane **12/12** (11 prior members green and
byte-stable on the richer STATIC fixture + the new fallback member);
snapshot lane **11/11** — **goldens NO delta**: all 9 SVGs
sha256-identical before/after the change
(`monitor_running.svg` 69552bed…, `monitor_empty.svg` c532af61… —
both still the n0w worktree bytes, LEFT UNCOMMITTED under the open
WINDOWS #42; the other 7 byte-identical, `run_config.svg` never
touched). NO regeneration was needed or run. Full suite
`.venv/bin/python -m pytest tests/tui -q --deselect
tests/tui/test_services_run_config.py::test_storage_overview_defaults_mirror_real_consumers`
-> **1268 passed, 1
deselected**; the deselected member re-run standalone confirms the
documented environmental cause (`pipeline/logs/` exists — the
maintainer's LIVE plant-dnabert/hyenadna sweep is writing there;
pre-existing, out of scope). No slot-4 pty flake this round. ruff +
`ty check tui/ tests/` clean. `git status --porcelain` confined to
the 2 uncommitted monitor SVGs + the orchestrator's `.planning`
bookkeeping; no Co-Authored-By trailers; the maintainer's live sweep
(finetuned-smoke, PIDs ~3109193/3109195) never touched — all pty
tests on isolated tmp roots; zero real GPU launches.

## Verification-gate cross-check

- Plan per-task verify green; pty lane 12/12 (incl. the new fallback
  member); pilot pins green (the maintainer's exact 4->1 case +
  fallback legs + gate-law rebuild/zero-write + focus clamp).
- Full tui suite green except the documented collateral.
- ruff + ty clean via .venv; `git status --porcelain` as specified.

## Self-Check: PASSED

Commits dfdd204 and 0a3eee5 are ancestors of HEAD; the three scoped
files landed in them; the two monitor SVGs are byte-identical to the
pre-task worktree state and UNCOMMITTED; the other 7 goldens
sha-identical; no attribution trailers; service tier untouched.
