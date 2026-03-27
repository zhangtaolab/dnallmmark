/* ========================================
   DNALLM Mark Fine-tuning Results Page
   微调结果页面
   ======================================== */

import CONFIG from './config.js';
import DataAPI from './data.js';

class FineTuningPage {
  constructor() {
    this.state = {
      selectedModel: null,
      selectedDataset: null,
      performanceData: {},
      modelsList: []
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
    console.log('Setting up Fine-tuning page...');

    try {
      await this.loadData();
      this.renderNavbar();
      this.renderHero();
      this.renderModelSelector();
      this.renderLeaderboard();
      this.renderParameterModal();
      this.bindEvents();

      console.log('Fine-tuning page setup complete!');
    } catch (error) {
      console.error('Failed to setup fine-tuning page:', error);
    }
  }

  async loadData() {
    const comparison = await DataAPI.loadModelsComparison();
    this.state.modelsList = Object.keys(comparison);
    this.state.performanceData = await DataAPI.loadAllModelPerformance();
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
        <h1>Fine-tuning Results</h1>
        <p class="hero-subtitle">Model performance across datasets and tasks</p>
      </section>
    `;
    document.querySelector('.hero-container').innerHTML = heroHTML;
  }

  renderModelSelector() {
    const container = document.querySelector('.model-selector-wrapper');
    if (!container) return;

    container.innerHTML = `
      <label for="model-select">Select Model:</label>
      <select id="model-select">
        <option value="">-- All Models --</option>
        ${this.state.modelsList.map(name =>
          `<option value="${name}">${name}</option>`
        ).join('')}
      </select>
    `;
  }

  renderLeaderboard() {
    const container = document.querySelector('.leaderboard-container');
    if (!container) return;

    const rows = this.prepareLeaderboardRows();

    container.innerHTML = `
      <div class="leaderboard">
        <h3>Dataset Performance Leaderboard</h3>
        <div class="table-wrapper">
          <table class="arena-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Dataset</th>
                <th>Species</th>
                <th>Type</th>
                <th>Accuracy</th>
                <th>F1</th>
                <th>AUROC</th>
                <th>AUPRC</th>
                <th>FLOPs (T)</th>
              </tr>
            </thead>
            <tbody>
              ${rows.join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  prepareLeaderboardRows() {
    const rows = [];

    for (const [modelName, perfData] of Object.entries(this.state.performanceData)) {
      if (this.state.selectedModel && modelName !== this.state.selectedModel) continue;

      for (const [datasetName, data] of Object.entries(perfData)) {
        const p = data.performance || {};
        const d = data.dataset || {};

        rows.push(`
          <tr class="clickable-row" data-model="${modelName}" data-dataset="${datasetName}">
            <td class="model-name-link">${modelName}</td>
            <td>${datasetName}</td>
            <td>${d.species || 'N/A'}</td>
            <td>${d.type || 'N/A'}</td>
            <td>${this.formatValue(p.accuracy)}</td>
            <td>${this.formatValue(p.f1)}</td>
            <td>${this.formatValue(p.auroc)}</td>
            <td>${this.formatValue(p.auprc)}</td>
            <td>${this.formatFLOPs(p.FLOPs)}</td>
          </tr>
        `);
      }
    }

    return rows;
  }

  formatValue(value) {
    if (value === undefined || value === '' || value === null) return 'N/A';
    const num = typeof value === 'number' ? value : parseFloat(value);
    return isNaN(num) ? 'N/A' : num.toFixed(4);
  }

  formatFLOPs(flops) {
    if (flops === undefined || flops === '' || flops === null) return 'N/A';
    const num = typeof flops === 'number' ? flops : parseFloat(flops);
    if (isNaN(num)) return 'N/A';
    return (num / 1e12).toFixed(2) + 'T';
  }

  renderParameterModal() {
    const container = document.querySelector('.modal-container');
    if (!container) return;

    container.innerHTML = `
      <div id="parameter-modal" class="modal" style="display: none;">
        <div class="modal-overlay"></div>
        <div class="modal-content">
          <div class="modal-header">
            <h3>Training Parameters</h3>
            <span class="modal-close">&times;</span>
          </div>
          <div class="modal-body">
            <div id="modal-parameters"></div>
          </div>
        </div>
      </div>
    `;
  }

  showParameterModal(modelName, datasetName) {
    const modal = document.getElementById('parameter-modal');
    const paramsDiv = document.getElementById('modal-parameters');

    const data = this.state.performanceData[modelName]?.[datasetName];
    if (!data) return;

    const params = data.parameters || {};
    const dataset = data.dataset || {};
    const performance = data.performance || {};

    paramsDiv.innerHTML = `
      <h4 style="margin-bottom: 1rem;">${modelName}</h4>
      <h5 style="color: #666; margin-bottom: 1rem;">${datasetName}</h5>

      <h6 style="margin: 1rem 0 0.5rem;">Dataset Info</h6>
      <table class="parameters-table">
        <tr><th>Species</th><td>${dataset.species || 'N/A'}</td></tr>
        <tr><th>Type</th><td>${dataset.type || 'N/A'}</td></tr>
        <tr><th>Labels</th><td>${dataset.labels || 'N/A'}</td></tr>
        <tr><th>Train/Test/Dev</th><td>${dataset.train || 0} / ${dataset.test || 0} / ${dataset.dev || 0}</td></tr>
        <tr><th>Sequence Length</th><td>${dataset.length || 'N/A'}</td></tr>
      </table>

      <h6 style="margin: 1rem 0 0.5rem;">Training Parameters</h6>
      <table class="parameters-table">
        <tr><th>Epochs</th><td>${params.epochs || 'N/A'}</td></tr>
        <tr><th>Steps</th><td>${params.steps || 'N/A'}</td></tr>
        <tr><th>Batch Size</th><td>${params.batch_size || 'N/A'}</td></tr>
        <tr><th>Gradient Accumulation</th><td>${params.gradient_accumulation_steps || 'N/A'}</td></tr>
        <tr><th>Learning Rate</th><td>${params.learning_rate || 'N/A'}</td></tr>
        <tr><th>Warmup</th><td>${params.warmup || 'N/A'}</td></tr>
        <tr><th>LR Scheduler</th><td>${params.lr_scheduler_type || 'N/A'}</td></tr>
        <tr><th>BF16</th><td>${params.bf16 ? 'Yes' : 'No'}</td></tr>
        <tr><th>FP16</th><td>${params.fp16 ? 'Yes' : 'No'}</td></tr>
      </table>

      <h6 style="margin: 1rem 0 0.5rem;">Performance Metrics</h6>
      <table class="parameters-table">
        <tr><th>Loss</th><td>${this.formatValue(performance.loss)}</td></tr>
        <tr><th>Accuracy</th><td>${this.formatValue(performance.accuracy)}</td></tr>
        <tr><th>F1 Score</th><td>${this.formatValue(performance.f1)}</td></tr>
        <tr><th>AUROC</th><td>${this.formatValue(performance.auroc)}</td></tr>
        <tr><th>AUPRC</th><td>${this.formatValue(performance.auprc)}</td></tr>
        <tr><th>MCC</th><td>${this.formatValue(performance.mcc)}</td></tr>
        <tr><th>FLOPs</th><td>${this.formatFLOPs(performance.FLOPs)}</td></tr>
        <tr><th>Runtime (h)</th><td>${this.formatValue(performance.runtime)}</td></tr>
      </table>
    `;

    modal.style.display = 'flex';
  }

  bindEvents() {
    document.getElementById('model-select')?.addEventListener('change', (e) => {
      this.state.selectedModel = e.target.value || null;
      this.renderLeaderboard();
    });

    document.querySelectorAll('.clickable-row').forEach(row => {
      row.addEventListener('click', () => {
        const modelName = row.dataset.model;
        const datasetName = row.dataset.dataset;
        this.showParameterModal(modelName, datasetName);
      });
    });

    document.querySelector('.modal-close')?.addEventListener('click', () => {
      document.getElementById('parameter-modal').style.display = 'none';
    });

    document.querySelector('.modal-overlay')?.addEventListener('click', () => {
      document.getElementById('parameter-modal').style.display = 'none';
    });
  }
}

const app = new FineTuningPage();
export default FineTuningPage;
