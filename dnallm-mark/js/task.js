/* ========================================
   DNALLM Mark Task Benchmark Page
   ======================================== */

import DataAPI from './data.js';

/**
 * LoadingController - Manages loading overlay UI
 * Controls visibility, text updates, and error states
 */
class LoadingController {
  constructor() {
    this.overlay = document.getElementById('task-loading');
    this.taskNameEl = document.getElementById('loading-task-name');
    this.statusEl = document.getElementById('loading-status');
    this.errorEl = document.getElementById('loading-error');
    this.retryBtn = document.getElementById('loading-retry');
    
    this.retryCallback = null;
    
    // Bind retry button click
    this.retryBtn.addEventListener('click', () => {
      if (this.retryCallback) {
        this.retryCallback();
      }
    });
  }

  /**
   * Show loading overlay for network fetch
   * @param {string} taskName - Name of task being loaded
   */
  show(taskName) {
    this.taskNameEl.textContent = taskName;
    this.statusEl.textContent = 'Downloading data...';
    this.statusEl.className = 'task-loading-status loading';
    this.errorEl.classList.remove('visible');
    this.retryBtn.disabled = true;
    this.overlay.classList.add('active');
  }

  /**
   * Show loading overlay for cache read (faster)
   * @param {string} taskName - Name of task being loaded
   */
  showCached(taskName) {
    this.taskNameEl.textContent = taskName;
    this.statusEl.textContent = 'Loading from cache...';
    this.statusEl.className = 'task-loading-status cached';
    this.errorEl.classList.remove('visible');
    this.overlay.classList.add('active');
    
    // Auto-hide after short delay since cache is fast
    setTimeout(() => this.hide(), 300);
  }

  /**
   * Hide loading overlay
   */
  hide() {
    this.overlay.classList.remove('active');
    
    // Reset state after animation completes
    setTimeout(() => {
      this.statusEl.className = 'task-loading-status';
      this.statusEl.textContent = '';
      this.errorEl.classList.remove('visible');
    }, 300);
  }

  /**
   * Show error state with retry option
   * @param {string} message - Error message
   * @param {Function} retryCallback - Function to call on retry
   */
  showError(message, retryCallback) {
    this.statusEl.textContent = message || 'Failed to load task data';
    this.statusEl.className = 'task-loading-status error';
    this.errorEl.classList.add('visible');
    this.retryBtn.disabled = false;
    this.retryCallback = retryCallback;
  }

  /**
   * Update status text
   * @param {string} message - Status message
   */
  updateStatus(message) {
    this.statusEl.textContent = message;
  }
}

// Create global instance
window.loadingController = new LoadingController();

class TaskBenchmark {
  constructor() {
    this.state = {
      currentTask: null,
      currentMetric: null,
      sortDirection: 'desc',
      taskList: [],
      taskData: null,
      models: [],
      chart: null
    };

    // Metrics that should be sorted ascending (lower = better)
    this.ascendingMetrics = new Set([
      'FLOPs', 'runtime', 'loss', 'mse', 'MAE'
    ]);

    // Use global instances from task-loader.js
    this.loader = window.taskLoader;
    this.loading = window.loadingController;

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
    console.log('Setting up Task Benchmark...');

    try {
      // Initialize task loader and load lightweight task index (~5KB)
      this.state.taskList = await this.loader.initialize();
      
      // Render UI immediately
      this.renderHero();
      this.populateTaskDropdown();
      this.bindEvents();

      // Auto-select first task
      if (this.state.taskList.length > 0) {
        const firstTask = this.state.taskList[0];
        document.getElementById('task-select').value = firstTask.id;
        await this.handleTaskChange(firstTask.id);
      }

      console.log('Task Benchmark setup complete!');
    } catch (error) {
      console.error('Failed to setup task benchmark:', error);
      alert('Initialization failed. Please refresh the page and try again.');
    }
  }

  renderHero() {
    const heroHTML = `
      <section class="hero">
        <h1>Task Benchmark</h1>
        <p class="hero-subtitle">Compare model performance on individual tasks</p>
      </section>
    `;
    document.querySelector('.hero-container').innerHTML = heroHTML;
  }

  populateTaskDropdown() {
    const taskSelect = document.getElementById('task-select');
    if (!taskSelect) return;

    if (this.state.taskList.length === 0) {
      taskSelect.innerHTML = '<option value="">No tasks found</option>';
      return;
    }

    const options = this.state.taskList.map(task => {
      const displayName = task.displayName || task.name || task.id;
      return `<option value="${task.id}">${displayName}</option>`;
    });

    taskSelect.innerHTML = '<option value="">Select a task...</option>' + options.join('');
  }

  populateMetricDropdown(taskData) {
    const metricSelect = document.getElementById('metric-select');
    if (!metricSelect) return;

    // Get available metrics from the first model's performance data
    const firstModelKey = Object.keys(taskData.performance)[0];
    const firstModelPerf = taskData.performance[firstModelKey]?.performance;

    if (!firstModelPerf) {
      metricSelect.innerHTML = '<option value="">No metrics available</option>';
      return;
    }

    // Get all available metrics (non-empty values)
    const availableMetrics = Object.entries(firstModelPerf)
      .filter(([_, value]) => value !== '' && value !== undefined && value !== null)
      .map(([key, _]) => key);

    // Determine default metric
    const defaultMetric = taskData.info?.metric || 'accuracy';

    // Build metric options with sort direction indicators
    const options = availableMetrics.map(metric => {
      const isAscending = this.ascendingMetrics.has(metric);
      const direction = isAscending ? '↓' : '↑';
      const label = this.formatMetricName(metric);
      return `<option value="${metric}" ${metric === defaultMetric ? 'selected' : ''}>${label} ${direction}</option>`;
    });

    metricSelect.innerHTML = options.join('');

    // Set current metric to default
    this.state.currentMetric = defaultMetric;

    // Update sort direction based on default metric
    this.state.sortDirection = this.ascendingMetrics.has(defaultMetric) ? 'asc' : 'desc';
    this.updateSortToggle();
  }

  formatMetricName(metric) {
    const metricNames = {
      'FLOPs': 'FLOPs',
      'runtime': 'Runtime',
      'loss': 'Loss',
      'accuracy': 'Accuracy',
      'precision': 'Precision',
      'recall': 'Recall',
      'f1': 'F1 Score',
      'mcc': 'MCC',
      'auroc': 'AUROC',
      'auprc': 'AUPRC',
      'pearson_r': 'Pearson R',
      'spearman_r': 'Spearman R',
      'mse': 'MSE',
      'r2': 'R²'
    };
    return metricNames[metric] || metric;
  }

  extractModels(taskData) {
    const models = [];

    // Create a case-insensitive lookup for the current metric
    const firstModelKey = Object.keys(taskData.performance)[0];
    const firstModelPerf = taskData.performance[firstModelKey]?.performance;

    // Find the actual metric key (case-insensitive)
    let actualMetricKey = this.state.currentMetric;
    if (firstModelPerf && !(this.state.currentMetric in firstModelPerf)) {
      const lowercaseMetric = this.state.currentMetric.toLowerCase();
      for (const [key, value] of Object.entries(firstModelPerf)) {
        if (key.toLowerCase() === lowercaseMetric) {
          actualMetricKey = key;
          break;
        }
      }
    }

    for (const [modelName, modelData] of Object.entries(taskData.performance)) {
      const perf = modelData.performance;
      const model = modelData.model;

      // Get the current metric value (using case-insensitive key)
      const metricValue = perf[actualMetricKey];

      // Skip models with empty/invalid metric values
      if (metricValue === '' || metricValue === undefined || metricValue === null) {
        continue;
      }

      models.push({
        key: modelName,
        name: model?.name || modelName,
        size: model?.['size (M)'] || 0,
        metricValue: parseFloat(metricValue),
        flops: perf.FLOPs !== '' ? (perf.FLOPs / 1e15).toFixed(4) : 'N/A',
        runtime: perf.runtime !== '' ? perf.runtime.toFixed(2) : 'N/A',
        color: DataAPI.getColorForModel(modelName, models.length),
        icon: modelName.charAt(0).toUpperCase()
      });
    }

    return models;
  }

  sortModels(models) {
    const isAscending = this.state.sortDirection === 'asc';

    models.sort((a, b) => {
      if (isAscending) {
        return a.metricValue - b.metricValue;
      } else {
        return b.metricValue - a.metricValue;
      }
    });

    // Add rank to each model
    models.forEach((model, index) => {
      model.displayRank = index + 1;
    });

    this.state.models = models;
  }

  renderTaskInfo(taskData) {
    const banner = document.getElementById('task-info-banner');
    if (!banner) return;

    banner.style.display = 'block';

    document.getElementById('info-species').textContent = taskData.info?.species || '-';
    document.getElementById('info-type').textContent = taskData.info?.type || '-';
    document.getElementById('info-labels').textContent = taskData.info?.labels || '-';
    document.getElementById('info-length').textContent = taskData.info?.length || '-';
    document.getElementById('info-metric').textContent = this.formatMetricName(taskData.info?.metric || '-');
  }



  renderBarChart() {
    const canvas = document.getElementById('barChart');
    if (!canvas) return;

    if (this.state.chart) {
      this.state.chart.destroy();
    }

    const models = this.state.models;
    const metricName = this.formatMetricName(this.state.currentMetric);
    const isAscending = this.state.sortDirection === 'asc';

    // Sort for display (best at top)
    const displayModels = [...models].sort((a, b) => {
      if (isAscending) {
        return a.metricValue - b.metricValue;
      } else {
        return b.metricValue - a.metricValue;
      }
    });

    const datasets = {
      labels: displayModels.map(m => m.name),
      datasets: [{
        label: metricName,
        data: displayModels.map(m => m.metricValue),
        backgroundColor: displayModels.map(m => m.color + '99'),
        borderColor: displayModels.map(m => m.color),
        borderWidth: 1
      }]
    };

    const config = {
      type: 'bar',
      data: datasets,
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        barPercentage: 0.6,
        categoryPercentage: 0.7,
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
              title: (context) => context[0].label,
              label: (context) => {
                const value = context.raw;
                return `${metricName}: ${typeof value === 'number' ? value.toFixed(4) : value}`;
              }
            }
          }
        },
        scales: {
          x: {
            ticks: { color: '#595F6E' },
            grid: { color: '#E0E0E0', borderDash: [5, 5], drawBorder: false }
          },
          y: {
            ticks: { 
              color: '#595F6E',
              autoSkip: false,
              maxRotation: 0,
              font: {
                size: 11
              }
            },
            grid: { color: '#E0E0E0', borderDash: [5, 5], drawBorder: false }
          }
        },
        layout: {
          padding: {
            left: 20
          }
        }
      }
    };

    this.state.chart = new Chart(canvas, config);
  }



  renderLeaderboard() {
    const tbody = document.getElementById('leaderboard-body');
    const sortMetric = document.getElementById('sort-metric');
    const metricHeader = document.getElementById('metric-header');

    if (!tbody) return;

    const metricName = this.formatMetricName(this.state.currentMetric);
    if (sortMetric) sortMetric.textContent = metricName;
    if (metricHeader) metricHeader.textContent = metricName;

    const rows = this.state.models.map(model => {
      const rankClass = model.displayRank <= 3 ? `rank-${model.displayRank}` : 'rank-default';

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
                <div class="model-name">${model.name}</div>
              </div>
            </div>
          </td>
          <td>
            <span class="rank-value">${model.size}</span>
          </td>
          <td>
            <span class="rank-value">${typeof model.metricValue === 'number' ? model.metricValue.toFixed(4) : model.metricValue}</span>
          </td>
          <td>
            <span class="flops-value">${model.flops}</span>
          </td>
          <td>
            <span class="flops-value">${model.runtime}</span>
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = rows.join('');
  }

  updateSortToggle() {
    const buttons = document.querySelectorAll('.sort-btn');
    buttons.forEach(btn => {
      const direction = btn.dataset.direction;
      if (direction === this.state.sortDirection) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  async handleTaskChange(taskId) {
    if (!taskId) {
      this.resetUI();
      return;
    }

    const taskInfo = this.state.taskList.find(t => t.id === taskId);
    if (!taskInfo) {
      console.error('Task not found:', taskId);
      return;
    }

    const displayName = taskInfo.displayName || taskInfo.name || taskId;
    
    // Show loading overlay
    this.loading.show(displayName);

    try {
      // Load task data with caching and preloading
      const taskData = await this.loader.loadTask(taskId);
      
      // Update state
      this.state.currentTask = taskId;
      this.state.taskData = taskData;
      
      // Render task data
      this.renderTaskInfo(taskData);
      this.populateMetricDropdown(taskData);
      await this.handleMetricChange(this.state.currentMetric || taskData.info?.metric || 'f1');
      
      // Hide loading overlay
      this.loading.hide();
      
    } catch (error) {
      console.error('Error loading task:', error);
      this.loading.showError(
        `Failed to load task: ${error.message}`,
        () => this.handleTaskChange(taskId) // Retry callback
      );
    }
  }

  resetUI() {
    this.state.taskData = null;
    this.state.models = [];
    this.state.currentMetric = null;
    
    document.getElementById('metric-select').innerHTML = '<option value="">Select a task first</option>';
    document.getElementById('leaderboard-body').innerHTML = `
      <tr>
        <td colspan="6" style="text-align: center; padding: 40px;">Select a task to view rankings</td>
      </tr>
    `;
    document.getElementById('task-info-banner').style.display = 'none';
    
    if (this.state.chart) {
      this.state.chart.destroy();
    }
  }

  async handleMetricChange(metric) {
    if (!metric) return;

    this.state.currentMetric = metric;

    // Update sort direction based on metric type
    this.state.sortDirection = this.ascendingMetrics.has(metric) ? 'asc' : 'desc';
    this.updateSortToggle();

    // Extract and sort models
    const models = this.extractModels(this.state.taskData);
    this.sortModels(models);

    // Render visualizations
    this.renderBarChart();
    this.renderLeaderboard();
  }

  handleSortToggle(direction) {
    if (this.state.sortDirection === direction) return;

    this.state.sortDirection = direction;

    if (this.state.models.length > 0) {
      this.sortModels(this.state.models);
      this.renderBarChart();
      this.renderLeaderboard();
    }
    this.updateSortToggle();
  }

  bindEvents() {
    // Task selection
    document.getElementById('task-select')?.addEventListener('change', (e) => {
      this.handleTaskChange(e.target.value);
    });

    // Metric selection
    document.getElementById('metric-select')?.addEventListener('change', (e) => {
      this.handleMetricChange(e.target.value);
    });

    // Sort direction toggle
    document.getElementById('sort-toggle')?.addEventListener('click', (e) => {
      const btn = e.target.closest('.sort-btn');
      if (btn) {
        this.handleSortToggle(btn.dataset.direction);
      }
    });
  }
}

const app = new TaskBenchmark();
export default TaskBenchmark;
