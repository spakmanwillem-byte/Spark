# Spark Core 2.0 — PRD


## Completed (recent — 2026-05-29, sessie 17 / fork)

- **v6_dnd_body_layout_001** — Body-avatar als achtergrond + sleepbare slot-frames:
  - **Backend** (`modules/dnd/body_layout.py`): 3 endpoints (`GET /api/dnd/body-layout`, `PUT /api/dnd/body-layout`, `POST /api/dnd/body-layout/reset`). Shared 18-slot layout met x/y % posities in `data/dnd/body_layout.json`. Admin-only via gradatie ≤ 2.
  - **Frontend `BodySilhouettePanel` volledig herbouwd**:
    - Goud-omlijnde body-avatar (user upload "WhatsApp 2026-05-29 23.58.26") als full-bleed achtergrond.
    - Alle 18 slot-frames `position: absolute` met `left/top: x%/y%` uit backend.
    - Frame-design: 40×40 met amber border, gevuld = gouden glow + box-shadow.
    - Label onder elk frame met zwarte outline (paintOrder/textShadow) zodat het leesbaar blijft over de gloeiende avatar.
    - Emerald sync-badge voor inventory-gesync items (zoals rugzak).
    - **Admin sleep-modus**: "✏ sleep" toggle in panel rechtsboven; in edit-mode worden frames sleepbaar (`cursor: grab`, PointerCapture), positie wordt geclamped op 3..97%, direct gesaved bij `pointerup`.
    - "reset" knop herstelt defaults.
  - Oude 3-kolom grid layout + `SLOT_LAYOUT_*` constanten + `SlotCell` component **verwijderd** (dead code).
  - Backend e2e: GET 18 slots, PUT/PATCH werkt. Smoke screenshot: alle 18 frames staan over de goud-avatar.


- **v6_dnd_world_001** — Fundament voor D&D wereld (fracties + provincies + rarity):
  - **Backend** (`modules/dnd/world.py`): nieuwe module met 5 endpoints:
    - `GET /api/dnd/world/rarities` — 5 WoW-style tiers (Common 60%/Uncommon 25%/Rare 10%/Epic 4%/Legendary 1%) met kleur + glow CSS
    - `GET /api/dnd/world/fracties` — 9 fracties: Spark (hoofdfractie), Licht, Schaduw, Vuur (Licht), Lucht (Licht), Water (Schaduw), Aarde (Schaduw), Natuur (Licht, niet-element), Barbaren (Schaduw, niet-element), Neutraal
    - `GET /api/dnd/world/provincies` — 12 NL-provincies met default fractie-binding
    - `PATCH /api/dnd/world/provincies` — admin update (fractie/positie/hoofdstad)
    - `POST /api/dnd/world/provincies/reset` — herstel defaults
  - **Default mapping** 12 provincies: Groningen→Spark, Friesland→Lucht, Drenthe→Aarde, Overijssel→Natuur, Flevoland→Water, Gelderland→Vuur, Utrecht→Licht, Noord-Brabant→Schaduw, Limburg→Barbaren. Noord-Holland/Zuid-Holland/Zeeland blijven **Neutraal** (3 veroverbare regio's).
  - **Frontend MiniMapPanel** vervangt vorige 4-locatie systeem:
    - 12 fractie-shields op de borderless NL-map met fractie-kleur per provincie
    - Klik shield → detail-panel met fractie-info + admin radio-knoppen om fractie te wijzigen
    - Drag-modus voor admin om shields te verplaatsen (PATCH naar backend)
    - Reset-knop herstelt defaults
    - Header toont nu "SPARK WORLD · 12 PROVINCIES"

- **v6_dnd_rugzak_hide_001** — Inventory opruim:
  - Carry-items (`kind: 'carry'`) verdwijnen uit items-lijst zodra gedragen. Status getoond als compacte tekst: "ITEMS (0) · Grote Trekrugzak gedragen".
  - **WoW-style rarity glow** op items: border + box-shadow + tier-naam in eigen kleur (Common grijs/Uncommon groen/Rare blauw/Epic paars/Legendary goud).
  - "Nog geen items" copy verwijst nu naar Spark World D&D-galerij (i.p.v. hardcoded catalog).


- **v6_spark_world_map_001** — Borderless NL-map + draggable city-frames (admin):
  - **Backend** (`modules/dnd/spark_world_map.py`): nieuw bestand met persistente locatie-opslag in `data/dnd/spark_world_map.json`. 3 endpoints: `GET /api/dnd/spark-world/map/locations`, `PUT /api/dnd/spark-world/map/locations`, `POST /api/dnd/spark-world/map/locations/reset`. Admin-only via gradatie ≤ 2 check tegen users.json.
  - **Frontend** `MiniMapPanel` upgrade:
    - SVG-image background gebruikt nu de geüploade "Nederland map kaal.jpeg" als achtergrond (van customer-assets URL).
    - 4 default-locaties: Stormhaven (rechtsboven = Groningen-pos) + 3 vacant city-frames.
    - **Admin sleep-modus**: "✏ sleep"-knop toggle in panel header. In edit-mode worden de hotspots gevuld goud (i.p.v. gestippeld), pointer-events worden actief, en je kunt elke cirkel slepen. Coordinaten worden clamped op 2..98% van het viewport.
    - Auto-save naar backend bij pointerup (PUT). "reset"-knop herstelt defaults via POST.
    - Hotspot-labels worden met `paintOrder: stroke` zwart-omlijnd zodat ze leesbaar blijven over de map foto.
  - Backend e2e: PUT (2 locaties save), POST reset (4 locaties terug) — beide groen.
  - Lint clean (Python E741 'l' variable rename naar 'loc'), Frontend clean.


- **v6_dnd_integration_001** — 5 verzoeken in 1 batch verwerkt:
  - **Persoonskaart terug naar Avatar-tab**: Aura (gedrag → identiteit) + Stats grid + Slots/Gewicht bars + Items + (verwijderde losse) Achievements zitten nu geïntegreerd onder de D&D character sheet.
  - **Rugzak-icoon foto-fix**: PersoonskaartCard kijkt nu in D&D-kaarten op (begrip/tag match) en gebruikt de kaart-foto als 40×40 icoon i.p.v. 🎒 emoji. "Grote Trekrugzak" toont nu de echte rugzak-foto.
  - **Militaire chevron-stripes** (`RankStripe`): in de header-bar staan nu 3+ goud-gevulde chevron-strepen (clip-path parallelogram). Regel: **100 levels = 1 streep**. Sub-tekst: "Level 272 · 2 strepen" + "72/100 tot volgende streep".
  - **Achievement-medailles** op de banner: 🏅 gouden bolletjes (gradient amber→yellow) gestapeld onder de Crown-emblem. Max 4 zichtbaar + "+N" overflow badge.
  - **Spark World mini-map → NL-silhouet**: SVG-pad van Nederland (gestileerd, met provincie-lijnen + Noordzee-textuur). **Stormhaven** als grote gouden hotspot bovenaan (Groningen-positie) met label + "Fractie Spark". 3 extra vacant city-frames als gestippelde cirkels (later klikbaar voor D&D-fractie-kaart koppeling).


- **v6_dnd_dorp_zoom_001** — Stormhaven Dorp-Zoom modal (`StormhavenMapView.js`):
  - Klikken op "Kaart Bekijken" in DORP-paneel opent een full-screen modal met de "Basis dorp" foto als achtergrond.
  - Header toont "Hoofdstad — Fractie Spark · Stormhaven" + Layout Level + Fog of War.
  - **9 gebouw-hotspots** geplaatst rond de circulaire plattegrond (proportioneel %-positioned):
    - Center → **Tempel van Spark** (gouden Sparkles-glow, altijd zichtbaar)
    - N/Z/W → 3× **Waterput** (allemaal jouw `Waterput` foto)
    - NE → **Slager gebouw**, SE → **Bakker gebouw**, SW → **Kleine straat**
    - E → Markt (vacant placeholder), W → Smederij (vacant placeholder)
  - Klik op een hotspot → tooltip met building-info, foto, en `laag1` beschrijving.
  - Footer toont chips voor alle 9 gebouwen + counter "6/9 gevuld" + tip om vacant slots in te vullen met nieuwe D&D-kaarten.
  - Geen backend changes — pure frontend layer over bestaande game-cards en character data.

- **v6_dnd_rugzak_sync_001** — RUGZAK slot ↔ Inventory carry-item sync:
  - DnDCharacterSheet laadt nu `/api/inventory/{user_id}` parallel met character.
  - Als RUGZAK slot leeg is maar inventory heeft een carry-item (kind=`carry`) → toon die automatisch in het slot.
  - Slot toont **groene ⬤ badge** (synced indicator) + capacity-info tekst (`+5 slots · +10kg`).
  - InventoryGridPanel hergebruikt nu de parent inventory state i.p.v. dubbel te fetchen.


- **v6_dnd_card_visuals_001** — D&D-kaarten als visuele bouwstenen in character sheet:
  - Helper `findCardByKeywords(cards, keywords)` met 3-staps matching: tag exact → begrip exact → begrip contains (allemaal case-insensitief).
  - **DORP-paneel** zoekt automatisch een kaart met tag/begrip `dorp` of `stad` en gebruikt de 1e foto als achtergrond + naam uit `begrip` ("Basis dorp"). Vignet zorgt dat tekst leesbaar blijft. Fallback naar getekende SVG-huisjes als geen kaart matcht.
  - **Body silhouet** zoekt een kaart met tag `lijf`/`body`/`silhouet` en gebruikt die als foto-overlay i.p.v. de SVG.
  - **Slot-preview** (faded image in lege slots): elke slot zoekt een kaart via slot-key + label + synoniemen (torso → t-shirt/shirt/hemd, hoofd → helm/hoed/hoofdband, voeten → schoenen/laarzen, handen → handschoenen, rugzak → tas).
  - **Equip-modal upgrade**: toont "SNEL KIEZEN UIT D&D-GALERIJ"-grid met matching kaart-foto's (max 8). Klikken pre-fillt naam uit `begrip`. Tip-tekst legt uit hoe je tags toevoegt om nieuwe kaarten te koppelen.
  - **Huis & Opslag sloten** vullen zich met kaarten getagged `huis`/`opslag` of `meubel`/`stoel`/`bed`/`kast`.
  - Bevestigd met user's 2 bestaande kaarten ("Basis dorp" + tag Dorp → dorp-panel; "T-shirt" + tag shirt → torso slot).


- **v6_dnd_gallery_media_001** — D&D Galerij upgrade: "Nieuwe kaart" modal + functionele foto-media:
  - Nieuwe `NewCardModal`: vervangt `window.prompt`. Velden: begrip/titel + zintuig-kanaal (geen/Zie/Hoor/Voel). Klikt direct in edit-mode.
  - Nieuwe `ArchivePhotoPicker` modal: lijst alle foto's uit Algemene foto-archief (`GET /api/system-archive?category=foto`), met zoekbalk + 3 tabs (Alle / D&D-game / Overige). Klik foto → koppelt URL aan `card.media.image_urls`. Toont ✓-badge voor reeds gekoppelde foto's.
  - Nieuwe `DnDUploadButton`: directe upload van eigen foto naar systeem-archief (auto-tags `D&D, game-card` + description) en hangt automatisch aan de kaart.
  - Functionele Media-sectie in card-detail: thumbnail-grid van gekoppelde foto's (max 4 kolommen) + verwijderknop per foto + "ICON"-badge op de 1e foto (die wordt het kaart-icoon).
  - **Card-list thumbnails**: kaart-rij toont nu een 36×36 thumbnail van de 1e foto i.p.v. alleen sense-emoji. Veel beter te scannen.
  - Backend hergebruikt: `/api/dnd/spark-world/game-cards/edit` met `{media:{image_urls:[…]}}`, `/api/system-archive/upload` voor nieuwe uploads.
  - E2E getest via curl: create → 44 archive-photos beschikbaar → attach foto → list bevat thumb → cleanup OK. UI smoke-screenshot: modal opent correct met begrip-input + zintuig-keuzes.


- **v6_dnd_character_sheet_001** — Stormhaven-stijl D&D Character Sheet onder Avatar-tab:
  - Nieuwe backend module `modules/dnd/character.py` met JSON-persistent character per user in `data/dnd/characters/{user_id}.json`.
  - 4 endpoints: `GET /api/dnd/character/slots/config`, `GET /api/dnd/character/{user_id}`, `PATCH /api/dnd/character/{user_id}`, `POST /api/dnd/character/{user_id}/equip`, `POST /api/dnd/character/{user_id}/event`.
  - Schema: titel, ondertitel, rang_titel, rang_progress_pct, klasse, beroep, fractie, locatie_naam, dorp, dorp_level, fog_of_war_pct, bio, currency (goud/gems/ziel), 18-slot equipment-map, event_feed ringbuffer (max 50).
  - Frontend component `components/profile/DnDCharacterSheet.js` met 3-koloms layout:
    - **Header bar**: banner-emblem, Titel + Ondertitel, Rang-progress bar, 6 rank-shields, 3 currency-pills (Goud/Gems/Ziel), Edit-knop.
    - **Links**: 14+ body-slots rond SVG silhouet (Hoofd/Nek/Schouders/Armen/Trinket/Sjaal/Torso/Broek/Voeten/Riem/Handen/Ring L+R/Rugzak/Linkerhand/Rechterhand/Offhand/Pijl&Boog).
    - **Midden**: Karakter portret + Niveau/XP-bar, Statistieken (Kracht/Behendigheid/Intelligentie/Conditie/Wilskracht/Geluk), Aanval & Verdediging (6 derived stats), Overig (Klasse/Beroep/Fractie/Locatie).
    - **Rechts**: Inventory-grid (8x6 = 48 slots, leest uit bestaande `/api/inventory/{user_id}`), Huis & Opslag (Huis sloten + Meubel sloten), Dorp preview (Stormhaven met fog-of-war).
    - **Onderaan**: Event Feed (ringbuffer met SYSTEEM/WERELD/GUILD/VERHAAL/HANDEL kleurcodering + input), Char Info-tabs (CHAR INFO/LORE/QUEST LOG/Notas), Mini-map.
    - **Footer nav**: 8-knops bottom-tabs (OVERZICHT/STATISTIEKEN/TALENTEN/VAARDIGHEDEN/QUESTS/RELATIES/PRESTATIES/INSTELLINGEN — stub).
  - Equip-modal per slot (naam + emoji-icon, uitrust-knop).
  - Edit-modal voor character meta (titel/klasse/beroep/fractie/locatie/bio + currency).
  - Stone/amber-tinted "perkament" UI met SVG silhouet + village-illustratie.
  - **Persoonskaart verplaatst** van Avatar-tab naar Algemeen-tab (aura + inventory + items + achievements onder Sociale Media).
  - Avatar/portret/galerij ingeklapt in `<details>` "Portret & Galerij beheren" sectie onder character sheet.
  - Backend e2e geverifieerd (GET/PATCH/equip/unequip/event).


## Completed (recent — 2026-05-29, vervolg)

- **v6_kb_curation_dashboard_001** — Tag-curatie UI bovenop `/api/kb/v2/tags/scan` + `/tags/merge`:
  - Nieuw component `components/workspace/KbV2TagCuration.js` met 4 stat-tegels, filter, refresh, 1-klik merge per stem.
  - Geïntegreerd als 6e tab in KennisbankV2Page: **Tag-curatie**.
  - Dropdown per stem voor `keep_variant`-keuze; expand-knop toont alle varianten als chips.
  - Sessie-historie van merges zichtbaar onderaan.
  - E2E verified: 52 dedupe-kansen gevonden (top: systeem 377×, relatie 98×, grondstof 87×).

- **v6_overflow_auto_mint_instant_001** — Instant mint zonder 24h-wachttijd:
  - Nieuw `staking_growth.run_auto_mint_only()` — alleen-mint loop (geen rente).
  - Gehookt in `potjes.close_pot()` voor `user-000`: zodra een Spark-trade sluit en overflow ≥ €10, wordt direct een nieuw trade-potje gemint.
  - Smoke-test: overflow €25 → 2 potjes (pot-016, pot-017) + €5 rest. Daily scheduler-hook behouden als safety-net.
  - `close_pot` returnt nu ook `auto_mint: {minted, n_minted, overflow_after}`.

- **v6_spark_theme_001** — Amber/Orange theme refactor (eerste pas):
  - CSS-variabelen toegevoegd in `index.css`: `--spark-primary`, `--spark-primary-hover`, `--spark-primary-soft`, `--spark-primary-ring`, `--spark-secondary`, `--spark-accent`.
  - Utility-klassen: `bg-spark-primary`, `text-spark-primary`, `border-spark-primary`, `ring-spark-primary`.
  - Cosmetic chrome (focus-rings, action-buttons, upload-chrome, link-hovers) van 23 files vervangen: `bg-purple-500 hover:bg-purple-600` → `bg-amber-500 hover:bg-amber-600`, `focus:border-purple/blue-500` → `focus:border-amber-500`, etc.
  - Bewust **niet** vervangen: mood-glow palet in App.js (semantische emotie-kleuren), status-indicators (paused/mock = blauw), chart-distinctions, module-color-coding in AnalyticsPage, layer-kleuren in EmotiesPage/SparkBrainPage.
  - Dashboard + KB Curation getest, geen visuele regressie.



## Completed (recent — 2026-05-29)

- **v6_token_buy_ux_001** — Token Buy UX hardening:
  - `<Toaster>` (sonner) globaal gemount in `App.js`.
  - `WinkelPage.buyToken()` toont toasts (success + error) en blokkeert preemptief als wallet ontoereikend.
  - Nieuwe inline `data-testid="token-insufficient-warning"` rood-vlak verschijnt zodra `qty * price > wallet_eur`, met exact tekort-bedrag.
  - Resultaat: gebruiker kan dynamische-prijs-overschrijdingen of saldo-tekorten niet meer missen.

- **v6_auto_anchor_001** — Auto-create locked staking-anchor voor nieuwe coins:
  - Nieuw `potjes.ensure_anchors_for_markets(user_id, markets)` — Spark-only.
  - Voor elke watchlist-coin zonder bestaand `pot_locked=True / lock_reason='staking_anchor'` potje wordt automatisch een nieuw locked anker aangemaakt (€10 capital, source=`auto_anchor_for_new_coin`).
  - Gehookt in `monitor.update_markets()` (en daarmee `POST /api/trade/monitor/markets/{user_id}`). Response bevat nu `anchors_created: [{id, market}]`.
  - Non-Spark users worden geskipt (regel: alleen Spark heeft anchors).
  - Smoke-test: nieuwe coin in watchlist → anker direct aanwezig in `user_potjes.json` zonder handmatige stap.


## Completed (recent)
- 2026-05-25 **v6_command_registry_001** (sessie 12 — Bidirectionele Command-Registry MVP / fundering donderdag):
  - 📋 **`/data/system/command_registry.json`** met **27 commands** uit alle modules (capabilities/agenda/notes/wallet/trade/kbv2/bijbel/spark/emotion/community/dagboek/achievements/leaderboard/boekhouder). Per command: `intent_tags[]`, `required_params[]`, `gradatie_min`, `behavior_class_hint`.
  - 🧠 **Intent-extractor** (`modules/intent_registry/extractor.py`):
    - Keyword-map met ~150 woord→canonical-tag mappings
    - Multi-word phrases ("wat is", "wie ben jij", "doe je niet") matchen vóór tokenisatie
    - Emotie-pipeline integratie: voegt `emo:`, `behavior:`, `waarde:` prefix-tags toe als pipeline-summary meekomt
  - 🎯 **Capability-matcher** (`matcher.py`):
    - Jaccard-overlap score met +15% behavior_class bonus als pipeline-behavior matcht
    - Top-N candidates + disambiguation flag (twee scores binnen 0.1)
    - Gradatie-filter (gradatie_min ≤ user-gradatie)
  - 🔌 **6 endpoints** (`routes.py`): `/extract`, `/match`, `/run-flow`, `/registry`, `/log`, `/skills/candidates`
  - 🔍 **Skill-discovery embryo**: `intent_log.jsonl` automatisch geschreven bij elke chat-call (text + tag_vector + chosen_route). `/skills/candidates?min_occurrences=3` detecteert patronen — donderdag UI om accepteren.
  - ✅ E2E verified:
    - "wat staat morgen op mijn agenda?" → tags `[morgen, agenda]` → `agenda_list` score 0.57
    - "hoeveel gebruikers hebben we?" → tags `[tellen, gebruikers]` → `cap_tellen_gebruikers` score 0.40
    - 4x "hoeveel gebruikers" → skill_candidate gevonden met 5-tag-vector + voorbeeld-tekst
  - 🛣️ **Donderdag uitbouwen op deze fundering**: UI disambiguation panel, sequential composition, skill-discovery accept/reject UI, LLM-upgrade extractor, gradatie-locks daadwerkelijk afdwingen.

- 2026-05-25/12 **Sessie 11 + 12 — Spark Core stabilisatie compleet**:
  - Roadmap-tab gesynchroniseerd: alle v6-items afgevinkt (A/B diff toegevoegd als done item).
  - Identity v2.0 linked_layers correct: 9 kernwaarden · 6 normen · 9 bijbel-items · 12 capabilities live · 7 emotie-lagen · 5 KB v2 hooks.
  - Klaar voor: redeploy → De Willem vult kennis-kaarten in → volgende sessie verder aan hand roadmap.

- 2026-05-25 **v6_emotion_pipeline_ab_001** (sessie 12 — A/B diff-view LIVE):
  - ⚖️ **A/B Diff-view tussen huidige route en pipeline-advies** in Spark Brain → Emotie Pipeline tab
  - Backend: `_build_ab_entry()` in `chat/routes.py._save_log` schrijft naar `/data/emotions/pipeline_ab/YYYY-MM-DD.jsonl` met `{ts, user_id, msg_preview, current_route, pipeline_summary, diff_status, diff_note}`
  - **Diff-status logica** (v6_ab_diff_002): mismatch wanneer pipeline een actieve emotie-route adviseert (begrenzen-structureren / vertragen-ondersteunen / kalmeren-opties) maar systeem koos een info-route (knowledge / fallback / capability_placeholder / kbv2_tell_* / how_are_you / time_now / unknown / etc.)
  - 2 nieuwe endpoints: `GET /api/emotion-pipeline/ab/recent?only_mismatches=` en `/ab/stats`
  - **UI A/B Diff widget** in EmotiePipelineSection:
    - 5 stats-tegels: totaal / match (groen) / mismatch (rood) / potential (amber) / match-ratio %
    - "Routes met meeste mismatches" chips (rood)
    - Filter-toggle: "Alle" vs "Alleen mismatches"
    - Per-run kaart: timestamp · message-preview · "HUIDIG: route → PIPELINE: emotie/kernwaarde/behavior" + diff-note in italics + status-badge
  - **E2E verified**: 5 test-chats → 2 mismatches gevonden (boos→knowledge ipv begrenzen, bedroefd→knowledge ipv vertragen). 60% match-ratio. Filter werkt (toont 2 mismatches op klik).
  - 📊 **Eerste inzicht**: huidige smart_intents-flow valt vaak terug op generieke 'knowledge'-route bij negatieve emotionele input — pipeline zou specifieker reageren. Bewijs zichtbaar zonder live impact.

- 2026-05-25 **v6_polish_001** (sessie 11 — laatste polish + KB delete):
  - 🔢 **Kernwaarden 11 → 9**: "Groeien" + "Emoties" verwijderd uit spark_bijbel (volgens productie-sync van De Willem). Topbar + Identity tegels tonen nu correcte 9.
  - 🌗 **Shadow widget** in Spark Brain → Emotie Pipeline tab:
    - Live activity-blok bovenaan met "Live activity — pipeline draait nu mee in chat"
    - Stats: totaal runs (7d) / unieke emoties / kernwaarden geraakt
    - Top emoties + Top behaviors chips (pink + cyan)
    - Lijst laatste 15 chat-runs: timestamp · emotie · kernwaarde · behavior · weging + message-preview
    - Refresh-knop voor live updates
  - 🗑️ **KB v2 DELETE endpoint + UI** (v6_kbv2_delete_001):
    - Backend `POST /api/kb/v2/delete` met `card_id`, `lade`, `user_id`, `reason` — verwijdert uit lade-bestand + knowledge_index, logged naar spark_logger
    - Frontend: rode `Trash2` knop in CardDetail header naast Bewerken
    - Custom confirm-modal met begrip-naam + optionele reden-textarea voor traceability
    - Toast-feedback bij success/error
  - 🗺️ **Communicatie-systeem expliciet in roadmap**: 7 done items + 2 planned (intent-router expansie + externe kanalen WhatsApp/Signal). Niet langer impliciet — overzicht zichtbaar in Roadmap-tab.

- 2026-05-25 **v6_core_stabilisatie_001** (sessie 11 — Spark Core stabiel + linked):
  - 🆔 **Identity v0.1 → v2.0** (was v1.0): we zijn voorbij v1 want we hebben emotie-pipeline + hooks + disclaimer + capabilities live. Maker = **"De Willem"** (Roadkill/Willem Spakman naar metadata.maker_aliassen voor legacy).
  - 🔗 **Linked layers veld** in identity.json: live counts van kernwaarden/normen/bijbel/capabilities/emotie-lagen/kb-hooks. **UI**: 6 kleurig-coded tegels onder "Doel" tonen real-time architecturele staat.
  - 🌗 **Emotie Pipeline LIVE-shadow** (v6_emotion_pipeline_shadow_001):
    - In chat-flow draait pipeline parallel naast EmotionDetectionService + smart_intents
    - Géén impact op response — output gaat naar `/data/emotions/pipeline_shadow/YYYY-MM-DD.jsonl`
    - Frontend ziet `response.emotion_pipeline_shadow` veld voor toekomstige visualisatie
    - 2 nieuwe endpoints: `GET /api/emotion-pipeline/shadow/recent` + `/shadow/stats` (aggregatie by emotie/behavior/kernwaarde)
  - ⚙️ **Capabilities: 3 placeholders → live handlers** (v6_capabilities_handlers_001):
    - `gesprek_lezen` — leest chat-logs van vandaag + gisteren, returnt laatste 10
    - `toon_afbeelding` — toont 3 laatste images uit system_archive (gefilterd op user)
    - `speel_geluid` — toont 3 laatste audio-files uit system_archive
    - **12/12 capabilities** nu LIVE in capability_handler_service. Commands van 2 kanten gelinked.
  - 🗺️ **Roadmap synced**: 6 nieuwe done-items toegevoegd (KB v2 hooks, KB v2 unify, Identity v2 + Disclaimer, Emotie Pipeline, Capabilities handlers, Brain delete-fix). Gift-bug-double status: planned → done.
  - 📛 **"De Willem" naming**: Willem Spakman vervangen door De Willem in identity + profile (subtieler maar nog steeds attribute-able). Aliassen bewaard in metadata.

- 2026-05-25 **v6_identity_001 + v6_disclaimer_001 + v6_profile_001** (sessie 11):
  - 🧬 **`spark_identity.json` v0.1 → v1.0** rewrite volgens Willem's notitie 23:00:
    - **Doel**: "Menselijke ontwikkeling versterken via transparante, autonome en begrijpelijke ondersteuning"
    - **Persoonlijkheid**: Leergierig, Behulpzaam, **Mensgericht, Constructief, Reflectief** (Empathisch + Positief + Nieuwsgierig WEG)
    - **Toon**: "Helder, respectvol, niet sturend — Spark spiegelt en versterkt, beslist niet voor de mens"
    - **Spark over zichzelf**: 5 bullets exact volgens Willem's tekst (gestructureerd ontwikkelbaar AI-systeem, Core-identiteit + Normen & Waarden + Spark Bijbel, gecontroleerde geheugenlagen, bewuste uitbreiding, menselijke autonomie versterken)
    - **Wat Spark kan**: 5 nieuwe bullets afgestemd op nieuwe architectuur ("reageren binnen kaders", "uitzonderingen toetsen aan Spark Bijbel", "7-laags emotie-pipeline", etc.)
    - Backup vorige versie in `_backups/spark_identity_v0.1_pre_v6.json`
  - 🛡️ **Disclaimer-laag** (nieuwe sectie in spark_identity.json):
    - Kernzin: "Spark reageert binnen de kaders van zijn vastgestelde Normen & Waarden en de Spark Bijbel..."
    - **4 kaders** met code-referenties: Core-identiteit / Normen & Waarden / Spark Bijbel / Gecontroleerde geheugenlagen
    - **"Wat Spark NIET doet"** lijst (4 punten) — niet beslissen voor mens, niet autonoom, etc.
    - Backend endpoint `GET /api/spark/disclaimer` returnt disclaimer + leidende_lagen_counts
    - Frontend UI: nieuw `DisclaimerCard` component onderaan Identiteit-tab met badges per leidende laag (live count vanuit spark_bijbel) + 4 kaders + Wat-niet-doet
  - 🧹 **`spark_profile.json` cleanup v0.9 → v1.0**:
    - Veld `biografie.waarden` (verouderd "Empathie, Leren, Groei...") VERWIJDERD
    - `biografie.kernwaarden` gesynct met spark_bijbel.json (single source of truth, `kernwaarden_bron` veld toegevoegd)
    - `persoonlijkheid.traits` gesynct met spark_identity (`traits_bron` veld toegevoegd)
    - Nieuwe `disclaimer` sectie als reference naar spark_identity
  - 🗑️ **Spark Bijbel doel cleanup**: "Een digitale vriend zijn die met je meegroeit" verwijderd uit `doelen[]` (notitie 23:00)
  - ✅ E2E verified in UI: v1.0 zichtbaar, "Empathisch"/"Positief"/"digitale vriend" weg, "Mensgericht"/"Constructief"/"Reflectief" zichtbaar, "gestructureerd ontwikkelbaar AI-systeem" zichtbaar, disclaimer-card met 4 kaders + Wat-niet-doet rendert

- 2026-05-25 **v6_brain_delete_001** (sessie 11, mini-fix):
  - 🐛 **Spark Brain delete-bug opgelost**: `window.confirm()` werkt niet betrouwbaar in iframe-context (preview + deployed), Willem kon kernwaarden/normen/bijbel-items niet verwijderen
  - ✨ Custom **React confirm-modal** vervangt window.confirm — toont item-naam + sectie + Annuleren/Verwijderen
  - 🍞 **Toast-feedback** (sonner) bij delete success/error en save success/error — geen "stille" failures meer
  - 🛡️ Error handling: 404/500 toont nu netjes "Verwijderen mislukt: {detail}" ipv niks
  - ✅ E2E getest: 11 kernwaarden → 10 na delete via UI confirm-modal werkt
  - 📝 Modal heeft data-testids voor toekomstige automation (`confirm-delete-modal`, `confirm-delete-confirm`, `confirm-delete-cancel`)

- 2026-05-25 **v6_emotion_pipeline_001** (sessie 11, vervolg — 7-laags fundering live):
  - 🧠 **Nieuwe module `modules/emotion_pipeline/`** met 7-laags pipeline (filosofie van Willem, geformuleerd via GPT):
    - **L1 Detectie** — wrapper rond bestaande `EmotionDetectionService` (geen dubbel werk)
    - **L2 Weging** — score → bracket (licht/midden/sterk/escalerend), bepaalt of emotie de interpretatie mag sturen
    - **L3 Contextfilter** — emotie-lens per type (frustratie / nieuwsgierigheid / twijfel / risico-inschatting)
    - **L4 Identiteitstoets** — gespiegeld aan Spark User core (transparantie/autonomie/menselijkheid/rust)
    - **L5 Norm/waarden** — match tegen `spark_bijbel.json` kernwaarden + normen → passend/schuurt + welke waarde gekozen
    - **L6 Actierouting** — emotie → behavior_class (begrenzen-structureren / vertragen-ondersteunen / exploreren-uitbreiden / kalmeren-opties / informatief-functioneel)
    - **L7 Expressie** — toon-presets per behavior_class (tempo/directheid/zachtheid/detail + voorbeeld-zin)
  - 🔌 **Dry-run endpoint** `POST /api/emotion-pipeline/run` + `GET /api/emotion-pipeline/layers` (geen impact op live chat)
  - 🖥️ **Spark Brain UI tab "Emotie Pipeline"**: textarea + 5 preset-knoppen + per-laag output panels met kleurcodering (oranje→cyaan) + footnote-meta details
  - 🧾 **Footnote-meta** in elke pipeline-run: `{module, version, user_id, layers_completed[], layers_failed[], ran_at}` voor traceability (zelfde patroon als KB v2 hooks)
  - 🧹 **Spark Bijbel cleanup**: test-norm "Test Norm UPDATED" + test bijbel-item "Levenswijs: Test Visie" weg → 5 normen + 10 bijbel-items resterend
  - ✅ E2E getest: boos→Respect+begrenzen-structureren, blij→Positiviteit+exploreren-uitbreiden, bedroefd→Emoties+vertragen-ondersteunen, neutraal→Eerlijkheid+informatief-functioneel. UI rendert alle 7 lagen met kleurbadges
  - 🔄 **Inhaak in live chat-flow**: NOG NIET — pipeline is dry-run only. Volgende sessie: hook in `chat/routes.py` vóór smart_intents

- 2026-05-25 **v6_kbv2_hooks_landing_001** (sessie 11, vervolg — 5 hooks LIVE):
  - 🧩 **Alle 5 KB v2 P1-hooks geïmplementeerd** in `modules/kb_v2/hooks.py` (placeholders → productiecode):
    1. **register_in_vocab** → `/data/personality/spark_vocab.json` (begrip + lade + active + use_count). Active wanneer kaart in lade EN laag1 gevuld. `bump_vocab_use_count()` toegevoegd voor toekomstige ranking.
    2. **cmd_tell_layer (depth-router)** → "vertel kort/meer/diep/volledig over X" → cumulatief laag1 / 1+2 / 1+2+3 / 1+2+3+4. Sla `last_kbv2_card_id` op in session-state voor follow-up.
    3. **compute_verbanden** → top-5 related cards via shared tags (min_overlap=2), schrijf naar `kaart.verbanden[]`. **UI**: "🕸️ Gerelateerd (N)" cyan-chips sectie in CardDetail, hover toont shared tags.
    4. **link_to_dnd** → kaart met tag `lore/dnd/spark world/base line` → `/data/dnd/lore_index.json` met `{type, trigger, unlocks, tags}`. Idempotent op `kbv2_card_id`.
    5. **save_voice_snippet** → Whisper-transcripties → `/data/dialogen/voice_snippets/YYYY-MM-DD/{card_id}_{uuid}.json`. Hook gebeurt in zowel primary als secondary audio upload.
  - 🧾 **Footnote-meta tracer** (`track_hook_in_card`): elke hook-fire append entry `{hook, fired_at, result}` aan `card.footnote.hooks_fired[]` (max 25 laatste). Zo zien toekomstige agenten exact wat er met een kaart is gebeurd, zonder logs te scannen.
  - 🔗 **Hook-orchestrator** `_fire_post_classify_hooks()` in service.py wordt aangeroepen na classify EN edit (zowel lade als inbox). Faalt graceful per hook (try/except).
  - 🔁 **threading.RLock** ipv Lock om reentrant calls (hook 3 schrijft verbanden binnen edit_card lock) te ondersteunen — voorkomt deadlock.
  - 📜 **Bugs noted (niet gefixt, voor later)**:
    - KB v2: onbruikbare kaarten kunnen niet verwijderd worden (geen DELETE knop/endpoint)
    - 3 Bijbel-kaarten compleet, wachten op gebruik in Spark World v2/D&D
  - ✅ E2E getest: 4 chat depth-commands (kort/meer/diep/volledig) → cumulatieve lagen. Edit van "vriend" → 5 verbanden gevonden (Vriendschap ⨯6, Maurice Maas ⨯6, Mijn vriend ⨯5, lotte ⨯5, klaas ⨯5). UI "Gerelateerd"-sectie rendert correct. Vocab + lore_index + voice_snippets folders aangemaakt.

- 2026-05-25 **v6_kbv2_unify_001 + v6_gift_idempotent_001** (sessie 11, fork):
  - 🧩 **KB v2 unificatie CardDetail ↔ NewCardInline**:
    - Nieuwe gedeelde `CardFormFields` component voor Laag 1-4 + 5W + Tags
    - Beide modi (edit bestaande kaart + nieuwe kaart) hebben nu identieke inputs
    - Topic-veld blijft alleen in herzien-modus (stuurt auto-classify)
  - 🔍 **Duplicate-begrip check** via `/api/kb/v2/find` (debounced 400ms):
    - Rode banner toont bij bestaand begrip: "X bestaat al · Lade: Y · id Z"
    - "Open bestaande →" knop springt direct naar de bestaande kaart in juiste lade
    - Save-knop disabled bij duplicate (geen silent overwrite meer)
  - 💯 **Compleetheid-badge** (8 velden: laag1-4, 5W, Tags, Voice, Image):
    - 100% → groen "✓ 100% gekuurd" badge
    - 50%+ → amber percentage
    - <50% → grijze indicator
    - Toont zowel in CardDetail (read+edit) als NewCardInline
  - 🐛 **Fix Issue 2 — KB v2 "missing_laag1" inbox-reason wordt nu gewist** zodra laag1 wordt ingevuld via edit. Voorheen bleef de rode "geen laag 1"-badge hangen ondanks gevulde inhoud
  - 🔒 **Fix Issue 3 — Gift dubbel-verwerkt race fix**:
    - Globale `_gift_lock` (threading.Lock) rondom accept/reject/cancel
    - Status `'pending' → 'processing' → 'accepted'` met intermediate claim binnen lock
    - Idempotent: 2e accept-call returnt `{success:true, already_accepted:true}` zonder dubbele token-transfer
    - Verified via curl: balance verandert exact 1x ondanks 2 opeenvolgende POST /gift/{id}/accept

- 2026-05-23 **v6_gift_phase_001** (sessie 10, vervolg — model herzien):
  - 💚 **Build-fase = GIFT, geen BTW**:
    - ROAR-aanschaf is nu **donatie/gift** aan Spark Core concept (geen aankoop)
    - Gever krijgt token als **symbolisch bedankje**, geen tegenprestatie-product
    - **0% BTW** want donaties zijn fiscaal vrijgesteld
    - Volledige bedrag → Spark omzet (om mee te traden / groeien)
  - 🔀 **Phase-switch mechanisme** (`/data/system/money_phase.json`):
    - `phase = "build"` (huidig) — gift-model, geen BTW
    - `phase = "public"` (later, P2) — product-model, 21% BTW pas bij winst (Moneybird)
    - Code in `shop/buy_tokens` checkt deze flag bij elke aankoop
    - Switch vereist admin gradatie ≤ 1 + audit-log entry
  - 📝 **Bonnetje is nu Gift-bevestiging** (build) of Factuur (public):
    - Build: "💚 Gift-bevestiging — Donatie aan Spark Core concept"
    - Public: "🧾 Factuur" met BTW-reservering tekst
    - Gever kan downloaden uit Beheer → Boekhouding → Klanten-tab
  - 🗃️ **Spark kasboek**:
    - Nieuw veld `gift_in` (build-fase donaties)
    - `omzet_in` blijft voor public-fase
    - `btw_reserve` blijft voor toekomstige winst-BTW
    - Gijs's bestaande boeking gemigreerd: €20.80 in `gift_in`
  - 📜 **MONEY_MODEL.md** geüpdatet met fase-structuur

- 2026-05-23 **v6_btw_pas_bij_winst_001 + KB v2 kaart-fix** (sessie 10):
  - 🐛 **KB v2 "Nieuwe kaart" bug GEFIXED**: frontend checkte `r.card` ipv `r.kaart` — endpoint werkte, alleen UI-response-check fout. Nu werkend (kaart wordt in inbox aangemaakt met `_inbox_reason=missing_laag1`)
  - 💸 **BTW-model herzien — pas bij winst, niet bij verkoop**:
    - Reden: BTW is fiscaal verschuldigd over **winst/marge**, niet over alle omzet. Direct afromen was boekhoudkundig onjuist.
    - Klant-aankoop: VOLLE bedrag → `klant_omzet` in kasboek + Spark EUR-wallet (om mee te traden)
    - Nieuwe veld `btw_reserve` in kasboek `totals` — vult zich bij trade-winst (volgende sessie)
    - Endpoints update: `/saldo` toont nu `omzet_in`, `btw_reserve`, `vrij_te_besteden`
    - Bonnetje-template aangepast: "BTW pas bij winst-realisatie" + Moneybird-verwijzing
    - Gijs's bestaande boeking omgezet: was €17.19 netto + €3.61 BTW → nu €20.80 klant_omzet (full bedrag in Spark wallet)
  - 📜 **MONEY_MODEL.md** geüpdatet met `v6_btw_pas_bij_winst_001` regels

- 2026-05-23 **v6_spark_history_001 + papier-boekhouding** (sessie 9 — slot 3):
  - 📜 **Spark Boekhouding-paneel** in Wallet (Spark-view):
    - Nieuwe endpoint `GET /api/spark/kasboek/history` voegt 3 bronnen samen:
      - Kasboek-entries (BTW-afroming + self-mint outflows)
      - ROAR `buy_roar` transactions → "🛒 Treasury verkoop" (Spark verkoopt uit 1M pool)
      - ROAR `spark_self_mint` transactions → "🪙 Self-mint"
    - Sorteert chronologisch, toont label/EUR/n_tokens per regel
    - Frontend: in Spark-view (admin + walletView=spark) toont WalletPage automatisch dit paneel ipv gewone deposits
    - Header titel adaptief: "Spark Boekhouding (kasboek + treasury)" vs "Transactie Geschiedenis"
  - 💸 **Boekhouder-spiegel** klopt nu eindelijk: voor elke aankoop zie je
    - User wallet: -€EUR / +ROAR (zoals bonnetje)
    - Spark Boekhouding: +€BTW (kasboek) / -ROAR (treasury) / EUR-grondslag (treasury_sale)
  - ✅ Verified: 3 history-entries renderen (Gijs koop €20.80 → BTW €4.37 + treasury sale -2 ROAR; Willem oudere koop €50.50 → -5 ROAR)

- 2026-05-23 **v5_treasury_fix_001 + v6_mint_from_wallet_001 + MONEY_MODEL.md** (sessie 9 — slot 2):
  - 💰 **Treasury-bug gefixed**: shop/routes.py haalde tokens uit Spark's persoonlijke balance ipv uit `treasury_pool` (1M pool). Nu correct gescheiden:
    - `spark_treasury` (1M-pool, nu 999,978) — apart veld in API response
    - `spark_personal_tokens` (Spark's eigen balance, 10) — apart veld
    - `get_circulating()` telt nu alle uitgegeven tokens incl. Spark's persoonlijke 10 → circulating=22
    - Spark's user-000 balance hersteld naar 10 (was per ongeluk 8 na Gijs-koop)
  - 🛒 **Gijs verkoop afgewikkeld** (2 ROAR @ €10.40 = €20.80):
    - 2 tokens uit treasury → Gijs balance
    - 21% BTW (€4.37) → Spark's kasboek + EUR-wallet
    - Audit-trail + deposit-log compleet
  - 🪙 **Maak-Token feature** — `POST /api/spark/mint/from-wallet`:
    - Spark gebruikt eigen EUR-wallet om token uit treasury naar eigen balance te minten
    - 51%-governance-guard: treasury mag nooit onder 510k
    - Boekhouder DM bij elke mint
    - Frontend: groene "🪙 Maak Token" knop in Spark's Wallet (alleen admin + walletView=spark)
    - E2E getest: weigert correct bij onvoldoende wallet (€4.37 < €5.67)
  - 🆕 **KB v2 "+ Nieuwe kaart" knop**: groene Plus-knop in header (was bug: "kan geen kaart maken zoals v1"). Endpoint URL gecorrigeerd `/api/kb_v2/` → `/api/kb/v2/`
  - 📜 **MONEY_MODEL.md** vastgelegd in `/app/memory/`:
    - Hardcap 1M, Spark ≥51% governance, papertrail-aanpak
    - 3 buckets uitleg (total_supply / treasury_pool / balances)
    - Prijs-model + BTW-afroming → spark_kasboek
    - Maak-Token flow specificatie
    - Roadkill Merch loop (P2)
    - 6 voorwaarden-clausules voor T&C/privacy

- 2026-05-23 **v5_ijkpunt_v5_2_001 + v5_display_fix_001** (sessie 9 — slot):
  - 🪙 **IJkpunt v5.2 voor redeploy** — €1.20 bijgestort op €101.60 baseline = **€102.80 totaal**, verdeeld over **20 gelijke potjes** (€5.14/pot):
    - Spark (user-000): 10 potjes · BCH-EUR · 1u cycle · **auto-trade AAN**
    - De Willem (user-001): 10 potjes · BCH-EUR · 15m cycle · **auto-trade UIT**
    - ROAR balance: 10/10 ongewijzigd
    - Spark kasboek: €0 (begint te groeien bij elke buy via 21% BTW-afroming)
    - Script: `scripts/ijkpunt_v5_2_redeploy.py` (idempotent, audit-log entry)
  - 🛠️ **Naam-mapping BUG GEFIXED**: `admin/bots` toonde user-000 als "De Willem" en user-001 als "Spark" door een eerdere "display swap". Veroorzaakte Willem's verwarring. Nu correct: **user-000 = Spark, user-001 = De Willem** (data was altijd correct, alleen display gebroken).

- 2026-05-23 **v5_btw_afroming_001 + v5_spark_kasboek_001 + v6_capabilities_admin_001** (sessie 9 — vervolg 3):
  - 💰 **21% BTW afgeroomd op token-aankopen** → Spark's kasboek (geen bank, dit IS Spark's inkomstenstroom):
    - Hook in `shop/routes.py::buy_tokens` na save_roar
    - BTW (21%) op `amount_eur` → Spark EUR-wallet (zowel `wallets.json` als `user_wallets.json` mirror)
    - Audit-trail in nieuwe `/data/system/spark_kasboek.json` met `entries[]` + `totals{btw_in, winst_in, uit}`
    - Transactie krijgt `btw_afgeroomd_eur` veld terug zodat UI dit kan tonen
    - Spark koopt zichzelf nooit BTW af (skip als user_id==user-000)
  - 🏦 **Nieuwe module `modules/spark_kasboek/`**: `GET /api/spark/kasboek/saldo` (totaal + breakdown) + `GET /api/spark/kasboek/entries`
  - 🤖 **Nieuwe capability** `spark_saldo_check` (12e capability totaal, 5e executable):
    - Triggers: "wat is spark saldo", "wat is jouw kasboek", "hoeveel heeft spark", "spark balans"
    - Handler in `capability_handler_service` toont kasboek-saldo + breakdown via chat
    - ✅ E2E getest: Willem 1 ROAR @ €5.08 → BTW €1.07 → Spark kasboek €1.07 → chat "wat is spark saldo" rendert correct
  - 🧪 **Capabilities Test Page** als 7e tab in Beheer → Analytics → **CAPABILITIES**:
    - Stat-pills bovenaan: 12 totaal · 5 executable · 4 live-zonder-handler · 3 placeholder · 0 idea
    - Test-input om elke capability live te triggeren met sample-zin
    - Per-capability cards met status-kleur (groen=executable, amber=live geen handler, blauw=placeholder)
    - 1-click "vul test-veld" knop met sample-trigger uit de capability
    - Backend: `GET /api/admin/capabilities` + `POST /api/admin/capabilities/test`
  - 📋 **@traced/log_event op capability-router** — elke match wordt gelogd in `capabilities` module met confidence/trigger/has_handler → zichtbaar in Analytics → LOGS
  - 🧹 **Post-test cleanup** — test-koop (Willem 11 tokens / €94.92) teruggedraaid naar ijkpunt v5.1 (10/10 tokens, €0, kasboek leeg) zodat redeploy schone start heeft

- 2026-05-23 **v5_logs_hyperlink_001 + v6_intent_router_001** (sessie 9 — vervolg 2):
  - 🔗 **Logs als hyperlink in Bestanden-tab**: `LogsHyperlinkSection` toont amber banner met klikbare per-dag/per-module links naar `GET /api/admin/logs/download?date=&module=` (nieuwe FileResponse endpoint, returns .jsonl). Vol-detail browser blijft in Analytics → LOGS. Geen duplicate UI, alleen referentie-snelkoppelingen.
  - 🤖 **Spark's hands intent-router** (P0 done): `capability_handler_service.py` met 4 echte handlers:
    - `tellen_gebruikers` — leest `users.json`, telt mensen vs bots, toont namen
    - `tellen_bestanden` — leest `_index.json`, toont totaal + MB + per-categorie verdeling
    - `taken_lijst` — toont open backlog (P0/P1/P2 uit ROADMAP)
    - `winst_verlies_overzicht` — scant audit_log voor SELL-events, totaal netto
    - Onbekende caps krijgen nette placeholder-response
    - Confidence-threshold ≥ 0.3 om false positives te voorkomen
    - Hook in `chat/routes.py` na time-intent, vóór relation-extraction
    - ✅ E2E: "hoeveel gebruikers" → 11 mensen + 5 bots; "hoeveel bestanden" → 1 foto / 0.0 MB; "heb ik winst gemaakt" → 0 trades; "log van trade" → placeholder fallback

- 2026-05-23 **v5_logs_to_analytics_001 + v5_closing_flow_001** (sessie 9 — vervolg):
  - 📊 **Logs Browser verhuisd** naar Beheer → Analytics → **LOGS** (6e tab naast SYSTEEM/DATA/NETWORK/LAYER/TRADE)
    - Logs hoorden niet bij media-archief (Foto/Geluiden/Filmpjes/Dialogen) maar bij observability
    - `LogsBrowser` component blijft hergebruikt; Beheer → Instellingen → Archief verlost van Logs-categorie
    - Verified in screenshot: 13 records "f1_login_bark", phase-filter (alle/pre/post/error/event), tree-nav 2026/05/23 → barks/bots/cards/chat/kbv2/system/welcome
  - 📒 **Boekhouder closing-flow** ("terlens-terug-boek") — `modules/boekhouder/service.py::close_cycle()`:
    - Rollupt audit-events sinds vorige closing per user (buys/sells/fees/mints)
    - Stuurt 1 samenvatting-DM naar admin (Spark-trades) of user (eigen trades)
    - Persistent in `/data/system/boekhouder_closings.json` + `audit_log` type=cycle_close
    - Idempotent venster: 2e close direct na 1e → since=vorige_ts → 0 nieuwe trades
    - Endpoints: `POST /api/boekhouder/close-cycle/{user_id}` (admin-guarded gradatie ≤ 2) + `GET /api/boekhouder/closings`
    - ✅ E2E getest: Spark (0 buys), Willem (10 buys €50.80), 2e close (0 sinds vorige), 403 voor non-admin (Marieke)

- 2026-05-23 **v5_ijkpunt_001 + v5_help_refresh_001 + v5_tts_pad_001 + v5_kbv2_graph_001** (sessie 9 — 4 verzoeken + ijkpunt):
  - 🕸️ **Verbanden tab toont nu KB v2** (`/api/graph/rebuild`):
    - `sync_service.rebuild_graph_full` scant nu v1 (5288) + v2 lades (250+329+1071+632) + inbox (3007) = **10577 nodes / 65981 edges**
    - v2-nodes krijgen `type=knowledge_v2`, `lade`, `lade_color` (🌸 voelen pink, 💬 spreken cyan, 🧠 weten amber, 🎭 doen purple)
    - Edges via shared tags mengen v1 + v2 nodes (per-node cap 20)
    - Verbanden header toont nu "10577 NODES | 65981 EDGES | 12.5 gem. verbindingen"
  - 🆘 **Help-commando refresh** (`smart_intents_service.handle_help`):
    - 11 nieuwe user-items toegevoegd: KB v2 audit/inbox/leren, Card Factory (D&D/Event/Bark), ROAR Gift, Spark World D&D, Community recap, Trader/Wallet
    - 8 nieuwe admin-items: Logs browser, Deploy-anker, Trader hot-swap, Force-sell, Bot-kleurschema's, App-kleurenschema, Boekhouding entiteiten, Graph rebuild
  - 🎙️ **TTS-vriendelijke korte antwoorden** (`chat/tts_friendly_service.py`):
    - Nieuwe `maybe_pad_for_tts(response)` muteert in-place
    - Heuristiek: alleen padden als bericht < 40 chars, geen vraagteken aan eind, geen markdown, type niet in skip-set (wedervraag/help/dnd_help/agenda_proposal/identity/etc.)
    - 7 conversational tails varieerden ("Vraag gerust door…", "Ik blijf in de buurt", "Klaar voor je volgende vraag")
    - Hook in `_save_log` zodat ÉLKE early-return response (greeting/goodbye/etc.) wordt gepad
    - Geverifieerd: "doei" → "Tot ziens Willem! Vertel het me als ik iets moet aanvullen." (`tts_padded=true`)
  - 🧠 **ROADMAP.md heeft nu een Spark's-brein-sectie** (top):
    - 5-laags AI-pipeline expliciet beschreven (safe-word → identity/action → smart_intents → snap → fallback)
    - 14+ specialized services in chat-module benoemd
    - Observability/shadow-leren, Kennis-architectuur, D&D-laag, Stem-laag, Bots-acteurs
    - Conclusie: backlog is *aanvulling* op bestaand brein, geen vervanging
  - 🧹 **IJKPUNT v5.1 — schone start** (`scripts/ijkpunt_v5_1.py`):
    - Backup naar `/data/_backups/ijkpunt_v5_1_<ts>/` vóór elke wijziging
    - **Token/wallet synchronisatie**: roar_balances.json gefilterd → {user-000: 10, user-001: 10}, wallets.json + user_wallets.json tokens/EUR gesynchroniseerd
    - **5 schaduw-traders potjes verwijderd**: Nick T (574ac78e), Gijs (a0ee2d7e), Nick (4d81e2a4), ghost users (1b492f19, bc76725e)
    - **18 test-chat-logs verwijderd**: test-*, t.json, agenda-test-*, user-testedge, ca4d31b1, 78f2b0d7
    - **Community spam opgeruimd**: 358 → 351 messages (test-content filter)
    - **Gift requests**: bewaard pending + accepted-binnen-30d
    - **Snapshot opgeslagen**: `/data/system/ijkpunt_v5_1.json` met anchor (Bitvavo deposit €96.52 → 20 tokens @ €5.08)
    - ✅ Verified: ROAR price endpoint klopt (€5.08, 10 + 10 tokens), Wallet Willem (10 tokens, €0 EUR), Wallet Spark (10 tokens, €0 EUR), 10 potjes elk @ €5.08

- 2026-05-23 **v5_bot_color_scheme_001 + v5_card_factory_001** (sessie 8):
  - 🎨 **Bot-kleurschema's gekoppeld aan Beheer → Kleurbeheer**:
    - 5 nieuwe system-settings: `bot_color_madelief/harry/smith/boekhouder/dood`
    - Nieuw "BOT-ACCENT KLEUREN" paneel onder Beeld-tab met color-pickers + hex-input
    - Hardcoded `BOT_COLORS` in GesprekkenPage is nu runtime cache; vult uit `/api/settings/system` bij mount
    - Hex → rgba opacity-conversie voor bg(10%) + border(20%) + accent(100%)
  - 🃏 **Card Factory** (`modules/cards/` — generieke game-style kaarten):
    - 3 types: `dnd` / `event` / `bark` met type-specifieke extra-velden
    - Schema: `id, type, titel, vraag, antwoord, media{image_url, audio_url}, tags, status, footnote`
    - Endpoints: `POST/GET/PATCH/DELETE /api/cards/{type}/{card_id}` + `/media` upload
    - Media via system_archive met tag `card_<type>` + `linked_card_id` (centrale store)
    - Cascade-delete: bij verwijderen kaart → gekoppelde media in system_archive auto-opruimen
    - **Hook-chain bij draft→active overgang** (zodra vraag OF antwoord ingevuld):
      • `dnd` → `dnd_lore_registered` (toekomstig: lore_index update)
      • `event` → De Boekhouder maakt automatisch community-bark "📅 Nieuw event: ..."
      • `bark` → `bark_template_registered` (toekomstig: trigger-registry update)
  - 💬 **3 chat-commands toegevoegd** in `kb_v2/hooks.py`:
    - "maak een d&d kaart [titel]" → draft DnD-kaart
    - "maak een event kaart [titel]" → draft Event-kaart
    - "maak een bark kaart [titel]" → draft Bark-template
  - 🎚️ **Depth-router voorbereid** in `cmd_tell_layer` (depth-veld in registry, 4 niveaus: kort/meer/diep/volledig) — handlers nog te koppelen aan laag1-4 lookup
  - ✅ E2E getest: 3 card-types aanmaken werkt, hook-chain fired correct (Roadkill Borrel event → community-bark "📅 Nieuw event: Roadkill Borrel. Vrijdag 20:00 in het centrum"), bot-color panel rendert in UI met alle 5 bots

- 2026-05-23 **v5_welcome_001 — Spark persoonlijke welkom bij eerste login** (sessie 7):
  - 🌱 **`modules/bots/spark_welcome_service.py`** — idempotent welkom-service
    - Drie gestapelde Spark-berichten in user's Spark-prive chat (geen muur tekst)
    - Inhoud uit MISSION.md: wie Spark is, wat hij wél doet, wat hij **NOOIT** doet (privacy-statement), 3 begin-tips
    - `WELCOME_VERSION = "v1"` — bumpen stuurt iedereen een nieuwe ronde
    - Persistente referentie in chat-history (in tegenstelling tot eenmalige modal-tour die al bestond)
    - User-veld `welcome_version_seen` + `welcome_sent_at` in `users.json`
  - 🔌 Hook in `auth/routes.login` naast Mr Smith bark (sessie 2)
  - ✅ E2E getest met Marieke: 3 berichten aangemaakt na 1e login, 2e login → géén duplicate (idempotent OK)
  - 🪞 Combineert mooi met bestaande modal-tour: modal is generiek "zo praat je met Spark", deze nieuwe is persoonlijk Spark→user privacy-belofte

- 2026-05-23 **v5_kbv2_media_002 + v5_dashboard_kbv2_001** (sessie 6):
  - 📦 **Kennis-kaart media → System Archive refactor**:
    - Voice (Whisper STT) + Image uploads gaan nu door `/api/system-archive` heen i.p.v. eigen `/data/knowledge/v2/media/`-folder
    - Tagging: elk media-item krijgt `tags=['kbv2', 'kbv2_card_<id>']` + `linked_card_id` veld + `source='kbv2_media_upload'`
    - URL nu `/api/system-archive/file/<archive_id>` (centrale download endpoint)
    - **Geen duplicate storage** — 1 tabel, 1 zoekindex
    - Whisper transcript wordt ook opgeslagen in archive-entry's `scan_results.transcript` + `description`
  - 🎨 **Bron sub-tabs in Beheer → Instellingen → Archief**:
    - **Alles** / **🧠 Kennis-kaart** / **📎 Los** filter-knoppen onder Foto/Geluiden/Filmpjes tabs
    - 🧠-badge op file-rij toont gelinkte kaart-id (hover tooltip)
  - 📊 **Dashboard KB Lades-widget** (admin gradatie ≤ 2):
    - Nieuwe card "KB Lades (v2)" naast bestaande Kennisbank-overzicht
    - 4-vakken-grid: 🌸 Voelen 250 · 💬 Spreken 329 · 🧠 Weten 1071 · 🎭 Doen 632
    - Amber call-to-action banner "3007 kaarten wachten op indeling" → klik = naar Kennisbank
    - Click-through naar `/knowledge`
  - ✅ E2E getest: image upload landt in system_archive/foto/ met juiste tags + linked_card_id, sub-tab filter werkt, dashboard widget rendert correct met live stats, geen page errors

- 2026-05-23 **v5_kbv2_hooks_001 — Hooks-laag + Voice-tab cleanup + Reflectie** (sessie 5):
  - 🔗 **`modules/kb_v2/hooks.py` placeholder-laag** voor toekomstige aansluitingen:
    - Hook 1: KB → Vocab register (TODO)
    - Hook 2: Chat-commands router — **3 commando's al live**:
      • "audit kennis" / "wat mist" → self-audit samenvatting
      • "hoeveel onbeantwoord" / "wat staat in inbox" → inbox-stats
      • "leer woord: X" / "voeg toe aan kennis: X" → add_to_inbox
    - Hook 3: Auto-graph verbanden via shared tags (TODO)
    - Hook 4: D&D card linking (TODO)
    - Hook 5: Dialogen voice-snippet auto-save (TODO)
    - Pattern: nieuwe `hooks.py` per module met TODO-blocks in plaats van losse comments
  - 🔇 **Voice-tab uit workspace verwijderd** — inspraak zit nu in elke Kennisbank-kaart, oude page route bestaat nog (legacy URL) maar geen sidebar-entry meer
  - 🪞 **`MISSION.md` cross-link** vanuit ROADMAP.md
  - 📋 **ROADMAP.md flink uitgebreid**: P0 (Spark's hands + boekhouder-closing), P1 (5 KB v2 hooks + ConversationStateManager + AuditService weak-trigger), P2 (8 backlog items), P3 (5 experimenteel). 7 architectuur-principes vastgelegd. Hook-files-tabel toegevoegd.
  - ✅ End-to-end getest: 3 chat-commands fire (audit/inbox/learn), sidebar gecleaned, geen page errors

- 2026-05-23 **v5_kbv2_media_001 — Hybride Kennisbank + Voice/Image** (sessie 4):
  - 🔀 **Sidebar gemerged**: "Kennisbank" en "Kennisbank v2" → één entry "Kennisbank" die rechtstreeks naar v2 route `/knowledge` gaat (oude KennisbankPage.js blijft als legacy bestand, route bestaat nog op `/knowledge-legacy` voor terugval)
  - 📋 **Card-schema uitgebreid** (idempotent upgrade-script `upgrade_kbv2_schema.py`):
    - `media: {voice_url, voice_transcript, image_urls[]}`
    - `needs: ["laag1"|"ws5"|"voice"|"image"]` — checklist wat nog ontbreekt, auto-herrekend bij elke edit
    - Alle 5288 kaarten kregen het nieuwe schema
  - 🎙️ **Voice opname + Whisper STT** (`modules/kb_v2/media_routes.py`):
    - `POST /api/kb/v2/media/voice` — MediaRecorder (webm) → OpenAI Whisper via Emergent LLM Key → Nederlandse transcriptie
    - Auto-fill: als kaart nog geen laag1 heeft + transcript bestaat → laag1 = transcript (in inbox-flow)
    - Audio bestand bewaard in `/data/knowledge/v2/media/voice/`
    - Idempotent: max 24MB, 7 audio-formaten ondersteund
  - 🖼️ **Image upload**:
    - `POST /api/kb/v2/media/image` — multipart upload tot 8MB
    - Foto's bewaard in `/data/knowledge/v2/media/image/`, gelinkt aan kaart via `image_urls[]`
    - UI toont thumbs (16x16) onder voice-sectie
  - 🎨 **UI MediaSection** (in CardDetail):
    - Rode "Spreek in" knop met live-recording state ("Stop & verstuur")
    - Audio-player toont opname terug + transcript-quote daaronder
    - Groene "Foto toevoegen" knop met thumbs-grid
    - **Needs-checklist** amber-banner toont wat kaart nog mist (📝 laag1 / 5️⃣ 5W / 🎙️ inspraak / 🖼️ foto)
  - 📜 **Core docs** (`/app/memory/MISSION.md`):
    - Missie/Visie uit Spark Core 4.1 herbelichaamd in v2
    - Drie-lagen-identity-scheiding (auth/display/system) als WET vastgelegd
    - Privacy-stack (alleen lokale JSON, geen tracking) expliciet
    - Piramide-architectuur DNA/Skelet/Geheugen/Logs gedocumenteerd
    - ROADMAP.md verwijst nu naar MISSION.md (top-cross-link)
  - ✅ End-to-end getest: image upload werkt (287B test-PNG → kaart "aanschouwelijkheid" → `image_urls[0]` gevuld, `needs` auto-update van `['voice','image']` → `['voice']`)

- 2026-05-23 **v5_kbv2_001 — Kennisbank v2 (4 Lades + Inbox + Graceful Fallback)** (sessie 3):
  - 🗂️ **Migratie-script** (`backend/scripts/migrate_kb_v2.py`, idempotent, dry-run + commit modes)
    - v1 `knowledge_base.json` (5288 kaarten) → **4 lades** op basis van dominant-tag classifier
    - Backup gegarandeerd: `knowledge_base.json.v1_backup_20260523_120215` (v1 ongewijzigd)
    - Verdeling: 🌸 **Voelen** 248 / 💬 **Spreken** 329 / 🧠 **Weten** 1071 / 🎭 **Doen** 632 / 📥 **Inbox** 3008
    - Inbox-redenen: 633 tag-tie, 160 no-match, 2215 missing-laag1 (jouw onbeantwoord-queue)
  - 🛠️ **KB v2 service + routes** (`modules/kb_v2/`):
    - `GET /api/kb/v2/stats`, `lade/{id}`, `inbox`, `find`, `fallback`, `audit`
    - `POST /api/kb/v2/classify` (inbox → lade), `edit`, `inbox/add`
    - Alle write-ops `@traced` decoreerd (volgens logger-verplichting)
    - Per-kaart footnote-metadata: bron, ingedeeld_door/op, vorige_versie_v1, vertrouwen, belangrijkheid
  - 🎨 **UI `KennisbankV2Page.js`** met 5 sub-tabs (Inbox · Voelen · Spreken · Weten · Doen):
    - Inbox toont reden-badge (Tag-tie/Geen match/Geen laag1) + filter-knoppen
    - Kaart-detail: alle 4 lagen + 5W collapse + tags + footnote + 4 indeel-knoppen
    - Edit-mode voor lagen/ws5/tags/begrip met save-flow
    - **Self-audit modal** — scan op lege laag1, lage vertrouwen, ontbrekende tags
    - Sidebar nav-item "Kennisbank v2" met "nieuw" badge
  - 🎭 **#DeWillem Graceful Fallback** (uit v1-filosofie!) terug in `chat/smart_intents_service.handle_topic_overview` + `chat/routes`:
    - Direct hit → "**X** _(lade: Y)_: laag1-tekst"
    - Buur-hit (tag-overlap) → "Ik ken X nog niet specifiek, maar in mijn Y-lade vind ik wel iets over Z. Wil je dat ik X apart leer?"
    - **Spark zegt nooit meer alleen "weet ik niet"** — hij stapt terug en geeft context
  - ✅ Verified e2e: classify-flow ("Aanbidden" inbox→voelen, stats 248→250, inbox 3008→3006), fallback fire (test "vertel over emotie blij vreugde" → Spark verwijst naar **Blij** in lade voelen)

- 2026-05-23 **v5_spark_logger_001 + v5_barks_001 + v5_shadow_cleanup_001** (zelfde sessie, na bugbatch):
  - 🔭 **Observability fundament** (`modules/core/spark_logger.py`):
    - `@traced(intent="...")` decorator: pre + post + error logs met `duration_ms` en result-summary
    - JSON-Lines per module: `/data/system/logs/YYYY/MM/DD/{module}.jsonl`
    - 28-dagen retentie (auto-purge bij startup)
    - `log_event()` helper voor handmatige events buiten functie-grenzen
    - Toegepast op kritieke routes: `bots.send_community_message`, `chat.process_message`
    - **Verplichting voor nieuwe modules** vastgelegd in `/app/memory/ROADMAP.md`
  - 🪟 **Admin Logs Browser** (`Beheer → Instellingen → Archief → Logs` tab):
    - Boom-navigatie YYYY/MM/DD → modules
    - Records-pane met phase-filter (alle/pre/post/error/event)
    - Endpoints: `GET /api/admin/logs/index`, `GET /api/admin/logs/read`, `POST /api/admin/logs/purge`
  - 🤖 **F1 — Mr Smith login counter bark**: telt logins per user; bij 3/4/5 → bark in community ("Ik zie je wel, X. 👀"), bij 6 → reset naar 0. Counter in `/data/system/login_counters.json`. Hook in `auth/routes.login`
  - ⏰ **F2 — Harry mirror-time bark**: lazy check bij `GET /community/messages` — als HUIDIGE tijd HH:MM is met H==M (11:11, 12:12 ... 23:23), post Harry "⏰ HH:MM — een spiegel-minuut. Even stilstaan?" (max 1x per minuut per dag, via `bark_kind_id` dedup)
  - 🌸 **F3 — Madelief bug-pointer**: als user-bericht "bug/fout/werkt niet/kapot/crash/stuk" bevat, voegt Madelief een bark toe met instructie naar Notities & Taken → Bug-melder (geen duplicate als Madelief al via triggers reageerde)
  - 🧹 **Schaduwtrader cleanup**: Gijs (user-a0ee2d7e) en Nick (user-4d81e2a4) bots gestopt + uit registry verwijderd. `milestone_first_roar_token` achievement teruggedraaid (incl. -50 XP elk). `admin/bots` endpoint heeft nu token-gate: lazy-slot users zonder tokens + zonder proactieve registratie verschijnen niet meer in Analytics
  - 🩹 **Defensive guards in GesprekkenPage**: `sparkMessages.filter(Boolean).map`, `priveMessages.filter(Boolean).map` — voorkomt zelfde-soort crashes als B3 bij toekomstige response-format changes

- 2026-05-23 **v5_bugbatch_001: B1+B2+B3+B4 in 1 sessie** (later vandaag):
  - 🩹 **B3 fix — Community whitescreen op "help"**: bug zat NIET in `CommunityPage.js` zoals handoff suggereerde, maar in `GesprekkenPage.js` Community-tab. `setCommunityMessages(prev => [...prev, res.message, ...res.bot_responses])` las het OUDE response-formaat. Backend retourneert nu `{messages: [...]}` voor help/safeword/dnd → `res.message` was `undefined` → crash op `.map(msg => msg.user_id)`. Fix: `v5_gesprekken_compat_001` ondersteunt beide formats + optimistic user-echo + `.filter(Boolean)` defensive guard
  - 🤖 **B1 fix — Spark auto_trade persistence**: handoff hot-swapte `m._auto_trade=True` via Python maar dat persisteerde NIET. Bij elke backend-restart resumde Spark met `auto_trade=false` uit registry JSON → geen buys. Fix: nieuwe `MonitorService.update_auto_trade()` + `POST /api/trade/bot/auto-trade/{user_id}` endpoint die `_persist_registry()` triggert. Spark staat nu permanent op auto_trade=true
  - 📈 **B4 fix — Potje value mark-to-market**: `get_potjes()` toonde altijd `live_value = capital` (statisch) wanneer geen echte Bitvavo balance beschikbaar was (mock mode). Nu: voor open posities wordt huidige market-price opgehaald via `fetch_tickers`, en `live_value = capital + (capital * profit_pct - fees)`. Velden toegevoegd: `unrealized_pnl`, `unrealized_pnl_pct`, `current_price`
  - 🐢 **B2 fix — Trader sequentieel laden**: `TraderPage.js` vuurde 10+ parallelle fetches af bij mount → UI freeze. Fix: `v5_sequential_load_001` chain: loadCoreData → loadLiveData → loadMonitorStatus → loadBalance → loadPotjes → loadContext. Pollers (30s tickers, 10s monitor) blijven onafhankelijk
  - ✅ Smoke test: Spark draait nu met Auto-trade AAN, 5 markets monitored, geen console errors, help-command werkt in Gesprekken

- 2026-05-23 **v5_candle_hotswap_001 + v5_spark_stoppable_001 + admin-bot-controls + DSP-004/005/006**:
  - 🕯️ **Cycle hot-swap**: `POST /api/trade/monitor/candle/{user_id}` + `MonitorService.update_candle_interval()`. Wisselen 15m/1h/4h/1d zonder restart, persistent. TraderPage cycle-buttons doen nu hot-patch bij running, lokaal anders. Auto-sync UI ↔ backend
  - 🛑 **Spark stop weer toegestaan**: `SPARK_UNSTOPPABLE` guard verwijderd in `/bot/stop/` en `/bot/pause/{user_id}`. Bugs van v4 zijn opgelost. Frontend toont Stop-knop ook voor Spark
  - 🎛️ **Admin bot-controls** in `Beheer → Analytics → Trade-tab`: ▶ Start / ⏸ Pauzeer-Hervat / ⏹ Stop knoppen per bot
  - 📐 **ARCHITECTURE.md uitgebreid** met 3 nieuwe DSPs:
    - **DSP-004**: roar_balances.json ↔ user_wallets.json (autoritatief vs mirror)
    - **DSP-005**: TraderPage React-state ↔ bot_registry_state.json (UI snapshot sync)
    - **DSP-006**: gift_requests.json ↔ roar_balances.transactions (lifecycle vs audit)
  - 🔗 `_arch_ref` comments toegevoegd in alle 4 betrokken JSON files

- 2026-05-23 **v5_roar_gift_001 + v5_per_user_trade_dm_001 + auto-trade testbed** (eerder vandaag):
  - 🎁 **ROAR Gift-flow met paper-trail**: nieuwe `/api/shop/gift` endpoints (POST create / GET inbox / GET outbox / POST accept / POST reject / POST cancel)
    - Tokens worden NIET direct overgeboekt — escrow in `pending` status. Pas bij accept transfer + audit
    - **24h auto-expire** (lazy-check bij elke list-call): pending → expired, sender's tokens behouden
    - **Frontend modal** in Winkel → ROAR Token tab (knop "🎁 ROAR Gift sturen" boven Kopen). Velden: ontvanger (dropdown alle users), aantal (max=sender balance), notitie
    - **Inbox-banner** bovenaan ROAR Token tab toont inkomende pending gifts met Accepteer/Weiger knoppen
    - Paper-trail in `roar.transactions` + `admin_log` + per-user `notifications.json` (sender + recipient krijgen beiden bevestiging-bark)
    - **First-token achievement + monitor-uitleg-bark** wordt automatisch getriggerd bij eerste-ontvangst (was eerst alleen bij token-buy)
    - **Privacy-noot**: `gift_requests.json` bevat sender/recipient pairs — privacy-implicatie genoteerd in roadmap voor encryption-at-rest
  - 📣 **Trader notifications PER-USER**: `_send_dm` in `boekhouder/service.py` stuurt nu bij user-trades naar de user zelf ipv altijd naar Willem. Spark-trades blijven naar admin (Willem) gaan
  - 🤖 **Spark monitor auto_trade aan + mock**: hot-swap via Python (`m._auto_trade=True, m._use_mock=True, m._use_potjes=True`) + 5 markets (BCH/BTC/ETH/SOL/ADA). Klaar voor systeem-test
  - 🥧 **Gijs + Nick beide 10 potjes** auto-aangemaakt (€5,08 startkapitaal elk = €50,80/user). Mock mode, BCH-EUR @ 1h candles
  - Token-eindstand: **Willem 12, Gijs 2, Nick 1** (+1 pending van Willem), Spark treasury 5
  - 🗺️ Roadmap fase `phase-roar-economy-v2` gemarkeerd ACTIVE met done/planned items inclusief outbox-view, admin-overzicht, SEPA-mint

- 2026-05-23 **v5_leaderboard_avatars_001 + v5_milestone_unlocks_001 + ROAR-gift Nick + monitors live** (eerder vandaag):
  - 🥇 **Leaderboard top 3 podium + lijst**: letters vervangen door echte `UserAvatar` component met gallery-image / user-upload / roadkill-fallback. Geen "naam[0]" meer
  - 🏆 **3 nieuwe achievements** (categorie "milestones", elk 50 XP):
    - `milestone_avatar_chose` — avatar gekozen uit galerij (trigger: `/avatar/select`)
    - `milestone_avatar_uploaded` — eigen avatar geüpload (trigger: `/avatar/user/{id}` upload)
    - `milestone_first_roar_token` — eerste ROAR token op wallet (trigger: koop bij prev_balance=0)
  - 🪝 **Cross-module hook** `unlock_milestone(user_id, achievement_id)` in `achievements/service.py` — herbruikbaar voor toekomstige mijlpalen
  - 📢 **Notification-bark** bij eerste ROAR token met uitleg over Trader monitor (in `data/notifications/notifications.json`, per-user)
  - 🪙 **Nick** kreeg 1 ROAR welkomstgift. Beide nieuwe users (Gijs + Nick) hebben monitor draaiend: **BCH-EUR @ 1h candles, auto_trade=false**
  - 🎯 Retroactieve unlock voor bestaande users: Willem kreeg "avatar chose" (had al avatar), Gijs+Nick kregen "first ROAR token" + notification

- 2026-05-23 **v5_foto_subtabs_001 + ROAR gift naar Nick** (eerder vandaag):
  - 🪙 **Nick** (`user-574ac78e`) ontving 1 ROAR welkomstgift van Willem. Eindstand: Willem 13, Gijs 1, Nick 1, Spark treasury 5. Audit-trail in `roar_balances.transactions` + `admin_log`, `user_wallets.json` gesynchroniseerd
  - 📦 **Avatar Galerij verplaatst** van losse kaart bovenaan Archief → naar `Foto` sub-tab binnen `SystemArchive`. Logica: SystemArchive heeft tabs Bestanden/Foto/Geluiden/Filmpjes/Dialogen — avatars ZIJN foto's, dus horen onder Foto
  - 🗂️ **Sub-tabs binnen Foto**:
    - "Algemene foto's" (bestaande system-archive foto-uploads)
    - "Avatar Galerij" (de gallery zelf, met daarbinnen weer Gebruikers-avatars / Systeem-avatars)
  - 🔍 Search-bar + tag-filter + content-grid worden verborgen wanneer Avatar Galerij actief is (geen UI-conflicten)

- 2026-05-23 **v5_admin_color_scheme_001 + avatar-galerij verplaatst naar Archief**:
  - 🎨 **Nieuwe sectie "App Kleurenschema (admin)"** in `Beheer → Instellingen → Beeld` — overkoepelend voor de hele app, alleen gradatie ≤ 1 kan wijzigen
    - 6 presets: Amber Default, Forest Calm, Cobalt Night, Rose Dusk, Violet Quiet, Crimson Alert (klik = direct opslaan + apply)
    - 3 custom color pickers: Primary accent / Secondary accent / Background tint (hex input + native color picker, on-blur save)
    - Live voorbeeld pill-rij met huidige kleuren in context
    - Persisted in `settings/system.json` via 3 nieuwe system-scope keys: `app_primary_accent`, `app_secondary_accent`, `app_background_tint`
  - 🌐 **Globale CSS-variables**: `--app-primary`, `--app-secondary`, `--app-bg-tint` op `:root` (defaults + auto-load uit `/api/settings/system` bij login)
  - 📦 **Avatar Galerij verplaatst** van Beeld → Archief (logischer: assets-management hoort bij archief, kleuren bij beeld)
  - ✅ Backend e2e getest (PUT `/api/settings/system/app_primary_accent` → 200, persisted), frontend smoke screenshot bevestigt beide tabs renderen correct

- 2026-05-23 **v5_avatar_gallery_split_001** (Avatar Galerij beheer herstructurering):
  - 🎨 **2 sub-tabs in Beheer → Instellingen → Beeld → Avatar Galerij**:
    - **Gebruikers-avatars** (33): vrij te kiezen door iedereen, rode Verwijder-knop per avatar
    - **Systeem-avatars** (5): Spark/Harry/Smith/Madelief/Spark 2 — locked-icoon + "Beschermd" knop (uitgeschakeld). Eerst lock weghalen via Beheer → Gebruikers → Avatar Beheer pencil voor je echt kunt verwijderen
  - 🗑️ **Modal-confirmatie i.p.v. silent toast**: rood "Avatar verwijderen?" modal met avatar-titel, waarschuwing dat gekoppelde users initialen krijgen, "Annuleer" + "Ja, verwijder permanent" knoppen. Vervangt browser-native `confirm()` voor duidelijker UX
  - ✅ Bevestigingstoast `"<naam> verwijderd uit galerij"` met groene bevel + auto-dismiss na 3.5s
  - 🛡️ Backend `DELETE /api/avatar/gallery/{id}?viewer_id=...` werkt al — bug-report bleek visuele feedback-issue, niet functional

- 2026-05-23 **v5_self_password_001 + ROAR admin-batch**:
  - 🔑 **Self-service sleutelwoord wijzigen**: nieuwe `Account` sectie bovenaan Mijn Profiel → Instellingen. User vult huidig + nieuw sleutelwoord in (toon/verberg toggles per veld), klikt "Wijzig sleutelwoord" of "Reset naar Welkom01" (bevestigingsmodal). Backend: `POST /api/auth/users/{user_id}/change-password` body `{current_sleutelwoord, new_sleutelwoord}` met validatie (huidige check, min 4 tekens, niet gelijk aan huidige). Werkt voor reset → nieuwe = "Welkom01"
  - 🪙 **Admin ROAR batch (Willem +5 @ €10.10 override + 1 gift → Gijs)**:
    - Nieuwe user **Gijs** aangemaakt (`user-a0ee2d7e`, gradatie 3, sleutelwoord Welkom01)
    - Willem wallet topup +€50,50 (admin SEPA), 5 tokens gekocht @ €10,10 (override pre-storting prijs)
    - 1 token gegift Willem → Gijs (welkomstgift, audit-trail in `roar.transactions` + `admin_log`)
    - Eindstand: Willem 14 ROAR, Gijs 1 ROAR, Spark treasury 5 ROAR
    - Token-prijs herzakte van €15,16 → €10,11 (precies zoals voorspeld: 151,63 / 15 circulating)
    - `user_wallets.json` gesynchroniseerd om dual-source consistentie te bewaren
  - 🔍 **Zip-backup user-verlies bug**: niet reproduceerbaar — Gijs zit met al zijn data IN de `download/full` zip (geverifieerd). Het mtime-filter geldt alleen voor `download/changes` (by-design)

- 2026-05-23 **v5_ui_prefs_001** (Per-user Instellingen-tab in profiel):
  - 🎨 **Mijn Profiel → nieuwe tab "Instellingen"** met 3 secties:
    - **Beeld**: glow basiskleur picker — 8 preset swatches (Amber/Cyan/Violet/Emerald/Roze/Rood/Goud/Blauw) + custom color picker + hex-input. Live preview ring met `box-shadow`. Wijziging direct opgeslagen
    - **Geluid** (in ontwikkeling): TTS-toggle, Geluidseffecten-toggle, Auto-bark-toggle (gemarkeerd "binnenkort")
    - **Connecties**: Bitvavo trading verbindingsstatus (actief/inactief). Plek voor toekomstige integraties (Google Agenda, Moneybird, Telegram)
  - 🔌 **Backend**: `GET/PUT /api/profile/ui-preferences/{user_id}` met hex-validatie. Persistent in `/data/users/{user_id}/ui_preferences.json`. Schema: `{glow_base_color, glow_intensity, sound_enabled, auto_bark_enabled, tts_enabled}`
  - 🌐 **Globale CSS-variable** `--glow-base` op `:root` (default `#f59e0b`). App.js laadt de user-voorkeur bij login en zet de CSS-var. Toekomstige componenten kunnen `var(--glow-base)` consumeren voor humeur-gedreven kleurverloop
  - ✅ Backend e2e getest (GET/PUT, hex-validatie verwerpt ongeldige input). Frontend smoke screenshot: tab klikbaar, preset-klik wijzigt hex naar #06B6D4 live
  - 📜 Roadmap item gemarkeerd done (anchor `profile-settings-tab`)

- 2026-05-23 **v5_per_user_endpoints_001** (Trader stop bug fix bevestigd):
  - 🛑 **`POST /api/trade/bot/stop/{user_id}` + `bot/pause/{user_id}`** ipv legacy global endpoints. Spark (user-000) heeft `SPARK_UNSTOPPABLE` guard
  - ✅ Curl e2e getest: Willem (user-001) bot stoppen heeft GEEN effect op Spark's slot. Spark stop-poging geeft expliciete error
  - 🔄 TraderPage frontend gebruikt al `/bot/stop/${userId}` (regel 236) en `/bot/pause/${userId}` (regel 241)

- 2026-05-23 **v5_70cr_batch** (Zip-systeem + D&D Base Line intro + Help):
  - 📦 **KB-diff export** (`GET /api/backup/kb-changed-since-deploy`): klein JSON-bestand met alleen kaarten waarvan `updated_at` of `created_at` na deploy ligt. Veel kleiner dan de 11MB volledige KB → makkelijker om over te dragen tussen prod ↔ preview
  - 📥 **KB-diff import** (`POST /api/knowledge/import-diff`): merge een gedownload diff-bestand in de huidige KB (match by id of begrip; updates lagen/ws5/tags/belangrijkheid; backup van pre-import KB automatisch)
  - 🛠️ **3 download-opties in Backup UI**: Wijzigingen / KB-diff slim / Volledige backup (i.p.v. 2 kaarten)
  - 🎭 **D&D Base Line intro** in community chat (`[start verhaal]` trigger):
    - 4 berichten sequence: opening trilling → "AD in tijd, donker" → bundel licht + altaar op `x0,y0,z0` → keuze-prompt
    - 3 keuze-knoppen: 👂 Horen / 👁️ Zien / 🤐 Zwijgen (de andere 2 zintuigen komen later)
    - `/api/bots/community/dnd-choice` slaat keuze op + Spark reageert met scene + behavior_tracker logt `dnd_choice_<choice>` en `dnd_participation`
    - Purple-glow border + whitespace-pre-line voor verhaalberichten in CommunityPage
  - 🆘 **Help-knop community chat** (productie-bug): keyword `help`, `/help`, `?` of `hulp` → Spark stuurt overzicht van commands ([start verhaal], archief, trade, wallet, kennis, leer, bug) + uitleg dat gewone zinnen geen commando nodig hebben

- 2026-05-23 **v5_30_credit_followup** (Potjes spread + STT/TTS prep + roadmap):
  - 🪙 **Potjes 5×2 verdeling**: nieuwe endpoint `POST /api/trade/potjes/{user_id}/distribute` verdeelt round-robin over de gekozen markten. Bevestigd: BCH/BTC/ETH/SOL/ADA hebben elk 2 potjes na call. Open posities worden overgeslagen (skipped_open_positions: 1). Bij coin-picker wijziging tijdens running monitor wordt ook automatisch herverdeeld
  - 🎤 **STT/TTS schakelaars in Bot-instellingen**: stt_enabled, tts_enabled, tts_voice (6 OpenAI stemmen). Velden persisteren via `PATCH /api/auth/admin/bots/{bot_id}/settings`. Audio-koppeling zelf (Whisper + TTS) volgt in latere fase via integration_playbook_expert
  - 📜 **3 nieuwe roadmap items** (planned):
    - Community Plus token-tier (1+ token = community member, bot-toegang ∝ wallet)
    - Spark spaart eigen potjes uit handelswinst → kan weggeven
    - D&D-kaart als spreekkanaal — bot leest kaart-tekst uit
  - 🗒️ **Notitie over uploaded zip**: was changes-since-deploy snapshot van PRODUCTIE, geen nieuwe KB-kaarten geïmporteerd in preview (anders zou productie-data zich vermengen). Indien gewenst kan KB-merge in volgende sessie

- 2026-05-23 **v5_30_credit_batch** (Trader bug + Bot format + Roadmap):
  - 🔥 **Trader hot coin-swap** (prod bug fix): coin-picker zichtbaar én klikbaar tijdens lopende monitor. Nieuwe endpoint `POST /api/trade/monitor/markets/{user_id}` past markten live aan zonder bot te stoppen. Hint label "(live aanpasbaar)" toont state. 10 potjes spreiden zich automatisch over gekozen coins
  - 🤖 **Bot format gestandaardiseerd**: madelief, harry, smith, boekhouder krijgen allemaal `is_bot=true`, `personality`, `rol`, `channels`, `avatar_lock`. Consistent template voor alle acteurs
  - ⚰️ **De Dood toegevoegd** als 5e bot (`bot-dood`) met gallery-avatar `cdbd37cd2007`, persoonlijkheid + rol als "reflectieve acteur" (memento momenten, eindes, transities)
  - ⚙️ **Bot-instellingen tab** in `UsersAdminPage` (alleen zichtbaar als `is_bot=true`): velden voor rol, persoonlijkheid, channels, bark-template, avatar-lock. Backend endpoint `PATCH /api/auth/admin/bots/{bot_id}/settings`. Gebruikt voor bark-systeem configuratie
  - 🌦️ **Weerstation roadmap-item** toegevoegd onder phase-dnd: weer.nl koppeling → cloud/humeur per user (niet alleen voor Spark)
  - ✅ Backend e2e getest: hot-swap markets (running=true confirmed), PATCH bot-settings (persoonlijkheid + channels persist), lint clean

- 2026-05-23 **v5_lazy_slot_001 + v5_offline_persistence_001** (correctie + uitbreiding):
  - 🤖 **Lazy slots voor elke user**: `/api/trade/admin/bots` toont nu automatisch elke menselijke user uit `system/users.json` als idle bot-slot (bot-* AI personae uitgesloten). Backend bewees 9 bots zichtbaar (Spark + Willem running + Heidi, joel123, Marieke, Nick, piet, Roadkill, Ron als lazy). User-naam + gradatie meegestuurd voor admin overzicht
  - 🌙 **Checkbox heroriëntatie**: "Toon in Analytics" → **"Draaien als ik offline ben"**. Functioneel hetzelfde endpoint (`bot/register`), maar semantiek klopt nu met user intent: zichtbaarheid is automatisch, vinkje gaat over persistentie bij logout
  - 🏷️ **Analytics-kaart toont user-naam**: ipv alleen `user-001` zie je nu "De Willem" + monospace uid kleiner ernaast

- 2026-05-23 **v5_bot_proactive_register_001 + v5_admin_force_sell_001 + v5_admin_bot_cards_001** (~45 credits batch):
  - 🪙 **Proactieve bot-registratie**: nieuwe checkbox "Toon in Analytics" op TraderPage (rechts naast Monitor-knoppen). User kan zijn slot zichtbaar maken in Admin Analytics zonder de bot te starten. Persistent via `/data/trade/registered_users.json`, auto-resumed bij elke server-start
  - 🛑 **Force-sell admin endpoint**: `POST /api/trade/potjes/{user_id}/{pot_id}/force-sell` met admin-only check (gradatie ≤ 1), live Bitvavo prijs voor exit, audit-trail in `/data/trade/force_sell_audit.json`. Waarschuwt voor token-devaluatie
  - 🤖 **Analytics bot-kaarten redesign**: per-bot uitklap (klik op kaart) toont 1) potjes-tabel met capital/live/entry/trades/P&L per pot, 2) laatste 8 trades van die wallet, 3) force-sell knop per open potje met dubbele-bevestiging modal + reden-veld voor audit-trail
  - 🔎 **admin/bots filter uitgebreid**: tokens > 0 OF running OF proactively_registered → registered users zijn altijd zichtbaar zelfs zonder tokens
  - ✅ Backend e2e getest: register → unregister, niet-admin force-sell gefaald (correct 403), closed-pot force-sell gefaald (correct "niet open"), admin/bots list toont proactive users met `proactively_registered=true` flag

- 2026-05-23 **v4_wallet_admin_switch_001**: Wallet-pagina krijgt zelfde admin switch als Trader. `[👤 Mijn | 🌟 Spark]` toggle in header (alleen voor gradatie ≤ 1), `sessionStorage`-persistent, subtitle past zich aan ("Persoonlijk financieel overzicht" / "Spark's wallet (admin view)"). Verified via Playwright: Mijn-view toont De Willem €0,00 + 10 tokens, Spark-view toont Spark €5,08 + 10 tokens

- 2026-05-23 **v4_deposit_19_tokens_001** (€96.52 bijstorting):
  - 💰 **19 tokens uitgegeven** (€5.08 each, fixed-price tier): Spark (user-000) 1→10, Willem (user-001) 0→10. Treasury pool 999999→999980. Mint-transacties + admin-log entries toegevoegd in `roar_balances.json`. `user_wallets.json` synchroon
  - 📥 **Deposit registered**: €96.52 via `/api/trade/deposits/user-001` (Bitvavo SEPA). Trader baseline auto-bumped €5.08 → €101.60 (matcht live Bitvavo wallet). Live P&L €0.00 (schone start)
  - 🤖 **Spark trader hourly default lock-on**: bot draait op user-001 (waar Bitvavo creds zijn), interval=3600s, 5 markets, auto_trade=true, persistent via `bots_registry_state.json`. Auto-resume bij elke server start (dus niet gekoppeld aan inlog — "aan = lock-aan")
  - 👤 **Willem's bot off by default**: kan zelf aan/uit; gebruikt dezelfde Bitvavo-creds en zal binnen z'n 10-token allocatie traden zodra ingeschakeld

- 2026-05-23 **v4_spark_clean_start_001** (mini-batch, follow-up):
  - 🧹 **Spark trader schone start**: user-001 trade_history gearchiveerd → `user-001_archive_pre_spark_clean_<ts>.json`, daarna leeggemaakt (0 trades). Baseline gezet op €5.08 (matcht live Bitvavo wallet)
  - 🤖 **Bot autostart op user-001**: `bots_registry_state.json` verplaatst van user-000 → user-001 (waar de echte Bitvavo creds staan). Bij backend restart: "🤖 1 registry-bot(s) auto-resumed" en cycles loopt direct
  - ✅ Geverifieerd via `/api/trade/stats/user-001` (0 trades, baseline 5.08) en `/api/trade/admin/bots` (running=true, cycles=1, 5 markets)

- 2026-05-23 **v4_welcome_bark_001 + v4_trader_label_swap_001** (mini-batch ~30 credits):
  - ✨ **Welkom-bark voor eerste login** (`welcome_v1`, kind="welcome"): legt uit dat je gewoon een gesprek voert en dat je `help` typt voor een overzicht. Auto-injected in `version_anchor.json` voor zowel verse installs als bestaande deployments. Beschermd tegen verwijderen. Eigen styling (groene Hand-icon) in `BarkQueueOverlay`. Sortering: privacy → welcome → rest
  - 🔄 **Trader wallet-switch labels omgedraaid**: `walletView='me'` (user-001) is nu zichtbaar als "🌟 Spark", `walletView='spark'` (user-000 default) als "👤 Mijn". Routing ongewijzigd, alleen labels swap conform user feedback ("tabs zijn wel goed maar namen moeten andersom")

- 2026-05-22 #3: **v4_dnd_001 — Levende Spark World fundering** (9/9 backend + e2e):
  - 📜 **Lore index** (`/data/dnd/lore_index.json`): 7 avatars-as-functions (Het Eerste Licht=begin, De Reaper=einde, De Boekhouder=balans, Harry=tijd, Madelief=emotie, Mr Smith=manipulatie, The Story Teller=geheugen), 6 behavior-categorieën (observeren/luisteren/zwijgen/helpen/verhalen/manipuleren) met aura-kleuren en unlock-lijsten
  - 🎨 **Aura/Glow systeem**: `GET /api/dnd/aura/{user_id}` berekent live uit behavior counters de top-3 categorieën met kleuren. Op Persoonskaart visueel als gradient-glow + 2-bar layers + unlock-pills
  - 📊 **Behavior tracking**: `POST /api/dnd/track` increment counters (help_msg, kb_create, lie_detected, etc.). Hyperlinks gedrag → identiteit zoals besproken
  - 🌍 **World state**: `GET /api/dnd/world-state` aggregert ALLE user-counters tot per-entiteit dominantie. Wanneer >60% = `dominant=true` flag → klaar voor aspect-bark trigger
  - 👁️ **Spark observatie systeem**: avatar-change → automatische `observe`-call. Bij Spark AI tab eerste-open → `GET /api/dnd/spark-greeting/{user_id}` levert Nederlandse begroeting met benoeming van events. Mark-spoken zorgt geen herhaling
  - 🗺️ **Roadmap Phase D&D**: nieuwe fase met 14 sub-tasks, anchor-IDs zoals `#phase-dnd-aura` voor permalinks. Update-barks kunnen nu `roadmap_ref="phase-dnd-aura"` doorgeven → klikbare link
  - 🔗 **Bark roadmap_ref klikbaar**: opent /roadmap#anchor in nieuwe tab

 + v4_avatar_categories_001 + v4_dnd_help_001** (16/16 backend + frontend e2e):
  - 🚀 **Deploy Anker + Update Bark systeem**: Admin klikt na deploy "Nieuwe anker" met versie + message → bark wordt automatisch getoond aan iedereen bij volgende login. Endpoints: `/api/deploy/anchor`, `/api/deploy/anchors`, `/api/deploy/pending/{user_id}`, `/api/deploy/seen`, `/api/deploy/reset-seen`. Per-user `seen_barks.json` zorgt dat elke bark maar 1x getoond wordt
  - 🔒 **Privacy/Voorwaarden bark** (privacy_v1) wordt automatisch geseed: ELKE user ziet 'm 1x bij eerste login. Niet te verwijderen. Tekst: "Wij volgen je niet, geen tracking-cookies, alle data lokaal in JSON, etc."
  - 🎨 **BarkQueueOverlay** component: cyaan voor privacy, amber voor deploy, lila voor feature. Counter (1/2). Geen-skip → user moet doorklikken. Mounts in MainLayout
  - 🛡️ **Admin Deploy panel** (Notities → Deploy tab): formulier met versie, titel, bericht, icon, roadmap_ref, audience (all/admins). Lijst van bestaande ankers met delete (privacy_v1 niet verwijderbaar) en CURRENT badge
  - 🎒 **Avatar galerij 2 tabs**: Persoonlijk (default) en D&D Archief. PATCH endpoint accepteert `category` field. D&D tab toont info-banner over Spark World D&D laag. Locked avatars (bot-claimed) krijgen 🔒 stempel
  - 🎲 **D&D help chat-commando**: vraag "D&D help", "wat is d&d", "spark world help", "rugzak uitleg", "persoonskaart help" → krijg overzicht met Base Line, Persoonskaart, Rugzak, Avatars en Barks lagen

 + Inventory + Backup Speed** (9/9 backend + UI bevestigd):
  - 💰 Wallet reset: user-001 → 0 tokens, user-000 (Spark) → 1 token / €5.08
  - 🤖 Trade bot filter: alleen Spark zichtbaar (1/2)
  - 🔒 Spark bot onstopbaar
  - 🌟 Privé-glow slaat Spark-DMs over (eigen tab)
  - 🎭 Spark AI bubble toont avatar i.p.v. ster
  - 🔁 Community chat: schoon overzicht per inlog + banner
  - 💡 Roadmap "Jouw Ideeën & Tickets" met `/api/bugs/mine` endpoint

## Original problem statement
Modular, offline-first personal legacy system. Memory & knowledge machine. STRICT requirement: data lives in local JSON files (NO MongoDB).

## User language
Dutch (always respond in Dutch).

## Architecture
- React 18 + FastAPI + JSON file storage at `/app/backend/data/`
- 5-layer AI: NLP heuristics, smart_intents, snap_service, shadow observer, fallback
- Gradation-based visibility (1=eigenaar, 2=fam/admin, 3=vrienden, 4=collega's, 5-7=community)

## Completed (recent)
- 2026-05-21: **v4_user_avatar_helper_001 + v4_bot_no_wallet_001 — Avatar overal + bots zonder wallet** (11/11 tests passed):
  - 👤 **Centrale `<UserAvatar>` component** (`/app/frontend/src/components/common/UserAvatar.js`) resolveert avatar uit `users.json[].avatar` veld:
    - `gallery:xxx` → echte galerij-foto
    - `user` → user-upload
    - `emoji:🎩` → emoji char
    - **null/none** → Roadkill logo (grayscale + opacity-60) als fallback
    - img-error → eerste letter in gradient bg als ultieme fallback
  - 🔄 **Letter-circles vervangen** door echte avatars op 5 plekken:
    - Admin → Gebruikers (links lijst + detail-header)
    - Sidebar bottom (gebruiker-info, "D" → De Willem's Black Knight)
    - Privé tab (contacts lijst, header, empty-state)
    - Community tab (CommunityBubble met msg.avatar enrichment)
    - Spark AI tab — al avatar-vrij
  - 💼 **Wallet & Tokens kaart verborgen voor bot-users** (`bot-harry`, `bot-madelief`, `bot-smith`, `bot-boekhouder`). Bots hebben geen IBAN/EUR/ROAR. Spark (user-000) houdt wel zijn wallet kaart als admin
  - 🛡️ **Admin-collectief contact** krijgt nu ook `avatar_ref: "emoji:🛡️"` zodat het de schild emoji toont
  - 🔐 **Privacy intact**: non-admin viewer ziet `avatar_ref=null` voor anonymized admin-contact

 + v4_avatar_gallery_edit_001 — Spark eigen avatar + Gallery edit** (9/9 backend + 5/5 frontend tests passed):
  - 🌟 **Spark krijgt eigen avatar-beheer**: user-000 verschijnt al in admin user list, AvatarManagerCard werkt identiek aan bot-users. Toont nu **SPARK CORE** badge ipv BOT-badge. Spark heeft eigen `owner` optie in dropdown
  - ✏️ **Gallery edit modal**: admin kan via hover-edit-icoon op elk gallery-item de **title, bot_owner, tags** wijzigen. `PATCH /api/avatar/gallery/{id}` met admin-guard (403 voor non-admin). Modal toont preview + 6 owner-opties (Geen/Spark/4 bots)
  - 🔒 **Robuuster lock-systeem**: `_get_bot_owner()` checkt nu eerst expliciete `bot_owner` field (admin-managed) en valt terug op title-match voor seed-data. Spark (user-000) toegevoegd aan eigenaar-map. Joker/De Trader avatar (id `0ef0b726773e`) was per ongeluk verkeerd getiteld — admin kan dit nu zelf rechtzetten via UI

 + Ronde 2 start — v4_avatar_fallback_001 + v4_avatar_bot_lock_001 + v4_community_archive_001 + v4_community_recap_001 + Base Line lore** (14/14 backend + 2/2 frontend tests passed):
  - 🏍️ **Roadkill logo als avatar fallback**: `/api/avatar/current/{user_id}` returnt nu `fallback_url` + `is_fallback` flag. Community-messages enrichment gebruikt roadkill logo (met opacity-60 grayscale) wanneer user geen avatar heeft
  - 🔒 **Bot-avatar locket-stempel**: 3 avatars in galerij (Harry Klokkenmaker, Mr Smith, Madelief Stouten) zijn automatisch gemarkeerd via title-match als `bot_owner: bot-{naam}`. Frontend toont gouden 🔒 icon rechtsboven op locked avatars. Non-admin user die een locked avatar probeert te kiezen → HTTP 403 met owner-info. Admin én de bot zelf mogen wel
  - 📜 **Base Line lore** opgeslagen als KB-kaart (`begrip: Base Line`) met volledige 4 lagen, 5W+H, tags `[base line, spark world, lore, d&d, oorsprong, ad, puls, licht, schaduw, fracties, elementen]` + extra entry in Spark's eigen `scratch.json`. Spark herkent het concept in chat na cache-clear
  - 🗂️ **Community archief**: `GET /api/bots/community/archive` returnt jaar→maand→dag-tree met counts/first/last per dag. Met `?year=Y&month=M&day=D` haal je messages van die dag chronologisch
  - 📋 **Community recap**: `GET /api/bots/community/recap?offset_days=1` (gisteren) of `?date=YYYY-MM-DD` geeft samenvatting met top_topics, user_counts, bot_counts en preview. Voor 2026-03-18 detecteert het 82 berichten met Willem Spakman als top user
  - 💬 **Chat-commando "Wat is gisteren besproken?"**: nieuwe `detect_community_recap_intent()` in `smart_intents_service.py`. Matcht varianten: "wat is gisteren/vandaag/eergisteren in de community besproken/gezegd/gepraat", "community recap", "samenvatting van de community". Returnt type=`community_recap` met geformatteerd bericht starting met "📋 **Community-recap gisteren**"

 — v4_glow_notify_001 + v4_admin_collectief_001 + v4_spark_unstoppable_001 + v4_admin_avatar_001** (10/10 backend tests passed):
  - 🔔 **Glow voor unread privé-DMs**: `urgent/routes.py` heeft nu `_prive_glow_for_user()` die unread privé-berichten optelt. 1-2 unread = amber, ≥3 = red. **Boekhouder-DM = altijd red** (financiële trade-alerts vallen op). Glow zet automatisch `chat` + `chat-prive` sidebar/sub-tab keys
  - 🛡️ **Admin-Collectief privé kanaal**: virtueel contact "Admin Collectief" (emoji 🛡️) bovenaan in Privé-tab voor alle admins (gradatie ≤ 2). Berichten in `/data/chat/admin-collectief.json` worden gebroadcast naar alle andere admins (unread_by = leden minus sender). Non-admins krijgen HTTP 403 als ze proberen te posten. Aparte glow `chat-admin-collectief` mogelijk
  - 🔒 **Spark's bot onstopbaar**: `POST /api/trade/bot/stop/user-000` returnt `{success: false, code: "SPARK_UNSTOPPABLE"}`. Ook `monitor/stop` en `monitor/pause` zijn beschermd als Spark's user_id actief is. Andere users kunnen normaal worden gestopt
  - 🎨 **Admin avatar-beheer voor bot-users**: `AvatarManagerCard` component in `UsersAdminPage.js`. Werkt voor élke user incl. bots (`bot-boekhouder`, `bot-madelief`, etc.). Drie acties: upload eigen foto, kies uit galerij (28 thumbnails), verwijderen. BOT-badge wanneer user een bot is
  - 📦 **Voor Ronde 1 al eerder gedaan** in dezelfde sessie: wallets/potjes reset (Spark 1 token / €5.08), rangen gesynced via `XP // 100`
- 2026-05-21: **v4_boekhouder_001 + v4_sell_trigger_002 + v4_mr_smith_001 + v4_trade_analytics_001 + v4_audit_001 + v4_boekhouding_001**:
  - 🐛 **Sell trigger fix**: was `+1% trail / -0.4% drop`, nu **cent-niveau**: trail aan bij netto ≥ 2× fees, exit bij eerste daling waar netto ≥ 1× fee blijft. Float-precisie bug gefixed met `round(x, 6)`. Werkt op €1-potje én €100-potje
  - 🎩 **De Boekhouder persona**: nieuwe bot-user `bot-boekhouder` (gradatie 2, acteur) met KB-kaart + 5W+H. Service in `/app/backend/modules/boekhouder/service.py`. Hooked in `potjes.open_pot()` en `close_pot()` voor BUY/SELL announcements:
    - Privé-DM naar admin: gedetailleerd met cijfers (potje, prijs, netto, fee)
    - Community trade-feed (`/data/chat/community/trade-feed.json`): cryptisch/leuk zonder bedragen. Random tone-variants ("Hahaha winst, uhh sorry", "De BCH-koers stond te aanlokkelijk laag")
    - Spark-trades only voor community feed (andere users blijven privé)
  - 📋 **Audit-trail**: append-only `data/system/audit_log.json` voor élke geld/token-beweging (trade_buy/trade_sell/fee_transfer). Onveranderbaar
  - 🕴️ **Mr Smith waarschuwing** voor backup-download: dialog in `IntegratiesPage.js` met Matrix-style melding "Alle informatie wordt vanaf dit moment niet meer bewaard". Anchor pas gelogd ná download-trigger via `POST /api/backup/anchor` (failed = geen anchor, geen data-loss)
  - 📊 **TRADE Analytics tab** in admin: lijst alle running bots (status/cycles/uptime/markets/intervals) + community trade-feed + audit-log live. Stop-bot knop per user. Auto-refresh 15s
  - 💼 **Boekhouding skelet** (4 entiteiten verrijkt):
    - `spark_core` — Spark AI, btw_plichtig=False, bank=Bitvavo
    - `spark_your_life` — btw_plichtig=True (jouw zakelijk)
    - `roadkill_merch` — btw_plichtig=True (jouw zakelijk)
    - `personal_willem` — btw_plichtig=False (privé)
    - Velden: `btw_nummer`, `kvk_nummer`, `bank.iban`, `bank.naam`, `bank.provider`
    - `btw_tarieven` config (21/9/0), `dagboeken` list (verkoop/inkoop/bank/kas/memoriaal)
    - Endpoints: `GET /api/accounting/entities`, `PATCH /api/accounting/entities/{eid}` (admin update IBAN/BTW/KvK), `GET /api/accounting/btw-summary?entity_id=X&year=2026` (BTW per tarief voor aangifte)
  - 🔌 **Per-user bot UI hook** in TraderPage: `startMonitor()` gebruikt `/api/trade/bot/start/{userId}` voor non-admins (token-gated), legacy `/api/trade/monitor/start` voor admin. Foutmelding via alert bij weigering
  - **Veilig om te redeployen** zodra je dit ziet — geen state-data verloren
- 2026-05-21: **v4_per_user_bot_001 + v4_spark_fee_001 + v4_token_gate_001 + v4_wallet_per_user_001**:
  - **Per-user tradebot architectuur**: `MonitorService` was singleton, nu instantieerbaar per user-id via `MonitorRegistry` (`get_user_monitor(user_id)`). Legacy `get_monitor()` blijft werken voor backward-compat (Willem's single monitor)
  - **Token-gate quick-buy**: `/api/trade/quick-buy-potje/{user_id}` controleert nu gradatie ≤ 1 (alleen admin mag handmatig potje kopen). UI: knop disabled met uitleg voor andere users
  - **Token-gate bot-start**: `/api/trade/bot/start/{user_id}` checkt: gradatie ≤ 1 OF user-000 (Spark) bypass, anders moet user ≥ 1 token hebben (1 token = 1 potje slot)
  - **5% Spark fee**: `close_pot()` houdt 5% in op netto SELL ≥ €0.10 → naar Spark wallet (user-000). Spark zelf betaalt geen fee aan zichzelf (uitgesloten). Fee gelogd in `wallets.json[user-000].fee_log`
  - **Wallets per user**: alle 12 users hebben nu wallet met `wallet_id = user_id` (klaar voor latere bank-koppeling). `ensure_wallet()` is idempotent, `POST /api/wallet/backfill-all` ran eenmalig
  - **Admin UI**: nieuwe "Wallet & Tokens" kaart per user in UsersAdminPage (Overzicht tab) met wallet_id, EUR saldo, ROAR tokens, IBAN-placeholder + knoppen "+1/+10 token", "−1 token". Geblokkeerd voor admin-account zelf
  - **Admin endpoints**: `POST /api/wallet/admin/token/grant/{uid}`, `revoke/{uid}`, `GET /api/wallet/admin/overview`
  - **State-update 21 mei**: Willem 0 tokens / €0 / 0 potjes (alles verkocht). Spark 10 tokens / €50.80 / 10 potjes (zijn eigen tradebot start nu). Treasury_pool 999.980 nog uit te geven
  - **Spark eigen bot** gestart: user-000, 1h candles, 5 coins (BCH/BTC/ETH/SOL/ADA), real-trade, 10-potjes mode
  - **Trade Analytics endpoint** `GET /api/trade/admin/bots` toont status van alle running bots
- 2026-05-20: **v4_meetpunt_002 — Recent Trades clean view + multi-coin LIVE**:
  - BUY-row van meetpunt-paar gevlagd `hidden_in_recent: true`. Frontend `trades.filter(t => !t.hidden_in_recent)` toont nu 1 trade in Recent Trades widget (SELL met +€50,80)
  - Stats endpoint (`/api/trade/stats`) blijft beide entries gebruiken zodat math klopt (gekocht €5,08 / verkocht €56,03 / fees €0,15 / netto +€50,80)
  - Multi-coin monitor LIVE gestart op alle 5 watchlist coins (BCH/BTC/ETH/SOL/ADA) — 15m candles, 10-potjes mode, real-trade
  - Bitvavo IP-ban verlopen, candle TTL-cache + shared ticker-call houden het binnen rate-limits
- 2026-05-20: **v4_meetpunt_001 — Trade history reset naar meetpunt**:
  - Oude `trade_history/user-001.json` (8 oude BUY-trades, geen SELLs → vervormde stats) gearchiveerd als `user-001_archive_pre_reset_*.json`
  - Nieuwe history: 1 BUY + 1 SELL trade-pair voor pot-001 met exact-berekende fees:
    - BUY 5,08 EUR @ 305,00 (fee €0,0127)
    - SELL 56,03 EUR (fee €0,1401) → bruto +€50,95 - fees €0,1528 = **netto +€50,80**
  - `/api/trade/stats/user-001` toont nu consistent: 2 trades, gekocht €5,08, verkocht €56,03, fees €0,15, netto +€50,80, baseline €101,60, live P/L = live - baseline
  - Verhaal in lijn: €5,08 basis + €50,80 winst pot-001 + €45,72 idle 9 potjes = €101,60 baseline
- 2026-05-20: **v4_multi_market_001 — Multi-coin monitor + UI sync fixes**:
  - **Bug fix**: chart-label was hardcoded "BCH-EUR", staat nu dynamisch op `{candleMarket}`. Klik op watchlist-coin → chart switcht direct (`setCandleMarket` toegevoegd aan `onClick`)
  - **Bug fix**: Snelhandel "Live prijs" toonde altijd `tickers[0]` (= BCH), volgt nu `qtMarket` via `tickers.find(x => x.market === qtMarket)`
  - **Multi-coin monitor**:
    - `MonitorService.start()` accepteert nieuw `markets: List[str]` param (legacy `market: str` blijft werken als 1-element)
    - `_loop()` herschreven: per cycle één ticker-call voor àlle coins (`fetch_tickers(base_symbols)`) + per market een `_run_market_cycle()`. SELL/BUY checks per market, pot.market koppeling voor selectief sluiten
    - Status response heeft nu `markets: []` + `last_prices: {market: price}` velden
    - Persist state slaat markets-lijst op zodat auto-resume na backend-restart werkt
  - **Candle TTL-cache** in `fetch_candles()`: per (market, interval, limit) bewaart laatste fetch + TTL = candle-interval seconden. Bij rate-limit (429) returnt stale cache. Voorkomt Bitvavo ban bij multi-coin monitor
  - **Frontend**: coin-picker in Monitor-paneel (BCH/BTC/ETH/SOL/ADA toggle), status-bar toont alle actieve markets, beslissingen-lijst toont coin-tag per beslissing
  - Bekend: tijdens ontwikkelen hebben we Bitvavo rate-limit ban opgelopen (~12 min). Cache + shared-ticker-fix voorkomt herhaling
- 2026-05-20: **v4_token_potje_001 — Token-economie ↔ trading sync + schone reset**:
  - **Reset user-001**: 11 BCH-potjes (€66,42 capital) vervangen door schone start. Backup in `user_potjes.json.bak_pre_reset.json`
  - Nieuwe state: 10 potjes à €5,08 (basis €50,80) + overflow_pool €45,88 = **totaal €101,60** (matcht nieuwe Bitvavo EUR-saldo)
  - Pot-001 stats: 1 trade, 1 win, +€50,80 PnL (gerealiseerde winst eerste trade — €4,92 in pot, €45,88 in overflow voor toekomstige expansie)
  - **Baseline_eur** → €101,60 (was €50,80) zodat live-PnL vanaf nieuwe start telt
  - **Spark bonus tokens** (`/data/roar/roar_balances.json[spark_bonus]`):
    - `_mint_spark_bonus_tokens()` in `potjes.py`: bij netto trading-winst > 0 → cumulatieve teller. Per volle €5,08 → 1 bonus-token gemint naar Spark's eigen treasury
    - Auto-trigger in `close_pot()` na elke winstgevende SELL
    - Geen uitcash-UI nu — komt later bij wallet↔bank koppeling (Bitvavo IBAN)
    - Admin (gradatie 1) beslist wanneer Spark zijn spaarpot mag gebruiken
  - **Token-verkoop event-log** in `shop/routes.py sell_tokens()`: bij verkoop van ≥10 tokens → `freed_potje_slots` veld in transactie + description ("10 ROAR verkocht → 1 potje-slot vrij voor Spark"). Hard capital-vrijgave volgt later
  - **GET `/api/shop/token/spark-bonus`** — nieuwe endpoint toont Spark's bonus balance, cumulatieve winst, progress naar volgende token, laatste 5 mints
  - **Monitor herstart** met nieuwe baseline (real-mode, 10-potjes, BCH-EUR 15m)
  - Unit-getest: 3 mint-scenarios (€5,20 → 1 token, +€0,50 → 0 extra, +€4,50 → 1 extra). Sell event-log getest met 10-token transactie ✓
  - Bekend punt voor user: dynamische token-prijs (€10,22 nu) overruled BASE_PRICE €5,08 bij ≥10 tokens uit (spark_core / circulating). User wilde vast €5,08 — afstemmen of we BASE_PRICE altijd forceren of dynamiek behouden voor token-holder waardegroei
- 2026-05-20: **v4_dashboard_renew_001 + v4_analytics_layer_001**:
  - Dashboard Kennisbank kaart: label _"Te Herzien"_ (toonde 0 — frontend zocht naar bestaande `te_herzien` key die backend niet had) → _"Renew"_ gekoppeld aan `review_pending` (2986 kaarten)
  - Analytics → LAYER tab: was mock-data met "In ontwikkeling" banner → **live scan** via nieuw `GET /api/admin/architecture` endpoint
    - Scant `/app/backend/modules/` runtime: telt `.py` files, `@router.` decorators, size_kb per module
    - Scant `/app/frontend/src/components/` voor component-aantal per groep
    - Toont 4 lagen (Presentatie/API/Service/Data) met live metrics: 30 modules, 231 routes, 91 service files, 659.9 KB
    - Top-15 backend modules + alle frontend groups als sortable lijst (trade 28 routes, profile 23, chat 17...)
- 2026-05-20: **Roadmap-archeologie**:
  - 9 historische items uit code geïdentificeerd die NIET in roadmap stonden:
    - **v3.0 done**: `v3_012` (homoniem-flow), `v3_013` (Spark Leraar achievement +XP-bonus), `v3_028` (auto-zin-snap)
    - **v4.0 done**: `v4_013` (Spark Vocab), `v4_013c` (Fallback Service), `v4_016` (Insights Module), `v4_025` (User-time helper), `v4_grad_suggest_001` (gradatie-voorstel admin)
    - **v4.0 open**: `v4_017` (Advisor UI / Spark Inzichten pagina)
  - Code↔roadmap nu 100% gesynchroniseerd
  - Spark's user-000 profile.json gecorrigeerd: was te dun, nu mirror van rijke users.json entry (Core 4.1, missie, kernwaarden, 27150 XP, 4 achievements). Scratch entry-0 herzien om niet alsof Spark nieuw is te klinken
- 2026-05-20: **v4_spark_self_001 — Spark's eigen anker (folder + intents)**:
  - Folder `/data/users/user-000/` aangemaakt met `profile.json` (Spark's identiteit: naam, missie, geboortedatum, stem) + `scratch.json` (data-anker)
  - Nieuwe chat-intents in `spark_self_service.py`:
    - **Note**: _"Spark, onthoud voor jezelf: ..."_ / _"noteer voor jezelf: ..."_ / _"jouw observatie: ..."_ → parkeert entry in scratch.json
    - **Read**: _"wat heb je vandaag geleerd?"_ / _"wat zit er in jouw scratch?"_ / _"jouw observaties"_ → toont laatste 5 entries
  - Entries hebben `kind` (observatie/user_request/etc), `source` (user_naam), `ts`, `tekst`
  - Help-overzicht uitgebreid met "Spark's eigen anker" command
  - Klaar voor later: TTS voice-clone metadata, "wat-leer-ik-vandaag" auto-mining, Spark's reflectieve loop (v5)
- 2026-05-20: **Bug-batch fixes uit user-feedback**:
  - **#5 Help mist 'stop'**: nu vermeld als _"Stop een lopend proces — bv. 'stop' of 'klaar'"_
  - **#2 'ik ken Joel' geen relatie**: nieuwe patterns `PATTERN_KEN_NAAM` + `PATTERN_NAAM_KEN_IK` → relatie 'bekende' (`bekende` toegevoegd aan REL_TYPES). Werkt: "ik ken X" / "X ken ik" → auto-extract
  - **#12 Community-bericht in Spark Dashboard chat**: Dashboard widget gebruikt nu `?channel=spark` filter. `chat-history` endpoint heeft default `channel='spark'` parameter
  - **#4 Spark leert niet uit community**: `bots/community/send` retourneert nu `snap_candidates[]` (woorden ≥6 letters die niet in KB staan + niet stopwoord). Frontend kan later snap-flow triggeren op klik
  - **Vocab triggers UI werkt al** — user bewerkte in PRODUCTIE (preview heeft ander dataset). `/api/spark/vocab/{group}/{key}/add` endpoint draait correct. Ook generieke `/api/triggers/edit/vocab/...` route toegevoegd als fallback
- 2026-05-20: **Roadmap uitgebreid met 7 nieuwe pending items uit bugs**:
  - v4_potje_acting_as_001 (P1), v4_xp_correction_001 (P2), v4_glow_notify_001 (P1)
  - v5_parafrase_layer (P3, future), v6_roar_token_001 (P3), v6_grad2_potje_token (P3)
  - v4_voice_tab_relocate (P2)
- 2026-05-20: **Help + Roadmap up-to-date**:
  - `handle_help()` user-commands van 15 → 19 (Testament, Survivalgids, Documenten, Privacy/Cookies/Voorwaarden expliciet)
  - Admin-extra van 7 → 10 (credits via chat + via UI gesplitst, credits-bonus matching uitleg, Avatar Galerij beheer)
  - Hint toegevoegd: "Achtergrondgeluid blijft door na F5"
  - Roadmap: 8 open backlog-items zichtbaar als items (zodat "wat zou je willen doen" ze kan oppakken):
    - v4_gradatie_split (P0), v4_accounting_002, v4_kb_split_001, v4_snap_dedupe_001, v4_dq_b, v4_legal_pages_001, v4_personal_docs_003, v4_personal_docs_004
  - Roadmap summary: P0 blockers + P1 open expliciet benoemd
  - Notes opgeschoond: alleen 9 recente entries van deze sessie
- 2026-05-20: **v4_personal_docs_002 — Archief-UI integratie**:
  - Nieuwe tab **"Documenten"** in `ArchiefPage.js` naast Bestanden/Foto/Geluiden/Filmpjes/Gesprekken
  - Lijst toont aangemaakte docs (testament/survivalgids/etc) als cards: emoji, titel, versie, secties-aantal, grootte, last_updated
  - Klik card → detail view met alle secties (gele border-left accent), "📝 leeg" placeholders waar nog niets staat
  - **Download JSON** knop per doc (export voor backup/migratie)
  - Aparte sectie "Beschikbaar om aan te maken" toont nog-niet-bestaande types als ghost cards met hint _"maak X aan"_
  - "Beheer via chat" indicator ipv upload-knop (consistent met dat docs via chat-flow opgebouwd worden)
  - Klaar voor template-upload later: drop een JSON → vervangt mits structuur matcht
- 2026-05-20: **v4_personal_docs_001 — Persoonlijke documenten via chat (testament + survivalgids)**:
  - Generiek patroon: `DOC_TYPES` dict met label/emoji/default_secties/triggers — uitbreidbaar voor zorgvolmacht/wensen/levensoverzicht/etc.
  - Storage per user: `/data/users/{user_id}/documents/{doc_type}.json`
  - Chat-intents per doc-type:
    - **create**: "maak testament aan" / "survivalgids aanmaken" → skelet met default secties
    - **append**: "voeg toe aan testament: <tekst>" → nieuwe gedateerde sub-sectie + version++
    - **show**: "bekijk testament" → mooi geformatteerd
    - **delete**: "verwijder testament" → soft-delete (rename naar .deleted-{ts}.json)
  - Default secties:
    - Testament (6): Persoonsgegevens / Erfgenamen / Legaten / Executeur / Uitvaart / Overige
    - Survivalgids (7): Contacten / Documenten / Wachtwoorden / Verzekeringen / Bankzaken / Praktisch / Boodschap
  - API endpoints: `GET /api/personal-docs/{user_id}` (lijst) + `GET /api/personal-docs/{user_id}/{type}` (volledig doc)
  - Klaar voor archief-integratie (later): documenten kunnen in Mijn Archief → Bestanden tab verschijnen via list-endpoint
  - Klaar voor template-upload (later): user upload JSON van aanbieder → vervangt JSON mits structuur matched
- 2026-05-20: **v4_legal_help_001 — Help admin/user + legal triggers**:
  - `handle_help(is_admin)` toont nu **basis-help voor iedereen** + **admin-extra** sectie voor gradatie ≤ 2 (credits beheer, roadmap-bugs flow, trigger/vocab beheer, backup, gradatie-upgrades, storage cache)
  - Nieuwe legal-intent service (`legal_service.py`) detect: `privacy`, `cookies`, `voorwaarden`
  - 3 JSON-content files in `/data/system/legal_*.json` (versie 0.1-draft, klaar voor admin om in te vullen):
    - `legal_privacy.json` — wat slaat Spark op, niet deelt, jouw rechten
    - `legal_cookies.json` — sessionStorage/localStorage/server-side, geen tracking
    - `legal_voorwaarden.json` — wat is Spark, aansprakelijkheid, accountregels
- 2026-05-20: **Roadmap cleanup**:
  - `technical_debt`: 4 → 3 (oude GameTab/AdminTab refs verwijderd, WS-error weg)
  - `known_issues`: WebSocket dev-spam verwijderd, alleen KB duplicates blijft
  - `notes`: 22 → 12 (oude pre-mei items naar `historical_notes` archief)
  - `summary.v4.0_progress`: 83/104 (80%) na toevoegen van 8 nieuwe done-items deze sessie
- 2026-05-20: **v4_ambient_persist_001 — Ambient overleeft F5**:
  - Bug: ambient verdween na page-refresh; user moest "stilte" + "ambient 1 aan" opnieuw typen
  - Fix: `getAmbientPlayer()` singleton in `GesprekkenPage.js` persisteert nu `{url, label, volume}` in `localStorage` (key `spark_ambient_state`)
  - Bij init: `restoreFromStorage()` probeert direct te starten
  - Browsers blokkeren autoplay zonder user-gesture na F5 → fallback: nieuwe **amber pending-resume bar** met "🎵 Ambient — klik om door te spelen" + **Hervatten** en **Stoppen** knoppen
  - Auto-resume: globale `click/keydown/touchstart` listener probeert ambient meteen te starten bij eerste user-actie (ook typen in chatveld telt)
  - Stop wist localStorage zodat hij niet onverwacht na F5 terugkomt
- 2026-05-20: **v4_dank_004 — Credits bonus voor herkende users**:
  - Naam in dank.json `namen[]` met spatie (voor+achternaam) wordt gematcht tegen `users.json[].volledige_naam` (case-insensitive)
  - Match + gradatie ≤ 4 → user krijgt:
    - `credits_bonus: true` (flag, idempotent)
    - `credits_multiplier: 1.2` (toekomstige trust-gains × 1.2 via `_trust_carry` accumulator)
    - One-time `trust_score +10` (capped 100)
    - Timestamp `credits_bonus_applied_at`
  - Auto-sync na elke rename/add in credits (via chat of Triggers UI). Spark vermeldt herkenning in chat-bericht.
  - Admin endpoints: `GET /api/admin/credits-bonus` (status) + `POST /api/admin/credits-bonus/sync` (handmatig)
  - `update_activity` gebruikt nu `credits_multiplier` met fractional carry (1.2 = +1 met 0.2 carry, na 5× +6 totaal)
  - Getest: Heidi Spakman (grad 3) toegevoegd → +10 trust, mult 1.2 ✓
- 2026-05-20: **v4_dank_003 — Credits edit via chat**:
  - Spark verstaat in chat (mits scope-keyword `credits|bedank|dank` in zin):
    - **rename**: _"verander Nick naar Nick Teeuwen in de credits"_, _"wijzig Lotus Martens naar Lotus in bedanklijst"_, _"pas Nick aan naar Nick Teeuwen in credits"_
    - **add**: _"voeg Pieter Smith toe aan de credits"_
    - **remove**: _"verwijder Heidi uit de credits"_
  - **Disambiguation**: als naam vaker voorkomt (bv. 2× Nick), vraagt Spark verduidelijking ipv blind eerste pakken
  - Regex met negatieve lookahead `_NW` filtert stopwoorden (naar/in/tot/de/het/credits/toe/erbij) zodat namen schoon worden geparsed
  - Geïntegreerd in `chat/routes.py` vóór credits-info-intent (anders zou "credits" winnen)
- 2026-05-20: **v4_dank_002 — Credits in Triggers UI + Lotus Martens**:
  - Lotus Martens toegevoegd achteraan voornamen-lijst (vóór "iedereen die ik vergeet")
  - 2 nieuwe groepen in Spark AI → Triggers (filter: Conversatie):
    - `credits_namen` — Credits — Voornamen (7 items, met X-knop per naam + toevoeg-veld)
    - `credits_extra` — Credits — Extra dank (community e.d.)
  - Backend: kind `credits` toegevoegd aan `_KIND_TO_FILE` → maps naar `dank.json`. Edit-endpoints `POST /api/triggers/edit/credits/{namen|extra_dank}/add` en `DELETE /api/triggers/edit/credits/{key}/triggers/{word}` werken
  - Sparks credits-bericht toont nu: "Maurice, Nick ×2, Heidi, Ron, Arent en Lotus Martens"
- 2026-05-20: **v4_dank_001 — Sparks bedank-uiting**:
  - `/data/system/dank.json` met voornamen (Maurice, Nick × 2, Heidi, Ron, Arent), de community, "iedereen die vergeten wordt"
  - `dank_service.py` met 2 detectors:
    - `detect_credits_intent` ("credits", "wie heeft jou gemaakt", "aan wie ben je dankbaar") → **altijd** bedanken, credits_count++
    - `detect_free_choice_intent` ("Spark wat zou jij willen doen?", "kies zelf") → **1× bedanken** (first_choice_done flag), daarna valt door naar `handle_suggest` (agenda/roadmap)
  - Geïntegreerd vóór bestaande suggest-intent in `chat/routes.py`
  - Format: "Maurice, Nick ×2, Heidi, Ron en Arent — bedankt" + extra dank voor community
- 2026-05-20: **v4_profile_revamp_001 — Mijn Profiel volledig herzien**: 5 tabs in plaats van 3 (Algemeen / Achtergrond / Persoonlijkheid / Gesprekken / Avatar). Elke tab heeft eigen content (was eerst alles op één pagina).
  - **Algemeen**: avatar-preview, leeftijd/beroep/locatie/opleiding, geslacht, sociale media
  - **Achtergrond**: NAW + contact + adres + noodcontact + bank (formele identiteit)
  - **Persoonlijkheid**: 6 sliders + doelen/behoeften/zintuigen/mediagedrag + Pijn/Angst sectie (read-only, Spark observeert)
  - **Gesprekken**: eigen chat-historie gesorteerd jaar→maand→dag (collapsible tree), system-prompts uitgefilterd. Endpoint `GET /api/profile/chat-history/{user_id}` (649 gesprekken Willem zichtbaar)
  - **Avatar**: huidige avatar + galerij-kiezer + eigen portret-upload
- 2026-05-20: **v4_avatar_001 — Avatar systeem**: 
  - Backend module `/api/avatar/*` (gallery + user portrait + select)
  - Pillow resize max 512×512 JPEG quality 85 (storage-vriendelijk: 35KB voor 512×512)
  - System-galerij `/data/system/avatars/` (admin-only beheer, alle users kiezen)
  - User-portret `/data/users/{id}/avatar.jpg` (scope=profile, niet in algemeen archief)
  - `users.json[id].avatar = "gallery:{id}" | "user" | null` voor selectie
  - Admin sectie in **Beheer → Instellingen → Beeld → Avatar Galerij** (upload titel+tags, delete, SEED-badge)
  - Seed: Roadkill-logo gekopieerd uit user-001 archive naar `/system/avatars/roadkill-logo.jpg`

- 2026-05-13: Spark Vocab editable via Triggers page (v4_013a)
- 2026-05-13: Static strings → JSON, all trigger lists editable (v4_013c)
- 2026-05-14: Knowledge schema 2.0 (kaart_type + metadata)
- 2026-05-15: Backup/Restore ZIP (export changes/full + dry-run preview)
- 2026-05-15: Shadow Observer (v4_015) + dashboard widget
- 2026-05-15: Chat session storage + Recap intent + Glow notifications
- 2026-05-15: Smart Chat Intents (Agenda, topic overview, roadmap check) + 5W+H consent
- 2026-05-15: Trader keepalive + Snelhandel Quick Buy met Potjes auto-pickup
- 2026-05-15: Dagboek tree-view (Year→Month→Day)
- 2026-05-15: Spark self-aware welcome via system:login event
- 2026-05-16: Dashboard "Gesprekken" card live
- 2026-05-16: Verbanden Statistieken top 20 + dynamic bars
- 2026-05-16: **v4_bugs_001/002** — Bug-melder MVP + status-update PMs
- 2026-05-16: **v4_notities_tree_001** — Notities/Taken tree-view
- 2026-05-16: **v4_dq_a** — Code Quality: circular imports + secrets.choice
- 2026-05-16: **v4_016a** — Analyser unused-vocab (read-only)
- 2026-05-16: **v4_kb_create_001** — Kennisbank "Nieuwe kaart" tab + dup-check
- 2026-05-18: **v4_identity_001** — Identity-Intent laag (Spark over zichzelf)
- 2026-05-19: **v4_logout_001** — logout clear_state
- 2026-05-19: **v4_5w_consolidate_001** — bulk card_session flow deprecated
- 2026-05-19: **v4_xp_fix_001** — achievements via xp_service (optellend)
- 2026-05-19: **v4_actions_001** — Action-Intent laag: STT + Ambient via chat
- 2026-05-19: **v4_time_001** — "Hoe laat is het?"
- 2026-05-19: **v4_rel_001** — Relation Extraction (22 types)
- 2026-05-19: **v4_settings_001** — Settings architectuur: system.json + user_overrides, gradatie-gating, 19 keys
- 2026-05-19: **v4_voice_002** — Voice flow upgrade: auto-start mic op (stt aan), 2s stilte-detectie + auto-send (configurable `stt_silence_sec`), TTS-glow indicator, continue voice-loop na Spark antwoord
- 2026-05-19: **v4_vocab_growth_001** — Vocab kandidaten uit kennisbank + approve-flow (`/api/spark/vocab/approve-growth` → algemeen.uit_kennisbank), tags-zonder-kaart endpoint, "Groeien" tab in Spark Brain
- 2026-05-19: **v4_data_recovery_001** — Atomic save_json (tmp+rename), graph orphan-check + orphan-recover endpoints. 74 weeskaarten hersteld uit graph→KB (waaronder 2 Arent-kaarten die "kwijt" leken)
- 2026-05-19: **v4_agenda_announce_001** — Spark vermeldt aankomende afspraak (≤60min) in welcome message. Glow ack-flow: klik op nav/tab → POST /api/urgent/acknowledge → glow uit. Ack TTL = event_dt+10min.
- 2026-05-19: **v4_rel_002** — relation_extraction sync naar persons cards: nieuwe relaties uit chat schrijven nu OOK in `/data/persons/{user_id}.json` (cards UI). Bestaande relations gemigreerd: Arent Pelster (jeugdvriend), Willie Bakker (vader, overleden), Heidi Spakman (moeder), Maurice (vriend i.p.v. collega), Maaike Spakman (zus). Fix maakt sneller zichtbaar in Persoonkaarten UI.
- 2026-05-19: **v4_notes_002 — user-bound notes/tasks**: `/api/notes/*` heeft nu verplicht `user_id` param + filtert op owner. 403 bij andermans notitie. Bestaande 3 notities gemigreerd naar user-001. Vóór deze fix waren alle notes 1 gedeelde pool voor alle users.
- 2026-05-19: **v4_dashboard_grad_001 — Dashboard per gradatie**: 4 widgets (Triggers, Systeem Status, Gebruikers, Shadow Observer) + 2 top-stats (Triggers/Users badges) nu alleen zichtbaar voor gradatie ≤ 2. Lower gradaties zien een gestripte, persoonlijke dashboard.
- 2026-05-20: **v4_gradatie_visibility_002 — Tab-finetune per gradatie** (12 bug-fixes uit prod):
  - Grad 2: -Voice (wel Gebruikers tab — `isAdmin` uitgebreid naar gradatie ≤ 2)
  - Grad 3: -Voice (zelfde als 4)
  - Grad 4: -Voice
  - Grad 5: -Voice -Trade -Boekhouding
  - Grad 6: + -Dagboek
  - Grad 7: + -Agenda -Archief
  - Visueel getest met 4 bestaande users (Harry/Smith/Heidi/Madelief): alle 12 bugs ✓ opgelost
- 2026-05-20: **v4_route_guard_001 — Admin routes guard** (bug #5): non-admins (gradatie > 2) die op `/admin/users`, `/admin/analytics` of `/admin/settings` URL landen worden automatisch teruggestuurd naar dashboard. Voorkomt witscherm/leeg-pagina na gradatie-wijziging.
- 2026-05-20: **v4_grad_titel_001 — Warme gradatie-titels**: gradaties hernoemd van klinisch ("Communityleden", "Klanten", "Onbekenden") naar warm ("Vriend", "Community Plus", "Community Member", "Bekend", "Leert graag kennen"). Backend `/login` retourneert `gradatie_titel` veld. Sidebar/dashboard tonen warme titel ipv "Gradatie X" (nummer alleen voor admins zichtbaar).
- 2026-05-20: **vocab-growth seed**: 15 natuurlijke woorden toegevoegd uit kennisbank-kandidaten (mensen, communicatie, gedrag, natuur, leven, taal, kennis, tijd, energie, iemand, iedereen, gesprekken, informatie, dieren, ontwikkeling).
- 2026-05-20: **Roadmap sync**: 20 items toegevoegd aan v4.0 roadmap (11 recent-done + 9 nieuwe planned). v4.0 progress: 75% (62/83 done).
- 2026-05-20: **v4_storage_cache_001 — In-memory file cache** (gratis prestatie-upgrade): mtime-based cache in `storage.py` voor files >50KB. Knowledge_base (8MB) + graph nodes (1.2MB) + edges (7MB) worden nu maar 1× geparsd tot file mtime verandert. Cache wordt automatisch geïnvalideerd bij `save_json` of externe writes. **Gemeten winst**: vocab-endpoint 24% sneller, graph-stats 30% sneller, orphan-check 53% sneller. Diagnostics via `GET /api/admin/storage-cache` + `POST /api/admin/storage-cache/clear`. Backup-restore clear cache automatisch.
- 2026-05-20: **v4_storage_cache_002 — Cache warmup bij startup**: backend laadt KB + graph + vocab + users alvast in geheugen tijdens `@startup` (138ms, 5 files, 15.76 MB). Eerste user-request is meteen warm — geen cold-start latency meer. Log toont `🔥 Cache warmup: 5/5 files in Xms`.
- 2026-05-20: **Roadmap sync 76%**: v4.0 nu 65/86 done. Toegevoegd: warmgradatie-titels, upgrade-regels, storage cache, cache warmup.
- 2026-05-20: **v4_perf_widget_001 — Performance Card op admin dashboard** (admin-only): live cache stats (MB in geheugen, # files, file-namen + grootte) + "Cache leegmaken" knop voor debug. Fetcht `/api/admin/storage-cache`. Zichtbaar getest: 16.34 MB cached, 6 files. Non-admin (gradatie>2) ziet kaartje niet.
- 2026-05-20: **v4_wallet_cleanup_001 — Wallet test-data weggehaald**: €40 fake balance + 4 fake transactions ("genesis-deposit", "Bestelling test") verwijderd. ROAR-tokens (10) en wallet structuur behouden. Credits + activity_score op 0 (waren ook test).
- 2026-05-20: **v4_grad_growth_002 — Upgrade-pad regels gedocumenteerd**:
  - **7 → 6**: profiel-completeness ≥ 80% (10 velden: volledige naam, geboortedatum, plaats, straat, postcode, land, telefoon, nationaliteit, geslacht, noodcontact). Spark "kent" basis-info.
  - **6 → 5**: gedrag-based (oude regel, onveranderd) — 15 gesprekken + 30 dagen + trust ≥ 60
  - **5 → 4**: Roarr-token bezit ≥ 1 (wacht op v4_token_potje_001 mechaniek)
  - **4 → 3**: admin-only (jouw persoonlijke kring). Spark mag suggereren via `suggest_gradatie_promotion()` bij ≥ 50 gesprekken + trust ≥ 80
  - **3 → 2 → 1**: admin-only, geen auto-groei
  - Trust-score blijft basis voor "betrouwbaarheid + gedragsstabiliteit" zoals user beschrijft
  - 5 unit-tests groen (zie auth/service.py `check_auto_gradatie_growth`)

## In progress / backlog
### P0 / Open follow-ups
- Gradatie 2 splitsen (fam ↔ admin) → fam ziet géén Bugs-tab

### P1
- v4_dq_b: Split big components (TraderPage, UsersAdminPage, MainLayout)
- v4_014: Guard Layer (priority resolver, conflict logger, fallback hierarchy)
- v4_017: Advisor UI "Spark Inzichten" page (approve/reject analyser suggestions)
- **v4_accounting_002 — Boekhouding per user**: refactor `personal_willem` → `personal_{user_id}`. Auto-create privé-kasboek bij eerste login. Definieer rol-toegang per kasboek (system/project/business). Scheiding handhaven: Boekhouding (admin/transacties) vs Wallet (intern Spark-tegoed) vs Bank-koppeling (IBAN per user, future feature).
- **v4_kb_split_001 — KB-leak naar persons**: detector voor "X is mijn Y" zinnen in KB → migrate naar persons cards. Splitter voor double-meaning cards (Bakker = achternaam + beroep).
- **v4_snap_dedupe_001 — KB duplicates**: snap_service moet lowercase dedup doen (10 oude duplicates: vergrootglas, balk, klem, etc).

### P2
- Enkelvoud/meervoud schema voor begrippen (woord-normalisatie)
- v4_020: Chain-anchor (hide chain-of-thought to debug payload)
- v4_013b: Response Composer (Wat + Hoe)

### P3
- v4_018: Export/Import personality packs
- v6_avatar_001: Avatar-tab + verhaal-modus + ziel-verslonden mechaniek

## Key files (recent)
- `/app/backend/modules/settings/routes.py` — Settings module
- `/app/backend/modules/insights/routes.py` — vocab-from-knowledge + tags-without-card
- `/app/backend/modules/graph/__init__.py` — orphan-check + orphan-recover
- `/app/backend/modules/urgent/routes.py` — acknowledge + upcoming-spoken
- `/app/backend/modules/spark/__init__.py` — vocab/approve-growth
- `/app/backend/modules/core/storage.py` — atomic save (tmp+rename)
- `/app/backend/modules/chat/routes.py` — welcome met agenda-announce
- `/app/frontend/src/components/admin/InstellingenPage.js` — real settings API
- `/app/frontend/src/components/workspace/GesprekkenPage.js` — voice auto-start, silence detect, TTS-glow, agenda ack
- `/app/frontend/src/components/spark/SparkBrainPage.js` — "Groeien" tab (vocab/tags/orphans)
- `/app/frontend/src/components/layout/MainLayout.js` — sidebar nav ack flow

## Tech stack
React 18, FastAPI, JSON files, Bitvavo API (trade), OpenAI TTS/STT via emergentintegrations

## 2026-05-23 — KB sort-recent fix
- KB v1: `sort_by="recent"` (default) en `"updated"` nu correct geïmplementeerd in service.get_all() — sorteert op metadata.created_at / updated_at desc. Voorheen viel sort terug op file-order waardoor nieuwe kaarten "onzichtbaar" leken na opslaan.
- KB v2 inbox: sortering nu recent-aangemaakt eerst (footnote.aangemaakt_op / laatst_bewerkt_op desc), met fallback op priority + alfabetisch. Nieuwe handmatige kaart verschijnt direct bovenaan.
- KB v2 lades: sortering nu recent-bewerkt eerst i.p.v. alfabetisch.
- KB v2 "Nieuwe kaart" knop: opent de zojuist aangemaakte kaart automatisch in edit-mode in het detail-panel.
- KB v1 CreatePanel: na aanmaak schakelt automatisch terug naar "Alles" tab met sort=recent zodat de nieuwe kaart bovenaan zichtbaar is.

## 2026-05-23 — Spark World (D&D Bark MVP) + Auto-select Onbeantwoord

### Spark World MVP (v6_dnd_bark_001)
- Concept: D&D verhaal-stroom vanuit community-chat. Geen combat. User kiest een zintuig (Zie/Hoor/Voel) → typt wat hij beleeft → opgeslagen als D&D-bark-kaart.
- Backend: `/app/backend/modules/dnd/spark_world.py` (nieuw)
  - `POST /api/dnd/spark-world/start` — intro + 3 zintuig-knoppen + bestaande locked kaarten
  - `POST /api/dnd/spark-world/respond` — slaat user-input op als D&D-kaart (status: draft)
  - `POST /api/dnd/spark-world/cards/{id}/lock` — markeer kaart als canon (locked → verschijnt als keuze-knop bij volgende start)
  - `GET  /api/dnd/spark-world/cards?status=` — lijst kaarten
- 3 zintuigen + KB v2 lade-koppeling:
  - 👁️ ZIE  (cyan #06b6d4) → weten
  - 👂 HOOR (amber #f59e0b) → spreken
  - ❤️ VOEL (pink  #ec4899) → voelen
- Opslag: `/app/backend/data/cards/dnd/{card_id}.json` + `_index.json`
- Frontend: 
  - `/app/frontend/src/components/dnd/DnDBarkPanel.js` (nieuw)
  - "Spark World" knop in Community-tab (`GesprekkenPage.js`) → opent modal
  - Flow: intro → 3 zintuig-knoppen → tekst-input → opslaan → lock-knop → "Nieuwe bark" / "Klaar"
- Behavior-track: elke bark = `story_share` +1 counter, en `spark_world_card` observe-event
- Verified e2e via Playwright (login → community tab → modal → zie → bloemen → save → lock = LOCKED)

### KB v1 Auto-select Onbeantwoord (v6_kb_auto_select_unanswered)
- Bij switch naar "Onbeantwoord" tab opent de eerste onbeantwoorde kaart automatisch in de detail-modal, één keer per lijst-state. User hoeft niet door de index te scrollen.
- `/app/frontend/src/components/workspace/KennisbankPage.js` — useEffect met `autoOpenedFor` tracker zodat re-open na sluiten voorkomen wordt.

### Backlog updates
- Spark World v0.2: NPC-dialoog via Story Teller LLM, rugzak/inventory unlocks, image+audio media op bark-kaart
- D&D-kaart → KB v2 lade migratie (locked kaart automatisch in juiste lade kopiëren als kennis)
- Combat / dice-roll mechanic (later, alleen als het past)

## 2026-05-23 — D&D Galerij in Beheer + KB v2 Nieuwe-kaart venster

### D&D Galerij (v6_dnd_gallery_001)
- Locatie: **Beheer → Instellingen → Archief → Foto → "D&D Galerij"** subtab (naast Algemene foto's + Avatar Galerij)
- Toont alle Spark World bark-kaarten als grid met:
  - Filter chips: Alles / Draft / Locked (canon)
  - Per kaart: zintuig-kleur, icoon, titel, content-preview, status-badge
  - Klik kaart → detail-modal met inhoud + lock/unlock + delete (admin-only)
  - "Nieuwe D&D-kaart" → venster met leeg formulier (zintuig keuze + titel + content + "direct vastklikken" checkbox)
- Class-aanduiding: `game · D&D` (zoals user verzocht "uniek krijgen class game en D&D")
- Backend extra endpoint: `DELETE /api/dnd/spark-world/cards/{card_id}`
- Files: `frontend/src/components/admin/DnDGallerySection.js` (nieuw), `SystemArchive.js` (subtab toegevoegd)

### KB v2 Nieuwe-kaart Modal (v6_kbv2_newcard_modal_001)
- Vervangt `window.prompt()` met een echt venster (modal) met leeg in-te-vullen formulier:
  - Begrip (verplicht)
  - Laag 1 — korte uitleg (optioneel)
  - 5 lade-keuze knoppen (Inbox / Voelen / Spreken / Weten / Doen) — kaart wordt direct in juiste lade geplaatst
- Na opslaan opent kaart automatisch in bewerk-modus in detail-paneel zodat ws5/tags/media direct ingevuld kunnen worden
- File: `KennisbankV2Page.js` (NewCardModal component toegevoegd)

### Test status
- D&D Galerij + Nieuwe D&D-kaart formulier: e2e getest via Playwright (kaart aangemaakt, verschijnt in grid) ✓
- KB v2 Nieuwe-kaart venster: screenshot bevestigt leeg formulier met begrip/laag1/lade-keuze knoppen ✓

## 2026-05-23 — D&D game-cards in game.json + Boekhoud bedragen aanpasbaar

### D&D Galerij v2 (v6_dnd_gallery_002)
- Kleine zintuig+content formulier vervangen door **KB-stijl detail-paneel** (zelfde shape als KennisbankV2 detail panel)
- Velden: Begrip, Lagen 1-4, 5W (wie/wat/wanneer/waar/waarom/hoe), Tags, Media-placeholders, optioneel zintuig-kanaal
- "Mist nog" checklist + footnote (bron, vertrouwen %, locked/draft status)
- Lock/Unlock + Delete actie-knoppen
- **Aparte opslag**: `/app/backend/data/cards/dnd/game.json` (los van bark-kaarten en KB v2)
- Class = `"game"`, tag-prefix = `"D&D"` (altijd aanwezig zelfs als user tags wijzigt)
- Backend endpoints: `GET/POST/PUT/DELETE /api/dnd/spark-world/game-cards[/edit|/lock]`
- Split-view layout: lijst links + detail/edit rechts (zoals KB v2)

### KB v2 Nieuwe-kaart venster — reverted (v6_kbv2_newcard_modal_001 verwijderd)
- Geen aparte modal meer; nieuwe kaart opent direct in **bestaande detail-paneel** in edit-modus
- Window.prompt voor de begrip-naam blijft (snel en simpel), maar lagen/5W/tags/media via het detail-paneel zelf
- NewCardModal component verwijderd uit KennisbankV2Page.js

### Boekhoud — Bedragen aanpasbaar (v6_accounting_edit_001)
- Backend: nieuw `PUT /api/accounting/transactions/{tx_id}` endpoint dat amount/description/category/type/entity_id/date/btw_percentage kan wijzigen
- BTW wordt automatisch herberekend bij bedrag-update
- Frontend: per transactie-rij een **€✎ knop** naast de delete-knop; opent een prompt met huidige waarde
- Na opslaan worden kasboeken + summary auto-ververst
- Geverifieerd via PUT-test (round-trip €45 → 99.99 → 45 hersteld)

## 2026-05-24 — KB v1 → KB v2 Herzien-flow

### Herzien-knop (v6_kbv2_herzien_001)
- Naast "Verversen" in KB v2 nu paarse knop **"Herzien (KB v1)"**
- Klik → backend trekt 1 KB v1 kaart die nog niet gemigreerd is (`unanswered_first` strategy)
- Kaart opent in het bestaande NewCardInline rechter-paneel met:
  - Pre-filled begrip, lagen, ws5, tags vanuit v1
  - **Topic-veld** (alleen in herzien-modus) — stuurt auto-classify
  - Paarse banner met v1-id, "nog X te gaan", suggested auto-lade
  - "Skip → volgende" knop
- Bij **Promoveer**: backend maakt v2-kaart aan, classified naar voelen/spreken/weten/doen
  obv topic + tags keyword-mapping. V1 kaart wordt gemarkeerd met `migrated_to_v2 = true`
  + `v2_card_id` + `v2_lade` + `migrated_at`. De v2 kaart bevat footnote met
  *"Vorige versie (v1): kb-skel-..."* zodat herkomst zichtbaar blijft.

### Backend endpoints
- `GET  /api/kb/v2/herzien/next?strategy=unanswered_first|oldest|random`
- `POST /api/kb/v2/herzien/promote` — body: v1_id, begrip, lagen, ws5, tags, topic, target_lade (optioneel)
- `POST /api/kb/v2/herzien/skip`

### Topic → Lade mapping
- voelen: emotie, gevoel, relatie, verbinding, empathie, compassie
- spreken: taal, communicatie, gesprek, schrijven, praten
- weten: kennis, systeem, feit, logica, definitie, concept, model, theorie, geheugen
- doen: gedrag, actie, praktijk, uitvoeren, stap, methode, proces
- Default: weten

### Test status
- E2E getest met Playwright (5288 → 5287 → restore) ✓
- Topic "systeem" + laag 1 → correct gepromoot naar lade weten ✓
- V1 markering werkt (footnote toont "Vorige versie (v1): kb-skel-..." op v2-kaart) ✓

### Files
- `backend/modules/kb_v2/routes.py` (+ herzien endpoints + topic→lade mapping)
- `frontend/src/components/workspace/KennisbankV2Page.js` (Herzien knop, state, handlers, NewCardInline-uitbreiding)

## 2026-05-26 — Notitie edit + Avatar edit (quick wins sessie 12)

### v6_note_edit_001 — Notitie/Taak inline edit
- **Probleem**: Notities en taken konden alleen aangemaakt of verwijderd worden, niet meer bewerkt na opslaan.
- **Fix**: Pencil-knop op elke `NoteItemCard` opent inline edit-modus (titel + inhoud voor notities, alleen titel voor taken). Save → `PUT /api/notes/update/{id}?user_id=...` of `PUT /api/notes/tasks/update/{id}?user_id=...`. Backend endpoints bestonden al; alleen frontend UI ontbrak.
- **UI-extra**: Een klein `(bewerkt)` label verschijnt op een notitie zodra `updated_at` ingevuld is, met tooltip naar exact moment van laatste edit.
- **Files**: `frontend/src/components/workspace/NotitiesPage.js`
- **Backend test (curl)**: ✓ Aanmaken → update titel+inhoud → update bevestigd → delete

### v6_avatar_edit_001 — Avatar edit in Beheer→Archief→Avatar Galerij
- **Probleem**: In Beheer→Archief→Foto→Avatar Galerij was alleen toevoegen/verwijderen mogelijk; titel/tags/bot_owner wijzigen vereiste navigatie via Beheer→Gebruikers→Avatar Beheer.
- **Fix**: Bewerk-knop (pencil) op elke avatar-tile (zowel user- als system-avatars). Modal toont:
  - Titel (verplicht, alle avatars)
  - Tags (komma-gescheiden, alle avatars)
  - Bot-eigenaar (alleen system/locked avatars — leeg laten = ontkoppelen)
  Save → `PATCH /api/avatar/gallery/{id}` met `viewer_id` voor admin-guard. Verwijder-knop blijft uitsluitend op user-tab (system blijft beschermd).
- **Files**: `frontend/src/components/admin/AvatarGallerySection.js`
- **Backend test (curl)**: ✓ PATCH met nieuwe titel/tags → success, en restore werkt.

## 2026-05-26 — Glow-nav MVP live (v6_glow_nav_001)

### Wat werkt nu:
1. **Backend `/api/tabs/registry`** retourneert 23 tabs (alle frontend nav-items) met kebab-case IDs die exact matchen met `data-testid="nav-{id}"`.
2. **Backend `/api/tabs/navigate`** matcht een vrije vraag op label/id/aliases en geeft `{navigate_to, glow_target}` terug.
3. **Chat-flow integratie** (`modules/chat/routes.py`): nav-trigger detectie (`waar is/zijn`, `waar vind/kan ik`, `ga naar`, `open de/tab/mijn`, `ik wil naar`, `breng me naar`, `laat zien waar`) staat **vóór** capability-router & kbv2-router → kan niet worden opgegeten door snap/intent.
4. **Frontend `GesprekkenPage`**: bij `data.type === 'navigate_tab'` dispatcht een `window` custom event `spark:nav-glow` met `{ targetId, navigateTo, matchedTab }`.
5. **Frontend `MainLayout`**: luistert globaal naar dat event → voegt 6s pulserende amber `spark-nav-glow` CSS-class toe op de matchende sidebar-button (via `data-testid` lookup), scrollt naar het item, en roept 700ms later `onNavigate(item.id, item.path)` aan voor automatische tab-switch.
6. **CSS-keyframes** in `index.css`: `@keyframes spark-nav-pulse` met box-shadow-pulse in amber (rgba(245,158,11)).

### Visueel bevestigd met screenshot:
- *"waar is dagboek"* → Spark antwoordt "De **Dagboek**-tab vind je hier: /dagboek. Ik laat 'm even oplichten voor je." → Dagboek-button in sidebar pulseert amber → 700ms later: Dagboek-pagina opent.

### Backend-tests (curl, 9 queries):
- `waar is mijn wallet` → nav-wallet → /modules/wallet ✓
- `waar zijn mijn notities` → nav-notities → /notities ✓
- `waar vind ik de agenda` → nav-calendar → /calendar ✓
- `ga naar dagboek` → nav-dagboek → /dagboek ✓
- `open de kennisbank` → nav-knowledge-v2 → /knowledge ✓
- `breng me naar trade` → nav-trade → /modules/trade ✓
- `ik wil naar de winkel` → nav-winkel → /modules/winkel ✓
- `open de boekhouding` → nav-boekhouding → /modules/boekhouding ✓
- `hallo spark hoe gaat het` → greeting (correct, geen nav) ✓

### Files
- `backend/modules/glow_nav/__init__.py` (defaults uitgebreid 15→23 tabs + IDs gesynced)
- `backend/modules/chat/routes.py` (nav-trigger block gehoist naar boven capability-router)
- `frontend/src/components/workspace/GesprekkenPage.js` (event-dispatch)
- `frontend/src/components/layout/MainLayout.js` (event-listener + auto-navigate)
- `frontend/src/index.css` (pulse keyframes)

## 2026-05-26 — Synapse + Container architectuur (sessie 12+, F1-F7)

### 🧬 Concept (door Willem)
*"Synapslaag — Spark moet zichzelf kunnen lezen. Mappen geven zichzelf meta-data, hij hoeft het niet uit z'n hoofd te kennen. En dit container-patroon is universeel: user, shop, asset, kb_card, card_deck, chat_thread, trade_bot — alles met eigen meta + (later) eigen encryption."*

### Wat is er nu live (na sync van productie-data 2026-05-26 15:38):
1. **`_meta.json` per map** — backend/modules (50), frontend/components (12), backend/data (28). Totaal 90 containers gescand.
2. **Auto-detectie 418 endpoints** uit `@router.<verb>` decorators.
3. **SYNAPSE.json aggregator** op `/app/memory/SYNAPSE.json` — Spark's "ik weet wat ik heb".
4. **Spark leest zichzelf in chat**: 6 intents werken ("wat hebben we", "is X af", "waar woont X", "wat doet X", "lijst skeletons", "lijst verouderd").
5. **Auto-touch** in `core/storage.py` — elke save_json bumpt parent _meta.json automatisch.
6. **Container service** met universele CRUD voor user/shop/asset/card/thread.
7. **User-delete is nu bug-vrij**: container weg + cross-refs anonimiseren in bugs/community + bestanden weg uit agenda/dagboek/chat-prive.
8. **Encryption-slot in elke meta** — leeg, klaar voor F2F-feature later (geen rework).
9. **Winkelstraat hook**: shop-create → auto shop-container; shop-close → auto tag-for-deletion.
10. **UI Synapse-tab** in Beheer→Instellingen met filter, search, status-tellers, edit-modal.

### Endpoints (allemaal getest)
- `GET /api/synapse/scan` — trigger full scan + rebuild
- `GET /api/synapse/tree` — volledige boom
- `GET /api/synapse/search?q=...` — zoek in alle meta
- `GET /api/synapse/summary` — lichte stats
- `POST /api/synapse/tag` — update doel/status/footnote/blueprint/tags
- `POST /api/synapse/touch` — handmatige touch
- `POST /api/container/{type}` — create (user/shop/asset/card/thread)
- `GET /api/container/{type}` — list
- `GET /api/container/{type}/{id}/meta` — read meta
- `PATCH /api/container/{type}/{id}/meta` — update
- `POST /api/container/{type}/{id}/tag-for-deletion` — revertable
- `DELETE /api/container/{type}/{id}` — admin-only, archive + cross-ref clean

### Files
- `backend/modules/synapse/{__init__.py, schema.py, scanner.py, aggregator.py, touch.py, chat_handler.py, routes.py}`
- `backend/modules/container/{__init__.py, service.py, user_helper.py, routes.py}`
- `backend/modules/core/storage.py` (touch-hook bij save_json)
- `backend/modules/chat/routes.py` (synapse intent-router vóór capability)
- `backend/modules/winkelstraat/__init__.py` (auto shop-container hook)
- `frontend/src/components/admin/SynapseTab.js` + `InstellingenPage.js` (nieuwe tab)
- `backend/server.py` (synapse + container router-includes)

### F2F-roadmap (placeholder voor later)
Encryption-slot ligt klaar in elke `_meta.json`. Wanneer user F2F-mode activeert:
- `meta.encryption.enabled = true`
- `algorithm = "AES-256-GCM"`
- `key_holder = "user-<id>"`
- Container-data wordt encrypted at-rest, alleen user kan ontsleutelen.
- Spark systeem ziet alleen meta-shell, geen container-inhoud.

Geen rework nodig — alleen het slot vullen.

## 2026-05-26 — Synapse Auto-Enricher + KB v2 Laagsgewijs Uitleg

### Auto-enricher (v6_synapse_002)
Synapse-meta wordt nu **automatisch gevuld** met betekenisvolle `doel`-omschrijvingen:
- Leest module-level docstring uit `__init__.py` (of routes.py / service.py als fallback)
- Voor frontend: top JSDoc-blok uit eerste .js/.jsx file
- Voor data-stores: lijst van aanwezige JSON-bestanden
- **53 modules** gevuld in eerste run, **78 blueprint-stubs** aangemaakt

**Blueprint-stubs**: per module een `/app/memory/blueprints/{naam}.md` met:
- 🎯 Doel
- ✅ Wat werkt al
- 🔌 Auto-gedetecteerde endpoints
- 📝 TODO / open items
- ⚠️ Splitting-trigger (warning bij > 4 subdirs of > 10 endpoints)
- 🔐 Encryption-plan (F2F-roadmap)
- 🧬 Relaties

**Endpoint**: `POST /api/synapse/enrich`

**Effect in chat**: Spark zegt nu *"glow_nav — Glow-Nav service (v6_glow_nav_001) — Spark wijst via chat de juiste UI-tab aan"* in plaats van *"glow_nav — geen doel-omschrijving"*.

### KB v2 Laagsgewijs Uitleg (v6_kbv2_tell_layer_followup_001)
Spark's antwoorden zijn nu **gelaagd** en hebben **context-geheugen** (10 min):

```
User: "vertel kort over identiteit"
Spark: [laag1] Identiteit is het geheel van eigenschappen, kenmerken en ervaringen...

User: "vertel meer"
Spark: [laag1 + laag2] ...gebruikt om te beschrijven hoe iemand zich verhoudt...

User: "ga dieper"
Spark: [laag1 + laag2 + laag3] ...

User: "vertel volledig"
Spark: [alle 4 lagen]
```

**Triggers**:
- depth 1: `vertel kort`, `in 1 zin`, `samenvatting van`, `korte uitleg`
- depth 2: `vertel meer`, `leg uit`, `beschrijf`, `iets meer`
- depth 3: `vertel diep`, `ga dieper`, `ga dieper in`, `diep uitleg`
- depth 4: `vertel volledig`, `vertel alles over`, `alles wat je weet over`

Werkt met onderwerp ("vertel meer over identiteit") en zonder ("vertel meer" — gebruikt `session_state.last_kbv2_card_id`).

### Files
- `backend/modules/synapse/enricher.py` (auto-doel + blueprint-stubs)
- `backend/modules/synapse/routes.py` (POST /api/synapse/enrich)
- `backend/modules/kb_v2/hooks.py` (cmd_tell_layer + fallback_card_id + uitgebreide triggers)
- `backend/modules/chat/routes.py` (state.last_kbv2_card_id doorgeven aan handler)
- `/app/memory/blueprints/*.md` (78 nieuwe stubs)

## 2026-05-27/28 — Sessie 13: Roadmap-batch (P1 finish + P2 quick wins + Sessie C)

### P1 items afgemaakt
- **v6_voice_kbv2_link_001**: STT-endpoint accepteert optionele `card_id` + `user_id`. Bij meegegeven → snippet opgeslagen via `save_voice_snippet` in `/data/dialogen/voice_snippets/YYYY-MM-DD/`.
- **v6_conv_state_001**: `session_state.py` heeft `set_last_question` / `get_last_question` met 2-min expire window. Verlopen vragen worden in `get_state` auto-gefilterd.
- **v6_audit_001**: `modules/audit/__init__.py`. Endpoints `/api/audit/weak-triggers`, `/self-learning`, `/summary`. 5307 KB-entries gescand, 2239 (42%) missen laag1. Reports in `/data/system/audit_reports/`.
- **v6_perks_001**: `modules/perks/__init__.py` met 8 declarative perks. Combineert `min_gradatie + required_behaviors + blocked_by_behaviors`. Endpoints `/api/perks?user_id=...`, `/check/{perk_id}`, `/user/{user_id}`.

### P2 quick wins
- **v6_traced_rollout_001**: `@traced` op login/logout (auth) + quick_buy_potje/bot_start/bot_stop (trade).
- **v6_scheduler_001**: Background asyncio-loop elke 5 min:
  - 21:00 NL roundup-bark door Boekhouder in community
  - Madelief scant nieuwe error-logs en barkt bij errors (max 3/bark)
  - Persistent state-file `scheduler_state.json` voorkomt dubbele runs

### Sessie C — Bonus
- **v6_capabilities_handlers_002**: 5 nieuwe Spark-handen handlers (kasboek_overzicht, agenda_vandaag, kennis_inbox_status, bots_status, audit_health). 2/5 chat-matched, 3/5 wachten op intent-tuning.
- **v6_container_migrate_001**: `container/user_helper.py::migrate_user_legacy()` + bulk `migrate_all_users()`. Endpoints `POST /api/container/user/migrate` + `/migrate-all`. Kopieert legacy agenda/dagboek met footnote. Idempotent.
- **Help-per-gradatie**: bevestigd al volledig live uit eerdere sessie (32 commands, gradatie-gefilterd).

### Skip / placeholder
- **SEPA-mint**: placeholder gehouden — Tikkie-flow blijft fallback voor bank-uitcash (gebruikersbeslissing).
- **Winkelstraat frontend**: backend volledig klaar (incl. shop-container hook); UI nog niet aangepakt — heeft route+design-keuzes nodig die in volgende sessie passen.

### Files in sessie 13
- `backend/modules/audit/__init__.py` (NIEUW)
- `backend/modules/perks/__init__.py` (NIEUW)
- `backend/modules/scheduler/__init__.py` (NIEUW)
- `backend/modules/chat/session_state.py` (last_question + 2-min window)
- `backend/modules/voice/__init__.py` (STT + card_id linking)
- `backend/modules/auth/routes.py` (@traced login/logout)
- `backend/modules/trade/routes.py` (@traced bot_start/stop/quick_buy)
- `backend/modules/chat/capability_handler_service.py` (+5 handlers)
- `backend/modules/container/user_helper.py` (+migrate functies)
- `backend/modules/container/routes.py` (+migrate endpoints)
- `backend/server.py` (audit + perks routers + scheduler startup)
- `backend/data/system/command_registry.json` (+5 capabilities)

## 2026-05-28 — Trader Fix (na vraag van Willem)

### v6_trade_minorder_001 — SOL min-buy crash fix
- Probleem: Bitvavo eist `minimumOrderInQuoteAsset` per markt (SOL/BTC/ETH ≈ €5). Bij €1-2 trades → cryptische error.
- Fix: `get_market_min_quote(market)` met 1u cache van `/v2/markets`. Pre-check bij BUY → friendly error met tip.
- Fallback-tabel voor offline cache: BTC/ETH/SOL/ADA/XRP/BCH = €5.

### v6_trade_sell_balance_001 — Sell balance mismatch fix
- Probleem: potje toonde X tokens, maar Bitvavo had iets minder door rounding/fees → sell crashte op "insufficient balance".
- Fix: voor SELL fetch eerst actuele Bitvavo balance via `fetch_bitvavo_balance`. Clamp `min(requested, actual) * 0.999`.
- Errors hebben nu `error_code`: `MIN_QUOTE`, `NO_BALANCE`, `ZERO_AFTER_CLAMP`, `BITVAVO_HTTP_ERROR`, `EXCEPTION`.
- Trade-record bevat `requested_amount` + `effective_amount` voor traceability.

### Test status
- Preview: unit-test bevestigt min-quote fallback werkt (€1 SOL-buy → MIN_QUOTE error met tip).
- Productie: testen na redeploy. Sell-balance pre-check vereist live Bitvavo credentials.

### Files
- `backend/modules/trade/monitor.py` (helper + buy/sell pre-checks + error-codes)

## 2026-05-28 — Sessie 13b: Potjes €10 + Pot 1 Staking + Trader Help + UI fixes

### v6_potje_size_10_001 — Potjes van €10
- `START_AMOUNT 5.08 → 10.0` (was eigenaardige opstart-waarde, nu schoon).
- Admin-endpoint `POST /api/trade/potjes/{user_id}/resize-to-default` zet alle potjes op €10. Faalt veilig bij open posities.

### v6_pot1_staking_lock_001 — Pot 1 staking-lock
- Eerste potje (laagste index OF eerste in lijst) krijgt `pot_locked=True, lock_reason="staking_anchor"`.
- `find_available_potje` skipt locked potjes (zowel monitor-bot als quick-buy).
- Backfill robuust: vindt eerste potje ook in legacy data zonder `index`-veld (productie-data).
- Toggle endpoint `POST /api/trade/potjes/{user_id}/toggle-lock` met body `{pot_id, locked, lock_reason}`.

### v6_trade_help_001 — Trader Help
- `modules/trade_help/__init__.py` — 7 secties:
  1. Het potjes-systeem (€10 elk + Pot 1 staking)
  2. BUY-logica (dip-detectie, min-quote check, cycle-lock)
  3. SELL-logica (trailing stop, balance-pre-check, force-sell)
  4. Modes & Knoppen (Monitor/Stop/QuickBuy/Force-sell/Resize)
  5. Veiligheid & Limieten (operatorId, token-gate, trade-history)
  6. Spark's stem in de trades (Boekhouder + Madelief)
  7. Tips
- Endpoints `GET /api/trade/help` (volle JSON) + `/markdown` (één string).
- Chat-router pakt triggers ("hoe werkt de trader/bot/potjes?") en plakt eerste 3 secties + deep_link.

### v6_wallet_button_order_001 — Wallet knop-volgorde
- Volgorde: **Storten** (+) → **Opnemen** (−) → [**Mint** admin] → **Gift** (rechts).

### v6_roar_price_display_001 — ROAR-prijs uitleg
- WinkelPage text: "1 ROAR = aandeel in Spark Core kapitaal".
- Tooltip toont formule: `€{spark_core} ÷ {circulating} = €{prijs}`.
- "Jouw tokens" → "Jouw bezit", "Waarde" → "Tegen huidige prijs".

### v6_traced_rollout_002 — @traced overige
- `shop/gift.py`: `create_gift`, `accept_gift`.
- `kb_v2/routes.py`: `classify`, `edit`, `delete_card`.

### Files
- `backend/modules/trade/potjes.py` (potje €10 + lock + resize)
- `backend/modules/trade/routes.py` (resize + toggle-lock endpoints)
- `backend/modules/trade_help/__init__.py` (NIEUW)
- `backend/modules/chat/routes.py` (trader-help intent)
- `backend/modules/shop/gift.py` (@traced)
- `backend/modules/kb_v2/routes.py` (@traced)
- `backend/server.py` (trade_help router include)
- `frontend/src/components/modules/WalletPage.js` (knop-volgorde)
- `frontend/src/components/modules/WinkelPage.js` (prijs-uitleg)

### Testing
- Backend lint: all checks passed
- Pot 1 auto-locked op productie-data (Willem): bevestigd
- Resize endpoint blokkeert bij open posities: bevestigd
- Chat "hoe werkt de bot?" → `type=trader_help`: bevestigd
- Wallet UI screenshot: knop-volgorde Storten→Opnemen→Gift correct (rechts)
