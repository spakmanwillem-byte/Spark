"""
Container — FastAPI routes (v6_container_001)
==============================================
Generieke container CRUD + user-specifieke acties.

  POST   /api/container/{type}                        : create
  GET    /api/container/{type}                        : list
  GET    /api/container/{type}/{id}/meta              : read meta
  PATCH  /api/container/{type}/{id}/meta              : update meta (admin)
  POST   /api/container/{type}/{id}/tag-for-deletion  : tag-for-deletion
  DELETE /api/container/{type}/{id}                   : finalize delete (archive + cross-ref clean)
"""
from modules.core.paths import SPARK_ROOT  # v14_spark_root_001
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.synapse.schema import VALID_CONTAINER_TYPES, VALID_STATUSES
from .service import (
    create_container, list_containers, read_meta, update_meta,
    tag_for_deletion, delete_container, container_exists,
)

router = APIRouter(prefix="/container", tags=["container"])


def _check_admin(viewer_id: Optional[str]) -> bool:
    """Lichte admin-check via users.json gradatie ≤ 2."""
    if not viewer_id:
        return False
    try:
        from modules.core.storage import load_json
        users = load_json(Path(f"{SPARK_ROOT}/backend/data/system/users.json"), default={"users": []}).get("users", [])
        for u in users:
            if u.get("id") == viewer_id:
                return (u.get("gradatie") or 7) <= 2
    except Exception:
        return False
    return False


# ============================================================
# CREATE
# ============================================================
class CreateBody(BaseModel):
    container_id: str
    naam: Optional[str] = None
    doel: str = ""
    owner: Optional[str] = None
    blueprint_ref: Optional[str] = None
    footnote: str = ""
    extra: Optional[Dict[str, Any]] = None


@router.post("/{container_type}")
async def create(container_type: str, body: CreateBody):
    if container_type not in VALID_CONTAINER_TYPES:
        raise HTTPException(400, f"Ongeldig container_type. Geldig: {sorted(VALID_CONTAINER_TYPES)}")
    meta = create_container(
        container_type, body.container_id,
        naam=body.naam, doel=body.doel,
        owner=body.owner, blueprint_ref=body.blueprint_ref,
        footnote=body.footnote, extra=body.extra,
    )
    return {"success": True, "meta": meta}


# ============================================================
# LIST
# ============================================================
@router.get("/{container_type}")
async def list_all(container_type: str):
    if container_type not in VALID_CONTAINER_TYPES:
        raise HTTPException(400, "Ongeldig container_type")
    return {
        "container_type": container_type,
        "items": list_containers(container_type),
    }


# ============================================================
# READ
# ============================================================
@router.get("/{container_type}/{container_id}/meta")
async def get_meta(container_type: str, container_id: str):
    if not container_exists(container_type, container_id):
        raise HTTPException(404, "Container niet gevonden")
    return read_meta(container_type, container_id)


# ============================================================
# UPDATE META
# ============================================================
class PatchBody(BaseModel):
    viewer_id: Optional[str] = None
    doel: Optional[str] = None
    footnote: Optional[str] = None
    blueprint_ref: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    owner: Optional[str] = None


@router.patch("/{container_type}/{container_id}/meta")
async def patch_meta(container_type: str, container_id: str, body: PatchBody):
    if not container_exists(container_type, container_id):
        raise HTTPException(404, "Container niet gevonden")
    patch: Dict[str, Any] = {}
    if body.doel is not None:
        patch["doel"] = body.doel
    if body.footnote is not None:
        patch["footnote"] = body.footnote
    if body.blueprint_ref is not None:
        patch["blueprint_ref"] = body.blueprint_ref
    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(400, f"Ongeldige status. Geldig: {sorted(VALID_STATUSES)}")
        patch["status"] = body.status
    if body.tags is not None:
        patch["tags"] = body.tags
    if body.owner is not None:
        patch["owner"] = body.owner
    meta = update_meta(container_type, container_id, patch)
    return {"success": True, "meta": meta}


# ============================================================
# DELETE (3-fase)
# ============================================================
class TagDeleteBody(BaseModel):
    viewer_id: Optional[str] = None
    reason: str = ""


@router.post("/{container_type}/{container_id}/tag-for-deletion")
async def tag_delete(container_type: str, container_id: str, body: TagDeleteBody):
    """Stap 1: markeer container als 'klaar voor verwijdering' (revertable)."""
    if not container_exists(container_type, container_id):
        raise HTTPException(404, "Container niet gevonden")
    meta = tag_for_deletion(container_type, container_id, reason=body.reason)
    return {"success": True, "meta": meta}


class FinalDeleteBody(BaseModel):
    viewer_id: str
    keep_archive: bool = True
    anonymize_cross_refs: bool = True


@router.delete("/{container_type}/{container_id}")
async def finalize_delete(container_type: str, container_id: str, viewer_id: str,
                          keep_archive: bool = True, anonymize_cross_refs: bool = True):
    """Stap 2: definitief weg. Container → _deleted_containers + cross-refs anoniem.

    Admin-only.
    """
    if not _check_admin(viewer_id):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2) kan een container definitief verwijderen")
    if not container_exists(container_type, container_id):
        raise HTTPException(404, "Container niet gevonden")
    result = delete_container(
        container_type, container_id,
        anonymize_cross_refs=anonymize_cross_refs,
        keep_archive=keep_archive,
    )
    return result


# ============================================================
# v6_container_migrate_001 — Legacy → Container migratie endpoints
# ============================================================
class MigrateUserBody(BaseModel):
    viewer_id: str
    user_id: str


@router.post("/user/migrate")
async def migrate_one_user(body: MigrateUserBody):
    """Kopieer legacy user-data naar nieuwe user-container. Idempotent."""
    if not _check_admin(body.viewer_id):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2) kan migratie triggeren")
    from .user_helper import migrate_user_legacy
    return migrate_user_legacy(body.user_id)


@router.post("/user/migrate-all")
async def migrate_all_users_endpoint(viewer_id: str):
    """Bulk-migratie voor alle users. Idempotent. Geeft per-user resultaat."""
    if not _check_admin(viewer_id):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2) kan bulk-migratie triggeren")
    from .user_helper import migrate_all_users
    return migrate_all_users()
