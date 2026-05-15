"""
Chat Routes - Spark AI chat met Snap/NLP knowledge lookup
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import random
from .snap_service import SnapNLPService
from .emotion_service import EmotionDetectionService
from . import chat_log_service
from . import session_state
from . import xp_service
from . import self_state_service
from . import wedervraag_service
from . import agenda_intent_service
from . import scan_service
from . import compositional_service
from . import spontaneous_w_service
from . import card_session_service
from . import bijbel_lookup_service
from . import fallback_service
from . import shadow_observer

router = APIRouter(prefix="/chat", tags=["chat"])
snap = SnapNLPService()

# XP beloning voor homoniem-disambiguatie (v3_013)
HOMONYM_XP_BONUS = 15


class ChatMessage(BaseModel):
    message: str
    user_naam: Optional[str] = "Gebruiker"
    user_id: Optional[str] = None
    channel: Optional[str] = "spark"
    session_id: Optional[str] = None


class SnapRequest(BaseModel):
    concept: str
    context: Optional[str] = ""
    user_naam: Optional[str] = "Gebruiker"
    is_sentence: bool = False


@router.post("/message")
async def process_message(req: ChatMessage):
    """
    Verwerk een chat bericht:
    1. Check triggers (begroeting, bedankt, hoe gaat het)
    2. Zoek begrippen in knowledge base
    3. Geef antwoord op basis van lagen
    4. Detecteer onbekende woorden (voor snap suggesties)
    """
    text = req.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Leeg bericht")

    response = {
        "type": "response",
        "message": "",
        "knowledge_matches": [],
        "sentiment": snap.detect_sentiment(text),
        "emotion": None,
        "unknown_words": [],
        "snap_suggestions": [],
    }

    # 0. Emotie detectie (hybride: static + learned van knowledge cards)
    emotion = EmotionDetectionService.detect_emotion(text)
    if emotion:
        response["emotion"] = emotion

    # 0b. HOMONIEM-FLOW (v3_012) — check session state eerst
    state = session_state.get_state(req.user_id) if req.user_id else {}

    # 0z. KAART-SESSIE FLOW (v4_008): HOOGSTE prioriteit — als sessie actief is,
    # niets anders mag voorrang krijgen. Anders eet bv. agenda-intent of een
    # 'Wanneer ...'-antwoord de input op.
    pending_card_session = state.get("pending_card_session")
    if pending_card_session:
        if card_session_service.is_stop(text):
            session_state.set_state(req.user_id, pending_card_session=None)
            response["type"] = "card_session_stopped"
            response["message"] = fallback_service.pick(
                "card_session_stopped",
                "Oké, sessie gepauzeerd. Voortzetten? Typ 'ik wil kaarten invullen' om verder te gaan.",
            )
            _save_log(req, response, "card_session_stopped")
            return response
        # Skip → markeer huidig veld als overgeslagen
        if card_session_service.is_skip(text):
            cur_field_key = pending_card_session.get("current_field")  # bv "ws5.wat"
            if cur_field_key:
                skipped = pending_card_session.get("skipped_fields_for_card", [])
                if cur_field_key not in skipped:
                    skipped.append(cur_field_key)
                pending_card_session["skipped_fields_for_card"] = skipped
        else:
            # Antwoord opslaan in huidig veld
            cur_card = None
            queue = pending_card_session.get("queue", [])
            idx = pending_card_session.get("current_index", 0)
            if idx < len(queue):
                cur_card = queue[idx]
            cur_field_key = pending_card_session.get("current_field")  # "ws5.wat" of "laag.laag1" of "belangrijkheid.belangrijkheid"
            if cur_card and cur_field_key and "." in cur_field_key:
                cat, key = cur_field_key.split(".", 1)
                ok = card_session_service.apply_answer(cur_card, cat, key, text)
                if not ok and cat == "belangrijkheid":
                    # User gaf geen cijfer 1-5 — vraag opnieuw
                    response["type"] = "card_session_invalid"
                    response["message"] = "Geef een cijfer tussen 1 en 5 (bv. '3'). Of typ 'skip' om over te slaan."
                    _save_log(req, response, "card_session_invalid")
                    session_state.set_state(req.user_id, pending_card_session=pending_card_session)
                    return response
        # Volgende vraag bepalen
        next_q = card_session_service.next_question(pending_card_session)
        if next_q.get("done"):
            session_state.set_state(req.user_id, pending_card_session=None)
            response["type"] = "card_session_done"
            response["message"] = (
                f"Klaar! Sessie afgerond. Alle {pending_card_session.get('total', 0)} kaarten "
                "doorlopen. Tag 'sessie-ingevuld' staat op de bewerkte kaarten. "
                "Loop ze door in Kennisbank → Onbeantwoord om de 'auto-generated' tag eraf te halen."
            )
            _save_log(req, response, "card_session_done")
            return response
        session_state.set_state(req.user_id, pending_card_session=pending_card_session)
        progress = next_q.get("card_progress", (0, 0))
        response["type"] = "card_session_question"
        response["message"] = (
            f"_(Kaart {progress[0]}/{progress[1]}: **{next_q['begrip']}**)_\n\n"
            f"{next_q['question']}\n\n"
            f"_(antwoord, of typ 'skip' om dit veld over te slaan, 'stop' om te pauzeren)_"
        )
        response["card_session"] = {
            "card_id": next_q["card_id"],
            "begrip": next_q["begrip"],
            "category": next_q.get("category"),
            "field": next_q["field"],
            "progress": progress,
        }
        _save_log(req, response, "card_session_question")
        return response

    # 0z2. CHAT RECAP (v4_recap_001) — "wat hebben we gisteren middag besproken?"
    # Hoge prio: vóór alle andere intent-detectie, ná card-sessie.
    try:
        from . import chat_recap_service
        if chat_recap_service.detect_recap_intent(text):
            # Laad user voor timezone
            from pathlib import Path as _P
            from modules.core.storage import load_json as _lj
            user_obj = None
            if req.user_id:
                udata = _lj(_P(__file__).parent.parent.parent / "data" / "system" / "users.json", default={"users": []})
                for u in udata.get("users", []):
                    if u.get("id") == req.user_id:
                        user_obj = u
                        break
            recap = chat_recap_service.build_recap(user_obj, req.user_id, text)
            response.update(recap)
            _save_log(req, response, "recap")
            return response
    except Exception:
        pass

    # 0z3. SMART INTENTS (v4_intents_001) — agenda / notitie / help / suggest / clarify
    try:
        from . import smart_intents_service as si
        # Helper voor user obj
        def _load_user():
            if not req.user_id:
                return None
            from pathlib import Path as _P
            from modules.core.storage import load_json as _lj
            udata = _lj(_P(__file__).parent.parent.parent / "data" / "system" / "users.json", default={"users": []})
            for u in udata.get("users", []):
                if u.get("id") == req.user_id:
                    return u
            return None

        # Notitie: "maak notitie: ..." — eerst want letterlijke command
        matched, content = si.detect_note_intent(text)
        if matched and content:
            out = si.handle_note(_load_user(), req.user_id, content)
            response.update(out)
            _save_log(req, response, "make_note")
            return response

        # Agenda
        if si.detect_agenda_intent(text) and req.user_id:
            out = si.handle_agenda(req.user_id, _load_user(), text)
            response.update(out)
            _save_log(req, response, "agenda_overview")
            return response

        # Help
        if si.detect_help_intent(text):
            out = si.handle_help()
            response.update(out)
            _save_log(req, response, "help_overview")
            return response

        # Suggest "wat zullen we doen"
        if si.detect_suggest_intent(text) and req.user_id:
            out = si.handle_suggest(req.user_id, _load_user())
            response.update(out)
            _save_log(req, response, "suggest_action")
            return response

        # Clarify "nee dat bedoel ik niet"
        if si.detect_clarify_intent(text):
            last_begrip = state.get("last_begrip")
            out = si.handle_clarify(last_begrip)
            response.update(out)
            # Sla state op zodat volgende bericht als 'alternative word' wordt opgepakt
            session_state.set_state(req.user_id, pending_clarify={"last_begrip": last_begrip})
            _save_log(req, response, "clarify_question")
            return response

        # Topic overview: "vertel me over X" / "wat heb je over X"
        matched_topic, topic_q = si.detect_topic_intent(text)
        if matched_topic and topic_q:
            out = si.handle_topic_overview(topic_q)
            response.update(out)
            _save_log(req, response, "topic_overview")
            return response
    except Exception:
        pass

    # 0d. SPONTANE W-VULLING (v4_007): stille verrijking van actieve snap
    # Veiligheid: alleen op last_entry_id, alleen als nog auto-generated, alleen lege velden
    spontaneous_hint = ""
    if req.user_id and state.get("last_entry_id"):
        sp_fields = spontaneous_w_service.extract_w_fields(text)
        if sp_fields:
            filled = spontaneous_w_service.apply_to_active_card(state["last_entry_id"], sp_fields)
            if filled:
                spontaneous_hint = "\n\n" + spontaneous_w_service.build_hint(filled)

    # 0a. AGENDA-PROPOSAL-FLOW (v3_303): wachten op ja/nee voor genoteerd voorstel
    pending_agenda = state.get("pending_agenda")
    if pending_agenda:
        if snap.detect_confirmation(text):
            # Maak agenda-event
            import uuid
            from pathlib import Path as _Path
            from modules.core.storage import load_json as _lj, save_json as _sj
            ag_file = _Path(__file__).parent.parent.parent / "data" / "agenda" / f"{req.user_id}.json"
            ag_data = _lj(ag_file, default={"events": []})
            new_event = {
                "id": str(uuid.uuid4())[:8],
                "titel": agenda_intent_service.format_event_title(pending_agenda),
                "beschrijving": f"Genoteerd via chat: {pending_agenda.get('raw_text','')}",
                "date": pending_agenda["datetime_iso"],
                "location": pending_agenda.get("waar", ""),
                "reminder": False,
                "status": "upcoming",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "chat-intent",
            }
            ag_data["events"].append(new_event)
            _sj(ag_file, ag_data)
            session_state.set_state(req.user_id, pending_agenda=None)
            response["type"] = "agenda_created"
            response["message"] = f"Genoteerd! '{new_event['titel']}' staat in je agenda."
            response["agenda_event"] = new_event
            _save_log(req, response, "agenda_created")
            return response
        elif snap.detect_rejection(text) or wedervraag_service.is_skip(text):
            session_state.set_state(req.user_id, pending_agenda=None)
            response["type"] = "agenda_declined"
            response["message"] = fallback_service.pick(
                "agenda_declined", "Oké, ik laat het zo. Niks in je agenda gezet."
            )
            _save_log(req, response, "agenda_declined")
            return response
        # Geen ja/nee — laat staan, val door

    # 0c0. CONSENT-FLOW (v4_consent_001) — vóór W-vragen vraagt Spark eerst "wil je 6 vragen invullen?"
    pending_consent = state.get("pending_wv_consent")
    if pending_consent:
        if snap.detect_confirmation(text):
            # JA → start echte wedervraag-flow met max 6 vragen
            from pathlib import Path as _Path
            from modules.core.storage import load_json as _lj
            kb = _lj(_Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json", default={"knowledge_entries": []})
            entry = next((e for e in kb.get("knowledge_entries", []) if e.get("id") == pending_consent["entry_id"]), None)
            session_state.set_state(req.user_id, pending_wv_consent=None)
            if entry:
                wv = wedervraag_service.kick_off(entry, max_questions=6)
                if wv:
                    session_state.set_state(req.user_id, pending_wedervraag=wv,
                                            last_entry_id=entry["id"], last_begrip=entry["begrip"])
                    response["type"] = "wedervraag"
                    response["message"] = f"Top! Eerste vraag: {wv['question']}"
                    response["wedervraag"] = wv
                    _save_log(req, response, "wedervraag")
                    return response
            response["type"] = "wedervraag_done"
            response["message"] = "Niks meer om in te vullen."
            _save_log(req, response, "wedervraag_done")
            return response
        elif snap.detect_rejection(text) or wedervraag_service.is_skip(text):
            # NEE → niet doorvragen, lees verder als normaal bericht
            session_state.set_state(req.user_id, pending_wv_consent=None)
            response["type"] = "consent_declined"
            response["message"] = "Oké, ik laat het zo. Je kan de kaart later in de Kennisbank aanvullen."
            _save_log(req, response, "consent_declined")
            return response
        # Anders: user gaf gewoon een vrij antwoord → behandel als normaal bericht
        # Reset consent state en val door naar de rest van de flow
        session_state.set_state(req.user_id, pending_wv_consent=None)

    # 0c. WEDERVRAAG-FLOW (v4_001b) — als Spark in vorige beurt een 5W+H vraag stelde
    pending_wv = state.get("pending_wedervraag")
    if pending_wv and not snap.detect_rejection(text):
        # User wil stoppen?
        if wedervraag_service.is_skip(text):
            session_state.set_state(req.user_id, pending_wedervraag=None)
            response["type"] = "wedervraag_skip"
            response["message"] = fallback_service.pick(
                "wedervraag_skip",
                "Geen probleem, ik laat het zo staan. Je kan de kaart later in de Kennisbank invullen.",
            )
            _save_log(req, response, "wedervraag_skip")
            return response
        # Antwoord opslaan in ws5 van die snap
        ok = wedervraag_service.apply_answer(
            pending_wv["entry_id"], pending_wv["field"], text
        )
        if ok:
            # Volgende veld vragen, of afronden
            next_step = wedervraag_service.continue_flow(pending_wv)
            if next_step:
                session_state.set_state(req.user_id, pending_wedervraag=next_step)
                response["type"] = "wedervraag"
                response["message"] = f"Dank je! Genoteerd. {next_step['question']}"
                response["wedervraag"] = next_step
                _save_log(req, response, "wedervraag")
                return response
            else:
                session_state.set_state(req.user_id, pending_wedervraag=None)
                response["type"] = "wedervraag_done"
                response["message"] = fallback_service.pick(
                    "wedervraag_done", "Dank je! De kaart heb ik bijgewerkt."
                )
                _save_log(req, response, "wedervraag_done")
                return response

    # -- CONFIRMATION flow: user zei eerder "nee" en Spark vroeg "bedoel je een andere X?"
    if state.get("awaiting_homonym_confirm") and snap.detect_confirmation(text):
        begrip = state.get("last_begrip", "")
        original_id = state.get("last_entry_id")
        if begrip:
            new_entry = snap.create_homonym_variant(begrip, req.user_naam or "Gebruiker", original_id)
            # XP grant (v3_013)
            xp_result = xp_service.grant_xp(
                req.user_id,
                HOMONYM_XP_BONUS,
                reason=f"Homoniem-disambiguatie: '{begrip}'"
            ) if req.user_id else {"success": False}

            responses = snap.triggers.get("confirmation", {}).get("responses", [])
            tmpl = random.choice(responses) if responses else "Top! Nieuwe kaart '{begrip}' aangemaakt. +{xp} XP!"
            response["message"] = tmpl.format(begrip=begrip, xp=HOMONYM_XP_BONUS)
            response["type"] = "homonym_created"
            response["snap_suggestions"] = [begrip]
            response["homonym"] = {
                "new_entry_id": new_entry["id"],
                "original_id": original_id,
                "xp_granted": HOMONYM_XP_BONUS if xp_result.get("success") else 0,
            }
            session_state.clear_state(req.user_id)
            _save_log(req, response, "homonym_confirm")
            return response

    # -- REJECTION flow: user zegt "nee dat bedoel ik niet" op vorig antwoord
    if state.get("last_begrip") and snap.detect_rejection(text):
        begrip = state.get("last_begrip")
        # Markeer awaiting confirmation, laatste begrip en entry_id blijven staan
        session_state.set_state(
            req.user_id,
            awaiting_homonym_confirm=True,
            last_begrip=begrip,
            last_entry_id=state.get("last_entry_id"),
        )
        responses = snap.triggers.get("rejection", {}).get("responses", [])
        tmpl = random.choice(responses) if responses else "Bedoel je een ander '{begrip}'?"
        response["message"] = tmpl.format(begrip=begrip)
        response["type"] = "homonym_question"
        response["homonym"] = {"awaiting_confirm": True, "begrip": begrip}
        _save_log(req, response, "homonym_reject")
        return response

    # Als user NIET bevestigt na een rejection-vraag → wis de awaiting flag
    if state.get("awaiting_homonym_confirm") and not snap.detect_confirmation(text):
        session_state.clear_state(req.user_id)
        # Flow valt door naar normale verwerking

    # 1. Trigger checks
    trigger_type = None
    if snap.detect_greeting(text):
        resp = snap.get_trigger_response("greeting")
        response["type"] = "greeting"
        response["message"] = resp or f"Hallo {req.user_naam}! Hoe kan ik je helpen?"
        trigger_type = "greeting"
        _save_log(req, response, trigger_type)
        return response

    if snap.detect_thanks(text):
        resp = snap.get_trigger_response("thanks")
        response["type"] = "thanks"
        response["message"] = resp or "Graag gedaan!"
        trigger_type = "thanks"
        _save_log(req, response, trigger_type)
        return response

    # Admin kaart-sessie start (v4_008): "ik wil kaarten invullen"
    if card_session_service.detect_start_command(text):
        gradatie = _get_user_gradatie(req.user_id)
        if gradatie not in (1, 2):
            response["type"] = "card_session_denied"
            response["message"] = fallback_service.pick(
                "card_session_denied",
                "Sorry, de kaart-invul sessie is alleen voor admin (gradatie 1 of 2).",
            )
            _save_log(req, response, "card_session_denied")
            return response
        sess = card_session_service.start_session(max_items=50)
        if sess.get("done") or not sess.get("queue"):
            response["type"] = "card_session_empty"
            response["message"] = fallback_service.pick(
                "card_session_empty",
                "Er zijn op dit moment geen onbeantwoorde kaarten met lege velden. Top!",
            )
            _save_log(req, response, "card_session_empty")
            return response
        first_q = card_session_service.next_question(sess)
        session_state.set_state(req.user_id, pending_card_session=sess)
        progress = first_q.get("card_progress", (0, 0))
        response["type"] = "card_session_started"
        response["message"] = (
            f"Top! Ik heb **{sess['total']} kaart(en)** klaar staan om in te vullen. "
            f"We gaan ze 1 voor 1 doen, 6 vragen per kaart (W+H).\n\n"
            f"_(Kaart {progress[0]}/{progress[1]}: **{first_q['begrip']}**)_\n\n"
            f"{first_q['question']}\n\n"
            f"_(antwoord, of typ 'skip' om dit veld over te slaan, 'stop' om te pauzeren)_"
        )
        response["card_session"] = {
            "card_id": first_q["card_id"],
            "begrip": first_q["begrip"],
            "category": first_q.get("category"),
            "field": first_q["field"],
            "progress": progress,
        }
        _save_log(req, response, "card_session_started")
        return response

    # Admin scan-command (v4_005): "scan alle knowledge kaarten op onderwerpen"
    if scan_service.detect_scan_command(text):
        # Admin-gated: alleen gradatie 1 of 2
        gradatie = _get_user_gradatie(req.user_id)
        if gradatie not in (1, 2):
            response["type"] = "scan_denied"
            response["message"] = fallback_service.pick(
                "scan_denied", "Sorry, het scan-commando is alleen voor admin (gradatie 1 of 2)."
            )
            _save_log(req, response, "scan_denied")
            return response
        result = scan_service.scan_for_new_subjects(user_naam=req.user_naam or "Spark", max_create=100)
        msg_parts = [
            f"Scan klaar! Ik heb mijn eigen {result['scanned_cards']} kaarten doorgenomen.",
            f"Kandidaat-woorden gevonden: **{result['candidates_found']}**.",
            f"Nieuwe draft-snaps aangemaakt: **{result['new_snaps_created']}** (limiet was {result['max_create_cap']}).",
        ]
        if result["sample_words"]:
            msg_parts.append(f"Voorbeelden: {', '.join(result['sample_words'])}.")
        if result["capped"]:
            msg_parts.append("Er waren meer kandidaten dan de limiet — draai het commando nogmaals om de rest op te pakken.")
        msg_parts.append("Bekijk ze in Kennisbank → Onbeantwoord (tag `scan-discovered`).")
        response["type"] = "scan_result"
        response["message"] = "\n\n".join(msg_parts)
        response["scan_result"] = result
        _save_log(req, response, "scan_result")
        return response

    # Self-state moet VOOR how_are_you komen — specifieker (jij/spark) wint
    if snap.detect_self_state(text):
        state = self_state_service.compute_health_score()
        msg = self_state_service.build_response(state, req.user_naam)
        response["type"] = "self_state"
        response["message"] = msg
        response["self_state"] = state
        trigger_type = "self_state"
        _save_log(req, response, trigger_type)
        return response

    if snap.detect_how_are_you(text):
        resp = snap.get_trigger_response("how_are_you")
        response["type"] = "how_are_you"
        response["message"] = resp or "Goed! Ik ben bezig om te leren en groeien."
        trigger_type = "how_are_you"
        _save_log(req, response, trigger_type)
        return response

    if snap.detect_goodbye(text):
        resp = snap.get_trigger_response("goodbye")
        response["type"] = "goodbye"
        response["message"] = resp or f"Tot ziens {req.user_naam}!"
        trigger_type = "goodbye"
        _save_log(req, response, trigger_type)
        return response

    # 1.4 DIEPERE UITLEG FLOW (v4_011) — user vraagt om laag 2/3/4 van laatste begrip
    if req.user_id and state.get("last_entry_id"):
        deeper = snap.detect_deeper_request(text)
        if deeper is not None:
            cur_depth = int(state.get("current_depth") or 1)
            target = deeper if deeper > 0 else min(cur_depth + 1, 4)
            target = max(1, min(target, 4))
            entry = snap.get_entry_by_id(state["last_entry_id"])
            if entry:
                actual_depth, layer_text, fallback = snap.get_layer(entry, target)
                begrip = entry.get("begrip", "")
                if layer_text:
                    depth_labels = {1: "kort", 2: "uitgebreider", 3: "diepgaand", 4: "essentieel"}
                    label = depth_labels.get(actual_depth, f"laag {actual_depth}")
                    prefix = ""
                    if fallback and target > actual_depth:
                        prefix = f"_(Laag {target} is nog leeg, dit is laag {actual_depth} — {label})_\n\n"
                    response["type"] = "knowledge_deeper"
                    response["message"] = f"{prefix}**{begrip}** _(laag {actual_depth} — {label})_: {layer_text}"
                    response["knowledge_matches"] = [snap._format_result(entry, "deeper")]
                    session_state.set_state(
                        req.user_id,
                        last_begrip=begrip,
                        last_entry_id=entry.get("id"),
                        current_depth=actual_depth,
                    )
                    _save_log(req, response, "knowledge_deeper")
                    return response
                else:
                    response["type"] = "knowledge_deeper_empty"
                    response["message"] = (
                        f"Ik heb voor **{begrip}** nog geen diepere uitleg in laag {target}. "
                        "Wil je het aanvullen in de Kennisbank of via de Bijdragen-portal?"
                    )
                    _save_log(req, response, "knowledge_deeper_empty")
                    return response

    # 1.5 AGENDA INTENT DETECTIE (v3_303) — vóór knowledge lookup
    # Als zin tijd + (wat/waar) bevat → voorstel om te noteren
    if req.user_id:
        # v4_025: user ophalen voor tijdzone-correcte parsing
        try:
            from modules.auth.service import AuthService as _Auth
            _user = _Auth.get_user_by_id(req.user_id)
        except Exception:
            _user = None
        intent = agenda_intent_service.detect_agenda_intent(text, user=_user)
        if intent.get("has_intent"):
            has_conflict = agenda_intent_service.has_agenda_conflict(req.user_id, intent["datetime_iso"])
            pending = {
                "datetime_iso": intent["datetime_iso"],
                "raw_time": intent.get("raw_time"),
                "wat": intent.get("wat"),
                "waar": intent.get("waar"),
                "raw_text": text,
                "has_conflict": has_conflict,
            }
            session_state.set_state(req.user_id, pending_agenda=pending)
            response["type"] = "agenda_proposal"
            response["message"] = agenda_intent_service.build_proposal_message(intent, has_conflict)
            response["agenda_intent"] = pending
            _save_log(req, response, "agenda_proposal")
            return response

    # 1.6 COMPOSITIONAL PRE-CHECK (v4_006): woord met 2 bekende delen krijgt voorrang
    # boven losse partial-match (suikerspin = suiker+spin, niet 'lijkt op suiker')
    def _lookup_exact(w):
        idx = snap._get_index()
        hits = idx.get(w)
        return hits[0] if hits else None
    meaningful_words = snap._extract_meaningful_words(text)
    compositional_hit = None
    for w in meaningful_words:
        if _lookup_exact(w):
            continue  # exact bekend, geen behoefte aan split
        decomp = compositional_service.find_best_decomposition(w, _lookup_exact)
        if decomp:
            compositional_hit = {"word": w, "decomp": decomp}
            break
    if compositional_hit:
        word = compositional_hit["word"]
        decomp = compositional_hit["decomp"]
        extra_tags = decomp["analysis"]["suggested_tags"]
        parts = [decomp["candidate"]["left"], decomp["candidate"]["right"]]
        new_entry = snap.create_word_snap(
            word, text, req.user_naam,
            extra_tags=extra_tags,
            decomposed_from=parts,
        )
        response["type"] = "compositional"
        response["message"] = decomp["message"]
        response["compositional"] = {
            "word": word,
            "left": parts[0],
            "right": parts[1],
            "analysis": decomp["analysis"],
            "new_snap_id": new_entry["id"] if new_entry else None,
        }
        if new_entry and req.user_id:
            session_state.set_state(req.user_id, pending_wedervraag={
                "entry_id": new_entry["id"],
                "field": "wat",
                "question": decomp["message"],
                "asked_count": 1,
                "max_questions": 1,
            })
        _save_log(req, response, "compositional")
        return response

    # 1.7 SPARK SELF-QUESTION (v4_011, Bijbel-integratie): user vraagt
    # naar Spark's eigen voorkeur/missie/doel/waarden/normen → antwoord uit Bijbel.
    self_intent = bijbel_lookup_service.detect_self_question(text)
    if self_intent:
        reply = bijbel_lookup_service.compose_reply(self_intent)
        if reply:
            response["type"] = "bijbel_reply"
            response["message"] = reply
            response["bijbel_intent"] = self_intent
            _save_log(req, response, "bijbel_reply")
            return response

    # 2. Knowledge lookup - zoek alle begrippen in de zin
    # 2a. ZIN-SNAP HIGH-CONFIDENCE MATCH (v4_011, Optie B): als 3+ woorden
    # overlappen met een opgeslagen contextzin die gevulde lagen heeft, krijgt
    # die zin voorrang op losse woord-lookup (anders eet 'gisteren' de hele zin op).
    sent_match_strong = snap.lookup_sentence_match(text, min_overlap=3, min_ratio=0.5)
    if sent_match_strong:
        layer_text = ""
        used_depth = 1
        for d in (1, 2, 3, 4):
            t = sent_match_strong.get(f"laag{d}", "")
            if t:
                layer_text = t
                used_depth = d
                break
        prefix = ""
        if emotion and emotion.get("empathic_response"):
            prefix = emotion["empathic_response"] + "\n\n"
        response["type"] = "sentence_reply"
        response["message"] = (
            f"{prefix}_(Dit doet me denken aan: \"{sent_match_strong['begrip']}\")_\n\n{layer_text}"
        )
        response["knowledge_matches"] = [sent_match_strong]
        if req.user_id:
            session_state.set_state(
                req.user_id,
                last_begrip=sent_match_strong.get("begrip", ""),
                last_entry_id=sent_match_strong.get("id"),
                current_depth=used_depth,
            )
        _save_log(req, response, "sentence_reply")
        return response

    matches = snap.multi_lookup(text)

    if matches:
        response["knowledge_matches"] = matches
        best = matches[0]
        # Sla laatste begrip op in state — voor rejection-flow (v3_012) + reset depth
        if req.user_id:
            session_state.set_state(
                req.user_id,
                last_begrip=best.get("begrip", ""),
                last_entry_id=best.get("id"),
                awaiting_homonym_confirm=False,
                current_depth=1,
            )
        laag1 = best.get("laag1", "")
        # Emotie prefix toevoegen als gedetecteerd
        prefix = ""
        if emotion and emotion.get("empathic_response"):
            prefix = emotion["empathic_response"] + "\n\n"
        if laag1:
            if len(matches) == 1:
                response["message"] = f"{prefix}**{best['begrip']}**: {laag1}"
            else:
                parts = [f"**{m['begrip']}**: {m['laag1']}" for m in matches if m.get('laag1')]
                response["message"] = prefix + ("\n\n".join(parts) if parts else f"Ik ken '{best['begrip']}' maar heb nog geen uitleg.")
            # Diepere-laag-hint als laag2/3/4 gevuld is
            if any(best.get(k) for k in ("laag2", "laag3", "laag4")):
                response["message"] += "\n\n_(Wil je een diepere uitleg? Typ 'vertel meer' of 'leg dieper uit'.)_"
        else:
            response["message"] = f"{prefix}Ik ken '{best['begrip']}' maar heb nog geen uitleg. Wil je het invullen in de Kennisbank?"
        response["type"] = "knowledge"

        # Check of er naast de matches ook onbekende woorden in de zin staan
        matched_words = set(m.get("matched_word", "").lower() for m in matches)
        matched_begrippen = set(m.get("begrip", "").lower() for m in matches)
        meaningful = snap._extract_meaningful_words(text)
        index = snap._get_index()
        still_unknown = [w for w in meaningful if w not in index and w not in matched_words and not any(w.startswith(b) or b.startswith(w) for b in matched_begrippen)]
        if still_unknown:
            created = []
            last_entry = None
            for word in still_unknown[:5]:
                result = snap.create_word_snap(word, text, req.user_naam)
                if result:
                    created.append(result["begrip"])
                    last_entry = result
            if created:
                response["snap_suggestions"] = created
                response["message"] += f"\n\nNieuw geleerd: **{', '.join(created)}** (opgeslagen als kaarten)"
                # Auto-zin-snap (v3_028): bewaar de hele zin als context-anker
                sentence_result = snap.create_sentence_snap(text, text, req.user_naam)
                if sentence_result:
                    response.setdefault("snap_sentence", sentence_result["begrip"])
                # Wedervraag (v4_001b): vraag 5W+H verrijking op nieuwste snap
                if last_entry and req.user_id:
                    wv = wedervraag_service.kick_off(last_entry)
                    if wv:
                        session_state.set_state(req.user_id, pending_wedervraag=wv)
                        response["message"] += f"\n\n{wv['question']}"
                        response["wedervraag"] = wv
    else:
        # 2b. ZIN-SNAP FUZZY MATCH (v4_011, Optie B): probeer een eerder
        # opgeslagen contextzin te vinden met overlap in betekenisvolle woorden.
        sent_match = snap.lookup_sentence_match(text)
        if sent_match:
            # Pak hoogste gevulde laag (laag1 prioriteit → val terug op hogere)
            layer_text = ""
            used_depth = 1
            for d in (1, 2, 3, 4):
                t = sent_match.get(f"laag{d}", "")
                if t:
                    layer_text = t
                    used_depth = d
                    break
            response["type"] = "sentence_reply"
            response["message"] = (
                f"_(Lijkt op een zin die ik eerder leerde: \"{sent_match['begrip']}\")_\n\n{layer_text}"
            )
            response["knowledge_matches"] = [sent_match]
            if req.user_id:
                session_state.set_state(
                    req.user_id,
                    last_begrip=sent_match.get("begrip", ""),
                    last_entry_id=sent_match.get("id"),
                    current_depth=used_depth,
                )
            _save_log(req, response, "sentence_reply")
            return response

        # 3. Geen match - detecteer onbekende woorden en maak automatisch snaps
        meaningful = snap._extract_meaningful_words(text)
        index = snap._get_index()
        unknown = [w for w in meaningful if w not in index]

        if unknown:
            # Compositional reasoning (v4_006): probeer onbekend woord op te splitsen
            # in bekende delen vóór het opslaan als 'leeg' snap.
            def _lookup_known(w):
                idx = snap._get_index()
                hits = idx.get(w)
                return hits[0] if hits else None
            decomp_results = []

            created_snaps = []
            last_entry = None
            for word in unknown[:5]:
                decomp = compositional_service.find_best_decomposition(word, _lookup_known)
                # v4_stem_001 — fallback: stem-match als full decomp niet lukt
                stem_hit = None
                if not decomp:
                    stem_hit = compositional_service.find_known_stem(word, _lookup_known)
                if decomp:
                    extra_tags = decomp["analysis"]["suggested_tags"]
                    parts = [decomp["candidate"]["left"], decomp["candidate"]["right"]]
                    result = snap.create_word_snap(
                        word, text, req.user_naam,
                        extra_tags=extra_tags,
                        decomposed_from=parts,
                    )
                    if result:
                        created_snaps.append(result["begrip"])
                        last_entry = result
                        decomp_results.append({"word": word, "decomp": decomp})
                elif stem_hit:
                    # Stem-match: erfde topic-tag van stem
                    stem_topic = (stem_hit["stem_entry"].get("topic") or "").strip()
                    extra_tags = [stem_topic] if stem_topic else []
                    result = snap.create_word_snap(
                        word, text, req.user_naam,
                        extra_tags=extra_tags,
                        decomposed_from=[stem_hit["stem"]],
                    )
                    if result:
                        created_snaps.append(result["begrip"])
                        last_entry = result
                        decomp_results.append({"word": word, "decomp": {"message": stem_hit["message"], "candidate": {"left": stem_hit["stem"], "right": ""}, "analysis": {"stem_only": True}}})
                else:
                    result = snap.create_word_snap(word, text, req.user_naam)
                    if result:
                        created_snaps.append(result["begrip"])
                        last_entry = result

            response["unknown_words"] = unknown
            response["snap_suggestions"] = created_snaps
            if created_snaps:
                response["message"] = f"Ik ken deze woorden nog niet: **{', '.join(created_snaps)}**. Ik heb ze als nieuwe kaarten opgeslagen zodat ik ze kan leren!"
                # Auto-zin-snap (v3_028): bewaar de hele zin als context-anker
                sentence_result = snap.create_sentence_snap(text, text, req.user_naam)
                if sentence_result:
                    response["snap_sentence"] = sentence_result["begrip"]
                # Compositional vraag (v4_006) wint van standaard wedervraag
                if decomp_results and req.user_id:
                    first_decomp = decomp_results[0]
                    response["message"] += f"\n\n{first_decomp['decomp']['message']}"
                    response["compositional"] = {
                        "word": first_decomp["word"],
                        "left": first_decomp["decomp"]["candidate"]["left"],
                        "right": first_decomp["decomp"]["candidate"]["right"],
                        "analysis": first_decomp["decomp"]["analysis"],
                    }
                    # Pending wedervraag op 'wat' veld zodat user-antwoord landt
                    target_entry = next((e for e in [last_entry] if e and e["begrip"] == first_decomp["word"]), last_entry)
                    if target_entry:
                        session_state.set_state(req.user_id, pending_wedervraag={
                            "entry_id": target_entry["id"],
                            "field": "wat",
                            "question": first_decomp["decomp"]["message"],
                            "asked_count": 1,
                            "max_questions": 1,
                        }, last_entry_id=target_entry["id"], last_begrip=target_entry["begrip"])
                # Wedervraag (v4_001b + v4_consent_001): vraag eerst toestemming, dan 6x W+H
                elif last_entry and req.user_id:
                    # Check of er nog lege W-velden zijn
                    has_empty = wedervraag_service.pick_next_field(last_entry) is not None
                    if has_empty:
                        session_state.set_state(req.user_id,
                                                pending_wv_consent={"entry_id": last_entry["id"], "begrip": last_entry.get("begrip", "")},
                                                last_entry_id=last_entry["id"],
                                                last_begrip=last_entry["begrip"])
                        response["message"] += f"\n\nWil je 6 vragen beantwoorden om '{last_entry.get('begrip','')}' rijker te maken? (wie/wat/wanneer/waar/waarom/hoe)"
                        response["consent_pending"] = True
                    else:
                        session_state.set_state(req.user_id, last_entry_id=last_entry["id"], last_begrip=last_entry["begrip"])
            else:
                response["message"] = fallback_service.pick(
                    "unknown_words_partial",
                    f"Hmm, ik ken deze woorden nog niet helemaal: {', '.join(unknown)}.",
                    words=", ".join(unknown),
                )
            response["type"] = "unknown"
        else:
            # Gewoon antwoord als er niks te matchen valt
            if snap.is_question(text):
                response["message"] = fallback_service.pick(
                    "topic_not_found",
                    "Goede vraag! Daar heb ik helaas nog geen antwoord op. Wil je het toevoegen aan de Kennisbank?",
                )
                response["type"] = "question"
            else:
                response["message"] = fallback_service.pick(
                    "general_fallback",
                    "Ik begrijp je, maar kan daar nog niet specifiek op reageren. Mijn kennis groeit elke dag!",
                )
                response["type"] = "general"

    # Append spontane W-hint (v4_007) als er stilletjes iets is bijgewerkt
    if spontaneous_hint and response.get("message"):
        response["message"] = response["message"] + spontaneous_hint
        response["spontaneous_w_filled"] = True

    _save_log(req, response, None)
    return response


def _save_log(req: "ChatMessage", response: dict, trigger_type):
    """Save gesprek naar user log."""
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
    # Shadow Observer (v4_015) — niet-blokkerend, mag chat nooit breken
    try:
        shadow_observer.record(req.user_id, req.message, response, trigger_type)
    except Exception:
        pass


def _get_user_gradatie(user_id):
    """Haal gradatie van user op. Return None als niet gevonden."""
    if not user_id:
        return None
    from pathlib import Path as _P
    from modules.core.storage import load_json as _lj
    data = _lj(_P(__file__).parent.parent.parent / "data" / "system" / "users.json", default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id:
            return u.get("gradatie")
    return None


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
