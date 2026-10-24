/* ========================================
   DNALLM Mark Sweep Progress Page
   Sweep 进度镜像页面（只读静态镜像, D-02）
   Loads data/progress/sweep.json once; reload = refresh (no polling,
   no timers, no localStorage — the static-hosting contract).
   ======================================== */

import DataAPI from './data.js';
import { renderNavbar } from './navbar.js';

// UI copy (12-UI-SPEC copy table, verbatim — English per the D-10
// site-convention ruling; web copy lives in the page module).
const PROGRESS = {
  TITLE: 'Sweep Progress',
  SUBTITLE: 'Read-only mirror of fine-tuning sweep runs',
  SUMMARY_ELAPSED: 'Elapsed {elapsed}',
  SUMMARY_ETA: 'ETA {eta}',
  STATE_FINISHED: 'finished',
  STATE_RUNNING: 'running',
  STATE_ARTIFACTS_ONLY: 'artifacts only',
  UNKNOWN_TOTAL: 'Unknown total',
  LEGEND: '✓ Done · ⠋ Running · ✗ Failed · ⊘ Skipped · ◌ Queued',
  COL_MODEL: 'Model',
  COL_TASK: 'Task',
  COL_SEED: 's{seed}',
  FILTER_ALL_MODELS: '-- All Models --',
  FILTER_ALL_TASKS: '-- All Tasks --',
  FILTER_ALL: 'All',
  EMPTY_NO_DATA_TITLE: 'No sweep data yet',
  EMPTY_NO_DATA_HINT: 'Run script/gen_progress.py to generate data/progress/sweep.json',
  EMPTY_FETCH_TITLE: 'Failed to load progress data',
  EMPTY_FETCH_HINT: 'Check that data/progress/sweep.json exists, then reload the page',
  EMPTY_NO_MATCH_TITLE: 'No cells match the current filters',
  EMPTY_NO_MATCH_HINT: 'Clear the model, task, or status filters to see all cells',
  FOOTER_STAMP: 'Data generated {generated_at} · regenerate via script/gen_progress.py',
};

// The five cross-surface cell states (the TUI glyph vocabulary VERBATIM):
// machine status -> glyph, CSS modifier, legend word. A status outside
// this map is an unknown record status — rendered VERBATIM in the glyph
// slot, uncolored, legend stays authoritative (the honesty rule).
const CELL_STATES = {
  completed: { glyph: '✓', css: 'done', label: 'Done' },
  running: { glyph: '⠋', css: 'running', label: 'Running' },
  failed: { glyph: '✗', css: 'failed', label: 'Failed' },
  skipped: { glyph: '⊘', css: 'skipped', label: 'Skipped' },
  queued: { glyph: '◌', css: 'queued', label: 'Queued' },
};

class ProgressPage {
  constructor() {
    this.state = {
      data: null,          // the whole sweep.json document
      sweepIndex: 0,       // selected sweep (index; root names may repeat)
      modelFilter: '',     // '' = all models
      taskFilter: '',      // '' = all tasks
      statusFilter: new Set(), // active statuses; empty = all (All-clears)
    };
    this.init();
  }

  async init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  async setup() {
    console.log('Setting up Progress page...');

    try {
      // The navbar is static chrome — render it before any I/O so a failed
      // data fetch still leaves the user able to navigate (WR-03).
      renderNavbar();
      await this.loadData();
      this.renderHero();
      const sweeps = this.state.data?.sweeps || [];
      if (sweeps.length === 0) {
        this.renderEmptyState(PROGRESS.EMPTY_NO_DATA_TITLE, PROGRESS.EMPTY_NO_DATA_HINT);
      } else {
        this.renderControls();
        this.renderSummary();
        this.renderTable();
      }
      this.renderStamp(this.state.data?.generated_at);
      this.bindEvents();

      console.log('Progress page setup complete!');
    } catch (error) {
      console.error('Failed to setup progress page:', error);
      // Never a blank body: navbar + hero already render above; the data
      // region honestly shows the fetch-error state (WR-03 discipline).
      this.renderHero();
      this.renderEmptyState(PROGRESS.EMPTY_FETCH_TITLE, PROGRESS.EMPTY_FETCH_HINT);
    }
  }

  async loadData() {
    this.state.data = await DataAPI.loadProgress();
  }

  /** The selected sweep, bounds-guarded against a stale index. */
  currentSweep() {
    const sweeps = this.state.data?.sweeps || [];
    if (this.state.sweepIndex >= sweeps.length) this.state.sweepIndex = 0;
    return sweeps[this.state.sweepIndex];
  }

  renderHero() {
    const container = document.querySelector('.hero-container');
    if (!container) return;
    container.innerHTML = `
      <section class="hero">
        <h1>${PROGRESS.TITLE}</h1>
        <p class="hero-subtitle">${PROGRESS.SUBTITLE}</p>
      </section>
    `;
  }

  // ===== Controls: sweep selector + model/task selects + status tags =====

  renderControls() {
    const container = document.querySelector('.model-selector-wrapper');
    if (!container) return;

    const sweep = this.currentSweep();
    const models = [...new Set((sweep.cells || []).map((cell) => cell.model))].sort();
    const tasks = [...new Set((sweep.cells || []).map((cell) => cell.task))].sort();
    const sweeps = this.state.data.sweeps;

    // The sweep selector appears ONLY when there is more than one sweep
    // (the multi-worker case is exactly when it shows — zero-one-many).
    const sweepSelect = sweeps.length > 1 ? `
      <div class="model-selector">
        <label for="sweep-select">Sweep:</label>
        <select id="sweep-select">
          ${sweeps.map((option, index) => `
            <option value="${index}" ${index === this.state.sweepIndex ? 'selected' : ''}>${DataAPI.escapeHTML(option.root)}</option>
          `).join('')}
        </select>
      </div>
    ` : '';

    container.innerHTML = `
      <div class="category-nav">
        ${sweepSelect}
        <div class="model-selector">
          <label for="progress-model-select">Model:</label>
          <select id="progress-model-select">
            <option value="" ${!this.state.modelFilter ? 'selected' : ''}>${PROGRESS.FILTER_ALL_MODELS}</option>
            ${models.map((name) => `
              <option value="${DataAPI.escapeHTML(name)}" ${this.state.modelFilter === name ? 'selected' : ''}>${DataAPI.escapeHTML(name)}</option>
            `).join('')}
          </select>
        </div>
        <div class="model-selector">
          <label for="progress-task-select">Task:</label>
          <select id="progress-task-select">
            <option value="" ${!this.state.taskFilter ? 'selected' : ''}>${PROGRESS.FILTER_ALL_TASKS}</option>
            ${tasks.map((name) => `
              <option value="${DataAPI.escapeHTML(name)}" ${this.state.taskFilter === name ? 'selected' : ''}>${DataAPI.escapeHTML(name)}</option>
            `).join('')}
          </select>
        </div>
        <div class="filter-group">
          ${this.renderStatusTags()}
        </div>
      </div>
    `;
  }

  renderStatusTags() {
    // `All` clears the active set; a state tag toggles its membership;
    // `.active` reflects the set (the main.js data-filter grammar).
    const allActive = this.state.statusFilter.size === 0;
    return `
      <button type="button" class="tag ${allActive ? 'active' : ''}" data-status="all">${PROGRESS.FILTER_ALL}</button>
      ${Object.entries(CELL_STATES).map(([status, cfg]) => `
        <button type="button" class="tag ${this.state.statusFilter.has(status) ? 'active' : ''}" data-status="${status}">${cfg.glyph} ${cfg.label}</button>
      `).join('')}
    `;
  }

  // ===== Summary card: name + state, done/total, bar, elapsed/ETA, chips =====

  renderSummary() {
    const container = document.querySelector('.progress-summary-container');
    if (!container) return;

    const sweep = this.currentSweep();
    const total = sweep.total ?? null;
    const done = sweep.done ?? 0;
    // Percent only when the total is known — a null total renders an
    // empty bar and no fabricated percent (the honesty rule, web-side).
    const percent = (total !== null && total > 0)
      ? Math.min(100, Math.round((done / total) * 100))
      : null;
    const counts = sweep.state_counts || {};
    const chips = Object.entries(CELL_STATES).map(([status, cfg]) =>
      `<span><span class="cell-state cell-state--${cfg.css}">${cfg.glyph}</span> ${counts[status] ?? 0}</span>`
    ).join(' · ');

    container.innerHTML = `
      <div class="leaderboard progress-summary">
        <div class="progress-summary-head">
          <span class="progress-sweep-name">${DataAPI.escapeHTML(sweep.root)}</span>
          <span class="tag">${this.sweepStateLabel(sweep.state)}</span>
          <span class="top-count">${total === null
            ? `${done} / ${PROGRESS.UNKNOWN_TOTAL}`
            : `${done} / ${total}`}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${percent ?? 0}%;"></div>
        </div>
        <div class="progress-summary-meta">
          <span>${PROGRESS.SUMMARY_ELAPSED.replace('{elapsed}', this.formatElapsed(sweep.elapsed_seconds))}</span>
          <span>${PROGRESS.SUMMARY_ETA.replace('{eta}', this.formatEta(sweep.eta))}</span>
          <span>${chips}</span>
        </div>
      </div>
    `;
  }

  sweepStateLabel(state) {
    if (state === 'finished') return PROGRESS.STATE_FINISHED;
    if (state === 'artifacts_only') return PROGRESS.STATE_ARTIFACTS_ONLY;
    return PROGRESS.STATE_RUNNING;
  }

  // ===== D-17 humanized durations (35m / 2.1h / 1d 3h shapes) =====

  trimDecimal(value) {
    return Number(value.toFixed(1)).toString();
  }

  humanizeDuration(seconds) {
    const total = Math.max(0, Number(seconds) || 0);
    if (total < 3600) return `${Math.max(1, Math.round(total / 60))}m`;
    if (total < 86400) return `${this.trimDecimal(total / 3600)}h`;
    const days = Math.floor(total / 86400);
    const hours = Math.round((total - days * 86400) / 3600);
    return hours > 0 ? `${days}d ${hours}h` : `${days}d`;
  }

  formatElapsed(seconds) {
    if (seconds === null || seconds === undefined) return '—';
    return this.humanizeDuration(seconds);
  }

  formatEta(eta) {
    if (!eta || eta.mode === 'none') return '—';
    if (eta.mode === 'pending') return 'Estimating…';
    if (eta.mode === 'point') return `≈${this.humanizeDuration(eta.point_seconds)}`;
    if (eta.mode === 'range') {
      return `≈${this.humanizeDuration(eta.lo_seconds)}–${this.humanizeDuration(eta.hi_seconds)}`;
    }
    return '—';
  }

  // ===== Cell table: Model | Task | one column per seed =====

  seedColumnsOf(cells) {
    const seeds = new Set();
    (cells || []).forEach((row) => (row.seeds || []).forEach((seed) => seeds.add(seed.seed)));
    return [...seeds].sort((a, b) => a - b);
  }

  rowMatches(row) {
    if (this.state.modelFilter && row.model !== this.state.modelFilter) return false;
    if (this.state.taskFilter && row.task !== this.state.taskFilter) return false;
    if (this.state.statusFilter.size > 0) {
      const states = (row.seeds || []).map((seed) => seed.state);
      if (!states.some((state) => this.state.statusFilter.has(state))) return false;
    }
    return true;
  }

  renderCellState(seedCell) {
    const known = CELL_STATES[seedCell.state];
    // Curve cells: the aggregate glyph + the per-fraction pairs in the
    // title (the TUI mini-count analog; no inline per-fraction table).
    const fractionTitle = seedCell.fraction_states
      ? seedCell.fraction_states
          .map(([name, state]) => `${name}: ${state}`)
          .join('; ')
      : '';
    const title = fractionTitle ? ` title="${DataAPI.escapeHTML(fractionTitle)}"` : '';
    if (!known) {
      // Unknown record status: the raw machine string, VERBATIM (the
      // scanner's honest rule — never translated, never colored).
      return `<span class="cell-state"${title}>${DataAPI.escapeHTML(String(seedCell.state))}</span>`;
    }
    return `<span class="cell-state cell-state--${known.css}"${title}>${known.glyph}</span>`;
  }

  renderTable() {
    const container = document.querySelector('.leaderboard-container');
    if (!container) return;

    const sweep = this.currentSweep();
    const allCells = sweep.cells || [];
    const rows = allCells.filter((row) => this.rowMatches(row));
    const seedColumns = this.seedColumnsOf(allCells);

    if (rows.length === 0 || seedColumns.length === 0) {
      this.renderEmptyState(PROGRESS.EMPTY_NO_MATCH_TITLE, PROGRESS.EMPTY_NO_MATCH_HINT);
      return;
    }

    const legend = Object.entries(CELL_STATES).map(([status, cfg]) =>
      `<span class="cell-state cell-state--${cfg.css}">${cfg.glyph}</span> ${cfg.label}`
    ).join(' · ');

    container.innerHTML = `
      <div class="leaderboard">
        <div class="leaderboard-header">
          <span class="progress-legend">${legend}</span>
        </div>
        <div class="table-wrapper">
          <table class="arena-table">
            <thead>
              <tr>
                <th>${PROGRESS.COL_MODEL}</th>
                <th>${PROGRESS.COL_TASK}</th>
                ${seedColumns.map((seed) => `<th>${PROGRESS.COL_SEED.replace('{seed}', seed)}</th>`).join('')}
              </tr>
            </thead>
            <tbody>
              ${rows.map((row) => {
                const seedMap = new Map((row.seeds || []).map((seed) => [seed.seed, seed]));
                // Truncation + the full key in the title attribute (the
                // long-key lesson; layout-only inline styles).
                const cellStyle = 'max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;';
                return `
                  <tr>
                    <td style="${cellStyle}" title="${DataAPI.escapeHTML(row.model)}">${DataAPI.escapeHTML(row.model)}</td>
                    <td style="${cellStyle}" title="${DataAPI.escapeHTML(row.task)}">${DataAPI.escapeHTML(row.task)}</td>
                    ${seedColumns.map((seed) => `
                      <td class="text-center">${seedMap.has(seed) ? this.renderCellState(seedMap.get(seed)) : ''}</td>
                    `).join('')}
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  // ===== Empty states + the data stamp =====

  renderEmptyState(title, hint) {
    const container = document.querySelector('.leaderboard-container');
    if (!container) return;
    container.innerHTML = `
      <div class="leaderboard">
        <div class="empty-state">
          <div class="empty-state-icon">📊</div>
          <div class="empty-state-text">${title}</div>
          <div class="empty-state-hint">${hint}</div>
        </div>
      </div>
    `;
  }

  renderStamp(generatedAt) {
    const container = document.querySelector('.progress-stamp-container');
    if (!container) return;
    // generated_at VERBATIM from the JSON — never a client clock; a
    // missing stamp renders nothing rather than a fabricated date.
    if (!generatedAt) return;
    container.innerHTML = `
      <p style="text-align: center; font-size: var(--font-sm); color: var(--color-text-muted); margin-top: var(--spacing-lg);">
        ${PROGRESS.FOOTER_STAMP.replace('{generated_at}', DataAPI.escapeHTML(generatedAt))}
      </p>
    `;
  }

  // ===== Events: delegation on the persistent controls container =====

  bindEvents() {
    // The controls row is re-rendered on sweep change and status toggle,
    // so select/tag listeners live on the persistent wrapper via
    // delegation (change and click both bubble; the finetuning-page
    // container-delegation pattern).
    const controls = document.querySelector('.model-selector-wrapper');

    controls?.addEventListener('change', (e) => {
      if (e.target.id === 'sweep-select') {
        this.state.sweepIndex = parseInt(e.target.value, 10) || 0;
        this.state.modelFilter = '';
        this.state.taskFilter = '';
        this.state.statusFilter.clear();
        this.renderControls();
        this.renderSummary();
        this.renderTable();
      } else if (e.target.id === 'progress-model-select') {
        this.state.modelFilter = e.target.value || '';
        this.renderTable();
      } else if (e.target.id === 'progress-task-select') {
        this.state.taskFilter = e.target.value || '';
        this.renderTable();
      }
    });

    controls?.addEventListener('click', (e) => {
      const tag = e.target.closest('button.tag[data-status]');
      if (!tag) return;
      const status = tag.dataset.status;
      if (status === 'all') {
        this.state.statusFilter.clear();
      } else if (this.state.statusFilter.has(status)) {
        this.state.statusFilter.delete(status);
      } else {
        this.state.statusFilter.add(status);
      }
      this.renderControls();
      this.renderTable();
    });
  }
}

const app = new ProgressPage();
export default ProgressPage;
