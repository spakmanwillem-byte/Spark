import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Award, Trophy, Crown, Star, Medal,
  BookOpen, Flame
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;
const rankColors = ['#f59e0b', '#94a3b8', '#b45309'];
const rankIcons = [Crown, Medal, Medal];

// v4_leaderboard_001 — Echte data uit /api/achievements/leaderboard
export function LeaderboardPage({ onNavigate }) {
  const { user } = useAuth();
  const [period, setPeriod] = useState('alltime');
  const [sortBy, setSortBy] = useState('xp');
  const [data, setData] = useState({ leaderboard: [], total_users: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/api/achievements/leaderboard?period=${period}&limit=50`)
      .then(r => r.json())
      .then(d => { setData(d || { leaderboard: [] }); setLoading(false); })
      .catch(() => setLoading(false));
  }, [period]);

  const sorted = [...(data.leaderboard || [])].sort((a, b) => (b[sortBy] || 0) - (a[sortBy] || 0));
  // Top 3 voor podium (sortBy=xp altijd voor podium)
  const top3 = [...(data.leaderboard || [])].slice(0, 3);

  return (
    <MainLayout activePage="leaderboard" onNavigate={onNavigate}>
      <div data-testid="leaderboard-page" className="p-4 md:p-6 space-y-5 max-w-4xl mx-auto">

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
            <Award className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-white">Leaderboard</h1>
            <p className="text-xs text-slate-500">{data.total_users} gebruikers — live data uit Spark Core</p>
          </div>
          {/* Period selector */}
          <div className="flex items-center gap-1 bg-slate-800/50 rounded-lg p-1">
            {[
              { id: 'week', label: 'Week' },
              { id: 'month', label: 'Maand' },
              { id: 'alltime', label: 'All-time' },
            ].map(p => (
              <button key={p.id} data-testid={`period-${p.id}`} onClick={() => setPeriod(p.id)}
                className={`px-2.5 py-1 rounded text-[10px] font-medium transition-colors ${period === p.id ? 'bg-amber-500/20 text-amber-300' : 'text-slate-500 hover:text-white'}`}>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {loading && <p className="text-xs text-slate-500 text-center py-6">Aan het laden...</p>}

        {/* Podium */}
        {!loading && top3.length >= 1 && (
          <div className="flex items-end justify-center gap-4 pt-4 pb-2">
            {[1, 0, 2].map(idx => {
              const p = top3[idx];
              if (!p) return null;
              const isFirst = idx === 0;
              const RankIcon = rankIcons[idx] || Medal;
              return (
                <div key={idx} className={`flex flex-col items-center ${isFirst ? 'order-2' : idx === 1 ? 'order-1' : 'order-3'}`}>
                  <RankIcon className="w-5 h-5 mb-2" style={{ color: rankColors[idx] || '#64748b' }} />
                  <div className={`rounded-2xl flex items-center justify-center text-white font-bold border-2 ${isFirst ? 'w-20 h-20 text-2xl' : 'w-16 h-16 text-xl'}`}
                    style={{ background: `linear-gradient(135deg, ${rankColors[idx]}40, ${rankColors[idx]}20)`, borderColor: `${rankColors[idx]}60` }}>
                    {p.naam[0]}
                  </div>
                  <p className="text-sm text-white font-semibold mt-2">{p.naam}</p>
                  <p className="text-xs text-amber-400 font-medium">{(p.xp || 0).toLocaleString()} XP</p>
                  <div className="flex items-center gap-1 mt-1">
                    <span className="text-[10px] text-slate-500">Lvl {p.level || 0}</span>
                    <span className="text-slate-700">|</span>
                    <span className="text-[10px] text-slate-500">{p.achievements || 0} badges</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Sort options */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {[
            { id: 'xp', label: 'XP', icon: Star },
            { id: 'words', label: 'Woorden', icon: BookOpen },
            { id: 'achievements', label: 'Achievements', icon: Trophy },
          ].map(s => (
            <button key={s.id} data-testid={`sort-${s.id}`} onClick={() => setSortBy(s.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex-shrink-0 ${sortBy === s.id ? 'bg-amber-500/15 text-amber-400' : 'bg-slate-800/50 text-slate-400 hover:text-white'}`}>
              <s.icon className="w-3.5 h-3.5" /> {s.label}
            </button>
          ))}
        </div>

        {/* Full rankings */}
        {!loading && (
          <div className="space-y-2">
            {sorted.map((p, i) => {
              const isMe = p.user_id === user?.id;
              return (
                <div key={p.user_id || i} data-testid={`rank-${i + 1}`}
                  className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${isMe ? 'border-amber-500/30 bg-amber-500/5' : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'}`}>
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ${i < 3 ? 'text-white' : 'text-slate-500 bg-slate-800'}`}
                    style={i < 3 ? { background: rankColors[i] } : {}}>
                    {i + 1}
                  </div>
                  <div className="w-10 h-10 rounded-xl overflow-hidden flex items-center justify-center text-white font-bold flex-shrink-0"
                    style={p.avatar_ref ? {} : { background: `linear-gradient(135deg, ${['#f59e0b', '#3b82f6', '#22c55e', '#a855f7'][i % 4]}, ${['#ea580c', '#6366f1', '#10b981', '#ec4899'][i % 4]})` }}>
                    {p.avatar_ref && p.avatar_ref.startsWith('gallery:') ? (
                      <img src={`${API}/api/avatar/gallery/${p.avatar_ref.split(':')[1]}/image`} alt={p.naam}
                        className="w-full h-full object-cover"
                        onError={(e) => { e.target.style.display = 'none'; }} />
                    ) : p.avatar_ref && p.avatar_ref.startsWith('emoji:') ? (
                      <span className="text-xl">{p.avatar_ref.split(':')[1]}</span>
                    ) : (
                      <span>{(p.naam || '?')[0]}</span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-sm font-semibold text-white">{p.naam}</h3>
                      {isMe && <span className="text-[10px] px-1.5 py-0.5 bg-amber-500/15 text-amber-400 rounded font-medium">JIJ</span>}
                      {p.is_bot && <span className="text-[10px] px-1.5 py-0.5 bg-slate-700 text-slate-400 rounded">BOT</span>}
                      <span className="text-[10px] text-slate-600">{p.gradatie_titel || `Gradatie ${p.gradatie}`}</span>
                    </div>
                    <div className="flex items-center gap-4 mt-1">
                      <span className="text-[10px] text-slate-500 flex items-center gap-1"><Star className="w-2.5 h-2.5 text-amber-400" /> {(p.xp || 0).toLocaleString()} XP</span>
                      <span className="text-[10px] text-slate-500 flex items-center gap-1"><BookOpen className="w-2.5 h-2.5 text-green-400" /> {p.words || 0} woorden</span>
                      <span className="text-[10px] text-slate-500 flex items-center gap-1"><Trophy className="w-2.5 h-2.5 text-purple-400" /> {p.achievements || 0} badges</span>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-lg font-bold text-white">Lvl {p.level || 0}</p>
                  </div>
                </div>
              );
            })}
            {sorted.length === 0 && !loading && (
              <p className="text-center text-xs text-slate-500 py-12">Nog geen gebruikers met activiteit in deze periode.</p>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  );
}

export default LeaderboardPage;
