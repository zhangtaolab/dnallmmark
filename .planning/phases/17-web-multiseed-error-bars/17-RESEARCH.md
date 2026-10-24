# Phase 17: Web 多种子 Error Bar - Research

**Researched:** 2026-10-21
**Domain:** additive multi-seed statistics through the offline data chain + Chart.js 4.4.0 error-bar rendering (vendored inline plugin, native floating bars) + Node-lane pure-function testing
**Confidence:** HIGH (all integration points read from live code with line citations; Chart.js facts verified against the pinned 4.4.0 sources and the exact shipped UMD bytes)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Aggregation Additive Fields (WEB-01)**
- **D17-01:** Every model×dataset gains optional `mean`/`std`/`n_seeds` when multi-seed data exists; std = population std over seeds (ddof=0), semantics fixed ONCE in METHODOLOGY.md appendix
- **D17-02:** Zero-drift gate EXTENDED (not rebuilt): no-multi-seed inputs produce byte-identical JSON (absent keys never written); multi-seed inputs add ONLY the new keys
- **D17-03:** Write point = script/summarize_comparison.py aggregation + the vendored aggregate_seeds per-seed statistics (single ownership)
- **D17-04:** Readers tolerant (optional keys, existing data stays valid); schemas/ gains optional-field definitions; display-only — no ranking/methodology version bump

**Chart Error Bars (WEB-02)**
- **D17-05:** Scatter whiskers via a vendored inline plugin (~40 lines, afterDatasetsDraw + getPixelForValue) — mean±std geometry; NO new CDN dependency (sgratzl plugin stays the documented ratified fallback only)
- **D17-06:** Task bar chart uses native Chart.js floating bars ([mean-std, mean+std]) + the same plugin's cap rendering
- **D17-07:** Tooltips gain a ±std line when the field exists (existing tooltip lines untouched)
- **D17-08:** Honest absence: points without std render normally with no whiskers — never a zero-width fake whisker

**Node Tests & Gates (WEB-03)**
- **D17-09:** The plugin's value→pixel math extracted as a pure importable function; Node-lane tests assert whisker-end geometry against generator-produced fixtures (never hand-written)
- **D17-10:** Schema tests: additive optional fields asserted; absent-field inputs produce byte-identical aggregation output (the zero-drift extension)
- **D17-11:** Full CPU lanes green + node lane green; zero CI changes; Chart.js 4.4.0 UMD CDN pin untouched; ES-module no-build architecture unchanged
- **D17-12:** METHODOLOGY.md appendix fixes std semantics + display-only declaration once; ranking math untouched

### Claude's Discretion
- The plugin's module home (js/ vendored file name) provided it is imported by both charts and covered by the pure-function tests
- Whisker styling details (cap width, color token choice from the existing palette) provided existing tokens are used
- Fixture generator shape (Node script location)

### Deferred Ideas (OUT OF SCOPE)
- TUI docs → Phase 18
- Full leaderboard regeneration with multi-seed data → maintainer decision post-milestone (real multi-seed artifacts exist from Phase 15's sweep)
- v2: ±std table columns, CI-95/IQR selector (WEB-D01/D02 in REQUIREMENTS)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WEB-01 | Aggregation emits additive-optional `mean`/`std`/`n_seeds` per model×dataset; absent fields → byte-identical JSON (zero-drift gate proves additivity); METHODOLOGY.md documents display-only semantics | Two-layer emission map (§ Additive Data Architecture): export_runs per-datasetEntry trio + summarize per-model propagation; zero-drift gate located (test_determinism.py absent-case, test_ci_replay.py additive-case); ddof=0 vs vendored ddof=1 discrepancy documented; schema addition points identified (strict, additionalProperties:false) |
| WEB-02 | Scatter whiskers via vendored inline Chart.js plugin (afterDatasetsDraw, no new CDN); task bar chart native floating bars + whisker caps; tooltips ±std | Chart.js 4.4.0 plugin/floating-bar APIs verified against v4.4.0 tag sources + shipped UMD bytes; exact integration line-citations in main.js/task.js; mixed scalar/array bar data confirmed; tooltip raw-array pitfall documented |
| WEB-03 | Node-lane tests cover plugin value→pixel math as pure function + additive schema fields (fixtures generated, not hand-written) | Node lane patterns documented (node:test, require(esm), 26 tests green); generator precedent (scripts/generate-tasks-index.js); real r2 multi-seed artifacts located for fixture generation; pure-function seam design provided |
</phase_requirements>

## Summary

Phase 17 threads seed-level statistics through an already highly-disciplined, byte-pinned data chain (run records → `export_runs.py` → per-model/task views → `summarize_comparison.py` → `models_comparison*.json` → static charts) and renders them as error bars on two Chart.js 4.4.0 charts, without moving a single published number and without any new dependency. The chain is provably deterministic end-to-end and guarded by two complementary byte-identity gates: `tests/test_determinism.py` (real committed single-run data — the **absent-field** case, already green and unmodifiable in its assertions since it compares regenerated bytes against committed bytes) and `tests/test_ci_replay.py` (committed 3-seed `e2_replay` fixture — the **additive** case, where the emitted views gain only the new keys). The phase extends the second and adds targeted schema/additivity tests; the first needs no edit to prove the absent case.

The single most load-bearing technical finding: **the vendored `aggregate_seeds`'s `sd` field is sample std (ddof=1), while D17-01 pins the new `std` as population std (ddof=0)** — these are different numbers (verified numerically against real r2 artifacts: seeds {0.0, 0.4, 0.2} → `sd: 0.2` in the artifact vs population std 0.16330). The vendored section is edit-forbidden (`VERBATIM COPY, DO NOT EDIT` banner pinned by `tests/test_vendored_stats.py`), so the ddof=0 `std` must be computed by NEW code outside the vendored block, and the METHODOLOGY appendix must state both conventions so no reviewer confuses `sd` (reviewer view) with `std` (display view).

Second key finding: WEB-01's "per model×dataset" fields must land in **both** producer layers, because the two charts read different files. The task bar chart reads `{task}_task_performance.json` (written by `export_runs.py` — summarize never touches these files); the scatter reads `models_comparison{,_arena}.json` (written by `summarize_comparison.py`). D17-03's "write point = summarize aggregation + vendored aggregate_seeds statistics (single ownership)" is satisfiable as: the per-dataset trio is emitted where per-seed values exist (`export_runs.py`'s `export_runs_tree` — its own docstring calls step 3 "aggregate"), and `summarize_comparison.py` (which already imports from `export_runs`) reads the optional trio and propagates a per-model display std into the comparison files. Single ownership of the *statistics semantics* stays with the vendored machinery plus one shared ddof=0 helper. The exact JSON shape (recommended below) is the main planning ratification item.

**Primary recommendation:** emit the optional trio `mean`/`std`/`n_seeds` per `datasetEntry` (primary metric) in both export views in the single D-16 pass, compute `std` via a new ddof=0 helper beside (never inside) the vendored section, propagate an optional per-model `std`/`n_seeds` into all four comparison files in `aggregate_models`, extend `test_ci_replay.py`-class tests for the additive case, and build the whisker plugin as `dnallm-mark/js/error-bars.js` with a pure `whiskerGeometry()` export tested in the Node lane against r2-derived generated fixtures.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Per-seed stats aggregation (mean/std/n_seeds emission) | Offline data scripts (`script/export_runs.py`) | — | Per-seed values exist only here (`_collect_cell_values`); committed data chain stays the single source of every published number |
| Per-model std propagation into leaderboard JSON | Offline aggregation (`script/summarize_comparison.py`) | — | `aggregate_models` already owns the per-model performance block read by the scatter |
| Schema contracts for optional fields | `schemas/*.json` | — | Strict draft-2020-12 contracts govern every committed file (test_schemas.py validates all) |
| Scatter error-bar rendering | Browser (`js/main.js` + vendored plugin) | — | Canvas drawing is client-only; destroy-before-render discipline lives here |
| Bar floating-bar + cap rendering | Browser (`js/task.js` + vendored plugin) | — | Same; tooltip ±std line is a tooltip callback change |
| Whisker value→pixel math | Browser-shared pure function (`js/error-bars.js`) | Node test lane | Pure geometry, importable by both charts and require-able by node:test |
| Zero-drift proof | Test lanes (`test_determinism.py`, `test_ci_replay.py`) | — | Byte-identity is a CI property, not a code property |
| std semantics documentation | `docs/METHODOLOGY.md` appendix | — | Fixed-once, display-only declaration per D17-12 |

## Standard Stack

No new packages. This phase installs ZERO external dependencies (vendored inline Chart.js plugin, no npm, no CDN change) — the Package Legitimacy Audit below is therefore a no-op confirmation.

### Core (existing, pinned — reuse, do not change)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Chart.js | 4.4.0 UMD via jsDelivr CDN | All charts; the error-bar plugin targets its plugin API | Repo CDN pin (`dnallm-mark/index.html:18`, `task.html:20`); D17-11 forbids touching it [VERIFIED: live HTML + CLAUDE.md] |
| node:test | built-in (Node ≥18 local v26.4.0, CI pins 24) | JS unit lane | Zero-npm-deps lane already green at 26 tests (`node --test tests/js/*.test.js`) [VERIFIED: Makefile:101-103, .github/workflows/ci.yml:87-88] |
| numpy | locked 2.5.3 (`data` group) | mean/std arithmetic in the scripts | `aggregate_seeds` and `summarize_comparison` already numpy-based [VERIFIED: script/export_runs.py:117, script/summarize_comparison.py:94] |
| jsonschema (Draft202012Validator) | dev/data group | schema tests for the optional fields | test_schemas.py / test_ci_replay.py pattern [VERIFIED: tests/test_ci_replay.py:61] |

### Supporting (existing fixtures/artifacts reused as generator inputs)

| Artifact | Location | Purpose | When to Use |
|----------|----------|---------|-------------|
| r2 sweep run records | `pipeline/finetuned-sweep-r2/{model}/{task}/seed_{42,43,44}/run_record.json` | Real multi-seed values with genuine spread (e.g. 5mC f1 seeds 0.7142857/0.5/0.5714286) for fixture generation and WEB-02 "verified against real sweep-derived artifacts" | Fixture generator input + manual render verification [VERIFIED: read this session] |
| Archived r2 chain outputs | `.planning/phases/15-dual-gpu-validation-subsets/artifacts/*.json` + `/root/autodl-tmp/phase15-evidence/consumption-r2/seed_stats/*.json` | The already-exported comparison + seed_stats shapes from the real sweep | Committed-copy source for Node fixtures (must land under `tests/fixtures/` for CI) [VERIFIED: read this session] |
| e2_replay fixture | `tests/fixtures/e2_replay/` (3 models × 1 task × 3 seeds) | The additive-case zero-drift extension | Extend test_ci_replay.py assertions [VERIFIED: tests/test_ci_replay.py:67-74] |
| synthetic_models fixture | `tests/fixtures/synthetic_models/` (3 fake models, single-run) | Absent-case unit tests for summarize | Existing pattern [VERIFIED: tests/test_golden.py] |

## Package Legitimacy Audit

> No external packages are installed or recommended by this phase. The plugin is vendored inline source (a new file in `dnallm-mark/js/`), Chart.js stays the existing CDN pin, and the Python/Node changes use only already-locked dependencies. Gate result: **nothing to check — no [SLOP]/[SUS] candidates possible**.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| (none) | — | — | — | — | — | No packages installed |

## Architecture Patterns

### System Architecture Diagram

```
run_record.json per seed            export_runs.py (export_runs_tree)            summarize_comparison.py
{root}/{model}/{task}/seed_{n}  →   ONE pass, TWO keyings (D-16)             →   load_model_inputs()
 metrics per seed                    ├─ {task}_task_performance.json               reads per-model view
                                     │    performance.{model} =                     (optional trio tolerated)
                                     │    {dataset, parameters, performance,       ├─ calculate_dataset_stats  (UNTOUCHED)
 real multi-seed trees:              │     + NEW optional mean/std/n_seeds}        ├─ aggregate_models
 · pipeline/finetuned-sweep-r2       ├─ {task}_seed_stats.json   (reviewer view;   │    + NEW optional per-model std/n_seeds
 · tests/fixtures/e2_replay              vendored aggregate_seeds: sd=ddof=1)      └─ writes models_comparison{,_animal,_plant,_microbe}.json
                                     └─ {model}_performance.json                        (sort_keys=True, indent 4)
                                          (same datasetEntry blocks)                          │
                                                                                           │ fetch (DataAPI)
                                          MISSING trio (single-run data)                    ↓
                                          ⇒ keys never written                        models_comparison*.json
                                                                                           │
   Browser (no build step) ────────────────────────────────────────────────────────────────┤
   js/error-bars.js (NEW vendored plugin)                                                  │
   ├─ pure whiskerGeometry(point, std, scale, opts) → {x, yLo, yHi, capHalf}  ←─── Node lane (node:test)
   ├─ scatter: afterDatasetsDraw → yScale.getPixelForValue(mean±std)          ←─── tests/js/error-bars.test.js
   └─ bar caps: same plugin draws caps over native floating bars               fixtures generated from r2 artifacts
```

Reader flow: main page scatter reads `models_comparison{arena}.json` per point `{x: sum_PFLOPs, y: weighted_score|rank_score, model}`; task page bar chart reads `{task}_task_performance.json` via TaskLoader. Both tolerate absent std (D17-08).

### Additive Data Architecture (the two-layer emission map)

WEB-01's "per model×dataset" fields must reach two DIFFERENT consumers through two different writers — this is the structural fact that shapes the whole phase:

| Layer | File(s) | Writer (live code) | Consumer | Optional fields |
|-------|---------|--------------------|----------|-----------------|
| Per-dataset trio | `{task}_task_performance.json` + `{model}_performance.json` (the SAME datasetEntry block, one pass — D-16) | `script/export_runs.py` `export_runs_tree` (script/export_runs.py:745-895; per-seed values exist only here, :566-617) | task bar chart (floating bars + tooltips); summarize's reader | `mean`/`std`/`n_seeds` per datasetEntry, primary metric, emitted when n_seeds ≥ 2 (A2/A3) |
| Per-model propagation | `models_comparison{,_animal,_plant,_microbe}.json` | `script/summarize_comparison.py` `aggregate_models` (mirror the `weighted_score` pattern at :408-411 so all four files inherit uniformly) | main-page scatter (whiskers + tooltips) | optional `std`/`n_seeds` on the per-model performance block (A1; `mean` not duplicated — `avg_raw` already is the mean) |

Why both layers are mandatory: the bar chart's data source (`task_performance/`) is **never written by summarize** (the pivot was deleted at 04-05; those files are static committed data until the maintainer runs an E2'-class export), and the scatter's data source (`models_comparison*.json`) is never written by export_runs. D17-03's single-ownership constraint is satisfied by: per-seed statistics semantics owned by the vendored machinery plus ONE new ddof=0 helper in `export_runs.py`, imported (never duplicated) by `summarize_comparison.py` — the same single-authority import shape as the existing `from export_runs import resolve_dataset_metric` (script/summarize_comparison.py:96).

Zero-drift per layer: absent case — summarize over committed (trio-less) model_performance files emits nothing new (test_determinism.py green unmodified); export over 1-seed cells emits nothing new (extend the existing 1-seed degenerate-cell tests in test_export_runs.py). Additive case — the e2_replay 3-seed chain (test_ci_replay.py:227-295) gains only-new-keys assertions in both views AND the propagated comparison files.

### Recommended Project Structure (delta only)

```
dnallm-mark/js/error-bars.js      # NEW — vendored plugin + pure geometry fn
                                  #   export function whiskerGeometry(...)  (pure, tested)
                                  #   export default errorBarsPlugin {id, afterDatasetsDraw}
                                  #   dual export: ES `export` (browser) — same file require-able
                                  #   via require(esm) in Node (the data.js precedent)
scripts/generate-errorbar-fixtures.js   # NEW (discretion; alternative: in-test generator) —
                                  #   reads committed r2-derived JSON → writes tests/fixtures/errorbar/*.json
tests/js/error-bars.test.js       # NEW — geometry assertions vs generated fixtures
tests/fixtures/errorbar/          # NEW — generated (never hand-written) fixture JSON
```

No new Python files: the ddof=0 std helper lands beside the vendored section in `script/export_runs.py` (emission) and is imported by `script/summarize_comparison.py` (propagation) — the IN-03-style single-owner import already exists (`from export_runs import resolve_dataset_metric`, script/summarize_comparison.py:96).

### Pattern 1: Additive-only JSON change (the zero-drift discipline)

**What:** Optional keys are added to strict schemas; producers write them ONLY when multi-seed data exists; byte-identity is proven per direction.
**When to use:** Every JSON emission this phase.
**Why:** The repo's core value — published numbers never move silently. The F6 `weighted_score` addition (schema-required 16th key, data_version 1.1.0) is the precedent, but that change REGENERATED data in the same commit. This phase is stricter: committed data files stay byte-identical (no regeneration — deferred to maintainer), so the absent case must hold over the CURRENT committed bytes.

The two gate halves, exactly:
- **Absent case (no edit needed to prove):** `tests/test_determinism.py::test_chain_is_deterministic_and_matches_committed` copies `dnallm-mark/data/model_performance/` + `task_performance/` into tmp, runs `summarize_comparison.py` + the JS generator twice, and asserts regenerated == committed **byte-for-byte** (lines 203-218) plus "the committed tree is untouched" (220-231). Committed model_performance files carry no trio → summarize must not emit per-model std → this test passing unmodified IS the absent-field proof. [VERIFIED: tests/test_determinism.py:147-231]
- **Additive case (extend):** `tests/test_ci_replay.py` runs the full D-16 chain over `tests/fixtures/e2_replay/` (every cell 3 seeds): export → both views → summarize. The extension asserts the emitted views gain ONLY the new keys (diff old-block vs new-block: every pre-existing key byte-equal; new keys exactly the trio), and that a 1-seed cell emits none (the ephemeral-tree builders in tests/test_export_runs.py already create 1-seed degenerate cells — line 22 docstring: "1-seed degenerate cells (sd/ci95 None, method `none`)"). [VERIFIED: tests/test_ci_replay.py:96-123, tests/test_export_runs.py:22,108-149]

### Pattern 2: Vendored inline Chart.js plugin (verified against v4.4.0)

**What:** A plugin object in the chart's `plugins` config array, hooking `afterDatasetsDraw`.
**When to use:** Both charts (scatter whiskers; bar caps).
**Example (API verified against the v4.4.0 docs source at `docs/developers/plugins.md`, tag v4.4.0):**

```javascript
// Source: https://raw.githubusercontent.com/chartjs/Chart.js/v4.4.0/docs/developers/plugins.md (verbatim)
const chart1 = new Chart(ctx, {
    plugins: [plugin]
});
// hook signature (same doc):
//     beforeInit: function(chart, args, options) { //.. }
```

- Plugin options scope under `options.plugins.{plugin-id}`; id follows npm-name rules (no uppercase — e.g. `id: 'errorBars'` is INVALID by the docs' "can't contain uppercase letters" rule; use `id: 'seed-error-bars'` or `'errorbars'`). [CITED: chartjs.org/docs/4.4.0/developers/plugins.html]
- `afterDatasetsDraw(chart, args, options)` draws AFTER datasets → whiskers overlay points/bars cleanly; drawing uses `chart.ctx` + `chart.chartArea`; per-dataset pixels via `chart.getDatasetMeta(i).data[j].x/.y`. All of `afterDatasetsDraw`, `getDatasetMeta`, `getPixelForValue` are present in the exact shipped artifact `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js` (205,222 bytes, downloaded and grepped this session). [VERIFIED: cdn.jsdelivr.net pinned artifact]
- Linear-scale math in the shipped build (de-minified): `getPixelForValue(t){return null===t?NaN:this.getPixelForDecimal((t-this._startValue)/this._valueRange)}` — the pure function should mirror this linear mapping so Node tests can assert pixel geometry with a fake scale. The log-scale override substitutes `this.min` for 0/undefined values — whiskers on the log x-axis are in scope only if x-whiskers are ever wanted (FLOPs std ≈ 0; not needed). [VERIFIED: pinned UMD bytes]

### Pattern 3: Native floating bars + mixed honest absence (verified against v4.4.0 source)

**What:** Bar `data` entries become `[mean-std, mean+std]` arrays; models without std keep scalar values.
**When to use:** task.js bar chart (D17-06).
**Why it works:** BarController v4.4.0 source (verbatim): `parseArrayData` override comment — *"Overriding array data parsing since we support mixed primitive/array data for float bars"*; and:

```javascript
// Source: https://raw.githubusercontent.com/chartjs/Chart.js/v4.4.0/src/controllers/controller.bar.js (verbatim)
function parseFloatBar(entry, item, vScale, i) {
  const startValue = vScale.parse(entry[0], i);
  const endValue = vScale.parse(entry[1], i);
  ...
  // Store `barEnd` (furthest away from origin) as parsed value,
  // to make stacking straight forward
  item[vScale.axis] = barEnd;
  item._custom = { barStart, barEnd, start: startValue, end: endValue, min, max };
}
```

So mixed scalar/array data in ONE dataset is first-party supported (honest absence rides the same dataset — no dataset splitting), and the parsed `_custom` carries `{min, max}` for free.

### Anti-Patterns to Avoid

- **Editing the vendored `aggregate_seeds` section:** banner says `VERBATIM COPY, DO NOT EDIT` (script/export_runs.py:122); `tests/test_vendored_stats.py` pins suite semantics. The ddof=0 std is a NEW sibling helper, never an edit, never a "fix" to `sd`.
- **Computing `std` as `sd/sqrt(n)` or reusing `sd`:** `sd` is ddof=1; D17-01 pins ddof=0. Confusing them silently changes every displayed whisker. Document both in the METHODOLOGY appendix.
- **Zero-width fake whiskers:** a point with `std === 0` from a single seed is still "no multi-seed data" → no keys, no whisker (D17-08). Only emit when n_seeds ≥ 2.
- **Sorting/handling arrays in the bar tooltip with `context.raw` typed checks:** today `label: (context) => { const value = context.raw; return \`...${typeof value === 'number' ? value.toFixed(4) : value}\`; }` (dnallm-mark/js/task.js:394-397). With floating bars `context.raw` is the `[lo, hi]` array → `typeof` fails → the tooltip would print `"F1 Score: 0.5,0.69"` (array toString). Use `context.dataIndex` + closure over the display models, or `context.parsed._custom`. Also note `context.parsed.x` for a horizontal floating bar is `barEnd` (furthest from ORIGIN — NOT reliably the hi end when negatives are involved); do not use parsed.x as "the value".
- **Client-side recomputation of anything:** every displayed number (including ±std) is precomputed offline; the browser only reads (the DATA-07 lesson, js/config.js:38-41 comment).
- **Touching ranking math to get scatter y-std:** per-seed rank_score would require per-seed re-ranking of the corpus — ranking-adjacent and out of bounds. The scatter's per-model std is a display-only propagation of per-dataset stds (see Open Questions).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Error-bar rendering | Custom canvas overlay / re-render loop | Chart.js inline plugin (`afterDatasetsDraw` + `getPixelForValue`) | First-party hook; pixel math already scale-aware (log included); the plugin mirrors internal BarController usage [VERIFIED: pinned UMD] |
| Bar range rendering | Drawing range rects manually | Native floating bars `[lo, hi]` | First-party since v2; mixed scalar/array in one dataset is explicitly supported [VERIFIED: v4.4.0 source] |
| Per-seed statistics | A new stats implementation | Vendored `aggregate_seeds` (n_seeds, mean) + one new ddof=0 std helper beside it | Single ownership (D17-03); the vendored copy is suite-pinned and edit-forbidden |
| Byte-identity checking | New diff logic | Existing gate tests (extend test_ci_replay; test_determinism already proves absent case) | The D-06 diff vocabulary + committed-byte comparison already exist |
| Fixture values | Hand-typed pixel expectations | Generator script over r2-derived real values | D17-09 explicitly forbids hand-written fixtures |

**Key insight:** every hard problem in this phase (byte-identity, schema strictness, statistics provenance, canvas geometry) already has a repo- or Chart.js-native mechanism; the phase is almost entirely *wiring*, and the discipline is not to invent parallel mechanisms.

## Common Pitfalls

### Pitfall 1: The `sd` (ddof=1) vs `std` (ddof=0) mismatch
**What goes wrong:** Reusing the vendored `sd` as the display `std` (or dividing by sqrt(n)) silently reports the wrong convention; reviewers cross-checking `seed_stats` artifacts against chart whiskers see inconsistent numbers.
**Why it happens:** The vendored block emits `{"n_seeds", "mean", "sd", "ci95", "method"}` [VERIFIED: script/export_runs.py:194-224 — `"sd": float(arr.std(ddof=1)) if n > 1 else None` at line 197]; D17-01's std is population (ddof=0). Real artifact proof: seeds {0.0, 0.4, 0.2} → artifact `sd: 0.2` (ddof=1) vs population std ≈ 0.16330.
**How to avoid:** New `population_std(values)` helper outside the vendored banner; METHODOLOGY appendix states both conventions in one sentence each; a test asserts the two differ on a fixture (guard against future "simplification").
**Warning signs:** any diff line inside the vendored banner; whisker half-width equal to `sd` on any n=3 cell.

### Pitfall 2: Strict schemas reject the additive fields
**What goes wrong:** Emission lands but `test_schemas.py` / `test_ci_replay.py` validators fail: `schemas/model_performance.json` and `schemas/task_performance.json` are `additionalProperties: false` at every level [VERIFIED: schemas/model_performance.json:4 "adding a field requires a schema change first"; datasetEntry `required: ["dataset","parameters","performance"]` at :48], and `schemas/models_comparison.json` performance block lists all 16 keys required with `additionalProperties: false` (:37).
**Why it happens:** The D-01 discipline: schema change FIRST, same commit as producer + data + tests.
**How to avoid:** Same-commit ordering: schema optional properties (added to `properties`, NOT to `required`) → producer emission → additive tests. Committed data files never change, so existing schema tests stay green with zero regeneration (the optional fields simply don't occur in committed files).
**Warning signs:** any `additionalProperties: true` relaxation; adding the trio to `required` anywhere.

### Pitfall 3: Byte-drift via float formatting / key insertion order
**What goes wrong:** The additive path accidentally changes serialization of EXISTING keys (e.g. recomputing `mean` and overwriting `performance[metric]` with a differently-rounded float; or dict iteration order changes).
**Why it happens:** Both writers serialize with `json.dump(..., indent=4, ensure_ascii=False, sort_keys=True)` [VERIFIED: script/summarize_comparison.py:569; script/export_runs.py:742] — key order is safe — but VALUES must be untouched: the trio's `mean` must equal the existing emitted mean exactly (`float(np.mean(ordered))`, export_runs.py:838) — compute it from the same `ordered` list, never re-derive via a different path.
**How to avoid:** The additive test asserts: for every pre-existing key, `old[key] == new[key]` byte-exact; new key set ⊆ {mean, std, n_seeds}; absent-case JSON equality on full bytes.
**Warning signs:** `repr` differences in regenerated e2_replay outputs; `FLOAT_ULP` diffs in the D-06 vocabulary.

### Pitfall 4: Floating-bar tooltip regression on non-std charts
**What goes wrong:** Converting bar data to arrays unconditionally breaks tooltips for models without std (raw = number → fine) and for std models (raw = array → prints "0.5,0.69"), and `extractModels`'s `parseFloat(metricValue)` (js/task.js:294) breaks if fed arrays.
**Why it happens:** The tooltip callback assumes scalar `context.raw` (js/task.js:394-397); the metricValue drives sorting and the leaderboard table too.
**How to avoid:** Keep `model.metricValue` scalar (mean) for sort/table; build the array form ONLY in the `data` mapping inside `renderBarChart` (`m.std != null ? [m.metricValue - m.std, m.metricValue + m.std] : m.metricValue`); tooltip reads `displayModels[context.dataIndex]` for mean ± std.
**Warning signs:** NaN in sort; tooltip strings containing commas from array coercion.

### Pitfall 5: Plugin id / registration conventions
**What goes wrong:** Plugin object without `id` (not configurable), or id with uppercase (violates the documented npm-name rule); or trying `Chart.register` for an inline plugin.
**Why it happens:** Chart.js docs: inline plugins "are not registered" and "can't be registered globally" [CITED: chartjs.org/docs/4.4.0/developers/plugins.html].
**How to avoid:** Plugin object `{id: 'errorbars', afterDatasetsDraw(chart, args, options){...}, defaults: {...}}` passed in each chart's `config.plugins` array (main.js renderScatterChart's `config` at :322-379 gains `plugins: [errorBarsPlugin]`; task.js renderBarChart's at :371-424 the same). Config currently has NO `plugins` array (only `options.plugins`) — adding the top-level key is the registration seam.
**Warning signs:** `options.plugins.errorbars` consulted but plugin reads raw defaults; two charts needing different cap widths without an options seam.

### Pitfall 6: Arena files divergence
**What goes wrong:** Per-model std lands in `models_comparison.json` but not the three arena files (or vice versa) — the scatter reads the ARENA file for animal/plant/microbe views.
**Why it happens:** `aggregate_models` is called 2× (all + per-species; main() :563-566 and :585-588) — the optional fields must be emitted inside `aggregate_models` so all four files inherit them uniformly.
**How to avoid:** Emit in `aggregate_models` (single site), exactly like `weighted_score` (:408-411).
**Warning signs:** any emission site in `main()` outside the shared aggregation function.

### Pitfall 7: CWD-sensitivity of summarize in new tests
**What goes wrong:** New summarize tests run from the wrong CWD and read the REAL `dnallm-mark/data/model_performance/` or write into the repo.
**Why it happens:** `main()` resolves `input_dir = 'model_performance'` against CWD (script/summarize_comparison.py:529); the established pattern is `monkeypatch.chdir(work)` + staged copies + `REGISTRY_PATH` monkeypatch (test_ci_replay.py:126-140).
**How to avoid:** Reuse `_run_aggregate_half`-style staging; never new path conventions.

## Code Examples

### Aggregation emission sites (live code, verbatim context)

The per-cell mean today — the trio's `mean` must equal this value exactly:
```python
# Source: script/export_runs.py:833-844 (verbatim)
            metric_block: dict[str, Any] = {}
            for key in sorted(EXPORT_METRIC_KEYS):
                values = per_metric.get(key)
                if values:
                    ordered = [values[seed] for seed in sorted(values)]
                    metric_block[key] = float(np.mean(ordered))
```
`per_metric` (from `_collect_cell_values`, :566-617) is `{stats key: {seed: finite value}}` over COMPLETED records only — the same source `stats_doc` uses; the trio joins here (per datasetEntry, on the primary metric) with `len(values) >= 2` as the emission gate.

The vendored output shape (do not edit; compute std alongside, not inside):
```python
# Source: script/export_runs.py:194-198 (verbatim)
    out: dict[str, Any] = {
        "n_seeds": n,
        "mean": float(arr.mean()),
        "sd": float(arr.std(ddof=1)) if n > 1 else None,
    }
```

The per-model optional-field precedent (weighted_score — the exact pattern to mirror):
```python
# Source: script/summarize_comparison.py:408-411 (verbatim)
        if include_weighted:
            aggregated_results[model_alias]["performance"]["weighted_score"] = (
                sum(s['zscore'] for s in model_m_stats) / len(target_datasets)
            )
```

Serialization contract (byte-identity depends on it — keep identical):
```python
# Source: script/summarize_comparison.py:568-569 (verbatim)
    with open(output_total, "w", encoding='utf-8') as f:
        json.dump(total_comparison, f, indent=4, ensure_ascii=False, sort_keys=True)
```

### Chart integration points (live code)

Scatter: one dataset per model, single point, plugin data rides the raw object (main.js:271-277 verbatim):
```javascript
      .map(model => ({
      label: model.id,
      data: [{
        x: model.performance?.sum_PFLOPs || 0,
        y: model.performance?.[viewAxis.field] || 0,
        model: model
      }],
```
Destroy-before-render (main.js:233-235 / task.js:343-345 verbatim): `if (this.state.chart) { this.state.chart.destroy(); }` — the plugin needs no lifecycle handling because charts are rebuilt wholesale.

Scatter tooltip label already returns an ARRAY of lines (main.js:341-355) — append the ±std line only when present (D17-07). Bar tooltip returns a STRING (task.js:394-397) — must learn the array/raw-array case (Pitfall 4).

Plugin consumption sketch (geometry as a pure function — the WEB-03 test seam):
```javascript
// Recommended shape (new file dnallm-mark/js/error-bars.js)
export function whiskerGeometry(point, std, yScale, capWidth) {
  // Pure: no Chart instance, no canvas — a scale-like object with
  // getPixelForValue is injected; Node tests pass a linear fake.
  const yLo = yScale.getPixelForValue(point.y - std);
  const yHi = yScale.getPixelForValue(point.y + std);
  return { x: point.x, yLo, yHi, capHalf: capWidth / 2 };
}

const errorBarsPlugin = {
  id: 'errorbars',
  afterDatasetsDraw(chart, _args, options) {
    const { ctx } = chart;
    const yScale = chart.scales.y;
    ctx.save();
    ctx.strokeStyle = options.color; ctx.lineWidth = options.lineWidth;
    chart.data.datasets.forEach((ds, i) => {
      if (chart.getDatasetMeta(i).hidden) return;
      ds.data.forEach((raw, j) => {
        const el = chart.getDatasetMeta(i).data[j];
        const std = raw.std;                       // optional — absent ⇒ skip (D17-08)
        if (typeof std !== 'number' || !isFinite(std) || std <= 0) return;
        const g = whiskerGeometry({ x: el.x, y: el.y }, std, yScale, options.capWidth);
        ctx.beginPath();
        ctx.moveTo(g.x, g.yLo); ctx.lineTo(g.x, g.yHi);        // stem
        ctx.moveTo(g.x - g.capHalf, g.yLo); ctx.lineTo(g.x + g.capHalf, g.yLo); // caps
        ctx.moveTo(g.x - g.capHalf, g.yHi); ctx.lineTo(g.x + g.capHalf, g.yHi);
        ctx.stroke();
      });
    });
    ctx.restore();
  },
  defaults: { color: '#595F6E', lineWidth: 1, capWidth: 8 },
};
export default errorBarsPlugin;
```
Notes: `el.y` is already the plotted mean's pixel; the ±std pixels come from the scale (clamping to `chart.chartArea` if whiskers exceed the axis limits — the scatter pins explicit `min`/`max` at main.js:298-299, so mean±std can fall OUTSIDE the chart area; clamp or let it draw — decide in plan). Color token: `--color-text-secondary` (#595F6E) already hardcoded in chart configs (main.js:308) — matching-token hex in `defaults` follows existing chart precedent; resolving via `getComputedStyle` is the stricter-token alternative (both defensible; discretion D17 styling).

Dual-export precedent for Node require(esm):
```javascript
// Source: dnallm-mark/js/data.js:255-261 (verbatim)
// Export for ES6 modules
export default DataAPI;

// Compatible with CommonJS
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DataAPI;
}
```
Tests import via `require('../../dnallm-mark/js/data.js').default` (tests/js/data-api.test.js:20) — `error-bars.js` follows the same shape; `node --check` (ci.yml:89-93) passes ES syntax via module detection (Node 24/26).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Chart.js v2 global plugins only | v4 inline `plugins: [plugin]` array per chart | Chart.js 3.0/4.x | No `Chart.register` needed; plugin scoped per chart instance [CITED: chartjs.org docs 4.4.0] |
| Custom error-bar drawing loops | Native floating bars + `getPixelForValue` plugins | Chart.js 2.9 (float bars) / 3.x (scale API) | First-party mixed scalar/array data; ~40-line vendored plugin suffices [VERIFIED: v4.4.0 source] |
| Hand-maintained per-task JSON (`get_task_performance.py`) | export_runs dual-view emission (D-16, one pass) | Phase 04-05 retirement | The trio joins the existing single-pass emission — no new writer |
| `sd` shown to reviewers via seed_stats only | Display `std` (ddof=0) on public charts | This phase | Two named conventions, both documented in METHODOLOGY |

**Deprecated/outdated:**
- `destroy` plugin hook — deprecated since 3.7.0, use `afterDestroy` (not needed here — charts are destroyed wholesale).
- The sgratzl `chartjs-plugin-error-bars` CDN script — RATIFIED FALLBACK ONLY; explicitly out of scope (no new CDN, D17-05/Out-of-Scope table).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The scatter's per-model `std` (models_comparison performance block) = mean of the model's per-task population stds (display-only propagation); mean/n_seeds trio at per-model level not duplicated (avg_raw already the mean) — RECOMMENDATION pending planner/maintainer ratification | Additive Data Architecture | If maintainer wants per-seed rank variance instead, scope grows materially (per-seed values must reach summarize; ranking-adjacent math) — flagged as the #1 planning question |
| A2 | Emission gate = "multi-seed data exists" interpreted as n_seeds ≥ 2 (population std well-defined at n=2; n_seeds disclosed in data) rather than aligning with CI_MIN_SEEDS=3 | WEB-01 | If maintainer prefers ≥3 (CI-consistency), bar/scatter whiskers appear on fewer cells; zero-drift logic identical either way |
| A3 | The trio attaches to the datasetEntry's PRIMARY metric only (dataset-declared metric, same one the leaderboard ranks on); other metrics in the dropdown show honest absence | WEB-02 | If per-metric std for ALL dropdown metrics is wanted, the schema shape becomes a per-metric map (bigger diff, n_seeds varies per metric) — shape decision, same mechanism |
| A4 | Committed r2-derived fixture inputs will be copied under `tests/fixtures/` (the `.planning/` archives and `/root/autodl-tmp/phase15-evidence/` are not CI-visible) | WEB-03 | If maintainer prefers generator-only (script computes values from constants seeded by r2 numbers), fixture layout differs; no behavioral risk |
| A5 | Whisker color/cap styling uses `--color-text-secondary` (#595F6E) matching-token hex in plugin defaults (existing chart-config precedent) | Code Examples | Cosmetic only; discretion item |

## Open Questions (RESOLVED — planner rulings: Q1 per-model scatter std = mean of per-task population stds + min-n, display-only, METHODOLOGY appendix — 17-01 Task 2; Q2 emission threshold n_seeds >= 2 — 17-01 emission gate; Q3 fixture generator at scripts/generate-errorbar-fixtures.js — 17-03 Task 1)

1. **Per-model scatter std semantics (the one genuine design ratification)**
   - What we know: the scatter plots per-model aggregates (y = `weighted_score`|`rank_score`, both ranking-derived); per-seed rank variance would need per-seed corpus re-ranking (forbidden territory); roadmap criterion 2 requires whiskers visible "verified against real sweep-derived artifacts" (the r2 export gives 2 models × 2 datasets × 3 seeds).
   - What's unclear: the exact one-sentence definition the maintainer will sign off in METHODOLOGY.
   - Recommendation: `std(model) = mean(per-task population std over tasks carrying std)`; tooltip line "Avg Raw: X ± Y"; whiskers drawn on y even though y is rank-derived (document that the whisker quantifies raw-score seed spread, display-only). Alternative: draw no y-whiskers until a corpus-wide multi-seed regeneration exists (plugin + tests still fully shippable this phase on fixtures) — but that weakens criterion 2's "verified against real sweep-derived artifacts" for the scatter leg.
2. **n threshold for emission (A2)** — recommend n ≥ 2 with n_seeds disclosed; confirm at plan gate.
3. **Where the fixture generator lives** (discretion) — recommend `scripts/generate-errorbar-fixtures.js` (CommonJS, `__dirname`-relative, the generate-tasks-index.js precedent) writing committed fixtures; tests read-only over them.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | JS test lane, `make data` generator line, `node --check` | ✓ | v26.4.0 local; CI pins 24 | — |
| uv + Python 3.13 (data group: numpy 2.5.3, pandas 2.3.3, scipy, jsonschema) | aggregation script changes + pytest lanes | ✓ | per uv.lock | — |
| Chart.js 4.4.0 CDN | both charts (unchanged) | ✓ | pinned jsDelivr UMD (bytes verified this session) | none needed — no new dependency |
| Real r2 sweep artifacts | fixture generation + render verification | ✓ | `pipeline/finetuned-sweep-r2/` (12 cells, 3 seeds each) + Phase 15 archives | e2_replay fixture (3-seed) if r2 tree is cleaned |
| Browser/dev server (`start-server.sh`) | manual scatter/bar verification | ✓ | python3 http.server | npx http-server |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

## Security Domain

ASVS L1 (config `security_enforcement: true`, `security_asvs_level: 1`, `security_block_on: high`).

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | static site, no auth surface |
| V3 Session Management | no | no sessions |
| V4 Access Control | no | static files only |
| V5 Input Validation | yes | JSON Schema strict contracts govern every consumed file; the new optional fields are schema-validated (`number`/`integer` types) and readers use defensive optional reads (`?.`, `typeof` checks) — never `parseInt` over untrusted strings; plugin guards non-finite/non-number std before drawing |
| V6 Cryptography | no | — |
| V12 File Upload | no | submit page out of scope this phase |

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed leaderboard JSON (missing/typed-wrong std) | Tampering | Schema validation at gate time + tolerant readers (absent/invalid ⇒ honest absence, no whisker — never a crash or fabricated bar) |
| XSS via interpolated values | Tampering | ±std lines are numbers rendered by Chart.js tooltip (canvas text, not innerHTML); no new innerHTML sites touch the new fields (FIX-04 discipline untouched) |
| CDN supply chain | Tampering | Pin unchanged (Chart.js 4.4.0 UMD); plugin is first-party vendored source in-repo, reviewed like any code — strictly narrower surface than adding a CDN script |

## Sources

### Primary (HIGH confidence)
- Live code read this session (all line-cited): `script/summarize_comparison.py`, `script/export_runs.py`, `dnallm-mark/js/{main,task,data,config}.js`, `schemas/{models,model_performance}.json`, `tests/{test_determinism,test_ci_replay,test_aggregation,test_export_runs,test_schemas,test_vendored_stats,test_golden}.py`, `tests/js/*.test.js`, `scripts/generate-tasks-index.js`, `Makefile`, `.github/workflows/ci.yml`, `docs/METHODOLOGY.md`, `pipeline/finetuned-sweep-r2/**/run_record.json`, Phase 15 archived JSONs, `/root/autodl-tmp/phase15-evidence/consumption-r2/seed_stats/*.json`
- Chart.js v4.4.0 tag sources (fetched verbatim): `docs/developers/plugins.md`, `src/controllers/controller.bar.js`
- The exact shipped artifact: `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js` (downloaded, grepped for `afterDatasetsDraw` / `getPixelForValue` / `getDatasetMeta` / linear+log `getPixelForValue` implementations)
- `.planning/research/ARCHITECTURE.md` §E (milestone research backbone — not re-derived)

### Secondary (MEDIUM confidence)
- [CITED: chartjs.org/docs/4.4.0/developers/plugins.html] — inline-plugin registration, plugin-id conventions, options scoping, destroy-deprecation (content-identical to the fetched v4.4.0 docs source)

### Tertiary (LOW confidence)
- None. sgratzl plugin internals deliberately NOT researched (ratified fallback only, out of scope).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — nothing new added; all pins verified live
- Architecture: HIGH — every integration point read with line numbers; the only MEDIUM-ish item is the per-model std semantics recommendation (A1, explicitly staged for ratification)
- Pitfalls: HIGH — ddof mismatch proven numerically on real artifacts; floating-bar parsed-value behavior verified in v4.4.0 source; strict-schema and byte-serialization contracts quoted verbatim

**Research date:** 2026-10-21
**Valid until:** 2026-11-21 (stable domain; Chart.js pin frozen by constraint, repo facts drift only via Phase 18 docs work)
