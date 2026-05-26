"""
Help-per-gradatie service (v6_help_per_gradatie_001)
================================================================================
Genereert PER GRADATIE een help-overzicht door command_registry te filteren op
`gradatie_min ≤ N`. Gegroepeerd per behavior_class_hint.

Endpoint:
  GET /api/help/{gradatie} → wat kan deze user
  GET /api/help/index     → samenvatting (counts per gradatie)
"""
from pathlib import Path
from typing import Optional
from collections import defaultdict

from fastapi import APIRouter, HTTPException

from modules.core.storage import load_json

router = APIRouter(prefix="/help", tags=["help-per-gradatie"])

REGISTRY = Path(__file__).parent.parent.parent / "data" / "system" / "command_registry.json"


def _category_for_command(cmd: dict) -> str:
    """Mapping van command-id prefix naar category-naam (NL)."""
    cid = cmd.get("id", "")
    path = cmd.get("path", "")
    if cid.startswith("cap_"):
        return "Spark capabilities"
    if "agenda" in cid or "/agenda" in path:
        return "Agenda & planning"
    if "notes" in cid or "/notes" in path:
        return "Notities"
    if "wallet" in cid or "/wallet" in path:
        return "Wallet & geld"
    if "trade" in cid or "/trade" in path:
        return "Trader"
    if "kbv2" in cid or "/kb/" in path:
        return "Kennisbank"
    if "bijbel" in cid or "spark_" in cid or "/spark/" in path:
        return "Spark Identity & Bijbel"
    if "emotion" in cid or "/emotion" in path:
        return "Emoties"
    if "achievement" in cid or "leaderboard" in cid:
        return "Achievements & ranking"
    if "community" in cid:
        return "Community"
    if "diary" in cid or "dagboek" in cid:
        return "Dagboek"
    if "boekhouder" in cid or "boekhoud" in path:
        return "Kasboek"
    return "Overig"


@router.get("/index")
async def help_index():
    """Samenvatting per gradatie + per-gradatie command-count."""
    reg = load_json(REGISTRY, default={"commands": []})
    cmds = reg.get("commands", [])
    counts = defaultdict(int)
    by_grad = defaultdict(list)
    for c in cmds:
        gm = int(c.get("gradatie_min") or 1)
        for g in range(gm, 8):  # ook beschikbaar voor hogere gradaties
            counts[g] += 1
            by_grad[g].append(c.get("id"))
    return {
        "success": True,
        "total_commands_in_registry": len(cmds),
        "by_gradatie": {str(g): counts[g] for g in range(1, 8)},
        "min_command_count": min(counts.values()) if counts else 0,
        "max_command_count": max(counts.values()) if counts else 0,
        "note": "Per gradatie zie je hoeveel commands beschikbaar zijn. /help/{gradatie} geeft de lijst.",
    }


@router.get("/{gradatie}")
async def help_for_gradatie(gradatie: int, group_by: Optional[str] = "category"):
    if gradatie < 1 or gradatie > 7:
        raise HTTPException(400, "Gradatie moet tussen 1 en 7 zijn.")
    reg = load_json(REGISTRY, default={"commands": []})
    cmds = reg.get("commands", [])
    visible = [c for c in cmds if int(c.get("gradatie_min") or 1) <= gradatie]

    # Group
    grouped = defaultdict(list)
    if group_by == "category":
        for c in visible:
            cat = _category_for_command(c)
            grouped[cat].append({
                "id": c.get("id"),
                "method": c.get("method"),
                "path": c.get("path"),
                "intent_tags": c.get("intent_tags"),
                "behavior_class_hint": c.get("behavior_class_hint"),
                "gradatie_min": c.get("gradatie_min"),
                "example": _example_for_command(c),
            })
    elif group_by == "behavior":
        for c in visible:
            beh = c.get("behavior_class_hint") or "overig"
            grouped[beh].append({
                "id": c.get("id"),
                "intent_tags": c.get("intent_tags"),
                "example": _example_for_command(c),
            })
    else:
        grouped["alle"] = visible

    return {
        "success": True,
        "gradatie": gradatie,
        "total_visible": len(visible),
        "groups": dict(grouped),
        "note": "Vraag Spark: 'wat kun jij?' om dit overzicht in chat te zien.",
    }


def _example_for_command(cmd: dict) -> str:
    """Maak van eerste paar tags een gebruikelijke chat-zin (placeholder voor donderdag)."""
    tags = cmd.get("intent_tags") or []
    if not tags:
        return ""
    if "agenda" in tags and "morgen" in tags:
        return "wat staat morgen op mijn agenda?"
    if "tellen" in tags and "gebruikers" in tags:
        return "hoeveel gebruikers hebben we?"
    if "winst" in tags or "pnl" in tags:
        return "laat trade-winst zien"
    if "kopen" in tags:
        return "koop voor 10 euro BTC"
    if "verkopen" in tags:
        return "verkoop al mijn ETH"
    if "saldo" in tags:
        return "wat is mijn saldo?"
    if "afbeelding" in tags or "foto" in tags:
        return "toon laatste foto"
    if "geluid" in tags or "audio" in tags:
        return "speel laatste geluidsfragment"
    if "kennis" in tags or "uitleg" in tags:
        return "leg X uit"
    if "notitie" in tags:
        return "noteer dat ik X moet doen"
    if "achievement" in tags:
        return "welke achievements heb ik?"
    if "bijbel" in tags or "kernwaarde" in tags:
        return "wat zegt de Spark Bijbel over X?"
    if "disclaimer" in tags:
        return "wat doe je niet?"
    return f"... ({', '.join(tags[:3])})"
