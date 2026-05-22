// v4_update_bark_001 — Admin Deploy Anker Panel
// Laat admin een nieuwe versie verankeren → bark naar alle users bij volgende login
import React, { useState, useEffect, useCallback } from 'react';
import { Rocket, Plus, Trash2, RefreshCw, Shield, Star, Calendar } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const KIND_META = {
  privacy: { icon: Shield, color: '#06b6d4', label: 'Privacy' },
  deploy: { icon: Rocket, color: '#f59e0b', label: 'Deploy' },
  feature: { icon: Star, color: '#a855f7', label: 'Feature' },
};

export function DeployAnchorPanel({ viewerId }) {
  const [anchors, setAnchors] = useState([]);
  const [current, setCurrent] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const [version, setVersion] = useState('');
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [icon, setIcon] = useState('🚀');
  const [roadmapRef, setRoadmapRef] = useState('');
  const [audience, setAudience] = useState('all');

  const load = useCallback(() => {
    fetch(`${API}/api/deploy/anchors?viewer_id=${viewerId}`)
      .then(r => r.json())
      .then(d => { setAnchors(d.barks || []); setCurrent(d.current); })
      .catch(() => {});
  }, [viewerId]);

  useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    if (!version.trim()) { setErr('Version is verplicht'); return; }
    setBusy(true); setErr(null);
    try {
      const r = await fetch(`${API}/api/deploy/anchor`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          viewer_id: viewerId,
          version: version.trim(),
          title: title.trim() || undefined,
          message: message.trim() || undefined,
          icon: icon.trim() || undefined,
          roadmap_ref: roadmapRef.trim() || undefined,
          audience,
        }),
      });
      const d = await r.json();
      if (r.ok) {
        setShowForm(false);
        setVersion(''); setTitle(''); setMessage(''); setRoadmapRef('');
        load();
      } else {
        setErr(d.detail || 'Fout bij verankeren');
      }
    } catch {
      setErr('Netwerkfout');
    } finally { setBusy(false); }
  };

  const remove = async (id) => {
    if (id === 'privacy_v1') return;
    if (!window.confirm(`Anker ${id} verwijderen? Iedereen die het nog niet zag, ziet het ook niet meer.`)) return;
    setBusy(true);
    try {
      await fetch(`${API}/api/deploy/anchor/${id}?viewer_id=${viewerId}`, { method: 'DELETE' });
      load();
    } finally { setBusy(false); }
  };

  return (
    <div data-testid="deploy-anchor-panel" className="max-w-3xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Rocket className="w-4 h-4 text-amber-400" /> Deploy Ankers & Update Barks
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Anker huidige versie na elke deploy. Iedereen krijgt 1x een bark bij volgende login.
            {current && <> Huidig: <span className="text-amber-400 font-mono">{current}</span></>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={load} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 transition-colors" title="Refresh">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <button data-testid="anchor-new-btn" onClick={() => setShowForm(s => !s)}
            className="px-3 py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5">
            <Plus className="w-3.5 h-3.5" /> {showForm ? 'Sluit' : 'Nieuwe anker'}
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={submit} data-testid="anchor-form" className="bg-slate-900/50 border border-amber-500/20 rounded-xl p-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] text-slate-400 mb-1 uppercase tracking-wider">Versie *</label>
              <input data-testid="anchor-version" type="text" value={version} onChange={e => setVersion(e.target.value)}
                placeholder="v0.6.5" required
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white font-mono focus:border-amber-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-[10px] text-slate-400 mb-1 uppercase tracking-wider">Icon</label>
              <input type="text" value={icon} onChange={e => setIcon(e.target.value)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:border-amber-500 focus:outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-[10px] text-slate-400 mb-1 uppercase tracking-wider">Titel (optioneel)</label>
            <input type="text" value={title} onChange={e => setTitle(e.target.value)}
              placeholder="Spark Core v0.6.5"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:border-amber-500 focus:outline-none" />
          </div>
          <div>
            <label className="block text-[10px] text-slate-400 mb-1 uppercase tracking-wider">Bericht (laat leeg = auto uit CHANGELOG)</label>
            <textarea data-testid="anchor-message" value={message} onChange={e => setMessage(e.target.value)} rows={4}
              placeholder="Wat is er nieuw in deze versie..."
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white resize-none focus:border-amber-500 focus:outline-none" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] text-slate-400 mb-1 uppercase tracking-wider">Roadmap referentie</label>
              <input type="text" value={roadmapRef} onChange={e => setRoadmapRef(e.target.value)}
                placeholder="phase-5"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:border-amber-500 focus:outline-none" />
            </div>
            <div>
              <label className="block text-[10px] text-slate-400 mb-1 uppercase tracking-wider">Audience</label>
              <select value={audience} onChange={e => setAudience(e.target.value)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:border-amber-500 focus:outline-none">
                <option value="all">Iedereen</option>
                <option value="admins">Alleen admins (gradatie ≤ 2)</option>
              </select>
            </div>
          </div>
          {err && <p className="text-xs text-red-400">{err}</p>}
          <div className="flex justify-end">
            <button data-testid="anchor-submit" type="submit" disabled={busy}
              className="px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded-lg text-xs font-medium transition-colors disabled:opacity-50">
              {busy ? 'Verankeren…' : 'Anker & broadcast'}
            </button>
          </div>
        </form>
      )}

      {/* Lijst van bestaande ankers */}
      <div className="space-y-2">
        {anchors.length === 0 && (
          <p className="text-center text-slate-500 text-xs py-8">Nog geen ankers.</p>
        )}
        {anchors.map(b => {
          const meta = KIND_META[b.kind] || KIND_META.deploy;
          const Icon = meta.icon;
          return (
            <div key={b.id} data-testid={`anchor-${b.id}`}
              className="flex items-start gap-3 p-3 bg-slate-900/50 border border-slate-800 rounded-xl">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                style={{ background: `${meta.color}15`, border: `1px solid ${meta.color}40` }}>
                <span className="text-lg">{b.icon || <Icon className="w-4 h-4" style={{ color: meta.color }} />}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider"
                    style={{ background: `${meta.color}20`, color: meta.color }}>{meta.label}</span>
                  <span className="text-sm font-bold text-white font-mono">{b.id}</span>
                  {b.audience === 'admins' && <span className="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400">admins-only</span>}
                  {current === b.id && <span className="text-[9px] px-1 py-0.5 rounded bg-emerald-500/15 text-emerald-300">CURRENT</span>}
                </div>
                <p className="text-sm text-slate-300 mt-0.5">{b.title}</p>
                <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{b.message}</p>
                <p className="text-[10px] text-slate-600 mt-1 flex items-center gap-1">
                  <Calendar className="w-2.5 h-2.5" />
                  {b.anchored_at ? new Date(b.anchored_at).toLocaleString('nl-NL', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                  {b.anchored_by && <span className="ml-2">door {b.anchored_by}</span>}
                </p>
              </div>
              {b.id !== 'privacy_v1' && (
                <button onClick={() => remove(b.id)} disabled={busy}
                  data-testid={`anchor-delete-${b.id}`}
                  className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default DeployAnchorPanel;
