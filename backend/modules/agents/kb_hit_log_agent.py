"""
kb_hit_log_agent — Registreert welke KB-kaarten Spark gebruikt per chat-turn.

Willem 15-feb 2026 (v13_kb_hit_log_skeleton_001):
Op dit moment logt Spark chat-turns wel (chat_log_service) maar niet *welke
KB-kaarten* hij daarbij heeft aangeraakt. Zonder die koppeling kan je niet
zien welke kaarten dood-gewicht zijn, welke veel-gebruikte kaarten dringend
verrijking nodig hebben, en waar `ervaring_agent` zijn conclusies op baseert.

kb_hit_log is een dun append-only ledger op `data/chat_analytics/kb_hits.jsonl`.
Één regel per gebruikte kaart per turn. Nergens read-blocking — schrijven is
best-effort en mag falen zonder de chat-flow te breken.

Vaste positie in de architectuur:
- KB (weten/doen/…)   = definitie ("wat is X")
- kb_hit_log          = gebruik-ledger ("welke kaarten heb ik geraakt in turn Y?")
- ervaring_agent      = conclusie ("wat leerde ik uit die reeks turns?")
- personal_agent      = user-specifieke context ("wat weet ik van deze user")

TODO — nog niet ingevuld (skeleton):
- Hook plaatsen in `chat/response_composer.py` waar KB-kaarten worden gebruikt
  (smart_intents topic-overview, snap_service.lookup_word, sentence-match,
  compose-embeddings). Elke bron krijgt een eigen `match_source`-label.
- `retrieve()` implementeren (topN kaarten in tijdsvenster, per user of globaal).
- `stats_snapshot()` voor spark_pulse_agent.
- Rotate-strategie: elke 100k regels → gzipped archief.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)

LEDGER_DIR = Path(__file__).parent.parent.parent / "data" / "chat_analytics"
LEDGER = LEDGER_DIR / "kb_hits.jsonl"

# Bron-labels die we willen kunnen filteren in analytics.
KNOWN_MATCH_SOURCES = {
    "smart_intents_topic_overview",   # "welke kaarten heb je over X" — topic-batch
    "smart_intents_topic_expand",     # "vertel er meer over" — vervolg
    "snap_lookup_word",               # single-word lookup in snap_service
    "snap_sentence_match",            # fuzzy sentence-match in snap_service
    "compose_embed",                  # compose-laag pakt kaart voor context
    "capability_kbv2_search",         # /api/kb/v2/search directe hit
    "unknown",                        # fallback
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record(
    user_id: str,
    turn_id: Optional[str],
    kaart_ids: Iterable[str],
    match_source: str = "unknown",
    user_text_snippet: str = "",
    lade: Optional[str] = None,
    extra: Optional[Dict] = None,
) -> Dict:
    """Append één regel per geraakt kaart_id.

    Best-effort — faalt stil (returnt {ok: False}) zodat chat-flow doorloopt.
    Schrijft naar `data/chat_analytics/kb_hits.jsonl` in JSON-Lines format:
        {"ts": "...", "user_id": "...", "turn_id": "...", "kaart_id": "...",
         "match_source": "...", "snippet": "...", "lade": "...", "extra": {...}}
    """
    try:
        LEDGER_DIR.mkdir(parents=True, exist_ok=True)
        now = _now_iso()
        source = match_source if match_source in KNOWN_MATCH_SOURCES else "unknown"
        rows = 0
        with LEDGER.open("a", encoding="utf-8") as fh:
            for kid in kaart_ids:
                if not kid:
                    continue
                fh.write(json.dumps({
                    "ts": now,
                    "user_id": user_id,
                    "turn_id": turn_id,
                    "kaart_id": kid,
                    "match_source": source,
                    "snippet": (user_text_snippet or "")[:180],
                    "lade": lade,
                    "extra": extra or None,
                }, ensure_ascii=False) + "\n")
                rows += 1
        return {"ok": True, "rows_written": rows, "ledger": str(LEDGER)}
    except Exception as e:  # pragma: no cover
        logger.warning("[kb_hit_log] record faalde: %s", e)
        return {"ok": False, "error": str(e)}


def retrieve(
    user_id: Optional[str] = None,
    since_iso: Optional[str] = None,
    match_source: Optional[str] = None,
    limit: int = 200,
) -> List[Dict]:
    """Lees terug uit de ledger met eenvoudige filters.

    TODO:
    - Streaming lezen voor grote ledgers.
    - Aggregeren per kaart_id (frequency-table).
    - Time-window helpers (last_1h, last_24h, last_7d).
    """
    if not LEDGER.exists():
        return []
    rows: List[Dict] = []
    try:
        with LEDGER.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if user_id and r.get("user_id") != user_id:
                    continue
                if match_source and r.get("match_source") != match_source:
                    continue
                if since_iso and r.get("ts", "") < since_iso:
                    continue
                rows.append(r)
    except Exception as e:  # pragma: no cover
        logger.warning("[kb_hit_log] retrieve faalde: %s", e)
        return []
    return rows[-limit:] if limit else rows


def stats_snapshot() -> Dict:
    """Return snelle statistieken voor spark_pulse_agent / analytics.

    TODO:
    - Aantal regels totaal, laatste 24h, laatste 1h.
    - Top-10 meest-gebruikte kaarten, laatste 7 dagen.
    - Dead-weight-kaarten: kaarten in KB die 0× voorkomen in ledger over
      afgelopen 30 dagen.
    """
    if not LEDGER.exists():
        return {"exists": False, "rows": 0}
    try:
        # Simpele line-count zonder alles in memory te laden
        rows = 0
        with LEDGER.open("r", encoding="utf-8") as fh:
            for _ in fh:
                rows += 1
        return {"exists": True, "rows": rows, "path": str(LEDGER)}
    except Exception as e:  # pragma: no cover
        return {"exists": True, "error": str(e)}
