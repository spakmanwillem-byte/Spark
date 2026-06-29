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

export function StormhavenMapView({ dorpCard, gameCards, char, onClose, stadNaam, fractieNaam }) {
  // v6_dnd_stad_minimap_001 — labels nu dynamisch ipv hardcoded 'Stormhaven/Spark'
  const displayNaam = stadNaam || char?.dorp || dorpCard?.begrip || 'Onbekend';
  const displayFractie = fractieNaam || char?.fractie_naam || char?.fractie || 'Neutraal';
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
              <p className="text-[10px] uppercase tracking-[0.25em] text-amber-500/70">Hoofdstad — Fractie {displayFractie}</p>
              <h2 className="text-2xl font-serif font-bold text-amber-100">{displayNaam}</h2>
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
                <img src={dorpImg} alt={`${displayNaam} plattegrond`}
                  className="absolute inset-0 w-full h-full object-contain" />
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
                  onClick={() => setSelectedBuilding(b)}
                  active={selectedBuilding?.id === b.id} />
              ))}

              {/* v6_player_glow_001 — Speler-avatar met groene puls op centrum (default) */}
              <PlayerOnMap char={char} />

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
            💡 Tip: maak een D&amp;D-kaart met begrip &ldquo;Tempel&rdquo; of &ldquo;Markt&rdquo; om deze plekken in te kleuren. Later wordt dit een aankleed-bare map zoals Zuid-Nederland.
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

// v6_player_glow_001 — Speler-avatar met groene puls-glow op de dorpskaart
function PlayerOnMap({ char }) {
  const userId = char?.user_id;
  const [avatarUrl, setAvatarUrl] = useState(null);
  React.useEffect(() => {
    if (!userId) return;
    fetch(`${API}/api/avatar/current/${userId}`)
      .then(r => r.json())
      .then(d => setAvatarUrl(d.url ? `${API}${d.url}` : null))
      .catch(() => {});
  }, [userId]);
  // Default: centrum van het dorp (50%, 50%). Later: per gebouw waar speler is.
  const px = char?.player_x_pct ?? 50;
  const py = char?.player_y_pct ?? 50;
  return (
    <div
      data-testid="player-on-map"
      title={`${char?.titel || 'Speler'} — Jij bent hier`}
      className="absolute"
      style={{
        left: `${px}%`,
        top: `${py}%`,
        transform: 'translate(-50%, -50%)',
        zIndex: 20,
      }}>
      <div className="relative">
        {/* Pulse-ring */}
        <div className="absolute -inset-3 rounded-full"
          style={{
            background: 'radial-gradient(circle, rgba(34,197,94,0.55) 0%, rgba(34,197,94,0) 70%)',
            animation: 'spark-player-pulse 1.8s ease-in-out infinite',
          }} />
        {/* Avatar circle */}
        <div className="relative w-12 h-12 rounded-full overflow-hidden border-2 border-emerald-400"
          style={{ boxShadow: '0 0 12px rgba(34,197,94,0.9), 0 0 24px rgba(34,197,94,0.4)' }}>
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
