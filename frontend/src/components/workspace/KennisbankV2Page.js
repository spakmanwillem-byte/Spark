import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Inbox, BookOpen, Search, Save, X, AlertTriangle,
  ChevronRight, RefreshCw, Eye, Edit3, ArrowRightLeft,
  Mic, Square, Image as ImageIcon, Upload, Trash2, CheckCircle2, Plus
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const LADES = [
  { id: 'voelen',   icon: '🌸', naam: 'Voelen',      stroom: 'Emotie & Verbinding', color: '#ec4899' },
  { id: 'spreken',  icon: '💬', naam: 'Spreken',     stroom: 'Communicatie & Taal', color: '#06b6d4' },
  { id: 'weten',    icon: '🧠', naam: 'Weten',       stroom: 'Systeem & Kennis',    color: '#f59e0b' },
  { id: 'doen',     icon: '🎭', naam: 'Doen',        stroom: 'Gedrag & Actie',      color: '#a855f7' },
];

const REASON_LABEL = {
  tag_tie:        { label: 'Tag-tie',       color: '#f59e0b' },
  no_match:       { label: 'Geen match',     color: '#94a3b8' },
  missing_laag1:  { label: 'Geen laag 1',    color: '#ef4444' },
};

/**
 * Kennisbank v2 — 4 Lades + Inbox
 * --------------------------------
 *   Tabs: Inbox · Voelen · Spreken · Weten · Doen
 *   • Inbox-kaart: 4 lade-knoppen + edit-form voor lagen/ws5/tags
 *   • Lade-kaarten: zoeken + paged lijst + edit
 *   • #DeWillem-principe in audit-panel zichtbaar
 */
export function KennisbankV2Page({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('inbox');     // 'inbox' | lade-id
  const [stats, setStats] = useState(null);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [reasons, setReasons] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [reasonFilter, setReasonFilter] = useState('');
  const [page, setPage] = useState(0);
  const [selectedCard, setSelectedCard] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState(null);
  const [savingClassify, setSavingClassify] = useState(false);
  const [showAudit, setShowAudit] = useState(false);
  const [auditData, setAuditData] = useState(null);

  const PAGE = 25;

  // Load stats
  const loadStats = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/kb/v2/stats`).then(x => x.json());
      setStats(r);
    } catch {}
  }, []);

  // Load list (inbox or lade)
  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams({ limit: String(PAGE), offset: String(page * PAGE) });
      if (search) qs.append('search', search);
      let url;
      if (activeTab === 'inbox') {
        if (reasonFilter) qs.append('reason', reasonFilter);
        url = `${API}/api/kb/v2/inbox?${qs}`;
      } else {
        url = `${API}/api/kb/v2/lade/${activeTab}?${qs}`;
      }
      const r = await fetch(url).then(x => x.json());
      setItems(r.kaarten || []);
      setTotal(r.total || 0);
      if (activeTab === 'inbox') setReasons(r.redenen || {});
    } catch {
      setItems([]); setTotal(0);
    }
    setLoading(false);
  }, [activeTab, page, search, reasonFilter]);

  useEffect(() => { loadStats(); }, [loadStats]);
  useEffect(() => { loadItems(); }, [loadItems]);

  // Reset page on tab change
  useEffect(() => { setPage(0); setReasonFilter(''); }, [activeTab]);

  const openCard = (card) => {
    setSelectedCard(card);
    setEditMode(false);
    setEditForm(null);
  };

  const startEdit = () => {
    setEditMode(true);
    setEditForm({
      lagen: { ...(selectedCard.lagen || {}) },
      ws5:   { ...(selectedCard.ws5 || {}) },
      tags:  [...(selectedCard.tags || [])],
      begrip: selectedCard.begrip || '',
    });
  };

  const classifyTo = async (lade) => {
    if (!selectedCard) return;
    setSavingClassify(true);
    try {
      const body = {
        card_id: selectedCard.id,
        lade,
        updates: editMode ? {
          lagen: editForm?.lagen,
          ws5:   editForm?.ws5,
          tags:  editForm?.tags,
        } : null,
        user_id: 'user-001',
      };
      const r = await fetch(`${API}/api/kb/v2/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then(x => x.json());
      if (r.success) {
        setSelectedCard(null);
        setEditMode(false);
        await loadStats();
        await loadItems();
      } else {
        alert(r.message || 'Classify mislukt');
      }
    } catch (e) { alert('Fout: ' + e.message); }
    setSavingClassify(false);
  };

  const saveEdit = async () => {
    if (!selectedCard || !editForm || activeTab === 'inbox') return;
    setSavingClassify(true);
    try {
      const r = await fetch(`${API}/api/kb/v2/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          card_id: selectedCard.id,
          lade: activeTab,
          updates: { lagen: editForm.lagen, ws5: editForm.ws5, tags: editForm.tags, begrip: editForm.begrip },
          user_id: 'user-001',
        }),
      }).then(x => x.json());
      if (r.success) {
        setSelectedCard(r.kaart);
        setEditMode(false);
        await loadItems();
      } else { alert(r.message || 'Opslaan mislukt'); }
    } catch (e) { alert('Fout: ' + e.message); }
    setSavingClassify(false);
  };

  const runAudit = async () => {
    try {
      const r = await fetch(`${API}/api/kb/v2/audit`).then(x => x.json());
      setAuditData(r);
      setShowAudit(true);
    } catch {}
  };

  const totalPages = Math.ceil(total / PAGE);

  return (
    <MainLayout onNavigate={onNavigate}>
      <div data-testid="kennisbank-v2-page" className="p-4 md:p-6 space-y-4 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-amber-400" /> Kennisbank
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">4 Lades + Inbox · Piramide-laag 3 (Geheugen) · v2 schema</p>
          </div>
          <div className="flex items-center gap-2">
            <button data-testid="kbv2-audit-btn" onClick={runAudit}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-amber-500/30 text-amber-300 hover:bg-amber-500/10 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" /> Self-audit
            </button>
            <button data-testid="kbv2-new-card-btn" onClick={async () => {
                const begrip = window.prompt('Nieuwe kennis-kaart (begrip):');
                if (!begrip || !begrip.trim()) return;
                try {
                  const r = await fetch(`${API}/api/kb/v2/inbox/add`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ begrip: begrip.trim(), source: 'manual', user_id: 'user-001' })
                  }).then(x => x.json());
                  if (r && (r.success || r.card)) {
                    setActiveTab('inbox');
                    await loadStats();
                    await loadItems();
                  } else {
                    alert('Kon niet aanmaken: ' + JSON.stringify(r));
                  }
                } catch (e) { alert('Fout: ' + e.message); }
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10 flex items-center gap-1.5">
              <Plus className="w-3.5 h-3.5" /> Nieuwe kaart
            </button>
            <button data-testid="kbv2-refresh-btn" onClick={() => { loadStats(); loadItems(); }}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-700 text-slate-300 hover:bg-slate-800 flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" /> Verversen
            </button>
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex flex-wrap gap-1.5">
          <TabButton id="inbox" active={activeTab === 'inbox'} onClick={setActiveTab}
            count={stats?.inbox_count || 0} icon={<Inbox className="w-3.5 h-3.5" />}
            label="Inbox" color="#ef4444" />
          {LADES.map(l => (
            <TabButton key={l.id} id={l.id} active={activeTab === l.id} onClick={setActiveTab}
              count={stats?.lades?.[l.id]?.count || 0} iconEmoji={l.icon}
              label={l.naam} color={l.color} />
          ))}
        </div>

        {/* Search + filter row */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
            <input data-testid="kbv2-search-input" type="text" value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              placeholder="Zoek op begrip..."
              className="w-full pl-8 pr-3 py-1.5 bg-slate-900/60 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-amber-500/50" />
          </div>
          {activeTab === 'inbox' && (
            <div className="flex items-center gap-1">
              <button data-testid="kbv2-reason-all" onClick={() => { setReasonFilter(''); setPage(0); }}
                className={`px-2 py-1 rounded text-[10px] font-medium border ${
                  reasonFilter === '' ? 'bg-amber-500/20 border-amber-500/40 text-amber-300' : 'border-slate-700 text-slate-400'
                }`}>alle</button>
              {Object.entries(REASON_LABEL).map(([k, v]) => (
                <button key={k} data-testid={`kbv2-reason-${k}`}
                  onClick={() => { setReasonFilter(k); setPage(0); }}
                  className={`px-2 py-1 rounded text-[10px] font-medium border ${
                    reasonFilter === k ? 'border-current' : 'border-slate-700 text-slate-400'
                  }`}
                  style={reasonFilter === k ? { color: v.color, borderColor: v.color, backgroundColor: v.color + '15' } : {}}>
                  {v.label} {reasons[k] ? `(${reasons[k]})` : ''}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* List + Detail */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-3">
          {/* List */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl">
            <div className="px-3 py-2 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-900/90 z-10">
              <p className="text-[11px] text-slate-400 font-medium">
                {activeTab === 'inbox' ? 'Onbeantwoord' : LADES.find(l => l.id === activeTab)?.naam}
                <span className="text-slate-500"> · {total} kaarten</span>
              </p>
              {totalPages > 1 && (
                <div className="flex items-center gap-1">
                  <button data-testid="kbv2-prev-page" onClick={() => setPage(Math.max(0, page - 1))}
                    disabled={page === 0}
                    className="px-1.5 py-0.5 rounded text-[10px] border border-slate-700 text-slate-300 disabled:opacity-40">‹</button>
                  <span className="text-[10px] text-slate-500">{page + 1}/{totalPages}</span>
                  <button data-testid="kbv2-next-page" onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                    disabled={page >= totalPages - 1}
                    className="px-1.5 py-0.5 rounded text-[10px] border border-slate-700 text-slate-300 disabled:opacity-40">›</button>
                </div>
              )}
            </div>
            <div className="max-h-[70vh] overflow-y-auto">
              {loading ? (
                <p className="text-xs text-slate-500 p-4 text-center">Laden...</p>
              ) : items.length === 0 ? (
                <p className="text-xs text-slate-500 p-6 text-center">Geen kaarten.</p>
              ) : (
                items.map(card => (
                  <CardListItem key={card.id} card={card} active={selectedCard?.id === card.id}
                    onClick={() => openCard(card)} showReason={activeTab === 'inbox'} />
                ))
              )}
            </div>
          </div>

          {/* Detail / Edit */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3">
            {!selectedCard ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-12 text-slate-500">
                <Eye className="w-8 h-8 mb-2 opacity-40" />
                <p className="text-xs">Selecteer een kaart links om te bekijken of in te delen.</p>
              </div>
            ) : (
              <CardDetail card={selectedCard} editMode={editMode} editForm={editForm}
                setEditForm={setEditForm} onStartEdit={startEdit}
                onCancelEdit={() => { setEditMode(false); setEditForm(null); }}
                onClassify={classifyTo} onSaveEdit={saveEdit}
                saving={savingClassify} inInbox={activeTab === 'inbox'} currentLade={activeTab}
                onMediaUpdated={loadItems} />
            )}
          </div>
        </div>

        {/* Audit modal */}
        {showAudit && auditData && (
          <AuditModal data={auditData} onClose={() => setShowAudit(false)} />
        )}
      </div>
    </MainLayout>
  );
}

function TabButton({ id, active, onClick, count, iconEmoji, icon, label, color }) {
  return (
    <button data-testid={`kbv2-tab-${id}`}
      onClick={() => onClick(id)}
      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors flex items-center gap-1.5 ${
        active ? 'border-current' : 'border-slate-700 text-slate-300 hover:bg-slate-800'
      }`}
      style={active ? { color, borderColor: color, backgroundColor: color + '15' } : {}}>
      {iconEmoji ? <span>{iconEmoji}</span> : icon}
      <span>{label}</span>
      <span className="text-[10px] opacity-70">({count})</span>
    </button>
  );
}

function CardListItem({ card, active, onClick, showReason }) {
  const reason = card._inbox_reason;
  const r = reason ? REASON_LABEL[reason] : null;
  const hasL1 = !!(card.lagen?.laag1 || '').trim();
  return (
    <button data-testid={`kbv2-card-${card.id}`}
      onClick={onClick}
      className={`w-full text-left px-3 py-2 border-b border-slate-800/60 hover:bg-slate-800/40 transition-colors ${
        active ? 'bg-amber-500/10 border-l-2 border-l-amber-500' : ''
      }`}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-slate-200 font-medium truncate">{card.begrip || '(leeg)'}</p>
        {showReason && r && (
          <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded"
            style={{ backgroundColor: r.color + '20', color: r.color }}>{r.label}</span>
        )}
      </div>
      <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-500">
        {hasL1 ? <span className="text-emerald-400">✓ laag1</span> : <span className="text-red-400">✗ laag1</span>}
        {card.tags?.length > 0 && <span>{card.tags.slice(0, 3).join(', ')}</span>}
        {card.footnote?.vertrouwen != null && <span>· {Math.round(card.footnote.vertrouwen * 100)}%</span>}
      </div>
    </button>
  );
}

function CardDetail({ card, editMode, editForm, setEditForm, onStartEdit, onCancelEdit,
                     onClassify, onSaveEdit, saving, inInbox, currentLade, onMediaUpdated }) {
  const lagen = editMode ? editForm.lagen : (card.lagen || {});
  const ws5 = editMode ? editForm.ws5 : (card.ws5 || {});
  const tags = editMode ? editForm.tags : (card.tags || []);
  const upd = (path, val) => {
    setEditForm(f => ({ ...f, [path]: val }));
  };
  const updLaag = (key, val) => setEditForm(f => ({ ...f, lagen: { ...f.lagen, [key]: val } }));
  const updWs5  = (key, val) => setEditForm(f => ({ ...f, ws5: { ...f.ws5, [key]: val } }));

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          {editMode ? (
            <input data-testid="kbv2-edit-begrip" value={editForm.begrip}
              onChange={(e) => upd('begrip', e.target.value)}
              className="w-full text-lg font-bold text-white bg-slate-800/60 border border-slate-700 rounded px-2 py-1" />
          ) : (
            <h2 className="text-lg font-bold text-white">{card.begrip || '(leeg)'}</h2>
          )}
          <p className="text-[10px] text-slate-500 mt-0.5">{card.id}</p>
        </div>
        {!editMode ? (
          <button data-testid="kbv2-edit-btn" onClick={onStartEdit}
            className="px-2 py-1 text-xs border border-slate-700 rounded text-slate-300 hover:bg-slate-800 flex items-center gap-1">
            <Edit3 className="w-3 h-3" /> Bewerken
          </button>
        ) : (
          <button data-testid="kbv2-cancel-edit" onClick={onCancelEdit}
            className="px-2 py-1 text-xs border border-slate-700 rounded text-slate-400 hover:bg-slate-800">
            <X className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* Lagen */}
      <div className="space-y-1.5">
        {['laag1','laag2','laag3','laag4'].map((k, i) => (
          <div key={k}>
            <label className="text-[10px] uppercase text-slate-500 tracking-wide">Laag {i+1}</label>
            {editMode ? (
              <textarea data-testid={`kbv2-edit-${k}`} value={lagen[k] || ''} rows={2}
                onChange={(e) => updLaag(k, e.target.value)}
                className="w-full mt-0.5 text-xs text-slate-200 bg-slate-800/60 border border-slate-700 rounded px-2 py-1 resize-y" />
            ) : (
              <p className={`text-xs px-2 py-1 rounded ${lagen[k] ? 'text-slate-200 bg-slate-800/40' : 'text-slate-600 italic'}`}>
                {lagen[k] || '(leeg)'}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* WS5 */}
      <details className="border border-slate-800 rounded-lg">
        <summary className="px-2 py-1.5 text-[11px] text-slate-400 cursor-pointer">5W (wie/wat/wanneer/waar/waarom/hoe)</summary>
        <div className="p-2 space-y-1">
          {['wie','wat','wanneer','waar','waarom','hoe'].map(k => (
            <div key={k} className="flex items-start gap-2">
              <span className="text-[10px] text-slate-500 w-14 mt-0.5 uppercase">{k}</span>
              {editMode ? (
                <input data-testid={`kbv2-edit-ws5-${k}`} value={ws5[k] || ''}
                  onChange={(e) => updWs5(k, e.target.value)}
                  className="flex-1 text-xs text-slate-200 bg-slate-800/60 border border-slate-700 rounded px-2 py-0.5" />
              ) : (
                <span className="text-xs text-slate-300">{ws5[k] || '—'}</span>
              )}
            </div>
          ))}
        </div>
      </details>

      {/* Tags */}
      <div>
        <label className="text-[10px] uppercase text-slate-500 tracking-wide">Tags</label>
        {editMode ? (
          <input data-testid="kbv2-edit-tags" value={(tags || []).join(', ')}
            onChange={(e) => upd('tags', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
            placeholder="emotie, verbinding, ..."
            className="w-full text-xs text-slate-200 bg-slate-800/60 border border-slate-700 rounded px-2 py-1" />
        ) : (
          <div className="flex flex-wrap gap-1 mt-0.5">
            {(tags || []).slice(0, 25).map((t, i) => (
              <span key={i} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800/60 text-slate-300">{t}</span>
            ))}
          </div>
        )}
      </div>

      {/* v5_kbv2_media_001 — Voice & Image upload */}
      <MediaSection card={card} currentLade={inInbox ? null : currentLade} onUpdated={onMediaUpdated} />

      {/* Needs checklist */}
      {(card.needs || []).length > 0 && (
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-2">
          <p className="text-[10px] uppercase text-amber-300 font-medium mb-1">Mist nog:</p>
          <div className="flex flex-wrap gap-1">
            {(card.needs || []).map(n => (
              <span key={n} className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30">
                {n === 'laag1' ? '📝 laag 1' :
                 n === 'ws5' ? '5️⃣ 5W' :
                 n === 'voice' ? '🎙️ inspraak' :
                 n === 'image' ? '🖼️ foto' : n}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Footnote */}
      {card.footnote && (
        <div className="text-[10px] text-slate-500 border-t border-slate-800 pt-2 leading-relaxed">
          <p>📜 Bron: <span className="text-slate-400">{card.footnote.bron}</span>
            {card.footnote.vertrouwen != null && <> · vertrouwen <span className="text-amber-300">{Math.round(card.footnote.vertrouwen * 100)}%</span></>}
          </p>
          {card.footnote.vorige_versie_v1 && <p>Vorige versie (v1): <code className="text-slate-400">{card.footnote.vorige_versie_v1}</code></p>}
          {card.footnote.ingedeeld_op && <p>Ingedeeld: {(card.footnote.ingedeeld_op || '').slice(0, 19).replace('T', ' ')}</p>}
        </div>
      )}

      {/* Actions */}
      {inInbox ? (
        <div className="space-y-2 border-t border-slate-800 pt-3">
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <ArrowRightLeft className="w-3 h-3" /> Indelen in lade:
          </p>
          <div className="grid grid-cols-2 gap-1.5">
            {LADES.map(l => (
              <button key={l.id} data-testid={`kbv2-classify-${l.id}`}
                onClick={() => onClassify(l.id)} disabled={saving}
                className="px-2 py-2 text-xs rounded-lg border transition-colors flex items-center gap-1.5 hover:bg-slate-800 disabled:opacity-50"
                style={{ borderColor: l.color + '60', color: l.color }}>
                <span>{l.icon}</span>
                <span>{l.naam}</span>
                <ChevronRight className="w-3 h-3 ml-auto" />
              </button>
            ))}
          </div>
        </div>
      ) : editMode ? (
        <div className="border-t border-slate-800 pt-3">
          <button data-testid="kbv2-save-edit" onClick={onSaveEdit} disabled={saving}
            className="w-full px-3 py-2 text-xs rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/30 disabled:opacity-50 flex items-center justify-center gap-1.5">
            <Save className="w-3.5 h-3.5" /> {saving ? 'Opslaan...' : 'Bewaar wijzigingen'}
          </button>
        </div>
      ) : null}
    </div>
  );
}

function AuditModal({ data, onClose }) {
  const s = data.summary || {};
  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-slate-900 border border-amber-500/30 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}>
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-amber-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" /> KB v2 Self-Audit
            </h3>
            <p className="text-[10px] text-slate-500 mt-0.5">#DeWillem principe — Spark scant zichzelf op gaten</p>
          </div>
          <button data-testid="kbv2-audit-close" onClick={onClose} className="text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-4 grid grid-cols-2 md:grid-cols-3 gap-2">
          <Stat label="Lege laag1 in lades" value={s.empty_laag1_count} color="#ef4444" />
          <Stat label="Ontbrekende footnote" value={s.missing_footnote_count} color="#f59e0b" />
          <Stat label="Laag vertrouwen (<50%)" value={s.low_confidence_count} color="#f59e0b" />
          <Stat label="Kaarten zonder tags" value={s.no_tags_count} color="#94a3b8" />
          <Stat label="Inbox: tag-tie" value={s.inbox_ties} color="#f59e0b" />
          <Stat label="Inbox: no-match" value={s.inbox_no_match} color="#94a3b8" />
          <Stat label="Inbox: zonder laag1" value={s.inbox_missing_laag1} color="#ef4444" />
        </div>
        <div className="p-4 border-t border-slate-800 text-[11px] text-slate-400 leading-relaxed">
          <p>Gevonden gaten zijn geen fouten — het zijn kaarten die wachten op een mens-in-de-loop.
          Open de Inbox-tab en geef ze hun lade. Hoe meer je doet, hoe sterker Spark's geheugen wordt.</p>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div className="bg-slate-800/40 rounded-lg p-2 border border-slate-800">
      <p className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</p>
      <p className="text-xl font-bold mt-0.5" style={{ color }}>{value || 0}</p>
    </div>
  );
}

/**
 * MediaSection — voice (Whisper STT) + image upload bij een kaart.
 * Voor inbox-kaarten: currentLade = null, backend leidt lade af via index.
 */
function MediaSection({ card, currentLade, onUpdated }) {
  const media = card.media || {};
  const [recording, setRecording] = useState(false);
  const [uploadingVoice, setUploadingVoice] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [err, setErr] = useState('');
  const mediaRecRef = useRef(null);
  const chunksRef = useRef([]);
  const imgInputRef = useRef(null);

  const startRecord = async () => {
    setErr('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(t => t.stop());
        await uploadVoice(blob);
      };
      mediaRecRef.current = mr;
      mr.start();
      setRecording(true);
    } catch (e) {
      setErr('Microfoon geweigerd of niet beschikbaar.');
    }
  };

  const stopRecord = () => {
    try { mediaRecRef.current?.stop(); } catch {}
    setRecording(false);
  };

  const uploadVoice = async (blob) => {
    setUploadingVoice(true);
    try {
      const fd = new FormData();
      fd.append('audio', blob, 'inspraak.webm');
      fd.append('card_id', card.id);
      if (currentLade) fd.append('lade', currentLade);
      fd.append('user_id', 'user-001');
      const r = await fetch(`${API}/api/kb/v2/media/voice`, { method: 'POST', body: fd }).then(x => x.json());
      if (!r.success) setErr(r.error || 'Voice-upload mislukt');
      onUpdated && onUpdated();
    } catch (e) { setErr('Voice-upload fout: ' + e.message); }
    setUploadingVoice(false);
  };

  const handleImageSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingImage(true);
    setErr('');
    try {
      const fd = new FormData();
      fd.append('image', file);
      fd.append('card_id', card.id);
      if (currentLade) fd.append('lade', currentLade);
      fd.append('user_id', 'user-001');
      const r = await fetch(`${API}/api/kb/v2/media/image`, { method: 'POST', body: fd }).then(x => x.json());
      if (!r.success) setErr('Image-upload mislukt');
      onUpdated && onUpdated();
    } catch (ex) { setErr('Image fout: ' + ex.message); }
    setUploadingImage(false);
    if (imgInputRef.current) imgInputRef.current.value = '';
  };

  return (
    <div className="border-t border-slate-800 pt-3 space-y-2">
      <p className="text-[10px] uppercase text-slate-500 tracking-wide">Media</p>

      {/* Voice */}
      <div className="bg-slate-800/30 rounded-lg p-2 space-y-2">
        <div className="flex items-center gap-2">
          {!recording ? (
            <button data-testid="kbv2-voice-record"
              onClick={startRecord} disabled={uploadingVoice}
              className="px-2 py-1 text-xs rounded-md bg-rose-500/15 border border-rose-500/40 text-rose-300 hover:bg-rose-500/25 disabled:opacity-50 flex items-center gap-1.5">
              <Mic className="w-3.5 h-3.5" /> {uploadingVoice ? 'Transcriberen...' : 'Spreek in'}
            </button>
          ) : (
            <button data-testid="kbv2-voice-stop" onClick={stopRecord}
              className="px-2 py-1 text-xs rounded-md bg-red-500/30 border border-red-500/60 text-red-200 animate-pulse flex items-center gap-1.5">
              <Square className="w-3.5 h-3.5" /> Stop & verstuur
            </button>
          )}
          {media.voice_url && (
            <audio data-testid="kbv2-voice-audio" controls className="h-7 flex-1" src={API + media.voice_url} />
          )}
        </div>
        {media.voice_transcript && (
          <div className="text-[11px] text-slate-300 italic bg-slate-900/50 rounded px-2 py-1 border-l-2 border-rose-500/40">
            <span className="text-slate-500">Transcript: </span>"{media.voice_transcript}"
          </div>
        )}
      </div>

      {/* Image */}
      <div className="bg-slate-800/30 rounded-lg p-2 space-y-2">
        <div className="flex items-center gap-2">
          <input ref={imgInputRef} type="file" accept="image/*" onChange={handleImageSelect}
            className="hidden" data-testid="kbv2-image-input" />
          <button data-testid="kbv2-image-upload" onClick={() => imgInputRef.current?.click()}
            disabled={uploadingImage}
            className="px-2 py-1 text-xs rounded-md bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/25 disabled:opacity-50 flex items-center gap-1.5">
            <ImageIcon className="w-3.5 h-3.5" /> {uploadingImage ? 'Uploaden...' : 'Foto toevoegen'}
          </button>
          {(media.image_urls || []).length > 0 && (
            <span className="text-[10px] text-slate-500">{media.image_urls.length} foto's</span>
          )}
        </div>
        {(media.image_urls || []).length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {(media.image_urls || []).map((url, i) => (
              <img key={i} src={API + url} alt={`media-${i}`}
                className="w-16 h-16 object-cover rounded border border-slate-700" />
            ))}
          </div>
        )}
      </div>

      {err && <p className="text-[10px] text-red-400">{err}</p>}
    </div>
  );
}

export default KennisbankV2Page;
