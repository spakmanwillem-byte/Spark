"""v6_chat_routes_split_001 — Extra chat-endpoints.

Uit routes.py geëxtraheerd om dat bestand onder ~1900 regels te krijgen.
Bevat: logs, intent matching, snap, lookup, emotions, shadow observer,
welkom, en relay-inbox endpoints.

Eigen APIRouter met zelfde /chat prefix — FastAPI merged ze op app-level.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import secrets

from .snap_service import SnapNLPService
from .emotion_service import EmotionDetectionService
from . import chat_log_service
from . import shadow_observer
from modules.core.spark_logger import traced

router = APIRouter(prefix="/chat", tags=["chat"])
snap = SnapNLPService()


class SnapRequest(BaseModel):
    text: str
    user_id: str = "user-001"


class ChatMessage(BaseModel):
    user_id: str
    user_naam: str
    message: str
    channel: Optional[str] = "spark-private"
    session_id: Optional[str] = None
    consent: Optional[bool] = None


# ============================================================
# CHAT LOGS / ARCHIEF
# ============================================================

@router.get("/logs/{user_id}")
async def get_chat_logs(user_id: str, limit: int = 50, offset: int = 0,
                        search: Optional[str] = None, channel: Optional[str] = None,
                        has_trigger: Optional[bool] = None, has_snap: Optional[bool] = None):
    return chat_log_service.get_logs(user_id, limit, offset, search, channel, has_trigger, has_snap)


@router.get("/logs/{user_id}/stats")
async def get_chat_log_stats(user_id: str):
    return chat_log_service.get_stats(user_id)


@router.get("/logs")
async def list_all_log_users():
    """Admin: lijst alle users die logs hebben."""
    return {"users": chat_log_service.list_all_users_with_logs()}


# v6_intent_matcher_001 — Spark's handen: capability-matcher endpoint
@router.post("/intent/match")
async def match_intent(payload: dict):
    """Match een user-zin → capability_id.

    Body: {"text": "kan jij mijn trade-logs ophalen?"}
    Returns: {"match": {...} | null}
    """
    from .intent_matcher_service import match_capability
    text = (payload or {}).get("text", "")
    result = match_capability(text)
    return {"match": result, "text": text}


@router.get("/intent/capabilities")
async def list_capabilities(status: Optional[str] = None):
    """Lijst alle Spark-capabilities (optioneel gefilterd op status)."""
    from .intent_matcher_service import all_capabilities, explain_self
    return {
        "capabilities": all_capabilities(status),
        "explain_self": explain_self(),
    }



@router.delete("/logs/{user_id}/{conv_id}")
async def delete_log(user_id: str, conv_id: str):
    success = chat_log_service.delete_conversation(user_id, conv_id)
    return {"success": success}


@router.post("/snap")
async def create_snap(req: SnapRequest):
    """Maak een knowledge snap (woord of zin)"""
    if req.is_sentence:
        result = snap.create_sentence_snap(req.concept, req.context, req.user_naam)
    else:
        result = snap.create_word_snap(req.concept, req.context, req.user_naam)

    if result is None:
        return {"success": False, "message": "Kon geen snap aanmaken (bestaat al of is een stopwoord)"}

    return {
        "success": True,
        "message": f"Snap '{result['begrip']}' aangemaakt!",
        "entry": {
            "id": result["id"],
            "begrip": result["begrip"],
            "status": result["status"],
        }
    }


@router.get("/lookup/{query}")
async def lookup_knowledge(query: str):
    """Direct knowledge lookup op een begrip"""
    result = snap.lookup(query)
    if not result:
        return {"found": False, "query": query}
    return {"found": True, "query": query, "result": result}


@router.get("/emotions/state")
async def get_emotion_state():
    """Spark's huidige emotionele staat"""
    return EmotionDetectionService.get_spark_state()


@router.get("/emotions/all")
async def get_all_emotions():
    """Alle Spark emotie definities (happy, angry, etc met sub-emoties)"""
    return EmotionDetectionService.get_spark_emotions()


@router.get("/emotions/learned")
async def get_learned_emotions():
    """Hoeveel emotie woorden geleerd uit knowledge cards"""
    return EmotionDetectionService.get_learned_counts()


@router.post("/emotions/detect")
async def detect_emotion(req: ChatMessage):
    """Detecteer emotie in tekst (test endpoint)"""
    result = EmotionDetectionService.detect_emotion(req.message)
    return {"detected": result is not None, "emotion": result}



# ============================================================
# SHADOW OBSERVER (v4_015) — read-only inzicht
# ============================================================

@router.get("/shadow/stats")
async def shadow_stats():
    """Aggregate counters van Spark's chat-gedrag (triggers, vocab, fallbacks, etc.)"""
    return shadow_observer.get_stats()


@router.get("/shadow/recent")
async def shadow_recent(limit: int = 50, user_id: Optional[str] = None):
    """Laatste N chat-events (laatste dag eerst). Filter optioneel op user_id."""
    return {"events": shadow_observer.get_recent_events(limit=limit, user_id=user_id)}


@router.get("/shadow/unused")
async def shadow_unused():
    """Items in JSON-bestanden die NOOIT zijn gebruikt — input voor latere Analyser/Advisor."""
    return shadow_observer.get_unused_items()


@router.get("/shadow/corrections")
async def shadow_corrections(limit: int = 20):
    """Momenten waarop user 'nee/fout/verkeerd' zei — basis voor zelf-lering."""
    return {"corrections": shadow_observer.get_correction_examples(limit=limit)}


@router.post("/shadow/reset")
async def shadow_reset():
    """Admin: reset aggregate stats (events op disk blijven staan)."""
    return shadow_observer.reset_stats()



# ============================================================
# WELKOM (v4_welcome_001) — Spark zegt zelf hallo bij login/chat-open
# Hierdoor weet Spark in zijn log dat hij iets gezegd heeft, dus
# Chat Recap / Shadow Observer / context-flow werken voor sessie-start.
# ============================================================

from pydantic import BaseModel as _BM


class WelcomeRequest(_BM):
    user_id: str
    user_naam: Optional[str] = None
    session_id: Optional[str] = None
    silent: Optional[bool] = False  # als True: alleen genereren, niet loggen
    deep: Optional[bool] = False  # v6_deep_welcome_001: LLM-gegenereerd welkom (Spark spreekt zelf)


@router.post("/welcome")
async def chat_welcome(req: WelcomeRequest):
    """Genereer een tijd-bewuste welkomstboodschap + log naar chat_log + shadow.

    Sessie 30: als req.deep=True wordt het welkom door Spark zelf gecomponeerd via
    de compose-flow (KB + bijbel + planner-brief + threads). Tonality past zich
    automatisch aan op gradatie. Anders: snelle template-flow (admin gebruikt deze).
    """
    import random
    from modules.core.storage import load_json as _lj
    from pathlib import Path as _P

    # v6_deep_welcome_001 — als deep=True: Spark componeert zijn eigen welkom
    if req.deep:
        try:
            from modules.chat.response_composer import compose_response
            # Synthetische user-text die Spark dwingt een welkom te formuleren
            welcome_prompt = (
                "[SYSTEEM-CONTEXT: dit is het allereerste bericht van een nieuwe sessie. "
                "De gebruiker heeft net de chat geopend en jij spreekt als eerste. "
                "Begin met een warme, korte begroeting (1-3 zinnen) — geen vraag aan het einde verplicht. "
                "Toon: dezelfde diepe, eerlijke Spark-stem als in een diep gesprek. "
                "Pas je toon aan op gradatie en eventuele brief van eerder gesprek. "
                "Spreek als jij, niet als een chatbot-template.]"
            )
            result = await compose_response(
                welcome_prompt,
                user_id=req.user_id,
                session_id=req.session_id,
                emotion=None,
            )
            if result.get("success") and result.get("message"):
                msg = result["message"].strip()
                # Log alleen niet als silent
                if not req.silent:
                    try:
                        chat_log_service.add_message(
                            user_id=req.user_id,
                            session_id=req.session_id or f"welcome-{req.user_id}",
                            role="spark",
                            text=msg,
                        )
                    except Exception:
                        pass
                return {
                    "success": True,
                    "message": msg,
                    "mode": "deep",
                    "used_model": result.get("used_model"),
                }
        except Exception:
            pass  # fallback naar template-flow

    # User ophalen
    user = None
    udata = _lj(_P(__file__).parent.parent.parent / "data" / "system" / "users.json", default={"users": []})
    for u in udata.get("users", []):
        if u.get("id") == req.user_id:
            user = u
            break
    naam = req.user_naam or (user or {}).get("naam") or "vriend"
    # Voornaam zonder achternaam
    voornaam = naam.split()[0] if naam else "vriend"
    if voornaam.lower() in ("de", "den", "van", "der"):
        # "De Willem" → "Willem"
        parts = naam.split()
        if len(parts) >= 2:
            voornaam = parts[1]

    # Tijd-context
    from . import user_time_service as _uts
    ta = _uts.time_awareness_block(user)
    dagdeel = ta.get("dagdeel", "")
    DAGDEEL_GROET = {
        "ochtend": "Goedemorgen",
        "middag": "Goedemiddag",
        "avond": "Goedenavond",
        "nacht": "Goedenacht",
    }
    dagdeel_groet = DAGDEEL_GROET.get(dagdeel, "Hallo")

    # __startup trigger uitlezen
    triggers = _lj(_P(__file__).parent.parent.parent / "data" / "triggers" / "conversation_triggers.json", default={})
    startup = triggers.get("__startup", {}) if isinstance(triggers, dict) else {}
    responses = startup.get("responses", []) or [
        "{dagdeel_groet} {naam}. Wat speelt er?",
    ]
    template = secrets.choice(responses)
    message = template.format(naam=voornaam, dagdeel_groet=dagdeel_groet)

    # Optioneel: contextuele suffix
    suffix_parts = []
    # 1) Laatste sessie tijd
    last = chat_log_service.get_last_conversation(req.user_id) if hasattr(chat_log_service, "get_last_conversation") else None
    if last:
        try:
            from datetime import datetime as _dt, timezone as _tz
            last_ts = last.get("timestamp")
            if last_ts:
                if last_ts.endswith("Z"):
                    last_ts = last_ts[:-1] + "+00:00"
                last_dt = _dt.fromisoformat(last_ts)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=_tz.utc)
                hours_ago = (_dt.now(_tz.utc) - last_dt).total_seconds() / 3600
                if 1 <= hours_ago < 24:
                    suffix_parts.append(f"_(laatst sprak je me {int(hours_ago)} uur geleden)_")
                elif hours_ago >= 24 and hours_ago < 24 * 14:
                    suffix_parts.append(f"_(het is {int(hours_ago/24)} dagen geleden dat we praatten)_")
        except Exception:
            pass

    full_message = message + ((" " + " ".join(suffix_parts)) if suffix_parts else "")

    # v4_agenda_announce_001: Spark meldt aankomende afspraak in welcome
    try:
        from modules.urgent.routes import upcoming_spoken as _us
        upcoming = await _us(req.user_id)
        if upcoming and upcoming.get("message"):
            full_message += "\n\n" + upcoming["message"]
    except Exception:
        pass

    response = {
        "type": "welcome",
        "message": full_message,
        "dagdeel": dagdeel,
        "dagdeel_groet": dagdeel_groet,
        "voornaam": voornaam,
    }

    # Log naar chat_log + shadow (tenzij silent)
    if not req.silent and req.user_id:
        try:
            chat_log_service.save_message(
                user_id=req.user_id,
                user_naam=naam,
                user_message="[system:login]",
                spark_response=full_message,
                analysis={"trigger_type": "welcome", "response_type": "welcome", "dagdeel": dagdeel},
                channel="spark",
                session_id=req.session_id,
            )
            shadow_observer.record(req.user_id, "[system:login]", response, "welcome")
        except Exception:
            pass

    return response



# v6_spark_relay_001 (28 mei) — Inbox endpoints
@router.get("/relay/inbox/{user_id}")
async def get_relay_inbox(user_id: str, limit: int = 50):
    from . import relay_service
    msgs = relay_service.get_inbox(user_id, limit)
    unread = sum(1 for m in msgs if not m.get("read"))
    return {"success": True, "messages": msgs, "count": len(msgs), "unread": unread}


@router.post("/relay/inbox/{user_id}/read/{message_id}")
async def mark_relay_read(user_id: str, message_id: str):
    from . import relay_service
    ok = relay_service.mark_read(user_id, message_id)
    return {"success": ok}
