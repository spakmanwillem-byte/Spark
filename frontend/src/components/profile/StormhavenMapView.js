/**
 * StormhavenMapView (v6_dnd_dorp_zoom_001)
 *
 * Volledig dorp-zoom modal: foto van "Basis dorp" als achtergrond,
 * gebouwen geplaatst als klikbare hotspots over de plattegrond.
 *
 * Layout (% van plattegrond, geoptimaliseerd voor de cirkelvormige basis-dorp foto):
 *   Center        — Tempel van Spark         (50%, 50%)
 *   N             — Waterput #1              (50%, 22%)
 *   NE            — Slager gebouw            (72%, 32%)
 *   E             — Markt (placeholder)      (78%, 50%)
 *   SE            — Bakker gebouw            (72%, 68%)
 *   S             — Waterput #2              (50%, 78%)
 *   SW            — Kleine straat            (28%, 68%)
 *   W             — Smederij (placeholder)   (22%, 50%)
 *   NW            — Waterput #3              (28%, 32%)
 */
import React, { useState, useEffect, useRef } from 'react';
import { X, MapPin, Sparkles, Plus, Move, Save, Lock } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// v6_dorp_buildings_full_001 — alle gebouwen uit blueprint dnd_dorp_layout.json
// Posities op octagonal-layout. Lege wedges krijgen ?-marker via placeholder.
const BUILDING_LAYOUT = [
  // ===== CENTER =====
  { id: 'tempel_spark',  pos: [50, 50], label: 'Tempel van Spark',  keywords: ['tempel van spark', 'tempel', 'spark'], badge: 'CENTER', central: true, placeholder: true },

  // ===== 8 WEDGES =====
  { id: 'gemeentehuis',  pos: [50, 18], label: 'Gemeentehuis',      keywords: ['gemeentehuis'],            placeholder: true },
  { id: 'smederij',      pos: [76, 28], label: 'Smederij',          keywords: ['smederij', 'smid'],         placeholder: true },
  { id: 'herberg',       pos: [85, 50], label: 'Herberg',           keywords: ['herberg'],                  placeholder: true },
  { id: 'wachterspost',  pos: [76, 72], label: 'Wachterspost',      keywords: ['wachterspost', 'wachter'],  placeholder: true },
  { id: 'akker',         pos: [50, 82], label: 'Akker',             keywords: ['akker', 'akkerveld'],       placeholder: true },
  { id: 'houthakkerij',  pos: [24, 72], label: 'Houthakkerij',      keywords: ['houthakkerij'],             placeholder: true },
  { id: 'kruidenwinkel', pos: [15, 50], label: 'Kruidenwinkel',     keywords: ['kruidenwinkel'],            placeholder: true },
  { id: 'jachthut',      pos: [24, 28], label: 'Jachthut',          keywords: ['jachthut'],                 placeholder: true },

  // ===== EXTRA WEDGES (markt + warehouse + auction + barracks) =====
  { id: 'markt',         pos: [62, 38], label: 'Markt',             keywords: ['markt', 'marktplaats'],     placeholder: true },
  { id: 'warehouse',     pos: [38, 38], label: 'Stedelijk Pakhuis', keywords: ['stedelijk pakhuis', 'warehouse', 'pakhuis'], placeholder: true },
  { id: 'auctionhouse',  pos: [62, 62], label: 'Auction House',     keywords: ['auction house', 'auctionhouse'], placeholder: true },
  { id: 'barracks',      pos: [38, 62], label: 'Kazerne',           keywords: ['kazerne', 'barracks'],      placeholder: true },

  // ===== PERIMETER (4 muren) =====
  { id: 'muur_n', pos: [50, 7],  label: 'Stadsmuur N', keywords: ['stadsmuur'], small: true, placeholder: true },
  { id: 'muur_o', pos: [93, 50], label: 'Stadsmuur O', keywords: ['stadsmuur'], small: true, placeholder: true },
  { id: 'muur_z', pos: [50, 93], label: 'Stadsmuur Z', keywords: ['stadsmuur'], small: true, placeholder: true },
  { id: 'muur_w', pos: [7,  50], label: 'Stadsmuur W', keywords: ['stadsmuur'], small: true, placeholder: true },

  // ===== PERIMETER (4 poorten) =====
  { id: 'poort_n', pos: [50, 4],  label: 'Stadspoort N', keywords: ['stadspoort'], small: true, placeholder: true },
  { id: 'poort_o', pos: [96, 50], label: 'Stadspoort O', keywords: ['stadspoort'], small: true, placeholder: true },
  { id: 'poort_z', pos: [50, 96], label: 'Stadspoort Z', keywords: ['stadspoort'], small: true, placeholder: true },
  { id: 'poort_w', pos: [4,  50], label: 'Stadspoort W', keywords: ['stadspoort'], small: true, placeholder: true },

  // ===== RIOLEN (avontuur) =====
  { id: 'riool_o', pos: [70, 65], label: 'Riool Oost', keywords: ['riool', 'riool-ingang'], small: true, placeholder: true },
  { id: 'riool_w', pos: [30, 65], label: 'Riool West', keywords: ['riool', 'riool-ingang'], small: true, placeholder: true },
];

function findCardFor(keywords, cards) {
  if (!cards) return null;
  const kw = keywords.map(k => String(k).toLowerCase());
  for (const k of kw) {
    const m = cards.find(c => (c.tags || []).some(t => String(t).toLowerCase() === k));
    if (m) return m;
  }
  for (const k of kw) {
    const m = cards.find(c => String(c.begrip || '').toLowerCase().includes(k));
    if (m) return m;
  }
  return null;
}

export function StormhavenMapView({ dorpCard, gameCards, char, onClose, stadNaam, fractieNaam, isAdmin = false }) {
  // v6_dnd_stad_minimap_001 — labels nu dynamisch ipv hardcoded 'Stormhaven/Spark'
  const displayNaam = stadNaam || char?.dorp || dorpCard?.begrip || 'Onbekend';
  const displayFractie = fractieNaam || char?.fractie_naam || char?.fractie || 'Neutraal';
  const dorpImg = dorpCard?.media?.image_urls?.[0] ? `${API}${dorpCard.media.image_urls[0]}` : null;

  // v6_dorp_layout_overrides_001 — admin kan posities slepen
  const [editMode, setEditMode] = useState(false);
  const [overrides, setOverrides] = useState({});   // {building_id: {x, y}}
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const mapRef = useRef(null);

  // v6_dorp_walk_to_building_001 — avatar loopt naar gebouw + trade-bark opent
  const startPos = { x: char?.player_x_pct ?? 53, y: char?.player_y_pct ?? 53 };
  const [playerPos, setPlayerPos] = useState(startPos);
  const [tradeBark, setTradeBark] = useState(null);   // {building} of null
  const [walking, setWalking] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/dnd/spark-world/dorp-layout-overrides`)
      .then(r => r.json())
      .then(d => setOverrides(d.overrides || {}))
      .catch(() => {});
  }, []);

  const updateOverride = (buildingId, x, y) => {
    setOverrides(prev => ({ ...prev, [buildingId]: { x, y } }));
    setDirty(true);
  };

  const saveOverrides = async () => {
    setSaving(true);
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/dorp-layout-overrides`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ overrides }),
      });
      if (r.ok) setDirty(false);
    } catch (e) {
      // negeer fout — gebruiker ziet "Opslaan" knop blijven en kan opnieuw klikken
    }
    finally { setSaving(false); }
  };

  const resetOverride = (buildingId) => {
    setOverrides(prev => {
      const next = { ...prev };
      delete next[buildingId];
      return next;
    });
    setDirty(true);
  };

  // v6_dorp_walk_to_building_001 — start "loop"-animatie van speler naar gebouw, daarna trade-bark
  const walkToBuilding = (building) => {
    if (editMode || walking) return;
    const [bx, by] = building.pos;
    setWalking(true);
    setPlayerPos({ x: bx, y: by });
    // 1.6s loop-animatie → daarna bark openen
    setTimeout(() => {
      setWalking(false);
      setTradeBark({ building });
    }, 1600);
  };

  const closeTradeBark = () => setTradeBark(null);

  // Resolve each building to a card from gameCards
  // v6_dnd_card_lookup_002 — altijd lookup; placeholder is dynamic afhankelijk van
  // of we een matching kaart vinden (niet meer een statische flag).
  const buildings = BUILDING_LAYOUT.map(b => {
    const card = findCardFor(b.keywords, gameCards);
    const img = card?.media?.image_urls?.[0] ? `${API}${card.media.image_urls[0]}` : null;
    const override = overrides[b.id];
    const pos = override ? [override.x, override.y] : b.pos;
    return { ...b, card, img, pos, hasOverride: !!override, placeholder: !card && !b.central };
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4" onClick={onClose}>
      <div data-testid="stormhaven-map-view"
        className="relative bg-stone-950 border-2 border-amber-600/60 rounded-xl w-full max-w-5xl max-h-[95vh] flex flex-col"
        onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b-2 border-amber-900/40 bg-gradient-to-r from-amber-950/40 to-stone-950">
          <div className="flex items-center gap-3">
            <div className="w-10 h-12 rounded border border-amber-600/60 bg-gradient-to-b from-amber-900/40 to-purple-900/30 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-[0.25em] text-amber-500/70">Hoofdstad — Fractie {displayFractie}</p>
              <h2 className="text-2xl font-serif font-bold text-amber-100">{displayNaam}</h2>
              <p className="text-[11px] text-amber-300/70 italic">Layout: Level {char?.dorp_level ?? 1} · Fog of War: {char?.fog_of_war_pct ?? 0}%</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isAdmin && (
              <>
                <button
                  data-testid="stormhaven-edit-toggle"
                  onClick={() => setEditMode(v => !v)}
                  title={editMode ? 'Bewerken uit' : 'Bewerken aan — sleep gebouwen naar nieuwe positie'}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider border transition-colors ${
                    editMode
                      ? 'border-emerald-500/70 bg-emerald-900/40 text-emerald-200 hover:bg-emerald-900/60'
                      : 'border-amber-700/60 bg-stone-900 text-amber-300 hover:bg-amber-900/30'
                  }`}>
                  {editMode ? <Move className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
                  {editMode ? 'Bewerken AAN' : 'Bewerken'}
                </button>
                {editMode && dirty && (
                  <button
                    data-testid="stormhaven-save-layout"
                    onClick={saveOverrides}
                    disabled={saving}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider border border-amber-500 bg-amber-600 text-stone-950 hover:bg-amber-500 disabled:opacity-50">
                    <Save className="w-3.5 h-3.5" />
                    {saving ? 'Opslaan…' : 'Opslaan'}
                  </button>
                )}
              </>
            )}
            <button data-testid="stormhaven-close-btn" onClick={onClose}
              className="w-9 h-9 rounded-full bg-stone-900 hover:bg-amber-900/30 text-amber-300 flex items-center justify-center border border-amber-900/40">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Map area */}
        <div className="relative flex-1 overflow-hidden bg-stone-950">
          <div ref={mapRef} className="relative w-full" style={{ paddingBottom: '70%' }}>
            <div className="absolute inset-0">
              {dorpImg ? (
                <img src={dorpImg} alt={`${displayNaam} plattegrond`}
                  className="absolute inset-0 w-full h-full object-contain" draggable={false} />
              ) : (
                <div className="absolute inset-0 bg-gradient-to-b from-stone-800 to-stone-950 flex items-center justify-center text-amber-400/40 italic">
                  Geen dorpskaart geüpload — maak een D&amp;D-kaart &ldquo;Basis dorp&rdquo;
                </div>
              )}
              {/* Vignet voor leesbaarheid */}
              <div className="absolute inset-0 pointer-events-none"
                style={{ background: 'radial-gradient(circle at center, transparent 30%, rgba(0,0,0,0.55) 95%)' }} />

              {/* Building hotspots */}
              {buildings.map(b => (
                <BuildingHotspot key={b.id} building={b}
                  onClick={() => walkToBuilding(b)}
                  active={tradeBark?.building?.id === b.id}
                  editMode={editMode}
                  mapRef={mapRef}
                  onMove={(x, y) => updateOverride(b.id, x, y)}
                  onReset={() => resetOverride(b.id)} />
              ))}

              {/* v6_player_glow_001 — Speler-avatar met groene puls op centrum (default) */}
              <PlayerOnMap char={char} pos={playerPos} walking={walking} />

              {/* Trade-bark modal voor aangeklikt gebouw */}
              {tradeBark && (
                <BuildingTradeBark
                  building={tradeBark.building}
                  char={char}
                  onClose={closeTradeBark} />
              )}
            </div>
          </div>
        </div>

        {/* Footer — building grid summary */}
        <div className="px-5 py-2.5 border-t border-amber-900/40 bg-stone-950/80">
          <p className="text-[10px] uppercase tracking-[0.2em] text-amber-500/70 mb-1.5">Gebouwen in deze laag · {buildings.filter(b => b.card).length}/{buildings.length}</p>
          <div className="flex flex-wrap gap-1.5">
            {buildings.map(b => (
              <button key={b.id} data-testid={`building-chip-${b.id}`}
                onClick={() => walkToBuilding(b)}
                disabled={editMode || walking}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] border ${
                  b.card ? 'border-amber-700/60 text-amber-200 bg-amber-950/30 hover:bg-amber-900/40'
                         : 'border-stone-700 text-stone-500 bg-stone-900/40 italic'} ${(editMode || walking) ? 'opacity-50 cursor-not-allowed' : ''}`}>
                {b.img ? (
                  <img src={b.img} alt="" className="w-4 h-4 rounded-sm object-cover" />
                ) : b.central ? (
                  <Sparkles className="w-3 h-3 text-amber-400" />
                ) : (
                  <Plus className="w-3 h-3" />
                )}
                {b.label}
              </button>
            ))}
          </div>
          <p className="text-[10px] text-amber-400/60 italic mt-2">
            💡 Tip: maak een D&amp;D-kaart met begrip &ldquo;Tempel&rdquo; of &ldquo;Markt&rdquo; om deze plekken in te kleuren. Later wordt dit een aankleed-bare map zoals Zuid-Nederland.
          </p>
        </div>
      </div>
    </div>
  );
}

function BuildingHotspot({ building, onClick, active, editMode = false, mapRef = null, onMove = null, onReset = null }) {
  const [x, y] = building.pos;
  const size = building.central ? 64 : 44;
  const filled = !!building.card;
  const [dragging, setDragging] = useState(false);

  const startDrag = (e) => {
    if (!editMode || !mapRef?.current) return;
    e.preventDefault();
    e.stopPropagation();
    setDragging(true);
    const rect = mapRef.current.getBoundingClientRect();
    const move = (ev) => {
      const cx = (ev.touches ? ev.touches[0].clientX : ev.clientX);
      const cy = (ev.touches ? ev.touches[0].clientY : ev.clientY);
      const px = Math.max(0, Math.min(100, ((cx - rect.left) / rect.width) * 100));
      const py = Math.max(0, Math.min(100, ((cy - rect.top) / rect.height) * 100));
      onMove?.(px, py);
    };
    const stop = () => {
      setDragging(false);
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', stop);
      window.removeEventListener('touchmove', move);
      window.removeEventListener('touchend', stop);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', stop);
    window.addEventListener('touchmove', move, { passive: false });
    window.addEventListener('touchend', stop);
  };

  return (
    <button
      data-testid={`hotspot-${building.id}`}
      onClick={editMode ? (e) => { e.preventDefault(); } : onClick}
      onMouseDown={startDrag}
      onTouchStart={startDrag}
      onDoubleClick={editMode ? (e) => { e.stopPropagation(); onReset?.(); } : undefined}
      title={editMode ? `${building.label} — sleep om te verplaatsen (dubbelklik = reset)` : building.label}
      style={{
        left: `${x}%`, top: `${y}%`,
        width: size, height: size,
        transform: 'translate(-50%, -50%)',
        cursor: editMode ? (dragging ? 'grabbing' : 'grab') : 'pointer',
      }}
      className={`absolute rounded-full overflow-hidden border-2 transition-all duration-200 ${
        active ? 'ring-4 ring-amber-300/60 scale-110' : (editMode ? '' : 'hover:scale-110')
      } ${
        editMode
          ? (building.hasOverride ? 'border-emerald-400 shadow-[0_0_16px_rgba(52,211,153,0.6)]' : 'border-sky-400 shadow-[0_0_12px_rgba(56,189,248,0.5)]')
          : building.central
            ? 'border-amber-300 shadow-[0_0_24px_rgba(245,158,11,0.6)]'
            : filled
              ? 'border-amber-500/80 shadow-[0_0_12px_rgba(245,158,11,0.4)]'
              : 'border-amber-700/40 bg-stone-900/70 border-dashed'
      }`}>
      {building.img ? (
        <img src={building.img} alt={building.label} className="w-full h-full object-cover" />
      ) : building.central ? (
        <div className="w-full h-full bg-gradient-to-br from-amber-700 via-amber-500 to-yellow-300 flex items-center justify-center">
          <Sparkles className="w-7 h-7 text-stone-950" />
        </div>
      ) : (
        <div className="w-full h-full flex items-center justify-center">
          <Plus className="w-4 h-4 text-amber-300/60" />
        </div>
      )}
      {/* Label */}
      <span className="absolute left-1/2 -translate-x-1/2 mt-1 text-[9px] font-serif font-bold uppercase tracking-wider text-amber-100 whitespace-nowrap"
        style={{
          top: `100%`,
          textShadow: '0 1px 4px rgba(0,0,0,0.9), 0 0 8px rgba(0,0,0,0.7)',
        }}>
        {building.label}
      </span>
    </button>
  );
}

// v6_trade_bark_002 — 2-paneel trade bark (Jij + NPC) op basis van dnd_trade_bark_spec.
// NPC-avatar mapping: archief-foto's voor bakker/slager/jager/tempel; rest = ?-placeholder.
const NPC_IMAGES = {
  bakker:          '4e8404edfcbf',  // Bakker Persoon.png
  slager:          '053982d483e4',  // De Slager.png
  jachthut:        'e82426dc658d',  // icoon jager.png
  tempel_spark:    '13ccbbf4fccf',  // Spark logo
};

const NPC_NAMES = {
  smederij:       'Smid',
  jachthut:       'Jager',
  kruidenwinkel:  'Kruidenkundige',
  houthakkerij:   'Houthakker',
  mijn:           'Mijner',
  haven:          'Havenmeester',
  waterput:       'Waterhaler',
  akker:          'Boer',
  stadsbank:      'Bankier',
  bakker:         'Bakker',
  slager:         'Slager',
  trader_post:    'Karavaanleider',
  auctionhouse:   'Veilingmeester',
  kazerne:        'Kapitein',
  herberg:        'Waard',
  tempel_spark:   'Tempelwachter',
  markt:          'Markt-NPC',
  huis_t1:        'Bewoner',
  wachterspost:   'Wachter',
  gemeentehuis:   'Stadsleider',
  warehouse:      'Magazijnmeester',
  stadsmuur:      'Muurwachter',
  stadspoort:     'Poortwachter',
  riool_o:        '???',
  riool_w:        '???',
  poort_n:        'Poortwachter',
  poort_o:        'Poortwachter',
  poort_z:        'Poortwachter',
  poort_w:        'Poortwachter',
  muur_n:         'Muurwachter',
  muur_o:         'Muurwachter',
  muur_z:         'Muurwachter',
  muur_w:         'Muurwachter',
};

// Mock-rugzak items om de trade-UI te demonstreren. Echte rugzak komt straks uit /api/inventory.
const MOCK_TRADER_INVENTORY = {
  bakker:        [{ id: 'brood', naam: 'Brood', price: 6, icon: '🍞' }, { id: 'koekje', naam: 'Koekje', price: 3, icon: '🍪' }],
  slager:        [{ id: 'vlees', naam: 'Vlees', price: 8, icon: '🥩' }, { id: 'worst', naam: 'Worst', price: 12, icon: '🌭' }],
  smederij:      [{ id: 'zwaard', naam: 'Handzwaard', price: 150, icon: '⚔️' }, { id: 'schild', naam: 'Schild', price: 100, icon: '🛡️' }],
  kruidenwinkel: [{ id: 'kruid', naam: 'Helende kruiden', price: 15, icon: '🌿' }, { id: 'potion', naam: 'Healing Potion', price: 40, icon: '🧪' }],
  herberg:       [{ id: 'kamer', naam: 'Kamer/nacht', price: 2, icon: '🛏️' }, { id: 'maaltijd', naam: 'Maaltijd', price: 4, icon: '🍲' }],
  markt:         [{ id: 'appel', naam: 'Appel', price: 4, icon: '🍎' }, { id: 'vis', naam: 'Vis', price: 5, icon: '🐟' }, { id: 'kaas', naam: 'Kaas', price: 7, icon: '🧀' }],
  haven:         [{ id: 'vis', naam: 'Verse vis', price: 5, icon: '🐟' }],
  akker:         [{ id: 'graan', naam: 'Graan', price: 3, icon: '🌾' }, { id: 'appel', naam: 'Appel', price: 4, icon: '🍎' }],
};


function BuildingTradeBark({ building, char, onClose }) {
  const userId = char?.user_id;
  const [userAvatar, setUserAvatar] = React.useState(null);
  const [verkopen, setVerkopen] = React.useState([]);  // jouw items te verkopen
  const [kopen, setKopen] = React.useState([]);        // trader items te kopen

  React.useEffect(() => {
    if (!userId) return;
    fetch(`${API}/api/avatar/current/${userId}`)
      .then(r => r.json())
      .then(d => setUserAvatar(d.url ? `${API}${d.url}` : null))
      .catch(() => {});
  }, [userId]);

  const npcImgId = NPC_IMAGES[building.id];
  const npcImg = npcImgId ? `${API}/api/system-archive/file/${npcImgId}` : null;
  const npcNaam = NPC_NAMES[building.id] || building.label;
  const traderInv = MOCK_TRADER_INVENTORY[building.id] || [];

  // Mock-rugzak (later: uit /api/inventory). Voor nu: stub items voor demo.
  const userInv = [
    { id: 'goud-pouch', naam: 'Goud-pouch', price: 0, icon: '💰' },
    { id: 'hp-potion', naam: 'HP-Potion (oud)', price: 5, icon: '🧪' },
  ];

  const TAX_PCT = 5;
  const sumKopen = kopen.reduce((a, b) => a + b.price, 0);
  const sumVerkopen = verkopen.reduce((a, b) => a + b.price, 0);
  const tax = Math.round((sumKopen * TAX_PCT) / 100);
  const netto = sumVerkopen - sumKopen - tax;

  const toggle = (list, setter, item) => {
    setter(list.find(x => x.id === item.id) ? list.filter(x => x.id !== item.id) : [...list, item]);
  };

  return (
    <div
      data-testid="building-trade-bark"
      className="absolute inset-0 flex items-center justify-center bg-black/70 backdrop-blur-sm z-30"
      onClick={onClose}>
      <div
        className="relative bg-stone-950 border-2 border-amber-500/70 rounded-xl w-[min(96%,720px)] shadow-[0_0_40px_rgba(245,158,11,0.4)] overflow-hidden flex flex-col max-h-[88%]"
        onClick={e => e.stopPropagation()}>

        {/* Header met 2 avatar-kaders */}
        <div className="flex items-stretch border-b border-amber-900/40 bg-gradient-to-r from-amber-950/60 to-stone-950">
          <TraderAvatar
            label="Jij"
            naam={char?.titel || 'Speler'}
            sub={`${char?.currency?.goud ?? 0} g`}
            img={userAvatar}
            accent="emerald" />
          <div className="flex items-center justify-center px-3 text-amber-500/70 font-serif text-xl">↔</div>
          <TraderAvatar
            label="Locatie · NPC"
            naam={npcNaam}
            sub={building.label}
            img={npcImg}
            accent="amber" />
          <button data-testid="trade-bark-close" onClick={onClose}
            className="self-start mt-2 mr-2 w-8 h-8 rounded-full bg-stone-900 hover:bg-amber-900/30 text-amber-300 flex items-center justify-center border border-amber-900/40 flex-shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 2 kolommen inventaris */}
        <div className="grid grid-cols-2 gap-0 flex-1 overflow-hidden">
          <InventoryPanel
            title="Jouw rugzak"
            subtitle="Klik items om te verkopen"
            items={userInv}
            selected={verkopen}
            onToggle={item => toggle(verkopen, setVerkopen, item)}
            accent="emerald" />
          <InventoryPanel
            title={`${npcNaam} · inboedel`}
            subtitle="Klik items om te kopen"
            items={traderInv}
            selected={kopen}
            onToggle={item => toggle(kopen, setKopen, item)}
            accent="amber" />
        </div>

        {/* Footer met berekening */}
        <div className="border-t border-amber-900/40 bg-stone-950/80 p-3">
          <div className="grid grid-cols-3 gap-2 text-[11px] font-mono mb-2">
            <div className="text-emerald-300/90">Verkoop <span className="float-right text-amber-100">+{sumVerkopen}g</span></div>
            <div className="text-amber-300/90">Koop <span className="float-right text-amber-100">−{sumKopen}g</span></div>
            <div className="text-rose-300/80">Tax ({TAX_PCT}%) <span className="float-right text-amber-100">−{tax}g</span></div>
          </div>
          <div className="flex items-center justify-between border-t border-amber-900/40 pt-2">
            <span className="text-[11px] uppercase tracking-wider text-amber-400/80">Netto</span>
            <span className={`font-mono font-bold text-base ${netto >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
              {netto >= 0 ? '+' : ''}{netto} g
            </span>
          </div>
          <button
            data-testid="trade-bark-accept"
            disabled
            className="mt-3 w-full px-3 py-2 rounded-md border border-amber-500/40 bg-stone-900 text-amber-400/60 text-xs uppercase tracking-wider font-bold cursor-not-allowed">
            Aanbod accepteren (binnenkort — Trader-AI koppeling)
          </button>
        </div>
      </div>
    </div>
  );
}


function TraderAvatar({ label, naam, sub, img, accent }) {
  const ring = accent === 'emerald' ? 'border-emerald-500/70 shadow-[0_0_16px_rgba(52,211,153,0.4)]' : 'border-amber-500/70 shadow-[0_0_16px_rgba(245,158,11,0.4)]';
  const labelClr = accent === 'emerald' ? 'text-emerald-300/80' : 'text-amber-300/80';
  return (
    <div className="flex-1 flex items-center gap-3 p-3">
      <div className={`w-16 h-16 rounded-lg overflow-hidden border-2 ${ring} bg-stone-900 flex-shrink-0 flex items-center justify-center`}>
        {img ? (
          <img src={img} alt="" className="w-full h-full object-cover" />
        ) : (
          <span className="text-3xl font-serif font-bold text-amber-400/60">?</span>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className={`text-[9px] uppercase tracking-[0.25em] ${labelClr}`}>{label}</p>
        <h4 className="text-sm font-serif font-bold text-amber-100 leading-tight truncate">{naam}</h4>
        <p className="text-[10px] text-amber-400/70 italic truncate">{sub}</p>
      </div>
    </div>
  );
}


function InventoryPanel({ title, subtitle, items, selected, onToggle, accent }) {
  const isSel = id => selected.some(s => s.id === id);
  const selRing = accent === 'emerald'
    ? 'border-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.5)] bg-emerald-950/40'
    : 'border-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.5)] bg-amber-950/40';
  return (
    <div className="p-3 overflow-y-auto" style={{ borderLeft: accent === 'amber' ? '1px solid rgba(146,64,14,0.4)' : 'none' }}>
      <p className="text-[9px] uppercase tracking-[0.2em] text-amber-400/70">{title}</p>
      <p className="text-[10px] text-amber-300/60 italic mb-2">{subtitle}</p>
      {items.length === 0 ? (
        <p className="text-[11px] text-stone-500 italic">Geen items beschikbaar.</p>
      ) : (
        <div className="space-y-1.5">
          {items.map(it => (
            <button key={it.id}
              data-testid={`trade-item-${it.id}`}
              onClick={() => onToggle(it)}
              className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md border text-left transition-all text-[11px] ${
                isSel(it.id) ? selRing : 'border-stone-700 bg-stone-900/40 hover:bg-stone-800/60 text-amber-200/90'
              }`}>
              <span className="text-base">{it.icon}</span>
              <span className="flex-1 truncate">{it.naam}</span>
              <span className="font-mono text-amber-100">{it.price}g</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// v6_player_glow_001 — Speler-avatar met groene puls-glow op de dorpskaart
// v6_dorp_walk_to_building_001 — pos kan dynamisch zijn; tijdens "walking" smooth CSS-transition.
function PlayerOnMap({ char, pos, walking = false }) {
  const userId = char?.user_id;
  const [avatarUrl, setAvatarUrl] = useState(null);
  React.useEffect(() => {
    if (!userId) return;
    fetch(`${API}/api/avatar/current/${userId}`)
      .then(r => r.json())
      .then(d => setAvatarUrl(d.url ? `${API}${d.url}` : null))
      .catch(() => {});
  }, [userId]);
  const px = pos?.x ?? char?.player_x_pct ?? 53;
  const py = pos?.y ?? char?.player_y_pct ?? 53;
  return (
    <div
      data-testid="player-on-map"
      title={`${char?.titel || 'Speler'} — ${walking ? 'Onderweg…' : 'Jij bent hier'}`}
      className="absolute"
      style={{
        left: `${px}%`,
        top: `${py}%`,
        transform: 'translate(-50%, -50%)',
        zIndex: 20,
        transition: 'left 1.5s ease-in-out, top 1.5s ease-in-out',
      }}>
      <div className="relative">
        {/* Pulse-ring */}
        <div className="absolute -inset-2 rounded-full"
          style={{
            background: walking
              ? 'radial-gradient(circle, rgba(56,189,248,0.7) 0%, rgba(56,189,248,0) 70%)'
              : 'radial-gradient(circle, rgba(34,197,94,0.55) 0%, rgba(34,197,94,0) 70%)',
            animation: `spark-player-pulse ${walking ? '0.8s' : '1.8s'} ease-in-out infinite`,
          }} />
        {/* Avatar circle */}
        <div className={`relative w-8 h-8 rounded-full overflow-hidden border-2 ${walking ? 'border-sky-300' : 'border-emerald-400'}`}
          style={{
            boxShadow: walking
              ? '0 0 12px rgba(56,189,248,0.95), 0 0 22px rgba(56,189,248,0.5)'
              : '0 0 10px rgba(34,197,94,0.9), 0 0 18px rgba(34,197,94,0.4)',
          }}>
          {avatarUrl ? (
            <img src={avatarUrl} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-emerald-900 flex items-center justify-center text-emerald-100 font-bold">
              {(char?.titel || '?').charAt(0)}
            </div>
          )}
        </div>
      </div>
      <style>{`
        @keyframes spark-player-pulse {
          0%, 100% { transform: scale(0.85); opacity: 0.5; }
          50%      { transform: scale(1.15); opacity: 0.9; }
        }
      `}</style>
    </div>
  );
}


export default StormhavenMapView;
