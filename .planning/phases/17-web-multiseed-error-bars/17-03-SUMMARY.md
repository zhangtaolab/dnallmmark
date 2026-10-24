---
phase: 17-web-multiseed-error-bars
plan: 3
subsystem: testing
tags: [node-test, generated-fixtures, r2-sweep, whisker-geometry, ddof0, additive-schema, zero-ci-change, phase-close]

# Dependency graph
requires:
  - phase: 17-web-multiseed-error-bars (17-01, WEB-01)
    provides: the additive optional trio in both export views + per-model std/n_seeds propagation + the three strict-schema property additions this lane pins
  - phase: 17-web-multiseed-error-bars (17-02, WEB-02)
    provides: dnallm-mark/js/error-bars.js — the pure whiskerGeometry/barDatum seam and the errorbars plugin this lane proves against real r2-derived values
provides:
  - scripts/generate-errorbar-fixtures.js — the zero-dep CommonJS fixture generator over the REAL pipeline/finetuned-sweep-r2 tree (loud-refusing, deterministic, independent of the module under test)
  - tests/fixtures/errorbar/geometry-fixtures.json — the committed generated fixture: 4 provenance cells (2 models x 2 tasks x 3 seeds, per-seed eval_f1 values + ddof=0 stds), 2 scale parameter sets, 8 point/bar geometry scenarios with inline-computed expected pixels, 3 honest-absence cases
  - tests/js/error-bars.test.js — the 14-case node lane: geometry-vs-fixture (1e-9), in-test ddof=0 recomputation tripwire, plugin shape/exact exports, barDatum honesty, additive schema fields, committed-data absence
  - The phase-close gate evidence: full pytest (2236 passed; 6 environmental failures classified), node lane 40/40, make lint, make typecheck, eslint 10.12.0 exact pin, ci.yml hash pin 33d2252e, data-tree porcelain clean, CDN pins x2 — zero CI changes (D17-11)
affects: [Phase 18 docs (the success-criteria mapping), maintainer post-milestone regeneration (whiskers activate when std keys appear), future fixture regeneration over new sweep trees]

# Actuals (#2632) — pairs with the plan's `estimate` (tokens 14000, tasks 3, confidence high).
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 8000
  tasks: 3
  commits: 2
  plan_head_before: 7551407abe33bbc6b5b99e5b1f31ed7b7af39c3a
  plan_head_after: f8991db00bbc08d4848f8fdb402ec9d0cbce2942

# Tech tracking
tech-stack:
  added: []  # zero installs; the only external invocation is the maintainer-blessed exact-pin npx eslint@10.12.0 already running in CI (T-17-SC held)
  patterns:
    - "Deterministic offline generator + committed generated fixture (the generate-tasks-index.js/tasks.json precedent) with a provenance block as the machine-checkable record of derivation"
    - "Triple tripwire against circular validation: grep gate on the generator source, in-test ddof=0 recomputation over provenance per-seed values, regeneration byte-idempotence"
    - "Committed-data absence AS an assertion — the public tree staying single-run is pinned, not assumed (D17-02 honesty both directions)"

key-files:
  created:
    - scripts/generate-errorbar-fixtures.js
    - tests/fixtures/errorbar/geometry-fixtures.json
    - tests/js/error-bars.test.js
  modified: []

key-decisions:
  - "The generator resolves the final_metrics key from the DECLARED datasets_info metric via lookup-ordered case candidates (eval_f1 first; AUPRC-style spellings covered) and enforces one uniform spelling across all three seeds of a cell — a mid-cell spelling change refuses loudly, never fabricates"
  - "Honest-absence fixture rows carry only JSON-representable stds (0 / null / negative); NaN and undefined are fed as in-test literals in the test lane (JSON cannot carry them)"
  - "Both fixture scale parameter sets are exercised in BOTH point and bar modes across the 4 cells (alternating assignment), so the geometry proof never rides a single scale"
  - "Task 3 is evidence-only (zero diff — its reversibility note says 'no production changes'), so it has NO separate commit; the measured commit count is 2 and the gate evidence lives in this SUMMARY"
  - "The full-suite pytest run requires the AutoDL academic accelerator (source /etc/network_turbo) on this box: tests/test_export_runs.py::test_d15_evaluate_cross_validates_suite_mapped_metric_conventions calls HF evaluate.load(), which phones home via HTTP HEAD unconditionally (its own file_utils path, unaffected by HF_HUB_OFFLINE) and hangs indefinitely when direct egress is silently dropped — environmental, resolved with the machine's sanctioned proxy, zero code changes"

patterns-established:
  - "Fake linear scale as the injected duck-typed seam: getPixelForValue = ((v - start) / range) * pixels mirrors the shipped UMD expression so fixture expectations and module output are computed against identical arithmetic (1e-9 holds trivially; bit-equal in practice)"

requirements-completed: [WEB-02, WEB-03]

# Coverage metadata (#1602) — one entry per shipped deliverable.
coverage:
  - id: D1
    description: "Fixture generator over the real r2 tree + committed generated fixtures: loud-refusing, deterministic (byte-idempotent), independent of the module under test, provenance-carrying (4 cells x 3 seeds with ddof=0 stds)"
    requirement: WEB-03
    verification:
      - kind: unit
        ref: "node --check scripts/generate-errorbar-fixtures.js && node scripts/generate-errorbar-fixtures.js && second-run byte-compare (idempotent OK); absent-root copy probe exits 1 naming the path"
        status: pass
      - kind: unit
        ref: "! grep -qE \"(require|import)[^;]*error-bars\" scripts/generate-errorbar-fixtures.js (independence OK) + node shape probe (4 cells x 3 per_seed keys)"
        status: pass
    human_judgment: false
  - id: D2
    description: "tests/js/error-bars.test.js — the 14-case node lane: geometry vs fixtures through the injected fake scale, in-test ddof=0 recomputation tripwire, plugin shape + exact export namespace + no DOM/canvas primitives, barDatum honest absence, additive schema fields (properties-only, required byte-pinned, additionalProperties:false at every closed level), committed-data absence across all four comparison files + one task file"
    requirement: WEB-03
    verification:
      - kind: unit
        ref: "node --test tests/js/error-bars.test.js (14/14 pass)"
        status: pass
      - kind: unit
        ref: "node --test tests/js/*.test.js (40/40 — full node lane, no cross-module regression)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Phase-close gates: full pytest suite (UNMODIFIED test_determinism.py + test_vendored_stats.py green), node lane, make lint, make typecheck, eslint 10.12.0 exact pin, ci.yml hash pin, committed-data porcelain cleanliness, CDN pins — zero CI workflow changes"
    requirement: WEB-03
    verification:
      - kind: unit
        ref: ".venv/bin/python -m pytest -q (2236 passed, 3 skipped, 6 failed — all six the documented environmental root-user chmod class: test_pilot_data_manager.py::test_driver_exits_bounded_when_claim_cannot_persist_cr02 + 5 test_services_download_queue.py persist-failure rows) + pytest tests/test_determinism.py tests/test_vendored_stats.py (10 passed unmodified)"
        status: pass
      - kind: unit
        ref: "make lint && make typecheck (both 'All checks passed!') && npx --yes eslint@10.12.0 --config eslint.config.mjs \"dnallm-mark/js/*.js\" (green)"
        status: pass
      - kind: unit
        ref: "git hash-object .github/workflows/ci.yml == 33d2252eb594e0faecece9e8015a332d8d6479ef && git status --porcelain dnallm-mark/data/ empty && grep -c 'chart.js@4.4.0' == 1 in both index.html and task.html"
        status: pass
    human_judgment: false

# Metrics
duration: 53min
completed: 2026-10-21
status: complete
---

# Phase 17 Plan 3: Node-Lane Fixtures + Phase-Close Gates (WEB-03) Summary

**Whisker geometry proven as a pure function against r2-sweep-derived generated fixtures (ddof=0 stds + inline expected pixels, triple-tripwired against circular validation), additive schema fields and committed-data absence pinned in a 14-case node lane, and the whole phase closed green under the existing CI lanes with zero workflow changes**

## Performance

- **Duration:** 53 min (started 2026-10-21T09:59:08Z, completed 2026-10-21T10:52:13Z; includes ~35 min diagnosing the environmental evaluate.load network hang and two full 10-min suite runs)
- **Tasks:** 3/3 (Task 3 evidence-only, no diff)
- **Files created:** 3 (exactly the declared files_modified set)

## Accomplishments

- Task 1: `scripts/generate-errorbar-fixtures.js` (311 lines, CommonJS zero-dep, the generate-tasks-index.js precedent) reads all 12 real r2 cells' final_metrics per-seed eval_f1 values, computes mean + ddof=0 population std + n_seeds with its OWN inline arithmetic (never the module under test), builds 2 scale parameter sets + 8 point/bar geometry scenarios with inline-computed expected pixels + 3 honest-absence cases, and writes the committed `tests/fixtures/errorbar/geometry-fixtures.json` with a provenance block in sorted-key deterministic serialization — byte-idempotent on regeneration (verified by byte-compare of two runs), loud-refusing on any missing cell/metric/non-finite value (verified by an absent-root copy probe: exit 1, named path), and grep-proven independent (`(require|import)[^;]*error-bars` matches nothing)
- Task 2: `tests/js/error-bars.test.js` (262 lines, 14 node:test cases, the data-api.test.js style) — GEOMETRY: every fixture scenario asserted through the injected fake linear scale (anchor/lo/hi/capHalf vs expected, 1e-9), both scales in both modes; RECOMPUTATION: per-cell ddof=0 std recomputed in-test over provenance per-seed values (1e-12) — the drifted/hand-edited fixture tripwire; PLUGIN SHAPE: id 'errorbars' lowercase, defaults (color/lineWidth/capWidth/drawStem), afterDatasetsDraw function, namespace exactly {barDatum, default, whiskerGeometry}, source free of window./document./getContext; HONEST ABSENCE: barDatum scalar for std 0/undefined/null/NaN/negative, [lo,hi] only for finite std > 0; SCHEMA: trio properties-only across the three strict schemas with required arrays byte-pinned (3-key entries / 16-key comparison) and additionalProperties:false at every closed level; COMMITTED-DATA ABSENCE: all four comparison files carry no std/n_seeds and a committed task file carries no modelEntry trio — the single-run tree pinned in both directions
- Task 3 (gates, evidence-only): full pytest 2236 passed / 3 skipped / 6 failed — every failure in the documented environmental root-user chmod class (persist-failure simulations that chmod 000, which root ignores; tests/tui/test_services_download_queue.py x5 + tests/tui/test_pilot_data_manager.py x1); tests/test_determinism.py + tests/test_vendored_stats.py pass UNMODIFIED (10/10 — the absent-case zero-drift proof over committed bytes and the vendored banner pin); full node lane 40/40; make lint and make typecheck "All checks passed!"; eslint 10.12.0 exact pin green over dnallm-mark/js/*.js; the byte-pin conjunction green in one command: ci.yml hash == 33d2252eb594e0faecece9e8015a332d8d6479ef, dnallm-mark/data/ porcelain clean, exactly one chart.js@4.4.0 occurrence in each of index.html and task.html. NO push — local commits only.

## ROADMAP Phase 17 Success-Criteria Mapping (the close-out assembly)

| # | Criterion | Evidence |
|---|-----------|----------|
| 1 | Aggregation emits additive-optional mean/std/n_seeds; suppressed fields → byte-identical output (zero-drift gate extended and green); METHODOLOGY.md documents display-only semantics + std definition | 17-01: population_std helper + both-view trio emission + per-model propagation; zero-drift split proven (test_trio_is_additive_over_trio_stripped_inputs + UNMODIFIED test_determinism over the committed tree — re-proven green in this plan's full-suite run); METHODOLOGY appendix fixes sd (ddof=1) vs std (ddof=0); close-out gates 145 + full suite green |
| 2 | Scatter renders whiskers via the vendored afterDatasetsDraw plugin (zero new CDN); task bar chart uses floating bars; tooltips gain ±std — verified against real sweep-derived artifacts | 17-02: error-bars.js plugin + scatter wiring + floating bars + closure tooltips, CDN pins byte-untouched; 17-03: the geometry the browser will draw proven as a pure function over the REAL r2 per-seed values (fixtures generated from pipeline/finetuned-sweep-r2, stds recomputed independently in-test) — the "verified against real sweep-derived artifacts" leg. OPTIONAL maintainer note (not a blocking gate; no automated browser lane exists by design): `bash start-server.sh` and eyeball the scatter/bar pages against a staged r2-derived data copy — whiskers stay visually dormant on the committed single-run data by construction (honest absence) |
| 3 | Node-lane tests cover plugin value→pixel math as a pure function and additive schema fields via generated fixtures | 17-03 Tasks 1-2: generator + committed fixture + 14-case lane (geometry 1e-9, ddof=0 recomputation tripwire, plugin shape, honest absence, additive schema fields, committed-data absence); full node lane 40/40 |

## Task Commits

Each task was committed atomically:

1. **Task 1: fixture generator over the real r2 tree + committed generated fixtures** - `588b368` (feat)
2. **Task 2: tests/js/error-bars.test.js — geometry vs fixtures, plugin shape, honest absence, additive schema fields** - `f8991db` (test)
3. **Task 3: phase-close full gates + zero-CI/zero-drift verification** - evidence-only (zero diff, no separate commit possible; the gate evidence is this SUMMARY's Accomplishments + the mapping table above)

**Plan metadata:** (see final docs commit below)

## Files Created/Modified

- `scripts/generate-errorbar-fixtures.js` (NEW) - the r2-reading deterministic fixture generator (independent inline arithmetic, loud refusal, sorted-key byte-idempotent serialization)
- `tests/fixtures/errorbar/geometry-fixtures.json` (NEW, generated) - 4 provenance cells x 3 seeds with per-seed eval_f1 values and ddof=0 stds, 2 scale sets, 8 geometry scenarios with expected pixels, 3 honest-absence cases
- `tests/js/error-bars.test.js` (NEW) - the 14-case geometry/schema/honest-absence node lane

## Decisions Made

- Metric-key resolution uses lookup-ordered case candidates from the DECLARED datasets_info metric (eval_f1 exact-first) with cross-seed spelling uniformity enforced — robust to AUPRC-style spellings without ever inventing a key
- NaN/undefined honest-absence inputs live as in-test literals (JSON cannot represent them); the fixture carries the representable 0/null/negative rows
- Scale/capWidth assignment alternates across the 4 cells so both fixture scale sets are exercised in both point and bar modes (the geometry proof never rides a single scale)
- The full-suite pytest invocation on this box requires `source /etc/network_turbo` (see Issues Encountered) — recorded here so the next phase close does not rediscover it

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**1. Full-suite pytest hang: HF evaluate.load() phones home unconditionally (environmental, resolved)**
- The first full-suite run (and a -v diagnostic rerun) stalled at tests/test_export_runs.py::test_d15_evaluate_cross_validates_suite_mapped_metric_conventions: `evaluate.load("pearsonr")` issues a real HTTP HEAD through its own file_utils retry path (unaffected by HF_HUB_OFFLINE, metric already cached), and direct egress to the HF endpoint is silently dropped on this AutoDL box without the academic accelerator — the connect() blocks indefinitely (faulthandler stack captured: urllib3 create_connection under evaluate/utils/file_utils.py http_head)
- Resolution: `source /etc/network_turbo` (the machine's sanctioned academic proxy) before the suite — evaluate.load then resolves in seconds; zero code changes, zero test changes; the completed run is the recorded evidence (2236 passed in 10:19)
- Classification: environmental network restriction on this machine, same class as the documented root-user chmod failures — not a regression, not masked

**2. The 6 pytest failures are exactly the documented environmental root-user chmod class**
- tests/tui/test_pilot_data_manager.py::test_driver_exits_bounded_when_claim_cannot_persist_cr02 + five tests/tui/test_services_download_queue.py persist-failure rows (chmod-000 write-block simulations that root ignores)
- Matches the machine's documented baseline ("runs as root — 6 chmod-based test failures are environmental"); this plan's JS-only diff cannot touch those lanes
- Note: the 4 documented TUI-golden reds (#50 pattern) did NOT appear — the working tree holds the orchestrator-owned regenerated uncommitted snapshots, so the golden tests passed against working-tree bytes; those files were left untouched per instructions

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 17 is COMPLETE: WEB-01 (17-01), WEB-02 (17-02, verification half closed here), WEB-03 (this plan) all landed; ROADMAP criteria 1-3 mapped to gate evidence above
- Whiskers/caps stay visually dormant on the committed single-run data (pinned by the committed-data absence assertions) — they activate when the maintainer regenerates from multi-seed artifacts post-milestone (deferred regeneration ruling)
- The r2 tree remains machine-local and gitignored; CI never needs it (the committed fixture is self-contained with provenance)
- Phase 18 (docs) can proceed; no blockers from this plan

## Self-Check: PASSED

All 3 created files exist on disk; both task commits (588b368, f8991db) are ancestors of HEAD; commits measured from the plan ledger = 2 (matches the two task commits; Task 3 evidence-only).

---
*Phase: 17-web-multiseed-error-bars*
*Completed: 2026-10-21*
