// v11_shop_tab_in_archief_001 — Per-shop tab in Workspace → Archief.
// Toont producten van user's eigen shop met bewerk-modal.
// v12_shop_owner_perms_001 — Header met kleur-picker: shop-owner beheert hier zijn winkel
// (naam + accent-kleur). Winkelstraat (front) blijft admin-only voor CRUD.
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Package, Plus, Edit3, Trash2, Image as ImageIcon, ShoppingBag, Camera, ClipboardList, Store } from 'lucide-react';
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
  // v14_shop_producten_tab_001 — subtabs: winkel (etalage) | producten (beheer) | bestellingen
  const [subTab, setSubTab] = useState('winkel');
  const [orders, setOrders] = useState([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  useEffect(() => {
    if (subTab !== 'bestellingen') return;
    setOrdersLoading(true);
    fetch(`${API}/api/shop/shops/${encodeURIComponent(shop.id)}/orders`).then(r => r.json())
      .then(d => setOrders(d.orders || [])).catch(() => setOrders([])).finally(() => setOrdersLoading(false));
  }, [subTab, shop.id]);
  // v12_shop_owner_perms_001 — lokale kleur-state (blijft in sync met shop prop maar
  // laat direct visuele feedback zien terwijl PATCH loopt).
  const [color, setColor] = useState(shop.color_accent || '#f59e0b');
  const [savingColor, setSavingColor] = useState(false);
  const [colorFlash, setColorFlash] = useState(false);

  useEffect(() => { setColor(shop.color_accent || '#f59e0b'); }, [shop.color_accent]);

  // v12_shop_owner_perms_001 — logo-upload (POST /api/winkelstraat/shops/{id}/logo)
  const [logoUrl, setLogoUrl] = useState(shop.logo_url || '');
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [logoErr, setLogoErr] = useState('');
  const logoInputRef = useRef(null);
  useEffect(() => { setLogoUrl(shop.logo_url || ''); }, [shop.logo_url]);

  const uploadLogo = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingLogo(true);
    setLogoErr('');
    try {
      const fd = new FormData();
      fd.append('logo', file);
      fd.append('actor_user_id', userId);
      const r = await fetch(`${API}/api/winkelstraat/shops/${shop.id}/logo`, { method: 'POST', body: fd }).then(x => x.json());
      if (r.success && r.logo_url) {
        // Cache-buster zodat browser nieuwe logo direct laadt
        setLogoUrl(`${r.logo_url}?t=${Date.now()}`);
      } else {
        setLogoErr(r.detail || 'Upload mislukt');
      }
    } catch (ex) { setLogoErr(ex.message); }
    setUploadingLogo(false);
    if (logoInputRef.current) logoInputRef.current.value = '';
  };

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
            {/* v12_shop_owner_perms_001 — Logo met klik-to-upload overlay */}
            <div className="relative w-11 h-11 rounded-xl overflow-hidden flex-shrink-0 group cursor-pointer"
              onClick={() => logoInputRef.current?.click()}
              data-testid={`shop-logo-edit-${shop.id}`}
              title="Klik om logo te wijzigen">
              {logoUrl ? (
                <img src={logoUrl.startsWith('http') ? logoUrl : `${API}${logoUrl}`} alt="" className="w-full h-full object-cover"
                  onError={e => { e.target.style.display = 'none'; }} />
              ) : (
                <div className="w-full h-full flex items-center justify-center"
                  style={{ background: `linear-gradient(135deg, ${color}, ${color}88)` }}>
                  <ShoppingBag className="w-5 h-5 text-white" />
                </div>
              )}
              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <Camera className="w-4 h-4 text-white" />
              </div>
              <input ref={logoInputRef} type="file" accept="image/*" className="hidden"
                onChange={uploadLogo} data-testid={`shop-logo-input-${shop.id}`} />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] uppercase tracking-wider text-slate-500">
                Jouw winkel {uploadingLogo && <span className="text-amber-400">· logo uploaden…</span>}
                {logoErr && <span className="text-red-400"> · {logoErr}</span>}
              </p>
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

      {/* v14_shop_producten_tab_001 — subtabs */}
      <div className="flex gap-1 border-b border-slate-800">
        {[['winkel', 'Winkel', Store], ['producten', 'Producten', Package], ['bestellingen', 'Bestellingen', ClipboardList]].map(([id, label, Icon]) => (
          <button key={id} data-testid={`shop-subtab-${id}`} onClick={() => setSubTab(id)}
            className={`relative flex items-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors ${subTab === id ? 'text-white' : 'text-slate-400 hover:text-slate-200'}`}>
            <Icon className="w-3.5 h-3.5" /> {label}
            {id === 'producten' && products.length > 0 && <span className="text-[10px] text-slate-500">({products.length})</span>}
            {subTab === id && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full" style={{ background: color }} />}
          </button>
        ))}
      </div>

      {subTab === 'producten' && (
        <ProductenTabel products={products} loading={loading} color={color} onEdit={setEditing} onDelete={doDelete} onNew={() => setCreating(true)} />
      )}
      {subTab === 'bestellingen' && (
        <BestellingenLijst orders={orders} loading={ordersLoading} color={color} />
      )}

      {/* Producten grid (etalage) */}
      {subTab === 'winkel' && (loading ? (
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
      ))}

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


// v14_shop_producten_tab_001 — productoverzicht met code / voorraad / leverancier
function ProductenTabel({ products, loading, color, onEdit, onDelete, onNew }) {
  if (loading) return <div className="text-center py-8 text-xs text-slate-500">Producten laden...</div>;
  return (
    <div data-testid="shop-producten-tabel" className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-[10px] uppercase tracking-wider text-slate-500 border-b border-slate-800">
            <th className="text-left px-3 py-2">Product</th>
            <th className="text-left px-3 py-2">Code</th>
            <th className="text-right px-3 py-2">Prijs</th>
            <th className="text-right px-3 py-2">Voorraad</th>
            <th className="text-left px-3 py-2">Leverancier</th>
            <th className="px-3 py-2" />
          </tr>
        </thead>
        <tbody>
          {products.map(p => (
            <tr key={p.id} data-testid={`shop-prodrow-${p.id}`} className="border-b border-slate-800/60 hover:bg-slate-800/40">
              <td className="px-3 py-2 text-white font-medium">{p.name}</td>
              <td className="px-3 py-2 font-mono text-slate-300">{p.product_code || <span className="text-slate-600">—</span>}</td>
              <td className="px-3 py-2 text-right" style={{ color }}>€{Number(p.price || 0).toFixed(2)}</td>
              <td className="px-3 py-2 text-right text-slate-300">
                {p.voorraad ?? (p.in_stock === false ? <span className="text-red-400">uitverkocht</span> : <span className="text-slate-500">onbekend</span>)}
              </td>
              <td className="px-3 py-2 text-slate-300">
                {p.leverancier_naam || (p.leverancier_contact_id ? p.leverancier_contact_id : <span className="text-slate-600">zelf</span>)}
              </td>
              <td className="px-3 py-2 text-right whitespace-nowrap">
                <button data-testid={`shop-prodrow-edit-${p.id}`} onClick={() => onEdit(p)} className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-white" title="Bewerken"><Edit3 className="w-3.5 h-3.5" /></button>
                <button data-testid={`shop-prodrow-delete-${p.id}`} onClick={() => onDelete(p)} className="p-1.5 rounded hover:bg-red-500/20 text-slate-400 hover:text-red-300" title="Verwijderen"><Trash2 className="w-3.5 h-3.5" /></button>
              </td>
            </tr>
          ))}
          {products.length === 0 && (
            <tr><td colSpan={6} className="px-3 py-8 text-center text-slate-500">
              Nog geen producten. <button onClick={onNew} className="underline" style={{ color }}>Nieuw product</button> — hij verschijnt dan ook in de Winkel.
            </td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// v14_shop_producten_tab_001 — bestellingen van deze winkel (later: hybride link naar boekhouder/voorraad)
const STATUS_KLEUR = { besteld: '#f59e0b', verzonden: '#10b981', geannuleerd: '#ef4444' };
function BestellingenLijst({ orders, loading, color }) {
  if (loading) return <div className="text-center py-8 text-xs text-slate-500">Bestellingen laden...</div>;
  if (!orders.length) return (
    <div data-testid="shop-bestellingen-leeg" className="text-center py-12 border border-dashed border-slate-700 rounded-xl text-xs text-slate-500">
      Nog geen bestellingen voor deze winkel.
    </div>
  );
  return (
    <div data-testid="shop-bestellingen" className="space-y-2">
      {orders.map(o => (
        <div key={o.id} data-testid={`shop-order-${o.id}`} className="bg-slate-900 border border-slate-800 rounded-xl p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="text-xs text-white font-medium">Order <span className="font-mono">{o.id}</span> · {o.shipping_name || o.user_id}</p>
              <p className="text-[10px] text-slate-500">{new Date(o.created_at).toLocaleString('nl-NL')}{o.shipping_address ? ` · ${o.shipping_address}` : ''}</p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-sm font-bold" style={{ color }}>€{Number(o.shop_total ?? o.total ?? 0).toFixed(2)}</p>
              <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ color: STATUS_KLEUR[o.status] || '#94a3b8', background: (STATUS_KLEUR[o.status] || '#94a3b8') + '22' }}>{o.status}</span>
            </div>
          </div>
          <ul className="mt-2 space-y-0.5">
            {o.items.map((i, idx) => (
              <li key={idx} className="text-[11px] text-slate-300 flex justify-between">
                <span>{i.quantity}× {i.name}{i.product_code ? <span className="font-mono text-slate-500"> · {i.product_code}</span> : ''}</span>
                <span className="text-slate-400">€{Number(i.line_total || 0).toFixed(2)}</span>
              </li>
            ))}
          </ul>
          {o.notes && <p className="text-[11px] text-slate-500 italic mt-1">{o.notes}</p>}
        </div>
      ))}
    </div>
  );
}
