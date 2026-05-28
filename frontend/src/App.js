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
import { AgendaPage } from "./components/workspace/AgendaPage";
import { GesprekkenPage } from "./components/workspace/GesprekkenPage";
import { ArchiefPage } from "./components/workspace/ArchiefPage";
import { KennisbankPage } from "./components/workspace/KennisbankPage";
import { KennisbankV2Page } from "./components/workspace/KennisbankV2Page";
import { RoadmapPage } from "./components/workspace/RoadmapPage";
import { DagboekPage } from "./components/workspace/DagboekPage";
import { NotitiesPage } from "./components/workspace/NotitiesPage";
import { BijdragenPage } from "./components/workspace/BijdragenPage";
import { LeaderboardPage } from "./components/modules/LeaderboardPage";
import { IntegratiesPage } from "./components/modules/IntegratiesPage";
import { AchievementsPage } from "./components/modules/AchievementsPage";
import { InstellingenPage } from "./components/admin/InstellingenPage";
import { WalletPage } from "./components/modules/WalletPage";
import { SparkBrainPage } from "./components/spark/SparkBrainPage";
import { SparkOverviewPage } from "./components/spark/SparkOverviewPage";
import { SynapsePage } from "./components/spark/SynapsePage";
import { EmotieRouteringPage } from "./components/spark/EmotieRouteringPage";
import { PersoonsPage } from "./components/modules/PersoonsPage";
import { WinkelPage } from "./components/modules/WinkelPage";
import { BoekhoudPage } from "./components/modules/BoekhoudPage";
import { CommunityPage } from "./components/workspace/CommunityPage";
import { VoicePage } from "./components/workspace/VoicePage";

// Main App Content with Navigation
function AppContent() {
  const { isLoggedIn, loading, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [activePage, setActivePage] = useState('dashboard');

  // Map paths to page ids
  const getPageIdFromPath = (path) => {
    const pathMap = {
      '/': 'dashboard',
      '/chat': 'chat',
      '/archief': 'archief',
      '/knowledge': 'knowledge-v2',
      '/knowledge-legacy': 'knowledge',
      '/spark/kennisbank-v2': 'knowledge-v2',
      '/calendar': 'calendar',
      '/roadmap': 'roadmap',
      '/dagboek': 'dagboek',
      '/notities': 'notities',
      '/bijdragen': 'bijdragen',
      '/spark/brain': 'spark-brain',
      '/spark/overzicht': 'spark-overzicht',
      '/spark/synapse': 'synapse',
      '/spark/triggers': 'triggers',
      '/spark/emotions': 'emotions',
      '/spark/routering': 'emotion-routing',
      '/spark/connections': 'connections',
      '/modules/trader': 'trade',
      '/modules/trade': 'trade',
      '/modules/achievements': 'achievements',
      '/modules/wallet': 'wallet',
      '/modules/leaderboard': 'leaderboard',
      '/modules/winkel': 'winkel',
      '/modules/boekhouding': 'boekhouding',
      '/modules/community': 'community',
      '/modules/persons': 'persons',
      '/modules/integrations': 'integrations',
      '/workspace/voice': 'voice',
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

  // v4_route_guard_001 — admin routes alleen voor gradatie ≤ 2 (bug #5)
  // Als URL een admin-pad is maar user is geen admin → forceer redirect naar dashboard
  const ADMIN_PAGES = ['users', 'analytics', 'settings'];
  useEffect(() => {
    if (!user) return;
    if (ADMIN_PAGES.includes(activePage) && (user.gradatie ?? 7) > 2) {
      setActivePage('dashboard');
      navigate('/', { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, activePage]);

  // v5_ui_prefs_001 — laad glow base color voorkeur en zet CSS variable op root
  useEffect(() => {
    if (!user?.id) return;
    const API = process.env.REACT_APP_BACKEND_URL;
    fetch(`${API}/api/profile/ui-preferences/${user.id}`)
      .then(r => r.json())
      .then(d => {
        const c = d?.preferences?.glow_base_color;
        if (c && /^#[0-9a-fA-F]{6}$/.test(c)) {
          document.documentElement.style.setProperty('--glow-base', c);
        }
      })
      .catch(() => {});
  }, [user?.id]);

  // v6_mood_glow_gradient_001 (28 mei) — glow-kleur shift met huidige emotie-state
  useEffect(() => {
    if (!user?.id) return;
    const API = process.env.REACT_APP_BACKEND_URL;
    const MOOD_COLORS = {
      blij:      '#22c55e', // groen
      vrolijk:   '#10b981',
      tevreden:  '#06b6d4',
      neutraal:  '#f59e0b', // default amber
      moe:       '#6366f1',
      verdrietig:'#475569',
      boos:      '#ef4444',
      gefrustreerd:'#dc2626',
      verbaasd:  '#a855f7',
      bang:      '#f97316',
    };
    const update = () => {
      fetch(`${API}/api/chat/emotions/state`)
        .then(r => r.json())
        .then(d => {
          const e = (d?.state || d?.current_emotion?.state || 'neutraal').toLowerCase();
          const color = MOOD_COLORS[e];
          if (color) document.documentElement.style.setProperty('--mood-glow', color);
        })
        .catch(() => {});
    };
    update();
    const t = setInterval(update, 60000); // refresh elke minuut
    return () => clearInterval(t);
  }, [user?.id]);

  // v5_admin_color_scheme_001 — laad overkoepelend kleurenschema (system-wide)
  useEffect(() => {
    if (!user?.id) return;
    const API = process.env.REACT_APP_BACKEND_URL;
    fetch(`${API}/api/settings/system`)
      .then(r => r.json())
      .then(d => {
        const s = d?.settings || {};
        const apply = (key, css) => {
          const v = s[key];
          if (v && /^#[0-9a-fA-F]{6}$/.test(v)) {
            document.documentElement.style.setProperty(css, v);
          }
        };
        apply('app_primary_accent', '--app-primary');
        apply('app_secondary_accent', '--app-secondary');
        apply('app_background_tint', '--app-bg-tint');
      })
      .catch(() => {});
  }, [user?.id]);

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
      case 'trade':
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
      case 'calendar':
        return <AgendaPage onNavigate={handleNavigate} />;
      case 'chat':
        return <GesprekkenPage onNavigate={handleNavigate} />;
      case 'archief':
        return <ArchiefPage onNavigate={handleNavigate} />;
      case 'knowledge':
        return <KennisbankPage onNavigate={handleNavigate} />;
      case 'knowledge-v2':
        return <KennisbankV2Page onNavigate={handleNavigate} />;
      case 'roadmap':
        return <RoadmapPage onNavigate={handleNavigate} />;
      case 'dagboek':
        return <DagboekPage onNavigate={handleNavigate} />;
      case 'notities':
        return <NotitiesPage onNavigate={handleNavigate} />;
      case 'bijdragen':
        return <BijdragenPage onNavigate={handleNavigate} />;
      case 'leaderboard':
        return <LeaderboardPage onNavigate={handleNavigate} />;
      case 'integrations':
        return <IntegratiesPage onNavigate={handleNavigate} />;
      case 'achievements':
        return <AchievementsPage onNavigate={handleNavigate} />;
      case 'settings':
        return <InstellingenPage onNavigate={handleNavigate} />;
      case 'wallet':
        return <WalletPage onNavigate={handleNavigate} />;
      case 'spark-brain':
        return <SparkBrainPage onNavigate={handleNavigate} />;
      case 'spark-overzicht':
        return <SparkOverviewPage onNavigate={handleNavigate} />;
      case 'synapse':
        return <SynapsePage onNavigate={handleNavigate} />;
      case 'emotion-routing':
        return <EmotieRouteringPage onNavigate={handleNavigate} />;
      case 'persons':
        return <PersoonsPage onNavigate={handleNavigate} />;
      case 'winkel':
        return <WinkelPage onNavigate={handleNavigate} />;
      case 'boekhouding':
        return <BoekhoudPage onNavigate={handleNavigate} />;
      case 'community':
        return <CommunityPage onNavigate={handleNavigate} />;
      case 'voice':
        return <VoicePage onNavigate={handleNavigate} />;
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
