// v11_shop_tab_in_archief_001 — Per-shop tab in Workspace → Archief.
// Toont producten van user's eigen shop met bewerk-modal.
// v12_shop_owner_perms_001 — Header met kleur-picker: shop-owner beheert hier zijn winkel
// (naam + accent-kleur). Winkelstraat (front) blijft admin-only voor CRUD.
import React, { useState, useEffect, useCallback } from 'react';
import { Package, Plus, Edit3, Trash2, Image as ImageIcon, ShoppingBag } from 'lucide-react';
import { ProductEditModal } from '../modules/ProductEditModal';

const API = process.env.REACT_APP_BACKEND_URL;

const SHOP_COLOR_PRESETS = [
  '#f59e0b', '#ef4444', '#ec4899', '#a855f7',
  '#3b82f6', '#06b6d4', '#10b981', '#eab308',
];

export function ShopTabView({ shop, userId }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);
  // v12_shop_owner_perms_001 — lokale kleur-state (blijft in sync met shop prop maar
  // laat direct visuele feedback zien terwijl PATCH loopt).
  const [color, setColor] = useState(shop.color_accent || '#f59e0b');
  const [savingColor, setSavingColor] = useState(false);
  const [colorFlash, setColorFlash] = useState(false);

  useEffect(() => { setColor(shop.color_accent || '#f59e0b'); }, [shop.color_accent]);

  const saveColor = async (hex) => {
    setColor(hex);
    setSavingColor(true);
    try {
      const r = await fetch(`${API}/api/winkelstraat/shops/${shop.id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actor_user_id: userId, patch: { color_accent: hex } }),
      }).then(x => x.json());
      if (r.success) {
        setColorFlash(true);
        setTimeout(() => setColorFlash(false), 1500);
      }
    } finally { setSavingColor(false); }
  };

  const load = useCallback(() => {
    setLoading(true);
    fetch(`${API}/api/shop/products?shop_id=${encodeURIComponent(shop.id)}`)
      .then(r => r.json())
      .then(d => setProducts(d.products || []))
      .finally(() => setLoading(false));
  }, [shop.id]);

  useEffect(() => { load(); }, [load]);

  const doDelete = async (p) => {
    if (!window.confirm(`Product "${p.name}" verwijderen?`)) return;
    await fetch(`${API}/api/shop/admin/products/${p.id}?viewer_id=${userId}&shop_id=${encodeURIComponent(shop.id)}`, { method: 'DELETE' });
    load();
  };

  return (
    <div data-testid={`shop-tab-view-${shop.id}`} className="space-y-4">
      {/* v12_shop_owner_perms_001 — Beheer-header: shop-naam prominent + kleur-picker + nieuw-product */}
      <div
        data-testid={`shop-owner-header-${shop.id}`}
        className="bg-slate-900/60 border rounded-xl p-4 space-y-3"
        style={{ borderColor: `${color}55` }}>
        <div className="flex flex-col md:flex-row md:items-center gap-3">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            {shop.logo_url ? (
              <img src={`${API}${shop.logo_url}`} alt="" className="w-11 h-11 rounded-xl object-cover flex-shrink-0"
                onError={e => { e.target.style.display = 'none'; }} />
            ) : (
              <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ background: `linear-gradient(135deg, ${color}, ${color}88)` }}>
                <ShoppingBag className="w-5 h-5 text-white" />
              </div>
            )}
            <div className="min-w-0">
              <p className="text-[10px] uppercase tracking-wider text-slate-500">Jouw winkel</p>
              <h2 className="text-lg font-bold text-white truncate">{shop.naam}</h2>
              {shop.tagline && <p className="text-[11px] text-slate-400 truncate">{shop.tagline}</p>}
            </div>
          </div>
          <button data-testid={`shop-add-product-${shop.id}`} onClick={() => setCreating(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-slate-950 flex-shrink-0"
            style={{ background: color }}>
            <Plus className="w-3.5 h-3.5" /> Nieuw product
          </button>
        </div>
        <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-slate-800/60">
          <span className="text-[11px] text-slate-400 mr-1">Accent-kleur:</span>
          {SHOP_COLOR_PRESETS.map(hex => (
            <button key={hex} onClick={() => saveColor(hex)}
              data-testid={`shop-color-preset-${hex.slice(1)}`}
              title={hex}
              className={`w-6 h-6 rounded-full border-2 transition-transform hover:scale-110 ${color === hex ? 'ring-2 ring-white/60' : ''}`}
              style={{ background: hex, borderColor: color === hex ? '#fff' : 'transparent' }} />
          ))}
          <input type="color" value={color} onChange={e => saveColor(e.target.value)}
            data-testid="shop-color-picker"
            className="w-8 h-8 rounded cursor-pointer bg-slate-800 border border-slate-700" />
          {savingColor && <span className="text-[10px] text-slate-500">…</span>}
          {colorFlash && <span className="text-[10px] text-emerald-400">✓ opgeslagen</span>}
        </div>
      </div>

      {/* Producten grid */}
      {loading ? (
        <div className="text-center py-8 text-xs text-slate-500">Producten laden...</div>
      ) : products.length === 0 ? (
        <div className="text-center py-16 border border-dashed border-slate-700 rounded-xl">
          <Package className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500 mb-3">Nog geen producten in deze winkel</p>
          <button onClick={() => setCreating(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs">
            <Plus className="w-3.5 h-3.5" /> Voeg eerste product toe
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {products.map(p => (
            <div key={p.id} data-testid={`shop-product-${p.id}`}
              className="group bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
              <div className="relative aspect-square bg-slate-800 flex items-center justify-center overflow-hidden">
                {p.image_url ? (
                  <img src={p.image_url.startsWith('http') ? p.image_url : `${API}${p.image_url}`}
                    alt={p.name} className="w-full h-full object-cover" />
                ) : (
                  <ImageIcon className="w-8 h-8 text-slate-600" />
                )}
                {/* Hover-actions */}
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <button data-testid={`shop-edit-${p.id}`} onClick={() => setEditing(p)}
                    className="p-2 rounded-lg bg-amber-500 text-slate-950 hover:bg-amber-400" title="Bewerken">
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button data-testid={`shop-delete-${p.id}`} onClick={() => doDelete(p)}
                    className="p-2 rounded-lg bg-red-500 text-white hover:bg-red-400" title="Verwijderen">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="p-2">
                <p className="text-xs text-white font-medium truncate">{p.name}</p>
                <p className="text-[10px] text-amber-400">€{Number(p.price || 0).toFixed(2)}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit/create modal */}
      <ProductEditModal
        open={!!editing || creating}
        onClose={() => { setEditing(null); setCreating(false); }}
        product={editing}
        userId={userId}
        shopId={shop.id}
        shopName={shop.naam}
        defaultCategory={editing?.category || 'merch'}
        onSaved={() => load()}
      />
    </div>
  );
}
