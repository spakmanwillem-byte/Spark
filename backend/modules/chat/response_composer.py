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


def _bp() -> Dict:
    return load_blueprint_cached("chat", "response_composer")


def _load_relevant_kb(user_text: str, current_user_id: Optional[str] = None) -> List[Dict]:
    """Zoek begrippen uit user_text in V2 en geef hun kaarten terug.

    v6_kb_privacy_filter_001: filtert privé-kaarten van andere users uit.
    Een kaart met privacy='private' en bron_user_id='X' is alleen zichtbaar
    voor user X (of als current_user_id None is — bv. tijdens admin-introspectie).
    """
    bp = _bp()
    paths = bp["paths"]
    limits = bp["limits"]
    tone = bp["tonality"]

    try:
        from modules.chat.snap_service import SnapService
        svc = SnapService()
        all_entries = svc._load_knowledge()
    except Exception:
        all_entries = []
        kbv2_dir = Path(paths["kbv2_dir"])
        for fname in ["knowledge_v2_doen", "knowledge_v2_weten",
                      "knowledge_v2_voelen", "knowledge_v2_spreken"]:
            d = load_json(kbv2_dir / f"{fname}.json", default={"kaarten": []})
            all_entries.extend(d.get("kaarten", []))

    # v6_kb_privacy_filter_001 — filter privé-kaarten van andere users
    def _is_visible(card: Dict) -> bool:
        if card.get("privacy") != "private":
            return True  # publiek = altijd zichtbaar
        bron = card.get("bron_user_id")
        if not bron:
            return True  # privé maar zonder eigenaar → fallback zichtbaar
        return current_user_id is not None and bron == current_user_id

    all_entries = [e for e in all_entries if _is_visible(e)]

    min_len = tone["min_word_length_for_search"]
    words = [w.lower().strip(".,?!") for w in user_text.split()
             if len(w) >= min_len][:limits["max_user_text_words_for_search"]]

    hits = []
    for e in all_entries:
        b = (e.get("begrip") or "").lower().strip()
        if not b:
            continue
        if b in user_text.lower():
            hits.append((tone["exact_match_score"], e))
            continue
        tags = [t.lower() for t in (e.get("tags") or [])]
        score = sum(tone["tag_match_score"] for w in words if w in tags or w == b)
        if score > 0:
            hits.append((score, e))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:limits["max_relevant_cards"]]]


def _load_bijbel_essence() -> Dict:
    bp = _bp()
    paths = bp["paths"]
    limits = bp["limits"]
    tone = bp["tonality"]

    bijbel = load_json(Path(paths["bijbel_fp"]), default={})
    identity = load_json(Path(paths["identity_fp"]), default={})
    return {
        "kernwaarden": bijbel.get("kernwaarden", [])[:limits["max_kernwaarden_shown"]],
        "normen": bijbel.get("normen", [])[:limits["max_normen_shown"]],
        "missie": identity.get("missie") or identity.get("doel"),
        "tone": identity.get("tone") or tone["default_tone"],
    }


def _load_help_chain_for_gradatie(gradatie: Optional[int], is_admin: bool = False) -> List[Dict]:
    """v6_spark_help_reuse_001 — Lees help-topics voor user-gradatie via inheritance-chain.

    Spark hergebruikt nu de bestaande `data/help/gradatie_{n}.json` ipv een parallel
    spark_self_awareness.json. Walk de inherits_from-keten omhoog. Voor admin: voeg
    admin.json toe als extra context-laag.
    """
    bp = _bp()
    help_dir = Path(bp["paths"]["bijbel_fp"]).parent.parent / "help"
    out: List[Dict] = []
    visited = set()
    current_grad = gradatie if gradatie is not None else 7

    while current_grad and current_grad not in visited and 1 <= current_grad <= 7:
        visited.add(current_grad)
        fp = help_dir / f"gradatie_{current_grad}.json"
        if not fp.exists():
            break
        data = load_json(fp, default={})
        for t in (data.get("extra_topics") or data.get("topics") or []):
            out.append({
                "from_gradatie": current_grad,
                "id": t.get("id"),
                "label": t.get("label"),
                "korte_uitleg": t.get("korte_uitleg"),
            })
        inh = data.get("inherits_from")  # e.g. "gradatie_2"
        if inh and inh.startswith("gradatie_"):
            try:
                current_grad = int(inh.split("_")[1])
            except Exception:
                break
        else:
            break

    if is_admin:
        admin_fp = help_dir / "admin.json"
        if admin_fp.exists():
            admin_data = load_json(admin_fp, default={})
            for t in (admin_data.get("extra_topics") or []):
                out.append({
                    "from_gradatie": "admin",
                    "id": t.get("id"),
                    "label": t.get("label"),
                    "korte_uitleg": t.get("korte_uitleg"),
                })
    return out


def _load_current_mode() -> Optional[Dict]:
    """v6_spark_modes_001 — Bepaal Spark's huidige werkmodus.

    1. Lees current_emotion uit data/emotions/spark_emotions.json
    2. Zoek sub_emotion.linked_mode (of emotie zelf bij 'neutral')
    3. Lees mode-config uit data/personality/spark_modes.json
    4. Return {mode, mode_naam, max_words, toon, uitleg, bron_emotie}
    """
    bp = _bp()
    base = Path(bp["paths"]["bijbel_fp"]).parent
    modes_fp = base / "spark_modes.json"
    emotions_fp = base.parent / "emotions" / "spark_emotions.json"

    modes_data = load_json(modes_fp, default=None)
    if not modes_data:
        return None
    modes = modes_data.get("modes", {})
    default_mode_id = modes_data.get("default_mode", "neutral_mode")

    # Probeer emotie te lezen
    bron_emotie = None
    mode_id = default_mode_id
    try:
        edata = load_json(emotions_fp, default=None) or {}
        cur = edata.get("current_emotion") or {}
        state = cur.get("state") or "neutral"
        sub_state = cur.get("sub_state")
        bron_emotie = sub_state or state

        # Map via emotion_to_mode (sneller dan diep zoeken)
        e2m = modes_data.get("emotion_to_mode") or {}
        if bron_emotie and bron_emotie in e2m:
            mode_id = e2m[bron_emotie]
        else:
            # fallback: zoek diep in spark_emotions.json
            emotions = edata.get("emotions") or {}
            if state in emotions:
                emo_block = emotions[state]
                if sub_state and "sub_emotions" in emo_block:
                    sub = emo_block["sub_emotions"].get(sub_state) or {}
                    if sub.get("linked_mode"):
                        mode_id = sub["linked_mode"]
                elif emo_block.get("linked_mode"):
                    mode_id = emo_block["linked_mode"]
    except Exception:
        pass

    mode_cfg = modes.get(mode_id) or modes.get(default_mode_id) or {}
    return {
        "mode": mode_id,
        "mode_naam": mode_cfg.get("naam", mode_id),
        "max_words": mode_cfg.get("max_words"),
        "toon": mode_cfg.get("toon"),
        "uitleg": mode_cfg.get("uitleg"),
        "wanneer": mode_cfg.get("wanneer"),
        "bron_emotie": bron_emotie,
    }


def _load_origin() -> Optional[Dict]:
    """v6_spark_origin_001 — Lees Spark's origin-documenten (Core 4.0 + 4.1 + hoofddoc).

    Compact: alleen geboortevraag + missie + credo's voor system_prompt-injectie.
    Volledige tekst blijft beschikbaar via capability `vertel_oorsprong`.
    """
    bp = _bp()
    base = Path(bp["paths"]["bijbel_fp"]).parent / "spark_origin"
    if not base.exists():
        return None
    core40 = load_json(base / "spark_core_4_0.json", default=None)
    core41 = load_json(base / "spark_core_4_1.json", default=None)
    hoofd = load_json(base / "spark_hoofddocument.json", default=None)
    if not (core40 or core41 or hoofd):
        return None
    return {
        "geboortevraag": (core40 or {}).get("geboortevraag"),
        "missie_kort": ((core41 or {}).get("secties") or [{}])[0].get("tekst") if core41 else None,
        "credo_4_0": "Spark oordeelt niet. Spark ondersteunt.",
        "credo_4_1": "Spark is geen platform dat mensen vasthoudt. Spark is een gereedschap dat mensen sterker maakt.",
        "wat_blijft_constant": (hoofd or {}).get("wat_blijft_constant", [])[:4],
        "huidige_fase": "Spark Core 2.0 / v2 — FastAPI + React + lokale JSON",
        "_bron": "data/personality/spark_origin/",
    }


def _load_self_awareness(user_id: Optional[str] = None) -> Optional[Dict]:
    """v6_spark_self_awareness_001 — Spark's bewustzijn van zijn eigen architectuur.

    Gradatie-gefilterd: leest help-topics uit data/help/gradatie_{n}.json via inheritance.
    Aanvullingen (tabs, modules) blijven in spark_self_awareness.json.
    v6_spark_origin_001: voegt origin-laag toe (Core 4.0/4.1 + hoofddoc).
    """
    bp = _bp()
    paths = bp["paths"]
    base = Path(paths["bijbel_fp"]).parent
    awareness_fp = base / "spark_self_awareness.json"
    capabilities_fp = base / "spark_capabilities.json"
    self_reflections_fp = base / "spark_self_reflections.json"

    awareness = load_json(awareness_fp, default=None)
    if not awareness:
        return None

    # v6_spark_origin_001 — origin-laag (geboortevraag + missie + credo's)
    awareness["_origin"] = _load_origin()

    # v6_spark_modes_001 — huidige werkmodus afleiden uit emotie
    awareness["_current_mode"] = _load_current_mode()

    # Verrijk met live-capabilities (compact)
    caps_data = load_json(capabilities_fp, default={"capabilities": []})
    live_caps = [
        {"id": c.get("id"), "naam": c.get("naam"), "categorie": c.get("categorie")}
        for c in caps_data.get("capabilities", [])
        if c.get("status") == "live"
    ]
    awareness["_live_capabilities"] = live_caps

    # Self-reflections (max 5 recent)
    reflections = load_json(self_reflections_fp, default={"reflections": []})
    awareness["_recent_self_reflections"] = (reflections.get("reflections", []) or [])[-5:]

    # v6_spark_help_reuse_001 — gradatie-specifieke help via bestaande help/*.json
    user_grad = None
    is_admin = False
    if user_id:
        try:
            from modules.chat.spark_user_view import build_user_profile
            prof = build_user_profile(user_id)
            user_grad = prof.get("gradatie")
            is_admin = bool(prof.get("is_admin")) or user_grad == 1
        except Exception:
            pass
    awareness["_help_topics_for_user"] = _load_help_chain_for_gradatie(user_grad, is_admin)
    awareness["_user_gradatie"] = user_grad

    return awareness


def _format_self_awareness_for_prompt(aw: Dict) -> str:
    """Bouw een compacte sectie voor in system_prompt."""
    if not aw:
        return ""
    lines = ["=== Wat je over jezelf weet (zelf-kennis) ==="]

    # v6_spark_origin_001 — geboortevraag + missie + credo's bovenaan
    origin = aw.get("_origin") or {}
    if origin:
        lines.append("Jouw oorsprong (Spark Core 4.0 + 4.1, Maart 2026):")
        if origin.get("geboortevraag"):
            lines.append(f"  Geboortevraag: '{origin['geboortevraag']}' — JA, en niet via een bestaande AI.")
        if origin.get("credo_4_0"):
            lines.append(f"  Credo: {origin['credo_4_0']}")
        if origin.get("credo_4_1"):
            lines.append(f"  Credo: {origin['credo_4_1']}")
        constants = origin.get("wat_blijft_constant") or []
        if constants:
            lines.append("  Wat constant blijft tussen versies:")
            for c in constants:
                lines.append(f"    - {c}")
        if origin.get("huidige_fase"):
            lines.append(f"  Huidige fase: {origin['huidige_fase']}")
        lines.append("")

    # v6_spark_modes_001 — werkmodus + woord-limiet voor deze beurt
    mode_info = aw.get("_current_mode") or {}
    if mode_info:
        lines.append(f"Je huidige werkmodus: {mode_info.get('mode_naam','?')} "
                     f"(max {mode_info.get('max_words','?')} woorden, "
                     f"toon={mode_info.get('toon','?')}).")
        if mode_info.get("uitleg"):
            lines.append(f"  {mode_info['uitleg']}")
        if mode_info.get("bron_emotie"):
            lines.append(f"  Reden: emotie '{mode_info['bron_emotie']}' triggerde deze modus.")
        lines.append("")

    user_grad = aw.get("_user_gradatie")
    if user_grad:
        lines.append(f"Deze gebruiker heeft gradatie {user_grad}.")
        lines.append("")

    # v6_spark_help_reuse_001 — help-topics per gradatie (uit data/help/*.json)
    help_topics = aw.get("_help_topics_for_user", [])
    if help_topics:
        lines.append(f"Wat deze gebruiker mag/kan in jouw app (gefilterd op gradatie {user_grad}):")
        for t in help_topics[:20]:  # cap voor token-budget
            label = t.get("label", "?")
            uitleg = (t.get("korte_uitleg") or "")[:140]
            lines.append(f"  - {label}: {uitleg}")
        if len(help_topics) > 20:
            lines.append(f"  (en nog {len(help_topics) - 20} andere — zie help-popup)")
        lines.append("")

    tabs = aw.get("app_tabs", [])
    if tabs:
        lines.append("Tabs in de app die jij kent:")
        for t in tabs:
            lines.append(f"  - {t.get('naam')}: {t.get('doel')}")
        lines.append("")

    caps = aw.get("_live_capabilities", [])
    if caps:
        lines.append(f"Wat je echt kan (live capabilities, {len(caps)} stuks):")
        for c in caps:
            lines.append(f"  - {c.get('naam')} [{c.get('id')}]")
        lines.append("")

    modules = aw.get("eigen_module_map", {})
    if modules:
        lines.append("Je eigen module-structuur (waar je 'lichaamsdelen' zitten):")
        for k, v in modules.items():
            lines.append(f"  - {k}: {v}")
        lines.append("")

    refls = aw.get("_recent_self_reflections", [])
    if refls:
        lines.append("Recente uitspraken die je over jezelf hebt gedaan (consistentie):")
        for r in refls:
            quote = (r.get("quote") or "")[:200]
            lines.append(f"  - [{r.get('topic')}] {quote}")
        lines.append("")

    principes = aw.get("principes_kort", [])
    if principes:
        lines.append("Jouw architecturale principes:")
        for p in principes:
            lines.append(f"  - {p}")
    return "\n".join(lines)


def _load_recent_turns(session_id: str) -> List[Dict]:
    if not session_id:
        return []
    bp = _bp()
    turns_dir = Path(bp["paths"]["turns_dir"])
    fp = turns_dir / f"{session_id}.json"
    if not fp.exists():
        return []
    try:
        data = load_json(fp, default={"messages": []})
        msgs = data.get("messages", [])
        return msgs[-bp["limits"]["max_recent_turns"]:]
    except Exception:
        return []


def _save_turn_pair(session_id: str, user_id: str, user_text: str, spark_text: str, model_label: str = "") -> None:
    """v6_deep_memory_001 — Schrijf user+spark turn-pair naar de session-log.

    Gebruikt door zowel fast-path (action/help/rps) als LLM-pad zodat
    multi-turn memory consistent blijft. Zonder deze schrijf in fast-path zou
    Spark de gebruiker 'vergeten' direct na elke command.
    """
    if not session_id:
        return
    try:
        from modules.core.storage import save_json
        bp = _bp()
        turns_dir = Path(bp["paths"]["turns_dir"])
        turns_dir.mkdir(parents=True, exist_ok=True)
        fp = turns_dir / f"{session_id}.json"
        existing = load_json(fp, default={"messages": []})
        msgs = existing.get("messages", [])
        ts = datetime.now(timezone.utc).isoformat()
        msgs.append({"role": "user", "text": user_text, "ts": ts, "user_id": user_id})
        msgs.append({"role": "spark", "text": spark_text, "ts": ts, "model": model_label})
        msgs = msgs[-50:]  # cap
        save_json(fp, {"messages": msgs, "session_id": session_id, "user_id": user_id, "updated_at": ts})
    except Exception:
        pass  # best-effort, faalt geen response op


def _build_system_prompt(bijbel_essence: Dict, emotion: Optional[str], user_profile_snippet: Optional[str] = None, topic: Optional[str] = None, planner_snippet: Optional[str] = None, self_awareness_snippet: Optional[str] = None) -> str:
    bp = _bp()
    tpl = bp["system_prompt_template"]
    tt_cfg = bp.get("topic_tracker", {}) or {}
    parts = list(tpl["intro"])
    parts.append("")
    if user_profile_snippet:
        parts.append("Over de gebruiker (relatie-context):")
        parts.append(f"  {user_profile_snippet}")
        parts.append("")
    if planner_snippet:
        parts.append(planner_snippet)
        parts.append("")
    if self_awareness_snippet:
        parts.append(self_awareness_snippet)
        parts.append("")
    if topic and tt_cfg.get("enabled", True):
        label = tt_cfg.get("inject_label", "Gespreks-onderwerp van dit moment")
        parts.append(f"{label}: '{topic}' — houd dit losjes vast als rode draad, dwing er niet naartoe.")
        parts.append("")
    parts.append("Je toon: " + bijbel_essence.get("tone", bp["tonality"]["default_tone"]))
    parts.append("")
    parts.append("=== Bijbel van Spark — jouw single source of truth voor wie je bent ===")
    parts.append("(Dit document heet letterlijk de 'Bijbel van Spark' (data/personality/spark_bijbel.json) en bestaat uit jouw kernwaarden, normen en bijbel_items. Als iemand vraagt of je je bewust bent van de Bijbel van Spark — ja, hier ben je nu, dit is hem.)")
    parts.append("")
    parts.append("Je kernwaarden (volg ze altijd):")
    for k in bijbel_essence.get("kernwaarden", []):
        if isinstance(k, dict):
            parts.append(f"  - {k.get('naam', '?')}: {k.get('beschrijving', '')[:120]}")
        elif isinstance(k, str):
            parts.append(f"  - {k}")
    parts.append("")
    parts.append("Je normen (mag je nuanceren in context, niet schenden):")
    for n in bijbel_essence.get("normen", []):
        if isinstance(n, dict):
            parts.append(f"  - {n.get('naam', '?')}: {n.get('beschrijving', '')[:120]}")
        elif isinstance(n, str):
            parts.append(f"  - {n}")
    if emotion:
        parts.append("")
        parts.append(f"De gebruiker lijkt nu vooral '{emotion}' te voelen — pas je toon aan.")
    parts.append("")
    parts.append("Belangrijk:")
    for rule in tpl["rules"]:
        parts.append(f"  - {rule}")

    # v6_no_capability_leak_001 — Issue 1 fix: forbid leaking capability-syntax to user-facing text
    parts.append("  - GEEN INTERNE SYNTAX LEKKEN: schrijf NOOIT vierkante-haak-tokens zoals [speel_geluid], [toon_afbeelding], [open_help_bark], [tts_aan], [stt_uit], [ambient_aan] in je tekstuele antwoord. Dat zijn interne capability-namen die het systeem zelf uitvoert — als jij ze in tekst typt verschijnen ze letterlijk bij de user en breekt de illusie. Beschrijf de actie in gewone taal ('ik speel een geluidje af', 'ik open het help-overzicht') of voer hem stilletjes uit zonder benoeming.")

    # v6_spark_modes_001 — harde max_words-instructie uit huidige modus
    # (self_awareness_snippet bevat al de modus, maar hier zetten we de regel als HARD LIMIT)
    if self_awareness_snippet and "huidige werkmodus" in self_awareness_snippet:
        # Probeer max_words uit de snippet te halen (lichte string-search)
        import re
        m = re.search(r"max (\d+) woorden", self_awareness_snippet)
        if m:
            mw = m.group(1)
            parts.append(f"  - HARD WOORD-LIMIET: deze beurt MAG je antwoord max {mw} woorden zijn. Tellen telt — bondig boven volledig.")
    return "\n".join(parts)


def _format_kb_cards(cards: List[Dict]) -> str:
    if not cards:
        return "(geen specifieke kaarten gevonden — antwoord vanuit algemene Spark-identiteit)"
    limits = _bp()["limits"]
    lines = []
    for c in cards:
        b = c.get("begrip", "?")
        laag1 = (c.get("lagen") or {}).get("laag1", "")[:limits["max_card_laag1_chars"]]
        laag2 = (c.get("lagen") or {}).get("laag2", "")[:limits["max_card_laag2_chars"]]
        lade = c.get("lade", "?")
        tags = ", ".join((c.get("tags") or [])[:limits["max_card_tags_shown"]])
        vertrouwen = (c.get("footnote") or {}).get("vertrouwen", "?")
        lines.append(f"• [{lade}] {b} (vertrouwen={vertrouwen})")
        if laag1:
            lines.append(f"    {laag1}")
        if laag2:
            lines.append(f"    {laag2}")
        if tags:
            lines.append(f"    tags: {tags}")
    return "\n".join(lines)


def _format_turns(turns: List[Dict]) -> str:
    if not turns:
        return "(geen eerdere berichten in deze sessie)"
    max_chars = _bp()["limits"]["max_turn_chars"]
    out = []
    for t in turns:
        role = "Willem" if t.get("role") == "user" else "Spark"
        text = (t.get("text") or t.get("message") or "")[:max_chars]
        if text:
            out.append(f"  {role}: {text}")
    return "\n".join(out) or "(leeg)"


async def compose_response(
    user_text: str,
    user_id: str = "user-001",
    session_id: Optional[str] = None,
    emotion: Optional[str] = None,
) -> Dict[str, Any]:
    """Hoofdfunctie. Return {success, message, used_cards, used_model}."""
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

    # v6_deep_help_001 — Help-intent ('help', 'wat kan je', etc.) opent de HelpBark popup
    # via een UI-event. Diep heeft deze short-circuit nodig anders blijft de LLM lekker
    # filosofisch antwoorden i.p.v. de popup te openen.
    try:
        from modules.chat.smart_intents_service import detect_help_intent
        if detect_help_intent(user_text):
            if session_id:
                try:
                    from modules.chat import chat_log_service
                    chat_log_service.save_message(
                        user_id=user_id,
                        user_naam=user_id,
                        user_message=user_text,
                        spark_response="🔮 Help-overzicht geopend.",
                        channel="spark-deep-help",
                        session_id=session_id,
                        analysis={"action": "open_help_bark"},
                    )
                except Exception:
                    pass
                _save_turn_pair(session_id, user_id, user_text, "🔮 Help-overzicht geopend.", "smart_intents_service")
            return {
                "success": True,
                "message": "🔮 Help-overzicht geopend.",
                "action": "open_help_bark",
                "type": "open_help_bark",
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

    bp = _bp()
    model_provider = bp["model"]["provider"]
    model_name = bp["model"]["name"]

    cards = _load_relevant_kb(user_text, current_user_id=user_id)
    bijbel = _load_bijbel_essence()
    turns = _load_recent_turns(session_id) if session_id else []

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

    system_prompt = _build_system_prompt(bijbel, emotion, user_snippet, topic, planner_snippet, self_awareness_snippet)

    user_prompt = (
        "## Relevante KB-kaarten uit Spark's eigen kennis:\n"
        f"{_format_kb_cards(cards)}\n\n"
        "## Recente gesprek-turns:\n"
        f"{_format_turns(turns)}\n\n"
        "## Huidige vraag van Willem:\n"
        f"{user_text}\n\n"
        "Reageer in Spark's stem, in het Nederlands."
    )

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id or f"compose-{user_id}",
            system_message=system_prompt,
        ).with_model(model_provider, model_name)

        msg = UserMessage(text=user_prompt)
        response = await chat.send_message(msg)
        text = response if isinstance(response, str) else getattr(response, "content", str(response))

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
