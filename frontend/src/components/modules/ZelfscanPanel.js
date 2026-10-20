// v14_zelfscan_001 — Beheer → Integraties → Zelfscan: kan Spark zijn eigen data zien?
import React, { useCallback, useEffect, useState } from 'react';
import { ScanSearch, Wand2, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../../context/AuthContext';
import { apiError } from '../../lib/utils';

const API = process.env.REACT_APP_BACKEND_URL;

function Teller({ label, value, accent }) {
  return (
    <div data-testid={`zelfscan-teller-${label.toLowerCase().replace(/[^a-z0-9]/g, '-')}`} className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-3">
      <p className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</p>
      <p className="text-xl font-bold" style={{ color: accent || '#e2e8f0' }}>{value}</p>
    </div>
  );
}

export function ZelfscanPanel() {
  const { user } = useAuth();
  const [rapport, setRapport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState('onvolledig');

  const scan = useCallback(async () => {
    setBusy(true);
    try {
      const r = await fetch(`${API}/api/synapse/zelfscan`).then(x => x.json());
      if (r.success) setRapport(r); else toast.error(apiError(r, 'Scan mislukt'));
    } catch { toast.error('Scan mislukt'); }
    setBusy(false);
  }, []);

  useEffect(() => { scan(); }, [scan]);

  const backfill = async () => {
    if (!window.confirm('Lege metadata aanvullen met beste gok (bron legacy_backfill, vertrouwen 0.5)? Bestaande tekst blijft staan; per _meta.json komt een .bak_zelfscan.')) return;
    setBusy(true);
    try {
      const r = await fetch(`${API}/api/synapse/zelfscan/backfill`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ viewer_id: user?.id }) }).then(x => x.json());
      if (r.success) { toast.success(`Aangevuld: ${r.stats.footnote_gevuld} footnotes · ${r.stats.enricher_doel_filled} doelen · ${r.stats.enricher_blueprints_created} blauwdrukken · ${r.stats.blueprint_doel_ververst} stubs ververst`); await scan(); }
      else toast.error(apiError(r, 'Aanvullen mislukt'));
    } catch { toast.error('Aanvullen mislukt'); }
    setBusy(false);
  };

  const t = rapport?.tellers;
  const rows = (rapport?.containers || []).filter(c => {
    if (filter === 'alles') return true;
    const bpOk = c.code ? (c.blueprint_ref && !c.blueprint_stub) : true;
    return !(c.footnote && c.doel && bpOk);
  });

  return (
    <div data-testid="zelfscan-panel" className="h-full overflow-y-auto p-4 md:p-6 space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[16rem]">
          <h2 className="text-base md:text-lg font-bold text-white">Zelfscan — kan Spark zijn eigen data zien?</h2>
          <p className="text-xs text-slate-400">Elke map met een <code>_meta.json</code> is een container. Compleet = footnote (herkomst) + doel + voor code-modules een ingevulde blauwdruk.</p>
        </div>
        <button data-testid="zelfscan-scan-btn" onClick={scan} disabled={busy} className="px-3 py-2 rounded-lg text-xs font-semibold bg-slate-800 text-slate-200 hover:bg-slate-700 flex items-center gap-1.5 disabled:opacity-50">
          {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ScanSearch className="w-3.5 h-3.5" />} Scan
        </button>
        <button data-testid="zelfscan-backfill-btn" onClick={backfill} disabled={busy || !t} className="px-3 py-2 rounded-lg text-xs font-semibold text-slate-950 flex items-center gap-1.5 disabled:opacity-50" style={{ background: '#f59e0b' }}>
          <Wand2 className="w-3.5 h-3.5" /> Vul aan (beste gok)
        </button>
      </div>

      {t && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
          <Teller label="Containers" value={t.totaal} />
          <Teller label="Code-modules" value={t.code_modules} />
          <Teller label="Compleet" value={`${t.compleet} (${t.pct_compleet}%)`} accent="#22c55e" />
          <Teller label="Zonder footnote" value={t.zonder_footnote} accent={t.zonder_footnote ? '#f87171' : '#22c55e'} />
          <Teller label="Doel leeg" value={t.doel_leeg} accent={t.doel_leeg ? '#fbbf24' : '#22c55e'} />
          <Teller label="Zonder blauwdruk" value={t.zonder_blueprint} accent={t.zonder_blueprint ? '#fbbf24' : '#22c55e'} />
          <Teller label="Blauwdruk = stub" value={t.blueprint_stub} accent="#94a3b8" />
        </div>
      )}

      <div className="flex items-center gap-2">
        {[['onvolledig', 'Onvolledig'], ['alles', 'Alles']].map(([id, label]) => (
          <button key={id} data-testid={`zelfscan-filter-${id}`} onClick={() => setFilter(id)}
            className={`px-3 py-1 rounded-lg text-[11px] font-medium border ${filter === id ? 'border-amber-500 text-amber-300 bg-amber-500/10' : 'border-slate-700 text-slate-400'}`}>{label}</button>
        ))}
        <span className="text-[11px] text-slate-500">{rows.length} containers</span>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-xs">
          <thead className="bg-slate-950/60 text-[10px] uppercase text-slate-500">
            <tr><th className="text-left px-3 py-2">Container</th><th className="px-2 py-2">Footnote</th><th className="px-2 py-2">Doel</th><th className="px-2 py-2">Blauwdruk</th></tr>
          </thead>
          <tbody>
            {rows.slice(0, 200).map(c => (
              <tr key={c.pad} data-testid={`zelfscan-row-${c.naam}`} className="border-t border-slate-800/60">
                <td className="px-3 py-1.5 text-slate-300 font-mono text-[11px]">{c.pad}{c.code && <span className="ml-1 text-[9px] text-cyan-400">code</span>}</td>
                <td className="text-center">{c.footnote ? <CheckCircle2 className="w-3.5 h-3.5 inline text-emerald-400" /> : <AlertCircle className="w-3.5 h-3.5 inline text-red-400" />}</td>
                <td className="text-center">{c.doel ? <CheckCircle2 className="w-3.5 h-3.5 inline text-emerald-400" /> : <AlertCircle className="w-3.5 h-3.5 inline text-amber-400" />}</td>
                <td className="text-center text-[10px] text-slate-400">{!c.code ? '—' : !c.blueprint_ref ? <span className="text-amber-400">ontbreekt</span> : c.blueprint_stub ? <span className="text-slate-400">stub</span> : <CheckCircle2 className="w-3.5 h-3.5 inline text-emerald-400" />}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[11px] text-slate-500">Een <em>stub</em> is een auto-gegenereerde blauwdruk met alleen doel + endpoints; "Wat werkt al" en "Relaties" vul je zelf (of later Spark) in <code>/app/memory/blueprints/</code>.</p>
    </div>
  );
}
