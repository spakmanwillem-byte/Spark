// v6_dnd_gallery_001 — D&D Galerij in Beheer → Archief → Foto sub-tab
// Toont alle D&D bark-kaarten (draft + locked), met form om nieuwe te maken
// en lock/unlock/delete per kaart.
import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Lock, Unlock, Trash2, Sparkles, X, Save, RefreshCw } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const SENSE_META = {
  zie:  { label: 'Zie',  icon: '👁️', color: '#06b6d4' },
  hoor: { label: 'Hoor', icon: '👂', color: '#f59e0b' },
  voel: { label: 'Voel', icon: '❤️', color: '#ec4899' },
};

export function DnDGallerySection({ adminId = 'user-001', isAdmin = true }) {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all' | 'draft' | 'locked'
  const [showForm, setShowForm] = useState(false);
  const [selected, setSelected] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/cards?limit=200`).then(x => x.json());
      setCards(r.cards || []);
    } catch (e) {
      console.error('Load D&D cards:', e);
      setCards([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = cards.filter(c => filter === 'all' || c.status === filter);

  const counts = {
    all: cards.length,
    draft: cards.filter(c => c.status === 'draft').length,
    locked: cards.filter(c => c.status === 'locked').length,
  };

  const toggleLock = async (card) => {
    try {
      await fetch(`${API}/api/dnd/spark-world/cards/${card.id}/lock`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: adminId, locked: card.status !== 'locked' }),
      });
      await load();
      if (selected?.id === card.id) {
        const fresh = await fetch(`${API}/api/dnd/spark-world/cards/${card.id}`).then(x => x.json());
        setSelected(fresh);
      }
    } catch (e) { alert('Lock-fout: ' + e.message); }
  };

  const deleteCard = async (card) => {
    if (!window.confirm(`Verwijder D&D-kaart "${card.titel}"?`)) return;
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/cards/${card.id}`, {
        method: 'DELETE',
      });
      if (!r.ok) {
        const t = await r.text();
        alert(`Verwijderen mislukt (${r.status}): ${t}`);
        return;
      }
      setSelected(null);
      await load();
    } catch (e) { alert('Delete-fout: ' + e.message); }
  };

  return (
    <div data-testid="dnd-gallery-section" className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" /> D&D Galerij — Spark World kaarten
          </h3>
          <p className="text-[11px] text-slate-400 mt-1 max-w-2xl">
            Alle bark-kaarten uit Spark World. Class: <span className="text-amber-300">game · D&D</span>.
            Locked kaarten verschijnen als keuze-knop bij volgende sessie-start.
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <button data-testid="dnd-gallery-refresh" onClick={load}
            className="px-2.5 py-1.5 rounded-lg text-[11px] font-medium border border-slate-700 text-slate-300 hover:bg-slate-800 flex items-center gap-1.5">
            <RefreshCw className="w-3 h-3" /> Verversen
          </button>
          {isAdmin && (
            <button data-testid="dnd-gallery-new-btn" onClick={() => setShowForm(true)}
              className="px-3 py-1.5 rounded-lg text-[11px] font-medium border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/15 flex items-center gap-1.5">
              <Plus className="w-3 h-3" /> Nieuwe D&D-kaart
            </button>
          )}
        </div>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-1.5">
        {[
          { id: 'all',    label: 'Alles',   color: '#64748b' },
          { id: 'draft',  label: 'Draft',   color: '#f59e0b' },
          { id: 'locked', label: 'Locked (canon)', color: '#10b981' },
        ].map(f => (
          <button key={f.id} data-testid={`dnd-gallery-filter-${f.id}`}
            onClick={() => setFilter(f.id)}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-colors ${
              filter === f.id ? 'border-current' : 'border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
            style={filter === f.id ? { color: f.color, borderColor: f.color, background: f.color + '15' } : {}}>
            {f.label} <span className="opacity-60">({counts[f.id]})</span>
          </button>
        ))}
      </div>

      {/* Grid */}
      {loading ? (
        <p className="text-xs text-slate-500 py-6 text-center">Kaarten laden...</p>
      ) : filtered.length === 0 ? (
        <p className="text-xs text-slate-500 py-8 text-center">
          {filter === 'all'
            ? 'Nog geen D&D-kaarten. Klik "Nieuwe D&D-kaart" om er een te maken.'
            : `Geen kaarten met status "${filter}".`}
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {filtered.map(c => {
            const m = SENSE_META[c.sense] || { label: '?', icon: '✨', color: '#94a3b8' };
            return (
              <button key={c.id} data-testid={`dnd-gallery-card-${c.id}`}
                onClick={() => setSelected(c)}
                className="text-left p-3 rounded-xl border-2 transition-all hover:scale-[1.02]"
                style={{ borderColor: (c.color || m.color) + '40', background: (c.color || m.color) + '08' }}>
                <div className="flex items-start gap-2">
                  <span className="text-xl">{c.icon || m.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1 mb-0.5">
                      <span className="text-[9px] font-bold uppercase tracking-wider"
                        style={{ color: c.color || m.color }}>{c.sense_label || m.label}</span>
                      {c.status === 'locked' ? (
                        <Lock className="w-2.5 h-2.5 text-emerald-400" />
                      ) : (
                        <span className="text-[9px] text-amber-400">draft</span>
                      )}
                    </div>
                    <p className="text-xs font-medium text-white truncate">{c.titel}</p>
                    <p className="text-[10px] text-slate-400 mt-1 line-clamp-2">{c.content_preview || '—'}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Detail modal */}
      {selected && (
        <DnDCardDetail card={selected} onClose={() => setSelected(null)}
          onToggleLock={() => toggleLock(selected)}
          onDelete={() => deleteCard(selected)}
          isAdmin={isAdmin} />
      )}

      {/* New card modal */}
      {showForm && (
        <DnDCardForm
          adminId={adminId}
          onClose={() => setShowForm(false)}
          onSaved={async () => { setShowForm(false); await load(); }}
        />
      )}
    </div>
  );
}

// ============================================================
// Detail modal — toon kaart-inhoud + lock/delete
// ============================================================
function DnDCardDetail({ card, onClose, onToggleLock, onDelete, isAdmin }) {
  const [full, setFull] = useState(null);
  useEffect(() => {
    fetch(`${API}/api/dnd/spark-world/cards/${card.id}`)
      .then(r => r.json()).then(setFull).catch(() => setFull(null));
  }, [card.id]);

  const m = SENSE_META[card.sense] || { label: '?', icon: '✨', color: '#94a3b8' };
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div data-testid="dnd-gallery-detail" className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full max-h-[85vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}>
        <div className="p-4 border-b border-slate-800 flex items-start justify-between gap-2"
          style={{ background: (card.color || m.color) + '08' }}>
          <div className="flex items-start gap-2.5 flex-1">
            <span className="text-3xl">{card.icon || m.icon}</span>
            <div>
              <p className="text-[10px] uppercase font-bold tracking-wider"
                style={{ color: card.color || m.color }}>{card.sense_label || m.label}</p>
              <h3 className="text-base font-bold text-white">{card.titel}</h3>
              <p className="text-[10px] text-slate-500 mt-0.5">{card.id}</p>
            </div>
          </div>
          <button data-testid="dnd-gallery-detail-close" onClick={onClose} className="p-1 hover:bg-slate-800 rounded">
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <p className="text-[10px] uppercase text-slate-500 tracking-wider mb-1">Inhoud</p>
            <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
              {full?.content || card.content_preview || '—'}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <InfoItem label="Status" value={card.status === 'locked'
              ? <span className="text-emerald-400 font-semibold">🔒 Locked (canon)</span>
              : <span className="text-amber-400">Draft</span>} />
            <InfoItem label="KB-lade" value={full?.kb_lade || '—'} />
            <InfoItem label="Class" value="game · D&D" />
            <InfoItem label="Aangemaakt" value={full?.footnote?.aangemaakt_op?.slice(0, 16).replace('T', ' ') || '—'} />
          </div>
        </div>
        {isAdmin && (
          <div className="p-4 border-t border-slate-800 flex gap-2 justify-end">
            <button data-testid="dnd-gallery-delete" onClick={onDelete}
              className="px-3 py-1.5 text-xs text-red-300 border border-red-500/40 hover:bg-red-500/10 rounded-lg flex items-center gap-1.5">
              <Trash2 className="w-3 h-3" /> Verwijder
            </button>
            <button data-testid="dnd-gallery-togglelock" onClick={onToggleLock}
              className="px-3 py-1.5 text-xs border rounded-lg flex items-center gap-1.5"
              style={card.status === 'locked'
                ? { color: '#fcd34d', borderColor: '#f59e0b40', background: '#f59e0b10' }
                : { color: '#6ee7b7', borderColor: '#10b98140', background: '#10b98110' }}>
              {card.status === 'locked' ? <><Unlock className="w-3 h-3" /> Unlock (draft)</> : <><Lock className="w-3 h-3" /> Vastklikken (canon)</>}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div className="p-2 bg-slate-800/40 rounded-lg">
      <p className="text-[9px] uppercase text-slate-500 tracking-wider">{label}</p>
      <div className="text-xs text-slate-200 mt-0.5">{value}</div>
    </div>
  );
}

// ============================================================
// New card form — venster met leeg format
// ============================================================
function DnDCardForm({ adminId, onClose, onSaved }) {
  const [sense, setSense] = useState('zie');
  const [titel, setTitel] = useState('');
  const [content, setContent] = useState('');
  const [lockNow, setLockNow] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState(null);

  const submit = async () => {
    setErr(null);
    if (!content.trim()) { setErr('Vul de inhoud in'); return; }
    setSaving(true);
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/respond`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: adminId,
          sense,
          content: content.trim(),
          titel: titel.trim() || null,
        }),
      }).then(x => x.json());
      if (!r.success) { setErr(r.message || 'Opslaan mislukt'); setSaving(false); return; }
      if (lockNow) {
        await fetch(`${API}/api/dnd/spark-world/cards/${r.card.id}/lock`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: adminId, locked: true }),
        });
      }
      onSaved?.();
    } catch (e) {
      setErr(e.message);
    }
    setSaving(false);
  };

  const m = SENSE_META[sense];
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div data-testid="dnd-gallery-form" className="bg-slate-900 border border-emerald-500/30 rounded-2xl max-w-lg w-full"
        onClick={e => e.stopPropagation()}>
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Plus className="w-4 h-4 text-emerald-400" /> Nieuwe D&D-kaart
          </h3>
          <button data-testid="dnd-gallery-form-close" onClick={onClose} className="p-1 hover:bg-slate-800 rounded">
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <label className="text-[10px] uppercase text-slate-400 tracking-wider mb-1.5 block">Zintuig (kanaal)</label>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(SENSE_META).map(([id, meta]) => (
                <button key={id} data-testid={`dnd-gallery-form-sense-${id}`}
                  onClick={() => setSense(id)}
                  className="flex flex-col items-center gap-1 py-2.5 rounded-lg border-2 transition-all"
                  style={{
                    borderColor: sense === id ? meta.color : meta.color + '30',
                    background: sense === id ? meta.color + '20' : meta.color + '05',
                  }}>
                  <span className="text-xl">{meta.icon}</span>
                  <span className="text-[11px] font-bold" style={{ color: meta.color }}>{meta.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-[10px] uppercase text-slate-400 tracking-wider mb-1 block">Titel <span className="text-slate-600">(optioneel)</span></label>
            <input data-testid="dnd-gallery-form-titel" type="text" value={titel}
              onChange={e => setTitel(e.target.value)}
              placeholder="Spark verzint anders een titel uit de inhoud"
              className="w-full px-3 py-1.5 bg-slate-800/60 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50" />
          </div>

          <div>
            <label className="text-[10px] uppercase text-slate-400 tracking-wider mb-1 block">Inhoud <span className="text-red-400">*</span></label>
            <textarea data-testid="dnd-gallery-form-content" value={content} rows={5}
              onChange={e => setContent(e.target.value)}
              placeholder={m.label === 'Zie' ? 'Wat zie je? Een beeld, een kleur, een vorm...'
                : m.label === 'Hoor' ? 'Wat hoor je? Een geluid, een woord, een context...'
                : 'Wat voel je? Een emotie, een spanning, een rust...'}
              className="w-full px-3 py-2 bg-slate-800/60 border-2 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none"
              style={{ borderColor: m.color + '40' }} />
          </div>

          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
            <input type="checkbox" data-testid="dnd-gallery-form-locknow" checked={lockNow} onChange={e => setLockNow(e.target.checked)}
              className="accent-emerald-500" />
            Direct vastklikken (canon) — verschijnt meteen als keuze in volgende sessie
          </label>

          {err && (
            <p data-testid="dnd-gallery-form-error" className="text-xs text-red-400 p-2 bg-red-500/10 border border-red-500/20 rounded-lg">{err}</p>
          )}
        </div>
        <div className="p-4 border-t border-slate-800 flex justify-end gap-2">
          <button data-testid="dnd-gallery-form-cancel" onClick={onClose}
            className="px-3 py-1.5 text-xs text-slate-400 hover:bg-slate-800 rounded-lg">Annuleren</button>
          <button data-testid="dnd-gallery-form-save" onClick={submit} disabled={saving}
            className="px-4 py-1.5 text-xs font-medium rounded-lg text-white disabled:opacity-40 flex items-center gap-1.5"
            style={{ background: m.color }}>
            <Save className="w-3 h-3" /> {saving ? 'Opslaan...' : 'Aanmaken'}
          </button>
        </div>
      </div>
    </div>
  );
}
