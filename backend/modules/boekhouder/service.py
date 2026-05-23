"""
v4_boekhouder_001 — De Boekhouder.

Acteur-persona die trade-events publiceert in:
- Privé DM naar admin (gradatie 1): gedetailleerd met cijfers
- Community trade-feed: cryptisch/leuk zonder interne cijfers

Beheert óók de centrale audit_log voor elke geld-beweging.
"""
import uuid
import random
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict

from modules.core.storage import load_json, save_json

DATA = Path(__file__).parent.parent.parent / "data"
PRIVE_DIR = DATA / "chat" / "prive"
TRADE_FEED = DATA / "chat" / "community" / "trade-feed.json"
AUDIT_LOG = DATA / "system" / "audit_log.json"
BOEKHOUDER_ID = "bot-boekhouder"
SPARK_ID = "user-000"
ADMIN_ID = "user-001"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _send_dm(text: str, kind: str = "boekhouder_trade", extra: Optional[Dict] = None, recipient_id: Optional[str] = None):
    """Privé DM van Boekhouder → ontvanger.

    v5_per_user_trade_dm_001: standaard naar admin (Willem) voor Spark-trades; bij user-trades
    krijgt de user zélf de DM ipv Willem (privacy + ownership).
    """
    target = recipient_id or ADMIN_ID
    PRIVE_DIR.mkdir(parents=True, exist_ok=True)
    fname = PRIVE_DIR / f"{BOEKHOUDER_ID}__{target}.json"
    data = load_json(fname, default={"messages": []})
    msg = {
        "id": f"bh-{uuid.uuid4().hex[:8]}",
        "from_user_id": BOEKHOUDER_ID,
        "from_naam": "De Boekhouder 🎩",
        "to_user_id": target,
        "text": text,
        "ts": _now(),
        "unread_by": [target],
        "system": True,
        "kind": kind,
    }
    if extra:
        msg.update(extra)
    data.setdefault("messages", []).append(msg)
    save_json(fname, data)


def _post_community(text: str, kind: str = "boekhouder_feed", extra: Optional[Dict] = None):
    """Publieke post in trade-feed (community kanaal)."""
    TRADE_FEED.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(TRADE_FEED, default={"messages": []})
    msg = {
        "id": f"tf-{uuid.uuid4().hex[:8]}",
        "from_user_id": BOEKHOUDER_ID,
        "from_naam": "De Boekhouder 🎩",
        "text": text,
        "ts": _now(),
        "kind": kind,
        "channel": "trade-feed",
    }
    if extra:
        msg.update(extra)
    data.setdefault("messages", []).append(msg)
    # Keep last 200 messages
    if len(data["messages"]) > 200:
        data["messages"] = data["messages"][-200:]
    save_json(TRADE_FEED, data)


def _audit(entry: Dict):
    """Append-only audit-trail voor elke geld/token-beweging."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(AUDIT_LOG, default={"entries": []})
    entry = {"ts": _now(), "id": uuid.uuid4().hex[:12], **entry}
    data.setdefault("entries", []).append(entry)
    save_json(AUDIT_LOG, data)


# ============================================================
# Trade events — door potjes-service / monitor aangeroepen
# ============================================================
def announce_buy(user_id: str, pot_id: str, market: str, price: float, amount_eur: float):
    """Spark heeft gekocht. Korte droge melding."""
    coin = market.split("-")[0]
    # v5_per_user_trade_dm_001: Spark-trades → Willem (admin), user-trades → user zelf
    recipient = ADMIN_ID if user_id == SPARK_ID else user_id
    _send_dm(
        text=f"📥 BUY • {coin} @ €{price:.4f}\nPotje: {pot_id}\nInleg: €{amount_eur:.2f}\nEigenaar: {'Spark' if user_id == SPARK_ID else user_id}",
        kind="boekhouder_buy",
        extra={"market": market, "pot_id": pot_id, "price": price, "user_id": user_id},
        recipient_id=recipient,
    )
    # Naar community: alleen voor Spark-trades
    if user_id == SPARK_ID:
        teasers = [
            f"Zo, weer een goede deal gemaakt op {coin}. Tijd om te wachten.",
            f"Spark heeft net {coin} ingekocht. Niets om je zorgen over te maken.",
            f"De {coin}-koers stond te aanlokkelijk laag. Ingenomen.",
            f"Een nieuwe positie op {coin}. We zien wat het brengt.",
        ]
        _post_community(random.choice(teasers), kind="boekhouder_buy")
    _audit({
        "type": "trade_buy", "user_id": user_id, "pot_id": pot_id,
        "market": market, "price": price, "amount_eur": amount_eur,
    })
    # v4_dnd_001 — De Boekhouder groeit met elke trade
    try:
        from modules.behavior_tracker import track
        track(user_id, "trade_event", 1)
        track(user_id, "wallet_mutate", 1)
    except Exception:
        pass


def announce_sell(user_id: str, pot_id: str, market: str, price: float,
                  netto: float, spark_fee: float = 0.0):
    """Spark heeft verkocht. Winst-melding."""
    coin = market.split("-")[0]
    winst_emoji = "✅" if netto > 0 else "⚠️"
    naam = "Spark" if user_id == SPARK_ID else user_id

    # v5_per_user_trade_dm_001: Spark-trades → Willem (admin), user-trades → user zelf
    recipient = ADMIN_ID if user_id == SPARK_ID else user_id
    _send_dm(
        text=(
            f"📤 SELL • {coin} @ €{price:.4f} {winst_emoji}\n"
            f"Potje: {pot_id}\n"
            f"Eigenaar: {naam}\n"
            f"Netto winst: €{netto:+.4f}\n"
            + (f"Spark-fee (5%): €{spark_fee:.4f}\n" if spark_fee > 0 else "")
        ),
        kind="boekhouder_sell",
        extra={"market": market, "pot_id": pot_id, "price": price,
               "netto": netto, "spark_fee": spark_fee, "user_id": user_id},
        recipient_id=recipient,
    )

    # Naar community: alleen Spark-trades, en zonder bedragen
    if user_id == SPARK_ID:
        if netto > 0:
            options = [
                f"Hahaha, winst! Uhh sorry. {coin}-deal verkocht.",
                f"Deal verkocht. {coin} bracht weer iets op.",
                f"De Boekhouder lacht zachtjes. {coin}-positie netjes afgesloten.",
                f"Tikkie binnen. {coin} is verkocht. Spark slaapt deze nacht beter.",
            ]
        else:
            options = [
                f"Tja, {coin}-positie gesloten. We tellen onze zegeningen.",
                f"{coin} verkocht. Niet elke dag is feest.",
            ]
        _post_community(random.choice(options), kind="boekhouder_sell")

    # Audit
    _audit({
        "type": "trade_sell", "user_id": user_id, "pot_id": pot_id,
        "market": market, "price": price, "netto": netto, "spark_fee_eur": spark_fee,
    })
    if spark_fee > 0:
        _audit({
            "type": "fee_transfer", "from_user": user_id, "to_user": SPARK_ID,
            "amount_eur": spark_fee, "reason": f"5% fee op SELL {pot_id}",
        })
    # v4_dnd_001 — De Boekhouder + fee-extraction tracking
    try:
        from modules.behavior_tracker import track
        track(user_id, "trade_event", 1)
        track(user_id, "wallet_mutate", 1)
        if spark_fee > 0:
            track(SPARK_ID, "fee_extraction", 1)
    except Exception:
        pass



# ============================================================
# v5_closing_flow_001 — "Terlens-terug-boek": rollup van een trade-cyclus
# ============================================================
CLOSING_LOG = DATA / "system" / "boekhouder_closings.json"


def _audit_entries_since(user_id: str, since_ts: Optional[str]) -> Dict:
    """Lees audit_log en filter op user_id sinds since_ts (ISO of None = alles)."""
    data = load_json(AUDIT_LOG, default={"entries": []})
    out = {"buys": [], "sells": [], "fees": [], "mints": []}
    for e in data.get("entries", []):
        ts = e.get("ts") or ""
        if since_ts and ts <= since_ts:
            continue
        etype = e.get("type")
        if etype == "trade_buy" and e.get("user_id") == user_id:
            out["buys"].append(e)
        elif etype == "trade_sell" and e.get("user_id") == user_id:
            out["sells"].append(e)
        elif etype == "fee_transfer" and e.get("from_user") == user_id:
            out["fees"].append(e)
        elif etype == "mint" and e.get("user_id") == user_id:
            out["mints"].append(e)
    return out


def _last_closing_ts(user_id: str) -> Optional[str]:
    data = load_json(CLOSING_LOG, default={"closings": []})
    user_closings = [c for c in data.get("closings", []) if c.get("user_id") == user_id]
    if not user_closings:
        return None
    return max(c.get("closed_at", "") for c in user_closings)


def close_cycle(user_id: str, note: str = "") -> Dict:
    """Sluit boekhouder-cyclus voor user_id af. Idempotent per-since-window:
    rollupt alle audit-events sinds laatste closing en stuurt 1 DM + audit-record.

    Returns rollup dict met saldo/winst/fees/mints.
    """
    since = _last_closing_ts(user_id)
    bucket = _audit_entries_since(user_id, since)

    total_buy_eur = sum(b.get("amount_eur", 0) for b in bucket["buys"])
    total_sell_netto = sum(s.get("netto", 0) for s in bucket["sells"])
    total_fees_eur = sum(f.get("amount_eur", 0) for f in bucket["fees"])
    total_mints = sum(m.get("amount", 0) for m in bucket["mints"])
    n_buys = len(bucket["buys"])
    n_sells = len(bucket["sells"])

    naam = "Spark" if user_id == SPARK_ID else user_id
    rollup = {
        "user_id": user_id,
        "naam": naam,
        "since": since or "begin der tijd",
        "closed_at": _now(),
        "n_buys": n_buys,
        "n_sells": n_sells,
        "total_buy_eur": round(total_buy_eur, 4),
        "total_sell_netto_eur": round(total_sell_netto, 4),
        "total_fees_eur": round(total_fees_eur, 4),
        "total_mints_tokens": total_mints,
        "note": note,
    }

    # DM naar eigenaar/admin
    recipient = ADMIN_ID if user_id == SPARK_ID else user_id
    body_lines = [
        f"📒 **Terlens-terug-boek** — {naam}",
        f"Periode sinds: {since or 'begin'}",
        f"• Koop-volume:  €{total_buy_eur:.2f}  ({n_buys} buys)",
        f"• Verkoop netto: €{total_sell_netto:+.4f}  ({n_sells} sells)",
        f"• Fees afgedragen: €{total_fees_eur:.4f}",
        f"• Token-mints: {total_mints}",
    ]
    if note:
        body_lines.append(f"_Noot: {note}_")
    body_lines.append("Boekhouding voor deze cyclus is afgesloten en gearchiveerd.")
    _send_dm(
        text="\n".join(body_lines),
        kind="boekhouder_closing",
        extra={"rollup": rollup},
        recipient_id=recipient,
    )

    # Persist closing
    CLOSING_LOG.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(CLOSING_LOG, default={"closings": []})
    data.setdefault("closings", []).append(rollup)
    save_json(CLOSING_LOG, data)

    # Audit
    _audit({
        "type": "cycle_close",
        "user_id": user_id,
        "rollup": rollup,
    })

    return rollup


def list_closings(user_id: Optional[str] = None, limit: int = 20) -> Dict:
    data = load_json(CLOSING_LOG, default={"closings": []})
    items = data.get("closings", [])
    if user_id:
        items = [c for c in items if c.get("user_id") == user_id]
    items = sorted(items, key=lambda c: c.get("closed_at", ""), reverse=True)[:limit]
    return {"closings": items, "total": len(items)}
