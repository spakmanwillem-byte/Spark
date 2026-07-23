import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { MainLayout, getPageInfo } from '../layout/MainLayout';
import {
  Activity, Brain, Zap, Plus, Network, GitBranch, BookOpen,
  Users, MessageSquare, Calendar, FolderOpen, Shield, Server,
  Cpu, HardDrive, Clock, TrendingUp, AlertTriangle, CheckCircle,
  Star, Tag, Eye, BarChart3, Layers, Sparkles, FileCode, Package, Gauge
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// Bouw de "Recente Gesprekken" lijst op uit live data (Spark, Community, Privé)
function buildRecentChats(sparkLog, community, contacts) {
  const fmtTime = (iso) => {
    if (!iso) return '';
    try {
      const t = new Date(iso);
      const now = new Date();
      const diffMs = now - t;
      const diffMin = Math.floor(diffMs / 60000);
      if (diffMin < 1) return 'nu';
      if (diffMin < 60) return `${diffMin}m`;
      if (diffMs < 24 * 3600 * 1000) {
        return t.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' });
      }
      return t.toLocaleDateString('nl-NL', { day: '2-digit', month: '2-digit' });
    } catch { return ''; }
  };

  const items = [];

  // Spark AI laatste gesprek
  const sparkConv = sparkLog?.conversations?.[0];
  if (sparkConv) {
    const msg = sparkConv.user_message || sparkConv.spark_response || '';
    items.push({
      from: 'Spark AI',
      msg: msg.length > 60 ? msg.slice(0, 60) + '…' : msg,
      time: fmtTime(sparkConv.timestamp),
      ts: sparkConv.timestamp,
      color: '#f59e0b',
    });
  }

  // Community laatste bericht
  const commMsg = community?.messages?.[0];
  if (commMsg) {
    const txt = commMsg.message || '';
    items.push({
      from: commMsg.user_name ? `Community · ${commMsg.user_name}` : 'Community',
      msg: txt.length > 60 ? txt.slice(0, 60) + '…' : txt,
      time: fmtTime(commMsg.timestamp),
      ts: commMsg.timestamp,
      color: '#a855f7',
    });
  }

  // Privé: eerste contact met een last_message
  const contactList = contacts?.contacts || [];
  const lastPrive = contactList.find(c => c.last_message);
  if (lastPrive) {
    items.push({
      from: lastPrive.naam || 'Privé',
      msg: lastPrive.last_message,
      time: lastPrive.last_time || '',
      ts: null,
      color: lastPrive.color || '#3b82f6',
    });
  }

  return items;
}

export function DashboardPage({ activePage = 'dashboard', onNavigate }) {
  const { user, isAdmin } = useAuth();
  const userGrad = user?.gradatie ?? 7;
  const isAdminUser = userGrad <= 2; // v4_dashboard_grad_001: 1-2 zien admin widgets
  const [knowledgeStats, setKnowledgeStats] = useState(null);
  const [fileStats, setFileStats] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [storageStats, setStorageStats] = useState(null);
  const [shadowStats, setShadowStats] = useState(null);
  const [shadowUnused, setShadowUnused] = useState(null);
  const [perfStats, setPerfStats] = useState(null); // v4_perf_widget_001
  const [recentChats, setRecentChats] = useState([]);
  const [kbv2Stats, setKbv2Stats] = useState(null);
  // v6_dashboard_fin_001 (28 mei) — saldo + vermogen widget
  const [finStats, setFinStats] = useState(null);

  useEffect(() => {
    if (activePage !== 'dashboard') return;
    // Fetch all stats in parallel
    Promise.all([
      fetch(`${API}/api/knowledge/stats`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/files/tree`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/auth/users`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/system/health`).then(r => r.json()).catch(() => null),
      user?.id ? fetch(`${API}/api/archive/${user.id}/stats`).then(r => r.json()).catch(() => null) : null,
      fetch(`${API}/api/chat/shadow/stats`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/chat/shadow/unused`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/admin/storage-cache`).then(r => r.json()).catch(() => null),
      user?.id ? fetch(`${API}/api/chat/logs/${user.id}?limit=1&channel=spark`).then(r => r.json()).catch(() => null) : null,
      fetch(`${API}/api/bots/community/messages?limit=1`).then(r => r.json()).catch(() => null),
      user?.id ? fetch(`${API}/api/contacts/list?user_id=${user.id}`).then(r => r.json()).catch(() => null) : null,
      // v5_dashboard_kbv2_001 — KB v2 lade-verdeling
      fetch(`${API}/api/kb/v2/stats`).then(r => r.json()).catch(() => null),
      // v6_dashboard_fin_001 — financiële widget data
      user?.id ? fetch(`${API}/api/dashboard/financial/${user.id}`).then(r => r.json()).catch(() => null) : null,
    ]).then(([kb, files, users, health, storage, shadow, unused, perf, sparkLog, community, contacts, kbv2, fin]) => {
      setKnowledgeStats(kb);
      setFileStats(files);
      setUserStats(users);
      setSystemHealth(health);
      setStorageStats(storage);
      setShadowStats(shadow);
      setShadowUnused(unused);
      setPerfStats(perf);
      setRecentChats(buildRecentChats(sparkLog, community, contacts));
      setKbv2Stats(kbv2);
      setFinStats(fin);
    });
  }, [activePage, user?.id]);

  const pageInfo = getPageInfo(activePage);
  const PageIcon = pageInfo?.icon || Activity;

  if (activePage !== 'dashboard') {
    return (
      <MainLayout activePage={activePage} onNavigate={onNavigate}>
        <div className="p-8">
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center">
                <PageIcon className="w-5 h-5 text-amber-400" />
              </div>
              <h1 className="text-2xl font-bold text-white">{pageInfo?.label || 'Module'}</h1>
            </div>
          </div>
          <div className="flex-1 flex items-center justify-center min-h-[60vh]">
            <div className="text-center max-w-md">
              <div className="w-20 h-20 bg-slate-800/50 border border-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <PageIcon className="w-10 h-10 text-slate-500" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">{pageInfo?.label}</h2>
              <p className="text-slate-400">Deze module is klaar om ingericht te worden.</p>
            </div>
          </div>
        </div>
      </MainLayout>
    );
  }

  const kbTotal = knowledgeStats?.total || 0;
  const kbUnanswered = knowledgeStats?.unanswered || 0;
  const kbAnswered = knowledgeStats?.answered || 0;
  const kbReviewPending = knowledgeStats?.review_pending || knowledgeStats?.te_herzien || 0;
  const kbPercent = kbTotal > 0 ? Math.round((kbAnswered / kbTotal) * 100) : 0;
  const totalFiles = fileStats?.total_files || 0;
  const backendFiles = fileStats?.tree?.[0]?.files?.length || 0;
  const frontendFiles = fileStats?.tree?.[1]?.files?.length || 0;
  const userList = Array.isArray(userStats) ? userStats : userStats?.users || [];
  const totalUsers = userList.length;
  const now = new Date();
  const timeStr = now.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' });
  const dateStr = now.toLocaleDateString('nl-NL', { weekday: 'short', day: 'numeric', month: 'long', year: 'numeric' });

  return (
    <MainLayout activePage="dashboard" onNavigate={onNavigate}>
      <div data-testid="dashboard-page" className="p-4 md:p-6 space-y-4 max-w-[1600px] mx-auto">

        {/* Top bar - Time + Welcome + Quick stats */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight">{timeStr}</h1>
              <p className="text-xs text-slate-500 capitalize">{dateStr}</p>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <p className="text-sm text-slate-400">
              Welkom, <span className="text-amber-400 font-semibold">{user?.naam}</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            {isAdminUser && <QuickStat icon={BookOpen} value={kbTotal.toLocaleString()} label="Kaarten" color="#f59e0b" />}
            {isAdminUser && <QuickStat icon={Zap} value="156" label="Triggers" color="#22c55e" />}
            {isAdminUser && <QuickStat icon={Users} value={totalUsers} label="Users" color="#3b82f6" />}
            {isAdminUser && <QuickStat icon={FolderOpen} value={totalFiles} label="Bestanden" color="#a855f7" />}
          </div>
        </div>

        {/* v6_dashboard_fin_001 — Saldo + Vermogen widget VERWIJDERD (sessie 23).
            Financiële info staat al in /modules/wallet en /modules/trade — dashboard hoeft het niet te dupliceren. */}

        {/* Main Grid */}
        <div className="grid grid-cols-12 gap-4">

          {/* === Col 1: Knowledge Base (span 4) === */}
          <div className="col-span-12 lg:col-span-4 space-y-4">
            {/* v6_dash_privacy_001 — KB Overview alleen voor admin */}
            {isAdminUser && (
            <Card title="Kennisbank" icon={Brain} accent="#f59e0b" badge={`${kbPercent}% compleet`} badgeColor="#22c55e" onClick={() => onNavigate('knowledge', '/knowledge')}>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <MiniStat label="Totaal" value={kbTotal.toLocaleString()} color="#f59e0b" />
                <MiniStat label="Beantwoord" value={kbAnswered.toLocaleString()} color="#22c55e" />
                <MiniStat label="Onbeantwoord" value={kbUnanswered} color="#f97316" />
                <MiniStat label="Renew" value={kbReviewPending} color="#ef4444" />
              </div>
              {/* Progress bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>Voortgang</span>
                  <span>{kbPercent}%</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${kbPercent}%`, background: 'linear-gradient(90deg, #f59e0b, #22c55e)' }} />
                </div>
              </div>
            </Card>
            )}

            {/* v5_dashboard_kbv2_001 — KB v2 Lades verdeling (ADMIN gradatie ≤ 2) */}
            {isAdminUser && kbv2Stats && (
              <Card title="KB v2 Lades" icon={Brain} accent="#a855f7"
                badge={`${(kbv2Stats.lades ? Object.values(kbv2Stats.lades).reduce((a, b) => a + (b.count || 0), 0) : 0) + (kbv2Stats.inbox_count || 0)} totaal`}
                badgeColor="#a855f7"
                onClick={() => onNavigate('knowledge-v2', '/knowledge')}>
                <div className="grid grid-cols-2 gap-2 mb-3">
                  {[
                    { id: 'voelen',  icon: '🌸', color: '#ec4899' },
                    { id: 'spreken', icon: '💬', color: '#06b6d4' },
                    { id: 'weten',   icon: '🧠', color: '#f59e0b' },
                    { id: 'doen',    icon: '🎭', color: '#a855f7' },
                  ].map(l => {
                    const d = kbv2Stats.lades?.[l.id] || {};
                    return (
                      <div key={l.id} className="flex items-center gap-2 bg-slate-800/40 rounded-lg p-2 border border-slate-800">
                        <span className="text-lg">{l.icon}</span>
                        <div>
                          <p className="text-[10px] text-slate-500 capitalize">{d.naam || l.id}</p>
                          <p className="text-sm font-bold" style={{ color: l.color }}>{d.count || 0}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-2 mb-2">
                  <p className="text-[10px] text-amber-300">
                    📥 <strong>{kbv2Stats.inbox_count || 0}</strong> kaarten in inbox wachten op indeling
                  </p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); onNavigate('namen', '/spark/namen'); }}
                  className="w-full bg-purple-500/10 border border-purple-500/30 rounded-lg p-2 mb-2 hover:bg-purple-500/20 transition text-left"
                  data-testid="btn-open-namen"
                >
                  <p className="text-[10px] text-purple-300">
                    🏷️ <strong>Namen-lade</strong> — voor- & achternamen, koosnamen (klik om te openen)
                  </p>
                </button>
                {/* v6_kb_v1_v2_split_001 — Toon ook KB v1 totaal voor context */}
                {knowledgeStats && (
                  <div className="bg-slate-800/30 rounded-lg p-2 text-[10px] text-slate-400">
                    KB v1 (legacy): <strong className="text-slate-300">{kbTotal}</strong> kaarten
                    {kbReviewPending > 0 && (
                      <span className="text-amber-400"> • {kbReviewPending} te herzien</span>
                    )}
                  </div>
                )}
              </Card>
            )}
            {isAdminUser && (
            <Card title="Triggers" icon={Zap} accent="#22c55e" badge="156 ACTIEF" badgeColor="#22c55e" onClick={() => onNavigate('triggers', '/spark/triggers')}>
              <div className="space-y-2">
                {[
                  { cat: 'Begroetingen', count: 42, color: '#22c55e' },
                  { cat: 'Afscheid', count: 28, color: '#3b82f6' },
                  { cat: 'Emotie', count: 35, color: '#f59e0b' },
                  { cat: 'Acties', count: 51, color: '#a855f7' },
                ].map(t => (
                  <div key={t.cat} className="flex items-center gap-3">
                    <span className="text-xs text-slate-400 w-24">{t.cat}</span>
                    <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${(t.count / 60) * 100}%`, background: t.color }} />
                    </div>
                    <span className="text-xs text-slate-300 w-8 text-right">{t.count}</span>
                  </div>
                ))}
              </div>
            </Card>
            )}

            {/* Emoties — v6_dash_privacy_001 ADMIN ONLY */}
            {isAdminUser && (
            <Card title="Emotie Systeem" icon={Sparkles} accent="#ec4899" onClick={() => onNavigate('emotions', '/spark/emotions')}>
              <div className="flex items-center justify-between">
                {[
                  { emoji: 'Blij', pct: 45, color: '#22c55e' },
                  { emoji: 'Neutraal', pct: 30, color: '#3b82f6' },
                  { emoji: 'Boos', pct: 10, color: '#ef4444' },
                  { emoji: 'Verdriet', pct: 15, color: '#a855f7' },
                ].map(e => (
                  <div key={e.emoji} className="text-center">
                    <div className="w-10 h-10 rounded-full mx-auto mb-1 flex items-center justify-center" style={{ background: `${e.color}15`, border: `2px solid ${e.color}` }}>
                      <span className="text-xs font-bold" style={{ color: e.color }}>{e.pct}%</span>
                    </div>
                    <span className="text-[10px] text-slate-500">{e.emoji}</span>
                  </div>
                ))}
              </div>
            </Card>
            )}
          </div>

          {/* === Col 2: System + Verbanden (span 5) === */}
          <div className="col-span-12 lg:col-span-5 space-y-4">
            {/* System Status — ADMIN ONLY */}
            {isAdminUser && (
            <Card title="Systeem Status" icon={Server} accent="#3b82f6">
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="p-3 bg-slate-800/50 rounded-xl text-center">
                  <Cpu className="w-5 h-5 text-green-400 mx-auto mb-1" />
                  <p className="text-lg font-bold text-white">OK</p>
                  <p className="text-[10px] text-slate-500">Backend</p>
                </div>
                <div className="p-3 bg-slate-800/50 rounded-xl text-center">
                  <HardDrive className="w-5 h-5 text-green-400 mx-auto mb-1" />
                  <p className="text-lg font-bold text-white">OK</p>
                  <p className="text-[10px] text-slate-500">Storage</p>
                </div>
                <div className="p-3 bg-slate-800/50 rounded-xl text-center">
                  <Shield className="w-5 h-5 text-green-400 mx-auto mb-1" />
                  <p className="text-lg font-bold text-white">3</p>
                  <p className="text-[10px] text-slate-500">Modules</p>
                </div>
              </div>
              <div className="space-y-2">
                <StatusRow label="Auth Module" status="active" />
                <StatusRow label="Knowledge Module" status="active" />
                <StatusRow label="Files & Sandbox" status="active" />
                <StatusRow label="Chat / Spark Brain" status="planned" />
              </div>
            </Card>
            )}

            {/* Verbanden / Knowledge Graph — v6_dash_privacy_001 ADMIN ONLY */}
            {isAdminUser && (
            <Card title="Verbanden" icon={Network} accent="#06b6d4" badge={`${kbTotal} nodes`} badgeColor="#06b6d4" onClick={() => onNavigate('connections', '/spark/connections')}>
              <div className="aspect-[16/9] bg-slate-800/30 rounded-xl border border-slate-700/50 relative overflow-hidden">
                {/* Simulated knowledge graph nodes */}
                <svg className="w-full h-full" viewBox="0 0 400 225">
                  {/* Lines */}
                  {[[200,112,100,50],[200,112,300,50],[200,112,80,180],[200,112,320,180],[200,112,150,30],[200,112,250,30],[100,50,80,180],[300,50,320,180],[150,30,250,30]].map(([x1,y1,x2,y2], i) => (
                    <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#334155" strokeWidth="1" />
                  ))}
                  {/* Center node */}
                  <circle cx="200" cy="112" r="18" fill="#f59e0b" opacity="0.8" />
                  <text x="200" y="116" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">Spark</text>
                  {/* Outer nodes */}
                  {[[100,50,'#3b82f6','Kennis'],[300,50,'#22c55e','Users'],[80,180,'#a855f7','Emotie'],[320,180,'#ec4899','Trigger'],[150,30,'#06b6d4','Topic'],[250,30,'#f97316','Tags']].map(([cx,cy,fill,label], i) => (
                    <g key={i}>
                      <circle cx={cx} cy={cy} r="12" fill={fill} opacity="0.6" />
                      <text x={cx} y={Number(cy)+3} textAnchor="middle" fill="white" fontSize="6">{label}</text>
                    </g>
                  ))}
                </svg>
              </div>
            </Card>
            )}
          </div>

          {/* === Col 3: Users + Files + Agenda (span 3) === */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            {/* Users — ADMIN ONLY */}
            {isAdminUser && (
            <Card title="Gebruikers" icon={Users} accent="#3b82f6" badge={`${totalUsers} actief`} badgeColor="#3b82f6" onClick={() => onNavigate('users', '/admin/users')}>
              <div className="space-y-2">
                {userList.slice(0, 4).map((u, i) => (
                  <div key={i} className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-[10px] font-bold" style={{ background: ['#f59e0b','#3b82f6','#22c55e','#a855f7'][i % 4] }}>
                      {(u.naam || 'U')[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-white truncate">{u.naam}</p>
                      <p className="text-[10px] text-slate-500">{u.rol || u.gradatie_titel || (isAdminUser ? `Gradatie ${u.gradatie}` : '')}</p>
                    </div>
                    <span className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
                  </div>
                ))}
              </div>
            </Card>
            )}

            {/* Mijn Opslag */}
            <StorageCard storageStats={storageStats} onNavigate={onNavigate} />

            {/* Agenda Quick */}
            <Card title="Agenda" icon={Calendar} accent="#f97316" onClick={() => onNavigate('calendar', '/calendar')}>
              <div className="space-y-2">
                {[
                  { time: '09:00', title: 'Daily standup', color: '#3b82f6' },
                  { time: '11:30', title: 'Knowledge review', color: '#f59e0b' },
                  { time: '14:00', title: 'Module testing', color: '#22c55e' },
                ].map((ev, i) => (
                  <div key={i} className="flex items-center gap-2.5">
                    <div className="w-1 h-8 rounded-full" style={{ background: ev.color }} />
                    <div>
                      <p className="text-xs text-white">{ev.title}</p>
                      <p className="text-[10px] text-slate-500">{ev.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Gesprekken */}
            <Card title="Gesprekken" icon={MessageSquare} accent="#06b6d4" onClick={() => onNavigate('chat', '/chat')}>
              <div className="space-y-2">
                {recentChats.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">Nog geen recente gesprekken.</p>
                ) : recentChats.map((c, i) => (
                  <div key={i} className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0" style={{ background: c.color }}>
                      {c.from[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-white truncate">{c.from}</p>
                        <span className="text-[10px] text-slate-500 ml-2 flex-shrink-0">{c.time}</span>
                      </div>
                      <p className="text-[10px] text-slate-400 truncate">{c.msg}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Shadow Observer — ADMIN ONLY */}
            {isAdminUser && (
            <ShadowCard shadowStats={shadowStats} shadowUnused={shadowUnused} />
            )}

            {/* Performance — ADMIN ONLY (v4_perf_widget_001) */}
            {isAdminUser && (
            <PerfCard perfStats={perfStats} />
            )}
          </div>

        </div>
      </div>
    </MainLayout>
  );
}

/* === Storage Card (eigen opslag met breakdown chart) === */
function StorageCard({ storageStats, onNavigate }) {
  const q = storageStats?.quota || {};
  const baseGb = q.base_gb || 0;
  const purchasedGb = q.purchased_gb || 0;
  const giftGb = q.gift_gb || 0;
  const totalGb = q.total_gb || 1;
  const usedBytes = q.used_bytes || 0;
  const totalBytes = q.total_bytes || 1;
  const usedPercent = q.used_percent || 0;
  const totalFiles = storageStats?.total_files || 0;

  // Bytes formatter
  const fmtBytes = (n) => {
    if (!n) return '0 B';
    const u = ['B','KB','MB','GB'];
    const i = Math.min(Math.floor(Math.log(n) / Math.log(1024)), 3);
    return `${(n / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${u[i]}`;
  };

  // Breakdown bar segments (percentages van totaal)
  const basePct = (baseGb / totalGb) * 100;
  const purchasedPct = (purchasedGb / totalGb) * 100;
  const giftPct = (giftGb / totalGb) * 100;

  const colors = {
    base: '#3b82f6',      // blauw — basis
    purchased: '#22c55e', // groen — gekocht
    gift: '#ec4899',      // roze — cadeau
    used: '#f59e0b',      // oranje — gebruikt
  };

  return (
    <div data-testid="storage-card"
      className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden cursor-pointer hover:border-slate-600 transition-colors"
      onClick={() => onNavigate('archief', '/archief')}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800/50">
        <div className="flex items-center gap-2">
          <HardDrive className="w-4 h-4" style={{ color: '#3b82f6' }} />
          <h3 className="text-sm font-semibold text-white">Mijn Opslag</h3>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{
          background: usedPercent > 90 ? '#ef444415' : '#22c55e15',
          color: usedPercent > 90 ? '#ef4444' : '#22c55e',
        }}>
          {totalGb}GB
        </span>
      </div>
      <div className="p-4 space-y-3">
        {/* Quota breakdown bar */}
        <div>
          <div className="flex items-baseline justify-between mb-1.5">
            <span className="text-xs text-slate-400">
              {fmtBytes(usedBytes)} <span className="text-slate-600">van</span> {fmtBytes(totalBytes)}
            </span>
            <span className="text-xs font-medium" style={{ color: colors.used }}>{usedPercent}%</span>
          </div>
          {/* Gestapeld: basis | gekocht | cadeau */}
          <div className="h-3 bg-slate-800 rounded-full overflow-hidden flex relative">
            {basePct > 0 && <div style={{ width: `${basePct}%`, background: colors.base }} title={`Basis: ${baseGb}GB`} />}
            {purchasedPct > 0 && <div style={{ width: `${purchasedPct}%`, background: colors.purchased }} title={`Gekocht: ${purchasedGb}GB`} />}
            {giftPct > 0 && <div style={{ width: `${giftPct}%`, background: colors.gift }} title={`Cadeau: ${giftGb}GB`} />}
            {/* Used overlay */}
            <div className="absolute top-0 left-0 h-full bg-gradient-to-r from-amber-400/30 to-amber-500/60 border-r-2 border-amber-400"
              style={{ width: `${Math.min(usedPercent, 100)}%` }} />
          </div>
        </div>

        {/* Legend met cijfers */}
        <div className="grid grid-cols-3 gap-2">
          <div className="p-2 rounded-lg" style={{ background: `${colors.base}10`, border: `1px solid ${colors.base}30` }}>
            <div className="flex items-center gap-1 mb-0.5">
              <span className="w-2 h-2 rounded-full" style={{ background: colors.base }} />
              <span className="text-[9px] text-slate-400 uppercase tracking-wider">Basis</span>
            </div>
            <p className="text-sm font-bold text-white">{baseGb}<span className="text-[10px] text-slate-500 ml-0.5">GB</span></p>
          </div>
          <div className="p-2 rounded-lg" style={{ background: `${colors.purchased}10`, border: `1px solid ${colors.purchased}30` }}>
            <div className="flex items-center gap-1 mb-0.5">
              <span className="w-2 h-2 rounded-full" style={{ background: colors.purchased }} />
              <span className="text-[9px] text-slate-400 uppercase tracking-wider">Gekocht</span>
            </div>
            <p className="text-sm font-bold text-white">{purchasedGb}<span className="text-[10px] text-slate-500 ml-0.5">GB</span></p>
          </div>
          <div className="p-2 rounded-lg" style={{ background: `${colors.gift}10`, border: `1px solid ${colors.gift}30` }}>
            <div className="flex items-center gap-1 mb-0.5">
              <span className="w-2 h-2 rounded-full" style={{ background: colors.gift }} />
              <span className="text-[9px] text-slate-400 uppercase tracking-wider">Cadeau</span>
            </div>
            <p className="text-sm font-bold text-white">{giftGb}<span className="text-[10px] text-slate-500 ml-0.5">GB</span></p>
          </div>
        </div>

        {/* Bottom: totaal files + upgrade-CTA */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/50">
          <span className="text-[10px] text-slate-500">{totalFiles} bestanden opgeslagen</span>
          <button onClick={(e) => { e.stopPropagation(); onNavigate('winkel', '/modules/winkel'); }}
            data-testid="storage-upgrade-btn"
            className="flex items-center gap-1 text-[10px] text-amber-400 hover:text-amber-300 font-medium">
            <Plus className="w-3 h-3" /> Koop extra
          </button>
        </div>
      </div>
    </div>
  );
}

/* === Reusable Card === */
function Card({ title, icon: Icon, accent, badge, badgeColor, children, onClick }) {
  return (
    <div
      data-testid={`card-${title.toLowerCase().replace(/\s/g, '-')}`}
      className={`bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden ${onClick ? 'cursor-pointer hover:border-slate-600 transition-colors' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800/50">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4" style={{ color: accent }} />
          <h3 className="text-sm font-semibold text-white">{title}</h3>
        </div>
        {badge && (
          <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ background: `${badgeColor}15`, color: badgeColor }}>
            {badge}
          </span>
        )}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

/* === Quick stat in header === */
function QuickStat({ icon: Icon, value, label, color }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/60 border border-slate-800 rounded-lg">
      <Icon className="w-3.5 h-3.5" style={{ color }} />
      <span className="text-sm font-bold text-white">{value}</span>
      <span className="text-[10px] text-slate-500">{label}</span>
    </div>
  );
}

/* === Mini stat in card === */
function MiniStat({ label, value, color }) {
  return (
    <div className="p-2 bg-slate-800/40 rounded-lg">
      <p className="text-[10px] text-slate-500 mb-0.5">{label}</p>
      <p className="text-sm font-bold" style={{ color }}>{value}</p>
    </div>
  );
}

/* === Status row === */
function StatusRow({ label, status }) {
  const isActive = status === 'active';
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-xs text-slate-400">{label}</span>
      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${isActive ? 'bg-green-500/10 text-green-400' : 'bg-slate-700/50 text-slate-500'}`}>
        {isActive ? 'Actief' : 'Gepland'}
      </span>
    </div>
  );
}

/* === Shadow Observer Widget (voorlopig op dashboard) === */
function ShadowCard({ shadowStats, shadowUnused }) {
  const totals = shadowStats?.totals || {};
  const events = totals.events || 0;
  const corrections = totals.corrections || 0;
  const confirmations = totals.confirmations || 0;
  const fallbacks = totals.fallbacks || 0;
  const matches = totals.knowledge_matches || 0;
  const correctPct = events > 0 ? Math.round((corrections / events) * 100) : 0;
  const fallbackPct = events > 0 ? Math.round((fallbacks / events) * 100) : 0;

  // Top-3 ongebruikte items
  const unusedTriggers = (shadowUnused?.triggers || []).slice(0, 3);
  const unusedVocab = (shadowUnused?.vocab || []).slice(0, 3);
  const unusedBijbel = (shadowUnused?.bijbel || []).slice(0, 3);

  // Top-3 meest gebruikte triggers
  const triggersUsed = shadowStats?.triggers_used || {};
  const topTriggers = Object.entries(triggersUsed)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  const lastSeen = shadowStats?.last_event_at
    ? new Date(shadowStats.last_event_at).toLocaleString('nl-NL', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })
    : '—';

  return (
    <div data-testid="shadow-widget" className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Eye className="w-3.5 h-3.5 text-emerald-400" />
          <h3 className="text-xs font-semibold text-white">Shadow Observer</h3>
          <span className="text-[9px] text-emerald-300 bg-emerald-500/10 px-1.5 py-0.5 rounded uppercase tracking-wider">live</span>
        </div>
        <span className="text-[9px] text-slate-500">{lastSeen}</span>
      </div>

      <div className="p-3 space-y-3">
        {/* Top stats */}
        <div className="grid grid-cols-3 gap-2">
          <ShadowStat label="Events" value={events} color="text-white" />
          <ShadowStat label="Correcties" value={`${corrections} (${correctPct}%)`} color="text-amber-300" />
          <ShadowStat label="Fallback" value={`${fallbacks} (${fallbackPct}%)`} color="text-rose-300" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <ShadowStat label="Bevestigingen" value={confirmations} color="text-emerald-300" />
          <ShadowStat label="K-matches" value={matches} color="text-blue-300" />
        </div>

        {/* Top triggers */}
        {topTriggers.length > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Top triggers</p>
            <div className="space-y-1">
              {topTriggers.map(([name, count], i) => (
                <div key={i} className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-300 truncate">{name}</span>
                  <span className="text-slate-500 ml-2">×{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Ongebruikt */}
        {(unusedTriggers.length + unusedVocab.length + unusedBijbel.length) > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Nog niet gebruikt</p>
            <div className="space-y-1 text-[11px]">
              {unusedTriggers.length > 0 && (
                <UnusedRow label="Triggers" items={unusedTriggers} total={shadowUnused?.triggers?.length || 0} color="text-emerald-300" />
              )}
              {unusedVocab.length > 0 && (
                <UnusedRow label="Vocab" items={unusedVocab} total={shadowUnused?.vocab?.length || 0} color="text-purple-300" />
              )}
              {unusedBijbel.length > 0 && (
                <UnusedRow label="Bijbel" items={unusedBijbel} total={shadowUnused?.bijbel?.length || 0} color="text-amber-300" />
              )}
            </div>
          </div>
        )}

        {events === 0 && (
          <p className="text-[10px] text-slate-500 italic text-center py-2">
            Nog geen chat-events. Praat met Spark om data te verzamelen.
          </p>
        )}
      </div>
    </div>
  );
}

function ShadowStat({ label, value, color }) {
  return (
    <div className="bg-slate-950/40 rounded-md px-2 py-1.5">
      <p className="text-[9px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`text-sm font-bold ${color}`}>{value}</p>
    </div>
  );
}

function UnusedRow({ label, items, total, color }) {
  return (
    <div className="flex items-start gap-2">
      <span className={`${color} font-medium flex-shrink-0`}>{label}:</span>
      <span className="text-slate-400 truncate flex-1">{items.join(', ')}</span>
      {total > items.length && <span className="text-slate-600 text-[9px] flex-shrink-0">+{total - items.length}</span>}
    </div>
  );
}

// v4_perf_widget_001 — Performance Card (admin-only)
function PerfCard({ perfStats }) {
  if (!perfStats) {
    return (
      <div className="rounded-2xl p-6 border border-slate-800/50 bg-gradient-to-br from-slate-900/80 to-slate-950/40">
        <p className="text-xs text-slate-500">Performance laden...</p>
      </div>
    );
  }
  const totalMb = perfStats.total_cached_mb || 0;
  const files = perfStats.files || [];
  const handleClear = async () => {
    if (!window.confirm('Cache leegmaken? Volgende request wordt langzamer.')) return;
    await fetch(`${API}/api/admin/storage-cache/clear`, { method: 'POST' });
    window.location.reload();
  };
  return (
    <div data-testid="perf-card" className="rounded-2xl p-6 border border-cyan-500/20 bg-gradient-to-br from-cyan-950/30 to-slate-950/40 hover:border-cyan-500/40 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Gauge className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white">Performance</h3>
        </div>
        <span className="text-[10px] text-cyan-300/70 uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">cache live</span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="p-3 bg-slate-800/40 rounded-xl">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">In geheugen</p>
          <p className="text-lg font-bold text-cyan-300">{totalMb} <span className="text-xs text-slate-500">MB</span></p>
        </div>
        <div className="p-3 bg-slate-800/40 rounded-xl">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">Files gecached</p>
          <p className="text-lg font-bold text-white">{files.length}</p>
        </div>
      </div>

      <div className="space-y-1.5 max-h-32 overflow-y-auto mb-3">
        {files.map((f, idx) => {
          const naam = (f.path || '').split('/').pop();
          return (
            <div key={idx} className="flex items-center justify-between text-[11px] py-1 border-b border-slate-800/50 last:border-0">
              <span className="text-slate-400 truncate flex-1 font-mono">{naam}</span>
              <span className="text-cyan-300/70 ml-2 flex-shrink-0">{Math.round(f.size_kb)}KB</span>
            </div>
          );
        })}
        {files.length === 0 && (
          <p className="text-[10px] text-slate-600 text-center py-2">Geen cache — eerste request wacht</p>
        )}
      </div>

      <button
        data-testid="perf-clear-btn"
        onClick={handleClear}
        className="w-full text-[10px] text-slate-500 hover:text-cyan-300 py-1 rounded border border-slate-800 hover:border-cyan-500/30 transition-colors"
      >
        Cache leegmaken
      </button>
    </div>
  );
}

export default DashboardPage;
