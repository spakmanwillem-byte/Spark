"""
D&D Perks Service (v6_perks_001) — Aura-gebaseerde feature-gates
====================================================================
Bepaalt welke perks/features een user beschikbaar heeft op basis van:
  - gradatie (1-7, lager = hoger)
  - aura: top-3 gedragingen uit behavior_tracker
  - badge / achievement-set

Perks zijn declaratief in PERKS_TABLE. Een perk heeft:
  - id, naam, doel
  - min_gradatie (optioneel)
  - required_behaviors (optioneel) — top-3 moet 1 hiervan bevatten
  - required_achievements (optioneel) — user heeft ten minste 1
  - desc_when_unlocked / desc_when_locked

Endpoints:
  GET  /api/perks                       → alle perks + lock-status voor viewer
  GET  /api/perks/check/{perk_id}       → ja/nee + reden
  GET  /api/perks/user/{user_id}        → unlocked perks lijst
"""
from modules.core.paths import SPARK_ROOT  # v14_spark_root_001
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from modules.core.storage import load_json

router = APIRouter(prefix="/perks", tags=["perks"])

DATA = Path(f"{SPARK_ROOT}/backend/data")
USERS_FILE = DATA / "system" / "users.json"
ACHIEVEMENTS_FILE = DATA / "achievements.json"


# ============================================================
# PERKS TABLE — declaratief
# ============================================================
PERKS_TABLE: List[Dict[str, Any]] = [
    {
        "id": "shop_open",
        "naam": "Eigen winkel openen",
        "doel": "Open een digitale winkel in de Winkelstraat met 2% commissie",
        "min_gradatie": 4,
        "desc_when_unlocked": "Je hebt het vertrouwen opgebouwd om een eigen winkel te starten.",
        "desc_when_locked": "Bereik gradatie 4 of hoger om een winkel te openen.",
    },
    {
        "id": "kbv2_curator",
        "naam": "Kennisbank curator",
        "doel": "Kaarten classificeren en lades aanpassen",
        "min_gradatie": 3,
        "desc_when_unlocked": "Je mag de kennisbank mee vormgeven.",
        "desc_when_locked": "Bereik gradatie 3 om de kennisbank te kunnen mee-classificeren.",
    },
    {
        "id": "potje_full_access",
        "naam": "Trade-potjes vullen",
        "doel": "Eigen ROAR storten in trade-potjes",
        "min_gradatie": 3,
        "desc_when_unlocked": "Je mag mee-investeren in trade-potjes.",
        "desc_when_locked": "Bereik gradatie 3 om potjes te vullen.",
    },
    {
        "id": "community_voting",
        "naam": "Stemmen in community-polls",
        "doel": "Beslis mee over Spark's koers",
        "min_gradatie": 5,
        "desc_when_unlocked": "Je stem telt mee in koers-beslissingen.",
        "desc_when_locked": "Bereik gradatie 5 om mee te stemmen.",
    },
    {
        "id": "private_chat",
        "naam": "Privé-chat met andere users",
        "doel": "1-op-1 gesprekken via vriendschap",
        "min_gradatie": 5,
        "desc_when_unlocked": "Je kan 1-op-1 met vrienden chatten.",
        "desc_when_locked": "Bereik gradatie 5 + accepteer een vriendschap voor privé-chat.",
    },
    {
        "id": "lore_kaart_maker",
        "naam": "Lore-kaart maker",
        "doel": "D&D lore-kaarten aanmaken voor de Levende Wereld",
        "required_behaviors": ["kb_create", "lore_contributed", "kbv2_classify"],
        "min_gradatie": 4,
        "desc_when_unlocked": "Je kennisbijdragen mogen lore worden.",
        "desc_when_locked": "Maak eerst kennis-kaarten (gradatie 4+) — dan kan je lore vormgeven.",
    },
    {
        "id": "spark_helper",
        "naam": "Spark Helper badge",
        "doel": "Bedankt voor je hulp-gedragingen in community",
        "required_behaviors": ["help_msg", "answered_question"],
        "min_gradatie": 5,
        "desc_when_unlocked": "Je helpt anderen actief — Spark erkent je.",
        "desc_when_locked": "Help andere users in community-chat om dit te ontgrendelen.",
    },
    {
        "id": "truth_keeper",
        "naam": "Truth Keeper",
        "doel": "Eerlijk gebleven — geen leugens-detectie afgelopen 30 dagen",
        "required_behaviors": [],
        "blocked_by_behaviors": ["lie_detected"],
        "min_gradatie": 4,
        "desc_when_unlocked": "Je communicatie wordt vertrouwd door Spark.",
        "desc_when_locked": "Wees consistent eerlijk om dit te behouden.",
    },
]


# ============================================================
# HELPERS
# ============================================================
def _get_user(user_id: str) -> Optional[Dict]:
    users = load_json(USERS_FILE, default={"users": []}).get("users", [])
    return next((u for u in users if u.get("id") == user_id), None)


def _get_aura(user_id: str) -> Dict[str, Any]:
    """Hergebruik aura-data via behavior_tracker."""
    try:
        from modules import behavior_tracker
        if hasattr(behavior_tracker, "get_top_behaviors"):
            top = behavior_tracker.get_top_behaviors(user_id, n=5)
            return {"top_behaviors": [b.get("kind") for b in top if isinstance(b, dict)]}
    except Exception:
        pass
    # Fallback: lees direct uit behavior_log
    bt_file = DATA / "system" / "behavior_log.json"
    if not bt_file.exists():
        return {"top_behaviors": []}
    data = load_json(bt_file, default={})
    user_data = data.get(user_id, {})
    counts = user_data.get("counts", {})
    top = sorted(counts.items(), key=lambda x: -x[1])[:5]
    return {"top_behaviors": [k for k, _ in top]}


def _check_perk(perk: Dict, user: Optional[Dict], aura: Dict) -> Dict[str, Any]:
    """Returns {unlocked: bool, reason: str}."""
    if not user:
        return {"unlocked": False, "reason": "user-niet-gevonden"}
    grad = user.get("gradatie", 7)
    if "min_gradatie" in perk and grad > perk["min_gradatie"]:
        return {"unlocked": False, "reason": f"gradatie {grad} > min {perk['min_gradatie']}"}
    if "required_behaviors" in perk and perk["required_behaviors"]:
        top = set(aura.get("top_behaviors", []))
        if not (top & set(perk["required_behaviors"])):
            return {"unlocked": False, "reason": f"behaviors niet in top-5: {perk['required_behaviors']}"}
    if "blocked_by_behaviors" in perk and perk["blocked_by_behaviors"]:
        top = set(aura.get("top_behaviors", []))
        blocked = top & set(perk["blocked_by_behaviors"])
        if blocked:
            return {"unlocked": False, "reason": f"geblokkeerd door gedrag: {sorted(blocked)}"}
    return {"unlocked": True, "reason": "ok"}


# ============================================================
# ENDPOINTS
# ============================================================
@router.get("")
async def list_perks(user_id: Optional[str] = None):
    """Returnt alle perks. Als user_id meegegeven → status per perk."""
    if not user_id:
        return {"perks": PERKS_TABLE}
    user = _get_user(user_id)
    aura = _get_aura(user_id)
    out = []
    for p in PERKS_TABLE:
        check = _check_perk(p, user, aura)
        out.append({
            **p,
            "unlocked": check["unlocked"],
            "reason": check["reason"],
            "desc": p["desc_when_unlocked"] if check["unlocked"] else p["desc_when_locked"],
        })
    return {
        "user_id": user_id,
        "gradatie": (user or {}).get("gradatie"),
        "aura_top_behaviors": aura.get("top_behaviors", [])[:3],
        "perks": out,
        "unlocked_count": sum(1 for p in out if p["unlocked"]),
        "total": len(out),
    }


@router.get("/check/{perk_id}")
async def check_one_perk(perk_id: str, user_id: str):
    perk = next((p for p in PERKS_TABLE if p["id"] == perk_id), None)
    if not perk:
        raise HTTPException(404, f"Perk {perk_id} niet gevonden")
    user = _get_user(user_id)
    aura = _get_aura(user_id)
    check = _check_perk(perk, user, aura)
    return {
        "perk_id": perk_id,
        "naam": perk["naam"],
        "user_id": user_id,
        "unlocked": check["unlocked"],
        "reason": check["reason"],
        "desc": perk["desc_when_unlocked"] if check["unlocked"] else perk["desc_when_locked"],
    }


@router.get("/user/{user_id}")
async def user_perks(user_id: str):
    """Lijst van perks die deze user beschikbaar heeft."""
    user = _get_user(user_id)
    aura = _get_aura(user_id)
    unlocked = []
    locked = []
    for p in PERKS_TABLE:
        check = _check_perk(p, user, aura)
        target = unlocked if check["unlocked"] else locked
        target.append({
            "id": p["id"],
            "naam": p["naam"],
            "doel": p["doel"],
            "desc": p["desc_when_unlocked"] if check["unlocked"] else p["desc_when_locked"],
            "reason": check["reason"],
        })
    return {
        "user_id": user_id,
        "gradatie": (user or {}).get("gradatie"),
        "aura_top_behaviors": aura.get("top_behaviors", [])[:3],
        "unlocked": unlocked,
        "locked": locked,
    }
