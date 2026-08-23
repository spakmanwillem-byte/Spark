"""
Shop Routes - Roadkill Winkel + ROAR Token
Producten: Merch (caps, hoodies) + ROAR tokens (dynamische prijs).
Winkelwagen + bestellingen. Kasboek koppeling per entity.
"""
from fastapi import APIRouter, Query, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timezone
import time
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/shop", tags=["shop"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"
ROAR_FILE = DATA_DIR / "roar" / "roar_balances.json"
WALLET_FILE = DATA_DIR / "wallet" / "wallets.json"
FINANCIAL_FILE = DATA_DIR / "financial" / "transactions.json"
POTJES_FILE = DATA_DIR / "financial" / "user_potjes.json"
PRODUCTS_FILE = DATA_DIR / "users" / "user-001" / "shops" / "shop-roadkill" / "products.json"
SHOPS_FILE = DATA_DIR / "shop" / "shops.json"  # v6_shop_admin_delete_001 — module-level


def _shop_products_path(shop_id: str = "shop-roadkill"):
    """v6_shop_per_user_001 (28 mei) — products per shop in shop-owner's container.
    Founder shop-roadkill = user-001's container. Andere shops = hun owner.
    v11_shop_scope_001 (31 jul) — voor nieuwe shops (nog geen products.json) toch de
    per-shop path retourneren; save_json maakt hem aan. Voorkomt dat nieuwe shops
    per ongeluk in Willem's Roadkillshop-file schrijven.
    """
    from pathlib import Path as _P
    SHOPS = _P(__file__).parent.parent.parent / "data" / "shop" / "shops.json"
    sdata = load_json(SHOPS, default={"shops": []})
    shop = next((s for s in sdata.get("shops", []) if s.get("id") == shop_id), None)
    if not shop:
        return PRODUCTS_FILE  # fallback voor onbekende shop_id
    owner = shop.get("owner_user_id", "user-001")
    return _P(__file__).parent.parent.parent / "data" / "users" / owner / "shops" / shop_id / "products.json"
ACCOUNTING_FILE = DATA_DIR / "accounting" / "transactions.json"

TOTAL_SUPPLY = 1_000_000
BASE_PRICE = 10.00  # v8_price_reset_001 — Willems live-start: €10 bodemprijs (was €5.08). 5 tokens = €50 → past bij zijn Bitvavo test-kapitaal.
FIXED_PRICE_LIMIT = 10  # Na 10 tokens: dynamische prijs

NOTIF_FILE = DATA_DIR / "notifications" / "notifications.json"

# Cache voor live Bitvavo balance (30s)
_bitvavo_cache = {"value": None, "timestamp": 0}


# v5_milestone_unlocks_001 — trigger achievement + per-user notification bark bij eerste ROAR token
def _trigger_first_roar_token(user_id: str):
    """Wordt aangeroepen wanneer user voor het eerst een ROAR token ontvangt (prev_balance==0)."""
    try:
        from modules.achievements.service import unlock_milestone
        unlock_milestone(user_id, "milestone_first_roar_token")
    except Exception as ex:
        print(f"[shop] milestone unlock failed: {ex}")
    # Per-user bark / notification met monitor-uitleg
    try:
        notif_file = NOTIF_FILE
        notif_file.parent.mkdir(parents=True, exist_ok=True)
        data = load_json(notif_file, default={"notifications": []})
        data.setdefault("notifications", []).append({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "kind": "first_roar_token",
            "icon": "🪙",
            "title": "Je eerste ROAR token is binnen",
            "message": (
                "Welkom in de Spark-economie! Eén ROAR token = één bot-slot. "
                "Met dit token kun je nu een eigen Trader monitor starten via de Trader-module. "
                "Hoe het werkt:\n\n"
                "• De monitor luistert naar 1 markt (bv BCH-EUR) en analyseert de candles\n"
                "• Bij auto-trade aan koopt en verkoopt hij automatisch volgens de signalen\n"
                "• Je kunt hem altijd pauzeren of stoppen — Spark's eigen monitor blijft draaien\n\n"
                "Veel succes!"
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read": False,
        })
        save_json(notif_file, data)
    except Exception as ex:
        print(f"[shop] notification create failed: {ex}")


def get_roar_data():
    return load_json(ROAR_FILE, default={"balances": {"user-000": TOTAL_SUPPLY}, "total_supply": TOTAL_SUPPLY})


def save_roar_data(data):
    save_json(ROAR_FILE, data)


def get_circulating():
    """v5_treasury_fix_001 — Circulating = alle uitgegeven tokens uit treasury (incl. Spark's persoonlijke 10).
    Spark's persoonlijke balance is óók gekocht uit treasury (voor €50.80), dus telt mee als circulating.
    """
    roar = get_roar_data()
    return sum(bal for bal in roar.get("balances", {}).values())


def get_bitvavo_balance_cached(user_id: str = "user-001") -> Optional[float]:
    """Haal live Bitvavo balance op met 30s cache. Returns None bij fout."""
    now = time.time()
    if _bitvavo_cache["value"] is not None and (now - _bitvavo_cache["timestamp"]) < 30:
        return _bitvavo_cache["value"]
    try:
        from modules.trade.monitor import fetch_bitvavo_balance
        result = fetch_bitvavo_balance(user_id)
        if result.get("success"):
            total = result.get("total_eur", 0)
            _bitvavo_cache["value"] = total
            _bitvavo_cache["timestamp"] = now
            return total
    except Exception:
        pass
    return None


def get_bitvavo_staking_adjustment() -> float:
    """v6_bitvavo_staking_manual_001 (sessie 16) — handmatige staking-adjustment.
    Bitvavo's `/v2/balance` ziet alleen spot. Voor coins in Bitvavo Spaar/Staking
    wordt deze waarde handmatig bijgehouden in `system/bitvavo_extras.json`.
    Admin kan dit updaten via `POST /api/financial/bitvavo-staking`.
    """
    try:
        extras_file = DATA_DIR / "system" / "bitvavo_extras.json"
        extras = load_json(extras_file, default={"staking_eur": 0.0})
        return float(extras.get("staking_eur", 0) or 0)
    except Exception:
        return 0.0


def get_spark_core_value():
    """
    Spark Core totale waarde = LIVE Bitvavo balance + Spark kasboek gifts/omzet
    (gifts in build-fase + omzet in public-fase). v6_value_includes_gifts_001.
    v6_bitvavo_staking_manual_001 — telt nu ook handmatige staking erbij.
    """
    total_value = 0.0
    # PRIMAIR: Live Bitvavo balance (spot)
    live = get_bitvavo_balance_cached()
    if live is not None and live > 0:
        total_value += live
    else:
        # FALLBACK: Bereken uit financial transactions
        fin = load_json(FINANCIAL_FILE, default={"transactions": []})
        for tx in fin.get("transactions", []):
            if tx["type"] == "deposit":
                total_value += tx.get("amount_eur", 0)
            elif tx["type"] == "profit":
                total_value += tx.get("amount_eur", 0)
            elif tx["type"] == "withdrawal":
                total_value -= tx.get("amount_eur", 0)
    # v6_bitvavo_staking_manual_001 — Spaar/Staking handmatig toegevoegd
    total_value += get_bitvavo_staking_adjustment()
    # v6_value_includes_gifts_001 / v6_no_double_count_001 — Spark vermogen rekening:
    # - Bitvavo live balance is de PRIMAIRE waarde (alle SEPA-stortingen + gifts + omzet
    #   zitten al in Bitvavo wallet, dus NIET dubbel tellen)
    # - WEL meetellen: open leningen (vordering op Willem) want dat geld is NIET in Bitvavo
    # - WEL meetellen: winst_in is administratieve PnL boven Bitvavo balance — toekomstig
    try:
        kb = load_json(DATA_DIR / "system" / "spark_kasboek.json", default={"totals": {}})
        t = kb.get("totals", {})
        total_value += t.get("open_leningen", 0)  # vordering = asset buiten Bitvavo
    except Exception:
        pass
    return total_value


def get_dynamic_price():
    """
    ROAR prijs model:
    - Tot en met 10 tokens: bodemprijs €5.08 (starterprijs)
    - Boven dat: dynamisch = Spark Core (Bitvavo) waarde / circulerende tokens
    - Als Bitvavo stijgt door trading → token prijs stijgt mee
    """
    circulating = get_circulating()

    # Altijd dynamische berekening als Spark Core waarde bekend is
    try:
        total_value = get_spark_core_value()
        if circulating > 0 and total_value > 0:
            dynamic = round(total_value / circulating, 2)
            # Bodem op BASE_PRICE zolang nog weinig tokens uitstaan
            if circulating <= FIXED_PRICE_LIMIT:
                return max(dynamic, BASE_PRICE)
            return dynamic
    except Exception:
        pass
    return BASE_PRICE


class BuyTokenRequest(BaseModel):
    amount_eur: Optional[float] = None
    amount_tokens: Optional[int] = None  # Alleen hele tokens
    via_shop_id: Optional[str] = None  # v6_shop_referral_token_001 — als ROAR via shop wordt verkocht, krijgt die shop 2% commissie


class SellTokenRequest(BaseModel):
    amount_tokens: int  # Alleen hele tokens


# ============================================================
# TOKEN INFO
# ============================================================

@router.get("/token/price")
async def get_token_price():
    """Huidige ROAR token prijs"""
    price = get_dynamic_price()
    circulating = get_circulating()
    roar = get_roar_data()
    # v5_treasury_fix_001 — Toon treasury_pool (1M-pool), niet Spark's persoonlijke balance
    treasury_pool = roar.get("treasury_pool", TOTAL_SUPPLY - circulating)
    spark_personal = roar.get("balances", {}).get("user-000", 0)
    spark_core_value = get_spark_core_value()
    is_fixed = circulating < FIXED_PRICE_LIMIT

    return {
        "success": True,
        "price_eur": price,
        "base_price": BASE_PRICE,
        "total_supply": TOTAL_SUPPLY,
        "circulating": circulating,
        "spark_treasury": treasury_pool,
        "spark_personal_tokens": spark_personal,
        "spark_core_value": round(spark_core_value, 2),
        "market_cap": round(circulating * price, 2),
        "price_model": "fixed" if is_fixed else "dynamic",
        "fixed_price_limit": FIXED_PRICE_LIMIT,
        "tokens_until_dynamic": max(0, FIXED_PRICE_LIMIT - circulating),
        "bitvavo_balance": round(spark_core_value, 2),
        # v6_bitvavo_staking_manual_001 — toon staking-adjustment apart voor transparantie
        "bitvavo_spot_eur": round((get_bitvavo_balance_cached() or 0), 2),
        "bitvavo_staking_eur": round(get_bitvavo_staking_adjustment(), 2),
    }


# v6_bitvavo_staking_manual_001 — admin endpoint om staking-bedrag in te stellen
class StakingUpdateBody(BaseModel):
    staking_eur: float
    viewer_id: str = "user-001"


@router.post("/token/bitvavo-staking")
async def update_bitvavo_staking(body: StakingUpdateBody):
    """Update handmatige Bitvavo Staking-waarde (zit in Bitvavo Spaar, niet
    via /v2/balance leesbaar). Telt mee in Spark Core value en dynamic price.
    Alleen admin (gradatie ≤ 1)."""
    # Auth check
    users = load_json(DATA_DIR / "system" / "users.json", default={"users": []})
    viewer = next((u for u in users.get("users", []) if (u.get("id") or u.get("user_id")) == body.viewer_id), None)
    if not viewer or (viewer.get("gradatie") or 99) > 1:
        return {"success": False, "error": "Alleen admin mag staking-adjustment aanpassen"}
    if body.staking_eur < 0:
        return {"success": False, "error": "Staking moet >= 0 zijn"}
    extras_file = DATA_DIR / "system" / "bitvavo_extras.json"
    extras = load_json(extras_file, default={"staking_eur": 0.0})
    old = extras.get("staking_eur", 0)
    extras["staking_eur"] = round(float(body.staking_eur), 2)
    extras["updated_at"] = datetime.now(timezone.utc).isoformat()
    extras["updated_by"] = body.viewer_id
    save_json(extras_file, extras)
    return {"success": True, "old_eur": old, "new_eur": extras["staking_eur"],
            "spark_core_value_now": round(get_spark_core_value(), 2)}


@router.get("/token/balance/{user_id}")
async def get_token_balance(user_id: str):
    """ROAR token saldo van user"""
    roar = get_roar_data()
    balance = roar.get("balances", {}).get(user_id, 0)
    price = get_dynamic_price()
    return {
        "user_id": user_id,
        "roar_balance": balance,
        "value_eur": round(balance * price, 2),
        "price_per_token": price,
    }


@router.get("/token/spark-bonus")
async def get_spark_bonus():
    """
    v4_token_potje_001 — Spark's bonus token spaarpot.
    Earned door trading-winst, 1 bonus-token per €5.08 cumulatieve netto winst.
    Bestemd voor server-kosten (uitcash via wallet→bank koppeling, later).
    """
    roar = get_roar_data()
    bonus = roar.get("spark_bonus", {
        "balance": 0, "cumulative_profit_eur": 0.0,
        "token_price_at_mint": BASE_PRICE, "history": []
    })
    price = get_dynamic_price()
    # Hoeveel tot volgende token?
    cum = float(bonus.get("cumulative_profit_eur", 0.0))
    tokens_so_far = int(cum // BASE_PRICE)
    next_threshold_eur = (tokens_so_far + 1) * BASE_PRICE
    return {
        "success": True,
        "balance": bonus.get("balance", 0),
        "cumulative_profit_eur": round(cum, 4),
        "token_price_at_mint": bonus.get("token_price_at_mint", BASE_PRICE),
        "value_eur_at_current_price": round(bonus.get("balance", 0) * price, 2),
        "current_token_price": price,
        "progress_to_next_token_eur": round(next_threshold_eur - cum, 4),
        "history_count": len(bonus.get("history", [])),
        "recent_mints": list(reversed(bonus.get("history", [])[-5:])),
    }


@router.get("/token/history/{user_id}")
async def get_token_history(user_id: str):
    """Aankoop/verkoop geschiedenis"""
    fin = load_json(FINANCIAL_FILE, default={"transactions": []})
    user_txs = [
        tx for tx in fin.get("transactions", [])
        if tx.get("user_id") == user_id and tx.get("type") in ("buy_roar", "sell_roar", "deposit", "withdrawal")
    ]
    user_txs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"transactions": user_txs}


# ============================================================
# KOPEN / VERKOPEN
# ============================================================

@router.post("/token/buy/{user_id}")
async def buy_tokens(user_id: str, req: BuyTokenRequest):
    """Koop ROAR tokens met EUR uit wallet - alleen hele tokens"""
    price = get_dynamic_price()

    # Bereken amounts - alleen hele tokens
    if req.amount_tokens and req.amount_tokens > 0:
        amount_tokens = int(req.amount_tokens)
        amount_eur = round(amount_tokens * price, 2)
    elif req.amount_eur and req.amount_eur > 0:
        amount_tokens = int(req.amount_eur / price)  # Afronden naar beneden
        if amount_tokens < 1:
            return {"success": False, "error": f"Minimaal 1 token nodig. Prijs: {price}"}
        amount_eur = round(amount_tokens * price, 2)
    else:
        return {"success": False, "error": "Geef amount_eur of amount_tokens op"}

    # Check EUR wallet saldo
    wallets = load_json(WALLET_FILE, default={"wallets": {}, "transactions": []})
    user_wallet = wallets.get("wallets", {}).get(user_id, {"balance": 0})
    if user_wallet.get("balance", 0) < amount_eur:
        return {
            "success": False,
            "error": f"Onvoldoende EUR saldo. Heb {user_wallet.get('balance', 0):.2f}, nodig {amount_eur:.2f}",
        }

    # Check ROAR supply uit treasury_pool (1M pool, los van Spark's persoonlijke balance)
    # v5_treasury_fix_001 — Spark's persoonlijke balance is GEEN treasury.
    # Treasury = aparte pool van 1M tokens waar verkoop uit gaat.
    roar = get_roar_data()
    treasury_pool = roar.get("treasury_pool", 0)
    if treasury_pool < amount_tokens:
        return {"success": False, "error": f"Onvoldoende treasury supply ({treasury_pool} beschikbaar)"}

    # Execute
    # 1. Deduct EUR
    wallets["wallets"][user_id]["balance"] = round(user_wallet["balance"] - amount_eur, 2)

    # 2. Transfer ROAR uit treasury_pool naar koper (Spark's personal balance blijft ongemoeid)
    prev_user_roar = roar.get("balances", {}).get(user_id, 0)
    roar["treasury_pool"] = treasury_pool - amount_tokens
    roar["balances"][user_id] = prev_user_roar + amount_tokens

    # v5_milestone_unlocks_001: trigger "First ROAR Token" achievement + bark
    if prev_user_roar == 0 and amount_tokens > 0:
        _trigger_first_roar_token(user_id)

    # 3. Log transaction
    tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "buy_roar",
        "amount_eur": amount_eur,
        "token_amount": amount_tokens,
        "price_per_token": price,
        "description": f"{amount_tokens} ROAR gekocht @ {price}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
    }

    fin = load_json(FINANCIAL_FILE, default={"transactions": [], "roar_config": {}})
    fin["transactions"].append(tx)
    save_json(FINANCIAL_FILE, fin)

    wallets["transactions"].append(tx)
    save_json(WALLET_FILE, wallets)
    save_roar_data(roar)

    # v6_accounting_hooks_001 — auto-post naar centraal Boekhouding (single source of truth)
    try:
        from modules.accounting.hooks import on_token_buy
        ANCHOR_USERS = {"user-000", "user-001"}
        is_anchor = user_id in ANCHOR_USERS
        # Lookup naam uit users.json (variable `user` bestaat niet in deze scope — was bug)
        _users_data = load_json(USERS_FILE, default={"users": []})
        _ulist = _users_data.get("users", []) if isinstance(_users_data, dict) else _users_data
        buyer_naam = next((u.get("naam") for u in _ulist if u.get("id") == user_id), user_id)
        on_token_buy(
            buyer_user_id=user_id, buyer_naam=buyer_naam,
            tokens=amount_tokens, total_eur=amount_eur,
            price_per_token=price, ref_id=tx["id"],
            is_anchor=is_anchor, btw_pct=0.0,
        )
        # v6_shop_referral_token_001 — als verkoop via shop liep, boek 2% commissie op shop_kasboek
        # (alleen voor klanten, niet voor anker-aankopen die zelf de fundering vormen)
        if (not is_anchor) and getattr(req, "via_shop_id", None):
            shop_id = req.via_shop_id
            try:
                # Vind shop_kasboek_id via shops.json
                _ws_file = DATA_DIR / "shop" / "shops.json"
                shops_data = load_json(_ws_file, default={"shops": []})
                shop = next((s for s in shops_data.get("shops", []) if s.get("id") == shop_id), None)
                shop_kasboek_id = shop.get("kasboek_id") if shop else None
                if shop_kasboek_id and shop_kasboek_id != "spark_core":
                    commissie = round(amount_eur * 0.02, 2)
                    if commissie > 0:
                        acc = load_json(ACCOUNTING_FILE, default={"transactions": []})
                        acc["transactions"].append({
                            "id": str(uuid.uuid4()),
                            "type": "income",
                            "category": "Referral",
                            "amount": commissie,
                            "description": f"ROAR-koop via {shop_id} ({amount_tokens} tokens à €{price:.2f})",
                            "entity_id": shop_kasboek_id,
                            "date": datetime.now(timezone.utc).isoformat(),
                            "btw_percentage": 0,
                            "btw_amount": 0,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "tx_ref": f"token_buy_referral_{tx['id']}",
                            "source": "auto_hook",
                        })
                        save_json(ACCOUNTING_FILE, acc)
                        print(f"[token_buy] shop-referral 2% (€{commissie}) → {shop_kasboek_id}")
            except Exception as ex:
                print(f"[token_buy] shop-referral failed (non-blocking): {ex}")
    except Exception as ex:
        print(f"[token_buy] accounting-hook failed (non-blocking): {ex}")

    # v6_gift_phase_001 — In bouw-fase = GIFT, geen BTW. Volledige bedrag → Spark omzet.
    # Anker-aankopen (Willem/Spark) tellen sowieso niet mee als gift (zij zijn fundering).
    try:
        from datetime import datetime as _dt, timezone as _tz
        import uuid as _uuid
        from pathlib import Path as _P
        ANCHOR_USERS = {"user-000", "user-001"}
        is_klant = user_id not in ANCHOR_USERS
        # Lees money_phase
        phase_path = _P(__file__).parent.parent.parent / "data" / "system" / "money_phase.json"
        phase = load_json(phase_path, default={"phase": "build"}).get("phase", "build")
        kb_path = _P(__file__).parent.parent.parent / "data" / "system" / "spark_kasboek.json"
        kb = load_json(kb_path, default={"entries": [], "totals": {"gift_in": 0, "omzet_in": 0, "btw_reserve": 0, "winst_in": 0, "uit": 0}})
        kb.setdefault("totals", {})
        for key in ("gift_in", "omzet_in", "btw_reserve", "winst_in", "uit"):
            kb["totals"].setdefault(key, 0)
        if is_klant:
            entry_type = "gift_in" if phase == "build" else "klant_omzet"
            label_text = "Gift" if phase == "build" else "Klant-omzet"
            kb["entries"].append({
                "id": _uuid.uuid4().hex[:12],
                "ts": _dt.now(_tz.utc).isoformat(),
                "type": entry_type,
                "phase": phase,
                "bron_tx": tx["id"],
                "bron_user": user_id,
                "bedrag_eur": amount_eur,
                "n_tokens": amount_tokens,
                "omschrijving": f"{label_text} €{amount_eur} → {amount_tokens} ROAR als bedankje (bouw-fase: geen BTW, fiscaal donatie)" if phase == "build" else f"Klant-omzet {amount_tokens} ROAR @ €{price:.2f} (BTW pas bij winst-realisatie)",
            })
            if phase == "build":
                kb["totals"]["gift_in"] = round(kb["totals"]["gift_in"] + amount_eur, 4)
            else:
                kb["totals"]["omzet_in"] = round(kb["totals"]["omzet_in"] + amount_eur, 4)
            save_json(kb_path, kb)
            # Spark EUR-wallet krijgt VOLLE bedrag
            spark_w = wallets.get("wallets", {}).get("user-000")
            if isinstance(spark_w, dict):
                spark_w["balance"] = round(spark_w.get("balance", 0) + amount_eur, 4)
                save_json(WALLET_FILE, wallets)
            tx["spark_omzet_eur"] = amount_eur
            tx["btw_afgeroomd_eur"] = 0
            tx["money_phase"] = phase
        else:
            tx["btw_afgeroomd_eur"] = 0
            tx["anker_aankoop"] = True
    except Exception as _ex:
        print(f"[gift-registratie] failed: {_ex}")

    # v6_potje_per_token_001 — 1 token = 1 potje voor non-Spark users.
    # Spark (user-000) heeft 10 base potjes via _init_potjes; alleen anderen syncen.
    if user_id != "user-000":
        try:
            from modules.trade.potjes import sync_potjes_to_tokens
            new_balance = roar["balances"].get(user_id, 0)
            sync_potjes_to_tokens(user_id, int(new_balance))
        except Exception as _ex:
            print(f"[potje-sync] failed for {user_id}: {_ex}")

        # v6_auto_provision_001 — auto-register bot + monitor zodat token-holder direct kan starten
        try:
            from modules.trade.monitor import auto_provision_bot_for_token_holder
            auto_provision_bot_for_token_holder(user_id, use_mock=False, auto_trade=True, autostart=False)
        except Exception as _ex:
            print(f"[auto-provision] failed for {user_id}: {_ex}")

    # v6_bonnetje_001 — Bonnetje voor klant-aankoop opslaan in user archief
    try:
        if user_id not in {"user-000", "user-001"}:  # alleen klanten
            from modules.bonnetjes import maak_bonnetje
            # Lookup naam
            users = load_json(DATA_DIR / "system" / "users.json", default={"users": []}).get("users", [])
            naam = next((u.get("naam") for u in users if u.get("id") == user_id), "Klant")
            maak_bonnetje({**tx, "netto_eur": round(amount_eur - tx.get("btw_afgeroomd_eur", 0), 4)}, user_naam=naam)
    except Exception as _ex:
        print(f"[bonnetje-gen] failed: {_ex}")

    return {
        "success": True,
        "message": f"{amount_tokens} ROAR gekocht voor {amount_eur}",
        "transaction": tx,
        "new_roar_balance": roar["balances"][user_id],
        "new_eur_balance": wallets["wallets"][user_id]["balance"],
        "price_per_token": price,
    }


@router.post("/token/sell/{user_id}")
async def sell_tokens(user_id: str, req: SellTokenRequest):
    """Verkoop ROAR tokens terug naar Spark voor EUR - alleen hele tokens"""
    price = get_dynamic_price()
    amount_tokens = int(req.amount_tokens)
    if amount_tokens < 1:
        return {"success": False, "error": "Minimaal 1 token verkopen"}
    amount_eur = round(amount_tokens * price, 2)

    # Check ROAR saldo
    roar = get_roar_data()
    user_roar = roar.get("balances", {}).get(user_id, 0)
    if user_roar < amount_tokens:
        return {"success": False, "error": f"Onvoldoende ROAR. Heb {user_roar}, wil {amount_tokens} verkopen"}

    # Execute
    roar["balances"][user_id] = user_roar - amount_tokens
    roar["balances"]["user-000"] = roar.get("balances", {}).get("user-000", 0) + amount_tokens

    wallets = load_json(WALLET_FILE, default={"wallets": {}, "transactions": []})
    if user_id not in wallets.get("wallets", {}):
        wallets["wallets"][user_id] = {"balance": 0}
    wallets["wallets"][user_id]["balance"] = round(wallets["wallets"][user_id].get("balance", 0) + amount_eur, 2)

    tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "sell_roar",
        "amount_eur": amount_eur,
        "token_amount": amount_tokens,
        "price_per_token": price,
        "description": f"{amount_tokens} ROAR verkocht @ {price}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
    }

    # v4_token_potje_001 — Token-verkoop event-log:
    # 10 tokens = 1 potje-equivalent. Log hoeveel potje-slots vrijkomen voor Spark.
    # Echte capital-vrijgave volgt later bij wallet↔bank koppeling.
    freed_slots = amount_tokens // 10
    if freed_slots > 0:
        tx["freed_potje_slots"] = freed_slots
        tx["description"] = f"{amount_tokens} ROAR verkocht @ {price} → {freed_slots} potje-slot{'s' if freed_slots > 1 else ''} vrij voor Spark"

    fin = load_json(FINANCIAL_FILE, default={"transactions": [], "roar_config": {}})
    fin["transactions"].append(tx)
    save_json(FINANCIAL_FILE, fin)
    wallets["transactions"].append(tx)
    save_json(WALLET_FILE, wallets)
    save_roar_data(roar)

    # v6_accounting_hooks_001 — sell-back → expense spark_core (Refunds)
    try:
        from modules.accounting.hooks import on_sell_back
        on_sell_back(
            seller_user_id=user_id, seller_naam=user.get("naam") or user_id,
            tokens=amount_tokens, total_eur=amount_eur, ref_id=tx["id"],
        )
    except Exception as ex:
        print(f"[sell_back] accounting-hook failed (non-blocking): {ex}")

    return {
        "success": True,
        "message": f"{amount_tokens} ROAR verkocht voor {amount_eur}",
        "transaction": tx,
        "new_roar_balance": roar["balances"].get(user_id, 0),
        "new_eur_balance": wallets["wallets"][user_id]["balance"],
        "price_per_token": price,
    }


# ============================================================
# POTJES SYSTEEM
# ============================================================

@router.get("/potjes/{user_id}")
async def get_potjes(user_id: str):
    """Haal potjes status op"""
    data = load_json(POTJES_FILE, default={"users": {}})
    user_data = data.get("users", {}).get(user_id, {})
    return {"success": True, "user_id": user_id, "potjes": user_data}



# ============================================================
# PRODUCTEN CATALOG
# ============================================================

@router.get("/products")
async def get_products(shop_id: str = "shop-roadkill"):
    """Alle winkel producten ophalen (filter via shop_id; default = Roadkillshop)."""
    pfile = _shop_products_path(shop_id)
    data = load_json(pfile, default={"products": []})
    products = data.get("products", [])
    # ROAR token prijs dynamisch updaten
    price = get_dynamic_price()
    for p in products:
        if p.get("dynamic_price"):
            p["price"] = price
    return {"success": True, "products": products, "shop_id": shop_id, "source": str(pfile)}


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    """Enkel product ophalen"""
    data = load_json(PRODUCTS_FILE, default={"products": []})
    for p in data.get("products", []):
        if p["id"] == product_id:
            if p.get("dynamic_price"):
                p["price"] = get_dynamic_price()
            return {"success": True, "product": p}
    return {"success": False, "error": "Product niet gevonden"}


# v6_shop_product_image_001 — Admin kan product-afbeelding uploaden
@router.post("/products/{product_id}/image")
async def upload_product_image(
    product_id: str,
    image: UploadFile = File(...),
    viewer_id: str = Form(...),
    shop_id: str = Form("shop-roadkill"),
):
    """Upload nieuwe afbeelding voor een product.
    v12_shop_image_owner_container_001 — Opslag verplaatst van globale
    /data/system_archive/foto/ naar de user-eigen container:
    /data/users/{owner}/archive/foto/{file_id}.{ext}, geregistreerd in de
    user's _index.json. URL = /api/archive/{owner}/file/{file_id}.
    Voordeel: bij shop/user-verwijdering gaan alle bijbehorende foto's
    automatisch mee — geen wees-bestanden meer in system_archive.
    """
    _require_admin_or_shop_owner(viewer_id, shop_id)

    ext = Path(image.filename or "img.png").suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(400, f"Image type '{ext}' niet toegestaan")
    data_bytes = await image.read()
    if len(data_bytes) > 8 * 1024 * 1024:
        raise HTTPException(413, "Image te groot (>8MB)")

    # Bepaal shop-owner (waar de foto naartoe geschreven wordt)
    shops = load_json(SHOPS_FILE, default={"shops": []})
    shop = next((s for s in shops.get("shops", []) if s.get("id") == shop_id), None)
    if not shop:
        raise HTTPException(404, "Shop niet gevonden")
    owner = shop.get("owner_user_id") or viewer_id

    # Schrijf naar user-container: /data/users/{owner}/archive/foto/
    user_foto_dir = DATA_DIR / "users" / owner / "archive" / "foto"
    user_foto_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4().hex[:12]
    safe_name = f"{file_id}{ext}"
    dest = user_foto_dir / safe_name
    dest.write_bytes(data_bytes)

    # Lees product-info voor betere index-entry
    pfile = _shop_products_path(shop_id)
    pdata = load_json(pfile, default={"products": []})
    prod = next((p for p in pdata.get("products", []) if p["id"] == product_id), None)
    pname = prod["name"] if prod else product_id

    # Registreer in user's _index.json (zodat quota/list endpoints het meetellen)
    user_index_file = DATA_DIR / "users" / owner / "archive" / "_index.json"
    uidx = load_json(user_index_file, default={"files": []})
    uidx.setdefault("files", []).append({
        "id": file_id, "filename": safe_name,
        "original_name": image.filename or safe_name,
        "category": "foto", "extension": ext,
        "mime_type": image.content_type or "image/png",
        "size_bytes": len(data_bytes),
        "description": f"Winkel-foto: {pname} ({shop.get('naam','')})",
        "tags": ["shop_product", f"shop_{shop_id}", f"product_{product_id}"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": viewer_id, "path": str(dest),
        "linked_product_id": product_id, "linked_shop_id": shop_id,
        "source": "shop_product_image",
    })
    save_json(user_index_file, uidx)

    # Hyperlink naar user-archive endpoint (bestaand): /api/archive/{owner}/file/{file_id}
    image_url = f"/api/archive/{owner}/file/{file_id}"
    if prod:
        imgs = prod.get("images") or ([prod["image_url"]] if prod.get("image_url") else [])
        imgs.append(image_url)
        prod["images"] = imgs
        if not prod.get("image_url"):
            prod["image_url"] = image_url
        prod["image_archive_id"] = file_id
        save_json(pfile, pdata)

    return {"success": True, "image_url": image_url, "archive_id": file_id, "product_id": product_id, "images": prod.get("images") if prod else [image_url]}


# v6_shop_admin_product_crud_001 — Admin product create/edit/delete + image management
class ProductUpsert(BaseModel):
    viewer_id: str
    name: str
    description: Optional[str] = ""
    price: float
    category: Optional[str] = "merch"  # 'merch' | 'digital'
    entity_id: Optional[str] = "roadkill_merch"
    in_stock: Optional[bool] = True
    image_icon: Optional[str] = "package"
    images: Optional[List[str]] = []  # full URLs (sa /api/system-archive/file/...)
    # v11_shop_scope_001 — Product-CRUD moet per shop schrijven, niet in de global PRODUCTS_FILE.
    shop_id: Optional[str] = "shop-roadkill"


def _require_admin(viewer_id: str) -> None:
    """v11_shop_delete_admin_only_001 — Strict admin check (drop legacy grad-2 fallback).
    Reden: Familie op grad-2 zoals Heidi/Lotus/Maaike had toegang tot shop-delete
    e.d. via de legacy check. Nu alleen `admin === true` in users.json = admin.
    """
    users = load_json(DATA_DIR / "system" / "users.json", default={"users": []})
    viewer = next((u for u in users.get("users", []) if u.get("id") == viewer_id), None)
    if not viewer:
        raise HTTPException(403, "Gebruiker niet gevonden")
    if viewer.get("admin") is not True:
        raise HTTPException(403, "Alleen admins")


def _require_admin_or_shop_owner(viewer_id: str, shop_id: str) -> None:
    """v12_shop_owner_perms_001 — Product-CRUD is toegestaan voor:
    - admins (admin===true in users.json), of
    - de eigenaar van de betreffende shop (owner_user_id).
    Voorkomt dat Maaike (niet-admin) haar eigen shop niet kan beheren."""
    users = load_json(DATA_DIR / "system" / "users.json", default={"users": []})
    viewer = next((u for u in users.get("users", []) if u.get("id") == viewer_id), None)
    if not viewer:
        raise HTTPException(403, "Gebruiker niet gevonden")
    if viewer.get("admin") is True:
        return
    shops = load_json(SHOPS_FILE, default={"shops": []})
    shop = next((s for s in shops.get("shops", []) if s.get("id") == shop_id), None)
    if shop and shop.get("owner_user_id") == viewer_id:
        return
    raise HTTPException(403, "Alleen admins of de eigenaar van deze shop")


# v6_shop_delete_001 — delete shop (test/legacy cleanup)
@router.delete("/admin/shops/{shop_id}")
async def admin_delete_shop(shop_id: str, viewer_id: str):
    """Verwijder een shop. Alleen door admin. Roadkillshop (system-default)
    kan niet verwijderd worden."""
    _require_admin(viewer_id)
    if shop_id == "shop-roadkill":
        raise HTTPException(400, "System-default shop kan niet verwijderd worden")
    data = load_json(SHOPS_FILE, default={"shops": []})
    shops = data.get("shops", [])
    before = len(shops)
    data["shops"] = [s for s in shops if s.get("id") != shop_id]
    if len(data["shops"]) == before:
        raise HTTPException(404, f"Shop {shop_id} niet gevonden")
    save_json(SHOPS_FILE, data)
    return {"success": True, "deleted": shop_id, "remaining": len(data["shops"])}


@router.post("/admin/products")
async def admin_create_product(req: ProductUpsert):
    # v12_shop_owner_perms_001 — Shop-owner mag zelf producten aanmaken in eigen shop
    _require_admin_or_shop_owner(req.viewer_id, req.shop_id or "shop-roadkill")
    if req.price < 0:
        raise HTTPException(400, "Prijs mag niet negatief zijn")
    # v11_shop_scope_001 — schrijf naar de container van de opgegeven shop, niet global.
    pfile = _shop_products_path(req.shop_id or "shop-roadkill")
    data = load_json(pfile, default={"products": []})
    pid = req.name.lower().replace(" ", "-").replace("/", "-")[:50] + "-" + uuid.uuid4().hex[:6]
    new_prod = {
        "id": pid, "name": req.name, "description": req.description or "",
        "price": round(req.price, 2),
        "category": req.category, "entity_id": req.entity_id,
        "in_stock": req.in_stock, "image_icon": req.image_icon,
        "images": req.images or [], "image_url": (req.images or [None])[0],
        "shop_id": req.shop_id or "shop-roadkill",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "btw_percentage": 0,  # Verkoopprijs is incl. BTW (per user: zonder BTW = wat ze betalen)
    }
    data.setdefault("products", []).append(new_prod)
    save_json(pfile, data)
    return {"success": True, "product": new_prod}


@router.put("/admin/products/{product_id}")
async def admin_update_product(product_id: str, req: ProductUpsert):
    # v12_shop_owner_perms_001 — Shop-owner mag zelf producten bewerken in eigen shop
    _require_admin_or_shop_owner(req.viewer_id, req.shop_id or "shop-roadkill")
    pfile = _shop_products_path(req.shop_id or "shop-roadkill")
    data = load_json(pfile, default={"products": []})
    for p in data.get("products", []):
        if p["id"] == product_id:
            p["name"] = req.name
            p["description"] = req.description or ""
            p["price"] = round(req.price, 2)
            p["category"] = req.category
            p["entity_id"] = req.entity_id
            p["in_stock"] = req.in_stock
            if req.image_icon:
                p["image_icon"] = req.image_icon
            if req.images is not None:
                p["images"] = req.images
                if req.images:
                    p["image_url"] = req.images[0]
            p["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_json(pfile, data)
            return {"success": True, "product": p}
    raise HTTPException(404, "Product niet gevonden")


@router.delete("/admin/products/{product_id}")
async def admin_delete_product(product_id: str, viewer_id: str, shop_id: str = "shop-roadkill"):
    # v12_shop_owner_perms_001 — Shop-owner mag zelf producten verwijderen in eigen shop
    _require_admin_or_shop_owner(viewer_id, shop_id)
    pfile = _shop_products_path(shop_id)
    data = load_json(pfile, default={"products": []})
    before = len(data.get("products", []))
    data["products"] = [p for p in data.get("products", []) if p["id"] != product_id]
    if len(data["products"]) == before:
        raise HTTPException(404, "Product niet gevonden")
    save_json(pfile, data)
    return {"success": True}


@router.delete("/admin/products/{product_id}/images")
async def admin_remove_product_image(product_id: str, image_url: str, viewer_id: str, shop_id: str = "shop-roadkill"):
    """Verwijder één image-URL uit product.images[]."""
    # v12_shop_owner_perms_001 — Shop-owner mag zelf image losmaken van eigen product
    _require_admin_or_shop_owner(viewer_id, shop_id)
    pfile = _shop_products_path(shop_id)
    data = load_json(pfile, default={"products": []})
    for p in data.get("products", []):
        if p["id"] == product_id:
            p["images"] = [u for u in (p.get("images") or []) if u != image_url]
            if p.get("image_url") == image_url:
                p["image_url"] = (p["images"][0] if p["images"] else None)
            save_json(pfile, data)
            return {"success": True, "images": p["images"]}
    raise HTTPException(404, "Product niet gevonden")


# v6_order_shipped_001 — Markeer order verzonden, stuur bark naar user
class ShipOrderRequest(BaseModel):
    viewer_id: str
    tracking_info: Optional[str] = None
    note: Optional[str] = None


@router.post("/orders/{order_id}/ship")
async def mark_order_shipped(order_id: str, req: ShipOrderRequest):
    _require_admin(req.viewer_id)
    data = load_json(PRODUCTS_FILE, default={"orders": []})
    target = None
    for o in data.get("orders", []):
        if o["id"] == order_id:
            target = o
            break
    if not target:
        raise HTTPException(404, "Order niet gevonden")
    if target["status"] == "verzonden":
        raise HTTPException(400, "Al verzonden")
    target["status"] = "verzonden"
    target["shipped_at"] = datetime.now(timezone.utc).isoformat()
    target["tracking_info"] = req.tracking_info
    target["ship_note"] = req.note
    save_json(PRODUCTS_FILE, data)

    # Markeer admin-taak als done
    try:
        tasks_file = DATA_DIR / "notes" / "tasks.json"
        td = load_json(tasks_file, default={"tasks": []})
        for t in td.get("tasks", []):
            if t.get("order_id") == order_id:
                t["status"] = "done"
                t["completed_at"] = datetime.now(timezone.utc).isoformat()
        save_json(tasks_file, td)
    except Exception:
        pass

    # Bark naar user
    items_summary = ", ".join(f"{i['quantity']}x {i['name']}" for i in target["items"])
    extra = f"\n\n📋 {req.note}" if req.note else ""
    tracking = f"\n\n🚚 Track & trace: {req.tracking_info}" if req.tracking_info else ""
    _bark_to_user(
        target["user_id"],
        f"📦 Je bestelling #{order_id} is onderweg!\n\n{items_summary}{tracking}{extra}",
        kind="order_shipped",
        meta={"order_id": order_id},
    )
    return {"success": True, "order": target}


# ============================================================
# BESTELLINGEN (Merch)
# ============================================================

class OrderItem(BaseModel):
    product_id: str
    quantity: int = 1


class CreateOrderRequest(BaseModel):
    items: List[OrderItem]
    shipping_name: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


@router.post("/orders/{user_id}")
async def create_order(user_id: str, req: CreateOrderRequest):
    """Bestelling plaatsen - trekt af van wallet, boekt in kasboek"""
    data = load_json(PRODUCTS_FILE, default={"products": [], "orders": []})
    products = {p["id"]: p for p in data.get("products", [])}

    # Bouw order items
    order_items = []
    total = 0.0
    for item in req.items:
        prod = products.get(item.product_id)
        if not prod:
            return {"success": False, "error": f"Product {item.product_id} niet gevonden"}
        if not prod.get("in_stock", True):
            return {"success": False, "error": f"{prod['name']} is niet op voorraad"}
        if prod.get("category") == "token":
            return {"success": False, "error": "ROAR tokens koop je via de Token sectie"}

        price = prod["price"]
        line_total = round(price * item.quantity, 2)
        total += line_total
        order_items.append({
            "product_id": item.product_id,
            "name": prod["name"],
            "price": price,
            "quantity": item.quantity,
            "line_total": line_total,
            "entity_id": prod.get("entity_id", "roadkill_merch"),
            "category": prod.get("category", "merch"),
            "metadata": prod.get("metadata", {}),
        })

    total = round(total, 2)

    # Check wallet saldo
    wallets = load_json(WALLET_FILE, default={"wallets": {}, "transactions": []})
    user_wallet = wallets.get("wallets", {}).get(user_id, {"balance": 0})
    if user_wallet.get("balance", 0) < total:
        return {
            "success": False,
            "error": f"Onvoldoende saldo. Heb {user_wallet.get('balance', 0):.2f}, nodig {total:.2f}",
        }

    # Maak order aan
    order_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    order = {
        "id": order_id,
        "user_id": user_id,
        "items": order_items,
        "total": total,
        "status": "besteld",
        "shipping_name": req.shipping_name,
        "shipping_address": req.shipping_address,
        "notes": req.notes,
        "created_at": now,
    }

    # Trek af van wallet
    wallets["wallets"][user_id]["balance"] = round(user_wallet["balance"] - total, 2)
    wallet_tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "purchase",
        "amount": total,
        "message": f"Bestelling #{order_id}: {', '.join(i['name'] for i in order_items)}",
        "created_at": now,
        "status": "completed",
    }
    wallets["transactions"].append(wallet_tx)
    save_json(WALLET_FILE, wallets)

    # Boek in kasboek per entity
    accounting = load_json(ACCOUNTING_FILE, default={"transactions": []})
    for item in order_items:
        acc_tx = {
            "id": str(uuid.uuid4()),
            "type": "income",
            "category": "Sales",
            "amount": item["line_total"],
            "description": f"Verkoop: {item['quantity']}x {item['name']} (order #{order_id})",
            "entity_id": item["entity_id"],
            "date": now,
            "btw_percentage": 21,
            "btw_amount": round(item["line_total"] * 0.21, 2),
            "created_at": now,
            "tx_ref": f"shop_sale_{order_id}_{item['id']}",
        }
        accounting["transactions"].append(acc_tx)
        # v6_accounting_hooks_001 — 2% shop-commissie naar spark_core
        if item["entity_id"] != "spark_core":
            commissie = round(item["line_total"] * 0.02, 2)
            if commissie > 0:
                accounting["transactions"].append({
                    "id": str(uuid.uuid4()),
                    "type": "income",
                    "category": "Sales",
                    "amount": commissie,
                    "description": f"Shop-commissie 2% van {item['entity_id']} (order #{order_id})",
                    "entity_id": "spark_core",
                    "date": now,
                    "btw_percentage": 0,
                    "btw_amount": 0,
                    "created_at": now,
                    "tx_ref": f"shop_commissie_{order_id}_{item['id']}",
                    "source": "auto_hook",
                })
    save_json(ACCOUNTING_FILE, accounting)

    # Sla order op
    if "orders" not in data:
        data["orders"] = []
    data["orders"].append(order)
    save_json(PRODUCTS_FILE, data)

    # Activeer storage-items DIRECT (intern API-call zou ook werken, maar direct is sneller)
    storage_granted_gb = 0
    for item in order_items:
        if item.get("category") == "storage":
            gb_per_unit = (item.get("metadata") or {}).get("gb_amount", 1)
            total_gb = gb_per_unit * item.get("quantity", 1)
            try:
                from modules.user_archive.routes import _load_quota, _save_quota, _user_dir
                _user_dir(user_id)
                quota = _load_quota(user_id)
                quota["purchased_gb"] = (quota.get("purchased_gb", 0) or 0) + total_gb
                quota.setdefault("events", []).append({
                    "type": "purchase",
                    "gb": total_gb,
                    "reason": f"Aankoop: {item['name']} (order #{order_id})",
                    "granted_at": now,
                })
                _save_quota(user_id, quota)
                storage_granted_gb += total_gb
            except Exception as e:
                print(f"[SHOP] Storage activeren mislukt: {e}")

    # v6_order_followup_001 — Bonnetje + admin-taak + bark naar user
    _create_order_bonnetje(user_id, order)
    if any(it.get("category") == "merch" for it in order_items):
        # Fysiek product: admin moet verzenden → bonnetje voor admin + taak + bark
        _create_order_bonnetje(user_id, order, viewer_target="user-001")
        _create_order_admin_task(order)
        _bark_to_user(
            user_id,
            f"🛍️ Je bestelling #{order_id} is binnen!\n\n"
            f"Totaal: €{total:.2f}\n"
            f"Status: in behandeling — admin gaat het inpakken & verzenden.\n"
            f"Je ontvangt een bericht zodra het onderweg is.",
            kind="order_placed",
            meta={"order_id": order_id, "total": total},
        )

    return {
        "success": True,
        "message": f"Bestelling #{order_id} geplaatst!",
        "order": order,
        "new_balance": wallets["wallets"][user_id]["balance"],
        "storage_granted_gb": storage_granted_gb,
    }


# v6_order_followup_001 — Helpers: bonnetje in archief + admin-taak + bark
def _create_order_bonnetje(user_id: str, order: dict, viewer_target: str = None) -> None:
    """Schrijf een Markdown-bonnetje naar user_archive/bestanden."""
    try:
        from modules.user_archive.routes import _user_dir, _load_index, _save_index
        target = viewer_target or user_id
        adir = _user_dir(target) / "bestanden"
        adir.mkdir(parents=True, exist_ok=True)
        file_id = uuid.uuid4().hex[:12]
        fname = f"bestelling_{order['id']}_{file_id}.md"
        dest = adir / fname
        rows = [
            f"# 🧾 Bestelling #{order['id']}",
            "",
            f"**Datum:** {order['created_at']}",
            f"**Klant:** {order.get('shipping_name', '—')}",
            f"**Adres:** {order.get('shipping_address', '—')}",
            "",
            "## Items",
            "",
            "| Aantal | Product | Prijs | Totaal |",
            "|---|---|---|---|",
        ]
        for it in order["items"]:
            rows.append(f"| {it['quantity']} | {it['name']} | €{it['price']:.2f} | €{it['line_total']:.2f} |")
        rows += ["", f"**Totaal: €{order['total']:.2f}**", "",
                 f"**Status:** {order.get('status', 'besteld')}"]
        if order.get("notes"):
            rows += ["", f"**Notitie:** {order['notes']}"]
        dest.write_text("\n".join(rows), encoding="utf-8")
        entry = {
            "id": file_id, "filename": fname, "original_name": f"Bestelling #{order['id']}.md",
            "category": "bestanden", "extension": ".md", "mime_type": "text/markdown",
            "size_bytes": dest.stat().st_size,
            "description": f"Bestelling #{order['id']} — €{order['total']:.2f}",
            "tags": ["bestelling", "bonnetje", f"order_{order['id']}"],
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "uploaded_by": target, "path": str(dest),
            "source": "shop_order", "order_id": order["id"],
            "for_role": "admin" if viewer_target == "user-001" else "user",
        }
        files = _load_index(target)
        files.append(entry)
        _save_index(target, files)
    except Exception as e:
        print(f"[shop] bonnetje schrijven mislukt: {e}")


def _create_order_admin_task(order: dict) -> None:
    """Maak admin-taak in notes voor het verzenden van de bestelling."""
    try:
        tasks_file = DATA_DIR / "notes" / "tasks.json"
        tasks_file.parent.mkdir(parents=True, exist_ok=True)
        d = load_json(tasks_file, default={"tasks": []})
        items_summary = ", ".join(f"{i['quantity']}x {i['name']}" for i in order["items"])
        d["tasks"].append({
            "id": str(uuid.uuid4()),
            "user_id": "user-001",
            "task": f"📦 Bestelling #{order['id']} verzenden — {items_summary} — €{order['total']:.2f} — Klant: {order.get('shipping_name', '?')}",
            "priority": "high",
            "status": "todo",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "source": "shop_order",
            "order_id": order["id"],
            "user_recipient": order["user_id"],
        })
        save_json(tasks_file, d)
    except Exception as e:
        print(f"[shop] admin taak mislukt: {e}")


def _bark_to_user(user_id: str, text: str, kind: str = "order_update", meta: dict = None) -> None:
    """Stuur privé-bark van Spark naar user.

    v13c_bots_consolidatie_001 (sessie 54) — was bot-smith, nu direct Spark
    (user-000). Mr Smith als aparte proxy-identiteit is niet meer nodig; Spark
    handelt shop-attribution zelf af."""
    try:
        bot_id = "user-000"  # Spark zelf
        prive_dir = DATA_DIR / "chat" / "prive"
        prive_dir.mkdir(parents=True, exist_ok=True)
        pair = sorted([bot_id, user_id])
        fp = prive_dir / f"{pair[0]}__{pair[1]}.json"
        data = load_json(fp, default={"messages": []})
        msg = {
            "id": f"pm-{uuid.uuid4().hex[:8]}",
            "from_user_id": bot_id,
            "from_naam": "Spark",
            "to_user_id": user_id,
            "text": text,
            "ts": datetime.now(timezone.utc).isoformat(),
            "unread_by": [user_id],
            "system": True,
            "kind": kind,
            "is_bot": True,
            **(meta or {}),
        }
        data["messages"] = data.get("messages", []) + [msg]
        save_json(fp, data)
    except Exception as e:
        print(f"[shop] bark naar user mislukt: {e}")


@router.get("/orders/{user_id}")
async def get_orders(user_id: str):
    """Bestellingen van gebruiker ophalen"""
    data = load_json(PRODUCTS_FILE, default={"orders": []})
    orders = [o for o in data.get("orders", []) if o.get("user_id") == user_id]
    orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
    return {"success": True, "orders": orders}
