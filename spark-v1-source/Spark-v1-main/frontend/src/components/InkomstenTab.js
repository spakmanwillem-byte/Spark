import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function InkomstenTab({ userId }) {
  const [income, setIncome] = useState([]);
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  
  // Form state
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, [userId]);

  const loadData = async () => {
    try {
      const [categoriesRes, summaryRes] = await Promise.all([
        axios.get(`${API}/income/categories`),
        axios.get(`${API}/income/summary`, { params: { user_id: userId } })
      ]);

      if (categoriesRes.data.success) {
        setCategories(categoriesRes.data.categories);
      }

      if (summaryRes.data.success) {
        setSummary(summaryRes.data);
        setIncome(summaryRes.data.income || []);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error loading income:', error);
      setLoading(false);
    }
  };

  const handleAddIncome = async (e) => {
    e.preventDefault();
    
    if (!amount || !category) {
      alert('Vul minimaal bedrag en categorie in');
      return;
    }

    setSaving(true);
    try {
      const response = await axios.post(
        `${API}/income/add`,
        {
          amount: parseFloat(amount),
          category,
          description,
          date
        },
        {
          params: { user_id: userId }
        }
      );

      if (response.data.success) {
        // Clear form
        setAmount('');
        setCategory('');
        setDescription('');
        setDate(new Date().toISOString().split('T')[0]);
        setShowAddForm(false);
        
        // Reload data
        await loadData();
      }
    } catch (error) {
      console.error('Error adding income:', error);
      alert('Kon inkomst niet toevoegen');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (incomeId) => {
    if (!window.confirm('Weet je zeker dat je deze inkomst wilt verwijderen?')) {
      return;
    }

    try {
      const response = await axios.delete(
        `${API}/income/${incomeId}`,
        {
          params: { user_id: userId }
        }
      );

      if (response.data.success) {
        await loadData();
      }
    } catch (error) {
      console.error('Error deleting income:', error);
      alert('Kon inkomst niet verwijderen');
    }
  };

  const formatDate = (isoDate) => {
    if (!isoDate) return '';
    const date = new Date(isoDate);
    return date.toLocaleDateString('nl-NL', { 
      day: '2-digit', 
      month: 'short',
      year: 'numeric'
    });
  };

  const formatAmount = (amount) => {
    return `€${amount.toFixed(2).replace('.', ',')}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-purple-400">Inkomsten laden...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">💰 Inkomsten</h2>
          <p className="text-sm text-gray-400 mt-1">Privé inkomsten administratie</p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          data-testid="income-add-button"
        >
          {showAddForm ? '✕ Annuleren' : '+ Nieuwe Inkomst'}
        </button>
      </div>

      {/* Summary Card */}
      {summary && (
        <div className="bg-slate-800/50 backdrop-blur-lg border border-green-500/20 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              📊 Overzicht {summary.month}
            </h3>
            <div className="text-right">
              <div className="text-2xl font-bold text-green-400">
                {formatAmount(summary.total)}
              </div>
              <div className="text-xs text-gray-400">{summary.count} inkomsten</div>
            </div>
          </div>

          {/* Category breakdown */}
          {summary.by_category && Object.keys(summary.by_category).length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-4">
              {Object.entries(summary.by_category).map(([cat, amount]) => (
                <div key={cat} className="bg-slate-900/50 rounded p-3">
                  <div className="text-xs text-gray-400">{cat}</div>
                  <div className="text-sm font-semibold text-white mt-1">
                    {formatAmount(amount)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Add Form */}
      {showAddForm && (
        <div className="bg-slate-800/50 backdrop-blur-lg border border-green-500/20 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">✍️ Nieuwe Inkomst</h3>
          <form onSubmit={handleAddIncome} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-300 mb-2">Bedrag *</label>
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.00"
                  className="w-full bg-slate-900/50 border border-green-500/20 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500/50"
                  required
                  data-testid="income-amount-input"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-300 mb-2">Categorie *</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-900/50 border border-green-500/20 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500/50"
                  required
                  data-testid="income-category-select"
                >
                  <option value="">Selecteer...</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-2">Beschrijving</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optioneel"
                className="w-full bg-slate-900/50 border border-green-500/20 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500/50"
                data-testid="income-description-input"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-2">Datum</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full bg-slate-900/50 border border-green-500/20 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500/50"
                data-testid="income-date-input"
              />
            </div>

            <button
              type="submit"
              disabled={saving}
              className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-green-800 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-semibold"
              data-testid="income-submit-button"
            >
              {saving ? 'Bezig met opslaan...' : '💾 Opslaan'}
            </button>
          </form>
        </div>
      )}

      {/* Income List */}
      <div className="bg-slate-800/50 backdrop-blur-lg border border-green-500/20 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">📋 Recente Inkomsten</h3>
        
        {income.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p>Geen inkomsten gevonden</p>
            <p className="text-sm mt-2">Voeg je eerste inkomst toe om te beginnen</p>
          </div>
        ) : (
          <div className="space-y-2">
            {income.map((entry) => (
              <div
                key={entry.id}
                className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg hover:bg-slate-900/70 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <div className="text-sm font-semibold text-white">
                      {entry.category}
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(entry.date)}
                    </div>
                  </div>
                  {entry.description && (
                    <div className="text-sm text-gray-400 mt-1">
                      {entry.description}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-lg font-bold text-green-400">
                    {formatAmount(entry.amount)}
                  </div>
                  <button
                    onClick={() => handleDelete(entry.id)}
                    className="text-red-400 hover:text-red-300 transition-colors"
                    title="Verwijderen"
                    data-testid={`income-delete-${entry.id}`}
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default InkomstenTab;
