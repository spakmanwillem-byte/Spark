import React, { useState, useRef, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import { 
  MessageSquare, Send, Plus, Search, Users, Lock,
  Sparkles, Heart, Smile, MoreHorizontal, Phone, Video,
  Image, Paperclip, Mic, ChevronDown, Star, Circle,
  Bot, User, Clock, Check, CheckCheck, Hash, BookOpen, Zap
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const initialConversations = {
  spark: [
    { id: 1, role: 'spark', message: 'Hallo! Ik ben Spark, je persoonlijke AI assistent. Hoe kan ik je vandaag helpen?', time: '09:00' },
    { id: 2, role: 'user', message: 'Hey Spark! Kun je me helpen met de knowledge base?', time: '09:01' },
    { id: 3, role: 'spark', message: 'Natuurlijk! De Knowledge Base bevat momenteel 1,847 entries verdeeld over 3 lagen. Wat wil je precies weten of toevoegen?', time: '09:01' },
  ],
  community: [
    { id: 1, user: 'Maurice', avatar: 'M', message: 'Heeft iemand ervaring met de nieuwe trigger functie?', time: '14:30', color: '#a855f7' },
    { id: 2, user: 'Lisa', avatar: 'L', message: 'Ja! Werkt super goed voor begroetingen', time: '14:32', color: '#ec4899' },
    { id: 3, user: 'Tom', avatar: 'T', message: 'Ik heb een paar custom triggers toegevoegd, delen?', time: '14:35', color: '#06b6d4' },
    { id: 4, user: 'Anna', avatar: 'A', message: 'Graag! Deel ze in het Ideeën kanaal', time: '14:40', color: '#10b981' },
  ],
  prive: [
    { id: 1, contact: 'Harry', avatar: 'H', lastMessage: 'Tot morgen!', time: '16:45', unread: 0, online: true, color: '#22c55e' },
    { id: 2, contact: 'Sandra', avatar: 'S', lastMessage: 'Die analyse ziet er goed uit', time: '15:30', unread: 2, online: false, color: '#f59e0b' },
    { id: 3, contact: 'Peter', avatar: 'P', lastMessage: 'Kan je de docs delen?', time: 'Gisteren', unread: 0, online: true, color: '#3b82f6' },
  ]
};

const communityRooms = [
  { id: 'algemeen', name: 'Algemeen', members: 12 },
  { id: 'ontwikkelaars', name: 'Ontwikkelaars', members: 5 },
  { id: 'support', name: 'Support', members: 8 },
  { id: 'ideeen', name: 'Ideeën', members: 15 },
];

export function GesprekkenPage({ onNavigate }) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('spark');
  const [sparkMessages, setSparkMessages] = useState(initialConversations.spark);
  const [newMessage, setNewMessage] = useState('');
  const [selectedContact, setSelectedContact] = useState(null);
  const [selectedRoom, setSelectedRoom] = useState('algemeen');
  const messagesEndRef = useRef(null);

  const tabs = [
    { id: 'spark', label: 'Spark AI', icon: Bot, accent: '#f59e0b' },
    { id: 'community', label: 'Community', icon: Users, accent: '#a855f7' },
    { id: 'prive', label: 'Privé', icon: Lock, accent: '#06b6d4' },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [sparkMessages, activeTab]);

  const handleSend = async () => {
    if (!newMessage.trim()) return;
    const userMsg = {
      id: sparkMessages.length + 1,
      role: 'user',
      message: newMessage,
      time: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })
    };
    setSparkMessages(prev => [...prev, userMsg]);
    setNewMessage('');

    if (activeTab === 'spark') {
      // Echte API call naar Snap/NLP engine
      try {
        const res = await fetch(`${API}/api/chat/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: newMessage, user_naam: user?.naam || 'Gebruiker' }),
        });
        const data = await res.json();
        
        const sparkMsg = {
          id: Date.now(),
          role: 'spark',
          message: data.message || 'Hmm, daar moet ik even over nadenken.',
          time: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }),
          type: data.type,
          knowledge_matches: data.knowledge_matches || [],
          unknown_words: data.unknown_words || [],
          snap_suggestions: data.snap_suggestions || [],
          sentiment: data.sentiment,
        };
        setSparkMessages(prev => [...prev, sparkMsg]);
      } catch (e) {
        setSparkMessages(prev => [...prev, {
          id: Date.now(), role: 'spark',
          message: 'Er ging iets mis met de verbinding. Probeer het opnieuw.',
          time: new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }),
        }]);
      }
    }
  };

  const activeTabData = tabs.find(t => t.id === activeTab);

  return (
    <MainLayout activePage="chat" onNavigate={onNavigate}>
      <div data-testid="gesprekken-page" className="h-[calc(100vh-4rem)] flex flex-col">

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
              return (
                <button
                  key={tab.id}
                  data-testid={`tab-${tab.id}`}
                  onClick={() => { setActiveTab(tab.id); setSelectedContact(null); }}
                  className="relative flex items-center gap-2 px-5 py-2.5 text-sm font-medium transition-colors"
                  style={{ color: isActive ? tab.accent : '#94a3b8' }}
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

          {/* --- COMMUNITY TAB --- */}
          {activeTab === 'community' && (
            <>
              {/* Room list sidebar */}
              <div className="w-52 md:w-60 bg-slate-900/40 border-r border-slate-800 flex flex-col flex-shrink-0">
                <div className="p-3">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-2 px-2">Kanalen</p>
                  {communityRooms.map(room => (
                    <button
                      key={room.id}
                      data-testid={`room-${room.id}`}
                      onClick={() => setSelectedRoom(room.id)}
                      className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors mb-0.5 ${
                        selectedRoom === room.id
                          ? 'bg-purple-500/15 text-purple-300'
                          : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                      }`}
                    >
                      <Hash className="w-3.5 h-3.5 flex-shrink-0" />
                      <span className="truncate">{room.name}</span>
                      <span className="ml-auto text-[10px] text-slate-600">{room.members}</span>
                    </button>
                  ))}
                </div>
              </div>
              {/* Community messages */}
              <div className="flex-1 flex flex-col">
                <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
                  {initialConversations.community.map(msg => (
                    <CommunityBubble key={msg.id} msg={msg} />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
                <ChatInput
                  value={newMessage}
                  onChange={setNewMessage}
                  onSend={handleSend}
                  placeholder="Typ een bericht..."
                  accent="#a855f7"
                />
              </div>
            </>
          )}

          {/* --- PRIVÉ TAB --- */}
          {activeTab === 'prive' && (
            <>
              {/* Contacts sidebar */}
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
                    {initialConversations.prive.map(c => (
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
              {/* Private chat area */}
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
                    {/* Contact header */}
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
                    {/* Placeholder chat area */}
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

/* === Reusable chat input === */
function ChatInput({ value, onChange, onSend, placeholder, accent }) {
  return (
    <div className="p-3 border-t border-slate-800 bg-slate-900/30 flex-shrink-0">
      <div className="flex items-center gap-2">
        <button data-testid="attach-btn" className="p-2 hover:bg-slate-800 rounded-lg transition-colors flex-shrink-0">
          <Plus className="w-4 h-4 text-slate-400" />
        </button>
        <div className="flex-1 relative">
          <input
            type="text"
            data-testid="chat-input"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onSend()}
            placeholder={placeholder}
            className="w-full px-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none transition-colors"
            style={{ '--tw-ring-color': accent }}
          />
        </div>
        <button
          data-testid="send-btn"
          onClick={onSend}
          className="p-2.5 rounded-xl transition-all flex-shrink-0"
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
          {/* Knowledge matches badges */}
          {hasMatches && (
            <div className="flex flex-wrap gap-1 mt-1.5 ml-1">
              {msg.knowledge_matches.map((m, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 bg-amber-500/10 text-amber-400 rounded-full flex items-center gap-1">
                  <BookOpen className="w-2.5 h-2.5" /> {m.begrip}
                </span>
              ))}
            </div>
          )}
          {/* Snap suggestions */}
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

/* === Community message bubble === */
function CommunityBubble({ msg }) {
  return (
    <div className="flex items-start gap-2.5">
      <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: msg.color }}>
        <span className="text-white text-[10px] font-bold">{msg.avatar}</span>
      </div>
      <div>
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-xs font-medium text-white">{msg.user}</span>
          <span className="text-[10px] text-slate-500">{msg.time}</span>
        </div>
        <div className="px-3.5 py-2 bg-slate-800 rounded-2xl rounded-tl-md">
          <p className="text-sm text-white leading-relaxed">{msg.message}</p>
        </div>
      </div>
    </div>
  );
}

export default GesprekkenPage;
