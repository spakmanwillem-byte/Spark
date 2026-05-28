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
              Iedere user met gradatie {minGradatie} of hoger kan een eigen winkel openen.
              Spark vraagt {commissieDefault}% commissie op netto-winst voor onderhoud van het platform.
            </p>
            <p className="text-[10px] text-slate-500 mt-2">
              {shops.length} winkels actief · Founder-shop = Roadkillshop (commissie-vrij)
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

  return (
    <div data-testid={`shop-card-${shop.id}`}
      className={`bg-slate-900/50 border rounded-xl p-4 transition-all ${isClosing ? 'border-red-500/30 opacity-70' : 'border-slate-800 hover:border-slate-700'}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: `linear-gradient(135deg, ${accent}, ${accent}88)` }}>
            {isFounder ? <Crown className="w-5 h-5 text-white" /> : <Store className="w-5 h-5 text-white" />}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span className="truncate">{shop.naam}</span>
              {isFounder && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 flex-shrink-0">FOUNDER</span>
              )}
              {isClosing && (
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30 flex-shrink-0">SLUIT</span>
              )}
            </h3>
            <p className="text-[11px] text-slate-400 truncate">{shop.tagline || `Type: ${shop.type}`}</p>
            <p className="text-[10px] text-slate-500 mt-1">
              door {shop.owner_naam || shop.owner_user_id} · commissie {shop.commissie_pct}%
            </p>
          </div>
        </div>
        {isOwner && !isClosing && (
          <button data-testid={`shop-edit-${shop.id}`} onClick={onEdit}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white flex-shrink-0">
            <Edit3 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
      <div className="mt-3 flex items-center gap-2 text-[10px]">
        {(shop.subtabs_enabled || []).map(s => (
          <span key={s} className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">{s}</span>
        ))}
        {isFounder && onNavigate && (
          <button data-testid={`shop-open-${shop.id}`} onClick={onNavigate}
            className="ml-auto text-amber-400 hover:text-amber-300">Bekijk →</button>
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
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [confirmClose, setConfirmClose] = useState(false);
  const [closeReden, setCloseReden] = useState('');

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
