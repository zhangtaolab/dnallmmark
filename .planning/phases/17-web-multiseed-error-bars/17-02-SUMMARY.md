---
phase: 17-web-multiseed-error-bars
plan: 2
subsystem: web-ui
tags: [chartjs-4.4.0, inline-plugin, error-bars, floating-bars, honest-absence, no-build, display-only]

# Dependency graph
requires:
  - phase: 17-web-multiseed-error-bars (17-01, WEB-01)
    provides: entry-level mean/std/n_seeds trio in {task}_task_performance.json (task bar chart via TaskLoader) + per-model performance.std/n_seeds in models_comparison*.json (scatter via DataAPI) — the optional fields this plan renders
provides:
  - dnallm-mark/js/error-bars.js — the vendored inline plugin: PURE whiskerGeometry (scale-injected, the WEB-03 test seam), barDatum (the single birthplace of the floating-bar array form, honest-absence scalar otherwise), errorBarsPlugin {id 'errorbars', afterDatasetsDraw, defaults}
  - main.js scatter wiring: std/nSeeds point payloads, top-level plugins: [errorBarsPlugin], ±std tooltip line appended only when typeof std === 'number'
  - task.js bar wiring: module-scope METRIC_MAP, primary-metric std/nSeeds gating in extractModels, native floating bars via barDatum, drawStem:false caps, displayModels[context.dataIndex] closure tooltip
affects: [17-03 (WEB-03 tests import whiskerGeometry/barDatum from this module + full phase gates), maintainer post-milestone regeneration (whiskers appear only when the data carries std)]

# Actuals (#2632) — pairs with the plan's estimate (tokens 16000, tasks 3, confidence high).
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 4200
  tasks: 3
  commits: 3
  plan_head_before: 815584e2f928a522a660acb526f189600ad19716
  plan_head_after: c06a46a1f5cadd843db311f3f3ddaa101cae130f

# Tech tracking
tech-stack:
  added: []  # zero installs, zero CDN change — vendored inline source only (T-17-SC/T-17-06 held)
  patterns:
    - "Vendored inline Chart.js plugin registered per chart via the top-level config plugins array (never global registration, never a new CDN script) — the D17-05 seam"
    - "Pure geometry seam: whiskerGeometry(anchor, loValue, hiValue, scale, capWidth) takes an injected duck-typed scale so Node tests pass a linear fake mirroring the shipped UMD math (D17-09)"
    - "Honest absence at every layer: barDatum returns the scalar for absent/zero/non-finite std; the plugin draws only on finite std > 0 (point mode) or a genuine [lo,hi] pair (bar mode) — no zero-width fake whiskers anywhere (D17-08)"

key-files:
  created:
    - dnallm-mark/js/error-bars.js
  modified:
    - dnallm-mark/js/main.js
    - dnallm-mark/js/task.js

key-decisions:
  - "Point-mode whiskers read chart.scales.y ONLY (never the x scale — the log-FLOPs axis is structurally out of reach); every endpoint pixel is clamped into chartArea so mean±std beyond the pinned axis limits renders toward the boundary"
  - "The AUD-20 metricMap hoisted to module scope as METRIC_MAP (UPPER_SNAKE per the repo constants convention) — ONE definition serves both the dropdown default and extractModels's primary-metric std gating"
  - "std/nSeeds attach to the bar-chart model objects only when the selected metric IS the dataset's declared primary (A3): switching the dropdown away shows scalar bars and no ±std line; metricValue stays the parseFloat scalar end-to-end (Pitfall 4)"
  - "Both tooltips read the model closure (displayModels[context.dataIndex] / context.raw.model) — never context.raw's type on floating bars (would print \"0.5,0.69\") and never context.parsed.x (barEnd, unreliable with negatives)"

patterns-established:
  - "barDatum as the single birthplace of the array data form: every other consumer (sort comparator, leaderboard table, tooltip mean line) provably receives scalars"
  - "Plugin options scoped via options.plugins.errorbars (drawStem:false on the bar chart — caps only, the floating bar itself is the range) with defaults riding the plugin object"

requirements-completed: [WEB-02]

# Coverage metadata (#1602) — one entry per shipped deliverable.
coverage:
  - id: D1
    description: "Vendored inline plugin module: pure whiskerGeometry + honest-absence barDatum + errorBarsPlugin (id 'errorbars' lowercase, afterDatasetsDraw + defaults), y-scale-only point mode, hidden-dataset skip, chartArea clamping"
    requirement: WEB-02
    verification:
      - kind: unit
        ref: "plan Task 1 inline node assertion (whiskerGeometry linear-fake pixels 30/70/capHalf 4; plugin id lowercase; barDatum 5,2->[3,7] and 5,0/5,undefined->5) — exit 0"
        status: pass
      - kind: unit
        ref: "node --check dnallm-mark/js/error-bars.js + node --test tests/js/*.test.js (26/26) + eslint 10 flat config clean"
        status: pass
    human_judgment: false
  - id: D2
    description: "main.js scatter integration: std/nSeeds optional-chained point payloads, top-level plugins: [errorBarsPlugin] seam, ±std tooltip line appended after the six existing lines only when typeof std === 'number'"
    requirement: WEB-02
    verification:
      - kind: unit
        ref: "tests/js/main-view-toggle.test.js + tests/js/main-topn-filter.test.js + tests/js/data-api.test.js (13/13 — main.js required under the document stub)"
        status: pass
      - kind: integration
        ref: "grep pins: 'plugins: [errorBarsPlugin]' present; index.html chart.js@4.4.0 exactly 1 occurrence (CDN pin byte-untouched, git diff 0 lines on both HTML files)"
        status: pass
    human_judgment: false
  - id: D3
    description: "task.js bar integration: module-scope METRIC_MAP, primary-metric std gating, floating bars via barDatum, drawStem:false caps, closure tooltip returning array only when std is a number"
    requirement: WEB-02
    verification:
      - kind: unit
        ref: "node --check dnallm-mark/js/task.js + full node lane 26/26 + eslint clean"
        status: pass
      - kind: integration
        ref: "grep pins: plugins array / context.dataIndex / barDatum( present in task.js; task.html chart.js@4.4.0 exactly 1; zero code reads of context.raw/context.parsed in the tooltip (comment references only)"
        status: pass
    human_judgment: false

# Metrics
duration: 7min
completed: 2026-10-21
status: complete
---

# Phase 17 Plan 2: Browser Error Bars (WEB-02) Summary

**Vendored inline Chart.js 4.4.0 plugin (zero new dependencies) renders multi-seed error bars on both public charts — scatter whiskers + ±std tooltip on the leaderboard, native floating bars + caps + honest-absence tooltip on the task benchmark — with metricValue scalar end-to-end and both CDN pins byte-untouched**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-21T09:48:29Z
- **Completed:** 2026-10-21T09:55:39Z
- **Tasks:** 3/3
- **Files modified:** 3 (exactly the declared files_modified set; git diff vs plan base shows zero changes to any other file, HTML included)

## Accomplishments

- Task 1: `dnallm-mark/js/error-bars.js` (181 lines, house style) — `whiskerGeometry(anchor, loValue, hiValue, scale, capWidth)` PURE over an injected duck-typed scale (no Chart/canvas/DOM anywhere in the module); `barDatum(metricValue, std)` returning arrays ONLY for finite std > 0 (the D17-08 honest-absence seam and the single birthplace of the array form); `errorBarsPlugin` with lowercase id `'errorbars'` (the npm-name rule), `afterDatasetsDraw` dispatching per element on `Array.isArray(raw)` — bar-cap mode over the value axis (`indexAxis === 'y' ? chart.scales.x : chart.scales.y`, stem gated on `drawStem`) vs point mode over `chart.scales.y` ONLY with the finite-std>0 guard — hidden datasets skipped, endpoint pixels clamped into chartArea, isFinite guards so malformed data degrades to silence (T-17-04); defaults `{color: '#595F6E' (--color-text-secondary), lineWidth: 1, capWidth: 8, drawStem: true}`; plain ES exports (require(esm) exposes the namespace — no CommonJS fallback needed)
- Task 2: main.js scatter — dataset point objects gain `std: model.performance?.std` / `nSeeds: model.performance?.n_seeds` (undefined stays undefined, never coerced); config gains the top-level `plugins: [errorBarsPlugin]` array (the registration seam — inline plugins are per-chart, never globally registered); the tooltip label array appends `Seed spread: ±x.xxxx (n=N)` only when `typeof performance.std === 'number'` with the six existing lines' content untouched; destroy-before-render, axis min/max, and the index.html CDN pin untouched
- Task 3: task.js bar chart — `METRIC_MAP` hoisted to module scope (one definition for the dropdown default and the primary-metric gating); `extractModels` attaches `std`/`nSeeds` only when `actualMetricKey === primaryKey` AND std is a number (the trio belongs to the declared primary metric — A3), keeping `metricValue` the parseFloat scalar; the data mapping goes through `barDatum` (native mixed scalar/array floating bars, first-party in 4.4.0); config gains `plugins: [errorBarsPlugin]` + `options.plugins.errorbars = { drawStem: false }` (caps only — the bar is the range); the tooltip is rewritten to the `displayModels[context.dataIndex]` closure returning a plain string without std and a two-line array with it — never reading `context.raw`'s type or `context.parsed.x` (Pitfall 4)
- Close-out gates: node lane 26/26, `node --check` on all three files, eslint 10 flat config clean over the whole `dnallm-mark/js/` glob, `make lint` and `make typecheck` both "All checks passed", prohibition sweep green (zero `Chart.register` literals in js/, no new script tags — 2 per HTML file, unchanged from base), zero DOM access in the plugin module, and no Python test file references the JS modules (the JS-only diff cannot regress pytest lanes)

## Task Commits

Each task was committed atomically:

1. **Task 1: js/error-bars.js — pure whiskerGeometry + barDatum + the errorbars plugin** - `9f6c64a` (feat)
2. **Task 2: main.js scatter — std point payloads, plugins array, ±std tooltip line** - `e852147` (feat)
3. **Task 3: task.js bar — primary-metric std gating, floating bars, closure tooltip** - `c06a46a` (feat)

**Plan metadata:** (see final docs commit below)

## Files Created/Modified

- `dnallm-mark/js/error-bars.js` (NEW) - vendored plugin module: whiskerGeometry (pure), barDatum, errorBarsPlugin
- `dnallm-mark/js/main.js` - scatter point payloads + plugins array + conditional ±std tooltip line
- `dnallm-mark/js/task.js` - module-scope METRIC_MAP + primary-metric gating + floating bars + caps + closure tooltip

## Decisions Made

- Point-mode whiskers deliberately read `chart.scales.y` ONLY — the log-scale FLOPs x axis is structurally out of reach, and every endpoint pixel is clamped into chartArea so a mean±std beyond the pinned axis limits still renders toward the boundary (the axis-overflow edge)
- The hoisted map landed as `METRIC_MAP` (UPPER_SNAKE, the repo constants convention) rather than keeping the lowercase local name — the plan's "hoist the metricMap constant" referred to the existing map, and module-scope constants follow the CLAUDE.md naming pattern
- The bar tooltip's mean line kept the original defensive format (`typeof value === 'number' ? value.toFixed(4) : value`) sourced from the closure model — byte-identical formatting semantics to the pre-change callback, so scalar data renders exactly as before
- The Task 1 header comment says "never globally registered" instead of naming the forbidden API — the acceptance criterion pins the literal string out of the file, so even the documentation avoids it

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All verify lanes passed on first run after each task's edits.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 17-03 (WEB-03) imports `whiskerGeometry`/`barDatum` from `dnallm-mark/js/error-bars.js` under require(esm) — the pure seam is in place and the plugin contract (finite std > 0, clamped pixels, drawStem option) is what the fixture tests will exercise
- Whiskers/caps stay visually dormant on the committed single-run data (no std keys anywhere) — honest absence by construction; they appear when the maintainer regenerates from multi-seed artifacts post-milestone
- Full phase gates (CPU lanes + node lane together) run in 17-03 per the phase split
- No blockers

## Self-Check: PASSED

All 3 files (SUMMARY + error-bars.js/main.js/task.js) exist on disk; all 3 task commits (9f6c64a, e852147, c06a46a) are ancestors of HEAD.
---
*Phase: 17-web-multiseed-error-bars*
*Completed: 2026-10-21*
