import React, { useState, useRef, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  MessageSquare, Send, Plus, Search, Users, Lock,
  Sparkles, Phone, Video, Bot, Circle, BookOpen, Zap,
  Shield, Timer
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const BOT_COLORS = {
  'bot-madelief': { bg: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/20', icon: Sparkles, accent: '#ec4899' },
  'bot-harry': { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/20', icon: Timer, accent: '#06b6d4' },
  'bot-smith': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', icon: Shield, accent: '#10b981' },
};

const initialSparkMessages = [
  { id: 1, role: 'spark', message: 'Hallo! Ik ben Spark, je persoonlijke AI assistent. Hoe kan ik je vandaag helpen?', time: '09:00' },
];

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

const initialPriveContacts = [
  { id: 1, contact: 'Harry', avatar: 'H', lastMessage: 'Tot morgen!', time: '16:45', unread: 0, online: true, color: '#22c55e' },
  { id: 2, contact: 'Sandra', avatar: 'S', lastMessage: 'Die analyse ziet er goed uit', time: '15:30', unread: 2, online: false, color: '#f59e0b' },
  { id: 3, contact: 'Peter', avatar: 'P', lastMessage: 'Kan je de docs delen?', time: 'Gisteren', unread: 0, online: true, color: '#3b82f6' },
];

export function GesprekkenPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const userName = user?.naam || 'Gebruiker';

  const [activeTab, setActiveTab] = useState('spark');
  // Lazy init: bij eerste render check sessionStorage. Behoud chat tussen page-switches.
  const [sparkMessages, setSparkMessages] = useState(() => loadStoredMessages(userId) || initialSparkMessages);
  const [newMessage, setNewMessage] = useState('');
  const [selectedContact, setSelectedContact] = useState(null);

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

  const tabs = [
    { id: 'spark', label: 'Spark AI', icon: Bot, accent: '#f59e0b' },
    { id: 'community', label: 'Community', icon: Users, accent: '#a855f7' },
    { id: 'prive', label: 'Privé', icon: Lock, accent: '#06b6d4' },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [sparkMessages, communityMessages, activeTab]);

  // Load community bot data when tab becomes active
  useEffect(() => {
    if (activeTab !== 'community') return;
    setCommunityLoading(true);
    Promise.all([
      fetch(`${API}/api/bots/community/messages?limit=100`).then(r => r.json()).catch(() => ({ messages: [] })),
      fetch(`${API}/api/bots/list`).then(r => r.json()).catch(() => ({ bots: [] })),
    ]).then(([m, b]) => {
      setCommunityMessages((m.messages || []).reverse());
      setBots(b.bots || []);
      setCommunityLoading(false);
    });
  }, [activeTab]);

  const handleSend = async () => {
    if (!newMessage.trim()) return;
    const text = newMessage.trim();
    setNewMessage('');

    if (activeTab === 'spark') {
      const userMsg = {
        id: Date.now(), role: 'user', message: text,
        time: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })
      };
      setSparkMessages(prev => [...prev, userMsg]);
      try {
        const res = await fetch(`${API}/api/chat/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, user_naam: userName, user_id: userId }),
        });
        const data = await res.json();
        setSparkMessages(prev => [...prev, {
          id: Date.now() + 1, role: 'spark',
          message: data.message || 'Hmm, daar moet ik even over nadenken.',
          time: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }),
          type: data.type,
          knowledge_matches: data.knowledge_matches || [],
          unknown_words: data.unknown_words || [],
          snap_suggestions: data.snap_suggestions || [],
          sentiment: data.sentiment,
        }]);
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
        setCommunityMessages(prev => [...prev, res.message, ...(res.bot_responses || [])]);
      }
      setSendingCommunity(false);
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
        <div className="flex-1 flex overflow-hidden">

          {/* --- SPARK AI TAB --- */}
          {activeTab === 'spark' && (
            <div className="flex-1 flex flex-col">
              <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
                {sparkMessages.map(msg => (
                  <SparkBubble key={msg.id} msg={msg} />
                ))}
                <div ref={messagesEndRef} />
              </div>
              <ChatInput
                value={newMessage}
                onChange={setNewMessage}
                onSend={handleSend}
                placeholder="Vraag Spark iets..."
                accent="#f59e0b"
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
                <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-3">
                  {communityLoading ? (
                    <p className="text-center text-slate-500 text-xs">Berichten laden...</p>
                  ) : communityMessages.length === 0 ? (
                    <p className="text-center text-slate-500 text-xs">Nog geen berichten. Typ iets om te starten!</p>
                  ) : (
                    communityMessages.map(msg => (
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
                />
              </div>
            </>
          )}

          {/* --- PRIVÉ TAB --- */}
          {activeTab === 'prive' && (
            <>
              <div className="w-52 md:w-64 bg-slate-900/40 border-r border-slate-800 flex flex-col flex-shrink-0">
                <div className="p-3">
                  <div className="relative mb-3">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                    <input
                      type="text"
                      placeholder="Zoek contact..."
                      data-testid="prive-search"
                      className="w-full pl-8 pr-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:border-cyan-500/50 focus:outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    {initialPriveContacts.map(c => (
                      <button
                        key={c.id}
                        data-testid={`contact-${c.contact.toLowerCase()}`}
                        onClick={() => setSelectedContact(c)}
                        className={`w-full flex items-center gap-3 p-2.5 rounded-lg transition-colors ${
                          selectedContact?.id === c.id
                            ? 'bg-cyan-500/10 border border-cyan-500/20'
                            : 'hover:bg-slate-800/50'
                        }`}
                      >
                        <div className="relative flex-shrink-0">
                          <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: c.color }}>
                            <span className="text-white text-xs font-bold">{c.avatar}</span>
                          </div>
                          {c.online && (
                            <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 border-2 border-slate-900 rounded-full" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0 text-left">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-white font-medium truncate">{c.contact}</span>
                            <span className="text-[10px] text-slate-500 ml-2 flex-shrink-0">{c.time}</span>
                          </div>
                          <p className="text-xs text-slate-400 truncate">{c.lastMessage}</p>
                        </div>
                        {c.unread > 0 && (
                          <span className="w-4 h-4 rounded-full text-[10px] text-white flex items-center justify-center flex-shrink-0" style={{ background: '#06b6d4' }}>
                            {c.unread}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex-1 flex flex-col">
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
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: selectedContact.color }}>
                          <span className="text-white text-xs font-bold">{selectedContact.avatar}</span>
                        </div>
                        <div>
                          <h3 className="text-sm font-semibold text-white">{selectedContact.contact}</h3>
                          <p className={`text-[10px] flex items-center gap-1 ${selectedContact.online ? 'text-green-400' : 'text-slate-500'}`}>
                            <Circle className="w-1.5 h-1.5 fill-current" />
                            {selectedContact.online ? 'Online' : 'Offline'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button data-testid="call-btn" className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                          <Phone className="w-4 h-4 text-slate-400" />
                        </button>
                        <button data-testid="video-btn" className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
                          <Video className="w-4 h-4 text-slate-400" />
                        </button>
                      </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-6 flex items-center justify-center">
                      <div className="text-center">
                        <div className="w-14 h-14 rounded-xl flex items-center justify-center mx-auto mb-3" style={{ background: selectedContact.color }}>
                          <span className="text-xl font-bold text-white">{selectedContact.avatar}</span>
                        </div>
                        <h3 className="text-white font-semibold text-sm">{selectedContact.contact}</h3>
                        <p className="text-slate-500 text-xs mt-1">Begin een gesprek</p>
                      </div>
                    </div>
                    <ChatInput
                      value={newMessage}
                      onChange={setNewMessage}
                      onSend={handleSend}
                      placeholder={`Bericht aan ${selectedContact.contact}...`}
                      accent="#06b6d4"
                    />
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </MainLayout>
  );
}

/* === Chat input in framed container === */
function ChatInput({ value, onChange, onSend, placeholder, accent, disabled = false }) {
  return (
    <div className="p-4 bg-slate-900/20 border-t border-slate-800 flex-shrink-0">
      <div
        className="flex items-center gap-2 max-w-4xl mx-auto bg-slate-800/60 border border-slate-700/60 rounded-2xl px-2 py-1.5 shadow-lg focus-within:border-slate-600 transition-colors"
        style={{ '--accent': accent }}
      >
        <button data-testid="attach-btn" className="p-2 hover:bg-slate-700/50 rounded-xl transition-colors flex-shrink-0">
          <Plus className="w-4 h-4 text-slate-400" />
        </button>
        <input
          type="text"
          data-testid="chat-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !disabled && onSend()}
          placeholder={placeholder}
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
function SparkBubble({ msg }) {
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
          <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
            <Sparkles className="w-3.5 h-3.5 text-white" />
          </div>
        )}
        <div>
          <div className={`px-4 py-2.5 rounded-2xl ${
            isUser
              ? 'bg-amber-500 text-white rounded-br-md'
              : 'bg-slate-800 text-white rounded-bl-md'
          }`}>
            <p className="text-sm leading-relaxed whitespace-pre-line">{msg.message}</p>
            <p className={`text-[10px] mt-1 ${isUser ? 'text-amber-200' : 'text-slate-500'}`}>{msg.time}</p>
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

  return (
    <div data-testid={`community-msg-${msg.id}`} className={`flex gap-2.5 ${isOwn ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
        isBot ? (style.bg || 'bg-slate-800') : isOwn ? 'bg-amber-500/20' : 'bg-slate-800'
      }`}>
        {isBot
          ? <BotIcon className={`w-4 h-4 ${style.text || 'text-slate-400'}`} />
          : <span className={`text-[11px] font-bold ${isOwn ? 'text-amber-400' : 'text-slate-400'}`}>{(msg.user_name || 'U').charAt(0)}</span>}
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
