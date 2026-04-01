"""
Triggers Routes - Read all trigger files from /data/triggers/ and /data/emotions/
Consolidates: conversation, calendar, emotion, admin, system_fallback triggers
"""
from fastapi import APIRouter
from pathlib import Path
from modules.core.storage import load_json

router = APIRouter(prefix="/triggers", tags=["triggers"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"
TRIGGERS_DIR = DATA_DIR / "triggers"
EMOTIONS_DIR = DATA_DIR / "emotions"


@router.get("/all")
async def get_all_triggers():
    """Return all trigger categories with their word lists"""
    result = {}

    # Conversation triggers (greeting, thanks, etc.)
    conv = load_json(TRIGGERS_DIR / "conversation_triggers.json", default={})
    for key, val in conv.items():
        if key == "metadata":
            continue
        triggers = val.get("triggers", []) if isinstance(val, dict) else val
        responses = val.get("responses", []) if isinstance(val, dict) else []
        result[key] = {
            "type": "conversation",
            "label": key.replace("_", " ").title(),
            "triggers": triggers,
            "responses": responses,
            "color": "amber",
        }

    # Calendar triggers
    cal = load_json(TRIGGERS_DIR / "calendar_triggers.json", default={})
    for key, words in cal.get("triggers", {}).items():
        result[f"cal_{key}"] = {
            "type": "calendar",
            "label": f"Kalender: {key.title()}",
            "triggers": words if isinstance(words, list) else [],
            "responses": [],
            "color": "blue",
        }

    # Emotion triggers
    emo = load_json(EMOTIONS_DIR / "emotion_triggers.json", default={})
    for key, val in emo.get("emotions", {}).items():
        triggers_dict = val.get("triggers", {})
        result[f"emotie_{key}"] = {
            "type": "emotion",
            "label": f"Emotie: {key.title()}",
            "triggers": list(triggers_dict.keys()) if isinstance(triggers_dict, dict) else [],
            "trigger_scores": triggers_dict if isinstance(triggers_dict, dict) else {},
            "responses": emo.get("empathic_responses", {}).get(key, []),
            "color": val.get("color", "pink"),
            "emoji": val.get("emoji", ""),
        }

    # Admin commands
    admin = load_json(TRIGGERS_DIR / "admin_commands.json", default={})
    for key, val in admin.items():
        if key == "metadata":
            continue
        triggers = val.get("triggers", []) if isinstance(val, dict) else []
        result[f"admin_{key}"] = {
            "type": "admin",
            "label": f"Admin: {key.replace('_', ' ').title()}",
            "triggers": triggers,
            "responses": [],
            "color": "red",
        }

    # System fallback
    fallback = load_json(TRIGGERS_DIR / "system_fallback.json", default={})
    for key, val in fallback.items():
        if key == "metadata":
            continue
        triggers = val.get("triggers", []) if isinstance(val, dict) else []
        result[f"fallback_{key}"] = {
            "type": "system",
            "label": f"Systeem: {key.replace('_', ' ').title()}",
            "triggers": triggers,
            "responses": val.get("responses", []) if isinstance(val, dict) else [],
            "color": "slate",
        }

    return {
        "trigger_groups": result,
        "stats": {
            "total_groups": len(result),
            "total_triggers": sum(len(g["triggers"]) for g in result.values()),
        },
    }


@router.get("/by-type/{trigger_type}")
async def get_triggers_by_type(trigger_type: str):
    """Get triggers filtered by type: conversation, calendar, emotion, admin, system"""
    all_data = await get_all_triggers()
    filtered = {k: v for k, v in all_data["trigger_groups"].items() if v["type"] == trigger_type}
    return {
        "trigger_groups": filtered,
        "stats": {
            "total_groups": len(filtered),
            "total_triggers": sum(len(g["triggers"]) for g in filtered.values()),
        },
    }
