import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Link2, Search, ZoomIn, ZoomOut, Maximize2,
  ChevronDown, ChevronRight, X, Target, Layers,
  GitBranch, Circle, ArrowRight, BarChart3, RefreshCw
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const tagColors = {
  systeem: '#f59e0b', communicatie: '#3b82f6', gedrag: '#22c55e', natuur: '#10b981',
  technologie: '#8b5cf6', emotie: '#ec4899', gaming: '#ef4444', willem: '#06b6d4',
  biografie: '#a855f7', relatie: '#f43f5e', community: '#14b8a6', gezondheid: '#84cc16',
  default: '#64748b',
};

function getColor(tags) {
  if (!tags || tags.length === 0) return tagColors.default;
  for (const t of tags) {
    if (tagColors[t]) return tagColors[t];
  }
  return tagColors.default;
}

export function VerbandenPage({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('graph');
  const [stats, setStats] = useState(null);
  const [clusters, setClusters] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [neighborhood, setNeighborhood] = useState(null);
  const [loadingNeighborhood, setLoadingNeighborhood] = useState(false);
  const [expandedCluster, setExpandedCluster] = useState(null);
  const [rebuilding, setRebuilding] = useState(false);
  const [rebuildMsg, setRebuildMsg] = useState(null);
  const [rebuildConfirm, setRebuildConfirm] = useState(false);

  const loadStats = useCallback(() => {
    fetch(`${API}/api/graph/stats`).then(r => r.json()).then(setStats).catch(() => {});
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const handleRebuild = async () => {
    if (rebuilding) return;
    // Two-step confirm zonder browser-popup
    if (!rebuildConfirm) {
      setRebuildConfirm(true);
      setRebuildMsg('Klik nogmaals op "Bevestig herbouw" om de Knowledge Graph volledig opnieuw op te bouwen.');
      setTimeout(() => { setRebuildConfirm(false); setRebuildMsg(null); }, 5000);
      return;
    }
    setRebuildConfirm(false);
    setRebuilding(true);
    setRebuildMsg('Herbouwen bezig… dit kan 5-15 seconden duren.');
    try {
      const res = await fetch(`${API}/api/graph/rebuild`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setRebuildMsg(`Graph herbouwd: ${data.nodes} nodes, ${data.edges} edges (${data.entries_scanned} entries gescand)`);
        loadStats();
      } else {
        setRebuildMsg('Herbouw mislukt — controleer de server logs.');
      }
    } catch (e) {
      setRebuildMsg(`Fout: ${e.message}`);
    }
    setRebuilding(false);
    setTimeout(() => setRebuildMsg(null), 8000);
  };

  const handleSearch = async (q) => {
    setSearchQuery(q);
    if (!q || q.length < 2) { setSearchResults([]); return; }
    setSearching(true);
    const res = await fetch(`${API}/api/graph/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    setSearchResults(data.results || []);
    setSearching(false);
  };

  const selectNode = async (node) => {
    setSelectedNode(node);
    setLoadingNeighborhood(true);
    const res = await fetch(`${API}/api/graph/neighborhood/${node.id}?depth=1`);
    const data = await res.json();
    setNeighborhood(data);
    setLoadingNeighborhood(false);
  };

  const loadClusters = async () => {
    if (clusters.length > 0) return;
    const res = await fetch(`${API}/api/graph/clusters?min_size=5`);
    const data = await res.json();
    setClusters(data.clusters || []);
  };

  useEffect(() => {
    if (activeTab === 'clusters') loadClusters();
  }, [activeTab]);

  const tabs = [
    { id: 'graph', label: 'Knowledge Graph', icon: GitBranch },
    { id: 'clusters', label: 'Clusters', icon: Layers },
    { id: 'stats', label: 'Statistieken', icon: BarChart3 },
  ];

  return (
    <MainLayout activePage="connections" onNavigate={onNavigate}>
      <div data-testid="verbanden-page" className="h-full flex flex-col">
        {/* Banner */}
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0 pr-16">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #06b6d4, #3b82f6)' }}>
              <Link2 className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1">
              <h1 className="text-base font-bold text-white leading-tight">Verbanden</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">
                {stats ? `${stats.total_nodes} nodes | ${stats.total_edges} edges | ${stats.avg_connections} gem. verbindingen` : 'Laden...'}
              </p>
            </div>
            <button
              data-testid="graph-rebuild-btn"
              onClick={handleRebuild}
              disabled={rebuilding}
              title="Knowledge Graph volledig herbouwen vanuit knowledge_base"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-[11px] font-medium whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${
                rebuildConfirm
                  ? 'border-amber-500/40 bg-amber-500/15 text-amber-300 hover:bg-amber-500/25 animate-pulse'
                  : 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20'
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${rebuilding ? 'animate-spin' : ''}`} />
              {rebuilding ? 'Herbouwen…' : (rebuildConfirm ? 'Bevestig herbouw' : 'Rebuild Graph')}
            </button>
          </div>
          {rebuildMsg && (
            <div data-testid="graph-rebuild-msg" className="mb-2 px-3 py-1.5 rounded-md text-[11px] bg-cyan-500/10 border border-cyan-500/20 text-cyan-200">
              {rebuildMsg}
            </div>
          )}
          <div className="flex overflow-x-auto gap-0">
            {tabs.map(t => {
              const isActive = activeTab === t.id;
              return (
                <button key={t.id} data-testid={`graph-tab-${t.id}`} onClick={() => setActiveTab(t.id)}
                  className="relative flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors whitespace-nowrap flex-shrink-0"
                  style={{ color: isActive ? '#06b6d4' : '#94a3b8' }}>
                  <t.icon className="w-3.5 h-3.5" /> {t.label}
                  {isActive && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full bg-cyan-500" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-4xl mx-auto space-y-4">

            {/* GRAPH TAB */}
            {activeTab === 'graph' && (
              <>
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                  <input data-testid="graph-search" type="text" value={searchQuery}
                    onChange={e => handleSearch(e.target.value)}
                    placeholder="Zoek een begrip om de Knowledge Graph te verkennen..."
                    className="w-full pl-9 pr-3 py-3 bg-slate-900/60 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors" />
                </div>

                {/* Search results */}
                {searchResults.length > 0 && (
                  <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="px-4 py-2 border-b border-slate-800/50">
                      <p className="text-xs text-slate-400">{searchResults.length} resultaten voor "{searchQuery}"</p>
                    </div>
                    <div className="max-h-60 overflow-y-auto">
                      {searchResults.map(node => {
                        const color = getColor(node.tags);
                        return (
                          <button key={node.id} data-testid={`search-result-${node.id}`}
                            onClick={() => { selectNode(node); setSearchResults([]); setSearchQuery(node.label); }}
                            className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-slate-800/30 transition-colors text-left border-b border-slate-800/30 last:border-0">
                            <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: color }} />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm text-white truncate">{node.label}</p>
                              <p className="text-[10px] text-slate-500 truncate">{node.short_description || node.description?.slice(0, 60)}</p>
                            </div>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400">{node.score}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Selected node + neighborhood */}
                {selectedNode ? (
                  <>
                    <NodeDetail node={selectedNode} onClose={() => { setSelectedNode(null); setNeighborhood(null); }} />
                    {loadingNeighborhood ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="w-6 h-6 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
                      </div>
                    ) : neighborhood && (
                      <GraphVisual
                        nodes={neighborhood.nodes}
                        edges={neighborhood.edges}
                        centerNodeId={selectedNode.id}
                        onNodeClick={selectNode}
                      />
                    )}
                  </>
                ) : (
                  /* Default: show most connected */
                  stats && (
                    <>
                      <div className="p-4 rounded-xl border border-cyan-500/20" style={{ background: 'linear-gradient(135deg, rgba(6,182,212,0.06), rgba(59,130,246,0.04))' }}>
                        <h2 className="text-lg font-bold text-white mb-1">Knowledge Graph</h2>
                        <p className="text-xs text-slate-400">
                          {stats.total_nodes} begrippen verbonden door {stats.total_edges} relaties.
                          Zoek een begrip hierboven om de graph te verkennen.
                        </p>
                      </div>

                      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                          <Target className="w-4 h-4 text-cyan-400" /> Meest Verbonden Begrippen
                        </h3>
                        <div className="space-y-2">
                          {stats.most_connected?.map((mc, i) => (
                            <button key={mc.id} onClick={() => selectNode({ id: mc.id, label: mc.label })}
                              data-testid={`top-node-${i}`}
                              className="w-full flex items-center gap-3 p-2.5 bg-slate-800/30 rounded-xl hover:bg-slate-800/60 transition-colors text-left">
                              <div className="w-7 h-7 rounded-lg bg-cyan-500/10 flex items-center justify-center text-[10px] font-bold text-cyan-400">{i + 1}</div>
                              <span className="text-sm text-white flex-1 truncate">{mc.label}</span>
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">{mc.connections} verbindingen</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                          <Layers className="w-4 h-4 text-amber-400" /> Top Tags
                        </h3>
                        <div className="flex flex-wrap gap-1.5">
                          {stats.top_tags?.map(t => (
                            <button key={t.tag} onClick={() => handleSearch(t.tag)}
                              className="text-[11px] px-2.5 py-1 rounded-lg border transition-colors"
                              style={{ background: `${getColor([t.tag])}08`, borderColor: `${getColor([t.tag])}25`, color: getColor([t.tag]) }}>
                              #{t.tag} <span className="opacity-60">({t.count})</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    </>
                  )
                )}
              </>
            )}

            {/* CLUSTERS TAB */}
            {activeTab === 'clusters' && (
              <>
                <div className="p-4 rounded-xl border border-purple-500/20" style={{ background: 'linear-gradient(135deg, rgba(168,85,247,0.06), rgba(139,92,246,0.04))' }}>
                  <h2 className="text-lg font-bold text-white mb-1">Knowledge Clusters</h2>
                  <p className="text-xs text-slate-400">{clusters.length} clusters gevonden op basis van gedeelde tags</p>
                </div>
                <div className="space-y-2">
                  {clusters.map(c => {
                    const isExp = expandedCluster === c.tag;
                    const color = getColor([c.tag]);
                    return (
                      <div key={c.tag} data-testid={`cluster-${c.tag}`} className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
                        <button onClick={() => setExpandedCluster(isExp ? null : c.tag)}
                          className="w-full flex items-center gap-3 p-3 hover:bg-slate-800/20 transition-colors">
                          {isExp ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                          <div className="w-3 h-3 rounded-full" style={{ background: color }} />
                          <span className="text-sm text-white font-medium flex-1 text-left">#{c.tag}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">{c.size} items</span>
                        </button>
                        {isExp && (
                          <div className="px-3 pb-3">
                            <div className="flex flex-wrap gap-1.5">
                              {c.members.map(m => (
                                <button key={m.id} onClick={() => { selectNode(m); setActiveTab('graph'); setSearchQuery(m.label); }}
                                  className="text-[11px] px-2 py-1 rounded-lg bg-slate-800/50 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors">
                                  {m.label}
                                </button>
                              ))}
                              {c.size > 20 && <span className="text-[10px] px-2 py-1 text-slate-600">+{c.size - 20} meer</span>}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </>
            )}

            {/* STATS TAB */}
            {activeTab === 'stats' && stats && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <StatCard label="Nodes" value={stats.total_nodes} color="#06b6d4" />
                  <StatCard label="Edges" value={stats.total_edges} color="#3b82f6" />
                  <StatCard label="Gem. Verbindingen" value={stats.avg_connections} color="#22c55e" />
                  <StatCard label="Top Tags" value={stats.top_tags?.length || 0} color="#f59e0b" />
                </div>

                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-white mb-4">Top 20 Tags verdeling</h3>
                  <div className="space-y-2">
                    {stats.top_tags?.map(t => {
                      const pct = Math.round((t.count / stats.total_nodes) * 100);
                      const color = getColor([t.tag]);
                      return (
                        <div key={t.tag} className="flex items-center gap-3">
                          <span className="text-xs text-slate-400 w-28 truncate">#{t.tag}</span>
                          <div className="flex-1 h-4 bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full rounded-full transition-all" style={{ width: `${Math.max(pct, 2)}%`, background: color }} />
                          </div>
                          <span className="text-[10px] text-slate-500 w-16 text-right">{t.count} ({pct}%)</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-white mb-3">Top 20 Meest Verbonden</h3>
                  <div className="space-y-2">
                    {(() => {
                      const maxConn = Math.max(1, ...(stats.most_connected || []).map(m => m.connections || 0));
                      return stats.most_connected?.map((mc, i) => {
                        const bars = Math.max(1, Math.round((mc.connections / maxConn) * 20));
                        return (
                          <div key={mc.id} className="flex items-center gap-3">
                            <span className="text-[10px] text-slate-600 w-6 text-center">{i + 1}</span>
                            <span className="text-xs text-white flex-1 truncate">{mc.label}</span>
                            <div className="flex-shrink-0 flex gap-0.5">
                              {Array.from({ length: bars }).map((_, j) => (
                                <div key={j} className="w-1.5 h-3 bg-cyan-500/60 rounded-sm" />
                              ))}
                            </div>
                            <span className="text-[10px] text-slate-500 w-12 text-right">{mc.connections}</span>
                          </div>
                        );
                      });
                    })()}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

function NodeDetail({ node, onClose }) {
  const color = getColor(node.tags);
  return (
    <div data-testid="node-detail" className="p-5 rounded-xl border" style={{ borderColor: `${color}30`, background: `${color}06` }}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold text-white" style={{ background: color }}>
            {(node.label || '?')[0].toUpperCase()}
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">{node.label}</h2>
            <p className="text-[10px] text-slate-500">{node.type || 'knowledge'} | {node.id?.slice(0, 8)}...</p>
          </div>
        </div>
        <button onClick={onClose} className="p-1.5 hover:bg-slate-800 rounded-lg"><X className="w-4 h-4 text-slate-400" /></button>
      </div>
      {node.description && <p className="text-sm text-slate-300 leading-relaxed mb-3">{node.description}</p>}
      {node.tags?.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {node.tags.map((t, i) => (
            <span key={i} className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: `${getColor([t])}15`, color: getColor([t]) }}>#{t}</span>
          ))}
        </div>
      )}
      {node.lagen && (
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(node.lagen).filter(([k, v]) => v).map(([k, v]) => (
            <div key={k} className="p-2 bg-slate-800/30 rounded-lg">
              <p className="text-[9px] text-slate-500 uppercase">{k}</p>
              <p className="text-[11px] text-slate-300 line-clamp-2">{String(v).slice(0, 100)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function GraphVisual({ nodes, edges, centerNodeId, onNodeClick }) {
  const canvasRef = useRef(null);
  const [positions, setPositions] = useState({});
  const [hoveredNode, setHoveredNode] = useState(null);

  useEffect(() => {
    if (!nodes || nodes.length === 0) return;
    const pos = {};
    const centerNode = nodes.find(n => n.id === centerNodeId);
    const others = nodes.filter(n => n.id !== centerNodeId);
    const cx = 400, cy = 250;
    if (centerNode) pos[centerNode.id] = { x: cx, y: cy };
    const radius = Math.min(200, 80 + others.length * 8);
    others.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / others.length - Math.PI / 2;
      const r = radius + (Math.random() * 40 - 20);
      pos[n.id] = { x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r };
    });
    setPositions(pos);
  }, [nodes, centerNodeId]);

  if (!nodes || nodes.length <= 1) {
    return (
      <div className="py-8 text-center border border-dashed border-slate-800 rounded-xl">
        <GitBranch className="w-8 h-8 text-slate-700 mx-auto mb-2" />
        <p className="text-sm text-slate-500">Geen directe verbindingen gevonden voor dit begrip</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-4 py-2 border-b border-slate-800/50 flex items-center justify-between">
        <p className="text-xs text-slate-400">{nodes.length} nodes, {edges.length} verbindingen</p>
      </div>
      <div className="relative" style={{ height: '500px' }}>
        <svg width="100%" height="100%" viewBox="0 0 800 500" className="select-none">
          {/* Edges */}
          {edges.map(e => {
            const from = positions[e.source];
            const to = positions[e.target];
            if (!from || !to) return null;
            const isHovered = hoveredNode === e.source || hoveredNode === e.target;
            return (
              <line key={e.id} x1={from.x} y1={from.y} x2={to.x} y2={to.y}
                stroke={isHovered ? '#06b6d4' : '#334155'} strokeWidth={isHovered ? 1.5 : 0.5}
                opacity={hoveredNode ? (isHovered ? 0.8 : 0.15) : 0.4} />
            );
          })}
          {/* Nodes */}
          {nodes.map(n => {
            const p = positions[n.id];
            if (!p) return null;
            const isCenter = n.id === centerNodeId;
            const isHovered = hoveredNode === n.id;
            const color = getColor(n.tags);
            const r = isCenter ? 18 : (isHovered ? 12 : 8);
            return (
              <g key={n.id} className="cursor-pointer"
                onMouseEnter={() => setHoveredNode(n.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => onNodeClick(n)}>
                <circle cx={p.x} cy={p.y} r={r + 3} fill={color} opacity={isHovered || isCenter ? 0.2 : 0.05} />
                <circle cx={p.x} cy={p.y} r={r} fill={isCenter ? color : '#1e293b'}
                  stroke={color} strokeWidth={isCenter ? 2.5 : (isHovered ? 2 : 1)}
                  opacity={hoveredNode ? (isHovered || isCenter ? 1 : 0.4) : 1} />
                {(isCenter || isHovered) && (
                  <text x={p.x} y={p.y + r + 14} textAnchor="middle"
                    fill={isCenter ? '#fff' : '#94a3b8'} fontSize={isCenter ? 11 : 9}
                    fontWeight={isCenter ? '600' : '400'}>
                    {n.label?.slice(0, 25)}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>
      {/* Legend */}
      <div className="px-4 py-2 border-t border-slate-800/50 flex items-center gap-3 flex-wrap">
        <span className="text-[10px] text-slate-600">Klik op een node om te navigeren</span>
        <span className="text-[10px] text-slate-600">|</span>
        {Object.entries(tagColors).slice(0, 6).map(([tag, color]) => (
          <span key={tag} className="flex items-center gap-1 text-[9px] text-slate-500">
            <span className="w-2 h-2 rounded-full" style={{ background: color }} /> {tag}
          </span>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl text-center">
      <p className="text-2xl font-bold" style={{ color }}>{value}</p>
      <p className="text-[10px] text-slate-500 mt-1">{label}</p>
    </div>
  );
}

export default VerbandenPage;
