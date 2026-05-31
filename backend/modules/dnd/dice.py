"""
v6_dice_001 — D&D Dobbelsteen-events

Speler kiest 'basis' of 'super' dobbelsteen en optioneel een stat (kracht/behendigheid/etc.).
Worp = 1d20 + stat_bonus (basis) of 1d20 + max(2 stats) (super, hogere baseline).

Uitkomst-niveaus:
  ≤ 1            → kritiek_faal (verhaaltje + minor penalty)
  2..9           → faal
  10..15         → succes (kleine reward)
  16..19         → groot_succes (medium reward)
  20+            → kritiek_succes (grote reward + lore)

Opslag: rollt geschreven naar character.events_feed (laatste 50)
"""
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import random
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/dnd/dice", tags=["dnd-dice"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"

DICE_CARDS = {
    # Begrip-based lookup (robuust tegen ID-wijzigingen)
    "basis": {"begrip": "Basis Dobbelstenen Avatar", "tag_hint": ["dobbelsteen", "basis"]},
    "super": {"begrip": "Super dobbelsteen avatar", "tag_hint": ["dobbelsteen", "super"]},
}


def _find_dice_card(key: str):
    """Vind de D&D-kaart voor een dobbelsteen via begrip-naam (case-insensitief)."""
    if key not in DICE_CARDS:
        return None
    target = DICE_CARDS[key]
    target_begrip = target["begrip"].lower().strip()
    game_file = DATA_ROOT / "cards" / "dnd" / "game.json"
    game = load_json(game_file, default={"cards": []})
    for c in game.get("cards", []):
        if (c.get("begrip") or "").lower().strip() == target_begrip:
            return c
    # Fallback: alle tag_hints aanwezig
    hints = [h.lower() for h in target["tag_hint"]]
    for c in game.get("cards", []):
        tags = [str(t).lower() for t in (c.get("tags") or [])]
        if all(h in tags for h in hints):
            return c
    return None

# Generieke uitkomst-flavor per niveau, themathisch
FLAVOR = {
    "kritiek_faal": [
        "De wereld kantelt heel even tegen je. Een vergissing die nog lang nasmeult.",
        "Wat misgaat, kan op zo veel manieren misgaan — en hier gebeurt het allemaal tegelijk.",
    ],
    "faal": [
        "Niet vandaag. Het lukt niet, maar de fout is klein en je leert ervan.",
        "Je voelt dat het ergens vastloopt. Een ademteug — en je probeert het later opnieuw.",
    ],
    "succes": [
        "Het werkt. Niet spectaculair, maar gewoon: het werkt.",
        "Een rustig succes. Genoeg om door te kunnen.",
    ],
    "groot_succes": [
        "Beter dan je had durven hopen. Een glimp van wat mogelijk is.",
        "Het loopt soepel — alsof iets je een zachte duw geeft.",
    ],
    "kritiek_succes": [
        "De wereld luistert. Wat je probeert lukt fenomenaal — en je weet: dit was niet alleen geluk.",
        "Een moment dat in je geheugen blijft hangen. Hier verandert iets.",
    ],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _level_for(total: int) -> str:
    if total <= 1:
        return "kritiek_faal"
    if total <= 9:
        return "faal"
    if total <= 15:
        return "succes"
    if total <= 19:
        return "groot_succes"
    return "kritiek_succes"


def _emoji_for(level: str) -> str:
    return {
        "kritiek_faal": "💀",
        "faal": "❌",
        "succes": "✅",
        "groot_succes": "✨",
        "kritiek_succes": "🌟",
    }.get(level, "🎲")


class RollReq(BaseModel):
    user_id: str
    dice: str = "basis"               # "basis" | "super"
    stat_key: Optional[str] = None    # bv. "kracht" / "behendigheid" / etc.
    actie: Optional[str] = None       # vrije tekst — bv. "verken Stormhaven"


@router.post("/roll")
async def roll_dice(req: RollReq):
    if req.dice not in DICE_CARDS:
        raise HTTPException(400, "dice moet 'basis' of 'super' zijn")

    char_fp = DATA_ROOT / "dnd" / "characters" / f"{req.user_id}.json"
    char = load_json(char_fp, default={})
    if not char.get("user_id"):
        raise HTTPException(404, "Speler-character niet gevonden")

    stats = char.get("statistieken") or {}
    stat_bonus = 0
    chosen_stat = req.stat_key
    if chosen_stat and chosen_stat in stats:
        stat_bonus = int(stats[chosen_stat])
    if req.dice == "super":
        # super: pak de TWEE hoogste stats erbij i.p.v. 1
        all_stats = sorted([int(v) for v in stats.values()], reverse=True)
        stat_bonus = sum(all_stats[:2]) if all_stats else 0
        chosen_stat = "Top 2 stats" if all_stats else chosen_stat

    base_roll = random.randint(1, 20)
    total = base_roll + stat_bonus
    level = _level_for(base_roll)  # natuurlijk niveau (vóór bonus)
    final_level = _level_for(total)

    # Schrijf event in events_feed
    text = f"{_emoji_for(final_level)} Dobbel ({req.dice}): {base_roll} + {stat_bonus} = {total} → {final_level.replace('_', ' ').title()}"
    if req.actie:
        text = f"{text} · actie: {req.actie}"
    flavor = random.choice(FLAVOR[final_level])
    events = char.setdefault("events_feed", [])
    events.append({
        "id": f"evt-{uuid.uuid4().hex[:8]}",
        "kind": "WERELD",
        "text": text,
        "flavor": flavor,
        "ts": _now(),
        "source": "dice_roll",
    })
    char["events_feed"] = events[-50:]
    save_json(char_fp, char)

    return {
        "success": True,
        "dice": req.dice,
        "base_roll": base_roll,
        "stat_key": chosen_stat,
        "stat_bonus": stat_bonus,
        "total": total,
        "natuurlijk_niveau": level,
        "uitkomst_niveau": final_level,
        "emoji": _emoji_for(final_level),
        "flavor": flavor,
        "card_id": (_find_dice_card(req.dice) or {}).get("id"),
    }


@router.get("/cards")
async def list_dice_cards():
    """Geef de 2 dobbelsteen-D&D-kaarten terug met hun image-URLs voor de UI."""
    out = {}
    for key in DICE_CARDS:
        c = _find_dice_card(key)
        if c:
            imgs = (c.get("media") or {}).get("image_urls") or []
            out[key] = {
                "card_id": c.get("id"),
                "begrip": c.get("begrip"),
                "image_url": imgs[0] if imgs else None,
                "lagen": c.get("lagen") or {},
                "tags": c.get("tags") or [],
            }
        else:
            out[key] = {"card_id": None, "image_url": None, "begrip": None}
    return out
