import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  TrendingUp, TrendingDown, Activity, DollarSign,
  ArrowUpRight, ArrowDownRight, Clock,
  BarChart2, PieChart, Wallet, RefreshCw,
  Settings, Bell, Key, Link, GripVertical, Loader2
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
  const [selectedCrypto, setSelectedCrypto] = useState('BCH');
  const [draggedCard, setDraggedCard] = useState(null);
  const [dragOverIndex, setDragOverIndex] = useState(null);

  const loadData = () => {
    Promise.all([
      fetch(`${API}/api/trade/stats/${userId}`).then(r => r.json()).catch(() => ({})),
      fetch(`${API}/api/trade/history/${userId}?limit=500`).then(r => r.json()).catch(() => ({ trades: [] })),
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
  };

  useEffect(() => { loadData(); }, [userId]);

  // Build portfolio data from real trade stats
  const portfolio = stats ? {
    totalValue: Math.abs(stats.total_buy_eur - stats.total_sell_eur),
    dayChange: stats.profit_loss || 0,
    dayChangePercent: stats.total_buy_eur > 0 ? ((stats.profit_loss / stats.total_buy_eur) * 100).toFixed(1) : 0,
    assets: Object.entries(markets).map(([market, data]) => {
      const symbol = market.split('-')[0];
      const totalValue = trades.filter(t => t.market === market && t.action === 'BUY').reduce((s, t) => s + (t.amount || 0), 0);
      return { symbol, market, trades: data.total, buys: data.buys, sells: data.sells, value: totalValue };
    })
  } : null;

  // Build price chart data from recent trades
  const chartData = trades.slice(0, 30).reverse().map(t => t.price || 0);
  const chartMax = Math.max(...chartData, 1);
  const chartMin = chartData.filter(p => p > 0).length > 0 ? Math.min(...chartData.filter(p => p > 0)) : 0;
  const chartRange = chartMax - chartMin || 1;

  // Drag handlers
  const handleDragStart = (e, index) => { setDraggedCard(index); e.dataTransfer.effectAllowed = 'move'; };
  const handleDragEnd = () => { setDraggedCard(null); setDragOverIndex(null); };
  const handleDragOver = (e, index) => { e.preventDefault(); if (draggedCard !== null) setDragOverIndex(index); };
  const handleDrop = (e, dropIndex) => { e.preventDefault(); setDraggedCard(null); setDragOverIndex(null); };

  if (loading) return (
    <MainLayout activePage="trade" onNavigate={onNavigate}>
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-green-500 animate-spin" />
      </div>
    </MainLayout>
  );

  return (
    <MainLayout activePage="trade" onNavigate={onNavigate}>
      <div data-testid="trade-page" className="p-4 md:p-6 space-y-5 max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Crypto Trader</h1>
              <p className="text-xs text-slate-400">
                {stats?.total_trades || 0} trades | {stats?.markets?.join(', ') || 'BCH-EUR'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {bitvavoStatus?.connected ? (
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/10 border border-green-500/20 text-[10px] text-green-400">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" /> Bitvavo
              </span>
            ) : (
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 text-[10px] text-slate-500">
                <Link className="w-3 h-3" /> Offline
              </span>
            )}
            <button onClick={loadData} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
              <RefreshCw className="w-4 h-4 text-slate-400" />
            </button>
            <button onClick={() => setActiveView(activeView === 'bitvavo' ? 'dashboard' : 'bitvavo')}
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
              <Settings className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>

        {activeView === 'bitvavo' ? (
          <BitvavoSettings userId={userId} status={bitvavoStatus} settings={traderSettings} />
        ) : (
          <>
            {/* Quick Stats Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <QuickStat
                label="Totaal Trades"
                value={stats?.total_trades || 0}
                icon={Activity}
                color="#06b6d4"
              />
              <QuickStat
                label="Gekocht (EUR)"
                value={`\u20AC${stats?.total_buy_eur || 0}`}
                change={stats?.buys || 0}
                subtext={`${stats?.buys || 0} buys`}
                icon={ArrowDownRight}
                color="#22c55e"
              />
              <QuickStat
                label="Verkocht (EUR)"
                value={`\u20AC${stats?.total_sell_eur || 0}`}
                subtext={`${stats?.sells || 0} sells`}
                icon={ArrowUpRight}
                color="#ef4444"
              />
              <QuickStat
                label="Winst/Verlies"
                value={`\u20AC${stats?.profit_loss || 0}`}
                change={parseFloat(portfolio?.dayChangePercent || 0)}
                icon={DollarSign}
                color={stats?.profit_loss >= 0 ? '#22c55e' : '#ef4444'}
              />
            </div>

            {/* Main Grid - Draggable Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

              {/* Portfolio Card */}
              <DraggableCard index={0} isDragging={draggedCard === 0} isDragOver={dragOverIndex === 0}
                onDragStart={handleDragStart} onDragEnd={handleDragEnd} onDragOver={handleDragOver} onDrop={handleDrop}
                className="lg:col-span-2">
                <CardHeader title="Portfolio Overzicht" icon={PieChart} />
                <div className="p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Donut Chart */}
                    <div className="aspect-square max-w-[200px] mx-auto relative">
                      <div className="absolute inset-0 rounded-full border-[20px] border-amber-500" style={{ clipPath: 'polygon(50% 50%, 100% 0, 100% 100%, 50% 100%)' }} />
                      <div className="absolute inset-0 rounded-full border-[20px] border-green-500" style={{ clipPath: 'polygon(50% 50%, 50% 0, 100% 0)' }} />
                      <div className="absolute inset-0 rounded-full border-[20px] border-red-500/30" style={{ clipPath: 'polygon(50% 50%, 30% 0, 50% 0)' }} />
                      <div className="absolute inset-4 bg-slate-900 rounded-full flex items-center justify-center">
                        <div className="text-center">
                          <p className="text-xl font-bold text-white">{stats?.total_trades || 0}</p>
                          <p className="text-[10px] text-slate-400">trades</p>
                        </div>
                      </div>
                    </div>
                    {/* Market List */}
                    <div className="space-y-3">
                      {Object.entries(markets).map(([market, data]) => (
                        <div key={market} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
                              <span className="text-sm font-bold">{market.split('-')[0][0]}</span>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-white">{market}</p>
                              <p className="text-[10px] text-slate-500">{data.total} trades</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-green-400">{data.buys} buys</p>
                            <p className="text-xs text-red-400">{data.sells} sells</p>
                          </div>
                        </div>
                      ))}
                      {Object.keys(markets).length === 0 && (
                        <p className="text-xs text-slate-500 text-center py-4">Geen markten gevonden</p>
                      )}
                    </div>
                  </div>
                </div>
              </DraggableCard>

              {/* Trade Breakdown */}
              <DraggableCard index={1} isDragging={draggedCard === 1} isDragOver={dragOverIndex === 1}
                onDragStart={handleDragStart} onDragEnd={handleDragEnd} onDragOver={handleDragOver} onDrop={handleDrop}>
                <CardHeader title="Trade Breakdown" icon={Activity} />
                <div className="p-4 space-y-3">
                  <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-blue-500" />
                      <span className="text-xs text-slate-300">Mock Trades</span>
                    </div>
                    <span className="text-sm font-bold text-blue-400">{stats?.mock_trades || 0}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-amber-500" />
                      <span className="text-xs text-slate-300">Real Trades</span>
                    </div>
                    <span className="text-sm font-bold text-amber-400">{stats?.real_trades || 0}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-green-500" />
                      <span className="text-xs text-slate-300">Gem. Koopprijs</span>
                    </div>
                    <span className="text-sm font-bold text-green-400">&euro;{stats?.avg_buy_price || 0}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-red-500" />
                      <span className="text-xs text-slate-300">Gem. Verkoopprijs</span>
                    </div>
                    <span className="text-sm font-bold text-red-400">&euro;{stats?.avg_sell_price || 0}</span>
                  </div>
                  {/* Trader settings quick view */}
                  <div className="mt-2 pt-3 border-t border-slate-800 space-y-2">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider">Instellingen</p>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-400">Markt</span>
                      <span className="text-[10px] text-white font-medium">{traderSettings?.market || 'BCH-EUR'}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-400">Trade bedrag</span>
                      <span className="text-[10px] text-white font-medium">&euro;{traderSettings?.trade_amount || 5}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-400">Mock modus</span>
                      <span className={`text-[10px] font-medium ${traderSettings?.use_mock ? 'text-blue-400' : 'text-green-400'}`}>
                        {traderSettings?.use_mock ? 'Aan' : 'Uit (LIVE)'}
                      </span>
                    </div>
                  </div>
                </div>
              </DraggableCard>

              {/* Chart Card */}
              <DraggableCard index={2} isDragging={draggedCard === 2} isDragOver={dragOverIndex === 2}
                onDragStart={handleDragStart} onDragEnd={handleDragEnd} onDragOver={handleDragOver} onDrop={handleDrop}
                className="lg:col-span-2">
                <CardHeader title={`${stats?.markets?.[0] || 'BCH-EUR'} Prijsverloop`} icon={BarChart2} />
                <div className="p-4">
                  <div className="h-48 bg-slate-800/30 rounded-xl flex items-end justify-between p-3 gap-0.5">
                    {chartData.length > 0 ? chartData.map((price, i) => {
                      const pct = ((price - chartMin) / chartRange) * 100;
                      const prevPrice = i > 0 ? chartData[i - 1] : price;
                      const isUp = price >= prevPrice;
                      return (
                        <div key={i} className="flex-1 group relative"
                          style={{ height: `${Math.max(pct, 5)}%` }}>
                          <div className={`w-full h-full rounded-t transition-all ${isUp ? 'bg-gradient-to-t from-green-500/50 to-green-500/10 hover:from-green-500/70' : 'bg-gradient-to-t from-red-500/50 to-red-500/10 hover:from-red-500/70'}`} />
                          <div className="absolute -top-6 left-1/2 -translate-x-1/2 hidden group-hover:block bg-slate-800 px-1.5 py-0.5 rounded text-[9px] text-white whitespace-nowrap z-10">
                            &euro;{price.toFixed(2)}
                          </div>
                        </div>
                      );
                    }) : (
                      <div className="flex-1 flex items-center justify-center text-xs text-slate-500">Geen data</div>
                    )}
                  </div>
                  {chartData.length > 0 && (
                    <div className="flex items-center justify-between mt-2 text-[10px] text-slate-500">
                      <span>&euro;{chartMin.toFixed(2)}</span>
                      <span>Laatste {chartData.length} trades</span>
                      <span>&euro;{chartMax.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </DraggableCard>

              {/* Recent Trades Card */}
              <DraggableCard index={3} isDragging={draggedCard === 3} isDragOver={dragOverIndex === 3}
                onDragStart={handleDragStart} onDragEnd={handleDragEnd} onDragOver={handleDragOver} onDrop={handleDrop}>
                <CardHeader title="Recente Trades" icon={Clock} />
                <div className="p-4 space-y-2 max-h-[350px] overflow-y-auto">
                  {trades.slice(0, 10).map(trade => (
                    <div key={trade.trade_id} data-testid={`trade-${trade.trade_id}`}
                      className="flex items-center justify-between p-2.5 bg-slate-800/50 rounded-xl">
                      <div className="flex items-center gap-2.5">
                        <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${trade.action === 'BUY' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                          {trade.action === 'BUY'
                            ? <ArrowDownRight className="w-3.5 h-3.5 text-green-400" />
                            : <ArrowUpRight className="w-3.5 h-3.5 text-red-400" />
                          }
                        </div>
                        <div>
                          <p className="text-xs font-medium text-white flex items-center gap-1.5">
                            <span className={trade.action === 'BUY' ? 'text-green-400' : 'text-red-400'}>{trade.action === 'BUY' ? 'Koop' : 'Verkoop'}</span>
                            {trade.market?.split('-')[0]}
                          </p>
                          <p className="text-[10px] text-slate-500">
                            {trade.timestamp ? new Date(trade.timestamp).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }) : '?'}
                            {trade.mock && <span className="ml-1 text-blue-400">[mock]</span>}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-white">&euro;{trade.amount?.toFixed(2)}</p>
                        <span className={`text-[9px] px-1.5 py-0.5 rounded ${trade.status === 'filled' ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'}`}>
                          {trade.status === 'filled' ? 'Voltooid' : trade.status}
                        </span>
                      </div>
                    </div>
                  ))}
                  {trades.length === 0 && (
                    <div className="py-8 text-center">
                      <Activity className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                      <p className="text-xs text-slate-500">Nog geen trades</p>
                    </div>
                  )}
                </div>
              </DraggableCard>
            </div>

            {/* Quick Trade Panel */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
              <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-amber-400" />
                Snel Handelen
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Markt</label>
                  <select data-testid="quick-trade-market" className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:border-amber-500 focus:outline-none">
                    {Object.keys(markets).map(m => <option key={m}>{m}</option>)}
                    {Object.keys(markets).length === 0 && <option>BCH-EUR</option>}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Bedrag (EUR)</label>
                  <input data-testid="quick-trade-amount"
                    type="number" placeholder={traderSettings?.trade_amount || '5.00'}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Type</label>
                  <div className="flex gap-2">
                    <button data-testid="quick-trade-buy" className="flex-1 py-3 bg-green-500/20 text-green-400 rounded-xl font-medium hover:bg-green-500/30 transition-colors text-sm">
                      Koop
                    </button>
                    <button data-testid="quick-trade-sell" className="flex-1 py-3 bg-red-500/20 text-red-400 rounded-xl font-medium hover:bg-red-500/30 transition-colors text-sm">
                      Verkoop
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-2">Actie</label>
                  <button data-testid="quick-trade-submit" className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold rounded-xl hover:from-amber-400 hover:to-orange-500 transition-all text-sm">
                    Order Plaatsen
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </MainLayout>
  );
}

/* === Sub Components === */

function QuickStat({ label, value, change, subtext, icon: Icon, color }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</span>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: `${color}15` }}>
          <Icon className="w-3.5 h-3.5" style={{ color }} />
        </div>
      </div>
      <p className="text-lg font-bold text-white">{value}</p>
      {change !== undefined && (
        <p className={`text-[10px] flex items-center gap-1 mt-1 ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
          {typeof change === 'number' ? `${Math.abs(change)}%` : change}
        </p>
      )}
      {subtext && <p className="text-[10px] text-slate-500 mt-0.5">{subtext}</p>}
    </div>
  );
}

function CardHeader({ title, icon: Icon }) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2">
        <Icon className="w-4 h-4 text-amber-400" />
        {title}
      </h3>
    </div>
  );
}

function DraggableCard({ children, index, isDragging, isDragOver, onDragStart, onDragEnd, onDragOver, onDrop, className = '' }) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, index)}
      onDragEnd={onDragEnd}
      onDragOver={(e) => onDragOver(e, index)}
      onDrop={(e) => onDrop(e, index)}
      className={`
        bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden cursor-move
        transition-all duration-200 group relative
        ${isDragging ? 'opacity-50 scale-95' : ''}
        ${isDragOver ? 'ring-2 ring-amber-500/50 scale-[1.02]' : ''}
        hover:border-slate-700
        ${className}
      `}
    >
      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10">
        <GripVertical className="w-4 h-4 text-slate-500" />
      </div>
      {children}
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
    setSaving(false);
    setSaved(true);
    setApiKey('');
    setApiSecret('');
  };

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="p-5 rounded-xl border border-cyan-500/20" style={{ background: 'linear-gradient(135deg, rgba(6,182,212,0.06), rgba(59,130,246,0.04))' }}>
        <h2 className="text-lg font-bold text-white mb-1">Bitvavo Integratie</h2>
        <p className="text-xs text-slate-400">Koppel je Bitvavo account voor live trading en portfolio tracking.</p>
      </div>

      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Key className="w-4 h-4 text-amber-400" /> API Credentials
        </h3>
        <div className="space-y-3">
          <div className="flex items-center gap-2 p-2.5 bg-slate-800/30 rounded-lg">
            <span className="text-[10px] text-slate-500">Status:</span>
            {status?.connected ? (
              <span className="text-[10px] text-green-400 font-medium">Verbonden sinds {new Date(status.connected_at).toLocaleDateString('nl-NL')}</span>
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
            {saving ? 'Opslaan...' : saved ? 'Opgeslagen!' : 'API Credentials Opslaan'}
          </button>
        </div>
      </div>

      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Settings className="w-4 h-4 text-slate-400" /> Trader Instellingen
        </h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between p-2.5 bg-slate-800/30 rounded-lg">
            <span className="text-xs text-slate-400">Trade bedrag</span>
            <span className="text-xs text-white font-medium">&euro;{settings?.trade_amount || 5}</span>
          </div>
          <div className="flex items-center justify-between p-2.5 bg-slate-800/30 rounded-lg">
            <span className="text-xs text-slate-400">Markt</span>
            <span className="text-xs text-white font-medium">{settings?.market || 'BCH-EUR'}</span>
          </div>
          <div className="flex items-center justify-between p-2.5 bg-slate-800/30 rounded-lg">
            <span className="text-xs text-slate-400">Mock modus</span>
            <span className={`text-xs font-medium ${settings?.use_mock ? 'text-blue-400' : 'text-green-400'}`}>{settings?.use_mock ? 'Aan' : 'Uit (LIVE)'}</span>
          </div>
          <div className="flex items-center justify-between p-2.5 bg-slate-800/30 rounded-lg">
            <span className="text-xs text-slate-400">Auto trade</span>
            <span className={`text-xs font-medium ${settings?.auto_trade ? 'text-green-400' : 'text-slate-500'}`}>{settings?.auto_trade ? 'Aan' : 'Uit'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TraderPage;
