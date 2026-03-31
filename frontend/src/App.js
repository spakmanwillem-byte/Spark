import React, { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { LoginForm } from "./components/auth/LoginForm";
import { DashboardPage } from "./components/dashboard/DashboardPage";

// Main App Content with Navigation
function AppContent() {
  const { isLoggedIn, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [activePage, setActivePage] = useState('dashboard');

  // Map paths to page ids
  const getPageIdFromPath = (path) => {
    const pathMap = {
      '/': 'dashboard',
      '/chat': 'chat',
      '/knowledge': 'knowledge',
      '/calendar': 'calendar',
      '/spark/brain': 'spark-brain',
      '/spark/triggers': 'triggers',
      '/spark/emotions': 'emotions',
      '/spark/connections': 'connections',
      '/modules/achievements': 'achievements',
      '/modules/wallet': 'wallet',
      '/modules/community': 'community',
      '/modules/integrations': 'integrations',
      '/admin/users': 'users',
      '/admin/analytics': 'analytics',
      '/admin/settings': 'settings',
    };
    return pathMap[path] || 'dashboard';
  };

  // Sync activePage with URL
  useEffect(() => {
    setActivePage(getPageIdFromPath(location.pathname));
  }, [location.pathname]);

  // Handle navigation from sidebar
  const handleNavigate = (pageId, path) => {
    setActivePage(pageId);
    navigate(path);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Laden...</p>
        </div>
      </div>
    );
  }

  // Not logged in - show login
  if (!isLoggedIn) {
    return <LoginForm />;
  }

  // Logged in - show dashboard with active page
  return <DashboardPage activePage={activePage} onNavigate={handleNavigate} />;
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
