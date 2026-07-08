# Willem's Ideeën & Correcties tijdens Bouwen

> Doel: geen enkele goede gedachte verloren laten gaan. Als Willem tussendoor iets zegt dat een idee, correctie, of betere oplossing is → hier vastleggen met datum + context.
> Format: nieuwste bovenaan.

---

## 2026-07-08 — Sessie 46 (fork)

### 🔴 Correctie: cooldown-fix is een pleister
- **Context**: agent bouwde 30-min EUR-cooldown na INSUFFICIENT_EUR_BALANCE
- **Willem's inzicht**: 22 potjes zouden 1-op-1 met Bitvavo moeten zijn. Als tekort optreedt → **er is een sync-mismatch**, geen kwestie van "even wachten". Root cause zit dieper (pot claimt kapitaal dat niet meer op Bitvavo staat).
- **Wat te doen**: root-cause via `/api/trade/delta`, cooldown blijft als vangnet.

### 🟢 Idee: Spark leest zijn eigen fundament
- **Context**: Willem vroeg trader-inhoudelijke vraag, Spark hallucineerde antwoord via LLM (geen KB-hit).
- **Willem's model**:
  ```
  trade.md (mens-editeerbaar, SOT)
    ↓ voedt
  KB v2 kaart "Spark Trader" 
    ↓ ingebed in compose bij trader-vraag
    ↓ hyperlink in legal voorwaarden
  ```
- **Regel**: "Help-data is single source of truth" — nu uitgebreid: **module-data is single source of truth**.

### 🟢 Idee: Elke Python-script ↔ parallel blueprint.json
- **Context**: 4 van ~55 modules hebben runtime-config-JSON gescheiden van code.
- **Willem's wens**: uitbreiden naar alle modules — zodat je reacties/limits/prompts kunt tunen ZONDER script aan te raken.
- **Bestaande infra**: `modules/core/blueprint.py::load_blueprint_cached()` — klaar voor gebruik.

### 🔵 Bouwregel voor deze sessie (en verder)
- **GEEN nieuwe features**. Alleen: bestaande dingen **afmaken**, **verbinden**, **volume geven**.
- Voorbeelden van "volume": module-blueprint markdown vullen, KB-kaarten genereren, code-config uit script trekken naar JSON.

---

_Update-instructie voor volgende agents: bij elke sessie hier bovenaan een nieuw datum-blok toevoegen. Nooit oude eruit halen._
