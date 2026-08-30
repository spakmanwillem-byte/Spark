"""Update Foto's-kaart met de door Willem aangeleverde uitgebreide versie
en verwijder de lege ghost-duplicaat 'foto’s' (unicode-apostrof) uit inbox.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.storage import load_json, save_json  # noqa: E402

BASE = Path(__file__).parent.parent / "data" / "knowledge" / "v2"
INBOX = BASE / "knowledge_inbox.json"
WETEN = BASE / "knowledge_v2_weten.json"
INDEX = BASE / "knowledge_index.json"

TARGET_ID = "kbv2-c0421b96"
GHOST_ID = "kbv2-63c3d542"

NEW_CONTENT = {
    "lagen": {
        "laag1": "Foto's zijn afbeeldingen die een moment, persoon, voorwerp, dier of omgeving visueel vastleggen.",
        "laag2": "Een foto wordt meestal gemaakt met een camera of smartphone. Foto's kunnen digitaal worden opgeslagen of op papier worden afgedrukt.",
        "laag3": "Foto's kunnen bijvoorbeeld worden gebruikt voor: herinneringen; communicatie; documentatie; kunst; nieuws en verslaggeving; identificatie; informatieverstrekking. Een foto kan digitaal worden opgeslagen, bewerkt, gedeeld of afgedrukt.",
        "laag4": "Een foto is een visuele vastlegging van een onderwerp of situatie die met behulp van een camera wordt gemaakt. Foto's kunnen mensen, dieren, voorwerpen, landschappen of gebeurtenissen weergeven. Ze kunnen digitaal worden opgeslagen en verwerkt of in fysieke vorm worden afgedrukt. Afhankelijk van het doel kunnen foto's dienen als herinnering, documentatie, communicatiemiddel, kunstwerk of bron van informatie.",
    },
    "ws5": {
        "wie": "Een fotograaf of andere persoon die een foto maakt of gebruikt.",
        "wat": "Een afbeelding die een onderwerp of situatie visueel vastlegt.",
        "wanneer": "Wanneer een moment, onderwerp of situatie in beeld wordt vastgelegd.",
        "waar": "Bijvoorbeeld thuis, buiten, op evenementen, in documenten of online.",
        "waarom": "Om iets vast te leggen, te herinneren, te communiceren, te documenteren of te informeren.",
        "hoe": "Door een camera of smartphone te gebruiken en de gemaakte afbeelding digitaal of op papier te bewaren.",
    },
    "core_tags": [
        "foto's", "foto", "afbeelding", "fotografie", "camera",
        "beeld", "digitaal", "afdruk", "documentatie", "herinnering",
    ],
    "topic": "media",
}


def _backup(p: Path, tag: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bak = p.with_suffix(p.suffix + f".bak_{tag}_{ts}")
    shutil.copy2(p, bak)
    print(f"  backup: {bak.name}")


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    print("Backups…")
    for p in (WETEN, INBOX, INDEX):
        _backup(p, "fotos_update")

    weten = load_json(WETEN, default={"kaarten": []})
    inbox = load_json(INBOX, default={"kaarten": []})
    index = load_json(INDEX, default={"entries": {}})

    # 1) Update kaart in Weten
    updated = False
    for k in weten.get("kaarten", []):
        if k.get("id") == TARGET_ID:
            k["lagen"] = dict(NEW_CONTENT["lagen"])
            k["ws5"] = dict(NEW_CONTENT["ws5"])
            # tags: merge core + bestaande extras (behoud zoekbaarheid)
            existing = set(k.get("tags") or [])
            merged = list(existing | set(NEW_CONTENT["core_tags"]))
            k["tags"] = sorted(merged)
            if not k.get("topic"):
                k["topic"] = NEW_CONTENT["topic"]
            fn = k.setdefault("footnote", {})
            fn["updated_at"] = now
            fn["updated_by"] = "willem_via_e1"
            fn["update_reason"] = "user_provided_richer_version"
            updated = True
            print(f"[UPDATE] {TARGET_ID} Foto's — lagen + ws5 + tags overschreven")
            break

    # 2) Verwijder ghost uit inbox
    before = len(inbox.get("kaarten", []))
    inbox["kaarten"] = [k for k in inbox.get("kaarten", []) if k.get("id") != GHOST_ID]
    removed = before - len(inbox.get("kaarten", []))
    print(f"[GHOST] {GHOST_ID} uit inbox verwijderd: {removed}")

    # 3) Index bijwerken
    entries = index.setdefault("entries", {})
    entries["foto's"] = {
        "kaart_id": TARGET_ID,
        "lade": "weten",
        "has_lagen": ["laag1", "laag2", "laag3", "laag4"],
        "last_updated": now,
    }
    # unicode-apostrof-alias eventueel opruimen als die apart in de index staat
    if "foto’s" in entries:
        entries.pop("foto’s")
        print("[INDEX] alias 'foto’s' (unicode-apostrof) verwijderd")
    index["rebuilt_at"] = now
    index["rebuilt_by"] = "e1_fotos_update"

    save_json(WETEN, weten)
    save_json(INBOX, inbox)
    save_json(INDEX, index)
    print("Klaar." if updated else "!! target-kaart niet gevonden!")


if __name__ == "__main__":
    main()
