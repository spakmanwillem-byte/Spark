"""Backfill: ga door bestaande chat-logs en extract identity-facts retrospectief.

Gebruik: python3 backfill_identity_facts.py [user_id]

Lees /app/backend/data/chat/logs/{user_id}.json (conversations[]) en bel
identity_facts.extract_and_save() voor elke user_message. Idempotent —
dedupe in extract_and_save zorgt dat dezelfde fact niet 2x wordt opgeslagen.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, "/app/backend")
from modules.chat import identity_facts  # noqa: E402


def backfill(user_id: str = "user-001") -> None:
    log_fp = Path(f"/app/backend/data/chat/logs/{user_id}.json")
    if not log_fp.exists():
        print(f"No log for {user_id}")
        return
    d = json.loads(log_fp.read_text(encoding="utf-8"))
    convs = d.get("conversations", [])
    print(f"Processing {len(convs)} turns for {user_id}...")

    extracted_count = 0
    for c in convs:
        um = c.get("user_message") or ""
        if not um or len(um) < 10:
            continue
        ts = c.get("timestamp")
        session_id = c.get("session_id") or c.get("id")
        new = identity_facts.extract_and_save(user_id, um, session_id=session_id)
        if new:
            extracted_count += len(new)

    facts = identity_facts._load(user_id)
    print()
    print(f"✅ Backfill compleet voor {user_id}")
    print(f"   • Extracted: {extracted_count} new facts in this run")
    print(f"   • Total about_user: {len(facts['about_user'])}")
    print(f"   • Total about_spark: {len(facts['about_spark'])}")
    print()
    print("Top 10 about_spark (meest gezegd):")
    for f in sorted(facts['about_spark'], key=lambda x: -x.get('count', 1))[:10]:
        print(f"  • [{f['trigger']}] \"{f['value']}\" (×{f['count']})")
    print()
    print("Top 5 about_user:")
    for f in sorted(facts['about_user'], key=lambda x: -x.get('count', 1))[:5]:
        print(f"  • [{f['trigger']}] \"{f['value']}\" (×{f['count']})")


if __name__ == "__main__":
    uid = sys.argv[1] if len(sys.argv) > 1 else "user-001"
    backfill(uid)
