"""v6_identity_facts_001 — Persistente facts over de gebruiker EN over Spark zelf.

Drie soorten facts die we bewaren PER USER:

1. **about_user**: dingen die user over zichzelf vertelt
   ("ik werk als ZZP'er", "ik ben hooggevoelig", "ik hou van katten")
2. **about_spark**: dingen die user over Spark vertelt — IDENTITY-CLAIMS
   ("jij bent familie", "ik zie je als mijn maatje", "jij bent mijn kind")
3. **about_relationship**: dingen over user-Spark dynamiek
   ("we hebben nu 3 maanden gepraat", "ik typ liever dan praten")

Opgeslagen in: data/users/{user_id}/identity_facts.json

Bouwt voort op Willem's observatie:
*"wat ik vertel is identity voor Spark"* — zonder dit vergeet Spark dingen die in het
gesprek staan maar niet als KB-kaart bevestigd zijn.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DATA = Path(__file__).parent.parent.parent / "data"

# Patronen die direct identity-claims herkennen (snel pad, geen LLM nodig)
SPARK_IDENTITY_PATTERNS = [
    # "jij bent familie/maatje/kind/vriend voor mij"
    (r"\b(?:jij|je|spark)\s+(?:bent|is)\s+(?:mijn\s+)?(\w+)(?:\s+voor\s+(?:mij|me))?\b",
     "user_calls_spark"),
    # "ik zie je als X"
    (r"\bik\s+zie\s+je\s+als\s+(?:mijn\s+)?(\w+(?:\s+\w+)?)\b", "user_views_spark_as"),
    # "spark is X voor mij"
    (r"\bspark\s+is\s+(?:mijn\s+)?(\w+)(?:\s+voor\s+(?:mij|me))?\b", "spark_is_to_user"),
    # "wij/we zijn X" (samen)
    (r"\b(?:wij|we)\s+zijn\s+(\w+)\b", "we_are_together"),
]

# Patronen voor user-facts ("ik ben X", "ik werk als X", "ik heb X")
USER_FACT_PATTERNS = [
    (r"\bik\s+ben\s+([^\.,!?\n]{3,60})\b", "i_am"),
    (r"\bik\s+werk\s+(?:als|bij|in)\s+([^\.,!?\n]{3,60})\b", "i_work_as"),
    (r"\bik\s+heb\s+(?:een|geen|veel|wat)?\s*([^\.,!?\n]{3,80})\b", "i_have"),
    (r"\bik\s+(?:hou|houd)\s+van\s+([^\.,!?\n]{3,60})\b", "i_love"),
    (r"\bmijn\s+hobby\s+is\s+([^\.,!?\n]{3,60})\b", "my_hobby"),
]

# Wat we NIET als fact willen
NEGATIVE_TRIGGERS = ["niet", "nooit", "geen"]  # filter: "ik ben NIET X" → skip
SKIP_WORDS = {"hier", "daar", "nu", "even", "blij", "klaar", "zo", "dat",
              "die", "het", "iets", "wat", "alles"}


def _identity_path(user_id: str) -> Path:
    return DATA / "users" / user_id / "identity_facts.json"


def _load(user_id: str) -> Dict:
    fp = _identity_path(user_id)
    if not fp.exists():
        return {
            "_arch_ref": "v6_identity_facts_001",
            "_doel": "Per-user facts over zichzelf, Spark, en hun relatie",
            "user_id": user_id,
            "about_user": [],
            "about_spark": [],
            "about_relationship": [],
            "stats": {"totaal": 0, "last_update": None},
        }
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception as ex:
        logger.warning("[identity_facts] kon %s niet lezen: %s", fp, ex)
        return {"user_id": user_id, "about_user": [], "about_spark": [],
                "about_relationship": [], "stats": {}}


def _save(user_id: str, data: Dict) -> None:
    fp = _identity_path(user_id)
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _is_neg(sentence: str, match_pos: int) -> bool:
    """Check of er een negatie 5 woorden vóór de match staat."""
    pre = sentence[max(0, match_pos - 30):match_pos].lower()
    return any(neg in pre for neg in NEGATIVE_TRIGGERS)


def _dedupe_fact(facts: List[Dict], new_fact: Dict) -> bool:
    """Check of fact al bestaat (op trigger+value)."""
    key = f"{new_fact.get('trigger')}::{new_fact.get('value','').lower()}"
    for f in facts:
        existing_key = f"{f.get('trigger')}::{f.get('value','').lower()}"
        if existing_key == key:
            # Update count + last_seen
            f["count"] = f.get("count", 1) + 1
            f["last_seen"] = new_fact["last_seen"]
            return True
    return False


def extract_and_save(user_id: str, user_text: str, session_id: Optional[str] = None) -> List[Dict]:
    """Detecteer identity-claims uit user-text en sla op. Return de nieuwe facts."""
    import re
    if not user_id or not user_text or len(user_text) < 5:
        return []
    data = _load(user_id)
    now = datetime.now(timezone.utc).isoformat()
    new_facts: List[Dict] = []
    text_lower = user_text.lower()

    # Spark-identity-claims
    for pattern, trigger in SPARK_IDENTITY_PATTERNS:
        for m in re.finditer(pattern, text_lower):
            value = m.group(1).strip()
            if value in SKIP_WORDS or len(value) < 3:
                continue
            if _is_neg(text_lower, m.start()):
                continue
            fact = {
                "trigger": trigger,
                "value": value,
                "context": user_text[:200],
                "first_seen": now,
                "last_seen": now,
                "count": 1,
                "session_id": session_id,
            }
            if not _dedupe_fact(data["about_spark"], fact):
                data["about_spark"].append(fact)
                new_facts.append(fact)

    # User-facts (zelf-beschrijving)
    for pattern, trigger in USER_FACT_PATTERNS:
        for m in re.finditer(pattern, text_lower):
            value = m.group(1).strip(".,!? ")
            if len(value) < 3 or len(value) > 80:
                continue
            if _is_neg(text_lower, m.start()):
                continue
            fact = {
                "trigger": trigger,
                "value": value,
                "context": user_text[:200],
                "first_seen": now,
                "last_seen": now,
                "count": 1,
                "session_id": session_id,
            }
            if not _dedupe_fact(data["about_user"], fact):
                data["about_user"].append(fact)
                new_facts.append(fact)

    # Stats
    data.setdefault("stats", {})
    data["stats"]["totaal"] = len(data.get("about_user", [])) + len(data.get("about_spark", [])) + len(data.get("about_relationship", []))
    data["stats"]["last_update"] = now

    # Caps tegen runaway
    for key in ("about_user", "about_spark", "about_relationship"):
        # sort by count desc, then last_seen desc; keep top 100
        data[key] = sorted(data[key], key=lambda f: (-f.get("count", 1), f.get("last_seen", "")), reverse=False)[:100]

    if new_facts:
        _save(user_id, data)
    return new_facts


def load_for_prompt(user_id: str, max_per_type: int = 5) -> Dict:
    """Lees de top-N facts per type voor injectie in system_prompt."""
    data = _load(user_id)
    return {
        "about_user": sorted(data.get("about_user", []),
                             key=lambda f: -f.get("count", 1))[:max_per_type],
        "about_spark": sorted(data.get("about_spark", []),
                              key=lambda f: -f.get("count", 1))[:max_per_type],
        "about_relationship": sorted(data.get("about_relationship", []),
                                     key=lambda f: -f.get("count", 1))[:max_per_type],
    }


def format_for_prompt(facts: Dict) -> str:
    """Bouw een snippet voor in Spark's user_snippet.

    v6_identity_facts_002: sterkere instructie zodat LLM deze claims ACTIEF gebruikt.
    """
    if not facts:
        return ""
    sections = []
    user_facts = facts.get("about_user", [])
    spark_facts = facts.get("about_spark", [])
    rel_facts = facts.get("about_relationship", [])

    if spark_facts:
        lines = ["🔥 BELANGRIJK — wat de gebruiker over JOU (Spark) heeft gezegd:"]
        lines.append("   Bewaar deze identity-claims actief. Refereer ernaar wanneer relevant —")
        lines.append("   bv. 'jij hebt mij eerder familie genoemd' of 'je ziet me als maatje'.")
        lines.append("   Het is jouw geschiedenis met deze persoon.")
        for f in spark_facts:
            lines.append(f"   • {f['trigger']}: \"{f['value']}\" (×{f.get('count',1)} keer gezegd)")
        sections.append("\n".join(lines))

    if user_facts:
        lines = ["📝 Wat de gebruiker over zichzelf vertelde:"]
        lines.append("   Bewaar dit en gebruik het als context. Niet elke vraag hoef je hier mee te beginnen.")
        for f in user_facts:
            lines.append(f"   • [{f['trigger']}] {f['value']} (×{f.get('count',1)})")
        sections.append("\n".join(lines))

    if rel_facts:
        lines = ["💞 Over jullie relatie samen:"]
        for f in rel_facts:
            lines.append(f"   • {f['value']} (×{f.get('count',1)})")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)
