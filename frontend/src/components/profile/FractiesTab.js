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
import { Crown, Users, Building, Coins, Map, ChevronRight, Sparkles } from 'lucide-react';
import { BarkModal } from '../shared/BarkModal';

const API = process.env.REACT_APP_BACKEND_URL;

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
// MAIN PANEL
// ============================================================
export function FractiesKaderPanel() {
  const [fracties, setFracties] = useState([]);
  const [steden, setSteden] = useState([]);
  const [provincies, setProvincies] = useState([]);
  const [openFractie, setOpenFractie] = useState(null);
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

  return (
    <PaperPanel>
      <PaperHeader right={
        <button
          data-testid="fracties-open-landkaart-btn"
          onClick={() => setOpenLandkaart(true)}
          className="flex items-center gap-1.5 px-2 py-0.5 rounded border border-amber-700/40 bg-amber-900/20 text-amber-300 hover:bg-amber-900/40 text-[10px] font-bold uppercase tracking-wider transition-colors"
        >
          <Map className="w-3 h-3" />
          Landkaart
        </button>
      }>FRACTIES · STORMHAVEN ({fracties.length})</PaperHeader>

      <div className="p-2 space-y-1.5">
        {fracties.map(f => (
          <FractieRij
            key={f.id}
            fractie={f}
            stedenCount={steden.filter(s => s.leidende_fractie_id === f.id).length}
            onClick={() => setOpenFractie(f)}
          />
        ))}
      </div>

      {/* Modals */}
      {openFractie && (
        <FractieDetailBark
          fractie={openFractie}
          steden={steden.filter(s => s.leidende_fractie_id === openFractie.id)}
          onClose={() => setOpenFractie(null)}
          onOpenStad={(s) => { setOpenFractie(null); setOpenStad(s); }}
        />
      )}
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
// FRACTIE RIJ (compact strip)
// ============================================================
function FractieRij({ fractie, stedenCount, onClick }) {
  const color = fractie.kleur || '#94a3b8';
  const stats = fractie.stats || {};
  return (
    <button
      data-testid={`fractie-rij-${fractie.id}`}
      onClick={onClick}
      className="w-full flex items-center gap-2 px-2 py-1.5 rounded border border-stone-800 bg-stone-900/40 hover:bg-stone-900/80 transition-colors text-left group"
    >
      {/* Kleur-strip + initiaal */}
      <div
        className="w-7 h-7 rounded-sm flex items-center justify-center text-xs font-bold flex-shrink-0"
        style={{ background: color, color: '#0f172a' }}
      >
        {fractie.icon_image_url ? (
          <img src={`${API}${fractie.icon_image_url}`} alt="" className="w-full h-full object-cover rounded-sm" />
        ) : fractie.naam[0]}
      </div>

      {/* Naam + leider */}
      <div className="flex-1 min-w-0">
        <div className="text-xs font-bold text-stone-100 truncate">{fractie.naam}</div>
        <div className="text-[10px] text-stone-500 truncate">
          {fractie.leider_naam || fractie.leider || '—'}
          {fractie.tagline && <span className="text-stone-600 italic"> · {fractie.tagline}</span>}
        </div>
      </div>

      {/* Stats grid */}
      <div className="flex items-center gap-2 text-[10px] text-stone-400">
        <span className="flex items-center gap-0.5" title="Aanhangers">
          <Users className="w-3 h-3 text-stone-500" />{stats.aanhangers_total ?? 0}
        </span>
        <span className="flex items-center gap-0.5" title="Leidende steden">
          <Building className="w-3 h-3 text-stone-500" />{stedenCount}
        </span>
        <span className="flex items-center gap-0.5" title="Goud">
          <Coins className="w-3 h-3 text-amber-500" />{stats.goud ?? 0}
        </span>
      </div>

      <ChevronRight className="w-3 h-3 text-stone-600 group-hover:text-stone-300 transition-colors flex-shrink-0" />
    </button>
  );
}

// ============================================================
// FRACTIE DETAIL BARK
// ============================================================
function FractieDetailBark({ fractie, steden, onClose, onOpenStad }) {
  const color = fractie.kleur || '#94a3b8';
  const stats = fractie.stats || {};
  const bonus = fractie.stads_bonus || {};

  return (
    <BarkModal isOpen={true} onClose={onClose} title="" maxWidth="max-w-2xl">
      <div className="space-y-3">
        {/* Banner */}
        <div
          className="h-20 rounded-lg flex items-center justify-between px-4 relative overflow-hidden border-2"
          style={{
            background: `linear-gradient(135deg, ${color}40, ${color}10)`,
            borderColor: `${color}60`,
          }}
        >
          {fractie.banner_image_url && (
            <img src={`${API}${fractie.banner_image_url}`} alt="" className="absolute inset-0 w-full h-full object-cover opacity-30" />
          )}
          <div className="relative z-10">
            <h2 className="text-xl font-bold text-white font-serif">{fractie.naam}</h2>
            {fractie.tagline && <p className="text-xs text-white/70 italic mt-0.5">{fractie.tagline}</p>}
          </div>
          <div
            className="relative z-10 w-12 h-12 rounded-lg flex items-center justify-center text-lg font-bold"
            style={{ background: color, color: '#0f172a' }}
          >
            {fractie.naam[0]}
          </div>
        </div>

        {/* Intro */}
        <div className="p-2.5 rounded border border-stone-800 bg-stone-950/40">
          <p className="text-xs text-stone-300 leading-relaxed">
            {fractie.introductie || <span className="italic text-stone-500">Geen introductie ingevuld in fracties.json</span>}
          </p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-4 gap-1.5">
          <MiniStat icon={Crown} label="Leider" value={fractie.leider_naam || fractie.leider || '—'} accent={color} />
          <MiniStat icon={Users} label="Aanhangers" value={stats.aanhangers_total ?? 0} accent={color} />
          <MiniStat icon={Building} label="Gebouwen" value={stats.gebouwen_total ?? 0} accent={color} />
          <MiniStat icon={Coins} label="Goud" value={stats.goud ?? 0} accent={color} />
        </div>

        {/* Stads-bonus */}
        {bonus.beschrijving && (
          <div className="p-2.5 rounded border" style={{ borderColor: `${color}40`, background: `${color}10` }}>
            <div className="flex items-center gap-1.5 mb-1">
              <Sparkles className="w-3.5 h-3.5" style={{ color }} />
              <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color }}>Stads-bonus</span>
            </div>
            <p className="text-xs text-stone-300">{bonus.beschrijving}</p>
          </div>
        )}

        {/* Leidende steden */}
        <div>
          <div className="text-[10px] font-bold uppercase tracking-wider text-amber-300/70 mb-1.5">
            Leidende steden ({steden.length})
          </div>
          {steden.length === 0 ? (
            <p className="text-xs italic text-stone-600">Geen steden waar deze fractie leidt.</p>
          ) : (
            <div className="grid grid-cols-2 gap-1.5">
              {steden.map(s => (
                <button
                  key={s.id}
                  data-testid={`leidende-stad-${s.id}`}
                  onClick={() => onOpenStad(s)}
                  className="text-left p-2 rounded border border-stone-800 bg-stone-900/40 hover:bg-stone-900/80 transition-colors flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-bold text-stone-100">{s.naam}</div>
                    <div className="text-[10px] text-stone-500">{s.provincie_naam} · {s.type}</div>
                  </div>
                  <ChevronRight className="w-3 h-3 text-stone-600" />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </BarkModal>
  );
}

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
// STAD DETAIL BARK
// ============================================================
function StadDetailBark({ stadId, onClose }) {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch(`${API}/api/dnd/world/steden/${stadId}`).then(r => r.json()).then(setData);
  }, [stadId]);

  if (!data?.stad) return <BarkModal isOpen={true} onClose={onClose} title="Laden..."><div /></BarkModal>;
  const s = data.stad;
  const leid = data.leidende_fractie || {};
  const color = leid.kleur || '#94a3b8';

  return (
    <BarkModal isOpen={true} onClose={onClose} title="" maxWidth="max-w-2xl">
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between border-b-2 border-amber-900/40 pb-2">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-stone-500">{s.type} · {s.provincie_id}</div>
            <h2 className="text-xl font-bold text-stone-100 font-serif mt-0.5">{s.naam}</h2>
          </div>
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-stone-500">Leidende fractie</div>
            <div className="text-sm font-bold" style={{ color }}>{leid.naam || '—'}</div>
          </div>
        </div>

        {s.introductie && (
          <div className="p-2.5 rounded border border-stone-800 bg-stone-950/40">
            <p className="text-xs text-stone-300 leading-relaxed">{s.introductie}</p>
          </div>
        )}

        {/* Kas + leider-bonus */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div className="p-2.5 rounded border border-amber-900/40 bg-amber-950/10">
            <div className="flex items-center gap-1.5 mb-1">
              <Coins className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-amber-300/80">Stadskas</span>
            </div>
            <div className="text-xl font-bold text-stone-100">{s.kas?.goud ?? 0}</div>
            <div className="text-[10px] text-stone-500">
              Tax {Math.round((s.kas?.tax_rate_inwoners ?? 0) * 100)}% inwoners · {Math.round((s.kas?.tax_rate_fracties ?? 0) * 100)}% fracties
            </div>
          </div>

          {s.leider_bonus?.beschrijving && (
            <div className="p-2.5 rounded border" style={{ borderColor: `${color}40`, background: `${color}10` }}>
              <div className="flex items-center gap-1.5 mb-1">
                <Sparkles className="w-3.5 h-3.5" style={{ color }} />
                <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color }}>Stads-bonus</span>
              </div>
              <p className="text-xs text-stone-300">{s.leider_bonus.beschrijving}</p>
            </div>
          )}
        </div>

        {/* Stadsfuncties */}
        <div>
          <div className="text-[10px] font-bold uppercase tracking-wider text-amber-300/70 mb-1.5">Stadsfuncties</div>
          <div className="grid grid-cols-5 gap-1.5">
            {Object.entries(s.functies || {}).map(([key, f]) => (
              <div key={key} className={`p-1.5 rounded border text-center ${
                (f.niveau || 0) > 0 ? 'border-amber-900/40 bg-stone-900/60' : 'border-stone-900 bg-stone-950/30 opacity-40'
              }`}>
                <div className="text-[9px] uppercase text-stone-500 mb-0.5 truncate">{key}</div>
                <div className="text-base font-bold text-stone-100">{f.niveau || 0}</div>
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
                  <div className="flex-1 text-xs text-stone-100 truncate">{f.naam}</div>
                  <div className="text-[10px] text-stone-400 flex items-center gap-2 flex-shrink-0">
                    <span><Users className="w-3 h-3 inline mr-0.5 text-stone-500" />{inv.aanhangers ?? 0}</span>
                    <span><Building className="w-3 h-3 inline mr-0.5 text-stone-500" />{inv.gebouwen ?? 0}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </BarkModal>
  );
}

// ============================================================
// LANDKAART BARK (NL provincie-map)
// ============================================================
function LandkaartBark({ provincies, steden, fracties, onClose, onOpenStad }) {
  const [selectedProv, setSelectedProv] = useState(null);
  const fractieById = Object.fromEntries(fracties.map(f => [f.id, f]));

  return (
    <BarkModal isOpen={true} onClose={onClose} title="Landkaart van Stormhaven" maxWidth="max-w-3xl">
      <div className="space-y-2">
        <p className="text-[11px] text-stone-400">
          Klik op een provincie om de steden te zien. De marker-kleur toont de leidende fractie.
        </p>

        <div className="relative aspect-[3/4] max-h-[55vh] bg-stone-950 rounded-lg border-2 border-amber-900/40 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-stone-800/40 to-stone-950/80" />
          {provincies.map(p => {
            const f = fractieById[p.fractie_id];
            const color = f?.kleur || '#94a3b8';
            const isSelected = selectedProv?.id === p.id;
            return (
              <button
                key={p.id}
                data-testid={`prov-marker-${p.id}`}
                onClick={() => setSelectedProv(p)}
                className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center group"
                style={{ left: `${p.x_pct}%`, top: `${p.y_pct}%` }}
                title={`${p.naam} — ${f?.naam || 'Neutraal'}`}
              >
                <div
                  className={`w-3.5 h-3.5 rounded-full border-2 transition-all ${
                    isSelected ? 'scale-150 border-amber-200' : 'border-stone-900 group-hover:scale-125'
                  }`}
                  style={{ background: color, boxShadow: isSelected ? `0 0 12px ${color}` : 'none' }}
                />
                <span className={`text-[9px] mt-0.5 px-1 rounded whitespace-nowrap transition-opacity ${
                  isSelected ? 'opacity-100 bg-stone-900 text-amber-200' : 'opacity-70 text-stone-400'
                }`}>
                  {p.naam}
                </span>
              </button>
            );
          })}
        </div>

        {selectedProv && (
          <div className="p-2.5 rounded border-2 border-amber-900/40 bg-stone-950/60">
            <div className="flex items-center justify-between mb-1.5">
              <div>
                <div className="text-[9px] uppercase tracking-wider text-stone-500">Provincie</div>
                <div className="text-sm font-bold text-stone-100">{selectedProv.naam}</div>
              </div>
              <div className="text-right">
                <div className="text-[9px] uppercase tracking-wider text-stone-500">Heerst</div>
                <div className="text-sm font-bold" style={{ color: fractieById[selectedProv.fractie_id]?.kleur }}>
                  {fractieById[selectedProv.fractie_id]?.naam || '—'}
                </div>
              </div>
            </div>
            <div className="space-y-1">
              {steden.filter(s => s.provincie_id === selectedProv.id).map(s => {
                const leid = fractieById[s.leidende_fractie_id];
                return (
                  <button
                    key={s.id}
                    data-testid={`landkaart-stad-${s.id}`}
                    onClick={() => onOpenStad(s)}
                    className="w-full text-left p-1.5 rounded bg-stone-900/50 hover:bg-stone-900 transition-colors flex items-center justify-between border border-stone-800"
                  >
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: leid?.kleur || '#94a3b8' }} />
                      <span className="text-xs text-stone-100">{s.naam}</span>
                      <span className="text-[9px] uppercase text-stone-500">{s.type}</span>
                    </div>
                    <ChevronRight className="w-3 h-3 text-stone-500" />
                  </button>
                );
              })}
              {steden.filter(s => s.provincie_id === selectedProv.id).length === 0 && (
                <p className="text-[11px] italic text-stone-600">Geen steden in deze provincie.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </BarkModal>
  );
}
