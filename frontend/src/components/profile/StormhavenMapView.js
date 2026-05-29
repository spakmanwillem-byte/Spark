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
import React, { useState } from 'react';
import { X, MapPin, Sparkles, Plus } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const BUILDING_LAYOUT = [
  { id: 'tempel',        pos: [50, 50], label: 'Tempel van Spark', keywords: ['tempel', 'spark'],            badge: 'CENTER',     central: true },
  { id: 'waterput-n',    pos: [50, 22], label: 'Waterput Noord',   keywords: ['waterput', 'water', 'put'] },
  { id: 'slager',        pos: [72, 32], label: 'Slager',           keywords: ['slager gebouw', 'slager'] },
  { id: 'markt',         pos: [78, 50], label: 'Markt',            keywords: ['markt', 'marktplaats'],       placeholder: true },
  { id: 'bakker',        pos: [72, 68], label: 'Bakker',           keywords: ['bakker gebouw', 'bakker'] },
  { id: 'waterput-z',    pos: [50, 78], label: 'Waterput Zuid',    keywords: ['waterput', 'water', 'put'] },
  { id: 'straat',        pos: [28, 68], label: 'Kleine straat',    keywords: ['kleine straat', 'straat'] },
  { id: 'smederij',      pos: [22, 50], label: 'Smederij',         keywords: ['smederij', 'smid'],           placeholder: true },
  { id: 'waterput-w',    pos: [28, 32], label: 'Waterput West',    keywords: ['waterput', 'water', 'put'] },
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

export function StormhavenMapView({ dorpCard, gameCards, char, onClose }) {
  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const dorpImg = dorpCard?.media?.image_urls?.[0] ? `${API}${dorpCard.media.image_urls[0]}` : null;

  // Resolve each building to a card from gameCards
  const buildings = BUILDING_LAYOUT.map(b => {
    const card = b.placeholder ? null : findCardFor(b.keywords, gameCards);
    const img = card?.media?.image_urls?.[0] ? `${API}${card.media.image_urls[0]}` : null;
    return { ...b, card, img };
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
              <p className="text-[10px] uppercase tracking-[0.25em] text-amber-500/70">Hoofdstad — Fractie Spark</p>
              <h2 className="text-2xl font-serif font-bold text-amber-100">Stormhaven</h2>
              <p className="text-[11px] text-amber-300/70 italic">Layout: Level {char?.dorp_level ?? 1} · Fog of War: {char?.fog_of_war_pct ?? 0}%</p>
            </div>
          </div>
          <button data-testid="stormhaven-close-btn" onClick={onClose}
            className="w-9 h-9 rounded-full bg-stone-900 hover:bg-amber-900/30 text-amber-300 flex items-center justify-center border border-amber-900/40">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Map area */}
        <div className="relative flex-1 overflow-hidden bg-stone-950">
          <div className="relative w-full" style={{ paddingBottom: '70%' }}>
            <div className="absolute inset-0">
              {dorpImg ? (
                <img src={dorpImg} alt="Stormhaven plattegrond"
                  className="absolute inset-0 w-full h-full object-contain" />
              ) : (
                <div className="absolute inset-0 bg-gradient-to-b from-stone-800 to-stone-950 flex items-center justify-center text-amber-400/40 italic">
                  Geen dorpskaart geüpload — maak een D&amp;D-kaart "Basis dorp"
                </div>
              )}
              {/* Vignet voor leesbaarheid */}
              <div className="absolute inset-0 pointer-events-none"
                style={{ background: 'radial-gradient(circle at center, transparent 30%, rgba(0,0,0,0.55) 95%)' }} />

              {/* Building hotspots */}
              {buildings.map(b => (
                <BuildingHotspot key={b.id} building={b}
                  onClick={() => setSelectedBuilding(b)}
                  active={selectedBuilding?.id === b.id} />
              ))}

              {/* Selected building tooltip */}
              {selectedBuilding && (
                <BuildingTooltip building={selectedBuilding} onClose={() => setSelectedBuilding(null)} />
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
                onClick={() => setSelectedBuilding(b)}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] border ${
                  b.card ? 'border-amber-700/60 text-amber-200 bg-amber-950/30 hover:bg-amber-900/40'
                         : 'border-stone-700 text-stone-500 bg-stone-900/40 italic'}`}>
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
            💡 Tip: maak een D&amp;D-kaart met begrip "Tempel" of "Markt" om deze plekken in te kleuren. Later wordt dit een aankleed-bare map zoals Zuid-Nederland.
          </p>
        </div>
      </div>
    </div>
  );
}

function BuildingHotspot({ building, onClick, active }) {
  const [x, y] = building.pos;
  const size = building.central ? 64 : 44;
  const filled = !!building.card;
  return (
    <button
      data-testid={`hotspot-${building.id}`}
      onClick={onClick}
      title={building.label}
      style={{
        left: `${x}%`, top: `${y}%`,
        width: size, height: size,
        transform: 'translate(-50%, -50%)',
      }}
      className={`absolute rounded-full overflow-hidden border-2 transition-all duration-200 ${
        active ? 'ring-4 ring-amber-300/60 scale-110' : 'hover:scale-110'
      } ${
        building.central
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

function BuildingTooltip({ building, onClose }) {
  return (
    <div data-testid="building-tooltip"
      className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-stone-950/95 border-2 border-amber-600/60 rounded-lg p-3 max-w-xs shadow-2xl backdrop-blur"
      onClick={e => e.stopPropagation()}>
      <div className="flex items-start gap-3">
        {building.img ? (
          <img src={building.img} alt="" className="w-16 h-16 rounded object-cover border border-amber-600/60 flex-shrink-0" />
        ) : (
          <div className="w-16 h-16 rounded border border-amber-700/40 bg-stone-900 flex items-center justify-center flex-shrink-0">
            {building.central ? <Sparkles className="w-7 h-7 text-amber-400" /> : <Plus className="w-7 h-7 text-amber-400/40" />}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-[9px] uppercase tracking-[0.2em] text-amber-500/70">
            {building.central ? 'Heilig Centrum' : building.placeholder ? 'Vacant — bouwen!' : 'Gebouw'}
          </p>
          <h4 className="text-sm font-serif font-bold text-amber-100">{building.label}</h4>
          {building.card ? (
            <p className="text-[11px] text-amber-200/80 italic mt-0.5">
              {building.card.lagen?.laag1 || building.card.begrip}
            </p>
          ) : (
            <p className="text-[10px] text-amber-400/60 italic mt-0.5">
              {building.placeholder
                ? `Maak een D&D-kaart "${building.label}" om hier in te vullen.`
                : 'Vacant'}
            </p>
          )}
        </div>
        <button onClick={onClose} className="text-amber-400/60 hover:text-amber-200">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default StormhavenMapView;
