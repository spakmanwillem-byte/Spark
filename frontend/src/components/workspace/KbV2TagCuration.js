/**
 * v6_kb_curation_dashboard_001 — Tag-curation dashboard
 * Bovenop /api/kb/v2/tags/scan + /api/kb/v2/tags/merge
 * 1-klik dedupe voor duplicate tag-varianten (emoties + emotie + Emoties → emotie).
 */
import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { RefreshCw, Tag as TagIcon, Merge, ChevronDown, AlertCircle, CheckCircle2, Search } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function KbV2TagCuration({ viewerId = 'user-001' }) {
  const [loading, setLoading] = useState(true);
  const [scanData, setScanData] = useState(null);
  const [mergingStem, setMergingStem] = useState(null);
  const [chosenVariant, setChosenVariant] = useState({}); // stem → keep_variant
  const [filter, setFilter] = useState('');
  const [mergeHistory, setMergeHistory] = useState([]); // last merges this session

  const loadScan = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/kb/v2/tags/scan?limit=200`).then(x => x.json());
      setScanData(r);
      // Default: keep_variant = de korst-variant (waarschijnlijk de stam)
      const defaults = {};
      (r.top_duplicates || []).forEach(d => {
        const shortest = [...d.variants].sort((a, b) => a.length - b.length)[0];
        defaults[d.stem] = shortest || d.stem;
      });
      setChosenVariant(defaults);
    } catch (e) {
      toast.error('Tag-scan mislukt: ' + e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadScan(); }, [loadScan]);

  const doMerge = async (stem) => {
    const keep = chosenVariant[stem];
    if (!keep) {
      toast.error('Kies eerst welke variant je behoudt');
      return;
    }
    setMergingStem(stem);
    try {
      const r = await fetch(`${API}/api/kb/v2/tags/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stem, keep_variant: keep, viewer_id: viewerId }),
      }).then(x => x.json());
      if (r.success) {
        toast.success(`Merge OK: ${r.tags_replaced} tags vervangen in ${r.cards_touched} kaarten → "${keep}"`, { duration: 5000 });
        setMergeHistory(prev => [{ stem, keep, ...r, ts: new Date().toISOString() }, ...prev].slice(0, 20));
        // Refresh scan
        await loadScan();
      } else {
        toast.error(r.error || 'Merge mislukt');
      }
    } catch (e) {
      toast.error('Merge fout: ' + e.message);
    } finally {
      setMergingStem(null);
    }
  };

  const filtered = (scanData?.top_duplicates || []).filter(d => {
    if (!filter) return true;
    const q = filter.toLowerCase();
    return d.stem.includes(q) || d.variants.some(v => v.toLowerCase().includes(q));
  });

  return (
    <div data-testid="kb-tag-curation" className="space-y-3">
      {/* Stats header */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <StatTile label="Tags gescand" value={scanData?.total_tags_scanned ?? '—'} color="#94a3b8" />
        <StatTile label="Unieke stammen" value={scanData?.unique_stems ?? '—'} color="#06b6d4" />
        <StatTile label="Dedupe-kansen" value={scanData?.stems_with_duplicates ?? '—'} color="#f59e0b" />
        <StatTile label="Sessie-merges" value={mergeHistory.length} color="#22c55e" />
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input data-testid="kb-curation-filter" type="text" value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Filter op stam of variant..."
            className="w-full pl-8 pr-3 py-1.5 bg-slate-900/60 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-amber-500/50" />
        </div>
        <button data-testid="kb-curation-refresh" onClick={loadScan} disabled={loading}
          className="px-3 py-1.5 rounded-lg text-[11px] border border-slate-700 text-slate-300 hover:bg-slate-800 flex items-center gap-1.5 disabled:opacity-50">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Scannen...' : 'Opnieuw scannen'}
        </button>
      </div>

      {/* Info banner */}
      <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 text-[11px] text-amber-200/80 flex gap-2">
        <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-amber-400" />
        <div>
          <p><b className="text-amber-300">Tag-stam = canonieke woord-vorm</b> (emoties/emotie/Emoties → "emotie").
          Kies welke variant je behoudt, daarna 1-klik merge over alle 4 lades. Read-only scan tussen merges.</p>
        </div>
      </div>

      {/* Duplicate list */}
      {loading ? (
        <p className="text-xs text-slate-500 p-6 text-center">Scannen alle KB v2 kaarten...</p>
      ) : filtered.length === 0 ? (
        <div className="p-8 text-center bg-slate-900/40 border border-slate-800 rounded-xl">
          <CheckCircle2 className="w-10 h-10 mx-auto text-green-400/60 mb-2" />
          <p className="text-sm text-slate-300">
            {scanData?.stems_with_duplicates === 0
              ? 'Geen dedupe-kansen meer — alle tags zijn schoon.'
              : 'Geen treffers voor dit filter.'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(d => (
            <DuplicateRow key={d.stem} d={d}
              chosen={chosenVariant[d.stem]}
              onChooseVariant={(v) => setChosenVariant(prev => ({ ...prev, [d.stem]: v }))}
              merging={mergingStem === d.stem}
              onMerge={() => doMerge(d.stem)} />
          ))}
        </div>
      )}

      {/* History */}
      {mergeHistory.length > 0 && (
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3">
          <p className="text-[11px] text-slate-400 font-semibold mb-2 flex items-center gap-1.5">
            <Merge className="w-3.5 h-3.5 text-green-400" /> Recent gemerged (sessie)
          </p>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {mergeHistory.map((h, i) => (
              <div key={i} className="text-[10px] text-slate-400 flex justify-between gap-2 py-0.5">
                <span>
                  <code className="text-amber-300">{h.stem}</code> → <code className="text-green-300">{h.keep}</code>
                </span>
                <span className="text-slate-500">{h.tags_replaced} tags · {h.cards_touched} kaarten</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatTile({ label, value, color }) {
  return (
    <div className="p-2.5 bg-slate-900/40 border border-slate-800 rounded-lg">
      <p className="text-[9px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className="text-lg font-bold" style={{ color }}>{value}</p>
    </div>
  );
}

function DuplicateRow({ d, chosen, onChooseVariant, merging, onMerge }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div data-testid={`kb-curation-row-${d.stem}`}
      className="bg-slate-900/60 border border-slate-800 hover:border-amber-500/30 rounded-lg p-3 transition-colors">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <TagIcon className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
          <code className="text-sm text-amber-300 font-mono">{d.stem}</code>
          <span className="text-[10px] text-slate-500">
            {d.variant_count} varianten · {d.total_occurrences}× gebruikt
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <select data-testid={`kb-curation-keep-${d.stem}`}
            value={chosen || d.variants[0]}
            onChange={e => onChooseVariant(e.target.value)}
            className="px-2 py-1 text-[11px] bg-slate-800 border border-slate-700 rounded text-slate-200 focus:outline-none focus:border-amber-500">
            {d.variants.map(v => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
          <button data-testid={`kb-curation-merge-${d.stem}`}
            onClick={onMerge} disabled={merging}
            className="px-3 py-1 rounded text-[11px] font-medium bg-amber-500 hover:bg-amber-600 text-white disabled:opacity-50 flex items-center gap-1">
            <Merge className="w-3 h-3" />
            {merging ? 'Mergen...' : 'Merge'}
          </button>
          <button onClick={() => setExpanded(e => !e)}
            data-testid={`kb-curation-expand-${d.stem}`}
            className="p-1 rounded border border-slate-700 text-slate-400 hover:text-amber-300">
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>
      {expanded && (
        <div className="mt-2 pt-2 border-t border-slate-800/60 flex flex-wrap gap-1">
          {d.variants.map(v => (
            <button key={v} onClick={() => onChooseVariant(v)}
              className={`px-2 py-0.5 rounded text-[10px] border ${
                chosen === v
                  ? 'bg-amber-500/20 border-amber-500/50 text-amber-200'
                  : 'border-slate-700 text-slate-300 hover:border-amber-500/30'
              }`}>
              {v} {chosen === v && <span className="text-amber-400">✓ behouden</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
