import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  ShoppingBag, Star, Package, Tag, Gift, Sparkles,
  Lock, Clock, Coins, CheckCircle, AlertCircle, Loader2
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function WinkelPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [items, setItems] = useState([]);
  const [balance, setBalance] = useState({ spark_tokens: 0, credits: 0 });
  const [filterCat, setFilterCat] = useState('Alles');
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(null);
  const [result, setResult] = useState(null);

  const iconMap = { 'custom-emoji': Sparkles, 'kleur-thema': Tag, 'priority-support': Star, 'extra-storage': Package, 'ai-boost': Sparkles, 'gift-card': Gift };

  const loadData = () => {
    Promise.all([
      fetch(`${API}/api/shop/items`).then(r => r.json()).catch(() => ({ items: [] })),
      fetch(`${API}/api/shop/balance/${userId}`).then(r => r.json()).catch(() => ({ spark_tokens: 0, credits: 0 })),
    ]).then(([shopData, bal]) => {
      setItems(shopData.items || []);
      setBalance(bal);
      setLoading(false);
    });
  };

  useEffect(() => { loadData(); }, [userId]);

  const buyItem = async (itemId) => {
    setBuying(itemId); setResult(null);
    const res = await fetch(`${API}/api/shop/buy/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: itemId }),
    }).then(r => r.json()).catch(() => ({ success: false, error: 'Verbinding mislukt' }));
    setResult({ itemId, ...res });
    setBuying(null);
    if (res.success) setBalance(b => ({ ...b, spark_tokens: res.new_balance }));
  };

  const categories = ['Alles', ...new Set(items.map(i => i.categorie))];
  const filtered = filterCat === 'Alles' ? items : items.filter(i => i.categorie === filterCat);

  if (loading) return (
    <MainLayout activePage="winkel" onNavigate={onNavigate}>
      <div className="flex items-center justify-center h-full"><Loader2 className="w-8 h-8 text-purple-500 animate-spin" /></div>
    </MainLayout>
  );

  return (
    <MainLayout activePage="winkel" onNavigate={onNavigate}>
      <div data-testid="winkel-page" className="h-[calc(100vh-4rem)] flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #a855f7, #ec4899)' }}>
                <ShoppingBag className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-base font-bold text-white leading-tight">Winkel</h1>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider">{items.length} items</p>
              </div>
            </div>
            {/* Token balance badge */}
            <div data-testid="token-balance" className="flex items-center gap-2 px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-xl">
              <Coins className="w-4 h-4 text-amber-400" />
              <span className="text-sm font-bold text-amber-400">{balance.spark_tokens}</span>
              <span className="text-[10px] text-amber-400/60">tokens</span>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            <div className="p-4 rounded-xl border border-purple-500/20" style={{ background: 'linear-gradient(135deg, rgba(168,85,247,0.06), rgba(236,72,153,0.04))' }}>
              <h2 className="text-lg font-bold text-white mb-1">Spark Winkel</h2>
              <p className="text-xs text-slate-400">Besteed je Spark Tokens aan upgrades, modules en personalisatie.</p>
            </div>

            {/* Result message */}
            {result && (
              <div data-testid="purchase-result" className={`p-3 rounded-xl text-xs flex items-center gap-2 ${result.success ? 'bg-green-500/10 border border-green-500/20 text-green-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
                {result.success ? <CheckCircle className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
                {result.success ? result.message : result.error}
              </div>
            )}

            {/* Category filter */}
            <div className="flex flex-wrap gap-2">
              {categories.map(c => (
                <button key={c} onClick={() => setFilterCat(c)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filterCat === c ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' : 'bg-slate-800/50 text-slate-400 border border-transparent hover:border-slate-700'}`}>
                  {c}
                </button>
              ))}
            </div>

            {/* Items grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {filtered.map(item => {
                const Icon = iconMap[item.id] || Package;
                const canAfford = balance.spark_tokens >= item.prijs;
                const wasBought = result?.itemId === item.id && result?.success;
                return (
                  <div key={item.id} data-testid={`shop-item-${item.id}`}
                    className={`p-4 bg-slate-900/50 border rounded-xl transition-all ${item.beschikbaar ? 'border-slate-800 hover:border-purple-500/30' : 'border-slate-800/50 opacity-60'}`}>
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center flex-shrink-0">
                        <Icon className="w-5 h-5 text-purple-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-sm font-semibold text-white">{item.naam}</h3>
                          {!item.beschikbaar && <Lock className="w-3 h-3 text-slate-500" />}
                        </div>
                        <p className="text-[11px] text-slate-400 mb-3">{item.beschrijving}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">{item.categorie}</span>
                          <div className="flex items-center gap-1.5">
                            <Coins className="w-3 h-3 text-amber-400" />
                            <span className={`text-sm font-bold ${canAfford ? 'text-amber-400' : 'text-red-400'}`}>{item.prijs}</span>
                            <span className="text-[10px] text-slate-500">tokens</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    {item.beschikbaar ? (
                      <button data-testid={`buy-${item.id}`} onClick={() => buyItem(item.id)}
                        disabled={!canAfford || buying === item.id}
                        className={`mt-3 w-full py-2 rounded-lg text-xs font-medium text-white transition-colors disabled:opacity-50 ${
                          wasBought ? 'bg-green-500' : canAfford ? '' : 'bg-slate-700 cursor-not-allowed'
                        }`}
                        style={canAfford && !wasBought ? { background: 'linear-gradient(135deg, #a855f7, #ec4899)' } : undefined}>
                        {buying === item.id ? 'Bezig...' : wasBought ? 'Gekocht!' : !canAfford ? 'Te weinig tokens' : 'Kopen'}
                      </button>
                    ) : (
                      <div className="mt-3 w-full py-2 rounded-lg text-xs font-medium text-center text-slate-500 bg-slate-800/30 flex items-center justify-center gap-1">
                        <Clock className="w-3 h-3" /> Binnenkort
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default WinkelPage;
