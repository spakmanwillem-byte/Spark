/**
 * v6_rps_001 — Steen-Papier-Schaar mini-game bark.
 *
 * Opent via window event 'spark:open-rps' (gedispatched vanuit chat-trigger).
 * Toont KB-kaarten als keuze-thumbnails, score, en learning-indicator.
 */
import React, { useState, useEffect } from 'react';
import { X, RotateCcw, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { UserAvatar } from '../common/UserAvatar';

const API = process.env.REACT_APP_BACKEND_URL;

const LABEL = { steen: 'Steen', papier: 'Papier', schaar: 'Schaar' };

// v6_rps_layout_002 — Cached user-lookup voor avatar
const _userCache = {};
async function fetchUserById(uid) {
  if (!uid) return null;
  if (_userCache[uid]) return _userCache[uid];
  try {
    const r = await fetch(`${API}/api/auth/users/${uid}`);
    if (!r.ok) return null;
    const d = await r.json();
    const u = d.user || d;
    _userCache[uid] = u;
    return u;
  } catch { return null; }
}

export function RpsBark({ userId, open, onClose, opponent = 'spark', dailyMode = false, onDailyPlayed = null }) {
  const [cards, setCards] = useState(null);
  const [session, setSession] = useState({ wins: 0, losses: 0, ties: 0, current_streak: 0 });
  const [lifetime, setLifetime] = useState({ wins: 0, losses: 0, longest_streak: 0 });
  const [lastRound, setLastRound] = useState(null);
  const [thinking, setThinking] = useState(false);
  const [playerPick, setPlayerPick] = useState(null);
  const [dailyPlayed, setDailyPlayed] = useState(false);  // v11_daily_rps_001 — daily-mode: after play, disable
  // v6_rps_layout_002 — Avatars voor zijkant
  const [playerUser, setPlayerUser] = useState(null);
  const [opponentUser, setOpponentUser] = useState(null);

  // v6_rps_001b — Init: start nieuwe sessie met juiste opponent + load stats
  // v11_daily_rps_001 — dailyMode: haal KB-cards op (voor thumbnails) MAAR gebruik daily-event endpoints
  useEffect(() => {
    if (!open) return;
    if (dailyMode) {
      // Alleen cards ophalen (via games/rps/start) om KB-kaart plaatjes te tonen.
      // Sessie-side-effect is prima — daily-play zelf gebruikt andere backend.
      fetch(`${API}/api/games/rps/start?user_id=${userId}&opponent=spark`, { method: 'POST' })
        .then(r => r.json())
        .then(d => setCards(d.cards));
      // Check of vandaag al gespeeld
      fetch(`${API}/api/dnd/daily-event/${userId}`)
        .then(r => r.json())
        .then(d => {
          if (d.played) {
            setDailyPlayed(true);
            setLastRound({
              outcome: d.result === 'win' ? 'gewonnen' : (d.result === 'draw' ? 'gelijkspel' : 'verloren'),
              player_choice: d.choice,
              opponent_choice: d.ai_choice,
              xp_delta: d.reward_goud || 0,
              bark: `Je hebt vandaag al gespeeld: ${d.result}. Kom morgen terug.`,
            });
          }
        });
      fetchUserById(userId).then(u => setPlayerUser(u));
      fetchUserById('user-000').then(u => setOpponentUser(u));
    } else {
      fetch(`${API}/api/games/rps/start?user_id=${userId}&opponent=${opponent}`, { method: 'POST' })
        .then(r => r.json())
        .then(d => {
          setCards(d.cards);
          setSession(d.session || {});
          if (d.session?.opponent && d.session.opponent !== opponent) {
            fetchUserById(d.session.opponent).then(u => setOpponentUser(u));
          }
        });
      fetch(`${API}/api/games/rps/stats?user_id=${userId}`).then(r => r.json()).then(d => setLifetime(d.stats || {}));
      fetchUserById(userId).then(u => setPlayerUser(u));
      const oppId = opponent === 'spark' ? 'user-000' : opponent;
      fetchUserById(oppId).then(u => setOpponentUser(u));
    }
  }, [open, userId, opponent, dailyMode]);

  const play = async (choice) => {
    if (thinking) return;
    if (dailyMode && dailyPlayed) return;
    setPlayerPick(choice);
    setThinking(true);
    setLastRound(null);
    // Simulate "Spark denkt na..." for 800ms
    setTimeout(async () => {
      try {
        if (dailyMode) {
          // v11_daily_rps_001 — daily-event backend (1× per dag + goud-uitkering)
          const r = await fetch(`${API}/api/dnd/daily-event/${userId}/play`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ choice }),
          }).then(x => x.json());
          if (r.detail) { toast.error(r.detail); return; }
          setLastRound({
            outcome: r.result === 'win' ? 'gewonnen' : (r.result === 'draw' ? 'gelijkspel' : 'verloren'),
            player_choice: r.choice,
            opponent_choice: r.ai_choice,
            xp_delta: r.reward_goud || 0,
            bark: r.bark,
          });
          setDailyPlayed(true);
          if (r.result === 'win' && r.reward_goud > 0) {
            toast.success(`🏆 +${r.reward_goud} goud`, { description: r.bark, duration: 4000 });
          }
          onDailyPlayed?.(r);
          return;
        }
        const r = await fetch(`${API}/api/games/rps/play`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, choice }),
        }).then(x => x.json());
        if (!r.success && r.detail) { toast.error(r.detail); return; }
        setSession(r.session || session);
        setLifetime({
          wins: r.lifetime_wins, losses: r.lifetime_losses, ties: r.lifetime_ties,
          longest_streak: r.longest_streak,
          battles_won: r.battles_won, battles_lost: r.battles_lost,
          gold: r.gold,
        });
        setLastRound(r);
        // Achievement-toasts
        (r.new_achievements || []).forEach(a => {
          toast.success(`🏆 ${a.title} (+${a.bonus_xp} XP)`, { description: a.text, duration: 5000 });
        });
        // v6_rps_battle_001 — Battle-toast (elke 10 rondes)
        if (r.battle_event) {
          const e = r.battle_event;
          if (e.won) {
            toast.success(`⚔️ Battle ${e.battle_index} gewonnen! ${e.wins_in_battle}/10 wins → +${e.gold_delta} goud`, {
              description: `Saldo: ${e.new_gold} goud`, duration: 6000,
            });
          } else {
            toast(`💔 Battle ${e.battle_index} verloren — ${e.wins_in_battle}/10 wins. Geen goud.`, {
              description: 'Volgende keer beter!', duration: 4500,
            });
          }
        }
      } catch (e) {
        toast.error('Spel-fout: ' + e.message);
      } finally {
        setThinking(false);
        setPlayerPick(null);
      }
    }, 800);
  };

  const resetScore = async () => {
    const r = await fetch(`${API}/api/games/rps/reset?user_id=${userId}`, { method: 'POST' }).then(x => x.json());
    setSession(r.session || {});
    setLastRound(null);
    toast.info('Sessie-score gereset (lifetime stats blijven staan)');
  };

  const stopGame = async () => {
    await fetch(`${API}/api/games/rps/stop?user_id=${userId}`, { method: 'POST' });
    onClose?.();
  };

  if (!open || !cards) return null;

  const outcomeCard = lastRound?.outcome === 'gewonnen' ? cards.gewonnen
                    : lastRound?.outcome === 'verloren' ? cards.verloren : null;
  // v6_rps_001b — Toon huidige tegenstander (Spark of bot-naam)
  const opp = lastRound?.opponent || session.opponent || opponent;
  const OPP_LABEL = {
    'spark': 'Spark',
    'bot-dood': 'De Dood 💀',
    'bot-madelief': 'Madelief',
    'bot-harry': 'Harry',
    'bot-smith': 'Smith',
    'bot-boekhouder': 'Boekhouder',
  };
  const oppLabel = OPP_LABEL[opp] || opp;

  return (
    <div data-testid="rps-bark" className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4" onClick={stopGame}>
      <div className="relative max-w-2xl w-full bg-slate-900 border-2 border-amber-500/40 rounded-2xl shadow-2xl ring-2 ring-amber-500/20 overflow-hidden"
        onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500/20 via-rose-500/15 to-cyan-500/20 px-5 py-3 border-b border-amber-500/30 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-300" />
            <h2 className="text-base font-bold text-amber-100">
              {dailyMode ? '⚔ Vecht voor je leven' : 'Steen — Papier — Schaar'}
            </h2>
            <span data-testid="rps-opponent-label" className="text-[11px] text-amber-200/80">
              · vs <strong>{oppLabel}</strong>
            </span>
          </div>
          <button data-testid="rps-close" onClick={dailyMode ? onClose : stopGame} className="text-amber-200 hover:text-white p-1.5 rounded-full bg-slate-800/60">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Score-bar — verborgen in daily-mode (1 ronde, geen sessie-stats) */}
        {!dailyMode && (
          <div className="px-5 py-3 bg-slate-950/50 border-b border-slate-800 flex items-center justify-between text-xs">
            <div className="flex gap-4">
              <span className="text-emerald-300" data-testid="rps-session-wins">✓ Win <strong>{session.wins || 0}</strong></span>
              <span className="text-rose-300"   data-testid="rps-session-losses">✗ Loss <strong>{session.losses || 0}</strong></span>
              <span className="text-slate-400"  data-testid="rps-session-ties">= Gelijk <strong>{session.ties || 0}</strong></span>
              {session.current_streak > 1 && (
                <span className="text-amber-300">🔥 Streak <strong>{session.current_streak}</strong></span>
              )}
            </div>
            <button data-testid="rps-reset" onClick={resetScore}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700">
              <RotateCcw className="w-3 h-3" /> Reset
            </button>
          </div>
        )}
        {dailyMode && (
          <div className="px-5 py-2 bg-rose-950/30 border-b border-rose-500/30 text-[11px] text-amber-100 italic text-center">
            {dailyPlayed
              ? 'Vandaag al gespeeld — kom morgen terug voor een nieuwe kans op 10 goud.'
              : 'Eén ronde. Win: +10 goud. Verlies: geen straf. Kom morgen terug.'}
          </div>
        )}

        {/* Game area — v6_rps_layout_002 — 3-koloms layout */}
        <div className="p-5">
          {/* Top rij: [Opponent avatar] [Midden status] [User avatar] */}
          <div className="grid grid-cols-[1fr_1.4fr_1fr] gap-4 items-center mb-4">

            {/* LINKS — Tegenstander avatar */}
            <div data-testid="rps-opponent-avatar-block" className="flex flex-col items-center gap-2 p-3 rounded-xl bg-slate-800/40 border border-slate-700/50">
              <UserAvatar
                user={opponentUser || { id: opponent, naam: oppLabel }}
                size="xl" rounded="rounded-2xl"
              />
              <p className="text-xs font-bold text-amber-200 text-center truncate w-full">{oppLabel}</p>
              {lastRound?.opponent_choice && (
                <div className="flex items-center gap-1.5 mt-1 px-2 py-1 rounded-md bg-slate-900/60">
                  {cards[lastRound.opponent_choice]?.image ? (
                    <img src={`${API}${cards[lastRound.opponent_choice].image}`} alt={lastRound.opponent_choice}
                      className="w-8 h-8 rounded object-cover" />
                  ) : null}
                  <span className="text-[10px] text-slate-300 capitalize">{lastRound.opponent_choice}</span>
                </div>
              )}
            </div>

            {/* MIDDEN — Status: denkt na / outcome */}
            <div className="flex flex-col items-center justify-center min-h-[140px]">
              {thinking ? (
                // "Denkt na" KB-kaart — laat afbeelding zien, niet alleen tekst
                <div className="flex flex-col items-center gap-2 animate-pulse">
                  {cards.denkt_na?.image ? (
                    <img src={`${API}${cards.denkt_na.image}`} alt="Denkt na"
                      className="w-24 h-24 rounded-xl object-cover ring-2 ring-amber-400/40" />
                  ) : (
                    <div className="w-24 h-24 rounded-xl bg-slate-700/40 flex items-center justify-center text-4xl">?</div>
                  )}
                  <p className="text-xs text-amber-300 italic">{oppLabel} denkt na…</p>
                </div>
              ) : outcomeCard ? (
                // Gewonnen/verloren-kaart afbeelding centraal
                <div className="flex flex-col items-center gap-2">
                  <img src={`${API}${outcomeCard.image}`} alt={lastRound.outcome}
                    className="w-24 h-24 rounded-xl object-cover ring-2 ring-amber-400/50" />
                  <p className={`text-sm font-bold ${lastRound.outcome === 'gewonnen' ? 'text-emerald-300' : 'text-rose-300'}`}>
                    {lastRound.outcome === 'gewonnen' ? 'Gewonnen!' : 'Verloren'}
                  </p>
                  {lastRound.xp_delta > 0 && <p className="text-[11px] text-amber-300">+{lastRound.xp_delta} XP</p>}
                </div>
              ) : lastRound?.outcome === 'gelijkspel' ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="text-3xl">🤝</div>
                  <p className="text-sm text-slate-300 font-medium">Gelijkspel</p>
                  <p className="text-[11px] text-amber-300">+{lastRound.xp_delta} XP</p>
                </div>
              ) : (
                // Idle: "VS" indicator
                <div className="flex flex-col items-center gap-2">
                  {cards.maak_een_keus?.image ? (
                    <img src={`${API}${cards.maak_een_keus.image}`} alt="Maak een keus"
                      className="w-20 h-20 rounded-xl object-cover opacity-60" />
                  ) : (
                    <div className="text-3xl text-slate-500">VS</div>
                  )}
                  <p className="text-[11px] text-slate-400">Maak je keuze</p>
                </div>
              )}
            </div>

            {/* RECHTS — User avatar */}
            <div data-testid="rps-player-avatar-block" className="flex flex-col items-center gap-2 p-3 rounded-xl bg-slate-800/40 border border-amber-500/30">
              <UserAvatar
                user={playerUser || { id: userId, naam: 'Jij' }}
                size="xl" rounded="rounded-2xl"
              />
              <p className="text-xs font-bold text-amber-100 text-center truncate w-full">{playerUser?.naam || 'Jij'}</p>
              {lastRound?.player_choice && (
                <div className="flex items-center gap-1.5 mt-1 px-2 py-1 rounded-md bg-slate-900/60">
                  {cards[lastRound.player_choice]?.image ? (
                    <img src={`${API}${cards[lastRound.player_choice].image}`} alt={lastRound.player_choice}
                      className="w-8 h-8 rounded object-cover" />
                  ) : null}
                  <span className="text-[10px] text-slate-300 capitalize">{lastRound.player_choice}</span>
                </div>
              )}
            </div>
          </div>

          {/* Choice buttons */}
          <div className="grid grid-cols-3 gap-3">
            {['steen', 'papier', 'schaar'].map(c => (
              <button
                key={c}
                data-testid={`rps-pick-${c}`}
                onClick={() => play(c)}
                disabled={thinking || (dailyMode && dailyPlayed)}
                className={`flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all
                  ${playerPick === c ? 'border-amber-400 bg-amber-500/20 scale-95'
                    : 'border-slate-700 bg-slate-800/50 hover:border-amber-500/60 hover:bg-slate-800 hover:scale-105'}
                  disabled:opacity-40 disabled:cursor-not-allowed`}>
                {cards[c]?.image ? (
                  <div className="w-20 h-20 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
                    <img src={`${API}${cards[c].image}`} alt={c} loading="eager"
                      className="w-full h-full object-cover" />
                  </div>
                ) : (
                  <div className="w-20 h-20 bg-slate-700 rounded-lg flex items-center justify-center text-3xl">?</div>
                )}
                <span className="text-xs text-slate-200 font-semibold">{LABEL[c]}</span>
              </button>
            ))}
          </div>

          {/* Lifetime stats — v6_rps_battle_001 — toont nu ook battles + goud */}
          {!dailyMode && (
          <div className="mt-4 border-t border-slate-800 pt-3 flex items-center justify-between flex-wrap gap-y-2 text-[11px] text-slate-400">
            <span className="flex items-center gap-3 flex-wrap">
              <span className="flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-400" />
                <strong className="text-slate-200" data-testid="rps-lifetime-wins">{lifetime.wins || 0}</strong> gew.
                <span className="text-slate-600 mx-0.5">·</span>
                <strong className="text-slate-300" data-testid="rps-lifetime-losses">{lifetime.losses || 0}</strong> verl.
              </span>
              <span className="flex items-center gap-1" data-testid="rps-battles">
                <span className="text-amber-400">⚔️</span>
                <strong className="text-emerald-300">{lifetime.battles_won || 0}</strong>
                <span className="text-slate-600">/</span>
                <strong className="text-rose-300">{lifetime.battles_lost || 0}</strong>
                <span className="text-[9px] text-slate-500">battles</span>
              </span>
              <span className="flex items-center gap-1" data-testid="rps-gold">
                <span className="text-yellow-400">🪙</span>
                <strong className="text-yellow-300">{lifetime.gold ?? 1000}</strong>
                <span className="text-[9px] text-slate-500">goud</span>
              </span>
              {lifetime.longest_streak > 1 && (
                <span className="text-[10px] text-amber-300">🔥 streak {lifetime.longest_streak}</span>
              )}
            </span>
            <span className={lastRound?.spark_is_learning ? 'text-cyan-400' : 'text-purple-400'}>
              {lastRound?.spark_is_learning ? `🧠 ${oppLabel} leert nog` : `⚡ ${oppLabel} heeft je door`}
            </span>
          </div>
          )}
          {/* Daily-mode: bark tonen na play */}
          {dailyMode && dailyPlayed && lastRound?.bark && (
            <div className="mt-4 p-3 rounded-lg bg-slate-900/60 border border-amber-500/30">
              <p className="text-xs text-amber-100 italic text-center">{lastRound.bark}</p>
              {lastRound.xp_delta > 0 && (
                <p className="mt-1 text-center text-yellow-300 text-sm font-mono font-bold">+{lastRound.xp_delta} goud</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ChoiceBadge() { return null; } // v6_rps_layout_002 — niet meer gebruikt, behouden voor backwards-import compat
export { ChoiceBadge };

export default RpsBark;
