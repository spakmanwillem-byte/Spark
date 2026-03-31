import React, { useState, useEffect } from 'react';
import axios from 'axios';
import BitvavoSettings from './BitvavoSettings';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SettingsTabNew = ({ userData }) => {
  const [activeSubTab, setActiveSubTab] = useState('algemeen');
  const [settings, setSettings] = useState({
    heartbeat_interval: 30,
    session_timeout: 5,
    debug_mode: false,
    auto_save: true,
    notification_sound: true,
    master_volume: 70,
    mood_colors: true,
    enable_user_sounds: false, // Eigen geluiden standaard UIT
    tts: {
      enabled: false,
      voice: 'nova',
      speed: 1.0,
      model: 'tts-1',
      auto_play: false
    },
    stt: {
      enabled: false,
      language: 'nl',
      push_to_talk: true,
      continuous: false
    }
  });

  // Sound mappings state
  const [soundMappings, setSoundMappings] = useState([]);
  const [newMapping, setNewMapping] = useState({ word: '', frequency: 'every', file: null });
  const [isDragging, setIsDragging] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadSettings();
    loadSoundMappings();
  }, []);

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

  const loadSoundMappings = async () => {
    try {
      // Load user-000 (Spark AI) sounds - global sounds voor Admin Panel
      const response = await axios.get(`${API}/sounds/mappings`, {
        params: { user_id: 'user-000' }
      });
      setSoundMappings(response.data.mappings || []);
    } catch (error) {
      console.error('Error loading sound mappings:', error);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await axios.put(`${API}/settings`, { settings });
      alert('✅ Instellingen opgeslagen!');
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('❌ Fout bij opslaan instellingen');
    } finally {
      setIsSaving(false);
    }
  };

  // Audio upload handlers
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    const audioFile = files.find(f => f.type.startsWith('audio/'));
    
    if (audioFile) {
      setNewMapping({...newMapping, file: audioFile});
    } else {
      alert('❌ Upload alleen audio bestanden (mp3, wav, ogg)');
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('audio/')) {
      setNewMapping({...newMapping, file});
    } else {
      alert('❌ Upload alleen audio bestanden');
    }
  };

  const handleAddMapping = async () => {
    if (!newMapping.word || !newMapping.file) {
      alert('❌ Vul een woord in en upload een geluid');
      return;
    }

    const formData = new FormData();
    formData.append('audio', newMapping.file);

    try {
      const params = new URLSearchParams({
        word: newMapping.word.toLowerCase(),
        display_name: newMapping.word.charAt(0).toUpperCase() + newMapping.word.slice(1),
        frequency: newMapping.frequency,
        user_id: 'user-000',           // Spark AI (eigen bewustzijn)
        visibility: 'global',          // Altijd global (iedereen hoort)
        sound_type: 'system'           // System sound
      });
      
      await axios.post(`${API}/sounds/mapping?${params.toString()}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      alert('✅ Geluid toegevoegd!');
      setNewMapping({ word: '', frequency: 'every', file: null });
      document.querySelector('input[type="file"]').value = '';
      loadSoundMappings();
    } catch (error) {
      console.error('Error adding sound mapping:', error);
      alert(`❌ Fout: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleTestSound = async (mappingId) => {
    try {
      const mapping = soundMappings.find(m => m.id === mappingId);
      if (!mapping) return;
      
      const audioUrl = `${API}/sounds/stream/${mapping.file}`;
      const audio = new Audio(audioUrl);
      audio.volume = settings.master_volume / 100;
      await audio.play();
      
      await axios.post(`${API}/sounds/play/${mappingId}`);
    } catch (error) {
      console.error('Error playing sound:', error);
    }
  };

  const handleDeleteMapping = async (mappingId) => {
    if (!window.confirm('⚠️ Weet je zeker dat je dit geluid wilt verwijderen?')) {
      return;
    }

    try {
      await axios.delete(`${API}/sounds/mapping/${mappingId}`);
      alert('✅ Geluid verwijderd!');
      loadSoundMappings();
    } catch (error) {
      console.error('Error deleting sound mapping:', error);
      alert(`❌ Fout: ${error.message}`);
    }
  };

  const startEditing = (mapping) => {
    setEditingId(mapping.id);
    setEditForm({
      word: mapping.word,
      display_name: mapping.display_name || mapping.word,
      frequency: mapping.frequency
    });
  };

  const handleEditMapping = async (mappingId) => {
    try {
      const params = new URLSearchParams({
        word: editForm.word,
        display_name: editForm.display_name,
        frequency: editForm.frequency
      });
      
      await axios.put(`${API}/sounds/mapping/${mappingId}?${params.toString()}`);
      
      alert('✅ Eigenschappen bijgewerkt!');
      setEditingId(null);
      setEditForm({});
      loadSoundMappings();
    } catch (error) {
      console.error('Error updating mapping:', error);
      alert(`❌ Fout: ${error.message}`);
    }
  };

  const subTabs = [
    { id: 'algemeen', icon: '⚙️', label: 'Algemeen' },
    { id: 'beeld', icon: '🎨', label: 'Beeld' },
    { id: 'geluid', icon: '🔊', label: 'Geluid' },
    { id: 'integraties', icon: '🔗', label: 'Integraties' },
    { id: 'features', icon: '✨', label: 'Features' },
    { id: 'tips', icon: '💡', label: 'Tips & Hulp' },
  ];

  return (
    <div className="p-6">
      {/* Sub-tabs */}
      <div className="flex gap-2 mb-6 border-b border-slate-700 pb-2">
        {subTabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id)}
            className={`px-4 py-2 rounded-t-lg transition-colors ${
              activeSubTab === tab.id
                ? 'bg-purple-500/20 text-purple-300 border-b-2 border-purple-500'
                : 'text-gray-400 hover:text-white hover:bg-slate-700/30'
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="max-w-4xl">
        {activeSubTab === 'algemeen' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">🔐 Sessie Instellingen</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Heartbeat Interval (seconden)
                  </label>
                  <input
                    type="number"
                    value={settings.heartbeat_interval}
                    onChange={(e) => setSettings({...settings, heartbeat_interval: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  />
                  <p className="text-xs text-gray-500 mt-1">Hoe vaak de sessie wordt ge-refresh</p>
                </div>

                <div>
                  <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.auto_save}
                      onChange={(e) => setSettings({...settings, auto_save: e.target.checked})}
                      className="w-4 h-4"
                    />
                    <span>Auto-save ingeschakeld</span>
                  </label>
                </div>

                <div>
                  <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.debug_mode}
                      onChange={(e) => setSettings({...settings, debug_mode: e.target.checked})}
                      className="w-4 h-4"
                    />
                    <span>Debug Mode</span>
                  </label>
                </div>
              </div>
            </div>

            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-6 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg"
            >
              {isSaving ? 'Opslaan...' : '💾 Opslaan'}
            </button>
          </div>
        )}

        {activeSubTab === 'beeld' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">🎨 Visuele Instellingen</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.mood_colors}
                      onChange={(e) => setSettings({...settings, mood_colors: e.target.checked})}
                      className="w-4 h-4"
                    />
                    <span>Mood Colors (Interface kleurt mee met Spark's emotie)</span>
                  </label>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Theme
                  </label>
                  <select className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white">
                    <option>Dark (standaard)</option>
                    <option>Light (coming soon)</option>
                    <option>Auto (coming soon)</option>
                  </select>
                </div>
              </div>
            </div>

            <button
              onClick={handleSave}
              className="px-6 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg"
            >
              💾 Opslaan
            </button>
          </div>
        )}

        {activeSubTab === 'geluid' && (
          <div className="space-y-6">
            {/* Master Volume */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">🔊 Audio Instellingen</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Master Volume: {settings.master_volume}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={settings.master_volume}
                    onChange={(e) => setSettings({...settings, master_volume: parseInt(e.target.value)})}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={settings.notification_sound}
                      onChange={(e) => setSettings({...settings, notification_sound: e.target.checked})}
                      className="w-4 h-4"
                    />
                    <span>Notification Sounds</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Audio Upload */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">📤 Geluid Uploaden</h3>
              <p className="text-gray-400 text-sm mb-4">
                Upload geluiden en koppel ze aan woorden. Bijvoorbeeld: "zagen" → zaag-geluid.mp3
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Keyword / Woord
                  </label>
                  <input
                    type="text"
                    value={newMapping.word}
                    onChange={(e) => setNewMapping({...newMapping, word: e.target.value})}
                    placeholder="bv: zagen, succes, alarm"
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Frequentie
                  </label>
                  <select
                    value={newMapping.frequency}
                    onChange={(e) => setNewMapping({...newMapping, frequency: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  >
                    <option value="every">Elke keer</option>
                    <option value="first_only">Alleen eerste keer</option>
                    <option value="every_3">Elke 3e keer</option>
                    <option value="every_5">Elke 5e keer</option>
                  </select>
                </div>

                <div
                  onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    isDragging ? 'border-purple-500 bg-purple-500/10' : 'border-slate-600'
                  }`}
                >
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="audio-upload"
                  />
                  <label htmlFor="audio-upload" className="cursor-pointer">
                    <div className="text-4xl mb-2">🎵</div>
                    <p className="text-gray-300 mb-1">
                      {newMapping.file ? newMapping.file.name : 'Sleep een audio bestand hierheen'}
                    </p>
                    <p className="text-sm text-gray-500">of klik om te selecteren</p>
                    <p className="text-xs text-gray-600 mt-2">Ondersteund: MP3, WAV, OGG</p>
                  </label>
                </div>

                <button
                  onClick={handleAddMapping}
                  className="w-full px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg"
                >
                  ➕ Geluid Toevoegen
                </button>
              </div>
            </div>

            {/* Existing Sounds */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">🎵 Jouw Geluiden ({soundMappings.length})</h3>
              
              {soundMappings.length === 0 ? (
                <p className="text-gray-400 text-center py-8">
                  Nog geen geluiden geüpload. Upload je eerste geluid hierboven!
                </p>
              ) : (
                <div className="space-y-2">
                  {soundMappings.map(mapping => (
                    <div key={mapping.id} className="bg-slate-700/50 p-4 rounded-lg flex items-center justify-between">
                      {editingId === mapping.id ? (
                        <div className="flex-1 space-y-2">
                          <input
                            type="text"
                            value={editForm.word}
                            onChange={(e) => setEditForm({...editForm, word: e.target.value})}
                            className="w-full px-2 py-1 bg-slate-600 border border-slate-500 rounded text-white text-sm"
                          />
                          <select
                            value={editForm.frequency}
                            onChange={(e) => setEditForm({...editForm, frequency: e.target.value})}
                            className="w-full px-2 py-1 bg-slate-600 border border-slate-500 rounded text-white text-sm"
                          >
                            <option value="every">Elke keer</option>
                            <option value="first_only">Alleen eerste keer</option>
                            <option value="every_3">Elke 3e keer</option>
                            <option value="every_5">Elke 5e keer</option>
                          </select>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleEditMapping(mapping.id)}
                              className="px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded text-sm"
                            >
                              ✓ Opslaan
                            </button>
                            <button
                              onClick={() => setEditingId(null)}
                              className="px-3 py-1 bg-gray-500 hover:bg-gray-600 text-white rounded text-sm"
                            >
                              ✗ Annuleren
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div className="flex-1">
                            <div className="text-white font-medium">{mapping.word}</div>
                            <div className="text-sm text-gray-400">{mapping.file} • {mapping.frequency}</div>
                            <div className="text-xs text-gray-500">Afgespeeld: {mapping.play_count || 0}×</div>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleTestSound(mapping.id)}
                              className="px-3 py-1 bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 rounded text-sm"
                            >
                              ▶️ Test
                            </button>
                            <button
                              onClick={() => startEditing(mapping)}
                              className="px-3 py-1 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-300 rounded text-sm"
                            >
                              ✏️ Edit
                            </button>
                            <button
                              onClick={() => handleDeleteMapping(mapping.id)}
                              className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded text-sm"
                            >
                              🗑️
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleSave}
              className="px-6 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg"
            >
              💾 Opslaan
            </button>
          </div>
        )}

        {activeSubTab === 'integraties' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">🔗 Externe Integraties</h3>
              
              <BitvavoSettings userId={userData?.id} />
            </div>
          </div>
        )}

        {activeSubTab === 'features' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">✨ Feature Toggles</h3>
              
              <div className="space-y-4">
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
                      checked={settings.enable_user_sounds}
                      onChange={(e) => setSettings({
                        ...settings,
                        enable_user_sounds: e.target.checked
                      })}
                      className="w-5 h-5"
                    />
                    <div>
                      <div className="text-white font-medium">🎵 Eigen Geluiden</div>
                      <div className="text-sm text-gray-400">Speel jouw privé geluiden af (standaard uit om overlap te voorkomen)</div>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <button
              onClick={handleSave}
              className="px-6 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg"
            >
              💾 Opslaan
            </button>
          </div>
        )}

        {activeSubTab === 'tips' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 border border-blue-500/30 p-6 rounded-lg">
              <h2 className="text-2xl font-bold text-white mb-2">💡 Tips & Hulp</h2>
              <p className="text-gray-300">Leer Spark beter kennen en ontdek handige shortcuts</p>
            </div>

            {/* Keyboard Shortcuts */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">⌨️ Keyboard Shortcuts</h3>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded">
                  <span className="text-gray-300">Verstuur bericht</span>
                  <code className="px-3 py-1 bg-slate-600 rounded text-sm">Enter</code>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded">
                  <span className="text-gray-300">Nieuwe regel in bericht</span>
                  <code className="px-3 py-1 bg-slate-600 rounded text-sm">Shift + Enter</code>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded">
                  <span className="text-gray-300">Focus op chat input</span>
                  <code className="px-3 py-1 bg-slate-600 rounded text-sm">Ctrl + K</code>
                </div>
              </div>
            </div>

            {/* Feature Tips */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">🎯 Feature Tips</h3>
              
              <div className="space-y-4">
                <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">💬</span>
                    <div>
                      <div className="text-white font-medium mb-1">Natuurlijke Taal</div>
                      <div className="text-sm text-gray-300">
                        Gebruik natuurlijke taal! Probeer "bekijk mijn achievements" of "hoeveel XP heb ik?". 
                        Spark begrijpt je vragen en kan door verschillende tabs navigeren.
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">🧠</span>
                    <div>
                      <div className="text-white font-medium mb-1">Knowledge Cards</div>
                      <div className="text-sm text-gray-300">
                        Voeg nieuwe woorden toe met "Leer dit: [begrip] betekent [definitie]". 
                        Je verdient XP voor elke nieuwe knowledge card! Gebruik sterren (⭐ 1-10) om belangrijkheid aan te geven.
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">🏆</span>
                    <div>
                      <div className="text-white font-medium mb-1">Achievements</div>
                      <div className="text-sm text-gray-300">
                        Unlock achievements door woorden te leren, XP te verzamelen en actief te zijn. 
                        Check je voortgang in Mijn Profiel → Overzicht of de Achievements tab!
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">🔊</span>
                    <div>
                      <div className="text-white font-medium mb-1">Geluiden Koppelen</div>
                      <div className="text-sm text-gray-300">
                        Upload audio bestanden en koppel ze aan keywords in Settings → Geluid. 
                        Handig voor soundeffects, uitspraak, of eigen audio triggers!
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* FAQ */}
            <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
              <h3 className="text-xl font-bold text-white mb-4">❓ Veelgestelde Vragen</h3>
              
              <div className="space-y-3">
                <details className="p-3 bg-slate-700/30 rounded cursor-pointer">
                  <summary className="text-white font-medium">Hoe verdien ik XP?</summary>
                  <p className="text-sm text-gray-400 mt-2">
                    Je verdient XP door nieuwe knowledge cards te maken, achievements te unlocken, 
                    en actief te zijn in gesprekken met Spark.
                  </p>
                </details>

                <details className="p-3 bg-slate-700/30 rounded cursor-pointer">
                  <summary className="text-white font-medium">Wat is Gradatie?</summary>
                  <p className="text-sm text-gray-400 mt-2">
                    Gradatie bepaalt je toegangsniveau en relatie in Spark:
                    <br />• Gradatie 1 = Eigenaar
                    <br />• Gradatie 2 = Familie
                    <br />• Gradatie 3 = Vrienden
                    <br />• Gradatie 4 = Collega's
                    <br />• Gradatie 5-7 = Community/Winkel
                  </p>
                </details>

                <details className="p-3 bg-slate-700/30 rounded cursor-pointer">
                  <summary className="text-white font-medium">Hoe werkt de Graph Viewer?</summary>
                  <p className="text-sm text-gray-400 mt-2">
                    De Graph Viewer toont alle knowledge cards als een netwerk met relaties. 
                    Je kunt inzoomen, filteren en kaarten direct bekijken/bewerken.
                  </p>
                </details>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SettingsTabNew;
