/* ========================================
   DNALLM Mark Models Page
   模型页面
   ======================================== */

import CONFIG from './config.js';
import DataAPI from './data.js';

class ModelsPage {
  constructor() {
    this.state = {
      models: [],
      sortField: 'name',
      sortAscending: true
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
    console.log('Setting up Models page...');

    try {
      await this.loadData();
      this.renderNavbar();
      this.renderHero();
      this.renderModelsTable();
      this.bindEvents();

      console.log('Models page setup complete!');
    } catch (error) {
      console.error('Failed to setup models page:', error);
    }
  }

  async loadData() {
    const comparison = await DataAPI.loadModelsComparison();
    const performanceData = await DataAPI.loadAllModelPerformance();

    this.state.models = Object.entries(comparison).map(([key, data]) => ({
      key,
      name: data.model?.name || key,
      size: data.model?.['size (M)'] || 0,
      type: data.model?.type || 'N/A',
      tokenizer: data.model?.tokenizer || 'N/A',
      architecture: data.model?.architecture || 'N/A',
      series: data.model?.series || 'N/A',
      contextLen: data.model?.['context_len (bp)'] || 'N/A',
      species: DataAPI.aggregateSpecies(key, performanceData[key]),
      huggingface: data.model?.huggingface || '',
      modelscope: data.model?.modelscope || ''
    }));
  }

  renderNavbar() {
    const navbarHTML = `
      <nav class="navbar">
        <div class="navbar-logo">
          <a href="/" class="logo">${CONFIG.APP_NAME}</a>
        </div>
        <ul class="navbar-nav">
          ${CONFIG.NAV_LINKS.map(link => `
            <li><a href="${link.url}" class="nav-link ${link.active ? 'active' : ''}">${link.name}</a></li>
          `).join('')}
        </ul>
      </nav>
    `;
    document.querySelector('.navbar-container').innerHTML = navbarHTML;
  }

  renderHero() {
    const heroHTML = `
      <section class="hero">
        <h1>Models</h1>
        <p class="hero-subtitle">DNA Large Language Models overview</p>
      </section>
    `;
    document.querySelector('.hero-container').innerHTML = heroHTML;
  }

  renderModelsTable() {
    const container = document.querySelector('.models-container');
    if (!container) return;

    const sortedModels = [...this.state.models].sort((a, b) => {
      let aVal = a[this.state.sortField];
      let bVal = b[this.state.sortField];

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      if (this.state.sortAscending) {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    container.innerHTML = `
      <div class="models-table-container">
        <table class="models-table">
          <thead>
            <tr>
              <th class="sortable" data-sort="name">Model Name</th>
              <th class="sortable" data-sort="size">Size (M)</th>
              <th class="sortable" data-sort="type">Type</th>
              <th class="sortable" data-sort="tokenizer">Tokenizer</th>
              <th class="sortable" data-sort="architecture">Architecture</th>
              <th class="sortable" data-sort="series">Series</th>
              <th class="sortable" data-sort="contextLen">Context Length (bp)</th>
              <th class="sortable" data-sort="species">Species</th>
              <th>Links</th>
            </tr>
          </thead>
          <tbody>
            ${sortedModels.map(model => `
              <tr>
                <td><strong>${model.name}</strong></td>
                <td>${model.size}</td>
                <td>${model.type}</td>
                <td>${model.tokenizer}</td>
                <td>${model.architecture}</td>
                <td>${model.series || 'N/A'}</td>
                <td>${model.contextLen || 'N/A'}</td>
                <td>${model.species.join(', ') || 'N/A'}</td>
                <td>
                  ${model.huggingface ? `<a href="${model.huggingface}" target="_blank" rel="noopener">HuggingFace</a>` : '-'}
                  ${model.modelscope ? `<a href="${model.modelscope}" target="_blank" rel="noopener">ModelScope</a>` : ''}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  bindEvents() {
    document.querySelectorAll('.models-table th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const field = th.dataset.sort;
        if (this.state.sortField === field) {
          this.state.sortAscending = !this.state.sortAscending;
        } else {
          this.state.sortField = field;
          this.state.sortAscending = false;
        }
        this.renderModelsTable();
      });
    });
  }
}

const app = new ModelsPage();
export default ModelsPage;
