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


def _load_relevant_kb(user_text: str) -> List[Dict]:
    """Zoek begrippen uit user_text in V2 en geef hun kaarten terug."""
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


def _build_system_prompt(bijbel_essence: Dict, emotion: Optional[str], user_profile_snippet: Optional[str] = None) -> str:
    bp = _bp()
    tpl = bp["system_prompt_template"]
    parts = list(tpl["intro"])
    parts.append("")
    if user_profile_snippet:
        parts.append("Over de gebruiker (relatie-context):")
        parts.append(f"  {user_profile_snippet}")
        parts.append("")
    parts.append("Je toon: " + bijbel_essence.get("tone", bp["tonality"]["default_tone"]))
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
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        return {"success": False, "error": "EMERGENT_LLM_KEY ontbreekt in env"}

    bp = _bp()
    model_provider = bp["model"]["provider"]
    model_name = bp["model"]["name"]

    cards = _load_relevant_kb(user_text)
    bijbel = _load_bijbel_essence()
    turns = _load_recent_turns(session_id) if session_id else []

    # v6_spark_user_view_001 — relatie-context per user
    try:
        from modules.chat.spark_user_view import build_user_profile, format_for_system_prompt
        user_profile = build_user_profile(user_id)
        user_snippet = format_for_system_prompt(user_profile)
    except Exception:
        user_profile = {}
        user_snippet = None

    system_prompt = _build_system_prompt(bijbel, emotion, user_snippet)

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

        return {
            "success": True,
            "message": text,
            "used_cards": [c.get("id") for c in cards],
            "used_model": f"{model_provider}/{model_name}",
            "blueprint_version": bp.get("_schema_version", "?"),
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
