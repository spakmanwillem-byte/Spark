"""
Agenda Monthly Archive Service (v13_agenda_monthly_archive_001, sessie 54)
---------------------------------------------------------------------------
Willem's wens: op de 1e van elke maand:
  1. Alle events waarvan `date` valt in een vórige maand (< 1e van huidige maand)
     worden uit /data/agenda/{user_id}.json verwijderd.
  2. Ze worden opgeslagen in /data/users/{user_id}/archive/agenda_archief/
     agenda-YYYY-MM.json (per bron-maand).
  3. Ook een entry in de archive `_index.json` zodat Willem het onder de
     Bestanden-tab kan zien / downloaden.

Idempotent: draait maximaal 1× per maand per user (state-marker in
/data/agenda/_archive_state.json).

Kan gedraaid worden:
  • Automatisch bij server-startup (checkt of nieuwe maand)
  • Handmatig via POST /api/agenda/archive-now/{user_id}
  • Voor alle users tegelijk via POST /api/agenda/archive-now
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"
AGENDA_DIR = DATA_ROOT / "agenda"
USERS_DIR = DATA_ROOT / "users"
STATE_FILE = AGENDA_DIR / "_archive_state.json"


def _month_key(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def _first_of_current_month(now: datetime) -> datetime:
    return datetime(now.year, now.month, 1, tzinfo=timezone.utc)


def _archive_dir(user_id: str) -> Path:
    d = USERS_DIR / user_id / "archive" / "agenda_archief"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _index_path(user_id: str) -> Path:
    return USERS_DIR / user_id / "archive" / "_index.json"


def _register_in_index(user_id: str, archive_file: Path, month_key: str, count: int) -> None:
    """Voeg archief-file toe aan de user's archive _index.json zodat het in de
    Bestanden/Archief UI verschijnt."""
    idx_path = _index_path(user_id)
    idx = load_json(idx_path, default={"entries": []})
    entries = idx.setdefault("entries", [])
    # Check of dit maand-archief al in index staat (idempotent)
    marker = f"agenda_archief:{month_key}"
    for e in entries:
        if e.get("marker") == marker:
            e["file_path"] = str(archive_file.relative_to(USERS_DIR / user_id))
            e["event_count"] = count
            e["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_json(idx_path, idx)
            return
    entries.append({
        "id": str(uuid.uuid4()),
        "marker": marker,
        "category": "agenda_archief",
        "filename": archive_file.name,
        "file_path": str(archive_file.relative_to(USERS_DIR / user_id)),
        "event_count": count,
        "month": month_key,
        "uploaded_by": user_id,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "source": "auto_monthly_archive",
    })
    save_json(idx_path, idx)


def archive_events_for_user(user_id: str, now: Optional[datetime] = None) -> Dict:
    """Archiveer alle events van user die vóór de 1e van huidige maand vielen.
    Groepeert per bron-maand (bv juli-events → agenda-2026-07.json)."""
    now = now or datetime.now(timezone.utc)
    cutoff = _first_of_current_month(now)

    agenda_fp = AGENDA_DIR / f"{user_id}.json"
    if not agenda_fp.exists():
        return {"user_id": user_id, "archived": 0, "reason": "no_agenda_file"}

    data = load_json(agenda_fp, default={"events": []})
    events = data.get("events", [])
    if not events:
        return {"user_id": user_id, "archived": 0, "reason": "no_events"}

    # Split events: past-month (archiveren) vs keep
    to_archive: Dict[str, List[dict]] = {}
    keep: List[dict] = []
    for e in events:
        date_str = e.get("date") or e.get("datum") or e.get("start_datetime_iso") or ""
        if not date_str:
            keep.append(e)
            continue
        try:
            dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            keep.append(e)
            continue
        if dt < cutoff:
            key = _month_key(dt)
            to_archive.setdefault(key, []).append(e)
        else:
            keep.append(e)

    if not to_archive:
        return {"user_id": user_id, "archived": 0, "reason": "nothing_old"}

    # Schrijf archive-files per maand
    archived_total = 0
    archive_dir = _archive_dir(user_id)
    for month_key, month_events in to_archive.items():
        archive_fp = archive_dir / f"agenda-{month_key}.json"
        existing = load_json(archive_fp, default={"user_id": user_id, "month": month_key, "events": []})
        existing_ids = {e.get("id") for e in existing.get("events", [])}
        for e in month_events:
            if e.get("id") not in existing_ids:
                existing["events"].append(e)
                archived_total += 1
        existing["archived_at"] = now.isoformat()
        save_json(archive_fp, existing)
        _register_in_index(user_id, archive_fp, month_key, len(existing["events"]))

    # Update main agenda-file (verwijder gearchiveerde events)
    data["events"] = keep
    data["last_archive_at"] = now.isoformat()
    save_json(agenda_fp, data)

    return {
        "user_id": user_id,
        "archived": archived_total,
        "months": sorted(to_archive.keys()),
        "remaining_events": len(keep),
    }


def _has_run_this_month(user_id: str, now: datetime) -> bool:
    state = load_json(STATE_FILE, default={"users": {}})
    last = state.get("users", {}).get(user_id)
    if not last:
        return False
    try:
        last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
        return last_dt.year == now.year and last_dt.month == now.month
    except (ValueError, TypeError):
        return False


def _mark_run(user_id: str, now: datetime) -> None:
    state = load_json(STATE_FILE, default={"users": {}})
    state.setdefault("users", {})[user_id] = now.isoformat()
    save_json(STATE_FILE, state)


def archive_all_users_if_new_month() -> Dict:
    """Draait per user het maand-archief, maar alleen als die user deze maand
    nog niet aan de beurt is geweest. Bedoeld voor server-startup hook."""
    now = datetime.now(timezone.utc)
    results = []
    for agenda_file in AGENDA_DIR.glob("user-*.json"):
        user_id = agenda_file.stem
        if _has_run_this_month(user_id, now):
            continue
        try:
            r = archive_events_for_user(user_id, now)
            results.append(r)
            if r.get("archived", 0) > 0:
                _mark_run(user_id, now)
        except Exception as e:
            results.append({"user_id": user_id, "error": str(e)})
    return {"ok": True, "checked": len(results), "results": results}


def archive_now(user_id: Optional[str] = None) -> Dict:
    """Handmatige trigger — override state-marker (draait ook al eerder gedraaid)."""
    now = datetime.now(timezone.utc)
    if user_id:
        r = archive_events_for_user(user_id, now)
        if r.get("archived", 0) > 0:
            _mark_run(user_id, now)
        return {"ok": True, "result": r}
    # All users
    results = []
    for agenda_file in AGENDA_DIR.glob("user-*.json"):
        uid = agenda_file.stem
        try:
            r = archive_events_for_user(uid, now)
            results.append(r)
            if r.get("archived", 0) > 0:
                _mark_run(uid, now)
        except Exception as e:
            results.append({"user_id": uid, "error": str(e)})
    return {"ok": True, "checked": len(results), "results": results}


def load_all_events(user_id: str, include_archive: bool = True) -> List[dict]:
    """Laad ALLE events voor een user: actieve agenda + optioneel het volledige
    archief. Gebruikt door Spark bij historie-vragen ('wat deed ik in juli?')
    zodat gearchiveerde events niet uit zijn bewustzijn verdwijnen."""
    events: List[dict] = []
    # Actief
    agenda_fp = AGENDA_DIR / f"{user_id}.json"
    if agenda_fp.exists():
        events.extend(load_json(agenda_fp, default={"events": []}).get("events", []))
    # Archief
    if include_archive:
        archive_dir = USERS_DIR / user_id / "archive" / "agenda_archief"
        if archive_dir.exists():
            for f in archive_dir.glob("agenda-*.json"):
                try:
                    events.extend(load_json(f, default={"events": []}).get("events", []))
                except Exception:
                    pass
    return events
