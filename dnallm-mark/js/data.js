/* ========================================
   DNALLM Mark Data Loading Utilities
   ======================================== */

const DataAPI = {
  cache: {
    modelsComparison: null,
    modelPerformance: {},
    modelsComparisonByArena: {
      all: null,
      animal: null,
      plant: null,
      microbe: null
    },
    dataManifest: null
  },

  /**
   * Load models_comparison.json for a specific arena
   * @param {string} arena - 'all', 'animal', 'plant', 'microbe'
   * @returns {Promise<Object>}
   */
  async loadModelsComparisonByArena(arena) {
    const arenaMap = {
      'all': 'models_comparison.json',
      'animal': 'models_comparison_animal.json',
      'plant': 'models_comparison_plant.json',
      'microbe': 'models_comparison_microbe.json'
    };

    const fileName = arenaMap[arena];
    if (!fileName) {
      throw new Error(`Unknown arena: ${arena}`);
    }

    if (this.cache.modelsComparisonByArena[arena]) {
      return this.cache.modelsComparisonByArena[arena];
    }

    try {
      const response = await fetch(`./data/${fileName}`);
      if (!response.ok) {
        throw new Error(`Failed to load ${fileName}: ${response.status}`);
      }
      const data = await response.json();
      this.cache.modelsComparisonByArena[arena] = data;
      return data;
    } catch (error) {
      console.error(`Error loading models comparison for ${arena}:`, error);
      throw error;
    }
  },

  /**
   * Load models_comparison.json
   * @returns {Promise<Object>}
   */
  async loadModelsComparison() {
    if (this.cache.modelsComparison) {
      return this.cache.modelsComparison;
    }

    try {
      const response = await fetch('./data/models_comparison.json');
      if (!response.ok) {
        throw new Error(`Failed to load models_comparison.json: ${response.status}`);
      }
      const data = await response.json();
      this.cache.modelsComparison = data;
      return data;
    } catch (error) {
      console.error('Error loading models comparison:', error);
      throw error;
    }
  },

  /**
   * Load the data-version manifest (data/manifest.json) — the STAMPED date +
   * data_version the leaderboard footer renders (DATA-06, D-17/OQ2).
   * Cached like every other fetch; a failed fetch throws so the caller can
   * hide the stamp entirely — the footer never falls back to a client-derived
   * value (no live clock).
   * @returns {Promise<Object>}
   */
  async loadDataManifest() {
    if (this.cache.dataManifest) {
      return this.cache.dataManifest;
    }

    try {
      const response = await fetch('./data/manifest.json');
      if (!response.ok) {
        throw new Error(`Failed to load manifest.json: ${response.status}`);
      }
      const data = await response.json();
      this.cache.dataManifest = data;
      return data;
    } catch (error) {
      console.error('Error loading data manifest:', error);
      throw error;
    }
  },

  /**
   * Load model performance JSON for a specific model
   * @param {string} modelName - Model name (file name without _performance.json)
   * @returns {Promise<Object>}
   */
  async loadModelPerformance(modelName) {
    if (this.cache.modelPerformance[modelName]) {
      return this.cache.modelPerformance[modelName];
    }

    try {
      const fileName = `${modelName}_performance.json`;
      const response = await fetch(`./data/model_performance/${fileName}`);
      if (!response.ok) {
        throw new Error(`Failed to load ${fileName}: ${response.status}`);
      }
      const data = await response.json();
      this.cache.modelPerformance[modelName] = data;
      return data;
    } catch (error) {
      console.error(`Error loading performance for ${modelName}:`, error);
      throw error;
    }
  },

  /**
   * Load all model performance files
   * @returns {Promise<Map<string, Object>>}
   */
  async loadAllModelPerformance() {
    try {
      // Load models_comparison to get model list
      const comparison = await this.loadModelsComparison();
      const modelNames = Object.keys(comparison);

      const results = {};
      for (const modelName of modelNames) {
        try {
          results[modelName] = await this.loadModelPerformance(modelName);
        } catch (error) {
          console.warn(`No performance data for ${modelName}`);
        }
      }
      return results;
    } catch (error) {
      console.error('Error loading all model performance:', error);
      return {};
    }
  },

  /**
   * Aggregate species from model performance data
   * @param {string} modelName - Model name
   * @param {Object} performanceData - Performance data
   * @returns {string[]} Array of unique species
   */
  aggregateSpecies(modelName, performanceData) {
    if (!performanceData) return [];

    const speciesSet = new Set();
    for (const dataset of Object.values(performanceData)) {
      if (dataset.dataset?.species) {
        speciesSet.add(dataset.dataset.species);
      }
    }
    return Array.from(speciesSet);
  },

  /**
   * Normalize species name to arena category
   * @param {string} species - Raw species name
   * @returns {string} Arena category (animal, plant, microbe)
   */
  normalizeToArena(species) {
    const speciesLower = species.toLowerCase();
    if (speciesLower.includes('animal') || speciesLower.includes('human') ||
        speciesLower.includes('mouse') || speciesLower.includes('rat')) {
      return 'animal';
    }
    if (speciesLower.includes('plant') || speciesLower.includes('arabidopsis') ||
        speciesLower.includes('rice') || speciesLower.includes('maize')) {
      return 'plant';
    }
    if (speciesLower.includes('microbe') || speciesLower.includes('bacteria') ||
        speciesLower.includes('yeast') || speciesLower.includes('ecoli')) {
      return 'microbe';
    }
    return 'all';
  },

  /**
   * Escape a string for safe interpolation into innerHTML template literals
   * (FIX-04, bounded scope: applied at the DOM-build sites the fix touches —
   * shared navbar, submit-page user-entered fields, touched task renderers)
   * @param {*} str - Value to escape
   * @returns {*} The escaped string, or the input unchanged when not a string
   */
  escapeHTML(str) {
    if (typeof str !== 'string') return str;
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  /**
   * Get color for model based on its index or name
   * @param {string} modelName - Model name
   * @param {number} index - Model index
   * @returns {string} Color hex code
   */
  getColorForModel(modelName, index = 0) {
    const colorPalette = [
      '#F97316', '#06B6D4', '#8B5CF6', '#10B981', '#EF4444',
      '#F59E0B', '#EC4899', '#14B8A6', '#3B82F6', '#A855F7',
      '#64748B', '#1E40AF', '#7C3AED', '#059669', '#0891B2'
    ];
    return colorPalette[index % colorPalette.length];
  }
};

// Export for ES6 modules
export default DataAPI;

// Compatible with CommonJS
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DataAPI;
}
