// v6_dnd_gallery_002 — D&D Galerij met KB-shape game-kaarten in game.json
// v6_dnd_gallery_media_001 — Functionele Media: upload + picker uit Algemene foto's + thumbnails
// Zelfde detail-paneel structuur als KB v2 (Lagen 1-4, 5W, Tags, Media, lock).
// Class: "game", category-tag: "D&D".
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Plus, Lock, Unlock, Trash2, Sparkles, X, Save, RefreshCw,
  Edit3, Mic, Image as ImageIcon, Upload, FolderOpen, Check,
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const SENSE_META = {
  zie:  { label: 'Zie',  icon: '👁️', color: '#06b6d4' },
  hoor: { label: 'Hoor', icon: '👂', color: '#f59e0b' },
  voel: { label: 'Voel', icon: '❤️', color: '#ec4899' },
};

export function DnDGallerySection({ adminId = 'user-001', isAdmin = true }) {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState(null);
  const [showNewModal, setShowNewModal] = useState(false);
  const [showPicker, setShowPicker] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/game-cards?limit=500`).then(x => x.json());
      setCards(r.cards || []);
    } catch (e) {
      console.error('Load game-cards:', e);
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

  const createNew = async (begrip, sense) => {
    const b = (begrip || '').trim();
    if (!b) return;
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/game-cards`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ begrip: b, user_id: adminId, sense: sense || null }),
      }).then(x => x.json());
      if (r.success && r.card) {
        setShowNewModal(false);
        await load();
        // Open direct in edit-mode
        setSelected(r.card);
        setEditMode(true);
        setEditForm({
          begrip: r.card.begrip,
          lagen:  { ...(r.card.lagen || {}) },
          ws5:    { ...(r.card.ws5 || {}) },
          tags:   [...(r.card.tags || [])],
          sense:  r.card.sense || '',
        });
      } else {
        alert('Aanmaken mislukt: ' + JSON.stringify(r));
      }
    } catch (e) { alert('Fout: ' + e.message); }
  };

  // ---- Media: voeg foto-URL toe aan card.media.image_urls ----
  const attachImageUrl = async (card, url) => {
    if (!card || !url) return;
    const current = card.media?.image_urls || [];
    if (current.includes(url)) return;
    const r = await fetch(`${API}/api/dnd/spark-world/game-cards/edit`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        card_id: card.id,
        updates: { media: { image_urls: [...current, url] } },
        user_id: adminId,
      }),
    }).then(x => x.json());
    if (r.success && r.card) {
      setSelected(r.card);
      await load();
    }
  };

  const removeImageUrl = async (card, url) => {
    if (!card || !url) return;
    const remaining = (card.media?.image_urls || []).filter(u => u !== url);
    const r = await fetch(`${API}/api/dnd/spark-world/game-cards/edit`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        card_id: card.id,
        updates: { media: { image_urls: remaining } },
        user_id: adminId,
      }),
    }).then(x => x.json());
    if (r.success && r.card) {
      setSelected(r.card);
      await load();
    }
  };

  const uploadAndAttach = async (card, file) => {
    if (!card || !file) return;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('category', 'foto');
    fd.append('uploaded_by', adminId);
    fd.append('tags', 'D&D, game-card');
    fd.append('description', `D&D-kaart: ${card.begrip}`);
    const r = await fetch(`${API}/api/system-archive/upload`, { method: 'POST', body: fd })
      .then(x => x.json()).catch(() => ({}));
    if (r.success && r.file?.download_url) {
      await attachImageUrl(card, r.file.download_url);
    } else {
      alert('Upload mislukt');
    }
  };

  const saveEdit = async () => {
    if (!selected || !editForm) return;
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/game-cards/edit`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          card_id: selected.id,
          updates: {
            begrip: editForm.begrip,
            lagen:  editForm.lagen,
            ws5:    editForm.ws5,
            tags:   editForm.tags,
            sense:  editForm.sense || null,
          },
          user_id: adminId,
        }),
      }).then(x => x.json());
      if (r.success && r.card) {
        setSelected(r.card);
        setEditMode(false);
        await load();
      } else {
        alert(r.message || 'Opslaan mislukt');
      }
    } catch (e) { alert('Fout: ' + e.message); }
  };

  const toggleLock = async (card) => {
    try {
      await fetch(`${API}/api/dnd/spark-world/game-cards/lock`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: card.id, locked: card.status !== 'locked', user_id: adminId }),
      });
      const fresh = await fetch(`${API}/api/dnd/spark-world/game-cards/${card.id}`).then(x => x.json());
      setSelected(fresh);
      await load();
    } catch (e) { alert('Lock-fout: ' + e.message); }
  };

  const deleteCard = async (card) => {
    if (!window.confirm(`Verwijder game-kaart "${card.begrip}"?`)) return;
    try {
      await fetch(`${API}/api/dnd/spark-world/game-cards/${card.id}`, { method: 'DELETE' });
      setSelected(null);
      setEditMode(false);
      await load();
    } catch (e) { alert('Delete-fout: ' + e.message); }
  };

  return (
    <div data-testid="dnd-gallery-section" className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" /> D&amp;D Galerij — Game-kaarten
          </h3>
          <p className="text-[11px] text-slate-400 mt-1 max-w-2xl">
            Zelfde format als kennis-kaarten (Lagen 1-4, 5W, Tags, Media), maar opgeslagen in
            <span className="text-amber-300"> game.json</span> met class <span className="text-amber-300">game · D&amp;D</span>.
            Locked kaarten worden gebruikt door de game-mage.
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <button data-testid="dnd-gallery-refresh" onClick={load}
            className="px-2.5 py-1.5 rounded-lg text-[11px] font-medium border border-slate-700 text-slate-300 hover:bg-slate-800 flex items-center gap-1.5">
            <RefreshCw className="w-3 h-3" /> Verversen
          </button>
          {isAdmin && (
            <button data-testid="dnd-gallery-new-btn" onClick={() => setShowNewModal(true)}
              className="px-3 py-1.5 rounded-lg text-[11px] font-medium border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/15 flex items-center gap-1.5">
              <Plus className="w-3 h-3" /> Nieuwe kaart
            </button>
          )}
        </div>
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-1.5">
        {[
          { id: 'all',    label: 'Alles',           color: '#64748b' },
          { id: 'draft',  label: 'Draft',           color: '#f59e0b' },
          { id: 'locked', label: 'Locked (canon)',  color: '#10b981' },
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

      {/* Split-view: list + detail */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-3">
        {/* List */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl">
          <div className="px-3 py-2 border-b border-slate-800 text-[11px] text-slate-400">
            {filtered.length} kaart{filtered.length === 1 ? '' : 'en'}
          </div>
          <div className="max-h-[60vh] overflow-y-auto">
            {loading ? (
              <p className="text-xs text-slate-500 p-4 text-center">Laden...</p>
            ) : filtered.length === 0 ? (
              <p className="text-xs text-slate-500 p-6 text-center">
                Geen kaarten. Klik "Nieuwe kaart" om er een te maken.
              </p>
            ) : filtered.map(c => {
              const m = SENSE_META[c.sense] || { icon: '🎲', color: '#a855f7' };
              const hasL1 = !!(c.lagen?.laag1 || '').trim();
              const active = selected?.id === c.id;
              const thumb = (c.media?.image_urls || [])[0];
              return (
                <button key={c.id} data-testid={`dnd-gallery-card-${c.id}`}
                  onClick={() => { setSelected(c); setEditMode(false); }}
                  className={`w-full text-left px-3 py-2 border-b border-slate-800/60 hover:bg-slate-800/40 transition-colors ${
                    active ? 'bg-amber-500/10 border-l-2 border-l-amber-500' : ''
                  }`}>
                  <div className="flex items-center gap-2">
                    {thumb ? (
                      <img src={`${API}${thumb}`} alt=""
                        className="w-9 h-9 rounded object-cover border border-amber-500/40 flex-shrink-0" />
                    ) : (
                      <span className="w-9 h-9 rounded bg-slate-800/60 border border-slate-700 flex items-center justify-center flex-shrink-0 text-sm"
                        style={{ color: c.sense ? m.color : '#a855f7' }}>{m.icon}</span>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm text-slate-200 font-medium truncate">{c.begrip || '(leeg)'}</p>
                        {c.status === 'locked' ? (
                          <Lock className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                        ) : (
                          <span className="text-[9px] uppercase text-amber-400 flex-shrink-0">draft</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-500">
                        {hasL1 ? <span className="text-emerald-400">✓ laag1</span> : <span className="text-red-400">✗ laag1</span>}
                        {c.tags?.length > 0 && <span className="truncate">{c.tags.slice(0, 3).join(', ')}</span>}
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Detail / Edit panel — zelfde stijl als KB v2 */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3">
          {!selected ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12 text-slate-500">
              <Sparkles className="w-8 h-8 mb-2 opacity-40" />
              <p className="text-xs">Selecteer een kaart links of klik "Nieuwe kaart".</p>
            </div>
          ) : (
            <GameCardDetail
              card={selected}
              editMode={editMode}
              editForm={editForm}
              setEditForm={setEditForm}
              isAdmin={isAdmin}
              onStartEdit={() => {
                setEditMode(true);
                setEditForm({
                  begrip: selected.begrip || '',
                  lagen:  { ...(selected.lagen || {}) },
                  ws5:    { ...(selected.ws5 || {}) },
                  tags:   [...(selected.tags || [])],
                  sense:  selected.sense || '',
                });
              }}
              onCancelEdit={() => { setEditMode(false); setEditForm(null); }}
              onSave={saveEdit}
              onToggleLock={() => toggleLock(selected)}
              onDelete={() => deleteCard(selected)}
              onUpload={(file) => uploadAndAttach(selected, file)}
              onOpenPicker={() => setShowPicker(true)}
              onRemoveImage={(url) => removeImageUrl(selected, url)}
              apiUrl={API}
            />
          )}
        </div>
      </div>

      {/* Nieuwe kaart modal */}
      {showNewModal && (
        <NewCardModal
          onCreate={createNew}
          onClose={() => setShowNewModal(false)}
        />
      )}

      {/* Picker uit Algemene foto's */}
      {showPicker && selected && (
        <ArchivePhotoPicker
          apiUrl={API}
          alreadyAttached={selected.media?.image_urls || []}
          onPick={async (url) => {
            await attachImageUrl(selected, url);
            setShowPicker(false);
          }}
          onClose={() => setShowPicker(false)}
        />
      )}
    </div>
  );
}

// ============================================================
// Detail / Edit paneel — zelfde structuur als KB v2
// ============================================================
function GameCardDetail({ card, editMode, editForm, setEditForm, isAdmin,
                         onStartEdit, onCancelEdit, onSave, onToggleLock, onDelete,
                         onUpload, onOpenPicker, onRemoveImage, apiUrl }) {
  const lagen = editMode ? editForm.lagen : (card.lagen || {});
  const ws5   = editMode ? editForm.ws5   : (card.ws5 || {});
  const tags  = editMode ? editForm.tags  : (card.tags || []);
  const sense = editMode ? editForm.sense : (card.sense || '');
  const updLaag = (k, v) => setEditForm(f => ({ ...f, lagen: { ...f.lagen, [k]: v } }));
  const updWs5  = (k, v) => setEditForm(f => ({ ...f, ws5:   { ...f.ws5,   [k]: v } }));
  const upd     = (k, v) => setEditForm(f => ({ ...f, [k]: v }));

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          {editMode ? (
            <input data-testid="dnd-edit-begrip" value={editForm.begrip}
              onChange={e => upd('begrip', e.target.value)}
              className="w-full text-lg font-bold text-white bg-slate-800/60 border border-slate-700 rounded px-2 py-1" />
          ) : (
            <h2 className="text-lg font-bold text-white">{card.begrip || '(leeg)'}</h2>
          )}
          <p className="text-[10px] text-slate-500 mt-0.5">{card.id} · class: <span className="text-amber-300">{card.class} · D&amp;D</span></p>
        </div>
        {!editMode ? (
          isAdmin && (
            <button data-testid="dnd-edit-btn" onClick={onStartEdit}
              className="px-2 py-1 text-xs border border-slate-700 rounded text-slate-300 hover:bg-slate-800 flex items-center gap-1">
              <Edit3 className="w-3 h-3" /> Bewerken
            </button>
          )
        ) : (
          <button data-testid="dnd-cancel-edit" onClick={onCancelEdit}
            className="px-2 py-1 text-xs border border-slate-700 rounded text-slate-400 hover:bg-slate-800">
            <X className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* Optioneel zintuig kanaal */}
      {editMode && (
        <div>
          <label className="text-[10px] uppercase text-slate-500 tracking-wide">Zintuig (optioneel)</label>
          <div className="flex gap-1.5 mt-1">
            <button data-testid="dnd-edit-sense-none" onClick={() => upd('sense', '')}
              className={`px-2 py-1 rounded text-[10px] border ${!sense ? 'bg-slate-700 text-white border-slate-600' : 'border-slate-700 text-slate-400'}`}>geen</button>
            {Object.entries(SENSE_META).map(([id, m]) => (
              <button key={id} data-testid={`dnd-edit-sense-${id}`} onClick={() => upd('sense', id)}
                className="px-2 py-1 rounded text-[10px] border"
                style={sense === id
                  ? { background: m.color + '20', color: m.color, borderColor: m.color }
                  : { borderColor: m.color + '40', color: m.color + 'aa' }}>
                {m.icon} {m.label}
              </button>
            ))}
          </div>
        </div>
      )}
      {!editMode && sense && (
        <p className="text-[10px] text-slate-500">
          Kanaal: <span style={{ color: SENSE_META[sense]?.color }}>{SENSE_META[sense]?.icon} {SENSE_META[sense]?.label}</span>
        </p>
      )}

      {/* Lagen */}
      <div className="space-y-1.5">
        {['laag1','laag2','laag3','laag4'].map((k, i) => (
          <div key={k}>
            <label className="text-[10px] uppercase text-slate-500 tracking-wide">Laag {i+1}</label>
            {editMode ? (
              <textarea data-testid={`dnd-edit-${k}`} value={lagen[k] || ''} rows={2}
                onChange={e => updLaag(k, e.target.value)}
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
      <details className="border border-slate-800 rounded-lg" open={editMode}>
        <summary className="px-2 py-1.5 text-[11px] text-slate-400 cursor-pointer">5W (wie/wat/wanneer/waar/waarom/hoe)</summary>
        <div className="p-2 space-y-1">
          {['wie','wat','wanneer','waar','waarom','hoe'].map(k => (
            <div key={k} className="flex items-start gap-2">
              <span className="text-[10px] text-slate-500 w-14 mt-0.5 uppercase">{k}</span>
              {editMode ? (
                <input data-testid={`dnd-edit-ws5-${k}`} value={ws5[k] || ''}
                  onChange={e => updWs5(k, e.target.value)}
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
          <input data-testid="dnd-edit-tags" value={(tags || []).join(', ')}
            onChange={e => upd('tags', e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
            placeholder="D&D, ..."
            className="w-full text-xs text-slate-200 bg-slate-800/60 border border-slate-700 rounded px-2 py-1" />
        ) : (
          <div className="flex flex-wrap gap-1 mt-0.5">
            {(tags || []).slice(0, 25).map((t, i) => (
              <span key={i} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800/60 text-slate-300">{t}</span>
            ))}
          </div>
        )}
      </div>

      {/* Media — v6_dnd_gallery_media_001: functioneel (upload + picker uit foto-archief) */}
      <div className="bg-slate-800/30 rounded-lg p-2.5 space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-[10px] uppercase text-slate-500 tracking-wide flex items-center gap-1.5">
            <ImageIcon className="w-3 h-3" /> Media — Foto's
          </p>
          {isAdmin && (
            <div className="flex items-center gap-1">
              <DnDUploadButton onUpload={onUpload} />
              <button data-testid="dnd-media-pick-btn" onClick={onOpenPicker}
                className="px-2 py-1 text-[10px] rounded border border-amber-500/40 text-amber-300 hover:bg-amber-500/15 flex items-center gap-1">
                <FolderOpen className="w-3 h-3" /> Kies uit foto's
              </button>
            </div>
          )}
        </div>
        {(card.media?.image_urls || []).length > 0 ? (
          <div data-testid="dnd-media-grid" className="grid grid-cols-3 sm:grid-cols-4 gap-1.5">
            {(card.media.image_urls || []).map((u, i) => (
              <div key={i} className="relative aspect-square rounded border border-slate-700 overflow-hidden bg-slate-900 group">
                <img src={`${apiUrl}${u}`} alt="" className="w-full h-full object-cover" />
                {i === 0 && (
                  <span className="absolute top-0.5 left-0.5 text-[8px] px-1 py-0.5 rounded bg-amber-500/80 text-stone-950 font-bold">
                    ICON
                  </span>
                )}
                {isAdmin && (
                  <button data-testid={`dnd-media-remove-${i}`}
                    onClick={() => onRemoveImage(u)}
                    className="absolute top-0.5 right-0.5 w-5 h-5 rounded-full bg-red-500/90 text-white opacity-0 group-hover:opacity-100 flex items-center justify-center">
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[10px] text-slate-500 italic">Nog geen foto's. Upload nieuw, of kies uit Algemene foto's. De 1e foto wordt het icoon op de kaart.</p>
        )}
        <div className="text-[10px] text-slate-500 flex items-center gap-1.5 pt-1 border-t border-slate-800/60">
          <button disabled className="px-2 py-1 rounded border border-slate-700 opacity-50 flex items-center gap-1">
            <Mic className="w-3 h-3" /> Spreek in
          </button>
          <span className="text-slate-600">(voice komt later)</span>
        </div>
      </div>

      {/* Needs */}
      {(card.needs || []).length > 0 && !editMode && (
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-2">
          <p className="text-[10px] uppercase text-amber-300 font-medium mb-1">Mist nog:</p>
          <div className="flex flex-wrap gap-1">
            {(card.needs || []).map(n => (
              <span key={n} className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30">
                {n === 'laag1' ? '📝 laag 1' : n === 'ws5' ? '5️⃣ 5W' : n === 'voice' ? '🎙️ inspraak' : n === 'image' ? '🖼️ foto' : n}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Footnote */}
      {card.footnote && !editMode && (
        <div className="text-[10px] text-slate-500 border-t border-slate-800 pt-2 leading-relaxed">
          <p>📜 Bron: <span className="text-slate-400">{card.footnote.bron}</span>
            {card.footnote.vertrouwen != null && <> · vertrouwen <span className="text-amber-300">{Math.round(card.footnote.vertrouwen * 100)}%</span></>}
          </p>
          <p>Status: {card.status === 'locked'
            ? <span className="text-emerald-400 font-semibold">🔒 LOCKED (canon)</span>
            : <span className="text-amber-400">draft</span>}</p>
        </div>
      )}

      {/* Action bar */}
      <div className="border-t border-slate-800 pt-3 flex flex-wrap items-center gap-2 justify-end">
        {editMode ? (
          <button data-testid="dnd-save-edit" onClick={onSave}
            className="px-3 py-1.5 text-xs rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/30 flex items-center gap-1.5">
            <Save className="w-3.5 h-3.5" /> Bewaar wijzigingen
          </button>
        ) : isAdmin && (
          <>
            <button data-testid="dnd-delete" onClick={onDelete}
              className="px-3 py-1.5 text-xs text-red-300 border border-red-500/40 hover:bg-red-500/10 rounded-lg flex items-center gap-1.5">
              <Trash2 className="w-3 h-3" /> Verwijder
            </button>
            <button data-testid="dnd-togglelock" onClick={onToggleLock}
              className="px-3 py-1.5 text-xs border rounded-lg flex items-center gap-1.5"
              style={card.status === 'locked'
                ? { color: '#fcd34d', borderColor: '#f59e0b40', background: '#f59e0b10' }
                : { color: '#6ee7b7', borderColor: '#10b98140', background: '#10b98110' }}>
              {card.status === 'locked' ? <><Unlock className="w-3 h-3" /> Unlock</> : <><Lock className="w-3 h-3" /> Vastklikken (canon)</>}
            </button>
          </>
        )}
      </div>
    </div>
  );
}


// ============================================================
// v6_dnd_gallery_media_001 — Upload-knop + Picker + Nieuwe-kaart modal
// ============================================================

function DnDUploadButton({ onUpload }) {
  const fileRef = useRef(null);
  const [busy, setBusy] = useState(false);
  return (
    <>
      <input ref={fileRef} type="file" accept="image/*" className="hidden"
        data-testid="dnd-media-upload-input"
        onChange={async e => {
          const f = e.target.files?.[0];
          if (!f) return;
          setBusy(true);
          try { await onUpload(f); }
          finally { setBusy(false); if (fileRef.current) fileRef.current.value = ''; }
        }} />
      <button data-testid="dnd-media-upload-btn"
        onClick={() => fileRef.current?.click()} disabled={busy}
        className="px-2 py-1 text-[10px] rounded border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/15 disabled:opacity-50 flex items-center gap-1">
        <Upload className="w-3 h-3" /> {busy ? 'Uploaden…' : 'Upload'}
      </button>
    </>
  );
}

function NewCardModal({ onCreate, onClose }) {
  const [begrip, setBegrip] = useState('');
  const [sense, setSense] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    if (!begrip.trim()) return;
    setBusy(true);
    try { await onCreate(begrip, sense); }
    finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={onClose}>
      <div data-testid="dnd-new-card-modal" onClick={e => e.stopPropagation()}
        className="bg-slate-950 border-2 border-emerald-500/40 rounded-xl p-5 w-full max-w-md">
        <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-400" /> Nieuwe D&amp;D kaart
        </h3>
        <p className="text-[11px] text-slate-400 mb-4">
          Maak een lege game-kaart aan. Vul daarna lagen, tags en foto's in.
        </p>
        <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">Begrip / titel</label>
        <input data-testid="dnd-new-card-begrip" value={begrip}
          onChange={e => setBegrip(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && submit()}
          autoFocus
          placeholder="Bijv. Eikenhouten Schild · De Smid · Mistmoeras…"
          className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-sm text-white mb-3" />

        <label className="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">Zintuig-kanaal (optioneel)</label>
        <div className="flex gap-1.5 mb-4">
          <button data-testid="dnd-new-card-sense-none" type="button" onClick={() => setSense('')}
            className={`px-2.5 py-1 rounded text-[11px] border ${!sense ? 'bg-slate-700 text-white border-slate-600' : 'border-slate-700 text-slate-400'}`}>
            geen
          </button>
          {Object.entries(SENSE_META).map(([id, m]) => (
            <button key={id} data-testid={`dnd-new-card-sense-${id}`} type="button" onClick={() => setSense(id)}
              className="px-2.5 py-1 rounded text-[11px] border"
              style={sense === id
                ? { background: m.color + '20', color: m.color, borderColor: m.color }
                : { borderColor: m.color + '40', color: m.color + 'aa' }}>
              {m.icon} {m.label}
            </button>
          ))}
        </div>

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800 rounded">Annuleer</button>
          <button data-testid="dnd-new-card-create" onClick={submit} disabled={busy || !begrip.trim()}
            className="px-4 py-1.5 text-xs bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/30 rounded flex items-center gap-1.5 disabled:opacity-50">
            <Plus className="w-3 h-3" /> {busy ? 'Aanmaken…' : 'Maak aan'}
          </button>
        </div>
      </div>
    </div>
  );
}

function ArchivePhotoPicker({ apiUrl, alreadyAttached, onPick, onClose }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState('all'); // all | game | other

  useEffect(() => {
    setLoading(true);
    fetch(`${apiUrl}/api/system-archive?category=foto`)
      .then(r => r.json())
      .then(d => setFiles(d.files || []))
      .catch(() => setFiles([]))
      .finally(() => setLoading(false));
  }, [apiUrl]);

  const isDnd = f => (f.tags || []).some(t => /^d&d$|game-card/i.test(t));
  const filtered = files.filter(f => {
    if (tab === 'game' && !isDnd(f)) return false;
    if (tab === 'other' && isDnd(f)) return false;
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (f.original_name || '').toLowerCase().includes(q)
        || (f.description || '').toLowerCase().includes(q)
        || (f.tags || []).some(t => (t || '').toLowerCase().includes(q));
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={onClose}>
      <div data-testid="dnd-archive-picker" onClick={e => e.stopPropagation()}
        className="bg-slate-950 border-2 border-amber-500/40 rounded-xl w-full max-w-4xl max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FolderOpen className="w-4 h-4 text-amber-400" /> Kies een foto uit Algemene foto's
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">{files.length} foto's beschikbaar. Klik om te koppelen.</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-5 py-2.5 border-b border-slate-800 flex flex-wrap items-center gap-2">
          <input data-testid="dnd-archive-search" value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Zoek op naam, tag of beschrijving…"
            className="flex-1 min-w-[160px] px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white" />
          <div className="flex gap-1">
            {[
              { id: 'all',   label: 'Alle' },
              { id: 'game',  label: '🎲 D&D / Game' },
              { id: 'other', label: 'Overige' },
            ].map(t => (
              <button key={t.id} data-testid={`dnd-archive-tab-${t.id}`}
                onClick={() => setTab(t.id)}
                className={`px-2.5 py-1 rounded text-[11px] ${tab === t.id ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'border border-slate-700 text-slate-400 hover:text-slate-200'}`}>
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <p className="text-center text-slate-500 text-sm py-12">Foto's laden…</p>
          ) : filtered.length === 0 ? (
            <p className="text-center text-slate-500 text-sm py-12">
              Geen foto's gevonden. Upload eerst foto's via Beheer → Archief → Foto.
            </p>
          ) : (
            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2">
              {filtered.map(f => {
                const url = f.download_url;
                const attached = (alreadyAttached || []).includes(url);
                return (
                  <button key={f.id} data-testid={`dnd-archive-pick-${f.id}`}
                    onClick={() => !attached && onPick(url)} disabled={attached}
                    title={f.original_name}
                    className={`group relative aspect-square rounded-lg overflow-hidden border-2 transition-all ${attached ? 'border-emerald-500 opacity-70 cursor-not-allowed' : 'border-slate-700 hover:border-amber-500'}`}>
                    <img src={`${apiUrl}${url}`} alt="" className="w-full h-full object-cover" />
                    <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 to-transparent p-1.5">
                      <p className="text-[9px] text-white truncate">{f.original_name}</p>
                    </div>
                    {attached && (
                      <div className="absolute top-1 right-1 w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center">
                        <Check className="w-3 h-3 text-white" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
