import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Calendar, Code2, AlertCircle, Activity, ChevronRight, RefreshCw } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const PHASE_STYLES = {
  pre:   { label: 'pre',   color: '#94a3b8', icon: ChevronRight },
  post:  { label: 'post',  color: '#22c55e', icon: Activity },
  error: { label: 'error', color: '#ef4444', icon: AlertCircle },
  event: { label: 'event', color: '#3b82f6', icon: FileText },
};

/**
 * LogsBrowser (v5_spark_logger_001)
 * ---------------------------------
 * Beheer → Archief → Logs:
 *   • Linkernavigatie: jaar → maand → dag → module
 *   • Rechts: laatste 200 records (pre/post/error/event) met intent, duration en result-summary
 */
export function LogsBrowser() {
  const [tree, setTree] = useState({});
  const [retentionDays, setRetentionDays] = useState(28);
  const [loadingIndex, setLoadingIndex] = useState(true);
  const [selectedDate, setSelectedDate] = useState(null);   // 'YYYY-MM-DD'
  const [selectedModule, setSelectedModule] = useState(null);
  const [phaseFilter, setPhaseFilter] = useState('');
  const [records, setRecords] = useState([]);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [total, setTotal] = useState(0);

  const loadIndex = useCallback(async () => {
    setLoadingIndex(true);
    try {
      const r = await fetch(`${API}/api/admin/logs/index`).then(x => x.json());
      setTree(r.tree || {});
      setRetentionDays(r.retention_days || 28);
    } catch {}
    setLoadingIndex(false);
  }, []);

  useEffect(() => { loadIndex(); }, [loadIndex]);

  // Bij eerste load: kies meest recente dag + eerste module
  useEffect(() => {
    if (selectedDate || Object.keys(tree).length === 0) return;
    const years = Object.keys(tree).sort().reverse();
    for (const y of years) {
      const months = Object.keys(tree[y] || {}).sort().reverse();
      for (const m of months) {
        const days = Object.keys(tree[y][m] || {}).sort().reverse();
        for (const d of days) {
          const modules = tree[y][m][d] || [];
          if (modules.length > 0) {
            setSelectedDate(`${y}-${m}-${d}`);
            setSelectedModule(modules[0]);
            return;
          }
        }
      }
    }
  }, [tree, selectedDate]);

  const loadRecords = useCallback(async () => {
    if (!selectedDate || !selectedModule) return;
    setLoadingRecords(true);
    try {
      const qs = new URLSearchParams({ date: selectedDate, module: selectedModule, limit: '200' });
      if (phaseFilter) qs.append('phase', phaseFilter);
      const r = await fetch(`${API}/api/admin/logs/read?${qs}`).then(x => x.json());
      setRecords(r.records || []);
      setTotal(r.total || 0);
    } catch {
      setRecords([]); setTotal(0);
    }
    setLoadingRecords(false);
  }, [selectedDate, selectedModule, phaseFilter]);

  useEffect(() => { loadRecords(); }, [loadRecords]);

  return (
    <div data-testid="logs-browser" className="space-y-3">
      <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3">
        <div className="flex items-start gap-2">
          <Code2 className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-[11px] text-slate-400 leading-relaxed">
            <p className="text-amber-300 font-medium mb-0.5">Module-trace logs — voor en na elke functie</p>
            <p>
              Elke gedecoreerde functie schrijft 2 regels: <code className="text-amber-200">pre</code> (intentie) en <code className="text-amber-200">post</code> (resultaat + duur).
              Logs worden geïndexeerd op jaar/maand/dag en automatisch verwijderd na <span className="text-amber-200">{retentionDays} dagen</span>.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] gap-3">
        {/* Tree navigation */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3 max-h-[60vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">Archief</p>
            <button data-testid="logs-refresh" onClick={loadIndex} className="text-slate-500 hover:text-amber-400">
              <RefreshCw className={`w-3 h-3 ${loadingIndex ? 'animate-spin' : ''}`} />
            </button>
          </div>
          {loadingIndex ? (
            <p className="text-xs text-slate-500">Index laden...</p>
          ) : Object.keys(tree).length === 0 ? (
            <p className="text-xs text-slate-500">Nog geen logs.</p>
          ) : (
            <LogsTree tree={tree} selectedDate={selectedDate} selectedModule={selectedModule}
              onPick={(date, module) => { setSelectedDate(date); setSelectedModule(module); }} />
          )}
        </div>

        {/* Records pane */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3 max-h-[60vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-3 sticky top-0 bg-slate-900/90 pb-2 -mx-3 px-3 z-10">
            <div className="flex items-center gap-2">
              <Calendar className="w-3.5 h-3.5 text-amber-400" />
              <p className="text-xs text-slate-300 font-medium">
                {selectedDate || '—'} <span className="text-slate-500">·</span>{' '}
                <span className="text-amber-300">{selectedModule || '—'}</span>
                <span className="text-slate-500 text-[10px] ml-2">({total} records)</span>
              </p>
            </div>
            <div className="flex items-center gap-1">
              {['', 'pre', 'post', 'error', 'event'].map(p => (
                <button key={p || 'all'}
                  data-testid={`logs-phase-${p || 'all'}`}
                  onClick={() => setPhaseFilter(p)}
                  className={`px-2 py-0.5 rounded text-[10px] font-medium border transition-colors ${
                    phaseFilter === p
                      ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                      : 'border-slate-700 text-slate-400 hover:text-slate-200'
                  }`}>
                  {p || 'alle'}
                </button>
              ))}
            </div>
          </div>

          {loadingRecords ? (
            <p className="text-xs text-slate-500">Records laden...</p>
          ) : records.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">Geen records (probeer een andere dag/module).</p>
          ) : (
            <div className="space-y-1.5">
              {records.slice().reverse().map((r, i) => <LogLine key={i} r={r} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LogsTree({ tree, selectedDate, selectedModule, onPick }) {
  const years = Object.keys(tree).sort().reverse();
  return (
    <div className="space-y-1.5">
      {years.map(y => (
        <div key={y}>
          <p className="text-[11px] text-slate-300 font-semibold">{y}</p>
          {Object.keys(tree[y] || {}).sort().reverse().map(m => (
            <div key={`${y}-${m}`} className="ml-2 mt-1">
              <p className="text-[10px] text-slate-500 uppercase">Maand {m}</p>
              {Object.keys(tree[y][m] || {}).sort().reverse().map(d => {
                const date = `${y}-${m}-${d}`;
                const modules = tree[y][m][d] || [];
                return (
                  <div key={date} className="ml-2 mt-0.5">
                    <p className="text-[10px] text-slate-400 mb-0.5">{y}-{m}-{d}</p>
                    <div className="ml-2 flex flex-col gap-0.5">
                      {modules.map(mod => {
                        const active = selectedDate === date && selectedModule === mod;
                        return (
                          <button key={mod}
                            data-testid={`logs-pick-${date}-${mod}`}
                            onClick={() => onPick(date, mod)}
                            className={`text-left text-[11px] px-2 py-0.5 rounded transition-colors ${
                              active
                                ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                                : 'text-slate-300 hover:bg-slate-800/60'
                            }`}>
                            {mod}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function LogLine({ r }) {
  const phase = PHASE_STYLES[r.phase] || PHASE_STYLES.event;
  const PhaseIcon = phase.icon;
  const ts = (r.ts || '').slice(11, 19);
  return (
    <div data-testid={`log-line-${r.phase}`} className="flex items-start gap-2 text-[11px] border-l-2 pl-2 py-1"
      style={{ borderColor: phase.color }}>
      <span className="text-slate-500 font-mono">{ts}</span>
      <PhaseIcon className="w-3 h-3 flex-shrink-0 mt-0.5" style={{ color: phase.color }} />
      <span className="font-mono uppercase" style={{ color: phase.color, minWidth: 36 }}>{phase.label}</span>
      <span className="text-slate-200 font-medium">{r.fn}</span>
      {r.intent && <span className="text-slate-400 italic flex-1 truncate">— {r.intent}</span>}
      {typeof r.duration_ms === 'number' && (
        <span className="text-slate-500 font-mono text-[10px]">{r.duration_ms}ms</span>
      )}
      {r.result && <span className="text-emerald-400/70 text-[10px] truncate max-w-[280px]" title={r.result}>{r.result}</span>}
      {r.error && <span className="text-red-400 text-[10px] truncate max-w-[280px]" title={r.error}>{r.error}</span>}
    </div>
  );
}

export default LogsBrowser;
