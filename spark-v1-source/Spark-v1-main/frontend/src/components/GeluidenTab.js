import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const GeluidenTab = ({ userData }) => {
  const [soundMappings, setSoundMappings] = useState([]);
  const [newMapping, setNewMapping] = useState({ 
    word: '', 
    frequency: 'every', 
    file: null,
    visibility: 'private',  // NEW: private, shared, global
    sound_type: 'user'      // NEW: user, system, button, command
  });
  const [isDragging, setIsDragging] = useState(false);
  const [filterView, setFilterView] = useState('all'); // all, own, shared, system

  useEffect(() => {
    loadSoundMappings();
  }, [userData]);

  const loadSoundMappings = async () => {
    try {
      // Fetch with user_id for filtering
      const userId = userData?.id || 'guest';
      const response = await axios.get(`${API}/sounds/mappings`, {
        params: { user_id: userId }
      });
      setSoundMappings(response.data.mappings || []);
    } catch (error) {
      console.error('Error loading sound mappings:', error);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

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
      // Send query params in URL including visibility and type
      const params = new URLSearchParams({
        word: newMapping.word.toLowerCase(),
        display_name: newMapping.display_name || newMapping.word.charAt(0).toUpperCase() + newMapping.word.slice(1),
        frequency: newMapping.frequency,
        user_id: userData?.id || 'user-001',
        visibility: newMapping.visibility,     // NEW
        sound_type: newMapping.sound_type      // NEW
      });
      
      await axios.post(`${API}/sounds/mapping?${params.toString()}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      alert('✅ Geluid toegevoegd!');
      setNewMapping({ 
        word: '', 
        display_name: '', 
        frequency: 'every', 
        file: null,
        visibility: 'private',
        sound_type: 'user'
      });
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.value = '';
      loadSoundMappings();
    } catch (error) {
      console.error('Error adding sound mapping:', error);
      alert(`❌ Fout: ${error.response?.data?.detail || error.message}`);
    }
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
      alert(`❌ Fout: ${error.response?.data?.detail || error.message}`);
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

  const handleTestSound = async (mappingId) => {
    try {
      // Find the mapping
      const mapping = soundMappings.find(m => m.id === mappingId);
      if (!mapping) {
        alert('❌ Mapping niet gevonden');
        return;
      }
      
      // Use new streaming endpoint
      const audioUrl = `${API}/sounds/stream/${mapping.file}`;
      console.log('[TEST SOUND] Playing:', audioUrl);
      
      const audio = new Audio(audioUrl);
      audio.volume = 0.7;
      await audio.play();
      
      // Update play count
      await axios.post(`${API}/sounds/play/${mappingId}`);
    } catch (error) {
      console.error('Error playing sound:', error);
      alert(`❌ Kon geluid niet afspelen: ${error.message}`);
    }
  };

  const handleDeleteMapping = async (mappingId) => {
    if (!window.confirm('⚠️ Weet je zeker dat je dit geluid wilt verwijderen?')) {
      return;
    }

    try {
      await axios.delete(`${API}/sounds/mapping/${mappingId}`);
      alert('✅ Geluid verwijderd');
      loadSoundMappings();
    } catch (error) {
      console.error('Error deleting sound:', error);
      alert('❌ Fout bij verwijderen');
    }
  };

  return (
    <div style={{ padding: '30px', maxWidth: '900px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '10px' }}>🔊 Geluiden & Audio Triggers</h2>
      <p style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '14px', marginBottom: '30px' }}>
        Koppel woorden aan geluiden die afspelen wanneer het woord in de chat verschijnt
      </p>

      {/* Add New Sound Mapping */}
      <div className="add-sound-section">
        <h3>➕ Nieuw Geluid Toevoegen</h3>

        <div className="form-grid">
          <div className="form-group">
            <label>Woord/Trigger</label>
            <input
              type="text"
              value={newMapping.word}
              onChange={(e) => setNewMapping({...newMapping, word: e.target.value})}
              placeholder="bijv. 'druppel', 'verzend', 'succes'"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label>Frequentie</label>
            <select
              value={newMapping.frequency}
              onChange={(e) => setNewMapping({...newMapping, frequency: e.target.value})}
              className="form-input"
            >
              <option value="every">Elke keer</option>
              <option value="every_5">Elke 5de keer</option>
              <option value="every_10">Elke 10de keer</option>
              <option value="first_only">Alleen eerste keer</option>
            </select>
          </div>

          {/* NEW: Visibility Control */}
          <div className="form-group">
            <label>Zichtbaarheid</label>
            <select
              value={newMapping.visibility}
              onChange={(e) => setNewMapping({...newMapping, visibility: e.target.value})}
              className="form-input"
            >
              <option value="private">🔒 Privé (alleen ik)</option>
              <option value="shared">🔊 Gedeeld (anderen ook)</option>
              {userData?.gradatie === 1 && (
                <option value="global">🌐 Globaal (systeem - iedereen)</option>
              )}
            </select>
          </div>

          {/* NEW: Type Control (Admin Only) */}
          {userData?.gradatie === 1 && (
            <div className="form-group">
              <label>Type (Admin)</label>
              <select
                value={newMapping.sound_type}
                onChange={(e) => setNewMapping({...newMapping, sound_type: e.target.value})}
                className="form-input"
              >
                <option value="user">👤 User geluid</option>
                <option value="system">⚙️ Systeem geluid</option>
                <option value="button">🔘 Button geluid</option>
                <option value="command">⌨️ Command geluid</option>
              </select>
            </div>
          )}
        </div>

        {/* Drag & Drop Area */}
        <div
          className={`drop-zone ${isDragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {newMapping.file ? (
            <div className="file-selected">
              <span style={{ fontSize: '32px' }}>🎵</span>
              <p style={{ margin: '10px 0 0 0' }}>{newMapping.file.name}</p>
              <button
                onClick={() => setNewMapping({...newMapping, file: null})}
                style={{ marginTop: '10px', fontSize: '12px', padding: '5px 15px', border: '1px solid rgba(255,255,255,0.2)', background: 'transparent', color: '#fff', borderRadius: '4px', cursor: 'pointer' }}
              >
                ❌ Verwijder
              </button>
            </div>
          ) : (
            <>
              <span style={{ fontSize: '48px', marginBottom: '15px' }}>📁</span>
              <p><strong>Sleep een audiobestand hierheen</strong></p>
              <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.5)', marginTop: '5px' }}>
                of klik om te uploaden
              </p>
              <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)', marginTop: '10px' }}>
                Ondersteund: MP3, WAV, OGG
              </p>
              <input
                type="file"
                accept="audio/*"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                id="audio-upload"
              />
              <label
                htmlFor="audio-upload"
                style={{ display: 'block', width: '100%', height: '100%', position: 'absolute', top: 0, left: 0, cursor: 'pointer' }}
              />
            </>
          )}
        </div>

        <button
          onClick={handleAddMapping}
          style={{
            padding: '12px 30px',
            borderRadius: '8px',
            border: 'none',
            background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
            color: 'white',
            fontWeight: 600,
            cursor: 'pointer',
            marginTop: '20px',
          }}
        >
          ➕ Geluid Toevoegen
        </button>
      </div>

      {/* Existing Sound Mappings */}
      <div className="sounds-list">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>📋 Actieve Geluiden ({soundMappings.length})</h3>
          
          {/* Filter Tabs */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setFilterView('all')}
              style={{
                padding: '6px 12px',
                fontSize: '13px',
                borderRadius: '6px',
                border: filterView === 'all' ? '2px solid #4CAF50' : '1px solid rgba(255,255,255,0.2)',
                background: filterView === 'all' ? 'rgba(76, 175, 80, 0.2)' : 'transparent',
                color: '#fff',
                cursor: 'pointer'
              }}
            >
              Alles
            </button>
            <button
              onClick={() => setFilterView('own')}
              style={{
                padding: '6px 12px',
                fontSize: '13px',
                borderRadius: '6px',
                border: filterView === 'own' ? '2px solid #4CAF50' : '1px solid rgba(255,255,255,0.2)',
                background: filterView === 'own' ? 'rgba(76, 175, 80, 0.2)' : 'transparent',
                color: '#fff',
                cursor: 'pointer'
              }}
            >
              🔒 Mijn geluiden
            </button>
            <button
              onClick={() => setFilterView('shared')}
              style={{
                padding: '6px 12px',
                fontSize: '13px',
                borderRadius: '6px',
                border: filterView === 'shared' ? '2px solid #4CAF50' : '1px solid rgba(255,255,255,0.2)',
                background: filterView === 'shared' ? 'rgba(76, 175, 80, 0.2)' : 'transparent',
                color: '#fff',
                cursor: 'pointer'
              }}
            >
              🔊 Gedeeld
            </button>
            <button
              onClick={() => setFilterView('system')}
              style={{
                padding: '6px 12px',
                fontSize: '13px',
                borderRadius: '6px',
                border: filterView === 'system' ? '2px solid #4CAF50' : '1px solid rgba(255,255,255,0.2)',
                background: filterView === 'system' ? 'rgba(76, 175, 80, 0.2)' : 'transparent',
                color: '#fff',
                cursor: 'pointer'
              }}
            >
              ⚙️ Systeem
            </button>
          </div>
        </div>
        
        {soundMappings.filter(m => {
          const isOwn = m.user_id === userData?.id;
          const isSystem = m.user_id === 'spark-system';
          const isShared = m.visibility === 'shared' && !isOwn;
          
          if (filterView === 'all') return true;
          if (filterView === 'own') return isOwn;
          if (filterView === 'shared') return isShared;
          if (filterView === 'system') return isSystem;
          return true;
        }).length > 0 ? (
          soundMappings.filter(m => {
            const isOwn = m.user_id === userData?.id;
            const isSystem = m.user_id === 'spark-system';
            const isShared = m.visibility === 'shared' && !isOwn;
            
            if (filterView === 'all') return true;
            if (filterView === 'own') return isOwn;
            if (filterView === 'shared') return isShared;
            if (filterView === 'system') return isSystem;
            return true;
          }).map((mapping, index) => {
            // Determine visibility icon
            const visibilityIcon = mapping.visibility === 'private' ? '🔒' :
                                  mapping.visibility === 'shared' ? '🔊' : '🌐';
            const isOwnSound = mapping.user_id === userData?.id;
            const isSparkSystem = mapping.user_id === 'spark-system';
            
            return (
            <div key={index} className="sound-item">
              <div className="sound-info">
                <span className="sound-icon">
                  {visibilityIcon} {isSparkSystem ? '⚙️' : '🔊'}
                </span>
                <div>
                  <strong className="sound-word">
                    {mapping.word}
                    {!isOwnSound && <span style={{fontSize: '11px', color: '#888', marginLeft: '8px'}}>
                      (van {isSparkSystem ? 'Spark Systeem' : `user-${mapping.user_id?.slice(-3)}`})
                    </span>}
                  </strong>
                  <p className="sound-meta">
                    {visibilityIcon} {mapping.visibility === 'private' ? 'Privé' : 
                       mapping.visibility === 'shared' ? 'Gedeeld' : 'Globaal'} •
                    Frequentie: {mapping.frequency === 'every' ? 'Elke keer' : `Elke ${mapping.frequency.split('_')[1]}de keer`}
                    {mapping.play_count && ` • ${mapping.play_count}× afgespeeld`}
                    {mapping.type && mapping.type !== 'user' && ` • ${mapping.type}`}
                  </p>
                </div>
              </div>
              <div className="sound-actions">{isOwnSound && (
                <>
                <button
                  onClick={() => handleTestSound(mapping.id)}
                  className="action-btn test-btn"
                >
                  ▶️ Test
                </button>
                <button
                  onClick={() => handleDeleteMapping(mapping.id)}
                  className="action-btn delete-btn"
                >
                  🗑️
                </button>
                </>
              )}
              {!isOwnSound && (
                <button
                  onClick={() => handleTestSound(mapping.id)}
                  className="action-btn test-btn"
                >
                  ▶️ Test
                </button>
              )}
              </div>
            </div>
          )})
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(255, 255, 255, 0.5)' }}>
            🔇 Geen geluiden in deze filter
          </div>
        )}
      </div>

      <style jsx>{`
        .add-sound-section {
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 25px;
          margin-bottom: 30px;
        }

        .add-sound-section h3 {
          margin: 0 0 20px 0;
        }

        .form-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.7);
          margin-bottom: 8px;
          font-weight: 600;
        }

        .form-input {
          width: 100%;
          padding: 10px;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: rgba(40, 40, 40, 0.8);
          color: rgb(255, 255, 255);
          font-size: 14px;
        }

        .form-input:focus {
          border-color: rgba(76, 175, 80, 0.4);
          outline: none;
        }

        .drop-zone {
          position: relative;
          border: 2px dashed rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          padding: 40px;
          text-align: center;
          transition: all 0.3s ease;
          background: rgba(40, 40, 40, 0.5);
        }

        .drop-zone.dragging {
          border-color: #4CAF50;
          background: rgba(76, 175, 80, 0.1);
        }

        .file-selected {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .sounds-list {
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 25px;
        }

        .sound-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(40, 40, 40, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          padding: 15px 20px;
          margin-bottom: 12px;
          transition: all 0.2s ease;
        }

        .sound-item:hover {
          background: rgba(40, 40, 40, 0.9);
          border-color: rgba(255, 255, 255, 0.1);
        }

        .sound-info {
          display: flex;
          gap: 15px;
          align-items: center;
        }

        .sound-icon {
          font-size: 24px;
        }

        .sound-word {
          display: block;
          font-size: 16px;
          margin-bottom: 4px;
        }

        .sound-meta {
          margin: 0;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.5);
        }

        .sound-actions {
          display: flex;
          gap: 10px;
        }

        .action-btn {
          padding: 8px 16px;
          border-radius: 6px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: transparent;
          color: rgb(200, 200, 200);
          cursor: pointer;
          font-size: 13px;
          transition: all 0.2s ease;
        }

        .action-btn:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .test-btn:hover {
          border-color: rgba(76, 175, 80, 0.4);
          color: #4CAF50;
        }

        .delete-btn:hover {
          border-color: rgba(244, 67, 54, 0.4);
          color: #f44336;
        }
      `}</style>
    </div>
  );
};

export default GeluidenTab;
