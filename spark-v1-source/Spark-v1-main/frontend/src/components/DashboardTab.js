import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './DashboardTab.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function DashboardTab({ userId, userName }) {
  const [loading, setLoading] = useState(true);
  const [showBitvavoSetup, setShowBitvavoSetup] = useState(false);
  const [bitvavoApiKey, setBitvavoApiKey] = useState('');
  const [bitvavoApiSecret, setBitvavoApiSecret] = useState('');
  const [bitvavoSaving, setBitvavoSaving] = useState(false);
  const [bitvavoTesting, setBitvavoTesting] = useState(false);
  const [bitvavoTestResult, setBitvavoTestResult] = useState(null);
  
  const [dashboardData, setDashboardData] = useState({
    financials: { expenses: 0, income: 0, balance: 0, expenseCount: 0, incomeCount: 0, crypto: 0, cryptoEnabled: false }
  });

  useEffect(() => {
    if (userId) {
      loadDashboardData();
    }
  }, [userId]);

  const loadDashboardData = async () => {
    setLoading(true);
    
    try {
      // Parallel requests voor alle data
      const [
        expensesRes,
        incomeRes,
        bitvavoRes
      ] = await Promise.all([
        axios.get(`${API}/expenses/summary`, { params: { user_id: userId } }).catch(() => ({ data: { success: false } })),
        axios.get(`${API}/income/summary`, { params: { user_id: userId } }).catch(() => ({ data: { success: false } })),
        axios.get(`${API}/bitvavo/balance`, { params: { user_id: userId } }).catch(() => ({ data: { success: false } }))
      ]);

      // Process expenses
      let totalExpenses = 0;
      let expenseCount = 0;
      if (expensesRes.data.success) {
        totalExpenses = expensesRes.data.total_amount || 0;
        expenseCount = expensesRes.data.total_count || 0;
      }

      // Process income
      let totalIncome = 0;
      let incomeCount = 0;
      if (incomeRes.data.success) {
        totalIncome = incomeRes.data.total_amount || 0;
        incomeCount = incomeRes.data.total_count || 0;
      }

      // Process Bitvavo
      let bitvavoBalance = 0;
      let bitvavoEnabled = false;
      if (bitvavoRes.data.success) {
        bitvavoBalance = bitvavoRes.data.total_eur || 0;
        bitvavoEnabled = true;
      }

      setDashboardData({
        financials: {
          expenses: totalExpenses,
          income: totalIncome,
          balance: totalIncome - totalExpenses,
          expenseCount,
          incomeCount,
          crypto: bitvavoBalance,
          cryptoEnabled: bitvavoEnabled
        }
      });

      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setLoading(false);
    }
  };

  const handleBitvavoSave = async () => {
    if (!bitvavoApiKey || !bitvavoApiSecret) {
      alert('Vul beide velden in');
      return;
    }

    setBitvavoSaving(true);
    setBitvavoTestResult(null);

    try {
      // Save credentials
      const saveRes = await axios.post(
        `${API}/bitvavo/credentials`,
        {
          api_key: bitvavoApiKey,
          api_secret: bitvavoApiSecret
        },
        { params: { user_id: userId } }
      );

      if (!saveRes.data.success) {
        alert(`❌ ${saveRes.data.message}`);
        setBitvavoSaving(false);
        return;
      }

      // Test connection
      setBitvavoTesting(true);
      const testRes = await axios.post(
        `${API}/bitvavo/test`,
        {},
        { params: { user_id: userId } }
      );

      setBitvavoTestResult(testRes.data);
      setBitvavoTesting(false);

      if (testRes.data.success) {
        // Reload dashboard data
        setTimeout(() => {
          loadDashboardData();
          setShowBitvavoSetup(false);
          setBitvavoApiKey('');
          setBitvavoApiSecret('');
        }, 2000);
      }

    } catch (error) {
      alert('❌ Error saving credentials');
      console.error(error);
    }

    setBitvavoSaving(false);
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading-spinner">Laden...</div>
      </div>
    );
  }

  const { financials } = dashboardData;

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>📊 Dashboard</h1>
        <p className="welcome-text">Welkom terug, {userName || 'User'}!</p>
      </div>

      <div className="dashboard-grid">
        {/* Financieel Overzicht */}
        <div className="dashboard-card financial-card">
          <div className="card-header">
            <h3>💰 Financieel Overzicht</h3>
            <span className="card-badge">{new Date().toLocaleDateString('nl-NL', { month: 'long', year: 'numeric' })}</span>
          </div>
          <div className="card-body">
            <div className="stat-row">
              <div className="stat-item income">
                <span className="stat-label">💚 Inkomsten</span>
                <span className="stat-value">€{financials.income.toFixed(2)}</span>
                <span className="stat-count">{financials.incomeCount} entries</span>
              </div>
              <div className="stat-item expense">
                <span className="stat-label">💸 Uitgaven</span>
                <span className="stat-value">€{financials.expenses.toFixed(2)}</span>
                <span className="stat-count">{financials.expenseCount} entries</span>
              </div>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-balance">
              <span className="balance-label">Saldo (excl. crypto)</span>
              <span className={`balance-value ${financials.balance >= 0 ? 'positive' : 'negative'}`}>
                €{financials.balance.toFixed(2)}
              </span>
            </div>

            {financials.cryptoEnabled && (
              <>
                <div className="stat-divider"></div>
                <div className="crypto-balance">
                  <div className="crypto-label">
                    <span>₿ Bitvavo Wallet</span>
                    <a href="#settings" className="crypto-link">→ Settings</a>
                  </div>
                  <span className="crypto-value">€{financials.crypto.toFixed(2)}</span>
                </div>
                <div className="stat-divider"></div>
                <div className="total-wealth">
                  <span className="wealth-label">Totaal Vermogen</span>
                  <span className="wealth-value">
                    €{(financials.balance + financials.crypto).toFixed(2)}
                  </span>
                </div>
              </>
            )}

            {!financials.cryptoEnabled && (
              <>
                <div className="stat-divider"></div>
                <div className="crypto-setup">
                  {!showBitvavoSetup ? (
                    <>
                      <div className="crypto-setup-header">
                        <span className="crypto-setup-icon">₿</span>
                        <span className="crypto-setup-title">Bitvavo Koppelen</span>
                      </div>
                      <p className="crypto-setup-text">
                        Koppel je Bitvavo account om je crypto vermogen te zien
                      </p>
                      <button 
                        className="crypto-setup-btn"
                        onClick={() => setShowBitvavoSetup(true)}
                      >
                        🔗 API Key Invoeren
                      </button>
                    </>
                  ) : (
                    <div className="bitvavo-form">
                      <h4 className="bitvavo-form-title">Bitvavo API Credentials</h4>
                      <p className="bitvavo-form-hint">
                        Maak een API key aan op{' '}
                        <a href="https://account.bitvavo.com/user/api" target="_blank" rel="noopener noreferrer">
                          Bitvavo
                        </a>
                        {' '}met <strong>View</strong> permissions (read-only).
                      </p>
                      
                      <div className="form-group">
                        <label>API Key</label>
                        <input
                          type="text"
                          value={bitvavoApiKey}
                          onChange={(e) => setBitvavoApiKey(e.target.value)}
                          placeholder="Plak je API key hier"
                          className="bitvavo-input"
                        />
                      </div>

                      <div className="form-group">
                        <label>API Secret</label>
                        <input
                          type="password"
                          value={bitvavoApiSecret}
                          onChange={(e) => setBitvavoApiSecret(e.target.value)}
                          placeholder="Plak je API secret hier"
                          className="bitvavo-input"
                        />
                      </div>

                      {bitvavoTestResult && (
                        <div className={`test-result ${bitvavoTestResult.success ? 'success' : 'error'}`}>
                          <strong>{bitvavoTestResult.success ? '✅ Verbonden!' : '❌ Fout'}</strong>
                          <br />
                          {bitvavoTestResult.message}
                        </div>
                      )}

                      <div className="bitvavo-form-actions">
                        <button
                          onClick={handleBitvavoSave}
                          disabled={bitvavoSaving || bitvavoTesting || !bitvavoApiKey || !bitvavoApiSecret}
                          className="btn-save"
                        >
                          {bitvavoSaving ? 'Opslaan...' : bitvavoTesting ? 'Testen...' : '💾 Opslaan & Testen'}
                        </button>
                        <button
                          onClick={() => {
                            setShowBitvavoSetup(false);
                            setBitvavoApiKey('');
                            setBitvavoApiSecret('');
                            setBitvavoTestResult(null);
                          }}
                          className="btn-cancel"
                        >
                          Annuleren
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h3>⚡ Snelle Acties</h3>
        <div className="actions-grid">
          <button className="action-btn" onClick={() => window.location.hash = '#uitgaven'}>
            💸 Voeg Uitgave Toe
          </button>
          <button className="action-btn" onClick={() => window.location.hash = '#inkomsten'}>
            💰 Voeg Inkomsten Toe
          </button>
        </div>
      </div>
    </div>
  );
}

export default DashboardTab;
