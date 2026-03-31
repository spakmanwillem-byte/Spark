/**
 * API Configuration met Auto-connect
 * 
 * Detecteert automatisch of app draait in:
 * - Production (deployed op Emergent/Kubernetes)
 * - Development (localhost)
 * 
 * Fallback: Als env variable niet bestaat, gebruik localhost
 */

/**
 * Get Backend URL met auto-detection
 * 
 * Priority:
 * 1. REACT_APP_BACKEND_URL env variable (production)
 * 2. Fallback: localhost:8001 (development)
 * 
 * @returns {string} Backend base URL
 */
export const getBackendUrl = () => {
  // Check environment variable
  const envUrl = process.env.REACT_APP_BACKEND_URL;
  
  if (envUrl && envUrl.trim() !== '') {
    // Production: gebruik env variable
    console.log('[API Config] Using production URL:', envUrl);
    return envUrl.trim();
  }
  
  // Development: fallback naar localhost
  const fallbackUrl = 'http://localhost:8001';
  console.log('[API Config] Using development fallback:', fallbackUrl);
  return fallbackUrl;
};

/**
 * Get API base URL (backend URL + /api prefix)
 * 
 * @returns {string} API base URL
 */
export const getApiUrl = () => {
  return `${getBackendUrl()}/api`;
};

/**
 * Check if running in development mode
 * 
 * @returns {boolean} True if development
 */
export const isDevelopment = () => {
  return !process.env.REACT_APP_BACKEND_URL || 
         process.env.NODE_ENV === 'development';
};

/**
 * Check if running in production mode
 * 
 * @returns {boolean} True if production
 */
export const isProduction = () => {
  return !isDevelopment();
};

// Export configured URLs
export const BACKEND_URL = getBackendUrl();
export const API_URL = getApiUrl();

// Log configuratie bij app start
console.log('='.repeat(60));
console.log('[API Config] Environment:', isDevelopment() ? 'DEVELOPMENT' : 'PRODUCTION');
console.log('[API Config] Backend URL:', BACKEND_URL);
console.log('[API Config] API URL:', API_URL);
console.log('='.repeat(60));
