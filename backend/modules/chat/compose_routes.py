"""v6_response_composer_001 — Endpoints voor Spark's gespreks-synthesizer.

POST /api/spark/compose                  — vraag een gesynthesizeerd antwoord
GET  /api/spark/compose/blueprint        — lees huidige blueprint config
POST /api/spark/compose/blueprint/reload — clear cache (na handmatige edit)
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from modules.chat.response_composer import compose_response
from modules.core.blueprint import load_blueprint, clear_blueprint_cache

router = APIRouter(prefix="/spark/compose", tags=["spark-compose"])

BP_FP = Path(__file__).parent / "blueprints" / "response_composer.json"


class ComposeRequest(BaseModel):
    text: str
    user_id: Optional[str] = "user-001"
    session_id: Optional[str] = None
    emotion: Optional[str] = None
    active_tab: Optional[str] = None  # v6_tab_context_001 — welke tab user nu bekijkt


@router.post("")
async def compose(req: ComposeRequest):
    """Synthesizeer een gespreks-antwoord vanuit KB + bijbel + turns.

    v13d_compose_capability_hook_001 (sessie 55) — Willem: op de Spark-tab werken
    capabilities niet, want frontend gaat via /api/spark/compose (LLM-direct)
    i.p.v. /api/chat/message (capability-router). Fix: eerst dezelfde intent-checks
    doen als in /api/chat/message; alleen als niets matcht → LLM aanroepen.
    """
    text = (req.text or "").strip()
    if not text:
        return {"success": False, "error": "empty text"}

    # 1) HANDS-FIRST intent-hooks — DELETE flows en direct-execute capabilities
    #    krijgen voorrang. Als één matcht → direct return, geen LLM-oproep.
    try:
        from . import smart_intents_service as si
        from . import session_state
        from modules.chat import wedervraag_service, snap_service
        _snap = snap_service.SnapNLPService()
        # Pending-states eerst (multi-turn confirmations)
        state = session_state.get_state(req.user_id or "user-001")

        pending_ad = state.get("pending_agenda_delete")
        pending_sd = state.get("pending_shop_delete")

        if pending_sd:
            step = pending_sd.get("step")
            if si.is_no(text) or wedervraag_service.is_skip(text):
                session_state.set_state(req.user_id, pending_shop_delete=None)
                out = si.handle_shop_delete_cancel()
                return {"success": True, "message": out["message"], "type": out["type"], "used_model": "hands"}
            if step == "choose":
                # Bij choose mag alleen nummer/alle/ja/nee — anders is dat verwarrend
                import re as _re
                if _re.match(r"^\s*(alle|allemaal|all|\d+)\s*$", text.lower()):
                    out = si.handle_shop_delete_choose(pending_sd, text)
                    if isinstance(out.get("pending_state"), dict):
                        session_state.set_state(req.user_id, pending_shop_delete=out["pending_state"])
                    return {"success": True, "message": out["message"], "type": out["type"], "used_model": "hands"}
                # Anders: clear pending en val door naar normale flow
                session_state.set_state(req.user_id, pending_shop_delete=None)
            elif si.is_yes(text) or _snap.detect_confirmation(text):
                ids = pending_sd.get("shop_ids") or []
                out = si.execute_shop_delete(req.user_id, ids)
                session_state.set_state(req.user_id, pending_shop_delete=None)
                return {"success": True, "message": out["message"], "type": out["type"], "used_model": "hands"}
            else:
                # Bij step==1 en tekst duidelijk iets ANDERS (langer dan een ja/nee/nummer),
                # clear pending en val door naar normale flow. Alleen bij héél korte input
                # (≤ 4 woorden) blijven we bij de "typ ja of nee" herhaling.
                if len(text.split()) > 4:
                    session_state.set_state(req.user_id, pending_shop_delete=None)
                else:
                    return {"success": True,
                            "message": f"Nog even bevestigen: **{pending_sd.get('summary','winkel')}** verwijderen? Typ **ja** of **nee**.",
                            "type": "shop_delete_repeat", "used_model": "hands"}

        if pending_ad:
            step = pending_ad.get("step")
            if si.is_no(text) or wedervraag_service.is_skip(text):
                session_state.set_state(req.user_id, pending_agenda_delete=None)
                out = si.handle_agenda_delete_cancel()
                return {"success": True, "message": out["message"], "type": out["type"], "used_model": "hands"}
            if step == "choose":
                import re as _re
                if _re.match(r"^\s*(alle|allemaal|all|\d+)\s*$", text.lower()):
                    out = si.handle_agenda_delete_choose(pending_ad, text)
                    if isinstance(out.get("pending_state"), dict):
                        session_state.set_state(req.user_id, pending_agenda_delete=out["pending_state"])
                    return {"success": True, "message": out["message"], "type": out["type"], "used_model": "hands"}
                session_state.set_state(req.user_id, pending_agenda_delete=None)
            elif si.is_yes(text) or _snap.detect_confirmation(text):
                ids = pending_ad.get("event_ids") or []
                out = si.execute_agenda_delete(req.user_id, ids)
                session_state.set_state(req.user_id, pending_agenda_delete=None)
                return {"success": True, "message": out["message"], "type": out["type"], "used_model": "hands"}
            else:
                if len(text.split()) > 4:
                    session_state.set_state(req.user_id, pending_agenda_delete=None)
                else:
                    return {"success": True,
                            "message": f"Nog even bevestigen: **{pending_ad.get('summary','afspraak')}** verwijderen? Typ **ja** of **nee**.",
                            "type": "agenda_delete_repeat", "used_model": "hands"}

        # Nieuwe intents (delete-starts)
        if req.user_id and si.detect_shop_delete_intent(text):
            out = si.handle_shop_delete_start(req.user_id, text)
            if isinstance(out.get("pending_state"), dict):
                session_state.set_state(req.user_id, pending_shop_delete=out["pending_state"])
            return {"success": True, "message": out["message"], "type": out["type"], "used_model": "hands"}

        # v13d_agenda_create_compose_001 (sessie 55) — Willem: "gedeployde Spark
        # kan niet in agenda schrijven". Root cause: compose (Spark-tab) had
        # geen CREATE-hook. Flow: detect → proposal + pending_agenda → ja → create.
        pending_ac = state.get("pending_agenda")
        if pending_ac:
            if si.is_yes(text) or _snap.detect_confirmation(text):
                # Schrijf event weg (kopie van chat/routes.py create-flow)
                import uuid as _uuid
                from pathlib import Path as _Path
                from datetime import datetime as _dt, timezone as _tz
                from modules.core.storage import load_json as _lj, save_json as _sj
                from . import agenda_intent_service
                ag_file = _Path(__file__).parent.parent.parent / "data" / "agenda" / f"{req.user_id}.json"
                ag_data = _lj(ag_file, default={"events": []})
                new_event = {
                    "id": str(_uuid.uuid4())[:8],
                    "titel": agenda_intent_service.format_event_title(pending_ac),
                    "beschrijving": f"Genoteerd via chat: {pending_ac.get('raw_text','')}",
                    "date": pending_ac["datetime_iso"],
                    "end_date": pending_ac.get("end_datetime_iso"),
                    "duration_minutes": pending_ac.get("duration_minutes"),
                    "location": pending_ac.get("waar", ""),
                    "reminder": False,
                    "status": "upcoming",
                    "created_at": _dt.now(_tz.utc).isoformat(),
                    "source": "chat-intent-compose",
                }
                ag_data["events"].append(new_event)
                _sj(ag_file, ag_data)
                session_state.set_state(req.user_id, pending_agenda=None)
                return {"success": True,
                        "message": f"📅 Genoteerd! **{new_event['titel']}** staat in je agenda.",
                        "type": "agenda_created", "agenda_event": new_event, "used_model": "hands"}
            if si.is_no(text) or wedervraag_service.is_skip(text):
                session_state.set_state(req.user_id, pending_agenda=None)
                return {"success": True,
                        "message": "Oké, ik laat het zo. Niks in je agenda gezet.",
                        "type": "agenda_declined", "used_model": "hands"}
            # geen ja/nee bij langere text → clear pending en val door
            if len(text.split()) > 4:
                session_state.set_state(req.user_id, pending_agenda=None)

        # CREATE-intent detectie (nieuwe afspraak in chat)
        if req.user_id:
            try:
                from . import agenda_intent_service
                from modules.auth.service import AuthService as _Auth
                _user_ac = _Auth.get_user_by_id(req.user_id)
                create_intent = agenda_intent_service.detect_agenda_intent(text, user=_user_ac)
                if create_intent.get("has_intent"):
                    has_conflict = agenda_intent_service.has_agenda_conflict(req.user_id, create_intent["datetime_iso"])
                    session_state.set_state(req.user_id, pending_agenda=create_intent)
                    return {"success": True,
                            "message": agenda_intent_service.build_proposal_message(create_intent, has_conflict),
                            "type": "agenda_proposal", "used_model": "hands"}
            except Exception as _ex_create:
                print(f"[compose-agenda-create] {_ex_create}")

        if req.user_id and si.detect_agenda_delete_intent(text):
            from modules.auth.service import AuthService
            _user = AuthService.get_user_by_id(req.user_id)
            out = si.handle_agenda_delete_start(req.user_id, _user, text)
            if isinstance(out.get("pending_state"), dict):
                session_state.set_state(req.user_id, pending_agenda_delete=out["pending_state"])
            return {"success": True, "message": out["message"], "type": out["type"], "used_model": "hands"}

        # 2) Capability-router (tellen_gebruikers, gebruikers_namen, etc.)
        from . import capability_handler_service
        cap_resp = capability_handler_service.route_capability(text, req.user_id)
        if cap_resp and cap_resp.get("type") != "capability_placeholder":
            return {
                "success": True,
                "message": cap_resp.get("message", ""),
                "type": cap_resp.get("type", "capability_response"),
                "capability_id": cap_resp.get("capability_id"),
                "used_model": "hands",
            }
    except Exception as _hook_ex:
        # Nooit de LLM-flow blokkeren door een hook-fout; log naar stdout en ga door.
        print(f"[compose-hands-hook] {_hook_ex}")

    # 3) Fallback: LLM-synthesizer (originele flow)
    result = await compose_response(
        user_text=req.text,
        user_id=req.user_id or "user-001",
        session_id=req.session_id,
        emotion=req.emotion,
        active_tab=req.active_tab,
    )
    return result


@router.get("/blueprint")
async def get_blueprint():
    """Toon de huidige Response Composer blueprint config (read-only voorbeeld)."""
    try:
        bp = load_blueprint("chat", "response_composer")
        return {"success": True, "blueprint": bp, "path": str(BP_FP)}
    except FileNotFoundError as ex:
        raise HTTPException(404, str(ex))


@router.post("/blueprint/reload")
async def reload_blueprint():
    """Clear blueprint-cache na handmatige edit van het JSON-bestand."""
    clear_blueprint_cache()
    return {"success": True, "msg": "Blueprint cache cleared. Volgende /compose-call gebruikt verse JSON."}


# v6_snuffel_bestand_001 — directe API voor file-search
class SnuffelRequest(BaseModel):
    query: str
    viewer_id: Optional[str] = None
    scope: Optional[list] = None  # ['kb', 'notes', 'personality', 'chat']


@router.post("/snuffel")
async def snuffel_bestand(req: SnuffelRequest):
    """Spark doorzoekt eigen JSON-data en geeft hits per bron."""
    from modules.chat.spark_snuffel import execute_snuffel
    result = execute_snuffel(req.query, viewer_id=req.viewer_id, scope=req.scope)
    return result


# v6_trigger_learner_001 — admin endpoints voor learned triggers
@router.get("/learned-triggers")
async def list_learned_triggers(limit: int = 50, status: Optional[str] = None):
    """Lijst van LLM-voorgestelde triggers wachtend op admin-review."""
    try:
        from modules.chat.trigger_learner import _load_learned
        data = _load_learned()
        voorstellen = data.get("voorstellen", [])
        if status:
            voorstellen = [v for v in voorstellen if v.get("status") == status]
        # Nieuwste eerst
        return {
            "success": True,
            "totaal": len(voorstellen),
            "voorstellen": voorstellen[-limit:][::-1],
            "statistieken": data.get("statistieken", {}),
        }
    except Exception as ex:
        raise HTTPException(500, str(ex))


@router.post("/learned-triggers/{voorstel_id}/approve")
async def approve_trigger(voorstel_id: str):
    from modules.chat.trigger_learner import approve
    ok = approve(voorstel_id)
    if not ok:
        raise HTTPException(404, f"Voorstel {voorstel_id} niet gevonden")
    return {"success": True, "voorstel_id": voorstel_id, "status": "approved"}


@router.post("/learned-triggers/{voorstel_id}/reject")
async def reject_trigger(voorstel_id: str):
    from modules.chat.trigger_learner import reject
    ok = reject(voorstel_id)
    if not ok:
        raise HTTPException(404, f"Voorstel {voorstel_id} niet gevonden")
    return {"success": True, "voorstel_id": voorstel_id, "status": "rejected"}
