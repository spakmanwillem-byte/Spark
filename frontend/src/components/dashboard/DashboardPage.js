import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { MainLayout } from '../layout/MainLayout';
import { 
  MessageSquare, Users, BookOpen, Zap, TrendingUp, 
  Clock, Star, Activity
} from 'lucide-react';

export function DashboardPage() {
  const { user, isAdmin } = useAuth();

  // Stats data - will be dynamic later
  const stats = [
    { 
      id: 'conversations', 
      label: 'GESPREKKEN VANDAAG', 
      value: '47', 
      subtext: 'Actief vandaag',
      icon: MessageSquare,
      color: 'blue',
      trend: null
    },
    { 
      id: 'weekly', 
      label: 'DEZE WEEK', 
      value: '312', 
      trend: '+23%',
      icon: TrendingUp,
      color: 'green',
      chart: true
    },
    { 
      id: 'knowledge', 
      label: 'KENNIS ENTRIES', 
      value: '1,847', 
      subtext: '/ 2,500',
      progress: 74,
      icon: BookOpen,
      color: 'purple'
    },
    { 
      id: 'response', 
      label: 'GEM. RESPONSTIJD', 
      value: '3.8s', 
      subtext: 'Snelle reacties',
      icon: Zap,
      color: 'amber'
    },
  ];

  const moduleStats = [
    { id: 'spark-brain', label: 'SPARK BRAIN', value: '218', status: 'connected', icon: '🧠', color: 'slate' },
    { id: 'emotions', label: 'EMOTIES', value: '268', status: 'connected', icon: '💫', color: 'pink' },
    { id: 'triggers', label: 'TRIGGERS', value: '156', subtext: '/ 500', status: 'active', icon: '⚡', color: 'yellow' },
    { id: 'total', label: 'TOTAAL BERICHTEN', value: '5,843', subtext: 'Alle tijd', icon: '📊', color: 'cyan' },
  ];

  return (
    <MainLayout activePage="dashboard">
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center">
              <Activity className="w-5 h-5 text-amber-400" />
            </div>
            <h1 className="text-2xl font-bold text-white">Dashboard Overview</h1>
          </div>
          <p className="text-slate-400">Real-time metrics en activiteit van je Spark systeem</p>
        </div>

        {/* Welcome Banner */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 mb-8">
          <p className="text-slate-300">
            Welkom terug, <span className="text-amber-400 font-semibold">{user?.naam}</span>! 
            Dit is wat er vandaag gebeurt.
          </p>
        </div>

        {/* Main Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {stats.map(stat => (
            <StatCard key={stat.id} stat={stat} />
          ))}
        </div>

        {/* Module Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {moduleStats.map(stat => (
            <ModuleStatCard key={stat.id} stat={stat} />
          ))}
        </div>

        {/* Bottom Section - Two Columns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Conversations */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
              <h3 className="text-lg font-semibold text-white">Recente Gesprekken</h3>
              <button className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-lg transition-colors">
                Bekijk Alles
              </button>
            </div>
            <div className="p-4">
              {/* Placeholder - will be filled with real data */}
              <div className="space-y-3">
                <ConversationRow 
                  name="Placeholder User" 
                  message="Dit is een placeholder bericht..."
                  platform="Spark"
                  status="active"
                  time="Nu"
                />
                <ConversationRow 
                  name="Test Gebruiker" 
                  message="Nog een placeholder..."
                  platform="Chat"
                  status="active"
                  time="5m"
                />
              </div>
              <div className="mt-4 p-4 border border-dashed border-slate-700 rounded-xl text-center">
                <p className="text-slate-500 text-sm">Gesprekken module nog niet actief</p>
              </div>
            </div>
          </div>

          {/* Upcoming / Activity */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
              <h3 className="text-lg font-semibold text-white">Agenda & Taken</h3>
              <button className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-lg transition-colors">
                Bekijk Agenda
              </button>
            </div>
            <div className="p-4">
              {/* Placeholder */}
              <div className="space-y-3">
                <ActivityRow 
                  title="Placeholder Taak"
                  type="Taak"
                  date="Vandaag"
                  status="pending"
                />
                <ActivityRow 
                  title="Placeholder Afspraak"
                  type="Agenda"
                  date="Morgen"
                  status="confirmed"
                />
              </div>
              <div className="mt-4 p-4 border border-dashed border-slate-700 rounded-xl text-center">
                <p className="text-slate-500 text-sm">Agenda module nog niet actief</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

// Stat Card Component
function StatCard({ stat }) {
  const Icon = stat.icon;
  
  const colorClasses = {
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/20',
    green: 'from-green-500/20 to-green-600/10 border-green-500/20',
    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/20',
    amber: 'from-amber-500/20 to-amber-600/10 border-amber-500/20',
  };

  const iconColorClasses = {
    blue: 'text-blue-400 bg-blue-500/20',
    green: 'text-green-400 bg-green-500/20',
    purple: 'text-purple-400 bg-purple-500/20',
    amber: 'text-amber-400 bg-amber-500/20',
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[stat.color]} border rounded-2xl p-5`}>
      <div className="flex items-start justify-between mb-4">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          {stat.label}
        </p>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${iconColorClasses[stat.color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      
      <div className="flex items-end gap-2">
        <span className="text-3xl font-bold text-white">{stat.value}</span>
        {stat.trend && (
          <span className="text-sm font-medium text-green-400 mb-1">{stat.trend}</span>
        )}
        {stat.subtext && !stat.progress && (
          <span className="text-sm text-slate-500 mb-1">{stat.subtext}</span>
        )}
      </div>

      {stat.progress && (
        <div className="mt-3">
          <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-purple-500 rounded-full transition-all"
              style={{ width: `${stat.progress}%` }}
            />
          </div>
          <p className="text-xs text-slate-500 mt-1">{stat.progress}% gevuld</p>
        </div>
      )}

      {stat.subtext && !stat.progress && (
        <p className="text-xs text-slate-500 mt-2 flex items-center gap-1">
          <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
          {stat.subtext}
        </p>
      )}
    </div>
  );
}

// Module Stat Card
function ModuleStatCard({ stat }) {
  const statusColors = {
    connected: 'bg-green-500/20 text-green-400',
    active: 'bg-amber-500/20 text-amber-400',
    offline: 'bg-slate-700 text-slate-500',
  };

  const bgColors = {
    slate: 'from-slate-800/80 to-slate-800/40',
    pink: 'from-pink-500/10 to-pink-600/5',
    yellow: 'from-amber-500/10 to-amber-600/5',
    cyan: 'from-cyan-500/10 to-cyan-600/5',
  };

  return (
    <div className={`bg-gradient-to-br ${bgColors[stat.color]} border border-slate-800 rounded-2xl p-5`}>
      <div className="flex items-start justify-between mb-4">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          {stat.label}
        </p>
        <span className="text-2xl">{stat.icon}</span>
      </div>
      
      <div className="flex items-end gap-2 mb-3">
        <span className="text-3xl font-bold text-white">{stat.value}</span>
        {stat.subtext && (
          <span className="text-sm text-slate-500 mb-1">{stat.subtext}</span>
        )}
      </div>

      {stat.status && (
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${statusColors[stat.status]}`}>
          <span className="w-1.5 h-1.5 bg-current rounded-full"></span>
          {stat.status === 'connected' ? 'CONNECTED' : stat.status === 'active' ? 'ACTIVE' : 'OFFLINE'}
        </span>
      )}

      {stat.subtext && stat.label === 'TOTAAL BERICHTEN' && (
        <p className="text-xs text-slate-500 flex items-center gap-1">
          <span className="w-1.5 h-1.5 bg-slate-500 rounded-full"></span>
          {stat.subtext}
        </p>
      )}
    </div>
  );
}

// Conversation Row
function ConversationRow({ name, message, platform, status, time }) {
  return (
    <div className="flex items-center gap-4 p-3 bg-slate-800/30 rounded-xl">
      <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center">
        <Users className="w-5 h-5 text-slate-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{name}</p>
        <p className="text-xs text-slate-500 truncate">{message}</p>
      </div>
      <div className="text-right">
        <span className="inline-block px-2 py-0.5 bg-slate-700 text-slate-400 text-xs rounded mb-1">
          {platform}
        </span>
        <p className="text-xs text-slate-500">{time}</p>
      </div>
    </div>
  );
}

// Activity Row
function ActivityRow({ title, type, date, status }) {
  const statusColors = {
    pending: 'bg-amber-500/20 text-amber-400',
    confirmed: 'bg-green-500/20 text-green-400',
  };

  return (
    <div className="flex items-center gap-4 p-3 bg-slate-800/30 rounded-xl">
      <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center">
        <Clock className="w-5 h-5 text-slate-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{title}</p>
        <p className="text-xs text-slate-500">{type}</p>
      </div>
      <div className="text-right">
        <p className="text-xs text-slate-400 mb-1">{date}</p>
        <span className={`inline-block px-2 py-0.5 text-xs rounded ${statusColors[status]}`}>
          {status === 'pending' ? 'PENDING' : 'CONFIRMED'}
        </span>
      </div>
    </div>
  );
}

export default DashboardPage;
