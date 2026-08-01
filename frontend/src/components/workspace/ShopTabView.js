// v11_shop_tab_in_archief_001 — Per-shop tab in Workspace → Archief.
// Toont producten van user's eigen shop met bewerk-modal.
import React, { useState, useEffect, useCallback } from 'react';
import { Package, Plus, Edit3, Trash2, Image as ImageIcon } from 'lucide-react';
import { ProductEditModal } from '../modules/ProductEditModal';

const API = process.env.REACT_APP_BACKEND_URL;

export function ShopTabView({ shop, userId }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);

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
      {/* Shop-header */}
      <div className="flex items-center justify-between bg-slate-800/50 border border-slate-700 rounded-xl px-4 py-3">
        <div className="flex items-center gap-3">
          {shop.logo_url && (
            <img src={`${API}${shop.logo_url}`} alt="" className="w-10 h-10 rounded-lg object-cover"
              onError={e => { e.target.style.display = 'none'; }} />
          )}
          <div>
            <h3 className="text-sm font-bold text-white">{shop.naam}</h3>
            <p className="text-[10px] text-slate-500">{shop.tagline || `${products.length} product(en)`}</p>
          </div>
        </div>
        <button data-testid={`shop-add-product-${shop.id}`} onClick={() => setCreating(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs hover:bg-amber-500/30">
          <Plus className="w-3.5 h-3.5" /> Nieuw product
        </button>
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
