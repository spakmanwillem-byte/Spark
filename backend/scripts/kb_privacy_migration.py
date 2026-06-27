"""v6_kb_privacy_migration_001 — Markeer persoonlijke relatie-kaarten als privé.

Eénmalig script. Idempotent (kun je opnieuw draaien).
Wat het doet:
  - Selecteert kaarten die expliciet persoonlijke claims bevatten ("X is mijn Y", "mijn X belde")
  - Skipt algemene woordenboek-termen ("Dochter is een vrouwelijk kind", "Vader is een mannelijke ouder")
  - Zet bron_user_id="user-001" + privacy="private" op de kandidaten

Achtergrond: tot 2026-06-27 werden relatie-uitspraken van Willem (admin/user-001)
opgeslagen in de publieke KB zonder eigenaarschap. Daardoor zag user 'Jantje' info
over "Maaike Spakman" en "Lotus Martens". Privacy-lek dichten.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

KB_DIR = Path("/app/backend/data/knowledge/v2")
OWNER = "user-001"

# Expliciete privé-kandidaten (whitelist op id om geen ongelukken te maken)
PRIVATE_CARD_IDS = [
    "kbv2-85ffc65f",  # Lotus komt elke woensdag
    "kbv2-52a80f85",  # Mijn moeder belde
    "kbv2-9b7572d0",  # Mijn vader is inmiddels overleden.
    "kbv2-00552819",  # Heidi Spakman is mijn Moeder
    "kbv2-326fe037",  # Willie Bakker was mijn vader. Hij is overleden.
    "kbv2-dd24f036",  # Maaike Spakman is mijn Zusje
    "kbv2-28f77d08",  # Lotus Martens is mijn Dochter
    "kbv2-5855e9cc",  # Willie Bakker is mijn Vader
]


def run(dry_run: bool = False) -> dict:
    """Migreer. Returnt rapport-dict."""
    ts = datetime.now(timezone.utc).isoformat()
    changed_ids = []
    skipped_already_private = []
    not_found = list(PRIVATE_CARD_IDS)

    for fp in sorted(KB_DIR.glob("knowledge_v2_*.json")):
        if "backup" in fp.name:
            continue
        d = json.loads(fp.read_text(encoding="utf-8"))
        modified = False
        for k in d.get("kaarten", []):
            if k.get("id") in PRIVATE_CARD_IDS:
                not_found = [x for x in not_found if x != k["id"]]
                if k.get("privacy") == "private" and k.get("bron_user_id") == OWNER:
                    skipped_already_private.append(k["id"])
                    continue
                k["bron_user_id"] = OWNER
                k["privacy"] = "private"
                k.setdefault("privacy_migrated_at", ts)
                changed_ids.append(k["id"])
                modified = True
        if modified and not dry_run:
            fp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "dry_run": dry_run,
        "owner": OWNER,
        "changed": changed_ids,
        "already_private": skipped_already_private,
        "not_found_in_kb": not_found,
        "timestamp": ts,
    }


if __name__ == "__main__":
    import sys
    dry = "--apply" not in sys.argv
    rep = run(dry_run=dry)
    mode = "DRY-RUN" if dry else "APPLIED"
    print(f"[{mode}] changed={len(rep['changed'])} | already_private={len(rep['already_private'])} | not_found={len(rep['not_found_in_kb'])}")
    for cid in rep["changed"]:
        print(f"  ✓ {cid}")
    if rep["not_found_in_kb"]:
        print("  ⚠ Not found:", rep["not_found_in_kb"])
