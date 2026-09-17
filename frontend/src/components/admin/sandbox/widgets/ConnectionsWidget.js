/**
 * v14_connections_001 (17-09-2026) — Willem: "ik wil geen cloud maar alle connecties,
 * verbindingen, poorten, api's op één plek." Tijdelijk in Kladblok tot eigen Beheer-tab.
 *
 * Zelfstandig: eigen fetch op /api/connections. JSON-waarde wint van .env; leeg veld = terug naar .env.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Plug, Eye, EyeOff, Save, Wifi, Loader2 } from 'lucide-react';
import { useAuth } from '../../../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

const SOURCE_LABEL = { json: 'opgeslagen', env: '.env', leeg: 'leeg' };
const SOURCE_COLOR = { json: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/20', env: 'text-amber-300 bg-amber-500/10 border-amber-500/20', leeg: 'text-slate-500 bg-slate-800/40 border-slate-700' };

function ConnectionRow({ conn, viewerId, onSaved }) {
  const [edits, setEdits] = useState({});
  const [show, setShow] = useState({});
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [test, setTest] = useState(conn.last_test || null);

  const dirty = Object.keys(edits).length > 0;

  const save = async () => {
    setSaving(true);
    try {
      await fetch(`${API}/api/connections/${conn.id}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ viewer_id: viewerId, values: edits }),
      });
      setEdits({}); onSaved();
    } finally { setSaving(false); }
  };

  const runTest = async () => {
    setTesting(true);
    try {
      const r = await fetch(`${API}/api/connections/${conn.id}/test?viewer_id=${viewerId}`, { method: 'POST' }).then(x => x.json());
      setTest({ ok: r.ok, detail: r.detail, at: new Date().toISOString() });
    } catch (e) { setTest({ ok: false, detail: String(e) }); }
    finally { setTesting(false); }
  };

  const dot = test == null ? 'bg-slate-600' : test.ok ? 'bg-emerald-400' : test.ok === null ? 'bg-slate-500' : 'bg-rose-400';

  return (
    <div data-testid={`connection-${conn.id}`} className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${dot}`} data-testid={`connection-${conn.id}-status`} />
            <span className="text-sm font-medium text-white">{conn.naam}</span>
            <span className="text-[9px] uppercase tracking-wider text-slate-500">{conn.type}</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">{conn.doel}</p>
        </div>
        {conn.testable && (
          <button onClick={runTest} disabled={testing} data-testid={`connection-${conn.id}-test-btn`}
            className="shrink-0 flex items-center gap-1 text-[11px] px-2 py-1 rounded-lg border border-slate-700 text-slate-300 hover:border-cyan-500/50 hover:text-cyan-300 transition-colors">
            {testing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Wifi className="w-3 h-3" />} Test
          </button>
        )}
      </div>

      {test && (
        <p data-testid={`connection-${conn.id}-test-result`} className={`text-[11px] ${test.ok ? 'text-emerald-300' : test.ok === null ? 'text-slate-400' : 'text-rose-300'}`}>
          {test.detail}{test.at && <span className="text-slate-600"> · {new Date(test.at).toLocaleString('nl-NL')}</span>}
        </p>
      )}

      {conn.readonly_info && (
        <div className="flex gap-3 text-[11px] text-slate-400">
          {Object.entries(conn.readonly_info).map(([k, v]) => <span key={k}><span className="text-slate-600">{k}:</span> <span className="font-mono text-slate-300">{v}</span></span>)}
        </div>
      )}

      {conn.velden.map(f => {
        const val = edits[f.key] !== undefined ? edits[f.key] : (f.secret ? '' : f.value);
        return (
          <div key={f.key} className="grid grid-cols-[110px_1fr_auto] items-center gap-2">
            <label className="text-[11px] text-slate-400">{f.label}</label>
            <div className="relative">
              <input
                data-testid={`connection-${conn.id}-${f.key}-input`}
                type={f.secret && !show[f.key] ? 'password' : 'text'}
                value={val}
                placeholder={f.secret && f.filled ? f.value : (f.hint || '')}
                onChange={e => setEdits(p => ({ ...p, [f.key]: e.target.value }))}
                className="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-2 py-1 text-xs text-slate-200 font-mono focus:border-cyan-500/50 focus:outline-none"
              />
              {f.secret && (
                <button type="button" onClick={() => setShow(p => ({ ...p, [f.key]: !p[f.key] }))}
                  className="absolute right-1.5 top-1 text-slate-500 hover:text-slate-300" data-testid={`connection-${conn.id}-${f.key}-toggle`}>
                  {show[f.key] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              )}
            </div>
            <span className={`text-[9px] px-1.5 py-0.5 rounded border ${SOURCE_COLOR[f.source]}`} title={`env: ${f.env}`}>{SOURCE_LABEL[f.source]}</span>
          </div>
        );
      })}

      {conn.velden.length > 0 && (
        <div className="flex items-center justify-between pt-1">
          <span className="text-[10px] text-slate-600">{conn.updated_at ? `bijgewerkt ${new Date(conn.updated_at).toLocaleString('nl-NL')}` : 'leeg veld = waarde uit .env'}</span>
          <button onClick={save} disabled={!dirty || saving} data-testid={`connection-${conn.id}-save-btn`}
            className={`flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-lg border transition-colors ${dirty ? 'border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10' : 'border-slate-800 text-slate-600'}`}>
            {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />} Opslaan
          </button>
        </div>
      )}
    </div>
  );
}

export function ConnectionsWidget() {
  const { user } = useAuth();
  const viewerId = user?.id || 'user-001';
  const [conns, setConns] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    fetch(`${API}/api/connections?viewer_id=${viewerId}`).then(r => r.json())
      .then(d => { if (d.success) setConns(d.connections); else setError(d.detail || 'Geen toegang'); })
      .catch(e => setError(String(e)));
  }, [viewerId]);

  useEffect(() => { load(); }, [load]);

  return (
    <div data-testid="connections-widget" className="rounded-2xl p-5 border border-cyan-500/20 bg-gradient-to-br from-cyan-950/20 to-slate-950/40">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Plug className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white">Verbindingen</h3>
        </div>
        <span className="text-[10px] text-cyan-300/70 uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">lokaal · connections.json</span>
      </div>
      {error && <p className="text-xs text-rose-300" data-testid="connections-error">{error}</p>}
      {!conns && !error && <p className="text-xs text-slate-500">Verbindingen laden...</p>}
      {conns && (
        <div className="space-y-3">
          {conns.map(c => <ConnectionRow key={c.id} conn={c} viewerId={viewerId} onSaved={load} />)}
        </div>
      )}
    </div>
  );
}
