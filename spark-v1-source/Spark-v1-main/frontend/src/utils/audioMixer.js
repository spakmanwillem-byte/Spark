/**
 * SPARK AUDIO MIXER SYSTEM
 * 
 * Centraal audio management systeem voor Spark Core 4.1
 * Handelt meerdere audio bronnen met prioriteit en volume mixing
 * 
 * Audio Channels:
 * 1. TTS Voice (Spark's stem) - Hoogste prioriteit
 * 2. System Sounds (alerts, errors) - Hoge prioriteit  
 * 3. User Sounds (trigger woorden) - Medium prioriteit
 * 4. Background Music - Laagste prioriteit
 * 
 * Features:
 * - Priority-based ducking (TTS dempt andere geluiden)
 * - Queue management (sounds in volgorde)
 * - Volume per channel
 * - Simultane playback met mixing
 */

class SparkAudioMixer {
  constructor() {
    // Audio Context (Web Audio API)
    this.audioContext = null;
    this.masterGain = null;
    
    // Channel Gains (aparte volume controls per type)
    this.channelGains = {
      tts: null,        // Text-to-Speech
      system: null,     // System sounds (Spark-system)
      user: null,       // User sounds
      background: null  // Background music
    };
    
    // Priority levels
    this.priorities = {
      tts: 100,
      system: 80,
      user: 60,
      background: 20
    };
    
    // Active audio sources
    this.activeSources = new Map();
    
    // Queue voor sounds die moeten wachten
    this.soundQueue = [];
    
    // Settings
    this.settings = {
      masterVolume: 70,
      channelVolumes: {
        tts: 100,
        system: 80,
        user: 70,
        background: 40
      },
      duckingEnabled: true,      // TTS dempt andere geluiden
      duckingAmount: 0.3,        // 70% volume reduction tijdens TTS
      simultaneousLimit: 3       // Max 3 sounds tegelijk
    };
    
    this.initialized = false;
  }
  
  /**
   * Initialize Audio Context (moet door user interaction)
   */
  async initialize() {
    if (this.initialized) return;
    
    try {
      // Create AudioContext
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      
      // Master gain node
      this.masterGain = this.audioContext.createGain();
      this.masterGain.connect(this.audioContext.destination);
      this.setMasterVolume(this.settings.masterVolume);
      
      // Create channel gain nodes
      for (const channel in this.channelGains) {
        const gain = this.audioContext.createGain();
        gain.connect(this.masterGain);
        this.channelGains[channel] = gain;
        this.setChannelVolume(channel, this.settings.channelVolumes[channel]);
      }
      
      this.initialized = true;
      console.log('[AUDIO MIXER] Initialized successfully');
      return true;
    } catch (error) {
      console.error('[AUDIO MIXER] Initialization failed:', error);
      return false;
    }
  }
  
  /**
   * Set master volume (0-100)
   */
  setMasterVolume(volume) {
    this.settings.masterVolume = volume;
    if (this.masterGain) {
      this.masterGain.gain.value = volume / 100;
    }
  }
  
  /**
   * Set channel volume (0-100)
   */
  setChannelVolume(channel, volume) {
    this.settings.channelVolumes[channel] = volume;
    if (this.channelGains[channel]) {
      this.channelGains[channel].gain.value = volume / 100;
    }
  }
  
  /**
   * Play audio via URL met channel type
   */
  async playSound(url, options = {}) {
    const {
      channel = 'user',      // tts, system, user, background
      onEnded = null,
      priority = null,
      id = `sound_${Date.now()}`
    } = options;
    
    if (!this.initialized) {
      await this.initialize();
    }
    
    const actualPriority = priority || this.priorities[channel];
    
    // Check simultaneous limit
    if (this.activeSources.size >= this.settings.simultaneousLimit) {
      // Queue if priority is lower than lowest active
      const lowestActive = Math.min(...Array.from(this.activeSources.values()).map(s => s.priority));
      if (actualPriority <= lowestActive) {
        this.soundQueue.push({ url, options, id });
        console.log(`[AUDIO MIXER] Queued: ${id} (${channel})`);
        return;
      }
    }
    
    try {
      // Fetch audio data
      const response = await fetch(url);
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      
      // Create source
      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      
      // Connect to channel gain
      source.connect(this.channelGains[channel]);
      
      // Apply ducking if TTS is playing
      if (channel === 'tts' && this.settings.duckingEnabled) {
        this.applyDucking();
      }
      
      // Track active source
      this.activeSources.set(id, {
        source,
        channel,
        priority: actualPriority,
        startTime: Date.now()
      });
      
      // Handle end
      source.onended = () => {
        this.activeSources.delete(id);
        console.log(`[AUDIO MIXER] Ended: ${id} (${channel})`);
        
        // Remove ducking if TTS ended
        if (channel === 'tts') {
          this.removeDucking();
        }
        
        // Process queue
        this.processQueue();
        
        if (onEnded) onEnded();
      };
      
      // Play
      source.start(0);
      console.log(`[AUDIO MIXER] Playing: ${id} (${channel}, priority: ${actualPriority})`);
      
    } catch (error) {
      console.error(`[AUDIO MIXER] Error playing ${id}:`, error);
      this.activeSources.delete(id);
    }
  }
  
  /**
   * Apply ducking (reduce volume of non-TTS sounds)
   */
  applyDucking() {
    if (!this.settings.duckingEnabled) return;
    
    const duckTo = this.settings.duckingAmount;
    const duckTime = 0.2; // 200ms fade
    
    for (const channel of ['system', 'user', 'background']) {
      if (this.channelGains[channel]) {
        const currentVolume = this.settings.channelVolumes[channel] / 100;
        this.channelGains[channel].gain.setTargetAtTime(
          currentVolume * duckTo,
          this.audioContext.currentTime,
          duckTime
        );
      }
    }
    
    console.log('[AUDIO MIXER] Ducking applied (TTS priority)');
  }
  
  /**
   * Remove ducking (restore original volumes)
   */
  removeDucking() {
    const restoreTime = 0.3; // 300ms fade
    
    for (const channel of ['system', 'user', 'background']) {
      if (this.channelGains[channel]) {
        const originalVolume = this.settings.channelVolumes[channel] / 100;
        this.channelGains[channel].gain.setTargetAtTime(
          originalVolume,
          this.audioContext.currentTime,
          restoreTime
        );
      }
    }
    
    console.log('[AUDIO MIXER] Ducking removed (TTS ended)');
  }
  
  /**
   * Process queued sounds
   */
  processQueue() {
    if (this.soundQueue.length === 0) return;
    if (this.activeSources.size >= this.settings.simultaneousLimit) return;
    
    // Get highest priority sound from queue
    this.soundQueue.sort((a, b) => {
      const aPrio = a.options.priority || this.priorities[a.options.channel || 'user'];
      const bPrio = b.options.priority || this.priorities[b.options.channel || 'user'];
      return bPrio - aPrio;
    });
    
    const next = this.soundQueue.shift();
    if (next) {
      this.playSound(next.url, next.options);
    }
  }
  
  /**
   * Stop all sounds in a channel
   */
  stopChannel(channel) {
    for (const [id, source] of this.activeSources.entries()) {
      if (source.channel === channel) {
        source.source.stop();
        this.activeSources.delete(id);
      }
    }
  }
  
  /**
   * Stop all sounds
   */
  stopAll() {
    for (const [id, source] of this.activeSources.entries()) {
      source.source.stop();
    }
    this.activeSources.clear();
    this.soundQueue = [];
  }
  
  /**
   * Get mixer stats
   */
  getStats() {
    return {
      initialized: this.initialized,
      activeCount: this.activeSources.size,
      queuedCount: this.soundQueue.length,
      activeSounds: Array.from(this.activeSources.entries()).map(([id, s]) => ({
        id,
        channel: s.channel,
        priority: s.priority,
        duration: Date.now() - s.startTime
      }))
    };
  }
}

// Export singleton instance
export const audioMixer = new SparkAudioMixer();
export default audioMixer;
