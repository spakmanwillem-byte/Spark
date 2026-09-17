"""v14_fill_missing_tags_001 — tags genereren voor KB v2-kaarten zonder tags (Willem 17-09-2026).

Gebruik: python scripts/fill_missing_tags_v14.py [--dry]
Per kaart: LLM (via llm_router) → 5-8 inhoudelijke tags op basis van begrip + lagen + ws5,
daarna sanitize_tag_list + begrip zelf als eerste tag. Testkaarten (test-*) worden overgeslagen.
"""
import asyncio, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.kb_v2 import service as kb
from modules.kb_v2.tag_sanitizer import sanitize_tag_list
from modules.chat import llm_router

DRY = "--dry" in sys.argv


def _prompt(c):
    lagen = c.get("lagen") or {}
    ws5 = c.get("ws5") or {}
    return [
        {"role": "system", "content": "Je bent een Nederlandse kennisbank-redacteur. Antwoord ALLEEN met een JSON-lijst van 5 tot 8 korte, inhoudelijke Nederlandse tags (kleine letters, enkelvoud, geen systeemwoorden). Geen uitleg."},
        {"role": "user", "content": f"Begrip: {c['begrip']}\nLade: {c.get('lade')}\nLaag1: {lagen.get('laag1','')}\nLaag2: {lagen.get('laag2','')[:400]}\n5W: {json.dumps(ws5, ensure_ascii=False)[:500]}"},
    ]


async def main():
    todo = [c for c in kb._all_cards_with_lade() if len(c.get("tags") or []) < kb.MIN_TAGS_FOR_LADE and c["_lade"] != "inbox" and not str(c.get("begrip", "")).lower().startswith("test-")]
    print(f"{len(todo)} kaarten met <{kb.MIN_TAGS_FOR_LADE} tags")
    done = 0
    for c in todo:
        resp = await llm_router.chat_complete(_prompt(c), temperature=0.3, max_tokens=700, timeout=30.0, use_cache=False)
        text = (resp.get("text") or "").strip()
        m = re.search(r"\[.*\]", text, re.S)
        try:
            raw = json.loads(m.group(0)) if m else []
        except Exception:
            raw = [t.strip() for t in re.split(r"[,\n]", text) if t.strip()]
        if len(raw) < 3:
            print(f"    RAW({c['begrip']}): {text[:160]!r}")
        tags = sanitize_tag_list([str(t).lower() for t in list(c.get("tags") or []) + [c["begrip"]] + list(raw)])
        print(f"  {c['_lade']:<7} {c['begrip']:<22} {len(c.get('tags') or [])}→{len(tags)}")
        if len(tags) >= kb.MIN_TAGS_FOR_LADE and not DRY:
            kb.edit_card(c["id"], c["_lade"], {"tags": tags}, user_id="user-001")
            done += 1
    print(f"klaar: {done} kaarten bijgewerkt" + (" (DRY)" if DRY else ""))


asyncio.run(main())
