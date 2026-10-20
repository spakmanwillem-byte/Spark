"""v14_contacten_klapper_001 (Willem 19-10-2026) — Telefoonklapper met twee lagen: privé en zakelijk.

Eén plek, niets dubbel:
  • eigen contacten  → data/users/<user_id>/contacten.json  (bron 'klapper', bewerkbaar)
  • privé-laag toont ook bel_contacts.json  (bron 'bel', alleen lezen hier)
  • zakelijke laag toont ook clienten        (bron 'clienten', alleen lezen hier)
Rollen zakelijk: leverancier | dienstverlener (advocaat, accountant…) | klant (koopt merch) | client (vraagt zorg/handelingen) | partner | overig. Privé: familie | vriend | overig.
Later (roadmap): Spark matcht contacten op e-mail/tel/naam aan users → zichtbaar in privé-gesprekken.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/contacten", tags=["contacten"])
USERS_DIR = Path(__file__).parent.parent.parent / "data" / "users"
LAGEN = ("prive", "zakelijk")


def _path(user_id: str) -> Path:
    d = USERS_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "contacten.json"


def _load(user_id: str) -> List[Dict]:
    return load_json(_path(user_id), default={"contacten": []}).get("contacten", [])


def _save(user_id: str, items: List[Dict]) -> None:
    save_json(_path(user_id), {"contacten": items})


class ContactIn(BaseModel):
    laag: str = "prive"
    naam: str
    rol: Optional[str] = None
    bedrijf: Optional[str] = None
    contactpersoon: Optional[str] = None
    email: Optional[str] = None
    email2: Optional[str] = None
    telefoon: Optional[str] = None
    telefoon2: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None
    adres: Optional[str] = None
    postcode: Optional[str] = None
    plaats: Optional[str] = None
    notities: Optional[str] = None
    # zakelijk (Willem 20-10: stonden in notities)
    kvk: Optional[str] = None
    btw_nummer: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    klantnummer: Optional[str] = None  # jouw debiteur-/klantnummer bij hen


def _clean(body: ContactIn) -> Dict:
    return {k: (v.strip() if isinstance(v, str) else v) for k, v in body.model_dump().items()}


def _from_bel(c: Dict) -> Dict:
    return {"id": f"bel:{c.get('id')}", "bron": "bel", "laag": "prive", "naam": c.get("name"),
            "rol": c.get("relation") or "overig", "telefoon": c.get("phone"), "notities": c.get("notes"),
            "readonly": False}


def _from_client(c: Dict) -> Dict:
    return {"id": f"client:{c.get('id')}", "bron": "clienten", "laag": "zakelijk", "naam": c.get("naam"),
            "rol": "client", "bedrijf": c.get("naam"), "contactpersoon": c.get("contactpersoon"),
            "email": c.get("email"), "email2": c.get("email2"), "telefoon": c.get("telefoon"),
            "telefoon2": c.get("telefoon2"), "fax": c.get("fax"), "website": c.get("website"), "adres": c.get("adres"),
            "postcode": c.get("postcode"), "plaats": c.get("plaats"), "notities": c.get("notities"),
            "readonly": False}


_BEL_MAP = {"naam": "name", "rol": "relation", "telefoon": "phone", "notities": "notes"}
_CLIENT_KEYS = ("naam", "contactpersoon", "email", "email2", "telefoon", "telefoon2", "fax", "website", "adres", "postcode", "plaats", "notities", "kvk", "btw_nummer", "iban", "bic", "klantnummer")


def _bel_file(user_id: str) -> Path:
    return USERS_DIR / user_id / "bel_contacts.json"


def _client_file(user_id: str) -> Path:
    return USERS_DIR.parent / "clienten" / f"{user_id}.json"


def _update_extern(user_id: str, contact_id: str, body: ContactIn) -> Optional[Dict]:
    """Bel-/client-contact vanuit de klapper bijwerken: schrijft terug naar het bronbestand."""
    data = body.model_dump()
    if contact_id.startswith("bel:"):
        f = _bel_file(user_id); d = load_json(f, default={"contacts": []})
        for c in d.get("contacts", []):
            if str(c.get("id")) == contact_id[4:]:
                for k, v in data.items():
                    if k == "laag":
                        continue
                    c[_BEL_MAP.get(k, k)] = v
                save_json(f, d)
                return {**_from_bel(c), **{k: v for k, v in c.items() if k in ("email", "email2", "telefoon2", "fax", "website", "bedrijf", "contactpersoon", "adres", "postcode", "plaats")}}
    if contact_id.startswith("client:"):
        f = _client_file(user_id); d = load_json(f, default={"clienten": []})
        for c in d.get("clienten", []):
            if str(c.get("id")) == contact_id[7:]:
                for k in _CLIENT_KEYS:
                    c[k] = data.get(k)
                c["updated_at"] = datetime.now(timezone.utc).isoformat()
                save_json(f, d)
                return _from_client(c)
    return None


def _delete_extern(user_id: str, contact_id: str) -> bool:
    if contact_id.startswith("bel:"):
        f = _bel_file(user_id); d = load_json(f, default={"contacts": []})
        rest = [c for c in d.get("contacts", []) if str(c.get("id")) != contact_id[4:]]
        if len(rest) == len(d.get("contacts", [])):
            return False
        save_json(f, {**d, "contacts": rest}); return True
    if contact_id.startswith("client:"):
        f = _client_file(user_id); d = load_json(f, default={"clienten": []})
        rest = [c for c in d.get("clienten", []) if str(c.get("id")) != contact_id[7:]]
        if len(rest) == len(d.get("clienten", [])):
            return False
        save_json(f, {**d, "clienten": rest}); return True
    return False


def alle_contacten(user_id: str, laag: str = "") -> List[Dict]:
    items = [{**c, "bron": "klapper", "readonly": False} for c in _load(user_id)]
    bel = load_json(_bel_file(user_id), default={"contacts": []}).get("contacts", [])
    items += [{**_from_bel(c), **{k: c.get(k) for k in ("email", "email2", "telefoon2", "fax", "website", "bedrijf", "contactpersoon", "adres", "postcode", "plaats") if c.get(k)}} for c in bel]
    cl = load_json(_client_file(user_id), default={"clienten": []}).get("clienten", [])
    items += [_from_client(c) for c in cl if (c.get("scope") or "zakelijk") == "zakelijk"]
    if laag in LAGEN:
        items = [c for c in items if c.get("laag") == laag]
    items.sort(key=lambda c: (c.get("naam") or "").lower())
    return items


@router.get("/{user_id}")
async def list_contacten(user_id: str, laag: str = Query("")):
    items = alle_contacten(user_id, laag)
    return {"success": True, "contacten": items,
            "per_laag": {l: sum(1 for c in alle_contacten(user_id) if c.get("laag") == l) for l in LAGEN}}


@router.post("/{user_id}")
async def create_contact(user_id: str, body: ContactIn):
    if body.laag not in LAGEN:
        raise HTTPException(400, "laag moet prive of zakelijk zijn")
    if not body.naam.strip():
        raise HTTPException(400, "naam is verplicht")
    items = _load(user_id)
    c = {"id": f"ct-{uuid.uuid4().hex[:8]}", **_clean(body),
         "created_at": datetime.now(timezone.utc).isoformat()}
    items.append(c)
    _save(user_id, items)
    return {"success": True, "contact": c}


@router.put("/{user_id}/{contact_id}")
async def update_contact(user_id: str, contact_id: str, body: ContactIn):
    if body.laag not in LAGEN:
        raise HTTPException(400, "laag moet prive of zakelijk zijn")
    ext = _update_extern(user_id, contact_id, body)
    if ext:
        return {"success": True, "contact": ext}
    items = _load(user_id)
    for c in items:
        if c["id"] == contact_id:
            c.update(_clean(body))
            c["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save(user_id, items)
            return {"success": True, "contact": c}
    raise HTTPException(404, "Contact niet gevonden")


@router.delete("/{user_id}/{contact_id}")
async def delete_contact(user_id: str, contact_id: str):
    if _delete_extern(user_id, contact_id):
        return {"success": True}
    items = _load(user_id)
    rest = [c for c in items if c["id"] != contact_id]
    if len(rest) == len(items):
        raise HTTPException(404, "Contact niet gevonden")
    _save(user_id, rest)
    return {"success": True}
