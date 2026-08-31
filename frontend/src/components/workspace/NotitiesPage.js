import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  StickyNote, Plus, Search, Trash2,
  Tag, Clock, ListTodo, FileText, Save,
  Circle, CheckCircle, Bug, AlertTriangle, Pencil, X
} from 'lucide-react';
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
  const { user, isAdmin } = useAuth();
  // v12_admin_toggle_001 — admin tabs/features (deploy-tab, alle-bugs-lijst, bug status/delete)
  // gated via AuthContext isAdmin, niet meer gradatie-gebaseerd.
  const isAdminViewer = isAdmin;
  const [notes, setNotes] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('all');
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState('Alles');
  const [showNew, setShowNew] = useState(false);
  const [newItem, setNewItem] = useState({
    type: 'note', titel: '', inhoud: '', categorie: 'Observatie', priority: 'medium', scope: 'prive',
    // v13d_task_doel_001 — taak = doel met tijdvenster + budget
    begin_datum: '', eind_datum: '', budget_uren: '', opdrachtgever: '', onderwerp: '',
  });
  const [bugs, setBugs] = useState([]);
  const [showBugForm, setShowBugForm] = useState(false);
  const [newBug, setNewBug] = useState({ description: '', when: '', page: '' });
  const [bugSubmitMsg, setBugSubmitMsg] = useState(null);
  // v13c_dashboard_live_cards_002 — focus-id vanuit dashboard-klik
  const [focusId, setFocusId] = useState(null);

  // Bij mount: check of dashboard een focus-item heeft doorgegeven via sessionStorage
  useEffect(() => {
    try {
      const fid = sessionStorage.getItem('notes_focus_id');
      const kind = sessionStorage.getItem('notes_focus_kind');
      if (fid) {
        setFocusId(fid);
        if (kind === 'task') setViewMode('tasks');
        else if (kind === 'note') setViewMode('notes');
        sessionStorage.removeItem('notes_focus_id');
        sessionStorage.removeItem('notes_focus_kind');
      }
    } catch {}
  }, []);

  // Scroll naar en highlight het focus-item zodra items geladen zijn
  useEffect(() => {
    if (!focusId || loading) return;
    // Wacht 1 render-tick zodat DOM up-to-date is
    const t = setTimeout(() => {
      const el = document.querySelector(`[data-note-item-id="${focusId}"]`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('ring-2', 'ring-amber-400', 'ring-offset-2', 'ring-offset-slate-900');
        setTimeout(() => el.classList.remove('ring-2', 'ring-amber-400', 'ring-offset-2', 'ring-offset-slate-900'), 3000);
      }
      setFocusId(null); // niet meer nodig
    }, 250);
    return () => clearTimeout(t);
  }, [focusId, loading, notes, tasks]);

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
    ...tasks.map(t => ({
      ...t, type: 'task', titel: t.task, inhoud: '', categorie: 'Taak', tags: [],
      datum: t.created_at, created_by: 'Willem', done: t.status === 'done',
    })),
  ].sort((a, b) => (b.datum || b.created_at || '').localeCompare(a.datum || a.created_at || ''));

  const filtered = items.filter(i => {
    if (viewMode === 'notes' && i.type !== 'note') return false;
    if (viewMode === 'tasks' && i.type !== 'task') return false;
    // v13d_notes_scope_001 — admin-scope hoort NIET op de reguliere notitie-pagina
    // (staat in Widget Kladblok → AdminNotesWidget).
    if ((i.scope || 'prive') === 'admin') return false;
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
        body: JSON.stringify({ titel: newItem.titel, inhoud: newItem.inhoud, categorie: newItem.categorie, priority: newItem.priority, scope: newItem.scope, user_id: user.id }),
      });
      const data = await res.json();
      if (data.success) setNotes([data.note, ...notes]);
    } else {
      const res = await fetch(`${API}/api/notes/tasks/create`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: newItem.titel,
          priority: newItem.priority,
          scope: newItem.scope,
          user_id: user.id,
          begin_datum: newItem.begin_datum || null,
          eind_datum: newItem.eind_datum || null,
          budget_uren: newItem.budget_uren ? Number(newItem.budget_uren) : null,
          opdrachtgever: newItem.opdrachtgever || null,
          onderwerp: newItem.onderwerp || null,
        }),
      });
      const data = await res.json();
      if (data.success) setTasks([...tasks, data.task]);
    }
    setNewItem({ type: 'note', titel: '', inhoud: '', categorie: 'Observatie', priority: 'medium', scope: 'prive',
      begin_datum: '', eind_datum: '', budget_uren: '', opdrachtgever: '', onderwerp: '' });
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

  if (loading) return <MainLayout activePage="notities" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 rounded-full animate-spin" style={{ borderColor: 'color-mix(in srgb, var(--glow-base) 30%, transparent)', borderTopColor: 'var(--glow-base)' }} /></div></MainLayout>;

  return (
    <MainLayout activePage="notities" onNavigate={onNavigate}>
      <div data-testid="notities-page" className="h-full flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'var(--glow-base)' }}>
              <StickyNote className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Notities & Taken</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{notesTotal} notities, {tasksDone}/{tasksTotal} taken klaar</p>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <button data-testid="add-note-btn" onClick={() => setShowNew(!showNew)} className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-white" style={{ background: 'var(--glow-base)' }}>
                <Plus className="w-3.5 h-3.5" /> Nieuw
              </button>
              <button data-testid="report-bug-btn" onClick={() => { setShowBugForm(true); setBugSubmitMsg(null); }}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                style={{
                  color: 'color-mix(in srgb, var(--alert-base) 80%, white)',
                  borderWidth: '1px', borderStyle: 'solid',
                  borderColor: 'color-mix(in srgb, var(--alert-base) 30%, transparent)',
                  background: 'color-mix(in srgb, var(--alert-base) 5%, transparent)',
                }}>
                Bug melden
              </button>
            </div>
          </div>
          <div className="flex">
            {[
              { id: 'all', label: 'Alles', icon: FileText, count: items.length },
              { id: 'notes', label: 'Notities', icon: StickyNote, count: notesTotal },
              { id: 'tasks', label: 'Taken', icon: ListTodo, count: tasksTotal },
            ].map(t => (
              <button key={t.id} data-testid={`view-${t.id}`} onClick={() => setViewMode(t.id)}
                className="relative flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors"
                style={{ color: viewMode === t.id ? 'var(--glow-base)' : '#94a3b8' }}>
                <t.icon className="w-3.5 h-3.5" /> {t.label}{t.count !== null ? ` (${t.count})` : ''}
                {viewMode === t.id && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full" style={{ background: 'var(--glow-base)' }} />}
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
                  <button data-testid="bug-submit" onClick={submitBug} className="px-4 py-1.5 rounded-lg text-xs font-medium text-white hover:brightness-110" style={{ background: 'var(--alert-base)' }}>Verzenden</button>
                </div>
              </div>
            </div>
          )}

          {viewMode === 'bugs' && isAdminViewer ? (
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
              <div className="p-4 bg-slate-900/60 rounded-xl space-y-3" style={{ borderWidth: '1px', borderStyle: 'solid', borderColor: 'color-mix(in srgb, var(--glow-base) 20%, transparent)' }}>
                <div className="flex gap-2">
                  {['note', 'task'].map(t => (
                    <button key={t} onClick={() => setNewItem({ ...newItem, type: t })}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                      style={newItem.type === t
                        ? { background: 'var(--glow-base)', color: '#ffffff' }
                        : { background: 'rgba(30,41,59,1)', color: '#94a3b8' }}>
                      {t === 'note' ? 'Notitie' : 'Taak'}
                    </button>
                  ))}
                </div>
                {/* v13d_notes_scope_001 — scope-toggle prive/zakelijk (admin alleen via directe backend of Kladblok) */}
                <div className="flex gap-2">
                  <button
                    data-testid="scope-prive-note-btn"
                    onClick={() => setNewItem({ ...newItem, scope: 'prive' })}
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition"
                    style={newItem.scope === 'prive' ? {
                      background: 'color-mix(in srgb, var(--glow-base) 20%, transparent)',
                      borderWidth: '1px', borderStyle: 'solid',
                      borderColor: 'color-mix(in srgb, var(--glow-base) 50%, transparent)',
                      color: 'var(--glow-base)',
                    } : { background: 'rgba(30,41,59,0.5)', borderWidth: '1px', borderStyle: 'solid', borderColor: 'rgba(51,65,85,0.5)', color: '#94a3b8' }}>
                    🏠 Privé
                  </button>
                  <button
                    data-testid="scope-zakelijk-note-btn"
                    onClick={() => setNewItem({ ...newItem, scope: 'zakelijk' })}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${newItem.scope === 'zakelijk' ? 'bg-amber-500/20 border border-amber-500/50 text-amber-300' : 'bg-slate-800/50 border border-slate-700/50 text-slate-400'}`}>
                    💼 Zakelijk
                  </button>
                  {isAdminViewer && (
                    <button
                      data-testid="scope-admin-note-btn"
                      onClick={() => setNewItem({ ...newItem, scope: 'admin' })}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition"
                      style={newItem.scope === 'admin' ? {
                        background: 'rgba(147,51,234,0.2)', borderWidth: '1px', borderStyle: 'solid',
                        borderColor: 'rgba(147,51,234,0.5)', color: '#c4b5fd',
                      } : { background: 'rgba(30,41,59,0.5)', borderWidth: '1px', borderStyle: 'solid', borderColor: 'rgba(51,65,85,0.5)', color: '#94a3b8' }}>
                      ⚙️ Admin
                    </button>
                  )}
                </div>
                <input type="text" value={newItem.titel} onChange={e => setNewItem({ ...newItem, titel: e.target.value })} placeholder={newItem.type === 'note' ? 'Titel...' : 'Taak omschrijving...'}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none" />
                {newItem.type === 'note' && (
                  <textarea value={newItem.inhoud} onChange={e => setNewItem({ ...newItem, inhoud: e.target.value })} placeholder="Inhoud..." rows={3}
                    className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none resize-none" />
                )}
                {/* v13d_task_doel_001 — taak-specifieke velden: tijdvenster + budget */}
                {newItem.type === 'task' && (
                  <>
                    <div className="grid grid-cols-3 gap-2">
                      <input data-testid="task-begin-datum" type="date" value={newItem.begin_datum}
                        onChange={e => setNewItem({ ...newItem, begin_datum: e.target.value })}
                        title="Aanvang"
                        className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white focus:outline-none" />
                      <input data-testid="task-eind-datum" type="date" value={newItem.eind_datum}
                        onChange={e => setNewItem({ ...newItem, eind_datum: e.target.value })}
                        title="Einde"
                        className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white focus:outline-none" />
                      <input data-testid="task-budget-uren" type="number" step="0.5" min="0"
                        value={newItem.budget_uren}
                        onChange={e => setNewItem({ ...newItem, budget_uren: e.target.value })}
                        placeholder="Budget u"
                        className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                    </div>
                    {newItem.scope === 'zakelijk' && (
                      <div className="grid grid-cols-2 gap-2">
                        <input data-testid="task-opdrachtgever" type="text"
                          value={newItem.opdrachtgever}
                          onChange={e => setNewItem({ ...newItem, opdrachtgever: e.target.value })}
                          placeholder="Opdrachtgever..."
                          className="px-3 py-1.5 bg-slate-800/50 border border-amber-500/20 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
                        <input data-testid="task-onderwerp" type="text"
                          value={newItem.onderwerp}
                          onChange={e => setNewItem({ ...newItem, onderwerp: e.target.value })}
                          placeholder="Onderwerp / offerte..."
                          className="px-3 py-1.5 bg-slate-800/50 border border-amber-500/20 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
                      </div>
                    )}
                  </>
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
                  <button data-testid="save-note-btn" onClick={addItem} className="ml-auto px-4 py-1.5 rounded-lg text-xs font-medium text-white" style={{ background: 'var(--glow-base)' }}>Opslaan</button>
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
              <NotitiesTreeView items={filtered} toggleDone={toggleDone} deleteItem={deleteItem} updateItem={updateItem} focusId={focusId} />
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

function NotitiesTreeView({ items, toggleDone, deleteItem, updateItem, focusId }) {
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

  // v13c_dashboard_live_cards_002 — als er een focusId is (vanuit dashboard-klik),
  // vind het item in de tree en open het juiste jaar/maand/dag zodat het item
  // gerendered wordt. De scroll+highlight zit in NotitiesPage.
  React.useEffect(() => {
    if (!focusId) return;
    const target = items.find(it => it.id === focusId);
    if (!target) return;
    const d = new Date(target.datum || target.created_at || Date.now());
    const y = d.getFullYear();
    const m = d.getMonth();
    const dd = d.getDate();
    if (availableYears.includes(y)) setActiveYear(y);
    setOpenMonths(s => ({ ...s, [`${y}-${m}`]: true }));
    setOpenDays(s => ({ ...s, [`${y}-${m}-${dd}`]: true }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusId, items]);

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
              className="text-xs px-3 py-1.5 rounded-t-md transition-colors"
              style={isActive ? {
                color: 'var(--glow-base)',
                background: 'color-mix(in srgb, var(--glow-base) 10%, transparent)',
                borderTop: '1px solid color-mix(in srgb, var(--glow-base) 30%, transparent)',
                borderLeft: '1px solid color-mix(in srgb, var(--glow-base) 30%, transparent)',
                borderRight: '1px solid color-mix(in srgb, var(--glow-base) 30%, transparent)',
              } : { color: '#64748b' }}>
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
      <div data-testid={`item-edit-${item.id}`} className="p-3 bg-slate-900/70 rounded-xl space-y-2" style={{ borderWidth: '1px', borderStyle: 'solid', borderColor: 'color-mix(in srgb, var(--glow-base) 40%, transparent)' }}>
        <div className="flex items-center gap-2">
          <Pencil className="w-3.5 h-3.5" style={{ color: 'var(--glow-base)' }} />
          <span className="text-[10px] uppercase tracking-wider font-medium" style={{ color: 'var(--glow-base)' }}>
            {item.type === 'note' ? 'Notitie bewerken' : 'Taak bewerken'}
          </span>
        </div>
        <input
          type="text"
          value={editTitel}
          onChange={e => setEditTitel(e.target.value)}
          placeholder="Titel..."
          data-testid={`edit-titel-${item.id}`}
          className="w-full px-3 py-2 bg-slate-800/60 border border-slate-700/60 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none"
          autoFocus
        />
        {item.type === 'note' && (
          <textarea
            value={editInhoud}
            onChange={e => setEditInhoud(e.target.value)}
            placeholder="Inhoud..."
            rows={4}
            data-testid={`edit-inhoud-${item.id}`}
            className="w-full px-3 py-2 bg-slate-800/60 border border-slate-700/60 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none resize-none"
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
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-white hover:brightness-110 disabled:opacity-50 flex items-center gap-1"
            style={{ background: 'var(--glow-base)' }}>
            <Save className="w-3 h-3" /> {saving ? 'Opslaan...' : 'Opslaan'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div data-testid={`item-${item.id}`} data-note-item-id={item.id} className={`p-3 bg-slate-900/50 border rounded-xl transition-all ${item.done ? 'border-slate-800/50 opacity-60' : 'border-slate-800 hover:border-slate-600'}`}>
      <div className="flex items-start gap-3">
        {item.type === 'task' ? (
          <button onClick={() => toggleDone(item)} className="mt-0.5 flex-shrink-0">
            {item.done ? <CheckCircle className="w-5 h-5 text-green-400" /> : <Circle className="w-5 h-5 text-slate-600 hover:opacity-80" style={{ transition: 'color 0.15s' }} onMouseEnter={e => e.currentTarget.style.color = 'var(--glow-base)'} onMouseLeave={e => e.currentTarget.style.color = ''} />}
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
            {item.scope === 'zakelijk' && (
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-medium uppercase tracking-wider">💼 Zakelijk</span>
            )}
          </div>
          {item.inhoud && <p className="text-xs text-slate-400 mt-1 whitespace-pre-wrap">{item.inhoud}</p>}
          {/* v13d_task_doel_001 — taak periode + budget + opdrachtgever/onderwerp */}
          {item.type === 'task' && (item.begin_datum || item.eind_datum || item.budget_uren || item.opdrachtgever) && (
            <div className="mt-1 flex items-center gap-2 flex-wrap text-[10px]">
              {(item.begin_datum || item.eind_datum) && (
                <span className="px-1.5 py-0.5 rounded" style={{ background: 'color-mix(in srgb, var(--app-secondary, #06b6d4) 15%, transparent)', color: 'var(--app-secondary, #06b6d4)' }}>
                  📅 {item.begin_datum || '?'} → {item.eind_datum || '?'}
                </span>
              )}
              {item.budget_uren != null && (
                <span className="px-1.5 py-0.5 rounded" style={{ background: 'color-mix(in srgb, var(--app-secondary, #06b6d4) 15%, transparent)', color: 'var(--app-secondary, #06b6d4)' }}>
                  ⏱️ {item.budget_uren}u budget
                </span>
              )}
              {item.opdrachtgever && (
                <span className="text-amber-300">💼 {item.opdrachtgever}</span>
              )}
              {item.onderwerp && (
                <span className="text-slate-500">· {item.onderwerp}</span>
              )}
            </div>
          )}
          {/* v6_order_shipped_ui_001 — Markeer verzonden knop voor shop-orders */}
          {item.source === 'shop_order' && item.order_id && !item.done && (
            <div className="mt-2 flex items-center gap-2 flex-wrap">
              <input
                type="text"
                value={item._tracking || ''}
                onChange={e => { item._tracking = e.target.value; }}
                placeholder="Track & trace (optioneel)"
                data-testid={`ship-tracking-${item.order_id}`}
                className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-[11px] text-white placeholder-slate-500 focus:outline-none"
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
            {item.updated_at && <span className="text-[10px] text-slate-500" title={`Bewerkt op ${new Date(item.updated_at).toLocaleString('nl-NL')}`}>(bewerkt)</span>}
            {(item.tags || []).slice(0, 2).map((t, i) => <span key={i} className="text-[10px] text-slate-600">#{t}</span>)}
          </div>
        </div>
        <div className="flex items-start gap-0.5 flex-shrink-0">
          {canEdit && (
            <button
              onClick={startEdit}
              data-testid={`edit-${item.id}`}
              title="Bewerken"
              className="p-1.5 rounded-lg transition-colors text-slate-600"
              onMouseEnter={e => { e.currentTarget.style.color = 'var(--glow-base)'; e.currentTarget.style.backgroundColor = 'color-mix(in srgb, var(--glow-base) 10%, transparent)'; }}
              onMouseLeave={e => { e.currentTarget.style.color = ''; e.currentTarget.style.backgroundColor = ''; }}>
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
