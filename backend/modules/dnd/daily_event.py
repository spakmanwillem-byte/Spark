"""
v6_daily_event_001 — Dagelijks "Vecht voor je leven" Steen-Papier-Schaar event.

- 1× per dag per user beschikbaar
- Win = +10 goud, draw/loss = niks (geen straf)
- Persistence: /app/backend/data/dnd/daily_events.json
"""
from __future__ import annotations
import json
import random
from datetime import datetime, timezone, date as _date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/dnd/daily-event", tags=["dnd-daily-event"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
EVENTS_PATH = DATA_ROOT / "dnd" / "daily_events.json"
USERS_PATH = DATA_ROOT / "users.json"
CHOICES = ["steen", "papier", "schaar"]
WIN_GOUD = 10


def _today_iso() -> str:
    return _date.today().isoformat()


def _resolve(player: str, ai: str) -> str:
    if player == ai:
        return "draw"
    if (player == "steen" and ai == "schaar") or \
       (player == "papier" and ai == "steen") or \
       (player == "schaar" and ai == "papier"):
        return "win"
    return "loss"


def _load_state() -> dict:
    if not EVENTS_PATH.exists():
        return {"users": {}}
    try:
        return json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"users": {}}


def _save_state(data: dict) -> None:
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class PlayReq(BaseModel):
    choice: str  # steen | papier | schaar


@router.get("/{user_id}")
async def get_daily_event(user_id: str):
    """Status van het dagelijkse SPS-gevecht voor deze user."""
    state = _load_state()
    user_state = (state.get("users") or {}).get(user_id) or {}
    today = _today_iso()
    if user_state.get("date") != today:
        return {
            "available": True,
            "played": False,
            "date": today,
            "title": "Vecht voor je leven",
            "subtitle": "Een schaduw nadert. Eén ronde Steen-Papier-Schaar — win en je krijgt 10 goud, verlies en je gaat met lege handen verder.",
            "choices": CHOICES,
            "win_goud": WIN_GOUD,
        }
    return {
        "available": False,
        "played": True,
        "date": today,
        "result": user_state.get("result"),
        "choice": user_state.get("choice"),
        "ai_choice": user_state.get("ai_choice"),
        "reward_goud": user_state.get("reward_goud", 0),
        "title": "Dagelijks gevecht — al voltooid",
        "subtitle": "Kom morgen terug voor een nieuwe ronde.",
        "choices": CHOICES,
        "win_goud": WIN_GOUD,
    }


@router.post("/{user_id}/play")
async def play_daily_event(user_id: str, req: PlayReq):
    """Speel 1 ronde SPS. 1× per dag."""
    if req.choice not in CHOICES:
        raise HTTPException(400, f"Ongeldige keuze: {req.choice}")
    state = _load_state()
    today = _today_iso()
    user_state = (state.get("users") or {}).get(user_id) or {}
    if user_state.get("date") == today and user_state.get("played"):
        raise HTTPException(400, "Vandaag al gespeeld — kom morgen terug.")

    ai_choice = random.choice(CHOICES)
    result = _resolve(req.choice, ai_choice)
    reward = WIN_GOUD if result == "win" else 0

    # Beloning uitkeren: update users.json -> currency.goud
    if reward > 0:
        users_data = load_json(USERS_PATH, default={"users": []})
        users = users_data.get("users", [])
        for u in users:
            if u.get("id") == user_id:
                cur = u.setdefault("currency", {})
                cur["goud"] = int(cur.get("goud", 0)) + reward
                break
        save_json(USERS_PATH, users_data)

    # State opslaan
    state.setdefault("users", {})[user_id] = {
        "date": today,
        "played": True,
        "choice": req.choice,
        "ai_choice": ai_choice,
        "result": result,
        "reward_goud": reward,
        "played_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_state(state)

    return {
        "success": True,
        "result": result,
        "choice": req.choice,
        "ai_choice": ai_choice,
        "reward_goud": reward,
        "bark": _bark_text(result, ai_choice, req.choice),
    }


def _bark_text(result: str, ai: str, player: str) -> str:
    if result == "win":
        return f"De schaduw koos {ai}, jij koos {player} — je hebt de strijd gewonnen! +{WIN_GOUD} goud."
    if result == "draw":
        return f"De schaduw koos {ai}, jij koos {player} — een staaroorlog. Geen winst, geen verlies."
    return f"De schaduw koos {ai}, jij koos {player} — je ontsnapte met de hakken over de sloot. Geen verlies, maar ook geen winst."
