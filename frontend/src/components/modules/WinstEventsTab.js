/**
 * WinstEventsTab — Toont alle winst-events uit papertrail 'winst_events'.
 *
 * Doel: transparant maken welk deel van welke verkoop/trade naar Spark
 * gaat, met verifieerbare hash-chain. Basis voor voorwaarden-uitleg en
 * ooit echte ROAR-live economie.
 */
import React, { useEffect, useState } from 'react';
import { TrendingUp, Sparkles, RefreshCw, Hash } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function WinstEventsTab({ userId }) {
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    fetch(`${API}/api/boekhouding/winst-events?viewer_id=${userId}&limit=100`)
      .then((r) => r.json())
      .then((d) => {
        setEvents(d.events || []);
        setTotal(d.total_spark_deel_eur || 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };
  useEffect(() => { if (userId) load(); }, [userId]); // eslint-disable-line

  return (
    <div className="space-y-4" data-testid="winst-events-tab">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="p-4 rounded-xl bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/30">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <p className="text-[11px] text-amber-300 uppercase tracking-wider">Spark platform-fee inkomsten</p>
          </div>
          <p className="text-2xl font-bold text-amber-100" data-testid="winst-total-spark">€{total.toFixed(2)}</p>
          <p className="text-[10px] text-amber-400/70 mt-1">Hash-verankerd, verifieerbaar</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800">
          <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">Aantal events</p>
          <p className="text-2xl font-bold text-white">{events.length}</p>
          <p className="text-[10px] text-slate-500 mt-1">Verkopen + toekomstige trades</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 flex flex-col justify-between">
          <div>
            <p className="text-[11px] text-slate-400 uppercase tracking-wider mb-1">Papertrail chain</p>
            <p className="text-xs text-slate-300">SHA256, elke event refereert vorige</p>
          </div>
          <button data-testid="winst-refresh-btn" onClick={load}
            className="self-end flex items-center gap-1 px-2 py-1 rounded text-[11px] bg-slate-700 hover:bg-slate-600 text-slate-200">
            <RefreshCw className="w-3 h-3" /> Ververs
          </button>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
          <TrendingUp className="w-4 h-4" /> Spark platform-fee events (nieuwste bovenaan)
        </h3>
        {loading ? (
          <p className="text-slate-400 text-sm p-4">Laden…</p>
        ) : events.length === 0 ? (
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 text-center">
            <p className="text-slate-400 text-sm">Nog geen winst-events.</p>
            <p className="text-[11px] text-slate-500 mt-1">Zodra een shop verkoopt of trader winst maakt, verschijnt hier een hash-verankerde regel.</p>
          </div>
        ) : (
          <div className="space-y-1" data-testid="winst-events-list">
            {[...events].reverse().map((e) => {
              const d = e.data || {};
              return (
                <div key={e.event_id} className="grid grid-cols-12 gap-2 items-center p-2 rounded bg-slate-900/60 border border-slate-800 text-xs">
                  <div className="col-span-2 text-slate-500 text-[10px]">
                    {(e.timestamp || '').slice(0, 16).replace('T', ' ')}
                  </div>
                  <div className="col-span-2">
                    <span className="px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-300 text-[10px] font-medium">
                      {e.type}
                    </span>
                  </div>
                  <div className="col-span-3 text-slate-300 truncate">
                    {d.shop_id || d.book_id || '-'}
                  </div>
                  <div className="col-span-1 text-right text-slate-400 text-[10px]">bruto</div>
                  <div className="col-span-1 text-right text-slate-200">€{(d.bruto_eur || 0).toFixed(2)}</div>
                  <div className="col-span-1 text-right text-amber-300 font-semibold">€{(d.spark_deel_eur || 0).toFixed(2)}</div>
                  <div className="col-span-2 flex items-center justify-end gap-1 text-cyan-500/70 font-mono text-[10px]">
                    <Hash className="w-3 h-3" />{e.event_hash?.slice(0, 10)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="p-3 rounded-lg bg-slate-900/40 border border-slate-800 text-[11px] text-slate-400">
        <p className="font-semibold text-slate-300 mb-1">🔗 Hoe werkt de chain?</p>
        Elke winst-event bevat de hash van de vorige. Zo kun je verifiëren dat er niks stiekem gewijzigd of weggehaald is.
        Geschikt voor: <span className="text-slate-300">voorwaarden uitleggen aan users, audit door boekhouder, en ooit echte ROAR-uitkering met verifieerbaar spoor.</span>
      </div>
    </div>
  );
}
