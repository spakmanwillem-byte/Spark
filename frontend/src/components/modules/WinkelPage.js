import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Coins, TrendingUp, ArrowUpRight, ArrowDownRight,
  ShoppingBag, PieChart, Clock, Loader2,
  Plus, Minus, DollarSign, BarChart2, History
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function WinkelPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [tokenInfo, setTokenInfo] = useState(null);
  const [userBalance, setUserBalance] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Buy/Sell state
  const [mode, setMode] = useState('buy'); // buy or sell
  const [inputEur, setInputEur] = useState('');
  const [inputTokens, setInputTokens] = useState('');
  const [inputMode, setInputMode] = useState('eur'); // eur or tokens
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);

  const loadData = useCallback(() => {
    Promise.all([
      fetch(`${API}/api/shop/token/price`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/shop/token/balance/${userId}`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/shop/token/history/${userId}`).then(r => r.json()).catch(() => ({ transactions: [] })),
    ]).then(([price, bal, hist]) => {
      setTokenInfo(price);
      setUserBalance(bal);
      setHistory(hist.transactions || []);
      setLoading(false);
    });
  }, [userId]);

  useEffect(() => { loadData(); }, [loadData]);

  // Auto-calculate - alleen hele tokens
  const price = tokenInfo?.price_eur || 5.08;
  const isFixed = tokenInfo?.price_model === 'fixed';
  const tokensUntilDynamic = tokenInfo?.tokens_until_dynamic || 0;
  const eurVal = inputMode === 'eur' ? parseFloat(inputEur) || 0 : (parseInt(inputTokens) || 0) * price;
  const tokenVal = inputMode === 'tokens' ? parseInt(inputTokens) || 0 : Math.floor((parseFloat(inputEur) || 0) / price);

  const executeTrade = async () => {
    if (tokenVal <= 0) return;
    setExecuting(true); setResult(null);
    const endpoint = mode === 'buy' ? 'buy' : 'sell';
    const body = { amount_tokens: tokenVal };

    const res = await fetch(`${API}/api/shop/token/${endpoint}/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(r => r.json()).catch(() => ({ success: false, error: 'Verbinding mislukt' }));

    setResult(res);
    setExecuting(false);
    if (res.success) {
      setInputEur(''); setInputTokens('');
      loadData();
    }
  };

  if (loading) return (
    <MainLayout activePage="winkel" onNavigate={onNavigate}>
      <div className="flex items-center justify-center h-full"><Loader2 className="w-8 h-8 text-amber-500 animate-spin" /></div>
    </MainLayout>
  );

  const roarBal = userBalance?.roar_balance || 0;
  const roarValEur = userBalance?.value_eur || 0;
  const circulating = tokenInfo?.circulating || 0;
  const marketCap = tokenInfo?.market_cap || 0;

  return (
    <MainLayout activePage="winkel" onNavigate={onNavigate}>
      <div data-testid="winkel-page" className="p-4 md:p-6 space-y-4 max-w-5xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
              <Coins className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">ROAR Token Winkel</h1>
              <p className="text-xs text-slate-400">Koop & verkoop tokens | Dynamische prijs</p>
            </div>
          </div>
        </div>

        {/* Top Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Token Prijs" value={`\u20AC${price.toFixed(2)}`} sub={`Basis: \u20AC${tokenInfo?.base_price || 5.08}`} icon={DollarSign} color="#f59e0b" />
          <StatCard label="Jouw ROAR" value={roarBal.toFixed(2)} sub={`Waarde: \u20AC${roarValEur.toFixed(2)}`} icon={Coins} color="#a855f7" />
          <StatCard label="In Omloop" value={circulating.toLocaleString()} sub={`van ${(tokenInfo?.total_supply || 0).toLocaleString()}`} icon={PieChart} color="#06b6d4" />
          <StatCard label="Market Cap" value={`\u20AC${marketCap.toFixed(2)}`} sub="Totale waarde" icon={BarChart2} color="#22c55e" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

          {/* Left: Buy/Sell Panel */}
          <div className="lg:col-span-5 space-y-4">

            {/* Token Info Card */}
            <div className="rounded-xl overflow-hidden" style={{ background: 'linear-gradient(135deg, #1a1333 0%, #f59e0b15 50%, #ea580c10 100%)' }}>
              <div className="p-5 border border-amber-500/20 rounded-xl">
                <div className="text-center mb-4">
                  <div className="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
                    <span className="text-2xl font-black text-white">R</span>
                  </div>
                  <h2 className="text-lg font-bold text-white">ROAR</h2>
                  <p className="text-xs text-slate-400">Spark Core Aandeel Token</p>
                  <p className="text-3xl font-bold text-amber-400 mt-2">&euro;{price.toFixed(2)}</p>
                  <p className="text-[10px] text-slate-500 mt-1">
                    {isFixed ? `Vaste prijs (nog ${tokensUntilDynamic} tokens)` : 'Dynamische prijs = Spark Core / tokens'}
                  </p>
                  {tokenInfo?.bitvavo_balance > 0 && (
                    <p className="text-[10px] text-cyan-400 mt-1">Bitvavo: &euro;{tokenInfo.bitvavo_balance.toFixed(2)}</p>
                  )}
                </div>
                <div className="flex items-center justify-between text-[10px] text-slate-400 pt-3 border-t border-slate-800">
                  <span>Jouw bezit: <b className="text-white">{roarBal} ROAR</b></span>
                  <span>Waarde: <b className="text-amber-400">&euro;{roarValEur.toFixed(2)}</b></span>
                </div>
              </div>
            </div>

            {/* Buy/Sell Form */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
              <div className="flex">
                <button data-testid="mode-buy" onClick={() => setMode('buy')}
                  className={`flex-1 py-3 text-sm font-medium text-center transition-colors ${mode === 'buy' ? 'bg-green-500/20 text-green-400 border-b-2 border-green-400' : 'text-slate-500 hover:text-slate-300'}`}>
                  <Plus className="w-4 h-4 inline mr-1" /> Kopen
                </button>
                <button data-testid="mode-sell" onClick={() => setMode('sell')}
                  className={`flex-1 py-3 text-sm font-medium text-center transition-colors ${mode === 'sell' ? 'bg-red-500/20 text-red-400 border-b-2 border-red-400' : 'text-slate-500 hover:text-slate-300'}`}>
                  <Minus className="w-4 h-4 inline mr-1" /> Verkopen
                </button>
              </div>
              <div className="p-4 space-y-3">
                {/* Input toggle */}
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="text-slate-500">Invoer:</span>
                  <button onClick={() => setInputMode('eur')}
                    className={`px-2 py-1 rounded ${inputMode === 'eur' ? 'bg-amber-500/20 text-amber-400' : 'text-slate-500'}`}>EUR</button>
                  <button onClick={() => setInputMode('tokens')}
                    className={`px-2 py-1 rounded ${inputMode === 'tokens' ? 'bg-amber-500/20 text-amber-400' : 'text-slate-500'}`}>Tokens</button>
                </div>

                {inputMode === 'eur' ? (
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Bedrag in EUR</label>
                    <input data-testid="input-eur" type="number" value={inputEur} onChange={e => setInputEur(e.target.value)}
                      placeholder={price.toFixed(2)} step="0.01" min="0"
                      className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm placeholder-slate-500 focus:outline-none focus:border-amber-500" />
                    <p className="text-[10px] text-slate-500 mt-1">= {tokenVal} ROAR tokens (hele tokens)</p>
                  </div>
                ) : (
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Aantal Tokens (heel)</label>
                    <input data-testid="input-tokens" type="number" value={inputTokens} onChange={e => setInputTokens(e.target.value)}
                      placeholder="1" step="1" min="1"
                      className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm placeholder-slate-500 focus:outline-none focus:border-amber-500" />
                    <p className="text-[10px] text-slate-500 mt-1">= &euro;{eurVal.toFixed(2)}</p>
                  </div>
                )}

                {/* Summary */}
                <div className="p-3 bg-slate-800/50 rounded-lg space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Prijs per token</span>
                    <span className="text-white">&euro;{price.toFixed(2)} {isFixed ? '(vast)' : '(dynamisch)'}</span>
                  </div>
                  {isFixed && tokensUntilDynamic > 0 && (
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">Nog vast</span>
                      <span className="text-amber-400">{tokensUntilDynamic} tokens tot dynamisch</span>
                    </div>
                  )}
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">{mode === 'buy' ? 'Je betaalt' : 'Je ontvangt'}</span>
                    <span className="text-white">&euro;{eurVal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">{mode === 'buy' ? 'Je ontvangt' : 'Je verkoopt'}</span>
                    <span className="text-amber-400">{tokenVal} ROAR</span>
                  </div>
                </div>

                <button data-testid="execute-trade" onClick={executeTrade} disabled={executing || tokenVal <= 0}
                  className={`w-full py-3 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-50 ${
                    mode === 'buy' ? 'bg-green-500 hover:bg-green-600' : 'bg-red-500 hover:bg-red-600'
                  }`}>
                  {executing ? 'Bezig...' : mode === 'buy' ? `${tokenVal} ROAR Kopen` : `${tokenVal} ROAR Verkopen`}
                </button>

                {result && (
                  <div data-testid="trade-result" className={`p-3 rounded-lg text-xs ${result.success ? 'bg-green-500/10 border border-green-500/20 text-green-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
                    {result.success ? result.message : result.error}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right: History + Potjes */}
          <div className="lg:col-span-7 space-y-4">

            {/* Token Verdeling Visual */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <PieChart className="w-4 h-4 text-amber-400" /> Token Verdeling
              </h3>
              <div className="flex items-center gap-4">
                {/* Simple bar */}
                <div className="flex-1">
                  <div className="h-6 bg-slate-800 rounded-full overflow-hidden flex">
                    <div className="h-full bg-amber-500 transition-all" style={{ width: `${(roarBal / Math.max(circulating, 1)) * 100}%`, minWidth: roarBal > 0 ? '2%' : '0' }} />
                    <div className="h-full bg-purple-500/50 transition-all" style={{ width: `${((circulating - roarBal) / Math.max(circulating, 1)) * 100}%` }} />
                  </div>
                  <div className="flex items-center justify-between mt-2 text-[10px]">
                    <span className="flex items-center gap-1 text-amber-400"><span className="w-2 h-2 rounded-sm bg-amber-500" /> Jij: {roarBal} ({circulating > 0 ? ((roarBal/circulating)*100).toFixed(1) : 0}%)</span>
                    <span className="flex items-center gap-1 text-slate-400"><span className="w-2 h-2 rounded-sm bg-purple-500/50" /> Overig: {(circulating - roarBal).toFixed(0)}</span>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-2xl font-bold text-amber-400">{roarBal}</p>
                  <p className="text-[10px] text-slate-500">ROAR tokens</p>
                </div>
              </div>
            </div>

            {/* Transaction History */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <History className="w-4 h-4 text-amber-400" /> Transactie Geschiedenis
                </h3>
              </div>
              <div className="p-2 space-y-1 max-h-[400px] overflow-y-auto">
                {history.map(tx => {
                  const isBuy = tx.type === 'buy_roar' || tx.type === 'deposit';
                  const isSell = tx.type === 'sell_roar' || tx.type === 'withdrawal';
                  return (
                    <div key={tx.id} data-testid={`tx-${tx.id}`} className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-800/30 transition-colors">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${isBuy ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                        {isBuy ? <ArrowDownRight className="w-4 h-4 text-green-400" /> : <ArrowUpRight className="w-4 h-4 text-red-400" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-white truncate">{tx.description || tx.type}</p>
                        <p className="text-[10px] text-slate-500">
                          {tx.timestamp ? new Date(tx.timestamp).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' }) : '?'}
                          {tx.token_amount > 0 && <span className="ml-2 text-amber-400">{tx.token_amount} ROAR</span>}
                          {tx.price_per_token > 0 && <span className="ml-1 text-slate-600">@ &euro;{tx.price_per_token}</span>}
                        </p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className={`text-sm font-semibold ${isSell ? 'text-red-400' : 'text-green-400'}`}>
                          {isSell ? '-' : '+'}&euro;{(tx.amount_eur || 0).toFixed(2)}
                        </p>
                        <p className="text-[10px] text-slate-600">{tx.status || 'completed'}</p>
                      </div>
                    </div>
                  );
                })}
                {history.length === 0 && (
                  <div className="py-8 text-center text-slate-500 text-xs">Nog geen transacties</div>
                )}
              </div>
            </div>

            {/* How it works */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-white mb-2">Hoe werkt het?</h3>
              <div className="space-y-2 text-[11px] text-slate-400">
                <p><b className="text-amber-400">ROAR Token</b> = aandeel in Spark Core. Elke token vertegenwoordigt een deel van de totale waarde.</p>
                <p><b className="text-white">Prijsmodel</b> = Eerste 10 tokens: vaste prijs van &euro;5,08. Daarna dynamisch (Spark Core waarde / circulerende tokens).</p>
                <p><b className="text-cyan-400">Alleen hele tokens</b> = Je koopt/verkoopt altijd hele ROAR tokens. Wisselgeld gaat naar Spark Core kapitaal.</p>
                <p><b className="text-green-400">Kopen</b> = EUR uit je wallet wordt omgezet naar ROAR tokens. <b className="text-red-400">Verkopen</b> = ROAR terug naar EUR.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

function StatCard({ label, value, sub, icon: Icon, color }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</span>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: `${color}15` }}>
          <Icon className="w-3.5 h-3.5" style={{ color }} />
        </div>
      </div>
      <p className="text-lg font-bold text-white">{value}</p>
      <p className="text-[10px] text-slate-500 mt-0.5">{sub}</p>
    </div>
  );
}

export default WinkelPage;
