import React, { useState } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  BookHeart, Plus, Search, Calendar, Smile, Frown, Meh, Heart,
  Sparkles, Zap, Coffee, Moon, Sun, CloudRain, Star, X, Save,
  ChevronDown, Tag, Clock
} from 'lucide-react';

const moods = [
  { id: 'blij', label: 'Blij', color: '#22c55e', icon: Smile },
  { id: 'enthousiast', label: 'Enthousiast', color: '#f59e0b', icon: Zap },
  { id: 'neutraal', label: 'Neutraal', color: '#3b82f6', icon: Meh },
  { id: 'gespannen', label: 'Gespannen', color: '#f97316', icon: Coffee },
  { id: 'verdrietig', label: 'Verdrietig', color: '#a855f7', icon: CloudRain },
  { id: 'boos', label: 'Boos', color: '#ef4444', icon: Frown },
];

const initialEntries = [
  { id: 'e0e00c39', content: 'Vandaag veel aan het programmeren geweest. met de programma\'s: GPT en Emergent.\nIK probeer minder te blowen wat moeizaam gaat.\nMijn financiële gebeuren is niet stabiel.', mood: 'blij', tags: [], created_at: '2026-03-13T21:18:52', word_count: 26 },
  { id: 'dd36dfdd', content: 'Weer een mijlpaal gehaald. #Spark', mood: 'blij', tags: [], created_at: '2026-03-13T21:16:17', word_count: 5 },
  { id: 'a6ca1014', content: 'Gesprek viel mee. maar nog geen duidelijkheid langer termijn.', mood: 'neutraal', tags: [], created_at: '2026-03-09T21:45:12', word_count: 9 },
  { id: '322b83c3', content: 'Morgen een belangrijk gesprek.', mood: 'gespannen', tags: [], created_at: '2026-03-08T15:15:31', word_count: 4 },
  { id: '6985c78f', content: 'Vandaag was een super dag! Veel gedaan en energie.', mood: 'enthousiast', tags: [], created_at: '2026-03-08T12:01:19', word_count: 9 },
  { id: '41447c36', content: 'Vandaag was een mooie dag!', mood: 'blij', tags: ['test'], created_at: '2026-03-08T11:35:57', word_count: 5 },
];

export function DagboekPage({ onNavigate }) {
  const [entries, setEntries] = useState(initialEntries);
  const [showNew, setShowNew] = useState(false);
  const [newContent, setNewContent] = useState('');
  const [newMood, setNewMood] = useState('neutraal');
  const [search, setSearch] = useState('');
  const [filterMood, setFilterMood] = useState('all');

  const filtered = entries.filter(e => {
    if (filterMood !== 'all' && e.mood !== filterMood) return false;
    if (search && !e.content.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const addEntry = () => {
    if (!newContent.trim()) return;
    const entry = {
      id: Date.now().toString(36),
      content: newContent,
      mood: newMood,
      tags: [],
      created_at: new Date().toISOString(),
      word_count: newContent.trim().split(/\s+/).length,
    };
    setEntries([entry, ...entries]);
    setNewContent('');
    setNewMood('neutraal');
    setShowNew(false);
  };

  const moodStats = moods.map(m => ({
    ...m,
    count: entries.filter(e => e.mood === m.id).length,
  }));

  return (
    <MainLayout activePage="dagboek" onNavigate={onNavigate}>
      <div data-testid="dagboek-page" className="p-4 md:p-6 space-y-5 max-w-4xl mx-auto">

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #a855f7)' }}>
              <BookHeart className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Dagboek</h1>
              <p className="text-xs text-slate-500">{entries.length} entries</p>
            </div>
          </div>
          <button data-testid="new-entry-btn" onClick={() => setShowNew(!showNew)} className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white" style={{ background: 'linear-gradient(135deg, #ec4899, #a855f7)' }}>
            <Plus className="w-4 h-4" /> Nieuwe Entry
          </button>
        </div>

        {/* Mood stats */}
        <div className="flex gap-2 overflow-x-auto pb-1">
          {moodStats.map(m => (
            <button key={m.id} onClick={() => setFilterMood(filterMood === m.id ? 'all' : m.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex-shrink-0 ${filterMood === m.id ? 'ring-1' : ''}`}
              style={{ background: `${m.color}15`, color: m.color, ringColor: m.color }}>
              <m.icon className="w-3.5 h-3.5" /> {m.label} ({m.count})
            </button>
          ))}
        </div>

        {/* New entry form */}
        {showNew && (
          <div className="p-4 bg-slate-900/60 border border-pink-500/20 rounded-xl space-y-3">
            <textarea data-testid="entry-content" value={newContent} onChange={e => setNewContent(e.target.value)} placeholder="Wat is er vandaag gebeurd..." rows={4}
              className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/40 resize-none" />
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Stemming:</span>
              {moods.map(m => (
                <button key={m.id} onClick={() => setNewMood(m.id)} title={m.label}
                  className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${newMood === m.id ? 'ring-2 scale-110' : 'opacity-40 hover:opacity-70'}`}
                  style={{ background: `${m.color}20`, ringColor: m.color }}>
                  <m.icon className="w-4 h-4" style={{ color: m.color }} />
                </button>
              ))}
              <button data-testid="save-entry-btn" onClick={addEntry} className="ml-auto px-4 py-2 rounded-lg text-sm font-medium text-white" style={{ background: '#ec4899' }}>
                <Save className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input data-testid="dagboek-search" type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Doorzoek dagboek..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/40" />
        </div>

        {/* Entries */}
        <div className="space-y-3">
          {filtered.map(entry => {
            const mood = moods.find(m => m.id === entry.mood) || moods[2];
            const MoodIcon = mood.icon;
            const date = new Date(entry.created_at);
            return (
              <div key={entry.id} data-testid={`entry-${entry.id}`} className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: `${mood.color}15` }}>
                    <MoodIcon className="w-4 h-4" style={{ color: mood.color }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ background: `${mood.color}15`, color: mood.color }}>{mood.label}</span>
                      <span className="text-[10px] text-slate-500 flex items-center gap-1"><Clock className="w-2.5 h-2.5" /> {date.toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' })} {date.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}</span>
                      <span className="text-[10px] text-slate-600">{entry.word_count} woorden</span>
                    </div>
                    <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-line">{entry.content}</p>
                    {entry.tags.length > 0 && (
                      <div className="flex gap-1 mt-2">{entry.tags.map((t, i) => <span key={i} className="text-[10px] px-2 py-0.5 bg-slate-800 text-slate-400 rounded-full">#{t}</span>)}</div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </MainLayout>
  );
}

export default DagboekPage;
