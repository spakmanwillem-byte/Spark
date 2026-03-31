import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AccountingTab.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AccountingTab = ({ userData }) => {
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    type: 'income',
    category: '',
    amount: '',
    description: '',
    date: new Date().toISOString().split('T')[0],
    btw_percentage: 21
  });
  const [loading, setLoading] = useState(true);

  // Check if user is admin
  const isAdmin = userData && userData.gradatie === 1;

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryRes, categoriesRes] = await Promise.all([
        axios.get(`${API}/accounting/summary`),
        axios.get(`${API}/accounting/categories`)
      ]);

      if (summaryRes.data.success) {
        setSummary(summaryRes.data.summary);
        setTransactions(summaryRes.data.transactions);
      }

      if (categoriesRes.data.success) {
        setCategories(categoriesRes.data);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error loading accounting data:', error);
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post(`${API}/accounting/transaction`, {
        type: formData.type,
        category: formData.category,
        amount: parseFloat(formData.amount),
        description: formData.description,
        date: formData.date,
        btw_percentage: parseFloat(formData.btw_percentage)
      });

      if (response.data.success) {
        alert('Transactie toegevoegd!');
        setFormData({
          type: 'income',
          category: '',
          amount: '',
          description: '',
          date: new Date().toISOString().split('T')[0],
          btw_percentage: 21
        });
        setShowAddForm(false);
        loadData();
      }
    } catch (error) {
      console.error('Error adding transaction:', error);
      alert('Fout bij toevoegen transactie');
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  if (!isAdmin) {
    return (
      <div className="accounting-tab">
        <h2>📊 Boekhouding</h2>
        <div className="admin-only-message">
          <p>🔒 Deze pagina is alleen toegankelijk voor admins</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="accounting-tab">
        <h2>📊 Boekhouding</h2>
        <p>Laden...</p>
      </div>
    );
  }

  const currentCategories = formData.type === 'income' 
    ? categories?.income_categories || []
    : categories?.expense_categories || [];

  return (
    <div className="accounting-tab">
      <div className="accounting-header">
        <h2>📊 Boekhouding</h2>
        <button 
          className="add-transaction-btn"
          onClick={() => setShowAddForm(!showAddForm)}
        >
          {showAddForm ? '❌ Annuleren' : '➕ Transactie Toevoegen'}
        </button>
      </div>

      {showAddForm && (
        <div className="transaction-form">
          <h3>Nieuwe Transactie</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Type</label>
                <select 
                  name="type" 
                  value={formData.type}
                  onChange={handleInputChange}
                  required
                >
                  <option value="income">📈 Inkomsten</option>
                  <option value="expense">📉 Uitgaven</option>
                </select>
              </div>

              <div className="form-group">
                <label>Categorie</label>
                <select 
                  name="category" 
                  value={formData.category}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">Selecteer categorie...</option>
                  {currentCategories.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Bedrag (€)</label>
                <input
                  type="number"
                  name="amount"
                  step="0.01"
                  min="0"
                  value={formData.amount}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>BTW %</label>
                <select 
                  name="btw_percentage" 
                  value={formData.btw_percentage}
                  onChange={handleInputChange}
                >
                  <option value="0">0%</option>
                  <option value="9">9%</option>
                  <option value="21">21%</option>
                </select>
              </div>

              <div className="form-group">
                <label>Datum</label>
                <input
                  type="date"
                  name="date"
                  value={formData.date}
                  onChange={handleInputChange}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Omschrijving</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows="3"
                required
              />
            </div>

            <button type="submit" className="submit-btn">
              💾 Opslaan
            </button>
          </form>
        </div>
      )}

      <div className="accounting-summary">
        <div className="summary-card income-card">
          <div className="summary-icon">📈</div>
          <div className="summary-info">
            <div className="summary-label">Inkomsten</div>
            <div className="summary-value">€ {summary?.income?.toFixed(2) || '0.00'}</div>
          </div>
        </div>

        <div className="summary-card expense-card">
          <div className="summary-icon">📉</div>
          <div className="summary-info">
            <div className="summary-label">Uitgaven</div>
            <div className="summary-value">€ {summary?.expenses?.toFixed(2) || '0.00'}</div>
          </div>
        </div>

        <div className="summary-card profit-card">
          <div className="summary-icon">💰</div>
          <div className="summary-info">
            <div className="summary-label">Winst/Verlies</div>
            <div className={`summary-value ${summary?.profit >= 0 ? 'positive' : 'negative'}`}>
              € {summary?.profit?.toFixed(2) || '0.00'}
            </div>
          </div>
        </div>

        <div className="summary-card btw-card">
          <div className="summary-icon">🧾</div>
          <div className="summary-info">
            <div className="summary-label">BTW Totaal</div>
            <div className="summary-value">€ {summary?.btw_total?.toFixed(2) || '0.00'}</div>
          </div>
        </div>
      </div>

      <div className="transactions-section">
        <h3>📋 Transacties ({summary?.transaction_count || 0})</h3>
        
        {transactions.length === 0 ? (
          <div className="no-transactions">
            <p>Nog geen transacties deze periode</p>
          </div>
        ) : (
          <div className="transactions-table">
            <table>
              <thead>
                <tr>
                  <th>Datum</th>
                  <th>Type</th>
                  <th>Categorie</th>
                  <th>Omschrijving</th>
                  <th>Bedrag</th>
                  <th>BTW</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.id} className={`transaction-row ${tx.type}`}>
                    <td>{new Date(tx.date).toLocaleDateString('nl-NL')}</td>
                    <td>
                      <span className={`type-badge ${tx.type}`}>
                        {tx.type === 'income' ? '📈 Inkomsten' : '📉 Uitgaven'}
                      </span>
                    </td>
                    <td>{tx.category}</td>
                    <td>{tx.description}</td>
                    <td className={`amount ${tx.type}`}>
                      {tx.type === 'income' ? '+' : '-'}€ {tx.amount.toFixed(2)}
                    </td>
                    <td>€ {tx.btw_amount?.toFixed(2) || '0.00'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="accounting-info">
        <h3>ℹ️ Informatie</h3>
        <ul>
          <li>💶 <strong>Placeholder Systeem:</strong> Dit is een test boekhoudsysteem voor Spark Foundation.</li>
          <li>📅 <strong>Periode:</strong> Standaard wordt de huidige maand getoond.</li>
          <li>🧾 <strong>BTW:</strong> BTW wordt automatisch berekend op basis van het gekozen percentage.</li>
          <li>🔐 <strong>Admin Only:</strong> Alleen admins kunnen transacties toevoegen en bekijken.</li>
        </ul>
      </div>
    </div>
  );
};

export default AccountingTab;
