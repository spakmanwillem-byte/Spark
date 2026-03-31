import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EmotionStatsTab = ({ userId }) => {
  const [summary, setSummary] = useState(null);
  const [patterns, setPatterns] = useState([]);
  const [recentEvents, setRecentEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (userId) {
      loadEmotionData();
    }
  }, [userId]);

  const loadEmotionData = async () => {
    try {
      const [summaryRes, patternsRes, historyRes] = await Promise.all([
        axios.get(`${API}/emotions/summary/${userId}`),
        axios.get(`${API}/emotions/patterns/${userId}`),
        axios.get(`${API}/emotions/history/${userId}?limit=20`)
      ]);

      setSummary(summaryRes.data);
      setPatterns(patternsRes.data.patterns || []);
      setRecentEvents(historyRes.data.events || []);
    } catch (error) {
      console.error('Error loading emotion data:', error);
    } finally {
      setLoading(false);
    }
  };

  const emotionColors = {
    blij: '#4CAF50',
    boos: '#F44336',
    bang: '#FFC107',
    bedroefd: '#2196F3'
  };

  const emotionIcons = {
    blij: '😊',
    boos: '😠',
    bang: '😰',
    bedroefd: '😢'
  };

  if (loading) {
    return <div className="text-white p-6">Laden...</div>;
  }

  if (!summary) {
    return <div className="text-white p-6">Nog geen emotie data beschikbaar</div>;
  }

  const totalEvents = summary.summary?.total_events || 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 p-6 rounded-lg">
        <h2 className="text-3xl font-bold text-white mb-2">📊 Emotie Statistieken</h2>
        <p className="text-gray-300">
          Inzicht in jouw emotionele patronen en triggers
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {Object.entries(summary.summary?.emotions || {}).map(([emotion, count]) => {
          const percentage = totalEvents > 0 ? ((count / totalEvents) * 100).toFixed(1) : 0;
          
          return (
            <div 
              key={emotion}
              className="bg-slate-800 border border-slate-700 p-4 rounded-lg"
              style={{ borderLeft: `4px solid ${emotionColors[emotion]}` }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-3xl">{emotionIcons[emotion]}</span>
                <span className="text-2xl font-bold text-white">{count}</span>
              </div>
              <div className="text-sm text-gray-400 capitalize mb-1">{emotion}</div>
              <div className="text-xs text-gray-500">{percentage}% van totaal</div>
              
              {summary.averages?.[emotion] && (
                <div className="mt-2 text-xs text-gray-400">
                  Ø score: {summary.averages[emotion].average}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Emotion Patterns */}
      {patterns.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
          <h3 className="text-xl font-bold text-white mb-4">
            🎯 Emotie Patronen per Topic
          </h3>
          <p className="text-sm text-gray-400 mb-4">
            Welke emoties voel je bij bepaalde onderwerpen?
          </p>

          <div className="space-y-3">
            {patterns.slice(0, 10).map((pattern, idx) => (
              <div 
                key={idx}
                className="bg-slate-700/50 p-4 rounded-lg"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{emotionIcons[pattern.dominant_emotion]}</span>
                    <div>
                      <div className="text-white font-medium">{pattern.topic}</div>
                      <div className="text-xs text-gray-400">
                        {pattern.total_mentions} keer genoemd
                      </div>
                    </div>
                  </div>
                  <div 
                    className="px-3 py-1 rounded-full text-sm font-medium"
                    style={{ 
                      backgroundColor: `${emotionColors[pattern.dominant_emotion]}20`,
                      color: emotionColors[pattern.dominant_emotion]
                    }}
                  >
                    {pattern.dominant_emotion} ({pattern.count}×)
                  </div>
                </div>

                {/* Emotion breakdown */}
                <div className="flex gap-2 mt-2">
                  {Object.entries(pattern.emotions).filter(([k]) => k !== 'total').map(([emotion, count]) => {
                    if (count === 0) return null;
                    return (
                      <div 
                        key={emotion}
                        className="flex items-center gap-1 text-xs text-gray-400"
                      >
                        <span>{emotionIcons[emotion]}</span>
                        <span>{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Events */}
      {recentEvents.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
          <h3 className="text-xl font-bold text-white mb-4">
            🕐 Recente Emoties
          </h3>

          <div className="space-y-2">
            {recentEvents.map((event, idx) => (
              <div 
                key={idx}
                className="bg-slate-700/30 p-3 rounded-lg flex items-start gap-3"
              >
                <span className="text-2xl">{emotionIcons[event.emotion]}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span 
                      className="px-2 py-0.5 rounded text-xs font-medium"
                      style={{ 
                        backgroundColor: `${emotionColors[event.emotion]}20`,
                        color: emotionColors[event.emotion]
                      }}
                    >
                      {event.emotion}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(event.timestamp).toLocaleString('nl-NL')}
                    </span>
                  </div>
                  
                  {event.context && (
                    <div className="text-sm text-gray-300 mb-1">"{event.context}"</div>
                  )}
                  
                  {(event.topics?.length > 0 || event.general_topics?.length > 0) && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {[...event.topics, ...event.general_topics.map(t => ({ topic: t }))].map((t, i) => (
                        <span 
                          key={i}
                          className="text-xs bg-slate-600 text-gray-300 px-2 py-0.5 rounded"
                        >
                          {typeof t === 'object' ? t.topic : t}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  <div className="text-xs text-gray-500 mt-1">
                    Score: {event.final_score}
                    {event.intensifier && ` (${event.intensifier} ×${event.multiplier})`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EmotionStatsTab;
