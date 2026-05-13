import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Zap, Search, ChevronDown, ChevronRight, X, Tag, Plus,
  MessageSquare, Calendar as CalIcon, Heart, Shield, Settings, Sparkles
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const typeConfig = {
  conversation: { label: 'Conversatie', color: '#f59e0b', icon: MessageSquare },
  calendar: { label: 'Kalender', color: '#3b82f6', icon: CalIcon },
  emotion: { label: 'Emotie', color: '#ec4899', icon: Heart },
  vocab: { label: 'Spark Vocab', color: '#a855f7', icon: Sparkles },
  admin: { label: 'Admin', color: '#ef4444', icon: Shield },
  system: { label: 'Systeem', color: '#64748b', icon: Settings },
};

export function TriggersPage({ onNavigate }) {
  const [groups, setGroups] = useState({});
  const [stats, setStats] = useState({ total_groups: 0, total_triggers: 0 });
  const [loading, setLoading] = useState(true);
  const [expandedList, setExpandedList] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [addInput, setAddInput] = useState('');

  const reloadAll = async () => {
    const d = await fetch(`${API}/api/triggers/all`).then(r => r.json()).catch(() => ({}));
    setGroups(d.trigger_groups || {});
    setStats(d.stats || {});
  };

  useEffect(() => {
    reloadAll().finally(() => setLoading(false));
  }, []);

  const addVocabWord = async (vocabPath, word) => {
    if (!word.trim()) return;
    const [group, key] = vocabPath.split('/');
    await fetch(`${API}/api/spark/vocab/${group}/${encodeURIComponent(key)}/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ word: word.trim() }),
    });
    setAddInput('');
    await reloadAll();
  };

  const deleteVocabWord = async (vocabPath, word) => {
    const [group, key] = vocabPath.split('/');
    await fetch(`${API}/api/spark/vocab/${group}/${encodeURIComponent(key)}/${encodeURIComponent(word)}`, {
      method: 'DELETE',
    });
    await reloadAll();
  };

  const filteredEntries = Object.entries(groups).filter(([key, group]) => {
    if (filterType !== 'all' && group.type !== filterType) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return group.label.toLowerCase().includes(q) || group.triggers.some(t => t.toLowerCase().includes(q));
    }
    return true;
  });

  const typeCounts = {};
  Object.values(groups).forEach(g => { typeCounts[g.type] = (typeCounts[g.type] || 0) + g.triggers.length; });

  if (loading) return <MainLayout activePage="triggers" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage="triggers" onNavigate={onNavigate}>
      <div data-testid="triggers-page" className="h-full flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Triggers</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{stats.total_triggers} triggers in {stats.total_groups} groepen</p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            {/* Type filter chips */}
            <div className="flex flex-wrap gap-2">
              <button onClick={() => setFilterType('all')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filterType === 'all' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-slate-800/50 text-slate-400 border border-transparent hover:border-slate-700'}`}>
                Alles ({stats.total_triggers})
              </button>
              {Object.entries(typeConfig).map(([type, cfg]) => (
                <button key={type} onClick={() => setFilterType(type)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${filterType === type ? `border` : 'bg-slate-800/50 text-slate-400 border border-transparent hover:border-slate-700'}`}
                  style={filterType === type ? { background: `${cfg.color}15`, color: cfg.color, borderColor: `${cfg.color}40` } : {}}>
                  <cfg.icon className="w-3 h-3" />
                  {cfg.label} ({typeCounts[type] || 0})
                </button>
              ))}
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Zoek triggers..."
                className="w-full pl-9 pr-3 py-2 bg-slate-900/60 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
            </div>

            {/* Trigger groups */}
            <div className="space-y-2">
              {filteredEntries.map(([key, group]) => {
                const isExpanded = expandedList === key;
                const cfg = typeConfig[group.type] || typeConfig.system;
                return (
                  <div key={key} data-testid={`trigger-group-${key}`} className={`border rounded-xl overflow-hidden transition-all ${isExpanded ? 'border-slate-700' : 'border-slate-800'} bg-slate-900/50`}>
                    <button onClick={() => { setExpandedList(isExpanded ? null : key); setAddInput(''); }}
                      className="w-full flex items-center justify-between p-3 hover:bg-slate-800/20 transition-colors">
                      <div className="flex items-center gap-2.5">
                        {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: cfg.color }} />
                        <div className="text-left">
                          <h3 className="text-sm text-white font-medium">{group.label}</h3>
                          <p className="text-[10px] text-slate-500">{cfg.label}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {group.emoji && <span className="text-sm">{group.emoji}</span>}
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">{group.triggers.length} triggers</span>
                      </div>
                    </button>
                    {isExpanded && (
                      <div className="px-3 pb-3 pt-1">
                        {/* Trigger words */}
                        <div className="flex flex-wrap gap-1.5 mb-3">
                          {group.triggers.map((trigger, idx) => {
                            const score = group.trigger_scores?.[trigger];
                            return (
                              <span key={idx} data-testid={`trigger-chip-${trigger}`} className="text-[11px] px-2 py-1 rounded-lg border flex items-center gap-1"
                                style={{ background: `${cfg.color}08`, color: cfg.color, borderColor: `${cfg.color}25` }}>
                                {trigger}
                                {score !== undefined && <span className="text-[9px] opacity-60">({score})</span>}
                                {group.editable && (
                                  <button
                                    data-testid={`del-vocab-${trigger}`}
                                    onClick={() => deleteVocabWord(group.vocab_path, trigger)}
                                    className="ml-1 hover:opacity-80"
                                    title="Verwijder">
                                    <X className="w-3 h-3" />
                                  </button>
                                )}
                              </span>
                            );
                          })}
                          {group.editable && group.triggers.length === 0 && (
                            <span className="text-[11px] text-slate-500 italic">Nog leeg — voeg woorden toe ↓</span>
                          )}
                        </div>
                        {/* Add input voor editable groepen (vocab) */}
                        {group.editable && (
                          <div className="flex gap-2 mb-2">
                            <input
                              data-testid={`add-vocab-input-${key}`}
                              type="text"
                              value={expandedList === key ? addInput : ''}
                              onChange={e => setAddInput(e.target.value)}
                              onKeyDown={e => {
                                if (e.key === 'Enter') { e.preventDefault(); addVocabWord(group.vocab_path, addInput); }
                              }}
                              placeholder="Nieuw woord/zin toevoegen..."
                              className="flex-1 bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-1.5 text-[11px] text-white placeholder-slate-500 focus:outline-none focus:border-violet-500" />
                            <button
                              data-testid={`add-vocab-btn-${key}`}
                              onClick={() => addVocabWord(group.vocab_path, addInput)}
                              className="px-2 py-1.5 rounded-lg bg-violet-500/15 hover:bg-violet-500/25 text-violet-300 text-[11px] flex items-center gap-1">
                              <Plus className="w-3 h-3" /> Toevoegen
                            </button>
                          </div>
                        )}
                        {/* Responses if any */}
                        {group.responses && group.responses.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-slate-800/50">
                            <p className="text-[10px] text-slate-500 mb-1.5">Antwoorden:</p>
                            <div className="space-y-1">
                              {group.responses.map((r, i) => (
                                <p key={i} className="text-[11px] text-slate-400 pl-3 border-l-2 border-slate-700">{r}</p>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {filteredEntries.length === 0 && (
              <div className="py-12 text-center">
                <Zap className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                <p className="text-slate-400 text-sm">Geen triggers gevonden{searchQuery ? ` voor "${searchQuery}"` : ''}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default TriggersPage;
