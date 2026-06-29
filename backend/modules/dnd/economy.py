"""v6_dnd_economy_001 — D&D economie helpers.

- Laad blueprints (klassen, beroepen, grondstoffen, prijscurve, dorp_income, buildings)
- Prijscurve berekening per stad per item
- Trader-AI tick (placeholder hook voor scheduler)
- Daily dorp-income tick
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter
from modules.core.storage import load_json, save_json

BP_DIR = Path(__file__).parent.parent.parent / "data" / "dnd" / "blueprints"
STEDEN_FP = Path(__file__).parent.parent.parent / "data" / "dnd" / "steden.json"

router = APIRouter(prefix="/dnd/economy", tags=["dnd-economy"])


# ════════════════════════════════════════════════════════════
# BLUEPRINT LOADERS (cached per request)
# ════════════════════════════════════════════════════════════

def load_klassen() -> List[Dict]:
    return load_json(BP_DIR / "dnd_klassen.json", default={"klassen": []}).get("klassen", [])


def load_beroepen() -> List[Dict]:
    return load_json(BP_DIR / "dnd_beroepen.json", default={"beroepen": []}).get("beroepen", [])


def load_grondstoffen() -> List[Dict]:
    return load_json(BP_DIR / "dnd_grondstoffen.json", default={"grondstoffen": []}).get("grondstoffen", [])


def load_prijscurve() -> Dict:
    return load_json(BP_DIR / "dnd_prijscurve.json", default={})


def load_dorp_income() -> Dict:
    return load_json(BP_DIR / "dnd_dorp_income.json", default={})


def load_buildings() -> List[Dict]:
    return load_json(BP_DIR / "dnd_buildings.json", default={"buildings": []}).get("buildings", [])


def get_resource_base_value(resource_id: str) -> int:
    for g in load_grondstoffen():
        if g["id"] == resource_id:
            return int(g.get("base_value", 1))
    return 1


# ════════════════════════════════════════════════════════════
# PRIJSCURVE
# ════════════════════════════════════════════════════════════

def price_for_voorraad(base_value: int, voorraad_pct: float) -> int:
    """Bereken dynamische prijs o.b.v. piecewise-linear curve uit blueprint."""
    curve = load_prijscurve()
    ankers = curve.get("formule", {}).get("ankers") or [
        {"voorraad_pct": 0, "prijs_multiplier": 10.0},
        {"voorraad_pct": 50, "prijs_multiplier": 1.0},
        {"voorraad_pct": 80, "prijs_multiplier": 0.4},
        {"voorraad_pct": 100, "prijs_multiplier": 0.1},
    ]
    p = max(0.0, min(100.0, float(voorraad_pct)))
    points = [(a["voorraad_pct"], a["prijs_multiplier"]) for a in ankers]
    points.sort(key=lambda x: x[0])
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= p <= x1:
            t = (p - x0) / (x1 - x0) if x1 != x0 else 0
            mul = y0 + t * (y1 - y0)
            return max(1, round(base_value * mul))
    # buiten range
    return max(1, round(base_value * points[-1][1]))


# ════════════════════════════════════════════════════════════
# DAILY DORP-INCOME (scheduler hook)
# ════════════════════════════════════════════════════════════

def grant_daily_dorp_income() -> Dict:
    """1× per dag aanroepen vanuit scheduler — stort basis grondstoffen in elke stad."""
    income_bp = load_dorp_income()
    basis = income_bp.get("basis_per_level_1", [])
    schaal = income_bp.get("schaling_per_level", {}).get("factor", 1.0)
    steden_data = load_json(STEDEN_FP, default={"steden": []})
    steden = steden_data.get("steden", [])
    granted = {}
    for stad in steden:
        # Resources opslaan in een sub-dict op stad ('warehouse_resources')
        stad.setdefault("warehouse_resources", {})
        level = stad.get("level", 1) or 1
        for entry in basis:
            res_id = entry["resource"]
            qty = int(entry["qty"] * level * schaal)
            stad["warehouse_resources"][res_id] = stad["warehouse_resources"].get(res_id, 0) + qty
        granted[stad["id"]] = {"level": level, "items_granted": len(basis)}
    save_json(STEDEN_FP, steden_data)
    return {"granted": granted, "stad_count": len(steden)}


# ════════════════════════════════════════════════════════════
# TRADER-AI (placeholder voor toekomstige scheduler hook)
# ════════════════════════════════════════════════════════════

def trader_decision_for_city(stad_id: str) -> Optional[Dict]:
    """Bepaal wat de trader van deze stad zou doen.
    Returns: {action: 'buy'|'sell'|'idle', resource, target_stad, expected_profit}
    """
    steden_data = load_json(STEDEN_FP, default={"steden": []})
    steden = {s["id"]: s for s in steden_data.get("steden", [])}
    if stad_id not in steden:
        return None
    src = steden[stad_id]
    src_voorraad = src.get("warehouse_resources", {})
    streven = load_prijscurve().get("stad_streven_voorraad_pct", 80)
    max_per_res = load_prijscurve().get("voorraad_warehouse_default_max", 1000)
    tax_pct = load_prijscurve().get("trade_tax_pct", 5) / 100.0
    best = {"action": "idle", "score": 0}

    for res_id, qty in src_voorraad.items():
        src_pct = (qty / max_per_res) * 100
        src_price = price_for_voorraad(get_resource_base_value(res_id), src_pct)
        # Onder streven → koop-mode (check verkoper-steden waar voorraad hoog is dus goedkoop)
        if src_pct < streven:
            for other_id, other in steden.items():
                if other_id == stad_id:
                    continue
                other_qty = other.get("warehouse_resources", {}).get(res_id, 0)
                other_pct = (other_qty / max_per_res) * 100
                if other_pct < 30:
                    continue
                other_price = price_for_voorraad(get_resource_base_value(res_id), other_pct)
                effective = other_price * (1 + tax_pct)
                if effective < src_price:
                    score = src_price - effective
                    if score > best["score"]:
                        best = {"action": "buy", "score": score, "resource": res_id,
                                "from_stad": other_id, "to_stad": stad_id,
                                "buy_price": other_price, "tax": round(other_price * tax_pct),
                                "src_pct": round(src_pct, 1), "other_pct": round(other_pct, 1)}
        # Boven streven → verkoop-mode
        elif src_pct > streven:
            for other_id, other in steden.items():
                if other_id == stad_id:
                    continue
                other_qty = other.get("warehouse_resources", {}).get(res_id, 0)
                other_pct = (other_qty / max_per_res) * 100
                if other_pct > streven:
                    continue
                other_price = price_for_voorraad(get_resource_base_value(res_id), other_pct)
                effective = other_price * (1 - tax_pct)
                if effective > src_price:
                    score = effective - src_price
                    if score > best["score"]:
                        best = {"action": "sell", "score": score, "resource": res_id,
                                "from_stad": stad_id, "to_stad": other_id,
                                "sell_price": other_price, "tax": round(other_price * tax_pct),
                                "src_pct": round(src_pct, 1), "other_pct": round(other_pct, 1)}
    return best


# ════════════════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════════════════

@router.get("/blueprints")
async def get_all_blueprints():
    """Alle game-blueprints in 1 response."""
    return {
        "klassen": load_klassen(),
        "beroepen": load_beroepen(),
        "grondstoffen": load_grondstoffen(),
        "prijscurve": load_prijscurve(),
        "dorp_income": load_dorp_income(),
        "buildings": load_buildings(),
    }


@router.get("/blueprints/{name}")
async def get_blueprint(name: str):
    loaders = {
        "klassen": load_klassen, "beroepen": load_beroepen,
        "grondstoffen": load_grondstoffen, "prijscurve": load_prijscurve,
        "dorp_income": load_dorp_income, "buildings": load_buildings,
    }
    if name not in loaders:
        return {"success": False, "error": f"unknown blueprint '{name}'", "available": list(loaders.keys())}
    return {"success": True, "name": name, "data": loaders[name]()}


@router.get("/price/{resource_id}/{voorraad_pct}")
async def price_check(resource_id: str, voorraad_pct: float):
    base = get_resource_base_value(resource_id)
    p = price_for_voorraad(base, voorraad_pct)
    return {"resource": resource_id, "base_value": base, "voorraad_pct": voorraad_pct, "current_price": p}


@router.get("/trader-decision/{stad_id}")
async def trader_decision(stad_id: str):
    d = trader_decision_for_city(stad_id)
    return d or {"action": "idle"}


@router.post("/admin/grant-daily-income")
async def admin_grant_daily_income():
    """Admin trigger om dorp-income handmatig te uitkeren (normaal via scheduler)."""
    return grant_daily_dorp_income()
