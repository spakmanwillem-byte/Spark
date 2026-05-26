/**
 * SynapseTab (v6_synapse_001 F6) — Spark's zelf-lezende laag in UI
 * =================================================================
 * Tree-view van alle backend modules, frontend components en data-stores.
 * - Filter op status (active/wip/skeleton/deprecated/tagged_for_deletion)
 * - Filter op groep (backend_modules / frontend_components / backend_data)
 * - Inline search (naam/doel/footnote/endpoints)
 * - Klik op item → detail-modal met edit-modus (doel/footnote/blueprint_ref/status/tags)
 * - Knop "Volledige scan" → trigger /api/synapse/scan
 */
import React, { useEffect, useState, useMemo } from 'react';
import {
  Brain, RefreshCw, Search, Filter, Tag, FileText, Folder, FolderOpen,
  Database, Component, Pencil, Save, X, Sparkles, AlertCircle,
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_META = {
  active:               { color: '#22c55e', icon: '✅', label: 'Actief' },
  wip:                  { color: '#f59e0b', icon: '🚧', label: 'In opbouw (WIP)' },
  skeleton:             { color: '#a855f7', icon: '🌱', label: 'Skelet' },
  deprecated:           { color: '#94a3b8', icon: '🍂', label: 'Verouderd' },
  tagged_for_deletion:  { color: '#ef4444', icon: '🗑️', label: 'Klaar voor verwijdering' },
  deleted:              { color: '#475569', icon: '❌', label: 'Verwijderd' },
};

const GROUP_META = {
  backend_modules:     { label: 'Backend Modules', icon: Component, accent: '#3b82f6' },
  frontend_components: { label: 'Frontend Components', icon: Component, accent: '#a855f7' },
  backend_data:        { label: 'Data Stores', icon: Database, accent: '#10b981' },
};

const STATUS_OPTIONS = ['active', 'wip', 'skeleton', 'deprecated', 'tagged_for_deletion', 'deleted'];

export function SynapseTab() {
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [groupFilter, setGroupFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  // Edit modal
  const [editing, setEditing] = useState(null); // {path, group, meta}
  const [editForm, setEditForm] = useState({ doel: '', footnote: '', blueprint_ref: '', status: '', tags: '' });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${API}/api/synapse/tree`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      setDoc(d);
    } catch (e) {
      setError(e.message || 'Laden mislukt');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const triggerScan = async () => {
    setScanning(true);
    try {
      await fetch(`${API}/api/synapse/scan`);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setScanning(false);
    }
  };

  // Vlak gefilterde lijst
  const flatList = useMemo(() => {
    if (!doc?.tree) return [];
    const out = [];
    for (const grp of Object.keys(doc.tree)) {
      if (groupFilter !== 'all' && groupFilter !== grp) continue;
      for (const [path, meta] of Object.entries(doc.tree[grp])) {
        if (statusFilter !== 'all' && meta.status !== statusFilter) continue;
        if (search) {
          const hay = [
            meta.naam, meta.doel, meta.footnote, meta.blueprint_ref,
            (meta.tags || []).join(' '),
            (meta.endpoints || []).join(' '),
          ].filter(Boolean).join(' ').toLowerCase();
          if (!hay.includes(search.toLowerCase())) continue;
        }
        out.push({ path, group: grp, meta });
      }
    }
    return out;
  }, [doc, groupFilter, statusFilter, search]);

  // Open edit modal
  const openEdit = (item) => {
    setEditing(item);
    setEditForm({
      doel: item.meta.doel || '',
      footnote: item.meta.footnote || '',
      blueprint_ref: item.meta.blueprint_ref || '',
      status: item.meta.status || 'active',
      tags: (item.meta.tags || []).join(', '),
    });
  };

  const saveEdit = async () => {
    if (!editing) return;
    setSaving(true);
    try {
      const containerPath = `/app/${editing.path}`;
      const payload = {
        container_path: containerPath,
        doel: editForm.doel,
        footnote: editForm.footnote,
        blueprint_ref: editForm.blueprint_ref || null,
        status: editForm.status,
        tags: editForm.tags.split(',').map(t => t.trim()).filter(Boolean),
      };
      const r = await fetch(`${API}/api/synapse/tag`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const d = await r.json();
      if (!r.ok || !d.success) throw new Error(d.detail || 'Opslaan mislukt');
      setEditing(null);
      // Refresh
      await load();
    } catch (e) {
      alert(`Opslaan mislukt: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div data-testid="synapse-loading" className="flex items-center justify-center py-16">
        <div className="w-8 h-8 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
      </div>
    );
  }
  if (error) {
    return (
      <div data-testid="synapse-error" className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
        <p className="text-red-300 text-sm">Fout: {error}</p>
      </div>
    );
  }

  const summary = doc?.summary || {};
  const byStatus = summary.by_status || {};

  return (
    <div data-testid="synapse-tab" className="space-y-4">
      {/* Header met summary */}
      <div className="rounded-xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 to-purple-500/5 p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-5 h-5 text-amber-400" />
              <h3 className="text-base font-bold text-white">Synapslaag — Spark leest zichzelf</h3>
            </div>
            <p className="text-xs text-slate-400 mb-3">
              Elke map heeft een `_meta.json` met naam, doel, status, footnote, blueprint en encryption-slot.
              Vraag Spark in chat: <em className="text-amber-300">"wat hebben we?"</em>, <em className="text-amber-300">"is X af?"</em>, <em className="text-amber-300">"waar woont Y?"</em>
            </p>
            <div className="flex flex-wrap gap-3 text-xs">
              <div className="px-2 py-1 rounded bg-slate-800/60 border border-slate-700">
                <span className="text-slate-500">Containers:</span>{' '}
                <span className="text-white font-medium">{summary.total_containers || 0}</span>
              </div>
              <div className="px-2 py-1 rounded bg-slate-800/60 border border-slate-700">
                <span className="text-slate-500">Endpoints:</span>{' '}
                <span className="text-white font-medium">{summary.total_endpoints_detected || 0}</span>
              </div>
              {Object.entries(byStatus).map(([st, count]) => {
                const sm = STATUS_META[st] || {};
                return (
                  <div key={st} data-testid={`synapse-summary-${st}`} className="px-2 py-1 rounded bg-slate-800/60 border border-slate-700">
                    <span style={{ color: sm.color }}>{sm.icon} {sm.label}:</span>{' '}
                    <span className="text-white font-medium">{count}</span>
                  </div>
                );
              })}
            </div>
            {doc?.generated_at && (
              <p className="text-[10px] text-slate-600 mt-3">
                Laatste scan: {new Date(doc.generated_at).toLocaleString('nl-NL')}
              </p>
            )}
          </div>
          <button
            onClick={triggerScan}
            disabled={scanning}
            data-testid="synapse-rescan-btn"
            className="px-3 py-2 rounded-lg text-xs font-medium text-amber-300 border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? 'Scannen…' : 'Volledige scan'}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-3 space-y-3">
        <div className="flex gap-2 items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
            <input
              data-testid="synapse-search"
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Zoek in naam, doel, footnote, endpoints…"
              className="w-full pl-9 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
            />
          </div>
          <select
            data-testid="synapse-group-filter"
            value={groupFilter}
            onChange={e => setGroupFilter(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500"
          >
            <option value="all">Alle groepen</option>
            {Object.entries(GROUP_META).map(([id, m]) => (
              <option key={id} value={id}>{m.label}</option>
            ))}
          </select>
          <select
            data-testid="synapse-status-filter"
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500"
          >
            <option value="all">Alle statussen</option>
            {STATUS_OPTIONS.map(s => (
              <option key={s} value={s}>{STATUS_META[s].icon} {STATUS_META[s].label}</option>
            ))}
          </select>
        </div>
        <div className="text-[11px] text-slate-500">
          {flatList.length} resultaten
        </div>
      </div>

      {/* Lijst gegroepeerd */}
      <div className="space-y-3">
        {Object.entries(GROUP_META).map(([grpId, grpMeta]) => {
          if (groupFilter !== 'all' && groupFilter !== grpId) return null;
          const items = flatList.filter(it => it.group === grpId);
          if (items.length === 0) return null;
          const Icon = grpMeta.icon;
          return (
            <div key={grpId} className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden">
              <div className="px-4 py-2 flex items-center gap-2 bg-slate-800/60 border-b border-slate-800">
                <Icon className="w-4 h-4" style={{ color: grpMeta.accent }} />
                <span className="text-sm font-medium text-white">{grpMeta.label}</span>
                <span className="text-[10px] text-slate-500">({items.length})</span>
              </div>
              <div className="divide-y divide-slate-800/70">
                {items.map(item => {
                  const sm = STATUS_META[item.meta.status] || STATUS_META.active;
                  const epCount = (item.meta.endpoints || []).length;
                  return (
                    <button
                      key={item.path}
                      onClick={() => openEdit(item)}
                      data-testid={`synapse-item-${item.meta.naam}`}
                      className="w-full text-left px-4 py-2.5 hover:bg-slate-800/40 transition-colors flex items-center gap-3"
                    >
                      <span className="text-base flex-shrink-0" style={{ color: sm.color }}>{sm.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium text-white">{item.meta.naam}</span>
                          {item.meta.blueprint_ref && (
                            <span title={item.meta.blueprint_ref} className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-300">📘 blueprint</span>
                          )}
                          {(item.meta.tags || []).slice(0, 3).map(t => (
                            <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">#{t}</span>
                          ))}
                        </div>
                        <p className="text-[11px] text-slate-500 truncate">
                          {item.meta.doel || <em className="text-slate-700">— geen doel —</em>}
                        </p>
                        {item.meta.footnote && (
                          <p className="text-[10px] text-amber-400/70 truncate mt-0.5">📝 {item.meta.footnote}</p>
                        )}
                      </div>
                      <div className="text-right flex-shrink-0 flex flex-col items-end gap-0.5">
                        <span className="text-[10px] text-slate-500">{item.path}</span>
                        <div className="flex gap-2 text-[10px] text-slate-600">
                          {epCount > 0 && <span>🔌 {epCount}</span>}
                          <span>📁 {item.meta.file_count || 0}</span>
                          {item.meta.activity_count > 0 && <span title="activity_count">⚡ {item.meta.activity_count}</span>}
                        </div>
                      </div>
                      <Pencil className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* EDIT MODAL */}
      {editing && (
        <div data-testid="synapse-edit-modal"
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => !saving && setEditing(null)}>
          <div className="bg-slate-900 border border-amber-500/30 rounded-2xl p-6 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <div className="flex items-start gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-amber-500/15 border border-amber-500/40 flex items-center justify-center flex-shrink-0">
                <Pencil className="w-5 h-5 text-amber-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-white">{editing.meta.naam}</h3>
                <p className="text-[11px] text-slate-500 truncate">{editing.path}</p>
              </div>
              <button onClick={() => !saving && setEditing(null)} className="p-1 text-slate-500 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 max-h-[55vh] overflow-y-auto pr-1">
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider">Doel</label>
                <input
                  data-testid="synapse-edit-doel"
                  type="text"
                  value={editForm.doel}
                  onChange={e => setEditForm(f => ({ ...f, doel: e.target.value }))}
                  placeholder="Wat is de bedoeling van deze module?"
                  className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider">Status</label>
                <select
                  data-testid="synapse-edit-status"
                  value={editForm.status}
                  onChange={e => setEditForm(f => ({ ...f, status: e.target.value }))}
                  className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500"
                >
                  {STATUS_OPTIONS.map(s => (
                    <option key={s} value={s}>{STATUS_META[s].icon} {STATUS_META[s].label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider">Blueprint-ref (link naar blueprint-doc)</label>
                <input
                  data-testid="synapse-edit-blueprint"
                  type="text"
                  value={editForm.blueprint_ref}
                  onChange={e => setEditForm(f => ({ ...f, blueprint_ref: e.target.value }))}
                  placeholder="bv. /app/memory/blueprints/winkelstraat.md"
                  className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider">Footnote (split-voorwaarde / TODO / notitie)</label>
                <textarea
                  data-testid="synapse-edit-footnote"
                  rows={3}
                  value={editForm.footnote}
                  onChange={e => setEditForm(f => ({ ...f, footnote: e.target.value }))}
                  placeholder="bv. 'Splitten in submap zodra > 4 endpoints'"
                  className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 resize-none"
                />
              </div>
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider">Tags (komma-gescheiden)</label>
                <input
                  data-testid="synapse-edit-tags"
                  type="text"
                  value={editForm.tags}
                  onChange={e => setEditForm(f => ({ ...f, tags: e.target.value }))}
                  placeholder="bv. core, p1, refactor-target"
                  className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                />
              </div>

              {/* READ-ONLY metadata */}
              <div className="pt-2 mt-2 border-t border-slate-800 space-y-1 text-[11px] text-slate-500">
                <div><strong className="text-slate-400">Container type:</strong> {editing.meta.container_type}</div>
                <div><strong className="text-slate-400">Owner:</strong> {editing.meta.owner}</div>
                <div><strong className="text-slate-400">Aangemaakt:</strong> {new Date(editing.meta.created_at).toLocaleString('nl-NL')}</div>
                <div><strong className="text-slate-400">Laatst aangeraakt:</strong> {new Date(editing.meta.last_touched).toLocaleString('nl-NL')}</div>
                <div><strong className="text-slate-400">Activity count:</strong> {editing.meta.activity_count || 0}</div>
                <div><strong className="text-slate-400">Bestanden:</strong> {editing.meta.file_count || 0} · subdirs: {editing.meta.subdir_count || 0}</div>
                {(editing.meta.endpoints || []).length > 0 && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-slate-400">🔌 {(editing.meta.endpoints || []).length} endpoints</summary>
                    <ul className="mt-1 ml-3 space-y-0.5">
                      {(editing.meta.endpoints || []).map(e => (
                        <li key={e} className="text-[10px] text-slate-500 font-mono">{e}</li>
                      ))}
                    </ul>
                  </details>
                )}
                {editing.meta.encryption && (
                  <div className="mt-2 px-2 py-1 rounded bg-slate-800/50 border border-slate-700/50">
                    <strong className="text-slate-400">🔐 Encryption:</strong>{' '}
                    {editing.meta.encryption.enabled
                      ? <span className="text-emerald-300">{editing.meta.encryption.algorithm} (key: {editing.meta.encryption.key_holder})</span>
                      : <span className="text-slate-500 italic">slot beschikbaar, niet geactiveerd (F2F later)</span>
                    }
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 mt-4 pt-3 border-t border-slate-800">
              <button
                onClick={() => setEditing(null)}
                disabled={saving}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-white disabled:opacity-50"
              >
                Annuleer
              </button>
              <button
                onClick={saveEdit}
                disabled={saving}
                data-testid="synapse-edit-save"
                className="px-4 py-1.5 rounded-lg text-xs font-medium text-white bg-amber-500/20 border border-amber-500/40 hover:bg-amber-500/30 disabled:opacity-50 flex items-center gap-2"
              >
                <Save className="w-3 h-3" />
                {saving ? 'Opslaan…' : 'Opslaan'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SynapseTab;
