/**
 * v13d_uren_rapport_001 (sessie 56b) — Willem: "uren-registratie formulier per
 * dag/week/maand/jaar als bron waar wat we gemaakt hebben heen kan schrijven".
 *
 * Aggregeert alle zakelijke agenda-events per opdrachtgever per periode.
 * Bron voor factuur/urenstaat exports.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { Clock, ChevronLeft, ChevronRight, Briefcase, Download } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

const PERIODS = [
  { id: 'dag', label: 'Dag' },
  { id: 'week', label: 'Week' },
  { id: 'maand', label: 'Maand' },
  { id: 'jaar', label: 'Jaar' },
];

export function UrenRapportPage({ onNavigate }) {
  const { user } = useAuth();
  const uid = user?.id || 'user-001';
  const [period, setPeriod] = useState('maand');
  const [anchor, setAnchor] = useState(new Date());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    const y = anchor.getFullYear(), m = anchor.getMonth() + 1, d = anchor.getDate();
    const url = `${API}/api/agenda/uren-rapport/${uid}?period=${period}&year=${y}&month=${m}&day=${d}&viewer_id=${uid}`;
    fetch(url).then(r => r.json()).then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [uid, period, anchor]);

  useEffect(() => { load(); }, [load]);

  const shift = (dir) => {
    const d = new Date(anchor);
    if (period === 'dag') d.setDate(d.getDate() + dir);
    else if (period === 'week') d.setDate(d.getDate() + 7 * dir);
    else if (period === 'maand') d.setMonth(d.getMonth() + dir);
    else d.setFullYear(d.getFullYear() + dir);
    setAnchor(d);
  };

  const exportCSV = () => {
    if (!data?.events) return;
    const rows = [['Datum', 'Titel', 'Opdrachtgever', 'Onderwerp', 'Pauze (min)', 'Uren']];
    for (const e of data.events) {
      rows.push([
        (e.date || '').slice(0, 10),
        (e.titel || '').replace(/,/g, ' '),
        (e.opdrachtgever || '').replace(/,/g, ' '),
        (e.onderwerp || '').replace(/,/g, ' '),
        e.pauze_minuten || 0,
        e.totaal_uren || 0,
      ]);
    }
    const csv = rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `urenstaat_${data.label.replace(/[^a-zA-Z0-9]/g, '_')}.csv`;
    link.click();
  };

  return (
    <MainLayout activePage="uren-rapport" onNavigate={onNavigate}>
      <div data-testid="uren-rapport-page" className="h-full flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'var(--glow-base)' }}>
              <Clock className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Uren-registratie</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">
                Bron: zakelijke agenda-events · per opdrachtgever
              </p>
            </div>
            <button data-testid="export-csv-btn" onClick={exportCSV} disabled={!data?.events?.length}
              className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white disabled:opacity-40"
              style={{ background: 'var(--app-secondary, #06b6d4)' }}>
              <Download className="w-3.5 h-3.5" /> CSV
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-4xl mx-auto space-y-4">
            {/* Periode-picker */}
            <div className="flex items-center gap-2 flex-wrap">
              {PERIODS.map(p => (
                <button key={p.id} data-testid={`period-${p.id}`} onClick={() => setPeriod(p.id)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium transition"
                  style={period === p.id
                    ? { background: 'color-mix(in srgb, var(--glow-base) 20%, transparent)',
                        borderWidth: '1px', borderStyle: 'solid',
                        borderColor: 'color-mix(in srgb, var(--glow-base) 50%, transparent)',
                        color: 'var(--glow-base)' }
                    : { background: 'rgba(30,41,59,0.5)', borderWidth: '1px', borderStyle: 'solid',
                        borderColor: 'rgba(51,65,85,0.5)', color: '#94a3b8' }}>
                  {p.label}
                </button>
              ))}
              <div className="ml-auto flex items-center gap-2">
                <button onClick={() => shift(-1)} className="p-1.5 hover:bg-slate-800 rounded-lg"><ChevronLeft className="w-4 h-4 text-slate-400" /></button>
                <p data-testid="period-label" className="text-sm font-semibold text-white min-w-[180px] text-center">{data?.label || '...'}</p>
                <button onClick={() => shift(1)} className="p-1.5 hover:bg-slate-800 rounded-lg"><ChevronRight className="w-4 h-4 text-slate-400" /></button>
              </div>
            </div>

            {/* Totalen */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider">Totaal uren</p>
                <p className="text-3xl font-bold mt-1" data-testid="totaal-uren" style={{ color: 'var(--glow-base)' }}>
                  {loading ? '...' : (data?.totaal_uren ?? 0)}
                </p>
              </div>
              <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider">Events</p>
                <p className="text-3xl font-bold text-white mt-1" data-testid="event-count">
                  {loading ? '...' : (data?.event_count ?? 0)}
                </p>
              </div>
            </div>

            {/* Per opdrachtgever */}
            <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Briefcase className="w-3.5 h-3.5" style={{ color: 'var(--app-secondary, #06b6d4)' }} /> Per opdrachtgever
              </h3>
              {loading || !data ? (
                <p className="text-xs text-slate-500 italic">Laden...</p>
              ) : data.per_opdrachtgever.length === 0 ? (
                <p className="text-xs text-slate-500 italic">Geen zakelijke uren in deze periode.</p>
              ) : (
                <div className="space-y-1.5">
                  {data.per_opdrachtgever.map(row => (
                    <div key={row.opdrachtgever} data-testid={`opdr-row-${row.opdrachtgever}`}
                      className="flex items-center gap-3 p-2 bg-slate-950/30 rounded">
                      <span className="text-xs text-white font-medium flex-1">{row.opdrachtgever}</span>
                      <span className="text-[10px] text-slate-500">{row.events} event{row.events !== 1 ? 's' : ''}</span>
                      <span className="text-sm font-bold" style={{ color: 'var(--glow-base)' }}>{row.uren}u</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Events detail */}
            {data?.events?.length > 0 && (
              <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
                <h3 className="text-sm font-semibold text-white mb-3">Events</h3>
                <div className="space-y-1.5">
                  {data.events.map(ev => (
                    <div key={ev.id} className="flex items-center gap-3 p-2 bg-slate-950/30 rounded text-xs">
                      <span className="text-slate-500 w-24">{(ev.date || '').slice(0, 10)}</span>
                      <span className="text-white flex-1 truncate">{ev.titel}</span>
                      {ev.opdrachtgever && <span className="text-amber-300 text-[10px]">💼 {ev.opdrachtgever}</span>}
                      {ev.pauze_minuten > 0 && <span className="text-[10px] text-slate-500">pauze {ev.pauze_minuten}m</span>}
                      <span className="font-semibold" style={{ color: 'var(--glow-base)' }}>{ev.totaal_uren}u</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default UrenRapportPage;
