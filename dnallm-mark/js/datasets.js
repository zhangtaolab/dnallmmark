/* ========================================
   DNALLM Mark Datasets Page
   数据集页面
   ======================================== */

import CONFIG from './config.js';
import DataAPI from './data.js';

class DatasetsPage {
  constructor() {
    this.state = {
      datasets: new Map(),
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
    console.log('Setting up Datasets page...');

    try {
      await this.loadData();
      this.renderNavbar();
      this.renderHero();
      this.renderDatasetsTable();
      this.bindEvents();

      console.log('Datasets page setup complete!');
    } catch (error) {
      console.error('Failed to setup datasets page:', error);
    }
  }

  async loadData() {
    const performanceData = await DataAPI.loadAllModelPerformance();

    for (const [modelName, modelData] of Object.entries(performanceData)) {
      for (const [datasetName, data] of Object.entries(modelData)) {
        if (!this.state.datasets.has(datasetName)) {
          this.state.datasets.set(datasetName, {
            name: datasetName,
            species: data.dataset?.species || 'N/A',
            type: data.dataset?.type || 'N/A',
            labels: data.dataset?.labels || 'N/A',
            trainSize: data.dataset?.train || 0,
            testSize: data.dataset?.test || 0,
            devSize: data.dataset?.dev || 0,
            length: data.dataset?.length || 'N/A',
            models: []
          });
        }
        this.state.datasets.get(datasetName).models.push(modelName);
      }
    }
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
        <h1>Datasets</h1>
        <p class="hero-subtitle">Benchmark datasets overview</p>
      </section>
    `;
    document.querySelector('.hero-container').innerHTML = heroHTML;
  }

  renderDatasetsTable() {
    const container = document.querySelector('.datasets-container');
    if (!container) return;

    const sortedDatasets = Array.from(this.state.datasets.values()).sort((a, b) => {
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
      <div class="datasets-table-container">
        <table class="datasets-table">
          <thead>
            <tr>
              <th class="sortable" data-sort="name">Dataset Name</th>
              <th class="sortable" data-sort="species">Species</th>
              <th class="sortable" data-sort="type">Task Type</th>
              <th class="sortable" data-sort="labels">Labels</th>
              <th class="sortable" data-sort="trainSize">Train Size</th>
              <th class="sortable" data-sort="testSize">Test Size</th>
              <th class="sortable" data-sort="devSize">Dev Size</th>
              <th class="sortable" data-sort="length">Length</th>
              <th>Models Used</th>
            </tr>
          </thead>
          <tbody>
            ${sortedDatasets.map(ds => `
              <tr>
                <td><strong>${ds.name}</strong></td>
                <td>${ds.species}</td>
                <td>${ds.type}</td>
                <td>${ds.labels}</td>
                <td>${ds.trainSize.toLocaleString()}</td>
                <td>${ds.testSize.toLocaleString()}</td>
                <td>${ds.devSize.toLocaleString()}</td>
                <td>${ds.length}</td>
                <td>${ds.models.length} models</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  bindEvents() {
    document.querySelectorAll('.datasets-table th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const field = th.dataset.sort;
        if (this.state.sortField === field) {
          this.state.sortAscending = !this.state.sortAscending;
        } else {
          this.state.sortField = field;
          this.state.sortAscending = false;
        }
        this.renderDatasetsTable();
      });
    });
  }
}

const app = new DatasetsPage();
export default DatasetsPage;
