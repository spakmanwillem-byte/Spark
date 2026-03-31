import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LogsTab = ({ userData }) => {
  const [logs, setLogs] = useState([]);
  const [bugReport, setBugReport] = useState({ title: '', description: '', severity: 'medium' });
  const [filter, setFilter] = useState('all'); // all, error, warning, info
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    try {
      const response = await axios.get(`${API}/logs`);
      setLogs(response.data.logs || []);
    } catch (error) {
      console.error('Error loading logs:', error);
    }
  };

  const handleSubmitBug = async () => {
    if (!bugReport.title || !bugReport.description) {
      alert('❌ Vul titel en beschrijving in');
      return;
    }

    setIsSubmitting(true);
    try {
      await axios.post(`${API}/bugs/report`, {
        user_id: userData?.id,
        user_name: userData?.naam || 'Anonymous',
        ...bugReport,
        timestamp: new Date().toISOString()
      });
      
      alert('✅ Bug report verstuurd! Bedankt voor je feedback.');
      setBugReport({ title: '', description: '', severity: 'medium' });
      loadLogs(); // Refresh logs
    } catch (error) {
      console.error('Error submitting bug:', error);
      alert('❌ Fout bij versturen bug report');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredLogs = logs.filter(log => {
    if (filter === 'all') return true;
    return log.level === filter;
  });

  const getLevelColor = (level) => {
    switch(level) {
      case 'error': return '#f44336';
      case 'warning': return '#ff9800';
      case 'info': return '#2196F3';
      case 'success': return '#4CAF50';
      default: return '#9E9E9E';
    }
  };

  const getLevelIcon = (level) => {
    switch(level) {
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      case 'success': return '✅';
      default: return '📝';
    }
  };

  return (
    <div style={{ padding: '30px', maxWidth: '1000px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '30px' }}>📊 System Logs & Bug Reporting</h2>

      {/* Bug Report Section */}
      <div className="bug-report-section">
        <h3>🐛 Bug Melden</h3>
        <p style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '14px', marginBottom: '20px' }}>
          Heb je een bug gevonden? Meld het hier zodat we het kunnen oplossen!
        </p>

        <div className="bug-form">
          <div className="form-group">
            <label>Titel</label>
            <input
              type="text"
              value={bugReport.title}
              onChange={(e) => setBugReport({...bugReport, title: e.target.value})}
              placeholder="Korte beschrijving van de bug"
              className="bug-input"
            />
          </div>

          <div className="form-group">
            <label>Beschrijving</label>
            <textarea
              value={bugReport.description}
              onChange={(e) => setBugReport({...bugReport, description: e.target.value})}
              placeholder="Wat ging er mis? Wat deed je toen de bug optrad?"
              className="bug-textarea"
              rows={5}
            />
          </div>

          <div className="form-group">
            <label>Ernst</label>
            <select
              value={bugReport.severity}
              onChange={(e) => setBugReport({...bugReport, severity: e.target.value})}
              className="bug-select"
            >
              <option value="low">🟢 Low - Kleine UI bug</option>
              <option value="medium">🟡 Medium - Functionaliteit werkt niet goed</option>
              <option value="high">🟠 High - Belangrijke feature werkt niet</option>
              <option value="critical">🔴 Critical - Applicatie crasht of data verlies</option>
            </select>
          </div>

          <button
            onClick={handleSubmitBug}
            disabled={isSubmitting}
            style={{
              padding: '12px 30px',
              borderRadius: '8px',
              border: 'none',
              background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
              color: 'white',
              fontWeight: 600,
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              opacity: isSubmitting ? 0.6 : 1,
            }}
          >
            {isSubmitting ? '⏳ Versturen...' : '📤 Bug Melden'}
          </button>
        </div>
      </div>

      {/* Logs Section */}
      <div className="logs-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>📋 System Logs</h3>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setFilter('all')}
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            >
              Alle
            </button>
            <button
              onClick={() => setFilter('error')}
              className={`filter-btn ${filter === 'error' ? 'active' : ''}`}
            >
              ❌ Errors
            </button>
            <button
              onClick={() => setFilter('warning')}
              className={`filter-btn ${filter === 'warning' ? 'active' : ''}`}
            >
              ⚠️ Warnings
            </button>
            <button
              onClick={() => setFilter('info')}
              className={`filter-btn ${filter === 'info' ? 'active' : ''}`}
            >
              ℹ️ Info
            </button>
          </div>
        </div>

        <div className="logs-container">
          {filteredLogs.length > 0 ? (
            filteredLogs.map((log, index) => (
              <div
                key={index}
                className="log-item"
                style={{ borderLeft: `3px solid ${getLevelColor(log.level)}` }}
              >
                <div className="log-header">
                  <span className="log-icon">{getLevelIcon(log.level)}</span>
                  <span className="log-level" style={{ color: getLevelColor(log.level) }}>
                    {log.level.toUpperCase()}
                  </span>
                  <span className="log-time">{log.timestamp}</span>
                </div>
                <div className="log-message">{log.message}</div>
                {log.details && (
                  <div className="log-details">{log.details}</div>
                )}
              </div>
            ))
          ) : (
            <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(255, 255, 255, 0.5)' }}>
              📭 Geen logs beschikbaar
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .bug-report-section {
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 25px;
          margin-bottom: 30px;
        }

        .bug-report-section h3 {
          margin: 0 0 10px 0;
        }

        .bug-form {
          margin-top: 20px;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.7);
          margin-bottom: 8px;
          font-weight: 600;
        }

        .bug-input, .bug-textarea, .bug-select {
          width: 100%;
          padding: 12px;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: rgba(40, 40, 40, 0.8);
          color: rgb(255, 255, 255);
          font-size: 14px;
          font-family: inherit;
        }

        .bug-input:focus, .bug-textarea:focus, .bug-select:focus {
          border-color: rgba(76, 175, 80, 0.4);
          outline: none;
        }

        .logs-section {
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 25px;
        }

        .filter-btn {
          padding: 8px 16px;
          border-radius: 6px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: transparent;
          color: rgb(200, 200, 200);
          cursor: pointer;
          font-size: 13px;
          transition: all 0.2s ease;
        }

        .filter-btn:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .filter-btn.active {
          background: rgba(76, 175, 80, 0.2);
          border-color: rgba(76, 175, 80, 0.4);
          color: #4CAF50;
        }

        .logs-container {
          max-height: 600px;
          overflow-y: auto;
          margin-top: 20px;
        }

        .log-item {
          background: rgba(40, 40, 40, 0.6);
          border-radius: 8px;
          padding: 15px;
          margin-bottom: 10px;
        }

        .log-header {
          display: flex;
          gap: 12px;
          align-items: center;
          margin-bottom: 8px;
          font-size: 13px;
        }

        .log-icon {
          font-size: 16px;
        }

        .log-level {
          font-weight: 600;
        }

        .log-time {
          margin-left: auto;
          color: rgba(255, 255, 255, 0.4);
          font-size: 12px;
        }

        .log-message {
          color: rgb(230, 230, 230);
          font-size: 14px;
          line-height: 1.5;
        }

        .log-details {
          margin-top: 8px;
          padding: 10px;
          background: rgba(0, 0, 0, 0.3);
          border-radius: 6px;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.6);
          font-family: monospace;
        }
      `}</style>
    </div>
  );
};

export default LogsTab;
