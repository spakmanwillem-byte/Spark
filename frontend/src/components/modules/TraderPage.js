import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  TrendingUp, TrendingDown, Activity, DollarSign,
  ArrowUpRight, ArrowDownRight, Clock, Play, Pause, Square,
  BarChart2, PieChart, RefreshCw, Eye,
  Settings, Key, Link, GripVertical, Loader2, Zap, Radio
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

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

  // Monitor
  const [monitorStatus, setMonitorStatus] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const monitorPollRef = useRef(null);

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

  useEffect(() => { loadCoreData(); loadLiveData(); loadMonitorStatus(); }, [loadCoreData, loadLiveData, loadMonitorStatus]);

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

  // Monitor controls
  const startMonitor = async () => {
    const settings = traderSettings || {};
    await fetch(`${API}/api/trade/monitor/start`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        interval: 30, market: candleMarket, candle_interval: candleInterval,
        user_id: userId, auto_trade: settings.auto_trade || false,
        trade_amount: settings.trade_amount || 5, use_mock: settings.use_mock !== false,
      }),
    });
    loadMonitorStatus();
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
              <p className="text-xs text-slate-400">{stats?.total_trades || 0} trades | {tickers[0] ? `BCH €${tickers[0].last}` : 'Laden...'}</p>
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
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <QuickStat label="Totaal Trades" value={stats?.total_trades || 0} icon={Activity} color="#06b6d4" />
              <QuickStat label="Gekocht" value={`\u20AC${stats?.total_buy_eur || 0}`} subtext={`${stats?.buys || 0} buys`} icon={ArrowDownRight} color="#22c55e" />
              <QuickStat label="Verkocht" value={`\u20AC${stats?.total_sell_eur || 0}`} subtext={`${stats?.sells || 0} sells`} icon={ArrowUpRight} color="#ef4444" />
              <QuickStat label="Winst/Verlies" value={`\u20AC${stats?.profit_loss || 0}`} icon={DollarSign} color={stats?.profit_loss >= 0 ? '#22c55e' : '#ef4444'} />
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
                      <select data-testid="chart-market-select" value={candleMarket} onChange={e => setCandleMarket(e.target.value)}
                        className="bg-transparent text-sm font-semibold text-white focus:outline-none cursor-pointer">
                        <option value="BCH-EUR" className="bg-slate-900">BCH-EUR</option>
                        <option value="BTC-EUR" className="bg-slate-900">BTC-EUR</option>
                        <option value="ETH-EUR" className="bg-slate-900">ETH-EUR</option>
                        <option value="SOL-EUR" className="bg-slate-900">SOL-EUR</option>
                        <option value="ADA-EUR" className="bg-slate-900">ADA-EUR</option>
                      </select>
                    </div>
                    <div className="flex items-center gap-1">
                      {['1h', '4h', '1d'].map(iv => (
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
                        <div className="flex items-center gap-4 text-[10px]">
                          <span className="flex items-center gap-1 text-green-400"><span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" /> Actief</span>
                          <span className="text-slate-400">Cyclus #{monitorStatus.cycles}</span>
                          <span className="text-slate-400">{monitorStatus.market} ({monitorStatus.candle_interval})</span>
                          <span className="text-slate-400">Prijs: €{monitorStatus.last_price?.toFixed(2)}</span>
                          {monitorStatus.auto_trade && <span className="text-amber-400">Auto-trade AAN</span>}
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
              </div>

              {/* Right: Watchlist + Recent Trades */}
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
                        <button key={t.market} data-testid={`watch-${t.symbol}`} onClick={() => { setCandleMarket(t.market); setQtMarket(t.market); }}
                          className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${candleMarket === t.market ? 'bg-amber-500/10 border border-amber-500/20' : 'hover:bg-slate-800/50'}`}>
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
            {status?.connected
              ? <span className="text-[10px] text-green-400 font-medium">Verbonden</span>
              : <span className="text-[10px] text-red-400 font-medium">Niet verbonden</span>}
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
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Settings className="w-4 h-4 text-slate-400" /> Trader Instellingen</h3>
        <div className="space-y-2">
          {[
            ['Trade bedrag', `€${settings?.trade_amount || 5}`],
            ['Markt', settings?.market || 'BCH-EUR'],
            ['Mock modus', settings?.use_mock !== false ? 'Aan' : 'Uit (LIVE)'],
            ['Auto trade', settings?.auto_trade ? 'Aan' : 'Uit'],
          ].map(([label, val]) => (
            <div key={label} className="flex items-center justify-between p-2.5 bg-slate-800/30 rounded-lg">
              <span className="text-xs text-slate-400">{label}</span>
              <span className="text-xs text-white font-medium">{val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default TraderPage;
