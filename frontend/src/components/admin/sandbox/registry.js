/**
 * v10_sandbox_registry_001 — Sandbox widget registry (Willems verzoek sessie 47).
 *
 * DOEL: Tijdelijk parkeer-plek voor front-end kaders die nog geen definitieve plek hebben.
 * Als je een nieuwe widget bouwt en niet zeker weet waar hij hoort, registreer 'm hier.
 * Later verplaats je 'm naar zijn definitieve module met 1 regel: verwijder uit deze array,
 * importeer 'm daar.
 *
 * BEST PRACTICE: elk widget = een zelfstandige `.js` file in `./widgets/`.
 * Kader heeft eigen state, eigen fetch-logica, geen dependency op de sandbox zelf.
 * Zo kun je 'm 1-op-1 verplaatsen naar bv. AnalyticsPage door daar te importeren:
 *
 *   import { LlmTokenUsageWidget } from './sandbox/widgets/LlmTokenUsageWidget';
 *   <LlmTokenUsageWidget />
 *
 * Willem's woorden sessie 47:
 * > "kaders in containers doen. dan hoef je dat alleen te verplaatsen."
 */
import { LlmTokenUsageWidget } from './widgets/LlmTokenUsageWidget';

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
  // Volgende sandbox-widgets komen hier:
  // { id: 'xxx', naam: '...', ..., Component: XxxWidget }
];
