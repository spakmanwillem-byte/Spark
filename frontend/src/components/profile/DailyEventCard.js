/**
 * DailyEventCard — v11_daily_event_rps_001
 *
 * Dagelijks "Vecht voor je leven" — 1× per dag SPS voor 10 goud.
 * Was: eigen minimalistische UI met verkeerde "ontsnapt"-tekst en losse win/loss info.
 * Nu: dunne wrapper die de rijke `RpsBark` component opent met `dailyMode=true`.
 * Backend `/api/dnd/daily-event/*` blijft ongewijzigd (1×/dag gate + goud-uitkering).
 */
import React from 'react';
import { RpsBark } from '../games/RpsBark';

const API = process.env.REACT_APP_BACKEND_URL;

export function DailyEventCard({ userId, onReload }) {
  const [state, setState] = React.useState(null);
  const [open, setOpen] = React.useState(false);

  const load = React.useCallback(() => {
    if (!userId) return;
    fetch(`${API}/api/dnd/daily-event/${userId}`)
      .then(r => r.json()).then(setState).catch(() => {});
  }, [userId]);

  React.useEffect(() => { load(); }, [load]);

  if (!state) return null;

  const palette = state.available
    ? { ring: 'border-rose-500/70', bg: 'from-rose-950/40 to-stone-950', accent: 'text-rose-300' }
    : { ring: 'border-stone-700', bg: 'from-stone-900 to-stone-950', accent: 'text-stone-400' };

  const icon = state.available ? '⚔' : (state.result === 'win' ? '🏆' : '🌙');

  return (
    <>
      <button
        data-testid="daily-event-card"
        onClick={() => setOpen(true)}
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

      {open && (
        <RpsBark
          userId={userId}
          open={open}
          onClose={() => { setOpen(false); load(); onReload?.(); }}
          dailyMode={true}
          onDailyPlayed={() => { load(); onReload?.(); }}
        />
      )}
    </>
  );
}

export default DailyEventCard;
