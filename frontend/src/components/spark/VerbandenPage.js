import React, { useState } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { 
  Link2, Network, GitBranch, Share2, Layers,
  Plus, Search, Filter, ZoomIn, ZoomOut, Maximize2,
  Circle, ArrowRight
} from 'lucide-react';

export function VerbandenPage({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('graph');
  const [zoomLevel, setZoomLevel] = useState(100);

  const tabs = [
    { id: 'graph', label: 'Knowledge Graph' },
    { id: 'chains', label: 'Chains' },
    { id: 'clusters', label: 'Clusters' },
    { id: 'instellingen', label: 'Instellingen' },
  ];

  return (
    <MainLayout activePage="connections" onNavigate={onNavigate}>
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center">
              <Link2 className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">Verbanden</h1>
          </div>
          <p className="text-slate-400">SPARK AI → Knowledge Graph & Chains</p>
        </div>

        {/* Tabs */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex gap-2">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          
          {/* Zoom Controls */}
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setZoomLevel(Math.max(50, zoomLevel - 10))}
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              <ZoomOut className="w-4 h-4 text-slate-400" />
            </button>
            <span className="text-sm text-slate-400 w-12 text-center">{zoomLevel}%</span>
            <button 
              onClick={() => setZoomLevel(Math.min(150, zoomLevel + 10))}
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              <ZoomIn className="w-4 h-4 text-slate-400" />
            </button>
            <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
              <Maximize2 className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>

        {/* Main Graph Area */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden mb-6">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Network className="w-5 h-5 text-cyan-400" />
              Knowledge Graph
            </h3>
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 bg-cyan-500/20 text-cyan-400 text-xs rounded">268 NODES</span>
              <span className="px-2 py-1 bg-purple-500/20 text-purple-400 text-xs rounded">512 EDGES</span>
            </div>
          </div>
          
          {/* Graph Visualization Placeholder */}
          <div className="h-96 bg-slate-800/20 relative overflow-hidden">
            {/* Grid Background */}
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAgTSAwIDIwIEwgNDAgMjAgTSAyMCAwIEwgMjAgNDAgTSAwIDMwIEwgNDAgMzAgTSAzMCAwIEwgMzAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzMzNCIgb3BhY2l0eT0iMC4yIiBzdHJva2Utd2lkdGg9IjEiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-50"></div>
            
            {/* Sample Nodes */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative" style={{ transform: `scale(${zoomLevel / 100})` }}>
                {/* Center Node */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                  <div className="w-16 h-16 bg-gradient-to-br from-amber-500 to-orange-600 rounded-full flex items-center justify-center shadow-lg shadow-amber-500/30">
                    <span className="text-white font-bold text-sm">CORE</span>
                  </div>
                </div>
                
                {/* Connected Nodes */}
                {[
                  { x: -120, y: -80, label: 'Kennis', color: 'cyan' },
                  { x: 120, y: -80, label: 'Context', color: 'purple' },
                  { x: -140, y: 60, label: 'Emotie', color: 'pink' },
                  { x: 140, y: 60, label: 'Trigger', color: 'amber' },
                  { x: 0, y: -120, label: 'User', color: 'green' },
                  { x: 0, y: 120, label: 'Response', color: 'blue' },
                ].map((node, idx) => (
                  <div 
                    key={idx}
                    className="absolute top-1/2 left-1/2"
                    style={{ transform: `translate(calc(-50% + ${node.x}px), calc(-50% + ${node.y}px))` }}
                  >
                    {/* Connection Line */}
                    <svg 
                      className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none"
                      width="300" 
                      height="300" 
                      style={{ transform: 'translate(-150px, -150px)' }}
                    >
                      <line 
                        x1="150" 
                        y1="150" 
                        x2={150 - node.x} 
                        y2={150 - node.y} 
                        stroke={`rgb(var(--${node.color}-500))`}
                        strokeWidth="2"
                        strokeOpacity="0.3"
                        className="stroke-slate-600"
                      />
                    </svg>
                    
                    {/* Node */}
                    <div className={`w-12 h-12 bg-${node.color}-500/20 border-2 border-${node.color}-500/50 rounded-full flex items-center justify-center backdrop-blur-sm`}>
                      <span className="text-white text-xs font-medium">{node.label.slice(0, 3)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Placeholder Text */}
            <div className="absolute bottom-4 left-4 text-slate-500 text-sm">
              Knowledge Graph Visualisatie - Placeholder
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Chains */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-cyan-400" />
              Chains
            </h3>
            <div className="space-y-3">
              {[
                { from: 'Vraag', to: 'Context', to2: 'Antwoord' },
                { from: 'Emotie', to: 'Trigger', to2: 'Reactie' },
                { from: 'Kennis', to: 'Verband', to2: 'Inzicht' },
              ].map((chain, idx) => (
                <div key={idx} className="flex items-center gap-2 p-3 bg-slate-800/50 rounded-xl border-2 border-dashed border-slate-700">
                  <span className="text-xs text-cyan-400 bg-cyan-500/20 px-2 py-1 rounded">{chain.from}</span>
                  <ArrowRight className="w-3 h-3 text-slate-600" />
                  <span className="text-xs text-purple-400 bg-purple-500/20 px-2 py-1 rounded">{chain.to}</span>
                  <ArrowRight className="w-3 h-3 text-slate-600" />
                  <span className="text-xs text-amber-400 bg-amber-500/20 px-2 py-1 rounded">{chain.to2}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Clusters */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Share2 className="w-4 h-4 text-cyan-400" />
              Clusters
            </h3>
            <div className="space-y-3">
              {[
                { name: 'Kennis Cluster', nodes: 45, color: 'cyan' },
                { name: 'Emotie Cluster', nodes: 28, color: 'pink' },
                { name: 'Context Cluster', nodes: 67, color: 'purple' },
                { name: 'User Cluster', nodes: 12, color: 'green' },
              ].map((cluster, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl border-2 border-dashed border-slate-700">
                  <div className="flex items-center gap-2">
                    <Circle className={`w-3 h-3 text-${cluster.color}-400 fill-current`} />
                    <span className="text-sm text-slate-300">{cluster.name}</span>
                  </div>
                  <span className="text-xs text-slate-500">{cluster.nodes} nodes</span>
                </div>
              ))}
            </div>
          </div>

          {/* Layers */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Lagen
            </h3>
            <div className="space-y-3">
              {[
                { name: 'Laag 1 - Basis', desc: 'Kern concepten', color: 'amber' },
                { name: 'Laag 2 - Context', desc: 'Relaties', color: 'cyan' },
                { name: 'Laag 3 - Diep', desc: 'Inzichten', color: 'purple' },
              ].map((layer, idx) => (
                <div key={idx} className={`p-3 bg-${layer.color}-500/10 border border-${layer.color}-500/30 rounded-xl`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white">{layer.name}</span>
                    <span className={`text-xs text-${layer.color}-400`}>{layer.desc}</span>
                  </div>
                </div>
              ))}
            </div>
            <button className="w-full mt-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-xl text-sm transition-colors flex items-center justify-center gap-2">
              <Plus className="w-4 h-4" />
              Laag Toevoegen
            </button>
          </div>

        </div>

      </div>
    </MainLayout>
  );
}

export default VerbandenPage;
