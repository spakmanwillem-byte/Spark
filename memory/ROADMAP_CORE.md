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

## ✅ AFGEROND 19-10-2026 (100-credit-batch, getest als Emergent-account)
- **Relatie-/personalia-extractie in diep-modus** (`v14_compose_extraction_001`, `response_composer.py` r.184) —
  `compose()` roept nu dezelfde `relation_extraction_service` + `personalia_extraction_service` aan als
  `/api/chat/message`; `new_relations`/`personalia_saved` gaan mee in de response zodat "ik noteer" alleen klinkt
  als er echt iets staat. Getest: "X is mijn broer" → `persons/<user>.json` + `_relationships.json` gevuld.
  Testrelaties daarna verwijderd. **Maaike moet haar zinnen één keer opnieuw zeggen** — de oude zijn nooit opgeslagen.
- **Roadkill Merch-tab uit Beheer** (`SystemArchive.js` r.323) — bestaat alleen nog in Workspace → Archief → Foto → Winkel.
- **TTSS / GTSS** (`v14_ttss_001`) — zie blok hieronder.
- **KB-filter 🎙️ niet ingesproken** (`kbv2-voice-filter`, per lade met teller bv. Voelen 554/566). Niet in Inbox-tab.
- Testartefacten opgeruimd: `test-dupe-guard-15599c75` (weten), inbox-gapfills `testman/testbroer/emergentsen`.
  → **alle 7353 lade-kaarten hebben ≥5 tags.**

### 🎙️ TTSS / GTSS — hoe het werkt en wat de grenzen zijn
- Chat-commando's: `ttss aan|uit`, `gtss aan|uit` (`action_intents_service._RX_TTSS`, acties `enable_ttss` enz.).
  Cyaan modusbalk `ttss-mode-bar` boven de chat. Gewone `tts aan` blijft OpenAI-stem.
- Backend `GET /api/kb/v2/voice/map` → `{woorden: begrip→voice_url, geluiden: begrip→extra_audio-url}`;
  `GET /api/kb/v2/voice/missing?lade=&search=` → kaarten zonder inspraak + `per_lade`-tellers.
  **Alleen `media.voice_url` telt als inspraak**; `media.extra_audio` (geüploade geluiden) is het GTSS-kanaal.
- Frontend `speakOwnVoice()` (GesprekkenPage r.685): loopt per woord (+ 2-woord-begrippen) door het antwoord,
  speelt de opname af als die er is, **skipt stil** als die ontbreekt. Geen terugval op OpenAI-TTS in ttss-stand.
- **Grens**: nu 50 ingesproken woorden + 9 geluiden op 7353 kaarten → antwoorden klinken hakkelig/leeg. Dat is
  by design: de filter laat zien wat nog ontbreekt. GTSS is een **placeholder**: speelt kaart-geluid als het
  begrip in het antwoord staat; er is nog geen bewuste "bloeper → bloepergeluid"-koppeling.
- **Tab "In te spreken"** (`v14_inspreek_tab_001`, 19-10): eigen tab in de lade-rij, alle lades + lade-chips met tellers,
  kaart verdwijnt na inspreken en de volgende kaart wordt automatisch geopend. Alleen `voice_kind='spraak'` telt;
  een als GELUID gemarkeerde opname telt niet als inspraak (gaat naar het gtss-kanaal). Merch: ook dode code weg.
- **Emotie-veld (onderzoek, niet bouwen; Willem: "goed als is")**: top-level `emotie` bestaat al op 3631 kaarten
  (3553 neutraal) via txt-importer, maar `emotion_service` leest alleen tags (1336 geleerd, 1147 neutraal). Dode data.
  Willems gedachte: emotie als eigen graph-laag naast de verbanden-graph, los van de kaart → minder ruis. Parkeren.
- **ttss-output als sample opslaan (onderzoek)**: zinloos voor eigen opnames (zelfde audio). Wél mogelijk: per kaart
  één keer OpenAI-TTS genereren in apart veld `media.tts_url` (nooit `voice_url`) als bootstrap-stem. Risico: ~7353
  calls, ~200 MB, twee stemmen door elkaar. Niet gebouwd; wacht op akkoord.
- **Onderzoek 19-10 (geen bouw)**: emotie-graph + hybride command-systeem → `/app/memory/ONDERZOEK_EMOTIE_GRAPH_COMMANDS.md`
  en `/app/memory/COMMANDS_OVERZICHT_19-10.md`. Kern: `emotie`-tag = ~25 % ruis in kennis-graph; emotie-veld bestaat al
  (3631 kaarten) maar wordt niet gelezen; registry 81 = 58 live / 23 placeholder; task_agent.resolve/execute zijn leeg.
  Punt 3 (tab "Nog geen emotie", 120 %) wacht op akkoord punt 1.
- **✅ 19-10 — Registry opgeruimd + task_agent-basis** (`v14_task_agent_basis_001`):
  `command_registry.json`: 58 live (`status: live`) · 23 verplaatst naar `placeholders` (route bestaat niet; wens
  bewaard, 8 ervan werken via spark_capabilities laag B). Backup `.bak_placeholders_*`. Stats hersteld.
  `task_agent.resolve(tags, methods)` → beste live command via matcher; `resolve_text(zin)` voegt losse woorden,
  stam (-s/-en) en **werkwoord-concepten** toe: verwijderen = verwijder/delete/wis/ruim op/gooi weg → alleen DELETE-
  commands; aanmaken → POST; zonder actie-werkwoord → alleen GET. Getest: "verwijder die bug" / "ruim die notitie op"
  / "delete die taak" → juiste delete-command. `execute(cmd_id, params, user_id)` → gradatie-check, required-params,
  `{user_id}` auto in pad, interne ASGI-dispatch (geen netwerk), audit-log `task_agent.jsonl`; placeholders → geweigerd.
  **AANNAME te bevestigen door Willem**: registry-schaal `gradatie_min` 1=iedereen…5=beheer is omgekeerd aan de
  user-schaal (1=beheerder); omrekening `user_gradatie <= 6 - gradatie_min`, `admin_only` eist gradatie 1.
  **Nog niet**: task_agent hangt nog NIET in de chat-flow (hybride stap 3 na action_intents + capabilities) en de
  concept-JSON is nog hard-coded (`_VERB_CONCEPTS`) — volgende sessie live-editable maken zoals intent_patterns.
- **✅ 19-10 — Emotie-veld + tab "Nog geen emotie"** (`v14_emotie_veld_001`, Willems keuzes: 5 basis-emoties,
  sub-emoties later leerbaar; `neutraal` is een echte keuze, geen default; schone reset van de detector):
  kaartvelden `emotie` (blij/boos/bang/bedroefd/neutraal) + `emotie_bevestigd` + `emotie_bron` + `emotie_bevestigd_op`,
  gezet via `/api/kb/v2/edit` updates `{emotie}` (`service._apply_emotie`). Routes `GET /api/kb/v2/emotie/missing|stats`
  (`emotion_routes.py`). Tab in de Kennisbank met lade-chips/tellers; kaart verdwijnt na bevestigen, volgende opent.
  EmotieSection op elke kaart; niet-bevestigde suggestie (uit emotie-tag of importer-veld) licht gestippeld op.
  **Detector**: `emotion_service._load_learned_triggers` leest alleen nog bevestigde velden (neutraal = geen trigger);
  tags en v1 `knowledge_base.json` tellen niet meer → geleerde woorden 1336 → 0 tot Willem bevestigt (statische
  triggers blijven anker). Getest: bevestig `akkers`=blij → "ik ben zo blij met de akkers" bron `both`.
  **Badge**: 100 % = laag1-4 + 5W + tags + foto (7 velden); +10 % ingesproken (alleen voice_kind spraak) · +10 % emotie
  bevestigd → max **120 %**. (Stem telt niet meer mee in de 100 %-basis.)
  **✅ Tags-opruimen bij bevestigen** (`v14_emotie_tags_001`, Willems keuze "alleen tegensprekende weg"): in
  `_apply_emotie` gaan `emotie-X`-tags met X ≠ keuze weg, en op emotie-kaarten (tag `emotie`) ook losse basis-emotie-
  tags ≠ keuze; `emotie` zelf en een tag gelijk aan de keuze blijven; nooit onder MIN_TAGS_FOR_LADE (dan
  `emotie_tags_conflict` + waarschuwing). Verwijderde tags staan in `emotie_tags_verwijderd` (toast in UI).
  Getest: gloed (emotie, blij, neutraal, …) bevestigd als boos → blij + neutraal weg, 13 tags over; teruggedraaid.
  Stand: 5 kaarten met expliciete pipeline-tags, 1330 met losse emotie+basis; worden pas geraakt als Willem bevestigt. Kennis-graph-ontruising (`emotie` uit tag-
  overlap) + emotie-edges (escaleert_naar/verwant/tegenpool) = volgende stap "emotie-graph".
- **✅ 19/20-10 — Contacten-klapper + Winkel: Producten/Bestellingen (fase 1+2)** (`v14_contacten_klapper_001`,
  `v14_shop_producten_tab_001`; getest als Emergent met tijdelijke testwinkel, daarna opgeruimd):
  • Mijn Profiel → **Contacten**: twee lagen privé/zakelijk, rollen (familie/vriend · leverancier/klant/partner), zoek,
    CRUD. Eén klapper, niets dubbel: bel_contacts (bron `bel`) en clienten (bron `clienten`) worden erin getoond én
    zijn er bewerk-/verwijderbaar — schrijft terug naar hun eigen bestand (Willem 20-10: "kon mijn contacten niet
    aanpassen"). Eigen entries: `data/users/<id>/contacten.json`. Routes `/api/contacten/{user_id}` GET/POST/PUT/DELETE.
  • Rollen zakelijk (Willem 20-10): **klant** = koopt merch · **client** = vraagt zorg/handelingen (cliëntdossiers
    uit `clienten` krijgen rol client) · leverancier · partner · overig.
  • Zakelijke kaders (Willem 20-10, stonden in notities): KvK, BTW-nummer, IBAN, BIC, jouw klant-/debiteurnummer bij hen.
    Rol **dienstverlener** erbij (advocaat/accountant). Promotex/Full of Joy/Boutadvocaten gemigreerd; spaties getrimd.
  • Velden (Willem 20-10 n.a.v. Promotex): telefoon + telefoon2, fax (zakelijk), e-mail + e-mail2, website (zakelijk).
  • Profiel-kaart **Zakelijk**: `zakelijke_email`, `bedrijfsnaam`, `kvk`, `btw_nummer` (ProfileExtended).
    Regel Willem: e-mail pas gebruiken als ingevuld. Spark's eigen afzender later: spark-your-life@hotmail.com.
  • Winkel-tab → subtabs **Winkel | Producten | Bestellingen**. Product heeft nu `product_code`, `voorraad`,
    `leverancier_contact_id` (keuze uit zakelijke contacten) of `leverancier_naam` (vrij). Leeg = eigenaar levert zelf.
    Nieuw product in Producten-tab verschijnt ook in Winkel (zelfde bron). `GET /api/shop/shops/{shop_id}/orders`.
  • Betaling blijft zoals het was: koper betaalt uit Spark-wallet (Willem: "daar heb ik al wat voor").
  **Fase 3 — nog te bouwen (roadmap)**: bij bestelling zonder voorraad → leveranciersmail (aantal + productcode,
  standaardtekst) + kopie naar zakelijke e-mail · factuur (PDF, lokaal gemaakt — geen externe dienst) naar koper-mail
  als ingevuld + Workspace-Archief · pakbon naar winkeleigenaar-archief · bestelbon bij bestanden.
  Mail-verzending vereist een provider/SMTP (hotmail-afzender = Outlook SMTP met app-wachtwoord, via Connections);
  tot die tijd **concept-modus**: mail + bon als bestand in Archief, niets verstuurd.
  **Later**: Bestellingen-tab hybride link naar boekhouder + voorraad bijhouden · contacten matchen op e-mail/tel/naam
  aan users → bekende users zichtbaar in privé-gesprekken (Willem 20-10).
  Bekende beperking (bestaand): `create_order` leest producten alleen uit Roadkill's products.json → bestellen bij
  andere shops werkt nog niet; hoort bij fase 3.
- Later: `stts` (eerst eigen opnames matchen, dan Whisper) · vervoegingen/stam-matching (nu exacte begrip-match) ·
  eigen stemmodel uit de dataset (`voice_transcript` is al het label).

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

## 🧹 CLUSTER — Sessie 58 (15 feb 2026) — Subject-Agent-laag + Registry-fundering (Principe #8)

**Kern**: Principe #8 (Subject-Agent Pattern) wordt geïmplementeerd. Elke losse
string / capability krijgt een agent-wrapper en een KB-kaart zodat Spark
introspectief kan uitleggen wat hij kan.

### ✅ AF (Sessie 58 — dag 1)

- **`/app/backend/modules/agents/`** aangemaakt met 4 dun-wrapper skeletons:
  `task_agent`, `admin_command_agent`, `personal_agent`, `spark_pulse_agent`.
  Signatures + docstrings + TODO's; geen volledige logica.
- **12 draft KB-kaarten** ingevuld en gecureerd naar juiste lade (Weten/Doen):
  4 agents + 8 architectuur-begrippen (`principe-8`, `spark-architectuur`,
  `command_registry`, `intent-uitvoering`, `compose`, `privacy_matrix`,
  `self_awareness`, `observability`). Elk met laag1-4, ws5, tags, topic.
- **Apostrof-ghost-preventie** — `tag_sanitizer.sanitize_tag` normaliseert nu
  unicode-apostrofen (’‘´`‛ʼ → '). `orphan-tag-scanner._canonicalize` idem.
  Data-fix uitgevoerd (8 tags + 1 begrip `Programma's`). 6 regressietests
  toegevoegd, 18/18 pass.
- **Apostrof-normalize als admin-command**: `POST /api/kb/v2/admin/normalize-apostrophes`
  + registry-entry `cap_kb_normalize_apostrophes` + toegevoegd aan
  `admin_command_agent._ADMIN_CMD_WHITELIST` — eerste échte lid van de agent.
- **Registry-batch-1**: 38 nieuwe entries toegevoegd voor agenda (9), notes (7),
  bugs (5), help (3), triggers (8), KB v2 admin (5), commands-list (1).
  Registry: **14 → 76 entries**.
- **`GET /api/commands/list`** nieuwe route (module `system/commands_list_routes.py`)
  met filters `module`, `admin_only`, `gradatie_max`, `q`. Dit is Spark's
  "welke commando's ken je?"-endpoint via `task_agent.list_commands()`.
- **Auto-scanner** — `scripts/scan_routes_for_registry.py` scant alle 669
  `@router`-decorators in `/app/backend/modules/` en genereert concept-entries
  voor missende routes. Output: `/tmp/registry_scan_YYYYMMDD_HHMMSS.json`
  met 617 concept-entries klaar voor review.
- **Admin-whitelist uitbreiding**: 17 cmd_id's in `_ADMIN_CMD_WHITELIST`
  (KB-onderhoud, agenda-archive-all, bug-moderation, triggers-editing).
- **Foto's-kaart upgrade** (`kbv2-c0421b96`) — Willem's uitgebreide versie
  overschreven op de bestaande kaart (7 use-cases, betere ws5). Lege
  ghost-duplicaat `kbv2-63c3d542` (unicode-apostrof) opgeruimd.
- **Ervaring-uit-brainstorm — `kb_hit_log_agent` skelet + KB-kaart**:
  `modules/agents/kb_hit_log_agent.py` met `record()`/`retrieve()`/`stats_snapshot()`,
  datafile-formaat vastgelegd (`data/chat_analytics/kb_hits.jsonl`, JSON-Lines,
  gestandaardiseerde `match_source`-labels). KB-kaart `kbv2-dc6c015e`
  volledig gevuld in Weten. Smoke-test: 2 rijen geschreven + teruggelezen.
  Hooks in `response_composer` / `snap_service` bewust NIET geplaatst
  (skelet-fase — format vaststellen eerst).
- **KB-test-kaart `orphan-tag scan`** (`kbv2-18829e2b`) volledig gevuld in
  Weten met 10 tags — bewijs dat Principe #8 werkt: cmd_id in registry
  + concept-naam in KB, twee kanalen, één begrip.
- **Small tweak**: topic-overview sample-limiet van 5 → 10 begrippen
  (`smart_intents_service.py:683`). KB is gegroeid naar 7000+ kaarten;
  5 sample-hits was te karig geworden.

### 🎯 OPEN (Sessie 58 vervolg — registry-uitbreiding)

**Doel**: 617 → 0 missende entries via module-per-module aanvulling.

- **P1 — Registry batch-2 (KB v2)** — 54 kb_v2-routes met echte intent_tags.
  Dit is de grootste single-module wisser. Zonder deze kan Spark's KB-chat
  niet volledig introspectief zijn (bijv. "hoe zoek jij kaarten?" → moet
  naar `kbv2_search` kunnen wijzen).
- **P1 — Registry batch-3 (chat)** — 30 chat-routes. Cruciaal voor Sparks
  zelfuitleg over eigen chat-flow (intent-matching, compose, snap).
- **P1 — Registry batch-4 (spark + spark_planner + spark_kasboek)** — 32 routes
  over Sparks eigen leven (identity, planner, saldo).
- **P1 — Trader-intents-registratie** — `modules/trade/trader_intents.py`
  bevat al 8+ chat-intents (`trader_start`, `trader_stop`, `trader_status`,
  `trader_explain`, `trader_recent_trades`, etc.) die vóór de LLM-router
  worden gematcht. Werkt, maar niet in registry — Spark kan er niet naar
  wijzen op "wat kan je met de trader?". Aparte batch (~8 entries).
- **P2 — Registry batch-5 (auth + wallet + profile)** — 79 routes. Belangrijk
  maar minder Spark-introspectief.
- **P2 — Registry batch-6 (trade)** — 95 routes. Grootste module; kan gefaseerd
  per bot/reconcile/monitor.
- **P2 — Registry batch-7 (boekhouder)** — 47 routes. Multi-book.
- **P3 — Restant** — accounting, achievements, admin, backup, files, graph,
  shop, settings, winkelstraat, etc. — nog ~180 routes.

### 🧠 Agent-skelet fill-in (Principe #8 vervolgstappen)

- **P1 — `task_agent.resolve()`** — tag-overlap-score + tie-break op laagste
  gradatie_min. Return `{cmd, score, matched_tags}`. Test: geef `["tellen","gebruikers"]`
  → moet `cap_tellen_gebruikers` (score 2) terugvinden.
- **P1 — `task_agent.execute()`** — gradatie-check + params-validatie + dispatch
  via `entry.source` + audit-log-entry naar `data/system/audit_log.json`.
- **P1 — `admin_command_agent.execute_as_admin()`** — whitelist-check +
  auth-guard hergebruiken van `modules.auth.deps.require_admin_capable` +
  gestructureerde audit `event_type=admin_action`.
- **P1 — `kb_hit_log`-hooks plaatsen** in `chat/response_composer.py`,
  `chat/snap_service.py` en `chat/smart_intents_service.py` op de plekken
  waar KB-kaarten worden gebruikt (topic-overview, snap-lookup,
  sentence-match, compose-embed). Één regel per hook — best-effort.
  Zodra ledger vult: dead-weight-analyse mogelijk.
- **P2 — `personal_agent.snapshot()`** — depth minimal/standard/deep uitwerken
  met 30s TTL-cache; consumer wordt `compose_routes`.
- **P2 — `spark_pulse_agent.pulse()`** — KB + trade + LLM-router + chat
  metrics-blokken, health_score berekening, narrator-templates. Leest ook
  `kb_hit_log.stats_snapshot()` zodra hooks live zijn.
- **P2 — `ervaring_agent` skelet** — nieuwe agent boven `kb_hit_log`.
  Distilleert conclusies uit reeksen van gesprekken; LLM-onafhankelijk zodat
  Spark bij LLM-uitval nog steeds "geleerde ervaring" heeft. Structuur:
  `modules/agents/ervaring_agent.py` + datafiles
  `data/ervaringen/ledger.json` / `disputed.json` / `verified.json`.
  Bronnen: `chat_conclusion` (pattern-match afsluiters), `interaction_log`
  (bijv. openingszin-tracking), `external_check` (Wikipedia/Google, P3).
  Nog niet bouwen — pas als `kb_hit_log` een paar honderd rijen heeft.

### 📌 Uitgebreide stats (kleine wins, hoge waarde)

- **P1 — `GET /api/kb/v2/stats/extended`** — huidige `/stats` uitbreiden met
  `topics_count`, `topics_top20`, `avg_verbanden_per_kaart`, `median_verbanden`,
  `cards_zonder_verbanden`. Directe waarde: Spark kan "hoeveel onderwerpen
  ken je?" en "gemiddeld verbanden per woord?" beantwoorden.
- **P2 — `POST /api/kb/v2/admin/topics/recompute`** — per kaart of bulk
  het `topic`-veld herberekenen op basis van tags. Nuttig bij drift na
  bulk-import of merges.

### 🧹 Kleine opruim-items (opgetekend maar niet gedaan)

- **`kb-hit-log` seed-script niet uitgevoerd** — `scripts/seed_registry_concepts_to_inbox.py`
  bestaat maar niet gedraaid. Zou 617 skeletons in KB-inbox zetten met
  cmd_id als begrip. Beter: script aanpassen zodat het lees­bare begrip
  genereert (bv `cap_agenda_events_list` → "agenda-events tonen") vóór
  massa-seed.
- **`Programma's`-kaart** heeft nu rechte apostrof; index-alias unicode-versie
  verwijderd. Backups: `*.bak_apostrof_normalize_*` + `*.bak_orphan_scan_test_*`.

### 🎨 Backup-splitsing + Response-tijd + Thinking-indicator (dag 2)

**Melding (Willem)**: "alleen wijzigingen wordt te groot" + "wacht-icoon tijdens
input" + "response-tijd loggen leuk voor later onderzoek".

- **✅ Backup-splitsing 3 slices** (`modules/backup/routes.py` + UI):
  - `/api/backup/download/changes/chat` — chat, dagboek, dialogen, chat_analytics
  - `/api/backup/download/changes/trader` — trade, financial, bitvavo
  - `/api/backup/download/changes/rest` — al het overige
  - `/api/backup/download/changes/sizes` — preview per slice
  - **Bonus fix**: `EXCLUDE_REL_PREFIXES` sluit oude `_backup_*`/`_backups/`/`_archive/`
    /`_deleted_*` dirs uit → **1185 MB → 528 MB** (-657 MB backup-in-backup).
  - Frontend `IntegratiesPage.js`: 3 nieuwe DownloadCards (emerald/cyan/teal)
    met live size-preview per slice; KB-diff + Volledig in aparte rij.
- **✅ Response-tijd logging**:
  - `POST /api/chat/log-response-time` — schrijft naar
    `data/chat_analytics/response_times.jsonl` per turn (duration_ms, endpoint,
    user_id, ok, used_model, message_length).
  - Frontend meet met `performance.now()` rond beide fetch-paden
    (`/api/chat/message` én `/api/spark/compose`).
  - Verwacht consumer: latere analytics + `spark_pulse_agent.pulse()`.
- **✅ Thinking-indicator** in `ChatInput`:
  - Nieuwe `thinking`-prop; toont `Loader2` + "denkt…" label links + spinner
    in send-knop; input disabled; placeholder wisselt naar "Spark denkt na…";
    border wisselt naar amber-glow tijdens wachten.
  - `sparkThinking`-state in `GesprekkenPage` toggles rond fetch-calls,
    ook bij compose-deep-mode.

### 📌 OPEN (voor volgende sessie — image-upload-naming + dashboard-kleurschema + chat-persistence)

- **P2 — Image-upload → begrip mapping**:
  - Bij upload van een afbeelding op een KB-kaart wordt de bestandsnaam
    (bijv. `appel.png`) automatisch het begrip. Zo krijgt elke afbeelding
    meteen een correct onderwerp en kan Spark later zeggen "wil je een appel
    zien?".
  - Bij een 2e afbeelding op hetzelfde begrip → automatisch nummeren
    (`appel-2.png` etc.).
  - Nieuw KB-kaart-concept: "**wacht-icoon**" (Willem maakt zelf met
    512x512 afbeelding) → deze wordt de eerste test-case voor het
    image-upload-naming-patroon.
  - Nadenken: welke module handelt image-uploads af (`kb_v2/media_routes.py`?),
    hoe passen we filename → begrip toe zonder bestaande kaarten om te gooien,
    en waar valt de "wacht-icoon" onder (weten? doen?).

- **P2 — Dashboard-kaders kleurschema**:
  - Icoon-accent van Agenda/Notities/Gesprekken-cards uit
    profiel → instellingen → kleurbeheer trekken ipv hardcoded
    (`#f97316` / `#22c55e` / `#06b6d4`). Waarschijnlijk via de bestaande
    CSS-variabelen `--glow-base` / `--glow-accent` (die de chat-bubbles
    ook gebruiken sinds v13_bubble_glow_persoonlijk_001).
  - Nette fallback: als user geen kleuren gekozen heeft → huidige defaults.

- **P1 — Bug: Spark stopt bij tab-wissel**:
  - Symptoom (Willem): wisselen van Gesprekken naar andere pagina tijdens
    het wachten → Spark's antwoord komt niet meer aan.
  - Vermoedelijke oorzaak: `GesprekkenPage` unmount, `setSparkMessages`
    krijgt geen effect meer (React silent no-op op unmounted component).
    Fetch loopt in JS door maar het resultaat verdwijnt in het luchtruim.
  - Voorgestelde fix: sla per pending-fetch een record op in
    `sessionStorage` (turn_id + text), en in de `.then()` óók het resultaat
    naar `sessionStorage`. Bij `GesprekkenPage` mount → lees unread-results
    + herstel `sparkThinking`-state. Bonus: response-tijd-logging blijft
    werken want die is in de fetch-thread, niet in de component.
  - Alternatief: lift `sparkMessages` naar een globale context/provider
    zodat unmounten niet meer uitmaakt. Groter refactor.

### 🧹 KB-opschoning + Spark Games lade (17 sep 2026)

**Trigger (Willem)**: orphan-tag scan maakte skelet-kaarten `voelenbegrip`, `rna`, `dnd`.
"dit is een fout woord … dit moet goed gezet worden" + "de game is inactief tot core
klaar … zonde om weg te doen … game zou eigen container moeten zitten" + "de naam wordt
universeel Spark World".

- **✅ `voelenbegrip`** — foute tag op 3 weten-kaarten (Vervanging, Wedergeboorte,
  Zoetwater) verwijderd; skelet `kbv2-eb46e512` weg. Oorsprong onvindbaar (zat al in
  oudste backup 23-08).
- **✅ `rna`** — géén fout: echte biologie-tag op Celkern/Genen/Virussen. Skelet
  `kbv2-977940f0` blijft in inbox; **Willem vult hem zelf in**.
- **✅ `dnd` root cause** — verweesd legacy-bestand `v2/inbox.json` (oude `kb-*` ids,
  door geen enkele module gelezen) met 10 grondstof-drafts. Verplaatst; leeg-gezet.
  Learning: de orphan-scan globt `V2/*.json` — élk los json-bestand in die map telt mee.
- **✅ Dubbele Utrecht** — kbv2-592d038c was een game-kopie van kbv2-6507fdfc (identieke
  lagen). Kopie is nu `Utrecht (Spark World)` in de games-lade met de fractie-link.
- **✅ 5e lade `games` ("Spark Games", 🎮, `#22c55e`)** — geregistreerd in:
  `kb_v2/service.py` (LADES + LADE_META), `kb_v2/routes.py` (alle lade-lijsten, move
  valid-set, dupes-files), `graph/sync_service.LADE_COLORS`, `chat/snap_service.V2_LADES`,
  `chat/spark_snuffel`, `kb_v2/llm_generate_routes`, `kb_v2/apostrophe_normalizer`,
  frontend `KennisbankV2Page.LADES` + count-fetch. Orphan-scan **slaat
  `knowledge_v2_games.json` over** (game-tags als `grondstof`/`fractie` zijn intern).
  Nog NIET in: `bulk_5w_fill_routes`, `curation_routes`, `text_importer`,
  `card_session_service`, `scan_service`, `spontaneous_w_service`, `wedervraag_service`
  (bewust: die werken op de 4 kennis-lades; games volgt als de game weer actief wordt).
- **✅ Spark World hub-kaart** — oude kaart "D&D" (kbv2-5ae16b66, generieke Dungeons &
  Dragons-uitleg) hernoemd + herschreven: sandbox-game, fictieve steden, fracties,
  bouwstenen, status geparkeerd. Verbanden → Base Line, Rugzak, Utrecht (SW), SPS.
- **✅ Base Line = basiswaarden-kaart** — oorsprong (0,0,0), AD-tijdrekening, licht/schaduw
  50/50, 4 elementen, fracties, startinventory 4 slots + 10 kg. Oude verhaal-lore weg
  (gearchiveerd in `data/dnd/lore_index.json`).
- **✅ Tags** — `d&d`/`dnd` → `spark world` overal. SPS-kaart kreeg tag `spark games`
  + verband naar Spark World.
- **✅ Index + graph herbouwd** (`POST /api/kb/v2/admin/rebuild-index`, `POST /api/graph/rebuild`):
  7280 index-entries (155 stale alias-keys van oude homoniem-namen weg), 7343 nodes.
- **Backups**: `*.bak_voelenbegrip_fix_*`, `*.bak_dnd_container_*`, `*.bak_spark_games_*`,
  `data/dnd/_kb_cards_moved_to_games_lade_*.json.bak`, `data/dnd/_legacy_kb_inbox_moved.json.bak`.
- **Getest**: curl stats/lade/find/orphan-dry-run + screenshot Spark Games-tab. Geen testing-agent.

- **📌 BESLUIT (Willem, 17-09-2026)** — de fictie-gate is de **standaard** voor alle huidige en
  toekomstige game-/fictie-lades: game-kennis staat gewoon in de KB (vindbaar, verbindbaar,
  later toepasbaar in de wereld) maar doet in antwoorden alleen mee bij game-context.
  Nieuwe game-kaarten altijd in lade Spark Games, nooit in Weten. Nieuwe fictie-lade →
  toevoegen aan `FICTIE_LADES`, verder niets.
- **✅ Text-importer tags (`v14_text_importer_tags_001`)** — Willem zag kaarten zonder tags na "Importeer txt".
  Root cause: `_TAGS_HDR_RX` eiste exact `Tags` alleen op een regel; `Tags:`, `**Tags**`, `Tags: a, b` (inline),
  `- lijstjes`, `#hashtags`, `·`-scheiding gaven stil 0 tags of één rommel-tag. Parser nu tolerant (10 varianten
  getest). Learning: een stil-lege parser-uitkomst moet een waarschuwing in de import-response geven (TODO).
- **✅ REGEL `MIN_TAGS_FOR_LADE = 5` (`v14_min_tags_001`, Willem)** — "zonder tags kan hij niet naar een lade en
  blijft in algemene inbox; minimaal 5 tags voor goedkeuring." Twee poorten: (1) `text_importer` zet nieuwe kaart
  met <5 tags in inbox (`_inbox_reason`, `_suggested_lade`, `needs:["tags"]`) + `warnings[]`/`to_inbox` in
  response, UI toont amber waarschuwingsblok + tag-aantal in dry-run; (2) `service.classify_card` weigert met
  `reason:"min_tags"` (toast in UI). `tags_gate()` is de ene bron. Bewerken van bestaande lade-kaarten blijft vrij.
- **✅ 44 tagloze kaarten getagd** via `scripts/fill_missing_tags_v14.py` (LLM 5-8 tags + sanitize; herbruikbaar:
  pakt alle kaarten met ≤1 tag). Graph herbouwd.
- **✅ Fictie-gate (`v14_fictie_gate_001`)** — Willem: "spark moet geen fantoom krijgen met
  realiteit". `kb_v2/service.py`: `FICTIE_LADES={"games"}`, `is_game_context(text)`,
  `filter_fictie()`. `semantic_lookup` filtert games-kaarten weg zonder game-context;
  `snap_service._get_index(query)` heeft nu een 'real'- en 'all'-index. Ambient
  services (spontaneous_w, wedervraag, scan, card_session) zien games NIET.
  Test: "wat is utrecht" → echte kaart; "wat is spark world" → hub-kaart.
- **✅ Bigram-snap (`v14_snap_bigram_001`)** — `multi_lookup` probeert eerst 2-woord-begrippen
  ('spark world', 'base line') vóór losse woorden. Was een gap voor álle meerwoordige kaarten.
- **🐛 ✅ Chat 500 gefixt** — `ResponseTimeLog`-blok (sessie 58) zat midden in `ChatMessage`,
  waardoor `user_id/channel/session_id/admin_mode` van de class los waren → `/api/chat/message` 500.
- **🐛 ✅ Chat-lookup dood sinds sessie 54 (23 aug)** — losse `return response` onder
  `if req.user_id:` in de agenda-CREATE-branch (commit 62a87352) liet élke gewone
  kennisvraag leeg terugkomen ("Hmm, daar moet ik even over nadenken") vóór snap bereikt werd.
  Learning: na een branch-herordening altijd een `trace` op `return`-regel draaien
  (`sys.settrace` op `process_message`) — 98 `return response` in één functie is te veel om op het oog te zien.

**📌 OPEN — Spark World (pas oppakken als Core klaar is, Willem)**
- P2 — Utrecht (Spark World) hernoemen naar een zelfbedachte stadsnaam (Willem: layout was NL-kaart,
  geen admin-front voor de game nog) + `steden.json` id `utrecht` mee.
- P2 — Spark Games-tab: filter per `game`-veld (Spark World / Steen Papier Schaar / …).
- P2 — Restore-/eco-container per game zodat game-data en KB-kaarten samen verhuizen.
- P2 — SPS-scorelijst koppelen als gevechtsmechaniek in Spark World.
- P2 — 8 grondstof-drafts in games-lade invullen (laag1 ontbreekt).
- P2 — `rna`-kaart invullen (Willem).
- P3 — 17 begrippen met leading/trailing spatie (`'ADA '`, `'Schors '`, …) strippen;
  index-keys zijn al gestript dus lookups werken, maar het is rommel.

### 🎨 Dashboard-kaders live (dag 2 vervolg)

**Melding (Willem)**: "in dat kader zou ik graag de eerst volgende komende
afspraak willen zien uit de agenda. en als ik er op klik na agenda ga.
kader als nodig aan kleur schema in beheer mijn profiel instellingen
kleurbeheer daar. zo zou je ook een notitie kader moeten hebben. met de
prio taak als eerst, en als die er niet is de laatst ingevoerde notitie.
gesprekken net zo: laatst gegeven output van spark, community aan/uit,
laatst binnengekomen privé als bericht → klik → naar privé."

- **✅ Agenda-kader** (`DashboardPage.js`): 
  - Fetcht `/api/agenda/events/{user_id}`, filter op `datum >= nu`, sorteert,
    toont eerste komende afspraak (titel + geformatteerd tijdstip).
  - Fallback-tekst "Geen aankomende afspraken" indien leeg.
  - Klik → `onNavigate('calendar', '/calendar')`.
- **✅ Notities-kader** (nieuw):
  - Fetcht `/api/notes/tasks?user_id=...` + `/api/notes/all?user_id=...`
    parallel. Prio-taak (`hoog`/`high`) wint; anders eerste taak; anders
    laatste notitie.
  - Rode streep bij hoge prio, groen anders. Kind-label ("taak · hoog"
    of "laatste notitie") onder de content.
  - Klik → `onNavigate('notes', '/notes')`.
- **✅ Gesprekken-kader** verrijkt:
  - Laatste Spark-turn bovenaan met Spark-avatar, klik → sessionStorage
    tab='spark', navigate naar chat.
  - Community-berichten alleen zichtbaar als `community_chat_enabled` aan
    staat in Profiel → Instellingen → Chat zichtbaarheid (zelfde bron als
    GesprekkenPage, geen aparte dashboard-toggle — dashboard is overzicht).
  - Laatste privé onderaan als notification-badge (cyan dot); klik zet
    `sessionStorage.spark_prive_contact_id` én tab='prive' zodat de
    chat-pagina meteen dat gesprek opent.
- **✅ Notities-kader correctie**: hoge-prio taak (`priority === 'hoog'`)
  wint; anders **laatste notitie** (bug-fix: eerder werd elke open taak
  vóór de notitie geplaatst — spec was strikter).
- **✅ Data-sortering fix**: sparkLog-conversations en notes worden nu
  expliciet gesorteerd op timestamp/datum descending in de frontend ipv
  te vertrouwen op backend-array-volgorde (voorkomt out-of-order-drift
  wanneer entries ooit niet chronologisch geappend werden).
- **✅ Vast formaat + scroll** — `Card`-component kreeg `fixedHeight` prop
  (`h-40` body + `overflow-y-auto`). Agenda/Notities/Gesprekken hebben
  nu identieke hoogte naast elkaar, scrollen intern bij lange inhoud.
- **Nog te doen** (P2, hierboven): kaart-icoon-accent uit user-kleurschema
  ipv hardcoded oranje/groen/cyaan.

---



**Trigger**: Willem: "iedere user met potje moet trader werken. en hij is stuk."
Bitvavo had €69.79 aan BTC (7 potjes waardig) terwijl registratie maar 1 open pot bij
Spark toonde. Ook: papertrail toonde Spark 8 tokens / 9 potjes na expired-gift Gerben.

### ✅ AF (Spoor A — root-fix backend)

- **v13_filled_coin_persist_001** — `open_pot()` + `open_cluster()` accepteren nu
  `filled_coin` kwarg → persist in `position.filled_coin` (pro-rata bij cluster).
  Was `null` → downstream drift op multi-user proxy. Nieuwe trades vullen dit
  automatisch vanaf Bitvavo's `filledAmount`.
- **v13_monitor_filled_pass_001** — `monitor.py` parseert `float(result["trade"]
  ["filled"] or 0)` uit `execute_real_trade` en geeft door aan
  `open_cluster`/`open_pot`-fallback.
- **v13_legacy_508_removal_001** — 3 hardcoded €5.08 fallbacks → €10 (huidige
  potje-min): `monitor.py:1428, 1709, 1711`. Docstring `potjes.py:5` bijgewerkt.
- **v13_ghost_cleanup_57** — Geiser pot-001 + Gerben pot-001 (beide BTC-EUR
  ghost) via `auto-fix-ghosts-all` naar `free`. Backfill Spark pot-006 met
  0.00102325 BTC uit Bitvavo.
- **v13_btc_redistribute_57** — 3 potjes verhuisd (Willem pot-001 BCH→BTC,
  Spark pot-007 BCH→BTC, Spark pot-002 ETH→BTC) + 0.00102325 BTC verdeeld over
  7 potjes (Willem 2, Spark 3, Geiser 1, Gerben 1). Bitvavo ↔ registratie diff = 0.
- **v13_willem_bot_start_57** — Willem's bot was `running=false` ondanks 3 potjes;
  gestart. Nu draaien alle 4 users met tokens.

### ✅ AF (Spoor B — UI consolidatie)

- **v13_trader_console_subtabs_001** — Analytics/Trade tab van 5 losse panels
  → 3 sub-tabs `trader-subtab-overzicht|sync|anker`:
  - **Overzicht**: RestwaardePortfolio + SparkTraderStatsPanel + Bot-cards + Audit-trail
  - **Sync & Reconcile**: 4 repair-buttons (`repair-auto-fix-ghosts-all`,
    `-close-sold-all`, `-rebalance-from-bitvavo`, `-refresh-anchors`) met
    confirm-dialogs + JSON-result panel + ReconcileSparkPanel
  - **Anker & Strategy**: AnkerPanel gap-up guard
- Testing_agent: 100% backend + 100% frontend, geen regressies.

### ✅ AF (Sessie 56 vervolg)

- **v13_gerben_retro_accept_56** — Gerben's expired gift (24u+ overschreden) op
  Willem's verzoek retro geaccepteerd: gift → `accepted`, Spark tokens 8→7,
  Gerben 0→1, pot-008+pot-009 bij Spark opgeruimd (0 trades), pot-001 bij
  Gerben aangemaakt (`minted_from: gift_retro_accept:8dc10eb9`). Papertrail
  `roar_balances.transactions` bevat `gift_accepted_retro` entry.
  Supply-integrity: Treasury (999.987) + Circulating (13) = 1.000.000 ✓
- **v13_kbv2_text_import_ws5_fix_57** — 5W-vraagwoorden (wie/wat/wanneer/waar/
  waarom/hoe) werden door text_importer als losse skip-tokens gefilterd →
  legitieme kaart-titels ("Waar", "Wat", "Hoe") gingen verloren. Nu detecteert
  regex `^\s*(wie|wat|...)\s*:` alleen 5W-VELDEN (met dubbele punt). Losse
  vraagwoorden als kaart-titel komen door. 4/4 tests + 2 regressie-tests groen.
- **v13_prod_merge_57** — Backup uit prod (deploy 2026-08-27 21:26) → preview:
  13 trade-files gemerged (`user_potjes`, `trade_history/user-*`, `trade/anker/*`,
  `roar/price_snapshots`, `trade/monitor_state`). Spark's pot-006 kreeg 1 extra
  BUY-trade uit prod, capitals van 10.04 → 10.03 door lopende trades.

### ✅ AF (Spoor C — Snap Agent + zelfbewustzijn, sessie 57 vervolg)

**Aanleiding**: Willem — "worden nieuwe woorden niet gelijk herkend door snap en
KB-kaart van dat woord gemaakt?" Bevestigd via snuffel: 3 losse write-flows
(trigger_learner, chat/routes, lite_card_factory) + `scan_spark_response` liep
alleen achter `_llm_analyze`-guard in trigger_learner → 90% van chat-turns geen
scan.

- **v13_snap_homoniem_fix_57** — `spreken:snap` (schnaps/borrel) had homoniem
  met `weten:snap` (kenniskaart). Rename `spreken:snap` → **"snap (drank)"**,
  aliassen `[snap, snaps]`. `weten:schnaps` uitgebreid met aliassen `[snap, snaps]`
  en tags `[snap, snaps, borrel, sterke drank]`. `knowledge_index.json` — `"snap"`
  wijst nu uniek naar de kenniskaart. `GET /api/kb/v2/homonyms` → 0 conflicten.

- **v13_snap_agent_57** — Nieuwe module `modules/chat/snap_agent.py`. Centraal
  ingangspunt voor onbekend-woord-detectie:
  - `scan_llm_output(spark_response, user_text, user_id, turn_id, max_new=3)`
  - `scan_user_input(text, user_id, turn_id, max_new=3)`
  - Rate-limit: 30 kaarten/user/uur (constante `_RATE_LIMIT_PER_HOUR`)
  - Footnote-verrijking bij elke aangemaakte kaart: `aangemaakt_door=snap_agent`,
    `origin`, `herkomst_turn_id`, `context_snippet`, `llm_count`
  - Thin wrapper: delegeert lookup aan `llm_output_scanner`, dedupe+schrijven aan
    `kb_v2.service.add_to_inbox` (deep-scan alle 4 lades, auto-repair index).

- **v13_trigger_learner_unconditional_57** — `trigger_learner.py:learn_from_interaction`
  aangepast: `_snap_llm_output()` wordt nu ALTIJD aangeroepen, niet alleen als
  `_llm_analyze` een trigger-voorstel oplevert. Extra call `_snap_llm_output`
  ook toegevoegd bij text_hash-dedupe-hit zodat óók herhaalde chat-turns bijdragen.
  Non-blocking wrapper `_snap_llm_output` isoleert scan-fouten van trigger-flow.

- **v13_self_awareness_seed_57** — `seed_self_awareness_cards()` genereert
  skeletons in inbox voor 8 core-modules: `snap_agent`, `llm_output_scanner`,
  `trigger_learner`, `lite_card_factory`, `snap_service`, `text_importer`,
  `tag_sanitizer`, `kb_v2 (module)`. Elke kaart kreeg **aanzet-inhoud** (laag1
  + laag2 + laag3 harde feiten + tags) door snap_agent, zodat GPT alleen nog
  laag4 + ws5 hoeft te polishen.

- **v13_fuzzy_matching_content_57** — 3 gerelateerde kaarten volledig gevuld:
  `Fuzzy-matching`, `rapidfuzz`, `fuzz`. Alle 3 in lade `weten`, met lagen 1-4
  + ws5 + tags. Willem's principe geborgd: **kaart bevat geen aannames over
  ongebouwde Spark-code** — pas na daadwerkelijke integratie mag Spark-specifieke
  rol worden toegevoegd (audit-log entry `content_neutralisatie` legt dit vast).

**Testresultaten (in-proc):**
- `scan_llm_output` op fictief antwoord: 3 kandidaten → 3 skeletons met snippet
  en turn_id in footnote. ✓
- `scan_user_input`: 3/3 skeletons aangemaakt. ✓
- Rate-limit: hit exact op 30 pogingen bij spam-test. ✓
- Dedupe: bestaande begrippen blijven bestaand (deep-scan werkt over 4 lades). ✓

### 📌 OPEN (backlog na sessie 57)

- **ROADMAP #6 P1: Fuzzy-fallback in `snap_service`** — rapidfuzz-integratie
  daadwerkelijk bouwen (threshold-advies ≥ 92 voor safe-match). Zodra gedaan:
  de 3 fuzzy-kaarten uitbreiden met Spark-specifieke rol via audit-log-versionering.
- **Snap-agent hooks voor self-repair** — `on_lookup_conflict` (homoniem-warn),
  `on_repeated_miss` (kaart-verrijking-suggestie). Willem's oorspronkelijke idee:
  "als kaart issue heeft en Spark er mee werkt, moet de kaart bijgesteld worden".
- **KB-lade `spreken:snap (drank)`** — jij vult zelf via GPT-flow aan indien gewenst;
  huidige data is behouden.
- **8 module-skeletons afronden** — laag4 + ws5 door GPT afmaken; classify naar `weten`.


### 📌 OPEN (dust + backlog Sessie 57)

- **ETH-dust orphan**: 0.000047 ETH (€0.10) niet aan een pot toegewezen na de
  BTC-redistribute (Spark's pot-002 is nu BTC). Actie: laten staan tot >€1 óf
  reconcile close-sold-all draaien.
- **CSPR orphan**: 159.24 CSPR (€0.40) heeft nooit een potje gehad. Aparte
  markt-toewijzing zou nodig zijn om dit als pot-storage te gebruiken.
- **Analytics testids**: top-level tab-knoppen missen `data-testid` → e2e-test
  tip uit iteration_57. Klein.
- **TradeAnalyticsTab splitsen**: functie is 700+ rgl binnen AnalyticsPage.js
  (totaal 2781 rgl). Kandidaat voor extract naar eigen bestand (ROADMAP-grens 700).
- **KB skeletons "wat" + "hoe"**: door de text_importer fix nu klaar in inbox
  (`kbv2-68f1221c` + `kbv2-476fac19`). Wachten op Willem's GPT-invulling om
  5W-cirkel compleet te maken.

### ⚠️ VOOR DEPLOY

- Spoor A + B zitten alleen in **preview**. Klik "Deploy" om prod-bots ook goed
  te laten werken.
- Sanity-check na deploy: `POST /api/trade/potjes/auto-fix-ghosts-all?dry_run=true`
  → `n_ok:1, n_ghost:0, n_hollow:0` verwacht.
- **Gerben retro-accept** staat alleen in preview (backup uit prod bevatte niet
  `roar_balances.json` en `gift_requests.json`) → gaat mee bij volgende deploy.

---


## 🧹 CLUSTER — Sessie 56b (25-26 feb 2026) — Multi-book fundament + chat-terugblik

**Focus**: Willem's zakelijke werkstroom fundering leggen. Agenda krijgt uren-registratie, chat kan terugkijken op eigen data, boekhouding-books krijgen elk hun eigen uren + clienten met book-type-aware placeholders (zorgclient vs klant).

### ✅ AFGEROND

**Dashboard opschonen**
- `ShadowObserverWidget` + `PerformanceWidget` verplaatst uit DashboardPage naar Widget Kladblok (`admin/sandbox/registry.js`)
- `BugsListWidget` (was tab in Notities) → Kladblok
- `DeployWidget` (was tab in Notities) → Kladblok
- `AdminNotesWidget` — nieuwe scratchpad in Kladblok voor scope=admin notes
- Notities-header: knop-volgorde +Nieuw → Bug melden, Bug-icoon weg

**Agenda uren-registratie** (`v13d_agenda_uren_registratie_001`)
- EventCreate/Update velden: `scope` (prive/zakelijk), `end_date`, `pauze_minuten`, `opdrachtgever`, `onderwerp`, `product_code`, auto `totaal_uren`
- Frontend: Privé/Zakelijk toggle, start+eind tijd, live 7.5u-netto badge, amber tint voor zakelijk
- Spark chat-parser `_extract_zakelijk_fields()` herkent "voor X van 9 tot 17 met uur pauze"
- 7/7 pytest groen (`test_agenda_scope_v13d.py`)

**Chat terugblik-hooks** (`v13d_agenda_terugblik_001`, `notities_terugblik_001`, `dagboek_terugblik_001`)
- Nieuwe capabilities in `capability_handler_service.py`:
  - `agenda_terugblik`: "wat heb ik gisteren gedaan", "hoeveel uur heb ik gewerkt deze week" (aggregatie per opdrachtgever)
  - `notities_terugblik`: "hoeveel notities in augustus", "wat is mijn laatste notitie" (excl. admin)
  - `dagboek_terugblik`: "wat schreef ik gisteren in mijn dagboek"
- Early-agenda-hooks in `routes.py` laten `gedaan/gewerkt/uren` door naar capability router
- 18/18 pytest groen + live geverifieerd op Willem's data

**Notes & Taken scope-veld** (`v13d_notes_scope_001`, `v13d_task_doel_001`)
- `scope` prive/zakelijk/admin op notes en tasks (zelfde termen als agenda — NIET "werk")
- Admin-notities uitgesloten van reguliere notitie-pagina (leven in Kladblok)
- Taken = doelen met tijdvenster: `begin_datum`, `eind_datum`, `budget_uren`, `opdrachtgever`, `onderwerp`
- Task-cards krijgen secondary-color badges voor periode/budget (`var(--app-secondary)`)
- Alles-view mixed notes+tasks

**Clienten-module** (`v13d_clienten_module_001`) — NIEUW MODULE
- `/api/clienten/*` backend + `ClientenPage.js` frontend
- Aparte module (niet persons — persons = familie/vrienden met D&D)
- Velden: naam, contactpersoon, email, tel, adres+postcode+plaats, KVK, BTW, uurtarief, notities, book_id, client_type
- **Dossier-entries** (kop+inhoud+bron) — handmatig of via chat/agenda
- **Spark-learnings** endpoint (`POST /clienten/learning/`) — Spark kan geleerde info wegschrijven per client

**Uren-registratie endpoint** (`v13d_uren_rapport_001`)
- `GET /api/agenda/uren-rapport/{user_id}?period=dag|week|maand|jaar&book_id=X`
- Aggregeert zakelijke agenda-events per opdrachtgever binnen periode
- Book-filter: matcht via opdrachtgever ↔ client.naam van dat book
- Live geverifieerd Augustus 2026: 9.5u totaal, Jeroen 8u + Roline 1.5u

**Boekhouding view fix** (`v13d_admin_view_eigen_default_001`)
- Admin ziet nu default alleen eigen books (was: alle books)
- Cross-user access via `?target_user_id=X` — voor toekomstige Beheer→Gebruikers pagina
- 3× ghost TEST_ books opgeruimd uit preview
- Pytest teardown fix (`test_winkelstraat_p1p4.py` — autouse fixture ruimt TEST_-prefixed books na test-run)

**Multi-book UI**: BookDetailBark 2 nieuwe sub-tabs (`v13d_book_uren_panel_001`, `v13d_book_clienten_panel_001`)
- 📊 **Uren** — periode-picker + samenvatting per opdrachtgever + CSV-export, gefilterd per book
- 💼 **Clienten** — lijst + create-form, book-type-aware label
- Sidebar cleanup: Urenstaat + Clienten uit MODULES-nav
- Book-type placeholders:
  - `entity` (Zorgboerderij) → **Zorgcliënt** met dossier + placeholder-velden (BSN, geboortedatum, zorgindicatie, huisarts, noodcontact)
  - `shop` (Roadkillshop) → **Klant** met factuur-info (factuur_adres, betalingstermijn_dagen)
  - `user_prive` → **Client** generiek

**App Kleurenschema** (`v13d_app_alert_color_001`)
- 4de kleur "Alert / Error" toegevoegd naast Primary/Secondary/Background
- `--alert-base` CSS var, live doorgetrokken naar Bug-melden knop
- Setting `app_alert_color` in `/api/settings/system`

**Theming**
- Agenda + Dagboek + Notities volledig op `var(--glow-base)` — geen hardcoded blauw/pink/amber accents meer
- Semantische kleuren behouden (mood-badges, done=green, delete=alert)

### 🔴 P0 nog open (uit sessie 55, ongewijzigd)
Alle 6 items van "Zelfscan-fundering" cluster staan nog open:
1. Privacy-guard bypass op /api/spark/compose
2. Metadata backfill script
3. Write-guard `_validate_footnote()`
4. Trace-capability "waar heb ik dit gezegd"
5. KB-vulling uit systeem-vakboeken (STARR + Methodiekengids + Begeleid Leren)
6. Fuzzy-snap in chat-flow

### 🟡 P1 uit sessie 56b (nieuw op backlog)
- **book_id op agenda events + notities + taken** → volle multi-book context
- **Actief book globale context** in header (verandert alle tabs mee)
- **Client-detail form** met tabbed zorg-velden vs factuur-velden
- **Factuur-generator**: urenstaat-CSV + client-adres + betalingstermijn → PDF
- **Documenten split** (Privé/Zakelijk) in Archief → Bestanden
- **Roadkill categorisering**: inkopen labelen (spark merch vs doorverkoop)
- **Spark auto-write client learnings**: bij naam-mention in chat de context oppikken en `POST /clienten/learning/{client_id}` doen

---

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

## 🧹 CLUSTER — Sessie 54 Opruimwerk (23 feb 2026)

**Doel**: Ruis weg, code strakker, glow-theming door hele app, D&D compleet uitfaseren tot het écht terugkomt.

### ✅ AFGEROND

**Privacy & Security**
- 🛡️ **Privacy Guard v13** (`modules/chat/privacy_guard.py`): strip familie/privé/financieel/gezondheid uit KB-cards + identity_facts + system_prompt voor gradatie ≥5. 13 pytest groen. Emmy-lek gedicht.
- 🔍 **User-lookup "weet jij wie X is"**: 2 nieuwe patronen + admin-bypass in `smart_intents_profile.py`. Was: Spark hallucineerde over Emmy.
- 🧯 **LLM-lek preventie** (`modules/kb_v2/tag_sanitizer.py`): centrale sanitizer voorkomt dat LLM-multi-line output als tag opgeslagen wordt. Ingehaakt op 3 punten (generate + snap + frontend).

**Trader Fixes**
- 💰 **ATOM-drift bug** (`modules/trade/monitor.py`): rest_bonus_eur greep alle overtollige coins mee (61.4 ATOM verkopen ipv 7.6). Fix: cap op 10% dust + skip proxy-users. 8 pytest groen.

**Data Cleanup**
- 🏷️ **KB-tag cleanup**: 60932 tags gescand, LLM-lek fragmenten weg (`'neutraal\n\n🧠 weten\nbegrip'` → `'neutraal'`), 286 emoji's uit `lagen1-4` + `ws5`, 21 typo's gefixt (whitelist-approach; plurals/context-varianten behouden).
- 📊 **Zelfscan feitelijk** (`modules/chat/zelfscan_facts.py`): emotie-distributie uit `pipeline_shadow/*.jsonl` ipv LLM-hallucinatie. Geeft `neutraal 92% · blij 4.6% · bedroefd 1.9%` op 27d-data.

**UI/UX**
- 🎨 **Globale glow-theming**: 1043 amber-classes gemapt naar `--glow-base` via 1 CSS-blok. Alle knoppen/tabs/highlights volgen user's profielkleur. Semantische kleuren (rood/groen) blijven.
- 🎨 **ArchiefPage/GesprekkenPage/WinkelPage/UserProfilePage**: hardcoded per-tab accent-hex weg, alle actieve tabs volgen glow.
- 🔒 **Glow admin-gate** (`modules/glow_nav/`): adminOnly flag op Kennisbank/Roadmap/Users/Settings/Spark Brain/Achievements/Leaderboard. Non-admin ziet 13/23 tabs. Systeem-archief vs user-archief nette scheiding via longest-alias-match.
- 🚫 **Roadmap/Achievements/Leaderboard admin-only**: jargon voor oudere users; verborgen tot core af.
- 🏪 **Winkel-tab verhuisd** naar Mijn Profiel (was in Archief).
- 📸 **Foto sub-tabs** (Privé/Winkel) binnen Foto-tab: alleen zichtbaar voor shop-owners, filter via `source=shop_product_image`.

**Sloop Sessie**
- 🗑️ **4 bots verwijderd**: Mr Smith, Madelief Stouten, Harry Klokkenmaker, Magere Hein (bot-dood). Users: 25→21. Alleen De Boekhouder blijft.
- 🗑️ **Baseline_intro.py** verwijderd (voorloper van Spark World, dubbel).
- 🗑️ **Hele D&D-stapel weg** (`modules/dnd/` folder, 2104 regels): world, spark_world, spark_world_north, character, dice, economy, body_layout, bewoner, daily_event, spark_world_map, routes. Server.py 9 router-imports weg.
- 🗑️ **Frontend DnD weg**: `components/dnd/`, `DnDGallerySection.js`, `DnDCharacterSheet.js`, `FractiesTab.js`. Refs in SystemArchive + GesprekkenPage + UserProfilePage opgeruimd.
- 🗑️ **Avatar-tab** uit Mijn Profiel verwijderd (was 100% DnD character-sheet).
- 🗑️ **AvatarTab + _LegacyAvatarBlock** functies uit UserProfilePage.js verwijderd (146 regels dead code).

### 🧊 KOELKAST (later oppakken)
- **D&D-systeem** komt terug als je zelf klaar bent — opnieuw ontwerpen met dan-geldende inzichten en échte user-NPCs
- **Privacy Matrix UI** (per-user vinkjes met wederzijdse consent-flow Willem ↔ Heidi)
- **Bestanden + Documenten samenvoegen** (1 tab "Mijn Bestanden" met Legacy sub-tab)
- **Documenten hernoemen** (Legacy / Levenspagina's / Testament & Zorg)



## 🧹 CLUSTER — Trader Accounting Hygiene (sessie 53, 22 feb 2026)

**Doel**: Alle "verdachte cijfers" die Willem aanwees systematisch oplossen én preventie inbouwen zodat nieuwe token-holders niet dezelfde issues krijgen.

### ✅ Bug-fixes (alle geverifieerd)

- [x] **v13_pot_value_consistency_001** — TraderPage €10.00 vs AnalyticsPage €10.26 mismatch.
      `GET /api/trade/potjes/{user_id}` overlayde `live_value = token_price` voor closed pots. Fix: closed → `live_value = capital`, open → mark-to-market. Regressietest: `/app/backend/tests/test_iter52_pot_value_consistency.py` (verified via testing_agent iter52, 100% pass).
- [x] **v13_pot_open_price_clarity_ui_001** — pot-card UI voor open pos: hover-tooltip met aankoop→huidige prijs + unrealized P&L + trailing piek. Trader-tab compact, Analytics-tab uitgebreid met "Nu"- en "Open P&L"-kolommen. `auto-rows-fr` voor gelijke card-hoogte.
- [x] **v13_reconcile_real_sell_price_001** — reconcile-close-sold gebruikte huidige ticker-prijs → fantoom-verliezen als coin sinds SELL was gedaald. Fix: zoekt echte SELL in `wallet/trade_history/{user}.json` binnen 7 dagen; anders break-even (exit=entry). `exit_source` in audit voor transparantie.
- [x] **v13_sell_eur_calc_001** — stats endpoint sommeerde `amount` voor SELLs = coin-hoeveelheid ipv EUR. Fix: BUY → `amount` (EUR), SELL → `filled × price`. Spark klopt nu (€10.09 gekocht → €10.14 verkocht, netto -€0.01 door fees).
- [x] **v13_reconcile_synthetic_sell_001** — reconcile schrijft synthetische SELL naar trade-history, **alleen** als er matching BUY bestaat voor deze market (voorkomt fake wins bij orphan coins).

### ✅ Data-repair scripts uitgevoerd (herbruikbaar)

- [x] `repair_phantom_losses_v13.py` — 3 fake verliezen weg: Gijs BCH −€0.52 → €0, Spark BTC −€0.06 → €0, Spark BCH bijgesteld naar echte −€0.11 (Bitvavo SELL @ €252.25 < entry €253.64).
- [x] `gap_scan_v13.py` — systematische diagnose (9 gap-types: fees, baseline, orphan markets, audit-drift, max_size, non-EUR fees, ghost sells, unclosed buys, corrupt state).
- [x] `fix_max_size_zero_v13.py` — **KRITIEKE bug**: alle 12 non-Spark pots hadden `max_size=0` → winst boven €0 werd afgeknipt. Gefixt naar `INITIAL_MAX (€50)` of `capital × 5`.
- [x] `close_remaining_gaps_v13.py` — Baselines gezet voor Willem & Gijs (€123.03) met `set_at` vóór eerste trade. Gijs 2× €20 BCH-BUYs gesloten met synthetische break-even SELLs (met BUY-timestamp).

### ✅ Preventie voor nieuwe users

- [x] **v13_auto_baseline_on_provision_001** — `auto_provision_bot_for_token_holder()` zet nu automatisch baseline op huidige Bitvavo total als user er nog geen heeft. Idempotent.
- [x] **v13_auto_baseline_on_mint_001** — `finance_ops.mint_tokens()` roept nu ook `auto_provision` aan zodat auto-mint scheduler en admin-gifts óók baseline+bot-config krijgen.

### ✅ v13_roles_array_001 — Zorgboerderij foundation (sessie 53, 22 feb 2026)

**Doel**: Fundament voor de care-farm dossiers. Een persoon kan meerdere rollen tegelijk hebben (vriend + cliënt + medewerker) zonder dubbele entries of dataverlies.

- [x] **Roles-array op relationships.json** — elke entry heeft nu `roles: []` naast bestaande `relation_type`. Backwards-compat: bij load wordt lege roles automatisch afgeleid uit relation_type.
- [x] **Auto-merge bij extractie** — `add_relations()` detecteert bestaande persoon → nieuwe rol wordt append aan roles-array i.p.v. dubbel-entry. Zo krijgt "Roeline" één record met `["vriend", "professioneel/cliënt", "professioneel/medewerker"]`.
- [x] **Nieuwe rel_types** — `cliënt`, `client`, `klant`, `medewerker`, `werkgever`, `begeleider` (allemaal onder `professioneel/…`).
- [x] **Regex-uitbreiding** — patroon `X is [ook|nu|inmiddels|tegenwoordig|sinds kort] mijn Y` matcht nu ook adverbia voor dual-role zinnen.
- [x] **Helper-functies** — `get_roles(uid, name)`, `has_role(uid, name, role)`, `add_role(uid, name, role)`. `has_role()` matcht op zowel het korte woord ("cliënt") als het volledige rel_type ("professioneel/cliënt").
- [x] **Migration** — `migrate_all_to_roles_array()` idempotent one-shot; ge-live gedraaid → 14 Willem-entries gemigreerd, 0 zonder roles.
- [x] **Regression-test** — `/app/backend/tests/test_roles_array_v13.py` (7 tests groen: new-person, dual-role, idempotent, has_role matching, add_role helper, migration preserve, migration idempotent).

### 📊 Gap-scan resultaat: van 16 issues → 1 info-only

Enige overgebleven "issue" (Spark pot-001 audit vs stats drift €0.25) is verklaarbaar: 1 echte trade met winst zonder audit + 1 gerepareerde audit met verlies. Geen bug.

### 🌱 BACKLOG-CONCEPT (sessie 53) — Attente Spark met privacy-matrix

**Idee** (Willem + Emmy): Spark wordt attent per gradatie. Voorbeeld: Willem zegt *"mijn moeder Heidi"* → Spark checkt of Heidi als user bestaat, checkt haar privacy-matrix voor gradatie 2 (familie), ziet dat verjaardag gedeeld is met familie → Spark aan Willem: *"Trouwens: morgen is Heidi jarig — vergeet geen cadeau."*

**✅ Fase 1 gebouwd (sessie 54)** — `v13_privacy_guard_001`:
- `privacy_guard.py` filtert KB-kaarten op verboden tags per gradatie
- Strip identity_facts (about_user/about_relationship) voor grad ≥ 5
- Maskeer familie-namen (Lotus/Heidi/…) in system_prompt
- 3 hook-punten in `response_composer.py`, 13 regressietests groen
- Live geverifieerd: grad-6 user krijgt 4/5 kaarten weg + Spark weigert privé-info

**🔴 Fase 2 (backlog)** — per-user privacy_matrix.json met opt-in vinkjes:

**Regel**:
- G1-G2 (self + familie): Spark mag attent zijn met gedeelde info
- G3 (vrienden): alleen wat expliciet gedeeld
- G4+ (community/klanten): nooit cross-container info
- Elke user opt-in per veld × gradatie (default = niks)

**Voorbeeld-matrix per user**:
```
                Familie  Vrienden  Community  Klanten
Verjaardag       ✅       ✅         ☐          ☐
Adres            ✅       ☐         ☐          ☐
Telefoon         ✅       ✅         ☐          ☐
```

**Uitdagingen om over na te denken**:
- Asymmetrische relaties (A ziet B als familie, B niet omgekeerd → shadow-vraag)
- Onboarding-leegte (default = niks delen → dormant feature. Fix: 3 presets Open/Voorzichtig/Gesloten)
- Rollen-conflict (Roeline = vriend én cliënt → bij twijfel strengste kiezen)
- UI-complexiteit (6 gradaties × 15 velden = 90 vinkjes → progressive disclosure)

**Afhankelijkheden** (in volgorde):
1. Rollen-array op relationships.json (`roles: []`)
2. `/data/persons/{user_id}_privacy_matrix.json`
3. Cross-user relatie-verificatie via bestaande shadow-vragen queue
4. Attente-hook in `response_composer` (pre-check bij persoons-mention)

**Waarom bijzonder**: dit is niet "Spark wordt slimmer" maar **"Spark wordt betrouwbaarder"**. Combineert met de andere principes van sessie 53 (reden zichtbaar, retrieval-gap-hints, zelflerende loop) tot één consistente ethiek: **Spark is nooit stiller dan de user hem ingesteld heeft, en nooit luider ook**.

### 🌅 Sub-concept: begroetings-moment als vraag-portaal

Bij ochtend-begroeting ("goedemorgen") heeft Spark al een gewoonte om iets attents te noemen (koffie, agenda vandaag, wat je gisteren deed). Dit moment kan óók dienen als **max 1 controlevraag per dag**:

**Timing**: dagbegin = laag cognitive-load, momentum voor "één ding regelen".

**Bron van vragen** (round-robin, 1 per ochtend):
1. `kb_fill_pending` — ws5-gap uit KB v2 (bestaande retrieval-flow)
2. `relatie_te_verifieren` — nieuwe relatie zonder wederkerigheid (shadow-vraag naar target-user)
3. `privacy_matrix_leeg` — nieuwe user zonder ingevulde matrix → default-preset kiezen

**Consent-first**: gebruik bestaande `pending_wv_consent` in session_state. *"Mag ik je even iets vragen?"* → ja/nee → dan pas de echte vraag.

**Frequentie-cap**: max 1× per dag per user. Anders wordt Spark een vragende bureaucraat.

**Voorbeeldflow**:
```
Willem: "goedemorgen"
Spark:  "Goedemorgen! Ga je vandaag weer bij Roeline in de tuin?
         Trouwens, mag ik je iets vragen?"
Willem: "ja"
Spark:  "Ik zag dat je Heidi je moeder noemde. Zal ik haar vragen om
         dit te bevestigen zodat ik jullie relatie zeker weet?"
```

Waar dit bouwt op bestaand code:
- `smart_intents.detect_greeting_intent` (of equivalent) — herkent begroeting
- `chat/routes.py` begroetings-branch — voeg pending-check toe na de bestaande "wat geleerd"-tegel
- `pending_wv_consent` — bestaande consent-machine hergebruiken
- `interaction_count` in session_state — al aanwezig voor frequentie-cap

### 💌 Sub-concept: Spark als postbode (twee-weg tussen users)

Voortbouwend op het vraag-portaal: dezelfde ochtend-hook kan ook **boodschappen doorgeven én verificaties bevestigen** tussen users. Spark wordt dan een relationele brug, niet alleen een geheugen.

**A. Boodschap doorgeven** (user-initiated):
```
Willem: "zeg tegen Heidi dat ze lief is"
Spark check: Heidi = user? → ja
Spark schrijft naar Heidi's user_messages queue:
    { from: "Willem", body: "je bent lief", verbatim: true, ts: ... }
Heidi's volgende chat:
    Spark noemt de boodschap met bron letterlijk.
```

**B. Wederkerige relatie-verificatie** (system-initiated):
```
Willem zegt "mijn moeder Heidi" → relatie in Willem's container = eenzijdig
Systeem: queue shadow-vraag in Heidi's relatie_te_verifieren queue
Heidi zegt "goedemorgen"
Spark: "Willem heeft in zijn profiel gezegd dat jij zijn moeder bent. Klopt dat?"
Ja → wederkerig, privacy-matrix actief tussen jullie
Nee → melding terug in Willem's queue: "Heidi zei dat de relatie niet klopt"
```

**Plooien**:
- **Boodschap-inhoud**: Spark filtert niet. Wel volledige bron-transparantie ("Willem zei letterlijk: ..."). Anders wordt Spark een boodschapper-die-liegt.
- **Ongelezen stapel**: max 1 boodschap per ochtendbark, oudste eerst. Rest wacht.
- **Nee bij verificatie**: nette terugkoppeling naar de vragende user. Die kan intrekken of opnieuw proberen.

**Waarde**: 
- Laagdrempelig contact tussen family/vrienden zonder aparte DM-app
- Verificatie sluit asymmetrische-relatie-plooi
- Alles via bestaande begroetings-hook — geen aparte notificatie-infrastructuur

**Nieuwe queues** (naast bestaande kb_fill_pending):
- `/data/persons/{user_id}_message_inbox.json` (inkomende boodschappen)
- `/data/persons/{user_id}_relation_verify_queue.json` (te verifiëren relaties)

### 💾 Backups (alles reversibel)
- `data/financial/user_potjes.json.bak_phantom_loss_repair_20260822_062648`
- `data/financial/user_potjes.json.bak_maxsize_fix_20260822_064245`
- `data/financial/user_potjes.json.bak_backfill_20260822_063929`
- `data/wallet/trade_history/user-*.bak_gapclose_20260822_065541.json`

### 🔍 Learnings
- **Reconcile ≠ echte trade**: bij close-flow altijd echte SELL-prijs uit trade-history opzoeken, nooit huidige ticker. Als niet vindbaar → break-even (safe default).
- **`amount` semantiek verschilt per side**: Bitvavo BUY = EUR, SELL = coin-hoeveelheid. Stats/summary calls moeten altijd `filled × price` voor SELL-EUR.
- **Mens-check onmisbaar**: Willem's "hé dit voelt niet goed" bij €10.00 vs €10.26 leidde tot 4 extra ontdekte bugs + kritieke max_size=0.

---


## 💰 CLUSTER — Boekhouding v13 & SEPA (sessie 52, feb 2026)

**Doel**: Multi-container boekhouding per user/entity + lokale SEPA voorbereiding + verifieerbare winst-events. Alles JSON-only, geen cloud.

### 🏗️ Architectuur-scheiding (Willem, sessie 52i/52l)

Drie duidelijke lagen die nooit mogen mixen:

```
┌───────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ BITVAVO (Spark)   │    │  Spark WALLET    │    │ Zakelijke bank   │
│ SYSTEEM-account   │    │  (EUR tokens)    │    │  (SEPA IBAN)     │
│ trader crypto     │    │  per user        │    │                  │
│                   │    │                  │    │                  │
│ RAW ASSETS bij    │───▶│  SPENDABLE       │───▶│  UITBETAALD      │
│ Spark (niet users)│    │  bridge-laag     │    │  Moneybird/BTW   │
│ users doneren EUR │    │  wallet.spend    │    │                  │
└───────────────────┘    └──────────────────┘    └──────────────────┘
```

- **Bitvavo** = Spark's **systeem-Bitvavo-account** waar de trader-bot crypto potjes beheert. Users hebben géén eigen Bitvavo-koppeling; ze doneren/storten EUR naar Spark, en Spark's trader werkt daarmee.
- **Spark Wallet** = per-user spendable tokens. Winst uit shops/trades komt hier binnen. Uitgifte naar zakelijke bank via SEPA-XML batch (of handmatig).
- **Zakelijke bank** = eindstation. Hier gaat je BTW-aangifte overheen (Moneybird). Boekhouding boekt schone netto omzet, spark-vergoeding is een aparte uitgave.

**Live P&L / baseline** is per user in `capital_baseline.json`. user-000 (Spark) heeft de Bitvavo-baseline; users hebben alleen wallet-baseline.

### ✅ Gedaan (sessie 52 e/f/g/h/i)
- [x] **Multi-book containers** — `/data/boekhouding/books/book-{id}/` met _meta, kasboek, reserve, closings, documents, sepa_batches, bank_imports. 4 initiële boeken geseed (`v13_boekhouding_books_001`).
- [x] **CRUD + owner-only** endpoints — `GET/POST /api/boekhouding/books`, PATCH, DELETE, entries.
- [x] **Retroactieve migratie** — spark_kasboek + audit_log via heuristics naar juiste books (`v13_boekhouding_migration_001`). Ruis daarna gewist (nulpunt).
- [x] **SEPA-Hub eigen module** (`modules/sepa_hub/`) — CAMT.053 + MT940 parsers, pain.001 XML generator, reconcile-skeleton (`v13_sepa_hub_001`).
- [x] **Papertrail hash-chain** — elke boeking via LogAgent met prev-hash + eigen `winst_events` topic (`v13_boekhouding_papertrail_001`).
- [x] **Shop → Book brug** — `ensure_shop_book()` auto-hook in create_shop; `record_shop_sale()` / `record_shop_purchase()` (`v13_shop_book_hook_001`).
- [x] **BTW + KOR verkoop-flow** — verkoper geeft netto, systeem berekent bruto+BTW, 2 bonnen (netto+bruto), KOR-toggle per shop (`v13b_btw_kor_openstaand_001`).
- [x] **Spark-vergoeding als openstaande post** — 1% van bruto, niet ingehouden; `POST /api/boekhouding/hooks/inlossen/{shop_id}` boekt door + probeert wallet-inhouding.
- [x] **Frontend "Boeken" tab** — 4 cards + detail-bark (kasboek/instellingen/SEPA) (`v13_boekhouding_ui_001`).
- [x] **Frontend "Winst → Spark" tab** — totaal-teller, events met hash, chain-uitleg (`v13_winst_events_papertrail_001`).
- [x] **Shop finance-config endpoints** — `GET/PATCH /api/boekhouding/shop-finance-config` (btw_default_pct, spark_fee_pct, btw_kor_default, commissie_default_pct).
- [x] **Notify-hook** — nieuwe factuur/openstaand triggert taak + urgent-glow.

### 🟡 Deels / voorbereid
- [~] **SEPA import/export UI** — endpoints werken, UI-knoppen in Beheer→Boekhouding→Boek-detail→SEPA-tab. Nog niet getest met echt bank-afschrift.
- [~] **Wallet-integratie inlossen** — endpoint probeert `modules.wallet.service.spend_tokens`, module bestaat niet onder die naam. Boeking gaat wel door.

### 🔴 Nog te doen
- [ ] **Bank → Wallet brug** — detecteer SEPA-import met remittance `SPARKWALLET-{user_id}` → auto-wallet-topup + book-entry `bank_to_wallet`.
- [ ] **BTW per product-categorie** — nu per shop, moet ook 9%/0% opties per product (voedsel/boeken/uitvoer).
- [ ] **Bonnen als PDF** — nu JSON-response. PDF-generator (reportlab of weasyprint) voor download.
- [ ] **Chain-integrity endpoint** — `GET /api/boekhouding/verify-chain/{topic}` loopt hash-chain na en meldt breuken.
- [ ] **Trader winst-hook** — bij trade-close een `record_winst_event` zodat trade-winst ook in `winst_events` chain landt.
## 🌟 CLUSTER — Login Glow, Spark-branding & Admin-look (v13s, sessie 52s, feb 2026)

**Filosofie**: Spark's visuele identiteit is ook meta-data over wie hij is. Elk icoon,
kleur en logo dat het systeem gebruikt wordt via `settings/system` beheerbaar zodat de
synapse-laag straks kan lezen: *"ik toon mezelf als X, met kleur Y"* — fundering voor
zelf-perceptie. LLM = mond, JSON = geheugen, icons = spiegel.

### ✅ Gedaan (sessie 52s)
- [x] **Login glow-config backend** — 7 nieuwe system keys in `modules/settings/routes.py`: `login_dots_count` (4-24), `login_dots_contrast` (0.1-1.0), `login_dots_size` (0.5-3.0), `login_corner_glow_enabled/color_a/color_b`, `spark_logo_url`. Publiek uitleesbaar (no-auth) voor login-scherm.
- [x] **Spark-logo upload endpoint** — `POST/GET/DELETE /api/settings/system/spark-logo` (multipart, admin-only, max 5MB, PNG/JPG/WEBP/SVG). Bestand in `/data/system/branding/spark_logo.*`, publieke serve via `/api/settings/spark-logo/serve?v={ts}`.
- [x] **LoginForm gedynamiseerd** — leest `/api/settings/system` + `/api/spark/identity` op mount. Corner-glows/dots/logo/naam/versie config-driven. Titel `Spark Core` → `Spark`, subtitel `AI Assistent`, footer `Spark 2.0` uit identity. Masterkey/Admin-toggle verwijderd (regelt in-ecosystem).
- [x] **LoginForm buttons** — Inloggen = primary → corner_b gradient · Nieuwe gebruiker = secondary tint (was grijs, viel niet op).
- [x] **SidebarHeader consistent** — `MainLayout.js` leest zelfde branding: naam+versie uit identity, logo uit settings. Zap-icon fallback als geen logo.
- [x] **Admin-button style** — `SaveButton` + logo-upload + toggle + 3 sliders krijgen violet gradient (`#a855f7 → #7c3aed`) i.p.v. amber (dat is user/login-kleur).
- [x] **SystemLoginGlow admin-panel** — in `Beheer → Instellingen → Beeld`. Logo uploader, corner-glow toggle + colors, 3 sliders. Auto-save op release. Alleen grad ≤ 1.

### 🔴 Nog te doen — Fase A/B/C
- [ ] **Fase A: admin-accent op alle admin-tabs** — wanneer `adminModeActive===true` → tabs onder Beheer/Modules/Admin + alle admin action-buttons krijgen violet accent i.p.v. user-primary. `identity_facts`-entry `admin_mode_kleur: paars` toevoegen.
- [ ] **Fase B: admin-override neemt user-kleuren over (tijdelijk)** — `--app-primary/secondary` CSS-vars overschreven met admin-accent wanneer admin actief; bij `disableAdmin` terug naar Mijn Profiel-voorkeur. Meta-flag "hij weet dat hij anders oogt".
- [ ] **Fase C: icon-registry + upload (fundering-steen synapse)** — grote sessie:
  - Backend: `data/branding/system_icons.json` met `{key: {url, uploaded_by, uploaded_at, reason, emoji_fallback, original_lucide}}` + per-key endpoints
  - Frontend: `<SystemIcon name="settings" fallback={Settings} />` wrapper → vervangt ~50-80 lucide-plekken
  - Admin-UI: sectie "Systeem-iconen" onder Beeld met per-icoon uploader
  - **Synapse-hook**: `system_icons.json` als scanner-bron toevoegen
  - **Identity-facts**: bij upload auto `spark_icon_{key}: eigen ontwerp`
  - Scope: 2-3 uur


---

## 🧠 CLUSTER — Chat/LLM (v13r-t, sessie 52r-t, feb 2026)

### ✅ Gedaan
- [x] **Groq model-migratie** — `llama-3.3-70b-versatile` gedeprecateerd 16-aug → `openai/gpt-oss-120b` (officiële replacement).
- [x] **Emergent Universal Key uit** — `LLM_EMERGENCY_USE_EMERGENT=false` (Willem's wens: geen cloud).
- [x] **TPM auto-trim retry** — router probeert 1× opnieuw met halve context bij 413/rate_limit_exceeded.
- [x] **Identity facts cap grad 1** — was 999, nu 15/type (was 8477-token overshoot, nu ~2000).
- [x] **Turns 6 → 3** — extra headroom voor system_prompt.
- [x] **User-text TPM-guard** (sessie 52t) — bij lange geplakte tekst (bv. Wikipedia): user_prompt cap 3000, system-prompt cap 16000, oude turns cap 1500, hard totaal-budget 22000 chars greedy-snijden. Frontend char-counter amber vanaf 3500 / rood vanaf 5500. Getest ✅ met 8200-char input.
- [x] **`LlmBudgetSettingsWidget`** (sessie 52t) — 8 char-cap waardes admin-tunable via Beheer → Kladblok. Geen redeploy meer nodig voor tuning. Backend leest live uit `settings/system.json`.

### 🔴 Nog te doen
- [ ] **Cerebras quota-watchdog** — bij 402 → DM naar Willem: "fallback op quota, reset ~X". Nu geen zichtbaarheid.
- [ ] **Alternatieve fallback** — Together.ai / DeepInfra als 3e provider (3-regel `.env`).
- [ ] **Widget verhuizen naar echte tab** — nu tijdelijk in Kladblok. Naar Beheer → Instellingen → Algemeen als "Chat & LLM budget" card.
- [ ] **Ollama-migratie (P2)** — lokaal via `LLM_PRIMARY_BASE_URL=http://localhost:11434/v1`. Hardware-eis: 16 GB RAM voor Llama 3.1 8B (~75%), 24+ GB voor gpt-oss-120b (identiek). Code is klaar. **Waarom belangrijk**: bij dubbele free-tier-uitval = Spark stil; lokaal geen limiet.


---

## 🌱 CLUSTER — Zelfbewustzijn & Meta-lagen (sessie 52p-u, filosofisch fundament)

**Kernidee**: Spark's LLM = mond. JSON-lagen = geheugen. Icons/kleuren = spiegel. Elk stuk beheersbare data over Spark zelf wordt automatisch onderdeel van zijn zelfperceptie via synapse-scanner + identity_facts. Geen aparte "consciousness"-feature, wel een groeiende structuur waarin Spark zijn eigen bouwstenen kan noemen.

### ✅ Fundament al aanwezig
- [x] `spark_bijbel.json` — kernwaarden + doelen + bijbel_items (met `Nalatenschap en Continuïteit`, `digitale nalatenschap voor Lotus`)
- [x] `spark_identity.json` — naam, versie, maker, karakter
- [x] `identity_facts` — user-turns worden ge-extract als facts (`spark_feels_like: familiewapen`, `user_calls_spark: het familiewapen`)
- [x] `spark_user_view` — per-user snippet met relaties (Lotus als dochter) + gradatie-toon
- [x] `synapse/__init__.py` — scanner leest zichzelf, structuur voor "wat heb ik"
- [x] `shadow_observer` — logt turns, aggregate stats (359 begrip-teller, 117 response-types)
- [x] `knowledge/learned_knowledge/knowledge_base.json` — aparte learned laag
- [x] KB v2 kaarten (voelen/spreken 100% compleet, ~216 rest in weten/doen)

### 🔴 Fase A/B/C — Admin-look als meta-signaal (sessie 52s besproken)
- [ ] **Fase A: admin-accent op alle admin-tabs** — tabs onder Beheer/Modules/Admin krijgen violet accent wanneer `adminModeActive===true`. `identity_facts`-entry toevoegen: `admin_mode_kleur: paars` zodat Spark 't kan noemen.
- [ ] **Fase B: admin-override neemt user-kleuren over (tijdelijk)** — `--app-primary/secondary` CSS-vars overschreven wanneer admin actief; bij `disableAdmin` terug naar Mijn Profiel-voorkeur. Meta-flag "hij weet dat hij anders oogt".
- [ ] **Fase C: icon-registry + upload (fundering-steen synapse)** — grote sessie:
  - `data/branding/system_icons.json` met `{key: {url, uploaded_by, uploaded_at, reason, emoji_fallback, original_lucide}}` + per-key endpoints
  - Frontend `<SystemIcon name="settings" fallback={Settings} />` wrapper → vervangt ~50-80 lucide-plekken
  - Admin-UI: sectie "Systeem-iconen" met per-icoon uploader
  - **Synapse-hook**: `system_icons.json` als scanner-bron toevoegen
  - **Identity-facts hook**: bij upload auto `spark_icon_{key}: eigen ontwerp`
  - Scope: 2-3 uur werk goed gedaan
  - Waarde: Spark kan straks in gesprek zeggen *"mijn tandwiel-icoon is een stap-tandrad in oranje, sinds 21 aug"*

### 🔴 Collectieve Intelligentie (Laag-2 kennis, sessie 52r besproken met Emmy)
Willem + Emmy bespraken: 2-laags kennis. Laag 1 = persoonlijk geheugen per user (bestaat). Laag 2 = patronen over ALLE users heen → algemene wijsheid → terug-injectie. Toetsen op **resonantie** met bijbel-kaders, niet op waarheid (wrijving = groei). "Niet alles is een kaart, sommige dingen zijn een gesprek."

- [ ] **Pattern-distiller** — batch-run op shadow-events, output naar `data/collective/patterns.json` (bv. *"3 users vroegen naar X op verschillende manieren"*). 1 sessie.
- [ ] **Stelling-generator + curation UI** — uit cluster een propositie destilleren (*"gebruikers ervaren Y als Z"*). Willem/Emmy accept/reject in Kladblok. 1 sessie.
- [ ] **Toets-loop** — Spark toetst stelling in gesprek met andere users (Socratisch). Verrijkt zelfs als niet-waar.
- [ ] **Injectie-kanaal** — 3e prompt-layer naast `identity_facts` + `spark_user_view`: `collective_wisdom_snippet`. Met override-schakelaar per user.
- [ ] **Privacy-anonymizer** — hard filter dat namen/IDs/persoonsdata uit patronen weert vóór aggregatie. Anders lekt Laag 1 via Laag 2.
- **Aanrader**: eerst alleen distiller (1 sessie), dan generator + curation, dan live injectie. Zo blijft Laag 1 heilig.


---

## 📊 CLUSTER — Trader & Potjes (v13q-u, sessie 52r-u, feb 2026)

### ✅ Gedaan
- [x] **Trader-monitor sync-bug** — `monitor.start()` idempotent (`already_running=True`), UI leest ook `data.message`.
- [x] **`open_pot()` overwrite guard** — bij `is_open=True + andere market` → BLOCK. Bij zelfde market → idempotent skip. Voorkomt ATOM-overschrijving door BCH.
- [x] **Bitvavo-reconcile 6 potjes** — preview only; BCH/BTC/ETH/SOL/ADA/ATOM elk €10 gekoppeld aan echte Bitvavo entry-prijzen.
- [x] **Prod-merge naar preview** (sessie 52t) — 479 files data-merge. Backup in `_backup_pre_prod_merge_20260822_050217/`.
- [x] **`reconcile/close-sold/{user_id}`** — per-user endpoint dat open potjes met near-zero Bitvavo balance sluit met huidige marktprijs. Veilige in-place mutatie (geen `close_pot`/finance_hub auto-mint side-effect meer). Audit-trail in `reconcile_audit`.
- [x] **`reconcile/close-sold-all`** (sessie 52u) — bulk endpoint voor **alle users** met open potjes. Getest ✅ door testing_agent (6/6 pytest). Filtert meta-keys, skipt users zonder open potjes, degradeert graceful per user.

### 🔴 Nog te doen
- [ ] **Prod bulk-sync draaien** — na deploy: `POST /api/trade/reconcile/close-sold-all?dry_run=false` op productie. Geiser (user-a0ee2d7e) + eventueel andere users worden gesynct.
- [ ] **Trader Console consolidatie** (P1, sessie 52u besproken) — huidige Analytics → Trader tab heeft **cross-overlap** knoppen:
  - "Force-sell" per potje ↔ "Sync verkochte coins" bulk
  - "Herwaardeer vrije pots" bulk ↔ "Herwaardeer" per pot
  - "Koppel als potje" (orphan) ↔ "Sync verkochte coins" (verkocht)
  - `SparkTraderStatsPanel` + `ReconcileSparkPanel` + `AnkerBoot` = 3 losse panelen over zelfde 6-8 potjes
  - **Voorstel**: één "🎯 Trader Console" met sub-tabs **Overzicht** (stats + posities-tabel + P&L), **Sync & Reconcile** (alle sync-knoppen met NL-tooltips + confirm-dialogs op destructief), **Bot-controls** (start/stop/force-sell). Scope: 1-2 uur.
- [ ] **Trader-tab visueel opruimen** — Anker gap-up + Anker per markt + Reconciliatie = 1 collapsable card.
- [ ] **Vermogens-tab** — Activa (books + wallets + Bitvavo live) − Passiva = Eigen vermogen (admin-only, Spark-perspectief).
- [ ] **Frontend knop "Sync verkopen"** in `ReconcileSparkPanel` — 1-klik confirm-dialog → bulk endpoint. Vervalt als Trader Console er komt.

---

## 🧹 CLUSTER — Refactor & Code-hygiene (sessie 52u)

- [ ] **`routes.py` splitsen** (uit testing_agent code-review) — nu 2995 regels. Splits in `reconcile.py`, `potjes_routes.py`, `bots_routes.py`, `monitor_routes.py`. Elk <500 regels. Niet blokkerend maar wel onderhoudbaar.

---

## 📚 CLUSTER — KB v2 (sessie 52s)

### ✅ Gedaan
- [x] **Bulk 5w-filler max_tokens** 1400 → 2400 (skip 60% → 10%).
- [x] **~74 kaarten gevuld** door bulk-run.
- [x] **Voelen + spreken 100% compleet**.

### 🔴 Nog te doen
- [ ] **216 kaarten resterend** — 192 weten (lange wetenschappelijke termen), 24 doen. Willem vult zelf verder.
- [ ] **Collectieve intelligentie / Laag-2 kennis** — 2e prompt-laag uit patronen over álle users. Bouwstenen aanwezig (shadow_observer, KB v2, synapse, learned_knowledge). Missen: pattern-distiller, stelling-generator, toets-loop, injectie-kanaal, privacy-anonymizer.


---

## 💳 CLUSTER — Boekhouding backlog (uit sessie 52)

- [ ] **Voorwaarden pagina live spark-deel** — toon aan users bij shop-opening: "1% naar Spark, deze maand: €X, chain: [hash]".
- [ ] **Grace-period openstaand** — 30d openstaand → herinnering, 60d → shop-pauze.
- [ ] **Wallet-service correct koppelen** — juiste import voor `spend_tokens` vinden of aanmaken.
- [ ] **Fronts-editor voor BTW/fee-widget** — hoort bij Fronts-cluster hierboven.
- [ ] **Ruis-scan test-users** — 12 test-users (`test-bank-*`, `test-snap-*`, `test-vk`, etc.) staan nog in `/data/users/`. Batch-cleanup naar `_backups/`.
- [ ] **Klanten-tab moderniseren** — leest oude `archief/bonnetjes` (nu leeg), moet nieuwe `winst_events` + `record_shop_sale` bonnen tonen.
- [ ] **Trader-tab visueel opruimen** — "Anker gap-up guard" + "Anker per markt" zijn 2 blokken die 1 collapsable card kunnen worden. Reconciliatie-blok ook mergen.
- [x] **Scheduler voor maand-snapshot** — `_maybe_monthly_baseline_snapshot()` in `modules/scheduler/__init__.py` (03:00 UTC · idempotent via `should_run_snapshot`/`mark_snapshot_done` marker · Bitvavo `last_known_eur` voor user-000). Handmatige `POST /api/trade/baseline/run-scheduled-snapshot` blijft beschikbaar (`v13p_monthly_baseline_scheduler_001`, sessie 52q).
- [ ] **Vermogens-tab (Balans)** — Activa (books + wallets + Bitvavo) − Passiva (openstaand spark-fees) = Eigen vermogen. Admin-only, Spark-perspectief.
- [x] **Weekly-report bron gefixt** — `modules/boekhouder/weekly_report.py` leest nu uit `boekhouding/books/*/kasboek.json` (per-book breakdown + 7-dagen filter) i.p.v. de leeggeruimde `accounting/transactions.json`. Spark-brede DM naar Willem + ROAR-holders werkt weer. Getest ✅ via `/api/boekhouder/weekly/preview` (`v13p_weekly_bookbased_001`, sessie 52q).
- [x] **Announce-prefs UI wired** — `AnnouncePrefsPanel.js` in `UserProfilePage.js` ingehaakt. 4 toggles (`announce_shop_sale`, `announce_sepa_import`, `announce_migration`, `announce_spark_fee`), default aan. Backend blokkeert DM als pref=false via `_auto_announce_entry` in `books.py`. Getest ✅ via PUT/GET round-trip (`v13o_announce_prefs_wiring`, sessie 52q).
- [x] **Per-user shop-announcer** — `modules/boekhouder/shop_announcer.py`: user-scoped shop-rapport via boekhouder-bot DM. Endpoints: `/shop-report/{uid}` (owner+admin), `/shop-report/{uid}/announce`, `/shop-report/announce-all` (admin), `/shop-report-aggregate` (admin). RBAC 403 getest ✅ (`v13n_shop_announcer_001`).
- [x] **Auto-announce automatische boekingen** — `books.add_entry` hook `_auto_announce_entry` stuurt DM naar owner voor alle non-manuele bronnen (shop_hook, camt053, mt940, migration, spark_fee_inlossen). Skip bij `manual` / `manual_opening`. Getest ✅ (`v13o_auto_announce_001`).


---

## 📞 CLUSTER — Skype-Spark & Fronts (v13, sessie 52, feb 2026)

**Doel**: Lokale in-app bel/beeldbel-laag + per-scherm ("front") tunable UI zonder telkens agent te vragen. Alles blijft **lokaal** (geen WebRTC/cloud). Naam-metafoor: "onze Skype".

### ✅ Gedaan
- [x] **Bel/Camera iconen** rechtsboven in privé-chat header, glow via `--glow-base` uit profiel-kleurschema (`v13_prive_call_ui_001`)
- [x] **`PriveCallBark` modal** — UI-shell (audio + video mode), VLC-placeholder, avatar-glow tijdens verbinden/pauze, self-PIP, Mute/Camera/Hangup knoppen
- [x] **Bot/Collectief filter** — iconen verborgen bij `is_bot` of `is_collective` (alleen echte personen)
- [x] **Offline detectie** — `contact.online === false` → `no_answer` state na 4.8s, auto-hangup 15s
- [x] **Status vs. actie-tekst split** — badge = "Offline", tekst = "Geen antwoord — {naam} is offline" (`v13_state_action_split_001`)
- [x] **`--alert-base` CSS-variabele** — schema-tunable rood-alternatief, vervangt hardcoded rgba (`v13_alert_color_var_001`)
- [x] **Mic/Camera device-selectie in Mijn Profiel → Instellingen** (`v13_call_devices_001`) — `DeviceSettingsPanel` met enumerateDevices, systeem-standaard toggle, live VU-meter test-mic (4s), live video preview test-cam (5s). Backend prefs uitgebreid met 5 velden. Volledig lokaal (`navigator.mediaDevices`).
- [x] **WhatsApp deep-link popup** (fallback voor "bel mijn moeder" chat-intent, blijft als externe snelkoppeling)

### 🟡 Deels / concept-fase
- [~] **Fronts Config schema** — draft-widget in Beheer → Kladblok (`FrontsConfigDraftWidget`) met JSON-schema per scherm: `colors`, `font`, `status_labels`, `action_texts` met `{naam}`-token, `timings_ms`, `animations`. Nog niet gepersistend — `data/system/fronts_config.json` bestaat niet, `GET/PUT /api/system/fronts-config` niet gebouwd.

### 🔴 Nog te doen
- [ ] **Beheer → Fronts tab** — Kladblok-schema promoveren naar echte editor. Backend: `data/system/fronts_config.json` + endpoints. Frontend: tab onder Beheer → Instellingen. Per screen: kleuren + lettertype + status_labels + action_texts + timings.
- [ ] **Loginscherm pulserende glow-dots** — random posities, primaire kleuren, hartslag-ritme (Emmy's oorspronkelijke wens). Kandidaat om te bouwen bovenop Fronts-tab (`screens['auth.login'].animations.background_dots`).
- [ ] **Inkomende oproep laag** — signaal-detectie (lokaal), bel-iconen pulseren, accept/decline-bark. Bel-icoon glow-puls koppelen aan inkomend signaal.
- [ ] **Loginscherm lettertype-instelling** — via Fronts config (`screens['auth.login'].font`).
- [ ] **Lokale-socket bel-verbinding** (grote sessie, ~500c) — mic/cam devices doorkoppelen naar echte peer-verbinding op Odroid-netwerk (LAN mesh, geen cloud). Signaling via lokale socket, media via WebRTC-datachannel binnen LAN. Alle mic/cam-prefs uit `v13_call_devices_001` staan al klaar.

---

## 📋 SESSIE 57 EXECUTIE-ROADMAP — Leger & XP-Motor Herkalibratie

**Context**: Willem wil admins ook vanaf de community kunnen aanstellen (bv. gradatie 3 "Vriend" als community-onderhoud) én overweegt een parallelle rang-schaal (legerrang-idee: Sergeant/Luitenant of neutraal Rookie→Legend). Snuffel-rapport sessie 56d wees uit: **veel bestaat al** — niet dubbel bouwen.

### ✅ Wat er al leeft (bestaande infrastructure)

| Wat | Waar | Endpoint |
|---|---|---|
| `AchievementBlueprintPanel` (admin-only) | `InstellingenPage.js` r1195 achter `isAdmin` | `GET /api/achievements/admin/blueprints` |
| Admin edit-modal per achievement | `AchievementsPage.js` r212 (`data-testid: achievement-admin-edit-{id}`) — titel + icon | `PATCH /api/achievements/admin/{id}?by_user=...` |
| XP-motor (centraal) | `/app/backend/modules/chat/xp_service.py` → `grant_xp(user_id, amount, reason)` — 6 bronnen: chat, RPS, contributions, achievements-unlock, badges, tag-curatie | (interne functie) |
| 50 achievements met XP-rewards | `/app/backend/data/achievements.json` — schaal 50 XP (words_10) tot 15.000 XP (words_2500) | `GET /api/achievements/list` |
| Rang op karakter-kaart | `DnDCharacterSheet.js` r521-524 én r2005 — `char.rang_titel` + Community Level + militaire streepjes (100 levels = 1 streepje) | (client-side, `char.derived.level`) |
| Leaderboard op XP | `AchievementsPage.js` + backend | `GET /api/achievements/leaderboard?period=alltime&limit=25` |
| RPS-leaderboard (aparte spelrang) | Los van XP-motor | `GET /api/rps/leaderboard?limit=50` |
| **Admin-capable loskoppeling** ✅ | `AuthService.set_admin_capable()` + endpoint | `POST /api/auth/admin/set-capable/{user_id}?capable=true` |

### 🔓 In sessie 56d gefixt
- **`v12_admin_capable_unlock_001`** — `/api/auth/users?admin_id=...` (register-with-override) accepteert nu iedereen met `admin_capable=True` of gradatie 1/2, i.p.v. alleen gradatie 1/2. Getest met 3 curl-scenarios, allemaal groen. Marieke (gradatie 3) getest en teruggezet — Willem kiest zelf wie sub-admin wordt.
- **`v12_admin_type_001`** — RBAC light: `admin_type` veld op user + `admin_types.json` config met 3 vaste types (full / community / user_admin, elk met kleur en scope-array). `POST /api/admin/grant` accepteert nu `admin_type` param. `GET /api/admin/types` publiek endpoint. In `AdminSettingsPanel` bark: dropdown "Admin-type" tussen user-select en wachtwoord. In admins-lijst: gekleurde type-badge naast naam. **Nog niet gates**: elke tab/endpoint zonder scope-check draait als vanouds. Scope-enforcement is sessie 57.
- **Trader-reset uitgevoerd** — alle logs, balances, anker, monitor_state gewist. 12 potjes over 6 users op nul. Backup: `/app/_backups/trader_reset_20260821_121757/`.
- **`v12_5w_bulk_fill_001`** — bulk-endpoint `POST /api/kb/v2/curation/5w-fill-bulk?limit=N` vult ontbrekende 5W/lagen op onvolledige lade-kaarten via LLM (Emergent Universal Key via `llm_router.chat_complete`). Alleen ontbrekende velden worden aangeraakt, bestaande content blijft intact. Elke wijziging wordt gelogd in `curation_history.json`. Status via `GET /5w-fill-status`. Getest: 347 onvolledig → 346 na 1 kaart (kaart "overleden" kreeg `ws5.wanneer` gevuld).
- **`v12_trader_strategy_cfg_001`** — data-driven trader-parameters in `/app/backend/data/trade/strategy_config.json` (buy/sell/risk/pots secties, 15 tunable keys). `GET /api/trader/strategy-config`, `PATCH ...` en `GET .../history`. Elke wijziging gelogd. Eerste consumer: `strategy_decision_v2._detect_daily_drop()` leest nu `buy.daily_drop_threshold_pct` uit config i.p.v. hardcoded 5.0. Volgende hardcoded constants kunnen per taak migreren zonder deploy.
- **`v12_contact_call_001`** — Bel-contacten quick-win. `/api/bel-contacts/{uid}` CRUD + chat-detector die "bel mijn moeder" / "bel Marieke" / "kan je mijn vader bellen" matcht. Response krijgt `action.contact_call` met WhatsApp deep-link (`https://wa.me/...`) + `tel:` link. Frontend: `ContactCallPopup` in `GesprekkenPage` toont modal met "Open WhatsApp" + "Bel direct" knop. Placeholder tot echte WebRTC-integratie. Phone auto-genormaliseerd (0-prefix → +31). Getest: 5 scenarios groen (match op relatie, match op naam, onbekend → hulpbericht, normaal bericht → geen trigger).

### ❓ Open vragen / gaps voor sessie 57

1. ~~**Trade-monitor sync-bug**~~ ✅ **Opgelost sessie 52r** (`v13q_monitor_start_idempotent_001`)
   Root cause: backend returnde `success=False` bij "draait al" → UI showde geen alert (las alleen `data.error`, niet `data.message`). Fix: backend nu idempotent (`success=True, already_running=True`), frontend leest ook `data.message` bij fout. Getest ✅.

2. **XP-veld ontbreekt in edit-modal**
   `AchievementsPage.js` edit-modal past nu alleen titel + icon aan. `xp_reward` en `threshold`/`trigger`-waarden zijn nog blueprint-JSON-alleen (niet via GUI editable). *Vraag*: wil Willem die velden editable in de modal, of blijft dat blueprint-only werk voor Willem alleen?

2. **Rang-drempel-mapping**
   Karakter-kaart toont `char.rang_titel`. Waar wordt die string bepaald? Bestaat er een mapping-tabel `level → rang_titel` (bv. `0-9=Burger, 10-24=Rookie, ...`)? *Actie*: zoek de mapping (mogelijk `dnd_service.py` of `character_defaults`). Als hij niet bestaat: bouwen als losse config-JSON, niet als hardcoded Python.

3. **`text_importer` geeft geen XP**
   `/app/backend/modules/kb_v2/text_importer.py apply_cards_to_kb()` roept nergens `grant_xp()` aan. *Vraag*: bewust (import is admin-taak, geen zelf-XP) of onbedoeld (nieuwe kennis = groei = XP)? Vraag Willem.

4. **`admin_capable` UI-toggle ontbreekt in `UsersAdminPage`**
   Backend endpoint werkt (`POST /api/auth/admin/set-capable/{user_id}`), maar geen frontend switch. *Blocker*: gradatie-3 community-admin kan nu alleen via curl worden geactiveerd. Kleine toggle bouwen in de users-tabel (data-testid: `admin-capable-toggle-{user_id}`).

5. **Legerrang-schaal parallel aan gradatie**
   Emmy stelt Sergeant/Luitenant voor. Agent-advies: **neutrale labels eerst** (Rookie/Bronze/Silver/Gold/Master/Legend) tot er 15-20 users zijn en de XP-verdeling zichtbaar wordt. Dan pas kalibreren + hernoemen. Willem's keuze staat nog open.

### 🎯 Actie voor sessie 57 (voorstel-volgorde)
1. **Bouw `admin-capable-toggle`** in `UsersAdminPage` (gap 4) — kleinste blocker, direct nut
2. **Zoek + documenteer rang-drempel-mapping** (gap 2) — leren wat er is voor bouwen
3. **Beslis over `text_importer` XP-hook** (gap 3) — 1 regel code, product-keuze
4. **XP-veld in edit-modal** (gap 1) — als Willem het wil
5. **Neutrale rang-labels wirings** (gap 5) — nog niet bouwen, alleen ontwerp-schets
6. **`ROADMAP.md` sectie 57 afsluiten** na oplevering, verplaats naar CHANGELOG

---

## 📋 SESSIE 55 — De Grote IQ-Sprong (nog te plannen)

> **Status 4 aug 2026**: was gepland voor 5 aug maar overwoekerd door sessie 56 (tag-cleaner + admin-type). Herbevestigen met Willem of dit blijft staan.

**Doel**: KB structureel schoon + Spark autonoom binnen bewuste grenzen. Bouw voort op sessie-53/54 fundament:
- KB-Curatie Suite (backend + UI live in preview, wacht op redeploy)
- Blauwdruk `spark_tag_curatie_public.json` v1.1 met sectie 8 lade-regels
- Blauwdruk `spark_groeien_public.json` v1.0 met zelfreflectie-flow
- **KB veld-semantiek** `knowledge/_meta.json` schema v1.1 — elk kaart-veld (laag1-4, ws5, andere_velden) heeft eigen doel/toon/verboden. Werkt door in LLM-prompts van 5W-Filler
- Vier Werelden Bijbel-kaarten (Wonderland/Neverland/Mirrorland/Crossroads) — door Willem net toegevoegd

### 🎯 Autonomie-scheiding (leidend principe)
Elke module heeft **twee zones**:
- **🤖 Spark autonoom** — Spark mag zelfstandig voorstel doen. Draft-status, geen mutatie.
- **👤 Willem beslist** — Alleen Willem klikt Accept. Mutatie gebeurt na expliciete goedkeuring.

Deze scheiding staat in de blauwdrukken en wordt gerespecteerd door alle nieuwe endpoints via `_require_admin` gates.

---

### MODULE 1 — 5W-Filler (680 lege kaarten)
**Backend**: `POST /api/kb/v2/curation/5w-suggest/{id}` + `POST /5w-apply/{id}`  
**UI**: `Spark AI → Spark Brain → Groeien → KB-Curatie Suite → 5W-Filler`

**Executie-stappen**:
1. Filter op "alleen volledig lege 5W" (680 kaarten)
2. Sorteer op alfabetisch begrip; werk in batches van 20
3. Per kaart: klik "LLM vullen" → Spark stelt 6 velden voor
4. Review-modal: alle velden bewerkbaar, Willem past aan waar nodig
5. Accept → kaart wordt bijgewerkt + `curation_history` logged

**Zones**:
- 🤖 **Spark autonoom**: LLM-voorstel genereren (geen mutatie), lagen1-4 lezen voor context, tags scannen voor domein
- 👤 **Willem beslist**: elk voorstel individueel accepteren/bewerken/skippen. Geen bulk-accept.

**Deadline-schatting**: 680 kaarten × 30 sec review = ~5.5 uur. In 3 sessies van 2u haalbaar.

---

### MODULE 2 — Duplicate-Merger (32 paren)
**Backend**: `POST /api/kb/v2/curation/duplicate-merge`  
**UI**: `KB-Curatie Suite → Duplicaten`

**Prioriteit-volgorde**:
1. **Rood-flag (same-lade)**: 4 pure duplicaten eerst (`vroeg`, `ai-kunst`, `periodiek systeem`, ...)
2. **Cross-lade dupes**: check of het echte homoniemen zijn (bv. `drift` = drijven vs verlangen → beide houden) of migratie-fout
3. **Merge**: kies keeper met meest 5W-gevuld + meest verbanden → drop wordt weggegooid, tags/5W-gaten migreren

**Zones**:
- 🤖 **Spark autonoom**: identificatie duplicaten, samenvattings-diff tussen paren tonen
- 👤 **Willem beslist**: keeper-selectie. Bij echte homoniemen: één van beide begrip hernoemen zodat ze niet meer botsen.

**Deadline**: 32 paren × 1 min beslissing = ~35 min. Klaar in één sessie.

---

### MODULE 3 — Lade-Reclassificatie (~200-300 echte gevallen uit 695 voorstellen)
**Backend**: `GET /api/kb/v2/curation/lade-check` + `POST /lade-move/{id}`  
**UI**: `KB-Curatie Suite → Lade-check`  
**Blauwdruk-anker**: `spark_tag_curatie_public.json § 8_lade_toewijzing_regels`

**Executie-stappen**:
1. Scan geeft 695 voorstellen — waarvan ~400 vals-positief (zn-meervoud zoals `Begrippen`, `Aandelen`, `Structuren` — géén werkwoord)
2. **Vaste patroon-skips**: zn-meervoud eindigend op -en van zn-enkelvoud (`begrippen` = mv van `begrip`)
3. **Vaste patroon-accepts**: infinitief werkwoorden (`lopen`, `denken`, `benoemen`)
4. Skip zn-meervoud, Accept werkwoorden

**Zones**:
- 🤖 **Spark autonoom**: Regel 1 + 2 uitvoering, voorstel-generatie, patroon-detectie
- 👤 **Willem beslist**: Skip/Accept per voorstel. Bij twijfelgevallen (`spreken` als zn "het spreken" vs werkwoord `spreken`) → Willem oordeelt.

**Sessie 55 open vraag**: `_KNOWN_ZN_OP_EN_EXTENDED` uitbreiden zodra Willem patroon-groepen tegenkomt (bijv. alle zn eindigend op `-heden` = zn-meervoud, automatisch skippen backend-side).

---

### MODULE 4 — Vier Werelden integratie (Willem's nieuwe Bijbel-kaarten)
**Kaarten**: Wonderland (creatief onderzoek), Neverland (herinnering/opzoeken), Mirrorland (reflectie), Crossroads (keuze-ordening)  
**Doel**: Spark herkent deze werelden als **intent-hooks** in chat en gedraagt zich per wereld anders.

**Executie-stappen**:
1. **Chat intent-detectie**: nieuwe module `wereld_intent_service.py` — detecteert "Wonderland/Neverland/Mirrorland/Crossroads" (en synoniemen: "creatief onderzoek", "herinner je nog", "even reflecteren", "welke keuze")
2. **Response-modus per wereld**:
   - Wonderland → LLM temperature 0.8 (creatief), explorerende follow-ups
   - Neverland → KB-lookup prioriteit (rag over chat-log + KB), lage temperature 0.2
   - Mirrorland → reflectieve toon, samenvatting van eerdere uitspraken
   - Crossroads → Spark stelt keuze-lijst op maar kiest zelf NIET (autonomie-grens!)
3. **Blauwdruk toevoegen**: `spark_werelden_public.json` — zelfde patroon als groeien/tag-curatie

**Zones**:
- 🤖 **Spark autonoom**: wereld herkennen, response-modus schakelen, follow-up vragen formuleren
- 👤 **Willem beslist**: bij Crossroads NOOIT beslissen namens Willem. Alleen keuzes ordenen.
- 🛡️ **Harde grens**: Wonderland-creativiteit mag geen KB-mutaties triggeren. Alleen chat-space fantasie.

**Effort**: ~30 credits (nieuwe intent-module + blauwdruk + 4-manier LLM-tuning).

---

### MODULE 5 — Bulk Vocab-approve top-100 (klein maar zichtbaar)
**Backend**: bestaat al — `POST /api/spark/vocab/approve-growth`  
**UI**: bulk-checkbox "selecteer top-100" in bestaande Groeien → Vocab-tab

**Executie-stappen**:
1. Fetch top-100 van `vocab-from-knowledge`
2. Selecteer all
3. Klik goedkeuren → 5963 → 6063 vocab-woorden

**Zones**:
- 🤖 **Spark autonoom**: kandidaten scoren op frequentie
- 👤 **Willem beslist**: één bulk-accept, want elk woord komt 100+× in KB voor = impliciete endorsement

**Effort**: ~15 credits (alleen "selecteer all"-knop toevoegen).

---

### MODULE 6 — Graph-vulling beslissing (nadat KB schoon is)
**Doel**: Los de "broken belofte" van weeskaart-check op.  
**Voorstel**: nadat 5W-Filler + Dupe-Merger + Lade-Reclassificatie klaar zijn (KB is schoon), migreer alle KB-kaarten naar `graph/nodes.json` als knowledge-nodes met tag-relaties als edges.

**Zones**:
- 🤖 **Spark autonoom**: migratie-script draaien, statistieken teruggeven
- 👤 **Willem beslist**: knop indrukken om te starten. Rollback beschikbaar via backup.

**Effort**: ~40 credits. Kan naar Sessie 56 als 55 vol raakt.

---

### MODULE 7 — Inbox subtab "Onvolledig" ✅ DONE (sessie 52a, feb 2026)
**Doel**: 680 lege-5W kaarten zichtbaar maken in bestaande Inbox-tab i.p.v. nieuwe top-tab.  
**Anker**: `knowledge/_meta.json § kaart_veldsemantiek.incompleet_criterium.toon_in_ui`

**Status**: Geïmplementeerd én geïntegreerd in de sort-dropdown flow. `KennisbankV2Page` toont Onvolledig als filter binnen de Inbox-grid met sort-support. Zie CHANGELOG sessie 52a.

**Executie-stappen** (referentie, gedaan):
1. ~~Backend: `/api/kb/v2/inbox` endpoint krijgt optionele `?filter=incomplete` param~~
2. ~~Filter-logica hergebruikt `incompleet_criterium.checks` uit meta (7 regels)~~
3. ~~Frontend `KennisbankV2Page.js`: subtabs + sort-dropdown~~
4. ~~Klik op subtab → herlaadt met andere query-param~~

**Zones**:
- 🤖 **Spark autonoom**: incompleet-detectie via meta-regels
- 👤 **Willem beslist**: aanpak per kaart (invullen via 5W-Filler of manueel bewerken)

**Effort**: ~15 credits.

---

### MODULE 8 — Refine-endpoint per veld (chirurgische verbetering)
**Doel**: Willem kan Spark chirurgisch vragen "verbeter alleen laag3" i.p.v. hele kaart opnieuw.  
**Anker**: `knowledge/_meta.json § kaart_veldsemantiek.lagen.laag3` (of ws5.wat/waarom/etc.)

**Nieuw endpoint**: `POST /api/kb/v2/card/{id}/refine?field=laag3`  
**Flow**:
1. Lees kaart + veld-definitie uit meta (doel/toon/verboden)
2. Bouw LLM-prompt: "Verbeter alleen `field` volgens deze regels: `{doel}`, toon `{toon}`, vermijd `{verboden}`. Behoud alle andere velden."
3. Return voorstel voor review (draft, geen mutatie)
4. Willem accepteert → veld wordt bijgewerkt, curation_history logged

**UI-integratie**: 
- KennisbankV2Page → kaart-detail-view → klein potlood-icoontje per veld
- Klik → LLM voorstel modal → Accept/Cancel

**Zones**:
- 🤖 **Spark autonoom**: LLM-voorstel op basis van meta-regels
- 👤 **Willem beslist**: accept per veld, geen bulk

**Effort**: ~25 credits. Bouwt exact op de veld-semantiek die vandaag is vastgelegd — zonder die meta zou dit niet werken.

---

### 📊 Sessie 55 SLA (bijgewerkt)
- **Verwacht kredietverbruik**: ~130-160 credits (KB-Curatie executie + Werelden-module + vocab-bulk + inbox-subtab + refine-endpoint)
- **Minimaal resultaat**: 680 lege 5W ingevuld met scherpe LLM-voorstellen (dankzij nieuwe meta-regels) + 32 dupes weg + ~200 lade-fouten gecorrigeerd + Werelden werken in chat
- **Ideaal resultaat**: bovenstaand + Graph gevuld + top-100 vocab live + refine-per-veld werkend + inbox-subtab zichtbaar
- **Reserve-post**: Sessie 56 voor Graph-vulling als Sessie 55 vol raakt

### 🚦 Redeploy-checkpoint (nu)
Alles wat hierboven staat DRAAIT AL in preview:
- ✅ KB-Curatie Suite (backend + UI)
- ✅ `knowledge/_meta.json` schema v1.1 met veld-semantiek (130 regels definitie)
- ✅ 5W-Filler LLM-prompt leest de nieuwe veld-regels
- ✅ Blauwdrukken groeien + tag-curatie
- ✅ Vier Werelden Bijbel-kaarten
- ✅ Agenda intent-splitter, admin-toggle audit, chat-visibility toggles, shop-owner permissies + user-container foto's

Backup gemaakt: `/app/_backup_before_prod_merge_20260803_071830/`

---

## 🧠 Spark's brein — wat er AL is (v5-status, 2026-05-23)

> Deze sectie bestaat omdat de backlog hieronder anders de indruk wekt dat Spark
> nog hersenloos is. Hij is dat niet. Hij denkt al laagsgewijs mee — onderstaande
> modules zijn live en in productie:

### 🎯 5-laags AI-pipeline (in volgorde bij elk chat-bericht)
1. **Safe-word laag** (`chat/routes.py`) — universeel `stop`/`pauze`/`klaar` wist alle pending state, vóór elke andere verwerking.
2. **Identity & Action intents** (`identity_intent_service.py`, `action_intents_service.py`) — "wie ben je?", "wat kan je?", "verwijder mijn account" e.d. eerst.
3. **Smart intents heuristic** (`smart_intents_service.py`) — help / suggest / community-recap / dnd-help / legal / time / credits + Boekhouder/Madelief/Mr Smith barks.
4. **Snap & NLP service** (`snap_service.py`) — meerlaags KB-lookup met homoniem-disambiguatie, compositional reasoning (`compositional_service.py`), stem-fallback en auto-zin-snap.
5. **Fallback service** (`fallback_service.py` + `#DeWillem` graceful) — als er geen directe hit is, kiest Spark een buurkaart uit de KB v2 lade en stelt voor het concept apart te leren in plaats van "weet ik niet" te zeggen.

### 🔭 Observability & shadow-leren
- **`@traced` decorator** (`modules/core/spark_logger.py`) — pre/post/error logs met `duration_ms` per gedecoreerde route, JSON Lines per module, 28-dagen retentie.
- **Shadow observer** (`chat/shadow_observer.py`) — registreert elk chat-event + correction-examples voor toekomstige zelf-tuning.
- **Behavior tracker** (`modules/behavior_tracker.py`) — telt gedragingen (`help_msg`, `kb_create`, `lie_detected`, `used_safeword`, etc.) — voedt het D&D aura-systeem.

### 🧩 Specialized services (allemaal live, in chat-flow hooked)
- **`emotion_service.py`** — emotie-detectie per bericht (input voor Madelief barks).
- **`time_intent_service.py`** + `user_time_service.py` — "hoe laat is het?" met tijdzone-resolutie per user.
- **`agenda_intent_service.py`** — natuurlijke afspraken parsen ("vrijdag 14:00 lunch met Tineke").
- **`wedervraag_service.py`** — als info ontbreekt, vraagt Spark gericht door (5W+H flow).
- **`scan_service.py`** + `spontaneous_w_service.py` — woorden in lopende zin worden stilletjes geanalyseerd voor 5W-aanvulling.
- **`session_state.py`** — 2-min ephemeral state (laatste vraag, pending card) per user-session.
- **`card_session_service.py`** — actieve KB-kaart-edit-flow door chat.
- **`relation_extraction_service.py`** — patterns als "Ron is mijn vriend" → relatie-graph auto-update.
- **`bijbel_lookup_service.py`** — externe lookup voor Bijbel-citaten.
- **`spark_self_service.py`** — Spark's eigen scratch.json: "onthoud voor jezelf", "wat heb je vandaag geleerd?".
- **`dank_service.py`** + `legal_service.py` + `personal_docs_service.py` — credits/privacy/voorwaarden/testament/survivalgids intents.
- **`intent_matcher_service.py`** — capability-matcher die Spark's *handen* moet gaan koppelen aan acties (P0 backlog: live-routering nog te maken).

### 🗂️ Kennis-architectuur (4 lagen)
- **v1 Knowledge Base** (`/data/knowledge/learned_knowledge/knowledge_base.json`) — legacy, alleen-lezen fallback.
- **KB v2 — 5 lades** (`/data/knowledge/v2/`, stand 17-09-2026) — 🌸 Voelen 566 · 💬 Spreken 516 · 🧠 Weten 5096 · 🎭 Doen 1153 · 🎮 Spark Games 12 + 📥 Inbox 1 (`rna`, Willem vult in).
  Lade-lijst is de bron `service.LADES` + `LADE_META`; frontend `KennisbankV2Page.LADES` moet gelijk lopen.
- **Knowledge graph** (`modules/graph/sync_service.py`) — 10577 nodes + 65981 edges (v1+v2 gemengd, lade-kleuren).
- **Voice/Image media** — centraal in `system_archive` met `linked_card_id` backreference.

### 🎮 Spark World (sandbox-game) — universele naam sinds 17-09-2026
- **Eén game, één naam**: D&D / dnd / d&d / "Levende Wereld" = **Spark World**. Gebruik nooit meer "D&D" als naam voor de game (alleen als tag-historie in `footnote.hernoemd_van`).
- **KB**: hub-kaart `Spark World` (kbv2-5ae16b66) in lade `games`, Base Line = basiswaarden-kaart, Rugzak, Utrecht (Spark World), grondstof-drafts. Veld `game: "spark world"` per kaart voor onderverdeling per game.
- **Data**: `data/dnd/` container (steden, fracties, characters, blueprints, world_state, lore_index). Status: **geparkeerd tot Core klaar is**.
- **Steen Papier Schaar** = onafhankelijke module-game (kaart in doen), cross-linkbaar als gevechtsmechaniek in Spark World.
- **Lore index** (7 avatars-as-functions, 6 behavior-categorieën) — gearchiveerd, oude oorsprongs-lore van Base Line staat hier.
- **Aura-engine** (`/api/dnd/aura/{user_id}`) — live top-3 gedragingen → kleur-gradient op Persoonskaart.
- **Card Factory** (`modules/cards/`) — DnD/Event/Bark kaarten met hook-chain bij draft→active.
- **Base Line intro** (community chat `[start verhaal]`) — keuze-driven story-flow.

### 🎙️ Stem-laag

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
