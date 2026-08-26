"""
v13d_clienten_module_001 (sessie 56b) — Willem: "clienten index formulier om
weg te schrijven. index verwijst naar client dossier. basis personalia.
als spark wat leert over client kan hij gebonden info hier wegzetten".

Aparte module (níet persons — persons is familie/vrienden met D&D slots).
Clienten = opdrachtgevers met factuur-info + dossier + spark_learnings.

Storage: /app/backend/data/clienten/{user_id}.json
Structure:
  {"clienten": [{id, naam, ...contactvelden..., dossier: [{...}], spark_learnings: [{...}]}]}
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
import uuid

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/clienten", tags=["clienten"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "clienten"


class ClientCreate(BaseModel):
    naam: str  # bedrijfsnaam of persoonsnaam
    contactpersoon: Optional[str] = None
    email: Optional[str] = None
    telefoon: Optional[str] = None
    adres: Optional[str] = None
    postcode: Optional[str] = None
    plaats: Optional[str] = None
    kvk: Optional[str] = None
    btw_nummer: Optional[str] = None
    uurtarief: Optional[float] = None
    notities: Optional[str] = None
    scope: Optional[str] = "zakelijk"  # standaard zakelijk, kan ook prive (particulier)
    # v13d_client_book_type_001 (sessie 56b) — Willem: "zorg krijgt zorg-dossier,
    # shop krijgt klant-facturatie, prive krijgt algemene client. Zelfde format,
    # andere velden per book-type."
    book_id: Optional[str] = None  # koppel client aan boek
    client_type: Optional[str] = "generiek"  # 'zorgclient' | 'klant' | 'generiek'
    # Zorg-specifieke placeholders
    geboortedatum: Optional[str] = None
    bsn: Optional[str] = None
    zorgindicatie: Optional[str] = None
    huisarts: Optional[str] = None
    noodcontact: Optional[str] = None
    # Klant-specifieke placeholders (facturatie)
    factuur_adres: Optional[str] = None
    betalingstermijn_dagen: Optional[int] = 14


class ClientUpdate(BaseModel):
    naam: Optional[str] = None
    contactpersoon: Optional[str] = None
    email: Optional[str] = None
    telefoon: Optional[str] = None
    adres: Optional[str] = None
    postcode: Optional[str] = None
    plaats: Optional[str] = None
    kvk: Optional[str] = None
    btw_nummer: Optional[str] = None
    uurtarief: Optional[float] = None
    notities: Optional[str] = None
    scope: Optional[str] = None
    book_id: Optional[str] = None
    client_type: Optional[str] = None
    geboortedatum: Optional[str] = None
    bsn: Optional[str] = None
    zorgindicatie: Optional[str] = None
    huisarts: Optional[str] = None
    noodcontact: Optional[str] = None
    factuur_adres: Optional[str] = None
    betalingstermijn_dagen: Optional[int] = None


class DossierEntry(BaseModel):
    kop: str
    inhoud: str = ""
    bron: Optional[str] = "handmatig"  # 'handmatig' | 'chat' | 'agenda' | 'boekhouding'


class SparkLearning(BaseModel):
    inhoud: str
    bron: Optional[str] = "chat"
    context: Optional[str] = None  # bv. gesprekref


def _get_file(user_id: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"{user_id}.json"


@router.get("/index/{user_id}")
async def list_clienten(user_id: str, viewer_id: Optional[str] = None, book_id: Optional[str] = None):
    """Compacte lijst — bedoeld voor dropdown-koppeling in agenda/boekhouding.
    Filter optioneel op book_id (voor per-book weergave)."""
    from modules.core.privacy import require_access
    require_access(viewer_id or user_id, user_id)
    data = load_json(_get_file(user_id), default={"clienten": []})
    clienten = data.get("clienten", [])
    if book_id:
        clienten = [c for c in clienten if c.get("book_id") == book_id]
    return {"clienten": [
        {"id": c["id"], "naam": c["naam"], "contactpersoon": c.get("contactpersoon"),
         "uurtarief": c.get("uurtarief"), "scope": c.get("scope", "zakelijk"),
         "book_id": c.get("book_id"), "client_type": c.get("client_type", "generiek")}
        for c in clienten
    ]}


@router.get("/list/{user_id}")
async def get_full_clienten(user_id: str, viewer_id: Optional[str] = None, book_id: Optional[str] = None):
    """Volledige lijst met alle velden. Filter optioneel op book_id."""
    from modules.core.privacy import require_access
    require_access(viewer_id or user_id, user_id)
    data = load_json(_get_file(user_id), default={"clienten": []})
    if book_id:
        return {"clienten": [c for c in data.get("clienten", []) if c.get("book_id") == book_id]}
    return data


@router.get("/detail/{user_id}/{client_id}")
async def get_client_detail(user_id: str, client_id: str, viewer_id: Optional[str] = None):
    from modules.core.privacy import require_access
    require_access(viewer_id or user_id, user_id)
    data = load_json(_get_file(user_id), default={"clienten": []})
    for c in data.get("clienten", []):
        if c["id"] == client_id:
            return c
    raise HTTPException(404, "Client niet gevonden")


@router.post("/create/{user_id}")
async def create_client(user_id: str, client: ClientCreate):
    fpath = _get_file(user_id)
    data = load_json(fpath, default={"clienten": []})
    scope = client.scope if client.scope in ("zakelijk", "prive") else "zakelijk"
    client_type = client.client_type if client.client_type in ("zorgclient", "klant", "generiek") else "generiek"
    new_client = {
        "id": str(uuid.uuid4())[:8],
        "naam": client.naam,
        "contactpersoon": client.contactpersoon,
        "email": client.email,
        "telefoon": client.telefoon,
        "adres": client.adres,
        "postcode": client.postcode,
        "plaats": client.plaats,
        "kvk": client.kvk,
        "btw_nummer": client.btw_nummer,
        "uurtarief": client.uurtarief,
        "notities": client.notities,
        "scope": scope,
        "book_id": client.book_id,
        "client_type": client_type,
        # Zorg-velden
        "geboortedatum": client.geboortedatum,
        "bsn": client.bsn,
        "zorgindicatie": client.zorgindicatie,
        "huisarts": client.huisarts,
        "noodcontact": client.noodcontact,
        # Klant/factuur-velden
        "factuur_adres": client.factuur_adres,
        "betalingstermijn_dagen": client.betalingstermijn_dagen,
        "aangemaakt_op": datetime.now(timezone.utc).isoformat(),
        "aangemaakt_door": user_id,
        "dossier": [],
        "spark_learnings": [],
    }
    data.setdefault("clienten", []).append(new_client)
    save_json(fpath, data)
    return {"success": True, "client": new_client}


@router.put("/update/{user_id}/{client_id}")
async def update_client(user_id: str, client_id: str, updates: ClientUpdate):
    fpath = _get_file(user_id)
    data = load_json(fpath, default={"clienten": []})
    for c in data.get("clienten", []):
        if c["id"] == client_id:
            for k, v in updates.model_dump(exclude_none=True).items():
                c[k] = v
            c["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_json(fpath, data)
            return {"success": True, "client": c}
    raise HTTPException(404, "Client niet gevonden")


@router.delete("/delete/{user_id}/{client_id}")
async def delete_client(user_id: str, client_id: str):
    fpath = _get_file(user_id)
    data = load_json(fpath, default={"clienten": []})
    before = len(data.get("clienten", []))
    data["clienten"] = [c for c in data.get("clienten", []) if c["id"] != client_id]
    if len(data["clienten"]) == before:
        raise HTTPException(404, "Client niet gevonden")
    save_json(fpath, data)
    return {"success": True}


@router.post("/dossier/{user_id}/{client_id}")
async def add_dossier_entry(user_id: str, client_id: str, entry: DossierEntry):
    """Voeg dossier-entry toe (handmatig of via chat)."""
    fpath = _get_file(user_id)
    data = load_json(fpath, default={"clienten": []})
    for c in data.get("clienten", []):
        if c["id"] == client_id:
            c.setdefault("dossier", []).append({
                "id": str(uuid.uuid4())[:8],
                "kop": entry.kop,
                "inhoud": entry.inhoud,
                "bron": entry.bron or "handmatig",
                "aangemaakt_op": datetime.now(timezone.utc).isoformat(),
            })
            save_json(fpath, data)
            return {"success": True, "dossier_entries": len(c["dossier"])}
    raise HTTPException(404, "Client niet gevonden")


@router.post("/learning/{user_id}/{client_id}")
async def add_spark_learning(user_id: str, client_id: str, learning: SparkLearning):
    """Spark gebruikt dit endpoint om geleerde info bij client op te slaan.
    Willem: 'als spark wat leert over client kan hij gebonden info hier wegzetten'."""
    fpath = _get_file(user_id)
    data = load_json(fpath, default={"clienten": []})
    for c in data.get("clienten", []):
        if c["id"] == client_id:
            c.setdefault("spark_learnings", []).append({
                "id": str(uuid.uuid4())[:8],
                "inhoud": learning.inhoud,
                "bron": learning.bron or "chat",
                "context": learning.context,
                "aangemaakt_op": datetime.now(timezone.utc).isoformat(),
            })
            save_json(fpath, data)
            return {"success": True, "learning_count": len(c["spark_learnings"])}
    raise HTTPException(404, "Client niet gevonden")
