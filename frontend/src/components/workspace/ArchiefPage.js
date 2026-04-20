import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Archive, Search, Filter, Download, Trash2, ChevronDown, ChevronRight,
  Bot, Users, Lock, Sparkles, Zap, BookOpen, Heart, MessageSquare, X
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const channelConfig = {
  spark: { label: 'Spark AI', icon: Sparkles, color: '#f59e0b' },
  community: { label: 'Community', icon: Users, color: '#a855f7' },
  prive: { label: 'Privé', icon: Lock, color: '#06b6d4' },
};

export function ArchiefPage({ onNavigate }) {
  const { user, isAdmin } = useAuth();
  const ownId = user?.id || 'user-001';
  const [viewUserId, setViewUserId] = useState(ownId);
  const [allUsers, setAllUsers] = useState([]);

  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [channel, setChannel] = useState(null);
  const [hasTrigger, setHasTrigger] = useState(false);
  const [hasSnap, setHasSnap] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    params.append('limit', '200');
    if (search) params.append('search', search);
    if (channel) params.append('channel', channel);
    if (hasTrigger) params.append('has_trigger', 'true');
    if (hasSnap) params.append('has_snap', 'true');
    try {
      const [logsRes, statsRes] = await Promise.all([
        fetch(`${API}/api/chat/logs/${viewUserId}?${params}`).then(r => r.json()),
        fetch(`${API}/api/chat/logs/${viewUserId}/stats`).then(r => r.json()),
      ]);
      setLogs(logsRes.conversations || []);
      setStats(statsRes);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [viewUserId, search, channel, hasTrigger, hasSnap]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!isAdmin) return;
    fetch(`${API}/api/auth/users`).then(r => r.json()).then(d => setAllUsers(d.users || [])).catch(() => {});
  }, [isAdmin]);

  const deleteLog = async (id) => {
    if (!confirm('Dit gesprek permanent verwijderen?')) return;
    await fetch(`${API}/api/chat/logs/${viewUserId}/${id}`, { method: 'DELETE' });
    load();
  };

  const exportLogs = () => {
    const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gesprekslog_${viewUserId}_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearFilters = () => {
    setSearch(''); setChannel(null); setHasTrigger(false); setHasSnap(false);
  };

  return (
    <MainLayout activePage="archief" onNavigate={onNavigate}>
      <div data-testid="archief-page" className="h-full flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #64748b, #475569)' }}>
              <Archive className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Gesprekken Archief</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">
                {stats?.total || 0} gesprekken gelogd
              </p>
            </div>
            {isAdmin && allUsers.length > 0 && (
              <select data-testid="archief-user-selector" value={viewUserId}
                onChange={(e) => setViewUserId(e.target.value)}
                className="ml-4 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:outline-none">
                {allUsers.map(u => <option key={u.id} value={u.id}>{u.naam}{u.id === ownId ? ' (jij)' : ''}</option>)}
              </select>
            )}
            <button onClick={exportLogs} disabled={logs.length === 0}
              data-testid="export-logs-btn"
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs text-slate-300 disabled:opacity-40">
              <Download className="w-3.5 h-3.5" /> Export
            </button>
          </div>

          {/* Stats cards */}
          {stats && stats.total > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-3">
              <StatCard label="Totaal" value={stats.total} />
              <StatCard label="Spark" value={stats.channels?.spark || 0} color="#f59e0b" />
              <StatCard label="Community" value={stats.channels?.community || 0} color="#a855f7" />
              <StatCard label="Snaps" value={stats.snap_count || 0} color="#3b82f6" />
              <StatCard label="Gem. woorden" value={stats.avg_words || 0} />
            </div>
          )}

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative flex-1 min-w-[180px] max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input data-testid="archief-search" type="text" value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Zoek in gesprekken..."
                className="w-full pl-8 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-slate-500" />
            </div>
            {Object.entries(channelConfig).map(([key, cfg]) => {
              const Icon = cfg.icon;
              const active = channel === key;
              return (
                <button key={key} data-testid={`filter-${key}`} onClick={() => setChannel(active ? null : key)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                    active ? 'text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                  }`}
                  style={active ? { background: cfg.color } : undefined}>
                  <Icon className="w-3 h-3" /> {cfg.label}
                </button>
              );
            })}
            <button data-testid="filter-snap" onClick={() => setHasSnap(!hasSnap)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                hasSnap ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}>
              <Zap className="w-3 h-3" /> Met snap
            </button>
            <button data-testid="filter-trigger" onClick={() => setHasTrigger(!hasTrigger)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                hasTrigger ? 'bg-amber-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}>
              Trigger
            </button>
            {(search || channel || hasTrigger || hasSnap) && (
              <button onClick={clearFilters} className="text-xs text-slate-500 hover:text-white flex items-center gap-1">
                <X className="w-3 h-3" /> Reset
              </button>
            )}
          </div>
        </div>

        {/* Lijst */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-4xl mx-auto space-y-2">
            {loading ? (
              <div className="text-center py-16 text-xs text-slate-500">Laden...</div>
            ) : logs.length === 0 ? (
              <div className="text-center py-16">
                <Archive className="w-12 h-12 text-slate-700 mx-auto mb-3" />
                <p className="text-sm text-slate-400 mb-1">
                  {stats?.total === 0 ? 'Nog geen gesprekken gelogd' : 'Geen gesprekken matchen de filters'}
                </p>
                {stats?.total === 0 && (
                  <p className="text-xs text-slate-600">Start een gesprek in Gesprekken → Spark AI om te beginnen</p>
                )}
              </div>
            ) : (
              logs.map(c => (
                <LogEntry key={c.id} conv={c} expanded={expandedId === c.id}
                  onToggle={() => setExpandedId(expandedId === c.id ? null : c.id)}
                  onDelete={() => deleteLog(c.id)} />
              ))
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div className="bg-slate-800/40 rounded-lg px-3 py-2">
      <p className="text-[9px] text-slate-500 uppercase tracking-wider">{label}</p>
      <p className="text-sm font-bold" style={{ color: color || '#fff' }}>{value}</p>
    </div>
  );
}

function LogEntry({ conv, expanded, onToggle, onDelete }) {
  const cfg = channelConfig[conv.channel] || channelConfig.spark;
  const Icon = cfg.icon;
  const analysis = conv.analysis || {};
  const ts = new Date(conv.timestamp);
  const timeStr = ts.toLocaleString('nl-NL', { dateStyle: 'short', timeStyle: 'short' });
  const hasSnap = (analysis.snap_suggestions || []).length > 0;
  const hasMatches = (analysis.knowledge_matches || []).length > 0;
  const trigger = analysis.trigger_type;

  return (
    <div data-testid={`log-${conv.id}`}
      className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
      <button onClick={onToggle} className="w-full flex items-start gap-3 p-3 text-left">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${cfg.color}20` }}>
          <Icon className="w-3.5 h-3.5" style={{ color: cfg.color }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-[10px] font-medium" style={{ color: cfg.color }}>#{conv.metadata?.gesprek_nummer}</span>
            <span className="text-[10px] text-slate-500">{timeStr}</span>
            {trigger && <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">{trigger}</span>}
            {hasSnap && <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400">snap</span>}
            {hasMatches && <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">match</span>}
          </div>
          <p className="text-sm text-white truncate">{conv.user_message}</p>
          <p className="text-xs text-slate-400 truncate mt-0.5">→ {conv.spark_response}</p>
        </div>
        {expanded ? <ChevronDown className="w-4 h-4 text-slate-500 flex-shrink-0" /> : <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0" />}
      </button>
      {expanded && (
        <div className="border-t border-slate-800 p-4 bg-slate-950/30 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <p className="text-[10px] text-slate-500 uppercase mb-1">{conv.user_naam}</p>
              <p className="text-sm text-white bg-slate-800/50 p-2 rounded-lg whitespace-pre-wrap">{conv.user_message}</p>
            </div>
            <div>
              <p className="text-[10px] text-slate-500 uppercase mb-1">Spark</p>
              <p className="text-sm text-white bg-amber-500/10 p-2 rounded-lg whitespace-pre-wrap">{conv.spark_response}</p>
            </div>
          </div>
          {/* Analysis */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
            {analysis.sentiment && <AnalysisCell label="Sentiment" value={analysis.sentiment} />}
            {analysis.emotion?.emotion && <AnalysisCell label="Emotie" value={analysis.emotion.emotion} />}
            {trigger && <AnalysisCell label="Trigger" value={trigger} color="#f59e0b" />}
            <AnalysisCell label="Woorden" value={analysis.word_count} />
            {analysis.response_type && <AnalysisCell label="Type" value={analysis.response_type} />}
          </div>
          {hasMatches && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase mb-1 flex items-center gap-1"><BookOpen className="w-3 h-3" /> Knowledge matches</p>
              <div className="flex flex-wrap gap-1">
                {analysis.knowledge_matches.map((m, i) => (
                  <span key={i} className="text-[10px] px-2 py-0.5 bg-green-500/10 text-green-400 rounded">{m.begrip}</span>
                ))}
              </div>
            </div>
          )}
          {hasSnap && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase mb-1 flex items-center gap-1"><Zap className="w-3 h-3" /> Geleerde woorden</p>
              <div className="flex flex-wrap gap-1">
                {analysis.snap_suggestions.map((s, i) => (
                  <span key={i} className="text-[10px] px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded">{s}</span>
                ))}
              </div>
            </div>
          )}
          {analysis.bots_reacted && analysis.bots_reacted.length > 0 && (
            <div>
              <p className="text-[10px] text-slate-500 uppercase mb-1">Bots reageerden</p>
              <div className="flex flex-wrap gap-1">
                {analysis.bots_reacted.map((b, i) => <span key={i} className="text-[10px] px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded">{b}</span>)}
              </div>
            </div>
          )}
          <div className="flex justify-end pt-2 border-t border-slate-800/50">
            <button onClick={onDelete}
              className="flex items-center gap-1 px-2 py-1 text-[10px] text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
              <Trash2 className="w-3 h-3" /> Gesprek verwijderen
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function AnalysisCell({ label, value, color }) {
  return (
    <div className="bg-slate-800/30 rounded-lg px-2 py-1.5">
      <p className="text-[9px] text-slate-500 uppercase">{label}</p>
      <p className="text-xs font-medium" style={{ color: color || '#fff' }}>{value}</p>
    </div>
  );
}

export default ArchiefPage;
