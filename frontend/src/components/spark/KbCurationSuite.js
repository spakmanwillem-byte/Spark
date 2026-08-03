/**
 * v12_kb_curation_suite_001 — KB-Curatie Suite UI (Sessie 55)
 *
 * Drie sub-tabs in één component:
 * 1. 5W-Filler: LLM-voorstel per lege kaart → review → accept
 * 2. Duplicaten: 32 paren begrip → kies keeper → merge
 * 3. Lade-check: Regel 1/2 uit blauwdruk → verplaats voorstel → accept
 *
 * Verankerd aan blauwdruk: spark_tag_curatie_public.json § 8_lade_toewijzing_regels
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Sparkles, Copy, ArrowRightLeft, Loader2, Check, X, RefreshCw, BookOpen } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function KbCurationSuite({ userId }) {
  const [activeTab, setActiveTab] = useState('summary');
  const [summary, setSummary] = useState(null);

  const loadSummary = useCallback(async () => {
    const r = await fetch(`${API}/api/kb/v2/curation/summary`).then(x => x.json());
    if (r.success) setSummary(r);
  }, []);

  useEffect(() => { loadSummary(); }, [loadSummary]);

  const tabs = [
    { id: 'summary', label: 'Overzicht', icon: BookOpen, count: null },
    { id: 'empty5w', label: '5W-Filler', icon: Sparkles, count: summary?.empty_5w },
    { id: 'dupes', label: 'Duplicaten', icon: Copy, count: summary?.duplicates },
    { id: 'lade', label: 'Lade-check', icon: ArrowRightLeft, count: summary?.lade_misplaced },
  ];

  return (
    <div data-testid="kb-curation-suite" className="space-y-4">
      <div className="flex items-center gap-2 flex-wrap">
        {tabs.map(t => {
          const Icon = t.icon;
          const active = activeTab === t.id;
          return (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              data-testid={`kb-curation-tab-${t.id}`}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                active
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-emerald-500/30'
              }`}>
              <Icon className="w-3.5 h-3.5" />
              {t.label}
              {t.count !== null && t.count !== undefined && (
                <span className="ml-1 px-1.5 py-0.5 text-[10px] rounded bg-slate-900/60 border border-slate-700">
                  {t.count}
                </span>
              )}
            </button>
          );
        })}
        <button onClick={loadSummary}
          data-testid="kb-curation-refresh"
          className="ml-auto p-1.5 rounded border border-slate-700 text-slate-400 hover:text-emerald-300"
          title="Herlaad">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {activeTab === 'summary' && <SummaryPanel summary={summary} />}
      {activeTab === 'empty5w' && <Empty5WPanel userId={userId} onChange={loadSummary} />}
      {activeTab === 'dupes' && <DuplicatesPanel userId={userId} onChange={loadSummary} />}
      {activeTab === 'lade' && <LadeCheckPanel userId={userId} onChange={loadSummary} />}
    </div>
  );
}

function SummaryPanel({ summary }) {
  if (!summary) return <div className="text-xs text-slate-500">Laden...</div>;
  const stat = (label, value, color) => (
    <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
      <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className="text-xl font-bold" style={{ color }}>{value}</p>
    </div>
  );
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {stat('Lege 5W kaarten', summary.empty_5w, '#f59e0b')}
        {stat('Deels 5W', summary.partial_5w, '#eab308')}
        {stat('Dubbele begrippen', summary.duplicates, '#a855f7')}
        {stat('Lade-verkeerd', summary.lade_misplaced, '#ef4444')}
      </div>
      <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3 text-[11px] text-slate-400">
        <p className="text-emerald-300 font-medium mb-1">Blauwdruk-gestuurde curatie</p>
        <p>Alle voorstellen leunen op de regels in <code className="text-cyan-300">{summary.blauwdruk_ref}</code>. Lade-verplaatsingen volgen Regel 1 (werkwoord meervoud → doen) en Regel 2 (proces-zn → doen). Alle acties zijn read-only tot je op Accept klikt.</p>
      </div>
    </div>
  );
}

// ============================================================
// 5W-Filler
// ============================================================
function Empty5WPanel({ userId, onChange }) {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [proposal, setProposal] = useState(null);
  const [busyCard, setBusyCard] = useState(null);
  const [onlyFullyEmpty, setOnlyFullyEmpty] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const r = await fetch(`${API}/api/kb/v2/curation/empty-5w?limit=50&only_fully_empty=${onlyFullyEmpty}`).then(x => x.json());
    setCards(r.cards || []);
    setLoading(false);
  }, [onlyFullyEmpty]);

  useEffect(() => { load(); }, [load]);

  const suggest = async (card) => {
    setBusyCard(card.id);
    setProposal(null);
    try {
      const r = await fetch(`${API}/api/kb/v2/curation/5w-suggest/${card.id}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewer_id: userId }),
      }).then(x => x.json());
      if (r.success) { setProposal(r); setExpanded(card.id); }
      else alert('LLM-call mislukt: ' + (r.detail || 'onbekende fout'));
    } finally { setBusyCard(null); }
  };

  const apply = async (cardId, ws5) => {
    setBusyCard(cardId);
    const r = await fetch(`${API}/api/kb/v2/curation/5w-apply/${cardId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ viewer_id: userId, ws5 }),
    }).then(x => x.json());
    if (r.success) {
      setExpanded(null); setProposal(null);
      await load(); onChange && onChange();
    } else alert('Opslaan mislukt');
    setBusyCard(null);
  };

  if (loading) return <div className="text-xs text-slate-500">Laden...</div>;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-[11px]">
        <label className="flex items-center gap-1.5 text-slate-400 cursor-pointer">
          <input type="checkbox" checked={onlyFullyEmpty} onChange={e => setOnlyFullyEmpty(e.target.checked)} />
          Alleen volledig lege 5W tonen
        </label>
        <span className="text-slate-600">·</span>
        <span className="text-slate-500">{cards.length} kaart{cards.length === 1 ? '' : 'en'}</span>
      </div>
      {cards.map(c => (
        <div key={c.id} data-testid={`empty5w-row-${c.id}`}
          className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="min-w-0 flex-1">
              <p className="text-sm text-white font-medium">
                {c.begrip} <span className="text-[10px] text-slate-500">· {c.lade} · {c.filled_count}/6 ingevuld</span>
              </p>
              <p className="text-[11px] text-slate-500 truncate">{c.laag1}</p>
            </div>
            <button onClick={() => suggest(c)} disabled={busyCard === c.id}
              data-testid={`empty5w-suggest-${c.id}`}
              className="flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-medium bg-emerald-500 hover:bg-emerald-600 text-white disabled:opacity-50">
              {busyCard === c.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
              LLM vullen
            </button>
          </div>
          {expanded === c.id && proposal && proposal.card_id === c.id && (
            <ProposalReview proposal={proposal} onApply={ws5 => apply(c.id, ws5)}
              onCancel={() => { setExpanded(null); setProposal(null); }} busy={busyCard === c.id} />
          )}
        </div>
      ))}
      {cards.length === 0 && (
        <p className="text-xs text-slate-500 text-center py-4">Geen kaarten meer met leeg 5W ✓</p>
      )}
    </div>
  );
}

function ProposalReview({ proposal, onApply, onCancel, busy }) {
  const [ws5, setWs5] = useState(proposal.proposal || {});
  const fields = ['wie', 'wat', 'wanneer', 'waar', 'waarom', 'hoe'];
  return (
    <div className="mt-3 pt-3 border-t border-slate-800/60 space-y-2">
      <p className="text-[10px] text-emerald-400 uppercase tracking-wider">
        LLM-voorstel · {proposal.llm_provider || 'llm'} · bewerkbaar
      </p>
      {fields.map(f => (
        <div key={f} className="flex items-start gap-2">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider w-14 pt-1.5">{f}</span>
          <textarea data-testid={`5w-input-${f}`}
            value={ws5[f] || ''} onChange={e => setWs5(prev => ({ ...prev, [f]: e.target.value }))}
            rows={1}
            className="flex-1 px-2 py-1 text-[12px] bg-slate-800 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-emerald-500 resize-y" />
        </div>
      ))}
      <div className="flex items-center justify-end gap-2 pt-1">
        <button onClick={onCancel}
          data-testid="5w-cancel"
          className="px-3 py-1 rounded text-[11px] border border-slate-700 text-slate-400 hover:text-white">
          Annuleer
        </button>
        <button onClick={() => onApply(ws5)} disabled={busy}
          data-testid="5w-accept"
          className="flex items-center gap-1 px-3 py-1 rounded text-[11px] font-medium bg-emerald-500 hover:bg-emerald-600 text-white disabled:opacity-50">
          <Check className="w-3 h-3" /> Accept
        </button>
      </div>
    </div>
  );
}

// ============================================================
// Duplicaten
// ============================================================
function DuplicatesPanel({ userId, onChange }) {
  const [dupes, setDupes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    const r = await fetch(`${API}/api/kb/v2/curation/duplicates`).then(x => x.json());
    setDupes(r.duplicates || []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const merge = async (keep, drop, begrip) => {
    if (!window.confirm(`Merge "${begrip}"?\n\nKEEP: ${keep}\nDROP: ${drop}\n\nTags + 5W-gaten worden overgezet naar de keeper. Drop wordt verwijderd.`)) return;
    setBusy(drop);
    const r = await fetch(`${API}/api/kb/v2/curation/duplicate-merge`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ viewer_id: userId, keep_card_id: keep, drop_card_id: drop }),
    }).then(x => x.json());
    if (r.success) { await load(); onChange && onChange(); }
    else alert('Merge mislukt: ' + (r.detail || 'onbekende fout'));
    setBusy(null);
  };

  if (loading) return <div className="text-xs text-slate-500">Laden...</div>;

  return (
    <div className="space-y-2">
      <p className="text-[11px] text-slate-500">{dupes.length} dubbele begrippen — kies keeper, drop verdwijnt (tags/5W mergen naar keeper).</p>
      {dupes.map(d => (
        <div key={d.begrip} data-testid={`dupe-row-${d.begrip}`}
          className={`bg-slate-900/60 border rounded-lg p-3 ${d.same_lade ? 'border-red-500/40' : 'border-slate-800'}`}>
          <div className="flex items-center gap-2 mb-2">
            <code className="text-sm text-purple-300">{d.begrip}</code>
            <span className="text-[10px] text-slate-500">{d.count}×</span>
            {d.same_lade && (
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/40">
                ⚠ zelfde lade
              </span>
            )}
          </div>
          <div className="space-y-1.5">
            {d.cards.map((card, i) => (
              <div key={card.id} className="flex items-center gap-2 text-[11px]">
                <span className="text-slate-500">#{i + 1}</span>
                <span className="text-slate-400">{card.lade}</span>
                <span className="text-slate-500">· {card.filled_5w}/6 5W · {card.tags_count} tags · {card.n_verbanden} verbanden</span>
                <span className="text-slate-600 truncate flex-1">{card.laag1}</span>
                <button data-testid={`dupe-keep-${card.id}`}
                  onClick={() => {
                    const drop = d.cards.find(x => x.id !== card.id);
                    if (drop) merge(card.id, drop.id, d.begrip);
                  }}
                  disabled={busy === card.id}
                  className="px-2 py-0.5 rounded text-[10px] font-medium bg-purple-500/20 hover:bg-purple-500/40 text-purple-300 border border-purple-500/40 disabled:opacity-50">
                  Keep deze
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
      {dupes.length === 0 && <p className="text-xs text-slate-500 text-center py-4">Geen duplicaten meer ✓</p>}
    </div>
  );
}

// ============================================================
// Lade-check (Regel 1 + 2)
// ============================================================
function LadeCheckPanel({ userId, onChange }) {
  const [proposals, setProposals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);
  const [skipped, setSkipped] = useState(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    const r = await fetch(`${API}/api/kb/v2/curation/lade-check?limit=200`).then(x => x.json());
    setProposals(r.proposals || []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const skip = (id) => setSkipped(s => new Set([...s, id]));

  const accept = async (p) => {
    setBusy(p.id);
    const r = await fetch(`${API}/api/kb/v2/curation/lade-move/${p.id}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ viewer_id: userId, target_lade: p.target_lade }),
    }).then(x => x.json());
    if (r.success) { await load(); setSkipped(new Set()); onChange && onChange(); }
    else alert('Verplaatsen mislukt: ' + (r.detail || 'onbekende fout'));
    setBusy(null);
  };

  if (loading) return <div className="text-xs text-slate-500">Laden...</div>;
  const visible = proposals.filter(p => !skipped.has(p.id));

  return (
    <div className="space-y-2">
      <p className="text-[11px] text-slate-500">
        {visible.length} voorstellen ({skipped.size} overgeslagen) — regel-based scan, niet alles klopt. Skip zn-meervoud die géén werkwoord is.
      </p>
      {visible.map(p => (
        <div key={p.id} data-testid={`lade-row-${p.id}`}
          className="bg-slate-900/60 border border-slate-800 rounded-lg p-3">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <code className="text-sm text-red-300">{p.begrip}</code>
                <span className="text-[10px] text-slate-500">{p.current_lade} → doen</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {p.rule === 'regel_1' ? 'R1' : 'R2'}
                </span>
              </div>
              <p className="text-[10px] text-slate-500 mt-0.5">{p.reason}</p>
              <p className="text-[11px] text-slate-500 truncate mt-1">{p.laag1_snippet}</p>
            </div>
            <div className="flex gap-1">
              <button onClick={() => skip(p.id)} disabled={busy === p.id}
                data-testid={`lade-skip-${p.id}`}
                className="flex items-center gap-1 px-2 py-1 rounded text-[11px] border border-slate-700 text-slate-400 hover:text-white disabled:opacity-50">
                <X className="w-3 h-3" /> Skip
              </button>
              <button onClick={() => accept(p)} disabled={busy === p.id}
                data-testid={`lade-accept-${p.id}`}
                className="flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-medium bg-red-500 hover:bg-red-600 text-white disabled:opacity-50">
                {busy === p.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                Verplaats
              </button>
            </div>
          </div>
        </div>
      ))}
      {visible.length === 0 && <p className="text-xs text-slate-500 text-center py-4">Alles verwerkt ✓</p>}
    </div>
  );
}

export default KbCurationSuite;
