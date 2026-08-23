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

  const logout = useCallback(() => {
    if (user) {
      AuthAPI.logout(user.id).catch(() => {});
      // Wis Spark chat sessie van deze user (chat staat in sessionStorage)
      try {
        sessionStorage.removeItem(`spark_chat_session_${user.id}`);
      } catch {
        // Ignore storage errors
      }
    }
    // v13_tab_reset_on_switch_001 (sessie 54) — Willem: bij uitloggen + inloggen
    // op ander account opent oude tab van vorige user. Reset actieve-tab
    // sessionStorage bij elke logout zodat volgende user vers begint.
    try {
      sessionStorage.removeItem('spark_active_tab');
      sessionStorage.removeItem('spark_last_non_chat_tab');
    } catch {
      // Ignore storage errors
    }
    setUser(null);
    localStorage.removeItem(STORAGE_KEY);
  }, [user]);

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
  }, [user, logout]);

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

  // v6_avatar_live_refresh — luister naar avatar-changed event en refresh user-object
  // zodat sidebar/header/etc. de nieuwe avatar zien zonder login-reload
  useEffect(() => {
    if (!user?.id) return;
    const handler = (e) => {
      if (!e?.detail?.userId || e.detail.userId === user.id) {
        refreshUser();
      }
    };
    window.addEventListener('avatar-changed', handler);
    return () => window.removeEventListener('avatar-changed', handler);
  }, [user?.id, refreshUser]);

  // v11_admin_mode_001 — Admin losgekoppeld van gradatie. Standaard NIEMAND is admin,
  // ook Willem (gradatie 1) niet. Enable via 'Admin aan' + admin_key. Bewaard in
  // localStorage per user zodat het session-survivable is.
  const [adminModeActive, setAdminModeActive] = useState(() => {
    try {
      const uid = JSON.parse(localStorage.getItem('spark_user') || 'null')?.id;
      return uid ? localStorage.getItem(`spark_admin_mode_${uid}`) === '1' : false;
    } catch { return false; }
  });
  const [adminCapable, setAdminCapable] = useState(false);

  // Load admin_capable status wanneer user verandert
  useEffect(() => {
    if (!user?.id) { setAdminCapable(false); return; }
    const API = process.env.REACT_APP_BACKEND_URL;
    fetch(`${API}/api/auth/admin/status/${user.id}`)
      .then(r => r.json())
      .then(d => setAdminCapable(!!d.admin_capable))
      .catch(() => setAdminCapable(false));
  }, [user?.id]);

  const enableAdmin = useCallback(async (adminKey) => {
    const API = process.env.REACT_APP_BACKEND_URL;
    const r = await fetch(`${API}/api/auth/admin/enable`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user.id, admin_key: adminKey }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || 'Ongeldige admin-key');
    }
    setAdminModeActive(true);
    localStorage.setItem(`spark_admin_mode_${user.id}`, '1');
    return true;
  }, [user?.id]);

  const disableAdmin = useCallback(() => {
    setAdminModeActive(false);
    if (user?.id) localStorage.removeItem(`spark_admin_mode_${user.id}`);
  }, [user?.id]);

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    refreshUser,
    isLoggedIn: !!user,
    // v11_admin_mode_001: isAdmin nu = admin_capable EN admin-mode actief (niet meer gradatie-gebaseerd)
    isAdmin: adminCapable && adminModeActive,
    adminCapable,
    adminModeActive,
    enableAdmin,
    disableAdmin,
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
