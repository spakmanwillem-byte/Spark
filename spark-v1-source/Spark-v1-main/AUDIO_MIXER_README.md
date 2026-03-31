# 🎛️ Spark Audio Mixer System

## Probleem

Met meerdere audio bronnen in Spark:
- 🗣️ **TTS Voice** (Spark's stem)
- ⚙️ **System Sounds** (button clicks, alerts)
- 👤 **User Sounds** (trigger woorden zoals "koe")
- 🎵 **Background Music** (optioneel)

...kunnen geluiden elkaar overschreeuwen, gelijktijdig afspelen (chaos!), of belangrijke TTS voice overspoelen.

## Oplossing: Audio Mixer met Prioriteit

### 🎯 Features

**1. Priority-based Channels**
```
Priority 100: TTS Voice      (hoogste)
Priority  80: System Sounds  (hoog)
Priority  60: User Sounds    (medium)
Priority  20: Background     (laagste)
```

**2. Ducking (Automatisch volume dempen)**
- Als TTS voice speelt → andere geluiden naar 30% volume
- Als TTS stopt → volume terug naar normaal
- Smooth fades (200-300ms)

**3. Queue Management**
- Max 3 sounds tegelijk (instelbaar)
- Extra sounds gaan in queue
- Hoogste prioriteit eerst

**4. Volume Controls**
- Master volume (alles)
- Per-channel volume (TTS, system, user, background)
- Real-time aanpasbaar

### 📊 Hoe het werkt

```javascript
import audioMixer from './utils/audioMixer';

// Initialize (1x, bij user interaction)
await audioMixer.initialize();

// Play TTS (hoogste prioriteit)
await audioMixer.playSound('/api/tts/audio.mp3', {
  channel: 'tts',
  onEnded: () => console.log('TTS finished')
});

// Play system sound (high priority)
await audioMixer.playSound('/api/sounds/stream/success.mp3', {
  channel: 'system'
});

// Play user sound (medium priority)
await audioMixer.playSound('/api/sounds/stream/koe.mp3', {
  channel: 'user',
  id: 'koe_sound'
});

// Adjust volumes
audioMixer.setMasterVolume(70);        // 0-100
audioMixer.setChannelVolume('tts', 100);
audioMixer.setChannelVolume('user', 60);

// Get stats
const stats = audioMixer.getStats();
console.log(stats);
// {
//   initialized: true,
//   activeCount: 2,
//   queuedCount: 1,
//   activeSounds: [...]
// }
```

### 🔧 Settings

```javascript
audioMixer.settings = {
  masterVolume: 70,              // Master volume
  channelVolumes: {
    tts: 100,                    // TTS voice volume
    system: 80,                  // System sounds
    user: 70,                    // User sounds
    background: 40               // Background music
  },
  duckingEnabled: true,          // Auto-duck tijdens TTS?
  duckingAmount: 0.3,            // Duck naar 30% volume
  simultaneousLimit: 3           // Max 3 sounds tegelijk
};
```

### 🎬 Ducking Demo

**Zonder ducking:**
```
User sound: "koe" 🐄 (100% volume)
TTS: "Ja, koe is een dier" 🗣️ (100% volume)
→ Chaos! Beide overschreeuwen elkaar
```

**Met ducking:**
```
User sound: "koe" 🐄 (100% volume)
TTS start → "koe" gaat naar 30% 🔉
TTS: "Ja, koe is een dier" 🗣️ (100% volume)
TTS eindigt → "koe" terug naar 100% 🔊
```

### 📋 Integratie in Spark

**App.js updates nodig:**

```javascript
import audioMixer from './utils/audioMixer';

// Initialize bij eerste user interaction
useEffect(() => {
  const initAudio = async () => {
    await audioMixer.initialize();
  };
  // Trigger bij eerste click/tap
  document.addEventListener('click', initAudio, { once: true });
}, []);

// Replace playSound functie
const playSound = async (filename, channel = 'user') => {
  const audioUrl = `${API}/sounds/stream/${filename}`;
  await audioMixer.playSound(audioUrl, { channel });
};

// Replace playTextToSpeech
const playTextToSpeech = async (text, ttsSettings) => {
  try {
    const response = await axios.post(`${API}/voice/tts`, {
      text,
      voice: ttsSettings.voice,
      model: ttsSettings.model,
      speed: ttsSettings.speed
    });
    
    const audioUrl = URL.createObjectURL(response.data);
    await audioMixer.playSound(audioUrl, {
      channel: 'tts',
      onEnded: () => URL.revokeObjectURL(audioUrl)
    });
  } catch (error) {
    console.error('[TTS] Error:', error);
  }
};

// System sounds (button clicks, etc)
const playSystemSound = (filename) => {
  const audioUrl = `${API}/sounds/stream/${filename}`;
  audioMixer.playSound(audioUrl, { channel: 'system' });
};
```

### 🎚️ Settings UI Integration

In `SettingsTabNew.js` → "Geluid" tab:

```jsx
<div>
  <label>Master Volume: {audioMixer.settings.masterVolume}%</label>
  <input 
    type="range" 
    min="0" 
    max="100" 
    value={audioMixer.settings.masterVolume}
    onChange={(e) => audioMixer.setMasterVolume(e.target.value)}
  />
</div>

<div>
  <label>TTS Volume: {audioMixer.settings.channelVolumes.tts}%</label>
  <input 
    type="range" 
    min="0" 
    max="100" 
    value={audioMixer.settings.channelVolumes.tts}
    onChange={(e) => audioMixer.setChannelVolume('tts', e.target.value)}
  />
</div>

<div>
  <label>User Sounds Volume: {audioMixer.settings.channelVolumes.user}%</label>
  <input 
    type="range" 
    min="0" 
    max="100" 
    value={audioMixer.settings.channelVolumes.user}
    onChange={(e) => audioMixer.setChannelVolume('user', e.target.value)}
  />
</div>

<div>
  <label>
    <input 
      type="checkbox"
      checked={audioMixer.settings.duckingEnabled}
      onChange={(e) => audioMixer.settings.duckingEnabled = e.target.checked}
    />
    Ducking (TTS dempt andere geluiden)
  </label>
</div>
```

### 🎯 Benefits

✅ **Geen chaos meer**: Sounds worden netjes gemixt
✅ **TTS altijd verstaanbaar**: Auto-ducking dempt andere geluiden
✅ **Controle**: Volume per channel
✅ **Performance**: Web Audio API (hardware accelerated)
✅ **Queue**: Geen gemiste sounds
✅ **Priority**: Belangrijke sounds eerst

### 🚀 Implementatie Stappen

1. ✅ Audio Mixer class aangemaakt (`/app/frontend/src/utils/audioMixer.js`)
2. ⏳ App.js updaten om mixer te gebruiken
3. ⏳ Settings UI updaten met channel volumes
4. ⏳ TTS/STT integreren met mixer
5. ⏳ Testing met meerdere simultane sounds

### 🐛 Known Issues & TODO

**STT (Speech-to-Text):**
- Backend route checken (`/api/voice/stt`)
- Frontend VoiceControls component checken
- Mic permissions & browser compatibility

**TTS (Text-to-Speech):**
- Backend route checken (`/api/voice/tts`)
- OpenAI TTS API key (als gebruikt)
- Response format (audio blob)

**Mixer:**
- Browser compatibility (Web Audio API)
- Mobile audio autoplay restrictions
- Persist settings in localStorage

---

**Status:** 🟡 Audio Mixer gebouwd, integratie in App.js TODO
