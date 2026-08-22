"""
v13_gap_scanner_001 — systematisch scan voor inconsistenties tussen:
  1. wallet/trade_history/{user}.json  (echte Bitvavo trades)
  2. financial/user_potjes.json         (pot state + stats + audit)
  3. trade/capital_baseline.json        (baseline voor live_pnl)
  4. Bitvavo API live saldo (optioneel)

Rapporteert per user:
  A. Fee-completeness:  som(fees) = som(buy_fees) + som(sell_fees) én non-nul
  B. Baseline-check:    baseline gezet en > 0 (anders live_pnl vertekend)
  C. Trade-pot mismatch: BUYs in history zonder matching pot / pot BUYs zonder matching history
  D. Audit-pot drift:   som(audit.netto) matcht met pot.stats.total_pnl?
  E. Fee-currency gap:  fees in non-EUR currencies (die worden nu genegeerd)
  F. Ghost sells:       SELLs zonder BUY erboven
  G. Ghost buys:        BUYs zonder eventual SELL (open positions OK)
"""
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
POTJES_FP = ROOT / "data" / "financial" / "user_potjes.json"
BASELINE_FP = ROOT / "data" / "trade" / "capital_baseline.json"
HIST_DIR = ROOT / "data" / "wallet" / "trade_history"

BITVAVO_FEE_RATE = 0.0025


def load_hist(uid):
    fp = HIST_DIR / f"{uid}.json"
    if not fp.exists():
        return []
    d = json.load(open(fp))
    return d if isinstance(d, list) else d.get("trades", [])


def scan():
    potjes_data = json.load(open(POTJES_FP)) if POTJES_FP.exists() else {"users": {}}
    baseline_data = json.load(open(BASELINE_FP)) if BASELINE_FP.exists() else {}

    findings = []

    for uid, u in potjes_data.get("users", {}).items():
        potjes = u.get("potjes", [])
        if not potjes:
            continue
        hist = load_hist(uid)
        user_report = {"user_id": uid, "n_potjes": len(potjes), "issues": []}

        # A. Fee completeness
        buys = [t for t in hist if (t.get("action") or "").upper() == "BUY" and t.get("success")]
        sells = [t for t in hist if (t.get("action") or "").upper() == "SELL" and t.get("success")]
        buy_fees = sum(float(t.get("fee") or 0) for t in buys if (t.get("fee_currency") or "EUR") == "EUR")
        sell_fees = sum(float(t.get("fee") or 0) for t in sells if (t.get("fee_currency") or "EUR") == "EUR")
        # Expected round-trip fees: 2× BITVAVO_FEE × sum(buy amounts)
        exp_buy_fee = sum(float(t.get("amount") or 0) for t in buys) * BITVAVO_FEE_RATE
        exp_sell_fee = sum(float(t.get("filled") or 0) * float(t.get("price") or 0) for t in sells) * BITVAVO_FEE_RATE
        if buys and buy_fees == 0:
            user_report["issues"].append({"type": "A_missing_buy_fees", "buys": len(buys), "buy_fees_eur": buy_fees})
        if sells and sell_fees == 0:
            user_report["issues"].append({"type": "A_missing_sell_fees", "sells": len(sells), "sell_fees_eur": sell_fees})
        if abs((buy_fees + sell_fees) - (exp_buy_fee + exp_sell_fee)) > 0.05 and (buys or sells):
            user_report["issues"].append({
                "type": "A_fee_amount_drift",
                "actual_fees": round(buy_fees + sell_fees, 4),
                "expected_fees": round(exp_buy_fee + exp_sell_fee, 4),
                "diff": round((buy_fees + sell_fees) - (exp_buy_fee + exp_sell_fee), 4),
            })

        # B. Baseline check
        bl_raw = baseline_data.get(uid)
        bl_eur = None
        if isinstance(bl_raw, (int, float)):
            bl_eur = float(bl_raw)
        elif isinstance(bl_raw, dict):
            bl_eur = bl_raw.get("baseline_eur")
        if bl_eur is None:
            user_report["issues"].append({"type": "B_no_baseline", "hint": "live_pnl kan niet berekend worden"})
        elif bl_eur == 0:
            user_report["issues"].append({"type": "B_baseline_zero", "hint": "live_pnl toont ALLE Bitvavo als winst — waarschijnlijk niet gezet"})

        # C. Trade-pot market mismatch
        pot_markets = defaultdict(int)
        for p in potjes:
            m = p.get("market") or ""
            if m:
                pot_markets[m] += 1
        hist_markets = defaultdict(int)
        for t in hist:
            m = t.get("market") or ""
            if m:
                hist_markets[m] += 1
        # BUYs in history voor market die niet in potjes voorkomt (orphan BUYs)
        for m, n in hist_markets.items():
            if m not in pot_markets:
                buys_in_m = sum(1 for t in buys if t.get("market") == m)
                sells_in_m = sum(1 for t in sells if t.get("market") == m)
                if buys_in_m or sells_in_m:
                    user_report["issues"].append({
                        "type": "C_orphan_market_in_history",
                        "market": m, "buys": buys_in_m, "sells": sells_in_m,
                        "hint": "trades in history maar geen pot heeft deze market",
                    })
        # BUYs zonder matching SELL (open positions of gaps)
        for m in hist_markets:
            b = sum(1 for t in buys if t.get("market") == m)
            s = sum(1 for t in sells if t.get("market") == m)
            if b > s:
                # Check of er een OPEN pot is voor deze market die dat verklaart
                open_pot_for_m = any(p.get("market") == m and (p.get("position") or {}).get("is_open") for p in potjes)
                if not open_pot_for_m:
                    user_report["issues"].append({
                        "type": "G_unclosed_buys",
                        "market": m, "buys": b, "sells": s, "gap": b - s,
                        "hint": "meer BUYs dan SELLs én geen open pot → coin ergens 'zoek' of trade ontbreekt",
                    })

        # D. Audit-pot drift: som(audit.netto na repair) == pot.stats.total_pnl?
        # We tellen alle audit.netto's op — als repaired: gebruik new_netto.
        for p in potjes:
            audits = p.get("reconcile_audit") or []
            if not audits:
                continue
            audit_pnl = 0.0
            for a in audits:
                if a.get("repaired_at"):
                    audit_pnl += float(a.get("new_netto", 0) or 0)
                else:
                    audit_pnl += float(a.get("netto", 0) or 0)
            stats_pnl = float((p.get("stats") or {}).get("total_pnl") or 0)
            if abs(audit_pnl - stats_pnl) > 0.01:
                user_report["issues"].append({
                    "type": "D_audit_vs_stats_drift",
                    "pot_id": p["id"], "market": p.get("market"),
                    "audit_pnl": round(audit_pnl, 4),
                    "stats_pnl": round(stats_pnl, 4),
                    "diff": round(audit_pnl - stats_pnl, 4),
                    "hint": "kan ook door echte trades ZONDER audit komen (dan hoort diff = echt-trade PnL)",
                })

        # E. Fee currency gap: fees in non-EUR
        non_eur_fees = [t for t in hist if (t.get("fee") or 0) > 0 and (t.get("fee_currency") or "EUR") != "EUR"]
        if non_eur_fees:
            user_report["issues"].append({
                "type": "E_non_eur_fees",
                "count": len(non_eur_fees),
                "hint": "stats endpoint negeert non-EUR fees — kunnen crypto-fees (BCH/BTC) zijn",
            })

        # F. Ghost sells (SELLs zonder BUY-context per market)
        for m, s in hist_markets.items():
            b = sum(1 for t in buys if t.get("market") == m)
            s_count = sum(1 for t in sells if t.get("market") == m)
            if s_count > b:
                user_report["issues"].append({
                    "type": "F_ghost_sells",
                    "market": m, "buys": b, "sells": s_count,
                    "hint": "meer SELLs dan BUYs — trade-history incompleet of synthetische SELLs zonder BUY",
                })

        # H. Pot capital vs Bitvavo baseline coherency (voor open pots)
        for p in potjes:
            pos = p.get("position") or {}
            if pos.get("is_open") and not pos.get("entry_price"):
                user_report["issues"].append({
                    "type": "H_open_pot_no_entry",
                    "pot_id": p["id"], "market": p.get("market"),
                    "hint": "position.is_open=True maar entry_price=None → corrupte state",
                })

        # I. Max_size = 0 (corrupted pots)
        for p in potjes:
            if float(p.get("max_size", 0) or 0) == 0:
                user_report["issues"].append({
                    "type": "I_max_size_zero",
                    "pot_id": p["id"], "market": p.get("market"),
                    "hint": "max_size=0 blokkeert groei van pot bij winst",
                })

        if user_report["issues"]:
            findings.append(user_report)

    return findings


if __name__ == "__main__":
    result = scan()
    print(f"\n{'='*60}\nGAP SCAN — {len(result)} user(s) met issues\n{'='*60}")
    if not result:
        print("Geen gaps gevonden. Alles clean. ")
    for r in result:
        print(f"\n### {r['user_id']} ({r['n_potjes']} pots) — {len(r['issues'])} issues")
        for i in r["issues"]:
            print(f"  [{i['type']}] {json.dumps({k:v for k,v in i.items() if k!='type'}, default=str)}")
