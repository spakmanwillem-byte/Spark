"""v14_ttss_001 (Willem 19-10-2026) — Spark spreekt met Willems eigen ingesproken kaarten.

GET /api/kb/v2/voice/map      → {woorden: {begrip_lower: voice_url}, geluiden: {begrip_lower: url}}
GET /api/kb/v2/voice/missing  → kaarten zonder inspraak (voor de 🎙️-filter in de Kennisbank)
Alleen `media.voice_url` telt als inspraak; `media.extra_audio` zijn geluiden (gtss).
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, Query

from . import service

router = APIRouter(prefix="/kb/v2/voice", tags=["kb-v2-voice"])


def _voice(c: Dict) -> Optional[str]:
    m = c.get("media")
    return (m or {}).get("voice_url") if isinstance(m, dict) else None


def _sound(c: Dict) -> Optional[str]:
    m = c.get("media")
    extras = (m or {}).get("extra_audio") if isinstance(m, dict) else None
    for e in extras or []:
        if e.get("url"):
            return e["url"]
    return None


@router.get("/map")
async def voice_map():
    woorden: Dict[str, str] = {}
    geluiden: Dict[str, str] = {}
    for c in service._all_cards_with_lade():
        if c.get("_lade") == "inbox":
            continue
        key = (c.get("begrip") or "").strip().lower()
        if not key:
            continue
        v = _voice(c)
        if v:
            woorden[key] = v
        s = _sound(c)
        if s:
            geluiden[key] = s
    return {"success": True, "woorden": woorden, "geluiden": geluiden,
            "count_woorden": len(woorden), "count_geluiden": len(geluiden)}


@router.get("/missing")
async def voice_missing(lade: str = Query("", description="leeg = alle lades"),
                        limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
                        search: str = ""):
    per_lade: Dict[str, Dict[str, int]] = {}
    missing: List[Dict] = []
    q = search.strip().lower()
    for c in service._all_cards_with_lade():
        ld = c.get("_lade")
        if ld == "inbox":
            continue
        st = per_lade.setdefault(ld, {"totaal": 0, "ingesproken": 0, "niet": 0})
        st["totaal"] += 1
        if _voice(c):
            st["ingesproken"] += 1
            continue
        st["niet"] += 1
        if lade and ld != lade:
            continue
        if q and q not in (c.get("begrip") or "").lower():
            continue
        missing.append({"id": c["id"], "begrip": c.get("begrip"), "lade": ld,
                        "tags": (c.get("tags") or [])[:4],
                        "lagen": {"laag1": ((c.get("lagen") or {}).get("laag1") or "")[:90]}})
    missing.sort(key=lambda x: (x["begrip"] or "").lower())
    return {"success": True, "total": len(missing), "offset": offset, "limit": limit,
            "kaarten": missing[offset:offset + limit], "per_lade": per_lade}
