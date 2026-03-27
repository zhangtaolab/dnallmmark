/* ========================================
   DNALLM Mark Main JavaScript
   Main logic file - Load data from models_comparison.json
   ======================================== */

import CONFIG from './config.js';
import DataAPI from './data.js';

class DNALLMMark {
  constructor() {
    this.state = {
      currentArena: 'all',
      currentFilter: 'all',
      currentSort: 'rank_score',
      models: [],
      filteredModels: [],
      sortAscending: false,
      chart: null
    };

    this.init();
  }

  init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  async setup() {
    console.log('Setting up DNALLM Mark...');

    try {
      await this.loadData();
      this.renderHero();
      this.renderCategoryNav();
      this.filterAndSortModels();
      this.renderScatterChart();
      this.renderLeaderboard();
      this.bindEvents();

      console.log('DNALLM Mark setup complete!');
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  }

  async loadData() {
    // Load data based on current arena
    const comparison = await DataAPI.loadModelsComparisonByArena(this.state.currentArena);

    this.state.models = Object.entries(comparison).map(([key, data], index) => ({
      key,
      id: data.model?.name || key,
      name: data.model?.name || key,
      size: data.model?.['size (M)'] || 0,
      type: data.model?.type || 'N/A',
      tokenizer: data.model?.tokenizer || 'N/A',
      architecture: data.model?.architecture || 'N/A',
      species: data.model?.species || [],
      performance: data.performance || {},
      color: DataAPI.getColorForModel(key, index),
      icon: key.charAt(0).toUpperCase()
    }));

    console.log(`Loaded ${this.state.models.length} models for arena: ${this.state.currentArena}`);
  }

  renderNavbar() {
    // Determine active link based on current page
    const currentPage = window.location.pathname;
    const navbarHTML = `
      <nav class="navbar">
        <div class="navbar-logo">
          <a href="/" class="logo">${CONFIG.APP_NAME}</a>
        </div>
        <ul class="navbar-nav">
          ${CONFIG.NAV_LINKS.map(link => {
            const isActive = (link.url === '/' && currentPage === '/') ||
                             (link.url !== '/' && currentPage.includes(link.url));
            return `<li><a href="${link.url}" class="nav-link ${isActive ? 'active' : ''}">${link.name}</a></li>`;
          }).join('')}
        </ul>
      </nav>
    `;
    document.querySelector('.navbar-container').innerHTML = navbarHTML;
  }

  renderHero() {
    const heroHTML = `
      <section class="hero">
        <h1>Leaderboards</h1>
        <p class="hero-subtitle">${CONFIG.APP_DESCRIPTION}</p>
      </section>
    `;
    document.querySelector('.hero-container').innerHTML = heroHTML;
  }

  renderCategoryNav() {
    const categoryNavHTML = `
      <nav class="category-nav">
        ${CONFIG.ARENAS.map(arena => `
          <button
            class="tag ${this.state.currentArena === arena.id ? 'active' : ''}"
            data-arena="${arena.id}"
          >
            <span class="tag-icon">${arena.icon}</span>
            <span class="tag-text">${arena.name}</span>
          </button>
        `).join('')}
      </nav>
    `;
    document.querySelector('.category-nav-container').innerHTML = categoryNavHTML;
  }

  filterAndSortModels() {
    let models = [...this.state.models];

    // Filter by count
    if (this.state.currentFilter === 'top-20') {
      models = models.slice(0, 20);
    } else if (this.state.currentFilter === 'top-10') {
      models = models.slice(0, 10);
    }

    // Sort by rank_score (descending, higher Rank Score = better)
    models.sort((a, b) => {
      const rankA = a.performance?.rank_score ?? 0;
      const rankB = b.performance?.rank_score ?? 0;
      return rankB - rankA;
    });

    models.forEach((model, index) => {
      model.displayRank = index + 1;
    });

    this.state.filteredModels = models;
  }

  /**
   * Calculate nice axis limits with rounded values
   * @param {number} min - Minimum data value
   * @param {number} max - Maximum data value
   * @param {string} axis - 'x' or 'y' axis
   * @returns {{min: number, max: number}}
   */
  calculateAxisLimits(min, max, axis) {
    const range = max - min;

    if (axis === 'x') {
      // X axis (Sum PFLOPs) - typically smaller values
      const xStep = Math.max(10, Math.pow(10, Math.floor(Math.log10(range || 1))));
      const niceMin = Math.floor(min / xStep) * xStep;
      const niceMax = Math.ceil(max / xStep) * xStep;
      return {
        min: Math.max(0, niceMin),
        max: niceMax
      };
    } else {
      // Y axis (Rank Score) - typically larger values
      const magnitude = Math.floor(Math.log10(range || 1));
      const baseStep = Math.pow(10, magnitude);
      // Use 1, 2, 5 step sequence
      let stepMultiplier = 1;
      const normalizedRange = range / baseStep;
      if (normalizedRange > 5) {
        stepMultiplier = 1;
      } else if (normalizedRange > 2) {
        stepMultiplier = 0.5;
      } else {
        stepMultiplier = 0.2;
      }
      const yStep = Math.max(50, baseStep * stepMultiplier);
      const niceMin = Math.floor(min / yStep) * yStep;
      const niceMax = Math.ceil(max / yStep) * yStep;
      return {
        min: Math.max(0, niceMin),
        max: niceMax
      };
    }
  }

  renderScatterChart() {
    const canvas = document.getElementById('scatterChart');
    if (!canvas) return;

    if (this.state.chart) {
      this.state.chart.destroy();
    }

    // Set title based on arena
    const arenaTitles = {
      'all': 'FLOPs vs Rank Score (All Species)',
      'animal': 'FLOPs vs Rank Score (Animal)',
      'plant': 'FLOPs vs Rank Score (Plant)',
      'microbe': 'FLOPs vs Rank Score (Microbe)'
    };
    const arenaDescriptions = {
      'all': 'Top-right corner shows models with higher rank score and better performance',
      'animal': 'Animal genome models: higher Rank Score = better performance',
      'plant': 'Plant genome models: higher Rank Score = better performance',
      'microbe': 'Microbe genome models: higher Rank Score = better performance'
    };

    // Update chart title
    const chartTitle = document.querySelector('.chart-header h3');
    const chartDescription = document.querySelector('.chart-header p');
    if (chartTitle) chartTitle.textContent = arenaTitles[this.state.currentArena];
    if (chartDescription) chartDescription.textContent = arenaDescriptions[this.state.currentArena];

    const datasets = this.state.filteredModels.map(model => ({
      label: model.id,
      data: [{
        x: model.performance?.sum_PFLOPs || 0,
        y: model.performance?.rank_score || 0,
        model: model
      }],
      backgroundColor: model.color + '99', // Add semi-transparency (60% alpha)
      borderColor: model.color,
      borderWidth: 1,
      pointRadius: 4, // Smaller points
      pointHoverRadius: 6,
      pointStyle: 'circle',
      pointHoverBorderWidth: 2,
      pointHoverBorderColor: '#FFFFFF'
    }));

    const allScores = this.state.filteredModels.map(m => m.performance?.sum_PFLOPs || 0);
    const allRanks = this.state.filteredModels.map(m => m.performance?.rank_score || 0);
    const minScore = Math.min(...allScores) || 0;
    const maxScore = Math.max(...allScores) || 0;
    const minRank = Math.min(...allRanks) || 0;
    const maxRank = Math.max(...allRanks) || 0;

    // Calculate smart axis limits
    const xLimits = this.calculateAxisLimits(minScore, maxScore, 'x');
    const yLimits = this.calculateAxisLimits(minRank, maxRank, 'y');

    const config = {
      type: 'scatter',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            enabled: true,
            backgroundColor: '#292C33',
            titleColor: '#FFFFFF',
            bodyColor: '#FFFFFF',
            borderColor: '#E9ECEF',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              title: (context) => context[0].raw.model.id,
              label: (context) => {
                const m = context.raw.model;
                const p = m.performance;
                return [
                  `Sum PFLOPs: ${(p?.sum_PFLOPs || 0).toFixed(2)}`,
                  `Rank Score: ${p?.rank_score || 0}`,
                  `Avg Raw: ${(p?.avg_raw || 0).toFixed(4)}`,
                  `Top 3: ${p?.top3_count || 0}`,
                  `Top 5: ${p?.top5_count || 0}`,
                  `Top 10: ${p?.top10_count || 0}`
                ];
              }
            }
          },
          title: {
            display: false
          }
        },
        scales: {
          x: {
            type: 'linear',
            position: 'bottom',
            title: {
              display: true,
              text: 'Sum PFLOPs (lower = faster)',
              color: '#595F6E'
            },
            ticks: { color: '#595F6E' },
            grid: { color: '#E0E0E0', borderDash: [5, 5], drawBorder: false },
            min: xLimits.min,
            max: xLimits.max
          },
          y: {
            type: 'linear',
            title: {
              display: true,
              text: 'Rank Score (higher = better)',
              color: '#595F6E'
            },
            ticks: { color: '#595F6E' },
            grid: { color: '#E0E0E0', borderDash: [5, 5], drawBorder: false },
            reverse: false,
            min: yLimits.min,
            max: yLimits.max
          }
        }
      }
    };

    this.state.chart = new Chart(canvas, config);

    // Render custom legend
    this.renderCustomLegend();
  }

  renderCustomLegend() {
    const legendContainer = document.getElementById('custom-legend');
    if (!legendContainer) return;

    const models = this.state.filteredModels;
    const legendHTML = models.map(model => `
      <div class="legend-item">
        <div class="legend-color" style="background-color: ${model.color}"></div>
        <span class="legend-label">${model.id}</span>
      </div>
    `).join('');

    legendContainer.innerHTML = legendHTML;
  }

  renderLeaderboard() {
    const leaderboardHTML = `
      <div class="leaderboard">
        <div class="leaderboard-header">
          <div class="leaderboard-title">
            <h3>Model Performance</h3>
            <small>Updated: ${new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</small>
          </div>
          <div class="leaderboard-controls">
            ${CONFIG.FILTER_OPTIONS.map(option => `
              <button
                class="btn btn-sm ${this.state.currentFilter === option.id ? 'active' : ''}"
                data-filter="${option.id}"
              >
                ${option.name}
              </button>
            `).join('')}
          </div>
        </div>

        <div class="leaderboard-content">
          <div class="table-wrapper">
            <table class="arena-table">
              <thead>
                <tr>
                  <th class="sortable" data-sort="rank">Rank</th>
                  <th class="sortable" data-sort="id">Model</th>
                  <th class="sortable" data-sort="rank_score">Rank Score</th>
                  <th class="sortable" data-sort="sum_minmax">Sum MinMax</th>
                  <th class="sortable" data-sort="sum_PFLOPs">Sum PFLOPs</th>
                  <th class="sortable" data-sort="top3_count">Top3 Count</th>
                  <th class="sortable" data-sort="top5_count">Top5 Count</th>
                  <th class="sortable" data-sort="top10_count">Top10 Count</th>
                </tr>
              </thead>
              <tbody>
                ${this.state.filteredModels.map(model => this.renderModelRow(model)).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;

    document.querySelector('.leaderboard-container').innerHTML = leaderboardHTML;
  }

  renderModelRow(model) {
    const rankClass = model.displayRank <= 3 ? `rank-${model.displayRank}` : 'rank-default';
    const p = model.performance || {};

    return `
      <tr>
        <td>
          <span class="rank-badge ${rankClass}">${model.displayRank}</span>
        </td>
        <td>
          <div class="model-info">
            <div class="model-icon" style="background-color: ${model.color}20; color: ${model.color}">
              ${model.icon}
            </div>
            <div>
              <div class="model-name">${model.id}</div>
              <small class="model-size">${model.size}M</small>
            </div>
          </div>
        </td>
        <td>
          <span class="rank-value">${p.rank_score || 0}</span>
        </td>
        <td>
          <span class="rank-value">${(p.sum_minmax || 0).toFixed(2)}</span>
        </td>
        <td>
          <span class="flops-value">${(p.sum_PFLOPs || 0).toFixed(2)}</span>
        </td>
        <td>
          <span class="top-count">${p.top3_count || 0}</span>
        </td>
        <td>
          <span class="top-count">${p.top5_count || 0}</span>
        </td>
        <td>
          <span class="top-count">${p.top10_count || 0}</span>
        </td>
      </tr>
    `;
  }

  bindEvents() {
    document.querySelector('.category-nav-container').addEventListener('click', (e) => {
      const tag = e.target.closest('.category-nav .tag');
      if (tag) {
        this.state.currentArena = tag.dataset.arena;
        // Reload data
        this.loadData().then(() => {
          this.filterAndSortModels();
          this.renderCategoryNav();
          this.renderScatterChart();
          this.renderLeaderboard();
        });
      }
    });

    // Use event delegation for dynamically rendered buttons (bound to document to avoid losing events due to re-rendering)
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-filter]');
      if (btn) {
        const filterId = btn.dataset.filter;
        this.state.currentFilter = filterId;
        this.filterAndSortModels();
        this.renderScatterChart();
        this.renderLeaderboard();
      }
    });

    document.querySelectorAll('.arena-table th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const sortField = th.dataset.sort;
        if (this.state.currentSort === sortField) {
          this.state.sortAscending = !this.state.sortAscending;
        } else {
          this.state.currentSort = sortField;
          this.state.sortAscending = false;
        }
        this.filterAndSortModels();
        this.renderLeaderboard();
      });
    });
  }
}

const app = new DNALLMMark();
export default DNALLMMark;
