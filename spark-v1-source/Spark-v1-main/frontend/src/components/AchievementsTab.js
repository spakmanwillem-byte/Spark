import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AchievementsTab({ userId, isAdmin, userName }) {
  const [allAchievements, setAllAchievements] = useState([]);
  const [userProgress, setUserProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [userId]);

  const fetchData = async () => {
    try {
      const [allAchResponse, userProgressResponse] = await Promise.all([
        axios.get(`${API}/admin/achievements`),
        axios.get(`${API}/admin/achievements/${userId}`)
      ]);
      
      setAllAchievements(allAchResponse.data.achievements || []);
      setUserProgress(userProgressResponse.data);
    } catch (error) {
      console.error("Error fetching achievements:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-purple-400">Laden...</div>;
  }

  const unlockedIds = (userProgress?.unlocked || []).map(a => a.id);
  const unlockedAchievements = userProgress?.unlocked || [];
  const totalUnlocked = userProgress?.total_unlocked || 0;
  const totalAchievements = userProgress?.total_achievements || 13;
  const progressPercentage = userProgress?.progress_percentage || 0;
  const currentWordCount = userProgress?.current_word_count || 0;
  const nextMilestone = userProgress?.next_milestone;
  const totalXpFromAchievements = userProgress?.total_xp_earned || 0;

  return (
    <div className="space-y-6">
      {/* User Profile Banner with Stats */}
      <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 p-6 rounded-lg">
        <div className="flex items-center gap-4">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-3xl relative">
            👤
            <div className="absolute inset-0 rounded-full border-4 border-purple-400 animate-pulse"></div>
          </div>
          <div className="flex-1">
            <h3 className="text-2xl font-bold text-white">{userName}</h3>
            <div className="mt-2 space-y-2">
              <div className="flex items-center gap-4 text-sm">
                <span className="text-gray-300">📚 {currentWordCount} woorden geleerd</span>
                <span className="text-purple-300">⭐ {totalXpFromAchievements} XP</span>
              </div>
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-300">Achievement Progress</span>
                  <span className="text-purple-300">{totalUnlocked}/{totalAchievements} ({progressPercentage}%)</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                  <div
                    className="h-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500"
                    style={{ width: `${progressPercentage}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Next Milestone */}
      {nextMilestone && (
        <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <span className="text-4xl">{nextMilestone.icon}</span>
            <div className="flex-1">
              <h4 className="text-white font-bold">{nextMilestone.name}</h4>
              <p className="text-sm text-gray-300">{nextMilestone.description}</p>
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-gray-400">Progress</span>
                  <span className="text-yellow-300">{nextMilestone.remaining} woorden remaining</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-2 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full transition-all duration-500"
                    style={{ width: `${(nextMilestone.current_progress / nextMilestone.milestone) * 100}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  {nextMilestone.current_progress} / {nextMilestone.milestone} woorden → +{nextMilestone.xp_reward} XP
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Unlocked Achievements */}
      {unlockedAchievements.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">✅ Unlocked Achievements ({unlockedAchievements.length})</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {unlockedAchievements.map(ach => (
              <div
                key={ach.id}
                className="p-5 rounded-lg border-2 bg-gradient-to-br from-purple-500/20 to-pink-500/20 border-purple-500/50 hover:border-purple-400/70 transition-all"
              >
                <div className="flex items-start justify-between mb-2">
                  <span className="text-4xl">{ach.icon}</span>
                  <span className="text-green-400 text-sm font-bold">✓ Unlocked</span>
                </div>
                <h4 className="text-white font-bold text-lg">{ach.name}</h4>
                <p className="text-sm text-gray-300 mt-1">{ach.description}</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs px-2 py-1 bg-purple-500/30 rounded text-purple-200">{ach.rarity}</span>
                  <span className="text-purple-300 font-bold">+{ach.xp_reward} XP</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {new Date(ach.unlocked_at).toLocaleDateString('nl-NL')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Achievements */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          🏆 Alle Achievements ({totalUnlocked}/{totalAchievements})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {allAchievements.map(ach => {
            const unlocked = unlockedIds.includes(ach.id);
            return (
              <div
                key={ach.id}
                className={`p-5 rounded-lg border-2 transition-all ${
                  unlocked
                    ? "bg-gradient-to-br from-purple-500/20 to-pink-500/20 border-purple-500/50"
                    : "bg-slate-800/30 border-slate-600/30 opacity-60 grayscale"
                }`}
              >
                <div className="text-4xl mb-2">{ach.icon}</div>
                <h4 className="text-white font-bold">{ach.name}</h4>
                <p className="text-sm text-gray-400 mt-1">{ach.description}</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-gray-400">{ach.milestone} woorden</span>
                  <span className="text-xs text-purple-300">+{ach.xp_reward} XP</span>
                </div>
                {unlocked && (
                  <div className="mt-2">
                    <span className="text-green-400 text-sm">✓ Unlocked</span>
                  </div>
                )}
                {!unlocked && (
                  <div className="mt-2">
                    <span className="text-gray-500 text-xs">🔒 Locked</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default AchievementsTab;
