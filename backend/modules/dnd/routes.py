"""
D&D Module (v4_dnd_001)

Levende wereld die groeit door gedrag. Niet pre-scripted.

Componenten:
  • lore_index.json — statische lore (avatars-as-functions, behavior-mapping, aura)
  • /data/users/{user_id}/behavior.json — gedragstellers per user (counters)
  • /data/dnd/world_state.json — globale entiteit-sterktes (Reaper / Story Teller / etc)
  • /data/dnd/observations.json — Spark's recente observaties per user (avatar-change, kb-add)

Endpoints:
  GET  /api/dnd/lore                         - statische lore index
  GET  /api/dnd/world-state                  - globale entiteit-sterktes
  GET  /api/dnd/aura/{user_id}               - berekende aura (top 3 behaviors → kleur)
  POST /api/dnd/track                        - increment behavior counter
  GET  /api/dnd/observations/{user_id}       - recente observaties van Spark over deze user
  POST /api/dnd/observe                      - log observatie (intern, ook door andere modules)
"""
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/dnd", tags=["dnd"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
LORE_FILE = DATA_ROOT / "dnd" / "lore_index.json"
WORLD_FILE = DATA_ROOT / "dnd" / "world_state.json"
OBS_FILE = DATA_ROOT / "dnd" / "observations.json"
USERS_DIR = DATA_ROOT / "users"


# ============== HELPERS ==============
def _behavior_path(user_id: str) -> Path:
    d = USERS_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "behavior.json"


def _load_behavior(user_id: str) -> dict:
    return load_json(_behavior_path(user_id), default={"counters": {}, "started_at": datetime.now(timezone.utc).isoformat()})


def _save_behavior(user_id: str, data: dict) -> None:
    save_json(_behavior_path(user_id), data)


def _load_lore() -> dict:
    return load_json(LORE_FILE, default={"avatars_as_functions": [], "behavior_to_unlock": {}})


def _aura_for_user(user_id: str) -> dict:
    """Bereken aura: top behavior-categorie → kleur, plus secondaire en particles."""
    behavior = _load_behavior(user_id)
    counters = behavior.get("counters", {})
    lore = _load_lore()
    mapping = lore.get("behavior_to_unlock", {})

    # Bereken score per categorie = som van counters voor zijn tracker_keys
    cat_scores: Dict[str, int] = {}
    for cat_id, cat in mapping.items():
        score = sum(counters.get(k, 0) for k in cat.get("tracker_keys", []))
        if score > 0:
            cat_scores[cat_id] = score

    sorted_cats = sorted(cat_scores.items(), key=lambda x: -x[1])
    top = sorted_cats[:3]
    total = sum(s for _, s in cat_scores.items()) or 1
    layers = []
    for cat_id, score in top:
        cat = mapping.get(cat_id, {})
        layers.append({
            "category": cat_id,
            "label": cat.get("label", cat_id),
            "color": cat.get("aura", "#94a3b8"),
            "score": score,
            "ratio": round(score / total, 3),
        })
    # Default als nog geen behavior
    if not layers:
        layers = [{
            "category": "leeg",
            "label": "Leeg / nog ongevormd",
            "color": "#475569",
            "score": 0,
            "ratio": 0,
        }]
    # Unlocks van de top categorie
    top_cat = top[0][0] if top else None
    unlocks = mapping.get(top_cat, {}).get("unlocks", []) if top_cat else []
    return {
        "user_id": user_id,
        "layers": layers,
        "primary_color": layers[0]["color"],
        "unlocks": unlocks[:5],
        "total_events": total if cat_scores else 0,
    }


def _recompute_world() -> dict:
    """Bereken sterkte per entiteit op basis van alle user-counters."""
    lore = _load_lore()
    avatars = lore.get("avatars_as_functions", [])
    # Per entiteit: tel events die mappen op zijn growth_trigger via tags
    # Voor MVP: gebruik simpele heuristieken via bekende tracker_keys
    entity_scores: Dict[str, int] = {}
    if not USERS_DIR.exists():
        return {"entities": [], "computed_at": datetime.now(timezone.utc).isoformat()}
    # Tel ALLE counters voor alle users
    total_counters: Dict[str, int] = {}
    for user_dir in USERS_DIR.iterdir():
        if not user_dir.is_dir():
            continue
        b = load_json(user_dir / "behavior.json", default={"counters": {}})
        for k, v in b.get("counters", {}).items():
            total_counters[k] = total_counters.get(k, 0) + v

    # Mapping van counters → entity (heuristic / rough proxy)
    proxies = {
        "Het Eerste Licht": ["kb_create", "story_share", "lore_anchor"],
        "De Reaper": ["kb_archive", "delete_action"],
        "De Boekhouder": ["trade_event", "fee_extraction", "wallet_mutate"],
        "Harry Klokkenmaker": ["agenda_event", "scheduled_task"],
        "Madelief Stouten": ["help_msg", "bijdrage_create", "snap_share"],
        "Mr Smith": ["lie_detected", "manipulate_attempt"],
        "The Story Teller": ["kb_create", "story_share", "long_read"],
    }
    for name, keys in proxies.items():
        entity_scores[name] = sum(total_counters.get(k, 0) for k in keys)

    grand_total = sum(entity_scores.values()) or 1
    entities = []
    for av in avatars:
        score = entity_scores.get(av["name"], 0)
        entities.append({
            "name": av["name"],
            "function": av["function"],
            "aura": av.get("aura"),
            "user_id": av.get("user_id"),
            "score": score,
            "ratio": round(score / grand_total, 3) if grand_total else 0,
            "dominant": (score / grand_total) > 0.6 if grand_total else False,
        })
    entities.sort(key=lambda e: -e["score"])
    state = {
        "entities": entities,
        "grand_total": grand_total,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
    save_json(WORLD_FILE, state)
    return state


# ============== MODELS ==============
class TrackBody(BaseModel):
    user_id: str
    counter_key: str
    delta: int = 1


class ObserveBody(BaseModel):
    user_id: str
    kind: str          # bv. "avatar_changed" | "kb_added" | "first_login_today"
    detail: Optional[Dict] = None


# ============== ROUTES ==============
@router.get("/lore")
async def get_lore():
    return _load_lore()


@router.post("/track")
async def track_behavior(body: TrackBody):
    """Increment een behavior-counter (idempotent veilig)."""
    if body.delta < 0 and body.delta > -1000:
        pass
    data = _load_behavior(body.user_id)
    counters = data.get("counters", {})
    counters[body.counter_key] = counters.get(body.counter_key, 0) + body.delta
    if counters[body.counter_key] < 0:
        counters[body.counter_key] = 0
    data["counters"] = counters
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    _save_behavior(body.user_id, data)
    return {"success": True, "counters": counters}


@router.get("/aura/{user_id}")
async def get_aura(user_id: str):
    return _aura_for_user(user_id)


@router.get("/world-state")
async def world_state():
    """Top entiteiten + dominantie. Hercomputeer altijd verse waarden."""
    return _recompute_world()


@router.post("/observe")
async def observe(body: ObserveBody):
    """Log een Spark-observatie. Spark gebruikt deze later om iemand te begroeten."""
    data = load_json(OBS_FILE, default={"events": []})
    ev = {
        "user_id": body.user_id,
        "kind": body.kind,
        "detail": body.detail or {},
        "ts": datetime.now(timezone.utc).isoformat(),
        "spoken": False,
    }
    events = data.get("events", []) + [ev]
    # Behoud max 200 events
    if len(events) > 200:
        events = events[-200:]
    data["events"] = events
    save_json(OBS_FILE, data)
    return {"success": True, "event": ev}


@router.get("/observations/{user_id}")
async def list_observations(user_id: str, only_unspoken: bool = True, limit: int = 5):
    """Wat heeft Spark de laatste tijd over deze user opgemerkt?"""
    data = load_json(OBS_FILE, default={"events": []})
    events: List[dict] = data.get("events", [])
    mine = [e for e in events if e.get("user_id") == user_id]
    if only_unspoken:
        mine = [e for e in mine if not e.get("spoken")]
    mine.sort(key=lambda e: e.get("ts", ""), reverse=True)
    return {"observations": mine[:limit], "total_for_user": len(mine)}


class MarkSpokenBody(BaseModel):
    user_id: str
    kinds: Optional[List[str]] = None  # bv. ['avatar_changed'] – None = alle


@router.post("/observations/mark-spoken")
async def mark_spoken(body: MarkSpokenBody):
    data = load_json(OBS_FILE, default={"events": []})
    changed = 0
    for e in data.get("events", []):
        if e.get("user_id") != body.user_id:
            continue
        if body.kinds and e.get("kind") not in body.kinds:
            continue
        if not e.get("spoken"):
            e["spoken"] = True
            changed += 1
    save_json(OBS_FILE, data)
    return {"success": True, "marked": changed}


@router.get("/spark-greeting/{user_id}")
async def spark_greeting(user_id: str):
    """Genereer greeting waarin Spark recente observaties benoemt.

    Wordt gebruikt door Spark AI tab bij eerste keer openen in een sessie.
    Marked observaties als 'spoken' zodat Spark niet herhaalt.
    """
    obs_data = load_json(OBS_FILE, default={"events": []})
    mine = [e for e in obs_data.get("events", [])
            if e.get("user_id") == user_id and not e.get("spoken")]
    mine.sort(key=lambda e: e.get("ts", ""), reverse=True)
    # Pak max 3 meest recente unieke kinds
    seen_kinds = set()
    selected = []
    for e in mine:
        if e["kind"] in seen_kinds:
            continue
        seen_kinds.add(e["kind"])
        selected.append(e)
        if len(selected) >= 3:
            break

    if not selected:
        return {"has_greeting": False, "message": None, "events": []}

    parts: List[str] = ["Ik merkte iets op terwijl je weg was."]
    for e in selected:
        kind = e["kind"]
        det = e.get("detail") or {}
        if kind == "avatar_changed":
            title = det.get("title") or "een nieuwe"
            parts.append(f"Je koos een nieuwe avatar — *{title}*. Past bij je vibe vandaag?")
        elif kind == "kb_added":
            begrip = det.get("begrip") or "een nieuw begrip"
            parts.append(f"Je hebt **{begrip}** toegevoegd aan de kennisbank. The Story Teller groeit.")
        elif kind == "first_login_today":
            parts.append("Goed je weer te zien.")
        elif kind == "trade_event":
            mark = det.get("market") or "een potje"
            parts.append(f"De Boekhouder zag een trade-event op {mark}.")
        elif kind == "achievement_unlocked":
            naam = det.get("naam") or det.get("code") or "iets"
            parts.append(f"Achievement unlocked: **{naam}**! 🏅")
        else:
            parts.append(f"Iets nieuws gebeurde: {kind}.")

    # Mark als gesproken zodat Spark niet herhaalt
    for e in obs_data.get("events", []):
        if e.get("user_id") == user_id and not e.get("spoken"):
            if any(s["ts"] == e.get("ts") for s in selected):
                e["spoken"] = True
    save_json(OBS_FILE, obs_data)

    return {
        "has_greeting": True,
        "message": " ".join(parts),
        "events": selected,
    }
