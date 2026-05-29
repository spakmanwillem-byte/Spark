"""
v6_spark_world_north_001 — Spark World: The North (Groningen base)
==================================================================

Statische lore-laag bovenop spark_world.py.

The North is de eerste vaste 'plaats' in Spark World — geïnspireerd op
Willem's basis in Groningen. Het bevat:
  - hoofd-locatie metadata (naam/sfeer/zintuigen)
  - sub-locaties (De Werkplaats, De Tuin, etc.)
  - NPC-stubs (kunnen later linken aan echte persoonskaarten)
  - 'travel_to' API zodat een Spark World sessie hier kan starten

Locaties zijn opgeslagen in /data/dnd/spark_world/locations.json zodat
ze persistent zijn én later via UI bewerkbaar. Bij eerste opstart
wordt The North uit de seed hieronder geladen.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from modules.core.storage import load_json, save_json


router = APIRouter(prefix="/dnd/spark-world/locations", tags=["dnd-spark-world-locations"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
LOCATIONS_FILE = DATA_ROOT / "dnd" / "spark_world" / "locations.json"


# ---------------------------------------------------------------------------
# Seed: The North (Groningen)
# ---------------------------------------------------------------------------
SEED_LOCATIONS: List[Dict] = [
    {
        "id": "north",
        "naam": "The North",
        "subtitle": "Groningen base — Willem's thuis",
        "icon": "🌲",
        "color_primary": "#10b981",     # emerald — bos / noord
        "color_secondary": "#f59e0b",   # amber — kampvuur / warmte
        "biome": "noordelijk vlakland · windrijk · stenen huizen · grachten",
        "tagline": "Waar het allemaal begint. Wind, stenen huizen, en stilte tussen de geluiden.",
        "intro": (
            "Je staat in The North.\n\n"
            "De wind komt van de zee, ruikt naar regen en oud hout. "
            "Achter je: een rij smalle huizen met blauwe deuren. "
            "Voor je: een open plein, een fiets tegen een lantaarn, "
            "ergens slaat een klok.\n\n"
            "Wat trekt jouw aandacht?"
        ),
        "senses_hint": {
            "zie": "Bakstenen huizen, grachten, fietsen, lage wolken.",
            "hoor": "Wind door bomen, fietsbel in de verte, klokken die kwart slaan.",
            "voel": "Koele lucht op je gezicht, gewicht van tijd, vertrouwd."
        },
        "sub_locations": [
            {
                "id": "north_werkplaats",
                "naam": "De Werkplaats",
                "icon": "🔧",
                "desc": "Willem's atelier. Code, kabels, koffievlekken op het bureau. Hier ontstaat Spark.",
                "tags": ["code", "build", "spark-core"],
                "vibe": "creatief · geconcentreerd · warm-licht",
            },
            {
                "id": "north_tuin",
                "naam": "De Tuin",
                "icon": "🌿",
                "desc": "Achter het huis. Plek waar dingen mogen groeien zonder dat je ze pusht.",
                "tags": ["rust", "groei", "natuur"],
                "vibe": "kalm · seizoenen voelbaar",
            },
            {
                "id": "north_studio",
                "naam": "De Studio",
                "icon": "🎙️",
                "desc": "Microfoon, koptelefoon, stem-opnames. Spark luistert hier mee.",
                "tags": ["stem", "podcast", "tts"],
                "vibe": "stil · gefocust · oren-open",
            },
            {
                "id": "north_kampvuur",
                "naam": "Het Kampvuur",
                "icon": "🔥",
                "desc": "Centrale plek voor verhalen. NPCs verzamelen hier 's avonds.",
                "tags": ["community", "verhalen", "ontmoeting"],
                "vibe": "warm · open · gedeeld",
            },
        ],
        "npc_stubs": [
            {
                "id": "npc_de_dood",
                "naam": "De Dood",
                "rol": "Reflectie & afsluiten",
                "appears_at": ["north_kampvuur"],
                "color": "#0f172a",
                "linked_bot_id": "bot-dood",
            },
            {
                "id": "npc_boekhouder",
                "naam": "De Boekhouder",
                "rol": "Cijfers & weekrapport",
                "appears_at": ["north_werkplaats"],
                "color": "#f59e0b",
                "linked_bot_id": "bot-boekhouder",
            },
        ],
        "world_rules": [
            "Geen gevechten. Geen levens. Alleen wat jij meebrengt.",
            "Elke locatie heeft eigen sfeer — kies bewust waar je heen gaat.",
            "NPCs reageren op wat je deelt, niet op stats.",
        ],
        "created_at": "2026-05-29T00:00:00+00:00",
        "is_seed": True,
    },
]


def _ensure_locations() -> Dict:
    """Idempotent: laadt locations.json; seed The North als nog leeg."""
    data = load_json(LOCATIONS_FILE, default={"locations": []})
    have_ids = {loc.get("id") for loc in data.get("locations", [])}
    changed = False
    for seed in SEED_LOCATIONS:
        if seed["id"] not in have_ids:
            data["locations"].append(seed)
            changed = True
    if changed:
        LOCATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        save_json(LOCATIONS_FILE, data)
    return data


def _find_location(loc_id: str) -> Optional[Dict]:
    data = _ensure_locations()
    return next((loc for loc in data["locations"] if loc.get("id") == loc_id), None)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("")
async def list_locations():
    """Alle Spark World locaties (seed + door admin toegevoegd)."""
    data = _ensure_locations()
    # Lichte payload voor lijst-view
    light = [
        {
            "id": loc.get("id"),
            "naam": loc.get("naam"),
            "subtitle": loc.get("subtitle"),
            "icon": loc.get("icon"),
            "color_primary": loc.get("color_primary"),
            "tagline": loc.get("tagline"),
            "sub_locations_count": len(loc.get("sub_locations", [])),
            "npc_count": len(loc.get("npc_stubs", [])),
        }
        for loc in data.get("locations", [])
    ]
    return {"success": True, "locations": light, "total": len(light)}


@router.get("/{location_id}")
async def get_location(location_id: str):
    """Volledige location-details inclusief sub-locaties + NPCs."""
    loc = _find_location(location_id)
    if not loc:
        return {"success": False, "error": f"Location '{location_id}' niet gevonden"}
    return {"success": True, "location": loc}


class TravelBody(BaseModel):
    user_id: str = "user-001"
    location_id: str
    sub_location_id: Optional[str] = None


@router.post("/travel")
async def travel_to(body: TravelBody):
    """Markeer dat user 'reist' naar een location. Returnt de intro-tekst
    + senses-hints + relevante NPCs voor deze plek. Idempotent (geen
    state-mutaties, alleen lezen).
    """
    loc = _find_location(body.location_id)
    if not loc:
        return {"success": False, "error": f"Location '{body.location_id}' niet gevonden"}

    response = {
        "success": True,
        "user_id": body.user_id,
        "location_id": loc["id"],
        "naam": loc["naam"],
        "subtitle": loc.get("subtitle"),
        "intro": loc.get("intro"),
        "senses_hint": loc.get("senses_hint", {}),
        "color_primary": loc.get("color_primary"),
        "world_rules": loc.get("world_rules", []),
        "npc_stubs": loc.get("npc_stubs", []),
        "arrived_at": datetime.now(timezone.utc).isoformat(),
    }

    if body.sub_location_id:
        sub = next((s for s in loc.get("sub_locations", []) if s.get("id") == body.sub_location_id), None)
        if sub:
            response["sub_location"] = sub
            response["intro"] = f"{response['intro']}\n\n— Je gaat naar {sub['naam']}.\n{sub.get('desc', '')}"

    return response
