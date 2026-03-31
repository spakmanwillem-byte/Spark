import React, { useState, useEffect, useRef } from "react";
import "@/App.css";
import "./components/layout/Layout.css";
import axios from "axios";
import VoiceControls from "./components/VoiceControls";

// API Configuration
import { BACKEND_URL, API_URL } from "./config/api";

// Layout Components
import StatusTicker from "./components/layout/StatusTicker";
import LeftNavigation from "./components/layout/LeftNavigation";
import MainContentArea from "./components/layout/MainContentArea";
// RightInfoPanel removed - info moved to tabs
import ChatArea from "./components/layout/ChatArea";

// Tab Components
import MijnProfielTabNew from "./components/MijnProfielTabNew";
import AdminTab from "./components/AdminTab";
import AchievementsTab from "./components/AchievementsTabUnified";
import StatusTabNew from "./components/StatusTabNew";
import BestandenTab from "./components/BestandenTab";
import AgendaTab from "./components/AgendaTab";
import DagboekTab from "./components/DagboekTab";
// TaskTab removed - Tasks now managed via Notes (hybrid system)
import RoadmapTab from "./components/RoadmapTab";
import NotitiesTab from "./components/NotitiesTab";
import KnowledgeBaseTab from "./components/KnowledgeBaseTab";
import SettingsTabNew from "./components/SettingsTabNew";
import LogsTab from "./components/LogsTab";
import GeluidenTab from "./components/GeluidenTab";
import TriggerManagerTab from "./components/TriggerManagerTab";
import TriggersTab from "./components/TriggersTab";  // New Triggers Overview
import MonitorTab from "./components/MonitorTab";  // Monitoring Service
import GraphViewerTab from "./components/GraphViewerTab";
import EmotionStatsTab from "./components/EmotionStatsTab";
import LeaderboardTab from "./components/LeaderboardTab";
import CommunityChat from "./components/CommunityChat";
import WalletTab from "./components/WalletTab";
import UserWalletTab from "./components/UserWalletTab";  // User Wallet
import WinkelTab from "./components/WinkelTab";  // ROAR Shop
import GameTab from "./components/GameTab";
import BuildingBlueprintTab from "./components/BuildingBlueprintTab";
import BuildingsOverviewTab from "./components/BuildingsOverviewTab";
import BlueprintEditorTab from "./components/BlueprintEditorTab";  // NIEUW
import UitgavenTab from "./components/UitgavenTab";  // Privé Uitgaven
import InkomstenTab from "./components/InkomstenTab";  // Privé Inkomsten
import DashboardTab from "./components/DashboardTab";  // Dashboard Overzicht
import SparkChatTab from "./components/SparkChatTab";  // Spark Info Banner

// Use auto-configured API URLs
const API = API_URL;

function App() {
  // State Management
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [userData, setUserData] = useState(() => {
    try {
      const saved = localStorage.getItem('spark_user_data');
      console.log('[INIT] Loading userData from localStorage:', saved ? 'found' : 'not found');
      
      // FALLBACK: Als geen userData in localStorage, gebruik user-001 voor testing
      if (!saved) {
        console.log('[INIT] No userData found, using fallback user-001');
        const fallbackUser = {
          id: 'user-001',
          naam: 'Willem',
          gradatie: 1
        };
        localStorage.setItem('spark_user_data', JSON.stringify(fallbackUser));
        return fallbackUser;
      }
      
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      console.error('[INIT] Error loading userData:', e);
      return null;
    }
  });
  
  const [sessionId] = useState(() => {
    let sid = localStorage.getItem('spark_session_id');
    if (!sid) {
      sid = 'anon_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('spark_session_id', sid);
    }
    return sid;
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState('online');
  const [activeTab, setActiveTab] = useState("chat");
  const [chatMode, setChatMode] = useState("spark"); // "spark" | "community"
  const [knowledgeCount, setKnowledgeCount] = useState(0);
  const [sparkEmotion, setSparkEmotion] = useState(null);
  const [masterVolume, setMasterVolume] = useState(70); // Default 70%
  const [moodColorsEnabled, setMoodColorsEnabled] = useState(true); // Default ON
  const messagesEndRef = useRef(null);

  // Persist userData
  useEffect(() => {
    if (userData) {
      localStorage.setItem('spark_user_data', JSON.stringify(userData));
    } else {
      localStorage.removeItem('spark_user_data');
    }
  }, [userData]);

  // Session heartbeat
  useEffect(() => {
    if (!userData) return;

    console.log('[HEARTBEAT] Starting session heartbeat for', userData.naam);

    const heartbeatInterval = setInterval(async () => {
      try {
        const response = await axios.post(`${API}/session/heartbeat`, null, {
          params: { user_id: userData.id }
        });
        
        console.log('[HEARTBEAT] Session active, expires in', response.data.expires_in, 'seconds');
      } catch (error) {
        console.error('[HEARTBEAT] Session expired or error:', error);
        
        if (error.response?.status === 401) {
          console.log('[HEARTBEAT] Auto-logout due to session expiry');
          
          setMessages(prev => [...prev, {
            content: "⏱️ Je sessie is verlopen na 5 minuten inactiviteit.",
            isUser: false,
            timestamp: new Date().toISOString()
          }]);
          
          setTimeout(() => {
            handleLogout();
          }, 1000);
        }
      }
    }, 30000);

    return () => {
      console.log('[HEARTBEAT] Stopping session heartbeat');
      clearInterval(heartbeatInterval);
    };
  }, [userData]);

  // Fetch knowledge count
  useEffect(() => {
    if (userData) {
      fetchKnowledgeCount();
    }
  }, [userData]);

  // Fetch Spark's current emotion
  useEffect(() => {
    const fetchEmotion = async () => {
      try {
        const response = await axios.get(`${API}/emotions/current`);
        if (response.data.success) {
          setSparkEmotion(response.data.emotion);
        }
      } catch (error) {
        console.error('[ERROR] Failed to fetch emotion:', error);
      }
    };
    
    fetchEmotion();
    // Poll emotion every 30 seconds
    const emotionInterval = setInterval(fetchEmotion, 30000);
    
    return () => clearInterval(emotionInterval);
  }, []);

  // Load master volume and mood colors from settings
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await axios.get(`${API}/settings`);
        if (response.data.settings) {
          if (response.data.settings.master_volume !== undefined) {
            setMasterVolume(response.data.settings.master_volume);
          }
          if (response.data.settings.mood_colors !== undefined) {
            setMoodColorsEnabled(response.data.settings.mood_colors);
          }
        }
      } catch (error) {
        console.error('[ERROR] Failed to load settings:', error);
      }
    };
    loadSettings();
  }, []);

  // 🎨 Mood-based Color Theming
  useEffect(() => {
    if (!moodColorsEnabled || !sparkEmotion) return;
    
    const moodThemes = {
      happy: {
        primary: '#4CAF50',
        primaryLight: '#81C784',
        primaryDark: '#388E3C',
        accent: '#66BB6A',
        glow: 'rgba(76, 175, 80, 0.5)'
      },
      angry: {
        primary: '#F44336',
        primaryLight: '#EF5350',
        primaryDark: '#D32F2F',
        accent: '#FF5252',
        glow: 'rgba(244, 67, 54, 0.5)'
      },
      sad: {
        primary: '#2196F3',
        primaryLight: '#42A5F5',
        primaryDark: '#1976D2',
        accent: '#448AFF',
        glow: 'rgba(33, 150, 243, 0.5)'
      },
      scared: {
        primary: '#FFC107',
        primaryLight: '#FFD54F',
        primaryDark: '#FFA000',
        accent: '#FFCA28',
        glow: 'rgba(255, 193, 7, 0.5)'
      },
      neutral: {
        primary: '#4CAF50',
        primaryLight: '#81C784',
        primaryDark: '#388E3C',
        accent: '#66BB6A',
        glow: 'rgba(76, 175, 80, 0.5)'
      }
    };
    
    const emotionState = sparkEmotion.state || 'neutral';
    const theme = moodThemes[emotionState] || moodThemes.neutral;
    
    // Apply theme to CSS variables
    const root = document.documentElement;
    root.style.setProperty('--color-primary', theme.primary);
    root.style.setProperty('--color-primary-light', theme.primaryLight);
    root.style.setProperty('--color-primary-dark', theme.primaryDark);
    root.style.setProperty('--color-accent', theme.accent);
    root.style.setProperty('--color-glow', theme.glow);
    
    console.log(`🎨 [THEME] Mood changed to: ${emotionState} → ${theme.primary}`);
  }, [sparkEmotion, moodColorsEnabled]);


  const fetchKnowledgeCount = async () => {
    try {
      const response = await axios.get(`${API}/knowledge`);
      // Handle both array and object responses
      const data = Array.isArray(response.data) ? response.data : response.data.knowledge || [];
      const activeCount = data.filter(k => k.status === 'active').length;
      setKnowledgeCount(activeCount);
    } catch (error) {
      console.error('[ERROR] Failed to fetch knowledge count:', error);
    }
  };


  // Audio trigger system
  const checkAudioTriggers = async (message) => {
    try {
      const userId = userData?.id || 'guest';
      const response = await axios.get(`${API}/sounds/mappings`, { params: { user_id: userId } });
      const mappings = response.data.mappings || [];
      
      // Check settings: filter user sounds if disabled
      const settings = JSON.parse(localStorage.getItem('spark_settings') || '{}');
      const enableUserSounds = settings.enable_user_sounds || false;
      
      // Filter mappings based on setting
      const filteredMappings = enableUserSounds 
        ? mappings // Alle geluiden (system + user)
        : mappings.filter(m => m.type === 'system'); // Alleen system geluiden
      
      console.log(`[AUDIO] User sounds enabled: ${enableUserSounds}, filtering ${mappings.length} → ${filteredMappings.length} sounds`);
      
      const lowerMessage = message.toLowerCase();
      
      // Collect all triggered sounds with their position in the message
      const triggeredSounds = [];
      
      for (const mapping of filteredMappings) {
        const wordLower = mapping.word.toLowerCase();
        const index = lowerMessage.indexOf(wordLower);
        
        if (index !== -1) {
          // Found trigger word!
          console.log(`[AUDIO] Trigger detected: ${mapping.word} (${mapping.type}) at position ${index}`);
          
          // Check frequency
          const shouldPlay = checkFrequency(mapping);
          
          if (shouldPlay) {
            triggeredSounds.push({
              position: index,
              word: mapping.word,
              file: mapping.file,
              id: mapping.id
            });
          }
        }
      }
      
      // Sort by position in message (left to right)
      triggeredSounds.sort((a, b) => a.position - b.position);
      
      // Play sounds sequentially (one after another)
      for (const sound of triggeredSounds) {
        await playSoundSequential(sound.file);
        // Update play count
        await axios.post(`${API}/sounds/play/${sound.id}`).catch(err => console.error(err));
      }
      
    } catch (error) {
      console.error('[AUDIO] Error checking triggers:', error);
    }
  };

  const checkFrequency = (mapping) => {
    const playCountKey = `sound_play_${mapping.id}`;
    let playCount = parseInt(localStorage.getItem(playCountKey) || '0');
    
    if (mapping.frequency === 'every') {
      localStorage.setItem(playCountKey, (playCount + 1).toString());
      return true;
    } else if (mapping.frequency === 'first_only') {
      if (playCount === 0) {
        localStorage.setItem(playCountKey, '1');
        return true;
      }
      return false;
    } else if (mapping.frequency.startsWith('every_')) {
      const interval = parseInt(mapping.frequency.split('_')[1]);
      playCount += 1;
      localStorage.setItem(playCountKey, playCount.toString());
      return playCount % interval === 0;
    }
    return true;
  };

  const playSound = (filename) => {
    try {
      // Use API route for streaming
      const audioUrl = `${API}/sounds/stream/${filename}`;
      console.log(`[AUDIO] Loading from: ${audioUrl}`);
      
      const audio = new Audio(audioUrl);
      audio.volume = masterVolume / 100; // Convert 0-100 to 0.0-1.0
      audio.play().catch(err => {
        console.error('[AUDIO] Playback failed:', err);
      });
      console.log(`[AUDIO] Playing: ${filename} at ${masterVolume}% volume`);
    } catch (error) {
      console.error('[AUDIO] Error playing sound:', error);
    }
  };

  // Play sound sequentially (wait until finished before returning)
  const playSoundSequential = (filename) => {
    return new Promise((resolve) => {
      try {
        const audioUrl = `${API}/sounds/stream/${filename}`;
        console.log(`[AUDIO] Sequential play: ${audioUrl}`);
        
        const audio = new Audio(audioUrl);
        audio.volume = masterVolume / 100;
        
        // Wait for sound to finish before resolving
        audio.onended = () => {
          console.log(`[AUDIO] Finished: ${filename}`);
          resolve();
        };
        
        // Also resolve on error to not block the queue
        audio.onerror = (err) => {
          console.error('[AUDIO] Playback error:', err);
          resolve();
        };
        
        audio.play().catch(err => {
          console.error('[AUDIO] Play failed:', err);
          resolve();
        });
      } catch (error) {
        console.error('[AUDIO] Error in sequential play:', error);
        resolve();
      }
    });
  };

  const playSendSound = () => {
    try {
      // Simple beep sound
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = 800; // Hz
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(masterVolume / 300, audioContext.currentTime); // Subtle
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.1);
    } catch (error) {
      // Silent fail
    }
  };

  // 🎤 Voice: Text-to-Speech
  const playTextToSpeech = async (text, ttsSettings) => {
    try {
      const response = await axios.post(`${API}/voice/tts`, {
        text,
        voice: ttsSettings?.voice || 'nova',
        speed: ttsSettings?.speed || 1.0,
        model: ttsSettings?.model || 'tts-1',
        format: 'audio'
      }, {
        responseType: 'blob'
      });

      const audioBlob = response.data;
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.volume = masterVolume / 100;
      
      await audio.play();
      console.log('[VOICE] TTS played successfully');
      
      // Cleanup
      audio.onended = () => URL.revokeObjectURL(audioUrl);
    } catch (error) {
      console.error('[VOICE] TTS error:', error);
    }
  };

  // 🎙️ Voice: Handle transcript from Speech-to-Text
  const handleTranscriptReceived = (transcript) => {
    console.log('[VOICE] Transcript received:', transcript);
    setInputMessage(transcript);
    // Optionally auto-send:
    // setTimeout(() => handleSendMessage(), 300);
  };


  // Chat handling
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    if (chatMode === 'community') return; // Community not implemented yet

    const userMessage = { content: inputMessage, isUser: true };
    setMessages(prev => [...prev, userMessage]);
    
    // Check for audio triggers BEFORE sending
    checkAudioTriggers(inputMessage);
    
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: inputMessage,
        user_id: userData?.id || sessionId
      });

      const sparkMessage = {
        content: response.data.response,
        isUser: false
      };
      
      setMessages(prev => [...prev, sparkMessage]);
      
      // Play subtle success sound
      playSendSound();

      // 🎤 TTS: Auto-play if enabled
      const settings = JSON.parse(localStorage.getItem('spark_settings') || '{}');
      if (settings.tts?.enabled && settings.tts?.auto_play) {
        await playTextToSpeech(response.data.response, settings.tts);
      }

      // 🔥 FIX: Handle session expiry - if backend returns user_id=null while we have userData, logout
      if (userData && response.data.user_id === null && response.data.context === null) {
        console.log('[SESSION] Session expired, logging out');
        setUserData(null);
        return; // Don't process further
      }

      // Update userData if login happened
      if (response.data.user_id && response.data.context) {
        setUserData(response.data.context);
      }
      
      // 🎯 AUTO-FILL NOTIFICATIE (Nieuw!)
      if (response.data.auto_fill && response.data.auto_fill.updated_fields.length > 0) {
        const updates = response.data.auto_fill.updates;
        const fields = response.data.auto_fill.updated_fields;
        
        // Toon notificatie IN CHAT
        const fieldLabels = {
          'naam': 'Naam',
          'beroep': 'Beroep',
          'opleiding': 'Opleiding',
          'hobbies': "Hobby's",
          'muziek_voorkeur': 'Muziek voorkeur',
          'film_voorkeur': 'Film voorkeur',
          'game_voorkeur': 'Game voorkeur',
          'email': 'Email',
          'telefoon': 'Telefoon',
          'plaats': 'Woonplaats',
          'adres': 'Adres',
          'postcode': 'Postcode',
          'geboortedatum': 'Geboortedatum',
          'over_mij': 'Over mij'
        };
        
        // Maak een chat notificatie bericht
        const updatesList = fields.map(field => {
          const label = fieldLabels[field] || field;
          const value = updates[field];
          return `  • ${label}: ${value}`;
        }).join('\n');
        
        const notificationMessage = {
          content: `✨ **Profiel Automatisch Updated!**\n\n${updatesList}\n\n_Zie Mijn Profiel → Bewerken. Niet correct? Zeg "zet terug"_`,
          isUser: false,
          isSystem: true  // Special styling
        };
        
        setTimeout(() => {
          setMessages(prev => [...prev, notificationMessage]);
        }, 500);
        
        // Update userData met nieuwe info
        setUserData(response.data.context);
      }
      
      // If logout happened
      if (response.data.user_id === null && userData) {
        setUserData(null);
        setMessages([]);
      }

    } catch (error) {
      console.error('[ERROR] Chat error:', error);
      const errorMessage = {
        content: "⚠️ Er ging iets mis. Probeer het opnieuw.",
        isUser: false
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    setUserData(null);
    setMessages([]);
    setActiveTab("chat");
    localStorage.removeItem('spark_user_data');
    console.log('[LOGOUT] User logged out');
  };

  // Render tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'profiel':
        return <MijnProfielTabNew userData={userData} setUserData={setUserData} />;
      case 'chat':
        return <SparkChatTab />;
      case 'dagboek':
        return <DagboekTab userId={userData?.id} />;
      case 'agenda':
        return <AgendaTab userId={userData?.id} />;
      case 'taken':
        // Tasks now managed via Notes (hybrid system)
        return <NotitiesTab userId={userData?.id} />;
      case 'bestanden':
        return <BestandenTab />;
      case 'roadmap':
        return <RoadmapTab />;
      case 'spark_world':
        return <GameTab />;
      case 'uitgaven':
        return <UitgavenTab userId={userData?.id} />;
      case 'inkomsten':
        return <InkomstenTab userId={userData?.id} />;
      case 'dashboard':
        return <DashboardTab userId={userData?.id} userName={userData?.naam} />;
      case 'wallet':
        return <WalletTab userData={userData} />;
      case 'blueprints':
        return <BuildingBlueprintTab />;
      case 'blueprint_editor':
        return <BlueprintEditorTab />;  // NIEUW: Custom gebouwen/resources editor
      case 'buildings_overview':
        return <BuildingsOverviewTab />;
      case 'knowledge':
        return <KnowledgeBaseTab userId={userData?.id} isAdmin={userData?.gradatie === 1} />;
      case 'triggers':
        return <TriggersTab />;
      case 'monitor':
        return <MonitorTab />;
      case 'graph':
        return <GraphViewerTab />;
      case 'emotions':
        return <EmotionStatsTab userId={userData?.id} />;
      case 'leaderboard':
        return <LeaderboardTab userData={userData} />;
      case 'achievements':
        return <AchievementsTab userData={userData} />;
      case 'notities':
        return <NotitiesTab />;
      case 'status':
        return <StatusTabNew />;
      case 'settings':
        return <SettingsTabNew userData={userData} />;
      case 'logs':
        return <LogsTab userData={userData} />;
      case 'community':
        return <CommunityChat userData={userData} />;
      case 'mijn_wallet':
        return <UserWalletTab userData={userData} />;
      case 'winkel':
        return <WinkelTab userData={userData} />;
      case 'admin':
        return <AdminTab currentUser={userData} />;
      default:
        return <div style={{ padding: '40px', textAlign: 'center' }}>Tab not found</div>;
    }
  };

  return (
    <div className="app-layout">
      {/* Simple Status Bar - User + System Status */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 20px',
        background: 'rgba(0, 0, 0, 0.3)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        fontSize: '14px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {userData ? (
            <>
              <span>👤</span>
              <span style={{ color: 'white' }}>{userData.naam}</span>
            </>
          ) : (
            <>
              <span>🖐️</span>
              <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>Niet ingelogd</span>
            </>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></span>
          <span style={{ color: 'rgba(255, 255, 255, 0.9)' }}>Spark Core Online</span>
        </div>
      </div>
      
      {/* Main Body: Left Nav + Center Content + Right Panel */}
      <div className="app-body">
        <LeftNavigation
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          userData={userData}
          handleLogout={handleLogout}
        />

        <MainContentArea activeTab={activeTab} userData={userData}>
          {renderTabContent()}
        </MainContentArea>

        {/* RightInfoPanel REMOVED - Info moved to tabs */}
      </div>

      {/* Bottom Chat Area */}
      <ChatArea
        chatMode={chatMode}
        setChatMode={setChatMode}
        messages={messages}
        input={inputMessage}
        setInput={setInputMessage}
        handleSendMessage={handleSendMessage}
        isLoading={isLoading}
        userData={userData}
        onTranscriptReceived={handleTranscriptReceived}
      />
    </div>
  );
}

export default App;
