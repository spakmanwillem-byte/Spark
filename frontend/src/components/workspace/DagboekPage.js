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

            {/* Entries */}
            {filtered.length === 0 ? (
              <div className="py-16 text-center"><BookHeart className="w-10 h-10 text-slate-700 mx-auto mb-3" /><p className="text-slate-400 text-sm">Geen entries gevonden</p></div>
            ) : (
              <div className="space-y-3">
                {filtered.map(entry => {
                  const mood = moods.find(m => m.id === entry.mood) || moods[2];
                  const MoodIcon = mood.icon;
                  return (
                    <div key={entry.id} data-testid={`dagboek-${entry.id}`} className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${mood.color}15` }}>
                          <MoodIcon className="w-4 h-4" style={{ color: mood.color }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-[10px] font-medium" style={{ color: mood.color }}>{mood.label}</span>
                            <span className="text-[10px] text-slate-600 flex items-center gap-1"><Clock className="w-2.5 h-2.5" />{new Date(entry.created_at).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                            <span className="text-[10px] text-slate-700">{entry.word_count}w</span>
                          </div>
                          <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">{entry.content}</p>
                        </div>
                        <button onClick={() => deleteEntry(entry.id)} className="p-1.5 hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded-lg transition-colors flex-shrink-0">
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default DagboekPage;
