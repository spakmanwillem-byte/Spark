/**
 * PapertrailWidget — v11_papertrail_widget_001 (Willems verzoek sessie 51).
 *
 * Doel: visueel bewijs dat 1M token-pool klopt.
 * Toont: treasury_pool + som(balances) = total_supply, alle houders met token-count,
 * en de laatste papertrail-transacties (mint/gift/buy).
 *
 * Bronnen (metadata / footnote / blueprint):
 * - /api/shop/token/price → treasury_pool, circulating, spark_treasury
 * - /api/wallet/all-users-tokens → per-user token-verdeling (eigen endpoint hierna)
 * - data/roar/roar_balances.json.transactions → recente papertrail (laatste 20)
 */
import React from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

export function PapertrailWidget() {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${API}/api/wallet/papertrail-overview`).then(x => x.json());
      if (!r.success) throw new Error(r.detail || r.error || 'onbekende fout');
      setData(r);
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => { load(); }, [load]);

  if (loading && !data) return <div className="p-4 text-xs text-slate-500">Papertrail laden...</div>;
  if (error) return <div className="p-4 text-xs text-red-300">Fout: {error}</div>;
  if (!data) return null;

  const supply = data.total_supply || 1000000;
  const treasury = data.treasury_pool || 0;
  const circulating = data.circulating || 0;
  const total_check = treasury + circulating;
  const supply_ok = total_check === supply;

  return (
    <div data-testid="papertrail-widget" className="space-y-4">
      {/* Supply integrity */}
      <div className={`rounded-lg border p-3 ${supply_ok ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-red-500/40 bg-red-500/10'}`}>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs font-semibold text-white">Supply integriteit</h4>
          <span data-testid="supply-check" className={`text-[10px] px-2 py-0.5 rounded ${supply_ok ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'}`}>
            {supply_ok ? '✓ klopt' : '✗ MISMATCH'}
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2 text-[11px]">
          <div>
            <p className="text-slate-500 text-[9px] uppercase">Treasury</p>
            <p data-testid="pt-treasury" className="text-slate-200 font-mono">{treasury.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-slate-500 text-[9px] uppercase">Circulating</p>
            <p data-testid="pt-circulating" className="text-slate-200 font-mono">{circulating.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-slate-500 text-[9px] uppercase">Total supply</p>
            <p data-testid="pt-total" className="text-slate-200 font-mono">{supply.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Holders */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 overflow-hidden">
        <div className="px-3 py-2 border-b border-slate-800 flex items-center justify-between">
          <h4 className="text-xs font-semibold text-white">Token-houders</h4>
          <button onClick={load} data-testid="pt-refresh" className="text-[10px] text-slate-400 hover:text-white">↻</button>
        </div>
        <div className="divide-y divide-slate-800/60">
          {(data.holders || []).map(h => (
            <div key={h.user_id} data-testid={`pt-holder-${h.user_id}`} className="px-3 py-2 flex items-center justify-between text-[11px]">
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">{h.naam || h.user_id}</p>
                <p className="text-[9px] text-slate-500 font-mono truncate">
                  user_id: {h.user_id} · wallet_id: {h.wallet_id || h.user_id}
                </p>
              </div>
              <div className="text-right">
                <p className="text-amber-300 font-mono">{h.tokens} ROAR</p>
                <p className="text-[9px] text-slate-500">€{(h.tokens * (data.current_price || 0)).toFixed(2)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent papertrail */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/40 overflow-hidden">
        <div className="px-3 py-2 border-b border-slate-800">
          <h4 className="text-xs font-semibold text-white">Recente papertrail (laatste 15)</h4>
        </div>
        <div className="divide-y divide-slate-800/60 max-h-72 overflow-y-auto">
          {(data.transactions || []).map((t, i) => (
            <div key={i} data-testid={`pt-tx-${i}`} className="px-3 py-1.5 flex items-center justify-between text-[10px]">
              <div className="flex-1 min-w-0">
                <span className={`px-1.5 py-0.5 rounded text-[9px] mr-1 ${
                  t.type === 'buy_tokens' ? 'bg-emerald-500/20 text-emerald-300'
                  : t.type === 'spark_self_mint' ? 'bg-amber-500/20 text-amber-300'
                  : t.type === 'admin_grant' ? 'bg-cyan-500/20 text-cyan-300'
                  : t.type === 'admin_revoke' ? 'bg-red-500/20 text-red-300'
                  : t.type === 'gift' ? 'bg-purple-500/20 text-purple-300'
                  : 'bg-slate-700 text-slate-300'
                }`}>{t.type}</span>
                <span className="text-slate-400">{t.user_id?.slice(0,10)}</span>
                {t.n_tokens && <span className="text-amber-300 ml-1">{t.n_tokens > 0 ? '+' : ''}{t.n_tokens}</span>}
                {t.amount && <span className="text-amber-300 ml-1">{t.amount > 0 ? '+' : ''}{t.amount}</span>}
              </div>
              <span className="text-slate-600 text-[9px]">{(t.ts || t.timestamp || '').slice(11, 19)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
