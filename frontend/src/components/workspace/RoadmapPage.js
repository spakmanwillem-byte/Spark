import React, { useState } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Map, CheckCircle, Clock, Circle, ChevronRight, ChevronDown,
  Rocket, Target, Flag, Star, Zap, Brain, Shield, Globe,
  Package, MessageSquare, Coins, Users, BarChart3, Layers
} from 'lucide-react';

const phases = [
  {
    id: 'phase-0',
    title: 'Phase 0: Core Foundation',
    status: 'done',
    progress: 100,
    color: '#22c55e',
    icon: Shield,
    period: 'Q1 2026',
    items: [
      { title: 'FastAPI backend met JSON storage', status: 'done' },
      { title: 'Auth module (login, users, gradaties)', status: 'done' },
      { title: 'React frontend met dark theme', status: 'done' },
      { title: 'Sidebar navigatie met secties', status: 'done' },
      { title: 'Dashboard met live data kaarten', status: 'done' },
    ],
  },
  {
    id: 'phase-1',
    title: 'Phase 1: Knowledge & Workspace',
    status: 'done',
    progress: 100,
    color: '#22c55e',
    icon: Brain,
    period: 'Q1 2026',
    items: [
      { title: 'Kennisbank zoekengine (2400+ kaarten)', status: 'done' },
      { title: 'Knowledge card CRUD met 4 lagen', status: 'done' },
      { title: 'Gesprekken (Spark AI, Community, Privé)', status: 'done' },
      { title: 'Agenda module', status: 'done' },
      { title: 'Emotie analyse systeem', status: 'done' },
      { title: 'Verbanden / Knowledge Graph', status: 'done' },
      { title: 'Triggers beheer', status: 'done' },
    ],
  },
  {
    id: 'phase-2',
    title: 'Phase 2: Modules & Gamification',
    status: 'done',
    progress: 100,
    color: '#22c55e',
    icon: Package,
    period: 'Q1 2026',
    items: [
      { title: 'Achievements systeem (13 milestones, XP)', status: 'done' },
      { title: 'Integraties (bestandsbrowser + sandbox)', status: 'done' },
      { title: 'Wallet overzicht', status: 'done' },
      { title: 'Trader interface', status: 'done' },
      { title: 'Instellingen (6 tabs)', status: 'done' },
      { title: 'Analytics dashboard', status: 'done' },
    ],
  },
  {
    id: 'phase-3',
    title: 'Phase 3: Backend Integratie',
    status: 'active',
    progress: 15,
    color: '#f59e0b',
    icon: Zap,
    period: 'Q2 2026',
    items: [
      { title: 'Instellingen API (opslaan/laden)', status: 'planned' },
      { title: 'Wallet API koppelen aan oude data', status: 'planned' },
      { title: 'Trader API met live data', status: 'planned' },
      { title: 'Agenda persistent opslaan', status: 'planned' },
      { title: 'Gesprekken opslaan in JSON', status: 'planned' },
      { title: 'Analytics met echte metrics', status: 'planned' },
    ],
  },
  {
    id: 'phase-4',
    title: 'Phase 4: AI & Communicatie',
    status: 'planned',
    progress: 0,
    color: '#3b82f6',
    icon: MessageSquare,
    period: 'Q2-Q3 2026',
    items: [
      { title: 'Spark Brain - AI conversatie engine', status: 'planned' },
      { title: 'TTS / STT integratie', status: 'planned' },
      { title: 'Community module', status: 'planned' },
      { title: 'Notificatie systeem', status: 'planned' },
      { title: 'Externe integraties (Bitvavo, Telegram)', status: 'planned' },
    ],
  },
  {
    id: 'phase-5',
    title: 'Phase 5: Deployment & Polish',
    status: 'planned',
    progress: 0,
    color: '#a855f7',
    icon: Rocket,
    period: 'Q3 2026',
    items: [
      { title: 'Standalone deployment setup', status: 'planned' },
      { title: 'Data backup & restore systeem', status: 'planned' },
      { title: 'Performance optimalisatie', status: 'planned' },
      { title: 'Documentatie & handleiding', status: 'planned' },
      { title: 'Beveiligingsaudit', status: 'planned' },
    ],
  },
];

export function RoadmapPage({ onNavigate }) {
  const [expandedPhase, setExpandedPhase] = useState('phase-3');

  const totalItems = phases.reduce((a, p) => a + p.items.length, 0);
  const doneItems = phases.reduce((a, p) => a + p.items.filter(i => i.status === 'done').length, 0);
  const activePhase = phases.find(p => p.status === 'active');
  const overallPct = Math.round((doneItems / totalItems) * 100);

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
                {activePhase && <span className="text-amber-400 ml-2">Huidige fase: {activePhase.title}</span>}
              </p>
            </div>
            <div className="text-right">
              <span className="text-3xl font-bold text-amber-400">{overallPct}%</span>
            </div>
          </div>
          <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${overallPct}%`, background: 'linear-gradient(90deg, #22c55e, #f59e0b, #a855f7)' }} />
          </div>
          {/* Mini phase indicators */}
          <div className="flex gap-2 mt-3">
            {phases.map(p => (
              <div key={p.id} className="flex-1 h-1.5 rounded-full" style={{
                background: p.status === 'done' ? p.color : p.status === 'active' ? `${p.color}60` : '#1e293b'
              }} />
            ))}
          </div>
        </div>

        {/* Timeline */}
        <div className="space-y-3">
          {phases.map((phase, idx) => {
            const isExpanded = expandedPhase === phase.id;
            const PhaseIcon = phase.icon;
            const doneCount = phase.items.filter(i => i.status === 'done').length;

            return (
              <div key={phase.id} className="relative">
                {/* Timeline connector */}
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
                    {/* Phase icon */}
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
                          <div className="h-full rounded-full transition-all" style={{ width: `${phase.progress}%`, background: phase.color }} />
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

                {/* Expanded items */}
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
