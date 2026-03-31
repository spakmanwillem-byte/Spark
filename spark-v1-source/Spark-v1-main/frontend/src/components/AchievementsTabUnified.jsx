import React, { useState, useEffect } from 'react';
import { Award, Trophy, Star, Lock, TrendingUp, Coins, BookOpen } from 'lucide-react';

const AchievementsTabUnified = ({ userData }) => {
  const [knowledgeData, setKnowledgeData] = useState(null);
  const [allKnowledgeAchievements, setAllKnowledgeAchievements] = useState([]);
  const [financialData, setFinancialData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL;
  const userId = userData?.id;

  useEffect(() => {
    if (userId) {
      fetchAllAchievements();
    }
  }, [userId]);

  const fetchAllAchievements = async () => {
    console.log('🏆 [Achievements] Fetching for userId:', userId);
    
    try {
      setLoading(true);
      
      // Fetch all achievement types in parallel
      const [knowledgeUserResponse, allAchievementsResponse, financialResponse] = await Promise.all([
        fetch(`${API_URL}/api/admin/achievements/${userId}`),
        fetch(`${API_URL}/api/admin/achievements`),
        fetch(`${API_URL}/api/central/wallet/${userId}`)
      ]);
      
      const knowledgeJson = await knowledgeUserResponse.json();
      const allAchievementsJson = await allAchievementsResponse.json();
      const financialJson = await financialResponse.json();
      
      console.log('📚 [Knowledge User Data]:', knowledgeJson);
      console.log('📚 [All Achievements]:', allAchievementsJson);
      console.log('💰 [Financial Achievements]:', financialJson);
      
      if (knowledgeJson.success) {
        setKnowledgeData(knowledgeJson);
      }
      
      if (allAchievementsJson.achievements) {
        setAllKnowledgeAchievements(allAchievementsJson.achievements);
      }
      
      if (financialJson.success) {
        setFinancialData(financialJson.achievements);
      }
      
    } catch (err) {
      console.error('❌ [Achievements] Error:', err);
      setError('Fout bij ophalen achievements: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Laden...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 m-4">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  // Knowledge data
  const unlockedKnowledge = knowledgeData?.unlocked || [];
  const totalUnlocked = knowledgeData?.total_unlocked || 0;
  const totalAchievements = knowledgeData?.total_achievements || 13;
  const progressPercentage = knowledgeData?.progress_percentage || 0;
  const totalContributions = knowledgeData?.total_contributions || 0;
  const totalXpFromAchievements = knowledgeData?.total_xp_earned || 0;
  const nextMilestone = knowledgeData?.next_milestone;

  // Financial data
  const financialAchievements = financialData || {};
  const unlockedFinancial = financialAchievements.unlocked || [];
  const totalTokensBought = financialAchievements.total_tokens_bought || 0;

  // Financial achievement definitions
  const financialDefs = {
    'Community Supporter': {
      icon: '🤝',
      description: 'Kocht je eerste ROARR token',
      threshold: 1,
      color: 'from-blue-500 to-cyan-500'
    },
    'Core Supporter': {
      icon: '⭐',
      description: 'Kocht 5 ROARR tokens',
      threshold: 5,
      color: 'from-purple-500 to-pink-500'
    },
    'ROARR Builder': {
      icon: '🏆',
      description: 'Kocht 10 ROARR tokens',
      threshold: 10,
      color: 'from-yellow-500 to-orange-500'
    }
  };

  return (
    <div className="p-6 space-y-8">
      {/* =========================== */}
      {/* MAIN HEADER */}
      {/* =========================== */}
      <div className="bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30 p-6 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <Trophy className="w-8 h-8 text-yellow-500" />
              Community & Spel Achievements
            </h2>
            <p className="text-gray-300 mt-2">
              👤 {userData?.naam} - Jouw voortgang en bijdragen
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-white">{totalUnlocked + unlockedFinancial.length}</div>
            <div className="text-sm text-gray-400">Totaal Ontgrendeld</div>
          </div>
        </div>
      </div>

      {/* =========================== */}
      {/* SECTIE 1: KNOWLEDGE & SPEL */}
      {/* =========================== */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 border-b border-purple-500/30 pb-3">
          <BookOpen className="w-6 h-6 text-purple-400" />
          <h3 className="text-2xl font-bold text-white">📚 Knowledge & Spel</h3>
        </div>

        {/* Stats Banner */}
        <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 p-6 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-white">{totalContributions}</div>
              <div className="text-sm text-gray-400 mt-1">📝 Woorden Geleerd</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-400">{totalXpFromAchievements}</div>
              <div className="text-sm text-gray-400 mt-1">⭐ XP Verdiend</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-pink-400">{totalUnlocked}/{totalAchievements}</div>
              <div className="text-sm text-gray-400 mt-1">🏆 Achievements ({progressPercentage}%)</div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
              <div
                className="h-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        </div>

        {/* Next Milestone */}
        {nextMilestone && (
          <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 p-4 rounded-lg">
            <div className="flex items-center gap-4">
              <span className="text-5xl">{nextMilestone.icon}</span>
              <div className="flex-1">
                <h4 className="text-white font-bold text-lg">{nextMilestone.name}</h4>
                <p className="text-sm text-gray-300">{nextMilestone.description}</p>
                <div className="mt-3">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-400">Voortgang</span>
                    <span className="text-yellow-300 font-semibold">
                      {nextMilestone.current_progress} / {nextMilestone.milestone} woorden
                    </span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-2 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full transition-all duration-500"
                      style={{ width: `${(nextMilestone.current_progress / nextMilestone.milestone) * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Nog {nextMilestone.remaining} woorden → +{nextMilestone.xp_reward} XP 🎉
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Knowledge Achievements Grid */}
        <div>
          <h4 className="text-lg font-semibold text-white mb-4">
            Alle Spel Achievements ({totalUnlocked}/{totalAchievements})
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allKnowledgeAchievements.map(ach => {
              const unlockedIds = unlockedKnowledge.map(u => u.id);
              const isUnlocked = unlockedIds.includes(ach.id);
              const unlockedData = unlockedKnowledge.find(u => u.id === ach.id);
              
              return (
                <div
                  key={ach.id}
                  className={`p-5 rounded-lg border-2 transition-all ${
                    isUnlocked
                      ? "bg-gradient-to-br from-purple-500/20 to-pink-500/20 border-purple-500/50 hover:border-purple-400/70"
                      : "bg-slate-800/30 border-slate-600/30 opacity-60 grayscale"
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-4xl">{ach.icon}</span>
                    {isUnlocked && (
                      <span className="text-green-400 text-sm font-bold">✓ Unlocked</span>
                    )}
                    {!isUnlocked && (
                      <span className="text-gray-500 text-sm">🔒 Locked</span>
                    )}
                  </div>
                  <h4 className={`font-bold text-lg ${isUnlocked ? 'text-white' : 'text-gray-400'}`}>
                    {ach.name}
                  </h4>
                  <p className={`text-sm mt-1 ${isUnlocked ? 'text-gray-300' : 'text-gray-500'}`}>
                    {ach.description}
                  </p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className={`text-xs px-2 py-1 rounded ${
                      isUnlocked ? 'bg-purple-500/30 text-purple-200' : 'bg-gray-700/30 text-gray-500'
                    }`}>
                      {ach.milestone} woorden
                    </span>
                    <span className={`font-bold ${isUnlocked ? 'text-purple-300' : 'text-gray-500'}`}>
                      +{ach.xp_reward} XP
                    </span>
                  </div>
                  {isUnlocked && unlockedData && (
                    <p className="text-xs text-gray-500 mt-2">
                      {new Date(unlockedData.unlocked_at).toLocaleDateString('nl-NL')}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* =========================== */}
      {/* SECTIE 2: COMMUNITY & ROARR */}
      {/* =========================== */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 border-b border-blue-500/30 pb-3">
          <Coins className="w-6 h-6 text-blue-400" />
          <h3 className="text-2xl font-bold text-white">💰 Community & ROARR Tokens</h3>
        </div>

        {/* Token Stats */}
        <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 p-6 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-white font-bold text-lg">ROARR Token Aankopen</h4>
              <p className="text-gray-400 text-sm mt-1">
                {unlockedFinancial.length} van {Object.keys(financialDefs).length} achievements ontgrendeld
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-blue-400">{totalTokensBought.toFixed(1)}</div>
              <div className="text-xs text-gray-400">Tokens Gekocht</div>
            </div>
          </div>
        </div>

        {/* Financial Achievements */}
        <div className="grid gap-4">
          {Object.entries(financialDefs).map(([name, def]) => {
            const isUnlocked = unlockedFinancial.includes(name);
            const progress = Math.min((totalTokensBought / def.threshold) * 100, 100);

            return (
              <div
                key={name}
                className={`
                  relative overflow-hidden rounded-lg border transition-all
                  ${isUnlocked 
                    ? 'bg-gradient-to-r ' + def.color + ' bg-opacity-10 border-opacity-50' 
                    : 'bg-gray-800/30 border-gray-700'
                  }
                `}
              >
                {/* Progress bar (if not unlocked) */}
                {!isUnlocked && (
                  <div 
                    className="absolute inset-0 bg-gradient-to-r from-gray-700/20 to-transparent"
                    style={{ width: `${progress}%` }}
                  />
                )}

                <div className="relative p-4 flex items-center gap-4">
                  {/* Icon */}
                  <div className={`
                    text-4xl flex-shrink-0 
                    ${isUnlocked ? 'filter-none' : 'grayscale opacity-40'}
                  `}>
                    {def.icon}
                  </div>

                  {/* Content */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className={`font-bold ${isUnlocked ? 'text-white' : 'text-gray-400'}`}>
                        {name}
                      </h3>
                      {isUnlocked && (
                        <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                      )}
                      {!isUnlocked && (
                        <Lock className="w-4 h-4 text-gray-500" />
                      )}
                    </div>
                    <p className={`text-sm mt-1 ${isUnlocked ? 'text-gray-300' : 'text-gray-500'}`}>
                      {def.description}
                    </p>

                    {/* Progress info (if not unlocked) */}
                    {!isUnlocked && (
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all"
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 min-w-[60px]">
                          {totalTokensBought.toFixed(1)} / {def.threshold}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Status Badge */}
                  {isUnlocked && (
                    <div className="px-3 py-1 bg-green-500/20 border border-green-500/30 rounded-full">
                      <span className="text-xs font-medium text-green-400">Ontgrendeld</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Info Box */}
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <TrendingUp className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-300">
              <strong>Hoe werkt het?</strong>
              <p className="text-blue-400/80 mt-1">
                Koop ROARR tokens in de <strong>Winkel</strong> tab om Community achievements te ontgrendelen. 
                Leer Spark nieuwe woorden via gesprekken om Spel achievements te unlocken!
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AchievementsTabUnified;
