"""v6_kb_llm_generate_001 — Laat LLM een lege/incomplete KB-kaart invullen.

Workflow:
1. Admin opent inbox-kaart die laag1/ws5 mist
2. Klikt 'Genereer met LLM' knop
3. POST /api/kb/v2/cards/{id}/llm-generate
4. Backend stuurt huidige (lege) kaart + begrip naar Groq
5. LLM vult laag1/laag2/laag3/laag4 + ws5 in JSON-format
6. Frontend toont voorstel naast originele lege kaart
7. Admin keurt goed → kaart wordt opgeslagen + verplaatst naar gekozen lade

Geen Emergent-credits — alles via gratis Groq via bestaande llm_router.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json
from modules.kb_v2.service import _v2_dir  # bestaande helper

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kb/v2/cards", tags=["kb-v2-llm"])


class GenerateRequest(BaseModel):
    target_lade: Optional[str] = None  # admin kan voorkeur meegeven (doen/weten/voelen/spreken)


class ApproveRequest(BaseModel):
    proposal: Dict[str, Any]
    target_lade: str  # admin kiest waar de kaart heen gaat


def _find_inbox_card(card_id: str) -> Optional[Dict]:
    v2_dir = _v2_dir()
    inbox = load_json(v2_dir / "knowledge_inbox.json", default={"kaarten": []})
    for c in inbox.get("kaarten", []):
        if c.get("id") == card_id:
            return c
    return None


def _build_prompt(card: Dict, target_lade: Optional[str]) -> list:
    begrip = card.get("begrip", "")
    bestaande_tags = card.get("tags", [])
    bestaande_laag1 = (card.get("lagen") or {}).get("laag1") or ""
    bestaande_laag2 = (card.get("lagen") or {}).get("laag2") or ""

    sys = (
        "Je bent een Nederlandstalige KB-card editor voor Spark. "
        "Vul kaart-formaat in voor het gegeven begrip. "
        "Geef ALLEEN geldig JSON terug, geen markdown, geen extra tekst."
    )

    lade_hint = f"\nDe kaart wordt waarschijnlijk in lade: '{target_lade}'.\n" if target_lade else ""

    user = (
        f"Begrip: \"{begrip}\"\n"
        f"Bestaande tags: {bestaande_tags}\n"
        f"Bestaande laag1: \"{bestaande_laag1}\"\n"
        f"Bestaande laag2: \"{bestaande_laag2}\"\n"
        f"{lade_hint}\n"
        "Vul de volgende velden in (kort, Nederlands, geen ChatGPT-clichés):\n\n"
        "{\n"
        '  "laag1": "1 zin — kernbetekenis (max 20 woorden)",\n'
        '  "laag2": "2-3 zinnen — context/uitleg (max 50 woorden)",\n'
        '  "laag3": "max 200 woorden — diepere achtergrond",\n'
        '  "laag4": "max 300 woorden — uitgebreid",\n'
        '  "ws5": {\n'
        '    "wie": "subject",\n'
        '    "wat": "kerneigenschap",\n'
        '    "wanneer": "tijd/context",\n'
        '    "waar": "plaats",\n'
        '    "waarom": "reden/doel",\n'
        '    "hoe": "werking"\n'
        "  },\n"
        '  "voorgestelde_lade": "doen|weten|voelen|spreken",\n'
        '  "extra_tags": ["max 5 nieuwe tags"]\n'
        "}\n\n"
        "Houd het feitelijk en compact. Geen 'Hier zijn 3 punten...' en geen excuses."
    )
    return [{"role": "system", "content": sys}, {"role": "user", "content": user}]


@router.post("/{card_id}/llm-generate")
async def llm_generate_card(card_id: str, req: GenerateRequest):
    """Laat LLM een KB-kaart invullen. Returnt voorstel, schrijft niets weg."""
    card = _find_inbox_card(card_id)
    if not card:
        raise HTTPException(404, f"Inbox-kaart {card_id} niet gevonden")

    from modules.chat import llm_router
    messages = _build_prompt(card, req.target_lade)
    resp = await llm_router.chat_complete(messages, temperature=0.3, max_tokens=800, timeout=20.0)

    if not resp.get("success"):
        raise HTTPException(503, f"LLM-call mislukt: {resp.get('error')}")

    text = resp.get("text", "").strip()
    # Strip markdown fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)

    try:
        proposal = json.loads(text)
    except Exception as ex:
        raise HTTPException(500, f"LLM gaf geen geldig JSON: {ex}. Output: {text[:200]}")

    return {
        "success": True,
        "card_id": card_id,
        "begrip": card.get("begrip"),
        "original": card,
        "proposal": proposal,
        "llm_provider": resp.get("provider"),
        "llm_model": resp.get("model"),
        "llm_latency_s": resp.get("latency_s"),
    }


@router.post("/{card_id}/llm-approve")
async def llm_approve_card(card_id: str, req: ApproveRequest):
    """Pas LLM-voorstel toe en verplaats kaart naar target_lade."""
    if req.target_lade not in ("doen", "weten", "voelen", "spreken"):
        raise HTTPException(400, "target_lade moet zijn: doen/weten/voelen/spreken")

    v2_dir = _v2_dir()
    inbox_fp = v2_dir / "knowledge_inbox.json"
    target_fp = v2_dir / f"knowledge_v2_{req.target_lade}.json"

    inbox = load_json(inbox_fp, default={"kaarten": []})
    target = load_json(target_fp, default={"kaarten": []})

    found_idx = None
    for i, c in enumerate(inbox.get("kaarten", [])):
        if c.get("id") == card_id:
            found_idx = i
            break
    if found_idx is None:
        raise HTTPException(404, f"Inbox-kaart {card_id} niet meer in inbox")

    card = inbox["kaarten"].pop(found_idx)
    proposal = req.proposal or {}

    # Merge proposal in card
    card["lade"] = req.target_lade
    card.setdefault("lagen", {})
    for laag in ("laag1", "laag2", "laag3", "laag4"):
        if proposal.get(laag):
            card["lagen"][laag] = proposal[laag]
    if proposal.get("ws5"):
        card.setdefault("ws5", {})
        for k in ("wie", "wat", "wanneer", "waar", "waarom", "hoe"):
            if proposal["ws5"].get(k):
                card["ws5"][k] = proposal["ws5"][k]
    if proposal.get("extra_tags"):
        existing = set(card.get("tags", []))
        for t in proposal["extra_tags"]:
            if t not in existing:
                card.setdefault("tags", []).append(t)
    # Footnote update
    card.setdefault("footnote", {})
    card["footnote"]["llm_generated"] = True
    card["footnote"]["llm_approved_by"] = "admin"
    from datetime import datetime, timezone
    card["footnote"]["llm_approved_at"] = datetime.now(timezone.utc).isoformat()
    # Remove _inbox_reason / needs since now complete
    card.pop("_inbox_reason", None)
    card["needs"] = []

    # Insert in target lade
    target.setdefault("kaarten", []).insert(0, card)

    # Save both
    save_json(inbox_fp, inbox)
    save_json(target_fp, target)

    return {
        "success": True,
        "card_id": card_id,
        "moved_to": req.target_lade,
        "begrip": card.get("begrip"),
    }
