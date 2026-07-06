import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { LogsBrowser } from './LogsBrowser';
import { 
  Activity, Cpu, HardDrive, MemoryStick, Wifi, Server,
  Database, Globe, Users, MessageSquare, Clock, TrendingUp,
  Layers, Network, Monitor, Zap, BarChart2, PieChart,
  ArrowUp, ArrowDown, CheckCircle, AlertCircle, RefreshCw,
  ChevronRight, FolderOpen, FileText
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function AnalyticsPage({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('systeem');
  const [systemInfo, setSystemInfo] = useState(null);

  // Live system info — refresh elke 5 sec wanneer SYSTEEM tab actief is
  useEffect(() => {
    if (activeTab !== 'systeem') return;
    const fetchInfo = () => fetch(`${API}/api/analytics/system-info`).then(r => r.json()).then(setSystemInfo).catch(() => {});
    fetchInfo();
    const interval = setInterval(fetchInfo, 5000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const tabs = [
    { id: 'systeem', label: 'SYSTEEM', icon: Monitor },
    { id: 'data', label: 'DATA', icon: PieChart },
    { id: 'network', label: 'NETWORK', icon: Network },
    { id: 'layer', label: 'LAYER', icon: Layers },
    { id: 'trade', label: 'TRADE', icon: TrendingUp },
    { id: 'logs', label: 'LOGS', icon: FileText },
    { id: 'capabilities', label: 'CAPABILITIES', icon: Zap },
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
        {activeTab === 'systeem' && <SystemTab info={systemInfo} />}
        {activeTab === 'data' && <DataTab />}
        {activeTab === 'network' && <NetworkTab />}
        {activeTab === 'layer' && <LayerTab />}
        {activeTab === 'trade' && <TradeAnalyticsTab />}
        {activeTab === 'logs' && (
          <div data-testid="analytics-logs-tab" className="space-y-4">
            <div className="text-xs text-slate-400 flex items-center gap-2">
              <FileText className="w-3 h-3" />
              <span>Spark Logger (v5_spark_logger_001) — pre / post / error / event records per module per dag.</span>
            </div>
            <LogsBrowser />
          </div>
        )}
        {activeTab === 'capabilities' && <CapabilitiesTab />}
      </div>
    </MainLayout>
  );
}

// System Tab Content — gebruikt echte runtime info via psutil
function SystemTab({ info }) {
  if (!info) {
    return <div className="text-center py-16 text-slate-500">Systeem info ophalen...</div>;
  }

  const cpu = info.cpu || { percent: 0, count_physical: '?', count_logical: '?' };
  const mem = info.memory || { percent: 0, used_human: '—', total_human: '—' };
  const disk = info.disk || { percent: 0, used_human: '—', total_human: '—', device: '?', fs_type: '?' };
  const net = info.network || { sent_human: '—', recv_human: '—' };
  const host = info.host || {};
  const proc = info.process;

  const systemInfoRows = [
    { label: 'Platform', value: 'Spark Core 2.0', icon: Zap },
    { label: 'Host OS', value: `${host.platform || '?'} ${host.platform_release || ''}`.trim(), icon: Server },
    { label: 'Architectuur', value: host.architecture || '?', icon: Cpu },
    { label: 'Hostname', value: host.hostname || '?', icon: Globe },
    { label: 'Python', value: `${host.python_implementation || ''} ${host.python_version || ''}`.trim(), icon: Database },
    { label: 'App-pad', value: info.app?.root || '?', icon: FolderOpen },
    { label: 'Uptime', value: info.app?.uptime_human || '?', icon: Clock },
  ];

  return (
    <div data-testid="analytics-systeem-tab" className="space-y-6">
      {/* Resource Monitors — ECHT (psutil) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ResourceCard
          label="CPU Gebruik"
          value={Math.round(cpu.percent)}
          icon={Cpu}
          color="cyan"
          unit="%"
          sub={`${cpu.count_physical} core${cpu.count_physical === 1 ? '' : 's'} · ${cpu.count_logical} threads`}
        />
        <ResourceCard
          label="Geheugen"
          value={Math.round(mem.percent)}
          icon={MemoryStick}
          color="purple"
          unit="%"
          sub={`${mem.used_human} / ${mem.total_human}`}
        />
        <ResourceCard
          label="Opslag (schijf)"
          value={Math.round(disk.percent)}
          icon={HardDrive}
          color="amber"
          unit="%"
          sub={`${disk.used_human} / ${disk.total_human}`}
        />
        <ResourceCard
          label="Netwerk"
          value={net.bytes_sent && net.bytes_recv ? Math.round(((net.bytes_sent + net.bytes_recv) / (1024 ** 3))) : 0}
          icon={Wifi}
          color="green"
          unit="GB"
          sub={`↑${net.sent_human} ↓${net.recv_human}`}
        />
      </div>

      {/* System Info & Disk detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Information */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Monitor className="w-4 h-4 text-cyan-400" />
            Systeem Informatie
          </h3>
          <div className="space-y-3">
            {systemInfoRows.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
                <div className="flex items-center gap-2 text-slate-400 flex-shrink-0">
                  <item.icon className="w-4 h-4" />
                  <span className="text-sm">{item.label}</span>
                </div>
                <span className="text-xs text-white font-medium font-mono truncate ml-2" title={item.value}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Disk detail */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-amber-400" />
            Schijf
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-slate-800">
              <span className="text-sm text-slate-400">Device</span>
              <span className="text-xs text-white font-mono">{disk.device}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-800">
              <span className="text-sm text-slate-400">Bestandssysteem</span>
              <span className="text-xs text-white font-mono">{disk.fs_type}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-800">
              <span className="text-sm text-slate-400">Totaal</span>
              <span className="text-xs text-white">{disk.total_human}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-slate-800">
              <span className="text-sm text-slate-400">Gebruikt</span>
              <span className="text-xs text-amber-400">{disk.used_human}</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-slate-400">Vrij</span>
              <span className="text-xs text-green-400">{disk.free_human}</span>
            </div>
            {/* Progress */}
            <div className="pt-2">
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-amber-500 rounded-full transition-all" style={{ width: `${disk.percent}%` }} />
              </div>
              <p className="text-[10px] text-slate-500 mt-1.5 text-right">{disk.percent}% gebruikt</p>
            </div>
          </div>
        </div>

        {/* Process info */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            Spark Process
          </h3>
          {proc ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-sm text-slate-400">PID</span>
                <span className="text-xs text-white font-mono">{proc.pid}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-sm text-slate-400">Naam</span>
                <span className="text-xs text-white">{proc.name}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-sm text-slate-400">Geheugen (RSS)</span>
                <span className="text-xs text-purple-400">{proc.memory_used_human}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-slate-800">
                <span className="text-sm text-slate-400">CPU</span>
                <span className="text-xs text-cyan-400">{Math.round(proc.cpu_percent)}%</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-sm text-slate-400">Threads</span>
                <span className="text-xs text-white">{proc.threads}</span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 text-center py-8">Process info niet beschikbaar</p>
          )}
        </div>
      </div>
    </div>
  );
}

// Network Tab Content — ECHT (psutil + request tracker middleware)
function NetworkTab() {
  const [info, setInfo] = React.useState(null);

  React.useEffect(() => {
    const fetchIt = () => fetch(`${API}/api/analytics/network-info`).then(r => r.json()).then(setInfo).catch(() => {});
    fetchIt();
    const t = setInterval(fetchIt, 3000);
    return () => clearInterval(t);
  }, []);

  if (!info) return <div className="text-center py-16 text-slate-500">Network info laden...</div>;
  if (info.error) return <div className="text-center py-16 text-red-400">{info.error}</div>;

  const { interfaces, total, throughput, per_interface, connections, recent_requests } = info;

  return (
    <div data-testid="analytics-network-tab" className="space-y-6">
      {/* Throughput + Total stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Inkomend (rate)" value={throughput.recv_human} icon={ArrowDown} color="cyan" />
        <StatCard label="Uitgaand (rate)" value={throughput.sent_human} icon={ArrowUp} color="purple" />
        <StatCard label="Totaal ontvangen" value={total.recv_human} icon={Database} color="green" sub={`${total.packets_recv.toLocaleString('nl-NL')} packets`} />
        <StatCard label="Totaal verzonden" value={total.sent_human} icon={Database} color="amber" sub={`${total.packets_sent.toLocaleString('nl-NL')} packets`} />
      </div>

      {/* Interfaces + Connections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Interfaces */}
        <div className="lg:col-span-2 bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Network className="w-4 h-4 text-cyan-400" />
            Netwerk Interfaces
          </h3>
          <div className="space-y-3">
            {interfaces.map(i => {
              const counter = per_interface.find(c => c.name === i.name);
              return (
                <div key={i.name} className="flex items-center gap-4 p-3 bg-slate-800/40 rounded-xl">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${i.is_up ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-sm font-mono text-white w-20">{i.name}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-300 font-mono truncate" title={i.ipv4 || ''}>
                      {i.ipv4 || '—'}
                    </p>
                    <p className="text-[10px] text-slate-500 font-mono truncate">
                      {i.mac || ''} {i.speed_mbps && ` · ${i.speed_mbps} Mbps`} {i.mtu && ` · MTU ${i.mtu}`}
                    </p>
                  </div>
                  {counter && (
                    <div className="text-right text-[11px] flex-shrink-0">
                      <p className="text-cyan-400">↓ {counter.recv_human}</p>
                      <p className="text-purple-400">↑ {counter.sent_human}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Connections */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Globe className="w-4 h-4 text-cyan-400" />
            Verbindingen
          </h3>
          {connections ? (
            <div className="space-y-2">
              <ConnRow label="Established" value={connections.ESTABLISHED} color="green" />
              <ConnRow label="Listen" value={connections.LISTEN} color="cyan" />
              <ConnRow label="Time-wait" value={connections.TIME_WAIT} color="amber" />
              <ConnRow label="Overig" value={connections.OTHER} color="slate" />
              {/* Errors */}
              <div className="pt-3 mt-3 border-t border-slate-800">
                <p className="text-[10px] text-slate-500 uppercase mb-2">Fouten</p>
                <ConnRow label="In" value={total.errin} color={total.errin > 0 ? 'red' : 'green'} />
                <ConnRow label="Out" value={total.errout} color={total.errout > 0 ? 'red' : 'green'} />
                <ConnRow label="Drop in" value={total.dropin} color={total.dropin > 0 ? 'red' : 'green'} />
                <ConnRow label="Drop out" value={total.dropout} color={total.dropout > 0 ? 'red' : 'green'} />
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 text-center py-6">
              Verbinding-info niet beschikbaar (geen rechten in container)
            </p>
          )}
        </div>
      </div>

      {/* Recente requests — ECHT via middleware */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          Recente API requests
          <span className="text-[10px] text-slate-500 ml-2">(laatste {recent_requests.length} van {info.recent_count})</span>
        </h3>
        {recent_requests.length === 0 ? (
          <p className="text-xs text-slate-500 text-center py-6">Nog geen requests sinds backend start</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500 border-b border-slate-700">
                  <th className="pb-2">Wanneer</th>
                  <th className="pb-2">Method</th>
                  <th className="pb-2">Path</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Tijd</th>
                  <th className="pb-2">IP</th>
                </tr>
              </thead>
              <tbody>
                {recent_requests.map((r, i) => (
                  <tr key={i} className="border-b border-slate-800/40 last:border-0">
                    <td className="py-2 text-slate-500 text-xs">{r.age_str}</td>
                    <td className="py-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        r.method === 'GET' ? 'bg-cyan-500/20 text-cyan-400' :
                        r.method === 'POST' ? 'bg-amber-500/20 text-amber-400' :
                        r.method === 'DELETE' ? 'bg-red-500/20 text-red-400' :
                        r.method === 'PUT' ? 'bg-amber-500/20 text-amber-400' :
                        'bg-slate-700 text-slate-400'
                      }`}>{r.method}</span>
                    </td>
                    <td className="py-2 text-slate-300 font-mono text-xs truncate max-w-[280px]" title={r.path}>{r.path}</td>
                    <td className="py-2">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        r.status < 300 ? 'bg-green-500/20 text-green-400' :
                        r.status < 400 ? 'bg-blue-500/20 text-blue-400' :
                        r.status < 500 ? 'bg-amber-500/20 text-amber-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>{r.status}</span>
                    </td>
                    <td className="py-2 text-slate-500 text-xs">{r.duration_ms}ms</td>
                    <td className="py-2 text-slate-500 font-mono text-xs">{r.ip}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color, sub }) {
  const bgs = {
    cyan: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400',
    purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
    green: 'bg-green-500/10 border-green-500/20 text-green-400',
    amber: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
  };
  return (
    <div className={`${bgs[color]} border rounded-2xl p-4`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</span>
        <Icon className="w-4 h-4" />
      </div>
      <p className="text-2xl font-bold text-white truncate">{value}</p>
      {sub && <p className="text-[10px] text-slate-500 mt-1 truncate">{sub}</p>}
    </div>
  );
}

function ConnRow({ label, value, color }) {
  const dotColors = {
    green: 'bg-green-500', cyan: 'bg-cyan-500', amber: 'bg-amber-500',
    red: 'bg-red-500', slate: 'bg-slate-500',
  };
  return (
    <div className="flex items-center justify-between py-1.5">
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${dotColors[color]}`} />
        <span className="text-xs text-slate-400">{label}</span>
      </div>
      <span className="text-sm text-white font-mono">{value}</span>
    </div>
  );
}

// === Old NetworkTab (replaced) ===
function _OldNetworkTab() {
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
                    className="flex-1 bg-gradient-to-t from-amber-500 to-amber-400 rounded-t"
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

// Layer Tab Content — LIVE DATA via /api/admin/architecture (v4_analytics_layer_001)
function LayerTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/admin/architecture`)
      .then(r => r.json())
      .then(d => setData(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-12 text-xs text-slate-500">Architectuur scannen...</div>;
  if (!data?.success) return <div className="text-center py-12 text-xs text-red-400">Kon architectuur niet ophalen.</div>;

  const layerColors = [
    { bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', badge: 'bg-cyan-500' },
    { bg: 'bg-blue-500/10', border: 'border-blue-500/30', badge: 'bg-blue-500' },
    { bg: 'bg-purple-500/10', border: 'border-purple-500/30', badge: 'bg-purple-500' },
    { bg: 'bg-amber-500/10', border: 'border-amber-500/30', badge: 'bg-amber-500' },
  ];

  const sortedModules = [...(data.modules || [])].sort((a, b) => b.routes - a.routes);
  const topModules = sortedModules.slice(0, 15);

  return (
    <div data-testid="analytics-layer-tab" className="space-y-6">
      {/* Architectuur Lagen */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-6 flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          Architectuur Lagen <span className="text-[10px] text-slate-500 font-normal">(live scan)</span>
        </h3>
        <div className="relative space-y-3">
          {data.layers.map((layer, idx) => {
            const c = layerColors[idx] || layerColors[3];
            return (
              <div key={idx} className={`p-4 rounded-xl border ${c.bg} ${c.border}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold text-white ${c.badge}`}>
                      {idx + 1}
                    </span>
                    <div>
                      <h4 className="text-white font-medium">{layer.name}</h4>
                      <p className="text-xs text-slate-400">{layer.description}</p>
                    </div>
                  </div>
                  <span className="text-xs text-slate-500">{layer.tech}</span>
                </div>
                <div className="flex flex-wrap gap-2 mt-2 ml-11">
                  {Object.entries(layer.metrics).map(([k, v]) => (
                    <span key={k} className="px-2.5 py-1 bg-slate-800/60 rounded text-xs text-slate-300">
                      <span className="text-slate-500">{k.replace(/_/g, ' ')}:</span>{' '}
                      <span className="text-white font-semibold">{typeof v === 'number' ? v.toLocaleString() : v}</span>
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
          <div className="absolute left-8 top-12 w-0.5 h-[calc(100%-60px)] bg-gradient-to-b from-cyan-500 via-purple-500 to-amber-500 opacity-30 pointer-events-none" />
        </div>
      </div>

      {/* Module Overzicht */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Database className="w-4 h-4 text-cyan-400" />
            Backend Modules <span className="text-[10px] text-slate-500 font-normal">({data.modules?.length} totaal — top 15)</span>
          </h3>
          <div className="space-y-1.5">
            {topModules.map(m => (
              <div key={m.name} className="flex items-center justify-between text-xs px-3 py-2 bg-slate-800/40 hover:bg-slate-800/70 rounded-lg">
                <span className="text-white font-medium">{m.name}</span>
                <div className="flex items-center gap-3 text-[11px]">
                  <span className="text-cyan-400">{m.routes} routes</span>
                  <span className="text-slate-500">{m.files} files</span>
                  <span className="text-slate-600">{m.size_kb}KB</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Layers className="w-4 h-4 text-purple-400" />
            Frontend Groups <span className="text-[10px] text-slate-500 font-normal">({data.frontend_groups?.length} groepen)</span>
          </h3>
          <div className="space-y-1.5">
            {data.frontend_groups?.map(g => (
              <div key={g.group} className="flex items-center justify-between text-xs px-3 py-2 bg-slate-800/40 hover:bg-slate-800/70 rounded-lg">
                <span className="text-white font-medium capitalize">{g.group}</span>
                <span className="text-purple-400 text-[11px]">{g.components} components</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <p className="text-[10px] text-slate-600 text-center italic">
        Live data via <code className="bg-slate-800 px-1.5 py-0.5 rounded">/api/admin/architecture</code> — scant <code className="bg-slate-800 px-1.5 py-0.5 rounded">/app/backend/modules</code> bij elke load.
      </p>
    </div>
  );
}

// (oude mock weggehaald)

function _OldLayerTab() {
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
function ResourceCard({ label, value, icon: Icon, color, unit, sub }) {
  const colorClasses = {
    cyan: 'from-cyan-500 to-cyan-400',
    purple: 'from-amber-500 to-amber-400',
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
      <div className="text-3xl font-bold text-white mb-1">
        {Math.round(value)}<span className="text-lg text-slate-400">{unit}</span>
      </div>
      {sub && <p className="text-[10px] text-slate-500 mb-2 truncate" title={sub}>{sub}</p>}
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

// ============================================================
// DATA TAB — Storage breakdown met donut chart
// ============================================================
function DataTab() {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [activeCategory, setActiveCategory] = React.useState(null); // 'system' | 'user' | 'ongemapt'

  React.useEffect(() => {
    fetch(`${API}/api/analytics/storage-breakdown`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-16 text-slate-500">Laden...</div>;
  if (!data) return <div className="text-center py-16 text-red-400">Geen data beschikbaar</div>;

  // Top-level segments voor outer ring
  const topSegments = data.categories.map(c => ({
    id: c.id,
    label: c.label,
    color: c.color,
    value: c.size_bytes,
    percent: c.percent_of_total,
  })).concat([{
    id: 'ongemapt',
    label: data.ongemapt.label,
    color: data.ongemapt.color,
    value: data.ongemapt.size_bytes,
    percent: data.ongemapt.percent_of_total,
  }]);

  // Inner ring: sub-segmenten van actieve categorie
  let innerSegments = [];
  let innerLabel = '';
  if (activeCategory === 'system' || activeCategory === 'user') {
    const cat = data.categories.find(c => c.id === activeCategory);
    if (cat) {
      innerSegments = cat.segments.filter(s => s.size_bytes > 0).map(s => ({
        id: s.id, label: s.label, color: s.color, value: s.size_bytes,
        percent: cat.size_bytes ? (s.size_bytes / cat.size_bytes * 100) : 0,
      }));
      innerLabel = cat.label;
    }
  } else if (activeCategory === 'ongemapt') {
    innerSegments = data.ongemapt.items.filter(i => i.size_bytes > 0).map(i => ({
      id: i.name, label: i.name, color: '#475569', value: i.size_bytes,
      percent: data.ongemapt.size_bytes ? (i.size_bytes / data.ongemapt.size_bytes * 100) : 0,
    }));
    innerLabel = data.ongemapt.label;
  }

  return (
    <div data-testid="analytics-data-tab" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">Data Opslag</h2>
          <p className="text-xs text-slate-400">Totaal {data.total_human} verdeeld over categorieën</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500 uppercase tracking-wider">Locatie</p>
          <p className="text-sm font-mono text-slate-300">/backend/data</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Donut chart */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 flex flex-col items-center">
          <DonutChart
            segments={topSegments}
            innerSegments={innerSegments}
            activeId={activeCategory}
            onSelect={setActiveCategory}
            centerLabel={data.total_human}
            centerSub="totaal"
            innerLabel={innerLabel}
          />
          {/* Legend top */}
          <div className="w-full mt-4 space-y-1.5">
            {topSegments.map(s => (
              <button key={s.id} data-testid={`storage-cat-${s.id}`}
                onClick={() => setActiveCategory(activeCategory === s.id ? null : s.id)}
                className={`w-full flex items-center gap-2 p-2 rounded-lg text-xs transition-all ${
                  activeCategory === s.id ? 'bg-slate-800 border border-slate-700' : 'hover:bg-slate-800/50'
                }`}>
                <span className="w-2.5 h-2.5 rounded-sm" style={{ background: s.color }} />
                <span className="text-slate-300 flex-1 text-left">{s.label}</span>
                <span className="text-slate-500">{formatBytes(s.value)}</span>
                <span className="text-slate-600 w-12 text-right">{s.percent}%</span>
                <ChevronRight className={`w-3 h-3 text-slate-500 transition-transform ${activeCategory === s.id ? 'rotate-90' : ''}`} />
              </button>
            ))}
          </div>
        </div>

        {/* Detail panel */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
          {activeCategory ? (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <FolderOpen className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white">{innerLabel}</h3>
                <span className="ml-auto text-[10px] text-slate-500">{innerSegments.length} onderdelen</span>
              </div>
              {innerSegments.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-8">Geen onderdelen met data</p>
              ) : (
                <div className="space-y-1.5">
                  {innerSegments.map(s => (
                    <div key={s.id} className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800/40">
                      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: s.color }} />
                      <span className="text-xs text-slate-300 flex-1 truncate">{s.label}</span>
                      <span className="text-[10px] text-slate-500 w-16 text-right">{formatBytes(s.value)}</span>
                      <span className="text-[10px] text-slate-600 w-12 text-right">{s.percent.toFixed(1)}%</span>
                    </div>
                  ))}
                  {/* Sub-progress bar */}
                  <div className="mt-3 h-2 bg-slate-800 rounded-full overflow-hidden flex">
                    {innerSegments.map(s => (
                      <div key={s.id} style={{ width: `${s.percent}%`, background: s.color }} title={`${s.label}: ${formatBytes(s.value)}`} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-16">
              <PieChart className="w-12 h-12 text-slate-700 mx-auto mb-2" />
              <p className="text-sm text-slate-400">Klik op een categorie</p>
              <p className="text-[10px] text-slate-600 mt-1">Om de detail-opsplitsing te zien</p>
            </div>
          )}
        </div>
      </div>

      {/* Insights row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <InsightCard icon={Database} color="cyan" label="Grootste post"
          value={topSegments[0]?.label || '—'}
          sub={`${formatBytes(topSegments[0]?.value || 0)} (${topSegments[0]?.percent}%)`} />
        <InsightCard icon={Users} color="amber" label="User data"
          value={formatBytes(data.categories.find(c => c.id === 'user')?.size_bytes || 0)}
          sub={`${data.categories.find(c => c.id === 'user')?.percent_of_total || 0}% van totaal`} />
        <InsightCard icon={AlertCircle} color="slate" label="Ongemapt"
          value={data.ongemapt.size_human}
          sub={data.ongemapt.items.length > 0 ? `${data.ongemapt.items.length} bestanden` : 'volledig gemapt'} />
      </div>
    </div>
  );
}

function DonutChart({ segments, innerSegments, activeId, onSelect, centerLabel, centerSub, innerLabel }) {
  const size = 260;
  const cx = size / 2;
  const cy = size / 2;
  const outerR = 110;
  const outerW = 28;
  const innerR = 70;
  const innerW = 22;

  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  const innerTotal = innerSegments.reduce((s, x) => s + x.value, 0) || 1;

  // Helper: arc path
  const arc = (cx, cy, r, w, startAngle, endAngle) => {
    const sa = (startAngle - 90) * Math.PI / 180;
    const ea = (endAngle - 90) * Math.PI / 180;
    const r2 = r - w;
    const x1 = cx + r * Math.cos(sa), y1 = cy + r * Math.sin(sa);
    const x2 = cx + r * Math.cos(ea), y2 = cy + r * Math.sin(ea);
    const x3 = cx + r2 * Math.cos(ea), y3 = cy + r2 * Math.sin(ea);
    const x4 = cx + r2 * Math.cos(sa), y4 = cy + r2 * Math.sin(sa);
    const large = endAngle - startAngle > 180 ? 1 : 0;
    return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} L ${x3} ${y3} A ${r2} ${r2} 0 ${large} 0 ${x4} ${y4} Z`;
  };

  // Render outer ring
  let outerAngle = 0;
  const outerPaths = segments.map(s => {
    const pct = s.value / total;
    const start = outerAngle;
    outerAngle += pct * 360;
    const end = outerAngle;
    if (pct === 0) return null;
    return (
      <path key={s.id}
        d={arc(cx, cy, outerR, outerW, start, end)}
        fill={s.color}
        opacity={activeId === null || activeId === s.id ? 1 : 0.3}
        style={{ cursor: 'pointer', transition: 'opacity 0.2s' }}
        onClick={() => onSelect(activeId === s.id ? null : s.id)}>
        <title>{s.label}: {formatBytes(s.value)} ({s.percent}%)</title>
      </path>
    );
  });

  // Render inner ring (only if a category is selected)
  let innerAngle = 0;
  const innerPaths = innerSegments.map(s => {
    const pct = s.value / innerTotal;
    const start = innerAngle;
    innerAngle += pct * 360;
    const end = innerAngle;
    if (pct === 0) return null;
    return (
      <path key={s.id}
        d={arc(cx, cy, innerR, innerW, start, end)}
        fill={s.color}>
        <title>{s.label}: {formatBytes(s.value)}</title>
      </path>
    );
  });

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {outerPaths}
        {innerSegments.length > 0 && innerPaths}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <p className="text-2xl font-bold text-white">{centerLabel}</p>
        <p className="text-[10px] text-slate-500 uppercase tracking-wider">{centerSub}</p>
        {innerLabel && <p className="text-[9px] text-cyan-400 mt-1">{innerLabel}</p>}
      </div>
    </div>
  );
}

function InsightCard({ icon: Icon, color, label, value, sub }) {
  const colors = {
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    slate: 'text-slate-400 bg-slate-500/10 border-slate-500/20',
  };
  return (
    <div className={`p-3 rounded-xl border ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-3.5 h-3.5" />
        <span className="text-[10px] uppercase tracking-wider opacity-80">{label}</span>
      </div>
      <p className="text-sm font-bold text-white truncate">{value}</p>
      <p className="text-[10px] text-slate-500 truncate">{sub}</p>
    </div>
  );
}

function formatBytes(n) {
  if (!n) return '0 B';
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / (1024 ** 2)).toFixed(1)} MB`;
  return `${(n / (1024 ** 3)).toFixed(2)} GB`;
}


// ============================================================
// v4_trade_analytics_001 — TRADE Tab: alle user-bots overzicht
// ============================================================
function TradeAnalyticsTab() {
  const API = process.env.REACT_APP_BACKEND_URL;
  const [bots, setBots] = React.useState([]);
  const [feed, setFeed] = React.useState([]);
  const [audit, setAudit] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [busyUser, setBusyUser] = React.useState(null);
  // v5_admin_bot_cards_001 — per-bot uitklap met potjes + history
  const [expanded, setExpanded] = React.useState(null);  // user_id of null
  const [botData, setBotData] = React.useState({});  // { user_id: { potjes, history } }
  const [forceSelling, setForceSelling] = React.useState(null);  // { user_id, pot_id }
  const [forceSellReason, setForceSellReason] = React.useState('');

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const [b, f, a] = await Promise.all([
        fetch(`${API}/api/trade/admin/bots`).then(r => r.json()),
        fetch(`${API}/api/trade/community/trade-feed?limit=20`).then(r => r.json()),
        fetch(`${API}/api/trade/admin/audit-log?limit=30`).then(r => r.json()),
      ]);
      setBots(b.bots || []);
      setFeed(f.messages || []);
      setAudit(a.entries || []);
    } catch (e) { /* silent */ }
    setLoading(false);
  }, [API]);

  React.useEffect(() => {
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, [load]);

  const loadBotDetails = React.useCallback(async (uid) => {
    try {
      const [p, h] = await Promise.all([
        fetch(`${API}/api/trade/potjes/${uid}`).then(r => r.json()).catch(() => ({})),
        fetch(`${API}/api/trade/history/${uid}?limit=8`).then(r => r.json()).catch(() => ({ trades: [] })),
      ]);
      setBotData(prev => ({ ...prev, [uid]: { potjes: p.potjes || [], summary: p.summary || {}, history: h.trades || [] } }));
    } catch {}
  }, [API]);

  const stopBot = async (uid) => {
    setBusyUser(uid);
    try { await fetch(`${API}/api/trade/bot/stop/${uid}`, { method: 'POST' }); }
    finally { setBusyUser(null); load(); }
  };

  // v5_admin_bot_controls_001 + v7_bot_defaults_align_001 — start met correcte defaults
  const startBot = async (uid, prevSettings = {}) => {
    setBusyUser(uid);
    try {
      const defaultMarkets = ['BCH-EUR', 'BTC-EUR', 'ETH-EUR', 'SOL-EUR', 'ADA-EUR', 'ATOM-EUR'];
      await fetch(`${API}/api/trade/bot/start/${uid}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          market: (prevSettings.markets && prevSettings.markets[0]) || prevSettings.market || 'BCH-EUR',
          markets: (prevSettings.markets && prevSettings.markets.length >= 3) ? prevSettings.markets : defaultMarkets,
          candle_interval: prevSettings.candle_interval && prevSettings.candle_interval !== '1h' ? prevSettings.candle_interval : '15m',
          interval: prevSettings.interval && prevSettings.interval >= 300 ? prevSettings.interval : 300,
          auto_trade: prevSettings.auto_trade !== undefined ? prevSettings.auto_trade : true,
          use_mock: prevSettings.use_mock !== undefined ? prevSettings.use_mock : false,
          use_potjes: prevSettings.use_potjes !== undefined ? prevSettings.use_potjes : true,
        }),
      });
    } finally { setBusyUser(null); load(); }
  };

  // v7_admin_start_all_bots_001 — admin bulk aan/uit
  const [bulkBusy, setBulkBusy] = React.useState(false);
  const startAllBots = async () => {
    if (bulkBusy) return;
    if (!window.confirm('Alle geregistreerde bots starten? (Willem, Spark, Geiser)')) return;
    setBulkBusy(true);
    try {
      const r = await fetch(`${API}/api/trade/admin/start-all-bots`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewer_id: 'user-001' }),
      }).then(x => x.json());
      if (r.success) {
        alert(`✅ ${r.started_count} bot(s) gestart (${r.total_bots} totaal)`);
      } else {
        alert('Start-all mislukt: ' + (r.error || 'onbekende fout'));
      }
    } catch (e) { alert('Fout: ' + e.message); }
    finally { setBulkBusy(false); load(); }
  };

  const stopAllBots = async () => {
    if (bulkBusy) return;
    if (!window.confirm('Alle draaiende bots stoppen?')) return;
    setBulkBusy(true);
    try {
      const r = await fetch(`${API}/api/trade/admin/stop-all-bots`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewer_id: 'user-001' }),
      }).then(x => x.json());
      if (r.success) {
        alert(`⏹ ${r.stopped_count} bot(s) gestopt`);
      }
    } catch (e) { alert('Fout: ' + e.message); }
    finally { setBulkBusy(false); load(); }
  };

  const pauseBot = async (uid) => {
    setBusyUser(uid);
    try { await fetch(`${API}/api/trade/bot/pause/${uid}`, { method: 'POST' }); }
    finally { setBusyUser(null); load(); }
  };

  const toggleExpand = (uid) => {
    if (expanded === uid) {
      setExpanded(null);
    } else {
      setExpanded(uid);
      if (!botData[uid]) loadBotDetails(uid);
    }
  };

  const confirmForceSell = async () => {
    if (!forceSelling) return;
    const { user_id, pot_id } = forceSelling;
    try {
      const r = await fetch(`${API}/api/trade/potjes/${user_id}/${pot_id}/force-sell`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewer_id: 'user-001', reason: forceSellReason || 'Admin handmatige force-sell' }),
      }).then(x => x.json());
      if (r.success) {
        loadBotDetails(user_id);
      } else {
        alert('Force-sell mislukt: ' + (r.error || 'onbekende fout'));
      }
    } catch (e) {
      alert('Force-sell error: ' + e.message);
    } finally {
      setForceSelling(null);
      setForceSellReason('');
    }
  };

  // v7_pot_revalue_001 — Handmatige herwaardeer-knop per pot
  const revaluePot = async (user_id, pot_id) => {
    try {
      const r = await fetch(`${API}/api/trade/potjes/${user_id}/${pot_id}/revalue`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewer_id: 'user-001' }),
      }).then(x => x.json());
      if (r.success) {
        loadBotDetails(user_id);
      } else {
        alert('Herwaardeer mislukt: ' + (r.error || 'onbekende fout'));
      }
    } catch (e) {
      alert('Herwaardeer error: ' + e.message);
    }
  };

  // v7_pot_revalue_001 — Globaal alle vrije pots van een user herwaarderen
  const revalueAllPots = async (user_id) => {
    if (!window.confirm(`Alle vrije pots van ${user_id} herwaarderen naar huidige token-prijs?`)) return;
    try {
      const r = await fetch(`${API}/api/trade/potjes/${user_id}/revalue-all`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewer_id: 'user-001' }),
      }).then(x => x.json());
      if (r.success) {
        alert(`✅ ${r.revalued_count} pot(s) herwaardeerd naar €${(r.token_price_used || 0).toFixed(4)}`);
        loadBotDetails(user_id);
      } else {
        alert('Herwaardeer mislukt: ' + (r.error || 'onbekende fout'));
      }
    } catch (e) {
      alert('Herwaardeer error: ' + e.message);
    }
  };

  // v7_dead_code_001 — Event overlay demo is verwijderd uit trade-analytics tab.
  // De trigger-functionaliteit blijft beschikbaar via /api/events/trigger endpoint
  // voor toekomstig hergebruik (bv. in een eigen KB-devtools tab).

  return (
    <div data-testid="analytics-trade-tab" className="space-y-6">
      {/* v7_restwaarde_portfolio_001 — Live Bitvavo restwaarde-portfolio.
          Toont per coin de resterende hoeveelheid × huidige prijs. Vervangt
          de Event Overlay test die hier per abuis stond. */}
      <RestwaardePortfolio />

      {/* v7_admin_trader_stats_001 — Trader stats verplaatst uit user-facing module */}
      <SparkTraderStatsPanel />

      {/* v5_admin_bot_cards_001 — Bot kaarten (uitklap → potjes + history per wallet) */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            🤖 Trade-bots <span className="text-[11px] font-normal text-slate-500">({bots.filter(b => b.running).length} actief / {bots.length} zichtbaar)</span>
          </h3>
          <div className="flex items-center gap-2">
            <button onClick={startAllBots} disabled={bulkBusy}
              data-testid="start-all-bots"
              title="Start alle geregistreerde bots (Willem, Spark, Geiser)"
              className="px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 disabled:opacity-40 text-emerald-300 rounded text-[11px] font-medium flex items-center gap-1">
              {bulkBusy ? '⏳' : '▶'} Start alle bots
            </button>
            <button onClick={stopAllBots} disabled={bulkBusy}
              data-testid="stop-all-bots"
              className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 disabled:opacity-40 text-red-400 rounded text-[11px] font-medium">
              ⏹ Stop alle
            </button>
            <button onClick={load} disabled={loading} data-testid="refresh-bots"
              className="text-xs text-slate-400 hover:text-white ml-2">
              {loading ? '...' : 'Vernieuwen'}
            </button>
          </div>
        </div>

        {/* v6_reconcile_001 — Reconciliatie-panel: Spark potjes vs echte Bitvavo balance */}
        <ReconcileSparkPanel />
        {bots.length === 0 ? (
          <p className="text-sm text-slate-500 italic">Geen bots gestart.</p>
        ) : (
          <div className="space-y-2" data-testid="bot-cards-list">
            {bots.map(b => {
              const isOpen = expanded === b.user_id;
              const details = botData[b.user_id];
              return (
                <div key={b.user_id} className="bg-slate-800/40 rounded-xl border border-slate-700/40 overflow-hidden">
                  {/* Header rij — klik om uit te klappen */}
                  <button onClick={() => toggleExpand(b.user_id)}
                    data-testid={`bot-card-toggle-${b.user_id}`}
                    className="w-full p-3 flex flex-wrap items-center gap-3 text-xs hover:bg-slate-800/60 transition-colors text-left">
                    <span className={`w-2.5 h-2.5 rounded-full ${b.running ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`}></span>
                    <span className="font-medium text-white min-w-[140px]">{b.user_naam || b.user_id}</span>
                    <span className="font-mono text-[10px] text-slate-500 min-w-[110px]">{b.user_id}</span>
                    <span className="text-slate-400">
                      {Array.isArray(b.markets) ? b.markets.join('·') : b.market}
                    </span>
                    <span className="text-slate-500">{b.candle_interval}</span>
                    <span className="text-amber-400">cycle #{b.cycles}</span>
                    {b.use_potjes && <span className="text-cyan-400">{details?.potjes?.length ?? b.pot_count ?? '?'}-potjes</span>}
                    {b.auto_trade && <span className="text-emerald-400">auto</span>}
                    {b.use_mock && <span className="text-pink-400">MOCK</span>}
                    {!b.running && <span className="text-slate-500 italic">{b.lazy_slot ? 'slot leeg (niet gestart)' : 'slot-aanwezig (uit)'}</span>}
                    <span className="text-slate-500 ml-auto">{Math.round((b.uptime_seconds || 0) / 60)}m up</span>
                    <span className="text-slate-500">{isOpen ? '▾' : '▸'}</span>
                  </button>

                  {isOpen && (
                    <div className="border-t border-slate-700/40 bg-slate-900/40 p-4 space-y-4">
                      {/* v5_admin_bot_controls_001 — Start/Pause/Stop knoppen per bot */}
                      <div className="flex items-center gap-2 flex-wrap">
                        {!b.running && (
                          <button onClick={() => startBot(b.user_id, b)} disabled={busyUser === b.user_id}
                            data-testid={`bot-start-${b.user_id}`}
                            className="px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded text-[11px] font-medium disabled:opacity-40">
                            ▶ Start bot
                          </button>
                        )}
                        {b.running && (
                          <button onClick={() => pauseBot(b.user_id)} disabled={busyUser === b.user_id}
                            data-testid={`bot-pause-${b.user_id}`}
                            className={`px-3 py-1.5 rounded text-[11px] font-medium disabled:opacity-40 ${b.paused ? 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-400' : 'bg-blue-500/20 hover:bg-blue-500/30 text-blue-400'}`}>
                            {b.paused ? '▶ Hervat' : '⏸ Pauzeer'}
                          </button>
                        )}
                        {b.running && (
                          <button onClick={() => stopBot(b.user_id)} disabled={busyUser === b.user_id}
                            data-testid={`bot-stop-${b.user_id}`}
                            className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded text-[11px] font-medium disabled:opacity-40">
                            ⏹ Stop bot
                          </button>
                        )}
                        <button onClick={() => revalueAllPots(b.user_id)}
                          data-testid={`revalue-all-${b.user_id}`}
                          title="Herwaardeer alle vrije pots naar huidige dynamische token-prijs"
                          className="px-3 py-1.5 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 rounded text-[11px] font-medium ml-auto">
                          ↻ Herwaardeer vrije pots
                        </button>
                      </div>

                      {/* Potjes-tabel */}
                      <div>
                        <p className="text-[11px] text-slate-400 font-semibold mb-2">Potjes ({details?.potjes?.length || 0})</p>
                        {!details ? (
                          <p className="text-[11px] text-slate-500 italic">Laden...</p>
                        ) : details.potjes.length === 0 ? (
                          <p className="text-[11px] text-slate-500 italic">Geen potjes geconfigureerd.</p>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="w-full text-[11px]">
                              <thead className="text-slate-500 border-b border-slate-800">
                                <tr>
                                  <th className="text-left py-1.5 pr-2">#</th>
                                  <th className="text-left py-1.5 pr-2">Status</th>
                                  <th className="text-left py-1.5 pr-2">Market</th>
                                  <th className="text-right py-1.5 pr-2">Capital</th>
                                  <th className="text-right py-1.5 pr-2">Live</th>
                                  <th className="text-right py-1.5 pr-2">Entry</th>
                                  <th className="text-right py-1.5 pr-2">Trades</th>
                                  <th className="text-right py-1.5 pr-2">P&L</th>
                                  <th className="text-right py-1.5">Actie</th>
                                </tr>
                              </thead>
                              <tbody>
                                {details.potjes.map(p => {
                                  const isOpenPos = p?.position?.is_open;
                                  const pnl = p?.stats?.total_pnl || 0;
                                  return (
                                    <tr key={p.id} className="border-b border-slate-800/40">
                                      <td className="py-1.5 pr-2 font-mono text-slate-400">{p.nummer || p.index || '?'}</td>
                                      <td className="py-1.5 pr-2">
                                        {isOpenPos ? <span className="text-green-400">● gekocht</span> : <span className="text-blue-400">○ vrij</span>}
                                      </td>
                                      <td className="py-1.5 pr-2 text-slate-300">{p.market || '—'}</td>
                                      <td className="py-1.5 pr-2 text-right text-slate-300">€{(p.capital ?? 0).toFixed(2)}</td>
                                      <td className="py-1.5 pr-2 text-right text-cyan-400">€{(p.live_value ?? p.capital ?? 0).toFixed(2)}</td>
                                      <td className="py-1.5 pr-2 text-right text-slate-400">{isOpenPos && p.position?.entry_price ? `€${p.position.entry_price.toFixed(2)}` : '—'}</td>
                                      <td className="py-1.5 pr-2 text-right text-slate-400">{p.stats?.trades || 0}</td>
                                      <td className={`py-1.5 pr-2 text-right ${pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>€{pnl.toFixed(2)}</td>
                                      <td className="py-1.5 text-right">
                                        <div className="flex items-center gap-1 justify-end">
                                          {!isOpenPos && (
                                            <button onClick={() => revaluePot(b.user_id, p.id)}
                                              data-testid={`revalue-${b.user_id}-${p.id}`}
                                              title="Herwaardeer capital op huidige token-prijs (dynamisch)"
                                              className="px-1.5 py-0.5 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 rounded text-[10px] font-medium">
                                              ↻ Herw.
                                            </button>
                                          )}
                                          {isOpenPos && (
                                            <button onClick={() => setForceSelling({ user_id: b.user_id, pot_id: p.id, market: p.market, entry: p.position?.entry_price })}
                                              data-testid={`force-sell-${b.user_id}-${p.id}`}
                                              title="Force-sell dit potje (kan verlies geven)"
                                              className="px-1.5 py-0.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded text-[10px] font-medium">
                                              🛑 Force-sell
                                            </button>
                                          )}
                                        </div>
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>

                      {/* Laatste trades */}
                      <div>
                        <p className="text-[11px] text-slate-400 font-semibold mb-2">Laatste trades (8)</p>
                        {!details ? null : details.history.length === 0 ? (
                          <p className="text-[11px] text-slate-500 italic">Nog geen trades.</p>
                        ) : (
                          <div className="space-y-1">
                            {details.history.map((t, i) => (
                              <div key={t.trade_id || t.order_id || i} className="flex items-center gap-2 text-[10px] font-mono bg-slate-800/30 rounded px-2 py-1">
                                <span className="text-slate-500">{t.timestamp ? new Date(t.timestamp).toLocaleString('nl-NL', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}</span>
                                <span className={`min-w-[40px] ${t.action === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>{t.action}</span>
                                <span className="text-slate-300 min-w-[80px]">{t.market}</span>
                                <span className="text-amber-400">€{(t.amount || 0).toFixed(2)}</span>
                                <span className="text-slate-500">@€{(t.price || 0).toFixed(2)}</span>
                                {t.fee != null && <span className="text-pink-400">fee €{Number(t.fee).toFixed(3)}</span>}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Force-sell confirm modal */}
      {forceSelling && (
        <div className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-red-500/40 rounded-2xl shadow-2xl max-w-md w-full overflow-hidden" data-testid="force-sell-modal">
            <div className="px-5 py-4 border-b border-red-500/30 bg-red-500/10">
              <h3 className="text-base font-bold text-red-200">🛑 Force-sell bevestigen</h3>
            </div>
            <div className="px-5 py-4 space-y-3 text-sm text-slate-300">
              <p>Je staat op het punt om potje <span className="font-mono text-amber-300">{forceSelling.pot_id}</span> van user <span className="font-mono text-amber-300">{forceSelling.user_id}</span> te forceren naar verkoop op de huidige marktprijs ({forceSelling.market || 'onbekende markt'}).</p>
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-[12px] text-red-200">
                ⚠️ <strong>Let op:</strong> dit kan verlies geven. Bij verlies daalt het bot-vermogen en kunnen ROAR-tokens in waarde minderen voor iedereen. Gebruik alleen als laatste redmiddel.
              </div>
              <label className="block text-[11px] text-slate-400">Reden (audit-trail)</label>
              <input type="text" value={forceSellReason} onChange={e => setForceSellReason(e.target.value)}
                data-testid="force-sell-reason"
                placeholder="Bv. coin instort, hard stop loss..."
                className="w-full px-3 py-2 bg-slate-800/60 border border-slate-700 rounded text-sm text-white placeholder-slate-500 focus:outline-none focus:border-red-500/50" />
            </div>
            <div className="px-5 py-3 bg-slate-950/50 border-t border-slate-800 flex justify-end gap-2">
              <button onClick={() => { setForceSelling(null); setForceSellReason(''); }}
                data-testid="force-sell-cancel"
                className="px-4 py-1.5 rounded-lg text-sm text-slate-300 bg-slate-800 hover:bg-slate-700">
                Annuleer
              </button>
              <button onClick={confirmForceSell}
                data-testid="force-sell-confirm"
                className="px-4 py-1.5 rounded-lg text-sm font-medium text-white bg-red-500 hover:bg-red-600">
                Force-sell nu
              </button>
            </div>
          </div>
        </div>
      )}

      {/* v7_boekhouder_moved_to_logs_001 — Community feed hoort niet in trade-tab.
          Verhuist later naar Analytics → Logs (roadmap P1). */}

      {/* Audit log */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <h3 className="text-base font-semibold text-white mb-4">📋 Audit-trail (geld/token-bewegingen)</h3>
        {audit.length === 0 ? (
          <p className="text-sm text-slate-500 italic">Geen audit-entries.</p>
        ) : (
          <div className="space-y-1 max-h-80 overflow-y-auto">
            {audit.map(e => (
              <div key={e.id} className="bg-slate-800/30 rounded p-2 text-[11px] font-mono flex flex-wrap gap-2">
                <span className="text-slate-500">{new Date(e.ts).toLocaleTimeString('nl-NL')}</span>
                <span className="text-amber-400 min-w-[90px]">{e.type}</span>
                {e.user_id && <span className="text-white">{e.user_id}</span>}
                {e.pot_id && <span className="text-cyan-400">{e.pot_id}</span>}
                {(e.amount_eur != null) && <span className="text-emerald-400">€{Number(e.amount_eur).toFixed(4)}</span>}
                {(e.netto != null) && <span className={e.netto >= 0 ? 'text-emerald-400' : 'text-red-400'}>netto €{Number(e.netto).toFixed(4)}</span>}
                {(e.spark_fee_eur != null && e.spark_fee_eur > 0) && <span className="text-pink-400">fee €{Number(e.spark_fee_eur).toFixed(4)}</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


// v6_capabilities_admin_001 — Capabilities Test Page (Spark's handen overzicht)
function CapabilitiesTab() {
  const [data, setData] = React.useState(null);
  const [testText, setTestText] = React.useState('');
  const [testResult, setTestResult] = React.useState(null);
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/admin/capabilities`).then(x => x.json());
      setData(r);
    } catch {}
  }, []);

  React.useEffect(() => { load(); }, [load]);

  const runTest = async (text) => {
    setBusy(true);
    setTestResult(null);
    try {
      const r = await fetch(`${API}/api/admin/capabilities/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, user_id: 'user-001' }),
      }).then(x => x.json());
      setTestResult(r);
    } catch (e) {
      setTestResult({ error: String(e) });
    }
    setBusy(false);
  };

  if (!data) return <div className="text-slate-400 text-sm">Capabilities laden…</div>;

  const STATUS_STYLES = {
    executable:  { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-300', label: 'EXECUTABLE' },
    live:        { bg: 'bg-amber-500/10',   border: 'border-amber-500/30',   text: 'text-amber-300',   label: 'LIVE (geen handler)' },
    placeholder: { bg: 'bg-blue-500/10',    border: 'border-blue-500/30',    text: 'text-blue-300',    label: 'PLACEHOLDER' },
    idea:        { bg: 'bg-slate-700/30',   border: 'border-slate-600/40',   text: 'text-slate-400',   label: 'IDEA' },
  };

  return (
    <div data-testid="analytics-capabilities-tab" className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatPill label="Totaal" value={data.total} color="white" />
        <StatPill label="Executable" value={data.executable} color="emerald" />
        <StatPill label="Live (geen handler)" value={data.live_no_handler} color="amber" />
        <StatPill label="Placeholder" value={data.placeholder} color="blue" />
        <StatPill label="Idea" value={data.idea} color="slate" />
      </div>

      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 space-y-3">
        <div className="flex items-center gap-2 text-sm text-slate-300">
          <Zap className="w-4 h-4 text-amber-400" /> Test een capability
        </div>
        <div className="flex gap-2">
          <input
            data-testid="cap-test-input"
            type="text"
            value={testText}
            onChange={e => setTestText(e.target.value)}
            placeholder="Typ een zin (bv. 'hoeveel gebruikers' of 'wat is spark saldo')"
            className="flex-1 bg-slate-800 text-white text-sm px-3 py-2 rounded-lg border border-slate-700 focus:border-amber-500 outline-none"
            onKeyDown={e => e.key === 'Enter' && testText && runTest(testText)}
          />
          <button
            data-testid="cap-test-btn"
            onClick={() => testText && runTest(testText)}
            disabled={!testText || busy}
            className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium rounded-lg disabled:opacity-60"
          >
            {busy ? 'Bezig…' : 'Test'}
          </button>
        </div>
        {testResult && (
          <div className={`text-xs p-3 rounded-lg border ${testResult.matched ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-slate-800/40 border-slate-700'}`}>
            {testResult.matched ? (
              <>
                <div className="text-emerald-300 mb-1">
                  ✓ Match: <span className="font-mono">{testResult.match.capability_id}</span> (confidence {testResult.match.confidence})
                </div>
                <div className="text-slate-300 whitespace-pre-line">{testResult.execution?.message || '(geen execution-response)'}</div>
              </>
            ) : (
              <div className="text-slate-400">{testResult.message || 'Geen match'}</div>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data.capabilities.map(c => {
          const st = STATUS_STYLES[c.effective_status] || STATUS_STYLES.idea;
          const sample = (c.triggers && c.triggers[0]) ? c.triggers[0].replace(/[\\()?\[\]*^$|]/g, '').replace(/\s+/g, ' ').trim() : '';
          return (
            <div key={c.id} data-testid={`cap-card-${c.id}`}
                 className={`${st.bg} border ${st.border} rounded-xl p-3 space-y-2`}>
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">{c.naam || c.id}</div>
                  <div className="text-[10px] text-slate-500 font-mono truncate">{c.id} · {c.categorie}</div>
                </div>
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase ${st.text}`}>
                  {st.label}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 leading-relaxed">{c.beschrijving}</div>
              {sample && (
                <button
                  onClick={() => { setTestText(sample.slice(0, 60)); }}
                  className="text-[10px] text-amber-400 hover:text-amber-300 text-left">
                  ↻ Vul test-veld met "{sample.slice(0, 40)}…"
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatPill({ label, value, color }) {
  const colors = {
    white: 'text-white',
    emerald: 'text-emerald-300',
    amber: 'text-amber-300',
    blue: 'text-blue-300',
    slate: 'text-slate-400',
  };
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-3">
      <div className={`text-2xl font-bold ${colors[color] || colors.white}`}>{value}</div>
      <div className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</div>
    </div>
  );
}


// v6_reconcile_001 — Toont per coin: potje vs echte Bitvavo, met diff + sync-knop
// v7_restwaarde_portfolio_001 — Toon per coin de EUR-restwaarde op Bitvavo.
// Dit is admin-info die bij het trader-kader hoort (niet in aparte tab).
// v7_admin_trader_stats_001 — Trader stats-blok (was in user-facing TraderPage, nu admin-only hier)
function SparkTraderStatsPanel() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [selected, setSelected] = useState('user-000');
  const [baselineEditing, setBaselineEditing] = useState(false);
  const [baselineInput, setBaselineInput] = useState('');
  const API = process.env.REACT_APP_BACKEND_URL;

  const load = React.useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/trade/stats/${selected}`).then(x => x.json());
      setStats(r);
    } catch { setStats(null); }
  }, [API, selected]);

  useEffect(() => {
    fetch(`${API}/api/trade/admin/bots`).then(r => r.json()).then(d => {
      const list = (d.bots || []).map(b => ({ id: b.user_id, name: b.user_naam || b.user_id }));
      setUsers(list);
    }).catch(() => {});
  }, [API]);

  useEffect(() => { load(); }, [load]);

  const setBaseline = async () => {
    const v = parseFloat(baselineInput);
    if (isNaN(v) || v < 0) { alert('Ongeldig bedrag'); return; }
    try {
      const r = await fetch(`${API}/api/trade/baseline/${selected}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ baseline_eur: v, note: 'Manual reset via analytics' }),
      }).then(x => x.json());
      if (r.success) {
        setBaselineEditing(false);
        setBaselineInput('');
        load();
      } else {
        alert('Baseline zetten mislukt: ' + (r.error || 'onbekend'));
      }
    } catch (e) { alert('Fout: ' + e.message); }
  };

  const setBaselineToNow = async () => {
    if (!window.confirm(`Baseline resetten naar huidige Bitvavo balance voor ${selected}? P&L begint dan opnieuw vanaf 0.`)) return;
    try {
      const bv = await fetch(`${API}/api/trade/bitvavo/balance/${selected}`).then(x => x.json());
      if (!bv.success) { alert('Bitvavo balance ophalen mislukt'); return; }
      const total = bv.total_eur;
      const r = await fetch(`${API}/api/trade/baseline/${selected}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ baseline_eur: total, note: 'Reset to current Bitvavo balance' }),
      }).then(x => x.json());
      if (r.success) { load(); alert(`Baseline gezet op €${total.toFixed(2)}`); }
    } catch (e) { alert('Fout: ' + e.message); }
  };

  const s = stats || {};
  const pnl = s.netto_pnl ?? 0;
  const livePnl = s.live_pnl;

  return (
    <div data-testid="admin-trader-stats" className="bg-slate-900/50 border border-amber-500/30 rounded-2xl p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">📊 Trader stats (admin)</h3>
        <div className="flex items-center gap-2">
          <select value={selected} onChange={e => setSelected(e.target.value)}
            data-testid="admin-stats-user-select"
            className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200">
            {users.map(u => <option key={u.id} value={u.id}>{u.name} ({u.id})</option>)}
          </select>
          <button onClick={load} className="text-[11px] text-slate-400 hover:text-white">↻</button>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-xs">
        <StatMini label="Trades" value={s.total_trades || 0} color="text-cyan-400" />
        <StatMini label="Gekocht" value={`€${(s.total_buy_eur || 0).toFixed(2)}`} sub={`${s.buys || 0} buys`} color="text-emerald-400" />
        <StatMini label="Verkocht" value={`€${(s.total_sell_eur || 0).toFixed(2)}`} sub={`${s.sells || 0} sells`} color="text-red-400" />
        <StatMini label="Fees" value={`€${(s.total_fees_eur || 0).toFixed(2)}`} sub="0.25%" color="text-amber-400" />
        <StatMini label="Netto P&L" value={`€${pnl.toFixed(2)}`} sub={`Bruto €${(s.bruto_pnl || 0).toFixed(2)}`} color={pnl >= 0 ? 'text-emerald-400' : 'text-red-400'} />
        <StatMini
          label="Live P&L vs start"
          value={livePnl != null ? `€${livePnl.toFixed(2)}` : '—'}
          sub={s.baseline_eur ? `Baseline €${s.baseline_eur.toFixed(2)}` : 'Geen baseline'}
          color={livePnl != null ? (livePnl >= 0 ? 'text-emerald-400' : 'text-red-400') : 'text-slate-500'}
        />
      </div>
      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-800">
        {!baselineEditing ? (
          <>
            <button onClick={() => setBaselineEditing(true)}
              data-testid="baseline-set-manual"
              className="text-[10px] px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">
              Baseline zetten (handmatig)
            </button>
            <button onClick={setBaselineToNow}
              data-testid="baseline-reset-now"
              className="text-[10px] px-2 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded">
              🔁 Reset baseline naar nu (Bitvavo balance)
            </button>
            {s.baseline_set_at && <span className="text-[10px] text-slate-500 ml-auto">Set: {String(s.baseline_set_at).slice(0, 19)}</span>}
          </>
        ) : (
          <>
            <input type="number" step="0.01" value={baselineInput} onChange={e => setBaselineInput(e.target.value)}
              placeholder="Baseline in €" className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs w-32 text-slate-200" />
            <button onClick={setBaseline} className="text-[10px] px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded">Zetten</button>
            <button onClick={() => { setBaselineEditing(false); setBaselineInput(''); }} className="text-[10px] px-2 py-1 bg-slate-800 text-slate-400 rounded">Annuleer</button>
          </>
        )}
      </div>
    </div>
  );
}

function StatMini({ label, value, sub, color = 'text-slate-200' }) {
  return (
    <div className="bg-slate-800/40 rounded-lg p-2">
      <p className="text-[9px] uppercase text-slate-500 tracking-wide">{label}</p>
      <p className={`text-sm font-bold ${color}`}>{value}</p>
      {sub && <p className="text-[9px] text-slate-600">{sub}</p>}
    </div>
  );
}



function RestwaardePortfolio() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const API = process.env.REACT_APP_BACKEND_URL;

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/trade/bitvavo/balance/user-000`);
      const j = await r.json();
      setData(j);
    } catch (e) {
      setData({ success: false, error: String(e) });
    } finally {
      setLoading(false);
    }
  }, [API]);

  useEffect(() => { load(); }, [load]);

  if (!data || !data.success) {
    return (
      <div data-testid="restwaarde-portfolio" className="bg-slate-900/50 border border-cyan-500/30 rounded-2xl p-4 mb-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-cyan-300 flex items-center gap-2">
            💎 Live restwaarde-portfolio
          </h3>
          <button onClick={load} disabled={loading}
            data-testid="restwaarde-refresh"
            className="text-[11px] text-slate-400 hover:text-white">
            {loading ? '...' : 'Vernieuwen'}
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-2">{loading ? 'Bitvavo balance ophalen...' : 'Geen data'}</p>
      </div>
    );
  }

  // Sorteer op EUR-waarde aflopend
  const balances = (data.balances || []).slice().sort((a, b) => (b.value_eur || 0) - (a.value_eur || 0));
  const eur = balances.find(b => b.symbol === 'EUR');
  const nonEur = balances.filter(b => b.symbol !== 'EUR');
  const above = nonEur.filter(b => (b.value_eur || 0) >= 0.01);
  const dust = nonEur.filter(b => (b.value_eur || 0) < 0.01);
  const total = balances.reduce((s, b) => s + (b.value_eur || 0), 0);
  const nonEurTotal = nonEur.reduce((s, b) => s + (b.value_eur || 0), 0);

  return (
    <div data-testid="restwaarde-portfolio" className="bg-slate-900/50 border border-cyan-500/30 rounded-2xl p-4 mb-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-cyan-300 flex items-center gap-2">
            💎 Live restwaarde-portfolio
          </h3>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Echte Bitvavo balance per coin. Restwaarde = wat er nog van eerdere trades op Bitvavo staat.
          </p>
        </div>
        <div className="text-right">
          <p className="text-[10px] uppercase text-slate-500 tracking-wide">Totaal</p>
          <p className="text-lg font-bold text-white" data-testid="restwaarde-total">€{total.toFixed(2)}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {eur && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-2" data-testid="restwaarde-EUR">
            <p className="text-[10px] uppercase text-emerald-400 tracking-wide">EUR</p>
            <p className="text-sm font-bold text-white">€{eur.value_eur.toFixed(2)}</p>
            <p className="text-[10px] text-slate-500 font-mono">{eur.total.toFixed(2)} EUR</p>
          </div>
        )}
        {above.map(b => (
          <div key={b.symbol} className="bg-slate-800/40 border border-slate-700/40 rounded-lg p-2" data-testid={`restwaarde-${b.symbol}`}>
            <p className="text-[10px] uppercase text-cyan-300 tracking-wide">{b.symbol}</p>
            <p className="text-sm font-bold text-white">€{b.value_eur.toFixed(2)}</p>
            <p className="text-[10px] text-slate-500 font-mono">{b.total < 0.001 ? b.total.toExponential(2) : b.total.toFixed(6)} {b.symbol}</p>
            <p className="text-[9px] text-slate-600">@ €{(b.price_eur || 0).toFixed(2)}</p>
          </div>
        ))}
      </div>

      {dust.length > 0 && (
        <div className="mt-3">
          <button onClick={() => setExpanded(!expanded)}
            data-testid="restwaarde-dust-toggle"
            className="text-[10px] text-slate-500 hover:text-slate-300 flex items-center gap-1">
            {expanded ? '▾' : '▸'} +{dust.length} dust-restwaarde crypto (&lt;€0,01)
          </button>
          {expanded && (
            <div className="mt-2 grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-1.5">
              {dust.map(b => (
                <div key={b.symbol} className="bg-slate-900/60 border border-slate-800 rounded p-1.5" data-testid={`restwaarde-dust-${b.symbol}`}>
                  <p className="text-[9px] uppercase text-slate-500">{b.symbol}</p>
                  <p className="text-[10px] font-mono text-slate-400">{b.total.toExponential(2)}</p>
                  <p className="text-[9px] text-slate-600">€{(b.value_eur || 0).toFixed(4)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500">
        <span>Non-EUR crypto: <span className="text-slate-300 font-semibold">€{nonEurTotal.toFixed(2)}</span></span>
        <button onClick={load} disabled={loading}
          data-testid="restwaarde-refresh"
          className="hover:text-white">
          {loading ? 'Laden...' : 'Vernieuwen ↻'}
        </button>
      </div>
    </div>
  );
}



function ReconcileSparkPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(null); // coin tijdens sync
  const API = process.env.REACT_APP_BACKEND_URL;

  const load = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/trade/reconcile/spark`);
      const j = await r.json();
      setData(j);
    } catch (e) {
      setData({ success: false, error: String(e) });
    } finally {
      setLoading(false);
    }
  };

  const syncCoin = async (coin) => {
    if (!window.confirm(`Sync ${coin} anchor-pot met echte Bitvavo-balance?\n\nDit zet de anchor-pot's position.size + entry_price gelijk aan wat NU op Bitvavo staat.`)) return;
    setSyncing(coin);
    try {
      const r = await fetch(`${API}/api/trade/reconcile/spark/sync-anchor/${coin}`, { method: 'POST' });
      const j = await r.json();
      if (!r.ok || !j.success) {
        window.alert(`Sync ${coin} mislukt: ${j.detail || j.error || 'onbekend'}`);
      } else {
        window.alert(`✅ ${coin} gesynced: ${j.synced.size.toFixed(6)} coin @ €${j.synced.entry_price.toFixed(4)} = €${j.synced.eur_value}`);
        await load();
      }
    } catch (e) {
      window.alert('Fout: ' + e.message);
    } finally {
      setSyncing(null);
    }
  };

  if (!data) {
    return (
      <div className="mb-4 p-3 bg-slate-800/30 rounded-lg border border-slate-700/30">
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-400">
            💰 <strong className="text-slate-200">Reconciliatie</strong> — vergelijk Spark's potjes met echte Bitvavo-balance
          </p>
          <button data-testid="reconcile-load" onClick={load} disabled={loading}
            className="text-xs px-3 py-1 rounded bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50">
            {loading ? '...' : 'Check Bitvavo'}
          </button>
        </div>
      </div>
    );
  }

  if (!data.success) {
    return (
      <div className="mb-4 p-3 bg-red-900/20 rounded-lg border border-red-800/40">
        <p className="text-xs text-red-300">⚠ {data.error || data.detail || 'Onbekende fout'}</p>
        <button onClick={load} className="text-xs underline text-blue-300 mt-1">Opnieuw</button>
      </div>
    );
  }

  const rows = data.rows || [];
  return (
    <div className="mb-4 p-3 bg-slate-800/30 rounded-lg border border-slate-700/40" data-testid="reconcile-table">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-slate-300 font-semibold">💰 Spark · Potje ↔ Bitvavo</p>
        <button onClick={load} disabled={loading}
          className="text-[10px] text-slate-400 hover:text-white">{loading ? '...' : '↻ refresh'}</button>
      </div>
      <table className="w-full text-[11px]">
        <thead>
          <tr className="text-slate-500 border-b border-slate-700">
            <th className="text-left py-1">Coin</th>
            <th className="text-right">#pot</th>
            <th className="text-right">open</th>
            <th className="text-right">🔒</th>
            <th className="text-right">Expected coin</th>
            <th className="text-right">Bitvavo coin</th>
            <th className="text-right">€ waarde</th>
            <th className="text-right">Diff</th>
            <th className="text-left pl-2">Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => {
            const statusCls = {
              exact: 'text-green-400',
              overschot: 'text-amber-400',
              tekort: 'text-red-400',
            }[r.status] || 'text-slate-400';
            const canSync = r.n_locked > 0 && r.actual_coin_amount > 0;
            return (
              <tr key={r.coin} className="border-b border-slate-800/40" data-testid={`reconcile-row-${r.coin}`}>
                <td className="py-1 font-mono text-slate-200">{r.coin}</td>
                <td className="text-right text-slate-400">{r.n_pots}</td>
                <td className="text-right text-green-300">{r.n_open}</td>
                <td className="text-right text-blue-300">{r.n_locked}</td>
                <td className="text-right font-mono text-slate-400">{r.expected_coin_amount.toFixed(6)}</td>
                <td className="text-right font-mono text-slate-200">{r.actual_coin_amount.toFixed(6)}</td>
                <td className="text-right font-mono text-yellow-300">€{r.actual_eur_value.toFixed(2)}</td>
                <td className={`text-right font-mono ${r.diff_coin > 0 ? 'text-amber-300' : r.diff_coin < 0 ? 'text-red-300' : 'text-slate-500'}`}>
                  {r.diff_coin > 0 ? '+' : ''}{r.diff_coin.toFixed(6)}
                </td>
                <td className={`pl-2 ${statusCls} uppercase tracking-wider text-[10px] font-bold`}>{r.status}</td>
                <td className="text-right pl-2">
                  {canSync && (
                    <button data-testid={`reconcile-sync-${r.coin}`}
                      onClick={() => syncCoin(r.coin)}
                      disabled={syncing === r.coin}
                      className="text-[10px] px-2 py-0.5 rounded bg-emerald-700 hover:bg-emerald-600 text-white disabled:opacity-40">
                      {syncing === r.coin ? '...' : '🔄 Sync anchor'}
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="text-[9px] text-slate-500 italic mt-2 leading-snug">
        💡 <strong>🔄 Sync anchor</strong> = neem de anchor-pot (🔒) voor deze coin en zet z'n position.size + entry_price gelijk aan wat NU op Bitvavo staat.
        Gebruik dit na een handmatige aankoop op Bitvavo om het anchor-potje "te vullen". Audit bewaart elke wijziging.
      </p>
    </div>
  );
}

