/**
 * v13o_announce_prefs_001 — Aanvinkbaar kader voor auto-announce prefs.
 * Beheer → Mijn Profiel → Instellingen → Boekhouder-meldingen.
 */
import React from 'react';
import { Bell } from 'lucide-react';

const ITEMS = [
  { key: 'announce_shop_sale',  label: 'Verkoop in mijn shop', hint: 'DM bij elke automatische boeking uit shop-verkoop' },
  { key: 'announce_sepa_import', label: 'SEPA / MT940 bank-import', hint: 'DM per geïmporteerde bank-transactie' },
  { key: 'announce_migration',   label: 'Migratie-boekingen', hint: 'DM bij retroactieve migratie-entries' },
  { key: 'announce_spark_fee',   label: 'Spark-fee inlossingen', hint: 'DM bij inlossen openstaande Spark-vergoeding' },
];

export function AnnouncePrefsPanel({ prefs, updatePref, savePrefs }) {
  const onToggle = (key, val) => {
    updatePref(key, val);
    savePrefs({ [key]: val });
  };
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4" data-testid="announce-prefs-panel">
      <div className="flex items-center gap-2 mb-3">
        <Bell className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-semibold text-white">Boekhouder-meldingen</h3>
      </div>
      <p className="text-[11px] text-slate-400 mb-3">
        Welke automatische boekingen wil je als DM van de boekhouder-bot ontvangen? Handmatige boekingen worden nooit automatisch gemeld.
      </p>
      <div className="space-y-2">
        {ITEMS.map((it) => {
          const val = prefs?.[it.key] !== false;  // default = true
          return (
            <label key={it.key} className="flex items-start justify-between gap-3 p-2.5 rounded-lg bg-slate-800/40 border border-slate-800 cursor-pointer">
              <div>
                <p className="text-xs font-medium text-white">{it.label}</p>
                <p className="text-[10px] text-slate-500">{it.hint}</p>
              </div>
              <input
                type="checkbox"
                data-testid={`announce-toggle-${it.key}`}
                checked={val}
                onChange={(e) => onToggle(it.key, e.target.checked)}
                className="w-4 h-4 accent-amber-500 mt-0.5"
              />
            </label>
          );
        })}
      </div>
    </div>
  );
}
