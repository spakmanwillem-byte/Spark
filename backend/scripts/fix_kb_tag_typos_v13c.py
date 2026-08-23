"""v13c_kb_tag_typo_fix_001 — Merge whitelist-bevestigde typo's in KB v2 tags.

Alleen paren die 100% zeker een spelfout zijn (letter mist/extra letter/duidelijk
tikfout), NIET semantische varianten (verlangen/verlagen zijn 2 woorden).

Elke merge: typo-tag wordt overal vervangen door canonical. Dedupliceert
per kaart. Backup vóór schrijven.

Run: cd /app/backend && python -m scripts.fix_kb_tag_typos_v13c
     cd /app/backend && python -m scripts.fix_kb_tag_typos_v13c --dry-run
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge" / "v2"
LADES = ["voelen", "spreken", "weten", "doen"]

# Handmatig gevalideerde 100% typo's uit typo_report.json (sessie 54).
# Formaat: (typo, canonical). Alleen tikfouten, geen betekenisvarianten.
TYPO_MAP = {
    # Ontbrekende/extra letters
    "kmogelijkheden": "mogelijkheden",       # k-prefix per ongeluk
    "onsistentie": "consistentie",           # c ontbreekt
    "mytologie": "mythologie",               # h ontbreekt
    "voedingstof": "voedingsstof",           # s ontbreekt
    "bewegingm": "beweging",                 # m te veel
    "ncryptie": "encryptie",                 # e ontbreekt
    "astzetten": "vastzetten",               # v ontbreekt
    # Samenstelling-varianten (echte tik/schrijf-fouten, geen synoniem)
    "hackerscultuur": "hackercultuur",       # -s tussenvoegsel niet standaard
    # Alleen formatting (spatie/underscore) — safe, geen betekenisverandering
    "cloudcomputing": "cloud computing",
    "kunstmatige_intelligentie": "kunstmatige intelligentie",
    "persoonlijke_ontwikkeling": "persoonlijke ontwikkeling",
    "zelfstandig_naamwoord": "zelfstandig naamwoord",
    "zelfstandig-naamwoord": "zelfstandig naamwoord",
    "context-zin": "contextzin",
    "sociale-interactie": "sociale interactie",
    "sociale_interactie": "sociale interactie",
    "hacker cultuur": "hackercultuur",
    "klein kind": "kleinkind",
}


def apply_typo_fixes(fp: Path, dry_run: bool = False) -> dict:
    if not fp.exists():
        return {"skipped": True}
    data = json.loads(fp.read_text(encoding="utf-8"))
    cards = data.get("kaarten") or data.get("cards") or []
    replaced = 0
    deduped = 0
    per_typo: dict = {}
    for c in cards:
        if not isinstance(c, dict):
            continue
        tags = c.get("tags") or []
        if not tags:
            continue
        new_tags = []
        seen = set()
        touched = False
        for t in tags:
            key = str(t).strip().lower()
            if key in TYPO_MAP:
                canonical = TYPO_MAP[key]
                per_typo[key] = per_typo.get(key, 0) + 1
                replaced += 1
                key = canonical
                touched = True
            if key in seen:
                deduped += 1
                continue
            seen.add(key)
            new_tags.append(t if str(t).strip().lower() == key else key)
        if touched:
            c["tags"] = new_tags

    result = {
        "file": fp.name,
        "cards": len(cards),
        "replaced": replaced,
        "deduped": deduped,
        "per_typo": per_typo,
    }
    if replaced > 0 and not dry_run:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = fp.with_suffix(f".json.bak_typo_fix_{ts}")
        shutil.copy2(fp, bak)
        fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        result["backup"] = bak.name
        result["written"] = True
    else:
        result["written"] = False
    return result


def main():
    dry_run = "--dry-run" in sys.argv
    print(f"v13c_kb_tag_typo_fix_001 — dry_run={dry_run}")
    print(f"Whitelist: {len(TYPO_MAP)} typo→canonical mappings")
    print()

    total_replaced = 0
    total_deduped = 0
    combined_per_typo: dict = {}
    for lade in LADES:
        fp = DATA_DIR / f"knowledge_v2_{lade}.json"
        r = apply_typo_fixes(fp, dry_run=dry_run)
        print(f"[{lade:8s}] replaced={r.get('replaced',0):4d}  deduped={r.get('deduped',0):3d}  "
              f"written={r.get('written', False)}")
        total_replaced += r.get("replaced", 0)
        total_deduped += r.get("deduped", 0)
        for k, n in (r.get("per_typo") or {}).items():
            combined_per_typo[k] = combined_per_typo.get(k, 0) + n

    print()
    print("=== TOTAAL ===")
    print(f"  Vervangen: {total_replaced}")
    print(f"  Gededupliceerd: {total_deduped}")
    print()
    print("Per typo:")
    for k, n in sorted(combined_per_typo.items(), key=lambda x: -x[1]):
        print(f"  {k:35s} → {TYPO_MAP[k]:30s}  {n}×")


if __name__ == "__main__":
    main()
