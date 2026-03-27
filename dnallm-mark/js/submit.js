/* ========================================
   DNALLM Mark Submit Data Page
   数据提交页面
   ======================================== */

import CONFIG from './config.js';

class SubmitPage {
  constructor() {
    this.state = {
      uploadedFile: null,
      parsedData: null,
      submitterName: '',
      submitterEmail: '',
      modelName: ''
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

  setup() {
    console.log('Setting up Submit page...');

    this.renderNavbar();
    this.renderHero();
    this.renderUploadForm();
    this.bindEvents();

    console.log('Submit page setup complete!');
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
        <h1>Submit Data</h1>
        <p class="hero-subtitle">Contribute model performance data to the benchmark</p>
      </section>
    `;
    document.querySelector('.hero-container').innerHTML = heroHTML;
  }

  renderUploadForm() {
    const container = document.querySelector('.submit-container');
    if (!container) return;

    container.innerHTML = `
      <div class="upload-form-container">
        <form id="submit-form" class="submit-form">
          <div class="form-group">
            <label for="model-name">Model Name *</label>
            <input
              type="text"
              id="model-name"
              name="modelName"
              required
              placeholder="e.g., ModernBERT-DNA-v1-37M-hg38"
            >
          </div>

          <div class="form-group">
            <label for="json-file">Performance JSON File *</label>
            <input
              type="file"
              id="json-file"
              name="jsonFile"
              accept=".json"
              required
            >
            <small>File must match model_performance format</small>
          </div>

          <div class="form-group">
            <label for="submitter-name">Submitter Name *</label>
            <input
              type="text"
              id="submitter-name"
              name="submitterName"
              required
              placeholder="Your full name"
            >
          </div>

          <div class="form-group">
            <label for="submitter-email">Submitter Email *</label>
            <input
              type="email"
              id="submitter-email"
              name="submitterEmail"
              required
              placeholder="your.email@example.com"
            >
          </div>

          <button type="submit" class="btn btn-primary">Preview Submission</button>
        </form>

        <div id="preview-container" class="preview-container" style="display: none;">
          <h3>Preview</h3>
          <div id="preview-content"></div>
          <div class="preview-actions">
            <button id="confirm-submit" class="btn btn-success">Generate PR Instructions</button>
            <button id="edit-submission" class="btn btn-secondary">Edit</button>
          </div>
        </div>

        <div id="status-message" class="status-message"></div>
      </div>
    `;
  }

  renderPreview(data) {
    const previewContainer = document.getElementById('preview-container');
    const previewContent = document.getElementById('preview-content');

    if (!previewContainer || !previewContent) return;

    const datasetCount = Object.keys(data).length;
    const firstDataset = Object.values(data)[0];
    const firstDatasetName = Object.keys(data)[0];

    previewContent.innerHTML = `
      <div class="preview-summary">
        <h4>Submission Summary</h4>
        <ul>
          <li><strong>Model Name:</strong> ${this.state.modelName}</li>
          <li><strong>Dataset Count:</strong> ${datasetCount}</li>
          <li><strong>Submitter:</strong> ${this.state.submitterName}</li>
          <li><strong>Email:</strong> ${this.state.submitterEmail}</li>
        </ul>
      </div>

      <h4>Sample Dataset: ${firstDatasetName}</h4>
      <table class="preview-table">
        <tr><th>Field</th><th>Value</th></tr>
        <tr><th>Species</th><td>${firstDataset.dataset?.species || 'N/A'}</td></tr>
        <tr><th>Type</th><td>${firstDataset.dataset?.type || 'N/A'}</td></tr>
        <tr><th>Labels</th><td>${firstDataset.dataset?.labels || 'N/A'}</td></tr>
        <tr><th>Train/Test/Dev</th><td>${firstDataset.dataset?.train || 0} / ${firstDataset.dataset?.test || 0} / ${firstDataset.dataset?.dev || 0}</td></tr>
        <tr><th>Accuracy</th><td>${firstDataset.performance?.accuracy || 'N/A'}</td></tr>
        <tr><th>F1</th><td>${firstDataset.performance?.f1 || 'N/A'}</td></tr>
        <tr><th>AUROC</th><td>${firstDataset.performance?.auroc || 'N/A'}</td></tr>
      </table>
    `;

    previewContainer.style.display = 'block';
  }

  validateJSON(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          const parsed = JSON.parse(e.target.result);

          if (typeof parsed !== 'object' || parsed === null) {
            reject(new Error('JSON must be an object'));
            return;
          }

          const keys = Object.keys(parsed);
          if (keys.length === 0) {
            reject(new Error('JSON must contain at least one dataset'));
            return;
          }

          for (const [key, value] of Object.entries(parsed)) {
            if (!value.dataset || !value.performance) {
              reject(new Error(`Dataset "${key}" missing required fields (dataset, performance)`));
              return;
            }
          }

          resolve(parsed);
        } catch (error) {
          reject(new Error(`Invalid JSON: ${error.message}`));
        }
      };

      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }

  generatePRInstructions() {
    const statusDiv = document.getElementById('status-message');
    const safeModelName = this.state.modelName.replace(/[^a-zA-Z0-9_-]/g, '-');
    const branchName = `submit-${safeModelName}-${Date.now()}`;

    statusDiv.innerHTML = `
      <div class="pr-instructions">
        <h3>PR Generation Instructions</h3>

        <p>To submit your data, please follow these steps:</p>

        <ol>
          <li>
            <strong>Create a new branch:</strong>
            <pre>git checkout -b ${branchName}</pre>
          </li>

          <li>
            <strong>Save your JSON file to:</strong>
            <pre>data/model_performance/${safeModelName}_performance.json</pre>
          </li>

          <li>
            <strong>Commit your changes:</strong>
            <pre>git add data/model_performance/${safeModelName}_performance.json
git commit -m "data: Add performance data for ${this.state.modelName}

Submitted by: ${this.state.submitterName}
Email: ${this.state.submitterEmail}"</pre>
          </li>

          <li>
            <strong>Push and create PR:</strong>
            <pre>git push origin ${branchName}</pre>
            Then go to GitHub and create a Pull Request.
          </li>
        </ol>

        <div class="submission-info">
          <h4>Submission Details</h4>
          <ul>
            <li><strong>Model:</strong> ${this.state.modelName}</li>
            <li><strong>Submitter:</strong> ${this.state.submitterName}</li>
            <li><strong>Email:</strong> ${this.state.submitterEmail}</li>
            <li><strong>Datasets:</strong> ${Object.keys(this.state.parsedData || {}).length} datasets</li>
          </ul>
        </div>

        <p class="note">
          <strong>Note:</strong> After your PR is merged, the models_comparison.json will be recalculated
          to include your model's performance in the main leaderboard.
        </p>
      </div>
    `;
  }

  bindEvents() {
    const form = document.getElementById('submit-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const formData = new FormData(form);
      this.state.modelName = formData.get('modelName');
      this.state.submitterName = formData.get('submitterName');
      this.state.submitterEmail = formData.get('submitterEmail');

      const file = formData.get('jsonFile');

      try {
        const parsed = await this.validateJSON(file);
        this.state.parsedData = parsed;
        this.renderPreview(parsed);
      } catch (error) {
        const statusDiv = document.getElementById('status-message');
        statusDiv.innerHTML = `<p class="status-error">Validation Error: ${error.message}</p>`;
      }
    });

    document.getElementById('confirm-submit')?.addEventListener('click', () => {
      this.generatePRInstructions();
    });

    document.getElementById('edit-submission')?.addEventListener('click', () => {
      document.getElementById('preview-container').style.display = 'none';
      document.getElementById('status-message').innerHTML = '';
    });
  }
}

const app = new SubmitPage();
export default SubmitPage;
