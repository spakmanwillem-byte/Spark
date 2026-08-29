"""
snap_agent — Centraal ingangspunt voor onbekend-woord-detectie (v13_snap_agent_57).

Willem 28-feb 2026: 5 losse plekken schreven skeletons naar de KB inbox
(trigger_learner, chat/routes, lite_card_factory, text_importer, orphan_tag_scanner).
Deze agent bundelt drie scan-flows achter één API zodat:
- rate-limits, footnote-verrijking, fuzzy-fallback en dedupe op één plek zitten;
- Spark kan later hooks op dit centrale punt hangen (self-repair bij homoniem,
  reconcile bij drift, learning signals);
- de KB krijgt consistent aangevulde metadata (bron, herkomst_turn_id, snippet).

Deze module is thin: hij delegeert de daadwerkelijke lookup aan bestaande utils
(`llm_output_scanner`, `snap_service` waar aanwezig) en het schrijven aan
`kb_v2.service.add_to_inbox`. Puur, geen route-registratie.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from modules.kb_v2 import service as kb_service

logger = logging.getLogger(__name__)

# v13_snap_agent_57 — rate-limit tegen inbox-explosie: max N kaarten per user
# per uur die uit AUTOMATISCHE scans komen. Handmatige adds omzeilen dit.
_RATE_LIMIT_PER_HOUR = 30
_rate_state: Dict[str, List[float]] = {}


def _within_rate_limit(user_id: str) -> bool:
    now = time.time()
    hist = [t for t in _rate_state.get(user_id, []) if now - t < 3600]
    _rate_state[user_id] = hist
    return len(hist) < _RATE_LIMIT_PER_HOUR


def _tick_rate(user_id: str) -> None:
    _rate_state.setdefault(user_id, []).append(time.time())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def scan_llm_output(
    spark_response: str,
    user_text: str = "",
    user_id: str = "user-000",
    turn_id: Optional[str] = None,
    max_new: int = 3,
) -> Dict:
    """Scan Spark's LLM-antwoord en creëer skeletons voor onbekende woorden.

    Bestaande utility `llm_output_scanner.scan_spark_response` doet de detectie;
    deze agent voegt de verrijking en het rate-limit toe.
    """
    if not spark_response or len(spark_response) < 30:
        return {"created": [], "skipped_reason": "response_too_short"}

    try:
        from modules.chat.llm_output_scanner import scan_spark_response
    except Exception as e:  # pragma: no cover
        return {"created": [], "error": f"scanner_unavailable:{e}"}

    candidates = scan_spark_response(spark_response, user_text=user_text, top_n=max_new * 2)
    if not candidates:
        return {"created": [], "skipped_reason": "no_candidates"}

    return _enrich_and_create(
        candidates=candidates[:max_new],
        source="llm_auto_extract",
        user_id=user_id,
        turn_id=turn_id,
        origin="spark_llm_output",
    )


def scan_user_input(
    user_text: str,
    user_id: str = "user-000",
    turn_id: Optional[str] = None,
    max_new: int = 3,
) -> Dict:
    """Scan user-input op onbekende woorden en creëer skeletons.

    Bestaande route in `chat/routes.py:2045` gebruikt `snap_service` — deze agent
    is de canonieke wrapper voor toekomstige aanroepen.
    """
    if not user_text or len(user_text) < 4:
        return {"created": [], "skipped_reason": "input_too_short"}
    try:
        from modules.chat.llm_output_scanner import scan_spark_response
    except Exception as e:  # pragma: no cover
        return {"created": [], "error": f"scanner_unavailable:{e}"}

    # Hergebruik dezelfde tokenizer: scan_spark_response filtert stopwoorden en
    # bekende KB-begrippen. Voor user-input is er geen "user_text" om weg te
    # filteren — we geven lege string zodat alle onbekende woorden kandidaat zijn.
    candidates = scan_spark_response(user_text, user_text="", top_n=max_new * 2)
    if not candidates:
        return {"created": [], "skipped_reason": "no_candidates"}

    return _enrich_and_create(
        candidates=candidates[:max_new],
        source="user_input_snap",
        user_id=user_id,
        turn_id=turn_id,
        origin="user_chat_input",
    )


def _enrich_and_create(
    candidates: List[Dict],
    source: str,
    user_id: str,
    turn_id: Optional[str],
    origin: str,
) -> Dict:
    """Voeg footnote-metadata toe en creëer skeletons in de inbox.

    Rate-limit per user; harde dedupe via kb_service.add_to_inbox (deep-scan
    over 4 lades, auto-repair van index bij stale entry — v13_kbv2_inbox_dedupe_002).
    """
    if not _within_rate_limit(user_id):
        return {"created": [], "skipped_reason": "rate_limit_hit", "rate_limit": _RATE_LIMIT_PER_HOUR}

    created: List[Dict] = []
    skipped: List[Dict] = []
    now = _now_iso()

    for cand in candidates:
        begrip = (cand.get("begrip") or "").strip()
        if not begrip:
            continue
        _tick_rate(user_id)
        # kb_service.add_to_inbox doet zelf: index-check + deep-scan alle lades +
        # auto-repair (v13_kbv2_inbox_dedupe_002). Wij muteren daarna de footnote.
        r = kb_service.add_to_inbox(begrip=begrip, source=source, user_id=user_id)
        if not r.get("success"):
            skipped.append({"begrip": begrip, "reason": r.get("message", "add_failed")})
            continue
        kaart = r.get("kaart") or {}
        if r.get("existing"):
            skipped.append({"begrip": begrip, "reason": "already_exists", "lade": r.get("lade")})
            continue
        # Verrijk footnote in-place via kb_service.edit_card (indien beschikbaar)
        _enrich_footnote(
            kaart_id=kaart.get("id"),
            snippet=cand.get("context_snippet", ""),
            turn_id=turn_id,
            origin=origin,
            llm_count=cand.get("count_in_spark", 1),
            now=now,
        )
        created.append({
            "id": kaart.get("id"),
            "begrip": begrip,
            "source": source,
            "origin": origin,
        })

    logger.info(
        "[snap_agent] source=%s created=%d skipped=%d user=%s",
        source, len(created), len(skipped), user_id,
    )
    return {"created": created, "skipped": skipped, "created_count": len(created)}


def _enrich_footnote(kaart_id: Optional[str], snippet: str, turn_id: Optional[str],
                     origin: str, llm_count: int, now: str) -> None:
    """Verrijk kaart footnote met snap_agent metadata."""
    if not kaart_id:
        return
    try:
        # Direct file-mutatie via kb_service internals — geen public edit_card die
        # footnote-only accepteert. Doe het via het inbox-bestand.
        from modules.core.storage import load_json, save_json
        from pathlib import Path
        inbox_path = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2" / "knowledge_inbox.json"
        data = load_json(inbox_path, default={"kaarten": []})
        for k in data.get("kaarten", []):
            if k.get("id") == kaart_id:
                fn = k.setdefault("footnote", {})
                fn["aangemaakt_door"] = "snap_agent"
                fn["aangemaakt_op"] = now
                fn["origin"] = origin
                if turn_id:
                    fn["herkomst_turn_id"] = turn_id
                if snippet:
                    fn["context_snippet"] = snippet[:240]
                if llm_count:
                    fn["llm_count"] = llm_count
                break
        save_json(inbox_path, data)
    except Exception as e:  # pragma: no cover
        logger.warning("[snap_agent] footnote-enrich faalde voor %s: %s", kaart_id, e)


def seed_self_awareness_cards() -> Dict:
    """Eénmalige seed: skeletons voor Spark's eigen modules zodat de KB kan
    reflecteren op de eigen infrastructuur. Idempotent — bestaande kaarten
    worden niet overschreven (via add_to_inbox deep-scan).
    """
    modules = [
        "snap_agent",
        "llm_output_scanner",
        "trigger_learner",
        "lite_card_factory",
        "snap_service",
        "text_importer",
        "tag_sanitizer",
        "kb_v2",
    ]
    results = []
    for name in modules:
        r = kb_service.add_to_inbox(
            begrip=name,
            source="spark_self_awareness",
            user_id="user-000",
        )
        results.append({
            "module": name,
            "created": not r.get("existing"),
            "kaart_id": (r.get("kaart") or {}).get("id"),
            "existing_lade": r.get("lade") if r.get("existing") else None,
        })
    return {"seeded": results, "count": len(results)}
