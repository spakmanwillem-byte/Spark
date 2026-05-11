import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Archive, Search, Upload, Trash2, X, File as FileIcon,
  Image as ImageIcon, Music, Video, Download, Edit3, Save, Tag, HardDrive
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const CATEGORIES = [
  { id: 'bestanden', label: 'Bestanden', icon: FileIcon, color: '#64748b', accept: '*' },
  { id: 'foto', label: 'Foto', icon: ImageIcon, color: '#22c55e', accept: 'image/*' },
  { id: 'geluiden', label: 'Geluiden', icon: Music, color: '#a855f7', accept: 'audio/*' },
  { id: 'filmpjes', label: 'Filmpjes', icon: Video, color: '#ec4899', accept: 'video/*' },
];

function formatBytes(n) {
  if (!n) return '0 B';
  const k = 1024;
  const u = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(n) / Math.log(k));
  return `${(n / Math.pow(k, i)).toFixed(i === 0 ? 0 : 1)} ${u[i]}`;
}

export function ArchiefPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const fileInputRef = useRef(null);

  const [activeTab, setActiveTab] = useState('bestanden');
  const [files, setFiles] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams();
    params.append('category', activeTab);
    if (search) params.append('q', search);
    try {
      const res = await fetch(`${API}/api/archive/${userId}?${params}`).then(r => r.json());
      setFiles(res.files || []);
      setStats(res.stats || null);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [userId, activeTab, search]);

  useEffect(() => { load(); }, [load]);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${API}/api/archive/${userId}/upload`, { method: 'POST', body: fd });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload mislukt' }));
        throw new Error(err.detail || 'Upload mislukt');
      }
      const data = await res.json();
      // Switch naar tab waarin het bestand terechtkwam
      if (data.file?.category && data.file.category !== activeTab) {
        setActiveTab(data.file.category);
      }
      await load();
    } catch (err) {
      setUploadError(err.message || 'Upload fout');
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const deleteFile = async (fileId) => {
    if (!confirm('Dit bestand permanent verwijderen?')) return;
    await fetch(`${API}/api/archive/${userId}/${fileId}`, { method: 'DELETE' });
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
    await fetch(`${API}/api/archive/${userId}/${editingId}`, {
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
    <MainLayout activePage="archief" onNavigate={onNavigate}>
      <div data-testid="archief-page" className="h-full flex flex-col">

        {/* Banner */}
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #64748b, #475569)' }}>
              <Archive className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Persoonlijk Archief</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">
                Eigen opslag voor {user?.naam || 'gebruiker'} · {stats?.total_files || 0} bestanden · {formatBytes(stats?.total_size_bytes || 0)}
              </p>
            </div>

            <div className="ml-auto flex items-center gap-2">
              <input ref={fileInputRef} type="file" data-testid="archief-file-input"
                onChange={handleUpload} className="hidden" accept={activeCat.accept} />
              <button data-testid="archief-upload-btn"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-60">
                <Upload className="w-3.5 h-3.5" /> {uploading ? 'Uploaden...' : 'Upload bestand'}
              </button>
            </div>
          </div>

          {uploadError && (
            <div className="mb-3 px-3 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
              {uploadError}
            </div>
          )}

          {/* Tabs */}
          <div className="flex overflow-x-auto gap-0">
            {CATEGORIES.map(c => {
              const isActive = activeTab === c.id;
              const count = stats?.counts?.[c.id] ?? 0;
              return (
                <button key={c.id} data-testid={`archief-tab-${c.id}`}
                  onClick={() => setActiveTab(c.id)}
                  className="relative flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors whitespace-nowrap flex-shrink-0"
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

        {/* Search + Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-5xl mx-auto">
            {/* Search */}
            <div className="relative mb-4 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input data-testid="archief-search" type="text"
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder={`Zoek in ${activeCat.label.toLowerCase()} (naam, beschrijving, tags)...`}
                className="w-full pl-8 pr-8 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
              {search && (
                <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {loading ? (
              <div className="text-center py-16 text-xs text-slate-500">Laden...</div>
            ) : files.length === 0 ? (
              <EmptyState category={activeCat} search={search} onUpload={() => fileInputRef.current?.click()} />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {files.map(f => (
                  <FileCard key={f.id}
                    file={f}
                    userId={userId}
                    category={activeCat}
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
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

function EmptyState({ category, search, onUpload }) {
  const Icon = category.icon;
  return (
    <div className="text-center py-16">
      <Icon className="w-12 h-12 text-slate-700 mx-auto mb-3" />
      <p className="text-sm text-slate-400 mb-1">
        {search ? `Geen ${category.label.toLowerCase()} matchen "${search}"` : `Nog geen ${category.label.toLowerCase()}`}
      </p>
      {!search && (
        <>
          <p className="text-xs text-slate-600 mb-4">Upload je eerste bestand om te beginnen</p>
          <button onClick={onUpload}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs">
            <Upload className="w-3.5 h-3.5" /> Upload {category.label.toLowerCase()}
          </button>
        </>
      )}
    </div>
  );
}

function FileCard({ file, userId, category, isEditing, editForm, setEditForm, onStartEdit, onSave, onCancel, onDelete }) {
  const Icon = category.icon;
  const downloadUrl = `${API}${file.download_url}`;
  const ts = new Date(file.uploaded_at).toLocaleString('nl-NL', { dateStyle: 'short', timeStyle: 'short' });

  // Preview voor foto/audio/video
  const renderPreview = () => {
    if (file.category === 'foto') {
      return <img src={downloadUrl} alt={file.original_name} className="w-full h-32 object-cover rounded-lg bg-slate-800" loading="lazy" />;
    }
    if (file.category === 'geluiden') {
      return <audio src={downloadUrl} controls className="w-full mt-2" preload="none" />;
    }
    if (file.category === 'filmpjes') {
      return <video src={downloadUrl} controls className="w-full h-32 rounded-lg bg-black" preload="none" />;
    }
    return null;
  };

  return (
    <div data-testid={`file-card-${file.id}`} className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
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
              placeholder="tags, komma-gescheiden"
              className="w-full px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-white" />
            <div className="flex gap-2">
              <button data-testid={`save-${file.id}`} onClick={onSave}
                className="flex-1 py-1 bg-green-500/20 text-green-400 rounded text-xs flex items-center justify-center gap-1">
                <Save className="w-3 h-3" /> Opslaan
              </button>
              <button onClick={onCancel}
                className="flex-1 py-1 bg-slate-800 text-slate-400 rounded text-xs flex items-center justify-center gap-1">
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
            </div>
            {file.description && (
              <p className="text-xs text-slate-400 mt-1.5 mb-1">{file.description}</p>
            )}
            {file.tags?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {file.tags.map((t, i) => (
                  <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 flex items-center gap-0.5">
                    <Tag className="w-2 h-2" />{t}
                  </span>
                ))}
              </div>
            )}
            <div className="flex items-center gap-1 mt-2 pt-2 border-t border-slate-800/50">
              <a href={downloadUrl} download={file.original_name}
                data-testid={`download-${file.id}`}
                className="flex items-center gap-1 px-2 py-1 text-[10px] text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors">
                <Download className="w-3 h-3" /> Download
              </a>
              <button onClick={onStartEdit}
                data-testid={`edit-${file.id}`}
                className="flex items-center gap-1 px-2 py-1 text-[10px] text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors">
                <Edit3 className="w-3 h-3" /> Bewerk
              </button>
              <button onClick={onDelete}
                data-testid={`delete-${file.id}`}
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

export default ArchiefPage;
