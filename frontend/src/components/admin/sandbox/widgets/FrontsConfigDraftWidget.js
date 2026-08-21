/**
 * v13_fronts_config_draft_widget_001 — Fronts-config schema draft (parkeer-widget).
 *
 * STATUS: SKELETON — dit is een concept/kladpapier voor de latere Beheer → Fronts tab.
 * Toont het voorgestelde JSON-schema om per scherm (login, gesprekken, dashboard, …)
 * kleuren, teksten en animaties instelbaar te maken. Emmy's woorden:
 * > "als je fronts bij maakt kan je immers eerst kwijt in widget kladblok :D"
 *
 * VERPLAATSEN: als het schema is uitonderhandeld, verplaats deze widget naar
 *   Beheer → Instellingen → tab "Fronts", ga per screen-key een echte editor bouwen
 *   en persist naar /app/backend/data/system/fronts_config.json (JSON-only).
 */
import React, { useState } from 'react';
import { Layout, Copy, Check } from 'lucide-react';

// Concept-schema — één plek waar alle scherm-configuraties samenkomen.
// Later: PATCH /api/system/fronts-config/{screen_key}
const DRAFT_SCHEMA = {
  version: 1,
  screens: {
    'auth.login': {
      label: 'Loginscherm',
      colors: { primary: 'var(--glow-base)', bg: '#000000' },
      font: 'system-ui',
      animations: {
        background_dots: { enabled: true, palette: ['primary'], pulse_bpm: 60 },
      },
      texts: {}, // login-scherm heeft nog geen configureerbare teksten
    },
    'chat.prive.call': {
      label: 'Privé-bel bark',
      colors: {
        border: 'var(--glow-base)',
        alert: 'var(--alert-base)',   // wordt gebruikt bij offline/geen-antwoord
      },
      // BADGE = pure status (kort woord/token)
      status_labels: {
        connecting: 'Verbinden',
        ringing:    'Overgaan',
        active_audio: 'Verbonden',
        active_video: 'In beeld',
        no_answer:  'Offline',
        dropped:    'Verbroken',        // toekomst
        rejected:   'Afgewezen',        // toekomst
      },
      // TEKST ONDER AVATAR = actie-context, met {naam}-token
      action_texts: {
        connecting: 'Probeert {naam} te bereiken…',
        ringing:    '{naam} wordt gebeld…',
        active_audio: 'Gesprek met {naam}',
        active_video: 'Beeldgesprek met {naam}',
        no_answer:  'Geen antwoord — {naam} is offline. Probeer later opnieuw.',
        dropped:    'Verbinding met {naam} verbroken.',
        rejected:   '{naam} heeft afgewezen.',
      },
      timings_ms: {
        connecting_to_ringing: 800,
        ringing_to_active:     3200,
        ringing_to_no_answer:  4800,
        no_answer_auto_hangup: 15000,
      },
    },
    'workspace.dashboard': {
      label: 'Dashboard',
      colors: { accent: 'var(--glow-base)' },
      font: 'system-ui',
      texts: {},
    },
  },
};

export function FrontsConfigDraftWidget() {
  const [copied, setCopied] = useState(false);
  const json = JSON.stringify(DRAFT_SCHEMA, null, 2);

  const copyJson = async () => {
    try {
      await navigator.clipboard.writeText(json);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { /* clipboard may be blocked */ }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4" data-testid="fronts-config-draft-widget">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/25 flex items-center justify-center">
          <Layout className="w-4 h-4 text-cyan-400" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-bold text-white">Fronts — Config Draft</h3>
          <p className="text-[10px] text-slate-500">
            Concept voor Beheer → Fronts. Per scherm: kleuren · lettertype · teksten · animaties.
          </p>
        </div>
        <button
          data-testid="fronts-draft-copy"
          onClick={copyJson}
          className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          {copied ? 'Gekopieerd' : 'Kopieer JSON'}
        </button>
      </div>

      <div className="mb-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-[10px]">
        <div className="p-2 rounded bg-slate-800/40 border border-slate-800">
          <p className="text-slate-400 mb-1 font-semibold">Ontwerpprincipe</p>
          <p className="text-slate-500">
            <span className="text-white">Status-badge</span> = korte token (Offline).<br />
            <span className="text-white">Actie-tekst</span> = context met {'{naam}'} (Geen antwoord — Heidi is offline).<br />
            Beide instelbaar per scherm.
          </p>
        </div>
        <div className="p-2 rounded bg-slate-800/40 border border-slate-800">
          <p className="text-slate-400 mb-1 font-semibold">Kleuren</p>
          <p className="text-slate-500">
            <code className="text-amber-300">--glow-base</code> = primair.
            <code className="text-red-300 ml-1">--alert-base</code> = alarm/offline (nieuw, tunable via Fronts).
            Voorkomt hardcoded rood/oranje.
          </p>
        </div>
      </div>

      <pre
        data-testid="fronts-draft-json"
        className="text-[10px] leading-relaxed bg-slate-950 border border-slate-800 rounded p-3 overflow-x-auto text-slate-300 max-h-96"
      >
{json}
      </pre>

      <p className="text-[10px] text-slate-500 mt-2">
        Volgende stap: backend endpoint <code className="text-cyan-300">GET/PUT /api/system/fronts-config</code>
        {' '}met JSON-file storage in <code className="text-cyan-300">data/system/fronts_config.json</code>. Frontend leest bij mount, cached in context.
      </p>
    </div>
  );
}
