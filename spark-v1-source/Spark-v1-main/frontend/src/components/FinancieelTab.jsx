import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AchievementsTab from './AchievementsTab';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FinancieelTab = ({ userData }) => {
  const [activeSection, setActiveSection] = useState('wallet'); // 'wallet', 'winkel', or 'achievements'
  const [loading, setLoading] = useState(true);
  
  // Wallet state
  const [walletBalance, setWalletBalance] = useState(0);
  const [roarBalance, setRoarBalance] = useState(0);
  const [roarValue, setRoarValue] = useState(0);
  
  // ROAR market state
  const [roarPrice, setRoarPrice] = useState(5.08);
  const [roarStats, setRoarStats] = useState(null);
  
  // Buy form
  const [buyAmount, setBuyAmount] = useState('');
  const [buyMode, setBuyMode] = useState('eur'); // 'eur' or 'roar'
  const [buying, setBuying] = useState(false);

  useEffect(() => {
    if (userData?.id) {
      loadData();
      // Refresh every 30 seconds
      const interval = setInterval(loadData, 30000);
      return () => clearInterval(interval);
    }
  }, [userData]);

  const loadData = async () => {
    console.log('🔄 [FinancieelTab] Loading data for user:', userData?.id);
    try {
      setLoading(true);
      
      // CENTRALE WALLET API
      const response = await axios.get(`${API}/central/wallet/${userData.id}`);
      console.log('✅ [FinancieelTab] Wallet data loaded:', response.data);
      
      if (response.data.success) {
        setWalletBalance(response.data.balances.eur);
        setRoarBalance(response.data.balances.roar);
        setRoarValue(response.data.balances.roar_value_eur);
        setRoarPrice(response.data.roar_market.current_price);
        
        console.log('💰 [FinancieelTab] Balances set:', {
          eur: response.data.balances.eur,
          roar: response.data.balances.roar
        });
        
        // Stats
        setRoarStats({
          current_price: response.data.roar_market.current_price,
          total_supply: response.data.roar_market.total_supply,
          circulating_supply: response.data.roar_market.circulating,
          market_cap: response.data.roar_market.circulating * response.data.roar_market.current_price
        });
      }
      
    } catch (error) {
      console.error('❌ [FinancieelTab] Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateROAR = (eur) => {
    return (parseFloat(eur) / roarPrice).toFixed(6);
  };

  const calculateEUR = (roar) => {
    return (parseFloat(roar) * roarPrice).toFixed(2);
  };

  const handleBuy = async () => {
    console.log('🛒 [FinancieelTab] Buy button clicked');
    console.log('📝 [FinancieelTab] Buy amount:', buyAmount, 'Mode:', buyMode);
    
    if (!buyAmount || parseFloat(buyAmount) <= 0) {
      console.warn('⚠️ [FinancieelTab] Invalid amount');
      alert('⚠️ Voer een geldig bedrag in');
      return;
    }

    setBuying(true);
    try {
      // Bereken bedragen
      let amountEur, tokenAmount;
      if (buyMode === 'eur') {
        amountEur = parseFloat(buyAmount);
        tokenAmount = amountEur / roarPrice;
      } else {
        tokenAmount = parseFloat(buyAmount);
        amountEur = tokenAmount * roarPrice;
      }

      // POST naar centrale transaction
      const payload = {
        user_id: userData.id,
        type: 'buy_roar',
        amount_eur: parseFloat(amountEur.toFixed(2)),
        token_amount: parseFloat(tokenAmount.toFixed(6)),
        price_per_token: roarPrice,
        description: `Kocht ${tokenAmount.toFixed(2)} ROAR tokens`
      };

      console.log('📤 [FinancieelTab] Sending POST to /api/central/transaction');
      console.log('📦 [FinancieelTab] Payload:', payload);
      
      const response = await axios.post(`${API}/central/transaction`, payload);
      
      console.log('📥 [FinancieelTab] Response received:', response.data);
      
      if (response.data.success) {
        const achievements = response.data.achievements_unlocked || [];
        let msg = `✅ ${response.data.message}\n\n`;
        msg += `💰 Nieuw saldo: €${response.data.new_balances.eur}\n`;
        msg += `💎 ROAR tokens: ${response.data.new_balances.roar}`;
        
        if (achievements.length > 0) {
          msg += `\n\n🏆 Achievement unlocked: ${achievements.join(', ')}!`;
          console.log('🏆 [FinancieelTab] Achievements unlocked:', achievements);
        }
        
        alert(msg);
        setBuyAmount('');
        
        console.log('🔄 [FinancieelTab] Reloading wallet data...');
        await loadData();
        console.log('✅ [FinancieelTab] Wallet reloaded');
      }
    } catch (error) {
      console.error('❌ [FinancieelTab] Buy error:', error);
      console.error('❌ [FinancieelTab] Error response:', error.response?.data);
      const errorMsg = error.response?.data?.detail || error.message;
      alert(`❌ Aankoop mislukt: ${errorMsg}`);
    } finally {
      setBuying(false);
    }
  };

  const handleDepositRequest = async () => {
    const amount = prompt('Hoeveel wil je storten? (min. €10)');
    if (!amount || parseFloat(amount) < 10) return;

    try {
      const response = await axios.post(`${API}/central/transaction`, {
        user_id: userData.id,
        type: 'deposit',
        amount_eur: parseFloat(amount),
        description: `Storting van €${amount}`
      });

      if (response.data.success) {
        alert(`✅ Storting van €${amount} succesvol toegevoegd!`);
        loadData();
      }
    } catch (error) {
      alert('❌ Fout bij storting');
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center">
        <div className="text-5xl mb-4">⏳</div>
        <p className="text-gray-400">Laden...</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 border border-green-500/30 rounded-lg p-6">
        <h2 className="text-3xl font-bold text-white mb-2">💰 Financieel</h2>
        <p className="text-gray-300">Beheer je wallet en koop ROAR tokens</p>
      </div>

      {/* Section Toggle */}
      <div className="flex gap-3">
        <button
          onClick={() => setActiveSection('wallet')}
          className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-colors ${
            activeSection === 'wallet'
              ? 'bg-blue-500 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          💳 Mijn Wallet
        </button>
        <button
          onClick={() => setActiveSection('winkel')}
          className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-colors ${
            activeSection === 'winkel'
              ? 'bg-purple-500 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          🛒 Winkel
        </button>
        <button
          onClick={() => setActiveSection('achievements')}
          className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-colors ${
            activeSection === 'achievements'
              ? 'bg-yellow-500 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          🏆 Achievements
        </button>
      </div>

      {/* WALLET SECTION */}
      {activeSection === 'wallet' && (
        <div className="space-y-6">
          {/* Balance Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* EUR Balance */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
              <div className="flex items-center justify-between mb-3">
                <div className="text-gray-400 text-sm">💶 EUR Saldo</div>
                <button
                  onClick={handleDepositRequest}
                  className="px-3 py-1 bg-green-500/20 text-green-300 rounded text-sm hover:bg-green-500/30"
                >
                  ➕ Storten
                </button>
              </div>
              <div className="text-4xl font-bold text-white">
                €{walletBalance.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500 mt-2">
                user_id: {userData.id}
              </div>
            </div>

            {/* ROAR Balance */}
            <div className="bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30 rounded-lg p-6">
              <div className="text-gray-300 text-sm mb-3">💎 ROAR Tokens</div>
              <div className="text-4xl font-bold text-white mb-1">
                {roarBalance.toFixed(6)} <span className="text-lg text-gray-400">ROAR</span>
              </div>
              <div className="text-sm text-gray-400">
                ≈ €{roarValue.toFixed(2)} <span className="text-xs">(@ €{roarPrice})</span>
              </div>
            </div>
          </div>

          {/* Deposit Instructions */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h3 className="text-xl font-bold text-white mb-4">📥 Geld Storten</h3>
            <div className="space-y-3 text-sm text-gray-300">
              <p>
                <strong className="text-white">Stap 1:</strong> Klik op "➕ Storten" en voer bedrag in
              </p>
              <p>
                <strong className="text-white">Stap 2:</strong> Maak overschrijving naar opgegeven IBAN met referentie
              </p>
              <p>
                <strong className="text-white">Stap 3:</strong> Na ontvangst wordt je wallet automatisch gecrediteerd
              </p>
              <p className="text-xs text-gray-500 mt-4">
                💡 Geld komt op Willem's zakelijke rekening en wordt daarna overgezet naar Bitvavo voor trading
              </p>
            </div>
          </div>
        </div>
      )}

      {/* WINKEL SECTION */}
      {activeSection === 'winkel' && (
        <div className="space-y-6">
          {/* ROAR Stats Banner */}
          <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-4xl">💎</span>
              <div>
                <div className="text-2xl font-bold text-white">ROAR Token</div>
                <div className="text-sm text-gray-400">Dynamic Pricing • Gekoppeld aan Trading Potjes</div>
              </div>
            </div>
            
            {roarStats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-400 mb-1">Current Price</div>
                  <div className="text-xl font-bold text-green-400">€{roarStats.current_price}</div>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-400 mb-1">Total Supply</div>
                  <div className="text-xl font-bold text-white">
                    {roarStats.total_supply.toLocaleString()}
                  </div>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-400 mb-1">Circulating</div>
                  <div className="text-xl font-bold text-blue-400">
                    {roarStats.circulating_supply.toLocaleString()}
                  </div>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-400 mb-1">Market Cap</div>
                  <div className="text-xl font-bold text-purple-400">
                    €{roarStats.market_cap.toLocaleString()}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ROAR Product Card */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <h3 className="text-2xl font-bold text-white mb-4">🛒 Koop ROAR Tokens</h3>
            
            {/* Mode Toggle */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setBuyMode('eur')}
                className={`flex-1 px-4 py-2 rounded-lg font-medium ${
                  buyMode === 'eur'
                    ? 'bg-green-500 text-white'
                    : 'bg-slate-700 text-gray-300'
                }`}
              >
                💶 Betaal in EUR
              </button>
              <button
                onClick={() => setBuyMode('roar')}
                className={`flex-1 px-4 py-2 rounded-lg font-medium ${
                  buyMode === 'roar'
                    ? 'bg-purple-500 text-white'
                    : 'bg-slate-700 text-gray-300'
                }`}
              >
                💎 Koop ROAR
              </button>
            </div>

            {/* Input */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  {buyMode === 'eur' ? 'Bedrag in EUR' : 'Aantal ROAR'}
                </label>
                <input
                  type="number"
                  step={buyMode === 'eur' ? '0.01' : '0.000001'}
                  value={buyAmount}
                  onChange={(e) => setBuyAmount(e.target.value)}
                  placeholder={buyMode === 'eur' ? '0.00' : '0.000000'}
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white text-lg"
                />
              </div>

              {/* Calculator */}
              {buyAmount && parseFloat(buyAmount) > 0 && (
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-gray-300">
                      {buyMode === 'eur' ? (
                        <>Je krijgt: <strong className="text-white">{calculateROAR(buyAmount)} ROAR</strong></>
                      ) : (
                        <>Je betaalt: <strong className="text-white">€{calculateEUR(buyAmount)}</strong></>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">@ €{roarPrice}/ROAR</div>
                  </div>
                </div>
              )}

              {/* Wallet Check */}
              {buyAmount && parseFloat(buyAmount) > 0 && buyMode === 'eur' && parseFloat(buyAmount) > walletBalance && (
                <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3 text-sm text-red-300">
                  ⚠️ Onvoldoende saldo. Je hebt €{walletBalance.toFixed(2)}, maar probeert €{buyAmount} te gebruiken.
                </div>
              )}

              {/* Buy Button */}
              <button
                onClick={handleBuy}
                disabled={buying || !buyAmount || parseFloat(buyAmount) <= 0 || (buyMode === 'eur' && parseFloat(buyAmount) > walletBalance)}
                className="w-full px-6 py-4 bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 disabled:from-gray-600 disabled:to-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-bold text-lg"
              >
                {buying ? '⏳ Verwerken...' : '💎 Koop ROAR Tokens'}
              </button>
            </div>

            {/* Info */}
            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <div className="text-sm text-blue-300 space-y-2">
                <p><strong>💡 Dynamic Pricing:</strong></p>
                <p className="text-xs text-gray-400">
                  De ROAR prijs groeit mee met de trading potjes. Nu €{roarPrice}, groeit naar €10.16 over 10 trades.
                  Als de potjes waarde stijgt, stijgt jouw ROAR ook in waarde!
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ACHIEVEMENTS SECTION */}
      {activeSection === 'achievements' && (
        <AchievementsTab userId={userData?.id} />
      )}
    </div>
  );
};

export default FinancieelTab;
