import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Upload, Trash2, Image as ImageIcon, Plus, Star, Users, ShieldAlert, Lock, Pencil, X, Save } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * Avatar Galerij beheer — alleen voor admins (gradatie ≤ 2)
 * v5_avatar_gallery_split_001 — 2 sub-tabs:
 *   - 'user'   : Gebruikers-avatars (vrij te kiezen door iedereen) — delete actief
 *   - 'system' : Systeem-avatars (locked + bot/spark owners) — delete verborgen,
 *                edit beschikbaar via Beheer → Gebruikers → Avatar Beheer (pencil)
 */
export function AvatarGallerySection({ adminId, isAdmin }) {
  const [items, setItems] = useState([]);
  const [activeTab, setActiveTab] = useState('user');
  const [title, setTitle] = useState('');
  const [tags, setTags] = useState('');
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState(null);
  const [confirming, setConfirming] = useState(null); // {id, title} or null
  const [editing, setEditing] = useState(null); // {id, title, tags, bot_owner, category, locked} or null
  const [editTitle, setEditTitle] = useState('');
  const [editTags, setEditTags] = useState('');
  const [editBotOwner, setEditBotOwner] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);
  const fileRef = useRef(null);

  const load = useCallback(() => {
    fetch(`${API}/api/avatar/gallery`)
      .then(r => r.json()).then(d => setItems(d.avatars || []))
      .catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);

  const flash = (type, text) => { setMsg({ type, text }); setTimeout(() => setMsg(null), 3500); };

  const upload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) { flash('err', 'Kies een afbeelding'); return; }
    if (!title.trim()) { flash('err', 'Titel is verplicht'); return; }
    setUploading(true);
    const fd = new FormData();
    fd.append('file', file);
    fd.append('title', title.trim());
    fd.append('tags', tags.trim());
    fd.append('uploader_id', adminId);
    try {
      const r = await fetch(`${API}/api/avatar/gallery`, { method: 'POST', body: fd });
      const d = await r.json();
      if (r.ok && d.success) {
        flash('ok', `"${d.avatar.title}" toegevoegd`);
        setTitle(''); setTags('');
        if (fileRef.current) fileRef.current.value = '';
        load();
      } else flash('err', d.detail || 'Upload mislukt');
    } catch (e) { flash('err', e.message); }
    finally { setUploading(false); }
  };

  const remove = async (id, t) => {
    setConfirming(null);
    const r = await fetch(`${API}/api/avatar/gallery/${id}?viewer_id=${adminId}`, { method: 'DELETE' });
    const d = await r.json().catch(() => ({}));
    if (r.ok && d.success && (d.removed ?? 1) >= 1) {
      flash('ok', `"${t}" verwijderd uit galerij`);
      load();
    } else if (r.ok && d.removed === 0) {
      flash('err', `Niet gevonden of beschermd (geen wijziging)`);
      load();
    } else {
      flash('err', `Verwijderen mislukt (HTTP ${r.status})`);
    }
  };

  // v6_avatar_edit_001 — Open edit-modal voor titel/tags/bot_owner
  const startEdit = (avatar) => {
    setEditing({
      id: avatar.id,
      title: avatar.title || '',
      tags: (avatar.tags || []).join(', '),
      bot_owner: avatar.bot_owner || '',
      category: avatar.category || 'user',
      locked: !!avatar.locked,
    });
    setEditTitle(avatar.title || '');
    setEditTags((avatar.tags || []).join(', '));
    setEditBotOwner(avatar.bot_owner || '');
  };

  const saveEdit = async () => {
    if (!editing) return;
    if (!editTitle.trim()) { flash('err', 'Titel mag niet leeg zijn'); return; }
    setSavingEdit(true);
    try {
      const payload = {
        viewer_id: adminId,
        title: editTitle.trim(),
        tags: editTags.split(',').map(t => t.trim()).filter(Boolean),
      };
      // Alleen bot_owner meesturen als de avatar locked/system is (admin-relevant)
      if (editing.locked || editing.category === 'system') {
        payload.bot_owner = editBotOwner.trim();
      }
      const r = await fetch(`${API}/api/avatar/gallery/${editing.id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const d = await r.json().catch(() => ({}));
      if (r.ok && d.success) {
        flash('ok', `"${d.avatar.title}" bijgewerkt`);
        setEditing(null);
        load();
      } else {
        flash('err', d.detail || `Bewerken mislukt (HTTP ${r.status})`);
      }
    } catch (e) {
      flash('err', e.message);
    } finally {
      setSavingEdit(false);
    }
  };

  if (!isAdmin) return null;

  // Splits in 2 categorieën
  const userAvatars = items.filter(a => !a.locked && a.category !== 'system');
  const systemAvatars = items.filter(a => a.locked || a.category === 'system');
  const visible = activeTab === 'user' ? userAvatars : systemAvatars;

  return (
    <div className="space-y-4">
      {/* Upload form */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-4 space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <Plus className="w-4 h-4 text-amber-400" />
          <h4 className="text-sm font-bold text-white">Nieuwe avatar toevoegen</h4>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input
            type="text" value={title} onChange={e => setTitle(e.target.value)}
            placeholder="Titel (verplicht, bijv. 'Roadkill Logo')"
            data-testid="gallery-title-input"
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
          />
          <input
            type="text" value={tags} onChange={e => setTags(e.target.value)}
            placeholder="Tags (komma-gescheiden, optioneel)"
            data-testid="gallery-tags-input"
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
          />
        </div>
        <input ref={fileRef} type="file" accept="image/*" data-testid="gallery-file-input"
          className="text-xs text-slate-400 file:mr-3 file:px-3 file:py-1.5 file:bg-amber-500/20 file:text-amber-400 file:border-0 file:rounded-lg file:text-xs file:cursor-pointer" />
        <button onClick={upload} disabled={uploading}
          data-testid="gallery-upload-btn"
          className="px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/40 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50">
          <Upload className="w-4 h-4" />
          {uploading ? 'Uploaden...' : 'Toevoegen aan galerij'}
        </button>
        {msg && (
          <div data-testid="gallery-msg"
            className={`text-xs px-3 py-2 rounded-lg border ${msg.type === 'ok' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' : 'bg-red-500/10 text-red-300 border-red-500/30'}`}>
            {msg.text}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 p-1 bg-slate-800/40 rounded-xl w-fit">
        <button
          data-testid="gallery-cat-tab-user"
          onClick={() => setActiveTab('user')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-colors ${
            activeTab === 'user' ? 'bg-amber-500/20 text-amber-300' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          Gebruikers-avatars <span className="opacity-60">({userAvatars.length})</span>
        </button>
        <button
          data-testid="gallery-cat-tab-system"
          onClick={() => setActiveTab('system')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-colors ${
            activeTab === 'system' ? 'bg-amber-500/20 text-amber-300' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          Systeem-avatars <span className="opacity-60">({systemAvatars.length})</span>
        </button>
      </div>

      {activeTab === 'system' && (
        <div className="px-3 py-2 bg-amber-500/5 border border-amber-500/20 rounded-lg">
          <p className="text-[11px] text-amber-300/90">
            🛡️ Systeem-avatars zijn gereserveerd voor Spark/bots. Gebruikers kunnen ze niet zelf kiezen.
            Verwijderen is hier uitgeschakeld om hun rol in de wereld te beschermen — pas eerst de eigenaar/lock aan
            via <strong>Beheer → Gebruikers → kies user → Avatar Beheer → pencil</strong> als je er echt vanaf wilt.
          </p>
        </div>
      )}

      {/* Gallery list */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <ImageIcon className="w-4 h-4 text-amber-400" />
          <h4 className="text-sm font-bold text-white">
            {activeTab === 'user' ? 'Gebruikers-avatars' : 'Systeem-avatars'} ({visible.length})
          </h4>
        </div>
        {visible.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-3 text-center">Nog geen avatars in deze categorie.</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {visible.map(a => (
              <div key={a.id} data-testid={`admin-gallery-${a.id}`} className="rounded-xl overflow-hidden bg-slate-900/60 border border-slate-800 group">
                <div className="relative aspect-square">
                  <img src={`${API}/api/avatar/gallery/${a.id}/image`} alt={a.title}
                    className="w-full h-full object-cover" />
                  {a.seed && (
                    <span className="absolute top-1.5 left-1.5 px-1.5 py-0.5 bg-amber-500/90 text-[9px] text-white font-bold rounded flex items-center gap-1">
                      <Star className="w-2.5 h-2.5" /> SEED
                    </span>
                  )}
                  {a.locked && (
                    <span className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-amber-500/90 border border-amber-300/60 flex items-center justify-center"
                      title={`Beschermd — eigenaar: ${a.bot_owner || 'systeem'}`}>
                      <Lock className="w-2.5 h-2.5 text-slate-950" />
                    </span>
                  )}
                </div>
                <div className="p-2.5">
                  <p className="text-xs font-medium text-white truncate" title={a.title}>{a.title}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">
                    {a.width}×{a.height} · {(a.size_bytes / 1024).toFixed(0)}KB
                    {a.bot_owner && <span className="ml-1 text-amber-400">· {a.bot_owner}</span>}
                  </p>
                  {a.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {a.tags.slice(0, 3).map(t => (
                        <span key={t} className="text-[9px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded">{t}</span>
                      ))}
                    </div>
                  )}
                  {activeTab === 'user' ? (
                    <div className="mt-2 flex items-center gap-1">
                      <button onClick={() => startEdit(a)}
                        data-testid={`gallery-edit-${a.id}`}
                        title="Bewerken"
                        className="flex-1 px-2 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded flex items-center justify-center gap-1 text-[10px]">
                        <Pencil className="w-3 h-3" /> Bewerk
                      </button>
                      <button onClick={() => setConfirming({ id: a.id, title: a.title })}
                        data-testid={`gallery-delete-${a.id}`}
                        className="flex-1 px-2 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded flex items-center justify-center gap-1 text-[10px]">
                        <Trash2 className="w-3 h-3" /> Verwijder
                      </button>
                    </div>
                  ) : (
                    <div className="mt-2 flex items-center gap-1">
                      <button onClick={() => startEdit(a)}
                        data-testid={`gallery-edit-${a.id}`}
                        title="Bewerk titel/tags/eigenaar"
                        className="flex-1 px-2 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded flex items-center justify-center gap-1 text-[10px]">
                        <Pencil className="w-3 h-3" /> Bewerk
                      </button>
                      <button disabled
                        data-testid={`gallery-locked-${a.id}`}
                        title="Beschermd. Verwijder eerst de lock via Beheer → Gebruikers → Avatar Beheer."
                        className="flex-1 px-2 py-1 bg-slate-800/50 text-slate-500 border border-slate-700/50 rounded flex items-center justify-center gap-1 text-[10px] cursor-not-allowed">
                        <Lock className="w-3 h-3" /> Beschermd
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* v6_avatar_edit_001 — Edit modal */}
      {editing && (
        <div data-testid="gallery-edit-modal"
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => !savingEdit && setEditing(null)}>
          <div className="bg-slate-900 border border-amber-500/30 rounded-2xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-amber-500/15 border border-amber-500/40 flex items-center justify-center">
                <Pencil className="w-5 h-5 text-amber-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-white">Avatar bewerken</h3>
                <p className="text-[11px] text-slate-500 truncate">ID: {editing.id}</p>
              </div>
              <button onClick={() => !savingEdit && setEditing(null)} className="p-1 text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider">Titel *</label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  data-testid="gallery-edit-title"
                  className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider">Tags (komma-gescheiden)</label>
                <input
                  type="text"
                  value={editTags}
                  onChange={e => setEditTags(e.target.value)}
                  placeholder="bv. mannelijk, fantasy, dark"
                  data-testid="gallery-edit-tags"
                  className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
              </div>
              {(editing.locked || editing.category === 'system') && (
                <div>
                  <label className="text-[10px] text-amber-400 uppercase tracking-wider">Bot-eigenaar (system)</label>
                  <input
                    type="text"
                    value={editBotOwner}
                    onChange={e => setEditBotOwner(e.target.value)}
                    placeholder='bv. "bot-spark" of leeg om los te koppelen'
                    data-testid="gallery-edit-bot-owner"
                    className="mt-1 w-full px-3 py-2 bg-slate-800 border border-amber-500/30 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">Leeg laten = ontkoppelen van bot. Lock blijft staan.</p>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 justify-end mt-5">
              <button onClick={() => setEditing(null)} disabled={savingEdit}
                data-testid="gallery-edit-cancel"
                className="px-3 py-2 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-50">
                Annuleer
              </button>
              <button onClick={saveEdit} disabled={savingEdit || !editTitle.trim()}
                data-testid="gallery-edit-save"
                className="px-3 py-2 rounded-lg text-xs font-medium bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/40 flex items-center gap-2 disabled:opacity-50">
                <Save className="w-3 h-3" /> {savingEdit ? 'Opslaan...' : 'Opslaan'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm modal */}
      {confirming && (
        <div data-testid="gallery-delete-confirm"
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setConfirming(null)}>
          <div className="bg-slate-900 border border-red-500/30 rounded-2xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-red-500/15 border border-red-500/40 flex items-center justify-center">
                <Trash2 className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Avatar verwijderen?</h3>
                <p className="text-[11px] text-slate-500">Permanente actie — niet ongedaan te maken</p>
              </div>
            </div>
            <p className="text-sm text-slate-300 mb-4">
              Weet je zeker dat je <strong className="text-red-300">"{confirming.title}"</strong> uit de galerij wilt verwijderen?
              Gebruikers die deze avatar momenteel hebben gekozen, krijgen weer de standaard initialen.
            </p>
            <div className="flex items-center gap-2 justify-end">
              <button onClick={() => setConfirming(null)}
                data-testid="gallery-delete-cancel"
                className="px-3 py-2 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700">
                Annuleer
              </button>
              <button onClick={() => remove(confirming.id, confirming.title)}
                data-testid="gallery-delete-confirm-btn"
                className="px-3 py-2 rounded-lg text-xs font-medium bg-red-500/20 text-red-300 hover:bg-red-500/30 border border-red-500/40 flex items-center gap-2">
                <Trash2 className="w-3 h-3" /> Ja, verwijder permanent
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AvatarGallerySection;
