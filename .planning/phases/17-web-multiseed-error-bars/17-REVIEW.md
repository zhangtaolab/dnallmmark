---
phase: 17-web-multiseed-error-bars
reviewed: 2026-10-21T12:39:12Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - script/export_runs.py
  - script/summarize_comparison.py
  - dnallm-mark/js/error-bars.js
  - dnallm-mark/js/main.js
  - dnallm-mark/js/task.js
  - scripts/generate-errorbar-fixtures.js
  - docs/METHODOLOGY.md
  - tests/js/error-bars.test.js
findings:
  critical: 0
  warning: 0
  info: 3
  total: 3
status: issues_found
---

# Phase 17: Code Review Report — Post-Fix Re-Review (iteration 2 of --auto)

**Reviewed:** 2026-10-21T12:39:12Z
**Depth:** standard (with execution verification: full Node lane re-run, determinism + aggregation Python lanes re-run, diff-level verification of both fix commits)
**Files Reviewed:** 8 (7 from the workflow file list + `tests/js/error-bars.test.js` from required reading)
**Status:** issues_found — 0 new findings; 3 known Info items carried

## Summary

This is the post-fix re-review after iteration 1 found 2 Warnings (17-REVIEW.iter2.md),
both fixed in `3a8bc19` (WR-01) and `6930fed` (WR-02). Both fixes are **verified
correct, complete, and side-effect-free**. No new Critical or Warning findings were
introduced. The three known Info items (IN-01/IN-02/IN-03) remain accurate, remain
without live impact, and are carried below unchanged in substance with refreshed line
numbers.

### Fix verification

**WR-01 (3a8bc19) — bar-cap orientation dispatch: FIXED.**
`dnallm-mark/js/error-bars.js:117-159` now branches on
`chart.options.indexAxis === 'y'`: horizontal bars keep the `el.y` anchor, the x value
scale, `[chartArea.left, chartArea.right]` clamping, and horizontal strokes; vertical
bars (the previously broken latent path) use `el.x` (the category axis — `el.y` of a
vertical bar lies on the value axis), `chart.scales.y`, `[chartArea.top,
chartArea.bottom]` clamping, and vertical strokes with horizontal caps. I hand-traced
the geometry for both orientations through `whiskerGeometry`/`clampPixel` against
mock scales and the arithmetic is correct in both branches, including the clamp-order
(`Math.min(ceil, Math.max(floor, pixel))`) and the retained
`!valueScale` / `isFinite` guards. The fix matches iteration 1's suggested code
nearly verbatim. The commit's diff touches only this module's docs + bar-cap branch
and the test file — nothing else moved. The three new 3b draw-dispatch tests
(`tests/js/error-bars.test.js:191-246`) execute `afterDatasetsDraw` against
recording-ctx mock charts with **distinguishable clamp axis pairs** (left 10 / right
390 vs top 0 / bottom 300) and pin the exact stroke sequences: vertical anchor on
`el.x` with vertical strokes, the clamp regression (raw 2.0 → pixel 400 clamped to
bottom 300, where the pre-fix hardcoded pair would have clamped to 390), and the
horizontal path unchanged. All pass.

**WR-02 (6930fed) — scatter tooltip self-qualification: FIXED.**
`dnallm-mark/js/main.js:365-377` now emits
`` Raw-score seed spread: ±${p.std.toFixed(4)} (n=${p.n_seeds}) `` only when
`typeof m.performance?.std === 'number'`, with a comment explaining the dimensional
relationship (mean of per-task raw-metric population stds, not an error bound on the
weighted/rank score). The guard-on-`m.performance` / read-via-`p` split is safe (the
guard is false whenever `p` would be undefined). The source-pin test
(`tests/js/error-bars.test.js:365-387`) asserts the qualified label, the `(n=N)`
suffix shape, and `doesNotMatch /Seed spread: ±/` on main.js. Verified: the qualified
label's lowercase "seed spread" does not trip the capital-S negative pattern, and
main.js contains no other occurrence. Note, explicitly not a finding: `task.js:443`
still says `Seed spread: ±` — that is the task page, where the line renders only when
the selected metric IS the dataset's declared primary (gating at `task.js:320-323`),
so the whisker there is the seed spread of the exact metric being displayed;
dimensionally accurate, correctly outside WR-02's scope.

### Invariant re-checks (iteration-1 invariants, re-verified at HEAD)

- **Committed leaderboard data untouched** — `git diff 0c879b4..HEAD -- dnallm-mark/data`
  is empty and the working tree under `dnallm-mark/data` is clean; the Node lane's
  committed-data-absence tests (no `std`/`n_seeds`/trio keys anywhere in the public
  tree) pass.
- **Vendored banner byte-untouched** — the `@483a35c` section extracted from base
  `0c879b4` and from HEAD diffs empty (105 lines, character-identical);
  `population_std` still sits after the END marker and never feeds `aggregate_seeds`.
- **Ranking math untouched / determinism holds** — `tests/test_determinism.py` +
  `tests/test_aggregation.py` re-run at HEAD: **40 passed**. The fix commits touch no
  Python file (only `error-bars.js`, `main.js`, `tests/js/error-bars.test.js`).
- **Node lane green at HEAD** — `node --test tests/js/error-bars.test.js`:
  **18/18 pass**, including the fixture-drift tripwire (ddof=0 recomputation over the
  committed provenance cells), plugin purity, honest absence, the three strict
  schemas' additive optional fields, and both new regression groups.
- **Mean bit-equality / n>=2 gate / plugin purity / fixture provenance** — unchanged
  code since iteration 1 (no Python or generator edits in the fix commits); the
  relevant assertions all re-passed in the lanes above.
- **No security or debug-artifact regressions** — pattern sweep over all 8 files:
  no secrets, no `eval`, no `debugger`, no FIXME/XXX/HACK; no new catch blocks.

Test-lane provenance note: `tests/test_export_runs.py`, `test_ci_replay.py`, and
`test_vendored_stats.py` were not re-executed this iteration — the machine is under
heavy I/O from concurrent sweep work and those lanes stalled; they cover
`script/export_runs.py`, which neither fix commit touched, and passed at iteration 1.
The lanes that cover the actually-changed code (Node lane + determinism/aggregation)
were re-executed green at HEAD.

## Info (carried from iteration 1 — known open, no live impact)

### IN-01: METRIC_MAP diverges from the exporter's legacy metric table (MSE/MAE uppercase)

**File:** `dnallm-mark/js/task.js:103-111` vs `script/export_runs.py:416-422`
**Issue:** The exporter's `LEGACY_DATASET_METRIC` accepts uppercase
`F1/MCC/MSE/MAE/R2`; the JS `METRIC_MAP` covers `F1/MCC/R2`
(+ AUPRC/AUROC/pearsonr/spearmanr) but not `MSE`/`MAE`. A future dataset declaring
`metric: "MSE"` would get the exporter trio (`primary_slot` resolves to `mse`) while
the task page's gating compares `'mse' !== 'MSE'` and the display trio silently never
renders. No live impact today (the registry declares only metrics both maps resolve
identically).
**Fix:** Add `MSE: 'mse'` and `MAE: 'mae'` to `METRIC_MAP`, or generate the JS map
from the exporter table to keep one authority.

### IN-02: Trio recording is independent of the raw-score presence gate

**File:** `script/summarize_comparison.py:579-592`
**Issue:** `load_model_inputs` records `std`/`n_seeds` from a datasetEntry regardless
of whether that entry's primary-metric **score** passed the presence gate
(`raw_score is None`), so a hand-edited entry carrying a trio but an absent metric
value contributes its std to the per-model display mean while contributing nothing to
ranking/`samples` for that task. The exporter cannot produce this shape (the trio
requires >= 2 finite primary values); display-only.
**Fix:** For symmetry with the presence gate, record the trio only when
`raw_score is not None`, or document the tolerance for hand-edited inputs.

### IN-03: Floating bars can extend below the metric's natural domain (mean < std)

**File:** `dnallm-mark/js/task.js:394` + `dnallm-mark/js/error-bars.js:62-67`
**Issue:** `barDatum` returns `[mean - std, mean + std]`; for a small mean with a
larger std the bar — not just a whisker — starts below zero and the x axis
auto-scales there, visually implying an impossible negative metric. Does not trigger
on the current r2 data; inherent to the plan's native-floating-bars choice and
honest in the ±std sense (documented plan choice).
**Fix:** Leave as-is (documented behavior), or clamp the bar's `lo` at the metric's
natural bound while keeping the cap honest — only worth doing if real multi-seed
data ever exhibits mean < std.

---

_Reviewed: 2026-10-21T12:39:12Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
