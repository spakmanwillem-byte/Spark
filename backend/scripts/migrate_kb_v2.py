"""
Knowledge Base v2 Migration (v5_kbv2_001)
==========================================
Splitst /data/knowledge/learned_knowledge/knowledge_base.json (5288 entries, 10MB)
in 4 lades + inbox + index, volgens Willem's 4-vakken-grid:

  voelen   ← emotie / blij / boos / bedroefd / bang / verbinding / gevoel
  spreken  ← communicatie / taal / dialoog / gesprek / betekenis / vraag
  weten    ← systeem / structuur / proces / technologie / tijd / kennis / informatie
  doen     ← gedrag / sociaal / reactie / interactie / actie / samenwerking

Veiligheidsgaranties:
  • v1-bestand wordt niet gewijzigd (alleen kopie naar .v1_backup_TS)
  • Idempotent: meermaals draaien overschrijft alleen v2-files
  • Tag-tie of geen match → kaart blijft in Inbox voor handmatige keuze
  • Kaarten zonder laag1 → altijd Inbox
  • Schrijft uitgebreid report naar /app/memory/KB_V2_MIGRATION_REPORT.md

Gebruik:
  python3 -m backend.scripts.migrate_kb_v2 --dry-run
  python3 -m backend.scripts.migrate_kb_v2 --commit
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).parent.parent
V1_FILE = BACKEND_ROOT / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"
V2_DIR = BACKEND_ROOT / "data" / "knowledge" / "v2"
REPORT_FILE = Path("/app/memory/KB_V2_MIGRATION_REPORT.md")

# ---------------------------------------------------------------------------
# 4 Lades + classifier-keywords (sorteer op specificiteit)
# ---------------------------------------------------------------------------
LADES = {
    "voelen": {
        "icon": "🌸",
        "naam_nl": "Voelen",
        "stroom": "Emotie & Verbinding",
        "keywords": {
            "emotie", "blij", "boos", "bedroefd", "verdrietig", "bang", "bange",
            "verbinding", "gevoel", "gevoelens", "vreugde", "rouw", "angst",
            "liefde", "passie", "empathie", "warmte", "geluk", "verdriet",
            "frustratie", "boosheid", "vertrouwen", "veilig", "onveilig",
            "intuitief", "intuitie", "stemming", "schaamte", "trots",
            # uitgebreid: spirituele/innerlijke verbinding
            "spiritualiteit", "mythologie", "reiki", "traditie", "generatie",
            "balans", "kracht", "rust", "stilte", "vrede", "aanwezigheid",
            "herkenning", "dankbaarheid", "compassie", "hoop", "verlangen",
        },
    },
    "spreken": {
        "icon": "💬",
        "naam_nl": "Spreken",
        "stroom": "Communicatie & Taal",
        "keywords": {
            "communicatie", "taal", "dialoog", "gesprek", "betekenis", "vraag",
            "woord", "woorden", "spraak", "zeggen", "vertellen", "uitleg",
            "verhaal", "verhalen", "schrijven", "luisteren", "uiten", "delen",
            "context", "informatie", "boodschap", "tekst", "uitspraak",
            "intentie", "richting",
            # uitgebreid
            "overdracht", "vertaling", "uitdrukking", "stem", "geluid",
            "antwoord", "advies",
        },
    },
    "weten": {
        "icon": "🧠",
        "naam_nl": "Weten",
        "stroom": "Systeem & Kennis",
        "keywords": {
            "systeem", "structuur", "proces", "technologie", "tech", "tijd",
            "kennis", "leren", "wetenschap", "regel", "regels", "logica",
            "data", "database", "code", "computer", "algoritme", "model",
            "concept", "principe", "feiten", "feit", "wet", "wetten",
            "geschiedenis", "natuur", "fysica", "wiskunde", "biologie",
            "energie", "materie", "ruimte", "universum",
            # uitgebreid: materie, lichaam, natuur als kennis-domeinen
            "gereedschap", "grondstof", "materiaal", "metaal", "plant", "dier",
            "lichaam", "anatomie", "gezondheid", "water", "transport",
            "voeding", "voedsel", "eigenschap", "opslag", "gebouw",
            "constructie", "apparaat", "object", "fysiek", "biologie",
            "analyse", "soort", "soorten", "type", "categorie", "definitie",
        },
    },
    "doen": {
        "icon": "🎭",
        "naam_nl": "Doen",
        "stroom": "Gedrag & Actie",
        "keywords": {
            "gedrag", "sociaal", "reactie", "interactie", "actie", "handelen",
            "samenwerking", "doen", "maken", "bouwen", "werken", "spelen",
            "beweging", "gewoonte", "ritueel", "rol", "rollen", "leiderschap",
            "groep", "gemeenschap", "samenleving", "cultuur",
            "ontwikkeling", "groei", "verandering", "praktijk", "vaardigheid",
            # uitgebreid: economie & maken-doen
            "keuken", "koken", "landbouw", "bouw", "economie", "financiën",
            "geld", "handel", "verkoop", "kosten", "kleding", "hulpmiddel",
            "controle", "marketing", "administratie", "bedrijf", "industrie",
            "bescherming", "veiligheid", "spel", "game", "training", "oefenen",
            "regelen", "organiseren", "plannen", "uitvoeren",
        },
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_filestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def has_complete_lagen(entry: dict) -> bool:
    """v2-kandidaat: minimaal laag1 aanwezig en niet-leeg."""
    lagen = entry.get("lagen") or {}
    return bool((lagen.get("laag1") or "").strip())


def classify(entry: dict) -> tuple[str | None, dict]:
    """Bepaal lade op basis van tag-overlap met elke lade-keyword-set.
    Returnt (lade_id of None, scores-dict).
    Bij tie of geen match → None (= Inbox)."""
    tags_lower = {(t or "").lower().strip() for t in (entry.get("tags") or [])}
    topic_lower = (entry.get("topic") or "").lower().strip()
    haystack = tags_lower | {topic_lower}
    scores = {lade: len(haystack & cfg["keywords"]) for lade, cfg in LADES.items()}
    max_score = max(scores.values())
    if max_score == 0:
        return None, scores
    winners = [lade for lade, sc in scores.items() if sc == max_score]
    if len(winners) > 1:
        return None, scores  # tie → handmatige keuze
    return winners[0], scores


def build_v2_card(v1_entry: dict, lade: str | None) -> dict:
    """Bouw v2-kaart uit v1-entry, behoud traceability naar v1."""
    lagen = v1_entry.get("lagen") or {}
    has_l1 = bool((lagen.get("laag1") or "").strip())
    needs: list = []
    if not has_l1:
        needs.append("laag1")
    if not (v1_entry.get("ws5") or {}):
        needs.append("ws5")
    return {
        "id": f"kbv2-{v1_entry.get('id','')[3:]}" if v1_entry.get("id", "").startswith("kb-")
              else f"kbv2-{uuid.uuid4().hex[:8]}",
        "begrip": v1_entry.get("begrip") or v1_entry.get("term") or "",
        "lade": lade,  # None = nog in inbox
        "status": v1_entry.get("status") or "active",
        "lagen": {
            "laag1": (lagen.get("laag1") or "").strip(),
            "laag2": (lagen.get("laag2") or "").strip(),
            "laag3": (lagen.get("laag3") or "").strip(),
            "laag4": (lagen.get("laag4") or "").strip(),  # nieuw, optioneel
        },
        "ws5": v1_entry.get("ws5") or {},
        "tags": v1_entry.get("tags") or [],
        "topic": v1_entry.get("topic") or "",
        "verbanden": [],
        # v5_kbv2_media_001 — media + needs-checklist
        "media": {
            "voice_url": None,        # audio van de inspraak (Whisper bron)
            "voice_transcript": None,  # tekst van Whisper-transcriptie
            "image_urls": [],          # uploads van foto's bij deze kaart
        },
        "needs": needs,  # ["laag1","ws5","voice","image"] — checklist wat nog mist
        "footnote": {
            "bron": v1_entry.get("created_by") or v1_entry.get("detected_by") or "onbekend",
            "ingedeeld_door": "kbv2_migratie" if lade else None,
            "ingedeeld_op": now_iso() if lade else None,
            "vorige_versie_v1": v1_entry.get("id"),
            "vertrouwen": _confidence(v1_entry),
            "belangrijkheid": v1_entry.get("belangrijkheid") or 5,
        },
    }


def _confidence(v1: dict) -> float:
    """Schat vertrouwen op basis van metadata-flags + laag-volledigheid."""
    md = v1.get("metadata") or {}
    inferred_flags = sum(1 for k, v in md.items() if k.endswith("_inferred") and v)
    lagen = v1.get("lagen") or {}
    laag_count = sum(1 for v in lagen.values() if (v or "").strip())
    base = 0.5 + 0.1 * laag_count  # 0.5 → 0.9 op 4 lagen
    penalty = 0.05 * inferred_flags
    return max(0.1, min(0.99, round(base - penalty, 2)))


# ---------------------------------------------------------------------------
# Main migration
# ---------------------------------------------------------------------------

def migrate(commit: bool = False) -> dict:
    if not V1_FILE.exists():
        return {"error": f"v1 file niet gevonden: {V1_FILE}"}

    print(f"📖 v1 inlezen: {V1_FILE}")
    with V1_FILE.open(encoding="utf-8") as f:
        v1_data = json.load(f)
    entries = v1_data.get("knowledge_entries", []) or []
    print(f"   {len(entries)} entries gelezen")

    # Bucket distributie
    buckets: dict[str, list] = {lade: [] for lade in LADES}
    inbox: list = []
    reasons = Counter()  # waarom in inbox
    tie_examples: list = []
    sample_per_lade: dict[str, list] = {lade: [] for lade in LADES}

    for v1 in entries:
        if not has_complete_lagen(v1):
            v2 = build_v2_card(v1, lade=None)
            v2["_inbox_reason"] = "missing_laag1"
            inbox.append(v2)
            reasons["missing_laag1"] += 1
            continue
        lade, scores = classify(v1)
        if lade is None:
            v2 = build_v2_card(v1, lade=None)
            tie_or_none = "no_match" if max(scores.values()) == 0 else "tag_tie"
            v2["_inbox_reason"] = tie_or_none
            v2["_classifier_scores"] = scores
            inbox.append(v2)
            reasons[tie_or_none] += 1
            if tie_or_none == "tag_tie" and len(tie_examples) < 5:
                tie_examples.append({"begrip": v1.get("begrip"), "scores": scores})
            continue
        v2 = build_v2_card(v1, lade=lade)
        buckets[lade].append(v2)
        if len(sample_per_lade[lade]) < 5:
            sample_per_lade[lade].append(v1.get("begrip"))

    # Stats
    summary = {
        "total_v1": len(entries),
        "per_lade": {lade: len(buckets[lade]) for lade in LADES},
        "inbox": len(inbox),
        "inbox_reasons": dict(reasons),
        "tie_examples": tie_examples,
        "sample_per_lade": sample_per_lade,
    }

    if not commit:
        print("\n🔬 DRY-RUN — niets geschreven")
        write_report(summary, dry_run=True)
        return summary

    # COMMIT mode — backup + write
    V2_DIR.mkdir(parents=True, exist_ok=True)
    backup_file = V1_FILE.with_suffix(f".json.v1_backup_{now_filestamp()}")
    shutil.copy2(V1_FILE, backup_file)
    print(f"💾 Backup gemaakt: {backup_file.name}")

    # Schrijf 4 lade-files
    for lade, cards in buckets.items():
        cfg = LADES[lade]
        out = {
            "lade_id": lade,
            "lade_naam": cfg["naam_nl"],
            "icon": cfg["icon"],
            "stroom": cfg["stroom"],
            "metadata": {
                "version": "v2",
                "created_at": now_iso(),
                "card_count": len(cards),
                "source": "knowledge_base.json (v1) — auto-classified",
            },
            "kaarten": cards,
        }
        fp = V2_DIR / f"knowledge_v2_{lade}.json"
        with fp.open("w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"   📚 {fp.name}: {len(cards)} kaarten")

    # Inbox
    inbox_out = {
        "version": "v2",
        "created_at": now_iso(),
        "card_count": len(inbox),
        "metadata": {
            "purpose": "Wachtrij van onbeantwoorde of nog-niet-geclassificeerde kennis-kaarten",
            "redenen": dict(reasons),
        },
        "kaarten": inbox,
    }
    inbox_fp = V2_DIR / "knowledge_inbox.json"
    with inbox_fp.open("w", encoding="utf-8") as f:
        json.dump(inbox_out, f, ensure_ascii=False, indent=2)
    print(f"   📥 {inbox_fp.name}: {len(inbox)} kaarten")

    # Index
    index: dict[str, dict] = {}
    for lade, cards in buckets.items():
        for c in cards:
            index[c["begrip"].lower()] = {
                "kaart_id": c["id"],
                "lade": lade,
                "has_lagen": [k for k, v in c["lagen"].items() if v],
                "last_updated": now_iso(),
            }
    for c in inbox:
        index[c["begrip"].lower()] = {
            "kaart_id": c["id"],
            "lade": None,
            "has_lagen": [k for k, v in c["lagen"].items() if v],
            "last_updated": now_iso(),
        }
    idx_fp = V2_DIR / "knowledge_index.json"
    with idx_fp.open("w", encoding="utf-8") as f:
        json.dump({
            "version": "v2",
            "created_at": now_iso(),
            "entry_count": len(index),
            "entries": index,
        }, f, ensure_ascii=False, indent=2)
    print(f"   🗂️  {idx_fp.name}: {len(index)} begrippen")

    summary["backup_file"] = str(backup_file.name)
    summary["v2_dir"] = str(V2_DIR)
    write_report(summary, dry_run=False)
    print("\n✅ Migratie voltooid — v1 ongewijzigd, v2 staat naast.")
    return summary


def write_report(summary: dict, dry_run: bool):
    mode = "DRY-RUN" if dry_run else "COMMITTED"
    lines = [
        f"# KB v2 Migration Report — {mode}",
        f"_Generated: {now_iso()}_",
        "",
        "## 📊 Verdeling",
        "",
        "| Lade | Aantal kaarten | Sample |",
        "|---|---|---|",
    ]
    for lade in LADES:
        n = summary["per_lade"][lade]
        sample = ", ".join(summary["sample_per_lade"].get(lade, [])[:5])
        lines.append(f"| {LADES[lade]['icon']} **{LADES[lade]['naam_nl']}** ({lade}) | {n} | {sample} |")
    lines.append(f"| 📥 **Inbox** | {summary['inbox']} | (onbeantwoord / tag-tie / no-match) |")
    total_classified = sum(summary["per_lade"].values())
    pct_classified = round(100 * total_classified / max(1, summary["total_v1"]), 1)
    lines += [
        "",
        f"**Totaal v1:** {summary['total_v1']}",
        f"**Geclassificeerd:** {total_classified} ({pct_classified}%)",
        f"**Inbox:** {summary['inbox']}",
        "",
        "## 📥 Inbox-redenen",
        "",
    ]
    for reason, n in summary["inbox_reasons"].items():
        lines.append(f"- `{reason}`: {n}")
    lines.append("")
    if summary["tie_examples"]:
        lines.append("## ⚖️ Tag-tie voorbeelden (handmatige keuze nodig)")
        lines.append("")
        for ex in summary["tie_examples"]:
            lines.append(f"- **{ex['begrip']}** — scores: `{ex['scores']}`")
        lines.append("")
    if not dry_run:
        lines += [
            "## 💾 Files",
            "",
            f"- Backup: `{summary['backup_file']}`",
            f"- v2 directory: `{summary['v2_dir']}`",
            "",
            "## ✅ Status",
            "v1 `knowledge_base.json` is **niet gewijzigd**.",
            "Alle bestaande services blijven v1 lezen tot v2 routes klaar zijn.",
        ]
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"📝 Report: {REPORT_FILE}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true", help="Schrijf v2-files (anders dry-run)")
    args = ap.parse_args()
    out = migrate(commit=args.commit)
    print("\n=== SUMMARY ===")
    print(json.dumps({
        "total": out.get("total_v1"),
        "per_lade": out.get("per_lade"),
        "inbox": out.get("inbox"),
        "inbox_reasons": out.get("inbox_reasons"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
