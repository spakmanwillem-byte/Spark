"""v6_response_composer_001 — Spark's gespreks-synthesizer (blueprint-driven).

Configuratie zit in:
  /app/backend/modules/chat/blueprints/response_composer.json

LLM = synthesizer/mond. Spark's KB + bijbel = brein. Bron blijft Spark.

Pipeline:
  1. Snuffel relevante V2-kaarten via snap_service
  2. Laad bijbel (kernwaarden, normen)
  3. Recente conversation-turns (multi-turn memory)
  4. Detect emotion (via emotion_service als beschikbaar)
  5. Bouw system_prompt uit blueprint + bijbel
  6. Bouw user_prompt met context-pakket
  7. Roep model aan via Emergent LLM Key
  8. Return antwoord
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage

from modules.core.storage import load_json
from modules.core.blueprint import load_blueprint_cached



# v6_response_composer_refactor_001 — Alle helpers (loaders, formatters, prompt-builders)
# zijn verplaatst naar composer_helpers.py. Dit bestand bevat alleen de orkestrator.
from modules.chat.composer_helpers import (
    _bp,
    _load_relevant_kb,
    _load_bijbel_essence,
    _load_self_awareness,
    _format_now_for_prompt,
    _load_snap_cluster,
    _format_snap_cluster,
    _load_ops_context,
    _auto_snap_from_diep,
    _format_self_awareness_for_prompt,
    _format_kb_cards,
    _format_turns,
    _load_recent_turns,
    _save_turn_pair,
    _build_system_prompt,
)




async def compose_response(
    user_text: str,
    user_id: str = "user-001",
    session_id: Optional[str] = None,
    emotion: Optional[str] = None,
    active_tab: Optional[str] = None,
    admin_mode: bool = False,
) -> Dict[str, Any]:
    """Hoofdfunctie. Return {success, message, used_cards, used_model}."""
    # v8_trader_intents_001 — Trader-commando's ('start bot', 'wat verdiend', etc.)
    # Vóór action_intents zodat trader-triggers voorrang krijgen op algemene toggles.
    try:
        from modules.trade.trader_intents import try_detect as _trader_detect
        trader_hit = await _trader_detect(user_text, user_id=user_id)
        if trader_hit:
            if session_id:
                try:
                    from modules.chat import chat_log_service
                    chat_log_service.save_message(
                        user_id=user_id,
                        user_naam=user_id,
                        user_message=user_text,
                        spark_response=trader_hit.get("message", ""),
                        channel="spark-trader-intent",
                        session_id=session_id,
                        analysis={"intent": trader_hit.get("intent"), "action": trader_hit.get("action")},
                    )
                except Exception:
                    pass
                _save_turn_pair(session_id, user_id, user_text, trader_hit.get("message", ""), "trader_intents")
            return {
                "success": trader_hit.get("success", True),
                "message": trader_hit.get("message", ""),
                "action": trader_hit.get("action"),
                "intent": trader_hit.get("intent"),
                "data": trader_hit.get("data"),
                "used_cards": [],
                "used_model": "trader_intents",
                "blueprint_version": "1.0",
                "fast_path": True,
            }
    except Exception:
        pass  # bij fout: door naar action_intents / LLM

    # v11_spark_index_001 — Count-intent ('hoeveel bestanden/mappen/modules')
    # Fast-path uit spark_index (geen live scan, geen LLM guess).
    try:
        from modules.chat.count_intent_service import detect_count_intent, answer_count
        target = detect_count_intent(user_text)
        if target:
            ans = answer_count(target)
            if ans:
                if session_id:
                    _save_turn_pair(session_id, user_id, user_text, ans["message"], "spark_index")
                return {
                    "success": True,
                    "message": ans["message"],
                    "intent": ans["intent"],
                    "data": {"target": ans["target"], "totals": ans["totals"]},
                    "used_cards": [],
                    "used_model": "spark_index_fastpath",
                    "blueprint_version": "1.0",
                    "fast_path": True,
                }
    except Exception as _cx:
        print(f"[count-intent] error: {_cx}")

    # v9_self_profile_001 — Detecteer "waar woon ik / mijn adres / etc." → direct uit profile.json
    # Skip verificatie: ingelogde user MAG eigen data zien.
    try:
        from modules.chat.self_profile_intent import try_detect as _self_profile_detect
        sp_hit = _self_profile_detect(user_text, user_id=user_id)
        if sp_hit:
            if session_id:
                _save_turn_pair(session_id, user_id, user_text, sp_hit.get("message", ""), "self_profile")
            return {
                "success": True,
                "message": sp_hit.get("message", ""),
                "action": sp_hit.get("action"),
                "intent": sp_hit.get("intent"),
                "data": sp_hit.get("data"),
                "used_cards": [],
                "used_model": "self_profile_intent",
                "blueprint_version": "1.0",
                "fast_path": True,
            }
    except Exception:
        pass

    # v6_deep_side_effects_001 — Detecteer pure action-commands (TTS/STT/ambient toggle).
    # Bij match: skip de LLM (geen tokens, instant), return action + standaard-bevestiging.
    # Dit hergebruikt de bestaande action_intents_service zodat Diep dezelfde commands
    # herkent als normale chat.
    try:
        from modules.chat.action_intents_service import try_detect
        action_hit = try_detect(user_text)
        if action_hit:
            # Log ook in deze short-circuit pad
            if session_id:
                try:
                    from modules.chat import chat_log_service
                    chat_log_service.save_message(
                        user_id=user_id,
                        user_naam=user_id,
                        user_message=user_text,
                        spark_response=action_hit.get("message", ""),
                        channel="spark-deep-action",
                        session_id=session_id,
                        analysis={"action": action_hit.get("action"), "type": action_hit.get("type")},
                    )
                except Exception:
                    pass
                # v6_deep_memory_001: ook turns_dir bijhouden zodat geheugen niet kapot gaat
                _save_turn_pair(session_id, user_id, user_text, action_hit.get("message", ""), "action_intents_service")
            return {
                "success": True,
                "message": action_hit.get("message") or "",
                "action": action_hit.get("action"),
                "url": action_hit.get("url"),
                "ambient_label": action_hit.get("label"),
                "loop_id": action_hit.get("loop_id"),
                "type": action_hit.get("type"),
                "used_cards": [],
                "used_model": "action_intents_service",
                "blueprint_version": "1.0",
                "fast_path": True,
            }
    except Exception:
        pass  # bij fout: ga gewoon door naar LLM-pad

    # v14_compose_extraction_001 (Willem 19-10, Maaike-bug) — diep-modus sloeg relaties/personalia
    # NIET op ("Willem Spakman is mijn broer" → "ik noteer…" maar niets vastgelegd). Zelfde passieve
    # observers als /api/chat/message. Resultaat gaat als `new_relations`/`personalia_saved` mee
    # zodat de LLM alleen "ik noteer" zegt als er écht iets is opgeslagen.
    _new_relations, _personalia_saved = [], []
    if user_id and not user_text.startswith("[system:"):
        try:
            from modules.chat import relation_extraction_service as _rel
            _new_relations = _rel.detect_and_save(user_id, user_text) or []
        except Exception as ex:
            print(f"[compose relation-extract] failed: {ex}")
        try:
            from modules.chat import personalia_extraction_service as _pe
            _personalia_saved = _pe.detect_and_save(user_id, user_text) or []
        except Exception as ex:
            print(f"[compose personalia-extract] failed: {ex}")

    # v6_snuffel_bestand_001 — Spark doorzoekt eigen JSON-data op verzoek
    try:
        from modules.chat.spark_snuffel import detect_snuffel_intent, execute_snuffel, format_snuffel_result_for_chat
        snuffel_query = detect_snuffel_intent(user_text)
        if snuffel_query:
            result = execute_snuffel(snuffel_query, viewer_id=user_id)
            spark_msg = format_snuffel_result_for_chat(result)
            if session_id:
                try:
                    from modules.chat import chat_log_service
                    chat_log_service.save_message(
                        user_id=user_id,
                        user_naam=user_id,
                        user_message=user_text,
                        spark_response=spark_msg,
                        channel="spark-snuffel",
                        session_id=session_id,
                        analysis={"action": "snuffel_bestand", "query": snuffel_query, "total_hits": result.get("total_hits", 0)},
                    )
                except Exception:
                    pass
                _save_turn_pair(session_id, user_id, user_text, spark_msg, "spark_snuffel")
            return {
                "success": True,
                "message": spark_msg,
                "action": "snuffel_bestand",
                "type": "snuffel_result",
                "snuffel_query": snuffel_query,
                "snuffel_total": result.get("total_hits", 0),
                "snuffel_data": result.get("results", {}),
                "used_cards": [],
                "used_model": "spark_snuffel",
                "blueprint_version": "1.0",
                "fast_path": True,
            }
    except Exception:
        pass

    # v6_deep_help_001 — Help-intent ('help', 'wat kan je', etc.) opent de HelpBark popup
    # via een UI-event. Diep heeft deze short-circuit nodig anders blijft de LLM lekker
    # filosofisch antwoorden i.p.v. de popup te openen.
    try:
        from modules.chat import task_agent_bridge as _tab
        _cmd_out = await _tab.try_execute(user_text, user_id, admin_mode=admin_mode)
        if _cmd_out:
            if session_id:
                _save_turn_pair(session_id, user_id, user_text, _cmd_out.get("message", ""), "task_agent_bridge")
            return {"success": True, **_cmd_out, "used_cards": [], "used_model": "task_agent_bridge",
                    "blueprint_version": "1.0", "fast_path": True}
    except Exception as _cex:
        print(f"[compose task-agent-bridge] failed: {_cex}")
    try:
        from modules.chat.smart_intents_service import route_help
        _help_out = route_help(user_text, user_id, is_admin=admin_mode)
        if _help_out:
            _help_msg = _help_out.get("message", "")
            if session_id:
                try:
                    from modules.chat import chat_log_service
                    chat_log_service.save_message(
                        user_id=user_id,
                        user_naam=user_id,
                        user_message=user_text,
                        spark_response=_help_msg,
                        channel="spark-deep-help",
                        session_id=session_id,
                        analysis={"action": _help_out.get("action"), "type": _help_out.get("type")},
                    )
                except Exception:
                    pass
                _save_turn_pair(session_id, user_id, user_text, _help_msg, "smart_intents_service")
            return {
                "success": True,
                **_help_out,
                "used_cards": [],
                "used_model": "smart_intents_service",
                "blueprint_version": "1.0",
                "fast_path": True,
            }
    except Exception:
        pass

    # v6_deep_rps_001 — RPS (Steen-Papier-Schaar) opent het spel-bark.
    # Zelfde lijst triggers als /api/chat/message zodat 'sps', 'rps', 'speel sps' etc.
    # in Diep ook het spel openen i.p.v. dat Claude erover gaat filosoferen.
    try:
        _txt_rps = (user_text or "").lower().strip()
        rps_open_triggers = (
            "speel steen papier schaar", "steen papier schaar",
            "rock paper scissors", "speel sps", "open spel sps",
            "spelletje steen papier schaar",
            "speel steen", "speel papier", "speel schaar",
            "spelletje sps", "speel een spelletje", "speel spelletje",
            "spel sps", "spel rps", "speel rps",
            "open rps", "open sps", "rps game", "sps game",
            "begin sps", "begin rps", "start sps", "start rps",
            "start spel sps", "start spel rps", "begin spel sps", "begin spel rps",
        )
        rps_exact = ("sps", "rps")
        if any(t == _txt_rps or t in _txt_rps for t in rps_open_triggers) or _txt_rps in rps_exact:
            if session_id:
                try:
                    from modules.chat import chat_log_service
                    chat_log_service.save_message(
                        user_id=user_id,
                        user_naam=user_id,
                        user_message=user_text,
                        spark_response="🎮 Steen — Papier — Schaar! Kies je zet.",
                        channel="spark-deep-rps",
                        session_id=session_id,
                        analysis={"action": "open_game_rps"},
                    )
                except Exception:
                    pass
                _save_turn_pair(session_id, user_id, user_text, "🎮 Steen — Papier — Schaar! Kies je zet.", "rps_router")
            return {
                "success": True,
                "message": "🎮 Steen — Papier — Schaar! Kies je zet.",
                "action": "open_game_rps",
                "type": "open_game",
                "rps_opponent": "spark",
                "used_cards": [],
                "used_model": "rps_router",
                "blueprint_version": "1.0",
                "fast_path": True,
            }
    except Exception:
        pass

    # v6_semantic_intent_matcher_001 — laatste fast-path vóór LLM-call.
    # Voor synoniemen die we NIET expliciet kennen ('doe een potje sps', 'zet je stem aan')
    # — Spark herkent het toch via token_set_ratio fuzzy matching.
    try:
        from modules.chat.semantic_matcher import semantic_match
        sem_hit = semantic_match(user_text)
        if sem_hit:
            if session_id:
                try:
                    from modules.chat import chat_log_service
                    channel = sem_hit.get("log_channel", "spark-deep-semantic")
                    chat_log_service.save_message(
                        user_id=user_id,
                        user_naam=user_id,
                        user_message=user_text,
                        spark_response=sem_hit.get("message", ""),
                        channel=channel,
                        session_id=session_id,
                        analysis={
                            "action": sem_hit.get("action"),
                            "semantic_score": sem_hit.get("semantic_score"),
                            "matched_canonical": sem_hit.get("semantic_matched_canonical"),
                        },
                    )
                except Exception:
                    pass
                _save_turn_pair(session_id, user_id, user_text, sem_hit.get("message", ""), "semantic_matcher")
            return sem_hit
    except Exception:
        pass

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        return {"success": False, "error": "EMERGENT_LLM_KEY ontbreekt in env"}

    # v6_spark_handen_001 — schrijfacties fast-path (notitie/taak) vóór LLM-call
    # Bespaart credits + directe feedback aan user.
    try:
        from modules.chat.spark_handen import detect_and_execute
        hand_result = detect_and_execute(user_text, user_id)
        if hand_result and hand_result.get("hand_executed"):
            return {
                "success": True,
                "message": hand_result["message"],
                "action": hand_result.get("action"),
                "fast_path": "spark_handen",
                "used_model": "spark_handen_local",
                "session_id": session_id,
            }
    except Exception as ex:
        print(f"[spark_handen] detect/execute failed: {ex}")

    bp = _bp()
    model_provider = bp["model"]["provider"]
    model_name = bp["model"]["name"]

    cards = _load_relevant_kb(user_text, current_user_id=user_id)
    bijbel = _load_bijbel_essence()
    turns = _load_recent_turns(session_id) if session_id else []

    # v13_privacy_guard_001 (sessie 54) — Attente Spark privacy-matrix.
    # Filter KB-kaarten met verboden tags (financieel/gezondheid/familie/privé)
    # vóór ze in de LLM-context landen. Voorkomt dat lage-gradatie users
    # (bv gradatie 5-7 kennissen/onbekenden) admin's familie/financiën zien.
    _requester_grad = None
    try:
        from modules.chat.spark_user_view import _get_user_meta as _gum
        _requester_meta = _gum(user_id) if user_id else {}
        _requester_grad = _requester_meta.get("gradatie")
    except Exception:
        _requester_grad = None

    try:
        from modules.chat import privacy_guard
        _cards_before = len(cards)
        cards = privacy_guard.filter_kb_cards(cards, _requester_grad)
        if _cards_before != len(cards):
            print(f"[privacy_guard] grad={_requester_grad}: filtered {_cards_before - len(cards)}/{_cards_before} KB cards")
    except Exception as _pgex:
        print(f"[privacy_guard] KB filter error: {_pgex}")

    # v13_semantic_lookup_gap_offer_001 (sessie 53) — Zelflerende loop:
    # Als semantic_lookup een relevante kaart met ws5-gap teruggaf, plaats
    # kb_fill_pending offer in session_state. De bestaande state-machine in
    # chat/routes.py (fasen offer → awaiting_answer → awaiting_confirm) pikt
    # dan Willem's volgende bericht op en PATCHt de kaart automatisch.
    # Voorwaarden:
    #   • user_id aanwezig
    #   • geen actieve kb_fill_pending (respecteer lopende flow)
    #   • ten minste 1 kaart met _ws5_gap=True EN score >= 10 (relevant genoeg)
    if user_id and cards:
        try:
            from modules.chat import session_state as _ss
            from modules.chat import wedervraag_service as _wv
            cur_state = _ss.get_state(user_id) or {}
            if not cur_state.get("kb_fill_pending"):
                gap_cards = [c for c in cards
                             if c.get("_ws5_gap") and int(c.get("_match_score", 0)) >= 10]
                if gap_cards:
                    # Pak hoogst-scorende gap-kaart
                    top_gap = sorted(gap_cards, key=lambda c: -int(c.get("_match_score", 0)))[0]
                    offer = _wv.build_offer_from_card(top_gap)
                    if offer:
                        _ss.set_state(user_id, kb_fill_pending={
                            "phase": "awaiting_answer",   # skip offer-fase — de gap is al genoemd in prompt
                            "entry_id": offer["entry_id"],
                            "begrip": offer["begrip"],
                            "field": offer["field"],
                            "question": offer["question"],
                            "source": "semantic_lookup_gap",
                        })
        except Exception as _gex:
            # Loop mag composer nooit blokkeren
            pass

    # v6_topic_tracker_001 — detecteer dominant onderwerp over recente turns
    tt_cfg = bp.get("topic_tracker", {}) or {}
    topic: Optional[str] = None
    if session_id and tt_cfg.get("enabled", True):
        try:
            from modules.chat.topic_tracker import detect_topic
            topic = detect_topic(
                session_id,
                max_turns=int(tt_cfg.get("max_turns_lookback", 6)),
            )
        except Exception:
            topic = None

    # v6_diep_memory_layers_001 — cross-session topics + norm-matcher
    recent_topics: List[Dict] = []
    relevant_norms: List[Dict] = []
    try:
        from modules.chat import diep_memory
        recent_topics = diep_memory.load_recent_topics(user_id, max_n=5)
        relevant_norms = diep_memory.find_relevant_norms(user_text, max_n=3)
        # Schrijf huidige topic naar recent_topics (voor volgende sessie)
        if topic:
            diep_memory.record_topic(user_id, topic, session_id=session_id)
        else:
            fallback_topic = diep_memory.extract_topic_from_text(user_text)
            if fallback_topic:
                diep_memory.record_topic(user_id, fallback_topic, session_id=session_id)
    except Exception:
        pass

    # v6_spark_self_awareness_001 — laat Spark zijn eigen tabs/capabilities/help kennen
    # v6_spark_help_reuse_001 — help is gradatie-gefilterd per user
    self_awareness_snippet: Optional[str] = None
    try:
        aw = _load_self_awareness(user_id=user_id)
        if aw:
            self_awareness_snippet = _format_self_awareness_for_prompt(aw)
    except Exception:
        self_awareness_snippet = None

    # v6_spark_user_view_001 — relatie-context per user
    try:
        from modules.chat.spark_user_view import build_user_profile, format_for_system_prompt
        user_profile = build_user_profile(user_id)
        user_snippet = format_for_system_prompt(user_profile)

        # v6_identity_facts_002 — PRE-PEND facts (vóór toon-instructie) voor max prominentie
        # v10_admin_facts_full_001 — Voor gradatie 1 (Maker/Beheerder): geen cap.
        # v13s_identity_facts_tpm_cap_001 — cap toch nodig voor Groq's 8000 TPM. 15 per type
        # is ruim voldoende (~150 facts totaal), voorheen "999" gaf 8477-token prompts.
        try:
            from modules.chat import identity_facts
            # v13t_llm_budget_settings_001 — admin-cap uit settings/system
            from modules.core.storage import load_json as _lj2
            _cap_setting = None
            try:
                _sys2 = _lj2(Path(__file__).parent.parent.parent / "data" / "settings" / "system.json", default={}) or {}
                _cap_setting = int(_sys2.get("chat_identity_facts_cap_admin", 15))
            except Exception:
                _cap_setting = 15
            _grad = (user_profile or {}).get("gradatie") if isinstance(user_profile, dict) else None
            _cap = _cap_setting if _grad == 1 else 5
            facts = identity_facts.load_for_prompt(user_id, max_per_type=_cap)
            # v13_privacy_guard_001 — strip about_user/about_relationship voor grad >= 5
            try:
                from modules.chat import privacy_guard as _pg
                facts = _pg.filter_identity_facts(facts, _requester_grad)
            except Exception:
                pass
            facts_snippet = identity_facts.format_for_prompt(facts)
            if facts_snippet:
                # Plaats facts BOVENAAN het user_snippet — vóór tone-block
                user_snippet = facts_snippet + "\n\n" + (user_snippet or "")
        except Exception:
            pass
    except Exception:
        user_profile = {}
        user_snippet = None

    # v6_spark_planner_001 — Laag A (Daagse Brief) + Laag B (Open Draden) cross-day continuity
    planner_snippet: Optional[str] = None
    planner_meta: Dict[str, Any] = {}
    try:
        from modules.spark_planner.brief_builder import latest_brief as _latest_brief
        from modules.spark_planner.threads_service import active_threads_for_inject, format_for_system_prompt as _fmt_threads
        from modules.core.blueprint import load_blueprint_cached as _bp_load
        pbp = _bp_load("spark_planner", "planner")
        snippet_lines = []
        latest = _latest_brief(user_id)
        if latest and pbp.get("brief", {}).get("enabled", True):
            label = pbp["brief"].get("inject_label", "Wat je nog weet van het laatste gesprek")
            snippet_lines.append(f"{label} (van {latest.get('date')}):")
            snippet_lines.append(f"  {latest.get('summary', '')}")
            if latest.get("emotional_tone"):
                snippet_lines.append(f"  Toon van die dag: {latest['emotional_tone']}")
            planner_meta["brief_date"] = latest.get("date")
        if pbp.get("threads", {}).get("enabled", True):
            active = active_threads_for_inject(user_id)
            if active:
                tlabel = pbp["threads"].get("inject_label", "Open gespreksdraden die nog leven")
                snippet_lines.append("")
                snippet_lines.append(f"{tlabel}:")
                fmt = _fmt_threads(active)
                if fmt:
                    snippet_lines.append(fmt)
                planner_meta["active_threads"] = [t.get("topic") for t in active]
        if snippet_lines:
            planner_snippet = "\n".join(snippet_lines)
    except Exception:
        planner_snippet = None

    system_prompt = _build_system_prompt(
        bijbel, emotion, user_snippet, topic, planner_snippet, self_awareness_snippet,
        current_user_naam=(user_profile or {}).get("naam") or "Gebruiker",
        current_user_gradatie=(user_profile or {}).get("gradatie"),
    )

    # v13_privacy_guard_001 — laatste veeg: strip privacy-gevoelige namen uit
    # system_prompt voor grad >= 5. Requester's eigen naam blijft (die zit niet
    # in de blokkeer-lijst; als familie: dan mag hij die zelf kennen).
    try:
        from modules.chat import privacy_guard as _pg
        system_prompt = _pg.strip_person_names(system_prompt, _requester_grad)
    except Exception:
        pass

    # v6_diep_snaps_001 + v6_diep_ops_context_001 — extra context-lagen voor Diep
    snap_cluster = _load_snap_cluster(user_text)
    ops_context = _load_ops_context(user_text, user_id)

    user_prompt_parts = [
        # v6_diep_time_001 — tijd-bewustzijn bovenaan zodat Spark altijd weet wanneer
        _format_now_for_prompt(),
        "",
    ]
    # v6_tab_context_001 — welke UI-tab kijkt de user nu naar?
    # v7_tab_context_soft_001 — soberder formuleren; NIET als opener gebruiken.
    if active_tab:
        tab_labels = {
            "chat": "Gesprekken", "dashboard": "Dashboard", "kennisbank": "Kennisbank V2",
            "kennisbank-v2": "Kennisbank V2", "agenda": "Agenda", "notities": "Notities",
            "dagboek": "Dagboek", "community": "Community", "bijdragen": "Bijdragen",
            "archief": "Archief", "roadmap": "Roadmap", "voice": "Voice",
            "trader": "Trade-bot", "wallet": "Wallet", "winkel": "Winkelstraat",
            "boekhouding": "Boekhouding", "settings": "Instellingen",
            "deploy": "Deploy", "tag-curatie": "Tag-curatie",
        }
        tab_label = tab_labels.get(active_tab.lower(), active_tab)
        user_prompt_parts.append(
            f"(context: user kijkt naar tab '{tab_label}' — gebruik alleen als de vraag over dat scherm gaat, "
            f"NOOIT als openingszin of stopwoord. Begin je antwoord NIET met 'je bent nu op X tab' of 'nu je naar X kijkt'.)"
        )
        user_prompt_parts.append("")
    user_prompt_parts += [
        "## KB-kaarten (hoge betrouwbaarheid, uit bevestigde kennis):",
        _format_kb_cards(cards),
    ]

    # v6_diep_memory_layers_001 — recent topics (cross-session) + relevant norms
    try:
        from modules.chat import diep_memory
        rt_snippet = diep_memory.format_recent_topics_for_prompt(recent_topics)
        if rt_snippet:
            user_prompt_parts += ["", rt_snippet]
        norm_snippet = diep_memory.format_norms_for_prompt(relevant_norms)
        if norm_snippet:
            user_prompt_parts += ["", norm_snippet]
    except Exception:
        pass
    if snap_cluster:
        user_prompt_parts += [
            "",
            "## Snap-cluster (eerder genoemd in gesprekken, LAGER vertrouwen ~0.3):",
            "_Gebruik deze als context, niet als hard feit. Markeer in je antwoord:_",
            "_'voor zover ik me herinner...' of 'volgens onze eerdere gesprekken...'_",
            _format_snap_cluster(snap_cluster),
        ]
    if ops_context:
        user_prompt_parts += [
            "",
            "## Live operationele info (vers uit het systeem):",
            ops_context,
        ]
    # v6_identity_leak_fix_001 — gebruik echte naam ipv hardcoded "Willem"
    _current_user_naam = (user_profile or {}).get("naam") or "Gebruiker"
    user_prompt_parts += [
        "",
        "## Recente gesprek-turns:",
        _format_turns(turns, user_naam=_current_user_naam),
        "",
        f"## Huidige vraag van {_current_user_naam}:",
        user_text,
        "",
    ]
    if _new_relations or _personalia_saved:
        _saved_bits = [f"{r.get('relation_type', '')}: {r.get('person_name', '')}" for r in _new_relations]
        _saved_bits += [str(p.get("summary") or p.get("field") or p) for p in _personalia_saved]
        user_prompt_parts += [f"## Zojuist écht opgeslagen in het profiel van {_current_user_naam}: " + "; ".join(_saved_bits),
                              "Bevestig kort dat dit is vastgelegd. Zeg nooit 'ik noteer' over iets dat hier niet staat.", ""]
    else:
        user_prompt_parts += ["(Er is niets automatisch opgeslagen uit deze zin. Zeg dus NIET 'ik noteer' of 'ik sla op'; stel hooguit voor het in Mijn Profiel te zetten.)", ""]
    user_prompt_parts += [
        "Reageer in Spark's stem, in het Nederlands.",
    ]
    user_prompt = "\n".join(user_prompt_parts)

    # v13t_llm_budget_settings_001 — waardes uit settings/system (admin-tunable via
    # Beheer → Kladblok → LLM Budget Settings widget). Fallback op sensible defaults.
    try:
        from modules.core.storage import load_json as _lj
        _sys_settings = _lj(Path(__file__).parent.parent.parent / "data" / "settings" / "system.json", default={}) or {}
    except Exception:
        _sys_settings = {}
    HARD_INPUT_CHAR_BUDGET = int(_sys_settings.get("chat_hard_input_budget", 22000))
    MAX_USER_PROMPT_CHARS = int(_sys_settings.get("chat_max_user_prompt_chars", 3000))
    MAX_SYSTEM_PROMPT_CHARS = int(_sys_settings.get("chat_max_system_prompt_chars", 16000))
    _CONTEXT_TURNS = int(_sys_settings.get("chat_context_turns", 3))
    _MAX_TURN_CHARS = int(_sys_settings.get("chat_max_turn_chars", 1500))

    if len(user_prompt) > MAX_USER_PROMPT_CHARS:
        original_len = len(user_prompt)
        keep_head = int(MAX_USER_PROMPT_CHARS * 0.7)
        keep_tail = int(MAX_USER_PROMPT_CHARS * 0.25)
        user_prompt = (
            user_prompt[:keep_head]
            + f"\n\n[…{original_len - keep_head - keep_tail} tekens weggelaten om binnen TPM-limiet te blijven — Spark: als je dit ziet, meld dat de tekst was ingekort…]\n\n"
            + user_prompt[-keep_tail:]
        )

    if len(system_prompt) > MAX_SYSTEM_PROMPT_CHARS:
        system_prompt = system_prompt[:MAX_SYSTEM_PROMPT_CHARS] + "\n[…system context ingekort voor TPM-budget…]"

    try:
        # v6_llm_router_001 — gebruik multi-provider router i.p.v. directe Emergent-call.
        # Volgorde: Groq → Cerebras/Fallback → Emergent → template.
        from . import llm_router

        # Bouw OpenAI-compatible messages (system + accumulated turns + current user)
        messages = [{"role": "system", "content": system_prompt}]
        # v13t_llm_budget_settings_001 — laatste N turns uit settings (default 3)
        if turns:
            for t in turns[-_CONTEXT_TURNS:]:
                role = "user" if t.get("role") == "user" else "assistant"
                ttxt = (t.get("text") or t.get("message") or "").strip()
                if ttxt:
                    if len(ttxt) > _MAX_TURN_CHARS:
                        ttxt = ttxt[:int(_MAX_TURN_CHARS * 0.7)] + " […ingekort…] " + ttxt[-int(_MAX_TURN_CHARS * 0.2):]
                    messages.append({"role": role, "content": ttxt})
        messages.append({"role": "user", "content": user_prompt})

        # v13t_user_text_tpm_guard_001 — als totaal boven budget: agressief snijden op turns eerst
        total_chars = sum(len(m.get("content", "")) for m in messages)
        while total_chars > HARD_INPUT_CHAR_BUDGET and len(messages) > 2:
            # verwijder oudste non-system message
            for i, m in enumerate(messages):
                if m.get("role") != "system":
                    messages.pop(i)
                    break
            total_chars = sum(len(m.get("content", "")) for m in messages)

        router_resp = await llm_router.chat_complete(
            messages,
            temperature=0.7,
            max_tokens=1024,
            timeout=30.0,
        )

        if not router_resp.get("success"):
            # v13_llm_budget_user_message_001 (sessie 53): "all_providers_failed" was
            # cryptisch voor Willem. Nu: kijk naar de errors van de gefaalde providers
            # en geef een concreet Nederlands verhaal terug.
            tried = router_resp.get("tried") or []

            def _classify(err: str) -> str:
                e = (err or "").lower()
                if "tpd" in e or "tokens per day" in e or ("429" in e and "day" in e):
                    return "tpd"
                if "429" in e or "rate limit" in e or "rate_limit" in e:
                    return "rate"
                if "402" in e or "payment required" in e or "quota" in e or "budget" in e:
                    return "budget"
                if "timeout" in e:
                    return "timeout"
                return "other"

            classes = {_classify(t.get("error", "")) for t in tried if not t.get("ok")}
            if classes and classes.issubset({"tpd", "rate", "budget"}):
                # Alles op quota — Willem herkent dit pattern nu
                friendly = (
                    "Even niet mogelijk — Groq zit vandaag op quota-limiet en "
                    "Emergent-nood-nood is ook op. Reset volgt vanzelf, óf vul "
                    "Emergent bij: *Profile → Manage plan → Universal Key → Add Balance*."
                )
            elif "timeout" in classes:
                friendly = "Verbinding hapert even — probeer over een moment opnieuw."
            else:
                friendly = (
                    "Even iets mis met mijn taalmodel-lijnen. "
                    "Ik geef 't door aan de admin (details staan in de logs)."
                )

            return {
                "success": False,
                "error": router_resp.get("error", "llm_router_failed"),
                "message": friendly,
                "tried": tried,
                "fallback": True,
            }

        text = router_resp["text"]
        # v7_tool_leak_sanitizer_001 — strip elke tool-call syntax die de LLM per ongeluk
        # in de user-reactie plakt (bv. "[agenda_lezen {"date":"2026-05-17"}]" of
        # "We need to call agenda_lezen with date..."). Deze mogen NOOIT bij de user komen.
        # v13_tts_json_leak_sanitizer_001 (sessie 53): LLM begint soms "action/payload"
        # JSON-blokken te typen (tts_speak, open_help, ...). Als er een `text`-veld in zit
        # extraheren we dat als antwoord; anders halen we het blok gewoon weg.
        try:
            import re as _re
            import json as _json

            # Fase 0: JSON-actie-blokken detecteren (```json ... ``` of los blok)
            # Patroon vangt zowel ```json {...} ``` als bare {"action": ...}
            def _extract_text_from_action_block(match_body: str) -> str:
                try:
                    parsed = _json.loads(match_body)
                    payload = parsed.get("payload") or {}
                    inner = payload.get("text")
                    if isinstance(inner, str) and inner.strip():
                        return inner.strip()
                except Exception:
                    pass
                return ""

            # Fenced ```json {...} ```
            def _fenced_repl(m):
                return _extract_text_from_action_block(m.group(1))
            text = _re.sub(
                r"```(?:json)?\s*(\{[^`]*?\"action\"\s*:\s*\"[a-z_]+\"[^`]*?\})\s*```",
                _fenced_repl, text, flags=_re.DOTALL,
            )
            # Bare JSON-blok in tekst
            def _bare_repl(m):
                return _extract_text_from_action_block(m.group(1))
            text = _re.sub(
                r"(\{\s*\"action\"\s*:\s*\"[a-z_]+\"\s*,\s*\"payload\"\s*:\s*\{[^{}]*\}\s*\})",
                _bare_repl, text, flags=_re.DOTALL,
            )

            # Verwijder bracket-tool-calls: [tool_name {json}] of [tool_name(...)]
            text = _re.sub(r"\[[a-z_][a-z0-9_]{2,30}\s*[\{\(][^\]]*?[\}\)]\]", "", text)
            # Verwijder "We need to call X" / "Let me call X" / "I will call X" zinnen tot punt
            text = _re.sub(r"(?i)\b(we need to|let me|i (?:will|should)|ik moet)\s+call\s+[a-z_]+[^\.\n]*\.\s*", "", text)
            # Verwijder losse tool-annotaties als "[tool_name]" (zonder args)
            text = _re.sub(r"\[[a-z_][a-z0-9_]{4,30}\](?=[A-Z\n])", "", text)
            # Meerdere spaties + lege regels normaliseren
            text = _re.sub(r"[ \t]{2,}", " ", text)
            text = _re.sub(r"\n{3,}", "\n\n", text).strip()
        except Exception:
            pass  # sanitize is best-effort, faalt geen response op
        used_provider = router_resp.get("provider", "?")
        used_model = router_resp.get("model", "?")
        model_provider = used_provider  # voor log-write hieronder
        model_name = used_model

        # v6_response_composer_001 — persisteer multi-turn memory per session_id
        # Zodat volgende call _load_recent_turns() echte context heeft.
        if session_id:
            try:
                from modules.core.storage import save_json
                turns_dir = Path(bp["paths"]["turns_dir"])
                turns_dir.mkdir(parents=True, exist_ok=True)
                fp = turns_dir / f"{session_id}.json"
                existing = load_json(fp, default={"messages": []})
                msgs = existing.get("messages", [])
                ts = datetime.now(timezone.utc).isoformat()
                msgs.append({"role": "user", "text": user_text, "ts": ts, "user_id": user_id})
                msgs.append({"role": "spark", "text": text, "ts": ts, "model": f"{model_provider}/{model_name}"})
                # Beperk tot laatste 50 turns om bestand klein te houden
                msgs = msgs[-50:]
                save_json(fp, {"messages": msgs, "session_id": session_id, "user_id": user_id, "updated_at": ts})
            except Exception:
                pass  # Multi-turn memory is best-effort, faalt geen response op

        # v6_deep_log_001 — Diep-gesprekken ook in centrale chat_log_service zodat
        # Chat-Recap / Shadow-Observer / gesprek-overzicht-UI ze meeneemt.
        if session_id:
            try:
                from modules.chat import chat_log_service
                user_naam = (user_profile or {}).get("naam") or user_id
                chat_log_service.save_message(
                    user_id=user_id,
                    user_naam=user_naam,
                    user_message=user_text,
                    spark_response=text,
                    channel="spark-deep",
                    session_id=session_id,
                    analysis={
                        "topic": topic,
                        "used_cards": [c.get("id") for c in cards],
                        "model": f"{model_provider}/{model_name}",
                    },
                )
            except Exception:
                pass  # log-write is best-effort, faalt geen response op

        # v6_diep_snap_write_001 — auto-snap bij kennisgat (Diep doet 'snap' net als normale chat)
        try:
            had_kb = bool(cards) and len(cards) >= 2
            user_naam_for_snap = (user_profile or {}).get("naam") or user_id or "diep-user"
            _auto_snap_from_diep(user_text, user_naam_for_snap, had_kb_match=had_kb)
        except Exception:
            pass

        # v6_trigger_learner_001 — non-blocking LLM-driven trigger-learning
        # Spark leert welke triggers vragen had kunnen matchen voor fast-path next time
        try:
            from modules.chat.trigger_learner import schedule_learn
            schedule_learn(user_text, text, user_id=user_id, session_id=session_id)
        except Exception:
            pass

        # v6_identity_facts_001 — extract identity-claims uit user-text (sync, snel, regex-only)
        try:
            from modules.chat import identity_facts
            identity_facts.extract_and_save(user_id, user_text, session_id=session_id)
        except Exception:
            pass

        # v6_deep_side_effects_001 — KB-card geluid (voice_kind=geluid) — eerste card
        # met sound_url. Action-commands (TTS/STT/ambient) zijn al via try_detect short-circuit
        # afgehandeld vóór de LLM-call (zie boven in deze functie).
        deep_sound_url: Optional[str] = None
        try:
            for c in cards:
                media = c.get("media") or {}
                snd = media.get("sound_url") or c.get("sound_url")
                if snd and (media.get("voice_kind") == "geluid" or c.get("voice_kind") == "geluid"):
                    deep_sound_url = snd
                    break
        except Exception:
            pass

        return {
            "success": True,
            "message": text,
            "new_relations": _new_relations or None,
            "personalia_saved": _personalia_saved or None,
            "used_cards": [c.get("id") for c in cards],
            "used_model": f"{model_provider}/{model_name}",
            "blueprint_version": bp.get("_schema_version", "?"),
            "topic": topic if tt_cfg.get("expose_in_meta", True) else None,
            "planner": planner_meta or None,
            # v6_deep_side_effects_001 — frontend kan KB-geluid afspelen vóór TTS
            "sound_url": deep_sound_url,
            "user_profile": {
                "naam": user_profile.get("naam"),
                "gradatie": user_profile.get("gradatie"),
                "themes_count": len(user_profile.get("recente_themes") or []),
                "relaties_count": len(user_profile.get("relaties") or []),
            } if user_profile else None,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as ex:
        return {"success": False, "error": str(ex), "fallback": True}
