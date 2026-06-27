"""
v6_intent_matcher_001 (blueprint-driven sinds v6_intent_matcher_blueprint_001) — Layer 3 van "Spark's handen".

Doel: user-zin → capability_id match.
Leest patronen uit spark_capabilities.json (Layer 1).
Retourneert (capability_id, confidence, extracted_params).

Configuratie: modules/chat/blueprints/intent_matcher.json
  - paths.caps_fp                         : spark_capabilities.json locatie
  - preprocessing.strip_prefix_regex      : verwijder "hey spark," etc.
  - scoring.min_input_len_divider         : voorkomt deling door 0 bij korte input
  - scoring.multiword_trigger_boost       : boost voor specifiekere triggers
  - status_levels.*                       : welke statussen we kennen
"""
import json
import re
from pathlib import Path
from typing import Optional, List, Dict

from modules.core.blueprint import load_blueprint_cached


def _bp() -> Dict:
    return load_blueprint_cached("chat", "intent_matcher")


_cache = {"capabilities": None, "mtime": 0}


def _load_caps() -> List[Dict]:
    """Cache met file-mtime invalidation zodat hot-reload werkt."""
    try:
        caps_fp = Path(_bp()["paths"]["caps_fp"])
        m = caps_fp.stat().st_mtime
        if _cache["capabilities"] is None or m != _cache["mtime"]:
            data = json.loads(caps_fp.read_text())
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

    bp = _bp()
    pre = bp["preprocessing"]
    sc = bp["scoring"]
    levels = bp["status_levels"]

    t = text
    if pre.get("lowercase", True):
        t = t.lower()
    if pre.get("strip_whitespace", True):
        t = t.strip()
    strip_re = pre.get("strip_prefix_regex")
    if strip_re:
        t = re.sub(strip_re, "", t)

    best = None
    best_score = 0.0
    min_div = sc.get("min_input_len_divider", 8)
    boost = sc.get("multiword_trigger_boost", 0.15)
    max_sc = sc.get("max_score", 1.0)
    dec = sc.get("confidence_decimals", 2)

    for cap in _load_caps():
        for trigger in cap.get("triggers", []):
            try:
                m = re.search(trigger, t, re.IGNORECASE)
                if not m:
                    continue
                # Score: lengte gematched / lengte input. Voorkeur voor specifieke matches.
                match_len = len(m.group(0))
                score = min(max_sc, match_len / max(min_div, len(t)))
                # Boost als trigger meerdere woorden heeft (specifieker)
                if " " in trigger:
                    score += boost
                if score > best_score:
                    best_score = score
                    best = {
                        "capability_id": cap["id"],
                        "naam": cap.get("naam"),
                        "categorie": cap.get("categorie"),
                        "status": cap.get("status", levels.get("default_when_missing", "idea")),
                        "confidence": round(score, dec),
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
    levels = _bp()["status_levels"]
    caps = _load_caps()
    by_cat: Dict[str, List[str]] = {}
    for c in caps:
        cat = c.get("categorie", "overig")
        if c.get("status") == levels["live"]:
            by_cat.setdefault(cat, []).append(c.get("naam", c["id"]))
    return {
        "live_count": sum(1 for c in caps if c.get("status") == levels["live"]),
        "placeholder_count": sum(1 for c in caps if c.get("status") == levels["placeholder"]),
        "idea_count": sum(1 for c in caps if c.get("status") == levels["idea"]),
        "live_by_categorie": by_cat,
    }
