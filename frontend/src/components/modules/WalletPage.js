import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Wallet, Coins, CreditCard, ArrowUpRight, ArrowDownLeft,
  Plus, Clock, Building2, Sparkles, TrendingUp
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

export function WalletPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [wallet, setWallet] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [entities, setEntities] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/wallet/user/${userId}`).then(r => r.json()).catch(() => ({})),
      fetch(`${API}/api/wallet/transactions/${userId}`).then(r => r.json()).catch(() => ({ transactions: [] })),
      fetch(`${API}/api/wallet/entities`).then(r => r.json()).catch(() => ({ entities: {} })),
    ]).then(([w, t, e]) => {
      setWallet(w);
      setTransactions(t.transactions || []);
      setEntities(e.entities || {});
      setLoading(false);
    });
  }, [userId]);

  if (loading) return <MainLayout activePage="wallet" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage="wallet" onNavigate={onNavigate}>
      <div data-testid="wallet-page" className="h-[calc(100vh-4rem)] flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #22c55e)' }}>
              <Wallet className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Persoonlijke Wallet</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{wallet?.name || userId}</p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            {/* Balance cards */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-5 rounded-2xl border border-amber-500/20" style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.08), rgba(234,88,12,0.04))' }}>
                <Coins className="w-5 h-5 text-amber-400 mb-2" />
                <p className="text-2xl font-bold text-white">{wallet?.spark_tokens?.toLocaleString() || 0}</p>
                <p className="text-[10px] text-slate-500 mt-1">Spark Tokens</p>
              </div>
              <div className="p-5 rounded-2xl border border-blue-500/20" style={{ background: 'linear-gradient(135deg, rgba(59,130,246,0.08), rgba(99,102,241,0.04))' }}>
                <CreditCard className="w-5 h-5 text-blue-400 mb-2" />
                <p className="text-2xl font-bold text-white">{wallet?.credits || 0}</p>
                <p className="text-[10px] text-slate-500 mt-1">Credits</p>
              </div>
              <div className="p-5 rounded-2xl border border-green-500/20" style={{ background: 'linear-gradient(135deg, rgba(34,197,94,0.08), rgba(16,185,129,0.04))' }}>
                <TrendingUp className="w-5 h-5 text-green-400 mb-2" />
                <p className="text-2xl font-bold text-white">{wallet?.balance_eur?.toFixed(2) || '0.00'}</p>
                <p className="text-[10px] text-slate-500 mt-1">Saldo (EUR)</p>
              </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-slate-900/50 border border-slate-800 rounded-xl text-center">
                <p className="text-sm font-bold text-green-400">{wallet?.earned_total?.toFixed(2) || '0.00'}</p>
                <p className="text-[10px] text-slate-500">Totaal gestort</p>
              </div>
              <div className="p-3 bg-slate-900/50 border border-slate-800 rounded-xl text-center">
                <p className="text-sm font-bold text-red-400">{wallet?.total_withdrawn?.toFixed(2) || '0.00'}</p>
                <p className="text-[10px] text-slate-500">Opgenomen</p>
              </div>
              <div className="p-3 bg-slate-900/50 border border-slate-800 rounded-xl text-center">
                <p className="text-sm font-bold text-amber-400">{wallet?.activity_score || 0}</p>
                <p className="text-[10px] text-slate-500">Activiteit Score</p>
              </div>
            </div>

            {/* Entities overview */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-amber-400" /> Entiteiten
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(entities).map(([id, ent]) => {
                  const colors = { amber: '#f59e0b', blue: '#3b82f6', green: '#22c55e', purple: '#a855f7', gray: '#64748b' };
                  const c = colors[ent.color] || colors.blue;
                  return (
                    <div key={id} className="p-3 bg-slate-800/30 rounded-xl border border-slate-700/30">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: c }} />
                        <h4 className="text-xs text-white font-medium">{ent.name}</h4>
                      </div>
                      <p className="text-[10px] text-slate-500">{ent.type} | {ent.description?.slice(0, 40)}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Recent transactions */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-400" /> Recente Transacties
              </h3>
              {transactions.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-4">Nog geen transacties</p>
              ) : (
                <div className="space-y-2">
                  {transactions.slice(0, 10).map(tx => (
                    <div key={tx.id} className="flex items-center gap-3 p-2.5 bg-slate-800/30 rounded-lg">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${tx.type === 'deposit' ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                        {tx.type === 'deposit' ? <ArrowDownLeft className="w-4 h-4 text-green-400" /> : <ArrowUpRight className="w-4 h-4 text-red-400" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-white truncate">{tx.message || tx.type}</p>
                        <p className="text-[10px] text-slate-500">{tx.created_at ? new Date(tx.created_at).toLocaleDateString('nl-NL') : '?'}</p>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-medium ${tx.type === 'deposit' ? 'text-green-400' : 'text-red-400'}`}>
                          {tx.type === 'deposit' ? '+' : '-'}{tx.amount?.toFixed(2)}
                        </p>
                        <p className="text-[10px] text-slate-600">{tx.status}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default WalletPage;
