// v4_update_bark_001 — Bark queue overlay
// Toont pending barks (privacy + deploy updates) bij login. User klikt door, marked as seen.
import React, { useState, useEffect, useCallback } from 'react';
import { Sparkles, ChevronRight, Shield, Rocket, Star, X, Hand } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const KIND_STYLES = {
  privacy: { icon: Shield, accent: '#06b6d4', tag: 'PRIVACY' },
  deploy: { icon: Rocket, accent: '#f59e0b', tag: 'UPDATE' },
  feature: { icon: Star, accent: '#a855f7', tag: 'FEATURE' },
  welcome: { icon: Hand, accent: '#10b981', tag: 'WELKOM' },
};

export function BarkQueueOverlay({ userId, onAllSeen }) {
  const [queue, setQueue] = useState([]);
  const [active, setActive] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!userId) return;
    try {
      const r = await fetch(`${API}/api/deploy/pending/${userId}`);
      const d = await r.json();
      setQueue(d.pending || []);
      if ((d.pending || []).length > 0) {
        setActive(d.pending[0]);
      } else {
        onAllSeen && onAllSeen();
      }
    } catch {}
  }, [userId, onAllSeen]);

  useEffect(() => { load(); }, [load]);

  const dismiss = async () => {
    if (!active) return;
    setBusy(true);
    try {
      await fetch(`${API}/api/deploy/seen`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, bark_id: active.id }),
      });
      const remaining = queue.filter(b => b.id !== active.id);
      setQueue(remaining);
      if (remaining.length > 0) {
        setActive(remaining[0]);
      } else {
        setActive(null);
        onAllSeen && onAllSeen();
      }
    } finally { setBusy(false); }
  };

  if (!active) return null;
  const style = KIND_STYLES[active.kind] || KIND_STYLES.deploy;
  const Icon = style.icon;
  const total = queue.length;
  const idx = total - queue.indexOf(active);  // 1-based

  return (
    <div data-testid="bark-overlay" className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-300">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-800 relative" style={{ background: `linear-gradient(135deg, ${style.accent}15, transparent)` }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-2xl shadow-lg" style={{ background: `${style.accent}30`, border: `1px solid ${style.accent}80` }}>
              {active.icon || <Icon className="w-5 h-5 text-white" />}
            </div>
            <div className="flex-1">
              <span className="text-[9px] font-bold tracking-widest uppercase" style={{ color: style.accent }}>{style.tag}</span>
              <h2 className="text-lg font-bold text-white leading-tight">{active.title}</h2>
            </div>
            {total > 1 && (
              <div className="text-[10px] text-slate-500 px-2 py-1 bg-slate-800/60 rounded-full">
                {idx} / {total}
              </div>
            )}
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-5">
          <p className="text-sm text-slate-300 whitespace-pre-line leading-relaxed">{active.message}</p>
          {active.roadmap_ref && (
            <p className="mt-3 text-[11px] text-slate-500">
              <span className="opacity-60">Referentie: </span>
              <a href={`/roadmap#${active.roadmap_ref}`} target="_blank" rel="noopener"
                data-testid="bark-roadmap-link"
                className="text-amber-400 font-mono hover:underline">
                {active.roadmap_ref}
              </a>
            </p>
          )}
          {active.anchored_at && (
            <p className="mt-2 text-[10px] text-slate-600">
              {new Date(active.anchored_at).toLocaleString('nl-NL', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
            </p>
          )}
        </div>

        {/* Action */}
        <div className="px-6 py-4 bg-slate-950/50 border-t border-slate-800 flex justify-end gap-2">
          <button onClick={dismiss} disabled={busy} data-testid="bark-dismiss"
            className="px-5 py-2 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2 disabled:opacity-50"
            style={{ background: style.accent }}>
            {total > 1 ? 'Volgende' : (active.kind === 'privacy' ? 'Akkoord' : (active.kind === 'welcome' ? 'Laten we beginnen' : 'Begrepen'))}
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default BarkQueueOverlay;
