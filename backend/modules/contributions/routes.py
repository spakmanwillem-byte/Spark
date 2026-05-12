"""
Contributions API (v4_009 - Bijdrage portaal)

Endpoints:
  GET  /api/contributions/next-card?user_id=X  → claim huidige kaart
  POST /api/contributions/save                 → tussentijds opslaan
  POST /api/contributions/submit               → indienen voor review
  POST /api/contributions/skip                 → kaart te moeilijk, terug naar pool
  GET  /api/contributions/my-stats?user_id=X   → mijn voortgang
  GET  /api/contributions/pending              → admin: lijst wachtende kaarten
  POST /api/contributions/approve              → admin: keur goed (geeft XP)
  POST /api/contributions/reject               → admin: wijs af
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from modules.core.storage import load_json
from modules.contributions import (
    get_or_create_claim, release_claim, get_card,
    save_partial, submit_for_review, list_pending_for_admin,
    approve as approve_card, reject as reject_card, user_stats,
)
from modules.chat import xp_service

router = APIRouter(prefix="/api/contributions", tags=["contributions"])

DATA_DIR = Path(__file__).parent.parent.parent / "data"
ALLOWED_GRADATIES = (1, 2, 3, 4, 5)
XP_PER_APPROVED_CARD = 25


def _user_gradatie(user_id):
    users = load_json(DATA_DIR / "system" / "users.json", default={"users": []}).get("users", [])
    for u in users:
        if u.get("id") == user_id:
            return u.get("gradatie")
    return None


def _gate(user_id):
    g = _user_gradatie(user_id)
    if g not in ALLOWED_GRADATIES:
        raise HTTPException(403, "Bijdragen is alleen voor gradatie 1 tm 5.")
    return g


def _admin_gate(user_id):
    g = _user_gradatie(user_id)
    if g not in (1, 2):
        raise HTTPException(403, "Alleen admin (gradatie 1-2) mag goedkeuren.")


# ---- Schemas ----
class SaveRequest(BaseModel):
    user_id: str
    card_id: str
    ws5: Optional[dict] = None
    lagen: Optional[dict] = None
    belangrijkheid: Optional[int] = None


class SubmitRequest(BaseModel):
    user_id: str
    card_id: str
    ws5: Optional[dict] = None
    lagen: Optional[dict] = None
    belangrijkheid: Optional[int] = None


class SkipRequest(BaseModel):
    user_id: str


class AdminActionRequest(BaseModel):
    admin_id: str
    card_id: str
    reason: Optional[str] = ""


# ---- Endpoints ----

@router.get("/next-card")
def next_card(user_id: str):
    _gate(user_id)
    claim = get_or_create_claim(user_id)
    if not claim:
        return {"success": False, "message": "Geen kaarten beschikbaar in de pool."}
    card = get_card(claim["card_id"])
    if not card:
        release_claim(user_id, "card_missing")
        return {"success": False, "message": "Kaart verdwenen, probeer opnieuw."}
    return {
        "success": True,
        "claim_id": claim["id"],
        "claimed_at": claim["claimed_at"],
        "card": {
            "id": card["id"],
            "begrip": card["begrip"],
            "topic": card.get("topic", ""),
            "tags": card.get("tags", []),
            "ws5": card.get("ws5") or {},
            "lagen": card.get("lagen") or {},
            "belangrijkheid": card.get("belangrijkheid"),
            "is_sentence": "context-zin" in (card.get("tags") or []) or (card.get("metadata") or {}).get("is_sentence", False),
            "snap_context": card.get("snap_context", ""),
            "bron": card.get("bron", ""),
        },
    }


@router.post("/save")
def save(req: SaveRequest):
    _gate(req.user_id)
    card = save_partial(req.card_id, req.ws5 or {}, req.lagen, req.belangrijkheid)
    if not card:
        raise HTTPException(404, "Kaart niet gevonden.")
    return {"success": True, "ws5": card.get("ws5"), "lagen": card.get("lagen"), "belangrijkheid": card.get("belangrijkheid")}


@router.post("/submit")
def submit(req: SubmitRequest):
    _gate(req.user_id)
    result = submit_for_review(req.user_id, req.card_id, req.ws5 or {}, req.lagen, req.belangrijkheid)
    if not result.get("success"):
        raise HTTPException(400, result.get("error", "submit_failed"))
    return result


@router.post("/skip")
def skip(req: SkipRequest):
    _gate(req.user_id)
    released = release_claim(req.user_id, reason="skipped")
    return {"success": True, "released": released}


@router.get("/my-stats")
def my_stats(user_id: str):
    _gate(user_id)
    return user_stats(user_id)


@router.get("/pending")
def pending(admin_id: str):
    _admin_gate(admin_id)
    return {"pending": list_pending_for_admin()}


@router.post("/approve")
def approve(req: AdminActionRequest):
    _admin_gate(req.admin_id)
    result = approve_card(req.card_id, req.admin_id)
    if not result.get("success"):
        raise HTTPException(404, result.get("error", "card_not_found"))
    # Reken XP uit
    if result.get("eligible_for_xp") and result.get("contributor_user_id"):
        xp_result = xp_service.grant_xp(
            result["contributor_user_id"],
            XP_PER_APPROVED_CARD,
            reason=f"Bijdrage goedgekeurd ({result['percentage']}% gevuld)"
        )
        result["xp_granted"] = xp_result
    return result


@router.post("/reject")
def reject(req: AdminActionRequest):
    _admin_gate(req.admin_id)
    result = reject_card(req.card_id, req.admin_id, reason=req.reason or "")
    if not result.get("success"):
        raise HTTPException(404, result.get("error", "card_not_found"))
    return result
