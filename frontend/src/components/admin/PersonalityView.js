// v11_admin_personality_001 — Persoonlijkheid-panel per user (verhuisd uit Mijn Profiel).
// Toont wat Spark over de user "leert" (sliders + observatie-lijstjes).
// Persistentie is nog placeholder — UI-state per user-select.
import React, { useState, useEffect } from 'react';
import {
  Brain, Sparkles, Target, AlertTriangle, Eye, Ear, Heart, Globe,
} from 'lucide-react';

const DEFAULT_PERSONA = {
  introvert_extravert: 65,
  analytisch_creatief: 45,
  planmatig_spontaan: 70,
  rationeel_emotioneel: 50,
  traditioneel_vernieuwend: 80,
  zelfstandig_teamspeler: 55,
};

export function PersonalityView({ user }) {
  const [persona, setPersona] = useState(DEFAULT_PERSONA);

  // Reset persona bij user-wissel — later: backend-load van shadow-profile
  useEffect(() => {
    setPersona(DEFAULT_PERSONA);
  }, [user?.id]);

  const sliders = [
    ['introvert_extravert', 'Introvert', 'Extravert'],
    ['analytisch_creatief', 'Analytisch', 'Creatief'],
    ['planmatig_spontaan', 'Planmatig', 'Spontaan'],
    ['rationeel_emotioneel', 'Rationeel', 'Emotioneel'],
    ['traditioneel_vernieuwend', 'Traditioneel', 'Vernieuwend'],
    ['zelfstandig_teamspeler', 'Zelfstandig', 'Teamspeler'],
  ];

  return (
    <div data-testid="admin-personality-view" className="space-y-4">
      <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 p-3">
        <p className="text-[11px] text-purple-200/80 leading-relaxed">
          <Sparkles className="w-3 h-3 text-purple-400 inline mr-1" />
          Persoonlijkheid van <span className="text-amber-300 font-semibold">{user.naam}</span> — wat Spark
          uit gesprekken/gedrag afleidt. Alleen zichtbaar in Admin-mode. Aanpassingen dienen als
          startpunt; Spark stelt bij op basis van observaties.
        </p>
      </div>

      <Card title="Persoonlijkheid" accent="#a855f7" icon={Brain}
        subtitle="Sliders — Spark past aan op basis van wat hij leert">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
          {sliders.map(([key, left, right]) => (
            <Slider key={key} left={left} right={right}
              value={persona[key]}
              onChange={v => setPersona({ ...persona, [key]: v })} />
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Doelen, Behoeften & Verlangens" accent="#22c55e" icon={Target}
          subtitle="Wat wil deze user bereiken?">
          <ListInputs storageKey="doelen" rows={3} placeholder="Wat wil deze user bereiken?" label="Doelen" />
          <div className="h-2" />
          <ListInputs storageKey="behoeften" rows={3} placeholder="Wat heeft deze user nodig?" label="Behoeften" />
          <div className="h-2" />
          <ListInputs storageKey="verlangens" rows={3} placeholder="Waar verlangt deze user naar?" label="Verlangens" />
        </Card>

        <Card title="Pijn & Angst" accent="#ef4444" icon={AlertTriangle}
          subtitle="Shadow-observaties uit gesprekken">
          <div className="rounded-lg bg-slate-900/60 border border-red-500/20 p-3 text-xs text-slate-400 leading-relaxed">
            <Sparkles className="w-3 h-3 text-red-400 inline mr-1" />
            Spark houdt shadow-inzichten hier bij op basis van gesprekken met deze user.
          </div>
          <p className="text-[10px] text-slate-600 mt-3 italic">Coming soon: shadow-inzichten koppelen aan chat-logs</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Hoe deze user zich laat leiden" accent="#06b6d4" icon={Eye}>
          <ListInputs storageKey="hoort" rows={2} placeholder="Wat hoort deze user vaak?" label="Hoort" iconEl={Ear} />
          <div className="h-2" />
          <ListInputs storageKey="ziet" rows={2} placeholder="Wat ziet deze user?" label="Ziet" iconEl={Eye} />
          <div className="h-2" />
          <ListInputs storageKey="voelt" rows={2} placeholder="Wat voelt deze user?" label="Voelt" iconEl={Heart} />
        </Card>

        <Card title="Mediagedrag & Communicatie" accent="#3b82f6" icon={Globe}>
          <ListInputs storageKey="mediagedrag" rows={2} placeholder="Welke platforms?" label="Platforms" />
          <div className="h-2" />
          <ListInputs storageKey="communicatie" rows={2} placeholder="Hoe communiceert deze user?" label="Stijl" />
          <div className="h-2" />
          <ListInputs storageKey="invloeden" rows={2} placeholder="Wie volgt/inspireert deze user?" label="Invloeden" />
        </Card>
      </div>
    </div>
  );
}

// ============================================================
// LOKALE HERBRUIKBARE BOUWSTENEN (self-contained)
// ============================================================
function Card({ title, subtitle, accent = '#f59e0b', icon: Icon, children }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
        {Icon && <div className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: `${accent}22` }}>
          <Icon className="w-3.5 h-3.5" style={{ color: accent }} />
        </div>}
        <div className="flex-1">
          <h3 className="text-sm font-bold text-white">{title}</h3>
          {subtitle && <p className="text-[10px] text-slate-500">{subtitle}</p>}
        </div>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function Slider({ left, right, value, onChange }) {
  return (
    <div>
      <div className="flex justify-between text-[10px] text-slate-500 mb-1.5 uppercase tracking-wider">
        <span>{left}</span><span>{right}</span>
      </div>
      <div className="relative h-7">
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-1.5 bg-slate-800 rounded-full" />
        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-500"
          style={{ width: `${value}%` }} />
        <input type="range" min="0" max="100" value={value}
          onChange={e => onChange(parseInt(e.target.value, 10))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer" />
        <div className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full shadow-lg border-2 border-purple-500"
          style={{ left: `calc(${value}% - 8px)` }} />
      </div>
    </div>
  );
}

function ListInputs({ storageKey, label, placeholder, rows = 3, iconEl: IconEl }) {
  const [items, setItems] = useState(Array(rows).fill(''));
  const update = (i, v) => { const c = [...items]; c[i] = v; setItems(c); };
  return (
    <div>
      {label && (
        <div className="flex items-center gap-1.5 mb-1.5">
          {IconEl && <IconEl className="w-3 h-3 text-slate-400" />}
          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">{label}</span>
        </div>
      )}
      <div className="space-y-1">
        {items.map((v, i) => (
          <input key={i} type="text" value={v} placeholder={placeholder}
            onChange={e => update(i, e.target.value)}
            data-testid={`admin-personality-${storageKey}-${i}`}
            className="w-full px-2.5 py-1.5 bg-slate-800/40 border border-slate-700/50 rounded text-xs text-slate-300 placeholder-slate-600 focus:border-amber-500/60 focus:outline-none" />
        ))}
      </div>
    </div>
  );
}
