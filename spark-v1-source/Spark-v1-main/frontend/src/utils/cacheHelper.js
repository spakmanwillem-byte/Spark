// Cache helper voor Bitvavo data
// Stale-while-revalidate pattern

const CACHE_DURATION = {
  candles: 5 * 60 * 1000,      // 5 minuten voor candles (historical data)
  portfolio: 30 * 1000,         // 30 seconden voor portfolio (live data)
  balance: 30 * 1000,           // 30 seconden voor balance
};

export const CacheHelper = {
  // Set cache met timestamp
  set: (key, data, type = 'candles') => {
    try {
      const cacheItem = {
        data,
        timestamp: Date.now(),
        type,
      };
      localStorage.setItem(`spark_cache_${key}`, JSON.stringify(cacheItem));
    } catch (err) {
      console.warn('Cache set failed:', err);
    }
  },

  // Get cache (returns null if expired or not found)
  get: (key, allowStale = false) => {
    try {
      const cached = localStorage.getItem(`spark_cache_${key}`);
      if (!cached) return null;

      const { data, timestamp, type } = JSON.parse(cached);
      const age = Date.now() - timestamp;
      const maxAge = CACHE_DURATION[type] || CACHE_DURATION.candles;

      if (age > maxAge && !allowStale) {
        // Cache expired
        return null;
      }

      return {
        data,
        isStale: age > maxAge,
        age,
      };
    } catch (err) {
      console.warn('Cache get failed:', err);
      return null;
    }
  },

  // Clear specific cache
  clear: (key) => {
    try {
      localStorage.removeItem(`spark_cache_${key}`);
    } catch (err) {
      console.warn('Cache clear failed:', err);
    }
  },

  // Clear all Spark caches
  clearAll: () => {
    try {
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith('spark_cache_')) {
          localStorage.removeItem(key);
        }
      });
    } catch (err) {
      console.warn('Cache clearAll failed:', err);
    }
  },
};
