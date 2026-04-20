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
  const userId = user?.id || 'user-001';
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
    Promise.all([
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

  const loadLiveData = useCallback(() => {
    fetch(`${API}/api/trade/tickers`).then(r => r.json()).then(d => setTickers(d.tickers || [])).catch(() => {});
    fetch(`${API}/api/trade/candles?market=${candleMarket}&interval=${candleInterval}&limit=50`)
      .then(r => r.json()).then(d => setCandles(d.candles || [])).catch(() => {});
  }, [candleMarket, candleInterval]);

  const loadMonitorStatus = useCallback(() => {
    fetch(`${API}/api/trade/monitor/status`).then(r => r.json()).then(d => setMonitorStatus(d.status || null)).catch(() => {});
    fetch(`${API}/api/trade/monitor/decisions?limit=20`).then(r => r.json()).then(d => setDecisions(d.decisions || [])).catch(() => {});
  }, []);

  const loadBalance = useCallback(() => {
    fetch(`${API}/api/trade/bitvavo/balance/${userId}`).then(r => r.json()).then(d => setBvBalance(d)).catch(() => {});
  }, [userId]);

  const loadPotjes = useCallback(() => {
    fetch(`${API}/api/trade/potjes/${userId}`).then(r => r.json()).then(d => setPotjes(d)).catch(() => {});
  }, [userId]);

  const loadContext = useCallback(() => {
    fetch(`${API}/api/trade/context/${candleMarket}`).then(r => r.json()).then(d => setMarketContext(d)).catch(() => {});
  }, [candleMarket]);

  const refreshAllContexts = async () => {
    setContextLoading(true);
    await fetch(`${API}/api/trade/context/refresh-all`, { method: 'POST' });
    loadContext();
    setContextLoading(false);
  };

  useEffect(() => { loadCoreData(); loadLiveData(); loadMonitorStatus(); loadBalance(); loadPotjes(); loadContext(); }, [loadCoreData, loadLiveData, loadMonitorStatus, loadBalance, loadPotjes, loadContext]);

  // Auto-refresh live data every 30s, monitor every 10s when running
  useEffect(() => {
    const liveTimer = setInterval(loadLiveData, 30000);
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
  const startMonitor = async () => {
    const settings = traderSettings || {};
    await fetch(`${API}/api/trade/monitor/start`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        interval: 30, market: candleMarket, candle_interval: candleInterval,
        user_id: userId, auto_trade: settings.auto_trade || false,
        trade_amount: settings.trade_amount || 5, use_mock: settings.use_mock !== false,
        use_potjes: usePotjes,
      }),
    });
    loadMonitorStatus();
    if (usePotjes) loadPotjes();
  };
  const stopMonitor = async () => { await fetch(`${API}/api/trade/monitor/stop`, { method: 'POST' }); loadMonitorStatus(); };
  const pauseMonitor = async () => { await fetch(`${API}/api/trade/monitor/pause`, { method: 'POST' }); loadMonitorStatus(); };

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
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
              <Settings className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>

        {activeView === 'bitvavo' ? (
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
                      <span className="text-sm font-semibold text-white">BCH-EUR</span>
                      {/* Countdown */}
                      <div data-testid="candle-countdown" className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700">
                        <Timer className="w-3 h-3 text-amber-400" />
                        <span className="text-[10px] font-mono text-amber-400">{countdown}</span>
                        <span className="text-[9px] text-slate-500">{INTERVAL_LABELS[candleInterval]}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {['15m', '1h', '4h', '1d'].map(iv => (
                        <button key={iv} data-testid={`interval-${iv}`} onClick={() => setCandleInterval(iv)}
                          className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition-all ${candleInterval === iv ? 'bg-amber-500/20 text-amber-400' : 'text-slate-500 hover:text-slate-300'}`}>
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
                    {monitorStatus?.running ? (
                      <div className="space-y-3">
                        {/* Status bar */}
                        <div className="flex items-center gap-4 text-[10px] flex-wrap">
                          <span className="flex items-center gap-1 text-green-400"><span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" /> Actief</span>
                          <span className="text-slate-400">Cyclus #{monitorStatus.cycles}</span>
                          <span className="text-slate-400">{monitorStatus.market} ({monitorStatus.candle_interval})</span>
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
                        <span className="text-slate-400">Tier: <span className="text-amber-400 font-bold">{potjes.summary?.current_tier}</span></span>
                        <span className="text-slate-400">Totaal: <span className="text-white font-medium">€{potjes.summary?.total_capital?.toFixed(2)}</span></span>
                        <span className="text-slate-400">Open: <span className="text-amber-400">{potjes.summary?.open_positions}</span>/{potjes.summary?.pot_count}</span>
                        <span className={`${potjes.summary?.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          P&L: €{potjes.summary?.total_pnl?.toFixed(3)}
                        </span>
                        <button onClick={loadPotjes} className="text-slate-500 hover:text-white">
                          <RefreshCw className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                    {/* Tier progress bar */}
                    {potjes.summary?.next_tier_threshold && (
                      <div className="px-4 pt-3 pb-1">
                        <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
                          <span>Tier {potjes.summary.current_tier + 1} bij €{potjes.summary.next_tier_threshold}</span>
                          <span>{potjes.summary.progress_to_next_tier}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all" style={{ width: `${Math.min(100, potjes.summary.progress_to_next_tier)}%` }} />
                        </div>
                      </div>
                    )}
                    <div className="p-3 grid grid-cols-2 md:grid-cols-5 gap-2">
                      {potjes.potjes?.map(p => {
                        const open = p.position?.is_open;
                        const pnl = p.stats?.total_pnl || 0;
                        return (
                          <div key={p.id} data-testid={`pot-${p.id}`}
                            className={`rounded-xl p-2.5 border ${open ? 'bg-amber-500/10 border-amber-500/30' : 'bg-slate-800/30 border-slate-700'}`}>
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-[10px] font-bold text-white">{p.id}</span>
                              <span className="text-[9px] text-slate-400">€{p.capital?.toFixed(2)}</span>
                            </div>
                            {open ? (
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
                        <button key={t.market} data-testid={`watch-${t.symbol}`} onClick={() => setQtMarket(t.market)}
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
                    {trades.slice(0, 8).map(trade => (
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

            {/* Quick Trade Panel */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
              <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-400" /> Snel Handelen
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Markt</label>
                  <select data-testid="quick-trade-market" value={qtMarket} onChange={e => setQtMarket(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:border-amber-500 focus:outline-none">
                    <option value="BCH-EUR">BCH-EUR</option>
                    <option value="BTC-EUR">BTC-EUR</option>
                    <option value="ETH-EUR">ETH-EUR</option>
                    <option value="SOL-EUR">SOL-EUR</option>
                    <option value="ADA-EUR">ADA-EUR</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Bedrag (EUR)</label>
                  <input data-testid="quick-trade-amount" type="number" value={qtAmount} onChange={e => setQtAmount(e.target.value)} placeholder="5.00"
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Type</label>
                  <div className="flex gap-2">
                    <button data-testid="quick-trade-buy" onClick={() => setQtSide('buy')}
                      className={`flex-1 py-3 rounded-xl font-medium transition-colors text-sm ${qtSide === 'buy' ? 'bg-green-500 text-white' : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'}`}>
                      Koop
                    </button>
                    <button data-testid="quick-trade-sell" onClick={() => setQtSide('sell')}
                      className={`flex-1 py-3 rounded-xl font-medium transition-colors text-sm ${qtSide === 'sell' ? 'bg-red-500 text-white' : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'}`}>
                      Verkoop
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Modus</label>
                  <div className="flex items-center gap-2 py-3 px-4 bg-slate-800 rounded-xl text-sm">
                    <span className={`w-2 h-2 rounded-full ${traderSettings?.use_mock !== false ? 'bg-blue-400' : 'bg-green-400 animate-pulse'}`} />
                    <span className={traderSettings?.use_mock !== false ? 'text-blue-400' : 'text-green-400'}>
                      {traderSettings?.use_mock !== false ? 'Mock' : 'LIVE'}
                    </span>
                  </div>
                </div>
                <div>
                  <button data-testid="quick-trade-submit" onClick={executeQuickTrade} disabled={qtLoading}
                    className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold rounded-xl hover:from-amber-400 hover:to-orange-500 transition-all text-sm disabled:opacity-50">
                    {qtLoading ? 'Bezig...' : 'Order Plaatsen'}
                  </button>
                </div>
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
    </div>
  );
}

export default TraderPage;
