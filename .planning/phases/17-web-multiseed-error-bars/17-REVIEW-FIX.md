---
phase: 17-web-multiseed-error-bars
fixed_at: 2026-10-21T12:02:24Z
review_path: .planning/phases/17-web-multiseed-error-bars/17-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 2
skipped: 3
status: all_fixed
---

# Phase 17: Code Review Fix Report

**Fixed at:** 2026-10-21T12:02:24Z
**Source review:** .planning/phases/17-web-multiseed-error-bars/17-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope of this report: 5 (2 Warnings + 3 Info)
- Fixed: 2 (WR-01, WR-02 — both in-scope Warnings)
- Skipped: 3 (IN-01, IN-02, IN-03 — Info tier, out of scope per `fix_scope: critical_warning`; recorded as skipped-info, no code touched)
- In-scope outcome: **all_fixed** (2/2 Warnings fixed)

**Binding constraints honored:** only `dnallm-mark/js/error-bars.js`, `dnallm-mark/js/main.js`, and `tests/js/error-bars.test.js` were touched; ranking math, data files, schemas, and METHODOLOGY.md untouched; ES modules with no build step; each fix its own atomic commit; no push performed (local commits only, per milestone rule).

## Fixed Issues

### WR-01: Error-bar plugin's vertical-bar branch draws wrong geometry (latent)

**Files modified:** `dnallm-mark/js/error-bars.js`, `tests/js/error-bars.test.js`
**Commit:** 3a8bc19
**Applied fix:** Implemented the reviewer's orientation dispatch in the bar-cap branch of `afterDatasetsDraw`. The constant-axis anchor is now `horizontal ? el.y : el.x` (a vertical bar's `el.y` lies on the value axis — anchoring there was the bug), and the branch splits on `horizontal`: horizontal bars keep horizontal stems/caps clamped into `[chartArea.left, chartArea.right]`; vertical bars stroke vertically (`moveTo(anchor, lo)` order) with caps spanning the category axis, clamped into `[chartArea.top, chartArea.bottom]` (the previously hardcoded wrong-axis clamp pair). The `whiskerGeometry` anchor-param doc, `clampPixel` boundary doc, and the plugin draw-dispatch doc comment were updated to describe both orientations. Added a `3b. DRAW DISPATCH` test group in `tests/js/error-bars.test.js` executing `afterDatasetsDraw` against mock bar charts with a recording ctx fake: vertical bars anchor on `el.x` and stroke vertically; vertical clamp endpoints land on `[chartArea.top, chartArea.bottom]` (chartArea bounds chosen so the wrong pair — left 390 vs bottom 300 — is distinguishable); horizontal bars keep the `el.y` anchor and horizontal strokes (regression guard for the shipped task-page path). Red/green verified: stashing the plugin fix makes exactly the two vertical tests fail (2 pass / 2 fail) while the horizontal guard stays green; restoring the fix returns the lane to 17/17.

### WR-02: Scatter whiskers mix units — tooltip label invites misreading

**Files modified:** `dnallm-mark/js/main.js`, `tests/js/error-bars.test.js`
**Commit:** 6930fed
**Applied fix:** Relabeled the scatter tooltip whisker line from `Seed spread: ±X (n=N)` to `Raw-score seed spread: ±X (n=N)` (the reviewer's fix-snippet wording, matching the site's existing `Label: value` tooltip line style), so the whisker is explicitly qualified as raw-metric seed spread around the displayed weighted/rank score rather than an error bound on that score. The conditional `(n=N)` suffix, the six pre-existing tooltip lines, the payload, and all chart math are byte-unchanged; `docs/METHODOLOGY.md` remains the deep reference (untouched). Extended the pins in `tests/js/error-bars.test.js` with a `7. PUBLIC-VIEW TOOLTIP QUALIFICATION` group: a source-pin test asserts `main.js` carries the qualified label with the `p.std.toFixed(4)` payload and the `(n=' + p.n_seeds + ')` suffix shape, and that the unqualified `Seed spread: ±` label does not survive anywhere in `main.js`.

## Verification

**Where the lanes ran (#2825 disclosure):** per-fix syntax checks (`node --check`), the module test lane, eslint, and the plan-family greps ran in the isolated worktree (`gsd-reviewfix/17-493285`, since removed) BEFORE each commit; the final full-lane replay below ran in the MAIN checkout after the fast-forward merged both commits into `autorun` — the numbers are reproducible from the tree any reader sees now.

- `node --test tests/js/*.test.js` — 44/44 pass (17 in `error-bars.test.js` before WR-02; 44 across all suites after both fixes; includes the 4 new tests: 3 draw-dispatch + 1 tooltip qualification pin)
- `npx --yes eslint@10.12.0 --config eslint.config.mjs` over the two changed JS files — clean (exit 0)
- Plan-family greps (17-02 Tasks 2/3, 17-03 closeout): `plugins: [errorBarsPlugin]` counts in `main.js`/`task.js`, `context.dataIndex`, `barDatum(`, `chart.js@4.4.0` = 1 in both HTML files, `ci.yml` hash `33d2252...` unchanged, `dnallm-mark/data/` porcelain clean, generator independence grep, `ddof` count in METHODOLOGY — all pass
- `make lint` (ruff) — All checks passed
- `make typecheck` (ty) — All checks passed
- Worktree cleanup tail transactional: `autorun` fast-forwarded 7a08672 → 6930fed, worktree removed, temp branch deleted, recovery sentinel removed; no orphan artifacts

## Skipped Issues

### IN-01: METRIC_MAP diverges from the exporter's legacy metric table (MSE/MAE uppercase)

**File:** `dnallm-mark/js/task.js:103-111` vs `script/export_runs.py:416-422`
**Reason:** skipped-info: out of scope for this iteration (fix_scope `critical_warning`; orchestrator directive records Info items as skipped-info). Would additionally require touching `task.js`, outside this iteration's binding file list.
**Original issue:** The exporter's `LEGACY_DATASET_METRIC` accepts uppercase `F1/MCC/MSE/MAE/R2`; the JS `METRIC_MAP` covers `F1/MCC/R2` (+ others) but not `MSE`/`MAE`. A future dataset declaring `metric: "MSE"` would emit the trio but silently never render it (gating compares `'mse' !== 'MSE'`). No live impact today.

### IN-02: Trio recording is independent of the raw-score presence gate

**File:** `script/summarize_comparison.py:579-592`
**Reason:** skipped-info: out of scope for this iteration (fix_scope `critical_warning`; orchestrator directive records Info items as skipped-info). Would additionally require touching `script/summarize_comparison.py`, outside this iteration's binding file list.
**Original issue:** `load_model_inputs` records `std`/`n_seeds` regardless of whether the entry's primary-metric score passed the presence gate, so a hand-edited entry with a trio but absent metric value contributes std to the display mean while contributing nothing to ranking. Exporter cannot produce this shape; display-only.

### IN-03: Floating bars can extend below the metric's natural domain (mean < std)

**File:** `dnallm-mark/js/task.js:394` + `dnallm-mark/js/error-bars.js:61-66`
**Reason:** skipped-info: out of scope for this iteration (fix_scope `critical_warning`; orchestrator directive records Info items as skipped-info); reviewer's own first-listed remediation is "leave as-is (documented behavior)".
**Original issue:** `barDatum` returns `[mean - std, mean + std]`; a small mean with larger std draws a bar starting below the metric's natural bound. Does not trigger on current data (std ≤ 0.089 vs means ≥ 0.58); inherent to the native floating-bar choice.

---

_Fixed: 2026-10-21T12:02:24Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
