"""v6_kbv2_fill_002 — vul 'meester' + 'leerlingen' uit verlorenkennis.txt batch 2"""
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).parent.parent / "data" / "knowledge" / "v2"
NOW = datetime.now(timezone.utc).isoformat()

CARDS = [
    {
        "begrip": "meester",
        "lade_target": "weten",
        "lagen": {
            "laag1": "Een meester is een mannelijke leerkracht die lesgeeft aan leerlingen.",
            "laag2": "Een meester begeleidt leerlingen bij het leren, de ontwikkeling en het onderwijs.",
            "laag3": "Een meester is een mannelijke leerkracht die lesgeeft op een school, meestal in het basisonderwijs. Hij legt lesstof uit, begeleidt leerlingen, beoordeelt hun voortgang en helpt bij hun persoonlijke en sociale ontwikkeling. Een meester zorgt voor een veilige leeromgeving en ondersteunt leerlingen bij het ontwikkelen van kennis en vaardigheden.",
            "laag4": "Een meester vervult een belangrijke rol binnen het onderwijs. Naast het overdragen van kennis helpt hij leerlingen samenwerken, zelfstandig denken en verantwoordelijkheid nemen. Afhankelijk van de school kan een meester verschillende vakken geven en samenwerken met collega's, ouders en andere onderwijsprofessionals."
        },
        "ws5": {
            "wie": "Meesters, leerlingen, ouders en collega's.",
            "wat": "Een mannelijke leerkracht die onderwijs en begeleiding geeft.",
            "wanneer": "Tijdens lessen en andere onderwijsactiviteiten.",
            "waar": "Op scholen, vooral in het basisonderwijs.",
            "waarom": "Om leerlingen kennis, vaardigheden en ontwikkeling mee te geven.",
            "hoe": "Door les te geven, uitleg te geven, opdrachten te begeleiden en de voortgang van leerlingen te volgen."
        },
        "tags": ["meester", "leerkracht", "docent", "onderwijs", "school", "basisonderwijs", "leerling", "lesgeven", "persoon", "ontwikkeling", "kennis", "leren", "emotie", "neutraal"]
    },
    {
        "begrip": "leerlingen",
        "lade_target": "weten",
        "lagen": {
            "laag1": "Leerlingen zijn mensen die onderwijs volgen om te leren.",
            "laag2": "Leerlingen ontwikkelen kennis, vaardigheden en persoonlijke groei door onderwijs.",
            "laag3": "Een leerling is iemand die onderwijs volgt op een school of andere onderwijsinstelling. Leerlingen nemen deel aan lessen, maken opdrachten, oefenen vaardigheden en worden begeleid door leraren of docenten. Afhankelijk van hun leeftijd en niveau volgen zij verschillende vakken en leren zij zowel theoretische als praktische kennis.",
            "laag4": "Leerlingen vormen het middelpunt van het onderwijsproces. Zij ontwikkelen niet alleen kennis, maar ook sociale vaardigheden, zelfstandigheid, samenwerking en kritisch denken. Hun ontwikkeling wordt ondersteund door leraren, ouders en de leeromgeving."
        },
        "ws5": {
            "wie": "Kinderen, jongeren en volwassenen die onderwijs volgen.",
            "wat": "Mensen die leren binnen een onderwijsomgeving.",
            "wanneer": "Tijdens het volgen van onderwijs of een opleiding.",
            "waar": "Op scholen, opleidingen en andere onderwijsinstellingen.",
            "waarom": "Om kennis, vaardigheden en persoonlijke ontwikkeling op te bouwen.",
            "hoe": "Door lessen te volgen, opdrachten te maken, te oefenen en begeleiding te ontvangen."
        },
        "tags": ["leerling", "leerlingen", "onderwijs", "school", "leren", "ontwikkeling", "kennis", "docent", "leerkracht", "opleiding", "persoon", "educatie", "emotie", "neutraal"]
    }
]


def main():
    inbox_fp = BASE / "knowledge_inbox.json"
    inbox = json.loads(inbox_fp.read_text())
    moved = []
    for spec in CARDS:
        idx = next((i for i, k in enumerate(inbox.get("kaarten", []))
                    if (k.get("begrip") or "").lower().strip() == spec["begrip"]), None)
        if idx is None:
            print(f"  ⚠️  {spec['begrip']}: niet in inbox")
            continue
        kaart = inbox["kaarten"].pop(idx)
        kaart["lagen"] = spec["lagen"]
        kaart["ws5"] = spec["ws5"]
        kaart["tags"] = spec["tags"]
        kaart["lade"] = spec["lade_target"]
        kaart["updated_at"] = NOW
        kaart["updated_by"] = "user-001"
        kaart.setdefault("history", []).append({
            "ts": NOW, "actie": "filled_from_doc", "bron": "verlorenkennis.txt (batch 2)", "lade": spec["lade_target"]
        })
        kaart.pop("inbox_reden", None)
        lade_fp = BASE / f"knowledge_v2_{spec['lade_target']}.json"
        lade_data = json.loads(lade_fp.read_text())
        lade_data.setdefault("kaarten", []).append(kaart)
        lade_fp.write_text(json.dumps(lade_data, indent=2, ensure_ascii=False))
        moved.append((spec["begrip"], spec["lade_target"]))
        print(f"  ✅ {spec['begrip']} → {spec['lade_target']} (id={kaart['id']})")
    inbox_fp.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))
    print(f"\nVerplaatst: {len(moved)} · Inbox nu: {len(inbox.get('kaarten', []))}")


if __name__ == "__main__":
    main()
