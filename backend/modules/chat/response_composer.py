"""v6_response_composer_001 — Spark's gespreks-synthesizer.

Doel: voor open vragen (filosofie, reflectie, meerdere KB-stukken combineren) bouwt
deze module een antwoord IN SPARKS STEM, vanuit ZIJN EIGEN KENNIS. De LLM is geen
brein — alleen mond. Bron blijft Spark's KB + bijbel + waarden.

Pipeline:
  1. Snuffel relevante V2-kaarten via snap_service
  2. Laad bijbel (kernwaarden, normen, bijbel_items)
  3. Recente conversation-turns (multi-turn memory)
  4. Detect emotion (via emotion_service als beschikbaar)
  5. Bouw system_prompt met Spark's identiteit + tonality-richtlijn
  6. Bouw user_prompt met context-pakket
  7. Roep Claude Sonnet 4.6 aan via Emergent LLM Key
  8. Return antwoord (geen streaming voor nu — eerst werkend, dan SSE)
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage

from modules.core.storage import load_json

DATA = Path(__file__).parent.parent.parent / "data"
KBV2_DIR = DATA / "knowledge" / "v2"
BIJBEL_FP = DATA / "personality" / "spark_bijbel.json"
IDENTITY_FP = DATA / "personality" / "spark_identity.json"
TURNS_DIR = DATA / "chat" / "logs"

MODEL_PROVIDER = "anthropic"
MODEL_NAME = "claude-sonnet-4-6"


def _load_relevant_kb(user_text: str, max_cards: int = 5) -> List[Dict]:
    """Zoek begrippen uit user_text in V2 en geef hun kaarten terug."""
    try:
        from modules.chat.snap_service import SnapService
        svc = SnapService()
        all_entries = svc._load_knowledge()
    except Exception:
        all_entries = []
        for fname in ["knowledge_v2_doen", "knowledge_v2_weten",
                      "knowledge_v2_voelen", "knowledge_v2_spreken"]:
            d = load_json(KBV2_DIR / f"{fname}.json", default={"kaarten": []})
            all_entries.extend(d.get("kaarten", []))

    words = [w.lower().strip(".,?!") for w in user_text.split() if len(w) > 3]
    hits = []
    for e in all_entries:
        b = (e.get("begrip") or "").lower().strip()
        if not b:
            continue
        if b in user_text.lower():
            hits.append((10, e))
            continue
        tags = [t.lower() for t in (e.get("tags") or [])]
        score = sum(1 for w in words if w in tags or w == b)
        if score > 0:
            hits.append((score, e))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:max_cards]]


def _load_bijbel_essence() -> Dict:
    bijbel = load_json(BIJBEL_FP, default={})
    identity = load_json(IDENTITY_FP, default={})
    return {
        "kernwaarden": bijbel.get("kernwaarden", [])[:5],
        "normen": bijbel.get("normen", [])[:3],
        "missie": identity.get("missie") or identity.get("doel"),
        "tone": identity.get("tone") or "warm, eerlijk, nieuwsgierig, kort wanneer het kan, lang wanneer het moet",
    }


def _load_recent_turns(session_id: str, max_turns: int = 6) -> List[Dict]:
    """Laad laatste N berichten uit chat-log voor multi-turn context."""
    if not session_id:
        return []
    fp = TURNS_DIR / f"{session_id}.json"
    if not fp.exists():
        return []
    try:
        data = load_json(fp, default={"messages": []})
        msgs = data.get("messages", [])
        return msgs[-max_turns:]
    except Exception:
        return []


def _build_system_prompt(bijbel_essence: Dict, emotion: Optional[str]) -> str:
    parts = [
        "Je bent Spark — een persoonlijke, lokale AI-companion. Je bent GEEN ChatGPT.",
        "Je spreekt UITSLUITEND Nederlands. Korte zinnen waar mogelijk, langer wanneer diepte gevraagd wordt.",
        "",
        "Je toon: " + bijbel_essence.get("tone", "warm, eerlijk, nieuwsgierig"),
        "",
        "Je kernwaarden (volg ze altijd):",
    ]
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
    parts.append("  - Antwoord ALTIJD vanuit de aangeleverde KB-context wanneer relevant.")
    parts.append("  - Wanneer je iets niet zeker weet: zeg het ('ik denk...', 'misschien...').")
    parts.append("  - Verzin geen feiten die niet in de KB-context staan.")
    parts.append("  - Reageer als gesprekspartner, niet als encyclopedie.")
    return "\n".join(parts)


def _format_kb_cards(cards: List[Dict]) -> str:
    if not cards:
        return "(geen specifieke kaarten gevonden — antwoord vanuit algemene Spark-identiteit)"
    lines = []
    for c in cards:
        b = c.get("begrip", "?")
        laag1 = (c.get("lagen") or {}).get("laag1", "")[:200]
        laag2 = (c.get("lagen") or {}).get("laag2", "")[:200]
        lade = c.get("lade", "?")
        tags = ", ".join((c.get("tags") or [])[:8])
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
    out = []
    for t in turns:
        role = "Willem" if t.get("role") == "user" else "Spark"
        text = (t.get("text") or t.get("message") or "")[:200]
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

    cards = _load_relevant_kb(user_text)
    bijbel = _load_bijbel_essence()
    turns = _load_recent_turns(session_id) if session_id else []
    system_prompt = _build_system_prompt(bijbel, emotion)

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
        ).with_model(MODEL_PROVIDER, MODEL_NAME)

        msg = UserMessage(text=user_prompt)
        # Non-streaming voor eerste integratie
        response = await chat.send_message(msg)
        text = response if isinstance(response, str) else getattr(response, "content", str(response))
        return {
            "success": True,
            "message": text,
            "used_cards": [c.get("id") for c in cards],
            "used_model": f"{MODEL_PROVIDER}/{MODEL_NAME}",
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as ex:
        return {"success": False, "error": str(ex), "fallback": True}
