import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function RoadmapTab() {
  const [roadmapData, setRoadmapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('tree'); // 'tree' or 'list'

  useEffect(() => {
    fetchRoadmap();
  }, []);

  const fetchRoadmap = async () => {
    try {
      const response = await axios.get(`${API}/roadmap/`);
      setRoadmapData(response.data);
    } catch (error) {
      console.error("Error fetching roadmap:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-purple-400">Roadmap laden...</div>
      </div>
    );
  }

  if (!roadmapData) {
    return <div className="text-red-400">Kon roadmap niet laden</div>;
  }

  const statusColors = {
    done: "bg-green-500/20 text-green-300 border-green-500/50",
    in_progress: "bg-blue-500/20 text-blue-300 border-blue-500/50",
    blocked: "bg-red-500/20 text-red-300 border-red-500/50",
    todo: "bg-gray-500/20 text-gray-300 border-gray-500/50",
    planned: "bg-purple-500/20 text-purple-300 border-purple-500/50",
  };

  const statusIcons = {
    done: "✅",
    in_progress: "🔄",
    blocked: "🔒",
    todo: "⏳",
    planned: "📋",
  };

  return (
    <div className="space-y-6">
      {/* View Toggle */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">🗺️ Spark Roadmap</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('tree')}
            className={`px-4 py-2 rounded-lg transition-all ${
              viewMode === 'tree'
                ? 'bg-purple-500 text-white'
                : 'bg-slate-700/50 text-gray-400 hover:bg-slate-700'
            }`}
          >
            🌳 Tree View
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-4 py-2 rounded-lg transition-all ${
              viewMode === 'list'
                ? 'bg-purple-500 text-white'
                : 'bg-slate-700/50 text-gray-400 hover:bg-slate-700'
            }`}
          >
            📋 List View
          </button>
        </div>
      </div>

      {/* Metadata */}
      {roadmapData.metadata && (
        <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">📊 Overview</h3>
          <div className="grid grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{roadmapData.metadata.completed}</div>
              <div className="text-xs text-gray-400">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{roadmapData.metadata.in_progress}</div>
              <div className="text-xs text-gray-400">In Progress</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">{roadmapData.metadata.blocked}</div>
              <div className="text-xs text-gray-400">Blocked</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-400">{roadmapData.metadata.todo}</div>
              <div className="text-xs text-gray-400">Todo</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">{roadmapData.metadata.total_items}</div>
              <div className="text-xs text-gray-400">Total</div>
            </div>
          </div>
        </div>
      )}

      {/* Tree View */}
      {viewMode === 'tree' && (
        <div className="space-y-4">
          {Object.entries(roadmapData.versions || {}).map(([versionKey, versionData], versionIndex) => {
            const isLast = versionIndex === Object.keys(roadmapData.versions).length - 1;
            
            return (
              <div key={versionKey} className="relative">
                {/* Timeline connector */}
                {!isLast && (
                  <div className="absolute left-6 top-20 bottom-0 w-0.5 bg-gradient-to-b from-purple-500/50 to-transparent" />
                )}
                
                {/* Version Node */}
                <div className="flex items-start gap-4">
                  {/* Timeline dot */}
                  <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-xl border-2 ${
                    versionData.status === 'done' ? 'bg-green-500/20 border-green-500' :
                    versionData.status === 'in_progress' ? 'bg-blue-500/20 border-blue-500 animate-pulse' :
                    versionData.status === 'blocked' ? 'bg-red-500/20 border-red-500' :
                    'bg-purple-500/20 border-purple-500/50'
                  }`}>
                    {statusIcons[versionData.status]}
                  </div>
                  
                  {/* Version Card */}
                  <div className="flex-1 bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 rounded-lg overflow-hidden">
                    {/* Version Header */}
                    <div className="p-4 bg-slate-700/30 border-b border-purple-500/20">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-xl font-bold text-white">{versionKey}</h3>
                          <p className="text-sm text-gray-400">{versionData.naam}</p>
                        </div>
                        <div className={`px-4 py-2 rounded-lg border ${statusColors[versionData.status]}`}>
                          {statusIcons[versionData.status]} {versionData.status.replace('_', ' ')}
                        </div>
                      </div>
                      {versionData.progress !== undefined && (
                        <div className="mt-3">
                          <div className="flex items-center justify-between text-sm mb-1">
                            <span className="text-gray-400">Progress</span>
                            <span className="text-white font-semibold">{versionData.progress}%</span>
                          </div>
                          <div className="w-full bg-slate-700 rounded-full h-2">
                            <div
                              className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${versionData.progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Items - Show first 5, then collapse */}
                    <div className="p-4">
                      {versionData.items && versionData.items.length > 0 ? (
                        <>
                          <div className="space-y-2">
                            {versionData.items.slice(0, 5).map((item, itemIndex) => (
                              <div key={item.id} className="relative">
                                {/* Sub-item connector */}
                                {itemIndex < Math.min(4, versionData.items.length - 1) && (
                                  <div className="absolute left-2 top-8 bottom-0 w-px bg-purple-500/20" />
                                )}
                                
                                <div className="flex items-start gap-3">
                                  {/* Item dot */}
                                  <div className={`flex-shrink-0 w-4 h-4 mt-1 rounded-full border-2 ${
                                    item.status === 'done' ? 'bg-green-500 border-green-600' :
                                    item.status === 'in_progress' ? 'bg-blue-500 border-blue-600' :
                                    item.status === 'blocked' ? 'bg-red-500 border-red-600' :
                                    'bg-gray-500 border-gray-600'
                                  }`} />
                                  
                                  {/* Item content */}
                                  <div className="flex-1 bg-slate-700/30 p-3 rounded-lg border border-slate-600/50 hover:border-purple-500/50 transition-all">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                          <h4 className="text-white font-medium text-sm">{item.titel}</h4>
                                          {item.priority && item.priority !== 'medium' && (
                                            <span className={`text-xs px-2 py-0.5 rounded ${
                                              item.priority === 'critical' ? 'bg-red-500/20 text-red-300' :
                                              item.priority === 'high' ? 'bg-orange-500/20 text-orange-300' :
                                              'bg-gray-500/20 text-gray-300'
                                            }`}>
                                              {item.priority}
                                            </span>
                                          )}
                                        </div>
                                        {item.notes && (
                                          <p className="text-xs text-gray-400 mt-1">{item.notes}</p>
                                        )}
                                        {item.blocked_reason && (
                                          <p className="text-xs text-red-300 mt-1">🔒 {item.blocked_reason}</p>
                                        )}
                                      </div>
                                      {item.progress !== undefined && (
                                        <div className="ml-3 text-right">
                                          <div className="text-sm font-bold text-purple-400">{item.progress}%</div>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                          
                          {versionData.items.length > 5 && (
                            <div className="mt-3 text-center">
                              <button
                                onClick={() => setViewMode('list')}
                                className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
                              >
                                + {versionData.items.length - 5} meer items (klik voor list view)
                              </button>
                            </div>
                          )}
                        </>
                      ) : (
                        <p className="text-gray-500 text-center py-2 text-sm">Nog geen items</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
          
          {/* Future placeholder */}
          <div className="flex items-start gap-4 opacity-50">
            <div className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-xl border-2 border-dashed border-purple-500/30">
              🔮
            </div>
            <div className="flex-1 bg-slate-800/20 backdrop-blur-lg border border-dashed border-purple-500/20 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-400">Toekomst...</h3>
              <p className="text-sm text-gray-500 mt-1">Meer features worden toegevoegd naarmate Spark groeit</p>
            </div>
          </div>
        </div>
      )}

      {/* List View (Original) */}
      {viewMode === 'list' && (
        <div className="space-y-6">
          {Object.entries(roadmapData.versions || {}).map(([versionKey, versionData]) => (
            <div key={versionKey} className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 rounded-lg overflow-hidden">
              {/* Version Header */}
              <div className="p-4 bg-slate-700/30 border-b border-purple-500/20">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-white">{versionKey}</h3>
                    <p className="text-sm text-gray-400">{versionData.naam}</p>
                  </div>
                  <div className={`px-4 py-2 rounded-lg border ${statusColors[versionData.status]}`}>
                    {statusIcons[versionData.status]} {versionData.status.replace('_', ' ')}
                  </div>
                </div>
                {versionData.progress !== undefined && (
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-400">Progress</span>
                      <span className="text-white font-semibold">{versionData.progress}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                        style={{ width: `${versionData.progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Items */}
              <div className="p-4 space-y-2">
                {versionData.items && versionData.items.length > 0 ? (
                  versionData.items.map((item) => (
                    <div key={item.id} className="bg-slate-700/30 p-4 rounded-lg border border-slate-600/50 hover:border-purple-500/50 transition-all">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-lg">{statusIcons[item.status]}</span>
                            <h4 className="text-white font-medium">{item.titel}</h4>
                            {item.priority && item.priority !== 'medium' && (
                              <span className={`text-xs px-2 py-1 rounded ${
                                item.priority === 'critical' ? 'bg-red-500/20 text-red-300' :
                                item.priority === 'high' ? 'bg-orange-500/20 text-orange-300' :
                                'bg-gray-500/20 text-gray-300'
                              }`}>
                                {item.priority}
                              </span>
                            )}
                          </div>
                          {item.notes && (
                            <p className="text-sm text-gray-400 mt-1">{item.notes}</p>
                          )}
                          {item.blocked_reason && (
                            <p className="text-sm text-red-300 mt-1">🔒 {item.blocked_reason}</p>
                          )}
                          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                            {item.assigned_to && <span>👤 {item.assigned_to}</span>}
                            {item.completed_date && <span>✓ {new Date(item.completed_date).toLocaleDateString()}</span>}
                          </div>
                        </div>
                        {item.progress !== undefined && (
                          <div className="ml-4 text-right">
                            <div className="text-2xl font-bold text-purple-400">{item.progress}%</div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4">Nog geen items</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


export default RoadmapTab;
