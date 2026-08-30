"""v13d_orphan_tags_to_cards_001 (sessie 55) — Willem's verzoek:
scan alle KB-tags en maak voor elke tag die nog geen eigen kaart heeft, een
'onbeantwoorde' skeleton-kaart in de inbox.

**Waarom?**
Willem: "6000 nodes / 59347 edges, en toch pakt snap onbekende woorden niet".
Root cause: tags dragen kennis (bv 'verkoop' als tag op 'inkoop'-kaart), maar
er is geen eigen kaart voor 'verkoop' → snap detecteert niks bekends → user
krijgt geen snap-response.

Fix: elke unieke tag krijgt óf een bestaande kaart (goede match), óf een
skeleton-kaart in de inbox met needs=[laag1,laag2] zodat Willem 'm kan aanvullen.

**Filters** (om noise te vermijden):
- Skip < 3 chars
- Skip cijfers-only
- Skip als exacte match op bestaand begrip (case-insensitive)
- Skip als plural van bestaand begrip ('users' → 'user')
- Skip 'kbv2_*' interne tracer-tags
- Skip emoji / leesteken-only

**Idempotent**: 2× runnen = zelfde resultaat. Herkent bestaande skeletons via
_inbox_reason.

Usage:
  python3 /app/backend/scripts/orphan_tags_to_cards_v13d.py --dry-run
  python3 /app/backend/scripts/orphan_tags_to_cards_v13d.py --commit
"""
import json
import re
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

V2 = Path('/app/backend/data/knowledge/v2')
INBOX = V2 / 'knowledge_inbox.json'
NOW = datetime.now(timezone.utc).isoformat()
INBOX_REASON = "orphan_tag_v13d_sessie55"

# Skip patterns
SKIP_EXACT = {"kbv2","kb","v2","v13","nvt","nvt.","onbekend","null","none","tbd","todo",
              "?","??","???","...","..","-","--","x","y","z"}
SKIP_PREFIX = ("kbv2_card_", "kbv2_", "id_", "user-", "kbv2-", "session-", "sess-")

# v13d sessie 55 — Kwaliteitsfilters:
MIN_COUNT = 3  # minimaal aantal keer dat tag voorkomt om waardevol te zijn
META_TAGS = {
    'uitleg','patroon','concept','methode','type','soort','beleving','ervaring',
    'context','doel','functie','handeling','wetenbegrip','spreekbegrip','doenbegrip',
    'voelbegrip','begrip','eigenschap','kenmerk','vorm','kleur','materiaal',
    'onderdeel','object','proces','systeem','structuur','staat','fase',
    'symboliek','uiting','activiteit','moment','bezigheid','beweging',
    'werkwoord','naamwoord','bijvoeglijk','zelfstandig','stof','ding',
}


def _is_noise(tag: str) -> bool:
    t = (tag or "").strip()
    if not t or len(t) < 3: return True
    if t.lower() in SKIP_EXACT: return True
    if any(t.lower().startswith(p) for p in SKIP_PREFIX): return True
    if t.isdigit(): return True
    # geen letters
    if not re.search(r"[a-zà-ÿ]", t, re.IGNORECASE): return True
    # Alleen leestekens / emojis
    if re.match(r'^[\W_]+$', t, re.UNICODE): return True
    return False


def _canonicalize(word: str) -> str:
    """Naive plural→singular voor NL/EN om dubbele kaarten te voorkomen.

    v13d_sessie58: unicode-apostrofen (’ ‘ ´ ` ) worden éérst naar rechte
    apostrof genormaliseerd zodat "foto’s" en "foto's" niet als aparte
    begrippen worden gezien (ghost-preventie in orphan-scan).
    """
    w = (word or "").lower().strip()
    # Unicode-apostrofen normaliseren
    w = w.translate({
        0x2019: "'", 0x2018: "'", 0x02BC: "'",
        0x00B4: "'", 0x0060: "'", 0x201B: "'",
    })
    # -en (Dutch plural)  bv "gebruikers" → "gebruiker"; skip 3-letter woorden
    if len(w) > 5 and w.endswith('en') and not w.endswith('een'):
        return w[:-2]
    # -'s (Dutch bezittelijk-/meervoud met apostrof, bv "foto's" → "foto")
    if len(w) > 3 and w.endswith("'s"):
        return w[:-2]
    # -s (English + NL)
    if len(w) > 4 and w.endswith('s') and not w.endswith('ss'):
        return w[:-1]
    return w


def collect_all() -> tuple[dict, set, dict]:
    """Return: {tag: count}, set(bestaande_begrippen_canonical), {tag: representative_card_id}"""
    tag_counts: Counter[str] = Counter()
    tag_rep_card: dict[str, str] = {}
    known_begrippen: set[str] = set()

    for p in sorted(V2.glob('*.json')):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        for k in d.get('kaarten', []):
            b = (k.get('begrip') or '').strip()
            if b:
                known_begrippen.add(_canonicalize(b))
                known_begrippen.add(b.lower())
            for tag in (k.get('tags') or []):
                t = (tag or '').strip()
                if not t:
                    continue
                tag_counts[t] += 1
                tag_rep_card.setdefault(t, k.get('id'))
    return tag_counts, known_begrippen, tag_rep_card


def find_orphans(tag_counts, known_begrippen) -> list:
    """Return list of (tag, count) voor tags zonder eigen kaart.
    v13d: alleen tags met count >= MIN_COUNT + niet-meta."""
    orphans = []
    for tag, count in tag_counts.most_common():
        if _is_noise(tag):
            continue
        if count < MIN_COUNT:
            continue
        if tag.lower() in META_TAGS:
            continue
        canon = _canonicalize(tag)
        if canon in known_begrippen or tag.lower() in known_begrippen:
            continue
        orphans.append((tag, count))
    return orphans


def make_skeleton(tag: str, count: int, rep_card_id: str) -> dict:
    """Maak minimale kaart met correcte metadata (RULE_footnote_metadata_001)."""
    return {
        "id": f"kbv2-{uuid.uuid4().hex[:8]}",
        "begrip": tag,
        "lade": None,          # niet ingedeeld — Willem/curator moet indelen
        "status": "draft",
        "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
        "ws5": {},
        "tags": [tag.lower()],  # zelf-tag zodat search later matcht
        "verbanden": ([{"type": "orphan_source_card", "card_id": rep_card_id}]
                      if rep_card_id else []),
        "topic": None,
        "footnote": {
            "bron": "kb_v2:tag_scan",
            "aangemaakt_door": "orphan_tag_scanner",
            "aangemaakt_op": NOW,
            "vertrouwen": 0.3,
            "ingedeeld_door": None,
            "ingedeeld_op": None,
            "vorige_versie_v1": None,
            "extract_source": "orphan_tag_scanner_v13d",
            "extract_at": NOW,
            "extract_context_snippet": f"Tag komt {count}× voor in KB maar had geen eigen kaart",
            "needs_review": True,
            "llm_generated": False,
        },
        "media": {"voice_url": None, "voice_transcript": None, "image_urls": []},
        "needs": ["laag1", "laag2", "ws5", "lade"],
        "_inbox_reason": INBOX_REASON,
        "_orphan_frequency": count,
    }


def main():
    commit = "--commit" in sys.argv

    tag_counts, known_begrippen, tag_rep_card = collect_all()
    print(f"📊 Totaal unieke tags: {len(tag_counts)}")
    print(f"📊 Totaal bestaande begrippen (canonical): {len(known_begrippen)}")

    orphans = find_orphans(tag_counts, known_begrippen)
    print(f"🔍 Orphan tags gevonden: {len(orphans)}")

    # Top 20 preview
    print("\n=== TOP 20 orphans (meest voorkomend) ===")
    for tag, count in orphans[:20]:
        print(f"  {count:4d}× | {tag}")

    if not commit:
        print(f"\n💡 Dry-run — geen writes. Voeg --commit toe om {len(orphans)} skeleton-kaarten in inbox aan te maken.")
        return

    # Load inbox
    inbox = json.loads(INBOX.read_text()) if INBOX.exists() else {"kaarten": []}
    kaarten = inbox.setdefault('kaarten', [])

    # Skip als er al een orphan-skeleton bestaat voor dit begrip
    existing_orphan_begrippen = {
        (k.get('begrip') or '').lower()
        for k in kaarten
        if k.get('_inbox_reason') == INBOX_REASON
    }

    added = 0
    for tag, count in orphans:
        if tag.lower() in existing_orphan_begrippen:
            continue
        kaarten.append(make_skeleton(tag, count, tag_rep_card.get(tag)))
        added += 1

    INBOX.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))
    print(f"\n✅ {added} skeleton-kaarten toegevoegd aan inbox")
    print(f"   Inbox totaal nu: {len(kaarten)}")


if __name__ == '__main__':
    main()
