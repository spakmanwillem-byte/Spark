/**
 * v13d_shadow_observer_kladblok_001 (sessie 56) — Willem: "Shadow Observer
 * hoort niet op dashboard, park in Widget Kladblok tot goede plek gevonden."
 *
 * Zelfstandige widget: eigen fetch, eigen render. Copy uit DashboardPage.js
 * met de fetch-hook geïnternaliseerd. Verplaatsen later = 1 import elders.
 */
import React, { useState, useEffect } from 'react';
import { Eye } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

function Stat({ label, value, color }) {
  return (
    <div className="bg-slate-950/40 rounded-md px-2 py-1.5">
      <p className="text-[9px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`text-sm font-bold ${color}`}>{value}</p>
    </div>
  );
}
function UnusedRow({ label, items, total, color }) {
  return (
    <div className="flex items-start gap-2">
      <span className={`${color} font-medium flex-shrink-0`}>{label}:</span>
      <span className="text-slate-400 truncate flex-1">{items.join(', ')}</span>
      {total > items.length && <span className="text-slate-600 text-[9px] flex-shrink-0">+{total - items.length}</span>}
    </div>
  );
}

export function ShadowObserverWidget() {
  const [shadowStats, setShadowStats] = useState(null);
  const [shadowUnused, setShadowUnused] = useState(null);

  useEffect(() => {
    let cancel = false;
    Promise.all([
      fetch(`${API}/api/chat/shadow/stats`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/chat/shadow/unused`).then(r => r.json()).catch(() => null),
    ]).then(([s, u]) => { if (!cancel) { setShadowStats(s); setShadowUnused(u); } });
    return () => { cancel = true; };
  }, []);

  const totals = shadowStats?.totals || {};
  const events = totals.events || 0;
  const corrections = totals.corrections || 0;
  const confirmations = totals.confirmations || 0;
  const fallbacks = totals.fallbacks || 0;
  const matches = totals.knowledge_matches || 0;
  const correctPct = events > 0 ? Math.round((corrections / events) * 100) : 0;
  const fallbackPct = events > 0 ? Math.round((fallbacks / events) * 100) : 0;

  const unusedTriggers = (shadowUnused?.triggers || []).slice(0, 3);
  const unusedVocab = (shadowUnused?.vocab || []).slice(0, 3);
  const unusedBijbel = (shadowUnused?.bijbel || []).slice(0, 3);

  const triggersUsed = shadowStats?.triggers_used || {};
  const topTriggers = Object.entries(triggersUsed).sort((a, b) => b[1] - a[1]).slice(0, 3);

  const lastSeen = shadowStats?.last_event_at
    ? new Date(shadowStats.last_event_at).toLocaleString('nl-NL', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })
    : '—';

  return (
    <div data-testid="shadow-widget" className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2">
          <Eye className="w-3.5 h-3.5 text-emerald-400" />
          <h3 className="text-xs font-semibold text-white">Shadow Observer</h3>
          <span className="text-[9px] text-emerald-300 bg-emerald-500/10 px-1.5 py-0.5 rounded uppercase tracking-wider">live</span>
        </div>
        <span className="text-[9px] text-slate-500">{lastSeen}</span>
      </div>
      <div className="p-3 space-y-3">
        <div className="grid grid-cols-3 gap-2">
          <Stat label="Events" value={events} color="text-white" />
          <Stat label="Correcties" value={`${corrections} (${correctPct}%)`} color="text-amber-300" />
          <Stat label="Fallback" value={`${fallbacks} (${fallbackPct}%)`} color="text-rose-300" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Stat label="Bevestigingen" value={confirmations} color="text-emerald-300" />
          <Stat label="K-matches" value={matches} color="text-blue-300" />
        </div>
        {topTriggers.length > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Top triggers</p>
            <div className="space-y-1">
              {topTriggers.map(([name, count], i) => (
                <div key={i} className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-300 truncate">{name}</span>
                  <span className="text-slate-500 ml-2">×{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {(unusedTriggers.length + unusedVocab.length + unusedBijbel.length) > 0 && (
          <div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Nog niet gebruikt</p>
            <div className="space-y-1 text-[11px]">
              {unusedTriggers.length > 0 && <UnusedRow label="Triggers" items={unusedTriggers} total={shadowUnused?.triggers?.length || 0} color="text-emerald-300" />}
              {unusedVocab.length > 0 && <UnusedRow label="Vocab" items={unusedVocab} total={shadowUnused?.vocab?.length || 0} color="text-purple-300" />}
              {unusedBijbel.length > 0 && <UnusedRow label="Bijbel" items={unusedBijbel} total={shadowUnused?.bijbel?.length || 0} color="text-amber-300" />}
            </div>
          </div>
        )}
        {events === 0 && (
          <p className="text-[10px] text-slate-500 italic text-center py-2">Nog geen chat-events. Praat met Spark om data te verzamelen.</p>
        )}
      </div>
    </div>
  );
}
