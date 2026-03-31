import React, { useState, useEffect } from 'react';
import { audioMixer } from '../utils/AudioMixer';

/**
 * Audio Mixer UI Component
 * Shows volume sliders for each channel
 */
function AudioMixerUI({ show, onClose }) {
  const [mixerState, setMixerState] = useState(audioMixer.getState());
  
  useEffect(() => {
    // Update state every second
    const interval = setInterval(() => {
      setMixerState(audioMixer.getState());
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);
  
  const handleVolumeChange = (channel, value) => {
    audioMixer.setVolume(channel, value / 100);
    setMixerState(audioMixer.getState());
  };
  
  const handleMuteToggle = (channel) => {
    audioMixer.setMuted(channel, !mixerState.channels[channel].muted);
    setMixerState(audioMixer.getState());
  };
  
  if (!show) return null;
  
  return (
    <div style={styles.overlay}>
      <div style={styles.panel}>
        <div style={styles.header}>
          <h3>🎵 Audio Mixer</h3>
          <button onClick={onClose} style={styles.closeBtn}>×</button>
        </div>
        
        <div style={styles.content}>
          {Object.entries(mixerState.channels).map(([channel, settings]) => (
            <div key={channel} style={styles.channelRow}>
              <div style={styles.channelLabel}>
                <span style={styles.channelName}>
                  {channel === 'master' && '🎚️ Master'}
                  {channel === 'ambient' && '🌳 Ambient'}
                  {channel === 'sfx' && '🔨 SFX'}
                  {channel === 'animals' && '🦌 Animals'}
                </span>
                <button 
                  onClick={() => handleMuteToggle(channel)}
                  style={{
                    ...styles.muteBtn,
                    background: settings.muted ? '#f44336' : '#4CAF50'
                  }}
                >
                  {settings.muted ? '🔇' : '🔊'}
                </button>
              </div>
              
              <div style={styles.sliderContainer}>
                <input 
                  type="range"
                  min="0"
                  max="100"
                  value={settings.volume * 100}
                  onChange={(e) => handleVolumeChange(channel, parseInt(e.target.value))}
                  style={styles.slider}
                  disabled={settings.muted}
                />
                <span style={styles.volumeValue}>
                  {Math.round(settings.volume * 100)}%
                </span>
              </div>
            </div>
          ))}
          
          <div style={styles.info}>
            <p><strong>Spatial Audio:</strong> {mixerState.hearingRadius} tiles radius</p>
            <p><strong>Active Loops:</strong> {mixerState.activeLoops.length}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2000
  },
  panel: {
    background: '#1e1e1e',
    borderRadius: '8px',
    padding: '20px',
    minWidth: '400px',
    maxWidth: '500px',
    color: 'white',
    boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    borderBottom: '2px solid #333',
    paddingBottom: '10px'
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: 'white',
    fontSize: '24px',
    cursor: 'pointer',
    padding: '0 10px'
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px'
  },
  channelRow: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    padding: '10px',
    background: 'rgba(255,255,255,0.05)',
    borderRadius: '4px'
  },
  channelLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  channelName: {
    fontSize: '14px',
    fontWeight: 'bold'
  },
  muteBtn: {
    border: 'none',
    borderRadius: '4px',
    padding: '4px 12px',
    cursor: 'pointer',
    fontSize: '16px',
    color: 'white'
  },
  sliderContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px'
  },
  slider: {
    flex: 1,
    height: '6px',
    borderRadius: '3px',
    outline: 'none',
    background: '#333',
    cursor: 'pointer'
  },
  volumeValue: {
    minWidth: '45px',
    textAlign: 'right',
    fontSize: '12px',
    color: '#aaa'
  },
  info: {
    marginTop: '10px',
    padding: '10px',
    background: 'rgba(255,255,255,0.03)',
    borderRadius: '4px',
    fontSize: '12px',
    color: '#aaa'
  }
};

export default AudioMixerUI;
