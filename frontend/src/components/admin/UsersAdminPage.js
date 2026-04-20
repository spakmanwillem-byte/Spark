import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { AuthAPI } from '../../api';
import { 
  Users, User, Star, Calendar, BarChart2, Edit3, 
  Trash2, Shield, Clock, MessageSquare, Award,
  TrendingUp, Heart, ChevronRight, ChevronDown, Search, Plus,
  Check, X, Save, Sparkles, Lock, BookOpen, Zap, Filter, Bot
} from 'lucide-react';

export function UsersAdminPage({ onNavigate }) {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [gradaties, setGradaties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState({});

  // Create new user modal
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ naam: '', sleutelwoord: '', volledige_naam: '' });
  const [createError, setCreateError] = useState(null);
  const [creating, setCreating] = useState(false);

  // Detail tab (overview | persons | logs)
  const [detailTab, setDetailTab] = useState('overview');

  // Persoonskaarten per user (juist schema: persons, gradatie, relatie, tags)
  const [personCards, setPersonCards] = useState([]);
  const [cardLoading, setCardLoading] = useState(false);

  // Gesprekslogs per user
  const [chatLogs, setChatLogs] = useState([]);
  const [logStats, setLogStats] = useState(null);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logSearch, setLogSearch] = useState('');
  const [logChannel, setLogChannel] = useState(null);
  const [expandedLogId, setExpandedLogId] = useState(null);

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
    setDetailTab('overview');
  };

  // Load persoonskaarten op tab-switch
  useEffect(() => {
    if (detailTab !== 'persons' || !selectedUser) return;
    const load = async () => {
      setCardLoading(true);
      try {
        const API = process.env.REACT_APP_BACKEND_URL;
        const res = await fetch(`${API}/api/persons/cards/${selectedUser.id}`).then(r => r.json());
        setPersonCards(res.persons || []);
      } catch (e) { console.error(e); }
      setCardLoading(false);
    };
    load();
  }, [detailTab, selectedUser]);

  // Load gesprekslogs op tab-switch
  useEffect(() => {
    if (detailTab !== 'logs' || !selectedUser) return;
    const load = async () => {
      setLogsLoading(true);
      try {
        const API = process.env.REACT_APP_BACKEND_URL;
        const params = new URLSearchParams();
        params.append('limit', '100');
        if (logSearch) params.append('search', logSearch);
        if (logChannel) params.append('channel', logChannel);
        const [logsRes, statsRes] = await Promise.all([
          fetch(`${API}/api/chat/logs/${selectedUser.id}?${params}`).then(r => r.json()),
          fetch(`${API}/api/chat/logs/${selectedUser.id}/stats`).then(r => r.json()),
        ]);
        setChatLogs(logsRes.conversations || []);
        setLogStats(statsRes);
      } catch (e) { console.error(e); }
      setLogsLoading(false);
    };
    load();
  }, [detailTab, selectedUser, logSearch, logChannel]);

  const handleCreateUser = async () => {
    setCreateError(null);
    if (!createForm.naam.trim() || !createForm.sleutelwoord.trim()) {
      setCreateError('Naam en sleutelwoord zijn verplicht');
      return;
    }
    setCreating(true);
    try {
      await AuthAPI.createUser(
        createForm.naam.trim(),
        createForm.sleutelwoord,
        createForm.volledige_naam.trim() || null
      );
      const usersRes = await AuthAPI.getUsers();
      setUsers(usersRes.users || []);
      const newUser = (usersRes.users || []).find(u => u.naam === createForm.naam.trim());
      if (newUser) setSelectedUser(newUser);
      setCreateForm({ naam: '', sleutelwoord: '', volledige_naam: '' });
      setShowCreate(false);
    } catch (err) {
      setCreateError(err?.response?.data?.detail || 'Kon gebruiker niet aanmaken');
    }
    setCreating(false);
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
            <div className="flex items-center justify-between gap-3 mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center">
                  <Users className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-lg font-bold text-white">Gebruikers</h1>
                  <p className="text-xs text-slate-500">{users.length} gebruikers</p>
                </div>
              </div>
              <button
                data-testid="new-user-btn"
                onClick={() => { setShowCreate(true); setCreateError(null); }}
                className="p-2 bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 rounded-lg transition-colors"
                title="Nieuwe gebruiker aanmaken"
              >
                <Plus className="w-4 h-4" />
              </button>
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
              {/* Detail tabs */}
              <div className="flex items-center gap-1 mb-4 border-b border-slate-800">
                <button data-testid="tab-overview" onClick={() => setDetailTab('overview')}
                  className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
                    detailTab === 'overview' ? 'text-amber-400 border-amber-400' : 'text-slate-500 border-transparent hover:text-white'
                  }`}>
                  Overzicht
                </button>
                <button data-testid="tab-persons" onClick={() => setDetailTab('persons')}
                  className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 ${
                    detailTab === 'persons' ? 'text-amber-400 border-amber-400' : 'text-slate-500 border-transparent hover:text-white'
                  }`}>
                  <Heart className="w-3.5 h-3.5" /> Persoonskaarten
                </button>
                <button data-testid="tab-logs" onClick={() => setDetailTab('logs')}
                  className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 ${
                    detailTab === 'logs' ? 'text-amber-400 border-amber-400' : 'text-slate-500 border-transparent hover:text-white'
                  }`}>
                  <MessageSquare className="w-3.5 h-3.5" /> Gesprekslog
                </button>
              </div>

              {detailTab === 'persons' && (
                <PersonCardsView user={selectedUser} cards={personCards} loading={cardLoading} />
              )}

              {detailTab === 'logs' && (
                <ChatLogsView
                  user={selectedUser}
                  logs={chatLogs}
                  stats={logStats}
                  loading={logsLoading}
                  search={logSearch}
                  setSearch={setLogSearch}
                  channel={logChannel}
                  setChannel={setLogChannel}
                  expandedId={expandedLogId}
                  setExpandedId={setExpandedLogId}
                />
              )}

              {detailTab === 'overview' && (
              <>
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

                {/* Gradatie Overzicht */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Award className="w-4 h-4 text-amber-400" />
                    Gradatie Systeem
                  </h3>
                  <div className="space-y-1.5">
                    {gradaties.map(g => {
                      const isHuidig = g.niveau === selectedUser.gradatie;
                      const gColor = g.niveau === 1 ? '#f59e0b' : g.niveau === 2 ? '#ec4899' : g.niveau <= 4 ? '#3b82f6' : g.niveau <= 5 ? '#22c55e' : '#64748b';
                      return (
                        <div key={g.niveau} className={`flex items-center gap-2 p-2 rounded-lg transition-colors ${isHuidig ? 'border' : ''}`}
                          style={isHuidig ? { background: `${gColor}10`, borderColor: `${gColor}30` } : {}}>
                          <div className="w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold flex-shrink-0" style={{ background: `${gColor}15`, color: gColor }}>
                            {g.niveau}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`text-xs font-medium truncate ${isHuidig ? 'text-white' : 'text-slate-400'}`}>{g.titel}</p>
                            <p className="text-[9px] text-slate-600 truncate">{g.toegang?.length || 0} rechten</p>
                          </div>
                          {isHuidig && <span className="text-[9px] px-1.5 py-0.5 rounded font-medium" style={{ background: `${gColor}15`, color: gColor }}>Huidig</span>}
                        </div>
                      );
                    })}
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

                {/* Edit Form - Personalia */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                    <Edit3 className="w-4 h-4 text-amber-400" />
                    Personalia Bewerken
                  </h3>
                  
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Naam</label>
                      <input 
                        data-testid="edit-naam"
                        type="text"
                        value={editMode ? editForm.naam || '' : selectedUser.naam || ''}
                        onChange={(e) => editMode && setEditForm({...editForm, naam: e.target.value})}
                        disabled={!editMode}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none disabled:opacity-50 text-sm"
                      />
                    </div>

                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Volledige Naam</label>
                      <input 
                        data-testid="edit-volledige-naam"
                        type="text"
                        value={editMode ? editForm.volledige_naam || '' : selectedUser.volledige_naam || ''}
                        onChange={(e) => editMode && setEditForm({...editForm, volledige_naam: e.target.value})}
                        disabled={!editMode}
                        placeholder="Volledige naam"
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none disabled:opacity-50 text-sm"
                      />
                    </div>

                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Rol / Functie</label>
                      <input 
                        data-testid="edit-rol"
                        type="text"
                        value={editMode ? editForm.rol || '' : selectedUser.rol || ''}
                        onChange={(e) => editMode && setEditForm({...editForm, rol: e.target.value})}
                        disabled={!editMode}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none disabled:opacity-50 text-sm"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs text-slate-400 mb-1">Gradatie</label>
                      <select 
                        data-testid="edit-gradatie"
                        value={editMode ? editForm.gradatie : selectedUser.gradatie}
                        onChange={(e) => editMode && setEditForm({...editForm, gradatie: parseInt(e.target.value)})}
                        disabled={!editMode}
                        className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-xl text-white focus:border-amber-500 focus:outline-none disabled:opacity-50 text-sm"
                      >
                        {gradaties.map(g => (
                          <option key={g.niveau} value={g.niveau}>
                            G{g.niveau} — {g.titel}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Gradatie info voor geselecteerde */}
                    {(() => {
                      const g = getGradatieInfo(editMode ? editForm.gradatie : selectedUser.gradatie);
                      return g?.beschrijving ? (
                        <div className="p-3 bg-slate-800/30 rounded-lg border border-slate-700/30">
                          <p className="text-[10px] text-amber-400 mb-1">{g.titel}</p>
                          <p className="text-[11px] text-slate-400">{g.beschrijving}</p>
                          {g.toegang?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {g.toegang.map((t, i) => (
                                <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">{t}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      ) : null;
                    })()}

                    <button 
                      data-testid="edit-save-btn"
                      onClick={editMode ? handleEditSave : handleEditStart}
                      className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-xl transition-colors text-sm"
                    >
                      {editMode ? 'Wijzigingen Opslaan' : 'Bewerken'}
                    </button>
                  </div>
                </div>
              </div>
              </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setShowCreate(false)}>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Plus className="w-5 h-5 text-amber-400" /> Nieuwe gebruiker
              </h3>
              <button onClick={() => setShowCreate(false)} className="text-slate-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Naam *</label>
                <input data-testid="new-user-naam" type="text" value={createForm.naam}
                  onChange={e => setCreateForm({ ...createForm, naam: e.target.value })}
                  placeholder="Voornaam of nickname"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Volledige naam</label>
                <input data-testid="new-user-volledige" type="text" value={createForm.volledige_naam}
                  onChange={e => setCreateForm({ ...createForm, volledige_naam: e.target.value })}
                  placeholder="Optioneel"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Sleutelwoord *</label>
                <input data-testid="new-user-sleutel" type="password" value={createForm.sleutelwoord}
                  onChange={e => setCreateForm({ ...createForm, sleutelwoord: e.target.value })}
                  placeholder="Persoonlijk wachtwoord"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
              </div>
              {createError && <p className="text-xs text-red-400">{createError}</p>}
              <button data-testid="create-user-submit" onClick={handleCreateUser} disabled={creating}
                className="w-full py-2.5 bg-amber-500 hover:bg-amber-600 text-white rounded-lg font-medium text-sm transition-colors disabled:opacity-50">
                {creating ? 'Aanmaken...' : 'Gebruiker aanmaken'}
              </button>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}

// (PersonCardsTab verwijderd — was dubbel; PersoonsPage heeft nu admin-modus)

// =====================================================
// Persoonskaarten weergave — juiste schema (persons met naam/relatie/gradatie/tags)
// =====================================================
const GRADATIE_COLORS = {
  1: { bg: 'bg-red-500/10', text: 'text-red-400', label: 'Beheerder' },
  2: { bg: 'bg-amber-500/10', text: 'text-amber-400', label: 'Familie' },
  3: { bg: 'bg-green-500/10', text: 'text-green-400', label: 'Vriend' },
  4: { bg: 'bg-blue-500/10', text: 'text-blue-400', label: 'Kennis' },
  5: { bg: 'bg-slate-500/10', text: 'text-slate-400', label: 'Onbekend' },
};

function PersonCardsView({ user, cards, loading }) {
  if (loading) return <div className="text-center py-12 text-xs text-slate-500">Persoonskaarten laden...</div>;
  if (!cards || cards.length === 0) {
    return (
      <div className="text-center py-12 bg-slate-900/30 border border-slate-800 rounded-xl">
        <Heart className="w-10 h-10 text-slate-700 mx-auto mb-3" />
        <p className="text-sm text-slate-400 mb-1">{user.naam} heeft nog geen persoonskaarten</p>
        <p className="text-xs text-slate-600">Kaarten worden aangemaakt wanneer {user.naam} personen noemt in gesprekken</p>
      </div>
    );
  }
  const byGradatie = cards.reduce((acc, c) => {
    const g = c.gradatie || 5;
    if (!acc[g]) acc[g] = [];
    acc[g].push(c);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-white">Persoonskaarten van <span className="text-amber-400">{user.naam}</span></h3>
        <p className="text-xs text-slate-500 mt-0.5">{cards.length} relaties, gegroepeerd per gradatie</p>
      </div>
      {[1, 2, 3, 4, 5].map(g => {
        const group = byGradatie[g];
        if (!group || group.length === 0) return null;
        const style = GRADATIE_COLORS[g];
        return (
          <div key={g}>
            <p className={`text-[10px] uppercase tracking-wider mb-2 font-semibold ${style.text}`}>
              Gradatie {g} — {style.label} ({group.length})
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {group.map(p => (
                <div key={p.id} data-testid={`person-${p.id}`}
                  className={`${style.bg} border border-slate-800 rounded-xl p-3 hover:border-slate-700 transition-colors`}>
                  <div className="flex items-start gap-3">
                    <div className="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center flex-shrink-0">
                      <span className={`text-sm font-bold ${style.text}`}>{(p.naam || '?').charAt(0).toUpperCase()}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-white truncate">
                        {p.volledige_naam || p.naam}
                        {p.is_user && <span className="ml-1.5 text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">USER</span>}
                      </p>
                      {p.relatie && <p className={`text-xs ${style.text}`}>{p.relatie}</p>}
                      {p.notes && <p className="text-xs text-slate-500 mt-1 line-clamp-2">{p.notes}</p>}
                      {p.tags && p.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {p.tags.map((t, i) => (
                            <span key={i} className="text-[9px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded">{t}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// =====================================================
// Gesprekslog weergave in user detail panel
// =====================================================
const CHANNEL_STYLES = {
  spark: { icon: Sparkles, color: '#f59e0b', label: 'Spark' },
  community: { icon: Users, color: '#a855f7', label: 'Community' },
  prive: { icon: Lock, color: '#06b6d4', label: 'Privé' },
};

function ChatLogsView({ user, logs, stats, loading, search, setSearch, channel, setChannel, expandedId, setExpandedId }) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-white">Gesprekslog van <span className="text-amber-400">{user.naam}</span></h3>
        <p className="text-xs text-slate-500 mt-0.5">{stats?.total || 0} gesprekken gelogd • gem. {stats?.avg_words || 0} woorden</p>
      </div>

      {/* Stats cards */}
      {stats && stats.total > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <div className="bg-slate-800/40 rounded-lg px-3 py-2">
            <p className="text-[9px] text-slate-500 uppercase">Spark</p>
            <p className="text-sm font-bold text-amber-400">{stats.channels?.spark || 0}</p>
          </div>
          <div className="bg-slate-800/40 rounded-lg px-3 py-2">
            <p className="text-[9px] text-slate-500 uppercase">Community</p>
            <p className="text-sm font-bold text-purple-400">{stats.channels?.community || 0}</p>
          </div>
          <div className="bg-slate-800/40 rounded-lg px-3 py-2">
            <p className="text-[9px] text-slate-500 uppercase">Snaps gegenereerd</p>
            <p className="text-sm font-bold text-blue-400">{stats.snap_count || 0}</p>
          </div>
          <div className="bg-slate-800/40 rounded-lg px-3 py-2">
            <p className="text-[9px] text-slate-500 uppercase">Triggers</p>
            <p className="text-sm font-bold text-white">{Object.values(stats.triggers || {}).reduce((a, b) => a + b, 0)}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[180px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Zoek in berichten..."
            className="w-full pl-8 pr-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
        </div>
        {Object.entries(CHANNEL_STYLES).map(([key, cfg]) => {
          const Icon = cfg.icon;
          const active = channel === key;
          return (
            <button key={key} onClick={() => setChannel(active ? null : key)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                active ? 'text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
              style={active ? { background: cfg.color } : undefined}>
              <Icon className="w-3 h-3" /> {cfg.label}
            </button>
          );
        })}
      </div>

      {/* Logs */}
      {loading ? (
        <div className="text-center py-12 text-xs text-slate-500">Logs laden...</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 bg-slate-900/30 border border-slate-800 rounded-xl">
          <MessageSquare className="w-10 h-10 text-slate-700 mx-auto mb-3" />
          <p className="text-sm text-slate-400">
            {stats?.total === 0 ? `${user.naam} heeft nog geen gesprekken` : 'Geen gesprekken matchen filter'}
          </p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
          {logs.map(c => {
            const cfg = CHANNEL_STYLES[c.channel] || CHANNEL_STYLES.spark;
            const Icon = cfg.icon;
            const analysis = c.analysis || {};
            const expanded = expandedId === c.id;
            const ts = new Date(c.timestamp).toLocaleString('nl-NL', { dateStyle: 'short', timeStyle: 'short' });
            return (
              <div key={c.id} className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
                <button onClick={() => setExpandedId(expanded ? null : c.id)}
                  className="w-full flex items-start gap-3 p-3 text-left hover:bg-slate-900/80 transition-colors">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${cfg.color}20` }}>
                    <Icon className="w-3 h-3" style={{ color: cfg.color }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[10px] font-medium" style={{ color: cfg.color }}>#{c.metadata?.gesprek_nummer}</span>
                      <span className="text-[10px] text-slate-500">{ts}</span>
                      {analysis.trigger_type && <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">{analysis.trigger_type}</span>}
                      {(analysis.snap_suggestions || []).length > 0 && <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400">snap</span>}
                      {(analysis.knowledge_matches || []).length > 0 && <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">match</span>}
                    </div>
                    <p className="text-sm text-white truncate">{c.user_message}</p>
                    <p className="text-xs text-slate-400 truncate mt-0.5">→ {c.spark_response}</p>
                  </div>
                  {expanded ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                </button>
                {expanded && (
                  <div className="border-t border-slate-800 p-3 bg-slate-950/40 space-y-2">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      <div>
                        <p className="text-[9px] text-slate-500 uppercase mb-1">{c.user_naam}</p>
                        <p className="text-xs text-white bg-slate-800/50 p-2 rounded whitespace-pre-wrap">{c.user_message}</p>
                      </div>
                      <div>
                        <p className="text-[9px] text-slate-500 uppercase mb-1">Spark</p>
                        <p className="text-xs text-white bg-amber-500/10 p-2 rounded whitespace-pre-wrap">{c.spark_response}</p>
                      </div>
                    </div>
                    {(analysis.knowledge_matches || []).length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        <span className="text-[9px] text-slate-500">Matches:</span>
                        {analysis.knowledge_matches.map((m, i) => (
                          <span key={i} className="text-[9px] px-1.5 py-0.5 bg-green-500/10 text-green-400 rounded flex items-center gap-0.5">
                            <BookOpen className="w-2.5 h-2.5" />{m.begrip}
                          </span>
                        ))}
                      </div>
                    )}
                    {(analysis.snap_suggestions || []).length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        <span className="text-[9px] text-slate-500">Geleerd:</span>
                        {analysis.snap_suggestions.map((s, i) => (
                          <span key={i} className="text-[9px] px-1.5 py-0.5 bg-blue-500/10 text-blue-400 rounded flex items-center gap-0.5">
                            <Zap className="w-2.5 h-2.5" />{s}
                          </span>
                        ))}
                      </div>
                    )}
                    {analysis.bots_reacted && analysis.bots_reacted.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        <span className="text-[9px] text-slate-500">Bots reageerden:</span>
                        {analysis.bots_reacted.map((b, i) => <span key={i} className="text-[9px] px-1.5 py-0.5 bg-purple-500/10 text-purple-400 rounded flex items-center gap-0.5">
                          <Bot className="w-2.5 h-2.5" />{b}
                        </span>)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
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
