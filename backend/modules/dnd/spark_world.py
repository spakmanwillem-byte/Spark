"""
Spark World — Bark Flow (v6_dnd_bark_001)
==========================================
D&D verhaal-stroom vanuit community chat.

Concept:
  1. User triggert sessie ("help" / knop "Spark World")
  2. Intro-bark wordt getoond + 3 zintuig-knoppen (ZIE / HOOR / VOEL)
  3. User klikt zintuig → krijgt vraag → typt antwoord
  4. Antwoord wordt opgeslagen als D&D-kaart (draft) in /data/cards/dnd/
  5. Kaarten kunnen 'locked' worden (canon) zodat ze in volgend spel als
     keuze-knop verschijnen.

NB: combat / NPC-dialoog komt later. Dit is alleen het skelet.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json


router = APIRouter(prefix="/dnd/spark-world", tags=["dnd-spark-world"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
CARDS_DIR = DATA_ROOT / "cards" / "dnd"
CARDS_INDEX = CARDS_DIR / "_index.json"


# ---------------------------------------------------------------------------
# Statische config: de 3 zintuig-kanalen
# ---------------------------------------------------------------------------
SENSES = [
    {
        "id": "zie",
        "label": "Zie",
        "icon": "👁️",
        "color": "#06b6d4",          # cyan
        "prompt": "Wat zie je om je heen? Een kleur, een vorm, iets dat opvalt...",
        "kb_lade": "weten",          # → KB v2 lade-koppeling
    },
    {
        "id": "hoor",
        "label": "Hoor",
        "icon": "👂",
        "color": "#f59e0b",          # amber
        "prompt": "Wat hoor je? Een geluid, een woord, een onderwerp dat doorklinkt...",
        "kb_lade": "spreken",
    },
    {
        "id": "voel",
        "label": "Voel",
        "icon": "❤️",
        "color": "#ec4899",          # pink
        "prompt": "Wat voel je nu? Een emotie, een spanning, een rust...",
        "kb_lade": "voelen",
    },
]

INTRO_TEXT = (
    "Welkom in **Spark World**.\n\n"
    "Dit is een levende wereld. Geen gevechten, geen levens. "
    "Alleen dat wat jij meebrengt en wat de wereld terug geeft.\n\n"
    "Iets trekt je. Je staat ergens — maar waar precies, dat bepaal jij. "
    "Kies hoe je in deze wereld stapt:"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_index() -> dict:
    return load_json(CARDS_INDEX, default={"cards": [], "updated_at": _now()})


def _save_index(idx: dict) -> None:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    idx["updated_at"] = _now()
    save_json(CARDS_INDEX, idx)


def _card_path(card_id: str) -> Path:
    return CARDS_DIR / f"{card_id}.json"


def _sense(sense_id: str) -> Optional[dict]:
    for s in SENSES:
        if s["id"] == sense_id:
            return s
    return None


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class StartBody(BaseModel):
    user_id: str = "user-001"


class RespondBody(BaseModel):
    user_id: str = "user-001"
    sense: str          # "zie" | "hoor" | "voel"
    content: str        # wat user invulde
    titel: Optional[str] = None


class LockBody(BaseModel):
    user_id: str = "user-001"
    locked: bool = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/start")
async def start_session(body: StartBody):
    """Start een Spark World sessie.
    Geeft intro-tekst + 3 zintuig-knoppen + bestaande locked-kaarten
    die als nieuwe keuze-knoppen kunnen verschijnen.
    """
    idx = _load_index()
    locked_choices: List[Dict] = []
    for entry in idx.get("cards", []):
        if entry.get("status") != "locked":
            continue
        # Laad volledig kaart om sense+color te krijgen
        cp = _card_path(entry["id"])
        if not cp.exists():
            continue
        try:
            card = json.loads(cp.read_text(encoding="utf-8"))
        except Exception:
            continue
        sense = _sense(card.get("sense") or "")
        locked_choices.append({
            "id": card.get("id"),
            "titel": card.get("titel") or entry.get("titel"),
            "sense": card.get("sense"),
            "color": sense["color"] if sense else "#94a3b8",
            "icon": sense["icon"] if sense else "✨",
            "content_preview": (card.get("content") or "")[:80],
        })

    return {
        "success": True,
        "session_id": f"sw-{uuid.uuid4().hex[:8]}",
        "intro": INTRO_TEXT,
        "title": "Spark World",
        "baseline": "Een levende wereld. Wat jij invult, kleurt mee.",
        "senses": SENSES,
        "locked_cards": locked_choices,
        "draft_count": sum(1 for c in idx.get("cards", []) if c.get("status") == "draft"),
    }


@router.post("/respond")
async def respond(body: RespondBody):
    """User koos een zintuig + typte een tekst → maakt een nieuwe D&D-kaart aan
    in /data/cards/dnd/ met status 'draft'."""
    sense = _sense(body.sense)
    if not sense:
        raise HTTPException(400, f"Onbekend zintuig: {body.sense}")
    if not (body.content or "").strip():
        raise HTTPException(400, "Content mag niet leeg zijn")

    card_id = f"card-dnd-{uuid.uuid4().hex[:8]}"
    titel = (body.titel or "").strip() or _autotitle(body.content, sense["label"])
    card = {
        "id": card_id,
        "type": "dnd_bark",
        "titel": titel,
        "sense": sense["id"],
        "sense_label": sense["label"],
        "icon": sense["icon"],
        "color": sense["color"],
        "kb_lade": sense["kb_lade"],
        "content": body.content.strip(),
        "status": "draft",       # draft → locked als Willem vastklikt
        "media": {"image_url": None, "audio_url": None},
        "footnote": {
            "aangemaakt_door": body.user_id,
            "aangemaakt_op": _now(),
            "laatst_bewerkt": _now(),
            "trigger_count": 0,
        },
    }

    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    _card_path(card_id).write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")

    # Update index
    idx = _load_index()
    idx.setdefault("cards", []).insert(0, {
        "id": card_id,
        "titel": titel,
        "sense": sense["id"],
        "status": "draft",
        "created_at": card["footnote"]["aangemaakt_op"],
    })
    _save_index(idx)

    # Track behavior — story_share + kb_create proxy
    try:
        from .routes import track_behavior, TrackBody, observe, ObserveBody
        await track_behavior(TrackBody(user_id=body.user_id, counter_key="story_share", delta=1))
        await observe(ObserveBody(
            user_id=body.user_id,
            kind="spark_world_card",
            detail={"card_id": card_id, "sense": sense["id"], "titel": titel},
        ))
    except Exception:
        pass

    return {"success": True, "card": card}


@router.post("/cards/{card_id}/lock")
async def lock_card(card_id: str, body: LockBody):
    """Mark een D&D-kaart als 'locked' (canon) of zet 'm terug naar draft.
    Locked kaarten verschijnen bij volgende sessie-start als keuze-knop."""
    cp = _card_path(card_id)
    if not cp.exists():
        raise HTTPException(404, f"Kaart {card_id} niet gevonden")
    try:
        card = json.loads(cp.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(500, f"Kaart kapot: {e}")

    new_status = "locked" if body.locked else "draft"
    card["status"] = new_status
    card["footnote"]["laatst_bewerkt"] = _now()
    if body.locked:
        card["footnote"]["locked_op"] = _now()
        card["footnote"]["locked_door"] = body.user_id
    cp.write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")

    # Update index
    idx = _load_index()
    for entry in idx.get("cards", []):
        if entry.get("id") == card_id:
            entry["status"] = new_status
            break
    _save_index(idx)

    return {"success": True, "card_id": card_id, "status": new_status}


@router.get("/cards")
async def list_cards(status: Optional[str] = None, limit: int = 50):
    """Lijst D&D-bark-kaarten. Optioneel filter op status (draft|locked)."""
    idx = _load_index()
    items = idx.get("cards", [])
    if status:
        items = [c for c in items if c.get("status") == status]
    # Newest first (index voegt vooraan in, dus ok)
    items = items[:limit]
    # Verrijk met preview uit kaart-file
    out = []
    for entry in items:
        cp = _card_path(entry["id"])
        if not cp.exists():
            continue
        try:
            card = json.loads(cp.read_text(encoding="utf-8"))
        except Exception:
            continue
        out.append({
            **entry,
            "sense": card.get("sense"),
            "sense_label": card.get("sense_label"),
            "color": card.get("color"),
            "icon": card.get("icon"),
            "content_preview": (card.get("content") or "")[:140],
        })
    return {"success": True, "total": len(out), "cards": out}


@router.get("/cards/{card_id}")
async def get_card(card_id: str):
    cp = _card_path(card_id)
    if not cp.exists():
        raise HTTPException(404, f"Kaart {card_id} niet gevonden")
    return json.loads(cp.read_text(encoding="utf-8"))


@router.delete("/cards/{card_id}")
async def delete_card(card_id: str):
    """Verwijder een D&D-kaart definitief (admin-only via UI)."""
    cp = _card_path(card_id)
    if not cp.exists():
        raise HTTPException(404, f"Kaart {card_id} niet gevonden")
    cp.unlink()
    idx = _load_index()
    idx["cards"] = [c for c in idx.get("cards", []) if c.get("id") != card_id]
    _save_index(idx)
    return {"success": True, "deleted": card_id}


# ---------------------------------------------------------------------------
# v6_dnd_game_cards_001 — KB-shaped Game/D&D kaarten in aparte game.json
# Hetzelfde schema als KB v2: lagen 1-4, ws5, tags, media, footnote
# Class: "game", category-tag: "D&D"
# Opslag: /app/backend/data/cards/dnd/game.json
# ---------------------------------------------------------------------------
GAME_FILE = CARDS_DIR / "game.json"


def _load_game() -> Dict:
    return load_json(GAME_FILE, default={"cards": [], "updated_at": _now()})


def _save_game(data: Dict) -> None:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now()
    save_json(GAME_FILE, data)


def _compute_game_needs(card: Dict) -> list:
    needs = []
    lagen = card.get("lagen") or {}
    if not (lagen.get("laag1") or "").strip():
        needs.append("laag1")
    if not any((card.get("ws5") or {}).values()):
        needs.append("ws5")
    media = card.get("media") or {}
    if not media.get("voice_url"):
        needs.append("voice")
    if not (media.get("image_urls") or []):
        needs.append("image")
    return needs


class GameCreateBody(BaseModel):
    begrip: str
    user_id: Optional[str] = "user-001"
    sense: Optional[str] = None      # 'zie' | 'hoor' | 'voel' (optioneel kanaal-tag)


class GameEditBody(BaseModel):
    card_id: str
    updates: Dict
    user_id: Optional[str] = "user-001"


class GameLockBody(BaseModel):
    card_id: str
    locked: bool = True
    user_id: Optional[str] = "user-001"


@router.get("/game-cards")
async def list_game_cards(status: Optional[str] = None, limit: int = 200):
    """Lijst alle game/D&D kaarten (KB-shape)."""
    data = _load_game()
    cards = data.get("cards", [])
    if status:
        cards = [c for c in cards if c.get("status") == status]
    # Newest first (footnote.aangemaakt_op desc)
    cards = sorted(cards, key=lambda c: (c.get("footnote") or {}).get("aangemaakt_op") or "", reverse=True)
    return {"success": True, "total": len(cards), "cards": cards[:limit]}


@router.get("/game-cards/{card_id}")
async def get_game_card(card_id: str):
    data = _load_game()
    for c in data.get("cards", []):
        if c.get("id") == card_id:
            return c
    raise HTTPException(404, f"Game-kaart {card_id} niet gevonden")


@router.post("/game-cards")
async def create_game_card(body: GameCreateBody):
    """Maak een lege game/D&D-kaart met KB-shape. Default status = draft."""
    begrip = (body.begrip or "").strip()
    if not begrip:
        raise HTTPException(400, "Begrip mag niet leeg zijn")
    card_id = f"game-{uuid.uuid4().hex[:8]}"
    base_tags = ["D&D"]
    if body.sense:
        base_tags.append(body.sense)
    card = {
        "id": card_id,
        "class": "game",
        "type": "dnd_game_card",
        "begrip": begrip,
        "sense": body.sense,           # optioneel kanaal-aanduiding
        "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
        "ws5": {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""},
        "tags": base_tags,
        "media": {"voice_url": None, "voice_transcript": None, "image_urls": []},
        # v6_game_meta_001 — game-specifieke metadata (item-stats, fractie, etc.)
        # Leeg = niet-bruikbaar als item. Vul in om kaart als equipable/carry item te markeren.
        "game_meta": {
            "is_item": False,             # True = kaart kan in rugzak/inventory
            "slot": "",                   # equipment slot (rechterhand/torso/etc.) of "" voor non-equip
            "weight": 0.0,                # kg
            "stats_bonus": {},            # {kracht, behendigheid, intelligentie, conditie, wilskracht, geluk}
            "combat_bonus": {},           # {aanvalskracht, verdediging, magie, crit_kans, beweging, initiatief}
            "meta": {"klasse": "", "beroep": "", "fractie": "", "locatie": ""},
            "value_goud": 0,
            "rarity": "common",           # common / uncommon / rare / epic / legendary
            "kind": "",                   # food / weapon / armor / tool / shield / drink / currency / pet / etc.
        },
        "status": "draft",             # draft → locked als Willem vastklikt
        "footnote": {
            "bron": "manual",
            "vertrouwen": 0.3,
            "aangemaakt_door": body.user_id,
            "aangemaakt_op": _now(),
            "laatst_bewerkt_op": _now(),
        },
    }
    card["needs"] = _compute_game_needs(card)
    data = _load_game()
    data.setdefault("cards", []).insert(0, card)
    _save_game(data)
    return {"success": True, "card": card}


@router.post("/game-cards/edit")
async def edit_game_card(body: GameEditBody):
    """Update lagen / ws5 / tags / begrip / media van een game-kaart."""
    data = _load_game()
    for c in data.get("cards", []):
        if c.get("id") == body.card_id:
            u = body.updates or {}
            if "lagen" in u:  c["lagen"] = {**(c.get("lagen") or {}), **(u["lagen"] or {})}
            if "ws5"   in u:  c["ws5"]   = {**(c.get("ws5") or {}),   **(u["ws5"] or {})}
            if "tags"  in u and isinstance(u["tags"], list):
                # Zorg dat "D&D" tag altijd aanwezig blijft (class-aanduiding)
                tags = list(u["tags"])
                if "D&D" not in tags: tags.append("D&D")
                c["tags"] = tags
            if "begrip" in u and u["begrip"]:
                c["begrip"] = u["begrip"]
            if "media"  in u and isinstance(u["media"], dict):
                c["media"]  = {**(c.get("media") or {}), **u["media"]}
            if "sense" in u:
                c["sense"] = u["sense"]
            # v6_game_meta_001 — diep mergen van game_meta (item-stats etc.)
            if "game_meta" in u and isinstance(u["game_meta"], dict):
                gm_old = c.get("game_meta") or {}
                gm_new = dict(gm_old)
                for k, v in u["game_meta"].items():
                    if isinstance(v, dict) and isinstance(gm_old.get(k), dict):
                        gm_new[k] = {**gm_old.get(k, {}), **v}
                    else:
                        gm_new[k] = v
                c["game_meta"] = gm_new
            fn = c.get("footnote") or {}
            fn["laatst_bewerkt_door"] = body.user_id
            fn["laatst_bewerkt_op"] = _now()
            # vertrouwen omhoog als lagen ingevuld zijn
            lagen_filled = sum(1 for v in (c.get("lagen") or {}).values() if (v or "").strip())
            fn["vertrouwen"] = max(fn.get("vertrouwen", 0.3), round(0.3 + 0.15 * lagen_filled, 2))
            c["footnote"] = fn
            c["needs"] = _compute_game_needs(c)
            _save_game(data)
            return {"success": True, "card": c}
    raise HTTPException(404, f"Game-kaart {body.card_id} niet gevonden")


@router.post("/game-cards/lock")
async def lock_game_card(body: GameLockBody):
    """Markeer game-kaart als locked (canon) of zet terug naar draft."""
    data = _load_game()
    for c in data.get("cards", []):
        if c.get("id") == body.card_id:
            c["status"] = "locked" if body.locked else "draft"
            fn = c.setdefault("footnote", {})
            fn["laatst_bewerkt_op"] = _now()
            if body.locked:
                fn["locked_op"] = _now()
                fn["locked_door"] = body.user_id
            _save_game(data)
            return {"success": True, "card_id": body.card_id, "status": c["status"]}
    raise HTTPException(404, f"Game-kaart {body.card_id} niet gevonden")


@router.delete("/game-cards/{card_id}")
async def delete_game_card(card_id: str):
    data = _load_game()
    before = len(data.get("cards", []))
    data["cards"] = [c for c in data.get("cards", []) if c.get("id") != card_id]
    if len(data["cards"]) == before:
        raise HTTPException(404, f"Game-kaart {card_id} niet gevonden")
    _save_game(data)
    return {"success": True, "deleted": card_id}


# v6_game_meta_001 — Items uit D&D-kaarten halen (eenheid: 1 kaart-systeem voor alles)
@router.get("/game-items")
async def list_item_cards(slot: Optional[str] = None, fractie: Optional[str] = None):
    """
    Lijst alle D&D-kaarten die als items gemarkeerd zijn (game_meta.is_item: true).
    Filters: slot=rechterhand|torso|...  fractie=spark|...
    """
    data = _load_game()
    items = []
    for c in data.get("cards", []):
        gm = c.get("game_meta") or {}
        if not gm.get("is_item"):
            continue
        if slot and gm.get("slot") != slot:
            continue
        if fractie:
            meta = gm.get("meta") or {}
            if (meta.get("fractie") or "") != fractie:
                continue
        # Compose item-shape (consistent met /api/inventory/catalog/all)
        img_url = (c.get("media") or {}).get("image_urls", [None])[0] if (c.get("media") or {}).get("image_urls") else None
        items.append({
            "id": c.get("id"),
            "card_id": c.get("id"),
            "naam": c.get("begrip"),
            "kind": gm.get("kind") or "",
            "slot": gm.get("slot") or "",
            "weight": gm.get("weight", 0.0),
            "stats_bonus": gm.get("stats_bonus") or {},
            "combat_bonus": gm.get("combat_bonus") or {},
            "meta": gm.get("meta") or {},
            "value_goud": gm.get("value_goud", 0),
            "rarity": gm.get("rarity") or "common",
            "description": (c.get("lagen") or {}).get("laag1") or "",
            "tags": c.get("tags") or [],
            "image_url": img_url,
            "source": "dnd_card",
        })
    return {"success": True, "total": len(items), "items": items}


@router.post("/game-cards/migrate-items")
async def migrate_items_to_cards(user_id: str = "user-001"):
    """
    EENMALIGE MIGRATIE: kopieer ITEM_CATALOG entries uit inventory/routes.py
    naar game_meta op overeenkomende D&D-kaarten (matched op begrip/tags).
    Maakt het D&D-kaart-systeem dé bron-van-waarheid.
    """
    from ..inventory.routes import ITEM_CATALOG

    # Mapping van item_id → kandidaat begrip/tags op D&D-kaarten
    ID_TO_CARD_HINTS = {
        "brood":         ["basis brood", "brood"],
        "vlees":         ["basis vlees", "vlees"],
        "water":         ["waterput", "water"],
        "kaas":          ["kaas"],
        "appel":         ["appel"],
        "ei":            ["ei"],
        "fakkel":        ["fakkel", "toorts", "lantaarn"],
        "munt-goud":     ["goud", "munt"],
        "zwaard-klein":  ["1 hand wapen rechts", "zwaard"],
        "schild-basis":  ["basis schild", "schild"],
        "linnen-shirt":  ["t-shirt", "shirt"],
        "linnen-broek":  ["broek basis", "broek"],
        "lederen-helm":  ["hoofd"],
        "leren-laarzen": ["schoenen", "laarzen"],
        "backpack-basic": ["basis rugzak"],
    }

    data = _load_game()
    cards = data.get("cards", [])
    migrated = []
    for item_id, hints in ID_TO_CARD_HINTS.items():
        if item_id not in ITEM_CATALOG:
            continue
        item = ITEM_CATALOG[item_id]
        target = None
        for h in hints:
            lh = h.lower().strip()
            # 1. exact begrip match (altijd toegestaan)
            target = next((c for c in cards if (c.get("begrip") or "").lower().strip() == lh), None)
            if target:
                break
            # 2. substring alleen voor hints langer dan 3 chars (voorkomt "ei" → "Kleine straat")
            if len(lh) > 3:
                target = next((c for c in cards if lh in (c.get("begrip") or "").lower()), None)
                if target:
                    break
            # 3. tag-exact match (altijd toegestaan)
            target = next((c for c in cards if any(lh == str(t).lower().strip() for t in (c.get("tags") or []))), None)
            if target:
                break
        if not target:
            continue
        gm_old = target.get("game_meta") or {}
        gm_new = {
            "is_item": True,
            "slot": item.get("slot", gm_old.get("slot", "")),
            "weight": item.get("weight", gm_old.get("weight", 0.0)),
            "stats_bonus": item.get("stats_bonus") or gm_old.get("stats_bonus") or {},
            "combat_bonus": item.get("combat_bonus") or gm_old.get("combat_bonus") or {},
            "meta": item.get("meta") or gm_old.get("meta") or {"klasse": "", "beroep": "", "fractie": "", "locatie": ""},
            "value_goud": item.get("value_goud", gm_old.get("value_goud", 0)),
            "rarity": item.get("rarity", gm_old.get("rarity", "common")),
            "kind": item.get("kind", gm_old.get("kind", "")),
        }
        target["game_meta"] = gm_new
        fn = target.setdefault("footnote", {})
        fn["laatst_bewerkt_op"] = _now()
        fn["item_migrated_from"] = item_id
        migrated.append({"card_id": target.get("id"), "begrip": target.get("begrip"), "item_id": item_id})
    _save_game(data)
    return {"success": True, "migrated_count": len(migrated), "migrated": migrated}


# v6_game_seed_001 — Seed draft-kaarten voor ontbrekende slots/items zodat Willem alleen
# nog de echte image hoeft te uploaden + lagen te verfijnen. Placeholder = "Vraag" avatar.
PLACEHOLDER_IMAGE_URL = "/api/avatar/gallery/31c6dc04a2fd/image"


@router.post("/game-cards/seed-missing-items")
async def seed_missing_game_items(user_id: str = "user-001"):
    """
    Genereer DRAFT D&D-kaarten voor alle slots/item-types die nog ontbreken.
    Elke kaart krijgt:
      - placeholder image (Vraag-avatar) — Willem upload later z'n eigen 512x512
      - game_meta.is_item = true met voorgestelde slot/weight/stats
      - laag1 = mijn (Spark's) advies-aanvulling — Willem past aan
      - laag2-4, ws5 = leeg — Willem vult in zonder GPT
    Idempotent: skip-checks op begrip-naam in bestaande kaarten.
    """
    data = _load_game()
    cards = data.get("cards", [])
    existing_begrippen = {(c.get("begrip") or "").lower().strip() for c in cards}

    # Seed-definities: minimum-set items om volledige D&D body-coverage te hebben + basis consumables
    SEED_ITEMS = [
        # === Equipable per slot ===
        {"begrip": "Basis ketting", "slot": "nek", "weight": 0.1, "kind": "armor",
         "stats_bonus": {"wilskracht": 1}, "combat_bonus": {},
         "tags": ["D&D", "nek", "ketting", "sieraad"],
         "laag1": "Eenvoudige koorden-ketting met houten hanger. Geeft een licht beschermend gevoel."},
        {"begrip": "Basis mantel", "slot": "schouders", "weight": 0.8, "kind": "armor",
         "stats_bonus": {}, "combat_bonus": {"verdediging": 2},
         "tags": ["D&D", "schouders", "mantel", "kleding"],
         "laag1": "Wollen mantel die warmte vasthoudt op koude tochten. Biedt lichte bescherming."},
        {"begrip": "Basis armband", "slot": "armen", "weight": 0.1, "kind": "armor",
         "stats_bonus": {"behendigheid": 1}, "combat_bonus": {},
         "tags": ["D&D", "armen", "armband", "sieraad"],
         "laag1": "Leren armband met ijzeren stiftjes. Houdt de mouwen op hun plek."},
        {"begrip": "Basis medaillon", "slot": "trinket", "weight": 0.05, "kind": "trinket",
         "stats_bonus": {"geluk": 1}, "combat_bonus": {},
         "tags": ["D&D", "trinket", "medaillon", "amulet"],
         "laag1": "Bronzen medaillon met onleesbare runen. Voelt warm aan."},
        {"begrip": "Basis sjaal", "slot": "sjaal", "weight": 0.2, "kind": "armor",
         "stats_bonus": {"conditie": 1}, "combat_bonus": {},
         "tags": ["D&D", "sjaal", "doek", "kleding"],
         "laag1": "Stoffen sjaal in fractiekleur. Bedekt nek en gezicht tegen stof en kou."},
        {"begrip": "Basis riem", "slot": "riem", "weight": 0.3, "kind": "armor",
         "stats_bonus": {}, "combat_bonus": {},
         "tags": ["D&D", "riem", "gordel", "kleding"],
         "laag1": "Leren riem met ijzeren gesp. Houdt broek en zwaardschede vast."},
        {"begrip": "Basis handschoenen", "slot": "handen", "weight": 0.2, "kind": "armor",
         "stats_bonus": {}, "combat_bonus": {"verdediging": 1, "aanvalskracht": 1},
         "tags": ["D&D", "handen", "handschoenen", "kleding"],
         "laag1": "Leren handschoenen met geknoopte palmen. Beter grip op wapens."},
        {"begrip": "Basis ring", "slot": "ring_l", "weight": 0.02, "kind": "trinket",
         "stats_bonus": {"intelligentie": 1}, "combat_bonus": {},
         "tags": ["D&D", "ring", "sieraad", "ring_l"],
         "laag1": "Ijzeren ring met klein steentje. Symbool van een ambacht of belofte."},
        {"begrip": "Basis lantaarn", "slot": "offhand", "weight": 0.8, "kind": "tool",
         "stats_bonus": {}, "combat_bonus": {"beweging": -1},
         "tags": ["D&D", "offhand", "lantaarn", "licht"],
         "laag1": "Olielantaarn met glazen kapje. Verlicht donkere paden. 4 uur brandtijd."},
        {"begrip": "Basis boog", "slot": "pijl_boog", "weight": 1.2, "kind": "weapon",
         "stats_bonus": {"behendigheid": 1}, "combat_bonus": {"aanvalskracht": 4, "initiatief": 2},
         "tags": ["D&D", "pijl_boog", "boog", "wapen"],
         "laag1": "Houten kromboog met 10 simpele pijlen. Bereik tot 30 meter."},
        # Rugzak-slot heeft al "Basis rugzak" kaart maar zonder slot — fixen via migration
        # Geen extra rugzak-kaart, want bestaande wordt geupdated.

        # === Voedsel / consumables (geen slot, in rugzak) ===
        {"begrip": "Basis kaas", "slot": "", "weight": 0.3, "kind": "food",
         "stats_bonus": {}, "combat_bonus": {},
         "tags": ["D&D", "voeding", "kaas"], "value_goud": 3,
         "laag1": "Stuk gerijpte boerenkaas. Lichte snack onderweg. Herstelt 15 conditie."},
        {"begrip": "Basis appel", "slot": "", "weight": 0.15, "kind": "food",
         "stats_bonus": {}, "combat_bonus": {},
         "tags": ["D&D", "voeding", "fruit", "appel"], "value_goud": 1,
         "laag1": "Verse rode appel. Herstelt 8 conditie. Licht in dragen."},
        {"begrip": "Basis ei", "slot": "", "weight": 0.08, "kind": "food",
         "stats_bonus": {}, "combat_bonus": {},
         "tags": ["D&D", "voeding", "ei"], "value_goud": 1,
         "laag1": "Vers boerenei. Basis voor maaltijden, kan thuis gebakken worden."},
        {"begrip": "Basis fakkel", "slot": "", "weight": 0.5, "kind": "tool",
         "stats_bonus": {}, "combat_bonus": {},
         "tags": ["D&D", "tool", "fakkel", "licht"], "value_goud": 2,
         "laag1": "Handfakkel met pek-uiteinde. Verlicht donkere ruimtes, brandtijd 30 min."},
        {"begrip": "Basis goudstuk", "slot": "", "weight": 0.01, "kind": "currency",
         "stats_bonus": {}, "combat_bonus": {},
         "tags": ["D&D", "valuta", "goud", "munt"], "value_goud": 1,
         "laag1": "Eén glanzend goudstuk. Universele ruileenheid in Spark World."},
        {"begrip": "Basis heelkruid", "slot": "", "weight": 0.05, "kind": "consumable",
         "stats_bonus": {}, "combat_bonus": {},
         "tags": ["D&D", "kruid", "genezing", "consumable"], "value_goud": 5,
         "laag1": "Gedroogd kruid in linnen zakje. Bij inname: herstelt 25 conditie. 1 gebruik."},
        {"begrip": "Basis touw", "slot": "", "weight": 0.6, "kind": "tool",
         "stats_bonus": {}, "combat_bonus": {},
         "tags": ["D&D", "tool", "touw"], "value_goud": 4,
         "laag1": "10 meter hennep-touw. Onmisbaar bij klimmen of vastbinden."},
    ]

    created = []
    skipped = []
    for seed in SEED_ITEMS:
        if seed["begrip"].lower().strip() in existing_begrippen:
            skipped.append(seed["begrip"])
            continue
        card_id = f"game-{uuid.uuid4().hex[:8]}"
        card = {
            "id": card_id,
            "class": "game",
            "type": "dnd_game_card",
            "begrip": seed["begrip"],
            "sense": "zie",
            "lagen": {"laag1": seed.get("laag1", ""), "laag2": "", "laag3": "", "laag4": ""},
            "ws5": {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""},
            "tags": seed.get("tags", ["D&D"]),
            "media": {
                "voice_url": None,
                "voice_transcript": None,
                "image_urls": [PLACEHOLDER_IMAGE_URL],   # ← placeholder; Willem upload later
            },
            "game_meta": {
                "is_item": True,
                "slot": seed.get("slot", ""),
                "weight": seed.get("weight", 0.0),
                "stats_bonus": seed.get("stats_bonus", {}),
                "combat_bonus": seed.get("combat_bonus", {}),
                "meta": {"klasse": "", "beroep": "", "fractie": "", "locatie": "Overal"},
                "value_goud": seed.get("value_goud", 0),
                "rarity": "common",
                "kind": seed.get("kind", ""),
            },
            "status": "draft",
            "footnote": {
                "bron": "seed_advies",
                "vertrouwen": 0.4,
                "aangemaakt_door": user_id,
                "aangemaakt_op": _now(),
                "laatst_bewerkt_op": _now(),
                "needs_image": True,            # ← markeert dat echte image nog moet komen
                "needs_lagen": True,            # ← markeert dat laag2/3/4 + ws5 nog moet komen
            },
            "needs": ["image", "lagen", "voice"],
        }
        cards.insert(0, card)
        existing_begrippen.add(seed["begrip"].lower().strip())
        created.append({"card_id": card_id, "begrip": seed["begrip"], "slot": seed.get("slot")})

    # Ook: bestaande Basis rugzak kaart updaten met slot="rugzak" als die niet gezet is
    for c in cards:
        if (c.get("begrip") or "").lower().strip() == "basis rugzak":
            gm = c.get("game_meta") or {}
            if gm.get("is_item") and not gm.get("slot"):
                gm["slot"] = "rugzak"
                gm["kind"] = gm.get("kind") or "carry"
                c["game_meta"] = gm

    data["cards"] = cards
    _save_game(data)
    return {
        "success": True,
        "created_count": len(created),
        "skipped_count": len(skipped),
        "placeholder_image_url": PLACEHOLDER_IMAGE_URL,
        "created": created,
        "skipped": skipped,
        "instructie": "Open Kennisbank → D&D-kaarten. Voor elke 'draft' kaart: upload echte image, verfijn lagen + ws5, klik daarna 'lock'.",
    }


# ---------------------------------------------------------------------------
# v6_dorp_layout_overrides_001 — admin kan gebouw-posities slepen op de mini-map
# ---------------------------------------------------------------------------
DORP_LAYOUT_OVERRIDES_PATH = DATA_ROOT / "dnd" / "dorp_layout_overrides.json"


class DorpLayoutOverride(BaseModel):
    overrides: Dict[str, Dict[str, float]]  # {building_id: {"x":pct, "y":pct}}


@router.get("/dorp-layout-overrides")
async def get_dorp_layout_overrides():
    """Lees admin-gedragen building-position overrides voor de Stormhaven mini-map."""
    if not DORP_LAYOUT_OVERRIDES_PATH.exists():
        return {"overrides": {}}
    try:
        data = json.loads(DORP_LAYOUT_OVERRIDES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"overrides": {}}
    return {"overrides": data.get("overrides", {})}


@router.put("/dorp-layout-overrides")
async def put_dorp_layout_overrides(body: DorpLayoutOverride):
    """Sla admin-gedragen building-position overrides op."""
    # Clamp percentages naar [0, 100]
    cleaned: Dict[str, Dict[str, float]] = {}
    for bid, pos in (body.overrides or {}).items():
        x = max(0.0, min(100.0, float(pos.get("x", 50))))
        y = max(0.0, min(100.0, float(pos.get("y", 50))))
        cleaned[str(bid)] = {"x": x, "y": y}
    DORP_LAYOUT_OVERRIDES_PATH.parent.mkdir(parents=True, exist_ok=True)
    DORP_LAYOUT_OVERRIDES_PATH.write_text(
        json.dumps({
            "overrides": cleaned,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"success": True, "count": len(cleaned)}




# ---------------------------------------------------------------------------
# v6_dnd_items_001 — item-blueprint registry voor trade-bark + rugzak.
# Bron: data/dnd/blueprints/dnd_items.json
# ---------------------------------------------------------------------------
ITEMS_BLUEPRINT_PATH = DATA_ROOT / "dnd" / "blueprints" / "dnd_items.json"


@router.get("/items-blueprint")
async def get_items_blueprint():
    """Volledige item-registry. Frontend gebruikt dit voor trade-bark en rugzak-rendering."""
    if not ITEMS_BLUEPRINT_PATH.exists():
        return {"_meta": {}, "items": {}}
    try:
        return json.loads(ITEMS_BLUEPRINT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_meta": {}, "items": {}}


@router.get("/items-blueprint/{item_id}")
async def get_item_blueprint(item_id: str):
    """Eén item uit het register."""
    data = json.loads(ITEMS_BLUEPRINT_PATH.read_text(encoding="utf-8")) if ITEMS_BLUEPRINT_PATH.exists() else {"items": {}}
    item = (data.get("items") or {}).get(item_id)
    if not item:
        raise HTTPException(404, f"Item '{item_id}' niet in blueprint")
    return {"id": item_id, **item}







# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _autotitle(content: str, sense_label: str) -> str:
    snippet = (content or "").strip().split("\n", 1)[0]
    if len(snippet) > 50:
        snippet = snippet[:47].rstrip() + "..."
    return f"{sense_label}: {snippet}" if snippet else sense_label
