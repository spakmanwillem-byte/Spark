import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  StickyNote, Plus, Search, Trash2,
  Tag, Clock, ListTodo, FileText, Save,
  Circle, CheckCircle, HandHeart
} from 'lucide-react';
import { BijdragenPage } from './BijdragenPage';

const API = process.env.REACT_APP_BACKEND_URL;
const priorities = { high: { label: 'Hoog', color: '#ef4444' }, medium: { label: 'Normaal', color: '#f59e0b' }, low: { label: 'Laag', color: '#3b82f6' } };
const categories = ['Alles', 'Observatie', 'Technisch', 'Taak', 'Idee'];

export function NotitiesPage({ onNavigate }) {
  const [notes, setNotes] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('all');
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState('Alles');
  const [showNew, setShowNew] = useState(false);
  const [newItem, setNewItem] = useState({ type: 'note', titel: '', inhoud: '', categorie: 'Observatie', priority: 'medium' });

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/notes/all`).then(r => r.json()).catch(() => ({ notes: [] })),
      fetch(`${API}/api/notes/tasks`).then(r => r.json()).catch(() => ({ tasks: [] })),
    ]).then(([notesData, tasksData]) => {
      setNotes(notesData.notes || []);
      setTasks(tasksData.tasks || []);
      setLoading(false);
    });
  }, []);

  // Combine notes and tasks into unified list
  const items = [
    ...notes.map(n => ({ ...n, type: 'note', done: false })),
    ...tasks.map(t => ({ ...t, type: 'task', titel: t.task, inhoud: '', categorie: 'Taak', tags: [], datum: t.created_at, created_by: 'Willem', done: t.status === 'done' })),
  ].sort((a, b) => (b.datum || b.created_at || '').localeCompare(a.datum || a.created_at || ''));

  const filtered = items.filter(i => {
    if (viewMode === 'notes' && i.type !== 'note') return false;
    if (viewMode === 'tasks' && i.type !== 'task') return false;
    if (filterCat !== 'Alles' && i.categorie !== filterCat) return false;
    if (search && !(i.titel || '').toLowerCase().includes(search.toLowerCase()) && !(i.inhoud || '').toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const toggleDone = async (item) => {
    if (item.type !== 'task') return;
    const newStatus = item.done ? 'todo' : 'done';
    const res = await fetch(`${API}/api/notes/tasks/update/${item.id}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
    const data = await res.json();
    if (data.success) setTasks(tasks.map(t => t.id === item.id ? data.task : t));
  };

  const deleteItem = async (item) => {
    const url = item.type === 'note' ? `${API}/api/notes/delete/${item.id}` : `${API}/api/notes/tasks/delete/${item.id}`;
    const res = await fetch(url, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      if (item.type === 'note') setNotes(notes.filter(n => n.id !== item.id));
      else setTasks(tasks.filter(t => t.id !== item.id));
    }
  };

  const addItem = async () => {
    if (!newItem.titel.trim()) return;
    if (newItem.type === 'note') {
      const res = await fetch(`${API}/api/notes/create`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ titel: newItem.titel, inhoud: newItem.inhoud, categorie: newItem.categorie, priority: newItem.priority }),
      });
      const data = await res.json();
      if (data.success) setNotes([data.note, ...notes]);
    } else {
      const res = await fetch(`${API}/api/notes/tasks/create`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: newItem.titel, priority: newItem.priority }),
      });
      const data = await res.json();
      if (data.success) setTasks([...tasks, data.task]);
    }
    setNewItem({ type: 'note', titel: '', inhoud: '', categorie: 'Observatie', priority: 'medium' });
    setShowNew(false);
  };

  const tasksDone = tasks.filter(t => t.status === 'done').length;
  const notesTotal = notes.length;
  const tasksTotal = tasks.length;

  if (loading) return <MainLayout activePage="notities" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage="notities" onNavigate={onNavigate}>
      <div data-testid="notities-page" className="h-full flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #22c55e)' }}>
              <StickyNote className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Notities & Taken</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{notesTotal} notities, {tasksDone}/{tasksTotal} taken klaar</p>
            </div>
            <div className="ml-auto">
              <button data-testid="add-note-btn" onClick={() => setShowNew(!showNew)} className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-white" style={{ background: 'linear-gradient(135deg, #f59e0b, #22c55e)' }}>
                <Plus className="w-3.5 h-3.5" /> Nieuw
              </button>
            </div>
          </div>
          <div className="flex">
            {[
              { id: 'all', label: 'Alles', icon: FileText, count: items.length },
              { id: 'notes', label: 'Notities', icon: StickyNote, count: notesTotal },
              { id: 'tasks', label: 'Taken', icon: ListTodo, count: tasksTotal },
              { id: 'bijdragen', label: 'Bijdragen', icon: HandHeart, count: null },
            ].map(t => (
              <button key={t.id} data-testid={`view-${t.id}`} onClick={() => setViewMode(t.id)}
                className="relative flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors"
                style={{ color: viewMode === t.id ? '#f59e0b' : '#94a3b8' }}>
                <t.icon className="w-3.5 h-3.5" /> {t.label}{t.count !== null ? ` (${t.count})` : ''}
                {viewMode === t.id && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full bg-amber-500" />}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          {viewMode === 'bijdragen' ? (
            <div className="-m-4 md:-m-6 h-full">
              <BijdragenPage embedded={true} />
            </div>
          ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {showNew && (
              <div className="p-4 bg-slate-900/60 border border-amber-500/20 rounded-xl space-y-3">
                <div className="flex gap-2">
                  {['note', 'task'].map(t => (
                    <button key={t} onClick={() => setNewItem({ ...newItem, type: t })}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${newItem.type === t ? 'bg-amber-500 text-white' : 'bg-slate-800 text-slate-400'}`}>
                      {t === 'note' ? 'Notitie' : 'Taak'}
                    </button>
                  ))}
                </div>
                <input type="text" value={newItem.titel} onChange={e => setNewItem({ ...newItem, titel: e.target.value })} placeholder={newItem.type === 'note' ? 'Titel...' : 'Taak omschrijving...'}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none" />
                {newItem.type === 'note' && (
                  <textarea value={newItem.inhoud} onChange={e => setNewItem({ ...newItem, inhoud: e.target.value })} placeholder="Inhoud..." rows={3}
                    className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none resize-none" />
                )}
                <div className="flex items-center gap-3">
                  {newItem.type === 'note' && (
                    <select value={newItem.categorie} onChange={e => setNewItem({ ...newItem, categorie: e.target.value })}
                      className="px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-slate-300 focus:outline-none">
                      {categories.slice(1).map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  )}
                  <select value={newItem.priority} onChange={e => setNewItem({ ...newItem, priority: e.target.value })}
                    className="px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-slate-300 focus:outline-none">
                    {Object.entries(priorities).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                  </select>
                  <button data-testid="save-note-btn" onClick={addItem} className="ml-auto px-4 py-1.5 rounded-lg text-xs font-medium text-white bg-green-500">Opslaan</button>
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Zoeken..."
                  className="w-full pl-8 pr-3 py-2 bg-slate-900/60 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
              </div>
              <select value={filterCat} onChange={e => setFilterCat(e.target.value)}
                className="px-3 py-2 bg-slate-900/60 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none">
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {filtered.length === 0 ? (
              <div className="py-16 text-center"><StickyNote className="w-10 h-10 text-slate-700 mx-auto mb-3" /><p className="text-slate-400 text-sm">Geen items gevonden</p></div>
            ) : (
              <div className="space-y-2">
                {filtered.map(item => {
                  const pri = priorities[item.priority] || priorities.medium;
                  return (
                    <div key={item.id} data-testid={`item-${item.id}`} className={`p-3 bg-slate-900/50 border rounded-xl transition-all ${item.done ? 'border-slate-800/50 opacity-60' : 'border-slate-800 hover:border-slate-600'}`}>
                      <div className="flex items-start gap-3">
                        {item.type === 'task' ? (
                          <button onClick={() => toggleDone(item)} className="mt-0.5 flex-shrink-0">
                            {item.done ? <CheckCircle className="w-5 h-5 text-green-400" /> : <Circle className="w-5 h-5 text-slate-600 hover:text-amber-400" />}
                          </button>
                        ) : (
                          <div className="w-5 h-5 rounded flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: `${pri.color}15` }}>
                            <FileText className="w-3 h-3" style={{ color: pri.color }} />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h4 className={`text-sm font-medium ${item.done ? 'line-through text-slate-500' : 'text-white'}`}>{item.titel}</h4>
                            <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: `${pri.color}15`, color: pri.color }}>{pri.label}</span>
                            {item.categorie && <span className="text-[10px] text-slate-600">{item.categorie}</span>}
                          </div>
                          {item.inhoud && <p className="text-xs text-slate-400 mt-1 line-clamp-2">{item.inhoud}</p>}
                          <div className="flex items-center gap-3 mt-2">
                            <span className="text-[10px] text-slate-600 flex items-center gap-1"><Clock className="w-2.5 h-2.5" /> {new Date(item.datum || item.created_at).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' })}</span>
                            {item.created_by && <span className="text-[10px] text-slate-600">{item.created_by}</span>}
                            {(item.tags || []).slice(0, 2).map((t, i) => <span key={i} className="text-[10px] text-slate-600">#{t}</span>)}
                          </div>
                        </div>
                        <button onClick={() => deleteItem(item)} className="p-1.5 hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded-lg transition-colors flex-shrink-0">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}

export default NotitiesPage;
