import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { AuthAPI } from '../../api';
import { 
  Zap, LogOut, User, Shield, Star, Clock, MessageSquare, 
  ChevronRight, Settings, Users, BookOpen, Brain
} from 'lucide-react';

// Gradatie kleuren
const gradatieColors = {
  1: 'from-amber-500 to-orange-600',
  2: 'from-purple-500 to-pink-600',
  3: 'from-blue-500 to-cyan-600',
  4: 'from-green-500 to-emerald-600',
  5: 'from-slate-500 to-slate-600',
  6: 'from-slate-600 to-slate-700',
  7: 'from-slate-700 to-slate-800'
};

const gradatieIcons = {
  1: Shield,
  2: Star,
  3: Users,
  4: MessageSquare,
  5: User,
  6: User,
  7: User
};

export function Dashboard() {
  const { user, logout, isAdmin } = useAuth();
  const [gradaties, setGradaties] = useState([]);
  const [systemInfo, setSystemInfo] = useState(null);

  useEffect(() => {
    // Load gradaties
    AuthAPI.getGradaties().then(data => {
      setGradaties(data.gradaties || []);
    }).catch(console.error);

    // Load system info
    import('../../api').then(({ SystemAPI }) => {
      SystemAPI.getModules().then(setSystemInfo).catch(console.error);
    });
  }, []);

  const userGradatie = gradaties.find(g => g.niveau === user?.gradatie);
  const GradatieIcon = gradatieIcons[user?.gradatie] || User;

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return 'Onbekend';
    try {
      return new Date(dateStr).toLocaleDateString('nl-NL', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      });
    } catch {
      return 'Onbekend';
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-xl border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/20">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">Spark Core</h1>
                <p className="text-xs text-slate-500">v2.0</p>
              </div>
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-white">{user?.naam}</p>
                <p className="text-xs text-slate-500">{userGradatie?.titel || `Gradatie ${user?.gradatie}`}</p>
              </div>
              <button
                onClick={logout}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                data-testid="logout-btn"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl border border-slate-700/50 p-6 mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Welkom terug, {user?.naam?.split(' ')[0]}!
              </h2>
              <p className="text-slate-400">
                {isAdmin ? 'Je hebt volledige beheerderstoegang.' : 'Wat wil je vandaag doen?'}
              </p>
            </div>
            <div className={`w-16 h-16 bg-gradient-to-br ${gradatieColors[user?.gradatie] || 'from-slate-600 to-slate-700'} rounded-2xl flex items-center justify-center shadow-lg`}>
              <GradatieIcon className="w-8 h-8 text-white" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* User Profile Card */}
          <div className="lg:col-span-2">
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <User className="w-5 h-5 text-amber-500" />
                  Profiel
                </h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <ProfileField label="Volledige naam" value={user?.volledige_naam || user?.naam} />
                  <ProfileField label="Gradatie" value={`${user?.gradatie} - ${userGradatie?.titel || 'Onbekend'}`} />
                  <ProfileField label="Rol" value={user?.rol} />
                  <ProfileField label="Trust Score" value={`${user?.trust_score || 0}/100`} />
                  <ProfileField label="Gesprekken" value={user?.gesprekken_count || 0} />
                  <ProfileField label="XP" value={user?.xp || 0} />
                  <ProfileField label="Lid sinds" value={formatDate(user?.registered_date)} />
                  <ProfileField label="Laatst actief" value={formatDate(user?.last_active)} />
                </div>
              </div>
            </div>
          </div>

          {/* Stats & Modules */}
          <div className="space-y-6">
            {/* Modules Status */}
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Settings className="w-5 h-5 text-amber-500" />
                  Modules
                </h3>
              </div>
              <div className="p-4 space-y-2">
                <ModuleItem 
                  name="Auth" 
                  status="active" 
                  icon={Shield}
                  description="Inloggen & sessies"
                />
                <ModuleItem 
                  name="Knowledge" 
                  status="planned" 
                  icon={BookOpen}
                  description="Kennisbank"
                />
                <ModuleItem 
                  name="Chat" 
                  status="planned" 
                  icon={Brain}
                  description="Spark Brain"
                />
              </div>
            </div>

            {/* Quick Stats */}
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800 p-6">
              <h3 className="text-sm font-medium text-slate-400 mb-4">Statistieken</h3>
              <div className="space-y-4">
                <StatItem 
                  icon={MessageSquare} 
                  label="Gesprekken" 
                  value={user?.gesprekken_count || 0} 
                />
                <StatItem 
                  icon={Star} 
                  label="XP" 
                  value={user?.xp || 0} 
                />
                <StatItem 
                  icon={Clock} 
                  label="Trust Score" 
                  value={`${user?.trust_score || 0}%`} 
                />
              </div>
            </div>
          </div>
        </div>

        {/* Gradatie Info (Admin only) */}
        {isAdmin && gradaties.length > 0 && (
          <div className="mt-8">
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Shield className="w-5 h-5 text-amber-500" />
                  Gradatie Systeem
                </h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {gradaties.slice(0, 4).map(g => (
                    <div 
                      key={g.niveau} 
                      className={`p-4 rounded-xl bg-gradient-to-br ${gradatieColors[g.niveau]} bg-opacity-10 border border-slate-700/50`}
                    >
                      <div className="text-2xl font-bold text-white mb-1">{g.niveau}</div>
                      <div className="text-sm font-medium text-white/80">{g.titel}</div>
                      <div className="text-xs text-white/50 mt-2 line-clamp-2">{g.beschrijving}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// Helper Components
function ProfileField({ label, value }) {
  return (
    <div>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-sm font-medium text-white">{value || '-'}</p>
    </div>
  );
}

function ModuleItem({ name, status, icon: Icon, description }) {
  const isActive = status === 'active';
  return (
    <div className={`flex items-center gap-3 p-3 rounded-xl ${isActive ? 'bg-slate-800/50' : 'bg-slate-800/20'}`}>
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isActive ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-700/50 text-slate-500'}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1">
        <p className={`text-sm font-medium ${isActive ? 'text-white' : 'text-slate-500'}`}>{name}</p>
        <p className="text-xs text-slate-500">{description}</p>
      </div>
      <div className={`text-xs px-2 py-1 rounded-full ${isActive ? 'bg-green-500/20 text-green-400' : 'bg-slate-700/50 text-slate-500'}`}>
        {isActive ? 'Actief' : 'Gepland'}
      </div>
    </div>
  );
}

function StatItem({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Icon className="w-4 h-4 text-slate-500" />
        <span className="text-sm text-slate-400">{label}</span>
      </div>
      <span className="text-sm font-semibold text-white">{value}</span>
    </div>
  );
}

export default Dashboard;
