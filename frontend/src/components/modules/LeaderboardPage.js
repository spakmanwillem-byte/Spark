import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Award, Trophy, Crown, Star, Medal, TrendingUp, Zap,
  BookOpen, Brain, Target, Flame
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const mockLeaderboard = [
  { rank: 1, naam: 'De Willem', xp: 26350, level: 263, achievements: 9, words: 2371, streak: 14, gradatie: 1 },
  { rank: 2, naam: 'Harry Klokkenmaker', xp: 8200, level: 82, achievements: 5, words: 820, streak: 7, gradatie: 4 },
  { rank: 3, naam: 'Madelief Stouten', xp: 5100, level: 51, achievements: 4, words: 510, streak: 3, gradatie: 7 },
  { rank: 4, naam: 'Mr Smith', xp: 2400, level: 24, achievements: 3, words: 240, streak: 1, gradatie: 3 },
];

const rankColors = ['#f59e0b', '#94a3b8', '#b45309'];
const rankIcons = [Crown, Medal, Medal];

export function LeaderboardPage({ onNavigate }) {
  const { user } = useAuth();
  const [period, setPeriod] = useState('alltime');
  const [sortBy, setSortBy] = useState('xp');

  const sorted = [...mockLeaderboard].sort((a, b) => b[sortBy] - a[sortBy]);

  return (
    <MainLayout activePage="leaderboard" onNavigate={onNavigate}>
      <div data-testid="leaderboard-page" className="p-4 md:p-6 space-y-5 max-w-4xl mx-auto">

        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
            <Award className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Leaderboard</h1>
            <p className="text-xs text-slate-500">Ranglijst van alle Spark Core gebruikers</p>
          </div>
        </div>

        {/* Top 3 Podium */}
        <div className="flex items-end justify-center gap-4 pt-4 pb-2">
          {[1, 0, 2].map(idx => {
            const p = sorted[idx];
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
                <p className="text-xs text-amber-400 font-medium">{p.xp.toLocaleString()} XP</p>
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-[10px] text-slate-500">Lvl {p.level}</span>
                  <span className="text-slate-700">|</span>
                  <span className="text-[10px] text-slate-500">{p.achievements} badges</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Sort options */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {[
            { id: 'xp', label: 'XP', icon: Star },
            { id: 'words', label: 'Woorden', icon: BookOpen },
            { id: 'achievements', label: 'Achievements', icon: Trophy },
            { id: 'streak', label: 'Streak', icon: Flame },
          ].map(s => (
            <button key={s.id} data-testid={`sort-${s.id}`} onClick={() => setSortBy(s.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex-shrink-0 ${sortBy === s.id ? 'bg-amber-500/15 text-amber-400' : 'bg-slate-800/50 text-slate-400 hover:text-white'}`}>
              <s.icon className="w-3.5 h-3.5" /> {s.label}
            </button>
          ))}
        </div>

        {/* Full rankings */}
        <div className="space-y-2">
          {sorted.map((p, i) => {
            const isMe = p.naam === (user?.naam || 'De Willem');
            return (
              <div key={i} data-testid={`rank-${i + 1}`}
                className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${isMe ? 'border-amber-500/30 bg-amber-500/5' : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ${i < 3 ? 'text-white' : 'text-slate-500 bg-slate-800'}`}
                  style={i < 3 ? { background: rankColors[i] } : {}}>
                  {i + 1}
                </div>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold flex-shrink-0"
                  style={{ background: `linear-gradient(135deg, ${['#f59e0b', '#3b82f6', '#22c55e', '#a855f7'][i % 4]}, ${['#ea580c', '#6366f1', '#10b981', '#ec4899'][i % 4]})` }}>
                  {p.naam[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-white">{p.naam}</h3>
                    {isMe && <span className="text-[10px] px-1.5 py-0.5 bg-amber-500/15 text-amber-400 rounded font-medium">JIJ</span>}
                    <span className="text-[10px] text-slate-600">Gradatie {p.gradatie}</span>
                  </div>
                  <div className="flex items-center gap-4 mt-1">
                    <span className="text-[10px] text-slate-500 flex items-center gap-1"><Star className="w-2.5 h-2.5 text-amber-400" /> {p.xp.toLocaleString()} XP</span>
                    <span className="text-[10px] text-slate-500 flex items-center gap-1"><BookOpen className="w-2.5 h-2.5 text-green-400" /> {p.words} woorden</span>
                    <span className="text-[10px] text-slate-500 flex items-center gap-1"><Trophy className="w-2.5 h-2.5 text-purple-400" /> {p.achievements} badges</span>
                    <span className="text-[10px] text-slate-500 flex items-center gap-1"><Flame className="w-2.5 h-2.5 text-orange-400" /> {p.streak}d streak</span>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-lg font-bold text-white">Lvl {p.level}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </MainLayout>
  );
}

export default LeaderboardPage;
