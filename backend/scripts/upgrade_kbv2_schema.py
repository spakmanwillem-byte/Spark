"""
KB v2 in-place schema upgrade (v5_kbv2_media_001)
==================================================
Voegt `media` en `needs` velden toe aan ALLE bestaande v2-kaarten zonder
ze opnieuw te migreren. Idempotent — slaat skip over kaarten die al voorzien zijn.
"""
import json
from pathlib import Path
from datetime import datetime, timezone

V2_DIR = Path(__file__).parent.parent / "data" / "knowledge" / "v2"


def compute_needs(card: dict) -> list:
    needs = []
    lagen = card.get("lagen") or {}
    if not (lagen.get("laag1") or "").strip():
        needs.append("laag1")
    if not any((card.get("ws5") or {}).values()):
        needs.append("ws5")
    media = card.get("media") or {}
    if not media.get("voice_url"):
        needs.append("voice")
    if not (media.get("image_urls") or []):
        needs.append("image")
    return needs


def upgrade_file(fp: Path):
    if not fp.exists():
        return 0
    with fp.open(encoding="utf-8") as f:
        data = json.load(f)
    n = 0
    for c in data.get("kaarten", []):
        if "media" not in c:
            c["media"] = {"voice_url": None, "voice_transcript": None, "image_urls": []}
            n += 1
        # Refresh needs altijd (idempotent)
        c["needs"] = compute_needs(c)
    if n > 0 or True:  # ook needs-refresh schrijven
        with fp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return n


def main():
    files = list(V2_DIR.glob("knowledge_v2_*.json")) + [V2_DIR / "knowledge_inbox.json"]
    total_added = 0
    for fp in files:
        added = upgrade_file(fp)
        print(f"  {fp.name}: +{added} media-velden toegevoegd")
        total_added += added
    print(f"\n✅ Schema upgrade voltooid: {total_added} kaarten kregen 'media' veld + needs herberekend")


if __name__ == "__main__":
    main()
