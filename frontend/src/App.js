import React, { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { LoginForm } from "./components/auth/LoginForm";
import { DashboardPage } from "./components/dashboard/DashboardPage";
import { TraderPage } from "./components/modules/TraderPage";
import { UsersAdminPage } from "./components/admin/UsersAdminPage";
import { UserProfilePage } from "./components/profile/UserProfilePage";
import { AnalyticsPage } from "./components/admin/AnalyticsPage";
import { EmotiesPage } from "./components/spark/EmotiesPage";
import { VerbandenPage } from "./components/spark/VerbandenPage";
import { TriggersPage } from "./components/spark/TriggersPage";

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
      '/modules/trader': 'trader',
      '/modules/achievements': 'achievements',
      '/modules/wallet': 'wallet',
      '/modules/community': 'community',
      '/modules/integrations': 'integrations',
      '/profiel': 'profiel',
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

  // Logged in - show appropriate page based on activePage
  const renderPage = () => {
    switch (activePage) {
      case 'trader':
        return <TraderPage onNavigate={handleNavigate} />;
      case 'users':
        return <UsersAdminPage onNavigate={handleNavigate} />;
      case 'profiel':
        return <UserProfilePage onNavigate={handleNavigate} />;
      case 'analytics':
        return <AnalyticsPage onNavigate={handleNavigate} />;
      case 'emotions':
        return <EmotiesPage onNavigate={handleNavigate} />;
      case 'connections':
        return <VerbandenPage onNavigate={handleNavigate} />;
      case 'triggers':
        return <TriggersPage onNavigate={handleNavigate} />;
      default:
        return <DashboardPage activePage={activePage} onNavigate={handleNavigate} />;
    }
  };

  return renderPage();
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
