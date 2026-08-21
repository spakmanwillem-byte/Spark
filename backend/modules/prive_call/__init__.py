"""v13_prive_incoming_call_001 — Lokale inkomende oproep signaal.

Zuiver lokaal: er is (nog) geen echte peer-verbinding. Deze module maakt het
mogelijk dat één user een "belletje" verstuurt naar een andere user, dat
signaal wordt lokaal opgeslagen, en de ontvanger polt periodiek.

Wordt straks vervangen door de echte lokale-socket sessie (Odroid mesh).
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/prive-call", tags=["prive-call"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
CALLS_ROOT = DATA_ROOT / "prive_calls"
CALLS_ROOT.mkdir(parents=True, exist_ok=True)

RING_TIMEOUT_S = 30  # oproep verloopt na 30s als niet beantwoord


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


class RingIn(BaseModel):
    from_user_id: str
    to_user_id: str
    mode: str = "audio"  # audio | video


@router.post("/ring")
def ring(payload: RingIn):
    """Zender laat een inkomend-oproep signaal achter bij ontvanger."""
    call_id = "call-" + secrets.token_hex(6)
    now = _now_utc()
    call = {
        "id": call_id,
        "from_user_id": payload.from_user_id,
        "to_user_id": payload.to_user_id,
        "mode": payload.mode,
        "state": "ringing",
        "created_at": _iso(now),
        "expires_at": _iso(now + timedelta(seconds=RING_TIMEOUT_S)),
    }
    fp = CALLS_ROOT / f"{payload.to_user_id}.json"
    data = load_json(fp, default={"incoming": []})
    data["incoming"] = [c for c in data.get("incoming", []) if _iso(now) < c.get("expires_at", "")]
    data["incoming"].append(call)
    save_json(fp, data)
    return {"success": True, "call": call}


@router.get("/incoming/{user_id}")
def incoming(user_id: str):
    """Ontvanger polt: geeft actieve inkomende oproepen terug."""
    fp = CALLS_ROOT / f"{user_id}.json"
    data = load_json(fp, default={"incoming": []})
    now_iso = _iso(_now_utc())
    active = [c for c in data.get("incoming", []) if c.get("state") == "ringing" and now_iso < c.get("expires_at", "")]
    return {"success": True, "calls": active, "count": len(active)}


class AnswerIn(BaseModel):
    user_id: str  # ontvanger
    call_id: str
    action: str  # accept | decline


@router.post("/answer")
def answer(payload: AnswerIn):
    fp = CALLS_ROOT / f"{payload.user_id}.json"
    data = load_json(fp, default={"incoming": []})
    for c in data.get("incoming", []):
        if c.get("id") == payload.call_id:
            c["state"] = "accepted" if payload.action == "accept" else "declined"
            c["answered_at"] = _iso(_now_utc())
            save_json(fp, data)
            return {"success": True, "call": c}
    raise HTTPException(404, "Oproep niet gevonden of verlopen")
