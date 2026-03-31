import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const UserWalletTab = ({ userData }) => {
  console.log('🟢 UserWalletTab MOUNTED', userData);
  
  const [loading, setLoading] = useState(true);
  const [wallet, setWallet] = useState(null);

  useEffect(() => {
    loadWallet();
    
    // Auto reload every 10 seconds
    const interval = setInterval(loadWallet, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadWallet = async () => {
    console.log('🔄 Loading wallet...');
    try {
      const res = await axios.get(`${API}/central/wallet/${userData.id}`);
      console.log('✅ Wallet loaded:', res.data);
      setWallet(res.data);
    } catch (err) {
      console.error('❌ Wallet load error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'white' }}>
        ⏳ Laden...
      </div>
    );
  }

  if (!wallet) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'red' }}>
        ❌ Wallet niet geladen
      </div>
    );
  }

  const { balances, achievements, transactions } = wallet;

  return (
    <div style={{ padding: '40px', background: '#1a1a1a', minHeight: '100vh' }}>
      <h1 style={{ color: 'white', marginBottom: '30px' }}>💳 Mijn Wallet</h1>
      
      {/* Saldo */}
      <div style={{ 
        background: '#2a2a2a', 
        padding: '30px', 
        borderRadius: '10px',
        marginBottom: '20px',
        maxWidth: '600px'
      }}>
        <div style={{ color: '#aaa', fontSize: '14px', marginBottom: '10px' }}>
          EUR Saldo
        </div>
        <div style={{ color: 'white', fontSize: '48px', fontWeight: 'bold', marginBottom: '20px' }}>
          €{balances.eur.toFixed(2)}
        </div>
        
        <div style={{ borderTop: '1px solid #444', paddingTop: '20px' }}>
          <div style={{ color: '#aaa', fontSize: '14px', marginBottom: '5px' }}>
            ROAR Tokens
          </div>
          <div style={{ color: '#9C27B0', fontSize: '32px', fontWeight: 'bold' }}>
            {balances.roar.toFixed(2)}
          </div>
          <div style={{ color: '#666', fontSize: '12px', marginTop: '5px' }}>
            Waarde: €{balances.roar_value_eur.toFixed(2)}
          </div>
        </div>
      </div>
      
      {/* Achievements */}
      {achievements?.unlocked?.length > 0 && (
        <div style={{ 
          background: '#2a2a2a', 
          padding: '20px', 
          borderRadius: '10px',
          marginBottom: '20px',
          maxWidth: '600px'
        }}>
          <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold', marginBottom: '10px' }}>
            🏆 Achievements
          </div>
          <div style={{ color: '#FFC107' }}>
            {achievements.unlocked.join(', ')}
          </div>
        </div>
      )}
      
      {/* Recent Transactions */}
      {transactions?.length > 0 && (
        <div style={{ 
          background: '#2a2a2a', 
          padding: '20px', 
          borderRadius: '10px',
          maxWidth: '600px'
        }}>
          <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold', marginBottom: '15px' }}>
            📜 Recent
          </div>
          {transactions.slice(0, 5).map((tx, i) => (
            <div key={i} style={{ 
              background: '#333', 
              padding: '12px', 
              borderRadius: '6px',
              marginBottom: '8px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <div style={{ color: 'white', fontSize: '14px' }}>
                  {tx.type === 'buy_roar' ? '💎 ROAR Koop' : 
                   tx.type === 'deposit' ? '💰 Storting' : tx.type}
                </div>
                <div style={{ color: '#666', fontSize: '12px' }}>
                  {tx.description}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: tx.type === 'deposit' ? '#4CAF50' : 'white', fontWeight: 'bold' }}>
                  €{tx.amount_eur.toFixed(2)}
                </div>
                {tx.token_amount > 0 && (
                  <div style={{ color: '#9C27B0', fontSize: '12px' }}>
                    +{tx.token_amount} ROAR
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      <button 
        onClick={loadWallet}
        style={{
          marginTop: '20px',
          padding: '10px 20px',
          background: '#333',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer'
        }}
      >
        🔄 Refresh
      </button>
    </div>
  );
};

export default UserWalletTab;
