"""
Synapse — Meta-schema definitie (v6_synapse_001)
=================================================
Eén schema voor alle types containers/mappen.
Spark leest deze velden om zichzelf te kennen.
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


# Toegestane statussen
STATUS_ACTIVE = "active"
STATUS_SKELETON = "skeleton"
STATUS_WIP = "wip"
STATUS_DEPRECATED = "deprecated"
STATUS_TAGGED_FOR_DELETION = "tagged_for_deletion"
STATUS_DELETED = "deleted"

VALID_STATUSES = {
    STATUS_ACTIVE, STATUS_SKELETON, STATUS_WIP,
    STATUS_DEPRECATED, STATUS_TAGGED_FOR_DELETION, STATUS_DELETED,
}

# Container-types (F4)
CONTAINER_DIR = "dir"            # gewone map (backend/module, frontend/component)
CONTAINER_DATA = "data"          # data-folder (json-store)
CONTAINER_USER = "user"          # users/{id}/ container
CONTAINER_SHOP = "shop"          # shops/{id}/ container (Winkelstraat)
CONTAINER_ASSET = "asset"        # losse mediabestand-container
CONTAINER_CARD = "card"          # kb-card of dnd-card als container
CONTAINER_THREAD = "thread"      # chat-thread privé/community

VALID_CONTAINER_TYPES = {
    CONTAINER_DIR, CONTAINER_DATA, CONTAINER_USER, CONTAINER_SHOP,
    CONTAINER_ASSET, CONTAINER_CARD, CONTAINER_THREAD,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_encryption_slot() -> Dict[str, Any]:
    """Lege encryption-slot — toegevoegd vanaf dag 1, gevuld bij F2F-feature later."""
    return {
        "enabled": False,
        "algorithm": None,    # bv. "AES-256-GCM"
        "key_id": None,       # ref naar key in keystore
        "key_holder": None,   # bv. "user-001" of "spark-system"
    }


def new_meta(
    *,
    naam: str,
    doel: str = "",
    container_type: str = CONTAINER_DIR,
    status: str = STATUS_ACTIVE,
    owner: str = "spark-system",
    blueprint_ref: Optional[str] = None,
    footnote: str = "",
    split_from: Optional[str] = None,
    children_max: int = 4,
    endpoints: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construeer een vers _meta.json record."""
    if container_type not in VALID_CONTAINER_TYPES:
        container_type = CONTAINER_DIR
    if status not in VALID_STATUSES:
        status = STATUS_ACTIVE
    iso = now_iso()
    return {
        "_arch_ref": "v6_synapse_001",
        "schema_version": "1.0",
        "naam": naam,
        "doel": doel or f"({naam} — geen doel-omschrijving)",
        "container_type": container_type,
        "status": status,
        "owner": owner,
        "blueprint_ref": blueprint_ref,
        "footnote": footnote,
        "split_from": split_from,
        "children_max": children_max,
        "endpoints": endpoints or [],
        "tags": tags or [],
        "encryption": empty_encryption_slot(),
        "created_at": iso,
        "last_touched": iso,
        "activity_count": 0,
        "file_count": 0,
        "subdir_count": 0,
        "extra": extra or {},
    }


def merge_meta(existing: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge nieuwe scan-data over bestaande meta:
      - Beschermt user-edits: status/footnote/blueprint_ref/doel/tags blijven indien al ingevuld
      - Werkt automatische velden bij: file_count, subdir_count, endpoints, last_touched
    """
    if not existing:
        return new_data
    out = dict(existing)
    # Beschermde velden — alleen overschrijven als bestaande leeg/default is
    protected = ["doel", "footnote", "blueprint_ref", "tags", "owner", "split_from"]
    for k in protected:
        if k not in out or out.get(k) in (None, "", []):
            out[k] = new_data.get(k, out.get(k))
    # Status alleen wijzigen als ie nog "skeleton" was en nu code/files heeft
    if out.get("status") == STATUS_SKELETON and new_data.get("file_count", 0) > 1:
        out["status"] = STATUS_ACTIVE
    # Automatische velden — altijd overschrijven met scan-resultaat
    auto_fields = ["container_type", "endpoints", "file_count", "subdir_count", "_arch_ref", "schema_version"]
    for k in auto_fields:
        if k in new_data:
            out[k] = new_data[k]
    # Encryption slot: behoud user-keuze
    if "encryption" not in out:
        out["encryption"] = empty_encryption_slot()
    # Created_at behouden, last_touched bij scan niet bumpen (alleen bij echte touch)
    return out
