"""v14_emotie_veld_001 (Willem 19-10-2026) — emotie als bevestigde eigenschap op de KB-kaart.

GET /api/kb/v2/emotie/missing → kaarten zonder `emotie_bevestigd` (+ suggestie uit tag/veld, per_lade-tellers)
GET /api/kb/v2/emotie/stats   → tellers per lade + per emotie (bevestigd)
Zetten gaat via het bestaande /api/kb/v2/edit met updates {"emotie": "..."} (service.edit_card).
'neutraal' is een echte waarde, geen default: alleen een door Willem bevestigde keuze telt.
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, Query

from . import service

router = APIRouter(prefix="/kb/v2/emotie", tags=["kb-v2-emotie"])

EMOTIES = ("blij", "boos", "bang", "bedroefd", "neutraal")


def suggestie(c: Dict) -> Optional[str]:
    """Niet-bevestigde hint: eerst emotie-tag (bewust gezet), anders importer-veld."""
    tags = {str(t).lower().strip().lstrip("#") for t in (c.get("tags") or [])}
    for t in tags:
        for e in EMOTIES:
            if t in (f"emotie-{e}", f"emotie {e}"):
                return e
    if "emotie" in tags:
        for e in EMOTIES:
            if e in tags:
                return e
    v = (c.get("emotie") or "").lower().strip()
    return v if v in EMOTIES else None


def _stats(cards: List[Dict]) -> Dict:
    per_lade: Dict[str, Dict[str, int]] = {}
    per_emotie = {e: 0 for e in EMOTIES}
    for c in cards:
        st = per_lade.setdefault(c["_lade"], {"totaal": 0, "bevestigd": 0, "niet": 0})
        st["totaal"] += 1
        if c.get("emotie_bevestigd"):
            st["bevestigd"] += 1
            if c.get("emotie") in per_emotie:
                per_emotie[c["emotie"]] += 1
        else:
            st["niet"] += 1
    return {"per_lade": per_lade, "per_emotie": per_emotie}


@router.get("/stats")
async def emotie_stats():
    cards = [c for c in service._all_cards_with_lade() if c.get("_lade") != "inbox"]
    return {"success": True, **_stats(cards), "emoties": list(EMOTIES)}


@router.get("/missing")
async def emotie_missing(lade: str = Query(""), limit: int = Query(100, ge=1, le=500),
                         offset: int = Query(0, ge=0), search: str = ""):
    cards = [c for c in service._all_cards_with_lade() if c.get("_lade") != "inbox"]
    q = search.strip().lower()
    missing: List[Dict] = []
    for c in cards:
        if c.get("emotie_bevestigd"):
            continue
        if lade and c["_lade"] != lade:
            continue
        if q and q not in (c.get("begrip") or "").lower():
            continue
        full = {k: v for k, v in c.items() if k != "_lade"}
        full["lade"] = c["_lade"]
        full["emotie_suggestie"] = suggestie(c)
        missing.append(full)
    missing.sort(key=lambda x: (x.get("begrip") or "").lower())
    return {"success": True, "total": len(missing), "offset": offset, "limit": limit,
            "kaarten": missing[offset:offset + limit], **_stats(cards), "emoties": list(EMOTIES)}
