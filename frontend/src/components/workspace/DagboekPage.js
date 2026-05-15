import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  BookHeart, Plus, Search, Smile, Frown, Meh,
  Zap, Coffee, CloudRain, X, Clock
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

const moods = [
  { id: 'blij', label: 'Blij', color: '#22c55e', icon: Smile },
  { id: 'enthousiast', label: 'Enthousiast', color: '#f59e0b', icon: Zap },
  { id: 'neutraal', label: 'Neutraal', color: '#3b82f6', icon: Meh },
  { id: 'gespannen', label: 'Gespannen', color: '#f97316', icon: Coffee },
  { id: 'verdrietig', label: 'Verdrietig', color: '#a855f7', icon: CloudRain },
  { id: 'boos', label: 'Boos', color: '#ef4444', icon: Frown },
];

export function DagboekPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [newContent, setNewContent] = useState('');
  const [newMood, setNewMood] = useState('neutraal');
  const [search, setSearch] = useState('');
  const [filterMood, setFilterMood] = useState('all');

  useEffect(() => {
    fetch(`${API}/api/dagboek/entries/${userId}`)
      .then(r => r.json())
      .then(d => { setEntries(d.entries || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [userId]);

  const filtered = entries.filter(e => {
    if (filterMood !== 'all' && e.mood !== filterMood) return false;
    if (search && !(e.content || '').toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const addEntry = async () => {
    if (!newContent.trim()) return;
    const res = await fetch(`${API}/api/dagboek/entries/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newContent, mood: newMood }),
    });
    const data = await res.json();
    if (data.success) {
      setEntries([data.entry, ...entries]);
      setNewContent('');
      setNewMood('neutraal');
      setShowNew(false);
    }
  };

  const deleteEntry = async (id) => {
    const res = await fetch(`${API}/api/dagboek/entries/${userId}/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) setEntries(entries.filter(e => e.id !== id));
  };

  const moodStats = moods.map(m => ({ ...m, count: entries.filter(e => e.mood === m.id).length }));

  if (loading) return <MainLayout activePage="dagboek" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-pink-500/30 border-t-pink-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage="dagboek" onNavigate={onNavigate}>
      <div data-testid="dagboek-page" className="h-full flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #a855f7)' }}>
              <BookHeart className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Dagboek</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{entries.length} entries</p>
            </div>
            <button data-testid="add-dagboek-btn" onClick={() => setShowNew(!showNew)} className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white" style={{ background: 'linear-gradient(135deg, #ec4899, #a855f7)' }}>
              <Plus className="w-3.5 h-3.5" /> Nieuw
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            {/* New entry */}
            {showNew && (
              <div className="p-4 bg-slate-900/60 border border-pink-500/20 rounded-xl space-y-3">
                <textarea data-testid="dagboek-content" value={newContent} onChange={e => setNewContent(e.target.value)} placeholder="Hoe was je dag?" rows={4}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none resize-none" />
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] text-slate-500">Stemming:</span>
                  {moods.map(m => (
                    <button key={m.id} onClick={() => setNewMood(m.id)}
                      className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium transition-all ${newMood === m.id ? 'border' : 'bg-slate-800/50 text-slate-400 border border-transparent'}`}
                      style={newMood === m.id ? { background: `${m.color}15`, color: m.color, borderColor: `${m.color}40` } : {}}>
                      <m.icon className="w-3 h-3" /> {m.label}
                    </button>
                  ))}
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-slate-600">{newContent.trim().split(/\s+/).filter(Boolean).length} woorden</span>
                  <button data-testid="save-dagboek-btn" onClick={addEntry} className="px-4 py-1.5 rounded-lg text-xs font-medium text-white bg-pink-500">Opslaan</button>
                </div>
              </div>
            )}

            {/* Mood stats */}
            <div className="flex gap-2 overflow-x-auto pb-1">
              <button onClick={() => setFilterMood('all')}
                className={`px-3 py-1.5 rounded-lg text-[10px] font-medium whitespace-nowrap transition-all flex-shrink-0 ${filterMood === 'all' ? 'bg-slate-700 text-white' : 'bg-slate-800/50 text-slate-500'}`}>
                Alles ({entries.length})
              </button>
              {moodStats.filter(m => m.count > 0).map(m => (
                <button key={m.id} onClick={() => setFilterMood(m.id)}
                  className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-medium whitespace-nowrap transition-all flex-shrink-0 ${filterMood === m.id ? 'border' : 'bg-slate-800/50 text-slate-500 border border-transparent'}`}
                  style={filterMood === m.id ? { background: `${m.color}15`, color: m.color, borderColor: `${m.color}40` } : {}}>
                  <m.icon className="w-3 h-3" /> {m.label} ({m.count})
                </button>
              ))}
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Zoek in dagboek..."
                className="w-full pl-8 pr-3 py-2 bg-slate-900/60 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
            </div>

            {/* Entries — Tree-view (jaar → maand → dag), zelfde structuur als Archief (v4_dagboek_tree_001) */}
            {filtered.length === 0 ? (
              <div className="py-16 text-center"><BookHeart className="w-10 h-10 text-slate-700 mx-auto mb-3" /><p className="text-slate-400 text-sm">Geen entries gevonden</p></div>
            ) : (
              <DagboekTreeView entries={filtered} moods={moods} onDelete={deleteEntry} />
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default DagboekPage;

/* ================================================================ */
/* DAGBOEK TREE-VIEW (v4_dagboek_tree_001) — jaar → maand → dag      */
/* Zelfde principe als ArchiefPage ConversationsView                  */
/* ================================================================ */
const MONTHS_NL = ['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december'];

function DagboekTreeView({ entries, moods, onDelete }) {
  // Groepeer entries op jaar → maand → dag
  const tree = React.useMemo(() => {
    const t = {};
    for (const e of entries) {
      const d = new Date(e.created_at);
      const y = d.getFullYear();
      const m = d.getMonth();
      const dd = d.getDate();
      if (!t[y]) t[y] = {};
      if (!t[y][m]) t[y][m] = {};
      if (!t[y][m][dd]) t[y][m][dd] = [];
      t[y][m][dd].push(e);
    }
    return t;
  }, [entries]);

  const availableYears = React.useMemo(() => {
    const set = new Set(Object.keys(tree).map(Number));
    set.add(new Date().getFullYear());
    return [...set].sort((a, b) => b - a);
  }, [tree]);

  const [activeYear, setActiveYear] = React.useState(availableYears[0] || new Date().getFullYear());
  const [openMonths, setOpenMonths] = React.useState({});
  const [openDays, setOpenDays] = React.useState({});

  React.useEffect(() => {
    if (!availableYears.includes(activeYear) && availableYears.length > 0) setActiveYear(availableYears[0]);
  }, [availableYears, activeYear]);

  const toggleMonth = (y, m) => setOpenMonths(s => ({ ...s, [`${y}-${m}`]: !s[`${y}-${m}`] }));
  const toggleDay = (y, m, d) => setOpenDays(s => ({ ...s, [`${y}-${m}-${d}`]: !s[`${y}-${m}-${d}`] }));

  const yearData = tree[activeYear] || {};
  const monthsInYear = Object.keys(yearData).map(Number).sort((a, b) => b - a);

  return (
    <div className="space-y-3">
      {/* Jaar tabs */}
      <div className="flex flex-wrap gap-1 border-b border-slate-800 pb-1">
        {availableYears.map(y => {
          const yearTotal = tree[y]
            ? Object.values(tree[y]).reduce((s, mObj) => s + Object.values(mObj).reduce((sd, arr) => sd + arr.length, 0), 0)
            : 0;
          const isActive = y === activeYear;
          return (
            <button key={y} data-testid={`dagboek-year-${y}`} onClick={() => setActiveYear(y)}
              className={`text-xs px-3 py-1.5 rounded-t-md transition-colors ${isActive ? 'text-pink-300 bg-pink-500/10 border-t border-x border-pink-500/30' : 'text-slate-500 hover:text-slate-300'}`}>
              {y} {yearTotal > 0 && <span className="ml-1 text-[10px] text-slate-500">({yearTotal})</span>}
            </button>
          );
        })}
      </div>

      {/* Maand → dag tree */}
      {monthsInYear.length === 0 ? (
        <p className="text-xs text-slate-500 text-center py-8">Geen entries in {activeYear}.</p>
      ) : (
        <div className="space-y-2">
          {monthsInYear.map(m => {
            const monthData = yearData[m];
            const monthTotal = Object.values(monthData).reduce((s, arr) => s + arr.length, 0);
            const isMonthOpen = openMonths[`${activeYear}-${m}`];
            const days = Object.keys(monthData).map(Number).sort((a, b) => b - a);
            return (
              <div key={m} className="bg-slate-900/30 border border-slate-800 rounded-lg overflow-hidden">
                <button onClick={() => toggleMonth(activeYear, m)}
                  className="w-full px-3 py-2 flex items-center justify-between hover:bg-slate-800/40 transition-colors">
                  <span className="text-sm text-white font-medium capitalize">{MONTHS_NL[m]}</span>
                  <span className="text-[10px] text-slate-500">{monthTotal} entries · {isMonthOpen ? '−' : '+'}</span>
                </button>
                {isMonthOpen && (
                  <div className="border-t border-slate-800/60 px-2 py-2 space-y-1">
                    {days.map(dd => {
                      const dayEntries = monthData[dd];
                      const isDayOpen = openDays[`${activeYear}-${m}-${dd}`];
                      return (
                        <div key={dd} className="bg-slate-950/40 rounded">
                          <button onClick={() => toggleDay(activeYear, m, dd)}
                            className="w-full px-2.5 py-1.5 flex items-center justify-between hover:bg-slate-800/50 rounded transition-colors">
                            <span className="text-xs text-slate-300">
                              <strong>{dd}</strong> {MONTHS_NL[m].slice(0, 3)} {activeYear}
                            </span>
                            <span className="text-[10px] text-slate-500">{dayEntries.length} · {isDayOpen ? '−' : '+'}</span>
                          </button>
                          {isDayOpen && (
                            <div className="px-2 py-2 space-y-2 border-t border-slate-900/80">
                              {dayEntries.map(entry => {
                                const mood = moods.find(m2 => m2.id === entry.mood) || moods[2];
                                const MoodIcon = mood.icon;
                                return (
                                  <div key={entry.id} data-testid={`dagboek-${entry.id}`} className="p-3 bg-slate-900/50 border border-slate-800 rounded-lg">
                                    <div className="flex items-start gap-3">
                                      <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${mood.color}15` }}>
                                        <MoodIcon className="w-3.5 h-3.5" style={{ color: mood.color }} />
                                      </div>
                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                          <span className="text-[10px] font-medium" style={{ color: mood.color }}>{mood.label}</span>
                                          <span className="text-[10px] text-slate-600 flex items-center gap-1">
                                            <Clock className="w-2.5 h-2.5" />
                                            {new Date(entry.created_at).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}
                                          </span>
                                          <span className="text-[10px] text-slate-700">{entry.word_count}w</span>
                                        </div>
                                        <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">{entry.content}</p>
                                      </div>
                                      <button onClick={() => onDelete(entry.id)} className="p-1.5 hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded-lg transition-colors flex-shrink-0">
                                        <X className="w-3.5 h-3.5" />
                                      </button>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
