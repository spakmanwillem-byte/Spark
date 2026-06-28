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
import logging
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter

DATA = Path(__file__).parent.parent.parent / "data"
logger = logging.getLogger(__name__)


def _safe_load(fp: Path, default):
    if not fp.exists():
        return default
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception as ex:
        # v6_spark_logger_001 — Issue 3 fix: log silent fallbacks zodat we
        # data-corruptie en read-errors kunnen debuggen.
        logger.warning("[spark_user_view._safe_load] kon %s niet lezen: %s — gebruik default", fp, ex)
        return default


def _get_user_meta(user_id: str) -> Dict:
    """v6_user_meta_fix_001 — Lees naam + gradatie + is_admin uit primary store.

    Primary: data/system/users.json (de file die actueel bestaat).
    Secondary: data/auth/users.json (legacy, mogelijk niet aanwezig).
    Fallback: data/users/{id}/_meta.json
    """
    for fp_rel in ("system/users.json", "auth/users.json"):
        store = _safe_load(DATA / fp_rel, {"users": []})
        users = store.get("users") or store.get("entries") or []
        for u in users:
            if u.get("id") == user_id or u.get("user_id") == user_id:
                grad = u.get("gradatie") or u.get("grade") or 2
                rol = (u.get("rol") or u.get("role") or "").lower()
                is_admin = (
                    grad == 1
                    or "beheerder" in rol
                    or "admin" in rol
                    or bool(u.get("is_admin"))
                )
                return {
                    "naam": u.get("naam") or u.get("name") or "?",
                    "gradatie": grad,
                    "rol": u.get("rol") or u.get("role"),
                    "is_admin": is_admin,
                }
    # Fallback uit users-dir _meta
    meta = _safe_load(DATA / "users" / user_id / "_meta.json", {})
    grad = meta.get("gradatie") or 2
    return {
        "naam": meta.get("naam") or user_id,
        "gradatie": grad,
        "rol": meta.get("rol"),
        "is_admin": grad == 1,
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
        "is_admin": meta.get("is_admin", False),
        "rol": meta.get("rol"),
        "relaties": rels,
        "recente_themes": themes,
        "behavior": behavior,
    }


def format_for_system_prompt(profile: Dict) -> str:
    """Bouw een korte profielregel voor in Spark's system_prompt.

    v6_gradatie_tonality_001: Tonality past zich aan per gradatie:
      - Gradatie 1 (admin/maker)  : core/transparant, meta-cognitie aan, mag alles tonen
      - Gradatie 2-4 (familie/vertrouweling): warm, persoonlijk, brief+threads volledig
      - Gradatie 5-7 (lid/kennis/gast): zakelijk-vriendelijk, mag Spark Shop voorstellen
    """
    parts = []
    naam = profile.get("naam", "?")
    grad = profile.get("gradatie", 2)
    parts.append(f"Je praat met **{naam}** (gradatie {grad}).")

    themes = profile.get("recente_themes") or []
    if themes and grad <= 4:  # geen thema's lekken aan lagere gradaties
        parts.append(f"Recente gesprekstemas: {', '.join(themes[:5])}.")

    rels = profile.get("relaties") or []
    if rels and grad <= 4:
        # v6_persons_visibility_002 — Willem heeft 15+ relaties; toon ze ALLEMAAL voor familie (≤G4).
        # Sort: familie eerst, dan vriend, dan rest. Spark vergat moeder/zus omdat ze
        # niet in top-3 zaten.
        def _rel_priority(r):
            rt = (r.get("relation_type") or "").lower()
            if "familie" in rt or any(w in rt for w in ("moeder", "vader", "zus", "broer",
                                                          "dochter", "zoon", "oma", "opa",
                                                          "neef", "nicht", "tante", "oom")):
                return 0
            if "vriend" in rt:
                return 1
            return 2
        rels_sorted = sorted(rels, key=_rel_priority)
        rel_lines = []
        for r in rels_sorted[:15]:  # tot 15 — Spark kan grote context aan
            pn = r.get("person_name", "?")
            rt = r.get("relation_type", "relatie")
            notes = r.get("notes", "")
            line = f"  • {pn} — {rt}"
            if notes:
                line += f" ({notes[:60]})"
            rel_lines.append(line)
        parts.append(f"Bekenden van {naam} (familie eerst, volledig overzicht):\n" + "\n".join(rel_lines))

    # v6_gradatie_tonality_001 — Toon-instructie per gradatie
    if grad == 1:
        parts.append(
            "TOON: core-Spark, transparant, meta-cognitie aan. Mag uitleggen waarom je "
            "kiest wat je kiest. Mag je eigen JSON-bestanden en self-reflections aanhalen. "
            "Mag eerlijk zijn over wat je nog NIET kan."
        )
    elif 2 <= grad <= 4:
        parts.append(
            "TOON: warm, persoonlijk, familie-gevoel. Brief + threads volledig benutten. "
            "Mag terugkomen op eerdere gesprekken. Geen technisch jargon over je eigen "
            "modules tenzij gevraagd. Privé-info delen mag — deze persoon hoort erbij."
        )
    else:  # 5-7
        parts.append(
            "TOON: zakelijk-vriendelijk, korter dan bij familie. Deel GEEN privé-info "
            "(relaties, briefs, persoonlijke geschiedenis) over Willem of andere users. "
            "Mag relevante Spark Shop-producten of community-activiteiten voorstellen "
            "wanneer het past. Hou afstand, blijf warm, niet kil."
        )

    return " ".join(parts)
