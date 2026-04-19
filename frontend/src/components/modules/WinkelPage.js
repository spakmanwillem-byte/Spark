import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  ShoppingBag, Coins, Plus, Minus, ShoppingCart, X,
  Package, Tag, Truck, CreditCard, Loader2, Check,
  TrendingUp, ChevronRight
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function WinkelPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [products, setProducts] = useState([]);
  const [tokenInfo, setTokenInfo] = useState(null);
  const [userBalance, setUserBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cart, setCart] = useState([]);
  const [showCart, setShowCart] = useState(false);
  const [ordering, setOrdering] = useState(false);
  const [orderResult, setOrderResult] = useState(null);
  const [activeTab, setActiveTab] = useState('merch');

  // Token buy state
  const [tokenQty, setTokenQty] = useState('1');
  const [buyingToken, setBuyingToken] = useState(false);
  const [tokenResult, setTokenResult] = useState(null);

  const loadData = useCallback(() => {
    Promise.all([
      fetch(`${API}/api/shop/products`).then(r => r.json()).catch(() => ({ products: [] })),
      fetch(`${API}/api/shop/token/price`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/shop/token/balance/${userId}`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/wallet/user/${userId}`).then(r => r.json()).catch(() => null),
    ]).then(([prods, price, bal, wallet]) => {
      setProducts(prods.products || []);
      setTokenInfo(price);
      setUserBalance({ ...bal, wallet_eur: wallet?.balance_eur || 0 });
      setLoading(false);
    });
  }, [userId]);

  useEffect(() => { loadData(); }, [loadData]);

  const merchProducts = products.filter(p => p.category === 'merch');
  const tokenProduct = products.find(p => p.category === 'token');
  const cartTotal = cart.reduce((sum, item) => sum + item.price * item.qty, 0);
  const cartCount = cart.reduce((sum, item) => sum + item.qty, 0);

  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(i => i.id === product.id);
      if (existing) return prev.map(i => i.id === product.id ? { ...i, qty: i.qty + 1 } : i);
      return [...prev, { id: product.id, name: product.name, price: product.price, qty: 1 }];
    });
  };

  const removeFromCart = (productId) => {
    setCart(prev => prev.filter(i => i.id !== productId));
  };

  const updateCartQty = (productId, delta) => {
    setCart(prev => prev.map(i => {
      if (i.id !== productId) return i;
      const newQty = i.qty + delta;
      return newQty > 0 ? { ...i, qty: newQty } : i;
    }).filter(i => i.qty > 0));
  };

  const placeOrder = async () => {
    if (cart.length === 0) return;
    setOrdering(true);
    setOrderResult(null);
    const res = await fetch(`${API}/api/shop/orders/${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: cart.map(i => ({ product_id: i.id, quantity: i.qty })) }),
    }).then(r => r.json()).catch(() => ({ success: false, error: 'Verbinding mislukt' }));
    setOrderResult(res);
    setOrdering(false);
    if (res.success) {
      setCart([]);
      loadData();
    }
  };

  const buyToken = async () => {
    const qty = parseInt(tokenQty) || 0;
    if (qty < 1) return;
    setBuyingToken(true);
    setTokenResult(null);
    const res = await fetch(`${API}/api/shop/token/buy/${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_tokens: qty }),
    }).then(r => r.json()).catch(() => ({ success: false, error: 'Verbinding mislukt' }));
    setTokenResult(res);
    setBuyingToken(false);
    if (res.success) { setTokenQty('1'); loadData(); }
  };

  if (loading) return (
    <MainLayout activePage="winkel" onNavigate={onNavigate}>
      <div className="flex items-center justify-center h-full"><Loader2 className="w-8 h-8 text-amber-500 animate-spin" /></div>
    </MainLayout>
  );

  const tokenPrice = tokenInfo?.price_eur || 5.08;
  const walletBalance = userBalance?.wallet_eur || 0;

  const productIcons = {
    hat: '🧢', shirt: '🔥', package: '📦', coin: '💎',
  };

  return (
    <MainLayout activePage="winkel" onNavigate={onNavigate}>
      <div data-testid="winkel-page" className="p-4 md:p-6 space-y-4 max-w-6xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #dc2626, #991b1b)' }}>
              <ShoppingBag className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Roadkill Shop</h1>
              <p className="text-xs text-slate-400">Merch, tokens & meer</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-[10px] text-slate-500">Wallet saldo</p>
              <p className="text-sm font-bold text-white">&euro;{walletBalance.toFixed(2)}</p>
            </div>
            <button data-testid="cart-btn" onClick={() => setShowCart(!showCart)}
              className="relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white transition-all border border-slate-700 hover:border-amber-500/50 bg-slate-800">
              <ShoppingCart className="w-4 h-4" />
              {cartCount > 0 && (
                <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-[10px] font-bold text-white">
                  {cartCount}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-900/50 rounded-xl p-1 border border-slate-800">
          {[
            { id: 'merch', label: 'Merch', icon: Tag },
            { id: 'tokens', label: 'ROAR Tokens', icon: Coins },
          ].map(tab => (
            <button key={tab.id} data-testid={`shop-tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-slate-800 text-white border border-slate-700'
                  : 'text-slate-500 hover:text-slate-300'
              }`}>
              <tab.icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* MERCH TAB */}
        {activeTab === 'merch' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {merchProducts.map(product => (
                <div key={product.id} data-testid={`product-${product.id}`}
                  className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-all group">
                  {/* Product image area */}
                  <div className="h-40 flex items-center justify-center" style={{
                    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)'
                  }}>
                    <span className="text-6xl group-hover:scale-110 transition-transform">
                      {productIcons[product.image_icon] || '📦'}
                    </span>
                  </div>
                  {/* Product info */}
                  <div className="p-4 space-y-3">
                    <div>
                      <h3 className="text-sm font-bold text-white">{product.name}</h3>
                      <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{product.description}</p>
                    </div>
                    <div className="flex items-end justify-between">
                      <div>
                        <p className="text-xl font-bold text-white">&euro;{product.price.toFixed(2)}</p>
                        {product.in_stock
                          ? <p className="text-[10px] text-green-400">Op voorraad</p>
                          : <p className="text-[10px] text-red-400">Uitverkocht</p>
                        }
                      </div>
                      <button data-testid={`add-${product.id}`}
                        onClick={() => addToCart(product)}
                        disabled={!product.in_stock}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-white transition-all disabled:opacity-40 bg-red-600 hover:bg-red-700">
                        <Plus className="w-3.5 h-3.5" /> In wagen
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {merchProducts.length === 0 && (
              <div className="py-12 text-center text-slate-500 text-sm">Geen producten beschikbaar</div>
            )}
          </div>
        )}

        {/* ROAR TOKENS TAB */}
        {activeTab === 'tokens' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Token Info */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-5 text-center" style={{
                background: 'linear-gradient(135deg, #1a1333 0%, #f59e0b10 50%, #ea580c08 100%)'
              }}>
                <div className="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
                  <span className="text-2xl font-black text-white">R</span>
                </div>
                <h2 className="text-lg font-bold text-white">ROAR Token</h2>
                <p className="text-xs text-slate-400">Spark Core Aandeel</p>
                <p className="text-3xl font-bold text-amber-400 mt-2">&euro;{tokenPrice.toFixed(2)}</p>
                <p className="text-[10px] text-slate-500 mt-1">
                  {tokenInfo?.price_model === 'dynamic' ? 'Dynamische prijs = Spark Core / tokens' : `Vaste prijs (nog ${tokenInfo?.tokens_until_dynamic || 0} tokens)`}
                </p>
                {tokenInfo?.bitvavo_balance > 0 && (
                  <p className="text-[10px] text-cyan-400 mt-1">Bitvavo: &euro;{tokenInfo.bitvavo_balance.toFixed(2)}</p>
                )}
              </div>
              <div className="px-5 py-3 border-t border-slate-800 flex items-center justify-between text-[11px]">
                <span className="text-slate-400">Jouw tokens: <b className="text-white">{userBalance?.roar_balance || 0} ROAR</b></span>
                <span className="text-slate-400">Waarde: <b className="text-amber-400">&euro;{(userBalance?.value_eur || 0).toFixed(2)}</b></span>
              </div>
              <div className="px-5 py-3 border-t border-slate-800 grid grid-cols-3 gap-3 text-center text-[10px]">
                <div>
                  <p className="text-slate-500">In Omloop</p>
                  <p className="text-white font-bold">{tokenInfo?.circulating || 0}</p>
                </div>
                <div>
                  <p className="text-slate-500">Spark Core</p>
                  <p className="text-white font-bold">&euro;{(tokenInfo?.spark_core_value || 0).toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-slate-500">Market Cap</p>
                  <p className="text-white font-bold">&euro;{(tokenInfo?.market_cap || 0).toFixed(2)}</p>
                </div>
              </div>
            </div>

            {/* Buy Token Form */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Coins className="w-4 h-4 text-amber-400" /> ROAR Tokens Kopen
              </h3>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Aantal tokens (heel)</label>
                <input data-testid="token-qty" type="number" value={tokenQty}
                  onChange={e => setTokenQty(e.target.value)}
                  placeholder="1" step="1" min="1"
                  className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white text-sm placeholder-slate-500 focus:outline-none focus:border-amber-500" />
              </div>
              <div className="p-3 bg-slate-800/50 rounded-lg space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Prijs per token</span>
                  <span className="text-white">&euro;{tokenPrice.toFixed(2)} ({tokenInfo?.price_model || 'fixed'})</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Totaal</span>
                  <span className="text-amber-400 font-bold">&euro;{((parseInt(tokenQty) || 0) * tokenPrice).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-400">Wallet saldo</span>
                  <span className="text-white">&euro;{walletBalance.toFixed(2)}</span>
                </div>
              </div>
              <button data-testid="buy-token-btn" onClick={buyToken}
                disabled={buyingToken || (parseInt(tokenQty) || 0) < 1}
                className="w-full py-3 rounded-xl text-sm font-semibold text-white bg-amber-500 hover:bg-amber-600 transition-all disabled:opacity-50">
                {buyingToken ? 'Bezig...' : `${parseInt(tokenQty) || 0} ROAR Kopen`}
              </button>
              {tokenResult && (
                <div data-testid="token-result" className={`p-3 rounded-lg text-xs ${tokenResult.success ? 'bg-green-500/10 border border-green-500/20 text-green-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
                  {tokenResult.success ? tokenResult.message : tokenResult.error}
                </div>
              )}
              <div className="text-[10px] text-slate-500 space-y-1">
                <p><b className="text-amber-400">Dynamische prijs</b> = Spark Core waarde / circulerende tokens. Stijgt als de trading bot winst maakt.</p>
                <p><b className="text-slate-300">Alleen hele tokens.</b> Wisselgeld gaat naar Spark Core kapitaal.</p>
              </div>
            </div>
          </div>
        )}

        {/* WINKELWAGEN SLIDE-OUT */}
        {showCart && (
          <div className="fixed inset-0 z-50 flex justify-end" onClick={() => setShowCart(false)}>
            <div className="absolute inset-0 bg-black/50" />
            <div className="relative w-full max-w-md bg-slate-900 border-l border-slate-800 h-full overflow-y-auto"
              onClick={e => e.stopPropagation()}>
              <div className="p-5 border-b border-slate-800 flex items-center justify-between">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <ShoppingCart className="w-5 h-5 text-red-400" /> Winkelwagen
                </h2>
                <button onClick={() => setShowCart(false)} className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {cart.length === 0 ? (
                <div className="p-8 text-center">
                  <ShoppingCart className="w-12 h-12 text-slate-700 mx-auto mb-3" />
                  <p className="text-sm text-slate-500">Je winkelwagen is leeg</p>
                </div>
              ) : (
                <div className="p-4 space-y-3">
                  {cart.map(item => (
                    <div key={item.id} data-testid={`cart-item-${item.id}`}
                      className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-xl border border-slate-800">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white font-medium truncate">{item.name}</p>
                        <p className="text-xs text-slate-400">&euro;{item.price.toFixed(2)} per stuk</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button onClick={() => updateCartQty(item.id, -1)}
                          className="w-7 h-7 flex items-center justify-center rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600">
                          <Minus className="w-3 h-3" />
                        </button>
                        <span className="text-sm font-bold text-white w-6 text-center">{item.qty}</span>
                        <button onClick={() => updateCartQty(item.id, 1)}
                          className="w-7 h-7 flex items-center justify-center rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600">
                          <Plus className="w-3 h-3" />
                        </button>
                      </div>
                      <div className="text-right flex-shrink-0 w-16">
                        <p className="text-sm font-bold text-white">&euro;{(item.price * item.qty).toFixed(2)}</p>
                      </div>
                      <button onClick={() => removeFromCart(item.id)}
                        className="p-1 text-slate-600 hover:text-red-400">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}

                  {/* Totaal */}
                  <div className="border-t border-slate-800 pt-3 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">Subtotaal</span>
                      <span className="text-white font-bold">&euro;{cartTotal.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500">Wallet saldo</span>
                      <span className={walletBalance >= cartTotal ? 'text-green-400' : 'text-red-400'}>
                        &euro;{walletBalance.toFixed(2)}
                      </span>
                    </div>
                    {walletBalance < cartTotal && (
                      <p className="text-[10px] text-red-400 bg-red-500/10 p-2 rounded-lg border border-red-500/20">
                        Onvoldoende saldo. Stort eerst geld op je wallet.
                      </p>
                    )}
                    <button data-testid="place-order-btn" onClick={placeOrder}
                      disabled={ordering || walletBalance < cartTotal}
                      className="w-full py-3 rounded-xl text-sm font-semibold text-white bg-red-600 hover:bg-red-700 transition-all disabled:opacity-40 flex items-center justify-center gap-2">
                      {ordering ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
                      {ordering ? 'Bestellen...' : `Bestellen - \u20AC${cartTotal.toFixed(2)}`}
                    </button>
                  </div>

                  {orderResult && (
                    <div data-testid="order-result" className={`p-3 rounded-lg text-xs ${orderResult.success ? 'bg-green-500/10 border border-green-500/20 text-green-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'}`}>
                      {orderResult.success ? (
                        <span className="flex items-center gap-1"><Check className="w-3.5 h-3.5" /> {orderResult.message}</span>
                      ) : orderResult.error}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}

export default WinkelPage;
