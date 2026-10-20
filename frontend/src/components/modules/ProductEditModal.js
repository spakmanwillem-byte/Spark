// v6_shop_admin_product_crud_001 — Admin: nieuw / bewerk product met meerdere afbeeldingen
import React, { useState, useEffect, useRef } from 'react';
import { X, Upload, Trash2, Loader2, Plus } from 'lucide-react';
import { apiError } from '../../lib/utils';

const API = process.env.REACT_APP_BACKEND_URL;
const MATEN_STD = ['S', 'M', 'L', 'XL', 'XXL', 'XXXL'];
const KLEUREN_STD = ['Navy blauw', 'Khaki groen', 'Zwart', 'Marble grijs'];

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
  // v14_shop_producten_tab_001 — productcode, voorraad, leverancier (hybride link naar zakelijke contacten)
  const [productCode, setProductCode] = useState('');
  const [voorraad, setVoorraad] = useState('');
  const [leverancierId, setLeverancierId] = useState('');
  const [leverancierNaam, setLeverancierNaam] = useState('');
  const [leveranciers, setLeveranciers] = useState([]);
  // v14_shop_inkoop_stuklijst_001 — stuklijst: inkoop-artikelen × aantal
  const [inkoop, setInkoop] = useState([]);
  const [stuklijst, setStuklijst] = useState([]);
  // v14_shop_varianten_001 — maten/kleuren die de koper kiest
  const [maten, setMaten] = useState([]);
  const [kleuren, setKleuren] = useState([]);
  const [uploadingIdx, setUploadingIdx] = useState(-1);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  // v11_shop_scope_001 — entity_id (kasboek) volgt automatisch de shop-context.
  // shop-roadkill → 'roadkill_merch' (bestaand), andere shops → 'shop_<id>'.
  const derivedEntityId = shopId === 'shop-roadkill' ? 'roadkill_merch' : `shop_${shopId}`;
  // v11_roar_token_readonly_001 — ROAR Token in Spark Shop is display-only;
  // prijs wordt bepaald door potjes-mechaniek, niet handmatig.
  const isRoarToken = product?.id === 'roar-token' || product?.category === 'token';

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
      setProductCode(product.product_code || ''); setVoorraad(product.voorraad ?? '');
      setLeverancierId(product.leverancier_contact_id || ''); setLeverancierNaam(product.leverancier_naam || '');
      setStuklijst(product.stuklijst || []);
      setMaten(product.maten || []); setKleuren(product.kleuren || []);
    } else {
      setName(''); setDescription(''); setPrice(''); setCategory(defaultCategory);
      setEntityId(derivedEntityId);
      setInStock(true); setImageIcon('package'); setImages([]);
      setProductCode(''); setVoorraad(''); setLeverancierId(''); setLeverancierNaam(''); setStuklijst([]); setMaten([]); setKleuren([]);
    }
  }, [open, product, defaultCategory, derivedEntityId]);

  useEffect(() => {
    if (!open || !shopId) return;
    fetch(`${API}/api/shop/shops/${encodeURIComponent(shopId)}/inkoop`).then(r => r.json())
      .then(d => setInkoop(d.inkoop || [])).catch(() => setInkoop([]));
  }, [open, shopId]);

  const kostprijs = stuklijst.length ? stuklijst.reduce((sum, r) => {
    const a = inkoop.find(x => x.id === r.inkoop_id);
    if (!a || a.inkoopprijs_excl == null) return NaN;
    return sum + Number(a.inkoopprijs_excl) * Number(r.aantal || 1);
  }, 0) : null;
  const kostprijsOk = kostprijs != null && !Number.isNaN(kostprijs) && kostprijs > 0;
  const [margePct, setMargePct] = useState('');
  useEffect(() => {
    if (!kostprijsOk) return;
    const p = parseFloat(price);
    const m = Number.isNaN(p) ? '' : String(Math.round(((p - kostprijs) / kostprijs) * 100));
    setMargePct(prev => (prev !== '' && !Number.isNaN(parseFloat(prev)) && Math.abs((kostprijs * (1 + parseFloat(prev) / 100)) - p) < 0.011 ? prev : m));
  }, [price, kostprijs, kostprijsOk]);

  useEffect(() => {
    if (!open) return;
    fetch(`${API}/api/contacten/${userId}?laag=zakelijk`).then(r => r.json())
      .then(d => setLeveranciers((d.contacten || []).filter(c => !c.rol || c.rol === 'leverancier' || c.rol === 'partner' || c.rol === 'overig')))
      .catch(() => setLeveranciers([]));
  }, [open, userId]);

  const extraFields = () => ({
    maten, kleuren,
    stuklijst: stuklijst.filter(r => r.inkoop_id).map(r => ({ inkoop_id: r.inkoop_id, aantal: Number(r.aantal) || 1 })),
    product_code: productCode || null,
    voorraad: voorraad === '' ? null : parseInt(voorraad, 10),
    leverancier_contact_id: leverancierId || null,
    leverancier_naam: leverancierNaam || (leveranciers.find(c => c.id === leverancierId)?.naam ?? null),
  });

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
        body: JSON.stringify({ viewer_id: userId, name, description, price: pr, category, entity_id: entityId, in_stock: inStock, image_icon: imageIcon, shop_id: shopId, ...extraFields() }),
      }).then(r => r.json());
      if (!created.success) { setError(apiError(created, 'Aanmaken mislukt')); return; }
      pid = created.product.id;
    }
    const newImgs = [...images];
    for (let i = 0; i < files.length; i++) {
      setUploadingIdx(i);
      const fd = new FormData();
      fd.append('image', files[i]);
      fd.append('viewer_id', userId);
      // v12_shop_owner_perms_001 — shop_id nodig zodat backend de owner-check kan doen
      fd.append('shop_id', shopId || 'shop-roadkill');
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
      const body = { viewer_id: userId, name, description, price: pr, category, entity_id: entityId, in_stock: inStock, image_icon: imageIcon, images, shop_id: shopId, ...extraFields() };
      const url = isNew ? `${API}/api/shop/admin/products` : `${API}/api/shop/admin/products/${product.id}`;
      const method = isNew ? 'POST' : 'PUT';
      const r = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(x => x.json());
      if (!r.success) { setError(apiError(r, 'Opslaan mislukt')); return; }
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
          <h3 className="text-base font-bold text-white">
            {isRoarToken ? `ROAR Token — weergave` : (isNew ? 'Nieuw product' : `Bewerk: ${product.name}`)}
          </h3>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-800 rounded-lg"><X className="w-4 h-4 text-slate-400" /></button>
        </div>
        {isRoarToken && (
          <div className="mx-5 mt-3 rounded-lg bg-amber-500/10 border border-amber-500/30 px-3 py-2 text-[11px] text-amber-200 leading-relaxed">
            <strong>Read-only.</strong> ROAR-tokenprijs wordt automatisch bepaald door het potjes-systeem
            (revalue op basis van live Bitvavo BCH/ETH-koers). Aanpassen aan naam of prijs zou een
            valse waarde tonen — daarom hier alleen zichtbaar.
          </div>
        )}
        <div className={`flex-1 overflow-y-auto p-5 space-y-4 ${isRoarToken ? 'pointer-events-none opacity-70' : ''}`}>
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
              {/* v14_shop_marge_hybride_001 — Willem 20-10: marge % intypen → verkoopprijs volgt (en andersom) */}
              {kostprijsOk && (
                <div data-testid="product-marge-kader" className="mt-2 grid grid-cols-3 gap-2 items-end">
                  <div>
                    <label className="text-[9px] text-slate-500 uppercase">Marge %</label>
                    <input data-testid="product-marge-pct" type="number" step="1" value={margePct}
                      onChange={e => { setMargePct(e.target.value); const m = parseFloat(e.target.value); if (!Number.isNaN(m)) setPrice((kostprijs * (1 + m / 100)).toFixed(2)); }}
                      className="mt-0.5 w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-amber-500" />
                  </div>
                  <div>
                    <label className="text-[9px] text-slate-500 uppercase">Kostprijs</label>
                    <p className="text-xs text-slate-300 py-1.5">€{kostprijs.toFixed(2)}</p>
                  </div>
                  <div>
                    <label className="text-[9px] text-slate-500 uppercase">Marge €</label>
                    <p data-testid="product-marge-eur" className={`text-xs py-1.5 font-semibold ${Number(price || 0) - kostprijs >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>€{(Number(price || 0) - kostprijs).toFixed(2)}</p>
                  </div>
                </div>
              )}
              <p className="text-[9px] text-slate-500 mt-1">Excl. BTW — de winkelwagen rekent de BTW van de winkel erbij.{kostprijs != null && Number.isNaN(kostprijs) && (
                <span className="text-slate-500"> Kostprijs onbekend (inkoopprijs ontbreekt) — vul de stuklijst aan voor marge-berekening.</span>
              )}</p>
            </div>
          </div>

          {/* Omschrijving */}
          <div>
            <label className="text-[10px] text-slate-400 uppercase tracking-wider">Omschrijving</label>
            <textarea data-testid="product-desc" value={description} onChange={e => setDescription(e.target.value)} rows={3}
              placeholder="Materiaal, maten, levertijd…"
              className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 resize-none" />
          </div>

          {/* v14_shop_inkoop_stuklijst_001 — stuklijst: welke inkoop-artikelen (productcodes) maken dit product */}
          <div data-testid="product-stuklijst" className="bg-slate-800/40 border border-slate-700 rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[10px] text-slate-400 uppercase tracking-wider">Stuklijst (inkoop-artikelen)</label>
              <button type="button" data-testid="stuklijst-add" onClick={() => setStuklijst(l => [...l, { inkoop_id: '', aantal: 1 }])}
                className="text-[10px] text-amber-300 hover:text-amber-200">+ regel</button>
            </div>
            {stuklijst.length === 0 && <p className="text-[10px] text-slate-500">Leeg = jij levert dit zelf, zonder onderdelen. Inkoop-artikelen beheer je in Producten → Inkoop.</p>}
            {stuklijst.map((r, i) => {
              const a = inkoop.find(x => x.id === r.inkoop_id);
              return (
                <div key={i} className="flex items-center gap-2">
                  <select data-testid={`stuklijst-item-${i}`} value={r.inkoop_id} onChange={e => setStuklijst(l => l.map((x, j) => j === i ? { ...x, inkoop_id: e.target.value } : x))}
                    className="flex-1 px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white">
                    <option value="">— kies artikel —</option>
                    {inkoop.map(x => <option key={x.id} value={x.id}>{x.code ? `${x.code} · ` : ''}{x.naam}{x.inkoopprijs_excl != null ? ` (€${Number(x.inkoopprijs_excl).toFixed(2)})` : ''}</option>)}
                  </select>
                  <input data-testid={`stuklijst-aantal-${i}`} type="number" min="1" value={r.aantal} onChange={e => setStuklijst(l => l.map((x, j) => j === i ? { ...x, aantal: e.target.value } : x))}
                    className="w-16 px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white text-right" />
                  <span className="w-16 text-right text-[11px] text-slate-400">{a && a.inkoopprijs_excl != null ? `€${(Number(a.inkoopprijs_excl) * Number(r.aantal || 1)).toFixed(2)}` : '—'}</span>
                  <button type="button" onClick={() => setStuklijst(l => l.filter((_, j) => j !== i))} className="text-slate-500 hover:text-red-400 text-xs">✕</button>
                </div>
              );
            })}
          </div>

          {/* v14_shop_varianten_001 — maten/kleuren */}
          <div data-testid="product-varianten" className="grid grid-cols-2 gap-3">
            {[['Maten', maten, setMaten, MATEN_STD, 'maat'], ['Kleuren', kleuren, setKleuren, KLEUREN_STD, 'kleur']].map(([label, list, setList, std, tid]) => (
              <div key={label} className="bg-slate-800/40 border border-slate-700 rounded-lg p-2">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] text-slate-400 uppercase tracking-wider">{label} (koper kiest)</label>
                  <button type="button" onClick={() => setList(list.length ? [] : [...std])} className="text-[10px] text-amber-300">{list.length ? 'wis' : 'standaard'}</button>
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {[...new Set([...std, ...list])].map(v => (
                    <button type="button" key={v} data-testid={`product-${tid}-${v}`} onClick={() => setList(list.includes(v) ? list.filter(x => x !== v) : [...list, v])}
                      className={`px-2 py-0.5 rounded text-[10px] border ${list.includes(v) ? 'border-amber-500/60 text-amber-200 bg-amber-500/10' : 'border-slate-700 text-slate-500'}`}>{v}</button>
                  ))}
                  <input placeholder="+ eigen" onKeyDown={e => { if (e.key === 'Enter' && e.target.value.trim()) { setList([...list, e.target.value.trim()]); e.target.value = ''; e.preventDefault(); } }}
                    className="w-16 px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded text-[10px] text-white" />
                </div>
              </div>
            ))}
          </div>

          {/* v14_shop_producten_tab_001 — eigen code, voorraad, leverancier (alleen zonder stuklijst) */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-[10px] text-slate-400 uppercase tracking-wider">Eigen code (optioneel)</label>
              <input data-testid="product-code" value={productCode} onChange={e => setProductCode(e.target.value)} placeholder="leeg = Spark maakt er een (RK-0001)"
                className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase tracking-wider">Voorraad</label>
              <input data-testid="product-voorraad" type="number" min="0" value={voorraad} onChange={e => setVoorraad(e.target.value)} placeholder="leeg = onbekend"
                className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
            </div>
            <div>
              <label className="text-[10px] text-slate-400 uppercase tracking-wider">Leverancier</label>
              <select data-testid="product-leverancier" value={leverancierId} onChange={e => { setLeverancierId(e.target.value); setLeverancierNaam(''); }}
                className="mt-1 w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white">
                <option value="">— geen / zelf —</option>
                {leveranciers.map(c => <option key={c.id} value={c.id}>{c.naam}{c.rol ? ` (${c.rol})` : ''}</option>)}
              </select>
              {!leverancierId && (
                <input data-testid="product-leverancier-naam" value={leverancierNaam} onChange={e => setLeverancierNaam(e.target.value)} placeholder="of typ een naam"
                  className="mt-1 w-full px-2 py-1 bg-slate-800/60 border border-slate-700 rounded text-[11px] text-white placeholder-slate-500" />
              )}
            </div>
          </div>
          <p className="text-[9px] text-slate-500 -mt-2">Leverancier hier alleen als er géén stuklijst is; met stuklijst komt de leverancier van de inkoop-artikelen.</p>

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
          {!isNew && !isRoarToken && (
            <button onClick={deleteProduct} data-testid="product-delete"
              className="px-3 py-2 text-xs font-medium rounded-lg text-red-300 hover:bg-red-500/10 border border-red-500/30">
              Verwijder product
            </button>
          )}
          <div className="ml-auto flex gap-2">
            <button onClick={onClose} className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700">
              {isRoarToken ? 'Sluiten' : 'Annuleren'}
            </button>
            {!isRoarToken && (
              <button onClick={save} disabled={saving} data-testid="product-save"
                className="px-4 py-2 text-sm font-bold rounded-lg text-slate-900 disabled:opacity-60"
                style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
                {saving ? 'Opslaan…' : (isNew ? 'Product aanmaken' : 'Opslaan')}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductEditModal;
