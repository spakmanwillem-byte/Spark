/**
 * v10_sandbox_llm_token_widget_001 — LLM token-usage widget.
 * v13_llm_usage_tracker_001 (sessie 53) — endpoint /api/chat/llm/usage/today is live.
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
        // v13: endpoint zit onder chat-router → /api/chat/llm/usage/today
        const r = await fetch(`${API}/api/chat/llm/usage/today`).then(x => x.ok ? x.json() : null);
        if (!cancelled) setUsage(r);
      } catch { /* niet fataal */ }
      try {
        const c = await fetch(`${API}/api/chat/llm/cache/stats`).then(x => x.ok ? x.json() : null);
        if (!cancelled) setCache(c);
      } catch { /* ignore */ }
      if (!cancelled) setLoading(false);
    })();
    // Auto-refresh elke 30s zodat je live ziet wanneer een lijn vol raakt
    const iv = setInterval(async () => {
      try {
        const r = await fetch(`${API}/api/chat/llm/usage/today`).then(x => x.ok ? x.json() : null);
        if (!cancelled && r) setUsage(r);
      } catch { /* ignore */ }
    }, 30000);
    return () => { cancelled = true; clearInterval(iv); };
  }, [API]);

  const providers = usage?.providers || [
    // Fallback als endpoint tijdelijk niet reachable is
    { naam: 'Groq (openai/gpt-oss-120b)', used: null, limit: 200000, tier: 'on_demand', note: 'geen data — endpoint niet bereikbaar' },
    { naam: 'Cerebras (gpt-oss-120b)', used: null, limit: null, tier: 'quota', note: 'geen data' },
    { naam: 'Emergent LLM Key', used: null, limit: null, tier: 'noodrem', note: 'activeert alleen bij écht nood' },
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
              ) : p.last_error ? (
                // v13c_llm_failure_log_001 — toon foutstatus in plaats van "geen data"
                <div className="flex items-center gap-1 text-[10px] text-red-300"
                     data-testid={`provider-${i}-error`}>
                  <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                  <span>{p.last_error}</span>
                  {p.failed_calls > 0 && (
                    <span className="text-slate-500 ml-1">({p.failed_calls}× geweigerd)</span>
                  )}
                </div>
              ) : (
                <p className="text-[10px] text-slate-500 italic">{p.note || 'geen data — nog geen call vandaag'}</p>
              )}
            </div>
          );
        })}
      </div>

      <p className="text-[10px] text-slate-600 italic mt-2 leading-snug">
        💡 Live-data via <code className="text-slate-400">/api/chat/llm/usage/today</code>,
        auto-refresh elke 30s. Limits configureerbaar via env <code className="text-slate-400">LLM_*_TPD_LIMIT</code>.
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
