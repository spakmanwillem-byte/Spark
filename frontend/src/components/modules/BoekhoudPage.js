import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  BookMarked, Plus, Trash2, ArrowUpRight, ArrowDownLeft,
  Building2, TrendingUp, TrendingDown, Filter, X
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const entityColors = { spark_core: '#f59e0b', spark_your_life: '#a855f7', roadkill_merch: '#22c55e', personal_willem: '#64748b' };

export function BoekhoudPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [activeTab, setActiveTab] = useState('overzicht');
  const [kasboeken, setKasboeken] = useState([]);
  const [summary, setSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState({ income: [], expense: [] });
  const [loading, setLoading] = useState(true);
  const [filterEntity, setFilterEntity] = useState(null);
  const [showNew, setShowNew] = useState(false);
  const [newTx, setNewTx] = useState({ type: 'income', category: 'Donations', amount: '', description: '', entity_id: 'spark_core', btw_percentage: 21 });

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/accounting/kasboeken?user_id=${userId}`).then(r => r.json()).catch(() => ({ kasboeken: [] })),
      fetch(`${API}/api/accounting/summary`).then(r => r.json()).catch(() => ({})),
      fetch(`${API}/api/accounting/transactions`).then(r => r.json()).catch(() => ({ transactions: [] })),
      fetch(`${API}/api/accounting/categories`).then(r => r.json()).catch(() => ({ income: [], expense: [] })),
    ]).then(([k, s, t, c]) => {
      setKasboeken(k.kasboeken || []);
      setSummary(s);
      setTransactions(t.transactions || []);
      setCategories(c);
      setLoading(false);
    });
  }, [userId]);

  const addTransaction = async () => {
    if (!newTx.amount || !newTx.description.trim()) return;
    const res = await fetch(`${API}/api/accounting/transactions`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...newTx, amount: parseFloat(newTx.amount) }),
    });
    const data = await res.json();
    if (data.success) {
      setTransactions([data.transaction, ...transactions]);
      setNewTx({ type: 'income', category: 'Donations', amount: '', description: '', entity_id: 'spark_core', btw_percentage: 21 });
      setShowNew(false);
      // Refresh summary + kasboeken
      const [k, s] = await Promise.all([
        fetch(`${API}/api/accounting/kasboeken`).then(r => r.json()),
        fetch(`${API}/api/accounting/summary`).then(r => r.json()),
      ]);
      setKasboeken(k.kasboeken || []);
      setSummary(s);
    }
  };

  const deleteTx = async (id) => {
    const res = await fetch(`${API}/api/accounting/transactions/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      setTransactions(transactions.filter(t => t.id !== id));
      const [k, s] = await Promise.all([
        fetch(`${API}/api/accounting/kasboeken`).then(r => r.json()),
        fetch(`${API}/api/accounting/summary`).then(r => r.json()),
      ]);
      setKasboeken(k.kasboeken || []);
      setSummary(s);
    }
  };

  const filteredTx = filterEntity ? transactions.filter(t => t.entity_id === filterEntity) : transactions;
  const catOptions = newTx.type === 'income' ? categories.income : categories.expense;

  const tabs = [
    { id: 'overzicht', label: 'Kasboeken' },
    { id: 'transacties', label: 'Transacties' },
  ];

  if (loading) return <MainLayout activePage="boekhouding" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-green-500/30 border-t-green-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage="boekhouding" onNavigate={onNavigate}>
      <div data-testid="boekhouding-page" className="h-[calc(100vh-4rem)] flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #22c55e, #14b8a6)' }}>
              <BookMarked className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Boekhouding</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{kasboeken.length} kasboeken | {transactions.length} transacties</p>
            </div>
            <button data-testid="add-tx-btn" onClick={() => setShowNew(!showNew)} className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white" style={{ background: 'linear-gradient(135deg, #22c55e, #14b8a6)' }}>
              <Plus className="w-3.5 h-3.5" /> Nieuw
            </button>
          </div>
          <div className="flex">
            {tabs.map(t => (
              <button key={t.id} data-testid={`boek-tab-${t.id}`} onClick={() => setActiveTab(t.id)}
                className="relative flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors"
                style={{ color: activeTab === t.id ? '#22c55e' : '#94a3b8' }}>
                {t.label}
                {activeTab === t.id && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full bg-green-500" />}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            {/* New transaction form */}
            {showNew && (
              <div className="p-4 bg-slate-900/60 border border-green-500/20 rounded-xl space-y-3">
                <div className="flex gap-2">
                  {['income', 'expense'].map(t => (
                    <button key={t} onClick={() => setNewTx({ ...newTx, type: t, category: t === 'income' ? 'Donations' : 'Hosting' })}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${newTx.type === t ? (t === 'income' ? 'bg-green-500 text-white' : 'bg-red-500 text-white') : 'bg-slate-800 text-slate-400'}`}>
                      {t === 'income' ? 'Inkomst' : 'Uitgave'}
                    </button>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input type="number" value={newTx.amount} onChange={e => setNewTx({ ...newTx, amount: e.target.value })} placeholder="Bedrag..."
                    className="w-32 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none" />
                  <select value={newTx.category} onChange={e => setNewTx({ ...newTx, category: e.target.value })}
                    className="flex-1 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-slate-300 focus:outline-none">
                    {catOptions.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                  <select value={newTx.entity_id} onChange={e => setNewTx({ ...newTx, entity_id: e.target.value })}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-slate-300 focus:outline-none">
                    {kasboeken.map(k => <option key={k.id} value={k.id}>{k.name}</option>)}
                  </select>
                </div>
                <div className="flex gap-2">
                  <input type="text" value={newTx.description} onChange={e => setNewTx({ ...newTx, description: e.target.value })} placeholder="Omschrijving..."
                    className="flex-1 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none" />
                  <button data-testid="save-tx-btn" onClick={addTransaction} className="px-4 py-2 bg-green-500 text-white rounded-lg text-xs font-medium">Opslaan</button>
                </div>
              </div>
            )}

            {/* KASBOEKEN TAB */}
            {activeTab === 'overzicht' && (
              <>
                {/* Totaal overzicht */}
                {summary && (
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-4 rounded-xl border border-green-500/20" style={{ background: 'linear-gradient(135deg, rgba(34,197,94,0.06), transparent)' }}>
                      <TrendingUp className="w-4 h-4 text-green-400 mb-1" />
                      <p className="text-xl font-bold text-green-400">{summary.income?.toFixed(2)}</p>
                      <p className="text-[10px] text-slate-500">Totaal Inkomsten</p>
                    </div>
                    <div className="p-4 rounded-xl border border-red-500/20" style={{ background: 'linear-gradient(135deg, rgba(239,68,68,0.06), transparent)' }}>
                      <TrendingDown className="w-4 h-4 text-red-400 mb-1" />
                      <p className="text-xl font-bold text-red-400">{summary.expenses?.toFixed(2)}</p>
                      <p className="text-[10px] text-slate-500">Totaal Uitgaven</p>
                    </div>
                    <div className="p-4 rounded-xl border border-amber-500/20" style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.06), transparent)' }}>
                      <BookMarked className="w-4 h-4 text-amber-400 mb-1" />
                      <p className={`text-xl font-bold ${summary.profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>{summary.profit?.toFixed(2)}</p>
                      <p className="text-[10px] text-slate-500">Resultaat</p>
                    </div>
                  </div>
                )}

                {/* 4 kasboeken */}
                <div className="space-y-3">
                  {kasboeken.map(kb => {
                    const color = entityColors[kb.id] || '#64748b';
                    return (
                      <div key={kb.id} data-testid={`kasboek-${kb.id}`} className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}15` }}>
                            <Building2 className="w-5 h-5" style={{ color }} />
                          </div>
                          <div className="flex-1">
                            <h3 className="text-sm font-semibold text-white">{kb.name}</h3>
                            <p className="text-[10px] text-slate-500">
                              {kb.type} | {kb.tx_count} transacties
                              {kb.bank_info?.iban && <span className="ml-2 text-slate-400">| {kb.bank_info.iban}</span>}
                              {kb.bank_info?.provider === 'Bitvavo' && <span className="ml-2 text-cyan-400">| Bitvavo</span>}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className={`text-lg font-bold ${kb.saldo >= 0 ? 'text-green-400' : 'text-red-400'}`}>&euro;{kb.saldo.toFixed(2)}</p>
                            <p className="text-[10px] text-slate-500">Saldo</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <div className="p-2 bg-slate-800/30 rounded-lg flex items-center gap-2">
                            <ArrowDownLeft className="w-3 h-3 text-green-400" />
                            <span className="text-xs text-green-400 font-medium">{kb.income.toFixed(2)}</span>
                            <span className="text-[10px] text-slate-600">in</span>
                          </div>
                          <div className="p-2 bg-slate-800/30 rounded-lg flex items-center gap-2">
                            <ArrowUpRight className="w-3 h-3 text-red-400" />
                            <span className="text-xs text-red-400 font-medium">{kb.expenses.toFixed(2)}</span>
                            <span className="text-[10px] text-slate-600">uit</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}

            {/* TRANSACTIES TAB */}
            {activeTab === 'transacties' && (
              <>
                {/* Filter */}
                <div className="flex flex-wrap gap-2">
                  <button onClick={() => setFilterEntity(null)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium ${!filterEntity ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-slate-800/50 text-slate-400 border border-transparent'}`}>
                    Alles ({transactions.length})
                  </button>
                  {kasboeken.map(kb => {
                    const c = entityColors[kb.id] || '#64748b';
                    return (
                      <button key={kb.id} onClick={() => setFilterEntity(kb.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filterEntity === kb.id ? 'border' : 'bg-slate-800/50 text-slate-400 border border-transparent'}`}
                        style={filterEntity === kb.id ? { background: `${c}15`, color: c, borderColor: `${c}40` } : {}}>
                        {kb.name} ({kb.tx_count})
                      </button>
                    );
                  })}
                </div>

                {/* Transaction list */}
                <div className="space-y-2">
                  {filteredTx.map(tx => (
                    <div key={tx.id} data-testid={`tx-${tx.id}`} className="flex items-center gap-3 p-3 bg-slate-900/50 border border-slate-800 rounded-xl">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${tx.type === 'income' ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                        {tx.type === 'income' ? <ArrowDownLeft className="w-4 h-4 text-green-400" /> : <ArrowUpRight className="w-4 h-4 text-red-400" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white truncate">{tx.description}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] text-slate-600">{tx.date ? new Date(tx.date).toLocaleDateString('nl-NL') : '?'}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">{tx.category}</span>
                          {tx.btw_amount > 0 && <span className="text-[10px] text-slate-600">BTW: {tx.btw_amount?.toFixed(2)}</span>}
                        </div>
                      </div>
                      <p className={`text-sm font-bold ${tx.type === 'income' ? 'text-green-400' : 'text-red-400'}`}>
                        {tx.type === 'income' ? '+' : '-'}{tx.amount?.toFixed(2)}
                      </p>
                      <button onClick={() => deleteTx(tx.id)} className="p-1.5 hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded-lg"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  ))}
                  {filteredTx.length === 0 && (
                    <div className="py-12 text-center"><BookMarked className="w-10 h-10 text-slate-700 mx-auto mb-3" /><p className="text-sm text-slate-500">Geen transacties gevonden</p></div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default BoekhoudPage;
