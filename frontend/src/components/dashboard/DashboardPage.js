import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { MainLayout } from '../layout/MainLayout';
import { AuthAPI } from '../../api';
import { 
  Users, User, Smartphone, Battery, Wifi, Lock, Unlock,
  Sun, Cloud, Thermometer, Bell, Music, Play, Pause,
  Home, Building, Globe, Settings, Eye, Volume2,
  Plus, Minus, Shield, Clock, MapPin, Activity
} from 'lucide-react';

export function DashboardPage({ activePage = 'dashboard', onNavigate }) {
  const { user } = useAuth();
  const [activeZone, setActiveZone] = useState('overzicht');
  const [users, setUsers] = useState([]);
  const [thermostat, setThermostat] = useState(21);

  // Load users
  useEffect(() => {
    AuthAPI.getUsers().then(res => {
      setUsers(res.users || []);
    }).catch(console.error);
  }, []);

  // If not dashboard, show placeholder
  if (activePage !== 'dashboard') {
    return (
      <MainLayout activePage={activePage} onNavigate={onNavigate}>
        <PlaceholderContent activePage={activePage} />
      </MainLayout>
    );
  }

  const zones = [
    { id: 'overzicht', label: 'OVERZICHT' },
    { id: 'workspace', label: 'WORKSPACE' },
    { id: 'spark-ai', label: 'SPARK AI' },
    { id: 'modules', label: 'MODULES' },
    { id: 'beheer', label: 'BEHEER' },
  ];

  // Get online users (last active within 30 mins)
  const onlineUsers = users.filter(u => {
    if (!u.last_active) return false;
    const lastActive = new Date(u.last_active);
    const thirtyMinsAgo = new Date(Date.now() - 30 * 60 * 1000);
    return lastActive > thirtyMinsAgo;
  });

  return (
    <MainLayout activePage="dashboard" onNavigate={onNavigate}>
      <div className="min-h-full bg-slate-950">
        {/* Zone Tabs */}
        <div className="bg-slate-900/50 border-b border-slate-800 px-6">
          <div className="flex items-center gap-1">
            {zones.map(zone => (
              <button
                key={zone.id}
                onClick={() => setActiveZone(zone.id)}
                className={`px-4 py-3 text-sm font-medium uppercase tracking-wider transition-all ${
                  activeZone === zone.id
                    ? 'text-white border-b-2 border-amber-500'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {zone.label}
              </button>
            ))}
          </div>
        </div>

        {/* Dashboard Content */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            
            {/* Column 1: People & Devices */}
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                People & Devices
              </h2>

              {/* Current User Card */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center">
                    <span className="text-lg font-bold text-white">{user?.naam?.charAt(0)}</span>
                  </div>
                  <div>
                    <p className="font-medium text-white">{user?.naam}</p>
                    <p className="text-xs text-green-400 flex items-center gap-1">
                      <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                      Online
                    </p>
                  </div>
                </div>

                {/* User Devices */}
                <div className="space-y-2">
                  <DeviceRow icon={Smartphone} name="Browser Session" status="active" />
                  <DeviceRow icon={Battery} name="Session Time" value="30 min" />
                  <DeviceRow icon={Shield} name="Gradatie" value={user?.gradatie} />
                </div>
              </div>

              {/* Other Online Users */}
              {onlineUsers.filter(u => u.id !== user?.id).slice(0, 2).map(u => (
                <div key={u.id} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-slate-700 rounded-xl flex items-center justify-center">
                      <span className="text-sm font-bold text-slate-300">{u.naam?.charAt(0)}</span>
                    </div>
                    <div>
                      <p className="font-medium text-white text-sm">{u.naam}</p>
                      <p className="text-xs text-slate-500">
                        {u.last_active ? 'Recent actief' : 'Offline'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}

              {/* Offline Users Count */}
              <div className="bg-slate-800/30 border border-slate-800 rounded-xl p-4">
                <p className="text-sm text-slate-400">
                  {users.length - onlineUsers.length} andere gebruikers offline
                </p>
              </div>
            </div>

            {/* Column 2: Access Control */}
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Access Control
              </h2>

              {/* Security Status */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
                <div className="aspect-video bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center relative">
                  <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAgTSAwIDIwIEwgNDAgMjAgTSAyMCAwIEwgMjAgNDAgTSAwIDMwIEwgNDAgMzAgTSAzMCAwIEwgMzAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzMzNCIgb3BhY2l0eT0iMC4yIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-50"></div>
                  <Shield className="w-16 h-16 text-green-500/50" />
                  <span className="absolute bottom-2 left-2 text-xs text-slate-400">System Secure</span>
                  <span className="absolute bottom-2 right-2 px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded">
                    Active
                  </span>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-center gap-4">
                  <button className="p-4 bg-slate-800 hover:bg-slate-700 rounded-xl transition-colors">
                    <Lock className="w-6 h-6 text-slate-400" />
                  </button>
                  <div className="text-center">
                    <p className="text-sm text-slate-400">Session Lock</p>
                  </div>
                </div>
              </div>

              {/* Auth Status */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
                <div className="aspect-video bg-gradient-to-br from-cyan-900/20 to-slate-900 flex items-center justify-center relative">
                  <Eye className="w-12 h-12 text-cyan-500/30" />
                  <span className="absolute bottom-2 left-2 text-xs text-slate-400">Auth Module</span>
                  <span className="absolute bottom-2 right-2 px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-xs rounded">
                    Running
                  </span>
                </div>
              </div>

              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-center gap-4">
                  <button className="p-4 bg-slate-800 hover:bg-slate-700 rounded-xl transition-colors">
                    <Unlock className="w-6 h-6 text-green-400" />
                  </button>
                  <div className="text-center">
                    <p className="text-sm text-slate-400">Session Active</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Column 3: General */}
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                General
              </h2>

              {/* System Status */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-4">
                  <Sun className="w-10 h-10 text-amber-400" />
                  <div>
                    <p className="text-2xl font-bold text-white">Online</p>
                    <p className="text-xs text-slate-400">Spark Core 2.0</p>
                  </div>
                  <div className="ml-auto text-right">
                    <p className="text-lg font-medium text-white">99.9%</p>
                    <p className="text-xs text-slate-500">Uptime</p>
                  </div>
                </div>

                {/* Week Activity */}
                <div className="flex justify-between">
                  {['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'].map((day, i) => (
                    <div key={day} className="text-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${
                        i < 5 ? 'bg-amber-500 text-white' : 'bg-slate-700 text-slate-400'
                      }`}>
                        <Activity className="w-4 h-4" />
                      </div>
                      <span className="text-xs text-slate-500">{day}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Thermostat Style - Module Status */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">Actieve Modules</span>
                  <Settings className="w-4 h-4 text-slate-500" />
                </div>
                
                <div className="relative flex items-center justify-center py-4">
                  {/* Circular Progress */}
                  <div className="relative w-32 h-32">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle
                        cx="64"
                        cy="64"
                        r="56"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        className="text-slate-800"
                      />
                      <circle
                        cx="64"
                        cy="64"
                        r="56"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        strokeDasharray="352"
                        strokeDashoffset="176"
                        className="text-cyan-500"
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-xs text-slate-500">Actief</span>
                      <span className="text-3xl font-bold text-white">4</span>
                      <span className="text-xs text-slate-500">/ 8</span>
                    </div>
                  </div>
                </div>

                {/* Module Controls */}
                <div className="flex items-center justify-center gap-4 mt-2">
                  <button className="w-10 h-10 bg-slate-800 rounded-full flex items-center justify-center hover:bg-slate-700 transition-colors">
                    <Minus className="w-4 h-4 text-slate-400" />
                  </button>
                  <button className="w-10 h-10 bg-slate-800 rounded-full flex items-center justify-center hover:bg-slate-700 transition-colors">
                    <Plus className="w-4 h-4 text-slate-400" />
                  </button>
                </div>
              </div>

              {/* Alarm / Notifications */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-white">Notificaties</span>
                  <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">
                    Enabled
                  </span>
                </div>
                <div className="flex gap-2">
                  <button className="flex-1 py-2 bg-amber-500/20 text-amber-400 rounded-lg text-sm hover:bg-amber-500/30 transition-colors">
                    ALERTS
                  </button>
                  <button className="flex-1 py-2 bg-slate-800 text-slate-400 rounded-lg text-sm hover:bg-slate-700 transition-colors">
                    QUIET
                  </button>
                </div>
              </div>
            </div>

            {/* Column 4: Media / Content */}
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Media
              </h2>

              {/* Media Player Style */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                <p className="text-sm text-slate-400 mb-2">Spark Brain</p>
                <p className="text-amber-400 text-sm mb-4">Ready for input</p>

                {/* Music Notes Animation */}
                <div className="aspect-square bg-slate-800/50 rounded-xl flex items-center justify-center mb-4">
                  <div className="flex items-end gap-2">
                    <div className="w-4 h-12 bg-gradient-to-t from-amber-500 to-amber-400 rounded animate-pulse" />
                    <div className="w-4 h-20 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded animate-pulse" style={{ animationDelay: '0.2s' }} />
                    <div className="w-4 h-16 bg-gradient-to-t from-amber-500 to-amber-400 rounded animate-pulse" style={{ animationDelay: '0.4s' }} />
                    <div className="w-4 h-24 bg-gradient-to-t from-cyan-500 to-cyan-400 rounded animate-pulse" style={{ animationDelay: '0.6s' }} />
                  </div>
                </div>

                {/* Controls */}
                <div className="flex justify-center gap-4">
                  <button className="p-2 text-slate-400 hover:text-white transition-colors">
                    <Home className="w-5 h-5" />
                  </button>
                  <button className="p-2 text-slate-400 hover:text-white transition-colors">
                    <Activity className="w-5 h-5" />
                  </button>
                  <button className="p-2 text-slate-400 hover:text-white transition-colors">
                    <Clock className="w-5 h-5" />
                  </button>
                  <button className="p-2 text-slate-400 hover:text-white transition-colors">
                    <Settings className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Video / Content */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                <p className="text-sm text-slate-400 mb-3">Video</p>
                
                <div className="bg-slate-800 rounded-xl p-4 flex items-center gap-3">
                  <div className="w-10 h-10 bg-slate-700 rounded-lg flex items-center justify-center">
                    <Volume2 className="w-5 h-5 text-slate-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-white">Knowledge Base</p>
                    <p className="text-xs text-slate-500">1,847 entries</p>
                  </div>
                  <button className="p-2 text-slate-400 hover:text-white transition-colors">
                    <Play className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-3 text-center">
                  <p className="text-2xl font-bold text-white">{users.length}</p>
                  <p className="text-xs text-slate-500">Users</p>
                </div>
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-3 text-center">
                  <p className="text-2xl font-bold text-white">4</p>
                  <p className="text-xs text-slate-500">Modules</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

// Device Row Component
function DeviceRow({ icon: Icon, name, status, value }) {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-slate-500" />
        <span className="text-sm text-slate-300">{name}</span>
      </div>
      {status && (
        <span className={`text-xs ${status === 'active' ? 'text-green-400' : 'text-slate-500'}`}>
          {status}
        </span>
      )}
      {value && (
        <span className="text-sm text-white">{value}</span>
      )}
    </div>
  );
}

// Placeholder for other pages
function PlaceholderContent({ activePage }) {
  return (
    <div className="flex-1 flex items-center justify-center min-h-[60vh]">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 bg-slate-800/50 border border-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Settings className="w-10 h-10 text-slate-500" />
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">{activePage}</h2>
        <p className="text-slate-400 mb-6">
          Deze module is klaar om ingericht te worden.
        </p>
      </div>
    </div>
  );
}

export default DashboardPage;
