import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Wallet, ArrowUpRight, ArrowDownLeft, TrendingUp, CreditCard,
  Plus, Search, Star, Coins, PiggyBank,
  CircleDollarSign, Banknote, Receipt, Minus, Loader2
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function WalletPage({ onNavigate }) {
  const { user } = useAuth();
  const isAdmin = (user?.gradatie ?? 7) <= 1;
  // v4_wallet_admin_switch_001 — admin kan tussen eigen wallet en Spark wallet switchen
  const [walletView, setWalletView] = useState(() =>
    sessionStorage.getItem('wallet_view') || 'me'
  );
  const userId = walletView === 'spark' && isAdmin ? 'user-000' : (user?.id || 'user-001');
  useEffect(() => { if (isAdmin) sessionStorage.setItem('wallet_view', walletView); }, [walletView, isAdmin]);
  const [wallet, setWallet] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [showWithdraw, setShowWithdraw] = useState(false);
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [withdrawing, setWithdrawing] = useState(false);
  const [roar, setRoar] = useState(null);

  const loadData = () => {
    Promise.all([
      fetch(`${API}/api/wallet/user/${userId}`).then(r => r.json()).catch(() => ({})),
      fetch(`${API}/api/wallet/transactions/${userId}?limit=100`).then(r => r.json()).catch(() => ({ transactions: [] })),
      fetch(`${API}/api/shop/token/balance/${userId}`).then(r => r.json()).catch(() => null),
    ]).then(([w, t, r]) => {
      setWallet(w);
      setTransactions(t.transactions || []);
      setRoar(r);
      setLoading(false);
    });
  };

  useEffect(() => { loadData(); }, [userId]);

  const handleWithdraw = async () => {
    const amt = parseFloat(withdrawAmount);
    if (!amt || amt <= 0) return;
    setWithdrawing(true);
    await fetch(`${API}/api/wallet/withdraw/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: amt, message: 'Opname via wallet' }),
    });
    setWithdrawing(false);
    setShowWithdraw(false);
    setWithdrawAmount('');
    loadData();
  };

  if (loading) return (
    <MainLayout activePage="wallet" onNavigate={onNavigate}>
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
      </div>
    </MainLayout>
  );

  const savingsGoal = 50;
  const savingsPct = wallet ? Math.min(100, Math.round((wallet.balance_eur / savingsGoal) * 100)) : 0;

  // Build weekly overview from transactions
  const days = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
  const weeklyData = days.map((day, i) => {
    const dayTxs = transactions.filter(tx => {
      if (!tx.created_at) return false;
      const d = new Date(tx.created_at);
      return d.getDay() === (i === 6 ? 0 : i + 1);
    });
    const deposits = dayTxs.filter(t => t.type === 'deposit').reduce((s, t) => s + (t.amount || 0), 0);
    const withdrawals = dayTxs.filter(t => t.type === 'withdrawal').reduce((s, t) => s + (t.amount || 0), 0);
    return { day, deposits: deposits || (i % 3 === 0 ? 10 : 5), withdrawals: withdrawals || (i % 4 === 0 ? 3 : 1) };
  });
  const maxBar = Math.max(...weeklyData.map(d => d.deposits + d.withdrawals), 1);

  const filtered = transactions.filter(t => {
    if (filterType === 'incoming' && t.type !== 'deposit') return false;
    if (filterType === 'outgoing' && t.type !== 'withdrawal') return false;
    if (searchTerm && !(t.message || '').toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  return (
    <MainLayout activePage="wallet" onNavigate={onNavigate}>
      <div data-testid="wallet-page" className="p-4 md:p-6 space-y-5 max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
              <Wallet className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Wallet</h1>
              <p className="text-xs text-slate-500">{walletView === 'spark' && isAdmin ? 'Persoonlijk financieel overzicht' : "Spark's wallet (admin view)"}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* v4_wallet_admin_switch_001 — admin kan switchen tussen eigen wallet en Spark wallet */}
            {isAdmin && (
              <div data-testid="wallet-view-switch" className="flex items-center gap-1 p-1 bg-slate-800/60 rounded-lg border border-slate-700">
                <button onClick={() => setWalletView('me')} data-testid="wallet-view-me"
                  className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${walletView === 'me' ? 'bg-amber-500/30 text-amber-200' : 'text-slate-400 hover:text-slate-200'}`}>
                  🌟 Spark
                </button>
                <button onClick={() => setWalletView('spark')} data-testid="wallet-view-spark"
                  className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${walletView === 'spark' ? 'bg-amber-500/30 text-amber-200' : 'text-slate-400 hover:text-slate-200'}`}>
                  👤 Mijn
                </button>
              </div>
            )}
            <button data-testid="withdraw-btn" onClick={() => setShowWithdraw(!showWithdraw)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 transition-all border border-slate-700">
              <Minus className="w-4 h-4" /> Opnemen
            </button>
            <button data-testid="add-funds-btn" className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white transition-all" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
              <Plus className="w-4 h-4" /> Storten
            </button>
          </div>
        </div>

        {/* Withdraw panel */}
        {showWithdraw && (
          <div className="bg-slate-900/80 border border-amber-500/20 rounded-xl p-4 flex items-center gap-3">
            <input data-testid="withdraw-amount" type="number" value={withdrawAmount} onChange={e => setWithdrawAmount(e.target.value)}
              placeholder="Bedrag in EUR..." min="0" step="0.01"
              className="flex-1 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/30" />
            <button data-testid="withdraw-confirm" onClick={handleWithdraw} disabled={withdrawing}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white bg-red-500/80 hover:bg-red-500 transition-colors disabled:opacity-50">
              {withdrawing ? 'Bezig...' : 'Opnemen'}
            </button>
          </div>
        )}

        {/* Top Row: Income / Expenses / Total Balance */}
        <div className="grid grid-cols-12 gap-4">

          {/* Income + Expenses */}
          <div className="col-span-12 md:col-span-5 grid grid-cols-2 gap-3">
            <StatCard
              label="Inkomsten"
              icon={ArrowDownLeft}
              value={(wallet?.spark_tokens || 0).toLocaleString()}
              unit="tokens"
              change="+2.5%"
              changePositive
              sub="Spark Tokens verdiend"
              color="#22c55e"
            />
            <StatCard
              label="Uitgaven"
              icon={ArrowUpRight}
              value={(wallet?.credits || 0).toLocaleString()}
              unit="credits"
              change={`-${wallet?.total_withdrawn?.toFixed(1) || '0.0'}`}
              changePositive={false}
              sub="Credits gebruikt"
              color="#f97316"
            />
          </div>

          {/* Total Balance */}
          <div className="col-span-12 md:col-span-7">
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Totaal Saldo</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-white">&euro;{(wallet?.balance_eur || 0).toFixed(2)}</span>
                    <span className={`text-xs flex items-center gap-0.5 ${wallet?.total_withdrawn > 0 ? 'text-orange-400' : 'text-green-400'}`}>
                      <TrendingUp className="w-3 h-3" /> {wallet?.total_withdrawn > 0 ? `-${wallet.total_withdrawn.toFixed(2)}` : '+0.00'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Gestort: &euro;{(wallet?.earned_total || 0).toFixed(2)} | Opgenomen: &euro;{(wallet?.total_withdrawn || 0).toFixed(2)}</p>
                </div>
                {/* Donut chart */}
                <div className="relative w-20 h-20 flex-shrink-0">
                  <svg className="w-20 h-20 -rotate-90" viewBox="0 0 36 36">
                    <circle cx="18" cy="18" r="14" fill="none" stroke="#1e293b" strokeWidth="3" />
                    <circle cx="18" cy="18" r="14" fill="none" stroke="#f59e0b" strokeWidth="3"
                      strokeDasharray={`${savingsPct * 0.88} 88`} strokeLinecap="round" />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-sm font-bold text-white">{savingsPct}%</span>
                    <span className="text-[8px] text-slate-500">Spaardoel</span>
                  </div>
                </div>
              </div>
              {/* Quick assets */}
              <div className="flex gap-4 mt-4 pt-3 border-t border-slate-800">
                <MiniAsset icon={Coins} label="ROAR Tokens" value={roar ? roar.roar_balance.toString() : '0'} color="#f59e0b" />
                <MiniAsset icon={Star} label="ROAR Waarde" value={roar ? `\u20AC${roar.value_eur.toFixed(2)}` : '\u20AC0'} color="#a855f7" />
                <MiniAsset icon={TrendingUp} label="Token Prijs" value={roar ? `\u20AC${roar.price_per_token.toFixed(2)}` : '\u20AC5.08'} color="#06b6d4" />
                <MiniAsset icon={CircleDollarSign} label="Verdiend" value={`\u20AC${(wallet?.earned_total || 0).toFixed(2)}`} color="#22c55e" />
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Row: Transactions + Stats */}
        <div className="grid grid-cols-12 gap-4">

          {/* Transaction History */}
          <div className="col-span-12 lg:col-span-7 space-y-3">
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800/50 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Receipt className="w-4 h-4 text-amber-400" /> Transactie Geschiedenis
                </h3>
                <div className="flex items-center gap-2">
                  <select
                    data-testid="tx-filter"
                    value={filterType}
                    onChange={e => setFilterType(e.target.value)}
                    className="px-2 py-1 bg-slate-800/50 border border-slate-700/50 rounded-lg text-[10px] text-slate-300 focus:outline-none"
                  >
                    <option value="all">Alles</option>
                    <option value="incoming">Stortingen</option>
                    <option value="outgoing">Opnames</option>
                  </select>
                </div>
              </div>
              <div className="p-2">
                <div className="relative mb-2">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                  <input
                    data-testid="tx-search"
                    type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                    placeholder="Zoek transactie..."
                    className="w-full pl-8 pr-3 py-2 bg-slate-800/30 border border-slate-700/30 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/30"
                  />
                </div>
                <div className="space-y-1 max-h-[420px] overflow-y-auto">
                  {filtered.map(tx => (
                    <TransactionRow key={tx.id} tx={tx} />
                  ))}
                  {filtered.length === 0 && (
                    <div className="py-8 text-center text-slate-500 text-xs">Geen transacties gevonden</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right column: Weekly chart + Card */}
          <div className="col-span-12 lg:col-span-5 space-y-4">

            {/* Weekly Bar Chart */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800/50 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <PiggyBank className="w-4 h-4 text-amber-400" /> Wekelijks Overzicht
                </h3>
                <span className="text-[10px] text-slate-500">Deze week</span>
              </div>
              <div className="p-4">
                <div className="flex items-end justify-between gap-2 h-36">
                  {weeklyData.map((d, i) => (
                    <div key={i} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full flex flex-col items-center gap-0.5" style={{ height: '100px' }}>
                        <div className="w-full flex flex-col justify-end h-full gap-0.5">
                          <div className="w-full rounded-t" style={{ height: `${(d.deposits / maxBar) * 80}px`, background: '#f59e0b' }} />
                          <div className="w-full rounded-b" style={{ height: `${(d.withdrawals / maxBar) * 80}px`, background: '#a855f7' }} />
                        </div>
                      </div>
                      <span className="text-[10px] text-slate-500">{d.day}</span>
                    </div>
                  ))}
                </div>
                <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-800">
                  <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
                    <span className="w-2 h-2 rounded-sm bg-amber-500" /> Stortingen
                  </span>
                  <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
                    <span className="w-2 h-2 rounded-sm bg-purple-500" /> Opnames
                  </span>
                </div>
              </div>
            </div>

            {/* Spark Card */}
            <div className="rounded-xl overflow-hidden" style={{ background: 'linear-gradient(135deg, #1a1333 0%, #f59e0b20 50%, #ea580c20 100%)' }}>
              <div className="p-5 border border-amber-500/20 rounded-xl">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <CreditCard className="w-5 h-5 text-amber-400" />
                    <span className="text-sm font-semibold text-white">Spark Card</span>
                  </div>
                  <span className="text-[10px] text-amber-400/60">SPARK CORE</span>
                </div>
                <div className="mb-6">
                  <p className="text-lg font-mono text-slate-300 tracking-[0.2em]">
                    4 217 &bull;&bull;&bull;&bull; &bull;&bull;&bull;&bull; 0842
                  </p>
                </div>
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase">Kaarthouder</p>
                    <p className="text-sm text-white font-medium">{wallet?.name || user?.naam || 'De Willem'}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-slate-500 uppercase">Geldig tot</p>
                    <p className="text-sm text-white font-medium">12/28</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Payment Methods */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800/50">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Banknote className="w-4 h-4 text-amber-400" /> Betaalmethoden
                </h3>
              </div>
              <div className="p-4 space-y-2">
                <PaymentMethod label="Spark Card" sub="**** 0842" active icon={CreditCard} />
                <PaymentMethod label="Bank Overboeking" sub="NL12 ABCD ****" icon={Banknote} />
                <PaymentMethod label="Tokens" sub={roar ? `${roar.roar_balance} ROAR (\u20AC${roar.value_eur.toFixed(2)})` : '0 ROAR'} icon={Coins} />
                <button className="w-full py-2 text-xs text-slate-500 hover:text-amber-400 transition-colors flex items-center justify-center gap-1">
                  <Plus className="w-3 h-3" /> Methode Toevoegen
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

/* === Sub components === */

function StatCard({ label, icon: Icon, value, unit, change, changePositive, sub, color }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</p>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${color}15` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-white">{value}</span>
        <span className="text-[10px] text-slate-500">{unit}</span>
      </div>
      <div className="flex items-center gap-1.5 mt-1.5">
        <span className={`text-[10px] font-medium ${changePositive ? 'text-green-400' : 'text-orange-400'}`}>{change}</span>
      </div>
      <p className="text-[10px] text-slate-600 mt-1">{sub}</p>
    </div>
  );
}

function MiniAsset({ icon: Icon, label, value, color }) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="w-3.5 h-3.5" style={{ color }} />
      <div>
        <p className="text-xs text-white font-medium">{value}</p>
        <p className="text-[9px] text-slate-500">{label}</p>
      </div>
    </div>
  );
}

function TransactionRow({ tx }) {
  const isDeposit = tx.type === 'deposit' || tx.type === 'buy_roar';
  const amount = tx.amount || tx.amount_eur || 0;
  const label = tx.message || tx.description || tx.type;

  return (
    <div data-testid={`tx-${tx.id}`} className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-800/30 transition-colors">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${isDeposit ? 'bg-green-500/10' : 'bg-orange-500/10'}`}>
        {isDeposit
          ? <ArrowDownLeft className="w-4 h-4 text-green-400" />
          : <ArrowUpRight className="w-4 h-4 text-orange-400" />
        }
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white font-medium truncate">{label}</p>
        <p className="text-[10px] text-slate-500">
          {(tx.created_at || tx.timestamp) ? new Date(tx.created_at || tx.timestamp).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' }) : '?'}
          {(tx.created_at || tx.timestamp) ? ` - ${new Date(tx.created_at || tx.timestamp).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}` : ''}
        </p>
      </div>
      <div className="text-right flex-shrink-0">
        <p className={`text-sm font-semibold ${isDeposit ? 'text-green-400' : 'text-orange-400'}`}>
          {isDeposit ? '+' : '-'}&euro;{amount.toFixed(2)}
        </p>
        <p className="text-[10px] text-slate-600">{tx.status || 'completed'}</p>
      </div>
    </div>
  );
}

function PaymentMethod({ label, sub, active, icon: Icon }) {
  return (
    <div className={`flex items-center gap-3 p-3 rounded-xl border transition-colors ${active ? 'border-amber-500/30 bg-amber-500/5' : 'border-slate-800 bg-slate-800/20 hover:bg-slate-800/40'}`}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${active ? 'bg-amber-500/15' : 'bg-slate-800'}`}>
        <Icon className={`w-4 h-4 ${active ? 'text-amber-400' : 'text-slate-500'}`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-white">{label}</p>
        <p className="text-[10px] text-slate-500">{sub}</p>
      </div>
      {active && <span className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0" />}
    </div>
  );
}

export default WalletPage;
