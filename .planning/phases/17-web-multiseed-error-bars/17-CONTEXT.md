---
phase: 17-web-multiseed-error-bars
title: Web 多种子 Error Bar (Web Multi-Seed Error Bars)
status: approved
created: 2026-10-21
---

# Phase 17: Web 多种子 Error Bar - Context

**Gathered:** 2026-10-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Aggregation emits additive-optional mean/std/n_seeds per model×dataset (absent
fields → byte-identical JSON, zero-drift gate proves additivity); the
FLOPs-vs-rank scatter gains error-bar whiskers via a vendored inline Chart.js
plugin; the task bar chart uses native floating bars + whisker caps; tooltips
gain ±std. Node-lane tests cover the plugin's value→pixel math as a pure
function and the additive schema fields. METHODOLOGY.md documents the
display-only semantics. Ranking math is untouched (Core Value).

</domain>

<decisions>
## Implementation Decisions

### Aggregation Additive Fields (WEB-01)
- **D17-01:** Every model×dataset gains optional `mean`/`std`/`n_seeds` when multi-seed data exists; std = population std over seeds (ddof=0), semantics fixed ONCE in METHODOLOGY.md appendix
- **D17-02:** Zero-drift gate EXTENDED (not rebuilt): no-multi-seed inputs produce byte-identical JSON (absent keys never written); multi-seed inputs add ONLY the new keys
- **D17-03:** Write point = script/summarize_comparison.py aggregation + the vendored aggregate_seeds per-seed statistics (single ownership)
- **D17-04:** Readers tolerant (optional keys, existing data stays valid); schemas/ gains optional-field definitions; display-only — no ranking/methodology version bump

### Chart Error Bars (WEB-02)
- **D17-05:** Scatter whiskers via a vendored inline plugin (~40 lines, afterDatasetsDraw + getPixelForValue) — mean±std geometry; NO new CDN dependency (sgratzl plugin stays the documented ratified fallback only)
- **D17-06:** Task bar chart uses native Chart.js floating bars ([mean-std, mean+std]) + the same plugin's cap rendering
- **D17-07:** Tooltips gain a ±std line when the field exists (existing tooltip lines untouched)
- **D17-08:** Honest absence: points without std render normally with no whiskers — never a zero-width fake whisker

### Node Tests & Gates (WEB-03)
- **D17-09:** The plugin's value→pixel math extracted as a pure importable function; Node-lane tests assert whisker-end geometry against generator-produced fixtures (never hand-written)
- **D17-10:** Schema tests: additive optional fields asserted; absent-field inputs produce byte-identical aggregation output (the zero-drift extension)
- **D17-11:** Full CPU lanes green + node lane green; zero CI changes; Chart.js 4.4.0 UMD CDN pin untouched; ES-module no-build architecture unchanged
- **D17-12:** METHODOLOGY.md appendix fixes std semantics + display-only declaration once; ranking math untouched

### Claude's Discretion
- The plugin's module home (js/ vendored file name) provided it is imported by both charts and covered by the pure-function tests
- Whisker styling details (cap width, color token choice from the existing palette) provided existing tokens are used
- Fixture generator shape (Node script location)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `script/summarize_comparison.py`: aggregation + the existing zero-drift gate machinery; vendored `aggregate_seeds` per-seed statistics
- `dnallm-mark/js/main.js` scatter (renderScatterChart, destroy-before-render discipline); `js/task.js` bar chart
- `js/data.js` DataAPI tolerant reads (`model.performance?.…` defensive idiom)
- Node test lane (existing suite, 26 tests); `scripts/generate-tasks-index.js` as the Node generator precedent
- `css/variables.css` palette tokens; METHODOLOGY.md

### Established Patterns
- Additive-only JSON changes proven by byte-identity gates (zero-drift discipline)
- Chart destroy-before-render; defensive optional reads; CDN pin 4.4.0
- No build step — plain ES modules, Node-lane pure-function testing

### Integration Points
- summarize_comparison output → DataAPI → both charts read the new optional keys
- The vendored plugin file joins js/ (imported by main.js + task.js); the pure math function joins the Node test lane

</code_context>

<specifics>
- Research `.planning/research/ARCHITECTURE.md` §E is the design backbone
- Binding constraints: leaderboard numbers move only through zero-drift-proven additive changes; ranking math untouched; display-only semantics; no new CDN; Chart.js 4.4.0 pin
- v2 deferred: ±std table columns, CI-95/IQR selector (WEB-D01/D02 in REQUIREMENTS)

</specifics>

<deferred>
- TUI docs → Phase 18
- Full leaderboard regeneration with multi-seed data → maintainer decision post-milestone (real multi-seed artifacts exist from Phase 15's sweep)

</deferred>
