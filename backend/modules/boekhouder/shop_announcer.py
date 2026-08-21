"""v13n_shop_announcer_001 — Per-user shop-announcer via boekhouder-bot.

Vult het gat dat weekly_report.py niet meer vult (audit_log leeg na v13 nulpunt).
Deze announcer leest uit de NIEUWE boek-structuur (shop-books) en stuurt per
shop-eigenaar een privé DM met zijn eigen omzet van de afgelopen periode.

Admin (gradatie ≤ 2) kan aggregatie ophalen via aparte route.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json
from modules.boekhouder import books as book_svc
from modules.boekhouder.service import _send_dm

DATA_ROOT = Path(__file__).parent.parent.parent / "data"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_days_ago(days: int) -> str:
    return (_now() - timedelta(days=days)).isoformat()


def build_user_shop_report(user_id: str, days: int = 7) -> Dict:
    """Verzamel omzet-rapport voor 1 user: alle zijn/haar shop-books, laatste N dagen."""
    since = _iso_days_ago(days)
    period = f"laatste {days} dagen"
    shops_report: List[Dict] = []
    total_omzet = 0.0
    total_uitgaven = 0.0
    total_openstaand = 0.0
    total_n_verkopen = 0

    for meta in book_svc.list_books(owner_user_id=None):
        if meta.get("type") != "shop" or meta.get("owner_user_id") != user_id:
            continue
        entries = book_svc.list_entries(meta["id"], limit=100_000)
        recent = [e for e in entries if (e.get("ts") or "") >= since]
        income = sum(e["amount_eur"] for e in recent if e["amount_eur"] > 0)
        expense = sum(abs(e["amount_eur"]) for e in recent if e["amount_eur"] < 0)
        n_verkopen = sum(1 for e in recent if e.get("type") == "shop_sale_netto")
        # openstaand
        ofp = book_svc._book_dir(meta["id"]) / "openstaand_spark.json"
        os_total = 0.0
        if ofp.exists():
            os_data = load_json(ofp, default={})
            os_total = float(os_data.get("totaal_openstaand_eur", 0.0) or 0.0)
        shops_report.append({
            "book_id": meta["id"],
            "shop_naam": meta["naam"],
            "linked_shop_id": meta.get("linked_shop_id"),
            "n_entries": len(recent),
            "n_verkopen": n_verkopen,
            "omzet_eur": round(income, 2),
            "uitgaven_eur": round(expense, 2),
            "resultaat_eur": round(income - expense, 2),
            "openstaand_spark_fee_eur": round(os_total, 2),
        })
        total_omzet += income
        total_uitgaven += expense
        total_openstaand += os_total
        total_n_verkopen += n_verkopen

    return {
        "user_id": user_id,
        "period": period,
        "since": since,
        "shops": shops_report,
        "summary": {
            "n_shops": len(shops_report),
            "n_verkopen": total_n_verkopen,
            "omzet_eur": round(total_omzet, 2),
            "uitgaven_eur": round(total_uitgaven, 2),
            "resultaat_eur": round(total_omzet - total_uitgaven, 2),
            "openstaand_spark_fee_eur": round(total_openstaand, 2),
        },
    }


def announce_to_user(user_id: str, days: int = 7, force: bool = False) -> Dict:
    """Bouw rapport + verstuur privé DM van boekhouder-bot naar user.
    Skip als er geen shops of geen verkeer (tenzij force=True)."""
    report = build_user_shop_report(user_id, days=days)
    s = report["summary"]
    if not report["shops"]:
        return {"success": True, "sent": False, "reason": "user heeft geen shop-boeken"}
    if s["n_verkopen"] == 0 and not force:
        return {"success": True, "sent": False, "reason": "geen verkopen in periode"}

    arrow = "📈" if s["resultaat_eur"] >= 0 else "📉"
    shop_bullets = "\n".join(
        f"• {sh['shop_naam']}: {sh['n_verkopen']}× verkocht, omzet €{sh['omzet_eur']:.2f}"
        + (f", openstaand Spark-fee €{sh['openstaand_spark_fee_eur']:.2f}" if sh['openstaand_spark_fee_eur'] > 0 else "")
        for sh in report["shops"]
    )
    text = (
        f"{arrow} **Shop-rapport {report['period']}**\n\n"
        f"{shop_bullets}\n\n"
        f"**Totaal**: {s['n_verkopen']}× verkopen, omzet €{s['omzet_eur']:.2f}, "
        f"resultaat €{s['resultaat_eur']:+.2f}"
        + (f"\n\n⚠️ Openstaand Spark-fee: €{s['openstaand_spark_fee_eur']:.2f} — los in via wallet." if s['openstaand_spark_fee_eur'] > 0 else "")
    )
    _send_dm(text, kind="boekhouder_user_shop_report", extra={"period_days": days}, recipient_id=user_id)
    return {"success": True, "sent": True, "recipient": user_id, "report": report}


def announce_all_shop_owners(days: int = 7, force: bool = False) -> Dict:
    """Voor alle users met minstens 1 shop-book: bouw + verzend rapport."""
    results = []
    seen: set = set()
    for meta in book_svc.list_books(owner_user_id=None):
        if meta.get("type") != "shop":
            continue
        uid = meta.get("owner_user_id")
        if not uid or uid in seen:
            continue
        seen.add(uid)
        results.append({"user_id": uid, **announce_to_user(uid, days=days, force=force)})
    return {"success": True, "n_users": len(results), "results": results}


def admin_aggregate_report(days: int = 7) -> Dict:
    """Admin overzicht: per shop-owner de rapport-samenvatting. Alleen voor gradatie ≤ 2."""
    reports = []
    seen: set = set()
    for meta in book_svc.list_books(owner_user_id=None):
        if meta.get("type") != "shop":
            continue
        uid = meta.get("owner_user_id")
        if not uid or uid in seen:
            continue
        seen.add(uid)
        reports.append(build_user_shop_report(uid, days=days))
    total_omzet = sum(r["summary"]["omzet_eur"] for r in reports)
    total_openstaand = sum(r["summary"]["openstaand_spark_fee_eur"] for r in reports)
    return {
        "success": True,
        "period_days": days,
        "per_user": reports,
        "aggregate": {
            "n_users_with_shops": len(reports),
            "totaal_omzet_eur": round(total_omzet, 2),
            "totaal_openstaand_spark_fee_eur": round(total_openstaand, 2),
        },
    }
