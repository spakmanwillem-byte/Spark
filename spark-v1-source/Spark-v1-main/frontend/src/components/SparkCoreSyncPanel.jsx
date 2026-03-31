import React, { useState, useEffect } from 'react';
import { RefreshCw, Check, X, Clock, Settings, DollarSign } from 'lucide-react';

const SparkCoreSyncPanel = () => {
  const [syncStatus, setSyncStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchSyncStatus();
    // Refresh status every 60 seconds
    const interval = setInterval(fetchSyncStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchSyncStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/spark_core/sync/status`);
      const data = await response.json();
      
      if (data.success) {
        setSyncStatus(data);
      }
    } catch (error) {
      console.error('[SYNC] Error fetching status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleManualSync = async () => {
    setSyncing(true);
    setMessage(null);
    
    try {
      const response = await fetch(`${API_URL}/api/spark_core/sync/now`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        setMessage({
          type: 'success',
          text: `✅ Balance gesynchroniseerd: €${data.balance_eur.toFixed(2)} (${data.change >= 0 ? '+' : ''}€${data.change.toFixed(2)})`
        });
      } else {
        setMessage({
          type: 'error',
          text: `❌ Sync mislukt: ${data.message}`
        });
      }
      
      // Refresh status
      await fetchSyncStatus();
    } catch (error) {
      setMessage({
        type: 'error',
        text: `❌ Error: ${error.message}`
      });
    } finally {
      setSyncing(false);
    }
  };

  const handleToggleSync = async (enable) => {
    setLoading(true);
    
    try {
      const endpoint = enable ? '/api/spark_core/sync/enable' : '/api/spark_core/sync/disable';
      const params = enable ? '?interval_minutes=30&spark_user_id=user-001' : '';
      
      const response = await fetch(`${API_URL}${endpoint}${params}`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        setMessage({
          type: 'success',
          text: data.message
        });
        await fetchSyncStatus();
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Error: ${error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading && !syncStatus) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <div className="text-gray-400">Laden...</div>
      </div>
    );
  }

  const lastUpdated = syncStatus?.last_updated 
    ? new Date(syncStatus.last_updated).toLocaleString('nl-NL')
    : 'Nog niet gesynchroniseerd';

  const lastSync = syncStatus?.last_sync_success
    ? new Date(syncStatus.last_sync_success).toLocaleString('nl-NL')
    : 'Nog geen sync uitgevoerd';

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <DollarSign className="w-6 h-6 text-blue-400" />
              Spark Core Bitvavo Balance Sync
            </h3>
            <p className="text-gray-400 text-sm mt-1">
              Automatische synchronisatie met Bitvavo wallet
            </p>
          </div>
          <div className={`px-4 py-2 rounded-full ${
            syncStatus?.auto_sync 
              ? 'bg-green-500/20 border border-green-500/50' 
              : 'bg-gray-500/20 border border-gray-500/50'
          }`}>
            <span className={`text-sm font-medium ${
              syncStatus?.auto_sync ? 'text-green-400' : 'text-gray-400'
            }`}>
              {syncStatus?.auto_sync ? '● Actief' : '○ Uitgeschakeld'}
            </span>
          </div>
        </div>
      </div>

      {/* Current Balance */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-400 mb-1">Huidige Balance</div>
            <div className="text-3xl font-bold text-white">
              €{syncStatus?.current_balance?.toFixed(2) || '0.00'}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              <Clock className="w-3 h-3 inline mr-1" />
              Laatste update: {lastUpdated}
            </div>
          </div>
          
          <div>
            <div className="text-sm text-gray-400 mb-1">Sync Configuratie</div>
            <div className="space-y-1 text-sm text-gray-300">
              <div>• Interval: {syncStatus?.interval_minutes} minuten</div>
              <div>• User ID: {syncStatus?.spark_user_id}</div>
              {syncStatus?.last_sync_success && (
                <div className="text-green-400">
                  <Check className="w-3 h-3 inline mr-1" />
                  Laatste sync: {lastSync}
                </div>
              )}
              {syncStatus?.last_sync_error && (
                <div className="text-red-400">
                  <X className="w-3 h-3 inline mr-1" />
                  Error: {syncStatus.last_sync_error}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div className={`p-4 rounded-lg border ${
          message.type === 'success'
            ? 'bg-green-900/20 border-green-500/30 text-green-400'
            : 'bg-red-900/20 border-red-500/30 text-red-400'
        }`}>
          {message.text}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleManualSync}
          disabled={syncing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Synchroniseren...' : 'Nu Synchroniseren'}
        </button>

        {syncStatus?.auto_sync ? (
          <button
            onClick={() => handleToggleSync(false)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
            Auto-Sync Uitschakelen
          </button>
        ) : (
          <button
            onClick={() => handleToggleSync(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          >
            <Check className="w-4 h-4" />
            Auto-Sync Inschakelen
          </button>
        )}
      </div>

      {/* Info */}
      <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Settings className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-300">
            <strong>Hoe werkt het?</strong>
            <p className="text-blue-400/80 mt-1">
              De Bitvavo balance wordt automatisch opgehaald en gecached. De ROARR token prijs 
              wordt dynamisch berekend op basis van deze balance: <strong>Token Prijs = Balance / Totaal Tokens</strong>.
              Standaard interval: 30 minuten (configureerbaar).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SparkCoreSyncPanel;
