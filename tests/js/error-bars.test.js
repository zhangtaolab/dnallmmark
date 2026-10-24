#!/usr/bin/env node
/**
 * Phase 17, WEB-03 (D17-09/D17-10): the error-bar Node lane.
 *
 * What this file PROVES, per test group:
 *
 *  1. GEOMETRY — the browser's whisker math (whiskerGeometry in
 *     dnallm-mark/js/error-bars.js) is a pure function: for every scenario
 *     in the GENERATED fixture (tests/fixtures/errorbar/
 *     geometry-fixtures.json, produced by scripts/generate-errorbar-fixtures.js
 *     over the REAL Phase-15 r2 multi-seed sweep tree) the module's endpoint
 *     pixels through an injected fake linear scale equal the fixture's
 *     independently inline-computed expectations (tolerance 1e-9).
 *  2. REAL-VALUE RECOMPUTATION — for every provenance cell the ddof=0
 *     population std is recomputed HERE from the recorded per-seed values;
 *     a drifted or hand-edited fixture fails this tripwire.
 *  3. PLUGIN SHAPE — the default export is the inline plugin with a
 *     lowercase id, carrying defaults and afterDatasetsDraw, and the module
 *     namespace exposes exactly the expected exports (no Chart/canvas/DOM
 *     reference — the purity seam WEB-03 tests through).
 *  3b. DRAW DISPATCH — afterDatasetsDraw executed against mock bar charts
 *      (recording ctx fake): a VERTICAL bar (indexAxis 'x') anchors on
 *      el.x, strokes vertically, and clamps into [chartArea.top,
 *      chartArea.bottom]; a HORIZONTAL bar (indexAxis 'y') keeps the el.y
 *      anchor and horizontal strokes (the WR-01 orientation pair).
 *  4. HONEST ABSENCE — barDatum returns the scalar for std 0 / undefined /
 *     null / NaN / negative and the [lo, hi] floating-bar pair only for a
 *     finite std > 0 (D17-08: never a zero-width fake whisker).
 *  5. ADDITIVE SCHEMA FIELDS — the three strict schemas gained the optional
 *     display trio in properties ONLY; the required arrays are unchanged
 *     and every closed level stays additionalProperties:false (D17-04).
 *  6. COMMITTED-DATA ABSENCE — the committed public data tree carries no
 *     std/n_seeds anywhere (single-run until the maintainer regenerates —
 *     D17-02's data-side honesty; that absence IS the assertion).
 *  7. PUBLIC-VIEW TOOLTIP QUALIFICATION (WR-02) — the main.js scatter
 *     tooltip line is source-pinned to the self-qualifying
 *     "Raw-score seed spread: ±..." label; the unqualified
 *     "Seed spread: ±" must not survive on the public view.
 *
 * The fixture is read READ-ONLY everywhere (generated, never hand-written).
 */

const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const errorBars = require('../../dnallm-mark/js/error-bars.js');
const whiskerGeometry = errorBars.whiskerGeometry;
const barDatum = errorBars.barDatum;
const plugin = errorBars.default;

const FIXTURE_PATH = path.join(__dirname, '..', 'fixtures', 'errorbar', 'geometry-fixtures.json');
const SCHEMA_DIR = path.join(__dirname, '..', '..', 'schemas');
const DATA_DIR = path.join(__dirname, '..', '..', 'dnallm-mark', 'data');

const fixture = JSON.parse(fs.readFileSync(FIXTURE_PATH, 'utf8'));

/** Build the fake linear scale from a fixture scale parameter set — the
 * same expression shape the shipped Chart.js 4.4.0 UMD implements
 * (getPixelForValue -> getPixelForDecimal((t - start) / range)). */
function fakeLinearScale(scale) {
  return {
    getPixelForValue: (v) => ((v - scale.start) / scale.range) * scale.pixels
  };
}

/** ddof=0 population std recomputed IN-TEST (the anti-drift tripwire — the
 * same arithmetic the generator uses, arrived at independently here). */
function populationStd(values) {
  const n = values.length;
  let sum = 0;
  for (const v of values) sum += v;
  const mean = sum / n;
  let ss = 0;
  for (const v of values) ss += (v - mean) * (v - mean);
  return Math.sqrt(ss / n);
}

// ===== 1. GEOMETRY: whiskerGeometry vs the generated fixtures =====

test('whiskerGeometry matches every generated fixture scenario through the injected fake scale', () => {
  assert.ok(fixture.scenarios.length >= 8, 'fixture carries the 4 cells x point/bar scenarios');
  for (const scenario of fixture.scenarios) {
    const scale = fixture.scales[scenario.scale];
    assert.ok(scale, `scenario ${scenario.name} references a known scale`);
    const g = whiskerGeometry(
      scenario.anchor, scenario.loValue, scenario.hiValue,
      fakeLinearScale(scale), scenario.capWidth
    );
    assert.ok(Math.abs(g.anchor - scenario.anchor) <= 1e-9, `${scenario.name}: anchor`);
    assert.ok(Math.abs(g.lo - scenario.expected.lo) <= 1e-9, `${scenario.name}: lo pixel`);
    assert.ok(Math.abs(g.hi - scenario.expected.hi) <= 1e-9, `${scenario.name}: hi pixel`);
    assert.ok(Math.abs(g.capHalf - scenario.expected.capHalf) <= 1e-9, `${scenario.name}: capHalf`);
  }
});

test('both fixture scale parameter sets are exercised in both point and bar modes', () => {
  for (const scaleName of Object.keys(fixture.scales)) {
    for (const mode of ['point', 'bar']) {
      const hits = fixture.scenarios.filter((s) => s.scale === scaleName && s.mode === mode);
      assert.ok(hits.length >= 1, `scale ${scaleName} exercised in ${mode} mode`);
    }
  }
});

// ===== 2. REAL-VALUE RECOMPUTATION: the fixture-drift tripwire =====

test('every provenance cell std equals the in-test ddof=0 recomputation over its per-seed values', () => {
  const cells = fixture.provenance.cells;
  assert.strictEqual(cells.length, 4, 'the real r2 matrix: 2 models x 2 tasks');
  for (const cell of cells) {
    const seeds = Object.keys(cell.per_seed);
    assert.strictEqual(seeds.length, 3, `${cell.model}/${cell.task}: 3 seeds recorded`);
    const values = seeds.map((s) => cell.per_seed[s]);
    for (const v of values) {
      assert.ok(typeof v === 'number' && isFinite(v), `${cell.model}/${cell.task}: finite per-seed value`);
    }
    const recomputedStd = populationStd(values);
    assert.ok(
      Math.abs(recomputedStd - cell.std) <= 1e-12,
      `${cell.model}/${cell.task}: recorded std ${cell.std} vs recomputed ${recomputedStd}`
    );
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    assert.ok(Math.abs(mean - cell.mean) <= 1e-12, `${cell.model}/${cell.task}: recorded mean`);
    assert.strictEqual(cell.n_seeds, 3, `${cell.model}/${cell.task}: n_seeds`);
  }
});

// ===== 3. PLUGIN SHAPE: the inline plugin + the exact export surface =====

test('default export is the inline plugin: lowercase id, defaults, afterDatasetsDraw', () => {
  assert.strictEqual(plugin.id, 'errorbars');
  assert.doesNotMatch(plugin.id, /[A-Z]/, 'plugin id follows the npm-name rule');
  assert.strictEqual(typeof plugin.afterDatasetsDraw, 'function');
  assert.strictEqual(typeof plugin.defaults.color, 'string');
  assert.strictEqual(typeof plugin.defaults.lineWidth, 'number');
  assert.strictEqual(typeof plugin.defaults.capWidth, 'number');
  assert.strictEqual(typeof plugin.defaults.drawStem, 'boolean');
});

test('module namespace exposes exactly the expected exports (the purity seam)', () => {
  const exports = Object.keys(errorBars).filter((k) => k !== '__esModule').sort();
  assert.deepStrictEqual(exports, ['barDatum', 'default', 'whiskerGeometry']);
  assert.strictEqual(typeof whiskerGeometry, 'function');
  assert.strictEqual(typeof barDatum, 'function');
});

test('module source references no DOM/canvas access primitive', () => {
  const source = fs.readFileSync(
    path.join(__dirname, '..', '..', 'dnallm-mark', 'js', 'error-bars.js'), 'utf8'
  );
  assert.doesNotMatch(source, /window\./, 'no window access');
  assert.doesNotMatch(source, /document\./, 'no document access');
  assert.doesNotMatch(source, /getContext/, 'no canvas context acquisition');
});

// ===== 3b. DRAW DISPATCH: orientation-correct bar-cap strokes (WR-01) =====

/** Recording 2D-context fake — captures the plugin's path commands in
 * call order so the ORIENTATION of every stroke (which coordinate pair
 * it spans) can be asserted exactly. */
function fakeCtx(calls) {
  return {
    save() { calls.push(['save']); },
    restore() { calls.push(['restore']); },
    beginPath() { calls.push(['beginPath']); },
    moveTo(x, y) { calls.push(['moveTo', x, y]); },
    lineTo(x, y) { calls.push(['lineTo', x, y]); },
    stroke() { calls.push(['stroke']); }
  };
}

/** Minimal bar-chart double: one visible dataset, one element, a linear
 * value scale mapping value*200 to pixels (0.25 -> 50, 0.75 -> 150), and
 * chartArea bounds chosen so the two clamp axis pairs are DISTINGUISHABLE
 * (left 10 / right 390 vs top 0 / bottom 300). */
function mockBarChart(ctx, indexAxis, valueScale, el) {
  return {
    ctx,
    chartArea: { left: 10, top: 0, right: 390, bottom: 300 },
    options: { indexAxis },
    scales: { [indexAxis === 'y' ? 'x' : 'y']: valueScale },
    data: { datasets: [{ data: [[0.25, 0.75]] }] },
    getDatasetMeta: () => ({ hidden: false, data: [el] })
  };
}

const DRAW_OPTIONS = { color: '#595F6E', lineWidth: 1, capWidth: 8, drawStem: true };

test('afterDatasetsDraw: vertical bars anchor on el.x and stroke vertically (WR-01 regression)', () => {
  const calls = [];
  const chart = mockBarChart(
    fakeCtx(calls), 'x', { getPixelForValue: (v) => v * 200 }, { x: 100, y: 90 }
  );
  plugin.afterDatasetsDraw(chart, {}, DRAW_OPTIONS);
  // The whisker is a VERTICAL stem at the bar's x with caps spanning the
  // category axis — never horizontal strokes anchored on el.y (the
  // pre-fix geometry the reviewer reproduced).
  assert.deepStrictEqual(calls, [
    ['save'],
    ['beginPath'],
    ['moveTo', 100, 50], ['lineTo', 100, 150],
    ['moveTo', 96, 50], ['lineTo', 104, 50],
    ['moveTo', 96, 150], ['lineTo', 104, 150],
    ['stroke'],
    ['restore']
  ]);
});

test('afterDatasetsDraw: vertical bars clamp endpoints into [chartArea.top, chartArea.bottom]', () => {
  const calls = [];
  const chart = mockBarChart(
    fakeCtx(calls), 'x', { getPixelForValue: (v) => v * 200 }, { x: 100, y: 90 }
  );
  // 2.0 maps to pixel 400 — beyond bottom (300); the pre-fix hardcoded
  // [chartArea.left, chartArea.right] pair would clamp to 390 instead.
  chart.data.datasets[0].data = [[0.25, 2.0]];
  plugin.afterDatasetsDraw(chart, {}, DRAW_OPTIONS);
  assert.deepStrictEqual(calls, [
    ['save'],
    ['beginPath'],
    ['moveTo', 100, 50], ['lineTo', 100, 300],
    ['moveTo', 96, 50], ['lineTo', 104, 50],
    ['moveTo', 96, 300], ['lineTo', 104, 300],
    ['stroke'],
    ['restore']
  ]);
});

test('afterDatasetsDraw: horizontal bars keep the el.y anchor and horizontal strokes', () => {
  const calls = [];
  const chart = mockBarChart(
    fakeCtx(calls), 'y', { getPixelForValue: (v) => v * 200 }, { x: 90, y: 100 }
  );
  plugin.afterDatasetsDraw(chart, {}, DRAW_OPTIONS);
  assert.deepStrictEqual(calls, [
    ['save'],
    ['beginPath'],
    ['moveTo', 50, 100], ['lineTo', 150, 100],
    ['moveTo', 50, 96], ['lineTo', 50, 104],
    ['moveTo', 150, 96], ['lineTo', 150, 104],
    ['stroke'],
    ['restore']
  ]);
});

// ===== 4. HONEST ABSENCE: barDatum scalar/array mapping (D17-08) =====

test('barDatum returns the scalar for std 0, undefined, null, NaN and negative', () => {
  assert.strictEqual(barDatum(0.75, 0), 0.75);
  assert.strictEqual(barDatum(0.75, undefined), 0.75);
  assert.strictEqual(barDatum(0.75, null), 0.75);
  assert.strictEqual(barDatum(0.75, NaN), 0.75);
  assert.strictEqual(barDatum(0.42, -0.05), 0.42);
});

test('barDatum returns the [lo, hi] floating-bar pair only for finite std > 0', () => {
  assert.deepStrictEqual(barDatum(5, 2), [3, 7]);
  assert.deepStrictEqual(barDatum(0.5952380952380952, 0.0890870806356652), [
    0.5952380952380952 - 0.0890870806356652,
    0.5952380952380952 + 0.0890870806356652
  ]);
});

test('fixture honest-absence cases pin the scalar expectation', () => {
  for (const item of fixture.honestAbsence) {
    assert.strictEqual(barDatum(item.metricValue, item.std), item.expectScalar, item.name);
  }
});

// ===== 5. ADDITIVE SCHEMA FIELDS (D17-04) =====

/** Assert every subschema that declares `properties` is closed
 * (additionalProperties === false), recursively through $defs. */
function assertStrictAtEveryClosedLevel(node, where) {
  if (Array.isArray(node)) {
    node.forEach((child, i) => assertStrictAtEveryClosedLevel(child, `${where}[${i}]`));
    return;
  }
  if (!node || typeof node !== 'object') return;
  if ('properties' in node) {
    assert.strictEqual(
      node.additionalProperties, false,
      `${where}: closed level must keep additionalProperties:false`
    );
  }
  for (const [key, child] of Object.entries(node)) {
    assertStrictAtEveryClosedLevel(child, `${where}.${key}`);
  }
}

test('task_performance schema: modelEntry trio optional, required unchanged, strict everywhere', () => {
  const schema = JSON.parse(fs.readFileSync(path.join(SCHEMA_DIR, 'task_performance.json'), 'utf8'));
  const modelEntry = schema.$defs.modelEntry;
  for (const field of ['mean', 'std', 'n_seeds']) {
    assert.ok(field in modelEntry.properties, `modelEntry properties gained ${field}`);
    assert.ok(!modelEntry.required.includes(field), `${field} stays optional`);
  }
  assert.deepStrictEqual([...modelEntry.required].sort(), ['model', 'parameters', 'performance']);
  assertStrictAtEveryClosedLevel(schema, 'task_performance');
});

test('model_performance schema: datasetEntry trio optional, required unchanged, strict everywhere', () => {
  const schema = JSON.parse(fs.readFileSync(path.join(SCHEMA_DIR, 'model_performance.json'), 'utf8'));
  const datasetEntry = schema.$defs.datasetEntry;
  for (const field of ['mean', 'std', 'n_seeds']) {
    assert.ok(field in datasetEntry.properties, `datasetEntry properties gained ${field}`);
    assert.ok(!datasetEntry.required.includes(field), `${field} stays optional`);
  }
  assert.deepStrictEqual([...datasetEntry.required].sort(), ['dataset', 'parameters', 'performance']);
  assertStrictAtEveryClosedLevel(schema, 'model_performance');
});

test('models_comparison schema: performance std/n_seeds optional, 16-key required unchanged', () => {
  const schema = JSON.parse(fs.readFileSync(path.join(SCHEMA_DIR, 'models_comparison.json'), 'utf8'));
  const perf = schema.$defs.modelComparison.properties.performance;
  for (const field of ['std', 'n_seeds']) {
    assert.ok(field in perf.properties, `comparison performance properties gained ${field}`);
    assert.ok(!perf.required.includes(field), `${field} stays optional`);
  }
  assert.deepStrictEqual([...perf.required].sort(), [
    'avg_PFLOPs', 'avg_rank', 'avg_raw', 'rank', 'rank_score', 'samples',
    'sum_PFLOPs', 'sum_minmax', 'sum_robust', 'sum_zscore', 'top10_count',
    'top1_count', 'top3_count', 'top5_count', 'top8_count', 'weighted_score'
  ]);
  assert.strictEqual(perf.required.length, 16, 'the F6 16-key required list is unchanged');
  assertStrictAtEveryClosedLevel(schema, 'models_comparison');
});

// ===== 6. COMMITTED-DATA ABSENCE (D17-02 data-side honesty) =====

test('committed comparison files carry no std/n_seeds (single-run tree until regeneration)', () => {
  const files = [
    'models_comparison.json',
    'models_comparison_animal.json',
    'models_comparison_plant.json',
    'models_comparison_microbe.json'
  ];
  for (const file of files) {
    const doc = JSON.parse(fs.readFileSync(path.join(DATA_DIR, file), 'utf8'));
    for (const [alias, entry] of Object.entries(doc)) {
      assert.ok(!('std' in entry.performance), `${file}:${alias} carries no std`);
      assert.ok(!('n_seeds' in entry.performance), `${file}:${alias} carries no n_seeds`);
    }
  }
});

test('a committed task_performance file carries no modelEntry trio keys', () => {
  const taskDir = path.join(DATA_DIR, 'task_performance');
  const firstFile = fs.readdirSync(taskDir)
    .filter((f) => f.endsWith('_task_performance.json'))
    .sort()[0];
  assert.ok(firstFile, 'a committed task file exists');
  const doc = JSON.parse(fs.readFileSync(path.join(taskDir, firstFile), 'utf8'));
  for (const [alias, entry] of Object.entries(doc.performance)) {
    for (const field of ['mean', 'std', 'n_seeds']) {
      assert.ok(!(field in entry), `${firstFile}:${alias} carries no ${field}`);
    }
  }
});

// ===== 7. PUBLIC-VIEW TOOLTIP QUALIFICATION (WR-02) =====

test('main.js scatter tooltip qualifies the whisker line as raw-score seed spread', () => {
  const source = fs.readFileSync(
    path.join(__dirname, '..', '..', 'dnallm-mark', 'js', 'main.js'), 'utf8'
  );
  // The scatter whisker is a raw-metric spread drawn around the displayed
  // weighted/rank score — the tooltip line must say so (WR-02), with the
  // conditional (n=N) suffix shape intact.
  assert.match(
    source,
    /Raw-score seed spread: ±\$\{p\.std\.toFixed\(4\)\}/,
    'the self-qualifying label with the p.std payload'
  );
  assert.match(
    source,
    /\(n=' \+ p\.n_seeds \+ '\)/,
    'the existing n_seeds count suffix stays disclosed'
  );
  assert.doesNotMatch(
    source,
    /Seed spread: ±/,
    'the unqualified "Seed spread" label must not survive on the public view'
  );
});
