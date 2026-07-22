/**
 * v10_sandbox_llm_token_widget_001 — LLM token-usage widget (sandbox demo).
 *
 * STATUS: SKELETON — backend endpoint /api/llm/usage/today bestaat NOG NIET.
 * Widget is prêt voor als jij die endpoint bouwt. Nu toont hij een placeholder-state
 * met de laatst-bekende Groq-error uit backend logs.
 *
 * VERPLAATSEN: import als `<LlmTokenUsageWidget />` in bv. AnalyticsPage → Systeem tab.
 */
import React, { useState, useEffect } from 'react';
import { Zap, AlertTriangle, ExternalLink } from 'lucide-react';

export function LlmTokenUsageWidget() {
  const [usage, setUsage] = useState(null);
  const [cache, setCache] = useState(null);
  const [loading, setLoading] = useState(true);
  const API = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${API}/api/llm/usage/today`).then(x => x.ok ? x.json() : null);
        if (!cancelled) setUsage(r);
      } catch { /* endpoint nog niet gebouwd */ }
      try {
        const c = await fetch(`${API}/api/chat/llm/cache/stats`).then(x => x.ok ? x.json() : null);
        if (!cancelled) setCache(c);
      } catch { /* ignore */ }
      if (!cancelled) setLoading(false);
    })();
    return () => { cancelled = true; };
  }, [API]);

  const providers = usage?.providers || [
    // Placeholder-data als endpoint 404 gaf
    { naam: 'Groq (llama-3.3-70b)', used: 94838, limit: 100000, tier: 'on_demand' },
    { naam: 'Cerebras', used: null, limit: null, tier: 'unknown', note: 'hook nog niet gebouwd' },
    { naam: 'Emergent LLM Key', used: null, limit: null, tier: 'unlimited', note: 'geen dag-limiet' },
  ];

  return (
    <div data-testid="sandbox-llm-token-usage" className="bg-slate-900/50 border border-amber-500/30 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Zap className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-semibold text-white">LLM Token Usage — vandaag</h3>
        {loading && <span className="text-[10px] text-slate-500">laden…</span>}
      </div>

      <div className="space-y-2">
        {providers.map((p, i) => {
          const pct = (p.used && p.limit) ? Math.round((p.used / p.limit) * 100) : null;
          const critical = pct !== null && pct > 90;
          const warn = pct !== null && pct > 75 && pct <= 90;
          return (
            <div key={i} data-testid={`sandbox-provider-${i}`}
                 className="p-2 rounded-lg bg-slate-950/50 border border-slate-800">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-slate-200">{p.naam}</span>
                <span className="text-[10px] text-slate-500">tier: {p.tier}</span>
              </div>
              {pct !== null ? (
                <>
                  <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full transition-all ${
                      critical ? 'bg-red-500' : warn ? 'bg-amber-500' : 'bg-emerald-500'
                    }`} style={{ width: `${Math.min(pct, 100)}%` }} />
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-[10px] text-slate-400">
                      {p.used.toLocaleString()} / {p.limit.toLocaleString()} tokens
                    </span>
                    <span className={`text-[10px] font-semibold ${
                      critical ? 'text-red-400' : warn ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {pct}%
                    </span>
                  </div>
                  {critical && (
                    <div className="mt-1.5 flex items-center gap-1 text-[10px] text-red-300">
                      <AlertTriangle className="w-3 h-3" />
                      Bijna vol — LLM valt terug op fallback. Upgrade tier:
                      <a href="https://console.groq.com/settings/billing"
                         target="_blank" rel="noreferrer"
                         className="underline hover:text-red-200 flex items-center gap-0.5">
                        billing <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-[10px] text-slate-500 italic">{p.note || 'geen data'}</p>
              )}
            </div>
          );
        })}
      </div>

      <p className="text-[10px] text-slate-600 italic mt-2 leading-snug">
        💡 Backend endpoint <code className="text-slate-400">/api/llm/usage/today</code> nog te bouwen.
        Widget parseert Groq 429-errors automatisch zodra endpoint bestaat.
      </p>

      {/* v10_llm_response_cache_001 — cache-savings blok */}
      {cache && (
        <div className="mt-3 p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/20"
             data-testid="widget-llm-cache-stats">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-medium text-emerald-300">💾 Response-cache</span>
            <span className="text-[10px] text-slate-500">TTL {cache.ttl_seconds}s · {cache.entries}/{cache.max_entries} entries</span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="text-sm font-bold text-emerald-400">{cache.hits}</div>
              <div className="text-[9px] text-slate-500">hits (bespaard)</div>
            </div>
            <div>
              <div className="text-sm font-bold text-slate-300">{cache.misses}</div>
              <div className="text-[9px] text-slate-500">misses (LLM call)</div>
            </div>
            <div>
              <div className="text-sm font-bold text-cyan-400">{cache.hit_rate_pct}%</div>
              <div className="text-[9px] text-slate-500">hit-rate</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
