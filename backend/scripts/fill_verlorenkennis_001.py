"""
v6_kbv2_fill_001 — Vul 3 lege inbox-kaarten met door Willem aangeleverde lagen+5W+tags
en verplaats ze naar de juiste lade.

Input: hardcoded uit /tmp/verlorenkennis.txt parse
Output: kaarten verplaatst van knowledge_inbox.json → respectievelijke lade
"""
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).parent.parent / "data" / "knowledge" / "v2"
NOW = datetime.now(timezone.utc).isoformat()

# Definitieve invulling op basis van /tmp/verlorenkennis.txt
CARDS = [
    {
        "begrip": "indruk",
        "lade_target": "voelen",
        "lagen": {
            "laag1": "Een indruk is het beeld, gevoel of oordeel dat ontstaat door een waarneming of ervaring.",
            "laag2": "Een indruk ontstaat wanneer iemand iets ziet, hoort, ervaart of meemaakt en daar betekenis aan geeft.",
            "laag3": "Een indruk is de eerste of algemene beleving die iemand krijgt van een persoon, object, gebeurtenis of situatie. Deze ontstaat door waarneming, communicatie en eerdere ervaringen. Een indruk kan positief, negatief of neutraal zijn en kan veranderen wanneer nieuwe informatie beschikbaar komt.",
            "laag4": "Binnen Spark is een indruk een mentale en emotionele interpretatie van waarnemingen. Indrukken helpen mensen en AI om situaties snel te beoordelen, maar zijn niet altijd volledig of juist. Ze vormen vaak de basis voor verwachtingen, beslissingen en vervolginteracties."
        },
        "ws5": {
            "wie": "Mensen en AI-systemen.",
            "wat": "Een beeld, gevoel of oordeel dat ontstaat door een waarneming of ervaring.",
            "wanneer": "Wanneer iets wordt gezien, gehoord of ervaren.",
            "waar": "In sociale situaties, communicatie en dagelijkse ervaringen.",
            "waarom": "Om een situatie, persoon of object snel te beoordelen en te begrijpen.",
            "hoe": "Door waarnemingen te verwerken en deze te combineren met kennis, ervaringen en context."
        },
        "tags": ["indruk", "waarneming", "beleving", "oordeel", "ervaring", "interpretatie", "observatie", "communicatie", "sociaal", "emotie", "neutraal"]
    },
    {
        "begrip": "verdeling",
        "lade_target": "doen",
        "lagen": {
            "laag1": "Een verdeling is het verdelen van iets over meerdere personen, plaatsen of groepen.",
            "laag2": "Een verdeling zorgt ervoor dat middelen, taken of hoeveelheden volgens een bepaalde manier worden verdeeld.",
            "laag3": "Een verdeling is het proces waarbij iets wordt opgesplitst en toegewezen aan verschillende personen, groepen, locaties of onderdelen. Dit kan gaan om goederen, geld, taken, tijd, informatie of ruimte. Een verdeling kan gelijk, ongelijk of volgens vooraf bepaalde regels plaatsvinden.",
            "laag4": "Binnen Spark is een verdeling een actie waarbij objecten, gegevens, taken of middelen worden toegewezen aan meerdere bestemmingen. Verdelingen worden gebruikt om processen te organiseren, middelen efficiënt in te zetten en samenwerking mogelijk te maken."
        },
        "ws5": {
            "wie": "Mensen, organisaties en systemen.",
            "wat": "Het verdelen van middelen, taken, informatie of hoeveelheden.",
            "wanneer": "Wanneer iets over meerdere ontvangers of onderdelen moet worden verdeeld.",
            "waar": "In organisaties, logistiek, netwerken, huishoudens en digitale systemen.",
            "waarom": "Om middelen eerlijk, efficiënt of doelgericht toe te wijzen.",
            "hoe": "Door iets op te splitsen en volgens regels of keuzes toe te wijzen."
        },
        "tags": ["verdeling", "verdelen", "toewijzen", "organisatie", "middelen", "taken", "proces", "systeem", "samenwerking", "emotie", "neutraal"]
    },
    {
        "begrip": "reinigen",
        "lade_target": "doen",
        "lagen": {
            "laag1": "Reinigen is het verwijderen van vuil, verontreiniging of ongewenste stoffen.",
            "laag2": "Reinigen wordt gedaan om mensen, objecten, materialen of omgevingen schoon en veilig te maken.",
            "laag3": "Reinigen is de handeling waarbij vuil, stof, bacteriën, vet of andere ongewenste stoffen worden verwijderd van een persoon, object, oppervlak of ruimte. Dit kan gebeuren met water, schoonmaakmiddelen, lucht, warmte of andere reinigingstechnieken. Reinigen draagt bij aan hygiëne, onderhoud en veiligheid.",
            "laag4": "Binnen Spark is reinigen een fysieke actie waarbij ongewenste stoffen worden verwijderd om de kwaliteit, hygiëne of werking van een persoon, object of systeem te verbeteren. Reinigen wordt toegepast in huishoudens, industrie, gezondheidszorg en digitale systemen, waar ook gegevens of bestanden kunnen worden 'opgeschoond'."
        },
        "ws5": {
            "wie": "Mensen, schoonmakers, organisaties en systemen.",
            "wat": "Het verwijderen van vuil of verontreiniging.",
            "wanneer": "Wanneer iets schoongemaakt of onderhouden moet worden.",
            "waar": "In woningen, bedrijven, ziekenhuizen, openbare ruimtes en digitale systemen.",
            "waarom": "Om hygiëne, veiligheid, kwaliteit of een goede werking te behouden.",
            "hoe": "Door vuil of ongewenste stoffen te verwijderen met geschikte middelen of technieken."
        },
        "tags": ["reinigen", "schoonmaken", "hygiëne", "onderhoud", "vuil", "desinfecteren", "verzorging", "proces", "systeem", "emotie", "neutraal"]
    }
]


def main():
    inbox_fp = BASE / "knowledge_inbox.json"
    inbox = json.loads(inbox_fp.read_text())
    
    moved = []
    for spec in CARDS:
        begrip_target = spec["begrip"]
        # vind in inbox
        idx = next((i for i, k in enumerate(inbox.get("kaarten", []))
                    if (k.get("begrip") or "").lower().strip() == begrip_target.lower()), None)
        if idx is None:
            print(f"  ⚠️  {begrip_target}: niet gevonden in inbox — sla over")
            continue
        kaart = inbox["kaarten"].pop(idx)
        
        # Update kaart
        kaart["lagen"] = spec["lagen"]
        kaart["ws5"] = spec["ws5"]
        kaart["tags"] = spec["tags"]
        kaart["lade"] = spec["lade_target"]
        kaart["updated_at"] = NOW
        kaart["updated_by"] = "user-001"
        kaart.setdefault("history", []).append({
            "ts": NOW,
            "actie": "filled_from_doc",
            "bron": "verlorenkennis.txt",
            "lade": spec["lade_target"]
        })
        # remove inbox-only fields
        kaart.pop("inbox_reden", None)
        
        # toevoegen aan target-lade
        lade_fp = BASE / f"knowledge_v2_{spec['lade_target']}.json"
        lade_data = json.loads(lade_fp.read_text())
        lade_data.setdefault("kaarten", []).append(kaart)
        lade_fp.write_text(json.dumps(lade_data, indent=2, ensure_ascii=False))
        moved.append((begrip_target, spec["lade_target"], kaart["id"]))
        print(f"  ✅ {begrip_target} → {spec['lade_target']} (id={kaart['id']})")
    
    # save inbox
    inbox_fp.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))
    
    print(f"\nTotaal verplaatst: {len(moved)}")
    print(f"Inbox nu: {len(inbox.get('kaarten', []))} kaarten")


if __name__ == "__main__":
    main()
