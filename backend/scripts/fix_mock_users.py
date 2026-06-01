"""
v6_mock_migration_001 — One-off migratie: alle bestaande users met use_mock=True flippen naar False.

Run met: python3 /app/backend/scripts/fix_mock_users.py

- Backup van bots_registry_state.json wordt gemaakt voor de wijziging
- Alleen use_mock=True wordt geflipt; rest blijft ongemoeid
- Print rapport van wie ge-flipt is
"""
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

DATA = Path("/app/backend/data/trade/bots_registry_state.json")
BACKUP = DATA.parent / f"bots_registry_state.backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"


def main():
    if not DATA.exists():
        print(f"❌ {DATA} niet gevonden")
        return

    # Backup
    shutil.copy(DATA, BACKUP)
    print(f"📦 Backup → {BACKUP.name}")

    with open(DATA) as f:
        d = json.load(f)

    bots = d.get("bots", [])
    flipped = []
    already_ok = []

    for b in bots:
        uid = b.get("user_id")
        if b.get("use_mock") is True:
            b["use_mock"] = False
            flipped.append(uid)
        else:
            already_ok.append(uid)

    with open(DATA, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

    print(f"\n🟢 Geflipt ({len(flipped)} users):")
    for u in flipped:
        print(f"   • {u} (use_mock True → False)")
    print(f"\n✅ Al goed ({len(already_ok)} users):")
    for u in already_ok:
        print(f"   • {u}")
    print(f"\nKlaar. Restart backend voor effect: sudo supervisorctl restart backend")


if __name__ == "__main__":
    main()
