/**
 * v13d_bugs_list_kladblok_001 (sessie 56b) — Willem: "Bugs-tab in notities is
 * een admin-ding, breng even onder in Widget Kladblok tot goede plek."
 *
 * Zelfstandige widget: eigen fetch, eigen status-updates, eigen bulk-close.
 * Verplaatsen later = 1 import elders.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Bug, AlertTriangle, Clock, Trash2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const BUG_STATUSES = {
  nieuw: { label: 'Nieuw', color: '#ef4444' },
  bezig: { label: 'Bezig', color: '#f59e0b' },
  opgelost: { label: 'Opgelost', color: '#22c55e' },
  closed: { label: 'Gesloten', color: '#64748b' },
};

export function BugsListWidget() {
  const [bugs, setBugs] = useState([]);
  const [loading, setLoading] = useState(true);
  // Widget draait admin-only in Kladblok; user_id ophalen uit localStorage-style
  // is niet nodig — bugs/list retourneert alles wanneer viewer_id een admin is.
  // We halen viewer_id uit een input `?viewer_id=` fallback of we gebruiken user-001.
  const viewerId = (typeof window !== 'undefined' && window.__auth_user_id) || 'user-001';

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/bugs/list?viewer_id=${viewerId}`).then(x => x.json());
      setBugs(r.bugs || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [viewerId]);

  useEffect(() => { load(); }, [load]);

  const updateStatus = async (b, newStatus) => {
    await fetch(`${API}/api/bugs/${b.id}/status`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ viewer_id: viewerId, status: newStatus }),
    });
    load();
  };

  const deleteBug = async (b) => {
    if (!window.confirm(`Bug "${b.description?.slice(0, 40)}..." verwijderen?`)) return;
    await fetch(`${API}/api/bugs/${b.id}?viewer_id=${viewerId}`, { method: 'DELETE' });
    load();
  };

  const bulkCloseResolved = async () => {
    const resolved = bugs.filter(b => b.status === 'opgelost');
    if (!resolved.length) { alert('Geen opgeloste bugs.'); return; }
    if (!window.confirm(`${resolved.length} opgeloste bugs sluiten?`)) return;
    for (const b of resolved) {
      await fetch(`${API}/api/bugs/${b.id}/status`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewer_id: viewerId, status: 'closed' }),
      });
    }
    load();
  };

  return (
    <div data-testid="bugs-list-widget" className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Bug className="w-3.5 h-3.5" style={{ color: 'var(--alert-base, #ef4444)' }} />
          <h3 className="text-xs font-semibold text-white">Bug meldingen</h3>
          <span className="text-[9px] text-slate-500">
            {bugs.length} · {bugs.filter(b => b.status === 'nieuw').length} nieuw · {bugs.filter(b => b.status === 'opgelost').length} opgelost
          </span>
        </div>
        <button
          data-testid="bugs-bulk-close-resolved"
          onClick={bulkCloseResolved}
          className="text-[10px] px-2 py-0.5 rounded border border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white transition-colors">
          Bulk-close opgelost
        </button>
      </div>

      <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
        {loading ? (
          <p className="text-[10px] text-slate-500 italic text-center py-4">Laden...</p>
        ) : bugs.length === 0 ? (
          <div className="py-8 text-center">
            <Bug className="w-8 h-8 text-slate-700 mx-auto mb-2" />
            <p className="text-xs text-slate-500">Nog geen bugmeldingen.</p>
          </div>
        ) : bugs.map(b => {
          const st = BUG_STATUSES[b.status] || BUG_STATUSES.nieuw;
          return (
            <div key={b.id} data-testid={`bug-${b.id}`} className="p-2.5 bg-slate-950/40 border border-slate-800 rounded-lg">
              <div className="flex items-start gap-2">
                <div className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: `${st.color}15` }}>
                  <AlertTriangle className="w-3 h-3" style={{ color: st.color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[9px] px-1.5 py-0.5 rounded font-medium" style={{ background: `${st.color}20`, color: st.color }}>{st.label}</span>
                    <span className="text-[9px] text-slate-500">{b.created_by_naam || 'Anoniem'}</span>
                    {b.page && <span className="text-[9px] text-slate-600">· {b.page}</span>}
                    <span className="text-[9px] text-slate-600 ml-auto flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" /> {new Date(b.created_at).toLocaleString('nl-NL', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-xs text-white mt-1 whitespace-pre-wrap">{b.description}</p>
                  {b.when && <p className="text-[10px] text-slate-400 mt-0.5">Wanneer: {b.when}</p>}
                  <div className="flex items-center gap-1 mt-1.5 flex-wrap">
                    {Object.entries(BUG_STATUSES).filter(([k]) => k !== b.status).map(([k, v]) => (
                      <button key={k} data-testid={`bug-status-${k}`} onClick={() => updateStatus(b, k)}
                        className="text-[9px] px-1.5 py-0.5 rounded border border-slate-700 text-slate-400 hover:border-slate-500 hover:text-white transition-colors">
                        → {v.label}
                      </button>
                    ))}
                    <button
                      onClick={() => deleteBug(b)}
                      className="ml-auto p-0.5 rounded transition-colors"
                      style={{ color: '#64748b' }}
                      onMouseEnter={e => { e.currentTarget.style.color = 'var(--alert-base)'; e.currentTarget.style.backgroundColor = 'color-mix(in srgb, var(--alert-base) 10%, transparent)'; }}
                      onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; e.currentTarget.style.backgroundColor = ''; }}>
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
