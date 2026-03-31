import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { 
  Activity, Cpu, HardDrive, MemoryStick, Wifi, Server,
  Database, Globe, Users, MessageSquare, Clock, TrendingUp,
  Layers, Network, Monitor, Zap, BarChart2, PieChart,
  ArrowUp, ArrowDown, CheckCircle, AlertCircle, RefreshCw
} from 'lucide-react';

export function AnalyticsPage({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('systeem');
  const [systemStats, setSystemStats] = useState({
    cpu: 45,
    memory: 62,
    storage: 78,
    network: 23,
  });

  // Simulate live updates
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemStats(prev => ({
        cpu: Math.min(100, Math.max(10, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.min(100, Math.max(20, prev.memory + (Math.random() - 0.5) * 5)),
        storage: prev.storage, // Storage doesn't change often
        network: Math.min(100, Math.max(5, prev.network + (Math.random() - 0.5) * 15)),
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const tabs = [
    { id: 'systeem', label: 'SYSTEEM', icon: Monitor },
    { id: 'network', label: 'NETWORK', icon: Network },
    { id: 'layer', label: 'LAYER', icon: Layers },
  ];

  return (
    <MainLayout activePage="analytics" onNavigate={onNavigate}>
      <div className="p-6 min-h-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center">
              <BarChart2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Analytics</h1>
              <p className="text-sm text-slate-400">BEHEER → Analytics</p>
            </div>
          </div>
          <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
            <RefreshCw className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white'
                  : 'bg-slate-800/50 text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'systeem' && <SystemTab stats={systemStats} />}
        {activeTab === 'network' && <NetworkTab />}
        {activeTab === 'layer' && <LayerTab />}
      </div>
    </MainLayout>
  );
}

// System Tab Content
function SystemTab({ stats }) {
  const systemInfo = [
    { label: 'Platform', value: 'Spark Core 2.0', icon: Zap },
    { label: 'Versie', value: 'v2.0.0-stable', icon: CheckCircle },
    { label: 'Server', value: 'FastAPI / Python 3.11', icon: Server },
    { label: 'Frontend', value: 'React 19 / TailwindCSS', icon: Monitor },
    { label: 'Database', value: 'JSON Storage Layer', icon: Database },
    { label: 'Uptime', value: '99.9% (30 dagen)', icon: Clock },
  ];

  return (
    <div className="space-y-6">
      {/* Resource Monitors */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ResourceCard 
          label="CPU Gebruik" 
          value={stats.cpu} 
          icon={Cpu}
          color="cyan"
          unit="%"
        />
        <ResourceCard 
          label="Geheugen" 
          value={stats.memory} 
          icon={MemoryStick}
          color="purple"
          unit="%"
        />
        <ResourceCard 
          label="Opslag" 
          value={stats.storage} 
          icon={HardDrive}
          color="amber"
          unit="%"
        />
        <ResourceCard 
          label="Netwerk" 
          value={stats.network} 
          icon={Wifi}
          color="green"
          unit="Mbps"
        />
      </div>

      {/* System Info & Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Information */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Monitor className="w-4 h-4 text-cyan-400" />
            Systeem Informatie
          </h3>
          <div className="space-y-3">
            {systemInfo.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
                <div className="flex items-center gap-2 text-slate-400">
                  <item.icon className="w-4 h-4" />
                  <span className="text-sm">{item.label}</span>
                </div>
                <span className="text-sm text-white font-medium">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Performance Graph */}
        <div className="lg:col-span-2 bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            Performance Monitor
          </h3>
          <div className="h-48 flex items-end gap-1">
            {Array.from({ length: 30 }).map((_, i) => {
              const height = 20 + Math.random() * 60;
              return (
                <div 
                  key={i}
                  className="flex-1 bg-gradient-to-t from-cyan-500/50 to-cyan-500/10 rounded-t transition-all hover:from-cyan-500 hover:to-cyan-500/30"
                  style={{ height: `${height}%` }}
                />
              );
            })}
          </div>
          <div className="flex justify-between mt-3 text-xs text-slate-500">
            <span>30 min geleden</span>
            <span>20 min</span>
            <span>10 min</span>
            <span>Nu</span>
          </div>
        </div>
      </div>

      {/* Modules Status */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Server className="w-4 h-4 text-cyan-400" />
          Module Status
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[
            { name: 'Auth', status: 'online' },
            { name: 'Storage', status: 'online' },
            { name: 'Knowledge', status: 'pending' },
            { name: 'Chat', status: 'pending' },
            { name: 'Trader', status: 'online' },
            { name: 'Analytics', status: 'online' },
          ].map((module, idx) => (
            <div key={idx} className="flex items-center gap-2 p-3 bg-slate-800/50 rounded-xl">
              <span className={`w-2 h-2 rounded-full ${
                module.status === 'online' ? 'bg-green-500' : 
                module.status === 'pending' ? 'bg-amber-500' : 'bg-red-500'
              }`} />
              <span className="text-sm text-slate-300">{module.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Network Tab Content
function NetworkTab() {
  const connections = [
    { type: 'WebSocket', count: 12, status: 'active', latency: '23ms' },
    { type: 'HTTP/REST', count: 456, status: 'active', latency: '45ms' },
    { type: 'Database', count: 3, status: 'active', latency: '5ms' },
    { type: 'External API', count: 8, status: 'active', latency: '120ms' },
  ];

  const traffic = [
    { time: '00:00', in: 120, out: 80 },
    { time: '04:00', in: 45, out: 30 },
    { time: '08:00', in: 230, out: 180 },
    { time: '12:00', in: 380, out: 290 },
    { time: '16:00', in: 420, out: 350 },
    { time: '20:00', in: 280, out: 220 },
    { time: 'Nu', in: 190, out: 140 },
  ];

  return (
    <div className="space-y-6">
      {/* Connection Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {connections.map((conn, idx) => (
          <div key={idx} className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-slate-500 uppercase">{conn.type}</span>
              <span className={`px-2 py-0.5 rounded text-xs ${
                conn.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                {conn.status}
              </span>
            </div>
            <div className="text-3xl font-bold text-white mb-1">{conn.count}</div>
            <div className="text-xs text-slate-400">Latency: {conn.latency}</div>
          </div>
        ))}
      </div>

      {/* Traffic Graph */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Network className="w-4 h-4 text-cyan-400" />
            Netwerkverkeer (24u)
          </h3>
          <div className="h-64 flex items-end justify-between gap-4">
            {traffic.map((t, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                <div className="w-full flex gap-1 items-end h-48">
                  <div 
                    className="flex-1 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded-t"
                    style={{ height: `${(t.in / 420) * 100}%` }}
                  />
                  <div 
                    className="flex-1 bg-gradient-to-t from-purple-500 to-purple-400 rounded-t"
                    style={{ height: `${(t.out / 420) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-slate-500">{t.time}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-cyan-500 rounded" />
              <span className="text-xs text-slate-400">Inkomend (MB)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-purple-500 rounded" />
              <span className="text-xs text-slate-400">Uitgaand (MB)</span>
            </div>
          </div>
        </div>

        {/* Network Info */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">Netwerk Details</h3>
          <div className="space-y-4">
            <InfoRow label="IP Adres" value="192.168.1.100" />
            <InfoRow label="Gateway" value="192.168.1.1" />
            <InfoRow label="DNS" value="8.8.8.8, 8.8.4.4" />
            <InfoRow label="SSL/TLS" value="TLS 1.3" status="secure" />
            <InfoRow label="Firewall" value="Actief" status="active" />
            <InfoRow label="Rate Limit" value="1000 req/min" />
            
            <div className="pt-4 border-t border-slate-700">
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-slate-400">Bandbreedte</span>
                <span className="text-white">1 Gbps</span>
              </div>
              <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full w-1/4 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full" />
              </div>
              <p className="text-xs text-slate-500 mt-1">250 Mbps gebruikt</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Connections */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Globe className="w-4 h-4 text-cyan-400" />
          Recente Verbindingen
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-slate-700">
                <th className="pb-3">IP Adres</th>
                <th className="pb-3">Type</th>
                <th className="pb-3">Endpoint</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Tijd</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {[
                { ip: '192.168.1.45', type: 'GET', endpoint: '/api/auth/users', status: 200, time: '2s geleden' },
                { ip: '192.168.1.32', type: 'POST', endpoint: '/api/auth/login', status: 200, time: '15s geleden' },
                { ip: '192.168.1.45', type: 'GET', endpoint: '/api/auth/gradaties', status: 200, time: '30s geleden' },
                { ip: '10.0.0.5', type: 'POST', endpoint: '/api/auth/heartbeat', status: 200, time: '1m geleden' },
                { ip: '192.168.1.100', type: 'GET', endpoint: '/api', status: 200, time: '2m geleden' },
              ].map((row, idx) => (
                <tr key={idx} className="border-b border-slate-800">
                  <td className="py-3 text-slate-300">{row.ip}</td>
                  <td className="py-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      row.type === 'GET' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-amber-500/20 text-amber-400'
                    }`}>{row.type}</span>
                  </td>
                  <td className="py-3 text-slate-400 font-mono text-xs">{row.endpoint}</td>
                  <td className="py-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      row.status === 200 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>{row.status}</span>
                  </td>
                  <td className="py-3 text-slate-500">{row.time}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Layer Tab Content
function LayerTab() {
  const layers = [
    {
      name: 'Presentatie Laag',
      description: 'Frontend UI Components',
      tech: 'React 19, TailwindCSS',
      status: 'active',
      components: ['LoginForm', 'Dashboard', 'MainLayout', 'TraderPage', 'UsersAdminPage']
    },
    {
      name: 'API Laag',
      description: 'REST API Endpoints',
      tech: 'FastAPI',
      status: 'active',
      components: ['/api/auth/*', '/api/system/*', '/api (root)']
    },
    {
      name: 'Service Laag',
      description: 'Business Logic',
      tech: 'Python',
      status: 'active',
      components: ['AuthService', 'StorageService', 'SessionManager']
    },
    {
      name: 'Data Laag',
      description: 'Data Persistentie',
      tech: 'JSON Storage',
      status: 'active',
      components: ['users.json', 'gradaties.json', 'achievements.json']
    },
  ];

  const moduleArchitecture = [
    { name: 'Core', deps: 0, files: 4, status: 'stable' },
    { name: 'Auth', deps: 1, files: 4, status: 'stable' },
    { name: 'Knowledge', deps: 2, files: 0, status: 'planned' },
    { name: 'Chat', deps: 2, files: 0, status: 'planned' },
    { name: 'Trader', deps: 1, files: 1, status: 'active' },
  ];

  return (
    <div className="space-y-6">
      {/* Architecture Overview */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-6 flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          Architectuur Lagen
        </h3>
        
        <div className="relative">
          {/* Layer Stack Visualization */}
          <div className="space-y-4">
            {layers.map((layer, idx) => (
              <div 
                key={idx} 
                className={`p-4 rounded-xl border transition-all hover:scale-[1.02] cursor-pointer ${
                  idx === 0 ? 'bg-cyan-500/10 border-cyan-500/30' :
                  idx === 1 ? 'bg-blue-500/10 border-blue-500/30' :
                  idx === 2 ? 'bg-purple-500/10 border-purple-500/30' :
                  'bg-amber-500/10 border-amber-500/30'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                      idx === 0 ? 'bg-cyan-500 text-white' :
                      idx === 1 ? 'bg-blue-500 text-white' :
                      idx === 2 ? 'bg-purple-500 text-white' :
                      'bg-amber-500 text-white'
                    }`}>
                      {idx + 1}
                    </span>
                    <div>
                      <h4 className="text-white font-medium">{layer.name}</h4>
                      <p className="text-xs text-slate-400">{layer.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-500">{layer.tech}</span>
                    <div className="flex items-center gap-1 mt-1">
                      <span className="w-2 h-2 bg-green-500 rounded-full" />
                      <span className="text-xs text-green-400">{layer.status}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-wrap gap-2 mt-3">
                  {layer.components.map((comp, i) => (
                    <span key={i} className="px-2 py-1 bg-slate-800/50 rounded text-xs text-slate-300">
                      {comp}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Connection Lines */}
          <div className="absolute left-8 top-20 w-0.5 h-[calc(100%-80px)] bg-gradient-to-b from-cyan-500 via-purple-500 to-amber-500 opacity-30" />
        </div>
      </div>

      {/* Module Dependencies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Database className="w-4 h-4 text-cyan-400" />
            Module Overzicht
          </h3>
          <div className="space-y-3">
            {moduleArchitecture.map((mod, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                <div className="flex items-center gap-3">
                  <span className={`w-3 h-3 rounded-full ${
                    mod.status === 'stable' ? 'bg-green-500' :
                    mod.status === 'active' ? 'bg-cyan-500' :
                    'bg-slate-500'
                  }`} />
                  <span className="text-white font-medium">{mod.name}</span>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <span className="text-slate-400">{mod.deps} deps</span>
                  <span className="text-slate-400">{mod.files} files</span>
                  <span className={`px-2 py-0.5 rounded ${
                    mod.status === 'stable' ? 'bg-green-500/20 text-green-400' :
                    mod.status === 'active' ? 'bg-cyan-500/20 text-cyan-400' :
                    'bg-slate-700 text-slate-400'
                  }`}>{mod.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Data Flow */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            Data Flow
          </h3>
          <div className="space-y-4">
            <FlowItem 
              from="Frontend" 
              to="API Layer" 
              type="HTTP Request"
              color="cyan"
            />
            <FlowItem 
              from="API Layer" 
              to="Service Layer" 
              type="Function Call"
              color="blue"
            />
            <FlowItem 
              from="Service Layer" 
              to="Data Layer" 
              type="JSON I/O"
              color="purple"
            />
            <FlowItem 
              from="Data Layer" 
              to="Service Layer" 
              type="Data Return"
              color="amber"
              reverse
            />
          </div>
          
          <div className="mt-6 p-4 bg-slate-800/50 rounded-xl">
            <p className="text-xs text-slate-400 mb-2">Gemiddelde Response Time</p>
            <div className="flex items-center gap-4">
              <div className="text-2xl font-bold text-white">45ms</div>
              <div className="flex items-center gap-1 text-green-400 text-sm">
                <ArrowDown className="w-4 h-4" />
                12% sneller
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* File Structure */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <HardDrive className="w-4 h-4 text-cyan-400" />
          Project Structuur
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-sm">
          <div className="bg-slate-800/30 rounded-xl p-4">
            <p className="text-cyan-400 mb-2">/backend</p>
            <div className="pl-4 space-y-1 text-slate-400">
              <p>├── server.py</p>
              <p>├── config/</p>
              <p>│   └── settings.py</p>
              <p>├── modules/</p>
              <p>│   ├── core/storage.py</p>
              <p>│   └── auth/</p>
              <p>│       ├── routes.py</p>
              <p>│       ├── service.py</p>
              <p>│       └── models.py</p>
              <p>└── data/</p>
              <p>    └── system/*.json</p>
            </div>
          </div>
          <div className="bg-slate-800/30 rounded-xl p-4">
            <p className="text-purple-400 mb-2">/frontend/src</p>
            <div className="pl-4 space-y-1 text-slate-400">
              <p>├── App.js</p>
              <p>├── api/index.js</p>
              <p>├── context/AuthContext.js</p>
              <p>├── components/</p>
              <p>│   ├── layout/MainLayout.js</p>
              <p>│   ├── auth/LoginForm.js</p>
              <p>│   ├── dashboard/</p>
              <p>│   ├── modules/TraderPage.js</p>
              <p>│   ├── admin/UsersAdminPage.js</p>
              <p>│   └── profile/UserProfilePage.js</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper Components
function ResourceCard({ label, value, icon: Icon, color, unit }) {
  const colorClasses = {
    cyan: 'from-cyan-500 to-cyan-400',
    purple: 'from-purple-500 to-purple-400',
    amber: 'from-amber-500 to-amber-400',
    green: 'from-green-500 to-green-400',
  };

  const bgClasses = {
    cyan: 'bg-cyan-500/10 border-cyan-500/20',
    purple: 'bg-purple-500/10 border-purple-500/20',
    amber: 'bg-amber-500/10 border-amber-500/20',
    green: 'bg-green-500/10 border-green-500/20',
  };

  return (
    <div className={`${bgClasses[color]} border rounded-2xl p-5`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-slate-500 uppercase">{label}</span>
        <Icon className={`w-5 h-5 text-${color}-400`} />
      </div>
      <div className="text-3xl font-bold text-white mb-3">
        {Math.round(value)}<span className="text-lg text-slate-400">{unit}</span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div 
          className={`h-full bg-gradient-to-r ${colorClasses[color]} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
}

function InfoRow({ label, value, status }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
      <span className="text-sm text-slate-400">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm text-white">{value}</span>
        {status && (
          <span className={`w-2 h-2 rounded-full ${
            status === 'secure' || status === 'active' ? 'bg-green-500' : 'bg-slate-500'
          }`} />
        )}
      </div>
    </div>
  );
}

function FlowItem({ from, to, type, color, reverse }) {
  const colorClasses = {
    cyan: 'text-cyan-400 bg-cyan-500/20',
    blue: 'text-blue-400 bg-blue-500/20',
    purple: 'text-purple-400 bg-purple-500/20',
    amber: 'text-amber-400 bg-amber-500/20',
  };

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-slate-300 w-24">{from}</span>
      <div className="flex-1 flex items-center gap-2">
        <div className={`flex-1 h-0.5 ${reverse ? 'bg-gradient-to-l' : 'bg-gradient-to-r'} from-slate-700 to-slate-600`} />
        {reverse ? (
          <ArrowDown className={`w-4 h-4 ${colorClasses[color].split(' ')[0]} rotate-90`} />
        ) : (
          <ArrowUp className={`w-4 h-4 ${colorClasses[color].split(' ')[0]} rotate-90`} />
        )}
        <div className={`flex-1 h-0.5 ${reverse ? 'bg-gradient-to-r' : 'bg-gradient-to-l'} from-slate-700 to-slate-600`} />
      </div>
      <span className="text-sm text-slate-300 w-24 text-right">{to}</span>
    </div>
  );
}

export default AnalyticsPage;
