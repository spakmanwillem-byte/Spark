import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  StickyNote, Plus, Search, Trash2,
  Tag, Clock, ListTodo, FileText, Save,
  Circle, CheckCircle, Bug, AlertTriangle, Rocket, Pencil, X
} from 'lucide-react';
import { DeployAnchorPanel } from './DeployAnchorPanel';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;
const priorities = { high: { label: 'Hoog', color: '#ef4444' }, medium: { label: 'Normaal', color: '#f59e0b' }, low: { label: 'Laag', color: '#3b82f6' } };
const categories = ['Alles', 'Observatie', 'Technisch', 'Taak', 'Idee'];
const BUG_STATUSES = {
  nieuw: { label: 'Nieuw', color: '#ef4444' },
  in_behandeling: { label: 'In behandeling', color: '#f59e0b' },
  opgelost: { label: 'Opgelost', color: '#22c55e' },
  afgewezen: { label: 'Afgewezen', color: '#64748b' },
};

export function NotitiesPage({ onNavigate }) {
  const { user } = useAuth();
  const isAdminViewer = (user?.gradatie || 7) <= 2;
  const [notes, setNotes] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('all');
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState('Alles');
  const [showNew, setShowNew] = useState(false);
  const [newItem, setNewItem] = useState({ type: 'note', titel: '', inhoud: '', categorie: 'Observatie', priority: 'medium' });
  const [bugs, setBugs] = useState([]);
  const [showBugForm, setShowBugForm] = useState(false);
  const [newBug, setNewBug] = useState({ description: '', when: '', page: '' });
  const [bugSubmitMsg, setBugSubmitMsg] = useState(null);

  useEffect(() => {
    if (!user?.id) return;
    Promise.all([
      fetch(`${API}/api/notes/all?user_id=${user.id}`).then(r => r.json()).catch(() => ({ notes: [] })),
      fetch(`${API}/api/notes/tasks?user_id=${user.id}`).then(r => r.json()).catch(() => ({ tasks: [] })),
    ]).then(([notesData, tasksData]) => {
      setNotes(notesData.notes || []);
      setTasks(tasksData.tasks || []);
      setLoading(false);
    });
  }, [user?.id]);

  // Load bugs when Bugs tab opens (alle gradaties zien eigen meldingen; admins zien alles)
  useEffect(() => {
    if (viewMode !== 'bugs' || !user?.id) return;
    const url = isAdminViewer
      ? `${API}/api/bugs/list?viewer_id=${user.id}`
      : `${API}/api/bugs/mine?user_id=${user.id}`;
    fetch(url)
      .then(r => r.ok ? r.json() : { bugs: [] })
      .then(d => setBugs(d.bugs || []))
      .catch(() => setBugs([]));
  }, [viewMode, isAdminViewer, user?.id]);

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
    const res = await fetch(`${API}/api/notes/tasks/update/${item.id}?user_id=${user.id}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
    const data = await res.json();
    if (data.success) setTasks(tasks.map(t => t.id === item.id ? data.task : t));
  };

  const deleteItem = async (item) => {
    const url = item.type === 'note'
      ? `${API}/api/notes/delete/${item.id}?user_id=${user.id}`
      : `${API}/api/notes/tasks/delete/${item.id}?user_id=${user.id}`;
    const res = await fetch(url, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      if (item.type === 'note') setNotes(notes.filter(n => n.id !== item.id));
      else setTasks(tasks.filter(t => t.id !== item.id));
    }
  };

  // v6_note_edit_001 — Edit notitie/taak titel + inhoud
  const updateItem = async (item, updates) => {
    if (item.type === 'note') {
      const res = await fetch(`${API}/api/notes/update/${item.id}?user_id=${user.id}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      const data = await res.json();
      if (data.success) {
        setNotes(notes.map(n => n.id === item.id ? data.note : n));
        return true;
      }
      return false;
    } else {
      // Voor taken hernoemt alleen het 'task' veld
      const payload = updates.titel !== undefined ? { task: updates.titel } : updates;
      const res = await fetch(`${API}/api/notes/tasks/update/${item.id}?user_id=${user.id}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (data.success) {
        setTasks(tasks.map(t => t.id === item.id ? data.task : t));
        return true;
      }
      return false;
    }
  };

  const addItem = async () => {
    if (!newItem.titel.trim()) return;
    if (newItem.type === 'note') {
      const res = await fetch(`${API}/api/notes/create`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ titel: newItem.titel, inhoud: newItem.inhoud, categorie: newItem.categorie, priority: newItem.priority, user_id: user.id }),
      });
      const data = await res.json();
      if (data.success) setNotes([data.note, ...notes]);
    } else {
      const res = await fetch(`${API}/api/notes/tasks/create`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: newItem.titel, priority: newItem.priority, user_id: user.id }),
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

  const submitBug = async () => {
    if (!newBug.description.trim()) {
      setBugSubmitMsg({ type: 'error', text: 'Omschrijving is verplicht.' });
      return;
    }
    try {
      const res = await fetch(`${API}/api/bugs/create`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: newBug.description,
          when: newBug.when || null,
          page: newBug.page || null,
          created_by_id: user?.id || null,
          created_by_naam: user?.naam || null,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setBugSubmitMsg({ type: 'ok', text: 'Bug verzonden! Je krijgt een bevestiging in je privé-chat met Spark AI.' });
        setNewBug({ description: '', when: '', page: '' });
        if (isAdminViewer) setBugs([data.bug, ...bugs]);
        setTimeout(() => { setShowBugForm(false); setBugSubmitMsg(null); }, 2200);
      } else {
        setBugSubmitMsg({ type: 'error', text: 'Verzenden mislukt.' });
      }
    } catch {
      setBugSubmitMsg({ type: 'error', text: 'Netwerkfout. Probeer opnieuw.' });
    }
  };

  const updateBugStatus = async (bug, status) => {
    if (!isAdminViewer || !user?.id) return;
    const res = await fetch(`${API}/api/bugs/${bug.id}/status`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, viewer_id: user.id }),
    });
    const data = await res.json();
    if (data.success) setBugs(bugs.map(b => b.id === bug.id ? data.bug : b));
  };

  const deleteBug = async (bug) => {
    if (!isAdminViewer || !user?.id) return;
    if (!window.confirm('Bug verwijderen?')) return;
    const res = await fetch(`${API}/api/bugs/${bug.id}?viewer_id=${user.id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) setBugs(bugs.filter(b => b.id !== bug.id));
  };

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
            <div className="ml-auto flex items-center gap-2">
              <button data-testid="report-bug-btn" onClick={() => { setShowBugForm(true); setBugSubmitMsg(null); }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-red-300 border border-red-500/30 bg-red-500/5 hover:bg-red-500/10 transition-colors">
                <Bug className="w-3.5 h-3.5" /> Bug melden
              </button>
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
              { id: 'bugs', label: 'Bugs', icon: Bug, count: bugs.length || null },
              ...(isAdminViewer ? [{ id: 'deploy', label: 'Deploy', icon: Rocket, count: null }] : []),
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
          {/* Bug-melder modal */}
          {showBugForm && (
            <div data-testid="bug-form-modal" className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setShowBugForm(false)}>
              <div className="w-full max-w-md bg-slate-900 border border-red-500/30 rounded-2xl p-5 space-y-3" onClick={e => e.stopPropagation()}>
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-lg bg-red-500/15 flex items-center justify-center">
                    <Bug className="w-4 h-4 text-red-400" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Bug melden</h3>
                    <p className="text-[10px] text-slate-500">We bekijken het zo snel mogelijk.</p>
                  </div>
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase tracking-wider">Omschrijving *</label>
                  <textarea data-testid="bug-description" value={newBug.description} onChange={e => setNewBug({ ...newBug, description: e.target.value })}
                    placeholder="Wat ging er mis? Wat verwachtte je en wat zag je?" rows={4}
                    className="mt-1 w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-red-500/40 resize-none" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase tracking-wider">Wanneer gebeurde het?</label>
                  <input data-testid="bug-when" type="text" value={newBug.when} onChange={e => setNewBug({ ...newBug, when: e.target.value })}
                    placeholder='bv. "vandaag rond 14u" of "16-05 11:30"'
                    className="mt-1 w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-red-500/40" />
                  <p className="text-[10px] text-slate-600 mt-1">Hoe nauwkeuriger, hoe makkelijker we het in de logs vinden.</p>
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase tracking-wider">Waar in de app? (optioneel)</label>
                  <input data-testid="bug-page" type="text" value={newBug.page} onChange={e => setNewBug({ ...newBug, page: e.target.value })}
                    placeholder='bv. "Dashboard" of "Snelhandel"'
                    className="mt-1 w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-red-500/40" />
                </div>
                {bugSubmitMsg && (
                  <div className={`text-xs p-2 rounded-lg ${bugSubmitMsg.type === 'ok' ? 'bg-green-500/10 text-green-300 border border-green-500/30' : 'bg-red-500/10 text-red-300 border border-red-500/30'}`}>
                    {bugSubmitMsg.text}
                  </div>
                )}
                <div className="flex justify-end gap-2 pt-1">
                  <button onClick={() => setShowBugForm(false)} className="px-3 py-1.5 text-xs text-slate-400 hover:text-white">Annuleer</button>
                  <button data-testid="bug-submit" onClick={submitBug} className="px-4 py-1.5 rounded-lg text-xs font-medium text-white bg-red-500 hover:bg-red-600">Verzenden</button>
                </div>
              </div>
            </div>
          )}

          {viewMode === 'deploy' && isAdminViewer ? (
            <DeployAnchorPanel viewerId={user.id} />
          ) : viewMode === 'bugs' && isAdminViewer ? (
            <div className="max-w-3xl mx-auto space-y-2">
              {/* v6_bug_bulk_close_001 — Bulk-close knop */}
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
                <p className="text-xs text-slate-400">
                  {bugs.length} totaal · {bugs.filter(b => b.status === 'nieuw').length} nieuw · {bugs.filter(b => b.status === 'opgelost').length} opgelost
                </p>
                <button
                  data-testid="bugs-bulk-close-resolved"
                  onClick={async () => {
                    const resolved = bugs.filter(b => b.status === 'opgelost');
                    if (!resolved.length) { alert('Geen opgeloste bugs om op te schonen.'); return; }
                    if (!window.confirm(`${resolved.length} opgeloste bugs definitief sluiten? (status → closed)`)) return;
                    for (const b of resolved) {
                      await fetch(`${API}/api/bugs/${b.id}/status`, {
                        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ viewer_id: user.id, status: 'closed' }),
                      });
                    }
                    fetch(`${API}/api/bugs/list?viewer_id=${user.id}`).then(r => r.json()).then(d => setBugs(d.bugs || []));
                  }}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700">
                  🧹 Bulk-close opgelost
                </button>
              </div>
              {bugs.length === 0 ? (
                <div className="py-16 text-center"><Bug className="w-10 h-10 text-slate-700 mx-auto mb-3" /><p className="text-slate-400 text-sm">Nog geen bugmeldingen.</p></div>
              ) : bugs.map(b => {
                const st = BUG_STATUSES[b.status] || BUG_STATUSES.nieuw;
                return (
                  <div key={b.id} data-testid={`bug-${b.id}`} className="p-3 bg-slate-900/50 border border-slate-800 rounded-xl">
                    <div className="flex items-start gap-3">
                      <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: `${st.color}15` }}>
                        <AlertTriangle className="w-3.5 h-3.5" style={{ color: st.color }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[10px] px-1.5 py-0.5 rounded font-medium" style={{ background: `${st.color}20`, color: st.color }}>{st.label}</span>
                          <span className="text-[10px] text-slate-500">{b.created_by_naam || 'Anoniem'}</span>
                          {b.page && <span className="text-[10px] text-slate-600">· {b.page}</span>}
                          <span className="text-[10px] text-slate-600 ml-auto flex items-center gap-1">
                            <Clock className="w-2.5 h-2.5" /> {new Date(b.created_at).toLocaleString('nl-NL', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <p className="text-sm text-white mt-1 whitespace-pre-wrap">{b.description}</p>
                        {b.when && <p className="text-[11px] text-slate-400 mt-1">Wanneer: {b.when}</p>}
                        <div className="flex items-center gap-1 mt-2 flex-wrap">
                          {Object.entries(BUG_STATUSES).filter(([k]) => k !== b.status).map(([k, v]) => (
                            <button key={k} data-testid={`bug-status-${k}`} onClick={() => updateBugStatus(b, k)}
                              className="text-[10px] px-2 py-0.5 rounded border border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white transition-colors">
                              → {v.label}
                            </button>
                          ))}
                          <button onClick={() => deleteBug(b)} className="ml-auto p-1 hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded transition-colors">
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
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
              <NotitiesTreeView items={filtered} toggleDone={toggleDone} deleteItem={deleteItem} updateItem={updateItem} />
            )}
          </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}

export default NotitiesPage;

/* ================================================================ */
/* NOTITIES TREE-VIEW (v4_notities_tree_001) — jaar → maand → dag    */
/* Zelfde principe als Dagboek/Archief                                */
/* ================================================================ */
const MONTHS_NL = ['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december'];

function NotitiesTreeView({ items, toggleDone, deleteItem, updateItem }) {
  const tree = React.useMemo(() => {
    const t = {};
    for (const e of items) {
      const dStr = e.datum || e.created_at;
      if (!dStr) continue;
      const d = new Date(dStr);
      if (isNaN(d.getTime())) continue;
      const y = d.getFullYear();
      const m = d.getMonth();
      const dd = d.getDate();
      if (!t[y]) t[y] = {};
      if (!t[y][m]) t[y][m] = {};
      if (!t[y][m][dd]) t[y][m][dd] = [];
      t[y][m][dd].push(e);
    }
    return t;
  }, [items]);

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

  // Auto-open vandaag bij eerste render
  React.useEffect(() => {
    const now = new Date();
    const y = now.getFullYear();
    const m = now.getMonth();
    const dd = now.getDate();
    if (tree[y]?.[m]?.[dd]) {
      setOpenMonths(s => ({ ...s, [`${y}-${m}`]: true }));
      setOpenDays(s => ({ ...s, [`${y}-${m}-${dd}`]: true }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleMonth = (y, m) => setOpenMonths(s => ({ ...s, [`${y}-${m}`]: !s[`${y}-${m}`] }));
  const toggleDay = (y, m, d) => setOpenDays(s => ({ ...s, [`${y}-${m}-${d}`]: !s[`${y}-${m}-${d}`] }));

  const yearData = tree[activeYear] || {};
  const monthsInYear = Object.keys(yearData).map(Number).sort((a, b) => b - a);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1 border-b border-slate-800 pb-1">
        {availableYears.map(y => {
          const yearTotal = tree[y]
            ? Object.values(tree[y]).reduce((s, mObj) => s + Object.values(mObj).reduce((sd, arr) => sd + arr.length, 0), 0)
            : 0;
          const isActive = y === activeYear;
          return (
            <button key={y} data-testid={`notities-year-${y}`} onClick={() => setActiveYear(y)}
              className={`text-xs px-3 py-1.5 rounded-t-md transition-colors ${isActive ? 'text-amber-300 bg-amber-500/10 border-t border-x border-amber-500/30' : 'text-slate-500 hover:text-slate-300'}`}>
              {y} {yearTotal > 0 && <span className="ml-1 text-[10px] text-slate-500">({yearTotal})</span>}
            </button>
          );
        })}
      </div>

      {monthsInYear.length === 0 ? (
        <p className="text-xs text-slate-500 text-center py-8">Geen items in {activeYear}.</p>
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
                  data-testid={`notities-month-${activeYear}-${m}`}
                  className="w-full px-3 py-2 flex items-center justify-between hover:bg-slate-800/40 transition-colors">
                  <span className="text-sm text-white font-medium capitalize">{MONTHS_NL[m]}</span>
                  <span className="text-[10px] text-slate-500">{monthTotal} items · {isMonthOpen ? '−' : '+'}</span>
                </button>
                {isMonthOpen && (
                  <div className="border-t border-slate-800/60 px-2 py-2 space-y-1">
                    {days.map(dd => {
                      const dayItems = monthData[dd];
                      const isDayOpen = openDays[`${activeYear}-${m}-${dd}`];
                      return (
                        <div key={dd} className="bg-slate-950/40 rounded">
                          <button onClick={() => toggleDay(activeYear, m, dd)}
                            data-testid={`notities-day-${activeYear}-${m}-${dd}`}
                            className="w-full px-2.5 py-1.5 flex items-center justify-between hover:bg-slate-800/50 rounded transition-colors">
                            <span className="text-xs text-slate-300">
                              <strong>{dd}</strong> {MONTHS_NL[m].slice(0, 3)} {activeYear}
                            </span>
                            <span className="text-[10px] text-slate-500">{dayItems.length} · {isDayOpen ? '−' : '+'}</span>
                          </button>
                          {isDayOpen && (
                            <div className="px-2 py-2 space-y-2 border-t border-slate-900/80">
                              {dayItems.map(item => <NoteItemCard key={item.id} item={item} toggleDone={toggleDone} deleteItem={deleteItem} updateItem={updateItem} />)}
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

function NoteItemCard({ item, toggleDone, deleteItem, updateItem }) {
  const pri = priorities[item.priority] || priorities.medium;
  const [editing, setEditing] = React.useState(false);
  const [editTitel, setEditTitel] = React.useState(item.titel || '');
  const [editInhoud, setEditInhoud] = React.useState(item.inhoud || '');
  const [saving, setSaving] = React.useState(false);
  const isShopOrder = item.source === 'shop_order';
  const canEdit = typeof updateItem === 'function' && !isShopOrder;

  const startEdit = () => {
    setEditTitel(item.titel || '');
    setEditInhoud(item.inhoud || '');
    setEditing(true);
  };
  const cancelEdit = () => setEditing(false);
  const saveEdit = async () => {
    if (!editTitel.trim()) return;
    setSaving(true);
    const updates = item.type === 'note'
      ? { titel: editTitel.trim(), inhoud: editInhoud }
      : { titel: editTitel.trim() };
    const ok = await updateItem(item, updates);
    setSaving(false);
    if (ok) setEditing(false);
  };

  if (editing) {
    return (
      <div data-testid={`item-edit-${item.id}`} className="p-3 bg-slate-900/70 border border-amber-500/40 rounded-xl space-y-2">
        <div className="flex items-center gap-2">
          <Pencil className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-[10px] uppercase tracking-wider text-amber-400 font-medium">
            {item.type === 'note' ? 'Notitie bewerken' : 'Taak bewerken'}
          </span>
        </div>
        <input
          type="text"
          value={editTitel}
          onChange={e => setEditTitel(e.target.value)}
          placeholder="Titel..."
          data-testid={`edit-titel-${item.id}`}
          className="w-full px-3 py-2 bg-slate-800/60 border border-slate-700/60 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
          autoFocus
        />
        {item.type === 'note' && (
          <textarea
            value={editInhoud}
            onChange={e => setEditInhoud(e.target.value)}
            placeholder="Inhoud..."
            rows={4}
            data-testid={`edit-inhoud-${item.id}`}
            className="w-full px-3 py-2 bg-slate-800/60 border border-slate-700/60 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50 resize-none"
          />
        )}
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={cancelEdit}
            data-testid={`edit-cancel-${item.id}`}
            className="px-3 py-1.5 text-xs text-slate-400 hover:text-white flex items-center gap-1">
            <X className="w-3 h-3" /> Annuleer
          </button>
          <button
            onClick={saveEdit}
            disabled={saving || !editTitel.trim()}
            data-testid={`edit-save-${item.id}`}
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-white bg-green-600 hover:bg-green-500 disabled:opacity-50 flex items-center gap-1">
            <Save className="w-3 h-3" /> {saving ? 'Opslaan...' : 'Opslaan'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div data-testid={`item-${item.id}`} className={`p-3 bg-slate-900/50 border rounded-xl transition-all ${item.done ? 'border-slate-800/50 opacity-60' : 'border-slate-800 hover:border-slate-600'}`}>
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
          {item.inhoud && <p className="text-xs text-slate-400 mt-1 whitespace-pre-wrap">{item.inhoud}</p>}
          {/* v6_order_shipped_ui_001 — Markeer verzonden knop voor shop-orders */}
          {item.source === 'shop_order' && item.order_id && !item.done && (
            <div className="mt-2 flex items-center gap-2 flex-wrap">
              <input
                type="text"
                value={item._tracking || ''}
                onChange={e => { item._tracking = e.target.value; }}
                placeholder="Track & trace (optioneel)"
                data-testid={`ship-tracking-${item.order_id}`}
                className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-[11px] text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
              <button
                data-testid={`mark-shipped-${item.order_id}`}
                onClick={async () => {
                  if (!window.confirm(`Bestelling #${item.order_id} markeren als verzonden? User krijgt bark.`)) return;
                  const tracking = document.querySelector(`[data-testid="ship-tracking-${item.order_id}"]`)?.value || null;
                  const r = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/shop/orders/${item.order_id}/ship`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ viewer_id: 'user-001', tracking_info: tracking }),
                  }).then(x => x.json());
                  if (r.success) {
                    toggleDone(item);
                  } else {
                    alert('Verzenden mislukt: ' + (r.detail || 'onbekende fout'));
                  }
                }}
                className="px-2.5 py-1 rounded-md text-[11px] font-bold text-white bg-green-600 hover:bg-green-500">
                📦 Markeer verzonden
              </button>
            </div>
          )}
          <div className="flex items-center gap-3 mt-2">
            <span className="text-[10px] text-slate-600">{new Date(item.datum || item.created_at).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}</span>
            {item.created_by && <span className="text-[10px] text-slate-600">{item.created_by}</span>}
            {item.updated_at && <span className="text-[10px] text-amber-600/80" title={`Bewerkt op ${new Date(item.updated_at).toLocaleString('nl-NL')}`}>(bewerkt)</span>}
            {(item.tags || []).slice(0, 2).map((t, i) => <span key={i} className="text-[10px] text-slate-600">#{t}</span>)}
          </div>
        </div>
        <div className="flex items-start gap-0.5 flex-shrink-0">
          {canEdit && (
            <button
              onClick={startEdit}
              data-testid={`edit-${item.id}`}
              title="Bewerken"
              className="p-1.5 hover:bg-amber-500/10 text-slate-600 hover:text-amber-400 rounded-lg transition-colors">
              <Pencil className="w-3.5 h-3.5" />
            </button>
          )}
          <button onClick={() => deleteItem(item)} className="p-1.5 hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded-lg transition-colors">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
