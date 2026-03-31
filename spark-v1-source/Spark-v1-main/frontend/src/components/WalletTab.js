import React, { useState, useEffect } from 'react';
import CoinChartModal from './CoinChartModal';
import EntityDetailModal from './EntityDetailModal';
import { CacheHelper } from '../utils/cacheHelper';

const API = process.env.REACT_APP_BACKEND_URL;

const WalletTab = ({ userData }) => {
  // Entity system state
  const [entities, setEntities] = useState([]);
  const [totalEur, setTotalEur] = useState(0);
  const [userWallet, setUserWallet] = useState(null);
  const [loadingOverview, setLoadingOverview] = useState(true);
  
  // ROAR stats
  const [roarStats, setRoarStats] = useState({
    userBalance: 0,
    sparkBalance: 1000000,
    price: 5.08,
    tradingProgress: 0
  });
  
  // Old state (crypto detail view)
  const [portfolio, setPortfolio] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showSetup, setShowSetup] = useState(false);
  const [selectedCoin, setSelectedCoin] = useState(null);
  const [selectedEntity, setSelectedEntity] = useState(null); // Detail view
  const [showEntityModal, setShowEntityModal] = useState(false); // For non-crypto entities
  
  // Setup form
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [saving, setSaving] = useState(false);

  const API = process.env.REACT_APP_BACKEND_URL;

  // Hardcoded watchlist - Willem's focus coins
  const WATCHLIST = ['BTC', 'ETH', 'ADA', 'SOL', 'BCH'];

  useEffect(() => {
    if (userData) {
      loadWalletOverview();
    }
  }, [userData]);

  useEffect(() => {
    if (userData) {
      loadWalletOverview();
    }
  }, [userData]);

  const loadWalletOverview = async () => {
    try {
      setLoadingOverview(true);
      setTotalEur(null); // Reset naar null (niet 0!) tijdens loading
      
      const response = await fetch(
        `${API}/api/wallet/overview?user_id=${userData.id}`
      );
      const data = await response.json();
      
      if (data.success) {
        setEntities(data.entities || []);
        setTotalEur(data.total_eur || 0); // Pas NA success zetten
        setUserWallet(data.user_wallet || null);
      } else {
        console.error('Failed to load wallet overview:', data.error);
        setTotalEur(0); // Alleen bij error naar 0
      }
      
      // Load ROAR stats
      try {
        const roarRes = await fetch(`${API}/api/roar/balance/${userData.id}`);
        const roarData = await roarRes.json();
        
        const statsRes = await fetch(`${API}/api/roar/stats`);
        const statsData = await statsRes.json();
        
        if (roarData.success && statsData.success) {
          setRoarStats({
            userBalance: roarData.roar_balance || 0,
            sparkBalance: statsData.spark_balance || 1000000,
            price: statsData.current_price || 5.08,
            tradingProgress: 0
          });
        }
      } catch (err) {
        console.error('Error loading ROAR stats:', err);
      }
      
    } catch (err) {
      console.error('Error loading wallet overview:', err);
      setTotalEur(0); // Alleen bij error naar 0
    } finally {
      setLoadingOverview(false);
    }
  };

  const loadPortfolio = async () => {
    const cacheKey = `portfolio_${userData.id}`;
    
    // Stale-while-revalidate: show cache first
    const cached = CacheHelper.get(cacheKey, true);
    if (cached) {
      setPortfolio(cached.data);
      setLoading(false);
      
      if (!cached.isStale) return; // Fresh cache, done
    } else {
      setLoading(true);
    }
    
    try {
      setError(null);
      
      const watchlistParam = WATCHLIST.join(',');
      const response = await fetch(
        `${API}/api/bitvavo/portfolio?user_id=${userData.id}&watchlist=${watchlistParam}`
      );
      const data = await response.json();
      
      if (data.success) {
        setPortfolio(data);
        CacheHelper.set(cacheKey, data, 'portfolio');
      } else {
        setError(data.error || 'Kon portfolio niet laden');
        // Als het een credentials error is, toon setup
        if (data.error && data.error.includes('403')) {
          setShowSetup(true);
        }
      }
    } catch (err) {
      setError('Fout bij ophalen portfolio: ' + err.message);
      if (!cached) setPortfolio(null);
    } finally {
      setLoading(false);
    }
  };

  const loadHistoricalCoins = async () => {
    try {
      // Load on-demand (niet direct bij page load)
      const response = await fetch(
        `${API}/api/bitvavo/history/coins?user_id=${userData.id}`
      );
      const data = await response.json();
      
      if (data.success) {
        setHistoricalData(data);
      }
    } catch (err) {
      console.error('Fout bij ophalen historical data:', err);
    }
  };

  const handleSaveCredentials = async (e) => {
    e.preventDefault();
    
    if (!apiKey || !apiSecret) {
      alert('Vul beide velden in');
      return;
    }

    try {
      setSaving(true);
      
      const response = await fetch(
        `${API}/api/bitvavo/credentials?user_id=${userData.id}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            api_key: apiKey,
            api_secret: apiSecret
          })
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        alert('✅ Credentials opgeslagen!');
        setApiKey('');
        setApiSecret('');
        setShowSetup(false);
        
        // Test connection
        const testResponse = await fetch(
          `${API}/api/bitvavo/test?user_id=${userData.id}`,
          { method: 'POST' }
        );
        const testData = await testResponse.json();
        
        if (testData.success) {
          alert('✅ Connectie getest - werkt!');
          loadPortfolio(); // Reload portfolio
        } else {
          alert('⚠️ Credentials opgeslagen maar connectie test failed: ' + testData.message);
        }
      } else {
        alert('❌ Fout: ' + data.message);
      }
    } catch (err) {
      alert('❌ Fout bij opslaan: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!userData) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-white mb-4">💰 Spark Wallet</h2>
        <p className="text-gray-400">Login om je Spark wallet te bekijken</p>
      </div>
    );
  }

  // New: Entity Dashboard View
  if (!selectedEntity && !showSetup) {
    return (
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-white">💰 Spark Wallet</h2>
            <p className="text-gray-400 text-sm mt-1">
              Kasboeken & Vermogensbeheer
            </p>
          </div>
          <button
            onClick={loadWalletOverview}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
          >
            🔄 Ververs
          </button>
        </div>

        {loadingOverview ? (
          <div className="text-center text-gray-400 py-12">
            Laden...
          </div>
        ) : (
          <>
            {/* ROARR Token Overview */}
            <div className="bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-4xl">💎</span>
                <div>
                  <div className="text-sm text-gray-400">Spark Vermogen (ROARR Tokens)</div>
                  <div className="text-xs text-gray-500 mt-1">Eigendom van Spark AI</div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                <div className="bg-gray-800/50 rounded-lg p-4">
                  <div className="text-xs text-gray-400 mb-1">Totaal Tokens</div>
                  <div className="text-2xl font-bold text-white">
                    {roarStats.sparkBalance.toLocaleString()} <span className="text-sm text-gray-400">ROARR</span>
                  </div>
                  {roarStats.userBalance > 0 && (
                    <div className="text-xs text-blue-400 mt-1">
                      -{roarStats.userBalance} bezit jij
                    </div>
                  )}
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-4">
                  <div className="text-xs text-gray-400 mb-1">Potje Waarde</div>
                  <div className="text-2xl font-bold text-white">
                    €{roarStats.price.toFixed(2)}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">€5,00 start + €{(roarStats.price - 5.00).toFixed(2)} trade winst</div>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-4">
                  <div className="text-xs text-gray-400 mb-1">Totaal Waarde</div>
                  <div className="text-2xl font-bold text-purple-400">
                    €{(roarStats.sparkBalance * roarStats.price).toLocaleString('nl-NL', {minimumFractionDigits: 0, maximumFractionDigits: 0})}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Theoretisch</div>
                </div>
              </div>
              
              <div className="mt-4 text-xs text-gray-500">
                💡 Token waarde groeit mee met trading performance (10 potjes systeem)
              </div>
            </div>

            {/* Kasboeken (Bank Accounts) */}
            <div>
              <h3 className="text-xl font-semibold text-white mb-4">🏦 Kasboeken</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {entities.map((entity) => {
                  const colorMap = {
                    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30',
                    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30',
                    green: 'from-green-500/20 to-green-600/10 border-green-500/30',
                    gray: 'from-gray-500/20 to-gray-600/10 border-gray-500/30'
                  };
                  
                  return (
                    <div
                      key={entity.id}
                      className={`bg-gradient-to-br ${colorMap[entity.color] || colorMap.gray} border rounded-lg p-6 ${entity.error ? 'border-red-500/50' : ''}`}
                    >
                      {/* Kasboek Header */}
                      <div className="flex items-center gap-3 mb-4">
                        <span className="text-4xl">{entity.icon}</span>
                        <div>
                          <h4 className="text-lg font-bold text-white">{entity.name}</h4>
                          <p className="text-xs text-gray-400">
                            {entity.id === 'spark_core' ? 'Bankrekening' : 'Kasboek'}
                          </p>
                        </div>
                      </div>

                      {/* Balance - Simpel */}
                      {entity.error ? (
                        <div className="text-center py-4">
                          <div className="text-red-400 text-sm mb-2">⚠️ Niet bereikbaar</div>
                          <div className="text-xs text-gray-500">{entity.error_message || entity.error}</div>
                        </div>
                      ) : (
                        <div>
                          <div className="text-sm text-gray-400 mb-1">Saldo</div>
                          <div className="text-3xl font-bold text-white">
                            {entity.balance_eur === null ? (
                              <span className="text-gray-500">Laden...</span>
                            ) : (
                              `€${parseFloat(entity.balance_eur || 0).toLocaleString('nl-NL', { 
                                minimumFractionDigits: 2, 
                                maximumFractionDigits: 2 
                              })}`
                            )}
                          </div>
                          
                          {/* Type indicator */}
                          <div className="mt-3 text-xs text-gray-500">
                            {entity.type}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
        
        {/* Entity Detail Modal */}
        {showEntityModal && selectedEntity && selectedEntity.id !== 'spark_core' && (
          <EntityDetailModal 
            entity={selectedEntity}
            userId={userData?.id}
            onClose={() => {
              setShowEntityModal(false);
              setSelectedEntity(null);
            }}
          />
        )}
      </div>
    );
  }

  // Entity Detail View (Spark Core = Crypto detail)
  if (selectedEntity && selectedEntity.id === 'spark_core') {
    // Check if entity has error (Bitvavo not reachable)
    if (selectedEntity.error) {
      return (
        <div className="p-6 space-y-6">
          {/* Back button */}
          <button
            onClick={() => setSelectedEntity(null)}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg mb-4"
          >
            ← Terug naar overzicht
          </button>
          
          <h2 className="text-2xl font-bold text-white">🧠 Spark Core - Crypto Detail</h2>
          
          {/* Error Display */}
          <div className="bg-red-500/20 border-2 border-red-500/50 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <span className="text-4xl">⚠️</span>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-red-400 mb-2">
                  Bitvavo API Niet Bereikbaar
                </h3>
                <p className="text-gray-300 mb-3">
                  {selectedEntity.error}
                </p>
                <div className="text-sm text-gray-400">
                  <p className="mb-2"><strong>Mogelijke oorzaak:</strong></p>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li>IP adres niet toegestaan in Bitvavo API key whitelist</li>
                    <li>API key verlopen of incorrect</li>
                    <li>Bitvavo tijdelijk niet bereikbaar</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }
    
    // Show crypto detail (old WalletTab content)
    // Load portfolio data if not loaded
    if (!portfolio && !loading) {
      loadPortfolio();
      // Historical coins: load on-demand (button click)
    }
    
    // Auto-open BCH chart for learning (Willem's Fase 3 - BCH heeft voorspelbaar patroon)
    if (!selectedCoin && portfolio) {
      setSelectedCoin('BCH');
    }
    
    return (
      <div className="p-6 space-y-6">
        {/* Back button */}
        <button
          onClick={() => setSelectedEntity(null)}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg mb-4"
        >
          ← Terug naar overzicht
        </button>
        
        <h2 className="text-2xl font-bold text-white">🧠 Spark Core - Crypto Detail</h2>
        
        {/* Refresh button */}
        <div className="flex gap-2">
          <button
            onClick={() => loadPortfolio()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
          >
            🔄 Ververs Watchlist
          </button>
          
          {/* Historical coins button verwijderd - voor later */}
        </div>
        
        {loading && <p className="text-gray-400">Laden...</p>}
        {error && <p className="text-red-400">{error}</p>}
        
        {/* Portfolio Display */}
        {portfolio && !loading && (
          <div className="space-y-6">
            {/* Total Value */}
            <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-lg p-6">
              <div className="text-sm text-gray-400 mb-1">Totale Waarde</div>
              <div className="text-4xl font-bold text-white">
                €{portfolio.total_portfolio_value_eur?.toFixed(2) || '0.00'}
              </div>
            </div>

            {/* Balances Table */}
            {portfolio.balances && portfolio.balances.length > 0 && (
              <div>
                <h3 className="text-xl font-semibold text-white mb-4">💼 Jouw Coins</h3>
                <div className="bg-gray-800 rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-700">
                      <tr>
                        <th className="px-4 py-3 text-left text-gray-300 text-sm">Coin</th>
                        <th className="px-4 py-3 text-right text-gray-300 text-sm">Hoeveelheid</th>
                        <th className="px-4 py-3 text-right text-gray-300 text-sm">Waarde (EUR)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {portfolio.balances
                        .filter(b => parseFloat(b.available) > 0)
                        .map((balance, index) => {
                          const value = parseFloat(balance.value_eur || 0);

                          return (
                            <tr 
                              key={index} 
                              className="hover:bg-gray-700/30 cursor-pointer border-t border-gray-700"
                              onClick={() => balance.symbol !== 'EUR' && setSelectedCoin(balance.symbol)}
                            >
                              <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                  <span className="text-white font-medium">{balance.symbol}</span>
                                  {balance.symbol === 'EUR' && (
                                    <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">
                                      FIAT
                                    </span>
                                  )}
                                  {balance.symbol !== 'EUR' && (
                                    <span className="text-xs text-gray-500">📊 klik voor grafiek</span>
                                  )}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-right text-white">
                                {parseFloat(balance.available).toFixed(8)}
                              </td>
                              <td className="px-4 py-3 text-right">
                                <span className="text-white font-semibold">
                                  €{value.toFixed(2)}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Watchlist Prices */}
            {portfolio.watchlist_prices && Object.keys(portfolio.watchlist_prices).length > 0 && (
              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-white">👀 Watchlist Prijzen</h3>
                
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                  {Object.entries(portfolio.watchlist_prices).map(([coin, price]) => {
                    const priceNum = parseFloat(price);
                    
                    return (
                      <div 
                        key={coin} 
                        className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-blue-500 cursor-pointer transition-colors"
                        onClick={() => setSelectedCoin(coin)}
                      >
                        <div className="text-gray-400 text-sm mb-1">{coin}</div>
                        <div className="text-white font-bold">
                          €{priceNum > 0 ? priceNum.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">📈 Klik voor grafiek</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Historical Coins */}
            {historicalData && historicalData.current_coins && historicalData.current_coins.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-white">📊 Alle Coins (Ooit Gehad)</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="flex flex-wrap gap-2">
                    {historicalData.current_coins.map((coin) => (
                      <button
                        key={coin}
                        onClick={() => setSelectedCoin(coin)}
                        className="px-3 py-1 bg-green-600/20 text-green-400 border border-green-500/30 rounded-full text-sm font-medium hover:bg-green-600/30 transition-colors cursor-pointer"
                      >
                        {coin} 📈
                      </button>
                    ))}
                  </div>
                  {historicalData.note && (
                    <p className="text-gray-500 text-xs mt-3">
                      💡 {historicalData.note}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Coin Chart Modal (with REPLAY!) */}
        {selectedCoin && (
          <CoinChartModal 
            coin={selectedCoin} 
            onClose={() => setSelectedCoin(null)} 
          />
        )}
      </div>
    );
  }

  // Setup screen
  if (showSetup) {
    return (
      <div className="p-6 space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-white">💰 Spark Wallet - Setup</h2>
          <p className="text-gray-400 text-sm mt-1">
            Stel je Bitvavo API credentials in
          </p>
        </div>

        <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-4">
          <h3 className="text-white font-semibold mb-2">📝 Hoe krijg ik API credentials?</h3>
          <ol className="text-gray-300 text-sm space-y-1 list-decimal list-inside">
            <li>Ga naar <a href="https://account.bitvavo.com/user/api" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">Bitvavo API pagina</a></li>
            <li>Maak een nieuwe API key aan</li>
            <li>Zet permissions op <strong>Read-only</strong> (veilig!)</li>
            <li>Kopieer je API Key en Secret</li>
            <li>Plak ze hieronder</li>
          </ol>
        </div>

        <form onSubmit={handleSaveCredentials} className="bg-gray-800 rounded-lg p-6 space-y-4">
          <div>
            <label className="block text-gray-300 text-sm mb-2">API Key</label>
            <input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Plak je API key hier"
              className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm mb-2">API Secret</label>
            <input
              type="password"
              value={apiSecret}
              onChange={(e) => setApiSecret(e.target.value)}
              placeholder="Plak je API secret hier"
              className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-500 disabled:bg-gray-600 text-white rounded-lg font-medium"
            >
              {saving ? 'Opslaan...' : '✅ Opslaan & Testen'}
            </button>
            <button
              type="button"
              onClick={() => setShowSetup(false)}
              className="px-6 py-3 bg-gray-600 hover:bg-gray-500 text-white rounded-lg"
            >
              Annuleren
            </button>
          </div>
        </form>

        <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-4">
          <p className="text-yellow-300 text-sm">
            ⚠️ <strong>Belangrijk:</strong> Credentials worden veilig opgeslagen in je user settings. 
            Gebruik alleen <strong>read-only</strong> permissions voor veiligheid.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-white mb-4">💰 Bitvavo Wallet</h2>
        <p className="text-gray-400">Laden...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-white mb-4">💰 Bitvavo Wallet</h2>
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
          <p className="text-red-300">❌ {error}</p>
          <p className="text-gray-400 text-sm mt-2">
            Zorg dat je Bitvavo API credentials zijn ingesteld.
          </p>
          <div className="flex gap-3 mt-3">
            <button
              onClick={loadPortfolio}
              className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm"
            >
              🔄 Opnieuw proberen
            </button>
            <button
              onClick={() => setShowSetup(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm"
            >
              ⚙️ Credentials instellen
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="p-6">
        <h2 className="text-2xl font-bold text-white mb-4">💰 Bitvavo Wallet</h2>
        <p className="text-gray-400">Geen data beschikbaar</p>
      </div>
    );
  }

  const { total_eur, balances, watchlist_prices } = portfolio;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">💰 Spark Portfolio</h2>
          <p className="text-gray-400 text-sm mt-1">
            Live balans (handmatige refresh)
          </p>
        </div>
        <button
          onClick={loadPortfolio}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
        >
          🔄 Ververs
        </button>
      </div>

      {/* Total Value */}
      <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 border border-green-500/30 rounded-lg p-6">
        <div className="text-sm text-gray-400 mb-1">Totale Waarde</div>
        <div className="text-4xl font-bold text-white">
          €{total_eur.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Laatste update: {new Date(portfolio.last_updated * 1000).toLocaleTimeString('nl-NL')}
        </div>
      </div>

      {/* Balances Table */}
      <div className="space-y-3">
        <h3 className="text-xl font-semibold text-white">Mijn Coins</h3>
        
        {balances.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-6 text-center text-gray-400">
            Geen balans gevonden
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-700/50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Coin</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-300">Amount</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-300">Prijs</th>
                  <th className="px-4 py-3 text-right text-sm font-medium text-gray-300">Waarde (EUR)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {balances.map((balance, index) => {
                  const amount = parseFloat(balance.amount);
                  const price = parseFloat(balance.price_eur);
                  const value = parseFloat(balance.value_eur);

                  return (
                    <tr 
                      key={index} 
                      className="hover:bg-gray-700/30 cursor-pointer"
                      onClick={() => balance.symbol !== 'EUR' && setSelectedCoin(balance.symbol)}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{balance.symbol}</span>
                          {balance.symbol === 'EUR' && (
                            <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">
                              FIAT
                            </span>
                          )}
                          {balance.symbol !== 'EUR' && (
                            <span className="text-xs text-gray-500">📊 klik voor grafiek</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-white">
                        {amount.toLocaleString('nl-NL', { 
                          minimumFractionDigits: balance.symbol === 'EUR' ? 2 : 8,
                          maximumFractionDigits: balance.symbol === 'EUR' ? 2 : 8
                        })}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-300">
                        {balance.symbol === 'EUR' ? (
                          '€1.00'
                        ) : (
                          `€${price.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                        )}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-green-400">
                        €{value.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Watchlist Prices */}
      {watchlist_prices && Object.keys(watchlist_prices).length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xl font-semibold text-white">Watchlist Prijzen</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {Object.entries(watchlist_prices).map(([coin, price]) => {
              const priceNum = parseFloat(price);
              
              return (
                <div key={coin} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="text-gray-400 text-sm mb-1">{coin}</div>
                  <div className="text-white font-bold">
                    €{priceNum > 0 ? priceNum.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '-'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Historical Coins Section */}
      {historicalData && historicalData.current_coins && historicalData.current_coins.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-xl font-semibold text-white">📊 Alle Coins (Ooit Gehad)</h3>
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex flex-wrap gap-2">
              {historicalData.current_coins.map((coin) => (
                <button
                  key={coin}
                  onClick={() => setSelectedCoin(coin)}
                  className="px-3 py-1 bg-green-600/20 text-green-400 border border-green-500/30 rounded-full text-sm font-medium hover:bg-green-600/30 transition-colors cursor-pointer"
                >
                  {coin} 📈
                </button>
              ))}
            </div>
            {historicalData.note && (
              <p className="text-gray-500 text-xs mt-3">
                💡 {historicalData.note}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Chart Modal */}
      {selectedCoin && (
        <CoinChartModal 
          coin={selectedCoin} 
          onClose={() => setSelectedCoin(null)} 
        />
      )}
    </div>
  );
};

export default WalletTab;
