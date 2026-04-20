"""
User XP Service — simpele XP-grant voor gamification.
Gebruikt door snap-creatie (v3_013 Spark Leraar achievement).
"""
from pathlib import Path
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json

USERS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"


def grant_xp(user_id: str, amount: int, reason: str = "") -> dict:
    """
    Geef user XP. Retourneert {success, new_xp, user_naam} of {success: False, ...}.
    Logt reden in user.xp_events voor audit.
    """
    if not user_id or amount <= 0:
        return {"success": False, "reason": "invalid input"}

    data = load_json(USERS_FILE, default={"users": []})
    users = data.get("users", []) if isinstance(data, dict) else data

    for user in users:
        if user.get("id") == user_id:
            old = int(user.get("xp", 0) or 0)
            new_xp = old + amount
            user["xp"] = new_xp
            # Log event
            events = user.setdefault("xp_events", [])
            events.append({
                "amount": amount,
                "reason": reason,
                "granted_at": datetime.now(timezone.utc).isoformat(),
                "total_after": new_xp,
            })
            # Trim log tot laatste 100 events
            if len(events) > 100:
                user["xp_events"] = events[-100:]

            if isinstance(data, dict):
                data["users"] = users
                save_json(USERS_FILE, data)
            else:
                save_json(USERS_FILE, users)

            print(f"[XP] {user.get('naam')} +{amount} ({reason}) → {new_xp}")
            return {
                "success": True,
                "user_naam": user.get("naam"),
                "xp_granted": amount,
                "new_xp": new_xp,
                "reason": reason,
            }

    return {"success": False, "reason": "user niet gevonden"}
