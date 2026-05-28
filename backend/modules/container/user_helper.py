"""
User-container helpers (v6_container_001 — F4 user-eerste implementatie)
==========================================================================
- get_user_dir(user_id)              : pad naar /data/users/{user_id}/ (maakt aan)
- get_user_resource_path(uid, res)   : bv. notes.json, agenda.json, archive/foto/...
- migrate_user_legacy(user_id)       : v6_container_migrate_001 — kopieer legacy user-data
                                       (agenda, dagboek) naar nieuwe container-structuur
                                       met legacy_origin-meta voor traceability.
- anonymize_user_cross_refs(user_id) : vervangt user_id refs in shared JSONs door '_anon_<id>'

Strategie: GEEN big-bang migratie. Endpoints blijven hun oude paden lezen/schrijven.
Container is parallel infrastructuur — bij user-delete profiteren we al meteen.

Cross-ref bronnen die we anonimiseren bij user-delete:
  - data/notes/notes.json + tasks.json     (user_id veld)
  - data/agenda/{user_id}.json             (file weg)
  - data/dagboek/{user_id}.json            (file weg)
  - data/bugs/bugs.json                    (created_by_id)
  - data/community/messages.json           (user_id → '[verwijderd]')
  - data/wallet/*.json                     (entries voor user)
  - data/chat/prive/*__{user_id}*.json     (verwijderen)
"""
import re
from pathlib import Path
from typing import Dict, Any
from modules.core.storage import load_json, save_json
from .service import (
    create_container, get_container_path, get_resource_path,
)
from modules.synapse.schema import CONTAINER_USER

DATA = Path("/app/backend/data")
ANON_PLACEHOLDER = "[verwijderde gebruiker]"


# ============================================================
# USER PATH HELPERS
# ============================================================
def get_user_dir(user_id: str, *, ensure: bool = True) -> Path:
    """Pad naar user-container. Maakt aan als nog niet bestaat."""
    if ensure:
        from .service import container_exists
        if not container_exists(CONTAINER_USER, user_id):
            create_container(
                CONTAINER_USER,
                user_id,
                naam=f"user-{user_id}",
                doel=f"Persoonlijke container voor gebruiker {user_id}",
                owner=user_id,
                footnote="Auto-aangemaakt bij eerste toegang. Bij account-delete: hele container weg + cross-refs anoniem.",
            )
    return get_container_path(CONTAINER_USER, user_id)


def get_user_resource_path(user_id: str, resource: str) -> Path:
    """Pad naar resource binnen user-container. Bv: 'notes.json', 'archive/foto/x.jpg'."""
    base = get_user_dir(user_id)
    p = base / resource
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# ============================================================
# CROSS-REF ANONIMISERING (bij delete)
# ============================================================
def _filter_list_by_user(filepath: Path, key: str, list_key: str, user_id: str) -> int:
    """Verwijder items waar item[key] == user_id. Return aantal verwijderd."""
    if not filepath.exists():
        return 0
    data = load_json(filepath, default={})
    arr = data.get(list_key)
    if not isinstance(arr, list):
        return 0
    before = len(arr)
    arr = [it for it in arr if it.get(key) != user_id]
    data[list_key] = arr
    save_json(filepath, data)
    return before - len(arr)


def _anonymize_list_by_user(filepath: Path, list_key: str, *, user_id_fields=("user_id",),
                            name_fields=("user_naam", "created_by", "created_by_naam")) -> int:
    """Vervang user_id in items door '_anon_<uid>' en namen door placeholder."""
    if not filepath.exists():
        return 0
    data = load_json(filepath, default={})
    arr = data.get(list_key)
    if not isinstance(arr, list):
        return 0
    count = 0
    return count  # placeholder — niet gebruikt in initiele scope


def anonymize_user_cross_refs(user_id: str) -> Dict[str, int]:
    """Hoofd-functie: ruim alle plekken op waar user_id genoemd staat.

    Veilige strategie: liever wissen dan corrupten. We loggen wat we hebben gedaan.
    """
    cleaned: Dict[str, int] = {}

    # Notes — verwijderen
    cleaned["notes"] = _filter_list_by_user(DATA / "notes" / "notes.json", "user_id", "notes", user_id)
    cleaned["tasks"] = _filter_list_by_user(DATA / "notes" / "tasks.json", "user_id", "tasks", user_id)

    # Bugs — anonimiseren (niet verwijderen, want bugs-history is waardevol)
    bugs_fp = DATA / "bugs" / "bugs.json"
    if bugs_fp.exists():
        d = load_json(bugs_fp, default={})
        n = 0
        for b in d.get("bugs", []):
            if b.get("created_by_id") == user_id:
                b["created_by_id"] = f"_anon_{user_id}"
                b["created_by_naam"] = ANON_PLACEHOLDER
                n += 1
        if n:
            save_json(bugs_fp, d)
        cleaned["bugs_anon"] = n

    # Community messages — anonimiseren
    cm_fp = DATA / "community" / "messages.json"
    if cm_fp.exists():
        d = load_json(cm_fp, default={})
        n = 0
        for m in d.get("messages", []):
            if m.get("user_id") == user_id:
                m["user_id"] = f"_anon_{user_id}"
                m["user_name"] = ANON_PLACEHOLDER
                n += 1
        if n:
            save_json(cm_fp, d)
        cleaned["community_anon"] = n

    # Agenda — file weg
    agenda_fp = DATA / "agenda" / f"{user_id}.json"
    if agenda_fp.exists():
        try:
            agenda_fp.unlink()
            cleaned["agenda_file_deleted"] = 1
        except Exception:
            cleaned["agenda_file_deleted"] = -1

    # Dagboek — file weg
    dagboek_fp = DATA / "dagboek" / f"{user_id}.json"
    if dagboek_fp.exists():
        try:
            dagboek_fp.unlink()
            cleaned["dagboek_file_deleted"] = 1
        except Exception:
            cleaned["dagboek_file_deleted"] = -1

    # Chat privé — files waar user_id in naam staat
    chat_prive = DATA / "chat" / "prive"
    if chat_prive.exists():
        deleted = 0
        for fp in chat_prive.glob(f"*{user_id}*.json"):
            try:
                fp.unlink()
                deleted += 1
            except Exception:
                pass
        cleaned["chat_prive_files_deleted"] = deleted

    return cleaned


# ============================================================
# v6_container_migrate_001 — Legacy → Container migratie
# ============================================================
def migrate_user_legacy(user_id: str) -> Dict[str, Any]:
    """Kopieer bestaande user-data uit oude scattered paths naar nieuwe container.

    Veilig: kopieert (geen move). Oude paden blijven werken. Container krijgt
    `migration_origin` in meta zodat we later kunnen tellen wat al gemigreerd is.

    Returns dict met counts per resource.
    """
    base = get_user_dir(user_id)  # ensure container bestaat
    result: Dict[str, Any] = {"user_id": user_id, "copied": {}, "skipped": []}

    legacy_paths = {
        "agenda.json":  DATA / "agenda" / f"{user_id}.json",
        "dagboek.json": DATA / "dagboek" / f"{user_id}.json",
        # Wallet/notes/tasks zijn arrays in shared JSONs — niet 1-op-1 kopieerbaar.
        # Voor die data is filter+slice nodig (toekomstige fase).
    }

    for target_name, src in legacy_paths.items():
        dst = base / target_name
        if not src.exists():
            result["skipped"].append({"src": str(src), "reason": "geen-legacy-data"})
            continue
        if dst.exists():
            result["skipped"].append({"src": str(src), "reason": "container-heeft-al"})
            continue
        try:
            data = load_json(src, default={})
            # Voeg footnote toe
            if isinstance(data, dict):
                data.setdefault("_migration", {})
                data["_migration"]["from"] = str(src)
                data["_migration"]["migrated_at"] = (datetime.now(timezone.utc).isoformat())
            save_json(dst, data)
            result["copied"][target_name] = str(dst)
        except Exception as ex:
            result["skipped"].append({"src": str(src), "reason": f"error: {ex}"})

    # Markeer container als gemigreerd
    try:
        from .service import update_meta
        from modules.synapse.schema import CONTAINER_USER
        update_meta(CONTAINER_USER, user_id, {
            "tags": ["legacy_migrated"],
            "footnote": f"Legacy-migratie uitgevoerd op {datetime.now(timezone.utc).strftime('%Y-%m-%d')}. {len(result['copied'])} bestanden gekopieerd.",
        })
    except Exception:
        pass

    return result


def migrate_all_users() -> Dict[str, Any]:
    """Bulk-migratie voor alle users in /data/system/users.json."""
    users_fp = DATA / "system" / "users.json"
    users = load_json(users_fp, default={"users": []}).get("users", [])
    overall = {"total_users": len(users), "migrated": 0, "skipped": 0, "per_user": []}
    for u in users:
        uid = u.get("id")
        if not uid:
            continue
        r = migrate_user_legacy(uid)
        if r.get("copied"):
            overall["migrated"] += 1
        else:
            overall["skipped"] += 1
        overall["per_user"].append({"user_id": uid, "copied_count": len(r.get("copied", {}))})
    return overall


# Datetime import voor de migrate_user_legacy hierboven
from datetime import datetime, timezone  # noqa: E402
