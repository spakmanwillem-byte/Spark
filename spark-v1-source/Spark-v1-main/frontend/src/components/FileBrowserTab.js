import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './FileBrowserTab.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function FileBrowserTab({ userData }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [editedContent, setEditedContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validation, setValidation] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  
  // MODULE SANDBOX
  const [showModulePanel, setShowModulePanel] = useState(false);
  const [modules, setModules] = useState([]);
  const [showCreateModule, setShowCreateModule] = useState(false);
  const [newModuleName, setNewModuleName] = useState('');
  const [newModuleType, setNewModuleType] = useState('fullstack');
  const [newModuleDesc, setNewModuleDesc] = useState('');
  const [selectedModule, setSelectedModule] = useState(null);
  const [testResult, setTestResult] = useState(null);

  const userGradatie = userData?.gradatie || 99;
  const canEdit = userGradatie === 1;

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+S or Cmd+S to save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (canEdit && selectedFile && !selectedFile.protected) {
          saveFile();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [canEdit, selectedFile, editedContent]);

  // Auto-validate when content changes
  useEffect(() => {
    if (editedContent && editedContent !== fileContent && selectedFile) {
      const debounceValidate = setTimeout(() => {
        validateContent();
      }, 1000); // Validate 1 second after stop typing

      return () => clearTimeout(debounceValidate);
    }
  }, [editedContent]);

  useEffect(() => {
    loadFileTree();
  }, []);

  const loadFileTree = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/files/tree`, {
        params: { user_gradatie: userGradatie }
      });

      if (res.data.success) {
        // Flatten tree for easier display
        const allFiles = [];
        res.data.tree.forEach(dir => {
          dir.children.forEach(file => {
            allFiles.push({
              ...file,
              directory: dir.name
            });
          });
        });
        setFiles(allFiles);
      }
    } catch (error) {
      console.error('Error loading files:', error);
      alert('❌ Kon bestanden niet laden');
    }
    setLoading(false);
  };

  const openFile = async (file) => {
    setSelectedFile(file);
    setFileContent('Loading...');
    setEditedContent('');
    setValidation(null);

    try {
      const res = await axios.get(`${API}/files/content`, {
        params: {
          file_path: file.path,
          user_gradatie: userGradatie
        }
      });

      if (res.data.success) {
        setFileContent(res.data.content);
        setEditedContent(res.data.content);
      }
    } catch (error) {
      console.error('Error loading file:', error);
      setFileContent('❌ Error loading file');
    }
  };

  const validateContent = async () => {
    if (!selectedFile) return;

    setValidating(true);
    try {
      const res = await axios.post(`${API}/files/validate`, {
        path: selectedFile.path,
        content: editedContent,
        user_id: userData?.id,
        user_gradatie: userGradatie
      });

      if (res.data.success) {
        setValidation(res.data.validation);
      }
    } catch (error) {
      console.error('Validation error:', error);
    }
    setValidating(false);
  };

  // MODULE SANDBOX FUNCTIONS
  const loadModules = async () => {
    try {
      const res = await axios.get(`${API}/modules/list`);
      if (res.data.success) {
        setModules(res.data.modules);
      }
    } catch (error) {
      console.error('Error loading modules:', error);
    }
  };

  const createModule = async () => {
    if (!newModuleName.trim()) {
      alert('Module naam is verplicht');
      return;
    }

    try {
      const res = await axios.post(`${API}/modules/create`, {
        name: newModuleName,
        type: newModuleType,
        description: newModuleDesc
      });

      if (res.data.success) {
        alert(`✅ Module '${newModuleName}' aangemaakt!`);
        setShowCreateModule(false);
        setNewModuleName('');
        setNewModuleDesc('');
        loadModules();
        loadFileTree(); // Refresh file tree
      }
    } catch (error) {
      alert('❌ Fout bij aanmaken module: ' + (error.response?.data?.detail || error.message));
    }
  };

  const testModule = async (moduleName) => {
    setTestResult({ loading: true });
    try {
      const res = await axios.post(`${API}/modules/test`, {
        module_name: moduleName
      });

      setTestResult(res.data);
      
      if (res.data.success) {
        alert('✅ Module test geslaagd! Je kunt nu integreren.');
        loadModules(); // Refresh to show test status
      } else {
        alert('❌ Module test gefaald. Check de errors.');
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Test gefaald',
        errors: [error.response?.data?.detail || error.message]
      });
    }
  };

  const integrateModule = async (moduleName) => {
    if (!window.confirm(`Weet je zeker dat je module '${moduleName}' wilt integreren? Dit verplaatst de files naar de main codebase.`)) {
      return;
    }

    try {
      const res = await axios.post(`${API}/modules/integrate`, {
        module_name: moduleName
      });

      if (res.data.success) {
        alert(`✅ ${res.data.message}\n\nGeïntegreerde files:\n${res.data.integrated_files.join('\n')}\n\n⚠️ Herstart backend/frontend om module te activeren.`);
        loadModules();
      }
    } catch (error) {
      alert('❌ Fout bij integreren: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deleteModule = async (moduleName) => {
    if (!window.confirm(`Weet je zeker dat je module '${moduleName}' wilt verwijderen?`)) {
      return;
    }

    try {
      const res = await axios.delete(`${API}/modules/delete/${moduleName}`);
      if (res.data.success) {
        alert('✅ Module verwijderd');
        loadModules();
      }
    } catch (error) {
      alert('❌ Fout bij verwijderen: ' + (error.response?.data?.detail || error.message));
    }
  };

  useEffect(() => {
    if (showModulePanel) {
      loadModules();
    }
  }, [showModulePanel]);

  const saveFile = async () => {
    if (!canEdit) {
      alert('⚠️ Alleen gradatie 1 (admin) kan bestanden bewerken');
      return;
    }

    if (!selectedFile) return;

    setSaving(true);
    try {
      const res = await axios.post(`${API}/files/save`, {
        path: selectedFile.path,
        content: editedContent,
        user_id: userData?.id,
        user_gradatie: userGradatie
      });

      if (res.data.success) {
        alert('✅ Bestand opgeslagen!');
        setFileContent(editedContent);
        setValidation(res.data.validation);
      } else if (!res.data.success && res.data.validation) {
        // Syntax errors
        setValidation(res.data.validation);
        alert('❌ Syntax errors gevonden! Fix eerst de fouten.');
      }
    } catch (error) {
      alert('❌ Fout bij opslaan: ' + (error.response?.data?.detail || error.message));
    }
    setSaving(false);
  };

  const getFileIcon = (fileType) => {
    const icons = {
      python: '🐍',
      javascript: '⚡',
      json: '📋',
      css: '🎨',
      html: '🌐',
      markdown: '📝',
      text: '📄'
    };
    return icons[fileType] || '📄';
  };

  const filteredFiles = files.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          file.path.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || file.file_type === filterType;
    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return <div className="file-browser-loading">Bestanden laden...</div>;
  }

  return (
    <div className="file-browser-container">
      <div className="file-browser-header">
        <h2>📂 File Browser</h2>
        <div className="file-browser-info">
          <button
            onClick={() => setShowModulePanel(!showModulePanel)}
            style={{
              padding: '8px 16px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600',
              marginRight: '15px'
            }}
          >
            📦 Module Sandbox
          </button>
          {canEdit ? (
            <span className="access-badge edit">✏️ Edit Access (Gradatie 1)</span>
          ) : (
            <span className="access-badge readonly">👁️ Read-Only (Gradatie {userGradatie})</span>
          )}
        </div>
      </div>

      <div className="file-browser-body">
        {/* MODULE SANDBOX PANEL */}
        {showModulePanel && (
          <div style={{
            padding: '20px',
            background: 'rgba(103, 126, 234, 0.1)',
            borderBottom: '2px solid rgba(103, 126, 234, 0.3)',
            marginBottom: '20px'
          }}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
              <h3 style={{color: 'white', margin: 0}}>📦 Module Sandbox - Stoppenkast</h3>
              <button onClick={() => setShowCreateModule(!showCreateModule)} style={{
                padding: '8px 16px',
                background: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer'
              }}>
                ➕ Add Module
              </button>
            </div>

            {showCreateModule && (
              <div style={{
                background: 'rgba(0,0,0,0.5)',
                padding: '20px',
                borderRadius: '8px',
                marginBottom: '20px'
              }}>
                <h4 style={{color: 'white', marginBottom: '15px'}}>Nieuwe Module</h4>
                <input
                  type="text"
                  placeholder="Module naam"
                  value={newModuleName}
                  onChange={(e) => setNewModuleName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px',
                    marginBottom: '10px',
                    background: 'rgba(255,255,255,0.1)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '4px',
                    color: 'white'
                  }}
                />
                <select
                  value={newModuleType}
                  onChange={(e) => setNewModuleType(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px',
                    marginBottom: '10px',
                    background: 'rgba(255,255,255,0.1)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '4px',
                    color: 'white'
                  }}
                >
                  <option value="backend">Backend (Python)</option>
                  <option value="frontend">Frontend (React)</option>
                  <option value="fullstack">Full-stack</option>
                </select>
                <textarea
                  placeholder="Beschrijving"
                  value={newModuleDesc}
                  onChange={(e) => setNewModuleDesc(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px',
                    marginBottom: '10px',
                    background: 'rgba(255,255,255,0.1)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '4px',
                    color: 'white',
                    minHeight: '60px'
                  }}
                />
                <div style={{display: 'flex', gap: '10px'}}>
                  <button onClick={createModule} style={{
                    padding: '10px 20px',
                    background: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}>
                    ✅ Create
                  </button>
                  <button onClick={() => setShowCreateModule(false)} style={{
                    padding: '10px 20px',
                    background: '#6b7280',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}>
                    Cancel
                  </button>
                </div>
              </div>
            )}

            <div style={{display: 'grid', gap: '15px', maxHeight: '400px', overflowY: 'auto'}}>
              {modules.length === 0 ? (
                <div style={{textAlign: 'center', padding: '40px', color: '#9ca3af'}}>
                  <p>Nog geen modules in sandbox</p>
                  <p style={{fontSize: '14px'}}>Click "Add Module" om te beginnen</p>
                </div>
              ) : (
                modules.map(module => (
                  <div key={module.name} style={{
                    background: 'rgba(0,0,0,0.5)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    padding: '15px',
                    display: 'flex',
                    justifyContent: 'space-between'
                  }}>
                    <div style={{flex: 1}}>
                      <h4 style={{color: 'white', margin: '0 0 5px 0'}}>{module.display_name}</h4>
                      <p style={{color: '#9ca3af', fontSize: '12px', margin: '0 0 5px 0'}}>{module.type}</p>
                      <p style={{color: '#d1d5db', fontSize: '14px', margin: '0 0 10px 0'}}>{module.description}</p>
                      <div style={{display: 'flex', gap: '8px'}}>
                        {module.tested && <span style={{background: '#10b981', color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '11px'}}>✅ Tested</span>}
                        {module.integrated && <span style={{background: '#3b82f6', color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '11px'}}>🔗 Integrated</span>}
                        {!module.tested && <span style={{background: '#f59e0b', color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '11px'}}>📦 Sandbox</span>}
                      </div>
                    </div>
                    <div style={{display: 'flex', gap: '8px', alignItems: 'flex-start'}}>
                      {!module.integrated && (
                        <>
                          <button onClick={() => testModule(module.name)} disabled={module.tested} style={{padding: '8px 12px', background: module.tested ? '#6b7280' : '#8b5cf6', color: 'white', border: 'none', borderRadius: '6px', cursor: module.tested ? 'not-allowed' : 'pointer', fontSize: '12px'}}>▶️ Test</button>
                          {module.tested && <button onClick={() => integrateModule(module.name)} style={{padding: '8px 12px', background: '#10b981', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px'}}>🔗 Integreren</button>}
                        </>
                      )}
                      <button onClick={() => deleteModule(module.name)} style={{padding: '8px 12px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px'}}>🗑️</button>
                    </div>
                  </div>
                ))
              )}
            </div>

            {testResult && !testResult.loading && (
              <div style={{marginTop: '20px', padding: '15px', background: testResult.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', border: `1px solid ${testResult.success ? '#10b981' : '#ef4444'}`, borderRadius: '8px'}}>
                <h4 style={{color: testResult.success ? '#10b981' : '#ef4444', margin: '0 0 10px 0'}}>{testResult.success ? '✅ Test Geslaagd!' : '❌ Test Gefaald'}</h4>
                <p style={{color: 'white', margin: '0 0 10px 0'}}>{testResult.message}</p>
                {testResult.output && <pre style={{background: 'rgba(0,0,0,0.5)', padding: '10px', borderRadius: '4px', color: '#10b981', fontSize: '12px', overflow: 'auto'}}>{testResult.output}</pre>}
                {testResult.errors && testResult.errors.length > 0 && (
                  <div style={{marginTop: '10px'}}>
                    {testResult.errors.map((err, idx) => <div key={idx} style={{background: 'rgba(239, 68, 68, 0.2)', padding: '8px', borderRadius: '4px', color: '#fca5a5', fontSize: '12px', marginBottom: '5px'}}>{err}</div>)}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* File List */}
        <div className="file-list-panel">
          <div className="file-list-controls">
            <input
              type="text"
              placeholder="🔍 Zoek bestand..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="filter-select"
            >
              <option value="all">Alle types</option>
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="json">JSON</option>
              <option value="css">CSS</option>
            </select>
          </div>

          <div className="file-list">
            {filteredFiles.length === 0 ? (
              <div className="no-files">Geen bestanden gevonden</div>
            ) : (
              filteredFiles.map((file, idx) => (
                <div
                  key={idx}
                  className={`file-item ${selectedFile?.path === file.path ? 'active' : ''}`}
                  onClick={() => openFile(file)}
                >
                  <span className="file-icon">{getFileIcon(file.file_type)}</span>
                  <div className="file-info">
                    <div className="file-name">{file.name}</div>
                    <div className="file-path">{file.directory}</div>
                  </div>
                  {file.editable && <span className="edit-indicator">✏️</span>}
                </div>
              ))
            )}
          </div>

          <div className="file-list-footer">
            {filteredFiles.length} bestanden
          </div>
        </div>

        {/* Code Editor */}
        <div className="code-editor-panel">
          {selectedFile ? (
            <>
              <div className="editor-header">
                <div className="editor-title">
                  {getFileIcon(selectedFile.file_type)} {selectedFile.name}
                </div>
                <div className="editor-actions">
                  {selectedFile.protected && (
                    <span className="protected-badge">🔒 Protected</span>
                  )}
                  {canEdit && !selectedFile.protected && (
                    <button
                      onClick={saveFile}
                      disabled={saving || editedContent === fileContent}
                      className="btn-save"
                    >
                      {saving ? '💾 Opslaan...' : '💾 Opslaan'}
                    </button>
                  )}
                </div>
              </div>

              <div className="editor-body">
                <div className="code-editor-with-lines">
                  <div className="line-numbers">
                    {editedContent.split('\n').map((_, idx) => (
                      <div key={idx} className="line-number">{idx + 1}</div>
                    ))}
                  </div>
                  <textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    readOnly={!canEdit || selectedFile.protected}
                    className={`code-textarea ${!canEdit || selectedFile.protected ? 'readonly' : ''}`}
                    spellCheck={false}
                  />
                </div>

                {/* Validation Messages */}
                {validation && (
                  <div className={`validation-panel ${validation.valid ? 'valid' : 'invalid'}`}>
                    {validation.valid ? (
                      <div className="validation-success">
                        ✅ Syntax OK
                        {validation.warnings.length > 0 && (
                          <div className="warnings">
                            {validation.warnings.map((warn, idx) => (
                              <div key={idx} className="warning-item">⚠️ {warn}</div>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="validation-errors">
                        <div className="error-header">❌ Syntax Errors:</div>
                        {validation.errors.map((err, idx) => (
                          <div key={idx} className="error-item">
                            <strong>Line {err.line}:</strong> {err.message}
                            {err.text && <div className="error-code">{err.text}</div>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="editor-footer">
                <span>Lijnen: {editedContent.split('\n').length}</span>
                <span>Tekens: {editedContent.length}</span>
                {validating && <span className="validating">⏳ Valideren...</span>}
                {editedContent !== fileContent && (
                  <span className="unsaved-indicator">● Niet opgeslagen</span>
                )}
                <span className="shortcut-hint">💡 Ctrl+S om op te slaan</span>
              </div>
            </>
          ) : (
            <div className="no-file-selected">
              <div className="placeholder-icon">📂</div>
              <p>Selecteer een bestand om te openen</p>
              <p className="placeholder-hint">
                {canEdit ? 'Je kunt bestanden bewerken en opslaan' : 'Je kunt bestanden alleen lezen'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* AI Assist Placeholder */}
      {canEdit && selectedFile && (
        <div className="ai-assist-placeholder">
          <button className="btn-ai-placeholder" disabled>
            🤖 AI Suggestie (Binnenkort)
          </button>
        </div>
      )}
    </div>
  );
}

export default FileBrowserTab;
