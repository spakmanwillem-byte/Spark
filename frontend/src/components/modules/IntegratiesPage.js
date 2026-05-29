import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Search, FolderOpen, FileCode, FilePlus, Package, Play, Link2, Trash2,
  Save, X, ChevronRight, Code, AlertTriangle, CheckCircle, Lock,
  Plus, TestTube, Puzzle, Eye, FileText, Loader2,
  Archive, Download, Upload, Clock, RotateCcw
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function IntegratiesPage({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('files');

  const tabs = [
    { id: 'files', label: 'Bestanden', icon: FolderOpen, accent: '#3b82f6' },
    { id: 'sandbox', label: 'Module Sandbox', icon: Package, accent: '#a855f7' },
    { id: 'backup', label: 'Backup Systeem', icon: Archive, accent: '#10b981' },
  ];

  return (
    <MainLayout activePage="integrations" onNavigate={onNavigate}>
      <div data-testid="integraties-page" className="h-full flex flex-col">
        {/* Top banner with tabs */}
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
              <Puzzle className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Integraties</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Bestanden & Modules</p>
            </div>
          </div>
          <div className="flex">
            {tabs.map(tab => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  data-testid={`tab-${tab.id}`}
                  onClick={() => setActiveTab(tab.id)}
                  className="relative flex items-center gap-2 px-5 py-2.5 text-sm font-medium transition-colors"
                  style={{ color: isActive ? tab.accent : '#94a3b8' }}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                  {isActive && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full" style={{ background: tab.accent }} />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'files' && <FileBrowser />}
          {activeTab === 'sandbox' && <ModuleSandbox />}
          {activeTab === 'backup' && <BackupPanel />}
        </div>
      </div>
    </MainLayout>
  );
}

/* ================================================================ */
/*  FILE BROWSER                                                     */
/* ================================================================ */
function FileBrowser() {
  const [tree, setTree] = useState([]);
  const [allFiles, setAllFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [selectedFile, setSelectedFile] = useState(null);
  const [content, setContent] = useState('');
  const [editedContent, setEditedContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [validation, setValidation] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API}/api/files/tree`);
        const data = await res.json();
        if (data.success) {
          setTree(data.tree);
          const flat = [];
          data.tree.forEach(dir => dir.files.forEach(f => flat.push({ ...f, base: dir.name })));
          setAllFiles(flat);
        }
      } catch (e) { console.error(e); }
      setLoading(false);
    })();
  }, []);

  const filtered = allFiles.filter(f => {
    const matchSearch = !search || f.name.toLowerCase().includes(search.toLowerCase()) || f.path.toLowerCase().includes(search.toLowerCase());
    const matchType = filterType === 'all' || f.file_type === filterType;
    return matchSearch && matchType;
  });

  const openFile = async (file) => {
    setSelectedFile(file);
    setContent(''); setEditedContent(''); setValidation(null);
    try {
      const res = await fetch(`${API}/api/files/content?file_path=${encodeURIComponent(file.path)}`);
      const data = await res.json();
      if (data.success) { setContent(data.content); setEditedContent(data.content); }
    } catch (e) { console.error(e); }
  };

  const saveFile = async () => {
    if (!selectedFile || selectedFile.protected) return;
    setSaving(true);
    try {
      const res = await fetch(`${API}/api/files/save`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: selectedFile.path, content: editedContent }),
      });
      const data = await res.json();
      setValidation(data.validation);
      if (data.success) setContent(editedContent);
    } catch (e) { console.error(e); }
    setSaving(false);
  };

  const typeColors = { python: '#3572A5', javascript: '#f1e05a', json: '#40d47e', css: '#563d7c', html: '#e34c26', markdown: '#083fa1', text: '#6b7280' };
  const typeIcons = { python: 'PY', javascript: 'JS', json: '{}', css: 'CSS', html: 'HTML', markdown: 'MD', text: 'TXT' };

  if (loading) return <div className="flex-1 flex items-center justify-center"><Loader2 className="w-6 h-6 text-blue-400 animate-spin" /></div>;

  return (
    <div className="flex h-full">
      {/* File list sidebar */}
      <div className="w-72 md:w-80 bg-slate-900/40 border-r border-slate-800 flex flex-col flex-shrink-0">
        <div className="p-3 space-y-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
            <input
              data-testid="file-search"
              type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Zoek bestand..."
              className="w-full pl-8 pr-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:border-amber-500/50 focus:outline-none"
            />
          </div>
          <select
            data-testid="file-filter"
            value={filterType} onChange={e => setFilterType(e.target.value)}
            className="w-full px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-slate-300 focus:outline-none"
          >
            <option value="all">Alle types</option>
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
            <option value="json">JSON</option>
            <option value="markdown">Markdown</option>
            <option value="css">CSS</option>
            <option value="html">HTML</option>
            <option value="text">Tekst</option>
            <option value="yaml">YAML</option>
          </select>
        </div>
        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {filtered.map((f, i) => (
            <button
              key={i}
              onClick={() => openFile(f)}
              className={`w-full text-left flex items-center gap-2.5 px-3 py-2 rounded-lg mb-0.5 transition-colors ${
                selectedFile?.path === f.path ? 'bg-blue-500/10 border border-blue-500/20' : 'hover:bg-slate-800/50'
              }`}
            >
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded" style={{ background: `${typeColors[f.file_type] || '#6b7280'}25`, color: typeColors[f.file_type] || '#6b7280' }}>
                {typeIcons[f.file_type] || 'F'}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-xs text-white truncate">{f.name}</p>
                <p className="text-[10px] text-slate-600 truncate">{f.directory}</p>
              </div>
              {f.protected && <Lock className="w-3 h-3 text-slate-600 flex-shrink-0" />}
            </button>
          ))}
        </div>
        <div className="p-3 border-t border-slate-800 text-[10px] text-slate-500">
          {filtered.length} bestanden
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col bg-slate-950">
        {selectedFile ? (
          <>
            <div className="h-12 px-4 flex items-center justify-between border-b border-slate-800 bg-slate-900/30 flex-shrink-0">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-blue-400" />
                <span className="text-sm text-white font-medium">{selectedFile.name}</span>
                {selectedFile.protected && <span className="text-[9px] px-1.5 py-0.5 bg-red-500/15 text-red-400 rounded">Beschermd</span>}
                {editedContent !== content && <span className="w-2 h-2 rounded-full bg-amber-400 flex-shrink-0" />}
              </div>
              <div className="flex items-center gap-2">
                {validation && (
                  validation.valid
                    ? <span className="text-[10px] text-green-400 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> OK</span>
                    : <span className="text-[10px] text-red-400 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Fouten</span>
                )}
                {!selectedFile.protected && (
                  <button
                    data-testid="save-file-btn"
                    onClick={saveFile}
                    disabled={saving || editedContent === content}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all disabled:opacity-30"
                    style={{ background: editedContent !== content ? '#3b82f6' : '#334155', color: 'white' }}
                  >
                    <Save className="w-3 h-3" /> {saving ? 'Opslaan...' : 'Opslaan'}
                  </button>
                )}
              </div>
            </div>
            <div className="flex-1 overflow-hidden relative">
              <textarea
                data-testid="code-editor"
                value={editedContent}
                onChange={e => setEditedContent(e.target.value)}
                readOnly={selectedFile.protected}
                spellCheck={false}
                className="w-full h-full p-4 bg-transparent text-slate-200 text-xs font-mono leading-relaxed resize-none focus:outline-none"
                style={{ tabSize: 2 }}
              />
            </div>
            {validation && !validation.valid && (
              <div className="p-3 border-t border-red-500/30 bg-red-500/5 max-h-32 overflow-y-auto">
                {validation.errors.map((e, i) => (
                  <p key={i} className="text-xs text-red-400 mb-1">Lijn {e.line}: {e.message}</p>
                ))}
              </div>
            )}
            <div className="h-8 px-4 flex items-center justify-between border-t border-slate-800 bg-slate-900/30 text-[10px] text-slate-500">
              <span>Lijnen: {editedContent.split('\n').length}</span>
              <span>{selectedFile.file_type}</span>
              <span>Ctrl+S om op te slaan</span>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <FolderOpen className="w-12 h-12 text-slate-700 mx-auto mb-3" />
              <p className="text-slate-400 text-sm">Selecteer een bestand</p>
              <p className="text-slate-600 text-xs mt-1">Zoek en bekijk alle Spark Core bestanden</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ================================================================ */
/*  MODULE SANDBOX                                                   */
/* ================================================================ */
function ModuleSandbox() {
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('fullstack');
  const [newDesc, setNewDesc] = useState('');
  const [testResult, setTestResult] = useState(null);

  const loadModules = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/modules/list`);
      const data = await res.json();
      if (data.success) setModules(data.modules);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { loadModules(); }, [loadModules]);

  const createModule = async () => {
    if (!newName.trim()) return;
    try {
      const res = await fetch(`${API}/api/modules/create`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName, type: newType, description: newDesc }),
      });
      const data = await res.json();
      if (data.success) { setShowCreate(false); setNewName(''); setNewDesc(''); loadModules(); }
    } catch (e) { console.error(e); }
  };

  const testModule = async (name) => {
    setTestResult({ loading: true, module: name });
    try {
      const res = await fetch(`${API}/api/modules/test`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module_name: name }),
      });
      const data = await res.json();
      setTestResult({ ...data, module: name, loading: false });
      if (data.success) loadModules();
    } catch (e) { setTestResult({ success: false, message: 'Fout', errors: [String(e)], module: name, loading: false }); }
  };

  const integrateModule = async (name) => {
    if (!window.confirm(`Module '${name}' integreren in de main codebase?`)) return;
    try {
      const res = await fetch(`${API}/api/modules/integrate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module_name: name }),
      });
      const data = await res.json();
      if (data.success) loadModules();
    } catch (e) { console.error(e); }
  };

  const deleteModule = async (name) => {
    if (!window.confirm(`Module '${name}' verwijderen?`)) return;
    try {
      await fetch(`${API}/api/modules/delete/${name}`, { method: 'DELETE' });
      loadModules();
    } catch (e) { console.error(e); }
  };

  return (
    <div className="h-full overflow-y-auto p-4 md:p-6 space-y-5 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Module Sandbox</h2>
          <p className="text-xs text-slate-500">Maak, test en integreer nieuwe modules veilig</p>
        </div>
        <button
          data-testid="create-module-btn"
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white transition-all"
          style={{ background: 'linear-gradient(135deg, #a855f7, #ec4899)' }}
        >
          <Plus className="w-4 h-4" /> Nieuwe Module
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="p-4 bg-slate-900/60 border border-purple-500/20 rounded-xl space-y-3">
          <h3 className="text-sm font-semibold text-white">Nieuwe Module Aanmaken</h3>
          <input
            data-testid="module-name-input"
            type="text" value={newName} onChange={e => setNewName(e.target.value)}
            placeholder="Module naam"
            className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
          />
          <select
            data-testid="module-type-select"
            value={newType} onChange={e => setNewType(e.target.value)}
            className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-slate-300 focus:outline-none"
          >
            <option value="backend">Backend (Python)</option>
            <option value="frontend">Frontend (React)</option>
            <option value="fullstack">Full-stack</option>
          </select>
          <textarea
            data-testid="module-desc-input"
            value={newDesc} onChange={e => setNewDesc(e.target.value)}
            placeholder="Beschrijving (optioneel)"
            className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none resize-none"
            rows={2}
          />
          <div className="flex gap-2">
            <button
              data-testid="confirm-create-btn"
              onClick={createModule}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white" style={{ background: '#10b981' }}
            >
              Aanmaken
            </button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-sm">
              Annuleren
            </button>
          </div>
        </div>
      )}

      {/* Modules list */}
      {loading ? (
        <div className="py-16 flex items-center justify-center"><Loader2 className="w-6 h-6 text-purple-400 animate-spin" /></div>
      ) : modules.length === 0 ? (
        <div className="py-16 text-center">
          <Package className="w-12 h-12 text-slate-700 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Nog geen modules in sandbox</p>
          <p className="text-slate-600 text-xs mt-1">Klik "Nieuwe Module" om te beginnen</p>
        </div>
      ) : (
        <div className="space-y-3">
          {modules.map(mod => (
            <div key={mod.name} className="p-4 bg-slate-900/40 border border-slate-800 rounded-xl flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{
                background: mod.integrated ? '#3b82f620' : mod.tested ? '#10b98120' : '#a855f720'
              }}>
                {mod.integrated ? <Link2 className="w-5 h-5 text-blue-400" /> :
                 mod.tested ? <CheckCircle className="w-5 h-5 text-green-400" /> :
                 <Package className="w-5 h-5 text-purple-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-white">{mod.display_name}</h3>
                  <span className="text-[10px] px-1.5 py-0.5 rounded font-medium" style={{
                    background: mod.integrated ? '#3b82f620' : mod.tested ? '#10b98120' : '#f59e0b20',
                    color: mod.integrated ? '#60a5fa' : mod.tested ? '#34d399' : '#fbbf24',
                  }}>
                    {mod.integrated ? 'Geïntegreerd' : mod.tested ? 'Getest' : 'Sandbox'}
                  </span>
                  <span className="text-[10px] text-slate-600">{mod.type}</span>
                </div>
                {mod.description && <p className="text-xs text-slate-400 mb-2">{mod.description}</p>}
              </div>
              <div className="flex items-center gap-1.5 flex-shrink-0">
                {!mod.integrated && !mod.tested && (
                  <button data-testid={`test-${mod.name}`} onClick={() => testModule(mod.name)} className="p-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 rounded-lg transition-colors" title="Testen">
                    <Play className="w-4 h-4" />
                  </button>
                )}
                {mod.tested && !mod.integrated && (
                  <button data-testid={`integrate-${mod.name}`} onClick={() => integrateModule(mod.name)} className="p-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors" title="Integreren">
                    <Link2 className="w-4 h-4" />
                  </button>
                )}
                <button data-testid={`delete-${mod.name}`} onClick={() => deleteModule(mod.name)} className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors" title="Verwijderen">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Test result */}
      {testResult && !testResult.loading && (
        <div className={`p-4 rounded-xl border ${testResult.success ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
          <p className={`text-sm font-medium mb-2 ${testResult.success ? 'text-green-400' : 'text-red-400'}`}>
            {testResult.success ? 'Test geslaagd!' : 'Test gefaald'}
          </p>
          {testResult.output && (
            <pre className="text-xs text-green-300 bg-slate-900/50 p-3 rounded-lg overflow-x-auto">{testResult.output}</pre>
          )}
          {testResult.errors && testResult.errors.map((e, i) => (
            <p key={i} className="text-xs text-red-400 mt-1">{e}</p>
          ))}
        </div>
      )}
    </div>
  );
}

export default IntegratiesPage;


/* ================================================================ */
/*  BACKUP PANEL  -  v4_backup_001                                   */
/* ================================================================ */
function BackupPanel() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null); // 'mark' | 'full' | 'changes' | 'preview' | 'restore'
  const [toast, setToast] = useState(null);
  const [restoreFile, setRestoreFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  const loadStatus = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/backup/status`);
      const data = await res.json();
      setStatus(data);
    } catch (e) {
      showToast('Status kon niet geladen worden', 'error');
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadStatus(); }, [loadStatus]);

  const markDeployed = async () => {
    if (!window.confirm('Markeer huidige status als "laatste deploy"?\n\nVanaf nu wordt elk gewijzigd bestand opgenomen in de "Wijzigingen sinds deploy" backup.')) return;
    setBusy('mark');
    try {
      const res = await fetch(`${API}/api/backup/mark-deployed`, { method: 'POST' });
      const data = await res.json();
      if (data.ok) {
        showToast('Deploy-marker gezet', 'success');
        await loadStatus();
      } else {
        showToast('Markeren mislukt', 'error');
      }
    } catch (e) { showToast('Fout: ' + e.message, 'error'); }
    setBusy(null);
  };

  // v4_mr_smith_001 — dialog state
  const [mrSmithOpen, setMrSmithOpen] = useState(false);
  const [pendingDownloadType, setPendingDownloadType] = useState(null);

  const triggerDownload = (type) => {
    // Mr Smith waarschuwing eerst
    setPendingDownloadType(type);
    setMrSmithOpen(true);
  };

  const downloadZip = (type) => {
    // Directe browser-download via API URL.
    // Backend stuurt Content-Disposition: attachment, browser opent vanzelf "Opslaan als..."
    // Dit is betrouwbaarder dan fetch+blob voor grote bestanden (>10MB).
    setBusy(type);
    setMrSmithOpen(false);
    try {
      const url = type === 'full'
        ? `${API}/api/backup/download/full`
        : `${API}/api/backup/download/changes`;
      const a = document.createElement('a');
      a.href = url;
      a.rel = 'noopener';
      // download-attribuut forceert browser om Content-Disposition filename te respecteren
      a.download = '';
      document.body.appendChild(a);
      a.click();
      a.remove();
      // Anchor pas zetten ná download-trigger (Mr Smith principe)
      fetch(`${API}/api/backup/anchor`, { method: 'POST' }).catch(() => {});
      showToast(`Download gestart — check je Downloads map`, 'success');
    } catch (e) {
      showToast('Download fout: ' + e.message, 'error');
    }
    // Reset busy state na korte tijd (download loopt op de achtergrond)
    setTimeout(() => setBusy(null), 1500);
  };

  // v5_kb_diff_export_001 — Slim klein KB-diff bestand downloaden
  const downloadKbDiff = () => {
    setBusy('kb-diff');
    try {
      const a = document.createElement('a');
      a.href = `${API}/api/backup/kb-changed-since-deploy`;
      a.rel = 'noopener';
      a.download = '';
      document.body.appendChild(a);
      a.click();
      a.remove();
      showToast('KB-diff download gestart (klein JSON-bestand)', 'success');
    } catch (e) {
      showToast('Download fout: ' + e.message, 'error');
    }
    setTimeout(() => setBusy(null), 1500);
  };

  const previewRestore = async (file) => {
    setRestoreFile(file);
    setPreview(null);
    setBusy('preview');
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${API}/api/backup/restore/preview`, { method: 'POST', body: form });
      const data = await res.json();
      if (res.ok) {
        setPreview(data);
      } else {
        showToast(data.detail || 'Preview mislukt', 'error');
        setRestoreFile(null);
      }
    } catch (e) {
      showToast('Preview fout: ' + e.message, 'error');
      setRestoreFile(null);
    }
    setBusy(null);
  };

  const doRestore = async () => {
    if (!restoreFile) return;
    setBusy('restore');
    setShowConfirm(false);
    try {
      const form = new FormData();
      form.append('file', restoreFile);
      form.append('confirm', 'true');
      const res = await fetch(`${API}/api/backup/restore`, { method: 'POST', body: form });
      const data = await res.json();
      if (res.ok && data.ok) {
        showToast(`Restore klaar: ${data.created_count} nieuw, ${data.overwritten_count} overschreven`, 'success');
        setRestoreFile(null);
        setPreview(null);
        await loadStatus();
      } else {
        showToast(data.detail || 'Restore mislukt', 'error');
      }
    } catch (e) { showToast('Restore fout: ' + e.message, 'error'); }
    setBusy(null);
  };

  if (loading) {
    return <div className="flex-1 flex items-center justify-center"><Loader2 className="w-6 h-6 text-emerald-400 animate-spin" /></div>;
  }

  const marker = status?.marker || {};
  const hasMarker = !!marker.marked_at;

  return (
    <div data-testid="backup-panel" className="h-full overflow-y-auto p-6 space-y-6">
      {/* Toast */}
      {toast && (
        <div data-testid="backup-toast" className={`fixed top-20 right-6 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
          toast.type === 'success' ? 'bg-emerald-500/90 text-white' :
          toast.type === 'error' ? 'bg-red-500/90 text-white' : 'bg-slate-700/90 text-white'
        }`}>
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="max-w-4xl">
        <div className="flex items-center gap-3 mb-2">
          <Archive className="w-6 h-6 text-emerald-400" />
          <h2 className="text-xl font-bold text-white">Spark Backup Systeem</h2>
        </div>
        <p className="text-sm text-slate-400">
          Download alle Spark-data als ZIP naar je computer. Werkt zonder externe database — past bij offline-first filosofie.
          Restore is altijd <strong className="text-emerald-300">merge-only</strong> (overschrijft of voegt toe, verwijdert nooit).
        </p>
      </div>

      {/* Status card */}
      <div className="max-w-4xl bg-slate-900/40 border border-slate-800 rounded-xl p-5">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-400" />
              Status
            </h3>
            <p className="text-xs text-slate-500 mt-1">Wat zit er in het systeem en wat is er veranderd sinds laatste deploy.</p>
          </div>
          <button
            data-testid="backup-refresh"
            onClick={loadStatus}
            className="text-xs text-slate-400 hover:text-white flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-slate-800/50"
          >
            <RotateCcw className="w-3 h-3" /> Vernieuwen
          </button>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-4">
          <Stat label="Bestanden totaal" value={status?.total_files ?? 0} accent="text-blue-300" />
          <Stat label="Gewijzigd sinds deploy" value={status?.changed_files_count ?? 0} accent="text-emerald-300" />
          <Stat
            label="Laatste deploy"
            value={hasMarker ? new Date(marker.marked_at).toLocaleString('nl-NL') : 'Niet ingesteld'}
            accent={hasMarker ? 'text-slate-200' : 'text-amber-300'}
            small
          />
        </div>

        <button
          data-testid="backup-mark-deployed"
          onClick={markDeployed}
          disabled={busy === 'mark'}
          className="w-full text-sm font-medium px-4 py-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-200 hover:bg-amber-500/20 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {busy === 'mark' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Clock className="w-4 h-4" />}
          Markeer huidige status als "laatste deploy"
        </button>
        <p className="text-[11px] text-slate-500 mt-2">
          Klik hier <strong className="text-amber-200">direct na een succesvolle deploy</strong>. Vanaf dat moment telt elk gewijzigd bestand mee in de "Wijzigingen"-backup.
        </p>
      </div>

      {/* Download buttons */}
      <div className="max-w-4xl grid md:grid-cols-3 gap-4">
        <DownloadCard
          testid="backup-download-changes"
          icon={Download}
          title="Alleen wijzigingen"
          subtitle={`${status?.changed_files_count ?? 0} bestand(en) sinds laatste deploy`}
          desc="ZIP met alle gewijzigde bestanden (data + memory). Inclusief grote KB."
          color="emerald"
          loading={busy === 'changes'}
          disabled={!hasMarker && (status?.changed_files_count ?? 0) > 50}
          warning={!hasMarker ? 'Geen deploy-marker — alles wordt als "gewijzigd" gezien.' : null}
          onClick={() => triggerDownload('changes')}
        />
        <DownloadCard
          testid="backup-download-kb-diff"
          icon={Download}
          title="Alleen KB-diff (slim)"
          subtitle="Klein JSON-bestand"
          desc="Alleen kennis-kaarten die sinds laatste deploy gewijzigd of nieuw zijn. Veel kleiner dan volledige KB. Mergebaar via 'Restore' (KB-tab)."
          color="amber"
          loading={busy === 'kb-diff'}
          onClick={() => downloadKbDiff()}
        />
        <DownloadCard
          testid="backup-download-full"
          icon={Archive}
          title="Volledige backup"
          subtitle={`${status?.total_files ?? 0} bestanden`}
          desc="Complete ZIP van alle Spark-data (data/ + memory/). Groter maar volledig."
          color="blue"
          loading={busy === 'full'}
          onClick={() => triggerDownload('full')}
        />
      </div>

      {/* Restore */}
      <div className="max-w-4xl bg-slate-900/40 border border-slate-800 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
          <Upload className="w-4 h-4 text-purple-400" />
          Backup terugzetten (merge)
        </h3>
        <p className="text-xs text-slate-500 mb-4">
          Sleep een ZIP hierheen, bekijk wat er gemerged wordt, bevestig daarna. <strong className="text-emerald-300">Niets wordt verwijderd</strong> — alleen nieuwe en gewijzigde bestanden worden toegepast.
        </p>

        <label data-testid="backup-restore-upload" className="block border-2 border-dashed border-slate-700 hover:border-purple-500/50 rounded-lg p-6 text-center cursor-pointer transition-colors">
          <input
            type="file"
            accept=".zip"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) previewRestore(f);
              e.target.value = '';
            }}
          />
          <Upload className="w-6 h-6 text-slate-500 mx-auto mb-2" />
          <p className="text-sm text-slate-300">
            {restoreFile ? <span className="text-purple-300">{restoreFile.name}</span> : 'Klik om een .zip te kiezen'}
          </p>
          <p className="text-[11px] text-slate-500 mt-1">Geen automatische restore — je krijgt eerst een preview.</p>
        </label>

        {busy === 'preview' && (
          <div className="mt-4 flex items-center gap-2 text-xs text-slate-400">
            <Loader2 className="w-4 h-4 animate-spin" /> ZIP wordt geanalyseerd...
          </div>
        )}

        {preview && (
          <div data-testid="backup-preview" className="mt-4 bg-slate-950/50 border border-slate-800 rounded-lg p-4">
            <p className="text-xs text-slate-400 mb-3">
              Preview voor <strong className="text-white">{preview.summary?.filename}</strong> ({Math.round((preview.summary?.size_bytes || 0) / 1024)} KB)
            </p>
            <div className="grid grid-cols-4 gap-2 mb-3">
              <PreviewStat label="Nieuw" count={preview.summary?.new_count} color="text-emerald-300" />
              <PreviewStat label="Wijzigen" count={preview.summary?.modified_count} color="text-amber-300" />
              <PreviewStat label="Identiek" count={preview.summary?.identical_count} color="text-slate-400" />
              <PreviewStat label="Overgeslagen" count={preview.summary?.skipped_count} color="text-red-300" />
            </div>

            {preview.summary?.modified_count > 0 && (
              <details className="text-xs text-slate-400 mb-2">
                <summary className="cursor-pointer hover:text-white">Te wijzigen bestanden ({preview.summary.modified_count})</summary>
                <ul className="mt-2 max-h-40 overflow-y-auto space-y-1">
                  {(preview.details?.modified || []).slice(0, 100).map((f, i) => (
                    <li key={i} className="text-amber-200/80 truncate">~ {f.path}</li>
                  ))}
                </ul>
              </details>
            )}
            {preview.summary?.new_count > 0 && (
              <details className="text-xs text-slate-400 mb-3">
                <summary className="cursor-pointer hover:text-white">Nieuwe bestanden ({preview.summary.new_count})</summary>
                <ul className="mt-2 max-h-40 overflow-y-auto space-y-1">
                  {(preview.details?.new || []).slice(0, 100).map((f, i) => (
                    <li key={i} className="text-emerald-300/80 truncate">+ {f.path}</li>
                  ))}
                </ul>
              </details>
            )}

            <div className="flex gap-2 mt-3">
              <button
                data-testid="backup-restore-confirm"
                onClick={() => setShowConfirm(true)}
                disabled={busy === 'restore' || (preview.summary?.new_count + preview.summary?.modified_count) === 0}
                className="flex-1 px-4 py-2 text-sm font-medium rounded-lg bg-purple-500/20 border border-purple-500/40 text-purple-200 hover:bg-purple-500/30 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {busy === 'restore' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                Merge toepassen
              </button>
              <button
                data-testid="backup-restore-cancel"
                onClick={() => { setRestoreFile(null); setPreview(null); }}
                className="px-4 py-2 text-sm text-slate-300 hover:text-white rounded-lg hover:bg-slate-800/50"
              >
                Annuleren
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Changed files preview list */}
      {(status?.changed_files?.length ?? 0) > 0 && (
        <div className="max-w-4xl bg-slate-900/40 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Gewijzigde bestanden ({status.changed_files_count})</h3>
          <div className="max-h-60 overflow-y-auto space-y-1 text-xs">
            {status.changed_files.slice(0, 200).map((f, i) => (
              <div key={i} className="flex justify-between gap-3 text-slate-400 hover:text-slate-200 py-1 border-b border-slate-800/40">
                <span className="truncate font-mono">{f.path}</span>
                <span className="text-slate-600 text-[10px] whitespace-nowrap">{new Date(f.mtime).toLocaleString('nl-NL')}</span>
              </div>
            ))}
            {status.changed_files_count > 200 && (
              <p className="text-[11px] text-slate-500 text-center pt-2">... en nog {status.changed_files_count - 200} meer</p>
            )}
          </div>
        </div>
      )}

      {/* Confirm dialog */}
      {showConfirm && preview && (
        <div data-testid="backup-confirm-dialog" className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="bg-slate-900 border border-purple-500/40 rounded-xl p-6 max-w-md w-full">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h4 className="text-base font-semibold text-white">Bevestig merge</h4>
            </div>
            <p className="text-sm text-slate-300 mb-2">
              <strong className="text-emerald-300">{preview.summary?.new_count}</strong> nieuwe bestanden worden toegevoegd,
              <strong className="text-amber-300"> {preview.summary?.modified_count}</strong> bestaande bestanden worden overschreven.
            </p>
            <p className="text-xs text-slate-500 mb-4">
              Lokale bestanden die niet in de ZIP zitten blijven onaangetast. Deze actie is niet automatisch terug te draaien — maak eerst een volledige backup als je twijfelt.
            </p>
            <div className="flex gap-2">
              <button
                data-testid="backup-confirm-yes"
                onClick={doRestore}
                className="flex-1 px-4 py-2 text-sm font-medium rounded-lg bg-amber-500 hover:bg-amber-600 text-white"
              >
                Ja, merge toepassen
              </button>
              <button
                data-testid="backup-confirm-no"
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 text-sm text-slate-300 hover:text-white rounded-lg hover:bg-slate-800/50"
              >
                Annuleren
              </button>
            </div>
          </div>
        </div>
      )}

      {/* v4_mr_smith_001 — Mr. Smith waarschuwing vóór backup-download */}
      {mrSmithOpen && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div data-testid="mr-smith-dialog" className="bg-gradient-to-br from-slate-900 to-slate-950 border border-amber-500/40 rounded-2xl max-w-lg w-full p-6 shadow-2xl shadow-amber-500/10">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-2xl">🕴️</div>
              <div className="flex-1">
                <h3 className="text-base font-bold text-amber-400 mb-1">Een ogenblik, Mr. Anderson...</h3>
                <p className="text-xs text-slate-400">Authenticatie van Spark's geheugen</p>
              </div>
            </div>
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 mb-5 text-sm text-slate-200 italic leading-relaxed">
              "Alle informatie wordt vanaf dit moment niet meer bewaard op deze server.
              De zip die u nu gaat downloaden wordt het nieuwe anker van Spark. Bewaar
              hem zoals u uw eigen geheugen zou bewaren. Begrijpen wij elkaar?"
            </div>
            <div className="flex items-center gap-2 justify-end">
              <button data-testid="mr-smith-cancel"
                onClick={() => { setMrSmithOpen(false); setPendingDownloadType(null); }}
                className="px-4 py-2 text-sm text-slate-400 hover:text-white rounded-lg hover:bg-slate-800/50">
                Annuleren
              </button>
              <button data-testid="mr-smith-confirm"
                onClick={() => downloadZip(pendingDownloadType)}
                className="px-5 py-2 text-sm bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold rounded-lg transition-colors">
                Ik begrijp het — download
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, accent, small }) {
  return (
    <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-3">
      <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">{label}</p>
      <p className={`${small ? 'text-xs' : 'text-xl'} font-bold ${accent}`}>{value}</p>
    </div>
  );
}

function PreviewStat({ label, count, color }) {
  return (
    <div className="bg-slate-900/60 rounded-md p-2 text-center">
      <p className={`text-lg font-bold ${color}`}>{count ?? 0}</p>
      <p className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</p>
    </div>
  );
}

function DownloadCard({ testid, icon: Icon, title, subtitle, desc, color, loading, disabled, warning, onClick }) {
  const colorMap = {
    emerald: 'border-emerald-500/30 hover:border-emerald-500/60 text-emerald-300 bg-emerald-500/5',
    blue: 'border-blue-500/30 hover:border-blue-500/60 text-blue-300 bg-blue-500/5',
  };
  return (
    <button
      data-testid={testid}
      onClick={onClick}
      disabled={loading || disabled}
      className={`text-left p-4 rounded-xl border transition-all disabled:opacity-50 disabled:cursor-not-allowed ${colorMap[color]}`}
    >
      <div className="flex items-center gap-2 mb-1">
        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Icon className="w-5 h-5" />}
        <h4 className="text-sm font-semibold text-white">{title}</h4>
      </div>
      <p className="text-xs text-slate-400 mb-2">{subtitle}</p>
      <p className="text-[11px] text-slate-500 leading-relaxed">{desc}</p>
      {warning && <p className="text-[11px] text-amber-300 mt-2">⚠ {warning}</p>}
    </button>
  );
}
