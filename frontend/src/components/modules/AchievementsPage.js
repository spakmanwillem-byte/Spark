import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Trophy, Star, Lock, Sparkles, Target, Zap, Crown,
  ChevronRight, Award, TrendingUp, BookOpen
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const rarityConfig = {
  common:    { label: 'Common',    bg: '#475569', ring: '#64748b', glow: '' },
  uncommon:  { label: 'Uncommon',  bg: '#166534', ring: '#22c55e', glow: '0 0 12px rgba(34,197,94,0.3)' },
  rare:      { label: 'Rare',      bg: '#1e3a5f', ring: '#3b82f6', glow: '0 0 12px rgba(59,130,246,0.3)' },
  epic:      { label: 'Epic',      bg: '#581c87', ring: '#a855f7', glow: '0 0 16px rgba(168,85,247,0.4)' },
  legendary: { label: 'Legendary', bg: '#78350f', ring: '#f59e0b', glow: '0 0 20px rgba(245,158,11,0.4)' },
  mythic:    { label: 'Mythic',    bg: '#831843', ring: '#ec4899', glow: '0 0 24px rgba(236,72,153,0.5)' },
};

export function AchievementsPage({ onNavigate }) {
  const { user } = useAuth();
  const [allAch, setAllAch] = useState([]);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const userId = user?.id || 'user-001';
    Promise.all([
      fetch(`${API}/api/achievements/all`).then(r => r.json()),
      fetch(`${API}/api/achievements/progress/${userId}`).then(r => r.json()),
    ]).then(([all, prog]) => {
      setAllAch(all.achievements || []);
      setProgress(prog);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [user]);

  if (loading) {
    return (
      <MainLayout activePage="achievements" onNavigate={onNavigate}>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="w-8 h-8 border-3 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
        </div>
      </MainLayout>
    );
  }

  const unlocked = progress?.unlocked || [];
  const unlockedIds = unlocked.map(a => a.id);
  const totalUnlocked = progress?.total_unlocked || 0;
  const totalAch = progress?.total_achievements || 13;
  const pct = progress?.progress_percentage || 0;
  const totalXp = progress?.total_xp_earned || 0;
  const wordCount = progress?.word_count || 0;
  const nextMilestone = progress?.next_milestone;
  const userName = progress?.user_naam || user?.naam || 'User';

  return (
    <MainLayout activePage="achievements" onNavigate={onNavigate}>
      <div data-testid="achievements-page" className="p-4 md:p-6 space-y-5 max-w-6xl mx-auto">

        {/* Profile Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-amber-500/20" style={{ background: 'linear-gradient(135deg, #1a1333 0%, #0f172a 50%, #1a1333 100%)' }}>
          <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 20% 50%, #f59e0b 0%, transparent 50%), radial-gradient(circle at 80% 50%, #a855f7 0%, transparent 50%)' }} />
          <div className="relative p-6 flex flex-col md:flex-row items-center gap-6">
            {/* Avatar */}
            <div className="relative">
              <div className="w-20 h-20 rounded-2xl flex items-center justify-center text-3xl font-bold text-white" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
                {userName[0]}
              </div>
              <div className="absolute -bottom-1 -right-1 w-7 h-7 rounded-lg bg-amber-500 flex items-center justify-center text-[10px] font-bold text-white border-2 border-slate-900">
                {Math.floor(totalXp / 100)}
              </div>
            </div>
            {/* Stats */}
            <div className="flex-1 text-center md:text-left">
              <h2 className="text-xl font-bold text-white">{userName}</h2>
              <div className="flex flex-wrap justify-center md:justify-start gap-4 mt-2">
                <StatChip icon={BookOpen} value={wordCount.toLocaleString()} label="woorden" color="#f59e0b" />
                <StatChip icon={Star} value={totalXp.toLocaleString()} label="XP" color="#a855f7" />
                <StatChip icon={Trophy} value={`${totalUnlocked}/${totalAch}`} label="achievements" color="#22c55e" />
              </div>
              {/* Progress bar */}
              <div className="mt-4 max-w-md">
                <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                  <span>Achievement Voortgang</span>
                  <span className="text-amber-400 font-medium">{pct}%</span>
                </div>
                <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${pct}%`, background: 'linear-gradient(90deg, #f59e0b, #a855f7, #ec4899)' }} />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Next Milestone */}
        {nextMilestone && (
          <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-500/5">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl flex-shrink-0" style={{ background: `${rarityConfig[nextMilestone.rarity]?.ring || '#f59e0b'}15`, border: `2px solid ${rarityConfig[nextMilestone.rarity]?.ring || '#f59e0b'}40` }}>
                {nextMilestone.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-xs text-amber-400 font-medium uppercase tracking-wider">Volgende Milestone</span>
                </div>
                <h3 className="text-sm font-bold text-white">{nextMilestone.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{nextMilestone.description}</p>
                <div className="mt-2">
                  <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                    <span>{nextMilestone.current_progress} / {nextMilestone.milestone} woorden</span>
                    <span className="text-amber-400">nog {nextMilestone.remaining} te gaan → +{nextMilestone.xp_reward.toLocaleString()} XP</span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${(nextMilestone.current_progress / nextMilestone.milestone) * 100}%`, background: 'linear-gradient(90deg, #f59e0b, #ea580c)' }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Unlocked */}
        {unlocked.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <CheckMark /> Behaald ({unlocked.length})
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {unlocked.map(ach => (
                <AchievementCard key={ach.id} ach={ach} unlocked />
              ))}
            </div>
          </div>
        )}

        {/* All Achievements */}
        <div>
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Trophy className="w-4 h-4 text-amber-400" /> Alle Achievements ({totalUnlocked}/{totalAch})
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {allAch.map(ach => {
              const isUnlocked = unlockedIds.includes(ach.id);
              const userAch = unlocked.find(u => u.id === ach.id);
              return (
                <AchievementCard key={ach.id} ach={userAch || ach} unlocked={isUnlocked} />
              );
            })}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

function AchievementCard({ ach, unlocked }) {
  const rarity = rarityConfig[ach.rarity] || rarityConfig.common;
  return (
    <div
      data-testid={`achievement-${ach.id}`}
      className={`p-4 rounded-xl border-2 transition-all ${unlocked ? 'hover:scale-[1.02]' : 'opacity-40 grayscale'}`}
      style={{
        background: unlocked ? `${rarity.bg}30` : '#0f172a',
        borderColor: unlocked ? `${rarity.ring}50` : '#1e293b',
        boxShadow: unlocked ? rarity.glow : 'none',
      }}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-3xl">{ach.icon}</span>
        {unlocked ? (
          <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-green-500/15 text-green-400">Behaald</span>
        ) : (
          <Lock className="w-4 h-4 text-slate-600" />
        )}
      </div>
      <h4 className="text-sm font-bold text-white mb-0.5">{ach.name}</h4>
      <p className="text-[11px] text-slate-400 leading-relaxed">{ach.description}</p>
      <div className="mt-3 flex items-center justify-between">
        <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: `${rarity.ring}20`, color: rarity.ring }}>
          {rarity.label}
        </span>
        <div className="flex items-center gap-1">
          <span className="text-[10px] text-slate-500">{ach.milestone?.toLocaleString()} woorden</span>
          <span className="text-slate-700 mx-1">|</span>
          <span className="text-[10px] font-medium" style={{ color: rarity.ring }}>+{ach.xp_reward?.toLocaleString()} XP</span>
        </div>
      </div>
      {unlocked && ach.unlocked_at && (
        <p className="text-[10px] text-slate-600 mt-2">
          {new Date(ach.unlocked_at).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' })}
        </p>
      )}
    </div>
  );
}

function StatChip({ icon: Icon, value, label, color }) {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg" style={{ background: `${color}10` }}>
      <Icon className="w-3.5 h-3.5" style={{ color }} />
      <span className="text-sm font-bold text-white">{value}</span>
      <span className="text-[10px] text-slate-400">{label}</span>
    </div>
  );
}

function CheckMark() {
  return (
    <div className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center">
      <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    </div>
  );
}

export default AchievementsPage;
