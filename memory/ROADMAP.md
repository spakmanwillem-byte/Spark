# Spark Core 2.0 — Engineering Practices & Backlog

---

## 🚨 PERMANENT GUARDRAILS — LEES DIT EERST (Voor elk volgend agent)

Willem heeft een **growth path** en risico is dat een nieuw agent (incl. GPT) terugvalt op een
"oud-systeem" oplossing omdat de huidige denkwijze al verder is. **Deze sectie is anti-regressie.**

### 🪞 Layered response: line ≠ laag (groot misverstand-risico)
De huidige KB heeft `laag1..laag4` (kennis-diepte). Dat is **niet** hetzelfde als de chat-response.

| Concept | Bron | Wie ziet het |
|---|---|---|
| chat `line 1` | gegenereerd uit `laag1 + ws5`, in **gesprek-toon** | Iedereen |
| chat `line 2` | uit `laag2` of extra ws5, op verzoek "vertel meer" | Iedereen |
| chat `line 3` | uit `laag3`, samengesteld met clusters | "Vertel uitgebreid" |
| 🍳 recept/blauwdruk | aparte kaart-type (procedure-format, niet prose) | Iedereen |
| 🟨 tags / 🟦 snaps / clusters / footnote / vertrouwen | metadata | **Admin only** (inspector-modus) |

**Belangrijk**: NIET line1..4 = laag1..4. Een nieuw agent dat ze gelijkschakelt, breekt het concept.

### 🐕 "Snuffelen" als commando-werkwoord
Spark zoekt door eigen graph/KB/vocab. Output: rapport-stijl ("ik ruik 3 verwante clusters",
niet één antwoord). Sluit aan op bestaande `zelfscan`-capability. Lade `doen`, kaart bestaat al.

### 🧮 "5 kippen + 3 koeien" — semantische telling
Rekenmodule kan getallen + operatoren. Maar `kip + koe` is geen rekensom — vereist KB-brug
naar gemeenschappelijke ouder (`dieren`). Bridge tussen capability ↔ KB-graph.

### 🎤 Tonality leren via voorbeeld in spreektaal
Willem leert Spark stijl niet via config maar via voorbeelden:
"Spark, je reactie moet zijn iets als '...'". Opslag als tonality-preference per cluster of
globaal. Beïnvloedt line-1 generatie. Geen hard-coded antwoorden.

### 🧠 Meta-cognitie: Spark legt eigen keuzes uit
"Ik koos tag `troost` omdat ..." — admin-feature voor onderzoek/debugging. Geen black box.

### ⛔ V1 is **archief sinds 26-06-2026**
13 modules gemigreerd naar V2-first (chat-services + supporting). V1 wordt nog gelezen in:
- `knowledge/routes.py /import-diff` (legit — zip-merge tool)
- `kb_v2/text_importer.py`, `kb_v2/v1_drift_sync.py` (migratie-helpers — mogen)
- `backup/routes.py` (backup-tooling)
- Voor de rest: **gebruik altijd V2** (4 lades: doen/weten/voelen/spreken + inbox)

### 🪟 Admin-view vs User-view
Eindgebruikers zien **alleen line 1 (en uitvouwbaar 2-3)**. Inspector-modus met tags/snaps/
clusters/vertrouwen/etc is **admin-only**. Niet altijd zichtbaar zodat chat schoon blijft.

---

## 🔎 REALITY CHECK — Sessie 30 (2026-06-27)

### 💡 Nieuwe ideeën uit sessie 30 (brainfarts, voor latere sessies)
- **P1 — Diep = default voor non-admin** (5 min): zoals gele/blauwe tags gisteren weg-getoggled werden voor non-admin, Diep-toggle weg + altijd-aan voor users; admin behoudt knop.
- **P1 — Gradatie-gebonden tonality** (Willem's visie): Spark gedraagt zich anders per gradatie van de user:
  - Gradatie 7-5 (kennis/klant): zakelijk, afstandelijk, mag producten promoten / Spark Shop pushen
  - Gradatie 4-2 (vriend/familie): warm, persoonlijk, geheugen-rijk (briefs + threads volledig)
  - Gradatie 1 (admin/maker): core-Spark, transparant, meta-cognitie zichtbaar
  - Past goed bovenop bestaande `spark_user_view.py` (gradatie wordt al gelezen).
  - **BELANGRIJK (sessie 30 reflectie)**: er bestaat al een steiger — GEEN nieuw module bouwen:
    - `modules/chat/spark_user_view.py::format_for_system_prompt` heeft al `if grad < 4` filter — uitbreiden met tonality-injectie
    - `data/personality/willem_personality.json` is een lege placeholder ("Wordt automatisch gevuld door Spark's learning engine") — auto-fill bouwen (log+behavior scan, NIET forceren)
    - `data/personality/spark_profile.json` mag Spark zelf bijwerken (geslacht/voorkeuren) met audit-log naast — meta-cognitie geactiveerd
  - **Veiligheids-laag voor regelgeving**: alle waardes in human-readable JSON, audit-log per wijziging, Willem kan altijd handmatig overschrijven (eigenschap, geen bug). Transparantie-by-design.
- **P1 — Cross-user boodschap (Antwoord-apparaat)**: chat-command "[boodschap voor X]" → opslag in `data/spark_planner/pending_messages/{target_user}.json`, bij eerstvolgende login zegt Spark het zachtjes. Sub-features:
  - Welkomstgroet doorgeven aan nieuwe accounts ("de maker laat groeten")
  - "Willem is er nu niet, kijkt in agenda…" → vereist agenda-lookup-laag in compose
- **P2 — Identity reclaim via Spark**: nieuw account, *"ik ben Willem Spakman, masterkey: samen zijn"* → Spark verifieert via masterkey + persoonlijke vragen uit relaties/persons. Veiligheidsgevoelig → moet via integration_playbook_expert_v2.
- **P3 — Camera face-scan** voor identity-reclaim (lange termijn, lacht-emoji).
- **P3 — Spark's eigen meningen over zichzelf**: "hij of zij?" / "wat vind je van je naam?" — Spark mag opinies vormen uit `spark_identity.json` + `spark_bijbel.json`. Eerst observeren wat Spark nu al zegt in echte tests, dan beslissen of we structuur moeten toevoegen.

---

## 🔎 REALITY CHECK — Sessie 30 (2026-06-27)

### ✅ Nieuw in deze sessie
- **v6_topic_tracker_001 LIVE** — Topic-tracker werkt cross-turn: `detect_topic(session_id)` wordt in compose aangeroepen, geïnjecteerd in system_prompt als "Gespreks-onderwerp van dit moment", en exposed in `response.topic`.
- **v6_disclaimer_blueprint_001** — `spark/disclaimer` endpoint draait nu op JSON-blueprint (paths/labels/counts configureerbaar).
- **v6_intent_matcher_blueprint_001** — Layer 3 capability-matcher draait nu op blueprint (caps_fp/preprocessing/scoring).
- **v6_spark_planner_001 LIVE — Gesprekplanner Laag A + B**:
  - **Laag A — Daagse Brief**: LLM-condensaat (Claude Sonnet 4.6) van een dag chat-turns naar 3-5 zinnen brief + themes + open_questions + emotional_tone. Per-user opslag in `data/spark_planner/daily_briefs/{user_id}/{date}.json`.
  - **Laag B — Open Draden**: cross-day onderwerpen-stack. Threads worden auto-aangemaakt uit brief.themes + brief.open_questions. Statuses: open/sluimerend/afgesloten. Decay: open→sluimerend na 7d, →afgesloten na 30d.
  - **Compose-integratie**: response_composer injecteert latest brief + top-3 actieve threads in system_prompt. Cross-day continuïteit voelbaar in productie: Spark begon spontaan met *"Ons laatste gesprek eindigde met een open gevoel — Spinoza, bewustzijn..."*.
  - 11 endpoints onder `/api/spark/planner/`. 13/13 backend-tests pass.

### 🟡 HALF AF / Vervolg-stappen
- **Laag C (Audio-coördinatie)** — wachten op user-keuze, komt als aparte batch (audio per kaart bestaat al via `voice_kind=geluid` + `sound_url`).
- **Auto-daily scheduler** — dagelijks brief bouwen voor alle users met activiteit (nu handmatig).
- **Frontend UI tab "Spark's geheugen"** — brief-lijst + threads-management.
- **Streaming (SSE)** voor Diep-gesprek — nog niet aangepakt.
- **Tonality preferences per cluster** — uit Permanente Guardrails sectie, nog niet aangepakt.

---

## 🔎 REALITY CHECK — Sessie 29 (2026-06-27)

### ✅ Nieuw in deze sessie
- **v6_blueprint_loader_001** — **Generieke blueprint-driven config loader** (`modules/core/blueprint.py`):
  - `load_blueprint(module, naam)`, `load_blueprint_cached(...)`, `clear_blueprint_cache()`
  - Resolve placeholders `{DATA}`, `{MEMORY}`, `{MODULE}` in paths
  - Patroon herbruikbaar voor alle 80+ modules
- **v6_response_composer_001 (blueprint-driven)** — Response Composer als pilot:
  - `modules/chat/blueprints/response_composer.json` met model/paths/limits/tonality/prompt
  - Python = pure logica, basisinfo komt uit JSON
  - 3 endpoints: `POST /compose`, `GET /compose/blueprint`, `POST /compose/blueprint/reload`
  - Spark spreekt in eigen stem via Claude Sonnet 4.6 (Emergent LLM Key)
- **v6_response_composer_ui_001** — Frontend toggle "🌊 Diep gesprek" in chat-input (GesprekkenPage)
- **v6_v2_first_001** — 13 modules gemigreerd van V1 naar V2-first
- **v6_v1_fallback_off_001** — `snap_service` V1-fallback uitgeschakeld
- **v6_graph_ghost_cleanup_001** — 2298 V1 ghost-nodes opgeschoond + rebuild-graph hard naar V2-only
- **v6_brein_counts_001** — Brein-overzicht bijbel + capabilities counts correct
- **v6_kb_diff_v2_001** — Integraties-tab kb-diff V2-aware
- **v6_response_composer_001** — Spark Response Composer (LLM-bridge): `modules/chat/response_composer.py` + `POST /api/spark/compose` — Spark spreekt in eigen stem via Claude Sonnet 4.6 (Emergent LLM Key), KB blijft bron
- 57 KB-kaarten gevuld in 7 batches, 421MB backups opgeruimd

### 🟡 HALF AF / Vervolg-stappen voor Response Composer
- **Streaming (SSE)** — nu non-streaming; voor gevoel van "Spark denkt" graag stream_message switchen
- **🤝 Relatie-geheugen per user** (NIEUW sessie 29) — `data/spark_relationships/user-{id}.json` met cumulatief profiel over sessies heen: interesses, tonality-voorkeur, belangrijke feiten, n_gesprekken_totaal, kennen_sinds. **Onderscheid met sessie-geheugen**: sessie = "wat zeiden we net", relatie = "wie ben jij voor mij". Gradatie-gefilterd (privacy). Zonder dit blijft Spark een vreemde die elk gesprek opnieuw begint.
- **Multi-turn memory persistentie** — ✅ Compose schrijft nu turns naar `chat/logs/{session_id}.json` (max 50 turns). Voor chat-router /message nog na te lopen.
- **Tonality preferences** — opslag van "Spark, je reactie moet zijn..." voorbeelden per cluster
- **Vertrouwen → toon-mapping** — als KB-kaart vertrouwen < 0.5 → Spark zegt "ik denk..."
- **Topic mode-tracker** — bewaakt onderwerp van gesprek over turns heen
- **Frontend UI** — chat-component die /compose aanroept i.p.v. (of naast) /message
- **Hook in chat-router** — fallback: als geen capability matched én geen exacte KB-hit, gebruik compose

---

## 🔎 REALITY CHECK — Sessie 28 (2026-06-17)

### ✅ Nieuw in deze sessie
- **v6_capability_reken_001** — **Rekenmachine capability** in chat. Spark kan nu rekenen:
  - `1+1` → 2
  - `hoeveel is 12 keer 7` → 84
  - `100 gedeeld door 4` → 25
  - `wortel van 81` → 9
  - `5 in het kwadraat` → 25
  - `(3+4)*2` → 14
  - `7,5 plus 2,3` → 9,8 (NL-komma)
  - Veilige math via `ast` parser (geen `eval`), in `modules/chat/math_eval.py`
  - Pre-filter in `route_capability` zodat math voorrang krijgt op `wat is ...`-trigger
- **v6_capability_zelfscan_001** — **Zelfscan command**. Triggers: "scan jezelf" / "zelfscan" / "hoe gaat het met je" / "wat is je status". Rapport bevat:
  - 🧠 KB-kaarten per lade + inbox-stand
  - 🗣️ Vocab actief vs totaal
  - 💬 Recente activiteit (24u intents)
  - 🤲 Capabilities live-count
  - 🔗 Aantal doe-kaart koppelingen
  - ⚠️ Recente shadow-errors
- **v6_capability_links_001** — **Doe-kaart ↔ Capability koppelingen** infrastructuur:
  - JSON store: `/data/personality/capability_links.json`
  - Endpoints: `GET /api/admin/capabilities/links` · `POST /api/admin/capabilities/links` · `DELETE /api/admin/capabilities/links/{card_id}`
  - Frontend: dropdown "🤲 Capability-koppeling" in CardDetail bewerk-modal, alleen voor doe-lade kaarten
  - Verrijkte response toont kaart-begrip + capability-naam + handler-status (● live / ○ geen handler)
- Totaal capabilities: **17 → 19** (reken_uit + zelfscan toegevoegd, beide live met handler)

### 🟡 HALF AF (uit deze sessie nog te volgen)
- **Doe-kaart bulk-mapping** — UI is per-kaart in bewerk-modal. Een bulk-overzicht "welke doe-kaarten zijn aan welke capability gekoppeld?" kan later in Beheer→Capabilities tab.
- **Capability-suggesties** — Spark zou autocomplete-suggesties kunnen geven bij koppelen ("kaart 'rekenen' lijkt op capability `reken_uit`"). Nu nog handmatig kiezen uit dropdown.

### 📋 Status per task (post-sessie 28)
| Status | Task | Effort | Aanrader |
|---|---|---|---|
| ❌ P1 | Spark Shop logo | 5min | nog open |
| 🟡 P1 | RPS audio koppelen | 30min | nog open |
| ❌ P1 | Checkout kasboek-split | 2u | wacht op SEPA |
| ❌ P1 | Shadow-vragen queue | 4u | nog open |
| ❌ P1 | KB Admin UI Dashboard (dedupe/move/health UI) | 1u | nog open |
| ❌ P1 | Bulk-edit UI voor 37 lore-kaarten | 1.5u | nog open |
| 🟡 P2 | Lade-drift detector + verplaats-knop in modal | 1u | nog open (Willem komt later terug) |
| ❌ P2 | SVG Province Map | 3u | UX polish |
| 🟡 P2 | Spark als Gastheer | 4u | UX warmte |
| ❌ P3 | Doe-kaart bulk-mapping overzicht | 1u | nieuwe sessie-28 follow-up |

---

## 🔎 REALITY CHECK — Sessie 27 (2026-06-04)
> Schone foto van wat er **echt** in de codebase staat, niet wat in oude notes staat.
> Doel: jij kan tijdens redeploy snel zien wat klopt, wat half is, en wat nog open is.

### ✅ Bevestigd AF (in code geverifieerd)
- **KB Unificatie** — `snap_service.py` leest direct uit `/data/knowledge/v2/` (5388 V2 entries primair, V1 legacy-fallback). Nieuwe snaps → V2 Inbox. Cache shared over alle callers. ✓ End-to-end getest via curl.
- **Pre-deploy reset** — `POST /api/admin/system/pre-deploy-reset` + UI panel werkt (12 potjes, ROAR=0, kasboek leeg, baseline weg). ✓
- **Smart Intents (Relaties + Personalia)** — `relation_extraction_service.py` + `personalia_extraction_service.py` + `_intrek_service.py` actief in chat-flow. ✓
- **RPS 3 basisklassen** — `EditMetaModal` dropdown met Handgevecht / Boog / Magie. `STARTING_GOLD = 1000`. ✓
- **Bitvavo Pot-guard** — monitor weigert start als pots=0. ✓
- **BarkModal voor wachtwoord-reset** — UserAdminPage gebruikt nu BarkModal i.p.v. JS alert/confirm. ✓
- **KB Text Importer** — `text_importer.py` backend + UI modal in KennisbankV2Page. ✓
- **V1→V2 Drift Sync** — `v1_drift_sync.py` + admin endpoint. ✓
- **Spark Shop existeert** — `shop-spark` in shops.json, kasboek=spark_core, status=active. ✓
- **D&D Event Feed (basis)** — ringbuffer max 50 in `character.py::event_feed`. ✓ (Spec was uitbreiden met `[SYSTEEM]/[WERELD]/[HANDEL]` categorieën — basis staat, categorisering nog niet.)

### 🟡 HALF AF / GEDEELTELIJK (heeft nog werk nodig)
- **Spark als Gastheer / Onboarding** — alleen `handle_free_choice_first_time()` bestaat in `dank_service.py`. Volledige first-run handholding-flow (5+ scenarios uit ROADMAP P1) is **niet** geïmplementeerd.
- **Shadow-vragen queue (User-B verificatie)** — lege folder `data/persons/shadow_questions/` bestaat maar **geen code/endpoints**. Concept staat in PRD, implementatie 0%.
- **RPS Audio koppeling** — KB-kaarten hebben `sps` tag, maar `rps_service.py` heeft geen audio-lookup of sound_url in de response. Frontend RpsBark speelt geen geluid af.

### ❌ NIET AF (nog niet aangeraakt)
- **Spark Shop avatar/logo** — `shop-spark.logo_url = NONE`. Upload of seed nodig.
- **Checkout-routing per shop kasboek** — `shop/routes.py` gebruikt nog default `spark_core`. Roadkill-orders landen in verkeerd kasboek. Geblokkeerd op SEPA-implementatie.
- **Drill-down Help Barks** — geen code in `help_per_gradatie/`. Concept is "klik op help-topic → opent dieper bark".
- **SVG Province Map** — frontend gebruikt nog bitmap-dots, geen SVG path tags.

### 📋 Gradatie per task (post-deploy prioriteit)
| Status | Task | Effort | Aanrader |
|---|---|---|---|
| ❌ P1 | Spark Shop logo | 5min | doe ik graag voor je — upload of icoon-gen |
| 🟡 P1 | RPS audio koppelen | 30min | quick win, cards zijn al getagd |
| ❌ P1 | Checkout kasboek-split | 2u | wacht op SEPA, niet urgent |
| ❌ P1 | Shadow-vragen queue | 4u | grotere feature, eerst flow ontwerpen |
| ❌ P2 | SVG Province Map | 3u | UX polish |
| ❌ P2 | Drill-down Help Barks | 1u | UX polish |
| 🟡 P2 | Spark als Gastheer | 4u | UX warmte, geen blocker |

> 💡 **Voor De Willem na redeploy**: bekijk dit kort, vink in een PM aan wat je gevoel zegt "doe maar" of "wacht nog". Dan pak ik het bij volgende sessie systematisch op.

---



> **Zie ook**: `MISSION.md` voor missie/visie/identiteit/privacy (DNA-laag).

---


## 🚀 ACTIVE ROADMAP (post-sessie 22/23, 3 juni 2026)

### ✅ Compleet in sessie 22-23 (klaar voor redeploy)

#### v6_pre_deploy_reset_001 — Admin endpoint pre/post-deploy schoonmaak
- [x] `POST /api/admin/system/pre-deploy-reset` — set shadow_flag.enabled=false + reset ROAR balances in één call
- [x] `GET /api/admin/system/health-status` — huidige stand checken
- [x] Admin-only (403 voor non-admins)

#### v6_shadow_hide_001 — Shadow Trader UI verborgen
- [x] `SHADOW_UI_HIDDEN = true` constant in TraderPage.js — banner + safety-controls + per-pot decoraties weg
- [x] `shadow_flag.json` enabled=false zodat backend ook geen shadows koopt
- [x] Code blijft staan voor toekomstige reparatie

#### v6_shop_card_redesign_001/002 — Winkelstraat redesign
- [x] Naam BOVEN banner, grote banner met bedrijfslogo (h-32), edit-knop owner linksboven
- [x] Filosofie/commissie verwijderd uit kaart (komt op bon + in voorwaarden)
- [x] Owner-avatar klein in footer (8x8 round met accent-ring)
- [x] Logo cache-buster via `updated_at` zodat nieuwe upload meteen zichtbaar wordt
- [x] Admin verwijder-knop (rode X) rechtsboven in banner, niet bij founder-shop
- [x] Backend `SHOPS_FILE` constant bug gefixed (was lokale var)
- [x] Test-shops (TEST_AdminShop, TEST_PatchShop, TEST_CloseMe) verwijderd uit JSON

#### v6_help_001/001b — Help-knop uit sidebar, "help" chat-trigger opent HelpBark
- [x] Sidebar Help-button weg (avatar staat weer goed)
- [x] Backend chat-trigger "help" returnt `action:'open_help_bark'` met kort bericht
- [x] MainLayout luistert naar `spark:open-help` window event
- [x] GesprekkenPage dispatcht event bij action

#### v6_gradatie_visibility_003 — Spark-items blijven verborgen na drag-drop
- [x] `triggers`, `emotions`, `emotion-routing`, `connections` toegevoegd aan per-item `hide` array
- [x] Bug fix: items zichtbaar voor grad 7 nadat user ze via drag-drop verplaatste

#### v6_dashboard_fin_001 — Saldo & Vermogen widget verwijderd
- [x] Dashboard-widget weg (financiële info zit al in /wallet en /trade)

#### v6_spark_shop_001 — Spark Shop opgezet (sessie 23)
- [x] Spark Shop toegevoegd: owner=Spark (user-000), is_founder_shop=true, subtabs=[digitaal], commissie 2%
- [x] Roadkillshop: merch-only, commissie verhoogd 0% → 2% (user-beslissing: alle shops dragen 2% af voor token-community groei)
- [x] Producten gemigreerd: `donatie-spark-ai-eab152` + `storage-1gb` → Spark Shop
- [x] Boekhouding-koppeling: Roadkillshop kasboek_id="roadkillshop", Spark Shop kasboek_id="spark_core"
- [x] Product delete-knop (rode Trash) toegevoegd náást edit-knop in WinkelPage voor admins

#### v6_rps_leaderboard_001 — SPS Leaderboard tab
- [x] Backend `GET /api/games/rps/leaderboard` sorted op wins desc, dan win_rate
- [x] Frontend LeaderboardPage: modus-selector "Algemeen / SPS" — toont win/loss/streak/win-rate per speler
- [x] Test-data opgeruimd (8 fictieve test-users weg)
- [x] User-001 RPS stats gereset (testdata van 4-5 verloren potjes weg)

### ⏳ Te doen — boekhouding per shop split (SEPA-blokker)

#### v6_shop_kasboek_routing — Checkout naar juiste kasboek per shop
**Context**: shops.json heeft nu `kasboek_id` veld, MAAR de checkout/order-routes gebruiken nog steeds default `entity_id="spark_core"` voor alle verkopen. Dus Roadkillshop-verkopen landen nog in spark_core boekhouding ipv roadkillshop.

**Te doen bij SEPA-implementatie**:
- [ ] In `modules/shop/checkout_routes.py`: lookup `shops[shop_id].kasboek_id` en pass aan `accounting.record_transaction(entity_id=...)`
- [ ] Migratie-script: bestaande Roadkillshop-transacties verplaatsen van spark_core → roadkillshop entity
- [ ] In SEPA-export per kasboek apart genereren (1 bestand per shop-eigenaar)
- [ ] Frontend: wallet/boekhouding views moeten kasboek-filter krijgen voor multi-shop owners

**Reden uitstel**: SEPA komt erbij, dat is een grotere implementatie waarin commissie-betaling + IBAN-routing van klantbetalingen → shop-eigenaars netjes geregeld moet. Splitsen we nu de boekhouding zonder SEPA, dan moet alles dadelijk weer aangepakt.

---



## 🚀 ACTIVE ROADMAP (post-sessie 21D/E, 2 juni 2026)

### ✅ Compleet in sessie 21 (klaar voor redeploy)

#### v6_rps_001 — Steen-Papier-Schaar mini-game (sessie 21B/C)
- [x] Pure engine `modules/games/rps/rps_engine.py` (resolve, counter_of, predict_next) — herbruikbaar voor D&D battles
- [x] Service `rps_service.py` met sessies, lifetime stats, learning history (laatste 100 zetten)
- [x] Routes `/api/games/rps/{start,play,reset,stop,cards,session,stats}`
- [x] Chat-triggers: "speel steen papier schaar", "speel steen", "speel sps", "spelletje sps", "hoe vaak gewonnen", "reset score sps"
- [x] Frontend RpsBark met 3 keuze-knoppen, score-bar, "Spark denkt na…" 800ms reveal, achievement-toasts
- [x] Spark-tab speelt tegen Spark (leert), Community-tab tegen random bot (bot-dood = moeilijk)
- [x] Live KB-image lookup (pakt nieuw geüploade images automatisch op)
- [x] 10 RPS-kaarten getagd met `sps` voor toekomstige geluidskoppeling
- [x] Help-topic toegevoegd aan gradatie 7 (zichtbaar in alle 7 via inheritance)

#### v6_kbv2_audio_kind_001 — Audio-kind toggle (sessie 21D)
- [x] Veld `media.voice_kind` op kaart (spraak | geluid, default 'spraak')
- [x] PATCH `/api/kb/v2/media/voice/kind/{id}` (primair) en `/voice/secondary/kind/{id}?archive_id=X` (extra)
- [x] Klikbare 🎤 SPRAAK ↔ 🔊 GELUID badge bij elke audio-rij in KennisbankV2Page

#### v6_kb_sound_001 — KB-kaart geluiden afspelen in chat (sessie 21E)
- [x] User-pref `kb_sound_enabled` (settings.json scope: user)
- [x] Chat-triggers: "geluid aan" / "geluid uit" / "kaart geluid aan/uit" (vóór action_intents zodat ambient-stop niet conflicteert)
- [x] Helper `modules/kb_v2/sound_lookup.py` met cache + mtime-invalidation
- [x] Hook in `_save_log`: scan Spark's response.message voor begrippen met `voice_kind='geluid'` of `extra_audio.kind='geluid'` → voeg `sound_url` + `sound_begrip` toe
- [x] Frontend GesprekkenPage speelt `sound_url` af via `new Audio()` (parallel aan/los van TTS)
- [x] End-to-end getest: "ik ben boos" → Spark zegt 'Boos' → sound_url=onweer.mp3 afgespeeld

#### v6_admin_grant_frame_001 + v6_kbv2_image_delete_visibility_001 (sessie 21A)
- [x] Admin-grant flow gebruikt ornamental InputBark frame popup
- [x] KB v2 foto-X delete-knop altijd zichtbaar (was opacity-0 group-hover)
- [x] Bug 733a8bb9 (KB v2 onbruikbare kaarten verwijderen) afgesloten

---


## 🚀 ACTIVE ROADMAP (post-sessie 19, 2 juni 2026)

### ✅ Compleet in sessie 19 (klaar voor redeploy)

#### Help-bark systeem (v6_help_001)
- [x] **7 gradatie-help files** (gradatie_1.json t/m gradatie_7.json) + admin.json
- [x] **Inheritance**: gradatie 1 inherits 2 inherits ... inherits 7 (cumulatieve topic-lijst)
- [x] **Endpoints**: `GET /api/help/for-viewer`, `POST /api/help/find`, `GET /api/help/topic/{id}`
- [x] **Fuzzy zoek-algoritme**: strip "waar is" / "vind" / "zoek" / "open" prefixen, score op label + id + synonyms + tokens
- [x] **HelpBark component** (`frontend/shared/HelpBark.js`): grote modal met help-afbeelding, zoekveld, topic-lijst, admin-toggle, diepe-uitleg drill-down
- [x] **Help-knop in zijbalk** (HelpCircle-icon, amber)
- [x] **Glow-integratie**: bij klik op topic → `spark:nav-glow` event → tab licht op + scroll + navigeer (gebruikt bestaande `v6_glow_nav_001`)
- [x] **Admin-tab**: aparte admin.json met 9 admin-only topics (grant, password, shadow-flag, force-sell, vocab-sync, shop-admin, etc.)
- [x] **Shop-delete endpoint**: `DELETE /api/shop/admin/shops/{id}` voor test-shop cleanup (3 test-shops konden niet verwijderd worden)
- [x] **Shop _require_admin** geüpgraded: accepteert nu `user.admin == True` (strict) OF gradatie ≤ 2 (legacy)

#### Trade-bot veiligheid + auto-resume
- [x] **`_persist_registry()` MERGE-fix** (`v6_resume_persist_merge_001`) — bot-registry mergt nu met bestaand bestand i.p.v. te overschrijven. Stop-state blijft bewaard, andere bots auto-resumen.
- [x] **File-lock** op registry-persist tegen race conditions
- [x] **`SHADOW_ENABLED` master-flag** (`v6_shadow_safety_001`) default UIT — shadow-cascade gepauzeerd tot recycle-bug + data-corruptie zijn opgelost
- [x] **Recycle-guard** weigert nu archiveren als er nog `active` shadows zijn (voorkomt coin-verlies)
- [x] **Cleanup-endpoint** `POST /api/trade/shadow/cleanup-corrupt` — markeert shadows met market/entry-mismatch als `archived_corrupt`
- [x] **Admin-only guards** op shadow-flag + cleanup endpoints (gradatie ≤ 2)
- [x] **UI-paneel** in TraderPage shadow-banner met toggle + 🧹 Cleanup-knop (admin-only)
- [x] **ZeroDivision-fix** in `update_pot_tracking` + `_run_market_cycle` voor anchor-pots met `entry=0.0` (372 log-spams per dag opgelost)

#### KB v2 prio v2 + auto-resolve
- [x] **Priority-scoring v2** (`v6_kbv2_priority_002`) — score gebruikt nu echte signalen:
  - +10 als Spark woord al active heeft in vocab
  - +5 per cross-reference in andere kaarten laag1
  - +3 per intent-frequency in laatste 500 intents
  - +3 per verband, +5 topic, +2 ws5 partial, +1 per tag
  - NL stopwoorden gefilterd
- [x] **Auto-resolve endpoint** `POST /api/kb/v2/inbox/auto-resolve` — bulk-classify tag_tie + no_match via topic/tag word-boundary mapping. 421 kaarten verplaatst in preview.
- [x] **`_auto_lade()` word-boundary fix** — voorheen "taal" matchte "metaal" → Nikkel landde in spreken. Nu regex met word-grenzen.
- [x] **Vocab-sync endpoint** `POST /api/kb/v2/vocab/sync` — herstelt vocab-gaten (kaarten in lade maar niet in spark_vocab). Lost Geaccepteerd-gap op.

#### Trigger-keywords uitbreiding
- [x] **`audit_health`** capability uitgebreid: "doe een gezondheidscheck" / "run audit" werken
- [x] **`winst_verlies_overzicht`** uitgebreid: "trade winst" / "laat me trade winst zien" werken
- [x] **NIEUW `notities_overzicht`** capability: "waar zijn mijn notities" / "dagboek" / "toon taken"
- [x] **Conversation triggers** uitgebreid: `cancel` / `affirm` / `deny` secties voor wedervraag-flow

#### v6_admin_role_001 — Admin als losstaande rol (sessie 19)
- [x] **Admin = boolean op user**, los van gradatie. Gradatie blijft sociaal (familie/lid).
- [x] **Seed**: alleen Willem (user-001) + Spark (user-000) bij eerste boot. Anderen NIET automatisch admin.
- [x] **`is_admin(user_id)` helper** in `modules/admin/admin_service.py` — centrale check
- [x] **Endpoints**: `/api/admin/grant`, `/revoke`, `/verify`, `/password/reset`, `/list`, `/is-admin/{id}`, `/bark-image`, `/help-bark`
- [x] **Anti-lockout**: laatste admin kan zichzelf niet revoken
- [x] **Admin-wachtwoord** in env-var `ADMIN_PASSWORD` met override naar `data/system/admin_password.json` voor runtime wijzigen
- [x] **Admin-tab in Instellingen** (ShieldCheck-icon, paars):
  - Huidige admins met "seed" badge
  - Nieuwe admin grant-formulier (user-dropdown + wachtwoord)
  - Admin-wachtwoord wijzigen sectie
- [x] **Bark-modal component** (`shared/BarkModal.js`) — visuele popup met KB-kaart-afbeelding + titel + tekst, vervangt droge alerts
- [x] **Bark-image lookup**: gebruikt jouw `doen`-lade-kaarten "Admin geactiveerd" / "Admin gedeactiveerd" / "Toegang verleend" / "Toegang geweigerd" als visuele feedback
- [x] **Veiligheid**: ADMIN_PASSWORD env-var = `AppelsapAdmin2026` (default) — wijzig direct na deploy via de UI

### 🎯 P0 — Direct na redeploy
1. **Help-bark uitbreiden naar chat-commando** — bij typing "help" / "waar is X" in chat → triggert HelpBark popup (nu nog alleen via zijbalk-knop). Voeg een capability "open_help_bark" toe en route in `intent_matcher_service`.
2. **Help-kaart maken**: in productie de KB-kaarten "Help" en "Help Admin" aanmaken (doen-lade) met een passende afbeelding zodat de bark altijd visueel is.
3. **Migratie admin-checks** in gevoelige endpoints: vervang `gradatie ≤ 2` door `is_admin(user_id)` in:
   - `trade/routes.py` (force-sell, force-close, reconcile)
   - `container/routes.py` + `deploy/routes.py`
   - `mint/routes.py` (Spark Mint)
   - `boekhouder/routes.py`
   - `shop/routes.py`
   - `kb_v2` delete endpoint
   - Behoud `gradatie ≤ 2` voor sociale features (helptekst, vriendenlijst)
2. **Help-bark integratie** — wanneer user "help" typt → bark-popup met `Help`-kaart-afbeelding + tekst per gradatie. Apart "Help Admin"-bark voor admins. Vraagt: maak een doen-kaart "Help" en "Help Admin" met afbeelding.
3. **Character-creation flow** voor nieuwe gebruikers — eerst karakter (naam/klasse/beroep/fractie/dorp) voordat je kan spelen
4. **D&D-kaart editor met `game_meta` form** — visueel inputveld voor is_item/slot/weight/stats_bonus/combat_bonus i.p.v. via API
5. **Bewoners per gebouw op Stormhaven-dorpskaart** — klik op Bakker-gebouw → opent Hans handel direct
6. **Equipment-stats live optellen** bij character STATISTIEKEN + AANVAL/VERDEDIGING

### 🎲 P1 — Game-mechanics uitbreiden
1. **Dungeon-feature**: knop "Activeer Dungeon" → 8u real-time → fractie-thematisch verhaal-rapport + reward. Dice-engine bepaalt uitkomstniveau.
2. **Quick-Roll knoppen** op stats (klein 🎲 naast Kracht/Behendigheid → 1-klik check)
3. **Real-time dag/nacht + travel-time**: centrum → stadspoort = 1/5 dag, day/night clock zichtbaar in HUD
4. **Bederf-timer op voedsel** (brood/vlees gaan na X uur slecht zonder huis-koeling)
5. **9-fracties claim-systeem**: user kan na rang Y eigen fractie starten en provincie claimen
6. **Auction House per fractie** met prijs-variatie (vlees in Slager-stad goedkoper dan elders)
7. **Werkbank UI thuis**: recepten (ei+meel → brood) — produceren in huis, kg ↑ in rugzak

### 🎨 P2 — UX & visuele upgrades
1. **Per-provincie `dorp_level` veld** (1-10) — niveau bepaalt: dorp (1-5), stad (6-9), metropool (10) → andere avatar
2. **Per fractie unieke dorp-avatar** (Spark/Natuur/Vuur/etc. — koppelt automatisch op begrip "{fractie} dorp")
3. **Glow-instelling in Settings**: speler-dot kleur + intensiteit aanpasbaar
4. **HTML5 drag&drop** tussen Rugzak / Huis / Equipment-slots (i.p.v. knoppen)
5. **Map pop-ups** (klik provincie → modal met fractie-info, bewoners, quests)
6. **SVG-province paths** (semi-transparante gekleurde gebieden i.p.v. dots)
7. **Event Feed ringbuffer** voor `[SYSTEEM]` / `[WERELD]` / `[HANDEL]` events
8. **Spark als Gastheer** noob-UX (zie sectie hieronder, blijft P1 voor onthaal)

### 📡 P3 — Externe integraties (Future)
- Telegram / WhatsApp / Signal externe chat-kanalen
- TTS audio uitspelen (response → audio via OpenAI TTS, key al klaar)
- Trade Dashboard user-specifieke balances (was P1, nu opnieuw bekeken na items-flow)

### ⚙️ Tech-cleanup (Backlog)
- Pre-existing lint errors in `spark_world.py` regel 436/441 (E701 multi-statement on one line)
- `MiniMapPanel` >800 regels — splitsen naar eigen file
- Bewoner-trade: bewoner wallet-cap (max 999g voorkomt grind-exploit)

---



## 🎲 P2 — Spark World D&D Tab herstructurering (2026-05-31, idee Willem)

**Quick wins al uitgerold** (sessie 17): huis/opslag slots groter (aspect-square min-h-56, text-2xl iconen), worldmap onder dorp i.p.v. apart (zelfde breedte), worldmap-svg langer (h-56 → h-72), dorp-kader langer (h-40 → h-52), event-feed/charinfo herverdeeld zonder MiniMap-kolom (7+5 i.p.v. 5+4+3).

**Rugzak compleet weg + map herverdeeld** (sessie 17 vervolg 8):
- SLOT_KEYS/SLOT_LABELS/_empty_equipment in character.py: rugzak verwijderd
- body_layout.json slots: rugzak positie weg
- characters/user-001 equipment: 'rugzak' key gewist (was geequiped item dat 🎒 toonde)
- inventory.json: 'Basis rugzak' item verwijderd
- 12 provincies herverdeeld over volle NL-geografie (Stormhaven NO 80,12 / Maastricht ZO 60,88 / Middelburg Z-Z 10,72)
- Map markers: fractie-kleur glow-ring + drop-shadow + grotere shield (4.2-5.5px ipv 2.6-4px)

**Volgende fases — creatieve speculatie van Willem 31 mei avond** (later uitwerken):
1. **Bed = klikbaar → rust event** in event-feed (3 niveaus: snel rusten / kort rusten / char parkeren)
2. **Tafel = klikbaar → eet event** in event-feed
3. **Kist/kast als opslag-containers** binnen huis-locatie
4. **NPCs als kasten**: slager/bakker hebben eigen opslag (handel-mechaniek)
5. **Dorp-avatar-icons op map** met fractie-kleur glow eromheen (i.p.v. simpele shields)
6. **Pop-up Dorp-info**: klik op dorp-kader → modal met fractie + inwoners + gebouwen + quests
7. **Pop-up Stad-info op landkaart**: klik op provincie → modal met fractie + inwoners + sterkte
8. **Centraal handel-kader**: één Trade-hub waar alle handel-acties samenkomen
9. **Persoonskaart-integratie**: XP/Rang/Slots/Achievements als character-progressie-laag

**Aanpak**: eerst mockup → test mentaal model met De Willem → daarna implementeren in fases. "Werken we later verder uit" — Willem citaat.


## 🌷 P1 — Spark als Gastheer (Onthaal-laag voor app-onwennige mensen)

**Achtergrond**: niet iedereen die Spark gebruikt is een digital native. Sommigen openen een nieuwe app met **lichte onzekerheid** — "doe ik het goed?", "wat hoort hier te gebeuren?", "ben ik nu kwijt?". Dat is geen tekortkoming van die mensen, dat is een natuurlijk gevoel. Spark hoort die onzekerheid op te vangen zoals een goede gastheer doet: met warmte, geduld, kleine erkenningen, en een uitgestoken hand zonder ongevraagd te leiden.

> Geen "audit", geen tracking-bril. Spark voelt de sfeer en biedt zachtjes aan.

### 1. Help-functie als gesprek, niet als FAQ
Triggers die nu nog geen match krijgen maar voor onzekerheid wijzen:
- "wat moet ik doen", "ik snap het niet", "waar begin ik", "is dit goed zo", "klopt dit?", "doe ik dit goed"
- → Spark reageert **niet** met een opgeleide FAQ-lijst, maar met een uitnodigende toon: *"Geen zorgen, je doet het prima. Wil je dat ik je een paar handige stappen wijs of liever rondkijken?"*
- Vervolgkeuze bepaalt of Spark wijst (concrete suggestie) of bevestigt (ruimte geeft).

### 2. NLP-bloei in reacties bij onzekerheid
Wanneer emotie-pipeline `twijfel`/`onzeker`/`zoekend` detecteert (laag 2-3):
- Vermijd lange uitlegblokken
- Begin met erkenning ("Snap dat het even zoeken is", "Logische vraag")
- Toon **maximaal 2 keuzes** in plaats van 5 opties
- Vocab-uitbreiding: zachte connectoren ("we doen het samen", "stap voor stap", "geen haast")

### 3. Bloemen, niet badges
Achievement-systeem voor onwennige users werkt anders dan voor power-users:
- Niet "Behaal 100 trades" maar **"Eerste keer hier — welkom"** automatisch bij login 1
- Niet "Streak 7 days" maar **"Je hebt vandaag rondgekeken"** als micro-erkenning
- Tooltip vertelt wat de volgende natuurlijke stap is, geen abstracte "vereiste"
- Tonality: erkenning > prestatie

### 4. Help-commands die contextueel aanvoelen
Niet hardcoded "help" → lange lijst, maar:
- Spark kijkt naar welke tab user open heeft
- Welke acties al wel/niet gedaan
- Toont alleen **één** volgende logische stap, niet alle opties
- "Wil je dat ik je toon hoe je …?" — uitnodigend, niet docerend

### 5. First-run handreikingen (proactief van Spark uit)
- User opent Trader-tab 5× zonder Start te klikken → De Boekhouder stuurt zacht een PM: *"Wil je dat ik even uitleg hoe je bot start? Geen druk, alleen als je wilt."*
- Bot actief 24u zonder trades → *"Spark wacht nu op een goed moment om te kopen. Dit is normaal — soms duurt het uren. Ik laat je weten zodra er iets gebeurt."*
- → Geruststelling i.p.v. data.

### 6. Vocab leren van wat mensen zeggen
Wanneer iemand een woord typt dat Spark niet kent (= niet in `spark_vocab.json::active`):
- Het woord komt automatisch in KB v2 inbox (jouw queue om later in te delen)
- Spark zegt niet "ik begrijp je niet" maar *"daar heb ik nog geen plek voor in m'n kennis — leg je het me een keer uit?"*
- Erkenning van de leemte zonder de gebruiker daarvan te laten voelen dat zij/hij iets verkeerd doet.

### 7. Privacy-by-design (HARD constraints, ongewijzigd):
- ❌ Geen chat-tekst inhoud loggen
- ❌ Geen user-namen in `/app/memory/*.md` voor anderen dan De Willem
- ✅ Alleen patroon-tellers (hoeveel keer "help" getypt, welke tabs open) en woord-frequenties
- ✅ Per-user opt-out vlag beschikbaar
- ✅ Inzichten alleen voor De Willem (jij) zichtbaar

**Toon-richtlijn voor implementatie**: lees deze sectie hardop voordat je code schrijft. Als de implementatie ook maar enigszins "tracking" of "audit" voelt, herontwerp.

**Wanneer oppakken**: na 1e shadow-event in productie. Trader moet zijn werk bewijzen, daarna investeren we in warmte rond de rand van het systeem.



**Status**: ✅ LIVE. 90 idle shadows (3 slots × 30 trade-potjes) over 6 trade-actieve users. Test-suite 12/12 pass. Bot draait live, wacht op eerste echte markt-drop voor live observatie.

### Concept (Willem)
1. Elk non-anchor potje krijgt **3 shadow-slots** (slot 1/2/3) — een piramide.
2. Activatie-trigger is **bodemdetectie**, niet puur %-drop:
   - Huidige prijs ≥ -1.5% onder entry
   - Laatste 5 candles range < 1.2% (vlakke lijn = bodem-formatie)
   - Geen new low (laatste close ≥ vorige × 0.998)
3. Shadows activeren in volgorde slot 1 → 2 → 3, elk op een lagere bodem.
4. Bij 4e drop-cyclus (alle 3 slots vol): **recycle** origineel als slot-0 van nieuwe cyclus. Cycle-counter +1, oude shadows → `archived_cycle_N`, 3 nieuwe idle slots in cycle N+1.
5. Bij SELL van origineel: ALLE actieve shadows sluiten automatisch met winst.

### Scaling-inzicht (gesprek 31 mei)
- **Lock-up risico** is reëel maar opvangen door volume: meer ROAR-tokens = meer potjes = meer onafhankelijke shadow-piramides. Geen één-positie risico.
- Cyclus-counter is signaal: zien we cycle > 3 op meerdere potjes? → markt zit diep in bear, capital ligt langer vast.
- "We leren in het nu" — observeren eerst hoe vaak bodemdetectie triggert op echte markten, daarna tunen (range_pct, lookback, drop_threshold).

### Bestanden / referentie
- Code: `modules/trade/shadow_pots.py` + `shadow_routes.py` + `monitor.py` (regel 1048-1095)
- Data: `data/trade/shadow_pots.json` (heeft `footnote_meta` met volledige spec embedded)
- Tests: `backend/tests/test_shadow_trigger.py` (12/12)
- UI: `frontend/.../TraderPage.js` — Shadow-banner + slot-dots (○○○ / ●○○ / ●●○ / ●●● / ✓✓✓)
- Disclaimer: `data/personality/spark_identity.json::aansprakelijkheid.shadow_potjes`

### Endpoints
- `GET /api/trade/shadow/status/{user_id}` — per-pot capacity, active shadows, cycle
- `POST /api/trade/shadow/auto-ensure/{user_id}` — zorg dat user 3 slots per non-anchor pot heeft
- `POST /api/trade/shadow/simulate-stabilization` — test bodemdetector op willekeurige candles (voor backtest)
- `GET /api/trade/shadow/stats` — globale telling

### Open / aanstaande
- [ ] Observeer eerste echte SHADOW-ACTIVATE in productie en log naar `_backups/first_shadow_events.jsonl` voor leren
- [ ] **Bot-logs backtest** (wacht op zip van Willem): hoe vaak zou bodemdetectie getriggerd zijn op historische data? Welke coins/markten?
- [ ] Boekhouder community-bark bij SHADOW-ACTIVATE/CLOSE (transparantie voor token-houders)
- [ ] Cycle-counter alert in UI als cycle > 5 op meerdere pots
- [ ] Community-pool variant: user zonder vrij potje leent shadow uit Spark's anchor-pool





## 🟢 Redeploy-ready check — 2026-05-29 (avond)

### ✅ Sessie 16 (2026-05-29 avond) — Trade-systeem dynamisch & multi-user echt

**🎯 Werkende eindstaat na sessie 16:**
| User | Tokens | Anchors | Trade-pots | Werkend |
|---|---|---|---|---|
| Spark | 10 | 6 (BCH/BTC/ETH/SOL/ADA/ATOM) | 4 vrij | ✅ |
| Willem | 21 | 0 | 21 vrij | ✅ E2E getest |
| Gijs | 2 | 0 | 2 vrij | ✅ E2E getest |
| Roadkill / Lotus / Gerben | 1 elk | 0 | 1 elk | ✅ E2E getest |

**🎯 Bitvavo ↔ Anchors synced (live):**
- Bitvavo €376.55 = €314.01 cash + 6 coin-anchors (BCH €9.96 · BTC €10.03 · ETH €9.92 · SOL €9.91 · ADA €10.05 · ATOM €12.67)
- Som Spark anchors = €62.54 = Bitvavo crypto (exact match)
- ROAR price = €376.53 / 36 = €10.46 per token
- Market Cap = €376.56

**Belangrijkste fixes:**
- [x] 🪙 **ATOM** toegevoegd aan watchlist (6e coin)
- [x] 🔗 **Bitvavo proxy via Spark** (v6_bitvavo_proxy_via_spark_001): non-Spark users zonder eigen keys → fallback op Spark's keys. Trade-log markeert `proxied_via_spark`. Mock-fallback verwijderd.
- [x] 🎯 **Echte fill-prices** (v6_pot_real_price_001): entry_price en close_pot gebruiken Bitvavo's `avg_price` ipv ticker.
- [x] 🎯 **Potje blijft op zijn coin** (v6_pot_market_match_001): `get_available_pot(prefer_market=...)` zoekt eerst potje van diezelfde markt.
- [x] 📊 **Per-user stats** (v6_pot_live_value_per_user_001): non-Spark users zien eigen JSON-aandeel.
- [x] ⚖️ **Token = Potje model** geherbevestigd (sessie 16 evening): 1 ROAR = 1 trade-pot van €10. Capital is claim op gedeelde Bitvavo, niet vastgezette coin. `rebalance_from_bitvavo()` endpoint blijft beschikbaar maar auto-trigger uit close_pot is uit (botste met token-model).
- [x] 🔒 **Lock-enforcement bevestigd**: open/close/get-available respecteren `pot_locked=True`. E2E getest.
- [x] 💰 **Bitvavo Staking adjustment** (v6_bitvavo_staking_manual_001): handmatige veld voor Spaar/Staking-deel (`bitvavo_extras.json`). Endpoint `POST /api/shop/token/bitvavo-staking`. Telt mee in `spark_core_value` en `bitvavo_base_locked_eur`.
- [x] 🔧 **Force-sell endpoint** (v6_force_sell_real_001): doet nu echte Bitvavo SELL voor admin-close.
- [x] 🔧 **Bitvavo amount format fix** (v6_sell_amount_decimals_001): 8-decimal string ipv wetenschappelijke notatie.
- [x] 📊 **Dashboard breakdown**: `bitvavo_cash_eur` + `bitvavo_base_locked_eur` (= coins, groeit met prijs) + `bitvavo_staking_eur` (handmatig).
- [x] 🏷️ **Admin/Analytics bots-view fix**: `pot_count` altijd gezet (was None), markets uit registry overlay (v6_admin_bots_potcount_fix_001 + v6_admin_bots_markets_fix_001).
- [x] 🚫 **Spark auto-fill UIT** (v6_spark_no_autofill_001): Spark krijgt geen automatische 15 base-pots meer. Voorkomt fantoom-potjes.
- [x] 🧹 **Clean Slate '1 juni 2026'**: accounting + financial + wallet + spark_kasboek + roar transactions allemaal op 0. ROAR balances behouden. Capital baseline gereset. Trade-logs gearchiveerd in `data/_backups/clean_slate_1juni_2026/` en `data/_backups/post_user_bot_tests_29mei/`.
- [x] 📥 **Productie-data sync** (sessie 16 morning): 22 users + 36 ROAR + alle relaties uit prod-zip. Backup: `data/_backups/preview_before_prodsync_20260529_180040/`.
- [x] 🐛 **Gerben sync**: user toegevoegd met basis-avatar (gallery:31c6dc04a2fd).
- [x] 🐛 **joel123/Jayden avatar+gradatie sync** uit productie.
- [x] 📈 **Wallet line-chart fluctuatie** (v6_price_chart_density_001): 5-min snapshot interval ipv 1u, ±1% padding, auto-refresh 30s, "+" knop voor manual snapshot, delta-info in header. Snapshot bucket dedupe-bug gefixt (laatste prijs wint).
- [x] 🤝 **5/6 users E2E getest** met echte BUY+SELL via Bitvavo proxy. Spark ATOM-restje was dust (1.47 ATOM < min-order 2.81), administratief gesloten.

**Bekend / aan te scherpen:**
- Bitvavo Staking API direct lezen ipv handmatige veld (kost extra endpoint research)
- Capital-row in stats kan beter splitsen tussen "claim op cash" vs "echte coin-waarde"

**Status**: Stabiel. Klaar voor redeploy.

### ✅ Sessie 15 (2026-05-29, vervolg) — D&D Spark World
- [x] 🎭 **Body Slots** (v6_body_slots_001):
  - Backend: 3 endpoints (`GET /persons/body-slots/config`, `PUT /persons/cards/{u}/{p}/body-slots`, `DELETE .../body-slots/{slot_id}`)
  - 8 slot-types met anatomische posities: head / shoulders / chest / hands / waist / feet / aura / pocket
  - Per slot: label · icon (emoji) · color · note · ts
  - Frontend: `BodySlotsPanel.js` met SVG-silhouet + visuele klikbare slots + edit-modal
  - Geïntegreerd in PersoonsPage expand-view (onder notes, boven verwijder-knop)
  - E2E getest: Lotus krijgt "Houten ketting" in borst-slot → orange glow + legenda
- [x] 🌲 **Spark World "The North"** (v6_spark_world_north_001):
  - Backend: `modules/dnd/spark_world_north.py` — locaties als persistent JSON in `data/dnd/spark_world/locations.json`
  - Seed: **The North** (Groningen base) met 4 sub-locaties (Werkplaats/Tuin/Studio/Kampvuur) + 2 NPCs (De Dood, De Boekhouder)
  - Endpoints: `GET /dnd/spark-world/locations`, `GET /.../locations/{id}`, `POST /.../locations/travel`
  - Frontend: travel-banner in `DnDBarkPanel.js` + lazy-loaded sub-locaties + NPC-chips + senses-hints per plek
  - E2E getest: Spark World modal → Locaties → The North → werkplaats sub-pick → full travel context

**Status**: Stabiel. Geen code-blockers. Wacht op EUR-storting Willem zodat Spark potjes-commitment volledig gedekt is door Bitvavo.

### ✅ Sessie 15 (2026-05-29) — wat gedaan
- [x] 🐛 **Token-buy UI feedback** (v6_token_buy_ux_001):
  - `<Toaster>` globaal gemount in `App.js`
  - Preemptive guard in `WinkelPage.buyToken()`: blokkeert API-call als `qty × price > wallet`
  - 3 zichtbare lagen bij tekort: inline rood waarschuwingsvlak (live met qty), toast rechtsboven, inline error-box
  - E2E: 999 ROAR met €9.18 → alle 3 signalen tegelijk zichtbaar
- [x] 🚀 **Auto-anchor voor nieuwe coins** (v6_auto_anchor_001):
  - `potjes.ensure_anchors_for_markets(user_id, markets)` — Spark-only
  - Gehookt op `POST /api/trade/monitor/markets/{user_id}` → response geeft `anchors_created`
  - Per nieuwe coin: locked anker (€10, `source=auto_anchor_for_new_coin`) automatisch aangemaakt
  - Verified: bestaande coins worden correct overgeslagen
- [x] 🏷️ **KB Curation Dashboard** (v6_kb_curation_dashboard_001):
  - Nieuw component `components/workspace/KbV2TagCuration.js`
  - 6e tab "Tag-curatie" in Kennisbank met 4 stat-tegels (gescand/stammen/dedupe-kansen/sessie-merges)
  - 1-klik merge per stem met variant-dropdown + expand-knop voor alle varianten als chips
  - Sessie-historie van merges onderaan
  - E2E: 52 dedupe-kansen zichtbaar (systeem 377×, relatie 98×, grondstof 87×)
- [x] 💸 **Overflow Auto-Mint instant** (v6_overflow_auto_mint_instant_001):
  - `staking_growth.run_auto_mint_only()` — mint-only loop (geen rente)
  - Direct gehookt in `potjes.close_pot()` voor `user-000`
  - Smoke-test: overflow €25 → 2 potjes gemint + €5 rest, geen 24h-wachttijd meer
  - `close_pot` returnt nu ook `auto_mint: {minted, n_minted, overflow_after}`
  - Daily scheduler-hook behouden als safety-net
- [x] 🎨 **UI Theme refactor — Amber/Orange** (v6_spark_theme_001):
  - CSS-variabelen in `index.css`: `--spark-primary/-hover/-soft/-ring/-secondary/-accent`
  - Utility-klassen: `bg-spark-primary`, `text-spark-primary`, `border-spark-primary`, `ring-spark-primary`
  - 23 frontend files gepasseerd: cosmetic chrome (buttons, focus-rings, upload-chrome, link-hovers) van purple/blue → amber
  - Bewust intact: mood-glow palet (semantische emotie-kleuren), status-indicators (paused/mock = blauw), chart-distinctions, module-color-coding in AnalyticsPage, layer-kleuren in EmotiesPage/SparkBrainPage
  - Dashboard + KB Curation getest, geen visuele regressie

### ✅ Sessie 14 (2026-05-28/29) — wat gedaan
- [x] 🐛 KB v2 legacy media routes hersteld (path-traversal guard)
- [x] 🧹 Disk cleanup 615 MB
- [x] 🔄 KB v2 sync uit productie (42 verhuisde kaarten)
- [x] 🔤 Tag-normalizer (45 dedupe-kansen, 5 endpoints)
- [x] 🧠 SPARK AI sidebar restructure (geen dubbele tabs)
- [x] 🦅 Spark Brein-overzicht dashboard (6-kaarten helikopter-view)
- [x] 🐛 `/api/trade/stats/*` HTTP 500 (float vs dict fix)
- [x] 🐛 Quick-buy €5.08 → €10 (capital als bron)
- [x] 🐛 Open potje amount_eur backfill (11 gefixed)
- [x] 🐛 Winkelstraat avatar/logo (gallery: prefix resolve)
- [x] 🔒 Lock-bug defense-in-depth (open+close+distribute)
- [x] 🏗️ Spark 5 anchor pots (1 per coin) + hernummering pot-001..015
- [x] 🎨 Locked potjes onderaan UI (sort-key)
- [x] 🐛 €43.25 fix (growth-distortion in live_value)
- [x] 🐛 Snel Handelen panel (skip locked + capital + refresh 10s)
- [x] 🐛 Ghost-anchors Willem + Gijs verwijderd (alleen Spark hoort anchors te hebben)
- [x] 🐛 Ghost-positions Willem (6 fake OPEN → cleared)
- [x] 🐛 Auto-lock hook beperkt tot Spark (was bug die anchors bij iedereen herstelde)
- [x] 🐛 Willem coin-balance 3-1-2-2-2 → 2-2-2-2-2 symmetrisch
- [x] 📋 7 bugs.json afgevinkt met resolution-tag
- [x] 📈 ROAR price-history snapshots + scheduler-hook (1×/uur)
- [x] 📜 Disclaimer uitgebreid (5 nieuwe secties: privacy/werking/eigendom/transparantie/aansprakelijkheid)
- [x] 💰 **6 Boekhouding-hooks gecentraliseerd** (v6_accounting_hooks_001):
  - `modules/accounting/hooks.py` met 6 idempotente helpers (tx_ref-based)
  - Hook 1: ROAR token-buy → income spark_core (gift/sales o.b.v. anker/klant)
  - Hook 2: Bitvavo coin-buy → expense spark_core (Materiaal)
  - Hook 3: Sell-back → expense spark_core (Refunds)
  - Hook 4: Shop verkoop → income shop-kasboek + 2% commissie naar spark_core
  - Hook 5: Tikkie deposit → income personal_<naam>
  - Hook 6: Trade SELL resultaat → income/expense Crypto Profit
  - Aanroepen toegevoegd in `shop/routes.py` (token-buy/sell-back/shop-sale), `trade/potjes.py` (open_pot+close_pot), `wallet/tikkie.py` (confirm)
  - Stille-fail mode: hook-error blokkeert nooit een product-actie
- [x] 🌱 **Staking Growth Engine** (v6_staking_growth_engine_001):
  - `modules/trade/staking_growth.py` — 3-in-1 module
  - Auto-rente: 1.5% per anchor per maand uit overflow_pool (30-dag interval)
  - Auto-mint: bij overflow >= €10 → nieuw trade-potje
  - Auto-anchor: `POST /auto-anchor` voor nieuwe coin (alleen Spark, idempotent)
  - 3 endpoints: `/trade/growth/run`, `/trade/growth/status`, `/trade/growth/auto-anchor`
  - Scheduler-hook dagelijks check (intern 30-dag rente-interval)
  - **Live getest**: €25.50 overflow → 5 anchors +€0.38 elk + 2 mints + €3.59 rest. Reset naar clean state.
- [x] 📅 **Boekhouder weekrapport** (v6_boekhouder_weekrapport_001 + v6_weekrapport_token_holders_001):
  - `modules/boekhouder/weekly_report.py` — verzamelt anchor-groei + overflow + mints + trade-PnL + ROAR-activiteit
  - Stuurt zondagavond 20:00-22:00 UTC een PM naar admin met human-readable rapport
  - **+ Alle ROAR token-houders krijgen PM** (idee Willem): bot stuurt rapport aan iedereen met >=1 token, holders voelen de groei van hun investering zonder app-bezoek
  - Projectie: "Bij dit tempo verdienen anchors zichzelf in N maanden terug"
  - 3 endpoints: `/preview` (UI), `/run` (admin-trigger met `also_token_holders` toggle), `/history`
  - History archief in `data/boekhouder/weekly_reports.json` (max 200 entries = ~4 jaar) + recipients-tracking
- [x] 🛍️ **Token-koop via shop referral** (v6_shop_referral_token_001):
  - `BuyTokenRequest.via_shop_id` optionele parameter
  - Als ROAR via een specifieke shop wordt verkocht (bv. Roadkillshop), krijgt die shop **2% commissie** in z'n eigen kasboek (`Referral`-categorie)
  - Alleen voor klanten, niet voor anker-aankopen (die zijn fundering)
  - Stille-fail (non-blocking)
- [x] 📜 **Disclaimer v6.2** — `staking_growth` sectie + `nieuw_sessie14` shop-referral & holder-newsletter

### Conceptueel kader (uit deze sessie)
- **Emotie Detectie** (`/spark/emotions`, iedereen) = "Wat voelt user nú?" → 4 emoties (blij/boos/bang/bedroefd) + state + test
- **Emotie Routering** (`/spark/routering`, admin) = "Hoe reageer ik?" → 7 lagen → behavior_class (begrenzen/vertragen/exploreren/kalmeren)
- Niet duplicaat, maar gestapelde ketting (hybride-by-design, niet bipolair)

### Token-balans (live, ongewijzigd)
| Wie | Tokens | Betaald (cash in) | Rol |
|---|---|---|---|
| Spark (user-000) | 10 | — | Anker / fundering |
| Willem (user-001) | 10 | €50.80 | Anker / fundering |
| Gijs (user-a0ee2d7e) | 2 | €20.80 | Klant (gift-fase, 0% BTW) |
| **Totaal circulating** | **22** | **€71.60 cash in** | |
| Spark treasury | 999,978 | — | Pool |

### Bitvavo & potjes-status (sessie 16, na rebalance-from-bitvavo)
- Bitvavo live crypto: **€90.50** (BCH €20 / BTC €20 / ETH €10 / SOL €10 / ADA €20 / ATOM €10)
- Bitvavo EUR-cash: ~€245
- Spark commitment: 6 locked anchors = **€10.50** (BCH €0.01 / BTC €0.10 / ETH €0.21 / SOL €0.16 / ADA €9.90 / ATOM €0.12)
- Willem trade-pots: 8 × €10 = **€80** (2 BCH / 2 BTC / 1 ETH / 1 SOL / 1 ADA / 1 ATOM)
- **Som potjes = Bitvavo crypto: €90.50 ✅** (exact match)
- ROAR-prijs-formule: `Bitvavo balance ÷ circulating` — past zich auto aan bij elke storting
- Auto-rebalance triggert na elke `close_pot()` → systeem houdt zichzelf in sync

### Wat live werkt (smoke-checked, mag op productie)
- Bitvavo trading LIVE — alle user-bots via Spark's keys (proxy fallback, sessie 16). Echte fills uit Bitvavo `avg_price` voor entry/exit op potjes.
- Multi-user bots: Spark + Willem + Gijs + Roadkill + Lotus + Gerben (5 users met tokens kunnen autonoom traden)
- ROAR economy v6 (gift-fase, 0% BTW, dynamic price)
- Boekhouding 4 entiteiten (Spark Core / Zorgboerderij / Roadkill Merch / Privé Willem) met BTW-summary + reconcile + retroactief fix-endpoint
- Tikkie-storting flow (user→admin PM→confirm→wallet bijschrijven + auto-archief in admin's bestanden)
- Winkelstraat hub met owner-shop-isolation (`shops/{shop_id}/products.json`)
- 8 capabilities + 17 in chat-router (5 executable, 12 met handlers ready)
- Synapse auto-documenter (90 containers, 419 endpoints, 78 actief, 12 skelet, 59 blueprints)
- KB v2 hooks-laag (5 hooks live: vocab/tell-layer/verbanden/dnd-link/voice-snippet)
- KB tag-normalizer met 45 dedupe-kansen geïdentificeerd
- @traced observability (auth/login + logout, trade buy/start/stop, shop-gift, kbv2 mutations)
- 21:00 Boekhouder roundup-bark + Madelief error-pointer (5-min scheduler)

### Open P0 (niet blocker voor deploy, mag erna)
- [ ] 6 Boekhouding-hooks centraliseren (token-buy / bitvavo coin-buy / sell-back / shop-sale / deposit / trader-result → automatisch posten op `/api/accounting/transactions`)
- [ ] Legacy `spark_kasboek.json` schrijfpaden uitfaseren (alleen-lezen + migratie-script)

### Open daarna (P1+)
- [ ] **📚 Help + Commands update + spliten** (afgesproken, sessie 15):
  - Bestaande `help_g{n}.json` per gradatie staan nog niet voor v6-features (staking-growth, weekrapport, shop-referral, 5 anchors, tag-merge, ...)
  - Plan: split per module-area (trade-help / shop-help / kb-help / boekhouding-help) ipv 1 grote per-gradatie file
  - Auto-gegeneer uit command_registry tags
  - Cluster D #cmd-gradatie-files + #cmd-grad-lock + #cmd-priv-fallback bouwen hier verder op
- [x] ✅ 1-klik UI **#kb-curation-dash** bovenop `/api/kb/v2/tags/scan` (sessie 15, v6_kb_curation_dashboard_001)
- [x] ✅ **🌱 Staking Growth Engine** (sessie 14 + sessie 15 instant-mint):
  - [x] Auto-rente uit overflow_pool → anchor.capital groei (sessie 14)
  - [x] Auto-mint bij `overflow_pool >= €10` (sessie 14, daily) + **instant na elke close_pot** (sessie 15)
  - [x] Auto-create base-anchor bij toevoegen nieuwe coin aan watch (sessie 15, v6_auto_anchor_001)
- [x] ✅ **🎨 Unified Theme Engine** (sessie 15, v6_spark_theme_001 — eerste pas):
  - [x] CSS-vars in `index.css` (`--spark-primary`, `--spark-secondary`, `--spark-accent`, ...)
  - [x] Sweep cosmetic chrome `bg-purple-/bg-blue-/focus:border-purple-` → `bg-amber-/focus:border-amber-` in 23 files
  - [x] Semantic colors (mood/status/charts) bewust intact gelaten
  - [ ] Nog te doen (v2): ThemeContext per section, user-override in Settings, light/dark-mode voorbereiden
- [ ] Tag-merge auto-fire optie in `classify_card` (opt-in flag)
- [ ] Exception-list uitbreiden bij volgende false-positives
- [ ] 2 endpoints uitbreiden (`/spark/disclaimer.leidende_lagen_counts.bijbel + capabilities` + `/kb/v2/stats.inbox.count`) zodat overzicht alle cijfers heeft i.p.v. `-`
- → Zie clusters A-J hieronder voor volledige backlog

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
- **v1 Knowledge Base** (`/data/knowledge/learned_knowledge/knowledge_base.json`) — 5288 entries, full graph-coverage.
- **KB v2 — 4 lades** (`/data/knowledge/v2/`) — 🌸 Voelen 250 · 💬 Spreken 329 · 🧠 Weten 1071 · 🎭 Doen 632 + 📥 Inbox 3007 (te classificeren).
- **Knowledge graph** (`modules/graph/sync_service.py`) — 10577 nodes + 65981 edges (v1+v2 gemengd, lade-kleuren).
- **Voice/Image media** — centraal in `system_archive` met `linked_card_id` backreference.

### 🎭 D&D / Levende Wereld laag
- **Lore index** (7 avatars-as-functions, 6 behavior-categorieën).
- **Aura-engine** (`/api/dnd/aura/{user_id}`) — live top-3 gedragingen → kleur-gradient op Persoonskaart.
- **Card Factory** (`modules/cards/`) — DnD/Event/Bark kaarten met hook-chain bij draft→active.
- **Base Line intro** (community chat `[start verhaal]`) — keuze-driven story-flow.

### 🎙️ Stem-laag
- **TTS-friendly padding** (`chat/tts_friendly_service.py`, v5_tts_pad_001) — korte antwoorden krijgen een natuurlijke tail zodat de stem niet abrupt stopt.
- **Whisper STT** voor voice-notes in kennis-kaarten (Emergent LLM Key).
- **6 OpenAI TTS-stemmen** per bot configureerbaar (`auth/admin/bots/{bot_id}/settings`).

### 🤖 Bots als acteurs (live)
- **De Boekhouder** — trade-aankondigingen + community-feed + event-barks.
- **Harry Klokkenmaker** — spiegel-minuut bark (11:11, 12:12, …).
- **Madelief Stouten** — bug-pointer bark wanneer user "bug/kapot/crash" zegt.
- **Mr Smith** — login-counter bark + Matrix-style backup-waarschuwing.
- **De Dood** — reflectieve momenten/eindes/transities.

> **Conclusie**: Spark heeft 5 lagen denken, 14+ specialized services, shadow-observation,
> 10K+ knowledge nodes, en 5 acteur-bots die zelfstandig in community barken. De backlog
> hieronder zijn *aanvullingen* op dit bestaande brein, geen vervanging.

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

## 🗺️ Backlog (prioriteit hoog → laag)

### P0 — In Progress
- [x] **AUDIT 2026-05-28 — 9 items reeds done in eerdere sessies, nu expliciet ✅ in roadmap** (op verzoek Willem):
  - 🛣️ **Communicatie / Spark hands intent-router** — `spark_capabilities.json` heeft nu **16 capabilities** met expliciete NL-triggers. Chat-router pakt 5/5 in deze sessie + 11 eerder. Volgende uitbreiding (5 nieuwe semantic intent-tags) is een aanvulling op werkende fundering.
  - 📚 **Spark eigen index-mapstructuur + meta-index** — Synapse-architectuur live: **57 `_meta.json` files** in containers + aggregator op `/app/memory/SYNAPSE.json`. Auto-scanner + touch-hook + UI-tab "Synapslaag" in Beheer.
  - 🗣️ **Voice module STT** — `kb_v2/media_routes.py` met Whisper-koppeling via Emergent LLM Key live. Voice-snippets → `dialogen/voice_snippets/`. TTS-stem-instellingen per bot in `bot.settings.tts_voice`. (TTS audio-uitspeel volgt later — STT-flow werkt end-to-end.)
  - 🆘 **Help-JSON per gradatie (g1 t/m g7)** — `modules/help_per_gradatie/` module live met `GET /api/help/index` + `/help/g{n}` endpoints per gradatie. Help-tekst per gradatie geseed.
  - 📐 **Blueprint-systeem (1 JSON ↔ 1 module)** — Synapse-enricher genereert **59 markdown blueprints** in `/app/memory/blueprints/{naam}.md` met Doel/Wat werkt/TODO/Splitting-trigger/Encryption/Relaties-checklist.
  - 🤖 **Trade bot — Pot 1 als €10 staking-anker** — `LOCKED_POT_INDEX=0` met `pot_locked=True, lock_reason="staking_anchor"`. `find_available_potje` skipt gelockte potjes. Backfill werkend, toggle-endpoint aanwezig.
  - 🖼️ **Avatar edit in Beheer→Archief** — `AvatarGallerySection.js` heeft Bewerk-knop op user + system avatars. Modal met titel + tags (+ bot_owner voor system). Backend `PATCH /api/avatar/gallery/{id}` admin-guarded en werkend.
  - 🔗 **KB v2 verbanden (fase 1)** — `compute_verbanden` hooked en gefired op classify/edit. 644/659 kaarten in lade 'doen' hebben verbanden, UI rendert ze in CardDetail. (Volgende fase: hernoemen + handmatig koppelen — nog open.)
  - 🧪 **Leermodules — synoniem-detectie + auto-tag-normalisatie** — `intent_registry/extractor.py` met **~150 synoniem→canonical-tag mappings**. Multi-word phrases worden vóór tokenisatie gematched. Skill-discovery via `intent_log.jsonl` voor auto-leren van nieuwe patronen.

- [x] **Winkelstraat frontend + container-isolatie** ✅ DONE (v6_winkelstraat_frontend_001, 2026-05-28):
  - 3e hoofd-tab in `WinkelPage.js` (`WinkelstraatTab.js`) — toont actieve shops, "Open mijn winkel"-knop, voorwaarden-modal (v1, 2% commissie), create/edit/close flow.
  - Admin (gradatie ≤ 2) bypass: kan winkel openen zonder min_gradatie 4-eis.
  - Backend bug gefixt: `USERS_FILE` pad was `/data/users/` ipv `/data/system/`.
  - Founder-shop (Roadkillshop) krijgt FOUNDER-badge en commissie 0%.
  - Auto shop-container met `_meta.json` aangemaakt bij elke nieuwe winkel (F7).
  - Status `closing` → container getagd voor archivering bij sluiting.

- [x] **Boekhouding reconciliatie** ✅ DONE (v6_kasboek_reconcile_001, 2026-05-28):
  - `GET /api/spark/kasboek/reconcile` vergelijkt ROAR-transactions (anchor_mint + buy_roar excl. Spark) ↔ spark_kasboek totals ↔ Spark EUR-wallet.
  - `POST /api/spark/kasboek/reconcile/fix?viewer_id=...` boekt unbooked tx retroactief als `gift_in`/`omzet_in` afhankelijk van money_phase (admin-only).
  - Bevestigd: Willem's anchor_mint €50.80 ontbrak → na fix `gift_in=€71.60` (Willem €50.80 + Gijs €20.80), `in_balance=true`.
  - Ook sell_back uit-boekingen gevangen via aparte bucket.

- [x] **Potje 1:1 regel (1 token = 1 potje)** ✅ DONE (v6_potje_per_token_001, 2026-05-28):
  - Regel: alleen Spark (user-000) krijgt 10 base potjes; alle andere users 1 potje per ROAR-token.
  - `_load()` skipt auto-init voor non-Spark users (legen user-record ipv 10 potjes).
  - `sync_potjes_to_tokens(user_id, n_tokens)` voegt potjes toe bij token-buy.
  - `trim_potjes_to_tokens(user_id, n_tokens)` verwijdert ongebruikte potjes (geen open positie, niet de lock-anker) bij sell_back/gift_sent.
  - Hooks in `shop/routes.buy_tokens` + `shop/gift.accept_gift` voor live-sync.
  - Admin bulk endpoint `POST /api/trade/potjes/sync-all-to-tokens?viewer_id=...` voor backfill.
  - Resultaat: Gijs 10→2 potjes (matcht 2 tokens), Marieke 0 potjes (matcht 0 tokens), Spark/Willem ongewijzigd.

- [x] **Spark hands intent-router 13 → 17 commands** ✅ DONE (v6_capabilities_handlers_003, 2026-05-28):
  - 4 nieuwe entries in `spark_capabilities.json` met NL-triggers: `kennis_inbox_status`, `bots_status`, `audit_health`, `agenda_vandaag`.
  - Chat-routing nu **5/5 capability-handlers actief** (was 2/5 — intent-collision opgelost door expliciete trigger-patterns).
  - Getest: "welke bots draaien" → bots_status, "audit gezondheid" → audit_health, "hoeveel kaarten wachten op classificatie" → kennis_inbox_status, "wat staat morgen op mijn agenda" → agenda_vandaag, "wat is spark saldo" → spark_saldo_check.

### P0 — Vorige sessies (blijven done)
- [x] **Spark's hands** capability hookup naar live chat — ✅ DONE (v6_intent_router_001): `capability_handler_service.py` met 4 live handlers (tellen_gebruikers, tellen_bestanden, taken_lijst, winst_verlies). Hook in `chat/routes.py`. Onbekende caps → placeholder. Uitbreiden naar trade_logs_ophalen / kasboek_overzicht in volgende sessie.
- [x] **Boekhouder closing-flow** ("terlens-terug-boek") — ✅ DONE (v5_closing_flow_001): `close_cycle(user_id, note)` rollupt audit-events sinds vorige closing, DM naar admin/user, audit-log + closings-log. Endpoints: `POST /api/boekhouder/close-cycle/{user_id}` (admin-guarded) + `GET /api/boekhouder/closings`
- [x] **Notitie & Taak edit** (v6_note_edit_001, 2026-05-26) — ✅ DONE: pencil-knop op notitie/taak-kaart opent inline edit (titel + inhoud). Backend `PUT /api/notes/update/{id}` + `PUT /api/notes/tasks/update/{id}` reeds aanwezig; frontend `NotitiesPage.js::updateItem()` + `NoteItemCard` edit-modus toegevoegd. (bewerkt)-label op kaart bij `updated_at`.
- [x] **Avatar edit in Beheer→Archief** (v6_avatar_edit_001, 2026-05-26) — ✅ DONE: Bewerk-knop op zowel user- als system-avatar tiles in `AvatarGallerySection`. Modal met titel + tags (alle) + bot_owner (alleen system). Backend `PATCH /api/avatar/gallery/{id}` reeds aanwezig en admin-guarded.
- [x] **Glow-nav volledig live** (v6_glow_nav_001, 2026-05-26) — ✅ DONE: Backend `tabs_registry` gesynchroniseerd met frontend `MainLayout.navigationConfig` (23 tabs, kebab-case IDs matchen `data-testid="nav-{id}"`). Chat-flow nav-trigger gehoist boven capability-router. Frontend dispatcht `spark:nav-glow` event op `data.type==='navigate_tab'`. `MainLayout` luistert → voegt 6s pulserende amber `spark-nav-glow` CSS-class toe op de matchende nav-button + scroll-into-view + auto-`onNavigate()` na 700ms. Triggers: `waar is/zijn`, `waar vind/kan ik`, `ga naar`, `open de/tab/mijn`, `ik wil naar`, `breng me naar`, `laat zien waar`. Getest met 9 queries: 8/8 navigate_tab, greeting valt door (correct).

### P1 — Aanstaande (deze maand)

#### 🧬 Synapse / Container architectuur — ✅ Fase 1+2 LIVE (sessie 12+, 2026-05-26)
- [x] **F1+F5 — Map-meta fundament** ✅ DONE: `_meta.json` per map (88→90 containers gescand). Schema in `modules/synapse/schema.py` met blueprint_ref, footnote, encryption-slot (leeg, klaar voor F2F). Auto-scanner `modules/synapse/scanner.py` detecteert 418 endpoints uit `@router.<verb>` decorators. Aggregator → `/app/memory/SYNAPSE.json`. Skeleton-heuristiek (≤1 code-file, geen endpoints) markeert 12 placeholders correct.
- [x] **F2 — Spark leest zichzelf via chat** ✅ DONE: `modules/synapse/chat_handler.py` met intent-detectie (NL): *"wat hebben we?"*, *"is X af?"*, *"waar woont X?"*, *"wat doet X?"*, *"lijst skeletons"*, *"lijst verouderd"*. Hookt in `chat/routes.py` vóór glow-nav/capability-router. 6/6 test-queries werken.
- [x] **F3 — Auto-touch hook** ✅ DONE: `modules/synapse/touch.py::touch_path()`. Hookt in `core/storage.py::save_json()`. Elke file-mutatie bumpt `_meta.json::last_touched + activity_count` van de parent-container. Getest: notes _meta activity_count 0→1 (create) →2 (delete) automatisch.
- [x] **F4 — Container abstractie (universeel patroon)** ✅ DONE: `modules/container/service.py` met generieke CRUD. User-container als 1e implementatie. Endpoints: `POST/GET/PATCH/DELETE /api/container/{type}/{id}`. 3-fase delete: tag → archive → cleanup-cross-refs. User-delete anonimiseert bugs/community, verwijdert agenda/dagboek/chat-prive files. Encryption-slot reeds in elke meta voor F2F-feature later. E2E getest: create→list→patch→tag→delete-archived✓.
- [x] **F6 — UI Synapse-tab** ✅ DONE: `frontend/src/components/admin/SynapseTab.js` in Beheer→Instellingen→Synapslaag. Header met live summary (88+ containers, 418 endpoints, status-tellingen). Filter op groep + status + zoek. Klik op item → edit-modal voor doel/status/blueprint_ref/footnote/tags + readonly metadata (created/touched/endpoints/encryption-slot). Knop "Volledige scan" trigger backend rescan.
- [x] **F7 — Shop container (Winkelstraat)** ✅ DONE (auto-hook): `winkelstraat::create_shop` maakt nu ook automatisch een shop-container aan met `CONTAINER_SHOP` type, commissie+gradatie in meta.extra. `winkelstraat::close_shop` tagt container voor deletion. Bij admin-finalize → shop-data isolated weg, geen cross-pollution.
- [x] **F8 — Synapse auto-enricher** ✅ DONE (v6_synapse_002): `enricher.py` leest docstrings uit `__init__.py` + JSDoc-blokken en vult automatisch het `doel` veld voor 53 modules. Genereert blueprint-stubs in `/app/memory/blueprints/{naam}.md` met checklist-template (Doel/Wat werkt/TODO/Splitting-trigger/Encryption-plan/Relaties). Endpoint: `POST /api/synapse/enrich`. Spark antwoordt nu *"glow_nav helpt user navigeren via chat-intent → tab-glow"* in plaats van *"geen omschrijving"*.

#### 🧠 KB v2 laagsgewijs uitleg ✅ DONE (sessie 12+, 2026-05-26)
- [x] **B — KB v2 "vertel kort / meer / diep / volledig"** ✅ DONE (v6_kbv2_tell_layer_followup_001): Spark's antwoorden zijn nu gelaagd. Triggers werken met of zonder onderwerp:
  - *"vertel kort over identiteit"* → laag1
  - *"vertel meer"* → laag1+laag2 (van laatst-besproken kaart)
  - *"ga dieper"* → laag1+2+3
  - *"vertel volledig"* → alle 4 lagen
  Session-state houdt `last_kbv2_card_id` 10 min bij. Fallback gebruikt index-lookup om kaart in juiste lade te vinden. E2E getest met "Identiteit"-kaart: alle 4 follow-ups correct.

#### 🔧 Refactor + minor bugs (sessie 13+, 2026-05-28 ALLES DONE)
- [x] **Wallet header-knop volgorde** ✅ DONE (v6_wallet_button_order_001, 2026-05-28): Storten (+) → Opnemen (−) → [Mint admin] → Gift (rechts). `data-testid="add-funds-btn", "withdraw-btn", "spark-mint-token-btn", "open-gift-modal"`.
- [x] **ROAR-prijs consistentie display** ✅ DONE (v6_roar_price_display_001, 2026-05-28): WinkelPage tekst opgeschoond — "1 ROAR = aandeel in Spark Core kapitaal" + formule `€{spark_core} ÷ {circulating} = €{price}` zichtbaar in tooltip. "Jouw tokens" → "Jouw bezit" + "Waarde" → "Tegen huidige prijs".
- [x] **Potje grootte €5.08 → €10** ✅ DONE (v6_potje_size_10_001, 2026-05-28): `START_AMOUNT = 10.0` voor nieuwe users. Admin-endpoint `POST /api/trade/potjes/{user_id}/resize-to-default` voor bestaande users (faalt bij open posities).
- [x] **Pot 1 Staking Anchor (€10 lock)** ✅ DONE (v6_pot1_staking_lock_001, 2026-05-28): eerste potje krijgt `pot_locked=True, lock_reason="staking_anchor"`. `find_available_potje` skipt gelockte potjes. Backfill robuust (vindt eerste potje ook in legacy data zonder `index`). Toggle-endpoint `POST /api/trade/potjes/{user_id}/toggle-lock`.
- [x] **Trader Help (in chat + UI-ready endpoint)** ✅ DONE (v6_trade_help_001, 2026-05-28): `modules/trade_help/__init__.py` met 7 secties (potjes-systeem, BUY/SELL-logica, Modes, Veiligheid, Spark Brain, Tips). Endpoints `GET /api/trade/help` + `/markdown`. Chat-router pakt triggers ("hoe werkt de trader/bot/potjes?") en post eerste 3 secties met deep_link `/modules/trade?tab=help`.
- [x] **`@traced` uitrol overige** ✅ DONE (v6_traced_rollout_002, 2026-05-28): shop.gift (`create_gift`, `accept_gift`) + KB v2 mutations (`classify`, `edit`, `delete_card`).

#### Bestaande P1 items — Status 2026-05-27 inventarisatie

- [x] **KB v2 → Vocab register hook** ✅ AL LIVE (sessie 11): `register_in_vocab` is gehookd in `service.py::_fire_post_classify_hooks`. `spark_vocab.json` heeft **5304 entries, 2316 active**. Spark gebruikt de active-set voor spontane spraak.
- [x] **KB v2 → Chat-commands "vertel kort/meer/diep"** ✅ DONE (v6_kbv2_tell_layer_followup_001, 2026-05-26): zie boven.
- [x] **KB v2 → Auto-graph (verbanden)** ✅ AL LIVE (sessie 11): `compute_verbanden` is gehookd. Op lade `doen`: **644/659 kaarten** hebben verbanden. UI in CardDetail toont ze al.
- [x] **KB v2 → D&D Kaarten integratie** ✅ AL LIVE (sessie 11): `link_to_dnd` is gehookd. Lore-cards met `dnd.type=="lore"` syncen naar lore_index.
- [x] **KB v2 → Voice-snippet auto-save** ✅ DONE (v6_voice_kbv2_link_001, 2026-05-27): STT endpoint accepteert optionele `card_id` + `user_id` query params. Bij meegegeven → `save_voice_snippet` schrijft transcript naar `/data/dialogen/voice_snippets/YYYY-MM-DD/{card_id}_{snippet_id}.json`.
- [x] **ConversationStateManager terug uit v1** ✅ DONE (v6_conv_state_001, 2026-05-27): `session_state.py` heeft nu `set_last_question` / `get_last_question` met 2-min expire window. Verlopen vragen worden in `get_state` automatisch weg-gefilterd.
- [x] **AuditService weak-trigger scan** ✅ DONE (v6_audit_001, 2026-05-27): `modules/audit/__init__.py`. Endpoints `GET /api/audit/weak-triggers`, `/self-learning`, `/summary`. 5307 KB-entries gescand, 2239 (42%) missen `laag1`. Reports persisteren in `/data/system/audit_reports/`.
- [x] **Self-learning audit (B5)** ✅ DONE (v6_audit_001): zelfde service. Verifieert shadow_observations.jsonl recentheid (<48h), unique-kinds variatie, parse-errors.
- [x] **D&D Perks & Unlocks** ✅ DONE (v6_perks_001, 2026-05-27): `modules/perks/__init__.py` met 8 declarative perks. Combineert `min_gradatie + required_behaviors + blocked_by_behaviors`. Endpoints `GET /api/perks?user_id=...`, `/check/{perk_id}`, `/user/{user_id}`. Klaar voor frontend-integratie om feature-gates aan/uit te schakelen.

### P2 — Volgend kwartaal

#### ✅ Done in sessie 13 (2026-05-27/28)
- [x] **`@traced` uitrol (auth + trade)** ✅ DONE (v6_traced_rollout_001): `login`, `logout` (auth) + `quick_buy_potje`, `bot_start`, `bot_stop` (trade) hebben `@traced` decorator. Logs verschijnen in `/data/system/logs/YYYY/MM/DD/spark.jsonl` met phase=start/done/error.
- [x] **Auto-expire archive (pending gifts)** ✅ AL LIVE (eerdere sessie): `shop/gift.py` heeft expire-logica naar status="expired" na 24h.
- [x] **Boekhouder 21:00 roundup-bark** ✅ DONE (v6_scheduler_001): `modules/scheduler/__init__.py` draait elke 5 min in background. 19:00/20:00 UTC (= 21:00 NL) post Boekhouder samenvatting in community. Persistent state-file voorkomt dubbele post.
- [x] **Spark "merkt eigen errors"** ✅ DONE (v6_scheduler_001): Madelief Stouten scant elke 5 min nieuwe `phase=error` log-records. Bij errors → bark in community met module/intent/err-context (max 3 per bark, anti-spam).
- [x] **Spark hands intent-router 8 → 13 commands** ✅ DONE (v6_capabilities_handlers_002): 5 nieuwe handlers in `capability_handler_service.py`: kasboek_overzicht, agenda_vandaag (alias voor agenda_lezen placeholder), kennis_inbox_status, bots_status, audit_health. 2/5 actief gematcht in chat (kasboek + agenda); andere 3 wachten op verfijning van intent-triggers maar handlers staan klaar.
- [x] **User-migratie helper** ✅ DONE (v6_container_migrate_001): `container/user_helper.py::migrate_user_legacy()` + `migrate_all_users()`. Endpoints `POST /api/container/user/migrate` + `/migrate-all`. Idempotent: kopieert legacy agenda/dagboek naar user-container met migration-footnote. 1/21 users had legacy-data om te migreren (Willem, 2 bestanden).

#### Nog open
- [x] **Trader sell-balance + SOL min-buy fix** ✅ DONE (v6_trade_minorder_001 + v6_trade_sell_balance_001, 2026-05-28):
  - `monitor.py::get_market_min_quote(market)` — 1u-cache van Bitvavo `/v2/markets` minimums, met fallbacks (BTC/ETH/SOL/ADA = €5).
  - **Buy pre-check**: bij `amount_eur < min_quote` → vriendelijke error met tip (geen crash meer op SOL).
  - **Sell pre-check**: voor SELL fetch eerst actuele balance, clamp naar `min(requested, actual) * 0.999` om dust-rounding te vermijden. Bij 0 balance → duidelijke error met base_asset.
  - Errors hebben nu `error_code` (`MIN_QUOTE`, `NO_BALANCE`, `ZERO_AFTER_CLAMP`, `BITVAVO_HTTP_ERROR`, `EXCEPTION`) voor frontend-handling.
  - Trade-record bevat extra `requested_amount` + `effective_amount` voor traceability.
  - Unit-test in preview bevestigt min-quote fallback werkt (Bitvavo timeout in preview is normaal).
- [ ] **`@traced` uitrol (overige overig)** — dnd.observe + monitor.execute_real_trade nog niet (rest is gedaan in v6_traced_rollout_001/002). (deel al gedaan, restant in volgende sessie)
- [ ] **Identity 3-lagen-enforcement** in seed-data (CR-001/002/003 als code-wet ipv alleen doc)
- [ ] **ROAR-gift encryption-at-rest** — sender/recipient pairs privacy-gevoelig
- [ ] **SEPA-mint koppeling** voor ROAR economy v2 — PLACEHOLDER, Tikkie blijft fallback
- [ ] **ReplayLogService uit v1** — trade backtest met run_id replay
- [ ] **Winkelstraat eigen boekhouding per shop** — owner ziet eigen omzet/orders/commissie binnen zijn shop-container (`shops/{shop_id}/`). Decentrale boekhouding ipv globaal kasboek.
- [ ] **Winkelstraat producten-CRUD per shop** — owner kan eigen merch/digital producten toevoegen binnen zijn shop. Nu zit alle producten-data global in `/data/shop/products.json`.
- [ ] **WinkelPage.js refactor** — 684 lines splitsen in `MerchTab.js` / `DigitalTab.js` (storage+tokens) / `WinkelstraatTab.js` (al gedaan).
- [ ] **Closed-shops filter** — 'closing' shops verbergen uit publieke lijst, of admin hard-delete endpoint.

### P3 — Future / Experimenteel
- [ ] **Dynamic theming** via `lore_index.json` (kleuren shiften met seizoen/lore)
- [ ] **Krachtigere "spark's eigen anker"** — Spark maakt eigen notities die over sessies heen bestaan
- [ ] **ROAR-token reward per geclassificeerde kaart** (gamification Inbox doorlopen)
- [ ] **Krachtigere log-search** — full-text zoeken over alle modules op een dag
- [ ] **Boekhouder closing-flow** uitgebreid met PDF-export per maand

---

## 🌱 Backlog 2026-05-28 — 21 nieuwe ideeën (Willem brainstorm)

Geordend per cluster. Veel haakt aan op fundering van v6_command_registry_001 (al live).

### Cluster A — KB curation & normalisatie
- [ ] **#zip-mindgraph** — Zip-backup bevat ook mindgraph + andere afgeleide data. Bij restore meeladen ipv alleen kaarten.
- [ ] **#kb-node-hierarchy** — Hoofd-node vs sub-tag hierarchie (bv. "emotie" = hoofd-node, "blij/boos" = sub-tags). Schema-uitbreiding op tags-array → tree.
- [x] **#kb-tag-singular + #kb-verb-stem** ✅ FUNDERING + MERGE-ENGINE DONE (v6_kb_tag_normalizer_001 + v6_kb_tag_merge_001, 2026-05-28):
  - `modules/kb_v2/tag_normalizer.py` met `normalize_tag()`, `normalize_tags()`, `tags_similar()`, `overlap_score()`. 20/20 unit-tests pass.
  - Plant/plan false-positive opgelost via `_NOUN_T_EXCEPTIONS` (~50 NL nouns: plant, kant, kunst, boot, moet, voet, post, kist, etc.) — kan groeien per false-positive.
  - **5 endpoints**: `GET /api/kb/v2/tags/normalize?tag=...`, `POST /tags/normalize-batch`, `GET /tags/scan?limit=...`, `GET /tags/similarity?a=...&b=...`, `POST /tags/merge` (admin-only).
  - **Live scan resultaten** (na plant-fix): 18.041 tags / 3.423 stammen / **45 dedupe-kansen**:
    - `emotie/emoties` — 457 occurrences (✅ gemergd via API, dedupe-kansen → 44)
    - `systeem/systeemm` — 376 (typo, wacht op handmatige keuze)
    - `relatie/relaties` — 98 · `grondstof/grondstoffen` — 87 · `dier/dieren` — 54
    - `game/games` — 49 · `doel/doelen` — 30 · `werk/werkt` — 28 · `eigenschap/eigenschappen` — 27 · `speler/spelers` — 25
  - **Merge-endpoint flow** (admin-only, gradatie ≤ 2): POST `/api/kb/v2/tags/merge` met `{stem, keep_variant, viewer_id}` → vervangt alle varianten met zelfde stam door `keep_variant` in alle 4 lades. Returnt `cards_touched + tags_replaced + per_lade`.
  - **Open volgende sessie**: 1-klik UI in #kb-curation-dash bovenop `/tags/scan` data; auto-normalisatie bij `service.classify_card` (opt-in flag); uitbreiding exception-list bij meer false-positives.
- [ ] **#kb-similarity** — Gelijkheid-engine met stam-herkenning. Voedt `compute_verbanden` en disambiguatie. Bouwt op tag_normalizer.
- [ ] **#kb-curation-dash** — Curatie-dashboard: zie afwijkingen, los enkelvoud/synoniem-conflict op met 1 klik. Backend `/tags/scan` levert nu al de data; UI moet nog.
- [ ] **#kb-ui-unified** — KB-invul UI volledig consistent maken (één layout overal — inbox / lade-detail / nieuwe-kaart / herzien). Reeds gedeeltelijk via `CardFormFields`.
- [ ] **#snap-topic-unique** — Snap-creatie: topic-uniqueness check tegen `knowledge_index.json` vóór auto-create.

### Cluster B — Triggers & Hooks (community-extensible)
- [ ] **#trigger-hooks** — Hook-systeem voor triggers/commands (gebruiker-uitbreidbaar). Schema: `/data/triggers/user_triggers.json` met owner/gradatie/pattern/action.
- [ ] **#trigger-community** — Triggers community-extensible: g2+ stelt voor, g1 keurt goed. Workflow: voorstel → review-queue → approve/reject.
- [ ] **#negate-trigger** — Negatie-trigger: "nee niet [onderwerp]" → exclude voor sessie. Hook in session_state met `excluded_topics[]`.

### Cluster C — Command Registry uitbreiding (fundering v6_command_registry_001 leeft al)
- [x] **#cmd-registry** — ✅ DONE (v6_command_registry_001): elke api-endpoint krijgt intent-tags. 27 commands in `/data/system/command_registry.json`. Uitbreiden naar alle 418 endpoints (Synapse-scan).
- [x] **#intent-extractor** — ✅ DONE (v6_command_registry_001): user-zin → tag-vector via `modules/intent_registry/extractor.py` (~150 synoniem-mappings).
- [x] **#cap-matcher** — ✅ DONE (v6_command_registry_001): tag-overlap Jaccard-score → top-3 kandidaten in `matcher.py`.
- [ ] **#cmd-disambiguation** — Bij meerdere matches → "Bedoelde je X of Y?". UI-panel + chat-response. Disambiguation flag is al in matcher; UI moet nog.
- [ ] **#cmd-compose-seq** — Sequential composition: command-keten bouwen voor onbekende intent. Bv. "stuur Gijs €10 voor zijn verjaardag" → wallet.transfer + bark.send.
- [ ] **#cmd-fallback** — Fallback chains: dichtstbijzijnde match + user-bevestiging vóór execution.
- [ ] **#cmd-skill-discovery** — Spark biedt aan herkende compositie als snelkoppeling op te slaan. Fundering staat: `intent_log.jsonl` + `/skills/candidates`. UI accept/reject mist nog.

### Cluster D — Gradatie-enforcement
- [ ] **#cmd-gradatie-files** — Per-gradatie command-JSON (commands_g1.json t/m commands_g7.json). Naast bestaande `help_g{n}` per gradatie. Beheer-UI per file.
- [ ] **#cmd-grad-lock** — Gradatie-lock check IN command-registry, niet alleen in UI. Backend-guard ook bij chat-routed commands.
- [ ] **#cmd-priv-fallback** — Privilege-fallback: blocked command → bied request-flow aan ("Vraag toestemming aan beheerder?"). Mini-inbox voor admin.

### Cluster E — Conversational depth
- [ ] **Spark vraagt elke 4e interactie**: *"Wat denk jij dat ik zou moeten kunnen?"* → log-naar `intent_log.jsonl` + categoriseer als feature-request. Voedt skill-discovery (#cmd-skill-discovery).

### Cluster F — Volgorde-suggestie (bouwen in deze volgorde)
1. **#kb-tag-singular** + **#kb-verb-stem** (fundering voor similarity)
2. **#kb-similarity** + **#kb-node-hierarchy** (semantische upgrade)
3. **#cmd-disambiguation** (UI op bestaande matcher-output)
4. **#cmd-skill-discovery** (accept/reject UI op bestaande intent_log)
5. **#trigger-hooks** + **#trigger-community** (gemeenschap-uitbreidbaar)
6. **#cmd-gradatie-files** + **#cmd-grad-lock** + **#cmd-priv-fallback** (privacy/governance)
7. Rest in fluctuerende volgorde

---

## 🎭 Backlog 2026-05-28 — D&D / Spark World (29 items)

> Veel hiervan haakt op **v4_dnd_001** (lore index, aura, observatie, world state — reeds live).
> Onderstaande lijst toont per item de status zodat we weten wat fundering al is en wat nog open is.

### Cluster G — D&D Levende Wereld (avatars, aura, observatie)
- [x] **#lore-index** ✅ DONE (v4_dnd_001): `/data/dnd/lore_index.json` met 7 avatars-as-functions + 6 behavior-categorieën met aura-kleuren. Open: uitbreiden met Base Line fracties + elementen-systeem.
- [x] **#aura** ✅ DONE (v4_dnd_001): `GET /api/dnd/aura/{user_id}` berekent live top-3 categorieën met gradient-kleuren. UI: Persoonskaart toont gradient-glow + bar-layers.
- [x] **#spark-observe** ✅ DONE (v4_dnd_001): avatar-change → auto observe-call; Spark begroet bij eerste Spark AI tab-open met benoeming van events; mark-spoken voorkomt herhaling.
- [x] **#avatar-functions** ✅ DONE (v4_dnd_001): 7 avatars-as-functions (Het Eerste Licht=begin, De Reaper=einde, Boekhouder=balans, Harry=tijd, Madelief=emotie, Mr Smith=manipulatie, Story Teller=geheugen). Acteren actief in community.
- [x] **#world-state** ✅ DONE (v4_dnd_001): `GET /api/dnd/world-state` aggregeert per-entiteit dominantie over alle users. >60% = `dominant=true` flag (klaar voor aspect-bark trigger).
- [x] **#hyperlink-stats** ✅ DONE (v4_dnd_001): gedrag → identiteit zonder cijfers; behaviors verschijnen als pills op Persoonskaart met kleur-codering.
- [ ] **#persoonskaart** — Persoonskaart UI uitbreiden met **inventory + slots/gewicht** systeem (rugzak/cape/helm/schoenen). Inventory leest uit user-container + KB v2 kaarten met `dnd.type=item` tag.
- [ ] **#body-slots** — Body-slots na Rugzak: helm / cape / schoenen / handschoenen / amulet. Equip-mechanic via D&D-kaart drag-drop. Effect-modifiers op aura.
- [ ] **#particles** — Particles op aura: klok-deeltjes (Harry), runen (Smith), mist (Reaper), confetti (Madelief). Canvas-overlay op gradient-glow.
- [ ] **#auto-bark** — Auto-bark als community reward bij milestone-unlock. Bot kiest passende reactie op basis van event-type.
- [ ] **#aspect-bark** — Aspect-bark bij dominantie (>60% van events in een week). Avatar reageert met spreuk uit lore_index. Hook in `world-state` cron.
- [ ] **#emergent-quests** — Quest-systeem ontstaat **uit gedragspatronen**. Pattern-detector scant behavior-tracker → genereert "Vind de balans"-quest als user 7d veel kb_create + 0 emotie-trigger heeft.
- [ ] **#lore-currency** — Zeldzame KB-kaarten = waarde. Kaart met `dnd.rarity=legendary` + tag `lore/dnd/spark world/base line` telt mee in user-score. Display als trophy-grid.
- [ ] **#dynamic-canon** — Vervormde verhalen: canon herschrijven via community-consensus. Bv. 5+ users met `dnd_choice_horen` → "Horen werd het pad". Vereist 51%-vote in community.

### Cluster H — Stem-laag + Bots
- [x] **#bot-voice** ✅ DEELS DONE (sessie 8): STT/TTS toggles per bot in `auth/admin/bots/{bot_id}/settings` met 6 OpenAI stemmen. Audio-uitspeel hangt nog (TTS settings opgeslagen maar player niet gehookt).
- [ ] **#dnd-voice-cards** — D&D-kaart als spreekkanaal: bot leest kaart-tekst (`vraag` + `antwoord`) voor via TTS. Hook in `cards/service.py::play_card_voice(card_id, bot_id)`.

### Cluster I — Spark World (NL als fantasy-continent)
- [ ] **#sw-nl-base** — **Nederland als fantasy-continent** (basiswereld). Begin met geografische skelet uit Open Street Map → vertaal naar lore-vlakken.
- [ ] **#sw-facties** — **12 provincies = 12 facties** met eigen kleur/wapen/leider. Hook in lore_index als sub-tree.
- [ ] **#sw-the-north** — **Startgebied "The North" — Groningen**. Eerste fase content. Locaties: Stad-Groningen (hoofdstad), Lauwersmeer (mistgebied), Borkum-fjord.
- [ ] **#sw-foto-flow** — **Foto → Fantasy workflow** (asset creator). User uploadt foto → AI genereert lore-asset (Nano Banana / Sora 2). Output landt in system_archive met tag `sw_asset`.
- [ ] **#sw-asset-types** — 4 asset-types: wereldkaart (continent-view) / stad top-down / scene view (1st-person) / NPC avatars. Per type aparte prompt-template.
- [ ] **#sw-realtime-weer** — **Realtime weer-koppeling per regio** (weer.nl per provincie). Voedt sw-weather-mood (#weather-mood is breder).
- [ ] **#sw-realtime-tijd** — **24-uurs realtime dag/nacht sync** (zonsop/zonsondergang per breedtegraad). Beïnvloedt scene-lighting in asset-render.
- [ ] **#sw-char-sheet** — **D&D character sheet UI (Stormhaven-stijl)**: stats / inventory / aura / lore-currency / faction-banner. Vervangt huidige Persoonskaart.
- [ ] **#sw-multi-shop** — **Multi-tenant shop per user** (in-world eigen tab). Reeds: Winkelstraat-hub. Sw-extensie: shop-locatie in fantasy-stad (Groningen-marktplein).
- [ ] **#sw-avatar-tshirts** — **Avatar-T-shirts (on-demand print)**. Roadkill-merch uitbreiden met user-avatar-as-design. Print-on-demand via Printful API (P3).
- [ ] **Per-user GB opslagsysteem** — 1GB standaard, bij te kopen met ROAR/EUR. `users/{user_id}/_meta.json.quota_gb`. Block uploads bij overschrijding. Voedt sw-foto-flow want assets schalen snel.

### Cluster J — Andere
- [x] **#weather-mood** ✅ ROADMAPPED (sessie 8): weer.nl koppeling → cloud/humeur per user. **Niet alleen voor Spark** (universeel). Wachten op user-locatie-veld in profile.
- [x] **#community-plus** ✅ ROADMAPPED: token-tier (1+ token = community member, bot-toegang ∝ wallet). Voorbereid in shop/balance endpoints.

### Volgorde-suggestie cluster G→I (na P0 boekhouding-hooks)
1. **#persoonskaart + #body-slots** — Eerste visuele win (bestaande aura uitbreiden met inventory-grid).
2. **#aspect-bark** — Hook bovenop bestaande `world-state >60%` flag → eerste autonoom-gedrag.
3. **#emergent-quests** — Pattern-detector op bestaande behavior-tracker counters.
4. **#sw-nl-base + #sw-the-north** — Begin klein (1 provincie) als testbed.
5. **#sw-foto-flow** — Pas zodra Nano Banana / Sora budget vast staat (kost credits per asset).
6. **#sw-char-sheet** — Vervang Persoonskaart pas als alle data-streams er zijn.

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
