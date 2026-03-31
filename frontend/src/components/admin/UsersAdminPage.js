import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { AuthAPI } from '../../api';
import { 
  Users, User, Star, Calendar, BarChart2, Edit3, 
  Trash2, Shield, Clock, MessageSquare, Award,
  TrendingUp, Heart, ChevronRight, Search, Plus,
  Check, X, Save
} from 'lucide-react';

export function UsersAdminPage({ onNavigate }) {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [gradaties, setGradaties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState({});

  // Load users and gradaties
  useEffect(() => {
    const loadData = async () => {
      try {
        const [usersRes, gradatiesRes] = await Promise.all([
          AuthAPI.getUsers(),
          AuthAPI.getGradaties()
        ]);
        setUsers(usersRes.users || []);
        setGradaties(gradatiesRes.gradaties || []);
        if (usersRes.users?.length > 0) {
          setSelectedUser(usersRes.users[0]);
        }
      } catch (err) {
        console.error('Failed to load users:', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleSelectUser = (user) => {
    setSelectedUser(user);
    setEditMode(false);
    setEditForm({});
  };

  const handleEditStart = () => {
    setEditMode(true);
    setEditForm({
      naam: selectedUser.naam,
      volledige_naam: selectedUser.volledige_naam || '',
      rol: selectedUser.rol || '',
      gradatie: selectedUser.gradatie || 7,
    });
  };

  const handleEditSave = async () => {
    try {
      await AuthAPI.updateUser(selectedUser.id, editForm);
      // Refresh users
      const usersRes = await AuthAPI.getUsers();
      setUsers(usersRes.users || []);
      const updated = usersRes.users.find(u => u.id === selectedUser.id);
      if (updated) setSelectedUser(updated);
      setEditMode(false);
    } catch (err) {
      console.error('Failed to update user:', err);
    }
  };

  const getGradatieInfo = (niveau) => {
    return gradaties.find(g => g.niveau === niveau) || { titel: 'Onbekend', niveau };
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Onbekend';
    try {
      return new Date(dateStr).toLocaleDateString('nl-NL', {
        day: 'numeric', month: 'short', year: 'numeric'
      });
    } catch {
      return 'Onbekend';
    }
  };

  // Calculate user stats
  const getUserStats = (user) => ({
    gesprekken: user.gesprekken_count || 0,
    trustScore: user.trust_score || 0,
    xp: user.xp || 0,
    daysActive: user.registered_date 
      ? Math.floor((Date.now() - new Date(user.registered_date).getTime()) / (1000 * 60 * 60 * 24))
      : 0
  });

  if (loading) {
    return (
      <MainLayout activePage="users" onNavigate={onNavigate}>
        <div className="flex items-center justify-center h-full">
          <div className="w-12 h-12 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
        </div>
      </MainLayout>
    );
  }

  const stats = selectedUser ? getUserStats(selectedUser) : null;

  return (
    <MainLayout activePage="users" onNavigate={onNavigate}>
      <div className="h-full flex">
        {/* Left Panel - Users List */}
        <div className="w-80 bg-slate-900/50 border-r border-slate-800 flex flex-col">
          {/* Search Header */}
          <div className="p-4 border-b border-slate-800">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center">
                <Users className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">Gebruikers</h1>
                <p className="text-xs text-slate-500">{users.length} gebruikers</p>
              </div>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input 
                type="text"
                placeholder="Zoek gebruiker..."
                className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
              />
            </div>
          </div>

          {/* Users List */}
          <div className="flex-1 overflow-y-auto p-2">
            {users.map(user => (
              <button
                key={user.id}
                onClick={() => handleSelectUser(user)}
                className={`w-full flex items-center gap-3 p-3 rounded-xl mb-1 transition-all ${
                  selectedUser?.id === user.id 
                    ? 'bg-amber-500/10 border border-amber-500/30' 
                    : 'hover:bg-slate-800/50'
                }`}
              >
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold ${
                  user.gradatie === 1 ? 'bg-gradient-to-br from-amber-500 to-orange-600' :
                  user.gradatie === 2 ? 'bg-gradient-to-br from-purple-500 to-pink-600' :
                  user.gradatie <= 4 ? 'bg-gradient-to-br from-blue-500 to-cyan-600' :
                  'bg-gradient-to-br from-slate-600 to-slate-700'
                }`}>
                  {user.naam?.charAt(0) || 'U'}
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-white truncate">{user.naam}</p>
                  <p className="text-xs text-slate-500">{getGradatieInfo(user.gradatie).titel}</p>
                </div>
                <ChevronRight className={`w-4 h-4 transition-colors ${
                  selectedUser?.id === user.id ? 'text-amber-400' : 'text-slate-600'
                }`} />
              </button>
            ))}
          </div>
        </div>

        {/* Right Panel - User Details */}
        {selectedUser && (
          <div className="flex-1 overflow-y-auto p-6">
            <div className="max-w-5xl mx-auto">
              {/* Top Row */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                {/* User Profile Card */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <div className="flex items-start justify-between mb-4">
                    <Heart className="w-5 h-5 text-slate-600 hover:text-red-400 cursor-pointer transition-colors" />
                    {!editMode && (
                      <button onClick={handleEditStart} className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                        <Edit3 className="w-4 h-4 text-slate-400" />
                      </button>
                    )}
                  </div>
                  
                  <div className="text-center mb-4">
                    <div className={`w-20 h-20 mx-auto rounded-2xl flex items-center justify-center text-2xl font-bold text-white mb-3 ${
                      selectedUser.gradatie === 1 ? 'bg-gradient-to-br from-amber-500 to-orange-600' :
                      selectedUser.gradatie === 2 ? 'bg-gradient-to-br from-purple-500 to-pink-600' :
                      selectedUser.gradatie <= 4 ? 'bg-gradient-to-br from-blue-500 to-cyan-600' :
                      'bg-gradient-to-br from-slate-600 to-slate-700'
                    }`}>
                      {selectedUser.naam?.charAt(0) || 'U'}
                    </div>
                    
                    {editMode ? (
                      <input 
                        type="text"
                        value={editForm.naam || ''}
                        onChange={(e) => setEditForm({...editForm, naam: e.target.value})}
                        className="w-full text-center bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white mb-2"
                      />
                    ) : (
                      <h2 className="text-xl font-bold text-white mb-1">{selectedUser.naam}</h2>
                    )}
                    
                    <p className="text-sm text-slate-400 mb-3">
                      {editMode ? (
                        <input 
                          type="text"
                          value={editForm.volledige_naam || ''}
                          onChange={(e) => setEditForm({...editForm, volledige_naam: e.target.value})}
                          placeholder="Volledige naam"
                          className="w-full text-center bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white"
                        />
                      ) : (
                        selectedUser.volledige_naam || selectedUser.rol || 'Geen beschrijving'
                      )}
                    </p>
                    
                    {/* Star Rating based on trust_score */}
                    <div className="flex items-center justify-center gap-1">
                      {[1, 2, 3, 4, 5].map(star => (
                        <Star 
                          key={star} 
                          className={`w-4 h-4 ${
                            star <= Math.ceil(stats.trustScore / 20) 
                              ? 'text-amber-400 fill-amber-400' 
                              : 'text-slate-600'
                          }`} 
                        />
                      ))}
                    </div>
                  </div>

                  {editMode && (
                    <div className="flex gap-2 mt-4">
                      <button 
                        onClick={handleEditSave}
                        className="flex-1 py-2 bg-green-500/20 text-green-400 rounded-lg flex items-center justify-center gap-2 hover:bg-green-500/30 transition-colors"
                      >
                        <Save className="w-4 h-4" /> Opslaan
                      </button>
                      <button 
                        onClick={() => setEditMode(false)}
                        className="flex-1 py-2 bg-slate-800 text-slate-400 rounded-lg flex items-center justify-center gap-2 hover:bg-slate-700 transition-colors"
                      >
                        <X className="w-4 h-4" /> Annuleren
                      </button>
                    </div>
                  )}
                </div>

                {/* Statistics Card */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-amber-400" />
                    Statistieken
                  </h3>
                  
                  <div className="space-y-4">
                    <ProgressBar label="Trust Score" value={stats.trustScore} max={100} color="amber" />
                    <ProgressBar label="XP Level" value={Math.min(stats.xp, 1000)} max={1000} color="purple" />
                    <ProgressBar label="Activiteit" value={Math.min(stats.gesprekken * 5, 100)} max={100} color="cyan" />
                    <ProgressBar label="Betrokkenheid" value={Math.min(stats.daysActive, 100)} max={100} color="red" />
                  </div>
                </div>

                {/* Schedule Card */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-amber-400" />
                    Activiteit
                  </h3>
                  
                  {/* Week Calendar */}
                  <div className="bg-slate-800 rounded-xl p-3 mb-4">
                    <div className="grid grid-cols-7 gap-1 text-center">
                      {['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'].map((day, i) => (
                        <div key={day} className="text-xs text-slate-500">{day}</div>
                      ))}
                      {[17, 18, 19, 20, 21, 22, 23].map((date, i) => (
                        <div 
                          key={date}
                          className={`py-2 rounded-lg text-sm ${
                            date === 20 
                              ? 'bg-amber-500 text-white font-bold' 
                              : 'text-slate-400'
                          }`}
                        >
                          {date}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between text-slate-400">
                      <span>Lid sinds</span>
                      <span className="text-white">{formatDate(selectedUser.registered_date)}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Laatst actief</span>
                      <span className="text-white">{formatDate(selectedUser.last_active)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Middle Row */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                {/* XP Card */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <p className="text-xs text-slate-500 mb-1">Experience Points</p>
                  <div className="flex items-end gap-2 mb-2">
                    <span className="text-4xl font-bold text-white">{stats.xp}</span>
                    <span className="text-slate-400 mb-1">XP</span>
                    <span className="text-green-400 text-sm mb-1 flex items-center">
                      <TrendingUp className="w-3 h-3 mr-1" />
                      +{Math.floor(stats.gesprekken * 2)}%
                    </span>
                  </div>
                  <div className="inline-block px-3 py-1 bg-slate-800 rounded-lg text-xs text-slate-400">
                    Level {Math.floor(stats.xp / 100) + 1}
                  </div>
                </div>

                {/* Activity Graph */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <p className="text-xs text-slate-500 mb-3">Gesprekken per week</p>
                  <div className="flex items-end justify-between h-24 gap-1">
                    {[35, 45, 30, 60, 45, 70, 55, 80, 65, 75].map((height, i) => (
                      <div 
                        key={i}
                        className="flex-1 bg-slate-700 rounded-t transition-all hover:bg-amber-500"
                        style={{ height: `${height}%` }}
                      />
                    ))}
                  </div>
                  <div className="flex justify-between mt-2">
                    <div className="w-12 h-12 border-4 border-slate-700 rounded-full flex items-center justify-center">
                      <span className="text-xs text-slate-400">50%</span>
                    </div>
                    <div className="w-12 h-12 border-4 border-red-500/50 rounded-full flex items-center justify-center">
                      <span className="text-xs text-red-400">25%</span>
                    </div>
                  </div>
                </div>

                {/* Gradatie / Ranks */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Award className="w-4 h-4 text-amber-400" />
                    Gradatie
                  </h3>
                  <div className="space-y-2">
                    {[1, 2, 3, 4, 5].map(level => (
                      <div key={level} className="flex items-center gap-3">
                        <div className="flex">
                          {[1, 2, 3, 4, 5].map(star => (
                            <Star 
                              key={star}
                              className={`w-3 h-3 ${
                                star <= level 
                                  ? 'text-amber-400 fill-amber-400' 
                                  : 'text-slate-700'
                              }`}
                            />
                          ))}
                        </div>
                        <span className={`text-sm ${
                          (8 - selectedUser.gradatie) >= level ? 'text-white' : 'text-slate-600'
                        }`}>
                          {level}/5
                        </span>
                        {(8 - selectedUser.gradatie) === level && (
                          <span className="text-xs text-amber-400">← Huidig</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Bottom Row */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Action Buttons */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-white mb-4">Acties</h3>
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <button className="py-3 bg-amber-500/20 text-amber-400 rounded-xl font-medium hover:bg-amber-500/30 transition-colors flex items-center justify-center gap-2">
                      <MessageSquare className="w-4 h-4" /> Bericht
                    </button>
                    <button className="py-3 bg-slate-800 text-slate-300 rounded-xl font-medium hover:bg-slate-700 transition-colors flex items-center justify-center gap-2">
                      <Shield className="w-4 h-4" /> Rechten
                    </button>
                    <button className="py-3 bg-slate-800 text-slate-300 rounded-xl font-medium hover:bg-slate-700 transition-colors flex items-center justify-center gap-2">
                      <Clock className="w-4 h-4" /> Historie
                    </button>
                    <button className="py-3 bg-red-500/10 text-red-400 rounded-xl font-medium hover:bg-red-500/20 transition-colors flex items-center justify-center gap-2">
                      <Trash2 className="w-4 h-4" /> Verwijder
                    </button>
                  </div>
                  
                  {/* Search */}
                  <div className="relative">
                    <input 
                      type="text"
                      placeholder="Zoek in gebruikersdata..."
                      className="w-full pl-4 pr-10 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
                    />
                    <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                  </div>
                </div>

                {/* Edit Form */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Edit3 className="w-4 h-4 text-amber-400" />
                    Gebruiker Bewerken
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Rol / Functie</label>
                      <input 
                        type="text"
                        value={editMode ? editForm.rol || '' : selectedUser.rol || ''}
                        onChange={(e) => editMode && setEditForm({...editForm, rol: e.target.value})}
                        disabled={!editMode}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none disabled:opacity-50"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Gradatie</label>
                      <select 
                        value={editMode ? editForm.gradatie : selectedUser.gradatie}
                        onChange={(e) => editMode && setEditForm({...editForm, gradatie: parseInt(e.target.value)})}
                        disabled={!editMode}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:border-amber-500 focus:outline-none disabled:opacity-50"
                      >
                        {gradaties.map(g => (
                          <option key={g.niveau} value={g.niveau}>
                            {g.niveau} - {g.titel}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center gap-2">
                      <input type="checkbox" id="masterkey" className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-amber-500" />
                      <label htmlFor="masterkey" className="text-sm text-slate-400">Masterkey toegang</label>
                    </div>

                    <button 
                      onClick={editMode ? handleEditSave : handleEditStart}
                      className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-xl transition-colors"
                    >
                      {editMode ? 'Wijzigingen Opslaan' : 'Bewerken'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}

// Progress Bar Component
function ProgressBar({ label, value, max, color }) {
  const percentage = Math.min((value / max) * 100, 100);
  
  const colorClasses = {
    amber: 'bg-amber-500',
    purple: 'bg-purple-500',
    cyan: 'bg-cyan-500',
    red: 'bg-red-500',
    green: 'bg-green-500',
  };

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="text-white">{Math.round(percentage)}%</span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div 
          className={`h-full ${colorClasses[color]} rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

export default UsersAdminPage;
