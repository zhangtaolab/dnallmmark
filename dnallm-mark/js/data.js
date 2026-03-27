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
    }
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
  },

  /**
   * Recalculate models_comparison.json performance data
   * from model_performance files (frontend implementation)
   * @param {Object} allPerformanceData - All model performance data
   * @returns {Object} Updated comparison data
   */
  recalculateComparison(allPerformanceData) {
    const comparison = {};

    for (const [modelName, perfData] of Object.entries(allPerformanceData)) {
      const datasets = Object.values(perfData);
      if (datasets.length === 0) continue;

      // Calculate metrics
      let sumRank = 0;
      let sumMinmax = 0;
      let sumZscore = 0;
      let sumRobust = 0;
      let sumRaw = 0;
      let count = 0;
      let sumPFLOPs = 0;
      let top1Count = 0;
      let top3Count = 0;
      let top5Count = 0;
      let top10Count = 0;

      // Collect scores for ranking
      const scores = [];
      const flops = [];

      for (const dataset of datasets) {
        const perf = dataset.performance;
        if (perf?.accuracy !== undefined && perf.accuracy !== '') {
          scores.push(perf.accuracy);
          count++;
          sumRaw += perf.accuracy;
        }
        if (perf?.FLOPs !== undefined && perf.FLOPs !== '') {
          flops.push(perf.FLOPs);
          sumPFLOPs += perf.FLOPs / 1e15; // Convert to PFLOPs
        }
      }

      if (count === 0) continue;

      // Calculate average and ranks
      const avgRaw = sumRaw / count;
      const avgPFLOPs = sumPFLOPs / count;

      // Simple ranking based on average score
      const rank = 1; // Will be calculated after all models are processed

      // Count top-N rankings (simplified - would need cross-model comparison)
      top1Count = avgRaw >= 0.9 ? 1 : 0;
      top3Count = avgRaw >= 0.8 ? 1 : 0;
      top5Count = avgRaw >= 0.7 ? 1 : 0;
      top10Count = avgRaw >= 0.6 ? 1 : 0;

      comparison[modelName] = {
        model: {
          name: modelName.split('/').pop().replace('_performance', ''),
          'size (M)': 0,
          type: '',
          tokenizer: '',
          mean_token_len: '',
          architecture: '',
          series: '',
          'context_len (bp)': '',
          species: this.aggregateSpecies(modelName, perfData).join(', '),
          huggingface: '',
          modelscope: ''
        },
        performance: {
          samples: count,
          rank_score: sumRank,
          sum_minmax: sumMinmax,
          sum_zscore: sumZscore,
          sum_robust: sumRobust,
          avg_raw: avgRaw,
          avg_rank: 0,
          top1_count: top1Count,
          top3_count: top3Count,
          top5_count: top5Count,
          top10_count: top10Count,
          sum_PFLOPs: sumPFLOPs,
          avg_PFLOPs: avgPFLOPs,
          rank: rank
        }
      };
    }

    return comparison;
  }
};

// Export for ES6 modules
export default DataAPI;

// Compatible with CommonJS
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DataAPI;
}
