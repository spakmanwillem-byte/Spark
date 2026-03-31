import React, { useState, useEffect } from 'react';
import { Award, Trophy, Star, Lock } from 'lucide-react';

const AchievementsTab = ({ userId }) => {
  const [achievements, setAchievements] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (userId) {
      fetchAchievements();
    }
  }, [userId]);

  const fetchAchievements = async () => {
    console.log('🏆 [AchievementsTab] Fetching for userId:', userId);
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/central/wallet/${userId}`);
      const data = await response.json();
      
      console.log('🏆 [AchievementsTab] API response:', data);
      console.log('🏆 [AchievementsTab] Achievements data:', data.achievements);
      
      if (data.success) {
        setAchievements(data.achievements);
        console.log('✅ [AchievementsTab] Achievements set:', data.achievements);
      } else {
        setError('Kon achievements niet laden');
      }
    } catch (err) {
      console.error('❌ [AchievementsTab] Error:', err);
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

  if (!achievements) {
    return (
      <div className="text-center text-gray-400 p-8">
        Geen achievement data beschikbaar
      </div>
    );
  }

  // Achievement definitions
  const achievementDefs = {
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

  const unlocked = achievements.unlocked || [];
  const totalBought = achievements.total_tokens_bought || 0;
  
  console.log('🏆 [AchievementsTab] Rendering with:', {unlocked, totalBought});

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Trophy className="w-6 h-6 text-yellow-500" />
            Achievements
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            {unlocked.length} van {Object.keys(achievementDefs).length} ontgrendeld
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-white">{totalBought.toFixed(1)}</div>
          <div className="text-xs text-gray-400">Tokens gekocht</div>
        </div>
      </div>

      {/* Achievement List */}
      <div className="grid gap-4">
        {Object.entries(achievementDefs).map(([name, def]) => {
          const isUnlocked = unlocked.includes(name);
          const progress = Math.min((totalBought / def.threshold) * 100, 100);

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
                        {totalBought.toFixed(1)} / {def.threshold}
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

      {/* Info */}
      <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Award className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-300">
            <strong>Hoe werkt het?</strong>
            <p className="text-blue-400/80 mt-1">
              Koop ROARR tokens in de Winkel tab om achievements te ontgrendelen. 
              Je voortgang wordt automatisch bijgewerkt bij elke aankoop.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AchievementsTab;
