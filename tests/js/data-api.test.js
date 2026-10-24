#!/usr/bin/env node
/**
 * Behavior tests for the DataAPI module surface (dnallm-mark/js/data.js,
 * node:test, zero npm deps) — the DATA-07 removal proof:
 *
 *  - the default export still loads under Node (require(esm) namespace
 *    `.default`, the data-escape.test.js pattern), and
 *  - the module still memoizes: a doubled fetch called twice returns the
 *    cached instance and the network is hit only once, and
 *  - the exported object no longer carries `recalculateComparison` — the
 *    dead divergent client-side aggregation logic was removed (its only
 *    legitimate successor lives offline in
 *    script/summarize_comparison.py; the leaderboard never recomputes).
 */

const { test } = require('node:test');
const assert = require('node:assert');

const DataAPI = require('../../dnallm-mark/js/data.js').default;

test('DataAPI default export loads as an object with its cache surface', () => {
  assert.strictEqual(typeof DataAPI, 'object');
  assert.notStrictEqual(DataAPI, null);
  assert.strictEqual(typeof DataAPI.cache, 'object');
  assert.strictEqual(typeof DataAPI.loadModelsComparison, 'function');
  assert.strictEqual(typeof DataAPI.loadModelPerformance, 'function');
  assert.strictEqual(typeof DataAPI.escapeHTML, 'function');
});

test('DataAPI memoizes a fetch: a doubled fetch called twice hits the network once', async () => {
  const payload = { stamped: 'data-v1.1.0' };
  let fetchCalls = 0;

  // A doubled fetch: counts invocations, returns a Response-shaped object.
  globalThis.fetch = async () => {
    fetchCalls += 1;
    return { ok: true, json: async () => payload };
  };

  // Fresh module state would be ideal, but the cache is module-level by
  // design; clear the slot this test exercises instead (the same discipline
  // window.DNALLMDebug.clearCache() exposes in the browser).
  DataAPI.cache.modelsComparison = null;

  const first = await DataAPI.loadModelsComparison();
  const second = await DataAPI.loadModelsComparison();

  assert.strictEqual(fetchCalls, 1, 'fetch must be invoked exactly once');
  assert.strictEqual(first, payload, 'first call resolves the fetched payload');
  assert.strictEqual(
    second,
    first,
    'second call returns the cached instance, not a refetch',
  );
  assert.strictEqual(
    DataAPI.cache.modelsComparison,
    payload,
    'the cache slot holds the fetched payload',
  );

  delete globalThis.fetch;
});

test('DataAPI no longer exports recalculateComparison (dead logic removed, DATA-07)', () => {
  assert.strictEqual(
    Object.prototype.hasOwnProperty.call(DataAPI, 'recalculateComparison'),
    false,
    'the exported DataAPI object must not carry a recalculateComparison property',
  );
  assert.strictEqual(DataAPI.recalculateComparison, undefined);
});
