/**
 * v10_kladblok_registry_001 — Kladblok widget registry (Willems verzoek sessie 47).
 *
 * DOEL: Tijdelijk parkeer-plek voor front-end kaders die nog geen definitieve plek hebben.
 * Als je een nieuwe widget bouwt en niet zeker weet waar hij hoort, registreer 'm hier.
 * Later verplaats je 'm naar zijn definitieve module met 1 regel: verwijder uit deze array,
 * importeer 'm daar.
 *
 * BEST PRACTICE: elk widget = een zelfstandige `.js` file in `./widgets/`.
 * Kader heeft eigen state, eigen fetch-logica, geen dependency op het kladblok zelf.
 * Zo kun je 'm 1-op-1 verplaatsen naar bv. AnalyticsPage door daar te importeren:
 *
 *   import { LlmTokenUsageWidget } from './sandbox/widgets/LlmTokenUsageWidget';
 *   <LlmTokenUsageWidget />
 *
 * Willem's woorden sessie 47:
 * > "kaders in containers doen. dan hoef je dat alleen te verplaatsen."
 * > "je hoeft het geen sandbox meer te noemen hoor heet immers nu kladblok"
 *
 * Route + folder blijven `sandbox` (backwards compat, geen breaking change).
 * Label + UI zeggen "Kladblok".
 */
import { LlmTokenUsageWidget } from './widgets/LlmTokenUsageWidget';
import { PapertrailWidget } from './widgets/PapertrailWidget';
import { AchievementSnuffelWidget } from './widgets/AchievementSnuffelWidget';

export const SANDBOX_WIDGETS = [
  {
    id: 'llm-token-usage',
    naam: 'LLM Token Usage',
    doel: 'Toont dagelijks token-verbruik per LLM-provider (Groq/Cerebras) met % van limit.',
    waar_hoort_het: 'Analytics → Systeem tab, of eigen Integraties → LLM overzicht',
    aangemaakt_op: '2026-07-22',
    aangemaakt_door: 'e1 sessie 47',
    reden: "Willem's Groq rate limit hit vandaag (94k/100k tokens). Widget voorkomt verrassingen midden in gesprek.",
    Component: LlmTokenUsageWidget,
  },
  {
    id: 'papertrail-supply',
    naam: 'Token Papertrail',
    doel: 'Toont treasury (999.990) + alle houders + laatste papertrail-transacties. Bewijs dat 1M pool klopt.',
    waar_hoort_het: 'WalletPage → admin tab, of eigen Token-management module',
    aangemaakt_op: '2026-07-31',
    aangemaakt_door: 'e1 sessie 51',
    reden: "Willem wil visueel bewijs dat mint/gift/buy allemaal via dezelfde treasury_pool gaan zonder losse eindjes. Fraude-preventie.",
    Component: PapertrailWidget,
  },
  // Volgende sandbox-widgets komen hier:
  // { id: 'xxx', naam: '...', ..., Component: XxxWidget }
  {
    id: 'achievement-snuffel',
    naam: 'Achievement / XP / Rang — inventaris',
    doel: 'Overzicht van wat er ECHT bestaat rondom achievements, XP en rang, zodat we geen dubbele modules bouwen.',
    waar_hoort_het: 'Tijdelijk kladblok — verwijder als Willem gaps heeft besproken en/of opgepakt.',
    aangemaakt_op: '2026-08-04',
    aangemaakt_door: 'e1 sessie 56d',
    reden: "Willem: 'als je info niet kwijt kan en graag kwijt wil geen plek weet, plaats gerust in beheer widget kladblok.' Snuffel-findings over 7 bestaande dingen + 5 open vragen + 1 nu gefixt.",
    Component: AchievementSnuffelWidget,
  },
];
