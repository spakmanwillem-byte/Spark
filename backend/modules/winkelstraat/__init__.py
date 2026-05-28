"""
Winkelstraat — multi-tenant shop architecture (v6_winkelstraat_001)
================================================================================
- GET  /api/winkelstraat/shops              → lijst alle shops
- GET  /api/winkelstraat/shops/{shop_id}    → 1 shop
- GET  /api/winkelstraat/voorwaarden        → standaard voorwaarden + commissie
- POST /api/winkelstraat/shops              → nieuwe shop aanmaken (gradatie ≥ 4)
- PATCH /api/winkelstraat/shops/{shop_id}   → bewerken (alleen owner)
- POST /api/winkelstraat/shops/{shop_id}/close → sluiting-verzoek
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/winkelstraat", tags=["winkelstraat"])

SHOPS_FILE = Path(__file__).parent.parent.parent / "data" / "shop" / "shops.json"
USERS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"


def _load_shops() -> dict:
    return load_json(SHOPS_FILE, default={"shops": [], "commissie_default_pct": 2.0, "min_gradatie_to_open": 4})


def _save_shops(d: dict) -> None:
    save_json(SHOPS_FILE, d)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_user_gradatie(user_id: str) -> int:
    try:
        users_data = load_json(USERS_FILE, default={"users": []})
        users = users_data.get("users", []) if isinstance(users_data, dict) else users_data
        for u in users:
            if u.get("id") == user_id or u.get("user_id") == user_id:
                return int(u.get("gradatie", 1) or 1)
    except Exception:
        pass
    return 1


# ---------- LIST + GET ----------

@router.get("/shops")
async def list_shops():
    d = _load_shops()
    shops = d.get("shops", [])
    # v6_shop_visuals_001 (28 mei) — enrich met owner_avatar_url uit users.json
    try:
        users_data = load_json(USERS_FILE, default={"users": []})
        users = users_data.get("users", []) if isinstance(users_data, dict) else users_data
        user_map = {u.get("id"): u for u in users if u.get("id")}
        for s in shops:
            owner = user_map.get(s.get("owner_user_id"))
            if owner:
                s["owner_avatar_url"] = owner.get("avatar_url") or owner.get("avatar")
                if not s.get("owner_naam"):
                    s["owner_naam"] = owner.get("naam") or owner.get("name")
    except Exception:
        pass
    return {
        "success": True,
        "count": len(shops),
        "shops": shops,
        "commissie_default_pct": d.get("commissie_default_pct", 2.0),
        "min_gradatie_to_open": d.get("min_gradatie_to_open", 4),
    }


@router.get("/shops/{shop_id}")
async def get_shop(shop_id: str):
    d = _load_shops()
    shop = next((s for s in d.get("shops", []) if s.get("id") == shop_id), None)
    if not shop:
        raise HTTPException(404, f"Shop '{shop_id}' niet gevonden")
    return {"success": True, "shop": shop}


@router.get("/voorwaarden")
async def get_voorwaarden():
    d = _load_shops()
    return {
        "success": True,
        "voorwaarden": d.get("voorwaarden_template", {}),
        "commissie_default_pct": d.get("commissie_default_pct", 2.0),
        "min_gradatie_to_open": d.get("min_gradatie_to_open", 4),
    }


# ---------- CREATE ----------

class CreateShopBody(BaseModel):
    naam: str
    type: str = "hybride"  # merch / digitaal / hybride
    owner_user_id: str
    owner_naam: Optional[str] = None
    tagline: Optional[str] = None
    color_accent: Optional[str] = None
    voorwaarden_geaccepteerd: bool = False
    subtabs_enabled: Optional[List[str]] = None


@router.post("/shops")
async def create_shop(body: CreateShopBody):
    """Nieuwe winkel — vereist gradatie ≥ 4 + voorwaarden geaccepteerd."""
    if not body.voorwaarden_geaccepteerd:
        raise HTTPException(400, "Voorwaarden moeten worden geaccepteerd voordat een winkel wordt aangemaakt.")
    grad = _get_user_gradatie(body.owner_user_id)
    d = _load_shops()
    min_grad = int(d.get("min_gradatie_to_open", 4))
    # Admin (gradatie ≤ 2) mag altijd; anderen moeten gradatie ≥ min_grad hebben
    is_admin = grad <= 2
    if not is_admin and grad < min_grad:
        raise HTTPException(403, f"Gradatie {grad} is te laag — minimum gradatie {min_grad} vereist om een winkel te openen.")

    # Owner mag maximaal 3 actieve shops hebben (placeholder voor donderdag)
    own_active = sum(1 for s in d.get("shops", [])
                     if s.get("owner_user_id") == body.owner_user_id and s.get("status") == "active")
    if own_active >= 3:
        raise HTTPException(429, f"Maximaal 3 actieve winkels per gebruiker. Je hebt er nu {own_active}.")

    new_shop = {
        "id": f"shop-{uuid.uuid4().hex[:10]}",
        "naam": body.naam,
        "type": body.type,
        "owner_user_id": body.owner_user_id,
        "owner_naam": body.owner_naam,
        "subtabs_enabled": body.subtabs_enabled or (["merch", "digitaal"] if body.type == "hybride" else [body.type]),
        "commissie_pct": d.get("commissie_default_pct", 2.0),
        "is_founder_shop": False,
        "status": "active",
        "created_at": _now(),
        "tagline": body.tagline,
        "color_accent": body.color_accent or "#f59e0b",
        "voorwaarden_geaccepteerd_op": _now(),
        "voorwaarden_geaccepteerd_versie": (d.get("voorwaarden_template") or {}).get("version", "v1"),
        "metadata": {
            "openings_gradatie": grad,
            "exempt_from_commissie": False,
        },
    }
    d.setdefault("shops", []).append(new_shop)
    _save_shops(d)

    # v6_container_001 F7 — Maak ook een shop-container met _meta.json zodat:
    #  - producten/orders/listing-fotos per shop geïsoleerd staan
    #  - bij sluiting de hele container weg kan zonder cross-pollution
    #  - encryption-slot reeds aanwezig voor F2F-secure shops later
    try:
        from modules.container.service import create_container
        from modules.synapse.schema import CONTAINER_SHOP
        create_container(
            CONTAINER_SHOP, new_shop["id"],
            naam=new_shop["naam"],
            doel=f"Shop-container voor {new_shop['naam']} ({new_shop['type']}, owner: {new_shop['owner_user_id']})",
            owner=new_shop["owner_user_id"],
            footnote=f"Commissie: {new_shop['commissie_pct']}% naar Spark. Bij sluiting: container archiveren.",
            extra={
                "commissie_pct": new_shop["commissie_pct"],
                "type": new_shop["type"],
                "openings_gradatie": grad,
            },
        )
    except Exception as _ex:
        print(f"[winkelstraat] container create voor {new_shop['id']} faalde: {_ex}")

    return {"success": True, "shop": new_shop,
            "message": f"Winkel '{body.naam}' aangemaakt. Commissie {new_shop['commissie_pct']}%."}


# ---------- PATCH (owner only) ----------

class UpdateShopBody(BaseModel):
    actor_user_id: str
    patch: dict


@router.patch("/shops/{shop_id}")
async def update_shop(shop_id: str, body: UpdateShopBody):
    d = _load_shops()
    shop = next((s for s in d.get("shops", []) if s.get("id") == shop_id), None)
    if not shop:
        raise HTTPException(404, "Shop niet gevonden")
    if shop.get("owner_user_id") != body.actor_user_id:
        raise HTTPException(403, "Alleen owner kan deze winkel bewerken.")
    # Witte lijst van editbare velden
    editable = {"naam", "tagline", "color_accent", "subtabs_enabled", "type", "logo_url"}
    for k, v in (body.patch or {}).items():
        if k in editable:
            shop[k] = v
    shop["last_edited_at"] = _now()
    _save_shops(d)
    return {"success": True, "shop": shop}


# ---------- CLOSE request ----------

class CloseShopBody(BaseModel):
    actor_user_id: str
    reden: Optional[str] = None


@router.post("/shops/{shop_id}/close")
async def close_shop(shop_id: str, body: CloseShopBody):
    d = _load_shops()
    shop = next((s for s in d.get("shops", []) if s.get("id") == shop_id), None)
    if not shop:
        raise HTTPException(404, "Shop niet gevonden")
    if shop.get("owner_user_id") != body.actor_user_id:
        raise HTTPException(403, "Alleen owner kan sluiting aanvragen.")
    shop["status"] = "closing"
    shop["close_requested_at"] = _now()
    shop["close_reden"] = body.reden
    _save_shops(d)

    # v6_container_001 F7 — Tag shop-container voor verwijdering (revertable).
    # Definitieve cleanup gebeurt later via admin via /api/container/shop/{id} DELETE.
    try:
        from modules.container.service import tag_for_deletion, container_exists
        from modules.synapse.schema import CONTAINER_SHOP
        if container_exists(CONTAINER_SHOP, shop_id):
            tag_for_deletion(CONTAINER_SHOP, shop_id, reason=body.reden or "Owner-verzoek sluiting")
    except Exception as _ex:
        print(f"[winkelstraat] container tag-for-deletion voor {shop_id} faalde: {_ex}")

    return {"success": True, "shop": shop,
            "message": "Sluitings-verzoek geregistreerd. Producten worden gearchiveerd, openstaande orders nog afgehandeld."}


# ---------- LOGO UPLOAD (v6_shop_visuals_001) ----------

from fastapi import UploadFile, File, Form
import shutil, os


@router.post("/shops/{shop_id}/logo")
async def upload_shop_logo(shop_id: str, logo: UploadFile = File(...), actor_user_id: str = Form(...)):
    """Upload shop-logo. Alleen owner. Slaat op in /data/users/{owner}/shops/{shop_id}/logo.{ext}."""
    d = _load_shops()
    shop = next((s for s in d.get("shops", []) if s.get("id") == shop_id), None)
    if not shop:
        raise HTTPException(404, "Shop niet gevonden")
    if shop.get("owner_user_id") != actor_user_id:
        raise HTTPException(403, "Alleen owner kan logo uploaden.")
    if not logo.content_type or not logo.content_type.startswith("image/"):
        raise HTTPException(400, "Alleen images toegestaan")
    ext = (logo.filename or "logo.png").split(".")[-1].lower()
    if ext not in ("png", "jpg", "jpeg", "webp", "svg"):
        ext = "png"
    owner = shop["owner_user_id"]
    target_dir = Path(__file__).parent.parent.parent / "data" / "users" / owner / "shops" / shop_id
    os.makedirs(target_dir, exist_ok=True)
    target = target_dir / f"logo.{ext}"
    with open(target, "wb") as f:
        shutil.copyfileobj(logo.file, f)
    # Static URL via /api/shop/container-static/{shop_id}/logo.{ext}
    rel_url = f"/api/winkelstraat/shops/{shop_id}/logo.{ext}"
    shop["logo_url"] = rel_url
    shop["logo_uploaded_at"] = _now()
    _save_shops(d)
    return {"success": True, "logo_url": rel_url, "shop": shop}


@router.get("/shops/{shop_id}/logo.{ext}")
async def serve_shop_logo(shop_id: str, ext: str):
    """Static serve van shop-logo."""
    from fastapi.responses import FileResponse
    d = _load_shops()
    shop = next((s for s in d.get("shops", []) if s.get("id") == shop_id), None)
    if not shop:
        raise HTTPException(404, "Shop niet gevonden")
    owner = shop["owner_user_id"]
    path = Path(__file__).parent.parent.parent / "data" / "users" / owner / "shops" / shop_id / f"logo.{ext}"
    if not path.exists():
        raise HTTPException(404, "Logo niet gevonden")
    return FileResponse(str(path))
