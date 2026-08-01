# Productie-sync handoff — 2026-05-25 21:11

## Achtergrond
Willem heeft direct na de deploy een volledige productie-backup geüpload als
handoff naar de volgende sessie. Bestand ligt op:

  /app/_uploads/spark_backup_full_20260525_210547.zip   (198 MB · 362 files)

## Wat zit erin
- `backend/data/**` — volledige productie-state (KB v2, accounting, archief, etc.)
- `memory/*.md` — laatste versies van PRD, ROADMAP, MISSION, ARCHITECTURE
- `spark_backup_manifest.json` (top-level) — index van wat erin zit

## Wat WEL nieuw is in productie (vs huidige preview)
Productie-data is **na** onze KB v2 hooks-landing gemaakt (zip-timestamp 21:05,
ná onze backfill op 15:19). Productie heeft dus:
- ✅ Onze 5 hooks + footnote.hooks_fired trail
- ✅ De backfill van 5318 kaarten met verbanden/vocab
- ➕ Mogelijk **nieuwe** community messages / archive uploads / trades
  die Willem ná onze sessie heeft gedaan

## Wat preview MIST en sync nodig heeft (vermoedelijk)
- Eventuele nieuwe community-berichten ná 15:37
- Eventuele archive-uploads (foto/geluid/filmpje) ná 09:50
- Eventuele trades / kasboek-mutaties ná onze laatste run

## Aanbevolen sync-strategie (volgende sessie)
1. Maak backup van huidige preview-data:
     cp -r /app/backend/data /app/_uploads/preview_data_pre_sync_$(date +%Y%m%d_%H%M)
2. Unzip productie-backup naar tmp:
     unzip -q /app/_uploads/spark_backup_full_20260525_210547.zip -d /tmp/prod_sync
3. **Selectief mergen** — NIET blind overschrijven, omdat preview de hooks-landing heeft.
   Specifiek:
   - `community/messages.json` — productie overschrijft (Willem's live chat)
   - `system_archive/*` — merge (nieuwe files toevoegen, _index.json regenereren)
   - `accounting/`, `wallets/`, `roar/` — productie overschrijft (live finance)
   - `knowledge/v2/*` — **NIET overschrijven** (preview heeft hooks_fired + verbanden;
     productie zou kunnen overschrijven; eerst diff maken)
   - `memory/*.md` — productie overschrijft (heeft laatste PRD/ROADMAP)
4. Herstart backend en draai backfill-hooks opnieuw op kbv2 als productie-data nieuwe
   kaarten bevat zonder hooks_fired.

## Bug-noot (genoteerd door Willem in sessie 11)
- KB v2 onbruikbare kaarten kunnen niet verwijderd worden (bugs.json id staat klaar)
- 3 Bijbel-kaarten compleet voor toekomstig Spark World v2 / D&D
