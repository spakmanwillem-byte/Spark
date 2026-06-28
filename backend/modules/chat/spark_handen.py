"""v6_spark_handen_001 — Spark's "Handen": schrijfacties vanuit chat.

Detecteert schrijf-intenties in user-text via regex én roept de bijbehorende
backend-service aan. Geen LLM-call nodig (snel, gratis).

Capabilities geleverd:
- `maak_notitie` — schrijf naar notes service
- `voeg_taak_toe` — schrijf naar tasks service
- (uitbreidbaar: agenda, KB-card, bug-report, etc.)

Pattern-detectie loopt VOOR de LLM-call zodat we direct kunnen reageren met
'Notitie opgeslagen!' zonder credits te branden.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from modules.core.storage import load_json, save_json

logger = logging.getLogger(__name__)
DATA = Path(__file__).parent.parent.parent / "data"

# Patronen die schrijf-intentie herkennen
# Group 1 = content (wat moet er bewaard worden)
NOTE_PATTERNS = [
    r"^(?:maak\s+(?:een\s+)?notitie(?:\s+aan)?(?:\s+over)?|noteer(?:\s+dit)?|schrijf\s+(?:dit\s+)?op|onthoud\s+(?:dit|voor\s+mij)?|leg\s+vast)\s*[:,]?\s*(.+)$",
    r"^(?:zet\s+(?:dit\s+)?in\s+(?:mijn\s+)?notities|voeg\s+(?:toe\s+)?aan\s+(?:mijn\s+)?notities)\s*[:,]?\s*(.+)$",
    r"^(?:nieuwe\s+notitie|nieuwe\s+note)\s*[:,]?\s*(.+)$",
]

TASK_PATTERNS = [
    r"^(?:maak\s+(?:een\s+)?taak|voeg\s+(?:een\s+)?taak\s+toe|nieuwe\s+taak|nieuwe\s+todo|todo)\s*[:,]?\s*(.+)$",
    r"^(?:zet\s+op\s+(?:mijn\s+)?(?:taken|todo)(?:\s*lijst)?)\s*[:,]?\s*(.+)$",
]


def _user_naam(user_id: str) -> str:
    try:
        users = load_json(DATA / "system" / "users.json", default={"users": []})
        for u in users.get("users", []):
            if u.get("id") == user_id:
                return u.get("naam") or user_id
    except Exception:
        pass
    return user_id


def detect_and_execute(user_text: str, user_id: str) -> Optional[Dict]:
    """Detecteer schrijf-intentie en voer uit. Return Spark-respons dict of None.

    Output format compatible met compose_response — main flow check op
    result.get('hand_executed') om LLM-call over te slaan.
    """
    if not user_text or not user_id:
        return None
    text = user_text.strip()
    if len(text) < 10:
        return None  # te kort om zinvol te zijn

    text_lower = text.lower()

    # NOTITIE
    for pattern in NOTE_PATTERNS:
        m = re.match(pattern, text_lower, re.IGNORECASE)
        if m:
            # Pak content uit ORIGINELE text (niet lower) voor casing
            start_pos = m.start(1)
            content = text[start_pos:].strip(" .,!?:;")
            if not content or len(content) < 3:
                return None
            return _create_note(user_id, content)

    # TAAK
    for pattern in TASK_PATTERNS:
        m = re.match(pattern, text_lower, re.IGNORECASE)
        if m:
            start_pos = m.start(1)
            content = text[start_pos:].strip(" .,!?:;")
            if not content or len(content) < 3:
                return None
            return _create_task(user_id, content)

    return None


def _create_note(user_id: str, content: str) -> Dict:
    notes_file = DATA / "notes" / "notes.json"
    data = load_json(notes_file, default={"notes": []})
    # Genereer titel uit eerste 50 chars
    titel = content[:50].rstrip()
    if len(content) > 50:
        titel += "..."
    new_note = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "titel": titel,
        "inhoud": content,
        "categorie": "Observatie",
        "tags": ["spark-handen", "via-chat"],
        "priority": "medium",
        "datum": datetime.now(timezone.utc).isoformat(),
        "created_by": _user_naam(user_id),
        "updated_at": None,
    }
    data.setdefault("notes", []).insert(0, new_note)
    save_json(notes_file, data)
    logger.info("[spark_handen] notitie aangemaakt voor %s: '%s'", user_id, titel[:40])
    return {
        "hand_executed": True,
        "action": "create_note",
        "note_id": new_note["id"],
        "message": (
            f"✍️ Notitie opgeslagen!\n\n"
            f"**{titel}**\n\n"
            f"Te vinden in **Notities-tab** (categorie: Observatie). "
            f"Wil je nog tags toevoegen of de categorie veranderen?"
        ),
    }


def _create_task(user_id: str, content: str) -> Dict:
    tasks_file = DATA / "notes" / "tasks.json"
    data = load_json(tasks_file, default={"tasks": []})
    new_task = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "task": content[:200],
        "priority": "medium",
        "status": "open",
        "created": datetime.now(timezone.utc).isoformat(),
        "created_by": _user_naam(user_id),
    }
    data.setdefault("tasks", []).insert(0, new_task)
    save_json(tasks_file, data)
    logger.info("[spark_handen] taak aangemaakt voor %s: '%s'", user_id, content[:40])
    return {
        "hand_executed": True,
        "action": "create_task",
        "task_id": new_task["id"],
        "message": (
            f"✅ Taak toegevoegd!\n\n"
            f"**{content[:80]}**\n\n"
            f"Te vinden in **Notities-tab → Taken**. Status: open."
        ),
    }
