"""
Capability Matcher v1 — tag_vector → top-N commands via overlap-score
================================================================================
v6_command_registry_001 — Bidirectionele match tussen user-intent (tag_vector
uit extractor) en command-registry (intent_tags per endpoint).

Score = simple Jaccard-achtig: |overlap| / |union| × weight
Bonus voor behavior_class-tag (`behavior:...`) als die matcht met behavior_class_hint.
"""
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json

REGISTRY_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "command_registry.json"


def _load_registry() -> dict:
    return load_json(REGISTRY_FILE, default={"commands": []})


def _strip_prefix(tag: str) -> str:
    """'behavior:exploreren-uitbreiden' → 'exploreren-uitbreiden'"""
    if ":" in tag:
        return tag.split(":", 1)[1]
    return tag


def score_command(cmd: dict, tag_vector: List[str]) -> Dict:
    """Bereken match-score van 1 command tegen tag_vector.
    Returns {score, overlap, behavior_bonus, missing}"""
    cmd_tags = set((cmd.get("intent_tags") or []))
    if not cmd_tags or not tag_vector:
        return {"score": 0.0, "overlap": [], "behavior_bonus": 0, "missing": list(cmd_tags)}

    # Tag-overlap (zonder prefix-tags)
    user_tags_plain = {_strip_prefix(t) for t in tag_vector if not t.startswith(("emo:", "behavior:", "waarde:"))}
    overlap = cmd_tags & user_tags_plain
    union = cmd_tags | user_tags_plain
    if not union:
        return {"score": 0.0, "overlap": [], "behavior_bonus": 0, "missing": list(cmd_tags)}
    base_score = len(overlap) / len(union)

    # Behavior-bonus
    behavior_bonus = 0.0
    behavior_class_hint = cmd.get("behavior_class_hint")
    for t in tag_vector:
        if t.startswith("behavior:") and _strip_prefix(t) == behavior_class_hint:
            behavior_bonus = 0.15  # +15% als pipeline-behavior matcht
            break

    final_score = min(1.0, base_score + behavior_bonus)
    return {
        "score": round(final_score, 3),
        "overlap": sorted(list(overlap)),
        "behavior_bonus": behavior_bonus,
        "missing_required": [
            p for p in (cmd.get("required_params") or [])
            if p not in ("user_id",)  # user_id heeft chat automatisch
        ],
    }


def match_capability(tag_vector: List[str], top_n: int = 3,
                     min_score: float = 0.05,
                     gradatie: Optional[int] = None) -> Dict:
    """Match tag_vector tegen registry, returnt top-N candidates met scores.

    Args:
      tag_vector: output van extractor.extract_tags
      top_n: hoeveel candidates terug
      min_score: drempel — onder deze score = geen kandidaat
      gradatie: optioneel — filter op commands met gradatie_min <= gradatie

    Returns:
      {
        "tag_vector": [...],
        "candidates": [{cmd_id, path, score, overlap, ...}, ...],
        "best": ..., "best_score": ...,
        "needs_disambiguation": bool (top 2 binnen 0.1 van elkaar),
      }
    """
    registry = _load_registry()
    cmds = registry.get("commands", [])
    if gradatie is not None:
        cmds = [c for c in cmds if (c.get("gradatie_min") or 1) <= gradatie]

    scored = []
    for cmd in cmds:
        s = score_command(cmd, tag_vector)
        if s["score"] >= min_score:
            scored.append({
                "id": cmd.get("id"),
                "path": cmd.get("path"),
                "method": cmd.get("method"),
                "intent_tags": cmd.get("intent_tags"),
                "behavior_class_hint": cmd.get("behavior_class_hint"),
                "gradatie_min": cmd.get("gradatie_min"),
                **s,
            })
    scored.sort(key=lambda x: x["score"], reverse=True)

    top = scored[:top_n]
    best = top[0] if top else None
    best_score = best["score"] if best else 0.0
    # Disambiguation: top-2 dicht bij elkaar (<= 0.1 verschil) én beide >= 0.3
    needs_disambig = (
        len(top) >= 2
        and top[0]["score"] >= 0.3
        and (top[0]["score"] - top[1]["score"]) <= 0.1
    )

    return {
        "tag_vector": tag_vector,
        "candidates": top,
        "best": best,
        "best_score": best_score,
        "needs_disambiguation": needs_disambig,
        "registry_size": len(registry.get("commands", [])),
    }
