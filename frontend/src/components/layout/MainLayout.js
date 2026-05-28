import React, { useState, useEffect } from 'react';
import { 
  Zap, Home, MessageSquare, Users, Calendar, Brain, 
  Sparkles, Zap as Bolt, Link2, Puzzle, UsersRound, MessageCircle, Volume2,
  BarChart3, Target, ChevronLeft, ChevronRight, LogOut,
  BookOpen, Settings, Shield, Wallet, Trophy, Bell, TrendingUp, User, Map,
  BookHeart, StickyNote, Award, ShoppingBag, BookMarked, Archive, HandHeart,
  Activity
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { UserAvatar } from '../common/UserAvatar';
import { BarkQueueOverlay } from '../common/BarkQueueOverlay';

// Navigation configuration - easy to extend
export const navigationConfig = {
  workspace: {
    label: 'WORKSPACE',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: Home, path: '/' },
      { id: 'chat', label: 'Gesprekken', icon: MessageSquare, path: '/chat' },
      { id: 'archief', label: 'Archief', icon: Archive, path: '/archief' },
      { id: 'calendar', label: 'Agenda', icon: Calendar, path: '/calendar' },
      { id: 'dagboek', label: 'Dagboek', icon: BookHeart, path: '/dagboek' },
      { id: 'notities', label: 'Notities & Taken', icon: StickyNote, path: '/notities' },
      { id: 'roadmap', label: 'Roadmap', icon: Map, path: '/roadmap' },
    ]
  },
  spark: {
    label: 'SPARK AI',
    items: [
      { id: 'spark-overzicht', label: 'Brein-overzicht', icon: Brain, path: '/spark/overzicht' },
      { id: 'spark-brain', label: 'Spark Brain', icon: Brain, path: '/spark/brain' },
      { id: 'synapse', label: 'Synapslaag', icon: Brain, path: '/spark/synapse', adminOnly: true },
      { id: 'knowledge-v2', label: 'Kennisbank', icon: BookOpen, path: '/knowledge' },
      { id: 'triggers', label: 'Triggers', icon: Bolt, path: '/spark/triggers' },
      { id: 'emotions', label: 'Emotie Detectie', icon: Sparkles, path: '/spark/emotions' },
      { id: 'emotion-routing', label: 'Emotie Routering', icon: Activity, path: '/spark/routering', adminOnly: true },
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

// Per-gradatie zichtbaarheid (v4_gradatie_visibility_002 — verfijnd op basis van bug-meldingen 19/05)
// Grad 1 (eigenaar): alle tabs
// Grad 2 (admin/fam): alle workspace, geen voice-onder-workspace (komt later als kader in Features)
// Grad 3 (vrienden): geen voice, geen Spark AI sectie, geen Integraties
// Grad 4 (collega's): zelfde als 3 + geen voice
// Grad 5: + geen Trade + geen Boekhouding
// Grad 6: + geen Dagboek
// Grad 7: + geen Agenda (krijgt Agenda terug bij upgrade naar 6) + geen Archief + geen Boekhouding (heeft Wallet)
const VISIBILITY_RULES = {
  1: { hideSection: [], hide: [] },
  2: { hideSection: [], hide: ['voice'] },
  3: { hideSection: ['spark'], hide: ['voice', 'integrations', 'analytics', 'settings'] },
  4: { hideSection: ['spark'], hide: ['voice', 'integrations', 'users', 'analytics', 'settings'] },
  5: { hideSection: ['spark'], hide: ['voice', 'integrations', 'users', 'analytics', 'settings', 'trade', 'boekhouding'] },
  6: { hideSection: ['spark'], hide: ['voice', 'integrations', 'users', 'analytics', 'settings', 'trade', 'boekhouding', 'dagboek'] },
  7: { hideSection: ['spark'], hide: ['voice', 'integrations', 'users', 'analytics', 'settings', 'trade', 'boekhouding', 'dagboek', 'archief', 'calendar'] },
};

export function getVisibilityForGradatie(grad) {
  return VISIBILITY_RULES[grad] || VISIBILITY_RULES[7];
}

export function MainLayout({ children, activePage = 'dashboard', onNavigate }) {
  const { user, logout, isAdmin } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // v5_presence_heartbeat_001 — Globale heartbeat, update last_active elke 30s
  useEffect(() => {
    if (!user?.id) return;
    const API = process.env.REACT_APP_BACKEND_URL;
    const beat = () => fetch(`${API}/api/contacts/heartbeat?user_id=${user.id}`, { method: 'POST' }).catch(() => {});
    beat();
    const t = setInterval(beat, 30_000);
    return () => clearInterval(t);
  }, [user?.id]);

  // Urgent notifications glow (v4_glow_001) — pollt elke 60s
  const [urgentGlow, setUrgentGlow] = useState({});
  const [urgentItems, setUrgentItems] = useState([]);
  useEffect(() => {
    if (!user?.id) return;
    const API = process.env.REACT_APP_BACKEND_URL;
    let cancelled = false;
    const fetchUrgent = () => {
      fetch(`${API}/api/urgent/notifications?user_id=${user.id}`)
        .then(r => r.json())
        .then(d => {
          if (cancelled) return;
          setUrgentGlow(d?.glow || {});
          setUrgentItems(d?.items || []);
        })
        .catch(() => {});
    };
    fetchUrgent();
    const interval = setInterval(fetchUrgent, 60_000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [user?.id]);

  // Backend keepalive (v4_keepalive_001) — pingt elke 4 min zodat Emergent pod actief blijft
  // en de trade monitor blijft draaien wanneer admin is uitgelogd maar tab open.
  useEffect(() => {
    const API = process.env.REACT_APP_BACKEND_URL;
    const ping = () => fetch(`${API}/api/system/health`).catch(() => {});
    ping();
    const interval = setInterval(ping, 240_000); // 4 min
    return () => clearInterval(interval);
  }, []);

  // v6_glow_nav_001 — Spark wijst tab aan: pulserende glow op nav-button + auto-navigatie
  useEffect(() => {
    const handler = (e) => {
      const targetId = e?.detail?.targetId;
      const navigateTo = e?.detail?.navigateTo;
      const pulseDurationMs = 6000;
      if (!targetId) return;

      const tryGlow = (attempt = 0) => {
        const el = document.querySelector(`[data-testid="${targetId}"]`);
        if (!el && attempt < 6) {
          setTimeout(() => tryGlow(attempt + 1), 300);
          return;
        }
        if (!el) return;
        el.classList.add('spark-nav-glow');
        try { el.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch {}
        setTimeout(() => {
          try { el.classList.remove('spark-nav-glow'); } catch {}
        }, pulseDurationMs);
      };

      // Eerste pulse meteen, dan navigeer (zodat user het ziet oplichten)
      tryGlow();

      // Zoek bijbehorend nav-item en roep onNavigate aan
      if (navigateTo && typeof onNavigate === 'function') {
        let foundItem = null;
        for (const section of Object.values(navigationConfig)) {
          const m = section.items.find(it => it.path === navigateTo);
          if (m) { foundItem = m; break; }
        }
        if (foundItem) {
          // Kleine vertraging zodat de glow eerst zichtbaar wordt
          setTimeout(() => onNavigate(foundItem.id, foundItem.path), 700);
        }
      }
    };
    window.addEventListener('spark:nav-glow', handler);
    return () => window.removeEventListener('spark:nav-glow', handler);
  }, [onNavigate]);
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const stored = parseInt(localStorage.getItem('sidebarWidth') || '256', 10);
    return isNaN(stored) ? 256 : Math.min(Math.max(stored, 200), 420);
  });
  const [isResizing, setIsResizing] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifs, setShowNotifs] = useState(false);
  const [notifs, setNotifs] = useState([]);

  // Drag-to-reorder sidebar items (per sectie + cross-sectie)
  // Format: { sectionKey: [{id, fromSection}] } — fromSection geeft aan waar item origineel vandaan kwam
  const [customOrder, setCustomOrder] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('sidebarOrder') || '{}');
    } catch {
      return {};
    }
  });
  const [dragState, setDragState] = useState(null); // { sectionKey, itemId, fromSection }

  const saveOrder = (next) => {
    setCustomOrder(next);
    localStorage.setItem('sidebarOrder', JSON.stringify(next));
  };

  // Zoek waar een item standaard thuishoort
  const findOriginalSection = (itemId) => {
    for (const [key, section] of Object.entries(navigationConfig)) {
      if (section.items.find(i => i.id === itemId)) return key;
    }
    return null;
  };

  // Zoek een item (volledig object) op basis van ID, ongeacht sectie
  const findItemById = (itemId) => {
    for (const section of Object.values(navigationConfig)) {
      const item = section.items.find(i => i.id === itemId);
      if (item) return item;
    }
    return null;
  };

  // Pas custom volgorde toe, inclusief cross-sectie relocations
  const getItemsForSection = (sectionKey) => {
    const customForSection = customOrder[sectionKey];
    // Alle items die hun originele sectie verlaten hebben (staan nu ergens anders)
    const relocatedOut = new Set();
    for (const [sk, entries] of Object.entries(customOrder)) {
      if (!Array.isArray(entries)) continue;
      for (const entry of entries) {
        const id = typeof entry === 'string' ? entry : entry.id;
        const fromSection = typeof entry === 'object' ? entry.fromSection : findOriginalSection(id);
        if (fromSection && fromSection !== sk) {
          relocatedOut.add(id);
        }
      }
    }

    if (customForSection && Array.isArray(customForSection)) {
      const ordered = customForSection
        .map(entry => {
          const id = typeof entry === 'string' ? entry : entry.id;
          return findItemById(id);
        })
        .filter(Boolean);
      // Voeg nieuwe defaults toe die nog niet in custom order staan (en niet verhuisd zijn)
      const knownIds = new Set(customForSection.map(e => typeof e === 'string' ? e : e.id));
      const extras = navigationConfig[sectionKey].items.filter(
        i => !knownIds.has(i.id) && !relocatedOut.has(i.id)
      );
      return [...ordered, ...extras];
    }
    // Geen custom order: gewoon defaults, minus de items die naar andere secties zijn verhuisd
    return navigationConfig[sectionKey].items.filter(i => !relocatedOut.has(i.id));
  };

  const handleDragStart = (sectionKey, itemId) => {
    setDragState({ sectionKey, itemId, fromSection: sectionKey });
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  // Drop op een specifiek item: plaats vóór dat item
  const handleDropOnItem = (targetSectionKey, targetItemId) => {
    if (!dragState) { setDragState(null); return; }
    if (dragState.itemId === targetItemId && dragState.sectionKey === targetSectionKey) {
      setDragState(null); return;
    }

    // Haal ID lijsten op van source + target
    const next = { ...customOrder };

    const getIdList = (sk) => {
      const existing = next[sk];
      if (Array.isArray(existing)) {
        return existing.map(e => typeof e === 'string' ? e : e.id);
      }
      return getItemsForSection(sk).map(i => i.id);
    };

    const sourceIds = getIdList(dragState.sectionKey);
    const targetIds = getIdList(targetSectionKey);

    // Verwijder uit source
    const sourceFiltered = sourceIds.filter(id => id !== dragState.itemId);

    // Voeg in target in vóór target item
    const targetIdx = targetIds.indexOf(targetItemId);
    let newTargetIds;
    if (dragState.sectionKey === targetSectionKey) {
      // Same section reorder
      newTargetIds = sourceFiltered;
      const newIdx = newTargetIds.indexOf(targetItemId);
      newTargetIds = [...newTargetIds];
      const insertAt = newIdx >= 0 ? newIdx : newTargetIds.length;
      newTargetIds.splice(insertAt, 0, dragState.itemId);
    } else {
      newTargetIds = [...targetIds];
      const insertAt = targetIdx >= 0 ? targetIdx : newTargetIds.length;
      newTargetIds.splice(insertAt, 0, dragState.itemId);
      next[dragState.sectionKey] = sourceFiltered;
    }
    next[targetSectionKey] = newTargetIds;

    saveOrder(next);
    setDragState(null);
  };

  // Drop op het einde van een sectie (lege ruimte)
  const handleDropOnSection = (targetSectionKey) => {
    if (!dragState) { setDragState(null); return; }
    if (dragState.sectionKey === targetSectionKey) { setDragState(null); return; }

    const next = { ...customOrder };
    const getIdList = (sk) => {
      const existing = next[sk];
      if (Array.isArray(existing)) return existing.map(e => typeof e === 'string' ? e : e.id);
      return getItemsForSection(sk).map(i => i.id);
    };

    const sourceIds = getIdList(dragState.sectionKey);
    const targetIds = getIdList(targetSectionKey);

    next[dragState.sectionKey] = sourceIds.filter(id => id !== dragState.itemId);
    next[targetSectionKey] = [...targetIds, dragState.itemId];

    saveOrder(next);
    setDragState(null);
  };

  const resetOrder = () => {
    localStorage.removeItem('sidebarOrder');
    setCustomOrder({});
  };

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
    // v4_agenda_ack_001: bij klik op chat/calendar nav-item → ack alle urgente agenda items
    if ((item.id === 'chat' || item.id === 'calendar') && user?.id && urgentGlow[item.id]) {
      const API = process.env.REACT_APP_BACKEND_URL;
      fetch(`${API}/api/urgent/acknowledge?user_id=${user.id}&all_agenda=true`, { method: 'POST' })
        .then(() => {
          setUrgentGlow(g => {
            const c = { ...g };
            delete c[item.id];
            // ook chat-spark sub-tab glow weg
            if (item.id === 'chat') delete c['chat-spark'];
            return c;
          });
        })
        .catch(() => {});
    }
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
            // Verberg hele sectie op basis van gradatie (v4_gradatie_visibility_001)
            const visibility = getVisibilityForGradatie(user?.gradatie);
            if (visibility.hideSection.includes(key)) return null;

            // Pas custom volgorde + cross-sectie relocations toe
            const allItems = getItemsForSection(key);
            // Filter admin-only items voor non-admins + gradatie-hides
            const visibleItems = allItems.filter(item =>
              (!item.adminOnly || isAdmin) && !visibility.hide.includes(item.id)
            );
            if (visibleItems.length === 0) return null;

            return (
              <div
                key={key}
                className="mb-6"
                onDragOver={handleDragOver}
                onDrop={(e) => {
                  // Alleen drop-op-sectie activeren als we niet op een specifiek item droppen
                  if (e.target === e.currentTarget || e.target.closest('[data-section-empty]')) {
                    handleDropOnSection(key);
                  }
                }}
              >
                {!sidebarCollapsed && (
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
                    {section.label}
                  </p>
                )}
                <div className="space-y-1">
                  {visibleItems.map(item => {
                    const itemGlow = urgentGlow[item.id];
                    const itemUrgentCount = urgentItems.filter(it => {
                      if (item.id === 'chat' || item.id === 'calendar') {
                        return it.kind === 'agenda';
                      }
                      return false;
                    }).length;
                    return (
                      <NavItem
                        key={item.id}
                        item={item}
                        isActive={activePage === item.id}
                        isCollapsed={sidebarCollapsed}
                        glow={itemGlow}
                        glowCount={itemUrgentCount}
                        onClick={() => handleNavClick(item)}
                        draggable={!sidebarCollapsed}
                        isDragging={dragState?.itemId === item.id}
                        onDragStart={() => handleDragStart(key, item.id)}
                        onDragOver={handleDragOver}
                        onDrop={() => handleDropOnItem(key, item.id)}
                        onDragEnd={() => setDragState(null)}
                      />
                    );
                  })}
                  {/* Drop zone aan einde van sectie */}
                  {!sidebarCollapsed && dragState && dragState.sectionKey !== key && (
                    <div
                      data-section-empty
                      onDragOver={handleDragOver}
                      onDrop={() => handleDropOnSection(key)}
                      className="h-10 rounded-xl border-2 border-dashed border-amber-500/30 bg-amber-500/5 flex items-center justify-center text-[10px] text-amber-400"
                    >
                      Laat hier los in {section.label}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {/* Reset volgorde knop */}
          {!sidebarCollapsed && Object.keys(customOrder).length > 0 && (
            <button onClick={resetOrder}
              data-testid="reset-sidebar-order"
              className="w-full mt-2 text-[10px] text-slate-600 hover:text-amber-400 transition-colors px-3 py-1">
              ↺ Reset menuvolgorde
            </button>
          )}
        </nav>

        {/* User & Collapse */}
        <div className="border-t border-slate-800 p-3">
          {/* User info */}
          {!sidebarCollapsed && (
            <div className="flex items-center gap-3 px-3 py-2 mb-2">
              <UserAvatar user={user} size="sm" rounded="rounded-lg" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user?.naam}</p>
                <p className="text-xs text-slate-500">{user?.rol || user?.gradatie_titel || (isAdmin ? `Gradatie ${user?.gradatie}` : '')}</p>
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
        {/* v5_no_bell_001 — notification bell verborgen op verzoek user; De Dood barkt privé in DM waar nodig */}
        {children}
      </main>
      {/* v4_update_bark_001 — privacy + deploy update barks */}
      {user?.id && <BarkQueueOverlay userId={user.id} />}
    </div>
  );
}

// Navigation Item Component (drag-and-drop)
function NavItem({ item, isActive, isCollapsed, glow, glowCount, onClick, draggable, isDragging, onDragStart, onDragOver, onDrop, onDragEnd }) {
  const Icon = item.icon;
  const [dragOver, setDragOver] = React.useState(false);

  // Glow severity → kleur + animatie
  const glowStyle = glow === 'red'
    ? 'ring-2 ring-red-500/60 shadow-[0_0_12px_rgba(239,68,68,0.5)] animate-pulse'
    : glow === 'amber'
      ? 'ring-2 ring-amber-400/50 shadow-[0_0_10px_rgba(251,191,36,0.35)]'
      : '';
  const glowIconColor = glow === 'red' ? 'text-red-400' : glow === 'amber' ? 'text-amber-300' : '';

  return (
    <div
      draggable={!!draggable}
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = 'move';
        onDragStart && onDragStart();
      }}
      onDragOver={(e) => {
        if (onDragOver) {
          onDragOver(e);
          setDragOver(true);
        }
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={() => {
        setDragOver(false);
        onDrop && onDrop();
      }}
      onDragEnd={() => {
        setDragOver(false);
        onDragEnd && onDragEnd();
      }}
      className={`group relative ${dragOver ? 'ring-1 ring-amber-500/40 rounded-xl' : ''} ${isDragging ? 'opacity-40' : ''}`}
    >
      <button
        onClick={onClick}
        data-glow={glow || undefined}
        className={`
          w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all cursor-pointer
          ${isActive
            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
            : `text-slate-400 hover:text-white hover:bg-slate-800/50 ${glowStyle}`
          }
          ${isCollapsed ? 'justify-center' : ''}
        `}
        title={isCollapsed ? item.label : (draggable ? `${item.label} (sleep om te verplaatsen)` : item.label)}
        data-testid={`nav-${item.id}`}
      >
        <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-amber-400' : glowIconColor}`} />
        {!isCollapsed && (
          <span className="flex-1 text-left text-sm font-medium">{item.label}</span>
        )}
        {!isCollapsed && !!glowCount && glowCount > 0 && (
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${glow === 'red' ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'}`}>
            {glowCount}
          </span>
        )}
        {!isCollapsed && draggable && !glow && (
          <span className="opacity-0 group-hover:opacity-100 text-slate-600 text-xs transition-opacity cursor-grab active:cursor-grabbing">⋮⋮</span>
        )}
      </button>
    </div>
  );
}

export default MainLayout;
