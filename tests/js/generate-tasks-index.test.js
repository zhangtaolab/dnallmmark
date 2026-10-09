#!/usr/bin/env node
/**
 * Unit tests for scripts/generate-tasks-index.js (node:test, zero npm deps).
 *
 * The generator is CommonJS, runs generateTaskIndex() unconditionally at
 * module load, and resolves TASK_PERFORMANCE_DIR / OUTPUT_FILE relative to
 * __dirname — it cannot be CWD-redirected or imported without side effects.
 * The verified zero-production-change mechanism (Phase 2 research, Pattern 4)
 * is to copy the script into an OS-tmp fixture tree:
 *
 *   <tmp>/inner/gen.js                       (the copied generator)
 *   <tmp>/dnallm-mark/data/task_performance/ (fixture task files)
 *   <tmp>/dnallm-mark/data/tasks.json        (asserted output)
 *
 * IN-02 (raw readdirSync crash when task_performance/ is missing) is milestone
 * backlog per D-05 and deliberately NOT covered here.
 */

const { test } = require('node:test');
const assert = require('node:assert');
const { execFileSync, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const GENERATOR = path.join(__dirname, '..', '..', 'scripts', 'generate-tasks-index.js');

/** Build the isolated fixture tree and copy the generator into it. */
function buildTree() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dnallmmark-js-'));
  fs.mkdirSync(path.join(tmp, 'inner'));
  fs.mkdirSync(path.join(tmp, 'dnallm-mark', 'data', 'task_performance'), { recursive: true });
  fs.copyFileSync(GENERATOR, path.join(tmp, 'inner', 'gen.js'));
  return tmp;
}

function writeTask(tmp, file, doc) {
  fs.writeFileSync(
    path.join(tmp, 'dnallm-mark', 'data', 'task_performance', file),
    JSON.stringify(doc),
  );
}

function runGenerator(tmp) {
  return execFileSync(process.execPath, [path.join(tmp, 'inner', 'gen.js')], {
    encoding: 'utf8',
  });
}

function readIndex(tmp) {
  return JSON.parse(
    fs.readFileSync(path.join(tmp, 'dnallm-mark', 'data', 'tasks.json'), 'utf8'),
  );
}

test('index projects task files with displayName collapse and defensive fallbacks', () => {
  const tmp = buildTree();
  try {
    writeTask(tmp, 'Fake__one_task_performance.json', {
      info: { species: 'Microbe', type: 'binary', labels: 2, length: 500, metric: 'f1' },
    });
    // Second fixture: info block missing the species field -> 'Unknown' fallback.
    writeTask(tmp, 'Fake__two_task_performance.json', {
      info: { type: 'regression', labels: 1, length: 1000, metric: 'spearmanr' },
    });

    runGenerator(tmp);
    const index = readIndex(tmp);

    assert.strictEqual(index.version, '1.0.0');
    assert.strictEqual(index.count, 2);
    assert.strictEqual(index.tasks.length, 2);

    const one = index.tasks.find((t) => t.id === 'Fake__one');
    assert.ok(one, 'Fake__one indexed');
    // Underscore runs collapse to single spaces: Fake__one -> "Fake one".
    assert.strictEqual(one.displayName, 'Fake one');
    assert.strictEqual(one.name, 'Fake__one');
    assert.strictEqual(one.species, 'Microbe');
    assert.strictEqual(one.type, 'binary');
    assert.strictEqual(one.labels, 2);
    assert.strictEqual(one.length, 500);
    assert.strictEqual(one.metric, 'f1');
    assert.strictEqual(one.fileName, 'Fake__one_task_performance.json');

    const two = index.tasks.find((t) => t.id === 'Fake__two');
    assert.ok(two, 'Fake__two indexed');
    assert.strictEqual(two.displayName, 'Fake two');
    assert.strictEqual(two.species, 'Unknown'); // defensive projection fallback
    assert.strictEqual(two.type, 'regression');
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test('malformed JSON logs [Skip] and valid files are still indexed', () => {
  const tmp = buildTree();
  try {
    writeTask(tmp, 'Good__task_task_performance.json', {
      info: { species: 'Plants', type: 'binary', labels: 2, length: 500, metric: 'f1' },
    });
    fs.writeFileSync(
      path.join(tmp, 'dnallm-mark', 'data', 'task_performance', 'Bad__task_task_performance.json'),
      '{ not valid json !!',
    );

    const result = spawnSync(process.execPath, [path.join(tmp, 'inner', 'gen.js')], {
      encoding: 'utf8',
    });
    assert.strictEqual(result.status, 0, result.stderr);
    // The per-file [Skip] line goes to stderr via console.warn.
    assert.match(result.stderr, /\[Skip\] Failed to read file Bad__task_task_performance\.json/);

    const index = readIndex(tmp);
    assert.strictEqual(index.count, 1); // only the valid file is indexed
    assert.strictEqual(index.tasks[0].id, 'Good__task');
    assert.strictEqual(index.tasks[0].species, 'Plants');
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});
