import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LeaderboardTab = ({ userData }) => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [userRank, setUserRank] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLeaderboard();
  }, [userData]);

  const loadLeaderboard = async () => {
    try {
      const response = await axios.get(`${API}/leaderboard/top`);
      setLeaderboard(response.data.leaderboard || []);
      
      if (userData?.id) {
        const rankResponse = await axios.get(`${API}/leaderboard/rank/${userData.id}`);
        setUserRank(rankResponse.data);
      }
    } catch (error) {
      console.error('Error loading leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankColor = (rank) => {
    if (rank === 1) return 'from-yellow-500 to-yellow-600';
    if (rank === 2) return 'from-gray-400 to-gray-500';
    if (rank === 3) return 'from-orange-600 to-orange-700';
    return 'from-purple-500 to-purple-600';
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return '🏅';
  };

  if (loading) {
    return <div className="text-white p-6">Laden...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border border-yellow-500/30 p-6 rounded-lg">
        <h2 className="text-3xl font-bold text-white mb-2">🏆 Leaderboard</h2>
        <p className="text-gray-300">
          Top contributors die Spark helpen leren
        </p>
      </div>

      {/* User's Rank Card */}
      {userRank && userRank.rank && (
        <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 p-6 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-400 mb-1">Jouw Ranking</div>
              <div className="text-4xl font-bold text-white">
                #{userRank.rank}
              </div>
              <div className="text-sm text-gray-400 mt-1">
                van {userRank.total_users} gebruikers
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-400 mb-1">Woorden geleerd</div>
              <div className="text-3xl font-bold text-purple-400">
                {userRank.word_count}
              </div>
              <div className="text-sm text-gray-400 mt-1">
                Top {userRank.percentile}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Leaderboard Table */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
        <div className="bg-slate-700/50 px-6 py-4 border-b border-slate-600">
          <h3 className="text-xl font-bold text-white">Top 10 Contributors</h3>
        </div>

        <div className="divide-y divide-slate-700">
          {leaderboard.map((entry, idx) => {
            const isCurrentUser = userData?.id === entry.user_id;
            
            return (
              <div 
                key={entry.user_id}
                className={`px-6 py-4 flex items-center gap-4 ${
                  isCurrentUser ? 'bg-purple-500/10' : 'hover:bg-slate-700/30'
                }`}
              >
                {/* Rank */}
                <div className="w-16 flex items-center justify-center">
                  {entry.rank <= 3 ? (
                    <div className={`
                      w-12 h-12 rounded-full bg-gradient-to-br ${getRankColor(entry.rank)}
                      flex items-center justify-center text-2xl shadow-lg
                    `}>
                      {getRankIcon(entry.rank)}
                    </div>
                  ) : (
                    <div className="text-2xl font-bold text-gray-400">
                      #{entry.rank}
                    </div>
                  )}
                </div>

                {/* User Info */}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-semibold text-white">
                      {entry.naam}
                    </span>
                    {isCurrentUser && (
                      <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 text-xs rounded-full">
                        Jij
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-400 flex gap-3">
                    <span>⚔️ Level {entry.leven || 0}</span>
                    <span>🏆 Rank {entry.user_rank || 0}</span>
                  </div>
                </div>

                {/* Stats */}
                <div className="text-right">
                  <div className="text-2xl font-bold text-white">
                    {entry.word_count}
                  </div>
                  <div className="text-xs text-gray-400">woorden</div>
                </div>

                <div className="text-right hidden md:block">
                  <div className="text-lg font-semibold text-purple-400">
                    {entry.xp}
                  </div>
                  <div className="text-xs text-gray-400">XP</div>
                </div>

                <div className="text-right hidden md:block">
                  <div className="text-lg font-semibold text-yellow-400">
                    {entry.achievements_count}
                  </div>
                  <div className="text-xs text-gray-400">achievements</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Motivational Message */}
      {userRank && userRank.rank > 10 && (
        <div className="bg-blue-500/10 border border-blue-500/30 p-4 rounded-lg text-center">
          <p className="text-blue-300">
            💪 Blijf woorden toevoegen om hoger te klimmen in de leaderboard!
          </p>
        </div>
      )}
    </div>
  );
};

export default LeaderboardTab;
