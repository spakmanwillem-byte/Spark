/**
 * v13d_clienten_module_001 (sessie 56b) — Willem: "clienten index formulier +
 * dossier. Basis personalia. Spark kan later info wegzetten."
 *
 * MVP: index-lijst + create-form + detail-panel met dossier/spark-learnings.
 */
import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { Briefcase, Plus, Trash2, Edit3, Mail, Phone, MapPin, Euro, Sparkles, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

const EMPTY = {
  naam: '', contactpersoon: '', email: '', telefoon: '',
  adres: '', postcode: '', plaats: '',
  kvk: '', btw_nummer: '', uurtarief: '', notities: '', scope: 'zakelijk',
};

export function ClientenPage({ onNavigate }) {
  const { user } = useAuth();
  const uid = user?.id || 'user-001';
  const [clienten, setClienten] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [selected, setSelected] = useState(null);
  const [dossierKop, setDossierKop] = useState('');
  const [dossierInhoud, setDossierInhoud] = useState('');

  const load = () => {
    setLoading(true);
    fetch(`${API}/api/clienten/list/${uid}?viewer_id=${uid}`)
      .then(r => r.json())
      .then(d => { setClienten(d.clienten || []); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [uid]);

  const create = async () => {
    if (!form.naam.trim()) return;
    const body = { ...form, uurtarief: form.uurtarief ? Number(form.uurtarief) : null };
    const r = await fetch(`${API}/api/clienten/create/${uid}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const d = await r.json();
    if (d.success) { setForm(EMPTY); setShowNew(false); load(); }
  };

  const remove = async (c) => {
    if (!window.confirm(`Client "${c.naam}" verwijderen?`)) return;
    await fetch(`${API}/api/clienten/delete/${uid}/${c.id}`, { method: 'DELETE' });
    if (selected?.id === c.id) setSelected(null);
    load();
  };

  const openDetail = async (c) => {
    const r = await fetch(`${API}/api/clienten/detail/${uid}/${c.id}?viewer_id=${uid}`).then(x => x.json());
    setSelected(r);
  };

  const addDossierEntry = async () => {
    if (!dossierKop.trim() || !selected) return;
    await fetch(`${API}/api/clienten/dossier/${uid}/${selected.id}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kop: dossierKop, inhoud: dossierInhoud, bron: 'handmatig' }),
    });
    setDossierKop(''); setDossierInhoud('');
    openDetail(selected);
  };

  return (
    <MainLayout activePage="clienten" onNavigate={onNavigate}>
      <div data-testid="clienten-page" className="h-full flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'var(--glow-base)' }}>
              <Briefcase className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Clienten</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">
                {clienten.length} client{clienten.length !== 1 ? 'en' : ''} · opdrachtgevers & dossiers
              </p>
            </div>
            <button data-testid="add-client-btn" onClick={() => setShowNew(!showNew)}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white"
              style={{ background: 'var(--glow-base)' }}>
              <Plus className="w-3.5 h-3.5" /> Nieuw
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-4">

            {/* Kolom links: lijst + formulier */}
            <div className="space-y-4">
              {showNew && (
                <div className="p-4 bg-slate-900/60 rounded-xl space-y-2"
                  style={{ borderWidth: '1px', borderStyle: 'solid', borderColor: 'color-mix(in srgb, var(--glow-base) 20%, transparent)' }}>
                  <input data-testid="client-naam" type="text" value={form.naam} onChange={e => setForm({ ...form, naam: e.target.value })}
                    placeholder="Bedrijfsnaam / naam..." className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none" />
                  <div className="grid grid-cols-2 gap-2">
                    <input type="text" value={form.contactpersoon} onChange={e => setForm({ ...form, contactpersoon: e.target.value })}
                      placeholder="Contactpersoon..." className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                    <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })}
                      placeholder="Email..." className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                    <input type="text" value={form.telefoon} onChange={e => setForm({ ...form, telefoon: e.target.value })}
                      placeholder="Telefoon..." className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                    <input type="number" step="0.5" value={form.uurtarief} onChange={e => setForm({ ...form, uurtarief: e.target.value })}
                      placeholder="Uurtarief €..." className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                  </div>
                  <input type="text" value={form.adres} onChange={e => setForm({ ...form, adres: e.target.value })}
                    placeholder="Adres..." className="w-full px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                  <div className="grid grid-cols-2 gap-2">
                    <input type="text" value={form.postcode} onChange={e => setForm({ ...form, postcode: e.target.value })}
                      placeholder="Postcode..." className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                    <input type="text" value={form.plaats} onChange={e => setForm({ ...form, plaats: e.target.value })}
                      placeholder="Plaats..." className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                    <input type="text" value={form.kvk} onChange={e => setForm({ ...form, kvk: e.target.value })}
                      placeholder="KVK..." className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                    <input type="text" value={form.btw_nummer} onChange={e => setForm({ ...form, btw_nummer: e.target.value })}
                      placeholder="BTW-nummer..." className="px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                  </div>
                  <textarea value={form.notities} onChange={e => setForm({ ...form, notities: e.target.value })}
                    placeholder="Notities..." rows={2}
                    className="w-full px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none resize-none" />
                  <button data-testid="save-client-btn" onClick={create}
                    className="w-full px-4 py-1.5 rounded-lg text-xs font-medium text-white" style={{ background: 'var(--glow-base)' }}>Opslaan</button>
                </div>
              )}

              <div className="space-y-1.5">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Index</p>
                {loading ? (
                  <p className="text-xs text-slate-500 italic">Laden...</p>
                ) : clienten.length === 0 ? (
                  <div className="py-8 text-center border border-dashed border-slate-800 rounded-xl">
                    <Briefcase className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                    <p className="text-sm text-slate-500">Nog geen clienten. Klik + Nieuw om te beginnen.</p>
                  </div>
                ) : clienten.map(c => (
                  <div key={c.id} data-testid={`client-row-${c.id}`}
                    className={`flex items-center gap-2 p-2.5 rounded-lg transition-colors cursor-pointer ${selected?.id === c.id ? 'bg-slate-800/50' : 'bg-slate-900/40 hover:bg-slate-900/60'}`}
                    style={{ borderWidth: '1px', borderStyle: 'solid', borderColor: selected?.id === c.id ? 'color-mix(in srgb, var(--glow-base) 40%, transparent)' : 'rgba(30,41,59,1)' }}
                    onClick={() => openDetail(c)}>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white font-medium truncate">{c.naam}</p>
                      <p className="text-[10px] text-slate-500 truncate">
                        {c.contactpersoon ? c.contactpersoon + ' · ' : ''}
                        {c.uurtarief ? `€${c.uurtarief}/u` : 'geen tarief'}
                      </p>
                    </div>
                    <button onClick={(e) => { e.stopPropagation(); remove(c); }}
                      className="p-1 text-slate-600 hover:text-red-400"
                      style={{ transition: 'color 0.15s' }}
                      onMouseEnter={e => e.currentTarget.style.color = 'var(--alert-base)'}
                      onMouseLeave={e => e.currentTarget.style.color = ''}>
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Kolom rechts: detail */}
            <div className="space-y-3">
              {!selected ? (
                <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl">
                  <Edit3 className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">Klik een client om details en dossier te zien.</p>
                </div>
              ) : (
                <>
                  <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-800">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h2 className="text-base font-bold text-white">{selected.naam}</h2>
                        {selected.contactpersoon && <p className="text-xs text-slate-400">{selected.contactpersoon}</p>}
                      </div>
                      <button onClick={() => setSelected(null)} className="p-1 text-slate-500 hover:text-white"><X className="w-3.5 h-3.5" /></button>
                    </div>
                    <div className="mt-3 space-y-1 text-xs text-slate-300">
                      {selected.email && <div className="flex items-center gap-1.5"><Mail className="w-3 h-3 text-slate-500" /> {selected.email}</div>}
                      {selected.telefoon && <div className="flex items-center gap-1.5"><Phone className="w-3 h-3 text-slate-500" /> {selected.telefoon}</div>}
                      {(selected.adres || selected.plaats) && (
                        <div className="flex items-center gap-1.5"><MapPin className="w-3 h-3 text-slate-500" /> {[selected.adres, selected.postcode, selected.plaats].filter(Boolean).join(' · ')}</div>
                      )}
                      {selected.uurtarief != null && <div className="flex items-center gap-1.5"><Euro className="w-3 h-3 text-slate-500" /> €{selected.uurtarief}/uur</div>}
                      {selected.kvk && <div className="text-[10px] text-slate-500">KVK {selected.kvk} · BTW {selected.btw_nummer || '-'}</div>}
                    </div>
                    {selected.notities && <p className="text-xs text-slate-400 mt-2 whitespace-pre-wrap">{selected.notities}</p>}
                  </div>

                  {/* Dossier */}
                  <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-800">
                    <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                      <Edit3 className="w-3.5 h-3.5" style={{ color: 'var(--app-secondary, #06b6d4)' }} /> Dossier
                      <span className="text-[10px] text-slate-500">({(selected.dossier || []).length})</span>
                    </h3>
                    <div className="space-y-2 mb-3 max-h-48 overflow-y-auto">
                      {(selected.dossier || []).length === 0 && <p className="text-[11px] text-slate-500 italic">Nog geen dossier-entries.</p>}
                      {(selected.dossier || []).map(e => (
                        <div key={e.id} className="p-2 bg-slate-950/50 rounded border border-slate-800">
                          <p className="text-xs font-medium text-white">{e.kop}</p>
                          {e.inhoud && <p className="text-[11px] text-slate-400 whitespace-pre-wrap mt-0.5">{e.inhoud}</p>}
                          <p className="text-[9px] text-slate-600 mt-1">{(e.aangemaakt_op || '').slice(0, 10)} · bron: {e.bron}</p>
                        </div>
                      ))}
                    </div>
                    <input value={dossierKop} onChange={e => setDossierKop(e.target.value)} placeholder="Kop..."
                      className="w-full px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded text-xs text-white placeholder-slate-500 focus:outline-none mb-1.5" />
                    <textarea value={dossierInhoud} onChange={e => setDossierInhoud(e.target.value)} placeholder="Inhoud..." rows={2}
                      className="w-full px-2 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded text-xs text-white placeholder-slate-500 focus:outline-none resize-none mb-1.5" />
                    <button onClick={addDossierEntry} disabled={!dossierKop.trim()}
                      className="px-3 py-1 rounded text-[11px] font-medium text-white disabled:opacity-40"
                      style={{ background: 'var(--app-secondary, #06b6d4)' }}>+ Entry</button>
                  </div>

                  {/* Spark leerpunten */}
                  {(selected.spark_learnings || []).length > 0 && (
                    <div className="p-4 bg-slate-900/50 rounded-xl border border-slate-800">
                      <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                        <Sparkles className="w-3.5 h-3.5" style={{ color: 'var(--glow-base)' }} />
                        Spark-leerpunten <span className="text-[10px] text-slate-500">({selected.spark_learnings.length})</span>
                      </h3>
                      <div className="space-y-1 max-h-40 overflow-y-auto">
                        {selected.spark_learnings.map(l => (
                          <div key={l.id} className="p-2 bg-slate-950/50 rounded border border-slate-800">
                            <p className="text-[11px] text-slate-300">{l.inhoud}</p>
                            <p className="text-[9px] text-slate-600 mt-0.5">{(l.aangemaakt_op || '').slice(0, 10)} · bron: {l.bron}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default ClientenPage;
