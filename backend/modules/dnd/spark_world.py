"""
Spark World — Bark Flow (v6_dnd_bark_001)
==========================================
D&D verhaal-stroom vanuit community chat.

Concept:
  1. User triggert sessie ("help" / knop "Spark World")
  2. Intro-bark wordt getoond + 3 zintuig-knoppen (ZIE / HOOR / VOEL)
  3. User klikt zintuig → krijgt vraag → typt antwoord
  4. Antwoord wordt opgeslagen als D&D-kaart (draft) in /data/cards/dnd/
  5. Kaarten kunnen 'locked' worden (canon) zodat ze in volgend spel als
     keuze-knop verschijnen.

NB: combat / NPC-dialoog komt later. Dit is alleen het skelet.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json


router = APIRouter(prefix="/dnd/spark-world", tags=["dnd-spark-world"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
CARDS_DIR = DATA_ROOT / "cards" / "dnd"
CARDS_INDEX = CARDS_DIR / "_index.json"


# ---------------------------------------------------------------------------
# Statische config: de 3 zintuig-kanalen
# ---------------------------------------------------------------------------
SENSES = [
    {
        "id": "zie",
        "label": "Zie",
        "icon": "👁️",
        "color": "#06b6d4",          # cyan
        "prompt": "Wat zie je om je heen? Een kleur, een vorm, iets dat opvalt...",
        "kb_lade": "weten",          # → KB v2 lade-koppeling
    },
    {
        "id": "hoor",
        "label": "Hoor",
        "icon": "👂",
        "color": "#f59e0b",          # amber
        "prompt": "Wat hoor je? Een geluid, een woord, een onderwerp dat doorklinkt...",
        "kb_lade": "spreken",
    },
    {
        "id": "voel",
        "label": "Voel",
        "icon": "❤️",
        "color": "#ec4899",          # pink
        "prompt": "Wat voel je nu? Een emotie, een spanning, een rust...",
        "kb_lade": "voelen",
    },
]

INTRO_TEXT = (
    "Welkom in **Spark World**.\n\n"
    "Dit is een levende wereld. Geen gevechten, geen levens. "
    "Alleen dat wat jij meebrengt en wat de wereld terug geeft.\n\n"
    "Iets trekt je. Je staat ergens — maar waar precies, dat bepaal jij. "
    "Kies hoe je in deze wereld stapt:"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_index() -> dict:
    return load_json(CARDS_INDEX, default={"cards": [], "updated_at": _now()})


def _save_index(idx: dict) -> None:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    idx["updated_at"] = _now()
    save_json(CARDS_INDEX, idx)


def _card_path(card_id: str) -> Path:
    return CARDS_DIR / f"{card_id}.json"


def _sense(sense_id: str) -> Optional[dict]:
    for s in SENSES:
        if s["id"] == sense_id:
            return s
    return None


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class StartBody(BaseModel):
    user_id: str = "user-001"


class RespondBody(BaseModel):
    user_id: str = "user-001"
    sense: str          # "zie" | "hoor" | "voel"
    content: str        # wat user invulde
    titel: Optional[str] = None


class LockBody(BaseModel):
    user_id: str = "user-001"
    locked: bool = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/start")
async def start_session(body: StartBody):
    """Start een Spark World sessie.
    Geeft intro-tekst + 3 zintuig-knoppen + bestaande locked-kaarten
    die als nieuwe keuze-knoppen kunnen verschijnen.
    """
    idx = _load_index()
    locked_choices: List[Dict] = []
    for entry in idx.get("cards", []):
        if entry.get("status") != "locked":
            continue
        # Laad volledig kaart om sense+color te krijgen
        cp = _card_path(entry["id"])
        if not cp.exists():
            continue
        try:
            card = json.loads(cp.read_text(encoding="utf-8"))
        except Exception:
            continue
        sense = _sense(card.get("sense") or "")
        locked_choices.append({
            "id": card.get("id"),
            "titel": card.get("titel") or entry.get("titel"),
            "sense": card.get("sense"),
            "color": sense["color"] if sense else "#94a3b8",
            "icon": sense["icon"] if sense else "✨",
            "content_preview": (card.get("content") or "")[:80],
        })

    return {
        "success": True,
        "session_id": f"sw-{uuid.uuid4().hex[:8]}",
        "intro": INTRO_TEXT,
        "title": "Spark World",
        "baseline": "Een levende wereld. Wat jij invult, kleurt mee.",
        "senses": SENSES,
        "locked_cards": locked_choices,
        "draft_count": sum(1 for c in idx.get("cards", []) if c.get("status") == "draft"),
    }


@router.post("/respond")
async def respond(body: RespondBody):
    """User koos een zintuig + typte een tekst → maakt een nieuwe D&D-kaart aan
    in /data/cards/dnd/ met status 'draft'."""
    sense = _sense(body.sense)
    if not sense:
        raise HTTPException(400, f"Onbekend zintuig: {body.sense}")
    if not (body.content or "").strip():
        raise HTTPException(400, "Content mag niet leeg zijn")

    card_id = f"card-dnd-{uuid.uuid4().hex[:8]}"
    titel = (body.titel or "").strip() or _autotitle(body.content, sense["label"])
    card = {
        "id": card_id,
        "type": "dnd_bark",
        "titel": titel,
        "sense": sense["id"],
        "sense_label": sense["label"],
        "icon": sense["icon"],
        "color": sense["color"],
        "kb_lade": sense["kb_lade"],
        "content": body.content.strip(),
        "status": "draft",       # draft → locked als Willem vastklikt
        "media": {"image_url": None, "audio_url": None},
        "footnote": {
            "aangemaakt_door": body.user_id,
            "aangemaakt_op": _now(),
            "laatst_bewerkt": _now(),
            "trigger_count": 0,
        },
    }

    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    _card_path(card_id).write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")

    # Update index
    idx = _load_index()
    idx.setdefault("cards", []).insert(0, {
        "id": card_id,
        "titel": titel,
        "sense": sense["id"],
        "status": "draft",
        "created_at": card["footnote"]["aangemaakt_op"],
    })
    _save_index(idx)

    # Track behavior — story_share + kb_create proxy
    try:
        from .routes import track_behavior, TrackBody, observe, ObserveBody
        await track_behavior(TrackBody(user_id=body.user_id, counter_key="story_share", delta=1))
        await observe(ObserveBody(
            user_id=body.user_id,
            kind="spark_world_card",
            detail={"card_id": card_id, "sense": sense["id"], "titel": titel},
        ))
    except Exception:
        pass

    return {"success": True, "card": card}


@router.post("/cards/{card_id}/lock")
async def lock_card(card_id: str, body: LockBody):
    """Mark een D&D-kaart als 'locked' (canon) of zet 'm terug naar draft.
    Locked kaarten verschijnen bij volgende sessie-start als keuze-knop."""
    cp = _card_path(card_id)
    if not cp.exists():
        raise HTTPException(404, f"Kaart {card_id} niet gevonden")
    try:
        card = json.loads(cp.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(500, f"Kaart kapot: {e}")

    new_status = "locked" if body.locked else "draft"
    card["status"] = new_status
    card["footnote"]["laatst_bewerkt"] = _now()
    if body.locked:
        card["footnote"]["locked_op"] = _now()
        card["footnote"]["locked_door"] = body.user_id
    cp.write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")

    # Update index
    idx = _load_index()
    for entry in idx.get("cards", []):
        if entry.get("id") == card_id:
            entry["status"] = new_status
            break
    _save_index(idx)

    return {"success": True, "card_id": card_id, "status": new_status}


@router.get("/cards")
async def list_cards(status: Optional[str] = None, limit: int = 50):
    """Lijst D&D-bark-kaarten. Optioneel filter op status (draft|locked)."""
    idx = _load_index()
    items = idx.get("cards", [])
    if status:
        items = [c for c in items if c.get("status") == status]
    # Newest first (index voegt vooraan in, dus ok)
    items = items[:limit]
    # Verrijk met preview uit kaart-file
    out = []
    for entry in items:
        cp = _card_path(entry["id"])
        if not cp.exists():
            continue
        try:
            card = json.loads(cp.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append({
            **entry,
            "sense": card.get("sense"),
            "sense_label": card.get("sense_label"),
            "color": card.get("color"),
            "icon": card.get("icon"),
            "content_preview": (card.get("content") or "")[:140],
        })
    return {"success": True, "total": len(out), "cards": out}


@router.get("/cards/{card_id}")
async def get_card(card_id: str):
    cp = _card_path(card_id)
    if not cp.exists():
        raise HTTPException(404, f"Kaart {card_id} niet gevonden")
    return json.loads(cp.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _autotitle(content: str, sense_label: str) -> str:
    snippet = (content or "").strip().split("\n", 1)[0]
    if len(snippet) > 50:
        snippet = snippet[:47].rstrip() + "..."
    return f"{sense_label}: {snippet}" if snippet else sense_label
