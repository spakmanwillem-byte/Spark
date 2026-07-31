import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Wallet, ArrowUpRight, ArrowDownLeft, TrendingUp, CreditCard,
  Plus, Search, Star, Coins, PiggyBank,
  CircleDollarSign, Banknote, Receipt, Minus, Loader2, Gift
} from 'lucide-react';
import { TikkieTopupModal } from './TikkieTopupModal';

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

  // v5_roar_gift_001 — Gift state (verhuisd van Winkel naar Wallet)
  const [giftModalOpen, setGiftModalOpen] = useState(false);
  const [giftInbox, setGiftInbox] = useState([]);
  const [giftOutbox, setGiftOutbox] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  // v5_tikkie_topup_001 — Storten modal (admin-inbox staat nu in Boekhouden)
  const [showTikkie, setShowTikkie] = useState(false);
  // v6_spark_history_001 — Spark-specific transactie-papier (kasboek + treasury verkopen + self-mints)
  const [sparkHistory, setSparkHistory] = useState([]);

  const loadGifts = useCallback(() => {
    if (!userId) return;
    fetch(`${API}/api/shop/gift/inbox/${userId}`).then(r => r.json()).then(d => setGiftInbox(d.gifts || [])).catch(() => {});
    fetch(`${API}/api/shop/gift/outbox/${userId}`).then(r => r.json()).then(d => setGiftOutbox(d.gifts || [])).catch(() => {});
    fetch(`${API}/api/auth/users?viewer_id=${userId}`).then(r => r.json()).then(d => setAllUsers((d.users || []).filter(u => u.id !== userId))).catch(() => {});
  }, [userId]);

  useEffect(() => { loadGifts(); }, [loadGifts]);

  const loadData = () => {
    Promise.all([
      fetch(`${API}/api/wallet/user/${userId}`).then(r => r.json()).catch(() => ({})),
      fetch(`${API}/api/wallet/transactions/${userId}?limit=100`).then(r => r.json()).catch(() => ({ transactions: [] })),
      fetch(`${API}/api/shop/token/balance/${userId}`).then(r => r.json()).catch(() => null),
      // v6_spark_history_001 — combi-history voor Spark wallet view
      userId === 'user-000'
        ? fetch(`${API}/api/spark/kasboek/history?limit=100`).then(r => r.json()).catch(() => ({ history: [] }))
        : Promise.resolve({ history: [] }),
    ]).then(([w, t, r, sh]) => {
      setWallet(w);
      setTransactions(t.transactions || []);
      setRoar(r);
      setSparkHistory(sh.history || []);
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
              <p className="text-xs text-slate-500">{walletView === 'spark' && isAdmin ? "Spark's wallet (admin view)" : 'Persoonlijk financieel overzicht'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* v4_wallet_admin_switch_001 — admin kan switchen tussen eigen wallet en Spark wallet */}
            {isAdmin && (
              <div data-testid="wallet-view-switch" className="flex items-center gap-1 p-1 bg-slate-800/60 rounded-lg border border-slate-700">
                <button onClick={() => setWalletView('me')} data-testid="wallet-view-me"
                  className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${walletView === 'me' ? 'bg-amber-500/30 text-amber-200' : 'text-slate-400 hover:text-slate-200'}`}>
                  👤 Mijn
                </button>
                <button onClick={() => setWalletView('spark')} data-testid="wallet-view-spark"
                  className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${walletView === 'spark' ? 'bg-amber-500/30 text-amber-200' : 'text-slate-400 hover:text-slate-200'}`}>
                  🌟 Spark
                </button>
              </div>
            )}
            {/* v6_wallet_button_order_001 — Volgorde: Storten (+) → Opnemen (−) → [Mint admin] → Gift (rechts) */}
            <button data-testid="add-funds-btn" onClick={() => setShowTikkie(true)}
              className="flex items-center justify-center gap-2 px-4 h-10 min-w-[120px] rounded-xl text-sm font-medium text-white transition-all"
              style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
              <Plus className="w-4 h-4" /> Storten
            </button>
            <button data-testid="withdraw-btn" onClick={() => setShowWithdraw(!showWithdraw)}
              className="flex items-center justify-center gap-2 px-4 h-10 min-w-[120px] rounded-xl text-sm font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 transition-all border border-slate-700">
              <Minus className="w-4 h-4" /> Opnemen
            </button>
            {/* v6_mint_from_wallet_001 — Spark "Maak Token" knop, alleen in Spark wallet view */}
            {isAdmin && walletView === 'spark' && (
              <button
                data-testid="spark-mint-token-btn"
                onClick={async () => {
                  // v11_mint_bitvavo_ux_001 — Willems correctie: mint neemt Bitvavo saldo,
                  // niet Spark's EUR-wallet. Toon dus Bitvavo-free ipv wallet-balance.
                  let mintCost = null;
                  let bitvavoFree = null;
                  try {
                    const p = await fetch(`${API}/api/boekhouder/token/price`).then(x => x.json());
                    mintCost = p?.next_mint_threshold_eur ?? p?.base_pot_size_eur ?? null;
                    bitvavoFree = p?.bitvavo_free_eur ?? null;
                  } catch { /* fallback: null → UI toont '?' */ }
                  const costStr = mintCost !== null ? `€${mintCost.toFixed(2)}` : '?';
                  const balStr = bitvavoFree !== null ? `€${bitvavoFree.toFixed(2)}` : '?';
                  if (mintCost !== null && bitvavoFree !== null && bitvavoFree < mintCost) {
                    alert(
                      `🪙 Mint nog niet mogelijk\n\n` +
                      `Kosten volgende mint: ${costStr}\n` +
                      `Bitvavo saldo (vrij): ${balStr}\n` +
                      `Tekort: €${(mintCost - bitvavoFree).toFixed(2)}\n\n` +
                      `De mint neemt uit Bitvavo's vrije EUR. Wacht op meer ruis (SELL-winst of storting).`
                    );
                    return;
                  }
                  const ok = window.confirm(
                    `Spark mint 1 ROAR uit treasury.\n\n` +
                    `Kosten (papertrail): ${costStr}\n` +
                    `Bitvavo saldo: ${balStr}\n` +
                    `Effect: Circulating +1 · prijs stijgt voor holders\n\n` +
                    `Doorgaan?`
                  );
                  if (!ok) return;
                  try {
                    const r = await fetch(`${API}/api/spark/mint/from-wallet`, {
                      method: 'POST', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ viewer_id: user?.id || 'user-001', amount_tokens: 1 })
                    }).then(x => x.json());
                    if (r.success) {
                      alert(`🪙 Spark heeft 1 ROAR gemaakt!\n\nKosten: €${r.cost_eur}\nTreasury: ${r.new_treasury.toLocaleString()}\nSpark balance: ${r.new_spark_balance}\nBitvavo saldo (over): €${r.bitvavo_free_eur}`);
                      window.location.reload();
                    } else {
                      alert('🪙 Mint mislukt:\n\n' + (r.detail || 'Onbekende fout — check backend logs'));
                    }
                  } catch (e) { alert('Fout: ' + e.message); }
                }}
                className="flex items-center justify-center gap-2 px-4 h-10 min-w-[120px] rounded-xl text-sm font-medium text-emerald-200 bg-emerald-500/10 hover:bg-emerald-500/20 transition-all border border-emerald-500/30">
                🪙 Mint
              </button>
            )}
            {/* v6_wallet_button_order_001 — Gift altijd uiterst rechts */}
            <button
              data-testid="open-gift-modal"
              onClick={() => setGiftModalOpen(true)}
              disabled={(wallet?.spark_tokens || 0) < 1}
              title={(wallet?.spark_tokens || 0) < 1 ? 'Je hebt minimaal 1 ROAR nodig om te giften' : 'Stuur een ROAR token naar een andere user'}
              className="flex items-center justify-center gap-2 px-4 h-10 min-w-[120px] rounded-xl text-sm font-medium text-pink-300 bg-pink-500/10 hover:bg-pink-500/20 transition-all border border-pink-500/30 disabled:opacity-40 disabled:cursor-not-allowed">
              <Gift className="w-4 h-4" /> Gift
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

        {/* v5_roar_gift_001 — Inbox banner voor inkomende ROAR gifts */}
        {giftInbox.length > 0 && (
          <div data-testid="wallet-gift-inbox" className="bg-pink-500/10 border border-pink-500/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Gift className="w-4 h-4 text-pink-400" />
              <h3 className="text-sm font-semibold text-pink-300">Inkomende ROAR gift{giftInbox.length > 1 ? 's' : ''} ({giftInbox.length})</h3>
            </div>
            <div className="space-y-2">
              {giftInbox.map(g => (
                <GiftInboxRow key={g.id} gift={g} actorId={userId} onUpdated={() => { loadGifts(); loadData(); }} />
              ))}
            </div>
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

        {/* v6_price_chart_001 — token-prijs grafiek bovenaan transactie-paneel (Spark view only) */}
        {/* v6_token_chart_all_users_001 (28 mei) — ROAR koersgrafiek zichtbaar voor ALLE users (was admin-only) */}
        <TokenPriceChart />

        {/* Bottom Row: Transactions + Stats */}
        <div className="grid grid-cols-12 gap-4">

          {/* Transaction History */}
          <div className="col-span-12 lg:col-span-7 space-y-3">
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800/50 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Receipt className="w-4 h-4 text-amber-400" />
                  {walletView === 'spark' && isAdmin ? 'Spark Boekhouding (kasboek + treasury)' : 'Transactie Geschiedenis'}
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
                  {/* v6_spark_history_001 — in Spark-view tonen we kasboek + treasury verkopen + mints ipv gewone deposits */}
                  {walletView === 'spark' && isAdmin ? (
                    sparkHistory.length === 0 ? (
                      <div className="py-8 text-center text-slate-500 text-xs">Nog geen Spark-transacties</div>
                    ) : sparkHistory.map((h, i) => (
                      <div key={i} data-testid="spark-history-row" className="flex items-start justify-between px-3 py-2 hover:bg-slate-800/30 rounded-lg border-b border-slate-800/30 last:border-0">
                        <div className="flex-1 min-w-0">
                          <div className="text-xs text-white truncate">{h.label} · <span className="text-slate-400">{h.description}</span></div>
                          <div className="text-[10px] text-slate-500 mt-0.5">{(h.ts || '').slice(0, 16).replace('T', ' ')}{h.bron_user && ` · ${h.bron_user}`}</div>
                        </div>
                        <div className="text-right ml-2 shrink-0">
                          {h.amount_eur != null && (
                            <div className={`text-xs font-semibold ${h.amount_eur >= 0 ? 'text-emerald-300' : 'text-red-300'}`}>
                              {h.amount_eur >= 0 ? '+' : ''}€{h.amount_eur.toFixed(2)}
                            </div>
                          )}
                          {h.n_tokens != null && h.n_tokens !== 0 && (
                            <div className={`text-[10px] ${h.n_tokens >= 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                              {h.n_tokens >= 0 ? '+' : ''}{h.n_tokens} ROAR
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <>
                      {filtered.map(tx => (
                        <TransactionRow key={tx.id} tx={tx} />
                      ))}
                      {filtered.length === 0 && (
                        <div className="py-8 text-center text-slate-500 text-xs">Geen transacties gevonden</div>
                      )}
                    </>
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

      {/* v5_roar_gift_001 — Gift Modal */}
      {giftModalOpen && (
        <GiftModal
          senderId={userId}
          senderBalance={wallet?.spark_tokens || 0}
          users={allUsers}
          onClose={() => setGiftModalOpen(false)}
          onSent={() => { setGiftModalOpen(false); loadGifts(); loadData(); }}
        />
      )}
      {/* v5_tikkie_topup_001 — Tikkie storten modal (admin-inbox staat in Boekhouden) */}
      <TikkieTopupModal open={showTikkie} onClose={() => setShowTikkie(false)} user={user} />
    </MainLayout>
  );
}

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

// ============================================================
// v5_roar_gift_001 — Gift Modal + Inbox Row (verhuisd van Winkel naar Wallet)
// ============================================================
function GiftModal({ senderId, senderBalance, users, onClose, onSent }) {
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState(1);
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const send = async () => {
    setErr(null);
    if (!recipient) return setErr('Kies een ontvanger');
    const n = parseInt(amount, 10);
    if (!n || n < 1) return setErr('Aantal moet minstens 1 zijn');
    if (n > senderBalance) return setErr(`Je hebt maar ${senderBalance} ROAR`);
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/shop/gift`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender_id: senderId, recipient_id: recipient, amount: n, note: note.trim() || null }),
      });
      const d = await res.json().catch(() => ({}));
      if (res.ok && d.success) onSent();
      else setErr(d.detail || d.error || 'Versturen mislukt');
    } catch (e) { setErr(e.message || 'Netwerkfout'); }
    finally { setBusy(false); }
  };

  return (
    <div data-testid="gift-modal" className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-slate-900 border border-pink-500/30 rounded-2xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-pink-500/15 border border-pink-500/40 flex items-center justify-center">
            <Gift className="w-5 h-5 text-pink-400" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">ROAR Gift sturen</h3>
            <p className="text-[10px] text-slate-500">Je tokens worden pas overgemaakt na acceptatie · vervalt na 24u</p>
          </div>
        </div>
        <div className="space-y-3">
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">Ontvanger</label>
            <select data-testid="gift-recipient" value={recipient} onChange={e => setRecipient(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white">
              <option value="">— kies een user —</option>
              {users.map(u => <option key={u.id} value={u.id}>{u.naam} {u.is_bot ? '(bot)' : ''}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">Aantal tokens (1-{senderBalance})</label>
            <input data-testid="gift-amount" type="number" min="1" max={senderBalance} value={amount}
              onChange={e => setAmount(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white" />
          </div>
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-slate-500 mb-1">Notitie (optioneel)</label>
            <textarea data-testid="gift-note" value={note} onChange={e => setNote(e.target.value)} rows={2}
              placeholder="Bv. 'Welkom in de community!'"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500" />
          </div>
          {err && <p data-testid="gift-error" className="text-[11px] text-red-300 bg-red-500/10 border border-red-500/30 px-2 py-1.5 rounded">{err}</p>}
        </div>
        <div className="flex items-center gap-2 justify-end mt-5">
          <button onClick={onClose} className="px-3 py-2 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700">Annuleer</button>
          <button data-testid="gift-send-btn" onClick={send} disabled={busy || !recipient}
            className="px-3 py-2 rounded-lg text-xs font-medium bg-pink-500/20 text-pink-300 hover:bg-pink-500/30 border border-pink-500/40 disabled:opacity-40 flex items-center gap-2">
            <Gift className="w-3 h-3" /> {busy ? 'Versturen...' : 'Verstuur gift'}
          </button>
        </div>
      </div>
    </div>
  );
}

function GiftInboxRow({ gift, actorId, onUpdated }) {
  const [busy, setBusy] = useState(false);
  const act = async (action) => {
    if (action === 'reject' && !window.confirm(`Weet je zeker dat je deze gift wilt weigeren?`)) return;
    setBusy(true);
    try {
      await fetch(`${API}/api/shop/gift/${gift.id}/${action}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actor_id: actorId }),
      });
      onUpdated();
    } finally { setBusy(false); }
  };
  return (
    <div data-testid={`gift-row-${gift.id}`} className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/60 border border-pink-500/20">
      <div className="flex-1">
        <p className="text-xs font-semibold text-white">
          <span className="text-pink-300">{gift.sender_naam}</span> stuurt je <span className="text-amber-300">{gift.amount} ROAR</span>
        </p>
        {gift.note && <p className="text-[10px] text-slate-400 italic mt-0.5">"{gift.note}"</p>}
        <p className="text-[9px] text-slate-500 mt-0.5">Vervalt: {new Date(gift.expires_at).toLocaleString('nl-NL', { dateStyle: 'short', timeStyle: 'short' })}</p>
      </div>
      <button data-testid={`gift-accept-${gift.id}`} onClick={() => act('accept')} disabled={busy}
        className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 disabled:opacity-40">
        ✓ Accepteer
      </button>
      <button data-testid={`gift-reject-${gift.id}`} onClick={() => act('reject')} disabled={busy}
        className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40">
        ✕ Weiger
      </button>
    </div>
  );
}


// v6_price_chart_001 — Token-prijs grafiek met 2 lijnen (incl-BTW vs netto) + cycle-buttons
function TokenPriceChart() {
  const [interval, setInterval_] = useState('15m');
  const [points, setPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatedAt, setUpdatedAt] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      fetch(`${API}/api/spark/kasboek/price-history?interval=${interval}&limit=200`)
        .then(r => r.json())
        .then(d => {
          if (cancelled) return;
          setPoints(d.points || []);
          setUpdatedAt(new Date());
          setLoading(false);
        })
        .catch(() => { if (!cancelled) setLoading(false); });
    };
    load();
    // v6_price_chart_density_001 (sessie 15) — auto-refresh elke 30s
    const t = window.setInterval(load, 30000);
    return () => { cancelled = true; window.clearInterval(t); };
  }, [interval]);

  // v6_price_chart_density_001 — manueel snapshot triggeren als debug-knop
  const triggerSnapshot = async () => {
    try {
      await fetch(`${API}/api/spark/kasboek/price-snapshot`, { method: 'POST' });
      // Refresh
      const d = await fetch(`${API}/api/spark/kasboek/price-history?interval=${interval}&limit=200`).then(r => r.json());
      setPoints(d.points || []);
      setUpdatedAt(new Date());
    } catch {}
  };

  const W = 800, H = 180, P = 30;
  const prices = points.flatMap(p => [p.price_incl, p.price_netto]).filter(x => x > 0);
  // v6_price_chart_density_001 — tightere y-as: 1% padding ipv 8% zodat
  // kleine fluctuaties (€0.01 .. €0.50) zichtbaar worden. Bij volledig vlak
  // (alle prijzen identiek) val terug op ±2% zodat de lijn niet op de rand kleeft.
  const rawMin = prices.length ? Math.min(...prices) : 0;
  const rawMax = prices.length ? Math.max(...prices) : 1;
  const range = rawMax - rawMin;
  const padPct = range < 0.001 ? 0.02 : 0.01;
  const padAbs = Math.max(range * padPct, 0.005); // min 0.5 cent padding
  const minP = Math.max(0, rawMin - padAbs);
  const maxP = rawMax + padAbs;
  const x = i => P + ((W - 2 * P) * i) / Math.max(1, points.length - 1);
  const y = v => H - P - ((H - 2 * P) * (v - minP)) / Math.max(0.0001, maxP - minP);
  const path = key => points.length === 0 ? '' :
    points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${x(i)} ${y(p[key])}`).join(' ');

  const lastPrice = points.length ? points[points.length - 1].price_incl : null;
  const firstPrice = points.length ? points[0].price_incl : null;
  const deltaAbs = (lastPrice !== null && firstPrice !== null) ? lastPrice - firstPrice : 0;
  const deltaPct = firstPrice ? (deltaAbs / firstPrice) * 100 : 0;

  return (
    <div data-testid="token-price-chart" className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            📈 ROAR Token-prijs
            {lastPrice && (
              <span className="text-[10px] font-normal text-slate-400">
                · nu &euro;{lastPrice.toFixed(2)}
                {points.length > 1 && (
                  <span className={deltaAbs >= 0 ? ' text-emerald-400' : ' text-red-400'}>
                    {' '}({deltaAbs >= 0 ? '+' : ''}{deltaAbs.toFixed(2)} / {deltaPct >= 0 ? '+' : ''}{deltaPct.toFixed(2)}%)
                  </span>
                )}
              </span>
            )}
          </h3>
          <p className="text-[10px] text-slate-500">
            <span className="text-emerald-300">━━ Incl-BTW (klant)</span>
            {' · '}
            <span className="text-amber-300">━━ Netto (Spark ontvangt)</span>
            {updatedAt && <span> · ververst {updatedAt.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>}
          </p>
        </div>
        <div className="flex items-center gap-1 p-1 bg-slate-800/60 rounded-lg">
          {['15m', '1h', '4h', '1d'].map(iv => (
            <button key={iv} onClick={() => setInterval_(iv)} data-testid={`chart-cycle-${iv}`}
              className={`px-2 py-1 rounded text-[10px] font-medium ${interval === iv ? 'bg-amber-500/30 text-amber-200' : 'text-slate-400 hover:text-slate-200'}`}>
              {iv}
            </button>
          ))}
          <button onClick={triggerSnapshot} data-testid="chart-snapshot-now"
            className="px-2 py-1 rounded text-[10px] font-medium text-slate-400 hover:text-amber-300 border border-slate-700/50"
            title="Forceer nu een prijs-snapshot">
            +
          </button>
        </div>
      </div>
      {loading ? (
        <div className="py-8 text-center text-slate-500 text-xs">Prijs-historie laden...</div>
      ) : points.length === 0 ? (
        <div className="py-8 text-center text-slate-500 text-xs">
          Nog geen prijs-historie op dit interval.<br />
          <span className="text-[10px]">Klik op + om nu een snapshot te maken, of wacht 5 min op de volgende automatische snapshot.</span>
        </div>
      ) : (
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
          {/* Grid */}
          {[0, 0.25, 0.5, 0.75, 1].map(t => (
            <line key={t} x1={P} y1={P + (H - 2 * P) * t} x2={W - P} y2={P + (H - 2 * P) * t} stroke="#1e293b" strokeWidth="1" />
          ))}
          {/* Y-axis labels */}
          {[0, 0.5, 1].map(t => {
            const v = maxP - (maxP - minP) * t;
            return <text key={t} x={W - P + 4} y={P + (H - 2 * P) * t + 3} fill="#64748b" fontSize="9">€{v.toFixed(2)}</text>;
          })}
          {/* Lines */}
          <path d={path('price_netto')} stroke="#f59e0b" strokeWidth="2" fill="none" />
          <path d={path('price_incl')} stroke="#10b981" strokeWidth="2" fill="none" />
          {/* Dots */}
          {points.map((p, i) => (
            <g key={i}>
              <circle cx={x(i)} cy={y(p.price_incl)} r="3" fill="#10b981" />
              <circle cx={x(i)} cy={y(p.price_netto)} r="3" fill="#f59e0b" />
            </g>
          ))}
          {/* X-axis dates */}
          {points.map((p, i) => i % Math.max(1, Math.floor(points.length / 5)) === 0 && (
            <text key={i} x={x(i)} y={H - 8} fill="#64748b" fontSize="9" textAnchor="middle">
              {(p.ts || '').slice(5, 16).replace('T', ' ')}
            </text>
          ))}
        </svg>
      )}
    </div>
  );
}
