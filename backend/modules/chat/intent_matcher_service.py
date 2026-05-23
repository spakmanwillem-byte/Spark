"""
v6_intent_matcher_001 — Layer 3 van "Spark's handen".

Doel: user-zin → capability_id match.
Leest patronen uit spark_capabilities.json (Layer 1).
Retourneert (capability_id, confidence, extracted_params).

Patroon van Willem (DSP-007):
  "kan jij [X]", "wil je voor mij [X]", "weet jij [X]", "heb ik [X]", "hoeveel [X]"

Strategie:
  - regex match op `triggers` lijst van elke capability
  - Highest scoring match wins (lengte van match als tie-breaker)
  - Geen LLM nodig — deterministisch, snel, log-baar
"""
import json
import re
from pathlib import Path
from typing import Optional, List, Dict

CAPS_FILE = Path(__file__).parent.parent.parent / "data" / "personality" / "spark_capabilities.json"


_cache = {"capabilities": None, "mtime": 0}


def _load_caps() -> List[Dict]:
    """Cache met file-mtime invalidation zodat hot-reload werkt."""
    try:
        m = CAPS_FILE.stat().st_mtime
        if _cache["capabilities"] is None or m != _cache["mtime"]:
            data = json.loads(CAPS_FILE.read_text())
            _cache["capabilities"] = data.get("capabilities", [])
            _cache["mtime"] = m
        return _cache["capabilities"]
    except Exception as ex:
        print(f"[intent_matcher] load failed: {ex}")
        return []


def match_capability(text: str) -> Optional[Dict]:
    """Match user-tekst tegen capability-triggers.

    Returns dict zoals:
      {
        "capability_id": "trade_logs_ophalen",
        "naam": "Trade-logs ophalen",
        "status": "live",
        "confidence": 0.85,
        "matched_trigger": "log van trade",
        "module": "trade/routes.py",
        "endpoint": "/api/trade/history/{user_id}",
        "placeholder_response": null,
      }
    of None als niets matcht.
    """
    if not text or not isinstance(text, str):
        return None

    t = text.lower().strip()
    # Strip leading "spark," "hey spark" etc.
    t = re.sub(r"^(hey |hoi |hallo )?spark[,!.]?\s*", "", t)

    best = None
    best_score = 0.0

    for cap in _load_caps():
        for trigger in cap.get("triggers", []):
            try:
                m = re.search(trigger, t, re.IGNORECASE)
                if not m:
                    continue
                # Score: lengte gematched / lengte input. Voorkeur voor specifieke matches.
                match_len = len(m.group(0))
                score = min(1.0, match_len / max(8, len(t)))
                # Boost als trigger meerdere woorden heeft (specifieker)
                if " " in trigger:
                    score += 0.15
                if score > best_score:
                    best_score = score
                    best = {
                        "capability_id": cap["id"],
                        "naam": cap.get("naam"),
                        "categorie": cap.get("categorie"),
                        "status": cap.get("status", "idea"),
                        "confidence": round(score, 2),
                        "matched_trigger": trigger,
                        "module": cap.get("module"),
                        "endpoint": cap.get("endpoint"),
                        "data_source": cap.get("data_source"),
                        "placeholder_response": cap.get("placeholder_response"),
                    }
            except re.error:
                continue

    return best


def all_capabilities(status: Optional[str] = None) -> List[Dict]:
    """Geef alle capabilities (optioneel gefilterd op status: live/placeholder/idea)."""
    caps = _load_caps()
    if status:
        return [c for c in caps if c.get("status") == status]
    return caps


def explain_self() -> Dict:
    """Wat kan Spark? — voor 'wat kan jij doen' vraag."""
    caps = _load_caps()
    by_cat: Dict[str, List[str]] = {}
    for c in caps:
        cat = c.get("categorie", "overig")
        if c.get("status") == "live":
            by_cat.setdefault(cat, []).append(c.get("naam", c["id"]))
    return {
        "live_count": sum(1 for c in caps if c.get("status") == "live"),
        "placeholder_count": sum(1 for c in caps if c.get("status") == "placeholder"),
        "idea_count": sum(1 for c in caps if c.get("status") == "idea"),
        "live_by_categorie": by_cat,
    }
