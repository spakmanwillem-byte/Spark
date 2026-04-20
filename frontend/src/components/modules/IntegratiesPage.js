import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Search, FolderOpen, FileCode, FilePlus, Package, Play, Link2, Trash2,
  Save, X, ChevronRight, Code, AlertTriangle, CheckCircle, Lock,
  Plus, TestTube, Puzzle, Eye, FileText, Loader2
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function IntegratiesPage({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('files');

  const tabs = [
    { id: 'files', label: 'Bestanden', icon: FolderOpen, accent: '#3b82f6' },
    { id: 'sandbox', label: 'Module Sandbox', icon: Package, accent: '#a855f7' },
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
              className="w-full pl-8 pr-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:border-blue-500/50 focus:outline-none"
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
            <option value="css">CSS</option>
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
            className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500/50"
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
