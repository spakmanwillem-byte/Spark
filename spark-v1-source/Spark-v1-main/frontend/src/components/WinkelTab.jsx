import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const WinkelTab = ({ userData }) => {
  console.log('🟢 WinkelTab MOUNTED', userData);
  
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(false);
  const [wallet, setWallet] = useState(null);
  const [tokenAmount, setTokenAmount] = useState('1');

  useEffect(() => {
    if (userData?.id) {
      loadWallet();
      // Refresh elke 30 seconden (prijs kan veranderen)
      const interval = setInterval(loadWallet, 30000);
      return () => clearInterval(interval);
    }
  }, [userData]);

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

  const handleBuy = async () => {
    const tokens = parseFloat(tokenAmount);
    if (!tokens || tokens <= 0) {
      alert('⚠️ Voer een geldig aantal tokens in');
      return;
    }
    
    const currentPrice = wallet.roar_market.current_price;
    const totalCost = tokens * currentPrice;
    
    // Check if user has enough EUR
    if (wallet.balances.eur < totalCost) {
      alert(`⚠️ Onvoldoende saldo!\n\nNodig: €${totalCost.toFixed(2)}\nBeschikbaar: €${wallet.balances.eur.toFixed(2)}`);
      return;
    }
    
    console.log('🛒 BUY CLICKED', {tokens, price: currentPrice, total: totalCost});
    setBuying(true);
    
    try {
      const payload = {
        user_id: userData.id,
        type: 'buy_roar',
        amount_eur: parseFloat(totalCost.toFixed(2)),
        token_amount: tokens,
        price_per_token: currentPrice,
        description: `Kocht ${tokens} ROAR token(s) @ €${currentPrice.toFixed(2)}`
      };
      
      console.log('📤 POST /api/central/transaction', payload);
      
      const res = await axios.post(`${API}/central/transaction`, payload);
      
      console.log('📥 Response:', res.data);
      
      if (res.data.success) {
        const achievements = res.data.achievements_unlocked || [];
        let msg = `✅ ${res.data.message}\n\n`;
        msg += `💰 Nieuw saldo: €${res.data.new_balances.eur.toFixed(2)}\n`;
        msg += `💎 ROAR tokens: ${res.data.new_balances.roar}\n`;
        msg += `📊 Token prijs: €${currentPrice.toFixed(2)}`;
        
        if (achievements.length > 0) {
          msg += `\n\n🏆 Achievement: ${achievements.join(', ')}!`;
        }
        
        alert(msg);
        setTokenAmount('1');
        
        console.log('🔄 Reloading wallet...');
        await loadWallet();
        console.log('✅ Wallet reloaded');
      }
      
    } catch (err) {
      console.error('❌ Buy error:', err);
      alert('❌ Error: ' + (err.response?.data?.detail || err.message));
    } finally {
      setBuying(false);
    }
  };

  if (loading) {
    return (
      <div style={{padding: '40px', textAlign: 'center', color: 'white'}}>
        ⏳ Laden...
      </div>
    );
  }

  if (!wallet) {
    return (
      <div style={{padding: '40px', textAlign: 'center', color: 'red'}}>
        ❌ Wallet niet geladen
      </div>
    );
  }

  const currentPrice = wallet.roar_market.current_price;
  const totalCost = parseFloat(tokenAmount || 0) * currentPrice;
  const canAfford = wallet.balances.eur >= totalCost;

  return (
    <div style={{ padding: '40px', background: '#1a1a1a', minHeight: '100vh' }}>
      <h1 style={{ color: 'white', marginBottom: '30px' }}>🛒 ROAR Token Winkel</h1>
      
      {/* 💎 Jouw Positie */}
      <div style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '24px', 
        borderRadius: '12px',
        marginBottom: '20px',
        maxWidth: '600px'
      }}>
        <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>
          💎 Jouw Positie
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
          <div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px', marginBottom: '4px' }}>
              Jouw tokens
            </div>
            <div style={{ color: 'white', fontSize: '24px', fontWeight: 'bold' }}>
              {wallet.balances.roar.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px', marginBottom: '4px' }}>
              Prijs per token
            </div>
            <div style={{ color: 'white', fontSize: '24px', fontWeight: 'bold' }}>
              €{currentPrice.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px', marginBottom: '4px' }}>
              Jouw waarde
            </div>
            <div style={{ color: 'white', fontSize: '24px', fontWeight: 'bold' }}>
              €{(wallet.balances.roar * currentPrice).toFixed(2)}
            </div>
          </div>
        </div>
      </div>
      
      {/* 📊 Markt */}
      <div style={{ 
        background: '#1e293b',
        padding: '24px', 
        borderRadius: '12px',
        marginBottom: '30px',
        maxWidth: '600px',
        border: '1px solid #334155'
      }}>
        <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>
          📊 Markt
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '4px' }}>
              Tokens in omloop
            </div>
            <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
              {wallet.roar_market.total_user_tokens}
            </div>
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '4px' }}>
              Beschikbaar saldo
            </div>
            <div style={{ color: '#4ade80', fontSize: '20px', fontWeight: 'bold' }}>
              €{wallet.balances.eur.toFixed(2)}
            </div>
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '4px' }}>
              Spark Core
            </div>
            <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
              €{wallet.roar_market.spark_core_value.toFixed(2)}
            </div>
          </div>
        </div>
      </div>
      
      {/* Buy Section */}
      <div style={{ 
        background: '#2a2a2a', 
        padding: '30px', 
        borderRadius: '10px', 
        maxWidth: '600px',
        border: '2px solid #4CAF50'
      }}>
        <h3 style={{ color: 'white', marginBottom: '20px' }}>💎 Koop ROAR Tokens</h3>
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ color: '#aaa', fontSize: '14px', display: 'block', marginBottom: '8px' }}>
            Aantal tokens:
          </label>
          <input
            type="number"
            min="0.01"
            step="0.01"
            value={tokenAmount}
            onChange={(e) => setTokenAmount(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '18px',
              background: '#1a1a1a',
              border: '1px solid #444',
              borderRadius: '6px',
              color: 'white'
            }}
          />
        </div>
        
        <div style={{ 
          background: '#1a1a1a', 
          padding: '15px', 
          borderRadius: '6px',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: '#aaa' }}>Prijs per token:</span>
            <span style={{ color: 'white', fontWeight: 'bold' }}>€{currentPrice.toFixed(2)}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: '#aaa' }}>Aantal:</span>
            <span style={{ color: 'white' }}>{parseFloat(tokenAmount || 0).toFixed(2)}</span>
          </div>
          <div style={{ borderTop: '1px solid #444', paddingTop: '8px', marginTop: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'white', fontWeight: 'bold' }}>Totaal:</span>
              <span style={{ 
                color: canAfford ? '#4CAF50' : '#f44336', 
                fontSize: '20px', 
                fontWeight: 'bold' 
              }}>
                €{totalCost.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
        
        {!canAfford && tokenAmount > 0 && (
          <div style={{ 
            background: '#5d1a1a', 
            border: '1px solid #f44336',
            padding: '10px', 
            borderRadius: '6px',
            marginBottom: '15px',
            color: '#ffcdd2',
            fontSize: '13px'
          }}>
            ⚠️ Onvoldoende saldo. Nodig: €{totalCost.toFixed(2)}, beschikbaar: €{wallet.balances.eur.toFixed(2)}
          </div>
        )}
        
        <button
          onClick={handleBuy}
          disabled={buying || !canAfford || !tokenAmount || parseFloat(tokenAmount) <= 0}
          style={{
            width: '100%',
            padding: '16px',
            fontSize: '18px',
            background: (buying || !canAfford) ? '#666' : '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: (buying || !canAfford) ? 'not-allowed' : 'pointer',
            fontWeight: 'bold'
          }}
        >
          {buying ? '⏳ Verwerken...' : `🔥 KOOP ${parseFloat(tokenAmount || 0).toFixed(2)} TOKEN(S)`}
        </button>
        
        <div style={{ 
          marginTop: '15px',
          padding: '12px',
          background: '#1a1a1a',
          borderRadius: '6px',
          fontSize: '12px',
          color: '#888'
        }}>
          💡 Token prijs is dynamisch en gebaseerd op de actuele Bitvavo Spark Core waarde.
          Prijs wordt elke 30 seconden ververst.
        </div>
      </div>
    </div>
  );
};

export default WinkelTab;
