#!/usr/bin/env node
/**
 * Behavior tests for the F6 dual-view toggle in dnallm-mark/js/main.js
 * (node:test, zero npm deps) — F6 Q4: the z-score × uniform-difficulty
 * weighted view is the DEFAULT public number and the raw-rank view is one
 * click away. The weighted value is only ever READ from
 * performance.weighted_score (precomputed offline by
 * script/summarize_comparison.py) — never computed client-side (the dead
 * recalculateComparison lesson, DATA-07).
 *
 * main.js is an ES module that instantiates its page controller at import
 * time; under require(esm) it needs only a minimal document stub —
 * readyState 'loading' parks setup() behind a DOMContentLoaded listener that
 * never fires in Node, leaving the exported class directly testable (the
 * main-topn-filter.test.js pattern).
 */

const { test } = require('node:test');
const assert = require('node:assert');

globalThis.document = { readyState: 'loading', addEventListener: () => {} };

const DNALLMMark = require('../../dnallm-mark/js/main.js').default;
const CONFIG = require('../../dnallm-mark/js/config.js').default;

function pageWithState(overrides) {
  const page = Object.create(DNALLMMark.prototype);
  page.state = {
    models: [],
    filteredModels: [],
    currentFilter: 'all',
    currentView: 'weighted',
    currentSort: 'weighted_score',
    sortAscending: false,
    dataManifest: null,
    ...overrides,
  };
  return page;
}

test('default state is the weighted view with its sort field (F6 Q4)', () => {
  const page = new DNALLMMark();
  assert.strictEqual(page.state.currentView, 'weighted');
  assert.strictEqual(page.state.currentSort, 'weighted_score');
});

test('switching views maps to the view-derived sort field and back', () => {
  const page = pageWithState({
    models: [{ id: 'a', performance: { weighted_score: 0.2, rank_score: 3 } }],
  });
  const renders = [];
  page.filterAndSortModels = () => renders.push('sort');
  page.renderScatterChart = () => renders.push('scatter');
  page.renderLeaderboard = () => renders.push('leaderboard');

  page.switchView('rank');
  assert.strictEqual(page.state.currentView, 'rank');
  assert.strictEqual(page.state.currentSort, 'rank_score');
  assert.strictEqual(page.state.sortAscending, false);
  assert.deepStrictEqual(renders, ['sort', 'scatter', 'leaderboard']);

  page.switchView('weighted');
  assert.strictEqual(page.state.currentView, 'weighted');
  assert.strictEqual(page.state.currentSort, 'weighted_score');
});

test('switchView ignores unknown ids and same-view no-ops', () => {
  const page = pageWithState({});
  let renders = 0;
  page.filterAndSortModels = () => { renders += 1; };
  page.renderScatterChart = () => { renders += 1; };
  page.renderLeaderboard = () => { renders += 1; };

  page.switchView('banana');
  page.switchView('weighted'); // already active — no-op
  assert.strictEqual(renders, 0);
  assert.strictEqual(page.state.currentView, 'weighted');
});

test('weighted sorting reads performance.weighted_score, never recomputes it', () => {
  // model-b wins on weighted_score while losing on rank_score — ordering by
  // the weighted field proves the accessor reads the precomputed value.
  const page = pageWithState({
    models: [
      { id: 'w-low', performance: { weighted_score: 0.1, rank_score: 99, sum_zscore: 4.7 } },
      { id: 'w-high', performance: { weighted_score: 0.5, rank_score: 1, sum_zscore: 23.5 } },
    ],
  });
  page.filterAndSortModels();
  assert.deepStrictEqual(page.state.filteredModels.map((m) => m.id), ['w-high', 'w-low']);

  const rankPage = pageWithState({
    models: page.state.models,
    currentView: 'rank',
    currentSort: 'rank_score',
  });
  rankPage.filterAndSortModels();
  assert.deepStrictEqual(rankPage.state.filteredModels.map((m) => m.id), ['w-low', 'w-high']);
});

test('renderModelRow shows the active view metric from the performance block', () => {
  const model = {
    displayRank: 1,
    color: '#123456',
    icon: 'F',
    id: 'fake-model',
    size: 12,
    performance: { weighted_score: 0.1234, rank_score: 5.0 },
  };

  const weighted = pageWithState({ currentView: 'weighted' });
  const weightedRow = weighted.renderModelRow(model);
  assert.ok(weightedRow.includes('0.123'), `expected the weighted value, got: ${weightedRow}`);
  assert.ok(!weightedRow.includes('>5<'), 'the rank_score must not render as the metric cell');

  const rank = pageWithState({ currentView: 'rank' });
  const rankRow = rank.renderModelRow(model);
  assert.ok(rankRow.includes('>5<'), 'the rank view renders rank_score');
});

test('renderFooterStamp renders the manifest stamps and hides on fetch failure', () => {
  // DATA-06: stamped date + data_version from data/manifest.json; a failed
  // fetch (dataManifest null) hides the stamp entirely — no client values.
  const stamped = pageWithState({
    dataManifest: { data_version: '1.1.0', date: '2026-10-10', generated_from: 'a'.repeat(40) },
  });
  const stamp = stamped.renderFooterStamp();
  assert.ok(stamp.includes('2026-10-10'));
  assert.ok(stamp.includes('1.1.0'));
  assert.ok(!stamp.includes('toLocaleDateString'));

  assert.strictEqual(pageWithState({ dataManifest: null }).renderFooterStamp(), '');
  // A malformed manifest (missing fields) also hides rather than half-renders.
  assert.strictEqual(
    pageWithState({ dataManifest: { data_version: '1.1.0' } }).renderFooterStamp(), ''
  );
});

test('VIEW_OPTIONS declares weighted as the default view in config', () => {
  assert.deepStrictEqual(
    CONFIG.VIEW_OPTIONS.map((o) => o.id),
    ['weighted', 'rank']
  );
  assert.strictEqual(CONFIG.SCATTER_CONFIG.HOME.viewYAxis.weighted.field, 'weighted_score');
  assert.strictEqual(CONFIG.SCATTER_CONFIG.HOME.viewYAxis.rank.field, 'rank_score');
});
