import React, { useState, useEffect, useRef } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  MessageCircle, Send, Bot, User, Clock, Users,
  Loader2, Sparkles, Shield, Timer
} from 'lucide-react';
import EventOverlay from '../events/EventOverlay';

const API = process.env.REACT_APP_BACKEND_URL;

const BOT_COLORS = {
  'bot-madelief': { bg: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/20', icon: Sparkles },
  'bot-harry': { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/20', icon: Timer },
  'bot-smith': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', icon: Shield },
};

export function CommunityPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const userName = user?.naam || 'Willem';
  const [messages, setMessages] = useState([]);
  const [bots, setBots] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  const loadData = () => {
    Promise.all([
      fetch(`${API}/api/bots/community/messages?limit=100`).then(r => r.json()).catch(() => ({ messages: [] })),
      fetch(`${API}/api/bots/list`).then(r => r.json()).catch(() => ({ bots: [] })),
    ]).then(([m, b]) => {
      setMessages((m.messages || []).reverse());
      setBots(b.bots || []);
      setLoading(false);
    });
  };

  useEffect(() => { loadData(); }, []);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || sending) return;
    const text = input.trim();
    setInput('');
    setSending(true);

    const res = await fetch(`${API}/api/bots/community/send`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, user_id: userId, user_name: userName }),
    }).then(r => r.json()).catch(() => ({ success: false }));

    if (res.success) {
      setMessages(prev => [...prev, res.message, ...(res.bot_responses || [])]);
    }
    setSending(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  if (loading) return (
    <MainLayout activePage="community" onNavigate={onNavigate}>
      <div className="flex items-center justify-center h-full"><Loader2 className="w-8 h-8 text-blue-500 animate-spin" /></div>
    </MainLayout>
  );

  return (
    <MainLayout activePage="community" onNavigate={onNavigate}>
      <div data-testid="community-page" className="h-full flex flex-col">
        <EventOverlay target="community" />

        {/* Header */}
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <MessageCircle className="w-4 h-4 text-blue-400" />
              </div>
              <div>
                <h1 className="text-base font-bold text-white leading-tight">Community</h1>
                <p className="text-[10px] text-slate-500">{messages.length} berichten | {bots.length} bots online</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {bots.map(bot => {
                const style = BOT_COLORS[bot.id] || { bg: 'bg-slate-800', text: 'text-slate-400', border: 'border-slate-700', icon: Bot };
                const BotIcon = style.icon;
                return (
                  <div key={bot.id} className={`flex items-center gap-1.5 px-2 py-1 rounded-lg ${style.bg} border ${style.border}`}>
                    <BotIcon className={`w-3 h-3 ${style.text}`} />
                    <span className={`text-[10px] font-medium ${style.text}`}>{bot.naam.split(' ')[0]}</span>
                    <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {messages.map(msg => (
            <ChatBubble key={msg.id} msg={msg} isOwn={msg.user_id === userId} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="flex-shrink-0 bg-slate-900/80 border-t border-slate-800 p-3">
          <div className="flex items-center gap-2 max-w-3xl mx-auto">
            <input
              data-testid="community-input"
              type="text" value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Typ een bericht... (bots reageren op keywords)"
              className="flex-1 px-4 py-3 bg-slate-800/80 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50"
            />
            <button data-testid="community-send" onClick={sendMessage} disabled={sending || !input.trim()}
              className="p-3 bg-blue-500 hover:bg-blue-600 rounded-xl transition-colors disabled:opacity-50 disabled:bg-slate-700">
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

function ChatBubble({ msg, isOwn }) {
  const isBot = msg.is_bot;
  const style = BOT_COLORS[msg.user_id] || {};
  const BotIcon = style.icon || Bot;
  const API = process.env.REACT_APP_BACKEND_URL;
  const avatar = msg.avatar;  // v4_community_avatar_001
  const avatarUrl = avatar?.kind === 'image' && avatar.url ? `${API}${avatar.url}` : null;
  const avatarEmoji = avatar?.kind === 'emoji' ? avatar.emoji : null;

  return (
    <div data-testid={`msg-${msg.id}`} className={`flex gap-2.5 ${isOwn ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div data-testid={`msg-avatar-${msg.user_id}`} className={`w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 ${
        avatarUrl ? '' : isBot ? (style.bg || 'bg-slate-800') : isOwn ? 'bg-amber-500/20' : 'bg-slate-800'
      }`}>
        {avatarUrl ? (
          <img src={avatarUrl} alt={msg.user_name} className="w-full h-full object-cover"
            onError={(e) => { e.target.style.display = 'none'; e.target.parentNode.classList.add(isBot ? 'bg-slate-800' : 'bg-slate-800'); }} />
        ) : avatarEmoji ? (
          <span className="text-lg leading-none">{avatarEmoji}</span>
        ) : isBot ? (
          <BotIcon className={`w-4 h-4 ${style.text || 'text-slate-400'}`} />
        ) : (
          <User className={`w-4 h-4 ${isOwn ? 'text-amber-400' : 'text-slate-400'}`} />
        )}
      </div>

      {/* Bubble */}
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

export default CommunityPage;
