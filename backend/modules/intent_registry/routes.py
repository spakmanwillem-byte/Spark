"""
Intent Registry routes (v6_command_registry_001)
================================================================================
- POST /api/intent-registry/extract       → user-text → tag_vector
- POST /api/intent-registry/match         → tag_vector → top-N candidates
- POST /api/intent-registry/run-flow      → end-to-end demo (extract → match)
- GET  /api/intent-registry/registry      → registry inhoud
- GET  /api/intent-registry/skills/candidates → patroon-detect uit intent_log.jsonl
- POST /api/intent-registry/log           → registreer een (text, chosen_route) paar
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import json
from collections import Counter

from fastapi import APIRouter
from pydantic import BaseModel

from .extractor import extract_tags
from .matcher import _load_registry, match_capability

router = APIRouter(prefix="/intent-registry", tags=["intent-registry"])

INTENT_LOG = Path(__file__).parent.parent.parent / "data" / "system" / "intent_log.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExtractBody(BaseModel):
    text: str
    emotion_summary: Optional[dict] = None


@router.post("/extract")
async def extract(body: ExtractBody):
    tags = extract_tags(body.text, body.emotion_summary)
    return {"success": True, "tag_vector": tags, "input_chars": len(body.text or "")}


class MatchBody(BaseModel):
    tag_vector: List[str]
    top_n: int = 3
    gradatie: Optional[int] = None


@router.post("/match")
async def match(body: MatchBody):
    r = match_capability(body.tag_vector, top_n=body.top_n, gradatie=body.gradatie)
    return {"success": True, **r}


class FlowBody(BaseModel):
    text: str
    emotion_summary: Optional[dict] = None
    gradatie: Optional[int] = None
    top_n: int = 3


@router.post("/run-flow")
async def run_flow(body: FlowBody):
    """End-to-end demo: text → tags → top-N candidates."""
    tags = extract_tags(body.text, body.emotion_summary)
    r = match_capability(tags, top_n=body.top_n, gradatie=body.gradatie)
    return {"success": True, "input": body.text, **r}


@router.get("/registry")
async def get_registry():
    return _load_registry()


class LogBody(BaseModel):
    text: str
    tag_vector: List[str]
    chosen_route: Optional[str] = None
    chosen_command_id: Optional[str] = None
    user_id: Optional[str] = None


@router.post("/log")
async def log_intent(body: LogBody):
    """Schrijf 1 regel naar intent_log voor skill-discovery patroon-detect."""
    INTENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": _now_iso(),
        "user_id": body.user_id,
        "text": (body.text or "")[:200],
        "tag_vector": body.tag_vector,
        "tag_key": "|".join(sorted(body.tag_vector)),
        "chosen_route": body.chosen_route,
        "chosen_command_id": body.chosen_command_id,
    }
    with open(INTENT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"success": True, "logged": True}


@router.get("/skills/candidates")
async def skill_candidates(min_occurrences: int = 3, limit: int = 20):
    """v6_command_registry_001 — Patroon-detect: welke tag-vectors komen 3+ keer
    voor met dezelfde chosen_route? Dat zijn skill-candidates die we donderdag
    aan user mogen aanbieden ("Zal ik hier 1 command van maken?").
    """
    if not INTENT_LOG.exists():
        return {"success": True, "candidates": [], "total_logged": 0}
    entries = []
    try:
        for line in INTENT_LOG.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    except Exception:
        return {"success": False, "candidates": [], "error": "log_read_failed"}

    # Tel patronen (tag_key + chosen_route)
    counter = Counter()
    examples = {}
    for e in entries:
        key = (e.get("tag_key") or "", e.get("chosen_route") or "")
        counter[key] += 1
        # Bewaar 1 voorbeeld-text per key
        if key not in examples:
            examples[key] = e.get("text", "")

    candidates = []
    for (tag_key, route), n in counter.most_common():
        if n < min_occurrences:
            continue
        candidates.append({
            "tag_vector": tag_key.split("|") if tag_key else [],
            "chosen_route": route,
            "occurrences": n,
            "example_text": examples.get((tag_key, route), ""),
            "skill_candidate": True,
        })
    return {
        "success": True,
        "total_logged": len(entries),
        "candidates": candidates[:limit],
        "min_occurrences": min_occurrences,
    }
