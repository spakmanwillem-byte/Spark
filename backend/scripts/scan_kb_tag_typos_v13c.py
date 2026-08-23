"""v13c_kb_tag_typo_scan_001 — Zoek waarschijnlijke spelfouten in KB v2 tags.

Gebruikt rapidfuzz om near-duplicates te vinden (bv 'muziek' vs 'musziek',
'psychologie' vs 'psycholgie', 'ontwikkelen' vs 'ontwikklen').

Werkwijze:
  1. Verzamel alle unieke tags uit 4 lades
  2. Voor elke tag: zoek tags met levenshtein-similarity ≥ 88% maar niet identiek
  3. Alleen paren waar 1 tag ≥ 3× voorkomt en de ander ≤ 2×
     (waarschijnlijk = correcte + typo)

Output: rapport in /app/backend/data/knowledge/v2/typo_report.json + terminal.

Geen automatische fixes — Willem beslist per stem via KbV2TagCuration UI
of via handmatige merge.

Run: cd /app/backend && python -m scripts.scan_kb_tag_typos_v13c
     cd /app/backend && python -m scripts.scan_kb_tag_typos_v13c --min-ratio 92
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from rapidfuzz import fuzz

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge" / "v2"
LADES = ["voelen", "spreken", "weten", "doen"]
REPORT_FP = DATA_DIR / "typo_report.json"


def collect_tags() -> Counter:
    counter: Counter = Counter()
    for lade in LADES:
        fp = DATA_DIR / f"knowledge_v2_{lade}.json"
        if not fp.exists():
            continue
        data = json.loads(fp.read_text(encoding="utf-8"))
        for c in data.get("kaarten", []):
            for t in (c.get("tags") or []):
                if isinstance(t, str) and t.strip():
                    counter[t.strip().lower()] += 1
    return counter


def find_typo_pairs(counter: Counter, min_ratio: int = 88, min_freq_correct: int = 3) -> list:
    """Return list of (canonical, typo, ratio, canonical_freq, typo_freq)."""
    tags = list(counter.keys())
    # Filter: alleen tags met lengte >= 4 (typo-detectie op korte tags = false-positives)
    tags = [t for t in tags if len(t) >= 4]
    tags_sorted = sorted(tags, key=lambda t: -counter[t])

    pairs = []
    seen_pairs = set()
    # Voor efficiëntie: alleen typo-candidates die < min_freq_correct voorkomen
    for typo in tags_sorted:
        if counter[typo] >= min_freq_correct:
            continue
        # Zoek de dichtstbijzijnde tag die WEL vaak voorkomt
        best = None
        best_ratio = 0
        for cand in tags_sorted:
            if cand == typo:
                continue
            if counter[cand] < min_freq_correct:
                continue
            # Snelle length-check: verschil > 3 tekens → skip
            if abs(len(cand) - len(typo)) > 3:
                continue
            r = fuzz.ratio(typo, cand)
            if r >= min_ratio and r > best_ratio:
                best_ratio = r
                best = cand
        if best:
            key = tuple(sorted([typo, best]))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            pairs.append({
                "canonical": best,
                "typo": typo,
                "ratio": best_ratio,
                "canonical_freq": counter[best],
                "typo_freq": counter[typo],
            })
    pairs.sort(key=lambda p: (-p["ratio"], -p["canonical_freq"]))
    return pairs


def main():
    min_ratio = 88
    for arg in sys.argv[1:]:
        if arg.startswith("--min-ratio"):
            try:
                min_ratio = int(arg.split("=")[-1] if "=" in arg
                                else sys.argv[sys.argv.index(arg) + 1])
            except Exception:
                pass

    print(f"v13c_kb_tag_typo_scan_001 — min_ratio={min_ratio}")
    print("Verzamelen tags...")
    counter = collect_tags()
    print(f"Unieke tags: {len(counter)}")
    print(f"Totaal tag-instances: {sum(counter.values())}")
    print()
    print("Scannen op typo's...")
    pairs = find_typo_pairs(counter, min_ratio=min_ratio)
    print(f"Verdachte paren gevonden: {len(pairs)}")
    print()
    print("Top 40 (canonical <- typo, similarity, freq):")
    print("-" * 80)
    for p in pairs[:40]:
        print(f"  {p['canonical']:25s} ← {p['typo']:25s} "
              f"[{p['ratio']:5.1f}%]  ({p['canonical_freq']}× vs {p['typo_freq']}×)")

    # Save rapport
    report = {
        "total_unique_tags": len(counter),
        "total_tag_instances": sum(counter.values()),
        "min_ratio": min_ratio,
        "pairs_found": len(pairs),
        "pairs": pairs,
    }
    REPORT_FP.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print(f"Rapport: {REPORT_FP}")


if __name__ == "__main__":
    main()
