import React, { useState } from 'react';
import { 
  Zap, Home, MessageSquare, Users, Calendar, Brain, 
  Sparkles, Zap as Bolt, Link2, Puzzle, UsersRound, MessageCircle, Volume2,
  BarChart3, Target, ChevronLeft, ChevronRight, LogOut,
  BookOpen, Settings, Shield, Wallet, Trophy, Bell, TrendingUp, User, Map,
  BookHeart, StickyNote, Award, ShoppingBag, BookMarked
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
      { id: 'voice', label: 'Voice', icon: Volume2, path: '/workspace/voice' },
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
      { id: 'trade', label: 'Trade', icon: TrendingUp, path: '/modules/trade' },
      { id: 'wallet', label: 'Wallet', icon: Wallet, path: '/modules/wallet' },
      { id: 'winkel', label: 'Winkel', icon: ShoppingBag, path: '/modules/winkel' },
      { id: 'boekhouding', label: 'Boekhouding', icon: BookMarked, path: '/modules/boekhouding' },
      { id: 'achievements', label: 'Achievements', icon: Trophy, path: '/modules/achievements' },
      { id: 'leaderboard', label: 'Leaderboard', icon: Award, path: '/modules/leaderboard' },
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
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const stored = parseInt(localStorage.getItem('sidebarWidth') || '256', 10);
    return isNaN(stored) ? 256 : Math.min(Math.max(stored, 200), 420);
  });
  const [isResizing, setIsResizing] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifs, setShowNotifs] = useState(false);
  const [notifs, setNotifs] = useState([]);

  // Drag-to-resize
  React.useEffect(() => {
    if (!isResizing) return;
    const handleMove = (e) => {
      const w = Math.min(Math.max(e.clientX, 200), 420);
      setSidebarWidth(w);
    };
    const handleUp = () => {
      setIsResizing(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', handleUp);
    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleUp);
    };
  }, [isResizing]);

  React.useEffect(() => {
    localStorage.setItem('sidebarWidth', String(sidebarWidth));
  }, [sidebarWidth]);

  const userId = user?.id || 'user-001';
  const API = process.env.REACT_APP_BACKEND_URL;

  React.useEffect(() => {
    fetch(`${API}/api/notifications/${userId}`)
      .then(r => r.json())
      .then(d => { setUnreadCount(d.unread_count || 0); setNotifs(d.notifications || []); })
      .catch(() => {});
  }, [userId, API]);

  const markAllRead = () => {
    fetch(`${API}/api/notifications/${userId}/read-all`, { method: 'POST' }).then(() => {
      setUnreadCount(0);
      setNotifs(prev => prev.map(n => ({ ...n, read: true })));
    });
    setShowNotifs(false);
  };

  const handleNavClick = (item) => {
    if (onNavigate) {
      onNavigate(item.id, item.path);
    }
  };

  return (
    <div className="h-screen bg-slate-950 flex overflow-hidden">
      {/* Sidebar */}
      <aside 
        className="bg-slate-900/50 border-r border-slate-800 flex flex-col flex-shrink-0 relative"
        style={{ width: sidebarCollapsed ? 80 : sidebarWidth, transition: isResizing ? 'none' : 'width 300ms ease-in-out' }}
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

        {/* Drag handle to resize */}
        {!sidebarCollapsed && (
          <div
            data-testid="sidebar-resize-handle"
            onMouseDown={(e) => { e.preventDefault(); setIsResizing(true); }}
            className="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-amber-500/30 transition-colors z-10"
            title="Sleep om sidebar breder te maken"
          />
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 h-full overflow-y-auto overflow-x-hidden relative">
        {/* Top bar with notifications */}
        <div className="absolute top-3 right-4 z-30 flex items-center gap-2">
          <div className="relative">
            <button data-testid="notification-bell" onClick={() => setShowNotifs(!showNotifs)}
              className="p-2 bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-xl transition-colors relative">
              <Bell className="w-4 h-4 text-slate-400" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[9px] font-bold text-white flex items-center justify-center">
                  {unreadCount}
                </span>
              )}
            </button>
            {showNotifs && (
              <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden">
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
                  <span className="text-sm font-semibold text-white">Meldingen</span>
                  {unreadCount > 0 && (
                    <button onClick={markAllRead} className="text-[10px] text-amber-400 hover:underline">Alles gelezen</button>
                  )}
                </div>
                <div className="max-h-72 overflow-y-auto">
                  {notifs.map(n => (
                    <div key={n.id} className={`px-4 py-3 border-b border-slate-800/50 ${n.read ? 'opacity-50' : ''}`}>
                      <p className="text-xs font-medium text-white">{n.title}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{n.message}</p>
                      <p className="text-[9px] text-slate-600 mt-1">{n.timestamp ? new Date(n.timestamp).toLocaleString('nl-NL') : ''}</p>
                    </div>
                  ))}
                  {notifs.length === 0 && <p className="px-4 py-6 text-center text-xs text-slate-500">Geen meldingen</p>}
                </div>
              </div>
            )}
          </div>
        </div>
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
