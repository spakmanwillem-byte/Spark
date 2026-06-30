/**
 * DailyEventCard — v6_daily_event_001
 *
 * Standalone component: 1× per dag SPS-gevecht voor 10 goud.
 * Geëxtraheerd uit DnDCharacterSheet.js (v6_dndsheet_split_001) zodat het
 * hoofdbestand kleiner blijft. Backend: /api/dnd/daily-event/{user_id}.
 */
import React from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

export function DailyEventCard({ userId, onReload }) {
  const [state, setState] = React.useState(null);
  const [open, setOpen] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [last, setLast] = React.useState(null);

  const load = React.useCallback(() => {
    if (!userId) return;
    fetch(`${API}/api/dnd/daily-event/${userId}`)
      .then(r => r.json()).then(setState).catch(() => {});
  }, [userId]);

  React.useEffect(() => { load(); }, [load]);

  const play = async (choice) => {
    if (busy) return;
    setBusy(true);
    try {
      const r = await fetch(`${API}/api/dnd/daily-event/${userId}/play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ choice }),
      });
      if (r.ok) {
        const d = await r.json();
        setLast(d);
        await load();
        onReload?.();
      }
    } finally {
      setBusy(false);
    }
  };

  if (!state) return null;

  const palette = state.available
    ? { ring: 'border-rose-500/70', bg: 'from-rose-950/40 to-stone-950', accent: 'text-rose-300' }
    : { ring: 'border-stone-700', bg: 'from-stone-900 to-stone-950', accent: 'text-stone-400' };

  const lastResult = last || (state.played ? state : null);
  const icon = lastResult?.result === 'win' ? '🏆' : (state.available ? '⚔' : '🌙');

  return (
    <>
      <button
        data-testid="daily-event-card"
        onClick={() => state.available && setOpen(true)}
        disabled={!state.available}
        className={`w-full text-left rounded-lg border-2 ${palette.ring} bg-gradient-to-r ${palette.bg} p-3 flex items-center gap-3 transition-all ${state.available ? 'hover:scale-[1.01] cursor-pointer shadow-[0_0_18px_rgba(244,63,94,0.25)]' : 'opacity-70 cursor-not-allowed'}`}>
        <div className={`w-10 h-10 rounded-full bg-stone-950/60 border ${palette.ring} flex items-center justify-center text-xl flex-shrink-0`}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[9px] uppercase tracking-[0.25em] text-amber-500/70">Dagelijks event</p>
          <h4 className={`text-sm font-serif font-bold ${palette.accent} leading-tight`}>{state.title}</h4>
          <p className="text-[11px] text-amber-200/70 italic truncate">{state.subtitle}</p>
        </div>
        {state.available && (
          <span className="text-[10px] font-mono text-amber-300 font-bold bg-stone-950/70 px-2 py-1 rounded border border-amber-700/50">
            +{state.win_goud}g
          </span>
        )}
      </button>

      {open && state.available && !last && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setOpen(false)}>
          <div className="bg-stone-950 border-2 border-rose-500/70 rounded-xl p-6 max-w-md w-full shadow-[0_0_50px_rgba(244,63,94,0.4)]" onClick={e => e.stopPropagation()}>
            <h3 className="text-xl font-serif font-bold text-rose-200 text-center mb-1">⚔ Vecht voor je leven ⚔</h3>
            <p className="text-[12px] text-amber-200/80 italic text-center mb-5">{state.subtitle}</p>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: 'steen',   label: 'Steen',   icon: '🪨' },
                { id: 'papier',  label: 'Papier',  icon: '📜' },
                { id: 'schaar',  label: 'Schaar',  icon: '✂' },
              ].map(c => (
                <button key={c.id} data-testid={`sps-choice-${c.id}`}
                  onClick={() => play(c.id)}
                  disabled={busy}
                  className="flex flex-col items-center gap-1 p-4 rounded-lg border-2 border-amber-700/60 bg-stone-900 hover:bg-amber-950/40 hover:border-amber-400 transition-all disabled:opacity-50">
                  <span className="text-3xl">{c.icon}</span>
                  <span className="text-[11px] uppercase tracking-wider text-amber-200">{c.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {open && last && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => { setOpen(false); setLast(null); }}>
          <div className="bg-stone-950 border-2 border-amber-500/70 rounded-xl p-6 max-w-md w-full" onClick={e => e.stopPropagation()}>
            <h3 className={`text-xl font-serif font-bold text-center mb-2 ${
              last.result === 'win' ? 'text-emerald-300'
              : last.result === 'draw' ? 'text-amber-300' : 'text-rose-300'
            }`}>
              {last.result === 'win' ? '🏆 Overwinning!'
                : last.result === 'draw' ? '⚖ Gelijkspel' : '🌫 Ontsnapt'}
            </h3>
            <p className="text-[12px] text-amber-200/90 italic text-center mb-4">{last.bark}</p>
            {last.reward_goud > 0 && (
              <p className="text-center text-amber-300 font-mono font-bold mb-3">+{last.reward_goud} goud</p>
            )}
            <button data-testid="sps-close-result"
              onClick={() => { setOpen(false); setLast(null); }}
              className="w-full mt-2 px-4 py-2 rounded-md border border-amber-600/60 bg-amber-900/40 hover:bg-amber-800/60 text-amber-100 text-sm uppercase tracking-wider font-bold">
              Sluiten
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default DailyEventCard;
