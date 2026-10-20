// v14_feiten_archief_001 — Beheer → Instellingen → Feiten: index + kaartweergave (mening · waarde · overtuiging · feit)
import React, { useCallback, useEffect, useState } from 'react';
import { BookOpen, Check, X, Trash2, RefreshCw, Loader2, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../../context/AuthContext';
import { apiError } from '../../lib/utils';

const API = process.env.REACT_APP_BACKEND_URL;
const KIND = {
  feit: { label: 'Feit', kleur: '#38bdf8', uitleg: 'toetsbaar — ongetoetst tot jij het toetst' },
  mening: { label: 'Mening', kleur: '#f472b6', uitleg: 'persoonlijk, nooit waar/onwaar' },
  waarde: { label: 'Waarde', kleur: '#fbbf24', uitleg: 'normen & waarden' },
  overtuiging: { label: 'Overtuiging', kleur: '#a78bfa', uitleg: 'geloof / levensbeschouwing' },
};
const STATUS = { ongetoetst: '#94a3b8', getoetst: '#22c55e', verworpen: '#f87171', bevestigd: '#22c55e' };
const sel = 'bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500';
const inp = 'w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500';

function FeitKaart({ f, onStatus, onDelete, onEdit }) {
  const [edit, setEdit] = useState(false);
  const [wat, setWat] = useState(f.lagen.wat);
  const [waarom, setWaarom] = useState(f.lagen.waarom || '');
  const k = KIND[f.kind] || KIND.feit;
  return (
    <div data-testid={`feit-kaart-${f.id}`} className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2" style={{ borderLeft: `3px solid ${k.kleur}` }}>
      <div className="flex items-start gap-2 flex-wrap">
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: k.kleur + '22', color: k.kleur }}>{k.label}</span>
        <span className="text-[10px] px-2 py-0.5 rounded-full border border-slate-700" style={{ color: STATUS[f.status] }}>{f.status}</span>
        <span className="text-[10px] text-slate-500">{f.user_id || 'Spark'} · {f.keer_gehoord || 1}× · vertrouwen {Math.round((f.vertrouwen || 0) * 100)}%</span>
        <span className="ml-auto text-[10px] text-slate-600">{(f.updated_at || '').slice(0, 10)}</span>
      </div>
      <h4 className="text-sm font-semibold text-white">{f.begrip}</h4>
      {edit ? (
        <div className="space-y-1.5">
          <input data-testid={`feit-edit-wat-${f.id}`} value={wat} onChange={e => setWat(e.target.value)} className={inp} placeholder="Wat" />
          <input data-testid={`feit-edit-waarom-${f.id}`} value={waarom} onChange={e => setWaarom(e.target.value)} className={inp} placeholder="Waarom (optioneel)" />
          <div className="flex gap-2">
            <button data-testid={`feit-edit-save-${f.id}`} onClick={() => { onEdit(f, { wat, waarom }); setEdit(false); }} className="text-[11px] px-2 py-1 rounded bg-amber-500 text-slate-950 font-semibold">Opslaan</button>
            <button onClick={() => setEdit(false)} className="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-300">Annuleer</button>
          </div>
        </div>
      ) : (
        <>
          <p className="text-xs text-slate-200"><span className="text-slate-500">wat · </span>{f.lagen.wat}</p>
          {f.lagen.waarom && <p className="text-xs text-slate-300"><span className="text-slate-500">waarom · </span>{f.lagen.waarom}</p>}
          {f.lagen.context && <p className="text-[11px] text-slate-500 italic">"{f.lagen.context}"</p>}
        </>
      )}
      <div className="flex flex-wrap gap-1">{(f.tags || []).map(t => <span key={t} className="text-[10px] text-slate-500">#{t}</span>)}</div>
      <div className="flex items-center gap-1.5 pt-1 border-t border-slate-800/60">
        <span className="text-[10px] text-slate-600 mr-auto">bron: {f.bron?.type}</span>
        {f.kind === 'feit' && f.status !== 'getoetst' && <button data-testid={`feit-getoetst-${f.id}`} onClick={() => onStatus(f, 'getoetst')} className="text-[11px] px-2 py-1 rounded bg-emerald-500/15 text-emerald-300 flex items-center gap-1"><Check className="w-3 h-3" /> getoetst</button>}
        {f.status !== 'verworpen' && <button data-testid={`feit-verworpen-${f.id}`} onClick={() => onStatus(f, 'verworpen')} className="text-[11px] px-2 py-1 rounded bg-red-500/10 text-red-300 flex items-center gap-1"><X className="w-3 h-3" /> verwerp</button>}
        {f.status === 'verworpen' && <button onClick={() => onStatus(f, f.kind === 'feit' ? 'ongetoetst' : 'bevestigd')} className="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-300">herstel</button>}
        <button data-testid={`feit-edit-${f.id}`} onClick={() => setEdit(true)} className="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-300">bewerk</button>
        <button data-testid={`feit-delete-${f.id}`} onClick={() => onDelete(f)} className="text-[11px] px-2 py-1 rounded bg-slate-800 text-slate-400"><Trash2 className="w-3 h-3" /></button>
      </div>
    </div>
  );
}

export function FeitenTab() {
  const { user } = useAuth();
  const [data, setData] = useState({ feiten: [], users: [] });
  const [stats, setStats] = useState(null);
  const [scope, setScope] = useState('user');
  const [userId, setUserId] = useState('');
  const [kind, setKind] = useState('');
  const [status, setStatus] = useState('');
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(false);
  const [nieuw, setNieuw] = useState(null);

  const load = useCallback(async () => {
    setBusy(true);
    const p = new URLSearchParams({ viewer_id: user?.id, scope });
    if (userId) p.set('user_id', userId); if (kind) p.set('kind', kind); if (status) p.set('status', status); if (q) p.set('q', q);
    try {
      const [r, s] = await Promise.all([
        fetch(`${API}/api/feiten?${p}`).then(x => x.json()),
        fetch(`${API}/api/feiten/stats?viewer_id=${user?.id}`).then(x => x.json()),
      ]);
      if (r.success) setData(r); else toast.error(apiError(r));
      if (s.success) setStats(s);
    } catch { toast.error('Laden mislukt'); }
    setBusy(false);
  }, [user?.id, scope, userId, kind, status, q]);

  useEffect(() => { load(); }, [load]);

  const onStatus = async (f, st) => {
    const r = await fetch(`${API}/api/feiten/${f.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ viewer_id: user?.id, scope: f.scope, user_id: f.user_id, status: st }) }).then(x => x.json());
    if (r.success) { toast.success(`→ ${st}`); load(); } else toast.error(apiError(r));
  };
  const onEdit = async (f, upd) => {
    const r = await fetch(`${API}/api/feiten/${f.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ viewer_id: user?.id, scope: f.scope, user_id: f.user_id, ...upd }) }).then(x => x.json());
    if (r.success) { toast.success('Opgeslagen'); load(); } else toast.error(apiError(r));
  };
  const onDelete = async (f) => {
    if (!window.confirm(`"${f.begrip}: ${f.lagen.wat}" verwijderen?`)) return;
    const p = new URLSearchParams({ viewer_id: user?.id, scope: f.scope }); if (f.user_id) p.set('user_id', f.user_id);
    const r = await fetch(`${API}/api/feiten/${f.id}?${p}`, { method: 'DELETE' }).then(x => x.json());
    if (r.success) { toast.success('Verwijderd'); load(); } else toast.error(apiError(r));
  };
  const migreer = async () => {
    const r = await fetch(`${API}/api/feiten/migreer`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ viewer_id: user?.id }) }).then(x => x.json());
    if (r.success) { toast.success(`Migratie: ${r.stats.nieuw} nieuwe kaarten uit ${r.stats.users} users`); load(); } else toast.error(apiError(r));
  };
  const maak = async () => {
    const r = await fetch(`${API}/api/feiten`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ viewer_id: user?.id, ...nieuw, user_id: nieuw.scope === 'user' ? nieuw.user_id : null }) }).then(x => x.json());
    if (r.success) { toast.success('Kaart aangemaakt'); setNieuw(null); load(); } else toast.error(apiError(r));
  };

  return (
    <div data-testid="feiten-tab" className="space-y-4">
      <div className="flex flex-wrap items-start gap-3">
        <div className="flex-1 min-w-[16rem]">
          <h3 className="text-base md:text-lg font-bold text-white flex items-center gap-2"><BookOpen className="w-4 h-4 text-amber-400" /> Feiten-archief</h3>
          <p className="text-xs text-slate-400">Wat Spark uit gesprekken leert, als kaart. Alleen voor beheer — "soms willen mensen dingen niet weten over zichzelf". Feiten en meningen winnen in de chat van de LLM.</p>
        </div>
        <button data-testid="feiten-migreer-btn" onClick={migreer} className="text-xs px-3 py-2 rounded-lg bg-slate-800 text-slate-200 flex items-center gap-1.5"><RefreshCw className="w-3.5 h-3.5" /> Oude identity-facts inlezen</button>
        <button data-testid="feiten-nieuw-btn" onClick={() => setNieuw({ scope: 'spark', kind: 'feit', begrip: '', wat: '', waarom: '', user_id: userId })} className="text-xs px-3 py-2 rounded-lg text-slate-950 font-semibold flex items-center gap-1.5" style={{ background: '#f59e0b' }}><Plus className="w-3.5 h-3.5" /> Handmatig</button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2 text-center">
          {[['Totaal', stats.totaal, '#e2e8f0'], ['Spark', stats.spark, '#e2e8f0'], ...Object.entries(KIND).map(([k, v]) => [v.label, stats.tellers[k] || 0, v.kleur]), ['Ongetoetst', stats.tellers.ongetoetst, '#94a3b8'], ['Getoetst', stats.tellers.getoetst, '#22c55e']].map(([l, v, c]) => (
            <div key={l} data-testid={`feiten-teller-${l.toLowerCase()}`} className="bg-slate-900 border border-slate-800 rounded-lg py-2"><p className="text-[10px] text-slate-500 uppercase">{l}</p><p className="text-lg font-bold" style={{ color: c }}>{v}</p></div>
          ))}
        </div>
      )}

      {nieuw && (
        <div data-testid="feiten-nieuw-form" className="bg-slate-900 border border-amber-500/40 rounded-xl p-4 grid grid-cols-1 md:grid-cols-6 gap-2">
          <select value={nieuw.scope} onChange={e => setNieuw({ ...nieuw, scope: e.target.value })} className={inp}><option value="spark">Spark (algemeen)</option><option value="user">Gebruiker</option></select>
          {nieuw.scope === 'user' && <select data-testid="feiten-nieuw-user" value={nieuw.user_id} onChange={e => setNieuw({ ...nieuw, user_id: e.target.value })} className={inp}><option value="">— user —</option>{data.users.map(u => <option key={u} value={u}>{u}</option>)}</select>}
          <select value={nieuw.kind} onChange={e => setNieuw({ ...nieuw, kind: e.target.value })} className={inp}>{Object.entries(KIND).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</select>
          <input data-testid="feiten-nieuw-begrip" value={nieuw.begrip} onChange={e => setNieuw({ ...nieuw, begrip: e.target.value })} className={inp} placeholder="Begrip" />
          <input data-testid="feiten-nieuw-wat" value={nieuw.wat} onChange={e => setNieuw({ ...nieuw, wat: e.target.value })} className={inp + ' md:col-span-2'} placeholder="Wat" />
          <div className="md:col-span-6 flex gap-2"><button data-testid="feiten-nieuw-save" onClick={maak} disabled={!nieuw.begrip || !nieuw.wat} className="text-xs px-3 py-1.5 rounded bg-amber-500 text-slate-950 font-semibold disabled:opacity-40">Aanmaken</button><button onClick={() => setNieuw(null)} className="text-xs px-3 py-1.5 rounded bg-slate-800 text-slate-300">Annuleer</button></div>
        </div>
      )}

      <div className="flex flex-wrap gap-2 items-center">
        <select data-testid="feiten-filter-scope" value={scope} onChange={e => setScope(e.target.value)} className={sel}><option value="user">Gebruikers</option><option value="spark">Spark (algemeen)</option></select>
        {scope === 'user' && <select data-testid="feiten-filter-user" value={userId} onChange={e => setUserId(e.target.value)} className={sel}><option value="">alle users</option>{data.users.map(u => <option key={u} value={u}>{u}{stats?.per_user?.[u] != null ? ` (${stats.per_user[u]})` : ''}</option>)}</select>}
        <select data-testid="feiten-filter-kind" value={kind} onChange={e => setKind(e.target.value)} className={sel}><option value="">alle soorten</option>{Object.entries(KIND).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}</select>
        <select data-testid="feiten-filter-status" value={status} onChange={e => setStatus(e.target.value)} className={sel}><option value="">alle statussen</option>{Object.keys(STATUS).map(s => <option key={s} value={s}>{s}</option>)}</select>
        <input data-testid="feiten-zoek" value={q} onChange={e => setQ(e.target.value)} placeholder="zoek…" className={sel + ' w-40'} />
        <span className="text-[11px] text-slate-500 flex items-center gap-1">{busy && <Loader2 className="w-3 h-3 animate-spin" />}{data.total ?? 0} kaarten</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {data.feiten.map(f => <FeitKaart key={f.id} f={f} onStatus={onStatus} onDelete={onDelete} onEdit={onEdit} />)}
        {!busy && data.feiten.length === 0 && <p className="text-xs text-slate-500">Nog geen kaarten voor deze selectie.</p>}
      </div>
    </div>
  );
}
