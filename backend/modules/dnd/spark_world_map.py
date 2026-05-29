"""
Spark World Map locations (v6_spark_world_map_001)

Globale (shared) NL-map locaties voor de SPARK WORLD mini-map.
Admin kan locaties slepen en de posities worden persistent opgeslagen.

JSON: /app/backend/data/dnd/spark_world_map.json
{
  "locations": [
    {"id": "stormhaven", "x": 78, "y": 18, "label": "Stormhaven", "fractie": "Spark", "isMain": true, "fractie_card_id": null},
    ...
  ],
  "updated_at": "ISO",
  "updated_by": "user-001"
}
"""
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/dnd/spark-world/map", tags=["dnd-spark-world-map"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
MAP_FILE = DATA_ROOT / "dnd" / "spark_world_map.json"
USERS_FILE = DATA_ROOT / "system" / "users.json"

DEFAULT_LOCATIONS = [
    {"id": "stormhaven", "x": 78, "y": 18, "label": "Stormhaven", "fractie": "Spark", "isMain": True,  "fractie_card_id": None},
    {"id": "loc-2",      "x": 60, "y": 32, "label": "—",          "fractie": "",      "isMain": False, "fractie_card_id": None},
    {"id": "loc-3",      "x": 50, "y": 55, "label": "—",          "fractie": "",      "isMain": False, "fractie_card_id": None},
    {"id": "loc-4",      "x": 45, "y": 80, "label": "—",          "fractie": "",      "isMain": False, "fractie_card_id": None},
]


def _load() -> dict:
    MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(MAP_FILE, default={})
    if not data or "locations" not in data:
        data = {"locations": [dict(loc) for loc in DEFAULT_LOCATIONS], "updated_at": None, "updated_by": None}
        save_json(MAP_FILE, data)
    return data


def _is_admin(user_id: Optional[str]) -> bool:
    if not user_id:
        return False
    users = load_json(USERS_FILE, default={"users": []}).get("users", [])
    u = next((x for x in users if x.get("id") == user_id), None)
    return bool(u and (u.get("gradatie", 99) <= 2))


class Location(BaseModel):
    id: str
    x: float
    y: float
    label: str = "—"
    fractie: str = ""
    isMain: bool = False
    fractie_card_id: Optional[str] = None


class LocationsUpdate(BaseModel):
    locations: List[Location]
    user_id: str


@router.get("/locations")
async def get_locations():
    return _load()


@router.put("/locations")
async def put_locations(req: LocationsUpdate):
    if not _is_admin(req.user_id):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2) kan de SPARK WORLD map bewerken")
    data = {
        "locations": [loc.dict() for loc in req.locations],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": req.user_id,
    }
    save_json(MAP_FILE, data)
    return data


@router.post("/locations/reset")
async def reset_locations(req: dict):
    user_id = req.get("user_id")
    if not _is_admin(user_id):
        raise HTTPException(403, "Alleen admin kan resetten")
    data = {
        "locations": [dict(loc) for loc in DEFAULT_LOCATIONS],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user_id,
    }
    save_json(MAP_FILE, data)
    return data
