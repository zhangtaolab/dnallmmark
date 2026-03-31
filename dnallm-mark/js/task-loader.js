/**
 * TaskLoader - Intelligent task loading with caching and preloading
 * Manages task data loading with priority queue, localStorage caching,
 * and idle-time preloading of adjacent tasks
 */
class TaskLoader {
  constructor() {
    this.memoryCache = new Map();           // In-memory cache for current session
    this.taskList = null;                   // List of available tasks
    this.maxCacheSize = 10;                 // Maximum number of tasks to cache
    this.cacheKeyPrefix = 'dnallm_task_';   // localStorage key prefix
    this.cacheVersion = '1.0.0';            // Cache version for invalidation
    this.retryAttempts = 3;                 // Number of retry attempts for failed requests
    this.retryDelay = 1000;                 // Delay between retries (ms)
    this.preloadNeighborsCount = 2;         // Number of adjacent tasks to preload
    this.maxCacheAge = 24 * 60 * 60 * 1000; // Cache expiration: 24 hours
  }

  /**
   * Initialize the loader by fetching the task index
   * @returns {Promise<Array>} List of available tasks
   */
  async initialize() {
    if (this.taskList) return this.taskList;
    
    try {
      const response = await fetch('./data/tasks.json');
      if (!response.ok) {
        throw new Error(`Failed to load task index: HTTP ${response.status}`);
      }
      
      const data = await response.json();
      this.taskList = data.tasks;
      console.log(`[TaskLoader] Initialized with ${this.taskList.length} tasks`);
      return this.taskList;
    } catch (error) {
      console.error('[TaskLoader] Initialization failed:', error);
      throw error;
    }
  }

  /**
   * Load a specific task with priority handling
   * High priority: Load immediately with loading indicator
   * @param {string} taskId - Task identifier
   * @returns {Promise<Object>} Task data
   */
  async loadTask(taskId) {
    // Check memory cache first (fastest)
    if (this.memoryCache.has(taskId)) {
      console.log(`[TaskLoader] Task ${taskId} loaded from memory cache`);
      return this.memoryCache.get(taskId);
    }

    // Check localStorage cache
    const cached = this.getFromLocalStorage(taskId);
    if (cached && !this.isCacheExpired(cached)) {
      console.log(`[TaskLoader] Task ${taskId} loaded from localStorage cache`);
      this.memoryCache.set(taskId, cached.data);
      return cached.data;
    }

    // Fetch from network
    console.log(`[TaskLoader] Fetching task ${taskId} from network...`);
    const data = await this.fetchWithRetry(taskId);
    
    // Cache the loaded data
    this.cacheTask(taskId, data);
    
    // Schedule preloading of adjacent tasks
    this.scheduleNeighborPreload(taskId);
    
    return data;
  }

  /**
   * Fetch task data with automatic retry on failure
   * @param {string} taskId - Task identifier
   * @returns {Promise<Object>} Task data
   */
  async fetchWithRetry(taskId) {
    const taskInfo = this.taskList.find(t => t.id === taskId);
    if (!taskInfo) {
      throw new Error(`Task ${taskId} not found in task list`);
    }

    const url = `./data/task_performance/${taskInfo.fileName}`;
    
    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        return data;
      } catch (error) {
        console.warn(
          `[TaskLoader] Attempt ${attempt}/${this.retryAttempts} failed for ${taskId}: ${error.message}`
        );
        
        if (attempt === this.retryAttempts) {
          throw new Error(
            `Failed to load task "${taskId}" after ${this.retryAttempts} attempts. ` +
            `Please check your network connection and try again.`
          );
        }
        
        // Exponential backoff: wait longer between retries
        await this.delay(this.retryDelay * attempt);
      }
    }
  }

  /**
   * Cache task data in both memory and localStorage
   * Implements LRU eviction for memory cache
   * @param {string} taskId - Task identifier
   * @param {Object} data - Task data to cache
   */
  cacheTask(taskId, data) {
    // Memory cache with LRU eviction
    if (this.memoryCache.size >= this.maxCacheSize) {
      // Remove oldest entry (first in Map)
      const firstKey = this.memoryCache.keys().next().value;
      this.memoryCache.delete(firstKey);
      console.log(`[TaskLoader] Evicted oldest cache entry: ${firstKey}`);
    }
    this.memoryCache.set(taskId, data);

    // localStorage cache
    const cacheEntry = {
      data: data,
      timestamp: Date.now(),
      version: this.cacheVersion
    };
    
    try {
      localStorage.setItem(
        this.cacheKeyPrefix + taskId,
        JSON.stringify(cacheEntry)
      );
    } catch (e) {
      // localStorage might be full, clear expired entries and retry
      console.warn('[TaskLoader] localStorage full, clearing expired caches...');
      this.clearExpiredCaches();
      
      try {
        localStorage.setItem(
          this.cacheKeyPrefix + taskId,
          JSON.stringify(cacheEntry)
        );
      } catch (e2) {
        console.error('[TaskLoader] Failed to cache task data:', e2);
      }
    }
  }

  /**
   * Check if cache entry has expired
   * @param {Object} cached - Cache entry with timestamp
   * @returns {boolean} True if expired
   */
  isCacheExpired(cached) {
    return (Date.now() - cached.timestamp) > this.maxCacheAge;
  }

  /**
   * Schedule preloading of adjacent tasks during browser idle time
   * @param {string} currentTaskId - Currently loaded task ID
   */
  scheduleNeighborPreload(currentTaskId) {
    const preloadFn = () => this.preloadNeighbors(currentTaskId);
    
    if (window.requestIdleCallback) {
      // Use requestIdleCallback if available (optimal)
      window.requestIdleCallback(preloadFn, { timeout: 5000 });
    } else {
      // Fallback to setTimeout
      setTimeout(preloadFn, 2000);
    }
  }

  /**
   * Preload adjacent tasks (previous and next N tasks)
   * These tasks are likely to be accessed next by the user
   * @param {string} currentTaskId - Currently loaded task ID
   */
  async preloadNeighbors(currentTaskId) {
    const currentIndex = this.getTaskIndex(currentTaskId);
    if (currentIndex === -1) return;

    // Get adjacent task IDs
    const neighborIds = [];
    for (let offset = 1; offset <= this.preloadNeighborsCount; offset++) {
      const prevIndex = currentIndex - offset;
      const nextIndex = currentIndex + offset;
      
      if (prevIndex >= 0) {
        neighborIds.push(this.taskList[prevIndex].id);
      }
      if (nextIndex < this.taskList.length) {
        neighborIds.push(this.taskList[nextIndex].id);
      }
    }

    console.log(`[TaskLoader] Preloading neighbors of ${currentTaskId}:`, neighborIds);

    // Load neighbors in parallel without blocking
    neighborIds.forEach(async (taskId) => {
      // Skip if already cached
      if (this.memoryCache.has(taskId) || this.getFromLocalStorage(taskId)) {
        return;
      }

      try {
        const data = await this.fetchWithRetry(taskId);
        this.cacheTask(taskId, data);
        console.log(`[TaskLoader] Preloaded neighbor: ${taskId}`);
      } catch (error) {
        console.warn(`[TaskLoader] Failed to preload ${taskId}:`, error.message);
      }
    });
  }

  /**
   * Get task index in the task list
   * @param {string} taskId - Task identifier
   * @returns {number} Index or -1 if not found
   */
  getTaskIndex(taskId) {
    return this.taskList.findIndex(t => t.id === taskId);
  }

  /**
   * Retrieve cached data from localStorage
   * @param {string} taskId - Task identifier
   * @returns {Object|null} Cached entry or null
   */
  getFromLocalStorage(taskId) {
    try {
      const item = localStorage.getItem(this.cacheKeyPrefix + taskId);
      return item ? JSON.parse(item) : null;
    } catch (e) {
      return null;
    }
  }

  /**
   * Clear all expired cache entries from localStorage
   */
  clearExpiredCaches() {
    const keys = Object.keys(localStorage);
    let clearedCount = 0;
    
    keys.forEach(key => {
      if (key.startsWith(this.cacheKeyPrefix)) {
        try {
          const item = JSON.parse(localStorage.getItem(key));
          if (this.isCacheExpired(item)) {
            localStorage.removeItem(key);
            clearedCount++;
          }
        } catch (e) {
          // Invalid cache entry, remove it
          localStorage.removeItem(key);
          clearedCount++;
        }
      }
    });
    
    if (clearedCount > 0) {
      console.log(`[TaskLoader] Cleared ${clearedCount} expired cache entries`);
    }
  }

  /**
   * Utility: Delay function for async/await
   * @param {number} ms - Milliseconds to delay
   * @returns {Promise<void>}
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ============ Debug API (Available in Browser Console) ============

  /**
   * Get cache statistics for debugging
   * @returns {Object} Cache statistics
   */
  getCacheStats() {
    const memoryTasks = Array.from(this.memoryCache.keys());
    let localStorageCount = 0;
    let localStorageSize = 0;

    Object.keys(localStorage).forEach(key => {
      if (key.startsWith(this.cacheKeyPrefix)) {
        localStorageCount++;
        localStorageSize += localStorage.getItem(key).length;
      }
    });

    return {
      memoryCache: {
        count: this.memoryCache.size,
        tasks: memoryTasks,
        maxSize: this.maxCacheSize
      },
      localStorage: {
        count: localStorageCount,
        sizeKB: (localStorageSize / 1024).toFixed(2),
        maxAge: '24 hours'
      }
    };
  }

  /**
   * Clear all caches (memory and localStorage)
   */
  clearAllCaches() {
    const memoryCount = this.memoryCache.size;
    this.memoryCache.clear();
    
    let localStorageCount = 0;
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith(this.cacheKeyPrefix)) {
        localStorage.removeItem(key);
        localStorageCount++;
      }
    });
    
    console.log(
      `[TaskLoader] Cleared all caches: ${memoryCount} memory, ${localStorageCount} localStorage`
    );
  }

  /**
   * Clear cache for specific task
   * @param {string} taskId - Task identifier
   */
  clearTaskCache(taskId) {
    this.memoryCache.delete(taskId);
    localStorage.removeItem(this.cacheKeyPrefix + taskId);
    console.log(`[TaskLoader] Cache cleared for task: ${taskId}`);
  }
}

// Create global instance
window.taskLoader = new TaskLoader();
export default TaskLoader;

// ============ Console Debug API ============

/**
 * Debug utilities accessible via browser console
 * Usage:
 *   DNALLMDebug.cacheStats()     - Show cache statistics
 *   DNALLMDebug.clearCache()     - Clear all caches
 *   DNALLMDebug.clearTask(id)    - Clear specific task cache
 *   DNALLMDebug.preload(id)      - Manually preload a task
 *   DNALLMDebug.tasks()          - Show task list
 */
window.DNALLMDebug = {
  cacheStats: () => {
    const stats = window.taskLoader.getCacheStats();
    console.log('=== DNALLM Cache Statistics ===');
    console.log(`Memory Cache: ${stats.memoryCache.count}/${stats.memoryCache.maxSize} tasks`);
    console.log(`Cached Tasks: ${stats.memoryCache.tasks.join(', ') || 'None'}`);
    console.log(`LocalStorage: ${stats.localStorage.count} entries, ${stats.localStorage.sizeKB} KB`);
    console.log(`Cache Expiration: ${stats.localStorage.maxAge}`);
    console.log('===============================');
    return stats;
  },
  
  clearCache: () => {
    window.taskLoader.clearAllCaches();
  },
  
  clearTask: (taskId) => {
    window.taskLoader.clearTaskCache(taskId);
  },
  
  preload: (taskId) => {
    console.log(`[DNALLMDebug] Preloading task: ${taskId}...`);
    window.taskLoader.loadTask(taskId).then(() => {
      console.log(`[DNALLMDebug] Preload complete: ${taskId}`);
    }).catch(err => {
      console.error(`[DNALLMDebug] Preload failed: ${err.message}`);
    });
  },
  
  tasks: () => {
    const tasks = window.taskLoader.getTaskList();
    console.log('=== Available Tasks ===');
    console.table(tasks.map(t => ({
      ID: t.id,
      Name: t.displayName || t.name,
      Species: t.species,
      Type: t.type,
      Metric: t.metric
    })));
    return tasks;
  }
};

console.log('%c DNALLM Task Loader Initialized ', 'background: #3b82f6; color: white; padding: 4px 8px; border-radius: 4px;');
console.log('Debug functions available:');
console.log('  DNALLMDebug.cacheStats()  - Show cache statistics');
console.log('  DNALLMDebug.clearCache()  - Clear all caches');
console.log('  DNALLMDebug.clearTask(id) - Clear specific task cache');
console.log('  DNALLMDebug.preload(id)   - Manually preload a task');
console.log('  DNALLMDebug.tasks()       - List all available tasks');
