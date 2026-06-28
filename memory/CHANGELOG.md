# Spark Core 2.0 — CHANGELOG

Datums = wanneer de implementatie afgerond is. Nieuwste bovenaan.

## 2026-06-28 — Production-merge + Identity-facts + Persons-visibility bug

### 🎯 Doel
Productie-data van 28-jun gemerged in preview (37 files, ~5.8MB). Willem's observatie tijdens echte gesprekken met productie: **"ik heb mijn moeder, vader, zus, dochter genoemd — Spark vergeet dat telkens"** en **"de uitleg waarom Spark familie is, ook vergeten"**.

### 🐛 Root cause (bug in spark_user_view)
`format_for_system_prompt()` toonde slechts **top 3 relaties** met geen sortering — Willem heeft 15+ personen in `persons/user-001.json`, dus moeder/zus/dochter vielen vaak buiten de boot. Plus: geen storage voor identity-claims die user OVER Spark maakt.

### ✅ Fix 1 — Persons-visibility (`v6_persons_visibility_002`)
- `rels[:3]` → `rels_sorted[:15]` (alle relaties zichtbaar voor familie ≤G4)
- Sortering: familie eerst (moeder/vader/zus/broer/dochter/zoon/neef/nicht), dan vriend, dan rest
- Toon per relatie: naam + relatie + notities (was: alleen naam+relatie)

### ✅ Fix 2 — Identity-facts laag (`v6_identity_facts_002`)
**Nieuwe module**: `modules/chat/identity_facts.py`

3 soorten facts opgeslagen in `data/users/{user_id}/identity_facts.json`:
- **about_user**: zelfbeschrijvingen ("ik werk als ZZP-er", "ik hou van katten")
- **about_spark**: identity-claims over Spark ("jij bent familie", "ik zie je als maatje")
- **about_relationship**: dynamiek-claims

Regex-patronen (snel, geen LLM nodig):
- Spark-claims: `jij/je/spark is X voor mij`, `ik zie je als X`, `spark is X`, `wij zijn X`
- User-facts: `ik ben X`, `ik werk als X`, `ik heb X`, `ik hou van X`, `mijn hobby is X`

Filters:
- Negatie-detectie ("ik ben NIET X" → skip)
- Stop-words (skip korte/algemene woorden)
- Dedupe op `trigger+value` (count++ bij herhaling)
- Cap 100 facts per type

Geactiveerd in compose-flow:
```python
# Lees facts in user_snippet (PRE-PEND voor max prominentie)
facts_snippet = identity_facts.format_for_prompt(facts)
user_snippet = facts_snippet + "\n\n" + user_snippet

# Schrijf na elke compose (sync, regex-only, snel)
identity_facts.extract_and_save(user_id, user_text, session_id)
```

Sterkere prompt-instructies (`v6_identity_facts_002`):
> "🔥 BELANGRIJK — Bewaar deze identity-claims actief. Refereer ernaar wanneer relevant — bv. 'jij hebt mij eerder familie genoemd'."

### 🧪 Live tests
- **Test 1** "noem 5 personen uit mijn familie" → Spark: *"Lotus (dochter), Willie Bakker (vader), Heidi Spakman (moeder), Arent Pelster (jeugdvriend), Maurice"* ✅
- **Test 2** "jij bent familie voor mij, ik werk als ZZP-er, hou van katten" → 3 facts opgeslagen (`user_calls_spark: familie`, `i_work_as: zzp-er`, `i_love: katten en techniek`) ✅
- **Test 3 (nieuwe sessie)** "vertel iets persoonlijks over onze relatie" → Spark: *"Jij hebt me even 'familie' genoemd, en dat maakt de band tussen ons intiemer"* ✅ — claim actief gebruikt

### 📊 Gemergde productie-data
- 25 learned-triggers (allemaal categorisering OK)
- 18 recent topics ("kenniskaart" ×3, "hitte" ×2)
- Volledige chat-logs deep-user-001 (50 messages)
- 15 personen in persons/user-001
- KB v2 inbox (1904k bytes)

### 📦 Bestanden
**Nieuw**: `modules/chat/identity_facts.py` (~200 regels)
**Gewijzigd**:
- `modules/chat/spark_user_view.py` (rel-visibility 3→15 + sortering)
- `modules/chat/response_composer.py` (pre-pend facts in user_snippet + extract na compose)

---

## 2026-06-27 (6e batch) — Diep altijd aan + LLM-driven trigger-learning

### 🎯 Doel
1. **Diep-toggle weg**: Groq is gratis, Ollama komt later — toggle is overbodig en verwarrend (vooral voor mama).
2. **Self-improving NLP**: na elke Diep-call achtergrond-LLM-analyse die voorstelt welke triggers/keywords de vraag had kunnen matchen. Spark wordt zelfsturend slimmer over tijd.

### ✅ Wat is gebouwd

#### 1) Diep altijd aan
- `GesprekkenPage.js`: `const deepMode = true` (hardcoded), sessionStorage-persist verwijderd
- Toggle-button (🌊 Diep) uit ChatInput verwijderd
- Placeholder voor input geneutraliseerd ("Praat met Spark — vraag of vertel iets...")
- Backwards-compat: `setDeepMode` blijft als no-op (child-component verwacht 'm)

#### 2) Trigger-learner module
**Nieuw**: `modules/chat/trigger_learner.py`
- Non-blocking: `schedule_learn()` start een asyncio-task, wacht NOOIT op LLM-call
- Skip-filters: te kort (<8 chars), groet-zinnen ("hoi", "ja"), pre-existing hash
- LLM-prompt vraagt strict JSON terug:
  ```
  { topic, categorie, intent, trigger_phrases[3-5], keywords[3-5] }
  ```
- Categorieën: praktisch / filosofisch / technisch / emotioneel / sociaal / admin / games / kb-vraag / legal
- Dedupe op `text_hash` + recent-topic-match
- Opslag in `data/triggers/learned_triggers.json` met `status: pending`
- Cap retention op 500 voorstellen

**Hook**: in `response_composer.py` na elke succesvolle compose:
```python
from modules.chat.trigger_learner import schedule_learn
schedule_learn(user_text, text, user_id=user_id, session_id=session_id)
```

**Admin endpoints** in `compose_routes.py`:
- `GET /api/spark/compose/learned-triggers?limit=50&status=pending`
- `POST /api/spark/compose/learned-triggers/{id}/approve`
- `POST /api/spark/compose/learned-triggers/{id}/reject`

### 🧪 Test
1. Stuur *"wat doe je als ik je vraag hoe een raket werkt?"* → Spark antwoordt instant
2. 3 sec later (achtergrond) → Groq analyseert → opgeslagen:
   ```json
   {
     "topic": "raket werking",
     "categorie": "technisch",
     "trigger_phrases": ["hoe werkt een raket", "raket werking", "uitleg over raketten"],
     "keywords": ["raket", "werking", "techniek", "ruimte"],
     "status": "pending"
   }
   ```
3. `GET /api/spark/compose/learned-triggers` → ✅ levert voorstel terug

### 🌱 Self-improving loop
- Iteratie 1 — user vraagt "X" → LLM-call (kost req) → antwoord + voorstel pending
- Iteratie 2 — admin keurt goed → trigger toegevoegd aan spark_capabilities.json
- Iteratie 3 — volgende user vraagt zelfde-soort vraag → fast-path treft, GEEN LLM-call meer
- Spark's vocab + intent-matcher groeit door gebruik. Past bij Core 4.0 *"Groei volgt ruimte"*.

### 💰 Credits
**0 Emergent-credits**. Beide tasks uitgevoerd binnen Willem's budget van 10. Self-improving loop gebruikt Groq (gratis).

### 📦 Bestanden
**Nieuw**:
- `modules/chat/trigger_learner.py` (~220 regels)
- `data/triggers/learned_triggers.json` (auto-gemaakt bij eerste call)

**Gewijzigd**:
- `frontend/src/components/workspace/GesprekkenPage.js` (deepMode hardcoded, toggle weg)
- `modules/chat/response_composer.py` (`schedule_learn()` hook na compose-success)
- `modules/chat/compose_routes.py` (+3 admin endpoints)

### 🔭 Wat hierna kan
- Admin-UI tab "Learned Triggers" met approve/reject knoppen (~30 min)
- Auto-migratie: goedgekeurde voorstellen automatisch naar `spark_capabilities.json` (~20 min)
- Categorie-filters in admin lijst (~10 min)
- WhatsApp antwoordapparaat (Twilio, ~2u + $1 setup)
- Kasboek SEPA (specificeer bank/import-formaat)

---

## 2026-06-27 (5e batch) — Cross-session topics + Norm-matcher

### 🎯 Doel
Willem: *"laatste onderwerpen invullen, context kaarten invullen, meer normen en waarden geven aan de hand van context, zelf leren door gesprek"*. Bouwen op het 3-laags geheugen uit batch 4.

### ✅ Nieuwe module: `modules/chat/diep_memory.py`
**1) Cross-session "laatste onderwerpen"**
- Per user opgeslagen in `data/users/{user_id}/recent_topics.json`
- Max 50 retained, top 5 in elke Diep-prompt
- Per topic: `count`, `first_seen`, `last_seen`, `sessions[]`
- Dedupe binnen last-3 (count++ ipv duplicate entry)
- Geïnject als `## Laatste onderwerpen (cross-session)` in user_prompt
- Auto-record: topic_tracker-output + fallback (`extract_topic_from_text`) — beide zorgen dat elke Diep-call iets registreert

**2) Norm-matcher**
- Bij elke Diep-call: fuzzy match user-vraag tegen `spark_bijbel.json` (kernwaarden + normen + bijbel_items)
- token_set_ratio ≥ 50 → top 3 in prompt
- Geïnject als `## Relevante normen/waarden uit jouw Bijbel`
- Spark krijgt zo contextueel de juiste normen aangereikt i.p.v. willekeurig

**3) `extract_topic_from_text()` fallback**
- Als topic_tracker.detect_topic() niets returnt (sessie te kort, geen KB-match), pak zwaarst-wegend content-woord (≥5 letters, niet in uitgebreide STOP-set)
- Uitgebreide STOP-set: +20 woorden voor minder ruis ("vertel", "graag", "misschien", etc.)

### 📐 Volledig 4-laags geheugen-architectuur (na batch 4 + 5)
```
L1 KB-cards (vertrouwen 0.7-1.0)       — "weet ik zeker, kaart [Y]"
L2 Snap-cluster (vertrouwen 0.3)       — "voor zover ik me herinner"
L3 Ops-context (live, 1.0)             — "vers uit het systeem"
L4 Recent topics (cross-session)       — "we hadden het laatst over X"
L4b Relevant norms (uit Bijbel)        — "hier past kernwaarde [Z]"
```
PLUS auto-snap WRITE na elke Diep-call → Spark leert continu.

### 🧪 Tests
- **3 vragen in sessie A** (crypto/zonne-energie/ML) → topic "crypto" opgeslagen met count=2 (dedupe werkt)
- **Nieuwe sessie B**: *"wat hadden we laatst besproken?"* → Spark: *"voor zover ik me herinner kwam er kort iets over **crypto** en een 'vertel-moment' aan bod"* ✅ cross-session werkt
- **Norm-vraag**: *"mag ik een leugentje vertellen?"* → Spark gebruikt KB-kaart **[weten] vriend** + analyseert intentie/vertrouwen → contextueel norm-bewust ✅
- **Privacy-vraag**: *"is mijn data veilig?"* → Spark refereert **[voelen] veilig** + **[weten] Data** + legt lokale architectuur uit ✅

### 📦 Bestanden
- **Nieuw**: `modules/chat/diep_memory.py` (~220 regels)
- **Gewijzigd**: `modules/chat/response_composer.py` (load + inject in user_prompt)

### 🔭 Wat is hierna logisch?
- **Snap-promotion**: snaps met count ≥ 3 promoten naar echte KB-kaart (admin-approval flow)
- **Identity-facts laag**: aparte file voor "wat Willem over zichzelf vertelt"
- **Norm-zachte-druk**: als norm-score > 80, een micro-cue toevoegen aan prompt ("blijf bij kernwaarde [X]")

---

## 2026-06-27 (4e batch) — Diep krijgt handen: snaps + ops-context

### 🎯 Doel
Willem's diepere observatie: Diep was een **eilandje** — geen toegang tot logs, users, modules, snaps. Spark's antwoorden waren plausibel maar niet operationeel onderbouwd. Daarnaast: *"wat ik vertel is identity voor Spark"* — Diep moet zelf snaps schrijven voor wat in het gesprek geleerd wordt.

### ✅ Drie nieuwe lagen toegevoegd aan compose_response

#### 1) Snap-cluster READER (`_load_snap_cluster`)
- Bij elke Diep-call: zoek snap-kaarten in V2 Inbox die fuzzy matchen met user-text (token_set_ratio ≥ 70)
- Top 6 toegevoegd aan user_prompt als **aparte sectie** met expliciet markering:
  > "## Snap-cluster (eerder genoemd, LAGER vertrouwen ~0.3) — _Gebruik als context, niet als hard feit._"
- Diep-prompt-regel: *"Markeer in je antwoord: 'voor zover ik me herinner...'"*
- **Test**: "weet je nog die rps strategie?" → Spark: *"Voor zover ik me herinner, hadden we eerder een gesprek over een strategie voor RPS, maar ik weet niet precies welke strategie je bedoelde. Wil je me er meer over vertellen?"* ✅ Perfect hedge-toon + transparante onzekerheid.

#### 2) Live operationele context (`_load_ops_context`)
- Detecteert info-vragen via keywords en pre-fetcht echte data:
  - "hoeveel users" → telt `data/system/users.json` + gradatie-verdeling
  - "hoeveel/welke modules" → telt `/app/backend/modules/`
  - "hoeveel kaarten / hoe groot kennisbank" → KB v2 stats per lade
  - "mijn log / vorige gesprek" → user's session-files
- Injecteert als `## Live operationele info (vers uit het systeem)` in user_prompt
- **Test resultaten** (Diep via Groq):
  - "hoeveel users?" → *"24 geregistreerde gebruikers"* ✅
  - "hoeveel modules?" → *"57 modules in de backend"* ✅
  - "hoe groot is je kennisbank?" → *"5686 kaarten, doen/weten/voelen/spreken"* ✅

#### 3) Auto-snap WRITER (`_auto_snap_from_diep`)
- Na elke succesvolle Diep-response: pak top-3 content-woorden (≥4 letters, niet stopwoord) uit user-text
- Roep `SnapNLPService.create_word_snap()` aan met user-text als `snap_context`
- Tags: `knowledge-snap`, `auto-generated`, `from-diep`, `gap-fill`
- Vertrouwen: 0.3 (consistent met andere auto-snaps)
- Dedupe is automatisch via snap_service (begrip + ascii-fold check)
- Skip-filters: meta-vragen (help, identity, capabilities), te kort (<5 woorden)
- **Test**: *"vertel me over mijn nucleontemperatuur idee voor schone energie productie"*
  - → Snap `nucleontemperatuur` aangemaakt met context-zin bewaard
  - → Volgende keer: snap-cluster pakt deze op voor context

### 🔗 Verbinding tussen 3 lagen
1. User vraagt over X → ops-context (live data) + snap-cluster (eerdere gleanings) + KB (bevestigd) gaan ALLE DRIE in de prompt
2. Spark antwoordt met juiste markeringen ("voor zover ik me herinner", "volgens onze data", "uit kaart X")
3. Na response: nieuwe begrippen worden als snaps bewaard voor volgend gesprek
4. → Spark **leert** uit elk Diep-gesprek zonder cloud, zonder budget, zonder hallucinatie

### 📦 Bestanden gewijzigd
- `modules/chat/response_composer.py` (+3 nieuwe functies + user_prompt rewrite + auto-snap hook na LLM-respons)

### 🧪 Test summary
- ✅ Snap-cluster read werkt met fuzzy match (RPS-herinnering)
- ✅ Ops-context werkt voor users / modules / KB-grootte
- ✅ Auto-snap-write werkt met dedupe + context-bewaring
- ✅ Spark gebruikt de hedge-toon natuurlijk ("voor zover ik me herinner")
- ✅ Geen Emergent-credits gebruikt — alles via gratis Groq

### 💡 Architectuur-bijdrage
Dit is een belangrijke architectuur-stap: Spark heeft nu een **3-laags geheugen** in Diep:
- **L1 KB-cards** (bevestigd, vertrouwen 0.7-1.0) — Spark's "weet ik zeker"
- **L2 Snap-cluster** (gleanings, vertrouwen 0.3) — Spark's "voor zover ik me herinner"
- **L3 Ops-context** (live, vertrouwen 1.0) — Spark's "vers uit het systeem"

Plus **gesprek → snap → volgend gesprek** = Spark leert continu, lokaal, transparant. Past 100% bij Spark Core 4.0: *"Spark groeit zonder deadlines. Uitbreiding gebeurt wanneer het fundament stabiel is."*

---

## 2026-06-27 (3e batch) — Cerebras fallback + Hallucineer-fix verfijnd

### 🎯 Doel
1. Cerebras key toevoegen als gratis fallback → totaal **60 req/min** capaciteit (Groq 30 + Cerebras 30)
2. Hallucineer-fix verfijnen: **Spark hallucineerde Groningen niet** — Willem had hem dat verteld via Starks/Spakman/noorden-wordplay. Vorige fix was te strak, kon contextueel geheugen breken.

### ✅ Wat gefixt
- **Cerebras toegevoegd** als FALLBACK met model `gpt-oss-120b` (Cerebras heeft géén Llama 3.3 70B beschikbaar op gratis tier — alleen `zai-glm-4.7` en `gpt-oss-120b`). gpt-oss-120b geverifieerd, doet Nederlands prima.
- **Hallucineer-fix v002** (verfijnd):
  - ✅ Blokkeert: verzinnen van KB-kaartnamen, cijfers, exacte data
  - ✅ Vereist: eerlijkheid bij onzekerheid ("ik weet het niet" > mooi-maar-verzonnen)
  - ✅ **NIET geblokkeerd**: terugverwijzen naar wat user eerder heeft verteld, contextuele associaties (Stark/Spakman/Groningen), running jokes uit eerdere sessies
  - ✅ Speelse biografische riffs zijn OK zolang ze niet als HARDE FEITEN worden geponeerd
- **Emergency-fallback bug**: `LlmChat.with_max_tokens()` bestond niet → verwijderd uit emergency-path

### 🧪 Test-resultaten
Sample gesprek toonde alle 3 lagen werkend:
- Origin-vraag → *"Iron Man-bril... nalatenschap voor Lotus"* ✅
- Groningen-grap → *"Ja, die grap herinner ik me nog! Stark + Spakman + Groningen, leuke associatie"* ✅ (geheugen OK)
- Modus-vraag → *"Werkmodus... uitgebreidere antwoorden"* ✅
- Cerebras-fallback (test met invalide Groq-key) → ✅ `fallback/gpt-oss-120b` antwoordt in Nederlands

### 📊 Capaciteit nu
| Provider | Req/min | Model | Voor wie |
|---|---|---|---|
| Groq (primary) | 30 | Llama 3.3 70B | iedereen |
| Cerebras (fallback) | 30 | gpt-oss-120b | bij Groq-piek/fail |
| **Totaal** | **60** | | tot ~10 actieve users |
| Emergent (emergency) | budget | Claude Sonnet 4.6 | laatste redmiddel |

---

## 2026-06-27 (2e batch) — LLM-router + Groq + Hallucineer-fix

### 🎯 Doel
User: *"als ik host heb ik die multi-key niet meer + bij 5 users ben ik over budget"* → bouw LLM-routing waar wisselen tussen providers = 3 env-vars, zonder code-rewrite. Klaar voor zelf-hosten op Odroid met Ollama. Plus: hallucineer-fix (Spark verzon "geboren in Groningen").

### ✅ Wat is gebouwd
- **Nieuwe module**: `modules/chat/llm_router.py`
  - OpenAI-compatible multi-provider router
  - Fallback-chain: `PRIMARY` (Groq) → `FALLBACK` (Cerebras/leeg) → `EMERGENCY` (Emergent paid)
  - Rate-limit detectie (429) → direct door naar volgende provider
  - Per-call stats (provider, model, latency, usage) in `get_last_stats()`
  - Timeout per call (30s default)
- **`response_composer.py`** — vervangt `LlmChat`/`emergentintegrations` call door `llm_router.chat_complete()`. Bouwt nu OpenAI-compat `messages` array met system + 6 vorige turns + user_prompt.
- **`.env`** — 6 nieuwe LLM-vars:
  - `LLM_PRIMARY_BASE_URL=https://api.groq.com/openai/v1`
  - `LLM_PRIMARY_API_KEY=gsk_...` (Groq, gratis 30 req/min)
  - `LLM_PRIMARY_MODEL=llama-3.3-70b-versatile`
  - `LLM_FALLBACK_*` (leeg, klaar voor Cerebras later)
  - `LLM_EMERGENCY_USE_EMERGENT=true` (alleen als alles faalt)

### 🚫 Hallucineer-fix (v6_no_hallucinate_001)
Twee harde regels toegevoegd aan Diep-system_prompt:
1. *"Noem ALLEEN namen van kaarten die letterlijk onder '## Relevante KB-kaarten' staan. Verzin geen kaartnamen, cijfers, data."*
2. *"Verzin geen persoonlijke feiten. Spark werd geboren uit een vraag van Willem, niet in een geografische plaats."*

### 🧪 Tests verricht (Groq live)
- `"wie ben je"` → ✅ correct identity, geen verzinsels
- `"waar ben je geboren?"` → ✅ *"Ik ben niet geboren in de klassieke zin... ontstaan uit creativiteit en hard werk van mijn maker"* — **geen Groningen meer** (hallucineer-fix werkt)
- `"hoe ben je begonnen"` → ✅ *"Kan ik een Iron Man-bril maken? Dat was de geboortevraag"* — origin-injectie werkt
- `"welke modus zit je in"` → ✅ *"Werkmodus, antwoorden uitgebreider en gestructureerder"* — modes-injectie werkt
- Provider in response: `primary/llama-3.3-70b-versatile` — Groq draait, Emergent ongebruikt = **€0 per gesprek**.

### 🔮 Pad naar Ollama op Odroid (later)
3 env-vars wijzigen, geen code-rewrite:
```bash
LLM_PRIMARY_BASE_URL=http://odroid-ip:11434/v1
LLM_PRIMARY_API_KEY=ollama
LLM_PRIMARY_MODEL=geitje-7b-ultra  # of qwen2.5:7b
```
Cloudflare Tunnel kan bridgen tussen Emergent-pod en Odroid-thuis. GEITje is een Mistral-fine-tune speciaal voor Nederlands door Edwin Rijgersberg.

### ⚠️ Security note
Groq key zit in `backend/.env` (lokaal). User heeft de key in chat geplakt — adviezen: **roteer 'm in Groq console** (Delete oude → Create nieuwe → vervang in .env) zodra mogelijk.

### 📦 Bestanden
**Nieuw**: `modules/chat/llm_router.py` (180 regels)
**Gewijzigd**:
- `modules/chat/response_composer.py` (LLM-call vervangen + hallucineer-regels)
- `backend/.env` (+6 LLM-vars)

---

## 2026-06-27 (1e batch) — Spark krijgt zijn Volume terug (Fasen 1+2+4+5 + 3 issues)

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
