import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Auth API Module
 * Alle auth-gerelateerde API calls
 */
export const AuthAPI = {
  /**
   * Login met naam en sleutelwoord
   */
  login: async (naam, sleutelwoord, masterkey = null) => {
    const response = await axios.post(`${API}/auth/login`, {
      naam,
      sleutelwoord,
      masterkey
    });
    return response.data;
  },

  /**
   * Logout
   */
  logout: async (userId) => {
    const response = await axios.post(`${API}/auth/logout?user_id=${userId}`);
    return response.data;
  },

  /**
   * Session heartbeat - houdt sessie actief
   */
  heartbeat: async (userId) => {
    const response = await axios.post(`${API}/auth/session/heartbeat?user_id=${userId}`);
    return response.data;
  },

  /**
   * Valideer sessie
   */
  validateSession: async (userId) => {
    const response = await axios.get(`${API}/auth/session/validate?user_id=${userId}`);
    return response.data;
  },

  /**
   * Haal alle users op
   */
  getUsers: async () => {
    const response = await axios.get(`${API}/auth/users`);
    return response.data;
  },

  /**
   * Haal specifieke user op
   */
  getUser: async (userId) => {
    const response = await axios.get(`${API}/auth/users/${userId}`);
    return response.data;
  },

  /**
   * Maak nieuwe user aan
   */
  createUser: async (naam, sleutelwoord, volledigeNaam = null) => {
    const response = await axios.post(`${API}/auth/users`, {
      naam,
      sleutelwoord,
      volledige_naam: volledigeNaam
    });
    return response.data;
  },

  /**
   * Update user
   */
  updateUser: async (userId, updates) => {
    const response = await axios.put(`${API}/auth/users/${userId}`, updates);
    return response.data;
  },

  /**
   * Verwijder user (admin user-001 is beschermd)
   */
  deleteUser: async (userId) => {
    const response = await axios.delete(`${API}/auth/users/${userId}`);
    return response.data;
  },

  /**
   * Reset sleutelwoord van user (default: Welkom01)
   */
  resetPassword: async (userId, newSleutelwoord = null) => {
    const url = newSleutelwoord
      ? `${API}/auth/users/${userId}/reset-password?new_sleutelwoord=${encodeURIComponent(newSleutelwoord)}`
      : `${API}/auth/users/${userId}/reset-password`;
    const response = await axios.post(url);
    return response.data;
  },

  /**
   * Haal gradaties op
   */
  getGradaties: async () => {
    const response = await axios.get(`${API}/auth/gradaties`);
    return response.data;
  },

  /**
   * Update user gradatie
   */
  updateGradatie: async (userId, gradatie, reden = '') => {
    const response = await axios.put(
      `${API}/auth/users/${userId}/gradatie?gradatie=${gradatie}&reden=${encodeURIComponent(reden)}`
    );
    return response.data;
  }
};

/**
 * System API
 */
export const SystemAPI = {
  /**
   * Haal module overzicht op
   */
  getModules: async () => {
    const response = await axios.get(`${API}`);
    return response.data;
  },

  /**
   * Health check
   */
  health: async () => {
    const response = await axios.get(`${BACKEND_URL}/health`);
    return response.data;
  }
};

export default { AuthAPI, SystemAPI };
