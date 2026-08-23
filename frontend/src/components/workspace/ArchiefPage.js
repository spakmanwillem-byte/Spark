import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Archive, Search, Upload, Trash2, X, File as FileIcon,
  Image as ImageIcon, Music, Video, Download, Edit3, Save, Tag, HardDrive,
  MessageSquare, Lock, Calendar, ChevronRight, ChevronDown, FileText
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const MAANDEN = ['Januari','Februari','Maart','April','Mei','Juni','Juli','Augustus','September','Oktober','November','December'];

const CATEGORIES = [
  { id: 'bestanden', label: 'Bestanden', icon: FileIcon, color: '#64748b', accept: '*' },
  { id: 'foto', label: 'Foto', icon: ImageIcon, color: '#22c55e', accept: 'image/*' },
  { id: 'geluiden', label: 'Geluiden', icon: Music, color: '#a855f7', accept: 'audio/*' },
  { id: 'filmpjes', label: 'Filmpjes', icon: Video, color: '#ec4899', accept: 'video/*' },
  { id: 'documenten', label: 'Documenten', icon: FileText, color: '#f59e0b', accept: null },
  { id: 'gesprekken', label: 'Gesprekken', icon: MessageSquare, color: '#06b6d4', accept: null },
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
  // v13c_foto_subtab_001 (sessie 54) — Binnen de Foto-tab: Privé (default) of Winkel.
  // Alleen als user shops heeft, wordt "Winkel" sub-tab zichtbaar.
  const [fotoSubTab, setFotoSubTab] = useState('prive'); // 'prive' | 'winkel'
  const [hasShops, setHasShops] = useState(false);
  useEffect(() => {
    fetch(`${API}/api/winkelstraat/shops`)
      .then(r => r.json())
      .then(d => setHasShops((d.shops || []).some(s => s.owner_user_id === userId)))
      .catch(() => setHasShops(false));
  }, [userId]);
  const [files, setFiles] = useState([]);
  const [stats, setStats] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [chatStats, setChatStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [expandedConv, setExpandedConv] = useState(null);
  const [personalDocs, setPersonalDocs] = useState([]);
  const [availableDocTypes, setAvailableDocTypes] = useState([]);
  const [openDoc, setOpenDoc] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    if (activeTab === 'gesprekken') {
      // Read-only: gesprekslogs ophalen
      const params = new URLSearchParams({ limit: '200' });
      if (search) params.append('search', search);
      try {
        const [logsRes, sRes] = await Promise.all([
          fetch(`${API}/api/chat/logs/${userId}?${params}`).then(r => r.json()),
          fetch(`${API}/api/chat/logs/${userId}/stats`).then(r => r.json()),
        ]);
        setConversations(logsRes.conversations || []);
        setChatStats(sRes);
        const fileStatRes = await fetch(`${API}/api/archive/${userId}/stats`).then(r => r.json()).catch(() => null);
        setStats(fileStatRes);
      } catch (e) { console.error(e); }
    } else if (activeTab === 'documenten') {
      try {
        const res = await fetch(`${API}/api/personal-docs/${userId}`).then(r => r.json());
        setPersonalDocs(res.documents || []);
        setAvailableDocTypes(res.available_types || []);
      } catch (e) { console.error(e); }
    } else {
      const params = new URLSearchParams();
      params.append('category', activeTab);
      if (search) params.append('q', search);
      // v13c_foto_subtab_001 — Foto sub-filter: alleen actief als user shops heeft
      // (anders is er niks te scheiden en tonen we alles zoals voorheen).
      if (activeTab === 'foto' && hasShops) {
        if (fotoSubTab === 'prive') params.append('exclude_source', 'shop_product_image');
        else if (fotoSubTab === 'winkel') params.append('source', 'shop_product_image');
      }
      try {
        const res = await fetch(`${API}/api/archive/${userId}?${params}`).then(r => r.json());
        setFiles(res.files || []);
        setStats(res.stats || null);
        // Ook chat stats laden zodat tab-counter klopt
        const cs = await fetch(`${API}/api/chat/logs/${userId}/stats`).then(r => r.json()).catch(() => null);
        setChatStats(cs);
      } catch (e) { console.error(e); }
    }
    setLoading(false);
  }, [userId, activeTab, search, fotoSubTab, hasShops]);

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
                onChange={handleUpload} className="hidden" accept={activeCat.accept || '*'} />
              {activeTab !== 'gesprekken' && activeTab !== 'documenten' ? (
                <button data-testid="archief-upload-btn"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-60">
                  <Upload className="w-3.5 h-3.5" /> {uploading ? 'Uploaden...' : 'Upload bestand'}
                </button>
              ) : activeTab === 'gesprekken' ? (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/60 border border-slate-700 rounded-lg text-xs text-slate-400" title="Gesprekken kunnen niet handmatig worden toegevoegd of verwijderd">
                  <Lock className="w-3.5 h-3.5" /> Read-only
                </div>
              ) : (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs text-amber-300" title="Documenten beheer je via Spark chat">
                  <MessageSquare className="w-3.5 h-3.5" /> Beheer via chat
                </div>
              )}
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
              const count = c.id === 'gesprekken'
                ? (chatStats?.total ?? 0)
                : (stats?.counts?.[c.id] ?? 0);
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
            {/* v13c_foto_subtab_001 — Sub-tabs binnen Foto: Privé (default) + Winkel (alleen shop-owners) */}
            {activeTab === 'foto' && hasShops && (
              <div className="flex gap-2 mb-3 pb-2 border-b border-slate-800">
                <button
                  data-testid="foto-subtab-prive"
                  onClick={() => setFotoSubTab('prive')}
                  className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                    fotoSubTab === 'prive'
                      ? 'bg-green-500/20 text-green-300 border border-green-500/40'
                      : 'text-slate-400 hover:text-white border border-transparent'
                  }`}
                >
                  Privé {stats?.foto_prive != null && <span className="ml-1 opacity-60">({stats.foto_prive})</span>}
                </button>
                <button
                  data-testid="foto-subtab-winkel"
                  onClick={() => setFotoSubTab('winkel')}
                  className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                    fotoSubTab === 'winkel'
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                      : 'text-slate-400 hover:text-white border border-transparent'
                  }`}
                >
                  Winkel {stats?.foto_winkel != null && <span className="ml-1 opacity-60">({stats.foto_winkel})</span>}
                </button>
              </div>
            )}
            <div className="relative mb-4 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input data-testid="archief-search" type="text"
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder={`Zoek in ${activeCat.label.toLowerCase()}${activeTab === 'foto' && hasShops ? ' (' + fotoSubTab + ')' : ''} (naam, beschrijving, tags)...`}
                className="w-full pl-8 pr-8 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
              {search && (
                <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {loading ? (
              <div className="text-center py-16 text-xs text-slate-500">Laden...</div>
            ) : activeTab === 'gesprekken' ? (
              <ConversationsView
                conversations={conversations}
                chatStats={chatStats}
                search={search}
                expandedConv={expandedConv}
                setExpandedConv={setExpandedConv}
              />
            ) : activeTab === 'documenten' ? (
              <DocumentsView
                userId={userId}
                docs={personalDocs}
                availableTypes={availableDocTypes}
                openDoc={openDoc}
                setOpenDoc={setOpenDoc}
                onReload={load}
              />
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

/* === Conversations View — hiërarchisch Jaar > Maand > Dag === */
function ConversationsView({ conversations, chatStats, search, expandedConv, setExpandedConv }) {
  // Groepeer alle gesprekken op jaar > maand > dag
  const tree = React.useMemo(() => {
    const t = {};
    for (const c of conversations) {
      const d = new Date(c.timestamp);
      const y = d.getFullYear();
      const m = d.getMonth(); // 0-11
      const dd = d.getDate();
      if (!t[y]) t[y] = {};
      if (!t[y][m]) t[y][m] = {};
      if (!t[y][m][dd]) t[y][m][dd] = [];
      t[y][m][dd].push(c);
    }
    return t;
  }, [conversations]);

  // Beschikbare jaren (gesorteerd nieuwste eerst).
  // Bonus: in december ook al automatisch volgend jaar tonen als placeholder.
  const availableYears = React.useMemo(() => {
    const set = new Set(Object.keys(tree).map(Number));
    const now = new Date();
    set.add(now.getFullYear());
    if (now.getMonth() === 11) {
      set.add(now.getFullYear() + 1); // 1 dec → volgend jaar zichtbaar
    }
    return [...set].sort((a, b) => b - a);
  }, [tree]);

  const [activeYear, setActiveYear] = useState(availableYears[0] || new Date().getFullYear());
  const [openMonths, setOpenMonths] = useState({}); // {2026-4: true}
  const [openDays, setOpenDays] = useState({});     // {2026-4-7: true}

  // Sync activeYear als nieuwe jaren binnenkomen
  useEffect(() => {
    if (!availableYears.includes(activeYear) && availableYears.length > 0) {
      setActiveYear(availableYears[0]);
    }
  }, [availableYears, activeYear]);

  const toggleMonth = (y, m) => setOpenMonths(s => ({ ...s, [`${y}-${m}`]: !s[`${y}-${m}`] }));
  const toggleDay = (y, m, d) => setOpenDays(s => ({ ...s, [`${y}-${m}-${d}`]: !s[`${y}-${m}-${d}`] }));

  if (!conversations || conversations.length === 0) {
    return (
      <div className="text-center py-16">
        <MessageSquare className="w-12 h-12 text-slate-700 mx-auto mb-3" />
        <p className="text-sm text-slate-400 mb-1">
          {search ? `Geen gesprekken matchen "${search}"` : 'Nog geen gesprekken gearchiveerd'}
        </p>
        <p className="text-xs text-slate-600">Praat met Spark om hier je gesprekslogs te zien</p>
      </div>
    );
  }

  const total = chatStats?.total || conversations.length;
  const snapCount = chatStats?.snap_count || 0;
  const avgWords = chatStats?.avg_words || 0;

  // Data voor actief jaar (kan leeg zijn als toekomst-jaar)
  const yearData = tree[activeYear] || {};
  const monthsInYear = Object.keys(yearData).map(Number).sort((a, b) => b - a); // nieuwste maand eerst

  return (
    <div className="space-y-3">
      {/* Privacy banner */}
      <div className="flex items-start gap-2 p-3 bg-cyan-500/5 border border-cyan-500/20 rounded-xl">
        <Lock className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div className="text-[11px] text-slate-400 leading-relaxed">
          <p className="text-cyan-300 font-medium mb-0.5">Privé gesprekken</p>
          <p>Deze gesprekken zijn alleen voor jou. Spark gebruikt context (zoals onbekende woorden) om kennis te bouwen, maar het persoonlijke gesprek zelf blijft privé. Logs kunnen niet handmatig verwijderd worden — alleen bij het verwijderen van je account.</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2">
        <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800">
          <p className="text-[9px] text-slate-500 uppercase tracking-wider">Gesprekken</p>
          <p className="text-lg font-bold text-white">{total}</p>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800">
          <p className="text-[9px] text-slate-500 uppercase tracking-wider">Met snaps</p>
          <p className="text-lg font-bold text-cyan-400">{snapCount}</p>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800">
          <p className="text-[9px] text-slate-500 uppercase tracking-wider">Avg woorden</p>
          <p className="text-lg font-bold text-white">{avgWords}</p>
        </div>
      </div>

      {/* Jaar tabs */}
      <div className="flex flex-wrap gap-1 border-b border-slate-800 pb-1">
        {availableYears.map(y => {
          const yearTotal = tree[y] ? Object.values(tree[y]).reduce((s, mObj) =>
            s + Object.values(mObj).reduce((sd, arr) => sd + arr.length, 0), 0) : 0;
          const isActive = y === activeYear;
          const isFuture = y > new Date().getFullYear();
          return (
            <button key={y} data-testid={`year-tab-${y}`}
              onClick={() => setActiveYear(y)}
              className={`px-3 py-1.5 rounded-t-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
                isActive
                  ? 'bg-cyan-500/15 text-cyan-300 border-b-2 border-cyan-400'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
              title={isFuture ? `${y} — nog geen gesprekken (placeholder)` : undefined}>
              {y}
              <span className={`text-[9px] px-1.5 py-0.5 rounded ${isActive ? 'bg-cyan-500/20 text-cyan-300' : 'bg-slate-800 text-slate-500'}`}>
                {yearTotal}
              </span>
            </button>
          );
        })}
      </div>

      {/* Maanden + dagen */}
      {monthsInYear.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="w-10 h-10 text-slate-700 mx-auto mb-2" />
          <p className="text-sm text-slate-400">Nog geen gesprekken in {activeYear}</p>
          <p className="text-[10px] text-slate-600 mt-1">
            {activeYear > new Date().getFullYear()
              ? 'Dit jaar staat klaar voor toekomstige gesprekken'
              : 'Start een gesprek met Spark om hier iets te zien'}
          </p>
        </div>
      ) : (
        <div className="space-y-1.5">
          {monthsInYear.map(mIdx => {
            const days = yearData[mIdx];
            const dayKeys = Object.keys(days).map(Number).sort((a, b) => b - a);
            const monthTotal = dayKeys.reduce((s, d) => s + days[d].length, 0);
            const monthKey = `${activeYear}-${mIdx}`;
            const monthOpen = !!openMonths[monthKey];
            return (
              <div key={mIdx} data-testid={`month-${activeYear}-${mIdx}`}
                className="bg-slate-900/30 border border-slate-800/60 rounded-lg overflow-hidden">
                <button onClick={() => toggleMonth(activeYear, mIdx)}
                  className="w-full flex items-center gap-2 px-3 py-2 hover:bg-slate-800/40 text-left">
                  {monthOpen ? <ChevronDown className="w-3.5 h-3.5 text-slate-500" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-500" />}
                  <span className="text-sm font-medium text-white flex-1">{MAANDEN[mIdx]}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                    {monthTotal} gesprek{monthTotal === 1 ? '' : 'ken'}
                  </span>
                </button>

                {monthOpen && (
                  <div className="px-3 pb-2 space-y-1">
                    {dayKeys.map(dd => {
                      const convs = days[dd];
                      const dayKey = `${activeYear}-${mIdx}-${dd}`;
                      const dayOpen = !!openDays[dayKey];
                      const dayDate = new Date(activeYear, mIdx, dd);
                      const weekday = ['Zo','Ma','Di','Wo','Do','Vr','Za'][dayDate.getDay()];
                      return (
                        <div key={dd} data-testid={`day-${dayKey}`}
                          className="bg-slate-950/40 rounded-md border border-slate-800/50">
                          <button onClick={() => toggleDay(activeYear, mIdx, dd)}
                            className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-slate-800/40 text-left">
                            {dayOpen ? <ChevronDown className="w-3 h-3 text-slate-600" /> : <ChevronRight className="w-3 h-3 text-slate-600" />}
                            <span className="text-[10px] text-slate-500 w-6">{weekday}</span>
                            <span className="text-sm text-slate-300 flex-1">{dd} {MAANDEN[mIdx].toLowerCase()}</span>
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                              {convs.length}
                            </span>
                          </button>
                          {dayOpen && (
                            <div className="px-2 pb-2 space-y-1">
                              {convs.map(c => {
                                const isExpanded = expandedConv === c.id;
                                const ts = new Date(c.timestamp).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' });
                                const hasSnap = c.analysis?.snap_suggestions?.length > 0;
                                return (
                                  <div key={c.id} data-testid={`conv-${c.id}`}
                                    className="bg-slate-900/60 border border-slate-800 rounded-md">
                                    <button onClick={() => setExpandedConv(isExpanded ? null : c.id)}
                                      className="w-full text-left px-2.5 py-2">
                                      <div className="flex items-start gap-2">
                                        <span className="text-[10px] text-slate-500 mt-0.5 w-9 flex-shrink-0">{ts}</span>
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-center gap-2 mb-0.5">
                                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{c.channel || 'spark'}</span>
                                            {hasSnap && (
                                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-400">
                                                +{c.analysis.snap_suggestions.length} snap
                                              </span>
                                            )}
                                          </div>
                                          <p className="text-xs text-white truncate">
                                            <span className="text-amber-400">Jij:</span> {c.user_message}
                                          </p>
                                          {!isExpanded && c.spark_response && (
                                            <p className="text-[11px] text-slate-500 truncate mt-0.5">
                                              <span className="text-cyan-400">Spark:</span> {c.spark_response}
                                            </p>
                                          )}
                                        </div>
                                      </div>
                                    </button>
                                    {isExpanded && (
                                      <div className="px-2.5 pb-2 pt-1 border-t border-slate-800/50 space-y-1.5">
                                        <div className="bg-slate-800/40 rounded p-2">
                                          <p className="text-[10px] text-cyan-400 mb-1 font-medium">Spark:</p>
                                          <p className="text-xs text-slate-300 whitespace-pre-wrap">{c.spark_response || '(geen antwoord)'}</p>
                                        </div>
                                        {c.analysis?.knowledge_matches?.length > 0 && (
                                          <div className="text-[10px] text-slate-500">
                                            Kennis gebruikt: {c.analysis.knowledge_matches.map(m => m.begrip).join(', ')}
                                          </div>
                                        )}
                                        {c.analysis?.snap_suggestions?.length > 0 && (
                                          <div className="text-[10px] text-cyan-400">
                                            Snaps gemaakt: {c.analysis.snap_suggestions.join(', ')}
                                          </div>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


// v4_personal_docs_001 — Persoonlijke documenten (testament/survivalgids/etc)
function DocumentsView({ userId, docs, availableTypes, openDoc, setOpenDoc, onReload }) {
  const [fullDoc, setFullDoc] = useState(null);
  const [loading, setLoading] = useState(false);

  const open = async (docType) => {
    setLoading(true);
    setOpenDoc(docType);
    try {
      const res = await fetch(`${API}/api/personal-docs/${userId}/${docType}`).then(r => r.json());
      setFullDoc(res.document || null);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const close = () => { setOpenDoc(null); setFullDoc(null); };

  const downloadJson = () => {
    if (!fullDoc) return;
    const blob = new Blob([JSON.stringify(fullDoc, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `${fullDoc.type}-${userId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (openDoc && fullDoc) {
    return (
      <div data-testid="docs-detail" className="space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <button onClick={close} className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
            <ChevronRight className="w-3 h-3 rotate-180" /> Terug naar lijst
          </button>
          <button onClick={downloadJson}
            className="ml-auto text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg flex items-center gap-1.5">
            <Download className="w-3 h-3" /> Download JSON
          </button>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h2 className="text-lg font-bold text-white mb-1">{fullDoc.title}</h2>
          <p className="text-[10px] text-slate-500 mb-4 uppercase tracking-wider">
            Versie {fullDoc.version} · {fullDoc.secties?.length || 0} secties · laatst bewerkt {(fullDoc.last_updated || '').slice(0, 16).replace('T', ' ')}
          </p>
          <div className="space-y-4">
            {(fullDoc.secties || []).map((sec, i) => (
              <div key={sec.id || i} className="border-l-2 border-amber-500/40 pl-3">
                <h3 className="text-sm font-semibold text-amber-300 mb-1">{sec.titel}</h3>
                <p className="text-xs text-slate-300 whitespace-pre-wrap">
                  {sec.tekst || <span className="text-slate-600 italic">(nog leeg — voeg toe via chat)</span>}
                </p>
                {sec.notitie && <p className="text-[10px] text-slate-500 mt-1 italic">📝 {sec.notitie}</p>}
              </div>
            ))}
          </div>
          {fullDoc.notitie_globaal && (
            <p className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400 italic">
              📝 {fullDoc.notitie_globaal}
            </p>
          )}
        </div>
        <p className="text-[10px] text-slate-500 italic text-center">
          Bewerken? Zeg in chat: <span className="text-amber-400">"voeg toe aan {fullDoc.type}: ..."</span>
        </p>
      </div>
    );
  }

  if (loading) return <div className="text-center py-8 text-xs text-slate-500">Document laden...</div>;

  return (
    <div data-testid="docs-list">
      {docs.length > 0 && (
        <>
          <h3 className="text-xs text-slate-400 uppercase tracking-wider mb-2">Jouw documenten</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
            {docs.map(d => (
              <button
                key={d.doc_type} data-testid={`doc-card-${d.doc_type}`}
                onClick={() => open(d.doc_type)}
                className="text-left p-4 bg-slate-900/60 border border-slate-800 hover:border-amber-500/40 rounded-xl transition-colors group"
              >
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{d.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-white group-hover:text-amber-300">{d.title || d.label}</h4>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      v{d.version} · {d.secties_count} secties · {formatBytes(d.size_bytes)}
                    </p>
                    <p className="text-[10px] text-slate-600 mt-0.5">
                      Bijgewerkt: {(d.last_updated || '').slice(0, 10)}
                    </p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-amber-400 flex-shrink-0" />
                </div>
              </button>
            ))}
          </div>
        </>
      )}

      <h3 className="text-xs text-slate-400 uppercase tracking-wider mb-2">Beschikbaar om aan te maken</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {availableTypes
          .filter(t => !docs.find(d => d.doc_type === t.type))
          .map(t => (
            <div key={t.type} className="p-4 bg-slate-900/30 border border-dashed border-slate-700 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl opacity-60">{t.emoji}</span>
                <h4 className="text-sm font-semibold text-slate-400">{t.label}</h4>
              </div>
              <p className="text-[10px] text-slate-500">
                Zeg in chat: <span className="text-amber-400">"maak {t.type} aan"</span>
              </p>
            </div>
          ))}
      </div>

      {docs.length === 0 && availableTypes.length === 0 && (
        <p className="text-center py-12 text-xs text-slate-500">Geen documenten beschikbaar.</p>
      )}
    </div>
  );
}
