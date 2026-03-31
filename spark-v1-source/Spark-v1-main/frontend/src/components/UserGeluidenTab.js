import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const UserGeluidenTab = ({ userData }) => {
  const [soundMappings, setSoundMappings] = useState([]);
  const [newMapping, setNewMapping] = useState({ 
    word: '', 
    frequency: 'every', 
    file: null
  });
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (userData?.id) {
      loadSoundMappings();
    }
  }, [userData]);

  const loadSoundMappings = async () => {
    try {
      // Load only this user's sounds + spark-system (geen andere users!)
      const response = await axios.get(`${API}/sounds/mappings`, {
        params: { user_id: userData?.id }
      });
      
      // Filter: alleen eigen sounds (niet spark-system in deze lijst)
      const userSounds = (response.data.mappings || []).filter(m => m.user_id === userData?.id);
      setSoundMappings(userSounds);
    } catch (error) {
      console.error('Error loading sound mappings:', error);
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
        user_id: userData?.id,           // User's eigen ID
        visibility: 'private',           // Altijd private (alleen jij hoort)
        sound_type: 'user'               // User sound
      });
      
      await axios.post(`${API}/sounds/mapping?${params.toString()}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      alert('✅ Geluid toegevoegd!');
      setNewMapping({ word: '', frequency: 'every', file: null });
      document.querySelector('input[type="file"]')?.value && (document.querySelector('input[type="file"]').value = '');
      loadSoundMappings();
    } catch (error) {
      console.error('Error adding sound mapping:', error);
      alert(`❌ Fout: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteMapping = async (mappingId) => {
    if (!window.confirm('Weet je zeker dat je dit geluid wilt verwijderen?')) return;
    
    try {
      await axios.delete(`${API}/sounds/mapping/${mappingId}`);
      alert('✅ Geluid verwijderd');
      loadSoundMappings();
    } catch (error) {
      console.error('Error deleting sound:', error);
      alert('❌ Fout bij verwijderen');
    }
  };

  const handleTestSound = async (mappingId) => {
    try {
      const mapping = soundMappings.find(m => m.id === mappingId);
      if (!mapping) return;
      
      const audio = new Audio(`${API}/sounds/stream/${mapping.file}`);
      audio.volume = 0.7;
      await audio.play();
    } catch (error) {
      console.error('Error playing sound:', error);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setNewMapping({...newMapping, file});
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setNewMapping({...newMapping, file});
    }
  };

  return (
    <div className="space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
      <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
        <h3 className="text-xl font-bold text-white mb-2">🎵 Mijn Eigen Geluiden</h3>
        <p className="text-gray-400 text-sm mb-6">
          Upload je persoonlijke geluiden. Alleen jij hoort deze + Spark systeem geluiden.
        </p>

        {/* Upload Form */}
        <div className="space-y-4 mb-6 p-4 bg-slate-700/30 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Trigger Woord *
              </label>
              <input
                type="text"
                value={newMapping.word}
                onChange={(e) => setNewMapping({...newMapping, word: e.target.value})}
                placeholder="bijv. koe, hoi, yes"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-gray-500"
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
                <option value="every_5">Elke 5de keer</option>
                <option value="every_10">Elke 10de keer</option>
                <option value="first_only">Alleen eerste keer</option>
              </select>
            </div>
          </div>

          {/* File Upload */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-slate-600 bg-slate-700/30'
            }`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            {newMapping.file ? (
              <div>
                <span className="text-4xl mb-2">🎵</span>
                <p className="text-white font-medium">{newMapping.file.name}</p>
                <button
                  onClick={() => setNewMapping({...newMapping, file: null})}
                  className="mt-2 px-4 py-1 text-sm bg-red-500/20 text-red-300 rounded hover:bg-red-500/30"
                >
                  ❌ Verwijder
                </button>
              </div>
            ) : (
              <>
                <span className="text-5xl mb-3 block">📁</span>
                <p className="text-white font-medium mb-1">Sleep audiobestand hierheen</p>
                <p className="text-gray-400 text-sm mb-3">of klik om te uploaden</p>
                <p className="text-gray-500 text-xs">MP3, WAV, OGG</p>
                <input
                  type="file"
                  accept="audio/*"
                  onChange={handleFileSelect}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  id="user-audio-upload"
                />
              </>
            )}
          </div>

          <button
            onClick={handleAddMapping}
            className="w-full px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white font-semibold rounded-lg"
          >
            ➕ Geluid Toevoegen
          </button>

          <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <p className="text-sm text-blue-300">
              💡 <strong>Tip:</strong> Je hoort je eigen geluiden + Spark systeem geluiden. 
              Andere users horen jouw geluiden niet (privacy).
            </p>
          </div>
        </div>

        {/* Sound List */}
        <div className="space-y-3">
          <h4 className="text-lg font-semibold text-white">
            📋 Mijn Geluiden ({soundMappings.length})
          </h4>
          {soundMappings.length > 0 ? (
            soundMappings.map((mapping, index) => (
              <div key={index} className="p-4 bg-slate-700/50 rounded-lg flex justify-between items-center">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-2xl">🔊</span>
                    <strong className="text-white text-lg">{mapping.word}</strong>
                    <span className="px-2 py-1 text-xs bg-blue-500/20 text-blue-300 rounded">
                      🔒 Privé
                    </span>
                  </div>
                  <p className="text-sm text-gray-400">
                    Frequentie: {mapping.frequency === 'every' ? 'Elke keer' : `Elke ${mapping.frequency.split('_')[1]}de keer`}
                    {mapping.play_count ? ` • ${mapping.play_count}× afgespeeld` : ''}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleTestSound(mapping.id)}
                    className="px-4 py-2 bg-green-500/20 text-green-300 hover:bg-green-500/30 rounded"
                  >
                    ▶️ Test
                  </button>
                  <button
                    onClick={() => handleDeleteMapping(mapping.id)}
                    className="px-4 py-2 bg-red-500/20 text-red-300 hover:bg-red-500/30 rounded"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-400">
              🔇 Nog geen persoonlijke geluiden toegevoegd
            </div>
          )}
        </div>

        {/* Info Section */}
        <div className="mt-6 p-4 bg-slate-900 border border-slate-700 rounded-lg">
          <h4 className="text-md font-semibold text-white mb-2">ℹ️ Hoe werkt het?</h4>
          <ul className="text-sm text-gray-400 space-y-1">
            <li>• Upload geluiden die je hoort bij trigger woorden</li>
            <li>• Alleen jij hoort jouw geluiden (100% privé)</li>
            <li>• Spark systeem geluiden hoor je ook altijd</li>
            <li>• Later: delen met andere users via mixer (coming soon)</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default UserGeluidenTab;
