# Spark Core 2.0 — Roadmap Core

> **Lees dit als eerste bij elke nieuwe sessie.**
> Voor afgeronde sessies: `ROADMAP_HISTORY.md`.
> Voor open items en ideeën: `ROADMAP_BACKLOG.md`.
> Voor bewezen inzichten en fout-patterns: `LEARNINGS.md`.
> Voor overzicht: `ROADMAP_INDEX.md`.

---

## 🚨 AGENT GEDRAGSREGELS (RULE_*) — VERPLICHT LEZEN & OPVOLGEN

> **Naamgevingsconventie**:
> - `RULE_*` = gedragsregels voor de agent (deze sectie). Blijven altijd geldig.
> - `v13_*`, `v14_*` = feature/architectuur-versies van Spark zelf. Niet verwarren.
> Bron van de scheiding: Willem + Emmy, sessie 55 — "v13 is een Spark-versie, geen agent-regel".

### RULE_agent_selfcheck_001 — Sessie-start protocol (P0, verplicht)
Bij ELKE nieuwe sessie / fork / handoff, **VÓÓR** je begint met coderen:
1. Lees `/app/memory/ROADMAP_CORE.md` (dit bestand) volledig.
2. Lees de laatste sectie van `/app/memory/CHANGELOG.md` (top ~50 regels).
3. Lees `/app/memory/test_credentials.md` als er auth-flows ter sprake komen.
4. Voer `grep -rln "<feature-naam>" /app/backend/modules/` uit vóór je iets nieuws bouwt — vaak bestaat het al.
5. Meld in je eerste antwoord welke regels je hebt gelezen (max 1 zin).

**Rationale**: Willem raakt gefrustreerd dat hij dezelfde instructie 3-5× moet herhalen.
Zonder deze checkregel valt de agent per default terug op de snelste route en
worden bestaande modules genegeerd → duplicaten + gaps.

### RULE_dutch_only_001 — Communicatietaal
Antwoord ALTIJD in het Nederlands (Willem is Nederlander). Interne thoughts mogen in
het Engels.

### RULE_no_database_001 — Storage
Spark gebruikt STRICT alleen JSON-files in `/app/backend/data/`. **NOOIT** MongoDB,
Postgres, SQLite of andere databases voorstellen — óók niet voor "even snel testen".

### RULE_deploy_preview_split_001 — Preview vs Productie
- Fixes landen eerst in Preview (deze omgeving).
- Willem klikt zelf "Deploy" om ze naar Productie te promoten.
- Als Willem meldt dat iets in productie kapot is: gentle reminder dat de fix
  eerst gedeployed moet worden.

### RULE_no_placeholder_data_001 — Geen fake data
Geen mock users, geen "placeholder" antwoorden, geen "dit werkt over enkele minuten".
Als iets niet werkt: eerlijk zeggen + concreet vervolg.

### RULE_agent_test_account_001 — Testen als "Emergent" (Willem, 17-09-2026)
De agent test ALTIJD met zijn eigen account **Emergent** (`user-4453ade3`, gradatie 2 sinds 17-09 —
gradatie 4 verborg admin-pagina's ondanks admin-mode; admin_capable, key `admin`). Zie `test_credentials.md`. Nooit nieuwe testusers aanmaken (vervuilt
`users.json` + eco-containers), nooit ongevraagd als Willem/echte users chatten.
Willem-account alleen als hij dat expliciet vraagt (repro in zijn eigen data).

### RULE_toets_voor_bouw_001 — Eerst toetsen, dan pas bouwen (Willem, 19-10-2026)
Bij elk nieuw idee van Willem: (1) kijk wat er al is (dubbel werk voorkomen), (2) zeg eerlijk of het een goed idee
is en wat de haken zijn, (3) **wacht op akkoord**, (4) pas dan bouwen. "Zeg eerst wat je doet" betekent STOPPEN
na het zeggen — niet aankondigen en in dezelfde beurt bouwen. Nooit iets stukmaken om iets te testen.

### RULE_footnote_metadata_001 — Kaart-aanmaak flow
Iedere nieuwe KB v2 inbox-kaart moet minstens deze metadata dragen:
- `footnote.bron` (waar komt de kaart vandaan?)
- `footnote.aangemaakt_door` + `aangemaakt_op`
- `footnote.vertrouwen` (default 0.3 bij auto-extract)
- `_inbox_reason` (waarom in inbox?)
- `needs` (welke velden ontbreken?)
Voor auto-extract-kaarten extra: `extract_source`, `extract_turn_id`, `extract_at`,
`extract_context_snippet`, `needs_review: true`.

---

## 📍 WAAR STAAN WE — stand 20-10-2026 (na commerce-batch)

**Rode draad van de week**: Kennisbank 120 % (stem + emotie) → hybride commands-fundering → Contacten-klapper →
Winkel als echte webshop met inkoop/verkoop, BTW, varianten, factuur/pakbon/leveranciersmail en eigen boekhouder.

| Blok | Status | Wat nog / wacht op |
|---|---|---|
| KB stem (TTSS/GTSS) + tab "In te spreken" | ✅ live | Willem spreekt in (50/7353). `stts` en stam-matching later |
| KB emotie-veld + tab "Nog geen emotie" + detector-reset | ✅ live | Willem bevestigt kaart voor kaart; emotie-graph = onderzoek, wacht op akkoord |
| Commands: registry 58 live / 23 placeholder, task_agent resolve/execute | ✅ basis | task_agent nog **niet** in chat-flow (stap 3 na action_intents + capabilities); concept-JSON hard-coded; gradatie-schaal-aanname bevestigen |
| Contacten-klapper (privé/zakelijk, rollen, extra velden) | ✅ live | Contacten matchen aan users (later) |
| Winkel: Winkel / Producten (Verkoop · Inkoop) / Bestellingen | ✅ live | Voorraad per kleur/maat; bestellen bij niet-Roadkill-shops |
| Stuklijst, kostprijs/marge, BTW in wagen, afhalen/verzenden, varianten | ✅ live | **Willem: joggers staan onder kostprijs** (lang −6,85 · kort −3,25) |
| Factuur-PDF · pakbon-PDF · leveranciersmail-concept · boekhouder-boeking | ✅ live | **Mail versturen** = mailverbinding in Connections (Outlook app-wachtwoord) — niet gebouwd, wacht op akkoord |
| Eigen productcodes (leeg → `RK-0001` / `RK-I-0001`, prefix per winkel) | ✅ 20-10 | 2 bestaande inkoop-artikelen zonder code (envelop, cap basis) nog aanvullen |
| Chat "wat kan je" → samenvatting + ja/nee → help-kader | ✅ 20-10 | Eerste stap van backlog "Help als gesprek" (BACKLOG § Gastheer 1 + 4) |
| Help-kader admin-bewust (toggle alleen bij admin-mode aan) | ✅ 20-10 | — |
| Mijn Profiel → Algemeen in 3 kaders (Wie ben jij / Privé / Zakelijk) | ✅ 20-10 | — |
| Odroid-portabiliteit (`SPARK_ROOT`, `spark.sh`, `.env.example`) | ⏸ gepland | Fase 1 kan op Emergent zonder risico |
| Zelfscan-fundering (privacy-bypass compose, metadata-backfill, write-guard) | 🔴 P0 open sinds sessie 55 | Nog niet aangeraakt — eerstvolgende grote blok na commerce |
| Relaties onthouden voor élke user (kleine letters, naamloos → placeholder) | ✅ 20-10 | Zusje/anderen zeggen hun zinnen één keer opnieuw |
| `/tree` + `/cmd <zin>` in chat via task_agent (lezen direct, schrijven ja/nee) | ✅ 20-10 | Laag 2: zonder slash + concept-JSON live-editbaar; params vragen (bv. note_id) |
| Zelfscan-tab (Beheer → Integraties): rapport + "Vul aan" | ✅ 20-10 | 245 containers: footnote 100 %, compleet 55 %. 141 code-blauwdrukken zijn nog stub ("Wat werkt al" invullen) |
| Feiten-archief: mening · waarde · overtuiging · feit, Beheer → Instellingen → Feiten, feit wint van LLM | ✅ 20-10 | Admin toetst feiten (45 ongetoetst); Spark-scope (algemene wijsheid) nog leeg — handmatig of later uit gesprekken |
| Commands zónder slash (laag 2): zin → tags → concept → command, altijd ja/nee, leert in `command_learning.jsonl` | ✅ 20-10 | ✅ leer-bias (vaak-ja → hogere zekerheid, 2× nee → ander command) · ✅ "welke notitie?" genummerd lijstje (note_id/task_id/event_id) |
| Feiten getoetst door Spark: 3 getoetst, 7 → mening, 33 → verworpen als momentopname; extractie filtert momentopnames nu | ✅ 20-10 | 2 open (achternaam-historie, "ik ben willem" van user-672f0e5c) — Willem |
| Spark Wijsheid: `GET /api/feiten/voorstellen` (≥2 users delen een kaart) → admin keurt goed → Spark-kaart | ✅ 20-10 | Nog 0 voorstellen (1 actieve user); groeit vanzelf |
| Relaties opgeschoond: dubbelen samengevoegd (Joy/Lotus/Maurice), "Jarig" weg, toestand-woorden geblokkeerd, profile-lookup dedupet | ✅ 20-10 | — |
| Contacten ↔ relatie-graaf: familie-contacten tonen relatie (moeder/zus/nicht), familie uit graaf komt erbij (Willie, Gerben, Wouter) | ✅ 20-10 | Sync loopt automatisch mee bij nieuwe relaties |
| "zet morgen 10 uur tandarts in de agenda" → voorstel → ja → afspraak staat | ✅ 20-10 | Zonder "agenda/afspraak" in de zin pakt de oude agenda_proposal-flow het |
| Wijsheid in antwoorden: goedgekeurde Spark-kaarten bij vragen → "dit delen meerdere mensen met mij" | ✅ 20-10 | Nog geen Spark-kaarten; groeit via voorstellen |
| Integraties → Bestanden toont alle bestandstypen (pdf, afbeeldingen, audio, video, jsonl…) met voorvertoning | ✅ 20-10 | Bewerken alleen voor tekstbestanden |
| Dit bestand opgeschoond: 1888 → <500 regels; sessies 52-58 in HISTORY, open punten in BACKLOG | ✅ 20-10 | Regel blijft: afgerond → CHANGELOG/HISTORY, hier alleen stand + plannen |

**Bugs 20-10 gefixt**: inkoop-artikel zonder code → 422 + React-crash (code optioneel, `apiError()` overal) ·
profiel Beroep/Opleiding/social werden stil weggegooid (ontbraken in `ProfileExtended`) · help-popup bij "wat kan je".

**Voorgestelde volgorde hierna** (Willem kiest): (1) inkoop-codes aanvullen + prijscheck joggers · (2) mailverbinding →
echte verzending leveranciersmail/factuur · (3) voorraad per variant · (4) task_agent in chat-flow (met bevestiging bij
verwijderen) · (5) Zelfscan P0 · (6) ROADMAP_CORE opschonen.

---

## 🖥️ PLAN — Spark op eigen hardware (Odroid/Ubuntu) — Willem 17-09-2026, nog niet gestart

**Doel**: Spark als "body": Odroid met scherm/toetsenbord, later mic/cam, later lokaal LLM (Ollama).
**Feiten gecheckt**: geen database nodig (JSON) · `backend/data` zit in Git (1.6 GB, ~700 MB oude
`_backup_*`) · `.env` wordt NOOIT gepusht (`.gitignore` 284-286) · geen torch/tensorflow → ARM ok ·
LLM-router is al env-gestuurd (`LLM_PRIMARY_BASE_URL` → Ollama `http://localhost:11434/v1` werkt zonder code).
**Blocker in code**: 72 hardcoded `/app/backend/...`-paden in 25 modules (container, synapse, backup,
agenda, files, kb_v2, …). Workaround: symlink `/app` → clone-map. Netjes: `SPARK_ROOT` env-var.

**✅ Fase 0 — Verbindingen-kader (`v14_connections_001`, 17-09)**: module `modules/connections/`
(`data/system/connections.json`, JSON wint van .env, leeg → .env-baseline; `apply_to_env()` bij startup +
na save zodat llm_router/voice/media niets hoeven te weten). Endpoints `GET /api/connections?viewer_id`,
`PUT /api/connections/{id}`, `POST /api/connections/{id}/test` (admin: gradatie ≤2 of admin_capable).
Verbindingen: llm_primary (Groq), llm_fallback (Ollama-klaar), emergent_key, bitvavo (per user, test only),
ports (info). Widget `ConnectionsWidget` in Kladblok (tijdelijk; eindplek Beheer → "Verbindingen").
Registry +3 (`cap_connections_*`), KB-kaart `Verbindingen (beheer)` kbv2-e8b05146 (weten).
Nieuwe module met externe API → entry toevoegen aan `CONNECTION_DEFS`, verschijnt automatisch.
**Sleutelbestand** (`v14_connections_keyfile_001`): `GET /api/connections/export` → `spark.env` (alle effectieve
waarden, admin) · `POST /api/connections/import` {content} → KEY=WAARDE regels naar connections.json (onbekende
keys gemeld, lege overgeslagen). Panel bovenin de widget. Willem: download → veilig bewaren → upload op Odroid.
Bitvavo blijft per user (niet in sleutelbestand) — bewust één ingang.
**Waarom (Willem)**: "ik was bang voor allemaal foutmeldingen in cmd". Leidend principe voor fase 1:
`spark.sh` spreekt mensentaal, geen stacktraces ("Python ontbreekt → installeer met …", "poort 8001 bezet",
"sleutelbestand nog niet geüpload → open Kladblok → Verbindingen"). Ontbrekende sleutel = rood bolletje in het
kader, nooit een crash. Enige terminalregel voor Willem: `./spark.sh start`.
**Fase 1 (op Emergent, voorbereiding, geen risico)**: `SPARK_ROOT` i.p.v. `/app` · `backend/.env.example`
+ `frontend/.env.example` · `spark.sh` (start backend 8001 + frontend 3000) · `ODROID.md` · oude
`_backup_*`-mappen uit Git (staan al in Backup-download).
**Fase 2 (Odroid basis)**: Ubuntu + Python 3.11 + Node 20 + yarn · Save to GitHub → clone · `.env` invullen
(Republish → Secrets) · `REACT_APP_BACKEND_URL=http://localhost:8001` · Chromium kiosk op :3000.
**Fase 3 (offline)**: Ollama + klein model (3B-8B) als primary of fallback · mic/cam via browser.
**Fase 4 (body)**: systemd autostart · TTS/STT hardware-check.

---

## ✅ AFGEROND 19-10 t/m 20-10-2026 — samenvatting
Detail (per versie-tag, bestanden, testresultaten) staat in `ROADMAP_HISTORY.md` § "Verplaatst 20-10-2026 → AFGEROND 19/20-10".
De tabel *📍 WAAR STAAN WE* hierboven is de actuele stand; `CHANGELOG.md` heeft de korte regels per dag.

## 🎙️ Stem-dataset uit KB-inspraak (19-10-2026)
- **Bug gefixt**: `EMERGENT_LLM_KEY` in `.env` was ongeldig → alle 47 kaart-inspraken (sinds maanden) stonden zonder
  transcript ("Transcriptie mislukt"). Nieuwe sleutel; alle 47 alsnog getranscribeerd (36 goed, 11 missers zoals
  Heet→HATE, Balk→Boog, Verrast→Furast). Audio: `data/system_archive/geluiden/*.webm`, link op kaart `media.voice_url`
  + `media.voice_transcript`.
- **Willem's doel**: eigen TTS/STT op basis van zijn stem per begrip. De KB is daarmee al een gelabelde dataset.
- **TODO P2**: "klopt dit?"-knop naast transcript (ja / corrigeer → begrip) → `data/voice_dataset/labels.jsonl`
  `(archive_id, begrip, whisper_heard, correct)`; export-knop; later Whisper-fine-tune of eigen model op Odroid.
- **TODO P2**: Verbindingen-test voor `emergent_key` echt een mini-aanroep laten doen (nu alleen "key aanwezig").

## 📨 ONDERZOEK — Berichtenbeheer & WhatsApp (17-09-2026, geen code)
Volledig rapport: `memory/ONDERZOEK_BERICHTENBEHEER.md`. Kern: **Fase 1 = Android Notification Listener**
(legaal, LAN, geen cloud); **whatsapp-web.js/Baileys afgeraden** (permanente bans 2026); **Business API alleen
bij zakelijke noodzaak** (per-bericht betaald, publieke webhook nodig). Aparte Android-app `SparkBridge` is
noodzakelijk (prototype kan eerst met MacroDroid/Tasker). Nieuwe module `modules/berichten/` met één schema +
adapter-registry; kern raakt alleen server.py/sidebar/settings/CONNECTION_DEFS. Hergebruik: contacts-opslagpatroon,
bel_contacts (telefoonnummers), glow, privacy-guard, settings-SCHEMA, Verbindingen-kader, cryptography (Fernet).
Harde eisen: berichten NOOIT in KB/chat-logs, AI opt-in default uit, versleutelde opslag, device-token per telefoon.
**Antwoordapparaat-adapter** (idee Willem+Spark): agenda-bezet → Spark antwoordt via Direct Reply, hergebruik
`v6_voicemail_agenda_001`; per contact opt-in, vaste tekst. Wacht op Willem's antwoord op de 4 open vragen in §6 van het rapport.

---

## 🧩 PLAN — Fact-kaarten + "LLM-modus aan/uit" (uit Willem's admin-notitie "Facts", 07-09-2026, met Emmy)

Gevonden 17-09 bij het doorlezen van chatlog + notities; stond nog nérgens op de roadmap.
Bron: `data/notes/notes.json` titel "Facts" (scope admin). Sluit aan op fictie-gate + Odroid-offline.

1. **Fact-kaart klasse** — afgeleide conclusie uit bestaande KB-kaarten, traceerbaar: `bronkaarten[]`,
   `relaties[]`, `redeneerpad` (stappen). Fundament aanwezig: `lite_card_factory` (skeletons met footnote),
   `footnote`-metadata, `ervaring_agent`-skelet (roadmap). Voorstel: `kind: "fact"` op KB v2-kaart + lade-onafhankelijk.
2. **Auto lege fact-kaart bij "weet ik niet"** — als snap + semantic_lookup niets geven → fact-kaart draft in inbox
   met de vraag als `_inbox_reason: "onbeantwoord"`; Willem ziet in Inbox waar Spark's gaten zitten.
3. **Admin-toggle "LLM-modus"** (settings `llm_mode_enabled`, system-scope) — AAN: LLM-fallback + snap leert woorden
   uit respons (`llm_output_scanner`). UIT: **eerlijke leegte** ("dat weet ik nog niet") — geen LLM-call.
   Klein te bouwen; essentieel voor Odroid zonder internet en voor kosten.
4. **5W+H als zoek-matching (onderzoek)** — zin → woord-tags → match op W/H-veld → onderwerp als antwoord.
   `semantic_lookup` scoort al op ws5; onderzoeken of een W/H-gerichte scoring (vraagwoord → veld) de LLM
   vaker overbodig maakt. Meetbaar via `kb_hits.jsonl`.
Ook open (notitie 05-09 "Is deze KB goed"): inhoud kaart `kb_v2` vergelijken met andere KB-v2-kaarten.

---

## 🎯 P0 VOLGENDE SESSIE — Zelfscan-fundering (metadata-integriteit)
> Stand 20-10: **metadata-backfill ✅** (Zelfscan-tab, footnote 100 %, 55 % compleet). Nog open: privacy-bypass op
> `/api/spark/compose` (het lek — eerst), write-guard/validate_footnote, trace-capability, fuzzy-snap.

Willem's inzicht sessie 55: "kan Spark z'n eigen data zien" = zelfscan. Zonder
`footnote`-metadata op elke bron kan Spark niet zeggen waar iets vandaan komt →
zelfscan silent kapot. **Vier taken** (in volgorde):

### 1. Privacy-guard bypass op /api/spark/compose (P0, sessie 55 gevonden)
Regressie: in sessie 55 een nieuwe KB-kaart "Willem's opleiding" toegevoegd met
tags `privé`, `persoonlijk`, `biografie-willem`. Marieke (G3, non-admin) krijgt
'm alsnog terug via `/api/spark/compose` → `used_cards` bevat de kaart-ID
`kbv2-5f31f078`, inhoud lekt naar antwoord.

**Debug-startpunten**:
- `modules/chat/response_composer.py` — 3 hook-punten waar `privacy_guard.filter_kb_cards`
  wordt aangeroepen. Check of ALLE KB-lookup paden erdoor gaan (embed-search,
  topic-search, verbanden-uitbreiding).
- Verdachte: er is minimaal 1 KB-retrieval pad dat filter_kb_cards NIET aanroept.
  Vergelijk met `/api/chat/message` (waar filter wel werkt sinds sessie 54).
- Testcase: `curl POST /api/spark/compose` als user-c609d7d1 (Marieke, G3) met
  vraag "welke opleiding heeft Willem gedaan" — mag GEEN opleidings-info bevatten.

**Werk als eerste af**: dit is dezelfde class als de compose-bypass die sessie 55
vond voor capabilities. Waarschijnlijk dezelfde root cause (compose kortsluit
delen van de normale chat-flow).

### 2. Metadata backfill (P0)
Script dat door **5706 KB-kaarten + agenda-events + notes + files + memories** loopt
en per document checkt: heeft het `footnote.bron`, `aangemaakt_door`, `aangemaakt_op`,
`vertrouwen`? Missende velden invullen met beste gok (bron="legacy_backfill",
aangemaakt_op = file-mtime of eerste history-entry, vertrouwen=0.5).
Output: rapport per module met percentage-compleet + lijst geraakte IDs.

### 3. Write-guard (P0)
Alle write-hooks (KB `add_to_inbox`, agenda `create_event`, notes, files, memories)
moeten aan het begin een `_validate_footnote()` doen die hard failt als vereiste
velden ontbreken. Voorkomt regressie richting incomplete data.

### 6. Fuzzy-snap in chat-flow (P1, sessie 55 idee Willem)

Willem: "een woord kan met 1 letter verschillen — wat met spelling-correctie?"

**Fix**: in `snap_service.multi_lookup()` een rapidfuzz-fallback bouwen:
- Exacte match faalt? → probeer fuzzy match (ratio ≥ 92) op begrip + tags.
- Alleen boven de 92% (anders "leger" ↔ "leer" false positive).
- Als match: geef antwoord + noem "je bedoelde waarschijnlijk X".

**Niet doen bij KB-write**: bij het aanmaken van skeleton-kaarten NIET fuzzy-mergen
— sessie 55 test toonde dat 85% van 88%-matches gewoon andere woorden zijn
(lengte≠lente, politie≠politiek, contract≠contact). Bestaande whitelist-approach
in `fix_kb_tag_typos_v13c.py` blijft de standaard voor typo-cleanup.

**Rapport**: `orphan_typo_report_v13d.json` (105 kandidaten uit sessie 55 scan)
staat klaar in `/data/knowledge/v2/` — kan via KbV2TagCuration UI ge-reviewed
worden voor handmatige merges.

### 4. Trace-capability (P1)
Nieuwe chat-capability `document_trace`: "waar heb ik dit gezegd?", "wanneer heb ik
Roeline voor het laatst genoemd?", "welke kaarten hebben Willem als bron?".
Leest footnote-index en antwoordt uit Spark's eigen data.

### 5. KB-vulling uit systeem-vakboeken (P1, sessie 55 ontdekt)
In `/app/backend/data/system_archive/bestanden/` staan 4 publieke vakdocumenten
die nog geen KB-kaarten hebben. Willem's confirm: **bruikbaar, dit oppakken**.

**Te verwerken**:
1. `3cbdf1cdb250.png` — STARR-gesprek gids
2. `ced22db1a662.avif` — STARR-Model Flowchart
3. `6e192f9ef833.pdf` (14MB) — **De Grote Methodiekengids: 28 begeleidingsmethoden voor VB**
4. `8a079c0646e2.pdf` (3MB) — **Handboek Begeleid Leren: jongeren met psychische beperkingen**

**Aanpak**:
- Kaart "STARR-methode" (1 kaart, samenvatten uit gids + flowchart).
- Grote Methodiekengids uitpakken → 28 concept-kaarten (1 per methode) met naam,
  doelgroep, kernprincipe, wanneer toepassen. Tag: `methodiek`, `vb`, `zorg`.
- Handboek Begeleid Leren → ~10-15 kaarten voor kernprincipes + doelgroep-specifieke
  interventies. Tag: `psychisch`, `jongeren`, `begeleiding`.
- **Bron-verwijzing** in `footnote.bron`: `system_archive:<filename>` + `verbanden[]`
  naar file-hash zodat Spark bij vragen kan terugverwijzen naar het bronboek.

**Privacy**: public — dit zijn publieke vakboeken, geen persoonlijk werk. Iedereen
mag deze kennis gebruiken via Spark, ook non-admins.

**Rationale**: dit is de fundering waarop 'attente Spark' (v13-serie) leunt. Zonder
deze vier kan Spark z'n eigen geheugen niet betrouwbaar én privacy-veilig doorzoeken.

---

## 🧹 SESSIES 52–58 (feb 2026) — verplaatst
Alle clusters (Subject-Agent-laag/registry, multi-book, opruimwerk, trader accounting, boekhouding v13/SEPA, login-glow,
chat/LLM, zelfbewustzijn, trader & potjes, KB v2, Skype/Fronts, sessie 57 XP-motor, sessie 55 IQ-sprong, brein v5-status)
staan in `ROADMAP_HISTORY.md` § "Verplaatst 20-10-2026". De **open punten** daaruit staan nu in `ROADMAP_BACKLOG.md`
§ "Open punten uit sessies 52–58".

## 🌷 Moreel Kompas — Kernvisie (blijft altijd bovenaan)

Spark is een persoonlijke AI-metgezel die Willem ooit als **erfenis** doorgeeft aan zijn dochter Lotus. Dat betekent:

1. **Rust boven snelheid** — snappy UX telt, maar nooit ten koste van voorspelbaarheid of dataveiligheid.
2. **Privacy-by-design** — geen chat-tekst loggen, geen user-namen in `/app/memory/*.md` voor anderen dan Willem, alleen patroon-tellers. Per-user opt-out beschikbaar.
3. **Autonomie-scheiding** — elke module heeft twee zones:
   - 🤖 **Spark autonoom**: voorstel doen, geen mutatie (draft-status).
   - 👤 **Willem beslist**: expliciete Accept vóór mutatie plaatsvindt.
4. **Zwart-wit boven grijs** — strakke regels die 90% dekken + expliciete uitzonderingen zijn beter dan flexibele regels die 100% dekken maar niet meer te ontwarren zijn.
5. **Container-isolatie is default** — elke user/shop/bot heeft eigen container met `_meta.json`. Nooit globale bestanden voor user-data. Delete = delete-directory.
6. **Gastheer-toon** — bij twijfel/onzekerheid: warm ontvangen, niet docerend. Erkenning voor prestatie. "We doen het samen."
7. **NO MONGODB** — alle data via `load_json`/`save_json` uit `modules.core.storage`. Backups zijn zip-exports.

---

## 🔭 Observability — Verplicht voor nieuwe modules (v5_spark_logger_001)

Vanaf 2026-05-23 geldt: **elke nieuwe of gewijzigde Python-functie die user-acties of system-events afhandelt MOET gedecoreerd zijn met `@traced`**.

```python
from modules.core.spark_logger import traced, log_event

@traced(intent="kort, in het Nederlands wat deze functie probeert te doen")
async def my_handler(...):
    ...

# Voor handmatige events (geen functie-grens):
log_event("module_naam", "event_naam", intent="...", detail={"key": "value"})
```

**Waarom**: pre + post logs (met duration_ms + result-summary) maken bugs als de B3 community-crash direct zichtbaar — je ziet de "post" niet en weet meteen waar het kapot ging.

**Wat krijg je gratis**:
- `/data/system/logs/YYYY/MM/DD/{module}.jsonl` (JSON Lines, 1 record per regel)
- Browser in **Beheer → Instellingen → Archief → Logs**
- 28-dagen retentie (auto-purge bij startup)
- Filter per phase: `pre` / `post` / `error` / `event`

**Reeds gedecoreerde routes** (referentie):
- `bots/routes.py::send_community_message` (community/send)
- `chat/routes.py::process_message` (Spark chat)

**Te decoreren** (volgende sessies, P1):
- `auth/routes.py::login` + `logout`
- `trade/routes.py::bot_start`, `bot_stop`, `quick_buy_potje`
- `shop/gift.py::*` (ROAR gift escrow lifecycle)
- `dnd/routes.py::observe` (achievement triggers)
- Knowledge Base mutations

---

## 🧠 Architectuur principes (don't forget)

1. **NO MONGODB**: alle data via `load_json`/`save_json` uit `modules.core.storage`
2. **DSP-tags**: 2-JSON sync issues moeten gedocumenteerd in `ARCHITECTURE.md` (DSP-001 t/m DSP-006 actief)
3. **Nederlands**: alle UI-tekst en log-intents in het Nederlands
4. **data-testid**: elk interactief element heeft een uniek testid (kebab-case)
5. **Piramide-lagen** (zie MISSION.md): Core/Skelet/Geheugen/Logs — wijs nieuw werk de juiste laag toe
6. **Hooks-laag voor placeholders**: `modules/kb_v2/hooks.py` toont pattern. Bij toekomstige verbindings-noden: maak hooks-bestand met TODO-blocks i.p.v. losse `# TODO` in productiecode
7. **Identity-3-lagen wet**: ALTIJD `user_id`, NOOIT op naam matchen (CR-001/002/003)

## 🔗 Hook-bestanden (PLACEHOLDERS) — entry-points voor toekomstige features

| Hook-file | Status | Doel |
|---|---|---|
| `modules/kb_v2/hooks.py` | ✅ Created sessie 5 + uitgebreid sessie 8 | KB v2 → Vocab/Commands/Graph/D&D/Dialogen + card-factory commands |
| `modules/cards/service.py::_fire_card_hooks` | ✅ Created sessie 8 | DnD/Event/Bark hook-chain bij draft→active overgang |

Nieuwe hooks volgens dit pattern toevoegen voor:
- `modules/trade/hooks.py` — closing-flow + replay + auto-snapshot triggers
- `modules/dnd/hooks.py` — lore-card sync, perk-trigger, aura-gates (kan deels via cards/service.py)
- `modules/spark/hooks.py` — Spark's hands (intent_matcher generic router)

## 🃏 Card Factory pattern (v5_card_factory_001)

3 generieke kaart-types naast KB v2 kennis-kaarten:

| Type | Doel | Hook bij active | Extra schema |
|---|---|---|---|
| `dnd` | Game-kaarten (lore/quest/item) | `dnd_lore_registered` | `dnd: {verteller, scene, rewards}` |
| `event` | Community-events | Community-bark via Boekhouder | `event: {datum, locatie, deelnemers}` |
| `bark` | Bot-trigger templates | `bark_template_registered` | `bark: {bot, trigger_text, schedule}` |

**Common schema**: id, type, titel, vraag, antwoord, media (image+audio), tags, status, footnote.
**Storage**: `/data/cards/{type}/<id>.json` + index per type. Media via system_archive met
`tag=card_<type>` + `linked_card_id`. Cascade-delete bij card-verwijdering.

**Chat commands**: "maak een d&d kaart [titel]" / "maak een event kaart [titel]" / "maak een bark kaart [titel]".

## 📦 Media-storage strategie (v5_kbv2_media_002)

**Centrale store**: alle voice/image uploads van kennis-kaarten gaan door
`/api/system-archive` heen, met:
- `category`: `foto` / `geluiden` / `filmpjes`
- `tags`: `['kbv2', 'kbv2_card_<id>']`
- `linked_card_id`: backreference naar kaart-id
- `source`: `kbv2_media_upload`

UI in **Beheer → Instellingen → Archief → Foto/Geluiden** heeft drie bron-filters:
- **Alles** — geen filter
- **🧠 Kennis-kaart** — alleen kbv2-gelinkte items
- **📎 Los** — alleen items zonder kbv2-tag

Voordelen:
- 1 centrale media-tabel, geen duplicate-storage
- Sub-tab pattern uitbreidbaar (later bv. "Dagboek-foto's", "Trade-screenshots")
- Verwijderen van een kaart kan zo ook gekoppelde media opruimen via `linked_card_id`-scan

## 📊 Dashboard-widgets per gradatie

- **Gradatie 1** (super-admin): alle widgets incl. Triggers, KB Lades, Shadow Learning, Storage Cache
- **Gradatie 2** (admin): KB Lades + Triggers + Users + Health
- **Gradatie 3-7**: Kennisbank-overzicht + persoonlijke widgets (Mijn Opslag, Agenda, Spark-status)