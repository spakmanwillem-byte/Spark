"""
v6_intent_router_001 — Spark's handen (Layer 4): match → execute.

intent_matcher_service matcht een user-zin → capability_id.
Deze module bevat de daadwerkelijke handlers die de capability uitvoeren
en een chat-bericht terug formatteren.

Geen LLM nodig — directe data-lookups via bestaande services.

Hook punt: chat/routes.py vóór smart_intents (na safe-word + identity).
"""
from pathlib import Path
from typing import Optional, Dict
from modules.core.storage import load_json

DATA = Path(__file__).parent.parent.parent / "data"


def _handle_tellen_gebruikers(user_id: Optional[str]) -> Optional[Dict]:
    users = load_json(DATA / "system" / "users.json", default={"users": []}).get("users", [])
    humans = [u for u in users if not (u.get("id") or "").startswith("bot-")]
    bots = [u for u in users if (u.get("id") or "").startswith("bot-")]
    return {
        "type": "capability_response",
        "capability_id": "tellen_gebruikers",
        "message": (
            f"📊 We zijn met **{len(humans)} mensen** en **{len(bots)} bots** in Spark Core.\n"
            f"_Mensen: {', '.join((u.get('naam') or '?') for u in humans[:8])}{'…' if len(humans) > 8 else ''}_"
        ),
    }


def _handle_tellen_bestanden(user_id: Optional[str]) -> Optional[Dict]:
    arc = load_json(DATA / "system_archive" / "_index.json", default={"files": []})
    files = arc.get("files", [])
    total_bytes = sum(f.get("size_bytes", 0) for f in files)
    cats = {}
    for f in files:
        c = f.get("category", "overig")
        cats[c] = cats.get(c, 0) + 1
    parts = ", ".join(f"{k}: {v}" for k, v in sorted(cats.items()))
    mb = total_bytes / (1024 * 1024)
    return {
        "type": "capability_response",
        "capability_id": "tellen_bestanden",
        "message": f"📦 In het systeem-archief: **{len(files)} bestanden** ({mb:.1f} MB).\n_Verdeling: {parts}_",
    }


def _handle_taken_lijst(user_id: Optional[str]) -> Optional[Dict]:
    # Pak open backlog uit ROADMAP-JSON als die bestaat, anders een statisch overzicht
    rm = load_json(DATA / "system" / "roadmap.json", default={})
    open_items = []
    for k, section in (rm or {}).items():
        if isinstance(section, dict):
            for item in (section.get("items") or []):
                if item.get("status") in ("open", "pending", "in_progress"):
                    open_items.append(f"• {item.get('title', item.get('id', '?'))}")
    if not open_items:
        return {
            "type": "capability_response",
            "capability_id": "taken_lijst",
            "message": (
                "📋 **Open taken** (uit `/app/memory/ROADMAP.md`):\n"
                "• P0: Spark's hands — generic intent-router (deze laag nu live!)\n"
                "• P1: D&D Perks & Unlocks enforcement\n"
                "• P1: KB v2 hooks (Vocab/Graph/D&D/Voice-snippet)\n"
                "• P2: Frontend-knop boekhouder closing\n"
                "• P2: Closing-flow auto-trigger 21:00\n"
                "_Vraag 'wat zullen we doen?' voor concreter suggestie._"
            ),
        }
    return {
        "type": "capability_response",
        "capability_id": "taken_lijst",
        "message": "📋 **Open taken:**\n" + "\n".join(open_items[:10]),
    }


def _handle_winst_verlies(user_id: Optional[str]) -> Optional[Dict]:
    uid = user_id or "user-001"
    # Gebruik audit_log voor zekerste cijfers
    audit = load_json(DATA / "system" / "audit_log.json", default={"entries": []}).get("entries", [])
    sells = [e for e in audit if e.get("type") == "trade_sell" and e.get("user_id") == uid]
    netto = sum(s.get("netto", 0) for s in sells)
    n = len(sells)
    if n == 0:
        return {
            "type": "capability_response",
            "capability_id": "winst_verlies_overzicht",
            "message": "📈 Nog geen afgesloten trades op je account. Pas na een SELL komt hier een cijfer te staan.",
        }
    emoji = "✅" if netto >= 0 else "⚠️"
    return {
        "type": "capability_response",
        "capability_id": "winst_verlies_overzicht",
        "message": f"{emoji} Totaal over **{n} afgesloten trade(s)**: netto **€{netto:+.2f}**.",
    }


_HANDLERS = {
    "tellen_gebruikers":         _handle_tellen_gebruikers,
    "tellen_bestanden":          _handle_tellen_bestanden,
    "taken_lijst":               _handle_taken_lijst,
    "winst_verlies_overzicht":   _handle_winst_verlies,
}


def route_capability(text: str, user_id: Optional[str]) -> Optional[Dict]:
    """Match user-tekst → capability → execute handler. Return chat-response of None."""
    from . import intent_matcher_service
    match = intent_matcher_service.match_capability(text)
    if not match or match.get("confidence", 0) < 0.3:
        return None
    cap_id = match["capability_id"]
    handler = _HANDLERS.get(cap_id)
    if not handler:
        # Capability bekend maar geen handler: toon nette placeholder met info
        placeholder = match.get("placeholder_response") or (
            f"Ik kan **{match.get('naam') or cap_id}** herkennen ({match.get('status')}), "
            f"maar de uitvoering staat nog op de planning."
        )
        return {
            "type": "capability_placeholder",
            "capability_id": cap_id,
            "message": f"🤖 {placeholder}",
        }
    try:
        return handler(user_id)
    except Exception as ex:
        return {
            "type": "capability_error",
            "capability_id": cap_id,
            "message": f"Ik probeerde **{match.get('naam')}** uit te voeren maar er ging iets mis: {ex}",
        }
