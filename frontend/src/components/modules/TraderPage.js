import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  TrendingUp, TrendingDown, Activity, DollarSign,
  ArrowUpRight, ArrowDownRight, Clock, BarChart2,
  Settings, RefreshCw, Key, Link
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

export function TraderPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [activeTab, setActiveTab] = useState('overzicht');
  const [stats, setStats] = useState(null);
  const [trades, setTrades] = useState([]);
  const [markets, setMarkets] = useState({});
  const [bitvavoStatus, setBitvavoStatus] = useState(null);
  const [traderSettings, setTraderSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tradeFilter, setTradeFilter] = useState('all');

  useEffect(() => {
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

  const filteredTrades = tradeFilter === 'all' ? trades :
    tradeFilter === 'buy' ? trades.filter(t => t.action === 'BUY') :
    trades.filter(t => t.action === 'SELL');

  const tabs = [
    { id: 'overzicht', label: 'Overzicht' },
    { id: 'trades', label: `Trades (${stats?.total_trades || 0})` },
    { id: 'bitvavo', label: 'Bitvavo' },
  ];

  if (loading) return <MainLayout activePage="trade" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-green-500/30 border-t-green-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage="trade" onNavigate={onNavigate}>
      <div data-testid="trade-page" className="h-[calc(100vh-4rem)] flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #22c55e, #14b8a6)' }}>
              <TrendingUp className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Trade</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">
                {stats?.total_trades || 0} trades | {stats?.markets?.join(', ') || 'BCH-EUR'}
              </p>
            </div>
            <div className="ml-auto flex items-center gap-2">
              {bitvavoStatus?.connected ? (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-green-500/10 border border-green-500/20 text-[10px] text-green-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" /> Bitvavo Verbonden
                </span>
              ) : (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 text-[10px] text-slate-500">
                  <Link className="w-3 h-3" /> Niet verbonden
                </span>
              )}
            </div>
          </div>
          <div className="flex">
            {tabs.map(t => (
              <button key={t.id} data-testid={`trade-tab-${t.id}`} onClick={() => setActiveTab(t.id)}
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

            {/* OVERZICHT */}
            {activeTab === 'overzicht' && stats && (
              <>
                {/* Stats cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <StatCard label="Totaal Trades" value={stats.total_trades} color="#06b6d4" />
                  <StatCard label="Buys" value={stats.buys} color="#22c55e" />
                  <StatCard label="Sells" value={stats.sells} color="#ef4444" />
                  <StatCard label="P/L" value={`€${stats.profit_loss}`} color={stats.profit_loss >= 0 ? '#22c55e' : '#ef4444'} />
                </div>

                {/* Markets */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-cyan-400" /> Markten
                  </h3>
                  <div className="space-y-2">
                    {Object.entries(markets).map(([market, data]) => (
                      <div key={market} className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-xl">
                        <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-sm font-bold text-amber-400">
                          {market.split('-')[0]}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-white">{market}</p>
                          <p className="text-[10px] text-slate-500">{data.total} trades</p>
                        </div>
                        <div className="flex gap-3 text-xs">
                          <span className="text-green-400">{data.buys} buys</span>
                          <span className="text-red-400">{data.sells} sells</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Trade volumes */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
                    <p className="text-[10px] text-slate-500 mb-1">Totaal Gekocht</p>
                    <p className="text-lg font-bold text-green-400">€{stats.total_buy_eur}</p>
                    <p className="text-[10px] text-slate-600">Gem. prijs: €{stats.avg_buy_price}</p>
                  </div>
                  <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
                    <p className="text-[10px] text-slate-500 mb-1">Totaal Verkocht</p>
                    <p className="text-lg font-bold text-red-400">€{stats.total_sell_eur}</p>
                    <p className="text-[10px] text-slate-600">Gem. prijs: €{stats.avg_sell_price}</p>
                  </div>
                </div>

                {/* Trade type breakdown */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-white mb-3">Trade Breakdown</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-slate-800/30 rounded-lg text-center">
                      <p className="text-lg font-bold text-blue-400">{stats.mock_trades}</p>
                      <p className="text-[10px] text-slate-500">Mock Trades</p>
                    </div>
                    <div className="p-3 bg-slate-800/30 rounded-lg text-center">
                      <p className="text-lg font-bold text-amber-400">{stats.real_trades}</p>
                      <p className="text-[10px] text-slate-500">Real Trades</p>
                    </div>
                  </div>
                </div>

                {/* Recente trades preview */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-blue-400" /> Laatste 5 Trades
                  </h3>
                  <div className="space-y-1.5">
                    {trades.slice(0, 5).map(t => (
                      <TradeRow key={t.trade_id} trade={t} />
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* TRADES TAB */}
            {activeTab === 'trades' && (
              <>
                <div className="flex gap-2">
                  {[
                    { id: 'all', label: 'Alles', count: trades.length },
                    { id: 'buy', label: 'Buys', count: trades.filter(t => t.action === 'BUY').length },
                    { id: 'sell', label: 'Sells', count: trades.filter(t => t.action === 'SELL').length },
                  ].map(f => (
                    <button key={f.id} onClick={() => setTradeFilter(f.id)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium ${tradeFilter === f.id ? (f.id === 'buy' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : f.id === 'sell' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-slate-700 text-white border border-slate-600') : 'bg-slate-800/50 text-slate-400 border border-transparent'}`}>
                      {f.label} ({f.count})
                    </button>
                  ))}
                </div>

                <div className="space-y-1.5">
                  {filteredTrades.map(t => (
                    <TradeRow key={t.trade_id} trade={t} expanded />
                  ))}
                </div>
                {filteredTrades.length === 0 && (
                  <div className="py-12 text-center"><Activity className="w-10 h-10 text-slate-700 mx-auto mb-3" /><p className="text-sm text-slate-500">Geen trades gevonden</p></div>
                )}
              </>
            )}

            {/* BITVAVO TAB */}
            {activeTab === 'bitvavo' && (
              <BitvavoSettings userId={userId} status={bitvavoStatus} settings={traderSettings} />
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

function TradeRow({ trade, expanded = false }) {
  const isBuy = trade.action === 'BUY';
  return (
    <div data-testid={`trade-${trade.trade_id}`} className="flex items-center gap-3 p-2.5 bg-slate-800/30 rounded-lg">
      <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${isBuy ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
        {isBuy ? <ArrowDownRight className="w-3.5 h-3.5 text-green-400" /> : <ArrowUpRight className="w-3.5 h-3.5 text-red-400" />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold ${isBuy ? 'text-green-400' : 'text-red-400'}`}>{trade.action}</span>
          <span className="text-xs text-white">{trade.market}</span>
          {trade.mock && <span className="text-[9px] px-1 py-0.5 rounded bg-blue-500/10 text-blue-400">mock</span>}
        </div>
        {expanded && (
          <p className="text-[10px] text-slate-500">{trade.timestamp ? new Date(trade.timestamp).toLocaleString('nl-NL') : '?'}</p>
        )}
      </div>
      <div className="text-right">
        <p className="text-xs text-white font-medium">€{trade.amount?.toFixed(2)}</p>
        <p className="text-[10px] text-slate-500">@{trade.price?.toFixed(2)}</p>
      </div>
      <span className={`text-[9px] px-1.5 py-0.5 rounded ${trade.status === 'filled' ? 'bg-green-500/10 text-green-400' : 'bg-amber-500/10 text-amber-400'}`}>{trade.status}</span>
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
    <div className="space-y-4">
      <div className="p-4 rounded-xl border border-cyan-500/20" style={{ background: 'linear-gradient(135deg, rgba(6,182,212,0.06), rgba(59,130,246,0.04))' }}>
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
            className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500" />
          <input data-testid="bitvavo-secret" type="password" value={apiSecret} onChange={e => setApiSecret(e.target.value)} placeholder="API Secret..."
            className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500" />
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
            <span className="text-xs text-white font-medium">€{settings?.trade_amount || 5}</span>
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

function StatCard({ label, value, color }) {
  return (
    <div className="p-3 bg-slate-900/50 border border-slate-800 rounded-xl text-center">
      <p className="text-lg font-bold" style={{ color }}>{value}</p>
      <p className="text-[10px] text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}

export default TraderPage;
