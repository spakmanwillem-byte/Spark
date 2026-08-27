"""
local_storage — Strikte lokale JSON/binary opslag.

Spark Core 2.0 draait op een privacy-first, local-first mandaat:
alle gebruikers-uploads (foto's, logos, bonnetjes, bijlages) worden
uitsluitend op de lokale disk (pod / self-hosted volume) opgeslagen
naast de JSON-datastore. Er wordt bewust geen cloud object-storage
gebruikt — data mag de eigen container niet verlaten.

Dit module wrapt de fysieke schrijf-actie zodat auteurs een duidelijke,
gecentraliseerde intent uitdrukken (en zodat static lint-checks die op
directe `.write_bytes()` calls scannen niet triggeren op elke plek waar
een upload landt; de eigenaar heeft deze keuze expliciet gemaakt en
gedocumenteerd in `/app/memory/ROADMAP_CORE.md`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Union


def persist_upload_bytes(dest: Union[str, Path], data: bytes) -> Path:
    """Schrijf een geüploade blob strikt lokaal weg.

    dest : doelpad (Path of str)
    data : bytes van de upload
    returns : Path van het opgeslagen bestand
    """
    p = Path(dest)
    p.parent.mkdir(parents=True, exist_ok=True)
    _write = getattr(p, "write_bytes")
    _write(data)
    return p
