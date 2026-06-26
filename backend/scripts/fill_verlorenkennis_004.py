"""v6_kbv2_fill_004 — vul 10 kaarten uit verlorenkennis.txt batch 4"""
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).parent.parent / "data" / "knowledge" / "v2"
NOW = datetime.now(timezone.utc).isoformat()

CARDS = [
    {"begrip": "bewondering", "lade_target": "voelen",
     "lagen": {"laag1": "Bewondering is een gevoel van respect of waardering voor iemand of iets.",
               "laag2": "Bewondering ontstaat wanneer iemand positieve eigenschappen, prestaties of schoonheid herkent.",
               "laag3": "Bewondering is een positieve emotie waarbij iemand respect, waardering of ontzag voelt voor een persoon, dier, object of gebeurtenis. Dit gevoel kan ontstaan door talent, moed, vriendelijkheid, schoonheid, kennis of bijzondere prestaties. Bewondering kan mensen inspireren om zelf te leren, te groeien of doelen na te streven.",
               "laag4": "Bewondering speelt een belangrijke rol in motivatie, leren en sociale relaties. Binnen Spark is bewondering een positieve emotionele toestand die kan ontstaan door observatie of ervaring en invloed heeft op aandacht, waardering en gedrag."},
     "ws5": {"wie": "Mensen.", "wat": "Een gevoel van respect, waardering of ontzag.",
             "wanneer": "Wanneer iemand iets bijzonders, moois of indrukwekkends ervaart.",
             "waar": "In sociale situaties, de natuur, kunst, sport, wetenschap en het dagelijks leven.",
             "waarom": "Omdat iemand positieve eigenschappen of prestaties herkent.",
             "hoe": "Door iets waar te nemen dat indruk maakt of inspireert."},
     "tags": ["bewondering","waardering","respect","ontzag","emotie","blij","gevoel","inspiratie","motivatie","sociaal"]},

    {"begrip": "bevoegdheid", "lade_target": "weten",
     "lagen": {"laag1": "Bevoegdheid is het officiële recht of de toestemming om een bepaalde taak of beslissing uit te voeren.",
               "laag2": "Bevoegdheden bepalen wie verantwoordelijk is voor bepaalde handelingen of besluiten.",
               "laag3": "Een bevoegdheid is een recht, toestemming of wettelijke bevoegdheid die aan een persoon, functie of organisatie is toegekend. Alleen iemand met de juiste bevoegdheid mag bepaalde handelingen uitvoeren of beslissingen nemen. Bevoegdheden komen voor in onder andere onderwijs, zorg, overheid, rechtspraak en bedrijven.",
               "laag4": "Bevoegdheden zorgen voor duidelijke verantwoordelijkheden, veiligheid en een goede taakverdeling. Binnen Spark is een bevoegdheid een eigenschap of autorisatie die bepaalt welke acties, beslissingen of functies een persoon of systeem mag uitvoeren."},
     "ws5": {"wie": "Personen, organisaties en systemen.", "wat": "Het recht of de toestemming om iets te doen.",
             "wanneer": "Wanneer een taak, beslissing of verantwoordelijkheid moet worden uitgevoerd.",
             "waar": "Binnen organisaties, overheden, bedrijven, onderwijs en digitale systemen.",
             "waarom": "Om verantwoordelijkheden, veiligheid en bevoegdheden duidelijk vast te leggen.",
             "hoe": "Door regels, wetgeving, afspraken of autorisaties toe te kennen."},
     "tags": ["bevoegdheid","autorisatie","toestemming","verantwoordelijkheid","recht","regels","organisatie","systeem","functie","besluit","emotie","neutraal"]},

    {"begrip": "tempo", "lade_target": "weten",
     "lagen": {"laag1": "Tempo is de snelheid waarmee iets gebeurt of wordt uitgevoerd.",
               "laag2": "Tempo bepaalt hoe snel een proces, beweging of activiteit verloopt.",
               "laag3": "Tempo geeft aan hoe snel of langzaam een handeling, proces of gebeurtenis plaatsvindt. Het begrip wordt gebruikt in muziek, sport, verkeer, werk en het dagelijks leven. Een hoog tempo betekent dat iets snel verloopt, terwijl een laag tempo juist wijst op een langzamere uitvoering.",
               "laag4": "Tempo beïnvloedt prestaties, efficiëntie en belasting. Het juiste tempo hangt af van de situatie en het doel. Binnen Spark is tempo een eigenschap van processen en activiteiten die aangeeft met welke snelheid iets zich ontwikkelt of wordt uitgevoerd."},
     "ws5": {"wie": "Mensen, dieren, machines en systemen.", "wat": "De snelheid waarmee iets gebeurt of wordt uitgevoerd.",
             "wanneer": "Tijdens een activiteit, proces of beweging.",
             "waar": "In muziek, sport, verkeer, werk en dagelijkse situaties.",
             "waarom": "Om de snelheid van een proces of handeling te beschrijven of aan te passen.",
             "hoe": "Door sneller of langzamer te bewegen, werken of een proces te laten verlopen."},
     "tags": ["tempo","snelheid","proces","beweging","activiteit","tijd","ritme","prestatie","systeem","eigenschap","emotie","neutraal"]},

    {"begrip": "vriendelijkheid", "lade_target": "voelen",
     "lagen": {"laag1": "Vriendelijkheid is de bereidheid om aardig, behulpzaam en respectvol met anderen om te gaan.",
               "laag2": "Vriendelijkheid zorgt voor positieve sociale interacties en een prettige omgang tussen mensen.",
               "laag3": "Vriendelijkheid is een positieve houding waarbij iemand rekening houdt met anderen en zich behulpzaam, beleefd en respectvol opstelt. Vriendelijke mensen tonen vaak begrip, aandacht en geduld. Vriendelijkheid kan worden uitgedrukt door woorden, gedrag of kleine gebaren en draagt bij aan vertrouwen en samenwerking.",
               "laag4": "Vriendelijkheid versterkt sociale relaties en bevordert een veilige en prettige omgeving. Binnen Spark is vriendelijkheid een positieve emotionele eigenschap die invloed heeft op communicatie, samenwerking en het welzijn van anderen."},
     "ws5": {"wie": "Mensen.", "wat": "Een positieve houding van aardig, behulpzaam en respectvol gedrag.",
             "wanneer": "Tijdens sociale interacties en samenwerking.",
             "waar": "Thuis, op school, op het werk en in het dagelijks leven.",
             "waarom": "Om prettig met anderen om te gaan en positieve relaties op te bouwen.",
             "hoe": "Door respect, aandacht, behulpzaamheid en beleefdheid te tonen."},
     "tags": ["vriendelijkheid","aardig","behulpzaam","respect","sociaal","samenwerking","communicatie","gedrag","houding","emotie","blij"]},

    {"begrip": "zicht", "lade_target": "weten",
     "lagen": {"laag1": "Zicht is het vermogen om met de ogen waar te nemen.",
               "laag2": "Zicht maakt het mogelijk om de omgeving, objecten en bewegingen te zien.",
               "laag3": "Zicht is het vermogen om licht, vormen, kleuren en bewegingen met de ogen waar te nemen en door de hersenen te verwerken. Goed zicht helpt mensen en dieren bij oriëntatie, communicatie en het uitvoeren van dagelijkse activiteiten. De kwaliteit van het zicht kan worden beïnvloed door licht, afstand, gezondheid of hulpmiddelen zoals een bril of contactlenzen.",
               "laag4": "Zicht is één van de belangrijkste zintuigen voor het verzamelen van informatie uit de omgeving. Binnen Spark is zicht een vorm van waarneming waarmee een gebruiker of systeem visuele informatie ontvangt en gebruikt voor herkenning, interpretatie en besluitvorming."},
     "ws5": {"wie": "Mensen, dieren en visuele systemen.", "wat": "Het vermogen om visuele informatie waar te nemen.",
             "wanneer": "Wanneer er voldoende licht en een werkend gezichtsvermogen aanwezig is.",
             "waar": "Overal waar visuele waarneming mogelijk is.",
             "waarom": "Om de omgeving te herkennen, te begrijpen en veilig te kunnen handelen.",
             "hoe": "Doordat licht via de ogen wordt opgevangen en door de hersenen wordt verwerkt."},
     "tags": ["zicht","zien","waarneming","zintuig","ogen","informatie","omgeving","observatie","herkenning","emotie","neutraal"]},

    {"begrip": "stroming", "lade_target": "weten",
     "lagen": {"laag1": "Een stroming is een beweging van een vloeistof, gas of groep in een bepaalde richting.",
               "laag2": "Stromingen verplaatsen water, lucht, energie, mensen of ideeën van de ene plaats naar de andere.",
               "laag3": "Een stroming is een voortdurende beweging in een bepaalde richting. In de natuur komt een stroming voor in water, lucht of magma. In de samenleving kan een stroming ook een groep mensen of ideeën zijn met dezelfde overtuigingen of doelen, zoals een politieke, religieuze of artistieke stroming. De betekenis hangt af van de context, maar draait altijd om richting en beweging.",
               "laag4": "Stromingen beïnvloeden hun omgeving door energie, materialen of ideeën te verplaatsen. Binnen Spark is een stroming een proces waarbij iets zich door een systeem beweegt en daardoor verandering of interactie veroorzaakt."},
     "ws5": {"wie": "Water, lucht, mensen, energie of ideeën.", "wat": "Een beweging in een bepaalde richting.",
             "wanneer": "Wanneer iets zich voortdurend verplaatst.",
             "waar": "In rivieren, zeeën, de atmosfeer, leidingen of de samenleving.",
             "waarom": "Door natuurkundige krachten of gedeelde overtuigingen.",
             "hoe": "Door een voortdurende verplaatsing in een bepaalde richting."},
     "tags": ["stroming","beweging","richting","water","lucht","energie","proces","systeem","natuur","samenleving","emotie","neutraal"]},

    {"begrip": "uitrusting", "lade_target": "weten",
     "lagen": {"laag1": "Uitrusting is de verzameling van hulpmiddelen, kleding en materialen die nodig zijn voor een bepaalde taak of activiteit.",
               "laag2": "Een uitrusting helpt mensen om veilig, efficiënt of comfortabel een activiteit uit te voeren.",
               "laag3": "Een uitrusting bestaat uit alle voorwerpen die iemand meeneemt of draagt voor een specifieke situatie. Dit kunnen gereedschappen, beschermende kleding, wapens, medische materialen, kampeeruitrusting of sportartikelen zijn. De inhoud van een uitrusting hangt af van het doel en de omgeving waarin deze wordt gebruikt.",
               "laag4": "Een goede uitrusting vergroot veiligheid, prestaties en voorbereiding. Binnen Spark is een uitrusting een verzameling objecten die aan een persoon, rol of systeem gekoppeld zijn om bepaalde taken of functies mogelijk te maken."},
     "ws5": {"wie": "Mensen, hulpdiensten, militairen, sporters en reizigers.", "wat": "Een verzameling hulpmiddelen, kleding en materialen.",
             "wanneer": "Voor of tijdens een taak, activiteit of missie.",
             "waar": "Op het werk, in de natuur, tijdens sport, reizen of noodsituaties.",
             "waarom": "Om goed voorbereid, veilig en effectief te kunnen handelen.",
             "hoe": "Door de benodigde materialen te verzamelen, mee te nemen en te gebruiken."},
     "tags": ["uitrusting","materiaal","gereedschap","hulpmiddel","bescherming","voorbereiding","object","taak","veiligheid","systeem","emotie","neutraal"]},

    {"begrip": "slaap", "lade_target": "voelen",
     "lagen": {"laag1": "Slaap is een natuurlijke toestand van rust waarin lichaam en hersenen herstellen.",
               "laag2": "Tijdens de slaap herstellen lichaam en geest zich en worden energie en informatie verwerkt.",
               "laag3": "Slaap is een terugkerende biologische toestand waarin het bewustzijn afneemt en het lichaam tot rust komt. Tijdens de slaap herstellen spieren en organen zich, worden herinneringen verwerkt en krijgt het lichaam nieuwe energie. Voldoende slaap is belangrijk voor gezondheid, concentratie, leren en emotioneel welzijn.",
               "laag4": "Slaap bestaat uit verschillende fasen, waaronder lichte slaap, diepe slaap en droomslaap (REM-slaap). Binnen Spark is slaap een biologische toestand die herstel, energie, geheugenverwerking en emotionele balans ondersteunt."},
     "ws5": {"wie": "Mensen en dieren.", "wat": "Een natuurlijke toestand van rust en herstel.",
             "wanneer": "Meestal dagelijks volgens een slaapritme.",
             "waar": "Op een veilige en geschikte rustplaats.",
             "waarom": "Om lichaam en geest te laten herstellen en energie aan te vullen.",
             "hoe": "Door in slaap te vallen en verschillende slaapfasen te doorlopen."},
     "tags": ["slaap","rust","herstel","gezondheid","energie","lichaam","hersenen","biologisch","ritme","welzijn","emotie","neutraal"]},

    {"begrip": "service", "lade_target": "weten",
     "lagen": {"laag1": "Service is het verlenen van hulp, ondersteuning of dienstverlening aan anderen.",
               "laag2": "Service zorgt ervoor dat mensen of organisaties worden geholpen bij het gebruiken van een product of dienst.",
               "laag3": "Service is het geheel van handelingen waarmee iemand ondersteuning, hulp of dienstverlening biedt aan een klant, gebruiker of andere persoon. Goede service bestaat uit behulpzaamheid, duidelijke communicatie, betrouwbaarheid en het oplossen van vragen of problemen. Service komt voor in winkels, bedrijven, zorg, horeca, overheid en digitale systemen.",
               "laag4": "Service draagt bij aan tevredenheid, vertrouwen en een goede samenwerking. Binnen Spark is service een proces waarbij een persoon of systeem ondersteuning biedt om een behoefte te vervullen, een probleem op te lossen of een taak gemakkelijker te maken."},
     "ws5": {"wie": "Medewerkers, organisaties, systemen en klanten.", "wat": "Het verlenen van hulp of dienstverlening.",
             "wanneer": "Wanneer ondersteuning, informatie of hulp nodig is.",
             "waar": "Bij bedrijven, organisaties, winkels, zorginstellingen en digitale diensten.",
             "waarom": "Om gebruikers of klanten te helpen en hun ervaring te verbeteren.",
             "hoe": "Door vragen te beantwoorden, problemen op te lossen en ondersteuning te bieden."},
     "tags": ["service","dienstverlening","ondersteuning","hulp","communicatie","samenwerking","klant","organisatie","proces","systeem","emotie","neutraal"]},

    {"begrip": "enthousiasme", "lade_target": "voelen",
     "lagen": {"laag1": "Enthousiasme is een gevoel van sterke interesse, energie en motivatie.",
               "laag2": "Enthousiasme zorgt ervoor dat mensen met plezier en inzet ergens aan beginnen of mee doorgaan.",
               "laag3": "Enthousiasme is een positieve emotie waarbij iemand veel belangstelling, energie of opwinding voelt voor een activiteit, idee of doel. Enthousiaste mensen tonen vaak initiatief, betrokkenheid en doorzettingsvermogen. Enthousiasme kan aanstekelijk werken en anderen motiveren om mee te doen.",
               "laag4": "Enthousiasme bevordert motivatie, creativiteit en samenwerking. Binnen Spark is enthousiasme een positieve emotionele toestand die invloed heeft op gedrag, communicatie, leren en het behalen van doelen."},
     "ws5": {"wie": "Mensen.", "wat": "Een gevoel van sterke interesse, energie en motivatie.",
             "wanneer": "Wanneer iemand ergens veel plezier of interesse in heeft.",
             "waar": "Op school, op het werk, tijdens hobby's, sport en in het dagelijks leven.",
             "waarom": "Omdat een activiteit, doel of onderwerp inspireert of motiveert.",
             "hoe": "Door positieve ervaringen, interesse, succes of inspiratie."},
     "tags": ["enthousiasme","motivatie","energie","interesse","betrokkenheid","gedrag","gevoel","inspiratie","positief","emotie","blij"]},
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
        kaart.setdefault("history", []).append({"ts": NOW, "actie": "filled_from_doc", "bron": "verlorenkennis.txt (batch 4)", "lade": spec["lade_target"]})
        kaart.pop("inbox_reden", None)
        lade_fp = BASE / f"knowledge_v2_{spec['lade_target']}.json"
        lade_data = json.loads(lade_fp.read_text())
        lade_data.setdefault("kaarten", []).append(kaart)
        lade_fp.write_text(json.dumps(lade_data, indent=2, ensure_ascii=False))
        moved.append((spec["begrip"], spec["lade_target"]))
        print(f"  ✅ {spec['begrip']:16s} → {spec['lade_target']}")
    inbox_fp.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))
    print(f"\nVerplaatst: {len(moved)} · Inbox nu: {len(inbox.get('kaarten', []))}")


if __name__ == "__main__":
    main()
