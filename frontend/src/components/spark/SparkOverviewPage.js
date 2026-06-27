/**
 * SparkOverviewPage (v6_spark_overview_001, 2026-05-28)
 * Helikopter-view over Spark's complete brein.
 *
 * 6 live-teller-kaarten:
 *   1. Spark Brain      → identiteit/normen/bijbel counts
 *   2. Synapslaag       → containers/endpoints/blueprints
 *   3. Kennisbank       → 4 lades + inbox
 *   4. Triggers         → groepen + total triggers
 *   5. Emotie Routering → pipeline runs + top behaviors
 *   6. Verbanden        → graph nodes + edges
 *
 * Klik op kaart → onNavigate naar betreffende sidebar-item.
 */
import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Brain, BookOpen, Zap as Bolt, Activity, Link2, Layers,
  RefreshCw, ChevronRight
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function SparkOverviewPage({ onNavigate }) {
  const [data, setData] = useState({
    brain: null, synapse: null, kb: null,
    triggers: null, pipeline: null, graph: null,
  });
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const safeJson = (p) => fetch(`${API}${p}`).then(r => r.json()).catch(() => null);
      const [brain, synapse, kb, triggers, pipeline, graph] = await Promise.all([
        safeJson('/api/spark/disclaimer'),
        safeJson('/api/synapse/scan'),
        safeJson('/api/kb/v2/stats'),
        safeJson('/api/triggers/all'),
        safeJson('/api/emotion-pipeline/shadow/stats'),
        safeJson('/api/graph/stats'),
      ]);
      setData({ brain, synapse, kb, triggers, pipeline, graph });
      setLastRefresh(new Date());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  // Helpers — null-safe value extraction
  const kbCounts = data.kb?.lades || {};
  const totalKb = Object.values(kbCounts).reduce((s, l) => s + (l.count || 0), 0)
    + (data.kb?.inbox?.count || 0);
  const synSummary = data.synapse?.summary || {};
  const triggerStats = data.triggers?.stats || {};
  const pipelineEmoties = data.pipeline?.by_emotie || {};
  const pipelineBehaviors = data.pipeline?.by_behavior || {};
  const brainCounts = data.brain?.leidende_lagen_counts || {};

  const cards = [
    {
      id: 'spark-brain',
      title: 'Spark Brain',
      subtitle: 'Identiteit · Normen · Bijbel',
      icon: Brain,
      accent: '#f59e0b',
      stats: [
        { label: 'Kernwaarden', value: brainCounts.kernwaarden ?? '-' },
        { label: 'Normen', value: brainCounts.normen ?? '-' },
        { label: 'Bijbel', value: brainCounts.bijbel ?? brainCounts.bijbel_items ?? '-' },
        { label: 'Capabilities', value: brainCounts.capabilities ?? '-' },
      ],
    },
    {
      id: 'synapse',
      title: 'Synapslaag',
      subtitle: 'Spark leest zichzelf',
      icon: Brain,
      accent: '#0ea5e9',
      stats: [
        { label: 'Containers', value: synSummary.total_containers ?? '-' },
        { label: 'Actief', value: synSummary.by_status?.active ?? '-' },
        { label: 'Skelet', value: synSummary.by_status?.skeleton ?? '-' },
        { label: 'Endpoints', value: synSummary.total_endpoints_detected ?? '-' },
      ],
    },
    {
      id: 'knowledge-v2',
      title: 'Kennisbank',
      subtitle: '4 lades + inbox',
      icon: BookOpen,
      accent: '#a855f7',
      stats: [
        { label: '🌸 Voelen', value: kbCounts.voelen?.count ?? '-' },
        { label: '💬 Spreken', value: kbCounts.spreken?.count ?? '-' },
        { label: '🧠 Weten', value: kbCounts.weten?.count ?? '-' },
        { label: '🎭 Doen', value: kbCounts.doen?.count ?? '-' },
        { label: '📥 Inbox', value: data.kb?.inbox?.count ?? '-', warn: true },
      ],
    },
    {
      id: 'triggers',
      title: 'Triggers',
      subtitle: 'Bark-templates & reflexes',
      icon: Bolt,
      accent: '#22c55e',
      stats: [
        { label: 'Groepen', value: triggerStats.total_groups ?? '-' },
        { label: 'Triggers', value: triggerStats.total_triggers ?? '-' },
      ],
    },
    {
      id: 'emotion-routing',
      title: 'Emotie Routering',
      subtitle: '7-laags pipeline · live shadow',
      icon: Activity,
      accent: '#fb923c',
      stats: [
        { label: 'Runs (7d)', value: data.pipeline?.total_runs ?? '-' },
        { label: 'Unieke emoties', value: Object.keys(pipelineEmoties).length },
        { label: 'Behaviors', value: Object.keys(pipelineBehaviors).length },
      ],
      topPills: Object.entries(pipelineEmoties).slice(0, 4).map(([emo, n]) => ({
        label: `${emo} ×${n}`, color: '#fb923c',
      })),
    },
    {
      id: 'connections',
      title: 'Verbanden',
      subtitle: 'Knowledge graph (v2)',
      icon: Link2,
      accent: '#ec4899',
      stats: [
        { label: 'Nodes', value: data.graph?.total_nodes?.toLocaleString('nl') ?? '-' },
        { label: 'Edges', value: data.graph?.total_edges?.toLocaleString('nl') ?? '-' },
      ],
      topPills: (data.graph?.top_tags || []).slice(0, 4).map(t => ({
        label: `${t.tag} ×${t.count}`, color: '#ec4899',
      })),
    },
  ];

  return (
    <MainLayout activePage="spark-overzicht" onNavigate={onNavigate}>
      <div data-testid="spark-overview-page" className="h-full overflow-y-auto">
        <div className="p-4 sm:p-6 max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-3">
                <span className="inline-flex w-10 h-10 rounded-lg items-center justify-center"
                  style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
                  <Brain className="w-6 h-6 text-white" />
                </span>
                Spark Brein-overzicht
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                Helikopter-view · klik op een kaart om dieper te kijken
              </p>
              {lastRefresh && (
                <p className="text-[10px] text-slate-600 mt-1">
                  Laatste refresh: {lastRefresh.toLocaleTimeString('nl-NL')}
                </p>
              )}
            </div>
            <button
              data-testid="spark-overview-refresh"
              onClick={load}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/60 hover:bg-slate-700 border border-slate-700 text-slate-200 text-sm transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Laden…' : 'Verversen'}
            </button>
          </div>

          {/* Cards grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {cards.map(card => (
              <OverviewCard key={card.id} card={card} onClick={() => onNavigate?.(card.id)} />
            ))}
          </div>

          {/* Footer hint */}
          <div className="mt-8 p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-sm text-slate-400">
            <p className="mb-2">
              <Layers className="inline w-4 h-4 mr-1 text-amber-400" />
              <strong className="text-slate-200">Wat zie je hier?</strong>
            </p>
            <p>
              Dit dashboard combineert alle SPARK AI submenu's tot één overzicht.
              Elke kaart toont de live status van een laag in Spark's brein.
              Klik om er dieper in te duiken.
            </p>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}


function OverviewCard({ card, onClick }) {
  const Icon = card.icon;
  return (
    <button
      data-testid={`spark-overview-card-${card.id}`}
      onClick={onClick}
      className="text-left bg-slate-900/40 hover:bg-slate-900/70 border border-slate-800 hover:border-slate-700 rounded-xl p-4 transition group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center"
            style={{ background: `${card.accent}20`, border: `1px solid ${card.accent}40` }}
          >
            <Icon className="w-5 h-5" style={{ color: card.accent }} />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">{card.title}</h3>
            <p className="text-xs text-slate-500">{card.subtitle}</p>
          </div>
        </div>
        <ChevronRight className="w-5 h-5 text-slate-600 group-hover:text-slate-300 transition" />
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-2 mb-2">
        {card.stats.map((s, i) => (
          <div
            key={i}
            className={`px-3 py-2 rounded-lg ${s.warn ? 'bg-amber-500/10 border border-amber-500/30' : 'bg-slate-800/40'}`}
          >
            <div className="text-[10px] uppercase text-slate-500 tracking-wide">{s.label}</div>
            <div className={`text-base font-bold ${s.warn ? 'text-amber-300' : 'text-white'}`}>
              {s.value}
            </div>
          </div>
        ))}
      </div>

      {/* Optional pills */}
      {card.topPills && card.topPills.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {card.topPills.map((p, i) => (
            <span
              key={i}
              className="text-[10px] px-2 py-0.5 rounded-full"
              style={{ background: `${p.color}20`, color: p.color, border: `1px solid ${p.color}40` }}
            >
              {p.label}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}

export default SparkOverviewPage;
