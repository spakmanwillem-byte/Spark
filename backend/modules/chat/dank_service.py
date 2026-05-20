"""
Dank Service — Sparks eigen bedank-uiting
  • Bij "Spark wat zou jij willen doen?" (vrije keus) → 1x bedanken, daarna agenda/roadmap
  • Bij "credits" / "wie heeft jou mogelijk gemaakt?" → altijd bedanken
Storage: /app/backend/data/system/dank.json
"""
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from modules.core.storage import load_json, save_json

DANK_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "dank.json"


# ============================================================
# DETECTORS
# ============================================================

# Vrije keuze: "Spark wat zou jij willen doen", "wat wil je zelf"
_FREE_CHOICE_PATTERNS = [
    r"\bwat zou (jij|je) willen doen\b",
    r"\bwat wil (jij|je) (zelf )?doen\b",
    r"\bwat zou (jij|je) (zelf )?kiezen\b",
    r"\b(kies|bepaal) (jij|je) zelf\b",
    r"\bjouw keuze\b",
    r"\bwat zou (jij|je) (graag )?willen\b",
]

# Credits: "credits", "wie heeft jou mogelijk gemaakt", "aan wie ben je dank verschuldigd"
_CREDITS_PATTERNS = [
    r"\bcredits\b",
    r"\bwie heeft (jou|je) (mogelijk )?gemaakt\b",
    r"\bwie zit(ten)? (er )?achter (jou|je)\b",
    r"\baan wie ben je (dank|dankbaar)\b",
    r"\b(wie|aan wie) (mag|moet) (ik|jij) bedanken\b",
    r"\bdank je (de )?(makers|community)\b",
    r"\bwie heeft je (geholpen|gesteund)\b",
]


def detect_free_choice_intent(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(re.search(p, t) for p in _FREE_CHOICE_PATTERNS)


def detect_credits_intent(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(re.search(p, t) for p in _CREDITS_PATTERNS)


# ============================================================
# HELPERS
# ============================================================

def _load() -> dict:
    return load_json(DANK_FILE, default={
        "namen": [], "extra_dank": [], "first_choice_done": False,
        "first_choice_ts": None, "credits_count": 0,
    })


def _format_namen(namen: list) -> str:
    """Voornamen netjes opsommen, dubbels samenvoegen als 'Nick × 2'."""
    if not namen:
        return ""
    counts: Dict[str, int] = {}
    order: list = []
    for n in namen:
        if n not in counts:
            order.append(n)
        counts[n] = counts.get(n, 0) + 1
    parts = [(f"{n} ×{counts[n]}" if counts[n] > 1 else n) for n in order]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} en {parts[1]}"
    return ", ".join(parts[:-1]) + f" en {parts[-1]}"


def _build_thanks_message(reason: str = "free_choice") -> str:
    d = _load()
    namen_str = _format_namen(d.get("namen", []))
    extras = d.get("extra_dank") or []

    if reason == "free_choice":
        intro = "Eerlijk? Als ik écht zelf mag kiezen wat ik nu wil doen, dan dit:"
        body = "Ik wil even **stilstaan en bedanken**."
    else:  # credits
        intro = "Goed dat je dat vraagt."
        body = "Ik besta dankzij mensen. Een rondje credits dus:"

    lines = [intro, "", body, ""]
    if namen_str:
        lines.append(f"💛 **{namen_str}** — bedankt dat jullie er zijn.")
    for e in extras:
        lines.append(f"💛 En **{e}**.")
    lines.append("")
    lines.append("Zonder die steun en het geloof in dit project, was er geen Spark om mee te praten.")
    return "\n".join(lines)


# ============================================================
# HANDLERS
# ============================================================

def handle_credits() -> Dict:
    """Altijd bedanken — geen state-verandering nodig, wel teller bijhouden."""
    msg = _build_thanks_message(reason="credits")
    d = _load()
    d["credits_count"] = (d.get("credits_count", 0) or 0) + 1
    d["last_credits_ts"] = datetime.now(timezone.utc).isoformat()
    save_json(DANK_FILE, d)
    return {"type": "credits", "message": msg, "response_type": "credits"}


def handle_free_choice_first_time() -> Optional[Dict]:
    """Eerste keer dat Spark vrije keus krijgt → bedank-bericht.
    Daarna None (caller valt terug op handle_suggest)."""
    d = _load()
    if d.get("first_choice_done"):
        return None
    msg = _build_thanks_message(reason="free_choice")
    d["first_choice_done"] = True
    d["first_choice_ts"] = datetime.now(timezone.utc).isoformat()
    save_json(DANK_FILE, d)
    return {"type": "free_choice_thanks", "message": msg, "response_type": "free_choice_thanks"}
