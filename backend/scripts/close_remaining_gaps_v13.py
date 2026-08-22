"""
v13_close_remaining_gaps_001 — sluit de laatste 3 gaps automatisch:

1. Baseline zetten voor users zonder baseline: gebruik CURRENT Bitvavo balance
   als "vanaf nu" baseline. Dat betekent: live_pnl start op €0 en groeit vanaf
   dit moment. Netjes en eerlijk startpunt.

2. Onafgesloten BUYs (BUYs zonder matching SELL én zonder open pot) → sluit
   accounting met synthetische break-even SELL @ BUY-prijs. Effect: fee blijft
   (klein kost), verder geen P&L. Coins "verdwijnen" uit stats-view, wat correct
   is want ze zijn er niet meer (of ze zitten in shared Bitvavo treasury).

Run: python3 /app/backend/scripts/close_remaining_gaps_v13.py [--apply]
"""
import json
import sys
from datetime import datetime, timezone
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
        return None, None
    d = json.load(open(fp))
    return d, fp


def get_bitvavo_balance(uid):
    """Haal huidige Bitvavo total EUR op voor deze user (via monitor module).
    Return None bij falen zodat we baseline niet vervuild kunnen zetten."""
    try:
        sys.path.insert(0, str(ROOT))
        from modules.trade.monitor import fetch_bitvavo_balance
        bv = fetch_bitvavo_balance(uid)
        if bv.get("success"):
            return float(bv.get("total_eur") or 0)
    except Exception as e:
        print(f"  [warn] Bitvavo lookup faalde voor {uid}: {e}")
    return None


def fix(dry_run: bool = True):
    potjes = json.load(open(POTJES_FP))
    baselines = json.load(open(BASELINE_FP)) if BASELINE_FP.exists() else {}
    now = datetime.now(timezone.utc).isoformat()
    actions = []

    users_with_potjes = [uid for uid, u in potjes.get("users", {}).items() if u.get("potjes")]

    # === 1. Baselines zetten voor users zonder baseline ===
    for uid in users_with_potjes:
        bl = baselines.get(uid)
        cur_bl = None
        if isinstance(bl, (int, float)):
            cur_bl = float(bl)
        elif isinstance(bl, dict):
            cur_bl = bl.get("baseline_eur")

        if cur_bl and cur_bl > 0:
            continue  # al gezet

        bv_total = get_bitvavo_balance(uid)
        if bv_total is None:
            actions.append({
                "type": "baseline_skip", "user_id": uid,
                "reason": "kon Bitvavo balance niet ophalen",
            })
            continue
        # v13_baseline_before_first_trade_001 — set_at moet VÓÓR de oudste trade
        # liggen zodat historische trades allemaal meetellen in stats. Anders
        # filtert `get_trade_stats` de trades WEG (baseline_since > trade_ts).
        hist_for_bl, _ = load_hist(uid)
        trades_for_bl = hist_for_bl if isinstance(hist_for_bl, list) else (hist_for_bl or {}).get("trades", [])
        oldest_ts = None
        for t in (trades_for_bl or []):
            ts = t.get("timestamp")
            if ts and (oldest_ts is None or ts < oldest_ts):
                oldest_ts = ts
        # 1 seconde vóór oudste trade, of "1970" als geen trades
        if oldest_ts:
            try:
                from datetime import timedelta as _td2
                _o = datetime.fromisoformat(oldest_ts.replace("Z", "+00:00"))
                set_at = (_o - _td2(seconds=1)).isoformat()
            except Exception:
                set_at = "1970-01-01T00:00:00+00:00"
        else:
            set_at = "1970-01-01T00:00:00+00:00"
        # Shared Bitvavo (proxied) — voor non-Spark users is total_eur
        # het gedeelde saldo (~€123). Baseline moet dat dan zijn zodat live_pnl
        # start op 0. Correcte "fresh start" semantiek voor multi-user proxied trading.
        baselines[uid] = {
            "baseline_eur": round(bv_total, 2),
            "set_at": set_at,
            "note": "auto-set via close_remaining_gaps_v13 (fresh start = huidige Bitvavo total, historische trades tellen mee)",
        }
        actions.append({
            "type": "baseline_set", "user_id": uid,
            "baseline_eur": round(bv_total, 2),
            "set_at": set_at,
        })

    # === 2. Onafgesloten BUYs → synthetische break-even SELL ===
    for uid in users_with_potjes:
        hist, fp = load_hist(uid)
        if hist is None:
            continue
        trades = hist if isinstance(hist, list) else hist.get("trades", [])

        # Tel BUYs vs SELLs per market
        per_market_buys = defaultdict(list)
        per_market_sells = defaultdict(list)
        for t in trades:
            act = (t.get("action") or "").upper()
            m = t.get("market") or ""
            if not t.get("success"):
                continue
            if act == "BUY":
                per_market_buys[m].append(t)
            elif act == "SELL":
                per_market_sells[m].append(t)

        user_pots = potjes["users"][uid].get("potjes", [])

        for market, buys in per_market_buys.items():
            sells = per_market_sells.get(market, [])
            gap = len(buys) - len(sells)
            if gap <= 0:
                continue
            # Skip als er nog een open pot is voor deze market (die BUYs zijn "in gebruik")
            n_open_pots = sum(1 for p in user_pots
                              if p.get("market") == market
                              and (p.get("position") or {}).get("is_open"))
            gap_to_close = gap - n_open_pots
            if gap_to_close <= 0:
                continue

            # Sluit de OUDSTE (zonder-SELL) BUYs eerst: neem laatste gap_to_close BUYs
            unclosed_buys = buys[-gap_to_close:] if gap_to_close < len(buys) else buys
            for buy in unclosed_buys:
                buy_price = float(buy.get("price") or 0)
                filled = float(buy.get("filled") or 0)
                if buy_price <= 0 or filled <= 0:
                    continue
                # v13_gap_close_hist_ts_001 — synthetic SELL krijgt BUY-timestamp
                # (+ 1 minuut) zodat baseline-filter niet BUY én SELL uit elkaar
                # trekt. Zonder deze fix: baseline gezet op NU → oude BUY valt buiten
                # window, nieuwe SELL binnen → fake winst in stats.
                buy_ts = buy.get("timestamp") or now
                try:
                    from datetime import timedelta as _td
                    _buy_dt = datetime.fromisoformat(buy_ts.replace("Z", "+00:00"))
                    sell_ts = (_buy_dt + _td(minutes=1)).isoformat()
                except Exception:
                    sell_ts = buy_ts
                # Break-even synthetic SELL @ same price
                sell_fee = round(filled * buy_price * BITVAVO_FEE_RATE, 4)
                new_sell = {
                    "trade_id": f"gap-close-{uid}-{market}-{int(datetime.now(timezone.utc).timestamp())}-{len(actions)}",
                    "run_id": "close_remaining_gaps_v13",
                    "timestamp": sell_ts,
                    "action": "SELL",
                    "market": market,
                    "amount": filled,
                    "price": buy_price,  # break-even
                    "filled": filled,
                    "status": "filled",
                    "mock": False,
                    "success": True,
                    "synthetic": True,
                    "source": "gap_close_v13",
                    "note": f"break-even close voor onafgesloten BUY {buy.get('trade_id','?')}",
                    "fee": sell_fee,
                    "fee_currency": "EUR",
                    "requested_amount": round(filled * buy_price, 4),
                    "effective_amount": filled,
                    "proxied_via_spark": buy.get("proxied_via_spark", False),
                }
                trades.append(new_sell)
                actions.append({
                    "type": "gap_sell_added", "user_id": uid,
                    "market": market, "eur_value": round(filled * buy_price, 4),
                    "for_buy_id": buy.get("trade_id"),
                    "sell_ts": sell_ts,
                })

        if not dry_run:
            # Persist naar disk
            bak = fp.parent / f"{fp.stem}.bak_gapclose_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            with open(bak, "w") as f:
                json.dump(json.load(open(fp)), f, indent=2)
            with open(fp, "w") as f:
                json.dump(hist, f, indent=2)

    # === Persist baselines ===
    if not dry_run:
        BASELINE_FP.parent.mkdir(parents=True, exist_ok=True)
        with open(BASELINE_FP, "w") as f:
            json.dump(baselines, f, indent=2)

    return {"dry_run": dry_run, "n_actions": len(actions), "actions": actions}


if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    r = fix(dry_run=dry)
    print(json.dumps(r, indent=2))
    if dry:
        print("\nDRY RUN — voeg --apply toe.")
