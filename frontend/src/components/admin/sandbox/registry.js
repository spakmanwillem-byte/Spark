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
import { FrontsConfigDraftWidget } from './widgets/FrontsConfigDraftWidget';
import { LlmBudgetSettingsWidget } from './widgets/LlmBudgetSettingsWidget';
import { IncompleteCardsWidget } from './widgets/IncompleteCardsWidget';
import { ShadowObserverWidget } from './widgets/ShadowObserverWidget';
import { PerformanceWidget } from './widgets/PerformanceWidget';
import { BugsListWidget } from './widgets/BugsListWidget';
import { DeployWidget } from './widgets/DeployWidget';
import { AdminNotesWidget } from './widgets/AdminNotesWidget';
import { ConnectionsWidget } from './widgets/ConnectionsWidget';

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
  {
    id: 'fronts-config-draft',
    naam: 'Fronts Config Draft',
    doel: 'Concept-schema per scherm (kleuren, teksten, animaties) voor de latere Beheer → Fronts tab. Statusbadge vs actie-tekst gesplitst.',
    waar_hoort_het: 'Beheer → Instellingen → nieuwe tab "Fronts"',
    aangemaakt_op: '2026-02-21',
    aangemaakt_door: 'e1 sessie 52c',
    reden: "Emmy wil hardgecodeerde teksten (bv 'Heidi is offline') en kleuren (bv rood alert) instelbaar maken per scherm zonder telkens de agent te vragen. Kladblok = eerste parking.",
    Component: FrontsConfigDraftWidget,
  },
  {
    id: 'llm-budget-settings',
    naam: 'LLM Budget Settings',
    doel: '8 char-caps voor Groq TPM-budget: turns, user_text, system_prompt, hard-cap, identity-facts, frontend counter-thresholds. Voorkomt `all_providers_failed` bij lange plakkerige input.',
    waar_hoort_het: 'Beheer → Instellingen → nieuwe card "Chat & LLM budget" onder Algemeen, of eigen LLM-tab',
    aangemaakt_op: '2026-08-22',
    aangemaakt_door: 'e1 sessie 52t',
    reden: "Willem: 'ik wil die waardes zelf kunnen tunen zonder redeploy'. Waardes stonden hardcoded in response_composer.py. Nu leest backend ze uit settings/system bij elke chat-request.",
    Component: LlmBudgetSettingsWidget,
  },
  {
    id: 'incomplete-cards',
    naam: 'Onvolledige Kaarten',
    doel: 'Auto-scan + edit-panel voor KB-kaarten met leeg 5W of laag<20 chars. Links lijst, rechts full-card editor. Save → herscan → kaart verdwijnt als compleet.',
    waar_hoort_het: 'Admin → eigen kader (KB-Beheer), of Kennisbank → sidepanel. Voorlopig in Kladblok.',
    aangemaakt_op: '2026-02-22',
    aangemaakt_door: 'e1 sessie 54',
    reden: "Willem: ⚠ Onvolledig subtab in Inbox maakte kaart-kopieën met dezelfde id → dubbels-bug. Widget is monitoring + edit i.p.v. een tweede kaart-collectie. Geen bulk-import meer nodig.",
    Component: IncompleteCardsWidget,
  },
  {
    id: 'shadow-observer',
    naam: 'Shadow Observer',
    doel: 'Live chat-events, correcties, fallbacks, top-triggers en nog niet gebruikte triggers/vocab/bijbel-items.',
    waar_hoort_het: 'Spark AI → Spark Brain → Observer tab, of Analytics → Chat inzicht',
    aangemaakt_op: '2026-02-23',
    aangemaakt_door: 'e1 sessie 56',
    reden: "Willem: 'Shadow Observer hoort niet op dashboard, park in Widget Kladblok tot goede plek gevonden.'",
    Component: ShadowObserverWidget,
  },
  {
    id: 'performance',
    naam: 'Performance',
    doel: 'Storage-cache overzicht (MB in geheugen, gecachede files, cache leegmaken).',
    waar_hoort_het: 'Beheer → Systeem, of Analytics → Systeem tab',
    aangemaakt_op: '2026-02-23',
    aangemaakt_door: 'e1 sessie 56',
    reden: "Willem: 'Performance-kaart hoort niet op dashboard, park in Widget Kladblok tot goede plek gevonden.'",
    Component: PerformanceWidget,
  },
  {
    id: 'bugs-list',
    naam: 'Bug meldingen',
    doel: 'Admin-tab uit Notities & Taken: lijst van bug-reports, status wijzigen, bulk-close, verwijderen.',
    waar_hoort_het: 'Beheer → eigen "Bug tracker" tab, of onder Analytics → Kwaliteit',
    aangemaakt_op: '2026-02-25',
    aangemaakt_door: 'e1 sessie 56b',
    reden: "Willem: 'Bugs-tab in notities is een admin-ding, breng even onder in Widget Kladblok tot goede plek'.",
    Component: BugsListWidget,
  },
  {
    id: 'deploy',
    naam: 'Deploy Anchor',
    doel: 'Admin-tab uit Notities & Taken: deploy/anchor state en actiepanel voor productie-promotie.',
    waar_hoort_het: 'Beheer → eigen "Deploy" of "Systeem" tab',
    aangemaakt_op: '2026-02-25',
    aangemaakt_door: 'e1 sessie 56b',
    reden: "Willem: 'Deploy-tab uit notities mag ook naar Widget Kladblok tot betere plek'.",
    Component: DeployWidget,
  },
  {
    id: 'admin-notes',
    naam: 'Admin notities',
    doel: 'Aparte scratchpad voor systeem-observaties, roadmap-brainfarts en dev-todos. Notities met scope=admin verschijnen hier i.p.v. in Notities & Taken.',
    waar_hoort_het: 'Beheer → eigen "Admin notities" tab, of Analytics → Roadmap',
    aangemaakt_op: '2026-02-25',
    aangemaakt_door: 'e1 sessie 56b',
    reden: "Willem: 'admin notities maar even een kader voor in Widget Kladblok om zo te splitten'.",
    Component: AdminNotesWidget,
  },
  {
    id: 'connections',
    naam: 'Verbindingen',
    doel: 'Alle externe koppelingen op één plek: LLM (Groq/Ollama), Emergent-key, Bitvavo, poorten. Invullen, opslaan (JSON wint van .env), testen.',
    waar_hoort_het: 'Beheer → eigen tab "Verbindingen" (of Instellingen → Systeem)',
    aangemaakt_op: '2026-09-17',
    aangemaakt_door: 'e1 sessie 59',
    reden: "Willem: 'ik wil geen cloud maar alle connecties, verbindingen, poorten, api's op één plek' — voorbereiding Spark op eigen hardware (Odroid). Sleutels in data/system/connections.json i.p.v. alleen .env.",
    Component: ConnectionsWidget,
  },
  // Volgende sandbox-widgets komen hier:
  // { id: 'xxx', naam: '...', ..., Component: XxxWidget }
];
