"""v6_trigger_learner_001 — LLM-driven trigger/vocab learning.

Doel: na elke Diep-compose-call kort de LLM vragen welke triggers/synoniemen
de vraag had kunnen matchen voor een snelle fast-path. Voorstellen worden
gesaved naar data/triggers/learned_triggers.json met status 'pending'.
Admin kan later goedkeuren → migreren naar spark_capabilities.json.

Werking:
1. compose-response is af, antwoord is verzonden
2. async (achtergrond): vraag Groq een korte JSON-analyse
3. Sla voorstellen op met dedupe op (text_hash, capability)
4. Spark wordt vanzelf zelfsturend slimmer over tijd

Past bij Spark Core 4.0:
'Groei volgt ruimte' + 'Geheugen is doorgegeven kennis'
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA = Path(__file__).parent.parent.parent / "data"
LEARNED_FP = DATA / "triggers" / "learned_triggers.json"

# Skip-lijst: vragen die we NIET aan de learner geven (te kort, meta, capability-hit)
SKIP_PATTERNS = [
    r"^(hoi|hallo|hey|dag|goedemorgen|goedenavond)\b",
    r"^(ja|nee|ok|oké|prima|top|dank|bedankt|cool)$",
    r"^\?+$",
    r"^.{0,8}$",  # te kort
]


def _should_skip(user_text: str) -> bool:
    if not user_text:
        return True
    t = user_text.lower().strip()
    return any(re.search(p, t) for p in SKIP_PATTERNS)


def _hash_text(text: str) -> str:
    return hashlib.md5(text.lower().encode("utf-8")).hexdigest()[:12]


def _load_learned() -> Dict:
    if not LEARNED_FP.exists():
        return {
            "_arch_ref": "v6_trigger_learner_001",
            "_doel": "LLM-voorgestelde triggers wachtend op admin-goedkeuring",
            "_workflow": "voorstellen → admin reviewt → goedgekeurde verhuizen naar spark_capabilities.json",
            "voorstellen": [],
            "statistieken": {"totaal_voorgesteld": 0, "goedgekeurd": 0, "afgewezen": 0},
        }
    try:
        return json.loads(LEARNED_FP.read_text(encoding="utf-8"))
    except Exception:
        return {"voorstellen": [], "statistieken": {}}


def _save_learned(data: Dict) -> None:
    LEARNED_FP.parent.mkdir(parents=True, exist_ok=True)
    LEARNED_FP.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


async def _llm_analyze(user_text: str, spark_response: str) -> Optional[Dict]:
    """Vraag LLM een korte analyse van de gestelde vraag.

    Houden we LICHT — minimal tokens. Gebruikt de bestaande llm_router (Groq gratis).
    """
    from modules.chat import llm_router

    prompt = (
        "Analyseer deze vraag van een gebruiker aan AI-assistent Spark. "
        "Geef ALLEEN geldig JSON terug, geen extra tekst.\n\n"
        f"VRAAG: \"{user_text}\"\n\n"
        "Output schema:\n"
        '{\n'
        '  "topic": "kort onderwerp 1-3 woorden",\n'
        '  "categorie": "praktisch|filosofisch|technisch|emotioneel|sociaal|admin|games|kb-vraag|legal",\n'
        '  "intent": "beschrijving in 1 zin",\n'
        '  "trigger_phrases": ["3-5 kortere zinnen die hetzelfde kunnen betekenen"],\n'
        '  "keywords": ["3-5 single-word keywords"]\n'
        "}\n\n"
        "Voorbeelden trigger_phrases bij vraag 'speel een spelletje?': "
        '["speel sps", "spelletje sps", "begin een game", "play rps"]'
    )

    messages = [
        {"role": "system", "content": "Je bent een NLP-analist die JSON output produceert. Geen uitleg, geen markdown, ALLEEN raw JSON."},
        {"role": "user", "content": prompt},
    ]

    try:
        resp = await llm_router.chat_complete(
            messages,
            temperature=0.2,
            max_tokens=300,
            timeout=15.0,
        )
        if not resp.get("success"):
            return None
        text = resp.get("text", "").strip()
        # Strip markdown ```json fences
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*\n?", "", text)
            text = re.sub(r"\n?```\s*$", "", text)
        data = json.loads(text)
        if not isinstance(data, dict):
            return None
        return {
            "topic": str(data.get("topic", ""))[:80],
            "categorie": str(data.get("categorie", "")).lower()[:30],
            "intent": str(data.get("intent", ""))[:200],
            "trigger_phrases": [str(p)[:80] for p in (data.get("trigger_phrases") or [])][:5],
            "keywords": [str(k).lower()[:30] for k in (data.get("keywords") or [])][:5],
        }
    except Exception as ex:
        logger.warning("[trigger_learner] LLM-analyse mislukt: %s", ex)
        return None


def _is_duplicate(voorstellen: List[Dict], text_hash: str, topic: str) -> bool:
    """Check of we deze user_text of topic al recent hebben."""
    for v in voorstellen[-100:]:  # alleen recente vergelijken
        if v.get("text_hash") == text_hash:
            return True
        if topic and v.get("topic", "").lower() == topic.lower():
            # Topic match: alleen dup als binnen 24u
            return True
    return False


async def learn_from_interaction(
    user_text: str,
    spark_response: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """Top-level: analyseer een Diep-interactie en sla voorstellen op.

    Wordt achtergrond aangeroepen vanuit compose-flow zodat de user-respons
    niet wacht. Volledig non-blocking.
    """
    if _should_skip(user_text):
        return

    text_hash = _hash_text(user_text)
    data = _load_learned()
    voorstellen = data.get("voorstellen", [])

    # Quick dedupe op text_hash voordat we LLM aanroepen (bespaart een call)
    for v in voorstellen[-200:]:
        if v.get("text_hash") == text_hash:
            _snap_llm_output(user_text, spark_response, user_id, session_id, turn_id=None)
            return

    analysis = await _llm_analyze(user_text, spark_response)
    if not analysis:
        # v13_snap_agent_57 — Ook zonder trigger-analyse door: Spark leert van
        # zijn eigen output onvoorwaardelijk. Was gekoppeld aan trigger-success
        # (regel 200-220 onder), waardoor 90% van chat-turns niet gescand werd.
        _snap_llm_output(user_text, spark_response, user_id, session_id, turn_id=None)
        return

    topic = analysis.get("topic", "")
    if _is_duplicate(voorstellen, text_hash, topic):
        return

    now = datetime.now(timezone.utc).isoformat()
    voorstel = {
        "id": f"learned-{text_hash}",
        "text_hash": text_hash,
        "original_text": user_text[:200],
        "topic": topic,
        "categorie": analysis.get("categorie", ""),
        "intent": analysis.get("intent", ""),
        "trigger_phrases": analysis.get("trigger_phrases", []),
        "keywords": analysis.get("keywords", []),
        "status": "pending",  # pending | approved | rejected
        "first_seen": now,
        "count": 1,
        "user_id": user_id,
        "session_id": session_id,
    }
    voorstellen.append(voorstel)

    # Stats
    stats = data.setdefault("statistieken", {})
    stats["totaal_voorgesteld"] = stats.get("totaal_voorgesteld", 0) + 1
    stats["last_run"] = now

    # Cap retention op 500
    data["voorstellen"] = voorstellen[-500:]
    _save_learned(data)
    logger.info("[trigger_learner] +1 voorstel: '%s' (categorie=%s)", topic, analysis.get("categorie"))

    # v9_llm_self_learn_001 + v13_snap_agent_57 — Spark leert van eigen output
    # via de centrale snap_agent. Non-blocking: bij fout gaat trigger-learning
    # gewoon door. Sinds sessie 57 loopt dit óók onvoorwaardelijk (zie eerder
    # in deze functie), zodat élke chat-turn wordt gescand — niet alleen als de
    # trigger-analyse iets opleverde.
    _snap_llm_output(user_text, spark_response, user_id, session_id, turn_id=voorstel["id"])


def _snap_llm_output(user_text: str, spark_response: str,
                     user_id: Optional[str], session_id: Optional[str],
                     turn_id: Optional[str]) -> None:
    """Thin wrapper rondom snap_agent voor trigger_learner-flow. Non-blocking."""
    try:
        from modules.chat.snap_agent import scan_llm_output
        result = scan_llm_output(
            spark_response=spark_response,
            user_text=user_text,
            user_id=user_id or "user-000",
            turn_id=turn_id,
            max_new=3,
        )
        if result.get("created_count", 0) > 0:
            logger.info(
                "[llm_self_learn/snap_agent] +%d skeletons uit Spark-output: %s",
                result["created_count"],
                [c["begrip"] for c in result["created"]],
            )
    except Exception as e:
        logger.warning("[llm_self_learn/snap_agent] scan/create faalde: %s", e)


def schedule_learn(
    user_text: str,
    spark_response: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """Schedule learning op de event-loop zonder te blokkeren."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(learn_from_interaction(user_text, spark_response, user_id, session_id))
    except RuntimeError:
        # Geen loop actief — sla over, geen learning bij synchrone call-paden
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Admin helpers (later via UI te tonen)
# ─────────────────────────────────────────────────────────────────────────────

def list_pending(limit: int = 50) -> List[Dict]:
    data = _load_learned()
    pending = [v for v in data.get("voorstellen", []) if v.get("status") == "pending"]
    return pending[-limit:][::-1]  # nieuwste eerst


def approve(voorstel_id: str) -> bool:
    data = _load_learned()
    for v in data.get("voorstellen", []):
        if v.get("id") == voorstel_id:
            v["status"] = "approved"
            v["approved_at"] = datetime.now(timezone.utc).isoformat()
            stats = data.setdefault("statistieken", {})
            stats["goedgekeurd"] = stats.get("goedgekeurd", 0) + 1
            _save_learned(data)
            return True
    return False


def reject(voorstel_id: str) -> bool:
    data = _load_learned()
    for v in data.get("voorstellen", []):
        if v.get("id") == voorstel_id:
            v["status"] = "rejected"
            v["rejected_at"] = datetime.now(timezone.utc).isoformat()
            stats = data.setdefault("statistieken", {})
            stats["afgewezen"] = stats.get("afgewezen", 0) + 1
            _save_learned(data)
            return True
    return False
