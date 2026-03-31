import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

function DebugTab() {
  const [logs, setLogs] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [filter, setFilter] = useState('all'); // all, errors, success

  const loadLogs = async () => {
    try {
      const response = await axios.get(`${API}/admin/debug/logs?limit=100`);
      setLogs(response.data.logs || []);
    } catch (error) {
      console.error("Could not load logs:", error);
    }
  };

  const clearLogs = async () => {
    if (!window.confirm("Weet je zeker dat je alle logs wilt verwijderen?")) return;
    try {
      await axios.delete(`${API}/admin/debug/logs`);
      setLogs([]);
    } catch (error) {
      alert("Kon logs niet verwijderen");
    }
  };

  useEffect(() => {
    loadLogs();
    
    if (autoRefresh) {
      const interval = setInterval(loadLogs, 2000); // Refresh every 2 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const filteredLogs = logs.filter(log => {
    if (filter === 'errors') return !log.success;
    if (filter === 'success') return log.success;
    return true;
  });

  const getActionColor = (action) => {
    if (action.includes('DELETE') || action.includes('TRASH')) return 'text-red-400';
    if (action.includes('RESTORE') || action.includes('CREATE')) return 'text-green-400';
    if (action.includes('UPDATE') || action.includes('SAVE')) return 'text-blue-400';
    return 'text-gray-400';
  };

  const getStatusIcon = (success) => {
    return success ? '✅' : '❌';
  };

  return (
    <div className="p-6 max-w-7xl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">🐛 Debug Console</h2>
        <p className="text-gray-400">Live logging van alle Spark acties</p>
      </div>

      {/* Controls */}
      <div className="bg-slate-800/50 border border-purple-500/30 p-4 rounded-lg mb-4">
        <div className="flex items-center justify-between">
          <div className="flex gap-4">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded ${filter === 'all' ? 'bg-purple-500 text-white' : 'bg-slate-700 text-gray-400'}`}
            >
              Alles ({logs.length})
            </button>
            <button
              onClick={() => setFilter('errors')}
              className={`px-4 py-2 rounded ${filter === 'errors' ? 'bg-red-500 text-white' : 'bg-slate-700 text-gray-400'}`}
            >
              Errors ({logs.filter(l => !l.success).length})
            </button>
            <button
              onClick={() => setFilter('success')}
              className={`px-4 py-2 rounded ${filter === 'success' ? 'bg-green-500 text-white' : 'bg-slate-700 text-gray-400'}`}
            >
              Success ({logs.filter(l => l.success).length})
            </button>
          </div>

          <div className="flex gap-2">
            <label className="flex items-center gap-2 text-gray-300">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              Auto-refresh (2s)
            </label>
            <button
              onClick={loadLogs}
              className="px-4 py-2 bg-blue-500/20 text-blue-300 rounded hover:bg-blue-500/30"
            >
              🔄 Refresh
            </button>
            <button
              onClick={clearLogs}
              className="px-4 py-2 bg-red-500/20 text-red-300 rounded hover:bg-red-500/30"
            >
              🗑️ Clear
            </button>
          </div>
        </div>
      </div>

      {/* Logs */}
      <div className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-4 font-mono text-sm max-h-[600px] overflow-y-auto">
        {filteredLogs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            Geen logs gevonden. Voer een actie uit om logs te zien.
          </div>
        ) : (
          <div className="space-y-2">
            {filteredLogs.reverse().map((log, idx) => (
              <div
                key={idx}
                className={`p-3 rounded ${log.success ? 'bg-slate-800/50' : 'bg-red-900/20 border border-red-500/30'}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <span className="text-lg">{getStatusIcon(log.success)}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`font-bold ${getActionColor(log.action)}`}>
                          {log.action}
                        </span>
                        <span className="text-purple-400">{log.entity_type}</span>
                        <span className="text-gray-500 text-xs">{log.entity_id}</span>
                      </div>
                      {Object.keys(log.details).length > 0 && (
                        <div className="mt-1 text-xs text-gray-400">
                          {JSON.stringify(log.details)}
                        </div>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-gray-600">
                    {new Date(log.timestamp).toLocaleTimeString('nl-NL')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="mt-4 p-4 bg-slate-800/30 rounded-lg">
        <p className="text-sm text-gray-400 mb-2"><strong>Legend:</strong></p>
        <div className="grid grid-cols-3 gap-2 text-xs text-gray-500">
          <div><span className="text-red-400">DELETE/TRASH</span> - Item verwijderd</div>
          <div><span className="text-green-400">RESTORE/CREATE</span> - Item toegevoegd/hersteld</div>
          <div><span className="text-blue-400">UPDATE/SAVE</span> - Item aangepast/opgeslagen</div>
        </div>
      </div>
    </div>
  );
}

export default DebugTab;
