---
phase: 17-web-multiseed-error-bars
verified: 2026-10-21T13:05:00Z
status: passed
score: 16/16 must-haves verified
covered_files: [".planning/phases/17-web-multiseed-error-bars/17-01-PLAN.md", ".planning/phases/17-web-multiseed-error-bars/17-01-SUMMARY.md", ".planning/phases/17-web-multiseed-error-bars/17-02-PLAN.md", ".planning/phases/17-web-multiseed-error-bars/17-02-SUMMARY.md", ".planning/phases/17-web-multiseed-error-bars/17-03-PLAN.md", ".planning/phases/17-web-multiseed-error-bars/17-03-SUMMARY.md", "dnallm-mark/js/error-bars.js", "dnallm-mark/js/main.js", "dnallm-mark/js/task.js", "docs/METHODOLOGY.md", "schemas/model_performance.json", "schemas/models_comparison.json", "schemas/task_performance.json", "script/export_runs.py", "script/permutation_tests.py", "script/summarize_comparison.py", "scripts/generate-errorbar-fixtures.js", "tests/fixtures/errorbar/geometry-fixtures.json", "tests/js/error-bars.test.js", "tests/test_aggregation.py", "tests/test_ci_replay.py", "tests/test_export_runs.py"]
covered_digest: "v3:sha256:527d3c139f851632a52d7f42ad2488ee4a4fc679149a1742ee42366d00141a22"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Visual browser spot-check of the error-bar rendering (OPTIONAL per plan, but it is the only uncovered seam): stage a multi-seed (std-carrying) copy of the data (e.g. r2-derived export), run bash start-server.sh, open the leaderboard scatter and a task bar-chart page"
    expected: "Scatter points on the y axis carry vertical whiskers with caps clamped into the chart area; the primary-metric task bar chart shows floating bars with caps and no stems; tooltips show 'Raw-score seed spread: ±x.xxxx (n=N)' on std-carrying models and the unchanged lines otherwise; std-less data renders exactly as before (no zero-width whiskers)"
    why_human: "No automated browser lane exists by design (17-03 Task 3 records the visual spot-check as an optional maintainer note). Node lane proves the draw commands against mock charts and the geometry on real values, but not pixels on a real canvas."
  - test: "Human review of the 9 ADR-550 judgment-tier prohibition flags (unverified-prohibition — human review recommended; auto-judge verdict: all 9 HELD with evidence, non-authoritative)"
    expected: "Confirm or reject the auto-judge dispositions: vendored banner untouched + ddof=0 helper outside it; no required-array additions / additionalProperties relaxation / ranking-math change; committed data tree never regenerated; no new CDN tag / no Chart.register / lowercase plugin id; no zero-width whisker or [v,v] bar; arrays never reach extractModels/sort/table; fixtures generated not hand-written with independent generator; zero CI workflow changes; generator refuses loudly rather than fabricating"
    why_human: "Judgment-tier prohibitions cannot be deterministically proven by an LLM verifier; the evidence recorded below is non-authoritative per ADR-550 D4 (consistent with Phases 13-16 flagging)"
---

## Visual Verification — Delegated to Orchestrator (Maintainer Ruling 2026-10-22)

The browser spot-check was executed programmatically at pixel level (stronger than eyeballing):

- **Harness**: real Chromium headless (playwright-core) over a staged gitignored preview
  (/root/autodl-tmp/phase17-preview) — the Phase-15 r2 sweep re-run through the real
  export→summarize chain with the Phase-17 aggregation code (repo untouched, porcelain clean).
- **Bars (task.html, 5mC)**: live chart state read back — dataset = 2 FLOATING-BAR arrays exactly
  mean±std (0.5952±0.0891 → [0.5062,0.6843]; 0.5861±0.0607 → [0.5654,0.6068]); PNG pixel assertions
  at canvas-rect-offset computed coordinates: bar ink across both spans AND both whisker caps at the
  exact predicted pixels (bar0 x1032..1321 rows 548..744; bar1 x1128..1195 rows 854..1050).
- **Scatter (index.html)**: plugin 'errorbars' registered on the live chart; std point carries
  std=0.0488/nSeeds=3; marker ink verified at the point pixel; whisker geometry computed by the live
  scale — sub-pixel on this view (std 0.049 vs a 0-50 y-axis), the honest rendering of a tiny spread.
- **Serving layer**: all resources HTTP 200.

Evidence: /root/autodl-tmp/phase17-preview/ (geometry.json, bars-geo.json, PNG screenshots).
The 9 ADR-550 prohibition flags remain recorded as non-authoritative (consistent with Phases 13-16).


# Phase 17: Web Multi-seed Error Bars Verification Report

**Phase Goal:** Multi-seed results display with error bars on the public pages — additive mean/std/n_seeds through the data chain, scatter whiskers via a vendored inline Chart.js plugin, floating-bar task charts — with zero drift in existing numbers
**Verified:** 2026-10-21T13:05:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Merged from ROADMAP success criteria (3) + PLAN must_haves across 17-01/17-02/17-03. All behavior-dependent truths carry behavioral test evidence (named tests run this pass), so none are PRESENT_BEHAVIOR_UNVERIFIED.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | (SC-1a) Multi-seed cells (>= 2 completed seeds on the declared primary metric) gain entry-level optional mean/std/n_seeds in BOTH export views from ONE emission site | ✓ VERIFIED | `script/export_runs.py:845-912` — `primary_slot = resolve_dataset_metric(...)` once per task; trio captured in the metric_block loop when `key == primary_slot and len(ordered) >= 2`; attached via `task_entry.update(trio)` / `model_entry.update(trio)` (one emission, both D-16 views). Behavioral: `test_multi_seed_cell_emits_population_std_trio` passed |
| 2 | (SC-1b) std is POPULATION std (ddof=0) via a NEW helper OUTSIDE the vendored banner — never sd (ddof=1), never sd/sqrt(n) | ✓ VERIFIED | `population_std` at `script/export_runs.py:237-256`, directly after the `# ===== END vendored section @483a35c =====` marker (:234); body is `float(np.asarray(values, dtype=float).std(ddof=0))` — no derivation from sd. `tests/test_vendored_stats.py` unmodified since before the phase (git log empty) and passed this pass |
| 3 | (SC-1c) EDGE (absent, export layer): a 1-seed cell emits NOTHING in either view | ✓ VERIFIED | `test_one_seed_cell_emits_degenerate_statistics` passed (fixture plants eval_AUPRC on the lone seed so the n>=2 gate itself is what's pinned); `barDatum` honest-absence node tests passed |
| 4 | (SC-1d) EDGE (absent, summarize layer): trio-less inputs produce byte-identical output — test_determinism.py passes UNMODIFIED | ✓ VERIFIED | `tests/test_determinism.py` + `tests/test_vendored_stats.py` run this pass: 10 passed; git log since phase start shows zero edits to either file; `dnallm-mark/data/` porcelain clean |
| 5 | (SC-1e) EDGE (additive, chain layer): trio-stripped inputs aggregate byte-equal on every pre-existing key | ✓ VERIFIED | `test_trio_is_additive_over_trio_stripped_inputs` (`tests/test_ci_replay.py:354`) passed this pass |
| 6 | (SC-1f) Per-model std/n_seeds propagate inside aggregate_models so ALL FOUR arena files inherit uniformly (mean of per-task stds, min n_seeds) | ✓ VERIFIED | `script/summarize_comparison.py:437-450` — conditional emission after performance construction, inside `aggregate_models`; `main()` threads `dataset_seed_stats` into both calls (:641-643, :663-665). Behavioral: 3 `test_seed_stats_*` unit pins passed |
| 7 | (SC-1g) Schemas gain the fields in properties ONLY — required arrays unchanged, additionalProperties:false everywhere | ✓ VERIFIED | Schema inspection: task_performance modelEntry required = [model, parameters, performance]; model_performance datasetEntry required = [dataset, parameters, performance]; models_comparison performance required = the 16 keys; std/n_seeds/mean present in properties; additionalProperties:false at every checked level; `tests/test_schemas.py` 105 passed |
| 8 | (SC-1h) METHODOLOGY.md appendix fixes sd (ddof=1) vs std (ddof=0) once + display-only declaration | ✓ VERIFIED | `docs/METHODOLOGY.md:158-184` "Appendix: Display error bars (multi-seed std)"; names both conventions with ddof; declares display-only (no ranking/aggregation/version change); grep ddof count = 2 |
| 9 | (SC-1i) The committed dnallm-mark/data/ tree NEVER regenerates in this phase | ✓ VERIFIED | `git status --porcelain dnallm-mark/data/` empty; grep for `"n_seeds"` across all committed comparison/task/model data files: zero hits (node-lane committed-data absence assertions also green) |
| 10 | (SC-2a) Vendored inline Chart.js plugin (id 'errorbars', afterDatasetsDraw, getPixelForValue) wired via top-level plugins array — never Chart.register, never a new CDN script | ✓ VERIFIED | `dnallm-mark/js/error-bars.js:99-199` — id 'errorbars' lowercase, `afterDatasetsDraw`, `defaults`; registered via `plugins: [errorBarsPlugin]` in `main.js:333` and `task.js:406`; `Chart.register` grep over js/ = 0 hits; chart.js@4.4.0 occurrences = exactly 1 in each HTML; HTML files untouched since Phase 4 |
| 11 | (SC-2b) Scatter gains whiskers + ±std tooltip line; existing six tooltip lines untouched; y-scale only; axis-overflow clamped | ✓ VERIFIED | `main.js:279-280` (std/nSeeds optional-chained payloads), `:365-377` (conditional appended line, WR-02-qualified "Raw-score seed spread"); plugin point mode reads `chart.scales.y` only with chartArea clamping (`error-bars.js:160-185`); draw-dispatch mock-chart tests assert exact stroke commands |
| 12 | (SC-2c) Task bar chart uses native floating bars on the PRIMARY metric with plugin caps + closure tooltip | ✓ VERIFIED | `task.js:103-111` (module-scope METRIC_MAP), `:320-323` (std attached only when `actualMetricKey === primaryKey`), `:394` (`barDatum` — single birthplace of the array form), `:406/:417` (plugins + drawStem:false), `:437-444` (`displayModels[context.dataIndex]` closure tooltip, array only when std is a number); WR-01 orientation-dispatch regression test passed |
| 13 | (SC-2d) Geometry verified against real sweep-derived artifacts (fixtures generated, not hand-written) | ✓ VERIFIED | Fixture per-seed values byte-match the real r2 `final_metrics.json` (spot-checked plant-dnabert-6mer/5mC seeds 42/43/44: 0.7142857/0.5/0.5714286); regeneration over the live r2 tree is byte-idempotent (git hash identical before/after); generator independence grep clean (never imports error-bars.js); provenance = 4 cells x 3 seeds |
| 14 | (SC-2e) EDGE (honest absence): std-less / std 0 / non-finite renders exactly as today; non-primary metric shows no ±std | ✓ VERIFIED | `barDatum` returns scalar for 0/undefined/null/NaN/negative (node tests passed); plugin draws only on finite std > 0 (:163) and skips `raw[0] === raw[1]` pairs (:120); primary-metric gating at `task.js:320` |
| 15 | (SC-2f) metricValue stays SCALAR end-to-end; arrays exist only inside the chart data mapping; no client-side std recomputation | ✓ VERIFIED | `task.js:308` (`parseFloat` scalar in extractModels), sort comparator :334-340 over `metricValue`; array form born only at :394 via `barDatum`; std is precomputed offline (read-only display) |
| 16 | (SC-3) Node-lane tests cover plugin value→pixel math as a pure function and additive schema fields via generated fixtures | ✓ VERIFIED | `tests/js/error-bars.test.js` (387 lines, 18 cases incl. the review-fix draw-dispatch and tooltip-qualification additions): geometry vs fixtures at 1e-9 through injected fake scales, in-test ddof=0 recomputation tripwire, plugin shape/exact exports, honest absence, additive schema fields with required arrays byte-pinned, committed-data absence. Full node lane `node --test tests/js/*.test.js`: 44/44 pass this pass |

**Score:** 16/16 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `script/export_runs.py` | population_std helper outside vendored banner + gated trio emission in both views | ✓ VERIFIED | Helper :237-256 after END marker :234; emission :869-912; substantive (test-backed) |
| `script/summarize_comparison.py` | 5-tuple load_model_inputs + aggregate_models dataset_seed_stats kwarg | ✓ VERIFIED | :465+ (5-tuple, presence-gated), :320-321/:437-450 (kwarg + conditional emission), main threads both calls |
| `docs/METHODOLOGY.md` | sd-vs-std appendix + display-only declaration | ✓ VERIFIED | :158-184 |
| `dnallm-mark/js/error-bars.js` | whiskerGeometry + barDatum + errorBarsPlugin (min 80 lines) | ✓ VERIFIED | 204 lines; all three exports; pure geometry (injected scale, no Chart/canvas/DOM) |
| `scripts/generate-errorbar-fixtures.js` | zero-dep r2-reading deterministic generator (min 120 lines) | ✓ VERIFIED | 311 lines; CommonJS; loud-refusal path (:129-131, :149+); independence verified |
| `tests/fixtures/errorbar/geometry-fixtures.json` | committed generated fixture with provenance | ✓ VERIFIED | 4 cells x 3 seeds, 2 scale sets, 8 scenarios, honest-absence rows; regeneration byte-idempotent |
| `tests/js/error-bars.test.js` | node:test lane (min 150 lines) | ✓ VERIFIED | 387 lines, 18 cases, all passing |

All artifacts: exists ✓, substantive ✓, wired ✓ (imports/usage verified: `error-bars.js` imported by `main.js:8` and `task.js:6`; plugin file has zero orphan consumers), data flows ✓ (fixture provenance traced to real r2 files).

### Key Link Verification

Tool `verify.key-links` could not resolve prose `from:` fields (not file paths) — verified manually by direct code inspection.

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| export_runs emission loop | schemas (trio in properties) → summarize load_model_inputs → aggregate_models → 4 arena files + models_comparison schema | presence-gated additive emission | ✓ WIRED | Full chain read in source; every hop present and conditional; absent upstream ⇒ key never written downstream |
| `dnallm-mark/js/error-bars.js` | `main.js` renderScatterChart + `task.js` renderBarChart | one import per page module, optional-chained reads | ✓ WIRED | `main.js:8`, `task.js:6` imports; point payloads / plugins array / barDatum / closure tooltip all present |
| r2 sweep tree (gitignored) → generator → committed fixture → test lane → module under test | | generator independence; read-only fixture consumption | ✓ WIRED | Generator never imports the module; tests read fixture read-only; CI needs only committed artifacts |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| geometry-fixtures.json | provenance.cells[].per_seed | real `pipeline/finetuned-sweep-r2/**/final_metrics.json` | Yes — values byte-match the live r2 files | ✓ FLOWING |
| main.js scatter | performance.std / n_seeds | `models_comparison*.json` (optional, absent on committed single-run data) | Yes — honest absence pinned by design | ✓ FLOWING |
| task.js bar chart | modelData.std / n_seeds | `{task}_task_performance.json` modelEntry (optional) | Yes — honest absence pinned by design | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Trio emission both views, ddof=0, mean bit-equal | `pytest tests/test_export_runs.py::test_multi_seed_cell_emits_population_std_trio + test_one_seed_cell_emits_degenerate_statistics` | 2 passed | ✓ PASS |
| Additive-case zero-drift (trio-stripped equivalence) | `pytest tests/test_ci_replay.py::test_trio_is_additive_over_trio_stripped_inputs` | 1 passed | ✓ PASS |
| Absent-case zero-drift + vendored banner pin (UNMODIFIED gates) | `pytest tests/test_determinism.py tests/test_vendored_stats.py` | 10 passed | ✓ PASS |
| Per-model propagation (mean-of-stds, min-n) | `pytest tests/test_aggregation.py::test_seed_stats_*` (3 named) | 3 passed | ✓ PASS |
| WEB-03 node lane (geometry/schema/honest-absence/draw dispatch) | `node --test tests/js/error-bars.test.js` | 18 pass, 0 fail | ✓ PASS |
| Full node lane (regression tripwire) | `node --test tests/js/*.test.js` | 44 pass, 0 fail | ✓ PASS |
| Committed-data schema validation after schema edits | `pytest tests/test_schemas.py` | 105 passed | ✓ PASS |
| Fixture regeneration idempotence | `node scripts/generate-errorbar-fixtures.js` + hash compare | byte-identical (215359bc… before and after) | ✓ PASS |
| Generator independence | `grep -cE "(require\|import)[^;]*error-bars" scripts/generate-errorbar-fixtures.js` | 0 matches | ✓ PASS |
| ESLint exact-pin lane (same as CI) | `npx --yes eslint@10.12.0 --config eslint.config.mjs "dnallm-mark/js/*.js"` | exit 0 | ✓ PASS |
| CI byte pin / data tree / CDN pins | `git hash-object .github/workflows/ci.yml`; porcelain; grep counts | 33d2252eb594e0faecece9e8015a332d8d6479ef; empty; 1 and 1 | ✓ PASS |

Full pytest suite was NOT re-run this pass (SUMMARY records 2236 passed / 6 documented environmental root-chmod failures, and the suite needs the machine's academic proxy for one evaluate-touching lane); every phase-relevant named gate was run individually instead, all green.

### Probe Execution

Not applicable — no `scripts/*/tests/probe-*.sh` declared or conventional for this phase; the phase's gates are pytest/node/lint lanes, spot-checked above.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| WEB-01 | 17-01 | Additive-optional mean/std/n_seeds through aggregation; zero-drift; METHODOLOGY display-only semantics | ✓ SATISFIED | Truths 1-9 |
| WEB-02 | 17-02, 17-03 | Scatter whiskers via vendored inline plugin; floating-bar task chart; ±std tooltips | ✓ SATISFIED | Truths 10-15 |
| WEB-03 | 17-03 | Node-lane tests: pure value→pixel math + additive schema fields via generated fixtures | ✓ SATISFIED | Truth 13, 16 |

Orphaned requirements: none — REQUIREMENTS.md maps exactly WEB-01/02/03 to Phase 17 and all three are claimed by plans.

### Anti-Patterns Found

Debt-marker scan (TBD/FIXME/XXX + TODO/HACK/PLACEHOLDER) over all 16 phase-modified files: zero hits. Stub-pattern scan over the new JS/Python: no empty implementations, no placeholder returns, no console-log-only bodies. The three skipped review Info items (IN-01 METRIC_MAP MSE/MAE divergence, IN-02 trio-vs-raw-score gate independence, IN-03 floating bars below metric domain) are recorded dispositions in `17-REVIEW-DISPOSITION.md`, not debt markers — no live impact documented.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | none found | — | — |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| tests/test_export_runs.py | WEB-01 | 2 named (+suite) | 0 | No — expected std computed from hand-derived math (0.0163299…) and ddof=0 formula, not from the module | Value (approx equality, bit-equality, key-set) | OK |
| tests/test_ci_replay.py | WEB-01 | 1 named (+chain pins) | 0 | No — byte-equality vs staged fixture trees | Behavioral (chain equivalence) | OK |
| tests/test_aggregation.py | WEB-01 | 3 | 0 | No — pure-function calls with literal maps | Value | OK |
| tests/js/error-bars.test.js | WEB-02, WEB-03 | 18 | 0 | No — generator never imports module under test (grep-verified); in-test ddof=0 recomputation over provenance values; fixture expectations computed by generator's own inline arithmetic | Behavioral (exact stroke-command sequences, geometry 1e-9, schema key-set equality) | OK |

Disabled tests on requirements: 0. Circular patterns: 0 (triple tripwire verified). Insufficient assertions: 0.

### Decision Coverage

All trackable CONTEXT.md decisions honored by shipped artifacts (gsd-tools check.decision-coverage-verify: 12/12 honored, 0 not honored).

### Human Verification Required

### 1. Visual browser spot-check of error-bar rendering

**Test:** Stage a std-carrying (multi-seed) copy of the data (e.g. r2-derived export), run `bash start-server.sh`, open the leaderboard scatter and a primary-metric task bar-chart page.
**Expected:** Vertical whiskers with caps on scatter points (clamped into the chart area when mean±std exceeds axis limits); floating bars with caps and no stems on the task chart; tooltip line "Raw-score seed spread: ±x.xxxx (n=N)" on std-carrying models only; std-less data renders exactly as before.
**Why human:** No automated browser lane exists by design (17-03 Task 3 records this as an optional maintainer note). The node lane proves draw commands against mock charts and geometry on real values — not pixels on a real canvas. On the committed single-run data the whiskers are dormant by construction, so the multi-seed visual needs staged data.

### 2. ADR-550 judgment-tier prohibition flags (9) — human review recommended

**Test:** Review the auto-judge dispositions below; confirm or reject.
**Expected:** All 9 prohibitions hold. Non-authoritative auto-judge verdicts with evidence:
1. Vendored banner never edited; std never from sd/sqrt(n) — **HELD** (helper outside banner; test_vendored_stats unmodified + passing)
2. No required-array additions, no additionalProperties relaxation, ranking math untouched — **HELD** (schema inspection; diff vs phase base shows additions only)
3. Committed data tree never regenerated — **HELD** (porcelain clean; no trio keys in committed data)
4. No new CDN tag, no Chart.register, lowercase plugin id — **HELD** (verified by grep)
5. No zero-width whisker / [v,v] floating bar — **HELD** (code guards + passing tests)
6. Arrays never reach extractModels/sort/table — **HELD** (code verified)
7. Fixtures generated not hand-written; generator independent — **HELD** (idempotent regeneration from real r2 tree; independence grep)
8. Zero CI workflow changes — **HELD** (ci.yml hash = 33d2252e…)
9. Generator refuses loudly, never fabricates — **HELD** (refusal code path present; documented exit-1 probe)

**Why human:** Judgment-tier prohibitions cannot be deterministically proven by an LLM verifier; per ADR-550 D4 (autonomous mode) these verdicts are non-authoritative and flagged, never silently absorbed into a pass — consistent with Phases 13-16.

### Gaps Summary

No gaps. All 16 merged truths verified with behavioral evidence; all artifacts exist, are substantive, wired, and data-flowing; all three requirements satisfied with no orphans; zero debt markers; all documented commits valid (11/11); review Warnings WR-01/WR-02 confirmed fixed in code with regression tests passing. The `human_needed` status comes solely from the two items above: the by-design-absent browser visual check and the ADR-550 prohibition-flag review — not from any failed check.

---

_Verified: 2026-10-21T13:05:00Z_
_Verifier: Claude (gsd-verifier)_
