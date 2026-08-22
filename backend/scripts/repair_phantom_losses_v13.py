"""
v13_repair_phantom_losses_001 — herstel fantoom-verliezen van reconcile_close_sold.

Achtergrond: reconcile-endpoint gebruikte de HUIDIGE marktprijs als exit_price bij
het sluiten van open pots waarvan coin al weg was op Bitvavo. Als de coin sinds
de daadwerkelijke SELL was gedaald, werden er fake verliezen geboekt.

Deze repair:
- Loop reconcile_audit entries per pot.
- Voor entries met netto < 0: zoek in wallet/trade_history/{user}.json de meest
  recente SELL voor deze market (binnen 7d rond audit ts). Vindbaar → recompute
  met echte SELL-prijs. Niet vindbaar → break-even (netto=0).
- Rollback stats.losses/trades/total_pnl + capital dienovereenkomstig.
- Markeer audit-entry met `repaired_at` en nieuwe waarden (bewaart historie).

Uitvoerbaar als: python3 /app/backend/scripts/repair_phantom_losses_v13.py [--dry-run]
"""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
POTJES_FP = ROOT / "data" / "financial" / "user_potjes.json"
HIST_DIR = ROOT / "data" / "wallet" / "trade_history"

BITVAVO_FEE = 0.0025


def _load_history(user_id: str):
    fp = HIST_DIR / f"{user_id}.json"
    if not fp.exists():
        return []
    d = json.load(open(fp))
    return d if isinstance(d, list) else d.get("trades", [])


def _find_real_sell(user_id: str, market: str, audit_ts: str):
    """Zoek recente SELL voor deze market binnen 7 dagen vóór audit_ts."""
    trades = _load_history(user_id)
    try:
        audit_dt = datetime.fromisoformat(audit_ts.replace("Z", "+00:00"))
    except Exception:
        return None
    candidates = []
    for t in trades:
        if (t.get("action") or "").upper() != "SELL":
            continue
        if t.get("market") != market:
            continue
        try:
            t_dt = datetime.fromisoformat((t.get("timestamp") or "").replace("Z", "+00:00"))
        except Exception:
            continue
        if t_dt > audit_dt:
            continue  # SELL na de audit kan niet de bron zijn
        if (audit_dt - t_dt) > timedelta(days=7):
            continue
        candidates.append((t_dt, t))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def repair(dry_run: bool = False):
    data = json.load(open(POTJES_FP))
    now_iso = datetime.now(timezone.utc).isoformat()
    changes = []

    for uid, u in data.get("users", {}).items():
        for pot in u.get("potjes", []):
            audit = pot.get("reconcile_audit") or []
            for a in audit:
                if a.get("type") != "reconcile_close_sold":
                    continue
                if a.get("repaired_at"):
                    continue  # al gerepareerd
                old_netto = float(a.get("netto", 0) or 0)
                if old_netto >= 0:
                    continue  # alleen fake verliezen fixen
                entry = float(a.get("entry", 0) or 0)
                capital_before = float(a.get("capital_before", 0) or 0)
                if entry <= 0 or capital_before <= 0:
                    continue

                real_sell = _find_real_sell(uid, pot.get("market", ""), a.get("ts", ""))
                if real_sell:
                    real_exit = float(real_sell.get("price") or 0)
                    if real_exit > 0:
                        profit_pct = (real_exit - entry) / entry
                        bruto = capital_before * profit_pct
                        fees = capital_before * BITVAVO_FEE * 2
                        new_netto = round(bruto - fees, 4)
                        reason = f"echte SELL @ €{real_exit:.4f} uit trade_history"
                    else:
                        new_netto = 0.0
                        reason = "echte SELL zonder prijs → break-even"
                else:
                    new_netto = 0.0
                    reason = "geen SELL in trade_history → break-even"

                delta_netto = new_netto - old_netto  # positief = we voegen winst toe / verlies weg
                new_capital = round(capital_before + new_netto, 4)

                # Pas pot state aan
                stats = pot.setdefault("stats", {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0})
                # Rollback oude klassifiek
                if old_netto > 0:
                    stats["wins"] = max(0, int(stats.get("wins", 0)) - 1)
                elif old_netto < 0:
                    stats["losses"] = max(0, int(stats.get("losses", 0)) - 1)
                # Nieuwe klassifiek
                if new_netto > 0:
                    stats["wins"] = int(stats.get("wins", 0)) + 1
                elif new_netto < 0:
                    stats["losses"] = int(stats.get("losses", 0)) + 1
                # total_pnl compenseren
                stats["total_pnl"] = round(float(stats.get("total_pnl", 0)) - old_netto + new_netto, 4)
                # trades teller blijft (de close is gebeurd, alleen exit_price fout)

                # Capital aanpassen: rollback oude netto, add new netto
                pot["capital"] = round(float(pot.get("capital", 0) or 0) - old_netto + new_netto, 4)

                # Audit-entry uitbreiden
                a["repaired_at"] = now_iso
                a["repair_reason"] = reason
                a["old_netto"] = old_netto
                a["new_netto"] = new_netto
                a["old_exit_price"] = a.get("exit_price")
                a["new_exit_price"] = float(real_sell.get("price")) if real_sell else entry
                a["capital_after_repair"] = new_capital

                changes.append({
                    "user_id": uid,
                    "pot_id": pot["id"],
                    "market": pot.get("market"),
                    "old_netto": old_netto,
                    "new_netto": new_netto,
                    "delta_capital": round(delta_netto, 4),
                    "reason": reason,
                })

    if not dry_run and changes:
        # backup vóór save
        bak_fp = POTJES_FP.parent / f"user_potjes.json.bak_phantom_loss_repair_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        with open(bak_fp, "w") as f:
            json.dump(json.load(open(POTJES_FP)), f, indent=2)
        with open(POTJES_FP, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Backup gemaakt: {bak_fp}")

    return {
        "dry_run": dry_run,
        "n_changes": len(changes),
        "changes": changes,
    }


if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    result = repair(dry_run=dry)
    print(json.dumps(result, indent=2))
    if dry:
        print("\nDRY RUN — voeg --apply toe om echt te schrijven.")
