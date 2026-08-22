"""
v13_fix_max_size_zero_001 — herstel max_size op alle potjes.

Bug: alle 13 potjes hebben `max_size=0`. Bij winstgevende SELL wordt in
close_pot() de nieuwe capital gecapped op max_size → alle winst boven €0
verdwijnt naar overflow_pool ipv in het potje te groeien.

Fix-regels:
- Als `original_max_size` bestaat → gebruik die (dat is de intent)
- Anders: als capital ≤ 15 → max_size = 50 (INITIAL_MAX = 5× starter)
- Anders: max_size = capital × 5 (evenredige groei-headroom)

Run: python3 /app/backend/scripts/fix_max_size_zero_v13.py [--apply]
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
POTJES_FP = ROOT / "data" / "financial" / "user_potjes.json"

INITIAL_MAX = 50.0


def fix(dry_run: bool = True):
    data = json.load(open(POTJES_FP))
    changes = []
    for uid, u in data.get("users", {}).items():
        for pot in u.get("potjes", []):
            cur_max = float(pot.get("max_size") or 0)
            if cur_max > 0:
                continue
            cap = float(pot.get("capital") or 0)
            orig = pot.get("original_max_size")
            if orig and float(orig) > 0:
                new_max = float(orig)
                reason = "restored from original_max_size"
            elif cap <= 15.0:
                new_max = INITIAL_MAX
                reason = f"starter default (cap €{cap:.2f})"
            else:
                new_max = round(cap * 5.0, 2)
                reason = f"5× current capital (grown pot)"
            pot["max_size"] = new_max
            if "original_max_size" not in pot:
                pot["original_max_size"] = new_max
            changes.append({
                "user_id": uid, "pot_id": pot["id"], "market": pot.get("market"),
                "capital": cap, "old_max": cur_max, "new_max": new_max, "reason": reason,
            })

    if not dry_run and changes:
        bak = POTJES_FP.parent / f"user_potjes.json.bak_maxsize_fix_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        with open(bak, "w") as f:
            json.dump(json.load(open(POTJES_FP)), f, indent=2)
        with open(POTJES_FP, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Backup: {bak}")

    return {"dry_run": dry_run, "n_changes": len(changes), "changes": changes}


if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    r = fix(dry_run=dry)
    print(json.dumps(r, indent=2))
    if dry:
        print("\nDRY RUN — voeg --apply toe.")
