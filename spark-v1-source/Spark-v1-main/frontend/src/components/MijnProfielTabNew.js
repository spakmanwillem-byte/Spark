import React, { useState, useEffect } from 'react';
import axios from 'axios';
import DagboekTab from './DagboekTab';
import AgendaTab from './AgendaTab';
import AchievementsTab from './AchievementsTab';
import LeaderboardTab from './LeaderboardTab';
import DashboardTab from './DashboardTab';
import UserGeluidenTab from './UserGeluidenTab';
import UserBestandenTab from './UserBestandenTab';  // NEW

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MijnProfielTabNew = ({ userData }) => {
  const [activeSubTab, setActiveSubTab] = useState('overzicht');
  const [achievements, setAchievements] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({});
  const [saveStatus, setSaveStatus] = useState(null);
  const [settings, setSettings] = useState({
    master_volume: 70,
    mood_colors: true,
    enable_user_sounds: false,
    notification_sound: true,
    tts: {
      enabled: false,
      voice: 'nova',
      speed: 1.0,
      auto_play: false
    },
    stt: {
      enabled: false,
      language: 'nl',
      push_to_talk: true
    }
  });
  
  // Wallet & ROAR balances
  const [walletBalance, setWalletBalance] = useState(0);
  const [roarBalance, setRoarBalance] = useState(0);

  useEffect(() => {
    if (userData?.id) {
      loadData();
      loadSettings();
      loadWalletData();
      // Initialize form data with user data
      setFormData({
        volledige_naam: userData.persoonlijke_info?.volledige_naam || '',
        geboortedatum: userData.persoonlijke_info?.geboortedatum || '',
        geslacht: userData.persoonlijke_info?.geslacht || '',
        email: userData.email || '',
        telefoon: userData.contact?.telefoon || '',
        straat: userData.adres?.straat || '',
        huisnummer: userData.adres?.huisnummer || '',
        postcode: userData.adres?.postcode || '',
        plaats: userData.adres?.plaats || '',
        land: userData.adres?.land || 'Nederland',
        beroep: userData.werk_carriere?.beroep || '',
        werkgever: userData.werk_carriere?.werkgever || '',
        opleiding: userData.opleiding?.opleiding || '',
        studierichting: userData.opleiding?.studierichting || '',
        bio: userData.bio || '',
        hobbies: userData.hobbies_interesses?.hobbies || '',
      });
    }
  }, [userData]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSaveProfile = async () => {
    setSaveStatus('saving');
    try {
      const response = await axios.put(`${API}/profile/me`, {
        user_id: userData.id,
        volledige_naam: formData.volledige_naam,
        geboortedatum: formData.geboortedatum,
        geslacht: formData.geslacht,
        email: formData.email,
        telefoon: formData.telefoon,
        straat: formData.straat,
        huisnummer: formData.huisnummer,
        postcode: formData.postcode,
        plaats: formData.plaats,
        land: formData.land,
        beroep: formData.beroep,
        werkgever: formData.werkgever,
        opleiding: formData.opleiding,
        studierichting: formData.studierichting,
        over_mij: formData.bio,
        hobbies: formData.hobbies,
      });

      if (response.data.success) {
        setSaveStatus('success');
        setTimeout(() => setSaveStatus(null), 3000);
        // Reload user data
        window.location.reload();
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const achRes = await axios.get(`${API}/admin/achievements/${userData.id}`);
      setAchievements(achRes.data);
    } catch (error) {
      console.error('Error loading profile data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      if (response.data.settings) {
        setSettings(response.data.settings);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const handleSaveSettings = async () => {
    try {
      await axios.put(`${API}/settings`, { settings });
      // Also save to localStorage for client-side access
      localStorage.setItem('spark_settings', JSON.stringify(settings));
      alert('✅ Instellingen opgeslagen!');
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('❌ Fout bij opslaan instellingen');
    }
  };

  const loadWalletData = async () => {
    try {
      // Load EUR wallet
      const walletRes = await axios.get(`${API}/wallet/overview?user_id=${userData.id}`);
      if (walletRes.data.success && walletRes.data.user_wallet) {
        setWalletBalance(walletRes.data.user_wallet.balance || 0);
      }
      
      // Load ROAR balance
      const roarRes = await axios.get(`${API}/roar/balance/${userData.id}`);
      if (roarRes.data.success) {
        setRoarBalance(roarRes.data.roar_balance || 0);
      }
    } catch (error) {
      console.error('Error loading wallet data:', error);
    }
  };

  const subTabs = [
    { id: 'overzicht', icon: '📊', label: 'Overzicht' },
    { id: 'bewerk', icon: '✏️', label: 'Bewerk Profiel' },
    { id: 'instellingen', icon: '⚙️', label: 'Instellingen' },
    { id: 'geluiden', icon: '🎵', label: 'Geluiden' },
    { id: 'bestanden', icon: '📁', label: 'Bestanden' },
  ];

  const [showHelpModal, setShowHelpModal] = useState(false);

  if (!userData) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-400">Log in om je profiel te bekijken</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header with Help Icon */}
      <div className="mb-6 pb-4 border-b border-slate-700 flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">
            👤 Mijn Profiel: {userData?.naam || "Gebruiker"}
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Beheer je persoonlijke informatie en voorkeuren
          </p>
        </div>
        
        {/* Help Icon */}
        <button
          onClick={() => setShowHelpModal(true)}
          className="w-12 h-12 bg-transparent border-2 border-red-500 hover:bg-red-500/20 rounded-full flex items-center justify-center text-2xl text-red-500 transition-all"
          title="Help & Ondersteuning"
        >
          ❓
        </button>
      </div>

      {/* Sub-tabs - 2 rows of 5 */}
      <div className="mb-6 border-b border-slate-700 pb-2">
        <div className="grid grid-cols-5 gap-2">
          {subTabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`px-3 py-2 rounded-lg transition-colors text-sm ${
                activeSubTab === tab.id
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500'
                  : 'text-gray-400 hover:text-white hover:bg-slate-700/30 border border-transparent'
              }`}
            >
              <span className="mr-1">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-6xl">
        {activeSubTab === 'overzicht' && (
          <div className="space-y-6">
            {/* Header Card */}
            <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 p-6 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 bg-purple-500/30 rounded-full flex items-center justify-center text-4xl">
                  👤
                </div>
                <div className="flex-1">
                  <h2 className="text-3xl font-bold text-white">{userData.naam}</h2>
                  <p className="text-gray-300">Spark Explorer</p>
                </div>
              </div>
            </div>

            {/* Quick Stats Grid - UITGEBREID */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* XP Card */}
              <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400 text-sm">Experience Points</span>
                  <span className="text-2xl">⭐</span>
                </div>
                <div className="text-3xl font-bold text-white">{userData.xp || 0}</div>
                <div className="text-xs text-gray-500 mt-1">XP</div>
                <div className="mt-2 bg-slate-700 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                    style={{ width: '65%' }}
                  ></div>
                </div>
                <div className="text-xs text-gray-400 mt-1">Level {Math.floor((userData.xp || 0) / 1000) + 1}</div>
              </div>

              {/* Achievements Card */}
              <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400 text-sm">Achievements</span>
                  <span className="text-2xl">🏆</span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {achievements?.total_unlocked || 0}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  van {achievements?.total_achievements || 13} unlocked
                </div>
                {achievements && (
                  <div className="mt-2">
                    <div className="text-xs text-purple-400">
                      Volgende: {achievements.next_milestone?.name}
                    </div>
                  </div>
                )}
              </div>

              {/* Gesprekken Card */}
              <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400 text-sm">Gesprekken</span>
                  <span className="text-2xl">💬</span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {userData.gesprekken_count || 0}
                </div>
                <div className="text-xs text-gray-500 mt-1">Totaal sessies</div>
              </div>

              {/* Knowledge Card */}
              <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400 text-sm">Knowledge</span>
                  <span className="text-2xl">🧠</span>
                </div>
                <div className="text-3xl font-bold text-white">
                  {achievements?.knowledge_count || 0}
                </div>
                <div className="text-xs text-gray-500 mt-1">Woorden geleerd</div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">📅 Recente Activiteit</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-green-400">✓</span>
                  <span className="text-gray-300">Achievement unlocked: Word Explorer (500 woorden)</span>
                  <span className="text-gray-500 ml-auto">Vandaag</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-blue-400">+</span>
                  <span className="text-gray-300">15 nieuwe woorden toegevoegd</span>
                  <span className="text-gray-500 ml-auto">Gisteren</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-purple-400">★</span>
                  <span className="text-gray-300">250 XP verdiend</span>
                  <span className="text-gray-500 ml-auto">2 dagen geleden</span>
                </div>
              </div>
            </div>

            {/* Progress Overview */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">📊 Voortgang Overzicht</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-300">Kennis Bijdrage</span>
                    <span className="text-gray-400">{achievements?.current_word_count || 0} / 1000</span>
                  </div>
                  <div className="bg-slate-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full"
                      style={{ width: `${Math.min(100, ((achievements?.current_word_count || 0) / 1000) * 100)}%` }}
                    ></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-300">Achievement Completie</span>
                    <span className="text-gray-400">{achievements?.total_unlocked || 0} / {achievements?.total_achievements || 13}</span>
                  </div>
                  <div className="bg-slate-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-yellow-500 to-orange-500 h-2 rounded-full"
                      style={{ width: `${achievements?.total_achievements > 0 ? (achievements.total_unlocked / achievements.total_achievements * 100) : 0}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeSubTab === 'bewerk' && (
          <div className="space-y-6">
            {/* Basis Informatie */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">👤 Basis Informatie</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Naam</label>
                  <input
                    type="text"
                    defaultValue={userData.naam}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    disabled
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Volledige Naam</label>
                  <input
                    type="text"
                    name="volledige_naam"
                    value={formData.volledige_naam || ''}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="Voor- en achternaam"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Geboortedatum</label>
                  <input
                    type="date"
                    name="geboortedatum"
                    value={formData.geboortedatum || ''}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Geslacht</label>
                  <select
                    name="geslacht"
                    value={formData.geslacht || ''}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  >
                    <option value="">Selecteer...</option>
                    <option value="Man">Man</option>
                    <option value="Vrouw">Vrouw</option>
                    <option value="Anders">Anders</option>
                    <option value="Zeg ik liever niet">Zeg ik liever niet</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Contact Informatie */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">📧 Contact</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email || ''}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Telefoon</label>
                  <input
                    type="tel"
                    name="telefoon"
                    value={formData.telefoon || ''}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="+31 6 12345678"
                  />
                </div>
              </div>
            </div>

            {/* Adres */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">🏠 Adres</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-300 mb-2">Straat</label>
                  <input
                    type="text"
                    name="straat" value={formData.straat || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="Straatnaam"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Huisnummer</label>
                  <input
                    type="text"
                    name="huisnummer" value={formData.huisnummer || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="123"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Postcode</label>
                  <input
                    type="text"
                    name="postcode" value={formData.postcode || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="1234 AB"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Plaats</label>
                  <input
                    type="text"
                    name="plaats" value={formData.plaats || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="Amsterdam"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Land</label>
                  <input
                    type="text"
                    name="land" value={formData.land || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  />
                </div>
              </div>
            </div>

            {/* Werk & Opleiding */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">💼 Werk & Opleiding</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Beroep</label>
                  <input
                    type="text"
                    name="beroep" value={formData.beroep || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="Jouw beroep"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Werkgever</label>
                  <input
                    type="text"
                    name="werkgever" value={formData.werkgever || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="Bedrijfsnaam"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Opleiding</label>
                  <input
                    type="text"
                    name="opleiding" value={formData.opleiding || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="HBO/WO/MBO etc."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Studierichting</label>
                  <input
                    type="text"
                    name="studierichting" value={formData.studierichting || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="Jouw studierichting"
                  />
                </div>
              </div>
            </div>

            {/* Bio & Interesses */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">🎯 Over Mij</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Bio</label>
                  <textarea
                    name="bio" value={formData.bio || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    rows="4"
                    placeholder="Vertel iets over jezelf..."
                  ></textarea>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Hobby's & Interesses</label>
                  <input
                    type="text"
                    name="hobbies" value={formData.hobbies || ''} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                    placeholder="Lezen, Sporten, Muziek..."
                  />
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end gap-3">
              <button 
                className="px-6 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg transition-colors"
                onClick={() => window.location.reload()}
              >
                Annuleren
              </button>
              <button 
                className={`px-6 py-2 rounded-lg transition-colors font-semibold flex items-center gap-2 ${
                  saveStatus === 'saving' 
                    ? 'bg-gray-500 cursor-wait' 
                    : saveStatus === 'success'
                    ? 'bg-green-500'
                    : saveStatus === 'error'
                    ? 'bg-red-500'
                    : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600'
                } text-white`}
                onClick={handleSaveProfile}
                disabled={saveStatus === 'saving'}
              >
                {saveStatus === 'saving' && '⏳ Opslaan...'}
                {saveStatus === 'success' && '✅ Opgeslagen!'}
                {saveStatus === 'error' && '❌ Fout'}
                {!saveStatus && '💾 Opslaan'}
              </button>
            </div>

            {saveStatus === 'error' && (
              <div className="bg-red-500/10 border border-red-500/30 p-4 rounded-lg">
                <p className="text-sm text-red-300">
                  ❌ Er ging iets mis bij het opslaan. Probeer het opnieuw.
                </p>
              </div>
            )}

            {saveStatus === 'success' && (
              <div className="bg-green-500/10 border border-green-500/30 p-4 rounded-lg">
                <p className="text-sm text-green-300">
                  ✅ Profiel succesvol opgeslagen!
                </p>
              </div>
            )}
          </div>
        )}

        {activeSubTab === 'statistieken' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">📈 Jouw Statistieken</h3>
              <p className="text-gray-400 text-center py-12">
                Gedetailleerde statistieken worden binnenkort toegevoegd!
                <br />
                <span className="text-sm text-gray-500">
                  (Gebruikspatronen, top topics, learning trajectory, etc.)
                </span>
              </p>
            </div>
          </div>
        )}

        {activeSubTab === 'dagboek' && (
          <DagboekTab userId={userData?.id} />
        )}

        {activeSubTab === 'agenda' && (
          <AgendaTab userId={userData?.id} />
        )}

        {/* NEW: User Geluiden Tab (Eigen Eco) */}
        {activeSubTab === 'geluiden' && (
          <UserGeluidenTab userData={userData} />
        )}

        {/* NEW: User Bestanden Tab (Eigen Cloud) */}
        {activeSubTab === 'bestanden' && (
          <UserBestandenTab userData={userData} />
        )}

        {/* Help Tab */}
        {activeSubTab === 'help' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-2xl font-bold text-white mb-4">❓ Help & Ondersteuning</h3>

              {/* Veelgestelde Vragen */}
              <div className="mb-8">
                <h4 className="text-lg font-semibold text-white mb-4">📚 Veelgestelde Vragen</h4>
                <div className="space-y-3">
                  <details className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                    <summary className="cursor-pointer font-medium text-white">Hoe werkt Spark Chat?</summary>
                    <p className="mt-3 text-gray-300 text-sm">
                      Spark Chat is een AI-assistent die je helpt met verschillende taken. Type gewoon je vraag en Spark antwoordt op basis van zijn kennis en jouw profiel.
                    </p>
                  </details>
                  <details className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                    <summary className="cursor-pointer font-medium text-white">Hoe waardeer ik mijn wallet op?</summary>
                    <p className="mt-3 text-gray-300 text-sm">
                      Ga naar FINANCIEEL → Mijn Wallet en klik op "Opwaarderen". Volg de instructies voor bank transfer. Na ontvangst wordt je saldo bijgewerkt (1-2 werkdagen).
                    </p>
                  </details>
                  <details className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                    <summary className="cursor-pointer font-medium text-white">Wat zijn Achievements?</summary>
                    <p className="mt-3 text-gray-300 text-sm">
                      Achievements zijn beloningen voor het voltooien van taken en mijlpalen in Spark. Bekijk je voortgang onder Community & Spel → Achievements.
                    </p>
                  </details>
                  <details className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                    <summary className="cursor-pointer font-medium text-white">Hoe wijzig ik mijn profiel?</summary>
                    <p className="mt-3 text-gray-300 text-sm">
                      Ga naar Mijn Profiel → Bewerk Profiel. Je kunt hier je naam, bio, contact info en voorkeuren aanpassen.
                    </p>
                  </details>
                </div>
              </div>

              {/* Sneltoetsen */}
              <div className="mb-8">
                <h4 className="text-lg font-semibold text-white mb-4">⌨️ Handige Sneltoetsen</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="bg-slate-700/50 p-3 rounded-lg">
                    <span className="text-gray-400 text-sm">File Browser opslaan:</span>
                    <code className="block mt-1 text-purple-300 font-mono">Ctrl + S</code>
                  </div>
                  <div className="bg-slate-700/50 p-3 rounded-lg">
                    <span className="text-gray-400 text-sm">Chat focus:</span>
                    <code className="block mt-1 text-purple-300 font-mono">Ctrl + K</code>
                  </div>
                </div>
              </div>

              {/* Contact */}
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-white mb-4">📧 Contact & Support</h4>
                <p className="text-gray-300 text-sm mb-4">
                  Heb je een vraag die hier niet beantwoord wordt? Neem contact op met het Spark team:
                </p>
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">📧</span>
                    <a href="mailto:support@spark.nl" className="text-blue-400 hover:text-blue-300">
                      support@spark.nl
                    </a>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">💬</span>
                    <span className="text-gray-300">Community Chat (via Community tab)</span>
                  </div>
                </div>
              </div>

              {/* System Info */}
              <div className="bg-blue-500/10 border border-blue-500/30 p-4 rounded-lg">
                <h5 className="font-semibold text-blue-300 mb-2">ℹ️ Systeem Informatie</h5>
                <div className="text-sm text-gray-300 space-y-1">
                  <p>Versie: Spark Core 4.1</p>
                  <p>Laatst bijgewerkt: {new Date().toLocaleDateString('nl-NL')}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Privacy & Disclaimer Tab */}
        {activeSubTab === 'privacy' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-2xl font-bold text-white mb-4">🔒 Privacy & Disclaimer</h3>

              {/* Privacy Policy */}
              <div className="mb-8">
                <h4 className="text-lg font-semibold text-white mb-4">📋 Privacyverklaring</h4>
                <div className="space-y-4 text-gray-300 text-sm">
                  <p>
                    <strong className="text-white">1. Gegevensverzameling</strong><br />
                    Spark verzamelt alleen gegevens die nodig zijn voor de werking van het platform: naam, e-mail, profiel informatie, en gebruiksdata. We verkopen jouw gegevens nooit aan derden.
                  </p>
                  <p>
                    <strong className="text-white">2. Gebruik van gegevens</strong><br />
                    Jouw gegevens worden gebruikt om:
                  </p>
                  <ul className="list-disc list-inside ml-4 space-y-1">
                    <li>Je profiel en voorkeuren te beheren</li>
                    <li>Spark AI te verbeteren (alleen met jouw toestemming)</li>
                    <li>Je Spark ervaring te personaliseren</li>
                    <li>Support en communicatie te faciliteren</li>
                  </ul>
                  <p>
                    <strong className="text-white">3. Beveiliging</strong><br />
                    We nemen passende technische en organisatorische maatregelen om jouw gegevens te beschermen tegen ongeautoriseerde toegang, verlies of misbruik.
                  </p>
                  <p>
                    <strong className="text-white">4. Jouw rechten</strong><br />
                    Je hebt het recht om:
                  </p>
                  <ul className="list-disc list-inside ml-4 space-y-1">
                    <li>Inzage te vragen in jouw gegevens</li>
                    <li>Correctie van onjuiste gegevens te verzoeken</li>
                    <li>Verwijdering van jouw account en gegevens aan te vragen</li>
                    <li>Bezwaar te maken tegen gegevensverwerking</li>
                  </ul>
                  <p>
                    <strong className="text-white">5. Cookies</strong><br />
                    Spark gebruikt alleen essentiële cookies voor login en voorkeuren. We gebruiken geen tracking cookies van derden.
                  </p>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="mb-8">
                <h4 className="text-lg font-semibold text-white mb-4">⚠️ Disclaimer</h4>
                <div className="space-y-4 text-gray-300 text-sm">
                  <p>
                    <strong className="text-white">1. Geen medisch/juridisch advies</strong><br />
                    Spark AI is een algemene assistent en verstrekt geen medisch, juridisch of financieel advies. Raadpleeg altijd een professional voor specifieke situaties.
                  </p>
                  <p>
                    <strong className="text-white">2. Betrouwbaarheid</strong><br />
                    Hoewel we streven naar accuraatheid, kunnen we niet garanderen dat alle informatie van Spark volledig correct of actueel is. Gebruik je eigen oordeel.
                  </p>
                  <p>
                    <strong className="text-white">3. Aansprakelijkheid</strong><br />
                    Spark is niet aansprakelijk voor schade voortvloeiend uit het gebruik van het platform, tenzij sprake is van opzet of grove schuld.
                  </p>
                  <p>
                    <strong className="text-white">4. Wijzigingen</strong><br />
                    We behouden het recht om deze voorwaarden en het platform te wijzigen. Belangrijke wijzigingen worden gecommuniceerd via e-mail of in-app notificatie.
                  </p>
                </div>
              </div>

              {/* AVG Compliance */}
              <div className="mb-8">
                <h4 className="text-lg font-semibold text-white mb-4">🇪🇺 AVG Naleving</h4>
                <p className="text-gray-300 text-sm mb-4">
                  Spark voldoet aan de Algemene Verordening Gegevensbescherming (AVG) van de Europese Unie. Voor vragen over gegevensbescherming:
                </p>
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📧</span>
                  <a href="mailto:privacy@spark.nl" className="text-blue-400 hover:text-blue-300">
                    privacy@spark.nl
                  </a>
                </div>
              </div>

              {/* Last Updated */}
              <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                <p className="text-gray-400 text-xs">
                  Laatst bijgewerkt: {new Date().toLocaleDateString('nl-NL', { year: 'numeric', month: 'long', day: 'numeric' })}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Instellingen Tab - User Instellingen (profiel-gebonden) */}
        {activeSubTab === 'instellingen' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-2xl font-bold text-white mb-2">⚙️ Mijn Instellingen</h3>
              <p className="text-gray-400 text-sm mb-6">
                Persoonlijke voorkeuren voor jouw Spark ervaring. Deze instellingen zijn gekoppeld aan jouw profiel.
              </p>

              {/* Audio Features */}
              <div className="mb-8">
                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  🎵 Audio Features
                </h4>
                <div className="space-y-4">
                  <div className="p-4 bg-slate-700/30 rounded-lg">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.enable_user_sounds}
                        onChange={(e) => setSettings({...settings, enable_user_sounds: e.target.checked})}
                        className="w-5 h-5"
                      />
                      <div>
                        <div className="text-white font-medium">Eigen Geluiden Afspelen</div>
                        <div className="text-sm text-gray-400">Speel jouw privé geluiden af naast Spark system geluiden</div>
                      </div>
                    </label>
                  </div>

                  <div className="p-4 bg-slate-700/30 rounded-lg">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.tts?.enabled}
                        onChange={(e) => setSettings({
                          ...settings,
                          tts: {...settings.tts, enabled: e.target.checked}
                        })}
                        className="w-5 h-5"
                      />
                      <div>
                        <div className="text-white font-medium">🗣️ Text-to-Speech (TTS)</div>
                        <div className="text-sm text-gray-400">Spark's antwoorden voorlezen</div>
                      </div>
                    </label>
                  </div>

                  <div className="p-4 bg-slate-700/30 rounded-lg">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.stt?.enabled}
                        onChange={(e) => setSettings({
                          ...settings,
                          stt: {...settings.stt, enabled: e.target.checked}
                        })}
                        className="w-5 h-5"
                      />
                      <div>
                        <div className="text-white font-medium">🎤 Speech-to-Text (STT)</div>
                        <div className="text-sm text-gray-400">Spraakherkenning voor input</div>
                      </div>
                    </label>
                  </div>

                  <div className="p-4 bg-slate-700/30 rounded-lg">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.notification_sound}
                        onChange={(e) => setSettings({...settings, notification_sound: e.target.checked})}
                        className="w-5 h-5"
                      />
                      <div>
                        <div className="text-white font-medium">🔔 Notificatie Geluiden</div>
                        <div className="text-sm text-gray-400">Geluiden bij nieuwe berichten en achievements</div>
                      </div>
                    </label>
                  </div>

                  <div className="p-4 bg-slate-700/30 rounded-lg">
                    <label className="text-gray-300 text-sm block mb-2">Master Volume</label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={settings.master_volume}
                      onChange={(e) => setSettings({...settings, master_volume: parseInt(e.target.value)})}
                      className="w-full"
                    />
                    <div className="text-center text-white font-medium mt-2">{settings.master_volume}%</div>
                  </div>
                </div>
              </div>

              {/* Weergave */}
              <div className="mb-8">
                <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  🎨 Weergave
                </h4>
                <div className="space-y-4">
                  <div className="p-4 bg-slate-700/30 rounded-lg">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.mood_colors}
                        onChange={(e) => setSettings({...settings, mood_colors: e.target.checked})}
                        className="w-5 h-5"
                      />
                      <div>
                        <div className="text-white font-medium">Stemming Kleuren</div>
                        <div className="text-sm text-gray-400">Visuele indicatoren voor Spark's emoties</div>
                      </div>
                    </label>
                  </div>
                </div>
              </div>

              <button 
                onClick={handleSaveSettings}
                className="px-6 py-3 bg-gradient-to-r from-green-600 to-green-500 text-white rounded-lg font-semibold"
              >
                💾 Instellingen Opslaan
              </button>

              <div className="bg-blue-500/10 border border-blue-500/30 p-4 rounded-lg mt-6">
                <div className="flex items-start gap-3">
                  <span className="text-xl">ℹ️</span>
                  <div className="text-sm text-gray-300">
                    <strong className="text-blue-300">Let op:</strong> Deze instellingen worden opgeslagen in jouw profiel en localStorage.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Mijn Wallet Tab - Persoonlijke user wallet (GEEN Bitvavo) */}
        {activeSubTab === 'wallet' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                💳 Mijn Wallet
              </h3>
              <p className="text-gray-400 text-sm mb-6">
                Jouw persoonlijke wallet binnen Spark. Waardeer op via bank transfer en gebruik je saldo voor features en services.
              </p>

              {/* Balans Card */}
              <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 border border-green-500/30 p-6 rounded-lg mb-6">
                <div className="text-center">
                  <div className="text-gray-400 text-sm mb-2">Beschikbaar Saldo</div>
                  <div className="text-5xl font-bold text-white mb-2">€{walletBalance.toFixed(2)}</div>
                  <div className="text-xs text-gray-500">User Wallet (Persoonlijk)</div>
                </div>
              </div>

              {/* Wallet Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-700/50 border border-slate-600 p-4 rounded-lg text-center">
                  <div className="text-gray-400 text-sm mb-1">ROAR Tokens</div>
                  <div className="text-2xl font-bold text-purple-400">{roarBalance.toFixed(2)}</div>
                  <div className="text-xs text-gray-500 mt-1">Koop in Winkel</div>
                </div>

                <div className="bg-slate-700/50 border border-slate-600 p-4 rounded-lg text-center">
                  <div className="text-gray-400 text-sm mb-1">Credits</div>
                  <div className="text-2xl font-bold text-blue-400">0</div>
                  <div className="text-xs text-gray-500 mt-1">Gebruik in de winkel</div>
                </div>

                <div className="bg-slate-700/50 border border-slate-600 p-4 rounded-lg text-center">
                  <div className="text-gray-400 text-sm mb-1">Transacties</div>
                  <div className="text-2xl font-bold text-green-400">0</div>
                  <div className="text-xs text-gray-500 mt-1">Totaal dit jaar</div>
                </div>
              </div>

              {/* Opwaarderen Knop */}
              <div className="text-center">
                <button 
                  className="px-8 py-3 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-green-500/50"
                  onClick={() => alert('💡 Opwaarderen: Stuur een bank transfer naar het opgegeven IBAN. Na ontvangst wordt je saldo bijgewerkt.')}
                >
                  💰 Opwaarderen
                </button>
                <p className="text-xs text-gray-500 mt-3">
                  Minimaal bedrag: €10.00 | Verwerktijd: 1-2 werkdagen
                </p>
              </div>

              {/* Info Box */}
              <div className="bg-blue-500/10 border border-blue-500/30 p-4 rounded-lg mt-6">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">ℹ️</span>
                  <div>
                    <h4 className="font-semibold text-blue-300 mb-1">Wallet Info</h4>
                    <ul className="text-sm text-gray-400 space-y-1">
                      <li>• Dit is je <strong>persoonlijke wallet</strong>, gescheiden van systeem kasboeken</li>
                      <li>• Geen crypto - alleen EUR via bank transfer</li>
                      <li>• Gebruik je saldo voor premium features, services en winkel items</li>
                      <li>• Voor crypto trading: zie Admin → Wallet → Spark Core (admin only)</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Transactions (placeholder) */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h4 className="text-lg font-semibold text-white mb-4">📜 Recente Transacties</h4>
              <div className="text-center py-8 text-gray-400">
                Nog geen transacties
              </div>
            </div>
          </div>
        )}

        {/* Financiën Tab */}
        {activeSubTab === 'financien' && (
          <DashboardTab userId={userData?.id} userName={userData?.naam} />
        )}

        {/* Achievements Tab */}
        {activeSubTab === 'achievements' && (
          <div>
            <AchievementsTab 
              userId={userData?.id} 
              isAdmin={userData?.gradatie === 1} 
              userName={userData?.naam}
            />
          </div>
        )}

        {/* Leaderboard Tab */}
        {activeSubTab === 'leaderboard' && (
          <div>
            <LeaderboardTab userData={userData} />
          </div>
        )}

        {/* Winkel Tab */}
        {activeSubTab === 'winkel' && (
          <div className="space-y-6">
            {/* Wallet Concept Uitleg */}
            <div className="bg-slate-800 border border-purple-500/30 p-4 rounded-lg">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <span>🪙</span> Over Spark Wallet
              </h3>
              <p className="text-gray-300 text-sm mb-3">
                <strong>Wallet</strong> = Credits systeem voor binnen Spark. Verdien credits door actief te zijn en besteed ze in de winkel.
              </p>
              <div className="bg-blue-500/10 border border-blue-500/30 p-2 rounded">
                <p className="text-blue-300 text-xs">
                  💡 <strong>Financiën</strong> = Overzicht van je Spark Wallet (crypto via Bitvavo)
                </p>
              </div>
            </div>

            <p className="text-gray-400">Koop items en features met je credits</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-lg text-center">
                <div className="text-5xl mb-4">🎨</div>
                <h4 className="text-lg font-semibold mb-2">Themes</h4>
                <p className="text-gray-400 text-sm mb-4">Personaliseer je Spark interface</p>
                <p className="text-2xl font-bold text-yellow-400 mb-4">100 Credits</p>
                <button className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
                  Koop Nu
                </button>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-lg text-center">
                <div className="text-5xl mb-4">⚡</div>
                <h4 className="text-lg font-semibold mb-2">XP Boost</h4>
                <p className="text-gray-400 text-sm mb-4">2x XP voor 24 uur</p>
                <p className="text-2xl font-bold text-yellow-400 mb-4">250 Credits</p>
                <button className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
                  Koop Nu
                </button>
              </div>

              <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-lg text-center">
                <div className="text-5xl mb-4">👤</div>
                <h4 className="text-lg font-semibold mb-2">Avatars</h4>
                <p className="text-gray-400 text-sm mb-4">Unieke profielfoto's</p>
                <p className="text-2xl font-bold text-yellow-400 mb-4">150 Credits</p>
                <button className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 rounded-lg transition-colors">
                  Koop Nu
                </button>
              </div>
            </div>

            <div className="bg-blue-500/10 border border-blue-500/30 p-4 rounded-lg text-center">
              <p className="text-gray-400 text-sm">
                🔮 Meer items komen binnenkort! Check regelmatig voor nieuwe aanbiedingen.
              </p>
            </div>
          </div>
        )}

        {/* Financiën Tab - VERWIJDERD (nu in Admin → Wallet) */}
      </div>

      {/* Privacy Footer */}
      <div className="mt-8 pt-4 border-t border-slate-700 text-center">
        <p className="text-gray-500 text-xs">
          © 2026 Spark Core 4.1 | 
          <button 
            onClick={() => setShowHelpModal(true)}
            className="text-blue-400 hover:text-blue-300 ml-1"
          >
            Privacy & Disclaimer
          </button>
        </p>
      </div>

      {/* Help Modal */}
      {showHelpModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setShowHelpModal(false)}>
          <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-3xl w-full max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="sticky top-0 bg-slate-800 border-b border-slate-700 p-6 flex items-center justify-between">
              <h3 className="text-2xl font-bold text-white">❓ Help & Privacy</h3>
              <button
                onClick={() => setShowHelpModal(false)}
                className="w-10 h-10 bg-slate-700 hover:bg-slate-600 rounded-full flex items-center justify-center text-xl"
              >
                ✕
              </button>
            </div>
            
            <div className="p-6 space-y-8">
              {/* FAQ */}
              <div>
                <h4 className="text-lg font-semibold text-white mb-4">📚 Veelgestelde Vragen</h4>
                <div className="space-y-3">
                  <details className="bg-slate-700/50 p-4 rounded-lg">
                    <summary className="cursor-pointer font-medium text-white">Hoe werkt Spark Chat?</summary>
                    <p className="mt-3 text-gray-300 text-sm">
                      Spark Chat is een AI-assistent die je helpt met verschillende taken.
                    </p>
                  </details>
                  <details className="bg-slate-700/50 p-4 rounded-lg">
                    <summary className="cursor-pointer font-medium text-white">Hoe waardeer ik mijn wallet op?</summary>
                    <p className="mt-3 text-gray-300 text-sm">
                      Ga naar FINANCIEEL → Mijn Wallet en klik op "Opwaarderen".
                    </p>
                  </details>
                </div>
              </div>

              {/* Privacy */}
              <div>
                <h4 className="text-lg font-semibold text-white mb-4">🔒 Privacy & Disclaimer</h4>
                <div className="space-y-3 text-gray-300 text-sm">
                  <p><strong className="text-white">Gegevensbescherming:</strong> We verzamelen alleen noodzakelijke data en verkopen nooit aan derden.</p>
                  <p><strong className="text-white">AVG Compliant:</strong> Volledig conform Europese wetgeving.</p>
                  <p><strong className="text-white">Contact:</strong> <a href="mailto:privacy@spark.nl" className="text-blue-400">privacy@spark.nl</a></p>
                </div>
              </div>

              {/* Contact */}
              <div>
                <h4 className="text-lg font-semibold text-white mb-4">📧 Contact</h4>
                <p className="text-gray-300 text-sm">
                  Support: <a href="mailto:support@spark.nl" className="text-blue-400">support@spark.nl</a>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MijnProfielTabNew;
