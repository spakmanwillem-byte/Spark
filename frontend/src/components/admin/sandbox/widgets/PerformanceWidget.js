/**
 * v13d_performance_kladblok_001 (sessie 56) — Willem: "Performance-kaart hoort
 * niet op dashboard, park in Widget Kladblok tot goede plek gevonden."
 *
 * Zelfstandige widget: eigen fetch (storage-cache endpoint), eigen render.
 */
import React, { useState, useEffect } from 'react';
import { Gauge } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function PerformanceWidget() {
  const [perfStats, setPerfStats] = useState(null);
  useEffect(() => {
    let cancel = false;
    fetch(`${API}/api/admin/storage-cache`).then(r => r.json())
      .then(d => { if (!cancel) setPerfStats(d); }).catch(() => {});
    return () => { cancel = true; };
  }, []);

  if (!perfStats) {
    return (
      <div className="rounded-2xl p-6 border border-slate-800/50 bg-gradient-to-br from-slate-900/80 to-slate-950/40">
        <p className="text-xs text-slate-500">Performance laden...</p>
      </div>
    );
  }
  const totalMb = perfStats.total_cached_mb || 0;
  const files = perfStats.files || [];
  const handleClear = async () => {
    if (!window.confirm('Cache leegmaken? Volgende request wordt langzamer.')) return;
    await fetch(`${API}/api/admin/storage-cache/clear`, { method: 'POST' });
    window.location.reload();
  };

  return (
    <div data-testid="perf-card" className="rounded-2xl p-6 border border-cyan-500/20 bg-gradient-to-br from-cyan-950/30 to-slate-950/40 hover:border-cyan-500/40 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Gauge className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white">Performance</h3>
        </div>
        <span className="text-[10px] text-cyan-300/70 uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">cache live</span>
      </div>
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="p-3 bg-slate-800/40 rounded-xl">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">In geheugen</p>
          <p className="text-lg font-bold text-cyan-300">{totalMb} <span className="text-xs text-slate-500">MB</span></p>
        </div>
        <div className="p-3 bg-slate-800/40 rounded-xl">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">Files gecached</p>
          <p className="text-lg font-bold text-white">{files.length}</p>
        </div>
      </div>
      <div className="space-y-1.5 max-h-32 overflow-y-auto mb-3">
        {files.map((f, idx) => {
          const naam = (f.path || '').split('/').pop();
          return (
            <div key={idx} className="flex items-center justify-between text-[11px] py-1 border-b border-slate-800/50 last:border-0">
              <span className="text-slate-400 truncate flex-1 font-mono">{naam}</span>
              <span className="text-cyan-300/70 ml-2 flex-shrink-0">{Math.round(f.size_kb)}KB</span>
            </div>
          );
        })}
        {files.length === 0 && <p className="text-[10px] text-slate-600 text-center py-2">Geen cache — eerste request wacht</p>}
      </div>
      <button data-testid="perf-clear-btn" onClick={handleClear}
        className="w-full text-[10px] text-slate-500 hover:text-cyan-300 py-1 rounded border border-slate-800 hover:border-cyan-500/30 transition-colors">
        Cache leegmaken
      </button>
    </div>
  );
}
