import React, { useState } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { 
  Sparkles, Heart, Smile, Frown, Meh, Zap,
  ThumbsUp, ThumbsDown, AlertCircle, Sun, Cloud,
  Plus, Search, Filter
} from 'lucide-react';

export function EmotiesPage({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('overzicht');

  const tabs = [
    { id: 'overzicht', label: 'Overzicht' },
    { id: 'detectie', label: 'Detectie' },
    { id: 'reacties', label: 'Reacties' },
    { id: 'instellingen', label: 'Instellingen' },
  ];

  return (
    <MainLayout activePage="emotions" onNavigate={onNavigate}>
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-pink-500 to-rose-600 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">Emoties</h1>
          </div>
          <p className="text-slate-400">SPARK AI → Emotie Systeem</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-pink-500/20 text-pink-400 border border-pink-500/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Emotie Status */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Heart className="w-4 h-4 text-pink-400" />
              Huidige Stemming
            </h3>
            <div className="aspect-square bg-slate-800/30 rounded-xl border-2 border-dashed border-slate-700 flex items-center justify-center">
              <div className="text-center">
                <Smile className="w-16 h-16 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">Emotie Detectie</p>
                <p className="text-slate-600 text-xs mt-1">Placeholder</p>
              </div>
            </div>
          </div>

          {/* Emotie Types */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-pink-400" />
              Emotie Types
            </h3>
            <div className="space-y-3">
              {[
                { icon: Smile, label: 'Positief', color: 'green' },
                { icon: Meh, label: 'Neutraal', color: 'slate' },
                { icon: Frown, label: 'Negatief', color: 'red' },
                { icon: AlertCircle, label: 'Urgent', color: 'amber' },
              ].map((emotie, idx) => (
                <div key={idx} className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-xl border-2 border-dashed border-slate-700">
                  <emotie.icon className={`w-5 h-5 text-${emotie.color}-400`} />
                  <span className="text-slate-400 text-sm">{emotie.label}</span>
                  <span className="ml-auto text-slate-600 text-xs">Placeholder</span>
                </div>
              ))}
            </div>
          </div>

          {/* Reactie Patronen */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Zap className="w-4 h-4 text-pink-400" />
              Reactie Patronen
            </h3>
            <div className="aspect-square bg-slate-800/30 rounded-xl border-2 border-dashed border-slate-700 flex items-center justify-center">
              <div className="text-center">
                <ThumbsUp className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">Reactie Mapping</p>
                <p className="text-slate-600 text-xs mt-1">Placeholder</p>
              </div>
            </div>
          </div>

        </div>

        {/* Bottom Section */}
        <div className="mt-6 bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Heart className="w-4 h-4 text-pink-400" />
              Emotie Configuratie
            </h3>
            <button className="px-4 py-2 bg-pink-500/20 text-pink-400 rounded-xl text-sm hover:bg-pink-500/30 transition-colors flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Toevoegen
            </button>
          </div>
          <div className="h-48 bg-slate-800/30 rounded-xl border-2 border-dashed border-slate-700 flex items-center justify-center">
            <div className="text-center">
              <Sparkles className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">Emotie Instellingen</p>
              <p className="text-slate-600 text-xs mt-1">Configureer hoe Spark emoties herkent en reageert</p>
            </div>
          </div>
        </div>

      </div>
    </MainLayout>
  );
}

export default EmotiesPage;
