// v5_tikkie_topup_001 — Admin Tikkie-aanvragen review (alleen gradatie ≤ 2)
import React, { useState, useEffect, useCallback } from 'react';
import { X, Loader2, Check, AlertCircle, Euro, RefreshCw } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function AdminTikkieReview({ open, onClose, user }) {
  const [topups, setTopups] = useState([]);
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('pending');
  const [selected, setSelected] = useState(null);
  const [potje, setPotje] = useState('0');
  const [free, setFree] = useState('');
  const [note, setNote] = useState('');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    if (!user?.id) return;
    setLoading(true);
    fetch(`${API}/api/wallet/tikkie/list?viewer_id=${user.id}&status=${filter}`)
      .then(r => r.json())
      .then(d => { setTopups(d.topups || []); setCounts(d.counts || {}); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user?.id, filter]);

  useEffect(() => { if (open) load(); }, [open, load]);

  useEffect(() => {
    if (selected) {
      setPotje('0');
      setFree(selected.amount_eur.toFixed(2));
      setNote('');
      setError(null);
    }
  }, [selected]);

  if (!open) return null;

  const confirm = async () => {
    setProcessing(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/wallet/tikkie/${selected.id}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          viewer_id: user.id,
          potje_amount: parseFloat(potje) || 0,
          free_amount: parseFloat(free) || 0,
          note: note.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.detail || 'Mislukt');
      setSelected(null);
      load();
    } catch (e) {
      setError(e.message || 'Bevestigen mislukt.');
    } finally {
      setProcessing(false);
    }
  };

  const cancel = async (topup) => {
    if (!window.confirm(`Annuleer Tikkie-aanvraag €${topup.amount_eur.toFixed(2)} van ${topup.user_naam}?`)) return;
    await fetch(`${API}/api/wallet/tikkie/${topup.id}/cancel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ viewer_id: user.id, reason: 'Door admin geannuleerd' }),
    });
    load();
  };

  return (
    <div data-testid="admin-tikkie-modal" className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="w-full max-w-2xl max-h-[90vh] bg-slate-900 border border-amber-500/30 rounded-2xl flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Tikkie-aanvragen (admin)</h3>
            <p className="text-[10px] text-slate-400">
              Pending: {counts.pending || 0} • Bevestigd: {counts.confirmed || 0} • Geannuleerd: {counts.cancelled || 0}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={load} data-testid="tikkie-refresh" className="p-1.5 hover:bg-slate-800 rounded-lg" title="Vernieuwen">
              <RefreshCw className={`w-4 h-4 text-slate-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button onClick={onClose} data-testid="admin-tikkie-close" className="p-1.5 hover:bg-slate-800 rounded-lg">
              <X className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="px-5 pt-3 border-b border-slate-800 flex gap-1">
          {['pending', 'confirmed', 'cancelled'].map(s => (
            <button key={s} data-testid={`filter-${s}`} onClick={() => setFilter(s)}
              className={`px-3 py-2 text-xs font-medium rounded-t-lg ${
                filter === s ? 'text-amber-400 border-b-2 border-amber-500' : 'text-slate-400 hover:text-slate-200'
              }`}>
              {s === 'pending' ? 'In afwachting' : s === 'confirmed' ? 'Bevestigd' : 'Geannuleerd'} ({counts[s] || 0})
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {topups.length === 0 && !loading && (
            <p className="text-center text-xs text-slate-500 py-8">Geen aanvragen in deze categorie.</p>
          )}
          {topups.map(t => (
            <div key={t.id} data-testid={`topup-row-${t.id}`} className="bg-slate-800/40 border border-slate-700/50 rounded-lg p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Euro className="w-3.5 h-3.5 text-amber-400" />
                    <span className="text-base font-bold text-white">€{t.amount_eur.toFixed(2)}</span>
                    <span className="text-[10px] text-slate-500 font-mono">#{t.id.slice(0, 10)}</span>
                  </div>
                  <p className="text-xs text-slate-300">
                    <b>{t.user_naam}</b> — invoer: "{t.naam_invoer}"
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">{new Date(t.created_at).toLocaleString('nl-NL')}</p>
                  {t.status === 'confirmed' && (
                    <p className="text-[10px] text-green-400 mt-1">
                      ✓ Bevestigd: €{(t.free_amount || 0).toFixed(2)} vrij + €{(t.potje_amount || 0).toFixed(2)} potje
                      {t.note && <span className="block text-slate-400 italic">"{t.note}"</span>}
                    </p>
                  )}
                </div>
                {t.status === 'pending' && (
                  <div className="flex flex-col gap-1.5">
                    <button data-testid={`btn-confirm-${t.id}`} onClick={() => setSelected(t)}
                      className="px-3 py-1.5 text-[11px] font-bold rounded-lg text-white bg-green-600 hover:bg-green-500">
                      Bevestigen
                    </button>
                    <button data-testid={`btn-cancel-${t.id}`} onClick={() => cancel(t)}
                      className="px-3 py-1.5 text-[11px] font-medium rounded-lg text-red-300 hover:bg-red-500/10">
                      Annuleren
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Inline confirm dialog */}
        {selected && (
          <div className="absolute inset-0 bg-black/80 flex items-center justify-center p-4 rounded-2xl" onClick={() => setSelected(null)}>
            <div className="w-full max-w-sm bg-slate-900 border border-green-500/30 rounded-xl p-5 space-y-3" onClick={e => e.stopPropagation()}>
              <h4 className="text-sm font-bold text-white">Tikkie bevestigen</h4>
              <p className="text-xs text-slate-400">
                €{selected.amount_eur.toFixed(2)} van <b>{selected.user_naam}</b> ({selected.naam_invoer})
              </p>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-400 uppercase tracking-wider">Potje (€)</label>
                  <input data-testid="confirm-potje" type="number" step="0.01" min="0" value={potje}
                    onChange={e => {
                      const v = e.target.value;
                      setPotje(v);
                      const p = parseFloat(v) || 0;
                      setFree((selected.amount_eur - p).toFixed(2));
                    }}
                    className="mt-1 w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-white" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 uppercase tracking-wider">Vrij saldo (€)</label>
                  <input data-testid="confirm-free" type="number" step="0.01" min="0" value={free}
                    onChange={e => setFree(e.target.value)}
                    className="mt-1 w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-sm text-white" />
                </div>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider">Notitie (optioneel)</label>
                <input data-testid="confirm-note" value={note} onChange={e => setNote(e.target.value)}
                  placeholder="bv. eerste storting"
                  className="mt-1 w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white placeholder-slate-500" />
              </div>
              {error && (
                <div className="flex items-center gap-2 text-xs text-red-300 bg-red-500/10 border border-red-500/30 rounded-lg p-2">
                  <AlertCircle className="w-3.5 h-3.5" /> {error}
                </div>
              )}
              <div className="flex gap-2 pt-1">
                <button data-testid="confirm-cancel-btn" onClick={() => setSelected(null)}
                  className="flex-1 py-2 text-xs font-medium rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700">
                  Terug
                </button>
                <button data-testid="confirm-submit-btn" onClick={confirm} disabled={processing}
                  className="flex-1 py-2 text-xs font-bold rounded-lg text-white bg-green-600 hover:bg-green-500 flex items-center justify-center gap-2 disabled:opacity-60">
                  {processing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  Bevestigen
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminTikkieReview;
