"""
v6_capabilities_admin_001 — Admin overzicht van alle Spark capabilities.

Endpoints:
  GET  /api/admin/capabilities        — alle caps met live/placeholder/handler status
  POST /api/admin/capabilities/test   — test een specifieke capability met sample text

v6_capability_links_001 — Doe-kaart ↔ capability koppelingen:
  GET    /api/admin/capabilities/links            — alle koppelingen
  POST   /api/admin/capabilities/links            — koppel kaart → capability
  DELETE /api/admin/capabilities/links/{card_id}  — ontkoppel
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from modules.chat import intent_matcher_service, capability_handler_service

router = APIRouter(prefix="/admin/capabilities", tags=["admin-capabilities"])

LINKS_FP = Path(__file__).parent.parent.parent / "data" / "personality" / "capability_links.json"


def _load_links() -> dict:
    if not LINKS_FP.exists():
        return {"links": {}}
    try:
        return json.loads(LINKS_FP.read_text())
    except Exception:
        return {"links": {}}


def _save_links(data: dict) -> None:
    LINKS_FP.parent.mkdir(parents=True, exist_ok=True)
    LINKS_FP.write_text(json.dumps(data, indent=2, ensure_ascii=False))


class TestRequest(BaseModel):
    text: str
    user_id: Optional[str] = "user-001"


class LinkRequest(BaseModel):
    card_id: str
    capability_id: str


@router.get("")
async def list_capabilities():
    caps = intent_matcher_service.all_capabilities()
    handlers = set(capability_handler_service._HANDLERS.keys())
    enriched = []
    for c in caps:
        enriched.append({
            **c,
            "has_handler": c.get("id") in handlers,
            "effective_status": (
                "executable" if c.get("id") in handlers
                else c.get("status", "idea")
            ),
        })
    return {
        "total": len(enriched),
        "executable": sum(1 for c in enriched if c["has_handler"]),
        "live_no_handler": sum(1 for c in enriched if c.get("status") == "live" and not c["has_handler"]),
        "placeholder": sum(1 for c in enriched if c.get("status") == "placeholder"),
        "idea": sum(1 for c in enriched if c.get("status") == "idea"),
        "capabilities": enriched,
    }


@router.post("/test")
async def test_capability(req: TestRequest):
    match = intent_matcher_service.match_capability(req.text)
    if not match:
        return {"matched": False, "message": "Geen capability gematched op die zin."}
    resp = capability_handler_service.route_capability(req.text, req.user_id)
    return {
        "matched": True,
        "match": match,
        "execution": resp,
    }


@router.get("/links")
async def list_links():
    """Geef alle doe-kaart↔capability koppelingen + verrijking met kaart-naam en capability-naam."""
    data = _load_links()
    links = data.get("links", {})

    # Verrijk met kaart-begrip en capability-naam
    cap_by_id = {c["id"]: c for c in intent_matcher_service.all_capabilities()}
    enriched = []
    try:
        from modules.core.storage import load_json
        # Doe-lade laden voor begrip-lookup
        doen_fp = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2" / "knowledge_v2_doen.json"
        doen = load_json(doen_fp, default={"kaarten": []}).get("kaarten", [])
        kaart_by_id = {k.get("id"): k for k in doen}
    except Exception:
        kaart_by_id = {}

    for card_id, cap_id in links.items():
        kaart = kaart_by_id.get(card_id, {})
        cap = cap_by_id.get(cap_id, {})
        enriched.append({
            "card_id": card_id,
            "card_begrip": kaart.get("begrip", "?"),
            "capability_id": cap_id,
            "capability_naam": cap.get("naam", cap_id),
            "capability_status": cap.get("status", "?"),
            "has_handler": cap_id in capability_handler_service._HANDLERS,
        })

    return {
        "total": len(enriched),
        "links": enriched,
    }


@router.post("/links")
async def add_link(req: LinkRequest):
    """Koppel een doe-kaart aan een capability."""
    cap_by_id = {c["id"]: c for c in intent_matcher_service.all_capabilities()}
    if req.capability_id not in cap_by_id:
        raise HTTPException(status_code=400, detail=f"Onbekende capability_id: {req.capability_id}")
    data = _load_links()
    data.setdefault("links", {})[req.card_id] = req.capability_id
    _save_links(data)
    return {"success": True, "card_id": req.card_id, "capability_id": req.capability_id}


@router.delete("/links/{card_id}")
async def remove_link(card_id: str):
    """Ontkoppel een doe-kaart."""
    data = _load_links()
    if card_id in data.get("links", {}):
        del data["links"][card_id]
        _save_links(data)
        return {"success": True, "removed": card_id}
    raise HTTPException(status_code=404, detail="Geen koppeling gevonden voor die kaart.")
