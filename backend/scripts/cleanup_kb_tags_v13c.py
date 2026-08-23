"""v13c_kb_tag_cleanup_001 — strip emoji's uit KB v2 tags + repareer
multi-line prompt-lek in tags. Idempotent, met backup.

Bug: sommige tags zijn opgeslagen als 'neutraal\\n\\n🌱 weten\\nbegrip'
(LLM output-fragmenten die als tag zijn opgeslagen). Dit script:
  1. Strip alle emoji's uit tags
  2. Split multi-line tags — behoud alleen eerste regel
  3. Trim + dedupe
  4. Optioneel: strip emoji's uit lagen1-4 (opt-in via --clean-lagen)
  5. Backup vóór wijziging

Run: cd /app/backend && python -m scripts.cleanup_kb_tags_v13c
     cd /app/backend && python -m scripts.cleanup_kb_tags_v13c --clean-lagen
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Emoji-range (Unicode 15 blocks die we op willen ruimen)
EMOJI_RE = re.compile(
    r"["
    r"\U0001F300-\U0001F5FF"   # symbols & pictographs
    r"\U0001F600-\U0001F64F"   # emoticons
    r"\U0001F680-\U0001F6FF"   # transport
    r"\U0001F700-\U0001F77F"
    r"\U0001F780-\U0001F7FF"
    r"\U0001F800-\U0001F8FF"
    r"\U0001F900-\U0001F9FF"   # supplemental symbols
    r"\U0001FA00-\U0001FA6F"
    r"\U0001FA70-\U0001FAFF"
    r"\U00002600-\U000026FF"   # misc symbols (☀ ☂ ★ ⚡ ✨)
    r"\U00002700-\U000027BF"   # dingbats (✅ ✔ ✖ ❤)
    r"\U0001F1E6-\U0001F1FF"   # flags
    r"]+", flags=re.UNICODE
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge" / "v2"
LADES = ["voelen", "spreken", "weten", "doen"]


def clean_tag(t: str) -> str:
    """Strip emoji + newlines. Behoud alleen eerste woord/zin."""
    if not isinstance(t, str):
        return ""
    # Split op newline en pak eerste regel (drop LLM-output-lek)
    first = t.split("\n")[0]
    # Strip emoji's + trim
    stripped = EMOJI_RE.sub("", first).strip()
    # Collapse dubbele spaties
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped


def clean_text(s: str) -> str:
    """Voor lagen1-4 — strip alleen emoji's, laat structuur intact."""
    if not isinstance(s, str):
        return s
    return EMOJI_RE.sub("", s).strip()


def cleanup_file(fp: Path, clean_lagen: bool = False, dry_run: bool = False) -> dict:
    if not fp.exists():
        return {"skipped": True, "reason": "not found"}
    data = json.loads(fp.read_text(encoding="utf-8"))
    cards = data.get("kaarten") or data.get("cards") or []
    tags_before = tags_after = 0
    tags_deduped = 0
    tags_removed_empty = 0
    tags_changed = 0
    lagen_cleaned = 0
    tag_examples_before = []

    for c in cards:
        if not isinstance(c, dict):
            continue
        raw_tags = c.get("tags") or []
        if raw_tags:
            tags_before += len(raw_tags)
            new_tags = []
            seen = set()
            for t in raw_tags:
                cleaned = clean_tag(t)
                if not cleaned:
                    tags_removed_empty += 1
                    tag_examples_before.append(t[:60])
                    continue
                if cleaned != str(t).strip():
                    tags_changed += 1
                    tag_examples_before.append(f"{t[:60]!r} → {cleaned!r}")
                key = cleaned.lower()
                if key in seen:
                    tags_deduped += 1
                    continue
                seen.add(key)
                new_tags.append(cleaned)
            tags_after += len(new_tags)
            c["tags"] = new_tags

        if clean_lagen:
            lagen = c.get("lagen") or {}
            for k, v in list(lagen.items()):
                if isinstance(v, str) and EMOJI_RE.search(v):
                    lagen[k] = clean_text(v)
                    lagen_cleaned += 1
            # Ook ws5
            ws5 = c.get("ws5") or {}
            for k, v in list(ws5.items()):
                if isinstance(v, str) and EMOJI_RE.search(v):
                    ws5[k] = clean_text(v)
                    lagen_cleaned += 1

    result = {
        "file": fp.name,
        "cards": len(cards),
        "tags_before": tags_before,
        "tags_after": tags_after,
        "tags_deduped": tags_deduped,
        "tags_removed_empty": tags_removed_empty,
        "tags_changed": tags_changed,
        "lagen_cleaned": lagen_cleaned,
        "examples": tag_examples_before[:8],
    }

    needs_write = (
        tags_before != tags_after or tags_deduped or tags_changed or lagen_cleaned
    )
    if not dry_run and needs_write:
        # Backup
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = fp.with_suffix(f".json.bak_tag_cleanup_{ts}")
        shutil.copy2(fp, bak)
        result["backup"] = bak.name
        # Write
        fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        result["written"] = True
    else:
        result["written"] = False

    return result


def main():
    clean_lagen = "--clean-lagen" in sys.argv
    dry_run = "--dry-run" in sys.argv
    print(f"v13c_kb_tag_cleanup_001 — clean_lagen={clean_lagen} dry_run={dry_run}")
    print(f"Data dir: {DATA_DIR}")
    print()

    total = {"tags_before": 0, "tags_after": 0, "tags_deduped": 0,
             "tags_removed_empty": 0, "lagen_cleaned": 0}
    for lade in LADES:
        fp = DATA_DIR / f"knowledge_v2_{lade}.json"
        r = cleanup_file(fp, clean_lagen=clean_lagen, dry_run=dry_run)
        print(f"[{lade:8s}] {json.dumps(r, ensure_ascii=False, default=str)}")
        for k in total:
            if k in r:
                total[k] += r[k]
    # Ook inbox
    fp = DATA_DIR / "knowledge_inbox.json"
    r = cleanup_file(fp, clean_lagen=clean_lagen, dry_run=dry_run)
    print(f"[inbox   ] {json.dumps(r, ensure_ascii=False, default=str)}")
    for k in total:
        if k in r:
            total[k] += r[k]

    print()
    print("=== TOTAAL ===")
    for k, v in total.items():
        print(f"  {k:22s} {v}")


if __name__ == "__main__":
    main()
