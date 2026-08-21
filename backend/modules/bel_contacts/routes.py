"""v12_contact_call_001 — Bel-contacten + WhatsApp deep-link quick-win.

Willem's opzet:
  User zegt "bel mijn moeder" → Spark herkent contact via relatie → Response bevat
  action.contact_call → Frontend toont popup met WhatsApp deep-link.

Data: `/app/backend/data/users/{user_id}/bel_contacts.json` (los van `modules/contacts`
die al bestaat voor online-users / admin-collectief).
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/bel-contacts", tags=["bel-contacts"])

USERS_DIR = Path("/app/backend/data/users")


def _contacts_path(user_id: str) -> Path:
    d = USERS_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "bel_contacts.json"


def _load(user_id: str) -> List[Dict]:
    return load_json(_contacts_path(user_id), default={"contacts": []}).get("contacts", [])


def _save(user_id: str, contacts: List[Dict]):
    save_json(_contacts_path(user_id), {"contacts": contacts})


def _norm_phone(phone: str) -> str:
    """+31612345678 canonical form. Strip spaces/dashes, 00→+, 0→+31."""
    p = re.sub(r"[\s\-\(\)]", "", phone or "")
    if p.startswith("00"):
        p = "+" + p[2:]
    elif p.startswith("0") and not p.startswith("+"):
        p = "+31" + p[1:]
    return p


def _whatsapp_link(phone: str, message: str = "") -> str:
    p = _norm_phone(phone).lstrip("+")
    base = f"https://wa.me/{p}"
    if message:
        base += f"?text={quote(message)}"
    return base


class Contact(BaseModel):
    name: str
    relation: Optional[str] = None
    phone: str
    whatsapp_ok: bool = True
    notes: Optional[str] = None


@router.get("/{user_id}")
async def list_contacts(user_id: str):
    return {"success": True, "contacts": _load(user_id)}


@router.post("/{user_id}")
async def add_contact(user_id: str, c: Contact):
    contacts = _load(user_id)
    c_dict = c.dict()
    c_dict["id"] = f"bel-{uuid.uuid4().hex[:8]}"
    c_dict["phone"] = _norm_phone(c_dict["phone"])
    contacts.append(c_dict)
    _save(user_id, contacts)
    return {"success": True, "contact": c_dict}


@router.delete("/{user_id}/{contact_id}")
async def delete_contact(user_id: str, contact_id: str):
    contacts = _load(user_id)
    new = [c for c in contacts if c.get("id") != contact_id]
    if len(new) == len(contacts):
        raise HTTPException(404, "Contact niet gevonden")
    _save(user_id, new)
    return {"success": True}


@router.get("/{user_id}/lookup")
async def lookup_call(user_id: str, target: str):
    """Chat-detector helper. Frontend/backend kan hem aanroepen zodra 'bel X'
    is herkend. Retourneert het gevonden contact + WhatsApp-link."""
    return detect_contact_call(f"bel {target}", user_id) or {"found": False, "query": target}


def detect_contact_call(text: str, user_id: str) -> Optional[Dict]:
    """Herken 'bel [mijn] [naam of relatie]' in chat-input.

    Voorbeelden die matchen:
      - "bel mijn moeder"
      - "bel Marieke"
      - "kan je mijn vader bellen"
      - "bel oma even"
    """
    if not text:
        return None
    t = text.lower().strip()
    m = re.search(r"\b(?:kan\s+je\s+)?(?:mijn\s+)?(\w+)\s+bellen\b", t) \
        or re.search(r"\bbel\s+(?:mijn\s+|even\s+)*(\w+)\b", t)
    if not m:
        return None
    target = m.group(1).strip()
    if target in {"bel", "mijn", "even", "een", "je", "de"}:
        return None
    contacts = _load(user_id)
    hit = next(
        (c for c in contacts
         if (c.get("relation") or "").lower() == target
         or (c.get("name") or "").lower() == target
         or target in (c.get("name") or "").lower().split()),
        None,
    )
    if not hit:
        return {
            "type": "contact_call",
            "found": False,
            "query": target,
            "message": f"Ik ken geen contact '{target}'. Voeg toe via Beheer → Bel-contacten of `POST /api/bel-contacts/{user_id}`.",
        }
    return {
        "type": "contact_call",
        "found": True,
        "contact": {
            "id": hit.get("id"),
            "name": hit.get("name"),
            "relation": hit.get("relation"),
            "phone": hit.get("phone"),
        },
        "whatsapp_link": _whatsapp_link(hit["phone"]) if hit.get("whatsapp_ok", True) else None,
        "tel_link": f"tel:{hit['phone']}",
        "message": f"Klik om {hit.get('name')} te bellen via WhatsApp.",
    }
