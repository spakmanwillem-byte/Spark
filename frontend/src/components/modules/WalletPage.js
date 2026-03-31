import React, { useState } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Wallet, ArrowUpRight, ArrowDownLeft, TrendingUp, CreditCard,
  Plus, Search, Filter, ChevronDown, Star, Coins, PiggyBank,
  ArrowUpDown, CircleDollarSign, Banknote, Receipt, Gift
} from 'lucide-react';

// Mocked wallet data (gebaseerd op oude v1 structuur)
const walletData = {
  spark_tokens: 1000,
  credits: 250,
  balance_eur: 15.40,
  earned_total: 20.32,
  activity_score: 1500,
  savings_goal: 50,
};

const transactions = [
  { id: 1, type: 'incoming', title: 'XP Achievement Bonus', desc: 'Keeper van het Woord unlocked', amount: 100, currency: 'tokens', date: '31 mrt 2026', time: '22:14' },
  { id: 2, type: 'outgoing', title: 'Module Activatie', desc: 'Trader Pro module', amount: 50, currency: 'credits', date: '30 mrt 2026', time: '14:30' },
  { id: 3, type: 'incoming', title: 'Kennisbank Bijdrage', desc: '25 nieuwe kaarten toegevoegd', amount: 250, currency: 'tokens', date: '28 mrt 2026', time: '09:15' },
  { id: 4, type: 'outgoing', title: 'Donatie aan Community', desc: 'Open source fonds', amount: 5.20, currency: 'eur', date: '25 mrt 2026', time: '16:45' },
  { id: 5, type: 'incoming', title: 'Dagelijkse Login Bonus', desc: '7 dagen streak', amount: 75, currency: 'tokens', date: '24 mrt 2026', time: '08:00' },
  { id: 6, type: 'incoming', title: 'Storting Ontvangen', desc: 'Bank overboeking', amount: 10.12, currency: 'eur', date: '22 mrt 2026', time: '11:30' },
  { id: 7, type: 'outgoing', title: 'Spark Skin Gekocht', desc: 'Gold theme pack', amount: 200, currency: 'tokens', date: '20 mrt 2026', time: '19:00' },
];

const weeklyData = [
  { day: 'Ma', tokens: 120, credits: 30 },
  { day: 'Di', tokens: 85, credits: 15 },
  { day: 'Wo', tokens: 200, credits: 45 },
  { day: 'Do', tokens: 150, credits: 20 },
  { day: 'Vr', tokens: 310, credits: 60 },
  { day: 'Za', tokens: 95, credits: 10 },
  { day: 'Zo', tokens: 40, credits: 5 },
];

export function WalletPage({ onNavigate }) {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  const maxBar = Math.max(...weeklyData.map(d => d.tokens + d.credits));
  const savingsPct = Math.round((walletData.balance_eur / walletData.savings_goal) * 100);

  const filtered = transactions.filter(t => {
    if (filterType === 'incoming' && t.type !== 'incoming') return false;
    if (filterType === 'outgoing' && t.type !== 'outgoing') return false;
    if (searchTerm && !t.title.toLowerCase().includes(searchTerm.toLowerCase()) && !t.desc.toLowerCase().includes(searchTerm.toLowerCase())) return false;
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
              <p className="text-xs text-slate-500">Persoonlijk financieel overzicht</p>
            </div>
          </div>
          <button data-testid="add-funds-btn" className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white transition-all" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
            <Plus className="w-4 h-4" /> Storten
          </button>
        </div>

        {/* Top Row: Income / Expenses / Total Balance */}
        <div className="grid grid-cols-12 gap-4">

          {/* Income + Expenses */}
          <div className="col-span-12 md:col-span-5 grid grid-cols-2 gap-3">
            <StatCard
              label="Inkomsten"
              icon={ArrowDownLeft}
              value={walletData.spark_tokens.toLocaleString()}
              unit="tokens"
              change="+2.5%"
              changePositive
              sub="Spark Tokens verdiend"
              color="#22c55e"
            />
            <StatCard
              label="Uitgaven"
              icon={ArrowUpRight}
              value={walletData.credits.toLocaleString()}
              unit="credits"
              change="+1.2%"
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
                    <span className="text-3xl font-bold text-white">&euro;{walletData.balance_eur.toFixed(2)}</span>
                    <span className="text-xs text-green-400 flex items-center gap-0.5">
                      <TrendingUp className="w-3 h-3" /> +2.5%
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Vergeleken met vorige maand (&euro;{(walletData.balance_eur * 0.975).toFixed(2)})</p>
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
                <MiniAsset icon={Coins} label="Tokens" value={walletData.spark_tokens.toLocaleString()} color="#f59e0b" />
                <MiniAsset icon={Star} label="Credits" value={walletData.credits.toLocaleString()} color="#a855f7" />
                <MiniAsset icon={TrendingUp} label="Activity" value={walletData.activity_score.toLocaleString()} color="#06b6d4" />
                <MiniAsset icon={CircleDollarSign} label="Verdiend" value={`\u20AC${walletData.earned_total.toFixed(2)}`} color="#22c55e" />
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
                    <option value="incoming">Inkomend</option>
                    <option value="outgoing">Uitgaand</option>
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
                          <div className="w-full rounded-t" style={{ height: `${(d.tokens / maxBar) * 80}px`, background: '#f59e0b' }} />
                          <div className="w-full rounded-b" style={{ height: `${(d.credits / maxBar) * 80}px`, background: '#a855f7' }} />
                        </div>
                      </div>
                      <span className="text-[10px] text-slate-500">{d.day}</span>
                    </div>
                  ))}
                </div>
                <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-800">
                  <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
                    <span className="w-2 h-2 rounded-sm bg-amber-500" /> Tokens
                  </span>
                  <span className="flex items-center gap-1.5 text-[10px] text-slate-400">
                    <span className="w-2 h-2 rounded-sm bg-purple-500" /> Credits
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
                    <p className="text-sm text-white font-medium">{user?.naam || 'De Willem'}</p>
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
                <PaymentMethod label="Tokens" sub="Intern saldo" icon={Coins} />
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
  const isIn = tx.type === 'incoming';
  const currSymbol = tx.currency === 'eur' ? '\u20AC' : tx.currency === 'tokens' ? '' : '';
  const currSuffix = tx.currency === 'tokens' ? ' tokens' : tx.currency === 'credits' ? ' credits' : '';

  return (
    <div data-testid={`tx-${tx.id}`} className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-800/30 transition-colors">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${isIn ? 'bg-green-500/10' : 'bg-orange-500/10'}`}>
        {isIn
          ? <ArrowDownLeft className="w-4 h-4 text-green-400" />
          : <ArrowUpRight className="w-4 h-4 text-orange-400" />
        }
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white font-medium truncate">{tx.title}</p>
        <p className="text-[10px] text-slate-500">{tx.date} - {tx.time}</p>
      </div>
      <div className="text-right flex-shrink-0">
        <p className={`text-sm font-semibold ${isIn ? 'text-green-400' : 'text-orange-400'}`}>
          {isIn ? '+' : '-'}{currSymbol}{tx.amount.toLocaleString()}{currSuffix}
        </p>
        <p className="text-[10px] text-slate-600">{tx.desc}</p>
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
