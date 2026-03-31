/**
 * Audio Mixer System
 * 
 * Features:
 * - Multiple audio channels (Ambient, SFX, Animals)
 * - Volume control per channel
 * - Spatial audio (distance-based)
 * - Random interval sounds
 */

class AudioMixer {
  constructor() {
    this.channels = {
      master: { volume: 0.7, muted: false },
      ambient: { volume: 0.3, muted: false },
      sfx: { volume: 0.5, muted: false },
      animals: { volume: 0.4, muted: false }
    };
    
    this.audioElements = {};
    this.activeLoops = new Set();
    this.spatialSounds = new Map(); // Track sounds with position
    this.randomIntervals = new Map();
    
    // Camera position (for spatial audio)
    this.cameraX = 0;
    this.cameraY = 0;
    this.hearingRadius = 20; // tiles
  }
  
  /**
   * Initialize audio element
   */
  registerAudio(id, audioElement, channel = 'sfx') {
    this.audioElements[id] = {
      element: audioElement,
      channel: channel,
      baseVolume: audioElement.volume
    };
  }
  
  /**
   * Play sound on specific channel
   */
  play(id, options = {}) {
    const audio = this.audioElements[id];
    if (!audio) {
      console.warn(`[AudioMixer] Sound '${id}' not registered`);
      return;
    }
    
    const channelVolume = this.channels[audio.channel].volume;
    const masterVolume = this.channels.master.volume;
    const isMuted = this.channels[audio.channel].muted || this.channels.master.muted;
    
    if (isMuted) {
      return; // Don't play if muted
    }
    
    // Calculate final volume
    let finalVolume = audio.baseVolume * channelVolume * masterVolume;
    
    // Spatial audio: reduce volume based on distance
    if (options.x !== undefined && options.y !== undefined) {
      const distance = this.getDistance(options.x, options.y);
      const spatialMultiplier = this.getSpatialMultiplier(distance);
      finalVolume *= spatialMultiplier;
      
      if (spatialMultiplier === 0) {
        return; // Too far, don't play
      }
    }
    
    audio.element.volume = Math.min(1, finalVolume);
    audio.element.currentTime = 0; // Reset to start
    audio.element.play().catch(err => {
      console.log(`[AudioMixer] Play failed for '${id}':`, err.message);
    });
  }
  
  /**
   * Play looping sound (ambient, etc.)
   */
  playLoop(id) {
    const audio = this.audioElements[id];
    if (!audio) return;
    
    audio.element.loop = true;
    this.play(id);
    this.activeLoops.add(id);
  }
  
  /**
   * Stop loop
   */
  stopLoop(id) {
    const audio = this.audioElements[id];
    if (!audio) return;
    
    audio.element.pause();
    audio.element.currentTime = 0;
    this.activeLoops.delete(id);
  }
  
  /**
   * Start random interval sound (animal bark, etc.)
   */
  startRandomSound(id, minInterval = 5000, maxInterval = 15000, options = {}) {
    const playRandom = () => {
      // Random chance to play (50%)
      if (Math.random() > 0.5) {
        this.play(id, options);
      }
      
      // Schedule next
      const nextDelay = minInterval + Math.random() * (maxInterval - minInterval);
      const timeout = setTimeout(playRandom, nextDelay);
      this.randomIntervals.set(id, timeout);
    };
    
    // Start first sound
    playRandom();
  }
  
  /**
   * Stop random interval sound
   */
  stopRandomSound(id) {
    const timeout = this.randomIntervals.get(id);
    if (timeout) {
      clearTimeout(timeout);
      this.randomIntervals.delete(id);
    }
  }
  
  /**
   * Set volume for channel (0-1)
   */
  setVolume(channel, volume) {
    if (this.channels[channel]) {
      this.channels[channel].volume = Math.max(0, Math.min(1, volume));
      this.updateActiveLoops();
    }
  }
  
  /**
   * Mute/unmute channel
   */
  setMuted(channel, muted) {
    if (this.channels[channel]) {
      this.channels[channel].muted = muted;
      this.updateActiveLoops();
    }
  }
  
  /**
   * Update camera position (for spatial audio)
   */
  updateCameraPosition(x, y) {
    this.cameraX = x;
    this.cameraY = y;
  }
  
  /**
   * Calculate distance from camera
   */
  getDistance(x, y) {
    const dx = x - this.cameraX;
    const dy = y - this.cameraY;
    return Math.sqrt(dx * dx + dy * dy);
  }
  
  /**
   * Get volume multiplier based on distance
   * 0 = too far (no sound)
   * 1 = very close (full volume)
   */
  getSpatialMultiplier(distance) {
    if (distance <= this.hearingRadius * 0.5) {
      return 1; // Full volume in center
    } else if (distance <= this.hearingRadius) {
      // Linear falloff
      const ratio = (this.hearingRadius - distance) / (this.hearingRadius * 0.5);
      return ratio;
    } else {
      return 0; // Too far
    }
  }
  
  /**
   * Update volumes of active looping sounds
   */
  updateActiveLoops() {
    this.activeLoops.forEach(id => {
      const audio = this.audioElements[id];
      if (!audio) return;
      
      const channelVolume = this.channels[audio.channel].volume;
      const masterVolume = this.channels.master.volume;
      const isMuted = this.channels[audio.channel].muted || this.channels.master.muted;
      
      if (isMuted) {
        audio.element.volume = 0;
      } else {
        audio.element.volume = audio.baseVolume * channelVolume * masterVolume;
      }
    });
  }
  
  /**
   * Clean up all sounds
   */
  cleanup() {
    // Stop all loops
    this.activeLoops.forEach(id => this.stopLoop(id));
    
    // Clear all random intervals
    this.randomIntervals.forEach((timeout, id) => {
      clearTimeout(timeout);
    });
    this.randomIntervals.clear();
  }
  
  /**
   * Get current mixer state (for UI)
   */
  getState() {
    return {
      channels: { ...this.channels },
      activeLoops: Array.from(this.activeLoops),
      hearingRadius: this.hearingRadius
    };
  }
}

// Singleton instance
export const audioMixer = new AudioMixer();
export default AudioMixer;
