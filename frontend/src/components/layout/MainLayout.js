import React, { useState } from 'react';
import { 
  Zap, Home, MessageSquare, Users, Calendar, Brain, 
  Sparkles, Zap as Bolt, Link2, Puzzle, UsersRound,
  BarChart3, Target, ChevronLeft, ChevronRight, LogOut,
  BookOpen, Settings, Shield, Wallet, Trophy, Bell, TrendingUp, User, Map,
  BookHeart, StickyNote, Award
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

// Navigation configuration - easy to extend
export const navigationConfig = {
  workspace: {
    label: 'WORKSPACE',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: Home, path: '/' },
      { id: 'chat', label: 'Gesprekken', icon: MessageSquare, path: '/chat' },
      { id: 'knowledge', label: 'Kennisbank', icon: BookOpen, path: '/knowledge' },
      { id: 'calendar', label: 'Agenda', icon: Calendar, path: '/calendar' },
      { id: 'dagboek', label: 'Dagboek', icon: BookHeart, path: '/dagboek' },
      { id: 'notities', label: 'Notities & Taken', icon: StickyNote, path: '/notities' },
      { id: 'roadmap', label: 'Roadmap', icon: Map, path: '/roadmap' },
    ]
  },
  spark: {
    label: 'SPARK AI',
    items: [
      { id: 'spark-brain', label: 'Spark Brain', icon: Brain, path: '/spark/brain' },
      { id: 'triggers', label: 'Triggers', icon: Bolt, path: '/spark/triggers' },
      { id: 'emotions', label: 'Emoties', icon: Sparkles, path: '/spark/emotions' },
      { id: 'connections', label: 'Verbanden', icon: Link2, path: '/spark/connections' },
    ]
  },
  modules: {
    label: 'MODULES',
    items: [
      { id: 'trader', label: 'Trader', icon: TrendingUp, path: '/modules/trader' },
      { id: 'achievements', label: 'Achievements', icon: Trophy, path: '/modules/achievements' },
      { id: 'leaderboard', label: 'Leaderboard', icon: Award, path: '/modules/leaderboard' },
      { id: 'wallet', label: 'Wallet', icon: Wallet, path: '/modules/wallet' },
      { id: 'persons', label: 'Persoonskaarten', icon: UsersRound, path: '/modules/persons' },
      { id: 'integrations', label: 'Integraties', icon: Puzzle, path: '/modules/integrations' },
    ]
  },
  admin: {
    label: 'BEHEER',
    items: [
      { id: 'profiel', label: 'Mijn Profiel', icon: User, path: '/profiel' },
      { id: 'users', label: 'Gebruikers', icon: Users, path: '/admin/users', adminOnly: true },
      { id: 'analytics', label: 'Analytics', icon: BarChart3, path: '/admin/analytics', adminOnly: true },
      { id: 'settings', label: 'Instellingen', icon: Settings, path: '/admin/settings' },
    ]
  }
};

// Get page info by id
export const getPageInfo = (pageId) => {
  for (const section of Object.values(navigationConfig)) {
    const item = section.items.find(i => i.id === pageId);
    if (item) return { ...item, section: section.label };
  }
  return null;
};

export function MainLayout({ children, activePage = 'dashboard', onNavigate }) {
  const { user, logout, isAdmin } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleNavClick = (item) => {
    if (onNavigate) {
      onNavigate(item.id, item.path);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex">
      {/* Sidebar */}
      <aside 
        className={`${sidebarCollapsed ? 'w-20' : 'w-64'} bg-slate-900/50 border-r border-slate-800 flex flex-col transition-all duration-300 ease-in-out flex-shrink-0`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-slate-800">
          <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/20 cursor-pointer" onClick={() => onNavigate && onNavigate('dashboard', '/')}>
            <Zap className="w-5 h-5 text-white" />
          </div>
          {!sidebarCollapsed && (
            <div className="ml-3">
              <h1 className="text-lg font-bold text-white">Spark Core</h1>
              <p className="text-xs text-slate-500">v2.0</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-3">
          {Object.entries(navigationConfig).map(([key, section]) => {
            // Filter admin-only items for non-admins
            const visibleItems = section.items.filter(item => !item.adminOnly || isAdmin);
            if (visibleItems.length === 0) return null;

            return (
              <div key={key} className="mb-6">
                {!sidebarCollapsed && (
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
                    {section.label}
                  </p>
                )}
                <div className="space-y-1">
                  {visibleItems.map(item => (
                    <NavItem 
                      key={item.id}
                      item={item}
                      isActive={activePage === item.id}
                      isCollapsed={sidebarCollapsed}
                      onClick={() => handleNavClick(item)}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </nav>

        {/* User & Collapse */}
        <div className="border-t border-slate-800 p-3">
          {/* User info */}
          {!sidebarCollapsed && (
            <div className="flex items-center gap-3 px-3 py-2 mb-2">
              <div className="w-8 h-8 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center">
                <span className="text-xs font-bold text-white">
                  {user?.naam?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user?.naam}</p>
                <p className="text-xs text-slate-500">{user?.rol || `Gradatie ${user?.gradatie}`}</p>
              </div>
              <button
                onClick={logout}
                className="p-1.5 text-slate-500 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                data-testid="logout-btn"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Collapse button */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-slate-500 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
          >
            {sidebarCollapsed ? (
              <ChevronRight className="w-5 h-5" />
            ) : (
              <>
                <ChevronLeft className="w-5 h-5" />
                <span className="text-sm">Inklappen</span>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}

// Navigation Item Component
function NavItem({ item, isActive, isCollapsed, onClick }) {
  const Icon = item.icon;

  return (
    <button
      onClick={onClick}
      className={`
        w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all cursor-pointer
        ${isActive 
          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' 
          : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
        }
        ${isCollapsed ? 'justify-center' : ''}
      `}
      title={isCollapsed ? item.label : undefined}
      data-testid={`nav-${item.id}`}
    >
      <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-amber-400' : ''}`} />
      {!isCollapsed && (
        <span className="flex-1 text-left text-sm font-medium">{item.label}</span>
      )}
    </button>
  );
}

export default MainLayout;
