import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TriggerManagerTab = () => {
  const [triggers, setTriggers] = useState({
    emotions: {},
    conversation: {},
    calendar: {},
  });
  const [actionTriggers, setActionTriggers] = useState([]); // NIEUW: Action triggers (monitor, logs, etc.)
  const [newWords, setNewWords] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTriggers();
    loadActionTriggers(); // NIEUW
  }, []);

  const loadTriggers = async () => {
    try {
      const response = await axios.get(`${API}/triggers/all`);
      setTriggers(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading triggers:', error);
      setLoading(false);
    }
  };

  // NIEUW: Laad action triggers uit knowledge base
  const loadActionTriggers = async () => {
    try {
      const response = await axios.get(`${API}/knowledge-base`);
      const kb = response.data;
      
      // Filter action triggers
      if (kb.triggers && Array.isArray(kb.triggers)) {
        const actions = kb.triggers.filter(t => t.type === 'action');
        setActionTriggers(actions);
      }
    } catch (error) {
      console.error('Error loading action triggers:', error);
    }
  };

  const handleAddWord = async (category, subcategory, word) => {
    if (!word || !word.trim()) {
      alert('❌ Vul een woord in');
      return;
    }

    try {
      await axios.post(`${API}/triggers/add`, {
        category,
        subcategory,
        word: word.trim().toLowerCase()
      });

      alert('✅ Woord toegevoegd!');
      setNewWords({...newWords, [`${category}_${subcategory}`]: ''});
      loadTriggers(); // Refresh
    } catch (error) {
      console.error('Error adding word:', error);
      alert('❌ Fout bij toevoegen woord');
    }
  };

  const handleRemoveWord = async (category, subcategory, word) => {
    if (!window.confirm(`⚠️ Weet je zeker dat je "${word}" wilt verwijderen?`)) {
      return;
    }

    try {
      await axios.delete(`${API}/triggers/remove`, {
        params: { category, subcategory, word }
      });

      alert('✅ Woord verwijderd');
      loadTriggers(); // Refresh
    } catch (error) {
      console.error('Error removing word:', error);
      alert('❌ Fout bij verwijderen');
    }
  };

  const renderTriggerCard = (category, subcategory, title, icon, words) => {
    const key = `${category}_${subcategory}`;
    const currentWord = newWords[key] || '';

    return (
      <div className="trigger-card" key={key}>
        <div className="card-header">
          <span className="card-icon">{icon}</span>
          <h3 className="card-title">{title}</h3>
        </div>

        <div className="card-input-section">
          <input
            type="text"
            value={currentWord}
            onChange={(e) => setNewWords({...newWords, [key]: e.target.value})}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleAddWord(category, subcategory, currentWord);
              }
            }}
            placeholder="Nieuw trigger woord..."
            className="trigger-input"
          />
          <button
            onClick={() => handleAddWord(category, subcategory, currentWord)}
            className="apply-btn"
          >
            ➕ Apply
          </button>
        </div>

        <div className="words-container">
          <div className="words-label">Huidige woorden ({(() => {
            if (Array.isArray(words)) return words.length;
            if (typeof words === 'object' && words !== null) {
              const wordKeys = Object.keys(words.triggers || words);
              return wordKeys.length;
            }
            return 0;
          })()}):</div>
          <div className="words-list">
            {(() => {
              // Handle both array and object formats
              let wordArray = [];
              if (Array.isArray(words)) {
                wordArray = words;
              } else if (typeof words === 'object' && words !== null) {
                // words is object like {triggers: {word1: score, word2: score}}
                wordArray = Object.keys(words.triggers || words);
              }
              
              return wordArray.length > 0 ? (
                wordArray.map((word, idx) => (
                  <div key={idx} className="word-chip">
                    <span>{word}</span>
                    <button
                      onClick={() => handleRemoveWord(category, subcategory, word)}
                      className="remove-word-btn"
                      style={{ 
                        pointerEvents: 'auto',
                        zIndex: 9999,
                        cursor: 'pointer'
                      }}
                      type="button"
                      title="Verwijder"
                    >
                      ×
                    </button>
                  </div>
                ))
              ) : (
                <div className="empty-state">Geen woorden</div>
              );
            })()}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p>⏳ Laden...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '30px' }}>
      <h2 style={{ marginBottom: '10px' }}>🎯 Trigger Manager</h2>
      <p style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '14px', marginBottom: '30px' }}>
        Beheer trigger woorden voor emoties, gesprekken en agenda events
      </p>

      {/* EMOTIES SECTION */}
      <div className="section-container">
        <h3 className="section-title">💭 Emotie Triggers</h3>
        <div className="trigger-grid">
          {triggers.emotions.blij && renderTriggerCard(
            'emotions', 'blij', 'Emotie - Blij', '😊', triggers.emotions.blij.triggers || triggers.emotions.blij
          )}
          {triggers.emotions.boos && renderTriggerCard(
            'emotions', 'boos', 'Emotie - Boos', '😠', triggers.emotions.boos.triggers || triggers.emotions.boos
          )}
          {triggers.emotions.bang && renderTriggerCard(
            'emotions', 'bang', 'Emotie - Bang', '😰', triggers.emotions.bang.triggers || triggers.emotions.bang
          )}
          {triggers.emotions.bedroefd && renderTriggerCard(
            'emotions', 'bedroefd', 'Emotie - Bedroefd', '😢', triggers.emotions.bedroefd.triggers || triggers.emotions.bedroefd
          )}
        </div>
      </div>

      {/* CONVERSATIE SECTION */}
      <div className="section-container">
        <h3 className="section-title">💬 Conversatie Triggers</h3>
        <div className="trigger-grid">
          {triggers.conversation.greeting && renderTriggerCard(
            'conversation', 'greeting', 'Begroeting', '👋', triggers.conversation.greeting
          )}
          {triggers.conversation.thanks && renderTriggerCard(
            'conversation', 'thanks', 'Bedankjes', '🙏', triggers.conversation.thanks
          )}
          {triggers.conversation.how_are_you && renderTriggerCard(
            'conversation', 'how_are_you', 'Hoe gaat het?', '❓', triggers.conversation.how_are_you
          )}
        </div>
      </div>

      {/* AGENDA & DAGBOEK SECTION - NIEUW */}
      <div className="section-container" style={{ marginTop: '30px', backgroundColor: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.3)', borderRadius: '8px', padding: '20px' }}>
        <h3 className="section-title">📅 Agenda & Dagboek Activatie</h3>
        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px', marginBottom: '20px' }}>
          Gebruik prefixes om agenda items of dagboek entries aan te maken
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '15px', borderRadius: '6px' }}>
            <div style={{ fontSize: '24px', marginBottom: '10px' }}>📅</div>
            <h4 style={{ color: '#60A5FA', marginBottom: '8px' }}>Agenda / Afspraken</h4>
            <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)', marginBottom: '8px' }}>
              Prefixes: "Note agenda:", "afspraak:", "agenda:"
            </p>
            <div style={{ backgroundColor: 'rgba(99, 102, 241, 0.2)', padding: '10px', borderRadius: '4px', fontSize: '13px', fontFamily: 'monospace' }}>
              💬 "Note agenda: Morgen meeting om 10:00"
            </div>
          </div>
          <div style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '15px', borderRadius: '6px' }}>
            <div style={{ fontSize: '24px', marginBottom: '10px' }}>📔</div>
            <h4 style={{ color: '#34D399', marginBottom: '8px' }}>Dagboek Entries</h4>
            <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)', marginBottom: '8px' }}>
              Prefixes: "Note dagboek:", "dagboek entry:"
            </p>
            <div style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)', padding: '10px', borderRadius: '4px', fontSize: '13px', fontFamily: 'monospace' }}>
              💬 "Note dagboek: Vandaag was een goede dag"
            </div>
          </div>
        </div>
      </div>

      {/* AGENDA SECTION */}
      <div className="section-container">
        <h3 className="section-title">📅 Agenda Triggers</h3>
        <div className="trigger-grid">
          {triggers.calendar.add_event && renderTriggerCard(
            'calendar', 'add_event', 'Event Toevoegen', '➕', triggers.calendar.add_event
          )}
          {triggers.calendar.view_events && renderTriggerCard(
            'calendar', 'view_events', 'Events Bekijken', '👁️', triggers.calendar.view_events
          )}
        </div>
      </div>

      <style jsx>{`
        .section-container {
          margin-bottom: 40px;
        }

        .section-title {
          font-size: 20px;
          margin-bottom: 20px;
          color: rgb(255, 255, 255);
        }

        .trigger-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 20px;
        }

        .trigger-card {
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 20px;
          transition: all 0.2s ease;
        }

        .trigger-card:hover {
          border-color: rgba(255, 255, 255, 0.2);
          transform: translateY(-2px);
        }

        .card-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 15px;
          padding-bottom: 12px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .card-icon {
          font-size: 28px;
        }

        .card-title {
          margin: 0;
          font-size: 16px;
          color: rgb(255, 255, 255);
        }

        .card-input-section {
          display: flex;
          gap: 10px;
          margin-bottom: 15px;
        }

        .trigger-input {
          flex: 1;
          padding: 10px 12px;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: rgba(40, 40, 40, 0.8);
          color: rgb(255, 255, 255);
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .trigger-input:focus {
          border-color: rgba(76, 175, 80, 0.4);
          outline: none;
        }

        .apply-btn {
          padding: 10px 20px;
          border-radius: 8px;
          border: none;
          background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
          color: white;
          font-weight: 600;
          cursor: pointer;
          font-size: 13px;
          white-space: nowrap;
          transition: all 0.2s ease;
        }

        .apply-btn:hover {
          background: linear-gradient(135deg, #45a049 0%, #3d8b40 100%);
          transform: translateY(-1px);
        }

        .words-container {
          background: rgba(40, 40, 40, 0.5);
          border-radius: 8px;
          padding: 12px;
        }

        .words-label {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.5);
          margin-bottom: 10px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .words-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .word-chip {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: rgba(76, 175, 80, 0.15);
          border: 1px solid rgba(76, 175, 80, 0.3);
          border-radius: 16px;
          padding: 5px 10px 5px 12px;
          font-size: 13px;
          color: #4CAF50;
          transition: all 0.2s ease;
        }

        .word-chip:hover {
          background: rgba(76, 175, 80, 0.25);
        }

        .remove-word-btn {
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.5);
          font-size: 18px;
          line-height: 1;
          cursor: pointer;
          padding: 0;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: color 0.2s ease;
        }

        .remove-word-btn:hover {
          color: #f44336;
        }

        .empty-state {
          text-align: center;
          padding: 15px;
          color: rgba(255, 255, 255, 0.3);
          font-size: 13px;
          font-style: italic;
        }
      `}</style>

      {/* Action Triggers (Monitor, Logs, etc.) */}
      {actionTriggers.length > 0 && (
        <div className="triggers-section" style={{ marginTop: '24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#fff', marginBottom: '16px' }}>
            ⚡ Action Triggers (Chat Commands)
          </h2>
          <div className="triggers-grid">
            {actionTriggers.map((trigger, idx) => (
              <div key={idx} className="trigger-card">
                <div className="card-header">
                  <span className="card-icon">🎯</span>
                  <h3 className="card-title">{trigger.intent}</h3>
                </div>
                <div className="word-list">
                  {trigger.triggers && trigger.triggers.map((cmd, i) => (
                    <span key={i} className="word-chip" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3B82F6' }}>
                      "{cmd}"
                    </span>
                  ))}
                </div>
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#aaa' }}>
                  Type: {trigger.type} | Action: {trigger.action}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TriggerManagerTab;
