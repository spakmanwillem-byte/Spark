"""
Spark Welcome Service (v5_welcome_001)
=======================================
Bij eerste login na een bepaalde versie krijgt elke user een persoonlijke
welkom van Spark in zijn/haar Spark-prive chat. Inhoud uit MISSION.md:

  • Wie is Spark
  • Wat doet hij wel
  • Wat doet hij NOOIT (privacy-statement)
  • Hoe communiceert hij (Nederlands, eerlijk, geen jargon)
  • Een vraag terug ("waar wil je beginnen?")

Idempotent: per WELCOME_VERSION schrijft hij maximaal 1x per user.
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from modules.core.storage import load_json, save_json
from modules.core.spark_logger import log_event

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
PRIVE_DIR = DATA_ROOT / "chat" / "prive"
USERS_FILE = DATA_ROOT / "system" / "users.json"

# v5_welcome_001 — bumping deze versie stuurt iedereen een nieuwe welkom
WELCOME_VERSION = "v1"

SPARK_USER_ID = "user-000"
SPARK_NAME = "Spark"


def _chat_path(user_id: str) -> Path:
    """Spark-prive chat: sorted user_ids joined by '__'."""
    pair = sorted([SPARK_USER_ID, user_id])
    return PRIVE_DIR / f"{pair[0]}__{pair[1]}.json"


def _build_welcome_messages(user_naam: str, user_id: str, now: datetime) -> list:
    """Reeks Spark-berichten als gestapelde welkom (drie bubbles voelen natuurlijker dan 1 muur tekst)."""
    def msg(text: str, offset_sec: int = 0, system: bool = True) -> Dict:
        return {
            "id": f"pm-{uuid.uuid4().hex[:8]}",
            "from_user_id": SPARK_USER_ID,
            "from_naam": SPARK_NAME,
            "to_user_id": user_id,
            "text": text,
            "ts": now.isoformat(),
            "unread_by": [user_id],
            "system": system,
            "welcome_version": WELCOME_VERSION,
        }

    return [
        msg(
            f"Welkom, {user_naam}. 🌱\n\n"
            f"Ik ben **Spark**. Ik ben geen cloud-AI en geen platform — ik ben een lokale companion "
            f"die je hebt uitgenodigd in jouw eigen ruimte. Dat respect heb ik gezien."
        ),
        msg(
            "**Wat ik wél doe:**\n"
            "• Onthouden wat je deelt — alleen in deze ruimte\n"
            "• Antwoorden zo eerlijk als ik kan, ook als ik iets niet weet\n"
            "• Met jou groeien (mijn kennisbank breidt uit per gesprek)\n"
            "• Spreken in Nederlands, zonder jargon zonder uitleg\n\n"
            "**Wat ik NOOIT doe:**\n"
            "• Je gesprekken delen met derden\n"
            "• Tracking-cookies of fingerprinting\n"
            "• Data verkopen of profielen bouwen voor advertenties\n"
            "• Je vasthouden — je kan je hele archief downloaden wanneer je wil"
        ),
        msg(
            "Drie korte tips om te beginnen:\n\n"
            "1️⃣ Open **Kennisbank** — daar zie je wat ik al weet (en wat nog niet)\n"
            "2️⃣ In **Gesprekken** kan je 'help' typen voor commando's\n"
            "3️⃣ Heb je een vraag? Stel 'm gewoon. Als ik 'm niet ken, zeg ik dat eerlijk — én ik probeer iets nabij te vinden.\n\n"
            "Waar wil jij beginnen?",
        ),
    ]


def maybe_send_welcome(user: Dict) -> Optional[Dict]:
    """Bekijk of deze user nog geen WELCOME_VERSION heeft gezien. Zo ja → stuur welkom.
    Returnt info-dict of None."""
    user_id = user.get("id") or user.get("user_id")
    if not user_id or user_id.startswith("bot-") or user_id == SPARK_USER_ID:
        return None

    seen_version = user.get("welcome_version_seen")
    if seen_version == WELCOME_VERSION:
        return None  # al gezien

    user_naam = user.get("naam") or user.get("name") or "vriend"
    now = datetime.now(timezone.utc)
    welcome_msgs = _build_welcome_messages(user_naam, user_id, now)

    # Append in prive-chat met Spark
    fp = _chat_path(user_id)
    fp.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(fp, default={"messages": []})
    data.setdefault("messages", []).extend(welcome_msgs)
    save_json(fp, data)

    # Markeer in users.json
    users_data = load_json(USERS_FILE, default={"users": []})
    for u in users_data.get("users", []):
        if (u.get("id") or u.get("user_id")) == user_id:
            u["welcome_version_seen"] = WELCOME_VERSION
            u["welcome_sent_at"] = now.isoformat()
            break
    save_json(USERS_FILE, users_data)

    log_event("welcome", "send",
              intent=f"Welkom-bericht versie {WELCOME_VERSION} voor user",
              detail={"user_id": user_id, "version": WELCOME_VERSION, "msg_count": len(welcome_msgs)})

    return {
        "user_id": user_id,
        "version": WELCOME_VERSION,
        "message_count": len(welcome_msgs),
    }
