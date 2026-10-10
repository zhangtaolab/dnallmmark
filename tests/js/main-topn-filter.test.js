#!/usr/bin/env node
/**
 * Behavior test for DNALLMMark.filterAndSortModels (dnallm-mark/js/main.js,
 * node:test, zero npm deps) — CR-01: the Top-N filters must slice AFTER the
 * sort. models_comparison*.json is written with sort_keys=True, so the page's
 * model list arrives alphabetically; slicing first made "Top 10" show the
 * first ten models alphabetically instead of the ten best by the active sort
 * (rank_score descending by default — the leaderboard's own ordering).
 *
 * main.js is an ES module that instantiates its page controller at import
 * time; under require(esm) it needs only a minimal document stub —
 * readyState 'loading' parks setup() behind a DOMContentLoaded listener that
 * never fires in Node, leaving the exported class directly testable. The
 * method under test touches nothing but this.state, so a prototype instance
 * with a hand-built state exercises the real production code path.
 */

const { test } = require('node:test');
const assert = require('node:assert');

globalThis.document = { readyState: 'loading', addEventListener: () => {} };

const DNALLMMark = require('../../dnallm-mark/js/main.js').default;

// 15 models listed alphabetically with shuffled rank_scores (the committed
// comparison files' key order). The ranked top 10 deliberately includes
// models k..o — the tail of the alphabetical order — so a slice-before-sort
// regression cannot pass.
const SCORES = {
  'model-a': 5, 'model-b': 50, 'model-c': 10, 'model-d': 41, 'model-e': 8,
  'model-f': 33, 'model-g': 20, 'model-h': 45, 'model-i': 15, 'model-j': 28,
  'model-k': 90, 'model-l': 61, 'model-m': 72, 'model-n': 83, 'model-o': 55,
};
const RANKED_TOP_TEN = [
  'model-k', 'model-n', 'model-m', 'model-l', 'model-o',
  'model-b', 'model-h', 'model-d', 'model-f', 'model-j',
];

function pageWithState(overrides) {
  const page = Object.create(DNALLMMark.prototype);
  page.state = {
    models: Object.keys(SCORES).map((id) => ({
      key: id,
      id,
      name: id,
      performance: { rank_score: SCORES[id] },
    })),
    filteredModels: [],
    currentFilter: 'all',
    currentSort: 'rank_score',
    sortAscending: false,
    ...overrides,
  };
  return page;
}

test('top-10 shows the ten highest rank_score models, not an alphabetical subset (CR-01)', () => {
  const page = pageWithState({ currentFilter: 'top-10' });
  page.filterAndSortModels();

  assert.strictEqual(page.state.filteredModels.length, 10);
  assert.deepStrictEqual(
    page.state.filteredModels.map((m) => m.id),
    RANKED_TOP_TEN,
  );
  // The five lowest-ranked models (incl. alphabetical-first model-a) are out.
  for (const excluded of ['model-a', 'model-c', 'model-e', 'model-g', 'model-i']) {
    assert.ok(!page.state.filteredModels.some((m) => m.id === excluded));
  }
});

test('displayRank is the 1..N view position for top-10 and for all models', () => {
  const top10 = pageWithState({ currentFilter: 'top-10' });
  top10.filterAndSortModels();
  assert.deepStrictEqual(
    top10.state.filteredModels.map((m) => m.displayRank),
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  );

  const all = pageWithState({ currentFilter: 'all' });
  all.filterAndSortModels();
  assert.strictEqual(all.state.filteredModels.length, 15);
  assert.deepStrictEqual(
    all.state.filteredModels.map((m) => m.displayRank),
    Array.from({ length: 15 }, (_, i) => i + 1),
  );
});

test('top-10 follows the active sort: sorting by name yields the first ten alphabetical', () => {
  const page = pageWithState({
    currentFilter: 'top-10',
    currentSort: 'id',
    sortAscending: true,
  });
  page.filterAndSortModels();

  assert.deepStrictEqual(
    page.state.filteredModels.map((m) => m.id),
    Object.keys(SCORES).slice(0, 10),
  );
});
