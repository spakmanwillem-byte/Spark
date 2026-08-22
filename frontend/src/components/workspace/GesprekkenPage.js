import React, { useState, useRef, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import { UserAvatar } from '../common/UserAvatar';
import DnDBarkPanel from '../dnd/DnDBarkPanel';
import { ContactCallPopup } from '../chat/ContactCallPopup';
import { PriveCallBark } from '../chat/PriveCallBark';
import { IncomingCallBark } from '../chat/IncomingCallBark';
import { RpsBark } from '../games/RpsBark';
import {
  MessageSquare, Send, Plus, Search, Users, Lock,
  Sparkles, Phone, Video, Bot, Circle, BookOpen, Zap,
  Shield, Timer, Mic, MicOff, Volume2, VolumeX
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

/* Ambient player — singleton via window zodat hij blijft afspelen tussen pagina-switches.
   v4_ambient_persist_001: localStorage persistence over F5/refresh. */
const AMBIENT_LS_KEY = 'spark_ambient_state';
const getAmbientPlayer = () => {
  if (typeof window === 'undefined') return null;
  if (!window.__sparkAmbient) {
    const player = {
      audio: null,
      label: null,
      url: null,
      volume: 0.4,
      pendingResume: false,
      _saveState() {
        try {
          if (this.url) localStorage.setItem(AMBIENT_LS_KEY, JSON.stringify({ url: this.url, label: this.label, volume: this.volume }));
          else localStorage.removeItem(AMBIENT_LS_KEY);
        } catch {}
      },
      _loadState() {
        try {
          const raw = localStorage.getItem(AMBIENT_LS_KEY);
          return raw ? JSON.parse(raw) : null;
        } catch { return null; }
      },
      _broadcast() {
        window.dispatchEvent(new CustomEvent('spark:ambient', { detail: {
          playing: !!this.audio && !this.audio.paused,
          paused_pending: this.pendingResume,
          label: this.label,
        } }));
      },
      play(url, label) {
        try {
          if (this.audio) { this.audio.pause(); this.audio = null; }
          const a = new Audio(url);
          a.loop = true;
          a.volume = this.volume;
          const playPromise = a.play();
          this.audio = a;
          this.label = label;
          this.url = url;
          this.pendingResume = false;
          this._saveState();
          if (playPromise && typeof playPromise.catch === 'function') {
            playPromise.catch(() => {
              // Autoplay geweigerd — wacht op user-gesture
              this.pendingResume = true;
              this._armResumeListener();
              this._broadcast();
            });
          }
          this._broadcast();
        } catch {}
      },
      stop() {
        if (this.audio) { try { this.audio.pause(); } catch {} this.audio = null; }
        this.label = null;
        this.url = null;
        this.pendingResume = false;
        this._saveState();
        this._broadcast();
      },
      resume() {
        if (!this.url) return;
        if (this.audio && this.audio.paused) {
          this.audio.play().then(() => {
            this.pendingResume = false;
            this._broadcast();
          }).catch(() => {});
        } else if (!this.audio) {
          this.play(this.url, this.label);
        }
      },
      _armResumeListener() {
        const tryResume = () => {
          this.resume();
          if (this.audio && !this.audio.paused) {
            window.removeEventListener('click', tryResume, true);
            window.removeEventListener('keydown', tryResume, true);
            window.removeEventListener('touchstart', tryResume, true);
          }
        };
        window.addEventListener('click', tryResume, true);
        window.addEventListener('keydown', tryResume, true);
        window.addEventListener('touchstart', tryResume, true);
      },
      isPlaying() { return !!this.audio && !this.audio.paused; },
      isPendingResume() { return this.pendingResume; },
      restoreFromStorage() {
        const s = this._loadState();
        if (!s || !s.url || this.audio) return false;
        this.play(s.url, s.label);
        return true;
      },
    };
    window.__sparkAmbient = player;
    // Probeer ambient terug te zetten na refresh
    player.restoreFromStorage();
  }
  return window.__sparkAmbient;
};

// v5_bot_color_scheme_001 — defaults; worden overschreven via /api/settings/system
const BOT_COLOR_DEFAULTS = {
  'bot-madelief':   { bg: 'bg-pink-500/10',    text: 'text-pink-400',    border: 'border-pink-500/20',    icon: Sparkles, accent: '#ec4899' },
  'bot-harry':      { bg: 'bg-cyan-500/10',    text: 'text-cyan-400',    border: 'border-cyan-500/20',    icon: Timer,    accent: '#06b6d4' },
  'bot-smith':      { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', icon: Shield,   accent: '#10b981' },
  'bot-boekhouder': { bg: 'bg-amber-500/10',   text: 'text-amber-400',   border: 'border-amber-500/20',   icon: Bot,      accent: '#f59e0b' },
  'bot-dood':       { bg: 'bg-purple-500/10',  text: 'text-purple-400',  border: 'border-purple-500/20',  icon: Bot,      accent: '#a855f7' },
};
// Mutable runtime cache — gevuld bij eerste fetch en bij admin save (via storage event)
const BOT_COLORS = { ...BOT_COLOR_DEFAULTS };

function _hexToTailwindStyle(hex) {
  // Returnt inline styles voor bg + text + border met opacity
  return {
    bg: `${hex}1a`,        // 10% opacity
    text: hex,
    border: `${hex}33`,    // 20% opacity
    accent: hex,
  };
}

async function _refreshBotColors() {
  try {
    const r = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/settings/system`).then(x => x.json());
    const s = r?.settings || {};
    const map = {
      'bot-madelief':   s.bot_color_madelief,
      'bot-harry':      s.bot_color_harry,
      'bot-smith':      s.bot_color_smith,
      'bot-boekhouder': s.bot_color_boekhouder,
      'bot-dood':       s.bot_color_dood,
    };
    Object.entries(map).forEach(([botId, hex]) => {
      if (hex && /^#[0-9a-fA-F]{6}$/.test(hex)) {
        const ts = _hexToTailwindStyle(hex);
        BOT_COLORS[botId] = {
          ...(BOT_COLOR_DEFAULTS[botId] || {}),
          ...ts,
        };
      }
    });
  } catch {}
}
// Initial fetch
_refreshBotColors();

const initialSparkMessages = [];

// SessionStorage helpers — chat blijft staan tussen page-switches, wist bij logout/tab-close
const chatStorageKey = (userId) => `spark_chat_session_${userId || 'guest'}`;
const loadStoredMessages = (userId) => {
  try {
    const raw = sessionStorage.getItem(chatStorageKey(userId));
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : null;
  } catch {
    return null;
  }
};
const saveStoredMessages = (userId, messages) => {
  try {
    sessionStorage.setItem(chatStorageKey(userId), JSON.stringify(messages));
  } catch {
    // Storage quota / private mode — graceful fail
  }
};

// v6_deep_persist_001 — Diep-modus blijft staan over tab-switches heen
const deepModeKey = (userId) => `spark_deep_mode_${userId || 'guest'}`;
const loadDeepMode = (userId, fallback) => {
  try {
    const raw = sessionStorage.getItem(deepModeKey(userId));
    if (raw === null) return fallback;
    return raw === '1' || raw === 'true';
  } catch {
    return fallback;
  }
};
const saveDeepMode = (userId, value) => {
  try {
    sessionStorage.setItem(deepModeKey(userId), value ? '1' : '0');
  } catch {
    // graceful fail
  }
};

export function GesprekkenPage({ onNavigate }) {
  const { user, adminModeActive } = useAuth();
  const userId = user?.id || 'user-001';
  const userName = user?.naam || 'Gebruiker';
  const userGradatie = user?.gradatie ?? 2;
  const isAdmin = userGradatie === 1;

  const [activeTab, setActiveTab] = useState('spark');
  // Lazy init: bij eerste render check sessionStorage. Behoud chat tussen page-switches.
  const [sparkMessages, setSparkMessages] = useState(() => loadStoredMessages(userId) || initialSparkMessages);
  const [newMessage, setNewMessage] = useState('');
  const [selectedContact, setSelectedContact] = useState(null);

  // v4_actions_001 — STT + ambient + TTS state
  const [sttEnabled, setSttEnabled] = useState(false);
  const [sttListening, setSttListening] = useState(false);
  const [ambientPlaying, setAmbientPlaying] = useState(false);
  const [ambientLabel, setAmbientLabel] = useState(null);
  const [ambientPendingResume, setAmbientPendingResume] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [ttsSpeaking, setTtsSpeaking] = useState(false); // v4_voice_002 — TTS-glow
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const sparkAudioRef = useRef(null);

  // v4_voice_002 — Silence detection refs + effective settings
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const silenceRafRef = useRef(null);
  const silenceStartRef = useRef(null);
  const sttStreamRef = useRef(null);
  const autoSendPendingRef = useRef(false);
  const voiceLoopRef = useRef(false); // v4_voice_002 — continue voice mode (re-arm mic na TTS)
  const [voiceCfg, setVoiceCfg] = useState({ stt_silence_sec: 2.0, tts_enabled: false, tts_voice: 'nova', tts_speed: 1.0, tts_auto_play: false });

  // Load user-effective settings (silence threshold, tts voice/speed, etc.)
  useEffect(() => {
    if (!userId) return;
    fetch(`${API}/api/settings/effective/${userId}`)
      .then(r => r.json())
      .then(d => {
        const e = d?.effective || {};
        setVoiceCfg({
          stt_silence_sec: Number(e.stt_silence_sec) || 2.0,
          tts_enabled: !!e.tts_enabled,
          tts_voice: e.tts_voice || 'nova',
          tts_speed: Number(e.tts_speed) || 1.0,
          tts_auto_play: !!e.tts_auto_play,
        });
        // Sync TTS toggle uit settings (zodat Spark direct kan spreken als user dat aan heeft staan)
        if (e.tts_enabled) setTtsEnabled(true);
      })
      .catch(() => {});
  }, [userId]);

  // Sync met singleton ambient state bij eerste render + via events
  useEffect(() => {
    const player = getAmbientPlayer();
    if (player?.isPlaying()) {
      setAmbientPlaying(true);
      setAmbientLabel(player.label);
    } else if (player?.isPendingResume()) {
      setAmbientPendingResume(true);
      setAmbientLabel(player.label);
    }
    const handler = (e) => {
      setAmbientPlaying(!!e.detail.playing);
      setAmbientPendingResume(!!e.detail.paused_pending);
      setAmbientLabel(e.detail.label || null);
    };
    window.addEventListener('spark:ambient', handler);
    return () => window.removeEventListener('spark:ambient', handler);
  }, []);

  // v4_voice_002 — Cleanup bij unmount (mic stream, audio context, TTS audio)
  useEffect(() => {
    return () => {
      try { mediaRecorderRef.current?.stop(); } catch {}
      try { sttStreamRef.current?.getTracks()?.forEach(t => t.stop()); } catch {}
      try { audioCtxRef.current?.close(); } catch {}
      if (silenceRafRef.current) cancelAnimationFrame(silenceRafRef.current);
      try { sparkAudioRef.current?.pause(); } catch {}
    };
  }, []);

  // Persist messages naar sessionStorage bij elke wijziging
  useEffect(() => {
    saveStoredMessages(userId, sparkMessages);
  }, [sparkMessages, userId]);

  // Als user wisselt (bv. login als ander account) → laad hun eigen sessie of reset
  useEffect(() => {
    const stored = loadStoredMessages(userId);
    setSparkMessages(stored || initialSparkMessages);
  }, [userId]);

  // Community bot state
  const [communityMessages, setCommunityMessages] = useState([]);
  const [bots, setBots] = useState([]);
  const [communityLoading, setCommunityLoading] = useState(false);
  const [sendingCommunity, setSendingCommunity] = useState(false);
  // v6_dnd_bark_001 — Spark World D&D bark-flow modal in community-tab
  const [showSparkWorld, setShowSparkWorld] = useState(false);
  // v6_rps_001 — Steen-Papier-Schaar mini-game bark
  const [rpsOpen, setRpsOpen] = useState(false);
  // v12_contact_call_001 — WhatsApp deep-link popup
  const [contactCallAction, setContactCallAction] = useState(null);

  // v4_community_session_start_001 — alleen berichten vanaf inlog tonen
  const [communitySessionStart] = useState(() => {
    const key = `community_session_start_${userId}`;
    let ts = sessionStorage.getItem(key);
    if (!ts) {
      ts = new Date().toISOString();
      sessionStorage.setItem(key, ts);
    }
    return ts;
  });
  // v4_spark_avatar_in_chat_001 — toon Spark's eigen avatar i.p.v. ster
  const [sparkAvatarUrl, setSparkAvatarUrl] = useState(null);
  useEffect(() => {
    fetch(`${API}/api/avatar/current/user-000`)
      .then(r => r.json())
      .then(d => setSparkAvatarUrl(d.url ? `${API}${d.url}` : (d.fallback_url ? `${API}${d.fallback_url}` : null)))
      .catch(() => {});
  }, []);

  // v4_dnd_001 — Spark observatie greeting bij openen Spark AI tab (1x per sessie)
  useEffect(() => {
    if (activeTab !== 'spark' || !userId) return;
    const sessionKey = `spark_greeted_${userId}`;
    if (sessionStorage.getItem(sessionKey)) return;
    fetch(`${API}/api/dnd/spark-greeting/${userId}`)
      .then(r => r.json())
      .then(d => {
        if (d.has_greeting && d.message) {
          sessionStorage.setItem(sessionKey, '1');
          // Inject als Spark-bubble vooraan
          const greetingMsg = {
            id: `greet-${Date.now()}`,
            role: 'assistant',
            content: d.message,
            timestamp: new Date().toISOString(),
            is_observation: true,
          };
          setSparkMessages(prev => [...prev, greetingMsg]);
        }
      })
      .catch(() => {});
  }, [activeTab, userId]);

  // Privé contacten + messages (v4_contacts_001)
  const [priveContacts, setPriveContacts] = useState([]);
  const [priveLoading, setPriveLoading] = useState(false);
  const [priveMessages, setPriveMessages] = useState([]);
  const [priveSearch, setPriveSearch] = useState('');
  const [sendingPrive, setSendingPrive] = useState(false);

  // v13_prive_call_ui_001 — UI-shell voor bel/beeld in privé chat header
  const [callBark, setCallBark] = useState({ open: false, mode: 'audio' });
  const openPriveCall = (mode) => {
    if (!selectedContact) return;
    // Stuur ook een lokaal 'ring'-signaal naar de ontvanger (voor incoming bark)
    if (selectedContact?.id) {
      fetch(`${API}/api/prive-call/ring`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_user_id: userId, to_user_id: selectedContact.id, mode }),
      }).catch(() => {});
    }
    setCallBark({ open: true, mode });
  };
  const closePriveCall = () => setCallBark((s) => ({ ...s, open: false }));

  // v13_prive_incoming_call_001 — poll inkomende oproepen elke 4s
  const [incomingCall, setIncomingCall] = useState(null);
  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    const pollIncoming = async () => {
      try {
        const r = await fetch(`${API}/api/prive-call/incoming/${userId}`);
        const d = await r.json();
        if (cancelled) return;
        const active = (d.calls || []).find((c) => c.state === 'ringing');
        setIncomingCall((prev) => {
          if (active && (!prev || prev.id !== active.id)) return active;
          if (!active && prev) return null;
          return prev;
        });
      } catch { /* ignore */ }
    };
    pollIncoming();
    const t = setInterval(pollIncoming, 4000);
    return () => { cancelled = true; clearInterval(t); };
  }, [userId]);

  const answerIncoming = async (action) => {
    if (!incomingCall) return;
    try {
      await fetch(`${API}/api/prive-call/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, call_id: incomingCall.id, action }),
      });
    } catch { /* ignore */ }
    if (action === 'accept') {
      // Open bark, contact is de beller
      const callerContact = priveContacts.find((c) => c.id === incomingCall.from_user_id) || {
        id: incomingCall.from_user_id, naam: 'Onbekend', online: true,
      };
      setSelectedContact(callerContact);
      setCallBark({ open: true, mode: incomingCall.mode || 'audio' });
    }
    setIncomingCall(null);
  };

  const loadPriveContacts = async () => {
    if (!userId) return;
    setPriveLoading(true);
    try {
      const res = await fetch(`${API}/api/contacts/list?user_id=${userId}`);
      const data = await res.json();
      setPriveContacts(data.contacts || []);
    } catch { /* graceful */ }
    setPriveLoading(false);
  };

  // Laad contacten als Privé tab geopend
  useEffect(() => {
    if (activeTab !== 'prive') return;
    loadPriveContacts();
    const interval = setInterval(loadPriveContacts, 30_000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, userId]);

  // Laad messages voor geselecteerd contact
  const loadPriveMessages = async (contactId) => {
    if (!contactId) return;
    try {
      const res = await fetch(`${API}/api/contacts/messages?user_id=${userId}&contact_id=${contactId}`);
      const data = await res.json();
      setPriveMessages(data.messages || []);
    } catch { /* graceful */ }
  };

  useEffect(() => {
    if (activeTab !== 'prive' || !selectedContact?.id) return;
    loadPriveMessages(selectedContact.id);
    const interval = setInterval(() => loadPriveMessages(selectedContact.id), 5_000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, selectedContact?.id, userId]);

  // v13_no_auto_welcome_001 (sessie 53) — Willem: dubbele begroeting was raar.
  // Spark opende chat met "Hallo Willem, klaar om iets te leren?" → user antwoordt
  // "hallo Spark" → Spark antwoordt weer "hallo". Onnatuurlijk.
  // Nu: chat begint LEEG. Paarse Spark-messages tonen vanzelf dat Spark er is
  // zodra jij begint. Gevoel = normale chat-app. Backend /api/chat/welcome
  // blijft bestaan voor eventuele bewuste opt-in later.
  //
  // Voorheen: useEffect die /api/chat/welcome aanriep en setSparkMessages([msg]).
  // Verwijderd op verzoek Willem (sessie 53).

  const messagesEndRef = useRef(null);

  // Urgent glow voor sub-tabs (v4_glow_001)
  const [subTabGlow, setSubTabGlow] = useState({});
  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    const fetchUrgent = () => {
      fetch(`${API}/api/urgent/notifications?user_id=${userId}`)
        .then(r => r.json())
        .then(d => {
          if (cancelled) return;
          const g = d?.glow || {};
          setSubTabGlow({
            spark: g['chat-spark'] || null,
            community: g['chat-community'] || null,
            prive: g['chat-prive'] || null,
          });
        })
        .catch(() => {});
    };
    fetchUrgent();
    const interval = setInterval(fetchUrgent, 60_000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [userId]);

  // v4_agenda_ack_001: Bij Spark-tab open ack alle urgente agenda items → glow uit
  useEffect(() => {
    if (!userId || activeTab !== 'spark') return;
    if (!subTabGlow.spark) return; // niets te ack'en
    fetch(`${API}/api/urgent/acknowledge?user_id=${userId}&all_agenda=true`, { method: 'POST' })
      .then(() => {
        setSubTabGlow(g => ({ ...g, spark: null }));
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, userId, subTabGlow.spark]);

  // v11_community_grad5_001 — Community-chat zichtbaar vanaf gradatie 5 (Community Member).
  // Grad 6 (Bekend) en 7 (Leert graag kennen) zien alleen Spark + Privé.
  // v12_chat_visibility_toggles_001 — user-prefs kunnen community/privé extra verbergen
  // (Profiel → Instellingen → Chat zichtbaarheid). Community default off, privé default on.
  const [chatPrefs, setChatPrefs] = useState({ community_chat_enabled: false, private_chats_enabled: true });
  useEffect(() => {
    if (!userId) return;
    fetch(`${API}/api/profile/ui-preferences/${userId}`)
      .then(r => r.json())
      .then(d => { if (d?.preferences) setChatPrefs({
        community_chat_enabled: d.preferences.community_chat_enabled === true,
        private_chats_enabled: d.preferences.private_chats_enabled !== false,
      }); })
      .catch(() => {});
  }, [userId]);

  const communityAllowed = userGradatie <= 5 && chatPrefs.community_chat_enabled;
  const priveAllowed = chatPrefs.private_chats_enabled;

  const tabs = [
    { id: 'spark', label: 'Spark AI', icon: Bot, accent: '#f59e0b' },
    ...(communityAllowed ? [{ id: 'community', label: 'Community', icon: Users, accent: '#a855f7' }] : []),
    ...(priveAllowed ? [{ id: 'prive', label: 'Privé', icon: Lock, accent: '#06b6d4' }] : []),
  ];

  // Als user op verborgen tab staat, terug naar spark
  useEffect(() => {
    if (activeTab === 'community' && !communityAllowed) setActiveTab('spark');
    if (activeTab === 'prive' && !priveAllowed) setActiveTab('spark');
  }, [activeTab, communityAllowed, priveAllowed]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [sparkMessages, communityMessages, priveMessages, activeTab]);

  // Load community bot data when tab becomes active
  useEffect(() => {
    if (activeTab !== 'community') return;
    setCommunityLoading(true);
    Promise.all([
      fetch(`${API}/api/bots/community/messages?limit=200`).then(r => r.json()).catch(() => ({ messages: [] })),
      fetch(`${API}/api/bots/list`).then(r => r.json()).catch(() => ({ bots: [] })),
    ]).then(([m, b]) => {
      // v4_community_session_start_001: filter berichten vanaf inlogmoment
      const all = (m.messages || []).reverse();
      const sinceLogin = all.filter(msg => !msg.timestamp || msg.timestamp >= communitySessionStart);
      setCommunityMessages(sinceLogin);
      setBots(b.bots || []);
      setCommunityLoading(false);
    });
  }, [activeTab, communitySessionStart]);

  // v4_actions_001 — STT opname helpers (v4_voice_002: + silence detection + auto-send)
  const cleanupSilenceDetection = () => {
    if (silenceRafRef.current) { cancelAnimationFrame(silenceRafRef.current); silenceRafRef.current = null; }
    try { audioCtxRef.current?.close(); } catch {}
    audioCtxRef.current = null;
    analyserRef.current = null;
    silenceStartRef.current = null;
  };

  const startSttRecording = async (opts = {}) => {
    const { autoSendOnSilence = true } = opts;
    autoSendPendingRef.current = autoSendOnSilence;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      sttStreamRef.current = stream;
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mr.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        try { stream.getTracks().forEach(t => t.stop()); } catch {}
        sttStreamRef.current = null;
        cleanupSilenceDetection();
        // Skip empty/tiny recordings (under ~3kb = no speech)
        if (blob.size < 3000) { setSttListening(false); return; }
        const fd = new FormData();
        fd.append('audio', blob, 'recording.webm');
        try {
          const r = await fetch(`${API}/api/voice/stt`, { method: 'POST', body: fd });
          const data = await r.json();
          if (data.text) {
            const text = data.text.trim();
            if (autoSendPendingRef.current) {
              // Auto-send: zet text en stuur direct (zonder Enter)
              setNewMessage('');
              setTimeout(() => {
                setNewMessage(text);
                setTimeout(() => {
                  // Trigger send via ref-pattern: we roepen handleSend met text inline
                  autoSendVoiceMessage(text);
                }, 50);
              }, 0);
            } else {
              setNewMessage(prev => (prev ? prev + ' ' : '') + text);
            }
          }
        } catch (e) { console.error('STT failed', e); }
        setSttListening(false);
      };
      mediaRecorderRef.current = mr;
      mr.start();
      setSttListening(true);

      // === Silence detection via WebAudio AnalyserNode ===
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        const ctx = new AudioCtx();
        const src = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 1024;
        src.connect(analyser);
        audioCtxRef.current = ctx;
        analyserRef.current = analyser;
        const data = new Uint8Array(analyser.fftSize);
        const SILENCE_THRESHOLD = 0.015; // RMS van genormaliseerde [-1,1]
        const minSpeechMs = 400; // user moet eerst >0.4s spreken
        let firstSpeechTs = null;
        const tick = () => {
          if (!analyserRef.current) return;
          analyser.getByteTimeDomainData(data);
          let sum = 0;
          for (let i = 0; i < data.length; i++) {
            const v = (data[i] - 128) / 128;
            sum += v * v;
          }
          const rms = Math.sqrt(sum / data.length);
          const now = performance.now();
          if (rms > SILENCE_THRESHOLD) {
            if (!firstSpeechTs) firstSpeechTs = now;
            silenceStartRef.current = null;
          } else if (firstSpeechTs && (now - firstSpeechTs) > minSpeechMs) {
            if (!silenceStartRef.current) silenceStartRef.current = now;
            const silenceMs = now - silenceStartRef.current;
            if (silenceMs >= voiceCfg.stt_silence_sec * 1000) {
              // Stilte voldoende lang → stop recording
              try { mediaRecorderRef.current?.stop(); } catch {}
              return; // stop polling
            }
          }
          silenceRafRef.current = requestAnimationFrame(tick);
        };
        silenceRafRef.current = requestAnimationFrame(tick);
      } catch (e) {
        console.warn('Silence detection unavailable:', e);
      }
    } catch (e) {
      alert('Microfoon niet beschikbaar: ' + e.message);
      setSttListening(false);
    }
  };
  const stopSttRecording = async () => {
    // Manueel stoppen → géén auto-send (gebruiker drukte zelf op stop)
    autoSendPendingRef.current = false;
    try { mediaRecorderRef.current?.stop(); } catch {}
    setSttListening(false);
  };
  const toggleSttRecord = () => {
    if (sttListening) stopSttRecording();
    else startSttRecording({ autoSendOnSilence: false }); // handmatige klik → géén auto-send
  };

  // v4_tts_001 — speak Spark response via /api/voice/tts + duck ambient + TTS-glow state
  const speakSparkResponse = async (text) => {
    if (!text) return;
    // Strip markdown for cleaner TTS
    const clean = text
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/_([^_]+)_/g, '$1')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/^[•\-*]\s*/gm, '')
      .replace(/\n+/g, '. ');
    try {
      // Duck ambient (lower volume while Spark spreekt)
      const player = getAmbientPlayer();
      const wasPlaying = player?.isPlaying();
      const origVol = player?.audio?.volume || 0.4;
      if (wasPlaying && player?.audio) player.audio.volume = 0.08;

      const r = await fetch(`${API}/api/voice/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: clean.slice(0, 1000),
          voice: voiceCfg.tts_voice || 'nova',
          speed: voiceCfg.tts_speed || 1.0,
          return_format: 'base64',
        }),
      });
      const data = await r.json();
      if (!data.audio_base64) {
        if (wasPlaying && player?.audio) player.audio.volume = origVol;
        return;
      }
      // Stop previous if any
      if (sparkAudioRef.current) { try { sparkAudioRef.current.pause(); } catch {} }
      const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
      audio.volume = 1.0;
      sparkAudioRef.current = audio;
      setTtsSpeaking(true);
      audio.onended = () => {
        setTtsSpeaking(false);
        if (wasPlaying && player?.audio) player.audio.volume = origVol;
        rearmMicIfVoiceLoop();
      };
      audio.onpause = () => setTtsSpeaking(false);
      audio.play().catch(() => {
        setTtsSpeaking(false);
        if (wasPlaying && player?.audio) player.audio.volume = origVol;
      });
    } catch (e) {
      setTtsSpeaking(false);
      console.error('TTS failed', e);
    }
  };

  // v4_voice_002 — Auto-send wrapper voor voice-input (kan zonder React-state-timing)
  const autoSendVoiceMessage = (text) => {
    if (!text || !text.trim()) return;
    voiceLoopRef.current = true; // mark this conversation as voice-loop → re-arm mic na antwoord
    setNewMessage(text);
    setTimeout(() => handleSend(text), 150);
  };

  // Re-arm mic na Spark's antwoord (en eventueel TTS) als we in voice-loop zitten
  const rearmMicIfVoiceLoop = () => {
    if (!voiceLoopRef.current || !sttEnabled) return;
    setTimeout(() => {
      if (sttEnabled && !sttListening && voiceLoopRef.current) {
        startSttRecording({ autoSendOnSilence: true });
      }
    }, 400);
  };

  // v6_rps_001b — RPS opponent state, set by chat trigger
  const [rpsOpponent, setRpsOpponent] = useState('spark');
  // v6_diep_always_on_001 — Diep is ALTIJD aan (Groq is gratis, Ollama komt later)
  // Toggle weggehaald — gebruikers (incl. mama) verwarrende UX bespaard.
  const deepMode = true;
  const setDeepMode = () => { /* no-op: Diep is always on */ };

  const handleSend = async (overrideText) => {
    const raw = (typeof overrideText === 'string' ? overrideText : newMessage).trim();
    if (!raw) return;
    const text = raw;
    setNewMessage('');

    // v6_rps_001b — Client-side RPS-trigger in community tab (Spark tab gaat via backend)
    if (activeTab === 'community') {
      const txt = text.toLowerCase().trim();
      const rpsTriggers = [
        'speel steen papier schaar', 'steen papier schaar',
        'speel sps', 'spelletje sps', 'speel een spelletje',
        'speel steen', 'speel papier', 'speel schaar',
      ];
      if (rpsTriggers.some(t => txt === t || txt.includes(t))) {
        setRpsOpponent('bot');
        setRpsOpen(true);
        return;
      }
    }

    if (activeTab === 'spark') {
      const userMsg = {
        id: Date.now(), role: 'user', message: text,
        time: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })
      };
      setSparkMessages(prev => [...prev, userMsg]);
      // v6_response_composer_001 — Diep-gesprek modus: directe LLM-bridge via /api/spark/compose
      if (deepMode && activeTab === 'spark') {
        try {
          // v6_tab_context_001 — stuur laatst-bekeken tab mee zodat Spark context heeft
          let lastTab = null;
          try { lastTab = sessionStorage.getItem('spark_last_non_chat_tab') || sessionStorage.getItem('spark_active_tab'); } catch {}
          const r = await fetch(`${API}/api/spark/compose`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, user_id: userId, session_id: `deep-${userId}`, active_tab: lastTab || undefined }),
          });
          const d = await r.json();

          // v6_deep_side_effects_001 — Diep gebruikt nu DEZELFDE audio-pipeline als normale chat
          // (TTS-toggle / STT-toggle / ambient / KB-card geluid)
          if (d.action === 'enable_tts') {
            setTtsEnabled(true);
          } else if (d.action === 'disable_tts') {
            setTtsEnabled(false);
            if (sparkAudioRef.current) { try { sparkAudioRef.current.pause(); } catch {} sparkAudioRef.current = null; }
            setTtsSpeaking(false);
          } else if (d.action === 'enable_stt') {
            setSttEnabled(true);
            if (!sttListening) {
              setTimeout(() => startSttRecording({ autoSendOnSilence: true }), 250);
            }
          } else if (d.action === 'disable_stt') {
            setSttEnabled(false);
            voiceLoopRef.current = false;
            if (sttListening) await stopSttRecording();
          } else if (d.action === 'play_ambient' && d.url) {
            const fullUrl = d.url.startsWith('http') ? d.url : `${API}${d.url}`;
            getAmbientPlayer()?.play(fullUrl, d.ambient_label);
          } else if (d.action === 'stop_ambient') {
            getAmbientPlayer()?.stop();
          } else if (d.action === 'open_help_bark') {
            // v6_deep_help_001 — open HelpBark via global window event (MainLayout luistert)
            window.dispatchEvent(new CustomEvent('spark:open-help'));
          } else if (d.action === 'open_game_rps') {
            // v6_deep_rps_001 — open Steen-Papier-Schaar bark
            setRpsOpponent(d.rps_opponent || 'spark');
            setRpsOpen(true);
          }

          // KB-card geluid eerst (onweer → "ik ben boos"), daarna TTS van Spark's tekst
          if (d.sound_url) {
            await new Promise(resolve => {
              try {
                const fullUrl = d.sound_url.startsWith('http') ? d.sound_url : `${API}${d.sound_url}`;
                const a = new Audio(fullUrl);
                a.volume = 0.7;
                let done = false;
                const finish = () => { if (!done) { done = true; resolve(); } };
                a.addEventListener('ended', finish);
                a.addEventListener('error', finish);
                setTimeout(finish, 4000);
                a.play().catch(finish);
              } catch { resolve(); }
            });
          }

          // TTS van Diep-response (was missing — dat is bug 1)
          if (ttsEnabled && d.success && d.message && d.action !== 'enable_tts') {
            await speakSparkResponse(d.message);
          } else {
            rearmMicIfVoiceLoop();
          }

          const msg = {
            id: Date.now() + 1, role: 'spark',
            message: d.success ? (d.message || '...') : `Even iets mis: ${d.error || 'onbekende fout'}`,
            time: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }),
            deep: true,
            used_cards: d.used_cards || [],
            used_model: d.used_model,
          };
          setSparkMessages(prev => [...prev, msg]);

          // v8_trader_intent_glow_001 — Als Spark een trader-intent detecteerde en user
          // is NIET op de Trader-tab, laat de Trader-nav-tab gloeien zodat user weet waar
          // hij het live kan bekijken. Werkt alleen in deep/spark-chat context.
          try {
            const isTraderIntent = typeof d.intent === 'string' && d.intent.startsWith('trader_');
            const currentTab = sessionStorage.getItem('spark_active_tab') || '';
            if (isTraderIntent && currentTab !== 'trade') {
              window.dispatchEvent(new CustomEvent('spark:nav-glow', {
                detail: { targetId: 'nav-trade', matchedTab: 'trade' },
              }));
            }
          } catch {}
        } catch (e) {
          setSparkMessages(prev => [...prev, {
            id: Date.now() + 1, role: 'spark',
            message: `Diep-gesprek verbinding faalde: ${e.message}`,
            time: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }),
            deep: true,
          }]);
        }
        return;
      }
      try {
        const res = await fetch(`${API}/api/chat/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, user_naam: userName, user_id: userId, channel: 'spark', admin_mode: !!adminModeActive }),
        });
        const data = await res.json();

        // v4_actions_001 — Frontend voert action uit op basis van backend response
        if (data.action === 'enable_stt') {
          setSttEnabled(true);
          // v4_voice_002 — Mic direct auto-starten (geen 2e klik), met auto-send op stilte
          if (!sttListening) {
            setTimeout(() => startSttRecording({ autoSendOnSilence: true }), 250);
          }
        } else if (data.action === 'disable_stt') {
          setSttEnabled(false);
          voiceLoopRef.current = false;
          if (sttListening) await stopSttRecording();
        } else if (data.action === 'enable_tts') {
          setTtsEnabled(true);
        } else if (data.action === 'disable_tts') {
          setTtsEnabled(false);
          if (sparkAudioRef.current) { try { sparkAudioRef.current.pause(); } catch {} sparkAudioRef.current = null; }
          setTtsSpeaking(false);
        } else if (data.action === 'play_ambient' && data.url) {
          const fullUrl = data.url.startsWith('http') ? data.url : `${API}${data.url}`;
          getAmbientPlayer()?.play(fullUrl, data.label);
        } else if (data.action === 'stop_ambient') {
          getAmbientPlayer()?.stop();
        } else if (data.action === 'force_logout') {
          // v4_self_delete_001: account verwijderd → uitloggen + redirect met alert
          setTimeout(() => {
            try { localStorage.clear(); sessionStorage.clear(); } catch {}
            window.location.href = '/?deleted=1';
          }, 1500);
        } else if (data.action === 'open_game_rps') {
          // v6_rps_001 — open Steen-Papier-Schaar bark met juiste opponent
          setRpsOpponent(data.rps_opponent || 'spark');
          setRpsOpen(true);
        } else if (data.action === 'open_help_bark') {
          // v6_help_001b — open de Help-Bark via global window event (MainLayout luistert)
          window.dispatchEvent(new CustomEvent('spark:open-help'));
        }

        // v12_contact_call_001 — "bel mijn moeder" → WhatsApp popup
        if (data.type === 'contact_call' && data.action) {
          setContactCallAction(data.action);
        }

        // v6_kb_sound_001b — KB-kaart geluid EERST afspelen, daarna TTS (onweer → "ik ben boos")
        // Wacht tot geluid klaar is (max 4s) voordat TTS begint.
        const playKbSound = () => {
          if (!data.sound_url) return Promise.resolve();
          return new Promise(resolve => {
            try {
              const fullUrl = data.sound_url.startsWith('http') ? data.sound_url : `${API}${data.sound_url}`;
              const a = new Audio(fullUrl);
              a.volume = 0.7;
              let done = false;
              const finish = () => { if (!done) { done = true; resolve(); } };
              a.addEventListener('ended', finish);
              a.addEventListener('error', finish);
              // Hard timeout zodat lange/foute clips TTS niet ophouden
              setTimeout(finish, 4000);
              a.play().catch(finish);
            } catch { resolve(); }
          });
        };

        // Geluid eerst, daarna pas TTS
        await playKbSound();

        // TTS speak Spark's response — strip markdown for cleaner audio
        if (ttsEnabled && data.message && data.action !== 'enable_tts') {
          await speakSparkResponse(data.message);
        } else {
          // Geen TTS → meteen re-arm mic indien voice-loop
          rearmMicIfVoiceLoop();
        }

        setSparkMessages(prev => [...prev, {
          id: Date.now() + 1, role: 'spark',
          message: data.message || 'Hmm, daar moet ik even over nadenken.',
          time: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }),
          type: data.type,
          knowledge_matches: data.knowledge_matches || [],
          unknown_words: data.unknown_words || [],
          snap_suggestions: data.snap_suggestions || [],
          sentiment: data.sentiment,
          navigate_to: data.navigate_to,
          glow_target: data.glow_target,
          matched_tab: data.matched_tab,
        }]);

        // v6_glow_nav_001 — Frontend dispatch: laat nav-tab gloeien + optioneel navigeren
        if (data.type === 'navigate_tab' && data.glow_target) {
          try {
            window.dispatchEvent(new CustomEvent('spark:nav-glow', {
              detail: {
                targetId: data.glow_target,         // bv. "nav-wallet"
                navigateTo: data.navigate_to,        // bv. "/modules/wallet"
                matchedTab: data.matched_tab,
              },
            }));
          } catch {}
        }
      } catch (e) {
        setSparkMessages(prev => [...prev, {
          id: Date.now() + 1, role: 'spark',
          message: 'Er ging iets mis met de verbinding. Probeer het opnieuw.',
          time: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }),
        }]);
      }
    } else if (activeTab === 'community') {
      if (sendingCommunity) return;
      setSendingCommunity(true);
      const res = await fetch(`${API}/api/bots/community/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, user_id: userId, user_name: userName }),
      }).then(r => r.json()).catch(() => ({ success: false }));
      if (res.success) {
        // v5_gesprekken_compat_001 — ondersteunt nieuwe (messages) en oude (message+bot_responses) response
        if (Array.isArray(res.messages) && res.messages.length > 0) {
          // help / safeword / dnd_intro: server geeft alleen bot-antwoord(en) terug,
          // user-message wordt server-side opgeslagen → voeg lokaal toe voor directe feedback
          const userEcho = {
            id: `tmp-${Date.now()}`,
            user_id: userId,
            user_name: userName,
            message: text,
            is_bot: false,
            timestamp: new Date().toISOString(),
          };
          setCommunityMessages(prev => [...prev, userEcho, ...res.messages.filter(Boolean)]);
        } else if (res.message) {
          setCommunityMessages(prev => [...prev, res.message, ...(res.bot_responses || []).filter(Boolean)]);
        }
      }
      setSendingCommunity(false);
    } else if (activeTab === 'prive') {
      if (!selectedContact?.id || sendingPrive) return;
      setSendingPrive(true);
      const optimistic = {
        id: `tmp-${Date.now()}`,
        from_user_id: userId,
        from_naam: userName,
        to_user_id: selectedContact.id,
        text,
        ts: new Date().toISOString(),
      };
      setPriveMessages(prev => [...prev, optimistic]);
      try {
        await fetch(`${API}/api/contacts/send`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ from_user_id: userId, to_user_id: selectedContact.id, text }),
        });
        // Re-fetch om bot-reply en echte ids op te halen
        await loadPriveMessages(selectedContact.id);
        loadPriveContacts();
      } catch { /* graceful */ }
      setSendingPrive(false);
    }
  };

  return (
    <MainLayout activePage="chat" onNavigate={onNavigate}>
      <div data-testid="gesprekken-page" className="h-full flex flex-col">

        {/* === TOP BANNER WITH TABS === */}
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
              <MessageSquare className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Gesprekken</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Workspace</p>
            </div>
          </div>
          <div className="flex">
            {tabs.map(tab => {
              const isActive = activeTab === tab.id;
              const tabGlow = subTabGlow[tab.id];
              const glowRing = tabGlow === 'red'
                ? 'ring-2 ring-red-500/60 rounded-lg animate-pulse'
                : tabGlow === 'amber' ? 'ring-2 ring-amber-400/40 rounded-lg' : '';
              return (
                <button
                  key={tab.id}
                  data-testid={`tab-${tab.id}`}
                  data-glow={tabGlow || undefined}
                  onClick={() => { setActiveTab(tab.id); setSelectedContact(null); }}
                  className={`relative flex items-center gap-2 px-5 py-2.5 text-sm font-medium transition-colors ${glowRing}`}
                  style={{ color: isActive ? tab.accent : (tabGlow === 'red' ? '#fca5a5' : tabGlow === 'amber' ? '#fcd34d' : '#94a3b8') }}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                  {isActive && (
                    <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full" style={{ background: tab.accent }} />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* === CONTENT AREA === */}
        <div className="flex-1 flex overflow-hidden min-h-0">

          {/* --- SPARK AI TAB --- */}
          {activeTab === 'spark' && (
            <div className="flex-1 flex flex-col">
              {/* v4_voice_002 — TTS-glow indicator (Spark spreekt) */}
              {ttsSpeaking && (
                <div data-testid="tts-glow-bar" className="flex items-center gap-2 px-4 py-2 bg-amber-500/10 border-b border-amber-500/30">
                  <div className="relative flex items-center justify-center">
                    <span className="absolute w-5 h-5 rounded-full bg-amber-400/40 animate-ping" />
                    <Volume2 className="w-4 h-4 text-amber-400 relative" />
                  </div>
                  <span className="text-xs text-amber-200 flex-1">Spark spreekt...</span>
                  <button
                    data-testid="tts-stop-btn"
                    onClick={() => {
                      if (sparkAudioRef.current) { try { sparkAudioRef.current.pause(); } catch {} }
                      setTtsSpeaking(false);
                    }}
                    className="text-[10px] px-2 py-0.5 rounded border border-amber-400/40 text-amber-200 hover:bg-amber-500/15 flex items-center gap-1"
                  >
                    <VolumeX className="w-3 h-3" /> Stop
                  </button>
                </div>
              )}
              {/* Ambient status bar — zichtbaar wanneer ambient speelt OF wacht op user-gesture (na F5) */}
              {ambientPlaying && (
                <div data-testid="ambient-bar" className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border-b border-emerald-500/20">
                  <Volume2 className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                  <span className="text-xs text-emerald-300 flex-1">🎵 {ambientLabel || 'Achtergrondgeluid speelt af'}</span>
                  <button
                    data-testid="ambient-stop"
                    onClick={() => getAmbientPlayer()?.stop()}
                    className="text-[10px] px-2 py-0.5 rounded border border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/10 flex items-center gap-1"
                  >
                    <VolumeX className="w-3 h-3" /> Stop
                  </button>
                </div>
              )}
              {!ambientPlaying && ambientPendingResume && (
                <div data-testid="ambient-resume-bar" className="flex items-center gap-2 px-4 py-2 bg-amber-500/10 border-b border-amber-500/20">
                  <Volume2 className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-xs text-amber-300 flex-1">🎵 {ambientLabel || 'Ambient'} — klik om door te spelen</span>
                  <button
                    data-testid="ambient-resume"
                    onClick={() => getAmbientPlayer()?.resume()}
                    className="text-[10px] px-2 py-0.5 rounded border border-amber-400/40 text-amber-200 hover:bg-amber-500/15 flex items-center gap-1"
                  >
                    <Volume2 className="w-3 h-3" /> Hervatten
                  </button>
                  <button
                    data-testid="ambient-pending-stop"
                    onClick={() => getAmbientPlayer()?.stop()}
                    className="text-[10px] px-2 py-0.5 rounded border border-amber-400/40 text-amber-200 hover:bg-amber-500/15 flex items-center gap-1"
                  >
                    <VolumeX className="w-3 h-3" /> Stoppen
                  </button>
                </div>
              )}
              <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
                {sparkMessages.filter(Boolean).map(msg => (
                  <SparkBubble key={msg.id} msg={msg} sparkAvatarUrl={sparkAvatarUrl} />
                ))}
                <div ref={messagesEndRef} />
              </div>
              <ChatInput
                value={newMessage}
                onChange={setNewMessage}
                onSend={handleSend}
                placeholder="Vraag Spark iets..."
                accent="#f59e0b"
                sttEnabled={sttEnabled}
                sttListening={sttListening}
                onSttToggle={toggleSttRecord}
                deepMode={deepMode}
                onDeepToggle={isAdmin ? () => setDeepMode(v => !v) : null}
                showDeepToggle={isAdmin}
              />
            </div>
          )}

          {/* --- COMMUNITY TAB (BOTS) --- */}
          {activeTab === 'community' && (
            <>
              {/* Bots sidebar */}
              <div className="w-52 md:w-60 bg-slate-900/40 border-r border-slate-800 flex flex-col flex-shrink-0">
                <div className="p-3">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-2 px-2">Bots online</p>
                  {bots.length === 0 && (
                    <p className="text-[11px] text-slate-600 px-2">Geen bots geladen</p>
                  )}
                  {bots.map(bot => {
                    const style = BOT_COLORS[bot.id] || { bg: 'bg-slate-800', text: 'text-slate-400', border: 'border-slate-700', icon: Bot };
                    const BotIcon = style.icon;
                    return (
                      <div
                        key={bot.id}
                        data-testid={`bot-${bot.id}`}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm mb-1 ${style.bg} border ${style.border}`}
                      >
                        <BotIcon className={`w-3.5 h-3.5 flex-shrink-0 ${style.text}`} />
                        <span className={`truncate text-xs ${style.text}`}>{bot.naam.split(' ')[0]}</span>
                        <span className="ml-auto w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                      </div>
                    );
                  })}
                </div>
              </div>
              {/* Community messages */}
              <div className="flex-1 flex flex-col">
                {/* v6_dnd_bark_001 — Spark World launcher */}
                <div className="px-4 pt-3 pb-2 border-b border-slate-800/40 flex items-center justify-between gap-2">
                  <p className="text-[11px] text-slate-500">
                    Community chat · <span className="text-slate-400">{bots.length}</span> bots online
                  </p>
                  <button data-testid="open-spark-world" onClick={() => setShowSparkWorld(true)}
                    className="px-3 py-1.5 rounded-lg text-[11px] font-medium border border-amber-500/40 text-amber-300 hover:bg-amber-500/10 flex items-center gap-1.5 transition-colors">
                    <Sparkles className="w-3 h-3" /> Spark World
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-3">
                  {/* v4_community_session_start_001 — info-banner */}
                  <div data-testid="community-session-banner" className="text-center text-[10px] text-slate-500 italic pb-2 border-b border-slate-800/40">
                    🔁 Schoon overzicht sinds je inlog ({new Date(communitySessionStart).toLocaleTimeString('nl-NL', {hour: '2-digit', minute: '2-digit'})}). Vraag Spark "wat is gisteren besproken?" voor archief.
                  </div>
                  {communityLoading ? (
                    <p className="text-center text-slate-500 text-xs">Berichten laden...</p>
                  ) : communityMessages.length === 0 ? (
                    <p className="text-center text-slate-500 text-xs">Geen nieuwe berichten in deze sessie. Typ iets!</p>
                  ) : (
                    communityMessages.filter(Boolean).map(msg => (
                      <CommunityBubble key={msg.id} msg={msg} isOwn={msg.user_id === userId} />
                    ))
                  )}
                  <div ref={messagesEndRef} />
                </div>
                <ChatInput
                  value={newMessage}
                  onChange={setNewMessage}
                  onSend={handleSend}
                  placeholder="Typ een bericht aan de bots..."
                  accent="#a855f7"
                  disabled={sendingCommunity}
                  sttEnabled={sttEnabled}
                  sttListening={sttListening}
                  onSttToggle={toggleSttRecord}
                />
              </div>
            </>
          )}

          {/* --- PRIVÉ TAB --- */}
          {activeTab === 'prive' && (
            <>
              <div className="w-52 md:w-64 bg-slate-900/40 border-r border-slate-800 flex flex-col flex-shrink-0 min-h-0">
                <div className="p-3 flex flex-col min-h-0 flex-1">
                  <div className="relative mb-3 flex-shrink-0">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                    <input
                      type="text"
                      value={priveSearch}
                      onChange={e => setPriveSearch(e.target.value)}
                      placeholder="Zoek contact..."
                      data-testid="prive-search"
                      className="w-full pl-8 pr-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:border-cyan-500/50 focus:outline-none"
                    />
                  </div>
                  {priveLoading && priveContacts.length === 0 ? (
                    <p className="text-xs text-slate-500 text-center py-4">Contacten laden...</p>
                  ) : priveContacts.length === 0 ? (
                    <p className="text-xs text-slate-500 text-center py-4">Geen contacten beschikbaar</p>
                  ) : (
                    <div className="space-y-1 overflow-y-auto flex-1 pr-1" data-testid="prive-contact-list">
                      {priveContacts
                        .filter(c => !priveSearch || c.naam.toLowerCase().includes(priveSearch.toLowerCase()))
                        .map(c => (
                        <button
                          key={c.id}
                          data-testid={`contact-${c.naam.toLowerCase().replace(/\s+/g,'-')}`}
                          onClick={() => setSelectedContact(c)}
                          className={`w-full flex items-center gap-3 p-2.5 rounded-lg transition-colors ${
                            selectedContact?.id === c.id
                              ? 'bg-cyan-500/10 border border-cyan-500/20'
                              : 'hover:bg-slate-800/50'
                          }`}
                        >
                          <div className="relative flex-shrink-0">
                            <UserAvatar user={{id: c.id, naam: c.naam, avatar: c.avatar_ref, gradatie: c.gradatie}} size="md" rounded="rounded-lg" />
                            {c.online && (
                              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 border-2 border-slate-900 rounded-full" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0 text-left">
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-white font-medium truncate flex items-center gap-1">
                                {c.naam}
                                {c.is_bot && <span className="text-[9px] px-1 py-0.5 rounded bg-emerald-500/15 text-emerald-300">BOT</span>}
                                {c.is_admin_contact && <span className="text-[9px] px-1 py-0.5 rounded bg-amber-500/15 text-amber-300">TEAM</span>}
                                {c.is_collective && <span data-testid="badge-admin-collectief" className="text-[9px] px-1 py-0.5 rounded bg-amber-500/15 text-amber-300">COLLECTIEF</span>}
                              </span>
                              <span className="text-[10px] text-slate-500 ml-2 flex-shrink-0">{c.last_time}</span>
                            </div>
                            <p className="text-xs text-slate-400 truncate">{c.last_message || c.rol}</p>
                          </div>
                          {c.unread > 0 && (
                            <span className="w-4 h-4 rounded-full text-[10px] text-white flex items-center justify-center flex-shrink-0" style={{ background: '#06b6d4' }}>
                              {c.unread}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex-1 flex flex-col min-h-0">
                {!selectedContact ? (
                  <div className="flex-1 flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto mb-4">
                        <Lock className="w-7 h-7 text-slate-600" />
                      </div>
                      <p className="text-slate-400 text-sm">Selecteer een gesprek</p>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="h-14 px-5 flex items-center justify-between border-b border-slate-800 bg-slate-900/30 flex-shrink-0">
                      <div className="flex items-center gap-3">
                        <UserAvatar user={{id: selectedContact.id, naam: selectedContact.naam, avatar: selectedContact.avatar_ref, gradatie: selectedContact.gradatie}} size="sm" rounded="rounded-lg" />
                        <div>
                          <h3 className="text-sm font-semibold text-white flex items-center gap-1.5">
                            {selectedContact.naam}
                            {selectedContact.is_bot && <span className="text-[9px] px-1 py-0.5 rounded bg-emerald-500/15 text-emerald-300">BOT</span>}
                            {selectedContact.is_admin_contact && <span className="text-[9px] px-1 py-0.5 rounded bg-amber-500/15 text-amber-300">TEAM</span>}
                            {selectedContact.is_collective && <span className="text-[9px] px-1 py-0.5 rounded bg-amber-500/15 text-amber-300">COLLECTIEF</span>}
                          </h3>
                          <p className={`text-[10px] flex items-center gap-1 ${selectedContact.online ? 'text-green-400' : 'text-slate-500'}`}>
                            <Circle className="w-1.5 h-1.5 fill-current" />
                            {selectedContact.online ? 'Online' : 'Offline'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {!(selectedContact.is_bot || selectedContact.is_collective) && (() => {
                          const isRingingFromThis = incomingCall && incomingCall.from_user_id === selectedContact.id;
                          const pulseAnim = isRingingFromThis ? { animation: 'callIconPulse 1s ease-in-out infinite' } : {};
                          return (
                            <>
                              <button
                                data-testid="call-btn"
                                onClick={() => openPriveCall('audio')}
                                title={`Bel ${selectedContact.naam}`}
                                className="p-2 rounded-lg transition-all border border-transparent hover:border-[color:var(--glow-base,#f59e0b)]/40"
                                style={{
                                  color: 'var(--glow-base, #f59e0b)',
                                  backgroundColor: 'color-mix(in srgb, var(--glow-base, #f59e0b) 8%, transparent)',
                                  boxShadow: '0 0 12px color-mix(in srgb, var(--glow-base, #f59e0b) 30%, transparent)',
                                  ...pulseAnim,
                                }}
                              >
                                <Phone className="w-4 h-4" />
                              </button>
                              <button
                                data-testid="video-btn"
                                onClick={() => openPriveCall('video')}
                                title={`Beeldbellen met ${selectedContact.naam}`}
                                className="p-2 rounded-lg transition-all border border-transparent hover:border-[color:var(--glow-base,#f59e0b)]/40"
                                style={{
                                  color: 'var(--glow-base, #f59e0b)',
                                  backgroundColor: 'color-mix(in srgb, var(--glow-base, #f59e0b) 8%, transparent)',
                                  boxShadow: '0 0 12px color-mix(in srgb, var(--glow-base, #f59e0b) 30%, transparent)',
                                  ...pulseAnim,
                                }}
                              >
                                <Video className="w-4 h-4" />
                              </button>
                            </>
                          );
                        })()}
                        <style>{`@keyframes callIconPulse { 0%,100% { transform: scale(1); box-shadow: 0 0 12px color-mix(in srgb, var(--glow-base, #f59e0b) 30%, transparent); } 50% { transform: scale(1.15); box-shadow: 0 0 24px color-mix(in srgb, var(--glow-base, #f59e0b) 80%, transparent); } }`}</style>
                      </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-3">
                      {priveMessages.length === 0 ? (
                        <div className="h-full flex items-center justify-center">
                          <div className="text-center">
                            <div className="mx-auto mb-3 inline-block">
                              <UserAvatar user={{id: selectedContact.id, naam: selectedContact.naam, avatar: selectedContact.avatar_ref, gradatie: selectedContact.gradatie}} size="lg" rounded="rounded-xl" />
                            </div>
                            <h3 className="text-white font-semibold text-sm">{selectedContact.naam}</h3>
                            <p className="text-slate-500 text-xs mt-1">Begin een gesprek</p>
                          </div>
                        </div>
                      ) : (
                        priveMessages.filter(Boolean).map(m => {
                          const fromMe = m.from_user_id === userId;
                          return (
                            <div key={m.id} className={`flex ${fromMe ? 'justify-end' : 'justify-start'}`}>
                              <div className={`max-w-[75%] rounded-2xl px-4 py-2 ${
                                fromMe
                                  ? 'bg-cyan-500/15 border border-cyan-500/25 text-cyan-50'
                                  : 'bg-slate-800/60 border border-slate-700/40 text-slate-100'
                              }`}>
                                {!fromMe && (
                                  <p className="text-[10px] text-slate-400 mb-0.5 font-medium">{m.from_naam}</p>
                                )}
                                <p className="text-sm whitespace-pre-wrap">{m.text}</p>
                                <p className="text-[9px] text-slate-500 mt-1">
                                  {m.ts ? new Date(m.ts).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }) : ''}
                                </p>
                              </div>
                            </div>
                          );
                        })
                      )}
                      <div ref={messagesEndRef} />
                    </div>
                    <ChatInput
                      value={newMessage}
                      onChange={setNewMessage}
                      onSend={handleSend}
                      placeholder={`Bericht aan ${selectedContact.naam}...`}
                      accent="#06b6d4"
                      disabled={sendingPrive}
                      sttEnabled={sttEnabled}
                      sttListening={sttListening}
                      onSttToggle={toggleSttRecord}
                    />
                  </>
                )}
              </div>
            </>
          )}
        </div>

        {/* v6_dnd_bark_001 — Spark World D&D modal */}
        {showSparkWorld && (
          <div data-testid="spark-world-modal" className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => setShowSparkWorld(false)}>
            <div className="w-full max-w-xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
              <DnDBarkPanel userId={userId} onClose={() => setShowSparkWorld(false)} />
            </div>
          </div>
        )}

        {/* v6_rps_001 — Steen-Papier-Schaar mini-game bark */}
        <RpsBark userId={userId} open={rpsOpen} opponent={rpsOpponent} onClose={() => setRpsOpen(false)} />
        {/* v12_contact_call_001 */}
        <ContactCallPopup action={contactCallAction} onClose={() => setContactCallAction(null)} />
        {/* v13_prive_call_ui_001 — UI-shell privé-bel bark (lokaal, geen cloud) */}
        <PriveCallBark
          open={callBark.open}
          mode={callBark.mode}
          contact={selectedContact}
          onClose={closePriveCall}
        />
        {/* v13_prive_incoming_call_001 — inkomende oproep bark */}
        <IncomingCallBark
          call={incomingCall}
          caller={priveContacts.find((c) => c.id === incomingCall?.from_user_id)}
          onAccept={() => answerIncoming('accept')}
          onDecline={() => answerIncoming('decline')}
        />
      </div>
    </MainLayout>
  );
}

/* === Chat input in framed container === */
function ChatInput({ value, onChange, onSend, placeholder, accent, disabled = false, sttEnabled = false, sttListening = false, onSttToggle = null, deepMode = false, onDeepToggle = null, showDeepToggle = true }) {
  return (
    <div className="p-4 bg-slate-900/20 border-t border-slate-800 flex-shrink-0">
      <div
        className="flex items-center gap-2 max-w-4xl mx-auto bg-slate-800/60 border border-slate-700/60 rounded-2xl px-2 py-1.5 shadow-lg focus-within:border-slate-600 transition-colors"
        style={{ '--accent': accent }}
      >
        <button data-testid="attach-btn" className="p-2 hover:bg-slate-700/50 rounded-xl transition-colors flex-shrink-0">
          <Plus className="w-4 h-4 text-slate-400" />
        </button>
        {sttEnabled && onSttToggle && (
          <button
            data-testid="stt-mic-btn"
            onClick={onSttToggle}
            title={sttListening ? 'Stop opname' : 'Spreek in'}
            className={`p-2 rounded-xl transition-colors flex-shrink-0 ${sttListening ? 'bg-red-500/20 text-red-400 animate-pulse' : 'hover:bg-slate-700/50 text-amber-400'}`}
          >
            {sttListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>
        )}
        {/* v6_diep_always_on_001 — toggle weggehaald, Diep is altijd aan */}
        {/* v13t_user_text_tpm_guard_001 — char-counter zichtbaar zodra > 3500 chars,
             rood > 5500 chars (backend truncate). Verhindert stille TPM-crashes. */}
        {value.length > 3500 && (
          <span
            className={`text-[10px] tabular-nums flex-shrink-0 ${value.length > 5500 ? 'text-red-400 font-semibold' : 'text-amber-400'}`}
            data-testid="chat-input-char-counter"
            title={value.length > 5500 ? 'Tekst wordt automatisch ingekort — knip in stukken voor beste resultaat' : 'Lange tekst — LLM kan traag reageren'}
          >
            {value.length}/5500
          </span>
        )}
        <input
          type="text"
          data-testid="chat-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !disabled && onSend()}
          placeholder={sttListening ? 'Luistert... druk mic om te stoppen' : (placeholder || 'Praat met Spark — vraag of vertel iets...')}
          disabled={disabled}
          className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none px-2 py-2 disabled:opacity-50"
        />
        <button
          data-testid="send-btn"
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="p-2.5 rounded-xl transition-all flex-shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
          style={{ background: accent }}
        >
          <Send className="w-4 h-4 text-white" />
        </button>
      </div>
    </div>
  );
}

/* === Spark AI message bubble === */
function SparkBubble({ msg, sparkAvatarUrl }) {
  const isUser = msg.role === 'user';
  const hasMatches = msg.knowledge_matches && msg.knowledge_matches.length > 0;
  const hasSnaps = msg.snap_suggestions && msg.snap_suggestions.length > 0;

  const handleSnap = async (word) => {
    try {
      await fetch(`${API}/api/chat/snap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ concept: word, context: '', user_naam: 'Willem' }),
      });
    } catch (e) { console.error(e); }
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex items-end gap-2 max-w-[80%] md:max-w-[65%] ${isUser ? 'flex-row-reverse' : ''}`}>
        {!isUser && (
          <div className="w-7 h-7 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0"
            style={!sparkAvatarUrl ? { background: 'linear-gradient(135deg, #f59e0b, #ea580c)' } : undefined}>
            {sparkAvatarUrl ? (
              <img src={sparkAvatarUrl} alt="Spark" className="w-full h-full object-cover" />
            ) : (
              <Sparkles className="w-3.5 h-3.5 text-white" />
            )}
          </div>
        )}
        <div>
          <div className={`px-4 py-2.5 rounded-2xl ${
            isUser
              ? 'bg-amber-500 text-white rounded-br-md'
              : msg.deep ? 'bg-indigo-900/50 text-white rounded-bl-md border border-indigo-500/30' : 'bg-slate-800 text-white rounded-bl-md'
          }`}>
            <p className="text-sm leading-relaxed whitespace-pre-line">{msg.message}</p>
            <div className={`text-[10px] mt-1 flex items-center gap-1.5 ${isUser ? 'text-amber-200' : 'text-slate-500'}`}>
              <span>{msg.time}</span>
              {msg.deep && (
                <>
                  <span>·</span>
                  <span className="text-indigo-300" title={`Diep gesprek via ${msg.used_model || 'LLM-bridge'} — Spark synthesizeerde dit uit ${(msg.used_cards||[]).length} eigen kaarten`}>🌊 diep ({(msg.used_cards||[]).length} kaarten)</span>
                </>
              )}
            </div>
          </div>
          {hasMatches && (
            <div className="flex flex-wrap gap-1 mt-1.5 ml-1">
              {msg.knowledge_matches.map((m, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 bg-amber-500/10 text-amber-400 rounded-full flex items-center gap-1">
                  <BookOpen className="w-2.5 h-2.5" /> {m.begrip}
                </span>
              ))}
            </div>
          )}
          {hasSnaps && (
            <div className="flex flex-wrap gap-1 mt-1.5 ml-1">
              {msg.snap_suggestions.map((w, i) => (
                <button key={i} onClick={() => handleSnap(w)}
                  className="text-[10px] px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded-full flex items-center gap-1 hover:bg-blue-500/20 transition-colors">
                  <Zap className="w-2.5 h-2.5" /> Snap: {w}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* === Community (bot) message bubble === */
function CommunityBubble({ msg, isOwn }) {
  const isBot = msg.is_bot;
  const style = BOT_COLORS[msg.user_id] || {};
  const BotIcon = style.icon || Bot;
  const API = process.env.REACT_APP_BACKEND_URL;
  const avatar = msg.avatar;
  const avatarUrl = avatar?.kind === 'image' && avatar.url ? `${API}${avatar.url}` : null;
  const avatarEmoji = avatar?.kind === 'emoji' ? avatar.emoji : null;
  const isFallback = !!avatar?.is_fallback;

  return (
    <div data-testid={`community-msg-${msg.id}`} className={`flex gap-2.5 ${isOwn ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 ${
        avatarUrl ? '' : isBot ? (style.bg || 'bg-slate-800') : isOwn ? 'bg-amber-500/20' : 'bg-slate-800'
      }`}>
        {avatarUrl ? (
          <img src={avatarUrl} alt={msg.user_name} className={`w-full h-full object-cover ${isFallback ? 'opacity-60 grayscale' : ''}`}
            title={isFallback ? 'Roadkill logo fallback' : msg.user_name} />
        ) : avatarEmoji ? (
          <span className="text-base leading-none">{avatarEmoji}</span>
        ) : isBot ? (
          <BotIcon className={`w-4 h-4 ${style.text || 'text-slate-400'}`} />
        ) : (
          <span className={`text-[11px] font-bold ${isOwn ? 'text-amber-400' : 'text-slate-400'}`}>{(msg.user_name || 'U').charAt(0)}</span>
        )}
      </div>
      <div className={`max-w-[70%] ${isOwn ? 'text-right' : ''}`}>
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`text-[10px] font-medium ${isBot ? (style.text || 'text-slate-400') : isOwn ? 'text-amber-400' : 'text-slate-300'}`}>
            {msg.user_name}
          </span>
          {isBot && <span className="text-[8px] px-1 py-0.5 rounded bg-slate-800 text-slate-500">BOT</span>}
          <span className="text-[9px] text-slate-600">
            {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }) : ''}
          </span>
        </div>
        <div className={`inline-block px-3 py-2 rounded-xl text-sm ${
          isBot ? `${style.bg || 'bg-slate-800/50'} border ${style.border || 'border-slate-700'} ${style.text || 'text-slate-300'}`
            : isOwn ? 'bg-amber-500/15 border border-amber-500/20 text-white'
            : 'bg-slate-800/50 border border-slate-700 text-slate-200'
        }`}>
          {msg.message}
        </div>
      </div>
    </div>
  );
}

export default GesprekkenPage;
