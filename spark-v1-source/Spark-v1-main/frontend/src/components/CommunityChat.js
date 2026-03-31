import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './CommunityChat.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CommunityChat = ({ userData }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [activeUsers, setActiveUsers] = useState([]);
  const [hasJoined, setHasJoined] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load messages
    loadMessages();
    
    // Auto-join when component mounts
    if (userData && !hasJoined) {
      joinCommunity();
    }

    // Poll for new messages every 3 seconds
    const interval = setInterval(() => {
      loadMessages();
    }, 3000);

    return () => {
      clearInterval(interval);
      // Leave when unmounting
      if (userData && hasJoined) {
        leaveCommunity();
      }
    };
  }, [userData, hasJoined]);

  const loadMessages = async () => {
    try {
      const response = await axios.get(`${API}/community/messages?limit=50`);
      if (response.data.success) {
        setMessages(response.data.messages);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const joinCommunity = async () => {
    if (!userData) return;
    
    try {
      const response = await axios.post(`${API}/community/join`, {
        user_id: userData.id,
        user_name: userData.naam
      });
      
      if (response.data.success) {
        setHasJoined(true);
        // Reload messages to see Madelief's greeting
        setTimeout(() => loadMessages(), 500);
      }
    } catch (error) {
      console.error('Error joining community:', error);
    }
  };

  const leaveCommunity = async () => {
    if (!userData) return;
    
    try {
      await axios.post(`${API}/community/leave`, {
        user_id: userData.id,
        user_name: userData.naam
      });
      setHasJoined(false);
    } catch (error) {
      console.error('Error leaving community:', error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !userData) return;

    try {
      const response = await axios.post(`${API}/community/message`, {
        user_id: userData.id,
        user_name: userData.naam,
        message: input,
        is_bot: false
      });

      if (response.data.success) {
        setInput('');
        // Reload to see your message and bot responses
        setTimeout(() => loadMessages(), 300);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!userData) {
    return (
      <div className="community-chat">
        <div className="community-login-prompt">
          <h2>🌟 Community Chat</h2>
          <p>Login om deel te nemen aan de community!</p>
          <p className="bot-info">👋 Madelief, Harry en Mr Smith wachten op je!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="community-chat">
      <div className="community-header">
        <h2>🌟 Spark Community</h2>
        <div className="online-indicator">
          <span className="pulse-dot"></span>
          {activeUsers.length} online
        </div>
      </div>

      <div className="community-content">
        <div className="messages-area">
          <div className="welcome-message">
            <p>👋 Welkom in de Spark Community!</p>
            <p className="small">Chat met andere users en onze bot vrienden: Madelief 👋, Harry 🕐, en Mr Smith 🕵️</p>
          </div>

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`community-message ${
                msg.is_bot ? 'bot-message' : msg.user_id === userData?.id ? 'own-message' : 'other-message'
              }`}
            >
              <div className="message-header">
                <span className="message-author">
                  {msg.is_bot && '🤖 '}
                  {msg.user_name}
                </span>
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString('nl-NL', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
              <div className="message-content">{msg.message}</div>
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="community-input-area">
        <input
          type="text"
          className="community-input"
          placeholder="Type een bericht..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <button
          className="send-btn"
          onClick={sendMessage}
          disabled={!input.trim()}
        >
          Verstuur
        </button>
      </div>
    </div>
  );
};

export default CommunityChat;
