"""
v6_chat_routes_split_001 — Helpers geëxtraheerd uit chat/routes.py om de hoofdfile
onder 1700 lines te krijgen. Alle functions blijven identiek; chat/routes.py
re-exporteert ze zodat externe imports niets merken.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from modules.core.storage import load_json
from . import chat_log_service, shadow_observer


_DATA_ROOT = Path(__file__).parent.parent.parent / "data"
_USERS_FILE = _DATA_ROOT / "system" / "users.json"


def save_log(req, response: dict, trigger_type):
    """Save gesprek naar user log + side-effects (warmth, TTS-pad, sound-hook,
    shadow observer, A/B-diff, intent-log).

    v6_warmth_layer_001 — bij sterke negatieve emotie op info-route wordt een
    korte erkenningszin uit kernwaarde laag1 voorgevoegd.
    """
    # v6_warmth_layer_001
    try:
        from modules.emotion_pipeline import warmth as _warmth
        _route = trigger_type or response.get("type") or "unknown"
        _warmth.maybe_apply_warmth(
            response=response,
            pipeline_summary=response.get("emotion_pipeline_shadow"),
            current_route=_route,
        )
    except Exception:
        pass

    # v5_tts_pad_001
    try:
        from . import tts_friendly_service
        tts_friendly_service.maybe_pad_for_tts(response)
    except Exception:
        pass

    # v6_kb_sound_001 — KB-kaart geluid hook
    try:
        if req.user_id and response.get("message"):
            sfile = _DATA_ROOT / "settings" / f"user_{req.user_id}.json"
            if sfile.exists():
                upref = load_json(sfile, default={})
                if upref.get("kb_sound_enabled"):
                    from modules.kb_v2 import sound_lookup as _sl
                    hit = _sl.find_sound_for_text(response.get("message") or "")
                    if hit:
                        response["sound_begrip"] = hit[0]
                        response["sound_url"] = hit[1]
    except Exception as ex:
        print(f"[kb-sound-hook] failed: {ex}")

    if not req.user_id:
        return
    chat_log_service.save_message(
        user_id=req.user_id,
        user_naam=req.user_naam or "Gebruiker",
        user_message=req.message,
        spark_response=response.get("message", ""),
        analysis={
            "sentiment": response.get("sentiment"),
            "emotion": response.get("emotion"),
            "trigger_type": trigger_type,
            "knowledge_matches": [{"begrip": m.get("begrip")} for m in response.get("knowledge_matches", [])],
            "unknown_words": response.get("unknown_words", []),
            "snap_suggestions": response.get("snap_suggestions", []),
            "word_count": len(req.message.split()),
            "response_type": response.get("type"),
        },
        channel=req.channel or "spark",
        session_id=req.session_id,
    )
    # Shadow Observer
    try:
        shadow_observer.record(req.user_id, req.message, response, trigger_type)
    except Exception:
        pass

    # v6_emotion_pipeline_ab_001 — A/B diff-log
    try:
        _ab_entry = build_ab_entry(req, response, trigger_type)
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ab_dir = _DATA_ROOT / "emotions" / "pipeline_ab"
        ab_dir.mkdir(parents=True, exist_ok=True)
        with open(ab_dir / f"{day}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(_ab_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

    # v6_command_registry_001 — intent-log
    try:
        from modules.intent_registry.extractor import extract_tags as _extract_tags
        _pipe_summary = response.get("emotion_pipeline_shadow") or {}
        _tag_vector = _extract_tags(req.message, _pipe_summary)
        _intent_log = _DATA_ROOT / "system" / "intent_log.jsonl"
        _intent_log.parent.mkdir(parents=True, exist_ok=True)
        _entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "user_id": req.user_id,
            "text": (req.message or "")[:200],
            "tag_vector": _tag_vector,
            "tag_key": "|".join(sorted(_tag_vector)),
            "chosen_route": trigger_type,
            "chosen_command_id": response.get("capability_id"),
        }
        with open(_intent_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def build_ab_entry(req, response, trigger_type) -> dict:
    """v6_emotion_pipeline_ab_001 — bouw 1 vergelijkingsregel.

    Toont welke route smart_intents/capabilities koos vs welke pipeline zou adviseren.
    """
    pipeline_summary = response.get("emotion_pipeline_shadow") or {}
    current_route = trigger_type or response.get("type") or "unknown"
    pipeline_behavior = pipeline_summary.get("behavior")
    diff_status = "match"
    diff_note = "geen significant verschil"
    if pipeline_summary:
        emo = pipeline_summary.get("emotie")
        weging = pipeline_summary.get("weging")
        info_routes = {
            "identity_about", "capability_response", "capability_placeholder",
            "info", "knowledge", "unknown", "fallback", "time_now",
            "kbv2_cmd_inbox", "kbv2_cmd_audit", "how_are_you",
            "kbv2_tell_kort", "kbv2_tell_meer", "kbv2_tell_diep", "kbv2_tell_volledig",
            "kbv2_cmd_search", "kbv2_cmd_known", "kbv2_cmd_learned",
        }
        active_behaviors = {
            "begrenzen-structureren": "Sterke negatieve emotie — pipeline zou structureren/begrenzen",
            "vertragen-ondersteunen":  "Negatieve emotie — pipeline zou vertragen/ondersteunen",
            "kalmeren-opties":         "Angst-emotie — pipeline zou kalmeren met opties",
        }
        if pipeline_behavior in active_behaviors and current_route in info_routes:
            diff_status = "mismatch"
            diff_note = f"{active_behaviors[pipeline_behavior]} ({emo}, {weging}); systeem koos info-route '{current_route}'"
        elif pipeline_behavior == "exploreren-uitbreiden" and current_route in ("fallback", "unknown"):
            diff_status = "potential"
            diff_note = "Blije emotie — pipeline zou kunnen uitbreiden, systeem viel terug"
        elif not pipeline_behavior:
            diff_status = "neutraal"
            diff_note = "Geen pipeline-output"
    else:
        diff_status = "no_pipeline"
        diff_note = "Pipeline draaide niet"
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": req.user_id,
        "msg_preview": (req.message or "")[:100],
        "current_route": current_route,
        "current_type": response.get("type"),
        "pipeline_summary": pipeline_summary,
        "diff_status": diff_status,
        "diff_note": diff_note,
    }


def get_user_gradatie(user_id):
    """Haal gradatie van user op. Return None als niet gevonden."""
    if not user_id:
        return None
    data = load_json(_USERS_FILE, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id:
            return u.get("gradatie")
    return None


def get_user_for_time(user_id):
    """Haal volledig user-record op voor tijdzone-resolutie."""
    if not user_id:
        return None
    data = load_json(_USERS_FILE, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id:
            return u
    return None
