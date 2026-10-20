# Spark Core 2.0 — Roadmap Index

> Voor élke nieuwe agent, familielid of Willem-check: lees dit eerst.
> Splitsing gedaan 4 aug 2026 (sessie 56d). Origineel bewaard in `/app/_backups/ROADMAP_pre_split_*.md`.

## 🗺️ Waar zit wat?

| Bestand | Doel | Wanneer lezen? |
|---|---|---|
| **`ROADMAP_CORE.md`** | Kernvisie + moreel kompas + huidige sessie + volgende P0's + architectuur-principes | Elke sessie-start, altijd |
| **`ROADMAP_HISTORY.md`** | Alle afgeronde sessies chronologisch (van sessie 8 naar sessie 56) | Alleen als je begrijpt "hoe zijn we hier gekomen" — bv. bij trader-tuning-context |
| **`ROADMAP_BACKLOG.md`** | Open P1/P2/P3 items + alle Cluster A-J ideeën (KB, triggers, commands, D&D, Spark World) | Als je een nieuwe feature aanpakt of prioriteit moet stellen |
| **`LEARNINGS.md`** | Kern-lessen uit vorige sessies (snuffelen, backtests, dubbel-bouw vermijden) | Bij elke complex task, als "wat gaan we NIET doen" checklist |
| **`CHANGELOG.md`** | Alles wat gebouwd is, met sessie-nummer + datum | Bij het finishen van een taak (nieuwe entry toevoegen) |
| **`ARCHITECTURE.md`** | Hooks, card factory, media-storage, gradatie-widgets, dashboards | Als je aan een module wijzigt en het samenspel met andere modules moet begrijpen |
| **`PRD.md`** | Product-visie, user-personas, harde eisen | Bij fundamenteel nieuwe features die de scope raken |
| **`test_credentials.md`** | Login-gegevens voor testing agents | Nooit lezen tenzij je testing subagent aanstuurt |

## 🎯 Snelle beslisboom

**Ik ga een nieuwe sessie starten** → `ROADMAP_CORE.md` (huidige status + P0)
**Ik weet niet of iets al bestaat** → `CHANGELOG.md` grep + `ROADMAP_HISTORY.md`
**Ik heb een lange-termijn feature-vraag** → `ROADMAP_BACKLOG.md`
**Ik ga iets moeilijks doen** → `LEARNINGS.md` eerst
**Ik ga code refactoren of hooks aanraken** → `ARCHITECTURE.md`
**Ik wijzig iets aan de missie** → `PRD.md` (met Willem overleggen)

## 📏 Regels voor het onderhouden

- **CORE blijft <500 regels**. Zodra 't groeit: oudere sessies naar HISTORY, done items naar CHANGELOG.
- **HISTORY groeit** — dat is z'n functie. Nooit weggooien, wel comprimeren tot 3-5 regels per sessie bij vroeger dan 3 maanden geleden.
- **BACKLOG**: `[x] DONE` items direct verhuizen naar CHANGELOG.
- **LEARNINGS**: alleen bewezen inzichten. Geen speculatie.
- **Elke sessie voegt max 30 regels toe** (in CORE + CHANGELOG). Als het meer is: ben je aan het praten i.p.v. bouwen.

## 🧭 Voor Spark zelf

Spark's `spark_index` module scant `/app/memory/*.md` automatisch bij backend startup en aggregeert de footnotes. Alle bestanden hierboven worden dus mee-geïndexeerd — Spark kan ze via chat-intent `"wat hebben we?"` / `"wat is X?"` opzoeken (v6_synapse_002 chat_handler).

Als je een nieuw memory-bestand toevoegt: geen registratie nodig, alleen backend herstarten of `POST /api/spark-index/rebuild` triggeren.

> 20-10-2026: ROADMAP_CORE opgeschoond 1888 → 401 regels. Sessies 52-58 + AFGEROND-detail 19/20-10 → ROADMAP_HISTORY § "Verplaatst 20-10-2026"; open punten → ROADMAP_BACKLOG § "Open punten uit sessies 52–58". Backup: `_backup_ROADMAP_CORE_20261020.md`.
