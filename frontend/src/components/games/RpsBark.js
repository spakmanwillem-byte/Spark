/**
 * v6_rps_001 — Steen-Papier-Schaar mini-game bark.
 *
 * Opent via window event 'spark:open-rps' (gedispatched vanuit chat-trigger).
 * Toont KB-kaarten als keuze-thumbnails, score, en learning-indicator.
 */
import React, { useState, useEffect, useRef } from 'react';
import { X, RotateCcw, Trophy, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const LABEL = { steen: 'Steen', papier: 'Papier', schaar: 'Schaar' };

export function RpsBark({ userId, open, onClose }) {
  const [cards, setCards] = useState(null);
  const [session, setSession] = useState({ wins: 0, losses: 0, ties: 0, current_streak: 0 });
  const [lifetime, setLifetime] = useState({ wins: 0, losses: 0, longest_streak: 0 });
  const [lastRound, setLastRound] = useState(null); // {player_choice, spark_choice, outcome, xp_delta, new_achievements, spark_is_learning}
  const [thinking, setThinking] = useState(false);
  const [playerPick, setPlayerPick] = useState(null);

  // Init: load cards + session + stats
  useEffect(() => {
    if (!open) return;
    fetch(`${API}/api/games/rps/cards`).then(r => r.json()).then(d => setCards(d.cards));
    fetch(`${API}/api/games/rps/session?user_id=${userId}`).then(r => r.json()).then(d => setSession(d.session || {}));
    fetch(`${API}/api/games/rps/stats?user_id=${userId}`).then(r => r.json()).then(d => setLifetime(d.stats || {}));
  }, [open, userId]);

  const play = async (choice) => {
    if (thinking) return;
    setPlayerPick(choice);
    setThinking(true);
    setLastRound(null);
    // Simulate "Spark denkt na..." for 800ms
    setTimeout(async () => {
      try {
        const r = await fetch(`${API}/api/games/rps/play`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, choice }),
        }).then(x => x.json());
        if (!r.success && r.detail) { toast.error(r.detail); return; }
        setSession(r.session || session);
        setLifetime({ wins: r.lifetime_wins, losses: r.lifetime_losses, ties: r.lifetime_ties, longest_streak: r.longest_streak });
        setLastRound(r);
        // Achievement-toasts
        (r.new_achievements || []).forEach(a => {
          toast.success(`🏆 ${a.title} (+${a.bonus_xp} XP)`, { description: a.text, duration: 5000 });
        });
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

  return (
    <div data-testid="rps-bark" className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4" onClick={stopGame}>
      <div className="relative max-w-2xl w-full bg-slate-900 border-2 border-amber-500/40 rounded-2xl shadow-2xl ring-2 ring-amber-500/20 overflow-hidden"
        onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500/20 via-rose-500/15 to-cyan-500/20 px-5 py-3 border-b border-amber-500/30 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-300" />
            <h2 className="text-base font-bold text-amber-100">Steen — Papier — Schaar</h2>
          </div>
          <button data-testid="rps-close" onClick={stopGame} className="text-amber-200 hover:text-white p-1.5 rounded-full bg-slate-800/60">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Score-bar */}
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

        {/* Game area */}
        <div className="p-5 space-y-4">
          {/* Spark status */}
          <div className="text-center">
            {thinking ? (
              <p className="text-sm text-amber-300 italic animate-pulse">Spark denkt na…</p>
            ) : lastRound ? (
              <div className="space-y-2">
                <div className="flex items-center justify-center gap-6">
                  <ChoiceBadge label="Jij" choice={lastRound.player_choice} cards={cards} />
                  <span className="text-2xl">vs</span>
                  <ChoiceBadge label="Spark" choice={lastRound.spark_choice} cards={cards} />
                </div>
                {outcomeCard && (
                  <div className="flex items-center justify-center gap-2 pt-1">
                    <img src={`${API}${outcomeCard.image}`} alt={lastRound.outcome}
                      className="w-16 h-16 rounded-lg object-cover ring-2 ring-amber-400/50" />
                    <div className="text-left">
                      <p className={`text-sm font-bold ${lastRound.outcome === 'gewonnen' ? 'text-emerald-300' : lastRound.outcome === 'verloren' ? 'text-rose-300' : 'text-slate-300'}`}>
                        {lastRound.outcome === 'gewonnen' ? 'Je hebt gewonnen!'
                         : lastRound.outcome === 'verloren' ? 'Je hebt verloren'
                         : 'Gelijkspel'}
                      </p>
                      {lastRound.xp_delta > 0 && <p className="text-[11px] text-amber-300">+{lastRound.xp_delta} XP</p>}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-400">Kies je zet hieronder.</p>
            )}
          </div>

          {/* Choice buttons */}
          <div className="grid grid-cols-3 gap-3">
            {['steen', 'papier', 'schaar'].map(c => (
              <button
                key={c}
                data-testid={`rps-pick-${c}`}
                onClick={() => play(c)}
                disabled={thinking}
                className={`flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all
                  ${playerPick === c ? 'border-amber-400 bg-amber-500/20 scale-95'
                    : 'border-slate-700 bg-slate-800/50 hover:border-amber-500/60 hover:bg-slate-800 hover:scale-105'}
                  disabled:opacity-40 disabled:cursor-not-allowed`}>
                {cards[c]?.image ? (
                  <img src={`${API}${cards[c].image}`} alt={c} className="w-20 h-20 object-cover rounded-lg" />
                ) : (
                  <div className="w-20 h-20 bg-slate-700 rounded-lg flex items-center justify-center text-3xl">?</div>
                )}
                <span className="text-xs text-slate-200 font-semibold">{LABEL[c]}</span>
              </button>
            ))}
          </div>

          {/* Lifetime stats */}
          <div className="border-t border-slate-800 pt-3 flex items-center justify-between text-[11px] text-slate-400">
            <span className="flex items-center gap-1">
              <Trophy className="w-3 h-3 text-amber-400" />
              <strong className="text-slate-200" data-testid="rps-lifetime-wins">{lifetime.wins || 0}</strong> totaal gewonnen
              · <strong className="text-slate-300" data-testid="rps-lifetime-losses">{lifetime.losses || 0}</strong> verloren
              {lifetime.longest_streak > 0 && (
                <> · langste streak <strong className="text-amber-300">{lifetime.longest_streak}</strong></>
              )}
            </span>
            <span className={lastRound?.spark_is_learning ? 'text-cyan-400' : 'text-purple-400'}>
              {lastRound?.spark_is_learning ? '🧠 Spark leert nog' : '⚡ Spark heeft je door'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function ChoiceBadge({ label, choice, cards }) {
  const card = cards[choice];
  return (
    <div className="flex flex-col items-center gap-1">
      <p className="text-[10px] uppercase text-slate-500 tracking-wider">{label}</p>
      {card?.image ? (
        <img src={`${API}${card.image}`} alt={choice} className="w-14 h-14 object-cover rounded-lg ring-1 ring-slate-700" />
      ) : (
        <div className="w-14 h-14 bg-slate-700 rounded-lg flex items-center justify-center text-2xl">?</div>
      )}
      <span className="text-[10px] text-slate-300 capitalize">{choice}</span>
    </div>
  );
}

export default RpsBark;
