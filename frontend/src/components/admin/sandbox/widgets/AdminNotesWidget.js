/**
 * v13d_admin_notes_kladblok_001 (sessie 56b) — Willem: "admin notities maar
 * even een kader voor in Widget Kladblok om zo te splitten".
 *
 * Toont ALLE notities met scope=admin (van alle admin-users). Bedoeld als
 * scratchpad voor systeem-observaties, roadmap-brainfarts, dev-todo's.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Settings, Trash2, StickyNote } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function AdminNotesWidget() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newTitel, setNewTitel] = useState('');
  const [newInhoud, setNewInhoud] = useState('');
  const viewerId = (typeof window !== 'undefined' && window.__auth_user_id) || 'user-001';

  const load = useCallback(async () => {
    setLoading(true);
    try {
      // Haal alle notes op voor deze admin en filter op scope=admin.
      // (Backend /notes/all filtert al op user_id; voor cross-user admin-notes
      // moeten admins hun eigen admin-notes zien.)
      const r = await fetch(`${API}/api/notes/all?user_id=${viewerId}&viewer_id=${viewerId}`).then(x => x.json());
      const adminOnly = (r.notes || []).filter(n => n.scope === 'admin');
      setNotes(adminOnly);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [viewerId]);

  useEffect(() => { load(); }, [load]);

  const addAdminNote = async () => {
    if (!newTitel.trim()) return;
    await fetch(`${API}/api/notes/create`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        titel: newTitel,
        inhoud: newInhoud,
        categorie: 'Admin',
        priority: 'medium',
        scope: 'admin',
        user_id: viewerId,
      }),
    });
    setNewTitel(''); setNewInhoud('');
    load();
  };

  const deleteNote = async (n) => {
    if (!window.confirm(`Admin-notitie "${n.titel}" verwijderen?`)) return;
    await fetch(`${API}/api/notes/delete/${n.id}?user_id=${viewerId}`, { method: 'DELETE' });
    load();
  };

  return (
    <div data-testid="admin-notes-widget" className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Settings className="w-3.5 h-3.5 text-purple-400" />
          <h3 className="text-xs font-semibold text-white">Admin notities</h3>
          <span className="text-[9px] text-slate-500">{notes.length}</span>
        </div>
      </div>

      {/* Nieuw admin-notitie */}
      <div className="p-3 border-b border-slate-800 bg-slate-950/40 space-y-2">
        <input
          data-testid="admin-note-titel"
          value={newTitel}
          onChange={e => setNewTitel(e.target.value)}
          placeholder="Titel..."
          className="w-full px-2 py-1.5 bg-slate-800/50 border border-purple-500/20 rounded text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500/50"
        />
        <textarea
          data-testid="admin-note-inhoud"
          value={newInhoud}
          onChange={e => setNewInhoud(e.target.value)}
          placeholder="Inhoud, brainfart, todo..."
          rows={2}
          className="w-full px-2 py-1.5 bg-slate-800/50 border border-purple-500/20 rounded text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500/50 resize-none"
        />
        <button
          data-testid="admin-note-save"
          onClick={addAdminNote}
          disabled={!newTitel.trim()}
          className="px-3 py-1 rounded text-[10px] font-medium bg-purple-600 hover:bg-purple-500 disabled:opacity-40 text-white transition">
          + Admin notitie
        </button>
      </div>

      <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
        {loading ? (
          <p className="text-[10px] text-slate-500 italic text-center py-4">Laden...</p>
        ) : notes.length === 0 ? (
          <div className="py-6 text-center">
            <StickyNote className="w-6 h-6 text-slate-700 mx-auto mb-2" />
            <p className="text-[11px] text-slate-500">Nog geen admin-notities.</p>
          </div>
        ) : notes.map(n => (
          <div key={n.id} data-testid={`admin-note-${n.id}`} className="p-2 bg-slate-950/40 border border-slate-800 rounded">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-white truncate">{n.titel}</p>
                {n.inhoud && <p className="text-[11px] text-slate-400 mt-0.5 whitespace-pre-wrap">{n.inhoud}</p>}
                <p className="text-[9px] text-slate-600 mt-1">
                  {(n.datum || '').slice(0, 10)} · {n.created_by || n.user_id}
                </p>
              </div>
              <button
                onClick={() => deleteNote(n)}
                className="p-1 rounded transition-colors text-slate-600"
                onMouseEnter={e => { e.currentTarget.style.color = 'var(--alert-base)'; e.currentTarget.style.backgroundColor = 'color-mix(in srgb, var(--alert-base) 10%, transparent)'; }}
                onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.backgroundColor = ''; }}>
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
