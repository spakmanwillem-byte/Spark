"""
Lite Card Factory (v9_llm_self_learn_001)
=========================================
Creëert "lite" (skeleton) KB v2 inbox-kaarten met VOLLEDIGE metadata via
het bestaande footnote-systeem. Zorgt dat elke auto-extract herleidbaar
is naar bron (llm_output_scanner + turn_id + timestamp).

Filosofie: geen fantoom-kaarten — elke lite-kaart heeft een blueprint-link
en source-tag die Willem kan auditen via `GET /api/kb/v2/inbox`.

Klein: alleen kaart-creatie, geen scan (die zit in llm_output_scanner).
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from modules.kb_v2 import service as kb_service


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_lite_card_from_llm(
    begrip: str,
    context_snippet: str,
    count_in_spark: int,
    turn_id: Optional[str] = None,
    user_id: str = "user-000",
) -> Dict[str, Any]:
    """Maak een lite-kaart in inbox met footnote-metadata.

    Args:
        begrip: kandidaat-woord uit Spark's antwoord.
        context_snippet: tekstsnippet rondom eerste voorkomen.
        count_in_spark: hoeveel keer Spark dit woord noemde.
        turn_id: chat-turn ID van herkomst (indien beschikbaar).
        user_id: eigenaar (default Spark = user-000).

    Returns:
        Result van kb_service.add_to_inbox() + verrijking met footnote.
    """
    r = kb_service.add_to_inbox(begrip=begrip, source="llm_auto_extract", user_id=user_id)
    if not r or not r.get("success"):
        return r or {"success": False, "error": "add_to_inbox faalde"}

    # Verrijk kaart met footnote-metadata (herbruik bestaande footnote-veld)
    try:
        kaart_id = (r.get("kaart") or {}).get("id")
        if kaart_id:
            _stamp_footnote(
                kaart_id=kaart_id,
                footnote={
                    "llm_generated": True,
                    "llm_lite": True,  # markeer als skeleton/lite
                    "extract_source": "spark_llm_output_scanner_v1",
                    "extract_turn_id": turn_id,
                    "extract_at": _now_iso(),
                    "extract_context_snippet": context_snippet[:200],
                    "extract_count_in_spark": count_in_spark,
                    "extract_note": (
                        f"Spark noemde '{begrip}' {count_in_spark}× in eigen LLM-antwoord "
                        f"maar het staat nog niet in KB. Skeleton-kaart, invulling nog nodig."
                    ),
                    "needs_review": True,
                },
            )
    except Exception as e:
        r["footnote_stamp_error"] = str(e)
    r["is_lite"] = True
    return r


def _stamp_footnote(kaart_id: str, footnote: Dict[str, Any]) -> None:
    """Schrijf footnote-velden op een inbox-kaart. Herbruikt bestaande footnote-conventie."""
    from pathlib import Path
    from modules.core.storage import load_json, save_json
    # Same file als kb_v2.service._inbox_path() → knowledge_inbox.json (niet inbox.json!)
    inbox_path = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2" / "knowledge_inbox.json"
    data = load_json(inbox_path) or {"kaarten": []}
    for k in data.get("kaarten", []):
        if k.get("id") == kaart_id:
            k.setdefault("footnote", {})
            k["footnote"].update(footnote)
            k.setdefault("status", {})["last_touched"] = _now_iso()
            break
    save_json(inbox_path, data)


def batch_create_from_scan(
    candidates: List[Dict[str, Any]],
    turn_id: Optional[str] = None,
    user_id: str = "user-000",
    max_per_turn: int = 3,
) -> Dict[str, Any]:
    """Maakt maximaal N lite-kaarten per chat-turn (voorkomt inbox-flood).

    Returns:
        {"created": [...], "skipped_existing": N, "skipped_over_limit": N}
    """
    created: List[Dict[str, Any]] = []
    skipped_existing = 0
    for c in candidates[:max_per_turn]:
        r = create_lite_card_from_llm(
            begrip=c["begrip"],
            context_snippet=c.get("context_snippet", ""),
            count_in_spark=c.get("count_in_spark", 1),
            turn_id=turn_id,
            user_id=user_id,
        )
        if r.get("success"):
            if r.get("existing"):
                skipped_existing += 1
            else:
                created.append({
                    "begrip": c["begrip"],
                    "kaart_id": (r.get("kaart") or {}).get("id"),
                    "is_lite": True,
                })
    return {
        "created": created,
        "created_count": len(created),
        "skipped_existing": skipped_existing,
        "skipped_over_limit": max(0, len(candidates) - max_per_turn),
    }
