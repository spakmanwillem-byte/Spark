import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Map, CheckCircle, Clock, Circle, ChevronRight, ChevronDown,
  Rocket, Target, Flag, Star, Zap, Brain, Shield, Globe,
  Package, MessageSquare, Coins, Users, BarChart3, Layers,
  BookOpen, StickyNote, BookHeart, Award, Wallet, Trophy,
  Settings, Puzzle, Calendar, Home, TrendingUp, Link2, Sparkles,
  Lightbulb,
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const phases = [
  {
    id: 'phase-0',
    title: 'Phase 0: Core Setup',
    status: 'done',
    color: '#22c55e',
    icon: Shield,
    period: 'Maart 2026',
    items: [
      { title: 'FastAPI backend met JSON storage (geen MongoDB)', status: 'done' },
      { title: 'React frontend met dark theme', status: 'done' },
      { title: 'Auth module (login, users, gradaties)', status: 'done' },
      { title: 'Sidebar navigatie (4 secties)', status: 'done' },
    ],
  },
  {
    id: 'phase-1',
    title: 'Phase 1: Workspace',
    status: 'done',
    color: '#22c55e',
    icon: Home,
    period: 'Maart 2026',
    items: [
      { title: 'Dashboard met live data kaarten', status: 'done' },
      { title: 'Gesprekken (Spark AI / Community / Privé tabs)', status: 'done' },
      { title: 'Kennisbank zoekengine (2400+ kaarten, CRUD)', status: 'done' },
      { title: 'Agenda module', status: 'done' },
      { title: 'Dagboek met mood tracking', status: 'done' },
      { title: 'Notities & Taken (hybrid)', status: 'done' },
      { title: 'Roadmap overzicht', status: 'done' },
    ],
  },
  {
    id: 'phase-2',
    title: 'Phase 2: Spark AI',
    status: 'done',
    color: '#22c55e',
    icon: Brain,
    period: 'Maart 2026',
    items: [
      { title: 'Triggers beheer (toevoegen/verwijderen)', status: 'done' },
      { title: 'Emotie analyse systeem', status: 'done' },
      { title: 'Verbanden / Knowledge Graph', status: 'done' },
      { title: 'Spark Brain (identiteit & persoonlijkheid)', status: 'done' },
      { title: 'Spark Profiel (23 categorieën)', status: 'done' },
    ],
  },
  {
    id: 'phase-3',
    title: 'Phase 3: Modules',
    status: 'done',
    color: '#22c55e',
    icon: Package,
    period: 'Maart 2026',
    items: [
      { title: 'Trader interface', status: 'done' },
      { title: 'Live Bitvavo candles + Watchlist (5 coins)', status: 'done' },
      { title: 'Monitor systeem (Bollinger Band engine)', status: 'done' },
      { title: 'Snel Handelen (mock/live trades)', status: 'done' },
      { title: 'Achievements (13 milestones, XP, rarity)', status: 'done' },
      { title: 'Leaderboard (ranglijst + podium)', status: 'done' },
      { title: 'Wallet overzicht + opname systeem', status: 'done' },
      { title: 'ROAR Token Winkel (kopen/verkopen)', status: 'done' },
      { title: 'Boekhouding (4 kasboeken)', status: 'done' },
      { title: 'Persoonskaarten (6 personen)', status: 'done' },
      { title: 'Community Chat (3 bots)', status: 'done' },
      { title: 'Integraties (bestandsbrowser + module sandbox)', status: 'done' },
    ],
  },
  {
    id: 'phase-4',
    title: 'Phase 4: Beheer',
    status: 'done',
    color: '#22c55e',
    icon: Settings,
    period: 'Maart 2026',
    items: [
      { title: 'Mijn Profiel pagina', status: 'done' },
      { title: 'Gebruikers admin', status: 'done' },
      { title: 'Analytics (Systeem / Network / Layer)', status: 'done' },
      { title: 'Instellingen (6 tabs: Algemeen, Beeld, Geluid, Integraties, Features, Tips)', status: 'done' },
    ],
  },
  {
    id: 'phase-5',
    title: 'Phase 5: Backend Koppeling',
    status: 'active',
    color: '#f59e0b',
    icon: Zap,
    period: 'Q2 2026',
    items: [
      { title: 'Dagboek API (opslaan/laden entries)', status: 'done' },
      { title: 'Notities & Taken API (CRUD + sync)', status: 'done' },
      { title: 'Wallet koppelen aan oude wallet data', status: 'done' },
      { title: 'Trader API met live data', status: 'done' },
      { title: 'Agenda persistent opslaan', status: 'done' },
      { title: 'Gesprekken opslaan in JSON', status: 'done' },
      { title: 'Instellingen API (settings.json)', status: 'planned' },
      { title: 'Leaderboard berekenen uit echte user data', status: 'planned' },
      { title: 'Analytics met echte metrics', status: 'planned' },
    ],
  },
  {
    id: 'phase-6',
    title: 'Phase 6: Spark Brain & AI',
    status: 'planned',
    color: '#3b82f6',
    icon: Brain,
    period: 'Q2-Q3 2026',
    items: [
      { title: 'Spark Brain identiteit beheer', status: 'done' },
      { title: 'TTS / STT integratie', status: 'done' },
      { title: 'Notificatie systeem', status: 'done' },
      { title: 'Spark Profiel (biografie, filosofie, ethiek)', status: 'done' },
      { title: 'Willem Personality profiel', status: 'done' },
      { title: 'Uitgebreid profiel (adres, noodcontact)', status: 'done' },
      { title: 'Roadmap API backend', status: 'done' },
      { title: 'AI conversatie engine', status: 'planned' },
      { title: 'Externe integraties (Bitvavo live, Telegram)', status: 'planned' },
    ],
  },
  {
    id: 'phase-7',
    title: 'Phase 7: Deployment & Polish',
    status: 'planned',
    color: '#a855f7',
    icon: Rocket,
    period: 'Q3 2026',
    items: [
      { title: 'Standalone deployment setup', status: 'planned' },
      { title: 'Data backup & restore', status: 'planned' },
      { title: 'Performance optimalisatie', status: 'planned' },
      { title: 'Documentatie & handleiding', status: 'planned' },
      { title: 'Beveiligingsaudit', status: 'planned' },
    ],
  },
];

export function RoadmapPage({ onNavigate }) {
  const { user } = useAuth();
  const [expandedPhase, setExpandedPhase] = useState(
    phases.find(p => p.status === 'active')?.id || phases[0].id
  );
  // v4_roadmap_user_ideas_001 — toon bug-tickets / ideeën van user op roadmap
  const [myBugs, setMyBugs] = useState([]);
  const isAdmin = (user?.gradatie ?? 7) <= 2;
  useEffect(() => {
    if (!user?.id) return;
    // Alleen admins krijgen /bugs/list (403 anders) — voor non-admin probeer mijn-bugs endpoint
    const url = isAdmin
      ? `${API}/api/bugs/list?viewer_id=${user.id}`
      : `${API}/api/bugs/mine?user_id=${user.id}`;
    fetch(url)
      .then(r => r.ok ? r.json() : { bugs: [] })
      .then(d => {
        const all = d.bugs || [];
        // Voor admin filter op eigen tickets, voor non-admin returnt API al alleen eigen
        const mine = isAdmin ? all.filter(b => b.created_by_id === user.id) : all;
        setMyBugs(mine);
      })
      .catch(() => {});
  }, [user?.id, isAdmin]);

  const totalItems = phases.reduce((a, p) => a + p.items.length, 0);
  const doneItems = phases.reduce((a, p) => a + p.items.filter(i => i.status === 'done').length, 0);
  const overallPct = Math.round((doneItems / totalItems) * 100);
  const activePhase = phases.find(p => p.status === 'active');

  return (
    <MainLayout activePage="roadmap" onNavigate={onNavigate}>
      <div data-testid="roadmap-page" className="p-4 md:p-6 space-y-5 max-w-4xl mx-auto">

        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
            <Map className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Roadmap</h1>
            <p className="text-xs text-slate-500">Spark Core 2.0 ontwikkelplan</p>
          </div>
        </div>

        {/* Overall progress */}
        <div className="p-5 rounded-xl border border-amber-500/20" style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.06), rgba(234,88,12,0.03))' }}>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-lg font-bold text-white">Totale Voortgang</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {doneItems} van {totalItems} taken afgerond
                {activePhase && <span className="text-amber-400 ml-2">Nu: {activePhase.title}</span>}
              </p>
            </div>
            <div className="text-right">
              <span className="text-3xl font-bold text-amber-400">{overallPct}%</span>
            </div>
          </div>
          <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${overallPct}%`, background: 'linear-gradient(90deg, #22c55e, #f59e0b, #a855f7)' }} />
          </div>
          <div className="flex gap-1.5 mt-3">
            {phases.map(p => {
              const pDone = p.items.filter(i => i.status === 'done').length;
              const pPct = p.items.length > 0 ? (pDone / p.items.length) * 100 : 0;
              return (
                <div key={p.id} className="flex-1 h-1.5 rounded-full overflow-hidden bg-slate-800">
                  <div className="h-full rounded-full" style={{ width: `${pPct}%`, background: p.color }} />
                </div>
              );
            })}
          </div>
        </div>

        {/* v4_roadmap_user_ideas_001 — Jouw Ideeën */}
        {myBugs.length > 0 && (
          <div data-testid="roadmap-user-ideas" className="p-5 rounded-xl border border-amber-500/20 bg-slate-900/30">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-5 h-5 text-amber-400" />
              <h2 className="text-base font-bold text-white">Jouw Ideeën & Tickets</h2>
              <span className="text-[10px] px-2 py-0.5 bg-amber-500/15 text-amber-300 rounded-full">{myBugs.length}</span>
            </div>
            <div className="space-y-1.5">
              {myBugs.slice(0, 8).map(b => {
                const status = b.status || 'open';
                const sBg =
                  status === 'opgelost' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' :
                  status === 'in_behandeling' ? 'bg-blue-500/10 text-blue-300 border-blue-500/30' :
                  status === 'afgewezen' ? 'bg-slate-700/40 text-slate-500 border-slate-700' :
                  'bg-amber-500/10 text-amber-300 border-amber-500/30';
                return (
                  <div key={b.id} data-testid={`my-bug-${b.id}`}
                    className="flex items-start gap-3 p-3 bg-slate-800/30 hover:bg-slate-800/50 border border-slate-800/60 rounded-lg transition-colors">
                    <span className={`text-[9px] px-1.5 py-0.5 rounded border uppercase font-medium ${sBg} flex-shrink-0 mt-0.5`}>
                      {status === 'in_behandeling' ? 'in behandeling' : status}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white">{b.description || b.titel || b.summary || '(geen omschrijving)'}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        {b.created_at ? new Date(b.created_at).toLocaleString('nl-NL', {day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}) : ''}
                        {b.page && <span className="ml-2 text-slate-400">· {b.page}</span>}
                      </p>
                    </div>
                  </div>
                );
              })}
              {myBugs.length > 8 && (
                <p className="text-[10px] text-slate-500 text-center pt-1">+ {myBugs.length - 8} meer</p>
              )}
            </div>
          </div>
        )}

        {/* Timeline */}
        <div className="space-y-3">
          {phases.map((phase, idx) => {
            const isExpanded = expandedPhase === phase.id;
            const PhaseIcon = phase.icon;
            const doneCount = phase.items.filter(i => i.status === 'done').length;
            const phasePct = phase.items.length > 0 ? Math.round((doneCount / phase.items.length) * 100) : 0;

            return (
              <div key={phase.id} className="relative">
                {idx < phases.length - 1 && (
                  <div className="absolute left-[19px] top-[56px] w-0.5 h-[calc(100%-32px)] z-0" style={{
                    background: phase.status === 'done' ? '#22c55e40' : '#1e293b'
                  }} />
                )}

                <button
                  data-testid={`phase-${phase.id}`}
                  onClick={() => setExpandedPhase(isExpanded ? null : phase.id)}
                  className={`relative z-10 w-full text-left p-4 rounded-xl border transition-all ${
                    phase.status === 'active'
                      ? 'border-amber-500/30 bg-amber-500/5 hover:bg-amber-500/8'
                      : 'border-slate-800 bg-slate-900/50 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{
                      background: phase.status === 'done' ? `${phase.color}15` : phase.status === 'active' ? `${phase.color}20` : '#1e293b',
                      border: phase.status === 'active' ? `2px solid ${phase.color}40` : 'none',
                    }}>
                      {phase.status === 'done'
                        ? <CheckCircle className="w-5 h-5" style={{ color: phase.color }} />
                        : phase.status === 'active'
                          ? <PhaseIcon className="w-5 h-5" style={{ color: phase.color }} />
                          : <Circle className="w-5 h-5 text-slate-600" />
                      }
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-bold text-white">{phase.title}</h3>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                          phase.status === 'done' ? 'bg-green-500/10 text-green-400' :
                          phase.status === 'active' ? 'bg-amber-500/10 text-amber-400' :
                          'bg-slate-700/50 text-slate-500'
                        }`}>
                          {phase.status === 'done' ? 'Voltooid' : phase.status === 'active' ? 'Actief' : 'Gepland'}
                        </span>
                        <span className="text-[10px] text-slate-600">{phase.period}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-1.5">
                        <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden max-w-[200px]">
                          <div className="h-full rounded-full transition-all" style={{ width: `${phasePct}%`, background: phase.color }} />
                        </div>
                        <span className="text-[10px] text-slate-500">{doneCount}/{phase.items.length}</span>
                      </div>
                    </div>

                    {isExpanded
                      ? <ChevronDown className="w-4 h-4 text-slate-500 flex-shrink-0" />
                      : <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0" />
                    }
                  </div>
                </button>

                {isExpanded && (
                  <div className="ml-5 pl-5 border-l-2 mt-1 space-y-1 py-2" style={{ borderColor: `${phase.color}30` }}>
                    {phase.items.map((item, i) => (
                      <div key={i} className="flex items-center gap-2.5 py-1.5 px-3 rounded-lg hover:bg-slate-800/30 transition-colors">
                        {item.status === 'done'
                          ? <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                          : item.status === 'active'
                            ? <Clock className="w-4 h-4 text-amber-400 flex-shrink-0 animate-pulse" />
                            : <Circle className="w-4 h-4 text-slate-600 flex-shrink-0" />
                        }
                        <span className={`text-sm ${item.status === 'done' ? 'text-slate-300' : item.status === 'active' ? 'text-white' : 'text-slate-500'}`}>
                          {item.title}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </MainLayout>
  );
}

export default RoadmapPage;
