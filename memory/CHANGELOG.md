# Spark Core 2.0 — CHANGELOG

## 2026-10-19 — TTSS/GTSS, inspraak-filter, diep-modus relaties, Merch-tab weg
- `ttss aan/uit`: Spark spreekt met Willems eigen ingesproken KB-kaarten (`media.voice_url`), ontbrekende woorden worden stil overgeslagen (geen OpenAI-terugval). `gtss aan/uit` = placeholder voor kaart-geluiden (`media.extra_audio`).
- Nieuwe routes `GET /api/kb/v2/voice/map` en `/voice/missing` (`modules/kb_v2/voice_routes.py`).
- Kennisbank: 🎙️ "niet ingesproken"-filter per lade met teller (niet in Inbox).
- BUGFIX diep-modus (`/api/spark/compose`) sloeg relaties/personalia niet op — nu wel (Maaike-bug). Oude uitspraken van Maaike zijn niet met terugwerkende kracht opgeslagen.
- Roadkill Merch-tab verwijderd uit Beheer → Archief → Foto (blijft in Workspace → Winkel).
- Testartefacten opgeruimd; alle 7353 lade-kaarten ≥5 tags.
- Kennisbank-tab **In te spreken**: alle lades, lade-chips met tellers, kaart verdwijnt na inspreken + auto-volgende. GELUID-opnames tellen niet als inspraak. Merch: resterende dode code uit `SystemArchive.js`.
- Procesregel `RULE_toets_voor_bouw_001`: eerst bestaand onderzoeken + afstemmen, dan pas bouwen.

## 2026-09-17 — KB-opschoning + 5e lade "Spark Games"
- Orphan-skeletons opgeruimd: `voelenbegrip` (foute tag op 3 kaarten), `dnd` (legacy `v2/inbox.json` verplaatst). `rna` blijft (Willem vult in).
- Nieuwe KB-lade `games` = 🎮 Spark Games (backend + UI-tab + graph-kleur). Orphan-scan slaat de lade over.
- Universele game-naam **Spark World**: kaart D&D → hub-kaart Spark World; Base Line → basiswaarden-kaart; Utrecht (Spark World); 8 grondstof-drafts. Tags d&d/dnd → `spark world`.
- Steen Papier Schaar blijft in doen, gecrosslinkt met Spark World.
- Index + graph herbouwd. Lint-fix `t1` scope in GesprekkenPage.
- Fictie-gate: games-kaarten alleen in antwoorden bij game-context (`is_game_context`); ambient services zien ze niet.
- Bigram-snap: meerwoordige begrippen ('spark world', 'base line') matchen nu in chat.
- BUGFIX chat 500 (`ChatMessage` velden losgekoppeld door ResponseTimeLog-insert).
- **Verbindingen-kader** (`modules/connections`, Kladblok-widget): alle externe koppelingen op één plek, `connections.json` wint van `.env`, test-knop per verbinding. Voorbereiding Spark op Odroid.
- BUGFIX chat-lookup dood sinds 23 aug: losse `return response` in agenda-branch verwijderd — kennisvragen werken weer.


Datums = wanneer de implementatie afgerond is. Nieuwste bovenaan.

## 2026-02-26 (sessie 56b, deel 3) — Multi-book Uren + Clienten per kasboek

**Willem's verzoek**: "urenstaten + clienten horen niet als aparte modules, per
kasboek. Zorg krijgt zorg-dossier, shop krijgt klant-facturatie. Ieder zijn eigen
books (admin ziet default eigen, cross-user via Beheer → Gebruikers later)."

### 🏗️ v13d_multi_book_uren_clienten_001

**Sidebar cleanup**:
- Urenstaat + Clienten weggehaald uit MODULES top-level nav (leven nu per book)
- Routes `/modules/uren-rapport` en `/modules/clienten` blijven bestaan als deeplinks

**Backend clienten uitgebreid** (`modules/clienten/routes.py`):
- `book_id` veld — koppel client aan boek
- `client_type` — 'zorgclient' | 'klant' | 'generiek' (book-type-aware)
- Zorg-placeholder-velden: `geboortedatum`, `bsn`, `zorgindicatie`, `huisarts`, `noodcontact`
- Klant-placeholder-velden: `factuur_adres`, `betalingstermijn_dagen`
- `GET /list/{user_id}?book_id=X` — filter per book
- `GET /index/{user_id}?book_id=X` — compacte lijst per book

**Uren-rapport per book** (`GET /api/agenda/uren-rapport/{user}?book_id=X`):
- Filtert zakelijke events waarbij `opdrachtgever` matcht met client uit dat book
- Rest van API onveranderd (backwards compat)

**BookDetailBark 2 nieuwe sub-tabs** (`BoekhoudingBoekenTab.js`):
- 📊 **Uren** — periode-picker (dag/week/maand/jaar), samenvatting per opdrachtgever,
  CSV-export, per book gefilterd; ◀ ▶ periode-navigatie
- 💼 **Clienten** — book-type-aware label ("Zorgcliënt" / "Klant" / "Client"),
  create-form + lijst; book-color doorgetrokken

**Admin-view fix** (`modules/boekhouder/books_routes.py`):
- Admin ziet default alleen eigen books (was: alle books)
- `?target_user_id=X` cross-user access voor admin (voor Beheer → Gebruikers)
- Live geverifieerd: Willem 4 books, Heidi 2, Marieke 2

**Data-cleanup**:
- 3× ghost TEST_ books opgeruimd uit preview (TEST_CloseMe/PatchShop/AdminShop)
- Pytest teardown fixture toegevoegd (`test_winkelstraat_p1p4.py`) → autouse module-scope,
  ruimt alle books met naam-prefix TEST_ na test-run

**Live geverifieerd**:
- Client aangemaakt bij Zorgboerderij (client_type=zorgclient, zorgindicatie ingevuld)
- Client aangemaakt bij Roadkillshop (client_type=klant, betalingstermijn 30 dagen)
- Uren-rapport augustus 2026: 9.5u totaal, Jeroen 8u + Roline 1.5u


## 2026-02-25 (sessie 56b, deel 2) — Clienten-module + Uren-rapport page (voorloper)

**Nieuwe module `clienten`** (backend + frontend, later gemigreerd naar per-book):
- Aparte module (niet persons — persons = familie met D&D)
- Dossier-entries (kop+inhoud+bron)
- `POST /clienten/learning/` — Spark kan geleerde info wegschrijven per client

**Nieuwe uren-rapport page** (`UrenRapportPage.js`, later verhuisd naar BookDetail):
- Endpoint `GET /api/agenda/uren-rapport/{user}?period=dag|week|maand|jaar`
- Per-opdrachtgever aggregatie
- CSV-export


## 2026-02-25 (sessie 56b, deel 1) — Chat terugblik + notes scope + taken doelen

**Agenda-terugblik hook** (`v13d_agenda_terugblik_001`):
- Nieuwe capability `agenda_terugblik` in `capability_handler_service.py`
- Detecteert periode: gisteren/eergisteren/vandaag/deze week/vorige week/deze maand/vorige maand
- Aggregatie per opdrachtgever bij zakelijke events + uren-vraag
- Early-hooks in chat/routes.py laten "gedaan/gewerkt/uren" door naar capability router
- Live geverifieerd: "hoeveel uur heb ik gewerkt deze week" → 9.5u
- 7/7 pytest groen (`test_agenda_terugblik_v13d.py`)

**Notities/Dagboek terugblik-hooks** (`v13d_notities_terugblik_001`, `dagboek_terugblik_001`):
- "hoeveel notities in augustus" → 2 stuks
- "wat is mijn laatste notitie" → volledige inhoud + scope-badge
- "wat schreef ik gisteren in mijn dagboek"
- Admin-notes uitgesloten (die leven in Kladblok)
- 11/11 pytest groen (`test_notities_dagboek_terugblik_v13d.py`)

**Notes scope-veld** (`v13d_notes_scope_001`):
- Backend `NoteCreate` / `TaskCreate`: `scope` prive|zakelijk|admin (default prive)
- Frontend: 3-way toggle in nieuw-formulier (Admin alleen voor admins)
- Admin-notes verborgen uit reguliere pagina → **AdminNotesWidget** in Kladblok
- Item-cards krijgen 💼 Zakelijk badge
- Term "werk" → "zakelijk" (consistent met agenda)

**Taken = doelen** (`v13d_task_doel_001`):
- Task-model uitgebreid: `begin_datum`, `eind_datum`, `budget_uren`, `opdrachtgever`, `onderwerp`
- Frontend: 3 datum/budget velden bij Taak-mode, zakelijk-velden bij scope=zakelijk
- Task-cards krijgen secondary-color badges voor periode/budget (`var(--app-secondary)`)
- Alles-tab toont notes + tasks gemixed


## 2026-02-25 (sessie 56b, deel 0) — Widget Kladblok migraties + Alert-kleur

**Dashboard → Kladblok** (`v13d_dashboard_kladblok_migratie_001`):
- `ShadowObserverWidget` + `PerformanceWidget` verplaatst uit DashboardPage
- Registreerd in `admin/sandbox/registry.js` met meta-info
- Dashboard opgeschoond: ~173 regels inline code + 3 state-hooks + 3 fetches weg

**Notities → Kladblok**:
- `BugsListWidget`: Bugs-tab verplaatst uit Notities & Taken → eigen widget met fetch/status/bulk-close
- `DeployWidget`: Deploy-tab verplaatst → dunne wrapper rond `DeployAnchorPanel`
- Knop-volgorde in Notities: +Nieuw eerst, dan Bug melden (icoon weg → kleiner)

**App Kleurenschema uitgebreid** (`v13d_app_alert_color_001`):
- 4de kleur "Alert / Error" naast Primary/Secondary/Background
- Nieuwe backend-key `app_alert_color`, App.js past `--alert-base` toe bij startup
- Bug melden-knop nu gekoppeld aan `var(--alert-base)` — verandert mee met schema

**Theming**:
- Agenda, Dagboek, Notities: alle blauw/pink/amber accenten vervangen door `var(--glow-base)`
- Semantische kleuren behouden (mood-badges, done=green, delete=alert)



## 2026-02-25 (sessie 56b) — Agenda: Privé/Zakelijk + Uren-registratie

**Willem's verzoek**: "kies privé/zakelijk, begin/eind tijd, bij zakelijk pauze +
opdrachtgever + onderwerp voor uren-registratie. Later kunnen we dit door een
agent laten verwerken."

### 🗓️ v13d_agenda_uren_registratie_001

**Backend** (`modules/agenda/routes.py`):
- `EventCreate` / `EventUpdate` uitgebreid met: `scope` ('prive'|'zakelijk'),
  `end_date`, `pauze_minuten`, `opdrachtgever`, `onderwerp`, `product_code`
- `_compute_totaal_uren()` — server berekent uren = (end - start) - pauze
- Bij scope=prive worden zakelijk-velden genegeerd (guard)
- PUT herbetekent totaal_uren wanneer relevante velden wijzigen
- Backwards compat: bestaande events zonder scope tonen als 'prive'

**Frontend** (`workspace/AgendaPage.js`):
- Privé/Zakelijk toggle bovenaan formulier (data-testid `scope-prive-btn` /
  `scope-zakelijk-btn`)
- Start + eind tijd (i.p.v. losse `time`)
- Bij zakelijk: Opdrachtgever · Onderwerp · Pauze (min) velden
- Live berekende uren-badge tijdens invoeren (data-testid `computed-uren`)
- Event-cards krijgen amber-tint + "Zakelijk"-badge + toon opdrachtgever/uren

**Spark chat-parser** (`modules/chat/agenda_intent_service.py`):
- Nieuwe `_extract_zakelijk_fields()` detecteert trefwoorden 'zakelijk', 'werk',
  'gewerkt', 'klus', 'opdracht', 'factureer', 'declaratie'
- Extract opdrachtgever via 'voor <Naam>'
- Extract pauze via 'met een uur pauze' / '30 min pauze'
- `detect_agenda_intent()` return dict bevat nu scope/opdrachtgever/pauze_minuten

**Chat-write hooks** (`compose_routes.py` + `chat/routes.py`):
- Beide flows schrijven nieuwe velden naar agenda-JSON en berekenen totaal_uren

**Tests**: `tests/test_agenda_scope_v13d.py` — 7/7 groen (backwards-compat prive,
zakelijk full, geen end_date, guard prive, PUT herberekening, chat-scope
detectie, chat-prive default).

**Geverifieerd**: lint ✅ backend + frontend, screenshot toont "7.5 uur netto"
badge bij 09:00-17:00 met 30 min pauze.



## 2026-02-25 (sessie 56b) — Dashboard opschonen: Shadow Observer + Performance → Widget Kladblok

**Willem's verzoek**: "deze 2 kaders in dashboard (Shadow Observer + Performance)
wil ik verplaatsen naar Widget Kladblok, niet sandbox — dat is wat anders voor
testen, dit is verzamel-sandbox tot betere plek".

### 🧹 v13d_dashboard_kladblok_migratie_001

**Verplaatst**:
- `ShadowObserverWidget` (live chat-events, correcties, top-triggers, unused)
- `PerformanceWidget` (storage-cache stats, cache leegmaken)

Beide widgets zijn zelfstandig (eigen fetch, eigen state) in
`components/admin/sandbox/widgets/` en geregistreerd in `sandbox/registry.js`
met meta-info (doel, waar-hoort-het, aangemaakt-op, reden).

**Dashboard opgeschoond**: fetches naar `/api/chat/shadow/stats`,
`/api/chat/shadow/unused` en `/api/admin/storage-cache` verwijderd uit
`DashboardPage.js`. State (`shadowStats`, `shadowUnused`, `perfStats`) weg.
`ShadowCard`, `PerfCard`, `ShadowStat`, `UnusedRow` inline-functies (~173 regels)
verwijderd. Ongebruikte imports (`Eye`, `Gauge`) opgeruimd.

**Geverifieerd**: lint ✅, dashboard clean ✅, kladblok toont beide widgets ✅
(data-testid `kladblok-item-shadow-observer` + `kladblok-item-performance`).




## 2026-02-24 (sessie 56) — Eco-container per user + template-spawn

**Willem's principe** (kernbeslissing sessie 56): "iedere gebruiker is een eigen
ID en eco-container". Nieuwe users moeten automatisch dezelfde skeleton krijgen
zodat het nooit stuk kan door ontbrekende data.

### 🏠 v13d_user_container_001 — Auto-spawn template per user

**Nieuw** — `modules/core/user_container.py`:
- `ensure_user_container(user_id)` — creëert skeleton-files voor: agenda,
  dagboek, persons (relaties), personalia (admin-view). Idempotent.
- `backfill_all_users()` — bulk-run voor bestaande users.

**Auto-hook**: `AuthService.create_user` roept `ensure_user_container` aan bij
elke nieuwe registratie. Nieuwe users hebben direct een werkende omgeving.

**Backfill uitgevoerd**: 20 van 21 bestaande users kregen hun ontbrekende
skeleton-files (user-000 = system, skipped). Vanaf nu: nooit meer stuk.

### 🔒 v13d_multi_module_privacy_001 — 4 open lekken dicht

**Willem's melding**: "user Gerben had mijn kasboek". Snuffel toonde dat 4
modules geen auth-check hadden op `GET /{user_id}`:
1. **Boekhouding**: `_is_admin` gaf True voor iedereen met `gradatie<=2`.
   G2 = familie, geen admin. Fix: alleen echte `admin`/`admin_capable` flags.
2. **Agenda**: `GET /events/{uid}` was open. Nu `require_access(viewer_id, uid)`.
3. **Dagboek**: idem. `require_access(viewer_id, uid)`.
4. **Notes/Tasks**: `GET ?user_id=X` was open. Nu viewer_id-check.
5. **Persons/Relaties**: `GET /cards/{uid}` was open. Nu viewer_id-check.

**Nieuwe helper** — `modules/core/privacy.py`:
```python
require_access(viewer_id, target_user_id)  # 403 als geen owner/admin
is_admin(user_id)  # alleen echte admin-flags, geen gradatie-check
```

### 👤 v13d_boekhouder_auto_prive_001 — Auto-privé-book per user

Bij eerste GET `/api/boekhouding/books` autocreate `type=user_prive` book
als user nog geen heeft. Idempotent. Shop-books via bestaande hook.

**Tests**: 22/22 groen
- `test_boekhouder_privacy_v13d.py` (5×)
- `test_eco_container_privacy_v13d.py` (12×)
- `test_agenda_delete_v13d.py` (9×) — bestaand, nog steeds groen

**Impact live-versie na deploy**:
- Alle 20 non-admin users: geen cross-user leaks meer in 5 modules
- Nieuwe users krijgen automatisch werkende eco-container
- Backwards-compat: bestaande frontend-calls zonder viewer_id blijven werken


## 2026-02-24 (sessie 56) — Boekhouder privacy-lek + auto-privé-book + eco-container-fix

### 🔒 v13d_multi_module_privacy_001 — Eco-container per user (kritieke lek)

**Willem's melding**: "user Gerben had mijn kasboek". Snuffel toonde 4 open lekken:
1. `boekhouding/books` — Gerben (G2) zag alle 7 Willem's boeken
2. `agenda/events/{user_id}` — geen auth-check, iedereen ziet iedereens events
3. `dagboek/entries/{user_id}` — idem, dagboek volledig open
4. `notes/all` + `notes/tasks` — idem via `?user_id=X`

**Root cause #1 (boekhouder)**: `_is_admin(user_id)` gaf True voor iedereen met
`gradatie <= 2`. G2 = familie, geen admin. Fix: alleen echte `admin`/`admin_capable`
flags tellen.

**Root cause #2 (agenda/dagboek/notes)**: geen viewer_id-check op de path/query
user_id. Nieuwe helper `modules/core/privacy.py`:
```python
require_access(viewer_id, target_user_id)  # 403 als geen owner/admin
```

**Fix in 4 endpoints**: `viewer_id` optionele query-param. Als afwezig → fallback
op user_id (backwards-compat). Als aanwezig én niet-owner én niet-admin → 403.

### 👤 v13d_boekhouder_auto_prive_001 — Auto-privé-book per user

**Willem's logica**: "iedere gebruiker moet in zijn omgeving zijn eigen
boekhouding en als ze zelf een winkel beginnen dan de winkel meenemen".

**Fix**: bij eerste GET `/api/boekhouding/books` autocreate privé-book
(`type=user_prive`, icoon 👤, kleur groen). Idempotent. Shop-books gaan al via
bestaande `ensure_shop_book` hook.

**Tests**: 17/17 groen (`test_boekhouder_privacy_v13d.py` 5× + `test_eco_container_privacy_v13d.py` 12×).

**Impact live-versie na deploy**:
- Alle 20 non-admin users zien nu alleen eigen data (agenda/dagboek/notes/books)
- Elke user krijgt automatisch eigen kasboek bij eerste bezoek
- Backwards-compat: bestaande frontend-calls zonder viewer_id blijven werken


## 2026-02-24 (sessie 56) — Boekhouder privacy-lek + auto-privé-book

### 🔒 v13d_boekhouder_admin_leak_001 — Kritieke privacy-lek

**Willem's melding**: "user Gerben had mijn kasboek in boekhouden". Onderzoek
bevestigde: Gerben (G2, familie) zag alle 7 boeken van Willem incl. Zorgboerderij,
Roadkillshop, Willem-privé.

**Root cause** — `modules/boekhouder/books_routes.py` line 36:
```python
return u.get("admin") is True or (u.get("gradatie") or 99) <= 2
```
De gradatie-check behandelde **iedereen ≤ G2 als admin**. G1 = admin (correct),
maar G2 = familie (fout). Gerben, Lotus, Heidi, Nick, Marieke (G2/G3) werden
onterecht als admin behandeld → volledige toegang tot alle books.

**Fix**: `_is_admin` kijkt nu alleen naar `admin` en `admin_capable` flags,
niet naar gradatie. Regressietests in `test_boekhouder_privacy_v13d.py` (5×).

### 👤 v13d_boekhouder_auto_prive_001 — Elke user eigen kasboek

**Willem's logica**: "iedere gebruiker moet in zijn omgeving zijn eigen boekhouding
en als ze zelf een winkel beginnen dan de winkel meenemen".

**Fix**: bij eerste GET `/api/boekhouding/books` wordt automatisch een privé-book
(`type=user_prive`, `owner_user_id=viewer_id`, icoon 👤, kleur groen) aangemaakt
als de user er nog geen heeft. Idempotent. Shop-books gaan al via bestaande
`ensure_shop_book` in `shop_hooks.py`.

**Impact**: Gerben ziet nu 2 boeken (Gerben-Privé + Spark Core), niet 7.
Marieke idem, Heidi idem. Alle 20 users krijgen bij inloggen automatisch hun
eigen eco-container.


## 2026-02-23 (sessie 55, deel 2) — Chat: "noem alle gebruikers" werkt nu

### 👥 v13d_gebruikers_namen_001 — Nieuwe capability

**Willem's productie-frustratie**: "ik wil alle usernamen opgenoemd hebben" → Spark had
wel `tellen_gebruikers` (aantal + eerste 8 namen) maar geen manier om **alle** namen te
noemen. Antwoord: "Ga naar de Admin-tab". Dezelfde bug-klasse als agenda-delete.

**Fix** — nieuwe capability `gebruikers_namen`:
- Handler `_handle_gebruikers_namen(user_id)` in `capability_handler_service.py`:
  - **Admin** (Willem, Spark) → volledige lijst gegroepeerd per gradatie (G1..G7).
  - **Non-admin** → alleen users op eigen gradatie of hoger (geen leak van familie-namen).
- 10 triggers in `spark_capabilities.json`: `noem alle gebruikers`, `gebruikerslijst`,
  `wie zit er op spark`, `geef me alle namen`, etc.
- 4 regressietests in `tests/test_gebruikers_namen_v13d.py` (varianten + admin-view +
  non-admin filter + geen-lek-familie-namen naar G7).

**Impact**: Willem's productie-scenario werkt nu. Elke Nederlander-frasering match.
Privacy blijft intact (Emmy G7 ziet alleen Emmy + GPT, geen Lotus/Heidi).

---

## 2026-02-23 (sessie 55) — Agenda DELETE hook + Intent Patronen live-editable + RULE_-prefix

Willem's frustratie: "als ik in chat zeg 'haal aanstaande dinsdag uit de agenda' dan
moet Spark dat doen, niet zeggen 'via de agenda-tab'." + "vind raar dat je die Triggers
tabs nooit bent gaan gebruiken." + Emmy: "v13 = Spark-versie, geen agent-regel." → dit fixt drie.

### 📜 RULE_-prefix voor agent-gedragsregels — Naamgevingsscheiding
**Probleem**: `v13_agent_selfcheck_001` verwart Willem: `v13_` is Spark feature-versie,
niet agent-gedrag. Bovendien stond de regel nergens formeel in code/memory → per sessie
kwijt.

**Fix** — `/app/memory/ROADMAP_CORE.md`:
- Nieuwe sectie bovenaan "🚨 AGENT GEDRAGSREGELS (RULE_*) — VERPLICHT LEZEN & OPVOLGEN"
- Regels geherformuleerd met `RULE_`-prefix (los van feature-versies):
  - `RULE_agent_selfcheck_001` — sessie-start protocol (lees CORE + CHANGELOG + grep vóór bouwen)
  - `RULE_dutch_only_001` — Nederlands antwoorden
  - `RULE_no_database_001` — strict JSON, geen DB
  - `RULE_deploy_preview_split_001` — preview vs productie
  - `RULE_no_placeholder_data_001` — geen mock/fake data
  - `RULE_footnote_metadata_001` — verplichte metadata per KB v2 kaart

Rationale: nu staan de regels prominent in de codebase, niet enkel in vluchtige
handoff-samenvattingen die per fork wegvallen.

### 🗓️ v13d_agenda_delete_001 — Chat-gestuurde agenda-DELETE flow
**Probleem**: DELETE-intent bestond niet; Spark antwoordde met "doe dat via de agenda-tab".

**Backend** — `smart_intents_service.py`:
- `detect_agenda_delete_intent(text)` matcht op "haal/verwijder/schrap/annuleer … uit de agenda".
- `handle_agenda_delete_start(user_id, user, text)` — vindt matching events:
  - **0 matches** → melding + hint om READ te vragen.
  - **1 match** → bevestigingsvraag met titel + datum/tijd, `pending_state` opgeslagen.
  - **>1 matches** → genummerde lijst (max 8), user kiest **1** of **alle**.
- `handle_agenda_delete_choose(pending, text)` — verwerkt nummer/alle keuze → 2e confirmatie.
- `execute_agenda_delete(user_id, event_ids)` — verwijdert events uit `/data/agenda/{uid}.json`.
- `handle_agenda_delete_cancel()` — bij "nee".

**Routes** — `chat/routes.py`:
- Early hook vóór capability-router: agenda_delete + agenda_read direct afvangen (voorheen
  vong "agenda_vandaag" capability alle agenda-woorden op → verkeerde antwoord).
- `pending_agenda_delete` handler binnen smart-intents blok (verplichte plek: block doet
  aan einde onvoorwaardelijke `return response` voor logged-in users, dus buiten dat blok
  onbereikbaar).

**Regressie fix bonus**: pre-bestaande test-failure "wat staat er morgen → capability_response
i.p.v. agenda_overview" is opgelost via de early-hook (test_agenda_weekday_no_emoji nu 13/13).

### 🎛️ v13d_intent_patterns_json_001 — Live-editable regex-intents (Triggers-tab)
**Probleem**: Intent-detectors (`smart_intents_service`, `action_intents_service`) hadden
regex-patronen hardcoded in Python. Willem kon in Triggers-tab wél trigger-woorden bewerken
maar géén regex-patronen voor intents → moest per commit-cycle wachten.

**Architectuur**:
- Nieuw module `/app/backend/modules/chat/intent_pattern_store.py`:
  - `BASELINE: Dict[str, List[str]]` — hardcoded fallback, niet-verwijderbaar (garantie:
    basisgedrag altijd werkend, ook bij lege/foute JSON).
  - `/app/backend/data/triggers/intent_patterns.json` — live-editable additions.
  - `match_any(intent_key, text)` runtime lookup = BASELINE ∪ JSON.
  - Cache met mtime-invalidation: JSON-edit werkt direct door.
  - Auto-bootstrap: als JSON niet bestaat, wordt hij aangemaakt met alle bekende intent-keys
    op empty-additions.

**Gemigreerd** (BASELINE bevat alle voormalige hardcoded lijsten):
- `agenda_read`, `agenda_delete` (nieuw), `note_create`, `bug_report`, `help_overview`,
  `suggest_action`, `topic_overview`, `clarify`, `community_recap`, `dnd_help`,
  `account_delete`, `stt_on`, `stt_off`, `tts_on`, `tts_off`, `ambient_off` = **16 intents,
  118 baseline-patronen**.

**API** — `triggers/routes.py`:
- `GET  /api/triggers/intent-patterns` — lijst met per-intent baseline + additions + counts.
- `POST /api/triggers/edit/intent/{key}/add`  body `{pattern}` — regex-toevoegen (met compile-validatie).
- `DELETE /api/triggers/edit/intent/{key}/pattern?pattern=...` — verwijderen (weigert baseline).
- `POST /api/triggers/intent-patterns/test?text=...` — preview welke intents matchen.

**UI** — `TriggersPage.js`:
- Nieuw uitklapbaar blok "Intent Patronen (regex)" onderaan de Triggers-tab.
- Per intent-key: baseline (locked, groen) + additions (deletable, amber) + regex-input
  met live compile-check via backend.
- Toont totalen in header: `X patronen in Y intents · Z live-toegevoegd`.

**Tests**: `tests/test_agenda_delete_v13d.py` — 9 tests (single/multi/alle/cancel flow +
regex-store CRUD + baseline-protection). Alle groen.

**Impact voor Willem**: 
1. Chat-commando "haal aanstaande dinsdag uit de agenda" werkt nu end-to-end zonder UI-omweg.
2. Nieuwe intent-patronen kunnen via Triggers-tab live worden toegevoegd zonder redeploy.


## 2026-02-22 (sessie 53 vervolg) — LLM Usage Tracker live

### 📊 v13_llm_usage_tracker_001 — /api/chat/llm/usage/today endpoint
Willem's LLM-token-widget was tot nu toe placeholder-data. Nu leest hij **echte** gebruikscijfers per provider per dag.

**Backend**:
- `_log_usage(provider, model, usage)` in `llm_router.py` schrijft naar `/data/llm/usage_YYYY-MM-DD.json` bij élke succesvolle call. Providers zonder token-info in de response (bv. Emergent SDK) krijgen alleen call-count.
- `get_usage_today()` returned per provider: `used`, `calls`, `limit`, `pct`, `tier`, `last_call`.
- Limits configureerbaar via env-vars `LLM_PRIMARY_TPD_LIMIT` (default 100000), `LLM_FALLBACK_TPD_LIMIT` (default null), `LLM_PRIMARY_TIER`, `LLM_FALLBACK_TIER`.
- Endpoint `GET /api/chat/llm/usage/today` in `routes.py`.

**Frontend** (`LlmTokenUsageWidget.js`):
- URL geswitched van placeholder `/api/llm/usage/today` naar echte `/api/chat/llm/usage/today`.
- Auto-refresh elke 30s zodat je live ziet wanneer een lijn vol raakt.
- Placeholder-tekst vervangen door status-hint: *"Live-data via /api/chat/llm/usage/today, auto-refresh 30s. Limits configureerbaar via env LLM_*_TPD_LIMIT."*

**Live-verificatie preview**:
- Baseline: Groq 571 tokens, 1 call ✓
- Extra call via emergency-tier: Emergent +1 call gelogd (0 tokens want SDK ✓)
- Endpoint returned volledige provider-snapshot met pct-progressie ✓


## 2026-02-22 (sessie 53 vervolg) — Nood-nood emergency + vriendelijke budget-fout

### 🚨 v13_emergent_nood_nood_001 — Emergent alléén bij écht code-rood
Vorige tweak (default OFF) was té strikt. Willem zei letterlijk *"alleen nood nood"*, en dít is nood-nood: Groq TPD op + Cerebras quota op tegelijk → alles down.

**Nieuwe logic** in `llm_router.py`:
- `_try_emergent_emergency(..., true_emergency=bool)`
- `chat_complete` detecteert of *alle* gefaalde providers een quota/rate-limit/budget-error hadden. Zo ja → `true_emergency=True` → Emergent wordt gebruikt (ongeacht env-flag). Bij bv. netwerk-time-out of config-fout → Emergent blijft dicht.

**Quota-detector** matcht: `429`, `402`, `quota`, `rate_limit`, `rate limit`, `budget`, `tokens per day`, `tpd`, `insufficient`. 6/6 unit-tests groen (Groq TPD, Cerebras 402, Emergent budget = true; timeout, 404 = false).

### 🗣️ v13_llm_budget_user_message_001 — cryptische error → Nederlands verhaal
`Even iets mis: all_providers_failed` was voor Willem betekenisloos. Nu genereert `response_composer.py` een concrete Nederlandse zin per faal-categorie:

- **Alle 3 op quota** (Willem's productie-scenario, 22 feb): *"Mijn drie LLM-lijnen zijn vandaag allemaal over hun budget (Groq TPD vol, Cerebras quota op, Emergent budget op). Reset volgt vanzelf, óf vul één van deze bij: Emergent = Profile → Manage plan → Universal Key → Add Balance."*
- **Timeout**: *"Verbinding hapert even — probeer over een moment opnieuw."*
- **Andere**: *"Even iets mis met mijn taalmodel-lijnen. Ik geef 't door aan de admin (details staan in de logs)."*

Frontend `GesprekkenPage.js` gebruikt `d.message` als backend die zet, anders de generieke fallback.


## 2026-02-22 (sessie 53) — Chat-weergave-fixes (JSON-leak + HTML-error)

### 🧹 v13_tts_json_leak_sanitizer_001 — action/payload JSON-blokken weg uit chat
Spark begon soms ```json {"action": "tts_speak", "payload": {"text": "..."}} ``` te typen in plaats van gewoon te antwoorden. De bestaande tool-leak-sanitizer (v7) ving alleen `[tool_name {...}]` bracket-syntax, niet dit nieuwe JSON-blok-patroon.

**Fix** in `response_composer.py`:
- Detecteert zowel fenced (```json ... ```) als bare `{"action": ..., "payload": {...}}` blokken
- Als het blok een `payload.text` bevat → **extraheer die tekst** als antwoord (zo blijft Spark's bedoeling behouden)
- Anders → blok volledig strippen
- Bonus: `\n{3,}` → `\n\n` normalisatie voor cleane whitespace

**Getest** met Willem's twee originele voorbeelden:
- *"Jammer, ik hoor je. Wat kan ik doen om het beter te maken?"* → schone tekst ✓
- *"Ja, dat is best veel. Waar wil je dieper op ingaan?"* → schone tekst ✓
- Normale tekst blijft ongewijzigd ✓

### 🔌 v13_deep_response_guard_001 — HTML-error i.p.v. crash
Frontend deed onvoorwaardelijk `r.json()` op `/api/spark/compose`. Bij gateway-timeout (502/504) kwam er HTML terug → `Failed to execute 'json' on 'Response': Unexpected token '<'` in de chat.

**Fix** in `GesprekkenPage.js`:
- Check `content-type` header vóór `r.json()`
- Bij niet-JSON → toon Nederlandse fout: *"server had het even druk — probeer over een moment opnieuw"* (HTTP-5xx) of *"HTTP {status}"* (andere)
- Error-message opnieuw geformuleerd: *"Even geen verbinding — [reden]. Probeer het over een tel opnieuw."*


## 2026-02-22 (sessie 53 vervolg) — Login-dots rand-fade + Emergent default OFF + widget-labels

### 🎚️ v13_login_dots_fade_setting_001 — rand-fade slider werkt
Backend allowlist in `settings/routes.py` miste de key `login_dots_fade` waardoor de slider "Rand-fade (buiten zachter)" een `Onbekende setting 'login_dots_fade'`-fout gaf. Frontend + LoginForm gebruikten 'm al. Fix: toegevoegd aan SCHEMA met bereik `[0.0, 1.0]`. Value 0.3 succesvol opgeslagen + terug uitgelezen ✓.


## 2026-02-22 (sessie 53 vervolg) — Roles-array + productie ZIP-merge + LLM-diag fix

### 🐄 v13_roles_array_001 — Zorgboerderij foundation
Een persoon kan nu meerdere rollen tegelijk hebben (vriend + cliënt + medewerker) zonder dubbele entries. Fundament voor care-farm dossiers, hourly tracking en gedragingen die per rol verschillen.

**Wat is er gebouwd:**
- Elke entry in `/data/persons/{uid}_relationships.json` heeft nu een `roles: []` array naast bestaande `relation_type` (backwards-compat).
- `add_relations()` merged automatisch: persoon bestaat al met andere rol → nieuwe rol wordt geappend, geen dubbel-entry.
- Nieuwe rel_types onder `professioneel/…`: cliënt, klant, medewerker, werkgever, begeleider.
- Regex-patronen accepteren nu adverbia: "Roeline is **ook** mijn cliënt", "Roeline is **inmiddels** mijn medewerker".
- Helpers: `get_roles(uid, name)`, `has_role(uid, name, role)`, `add_role(uid, name, role)`. `has_role()` matcht zowel korte woord als volledige rel_type.
- `migrate_all_to_roles_array()` idempotent one-shot; ge-live gedraaid → 14 Willem-entries gemigreerd, 0 zonder roles.

**Regression-test** (`/app/backend/tests/test_roles_array_v13.py`, 7 tests groen):
- new person gets roles array
- second role appends not duplicates
- idempotent duplicate role
- has_role matches short + full
- add_role helper + idempotent
- migration preserves existing data
- migration idempotent

**Live-verificatie**:
```
Test 1: "Roeline is mijn vriendin"                    → roles: ['vriend']
Test 2: "Roeline is ook mijn cliënt sinds vorige week" → roles: ['vriend', 'professioneel/cliënt']
Test 3: "Roeline is inmiddels mijn medewerker"        → roles: ['vriend', 'professioneel/cliënt', 'professioneel/medewerker']
Test 4: idempotent (nogmaals cliënt) → geen wijziging ✓
```

### 📦 Productie ZIP-merge (spark_backup_changes_20260822_115856.zip)
- 2449 files gemerged: 4 nieuw + 2445 overschreven + 0 skipped/errors.
- Backup vóór merge: `/app/_backups/pre_merge_20260822_1205/backup.tgz`.

### 🩺 v13_llm_router_diagnostics_002 — env-hint fix
`_diagnose_missing_keys()` checkte oude namen (`LLM_A_API_KEY`, `LLM_B_API_KEY`) die niet meer bestaan. Nu de correcte `LLM_PRIMARY_API_KEY`, `LLM_PRIMARY_BASE_URL`, `LLM_PRIMARY_MODEL`, `LLM_FALLBACK_API_KEY`, `EMERGENT_LLM_KEY`.

### 🛠️ v13_model_alias_self_heal_001 — productie LLM zelfherstellend
Productie draaide nog op env-var `LLM_PRIMARY_MODEL=llama-3.3-70b-versatile` (door Groq gedeprecateerd 16-aug 2025 → elke call 404).

**Fix**: `_DEPRECATED_MODEL_ALIAS` map in `llm_router.py` swapt automatisch 4 bekende gedeprecateerde Groq-modellen naar `openai/gpt-oss-120b` bij `_get_provider()`. Waarschuwing in logs bij eerste substitutie. Modern model blijft onaangeraakt.

### 🚫 v13_emergent_default_off_001 — Emergent-key alleen op verzoek
Default omgedraaid van `true` naar `false`. Emergent Universal Key wordt nu alléén gebruikt als env-var `LLM_EMERGENCY_USE_EMERGENT=true` expliciet gezet is. Willem: *"alleen nood nood"*. Voorheen: default `true` → onbedoeld credits opgemaakt.

**Provider chain nu**:
```
1. Groq        → openai/gpt-oss-120b   (primary)
2. Cerebras    → gpt-oss-120b          (fallback)
3. Emergent    → default UIT           (alleen als env-var expliciet true)
```

### 🎨 Widget-label sync
`LlmTokenUsageWidget.js` toonde nog `Groq (llama-3.3-70b)` — placeholder ge-updated naar `Groq (openai/gpt-oss-120b)` + Cerebras krijgt naam-label + Emergent staat als `noodrem, default UIT`.

**Effect**: na redeploy werkt productie zonder dat env-vars aangepast hoeven te worden. Emergent-fallback verbruikt geen credits meer tenzij expliciet aangezet.

**Live-verificatie preview**:
- Deprecated env → swap-log + `openai/gpt-oss-120b` in provider config ✓
- Modern env → geen swap ✓
- Chat-call na fix → success via `primary/openai/gpt-oss-120b`, latency <2s ✓
- Provider chain check → 2 providers actief (Groq + Cerebras), Emergent uit ✓


## 2026-02-22 (sessie 53) — Trader Accounting Hygiene sprint

Systematische fix-batch geïnitieerd door Willem's "waarom staat er verlies terwijl ik alleen winst deed?". Elke stap onthulde volgende bug — resultaat: alle known gaps dicht, preventie voor nieuwe users, herbruikbare diagnose-scripts.

### 🔧 v13_pot_value_consistency_001 — TraderPage vs AnalyticsPage mismatch
€10.00 vs €10.26 verschil opgelost. Backend `/api/trade/potjes/{user_id}` overschreef `live_value` met dynamische token-prijs voor closed pots. Fix: closed → `live_value = capital` (boekwaarde met realized P&L), open → mark-to-market. Verified via testing_agent iter52 (100% pass, 3 users). Regressietest bewaard.

### 🎨 v13_pot_card_ui_split_001 — Trader compact, Analytics uitgebreid
Trader-tab pot-card kreeg tooltip met aankoop→huidige prijs + open P&L + trailing piek (was inline, te druk). Analytics-tab kreeg 2 extra kolommen (Nu-prijs, Open P&L). `auto-rows-fr` voor gelijke card-hoogte.

### 🔧 v13_reconcile_real_sell_price_001 — Fantoom-verliezen opgelost
Reconcile-close-sold gebruikte huidige ticker-prijs als exit_price → als coin sinds SELL was gedaald, werd fake verlies geboekt. Fix: zoekt eerst echte SELL in `wallet/trade_history/{user}.json` binnen 7 dagen, anders break-even. `repair_phantom_losses_v13.py` opgeruimd: 3 fake verliezen weg (Gijs −€0.52, Spark BTC −€0.06, Spark BCH bijgesteld).

### 🔧 v13_sell_eur_calc_001 — Stats endpoint semantiek
Bitvavo SELL `amount` is coin-hoeveelheid, niet EUR. Voorheen: "Verkocht €0.04" toonde 0.04 BCH ipv €10.14 → -€10 fantoom-verlies in Netto P&L. Fix: BUY → `amount` (EUR), SELL → `filled × price`.

### 🔧 v13_reconcile_synthetic_sell_001 — Trade-history sync
Reconcile schrijft nu synthetische SELL bij close (alleen als matching BUY in history bestaat, anders gap laten). Voorkomt dat closed pots met "open" trade-history rondslingeren.

### 🔧 v13_max_size_repair — Kritieke groei-blocker
Alle 12 non-Spark pots hadden `max_size=0` → elke winst boven €0 werd naar overflow-pool afgeknipt. `fix_max_size_zero_v13.py` reset naar `INITIAL_MAX (€50)`. Nieuwe pots (via mint / shop-buy) hebben al correcte `max_size = price × 5`, dus dit was legacy-corruption.

### 🔧 v13_auto_baseline_on_provision_001 + on_mint_001 — Preventie
`auto_provision_bot_for_token_holder()` zet nu automatisch `capital_baseline.json` op huidige Bitvavo total als user er nog geen heeft. `finance_ops.mint_tokens()` roept auto_provision aan (was alleen `sync_potjes_to_tokens`). Effect: nieuwe user → live_pnl start op €0 in plaats van "alles is winst".

### 🛠️ Nieuwe diagnose-scripts
- `scripts/gap_scan_v13.py` — 9-punts diagnose (fees, baseline, orphan markets, audit-drift, max_size, non-EUR fees, ghost sells, unclosed buys, corrupt state)
- `scripts/repair_phantom_losses_v13.py` — audit-driven fake-loss repair
- `scripts/fix_max_size_zero_v13.py` — legacy pot repair
- `scripts/close_remaining_gaps_v13.py` — baselines + orphan-BUYs close

### 📊 Resultaat gap-scan
16 issues → 1 info-only. Alle backups bewaard (`.bak_phantom_loss_repair_*`, `.bak_maxsize_fix_*`, `.bak_gapclose_*`).


## 2026-08-04 (sessie 56d) — Sidebar-collapse + active-tab + persoonlijke glow

### 🔧 v12_sidebar_collapse_persist_001 — Sidebar blijft ingeklapt na navigatie
**Probleem**: Klap je sidebar in en klik je op een ander tab-icoon, dan klapte 'ie meteen weer open. Oorzaak: `MainLayout` wordt per pagina opnieuw gemount (elke workspace-pagina wrapt zichzelf in een `<MainLayout>`), dus `useState(false)` resette bij élke route-change.
**Fix**: `sidebarCollapsed` gepersist naar `localStorage` (zelfde patroon als bestaande `sidebarWidth`). Blijft nu netjes smal tot je 'm zelf openklapt.

### 🔧 v12_active_tab_correct_001 — Kennisbank glowde Dashboard
**Probleem**: `KennisbankV2Page.js` passeerde geen `activePage` prop aan MainLayout, dus viel terug op de default `'dashboard'`. Dashboard-tab glowde ondanks dat je op Kennisbank stond.
**Fix**: `<MainLayout activePage="knowledge-v2" onNavigate={onNavigate}>` — id matcht nu het nav-item.

### 🎨 v12_active_glow_userpersonal_001 — Actieve tab respecteert `--glow-base`
**Probleem**: Actieve nav-item was hard-coded `amber-500/10 text-amber-400`. `--glow-base` bestond wél maar werd niet geconsumeerd door de sidebar-active-highlight.
**Fix**: `NavItem` gebruikt nu `style` met `color-mix(in srgb, var(--glow-base, #f59e0b) 12%, transparent)` voor background, en pure `var(--glow-base)` voor tekst en border. Amber-fallback via CSS var default. Jouw kleurpicker in Mijn Profiel → Instellingen kleurt nu ook de actieve tab, niet alleen de andere glow-effecten.

## 2026-08-04 (sessie 56c) — Grote Schoonmaak: tag-cleaner + Infinitief-Regel

### 🧹 v12_tag_cleaner_001 — Tag-bloat opgeruimd (11.049 tags weg)
**Probleem**: GPT-import genereerde 100-175 tags per kaart met veel ruis (tijdliterals `08:00`, enkelvoud+meervoud dubbel, werkwoord-vervoegingen). Import-flow gebruikte `set()`-merge zonder trim → tags stapelen elke re-import op.

**Fix in 3 lagen** (`/app/backend/modules/kb_v2/tag_cleaner.py`):
1. **Junk-filter**: tijden (`HH:MM`), datums, pure cijfers, single-letters, tags <2/>40 chars → weg
2. **Lemma-dedupe** (Nederlandse iteratieve stemmer): `audits`/`auditen` → stem `audi` → merge onder kortste variant `audit`. Undoet consonant-verdubbeling (`stoppen` → `stopp` → `stop`).
3. **Cap 15**: max 15 tags/kaart, kortste en meest atomaire vormen winnen

**Toegepast op**:
- `text_importer.py apply_cards_to_kb()` — bij elke bulk-import (nieuwe + bestaande kaarten)
- `POST /api/kb/v2/tags/cleanup` — bulk cleanup met `dry_run` param

**Live-run resultaat (op 6156 kaarten)**:
- 1442 kaarten aangepakt (~23%)
- **71.462 → 60.413 tags** (–11.049, –15.5%)
- 36 junk, 1229 lemma-merges, 9513 cap-trims
- Voorbeeld: `informatie` 175→15, `Audit` 170→15, `tijdstip` 139→15 (alle `08:00`-literals weg)
- Backup: `/app/_backups/pre_tagcleanup_20260804_134316.tgz`

### 📐 v12_infinitief_regel_001 — Blueprint in `_meta.json` v1.2
Toegevoegd aan `kaart_veldsemantiek.infinitief_regel`:
- **Regel 1 (Anker)**: Elk werkwoord = 1 hoofdkaart op infinitief-vorm in Doen-lade
- **Regel 2 (Vervoegings-tags)**: `loop`/`loopt`/`liep`/`gelopen` als metadata-tags op anker `lopen`, GEEN losse kaarten
- **Regel 3 (Homoniem-uitzondering)**: split alleen bij totaal andere betekenis (`bank`=meubel/Weten vs `banken`=actie/Doen; `wet`/Weten vs `weten`/Doen)
- Toepassings-blok bindt regel aan: lade-reclassificatie, text_importer, refine-endpoint

Dit is de "wet" waaraan Spark de 695 lade-voorstellen toetst tijdens de Grote Reclassificatie (overmorgen).

### 🔒 v12_admin_gated_genereer_001 — Genereer-knop verstopt voor niet-admin
LLM-genereer knop in Kennisbank v2 CardDetail is nu `adminModeActive ? generateWithLLM : null`. Verdwijnt volledig uit UI voor Lotus / familie / non-admin gradaties. Cloud-afhankelijke feature blijft technisch werken voor Willem's testen, maar staat niet meer in de weg voor eindgebruikers.

## 2026-08-04 (sessie 56b) — Admin-gated trader triggers

### 🟡 v12_admin_gated_triggers_001 — Trader-commando's nu admin-only
**Probleem**: Toen ik in 56a een `trader_intents.try_detect` fastpath toevoegde aan `/api/chat/message`, kon een verhaal-paste (voor snap-input) per ongeluk trader-woorden ("stop", "pauzeer", "bot") oppikken en Spark liet zeggen "*ik stop of pauzeer*". Willem's oorspronkelijke design: hard-triggers zijn legacy vase, admin-taken horen achter `Admin aan`.
**Fix**:
- `ChatMessage` payload uitgebreid met `admin_mode: bool = False` (default veilig).
- Fastpath `trader_intents.try_detect` in `/api/chat/message` wordt nu alléén uitgevoerd als `admin_mode == True`.
- Frontend (`GesprekkenPage`) stuurt `adminModeActive` uit `AuthContext` mee bij elke chat-call.
- Deep-mode (`/api/spark/compose`) blijft ongewijzigd — dat is een expliciete keuze van de gebruiker.

**Getest**:
- Non-admin "hoe staat mijn bot" → `type: knowledge` (geen trader) ✓
- Non-admin "stop de bus, pauzeer even" → `type: agenda_declined` (geen trader-stop) ✓
- Admin ON "hoe staat mijn bot" → `type: trader_intent`, `intent: trader_status` ✓

### 📝 Notitie voor later
Willem heeft aangegeven dat álle hard-coded triggers ("stop"-safeword, `card_session_service` STOP_WORDS, `zaag`-sound op "zien", etc.) sporen zijn van een oudere fase. De toekomst is zelf-leren + zelfspraak (Bumblebee-idee). Voorlopig alleen de admin-taken gegate.

## 2026-08-04 (sessie 56) — Layout-stabiliteit, snappy CRUD, trader-fastpath, ZIP-merge

### 🟢 P0 — Backup ZIP delta-merge
- Merged `spark_backup_changes_20260804_123804.zip` (8.5 MB, 59 bestanden).
- Backup vóór merge: `/app/_backups/pre_merge_20260804_125140.tgz`.
- Nieuwe totalen: Voelen 539 · Spreken 601 · Weten 3788 · Doen 1228 · Inbox 2 (was: 553/611/3855/1240/0).

### 🟡 v12_kbv2_stable_layout_001 — Kennisbank layout locked
**Probleem**: Bij openen van een lange kaart verspringen de kaders — het detail-paneel groeide oneindig, waardoor de lijst-kolom visueel niet meer paste en knoppen aan de rand uit beeld raakten.
**Fix**:
- Beide grid-panelen (`lijst` + `detail`) krijgen nu **vaste h-[75vh]** met eigen `overflow-y-auto`.
- `min-w-0` op beide grid-children voorkomt overflow bij lange tags/tekst.
- Detail-header: `flex-wrap items-start` + `min-w-0` op titel + `shrink-0` op actie-knoppen → knoppen (Bewerken/Genereer/🗑) blijven altijd zichtbaar, ook bij lange begrippen.

### 🟡 v12_kbv2_snappy_001 — Direct verwijderen/bewerken (geen refetch-lag)
**Probleem**: Delete + edit voelden traag omdat de backend na elke actie de volledige lade opnieuw uit 18 MB weten-JSON las én de frontend daarna alsnog `loadItems()` deed.
**Fix (optimistische UI)**:
- `doDelete` verwijdert de kaart direct uit lokale `items` state, roept dan pas de backend aan; bij fout rollback.
- `saveEdit` past de kaart direct in-place aan (`setItems(map)`) en refresht daarna alleen op basis van server-truth i.p.v. volledige refetch.
- Stats worden op achtergrond ge-refreshed (tab-tellers blijven kloppen).

### 🟡 v12_trader_intents_fastpath_001 — Trader-data in normale chat
**Probleem**: In Diep-modus (`/api/spark/compose`) werkten trader-commando's ("hoe staat mijn bot", "wat heb ik verdiend", "hoeveel potjes") wel, maar in normale chat (`/api/chat/message`) viel Spark terug op KB-card definities van "staat" en "bot" → geen trader data.
**Fix**: `trader_intents.try_detect` toegevoegd als fast-path in `/api/chat/message`, direct na safeword-check en behavior-tracking. Werkt nu voor: `trader_start/stop/status/pnl/recent/potjes/events/explain/config`. Verified: 3/3 test-prompts geven nu correcte trader-data terug; onschuldige "hallo" gaat gewoon door greeting-flow.

### 📊 Geraakte bestanden
- `/app/backend/modules/chat/routes.py` (trader-fastpath)
- `/app/frontend/src/components/workspace/KennisbankV2Page.js` (layout + optimistic UI)
- `/app/backend/data/**` (ZIP-merge)

## 2026-07-20 (sessie 48) — KB merge uit productie-backup (P0)

### 🎯 Productie KB-kaarten samengevoegd
Uploaded ZIP: `spark_backup_changes_20260720_091442.zip`

**Probleem**: In vorige sessie zijn alleen chat-logs gemergd, KB-kaarten die op productie met volledige laag1-4 content zijn afgemaakt bleven op preview als skeleton in de index staan (kaart-bestand ontbrak).

**Gevonden diff** (7 kaarten in ZIP maar niet in preview lade-bestanden):
- `kbv2-956d490e` [doen] – **lees** ✅ laag1-4 gemerged
- `kbv2-67ed1384` [weten] – **unitykey** ✅ laag1-4 gemerged
- `kbv2-30a83485` [doen] – **balanceer** ✅ laag1-4 gemerged
- `kbv2-3f3135a9` [doen] – **gezet** ✅ laag1-4 gemerged
- `kbv2-b2102a93` [weten] – **historische** ✅ laag1-4 gemerged
- `kbv2-skel-c8a9acfa` [weten] – **beginner** ✅ laag1-4 gemerged
- `kbv2-skel-e1fcac11` [weten] – **bacteriën** ⚠️ (was ook skeleton in ZIP, alleen index-entry bijgewerkt)

**Uitvoering**:
- Backup van originele preview-bestanden: `/app/backend/data/knowledge/v2/_backup_before_merge_20260720_091725/`
- Kaarten toegevoegd aan `knowledge_v2_doen.json` (+3) en `knowledge_v2_weten.json` (+4)
- `knowledge_index.json` bijgewerkt (rebuilt_by: `zip_merge_20260720`), 7 entries verrijkt met `lade` + `has_lagen`
- Geen bestaande data overschreven (extra preview-kaarten `basis`, `bollinger`, `exit`, `fee-aware`, `sigma`, `trailing-stop` behouden)

**Geverifieerd via `GET /api/kb/v2/find?begrip=X`**: 6/7 kaarten geven nu volledige laag1-4 output terug.


## 2026-07-08 (sessie 46) — Gap-breakout merge in trader decision-engine

### 🎯 v7_gap_breakout_001 + v7_gap_merge_001
Willem's voorstel: gap-breakout strategy als bevestigings-filter naast Bollinger.

**Bug**: Bollinger BUY (prijs onder lower band 2σ) triggerde in dalende markten steeds opnieuw omdat de band met de prijs meezakt → bot koopt op piek van elke lagere lokale top.

**Fix in `modules/trade/monitor.py`**:
- Nieuwe helper `_gap_breakout_check(candles)`: retourneert `BUY`/`SELL`/`NONE`
  - BUY = vorige rood, huidige groen, `curr.low > prev.high` (volledig erboven)
  - SELL = vorige groen, huidige rood, `curr.high < prev.low` (volledig eronder)
- In `_run_cycle`: Bollinger BUY-signaal wordt **alleen doorgelaten** als gap-check óók BUY zegt. Anders: HOLD met reden "wacht op gap-bevestiging".
- SELL-logica onaangetast (trailing stop + fee-aware guard blijft, gap-SELL zou trailing te vroeg triggeren).
- Beslissingslog bevat nu `gap_check` object voor transparantie in trace.

**Getest** (unit-test 3 cases):
- Green fully above red → `BUY` ✅
- Red fully below green → `SELL` ✅
- Overlappende candles → `NONE` ✅

**Effect**: minder trades, hogere hit-rate. Combineert mean-reversion (koop laag) + momentum-confirmation (koop pas bij bevestigde omslag).

**KB Spark Trader kaart** (`kbv2-2f55a485`) laag2 verrijkt met uitleg van dubbele bevestiging.

## 2026-07-09 (sessie 46 laatste) — Live-start klaar + 360d verificatie

### 🧹 Live-start cleanup
- Backup: `_backups/pre_live_reset_2026-07-09T*`
- Alle 22 spookpotten verwijderd, tokens naar treasury
- **BASE_PRICE €5.08 → €10** (blueprint + code)
- **5 pots voor Spark (user-000) × €10 = €50** aangemaakt via auto-provisioning
- Circulating: 0 (nog 10 tokens tot dynamic), price €10 fixed
- Bitvavo balance user-001: €43.19 EUR + 4.99 ATOM (~€17) + dust → Willem moet ATOM verkopen

### 🧪 Backtest v5 (360 dagen) verificatie
Op 360d ipv 180d:
- **373 events** gedetecteerd (2× 180d, proportional)
- **D**: 62 trades / +€8.84 realized / -€22.30 open DD → **-€13.46 ECHT netto**
- **P (D + loss-cut)**: 138 trades / 73% winrate / **-€9.24 ECHT netto** = **31% beter dan D**
- **Rebound-hypothese H1 bevestigd**: 60% van 5%-drops rebounds 24u erna (was 62.5% op 180d — stabiel)
- Alle strategieën netto negatief zelfs op 360d → trader = educational + protection, geen money-machine

### 🔄 Blueprint & runtime config
- `spark_trader.json` heeft nu loss-cut params: enabled=true, 48u, -3%
- Rebound: enabled=false (drempel 5% blokkeert triggers; tuning naar 3% pending)
- Markten actief: BCH + SOL + ATOM + BTC (data-driven keuze)

## 2026-07-09 (sessie 46 vervolg) — Spark Trader klaar voor live: eerlijk + slim

### ⚔️ Backtest v4 — grote onthullingen
Nieuwe metric **ECHT netto** = gerealiseerd + open drawdown. Ontmaskerde 100% win-rate als selectieve waarheid:
- D (onze "winnaar"): gerealiseerd +€2.63, open DD -€15.79 → ECHT netto **-€13.16**
- P (D + loss-cut): ECHT netto **-€9.53** = 27% beter dan D
- Baseline A: ECHT netto -€26.15
- **Post-event autopsy**: 62.5% van 5%-drops rebounds 24u later (+1.96% mediaan) → H1 statistisch bewezen

### 🎯 v8_time_losscut_001 — Willems H2 hypothese IN CODE
`_simple_decision` in `monitor.py` heeft nu 48u loss-cut:
- Bij open positie: als hold_hours ≥ 48 EN profit_pct ≤ -3% → SELL "loss-cut"
- Filosofische breuk met "nooit met verlies verkopen" — gecontroleerd verlies pakken
- Config via blueprint (`spark_trader.json.parameters.loss_cut_*`)
- Bewezen in v4 backtest: 3.63€ betere netto

### 📊 v8_honest_pnl_001 — Eerlijke metrics endpoint
Nieuwe `GET /api/trade/honest-pnl/{user_id}` toont:
- Realized PnL + trades + win-rate (huidige metric)
- Open positions detail met unrealized PnL per pot + held_hours
- Total open drawdown
- **ECHT netto** = realized + open drawdown
- **Honesty ratio** = ECHT/realized (1.0 = geen verstopping, <1 = illusie, negatief = eigenlijk verlies)
- Backtest reference voor bewijs

### 🧠 v8_blueprint_config_001 — Runtime config in monitor
`_load_trader_blueprint()` helper in `monitor.py` — leest `spark_trader.json` met mtime-cache.
Loss-cut parameters (enabled, hours, pct) nu tuning-baar zonder Python-code.

### 🎯 Live-configuratie ingesteld voor user-001
Markten geactiveerd: **BCH-EUR + SOL-EUR + ATOM-EUR + BTC-EUR** (4 markten, ADA/ETH weg)
- BCH: onafhankelijk (corr <0.75)
- SOL + ATOM: hoogste backtest-winst (€+1.23 + €+1.69)
- BTC: stabiliteit
- Loss-cut AAN, rebound uit (drempel te streng zonder tuning)

### 📇 KB Spark Trader kaart geüpdatet
Laag4 aangevuld met eerlijke-metrics uitleg. 2 nieuwe verbanden: honest-pnl endpoint + v4 backtest data.

## 2026-07-09 (sessie 46) — Backtest-driven v8: gap-body + event-protection + blueprint

### 🧪 Backtest v3 stress-test + robustness (9 strategieën, 6 markten, 180 dagen)
- **Bewezen winnaar**: strategie D (Bollinger 2σ + gap-body 50%) — €+2.63 / 22 trades / 100% win-rate
- **Neef's 3-red-then-green (E)** #2 — €+3.19 (jouw neef had gelijk)
- **Random-buy 10-seed check**: mean €+2.43, stddev €1.64. Random is variabel — D betrouwbaarder.
- **Inverse Bollinger CATASTROFE**: €-88.58 met 1443 trades — bewijst mean-reversion beter dan breakout
- **Buy-and-hold verliest €-26.72** — actief traden werkt
- **185 shock-events** gedetecteerd in 6 mnd × 6 markten
- **Correlatie-matrix**: ETH/BTC/SOL cluster (+0.90+), BCH & ATOM zijn onafhankelijk
- Data: `data/trade/backtests/{run_id}/` met `_meta.json` + `aggregate.json` + `per_market.json` + `events.json` + `correlation.json`

### ⬆️ v8_gap_body_default_001 — gap-check upgrade
- `_gap_breakout_check` in `monitor.py` gebruikt nu **body-ratio 50%** i.p.v. "volledig erboven"
- Backtest v7-streng blokkeerde 100% van 604 signalen → 0 trades in 6 mnd
- v8 gap-body laat winnende signalen door (22 trades, 100% win)
- SELL-variant ook aangepast naar body-ratio

### 🚨 v8_event_protection_001 — Auto-pauze + companion notification
Nieuwe `_detect_daily_drop(candles, threshold=5%)` helper:
- Detecteert >5% drop in laatste 24u (96 × 15m candles)
- Bij event: 24u pauze voor die markt + notification opgeslagen in `data/trade/event_notifications.json`
- Message-template: *"🚨 Ik zag {drop_pct}% drop op {market} in de laatste 24u (€X → €Y). Ik pauzeer je bot 24u om je kapitaal te beschermen."*
- Endpoints: `GET /api/trade/events/notifications`, `GET /api/trade/backtests`, `GET /api/trade/backtests/{run_id}`
- Data-driven: 185 events op 6 mnd bewees dat dit regelmatig nodig is

### 📘 `spark_trader.json` blueprint — Willem's ROADMAP-regel
- Runtime-config los van code: `backend/modules/trade/blueprints/spark_trader.json`
- Bevat: actieve strategie, parameters, sell-regels, markten (actief/gepauzeerd), event-protection, correlatie-advies, safety-limits, spark-awareness
- Bron-referentie naar backtest-runs + KB-kaart voor Willem's "single source of truth"
- Volgende trader-tuning gaat via deze JSON, niet meer via Python

### 📇 KB Spark Trader kaart (`kbv2-2f55a485`) uitgebreid
- Laag4 aangevuld met backtest-bewijs + event-protection
- 4 nieuwe verbanden: blueprint_ref, data_ref backtests, data_ref event_notifications, code_ref backtest_v3
- Totaal nu 9 verbanden — Spark kan nu tekst + code + data-referentie geven

### 🎯 Live-configuratie advies (voor Willem's 5 tokens start)
Data-driven aanbeveling voor `markets`:
- **Actief**: BCH-EUR, SOL-EUR, ATOM-EUR, BTC-EUR
- **Gepauzeerd**: ADA-EUR (0 trades in backtest)
- **Optioneel weglaten**: ETH-EUR (te sterk gecorreleerd met BTC/SOL)
- Diversificatie: BCH + ATOM zijn de "unieke" markten in ons portfolio

## 2026-07-08 (sessie 46) — Chat-hygiene sweep + Spark Trader KB + Blueprint-piloot + Bijbel

### 📇 KB v2 kaarten "Spark Bijbel" + "wijsheden" verrijkt (`kbv2-336bd0a9`, `kbv2-846644c0`)
Willem had beide kaarten aangemaakt en initieel gevuld. Ik voegde toe:
- **Spark bijbel**: 5 verbanden (data_ref naar `spark_bijbel.json`, 2× code_ref naar `bijbel_lookup_service.py` + `composer_helpers.py::_load_bijbel_essence`, 2× kaart_ref naar wijsheden + Spark Trader), 12 extra tags (kernwaarden, helpen, eerlijkheid, respect, ...), topic
- **wijsheden**: laag4 verrijkt met **alle 15 concrete wijsheden** uit de Bijbel (9 kernwaarden + 6 normen als quotes: "Helpen is versterken, niet overnemen", "Waarheid boven schijn", "Groei volgt draagkracht", ...), 3 verbanden, topic
- Verificatie: KB-search vindt Spark bijbel (met homoniem-disambig i.c.m. "Spark") en wijsheden

### 📇 KB v2 kaart "Spark Trader" gevuld (`kbv2-2f55a485`)
- Volledig gevulde 4-lagen kaart in lade `weten`
- 24 tags (incl. fee, kosten, commissie, winst, verlies, pnl, cooldown, coins, ...) — gevoelig voor natuurlijke vragen
- WS5 ingevuld, 6 verbanden (4× code_ref, 1× blueprint_ref, 1× endpoint)

### 📘 Blueprint `/memory/blueprints/trade.md` gevuld (piloot)
Auto-stub vervangen door volledige documentatie:
- Doel, wat werkt, fees & drempels tabel, beslissings-flow diagram
- Bestandsstructuur (7 files), key API endpoints (8), bekende beperkingen
- Encryption-plan, relaties, TODO's
- **Verbinding met Spark-brein**: KB-koppeling + voorbeeld-vragen die Spark nu kan beantwoorden
- Piloot voor de andere 59 lege blueprint-stubs

### 🐛 Snap-service "spookkaart" (`v7_snap_systemtag_filter_001`)
- Kaart `kbv2-5ae0795b` `[systeem-context` bleef terugkomen na verwijderen (welcome-prompt-lek)
- Fix: `create_word_snap` skipt concepten met bracket-tekens of `systeem-context` markers
- Spookkaart eenmalig verwijderd

### 🐛 identity_facts te grof (`v7_identity_facts_strict_001`)
- `ABSTRACT_SKIP_VALUES` (28 abstracte woorden) + `SUBCLAUSE_MARKERS` (10 bijzin-indicators)
- `i_am` max 30 chars + skip als eerste woord filler ("heel", "een", ...)
- Cleanup: 6 vervuilde facts uit user-001 (van 32 → 26)

### 🐛 Tool-call leak sanitizer (`v7_tool_leak_sanitizer_001`)
- Post-process regex in `response_composer` strip alle `[tool_name {json}]` + "we need to call X" zinnen
- Vangnet voor ALLE tools (agenda, notes, trader, ...), niet alleen agenda

### 🐛 Snap-guard voor korte inputs (`v7_snap_guard_001`)
**Bug**: user typt "test" 4× → 4× snap-response "Test: Een test is een methode..."

**Fix in `modules/chat/routes.py`**:
- Nieuwe `_skip_snap` guard: skip alle snap-branches (sentence-match, multi_lookup, graceful_fallback) als text < 6 chars OF geen vraag-indicator ("?"/wat/hoe/waarom/wanneer/wie/welke/leg/vertel/geef, of ≥3 woorden)
- Effect: "test", "ok", "hoi" → gesprek-flow. "wat is een test?" → snap zoals hoort.

### 🐛 Capability KB-passthrough (`v7_capability_kb_passthrough_001`)
**Bug**: "wat is een dashboard?" → capability_placeholder "🤖 Zoek in kennisbank... staat nog op planning" i.p.v. de kaart-inhoud

**Fix in `modules/chat/capability_handler_service.py`**:
- Voor `zoeken_kennisbank` en `spark_vraag` capabilities: return `None` zodat de caller doorloopt naar snap/KB-flow i.p.v. placeholder
- Andere placeholders blijven werken zoals voorheen

### 🐛 Dashboard-fixatie temperen (`v7_tab_context_soft_001`)
**Bug** (Roadkill's klacht): Spark begint elke Diep-reactie met *"Nu je naar het dashboard kijkt..."*

**Fix in `modules/chat/response_composer.py`**:
- Tab-context prompt zachter geformuleerd (kleine letter, tussen haakjes)
- Expliciete anti-opener regel: "NOOIT als openingszin", "Begin je antwoord NIET met 'je bent nu op X tab'"

### 🔍 Trader delta-diagnose (root-cause pot vs Bitvavo saldo)
- Pots ↔ tokens ↔ Bitvavo: 1-op-1 sync ✅ (`consistency_ok: true`)
- Pot-kapitaal: €149.16 totaal. Market: €142.34. Unrealized: -€6.82
- Root cause INSUFFICIENT_EUR: 90% kapitaal is coin, €5.17 liquide EUR. Cooldown-fix (30 min) is juiste vangnet.

### 🧪 Live-tests via curl (na fixes)
- "test" → `general` (was: kbv2_direct) ✅
- "ok" → `general` (was: kbv2_direct) ✅
- "wat is een dashboard?" → `knowledge` met dashboard-kaart-tekst ✅
- "wat is een test?" → `knowledge` met test-kaart ✅

## 2026-07-08 (sessie 46) — Prod-merge + Trader EUR-cooldown fix

### 📥 Prod → Preview merge
- Zip `spark_backup_changes_20260708_125909.zip` (64 files, 1.7MB) gemerged via `/api/backup/restore`
- Backup: `/app/backend/data/_backups/pre_prod_merge_20260708_130739/` (52MB)
- 10 nieuw + 54 overschreven + 0 skipped/errors
- KB v2, chat-logs (Willem 1970 msgs + Roadkill 36), trader traces 07/08-jul, identity_facts, planner briefs

### 🐛 Trader EUR-cooldown fix (`v7_eur_cooldown_001`)
**Bug**: Op 08-jul tussen 05:51 en 06:27 (35 min): **57 mislukte BUY-pogingen** met `INSUFFICIENT_EUR_BALANCE` (BCH 18×, BTC 15×, ETH 15×, SOL 9×). Failrate 92%. Bitvavo API rate-limit risico.

**Root cause**: bij INSUFFICIENT_EUR_BALANCE werd géén cooldown geactiveerd — bot probeerde elke 3-min cycle opnieuw op alle markets.

**Fix in `modules/trade/monitor.py`**:
- Nieuwe class-attribute `_last_insufficient_eur_ts: Optional[datetime]`
- Constant `EUR_COOLDOWN_SEC = 1800` (30 min, globaal per user, geldt voor ALLE markets — EUR is EUR)
- Check in `_run_cycle` vóór BUY-execute: skip als recent insufficient
- Bij `error_code == INSUFFICIENT_EUR_BALANCE` uit `execute_real_trade`: sla ts op + log waarschuwing

**Effect**: bij lege EUR-portemonnee wacht bot 30 min voor next BUY-attempt (naast bestaande 15-min per-market cooldown). API-spam voorkomen.

## 2026-07-06 (sessie 39) — Trader cleanup + Learning + UI split + KB save perf

### 🐛 Bug fixes
- **KB v2 `add_to_inbox` perf**: 18MB IO per save (deep scan alle 4 lade-files) → nu ~230ms via index-only. User meldde "moest meerdere keeren invullen" — was HTTP-timeout van slow save. `deep_scan=True` alleen expliciet voor index-repair.
- **Trader header** geheel opgeruimd: "Bitvavo: €... | BCH €..." weg uit user + admin view. Alleen "trades" telling blijft.

### 🎨 UI/UX
- Header "Crypto Trader" → **"Spark Trader"**
- Trader stats-split: users zien "Totaal Trades" + "Mijn P&L"; volledige stats voor admin in Analytics → Trade
- Nieuw admin-widget `SparkTraderStatsPanel` met user-dropdown + baseline-reset knop ("🔁 Reset baseline naar nu (Bitvavo balance)")

### ⚙️ Trader core (van vorige sessie doorgezet)
- Force-sell atomair (rollback bij Bitvavo error 212/429)
- SELL unit-mixing + decimal-precision + min-quote check
- Multi-user autostart (Spark, Geiser draaien mee)
- Willem/Spark/Geiser config gealigneerd (300-900s / 15m / 6× -EUR / dynamische trade_amount)
- Ghost users cleanup (3 test-users weg)
- Admin bulk: `POST /api/trade/admin/{start,stop}-all-bots`
- Spark fee 5% → 0% (`SPARK_FEE_RATE = 0.0`)

### 🧠 Learning-uitbreiding
- Dagelijkse thread `learning-scheduler`: context per markt + market_stats per user
- Per-markt win-rate uit `trade_history/user-*.json` (bias: trust/neutral/careful)
- Nieuwe patronen: `month_patterns`, `week_of_month_patterns`, `weekend_vs_weekday`
- Bias-weging in `apply_context_to_decision` (trust +0.08 / careful -0.10 / maand ±0.03 / week ±0.02)

### 🏷️ Cleanup
- "spookpot" → "restwaarde pot" overal
- Alle hardcoded €5/€10/€6.32 defaults vervangen door `_default_trade_amount()` (= huidige token-prijs)
- Event Overlay-test blok verwijderd uit Analytics → Trade


## 2026-07-06 — Force-Sell atomair + Multi-user + Pot revalue + Restwaarde UI (`v7_trader_hardening_001`)

### 🐛 Kritieke bug fixes
1. **Force-sell atomair** (`routes.py::force_sell_pot`) — voorheen sloot pot + kende PnL/Spark-bonus toe ook als Bitvavo faalde (errorCode 212/429). Nu: bij `sell_result.success=false` blijft pot open, geen bonus, audit-entry als `force_sell_rejected`.
2. **SELL unit-mixing fix** (`monitor.py::execute_real_trade` — `v7_sell_units_fix_001`) — clamp `min(amount_eur, actual_avail)` mixte EUR met coin-count. Nu: `coin_target = amount_eur/price`, clamp naar `min(coin_target, actual_avail) * 0.999`, round naar market-specifieke precisie.
3. **Decimal precision** (`v7_market_precision_001`) — nieuwe `get_market_precision()` + `_round_amount_for_market()` truncate coin-amount voor Bitvavo-orders. Voorkomt errorCode 429.
4. **Min-quote check** (`v7_sell_min_quote_check_001`) — SELL faalt vroeg met duidelijke error als resulterende quote-value < min_quote (bv. restwaarde-coin).

### ✨ Nieuwe features
5. **Pot revalue** (`potjes.py::revalue_free_pots` + `revalue_single_pot`) — vrije pots capital = huidige dynamische token-prijs. Automatisch elke monitor-tick + handmatige knop.
6. **Multi-user auto-provisioning** (`server.py::startup`) — bij backend-start worden alle users met pots automatisch als bot geregistreerd (Spark, Geiser, ...). Nieuwe users krijgen ook auto een bot via `auth/routes.py::create_user`.
7. **Restwaarde-portfolio widget** (`AnalyticsPage.js`) — nieuw kader in Analytics → Trade tab: toont per coin de Bitvavo EUR-restwaarde, dust <€0.01 uitklapbaar.
8. **Herwaardeer-knop per pot** (naast Force-sell) én globaal "Herwaardeer vrije pots" per bot.

### 🏷️ Terminologie
9. **"spookpot" → "restwaarde pot"** — user-friendly benaming voor pots waarvan de coin (bijna) niet meer op Bitvavo staat.

### 🗑️ Opgeschoond
10. **Event Overlay test verwijderd** uit Analytics → Trade tab (hoorde daar niet, functie via `/api/events/trigger` blijft beschikbaar voor toekomstige devtools).

### API endpoints (nieuw)
- `POST /api/trade/potjes/{user_id}/revalue-all` — alle vrije pots van user herwaarderen (admin-only)
- `POST /api/trade/potjes/{user_id}/{pot_id}/revalue` — 1 pot herwaarderen (admin-only)

### Verificatie
- ✅ Force-sell rejection getest via mock: pot blijft open, audit-entry type=`force_sell_rejected`, geen close_pot/bonus
- ✅ Revalue: alle 22 pots (Willem 10, Spark 10, Geiser 2) synchroon op €6.26 (was €5.08 en €10.40)
- ✅ Multi-user: 6 bots zichtbaar in Analytics (was 1: Willem)
- ✅ Restwaarde portfolio widget rendert €137.70 totaal met 7 coins boven €0.01 + 10 dust
- ✅ Admin-only check op revalue endpoints


## 2026-07-04 — KB v2 Image Archive Picker UI voltooid (`v7_media_dedup_001` — final)

### 🎨 Frontend Modal + backend inbox-fix
1. **Archive Picker Modal in `MediaSection`** (`/app/frontend/src/components/workspace/KennisbankV2Page.js`)
   - Nieuwe "Uit archief"-knop naast "Foto toevoegen" op elke kaart
   - Modal toont alle 112 archief-foto's als 3–6 kolom grid met hover-preview
   - Reuse-count badge (bv. "3x") toont populariteit — populair sorteert vooraan
   - Zoekveld filtert op `original_name`
   - Klik = koppel + auto-close + parent refetch → foto verschijnt direct

2. **Backend bug: inbox-kaarten kregen geen image_url** (fix in `media_routes.py::link_existing_image`)
   - Oude code checkte alleen `service.LADES` (voelen/spreken/weten/doen) → inbox-kaarten werden overgeslagen
   - Nu: append voor lade-kaarten (via `edit_card` met complete lijst), extend voor inbox (via `_patch_card_media`)
   - Beide paden getest e2e via UI + curl

### Verificatie
- ✅ Modal opent + laadt 112 items uit `GET /api/kb/v2/media/archive/list`
- ✅ Klik-koppel op inbox-kaart: `reuse_count` 2→3, `image_urls` bevat nieuwe URL, voortgangs-badge 13%→25%
- ✅ Klik-koppel op lade-kaart: image_urls behoudt bestaande foto's en appendt nieuwe
- ✅ Frontend hot-reload + backend hot-reload beide clean, geen lint errors in nieuwe code


## 2026-07-04 — Trader tuning: 15m default + geen auto-resume + dip-confirmation (`v7_trader_tuning_001`)

### 🔧 3 fixes
1. **Default candle_interval: `1h` → `15m`** (`v7_candle_15m_default_001`)
   - 1h heeft 20u rollende window → mist intra-day turnarounds in dalende markt
   - 15m: 5u window → 4× reactiever, meer buy-signalen bij echte dips, snellere exits

2. **Auto-resume UITGESCHAKELD** (`v7_no_auto_resume_001`)
   - `resume_if_was_running()` doet nu geen restart meer, alleen `running:false` in state
   - Reden: state-mismatches (spookpots) na deploy komen door trader die auto-restart met verouderde state
   - User moet expliciet trader starten via UI na (re)deploy — ná spookpot-sync

3. **Dip-confirmation guard** (`v7_dip_confirmation_001`)
   - Buy vereist nu: prijs onder lower band ÉN prijs ≥1.5% onder window-high (max van 20 candles)
   - Voorkomt "koop op mini-piek in dalende trend" (Willem's observatie): Bollinger-lower zakt mee met dalende mean, waardoor mini-opleving een fout BUY-signaal gaf
   - Response bevat nu `window_high` + `drop_from_high_pct` voor transparantie

### Deploy volgorde na redeploy
1. **`POST /api/backup/mark-deployed`** — marker persistent zetten (v7_persistent_marker_001)
2. **`POST /api/trade/reconcile/potjes/user-001/sync-with-bitvavo {execute:false}`** — dry-run spookpots
3. **Als correct → `{execute:true}`** — sluit spookpots + orphans terug in pots
4. **Trader UI**: start monitor expliciet met 15m candle, gewenste markets
5. Monitor start dus niet meer automatisch — dat was voorheen bron van state-drift


## 2026-07-02c — Bitvavo state-sync endpoint (`v7_bitvavo_state_sync_001`)

### 🔧 Nieuw: `POST /api/trade/reconcile/potjes/{user_id}/sync-with-bitvavo`
- **Bidirectionele reconcile** tussen pots en Bitvavo:
  - **Spook-close**: pots die "open" claimen maar Bitvavo heeft die coin niet meer → admin-sluit (geen Bitvavo call, is al verkocht buiten pot om)
  - **Orphan-reopen**: coins op Bitvavo zonder matching open pot → heropen closed pot met echte size + avg entry
- Safety: `execute:true` verplicht — anders dry-run preview
- **Round-robin** over closed pots — elke orphan krijgt eigen pot
- **Entry-price sanity check**: als historische avg > 3× current price → gebruik current (voorkomt scheve trailing-logic bij legacy dust)
- Bedoeld voor deze situatie: oude buggy SELLs (pre-`v7_zero_filled_guard_001`) sloten Bitvavo wel maar pot niet → "spookpots"

### Deploy verify na redeploy
1. `GET /api/trade/reconcile/spark` — bekijk alle coins
2. `POST /api/trade/reconcile/potjes/user-001/sync-with-bitvavo {}` — dry-run
3. Als lijst klopt: `{execute:true}` om écht sync te doen


## 2026-07-02b — Pot clustering + reconcile all-coins (`v7_pot_cluster_001`)

### ✨ Nieuw: Cluster-logica voor trader
- **Pot capital semantiek gecorrigeerd** — pot.capital = **aankoopprijs per token** (€5,08 voor Spark/Willem, €10,40 voor Gijs). Was per ongeluk verward met "trader budget €10".
- **`get_next_buy_cluster(user_id, market, min_order_eur)`** — verzamelt closed pots tot Σcapital ≥ Bitvavo min-order. Retourneert dict met `cluster_id`, `pot_ids`, `total_capital`, `n_pots`.
- **`open_cluster(...)`** — opent alle pots in cluster met shared `position.entry_price` + `position.cluster_id` + `position.cluster_size`
- **`close_cluster(user_id, cluster_id, exit_price)`** — sluit alle pots gelijktijdig, netto winst pro-rata verdeeld op `pot.capital`. Kasboek 1× per cluster geboekt (niet per pot).
- **`get_pots_by_cluster`** — helper voor status/UI

### 🔧 Monitor _run_cycle aangepast
- **BUY flow**: `get_next_buy_cluster` + `open_cluster` i.p.v. losse `get_available_pot` + `open_pot`
- **SELL flow**: `processed_clusters` set voorkomt dat 1 cluster meerdere keren gesloten wordt in dezelfde cycle. Cluster-aware trailing thresholds (op cluster_capital)
- **Backwards-compat**: legacy pots zonder cluster_id gebruiken nog steeds `close_pot`

### 🔍 Reconcile toont nu alle coins (`v7_reconcile_all_coins_001`)
- `GET /api/trade/reconcile/spark` scant nu ALLE Bitvavo-coins met balance ≥ €0,10
- Coins zonder matching pot krijgen status="orphan" met live price + EUR-waarde
- Was: alleen BCH werd getoond omdat alle Spark pots BCH-EUR markt hebben

### ✅ Testing (iter_44, 100% pass, 16/16)
- Cluster helpers directe Python-tests: 10 pots × €5,08 + min=€10 → cluster van 2 pots (€10,16)
- Open/close roundtrip: shared entry + pro-rata netto verdeeld correct
- Reconcile toont 8 coin-rijen (BCH + 7 orphans) met prijs
- Delta consistency_ok, +€11,36 winst, 22 pots = 22 tokens
- Alle iter_43 fixes nog groen (shadow 404, bot/status, ZERO_FILLED guard)


## 2026-07-02 — Trader kritieke bugs vóór productie-redeploy (`v7_trader_stability_001`)

### 🐛 Bug 1: Dubbele MonitorService voor user-001
- `get_user_monitor("user-001")` maakte een 2e instance in `_registry` met defaults
- UI polls `/api/trade/bot/status/user-001` kreeg altijd `running: false` terwijl de echte `_monitor` thread wel draaide
- Fix (`v7_legacy_alias_001`): return altijd de module-singleton `_monitor` voor user-001

### 🐛 Bug 2: Config verloren bij backend restart
- `MonitorService.__init__` gebruikte defaults (interval=60, market=BCH-EUR, use_potjes=False)
- Config uit `monitor_state.json` werd alleen via `resume_if_was_running()` geladen — maar die skipt als `running:false`
- Effect: elke restart wist Willem's interval/markets/auto_trade instellingen
- Fix (`v7_config_persist_on_init_001`): __init__ leest config uit state file (behalve `running` — die blijft false tot expliciete start)

### 🐛 Bug 3: SELL met filled=0 werd als success gezien
- Bitvavo gaf 200 OK met `filledAmount: 0` (bij te kleine sell na clamp/rounding)
- Onze code registreerde het als success → `close_pot` werd aangeroepen → pot leeg gesloten
- Maar de crypto stond nog op Bitvavo — geld werd "vergeten" in de boekhouding
- Concreet voorbeeld: BTC BUY €5,06 @ €52.840 (01:43), SELL amount=0 @ €53.759 (14:55). €5,06 aan BTC bleef op Bitvavo
- Fix (`v7_zero_filled_guard_001`): `execute_real_trade` returned nu `success:False` met `error_code:ZERO_FILLED` als filled≤0, pot blijft open zodat trader het next cycle opnieuw probeert

### ✨ Nieuw: `/api/trade/reconcile/orphans/{user_id}` (`v7_reconcile_orphans_001`)
- **GET**: dry-run scan — toont per coin op Bitvavo: bv_amount, net_paid_eur (uit trade_history), pnl_after_fee, proposed_action (SELL_PROFIT / REOPEN_POT / SKIP_DUST)
- **POST** met `execute:false` (default) → dry-run preview met `would_execute[]`
- **POST** met `execute:true` → daadwerkelijke uitvoering:
  - `SELL_PROFIT`: verkoop nu + registreer netto in `spark_kasboek` en `pot.stats`
  - `REOPEN_POT`: heropen closed pot met historische entry_price zodat trader retry
  - `SKIP_DUST`: laat staan (pnl < €0,02)
- Safety: `execute` MOET expliciet true zijn om écht te verkopen

### 🔧 Rebalance smart mode (`v7_rebalance_smart_001`)
- `POST /api/trade/potjes/rebalance-from-bitvavo` uitgebreid met:
  - `target_pot_count: int` → smart mode, exact N pots
  - `include_eur_liquide: bool` → EUR-saldo meetellen
  - `default_market: str` → markt voor EUR-only pots (die geen coin-holding hebben)
  - `pot_size` blijft aankoopprijs-per-token (default €5,08 anchor)
- Correcte semantiek: user's tokens × aankoopprijs = pot capital. Rest Bitvavo = systeem-treasury (zichtbaar in `/api/trade/delta`)
- Insufficient-funds guard: fout bij `total_needed > total_available`

### ✅ Testing (iter_43, 100% pass, 15/15)
- Alle 5 fixes bevestigd
- Backend logs schoon, geen tracebacks
- Delta consistency_ok (22 pots = 22 ROAR tokens = 22 circulating)


## 2026-07-01 — Trader schoonmaak: shadow weg, anchors weg, delta-view (`v7_treasury_delta_001`)

### 🧹 Shadow trader compleet verwijderd
- Files deleted: `modules/trade/shadow_pots.py`, `shadow_routes.py`, `data/trade/shadow_pots.json`, `shadow_flag.json`, `tests/test_shadow_trigger.py`
- `server.py`: shadow_pot_router import + include verwijderd
- `monitor.py`: 3 shadow-blocks verwijderd (close-cascade, activate-bodemdetectie, auto-ensure)
- Reden: dood spoor — werkte niet betrouwbaar, te weinig kapitaal om echt te testen

### ⚓ Anchor logic verwijderd (`v7_anchor_removed_001`)
- `ensure_anchors_for_markets()` is nu no-op stub (backwards-compat)
- `_load()`: geen auto-lock van Spark's pot-001 meer bij elke load
- `_init_potjes()`: geen `pot_locked=True` meer bij initiële 10 pots
- `sync_potjes_to_tokens()`: geen `LOCKED_POT_INDEX` check bij expansie
- `rebalance_from_bitvavo()`: geen anchor-remainder pot meer (restant blijft op Bitvavo, zichtbaar via delta)
- `distribute_potjes_over_markets()`: legacy pot_locked skip als defensive (nieuwe pots hebben dit nooit)
- `monitor.py update_markets()`: ensure_anchors call verwijderd
- **State migratie**: Spark's bestaande pot-001 handmatig unlocked in `user_potjes.json`
- **Resultaat**: Spark heeft nu 10 unlocked pots die 1-op-1 mappen aan 10 ROAR-tokens

### 💰 Nieuw endpoint `GET /api/trade/delta` (systeem-treasury view)
- Toont: `pots_capital_eur` (som alle pots), `bitvavo_actual_eur` (live), `bitvavo_staking_eur`, `delta_eur`
- Status categorisering:
  - `in_sync` (|delta| < €0,01) — boekhouding klopt exact
  - `zweeft_op_bitvavo` (delta > 0) — geld op Bitvavo niet in pots (winkel-inkomst / trader-winst / dynamic-price marge)
  - `tekort` (delta < 0) — pot-kapitaal hoger dan Bitvavo (trader-verlies / pending storting)
- Nederlandse `toelichting` bij elke status
- `per_user` breakdown: pot_count, capital_eur, open_positions per user
- `spark_kasboek` totalen (gift_in / omzet_in / btw_reserve / winst_in / uit)
- **Huidige staat**: pots €122,40 + Bitvavo €131,51 = delta €9,11 (coin-restjes BCH/BTC/ETH)

### ✅ Testing (iteration 42, 100% pass, 17/17)
- Delta endpoint shape + Dutch messages verified
- Spark/Willem: exact 10 unlocked pots
- Shadow endpoints geven 404
- Alle bestaande trader-flows werken (bitvavo/balance, history, stats, settings, shop/token/*)


## 2026-06-29 — D&D Gebouw-kaarten verrijkt (`v6_seed_building_cards_001`)

### 🏛️ Stormhaven mini-map gebouwen volledig aangekleed
- 22 gebouw-`game.json` kaarten verrijkt: laag1-4, ws5, tags + avatar-foto's
- Auto-seed pattern (`X — categorie gebouw. Bouwkost: …`) op laag1 vervangen door rijke beschrijvingen
- 6 gebouwen direct gekoppeld aan archief-foto's:
  - Haven → Haven.png, Akker → Akkers.png, Bakker → Bakker huis.png
  - Tempel van Spark → Spark wit logo, Markt → Voedsel Marktkraam.png
  - Gemeentehuis → basis stad.png, Waterput → Waterput.png
- 16 overige gebouwen krijgen `media.placeholder=true` flag voor latere admin drag/drop
- Script `backend/scripts/seed_building_cards.py` is idempotent (overschrijft alleen lege velden)

### 🐛 Bugfix: StormhavenMapView card lookup
- Statische `placeholder: true` flag in `BUILDING_LAYOUT` blokkeerde card-lookup
- `findCardFor()` wordt nu altijd uitgevoerd; placeholder-state is dynamisch op basis van match
- Resultaat: mini-map toont nu **23/23 gebouwen gekoppeld** i.p.v. 0/23



## 2026-06-29 — KB → D&D Brug (`v6_kb_to_dnd_link_001`) + Archief schoonmaak

### 🗑️ Archief duplicaten opgeruimd
- 2 verweesde archive-entries verwijderd (`cc532201b553` Score.png, `d5f30bd8b6b9` High Score.png)
- 2 fysieke `.png` bestanden gewist (~5.9 MB)
- `kbv2-2e9b7f0e` (High Score) `image_urls[]` van 3 → 2 (1 dubbele eruit)
- Archief 153 → 151 entries
- Hidden duplicate: Help.png × 2 echte kaarten (helpen + Help) — laten staan tot user keuze

### 🔗 KB → D&D Brug — 63 KB-kaarten met afbeelding gescand
Mapping-script `v6_kb_to_dnd_link_001` koppelt KB-kennis met game-systeem:
- Detecteert game-relevante concepten via begrip + tags (kleding/wapens/voedsel/schild/etc.)
- Smart slot-detectie: Schoenen→voeten, Broek→broek, Riem→riem, Schild→offhand, Handzwaard→rechterhand, Medaillon→nek
- Smart kind/value: voedsel/wapens/armor/drink/material
- **Geen file-duplicatie**: game-cards verwijzen naar dezelfde `/api/system-archive/file/{id}`
- Bi-directional links: KB heeft `linked_game_card_id`, game-card heeft `footnote.linked_kb_card_id`

**Resultaten:**
- 4 bestaande game-cards verrijkt met KB-afbeelding
- 19 nieuwe game-cards aangemaakt vanuit KB
- 40 KB-kaarten met image overgeslagen (filosofische/abstracte concepten — geen game-meta)
- Totaal D&D game-cards nu: **145**

⚠️ Admin-review nodig in DnD Gallery voor false-positives (bv. "Bakker (gebouw)" kreeg `kind=food` via brood-tag) — kan via bestaande `/api/dnd/spark-world/game-cards/edit` endpoint.


## 2026-06-29 — D&D Economie Fundament (`v6_dnd_economy_001`)

### 🏰 Land/Spark World preview kader (`v6_spark_world_preview_001`)
Nieuwe `LandPreviewPanel` in `DnDCharacterSheet.js` naast `DorpPreviewPanel`:
- Eigen `PaperPanel` met header "SPARK WORLD"
- Achtergrond = D&D-kaart "Spark World"/landkaart (of NL-map fallback)
- Label: `Spark World · 12 provincies · 12 steden · 9 fracties`
- Hover-only "KAART BEKIJKEN" knop → opent bestaande `LandkaartBark`
- Verstopte Landkaart-knop in `FractiesKaderPanel` tab-bar verwijderd

### 🎮 D&D Economie Blueprints (Fase 0)
Nieuwe map `data/dnd/blueprints/` met 6 blauwdruk-JSONs:

1. **`dnd_klassen.json`** — 3 base klassen (voet/afstand/support) met stats_start, beroep_affinity, starting_equipment, hybrid_unlock via beroep-XP
2. **`dnd_beroepen.json`** — 9 beroepen (smid/jager/healer/houthakker/mijner/visser/waterhaler/boer/trader). XP tier 1-5 (0→500→2500→10k→50k), blueprint-unlocks per tier, primary+secondary mechaniek (1 primary + 1 secondary onder uren-budget)
3. **`dnd_grondstoffen.json`** — 24 grondstoffen met `base_value` (basis-prijs in goud), `weight`, `stack_max`, ore-tiers 1-5 (mythril+adamantine)
4. **`dnd_prijscurve.json`** — piecewise-linear: voorraad 0%→10× / 50%→1× / 80%→0.4× / 100%→0.1×, stad_streven 80%, trade_tax 5% naar destination-city
5. **`dnd_dorp_income.json`** — basis 10 vis/graan/log/steen + 5 ijzererts per dorp_level
6. **`dnd_buildings.json`** — 14 gebouw-types (smid/jachthut/kruidenwinkel/houthakkerij/mijn/haven/put/akker/bank/bakker/slager/**trader_post**/**auctionhouse**/barracks) met build_cost en beroep_slots_per_level

### 🃏 Game-cards auto-gegenereerd
48 nieuwe D&D-kaarten in `data/cards/dnd/game.json` met status=draft (placeholder image leeg, admin kan via DnD Gallery editen):
- 24 grondstoffen
- 3 klassen
- 9 beroepen
- 12 gebouwen
Totaal nu 126 game-cards.

### 🛠 Module `modules/dnd/economy.py`
Nieuwe service met endpoints:
- `GET /api/dnd/economy/blueprints` — alle blauwdrukken in 1 call
- `GET /api/dnd/economy/blueprints/{name}` — losse blueprint
- `GET /api/dnd/economy/price/{resource_id}/{voorraad_pct}` — prijscurve-check
- `GET /api/dnd/economy/trader-decision/{stad_id}` — trader-AI advies (idle/buy/sell + score)
- `POST /api/dnd/economy/admin/grant-daily-income` — handmatig daily-tick triggeren

Live getest: 12 steden ontvingen 10/10/10/10/5 in `warehouse_resources`. Prijscurve klopt exact (0%=600g, 50%=60g, 80%=24g, 100%=6g voor ijzererts-T3). Trader-decision = idle want alle steden gelijk → wacht op productie-differentiatie.


## 2026-06-29 — Snuffel-bestand capability (`v6_snuffel_bestand_001`)

### 🔍 Spark Internal File Search
Nieuw: Spark kan op verzoek zijn eigen JSON-data doorzoeken en hits gestructureerd terugmelden.

**Doorzochte bronnen:**
- KB v2 (alle 4 lades + inbox) — privacy-filter op `bron_user_id` voor private kaarten
- Notes — alleen van viewer of zonder owner
- Personality (bijbel, self_awareness, capabilities, modes, origin docs)
- Chat-logs (alleen viewer's eigen logs, laatste 50 conversaties)

**Triggers (fast-path in `response_composer`):**
- `snuffel [naar] X`
- `zoek in (je) bestand(en) naar X`
- `doorzoek je geheugen op X`
- `waar staat info over X?`
- `vind X in je bestanden`
- `kan je snuffelen naar X`

**API:** `POST /api/spark/compose/snuffel` met `{query, viewer_id, scope?}`

**Scoring:** Eenvoudige substring + token-overlap (geen rapidfuzz overhead per file). Begrip krijgt +20 score-boost. Threshold ≥50.

**Performance:** Test "emoties" → 8 hits in 132ms (chat fast-path) / 399ms (directe API).

**Files:**
- `modules/chat/spark_snuffel.py` (290 regels) — detect + execute + format
- `modules/chat/response_composer.py` — fast-path integratie vóór Help-intent
- `modules/chat/compose_routes.py` — `/snuffel` endpoint
- `data/personality/spark_capabilities.json` — capability geregistreerd (status: live)

**Live getest met 4 trigger-varianten:** alle returnen `action=snuffel_bestand` + relevante hits.


## 2026-06-29 — Tab-context + Daily-brief scheduler + 3-file refactor + UI schoonmaak

### 🧹 UI Schoonmaak (KennisbankV2Page.js)
- **Herzien (KB v1) knop verwijderd** — KB v1 is archief sinds 26-06, knop was vestigial
- **Self-audit knop verwijderd** — endpoint hangde >60s op huidige KB-grootte, info ook via Spark trigger "audit kennis"

### 📍 Tab-context naar Spark compose (`v6_tab_context_001`)
- `App.js` tracked actieve tab in `sessionStorage.spark_active_tab` + `spark_last_non_chat_tab`
- `GesprekkenPage.js` stuurt `active_tab` mee in `POST /api/spark/compose`
- `ComposeRequest` (compose_routes.py) krijgt `active_tab: Optional[str]`
- `compose_response()` injecteert `📍 GEBRUIKER KIJKT NU NAAR TAB: **{label}**` in user_prompt
- Live getest: vraag *"laat eens zien"* met `active_tab=agenda` → Spark: *"je bent in de Agenda-tab — wil je overzicht van afspraken?"*

### 📅 Auto-daily-brief scheduler (`v6_daily_brief_scheduler_001`)
- `modules/scheduler/__init__.py` krijgt `_maybe_daily_brief()` task
- Trigger om 02:00-04:00 UTC, idempotent via `scheduler_state.daily_brief_date`
- Scant `chat/logs/user-*.json` op activiteit (≥3 turns, mtime <24h)
- Genereert per actieve user 1 brief via `build_daily_brief()` (max 30/dag voor budget)
- Resultaten in `scheduler_state.daily_brief_results: {success, skipped, errors}`

### 🧹 Refactor `smart_intents_service.py` (1205 → 769 regels)
- Nieuwe `smart_intents_profile.py` (462 regels) bevat: relation_lookup, age_lookup, profile_lookup, _users_data, _resolve_person
- `smart_intents_service.py` re-exporteert profile-functies onderaan voor backwards-compat
- Geen caller-updates nodig — `si.detect_profile_lookup()` blijft werken
- Live getest: *"wie is mijn moeder"* → `Heidi Spakman` ✓

### 🧹 Refactor `chat/routes.py` (2174 → 1845 regels)
- Nieuwe `chat_extra_routes.py` (365 regels) bevat: logs (GET/DELETE), intent matching, snap, lookup, emotions, shadow observer, welcome, relay-inbox
- Eigen APIRouter met `/chat` prefix — FastAPI merged op app-level
- `chat/__init__.py` exporteert `chat_extra_router`
- `server.py` registreert beide routers met `/api` prefix
- Live getest: `/api/chat/logs/user-001/stats`, `/api/chat/emotions/state`, `/api/chat/welcome`, `/api/chat/shadow/stats`, `/api/chat/message` — alle 5 werken
- Lint clean


## 2026-06-29 — Identity-lek fix + Genereer-tunes + response_composer refactor

### 🚨 BUG (P0) — Identity-lek
Spark sprak nieuwe users aan met "Willem" tijdens gradatie-test.

**Root cause** (`response_composer.py`):
1. Regel 736 `_format_turns()`: `role = "Willem" if t.get("role") == "user"` — ALLE user turns gelabeld als "Willem" in history die naar LLM gaat
2. Regel 1068 `## Huidige vraag van Willem:` — hardcoded in user_prompt
3. Geen expliciete "wie spreek je nu" header in system_prompt → LLM nam Willem over uit history

**Fix** (`v6_identity_leak_fix_001`):
- `_format_turns()` neemt nu `user_naam` parameter
- `## Huidige vraag van {naam}:` dynamisch
- System-prompt krijgt `⚠️ WIE JE NU SPREEKT: **{naam}** (gradatie X). NIET Willem...` header bovenaan
- Test bevestigd: `user-ceeba762` (Ron) → "Hoi Ron!"; `user-64bf063d` (Heidi) → "Hoi Heidi!"

### ✨ Genereer (LLM) tunes (`v6_kb_llm_generate_002`)
- Prompt herzien: minimum-eisen ipv alleen max ("12-25 woorden" / "50-90" / "150-220" / "220-320")
- max_tokens 800 → 1800 (voorkomt truncate laag3+4)
- Temperature 0.3 → 0.4 (iets meer variatie)
- Frontend beschermt 4 systeem-tags (`knowledge-snap`, `auto-generated`, `from-diep`, `gap-fill`) bij merge
- LLM kreeg expliciete instructie deze tags NIET in extra_tags te returneren
- Resultaat: 15/37/134/129 woorden ipv ~5/15/50/50

### 🧹 Refactor `response_composer.py` (1212 → 528 regels)
Nieuwe `modules/chat/composer_helpers.py` (695 regels) bevat:
- Alle `_load_*` loaders (KB, bijbel, mode, origin, awareness, help-chain)
- Alle `_format_*` formatters (snap-cluster, self-awareness, KB-cards, turns)
- `_build_system_prompt`, `_load_recent_turns`, `_save_turn_pair`, `_auto_snap_from_diep`, `_load_ops_context`

`response_composer.py` blijft de orkestrator met alleen `compose_response()`. Pure code-move, geen logic changes. Lint clean.


## 2026-06-29 — KB v2 "Genereer (LLM)" knop + login-fix

### 🐛 Login bleef hangen
`backend/modules/kb_v2/llm_generate_routes.py` importeerde `_v2_dir` uit `service.py` — die naam bestaat niet (alleen `V2_DIR`-constant). Backend laadde dus niet, uvicorn luisterde wel op :8001 maar gaf geen response → login bleef "zoeken".
**Fix**: import vervangen door `V2_DIR` met kleine wrapper-functie.

### ✅ Genereer-knop (`v6_kb_llm_generate_001`)
In `KennisbankV2Page.js CardDetail`:
- Nieuwe knop `data-testid="kbv2-llm-generate-btn"` naast "Bewerken"
- Roept `POST /api/kb/v2/cards/{id}/llm-generate` aan (Groq via `llm_router`)
- LLM-voorstel wordt in `editForm` geladen (bestaande velden hebben voorrang)
- Edit-mode opent automatisch → admin reviewt → klassieke "Sla op + classify naar lade" flow
- Loading-state via `llmGenerating`, toast bevestigt provider/latency/voorgestelde lade

### 📊 Backend endpoint geverifieerd
`roofdier` test-call: success in ~2s via Groq, geldige laag1-4 + 5W + extra_tags.


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
