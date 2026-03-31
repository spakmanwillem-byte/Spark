import React, { useState, useEffect } from 'react';

const EntityDetailModal = ({ entity, onClose, userId }) => {
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Form state
  const [amount, setAmount] = useState('');
  const [type, setType] = useState('donation');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  const API = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (entity) {
      loadTransactions();
    }
  }, [entity]);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${API}/api/wallet/entities/${entity.id}/transactions?limit=50`
      );
      const data = await response.json();
      
      if (data.success) {
        setTransactions(data.transactions || []);
        setStats(data.stats || {});
      }
    } catch (err) {
      console.error('Error loading transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!amount || parseFloat(amount) <= 0) {
      alert('Voer een geldig bedrag in');
      return;
    }
    
    if (!description.trim()) {
      alert('Voer een beschrijving in');
      return;
    }
    
    try {
      setSubmitting(true);
      
      const response = await fetch(
        `${API}/api/wallet/entities/${entity.id}/transaction?` +
        `amount=${parseFloat(amount)}&type=${type}&description=${encodeURIComponent(description)}&user_id=${userId}`,
        { method: 'POST' }
      );
      
      const data = await response.json();
      
      if (data.success) {
        alert('✅ Transaction toegevoegd!');
        setAmount('');
        setDescription('');
        loadTransactions();
        // Trigger parent refresh
        window.dispatchEvent(new Event('wallet-updated'));
      } else {
        alert('❌ Fout: ' + data.error);
      }
    } catch (err) {
      alert('❌ Fout bij opslaan: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (!entity) return null;

  const typeLabels = {
    donation: '🎁 Donatie',
    income: '💰 Inkomsten',
    expense: '💸 Kosten'
  };

  return (
    <div 
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-gray-900 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-auto border border-gray-700"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <span className="text-4xl">{entity.icon}</span>
            <div>
              <h2 className="text-2xl font-bold text-white">{entity.name}</h2>
              <p className="text-sm text-gray-400">{entity.description}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl font-bold"
            style={{ 
              pointerEvents: 'auto',
              zIndex: 99999,
              cursor: 'pointer'
            }}
            type="button"
          >
            ✕
          </button>
        </div>

        {/* Stats */}
        {stats && (
          <div className="p-6 bg-gray-800/50 border-b border-gray-700">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-gray-400 text-sm mb-1">Totaal Balance</div>
                <div className="text-2xl font-bold text-white">
                  €{stats.net?.toFixed(2) || '0.00'}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm mb-1">Donaties</div>
                <div className="text-2xl font-bold text-green-400">
                  €{stats.total_donations?.toFixed(2) || '0.00'}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm mb-1">Inkomsten</div>
                <div className="text-2xl font-bold text-blue-400">
                  €{stats.total_income?.toFixed(2) || '0.00'}
                </div>
              </div>
              <div>
                <div className="text-gray-400 text-sm mb-1">Kosten</div>
                <div className="text-2xl font-bold text-red-400">
                  €{stats.total_expenses?.toFixed(2) || '0.00'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Add Transaction Form */}
        <div className="p-6 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">➕ Nieuwe Transaction</h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-gray-400 text-sm block mb-1">Bedrag (EUR)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                  required
                />
              </div>
              
              <div>
                <label className="text-gray-400 text-sm block mb-1">Type</label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                >
                  <option value="donation">🎁 Donatie</option>
                  <option value="income">💰 Inkomsten</option>
                  <option value="expense">💸 Kosten</option>
                </select>
              </div>
              
              <div>
                <label className="text-gray-400 text-sm block mb-1">Beschrijving</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Korte omschrijving"
                  className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600 focus:border-purple-500 focus:outline-none"
                  required
                />
              </div>
            </div>
            
            <button
              type="submit"
              disabled={submitting}
              className="w-full px-4 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {submitting ? 'Opslaan...' : '✅ Transaction Toevoegen'}
            </button>
          </form>
        </div>

        {/* Transactions List */}
        <div className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📋 Recente Transactions</h3>
          
          {loading ? (
            <p className="text-gray-400 text-center py-8">Laden...</p>
          ) : transactions.length === 0 ? (
            <p className="text-gray-400 text-center py-8">Nog geen transactions</p>
          ) : (
            <div className="space-y-2">
              {transactions.map((tx) => (
                <div 
                  key={tx.id}
                  className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">
                        {tx.type === 'donation' && '🎁'}
                        {tx.type === 'income' && '💰'}
                        {tx.type === 'expense' && '💸'}
                      </span>
                      <div>
                        <div className="text-white font-medium">{tx.description}</div>
                        <div className="text-xs text-gray-500">
                          {new Date(tx.timestamp * 1000).toLocaleDateString('nl-NL', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      </div>
                    </div>
                    
                    <div className={`text-xl font-bold ${
                      tx.type === 'expense' ? 'text-red-400' : 'text-green-400'
                    }`}>
                      {tx.type === 'expense' ? '-' : '+'}€{tx.amount.toFixed(2)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EntityDetailModal;
