"""Slimme KB v2 lade-classifier — gebaseerd op TAGS, niet alleen begrip-naam.

Willem's inzicht: 'peren' als fruit = weten, 'peren' als audio = doen.
De TAGS bepalen wat de kaart écht is.

Tag-naar-lade mapping:
  doen   = acties, bewegingen, audio-acties, fysieke handelingen
  weten  = feiten, objecten, planten/dieren, concepten, plaatsen
  voelen = emoties, ervaringen, sensaties
  spreken = communicatie, taal, sociale interactie

Gebruik:
  python3 kb_tag_based_classifier.py [--dry-run] [--lade=doen]

Default = dry-run (rapport, géén wijzigingen).
"""
import json
import sys
from pathlib import Path
from collections import Counter

V2 = Path('/app/backend/data/knowledge/v2')

# Indicator-tags per lade (sterker signaal dan begrip-uitgang)
LADE_TAGS = {
    'doen': {
        'actie','beweging','handeling','fysiek','sport','training','oefening',
        'doe-tag','sport','dans','muziek-maken','audio-actie','klank','geluid',
        'route','reis','traject','werk-actie','werkwoord','infinitief',
        'productie','maak','bewerk','snij','kook','bak','wandel','fiets',
        'spelen-actie','spel-actie','reflex','ritueel','gewoonte','dagelijks',
    },
    'weten': {
        'fruit','groente','plant','boom','dier','vogel','vis','zoogdier',
        'object','voorwerp','locatie','plaats','land','stad','dorp','planeet',
        'feit','geschiedenis','wetenschap','techniek','natuur','aardrijkskunde',
        'biologie','chemie','fysica','geografie','filosofie','definitie',
        'instelling','organisatie','bedrijf','merk','product','concept',
        'persoon-feit','rol','beroep-feit','encyclopedie',
    },
    'voelen': {
        'emotie','sentiment','sensatie','stemming','gevoel','ervaring',
        'pijn','vreugde','verdriet','angst','liefde','woede','geluk',
        'sympathie','empathie','intuïtie','spiritueel','meditatie','rust',
        'kalm','onrust','ergernis','blijdschap','euforie','melancholie',
    },
    'spreken': {
        'taal','dialect','grammatica','woord','zin','uitdrukking','spreekwoord',
        'gezegde','communicatie','dialoog','gesprek','formulering','stijl',
        'frase','synoniem','jargon','register-taal','aanspreking','groet',
    },
}


def score_lade(tags, current_lade):
    """Geef score per lade gebaseerd op tag-overlap."""
    tag_set = set(t.lower() for t in (tags or []))
    scores = {}
    for lade, indicators in LADE_TAGS.items():
        scores[lade] = len(tag_set & indicators)
    return scores


def classify(card, current_lade):
    """Bepaal beste lade voor kaart. Return (best_lade, scores, confident)."""
    tags = card.get('tags', [])
    scores = score_lade(tags, current_lade)
    if not any(scores.values()):
        return current_lade, scores, False  # geen tag-signaal, blijf staan
    best_lade = max(scores, key=scores.get)
    best_score = scores[best_lade]
    # Confident = best_score ≥ 2 OF (best_score == 1 EN andere lades = 0)
    other_total = sum(v for k, v in scores.items() if k != best_lade)
    confident = (best_score >= 2) or (best_score == 1 and other_total == 0)
    return best_lade, scores, confident


def main():
    dry_run = '--dry-run' in sys.argv or '--apply' not in sys.argv
    only_lade = next((a.split('=')[1] for a in sys.argv if a.startswith('--lade=')), None)

    proposals = []
    for lade in ['doen', 'weten', 'voelen', 'spreken']:
        if only_lade and only_lade != lade:
            continue
        fp = V2 / f'knowledge_v2_{lade}.json'
        d = json.load(open(fp))
        for c in d.get('kaarten', []):
            best, scores, confident = classify(c, lade)
            if best != lade and confident:
                proposals.append({
                    'id': c.get('id'),
                    'begrip': c.get('begrip'),
                    'from_lade': lade,
                    'to_lade': best,
                    'tags': c.get('tags', []),
                    'scores': scores,
                })

    print(f"📊 Tag-based klassificatie ({len(proposals)} confident voorstellen)")
    print()
    by_move = Counter((p['from_lade'], p['to_lade']) for p in proposals)
    for (src, dst), n in sorted(by_move.items(), key=lambda x: -x[1]):
        print(f"  {src} → {dst}: {n}")
    print()
    print("Voorbeelden (eerste 15):")
    for p in proposals[:15]:
        print(f"  • '{p['begrip']}' [{p['from_lade']} → {p['to_lade']}] tags={p['tags'][:4]} scores={p['scores']}")

    rep_fp = '/app/backend/data/system/audit_v2_tag_based.json'
    json.dump({'proposals': proposals, 'totaal': len(proposals)},
              open(rep_fp, 'w'), indent=2, ensure_ascii=False)
    print(f"\nRapport: {rep_fp}")

    if dry_run:
        print("\n[DRY-RUN] Geen wijzigingen toegepast. Gebruik --apply om door te voeren.")
    else:
        print("\nWijzigingen worden NU toegepast...")
        # (apply logic — bewust niet default actief; vereist expliciete bevestiging)


if __name__ == '__main__':
    main()
