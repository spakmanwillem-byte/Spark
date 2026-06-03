/**
 * Winkelstraat — multi-tenant shop tab (v6_winkelstraat_frontend_001)
 * ----------------------------------------------------------------------------
 * - Lijst van actieve shops (Roadkillshop = founder-shop)
 * - Gradatie ≥ 4: knop "Open mijn winkel" → voorwaarden-modal + create-form
 * - Owner ziet "Bewerken" / "Sluiten" op zijn eigen shops
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Store, Plus, Edit3, X, Loader2, Check, AlertCircle, Crown, Lock } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function WinkelstraatTab({ user, onNavigateToShop }) {
  const userId = user?.id;
  const gradatie = user?.gradatie ?? 7;
  const [shops, setShops] = useState([]);
  const [minGradatie, setMinGradatie] = useState(4);
  const [commissieDefault, setCommissieDefault] = useState(2.0);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editShop, setEditShop] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    fetch(`${API}/api/winkelstraat/shops`)
      .then(r => r.json())
      .then(d => {
        setShops(d.shops || []);
        setMinGradatie(d.min_gradatie_to_open || 4);
        setCommissieDefault(d.commissie_default_pct || 2.0);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const eligible = gradatie <= minGradatie;
  const canOpen = eligible;
  const ownActive = shops.filter(s => s.owner_user_id === userId && s.status === 'active').length;

  if (loading) {
    return <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 text-amber-400 animate-spin" /></div>;
  }

  return (
    <div data-testid="winkelstraat-tab" className="space-y-4">
      {/* Header card met info + Open-mijn-winkel knop */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Store className="w-5 h-5 text-amber-400" /> Winkelstraat
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {/* v6_shop_card_redesign_001 — Commissie staat niet meer in de openbare tekst.
                  Eigenaars zien voorwaarden bij Open-mijn-winkel; klanten zien % alleen op de bon. */}
              Iedere user met gradatie {minGradatie} of hoger kan een eigen winkel openen.
            </p>
            <p className="text-[10px] text-slate-500 mt-2">
              {shops.length} {shops.length === 1 ? 'winkel actief' : 'winkels actief'}
            </p>
          </div>
          {canOpen ? (
            <button data-testid="open-shop-btn"
              onClick={() => setShowCreate(true)}
              disabled={ownActive >= 3}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-white bg-amber-500 hover:bg-amber-600 transition-all disabled:opacity-40">
              <Plus className="w-4 h-4" />
              {ownActive >= 3 ? `Max 3 (${ownActive}/3)` : 'Open mijn winkel'}
            </button>
          ) : (
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-slate-500 border border-slate-800">
              <Lock className="w-3.5 h-3.5" />
              Gradatie ≤ {minGradatie} vereist
            </div>
          )}
        </div>
      </div>

      {/* Shop-lijst */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {shops.map(shop => (
          <ShopCard key={shop.id} shop={shop} viewerId={userId} onEdit={() => setEditShop(shop)} onNavigate={onNavigateToShop} />
        ))}
        {shops.length === 0 && (
          <div className="col-span-2 py-8 text-center text-slate-500 text-sm">
            Nog geen winkels. Wees de eerste!
          </div>
        )}
      </div>

      {showCreate && (
        <CreateShopModal
          userId={userId}
          ownerNaam={user?.naam}
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); load(); }}
          commissieDefault={commissieDefault}
        />
      )}

      {editShop && (
        <EditShopModal
          shop={editShop}
          viewerId={userId}
          onClose={() => setEditShop(null)}
          onSaved={() => { setEditShop(null); load(); }}
        />
      )}
    </div>
  );
}

// ============================================================================
function ShopCard({ shop, viewerId, onEdit, onNavigate }) {
  const isOwner = shop.owner_user_id === viewerId;
  const isFounder = shop.is_founder_shop;
  const isClosing = shop.status === 'closing';
  const accent = shop.color_accent || '#f59e0b';
  // v6_shop_card_redesign_001 — Banner met groot bedrijfslogo, geen filosofie/commissie zichtbaar.
  // Commissie komt op de bon en in de owner-voorwaarden, niet in de openbare straat.
  const logoUrl = shop.logo_url ? (shop.logo_url.startsWith('http') ? shop.logo_url : `${API}${shop.logo_url}`) : null;
  const ownerAvatar = shop.owner_avatar_url ? (shop.owner_avatar_url.startsWith('http') ? shop.owner_avatar_url : `${API}${shop.owner_avatar_url}`) : null;

  return (
    <div data-testid={`shop-card-${shop.id}`}
      onClick={() => !isClosing && onNavigate && onNavigate(shop.id)}
      className={`bg-slate-900/50 border rounded-xl overflow-hidden transition-all cursor-pointer ${
        isClosing ? 'border-red-500/30 opacity-70 cursor-default' : 'border-slate-800 hover:border-amber-500/50 hover:shadow-lg hover:shadow-amber-500/5'
      }`}>

      {/* Banner met groot bedrijfslogo */}
      <div className="relative h-28 flex items-center justify-center overflow-hidden"
        style={{ background: `linear-gradient(135deg, ${accent}22 0%, ${accent}11 50%, #0f172a 100%)` }}>
        {logoUrl ? (
          <img src={logoUrl} alt={shop.naam}
            className="max-h-20 max-w-[60%] object-contain drop-shadow-lg" />
        ) : (
          <Store className="w-12 h-12" style={{ color: accent, opacity: 0.5 }} />
        )}
        {/* Badges in banner-rechterbovenhoek */}
        <div className="absolute top-2 right-2 flex items-center gap-1">
          {isFounder && (
            <span data-testid={`shop-badge-founder-${shop.id}`}
              className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/30 text-amber-200 border border-amber-400/50 backdrop-blur-sm font-semibold">
              FOUNDER
            </span>
          )}
          {isClosing && (
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-500/30 text-red-200 border border-red-400/50 backdrop-blur-sm font-semibold">
              SLUIT
            </span>
          )}
        </div>
        {/* Edit-knop voor owner (rechtsboven, alleen voor eigenaar) */}
        {isOwner && !isClosing && (
          <button data-testid={`shop-edit-${shop.id}`} onClick={(e) => { e.stopPropagation(); onEdit(); }}
            title="Winkel bewerken"
            className="absolute top-2 left-2 p-1.5 rounded-lg bg-slate-900/60 hover:bg-slate-900/80 text-slate-300 hover:text-white backdrop-blur-sm">
            <Edit3 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Footer-strip: owner-avatar + shop-naam + bekijk */}
      <div className="px-3 py-2.5 flex items-center gap-2.5 border-t border-slate-800/80">
        {ownerAvatar ? (
          <img src={ownerAvatar} alt={shop.owner_naam || 'owner'}
            className="w-8 h-8 rounded-full object-cover border-2 flex-shrink-0"
            style={{ borderColor: accent }} />
        ) : (
          <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-white font-bold text-xs border-2"
            style={{ background: `linear-gradient(135deg, ${accent}, ${accent}88)`, borderColor: accent }}>
            {(shop.owner_naam || shop.owner_user_id || '?').charAt(0).toUpperCase()}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-bold text-white truncate" data-testid={`shop-name-${shop.id}`}>
            {shop.naam}
          </h3>
          <p className="text-[10px] text-slate-500 truncate">
            door {shop.owner_naam || shop.owner_user_id}
          </p>
        </div>
        {/* Tag-cluster (compact) */}
        {(shop.subtabs_enabled || []).slice(0, 2).map(s => (
          <span key={s} className="hidden sm:inline-block text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400">
            {s}
          </span>
        ))}
        {!isClosing && onNavigate && (
          <span className="text-amber-400 text-xs flex-shrink-0 ml-1">→</span>
        )}
      </div>
    </div>
  );
}

// ============================================================================
function CreateShopModal({ userId, ownerNaam, onClose, onCreated, commissieDefault }) {
  const [step, setStep] = useState('voorwaarden'); // voorwaarden → form
  const [accepted, setAccepted] = useState(false);
  const [voorwaarden, setVoorwaarden] = useState(null);
  const [naam, setNaam] = useState('');
  const [type, setType] = useState('hybride');
  const [tagline, setTagline] = useState('');
  const [color, setColor] = useState('#f59e0b');
  const [creating, setCreating] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    fetch(`${API}/api/winkelstraat/voorwaarden`).then(r => r.json()).then(d => setVoorwaarden(d.voorwaarden));
  }, []);

  const submit = async () => {
    setCreating(true);
    setErr('');
    try {
      const r = await fetch(`${API}/api/winkelstraat/shops`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          naam, type, tagline, color_accent: color,
          owner_user_id: userId, owner_naam: ownerNaam,
          voorwaarden_geaccepteerd: true,
        }),
      });
      const d = await r.json();
      if (!r.ok || !d.success) { setErr(d.detail || 'Aanmaken mislukt'); setCreating(false); return; }
      onCreated();
    } catch (e) { setErr(e.message); setCreating(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="create-shop-modal">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <div className="relative bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Store className="w-5 h-5 text-amber-400" />
            {step === 'voorwaarden' ? 'Voorwaarden' : 'Nieuwe winkel'}
          </h2>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
        </div>

        {step === 'voorwaarden' && voorwaarden && (
          <div className="p-5 space-y-4">
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
              <p className="text-xs text-amber-200 italic">"{voorwaarden.kernzin}"</p>
            </div>
            <div className="space-y-2.5">
              {(voorwaarden.artikelen || []).map(art => (
                <div key={art.nr} className="bg-slate-800/40 rounded-lg p-3">
                  <p className="text-[11px] font-bold text-white">Art. {art.nr} — {art.titel}</p>
                  <p className="text-[11px] text-slate-300 mt-1">{art.tekst}</p>
                </div>
              ))}
            </div>
            <label className="flex items-start gap-2 cursor-pointer" data-testid="accept-voorwaarden">
              <input type="checkbox" checked={accepted} onChange={e => setAccepted(e.target.checked)}
                className="mt-0.5" />
              <span className="text-xs text-slate-300">
                Ik accepteer de voorwaarden en de {commissieDefault}% commissie op netto-winst.
              </span>
            </label>
            <div className="flex gap-2 pt-2">
              <button onClick={onClose} className="flex-1 py-2.5 rounded-xl text-sm text-slate-400 border border-slate-700 hover:bg-slate-800">
                Annuleer
              </button>
              <button data-testid="voorwaarden-next-btn" disabled={!accepted}
                onClick={() => setStep('form')}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white bg-amber-500 hover:bg-amber-600 disabled:opacity-40">
                Volgende →
              </button>
            </div>
          </div>
        )}

        {step === 'form' && (
          <div className="p-5 space-y-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Naam *</label>
              <input data-testid="shop-naam" value={naam} onChange={e => setNaam(e.target.value)}
                placeholder="Bijv. Marieke's Boekenhoek"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:border-amber-500" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Type</label>
              <select data-testid="shop-type" value={type} onChange={e => setType(e.target.value)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm">
                <option value="merch">Merch (fysiek)</option>
                <option value="digitaal">Digitaal</option>
                <option value="hybride">Hybride</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Tagline (optioneel)</label>
              <input data-testid="shop-tagline" value={tagline} onChange={e => setTagline(e.target.value)}
                placeholder="Wat verkoop je in 1 zin?"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:border-amber-500" />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Accent-kleur</label>
              <input data-testid="shop-color" type="color" value={color} onChange={e => setColor(e.target.value)}
                className="w-16 h-9 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer" />
            </div>
            {err && (
              <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-center gap-2">
                <AlertCircle className="w-3.5 h-3.5" /> {err}
              </div>
            )}
            <div className="flex gap-2 pt-2">
              <button onClick={() => setStep('voorwaarden')} className="flex-1 py-2.5 rounded-xl text-sm text-slate-400 border border-slate-700 hover:bg-slate-800">
                ← Terug
              </button>
              <button data-testid="create-shop-confirm" disabled={!naam || creating}
                onClick={submit}
                className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white bg-amber-500 hover:bg-amber-600 disabled:opacity-40 flex items-center justify-center gap-2">
                {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Aanmaken
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
function EditShopModal({ shop, viewerId, onClose, onSaved }) {
  const [naam, setNaam] = useState(shop.naam || '');
  const [tagline, setTagline] = useState(shop.tagline || '');
  const [color, setColor] = useState(shop.color_accent || '#f59e0b');
  const [logoUrl, setLogoUrl] = useState(shop.logo_url || '');
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [confirmClose, setConfirmClose] = useState(false);
  const [closeReden, setCloseReden] = useState('');

  const uploadLogo = async (file) => {
    if (!file) return;
    setUploadingLogo(true); setErr('');
    try {
      const fd = new FormData();
      fd.append('logo', file);
      fd.append('actor_user_id', viewerId);
      const r = await fetch(`${API}/api/winkelstraat/shops/${shop.id}/logo`, { method: 'POST', body: fd });
      const d = await r.json();
      if (!r.ok || !d.success) { setErr(d.detail || 'Logo upload mislukt'); setUploadingLogo(false); return; }
      setLogoUrl(d.logo_url);
    } catch (e) { setErr(e.message); }
    setUploadingLogo(false);
  };

  const save = async () => {
    setBusy(true); setErr('');
    try {
      const r = await fetch(`${API}/api/winkelstraat/shops/${shop.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actor_user_id: viewerId, patch: { naam, tagline, color_accent: color } }),
      });
      const d = await r.json();
      if (!r.ok || !d.success) { setErr(d.detail || 'Opslaan mislukt'); setBusy(false); return; }
      onSaved();
    } catch (e) { setErr(e.message); setBusy(false); }
  };

  const closeShop = async () => {
    setBusy(true); setErr('');
    try {
      const r = await fetch(`${API}/api/winkelstraat/shops/${shop.id}/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actor_user_id: viewerId, reden: closeReden || null }),
      });
      const d = await r.json();
      if (!r.ok || !d.success) { setErr(d.detail || 'Sluiten mislukt'); setBusy(false); return; }
      onSaved();
    } catch (e) { setErr(e.message); setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="edit-shop-modal">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <div className="relative bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">Bewerk {shop.naam}</h2>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-5 space-y-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Naam</label>
            <input data-testid="edit-shop-naam" value={naam} onChange={e => setNaam(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Tagline</label>
            <input data-testid="edit-shop-tagline" value={tagline} onChange={e => setTagline(e.target.value)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Accent-kleur</label>
            <input data-testid="edit-shop-color" type="color" value={color} onChange={e => setColor(e.target.value)}
              className="w-16 h-9 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Shop logo (verschijnt naast naam)</label>
            <div className="flex items-center gap-3">
              {logoUrl ? (
                <img src={logoUrl.startsWith('http') ? logoUrl : `${API}${logoUrl}`} alt="logo"
                  className="w-12 h-12 rounded object-contain bg-slate-800 border border-slate-700" />
              ) : (
                <div className="w-12 h-12 rounded bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-600 text-[10px]">geen</div>
              )}
              <label className="flex-1 cursor-pointer">
                <input type="file" accept="image/*" className="hidden"
                  onChange={e => uploadLogo(e.target.files?.[0])} data-testid="upload-logo-input" />
                <div className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300 hover:bg-slate-700 text-center">
                  {uploadingLogo ? 'Uploading...' : (logoUrl ? 'Vervang logo' : 'Upload logo')}
                </div>
              </label>
            </div>
          </div>
          {err && (
            <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5" /> {err}
            </div>
          )}
          <div className="flex gap-2 pt-2">
            <button data-testid="edit-shop-save" disabled={busy} onClick={save}
              className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white bg-amber-500 hover:bg-amber-600 disabled:opacity-40">
              {busy ? 'Bezig...' : 'Opslaan'}
            </button>
          </div>
          <div className="pt-3 border-t border-slate-800">
            {!confirmClose ? (
              <button data-testid="request-close-btn" onClick={() => setConfirmClose(true)}
                className="w-full py-2 rounded-xl text-xs text-red-400 border border-red-500/30 hover:bg-red-500/10">
                Sluiting aanvragen…
              </button>
            ) : (
              <div className="space-y-2">
                <p className="text-xs text-red-300">Weet je zeker dat je deze winkel wil sluiten?</p>
                <input data-testid="close-reden" value={closeReden} onChange={e => setCloseReden(e.target.value)}
                  placeholder="Reden (optioneel)"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-xs" />
                <div className="flex gap-2">
                  <button onClick={() => setConfirmClose(false)} className="flex-1 py-2 rounded-xl text-xs text-slate-400 border border-slate-700">
                    Annuleer
                  </button>
                  <button data-testid="confirm-close-btn" disabled={busy} onClick={closeShop}
                    className="flex-1 py-2 rounded-xl text-xs font-semibold text-white bg-red-600 hover:bg-red-700 disabled:opacity-40">
                    Ja, sluiten
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default WinkelstraatTab;
