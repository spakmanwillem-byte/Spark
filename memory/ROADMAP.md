# Spark Core 2.0 — Engineering Practices & Backlog

> **Zie ook**: `MISSION.md` voor missie/visie/identiteit/privacy (DNA-laag).

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
- [ ] **Spark's hands** capability hookup naar live chat — `intent_matcher_service` is gebouwd, moet nog gekoppeld aan `/chat/message` route (gedeeltelijk: kbv2-commands werken al, generic intent-router ontbreekt nog)
- [ ] **Boekhouder closing-flow** ("terlens-terug-boek") — aan eind van trade-cyclus: saldo + winst + fees + token-mints in 1 boeking. Nu open-eindjes in `accounting/`

### P1 — Aanstaande (deze maand)
- [ ] **KB v2 → Vocab register hook implementeren** (zie `modules/kb_v2/hooks.py::register_in_vocab`)
  - Bij elke `classify_card()` → schrijf begrip naar `/data/personality/spark_vocab.json`
  - spark_brain mag alleen `active=true` vocab spontaan gebruiken
- [ ] **KB v2 → Chat-commands handlers afmaken** (`hooks.py::cmd_tell_layer`)
  - "vertel kort" → laag1, "vertel meer" → laag2, "vertel diep" → laag3/4
  - Sla `last_kbv2_card_id` op in session_state voor follow-up vragen
- [ ] **KB v2 → Auto-graph (verbanden)** (`hooks.py::compute_verbanden`)
  - Periodieke job (1x/dag): vind top-5 related cards via shared tags
  - UI: "Gerelateerd:" sectie in CardDetail
- [ ] **KB v2 → D&D Kaarten integratie** (`hooks.py::link_to_dnd`)
  - Optionele `dnd` veld in card-schema (type/trigger/unlocks)
  - lore_index synct van v2-cards met `dnd.type == "lore"`
- [ ] **KB v2 → Dialogen voice-snippet auto-save** (`hooks.py::save_voice_snippet`)
  - Bij elke Whisper-transcriptie → /data/dialogen/voice_snippets/YYYY-MM-DD/
  - Spark's gesprek-stijl groeit mee met Willem's stem
- [ ] **ConversationStateManager terug uit v1** — 2-min `last_question` per session
- [ ] **AuditService weak-trigger scan** (uit v1) — vind triggers met <10-char responses
- [ ] **Self-learning audit (B5)** — verificatie dat shadow learning modules correct loggen
- [ ] **D&D Perks & Unlocks** — backend logic om Aura-gebaseerde feature-gates af te dwingen

### P2 — Volgend kwartaal
- [ ] **`@traced` uitrol** — auth.login/logout, trade.bot_start/stop/quick_buy_potje, shop.gift.*, dnd.observe, KB mutations
- [ ] **Identity 3-lagen-enforcement** in seed-data (CR-001/002/003 als code-wet ipv alleen doc)
- [ ] **ROAR-gift encryption-at-rest** — sender/recipient pairs privacy-gevoelig
- [ ] **SEPA-mint koppeling** voor ROAR economy v2 (uitcash naar bank)
- [ ] **Auto-expire archive tab** voor pending gifts (na 24h naar archive)
- [ ] **Boekhouder dagelijkse 21:00 roundup-bark** in community
- [ ] **ReplayLogService uit v1** — trade backtest met run_id replay
- [ ] **Spark "merkt eigen errors"** — log-watcher: elk `error`-record → bark in community

### P3 — Future / Experimenteel
- [ ] **Dynamic theming** via `lore_index.json` (kleuren shiften met seizoen/lore)
- [ ] **Krachtigere "spark's eigen anker"** — Spark maakt eigen notities die over sessies heen bestaan
- [ ] **ROAR-token reward per geclassificeerde kaart** (gamification Inbox doorlopen)
- [ ] **Krachtigere log-search** — full-text zoeken over alle modules op een dag
- [ ] **Boekhouder closing-flow** uitgebreid met PDF-export per maand

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
| `modules/kb_v2/hooks.py` | ✅ Created sessie 5 | KB v2 → Vocab/Commands/Graph/D&D/Dialogen koppeling |

Nieuwe hooks volgens dit pattern toevoegen voor:
- `modules/trade/hooks.py` — closing-flow + replay + auto-snapshot triggers
- `modules/dnd/hooks.py` — lore-card sync, perk-trigger, aura-gates
- `modules/spark/hooks.py` — Spark's hands (intent_matcher generic router)

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
