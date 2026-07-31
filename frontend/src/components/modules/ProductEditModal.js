// v6_shop_admin_product_crud_001 — Admin: nieuw / bewerk product met meerdere afbeeldingen
import React, { useState, useEffect, useRef } from 'react';
import { X, Upload, Trash2, Loader2, Plus } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function ProductEditModal({ open, onClose, product, userId, shopId = 'shop-roadkill', shopName = 'Roadkill Shop', onSaved, defaultCategory = 'merch' }) {
  const isNew = !product;
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [category, setCategory] = useState(defaultCategory);
  const [entityId, setEntityId] = useState('roadkill_merch');
  const [inStock, setInStock] = useState(true);
  const [imageIcon, setImageIcon] = useState('package');
  const [images, setImages] = useState([]);
  const [uploadingIdx, setUploadingIdx] = useState(-1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  // v11_shop_scope_001 — entity_id (kasboek) volgt automatisch de shop-context.
  // shop-roadkill → 'roadkill_merch' (bestaand), andere shops → 'shop_<id>'.
  const derivedEntityId = shopId === 'shop-roadkill' ? 'roadkill_merch' : `shop_${shopId}`;

  useEffect(() => {
    if (!open) return;
    setError(null);
    if (product) {
      setName(product.name || '');
      setDescription(product.description || '');
      setPrice(String(product.price ?? ''));
      setCategory(product.category || 'merch');
      setEntityId(product.entity_id || derivedEntityId);
      setInStock(product.in_stock !== false);
      setImageIcon(product.image_icon || 'package');
      setImages(product.images || (product.image_url ? [product.image_url] : []));
    } else {
      setName(''); setDescription(''); setPrice(''); setCategory(defaultCategory);
      setEntityId(derivedEntityId);
      setInStock(true); setImageIcon('package'); setImages([]);
    }
  }, [open, product, defaultCategory, derivedEntityId]);

  if (!open) return null;

  const uploadFiles = async (files) => {
    if (!files || !files.length) return;
    setError(null);
    let pid = product?.id;
    if (!pid) {
      // Eerst product aanmaken zodat we afbeeldingen kunnen koppelen
      const pr = parseFloat(price);
      if (!name.trim() || !Number.isFinite(pr) || pr < 0) {
        setError('Vul eerst naam en geldige prijs in voor je foto\'s uploadt.');
        return;
      }
      const created = await fetch(`${API}/api/shop/admin/products`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewer_id: userId, name, description, price: pr, category, entity_id: entityId, in_stock: inStock, image_icon: imageIcon, shop_id: shopId }),
      }).then(r => r.json());
      if (!created.success) { setError(created.detail || 'Aanmaken mislukt'); return; }
      pid = created.product.id;
    }
    const newImgs = [...images];
    for (let i = 0; i < files.length; i++) {
      setUploadingIdx(i);
      const fd = new FormData();
      fd.append('image', files[i]);
      fd.append('viewer_id', userId);
      const r = await fetch(`${API}/api/shop/products/${pid}/image`, { method: 'POST', body: fd }).then(x => x.json());
      if (r.success && r.image_url) newImgs.push(r.image_url);
    }
    setUploadingIdx(-1);
    setImages(newImgs);
    if (fileRef.current) fileRef.current.value = '';
    // Force re-set product on parent
    onSaved && onSaved({ silent: true });
  };

  const removeImage = async (url) => {
    if (!product?.id) {
      setImages(prev => prev.filter(u => u !== url));
      return;
    }
    if (!window.confirm('Foto verwijderen?')) return;
    const qs = new URLSearchParams({ image_url: url, viewer_id: userId, shop_id: shopId });
    const r = await fetch(`${API}/api/shop/admin/products/${product.id}/images?${qs}`, { method: 'DELETE' }).then(x => x.json());
    if (r.success) setImages(r.images);
  };

  const save = async () => {
    setError(null);
    const pr = parseFloat(price);
    if (!name.trim()) { setError('Naam is verplicht'); return; }
    if (!Number.isFinite(pr) || pr < 0) { setError('Prijs ongeldig'); return; }
    setSaving(true);
    try {
      const body = { viewer_id: userId, name, description, price: pr, category, entity_id: entityId, in_stock: inStock, image_icon: imageIcon, images, shop_id: shopId };
      const url = isNew ? `${API}/api/shop/admin/products` : `${API}/api/shop/admin/products/${product.id}`;
      const method = isNew ? 'POST' : 'PUT';
      const r = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(x => x.json());
      if (!r.success) { setError(r.detail || 'Opslaan mislukt'); return; }
      onSaved && onSaved(r.product);
      onClose && onClose();
    } finally { setSaving(false); }
  };

  const deleteProduct = async () => {
    if (!product?.id) return;
    if (!window.confirm(`Product "${product.name}" definitief verwijderen?`)) return;
    await fetch(`${API}/api/shop/admin/products/${product.id}?viewer_id=${userId}&shop_id=${encodeURIComponent(shopId)}`, { method: 'DELETE' });
    onSaved && onSaved(null);
    onClose && onClose();
  };

  return (
    <div data-testid="product-edit-modal" className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="w-full max-w-2xl max-h-[92vh] bg-slate-900 border border-amber-500/40 rounded-2xl flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-base font-bold text-white">{isNew ? 'Nieuw product' : `Bewerk: ${product.name}`}</h3>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-800 rounded-lg"><X className="w-4 h-4 text-slate-400" /></button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Afbeeldingen */}
          <div>
            <label className="text-[10px] text-slate-400 uppercase tracking-wider">Afbeeldingen (voor, achter, detail…)</label>
            <div className="mt-2 flex flex-wrap gap-2">
              {images.map((url, i) => (
                <div key={url} className="relative w-28 h-28 group">
                  <img src={`${API}${url}`} alt={`afb-${i}`} className="w-full h-full object-cover rounded-lg border border-slate-700" data-testid={`product-img-thumb-${i}`} />
                  <button onClick={() => removeImage(url)} data-testid={`product-img-remove-${i}`}
                    className="absolute -top-1.5 -right-1.5 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <Trash2 className="w-3.5 h-3.5 text-white" />
                  </button>
                  {i === 0 && <span className="absolute bottom-1 left-1 px-1.5 py-0.5 rounded bg-amber-500/80 text-[9px] font-bold text-slate-900">VOOR</span>}
                </div>
              ))}
              <input ref={fileRef} type="file" multiple accept="image/png,image/jpeg,image/webp" className="hidden"
                onChange={e => uploadFiles(e.target.files)} data-testid="product-img-input" />
              <button onClick={() => fileRef.current?.click()} disabled={uploadingIdx >= 0} data-testid="product-img-add-btn"
                className="w-28 h-28 rounded-lg border-2 border-dashed border-slate-700 hover:border-amber-500/60 flex flex-col items-center justify-center gap-1 text-slate-400 hover:text-amber-400 disabled:opacity-50">
                {uploadingIdx >= 0 ? <Loader2 className="w-5 h-5 animate-spin" /> : <Upload className="w-5 h-5" />}
                <span className="text-[10px]">{uploadingIdx >= 0 ? 'Uploaden…' : 'Voeg foto toe'}</span>
              </button>
            </div>
          </div>

          {/* Naam + prijs */}
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <label className="text-[10px] text-slate-400 uppercase tracking-wider">Titel</label>
              <input data-testid="product-name" value={name} onChange={e => setName(e.target.value)}
                placeholder="Bijv. Roadkill Hoodie Black"
                className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase tracking-wider">Verkoopprijs (€)</label>
              <input data-testid="product-price" type="number" step="0.01" min="0" value={price} onChange={e => setPrice(e.target.value)}
                placeholder="0.00"
                className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500" />
              <p className="text-[9px] text-slate-500 mt-1">Excl. BTW (intern wordt 0% gerekend)</p>
            </div>
          </div>

          {/* Omschrijving */}
          <div>
            <label className="text-[10px] text-slate-400 uppercase tracking-wider">Omschrijving</label>
            <textarea data-testid="product-desc" value={description} onChange={e => setDescription(e.target.value)} rows={3}
              placeholder="Materiaal, maten, levertijd…"
              className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 resize-none" />
          </div>

          {/* Categorie + kasboek (read-only, gekoppeld aan shop) */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-slate-400 uppercase tracking-wider">Categorie</label>
              <select data-testid="product-cat" value={category} onChange={e => setCategory(e.target.value)}
                className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white">
                <option value="merch">Merch (fysiek)</option>
                <option value="digital">Digitaal</option>
                <option value="storage">Opslag</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase tracking-wider">Kasboek</label>
              {/* v11_shop_scope_001 — Kasboek is vast per shop; niet meer los kiesbaar.
                  Voorkomt dat producten in andermans kasboek belanden. */}
              <div data-testid="product-entity-locked"
                className="mt-1 w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-slate-300 flex items-center gap-2">
                <span className="text-amber-400">🔒</span>
                <span className="truncate">{shopName}</span>
                <span className="text-[9px] text-slate-500 ml-auto">auto</span>
              </div>
              <p className="text-[9px] text-slate-500 mt-1">Kasboek volgt de huidige winkel</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input data-testid="product-instock" type="checkbox" checked={inStock} onChange={e => setInStock(e.target.checked)} />
              Op voorraad
            </label>
          </div>

          {error && <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded p-2">{error}</p>}
        </div>
        <div className="px-5 py-3 border-t border-slate-800 flex items-center justify-between gap-2">
          {!isNew && (
            <button onClick={deleteProduct} data-testid="product-delete"
              className="px-3 py-2 text-xs font-medium rounded-lg text-red-300 hover:bg-red-500/10 border border-red-500/30">
              Verwijder product
            </button>
          )}
          <div className="ml-auto flex gap-2">
            <button onClick={onClose} className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700">
              Annuleren
            </button>
            <button onClick={save} disabled={saving} data-testid="product-save"
              className="px-4 py-2 text-sm font-bold rounded-lg text-slate-900 disabled:opacity-60"
              style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
              {saving ? 'Opslaan…' : (isNew ? 'Product aanmaken' : 'Opslaan')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductEditModal;
