"""
v6_boekhouder_weekrapport_001 (sessie 14, 29 mei 2026)
Wekelijks Boekhouder-rapport — laat de stille groei van Spark Core zien.

Trigger: scheduler op zondag 20:00 (env-aware: respecteert _maybe_*-pattern).
Output:
  1. PM naar admin (Willem) via _send_dm
  2. Optioneel community-post (gradatie >= 5 trigger)
  3. Snapshot in /data/boekhouder/weekly_reports.json voor history

Inhoud rapport:
  - Anchor capital this week (van X → Y, totaal +€Z)
  - Overflow_pool growth (delta)
  - Mints deze week (aantal + ID's)
  - Trade results (winst/verlies SELLs)
  - ROAR transactions (buy / sell-back delta)
  - Projectie: bij dit tempo anchors-payback in N maanden
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from modules.core.storage import load_json, save_json

DATA = Path(__file__).parent.parent.parent / "data"
POTJES_FILE = DATA / "financial" / "user_potjes.json"
ROAR_FILE = DATA / "roar" / "roar_balances.json"
REPORTS_FILE = DATA / "boekhouder" / "weekly_reports.json"
GROWTH_STATE = DATA / "trade" / "growth_state.json"

# v13p_weekly_bookbased_001 — nieuwe bron: boek-entries per boek.
# audit_log.json + accounting/transactions.json zijn niet meer de bron sinds v13
# nulpunt en de multi-book refactor. Weekly report leest nu uit
# /data/boekhouding/books/*/kasboek.json.
BOOKS_ROOT = DATA / "boekhouding" / "books"

ADMIN_USER = "user-001"
SPARK_USER = "user-000"
RENTE_PCT_PER_MAAND = 1.5  # mirror van staking_growth


def _filter_tx_since(transactions: List[Dict], since: datetime, ts_key: str = "created_at") -> List[Dict]:
    out = []
    for t in transactions:
        ts_str = t.get(ts_key) or t.get("date") or t.get("ts") or t.get("timestamp")
        if not ts_str:
            continue
        try:
            tdt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if tdt >= since:
                out.append(t)
        except Exception:
            continue
    return out


def _projectie_text(total_anchor_value: float, weekly_growth: float) -> str:
    """Geef projectie in mensentaal."""
    if weekly_growth <= 0 or total_anchor_value <= 0:
        return "Nog geen tempo te meten — wacht op eerste winstronde."
    weken_terugverdiend = total_anchor_value / weekly_growth
    if weken_terugverdiend < 52:
        return f"Bij dit tempo (€{weekly_growth:.2f}/week) verdienen anchors zichzelf in **{weken_terugverdiend:.0f} weken** terug."
    jaren = weken_terugverdiend / 52
    return f"Bij dit tempo (€{weekly_growth:.2f}/week) verdienen anchors zichzelf in **{jaren:.1f} jaar** terug."


def build_weekly_report(force_since_days: int = 7) -> Dict:
    """Bouw het rapport-dict voor de afgelopen week.
    Geen mutaties — read-only aggregator.
    """
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=force_since_days)

    # --- Spark potjes ---
    potjes = load_json(POTJES_FILE, default={"users": {}})
    spark = potjes.get("users", {}).get(SPARK_USER, {})
    anchors = [p for p in spark.get("potjes", []) if p.get("pot_locked")]
    trade_pots = [p for p in spark.get("potjes", []) if not p.get("pot_locked")]
    overflow_now = float(spark.get("overflow_pool", 0))

    # Anchor groei deze week — uit growth_log per anchor
    anchor_growth_total = 0.0
    anchor_changes = []
    for a in anchors:
        log = a.get("growth_log", [])
        week_entries = []
        for e in log:
            try:
                edt = datetime.fromisoformat((e.get("ts", "")).replace("Z", "+00:00"))
                if edt >= since:
                    week_entries.append(e)
            except Exception:
                continue
        week_growth = sum(e.get("amount", 0) for e in week_entries)
        if week_growth > 0:
            anchor_growth_total += week_growth
            anchor_changes.append({
                "pot_id": a["id"], "market": a.get("market"),
                "growth_eur": round(week_growth, 4),
                "capital_now": round(a.get("capital", 10.0), 4),
            })

    # Mints deze week (nieuwe potjes)
    mints_this_week = [
        p for p in spark.get("potjes", [])
        if p.get("minted_at") and datetime.fromisoformat(p["minted_at"].replace("Z", "+00:00")) >= since
    ]

    # v13p_weekly_bookbased_001 — Boek-entries aggregatie (nieuwe bron)
    # Loop door alle /data/boekhouding/books/book-*/kasboek.json bestanden en
    # tel per book de income/expense van entries met ts >= since.
    books_summary: List[Dict] = []
    total_income_books = 0.0
    total_expense_books = 0.0
    total_entries_week = 0
    if BOOKS_ROOT.exists():
        for bdir in sorted(BOOKS_ROOT.glob("book-*")):
            if not bdir.is_dir():
                continue
            meta = load_json(bdir / "_meta.json", default=None)
            if not meta:
                continue
            kasboek = load_json(bdir / "kasboek.json", default={"entries": []})
            recent = _filter_tx_since(kasboek.get("entries", []), since, ts_key="ts")
            if not recent:
                continue
            b_income = sum(e.get("amount_eur", 0) for e in recent if e.get("amount_eur", 0) > 0)
            b_expense = sum(abs(e.get("amount_eur", 0)) for e in recent if e.get("amount_eur", 0) < 0)
            b_net = round(b_income - b_expense, 2)
            total_income_books += b_income
            total_expense_books += b_expense
            total_entries_week += len(recent)
            books_summary.append({
                "book_id": meta.get("id"),
                "naam": meta.get("naam", "?"),
                "type": meta.get("type"),
                "owner_user_id": meta.get("owner_user_id"),
                "n_entries": len(recent),
                "income_eur": round(b_income, 2),
                "expense_eur": round(b_expense, 2),
                "netto_eur": b_net,
            })

    # Crypto Profit approximatie uit spark-core book (source contains 'trade')
    crypto_pnl_in = 0.0
    crypto_pnl_out = 0.0
    spark_book_dir = BOOKS_ROOT / "book-spark-core"
    if spark_book_dir.exists():
        spark_kb = load_json(spark_book_dir / "kasboek.json", default={"entries": []})
        recent_spark = _filter_tx_since(spark_kb.get("entries", []), since, ts_key="ts")
        for e in recent_spark:
            src = (e.get("source") or "").lower()
            if "trade" in src or "spark_fee" in src or "winst" in src:
                amt = e.get("amount_eur", 0)
                if amt > 0:
                    crypto_pnl_in += amt
                elif amt < 0:
                    crypto_pnl_out += abs(amt)
    crypto_net = round(crypto_pnl_in - crypto_pnl_out, 2)

    # ROAR token activiteit
    roar = load_json(ROAR_FILE, default={"transactions": []})
    week_roar = _filter_tx_since(roar.get("transactions", []), since, ts_key="ts")
    tokens_bought = sum(t.get("amount", 0) for t in week_roar if t.get("type") == "buy_roar")
    tokens_sold = sum(t.get("amount", 0) for t in week_roar if t.get("type") == "sell_roar")
    eur_in = sum(t.get("amount_eur", 0) for t in week_roar if t.get("type") == "buy_roar")
    eur_out = sum(t.get("amount_eur", 0) for t in week_roar if t.get("type") == "sell_roar")

    # Totaal anchor-waarde (voor projectie)
    total_anchor_value = sum(a.get("capital", 10.0) for a in anchors)

    return {
        "period": {
            "from": since.isoformat(),
            "to": now.isoformat(),
            "days": force_since_days,
        },
        "anchors": {
            "count": len(anchors),
            "total_capital": round(total_anchor_value, 2),
            "weekly_growth": round(anchor_growth_total, 4),
            "changes": anchor_changes,
        },
        "trade_pots": {
            "count": len(trade_pots),
            "minted_this_week": [p["id"] for p in mints_this_week],
        },
        "overflow_pool": {
            "now": round(overflow_now, 2),
        },
        "trade_results": {
            "winst_total": round(crypto_pnl_in, 2),
            "verlies_total": round(crypto_pnl_out, 2),
            "netto": crypto_net,
        },
        "boeken": {
            "n_boeken_actief": len(books_summary),
            "n_entries_week": total_entries_week,
            "total_income_eur": round(total_income_books, 2),
            "total_expense_eur": round(total_expense_books, 2),
            "netto_eur": round(total_income_books - total_expense_books, 2),
            "per_book": books_summary,
        },
        "roar_activity": {
            "tokens_bought": int(tokens_bought),
            "tokens_sold_back": int(tokens_sold),
            "eur_in": round(eur_in, 2),
            "eur_out": round(eur_out, 2),
        },
        "projection": _projectie_text(total_anchor_value, anchor_growth_total),
        "generated_at": now.isoformat(),
    }


def format_report_text(report: Dict) -> str:
    """Mooie chat-tekst voor PM/bark."""
    a = report["anchors"]
    t = report["trade_results"]
    r = report["roar_activity"]
    ov = report["overflow_pool"]
    mints = report["trade_pots"]["minted_this_week"]

    lines = [
        f"🌱 **Boekhouder weekrapport** ({report['period']['days']} dagen)",
        "",
        f"⚓ **Anchors**: {a['count']} stuks, totaal capital €{a['total_capital']:.2f}",
    ]
    if a["weekly_growth"] > 0:
        lines.append(f"   → Groei deze week: **+€{a['weekly_growth']:.4f}**")
    else:
        lines.append(f"   → Geen rente deze week (interval 30 dagen)")

    lines.append("")
    lines.append(f"💼 **Trade-potjes**: {report['trade_pots']['count']} stuks")
    if mints:
        lines.append(f"   → 🎉 {len(mints)} nieuw geminted: {', '.join(mints)}")

    lines.append("")
    lines.append(f"💰 **Trade resultaat**: €{t['netto']:+.2f}")
    if t['winst_total'] > 0 or t['verlies_total'] > 0:
        lines.append(f"   → Winst €{t['winst_total']:.2f} · Verlies €{t['verlies_total']:.2f}")

    # v13p_weekly_bookbased_001 — per-book breakdown
    boeken = report.get("boeken", {})
    per_book = boeken.get("per_book", [])
    if per_book:
        lines.append("")
        lines.append(f"📚 **Boeken deze week** — {boeken.get('n_entries_week', 0)} regels · netto €{boeken.get('netto_eur', 0):+.2f}")
        for b in per_book:
            lines.append(
                f"   • {b['naam']} · {b['n_entries']} regels · "
                f"in €{b['income_eur']:.2f} · uit €{b['expense_eur']:.2f} · "
                f"netto €{b['netto_eur']:+.2f}"
            )
    else:
        lines.append("")
        lines.append("📚 **Boeken deze week**: geen boekingen")

    lines.append("")
    lines.append(f"🌊 **Overflow pool**: €{ov['now']:.2f}")

    if r['tokens_bought'] > 0 or r['tokens_sold_back'] > 0:
        lines.append("")
        lines.append(f"🪙 **ROAR**: +{r['tokens_bought']} gekocht (€{r['eur_in']:.2f}) · -{r['tokens_sold_back']} verkocht (€{r['eur_out']:.2f})")

    lines.append("")
    lines.append(f"📈 _{report['projection']}_")

    return "\n".join(lines)


def send_weekly_report(also_community: bool = False, also_token_holders: bool = True) -> Dict:
    """Bouw + verstuur + archiveer rapport.

    v6_weekrapport_token_holders_001 (sessie 14) — `also_token_holders=True` stuurt
    het rapport ook als PM naar iedereen die >=1 ROAR token bezit. Idee van Willem:
    "iedereen die een token heeft krijgt denk ik die output via bot". Zo voelen
    holders de groei van hun investering, zonder gedwongen app-login.
    """
    from modules.boekhouder.service import _send_dm, _post_community
    report = build_weekly_report()
    text = format_report_text(report)
    recipients = [ADMIN_USER]

    # 1. PM naar admin
    try:
        _send_dm(text, kind="boekhouder_weekly_report",
                 extra={"report": report}, recipient_id=ADMIN_USER)
    except Exception as e:
        print(f"[weekly-report] PM admin failed: {e}")

    # 2. v6_weekrapport_token_holders_001 — PM aan alle ROAR token-houders
    holder_count = 0
    if also_token_holders:
        try:
            ROAR = DATA / "roar" / "roar_balances.json"
            roar = load_json(ROAR, default={"balances": {}})
            balances = roar.get("balances", {})
            # Spark (treasury) en admin zelf overslaan (admin krijgt 'm al hierboven)
            ANCHOR_USERS = {"user-000", ADMIN_USER}
            for uid, bal in balances.items():
                tokens = bal.get("amount", 0) if isinstance(bal, dict) else bal
                if tokens >= 1 and uid not in ANCHOR_USERS:
                    try:
                        _send_dm(text, kind="boekhouder_weekly_report",
                                 extra={"report": report, "as_holder": True},
                                 recipient_id=uid)
                        recipients.append(uid)
                        holder_count += 1
                    except Exception as e:
                        print(f"[weekly-report] PM holder {uid} failed: {e}")
        except Exception as e:
            print(f"[weekly-report] holder-broadcast failed: {e}")

    # 3. Optioneel community-post
    if also_community:
        try:
            anchors_total = report["anchors"]["total_capital"]
            growth = report["anchors"]["weekly_growth"]
            short = (f"🌱 Spark Core deze week: anchors €{anchors_total:.2f}"
                     + (f" (+€{growth:.4f})" if growth > 0 else "")
                     + f", overflow €{report['overflow_pool']['now']:.2f}")
            _post_community(short, kind="boekhouder_weekly")
        except Exception as e:
            print(f"[weekly-report] community-post failed: {e}")

    # 4. Archiveer
    archive = load_json(REPORTS_FILE, default={"reports": []})
    report["recipients"] = recipients
    archive["reports"].append(report)
    if len(archive["reports"]) > 200:
        archive["reports"] = archive["reports"][-200:]
    save_json(REPORTS_FILE, archive)

    return {"success": True, "report": report, "text": text,
            "recipients_count": len(recipients), "holder_pms": holder_count}


# ============================================================
# Endpoint (admin trigger + history view)
# ============================================================
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/boekhouder/weekly", tags=["boekhouder-weekly"])


def _is_admin(viewer_id: str) -> bool:
    from pathlib import Path as _P
    USERS = _P(__file__).parent.parent.parent / "data" / "system" / "users.json"
    users = load_json(USERS, default={"users": []})
    ulist = users.get("users", []) if isinstance(users, dict) else users
    u = next((x for x in ulist if x.get("id") == viewer_id), None)
    return bool(u and int(u.get("gradatie", 7) or 7) <= 2)


class TriggerRequest(BaseModel):
    viewer_id: str
    also_community: bool = False
    also_token_holders: bool = True


@router.post("/run")
async def run_endpoint(req: TriggerRequest):
    """Forceer weekly report nu (admin-only). Test-trigger."""
    if not _is_admin(req.viewer_id):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2)")
    return send_weekly_report(
        also_community=req.also_community,
        also_token_holders=req.also_token_holders,
    )


@router.get("/preview")
async def preview_endpoint():
    """Genereer rapport zonder te versturen — voor UI-preview."""
    report = build_weekly_report()
    return {"report": report, "text": format_report_text(report)}


@router.get("/history")
async def history_endpoint(limit: int = 20):
    """Laatste N rapporten."""
    archive = load_json(REPORTS_FILE, default={"reports": []})
    return {"reports": archive.get("reports", [])[-limit:][::-1], "total": len(archive.get("reports", []))}
