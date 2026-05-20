"""
Triggers Routes - Read all trigger files from /data/triggers/ and /data/emotions/
Consolidates: conversation, calendar, emotion, admin, system_fallback triggers + spark vocab
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/triggers", tags=["triggers"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"
TRIGGERS_DIR = DATA_DIR / "triggers"
EMOTIONS_DIR = DATA_DIR / "emotions"
VOCAB_FILE = DATA_DIR / "personality" / "spark_vocab.json"


class TriggerWord(BaseModel):
    word: str
    field: str = "triggers"  # 'triggers' of 'responses'


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
            "edit_path": f"conversation/{key}",
            "editable": True,
            "supports_responses": True,
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
            "edit_path": f"calendar/{key}",
            "editable": True,
            "supports_responses": False,
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
            "edit_path": f"emotion/{key}",
            "editable": True,
            "supports_responses": True,
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
            "edit_path": f"admin/{key}",
            "editable": True,
            "supports_responses": False,
        }

    # System fallback — geen 'triggers' veld, alleen responses-lijsten per situatie
    fallback = load_json(TRIGGERS_DIR / "system_fallback.json", default={})
    for key, val in fallback.items():
        if key == "metadata":
            continue
        if isinstance(val, list):
            # Directe lijst van fallback strings → behandel als 'responses'
            result[f"fallback_{key}"] = {
                "type": "system",
                "label": f"Systeem: {key.replace('_', ' ').title()}",
                "triggers": [],
                "responses": val,
                "color": "slate",
                "edit_path": f"system/{key}",
                "editable": True,
                "supports_responses": True,
                "responses_only": True,
            }
        elif isinstance(val, dict):
            triggers = val.get("triggers", [])
            result[f"fallback_{key}"] = {
                "type": "system",
                "label": f"Systeem: {key.replace('_', ' ').title()}",
                "triggers": triggers,
                "responses": val.get("responses", []),
                "color": "slate",
                "edit_path": f"system/{key}",
                "editable": True,
                "supports_responses": True,
            }

    # Spark vocab (v4_013) — woordenlijsten voor antwoord-variatie
    vocab = load_json(VOCAB_FILE, default={"emoties": {}, "algemeen": {}})
    intent_label = {"begroeting": "Begroet", "bedanken": "Bedanken",
                    "afscheid": "Afscheid", "reactie": "Reactie"}
    for emotion, intents in (vocab.get("emoties") or {}).items():
        if not isinstance(intents, dict):
            continue
        for intent, words in intents.items():
            if not isinstance(words, list):
                continue
            result[f"vocab_emotie_{emotion}_{intent}"] = {
                "type": "vocab",
                "label": f"{emotion.title()} — {intent_label.get(intent, intent.title())}",
                "triggers": words,
                "responses": [],
                "color": "violet",
                "vocab_path": f"emoties/{emotion}.{intent}",
                "editable": True,
            }
    for cat, words in (vocab.get("algemeen") or {}).items():
        if isinstance(words, list):
            result[f"vocab_algemeen_{cat}"] = {
                "type": "vocab",
                "label": f"Algemeen — {cat.title()}",
                "triggers": words,
                "responses": [],
                "color": "violet",
                "vocab_path": f"algemeen/{cat}",
                "editable": True,
            }

    # Credits / Dank (v4_dank_001) — bewerkbaar via Triggers UI
    dank = load_json(DATA_DIR / "system" / "dank.json", default={})
    if dank:
        result["credits_namen"] = {
            "type": "conversation",
            "label": "Credits — Voornamen",
            "triggers": dank.get("namen", []),
            "responses": [],
            "color": "amber",
            "edit_path": "credits/namen",
            "editable": True,
            "supports_responses": False,
            "emoji": "💛",
        }
        result["credits_extra"] = {
            "type": "conversation",
            "label": "Credits — Extra dank (community e.d.)",
            "triggers": dank.get("extra_dank", []),
            "responses": [],
            "color": "amber",
            "edit_path": "credits/extra_dank",
            "editable": True,
            "supports_responses": False,
            "emoji": "💛",
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


# ============================================================
# GENERIC EDIT ENDPOINTS (v4_013c) — alle trigger-groepen editable
# edit_path = '{kind}/{key}' waar kind in: conversation, calendar, emotion, admin, system
# field = 'triggers' of 'responses'
# ============================================================

_KIND_TO_FILE = {
    "conversation": ("triggers", "conversation_triggers.json"),
    "calendar":     ("triggers", "calendar_triggers.json"),
    "emotion":      ("emotions", "emotion_triggers.json"),
    "admin":        ("triggers", "admin_commands.json"),
    "system":       ("triggers", "system_fallback.json"),
    "credits":      ("system",   "dank.json"),
    "vocab":        ("personality", "spark_vocab.json"),
}


def _kind_file(kind: str) -> Path:
    if kind not in _KIND_TO_FILE:
        raise HTTPException(400, f"Onbekend type: {kind}")
    folder, name = _KIND_TO_FILE[kind]
    return DATA_DIR / folder / name


def _get_list_ref(data: dict, kind: str, key: str, field: str):
    """Resolve list reference voor mutatie. Geeft (parent_dict, list_key) terug.

    Structuur per kind:
      conversation : { key: { triggers: [], responses: [] } }
      calendar     : { triggers: { key: [...] } }   (geen responses)
      emotion      : { emotions: { key: { triggers: {word: score} } }, empathic_responses: { key: [...] } }
      admin        : { key: { triggers: [...] } }   (geen responses)
      system       : { key: [...] } OR { key: { triggers, responses } }
    """
    if kind == "conversation":
        if key not in data:
            raise HTTPException(404, f"Groep '{key}' niet in conversation")
        if field == "triggers":
            if "triggers" not in data[key]:
                data[key]["triggers"] = []
            return data[key], "triggers"
        if field == "responses":
            if "responses" not in data[key]:
                data[key]["responses"] = []
            return data[key], "responses"
        raise HTTPException(400, f"Veld '{field}' niet ondersteund")

    if kind == "calendar":
        if field != "triggers":
            raise HTTPException(400, "Kalender heeft alleen triggers")
        triggers_root = data.setdefault("triggers", {})
        if key not in triggers_root:
            triggers_root[key] = []
        return triggers_root, key

    if kind == "emotion":
        emotions = data.setdefault("emotions", {})
        if key not in emotions:
            raise HTTPException(404, f"Emotie '{key}' niet gevonden")
        if field == "triggers":
            emotions[key].setdefault("triggers", {})
            # Voor mutatie: hier is een dict, niet lijst — speciale behandeling caller
            return emotions[key], "triggers"
        if field == "responses":
            empathic = data.setdefault("empathic_responses", {})
            if key not in empathic:
                empathic[key] = []
            return empathic, key
        raise HTTPException(400, f"Veld '{field}' niet ondersteund")

    if kind == "admin":
        if key not in data:
            raise HTTPException(404, f"Admin-commando '{key}' niet gevonden")
        if field == "triggers":
            if "triggers" not in data[key]:
                data[key]["triggers"] = []
            return data[key], "triggers"
        raise HTTPException(400, "Admin ondersteunt alleen 'triggers'")

    if kind == "system":
        if key not in data:
            raise HTTPException(404, f"Systeem-groep '{key}' niet gevonden")
        val = data[key]
        if isinstance(val, list):
            # Directe lijst = responses-only
            if field != "responses":
                raise HTTPException(400, "Deze groep heeft alleen responses")
            return data, key  # parent[key] is direct de lijst
        if isinstance(val, dict):
            if field == "triggers":
                if "triggers" not in val:
                    val["triggers"] = []
                return val, "triggers"
            if field == "responses":
                if "responses" not in val:
                    val["responses"] = []
                return val, "responses"
        raise HTTPException(400, f"Onverwacht type voor system/{key}")

    if kind == "credits":
        # key = 'namen' of 'extra_dank', altijd opgeslagen als 'triggers' in UI
        if key not in ("namen", "extra_dank"):
            raise HTTPException(404, f"Credits-groep '{key}' bestaat niet (gebruik 'namen' of 'extra_dank')")
        if field != "triggers":
            raise HTTPException(400, "Credits ondersteunt alleen 'triggers'")
        if key not in data or not isinstance(data[key], list):
            data[key] = []
        return data, key

    if kind == "vocab":
        # key kan zijn: "openers", "afsluiters", "twijfel", etc OF "algemeen/openers"
        if "/" in key:
            section, subkey = key.split("/", 1)
        else:
            section, subkey = "algemeen", key
        if field != "triggers":
            raise HTTPException(400, "Vocab ondersteunt alleen 'triggers' (lijst van woorden)")
        if section not in data or not isinstance(data[section], dict):
            data[section] = {}
        if subkey not in data[section] or not isinstance(data[section][subkey], list):
            data[section][subkey] = []
        return data[section], subkey

    raise HTTPException(400, f"Onbekend kind: {kind}")


@router.post("/edit/{kind}/{key}/add")
async def edit_add_word(kind: str, key: str, body: TriggerWord):
    """Voeg een woord/zin toe aan triggers of responses van een groep."""
    word = (body.word or "").strip()
    if not word:
        raise HTTPException(400, "Woord/zin mag niet leeg zijn")
    field = body.field or "triggers"
    fp = _kind_file(kind)
    data = load_json(fp, default={})
    parent, list_key = _get_list_ref(data, kind, key, field)

    # Speciaal voor emotion.triggers: dict {word: score}
    if kind == "emotion" and field == "triggers":
        triggers = parent.setdefault("triggers", {})
        if word in triggers:
            return {"success": False, "message": "Bestaat al", "list": list(triggers.keys())}
        triggers[word] = 3
        data.setdefault("emotions", {})[key] = parent
    else:
        target = parent[list_key]
        if word in target:
            return {"success": False, "message": "Bestaat al", "list": target}
        target.append(word)
        parent[list_key] = target

    data.setdefault("metadata", {})["last_updated"] = datetime.now().isoformat()
    save_json(fp, data)
    return {"success": True}


@router.delete("/edit/{kind}/{key}/{field}/{word}")
async def edit_delete_word(kind: str, key: str, field: str, word: str):
    """Verwijder een woord/zin uit triggers of responses."""
    fp = _kind_file(kind)
    data = load_json(fp, default={})
    parent, list_key = _get_list_ref(data, kind, key, field)

    if kind == "emotion" and field == "triggers":
        triggers = parent.setdefault("triggers", {})
        if word not in triggers:
            raise HTTPException(404, f"Woord '{word}' niet gevonden")
        del triggers[word]
        data.setdefault("emotions", {})[key] = parent
    else:
        target = parent[list_key]
        if word not in target:
            raise HTTPException(404, f"Item '{word}' niet gevonden")
        parent[list_key] = [w for w in target if w != word]

    data.setdefault("metadata", {})["last_updated"] = datetime.now().isoformat()
    save_json(fp, data)
    return {"success": True}
