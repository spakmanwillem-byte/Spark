// v6_dnd_bark_001 — Spark World bark-flow panel
// Toont intro + 3 zintuig-knoppen (Zie / Hoor / Voel) + bestaande locked cards.
// User klikt zintuig → vraag → typt antwoord → kaart opgeslagen als 'draft'.
import React, { useState, useEffect, useCallback } from 'react';
import { X, Save, Lock, Eye, ChevronRight, Sparkles, MapPin } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function DnDBarkPanel({ userId = 'user-001', onClose }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSense, setActiveSense] = useState(null);   // 'zie' | 'hoor' | 'voel'
  const [activeLocked, setActiveLocked] = useState(null); // locked card chosen as path
  const [content, setContent] = useState('');
  const [titel, setTitel] = useState('');
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);       // pas-aangemaakte kaart voor lock-knop
  // v6_spark_world_north_001 — locaties + travel-state
  const [locations, setLocations] = useState([]);
  const [activeLocation, setActiveLocation] = useState(null); // location-detail bij travel
  const [activeSubLocId, setActiveSubLocId] = useState(null);

  const start = useCallback(async () => {
    setLoading(true);
    setActiveSense(null);
    setActiveLocked(null);
    setContent('');
    setTitel('');
    setLastSaved(null);
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/start`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      }).then(x => x.json());
      setSession(r);
    } catch (e) {
      alert('Spark World kon niet starten: ' + e.message);
    }
    setLoading(false);
  }, [userId]);

  useEffect(() => { start(); }, [start]);

  // v6_spark_world_north_001 — laad locaties bij open
  useEffect(() => {
    fetch(`${API}/api/dnd/spark-world/locations`)
      .then(r => r.json())
      .then(d => setLocations(d.locations || []))
      .catch(() => setLocations([]));
  }, []);

  const travelTo = async (locId, subLocId = null) => {
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/locations/travel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, location_id: locId, sub_location_id: subLocId }),
      }).then(x => x.json());
      if (r.success) {
        setActiveLocation(r);
        setActiveSubLocId(subLocId);
        setActiveSense(null);
        setLastSaved(null);
      }
    } catch (e) {
      console.error('travel failed', e);
    }
  };

  const sense = session?.senses?.find(s => s.id === activeSense);

  const submit = async () => {
    if (!activeSense || !content.trim()) return;
    setSaving(true);
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/respond`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          sense: activeSense,
          content: content.trim(),
          titel: titel.trim() || null,
        }),
      }).then(x => x.json());
      if (r.success) {
        setLastSaved(r.card);
        setContent('');
        setTitel('');
      } else {
        alert(r.message || 'Opslaan mislukt');
      }
    } catch (e) {
      alert('Fout: ' + e.message);
    }
    setSaving(false);
  };

  const lock = async () => {
    if (!lastSaved) return;
    setSaving(true);
    try {
      const r = await fetch(`${API}/api/dnd/spark-world/cards/${lastSaved.id}/lock`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, locked: true }),
      }).then(x => x.json());
      if (r.success) {
        setLastSaved(prev => ({ ...prev, status: 'locked' }));
      }
    } catch (e) {
      alert('Lock mislukt: ' + e.message);
    }
    setSaving(false);
  };

  if (loading || !session) {
    return (
      <div data-testid="dnd-bark-loading" className="p-8 text-center text-slate-400">
        <Sparkles className="w-6 h-6 mx-auto mb-2 animate-pulse text-amber-400" />
        Spark World aan het wakker maken...
      </div>
    );
  }

  return (
    <div data-testid="dnd-bark-panel" className="border border-amber-500/30 bg-gradient-to-br from-slate-900/90 to-purple-950/40 rounded-2xl overflow-hidden">
      {/* Titel + baseline */}
      <div className="px-4 py-3 border-b border-amber-500/20 flex items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" /> {session.title}
          </h2>
          <p className="text-[11px] text-slate-400 mt-0.5">{session.baseline}</p>
        </div>
        {onClose && (
          <button data-testid="dnd-bark-close" onClick={onClose}
            className="p-1 text-slate-500 hover:text-white hover:bg-slate-800 rounded">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="p-4 space-y-4">
        {/* v6_spark_world_north_001 — Travel banner als user in een locatie staat */}
        {activeLocation && !activeSense && !lastSaved && (
          <div data-testid="dnd-travel-banner"
            className="rounded-xl border-2 p-3 space-y-2"
            style={{ borderColor: (activeLocation.color_primary || '#10b981') + '60',
                     background: (activeLocation.color_primary || '#10b981') + '10' }}>
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <MapPin className="w-4 h-4 flex-shrink-0" style={{ color: activeLocation.color_primary }} />
                <div className="min-w-0">
                  <p className="text-sm font-bold text-white truncate">
                    {activeLocation.naam}
                    {activeLocation.sub_location && (
                      <span className="text-slate-400 font-normal">
                        {' › '}{activeLocation.sub_location.naam}
                      </span>
                    )}
                  </p>
                  <p className="text-[10px] text-slate-400 truncate">{activeLocation.subtitle}</p>
                </div>
              </div>
              <button data-testid="dnd-travel-leave"
                onClick={() => { setActiveLocation(null); setActiveSubLocId(null); }}
                className="text-[10px] text-slate-400 hover:text-white px-2 py-1 rounded border border-slate-700">
                Verlaat plek
              </button>
            </div>
            <p className="text-xs text-slate-200 whitespace-pre-line">{activeLocation.intro}</p>
            {/* Sub-locaties */}
            {!activeLocation.sub_location && locations.length > 0 && (() => {
              const fullLoc = locations.find(l => l.id === activeLocation.location_id);
              return fullLoc && fullLoc.sub_locations_count > 0 ? (
                <SubLocationsList locationId={activeLocation.location_id} onPick={(subId) => travelTo(activeLocation.location_id, subId)} />
              ) : null;
            })()}
            {/* NPCs */}
            {(activeLocation.npc_stubs || []).length > 0 && (
              <div className="pt-2 border-t border-slate-700/50">
                <p className="text-[9px] uppercase tracking-wider text-slate-500 mb-1">NPCs hier</p>
                <div className="flex flex-wrap gap-1.5">
                  {activeLocation.npc_stubs.map(n => (
                    <span key={n.id} data-testid={`dnd-travel-npc-${n.id}`}
                      className="px-2 py-0.5 rounded-full text-[10px] border"
                      style={{ borderColor: (n.color || '#94a3b8') + '60',
                               color: n.color || '#94a3b8',
                               background: (n.color || '#94a3b8') + '12' }}>
                      {n.naam} · {n.rol}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {/* Senses hint */}
            {activeLocation.senses_hint && (
              <div className="pt-2 border-t border-slate-700/50 grid grid-cols-3 gap-1.5 text-[10px]">
                {['zie', 'hoor', 'voel'].map(k => (
                  <div key={k} className="text-slate-400">
                    <span className="text-slate-300 font-medium uppercase text-[9px]">{k}: </span>
                    {activeLocation.senses_hint[k] || '—'}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Intro */}
        {!activeSense && !lastSaved && (
          <>
            <div data-testid="dnd-bark-intro" className="text-sm text-slate-200 whitespace-pre-line leading-relaxed">
              {session.intro.split('**').map((part, i) => i % 2 === 1
                ? <strong key={i} className="text-amber-300">{part}</strong>
                : <span key={i}>{part}</span>)}
            </div>

            {/* 3 zintuig-knoppen */}
            <div className="grid grid-cols-3 gap-2">
              {session.senses.map(s => (
                <button key={s.id} data-testid={`dnd-bark-sense-${s.id}`}
                  onClick={() => { setActiveSense(s.id); setActiveLocked(null); }}
                  className="flex flex-col items-center gap-1.5 px-3 py-4 rounded-xl border-2 transition-all hover:scale-105 active:scale-95"
                  style={{
                    borderColor: s.color + '50',
                    background: s.color + '12',
                  }}>
                  <span className="text-2xl">{s.icon}</span>
                  <span className="text-sm font-bold" style={{ color: s.color }}>{s.label}</span>
                </button>
              ))}
            </div>

            {/* Bestaande locked-kaarten als alternatieve paden */}
            {session.locked_cards && session.locked_cards.length > 0 && (
              <div data-testid="dnd-bark-locked-paths" className="border-t border-slate-800 pt-3">
                <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1">
                  <Lock className="w-2.5 h-2.5" /> Of stap weer een bekend pad in:
                </p>
                <div className="flex flex-col gap-1.5">
                  {session.locked_cards.map(c => (
                    <button key={c.id} data-testid={`dnd-bark-path-${c.id}`}
                      onClick={() => { setActiveLocked(c); setActiveSense(c.sense); }}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-left border border-slate-700 hover:border-slate-500 transition-colors"
                      style={{ background: (c.color || '#94a3b8') + '08' }}>
                      <span style={{ color: c.color || '#94a3b8' }}>{c.icon || '✨'}</span>
                      <span className="text-xs text-slate-300 flex-1 truncate">{c.titel}</span>
                      <ChevronRight className="w-3 h-3 text-slate-600" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* v6_spark_world_north_001 — Locaties (incl. The North) */}
            {locations.length > 0 && !activeLocation && (
              <div data-testid="dnd-locations-panel" className="border-t border-slate-800 pt-3">
                <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1">
                  <MapPin className="w-2.5 h-2.5" /> Of reis naar een plek:
                </p>
                <div className="flex flex-col gap-1.5">
                  {locations.map(l => (
                    <button key={l.id} data-testid={`dnd-loc-${l.id}`}
                      onClick={() => travelTo(l.id)}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-left border-2 hover:scale-[1.01] transition-all"
                      style={{ borderColor: (l.color_primary || '#94a3b8') + '50',
                               background: (l.color_primary || '#94a3b8') + '10' }}>
                      <span className="text-lg">{l.icon}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-white truncate">{l.naam}</p>
                        <p className="text-[10px] text-slate-400 truncate">{l.tagline}</p>
                      </div>
                      <div className="text-[9px] text-slate-500 flex-shrink-0">
                        {l.sub_locations_count} plekken · {l.npc_count} NPCs
                      </div>
                      <ChevronRight className="w-3 h-3 text-slate-600 flex-shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Antwoord-vraag */}
        {activeSense && !lastSaved && sense && (
          <div data-testid="dnd-bark-prompt-panel" className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{sense.icon}</span>
              <div className="flex-1">
                <p className="text-[10px] uppercase tracking-wider" style={{ color: sense.color }}>{sense.label}</p>
                <p className="text-sm text-slate-100">{activeLocked
                  ? `Je stapt weer "${activeLocked.titel}" in. Wat zie je nu opnieuw, of anders?`
                  : sense.prompt}</p>
              </div>
            </div>
            <input data-testid="dnd-bark-titel" type="text" value={titel}
              onChange={e => setTitel(e.target.value)}
              placeholder="Titel (optioneel — Spark verzint anders een)"
              className="w-full px-3 py-1.5 bg-slate-900/60 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50" />
            <textarea data-testid="dnd-bark-content" value={content} rows={4}
              onChange={e => setContent(e.target.value)}
              placeholder="Schrijf wat je beleeft..."
              className="w-full px-3 py-2 bg-slate-900/60 border-2 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none"
              style={{ borderColor: sense.color + '50' }} />
            <div className="flex items-center gap-2 justify-end">
              <button data-testid="dnd-bark-cancel" onClick={() => { setActiveSense(null); setActiveLocked(null); }}
                className="px-3 py-1.5 text-xs text-slate-400 hover:bg-slate-800 rounded-lg">Terug</button>
              <button data-testid="dnd-bark-submit" onClick={submit}
                disabled={saving || !content.trim()}
                className="px-4 py-1.5 text-xs font-medium rounded-lg text-white disabled:opacity-40 transition-opacity flex items-center gap-1.5"
                style={{ background: sense.color }}>
                <Save className="w-3.5 h-3.5" /> {saving ? 'Opslaan...' : 'Opslaan als D&D kaart'}
              </button>
            </div>
          </div>
        )}

        {/* Resultaat + lock-knop */}
        {lastSaved && (
          <div data-testid="dnd-bark-result" className="space-y-3">
            <div className="p-3 rounded-xl border-2" style={{ borderColor: lastSaved.color + '60', background: lastSaved.color + '10' }}>
              <div className="flex items-start gap-2">
                <span className="text-2xl">{lastSaved.icon}</span>
                <div className="flex-1">
                  <p className="text-xs font-bold" style={{ color: lastSaved.color }}>{lastSaved.sense_label}</p>
                  <p className="text-sm font-medium text-white mt-0.5">{lastSaved.titel}</p>
                  <p className="text-xs text-slate-300 mt-1.5 whitespace-pre-line">{lastSaved.content}</p>
                </div>
              </div>
              <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/50">
                <p className="text-[10px] text-slate-500">
                  Status: {lastSaved.status === 'locked'
                    ? <span className="text-emerald-400 font-semibold">🔒 LOCKED (canon)</span>
                    : <span className="text-amber-400">draft — nog veranderbaar</span>}
                  <span className="mx-1.5">·</span>
                  KB-lade: {lastSaved.kb_lade}
                </p>
                {lastSaved.status !== 'locked' && (
                  <button data-testid="dnd-bark-lock" onClick={lock} disabled={saving}
                    className="px-3 py-1 text-[11px] font-medium rounded-lg border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/15 flex items-center gap-1">
                    <Lock className="w-3 h-3" /> Vastklikken (canon)
                  </button>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2 justify-end">
              <button data-testid="dnd-bark-new" onClick={start}
                className="px-3 py-1.5 text-xs text-amber-300 border border-amber-500/30 hover:bg-amber-500/10 rounded-lg flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" /> Nieuwe bark
              </button>
              {onClose && (
                <button data-testid="dnd-bark-finish" onClick={onClose}
                  className="px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800 rounded-lg">Klaar</button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer-info */}
      <div className="px-4 py-2 border-t border-slate-800 bg-slate-900/40 flex items-center justify-between text-[10px] text-slate-500">
        <span><Eye className="w-2.5 h-2.5 inline -mt-0.5 mr-1" />
          {session.draft_count} draft · {session.locked_cards?.length || 0} locked
        </span>
        <span>Spark World v0.1 · MVP</span>
      </div>
    </div>
  );
}

/* v6_spark_world_north_001 — sub-locaties lazy-loaden bij travel naar hoofdlocatie */
function SubLocationsList({ locationId, onPick }) {
  const [subs, setSubs] = useState([]);
  useEffect(() => {
    let cancel = false;
    fetch(`${API}/api/dnd/spark-world/locations/${locationId}`)
      .then(r => r.json())
      .then(d => { if (!cancel) setSubs((d.location || {}).sub_locations || []); })
      .catch(() => {});
    return () => { cancel = true; };
  }, [locationId]);
  if (subs.length === 0) return null;
  return (
    <div className="pt-2 border-t border-slate-700/50">
      <p className="text-[9px] uppercase tracking-wider text-slate-500 mb-1">Plekken hier</p>
      <div className="flex flex-wrap gap-1.5">
        {subs.map(s => (
          <button key={s.id} data-testid={`dnd-sublocation-${s.id}`}
            onClick={() => onPick(s.id)}
            className="px-2 py-1 rounded text-[11px] bg-slate-800/60 hover:bg-slate-800 border border-slate-700 text-slate-200 flex items-center gap-1">
            <span>{s.icon}</span> {s.naam}
          </button>
        ))}
      </div>
    </div>
  );
}
