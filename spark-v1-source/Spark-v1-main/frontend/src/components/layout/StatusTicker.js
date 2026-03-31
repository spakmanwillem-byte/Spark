import React from 'react';

// Rank system based on XP
const getRank = (xp) => {
  if (xp >= 50000) return { name: 'Master', icon: '👑', color: '#FFD700' };
  if (xp >= 20000) return { name: 'Expert', icon: '🎓', color: '#9C27B0' };
  if (xp >= 10000) return { name: 'Scholar', icon: '📚', color: '#2196F3' };
  if (xp >= 5000) return { name: 'Explorer', icon: '🗺️', color: '#4CAF50' };
  if (xp >= 2000) return { name: 'Learner', icon: '🌱', color: '#8BC34A' };
  if (xp >= 500) return { name: 'Beginner', icon: '✨', color: '#FFC107' };
  return { name: 'Novice', icon: '🔰', color: '#9E9E9E' };
};

const StatusTicker = ({ userData, sessionDuration, systemStatus, knowledgeCount, sparkEmotion }) => {
  const rank = userData ? getRank(userData.xp || 0) : null;
  
  // Emotie icon mapping
  const emotionIcons = {
    happy: '😊',
    sad: '😢',
    angry: '😠',
    scared: '😰',
    neutral: '😐',
    excited: '🤩',
    curious: '🤔',
    proud: '😌'
  };
  
  return (
    <div className="status-ticker">
      <div className="ticker-content">
        {userData && (
          <>
            {/* User Name */}
            <div className="ticker-item">
              <span className="ticker-icon">👤</span>
              <span className="ticker-text">{userData.naam}</span>
            </div>
            
            <div className="ticker-divider"></div>
            
            {/* XP with actual number */}
            <div className="ticker-item">
              <span className="ticker-icon">⭐</span>
              <span className="ticker-text">{userData.xp || 0} XP</span>
            </div>
            
            <div className="ticker-divider"></div>
            
            {/* Credits */}
            <div className="ticker-item">
              <span className="ticker-icon">💰</span>
              <span className="ticker-text">{userData.credits || 0} Credits</span>
            </div>
            
            <div className="ticker-divider"></div>
            
            {/* Rank/Title */}
            <div className="ticker-item">
              <span className="ticker-icon">{rank.icon}</span>
              <span className="ticker-text" style={{ color: rank.color, fontWeight: 600 }}>
                Rank {rank.name}
              </span>
            </div>
            
            <div className="ticker-divider"></div>
            
            {/* Achievements Count */}
            <div className="ticker-item">
              <span className="ticker-icon">🏆</span>
              <span className="ticker-text">
                {userData.achievements?.unlocked?.length || 0} Achievements
              </span>
            </div>
            
            <div className="ticker-divider"></div>
            
            {/* Gradatie */}
            <div className="ticker-item">
              <span className="ticker-icon">👥</span>
              <span className="ticker-text">
                Gradatie {userData.gradatie}
              </span>
            </div>
            
            <div className="ticker-divider"></div>
            
            {/* Knowledge Count */}
            <div className="ticker-item">
              <span className="ticker-icon">🧠</span>
              <span className="ticker-text">
                {knowledgeCount || userData.achievements?.progress?.word_count || 0} Knowledge
              </span>
            </div>
            
            {sparkEmotion && (
              <>
                <div className="ticker-divider"></div>
                
                {/* Spark's Current Emotion */}
                <div className="ticker-item" title={`Intensity: ${Math.round((sparkEmotion.intensity || 0.5) * 100)}%`}>
                  <span className="ticker-icon">{emotionIcons[sparkEmotion.state] || '😐'}</span>
                  <span className="ticker-text" style={{ fontStyle: 'italic', opacity: 0.9 }}>
                    Spark: {sparkEmotion.state}
                    {sparkEmotion.sub_state && ` (${sparkEmotion.sub_state})`}
                  </span>
                </div>
              </>
            )}
          </>
        )}
        
        {!userData && (
          <div className="ticker-item">
            <span className="ticker-icon">👋</span>
            <span className="ticker-text">Niet ingelogd - Stel jezelf voor aan Spark</span>
          </div>
        )}
        
        <div className="ticker-spacer"></div>
        
        {/* Spark Core Status - more alive! */}
        <div className="ticker-item spark-core-status">
          <span className={`status-indicator ${systemStatus === 'online' ? 'online' : 'offline'}`}></span>
          <span className="ticker-text">
            {systemStatus === 'online' ? 'Spark Core Online' : 'Spark Core Offline'}
          </span>
        </div>
        
        {sessionDuration && (
          <>
            <div className="ticker-divider"></div>
            <div className="ticker-item">
              <span className="ticker-icon">⏱️</span>
              <span className="ticker-text">{sessionDuration}</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default StatusTicker;
