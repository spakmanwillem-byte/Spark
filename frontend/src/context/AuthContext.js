import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AuthAPI } from '../api';

const AuthContext = createContext(null);

const STORAGE_KEY = 'spark_user';
const HEARTBEAT_INTERVAL = 30000; // 30 seconds

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Restore session from localStorage
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const userData = JSON.parse(stored);
        // Validate session
        AuthAPI.validateSession(userData.id)
          .then(result => {
            if (result.valid) {
              setUser(result.user);
            } else {
              localStorage.removeItem(STORAGE_KEY);
            }
          })
          .catch(() => {
            localStorage.removeItem(STORAGE_KEY);
          })
          .finally(() => setLoading(false));
      } catch {
        localStorage.removeItem(STORAGE_KEY);
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  // Heartbeat to keep session alive
  useEffect(() => {
    if (!user) return;

    const interval = setInterval(() => {
      AuthAPI.heartbeat(user.id).catch(() => {
        // Session expired
        logout();
      });
    }, HEARTBEAT_INTERVAL);

    return () => clearInterval(interval);
  }, [user]);

  const login = useCallback(async (naam, sleutelwoord, masterkey = null) => {
    setError(null);
    try {
      const result = await AuthAPI.login(naam, sleutelwoord, masterkey);
      if (result.success) {
        setUser(result.user);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(result.user));
        return { success: true, user: result.user, isMasterkey: result.is_masterkey };
      } else {
        setError(result.message);
        return { success: false, message: result.message };
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login mislukt';
      setError(msg);
      return { success: false, message: msg };
    }
  }, []);

  const logout = useCallback(() => {
    if (user) {
      AuthAPI.logout(user.id).catch(() => {});
    }
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  }, [user]);

  const refreshUser = useCallback(async () => {
    if (!user) return;
    try {
      const userData = await AuthAPI.getUser(user.id);
      setUser(userData);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
    } catch (err) {
      console.error('Failed to refresh user:', err);
    }
  }, [user]);

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    refreshUser,
    isLoggedIn: !!user,
    isAdmin: user?.gradatie === 1
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

export default AuthContext;
