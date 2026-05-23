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
- [ ] **Spark's hands** capability hookup naar live chat — `intent_matcher_service` is gebouwd, moet nog gekoppeld aan `/chat/message` route

### P1 — Aanstaande
- [ ] **Kennisbank v2 / D&D Kaarten integratie** — herontwerp: kennis-kaarten als grondvorm voor D&D-content (lore, items, inventory). Edit-in-bot moet behouden blijven
- [ ] **Self-learning audit (B5)** — verificatie dat shadow learning modules correct loggen
- [ ] **D&D Perks & Unlocks** — backend logic om Aura-gebaseerde feature-gates af te dwingen
- [ ] **D&D Lore indexering** — `lore_index.json` expanderen voor dynamic theming

### P2 — Backlog
- [ ] **ROAR-gift encryption-at-rest** — sender/recipient pairs privacy-gevoelig
- [ ] **SEPA-mint koppeling** voor ROAR economy v2 (uitcash naar bank)
- [ ] **Auto-expire archive tab** voor pending gifts (na 24h naar archive ipv puur expired-status)
- [ ] **Boekhouder dagelijkse roundup-bark** (21:00 samenvatting in community)
- [ ] **Krachtigere log-search**: full-text zoeken over alle modules op een dag

### P3 — Future / Experimenteel
- [ ] **Dynamic theming** via `lore_index.json` (kleuren shiften met seizoen/lore)
- [ ] **Krachtigere "spark's eigen anker"** — Spark kan eigen notities maken die over sessies heen bestaan

## 🧠 Architectuur principes (don't forget)

1. **NO MONGODB**: alle data via `load_json`/`save_json` uit `modules.core.storage`
2. **DSP-tags**: 2-JSON sync issues moeten gedocumenteerd in `ARCHITECTURE.md` (DSP-001 t/m DSP-006 actief)
3. **Nederlands**: alle UI-tekst en log-intents in het Nederlands
4. **data-testid**: elk interactief element heeft een uniek testid (kebab-case)
