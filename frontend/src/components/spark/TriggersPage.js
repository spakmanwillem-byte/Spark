import React, { useState } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { 
  Zap, Plus, X, Search, Filter, Edit3, Trash2,
  ChevronDown, ChevronRight, Save, Tag
} from 'lucide-react';

// Sample trigger data
const initialTriggerLists = [
  {
    id: 'begroeting',
    name: 'Begroeting',
    description: 'Triggers voor begroetingen',
    color: 'amber',
    triggers: ['hallo', 'hey', 'goedemorgen', 'goedemiddag', 'goedenavond', 'hi', 'hoi', 'yo']
  },
  {
    id: 'afscheid',
    name: 'Afscheid',
    description: 'Triggers voor afscheid nemen',
    color: 'blue',
    triggers: ['doei', 'tot ziens', 'dag', 'later', 'bye', 'tot morgen', 'slaap lekker']
  },
  {
    id: 'vraag',
    name: 'Vraag Herkenning',
    description: 'Triggers voor vragen',
    color: 'purple',
    triggers: ['wat', 'wie', 'waar', 'wanneer', 'waarom', 'hoe', 'welke', 'kun je', 'weet je']
  },
  {
    id: 'emotie-positief',
    name: 'Positieve Emotie',
    description: 'Triggers voor positieve emoties',
    color: 'green',
    triggers: ['blij', 'happy', 'geweldig', 'fantastisch', 'super', 'top', 'leuk', 'fijn', 'dankje']
  },
  {
    id: 'emotie-negatief',
    name: 'Negatieve Emotie',
    description: 'Triggers voor negatieve emoties',
    color: 'red',
    triggers: ['verdrietig', 'boos', 'gefrustreerd', 'teleurgesteld', 'moe', 'stress', 'zorgen']
  },
  {
    id: 'hulp',
    name: 'Hulp Verzoek',
    description: 'Triggers voor hulp vragen',
    color: 'cyan',
    triggers: ['help', 'hulp', 'assistentie', 'probleem', 'werkt niet', 'snap niet', 'uitleg']
  },
];

export function TriggersPage({ onNavigate }) {
  const [triggerLists, setTriggerLists] = useState(initialTriggerLists);
  const [expandedList, setExpandedList] = useState('begroeting');
  const [searchQuery, setSearchQuery] = useState('');
  const [newTrigger, setNewTrigger] = useState('');
  const [editingList, setEditingList] = useState(null);

  const toggleList = (id) => {
    setExpandedList(expandedList === id ? null : id);
  };

  const addTrigger = (listId) => {
    if (!newTrigger.trim()) return;
    
    setTriggerLists(lists => lists.map(list => {
      if (list.id === listId && !list.triggers.includes(newTrigger.toLowerCase().trim())) {
        return { ...list, triggers: [...list.triggers, newTrigger.toLowerCase().trim()] };
      }
      return list;
    }));
    setNewTrigger('');
  };

  const removeTrigger = (listId, trigger) => {
    setTriggerLists(lists => lists.map(list => {
      if (list.id === listId) {
        return { ...list, triggers: list.triggers.filter(t => t !== trigger) };
      }
      return list;
    }));
  };

  const filteredLists = triggerLists.filter(list => 
    list.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    list.triggers.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const totalTriggers = triggerLists.reduce((sum, list) => sum + list.triggers.length, 0);

  return (
    <MainLayout activePage="triggers" onNavigate={onNavigate}>
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Triggers</h1>
                <p className="text-slate-400">SPARK AI → Trigger Lijsten</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-amber-500/20 text-amber-400 text-sm rounded-lg">
                {totalTriggers} triggers
              </span>
              <span className="px-3 py-1 bg-slate-800 text-slate-400 text-sm rounded-lg">
                {triggerLists.length} lijsten
              </span>
            </div>
          </div>
        </div>

        {/* Search & Actions */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Zoek triggers of lijsten..."
              className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-800 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
            />
          </div>
          <button className="px-4 py-3 bg-amber-500/20 text-amber-400 rounded-xl hover:bg-amber-500/30 transition-colors flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Nieuwe Lijst
          </button>
        </div>

        {/* Trigger Lists */}
        <div className="space-y-4">
          {filteredLists.map(list => (
            <TriggerListCard
              key={list.id}
              list={list}
              isExpanded={expandedList === list.id}
              onToggle={() => toggleList(list.id)}
              onAddTrigger={(trigger) => {
                setNewTrigger(trigger);
                addTrigger(list.id);
              }}
              onRemoveTrigger={(trigger) => removeTrigger(list.id, trigger)}
              newTrigger={expandedList === list.id ? newTrigger : ''}
              setNewTrigger={setNewTrigger}
              onSubmitTrigger={() => addTrigger(list.id)}
            />
          ))}
        </div>

        {/* Empty State */}
        {filteredLists.length === 0 && (
          <div className="text-center py-12">
            <Zap className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400">Geen triggers gevonden voor "{searchQuery}"</p>
          </div>
        )}

      </div>
    </MainLayout>
  );
}

// Trigger List Card Component
function TriggerListCard({ list, isExpanded, onToggle, onRemoveTrigger, newTrigger, setNewTrigger, onSubmitTrigger }) {
  const colorClasses = {
    amber: 'border-amber-500/30 bg-amber-500/5',
    blue: 'border-blue-500/30 bg-blue-500/5',
    purple: 'border-purple-500/30 bg-purple-500/5',
    green: 'border-green-500/30 bg-green-500/5',
    red: 'border-red-500/30 bg-red-500/5',
    cyan: 'border-cyan-500/30 bg-cyan-500/5',
  };

  const tagColorClasses = {
    amber: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    purple: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    green: 'bg-green-500/20 text-green-400 border-green-500/30',
    red: 'bg-red-500/20 text-red-400 border-red-500/30',
    cyan: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  };

  const dotColorClasses = {
    amber: 'bg-amber-500',
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
    cyan: 'bg-cyan-500',
  };

  return (
    <div className={`border rounded-2xl overflow-hidden transition-all ${
      isExpanded ? colorClasses[list.color] : 'border-slate-800 bg-slate-900/50'
    }`}>
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-800/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronRight className="w-5 h-5 text-slate-400" />
          )}
          <span className={`w-3 h-3 rounded-full ${dotColorClasses[list.color]}`} />
          <div className="text-left">
            <h3 className="text-white font-medium">{list.name}</h3>
            <p className="text-xs text-slate-500">{list.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-2 py-1 bg-slate-800 text-slate-400 text-xs rounded">
            {list.triggers.length} triggers
          </span>
          <button 
            onClick={(e) => { e.stopPropagation(); }}
            className="p-1.5 text-slate-500 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <Edit3 className="w-4 h-4" />
          </button>
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4">
          {/* Add Trigger Input */}
          <div className="flex gap-2 mb-4">
            <div className="flex-1 relative">
              <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={newTrigger}
                onChange={(e) => setNewTrigger(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && onSubmitTrigger()}
                placeholder="Nieuw trigger woord toevoegen..."
                className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
              />
            </div>
            <button
              onClick={onSubmitTrigger}
              className="px-4 py-2 bg-amber-500/20 text-amber-400 rounded-xl hover:bg-amber-500/30 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Toevoegen
            </button>
          </div>

          {/* Triggers Grid */}
          <div className="flex flex-wrap gap-2">
            {list.triggers.map((trigger, idx) => (
              <div
                key={idx}
                className={`group flex items-center gap-2 px-3 py-1.5 border rounded-lg ${tagColorClasses[list.color]}`}
              >
                <span className="text-sm">{trigger}</span>
                <button
                  onClick={() => onRemoveTrigger(trigger)}
                  className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-red-500/20 rounded transition-all"
                >
                  <X className="w-3 h-3 text-red-400" />
                </button>
              </div>
            ))}
          </div>

          {/* Empty State */}
          {list.triggers.length === 0 && (
            <div className="text-center py-6 text-slate-500 text-sm">
              Geen triggers in deze lijst. Voeg er een toe!
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default TriggersPage;
