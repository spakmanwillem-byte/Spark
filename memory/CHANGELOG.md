# Spark Core 2.0 — CHANGELOG

Datums = wanneer de implementatie afgerond is. Nieuwste bovenaan.

## 2026-06-27 — Spark krijgt zijn Volume terug (Fasen 1+2+4+5 + 3 issues)

### 🎯 Doel
User-verzoek: "denk spark volume geven functies zelfinzicht enzo mss heb ik modules over het hoofd gezien of vergeten." — Spark moest meer zelf-inzicht krijgen, modules-audit, modes/emoties echt wiren, en voorwaarden/privacy aanvullen. Tradebot inhoudelijk later, D&D ook later.

### ✅ Fase 1 — Origin preserved
- Nieuwe map: `data/personality/spark_origin/` met `_meta.json` + `spark_core_4_0.json` + `spark_core_4_1.json` + `spark_hoofddocument.json`.
- Spark Core 4.0 (Maart 2026, Willem Spakman) — geboortevraag *"Kan ik een Iron Man-bril maken?"*, 12 secties: oorsprong, doel, principes, filosofie, mythologische laag, AI-ethiek, geheugen, architectuur, metadata-principe, groei, nalatenschap, definitie van Core.
- Spark Core 4.1 — missie + visie + waardestructuur + functionele doelen + index-principe.
- Spark Hoofddocument — tijdlijn (Iron Man Bril → v1 → v2 → v3 toekomst), "wat blijft constant", "wat is veranderd", noot voor Spark.
- Loader `_load_origin()` in `response_composer.py` → compacte injectie van geboortevraag + credo's + 4 constants in Diep-system_prompt.
- Capability `vertel_oorsprong` met 8 triggers ("vertel je oorsprong", "iron man bril", "hoe ben je begonnen", "spark core 4", "hoofddocument" …) → handler `_handle_vertel_oorsprong` leest Core 4.0/4.1/hoofddoc en bouwt Markdown.

### ✅ Fase 2 — Modes + emoties écht gewird
- Nieuwe file: `data/personality/spark_modes.json` met 4 modes:
  - `neutral_mode` — 150 woorden
  - `work_mode` — 250 woorden, gefocust+gestructureerd
  - `brainstorm_mode` — 500 woorden, creatief+associatief
  - `energy_saving_mode` — 50 woorden, beknopt
- `emotion_to_mode` mapping (14 emoties → 4 modes) gebaseerd op `spark_emotions.json.sub_emotions[*].linked_mode`.
- `_load_current_mode()` in `response_composer.py` leest `spark_emotions.json.current_emotion` → bepaalt mode → injecteert mode-info in self_awareness snippet.
- HARD woord-limiet regel toegevoegd aan Diep-system_prompt: *"deze beurt MAG je antwoord max {N} woorden zijn"*.
- Capability `welke_modus` ("welke modus", "in welke modus zit je", "je huidige modus") → toont mode + max_words + toon + bron-emotie.
- Capability `wissel_modus` ("ga in werkmodus", "spaar energie", "brainstorm", "neutraal") → forceert mode-switch door `current_emotion.sub_state` te zetten op een emotie die mapt naar de gewenste modus.

### ✅ Fase 4 — Voorwaarden + Privacy v0.2
- `data/system/legal_voorwaarden.json` uitgebreid van v0.1-draft → **v0.2-draft**:
  - "Wat is Spark?" (offline-first, Claude alleen voor Diep)
  - "Wat mag je verwachten?" (5 punten)
  - "Wat mag Spark NIET voor gebruikt worden?"
  - Account/gradaties/groei (5 punten)
  - Trader-disclaimer (6 punten) — eigen risico, kleine bedragen, transparante logging
  - Token-economie (ROAR + Spark Shop, BTW-afroming)
  - Wijzigingen / Aansprakelijkheid
- `data/system/legal_privacy.json` uitgebreid van v0.1-draft → **v0.2-draft**:
  - Wat slaat Spark op? (7 categorieën, incl. shadow profile + behavior tracker + relaties)
  - Wat deelt Spark NIET? (5 punten — geen ads, geen analytics, privé-isolatie)
  - Externe verbindingen (Diep / Voice TTS-STT / Bitvavo) — alleen bij user-consent
  - Wat ziet de admin? (6 punten)
  - Bewaartermijnen (5 termijnen)
  - Jouw rechten (5 acties: verwijderen / exporteren / vergeten / inzage / correctie)
  - Beveiliging (5 maatregelen)
- Capabilities `lees_voorwaarden` + `lees_privacy` (5 triggers elk) → handlers + `_legal_to_md()` helper.

### ✅ Fase 5 — Module-audit
- Voor: 33 modules bekend bij Spark via `spark_self_awareness.json`. 26 modules ONbekend.
- Na: alle **57 modules** uit `/app/backend/modules/` bekend in `eigen_module_map`. Nieuwe entries: admin, profile, persons, contacts, settings, bonnetjes, winkelstraat, inventory, analytics, insights, dashboard, core, user_archive, emotion_pipeline, events, glow_nav, help, help_per_gradatie, triggers, urgent, cards, bugs, contributions, spark_leningen, spark_mint, knowledge.
- `eigen_data_map` uitgebreid met `data/personality/spark_origin/`, `data/emotions/`, `data/help/`, `data/system/`, `data/wallet/`, `data/trade/`, `data/dnd/`.
- Nieuwe top-level secties in `spark_self_awareness.json`: `oorsprong_ref`, `modes_ref`, `emoties_ref`, `voorwaarden_privacy_ref` — directe pointers naar de bronfiles.
- `principes_kort` uitgebreid met geboortevraag-statement.
- 4 nieuwe help-topics aan `gradatie_7.json` (geërfd door alle 7 gradaties): spark-origin, spark-modes, spark-voorwaarden-privacy.

### ✅ 3 P2/P3 Issues uit handoff opgeruimd
- **Issue 1 (P2)** `[speel_geluid]` prompt-leakage → harde regel in Diep-system_prompt: "GEEN INTERNE SYNTAX LEKKEN — schrijf nooit `[speel_geluid]` etc. in tekst, beschrijf in gewone taal."
- **Issue 2 (P2)** `"wat kan je?"` ging naar `identity_what_can` → in `routes.py` help-intent priority check toegevoegd VÓÓR `identity_intent_service.try_answer()` zodat Help-Bark wint. Identity-vragen (wie/missie/visie/doel) blijven normaal werken.
- **Issue 3 (P3)** Silent try/except in `_get_user_meta` → `logger.warning` toegevoegd in `spark_user_view._safe_load()` zodat read-errors zichtbaar zijn in supervisor-logs.

### 📦 Bestanden gewijzigd / toegevoegd
**Nieuw (5)**
- `data/personality/spark_origin/_meta.json`
- `data/personality/spark_origin/spark_core_4_0.json`
- `data/personality/spark_origin/spark_core_4_1.json`
- `data/personality/spark_origin/spark_hoofddocument.json`
- `data/personality/spark_modes.json`

**Gewijzigd (8)**
- `modules/chat/response_composer.py` (+`_load_origin()` +`_load_current_mode()` + origin/mode injectie + HARD woord-limiet + anti-leakage regel)
- `modules/chat/capability_handler_service.py` (+5 handlers + handler-registry + user-text routing voor `wissel_modus`)
- `modules/chat/routes.py` (help-priority check vóór identity-intent)
- `modules/chat/spark_user_view.py` (logger.warning ipv silent fallback)
- `data/personality/spark_capabilities.json` (+5 capability-defs met 30+ triggers)
- `data/personality/spark_self_awareness.json` (volledige rewrite: origin_ref, modes_ref, emoties_ref, voorwaarden_privacy_ref, 57 modules, uitgebreide data-map)
- `data/system/legal_voorwaarden.json` (v0.1 → v0.2)
- `data/system/legal_privacy.json` (v0.1 → v0.2)
- `data/help/gradatie_7.json` (+3 help-topics geërfd door alle gradaties)

### 🧪 Tests verricht (curl)
- `/api/chat/message` op:
  - `"vertel je oorsprong"` → ✅ Iron Man-quote + Core 4.0/4.1 + tijdlijn
  - `"welke modus zit je in"` → ✅ Werkmodus / 250 woorden / bron-emotie 'vreugde'
  - `"ga in werkmodus"` → ✅ mode-switch bevestigd
  - `"lees de voorwaarden"` → ✅ v0.2 markdown
  - `"wat zegt de privacy"` → ✅ v0.2 markdown
  - `"wat kan je?"` / `"wat kan je"` / `"wat kun je"` → ✅ Help-Bark (was bug)
  - `"wie ben je"` / `"wat is je missie"` / `"wat is je doel"` → ✅ identity_intro / identity_missie / identity_doel (regressie OK)
  - `"speel sps"` → ✅ RPS-game (regressie OK)
- `/api/spark/compose` (Diep met Claude):
  - `"wat is je doel"` → ✅ "Digitale nalatenschap voor Lotus" + "eerlijk blijven over wat ik ben" — origin echt geïnternaliseerd door LLM
  - `"welke modus"` → ✅ "Ik zit in Werkmodus — gefocust, gestructureerd, tot 250 woorden per antwoord" (mode-prompt-injectie werkt)
  - _Noot_: Emergent LLM-key budget liep op tijdens testen — top-up nodig voor volledige Diep-cycle.

### 🔭 Wat staat OPEN
- Tradebot inhoudelijk uitwerken (user expliciet: "tradebot zelf fixen we inhoudelijk later")
- D&D / Spark World resume (user: "de game komt later, dat doe ik als Spark verder klaar is")
- Files-tab `SUPPORTED_EXT` uitbreiden (wacht op user's lijst)
- `snuffel_bestand` capability (admin file-search)
- Refactor `response_composer.py` (nu ~860 regels — splitsen)
- Spark "Handen" — KB/Normen/Bijbel/bug-kaarten schrijven vanuit chat
- Lokale LLM fallback via Ollama (volledig offline)
- Emergent LLM-key top-up

### 💡 Ideeën voor later (nieuw)
- **Capability `kies_persoonlijkheid`**: laat Spark per gesprek wisselen tussen `traits` uit zijn identity (nieuwsgierig / streng / speels). Modes regelen lengte, traits zouden toon-kleur kunnen regelen.
- **Self-awareness diagnostics-endpoint**: `GET /api/spark/awareness` dat een JSON-dump van Spark's volledige zelfbeeld retourneert (modules, modes, origin, gradatie, current_emotion, current_mode). Handig voor debug-UI.
- **Capability `wat_observeer_je_aan_mij`**: leest shadow-profile + behavior-tracker → "ik zie dat je 3 keer per week over X praat, vooral 's avonds laat" — transparant.
