#!/usr/bin/env node
/**
 * Behavior tests for the sweep-progress web mirror (12-02, WEB-01,
 * node:test, zero npm deps) — the DOM-less lane's two idioms:
 *
 *  (a) the data-api idiom (data-api.test.js pattern): loadProgress is a
 *      memoizing fetch wrapper over its own cache.progress slot that
 *      throws on an !ok response;
 *  (b) the file-structure idiom (generate-tasks-index.test.js pattern):
 *      progress.html loads exactly one script (the module, zero CDN),
 *      carries the Progress title; config.js gains the Progress
 *      NAV_LINKS entry appended last; styles.css imports progress.css
 *      last; progress.css holds the five cell-state classes with token
 *      colors only; js/progress.js carries the UI-SPEC copy constants
 *      and registers no timers (the deferred auto-refresh boundary);
 *      data/progress/ lands .gitkeep only — no fabricated sample JSON.
 */

const { test } = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const DataAPI = require('../../dnallm-mark/js/data.js').default;
const SITE = path.join(__dirname, '..', '..', 'dnallm-mark');

const read = (...parts) => fs.readFileSync(path.join(SITE, ...parts), 'utf8');

// ===== (a) DataAPI.loadProgress — the fetch-wrapper contract =====

test('loadProgress memoizes a stubbed fetch into its own cache slot', async () => {
  assert.strictEqual(typeof DataAPI.loadProgress, 'function');

  const payload = { version: 1, generated_at: '2026-10-13T09:30:00Z', sweeps: [] };
  let fetchCalls = 0;
  globalThis.fetch = async () => {
    fetchCalls += 1;
    return { ok: true, json: async () => payload };
  };

  DataAPI.cache.progress = null;
  const first = await DataAPI.loadProgress();
  const second = await DataAPI.loadProgress();

  assert.strictEqual(fetchCalls, 1, 'fetch must be invoked exactly once');
  assert.strictEqual(first, payload, 'first call resolves the fetched payload');
  assert.strictEqual(
    second,
    first,
    'second call returns the cached instance, not a refetch',
  );
  assert.strictEqual(
    DataAPI.cache.progress,
    payload,
    'the progress cache slot holds the fetched payload',
  );

  delete globalThis.fetch;
});

test('loadProgress throws on an !ok response (fetch failures surface)', async () => {
  globalThis.fetch = async () => ({ ok: false, status: 404 });

  DataAPI.cache.progress = null;
  await assert.rejects(
    () => DataAPI.loadProgress(),
    /sweep\.json/,
    'the error names the file like every other DataAPI loader',
  );

  delete globalThis.fetch;
});

// ===== (b) File-structure pins over the page set =====

test('progress.html: module script only — the zero-CDN pin', () => {
  const html = read('progress.html');
  assert.match(html, /<title>DNALLM Mark \| Progress<\/title>/);
  const scripts = [...html.matchAll(/<script\b[^>]*\ssrc="([^"]+)"/g)].map((m) => m[1]);
  assert.strictEqual(
    scripts.length,
    1,
    `exactly one sourced script, got: ${scripts.join(', ')}`,
  );
  assert.strictEqual(scripts[0], './js/progress.js');
});

test('config.js: NAV_LINKS gains Progress appended last', () => {
  const src = read('js', 'config.js');
  const block = src.match(/NAV_LINKS:\s*\[([\s\S]*?)\]/);
  assert.ok(block, 'NAV_LINKS array found');
  const entries = [
    ...block[1].matchAll(/\{\s*name:\s*'([^']+)'\s*,\s*url:\s*'([^']+)'\s*\}/g),
  ];
  assert.ok(entries.length >= 2, 'existing entries preserved');
  const last = entries[entries.length - 1];
  assert.strictEqual(last[1], 'Progress');
  assert.strictEqual(last[2], './progress.html');
});

test('styles.css: progress.css imported last (the task.css precedent)', () => {
  const css = read('css', 'styles.css');
  const imports = [...css.matchAll(/@import\s+url\('([^']+)'\);/g)].map((m) => m[1]);
  assert.ok(imports.length >= 1);
  assert.strictEqual(imports[imports.length - 1], './progress.css');
});

test('progress.css: the five cell-state classes, token colors only', () => {
  const css = read('css', 'progress.css');
  for (const state of ['done', 'running', 'failed', 'skipped', 'queued']) {
    assert.match(
      css,
      new RegExp(`\\.cell-state--${state}\\s*\\{`),
      `.cell-state--${state} rule present`,
    );
  }
  assert.doesNotMatch(
    css,
    /#[0-9a-fA-F]{3,8}\b/,
    'no hardcoded hex — every value a variables.css token',
  );
});

test('progress.js: the UI-SPEC copy table + no timer registration', () => {
  const src = read('js', 'progress.js');
  assert.match(src, /TITLE:\s*'Sweep Progress'/);
  assert.match(src, /SUBTITLE:\s*'Read-only mirror of fine-tuning sweep runs'/);
  assert.match(src, /FILTER_ALL_MODELS:\s*'-- All Models --'/);
  assert.match(src, /FILTER_ALL_TASKS:\s*'-- All Tasks --'/);
  assert.match(src, /UNKNOWN_TOTAL:\s*'Unknown total'/);
  assert.match(
    src,
    /FOOTER_STAMP:\s*'Data generated \{generated_at\} · regenerate via script\/gen_progress\.py'/,
  );
  assert.doesNotMatch(
    src,
    /setInterval|setTimeout/,
    'no timers — the deferred auto-refresh boundary stays deferred',
  );
});

test('data/progress/: .gitkeep only — no fabricated sample JSON on the public site', () => {
  const dir = path.join(SITE, 'data', 'progress');
  assert.ok(fs.existsSync(path.join(dir, '.gitkeep')));
  assert.deepStrictEqual(
    fs.readdirSync(dir).sort(),
    ['.gitkeep'],
    'the directory carries exactly the .gitkeep marker until the maintainer regenerates',
  );
});
