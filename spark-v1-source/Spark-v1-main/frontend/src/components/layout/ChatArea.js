import React, { useState, useRef, useEffect, useCallback } from 'react';
import VoiceControls from '../VoiceControls';

const ChatArea = ({ 
  chatMode, 
  setChatMode, 
  messages, 
  input, 
  setInput, 
  handleSendMessage, 
  isLoading,
  userData,
  onTranscriptReceived 
}) => {
  const [chatHeight, setChatHeight] = useState(() => {
    const saved = localStorage.getItem('spark_chat_height');
    return saved ? parseInt(saved) : 250;
  });
  const [isDragging, setIsDragging] = useState(false);
  const startY = useRef(0);
  const startHeight = useRef(0);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null); // Nieuwe ref voor input field
  const prevInputLength = useRef(input.length);

  // Auto-scroll naar beneden bij nieuwe berichten
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Auto-focus input field when it becomes empty (after sending)
  useEffect(() => {
    if (prevInputLength.current > 0 && input.length === 0 && inputRef.current) {
      // Input was just cleared → focus it immediately
      requestAnimationFrame(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      });
    }
    prevInputLength.current = input.length;
  }, [input]);

  // Always ensure input is focused when loading state changes
  useEffect(() => {
    if (!isLoading && inputRef.current && chatMode === 'spark') {
      requestAnimationFrame(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      });
    }
  }, [isLoading, chatMode]);

  const handleMouseDown = (e) => {
    setIsDragging(true);
    startY.current = e.clientY;
    startHeight.current = chatHeight;
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging) return;
      
      const deltaY = startY.current - e.clientY;
      const maxHeight = window.innerHeight * 0.75; // 75% van schermhoogte
      const newHeight = Math.max(80, Math.min(maxHeight, startHeight.current + deltaY));
      setChatHeight(newHeight);
    };

    const handleMouseUp = () => {
      if (isDragging) {
        setIsDragging(false);
        localStorage.setItem('spark_chat_height', chatHeight.toString());
      }
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, chatHeight]);

  return (
    <div className="chat-area minimized" style={{ height: `${chatHeight}px`, display: 'flex', flexDirection: 'column' }}>
      {/* Resize Handle */}
      <div 
        className={`chat-resize-handle ${isDragging ? 'dragging' : ''}`}
        onMouseDown={handleMouseDown}
      >
        <div className="resize-indicator"></div>
      </div>

      {/* Chat Messages - BOVEN de mode knoppen */}
      <div className="chat-messages" style={{ 
        flex: '1 1 auto', 
        overflowY: 'auto', 
        padding: '15px 20px',
        minHeight: '0'
      }}>
        {messages.length === 0 && (
          <div style={{ 
            textAlign: 'center', 
            color: 'rgba(255,255,255,0.4)', 
            padding: '20px' 
          }}>
            <div style={{ fontSize: '48px', marginBottom: '10px' }}>💬</div>
            <div>Chat met Spark</div>
            <div style={{ fontSize: '14px', marginTop: '5px' }}>
              {userData ? 'Type een bericht...' : 'Login om te chatten'}
            </div>
          </div>
        )}
        
        {chatMode === 'spark' && messages.map((msg, idx) => (
          <div
            key={idx}
            className={`message ${msg.isUser ? 'user-message' : 'spark-message'}`}
          >
            <div className="message-icon">
              {msg.isUser ? '👤' : '✨'}
            </div>
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        ))}
        
        {chatMode === 'community' && (
          <div className="chat-placeholder">
            <div className="placeholder-icon">👥</div>
            <h3>Community Chat</h3>
            <p>Binnenkort kunnen gebruikers hier met elkaar chatten via Spark.</p>
          </div>
        )}
        
        {/* Invisible div voor auto-scroll */}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input Container - ONDER de messages */}
      <div className="chat-input-container" style={{ flexShrink: 0 }}>
        {/* Chat Mode Toggle */}
        <div className="chat-mode-toggle">
          <button
            className={`mode-btn ${chatMode === 'spark' ? 'active' : ''}`}
            onClick={() => setChatMode('spark')}
          >
            💬 Spark
          </button>
          <button
            className={`mode-btn ${chatMode === 'community' ? 'active' : ''} disabled`}
            onClick={() => setChatMode('community')}
            disabled
          >
            👥 Community <span className="coming-soon">(binnenkort)</span>
          </button>
        </div>

        <div className="chat-input-area">
          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            placeholder={
              chatMode === 'spark' 
                ? 'Type een bericht...' 
                : 'Community chat komt binnenkort...'
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && chatMode === 'spark' && !isLoading) {
                e.preventDefault();
                if (input.trim()) {
                  handleSendMessage();
                }
              }
            }}
            disabled={isLoading || chatMode === 'community'}
          />
          
          {/* Voice Controls */}
          {onTranscriptReceived && (
            <VoiceControls 
              onTranscriptReceived={onTranscriptReceived}
              settings={JSON.parse(localStorage.getItem('spark_settings') || '{}')}
            />
          )}
          
          <button
            className="send-btn"
            onClick={() => {
              if (input.trim() && !isLoading) {
                handleSendMessage();
              }
            }}
            disabled={isLoading || !input.trim() || chatMode === 'community'}
          >
            {isLoading ? '...' : 'Verzend'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatArea;
