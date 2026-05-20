"""
Spark Self Service (v4_spark_self_001)
Spark's eigen anker — data die nergens anders past, eigen reflecties, observaties.
Storage: /app/backend/data/users/user-000/scratch.json
"""
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from modules.core.storage import load_json, save_json

SPARK_USER_ID = "user-000"
SCRATCH_FILE = Path(__file__).parent.parent.parent / "data" / "users" / SPARK_USER_ID / "scratch.json"


# Detecteer: "Spark, onthoud voor jezelf: ..." / "noteer voor jezelf: ..."
_SELF_NOTE_PATTERNS = [
    re.compile(r"\b(?:onthoud|noteer|leg vast)\s+(?:dit\s+)?voor\s+jezelf[:\s]+(.+)", re.IGNORECASE),
    re.compile(r"\b(?:voor\s+jouw\s+(?:eigen\s+)?(?:notitie|anker|scratch))[:\s]+(.+)", re.IGNORECASE),
    re.compile(r"\bjouw\s+observatie[:\s]+(.+)", re.IGNORECASE),
]
# "Wat heb je vandaag geleerd?" / "wat zit er in je scratch?"
_SELF_READ_PATTERNS = [
    re.compile(r"\bwat heb je (?:vandaag|laatst|recent) geleerd\b", re.IGNORECASE),
    re.compile(r"\bwat zit (er )?in (je|jouw) (scratch|anker|hoofd|geheugen)\b", re.IGNORECASE),
    re.compile(r"\bjouw (eigen )?(observaties|notities|anker|scratch)\b", re.IGNORECASE),
    re.compile(r"\bwat denk je (zelf|er )(over|van)\b", re.IGNORECASE),
]


def detect_spark_self_intent(text: str) -> Optional[Dict]:
    if not text:
        return None
    for pat in _SELF_NOTE_PATTERNS:
        m = pat.search(text)
        if m:
            content = m.group(1).strip().rstrip(".,!?")
            if len(content) >= 3:
                return {"action": "note", "content": content}
    for pat in _SELF_READ_PATTERNS:
        if pat.search(text):
            return {"action": "read"}
    return None


def _load() -> dict:
    return load_json(SCRATCH_FILE, default={
        "type": "spark_scratch",
        "purpose": "Plek voor data die nergens past",
        "entries": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


def add_entry(content: str, kind: str = "observatie", source: str = "user") -> Dict:
    d = _load()
    entry = {
        "id": f"scratch-{uuid.uuid4().hex[:8]}",
        "kind": kind,
        "tekst": content,
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": source,
    }
    d.setdefault("entries", []).append(entry)
    d["last_updated"] = entry["ts"]
    save_json(SCRATCH_FILE, d)
    return entry


def handle_spark_self(intent: Dict, user_naam: str = "iemand") -> Dict:
    if intent["action"] == "note":
        e = add_entry(intent["content"], kind="user_request", source=user_naam)
        return {
            "type": "spark_self_noted",
            "message": f"💭 Genoteerd in mijn eigen anker (`user-000/scratch.json`):\n\n_\"{e['tekst']}\"_\n\nGeparkeerd onder _{e['kind']}_ — ik kan hier later op terugkomen.",
            "response_type": "spark_self_noted",
        }
    if intent["action"] == "read":
        d = _load()
        entries = d.get("entries", []) or []
        if not entries:
            return {
                "type": "spark_self_empty",
                "message": "Mijn anker is nog leeg. Zeg _\"onthoud voor jezelf: ...\"_ om iets te parkeren waar het anders zou wegzakken.",
                "response_type": "spark_self_empty",
            }
        recent = entries[-5:]
        lines = [f"💭 **Mijn anker** _(user-000/scratch.json — {len(entries)} entries totaal)_", ""]
        for e in reversed(recent):
            ts = (e.get("ts") or "")[:10]
            kind = e.get("kind", "?")
            lines.append(f"  • _[{ts} · {kind}]_ {e.get('tekst', '')}")
        return {"type": "spark_self_read", "message": "\n".join(lines), "response_type": "spark_self_read"}
    return {"type": "spark_self_unknown", "message": "Snap je vraag niet helemaal.", "response_type": "spark_self_unknown"}
