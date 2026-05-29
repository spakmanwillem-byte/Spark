"""
Dashboard Financial Widget (v6_dashboard_fin_001 — 28 mei 2026)
==================================================================
Aggregator endpoint voor het Dashboard "Saldo + Vermogen" blok.
Combineert:
  • Cash (EUR-wallet) = wallets.json[user_id].balance_eur
  • Bitvavo portfolio = real-time som van crypto-holdings * prices (admin only)
  • Potjes vermogen   = som van potje.capital + open-pnl
  • ROAR tokens       = roar_balances * dynamic-price

Returns 1 dict met sub-totalen + grand-total.
"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from modules.core.storage import load_json

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DATA = Path(__file__).parent.parent.parent / "data"


@router.get("/financial/{user_id}")
async def financial(user_id: str):
    """Aggregeer saldo + vermogen voor user op het Dashboard."""
    out = {
        "cash_eur": 0.0,
        "potjes_eur": 0.0,
        "potjes_open_pnl": 0.0,
        "roar_tokens": 0,
        "roar_value_eur": 0.0,
        "bitvavo_eur": 0.0,
        "totaal_vermogen_eur": 0.0,
        "details": {},
    }

    # 1) Cash uit wallets.json
    wallets = load_json(DATA / "wallet" / "wallets.json", default={"wallets": {}})
    w = wallets.get("wallets", {}).get(user_id, {})
    out["cash_eur"] = round(float(w.get("balance_eur", w.get("balance", 0)) or 0), 2)

    # 2) Potjes uit user_potjes.json
    potjes_data = load_json(DATA / "financial" / "user_potjes.json", default={"users": {}})
    user_potjes = potjes_data.get("users", {}).get(user_id, {}).get("potjes", [])
    pot_cap = sum(float(p.get("capital", 0) or 0) for p in user_potjes)
    out["potjes_eur"] = round(pot_cap, 2)
    out["potjes_count"] = len(user_potjes)
    out["potjes_open_count"] = sum(1 for p in user_potjes if p.get("position", {}).get("is_open"))

    # 3) ROAR tokens + dynamic price
    roar = load_json(DATA / "roar" / "roar_balances.json", default={"balances": {}})
    tokens = int(roar.get("balances", {}).get(user_id, 0) or 0)
    out["roar_tokens"] = tokens
    # Dynamic price - probeer shop module te gebruiken
    try:
        from modules.shop.routes import get_dynamic_price
        token_price = float(get_dynamic_price() or 0)
    except Exception:
        token_price = 5.08  # fallback
    out["roar_token_price_eur"] = round(token_price, 2)
    out["roar_value_eur"] = round(tokens * token_price, 2)

    # 4) Bitvavo portfolio (alleen voor admin user-001 — vereist API key)
    # v6_bitvavo_base_locked_001 (sessie 16) — base = total - cash =
    # waarde van coins die in staking/anchors zitten. Groeit automatisch
    # met crypto-prijzen, geen handmatige sync nodig.
    if user_id == "user-001":
        try:
            from modules.trade.bitvavo_client import get_balance_summary
            summary = get_balance_summary()
            total_bv = round(float(summary.get("total_eur", 0)), 2)
            breakdown = summary.get("breakdown", {})
            cash_in_bv = round(float(breakdown.get("EUR", 0)), 2)
            out["bitvavo_eur"] = total_bv
            out["bitvavo_cash_eur"] = cash_in_bv
            out["bitvavo_base_locked_eur"] = round(total_bv - cash_in_bv, 2)
            out["details"]["bitvavo"] = breakdown
        except Exception:
            pass

    # 5) Grand total = cash + potjes-capital + roar-waarde + bitvavo
    out["totaal_vermogen_eur"] = round(
        out["cash_eur"] + out["potjes_eur"] + out["roar_value_eur"] + out["bitvavo_eur"], 2
    )

    return {"success": True, **out}
