"""v6_diep_memory_layers_001 — Cross-session memory + norm-matcher voor Diep.

Extra geheugen-lagen voor compose_response:

1. RECENT TOPICS — laatste 5 onderwerpen per user, OVER sessies heen
   Opgeslagen in data/users/{user_id}/recent_topics.json
   Spark kan zeggen "de laatste keer hadden we het over X, Y, Z"

2. NORM-MATCHER — bij elke Diep-call zoek 2-3 relevante normen/waarden uit
   spark_bijbel.json die fuzzy matchen met user-vraag. Inject in prompt zodat
   Spark contextueel een norm kan aanhalen i.p.v. willekeurig.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DATA = Path(__file__).parent.parent.parent / "data"

# Stopwoorden voor topic-extractie (uitgebreid)
TOPIC_STOP = {
    "ik", "je", "jij", "we", "wij", "het", "de", "een", "en", "of", "als",
    "is", "ben", "bent", "zijn", "was", "waren", "zou", "moet", "heeft",
    "ja", "nee", "ook", "niet", "naar", "maar", "met", "van", "voor", "die",
    "dat", "waar", "hoe", "wat", "wie", "wanneer", "waarom", "even",
    "kan", "wil", "wilde", "nu", "weer", "soms", "dan", "spark", "denk",
    "vind", "vond", "vraag", "vragen", "zeg", "zei", "ergens", "iets",
    "alles", "niks", "nog", "al", "ook", "echt", "wel", "geen", "even",
    "hier", "daar", "deze", "die", "dit", "dat", "zo", "veel", "weinig",
    "moeten", "kunnen", "willen", "hebben", "doen", "gaan", "komen", "maken",
    "krijgen", "zien", "weten", "vinden", "geven", "houden", "blijven",
    "vertel", "vertellen", "vertelt", "uitleg", "uitleggen", "kort", "even",
    "graag", "misschien", "eigenlijk", "leuk", "leuker", "interessant",
}


def _user_dir(user_id: str) -> Path:
    return DATA / "users" / user_id


# ─────────────────────────────────────────────────────────────────────────────
# RECENT TOPICS — cross-session memory per user
# ─────────────────────────────────────────────────────────────────────────────

def _recent_topics_path(user_id: str) -> Path:
    return _user_dir(user_id) / "recent_topics.json"


def load_recent_topics(user_id: str, max_n: int = 5) -> List[Dict]:
    """Lees laatste N topics voor deze user (over sessies heen)."""
    if not user_id:
        return []
    fp = _recent_topics_path(user_id)
    if not fp.exists():
        return []
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        topics = data.get("topics", [])
        return topics[:max_n]
    except Exception:
        return []


def record_topic(user_id: str, topic: str, session_id: Optional[str] = None) -> None:
    """Append een topic naar user's recent_topics (max 50 retained, top 5 zichtbaar).

    Dedupe: als topic in laatste 3 al voorkomt, alleen `last_seen` updaten.
    """
    if not user_id or not topic or len(topic) < 2:
        return
    topic = topic.strip().lower()
    if topic in TOPIC_STOP:
        return
    fp = _recent_topics_path(user_id)
    fp.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {"topics": []}
    except Exception:
        data = {"topics": []}
    topics: List[Dict] = data.get("topics", [])
    now = datetime.now(timezone.utc).isoformat()

    # Check of topic in laatste 3 al voorkomt → alleen last_seen updaten + count++
    for t in topics[:3]:
        if t.get("topic") == topic:
            t["last_seen"] = now
            t["count"] = int(t.get("count", 1)) + 1
            if session_id and session_id not in t.get("sessions", []):
                t.setdefault("sessions", []).append(session_id)
            data["topics"] = topics
            fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            return

    # Anders prepend
    new_entry = {
        "topic": topic,
        "first_seen": now,
        "last_seen": now,
        "count": 1,
        "sessions": [session_id] if session_id else [],
    }
    topics.insert(0, new_entry)
    # Cap retention op 50
    data["topics"] = topics[:50]
    fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def format_recent_topics_for_prompt(topics: List[Dict]) -> str:
    if not topics:
        return ""
    lines = ["## Laatste onderwerpen (cross-session, vorige gesprekken):"]
    for i, t in enumerate(topics[:5], 1):
        cnt = t.get("count", 1)
        ls = t.get("last_seen", "")
        ls_short = ls[:10] if ls else ""
        lines.append(f"  {i}. {t.get('topic','?')} (besproken {cnt}× — laatst {ls_short})")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# NORM-MATCHER — fuzzy match user-vraag met Spark bijbel-items
# ─────────────────────────────────────────────────────────────────────────────

def _load_bijbel() -> Optional[Dict]:
    fp = DATA / "personality" / "spark_bijbel.json"
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return None


def find_relevant_norms(user_text: str, max_n: int = 3) -> List[Dict]:
    """Zoek normen/waarden/items uit Spark-bijbel die match-en met user-vraag.

    Heuristiek: token-set-ratio van topic/item-tekst tegen user-text.
    Geeft top N met score ≥ 50%.
    """
    if not user_text:
        return []
    b = _load_bijbel()
    if not b:
        return []
    try:
        from rapidfuzz import fuzz
    except Exception:
        return []

    candidates: List[Dict] = []

    # Bijbel kernwaarden (typisch korte begrippen)
    for kw in (b.get("kernwaarden") or []):
        naam = kw.get("naam", "") if isinstance(kw, dict) else str(kw)
        omschrijving = kw.get("omschrijving", "") if isinstance(kw, dict) else ""
        haystack = f"{naam} {omschrijving}"
        if not haystack.strip():
            continue
        score = fuzz.token_set_ratio(haystack.lower(), user_text.lower())
        if score >= 50:
            candidates.append({
                "type": "kernwaarde",
                "naam": naam,
                "tekst": omschrijving or naam,
                "score": score,
            })

    # Bijbel normen
    for n in (b.get("normen") or []):
        naam = n.get("naam", "") if isinstance(n, dict) else str(n)
        omschrijving = n.get("omschrijving", "") if isinstance(n, dict) else ""
        haystack = f"{naam} {omschrijving}"
        if not haystack.strip():
            continue
        score = fuzz.token_set_ratio(haystack.lower(), user_text.lower())
        if score >= 50:
            candidates.append({
                "type": "norm",
                "naam": naam,
                "tekst": omschrijving or naam,
                "score": score,
            })

    # Bijbel-items (zinnen / principes)
    for item in (b.get("bijbel_items") or []):
        if isinstance(item, dict):
            tekst = item.get("tekst", "") or item.get("regel", "") or item.get("inhoud", "")
            naam = item.get("titel", "") or item.get("id", "")
        else:
            tekst = str(item)
            naam = ""
        if not tekst:
            continue
        score = fuzz.token_set_ratio(tekst.lower(), user_text.lower())
        if score >= 50:
            candidates.append({
                "type": "bijbel_item",
                "naam": naam or tekst[:30],
                "tekst": tekst,
                "score": score,
            })

    # Sorteer op score desc, top N
    candidates.sort(key=lambda x: -x["score"])
    return candidates[:max_n]


def format_norms_for_prompt(norms: List[Dict]) -> str:
    if not norms:
        return ""
    lines = ["## Relevante normen/waarden uit jouw Bijbel (pas waar toepasselijk toe):"]
    for n in norms:
        prefix = {"kernwaarde": "💎", "norm": "📐", "bijbel_item": "📖"}.get(n["type"], "•")
        lines.append(f"  {prefix} {n['naam']}: {n['tekst'][:200]}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: extract topic uit user_text (fallback voor recording als
# topic_tracker session-based niets vond)
# ─────────────────────────────────────────────────────────────────────────────

def extract_topic_from_text(user_text: str) -> Optional[str]:
    """Pak het zwaarst-wegende content-woord uit user-text."""
    if not user_text:
        return None
    words = re.findall(r"\b[a-zA-ZÀ-ÿ]{5,}\b", user_text.lower())
    # Filter stop
    words = [w for w in words if w not in TOPIC_STOP]
    if not words:
        return None
    # Frequency
    from collections import Counter
    c = Counter(words)
    return c.most_common(1)[0][0]
