import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const StatusTabNew = () => {
  const [activeSubTab, setActiveSubTab] = useState('system');
  const [systemHealth, setSystemHealth] = useState({
    backend: 'online',
    database: 'connected',
    session: 'active'
  });
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSystemHealth();
  }, []);

  const loadSystemHealth = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/system/status`);
      if (response.data) {
        // Map API response to component state
        setSystemHealth({
          backend: response.data.status === 'operational' ? 'online' : 'offline',
          database: 'connected',
          session: 'active',
          health: response.data.health,
          users_count: response.data.users_count,
          knowledge_count: response.data.knowledge_count,
          version: response.data.version
        });
      }
    } catch (error) {
      console.error('Error loading system health:', error);
      setSystemHealth({
        backend: 'offline',
        database: 'unknown',
        session: 'inactive'
      });
    } finally {
      setLoading(false);
    }
  };

  const subTabs = [
    { id: 'system', icon: '💚', label: 'System Health' },
    { id: 'performance', icon: '⚡', label: 'Performance' },
  ];

  const getStatusColor = (status) => {
    if (status === 'running' || status === 'online' || status === 'connected' || status === 'active') {
      return 'text-green-400';
    }
    if (status === 'stopped' || status === 'offline' || status === 'disconnected') {
      return 'text-red-400';
    }
    return 'text-yellow-400';
  };

  const getStatusIcon = (status) => {
    if (status === 'running' || status === 'online' || status === 'connected' || status === 'active') {
      return '🟢';
    }
    if (status === 'stopped' || status === 'offline' || status === 'disconnected') {
      return '🔴';
    }
    return '🟡';
  };

  return (
    <div className="p-6">
      {/* Sub-tabs */}
      <div className="flex gap-2 mb-6 border-b border-slate-700 pb-2">
        {subTabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id)}
            className={`px-4 py-2 rounded-t-lg transition-colors ${
              activeSubTab === tab.id
                ? 'bg-purple-500/20 text-purple-300 border-b-2 border-purple-500'
                : 'text-gray-400 hover:text-white hover:bg-slate-700/30'
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="max-w-6xl">
        {activeSubTab === 'system' && (
          <div className="space-y-6">
            {/* System Health Overview */}
            <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 p-6 rounded-lg">
              <h2 className="text-2xl font-bold text-white mb-2">💚 System Health</h2>
              <p className="text-gray-300">Real-time status van alle Spark services</p>
            </div>

            {/* Core Services Status */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">🔧 Core Services</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Backend */}
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-300 font-medium">Backend API</span>
                    <span className="text-2xl">{getStatusIcon(systemHealth.backend)}</span>
                  </div>
                  <div className={`text-sm ${getStatusColor(systemHealth.backend)}`}>
                    {systemHealth.backend.toUpperCase()}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">FastAPI Server</div>
                </div>

                {/* Database */}
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-300 font-medium">Database</span>
                    <span className="text-2xl">{getStatusIcon(systemHealth.database)}</span>
                  </div>
                  <div className={`text-sm ${getStatusColor(systemHealth.database)}`}>
                    {systemHealth.database.toUpperCase()}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">MongoDB</div>
                </div>

                {/* Session */}
                <div className="bg-slate-700/50 p-4 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-300 font-medium">Session</span>
                    <span className="text-2xl">{getStatusIcon(systemHealth.session)}</span>
                  </div>
                  <div className={`text-sm ${getStatusColor(systemHealth.session)}`}>
                    {systemHealth.session.toUpperCase()}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">User Session</div>
                </div>
              </div>
            </div>

            {/* All Services */}
            {services.length > 0 && (
              <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
                <h3 className="text-xl font-bold text-white mb-4">📋 All Services</h3>
                
                <div className="space-y-2">
                  {services.map((service, idx) => (
                    <div 
                      key={idx}
                      className="bg-slate-700/30 p-3 rounded flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{getStatusIcon(service.status)}</span>
                        <div>
                          <div className="text-white font-medium">{service.name}</div>
                          <div className="text-xs text-gray-500">{service.description || 'No description'}</div>
                        </div>
                      </div>
                      <div className={`text-sm font-medium ${getStatusColor(service.status)}`}>
                        {service.status}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* System Info */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">ℹ️ System Information</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-slate-700/30 p-3 rounded">
                  <div className="text-xs text-gray-400 mb-1">Environment</div>
                  <div className="text-white font-medium">Production</div>
                </div>
                <div className="bg-slate-700/30 p-3 rounded">
                  <div className="text-xs text-gray-400 mb-1">Version</div>
                  <div className="text-white font-medium">v3.3 (71% complete)</div>
                </div>
                <div className="bg-slate-700/30 p-3 rounded">
                  <div className="text-xs text-gray-400 mb-1">Uptime</div>
                  <div className="text-white font-medium">24h 15m</div>
                </div>
                <div className="bg-slate-700/30 p-3 rounded">
                  <div className="text-xs text-gray-400 mb-1">Last Restart</div>
                  <div className="text-white font-medium">Vandaag 14:12</div>
                </div>
              </div>
            </div>

            {/* Refresh Button */}
            <button
              onClick={loadSystemHealth}
              disabled={loading}
              className="px-6 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg"
            >
              {loading ? '🔄 Laden...' : '🔄 Refresh Status'}
            </button>
          </div>
        )}

        {activeSubTab === 'performance' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">⚡ Performance Metrics</h3>
              <p className="text-gray-400 text-center py-12">
                Performance metrics worden binnenkort toegevoegd!
                <br />
                <span className="text-sm text-gray-500">
                  (Cache hit rates, query performance, error rates, response times, etc.)
                </span>
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatusTabNew;
