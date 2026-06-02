"""v6_help_001 — Gradatie-gebaseerde help met fuzzy 'waar is X' lookup.

Datamodel: data/help/gradatie_{1..7}.json + admin.json
Elke file bevat:
  - intro (string)
  - topics[]: { id, label, korte_uitleg, deep_uitleg, nav_path, nav_testid, synonyms[] }
  - inherits_from: optionele referentie naar lagere-gradatie-file

API:
  GET  /api/help/for-viewer?user_id=X
       → return resolved help (eigen gradatie + alle inherits + admin als is_admin)
  POST /api/help/find  { "user_id": X, "query": "winkel" }
       → fuzzy zoekt topic, returnt nav_target + nav_testid voor glow
  GET  /api/help/topic/{topic_id}?user_id=X
       → diepe uitleg van 1 specifiek topic
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, List
import re

from fastapi import APIRouter
from pydantic import BaseModel

from modules.core.storage import load_json
from modules.admin.admin_service import is_admin, get_user

router = APIRouter(prefix="/help", tags=["help"])

HELP_DIR = Path(__file__).parent.parent.parent / "data" / "help"


def _load_help_file(name: str) -> Dict:
    path = HELP_DIR / f"{name}.json"
    if not path.exists():
        return {}
    return load_json(path, default={})


def _resolve_help_for_gradatie(gradatie: int) -> List[Dict]:
    """Resolve volledig topic-set door inherits_from chain te volgen.
    Higher gradatie = meer access dus topics worden cumulatief opgebouwd."""
    seen_ids = set()
    topics: List[Dict] = []
    # Start bij hoogste gradatie-nummer (= 7 minst toegang) en werk omhoog naar 1 (= meest)
    # Logic: gradatie 1 inherits 2 inherits 3 ... inherits 7
    # Dus voor gebruiker met gradatie G laden we G, G+1, G+2, ..., 7
    g = max(1, min(7, int(gradatie)))
    chain_order = list(range(g, 8))  # b.v. g=4 → [4,5,6,7]
    for n in reversed(chain_order):  # begin bij 7 (basis), eindig bij eigen gradatie
        data = _load_help_file(f"gradatie_{n}")
        # extra_topics zijn de UNIEKE topics van die gradatie; gradatie_7 heeft "topics" als basis
        items = data.get("topics") or data.get("extra_topics") or []
        for t in items:
            if t.get("id") not in seen_ids:
                seen_ids.add(t.get("id"))
                topics.append(t)
    return topics


def _get_intro(gradatie: int) -> str:
    data = _load_help_file(f"gradatie_{max(1, min(7, int(gradatie)))}")
    return data.get("intro", "")


@router.get("/for-viewer")
async def help_for_viewer(user_id: Optional[str] = None):
    """Return resolved help-content voor deze user."""
    u = get_user(user_id) if user_id else None
    gradatie = (u or {}).get("gradatie", 7) if u else 7
    admin_flag = is_admin(user_id) if user_id else False

    topics = _resolve_help_for_gradatie(gradatie)
    intro = _get_intro(gradatie)

    admin_topics: List[Dict] = []
    admin_intro = ""
    if admin_flag:
        adata = _load_help_file("admin")
        admin_topics = adata.get("extra_topics") or adata.get("topics") or []
        admin_intro = adata.get("intro", "")

    return {
        "user_id": user_id,
        "gradatie": gradatie,
        "is_admin": admin_flag,
        "intro": intro,
        "topics": topics,
        "topic_count": len(topics),
        "admin_intro": admin_intro,
        "admin_topics": admin_topics,
        "admin_topic_count": len(admin_topics),
    }


class FindRequest(BaseModel):
    user_id: Optional[str] = None
    query: str


@router.post("/find")
async def help_find(req: FindRequest):
    """v6_help_001 — Fuzzy zoek naar een topic op basis van query ('waar is winkel').

    Algoritme:
      1. Normaliseer query (lowercase, strip leestekens, verwijder 'waar is/vind/zoek')
      2. Voor elk topic: score = aantal matches in label + id + synonyms
      3. Hoogste score wint
      4. Tie-breaker: kortste topic-id

    Returnt {success, topic, nav_path, nav_testid} of {success:false, suggestions[]}.
    """
    u = get_user(req.user_id) if req.user_id else None
    gradatie = (u or {}).get("gradatie", 7) if u else 7
    admin_flag = is_admin(req.user_id) if req.user_id else False

    # Verzamel alle topics (eigen gradatie + admin als admin)
    all_topics = _resolve_help_for_gradatie(gradatie)
    if admin_flag:
        admin_topics = (_load_help_file("admin").get("extra_topics") or [])
        all_topics = all_topics + admin_topics

    # Normaliseer query: strip "waar is", "vind", "zoek", "open", "ga naar"
    q = req.query.lower().strip()
    for prefix in ["waar is", "waar staat", "vind de", "vind", "zoek de", "zoek", "open de", "open",
                   "ga naar de", "ga naar", "toon de", "toon", "laat zien", "laat de", "naar de"]:
        if q.startswith(prefix + " "):
            q = q[len(prefix) + 1:].strip()
            break
    # Strip vraagteken / punt
    q = re.sub(r"[?!.,;]+$", "", q).strip()
    if not q:
        return {"success": False, "error": "lege query"}

    # Tokenize voor multi-word matching
    q_tokens = set(re.findall(r"\w+", q))
    if not q_tokens:
        return {"success": False, "error": "geen woorden in query"}

    scored = []
    for t in all_topics:
        score = 0
        haystack = [
            (t.get("label", "") or "").lower(),
            (t.get("id", "") or "").lower().replace("-", " "),
        ]
        haystack.extend([(s or "").lower() for s in t.get("synonyms", [])])
        hay_combined = " ".join(haystack)
        hay_tokens = set(re.findall(r"\w+", hay_combined))

        # Volledige string-match krijgt zwaargewicht
        if q in hay_combined:
            score += 100

        # Token-overlap
        overlap = q_tokens & hay_tokens
        score += len(overlap) * 25

        # Bonus voor exact label-match
        if q == (t.get("label", "") or "").lower():
            score += 200
        if q in [(s or "").lower() for s in t.get("synonyms", [])]:
            score += 150

        if score > 0:
            scored.append((score, t))

    scored.sort(key=lambda x: (-x[0], len(x[1].get("id", ""))))

    if not scored:
        # Geen match — geef topic-lijst als suggesties
        return {
            "success": False,
            "query": q,
            "suggestions": [
                {"id": t.get("id"), "label": t.get("label")} for t in all_topics[:8]
            ],
        }

    best_score, best = scored[0]
    return {
        "success": True,
        "query": q,
        "topic": best,
        "score": best_score,
        "nav_path": best.get("nav_path"),
        "nav_testid": best.get("nav_testid"),
        "alternatives": [{"id": t.get("id"), "label": t.get("label"), "score": s}
                         for s, t in scored[1:4]],
    }


@router.get("/topic/{topic_id}")
async def help_topic(topic_id: str, user_id: Optional[str] = None):
    """Diepe uitleg van 1 specifiek topic."""
    u = get_user(user_id) if user_id else None
    gradatie = (u or {}).get("gradatie", 7) if u else 7
    admin_flag = is_admin(user_id) if user_id else False

    all_topics = _resolve_help_for_gradatie(gradatie)
    if admin_flag:
        all_topics = all_topics + (_load_help_file("admin").get("extra_topics") or [])

    topic = next((t for t in all_topics if t.get("id") == topic_id), None)
    if not topic:
        return {"success": False, "error": f"Topic '{topic_id}' niet gevonden voor gradatie {gradatie}"}
    return {"success": True, "topic": topic}
