import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  BookMarked, Plus, Trash2, ArrowUpRight, ArrowDownLeft,
  Building2, TrendingUp, TrendingDown, Filter, X, Inbox
} from 'lucide-react';
import { AdminTikkieReview } from './AdminTikkieReview';
import { BoekhoudingBoekenTab } from './BoekhoudingBoekenTab';
import { WinstEventsTab } from './WinstEventsTab';

const API = process.env.REACT_APP_BACKEND_URL;

const entityColors = { spark_core: '#f59e0b', spark_your_life: '#a855f7', roadkill_merch: '#22c55e', personal_willem: '#64748b' };

export function BoekhoudPage({ onNavigate }) {
  const { user, isAdmin } = useAuth();
  const userId = user?.id || 'user-001';
  const [activeTab, setActiveTab] = useState('boeken');
  const [kasboeken, setKasboeken] = useState([]);
  const [reconcile, setReconcile] = useState(null);  // v6_commitments_001
  const [summary, setSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState({ income: [], expense: [] });
  const [loading, setLoading] = useState(true);
  const [filterEntity, setFilterEntity] = useState(null);
  const [showNew, setShowNew] = useState(false);
  const [newTx, setNewTx] = useState({ type: 'income', category: 'Donations', amount: '', description: '', entity_id: 'spark_core', btw_percentage: 21 });

  // v12_admin_toggle_001 — isAdmin komt nu van AuthContext (admin_capable && adminModeActive).

  // v5_tikkie_topup_001 — Tikkie admin inbox in Boekhouden (verhuisd van Wallet)
  const [showAdminTikkie, setShowAdminTikkie] = useState(false);
  const [pendingTikkieCount, setPendingTikkieCount] = useState(0);
  useEffect(() => {
    if (!isAdmin || !user?.id) return;
    const load = () => fetch(`${API}/api/wallet/tikkie/list?viewer_id=${user.id}&status=pending`)
      .then(r => r.ok ? r.json() : { topups: [] })
      .then(d => setPendingTikkieCount((d.topups || []).length))
      .catch(() => {});
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [isAdmin, user?.id, showAdminTikkie]);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/accounting/kasboeken?user_id=${userId}&viewer_id=${userId}`).then(r => r.json()).catch(() => ({ kasboeken: [] })),
      // Summary + alle transactions alleen voor admin (gradatie <= 2)
      isAdmin ? fetch(`${API}/api/accounting/summary`).then(r => r.json()).catch(() => ({})) : Promise.resolve(null),
      isAdmin ? fetch(`${API}/api/accounting/transactions`).then(r => r.json()).catch(() => ({ transactions: [] })) : Promise.resolve({ transactions: [] }),
      fetch(`${API}/api/accounting/categories`).then(r => r.json()).catch(() => ({ income: [], expense: [] })),
      // v6_commitments_001 — Spark openstaande potje-commitments
      isAdmin ? fetch(`${API}/api/spark/kasboek/reconcile`).then(r => r.json()).catch(() => null) : Promise.resolve(null),
    ]).then(([k, s, t, c, rec]) => {
      setKasboeken(k.kasboeken || []);
      setSummary(s);
      setTransactions(t.transactions || []);
      setCategories(c);
      setReconcile(rec);
      setLoading(false);
    });
  }, [userId, isAdmin]);

  // v6_commitments_001 — re-check storting elke 5min als admin op deze pagina is
  useEffect(() => {
    if (!isAdmin) return;
    const check = () => {
      fetch(`${API}/api/spark/deposit-watcher/check?user_id=${userId}`)
        .then(r => r.json())
        .then(d => { if (d?.commitments) setReconcile(prev => ({ ...(prev || {}), commitments: d.commitments })); })
        .catch(() => {});
    };
    check();
    const t = setInterval(check, 5 * 60 * 1000);
    return () => clearInterval(t);
  }, [isAdmin, userId]);

  const addTransaction = async () => {
    if (!newTx.amount || !newTx.description.trim()) return;
    // v6_signed_amount_001 (28 mei) — bedrag met +/- teken: auto-detect type
    const raw = String(newTx.amount).trim().replace(',', '.');
    const num = parseFloat(raw);
    if (isNaN(num) || num === 0) return;
    // Negatief = expense, positief = income (signed-input overrules type-button)
    const isNeg = num < 0 || raw.startsWith('-');
    const finalType = isNeg ? 'expense' : 'income';
    const finalAmount = Math.abs(num);
    const finalCategory = newTx.category && (isNeg ? categories.expense : categories.income)?.includes(newTx.category)
      ? newTx.category
      : (isNeg ? 'Overig' : 'Donations');
    const res = await fetch(`${API}/api/accounting/transactions`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...newTx, type: finalType, category: finalCategory, amount: finalAmount }),
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

  // v6_accounting_edit_001 — bedrag inline aanpassen via modal (was prompt)
  const [editingTx, setEditingTx] = useState(null);
  const [editAmount, setEditAmount] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const openEditTx = (tx) => {
    setEditingTx(tx);
    // v6_signed_amount_001 — toon bedrag met teken (- voor expense, + voor income)
    const signed = tx.type === 'expense' ? `-${tx.amount}` : `${tx.amount}`;
    setEditAmount(signed);
  };
  const saveEditTx = async () => {
    const raw = String(editAmount).replace(',', '.').trim();
    const v = parseFloat(raw);
    if (!Number.isFinite(v) || v === 0) { alert('Ongeldig bedrag'); return; }
    // v6_signed_amount_001 — als teken veranderd is, ook type updaten
    const isNeg = v < 0 || raw.startsWith('-');
    const newType = isNeg ? 'expense' : 'income';
    const absAmt = Math.abs(v);
    setEditSaving(true);
    try {
      const res = await fetch(`${API}/api/accounting/transactions/${editingTx.id}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: absAmt, type: newType }),
      });
      const data = await res.json();
      if (!data.success) { alert('Aanpassen mislukt: ' + (data.message || JSON.stringify(data))); return; }
      setTransactions(prev => prev.map(t => t.id === editingTx.id ? data.transaction : t));
      const [k, s] = await Promise.all([
        fetch(`${API}/api/accounting/kasboeken`).then(r => r.json()),
        fetch(`${API}/api/accounting/summary`).then(r => r.json()),
      ]);
      setKasboeken(k.kasboeken || []);
      setSummary(s);
      setEditingTx(null);
    } finally { setEditSaving(false); }
  };
  const editTxAmount = openEditTx;  // backwards-compat (overige buttons gebruiken deze naam)

  // v6_accounting_edit_kasboek_001 — uitklap-state per kasboek voor inline transactie-edit
  const [expandedKb, setExpandedKb] = useState(null);

  const filteredTx = filterEntity ? transactions.filter(t => t.entity_id === filterEntity) : transactions;
  const catOptions = newTx.type === 'income' ? categories.income : categories.expense;

  const tabs = isAdmin ? [
    { id: 'boeken', label: 'Boeken' },
    { id: 'winst', label: 'Winst → Spark' },
    { id: 'klanten', label: 'Klanten' },
  ] : [
    { id: 'boeken', label: 'Mijn Boeken' },
  ];

  if (loading) return <MainLayout activePage="boekhouding" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-green-500/30 border-t-green-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage="boekhouding" onNavigate={onNavigate}>
      <div data-testid="boekhouding-page" className="h-full flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #22c55e, #14b8a6)' }}>
              <BookMarked className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Boekhouding</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">
                {isAdmin
                  ? `${kasboeken.length} kasboeken | ${transactions.length} transacties`
                  : 'Multi-book boekhouding'}
              </p>
            </div>
            <div className="ml-auto flex items-center gap-2">
              {isAdmin && (
                <button data-testid="open-admin-tikkie-btn" onClick={() => setShowAdminTikkie(true)}
                  title="Tikkie-aanvragen van users (storten op wallet)"
                  className="relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-amber-300 border border-amber-500/40 hover:border-amber-400 bg-amber-500/5">
                  <Inbox className="w-3.5 h-3.5" /> Tikkie
                  {pendingTikkieCount > 0 && (
                    <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-[10px] font-bold text-white">
                      {pendingTikkieCount}
                    </span>
                  )}
                </button>
              )}
              <button data-testid="add-tx-btn" onClick={() => setShowNew(!showNew)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white" style={{ background: 'linear-gradient(135deg, #22c55e, #14b8a6)' }}>
                <Plus className="w-3.5 h-3.5" /> Nieuw
              </button>
            </div>
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
                  {/* v6_signed_amount_001 — Bedrag accepteert +5.00 of -49.92 (teken overrules type-knop) */}
                  <input
                    type="text"
                    inputMode="decimal"
                    value={newTx.amount}
                    onChange={e => {
                      const v = e.target.value;
                      // Auto-toggle type-button als user expliciet teken typt
                      const cleaned = v.trim().replace(',', '.');
                      const isNeg = cleaned.startsWith('-');
                      const isPos = cleaned.startsWith('+');
                      const next = { ...newTx, amount: v };
                      if (isNeg && newTx.type !== 'expense') {
                        next.type = 'expense';
                        next.category = 'Overig';
                      } else if (isPos && newTx.type !== 'income') {
                        next.type = 'income';
                        next.category = 'Donations';
                      }
                      setNewTx(next);
                    }}
                    placeholder="Bedrag (gebruik +/- bv -49.92)"
                    data-testid="tx-amount-input"
                    className="w-40 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50" />
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
                    const isOpen = expandedKb === kb.id;
                    const kbTxs = transactions.filter(t => t.entity_id === kb.id);
                    return (
                      <div key={kb.id} data-testid={`kasboek-${kb.id}`} className="bg-slate-900/50 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors">
                        <button data-testid={`kasboek-toggle-${kb.id}`}
                          onClick={() => setExpandedKb(isOpen ? null : kb.id)}
                          className="w-full text-left p-4">
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}15` }}>
                              <Building2 className="w-5 h-5" style={{ color }} />
                            </div>
                            <div className="flex-1">
                              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                                {kb.name}
                                <span className="text-[10px] text-slate-500">{isOpen ? '▼' : '▶'} {isAdmin && kbTxs.length > 0 ? 'klik om transacties + bedragen aan te passen' : ''}</span>
                              </h3>
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
                        </button>
                        {/* v6_accounting_edit_kasboek_001 — uitgeklapte transactie-lijst met €✎ */}
                        {isOpen && (
                          <div data-testid={`kasboek-tx-list-${kb.id}`} className="border-t border-slate-800 px-4 py-3 space-y-1.5">
                            {kbTxs.length === 0 ? (
                              <p className="text-[11px] text-slate-500 italic py-2">Geen transacties.</p>
                            ) : kbTxs.map(tx => (
                              <div key={tx.id} data-testid={`kb-tx-row-${tx.id}`} className="flex items-center gap-2 py-1.5 px-2 bg-slate-800/30 rounded-lg">
                                <span className={`w-2 h-2 rounded-full ${tx.type === 'income' ? 'bg-green-400' : 'bg-red-400'}`} />
                                <div className="flex-1 min-w-0">
                                  <p className="text-xs text-slate-200 truncate">{tx.description}</p>
                                  <p className="text-[10px] text-slate-600">{tx.category}{tx.date && ` · ${new Date(tx.date).toLocaleDateString('nl-NL')}`}</p>
                                </div>
                                <span className={`text-sm font-bold ${tx.type === 'income' ? 'text-green-400' : 'text-red-400'}`}>
                                  {tx.type === 'income' ? '+' : '-'}€{tx.amount?.toFixed(2)}
                                </span>
                                {isAdmin && (
                                  <button data-testid={`kb-tx-edit-${tx.id}`} onClick={(e) => { e.stopPropagation(); openEditTx(tx); }}
                                    title="Bedrag aanpassen"
                                    className="px-2 py-1 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded text-[10px] font-bold">
                                    ✎ Bewerk
                                  </button>
                                )}
                                {isAdmin && (
                                  <button data-testid={`kb-tx-delete-${tx.id}`} onClick={(e) => { e.stopPropagation(); deleteTx(tx.id); }}
                                    className="p-1 hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded">
                                    <Trash2 className="w-3 h-3" />
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
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
                      <button data-testid={`tx-edit-${tx.id}`} onClick={() => openEditTx(tx)}
                        title="Bedrag aanpassen"
                        className="px-2 py-1 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded text-[11px] font-bold">
                        ✎ Bewerk
                      </button>
                      <button onClick={() => deleteTx(tx.id)} className="p-1.5 hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded-lg"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  ))}
                  {filteredTx.length === 0 && (
                    <div className="py-12 text-center"><BookMarked className="w-10 h-10 text-slate-700 mx-auto mb-3" /><p className="text-sm text-slate-500">Geen transacties gevonden</p></div>
                  )}
                </div>
              </>
            )}

            {activeTab === 'klanten' && <KlantenTab API={API} />}
            {activeTab === 'boeken' && <BoekhoudingBoekenTab userId={userId} />}
            {activeTab === 'winst' && <WinstEventsTab userId={userId} />}
          </div>
        </div>
      </div>

      {/* v6_accounting_edit_002 — Edit Transactie Modal */}
      {editingTx && (
        <div data-testid="edit-tx-modal" className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => !editSaving && setEditingTx(null)}>
          <div className="w-full max-w-md bg-slate-900 border border-amber-500/40 rounded-2xl p-5 space-y-4" onClick={e => e.stopPropagation()}>
            <div>
              <h3 className="text-base font-bold text-white">Bedrag aanpassen</h3>
              <p className="text-xs text-slate-400 mt-1">{editingTx.description}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">{editingTx.category} · {editingTx.entity_id}</p>
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase tracking-wider">Nieuw bedrag (€)</label>
              <input data-testid="edit-tx-input" type="number" step="0.01" autoFocus
                value={editAmount} onChange={e => setEditAmount(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && saveEditTx()}
                className="mt-1 w-full px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-base text-white focus:outline-none focus:border-amber-500" />
              <p className="text-[10px] text-slate-500 mt-1">Huidig: €{editingTx.amount?.toFixed(2)}</p>
            </div>
            <div className="flex gap-2">
              <button data-testid="edit-tx-cancel" onClick={() => setEditingTx(null)} disabled={editSaving}
                className="flex-1 py-2 rounded-lg text-sm font-medium bg-slate-800 text-slate-300 hover:bg-slate-700">
                Annuleren
              </button>
              <button data-testid="edit-tx-save" onClick={saveEditTx} disabled={editSaving}
                className="flex-1 py-2 rounded-lg text-sm font-bold text-slate-900 disabled:opacity-60"
                style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
                {editSaving ? 'Opslaan…' : 'Opslaan'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* v5_tikkie_topup_001 — Admin Tikkie review modal (verhuisd van Wallet) */}
      {isAdmin && <AdminTikkieReview open={showAdminTikkie} onClose={() => setShowAdminTikkie(false)} user={user} />}
    </MainLayout>
  );
}

// v6_bonnetje_001 — Klanten-tab toont per-klant aankoophistorie met link naar bonnetje-document
function KlantenTab({ API }) {
  const [klanten, setKlanten] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  React.useEffect(() => {
    (async () => {
      try {
        // 1. Haal alle users op (zonder ankers en bots)
        const users = await fetch(`${API}/api/auth/users?viewer_id=user-001`).then(r => r.json()).then(d => d.users || []);
        const klantUsers = users.filter(u =>
          !['user-000', 'user-001'].includes(u.id) && !(u.id || '').startsWith('bot-')
        );
        // 2. Voor elke klant: bonnetjes ophalen
        const result = await Promise.all(klantUsers.map(async u => {
          const b = await fetch(`${API}/api/bonnetjes/user/${u.id}`).then(r => r.json()).catch(() => ({ bonnetjes: [] }));
          return { ...u, bonnetjes: b.bonnetjes || [] };
        }));
        setKlanten(result.filter(k => k.bonnetjes.length > 0));  // alleen klanten met aankopen
      } finally {
        setLoading(false);
      }
    })();
  }, [API]);

  if (loading) return <div className="text-slate-400 text-sm py-8 text-center">Klanten laden...</div>;
  if (klanten.length === 0) return (
    <div className="py-12 text-center">
      <BookMarked className="w-10 h-10 text-slate-700 mx-auto mb-3" />
      <p className="text-sm text-slate-500">Nog geen klant-aankopen (anker-houders Spark/Willem worden niet getoond)</p>
    </div>
  );

  return (
    <div className="space-y-4" data-testid="boek-klanten-tab">
      {klanten.map(k => {
        const totaalIncl = k.bonnetjes.reduce((s, b) => s + (b.bedrag_eur || 0), 0);
        const totaalBtw = k.bonnetjes.reduce((s, b) => s + (b.btw_eur || 0), 0);
        const totaalNetto = k.bonnetjes.reduce((s, b) => s + (b.netto_eur || 0), 0);
        const totaalTokens = k.bonnetjes.reduce((s, b) => s + (b.n_tokens || 0), 0);
        return (
          <div key={k.id} data-testid={`klant-card-${k.id}`}
            className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h3 className="text-base font-bold text-white">{k.naam}</h3>
                <p className="text-[10px] text-slate-500 font-mono">{k.id}</p>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-400">{k.bonnetjes.length} aankoop · {totaalTokens} ROAR</div>
                <div className="text-sm text-emerald-300 font-semibold">€{totaalIncl.toFixed(2)} incl</div>
                <div className="text-[10px] text-slate-500">netto €{totaalNetto.toFixed(2)} · BTW €{totaalBtw.toFixed(2)}</div>
              </div>
            </div>
            <div className="space-y-1">
              {k.bonnetjes.map(b => (
                <div key={b.tx_id} className="flex items-center justify-between gap-3 py-2 px-3 bg-slate-800/40 rounded-lg text-xs">
                  <div className="flex-1 min-w-0">
                    <div className="text-slate-200">{b.n_tokens} ROAR — €{(b.bedrag_eur || 0).toFixed(2)} incl</div>
                    <div className="text-[10px] text-slate-500">{(b.ts || '').slice(0, 16).replace('T', ' ')}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-emerald-300">€{(b.netto_eur || 0).toFixed(2)}</div>
                    <div className="text-[10px] text-amber-400">BTW €{(b.btw_eur || 0).toFixed(2)}</div>
                  </div>
                  <a
                    data-testid={`bonnetje-link-${b.tx_id}`}
                    href={`${API}/api/bonnetjes/${b.tx_id}/download/file`}
                    target="_blank" rel="noreferrer"
                    title="Download bonnetje (.md)"
                    className="px-2 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-[10px] border border-amber-500/30">
                    🧾 Bonnetje
                  </a>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default BoekhoudPage;
