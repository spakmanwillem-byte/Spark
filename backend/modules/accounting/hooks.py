"""
v6_accounting_hooks_001 (sessie 14, 29 mei 2026)
Centrale hooks die financiële events automatisch posten naar
/api/accounting/transactions als single source of truth.

6 hooks (zoals afgesproken met Willem):
  1. on_token_buy()        — ROAR token-aankoop → income spark_core
  2. on_bitvavo_coin_buy() — Trade BUY → expense spark_core (Materiaal)
  3. on_sell_back()        — Refund / opname → expense spark_core (Refunds)
  4. on_shop_sale()        — Product-verkoop → income shop_kasboek + 2% commissie
  5. on_deposit()          — Verbal/bank storting → income personal_<naam>
  6. on_trade_result()     — SELL (winst of verlies) → income/expense Crypto Profit

Elke hook is IDEMPOTENT via tx_ref: poging-#2 met zelfde ref = silent skip.
Faalt geruisloos (log naar print, geen exception) zodat een boekhoud-issue
nooit een product-actie blokkeert.
"""
from pathlib import Path
from datetime import datetime, timezone
import uuid
from typing import Optional, Dict
from modules.core.storage import load_json, save_json

TX_FILE = Path(__file__).parent.parent.parent / "data" / "accounting" / "transactions.json"


def _exists_by_ref(tx_ref: str) -> bool:
    """Idempotency check: skip als tx_ref al geboekt is."""
    if not tx_ref:
        return False
    data = load_json(TX_FILE, default={"transactions": []})
    return any(t.get("tx_ref") == tx_ref for t in data.get("transactions", []))


def _post(
    type_: str,
    category: str,
    amount: float,
    description: str,
    entity_id: str = "spark_core",
    tx_ref: Optional[str] = None,
    btw_percentage: float = 0.0,
    date: Optional[str] = None,
) -> Optional[Dict]:
    """Append een transactie. Stille fail bij errors.
    Returns dict met de nieuwe tx, of None bij skip/error.
    """
    try:
        if tx_ref and _exists_by_ref(tx_ref):
            return None  # idempotent skip
        if amount is None or amount == 0:
            return None
        amount = round(abs(float(amount)), 2)
        data = load_json(TX_FILE, default={"transactions": []})
        btw_amount = round(amount * (btw_percentage / 100), 2) if btw_percentage else 0
        now_iso = datetime.now(timezone.utc).isoformat()
        new_tx = {
            "id": str(uuid.uuid4()),
            "type": type_,
            "category": category,
            "amount": amount,
            "description": description,
            "entity_id": entity_id,
            "date": date or now_iso,
            "btw_percentage": btw_percentage,
            "btw_amount": btw_amount,
            "created_at": now_iso,
            "tx_ref": tx_ref,
            "source": "auto_hook",
        }
        data["transactions"].append(new_tx)
        save_json(TX_FILE, data)
        print(f"[accounting-hook] {type_} €{amount:.2f} {entity_id}/{category} ref={tx_ref}")
        return new_tx
    except Exception as ex:
        print(f"[accounting-hook] FAILED ({type_} €{amount}): {ex}")
        return None


# ============================================================
# HOOK 1 — Token koop (klant koopt ROAR van Spark)
# ============================================================
def on_token_buy(*, buyer_user_id: str, buyer_naam: str, tokens: int,
                 total_eur: float, price_per_token: float, ref_id: str,
                 is_anchor: bool = False, btw_pct: float = 0.0) -> Optional[Dict]:
    """ROAR token-aankoop door klant of anker.
    Anker (Spark/Willem) = fundering, gift_in. Klant = sale.
    """
    category = "Donations" if is_anchor else "Sales"
    desc = f"ROAR-aankoop: {buyer_naam} kocht {tokens} token(s) à €{price_per_token:.2f}"
    return _post(
        type_="income",
        category=category,
        amount=total_eur,
        description=desc,
        entity_id="spark_core",
        tx_ref=f"token_buy_{ref_id}",
        btw_percentage=btw_pct,
    )


# ============================================================
# HOOK 2 — Bitvavo coin-buy (bot doet trade BUY)
# ============================================================
def on_bitvavo_coin_buy(*, user_id: str, user_naam: str, market: str,
                        amount_eur: float, trade_id: str) -> Optional[Dict]:
    """Bot koopt coin op Bitvavo → uitgaande EUR vanuit Spark Core (Materiaal-categorie).
    Wordt later geneutraliseerd door SELL (on_trade_result)."""
    return _post(
        type_="expense",
        category="Materiaal",
        amount=amount_eur,
        description=f"Trade BUY {market}: {user_naam}'s bot inzet €{amount_eur:.2f}",
        entity_id="spark_core",
        tx_ref=f"trade_buy_{trade_id}",
        btw_percentage=0.0,
    )


# ============================================================
# HOOK 3 — Sell-back / refund (user verkoopt tokens terug aan Spark)
# ============================================================
def on_sell_back(*, seller_user_id: str, seller_naam: str, tokens: int,
                 total_eur: float, ref_id: str) -> Optional[Dict]:
    """ROAR sell-back → Spark betaalt EUR uit (Refunds-categorie)."""
    return _post(
        type_="expense",
        category="Refunds",
        amount=total_eur,
        description=f"Sell-back: {seller_naam} verkocht {tokens} ROAR voor €{total_eur:.2f}",
        entity_id="spark_core",
        tx_ref=f"sell_back_{ref_id}",
        btw_percentage=0.0,
    )


# ============================================================
# HOOK 4 — Shop verkoop (product-verkoop in winkelstraat)
# ============================================================
def on_shop_sale(*, shop_id: str, shop_kasboek_id: str, product_naam: str,
                 amount: float, buyer_naam: str, ref_id: str,
                 commissie_pct: float = 2.0) -> Optional[tuple]:
    """Shop-verkoop boekt 2x:
       1. Volledig bedrag als income op shop's kasboek
       2. Commissie als income op spark_core
    """
    # 1. Shop kasboek
    main_tx = _post(
        type_="income",
        category="Sales",
        amount=amount,
        description=f"Verkocht: {product_naam} aan {buyer_naam}",
        entity_id=shop_kasboek_id,
        tx_ref=f"shop_sale_{ref_id}",
        btw_percentage=0.0,
    )
    # 2. Commissie naar spark_core
    commissie = round(amount * commissie_pct / 100, 2)
    com_tx = None
    if commissie > 0:
        com_tx = _post(
            type_="income",
            category="Sales",
            amount=commissie,
            description=f"Shop-commissie {commissie_pct}% van {shop_id} ({product_naam})",
            entity_id="spark_core",
            tx_ref=f"shop_commissie_{ref_id}",
            btw_percentage=0.0,
        )
    return (main_tx, com_tx)


# ============================================================
# HOOK 5 — Storting (verbal of bank-deposit)
# ============================================================
def on_deposit(*, user_id: str, user_naam: str, amount: float,
               source: str, ref_id: str,
               entity_id: Optional[str] = None) -> Optional[Dict]:
    """User stort EUR via Tikkie of bank. Default boek naar privé-entity.
    Voorbeeld: Willem stort €100 → income personal_willem.
    """
    entity = entity_id or (
        "personal_willem" if user_id == "user-001"
        else "spark_core"  # Spark = systeem-storting
    )
    return _post(
        type_="income",
        category="Donations" if entity == "spark_core" else "Sales",
        amount=amount,
        description=f"Storting {user_naam} via {source}",
        entity_id=entity,
        tx_ref=f"deposit_{ref_id}",
        btw_percentage=0.0,
    )


# ============================================================
# HOOK 6 — Trade resultaat (winst of verlies bij SELL)
# ============================================================
def on_trade_result(*, user_id: str, user_naam: str, market: str,
                    buy_amount: float, sell_amount: float,
                    trade_id: str) -> Optional[Dict]:
    """Bot sluit positie → boek winst (income) of verlies (expense) op spark_core.
    Crypto Profit-categorie zodat het apart geanalyseerd kan worden.
    """
    pnl = round(sell_amount - buy_amount, 2)
    if abs(pnl) < 0.01:
        return None  # te klein om te boeken
    is_profit = pnl > 0
    return _post(
        type_="income" if is_profit else "expense",
        category="Crypto Profit",
        amount=abs(pnl),
        description=(
            f"Trade {('WINST' if is_profit else 'VERLIES')} {market}: "
            f"{user_naam} sloot positie (€{buy_amount:.2f} → €{sell_amount:.2f})"
        ),
        entity_id="spark_core",
        tx_ref=f"trade_result_{trade_id}",
        btw_percentage=0.0,
    )
