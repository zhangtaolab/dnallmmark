#!/usr/bin/env node
/**
 * Unit tests for the DataAPI.escapeHTML helper (dnallm-mark/js/data.js,
 * node:test, zero npm deps) — FIX-04's escaping primitive pinned at the
 * unit level.
 *
 * data.js is authored as an ES module (`export default DataAPI;`); its
 * CommonJS fallback block never engages under Node because the file is
 * loaded via ESM syntax detection / require(esm), which returns the module
 * namespace — the DataAPI object is therefore the namespace's `.default`.
 */

const { test } = require('node:test');
const assert = require('node:assert');

const DataAPI = require('../../dnallm-mark/js/data.js').default;

test('escapeHTML turns each of the five HTML-significant characters into its entity form', () => {
  assert.strictEqual(DataAPI.escapeHTML('&'), '&amp;');
  assert.strictEqual(DataAPI.escapeHTML('<'), '&lt;');
  assert.strictEqual(DataAPI.escapeHTML('>'), '&gt;');
  assert.strictEqual(DataAPI.escapeHTML('"'), '&quot;');
  assert.strictEqual(DataAPI.escapeHTML("'"), '&#039;');
});

test('escapeHTML escapes combined hostile strings and leaves plain strings untouched', () => {
  // A full HTML tag payload must render as inert text.
  assert.strictEqual(
    DataAPI.escapeHTML('<img src=x onerror="window.pwned=1">'),
    '&lt;img src=x onerror=&quot;window.pwned=1&quot;&gt;',
  );
  // & is replaced first, so literal ampersands do not double-escape entities.
  assert.strictEqual(DataAPI.escapeHTML('a & b < c'), 'a &amp; b &lt; c');
  assert.strictEqual(DataAPI.escapeHTML('plain-model_name-123'), 'plain-model_name-123');
  assert.strictEqual(DataAPI.escapeHTML(''), '');
});

test('escapeHTML passes non-string values through unchanged', () => {
  assert.strictEqual(DataAPI.escapeHTML(42), 42);
  assert.strictEqual(DataAPI.escapeHTML(null), null);
  assert.strictEqual(DataAPI.escapeHTML(undefined), undefined);
  assert.strictEqual(DataAPI.escapeHTML(true), true);
  assert.deepStrictEqual(DataAPI.escapeHTML({ size: 117 }), { size: 117 });
});
