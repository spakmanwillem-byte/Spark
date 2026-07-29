"""v11_spark_index_001 — Spark's zelfbewuste bestand/map-teller.

Bouwt een index van alle mappen/bestanden/modules met aggregatie van
`_meta.json` footnotes. Fastpath voor "hoeveel bestanden/mappen" vragen.
"""
from .routes import router, build_index, read_index

# v11_spark_index_001 — Auto-rebuild bij startup (idempotent, ~200ms)
try:
    build_index()
except Exception as _e:
    print(f"[spark_index] startup index-build failed: {_e}")

__all__ = ["router", "build_index", "read_index"]

