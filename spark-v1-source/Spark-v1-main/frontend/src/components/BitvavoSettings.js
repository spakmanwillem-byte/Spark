import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './BitvavoSettings.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function BitvavoSettings({ userId }) {
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);
  
  // Trading fees state
  const [takerFee, setTakerFee] = useState(0.25);
  const [makerFee, setMakerFee] = useState(0.15);
  const [accountInfo, setAccountInfo] = useState({
    volume: 242.85,
    nextLevel: 100000
  });

  useEffect(() => {
    loadSettings();
  }, [userId]);

  const loadSettings = async () => {
    try {
      const response = await axios.get(`${API}/trading-settings`, {
        params: { user_id: userId || "user-001" }
      });
      
      if (response.data.success) {
        const { api_key, api_secret, taker_fee, maker_fee, account_info } = response.data.settings;
        
        // Mask API keys
        if (api_key) {
          setApiKey(`${"*".repeat(Math.max(0, api_key.length - 8))}${api_key.slice(-8)}`);
          setSaved(true);
        }
        if (api_secret) {
          setApiSecret(`${"*".repeat(Math.max(0, api_secret.length - 8))}${api_secret.slice(-8)}`);
        }
        
        setTakerFee(taker_fee || 0.25);
        setMakerFee(maker_fee || 0.15);
        
        if (account_info) {
          setAccountInfo(account_info);
        }
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const handleSave = async () => {
    if (!apiKey || !apiSecret) {
      alert('Vul beide velden in');
      return;
    }

    // Validate fees
    if (takerFee < 0.1 || takerFee > 0.5) {
      alert('Taker fee moet tussen 0.10% en 0.50% zijn');
      return;
    }
    if (makerFee < 0.05 || makerFee > 0.3) {
      alert('Maker fee moet tussen 0.05% en 0.30% zijn');
      return;
    }

    setSaving(true);
    try {
      // Save via new settings endpoint
      const payload = {
        user_id: userId || "user-001",
        taker_fee: takerFee,
        maker_fee: makerFee
      };
      
      // Only include API keys if they were modified (not masked)
      if (apiKey && !apiKey.includes("*")) {
        payload.api_key = apiKey;
      }
      if (apiSecret && !apiSecret.includes("*")) {
        payload.api_secret = apiSecret;
      }
      
      const response = await axios.post(`${API}/trading-settings/update`, payload);

      if (response.data.success) {
        setSaved(true);
        alert('✅ Instellingen opgeslagen!');
        // Refresh to get masked keys again
        setTimeout(() => loadSettings(), 1500);
      } else {
        alert(`❌ ${response.data.message}`);
      }
    } catch (error) {
      alert('❌ Error saving credentials');
      console.error(error);
    }
    setSaving(false);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const response = await axios.post(`${API}/trading-settings/test-connection`, {
        user_id: userId || "user-001"
      });

      setTestResult(response.data);
    } catch (error) {
      setTestResult({
        success: false,
        message: 'Connection failed'
      });
    }
    setTesting(false);
  };

  return (
    <div className="bitvavo-settings">
      <h3>🔐 Bitvavo API Credentials</h3>
      <p className="info-text">
        Voer je Bitvavo API key en secret in om je wallet te koppelen.
        <br />
        <a href="https://account.bitvavo.com/user/api" target="_blank" rel="noopener noreferrer">
          → API keys aanmaken op Bitvavo
        </a>
      </p>

      <div className="form-group">
        <label>API Key</label>
        <input
          type="text"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Plak hier je API key"
          className="input-field"
        />
      </div>

      <div className="form-group">
        <label>API Secret</label>
        <input
          type="password"
          value={apiSecret}
          onChange={(e) => setApiSecret(e.target.value)}
          placeholder="Plak hier je API secret"
          className="input-field"
        />
      </div>

      <div className="button-group">
        <button 
          onClick={handleSave}
          disabled={saving || !apiKey || !apiSecret}
          className="btn btn-primary"
        >
          {saving ? 'Opslaan...' : '💾 Opslaan'}
        </button>

        {saved && (
          <button 
            onClick={handleTest}
            disabled={testing}
            className="btn btn-secondary"
          >
            {testing ? 'Testen...' : '🔍 Test Verbinding'}
          </button>
        )}
      </div>

      {testResult && (
        <div className={`test-result ${testResult.success ? 'success' : 'error'}`}>
          <strong>{testResult.success ? '✅' : '❌'}</strong> {testResult.message}
        </div>
      )}

      {/* 💰 Handelskosten Section */}
      <div style={{ marginTop: '40px', paddingTop: '30px', borderTop: '2px solid #334155' }}>
        <h3>💰 Handelskosten</h3>
        <p className="info-text">
          Configureer je actuele handelskosten voor accurate winst berekeningen.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
          <div className="form-group">
            <label>Taker Fee (%)</label>
            <input
              type="number"
              step="0.01"
              min="0.10"
              max="0.50"
              value={takerFee}
              onChange={(e) => setTakerFee(parseFloat(e.target.value))}
              className="input-field"
            />
            <small style={{ color: '#64748b', fontSize: '12px', marginTop: '5px', display: 'block' }}>
              Huidig: 0.25% → Volgend niveau: 0.20%
            </small>
          </div>

          <div className="form-group">
            <label>Maker Fee (%)</label>
            <input
              type="number"
              step="0.01"
              min="0.05"
              max="0.30"
              value={makerFee}
              onChange={(e) => setMakerFee(parseFloat(e.target.value))}
              className="input-field"
            />
            <small style={{ color: '#64748b', fontSize: '12px', marginTop: '5px', display: 'block' }}>
              Huidig: 0.15% → Volgend niveau: 0.10%
            </small>
          </div>
        </div>

        <div style={{
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#0f172a',
          borderRadius: '8px',
          border: '1px solid #334155'
        }}>
          <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '10px' }}>
            💡 <strong>Impact op €5 trade:</strong>
          </p>
          <div style={{ color: '#fff', fontSize: '14px', fontFamily: 'monospace', lineHeight: '1.6' }}>
            • Koop fee: €{((takerFee / 100) * 5).toFixed(4)}<br />
            • Verkoop fee: €{((takerFee / 100) * 5).toFixed(4)}<br />
            • Totale fees: €{((takerFee / 100) * 5 * 2).toFixed(4)}<br />
            • Break-even: +{(takerFee * 2).toFixed(2)}%
          </div>
        </div>

        {/* Account Info */}
        <div style={{ marginTop: '20px' }}>
          <h4 style={{ color: '#fff', marginBottom: '15px' }}>📊 Account Informatie</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
            <div style={{
              backgroundColor: '#0f172a',
              padding: '15px',
              borderRadius: '8px',
              border: '1px solid #334155'
            }}>
              <div style={{ color: '#64748b', fontSize: '12px', marginBottom: '5px' }}>
                30-Daags Volume
              </div>
              <div style={{ color: '#fff', fontSize: '20px', fontWeight: 'bold' }}>
                €{accountInfo.volume.toFixed(2)}
              </div>
            </div>

            <div style={{
              backgroundColor: '#0f172a',
              padding: '15px',
              borderRadius: '8px',
              border: '1px solid #334155'
            }}>
              <div style={{ color: '#64748b', fontSize: '12px', marginBottom: '5px' }}>
                Volgend Niveau
              </div>
              <div style={{ color: '#fff', fontSize: '20px', fontWeight: 'bold' }}>
                €{accountInfo.nextLevel.toLocaleString()}
              </div>
            </div>

            <div style={{
              backgroundColor: '#0f172a',
              padding: '15px',
              borderRadius: '8px',
              border: '1px solid #334155'
            }}>
              <div style={{ color: '#64748b', fontSize: '12px', marginBottom: '5px' }}>
                Progress
              </div>
              <div style={{ color: '#10b981', fontSize: '20px', fontWeight: 'bold' }}>
                {((accountInfo.volume / accountInfo.nextLevel) * 100).toFixed(2)}%
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div style={{
            marginTop: '15px',
            width: '100%',
            height: '8px',
            backgroundColor: '#0f172a',
            borderRadius: '4px',
            overflow: 'hidden',
            border: '1px solid #334155'
          }}>
            <div style={{
              width: `${(accountInfo.volume / accountInfo.nextLevel) * 100}%`,
              height: '100%',
              backgroundColor: '#10b981',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>
      </div>

      <div className="security-note">
        <p><strong>⚠️ Veiligheid:</strong></p>
        <ul>
          <li>Start met <strong>read-only</strong> permissions (alleen balance lezen)</li>
          <li>Later kun je trading permissions toevoegen</li>
          <li>Je API secret wordt veilig opgeslagen</li>
          <li>Deel je credentials nooit met anderen</li>
          <li>Handelskosten worden gebruikt voor accurate P&L berekeningen</li>
        </ul>
      </div>
    </div>
  );
}

export default BitvavoSettings;
