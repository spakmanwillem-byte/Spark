import React, { useState, useEffect } from 'react';
import { 
  Zap, Home, MessageSquare, Users, Calendar, Brain, 
  Sparkles, Zap as Bolt, Link2, Puzzle, UsersRound, MessageCircle, Volume2,
  BarChart3, Target, ChevronLeft, ChevronRight, LogOut,
  BookOpen, Settings, Shield, Wallet, Trophy, Bell, TrendingUp, User, Map,
  BookHeart, StickyNote, Award, ShoppingBag, BookMarked, Archive, HandHeart,
  Activity, HelpCircle, Beaker
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { UserAvatar } from '../common/UserAvatar';
import { BarkQueueOverlay } from '../common/BarkQueueOverlay';
import { HelpBark } from '../shared/HelpBark';

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
      // v11_spark_admin_only_001 — Hele Spark AI sectie alleen zichtbaar in admin-mode.
      { id: 'spark-overzicht', label: 'Brein-overzicht', icon: Brain, path: '/spark/overzicht', adminOnly: true },
      { id: 'spark-brain', label: 'Spark Brain', icon: Brain, path: '/spark/brain', adminOnly: true },
      { id: 'synapse', label: 'Synapslaag', icon: Brain, path: '/spark/synapse', adminOnly: true },
      { id: 'knowledge-v2', label: 'Kennisbank', icon: BookOpen, path: '/knowledge', adminOnly: true },
      { id: 'triggers', label: 'Triggers', icon: Bolt, path: '/spark/triggers', adminOnly: true },
      { id: 'emotions', label: 'Emoties', icon: Sparkles, path: '/spark/emotions', adminOnly: true },
      { id: 'connections', label: 'Verbanden', icon: Link2, path: '/spark/connections', adminOnly: true },
      { id: 'integrations', label: 'Integraties', icon: Puzzle, path: '/modules/integrations', adminOnly: true },
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
    ]
  },
  admin: {
    label: 'BEHEER',
    items: [
      { id: 'profiel', label: 'Mijn Profiel', icon: User, path: '/profiel' },
      { id: 'users', label: 'Gebruikers', icon: Users, path: '/admin/users', adminOnly: true },
      { id: 'analytics', label: 'Analytics', icon: BarChart3, path: '/admin/analytics', adminOnly: true },
      { id: 'sandbox', label: 'Widget Kladblok', icon: Beaker, path: '/admin/sandbox', adminOnly: true },
      { id: 'settings', label: 'Instellingen', icon: Settings, path: '/admin/settings', adminOnly: true },
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
// v6_gradatie_visibility_003 — Bugfix: spark-items moeten ook verborgen blijven nadat user
// ze via drag-drop naar een andere sectie verplaatst (dus ook in `hide` per item).
// Grad 1 (eigenaar): alle tabs
// Grad 2 (admin/fam): alle workspace, geen voice-onder-workspace (komt later als kader in Features)
// Grad 3 (vrienden): geen voice, geen Spark AI sectie, geen Integraties
// Grad 4 (collega's): zelfde als 3 + geen voice
// Grad 5: + geen Trade + geen Boekhouding
// Grad 6: + geen Dagboek + geen Achievements/Leaderboard (die zijn voor Community-members)
// Grad 7: + geen Agenda (krijgt Agenda terug bij upgrade naar 6) + geen Boekhouding (heeft Wallet).
// v11_grad7_archief_001 — Archief WEL zichtbaar; daar staat gespreksgeschiedenis, die
// heeft ook grad 7 nodig om zichzelf terug te kunnen lezen.
// v11_community_only_items_001 — Achievements + Leaderboard vanaf grad 5 (Community Member).
const SPARK_ONLY_ITEMS = ['triggers', 'emotions', 'emotion-routing', 'connections'];
const COMMUNITY_ONLY_ITEMS = ['achievements', 'leaderboard'];
const VISIBILITY_RULES = {
  1: { hideSection: [], hide: [] },
  2: { hideSection: [], hide: ['voice'] },
  3: { hideSection: ['spark'], hide: ['voice', 'integrations', 'analytics', 'settings', ...SPARK_ONLY_ITEMS] },
  4: { hideSection: ['spark'], hide: ['voice', 'integrations', 'users', 'analytics', 'settings', ...SPARK_ONLY_ITEMS] },
  5: { hideSection: ['spark'], hide: ['voice', 'integrations', 'users', 'analytics', 'settings', 'trade', 'boekhouding', ...SPARK_ONLY_ITEMS] },
  6: { hideSection: ['spark'], hide: ['voice', 'integrations', 'users', 'analytics', 'settings', 'trade', 'boekhouding', 'dagboek', ...SPARK_ONLY_ITEMS, ...COMMUNITY_ONLY_ITEMS] },
  7: { hideSection: ['spark'], hide: ['voice', 'integrations', 'users', 'analytics', 'settings', 'trade', 'boekhouding', 'dagboek', 'calendar', ...SPARK_ONLY_ITEMS, ...COMMUNITY_ONLY_ITEMS] },
};

export function getVisibilityForGradatie(grad) {
  return VISIBILITY_RULES[grad] || VISIBILITY_RULES[7];
}

export function MainLayout({ children, activePage = 'dashboard', onNavigate }) {
  const { user, logout, isAdmin, adminCapable, adminModeActive, enableAdmin, disableAdmin } = useAuth();
  const [adminKeyPrompt, setAdminKeyPrompt] = React.useState(false);
  const [adminKeyInput, setAdminKeyInput] = React.useState('');
  const [adminKeyError, setAdminKeyError] = React.useState('');
  // v12_sidebar_collapse_persist_001 — Sidebar-collapse state overleeft page-nav
  // (MainLayout wordt per pagina opnieuw gemount, dus useState resette elke keer).
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try { return localStorage.getItem('sidebarCollapsed') === '1'; }
    catch { return false; }
  });
  useEffect(() => {
    try { localStorage.setItem('sidebarCollapsed', sidebarCollapsed ? '1' : '0'); }
    catch {}
  }, [sidebarCollapsed]);
  const [showHelp, setShowHelp] = useState(false);  // v6_help_001

  // v6_help_001 — Luister naar 'spark:open-help' event vanuit chat ("help" trigger)
  useEffect(() => {
    const onOpenHelp = () => setShowHelp(true);
    window.addEventListener('spark:open-help', onOpenHelp);
    return () => window.removeEventListener('spark:open-help', onOpenHelp);
  }, []);

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

  // v13s_login_identity_001 — Systeem-branding (naam + versie + logo) uit spark_identity + settings/system
  // Zelfde bron als login-scherm — 1 plek beheren, overal consistent
  const [branding, setBranding] = useState({ naam: 'Spark', versie: '2.0', logo_url: null, primary: '#f59e0b', accent: '#ea580c' });
  useEffect(() => {
    const API = process.env.REACT_APP_BACKEND_URL;
    Promise.all([
      fetch(`${API}/api/spark/identity`).then(r => r.json()).catch(() => ({})),
      fetch(`${API}/api/settings/system`).then(r => r.json()).catch(() => ({ settings: {} })),
    ]).then(([id, sys]) => {
      const s = sys.settings || {};
      setBranding({
        naam: id?.naam || 'Spark',
        versie: id?.versie || '',
        logo_url: s.spark_logo_url || null,
        primary: s.app_primary_accent || '#f59e0b',
        accent: s.login_corner_glow_color_b || '#ea580c',
      });
    });
  }, []);
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

      // v11_glow_no_self_glow_001 — als user al op de doel-tab staat, geen glow
      // (was: trader-intent op Trade-tab liet Trade-tab tóch pulseren)
      // Fix v11.1: routes zoals '/modules/trade' laten split('/')[0] = 'modules' geven.
      // Gebruik nu het LAATSTE pad-segment zodat '/modules/trade' → 'trade' matcht.
      try {
        const segs = window.location.pathname.split('/').filter(Boolean);
        const currentPage = segs.length ? segs[segs.length - 1] : 'dashboard';
        const wantedTab = String(targetId || '').replace(/^nav-/, '');
        if (currentPage === wantedTab) return;
      } catch {}

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
    // v11_glow_clear_on_nav_001 — verwijder ALLE spark-nav-glow classes bij nav-klik.
    // Was: glow van trader-intent bleef 6s staan ook op de tab die je aanklikte.
    try {
      document.querySelectorAll('.spark-nav-glow').forEach(el => el.classList.remove('spark-nav-glow'));
    } catch {}
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
        {/* v13s_login_identity_001 — Logo + naam + versie uit spark_identity/settings.
            Zelfde bron als login-scherm — 1 plek beheren via Beheer → Instellingen → Beeld. */}
        <div className="h-16 flex items-center px-4 border-b border-slate-800">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center shadow-lg cursor-pointer overflow-hidden"
            style={{
              background: branding.logo_url ? 'transparent' : `linear-gradient(135deg, ${branding.primary}, ${branding.accent})`,
              boxShadow: `0 8px 22px -12px ${branding.primary}55`,
            }}
            onClick={() => onNavigate && onNavigate('dashboard', '/')}
            data-testid="sidebar-spark-logo"
            title={`${branding.naam}${branding.versie ? ' ' + branding.versie : ''}`}
          >
            {branding.logo_url ? (
              <img
                src={`${process.env.REACT_APP_BACKEND_URL}${branding.logo_url}`}
                alt={branding.naam}
                className="w-full h-full object-cover"
              />
            ) : (
              <Zap className="w-5 h-5 text-white" />
            )}
          </div>
          {!sidebarCollapsed && (
            <div className="ml-3">
              <h1 className="text-lg font-bold text-white">{branding.naam}</h1>
              {branding.versie && <p className="text-xs text-slate-500">v{branding.versie}</p>}
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
          {/* v6_help_001 — Help-knop verwijderd uit sidebar (sessie 23).
              Help opent nu uitsluitend via chat-command "help" in Spark-gesprek/community.
              Sidebar luistert naar window event 'spark:open-help'. */}

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
          {/* v11_admin_mode_001 — Admin-toggle. Alleen zichtbaar als admin_capable. */}
          {adminCapable && !sidebarCollapsed && (
            <div className="px-3 pb-2">
              <button
                data-testid="admin-toggle"
                onClick={() => {
                  if (adminModeActive) { disableAdmin(); }
                  else { setAdminKeyPrompt(true); setAdminKeyError(''); setAdminKeyInput(''); }
                }}
                className={`w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                  adminModeActive
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30'
                    : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'
                }`}
              >
                {adminModeActive ? '🔓 Admin aan' : '🔒 Admin uit'}
              </button>
            </div>
          )}
          {/* Admin-key modal */}
          {adminKeyPrompt && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm"
                 onClick={() => setAdminKeyPrompt(false)}>
              <div className="bg-slate-900 border border-amber-500/40 rounded-2xl p-6 w-96 max-w-[90vw]"
                   onClick={e => e.stopPropagation()}>
                <h3 className="text-lg font-bold text-amber-300 mb-2">🔒 Admin-key</h3>
                <p className="text-xs text-slate-400 mb-4">
                  Voer je admin-key in om admin-features te activeren. Kan altijd weer uit via de knop.
                </p>
                <input
                  data-testid="admin-key-input"
                  type="password"
                  autoFocus
                  value={adminKeyInput}
                  onChange={e => setAdminKeyInput(e.target.value)}
                  onKeyDown={async (e) => {
                    if (e.key === 'Enter') {
                      try { await enableAdmin(adminKeyInput); setAdminKeyPrompt(false); }
                      catch (err) { setAdminKeyError(err.message); }
                    }
                  }}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:border-amber-500 focus:outline-none"
                  placeholder="admin-key..."
                />
                {adminKeyError && <p className="text-red-400 text-xs mt-2">{adminKeyError}</p>}
                <div className="flex gap-2 mt-4 justify-end">
                  <button onClick={() => setAdminKeyPrompt(false)}
                    className="px-3 py-1.5 text-xs text-slate-400 hover:text-white rounded-lg">Annuleer</button>
                  <button
                    data-testid="admin-key-submit"
                    onClick={async () => {
                      try { await enableAdmin(adminKeyInput); setAdminKeyPrompt(false); }
                      catch (err) { setAdminKeyError(err.message); }
                    }}
                    className="px-4 py-1.5 text-xs bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 rounded-lg border border-amber-500/40">
                    Admin aan
                  </button>
                </div>
              </div>
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
      {/* v6_help_001 — Help-bark popup */}
      <HelpBark open={showHelp} onClose={() => setShowHelp(false)} userId={user?.id} />
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
        style={isActive ? {
          backgroundColor: 'color-mix(in srgb, var(--glow-base, #f59e0b) 12%, transparent)',
          color: 'var(--glow-base, #f59e0b)',
          borderColor: 'color-mix(in srgb, var(--glow-base, #f59e0b) 25%, transparent)',
          borderWidth: 1,
          borderStyle: 'solid',
        } : undefined}
        className={`
          w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all cursor-pointer
          ${isActive
            ? ''
            : `text-slate-400 hover:text-white hover:bg-slate-800/50 ${glowStyle}`
          }
          ${isCollapsed ? 'justify-center' : ''}
        `}
        title={isCollapsed ? item.label : (draggable ? `${item.label} (sleep om te verplaatsen)` : item.label)}
        data-testid={`nav-${item.id}`}
      >
        <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? '' : glowIconColor}`}
              style={isActive ? { color: 'var(--glow-base, #f59e0b)' } : undefined} />
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
