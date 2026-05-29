import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  TrendingUp, TrendingDown, Activity, DollarSign,
  ArrowUpRight, ArrowDownRight, Clock, Play, Pause, Square,
  BarChart2, PieChart, RefreshCw, Eye, Timer,
  Settings, Key, Link, GripVertical, Loader2, Zap, Radio, Brain
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

// Interval durations in ms
const INTERVAL_MS = { '15m': 15*60*1000, '1h': 60*60*1000, '4h': 4*60*60*1000, '1d': 24*60*60*1000 };
const INTERVAL_LABELS = { '15m': '15 min', '1h': '1 uur', '4h': '4 uur', '1d': '1 dag' };

export function TraderPage({ onNavigate }) {
  const { user } = useAuth();
  const isAdmin = (user?.gradatie ?? 7) <= 1;
  const isFamilie = (user?.gradatie ?? 7) === 2;  // v4_trader_g2_hide_001
  // v4_trader_admin_switch_001 — admin kan switchen tussen eigen wallet en Spark wallet
  const [walletView, setWalletView] = useState(() => {
    return sessionStorage.getItem('trader_wallet_view') || (user?.id === 'user-001' ? 'spark' : 'me');
  });
  const userId = walletView === 'spark' && isAdmin ? 'user-000' : (user?.id || 'user-001');
  useEffect(() => {
    if (isAdmin) sessionStorage.setItem('trader_wallet_view', walletView);
  }, [walletView, isAdmin]);
  const [activeView, setActiveView] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [trades, setTrades] = useState([]);
  const [markets, setMarkets] = useState({});
  const [bitvavoStatus, setBitvavoStatus] = useState(null);
  const [traderSettings, setTraderSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  // Live data
  const [tickers, setTickers] = useState([]);
  const [candles, setCandles] = useState([]);
  const [candleMarket, setCandleMarket] = useState('BCH-EUR');
  const [candleInterval, setCandleInterval] = useState('1h');

  // Countdown
  const [countdown, setCountdown] = useState('');

  // Monitor
  const [monitorStatus, setMonitorStatus] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const monitorPollRef = useRef(null);

  // Live Bitvavo balance
  const [bvBalance, setBvBalance] = useState(null);

  // Potjes
  const [potjes, setPotjes] = useState(null);
  const [usePotjes, setUsePotjes] = useState(false);

  // v4_multi_market_001: meerdere coins tegelijk monitoren
  const [monitorMarkets, setMonitorMarkets] = useState(['BCH-EUR']);
  const ALL_MARKETS = ['BCH-EUR', 'BTC-EUR', 'ETH-EUR', 'SOL-EUR', 'ADA-EUR'];
  // Sync coin selectie naar live monitor markets als die anders zijn
  useEffect(() => {
    if (Array.isArray(monitorStatus?.markets) && monitorStatus.markets.length > 0) {
      const live = [...monitorStatus.markets].sort().join(',');
      const local = [...monitorMarkets].sort().join(',');
      if (live !== local) setMonitorMarkets(monitorStatus.markets);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monitorStatus?.markets?.join(',')]);

  // v5_candle_hotswap_001 — sync lokale candleInterval met wat de bot ECHT draait
  useEffect(() => {
    const live = monitorStatus?.candle_interval;
    if (live && live !== candleInterval) {
      setCandleInterval(live);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monitorStatus?.candle_interval]);

  // v5_candle_hotswap_001 — wissel cycle hot wanneer bot draait (anders alleen lokaal voor next start)
  const changeCandleInterval = async (newInterval) => {
    setCandleInterval(newInterval);
    if (monitorStatus?.running) {
      try {
        const r = await fetch(`${API}/api/trade/monitor/candle/${userId}`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ candle_interval: newInterval }),
        }).then(r => r.json()).catch(() => ({}));
        if (!r.success && r.message) alert(r.message);
      } finally { loadMonitorStatus(); }
    }
  };
  const toggleMonitorMarket = async (mkt) => {
    const next = monitorMarkets.includes(mkt)
      ? (monitorMarkets.length > 1 ? monitorMarkets.filter(m => m !== mkt) : monitorMarkets)
      : [...monitorMarkets, mkt];
    setMonitorMarkets(next);
    // v5_hot_market_swap_001 — als monitor draait: hot-patch direct backend
    if (monitorStatus?.running) {
      try {
        await fetch(`${API}/api/trade/monitor/markets/${userId}`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ markets: next })
        });
        // v5_potjes_distribute_001 — herverdeel potjes over nieuwe coin-set (5×2 etc.)
        if (monitorStatus?.use_potjes) {
          await fetch(`${API}/api/trade/potjes/${userId}/distribute`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ markets: next })
          });
        }
        loadMonitorStatus();
        loadPotjes && loadPotjes();
      } catch {}
    }
  };

  // Leermodule - Market Context
  const [marketContext, setMarketContext] = useState(null);
  const [contextLoading, setContextLoading] = useState(false);

  // Quick trade
  const [qtMarket, setQtMarket] = useState('BCH-EUR');
  const [qtSide, setQtSide] = useState('buy');
  const [qtAmount, setQtAmount] = useState('5');
  const [qtLoading, setQtLoading] = useState(false);
  const [qtResult, setQtResult] = useState(null);

  const loadCoreData = useCallback(() => {
    return Promise.all([
      fetch(`${API}/api/trade/stats/${userId}`).then(r => r.json()).catch(() => ({})),
      fetch(`${API}/api/trade/history/${userId}?limit=100`).then(r => r.json()).catch(() => ({ trades: [] })),
      fetch(`${API}/api/trade/markets/${userId}`).then(r => r.json()).catch(() => ({ markets: {} })),
      fetch(`${API}/api/trade/bitvavo/status/${userId}`).then(r => r.json()).catch(() => ({})),
      fetch(`${API}/api/trade/settings/${userId}`).then(r => r.json()).catch(() => ({ settings: {} })),
    ]).then(([s, t, m, b, set]) => {
      setStats(s);
      setTrades(t.trades || []);
      setMarkets(m.markets || {});
      setBitvavoStatus(b);
      setTraderSettings(set.settings || {});
      setLoading(false);
    });
  }, [userId]);

  const loadLiveData = useCallback(async () => {
    // v5_sequential_load_001 — sequentieel ipv parallel om UI freeze te voorkomen
    try {
      const d = await fetch(`${API}/api/trade/tickers`).then(r => r.json());
      setTickers(d.tickers || []);
    } catch {}
    try {
      const d = await fetch(`${API}/api/trade/candles?market=${candleMarket}&interval=${candleInterval}&limit=50`).then(r => r.json());
      setCandles(d.candles || []);
    } catch {}
  }, [candleMarket, candleInterval]);

  const loadMonitorStatus = useCallback(async () => {
    try {
      const d = await fetch(`${API}/api/trade/bot/status/${userId}`).then(r => r.json());
      setMonitorStatus(d.status || null);
    } catch {}
    try {
      const d = await fetch(`${API}/api/trade/bot/decisions/${userId}?limit=20`).then(r => r.json());
      setDecisions(d.decisions || []);
    } catch {}
  }, [userId]);

  const loadBalance = useCallback(() => {
    return fetch(`${API}/api/trade/bitvavo/balance/${userId}`).then(r => r.json()).then(d => setBvBalance(d)).catch(() => {});
  }, [userId]);

  const loadPotjes = useCallback(() => {
    return fetch(`${API}/api/trade/potjes/${userId}`).then(r => r.json()).then(d => setPotjes(d)).catch(() => {});
  }, [userId]);

  const loadContext = useCallback(() => {
    return fetch(`${API}/api/trade/context/${candleMarket}`).then(r => r.json()).then(d => setMarketContext(d)).catch(() => {});
  }, [candleMarket]);

  const refreshAllContexts = async () => {
    setContextLoading(true);
    await fetch(`${API}/api/trade/context/refresh-all`, { method: 'POST' });
    loadContext();
    setContextLoading(false);
  };

  // v5_sequential_load_001 (bug B2 fix) — laad data in volgorde ipv parallel
  // om UI freezes en api-burst te voorkomen. Pollers blijven onafhankelijk lopen.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (cancelled) return; await loadCoreData();
      if (cancelled) return; await loadLiveData();
      if (cancelled) return; await loadMonitorStatus();
      if (cancelled) return; await loadBalance();
      if (cancelled) return; await loadPotjes();
      if (cancelled) return; await loadContext();
    })();
    return () => { cancelled = true; };
  }, [loadCoreData, loadLiveData, loadMonitorStatus, loadBalance, loadPotjes, loadContext]);

  // Auto-refresh live data every 30s, monitor every 10s when running
  useEffect(() => {
    // v6_snelhandel_faster_refresh_001 (sessie 14) — was 30s, nu 10s zodat
    // "Live prijs" in Snel Handelen panel meebeweegt met market (gevoel van actueel).
    const liveTimer = setInterval(loadLiveData, 10000);
    return () => clearInterval(liveTimer);
  }, [loadLiveData]);

  useEffect(() => {
    if (monitorStatus?.running) {
      monitorPollRef.current = setInterval(loadMonitorStatus, 10000);
    } else {
      if (monitorPollRef.current) clearInterval(monitorPollRef.current);
    }
    return () => { if (monitorPollRef.current) clearInterval(monitorPollRef.current); };
  }, [monitorStatus?.running, loadMonitorStatus]);

  // Reload candles when market/interval changes
  useEffect(() => { loadLiveData(); }, [candleMarket, candleInterval, loadLiveData]);

  // v5_bot_proactive_register_001 — Toon mij in Analytics (opt-in zichtbaarheid)
  const [registeredInAnalytics, setRegisteredInAnalytics] = useState(false);
  const [registerBusy, setRegisterBusy] = useState(false);
  useEffect(() => {
    fetch(`${API}/api/trade/bot/register-status/${userId}`)
      .then(r => r.json()).then(d => setRegisteredInAnalytics(!!d.registered)).catch(() => {});
  }, [userId]);
  const toggleAnalyticsVisibility = async () => {
    setRegisterBusy(true);
    const endpoint = registeredInAnalytics
      ? `${API}/api/trade/bot/unregister/${userId}`
      : `${API}/api/trade/bot/register/${userId}`;
    try {
      const r = await fetch(endpoint, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewer_id: user?.id || userId }),
      }).then(x => x.json());
      if (r.success) setRegisteredInAnalytics(!registeredInAnalytics);
    } finally { setRegisterBusy(false); }
  };

  // Countdown timer - time until current candle closes
  useEffect(() => {
    const intervalMs = INTERVAL_MS[candleInterval] || 3600000;
    const tick = () => {
      const now = Date.now();
      const elapsed = now % intervalMs;
      const remaining = intervalMs - elapsed;
      const mins = Math.floor(remaining / 60000);
      const secs = Math.floor((remaining % 60000) / 1000);
      setCountdown(`${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [candleInterval]);

  // Monitor controls
  // v5_per_user_endpoints_001 — altijd per-user endpoints, ook voor admin.
  // Voorheen gebruikten admins de legacy singleton wat alle bots beïnvloedde (stop Willem → stopte ook Spark).
  const startMonitor = async () => {
    const settings = traderSettings || {};
    const res = await fetch(`${API}/api/trade/bot/start/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        interval: 30,
        market: monitorMarkets[0] || candleMarket,
        markets: monitorMarkets,
        candle_interval: candleInterval,
        user_id: userId, auto_trade: settings.auto_trade || false,
        trade_amount: settings.trade_amount || 5, use_mock: settings.use_mock !== false,
        use_potjes: usePotjes,
      }),
    });
    const data = await res.json();
    if (!data.success && data.error) {
      alert(data.error);  // simpele feedback voor token-gate weigering
    }
    loadMonitorStatus();
    if (usePotjes) loadPotjes();
  };
  const stopMonitor = async () => {
    const res = await fetch(`${API}/api/trade/bot/stop/${userId}`, { method: 'POST' }).then(r => r.json()).catch(() => ({}));
    if (!res.success && res.error) alert(res.error);
    loadMonitorStatus();
  };
  const pauseMonitor = async () => {
    await fetch(`${API}/api/trade/bot/pause/${userId}`, { method: 'POST' }).catch(() => {});
    loadMonitorStatus();
  };

  // Quick trade
  const executeQuickTrade = async () => {
    setQtLoading(true); setQtResult(null);
    const res = await fetch(`${API}/api/trade/execute/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ market: qtMarket, side: qtSide, amount: parseFloat(qtAmount) || 5, use_mock: traderSettings?.use_mock !== false }),
    }).then(r => r.json()).catch(() => ({ success: false, error: 'Verbinding mislukt' }));
    setQtResult(res);
    setQtLoading(false);
    if (res.success) { loadCoreData(); loadLiveData(); }
  };

  // Spark-buy (v4_quickpot_001): pakt vrij potje + start monitor automatisch
  const executeSparkBuy = async () => {
    setQtLoading(true); setQtResult(null);
    const res = await fetch(`${API}/api/trade/quick-buy-potje/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ market: qtMarket, use_mock: traderSettings?.use_mock !== false, candle_interval: '1h' }),
    }).then(r => r.json()).catch(() => ({ success: false, error: 'Verbinding mislukt' }));
    setQtResult(res);
    setQtLoading(false);
    if (res.success) {
      // v4_potje_refresh_001: quick-buy-potje gebruikt ALTIJD potjes, dus altijd refreshen
      loadCoreData();
      loadLiveData();
      loadMonitorStatus();
      loadPotjes();
      loadBalance();
    }
  };

  if (loading) return (
    <MainLayout activePage="trade" onNavigate={onNavigate}>
      <div className="flex items-center justify-center h-full"><Loader2 className="w-8 h-8 text-green-500 animate-spin" /></div>
    </MainLayout>
  );

  return (
    <MainLayout activePage="trade" onNavigate={onNavigate}>
      <div data-testid="trade-page" className="p-4 md:p-6 space-y-4 max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Crypto Trader</h1>
              <p className="text-xs text-slate-400">
                {stats?.total_trades || 0} trades
                {bvBalance?.success && <span className="ml-2 text-green-400">| Bitvavo: €{bvBalance.total_eur?.toFixed(2)}</span>}
                {' | '}{tickers[0] ? `BCH €${tickers[0].last}` : 'Laden...'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* v4_trader_admin_switch_001 — Wallet view switch (admin only) */}
            {isAdmin && (
              <div data-testid="wallet-switch" className="flex items-center gap-1 p-1 bg-slate-800/60 rounded-lg border border-slate-700">
                <button onClick={() => setWalletView('me')} data-testid="wallet-switch-me"
                  className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors flex items-center gap-1 ${walletView === 'me' ? 'bg-amber-500/30 text-amber-200' : 'text-slate-400 hover:text-slate-200'}`}>
                  👤 Mijn
                </button>
                <button onClick={() => setWalletView('spark')} data-testid="wallet-switch-spark"
                  className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${walletView === 'spark' ? 'bg-amber-500/30 text-amber-200' : 'text-slate-400 hover:text-slate-200'}`}>
                  🌟 Spark
                </button>
              </div>
            )}
            {/* Monitor indicator */}
            {monitorStatus?.running && (
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/10 border border-green-500/20 text-[10px] text-green-400 animate-pulse">
                <Radio className="w-3 h-3" /> Monitor actief
              </span>
            )}
            <button onClick={() => { loadCoreData(); loadLiveData(); loadMonitorStatus(); }} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
              <RefreshCw className="w-4 h-4 text-slate-400" />
            </button>
            <button data-testid="trade-settings-toggle" onClick={(e) => { e.stopPropagation(); setActiveView(activeView === 'bitvavo' ? 'dashboard' : 'bitvavo'); }}
              className={`p-2 rounded-lg transition-colors ${isFamilie ? 'opacity-30 cursor-not-allowed' : 'bg-slate-800 hover:bg-slate-700'}`}
              title={isFamilie ? 'Niet beschikbaar voor Familie (gradatie 2)' : 'Bitvavo instellingen'}
              disabled={isFamilie}>
              <Settings className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>

        {/* v4_trader_g2_hide_001 — Familie ziet alleen overzicht */}
        {isFamilie && (
          <div data-testid="trader-g2-info" className="px-4 py-3 bg-blue-500/5 border border-blue-500/20 rounded-xl">
            <p className="text-xs text-blue-300 flex items-center gap-2">
              <span className="text-base">👁️</span>
              Je bent op Familie-niveau (gradatie 2). Je ziet hier het portfolio-overzicht. Trade-uitvoering, Bitvavo-instellingen en donaties zijn beheerd door admins.
            </p>
          </div>
        )}

        {activeView === 'bitvavo' && !isFamilie ? (
          <BitvavoSettings userId={userId} status={bitvavoStatus} settings={traderSettings} />
        ) : (
          <>
            {/* Live Bitvavo Portfolio */}
            {bvBalance?.success && bvBalance.balances?.length > 0 && (
              <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/5 border border-green-500/20 rounded-2xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-green-400" /> Live Bitvavo Portfolio
                  </h3>
                  <div className="text-right">
                    <p className="text-[10px] text-slate-400">Totaal</p>
                    <p className="text-lg font-bold text-green-400">€{bvBalance.total_eur?.toFixed(2)}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {bvBalance.balances.filter(b => (b.value_eur ?? 0) >= 0.01 || b.symbol === 'EUR').map(b => (
                    <div key={b.symbol} data-testid={`balance-${b.symbol}`} className="bg-slate-900/50 rounded-xl p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-white">{b.symbol}</span>
                        <span className="text-[10px] text-green-400">€{b.value_eur?.toFixed(2)}</span>
                      </div>
                      <p className="text-[10px] text-slate-500">{b.total?.toFixed(6)} {b.symbol}</p>
                      {b.symbol !== 'EUR' && <p className="text-[9px] text-slate-600">@ €{b.price_eur?.toFixed(2)}</p>}
                    </div>
                  ))}
                </div>
                {bvBalance.balances.filter(b => (b.value_eur ?? 0) < 0.01 && b.symbol !== 'EUR').length > 0 && (
                  <p className="text-[10px] text-slate-600 mt-2">
                    + {bvBalance.balances.filter(b => (b.value_eur ?? 0) < 0.01 && b.symbol !== 'EUR').length} stofjes verborgen (&lt;€0,01)
                  </p>
                )}
              </div>
            )}
            {bvBalance && !bvBalance.success && (
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 text-[11px] text-amber-400 flex items-center gap-2">
                <Key className="w-3.5 h-3.5" /> Live Bitvavo saldo niet beschikbaar: {bvBalance.error}
              </div>
            )}

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              <QuickStat label="Totaal Trades" value={stats?.total_trades || 0} icon={Activity} color="#06b6d4" />
              <QuickStat label="Gekocht" value={`\u20AC${stats?.total_buy_eur || 0}`} subtext={`${stats?.buys || 0} buys`} icon={ArrowDownRight} color="#22c55e" />
              <QuickStat label="Verkocht" value={`\u20AC${stats?.total_sell_eur || 0}`} subtext={`${stats?.sells || 0} sells`} icon={ArrowUpRight} color="#ef4444" />
              <QuickStat label="Fees betaald" value={`\u20AC${stats?.total_fees_eur || 0}`} subtext="0.25% per trade" icon={DollarSign} color="#f59e0b" />
              <QuickStat label="Netto P&L (trades)" value={`\u20AC${stats?.netto_pnl ?? 0}`} subtext={`Bruto: \u20AC${stats?.bruto_pnl ?? 0}`} icon={TrendingUp} color={(stats?.netto_pnl ?? 0) >= 0 ? '#22c55e' : '#ef4444'} />
              <QuickStat
                label="Live P&L (vs start)"
                value={stats?.live_pnl != null ? `\u20AC${stats.live_pnl.toFixed(2)}` : '—'}
                subtext={stats?.baseline_eur ? `Baseline: \u20AC${stats.baseline_eur}` : 'Geen baseline'}
                icon={Zap}
                color={(stats?.live_pnl ?? 0) >= 0 ? '#22c55e' : '#ef4444'}
              />
            </div>

            {/* Main 3-col Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

              {/* Left: Candle Chart + Monitor */}
              <div className="lg:col-span-8 space-y-4">

                {/* Candle Chart */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
                  <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <BarChart2 className="w-4 h-4 text-amber-400" />
                      <span className="text-sm font-semibold text-white" data-testid="chart-market-label">{candleMarket}</span>
                      {/* Countdown */}
                      <div data-testid="candle-countdown" className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700">
                        <Timer className="w-3 h-3 text-amber-400" />
                        <span className="text-[10px] font-mono text-amber-400">{countdown}</span>
                        <span className="text-[9px] text-slate-500">{INTERVAL_LABELS[candleInterval]}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {['15m', '1h', '4h', '1d'].map(iv => (
                        <button key={iv} data-testid={`interval-${iv}`} onClick={() => changeCandleInterval(iv)}
                          className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition-all ${candleInterval === iv ? 'bg-amber-500/20 text-amber-400' : 'text-slate-500 hover:text-slate-300'}`}
                          title={monitorStatus?.running ? 'Wijzigt direct ook de cycle van je draaiende bot' : 'Wijzigt chart-cycle (en bot-cycle bij start)'}>
                          {iv}
                        </button>
                      ))}
                    </div>
                  </div>
                  <CandleChart candles={candles} />
                </div>

                {/* Monitor Panel */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
                  <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                      <Radio className="w-4 h-4 text-amber-400" /> Monitor
                    </h3>
                    <div className="flex items-center gap-2">
                      {/* Potjes toggle */}
                      {!monitorStatus?.running && (
                        <label className="flex items-center gap-1.5 text-[10px] text-slate-400 cursor-pointer select-none">
                          <input type="checkbox" data-testid="toggle-potjes-mode" checked={usePotjes} onChange={e => setUsePotjes(e.target.checked)}
                            className="w-3 h-3 accent-amber-500" />
                          10-Potjes
                        </label>
                      )}
                      {/* v5_offline_persistence_001 — bot blijft draaien als user offline is */}
                      <label className="flex items-center gap-1.5 text-[10px] text-slate-400 cursor-pointer select-none" title="Wanneer aan: jouw bot draait door ook als je uitlogt. Anders stopt-ie bij logout.">
                        <input type="checkbox" data-testid="toggle-offline-persistence"
                          checked={registeredInAnalytics} disabled={registerBusy}
                          onChange={toggleAnalyticsVisibility}
                          className="w-3 h-3 accent-cyan-500" />
                        Draaien als ik offline ben
                      </label>
                      {!monitorStatus?.running ? (
                        <button data-testid="monitor-start" onClick={startMonitor}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-medium bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors">
                          <Play className="w-3 h-3" /> Start
                        </button>
                      ) : (
                        <>
                          <button data-testid="monitor-pause" onClick={pauseMonitor}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-medium transition-colors ${monitorStatus.paused ? 'bg-amber-500/20 text-amber-400' : 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'}`}>
                            {monitorStatus.paused ? <><Play className="w-3 h-3" /> Hervat</> : <><Pause className="w-3 h-3" /> Pauzeer</>}
                          </button>
                          <button data-testid="monitor-stop" onClick={stopMonitor}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-medium bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors">
                            <Square className="w-3 h-3" /> Stop
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="p-4">
                    {/* v4_multi_market_001 + v5_hot_swap_001: coin-selectie altijd zichtbaar, ook tijdens running */}
                    <div className="mb-4 pb-3 border-b border-slate-800/50">
                      <p className="text-[10px] text-slate-500 mb-2">Welke coins monitoren? {monitorStatus?.running && <span className="text-emerald-400">(live aanpasbaar)</span>}</p>
                      <div className="flex flex-wrap gap-1.5" data-testid="monitor-coin-picker">
                        {ALL_MARKETS.map(mkt => {
                          const sym = mkt.split('-')[0];
                          const active = monitorMarkets.includes(mkt);
                          return (
                            <button key={mkt} data-testid={`monitor-coin-${sym}`}
                              onClick={() => toggleMonitorMarket(mkt)}
                              className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition-colors ${active ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-slate-800 text-slate-500 hover:text-slate-300 border border-transparent'}`}>
                              {sym}
                            </button>
                          );
                        })}
                      </div>
                      <p className="text-[9px] text-slate-600 mt-2">Candle interval: {candleInterval} (zelfde voor alle coins). 10 potjes spreiden zich automatisch over gekozen coins.</p>
                    </div>
                    {monitorStatus?.running ? (
                      <div className="space-y-3">
                        {/* Status bar */}
                        <div className="flex items-center gap-4 text-[10px] flex-wrap">
                          <span className="flex items-center gap-1 text-green-400"><span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" /> Actief</span>
                          <span className="text-slate-400">Cyclus #{monitorStatus.cycles}</span>
                          <span className="text-slate-400">
                            {Array.isArray(monitorStatus.markets) && monitorStatus.markets.length > 1
                              ? `${monitorStatus.markets.join(' · ')} (${monitorStatus.candle_interval})`
                              : `${monitorStatus.market} (${monitorStatus.candle_interval})`}
                          </span>
                          <span className="text-slate-400">Prijs: €{monitorStatus.last_price?.toFixed(2)}</span>
                          {monitorStatus.auto_trade && <span className="text-amber-400">Auto-trade AAN</span>}
                          {monitorStatus.position?.is_open && (
                            <span className="px-2 py-0.5 rounded bg-green-500/20 text-green-400">
                              LONG @ €{monitorStatus.position.entry_price?.toFixed(2)}
                              {monitorStatus.position.trailing_active && ' 🔒 trailing'}
                            </span>
                          )}
                          <span className="text-slate-500 ml-auto">{monitorStatus.uptime_seconds ? `${Math.floor(monitorStatus.uptime_seconds)}s` : ''}</span>
                        </div>
                        {/* Decisions */}
                        <div className="space-y-1 max-h-[200px] overflow-y-auto">
                          {decisions.map((d, i) => (
                            <div key={i} className="flex items-center gap-3 p-2 bg-slate-800/40 rounded-lg text-[10px]">
                              <span className={`font-bold px-1.5 py-0.5 rounded ${d.action === 'BUY' ? 'bg-green-500/20 text-green-400' : d.action === 'SELL' ? 'bg-red-500/20 text-red-400' : 'bg-slate-700 text-slate-400'}`}>
                                {d.action}
                              </span>
                              {d.market && <span className="text-amber-400 text-[9px]">{d.market.split('-')[0]}</span>}
                              <span className="text-white">€{d.price?.toFixed(2)}</span>
                              <span className="text-slate-500 flex-1 truncate">{d.reason}</span>
                              {d.executed && <Zap className="w-3 h-3 text-amber-400" />}
                              <span className="text-slate-600">#{d.cycle}</span>
                            </div>
                          ))}
                          {decisions.length === 0 && <p className="text-xs text-slate-500 text-center py-4">Wacht op eerste cyclus...</p>}
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-6">
                        <Radio className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                        <p className="text-xs text-slate-500">Monitor is uit. Klik Start om live markt te monitoren.</p>
                        <p className="text-[10px] text-slate-600 mt-1">Bollinger Band signalen | Auto-trade: {traderSettings?.auto_trade ? 'Aan' : 'Uit'} | Mock: {traderSettings?.use_mock !== false ? 'Ja' : 'Nee (LIVE)'}</p>
                      </div>
                    )}
                  </div>
                </div>
                {/* Potjes Panel (toont altijd als data aanwezig) */}
                {potjes?.success && (
                  <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                        <PieChart className="w-4 h-4 text-amber-400" /> 10-Potjes Systeem
                        {monitorStatus?.use_potjes && monitorStatus?.running && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">ACTIEF</span>
                        )}
                      </h3>
                      <div className="flex items-center gap-3 text-[10px]">
                        <span className="text-slate-400">
                          <span className="text-amber-400 font-bold">{potjes.summary?.pot_count}</span> × €{potjes.summary?.current_max_per_pot}
                        </span>
                        <span className="text-slate-400">
                          Live: <span className="text-white font-medium">€{(potjes.summary?.live_balance ?? potjes.summary?.total_capital)?.toFixed(2)}</span>
                          {potjes.summary?.baseline_eur && (
                            <span className="text-slate-500"> / €{potjes.summary.baseline_eur.toFixed(2)}</span>
                          )}
                        </span>
                        <span className="text-slate-400">Open: <span className="text-amber-400">{potjes.summary?.open_positions}</span>/{potjes.summary?.pot_count}</span>
                        <span className={`${(potjes.summary?.live_pnl ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'} font-medium`}>
                          P&L: {potjes.summary?.live_pnl != null ? `€${potjes.summary.live_pnl >= 0 ? '+' : ''}${potjes.summary.live_pnl.toFixed(2)}` : `€${potjes.summary?.total_pnl?.toFixed(3)}`}
                        </span>
                        <button onClick={loadPotjes} className="text-slate-500 hover:text-white">
                          <RefreshCw className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                    {/* Expansie progress bar naar volgende potje */}
                    {potjes.summary?.next_pot_cost && (
                      <div className="px-4 pt-3 pb-1">
                        <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
                          <span>Potje #{potjes.summary.next_pot_number} (€{potjes.summary.next_pot_max}) bij €{potjes.summary.next_pot_cost} overflow</span>
                          <span>{potjes.summary.expansion_progress_pct}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all" style={{ width: `${Math.min(100, potjes.summary.expansion_progress_pct)}%` }} />
                        </div>
                      </div>
                    )}
                    <div className="p-3 grid grid-cols-2 md:grid-cols-5 gap-2">
                      {(potjes.potjes ? [...potjes.potjes].sort((a, b) => {
                        // v6_pot_lock_visual_order_001 — locked potjes (staking-ankers) ONDERAAN
                        // zodat de actieve trade-potjes meteen in beeld staan en de "fundering"
                        // visueel apart blijft staan.
                        const aLocked = a.pot_locked ? 1 : 0;
                        const bLocked = b.pot_locked ? 1 : 0;
                        if (aLocked !== bLocked) return aLocked - bLocked;
                        // Binnen elke groep: open posities eerst, dan op index
                        const aOpen = a.position?.is_open ? 0 : 1;
                        const bOpen = b.position?.is_open ? 0 : 1;
                        if (aOpen !== bOpen) return aOpen - bOpen;
                        return (a.index || 0) - (b.index || 0);
                      }) : [])?.map(p => {
                        const open = p.position?.is_open;
                        const locked = p.pot_locked;
                        const pnl = p.stats?.total_pnl || 0;
                        const liveValue = p.live_value ?? p.capital;
                        const hasGrowth = Math.abs(liveValue - p.capital) >= 0.005;
                        return (
                          <div key={p.id} data-testid={`pot-${p.id}`}
                            className={`rounded-xl p-2.5 border ${
                              locked ? 'bg-emerald-500/5 border-emerald-500/30' :
                              open ? 'bg-amber-500/10 border-amber-500/30' :
                              'bg-slate-800/30 border-slate-700'
                            }`}>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-[10px] font-bold text-white flex items-center gap-1">
                                {locked && <span className="text-emerald-400" title={p.lock_reason || 'locked'}>🔒</span>}
                                {p.id}
                              </span>
                              <span className={`text-[9px] font-medium ${hasGrowth ? (liveValue > p.capital ? 'text-green-400' : 'text-red-400') : 'text-slate-400'}`}>
                                €{liveValue.toFixed(2)}
                              </span>
                            </div>
                            {locked ? (
                              <div>
                                <p className="text-[9px] text-emerald-400 font-semibold">STAKING ANKER</p>
                                <p className="text-[9px] text-slate-500 truncate">{p.market || '—'}</p>
                              </div>
                            ) : open ? (
                              <div>
                                <p className="text-[9px] text-amber-400">IN POSITIE</p>
                                <p className="text-[9px] text-slate-400">@ €{p.position.entry_price?.toFixed(2)}</p>
                                {p.position.trailing_active && <p className="text-[9px] text-green-400">🔒 trailing</p>}
                              </div>
                            ) : (
                              <p className="text-[9px] text-slate-500">Vrij</p>
                            )}
                            <div className="flex justify-between mt-1">
                              <span className="text-[9px] text-slate-500">{p.stats?.trades || 0} trades</span>
                              <span className={`text-[9px] ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>€{pnl.toFixed(3)}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    {potjes.summary?.overflow_pool > 0 && (
                      <div className="px-4 py-2 border-t border-slate-800 text-[10px] text-slate-500">
                        Overflow pool: €{potjes.summary.overflow_pool.toFixed(2)} (voor nieuwe potjes)
                      </div>
                    )}
                  </div>
                )}

                {/* Market Insights (Leermodule) */}
                {marketContext?.success && (
                  <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                        <Brain className="w-4 h-4 text-purple-400" /> Market Insights
                        {marketContext.context?.market_state?.trend && (
                          <span className={`text-[9px] px-1.5 py-0.5 rounded uppercase ${
                            marketContext.context.market_state.trend === 'bull' ? 'bg-green-500/20 text-green-400' :
                            marketContext.context.market_state.trend === 'bear' ? 'bg-red-500/20 text-red-400' :
                            'bg-slate-700 text-slate-400'
                          }`}>
                            {marketContext.context.market_state.trend}
                          </span>
                        )}
                        <span className="text-[9px] text-slate-600">{marketContext.context?.market}</span>
                      </h3>
                      <button data-testid="refresh-context-btn" onClick={refreshAllContexts} disabled={contextLoading}
                        className="text-[10px] text-purple-400 hover:text-purple-300 flex items-center gap-1 disabled:opacity-50">
                        <RefreshCw className={`w-3 h-3 ${contextLoading ? 'animate-spin' : ''}`} /> {contextLoading ? 'Leren...' : 'Refresh alle coins'}
                      </button>
                    </div>
                    <div className="p-3 grid grid-cols-1 md:grid-cols-3 gap-3">
                      {/* Support levels */}
                      <div>
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">Support</p>
                        {marketContext.context?.support_levels?.length > 0 ? (
                          <div className="space-y-1">
                            {marketContext.context.support_levels.slice(0, 3).map((s, i) => (
                              <div key={i} className="flex items-center justify-between px-2 py-1 bg-green-500/10 border border-green-500/20 rounded">
                                <span className="text-xs text-green-400 font-medium">€{s.price}</span>
                                <div className="flex items-center gap-1">
                                  <span className="text-[9px] text-slate-500">{s.bounces}x</span>
                                  <span className="text-[9px] text-green-400">{(s.strength * 100).toFixed(0)}%</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : <p className="text-[10px] text-slate-600">Geen data</p>}
                      </div>
                      {/* Resistance levels */}
                      <div>
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">Weerstand</p>
                        {marketContext.context?.resistance_levels?.length > 0 ? (
                          <div className="space-y-1">
                            {marketContext.context.resistance_levels.slice(0, 3).map((r, i) => (
                              <div key={i} className="flex items-center justify-between px-2 py-1 bg-red-500/10 border border-red-500/20 rounded">
                                <span className="text-xs text-red-400 font-medium">€{r.price}</span>
                                <div className="flex items-center gap-1">
                                  <span className="text-[9px] text-slate-500">{r.tests}x</span>
                                  <span className="text-[9px] text-red-400">{(r.strength * 100).toFixed(0)}%</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : <p className="text-[10px] text-slate-600">Geen data</p>}
                      </div>
                      {/* Patterns */}
                      <div>
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1.5">Patronen</p>
                        <div className="space-y-1">
                          {marketContext.context?.market_state && (
                            <div className="flex items-center justify-between px-2 py-1 bg-slate-800/50 rounded">
                              <span className="text-[10px] text-slate-400">Momentum</span>
                              <span className={`text-[10px] font-medium ${marketContext.context.market_state.momentum_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {marketContext.context.market_state.momentum_pct >= 0 ? '+' : ''}{marketContext.context.market_state.momentum_pct}%
                              </span>
                            </div>
                          )}
                          {marketContext.context?.patterns?.volatility && (
                            <div className="flex items-center justify-between px-2 py-1 bg-slate-800/50 rounded">
                              <span className="text-[10px] text-slate-400">Volatiliteit</span>
                              <span className="text-[10px] text-white capitalize">{marketContext.context.patterns.volatility.state}</span>
                            </div>
                          )}
                          {(() => {
                            const patterns = marketContext.context?.patterns?.weekday_patterns;
                            if (!patterns) return null;
                            const days = Object.entries(patterns).filter(([_, p]) => p.bias !== 'neutral').slice(0, 2);
                            return days.map(([day, p]) => (
                              <div key={day} className={`flex items-center justify-between px-2 py-1 rounded ${p.bias === 'bullish' ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                                <span className="text-[10px] text-slate-400 capitalize">{day}</span>
                                <span className={`text-[10px] ${p.bias === 'bullish' ? 'text-green-400' : 'text-red-400'}`}>
                                  {p.avg_change_pct >= 0 ? '+' : ''}{p.avg_change_pct}%
                                </span>
                              </div>
                            ));
                          })()}
                        </div>
                      </div>
                    </div>
                    <div className="px-4 py-2 border-t border-slate-800 text-[10px] text-slate-600 flex items-center justify-between">
                      <span>{marketContext.context?.candles_analyzed || 0} candles geanalyseerd</span>
                      <span>Cache: {marketContext.context?.cache_age_hours?.toFixed(1) || 0}h oud</span>
                    </div>
                  </div>
                )}
              </div>
              <div className="lg:col-span-4 space-y-4">

                {/* Watchlist */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
                  <div className="px-4 py-3 border-b border-slate-800">
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                      <Eye className="w-4 h-4 text-amber-400" /> Watchlist
                    </h3>
                  </div>
                  <div className="p-2 space-y-1">
                    {tickers.map(t => {
                      const change = t.open > 0 ? ((t.last - t.open) / t.open * 100) : 0;
                      const isUp = change >= 0;
                      return (
                        <button key={t.market} data-testid={`watch-${t.symbol}`} onClick={() => { setQtMarket(t.market); setCandleMarket(t.market); }}
                          className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${qtMarket === t.market ? 'bg-amber-500/10 border border-amber-500/20' : 'hover:bg-slate-800/50'}`}>
                          <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center text-xs font-bold">{t.symbol[0]}</div>
                          <div className="flex-1 text-left">
                            <p className="text-xs font-medium text-white">{t.symbol}</p>
                            <p className="text-[10px] text-slate-500">{t.name}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-white font-medium">€{t.last < 1 ? t.last.toFixed(5) : t.last.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                            <p className={`text-[10px] flex items-center justify-end gap-0.5 ${isUp ? 'text-green-400' : 'text-red-400'}`}>
                              {isUp ? <ArrowUpRight className="w-2.5 h-2.5" /> : <ArrowDownRight className="w-2.5 h-2.5" />}
                              {Math.abs(change).toFixed(2)}%
                            </p>
                          </div>
                        </button>
                      );
                    })}
                    {tickers.length === 0 && <p className="text-xs text-slate-500 text-center py-4">Laden...</p>}
                  </div>
                </div>

                {/* Recent Trades */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
                  <div className="px-4 py-3 border-b border-slate-800">
                    <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                      <Clock className="w-4 h-4 text-amber-400" /> Recente Trades
                    </h3>
                  </div>
                  <div className="p-2 space-y-1 max-h-[280px] overflow-y-auto">
                    {trades.filter(t => !t.hidden_in_recent).slice(0, 8).map(trade => (
                      <div key={trade.trade_id} data-testid={`trade-${trade.trade_id}`} className="flex items-center justify-between p-2.5 rounded-xl hover:bg-slate-800/40 transition-colors">
                        <div className="flex items-center gap-2.5">
                          <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${trade.action === 'BUY' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                            {trade.action === 'BUY' ? <ArrowDownRight className="w-3.5 h-3.5 text-green-400" /> : <ArrowUpRight className="w-3.5 h-3.5 text-red-400" />}
                          </div>
                          <div>
                            <p className="text-xs font-medium text-white">
                              <span className={trade.action === 'BUY' ? 'text-green-400' : 'text-red-400'}>{trade.action === 'BUY' ? 'Koop' : 'Verkoop'}</span>
                              {' '}{trade.market?.split('-')[0]}
                            </p>
                            <p className="text-[10px] text-slate-500">
                              {trade.timestamp ? new Date(trade.timestamp).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }) : '?'}
                              {trade.mock && <span className="ml-1 text-blue-400">[mock]</span>}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-white">€{trade.amount?.toFixed(2)}</p>
                          <p className="text-[10px] text-slate-500">@{trade.price?.toFixed(2)}</p>
                        </div>
                      </div>
                    ))}
                    {trades.length === 0 && <p className="text-xs text-slate-500 text-center py-4">Nog geen trades</p>}
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Trade Panel — vereenvoudigd v4_snelhandel_002 */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
              <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-400" /> Snel Handelen
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                {/* Markt */}
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Markt (coin)</label>
                  <select data-testid="quick-trade-market" value={qtMarket} onChange={e => setQtMarket(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:border-amber-500 focus:outline-none">
                    <option value="BCH-EUR">BCH-EUR</option>
                    <option value="BTC-EUR">BTC-EUR</option>
                    <option value="ETH-EUR">ETH-EUR</option>
                    <option value="SOL-EUR">SOL-EUR</option>
                    <option value="ADA-EUR">ADA-EUR</option>
                  </select>
                </div>

                {/* Inzet — leest uit het volgende vrije potje (read-only) */}
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Inzet (uit potje)</label>
                  <div data-testid="quick-trade-inzet" className="py-3 px-4 bg-slate-800/60 border border-slate-700/60 rounded-xl text-sm text-white">
                    {(() => {
                      const list = Array.isArray(potjes?.potjes) ? potjes.potjes : (Array.isArray(potjes) ? potjes : []);
                      const sorted = [...list].sort((a, b) => (a.nummer || a.index || 0) - (b.nummer || b.index || 0));
                      // v6_snelhandel_skip_lock_001 (sessie 14) — sla locked anchors over
                      // (anders pakt UI pot-001 ADA-anker als "volgende vrij potje")
                      const freePot = sorted.find(p => !p?.position?.is_open && !p?.pot_locked);
                      // v6_snelhandel_live_capital_001 — gebruik echte capital (€9.95 / €10.11 etc),
                      // niet de outdated 5.08 fallback.
                      const amt = freePot ? (freePot.capital || freePot.current_size || freePot.starting_size || 10.0) : null;
                      return freePot
                        ? <>€{amt.toFixed(2)} <span className="text-[10px] text-slate-500">(potje {freePot.nummer || freePot.index + 1})</span></>
                        : <span className="text-amber-400 text-xs">Alle potjes bezet</span>;
                    })()}
                  </div>
                </div>

                {/* Live prijs */}
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Live prijs</label>
                  <div data-testid="quick-trade-price" className="py-3 px-4 bg-slate-800/60 border border-slate-700/60 rounded-xl text-sm">
                    {(() => {
                      const t = tickers.find(x => x.market === qtMarket) || tickers[0];
                      return t?.last
                        ? <span className="text-emerald-400 font-medium">€{Number(t.last) < 1 ? Number(t.last).toFixed(5) : Number(t.last).toFixed(2)}</span>
                        : <span className="text-slate-500 text-xs">laden...</span>;
                    })()}
                    <p className="text-[10px] text-slate-500 mt-0.5">moment van koop · {qtMarket}</p>
                  </div>
                </div>

                {/* Modus: mock/live indicator (no input) */}
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Modus</label>
                  <div className="flex items-center gap-2 py-3 px-4 bg-slate-800 rounded-xl text-sm">
                    <span className={`w-2 h-2 rounded-full ${traderSettings?.use_mock !== false ? 'bg-blue-400' : 'bg-green-400 animate-pulse'}`} />
                    <span className={traderSettings?.use_mock !== false ? 'text-blue-400' : 'text-green-400'}>
                      {traderSettings?.use_mock !== false ? 'Mock' : 'LIVE'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Koop Potje — enige actie-knop. Spark regelt de rest. */}
              <div className="mt-4 pt-4 border-t border-slate-800">
                {(user?.gradatie ?? 7) > 1 ? (
                  <div data-testid="quick-buy-locked" className="w-full py-3.5 bg-slate-800/50 border border-slate-700 text-slate-400 font-medium rounded-xl text-sm flex items-center justify-center gap-2">
                    🔒 Alleen beheerder kan handmatig potje kopen
                  </div>
                ) : (
                  <button data-testid="spark-buy-potje" onClick={executeSparkBuy} disabled={qtLoading}
                    className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-semibold rounded-xl hover:from-emerald-400 hover:to-teal-500 transition-all text-sm disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20">
                    <span className="text-base">⚡</span>
                    {qtLoading ? 'Spark werkt...' : 'Koop potje'}
                  </button>
                )}
                <p className="text-[10px] text-slate-500 mt-2 text-center leading-relaxed">
                  {(user?.gradatie ?? 7) > 1
                    ? <>Jouw bot draait automatisch zodra je tokens hebt (1 token = 1 potje).</>
                    : <>Spark pakt het volgende vrije potje, koopt op de live prijs en start direct de monitor.<br/>Auto-verkoop op winst-moment via trailing stop.</>}
                </p>
              </div>

              {qtResult && (
                <div data-testid="quick-trade-result" className={`mt-3 p-3 rounded-xl text-xs ${qtResult.success ? 'bg-green-500/10 border border-green-500/20 text-green-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
                  {qtResult.success ? qtResult.message : `Fout: ${qtResult.error}`}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </MainLayout>
  );
}

/* === CandleChart Component === */
function CandleChart({ candles }) {
  if (!candles || candles.length === 0) {
    return <div className="h-56 flex items-center justify-center text-xs text-slate-500">Candle data laden...</div>;
  }

  const sorted = [...candles].sort((a, b) => a.timestamp - b.timestamp);
  const highs = sorted.map(c => c.high);
  const lows = sorted.map(c => c.low);
  const maxPrice = Math.max(...highs);
  const minPrice = Math.min(...lows);
  const range = maxPrice - minPrice || 1;

  const chartH = 200;
  const chartW = 100; // percentage
  const barW = chartW / sorted.length;

  return (
    <div className="p-4">
      <div className="relative h-56 bg-slate-800/30 rounded-xl overflow-hidden">
        <svg viewBox={`0 0 1000 ${chartH}`} className="w-full h-full" preserveAspectRatio="none">
          {/* Grid lines */}
          {[0.25, 0.5, 0.75].map(pct => (
            <line key={pct} x1="0" x2="1000" y1={chartH * pct} y2={chartH * pct} stroke="#334155" strokeWidth="0.5" strokeDasharray="4 4" />
          ))}

          {sorted.map((c, i) => {
            const x = (i / sorted.length) * 1000;
            const w = Math.max(1000 / sorted.length - 2, 3);
            const isGreen = c.close >= c.open;

            const bodyTop = chartH - ((Math.max(c.open, c.close) - minPrice) / range) * (chartH - 20) - 10;
            const bodyBot = chartH - ((Math.min(c.open, c.close) - minPrice) / range) * (chartH - 20) - 10;
            const bodyH = Math.max(bodyBot - bodyTop, 1);

            const wickTop = chartH - ((c.high - minPrice) / range) * (chartH - 20) - 10;
            const wickBot = chartH - ((c.low - minPrice) / range) * (chartH - 20) - 10;

            const color = isGreen ? '#22c55e' : '#ef4444';
            const cx = x + w / 2;

            return (
              <g key={i}>
                {/* Wick */}
                <line x1={cx} x2={cx} y1={wickTop} y2={wickBot} stroke={color} strokeWidth="1" />
                {/* Body */}
                <rect x={x + 1} y={bodyTop} width={w - 2} height={bodyH} fill={color} rx="1" opacity="0.85" />
              </g>
            );
          })}
        </svg>
        {/* Price labels */}
        <div className="absolute top-2 right-3 text-[9px] text-slate-500">€{maxPrice.toFixed(2)}</div>
        <div className="absolute bottom-2 right-3 text-[9px] text-slate-500">€{minPrice.toFixed(2)}</div>
        <div className="absolute top-1/2 right-3 -translate-y-1/2 text-[9px] text-slate-600">€{((maxPrice + minPrice) / 2).toFixed(2)}</div>
      </div>
      <div className="flex items-center justify-between mt-2 text-[10px] text-slate-500">
        <span>{sorted[0] ? new Date(sorted[0].timestamp).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' }) : ''}</span>
        <span>{sorted.length} candles</span>
        <span>{sorted[sorted.length - 1] ? new Date(sorted[sorted.length - 1].timestamp).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' }) : ''}</span>
      </div>
    </div>
  );
}

/* === Sub Components === */
function QuickStat({ label, value, subtext, icon: Icon, color }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</span>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: `${color}15` }}>
          <Icon className="w-3.5 h-3.5" style={{ color }} />
        </div>
      </div>
      <p className="text-lg font-bold text-white">{value}</p>
      {subtext && <p className="text-[10px] text-slate-500 mt-0.5">{subtext}</p>}
    </div>
  );
}

function BitvavoSettings({ userId, status, settings }) {
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Live editable settings
  const [useMock, setUseMock] = useState(settings?.use_mock !== false);
  const [autoTrade, setAutoTrade] = useState(!!settings?.auto_trade);
  const [tradeAmount, setTradeAmount] = useState(settings?.trade_amount || 5);
  const [settingsSaved, setSettingsSaved] = useState(false);

  // Sync state
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  useEffect(() => {
    setUseMock(settings?.use_mock !== false);
    setAutoTrade(!!settings?.auto_trade);
    setTradeAmount(settings?.trade_amount || 5);
  }, [settings]);

  const saveCredentials = async () => {
    if (!apiKey.trim() || !apiSecret.trim()) return;
    setSaving(true);
    await fetch(`${API}/api/trade/bitvavo/credentials/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret }),
    });
    setSaving(false); setSaved(true);
    setApiKey(''); setApiSecret('');
  };

  const saveTraderSettings = async () => {
    await fetch(`${API}/api/trade/settings/${userId}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ use_mock: useMock, auto_trade: autoTrade, trade_amount: parseFloat(tradeAmount) || 5 }),
    });
    setSettingsSaved(true);
    setTimeout(() => setSettingsSaved(false), 2000);
  };

  const syncOrders = async () => {
    setSyncing(true); setSyncResult(null);
    const res = await fetch(`${API}/api/trade/bitvavo/sync/${userId}`, { method: 'POST' })
      .then(r => r.json()).catch(() => ({ success: false, error: 'Verbinding mislukt' }));
    setSyncResult(res);
    setSyncing(false);
  };

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="p-5 rounded-xl border border-cyan-500/20" style={{ background: 'linear-gradient(135deg, rgba(6,182,212,0.06), rgba(59,130,246,0.04))' }}>
        <h2 className="text-lg font-bold text-white mb-1">Bitvavo Integratie</h2>
        <p className="text-xs text-slate-400">Koppel je Bitvavo account voor live trading en portfolio tracking.</p>
      </div>
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Key className="w-4 h-4 text-amber-400" /> API Credentials</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-2 p-2.5 bg-slate-800/30 rounded-lg">
            <span className="text-[10px] text-slate-500">Status:</span>
            {status?.connected ? (
              <span className="text-[10px] text-green-400 font-medium">Verbonden (LIVE)</span>
            ) : status?.placeholder ? (
              <span className="text-[10px] text-amber-400 font-medium">Placeholder keys - voer echte keys in</span>
            ) : (
              <span className="text-[10px] text-red-400 font-medium">Niet verbonden</span>
            )}
          </div>
          <input data-testid="bitvavo-key" type="text" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="API Key..."
            className="w-full px-3 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500" />
          <input data-testid="bitvavo-secret" type="password" value={apiSecret} onChange={e => setApiSecret(e.target.value)} placeholder="API Secret..."
            className="w-full px-3 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500" />
          <button data-testid="bitvavo-save-btn" onClick={saveCredentials} disabled={saving}
            className="w-full py-2.5 rounded-lg text-xs font-medium text-white bg-cyan-500 hover:bg-cyan-600 transition-colors disabled:opacity-50">
            {saving ? 'Opslaan...' : saved ? 'Opgeslagen!' : 'Opslaan'}
          </button>
        </div>
      </div>

      {/* Trader instellingen - editable */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Settings className="w-4 h-4 text-slate-400" /> Trader Instellingen</h3>
        <div className="space-y-3">
          {/* Mock / LIVE toggle */}
          <div className="flex items-center justify-between p-3 bg-slate-800/30 rounded-lg">
            <div>
              <span className="text-xs text-white font-medium">Handelsmodus</span>
              <p className="text-[10px] text-slate-500 mt-0.5">
                {useMock ? 'Mock: trades worden gesimuleerd' : 'LIVE: echte Bitvavo orders'}
              </p>
            </div>
            <button data-testid="toggle-mock" onClick={() => setUseMock(!useMock)}
              className={`relative w-14 h-7 rounded-full transition-colors ${useMock ? 'bg-blue-500' : 'bg-green-500'}`}>
              <span className={`absolute top-0.5 w-6 h-6 rounded-full bg-white transition-all ${useMock ? 'left-0.5' : 'left-7'}`} />
              <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold text-white/80 pointer-events-none">
                {useMock ? 'MOCK' : 'LIVE'}
              </span>
            </button>
          </div>

          {/* Auto trade toggle */}
          <div className="flex items-center justify-between p-3 bg-slate-800/30 rounded-lg">
            <div>
              <span className="text-xs text-white font-medium">Auto-trade</span>
              <p className="text-[10px] text-slate-500 mt-0.5">Monitor voert BUY/SELL automatisch uit bij signaal</p>
            </div>
            <button data-testid="toggle-auto-trade" onClick={() => setAutoTrade(!autoTrade)}
              className={`relative w-14 h-7 rounded-full transition-colors ${autoTrade ? 'bg-amber-500' : 'bg-slate-700'}`}>
              <span className={`absolute top-0.5 w-6 h-6 rounded-full bg-white transition-all ${autoTrade ? 'left-7' : 'left-0.5'}`} />
            </button>
          </div>

          {/* Trade amount */}
          <div className="flex items-center justify-between p-3 bg-slate-800/30 rounded-lg">
            <div>
              <span className="text-xs text-white font-medium">Trade bedrag (EUR)</span>
              <p className="text-[10px] text-slate-500 mt-0.5">Per order bij auto-trade</p>
            </div>
            <input data-testid="trade-amount-input" type="number" step="0.5" min="1" value={tradeAmount} onChange={e => setTradeAmount(e.target.value)}
              className="w-24 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white text-right focus:outline-none focus:border-amber-500" />
          </div>

          {!useMock && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-[11px] text-red-300">
              ⚠️ <strong>LIVE modus actief</strong> — trades gebruiken echte Bitvavo API met echt geld. Controleer alles goed voordat je Auto-trade aanzet!
            </div>
          )}

          <button data-testid="save-trader-settings" onClick={saveTraderSettings}
            className="w-full py-2.5 rounded-lg text-xs font-medium text-white bg-amber-500 hover:bg-amber-600 transition-colors">
            {settingsSaved ? 'Opgeslagen ✓' : 'Instellingen opslaan'}
          </button>
        </div>
      </div>

      {/* Sync Bitvavo orders */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2"><RefreshCw className="w-4 h-4 text-cyan-400" /> Order Historie Sync</h3>
        <p className="text-[11px] text-slate-400 mb-3">
          Importeer je echte Bitvavo aankopen/verkopen naar Spark's lokale trade historie. Handig voor orders die buiten Spark zijn gedaan (bv. je 10 BCH potjes).
        </p>
        <button data-testid="sync-bitvavo-btn" onClick={syncOrders} disabled={syncing || !status?.connected}
          className="w-full py-2.5 rounded-lg text-xs font-medium text-white bg-cyan-500 hover:bg-cyan-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          {syncing ? 'Bezig met synchroniseren...' : status?.connected ? 'Sync Bitvavo orders' : 'Eerst API keys invoeren'}
        </button>
        {syncResult && (
          <div className={`mt-3 p-3 rounded-lg text-[11px] ${syncResult.success ? 'bg-green-500/10 border border-green-500/20 text-green-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
            {syncResult.success
              ? `${syncResult.imported} nieuwe trades geïmporteerd (totaal: ${syncResult.total_trades}). Markten: ${syncResult.markets_synced?.join(', ')}`
              : `Fout: ${syncResult.error}`}
            {syncResult.errors?.length > 0 && (
              <ul className="mt-1 ml-4 list-disc">{syncResult.errors.map((e, i) => <li key={i}>{e}</li>)}</ul>
            )}
          </div>
        )}
      </div>

      {/* Donaties / Deposits */}
      {!isFamilie && <DonationsPanel userId={userId} />}
    </div>
  );
}

/* === Donaties / Deposits component === */
function DonationsPanel({ userId }) {
  const [deposits, setDeposits] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [amount, setAmount] = useState('');
  const [depType, setDepType] = useState('donation');
  const [source, setSource] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [tokenInfo, setTokenInfo] = useState(null);

  const load = async () => {
    const res = await fetch(`${API}/api/trade/deposits/${userId}`).then(r => r.json()).catch(() => ({ deposits: [] }));
    setDeposits(res);
    const tok = await fetch(`${API}/api/shop/token/price`).then(r => r.json()).catch(() => null);
    setTokenInfo(tok);
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  // Impact preview
  const amountNum = parseFloat(amount) || 0;
  const currentPrice = tokenInfo?.price_eur || 0;
  const currentBalance = tokenInfo?.bitvavo_balance || 0;
  const circulating = tokenInfo?.circulating || 1;
  const delta = depType === 'withdrawal' ? -amountNum : amountNum;
  const newBalance = currentBalance + delta;
  const newPrice = circulating > 0 ? (newBalance / circulating) : currentPrice;
  const priceImpact = newPrice - currentPrice;

  const save = async () => {
    if (!amount || parseFloat(amount) <= 0) return;
    setSaving(true);
    await fetch(`${API}/api/trade/deposits/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount_eur: parseFloat(amount),
        type: depType,
        source: source.trim() || 'onbekend',
        description: description.trim(),
      }),
    });
    setAmount(''); setSource(''); setDescription(''); setShowForm(false);
    await load();
    setSaving(false);
  };

  const remove = async (id) => {
    await fetch(`${API}/api/trade/deposits/${userId}/${id}`, { method: 'DELETE' });
    await load();
  };

  const totals = deposits?.totals || {};

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-purple-400" /> Donaties & Deposits
        </h3>
        <button data-testid="add-deposit-btn" onClick={() => setShowForm(!showForm)}
          className="text-[11px] px-2.5 py-1 rounded-md bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 transition-colors">
          {showForm ? 'Annuleer' : '+ Toevoegen'}
        </button>
      </div>
      <p className="text-[11px] text-slate-400 mb-3">
        Registreer extern geld (donatie, eigen storting, opname). Baseline wordt automatisch bijgewerkt zodat P&L zuiver trading-winst blijft.
      </p>

      {/* Totalen */}
      <div className="grid grid-cols-3 gap-2 mb-3 text-center">
        <div className="bg-slate-800/30 rounded-lg p-2">
          <p className="text-[9px] text-slate-500 uppercase">Donaties</p>
          <p className="text-xs font-bold text-purple-400">€{(totals.donations ?? 0).toFixed(2)}</p>
        </div>
        <div className="bg-slate-800/30 rounded-lg p-2">
          <p className="text-[9px] text-slate-500 uppercase">Eigen storting</p>
          <p className="text-xs font-bold text-cyan-400">€{(totals.deposits ?? 0).toFixed(2)}</p>
        </div>
        <div className="bg-slate-800/30 rounded-lg p-2">
          <p className="text-[9px] text-slate-500 uppercase">Opnames</p>
          <p className="text-xs font-bold text-orange-400">€{(totals.withdrawals ?? 0).toFixed(2)}</p>
        </div>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-3 space-y-2 mb-3">
          <div className="flex gap-2">
            {['donation', 'deposit', 'withdrawal'].map(t => (
              <button key={t} data-testid={`dep-type-${t}`} onClick={() => setDepType(t)}
                className={`flex-1 py-1.5 rounded text-[10px] uppercase tracking-wider font-medium ${
                  depType === t ? 'bg-purple-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}>
                {t === 'donation' ? 'Donatie' : t === 'deposit' ? 'Storting' : 'Opname'}
              </button>
            ))}
          </div>
          <input data-testid="dep-amount" type="number" step="0.01" placeholder="Bedrag in EUR" value={amount} onChange={e => setAmount(e.target.value)}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500" />
          <input data-testid="dep-source" type="text" placeholder="Van wie? (bv. Harry)" value={source} onChange={e => setSource(e.target.value)}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500" />
          <input data-testid="dep-description" type="text" placeholder="Omschrijving (verantwoording)" value={description} onChange={e => setDescription(e.target.value)}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500" />

          {/* Impact preview op ROAR token prijs */}
          {amountNum > 0 && tokenInfo && (
            <div className={`p-2.5 rounded-lg border ${priceImpact >= 0 ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
              <p className="text-[10px] text-slate-400 mb-1">Effect op ROAR token:</p>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400">€{currentPrice.toFixed(2)}</span>
                <span className={priceImpact >= 0 ? 'text-green-400' : 'text-red-400'}>
                  → €{newPrice.toFixed(2)} ({priceImpact >= 0 ? '+' : ''}€{priceImpact.toFixed(2)})
                </span>
              </div>
              <p className="text-[9px] text-slate-500 mt-1">
                {circulating} circulerende tokens • Jouw {circulating} stuk(s) = {priceImpact >= 0 ? '+' : ''}€{(priceImpact * circulating).toFixed(2)}
              </p>
            </div>
          )}

          <button data-testid="save-deposit-btn" onClick={save} disabled={saving || !amount}
            className="w-full py-2 rounded-lg bg-purple-500 hover:bg-purple-600 text-white text-xs font-medium disabled:opacity-50">
            {saving ? 'Opslaan...' : 'Registreren & baseline bijwerken'}
          </button>
        </div>
      )}

      {/* Lijst */}
      {deposits?.deposits?.length > 0 ? (
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {deposits.deposits.slice().reverse().map(d => (
            <div key={d.id} data-testid={`dep-${d.id}`} className="flex items-center justify-between px-3 py-2 bg-slate-800/30 rounded-lg">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-[9px] px-1.5 py-0.5 rounded uppercase ${
                    d.type === 'donation' ? 'bg-purple-500/20 text-purple-400' :
                    d.type === 'deposit' ? 'bg-cyan-500/20 text-cyan-400' :
                    'bg-orange-500/20 text-orange-400'
                  }`}>{d.type === 'donation' ? 'Donatie' : d.type === 'deposit' ? 'Storting' : 'Opname'}</span>
                  <span className="text-xs text-white font-medium">€{d.amount_eur.toFixed(2)}</span>
                  <span className="text-[10px] text-slate-500">van {d.source}</span>
                </div>
                {d.description && <p className="text-[10px] text-slate-500 mt-0.5 truncate">{d.description}</p>}
              </div>
              <button onClick={() => remove(d.id)} className="text-[10px] text-red-400/70 hover:text-red-400 ml-2">×</button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-[10px] text-slate-600 text-center py-2">Nog geen deposits/donaties</p>
      )}
    </div>
  );
}

export default TraderPage;
