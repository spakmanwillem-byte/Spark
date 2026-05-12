import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Search, BookOpen, Filter, ChevronDown, ChevronLeft, ChevronRight,
  Star, Edit3, Trash2, X, Save, ArrowUpDown, Tag, Layers, Brain,
  AlertTriangle, CheckCircle, Eye, Hash
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function KennisbankPage({ onNavigate }) {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState({ total: 0, answered: 0, unanswered: 0, te_herzien: 0 });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('recent');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState(null);
  const [showSortMenu, setShowSortMenu] = useState(false);

  const perPage = 50;

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/knowledge/stats`);
      const data = await res.json();
      setStats(data);
    } catch (e) { console.error('Stats error:', e); }
  }, []);

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: perPage.toString(),
        status_filter: statusFilter,
        sort_by: sortBy,
      });
      if (search.trim()) params.set('search', search.trim());
      const res = await fetch(`${API}/api/knowledge/all?${params}`);
      const data = await res.json();
      setEntries(data.entries || []);
      setTotalPages(data.total_pages || 1);
      setTotal(data.total || 0);
    } catch (e) { console.error('Fetch error:', e); }
    setLoading(false);
  }, [page, statusFilter, sortBy, search]);

  useEffect(() => { fetchStats(); }, [fetchStats]);
  useEffect(() => { fetchEntries(); }, [fetchEntries]);

  // Debounced search
  const [searchInput, setSearchInput] = useState('');
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const openDetail = async (entry) => {
    setSelectedEntry(entry);
    setDetailLoading(true);
    try {
      const res = await fetch(`${API}/api/knowledge/${entry.id}`);
      const data = await res.json();
      setDetailData(data);
    } catch (e) { console.error('Detail error:', e); }
    setDetailLoading(false);
  };

  const closeDetail = () => {
    setSelectedEntry(null);
    setDetailData(null);
    setIsEditing(false);
    setEditForm(null);
  };

  const startEdit = () => {
    if (!detailData) return;
    const lagen = detailData.lagen || {};
    setEditForm({
      begrip: detailData.begrip || '',
      laag1: lagen.laag1 || '',
      laag2: lagen.laag2 || '',
      laag3: lagen.laag3 || '',
      laag4: lagen.laag4 || '',
      topic: detailData.topic || '',
      tags: (detailData.tags || []).join(', '),
      belangrijkheid: detailData.belangrijkheid || 3,
      ws5: detailData.ws5 || { wie: '', wat: '', wanneer: '', waar: '', waarom: '', hoe: '' },
    });
    setIsEditing(true);
  };

  const saveEdit = async () => {
    if (!detailData || !editForm) return;
    try {
      await fetch(`${API}/api/knowledge/${detailData.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          begrip: editForm.begrip,
          lagen: { laag1: editForm.laag1, laag2: editForm.laag2, laag3: editForm.laag3, laag4: editForm.laag4 },
          topic: editForm.topic,
          tags: editForm.tags.split(',').map(t => t.trim()).filter(Boolean),
          belangrijkheid: editForm.belangrijkheid,
          ws5: editForm.ws5,
        }),
      });
      setIsEditing(false);
      closeDetail();
      fetchEntries();
      fetchStats();
    } catch (e) { console.error('Save error:', e); }
  };

  const deleteEntry = async (id, begrip) => {
    try {
      const res = await fetch(`${API}/api/knowledge/${id}`, { method: 'DELETE' });
      if (!res.ok) {
        const txt = await res.text();
        alert(`Verwijderen mislukt (${res.status}): ${txt}`);
        return;
      }
      closeDetail();
      fetchEntries();
      fetchStats();
    } catch (e) {
      console.error('Delete error:', e);
      alert(`Fout bij verwijderen: ${e.message}`);
    }
  };

  const filterButtons = [
    { id: 'all', label: 'Alles', count: stats.total, color: '#f59e0b' },
    { id: 'unanswered', label: 'Onbeantwoord', count: stats.unanswered, color: '#f97316' },
    { id: 'answered', label: 'Beantwoord', count: stats.answered, color: '#22c55e' },
    { id: 'te-herzien', label: 'Te Herzien', count: stats.te_herzien, color: '#ef4444' },
  ];

  const sortOptions = [
    { id: 'recent', label: 'Recent' },
    { id: 'alpha-asc', label: 'A-Z' },
    { id: 'alpha-desc', label: 'Z-A' },
    { id: 'importance-high', label: 'Belangrijk (hoog)' },
    { id: 'importance-low', label: 'Belangrijk (laag)' },
  ];

  return (
    <MainLayout activePage="knowledge" onNavigate={onNavigate}>
      <div data-testid="kennisbank-page" className="p-4 md:p-6 space-y-5 max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
            <BookOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Kennisbank</h1>
            <p className="text-xs text-slate-500">Alle knowledge kaarten doorzoeken en bewerken</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {filterButtons.map(f => (
            <button
              key={f.id}
              data-testid={`stat-${f.id}`}
              onClick={() => { setStatusFilter(f.id); setPage(1); }}
              className={`p-3 rounded-xl border transition-all text-left ${
                statusFilter === f.id
                  ? 'border-opacity-50 bg-opacity-10'
                  : 'border-slate-800 bg-slate-900/40 hover:bg-slate-800/50'
              }`}
              style={statusFilter === f.id ? { borderColor: f.color, background: `${f.color}15` } : {}}
            >
              <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">{f.label}</p>
              <p className="text-2xl font-bold" style={{ color: statusFilter === f.id ? f.color : '#e2e8f0' }}>
                {f.count.toLocaleString()}
              </p>
            </button>
          ))}
        </div>

        {/* Search + Sort */}
        <div className="flex gap-3 items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              data-testid="search-input"
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Zoek op begrip, definitie, topic of tag..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:border-amber-500/50 focus:outline-none transition-colors"
            />
          </div>
          <div className="relative">
            <button
              data-testid="sort-btn"
              onClick={() => setShowSortMenu(!showSortMenu)}
              className="flex items-center gap-2 px-4 py-2.5 bg-slate-900/60 border border-slate-800 rounded-xl text-sm text-slate-300 hover:border-slate-600 transition-colors"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
              {sortOptions.find(s => s.id === sortBy)?.label}
              <ChevronDown className="w-3 h-3" />
            </button>
            {showSortMenu && (
              <div className="absolute right-0 top-full mt-1 z-20 bg-slate-800 border border-slate-700 rounded-xl shadow-xl overflow-hidden min-w-[180px]">
                {sortOptions.map(s => (
                  <button
                    key={s.id}
                    onClick={() => { setSortBy(s.id); setShowSortMenu(false); setPage(1); }}
                    className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                      sortBy === s.id ? 'bg-amber-500/10 text-amber-400' : 'text-slate-300 hover:bg-slate-700/50'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Results info */}
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>{total.toLocaleString()} resultaten</span>
          <span>Pagina {page} van {totalPages}</span>
        </div>

        {/* Entries List */}
        <div className="space-y-2">
          {loading ? (
            <div className="py-20 text-center">
              <div className="w-8 h-8 border-3 border-amber-500/30 border-t-amber-500 rounded-full animate-spin mx-auto mb-3" />
              <p className="text-slate-500 text-sm">Laden...</p>
            </div>
          ) : entries.length === 0 ? (
            <div className="py-20 text-center">
              <Brain className="w-10 h-10 text-slate-700 mx-auto mb-3" />
              <p className="text-slate-400 text-sm">Geen kaarten gevonden</p>
            </div>
          ) : (
            entries.map(entry => (
              <KnowledgeCard
                key={entry.id}
                entry={entry}
                onClick={() => openDetail(entry)}
              />
            ))
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-2">
            <button
              data-testid="prev-page"
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(1, p - 1))}
              className="p-2 rounded-lg bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (page <= 3) {
                pageNum = i + 1;
              } else if (page >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = page - 2 + i;
              }
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${
                    page === pageNum
                      ? 'bg-amber-500 text-white'
                      : 'bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
            <button
              data-testid="next-page"
              disabled={page >= totalPages}
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              className="p-2 rounded-lg bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Detail Modal */}
        {selectedEntry && (
          <DetailModal
            detailData={detailData}
            detailLoading={detailLoading}
            isEditing={isEditing}
            editForm={editForm}
            setEditForm={setEditForm}
            onClose={closeDetail}
            onStartEdit={startEdit}
            onSaveEdit={saveEdit}
            onCancelEdit={() => setIsEditing(false)}
            onDelete={(id, begrip) => deleteEntry(id, begrip)}
          />
        )}
      </div>
    </MainLayout>
  );
}

/* === Knowledge Card === */
function KnowledgeCard({ entry, onClick }) {
  return (
    <button
      data-testid={`card-${entry.id}`}
      onClick={onClick}
      className="w-full text-left p-4 bg-slate-900/40 border border-slate-800 rounded-xl hover:border-slate-600 transition-all group"
    >
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Brain className="w-4 h-4 text-amber-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-semibold text-white truncate">{entry.begrip}</h3>
            {entry.needs_audit && (
              <span className="text-[10px] px-1.5 py-0.5 bg-red-500/15 text-red-400 rounded font-medium">TE HERZIEN</span>
            )}
            {!entry.is_answered && !entry.needs_audit && (
              <span className="text-[10px] px-1.5 py-0.5 bg-orange-500/15 text-orange-400 rounded font-medium">ONBEANTWOORD</span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1 line-clamp-1">
            {entry.laag1_preview || 'Nog geen antwoord'}
          </p>
          <div className="flex items-center gap-3 mt-2">
            {entry.topic && (
              <span className="text-[10px] text-slate-500 flex items-center gap-1">
                <Layers className="w-2.5 h-2.5" /> {entry.topic}
              </span>
            )}
            {entry.belangrijkheid > 0 && (
              <span className="text-[10px] text-amber-400/70 flex items-center gap-0.5">
                <Star className="w-2.5 h-2.5 fill-current" /> {entry.belangrijkheid}
              </span>
            )}
            {entry.tags && entry.tags.length > 0 && (
              <span className="text-[10px] text-slate-500 flex items-center gap-1">
                <Tag className="w-2.5 h-2.5" /> {entry.tags.slice(0, 3).join(', ')}
              </span>
            )}
          </div>
        </div>
        <Eye className="w-4 h-4 text-slate-600 group-hover:text-slate-400 transition-colors flex-shrink-0 mt-1" />
      </div>
    </button>
  );
}

/* === Detail Modal === */
function DetailModal({ detailData, detailLoading, isEditing, editForm, setEditForm, onClose, onStartEdit, onSaveEdit, onCancelEdit, onDelete }) {
  const [confirmDelete, setConfirmDelete] = React.useState(false);

  if (detailLoading || !detailData) {
    return (
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
        <div className="w-8 h-8 border-3 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
      </div>
    );
  }

  const lagen = detailData.lagen || {};
  const lagenConfig = [
    { key: 'laag1', label: 'Laag 1: Kort antwoord', sub: 'Directe, korte uitleg', color: '#22c55e' },
    { key: 'laag2', label: 'Laag 2: + Context', sub: 'Waarom belangrijk, context', color: '#3b82f6' },
    { key: 'laag3', label: 'Laag 3: Volledig', sub: 'Diepgaande uitleg', color: '#a855f7' },
    { key: 'laag4', label: 'Laag 4: Essentie', sub: 'Wat Spark hiermee doet', color: '#f59e0b' },
  ];

  const ws5Fields = [
    { key: 'wie', label: 'Wie', value: detailData.ws5?.wie || detailData.context_5wh?.wie || '' },
    { key: 'wat', label: 'Wat', value: detailData.ws5?.wat || detailData.context_5wh?.wat || '' },
    { key: 'wanneer', label: 'Wanneer', value: detailData.ws5?.wanneer || detailData.context_5wh?.wanneer || '' },
    { key: 'waar', label: 'Waar', value: detailData.ws5?.waar || detailData.context_5wh?.waar || '' },
    { key: 'waarom', label: 'Waarom', value: detailData.ws5?.waarom || detailData.context_5wh?.waarom || '' },
    { key: 'hoe', label: 'Hoe', value: detailData.ws5?.hoe || detailData.context_5wh?.hoe || '' },
  ];

  if (isEditing && editForm) {
    return (
      <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onCancelEdit}>
        <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
          <div className="sticky top-0 bg-slate-900 border-b border-slate-800 p-5 flex items-center justify-between z-10">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Edit3 className="w-4 h-4 text-amber-400" /> Bewerk: {detailData.begrip}
            </h3>
            <button onClick={onCancelEdit} className="p-1 hover:bg-slate-800 rounded-lg">
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>
          <div className="p-5 space-y-4">
            <Field label="Begrip" value={editForm.begrip} onChange={v => setEditForm({...editForm, begrip: v})} />
            {lagenConfig.map(l => (
              <Field
                key={l.key}
                label={l.label}
                sub={l.sub}
                value={editForm[l.key]}
                onChange={v => setEditForm({...editForm, [l.key]: v})}
                multiline
                color={l.color}
              />
            ))}
            <Field label="Topic" value={editForm.topic} onChange={v => setEditForm({...editForm, topic: v})} />
            <Field label="Tags (komma gescheiden)" value={editForm.tags} onChange={v => setEditForm({...editForm, tags: v})} />
            <div>
              <label className="text-xs text-slate-400 block mb-2">Belangrijkheid</label>
              <div className="flex gap-1.5">
                {[1,2,3,4,5].map(v => (
                  <button
                    key={v}
                    onClick={() => setEditForm({...editForm, belangrijkheid: v})}
                    className={`w-9 h-9 rounded-lg text-sm font-medium transition-all ${
                      editForm.belangrijkheid >= v ? 'bg-amber-500 text-white' : 'bg-slate-800 text-slate-500'
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
            <div className="border-t border-slate-800 pt-4">
              <p className="text-xs text-slate-400 mb-3">5W's Framework</p>
              <div className="grid grid-cols-2 gap-3">
                {ws5Fields.map(f => (
                  <Field
                    key={f.key}
                    label={f.label}
                    value={editForm.ws5[f.key] || ''}
                    onChange={v => setEditForm({...editForm, ws5: {...editForm.ws5, [f.key]: v}})}
                    small
                  />
                ))}
              </div>
            </div>
            <div className="flex gap-3 pt-4 border-t border-slate-800">
              <button data-testid="save-edit-btn" onClick={onSaveEdit} className="flex-1 py-2.5 rounded-xl font-medium text-sm text-white transition-all" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
                <span className="flex items-center justify-center gap-2"><Save className="w-4 h-4" /> Opslaan</span>
              </button>
              <button onClick={onCancelEdit} className="px-6 py-2.5 bg-slate-800 text-slate-300 rounded-xl text-sm hover:bg-slate-700 transition-colors">
                Annuleren
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-start justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">{detailData.begrip}</h3>
            {detailData.topic && (
              <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                <Layers className="w-3 h-3" /> {detailData.topic}
              </p>
            )}
          </div>
          <button onClick={onClose} className="p-1 hover:bg-slate-800 rounded-lg">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Lagen */}
        <div className="p-5 space-y-3">
          {lagenConfig.map(l => {
            const value = lagen[l.key];
            return (
              <div key={l.key} className={`p-4 rounded-xl border border-slate-800 ${!value ? 'opacity-40' : ''}`}>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: l.color }} />
                  <span className="text-xs font-medium text-slate-400">{l.label}</span>
                </div>
                <p className="text-sm text-slate-200 leading-relaxed">
                  {value || <span className="text-slate-600 italic">Niet ingevuld</span>}
                </p>
              </div>
            );
          })}

          {/* Tags */}
          {detailData.tags && detailData.tags.length > 0 && (
            <div className="pt-2">
              <p className="text-xs text-slate-500 mb-2">Tags</p>
              <div className="flex flex-wrap gap-1.5">
                {detailData.tags.map((tag, i) => (
                  <span key={i} className="text-[10px] px-2.5 py-1 bg-slate-800 text-slate-300 rounded-full border border-slate-700">
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Belangrijkheid */}
          <div className="flex items-center gap-2 pt-2">
            <span className="text-xs text-slate-500">Belangrijkheid:</span>
            <div className="flex gap-0.5">
              {[1,2,3,4,5].map(i => (
                <Star key={i} className={`w-3.5 h-3.5 ${i <= (detailData.belangrijkheid || 0) ? 'text-amber-400 fill-current' : 'text-slate-700'}`} />
              ))}
            </div>
          </div>

          {/* 5W+H Context */}
          {ws5Fields.some(f => f.value) && (
            <div className="border-t border-slate-800 pt-4 mt-2">
              <p className="text-xs text-slate-500 mb-3">5W+H Context</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {ws5Fields.map(f => f.value && (
                  <div key={f.key} className="p-2 bg-slate-800/50 rounded-lg">
                    <p className="text-[10px] text-slate-500 uppercase">{f.label}</p>
                    <p className="text-xs text-slate-300 mt-0.5">{f.value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="p-5 border-t border-slate-800 flex gap-3">
          <button
            data-testid="edit-btn"
            onClick={onStartEdit}
            className="flex-1 py-2.5 rounded-xl font-medium text-sm text-white transition-all flex items-center justify-center gap-2"
            style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}
          >
            <Edit3 className="w-4 h-4" /> Bewerken
          </button>
          <button
            data-testid="delete-btn"
            onClick={() => {
              if (!confirmDelete) {
                setConfirmDelete(true);
                setTimeout(() => setConfirmDelete(false), 4000);
                return;
              }
              setConfirmDelete(false);
              onDelete(detailData.id, detailData.begrip);
            }}
            className={`px-4 py-2.5 rounded-xl text-sm transition-colors flex items-center gap-2 ${
              confirmDelete
                ? 'bg-red-500/30 text-red-200 hover:bg-red-500/50 animate-pulse font-semibold'
                : 'bg-red-500/10 text-red-400 hover:bg-red-500/20'
            }`}
          >
            <Trash2 className="w-4 h-4" />
            {confirmDelete && <span className="text-xs">Bevestig</span>}
          </button>
          <button onClick={onClose} className="px-5 py-2.5 bg-slate-800 text-slate-300 rounded-xl text-sm hover:bg-slate-700 transition-colors">
            Sluiten
          </button>
        </div>
      </div>
    </div>
  );
}

/* === Reusable form field === */
function Field({ label, sub, value, onChange, multiline, color, small }) {
  const baseClass = `w-full px-3 ${small ? 'py-1.5 text-xs' : 'py-2 text-sm'} bg-slate-800/50 border border-slate-700/50 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-amber-500/40 transition-colors`;
  return (
    <div>
      <label className="text-xs text-slate-400 block mb-1.5">
        {color && <span className="inline-block w-1.5 h-1.5 rounded-full mr-1.5" style={{ background: color }} />}
        {label}
      </label>
      {sub && <p className="text-[10px] text-slate-600 mb-1.5">{sub}</p>}
      {multiline ? (
        <textarea value={value} onChange={e => onChange(e.target.value)} className={`${baseClass} resize-none`} rows={3} />
      ) : (
        <input type="text" value={value} onChange={e => onChange(e.target.value)} className={baseClass} />
      )}
    </div>
  );
}

export default KennisbankPage;
