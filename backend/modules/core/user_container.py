"""User Container Provisioning (v13d_user_container_001, sessie 56)
================================================================

Willem's principe: "iedere gebruiker is een eigen ID en eco-container".
Alle nieuwe users moeten automatisch dezelfde set skeleton-files krijgen
zodra ze in het systeem verschijnen — nooit meer stuk door ontbrekende data.

**Auto-spawned files per user**:
1. `data/agenda/{uid}.json`         — {"events": []}
2. `data/dagboek/{uid}.json`        — {"entries": []}
3. `data/persons/{uid}.json`        — {"persons": []} (relaties)
4. `data/personalia/{uid}.json`     — {"facts": [], "notes": []} (Spark's kennis over user, admin-only)
5. Boekhouding privé-book — via bestaande auto-hook in books_routes

**Aanroep-strategie** (idempotent, dus 2× is safe):
- AuthService.register / create_user → direct spawn
- Login (backup) → als er iets mist, aanvullen
- Bulk-backfill script voor bestaande users

**Skip-lijst**:
- system-user (user-000)
- test-agents (user-rps-test-agent, etc.)
- Al gedeplyed users met bestaande data (idempotent overslaan)
"""
from pathlib import Path
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json

_DATA = Path(__file__).parent.parent.parent / "data"
_NOW = lambda: datetime.now(timezone.utc).isoformat()

# Templates per module: {relatief_pad: default_content_lambda}
CONTAINER_TEMPLATES = {
    "agenda":     ("{uid}.json", lambda uid: {"events": []}),
    "dagboek":    ("{uid}.json", lambda uid: {"entries": []}),
    "persons":    ("{uid}.json", lambda uid: {"persons": [], "_meta": {"created_at": _NOW()}}),
    "personalia": ("{uid}.json", lambda uid: {
        "user_id": uid,
        "facts": [],
        "notes": [],
        "_meta": {"created_at": _NOW(), "visibility": "admin_only"},
    }),
}


def ensure_user_container(user_id: str, force: bool = False) -> dict:
    """Maak alle skeleton-files aan voor user_id als ze nog niet bestaan.

    Idempotent: bestaande files worden niet overschreven (tenzij force=True).
    Return: {module: 'created' | 'exists' | 'skipped'}
    """
    if not user_id or user_id.startswith(("user-rps-test", "user-000")):
        return {"skipped": "system_or_test_user"}

    report = {}
    for module, (filename_tpl, content_fn) in CONTAINER_TEMPLATES.items():
        fp = _DATA / module / filename_tpl.format(uid=user_id)
        fp.parent.mkdir(parents=True, exist_ok=True)
        if fp.exists() and not force:
            report[module] = "exists"
            continue
        content = content_fn(user_id)
        save_json(fp, content)
        report[module] = "created"
    return report


def backfill_all_users() -> dict:
    """Loop alle users → ensure_user_container. Return rapport."""
    users = load_json(_DATA / "system" / "users.json", default={"users": []}).get("users", [])
    stats = {"total": 0, "created": 0, "skipped": 0, "details": {}}
    for u in users:
        uid = u.get("id")
        if not uid:
            continue
        stats["total"] += 1
        r = ensure_user_container(uid)
        if "skipped" in r:
            stats["skipped"] += 1
        elif "created" in r.values():
            stats["created"] += 1
        stats["details"][uid] = r
    return stats
