import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SettingsTab = ({ userData }) => {
  const [settings, setSettings] = useState({
    heartbeat_interval: 30,
    session_timeout: 5,
    debug_mode: false,
    auto_save: true,
    notification_sound: true,
    master_volume: 70, // 0-100
    mood_colors: true, // Interface kleurt mee met Spark's emotie
    // Voice settings
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
  
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    loadSettings();
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

  const handleReset = () => {
    if (window.confirm('⚠️ Weet je zeker dat je alle instellingen wilt resetten naar de standaardwaarden?')) {
      setSettings({
        heartbeat_interval: 30,
        session_timeout: 5,
        debug_mode: false,
        auto_save: true,
        notification_sound: true,
        master_volume: 70,
        mood_colors: true,
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
    }
  };

  return (
    <div style={{ padding: '30px', maxWidth: '800px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '30px' }}>⚙️ Systeem Instellingen</h2>

      {/* Session Settings */}
      <div className="settings-section">
        <h3>🔐 Sessie Instellingen</h3>
        
        <div className="setting-item">
          <label>
            <strong>Heartbeat Interval</strong>
            <span className="setting-description">Hoe vaak de sessie wordt ge-refresh (in seconden)</span>
          </label>
          <select
            value={settings.heartbeat_interval}
            onChange={(e) => setSettings({...settings, heartbeat_interval: parseInt(e.target.value)})}
            className="setting-input"
          >
            <option value={10}>10 seconden (Frequent)</option>
            <option value={30}>30 seconden (Standaard)</option>
            <option value={60}>60 seconden (Relaxed)</option>
            <option value={120}>120 seconden (Minimal)</option>
          </select>
        </div>

        <div className="setting-item">
          <label>
            <strong>Session Timeout</strong>
            <span className="setting-description">Automatisch uitloggen na inactiviteit (in minuten)</span>
          </label>
          <select
            value={settings.session_timeout}
            onChange={(e) => setSettings({...settings, session_timeout: parseInt(e.target.value)})}
            className="setting-input"
          >
            <option value={2}>2 minuten</option>
            <option value={5}>5 minuten (Standaard)</option>
            <option value={10}>10 minuten</option>
            <option value={30}>30 minuten</option>
            <option value={60}>1 uur</option>
          </select>
        </div>
      </div>

      {/* Interface Settings */}
      <div className="settings-section">
        <h3>🎨 Interface Instellingen</h3>
        
        <div className="setting-item">
          <label>
            <input
              type="checkbox"
              checked={settings.notification_sound}
              onChange={(e) => setSettings({...settings, notification_sound: e.target.checked})}
              style={{ marginRight: '10px' }}
            />
            <strong>Notificatie Geluiden</strong>
            <span className="setting-description">Speel geluiden af bij acties en meldingen</span>
          </label>
        </div>

        <div className="setting-item">
          <label>
            <strong>Master Volume: {settings.master_volume}%</strong>
            <span className="setting-description">Algemeen volumeniveau voor alle geluiden</span>
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={settings.master_volume}
            onChange={(e) => setSettings({...settings, master_volume: parseInt(e.target.value)})}
            style={{ width: '100%', marginTop: '10px' }}
            className="volume-slider"
          />
        </div>

        <div className="setting-item">
          <label>
            <input
              type="checkbox"
              checked={settings.auto_save}
              onChange={(e) => setSettings({...settings, auto_save: e.target.checked})}
              style={{ marginRight: '10px' }}
            />
            <strong>Auto-Save</strong>
            <span className="setting-description">Sla wijzigingen automatisch op</span>
          </label>
        </div>

        <div className="setting-item">
          <label>
            <input
              type="checkbox"
              checked={settings.mood_colors}
              onChange={(e) => setSettings({...settings, mood_colors: e.target.checked})}
              style={{ marginRight: '10px' }}
            />
            <strong>🎨 Interface kleurt mee met Spark</strong>
            <span className="setting-description">
              Kleuren veranderen met Spark's emotie: 🟢 Blij | 🔴 Boos | 🔵 Bedroeft | 🟡 Bang
            </span>
          </label>
        </div>
      </div>

      {/* Developer Settings */}
      {userData && userData.gradatie === 1 && (
        <div className="settings-section">
          <h3>👨‍💻 Developer Instellingen</h3>
          
          <div className="setting-item">
            <label>
              <input
                type="checkbox"
                checked={settings.debug_mode}
                onChange={(e) => setSettings({...settings, debug_mode: e.target.checked})}
                style={{ marginRight: '10px' }}
              />
              <strong>Debug Mode</strong>
              <span className="setting-description">Toon extra debug informatie in de console en interface</span>
            </label>
          </div>
        </div>
      )}


      {/* Voice Settings */}
      <div className="settings-section">
        <h3>🎤 Voice Interface (Nieuw!)</h3>
        
        <div className="setting-item">
          <label>
            <input
              type="checkbox"
              checked={settings.tts?.enabled || false}
              onChange={(e) => setSettings({...settings, tts: {...settings.tts, enabled: e.target.checked}})}
              style={{ marginRight: '10px' }}
            />
            <strong>🔊 Text-to-Speech (TTS)</strong>
            <span className="setting-description">Spark spreekt zijn antwoorden uit</span>
          </label>
        </div>

        {settings.tts?.enabled && (
          <>
            <div className="setting-item">
              <label>
                <strong>Stem</strong>
                <span className="setting-description">Kies de stem voor Spark</span>
              </label>
              <select
                value={settings.tts?.voice || 'nova'}
                onChange={(e) => setSettings({...settings, tts: {...settings.tts, voice: e.target.value}})}
                className="setting-input"
              >
                <option value="nova">Nova (Energiek, vrouwelijk) - Aanbevolen</option>
                <option value="alloy">Alloy (Neutraal, gebalanceerd)</option>
                <option value="shimmer">Shimmer (Helder, vrolijk)</option>
                <option value="coral">Coral (Warm, vriendelijk)</option>
                <option value="echo">Echo (Glad, kalm, mannelijk)</option>
                <option value="onyx">Onyx (Diep, autoritair, mannelijk)</option>
                <option value="fable">Fable (Expressief, storytelling)</option>
                <option value="sage">Sage (Wijs, gemeten)</option>
                <option value="ash">Ash (Helder, duidelijk)</option>
              </select>
            </div>

            <div className="setting-item">
              <label>
                <strong>Spreeksnelheid</strong>
                <span className="setting-description">Hoe snel Spark praat (1.0 = normaal)</span>
              </label>
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={settings.tts?.speed || 1.0}
                onChange={(e) => setSettings({...settings, tts: {...settings.tts, speed: parseFloat(e.target.value)}})}
                className="setting-input"
                style={{width: '100%', maxWidth: '400px'}}
              />
              <span style={{fontSize: '12px', color: 'rgba(255,255,255,0.5)', marginLeft: '10px'}}>
                {settings.tts?.speed || 1.0}x
              </span>
            </div>

            <div className="setting-item">
              <label>
                <input
                  type="checkbox"
                  checked={settings.tts?.auto_play || false}
                  onChange={(e) => setSettings({...settings, tts: {...settings.tts, auto_play: e.target.checked}})}
                  style={{ marginRight: '10px' }}
                />
                <strong>Auto-play</strong>
                <span className="setting-description">Speel Spark's antwoorden automatisch af</span>
              </label>
            </div>
          </>
        )}

        <div className="setting-item">
          <label>
            <input
              type="checkbox"
              checked={settings.stt?.enabled || false}
              onChange={(e) => setSettings({...settings, stt: {...settings.stt, enabled: e.target.checked}})}
              style={{ marginRight: '10px' }}
            />
            <strong>🎙️ Speech-to-Text (STT)</strong>
            <span className="setting-description">Praat tegen Spark via je microfoon</span>
          </label>
        </div>

        {settings.stt?.enabled && (
          <>
            <div className="setting-item">
              <label>
                <input
                  type="checkbox"
                  checked={settings.stt?.push_to_talk || true}
                  onChange={(e) => setSettings({...settings, stt: {...settings.stt, push_to_talk: e.target.checked}})}
                  style={{ marginRight: '10px' }}
                />
                <strong>Push-to-talk</strong>
                <span className="setting-description">Houd de knop vast terwijl je spreekt (aanbevolen)</span>
              </label>
            </div>

            <div className="setting-item">
              <label>
                <strong>Taal</strong>
                <span className="setting-description">Taal voor spraakherkenning</span>
              </label>
              <select
                value={settings.stt?.language || 'nl'}
                onChange={(e) => setSettings({...settings, stt: {...settings.stt, language: e.target.value}})}
                className="setting-input"
              >
                <option value="nl">Nederlands</option>
                <option value="en">Engels</option>
                <option value="de">Duits</option>
                <option value="fr">Frans</option>
              </select>
            </div>
          </>
        )}

        <div style={{
          padding: '15px',
          background: 'rgba(76, 175, 80, 0.1)',
          border: '1px solid rgba(76, 175, 80, 0.3)',
          borderRadius: '8px',
          marginTop: '15px',
          fontSize: '13px',
          color: 'rgba(255, 255, 255, 0.8)'
        }}>
          <strong>💚 Accessibility Feature</strong><br/>
          Voice interface maakt Spark toegankelijk voor iedereen, inclusief mensen met dyslexie, visuele beperkingen, of wie liever praat dan typt.
        </div>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '15px', marginTop: '40px' }}>
        <button
          onClick={handleSave}
          disabled={isSaving}
          style={{
            padding: '12px 30px',
            borderRadius: '8px',
            border: 'none',
            background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
            color: 'white',
            fontWeight: 600,
            cursor: isSaving ? 'not-allowed' : 'pointer',
            opacity: isSaving ? 0.6 : 1,
          }}
        >
          {isSaving ? '⏳ Opslaan...' : '✅ Opslaan'}
        </button>
        
        <button
          onClick={handleReset}
          style={{
            padding: '12px 30px',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            background: 'transparent',
            color: 'rgb(200, 200, 200)',
            cursor: 'pointer',
          }}
        >
          🔄 Reset naar Standaard
        </button>
      </div>

      <style jsx>{`
        .settings-section {
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 25px;
          margin-bottom: 25px;
        }

        .settings-section h3 {
          margin: 0 0 20px 0;
          font-size: 18px;
        }

        .setting-item {
          margin-bottom: 20px;
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .setting-item:last-child {
          border-bottom: none;
          margin-bottom: 0;
          padding-bottom: 0;
        }

        .setting-item label {
          display: block;
        }

        .setting-item label strong {
          display: block;
          margin-bottom: 5px;
          font-size: 14px;
        }

        .setting-description {
          display: block;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.5);
          margin-bottom: 10px;
        }

        .setting-input {
          width: 100%;
          max-width: 300px;
          padding: 10px;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: rgba(40, 40, 40, 0.8);
          color: rgb(255, 255, 255);
          font-size: 14px;
        }

        .setting-input:focus {
          border-color: rgba(76, 175, 80, 0.4);
          outline: none;
        }
      `}</style>
    </div>
  );
};

export default SettingsTab;
