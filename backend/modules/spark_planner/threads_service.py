"""v6_spark_planner_001 — Open Threads Service (Laag B).

Houdt gespreks-draden bij over dagen heen.
Threads worden gevoed door:
  1. brief_builder.sync_threads_from_brief() — automatisch uit dagelijkse thema's
  2. Handmatige POST endpoints

Threads worden in Diep-gesprek system_prompt geïnject (max N active).
Decay-mechanisme: na X dagen zonder mention → 'sluimerend', na Y dagen → 'afgesloten'.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from datetime import datetime, timezone, date as date_cls
from typing import Dict, List, Optional, Any

from modules.core.storage import load_json, save_json
from modules.core.blueprint import load_blueprint_cached


def _bp() -> Dict:
    return load_blueprint_cached("spark_planner", "planner")


def _threads_fp() -> Path:
    return Path(_bp()["paths"]["threads_fp"])


def _load_all() -> Dict[str, List[Dict]]:
    return load_json(_threads_fp(), default={})


def _save_all(data: Dict[str, List[Dict]]) -> None:
    _threads_fp().parent.mkdir(parents=True, exist_ok=True)
    save_json(_threads_fp(), data)


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _days_since(d: str) -> int:
    if not d:
        return 9999
    try:
        then = date_cls.fromisoformat(d[:10])
        return (datetime.now(timezone.utc).date() - then).days
    except Exception:
        return 9999


def get_threads(user_id: str, status: Optional[str] = None) -> List[Dict]:
    """Geef threads voor user, optioneel gefilterd op status."""
    all_data = _load_all()
    threads = list(all_data.get(user_id, []) or [])
    if status:
        threads = [t for t in threads if t.get("status") == status]
    # Sort: open eerst, dan sluimerend, dan afgesloten. Binnen status: meest recent eerst.
    order = {"open": 0, "sluimerend": 1, "afgesloten": 2}
    threads.sort(key=lambda t: (order.get(t.get("status"), 99),
                                 -t.get("intensity", 0),
                                 t.get("last_seen") or ""), reverse=False)
    return threads


def active_threads_for_inject(user_id: str, max_n: Optional[int] = None) -> List[Dict]:
    """Pak top-N actieve threads voor system_prompt-injectie."""
    bp = _bp()
    if max_n is None:
        max_n = bp["threads"].get("max_active_to_inject", 3)
    threads = get_threads(user_id, status="open")
    # Decay: oudere threads krijgen lagere prioriteit
    threads.sort(key=lambda t: (
        -int(t.get("intensity", 1)),
        -(0 - _days_since(t.get("last_seen") or _today()))
    ))
    return threads[:max_n]


def add_or_bump_thread(user_id: str, topic: str, intensity: int = 1,
                       note: Optional[str] = None) -> Dict:
    """Voeg thread toe OF verhoog intensity als deze topic al bestaat.

    Topic-match is case-insensitive op letterlijke string.
    """
    if not topic or not topic.strip():
        return {"success": False, "error": "topic leeg"}
    topic_norm = topic.strip()

    all_data = _load_all()
    threads = all_data.get(user_id, []) or []

    existing = None
    for t in threads:
        if (t.get("topic") or "").lower().strip() == topic_norm.lower():
            existing = t
            break

    today = _today()
    if existing:
        existing["intensity"] = min(10, int(existing.get("intensity", 1)) + int(intensity))
        existing["last_seen"] = today
        existing["status"] = "open"
        if note:
            existing["note"] = note
        out = existing
    else:
        out = {
            "id": uuid.uuid4().hex[:8],
            "topic": topic_norm,
            "first_seen": today,
            "last_seen": today,
            "intensity": max(1, min(10, int(intensity))),
            "status": "open",
            "note": note or "",
        }
        threads.append(out)

    all_data[user_id] = threads
    _save_all(all_data)
    return {"success": True, "thread": out}


def set_status(user_id: str, thread_id: str, status: str) -> Dict:
    bp = _bp()
    valid = bp["threads"].get("statuses", ["open", "sluimerend", "afgesloten"])
    if status not in valid:
        return {"success": False, "error": f"status moet één van {valid} zijn"}

    all_data = _load_all()
    threads = all_data.get(user_id, []) or []
    for t in threads:
        if t.get("id") == thread_id:
            t["status"] = status
            t["last_seen"] = _today()
            _save_all(all_data)
            return {"success": True, "thread": t}
    return {"success": False, "error": "thread niet gevonden"}


def delete_thread(user_id: str, thread_id: str) -> Dict:
    all_data = _load_all()
    before = len(all_data.get(user_id, []) or [])
    all_data[user_id] = [t for t in (all_data.get(user_id, []) or [])
                          if t.get("id") != thread_id]
    if len(all_data[user_id]) == before:
        return {"success": False, "error": "thread niet gevonden"}
    _save_all(all_data)
    return {"success": True, "remaining": len(all_data[user_id])}


def run_decay(user_id: Optional[str] = None) -> Dict:
    """Loop alle threads: open → sluimerend → afgesloten op basis van last_seen."""
    bp = _bp()
    decay_days = bp["threads"].get("intensity_decay_days", 7)
    auto_close_days = bp["threads"].get("auto_close_after_days", 30)

    all_data = _load_all()
    targets = [user_id] if user_id else list(all_data.keys())
    n_demoted = 0
    n_closed = 0
    for uid in targets:
        for t in (all_data.get(uid, []) or []):
            days = _days_since(t.get("last_seen"))
            if t.get("status") == "open" and days >= decay_days:
                t["status"] = "sluimerend"
                n_demoted += 1
            if t.get("status") in ("open", "sluimerend") and days >= auto_close_days:
                t["status"] = "afgesloten"
                n_closed += 1
    _save_all(all_data)
    return {"success": True, "demoted_to_sluimerend": n_demoted, "closed": n_closed}


def sync_threads_from_brief(user_id: str, brief: Dict) -> Dict:
    """Wordt aangeroepen vanuit brief_builder na een nieuwe brief.

    Voor elk thema in brief.themes → add_or_bump_thread.
    Voor elke open_question → thread met status='open', intensity boost.
    """
    n_added = 0
    n_bumped = 0
    for theme in (brief.get("themes") or []):
        if not theme:
            continue
        res = add_or_bump_thread(user_id, theme, intensity=1,
                                  note=f"Uit brief van {brief.get('date')}")
        if res.get("success"):
            # Detecteer "bump" vs "added" via aanwezigheid van first_seen == today
            t = res.get("thread") or {}
            if t.get("first_seen") == t.get("last_seen") == _today():
                n_added += 1
            else:
                n_bumped += 1
    for q in (brief.get("open_questions") or []):
        if not q:
            continue
        add_or_bump_thread(user_id, q, intensity=2,
                            note=f"Open vraag uit brief {brief.get('date')}")
    return {"success": True, "added": n_added, "bumped": n_bumped}


def format_for_system_prompt(threads: List[Dict]) -> Optional[str]:
    """Render top-N actieve threads als korte injectie-text."""
    if not threads:
        return None
    lines = []
    for t in threads:
        topic = t.get("topic", "?")
        last = t.get("last_seen", "?")
        intensity = t.get("intensity", 1)
        marker = "●" * min(3, intensity) + "○" * max(0, 3 - intensity)
        lines.append(f"  {marker} '{topic}' (laatst aangeraakt: {last})")
    return "\n".join(lines)
