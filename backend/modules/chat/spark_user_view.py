"""v6_spark_user_view_001 — Spark's perspectief op de gebruiker.

GEEN nieuwe opslag — alleen aggregatie van bestaande bronnen:
  - data/persons/{user_id}_relationships.json (familieleden/vrienden)
  - data/users/{user_id}/behavior.json (gedrag)
  - data/users/{user_id}/_meta.json (user metadata)
  - data/chat/logs/{*user_id*}.json (recente thema's via begrippen)
  - data/auth/users.json (naam, gradatie)

Output: compact profiel-snippet voor inject in compose system_prompt:
  "Je praat met Willem (gradatie 6). Hij vroeg deze week vaak over: architectuur, KB,
   bewustzijn. Familie: dochter Anna. Tonality-voorkeur: kort, warm, geen vleierij."
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter

DATA = Path(__file__).parent.parent.parent / "data"


def _safe_load(fp: Path, default):
    if not fp.exists():
        return default
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return default


def _get_user_meta(user_id: str) -> Dict:
    """Naam + gradatie uit auth/users."""
    auth = _safe_load(DATA / "auth" / "users.json", {"users": []})
    users = auth.get("users") or auth.get("entries") or []
    for u in users:
        if u.get("id") == user_id or u.get("user_id") == user_id:
            return {
                "naam": u.get("naam") or u.get("name") or "?",
                "gradatie": u.get("gradatie") or u.get("grade") or 2,
            }
    # Fallback uit users-dir _meta
    meta = _safe_load(DATA / "users" / user_id / "_meta.json", {})
    return {
        "naam": meta.get("naam") or user_id,
        "gradatie": meta.get("gradatie") or 2,
    }


def _get_relationships(user_id: str, max_items: int = 5) -> List[Dict]:
    """Familie/vrienden uit relation_extraction_service output."""
    d = _safe_load(DATA / "persons" / f"{user_id}_relationships.json", {"relationships": []})
    rels = d.get("relationships") or []
    return rels[:max_items]


def _get_recent_themes(user_id: str, max_themes: int = 5) -> List[str]:
    """Pak laatste sessie-files met user_id en tel onderwerpen."""
    logs_dir = DATA / "chat" / "logs"
    if not logs_dir.exists():
        return []
    word_counts: Counter = Counter()
    skip_words = {"ik", "je", "de", "het", "een", "en", "is", "ja", "nee", "wat", "hoe",
                  "voor", "met", "van", "die", "dat", "ook", "niet", "naar", "maar",
                  "als", "kan", "wil", "nu", "even", "weer", "soms", "dan", "spark"}
    # Loop over alle log-files; filter op user_id in messages
    for fp in logs_dir.glob("*.json"):
        d = _safe_load(fp, {"messages": []})
        for m in (d.get("messages") or [])[-30:]:
            if m.get("user_id") and m.get("user_id") != user_id:
                continue
            if m.get("role") != "user":
                continue
            text = (m.get("text") or m.get("message") or "").lower()
            for w in text.split():
                w = w.strip(".,?!:;'\"()")
                if len(w) >= 5 and w not in skip_words and not w.isdigit():
                    word_counts[w] += 1
    return [w for w, _ in word_counts.most_common(max_themes)]


def _get_behavior(user_id: str) -> Dict:
    """Gedrag-info indien aanwezig."""
    return _safe_load(DATA / "users" / user_id / "behavior.json", {})


def build_user_profile(user_id: str) -> Dict:
    """Hoofdfunctie: aggregeer bestaande user-data tot compact profiel."""
    meta = _get_user_meta(user_id)
    rels = _get_relationships(user_id)
    themes = _get_recent_themes(user_id)
    behavior = _get_behavior(user_id)
    return {
        "user_id": user_id,
        "naam": meta["naam"],
        "gradatie": meta["gradatie"],
        "relaties": rels,
        "recente_themes": themes,
        "behavior": behavior,
    }


def format_for_system_prompt(profile: Dict) -> str:
    """Bouw een korte profielregel voor in Spark's system_prompt."""
    parts = []
    naam = profile.get("naam", "?")
    grad = profile.get("gradatie", 2)
    parts.append(f"Je praat met **{naam}** (gradatie {grad}).")

    themes = profile.get("recente_themes") or []
    if themes:
        parts.append(f"Recente gesprekstemas: {', '.join(themes[:5])}.")

    rels = profile.get("relaties") or []
    if rels:
        rel_str = ", ".join(
            f"{r.get('person_name','?')} ({r.get('relation_type','relatie')})"
            for r in rels[:3]
        )
        parts.append(f"Bekenden van {naam}: {rel_str}.")

    # Privacy-filter op gradatie
    if grad < 4:
        parts.append("(Gradatie-niveau laag: deel geen privé-info terug.)")

    return " ".join(parts)
