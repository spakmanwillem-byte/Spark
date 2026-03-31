import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { MainLayout, getPageInfo } from '../layout/MainLayout';
import {
  Activity, Brain, Zap, Plus, Network, GitBranch, BookOpen,
  Users, MessageSquare, Calendar, FolderOpen, Shield, Server,
  Cpu, HardDrive, Clock, TrendingUp, AlertTriangle, CheckCircle,
  Star, Tag, Eye, BarChart3, Layers, Sparkles, FileCode, Package
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function DashboardPage({ activePage = 'dashboard', onNavigate }) {
  const { user, isAdmin } = useAuth();
  const [knowledgeStats, setKnowledgeStats] = useState(null);
  const [fileStats, setFileStats] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);

  useEffect(() => {
    if (activePage !== 'dashboard') return;
    // Fetch all stats in parallel
    Promise.all([
      fetch(`${API}/api/knowledge/stats`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/files/tree`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/auth/users`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/system/health`).then(r => r.json()).catch(() => null),
    ]).then(([kb, files, users, health]) => {
      setKnowledgeStats(kb);
      setFileStats(files);
      setUserStats(users);
      setSystemHealth(health);
    });
  }, [activePage]);

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
  const kbTeHerzien = knowledgeStats?.te_herzien || 0;
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
            <QuickStat icon={BookOpen} value={kbTotal.toLocaleString()} label="Kaarten" color="#f59e0b" />
            <QuickStat icon={Zap} value="156" label="Triggers" color="#22c55e" />
            <QuickStat icon={Users} value={totalUsers} label="Users" color="#3b82f6" />
            <QuickStat icon={FolderOpen} value={totalFiles} label="Bestanden" color="#a855f7" />
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-12 gap-4">

          {/* === Col 1: Knowledge Base (span 4) === */}
          <div className="col-span-12 lg:col-span-4 space-y-4">
            {/* KB Overview */}
            <Card title="Kennisbank" icon={Brain} accent="#f59e0b" badge={`${kbPercent}% compleet`} badgeColor="#22c55e" onClick={() => onNavigate('knowledge', '/knowledge')}>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <MiniStat label="Totaal" value={kbTotal.toLocaleString()} color="#f59e0b" />
                <MiniStat label="Beantwoord" value={kbAnswered.toLocaleString()} color="#22c55e" />
                <MiniStat label="Onbeantwoord" value={kbUnanswered} color="#f97316" />
                <MiniStat label="Te Herzien" value={kbTeHerzien} color="#ef4444" />
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

            {/* Triggers */}
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

            {/* Emoties */}
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
          </div>

          {/* === Col 2: System + Verbanden (span 5) === */}
          <div className="col-span-12 lg:col-span-5 space-y-4">
            {/* System Status */}
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

            {/* Verbanden / Knowledge Graph */}
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
          </div>

          {/* === Col 3: Users + Files + Agenda (span 3) === */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            {/* Users */}
            <Card title="Gebruikers" icon={Users} accent="#3b82f6" badge={`${totalUsers} actief`} badgeColor="#3b82f6" onClick={() => onNavigate('users', '/admin/users')}>
              <div className="space-y-2">
                {userList.slice(0, 4).map((u, i) => (
                  <div key={i} className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-[10px] font-bold" style={{ background: ['#f59e0b','#3b82f6','#22c55e','#a855f7'][i % 4] }}>
                      {(u.naam || 'U')[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-white truncate">{u.naam}</p>
                      <p className="text-[10px] text-slate-500">Gradatie {u.gradatie}</p>
                    </div>
                    <span className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
                  </div>
                ))}
              </div>
            </Card>

            {/* Files */}
            <Card title="Bestanden" icon={FileCode} accent="#a855f7" onClick={() => onNavigate('integrations', '/modules/integrations')}>
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Backend</span>
                  <span className="text-xs text-white font-medium">{backendFiles} bestanden</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-blue-500" style={{ width: `${totalFiles > 0 ? (backendFiles/totalFiles)*100 : 0}%` }} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Frontend</span>
                  <span className="text-xs text-white font-medium">{frontendFiles} bestanden</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-purple-500" style={{ width: `${totalFiles > 0 ? (frontendFiles/totalFiles)*100 : 0}%` }} />
                </div>
                <div className="pt-1 flex items-center justify-between text-[10px] text-slate-500">
                  <span>Totaal</span>
                  <span className="text-slate-300">{totalFiles}</span>
                </div>
              </div>
            </Card>

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
                {[
                  { from: 'Spark AI', msg: 'Hoe kan ik je helpen?', time: 'Nu', color: '#f59e0b' },
                  { from: 'Community', msg: '4 nieuwe berichten', time: '14:30', color: '#a855f7' },
                  { from: 'Sandra', msg: 'Die analyse ziet er goed uit', time: '15:30', color: '#3b82f6' },
                ].map((c, i) => (
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
          </div>

        </div>
      </div>
    </MainLayout>
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

export default DashboardPage;
