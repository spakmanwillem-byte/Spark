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
import React, { useState, useEffect, useRef } from 'react';
import { Crown, Users, Building, Coins, Map, ChevronRight, Sparkles, X, Plus, Trash2, Upload, Copy, Pencil, Image as ImageIcon, Save, Link as LinkIcon } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// v6_spark_world_kaart_btn_001 — eigen modal-wrapper (BarkModal is te smal voor kaart)
function MapModal({ title, onClose, maxWidth = 'max-w-3xl', zIndex = 50, children }) {
  return (
    <div
      data-testid="map-modal"
      className="fixed inset-0 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
      style={{ zIndex }}
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
export function FractiesKaderPanel({ userId, isAdmin }) {
  const [fracties, setFracties] = useState([]);
  const [steden, setSteden] = useState([]);
  const [provincies, setProvincies] = useState([]);
  // v6_dnd_fracties_kader_001 — start op Spartanen (was 'spark', maar Spark = Spartanen-leider)
  const [activeFid, setActiveFid] = useState('neutraal');
  const [openStad, setOpenStad] = useState(null);
  const [openLandkaart, setOpenLandkaart] = useState(false);
  // v6_dnd_fractie_edit_001 — admin edit modal
  const [editingFid, setEditingFid] = useState(null);

  const reloadFracties = () => {
    fetch(`${API}/api/dnd/world/fracties/full`).then(r => r.json()).then(f => {
      setFracties(f.fracties || []);
    });
  };

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
          {/* v6_dnd_fractie_edit_001 — Banner (als beschikbaar) */}
          {active.banner_image_url && (
            <div className="relative mb-3 -mx-1 rounded overflow-hidden border-2" style={{ borderColor: `${activeColor}60` }}>
              <img
                src={`${API}${active.banner_image_url}`}
                alt={`${active.naam} banner`}
                className="w-full h-32 object-cover"
                data-testid={`fractie-banner-${active.id}`}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-stone-950/90 via-stone-950/30 to-transparent" />
              <div className="absolute bottom-1.5 left-2 right-2 flex items-end justify-between">
                <div className="min-w-0">
                  <div className="text-sm font-bold text-amber-100 font-serif drop-shadow-lg truncate">{active.naam}</div>
                  {active.tagline && (
                    <div className="text-[10px] italic text-amber-200/90 drop-shadow truncate">{active.tagline}</div>
                  )}
                </div>
                {isAdmin && (
                  <button
                    data-testid={`fractie-edit-btn-${active.id}`}
                    onClick={() => setEditingFid(active.id)}
                    className="flex-shrink-0 flex items-center gap-1 px-2 py-0.5 rounded bg-stone-950/80 border border-amber-700/60 text-amber-200 hover:bg-amber-900/40 text-[10px]"
                    title="Bewerk fractie-gegevens"
                  >
                    <Pencil className="w-3 h-3" />
                    Bewerk
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Header-strip (kleur + naam + leider) — alleen tonen als geen banner */}
          {!active.banner_image_url && (
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
              {isAdmin && (
                <button
                  data-testid={`fractie-edit-btn-${active.id}`}
                  onClick={() => setEditingFid(active.id)}
                  className="flex-shrink-0 flex items-center gap-1 px-2 py-1 rounded border border-amber-700/60 text-amber-200 hover:bg-amber-900/40 text-[10px]"
                  title="Bewerk fractie-gegevens"
                >
                  <Pencil className="w-3 h-3" />
                  Bewerk
                </button>
              )}
            </div>
          )}

          {/* Leider-titel (boven intro) */}
          {(active.leider_titel || active.leider) && (
            <div className="mb-2 flex items-center gap-1.5">
              <Crown className="w-3 h-3" style={{ color: activeColor }} />
              <span className="text-[10px] uppercase tracking-wider" style={{ color: activeColor }}>Leider:</span>
              <span className="text-[11px] text-amber-100 font-bold">
                {active.leider_naam ? `${active.leider_naam}` : ''}
                {active.leider_titel ? ` — ${active.leider_titel}` : (active.leider && active.leider !== '—' && !active.leider_naam ? active.leider : '')}
              </span>
            </div>
          )}

          {/* Intro */}
          {active.introductie ? (
            <p className="text-[11px] text-amber-100/85 mb-3 italic">{active.introductie}</p>
          ) : (
            <p className="text-[11px] italic text-amber-400/40 mb-3">Geen introductie ingevuld.</p>
          )}

          {/* Stats-rij (horizontaal) */}
          <div className="grid grid-cols-4 gap-1.5 mb-3">
            <MiniStat icon={Crown} label="Leider" value={active.leider_naam || active.leider_titel || active.leider || '—'} accent={activeColor} />
            <MiniStat icon={Users} label="Aanhangers" value={active.stats?.aanhangers_total ?? 0} accent={activeColor} />
            <MiniStat icon={Building} label="Steden" value={stedenVanFractie.length} accent={activeColor} />
            <MiniStat icon={Coins} label="Goud" value={active.stats?.goud ?? 0} accent={activeColor} />
          </div>

          {/* v6_dnd_fractie_edit_001 — Kernwaarden + Kleuren-palet */}
          {(active.kernwaarden?.length || active.kleuren?.length) ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
              {active.kernwaarden?.length > 0 && (
                <div className="p-2 rounded border border-stone-800 bg-stone-950/40">
                  <div className="text-[9px] font-bold uppercase tracking-wider text-amber-300/70 mb-1">Kernwaarden</div>
                  <div className="flex flex-wrap gap-1">
                    {active.kernwaarden.map((k, i) => (
                      <span key={i} className="text-[10px] px-1.5 py-0.5 rounded-full border" style={{ borderColor: `${activeColor}60`, background: `${activeColor}15`, color: '#fef3c7' }}>
                        {k}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {active.kleuren?.length > 0 && (
                <div className="p-2 rounded border border-stone-800 bg-stone-950/40">
                  <div className="text-[9px] font-bold uppercase tracking-wider text-amber-300/70 mb-1">Kleuren-palet</div>
                  <div className="flex flex-wrap gap-1.5">
                    {active.kleuren.map((k, i) => (
                      <span key={i} className="text-[10px] text-amber-100/85">{k}{i < active.kleuren.length - 1 ? ' ·' : ''}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}

          {/* v6_dnd_fractie_edit_001 — Bonussen + Malussen */}
          {(active.bonussen?.length || active.malussen?.length) ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
              {active.bonussen?.length > 0 && (
                <div className="p-2 rounded border border-emerald-900/40 bg-emerald-950/20">
                  <div className="text-[9px] font-bold uppercase tracking-wider text-emerald-300/80 mb-1">Bonussen</div>
                  <ul className="text-[11px] text-emerald-100/90 space-y-0.5">
                    {active.bonussen.map((b, i) => <li key={i}>• {b}</li>)}
                  </ul>
                </div>
              )}
              {active.malussen?.length > 0 && (
                <div className="p-2 rounded border border-red-900/40 bg-red-950/20">
                  <div className="text-[9px] font-bold uppercase tracking-wider text-red-300/80 mb-1">Malussen</div>
                  <ul className="text-[11px] text-red-100/90 space-y-0.5">
                    {active.malussen.map((m, i) => <li key={i}>• {m}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ) : null}

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

          {/* Link naar D&D archief kaart */}
          {active.linked_game_card_id && (
            <div className="mt-2 flex items-center gap-1.5 text-[10px] text-amber-300/70">
              <LinkIcon className="w-3 h-3" />
              Gekoppeld aan D&D-kaart: <span className="font-mono text-amber-200">{active.linked_game_card_id}</span>
            </div>
          )}
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
          userId={userId}
          isAdmin={isAdmin}
          onClose={() => setOpenLandkaart(false)}
          onOpenStad={(s) => setOpenStad(s)}
        />
      )}
      {editingFid && (
        <FractieEditModal
          key={editingFid}
          fractie={fracties.find(f => f.id === editingFid)}
          userId={userId}
          onClose={() => setEditingFid(null)}
          onSaved={() => { reloadFracties(); setEditingFid(null); }}
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

  if (!data?.stad) return <MapModal title="Laden..." onClose={onClose} maxWidth="max-w-2xl" zIndex={60}><div /></MapModal>;
  const s = data.stad;
  const leid = data.leidende_fractie || {};
  const color = leid.kleur || '#94a3b8';

  return (
    <MapModal title={`${s.type.toUpperCase()} · ${s.naam.toUpperCase()}`} onClose={onClose} maxWidth="max-w-3xl" zIndex={60}>
      <div className="space-y-3">
        {/* Hoofd-blok: avatar (fractie-logo voor hoofdstad, anders stad-banner/logo of initiaal) + info */}
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
            {/* v6_dnd_fractie_marker_001 — hoofdstad toont avatar van leidende fractie */}
            {(s.type === 'hoofdstad' && (leid.icon_image_url || leid.banner_image_url)) ? (
              <img src={`${API}${leid.icon_image_url || leid.banner_image_url}`} alt={leid.naam} className="w-full h-full object-cover" />
            ) : (s.logo_url || s.banner_image_url) ? (
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
// v6_dnd_resources_001 — admin: drag-and-drop voor steden + "+ Resource"
// ============================================================
const NL_MAP_URL = 'https://customer-assets.emergentagent.com/job_question-hub-160/artifacts/pkw3x971_Nederland%20map%20kaal.jpeg';

export function LandkaartBark({ provincies, steden: stedenProp, fracties, userId, isAdmin, onClose, onOpenStad }) {
  const [selectedProv, setSelectedProv] = useState(null);
  const [pulsingStadId, setPulsingStadId] = useState(null);
  // v6_dnd_steden_drag_001 — lokale overrides voor drag, valt anders terug op prop
  const [stedenOverride, setStedenOverride] = useState(null);
  const steden = stedenOverride ?? stedenProp ?? [];
  const setSteden = (updater) => {
    setStedenOverride(prev => {
      const base = prev ?? stedenProp ?? [];
      return typeof updater === 'function' ? updater(base) : updater;
    });
  };

  // v6_dnd_resources_001 — resources state + types
  const [resources, setResources] = useState([]);
  const [resourceTypes, setResourceTypes] = useState([]);
  const [addOpen, setAddOpen] = useState(false);
  const [editMode, setEditMode] = useState(false); // admin-drag toggle
  const [dragging, setDragging] = useState(null);  // {kind:'stad'|'resource', id}
  const mapRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/api/dnd/world/resources`).then(r => r.json()).then(d => {
      setResources(d.resources || []);
      setResourceTypes(d.types || []);
    }).catch(() => {});
  }, []);

  const fractieById = Object.fromEntries(fracties.map(f => [f.id, f]));
  const stedenInProv = selectedProv ? steden.filter(s => s.provincie_id === selectedProv.id) : [];
  const heersFractie = selectedProv ? fractieById[selectedProv.fractie_id] : null;

  const handleStadClick = (s) => {
    if (editMode) return; // tijdens drag-mode geen detail openen
    setPulsingStadId(s.id);
    setTimeout(() => onOpenStad(s), 300);
  };

  // v6_dnd_steden_drag_001 — drag helpers
  const pctFromEvent = (clientX, clientY) => {
    const el = mapRef.current;
    if (!el) return null;
    const rect = el.getBoundingClientRect();
    const x = ((clientX - rect.left) / rect.width) * 100;
    const y = ((clientY - rect.top) / rect.height) * 100;
    return { x_pct: Math.max(1, Math.min(99, x)), y_pct: Math.max(1, Math.min(99, y)) };
  };

  const onPointerDown = (e, kind, id) => {
    if (!editMode) return;
    e.preventDefault();
    e.stopPropagation();
    setDragging({ kind, id });
    e.currentTarget.setPointerCapture?.(e.pointerId);
  };

  const onPointerMove = (e) => {
    if (!dragging) return;
    const p = pctFromEvent(e.clientX, e.clientY);
    if (!p) return;
    if (dragging.kind === 'stad') {
      setSteden(prev => prev.map(s => s.id === dragging.id
        ? { ...s, kaart: { ...(s.kaart || {}), x_pct: p.x_pct, y_pct: p.y_pct } } : s));
    } else if (dragging.kind === 'resource') {
      setResources(prev => prev.map(r => r.id === dragging.id
        ? { ...r, kaart: { ...(r.kaart || {}), x_pct: p.x_pct, y_pct: p.y_pct } } : r));
    }
  };

  const onPointerUp = async () => {
    if (!dragging) return;
    const cur = dragging;
    setDragging(null);
    if (cur.kind === 'stad') {
      const s = steden.find(x => x.id === cur.id);
      if (!s) return;
      await fetch(`${API}/api/dnd/world/steden/${cur.id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, x_pct: s.kaart?.x_pct, y_pct: s.kaart?.y_pct }),
      }).catch(() => {});
    } else if (cur.kind === 'resource') {
      const r = resources.find(x => x.id === cur.id);
      if (!r) return;
      await fetch(`${API}/api/dnd/world/resources/${cur.id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, x_pct: r.kaart?.x_pct, y_pct: r.kaart?.y_pct }),
      }).catch(() => {});
    }
  };

  const handleResourceCreated = (newRes) => {
    setResources(prev => [...prev, newRes]);
    setAddOpen(false);
  };

  const handleResourceDelete = async (rid) => {
    if (!window.confirm('Verwijder deze grondstof van de kaart?')) return;
    await fetch(`${API}/api/dnd/world/resources/${rid}?user_id=${encodeURIComponent(userId)}`, {
      method: 'DELETE',
    }).catch(() => {});
    setResources(prev => prev.filter(r => r.id !== rid));
  };

  // v6_dnd_resources_dup_001 — dupliceer resource (hergebruikt image, maakt nieuwe kaarten)
  const handleResourceDuplicate = async (rid) => {
    try {
      const r = await fetch(`${API}/api/dnd/world/resources/${rid}/duplicate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });
      if (!r.ok) throw new Error(`${r.status}`);
      const d = await r.json();
      if (d.resource) setResources(prev => [...prev, d.resource]);
    } catch (e) {
      window.alert(`Dupliceren mislukt: ${e.message}`);
    }
  };

  return (
    <MapModal title="LANDKAART · STORMHAVEN" onClose={onClose} maxWidth="max-w-5xl">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3">
        {/* LINKS: grote kaart (col-span 8) */}
        <div className="lg:col-span-8">
          <div className="flex items-center justify-between mb-1.5">
            <p className="text-[11px] text-amber-300/60">
              Klik op een gebied om de steden te zien. De marker-kleur toont de leidende fractie.
            </p>
            {isAdmin && (
              <div className="flex items-center gap-1.5">
                <button
                  data-testid="landkaart-edit-toggle"
                  onClick={() => setEditMode(v => !v)}
                  className={`text-[10px] px-2 py-1 rounded border transition-colors ${
                    editMode
                      ? 'border-emerald-400 bg-emerald-900/40 text-emerald-200'
                      : 'border-amber-700/60 bg-stone-950 text-amber-200 hover:bg-amber-900/30'
                  }`}
                  title="Sleep steden & resources naar nieuwe positie"
                >
                  {editMode ? '✓ Sleep-modus aan' : '✎ Bewerk posities'}
                </button>
                <button
                  data-testid="landkaart-add-resource-btn"
                  onClick={() => setAddOpen(true)}
                  className="text-[10px] px-2 py-1 rounded border border-amber-700/60 bg-stone-950 text-amber-200 hover:bg-amber-900/30 flex items-center gap-1"
                  title="Voeg een grondstof toe op de kaart"
                >
                  <Plus className="w-3 h-3" />
                  Resource
                </button>
              </div>
            )}
          </div>
          <div
            ref={mapRef}
            className="relative aspect-[3/4] bg-stone-950 rounded-lg border-2 border-amber-900/40 overflow-hidden"
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerLeave={onPointerUp}
            style={{ touchAction: dragging ? 'none' : 'auto', cursor: dragging ? 'grabbing' : 'default' }}
          >
            <img src={NL_MAP_URL} alt="Nederland kaart" className="absolute inset-0 w-full h-full object-cover pointer-events-none" />
            <div className="absolute inset-0 bg-gradient-to-br from-stone-900/15 to-stone-950/30 pointer-events-none" />

            {/* v6_dnd_steden_only_001 — Geen aparte provincie-markers meer:
                de stad IS de hoofdstad van de provincie, 2 containers was verwarrend.
                Dorpen binnen een provincie worden later eigen markers. */}

            {/* Stad markers — alleen voor geselecteerd gebied of alle bij geen selectie */}
            {(selectedProv ? stedenInProv : steden).map(s => {
              const leid = fractieById[s.leidende_fractie_id];
              const color = leid?.kleur || '#94a3b8';
              const isPulsing = pulsingStadId === s.id;
              const x = s.kaart?.x_pct ?? 50;
              const y = s.kaart?.y_pct ?? 50;
              const isStad = s.type === 'hoofdstad' || s.type === 'stad';
              const isDraggingThis = dragging?.kind === 'stad' && dragging?.id === s.id;
              const isSelectedProv = selectedProv?.id === s.provincie_id;
              // v6_dnd_fractie_marker_001 — toon fractie-icon in marker als beschikbaar
              const fractieIcon = leid?.icon_image_url || leid?.banner_image_url;
              const markerSize = isStad ? 24 : 16; // px (was 12/8 als CSS classes)
              return (
                <button
                  key={s.id}
                  data-testid={`stad-marker-${s.id}`}
                  onPointerDown={(e) => onPointerDown(e, 'stad', s.id)}
                  onClick={() => handleStadClick(s)}
                  className="absolute -translate-x-1/2 -translate-y-1/2 group flex flex-col items-center"
                  style={{ left: `${x}%`, top: `${y}%`, cursor: editMode ? (isDraggingThis ? 'grabbing' : 'grab') : 'pointer' }}
                  title={`${s.naam} — ${leid?.naam || 'Neutraal'}${editMode ? ' (sleep om te verplaatsen)' : ''}`}
                >
                  <div
                    className={`rounded-md border-2 transition-all overflow-hidden ${
                      isPulsing ? 'animate-pulse scale-150' : 'group-hover:scale-125'
                    } ${isSelectedProv ? 'scale-150' : ''} ${
                      editMode ? 'ring-1 ring-emerald-400/70' : ''
                    }`}
                    style={{
                      width: markerSize, height: markerSize,
                      borderColor: isSelectedProv ? '#fde68a' : color,
                      background: fractieIcon ? '#000' : color,
                      boxShadow: isStad ? `0 0 6px ${color}80` : 'none',
                    }}
                  >
                    {fractieIcon ? (
                      <img
                        src={`${API}${fractieIcon}`}
                        alt={leid?.naam || ''}
                        className="w-full h-full object-cover"
                      />
                    ) : null}
                  </div>
                  <span className={`text-[9px] mt-0.5 px-1 rounded whitespace-nowrap font-bold transition-all ${
                    isSelectedProv
                      ? 'opacity-100 bg-stone-950 text-amber-200'
                      : 'opacity-80 bg-stone-950/60 text-stone-100 group-hover:opacity-100'
                  }`}>
                    {s.naam}
                  </span>
                </button>
              );
            })}

            {/* v6_dnd_resources_001 — Resource markers */}
            {resources.map(r => {
              const typeMeta = resourceTypes.find(t => t.id === r.type) || {};
              const color = typeMeta.kleur || '#94a3b8';
              const x = r.kaart?.x_pct ?? 50;
              const y = r.kaart?.y_pct ?? 50;
              const isDraggingThis = dragging?.kind === 'resource' && dragging?.id === r.id;
              return (
                <div
                  key={r.id}
                  data-testid={`resource-marker-${r.id}`}
                  onPointerDown={(e) => onPointerDown(e, 'resource', r.id)}
                  className="absolute -translate-x-1/2 -translate-y-1/2 group"
                  style={{ left: `${x}%`, top: `${y}%`, cursor: editMode ? (isDraggingThis ? 'grabbing' : 'grab') : 'pointer' }}
                  title={`${r.naam} (${typeMeta.naam || r.type})${editMode ? ' — sleep om te verplaatsen' : ''}`}
                >
                  <div
                    className={`w-4 h-4 rounded-md border-2 overflow-hidden transition-all group-hover:scale-125 ${
                      editMode ? 'ring-1 ring-emerald-400/70' : ''
                    }`}
                    style={{ borderColor: color, background: r.image_url ? '#000' : color }}
                  >
                    {r.image_url ? (
                      <img src={`${API}${r.image_url}`} alt={r.naam} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full" />
                    )}
                  </div>
                  {editMode && (
                    <>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleResourceDelete(r.id); }}
                        className="absolute -top-2 -right-2 w-4 h-4 bg-red-700 hover:bg-red-600 rounded-full flex items-center justify-center"
                        title="Verwijder"
                        data-testid={`resource-delete-${r.id}`}
                      >
                        <Trash2 className="w-2.5 h-2.5 text-white" />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleResourceDuplicate(r.id); }}
                        className="absolute -top-2 -left-2 w-4 h-4 bg-amber-700 hover:bg-amber-600 rounded-full flex items-center justify-center"
                        title="Dupliceer"
                        data-testid={`resource-duplicate-${r.id}`}
                      >
                        <Copy className="w-2.5 h-2.5 text-white" />
                      </button>
                    </>
                  )}
                  <span className="absolute top-full left-1/2 -translate-x-1/2 mt-0.5 text-[8px] whitespace-nowrap font-bold bg-stone-950/80 text-amber-100 px-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                    {r.naam}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* RECHTS: info-paneel (col-span 4) */}
        <div className="lg:col-span-4 flex flex-col">
          {!selectedProv ? (
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-amber-300/70 mb-1.5">Gebieden ({provincies.length})</div>
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
              {/* v6_dnd_resources_001 — resources lijst in side-panel */}
              {resources.length > 0 && (
                <div className="mt-3">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-amber-300/70 mb-1.5">
                    Grondstoffen ({resources.length})
                  </div>
                  <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
                    {resources.map(r => {
                      const t = resourceTypes.find(x => x.id === r.type) || {};
                      return (
                        <div key={r.id} className="flex items-center gap-2 p-1.5 rounded bg-stone-900/40 border border-stone-800">
                          {r.image_url ? (
                            <img src={`${API}${r.image_url}`} alt={r.naam} className="w-6 h-6 object-cover rounded" />
                          ) : (
                            <div className="w-6 h-6 rounded" style={{ background: t.kleur || '#94a3b8' }} />
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="text-[11px] font-bold text-amber-100 truncate">{r.naam}</div>
                            <div className="text-[9px] text-amber-400/60">{t.naam || r.type}</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
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
                    <div className="text-[9px] uppercase tracking-wider text-amber-300/60">Gebied</div>
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
                        onClick={() => handleStadClick(s)}
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
                    <p className="text-[11px] italic text-amber-400/40">Geen steden in dit gebied.</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add Resource modal */}
      {addOpen && (
        <AddResourceModal
          onClose={() => setAddOpen(false)}
          onCreated={handleResourceCreated}
          types={resourceTypes}
          fracties={fracties}
          userId={userId}
        />
      )}
    </MapModal>
  );
}

// ============================================================
// ADD RESOURCE MODAL (v6_dnd_resources_001)
// ============================================================
function AddResourceModal({ onClose, onCreated, types, fracties, userId }) {
  const [naam, setNaam] = useState('');
  const [type, setType] = useState('bos');
  const [beschrijving, setBeschrijving] = useState('');
  const [fractieId, setFractieId] = useState('');
  const [createKbCard, setCreateKbCard] = useState(true);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const onPick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const submit = async () => {
    setError(null);
    if (!file) { setError('Kies eerst een afbeelding.'); return; }
    if (!naam.trim()) { setError('Geef de grondstof een naam.'); return; }
    setBusy(true);
    const fd = new FormData();
    fd.append('image', file);
    fd.append('naam', naam.trim());
    fd.append('type', type);
    fd.append('beschrijving', beschrijving);
    if (fractieId) fd.append('fractie_id', fractieId);
    fd.append('x_pct', '50');     // initieel midden; admin sleept hem op zijn plek
    fd.append('y_pct', '50');
    fd.append('user_id', userId || '');
    fd.append('create_kb_card', createKbCard ? 'true' : 'false');
    try {
      const r = await fetch(`${API}/api/dnd/world/resources`, { method: 'POST', body: fd });
      if (!r.ok) {
        const txt = await r.text();
        throw new Error(`${r.status}: ${txt}`);
      }
      const d = await r.json();
      onCreated(d.resource);
    } catch (e) {
      setError(`Upload mislukt: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <MapModal title="GRONDSTOF · TOEVOEGEN AAN KAART" onClose={onClose} maxWidth="max-w-md" zIndex={70}>
      <div className="space-y-3 text-amber-100">
        <p className="text-[11px] italic text-amber-300/70">
          Upload een afbeelding voor de grondstof. Na opslaan verschijnt er een marker in het midden van de kaart;
          zet daarna &ldquo;Bewerk posities&rdquo; aan en sleep hem op zijn plek.
        </p>

        {/* Upload */}
        <label className="block">
          <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Afbeelding</span>
          <div className="mt-1 flex items-center gap-2">
            <label className="flex-1 cursor-pointer">
              <div className="flex items-center justify-center gap-1.5 px-3 py-2 rounded border border-amber-900/40 bg-stone-950 hover:bg-stone-900 text-[11px] text-amber-200">
                <Upload className="w-3.5 h-3.5" />
                {file ? file.name : 'Kies bestand…'}
              </div>
              <input
                data-testid="resource-file-input"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={onPick}
              />
            </label>
            {preview && (
              <img src={preview} alt="preview" className="w-12 h-12 object-cover rounded border border-amber-900/40" />
            )}
          </div>
        </label>

        {/* Naam */}
        <label className="block">
          <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Naam</span>
          <input
            data-testid="resource-naam-input"
            value={naam}
            onChange={e => setNaam(e.target.value)}
            placeholder="bijv. Zuiderzee visgrond"
            className="mt-1 w-full px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-[12px] text-amber-100 placeholder-amber-500/40"
          />
        </label>

        {/* Type */}
        <label className="block">
          <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Type</span>
          <select
            data-testid="resource-type-select"
            value={type}
            onChange={e => setType(e.target.value)}
            className="mt-1 w-full px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-[12px] text-amber-100"
          >
            {types.map(t => (
              <option key={t.id} value={t.id}>{t.naam}</option>
            ))}
          </select>
        </label>

        {/* Fractie (optioneel) */}
        <label className="block">
          <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Fractie (optioneel)</span>
          <select
            data-testid="resource-fractie-select"
            value={fractieId}
            onChange={e => setFractieId(e.target.value)}
            className="mt-1 w-full px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-[12px] text-amber-100"
          >
            <option value="">— geen —</option>
            {fracties.map(f => (
              <option key={f.id} value={f.id}>{f.naam}</option>
            ))}
          </select>
        </label>

        {/* Beschrijving */}
        <label className="block">
          <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Beschrijving</span>
          <textarea
            data-testid="resource-desc-input"
            value={beschrijving}
            onChange={e => setBeschrijving(e.target.value)}
            placeholder="Korte beschrijving (komt op de kaart in laag-1)"
            rows={2}
            className="mt-1 w-full px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-[12px] text-amber-100 placeholder-amber-500/40"
          />
        </label>

        {/* KB checkbox */}
        <label className="flex items-center gap-2 text-[11px] text-amber-200/80">
          <input
            type="checkbox"
            data-testid="resource-kb-checkbox"
            checked={createKbCard}
            onChange={e => setCreateKbCard(e.target.checked)}
          />
          Maak ook een KennisBank-inbox kaart aan (zodat Spark de grondstof kent)
        </label>

        {error && (
          <div className="text-[11px] text-red-300 bg-red-950/40 border border-red-900/60 rounded px-2 py-1">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-1">
          <button
            onClick={onClose}
            className="text-[11px] px-3 py-1.5 rounded border border-stone-700 text-stone-300 hover:bg-stone-900"
          >
            Annuleer
          </button>
          <button
            data-testid="resource-submit-btn"
            onClick={submit}
            disabled={busy}
            className="text-[11px] px-3 py-1.5 rounded bg-amber-700 hover:bg-amber-600 text-stone-950 font-bold disabled:opacity-50"
          >
            {busy ? 'Uploaden…' : 'Toevoegen'}
          </button>
        </div>
      </div>
    </MapModal>
  );
}


// ============================================================
// v6_dnd_fractie_edit_001 — FRACTIE EDIT MODAL
// Admin paneel voor naam, leider, tagline, intro, beschrijving,
// kernwaarden / kleuren / bonussen / malussen (lijsten), kleur,
// banner upload, link naar D&D game-card.
// ============================================================
function ListEditor({ label, items, setItems, placeholder, accent = '#f59e0b', testid }) {
  const [draft, setDraft] = useState('');
  const add = () => {
    const v = draft.trim();
    if (!v) return;
    setItems([...items, v]);
    setDraft('');
  };
  return (
    <div className="space-y-1">
      <div className="text-[10px] uppercase tracking-wider text-amber-300/70">{label}</div>
      <div className="flex flex-wrap gap-1">
        {items.map((it, i) => (
          <span key={i} className="text-[10px] px-1.5 py-0.5 rounded-full border flex items-center gap-1" style={{ borderColor: `${accent}60`, background: `${accent}15`, color: '#fef3c7' }}>
            {it}
            <button
              onClick={() => setItems(items.filter((_, idx) => idx !== i))}
              className="hover:text-red-300"
              title="Verwijder"
            >
              <X className="w-2.5 h-2.5" />
            </button>
          </span>
        ))}
        {items.length === 0 && <span className="text-[10px] italic text-stone-500">Nog leeg.</span>}
      </div>
      <div className="flex gap-1">
        <input
          data-testid={testid}
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), add())}
          placeholder={placeholder}
          className="flex-1 px-2 py-1 bg-stone-950 border border-amber-900/40 rounded text-[11px] text-amber-100 placeholder-amber-500/40"
        />
        <button
          onClick={add}
          className="px-2 py-1 text-[10px] rounded bg-amber-800 hover:bg-amber-700 text-amber-50 font-bold"
        >
          + Toevoegen
        </button>
      </div>
    </div>
  );
}

function GameCardPicker({ value, onChange, testid, fractieId, userId, onImported }) {
  const [cards, setCards] = useState([]);
  const [query, setQuery] = useState('');
  const [importing, setImporting] = useState(false);
  useEffect(() => {
    fetch(`${API}/api/dnd/spark-world/game-cards?limit=500`).then(r => r.json()).then(d => {
      setCards(d.cards || []);
    });
  }, []);
  const filtered = query.trim()
    ? cards.filter(c => (c.begrip || '').toLowerCase().includes(query.toLowerCase().trim()))
    : cards.slice(0, 20);
  const linked = cards.find(c => c.id === value);

  const handleImport = async () => {
    if (!value || !fractieId || !userId) return;
    if (!window.confirm(`Importeer alle velden uit "${linked?.begrip}" naar deze fractie? Bestaande waarden worden overschreven.`)) return;
    setImporting(true);
    try {
      const r = await fetch(`${API}/api/dnd/world/fracties/${fractieId}/import-from-card`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, card_id: value, apply: true, overwrite_existing: true }),
      });
      if (!r.ok) throw new Error(`${r.status}`);
      const d = await r.json();
      if (onImported) onImported(d);
    } catch (e) {
      window.alert(`Import mislukt: ${e.message}`);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-1">
      <div className="text-[10px] uppercase tracking-wider text-amber-300/70">D&amp;D archief kaart (optioneel)</div>
      {linked && (
        <div className="flex items-center gap-2 p-1.5 rounded border border-amber-900/40 bg-stone-950/60">
          {linked.media?.image_urls?.[0] ? (
            <img src={`${API}${linked.media.image_urls[0]}`} alt="" className="w-8 h-8 object-cover rounded" />
          ) : (
            <div className="w-8 h-8 rounded bg-stone-900 flex items-center justify-center">
              <LinkIcon className="w-4 h-4 text-amber-400/60" />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="text-[11px] font-bold text-amber-100 truncate">{linked.begrip}</div>
            <div className="text-[9px] text-stone-500 font-mono">{linked.id}</div>
          </div>
          {fractieId && userId && (
            <button
              data-testid="fractie-import-from-card-btn"
              onClick={handleImport}
              disabled={importing}
              className="text-[10px] px-2 py-0.5 rounded border border-emerald-700/60 bg-emerald-950/40 text-emerald-200 hover:bg-emerald-900/60 disabled:opacity-50 flex items-center gap-1"
              title="Lees alle velden (naam, leider, bonussen, malussen, banner) uit deze kaart"
            >
              <Upload className="w-3 h-3 rotate-180" />
              {importing ? 'Importeren…' : 'Importeer'}
            </button>
          )}
          <button
            onClick={() => onChange(null)}
            className="text-[10px] px-1.5 py-0.5 rounded border border-red-700/60 text-red-300 hover:bg-red-900/30"
            title="Ontkoppel"
          >
            × Ontkoppel
          </button>
        </div>
      )}
      <input
        data-testid={testid}
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder={linked ? 'Zoek een andere kaart…' : 'Zoek D&D-kaart…'}
        className="w-full px-2 py-1 bg-stone-950 border border-amber-900/40 rounded text-[11px] text-amber-100 placeholder-amber-500/40"
      />
      {query.trim() && (
        <div className="max-h-36 overflow-y-auto space-y-0.5 border border-amber-900/30 rounded bg-stone-950/40 p-1">
          {filtered.slice(0, 30).map(c => (
            <button
              key={c.id}
              onClick={() => { onChange(c.id); setQuery(''); }}
              className="w-full text-left px-1.5 py-0.5 text-[10px] rounded hover:bg-amber-900/30 text-amber-200 truncate"
            >
              {c.begrip} <span className="text-stone-500 font-mono">({c.id})</span>
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="text-[10px] italic text-stone-500 px-1">Geen kaarten gevonden.</p>
          )}
        </div>
      )}
      {linked && fractieId && (
        <p className="text-[9px] italic text-amber-400/60">
          Tip: schrijf de fractie-info in deze kaart (laag1 = + bonussen, − malussen, &ldquo;Leider:&rdquo;, &ldquo;Stads naam: X&rdquo;). Klik dan op <span className="text-emerald-300">Importeer</span> en de velden worden automatisch ingevuld.
        </p>
      )}
    </div>
  );
}

function FractieEditModal({ fractie, userId, onClose, onSaved }) {
  const [form, setForm] = useState(() => ({
    naam: fractie?.naam || '',
    kleur: fractie?.kleur || '#94a3b8',
    leider_naam: fractie?.leider_naam || '',
    leider_titel: fractie?.leider_titel || (fractie?.leider && fractie?.leider !== '—' ? fractie.leider : ''),
    tagline: fractie?.tagline || '',
    beschrijving: fractie?.beschrijving || '',
    introductie: fractie?.introductie || '',
    kernwaarden: Array.isArray(fractie?.kernwaarden) ? [...fractie.kernwaarden] : [],
    kleuren: Array.isArray(fractie?.kleuren) ? [...fractie.kleuren] : [],
    bonussen: Array.isArray(fractie?.bonussen) ? [...fractie.bonussen] : [],
    malussen: Array.isArray(fractie?.malussen) ? [...fractie.malussen] : [],
    banner_image_url: fractie?.banner_image_url || null,
    icon_image_url: fractie?.icon_image_url || null,
    linked_game_card_id: fractie?.linked_game_card_id || null,
  }));
  const [bannerFile, setBannerFile] = useState(null);
  const [bannerPreview, setBannerPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  if (!fractie) return null;

  const onPickBanner = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setBannerFile(f);
    setBannerPreview(URL.createObjectURL(f));
  };

  const save = async () => {
    setError(null);
    setBusy(true);
    try {
      // 1. Upload banner if changed
      let bannerUrl = form.banner_image_url;
      if (bannerFile) {
        const fd = new FormData();
        fd.append('image', bannerFile);
        fd.append('kind', 'banner');
        fd.append('user_id', userId);
        const r = await fetch(`${API}/api/dnd/world/fracties/${fractie.id}/banner`, { method: 'POST', body: fd });
        if (!r.ok) throw new Error(`Banner upload ${r.status}`);
        const d = await r.json();
        bannerUrl = d.image_url;
      }
      // 2. PATCH fractie
      const body = {
        user_id: userId,
        naam: form.naam,
        kleur: form.kleur,
        leider_naam: form.leider_naam,
        leider_titel: form.leider_titel,
        tagline: form.tagline,
        beschrijving: form.beschrijving,
        introductie: form.introductie,
        kernwaarden: form.kernwaarden,
        kleuren: form.kleuren,
        bonussen: form.bonussen,
        malussen: form.malussen,
        banner_image_url: bannerUrl,
        linked_game_card_id: form.linked_game_card_id,
      };
      const r2 = await fetch(`${API}/api/dnd/world/fracties/${fractie.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!r2.ok) {
        const txt = await r2.text();
        throw new Error(`PATCH ${r2.status}: ${txt}`);
      }
      onSaved();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <MapModal title={`FRACTIE BEWERKEN · ${(fractie.naam || '').toUpperCase()}`} onClose={onClose} maxWidth="max-w-3xl" zIndex={70}>
      <div className="space-y-3 text-amber-100">
        {/* Banner upload + preview */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-amber-300/70 mb-1">Banner-afbeelding</div>
          <div className="flex gap-2 items-start">
            <div className="flex-shrink-0 w-32 h-20 rounded border-2 overflow-hidden bg-stone-950" style={{ borderColor: `${form.kleur}60` }}>
              {bannerPreview || form.banner_image_url ? (
                <img
                  src={bannerPreview || `${API}${form.banner_image_url}`}
                  alt="banner"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-stone-600">
                  <ImageIcon className="w-8 h-8" />
                </div>
              )}
            </div>
            <div className="flex-1 space-y-1">
              <label className="cursor-pointer block">
                <div className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded border border-amber-900/40 bg-stone-950 hover:bg-stone-900 text-[11px] text-amber-200">
                  <Upload className="w-3.5 h-3.5" />
                  {bannerFile ? bannerFile.name : 'Vervang banner…'}
                </div>
                <input
                  data-testid="fractie-banner-input"
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={onPickBanner}
                />
              </label>
              <p className="text-[10px] italic text-amber-400/60">Max 8MB. Aanbevolen: 1024×512 of breder.</p>
            </div>
          </div>
        </div>

        {/* Naam + Kleur */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <label className="block md:col-span-2">
            <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Fractie-naam</span>
            <input
              data-testid="fractie-naam-input"
              value={form.naam}
              onChange={e => setForm(f => ({ ...f, naam: e.target.value }))}
              className="mt-1 w-full px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-[12px] text-amber-100"
            />
          </label>
          <label className="block">
            <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Kleur</span>
            <div className="mt-1 flex gap-1">
              <input
                type="color"
                value={form.kleur}
                onChange={e => setForm(f => ({ ...f, kleur: e.target.value }))}
                className="w-12 h-8 bg-stone-950 border border-amber-900/40 rounded cursor-pointer"
              />
              <input
                value={form.kleur}
                onChange={e => setForm(f => ({ ...f, kleur: e.target.value }))}
                className="flex-1 px-2 py-1 bg-stone-950 border border-amber-900/40 rounded text-[11px] text-amber-100 font-mono"
              />
            </div>
          </label>
        </div>

        {/* Leider naam + titel */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <label className="block">
            <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Leider — Naam</span>
            <input
              data-testid="fractie-leider-naam"
              value={form.leider_naam}
              onChange={e => setForm(f => ({ ...f, leider_naam: e.target.value }))}
              placeholder="(naam van de huidige leider)"
              className="mt-1 w-full px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-[12px] text-amber-100 placeholder-amber-500/40"
            />
          </label>
          <label className="block">
            <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Leider — Titel</span>
            <input
              data-testid="fractie-leider-titel"
              value={form.leider_titel}
              onChange={e => setForm(f => ({ ...f, leider_titel: e.target.value }))}
              placeholder="bv. Koning der Rijk van Aschen"
              className="mt-1 w-full px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-[12px] text-amber-100 placeholder-amber-500/40"
            />
          </label>
        </div>

        {/* Tagline */}
        <label className="block">
          <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Tagline / Bijnaam</span>
          <input
            data-testid="fractie-tagline-input"
            value={form.tagline}
            onChange={e => setForm(f => ({ ...f, tagline: e.target.value }))}
            placeholder="bv. Het Smeedverbond"
            className="mt-1 w-full px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-[12px] text-amber-100 placeholder-amber-500/40"
          />
        </label>

        {/* Beschrijving + Introductie */}
        <label className="block">
          <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Korte beschrijving (1 zin)</span>
          <input
            value={form.beschrijving}
            onChange={e => setForm(f => ({ ...f, beschrijving: e.target.value }))}
            className="mt-1 w-full px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-[12px] text-amber-100"
          />
        </label>
        <label className="block">
          <span className="text-[10px] uppercase tracking-wider text-amber-300/70">Introductie (lyrische tekst)</span>
          <textarea
            data-testid="fractie-introductie"
            value={form.introductie}
            onChange={e => setForm(f => ({ ...f, introductie: e.target.value }))}
            rows={3}
            className="mt-1 w-full px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-[12px] text-amber-100"
          />
        </label>

        {/* List editors: kernwaarden, kleuren, bonussen, malussen */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <ListEditor
            label="Kernwaarden"
            items={form.kernwaarden}
            setItems={(v) => setForm(f => ({ ...f, kernwaarden: v }))}
            placeholder="bv. 🔥 Vuur"
            accent={form.kleur}
            testid="fractie-kernwaarden-input"
          />
          <ListEditor
            label="Kleuren-palet (namen)"
            items={form.kleuren}
            setItems={(v) => setForm(f => ({ ...f, kleuren: v }))}
            placeholder="bv. Dieprood"
            accent={form.kleur}
            testid="fractie-kleuren-input"
          />
          <ListEditor
            label="Bonussen (+)"
            items={form.bonussen}
            setItems={(v) => setForm(f => ({ ...f, bonussen: v }))}
            placeholder="bv. +25% productie van metaal"
            accent="#22c55e"
            testid="fractie-bonussen-input"
          />
          <ListEditor
            label="Malussen (−)"
            items={form.malussen}
            setItems={(v) => setForm(f => ({ ...f, malussen: v }))}
            placeholder="bv. -10% landbouw"
            accent="#dc2626"
            testid="fractie-malussen-input"
          />
        </div>

        {/* Koppel D&D-kaart + Importeer */}
        <GameCardPicker
          value={form.linked_game_card_id}
          onChange={(v) => setForm(f => ({ ...f, linked_game_card_id: v }))}
          testid="fractie-cardpicker-input"
          fractieId={fractie.id}
          userId={userId}
          onImported={() => { onSaved(); }}
        />

        {error && (
          <div className="text-[11px] text-red-300 bg-red-950/40 border border-red-900/60 rounded px-2 py-1">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-1 sticky bottom-0 bg-stone-950 pb-1">
          <button
            onClick={onClose}
            className="text-[11px] px-3 py-1.5 rounded border border-stone-700 text-stone-300 hover:bg-stone-900"
          >
            Annuleer
          </button>
          <button
            data-testid="fractie-save-btn"
            onClick={save}
            disabled={busy}
            className="text-[11px] px-3 py-1.5 rounded bg-amber-700 hover:bg-amber-600 text-stone-950 font-bold disabled:opacity-50 flex items-center gap-1"
          >
            <Save className="w-3 h-3" />
            {busy ? 'Opslaan…' : 'Opslaan'}
          </button>
        </div>
      </div>
    </MapModal>
  );
}
