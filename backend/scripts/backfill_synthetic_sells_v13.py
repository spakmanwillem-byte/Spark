"""
v13_backfill_synthetic_sells_001 — voor bestaande reconcile_close_sold audits die
GEEN corresponding SELL in wallet/trade_history/{user}.json hebben: voeg
synthetische SELL toe zodat /api/trade/stats klopt.

Dit fixt de gap "2 BUYs / 0 SELLs" die Gijs's stats -€20 lieten zien terwijl
de pots via reconcile break-even werden gesloten.

Match-regel: audit_ts binnen 1 dag van eventual synthetic SELL.
Dubbele write voorkomen: sla over als er al een SELL is met `source=reconcile_close_sold`
voor dezelfde pot_id (via trade_id prefix).

Run: python3 /app/backend/scripts/backfill_synthetic_sells_v13.py [--apply]
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
POTJES_FP = ROOT / "data" / "financial" / "user_potjes.json"
HIST_DIR = ROOT / "data" / "wallet" / "trade_history"


def _load_hist(user_id: str):
    fp = HIST_DIR / f"{user_id}.json"
    if not fp.exists():
        return None, None
    d = json.load(open(fp))
    return d, fp


def backfill(dry_run: bool = True):
    data = json.load(open(POTJES_FP))
    added = []
    per_user_added = {}

    for uid, u in data.get("users", {}).items():
        hist, fp = _load_hist(uid)
        if hist is None:
            continue  # geen trade-history-file → skip (nooit iets gebought)
        trades = hist if isinstance(hist, list) else hist.get("trades", [])

        # Verzamel bestaande synthetic SELLs zodat we geen dubbels toevoegen
        existing_synth_ids = {t.get("trade_id") for t in trades
                              if t.get("source") == "reconcile_close_sold"}
        existing_pot_ids = set()
        for t in trades:
            tid = t.get("trade_id") or ""
            if tid.startswith("reconcile-"):
                parts = tid.split("-")
                if len(parts) >= 3:
                    existing_pot_ids.add(f"pot-{parts[2]}" if not parts[1].startswith("pot") else "-".join(parts[1:-1]))

        for pot in u.get("potjes", []):
            pot_id = pot["id"]
            for a in (pot.get("reconcile_audit") or []):
                if a.get("type") != "reconcile_close_sold":
                    continue
                if a.get("synthetic_sell_written"):
                    continue  # eerder al gebackfilled

                # Skip als er al een reconcile-{pot_id}-... trade bestaat
                if any((t.get("source") == "reconcile_close_sold" and
                        (t.get("trade_id") or "").startswith(f"reconcile-{pot_id}-"))
                       for t in trades):
                    a["synthetic_sell_written"] = "already_present"
                    continue

                entry = float(a.get("entry", 0) or 0)
                # v13_backfill_use_repaired_001 — als audit al gerepareerd is
                # (fantoom-loss repair), gebruik `new_exit_price` als exit i.p.v.
                # de oorspronkelijke foute exit_price. new_netto geeft ook de
                # gecorrigeerde P&L die matcht met pot.stats.total_pnl.
                if a.get("repaired_at"):
                    exit_price = float(a.get("new_exit_price") or a.get("exit_price") or 0)
                else:
                    exit_price = float(a.get("exit_price", 0) or 0)
                capital_before = float(a.get("capital_before", 0) or 0)
                if entry <= 0 or exit_price <= 0 or capital_before <= 0:
                    continue

                expected_coin = capital_before / entry
                ts = a.get("ts") or datetime.now(timezone.utc).isoformat()
                try:
                    ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    ts_dt = datetime.now(timezone.utc)

                new_trade = {
                    "trade_id": f"reconcile-{pot_id}-{int(ts_dt.timestamp())}",
                    "run_id": "reconcile_backfill_v13",
                    "timestamp": ts,
                    "action": "SELL",
                    "market": pot.get("market") or "?-EUR",
                    "amount": round(expected_coin, 8),
                    "price": exit_price,
                    "filled": round(expected_coin, 8),
                    "status": "filled",
                    "mock": False,
                    "success": True,
                    "synthetic": True,
                    "source": "reconcile_close_sold",
                    "exit_source": a.get("exit_source", "backfill_from_audit"),
                    "fee": round(capital_before * 0.0025, 4),
                    "fee_currency": "EUR",
                    "requested_amount": capital_before,
                    "effective_amount": round(expected_coin, 8),
                    "proxied_via_spark": False,
                    "backfilled_at": datetime.now(timezone.utc).isoformat(),
                }
                trades.append(new_trade)
                a["synthetic_sell_written"] = new_trade["trade_id"]
                added.append({
                    "user_id": uid, "pot_id": pot_id,
                    "market": new_trade["market"], "exit_price": exit_price,
                    "eur_value": round(expected_coin * exit_price, 4),
                    "ts": ts,
                })
                per_user_added[uid] = per_user_added.get(uid, 0) + 1

        # Save trade_history als er iets is toegevoegd voor deze user
        if not dry_run and per_user_added.get(uid, 0) > 0:
            bak = fp.parent / f"{fp.stem}.bak_backfill_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            with open(bak, "w") as f:
                json.dump(json.load(open(fp)), f, indent=2)
            with open(fp, "w") as f:
                json.dump(hist, f, indent=2)

    # Save potjes.json (voor synthetic_sell_written markers)
    if not dry_run and added:
        bak_p = POTJES_FP.parent / f"user_potjes.json.bak_backfill_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        with open(bak_p, "w") as f:
            json.dump(json.load(open(POTJES_FP)), f, indent=2)
        with open(POTJES_FP, "w") as f:
            json.dump(data, f, indent=2)

    return {"dry_run": dry_run, "n_added": len(added), "per_user": per_user_added, "added": added}


if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    r = backfill(dry_run=dry)
    print(json.dumps(r, indent=2))
    if dry:
        print("\nDRY RUN — voeg --apply toe om te schrijven.")
