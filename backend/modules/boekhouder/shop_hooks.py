"""v13_shop_transaction_hook_001 — Shop-verkoop/aankoop → Boekhouding brug.

v13b_btw_kor_openstaand_001 (feb 2026): verkoop-flow nu met echte BTW-regels:
  - User geeft NETTO verkoopprijs op
  - BRUTO = NETTO * (1 + btw_pct/100)  (of BRUTO=NETTO als KOR actief)
  - Verkoper's book krijgt NETTO als omzet (schone Moneybird-boekhouding)
  - BTW-bedrag = BRUTO - NETTO staat op koper-bon, verkoper is zelf verantwoordelijk
    voor BTW-aangifte via externe boekhouder
  - Spark-vergoeding = spark_pct% van BRUTO — NIET direct ingehouden, wel opgeteld
    bij openstaand_spark.json per shop. Winkeleigenaar lost handmatig in via wallet.

Publieke API:
    record_shop_sale(shop_id, netto_eur, ...)  → 2 bonnen + boeking + openstaand
    record_shop_purchase(shop_id, amount_eur, ...)
    get_openstaand(shop_id)                     → totaal + entries
    inlossen_openstaand(shop_id, actor_user_id) → trekt wallet, boekt naar spark-core
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json
from modules.boekhouder import books as book_svc


DATA_ROOT = Path(__file__).parent.parent.parent / "data"
SHOPS_FP = DATA_ROOT / "shops" / "_meta.json"
BOOKS_ROOT = DATA_ROOT / "boekhouding" / "books"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_shop(shop_id: str) -> Optional[Dict]:
    d = load_json(SHOPS_FP, default={"shops": []})
    for s in d.get("shops", []):
        if s.get("id") == shop_id:
            return s
    return None


def _shop_config() -> Dict:
    d = load_json(SHOPS_FP, default={})
    return d.get("config", {})


def _find_shop_book(shop_id: str) -> Optional[Dict]:
    for meta in book_svc.list_books(owner_user_id=None):
        if meta.get("linked_shop_id") == shop_id:
            return meta
    return None


def _openstaand_fp(book_id: str) -> Path:
    return BOOKS_ROOT / book_id / "openstaand_spark.json"


def _log_winst_event(shop_id: str, book_id: str, bruto: float, netto: float,
                     btw_eur: float, spark_fee: float, kor: bool,
                     event_type: str, source_id: Optional[str] = None):
    """Losse topic 'winst_events' in de papertrail."""
    try:
        from modules.boekhouder.agents.log_agent import LogAgent
        LogAgent().record(
            topic="winst_events",
            event_type=event_type,
            actor=book_id,
            data={
                "shop_id": shop_id,
                "book_id": book_id,
                "bruto_eur": round(bruto, 2),
                "netto_eur": round(netto, 2),
                "btw_eur": round(btw_eur, 2),
                "spark_deel_eur": round(spark_fee, 2),  # backward-compat naam
                "spark_fee_eur": round(spark_fee, 2),
                "kor_actief": kor,
                "source_id": source_id,
            },
        )
    except Exception:
        pass


def record_shop_sale(shop_id: str, netto_eur: float, koper_naam: str = "",
                     remittance: str = "", source_id: Optional[str] = None,
                     btw_pct_override: Optional[float] = None,
                     spark_pct_override: Optional[float] = None) -> Dict:
    """Verkoop-flow met BTW, KOR en openstaande Spark-vergoeding.

    Boekt NETTO als omzet in verkoper-book (schoon voor Moneybird).
    Genereert 2 bonnen (verkoper-netto + verkoper-bruto/koper-bruto).
    Spark-vergoeding wordt opgeteld bij openstaand, niet direct ingehouden.
    """
    shop = _get_shop(shop_id)
    if not shop:
        return {"success": False, "error": f"Shop {shop_id} niet gevonden"}
    shop_book = _find_shop_book(shop_id)
    if not shop_book:
        shop_book = book_svc.ensure_shop_book(shop_id, shop.get("owner_user_id"), shop.get("naam"))

    cfg = _shop_config()
    btw_pct = btw_pct_override if btw_pct_override is not None else float(shop.get("btw_pct", cfg.get("btw_default_pct", 21.0)))
    kor = bool(shop.get("btw_kor_actief", cfg.get("btw_kor_default", False)))
    spark_pct = spark_pct_override if spark_pct_override is not None else float(shop.get("commissie_pct", cfg.get("spark_fee_pct", 1.0)))

    netto = float(netto_eur)
    if kor:
        bruto = netto
        btw_eur = 0.0
    else:
        bruto = round(netto * (1 + btw_pct / 100.0), 2)
        btw_eur = round(bruto - netto, 2)
    spark_fee = round(bruto * spark_pct / 100.0, 2)

    # 1. NETTO → shop-book (echte omzet)
    entry_shop = book_svc.add_entry(shop_book["id"], {
        "type": "shop_sale_netto",
        "amount_eur": netto,
        "naam": f"Verkoop{f' aan {koper_naam}' if koper_naam else ''}",
        "note": remittance or f"Bruto €{bruto:.2f} (waarvan BTW €{btw_eur:.2f}). Spark-fee €{spark_fee:.2f} openstaand.",
        "source": "shop_hook",
        "source_id": source_id,
        "tags": ["verkoop", "netto", f"shop_{shop_id}", f"btw_{btw_pct}", "kor" if kor else "btw_plichtig"],
    })

    # 2. Openstaande Spark-vergoeding bijboeken (nog niet ingelost)
    ofp = _openstaand_fp(shop_book["id"])
    odata = load_json(ofp, default={"totaal_openstaand_eur": 0.0, "entries": []})
    odata["totaal_openstaand_eur"] = round(odata.get("totaal_openstaand_eur", 0.0) + spark_fee, 2)
    odata["entries"].append({
        "id": "os-" + secrets.token_hex(4),
        "ts": _now(),
        "bruto_eur": bruto,
        "netto_eur": netto,
        "btw_eur": btw_eur,
        "spark_fee_eur": spark_fee,
        "source_id": source_id,
        "shop_entry_id": entry_shop.get("id") if entry_shop else None,
    })
    save_json(ofp, odata)

    # 3. Papertrail winst_event
    _log_winst_event(shop_id, shop_book["id"], bruto, netto, btw_eur, spark_fee, kor, "shop_sale", source_id)

    # 4. Bonnen genereren (JSON — PDF komt later)
    bon_id = "bon-" + secrets.token_hex(4)
    ts = _now()
    bon_netto = {
        "type": "verkoper_netto",
        "bon_id": bon_id + "-N",
        "shop_naam": shop.get("naam"),
        "verkoop_ts": ts,
        "netto_eur": netto,
        "koper_naam": koper_naam or "Anoniem",
        "toelichting": "Interne kasboek-regel voor verkoper (Moneybird-import)",
    }
    bon_bruto = {
        "type": "koper_factuur",
        "bon_id": bon_id + "-B",
        "shop_naam": shop.get("naam"),
        "verkoop_ts": ts,
        "netto_eur": netto,
        "btw_pct": 0.0 if kor else btw_pct,
        "btw_eur": btw_eur,
        "bruto_eur": bruto,
        "kor_actief": kor,
        "koper_naam": koper_naam or "Anoniem",
        "opmerking": "Kleine ondernemersregeling — geen BTW berekend" if kor else f"BTW {btw_pct}% inbegrepen",
    }

    return {
        "success": True,
        "netto_eur": netto,
        "btw_eur": btw_eur,
        "bruto_eur": bruto,
        "btw_pct": 0.0 if kor else btw_pct,
        "kor_actief": kor,
        "spark_fee_eur": spark_fee,
        "spark_fee_pct": spark_pct,
        "openstaand_totaal_eur": odata["totaal_openstaand_eur"],
        "entry_shop": entry_shop,
        "bonnen": {"netto": bon_netto, "bruto": bon_bruto},
    }


def record_shop_purchase(shop_id: str, amount_eur: float, leverancier_naam: str = "",
                         remittance: str = "", source_id: Optional[str] = None) -> Dict:
    shop = _get_shop(shop_id)
    if not shop:
        return {"success": False, "error": f"Shop {shop_id} niet gevonden"}
    shop_book = _find_shop_book(shop_id)
    if not shop_book:
        shop_book = book_svc.ensure_shop_book(shop_id, shop.get("owner_user_id"), shop.get("naam"))
    entry = book_svc.add_entry(shop_book["id"], {
        "type": "shop_purchase",
        "amount_eur": -abs(amount_eur),
        "naam": f"Inkoop{f' bij {leverancier_naam}' if leverancier_naam else ''}",
        "note": remittance or "",
        "source": "shop_hook",
        "source_id": source_id,
        "tags": ["inkoop", f"shop_{shop_id}"],
    })
    return {"success": True, "entry": entry}


def get_openstaand(shop_id: str) -> Dict:
    shop_book = _find_shop_book(shop_id)
    if not shop_book:
        return {"success": False, "error": "Geen boek voor deze shop"}
    ofp = _openstaand_fp(shop_book["id"])
    data = load_json(ofp, default={"totaal_openstaand_eur": 0.0, "entries": []})
    return {"success": True, "book_id": shop_book["id"], **data}


def inlossen_openstaand(shop_id: str, actor_user_id: str) -> Dict:
    """Boek de openstaande Spark-vergoeding als uitgave in shop-book + inkomst in spark-core.
    Wallet-integratie: probeer wallet-inhouding; als wallet-module niet werkt, boek gewoon door.
    """
    shop = _get_shop(shop_id)
    if not shop:
        return {"success": False, "error": "Shop niet gevonden"}
    shop_book = _find_shop_book(shop_id)
    if not shop_book:
        return {"success": False, "error": "Geen boek"}
    ofp = _openstaand_fp(shop_book["id"])
    data = load_json(ofp, default={"totaal_openstaand_eur": 0.0, "entries": []})
    total = round(data.get("totaal_openstaand_eur", 0.0), 2)
    if total <= 0:
        return {"success": False, "error": "Niks openstaand"}

    # Wallet-trek (best-effort)
    wallet_msg = "wallet niet gekoppeld"
    try:
        from modules.wallet.service import spend_tokens  # best-guess API
        r = spend_tokens(actor_user_id, total, reden=f"Spark-fee inlossen {shop_id}")
        wallet_msg = f"wallet: {r}" if r else "wallet-trek zonder response"
    except Exception as e:
        wallet_msg = f"wallet niet gebruikt ({str(e)[:60]})"

    # Boek uitgave in shop-book
    entry_shop = book_svc.add_entry(shop_book["id"], {
        "type": "spark_fee_inlossen",
        "amount_eur": -total,
        "naam": f"Spark-vergoeding inlossen ({data.get('entries', [])[-1:] and 'batch'} of {len(data.get('entries',[]))} regels)",
        "note": f"Inlossing openstaande Spark-vergoedingen. {wallet_msg}",
        "source": "spark_fee_inlossen",
        "source_id": None,
        "tags": ["spark_fee", "inlossen"],
    })
    # Boek inkomst in spark-core
    entry_spark = book_svc.add_entry("book-spark-core", {
        "type": "spark_fee_income",
        "amount_eur": total,
        "naam": f"Spark-vergoeding uit {shop.get('naam')}",
        "note": f"{len(data.get('entries',[]))} verkopen ingelost door {actor_user_id}",
        "source": "spark_fee_inlossen",
        "source_id": None,
        "tags": ["spark_fee", "income", f"shop_{shop_id}"],
    })

    # Reset openstaand + archief
    data.setdefault("history", []).append({
        "ingelost_ts": _now(),
        "totaal_eur": total,
        "n_entries": len(data.get("entries", [])),
        "actor": actor_user_id,
        "wallet_msg": wallet_msg,
    })
    data["entries"] = []
    data["totaal_openstaand_eur"] = 0.0
    save_json(ofp, data)

    return {
        "success": True,
        "ingelost_eur": total,
        "entry_shop": entry_shop,
        "entry_spark": entry_spark,
        "wallet_msg": wallet_msg,
    }
