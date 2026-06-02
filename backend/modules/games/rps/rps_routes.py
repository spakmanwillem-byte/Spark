"""
v6_rps_001 — REST routes voor Steen-Papier-Schaar mini-game.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
from modules.games.rps import rps_service

router = APIRouter(prefix="/games/rps", tags=["games-rps"])


class PlayBody(BaseModel):
    user_id: str
    choice: str  # steen | papier | schaar


# Statische metadata voor frontend (KB-kaart links + image URLs).
# v6_rps_001b — Image-URL voor 'denkt_na' wordt live opgezocht (kaart-update).
RPS_CARDS = {
    "steen":         {"id": "kbv2-124bf8b6",      "image": "/api/system-archive/file/2f486d95b929"},
    "papier":        {"id": "kbv2-c0706698",      "image": "/api/system-archive/file/d38b8a5e2371"},
    "schaar":        {"id": "kbv2-2c6ae150",      "image": "/api/system-archive/file/7e90fa41d0b3"},
    "gewonnen":      {"id": "kbv2-2248bad7",      "image": "/api/system-archive/file/864af086c6ce"},
    "verloren":      {"id": "kbv2-89ce9289",      "image": "/api/system-archive/file/12d1aa8fb1ac"},
    "denkt_na":      {"id": "kbv2-a406125f",      "image": None},
    "maak_een_keus": {"id": "kbv2-a244cd34",      "image": "/api/system-archive/file/ba388a95bfbd"},
    "score":         {"id": "kbv2-skel-2522f483", "image": "/api/system-archive/file/47f37e76adf9"},
    "high_score":    {"id": "kbv2-2e9b7f0e",      "image": "/api/system-archive/file/118c2ea41377"},
    "stop":          {"id": "kbv2-30d45e45",      "image": "/api/system-archive/file/ae71125c340f"},
}

# v6_rps_001b — Live lookup voor kaarten die later een image krijgen (bv. denkt_na)
_KB_V2_DIR = Path(__file__).parent.parent.parent.parent / "data" / "knowledge" / "v2"


def _live_image_for(card_id: str) -> Optional[str]:
    """Zoek live image_url voor kaart-id over alle lades + inbox."""
    for f in list(_KB_V2_DIR.glob("knowledge_v2_*.json")) + [_KB_V2_DIR / "knowledge_inbox.json"]:
        try:
            d = json.loads(f.read_text())
            for k in d.get("kaarten", []):
                if k.get("id") == card_id:
                    imgs = (k.get("media") or {}).get("image_urls") or []
                    return imgs[0] if imgs else None
        except Exception:
            continue
    return None


def _hydrated_cards() -> dict:
    """Vul ontbrekende image-URLs aan uit live KB data."""
    out = {}
    for key, val in RPS_CARDS.items():
        live = _live_image_for(val["id"]) if not val.get("image") else None
        out[key] = {**val, "image": val.get("image") or live}
    return out


@router.get("/cards")
def get_cards():
    """Retourneer de KB-kaart afbeeldingen die de frontend gebruikt voor de bark."""
    return {"cards": _hydrated_cards()}


@router.post("/start")
def start(user_id: str, opponent: str = "spark"):
    """Start nieuwe sessie (reset sessie-score, niet lifetime stats).

    opponent: "spark" (default, in Spark-chat) | "bot" (random bot in community)
    """
    session = rps_service.start_session(user_id, opponent=opponent)
    return {"success": True, "session": session, "cards": _hydrated_cards()}


@router.post("/play")
def play(body: PlayBody):
    res = rps_service.play_round(body.user_id, body.choice)
    if not res.get("success"):
        raise HTTPException(400, res.get("error", "Onbekende fout"))
    return res


@router.post("/reset")
def reset(user_id: str, opponent: Optional[str] = None):
    session = rps_service.reset_session(user_id, opponent=opponent)
    return {"success": True, "session": session, "message": "Score gereset"}


@router.post("/stop")
def stop(user_id: str):
    session = rps_service.stop_session(user_id)
    return {"success": True, "session": session, "message": "Spel beëindigd"}


@router.get("/session")
def get_session(user_id: str):
    return {"session": rps_service.get_session(user_id)}


@router.get("/stats")
def get_stats(user_id: str):
    return {"stats": rps_service.get_stats(user_id)}
