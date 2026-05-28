import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  ShoppingBag, Coins, Plus, Minus, ShoppingCart, X,
  Package, Tag, Truck, CreditCard, Loader2, Check,
  TrendingUp, ChevronRight, HardDrive, Gift, Pencil
} from 'lucide-react';
import { ProductEditModal } from './ProductEditModal';
import { WinkelstraatTab } from './WinkelstraatTab';

const API = process.env.REACT_APP_BACKEND_URL;

export function WinkelPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [products, setProducts] = useState([]);
  const [tokenInfo, setTokenInfo] = useState(null);
  const [userBalance, setUserBalance] = useState(null);
  const [storageStats, setStorageStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cart, setCart] = useState([]);
  const [showCart, setShowCart] = useState(false);
  const [ordering, setOrdering] = useState(false);
  const [orderResult, setOrderResult] = useState(null);
  const [activeTab, setActiveTab] = useState('winkelstraat');
  const [selectedShopId, setSelectedShopId] = useState(null);  // v6_shop_per_user_001 — drill-in view
  const [selectedShop, setSelectedShop] = useState(null);
  const [digitalSubTab, setDigitalSubTab] = useState('storage');

  // Wanneer een shop wordt geselecteerd: laad shop-info + bepaal welke subtab default actief is
  const openShop = useCallback(async (shopId) => {
    try {
      const r = await fetch(`${API}/api/winkelstraat/shops`);
      const d = await r.json();
      const shop = (d.shops || []).find(s => s.id === shopId);
      if (!shop) return;
      setSelectedShopId(shopId);
      setSelectedShop(shop);
      // Default sub-tab = eerste in subtabs_enabled
      const firstSub = (shop.subtabs_enabled || ['merch'])[0];
      setActiveTab(firstSub === 'digitaal' ? 'digital' : firstSub);
    } catch (e) { console.error(e); }
  }, []);

  const backToWinkelstraat = () => {
    setSelectedShopId(null);
    setSelectedShop(null);
    setActiveTab('winkelstraat');
  };

  // Token buy state
  const [tokenQty, setTokenQty] = useState('1');
  const [buyingToken, setBuyingToken] = useState(false);
  const [tokenResult, setTokenResult] = useState(null);

  // v6_shop_admin_product_crud_001 — Admin product edit state (BEFORE early returns!)
  const isAdminViewer = (user?.gradatie ?? 7) <= 2;
  const [editingProduct, setEditingProduct] = useState(null);
  const [newProductTab, setNewProductTab] = useState(null);

  const loadData = useCallback(() => {
    Promise.all([
      fetch(`${API}/api/shop/products`).then(r => r.json()).catch(() => ({ products: [] })),
      fetch(`${API}/api/shop/token/price`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/shop/token/balance/${userId}`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/wallet/user/${userId}`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/archive/${userId}/stats`).then(r => r.json()).catch(() => null),
    ]).then(([prods, price, bal, wallet, storage]) => {
      setProducts(prods.products || []);
      setTokenInfo(price);
      setUserBalance({ ...bal, wallet_eur: wallet?.balance_eur || 0 });
      setStorageStats(storage);
      setLoading(false);
    });
  }, [userId]);

  useEffect(() => { loadData(); }, [loadData]);

  const merchProducts = products.filter(p => p.category === 'merch');
  const storageProducts = products.filter(p => p.category === 'storage');
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

  return (
    <MainLayout activePage="winkel" onNavigate={onNavigate}>
      <div data-testid="winkel-page" className="p-4 md:p-6 space-y-4 max-w-6xl mx-auto">

        {/* Header — dynamisch op basis van geselecteerde shop of Winkelstraat-overzicht */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {selectedShop ? (
              <>
                <button data-testid="back-to-winkelstraat" onClick={backToWinkelstraat}
                  className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
                  <ChevronRight className="w-5 h-5 rotate-180" />
                </button>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ background: `linear-gradient(135deg, ${selectedShop.color_accent || '#f59e0b'}, ${selectedShop.color_accent || '#f59e0b'}88)` }}>
                  <ShoppingBag className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">{selectedShop.naam}</h1>
                  <p className="text-xs text-slate-400">{selectedShop.tagline || `${selectedShop.type} · door ${selectedShop.owner_naam || selectedShop.owner_user_id}`}</p>
                </div>
              </>
            ) : (
              <>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #b45309)' }}>
                  <ShoppingBag className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">Winkelstraat</h1>
                  <p className="text-xs text-slate-400">Alle winkels op Spark Core</p>
                </div>
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-[10px] text-slate-500">Wallet saldo</p>
              <p className="text-sm font-bold text-white">&euro;{walletBalance.toFixed(2)}</p>
            </div>
            {selectedShop && (
              <button data-testid="cart-btn" onClick={() => setShowCart(!showCart)}
                className="relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white transition-all border border-slate-700 hover:border-amber-500/50 bg-slate-800">
                <ShoppingCart className="w-4 h-4" />
                {cartCount > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-[10px] font-bold text-white">
                    {cartCount}
                  </span>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Sub-tabs alleen tonen als een shop geselecteerd is */}
        {selectedShop && (
          <div className="flex gap-1 bg-slate-900/50 rounded-xl p-1 border border-slate-800">
            {(selectedShop.subtabs_enabled || ['merch', 'digitaal']).map(sub => {
              const tabId = sub === 'digitaal' ? 'digital' : sub;
              const label = sub === 'merch' ? 'Fysiek' : sub === 'digitaal' ? 'Digitaal' : sub.charAt(0).toUpperCase() + sub.slice(1);
              const Icon = sub === 'merch' ? Tag : sub === 'digitaal' ? Package : ShoppingBag;
              const hint = sub === 'merch' ? 'Fysieke producten' : sub === 'digitaal' ? 'Token & opslag' : '';
              return (
                <button key={tabId} data-testid={`shop-tab-${tabId}`}
                  onClick={() => setActiveTab(tabId)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    activeTab === tabId ? 'bg-slate-800 text-white border border-slate-700' : 'text-slate-500 hover:text-slate-300'
                  }`}>
                  <Icon className="w-3.5 h-3.5" />
                  <span>{label}</span>
                  {hint && <span className="hidden md:inline text-[10px] text-slate-600">· {hint}</span>}
                </button>
              );
            })}
          </div>
        )}

        {/* Storage subtab */}
        {selectedShop && activeTab === 'digital' && (
          <div className="flex gap-2 px-1">
            {[
              { id: 'storage', label: 'Opslag', icon: HardDrive, color: '#3b82f6' },
              { id: 'tokens', label: 'ROAR Token', icon: Coins, color: '#f59e0b' },
            ].map(sub => (
              <button key={sub.id} data-testid={`shop-subtab-${sub.id}`}
                onClick={() => setDigitalSubTab(sub.id)}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-[11px] font-medium transition-all ${
                  digitalSubTab === sub.id
                    ? 'bg-slate-800 text-white border border-slate-700'
                    : 'text-slate-500 hover:text-slate-300 border border-transparent'
                }`}
                style={{ color: digitalSubTab === sub.id ? sub.color : undefined }}>
                <sub.icon className="w-3 h-3" />
                {sub.label}
              </button>
            ))}
          </div>
        )}

        {/* MERCH TAB — alleen tonen als shop geselecteerd */}
        {selectedShop && activeTab === 'merch' && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {merchProducts.map(product => (
                <div key={product.id} data-testid={`product-${product.id}`}
                  className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-all group relative">
                  {/* Admin: edit knop top-right (los van image-overlay) */}
                  {isAdminViewer && (
                    <button onClick={() => setEditingProduct(product)} data-testid={`product-edit-${product.id}`}
                      title="Product bewerken"
                      className="absolute top-2 right-2 z-10 w-8 h-8 rounded-lg bg-slate-900/80 backdrop-blur border border-amber-500/40 flex items-center justify-center text-amber-300 hover:bg-amber-500/20">
                      <Pencil className="w-4 h-4" />
                    </button>
                  )}
                  <ProductImageArea product={product} isAdmin={isAdminViewer} userId={user?.id} onUpdated={loadData} />
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
              {/* v6_shop_admin_product_crud_001 — Nieuw product tegel (admin) */}
              {isAdminViewer && (
                <button data-testid="new-merch-product"
                  onClick={() => { setEditingProduct(null); setNewProductTab('merch'); }}
                  className="bg-slate-900/30 border-2 border-dashed border-amber-500/40 rounded-xl flex flex-col items-center justify-center gap-2 min-h-[280px] text-amber-300 hover:bg-amber-500/5 hover:border-amber-400 transition-all">
                  <Plus className="w-10 h-10" />
                  <span className="text-sm font-bold">Nieuw merch product</span>
                  <span className="text-[10px] text-slate-400">titel, prijs, voor/achter foto…</span>
                </button>
              )}
            </div>

            {merchProducts.length === 0 && !isAdminViewer && (
              <div className="py-12 text-center text-slate-500 text-sm">Geen producten beschikbaar</div>
            )}
          </div>
        )}

        {/* OPSLAG (sub van digitaal) */}
        {selectedShop && activeTab === 'digital' && digitalSubTab === 'storage' && (
          <StorageTab
            products={storageProducts}
            storageStats={storageStats}
            walletBalance={walletBalance}
            addToCart={addToCart}
          />
        )}

        {/* ROAR TOKENS (sub van digitaal) */}
        {selectedShop && activeTab === 'digital' && digitalSubTab === 'tokens' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Token Info */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-5 text-center" style={{
                background: 'linear-gradient(135deg, #1a1333 0%, #f59e0b10 50%, #ea580c08 100%)'
              }}>
                <div className="w-16 h-16 rounded-full mx-auto mb-3 overflow-hidden border-2 border-amber-500/40 bg-slate-900">
                  <img
                    src={`${API}/api/avatar/gallery/roadkill-logo/image`}
                    alt="Roadkill ROAR Token"
                    className="w-full h-full object-cover"
                    data-testid="roar-token-logo"
                  />
                </div>
                <h2 className="text-lg font-bold text-white">Roadkill ROAR Token</h2>
                <p className="text-xs text-slate-400">1 ROAR = aandeel in Spark Core kapitaal</p>
                <p className="text-3xl font-bold text-amber-400 mt-2">&euro;{tokenPrice.toFixed(2)}</p>
                <p className="text-[10px] text-slate-500 mt-1" title="Prijs per token = Spark Core kapitaal ÷ aantal tokens in omloop">
                  {tokenInfo?.price_model === 'dynamic'
                    ? `Dynamisch: €${(tokenInfo?.spark_core_value || 0).toFixed(2)} ÷ ${tokenInfo?.circulating || 0} = €${tokenPrice.toFixed(2)}`
                    : `Vaste startprijs — nog ${tokenInfo?.tokens_until_dynamic || 0} tokens tot dynamisch`}
                </p>
                {tokenInfo?.bitvavo_balance > 0 && (
                  <p className="text-[10px] text-cyan-400 mt-1" title="Live crypto-waarde op Bitvavo, onderdeel van Spark Core">
                    waarvan op Bitvavo: &euro;{tokenInfo.bitvavo_balance.toFixed(2)}
                  </p>
                )}
              </div>
              <div className="px-5 py-3 border-t border-slate-800 flex items-center justify-between text-[11px]">
                <span className="text-slate-400">Jouw bezit: <b className="text-white">{userBalance?.roar_balance || 0} ROAR</b></span>
                <span className="text-slate-400">Tegen huidige prijs: <b className="text-amber-400">&euro;{(userBalance?.value_eur || 0).toFixed(2)}</b></span>
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
              {/* v5_roar_gift_001 — Gift verhuisd naar Wallet pagina (bij Storten/Opnemen) */}
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

        {/* WINKELSTRAAT TAB — alle shops (entry point) */}
        {!selectedShopId && activeTab === 'winkelstraat' && (
          <WinkelstraatTab user={user} onNavigateToShop={openShop} />
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

      {/* v5_roar_gift_001 — Gift verhuisd naar WalletPage (bij Storten/Opnemen) */}

      {/* v6_shop_admin_product_crud_001 — Edit/new product modal */}
      {isAdminViewer && (
        <ProductEditModal
          open={!!editingProduct || !!newProductTab}
          onClose={() => { setEditingProduct(null); setNewProductTab(null); }}
          product={editingProduct}
          userId={user?.id}
          defaultCategory={newProductTab || editingProduct?.category || 'merch'}
          onSaved={(p) => { loadData(); if (p && p.id) setEditingProduct(p); }}
        />
      )}
    </MainLayout>
  );
}

export default WinkelPage;

// v6_shop_product_image_001 — Admin kan product-afbeelding wijzigen
const PRODUCT_ICONS = {
  hat: '🧢', shirt: '🔥', package: '📦', coin: '💎',
};

function ProductImageArea({ product, isAdmin, userId, onUpdated }) {
  const [uploading, setUploading] = useState(false);
  const [err, setErr] = useState('');
  const inputRef = React.useRef(null);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setErr('');
    try {
      const fd = new FormData();
      fd.append('image', file);
      fd.append('viewer_id', userId || '');
      const r = await fetch(`${API}/api/shop/products/${product.id}/image`, { method: 'POST', body: fd }).then(x => x.json());
      if (!r.success) { setErr(r.detail || 'Upload mislukt'); }
      else { onUpdated && onUpdated(); }
    } catch (ex) { setErr(ex.message); }
    setUploading(false);
    if (inputRef.current) inputRef.current.value = '';
  };

  const hasImage = !!product.image_url;

  return (
    <div className="relative h-40 flex items-center justify-center group" style={{
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)'
    }}>
      {hasImage ? (
        <img src={`${API}${product.image_url}`} alt={product.name} className="w-full h-full object-cover" data-testid={`product-img-${product.id}`} />
      ) : (
        <span className="text-6xl group-hover:scale-110 transition-transform">
          {PRODUCT_ICONS[product.image_icon] || '📦'}
        </span>
      )}
      {isAdmin && (
        <>
          <input ref={inputRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden"
            onChange={handleUpload} data-testid={`product-upload-${product.id}`} />
          <button
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            data-testid={`product-img-edit-${product.id}`}
            title="Klik om afbeelding te wijzigen"
            className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-1 text-white">
            <Plus className="w-7 h-7" />
            <span className="text-xs font-medium">{uploading ? 'Uploaden…' : (hasImage ? 'Wijzig foto' : 'Voeg foto toe')}</span>
            <span className="text-[10px] text-slate-300">{product.name}</span>
          </button>
        </>
      )}
      {err && (
        <p className="absolute bottom-1 left-1 right-1 text-[10px] text-red-300 bg-red-900/60 rounded px-1.5 py-0.5">{err}</p>
      )}
    </div>
  );
}

// ============================================================
// Storage Tab — koop opslag + zie huidige quota breakdown
// ============================================================
function StorageTab({ products, storageStats, walletBalance, addToCart }) {
  const q = storageStats?.quota || {};
  const baseGb = q.base_gb || 0;
  const purchasedGb = q.purchased_gb || 0;
  const giftGb = q.gift_gb || 0;
  const totalGb = q.total_gb || 1;
  const usedBytes = q.used_bytes || 0;
  const totalBytes = q.total_bytes || 1;
  const usedPercent = q.used_percent || 0;

  const fmtBytes = (n) => {
    if (!n) return '0 B';
    const u = ['B', 'KB', 'MB', 'GB'];
    const i = Math.min(Math.floor(Math.log(n) / Math.log(1024)), 3);
    return `${(n / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${u[i]}`;
  };

  const basePct = (baseGb / totalGb) * 100;
  const purchasedPct = (purchasedGb / totalGb) * 100;
  const giftPct = (giftGb / totalGb) * 100;
  const events = (q.events || []).slice(-5).reverse();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Huidige opslag - status card */}
      <div data-testid="storage-status-card" className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-5 text-center" style={{ background: 'linear-gradient(135deg, #1a1333 0%, #3b82f610 50%, #06b6d408 100%)' }}>
          <div className="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #3b82f6, #06b6d4)' }}>
            <HardDrive className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-lg font-bold text-white">Jouw Opslag</h2>
          <p className="text-3xl font-bold text-blue-400 mt-2">{totalGb} GB</p>
          <p className="text-[10px] text-slate-500 mt-1">{fmtBytes(usedBytes)} van {fmtBytes(totalBytes)} gebruikt</p>
        </div>

        <div className="p-5 space-y-3">
          {/* Gestapelde balk */}
          <div>
            <div className="flex justify-between text-[10px] text-slate-500 mb-1.5">
              <span>Verdeling</span>
              <span style={{ color: usedPercent > 90 ? '#ef4444' : '#22c55e' }}>{usedPercent}% gebruikt</span>
            </div>
            <div className="h-3 bg-slate-800 rounded-full overflow-hidden flex relative">
              {basePct > 0 && <div style={{ width: `${basePct}%`, background: '#3b82f6' }} title={`Basis: ${baseGb}GB`} />}
              {purchasedPct > 0 && <div style={{ width: `${purchasedPct}%`, background: '#22c55e' }} title={`Gekocht: ${purchasedGb}GB`} />}
              {giftPct > 0 && <div style={{ width: `${giftPct}%`, background: '#ec4899' }} title={`Cadeau: ${giftGb}GB`} />}
              <div className="absolute top-0 left-0 h-full bg-gradient-to-r from-amber-400/30 to-amber-500/60 border-r-2 border-amber-400"
                style={{ width: `${Math.min(usedPercent, 100)}%` }} />
            </div>
          </div>

          {/* Legenda */}
          <div className="grid grid-cols-3 gap-2">
            <div className="p-2 rounded-lg" style={{ background: '#3b82f610', border: '1px solid #3b82f630' }}>
              <div className="flex items-center gap-1 mb-0.5">
                <span className="w-2 h-2 rounded-full bg-blue-500" />
                <span className="text-[9px] text-slate-400 uppercase">Basis</span>
              </div>
              <p className="text-sm font-bold text-white">{baseGb}<span className="text-[10px] text-slate-500 ml-0.5">GB</span></p>
            </div>
            <div className="p-2 rounded-lg" style={{ background: '#22c55e10', border: '1px solid #22c55e30' }}>
              <div className="flex items-center gap-1 mb-0.5">
                <span className="w-2 h-2 rounded-full bg-green-500" />
                <span className="text-[9px] text-slate-400 uppercase">Gekocht</span>
              </div>
              <p className="text-sm font-bold text-white">{purchasedGb}<span className="text-[10px] text-slate-500 ml-0.5">GB</span></p>
            </div>
            <div className="p-2 rounded-lg" style={{ background: '#ec489910', border: '1px solid #ec489930' }}>
              <div className="flex items-center gap-1 mb-0.5">
                <span className="w-2 h-2 rounded-full bg-pink-500" />
                <span className="text-[9px] text-slate-400 uppercase">Cadeau</span>
              </div>
              <p className="text-sm font-bold text-white">{giftGb}<span className="text-[10px] text-slate-500 ml-0.5">GB</span></p>
            </div>
          </div>

          {/* Recent events */}
          {events.length > 0 && (
            <div className="pt-3 border-t border-slate-800">
              <p className="text-[10px] text-slate-500 uppercase mb-2">Geschiedenis</p>
              <div className="space-y-1.5">
                {events.map((e, i) => {
                  const isGift = e.type === 'gift';
                  return (
                    <div key={i} className="flex items-center gap-2 text-[11px]">
                      {isGift ? <Gift className="w-3 h-3 text-pink-400 flex-shrink-0" /> : <ShoppingBag className="w-3 h-3 text-green-400 flex-shrink-0" />}
                      <span className="text-slate-300 truncate flex-1">{e.reason}</span>
                      <span className="font-medium" style={{ color: isGift ? '#ec4899' : '#22c55e' }}>+{e.gb}GB</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Producten lijst */}
      <div className="space-y-4">
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
            <Plus className="w-4 h-4 text-blue-400" /> Extra opslag kopen
          </h3>
          <p className="text-[11px] text-slate-500 mb-4">Voeg ruimte toe wanneer je nodig hebt. Direct beschikbaar na aankoop.</p>

          {products.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-6">Geen opslagproducten beschikbaar</p>
          ) : (
            <div className="space-y-3">
              {products.map(p => (
                <div key={p.id} data-testid={`storage-product-${p.id}`}
                  className="flex items-center gap-3 p-3 bg-slate-800/40 rounded-xl border border-slate-700/50 hover:border-blue-500/40 transition-colors">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(135deg, #3b82f6, #06b6d4)' }}>
                    <HardDrive className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-bold text-white">{p.name}</h4>
                    <p className="text-[11px] text-slate-400 line-clamp-2">{p.description}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-lg font-bold text-white">&euro;{p.price.toFixed(2)}</p>
                    <button data-testid={`add-${p.id}`}
                      onClick={() => addToCart(p)}
                      disabled={!p.in_stock}
                      className="mt-1 flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-40">
                      <Plus className="w-3 h-3" /> In wagen
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 p-3 bg-slate-800/30 rounded-lg text-[10px] text-slate-500 space-y-1">
            <p><b className="text-blue-400">Basis: 1GB gratis</b> per gebruiker, automatisch toegekend.</p>
            <p><b className="text-pink-400">Cadeau-opslag</b> kan worden toegekend via events of door beheer.</p>
            <p>Saldo: <span className="text-white">&euro;{walletBalance.toFixed(2)}</span></p>
          </div>
        </div>
      </div>
    </div>
  );
}
