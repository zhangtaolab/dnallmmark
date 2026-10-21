#!/usr/bin/env node

/**
 * Generate tests/fixtures/errorbar/geometry-fixtures.json (Phase 17, WEB-03).
 *
 * Reads the REAL Phase-15 r2 multi-seed sweep tree
 * (pipeline/finetuned-sweep-r2: 2 models x 2 datasets x seeds 42/43/44 —
 * machine-local, gitignored) and derives the whisker-geometry test fixtures
 * the Node lane asserts against: per-cell mean / population std (ddof=0) /
 * n_seeds over the dataset's DECLARED primary metric, scale scenarios with
 * INLINE-computed expected pixels, and honest-absence expectations.
 *
 * INDEPENDENCE RULE (D17-09, non-negotiable): this generator never loads,
 * links, or references the module under test (dnallm-mark/js/error-bars.js)
 * in any executable form — every expected std and every expected pixel is
 * computed by the generator's OWN inline arithmetic (a ddof=0 population-std
 * recomputation, and the linear value→pixel formula mirroring the shipped
 * Chart.js 4.4.0 UMD getPixelForValue shape). A circular generator proves
 * nothing; the committed fixture's numbers must be derivable from the r2
 * per-seed values alone.
 *
 * DETERMINISM (the idempotence gate): no clock, no random, no environment
 * input beyond the r2 tree itself — the output serialization sorts every
 * object key and fixes the indent, so rerunning over an unchanged r2 tree
 * reproduces byte-identical fixture bytes. Regenerating over a future sweep
 * tree simply rewrites the fixture deterministically.
 *
 * LOUD REFUSAL (never fabricate): if the r2 root, any expected cell's
 * final_metrics.json, the declared metric row, or the per-seed
 * eval_{metric} value is missing or non-finite, the generator names every
 * missing path/key and exits non-zero — seed values are NEVER invented.
 */

const fs = require('fs');
const path = require('path');

// ===== Configuration =====
const REPO_ROOT = path.join(__dirname, '..');
const R2_ROOT = path.join(REPO_ROOT, 'pipeline', 'finetuned-sweep-r2');
const DATASETS_INFO_PATH = path.join(REPO_ROOT, 'pipeline', 'datasets_info.json');
const OUTPUT_FILE = path.join(REPO_ROOT, 'tests', 'fixtures', 'errorbar', 'geometry-fixtures.json');

// The real r2 matrix (2 models x 2 datasets x 3 seeds = 12 cells), sorted.
const R2_MODELS = ['plant-dnabert-6mer', 'plant-dnamamba-6mer'];
const R2_TASKS = ['GUE__emp_H3', 'iDNA_ABF_datasets__5mC'];
const R2_SEEDS = [42, 43, 44];

// Two fixture scale parameter sets. A linear fake mirroring the shipped UMD
// formula resolves a value as ((value - start) / range) * pixels — the same
// expression the Node lane's fake scale uses, so expected pixels are
// computed against identical arithmetic (never the module's function).
const SCALES = {
  scaleA: { start: 0.5, range: 0.3, pixels: 240 },
  scaleB: { start: 0.4, range: 0.5, pixels: 320 }
};

// Cap widths rotated across scenarios (capHalf = capWidth / 2).
const CAP_WIDTHS = [8, 14];

// Fixed anchor pixels (the constant-axis element position the plugin reads
// off the rendered chart element — deterministic literals, not measurements).
const POINT_ANCHORS = [96, 160, 224, 288];
const BAR_ANCHORS = [40, 62, 84, 106];

/**
 * Recursively return the value with every object key sorted (deterministic
 * serialization — regeneration over unchanged inputs is byte-identical).
 * @param {*} value - Any JSON value.
 * @returns {*} The same value with plain-object keys in sorted order.
 */
function sortKeysRecursive(value) {
  if (Array.isArray(value)) {
    return value.map(sortKeysRecursive);
  }
  if (value && typeof value === 'object') {
    const out = {};
    for (const key of Object.keys(value).sort()) {
      out[key] = sortKeysRecursive(value[key]);
    }
    return out;
  }
  return value;
}

/**
 * Mean and ddof=0 population std via the generator's OWN inline arithmetic
 * (sqrt of the mean squared deviation — the D17-01 display convention; NEVER
 * the vendored ddof=1 sd, never the module under test's functions).
 * @param {number[]} values - Finite per-seed values, sorted by seed.
 * @returns {{mean: number, std: number}} Population statistics.
 */
function populationStatsInline(values) {
  const n = values.length;
  let sum = 0;
  for (const v of values) sum += v;
  const mean = sum / n;
  let squaredDeviations = 0;
  for (const v of values) squaredDeviations += (v - mean) * (v - mean);
  return { mean, std: Math.sqrt(squaredDeviations / n) };
}

/**
 * The linear value→pixel formula the shipped Chart.js 4.4.0 UMD implements
 * (getPixelForValue → getPixelForDecimal((t - _startValue) / _valueRange)),
 * computed inline so the fixture's expected pixels never touch the module
 * under test.
 * @param {number} value - A whisker endpoint VALUE.
 * @param {{start: number, range: number, pixels: number}} scale - Linear
 *   fake-scale parameters.
 * @returns {number} The expected pixel.
 */
function linearPixelInline(value, scale) {
  return ((value - scale.start) / scale.range) * scale.pixels;
}

/**
 * Resolve the final_metrics key candidates for a task's DECLARED primary
 * metric (datasets_info.json metric field, e.g. 'f1' → ['eval_f1', ...];
 * case variants cover AUPRC-style declarations whose final_metrics
 * spellings differ). The first candidate PRESENT in the run's
 * final_metrics.json wins, uniformly across seeds.
 * @param {Object} datasetsInfo - The parsed registry (task key → row).
 * @param {string} task - The r2 task key.
 * @returns {string[]} Lookup-ordered final_metrics key candidates.
 */
function resolveMetricKeyCandidates(datasetsInfo, task) {
  const row = datasetsInfo[task];
  if (!row || typeof row.metric !== 'string' || row.metric.length === 0) {
    const detail = row ? `metric field missing on '${task}'` : `dataset row '${task}' absent`;
    console.error(`✗ ${DATASETS_INFO_PATH}: ${detail}`);
    process.exit(1);
  }
  const metric = row.metric;
  return [`eval_${metric}`, `eval_${metric.toUpperCase()}`, `eval_${metric.toLowerCase()}`];
}

/**
 * Collect one r2 cell: the per-seed primary-metric values (sorted seeds),
 * plus the generator's own mean / ddof=0 std / n_seeds. Refuses loudly on
 * any missing file, missing metric key, or non-finite value.
 * @param {string} model - Model directory name.
 * @param {string} task - Task directory name.
 * @param {string[]} metricCandidates - Lookup-ordered final_metrics keys.
 * @returns {{per_seed: Object, metric_key: string, mean: number,
 *   std: number, n_seeds: number}} The provenance record for the cell.
 */
function collectCell(model, task, metricCandidates) {
  const perSeed = {};
  const missing = [];
  let metricKey = null;
  for (const seed of R2_SEEDS) {
    const metricsPath = path.join(R2_ROOT, model, task, `seed_${seed}`, 'final_metrics.json');
    if (!fs.existsSync(metricsPath)) {
      missing.push(metricsPath);
      continue;
    }
    const doc = JSON.parse(fs.readFileSync(metricsPath, 'utf8'));
    const key = metricCandidates.find((candidate) => candidate in doc);
    if (!key) {
      missing.push(`${metricsPath}#${metricCandidates[0]}`);
      continue;
    }
    const value = doc[key];
    if (typeof value !== 'number' || !isFinite(value)) {
      missing.push(`${metricsPath}#${key} (non-finite: ${String(value)})`);
      continue;
    }
    if (metricKey === null) {
      metricKey = key;
    } else if (metricKey !== key) {
      missing.push(`${metricsPath}#${key} (spells differently than seed-resolved ${metricKey})`);
      continue;
    }
    perSeed[String(seed)] = value;
  }
  if (missing.length > 0) {
    console.error(`✗ Refusing to fabricate seed values — missing/non-finite inputs for ${model}/${task}:`);
    for (const entry of missing) console.error(`  - ${entry}`);
    process.exit(1);
  }
  const values = R2_SEEDS.map((seed) => perSeed[String(seed)]);
  const stats = populationStatsInline(values);
  return {
    per_seed: perSeed,
    metric_key: metricKey,
    mean: stats.mean,
    std: stats.std,
    n_seeds: values.length
  };
}

/**
 * Build the geometry scenario pair for one cell (point mode + bar mode),
 * each paired with a different scale/capWidth so both fixture scale sets
 * are exercised in both modes across the 4 cells. Expected endpoint pixels
 * and capHalf are computed inline (linearPixelInline / capWidth / 2).
 * @param {number} idx - The cell index (0..3), driving the rotation.
 * @param {{model: string, task: string, mean: number, std: number}} cell -
 *   The cell record.
 * @returns {Object[]} The two scenario objects.
 */
function buildScenarios(idx, cell) {
  const loValue = cell.mean - cell.std;
  const hiValue = cell.mean + cell.std;
  const pointScaleName = idx % 2 === 0 ? 'scaleA' : 'scaleB';
  const barScaleName = idx % 2 === 0 ? 'scaleB' : 'scaleA';
  const pointCapWidth = CAP_WIDTHS[idx % CAP_WIDTHS.length];
  const barCapWidth = CAP_WIDTHS[(idx + 1) % CAP_WIDTHS.length];
  const cellRef = `${cell.model}/${cell.task}`;

  const expectedFor = (scaleName, capWidth) => {
    const scale = SCALES[scaleName];
    return {
      lo: linearPixelInline(loValue, scale),
      hi: linearPixelInline(hiValue, scale),
      capHalf: capWidth / 2
    };
  };

  return [
    {
      name: `point-${cellRef}`,
      mode: 'point',
      cell: cellRef,
      scale: pointScaleName,
      anchor: POINT_ANCHORS[idx % POINT_ANCHORS.length],
      capWidth: pointCapWidth,
      loValue,
      hiValue,
      expected: expectedFor(pointScaleName, pointCapWidth)
    },
    {
      name: `bar-${cellRef}`,
      mode: 'bar',
      cell: cellRef,
      scale: barScaleName,
      anchor: BAR_ANCHORS[idx % BAR_ANCHORS.length],
      capWidth: barCapWidth,
      loValue,
      hiValue,
      expected: expectedFor(barScaleName, barCapWidth)
    }
  ];
}

function main() {
  console.log('Generating error-bar geometry fixtures (Phase 17, WEB-03)...');

  if (!fs.existsSync(R2_ROOT)) {
    console.error(`✗ Refusing to fabricate seed values — r2 sweep root is absent: ${R2_ROOT}`);
    console.error('  (The r2 tree is machine-local, gitignored data; regenerate it on the sweep machine.)');
    process.exit(1);
  }
  if (!fs.existsSync(DATASETS_INFO_PATH)) {
    console.error(`✗ Dataset registry absent: ${DATASETS_INFO_PATH}`);
    process.exit(1);
  }
  const datasetsInfo = JSON.parse(fs.readFileSync(DATASETS_INFO_PATH, 'utf8'));

  // Cells: the full 2x2 matrix, deterministic (sorted) order.
  const cells = [];
  for (const model of R2_MODELS) {
    for (const task of R2_TASKS) {
      const candidates = resolveMetricKeyCandidates(datasetsInfo, task);
      cells.push({ model, task, ...collectCell(model, task, candidates) });
    }
  }
  console.log(`Collected ${cells.length} cells x ${R2_SEEDS.length} seeds from the real r2 tree`);

  // Geometry scenarios: one point-mode + one bar-mode scenario per cell.
  const scenarios = [];
  cells.forEach((cell, idx) => {
    scenarios.push(...buildScenarios(idx, cell));
  });

  // Honest-absence expectations (D17-08): std 0 / absent / negative must map
  // to the scalar bar datum — no zero-width fake whiskers. (NaN and undefined
  // are JSON-unrepresentable / absent-key cases; the test lane feeds them as
  // in-test literals.)
  const honestAbsence = [
    { name: 'std-zero', metricValue: 0.75, std: 0, expectScalar: 0.75 },
    { name: 'std-absent-null', metricValue: 0.6, std: null, expectScalar: 0.6 },
    { name: 'std-negative', metricValue: 0.42, std: -0.05, expectScalar: 0.42 }
  ];

  const fixture = {
    provenance: {
      description: 'Whisker-geometry fixture derived from the real Phase-15 r2 multi-seed sweep; stds are ddof=0 population stds recomputed by the generator\'s own inline arithmetic.',
      source_root: 'pipeline/finetuned-sweep-r2',
      generator: 'scripts/generate-errorbar-fixtures.js',
      std_convention: 'population std (ddof=0) over completed seeds of the dataset-declared primary metric',
      seeds: R2_SEEDS,
      cells
    },
    scales: SCALES,
    scenarios,
    honestAbsence
  };

  const serialized = `${JSON.stringify(sortKeysRecursive(fixture), null, 2)}\n`;
  fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
  fs.writeFileSync(OUTPUT_FILE, serialized);

  console.log(`✓ Generated ${OUTPUT_FILE}`);
  console.log(`  ${cells.length} provenance cells, ${scenarios.length} geometry scenarios, ${honestAbsence.length} honest-absence cases`);
  for (const cell of cells) {
    console.log(`  - ${cell.model}/${cell.task} [${cell.metric_key}] mean=${cell.mean.toFixed(6)} std=${cell.std.toFixed(6)} n=${cell.n_seeds}`);
  }
}

main();
