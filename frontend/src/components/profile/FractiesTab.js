/**
 * FractiesKaderPanel + LandkaartBark (v6_dnd_fracties_kader_001)
 *
 * Kader binnen de Avatar-tab (DnDCharacterSheet) in de bestaande Paper-stijl:
 *  border-amber-900/40, bg stone-950, uppercase serif header.
 *
 * Toont compact:
 *  - 10 fractie-rijen (banner-strip met kleur, naam, leider, 3 stats)
 *  - "Landkaart" knop → BarkModal met provincie-markers + steden
 *  - Klik fractie → fractie-detail-bark
 *  - Klik stad → stad-detail-bark
 *
 * Geen edit-flow. Data komt uit fracties.json + steden.json.
 */
import React, { useState, useEffect } from 'react';
import { Crown, Users, Building, Coins, Map, ChevronRight, Sparkles, X } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// v6_spark_world_kaart_btn_001 — eigen modal-wrapper (BarkModal is te smal voor kaart)
function MapModal({ title, onClose, maxWidth = 'max-w-3xl', children }) {
  return (
    <div
      data-testid="map-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className={`relative ${maxWidth} w-full max-h-[90vh] overflow-y-auto bg-stone-950 border-2 border-amber-900/40 rounded-lg shadow-2xl`}
        onClick={e => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 flex items-center justify-between px-3 py-2 bg-gradient-to-r from-amber-950/60 to-stone-950 border-b border-amber-900/40">
          <h2 className="text-xs uppercase tracking-[0.25em] text-amber-300 font-serif font-bold">{title}</h2>
          <button
            data-testid="map-modal-close"
            onClick={onClose}
            className="text-amber-300 hover:text-amber-100 p-1 rounded hover:bg-amber-900/30"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-3">{children}</div>
      </div>
    </div>
  );
}

// ============================================================
// PAPER STYLE HELPERS (zelfde look als DnDCharacterSheet)
// ============================================================
function PaperPanel({ children }) {
  return (
    <div
      className="rounded-lg border-2 border-amber-900/40 bg-gradient-to-b from-stone-950 to-stone-900 overflow-hidden"
      style={{ boxShadow: 'inset 0 0 24px rgba(0,0,0,0.5), 0 0 0 1px rgba(245,158,11,0.1)' }}>
      {children}
    </div>
  );
}

function PaperHeader({ children, right }) {
  return (
    <div className="px-3 py-1.5 border-b border-amber-900/40 bg-gradient-to-r from-amber-950/40 to-stone-950 flex items-center justify-between">
      <h3 className="text-[10px] uppercase tracking-[0.25em] text-amber-300 font-serif font-bold">{children}</h3>
      {right}
    </div>
  );
}

// ============================================================
// MAIN PANEL — tabs-stijl zoals CharInfo (horizontaal, fractie per tab)
// ============================================================
export function FractiesKaderPanel() {
  const [fracties, setFracties] = useState([]);
  const [steden, setSteden] = useState([]);
  const [provincies, setProvincies] = useState([]);
  const [activeFid, setActiveFid] = useState('spark');
  const [openStad, setOpenStad] = useState(null);
  const [openLandkaart, setOpenLandkaart] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/dnd/world/fracties/full`).then(r => r.json()),
      fetch(`${API}/api/dnd/world/steden`).then(r => r.json()),
    ])
      .then(([f, s]) => {
        setFracties(f.fracties || []);
        setSteden(s.steden || []);
        setProvincies(s.provincies || []);
      });
  }, []);

  const active = fracties.find(f => f.id === activeFid) || fracties[0];
  const activeColor = active?.kleur || '#94a3b8';
  const stedenVanFractie = steden.filter(s => s.leidende_fractie_id === activeFid);

  return (
    <PaperPanel>
      {/* Tab-rij: 10 fracties als horizontale tabs (kleur-strip onder) */}
      <div className="flex border-b border-amber-900/40 overflow-x-auto">
        {fracties.map(f => {
          const a = f.id === activeFid;
          const color = f.kleur || '#94a3b8';
          return (
            <button
              key={f.id}
              data-testid={`fractie-tab-${f.id}`}
              onClick={() => setActiveFid(f.id)}
              className={`flex-shrink-0 px-2.5 py-1.5 text-[10px] uppercase tracking-wider transition-colors relative ${
                a ? 'text-amber-100 bg-amber-900/20' : 'text-amber-500/60 hover:text-amber-300'
              }`}
              title={f.naam}
            >
              {f.naam}
              {a && (
                <span
                  className="absolute bottom-0 left-0 right-0 h-[2px]"
                  style={{ background: color }}
                />
              )}
            </button>
          );
        })}
        {/* Landkaart-knop rechts */}
        <button
          data-testid="fracties-open-landkaart-btn"
          onClick={() => setOpenLandkaart(true)}
          className="ml-auto flex-shrink-0 flex items-center gap-1 px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-amber-300 hover:text-amber-100 hover:bg-amber-900/20 border-l border-amber-900/40 transition-colors"
        >
          <Map className="w-3 h-3" />
          Landkaart
        </button>
      </div>

      {/* Content — actieve fractie */}
      {active && (
        <div className="p-3 text-[11px] text-amber-100/90 leading-relaxed min-h-[180px]">
          {/* Header: banner-strip met naam, tagline, leider, kleur-icoon */}
          <div
            className="flex items-center gap-3 mb-3 p-2 rounded border-2"
            style={{
              background: `linear-gradient(90deg, ${activeColor}30, ${activeColor}05)`,
              borderColor: `${activeColor}50`,
            }}
          >
            <div
              className="w-10 h-10 rounded flex items-center justify-center text-lg font-bold flex-shrink-0"
              style={{ background: activeColor, color: '#0f172a' }}
            >
              {active.icon_image_url ? (
                <img src={`${API}${active.icon_image_url}`} alt="" className="w-full h-full object-cover rounded" />
              ) : active.naam[0]}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-bold text-amber-100 font-serif">{active.naam}</div>
              {active.tagline && (
                <div className="text-[10px] italic text-amber-300/70 truncate">{active.tagline}</div>
              )}
            </div>
          </div>

          {/* Intro */}
          {active.introductie ? (
            <p className="text-[11px] text-amber-100/85 mb-3 italic">{active.introductie}</p>
          ) : (
            <p className="text-[11px] italic text-amber-400/40 mb-3">Geen introductie ingevuld in fracties.json</p>
          )}

          {/* Stats-rij (horizontaal) */}
          <div className="grid grid-cols-4 gap-1.5 mb-3">
            <MiniStat icon={Crown} label="Leider" value={active.leider_naam || active.leider || '—'} accent={activeColor} />
            <MiniStat icon={Users} label="Aanhangers" value={active.stats?.aanhangers_total ?? 0} accent={activeColor} />
            <MiniStat icon={Building} label="Steden" value={stedenVanFractie.length} accent={activeColor} />
            <MiniStat icon={Coins} label="Goud" value={active.stats?.goud ?? 0} accent={activeColor} />
          </div>

          {/* Stads-bonus + leidende steden naast elkaar */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {/* Bonus */}
            {active.stads_bonus?.beschrijving ? (
              <div className="p-2 rounded border" style={{ borderColor: `${activeColor}40`, background: `${activeColor}10` }}>
                <div className="flex items-center gap-1 mb-1">
                  <Sparkles className="w-3 h-3" style={{ color: activeColor }} />
                  <span className="text-[9px] font-bold uppercase tracking-wider" style={{ color: activeColor }}>Stads-bonus</span>
                </div>
                <p className="text-[11px] text-amber-100/85">{active.stads_bonus.beschrijving}</p>
              </div>
            ) : (
              <div className="p-2 rounded border border-stone-800 bg-stone-950/30">
                <span className="text-[9px] font-bold uppercase tracking-wider text-stone-500">Stads-bonus</span>
                <p className="text-[11px] italic text-stone-600 mt-1">Niet ingesteld</p>
              </div>
            )}

            {/* Leidende steden */}
            <div className="p-2 rounded border border-stone-800 bg-stone-950/30">
              <div className="text-[9px] font-bold uppercase tracking-wider text-amber-300/70 mb-1">
                Leidende steden ({stedenVanFractie.length})
              </div>
              {stedenVanFractie.length === 0 ? (
                <p className="text-[11px] italic text-stone-600">Geen.</p>
              ) : (
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {stedenVanFractie.map(s => (
                    <button
                      key={s.id}
                      data-testid={`leidende-stad-${s.id}`}
                      onClick={() => setOpenStad(s)}
                      className="w-full text-left px-1.5 py-1 rounded bg-stone-900/40 hover:bg-stone-900/80 border border-stone-800 hover:border-stone-700 transition-colors flex items-center justify-between"
                    >
                      <div className="min-w-0">
                        <div className="text-[11px] font-bold text-amber-100 truncate">{s.naam}</div>
                        <div className="text-[9px] text-stone-500 truncate">{s.provincie_naam}</div>
                      </div>
                      <ChevronRight className="w-3 h-3 text-stone-600 flex-shrink-0" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modals */}
      {openStad && (
        <StadDetailBark stadId={openStad.id} onClose={() => setOpenStad(null)} />
      )}
      {openLandkaart && (
        <LandkaartBark
          provincies={provincies}
          steden={steden}
          fracties={fracties}
          onClose={() => setOpenLandkaart(false)}
          onOpenStad={(s) => { setOpenLandkaart(false); setOpenStad(s); }}
        />
      )}
    </PaperPanel>
  );
}

// ============================================================
// MINI STAT (4-stats grid blok)
// ============================================================
function MiniStat({ icon: Icon, label, value, accent }) {
  return (
    <div className="p-1.5 rounded border border-stone-800 bg-stone-950/40">
      <div className="flex items-center gap-1 mb-0.5">
        <Icon className="w-3 h-3" style={{ color: accent }} />
        <span className="text-[9px] text-stone-500 uppercase tracking-wider truncate">{label}</span>
      </div>
      <div className="text-xs font-bold text-stone-100 truncate">{value}</div>
    </div>
  );
}

// ============================================================
// STAD DETAIL BARK (bewoner-bark stijl: avatar links, info rechts)
// ============================================================
export function StadDetailBark({ stadId, onClose }) {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch(`${API}/api/dnd/world/steden/${stadId}`).then(r => r.json()).then(setData);
  }, [stadId]);

  if (!data?.stad) return <MapModal title="Laden..." onClose={onClose} maxWidth="max-w-2xl"><div /></MapModal>;
  const s = data.stad;
  const leid = data.leidende_fractie || {};
  const color = leid.kleur || '#94a3b8';

  return (
    <MapModal title={`${s.type.toUpperCase()} · ${s.naam.toUpperCase()}`} onClose={onClose} maxWidth="max-w-3xl">
      <div className="space-y-3">
        {/* Hoofd-blok: avatar (banner/logo of initiaal) + info — zoals BewonerHandelPanel */}
        <div className="flex gap-3 items-start">
          <div
            className="w-24 h-24 rounded-lg overflow-hidden border-2 flex-shrink-0 flex items-center justify-center text-4xl font-serif font-bold"
            style={{
              borderColor: `${color}80`,
              background: `linear-gradient(135deg, ${color}30, ${color}10)`,
              color: color,
              boxShadow: `0 0 16px ${color}40`,
            }}
          >
            {s.logo_url || s.banner_image_url ? (
              <img src={`${API}${s.logo_url || s.banner_image_url}`} alt={s.naam} className="w-full h-full object-cover" />
            ) : (
              s.naam[0]
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-base font-serif font-bold text-amber-100 leading-tight">{s.naam}</p>
            <p className="text-[10px] text-amber-400/70 capitalize">
              {s.type} · {s.provincie_id} · leidt: <span style={{ color }}>{leid.naam || '—'}</span>
            </p>
            <p className="text-[11px] text-yellow-300 font-mono mt-1">💰 {s.kas?.goud ?? 0}g · 👥 {Object.values(s.fractie_invloed || {}).reduce((a, b) => a + (b.aanhangers || 0), 0)} aanhangers</p>
            {s.introductie ? (
              <p className="text-[11px] italic text-amber-200/80 mt-1 leading-snug">&ldquo;{s.introductie}&rdquo;</p>
            ) : (
              <p className="text-[11px] italic text-amber-200/40 mt-1">&ldquo;(Geen introductie ingevuld)&rdquo;</p>
            )}
          </div>
        </div>

        {/* Stads-bonus (als beschikbaar) */}
        {s.leider_bonus?.beschrijving && (
          <div className="p-2.5 rounded border" style={{ borderColor: `${color}40`, background: `${color}10` }}>
            <div className="flex items-center gap-1.5 mb-1">
              <Sparkles className="w-3.5 h-3.5" style={{ color }} />
              <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color }}>Stads-bonus</span>
            </div>
            <p className="text-[11px] text-amber-100/85 italic">&ldquo;{s.leider_bonus.beschrijving}&rdquo;</p>
          </div>
        )}

        {/* Stadsfuncties als grid */}
        <div>
          <div className="text-[10px] font-bold uppercase tracking-wider text-amber-300/70 mb-1.5">Stadsfuncties</div>
          <div className="grid grid-cols-5 gap-1.5">
            {Object.entries(s.functies || {}).map(([key, f]) => (
              <div key={key} className={`p-1.5 rounded border text-center ${
                (f.niveau || 0) > 0 ? 'border-amber-900/40 bg-stone-900/60' : 'border-stone-900 bg-stone-950/30 opacity-40'
              }`}>
                <div className="text-[9px] uppercase text-amber-300/60 mb-0.5 truncate">{key}</div>
                <div className="text-base font-bold text-amber-100">{f.niveau || 0}</div>
                <div className="text-[8px] text-stone-600">niveau</div>
              </div>
            ))}
          </div>
        </div>

        {/* Fractie-ranking */}
        <div>
          <div className="text-[10px] font-bold uppercase tracking-wider text-amber-300/70 mb-1.5">Fractie-invloed (top 5)</div>
          <div className="space-y-1">
            {data.fractie_ranking.slice(0, 5).map(r => {
              const f = r.fractie || {};
              const inv = r.invloed || {};
              return (
                <div key={f.id} className="flex items-center gap-2 px-2 py-1 rounded bg-stone-950/40 border border-stone-800">
                  <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: f.kleur || '#94a3b8' }} />
                  <div className="flex-1 text-xs text-amber-100 truncate">{f.naam}</div>
                  <div className="text-[10px] text-amber-200/70 flex items-center gap-2 flex-shrink-0">
                    <span><Users className="w-3 h-3 inline mr-0.5 text-amber-400/60" />{inv.aanhangers ?? 0}</span>
                    <span><Building className="w-3 h-3 inline mr-0.5 text-amber-400/60" />{inv.gebouwen ?? 0}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </MapModal>
  );
}

// ============================================================
// LANDKAART BARK (NL provincie-map met dezelfde foto als MiniMap)
// ============================================================
const NL_MAP_URL = 'https://customer-assets.emergentagent.com/job_question-hub-160/artifacts/pkw3x971_Nederland%20map%20kaal.jpeg';

export function LandkaartBark({ provincies, steden, fracties, onClose, onOpenStad }) {
  const [selectedProv, setSelectedProv] = useState(null);
  const fractieById = Object.fromEntries(fracties.map(f => [f.id, f]));
  const stedenInProv = selectedProv ? steden.filter(s => s.provincie_id === selectedProv.id) : [];
  const heersFractie = selectedProv ? fractieById[selectedProv.fractie_id] : null;

  return (
    <MapModal title="LANDKAART · STORMHAVEN" onClose={onClose} maxWidth="max-w-5xl">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
        {/* LINKS: grote kaart (col-span 8) */}
        <div className="lg:col-span-8">
          <p className="text-[11px] text-amber-300/60 mb-1.5">
            Klik op een provincie om de steden te zien. De marker-kleur toont de leidende fractie.
          </p>
          <div className="relative aspect-[3/4] bg-stone-950 rounded-lg border-2 border-amber-900/40 overflow-hidden">
            <img src={NL_MAP_URL} alt="Nederland kaart" className="absolute inset-0 w-full h-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-br from-stone-900/20 to-stone-950/40" />
            {provincies.map(p => {
              const f = fractieById[p.fractie_id];
              const color = f?.kleur || '#94a3b8';
              const isSelected = selectedProv?.id === p.id;
              const x = p.x_pct ?? 50;
              const y = p.y_pct ?? 50;
              return (
                <button
                  key={p.id}
                  data-testid={`prov-marker-${p.id}`}
                  onClick={() => setSelectedProv(p)}
                  className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center group"
                  style={{ left: `${x}%`, top: `${y}%` }}
                  title={`${p.naam} — ${f?.naam || 'Neutraal'}`}
                >
                  <div
                    className={`w-4 h-4 rounded-full border-2 transition-all ${
                      isSelected ? 'scale-150 border-amber-200' : 'border-stone-900 group-hover:scale-125'
                    }`}
                    style={{ background: color, boxShadow: isSelected ? `0 0 12px ${color}` : '0 0 4px rgba(0,0,0,0.6)' }}
                  />
                  <span className={`text-[10px] mt-0.5 px-1 rounded whitespace-nowrap font-bold transition-all ${
                    isSelected
                      ? 'opacity-100 bg-stone-950 text-amber-200 shadow-lg'
                      : 'opacity-90 bg-stone-950/70 text-stone-100'
                  }`}>
                    {p.naam}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* RECHTS: info-paneel (col-span 4) */}
        <div className="lg:col-span-4 flex flex-col">
          {!selectedProv ? (
            // Leeg-staat: lijst van alle provincies met fractie
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-amber-300/70 mb-1.5">Provincies ({provincies.length})</div>
              <div className="space-y-1 max-h-[60vh] overflow-y-auto pr-1">
                {provincies.map(p => {
                  const f = fractieById[p.fractie_id];
                  return (
                    <button
                      key={p.id}
                      onClick={() => setSelectedProv(p)}
                      className="w-full text-left p-1.5 rounded bg-stone-900/40 hover:bg-stone-900 border border-stone-800 hover:border-amber-900/40 transition-colors flex items-center gap-2"
                    >
                      <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: f?.kleur || '#94a3b8' }} />
                      <div className="flex-1 min-w-0">
                        <div className="text-[11px] font-bold text-amber-100 truncate">{p.naam}</div>
                        <div className="text-[9px] text-amber-400/60 truncate">{f?.naam || '—'}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            // Geselecteerde provincie + steden
            <div className="space-y-2.5">
              <div
                className="p-2.5 rounded border-2"
                style={{
                  borderColor: `${heersFractie?.kleur || '#94a3b8'}60`,
                  background: `linear-gradient(135deg, ${heersFractie?.kleur || '#94a3b8'}20, transparent)`,
                }}
              >
                <div className="flex items-start justify-between mb-1">
                  <div>
                    <div className="text-[9px] uppercase tracking-wider text-amber-300/60">Provincie</div>
                    <div className="text-base font-bold text-amber-100 font-serif">{selectedProv.naam}</div>
                  </div>
                  <button
                    onClick={() => setSelectedProv(null)}
                    className="text-[9px] px-1.5 py-0.5 rounded border border-amber-700/40 text-amber-300/80 hover:bg-amber-900/30"
                  >
                    × terug
                  </button>
                </div>
                <div className="text-[10px] text-amber-200/80">
                  Heerst: <span className="font-bold" style={{ color: heersFractie?.kleur }}>{heersFractie?.naam || '—'}</span>
                </div>
              </div>

              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-amber-300/70 mb-1.5">
                  Steden ({stedenInProv.length})
                </div>
                <div className="space-y-1.5">
                  {stedenInProv.map(s => {
                    const leid = fractieById[s.leidende_fractie_id];
                    return (
                      <button
                        key={s.id}
                        data-testid={`landkaart-stad-${s.id}`}
                        onClick={() => onOpenStad(s)}
                        className="w-full text-left p-2 rounded bg-stone-900/50 hover:bg-stone-900 transition-colors flex items-center justify-between border border-stone-800 hover:border-amber-900/40"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: leid?.kleur || '#94a3b8' }} />
                          <div className="min-w-0">
                            <div className="text-[11px] font-bold text-amber-100 truncate">{s.naam}</div>
                            <div className="text-[9px] text-amber-400/60 uppercase">{s.type}</div>
                          </div>
                        </div>
                        <ChevronRight className="w-3.5 h-3.5 text-amber-400/60 flex-shrink-0" />
                      </button>
                    );
                  })}
                  {stedenInProv.length === 0 && (
                    <p className="text-[11px] italic text-amber-400/40">Geen steden in deze provincie.</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </MapModal>
  );
}
