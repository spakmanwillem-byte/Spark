"""
Spark World Fracties & Provincies (v6_dnd_fracties_001)

9 fracties met element-alignment, en mapping op de 12 NL-provincies.

JSON: /app/backend/data/dnd/fracties.json (statisch, baseline)
JSON: /app/backend/data/dnd/provincies.json (provincie → fractie binding, editable)
JSON: /app/backend/data/dnd/grondstoffen.json (resources op de map, editable)
"""
import uuid
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/dnd/world", tags=["dnd-world"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
FRACTIES_FILE = DATA_ROOT / "dnd" / "fracties.json"
PROVINCIES_FILE = DATA_ROOT / "dnd" / "provincies.json"
USERS_FILE = DATA_ROOT / "system" / "users.json"

# v6_dnd_fracties_001 — 9 fracties, kleur + element + alignment
FRACTIES_BASELINE = [
    {"id": "spark",    "naam": "Spark",     "kleur": "#f59e0b", "element": "spark",   "alignment": "neutraal", "leider": "Spark",         "is_main": True,  "beschrijving": "De centrale fractie. Hoofdstad: Stormhaven."},
    {"id": "licht",    "naam": "Licht",     "kleur": "#fde68a", "element": "licht",   "alignment": "licht",    "leider": "—",             "is_main": False, "beschrijving": "Hoofd-fractie van het licht."},
    {"id": "schaduw",  "naam": "Schaduw",   "kleur": "#7c3aed", "element": "schaduw", "alignment": "schaduw",  "leider": "—",             "is_main": False, "beschrijving": "Hoofd-fractie van de schaduw."},
    {"id": "vuur",     "naam": "Vuur",      "kleur": "#dc2626", "element": "vuur",    "alignment": "licht",    "leider": "—",             "is_main": False, "beschrijving": "Element Vuur (Licht-aligned)."},
    {"id": "lucht",    "naam": "Lucht",     "kleur": "#06b6d4", "element": "lucht",   "alignment": "licht",    "leider": "—",             "is_main": False, "beschrijving": "Element Lucht (Licht-aligned)."},
    {"id": "water",    "naam": "Water",     "kleur": "#3b82f6", "element": "water",   "alignment": "schaduw",  "leider": "—",             "is_main": False, "beschrijving": "Element Water (Schaduw-aligned)."},
    {"id": "aarde",    "naam": "Aarde",     "kleur": "#78350f", "element": "aarde",   "alignment": "schaduw",  "leider": "—",             "is_main": False, "beschrijving": "Element Aarde (Schaduw-aligned)."},
    {"id": "natuur",   "naam": "Natuur",    "kleur": "#22c55e", "element": "natuur",  "alignment": "licht",    "leider": "—",             "is_main": False, "beschrijving": "Natuur (Licht-aligned, niet-element). Tegenpool van Barbaren."},
    {"id": "barbaren", "naam": "Barbaren",  "kleur": "#991b1b", "element": "barbaren","alignment": "schaduw",  "leider": "—",             "is_main": False, "beschrijving": "Barbaren (Schaduw-aligned, niet-element). Tegenpool van Natuur."},
    {"id": "neutraal", "naam": "Neutraal",  "kleur": "#94a3b8", "element": "—",       "alignment": "—",        "leider": "—",             "is_main": False, "beschrijving": "Veroverbare regio. Nog geen fractie geclaimd."},
]

# v6_dnd_provincies_001 — 12 provincies met default-mapping op fracties
# Groningen = Stormhaven = Spark (hoofdstad)
# Andere wijs ik symbolisch toe; admin kan herzien via drag-edit + fractie-pick
PROVINCIES_BASELINE = [
    {"id": "groningen",     "naam": "Groningen",     "hoofdstad": "Stormhaven",       "fractie_id": "spark",    "x_pct": 78, "y_pct": 18},
    {"id": "friesland",     "naam": "Friesland",     "hoofdstad": "Leeuwarden",       "fractie_id": "lucht",    "x_pct": 60, "y_pct": 22},
    {"id": "drenthe",       "naam": "Drenthe",       "hoofdstad": "Assen",            "fractie_id": "aarde",    "x_pct": 76, "y_pct": 32},
    {"id": "overijssel",    "naam": "Overijssel",    "hoofdstad": "Zwolle",           "fractie_id": "natuur",   "x_pct": 72, "y_pct": 44},
    {"id": "flevoland",     "naam": "Flevoland",     "hoofdstad": "Lelystad",         "fractie_id": "water",    "x_pct": 58, "y_pct": 42},
    {"id": "gelderland",    "naam": "Gelderland",    "hoofdstad": "Arnhem",           "fractie_id": "vuur",     "x_pct": 68, "y_pct": 55},
    {"id": "utrecht",       "naam": "Utrecht",       "hoofdstad": "Utrecht",          "fractie_id": "licht",    "x_pct": 55, "y_pct": 55},
    {"id": "noord-holland", "naam": "Noord-Holland", "hoofdstad": "Haarlem",          "fractie_id": "neutraal", "x_pct": 44, "y_pct": 40},
    {"id": "zuid-holland",  "naam": "Zuid-Holland",  "hoofdstad": "Den Haag",         "fractie_id": "neutraal", "x_pct": 42, "y_pct": 58},
    {"id": "zeeland",       "naam": "Zeeland",       "hoofdstad": "Middelburg",       "fractie_id": "neutraal", "x_pct": 38, "y_pct": 74},
    {"id": "noord-brabant", "naam": "Noord-Brabant", "hoofdstad": "'s-Hertogenbosch", "fractie_id": "schaduw",  "x_pct": 56, "y_pct": 76},
    {"id": "limburg",       "naam": "Limburg",       "hoofdstad": "Maastricht",       "fractie_id": "barbaren", "x_pct": 70, "y_pct": 88},
]

# v6_dnd_rarity_001 — WoW-style 5 rarity-tiers
RARITY_TIERS = [
    {"id": "common",    "naam": "Common",    "kleur": "#9ca3af", "spawn_pct": 60, "glow": "0 0 6px rgba(156,163,175,0.4)"},
    {"id": "uncommon",  "naam": "Uncommon",  "kleur": "#22c55e", "spawn_pct": 25, "glow": "0 0 8px rgba(34,197,94,0.5)"},
    {"id": "rare",      "naam": "Rare",      "kleur": "#3b82f6", "spawn_pct": 10, "glow": "0 0 10px rgba(59,130,246,0.6)"},
    {"id": "epic",      "naam": "Epic",      "kleur": "#a855f7", "spawn_pct": 4,  "glow": "0 0 14px rgba(168,85,247,0.7)"},
    {"id": "legendary", "naam": "Legendary", "kleur": "#f59e0b", "spawn_pct": 1,  "glow": "0 0 18px rgba(245,158,11,0.85)"},
]


def _is_admin(user_id: Optional[str]) -> bool:
    if not user_id:
        return False
    users = load_json(USERS_FILE, default={"users": []}).get("users", [])
    u = next((x for x in users if x.get("id") == user_id), None)
    return bool(u and (u.get("gradatie", 99) <= 2))


def _load_fracties() -> List[dict]:
    FRACTIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(FRACTIES_FILE, default={})
    if not data or "fracties" not in data:
        data = {"fracties": [dict(f) for f in FRACTIES_BASELINE]}
        save_json(FRACTIES_FILE, data)
    return data.get("fracties", [])


def _load_provincies() -> List[dict]:
    PROVINCIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(PROVINCIES_FILE, default={})
    if not data or "provincies" not in data:
        data = {"provincies": [dict(p) for p in PROVINCIES_BASELINE], "updated_at": None}
        save_json(PROVINCIES_FILE, data)
    return data.get("provincies", [])


STEDEN_FILE = DATA_ROOT / "dnd" / "steden.json"
GRONDSTOFFEN_FILE = DATA_ROOT / "dnd" / "grondstoffen.json"


def _load_steden() -> List[dict]:
    """v6_dnd_fracties_tab_001 — laad steden.json (kan leeg zijn)."""
    STEDEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(STEDEN_FILE, default={"steden": []})
    return data.get("steden", []) or []


def _compute_fractie_stats(fracties: List[dict], steden: List[dict]) -> List[dict]:
    """Aggregeer fractie-stats over alle steden:
    - aanhangers_total = sum van fractie_invloed[f.id].aanhangers over alle steden
    - leidende_steden_count = aantal steden waar leidende_fractie_id == f.id
    - gebouwen_total = sum gebouwen die deze fractie bezit
    Eigen 'goud' blijft uit fracties.json (treasury), niet auto-overschreven.
    """
    out = []
    for f in fracties:
        fid = f.get("id")
        aanh = 0
        geb = 0
        for s in steden:
            inv = (s.get("fractie_invloed") or {}).get(fid) or {}
            aanh += int(inv.get("aanhangers") or 0)
            geb += int(inv.get("gebouwen") or 0)
        leidend = sum(1 for s in steden if s.get("leidende_fractie_id") == fid)
        f2 = dict(f)
        stats = dict(f.get("stats") or {})
        stats["aanhangers_total"] = aanh
        stats["leidende_steden_count"] = leidend
        stats["gebouwen_total"] = geb
        f2["stats"] = stats
        out.append(f2)
    return out


# ===== MODELS =====
class ProvincieUpdate(BaseModel):
    id: str
    fractie_id: Optional[str] = None
    hoofdstad: Optional[str] = None
    x_pct: Optional[float] = None
    y_pct: Optional[float] = None


class ProvinciesPatch(BaseModel):
    user_id: str
    updates: List[ProvincieUpdate]


# ===== ROUTES =====
@router.get("/rarities")
async def get_rarities():
    return {"rarities": RARITY_TIERS}


@router.get("/fracties")
async def get_fracties():
    return {"fracties": _load_fracties()}


# v6_dnd_fracties_tab_001 — fracties met live-aggregated stats vanuit steden.json
@router.get("/fracties/full")
async def get_fracties_full():
    """Fracties + automatisch berekende stats (aanhangers, leidende steden, gebouwen).
    Voor de Fracties-tab UI."""
    fracties = _load_fracties()
    steden = _load_steden()
    fracties_enriched = _compute_fractie_stats(fracties, steden)
    return {
        "fracties": fracties_enriched,
        "steden_count": len(steden),
    }


# v6_dnd_fracties_tab_001 — steden lijst
@router.get("/steden")
async def get_steden():
    """Alle steden + minimal provincie/fractie info voor map en lijsten."""
    steden = _load_steden()
    provincies = _load_provincies()
    prov_by_id = {p["id"]: p for p in provincies}
    out = []
    for s in steden:
        prov = prov_by_id.get(s.get("provincie_id")) or {}
        out.append({
            **s,
            "provincie_naam": prov.get("naam", ""),
        })
    return {"steden": out, "provincies": provincies, "fracties": _load_fracties()}


@router.get("/steden/{stad_id}")
async def get_stad(stad_id: str):
    """Volledig detail van één stad, inclusief fractie-info."""
    steden = _load_steden()
    s = next((x for x in steden if x.get("id") == stad_id), None)
    if not s:
        raise HTTPException(404, f"Stad '{stad_id}' niet gevonden")
    fracties = {f["id"]: f for f in _load_fracties()}
    invloed_ranked = sorted(
        ((fid, inv) for fid, inv in (s.get("fractie_invloed") or {}).items()),
        key=lambda x: -(x[1].get("aanhangers", 0) or 0)
    )
    return {
        "stad": s,
        "leidende_fractie": fracties.get(s.get("leidende_fractie_id")),
        "fractie_ranking": [
            {"fractie": fracties.get(fid), "invloed": inv}
            for fid, inv in invloed_ranked
        ],
    }


@router.get("/provincies")
async def get_provincies():
    return {"provincies": _load_provincies(), "fracties": _load_fracties()}


@router.patch("/provincies")
async def patch_provincies(req: ProvinciesPatch):
    """Admin: update fractie/coördinaten van één of meer provincies."""
    if not _is_admin(req.user_id):
        raise HTTPException(403, "Alleen admin kan provincies wijzigen")
    provincies = _load_provincies()
    by_id = {p["id"]: p for p in provincies}
    for upd in req.updates:
        if upd.id not in by_id:
            continue
        p = by_id[upd.id]
        if upd.fractie_id is not None:
            p["fractie_id"] = upd.fractie_id
        if upd.hoofdstad is not None:
            p["hoofdstad"] = upd.hoofdstad
        if upd.x_pct is not None:
            p["x_pct"] = float(upd.x_pct)
        if upd.y_pct is not None:
            p["y_pct"] = float(upd.y_pct)
    data = {
        "provincies": list(by_id.values()),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": req.user_id,
    }
    save_json(PROVINCIES_FILE, data)
    return data


@router.post("/provincies/reset")
async def reset_provincies(req: dict):
    if not _is_admin(req.get("user_id")):
        raise HTTPException(403, "Alleen admin")
    data = {
        "provincies": [dict(p) for p in PROVINCIES_BASELINE],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": req.get("user_id"),
    }
    save_json(PROVINCIES_FILE, data)
    return data


# ===========================================================================
# v6_dnd_steden_drag_001 — Steden PATCH (admin: x_pct/y_pct + andere velden)
# ===========================================================================
class StadUpdateBody(BaseModel):
    user_id: str
    x_pct: Optional[float] = None
    y_pct: Optional[float] = None
    naam: Optional[str] = None
    introductie: Optional[str] = None
    leidende_fractie_id: Optional[str] = None
    banner_image_url: Optional[str] = None
    logo_url: Optional[str] = None


@router.patch("/steden/{stad_id}")
async def patch_stad(stad_id: str, body: StadUpdateBody):
    """Admin: update coördinaten of metadata van één stad (b.v. Leeuwarden drag-and-drop)."""
    if not _is_admin(body.user_id):
        raise HTTPException(403, "Alleen admin kan steden wijzigen")
    data = load_json(STEDEN_FILE, default={"steden": []})
    steden = data.get("steden", [])
    target = next((s for s in steden if s.get("id") == stad_id), None)
    if not target:
        raise HTTPException(404, f"Stad '{stad_id}' niet gevonden")
    if body.x_pct is not None or body.y_pct is not None:
        kaart = target.setdefault("kaart", {})
        if body.x_pct is not None:
            kaart["x_pct"] = float(body.x_pct)
        if body.y_pct is not None:
            kaart["y_pct"] = float(body.y_pct)
    for field in ("naam", "introductie", "leidende_fractie_id", "banner_image_url", "logo_url"):
        val = getattr(body, field)
        if val is not None:
            target[field] = val
    data["steden"] = steden
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(STEDEN_FILE, data)
    return {"success": True, "stad": target}


# ===========================================================================
# v6_dnd_resources_001 — Grondstoffen (vis, bos, akker, mijn, …) op de kaart
# Upload image → opslaan in system_archive + auto-create KB v2 inbox kaart
# ===========================================================================
SA_DIR = DATA_ROOT / "system_archive"
SA_INDEX = SA_DIR / "_index.json"
GAME_FILE = DATA_ROOT / "cards" / "dnd" / "game.json"
KB_INBOX = DATA_ROOT / "knowledge" / "v2" / "inbox.json"
ALLOWED_IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAX_IMAGE_MB = 8

# Resource types met default-config (icon hint, kleur, beschrijving)
RESOURCE_TYPES = [
    {"id": "vis",         "naam": "Visgrond",      "kleur": "#3b82f6", "icon": "fish",     "beschrijving": "Visrijke wateren — kustlijn of meer."},
    {"id": "bos",         "naam": "Bos",           "kleur": "#15803d", "icon": "tree",     "beschrijving": "Hout en wildbestand — duurzame oogst."},
    {"id": "akker",       "naam": "Akker",         "kleur": "#ca8a04", "icon": "wheat",    "beschrijving": "Vruchtbare grond — graan en gewassen."},
    {"id": "mijn",        "naam": "Mijn",          "kleur": "#737373", "icon": "pickaxe",  "beschrijving": "Ondergrondse rijkdom — erts en edelstenen."},
    {"id": "weide",       "naam": "Weide",         "kleur": "#65a30d", "icon": "grass",    "beschrijving": "Grasland voor vee — wol en melk."},
    {"id": "kruid",       "naam": "Kruidenveld",   "kleur": "#a3e635", "icon": "leaf",     "beschrijving": "Geneeskrachtige kruiden — alchemie."},
    {"id": "steen",       "naam": "Steengroeve",   "kleur": "#a8a29e", "icon": "rock",     "beschrijving": "Bouwsteen voor stadsmuren en gebouwen."},
    {"id": "wild",        "naam": "Wildgebied",    "kleur": "#b45309", "icon": "boar",     "beschrijving": "Jachtterrein — vlees, vacht en gewei."},
    {"id": "haven",       "naam": "Zeehaven",      "kleur": "#0e7490", "icon": "anchor",   "beschrijving": "Aanlegplaats voor schepen — handel over zee."},
    {"id": "handelspost", "naam": "Handelspost",   "kleur": "#9333ea", "icon": "scale",    "beschrijving": "Knooppunt voor karavanen — handel over land."},
    {"id": "rovers",      "naam": "Roverskamp",    "kleur": "#7f1d1d", "icon": "skull",    "beschrijving": "Schuilplaats van rovers — gevaarlijk terrein."},
    {"id": "anders",      "naam": "Anders",        "kleur": "#94a3b8", "icon": "star",     "beschrijving": "Onbekende grondstof — admin om in te vullen."},
]


def _load_resources() -> List[dict]:
    GRONDSTOFFEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(GRONDSTOFFEN_FILE, default={"resources": []})
    return data.get("resources", []) or []


def _save_resources(resources: List[dict], user_id: Optional[str] = None) -> None:
    data = {
        "version": 1,
        "resources": resources,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user_id,
    }
    save_json(GRONDSTOFFEN_FILE, data)


def _save_image_to_system_archive(content: bytes, original_name: str, resource_id: str,
                                  resource_naam: str, user_id: str,
                                  mime_type: str = "image/png") -> dict:
    """Schrijf grondstof-afbeelding naar system_archive/foto + index-entry met dnd_resource tag."""
    SA_DIR.mkdir(parents=True, exist_ok=True)
    (SA_DIR / "foto").mkdir(parents=True, exist_ok=True)
    ext = Path(original_name).suffix.lower() or ".png"
    file_id = uuid.uuid4().hex[:12]
    safe_name = f"{file_id}{ext}"
    dest = SA_DIR / "foto" / safe_name
    dest.write_bytes(content)
    entry = {
        "id": file_id,
        "filename": safe_name,
        "original_name": original_name,
        "category": "foto",
        "extension": ext,
        "mime_type": mime_type,
        "size_bytes": len(content),
        "description": f"D&D grondstof: {resource_naam}",
        "tags": ["dnd", "dnd_resource", f"dnd_resource_{resource_id}"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user_id,
        "path": str(dest),
        "linked_resource_id": resource_id,
        "source": "dnd_resource_upload",
    }
    idx = load_json(SA_INDEX, default={"files": []})
    idx.setdefault("files", []).append(entry)
    idx["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(SA_INDEX, idx)
    return entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_game_card_for_resource(resource: dict, image_url: Optional[str], user_id: str) -> Optional[str]:
    """v6_dnd_resources_001 — Maak een D&D game-kaart aan voor de grondstof,
    inclusief image_url indien beschikbaar. Retourneert card_id of None."""
    try:
        GAME_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = load_json(GAME_FILE, default={"cards": []})
        card_id = f"game-{uuid.uuid4().hex[:8]}"
        rtype = resource.get("type", "anders")
        type_meta = next((t for t in RESOURCE_TYPES if t["id"] == rtype), {})
        card = {
            "id": card_id,
            "class": "game",
            "type": "dnd_resource_card",
            "begrip": resource.get("naam", "Onbekende grondstof"),
            "sense": None,
            "lagen": {
                "laag1": resource.get("beschrijving") or type_meta.get("beschrijving") or "",
                "laag2": "", "laag3": "", "laag4": "",
            },
            "ws5": {
                "wie": "", "wat": resource.get("naam", ""),
                "wanneer": "", "waar": resource.get("locatie") or "Op de Spark-kaart",
                "waarom": "Grondstofbron voor de wereld.", "hoe": "Te oogsten door bewoners.",
            },
            "tags": ["D&D", "grondstof", rtype],
            "media": {
                "voice_url": None,
                "voice_transcript": None,
                "image_urls": [image_url] if image_url else [],
            },
            "game_meta": {
                "is_item": False,
                "slot": "",
                "weight": 0.0,
                "stats_bonus": {},
                "combat_bonus": {},
                "meta": {
                    "klasse": "", "beroep": "", "fractie": resource.get("fractie_id") or "",
                    "locatie": resource.get("locatie") or "",
                },
                "value_goud": 0,
                "rarity": "common",
                "kind": "resource",
                "resource_type": rtype,
                "resource_id": resource.get("id"),
            },
            "status": "draft",
            "needs": [],
            "footnote": {
                "bron": "dnd_resource_upload",
                "vertrouwen": 0.5,
                "aangemaakt_door": user_id,
                "aangemaakt_op": _now_iso(),
                "laatst_bewerkt_op": _now_iso(),
            },
        }
        data.setdefault("cards", []).insert(0, card)
        data["updated_at"] = _now_iso()
        save_json(GAME_FILE, data)
        return card_id
    except Exception:
        return None


def _create_kb_inbox_card_for_resource(resource: dict, image_url: Optional[str], user_id: str) -> Optional[str]:
    """v6_dnd_resources_001 — Maak ook een KB v2 inbox-kaart zodat Spark hem kent."""
    try:
        KB_INBOX.parent.mkdir(parents=True, exist_ok=True)
        data = load_json(KB_INBOX, default={"kaarten": []})
        card_id = f"kb-{uuid.uuid4().hex[:8]}"
        rtype = resource.get("type", "anders")
        type_meta = next((t for t in RESOURCE_TYPES if t["id"] == rtype), {})
        kaart = {
            "id": card_id,
            "begrip": resource.get("naam", "Onbekende grondstof"),
            "lagen": {
                "laag1": resource.get("beschrijving") or type_meta.get("beschrijving") or "",
                "laag2": "", "laag3": "", "laag4": "",
            },
            "ws5": {"wie": "", "wat": resource.get("naam", ""),
                    "wanneer": "", "waar": resource.get("locatie") or "Op de Spark-kaart",
                    "waarom": "Grondstofbron voor de wereld.", "hoe": ""},
            "tags": ["dnd", "grondstof", rtype],
            "media": {
                "voice_url": None,
                "voice_transcript": None,
                "image_urls": [image_url] if image_url else [],
            },
            "status": "draft",
            "needs": [],
            "footnote": {
                "bron": "dnd_resource_upload",
                "vertrouwen": 0.4,
                "aangemaakt_door": user_id,
                "aangemaakt_op": _now_iso(),
                "laatst_bewerkt_op": _now_iso(),
            },
        }
        data.setdefault("kaarten", []).insert(0, kaart)
        data["updated_at"] = _now_iso()
        save_json(KB_INBOX, data)
        return card_id
    except Exception:
        return None


class ResourcePatchBody(BaseModel):
    user_id: str
    x_pct: Optional[float] = None
    y_pct: Optional[float] = None
    naam: Optional[str] = None
    type: Optional[str] = None
    beschrijving: Optional[str] = None
    fractie_id: Optional[str] = None


@router.get("/resources")
async def get_resources():
    """Lijst van alle grondstoffen op de kaart + resource-types meta."""
    return {
        "resources": _load_resources(),
        "types": RESOURCE_TYPES,
    }


@router.post("/resources")
async def create_resource(
    image: UploadFile = File(...),
    naam: str = Form(...),
    type: str = Form("anders"),
    x_pct: float = Form(...),
    y_pct: float = Form(...),
    beschrijving: Optional[str] = Form(None),
    fractie_id: Optional[str] = Form(None),
    user_id: str = Form(...),
    create_kb_card: bool = Form(True),
):
    """Upload image → opslaan in system_archive + grondstoffen.json + auto-create kaart."""
    if not _is_admin(user_id):
        raise HTTPException(403, "Alleen admin kan grondstoffen toevoegen")
    ext = Path(image.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE:
        raise HTTPException(400, f"Image-type '{ext}' niet toegestaan")
    data = await image.read()
    if len(data) > MAX_IMAGE_MB * 1024 * 1024:
        raise HTTPException(413, f"Image te groot (>{MAX_IMAGE_MB}MB)")

    resource_id = f"res-{uuid.uuid4().hex[:8]}"
    resource = {
        "id": resource_id,
        "naam": naam.strip(),
        "type": type or "anders",
        "beschrijving": (beschrijving or "").strip(),
        "fractie_id": fractie_id or None,
        "kaart": {"x_pct": float(x_pct), "y_pct": float(y_pct)},
        "image_url": None,
        "archive_id": None,
        "linked_card_id": None,
        "linked_kb_card_id": None,
        "aangemaakt_op": _now_iso(),
        "aangemaakt_door": user_id,
    }

    archive = _save_image_to_system_archive(
        content=data,
        original_name=image.filename or f"{resource_id}{ext}",
        resource_id=resource_id,
        resource_naam=naam,
        user_id=user_id,
        mime_type=image.content_type or "image/png",
    )
    image_url = f"/api/system-archive/file/{archive['id']}"
    resource["image_url"] = image_url
    resource["archive_id"] = archive["id"]

    # Auto-create game card + (optioneel) KB inbox card
    game_card_id = _create_game_card_for_resource(resource, image_url, user_id)
    resource["linked_card_id"] = game_card_id
    if create_kb_card:
        kb_card_id = _create_kb_inbox_card_for_resource(resource, image_url, user_id)
        resource["linked_kb_card_id"] = kb_card_id

    resources = _load_resources()
    resources.append(resource)
    _save_resources(resources, user_id=user_id)
    return {"success": True, "resource": resource}


@router.patch("/resources/{resource_id}")
async def patch_resource(resource_id: str, body: ResourcePatchBody):
    """Admin: update positie / metadata van een grondstof."""
    if not _is_admin(body.user_id):
        raise HTTPException(403, "Alleen admin")
    resources = _load_resources()
    target = next((r for r in resources if r.get("id") == resource_id), None)
    if not target:
        raise HTTPException(404, f"Grondstof '{resource_id}' niet gevonden")
    if body.x_pct is not None or body.y_pct is not None:
        kaart = target.setdefault("kaart", {})
        if body.x_pct is not None:
            kaart["x_pct"] = float(body.x_pct)
        if body.y_pct is not None:
            kaart["y_pct"] = float(body.y_pct)
    for field in ("naam", "type", "beschrijving", "fractie_id"):
        val = getattr(body, field)
        if val is not None:
            target[field] = val
    _save_resources(resources, user_id=body.user_id)
    return {"success": True, "resource": target}


@router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: str, user_id: str):
    """Admin: verwijder grondstof (linked card blijft staan, image blijft in archive)."""
    if not _is_admin(user_id):
        raise HTTPException(403, "Alleen admin")
    resources = _load_resources()
    if not any(r.get("id") == resource_id for r in resources):
        raise HTTPException(404, f"Grondstof '{resource_id}' niet gevonden")
    resources = [r for r in resources if r.get("id") != resource_id]
    _save_resources(resources, user_id=user_id)
    return {"success": True, "deleted": resource_id}


class ResourceDuplicateBody(BaseModel):
    user_id: str
    naam: Optional[str] = None       # default = "{originele naam} (kopie)"
    x_pct: Optional[float] = None    # default = origineel + 4% offset
    y_pct: Optional[float] = None
    create_kb_card: bool = True


@router.post("/resources/{resource_id}/duplicate")
async def duplicate_resource(resource_id: str, body: ResourceDuplicateBody):
    """v6_dnd_resources_dup_001 — Dupliceer een grondstof.
    Hergebruikt de image-archive-entry (geen tweede upload nodig) en maakt
    een nieuwe game-card + KB inbox-kaart aan."""
    if not _is_admin(body.user_id):
        raise HTTPException(403, "Alleen admin")
    resources = _load_resources()
    src = next((r for r in resources if r.get("id") == resource_id), None)
    if not src:
        raise HTTPException(404, f"Grondstof '{resource_id}' niet gevonden")

    new_id = f"res-{uuid.uuid4().hex[:8]}"
    src_kaart = src.get("kaart") or {}
    new_x = body.x_pct if body.x_pct is not None else min(99.0, float(src_kaart.get("x_pct", 50)) + 4.0)
    new_y = body.y_pct if body.y_pct is not None else min(99.0, float(src_kaart.get("y_pct", 50)) + 4.0)
    new_naam = (body.naam or f"{src.get('naam', 'Grondstof')} (kopie)").strip()

    resource = {
        "id": new_id,
        "naam": new_naam,
        "type": src.get("type", "anders"),
        "beschrijving": src.get("beschrijving", ""),
        "fractie_id": src.get("fractie_id"),
        "kaart": {"x_pct": new_x, "y_pct": new_y},
        "image_url": src.get("image_url"),     # hergebruik bestaande image
        "archive_id": src.get("archive_id"),   # zelfde archive entry
        "linked_card_id": None,
        "linked_kb_card_id": None,
        "aangemaakt_op": _now_iso(),
        "aangemaakt_door": body.user_id,
        "duplicated_from": resource_id,
    }

    # Auto-create kaarten (nieuw, NIET hergebruikt; anders verwijst kaart naar verkeerde resource)
    game_card_id = _create_game_card_for_resource(resource, resource["image_url"], body.user_id)
    resource["linked_card_id"] = game_card_id
    if body.create_kb_card:
        kb_card_id = _create_kb_inbox_card_for_resource(resource, resource["image_url"], body.user_id)
        resource["linked_kb_card_id"] = kb_card_id

    resources.append(resource)
    _save_resources(resources, user_id=body.user_id)
    return {"success": True, "resource": resource}
