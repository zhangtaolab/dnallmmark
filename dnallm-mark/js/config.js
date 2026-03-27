/* ========================================
   DNALLM Mark Configuration
   ======================================== */

const CONFIG = {
  // Application info
  APP_NAME: 'DNALLM Mark',
  APP_DESCRIPTION: 'DNA LLM benchmarking. Every task, one benchmark.',

  // Arena categories (by species type)
  ARENAS: [
    { id: 'all', name: 'ALL', icon: '🏆', description: 'All DNA models' },
    { id: 'animal', name: 'Animal', icon: '🐾', description: 'Animal genome models' },
    { id: 'plant', name: 'Plant', icon: '🌱', description: 'Plant genome models' },
    { id: 'microbe', name: 'Microbe', icon: '🦠', description: 'Microbe genome models' }
  ],

  // Sort options
  SORT_OPTIONS: [
    { id: 'score', name: 'Score', ascending: false },
    { id: 'win-rate', name: 'Win Rate', ascending: false },
    { id: 'battles', name: 'Battles', ascending: false },
    { id: 'name', name: 'Name', ascending: true }
  ],

  // Filter options
  FILTER_OPTIONS: [
    { id: 'all', name: 'All Models' },
    { id: 'top-20', name: 'Top 20' },
    { id: 'top-10', name: 'Top 10' }
  ],

  // Ranking display options
  RANKING_DISPLAY: {
    SHOW_RANKINGS: true,
    SHOW_ELO: true,
    SHOW_WIN_RATE: true,
    SHOW_BATTLES: true,
    SHOW_CONFIDENCE: true
  },

  // Table config
  TABLE_CONFIG: {
    ROWS_PER_PAGE: 20,
    DEFAULT_SORT: 'elo',
    DEFAULT_FILTER: 'top-20'
  },

  // Nav links (active state is set dynamically based on current page)
  NAV_LINKS: [
    { name: 'Leaderboards', url: '/' },
    { name: 'Task Benchmark', url: '/task.html' },
    { name: 'Fine-tuning', url: '/finetuning.html' },
    { name: 'Models', url: '/models.html' },
    { name: 'Datasets', url: '/datasets.html' },
    { name: 'Submit', url: '/submit.html' }
  ],

  // Social links
  SOCIAL_LINKS: {
    discord: 'https://discord.com/invite/Bw9Ajcb3pR',
    twitter: 'https://twitter.com/dnallm_mark',
    linkedin: 'https://linkedin.com/company/dnallm-mark'
  },

  // API config (reserved)
  API: {
    BASE_URL: 'https://api.dnallm-mark.com',
    ENDPOINTS: {
      MODELS: '/models',
      RANKINGS: '/rankings',
      ARENAS: '/arenas'
    }
  },

  // Development mode
  DEV_MODE: true,

  // Debug mode
  DEBUG: false,

  // Scatter chart config
  SCATTER_CONFIG: {
    HOME: {
      xAxis: 'sum_PFLOPs',
      yAxis: 'rank_score',
      xAxisLabel: 'Sum PFLOPs (lower = more efficient)',
      yAxisLabel: 'Rank Score (higher = better)'
    },
    FINETUNING: {
      defaultX: 'FLOPs',
      defaultY: 'accuracy',
      availableMetrics: [
        'FLOPs', 'accuracy', 'precision', 'recall', 'f1',
        'mcc', 'auroc', 'auprc', 'loss', 'runtime'
      ]
    }
  }
};

// 导出配置（ES6 模块语法）
export default CONFIG;

// 兼容 CommonJS
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CONFIG;
}
