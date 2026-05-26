"""
Synapse module (v6_synapse_001) — Spark's zelf-lezende synapslaag
==================================================================
Concept (door Willem):
  > "synapslaag — Spark moet zichzelf kunnen lezen. mappen geven zichzelf
  >  meta-data, hij hoeft het niet uit zijn hoofd te kennen."

Architectuur (3 lagen):
  1. _meta.json per map (backend/modules, frontend/components, backend/data)
     → zegt: wat ben ik, wat is mijn doel, status, last_touched, blueprint, footnote
  2. /app/memory/SYNAPSE.json (aggregator, root-level)
     → boomstructuur van alle _meta.json, snel doorzoekbaar
  3. Container-patroon (F4, separate module `modules/container/`)
     → user/shop/asset/kb_card/card_deck — alles met eigen _meta.json
        Bij delete: hele container weg + cross-refs anonimiseren.
        Encryption-slot reeds in schema voor F2F later.

Files in deze module:
  - schema.py         : Meta schema-definitie + helpers
  - scanner.py        : Walk-scanner die _meta.json genereert/bijwerkt
  - aggregator.py     : Bouwt SYNAPSE.json uit alle _meta.json
  - touch.py          : `touch_meta()` helper voor F3 auto-touch
  - routes.py         : FastAPI endpoints (/api/synapse/*)

Routes:
  - GET  /api/synapse/scan          : trigger volledige scan + rebuild aggregator
  - GET  /api/synapse/tree          : returnt SYNAPSE.json
  - GET  /api/synapse/search?q=...  : zoek in alle meta-records
  - POST /api/synapse/tag           : tag een container (active/wip/deprecated/...)
  - POST /api/synapse/touch         : handmatig touch (markeer aangeraakt)
"""
from .routes import router  # noqa: F401
