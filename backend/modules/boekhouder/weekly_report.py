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
ACC_FILE = DATA / "accounting" / "transactions.json"
ROAR_FILE = DATA / "roar" / "roar_balances.json"
REPORTS_FILE = DATA / "boekhouder" / "weekly_reports.json"
GROWTH_STATE = DATA / "trade" / "growth_state.json"

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

    # Trade results (income/expense Crypto Profit deze week)
    acc = load_json(ACC_FILE, default={"transactions": []})
    week_acc = _filter_tx_since(acc.get("transactions", []), since)
    crypto_pnl_in = sum(t.get("amount", 0) for t in week_acc
                       if t.get("category") == "Crypto Profit" and t.get("type") == "income")
    crypto_pnl_out = sum(t.get("amount", 0) for t in week_acc
                        if t.get("category") == "Crypto Profit" and t.get("type") == "expense")
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

    lines.append("")
    lines.append(f"🌊 **Overflow pool**: €{ov['now']:.2f}")

    if r['tokens_bought'] > 0 or r['tokens_sold_back'] > 0:
        lines.append("")
        lines.append(f"🪙 **ROAR**: +{r['tokens_bought']} gekocht (€{r['eur_in']:.2f}) · -{r['tokens_sold_back']} verkocht (€{r['eur_out']:.2f})")

    lines.append("")
    lines.append(f"📈 _{report['projection']}_")

    return "\n".join(lines)


def send_weekly_report(also_community: bool = False) -> Dict:
    """Bouw + verstuur + archiveer rapport. Return dict met outcome."""
    from modules.boekhouder.service import _send_dm, _post_community
    report = build_weekly_report()
    text = format_report_text(report)

    # 1. PM naar admin
    try:
        _send_dm(text, kind="boekhouder_weekly_report",
                 extra={"report": report}, recipient_id=ADMIN_USER)
    except Exception as e:
        print(f"[weekly-report] PM failed: {e}")

    # 2. Optioneel community-post (kortere versie)
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

    # 3. Archiveer
    archive = load_json(REPORTS_FILE, default={"reports": []})
    archive["reports"].append(report)
    if len(archive["reports"]) > 200:  # max ~4 jaar
        archive["reports"] = archive["reports"][-200:]
    save_json(REPORTS_FILE, archive)

    return {"success": True, "report": report, "text": text}


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


@router.post("/run")
async def run_endpoint(req: TriggerRequest):
    """Forceer weekly report nu (admin-only). Test-trigger."""
    if not _is_admin(req.viewer_id):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2)")
    return send_weekly_report(also_community=req.also_community)


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
