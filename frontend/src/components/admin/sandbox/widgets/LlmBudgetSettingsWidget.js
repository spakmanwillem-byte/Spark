/**
 * v13t_llm_budget_settings_001 — LLM Budget Settings widget (Kladblok, admin only).
 *
 * Beheer voor 8 waardes die de chat-prompt token-budget bepalen. Zonder deze widget
 * zaten ze hardcoded in `response_composer.py` — nu tunable zonder redeploy.
 *
 * Backend keys (in settings/system.json):
 *   - chat_context_turns          (aantal oude turns)
 *   - chat_max_turn_chars         (cap per oude turn)
 *   - chat_max_user_prompt_chars  (cap huidige user_text)
 *   - chat_max_system_prompt_chars(cap system-prompt)
 *   - chat_hard_input_budget      (totaal-cap alles)
 *   - chat_identity_facts_cap_admin (facts/type voor grad 1)
 *   - chat_input_warn_at          (frontend counter amber)
 *   - chat_input_hard_at          (frontend counter rood)
 */
import React, { useEffect, useState, useCallback } from 'react';
import { Zap, RefreshCw, Save } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const FIELDS = [
  { key: 'chat_context_turns',           label: 'Aantal oude turns mee',       def: 3,     min: 1,    max: 12,    hint: 'Meer = meer context maar meer tokens' },
  { key: 'chat_max_turn_chars',          label: 'Cap per oude turn',           def: 1500,  min: 300,  max: 5000,  hint: 'Oude turn > deze grens wordt getrimd' },
  { key: 'chat_max_user_prompt_chars',   label: 'Cap huidige bericht',         def: 3000,  min: 500,  max: 8000,  hint: 'Bij langer plakken → auto-trim met marker' },
  { key: 'chat_max_system_prompt_chars', label: 'Cap system-prompt',           def: 16000, min: 4000, max: 32000, hint: 'Identity + bijbel + user_view samen' },
  { key: 'chat_hard_input_budget',       label: 'Totaal-cap (alles samen)',    def: 22000, min: 8000, max: 60000, hint: 'Laatste vangnet — snijdt oudste msgs' },
  { key: 'chat_identity_facts_cap_admin',label: 'Facts/type voor admin (grad 1)', def: 15, min: 3,    max: 200,   hint: 'Was 999 → 8477-token overshoot' },
  { key: 'chat_input_warn_at',           label: 'Char-counter amber vanaf',    def: 3500,  min: 500,  max: 10000, hint: 'Frontend waarschuwing (gele teller)' },
  { key: 'chat_input_hard_at',           label: 'Char-counter rood vanaf',     def: 5500,  min: 1000, max: 10000, hint: 'Frontend waarschuwing (rode teller)' },
];

export function LlmBudgetSettingsWidget({ userId }) {
  const [values, setValues] = useState({});
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [dirty, setDirty] = useState({});

  const flash = (kind, text) => { setMsg({ kind, text }); setTimeout(() => setMsg(null), 2500); };

  const load = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/settings/system`).then(x => x.json());
      const s = r.settings || {};
      const initial = {};
      for (const f of FIELDS) initial[f.key] = Number.isFinite(s[f.key]) ? s[f.key] : f.def;
      setValues(initial);
      setDirty({});
    } catch (e) {
      flash('err', 'Kon settings niet laden');
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const setField = (key, val) => {
    setValues(v => ({ ...v, [key]: val }));
    setDirty(d => ({ ...d, [key]: true }));
  };

  const saveAll = async () => {
    setBusy(true);
    const failed = [];
    for (const key of Object.keys(dirty)) {
      try {
        const r = await fetch(`${API}/api/settings/system/${key}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ value: Number(values[key]), viewer_id: userId }),
        });
        if (!r.ok) {
          const d = await r.json().catch(() => ({}));
          failed.push(`${key}: ${d.detail || r.status}`);
        }
      } catch (e) {
        failed.push(`${key}: ${e.message}`);
      }
    }
    setBusy(false);
    if (failed.length) flash('err', failed.join(' · '));
    else { flash('ok', `${Object.keys(dirty).length} veld(en) opgeslagen`); setDirty({}); }
  };

  const resetToDefaults = () => {
    if (!window.confirm('Alle waardes terug naar defaults?')) return;
    const initial = {};
    const d = {};
    for (const f of FIELDS) { initial[f.key] = f.def; d[f.key] = true; }
    setValues(initial);
    setDirty(d);
  };

  const hasDirty = Object.keys(dirty).length > 0;

  return (
    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-3" data-testid="llm-budget-widget">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-purple-400" />
          <div>
            <h4 className="text-sm font-semibold text-white">LLM Budget Settings</h4>
            <p className="text-[10px] text-slate-500">Char-caps voor Groq's 8000 TPM budget — voorkomt <code className="text-amber-300">all_providers_failed</code> bij grote inputs</p>
          </div>
        </div>
        <button
          onClick={load}
          disabled={busy}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white disabled:opacity-40"
          title="Vernieuw"
          data-testid="llm-budget-refresh"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {FIELDS.map(f => (
          <label key={f.key} className={`p-2 rounded-lg border ${dirty[f.key] ? 'border-purple-500/50 bg-purple-500/5' : 'border-slate-800 bg-slate-900/40'}`}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[11px] text-slate-300 font-medium">{f.label}</span>
              {dirty[f.key] && <span className="text-[9px] text-purple-400">gewijzigd</span>}
            </div>
            <input
              type="number"
              value={values[f.key] ?? ''}
              onChange={e => setField(f.key, e.target.value === '' ? '' : Number(e.target.value))}
              min={f.min}
              max={f.max}
              data-testid={`llm-budget-input-${f.key}`}
              className="w-full px-2 py-1 text-sm bg-slate-950/60 border border-slate-800 rounded text-white font-mono focus:outline-none focus:border-purple-500"
            />
            <p className="text-[9px] text-slate-500 mt-1">
              default {f.def} · {f.hint}
            </p>
          </label>
        ))}
      </div>

      <div className="flex items-center gap-2 pt-1">
        <button
          onClick={saveAll}
          disabled={!hasDirty || busy}
          data-testid="llm-budget-save-btn"
          className="flex-1 flex items-center justify-center gap-2 py-2 text-xs font-medium text-white rounded-lg transition-all hover:brightness-110 disabled:opacity-40"
          style={{ background: hasDirty && !busy ? 'linear-gradient(135deg, #a855f7, #7c3aed)' : '#334155' }}
        >
          <Save className="w-3.5 h-3.5" />
          {busy ? 'Bezig…' : hasDirty ? `Opslaan (${Object.keys(dirty).length})` : 'Geen wijzigingen'}
        </button>
        <button
          onClick={resetToDefaults}
          disabled={busy}
          data-testid="llm-budget-reset-btn"
          className="px-3 py-2 text-xs rounded-lg border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 disabled:opacity-40"
        >
          Defaults
        </button>
      </div>

      {msg && (
        <p
          data-testid="llm-budget-msg"
          className={`text-[11px] px-3 py-2 rounded-lg border ${msg.kind === 'ok' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' : 'bg-red-500/10 text-red-300 border-red-500/30'}`}
        >
          {msg.text}
        </p>
      )}

      <p className="text-[9px] text-slate-600 italic">
        💡 Backend leest deze waardes bij elke chat-request. Wijziging is direct actief — geen redeploy nodig.
      </p>
    </div>
  );
}

export default LlmBudgetSettingsWidget;
