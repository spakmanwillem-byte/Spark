import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Search, Upload, Trash2, X, File as FileIcon,
  Image as ImageIcon, Music, Video, Download, Edit3, Save, Tag,
  MessageSquare, Server, FileText, Users, Code2
} from 'lucide-react';
import { AvatarGallerySection } from './AvatarGallerySection';
import { DnDGallerySection } from './DnDGallerySection';
import { LogsBrowser } from './LogsBrowser';

const API = process.env.REACT_APP_BACKEND_URL;

const CATEGORIES = [
  { id: 'bestanden', label: 'Bestanden', icon: FileIcon, color: '#64748b' },
  { id: 'foto', label: 'Foto', icon: ImageIcon, color: '#22c55e' },
  { id: 'geluiden', label: 'Geluiden', icon: Music, color: '#a855f7' },
  { id: 'filmpjes', label: 'Filmpjes', icon: Video, color: '#ec4899' },
  { id: 'dialogen', label: 'Dialogen', icon: MessageSquare, color: '#06b6d4' },
  // v5_logs_to_analytics_001 — Logs-tab verhuisd naar Beheer → Analytics → LOGS
  // (LogsBrowser nog steeds beschikbaar als legacy fallback, maar UI-entry hier weggehaald)
];

function formatBytes(n) {
  if (!n) return '0 B';
  const k = 1024, u = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(n) / Math.log(k));
  return `${(n / Math.pow(k, i)).toFixed(i === 0 ? 0 : 1)} ${u[i]}`;
}

export function SystemArchive({ currentUserId, isAdmin = true }) {
  const fileInputRef = useRef(null);

  const [activeTab, setActiveTab] = useState('bestanden');
  // v5_foto_subtabs_001 — sub-tabs binnen Foto: algemeen vs avatars
  const [fotoSubTab, setFotoSubTab] = useState('algemeen');
  // v5_kbv2_media_002 — bron-filter: 'alle' | 'kbv2' (kennis-kaart gebonden) | 'los' (overig)
  const [sourceFilter, setSourceFilter] = useState('alle');
  const [files, setFiles] = useState([]);
  const [stats, setStats] = useState(null);
  const [availableTags, setAvailableTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});

  const load = useCallback(async () => {
    // Logs-tab gebruikt eigen browser, niet system-archive API
    if (activeTab === 'logs') {
      setLoading(false);
      setFiles([]);
      return;
    }
    setLoading(true);
    const params = new URLSearchParams({ category: activeTab });
    if (search) params.append('q', search);
    if (tagFilter) params.append('tag', tagFilter);
    // v5_kbv2_media_002 — bron-filter via tag-query
    if (sourceFilter === 'kbv2') params.append('tag', 'kbv2');
    // v6_roadkill_merch_archive_001 — merch sub-tab filter
    if (activeTab === 'foto' && fotoSubTab === 'merch') params.append('tag', 'roadkill_merch');
    try {
      const res = await fetch(`${API}/api/system-archive?${params}`).then(r => r.json());
      let arr = res.files || [];
      // 'los' = alles behalve kbv2-gelinkte items
      if (sourceFilter === 'los') {
        arr = arr.filter(f => !(f.tags || []).includes('kbv2') && !f.linked_card_id);
      }
      setFiles(arr);
      setStats(res.stats || null);
      setAvailableTags(res.available_tags || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [activeTab, search, tagFilter, sourceFilter, fotoSubTab]);

  useEffect(() => { load(); }, [load]);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('category', activeTab); // forceer huidige tab
      if (currentUserId) fd.append('uploaded_by', currentUserId);
      const res = await fetch(`${API}/api/system-archive/upload`, { method: 'POST', body: fd });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload mislukt' }));
        throw new Error(err.detail || 'Upload mislukt');
      }
      await load();
    } catch (err) {
      setUploadError(err.message || 'Upload fout');
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const deleteFile = async (fileId) => {
    if (!confirm('Dit systeem-bestand permanent verwijderen?')) return;
    await fetch(`${API}/api/system-archive/${fileId}`, { method: 'DELETE' });
    await load();
  };

  const startEdit = (f) => {
    setEditingId(f.id);
    setEditForm({
      original_name: f.original_name || '',
      description: f.description || '',
      tags: (f.tags || []).join(', '),
    });
  };

  const saveEdit = async () => {
    await fetch(`${API}/api/system-archive/${editingId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        original_name: editForm.original_name,
        description: editForm.description,
        tags: editForm.tags.split(',').map(t => t.trim()).filter(Boolean),
      }),
    });
    setEditingId(null);
    await load();
  };

  const activeCat = CATEGORIES.find(c => c.id === activeTab) || CATEGORIES[0];

  return (
    <div data-testid="system-archive" className="space-y-4">
      {/* Header */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
            <Server className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-base font-bold text-white leading-tight">Systeem Archief</h3>
            <p className="text-[10px] text-slate-500 uppercase tracking-wider">
              Admin-opslag · {stats?.total_files || 0} bestanden · {formatBytes(stats?.total_size_bytes || 0)}
            </p>
          </div>
          <input ref={fileInputRef} type="file" data-testid="sys-archive-file-input"
            onChange={handleUpload} className="hidden" />
          <button data-testid="sys-archive-upload-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-60">
            <Upload className="w-3.5 h-3.5" /> {uploading ? 'Bezig...' : `Upload ${activeCat.label.toLowerCase()}`}
          </button>
        </div>

        {uploadError && (
          <div className="mb-2 px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
            {uploadError}
          </div>
        )}

        {/* Tabs */}
        <div className="flex overflow-x-auto gap-0 -mb-px">
          {CATEGORIES.map(c => {
            const isActive = activeTab === c.id;
            const count = stats?.counts?.[c.id] ?? 0;
            return (
              <button key={c.id} data-testid={`sys-tab-${c.id}`}
                onClick={() => { setActiveTab(c.id); setTagFilter(''); }}
                className="relative flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors whitespace-nowrap flex-shrink-0"
                style={{ color: isActive ? c.color : '#94a3b8' }}>
                <c.icon className="w-3.5 h-3.5" />
                {c.label}
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 ml-0.5">{count}</span>
                {isActive && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full" style={{ background: c.color }} />}
              </button>
            );
          })}
        </div>
      </div>

      {/* v5_logs_to_analytics_001 — hyperlink-sectie voor module-trace logs in Bestanden-tab */}
      {activeTab === 'bestanden' && <LogsHyperlinkSection apiBase={API} />}

      {/* Dialoog uitleg banner */}
      {activeTab === 'dialogen' && (
        <div className="bg-cyan-500/5 border border-cyan-500/20 rounded-xl p-3">
          <div className="flex items-start gap-2">
            <FileText className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
            <div className="text-[11px] text-slate-400 leading-relaxed">
              <p className="text-cyan-300 font-medium mb-0.5">Dialoog-archief — leer-materiaal voor Spark</p>
              <p>Upload teksten van gesprekken, dialogen, scripts of oefen-gesprekken (.txt, .md, .json, .srt). Tag ze met types (rauw, afscheid, vreugde, delen, etc.) zodat Spark later via een leer-module kan herkennen hoe gesprekken contextueel verlopen en hoe te reageren.</p>
            </div>
          </div>
        </div>
      )}

      {/* v5_spark_logger_001 — Logs tab rendert eigen browser */}
      {activeTab === 'logs' && <LogsBrowser />}

      {/* v5_foto_subtabs_001 — Foto sub-tabs (Algemene foto's / Avatar Galerij / D&D Galerij) */}
      {activeTab === 'foto' && (
        <div className="flex items-center gap-1 p-1 bg-slate-800/40 rounded-xl w-fit">
          <button
            data-testid="foto-subtab-algemeen"
            onClick={() => setFotoSubTab('algemeen')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              fotoSubTab === 'algemeen' ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" />
            Algemene foto's
          </button>
          <button
            data-testid="foto-subtab-avatars"
            onClick={() => setFotoSubTab('avatars')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              fotoSubTab === 'avatars' ? 'bg-purple-500/20 text-purple-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            Avatar Galerij
          </button>
          {/* v6_dnd_gallery_001 — D&D galerij naast avatars */}
          <button
            data-testid="foto-subtab-dnd"
            onClick={() => setFotoSubTab('dnd')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              fotoSubTab === 'dnd' ? 'bg-amber-500/20 text-amber-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            D&amp;D Galerij
          </button>
          {/* v6_roadkill_merch_archive_001 — Roadkill Merch galerij */}
          <button
            data-testid="foto-subtab-merch"
            onClick={() => setFotoSubTab('merch')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              fotoSubTab === 'merch' ? 'bg-red-500/20 text-red-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Tag className="w-3.5 h-3.5" />
            Roadkill Merch
          </button>
        </div>
      )}

      {/* Avatar Galerij sub-content (verbergt search/grid van system-archive) */}
      {activeTab === 'foto' && fotoSubTab === 'avatars' && (
        <div data-testid="foto-avatars-pane" className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
          <p className="text-[11px] text-slate-400 mb-3">
            Voorbeeld-avatars die <span className="text-purple-300">alle users</span> kunnen kiezen als profielfoto via Mijn Profiel → Avatar.
            Eigen user-portretten worden apart opgeslagen en zijn alleen voor het eigen profiel.
          </p>
          <AvatarGallerySection adminId={currentUserId} isAdmin={isAdmin} />
        </div>
      )}

      {/* v6_dnd_gallery_001 — D&D Galerij sub-content */}
      {activeTab === 'foto' && fotoSubTab === 'dnd' && (
        <div data-testid="foto-dnd-pane" className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
          <DnDGallerySection adminId={currentUserId} isAdmin={isAdmin} />
        </div>
      )}

      {/* v5_kbv2_media_002 — bron sub-tabs binnen media-categorieën */}
      {['foto', 'geluiden', 'filmpjes'].includes(activeTab) && !(activeTab === 'foto' && (fotoSubTab === 'avatars' || fotoSubTab === 'dnd' || fotoSubTab === 'merch')) && (
        <div className="flex items-center gap-1.5">
          {[
            { id: 'alle',  label: 'Alles' },
            { id: 'kbv2',  label: 'Kennis-kaart', icon: '🧠' },
            { id: 'los',   label: 'Los', icon: '📎' },
          ].map(opt => (
            <button key={opt.id}
              data-testid={`sys-source-${opt.id}`}
              onClick={() => setSourceFilter(opt.id)}
              className={`px-2.5 py-1 rounded text-[11px] font-medium border transition-colors ${
                sourceFilter === opt.id
                  ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                  : 'border-slate-700 text-slate-400 hover:text-slate-200'
              }`}>
              {opt.icon ? <span className="mr-1">{opt.icon}</span> : null}{opt.label}
            </button>
          ))}
        </div>
      )}

      {/* Search + tag filter (verberg in avatars-mode + logs-mode) */}
      {activeTab !== 'logs' && !(activeTab === 'foto' && (fotoSubTab === 'avatars' || fotoSubTab === 'dnd')) && (
        <div className="flex flex-wrap gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
            <input data-testid="sys-archive-search" type="text"
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder={`Zoek in ${activeCat.label.toLowerCase()}...`}
              className="w-full pl-8 pr-8 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
            {search && (
              <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white">
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
          {activeTab === 'dialogen' && availableTags.length > 0 && (
            <select value={tagFilter} onChange={e => setTagFilter(e.target.value)}
              data-testid="sys-archive-tag-filter"
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white">
              <option value="">Alle tags</option>
              {availableTags.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          )}
        </div>
      )}

      {/* Content (verberg in avatars-mode + logs-mode) */}
      {activeTab !== 'logs' && !(activeTab === 'foto' && (fotoSubTab === 'avatars' || fotoSubTab === 'dnd')) && (
        loading ? (
          <div className="text-center py-12 text-xs text-slate-500">Laden...</div>
        ) : files.length === 0 ? (
          <div className="text-center py-12">
            <activeCat.icon className="w-10 h-10 text-slate-700 mx-auto mb-2" />
            <p className="text-sm text-slate-400 mb-1">
              {search ? `Geen ${activeCat.label.toLowerCase()} matchen "${search}"` : `Nog geen ${activeCat.label.toLowerCase()}`}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {files.map(f => (
              <SystemFileCard key={f.id}
                file={f}
                category={CATEGORIES.find(c => c.id === f.category) || CATEGORIES[0]}
                availableTags={availableTags}
                isEditing={editingId === f.id}
                editForm={editForm}
                setEditForm={setEditForm}
                onStartEdit={() => startEdit(f)}
                onSave={saveEdit}
                onCancel={() => setEditingId(null)}
                onDelete={() => deleteFile(f.id)}
              />
            ))}
          </div>
        )
      )}
    </div>
  );
}

function SystemFileCard({ file, category, availableTags, isEditing, editForm, setEditForm, onStartEdit, onSave, onCancel, onDelete }) {
  const Icon = category.icon;
  const downloadUrl = `${API}${file.download_url}`;
  const ts = new Date(file.uploaded_at).toLocaleString('nl-NL', { dateStyle: 'short', timeStyle: 'short' });

  const renderPreview = () => {
    if (file.category === 'foto') {
      return <img src={downloadUrl} alt={file.original_name} className="w-full h-28 object-cover rounded-lg bg-slate-800" loading="lazy" />;
    }
    if (file.category === 'geluiden') {
      return <audio src={downloadUrl} controls className="w-full mt-2" preload="none" />;
    }
    if (file.category === 'filmpjes') {
      return <video src={downloadUrl} controls className="w-full h-28 rounded-lg bg-black" preload="none" />;
    }
    return null;
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
      {renderPreview()}
      <div className="p-3">
        {isEditing ? (
          <div className="space-y-2">
            <input type="text" value={editForm.original_name}
              onChange={e => setEditForm({ ...editForm, original_name: e.target.value })}
              className="w-full px-2 py-1 bg-slate-800 border border-slate-700 rounded text-sm text-white" />
            <input type="text" value={editForm.description}
              onChange={e => setEditForm({ ...editForm, description: e.target.value })}
              placeholder="Beschrijving"
              className="w-full px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-white" />
            <input type="text" value={editForm.tags}
              onChange={e => setEditForm({ ...editForm, tags: e.target.value })}
              placeholder={file.category === 'dialogen' ? "tags: rauw, afscheid, vreugde..." : "tags, komma-gescheiden"}
              className="w-full px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-white" />
            {file.category === 'dialogen' && availableTags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {availableTags.slice(0, 12).map(t => (
                  <button key={t} type="button"
                    onClick={() => {
                      const current = editForm.tags.split(',').map(x => x.trim()).filter(Boolean);
                      const next = current.includes(t) ? current.filter(x => x !== t) : [...current, t];
                      setEditForm({ ...editForm, tags: next.join(', ') });
                    }}
                    className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 hover:bg-cyan-500/20 hover:text-cyan-400 text-slate-400">
                    +{t}
                  </button>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <button onClick={onSave} className="flex-1 py-1 bg-green-500/20 text-green-400 rounded text-xs flex items-center justify-center gap-1">
                <Save className="w-3 h-3" /> Opslaan
              </button>
              <button onClick={onCancel} className="flex-1 py-1 bg-slate-800 text-slate-400 rounded text-xs flex items-center justify-center gap-1">
                <X className="w-3 h-3" /> Annuleren
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-start gap-2 mb-1">
              <Icon className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: category.color }} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate" title={file.original_name}>{file.original_name}</p>
                <p className="text-[10px] text-slate-500">{formatBytes(file.size_bytes)} · {ts}</p>
              </div>
              {file.scan_status === 'pending' && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 flex-shrink-0">scan pending</span>
              )}
              {file.linked_card_id && (
                <span data-testid="sys-kbv2-badge" className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 flex-shrink-0" title={`Gekoppeld aan kennis-kaart ${file.linked_card_id}`}>
                  🧠 kaart
                </span>
              )}
            </div>
            {file.description && <p className="text-xs text-slate-400 mt-1.5 mb-1">{file.description}</p>}
            {file.tags?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {file.tags.map((t, i) => (
                  <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 flex items-center gap-0.5">
                    <Tag className="w-2 h-2" />{t}
                  </span>
                ))}
              </div>
            )}
            <div className="flex items-center gap-1 mt-2 pt-2 border-t border-slate-800/50">
              <a href={downloadUrl} download={file.original_name}
                className="flex items-center gap-1 px-2 py-1 text-[10px] text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors">
                <Download className="w-3 h-3" /> Download
              </a>
              <button onClick={onStartEdit}
                className="flex items-center gap-1 px-2 py-1 text-[10px] text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors">
                <Edit3 className="w-3 h-3" /> Bewerk
              </button>
              <button onClick={onDelete}
                className="flex items-center gap-1 px-2 py-1 text-[10px] text-red-400 hover:bg-red-500/10 rounded transition-colors ml-auto">
                <Trash2 className="w-3 h-3" /> Verwijder
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default SystemArchive;


/**
 * LogsHyperlinkSection (v5_logs_to_analytics_001)
 * ----------------------------------------------
 * Toont in Bestanden-tab een sectie met hyperlinks naar module-trace logs.
 * Klik = download van .jsonl bestand. Vol-detail browser zit in Analytics → LOGS.
 */
function LogsHyperlinkSection({ apiBase }) {
  const [tree, setTree] = React.useState(null);
  React.useEffect(() => {
    fetch(`${apiBase}/api/admin/logs/index`)
      .then(r => r.json())
      .then(d => setTree(d.tree || {}))
      .catch(() => setTree({}));
  }, [apiBase]);

  // Plat-de-tree-uit naar {date: [module]}
  const flat = [];
  if (tree) {
    Object.entries(tree).sort().reverse().forEach(([y, mm]) => {
      Object.entries(mm).sort().reverse().forEach(([m, dd]) => {
        Object.entries(dd).sort().reverse().forEach(([d, modules]) => {
          flat.push({ date: `${y}-${m}-${d}`, modules: modules || [] });
        });
      });
    });
  }
  const recent = flat.slice(0, 7);

  return (
    <div data-testid="logs-hyperlink-section" className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3 space-y-2">
      <div className="flex items-start gap-2">
        <FileText className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="text-[11px] text-slate-400 leading-relaxed flex-1">
          <p className="text-amber-300 font-medium mb-0.5">Module-trace logs (JSONL)</p>
          <p>Volledige browser zit in <span className="text-amber-300">Beheer → Analytics → LOGS</span>. Hieronder snelkoppelingen om individuele log-bestanden te downloaden.</p>
        </div>
      </div>
      {tree === null && <div className="text-[10px] text-slate-500">Laden…</div>}
      {tree && recent.length === 0 && <div className="text-[10px] text-slate-500">Nog geen log-bestanden.</div>}
      {recent.map(({ date, modules }) => (
        <div key={date} className="flex items-center gap-2 flex-wrap pt-1 border-t border-slate-800/50">
          <span className="text-[10px] text-slate-500 font-mono w-20">{date}</span>
          {modules.map(mod => (
            <a key={mod}
              data-testid={`log-link-${date}-${mod}`}
              href={`${apiBase}/api/admin/logs/download?date=${date}&module=${mod}`}
              target="_blank" rel="noreferrer"
              className="text-[10px] px-2 py-0.5 rounded bg-slate-800 hover:bg-amber-500/20 text-amber-300 transition-colors">
              {mod}.jsonl
            </a>
          ))}
        </div>
      ))}
    </div>
  );
}
