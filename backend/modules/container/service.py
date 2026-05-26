"""
Container service (v6_container_001) — generieke container CRUD
================================================================
Universeel patroon. Vandaag voor users; morgen ook shop/asset/card/thread.

  create_container(type, id, ...)  : maakt dir + _meta.json
  get_container_path(type, id)     : pad zonder side-effects
  get_resource_path(type, id, res) : pad naar resource binnen container
  touch_container(type, id)        : last_touched + activity_count++
  delete_container(type, id, ...)  : status=deleting → archive → status=deleted
  list_containers(type)            : alle ids
"""
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.core.storage import load_json, save_json
from modules.synapse.schema import (
    new_meta, now_iso,
    CONTAINER_USER, CONTAINER_SHOP, CONTAINER_ASSET, CONTAINER_CARD, CONTAINER_THREAD,
    STATUS_ACTIVE, STATUS_DELETED, STATUS_TAGGED_FOR_DELETION,
)

DATA_ROOT = Path("/app/backend/data")
DELETED_ROOT = DATA_ROOT / "_deleted_containers"


# Map container_type → directory naam onder /data
TYPE_DIRS = {
    CONTAINER_USER: "users",
    CONTAINER_SHOP: "shops",
    CONTAINER_ASSET: "assets",
    CONTAINER_CARD: "container_cards",
    CONTAINER_THREAD: "container_threads",
}


# ============================================================
# PATH HELPERS
# ============================================================
def get_type_dir(container_type: str) -> Path:
    if container_type not in TYPE_DIRS:
        raise ValueError(f"Onbekend container_type: {container_type}")
    return DATA_ROOT / TYPE_DIRS[container_type]


def get_container_path(container_type: str, container_id: str) -> Path:
    return get_type_dir(container_type) / container_id


def get_resource_path(container_type: str, container_id: str, resource: str) -> Path:
    """Pad naar bv. users/{uid}/notes.json of users/{uid}/archive/foto/x.jpg."""
    return get_container_path(container_type, container_id) / resource


def container_exists(container_type: str, container_id: str) -> bool:
    p = get_container_path(container_type, container_id)
    return p.exists() and (p / "_meta.json").exists()


# ============================================================
# CREATE
# ============================================================
def create_container(
    container_type: str,
    container_id: str,
    *,
    naam: Optional[str] = None,
    doel: str = "",
    owner: Optional[str] = None,
    blueprint_ref: Optional[str] = None,
    footnote: str = "",
    extra: Optional[Dict[str, Any]] = None,
    overwrite: bool = False,
) -> Dict[str, Any]:
    """Maak nieuwe container met _meta.json.

    Returns meta dict.
    """
    cp = get_container_path(container_type, container_id)
    if cp.exists() and not overwrite:
        existing = load_json(cp / "_meta.json", default={})
        if existing:
            return existing  # idempotent
    cp.mkdir(parents=True, exist_ok=True)
    meta = new_meta(
        naam=naam or container_id,
        doel=doel or f"{container_type}-container voor {container_id}",
        container_type=container_type,
        status=STATUS_ACTIVE,
        owner=owner or "spark-system",
        blueprint_ref=blueprint_ref,
        footnote=footnote,
        extra=extra or {},
    )
    meta["container_id"] = container_id
    save_json(cp / "_meta.json", meta)
    return meta


def read_meta(container_type: str, container_id: str) -> Dict[str, Any]:
    return load_json(get_container_path(container_type, container_id) / "_meta.json", default={})


def update_meta(container_type: str, container_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    meta = read_meta(container_type, container_id)
    if not meta:
        raise FileNotFoundError(f"Container {container_type}/{container_id} bestaat niet")
    # Beschermde auto-velden niet via patch overschrijven
    auto = {"_arch_ref", "schema_version", "container_type", "created_at"}
    for k, v in patch.items():
        if k not in auto:
            meta[k] = v
    meta["last_touched"] = now_iso()
    save_json(get_container_path(container_type, container_id) / "_meta.json", meta)
    return meta


# ============================================================
# TOUCH
# ============================================================
def touch_container(container_type: str, container_id: str) -> bool:
    cp = get_container_path(container_type, container_id)
    mp = cp / "_meta.json"
    if not mp.exists():
        return False
    meta = load_json(mp, default={})
    meta["last_touched"] = now_iso()
    meta["activity_count"] = int(meta.get("activity_count", 0)) + 1
    save_json(mp, meta)
    return True


# ============================================================
# DELETE (3-fase: tag → archive → cleanup-cross-refs)
# ============================================================
def tag_for_deletion(container_type: str, container_id: str, reason: str = "") -> Dict[str, Any]:
    meta = read_meta(container_type, container_id)
    if not meta:
        raise FileNotFoundError(f"Container niet gevonden: {container_type}/{container_id}")
    meta["status"] = STATUS_TAGGED_FOR_DELETION
    meta["tagged_for_deletion_at"] = now_iso()
    if reason:
        meta["deletion_reason"] = reason
    save_json(get_container_path(container_type, container_id) / "_meta.json", meta)
    return meta


def delete_container(
    container_type: str,
    container_id: str,
    *,
    anonymize_cross_refs: bool = True,
    keep_archive: bool = True,
) -> Dict[str, Any]:
    """Daadwerkelijke verwijdering met archive-fallback.

    Stappen:
      1. Tag → deleted
      2. Anonimiseer cross-refs in andere data (notes/community/etc → '[verwijderde gebruiker]')
      3. Verplaats container naar _deleted_containers/{type}/{id}_{timestamp}/
    """
    cp = get_container_path(container_type, container_id)
    if not cp.exists():
        return {"success": False, "error": "container niet gevonden"}

    # 1. Tag
    meta = read_meta(container_type, container_id) or {}
    meta["status"] = STATUS_DELETED
    meta["deleted_at"] = now_iso()

    # 2. Cross-refs anonimiseren (user-specifiek nu; hook later voor andere types)
    cross_refs_cleaned = {}
    if anonymize_cross_refs and container_type == CONTAINER_USER:
        from .user_helper import anonymize_user_cross_refs
        cross_refs_cleaned = anonymize_user_cross_refs(container_id)

    meta["cross_refs_cleaned"] = cross_refs_cleaned
    save_json(cp / "_meta.json", meta)

    # 3. Verplaats naar archive of definitief weg
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if keep_archive:
        archive_dir = DELETED_ROOT / TYPE_DIRS[container_type] / f"{container_id}_{timestamp}"
        archive_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(cp), str(archive_dir))
        return {
            "success": True,
            "container_type": container_type,
            "container_id": container_id,
            "archived_to": str(archive_dir),
            "cross_refs_cleaned": cross_refs_cleaned,
        }
    else:
        shutil.rmtree(str(cp))
        return {
            "success": True,
            "container_type": container_type,
            "container_id": container_id,
            "archived_to": None,
            "cross_refs_cleaned": cross_refs_cleaned,
        }


# ============================================================
# LIST
# ============================================================
def list_containers(container_type: str) -> List[Dict[str, Any]]:
    td = get_type_dir(container_type)
    if not td.exists():
        return []
    out = []
    for sub in sorted(td.iterdir()):
        if not sub.is_dir():
            continue
        meta_path = sub / "_meta.json"
        if not meta_path.exists():
            continue
        m = load_json(meta_path, default={})
        if not m:
            continue
        out.append({
            "container_id": m.get("container_id") or sub.name,
            "container_type": container_type,
            "naam": m.get("naam"),
            "status": m.get("status"),
            "last_touched": m.get("last_touched"),
            "activity_count": m.get("activity_count", 0),
            "owner": m.get("owner"),
        })
    return out
