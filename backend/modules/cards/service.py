"""
Card Factory Service (v5_card_factory_001)
============================================
Generieke service voor maakbare "game-style" kaarten naast kennis-kaarten:

  • dnd     — D&D-game-kaart (vraag/antwoord, beeld, geluid)
  • event   — Event-kaart (community-event uitnodiging)
  • bark    — Bark-kaart (proactief bot-bericht template)

Verschil met KB v2 kaarten:
  • Geen lade-classifier — type is fixed bij creatie
  • 2 kaders: 'vraag' + 'antwoord' (1 hoeft ingevuld om hook te triggeren)
  • Media-velden net als KB v2 (afbeelding, geluid)
  • Opgeslagen in /data/cards/{type}/{id}.json + media via system_archive
    met tag 'card_<type>' + linked_card_id

Schema:
  {
    "id": "card-dnd-xxx",
    "type": "dnd"|"event"|"bark",
    "titel": "...",
    "vraag": "...",       (optioneel)
    "antwoord": "...",    (optioneel — minstens 1 van beiden vereist)
    "media": {
      "image_url": "...",  (system_archive /api/...)
      "audio_url": "...",  (system_archive)
    },
    "tags": [...],
    "status": "draft"|"active"|"archived",
    "footnote": {
      "aangemaakt_door": "user-001",
      "aangemaakt_op": "iso",
      "laatst_bewerkt": "iso",
      "trigger_count": 0,   (hoe vaak deze kaart fired)
    },
    # type-specifieke velden:
    "dnd": { "verteller": "user-000", "scene": "...", "rewards": [...] },
    "event": { "datum": "...", "locatie": "...", "deelnemers": [...] },
    "bark": { "bot": "bot-boekhouder", "trigger_text": "...", "schedule": "..." }
  }
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json
from modules.core.spark_logger import traced, log_event

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
CARDS_ROOT = DATA_ROOT / "cards"

VALID_TYPES = {"dnd", "event", "bark"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _index_path(card_type: str) -> Path:
    return CARDS_ROOT / card_type / "_index.json"


def _card_path(card_type: str, card_id: str) -> Path:
    return CARDS_ROOT / card_type / f"{card_id}.json"


def _load_index(card_type: str) -> Dict:
    return load_json(_index_path(card_type), default={"cards": [], "updated_at": None})


def _save_index(card_type: str, idx: Dict):
    idx["updated_at"] = _now()
    save_json(_index_path(card_type), idx)


# ---------------------------------------------------------------------------
# Create / Read / Update / Delete
# ---------------------------------------------------------------------------

@traced(intent="game-kaart aanmaken (DnD/Event/Bark)", module="cards")
def create_card(card_type: str, titel: str, user_id: str = "user-000",
                vraag: Optional[str] = None, antwoord: Optional[str] = None,
                extra: Optional[Dict] = None) -> Dict:
    if card_type not in VALID_TYPES:
        return {"success": False, "message": f"Onbekend type '{card_type}'. Geldig: {sorted(VALID_TYPES)}"}
    if not (vraag or antwoord):
        # Mag ook leeg gestart worden — wordt 'draft'. Bij invullen via PATCH triggert hook.
        pass

    card_id = f"card-{card_type}-{uuid.uuid4().hex[:8]}"
    now = _now()
    card = {
        "id": card_id,
        "type": card_type,
        "titel": titel.strip(),
        "vraag": (vraag or "").strip(),
        "antwoord": (antwoord or "").strip(),
        "media": {"image_url": None, "audio_url": None},
        "tags": [],
        "status": "draft" if not (vraag or antwoord) else "active",
        "footnote": {
            "aangemaakt_door": user_id,
            "aangemaakt_op": now,
            "laatst_bewerkt": now,
            "trigger_count": 0,
        },
    }
    if extra and isinstance(extra, dict):
        card[card_type] = {**(extra or {})}

    # Persist
    CARDS_ROOT.joinpath(card_type).mkdir(parents=True, exist_ok=True)
    save_json(_card_path(card_type, card_id), card)
    idx = _load_index(card_type)
    idx.setdefault("cards", []).append({
        "id": card_id, "titel": card["titel"], "status": card["status"],
        "created_at": now, "has_vraag": bool(card["vraag"]), "has_antwoord": bool(card["antwoord"]),
    })
    _save_index(card_type, idx)

    return {"success": True, "card": card}


def get_card(card_type: str, card_id: str) -> Optional[Dict]:
    if card_type not in VALID_TYPES:
        return None
    fp = _card_path(card_type, card_id)
    if not fp.exists():
        return None
    return load_json(fp, default=None)


def list_cards(card_type: str, status: Optional[str] = None) -> List[Dict]:
    idx = _load_index(card_type)
    cards = idx.get("cards", [])
    if status:
        cards = [c for c in cards if c.get("status") == status]
    return sorted(cards, key=lambda c: c.get("created_at", ""), reverse=True)


@traced(intent="game-kaart bewerken + hook-chain", module="cards")
def update_card(card_type: str, card_id: str, updates: Dict, user_id: str = "user-000") -> Dict:
    card = get_card(card_type, card_id)
    if not card:
        return {"success": False, "message": "Niet gevonden"}

    pre_filled = bool((card.get("vraag") or "").strip() or (card.get("antwoord") or "").strip())

    # Apply allowed fields
    for k in ("titel", "vraag", "antwoord", "tags"):
        if k in updates and updates[k] is not None:
            card[k] = updates[k].strip() if isinstance(updates[k], str) else updates[k]
    if "media" in updates and isinstance(updates["media"], dict):
        card["media"] = {**(card.get("media") or {}), **updates["media"]}
    if card_type in updates and isinstance(updates[card_type], dict):
        card[card_type] = {**(card.get(card_type) or {}), **updates[card_type]}
    if "status" in updates and updates["status"] in {"draft", "active", "archived"}:
        card["status"] = updates["status"]

    post_filled = bool((card.get("vraag") or "").strip() or (card.get("antwoord") or "").strip())

    # Auto status: draft → active wanneer eerste kader ingevuld
    if not pre_filled and post_filled and card["status"] == "draft":
        card["status"] = "active"

    card["footnote"]["laatst_bewerkt"] = _now()
    card["footnote"]["laatst_bewerkt_door"] = user_id

    save_json(_card_path(card_type, card_id), card)

    # Update index entry
    idx = _load_index(card_type)
    for e in idx.get("cards", []):
        if e.get("id") == card_id:
            e["titel"] = card["titel"]
            e["status"] = card["status"]
            e["has_vraag"] = bool(card["vraag"])
            e["has_antwoord"] = bool(card["antwoord"])
            break
    _save_index(card_type, idx)

    # ========== HOOK CHAIN ==========
    # Trigger wanneer vraag OF antwoord nieuw ingevuld werd (draft→active overgang)
    hooks_fired = []
    if not pre_filled and post_filled:
        try:
            hook_result = _fire_card_hooks(card)
            hooks_fired = hook_result.get("fired", [])
        except Exception as e:
            log_event("cards", "hook_chain_error", intent="kaart hook chain", detail={"error": str(e)})

    return {"success": True, "card": card, "hooks_fired": hooks_fired}


@traced(intent="game-kaart + media verwijderen", module="cards")
def delete_card(card_type: str, card_id: str) -> Dict:
    card = get_card(card_type, card_id)
    if not card:
        return {"success": False, "message": "Niet gevonden"}
    # Cascade: media in system_archive met linked_card_id == card_id opruimen
    cleaned_media = _cleanup_linked_media(card_id)
    # Verwijder JSON
    fp = _card_path(card_type, card_id)
    try:
        fp.unlink()
    except Exception:
        pass
    # Index opschonen
    idx = _load_index(card_type)
    idx["cards"] = [c for c in idx.get("cards", []) if c.get("id") != card_id]
    _save_index(card_type, idx)
    return {"success": True, "removed_media": cleaned_media}


def _cleanup_linked_media(card_id: str) -> int:
    """Verwijder alle system_archive entries met linked_card_id == card_id."""
    sa_index = DATA_ROOT / "system_archive" / "_index.json"
    if not sa_index.exists():
        return 0
    data = load_json(sa_index, default={"files": []})
    keep, removed = [], 0
    for f in data.get("files", []):
        if f.get("linked_card_id") == card_id:
            try:
                Path(f.get("path", "")).unlink(missing_ok=True)
                removed += 1
            except Exception:
                pass
        else:
            keep.append(f)
    data["files"] = keep
    data["updated_at"] = _now()
    save_json(sa_index, data)
    return removed


# ---------------------------------------------------------------------------
# Hook chain — wat gebeurt er als een kaart "active" wordt
# ---------------------------------------------------------------------------

def _fire_card_hooks(card: Dict) -> Dict:
    """Centrale chain: bij draft→active fire we type-specifieke triggers.
    Elke hook is failsoft."""
    fired = []
    ct = card.get("type")
    if ct == "dnd":
        fired.append(_hook_dnd_register(card))
    elif ct == "event":
        fired.append(_hook_event_announce(card))
    elif ct == "bark":
        fired.append(_hook_bark_register(card))
    log_event("cards", "hook_chain", intent=f"kaart {card['id']} active, hooks fired",
              detail={"card_id": card["id"], "type": ct, "fired": fired})
    return {"fired": [f for f in fired if f]}


def _hook_dnd_register(card: Dict) -> Optional[str]:
    """Registreer D&D-kaart in lore_index zodat verteller (De Dood) hem kan gebruiken.
    TODO P2: link aan kbv2.weten via shared tag 'lore'."""
    # Voor nu: log + return name. Echte index-update later.
    return "dnd_lore_registered"


def _hook_event_announce(card: Dict) -> Optional[str]:
    """Maak community-bark dat event live is."""
    try:
        from modules.bots.proactive_barks import _append_community_message
        msg = {
            "id": str(uuid.uuid4()),
            "user_id": "bot-boekhouder",
            "user_name": "De Boekhouder",
            "message": f"📅 Nieuw event: **{card.get('titel', '?')}**. "
                       + (card.get("vraag") or card.get("antwoord") or ""),
            "is_bot": True,
            "timestamp": _now(),
            "bark_kind": "event_announce",
            "linked_card_id": card["id"],
        }
        _append_community_message(msg)
        return "event_announced_in_community"
    except Exception:
        return None


def _hook_bark_register(card: Dict) -> Optional[str]:
    """Registreer bark-template zodat bot hem kan firen wanneer trigger-text matcht.
    TODO P2: voeg toe aan check_bot_triggers in routes.py."""
    return "bark_template_registered"
