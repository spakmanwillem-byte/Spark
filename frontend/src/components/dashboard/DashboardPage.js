import React, { useState, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { MainLayout, getPageInfo } from '../layout/MainLayout';
import { 
  MessageSquare, Users, BookOpen, Zap, TrendingUp, 
  Clock, Star, Activity, GripVertical, Plus, X
} from 'lucide-react';

// Initial cards configuration
const initialCards = [
  { 
    id: 'conversations', 
    label: 'GESPREKKEN VANDAAG', 
    value: '47', 
    subtext: 'Actief vandaag',
    icon: '💬',
    color: 'blue',
  },
  { 
    id: 'weekly', 
    label: 'DEZE WEEK', 
    value: '312', 
    trend: '+23%',
    icon: '📈',
    color: 'green',
  },
  { 
    id: 'knowledge', 
    label: 'KENNIS ENTRIES', 
    value: '1,847', 
    subtext: '/ 2,500',
    progress: 74,
    icon: '📚',
    color: 'purple',
  },
  { 
    id: 'response', 
    label: 'GEM. RESPONSTIJD', 
    value: '3.8s', 
    subtext: 'Snelle reacties',
    icon: '⚡',
    color: 'amber',
  },
  { 
    id: 'spark-brain', 
    label: 'SPARK BRAIN', 
    value: '218', 
    status: 'connected', 
    icon: '🧠', 
    color: 'slate' 
  },
  { 
    id: 'emotions', 
    label: 'EMOTIES', 
    value: '268', 
    status: 'connected', 
    icon: '💫', 
    color: 'pink' 
  },
  { 
    id: 'triggers', 
    label: 'TRIGGERS', 
    value: '156', 
    subtext: '/ 500', 
    status: 'active', 
    icon: '⚡', 
    color: 'yellow' 
  },
  { 
    id: 'total', 
    label: 'TOTAAL BERICHTEN', 
    value: '5,843', 
    subtext: 'Alle tijd', 
    icon: '📊', 
    color: 'cyan' 
  },
];

export function DashboardPage({ activePage = 'dashboard', onNavigate }) {
  const { user } = useAuth();
  const [cards, setCards] = useState(initialCards);
  const [draggedCard, setDraggedCard] = useState(null);
  const [dragOverIndex, setDragOverIndex] = useState(null);

  // Get current page info
  const pageInfo = getPageInfo(activePage);
  const PageIcon = pageInfo?.icon || Activity;

  // Drag handlers
  const handleDragStart = (e, index) => {
    setDraggedCard(index);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.target.outerHTML);
    e.target.style.opacity = '0.5';
  };

  const handleDragEnd = (e) => {
    e.target.style.opacity = '1';
    setDraggedCard(null);
    setDragOverIndex(null);
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (draggedCard === null) return;
    setDragOverIndex(index);
  };

  const handleDrop = (e, dropIndex) => {
    e.preventDefault();
    if (draggedCard === null || draggedCard === dropIndex) return;

    const newCards = [...cards];
    const draggedItem = newCards[draggedCard];
    newCards.splice(draggedCard, 1);
    newCards.splice(dropIndex, 0, draggedItem);
    setCards(newCards);
    setDraggedCard(null);
    setDragOverIndex(null);
  };

  // Dashboard content
  const renderDashboardContent = () => (
    <>
      {/* Welcome Banner */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 mb-8">
        <p className="text-slate-300">
          Welkom terug, <span className="text-amber-400 font-semibold">{user?.naam}</span>! 
          Dit is wat er vandaag gebeurt.
        </p>
      </div>

      {/* Draggable Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {cards.map((card, index) => (
          <DraggableCard
            key={card.id}
            card={card}
            index={index}
            isDragging={draggedCard === index}
            isDragOver={dragOverIndex === index}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          />
        ))}
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PlaceholderSection title="Recente Gesprekken" buttonText="Bekijk Alles" />
        <PlaceholderSection title="Agenda & Taken" buttonText="Bekijk Agenda" />
      </div>
    </>
  );

  // Empty placeholder content for other pages
  const renderPlaceholderContent = () => (
    <div className="flex-1 flex items-center justify-center min-h-[60vh]">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 bg-slate-800/50 border border-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <PageIcon className="w-10 h-10 text-slate-500" />
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">{pageInfo?.label || 'Module'}</h2>
        <p className="text-slate-400 mb-6">
          Deze module is klaar om ingericht te worden.
        </p>
        <div className="p-6 border-2 border-dashed border-slate-700 rounded-2xl">
          <Plus className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Drag & drop componenten hier</p>
        </div>
      </div>
    </div>
  );

  return (
    <MainLayout activePage={activePage} onNavigate={onNavigate}>
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center">
              <PageIcon className="w-5 h-5 text-amber-400" />
            </div>
            <h1 className="text-2xl font-bold text-white">
              {activePage === 'dashboard' ? 'Dashboard Overview' : pageInfo?.label || 'Module'}
            </h1>
          </div>
          <p className="text-slate-400">
            {activePage === 'dashboard' 
              ? 'Real-time metrics en activiteit van je Spark systeem' 
              : `${pageInfo?.section || ''} → ${pageInfo?.label || ''}`
            }
          </p>
        </div>

        {/* Content */}
        {activePage === 'dashboard' ? renderDashboardContent() : renderPlaceholderContent()}
      </div>
    </MainLayout>
  );
}

// Draggable Card Component
function DraggableCard({ card, index, isDragging, isDragOver, onDragStart, onDragEnd, onDragOver, onDrop }) {
  const colorClasses = {
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/20',
    green: 'from-green-500/20 to-green-600/10 border-green-500/20',
    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/20',
    amber: 'from-amber-500/20 to-amber-600/10 border-amber-500/20',
    slate: 'from-slate-800/80 to-slate-800/40 border-slate-700',
    pink: 'from-pink-500/10 to-pink-600/5 border-pink-500/20',
    yellow: 'from-amber-500/10 to-amber-600/5 border-amber-500/20',
    cyan: 'from-cyan-500/10 to-cyan-600/5 border-cyan-500/20',
  };

  const statusColors = {
    connected: 'bg-green-500/20 text-green-400',
    active: 'bg-amber-500/20 text-amber-400',
  };

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, index)}
      onDragEnd={onDragEnd}
      onDragOver={(e) => onDragOver(e, index)}
      onDrop={(e) => onDrop(e, index)}
      className={`
        bg-gradient-to-br ${colorClasses[card.color]} border rounded-2xl p-5 cursor-move
        transition-all duration-200 group relative
        ${isDragging ? 'opacity-50 scale-95' : ''}
        ${isDragOver ? 'ring-2 ring-amber-500/50 scale-105' : ''}
        hover:border-amber-500/30
      `}
    >
      {/* Drag Handle */}
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <GripVertical className="w-4 h-4 text-slate-500" />
      </div>

      <div className="flex items-start justify-between mb-4">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider pr-6">
          {card.label}
        </p>
        <span className="text-2xl">{card.icon}</span>
      </div>
      
      <div className="flex items-end gap-2 mb-2">
        <span className="text-3xl font-bold text-white">{card.value}</span>
        {card.trend && (
          <span className="text-sm font-medium text-green-400 mb-1">{card.trend}</span>
        )}
        {card.subtext && !card.progress && (
          <span className="text-sm text-slate-500 mb-1">{card.subtext}</span>
        )}
      </div>

      {card.progress && (
        <div className="mt-2">
          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-purple-500 rounded-full transition-all"
              style={{ width: `${card.progress}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mt-1">{card.progress}% gevuld</p>
        </div>
      )}

      {card.status && (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusColors[card.status]}`}>
          <span className="w-1.5 h-1.5 bg-current rounded-full"></span>
          {card.status === 'connected' ? 'CONNECTED' : 'ACTIVE'}
        </span>
      )}

      {card.subtext && !card.progress && !card.status && (
        <p className="text-xs text-slate-500 flex items-center gap-1">
          <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
          {card.subtext}
        </p>
      )}
    </div>
  );
}

// Placeholder Section Component
function PlaceholderSection({ title, buttonText }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <button className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-lg transition-colors">
          {buttonText}
        </button>
      </div>
      <div className="p-6">
        <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center">
          <Plus className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Inhoud wordt hier getoond</p>
          <p className="text-xs text-slate-600 mt-1">Module nog niet geconfigureerd</p>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
