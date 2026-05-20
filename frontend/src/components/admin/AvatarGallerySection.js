import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Upload, Trash2, Image as ImageIcon, Plus, Star } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * Avatar Galerij beheer — alleen voor admins (gradatie ≤ 2)
 * Bedoeld als sub-sectie binnen Instellingen → Beeld tab.
 */
export function AvatarGallerySection({ adminId, isAdmin }) {
  const [items, setItems] = useState([]);
  const [title, setTitle] = useState('');
  const [tags, setTags] = useState('');
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState(null);
  const fileRef = useRef(null);

  const load = useCallback(() => {
    fetch(`${API}/api/avatar/gallery`)
      .then(r => r.json()).then(d => setItems(d.avatars || []))
      .catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);

  const flash = (type, text) => { setMsg({ type, text }); setTimeout(() => setMsg(null), 3000); };

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
    if (!window.confirm(`Verwijder "${t}" uit galerij?`)) return;
    const r = await fetch(`${API}/api/avatar/gallery/${id}?viewer_id=${adminId}`, { method: 'DELETE' });
    if (r.ok) { flash('ok', 'Verwijderd'); load(); }
    else flash('err', 'Verwijderen mislukt');
  };

  if (!isAdmin) return null;

  return (
    <div className="space-y-4">
      {/* Upload form */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-4 space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <Plus className="w-4 h-4 text-purple-400" />
          <h4 className="text-sm font-bold text-white">Nieuwe avatar toevoegen</h4>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input
            type="text" value={title} onChange={e => setTitle(e.target.value)}
            placeholder="Titel (verplicht, bijv. 'Roadkill Logo')"
            data-testid="gallery-title-input"
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none"
          />
          <input
            type="text" value={tags} onChange={e => setTags(e.target.value)}
            placeholder="Tags (komma-gescheiden, optioneel)"
            data-testid="gallery-tags-input"
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none"
          />
        </div>
        <input ref={fileRef} type="file" accept="image/*" data-testid="gallery-file-input"
          className="text-xs text-slate-400 file:mr-3 file:px-3 file:py-1.5 file:bg-purple-500/20 file:text-purple-400 file:border-0 file:rounded-lg file:text-xs file:cursor-pointer" />
        <button onClick={upload} disabled={uploading}
          data-testid="gallery-upload-btn"
          className="px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 border border-purple-500/40 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50">
          <Upload className="w-4 h-4" />
          {uploading ? 'Uploaden...' : 'Toevoegen aan galerij'}
        </button>
        {msg && (
          <p className={`text-xs ${msg.type === 'ok' ? 'text-green-400' : 'text-red-400'}`}>{msg.text}</p>
        )}
      </div>

      {/* Gallery list */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <ImageIcon className="w-4 h-4 text-purple-400" />
          <h4 className="text-sm font-bold text-white">Galerij ({items.length})</h4>
        </div>
        {items.length === 0 ? (
          <p className="text-xs text-slate-500 italic py-3 text-center">Nog geen avatars in galerij.</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {items.map(a => (
              <div key={a.id} data-testid={`admin-gallery-${a.id}`} className="rounded-xl overflow-hidden bg-slate-900/60 border border-slate-800 group">
                <div className="relative aspect-square">
                  <img src={`${API}/api/avatar/gallery/${a.id}/image`} alt={a.title}
                    className="w-full h-full object-cover" />
                  {a.seed && (
                    <span className="absolute top-1.5 left-1.5 px-1.5 py-0.5 bg-amber-500/90 text-[9px] text-white font-bold rounded flex items-center gap-1">
                      <Star className="w-2.5 h-2.5" /> SEED
                    </span>
                  )}
                </div>
                <div className="p-2.5">
                  <p className="text-xs font-medium text-white truncate" title={a.title}>{a.title}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">
                    {a.width}×{a.height} · {(a.size_bytes / 1024).toFixed(0)}KB
                  </p>
                  {a.tags?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {a.tags.slice(0, 3).map(t => (
                        <span key={t} className="text-[9px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded">{t}</span>
                      ))}
                    </div>
                  )}
                  <button onClick={() => remove(a.id, a.title)}
                    data-testid={`gallery-delete-${a.id}`}
                    className="mt-2 w-full px-2 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded flex items-center justify-center gap-1 text-[10px]">
                    <Trash2 className="w-3 h-3" /> Verwijder
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default AvatarGallerySection;
