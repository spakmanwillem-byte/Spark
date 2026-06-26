"""v6_kbv2_fill_005 — vul 15 kaarten uit verlorenkennis.txt batch 5.
Bijzonder: 'rijzen' bestaat al in WETEN; wordt overschreven en verplaatst naar DOEN."""
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).parent.parent / "data" / "knowledge" / "v2"
NOW = datetime.now(timezone.utc).isoformat()

CARDS = [
    {"begrip": "reizen", "lade_target": "doen",
     "lagen": {"laag1": "Reizen is het verplaatsen van de ene plaats naar een andere.",
               "laag2": "Mensen reizen om een bestemming te bereiken, bijvoorbeeld voor werk, vakantie of bezoek.",
               "laag3": "Reizen is de handeling waarbij iemand zich verplaatst tussen verschillende locaties. Dit kan te voet of met vervoermiddelen zoals een auto, fiets, trein, vliegtuig of schip. Mensen reizen om uiteenlopende redenen, zoals werk, onderwijs, vakantie, familiebezoek of handel.",
               "laag4": "Reizen verbindt mensen, plaatsen en culturen en speelt een belangrijke rol in mobiliteit en economie. Binnen Spark is reizen een activiteit waarbij een persoon of groep zich doelgericht verplaatst van een vertrekpunt naar een bestemming."},
     "ws5": {"wie": "Mensen en reizigers.", "wat": "Het verplaatsen van de ene plaats naar een andere.",
             "wanneer": "Wanneer iemand een andere bestemming wil bereiken.",
             "waar": "Tussen steden, landen of andere locaties.",
             "waarom": "Voor werk, studie, vakantie, bezoek of andere doelen.",
             "hoe": "Te voet of met een vervoermiddel zoals een fiets, auto, trein, schip of vliegtuig."},
     "tags": ["reizen","verplaatsen","vervoer","mobiliteit","bestemming","route","activiteit","beweging","transport","emotie","neutraal"]},

    {"begrip": "rijzen", "lade_target": "doen", "overwrite": True,
     "lagen": {"laag1": "Rijzen is het groter worden van deeg door de vorming van gas.",
               "laag2": "Tijdens het rijzen wordt deeg luchtiger en neemt het in volume toe.",
               "laag3": "Rijzen is het proces waarbij deeg groter en luchtiger wordt. Dit gebeurt meestal doordat gist suikers omzet in koolstofdioxide. De gasbelletjes blijven in het deeg zitten, waardoor het uitzet. Ook andere rijsmiddelen, zoals bakpoeder of zuurdesem, kunnen ervoor zorgen dat deeg rijst.",
               "laag4": "Rijzen is een belangrijk onderdeel van het bakken van brood, pizza en andere deegproducten. Binnen Spark is rijzen een biologisch of chemisch proces waarbij een materiaal in volume toeneemt door de vorming van gas."},
     "ws5": {"wie": "Bakkers, koks en thuisbakkers.", "wat": "Het groter en luchtiger worden van deeg.",
             "wanneer": "Na het mengen van het deeg en vóór het bakken.",
             "waar": "In bakkerijen, keukens en andere plaatsen waar deeg wordt bereid.",
             "waarom": "Om een luchtige structuur en betere smaak te krijgen.",
             "hoe": "Door gist, zuurdesem of een ander rijsmiddel dat gas vormt waardoor het deeg uitzet."},
     "tags": ["rijzen","deeg","bakken","gist","zuurdesem","bakpoeder","gas","volume","proces","voedsel","emotie","neutraal"]},

    {"begrip": "scheiding", "lade_target": "weten",
     "lagen": {"laag1": "Een scheiding is het uit elkaar gaan of verdelen van mensen, materialen of onderdelen.",
               "laag2": "Een scheiding zorgt ervoor dat één geheel wordt opgesplitst in twee of meer afzonderlijke delen.",
               "laag3": "Een scheiding is het proces of de toestand waarbij een verbinding wordt verbroken of een geheel wordt verdeeld. Dit kan gaan om een relatie tussen mensen, een juridische echtscheiding, het scheiden van afval, het scheiden van stoffen in de natuurkunde of het verdelen van ruimtes door een wand of grens. De betekenis hangt af van de context, maar draait steeds om het uit elkaar brengen van een geheel.",
               "laag4": "Scheidingen komen voor in sociale, juridische, technische en natuurkundige systemen. Binnen Spark is een scheiding een verandering waarbij bestaande verbindingen of onderdelen worden losgemaakt, waardoor nieuwe afzonderlijke eenheden ontstaan."},
     "ws5": {"wie": "Mensen, organisaties, materialen of systemen.", "wat": "Het uit elkaar gaan of verdelen van een geheel.",
             "wanneer": "Wanneer een verbinding wordt verbroken of onderdelen worden gescheiden.",
             "waar": "In relaties, huishoudens, industrie, wetenschap en de natuur.",
             "waarom": "Om onderdelen van elkaar te onderscheiden, te verdelen of een relatie te beëindigen.",
             "hoe": "Door een verbinding te verbreken of een geheel op te splitsen in afzonderlijke delen."},
     "tags": ["scheiding","verdeling","verbinding","relatie","proces","verandering","systeem","structuur","juridisch","emotie","neutraal"]},

    {"begrip": "verdelen", "lade_target": "doen",
     "lagen": {"laag1": "Verdelen is het opsplitsen van iets in meerdere delen.",
               "laag2": "Verdelen wordt gebruikt om middelen, taken, ruimte of hoeveelheden over meerdere personen of onderdelen te verspreiden.",
               "laag3": "Verdelen is de handeling waarbij een geheel wordt opgesplitst en over meerdere personen, objecten of plaatsen wordt verspreid. Dit kan gaan om het verdelen van voedsel, geld, werk, tijd, ruimte of informatie. Het doel van verdelen is vaak om iets eerlijk, efficiënt of doelgericht toe te wijzen.",
               "laag4": "Verdelen is een fundamenteel proces in samenwerking, logistiek, economie en organisatie. Binnen Spark is verdelen een actie waarbij een hoeveelheid of verzameling systematisch wordt toegewezen aan meerdere ontvangers of onderdelen volgens bepaalde regels of keuzes."},
     "ws5": {"wie": "Mensen, organisaties en systemen.", "wat": "Het opsplitsen en toewijzen van een geheel.",
             "wanneer": "Wanneer iets over meerdere personen of onderdelen moet worden verdeeld.",
             "waar": "In huishoudens, bedrijven, scholen, logistiek en digitale systemen.",
             "waarom": "Om middelen, taken of informatie eerlijk of efficiënt te verdelen.",
             "hoe": "Door een geheel op te splitsen en de delen toe te wijzen aan verschillende ontvangers of locaties."},
     "tags": ["verdelen","verdeling","toewijzen","verspreiden","proces","samenwerking","organisatie","systeem","actie","emotie","neutraal"]},

    {"begrip": "behoud", "lade_target": "weten",
     "lagen": {"laag1": "Behoud is het in stand houden of beschermen van iets.",
               "laag2": "Behoud zorgt ervoor dat iets waardevols blijft bestaan of niet verloren gaat.",
               "laag3": "Behoud is het bewust beschermen, onderhouden of bewaren van mensen, objecten, natuur, kennis of andere waardevolle zaken. Het doel is om te voorkomen dat iets verdwijnt, beschadigt of achteruitgaat. Behoud speelt een belangrijke rol in natuurbeheer, cultureel erfgoed, gezondheid, techniek en informatiebeheer.",
               "laag4": "Behoud is essentieel voor duurzaamheid en continuïteit. Binnen Spark is behoud een proces of doel waarbij eigenschappen, informatie, objecten of systemen zoveel mogelijk onveranderd of bruikbaar worden gehouden ondanks veranderingen in de omgeving."},
     "ws5": {"wie": "Mensen, organisaties en systemen.", "wat": "Het beschermen of in stand houden van iets.",
             "wanneer": "Wanneer iets waardevol of belangrijk is om te behouden.",
             "waar": "In de natuur, cultuur, techniek, organisaties en digitale systemen.",
             "waarom": "Om verlies, schade of achteruitgang te voorkomen.",
             "hoe": "Door onderhoud, bescherming, beheer en zorgvuldig gebruik."},
     "tags": ["behoud","bescherming","behouden","onderhoud","duurzaamheid","continuiteit","beheer","waarde","systeem","proces","emotie","neutraal"]},

    {"begrip": "saus", "lade_target": "weten",
     "lagen": {"laag1": "Saus is een vloeibare of halfvloeibare toevoeging die smaak, structuur of vocht aan voedsel geeft.",
               "laag2": "Saus wordt gebruikt om gerechten smaakvoller, smeuïger of aantrekkelijker te maken.",
               "laag3": "Saus is een mengsel van ingrediënten dat als aanvulling op voedsel wordt gebruikt. Sauzen kunnen warm of koud zijn en bestaan uit bijvoorbeeld olie, water, room, tomaat, kruiden of specerijen. Bekende voorbeelden zijn tomatensaus, mayonaise, mosterd en currysaus. De samenstelling en smaak verschillen per keuken en toepassing.",
               "laag4": "Sauzen spelen een belangrijke rol in veel keukens en kunnen de smaak, textuur en presentatie van een gerecht veranderen. Binnen Spark is saus een voedingsmiddel dat als toevoeging wordt gebruikt om andere voedingsmiddelen aan te vullen of te verrijken."},
     "ws5": {"wie": "Koks, producenten en consumenten.", "wat": "Een vloeibare of halfvloeibare toevoeging aan voedsel.",
             "wanneer": "Tijdens of na het bereiden en serveren van gerechten.",
             "waar": "In keukens, restaurants en voedselproductie.",
             "waarom": "Om smaak, textuur of vocht aan een gerecht toe te voegen.",
             "hoe": "Door ingrediënten te mengen, te bereiden en over of naast voedsel te serveren."},
     "tags": ["saus","voedsel","smaak","koken","ingrediënt","voeding","keuken","bereiding","toevoeging","product","emotie","neutraal"]},

    {"begrip": "consistentie", "lade_target": "weten",
     "lagen": {"laag1": "Consistentie is de mate waarin iets hetzelfde of voorspelbaar blijft.",
               "laag2": "Consistentie zorgt ervoor dat gedrag, eigenschappen of resultaten over langere tijd gelijk blijven.",
               "laag3": "Consistentie betekent dat iets op een stabiele en samenhangende manier verloopt zonder onnodige tegenstrijdigheden. Dit kan betrekking hebben op gedrag, kwaliteit, informatie, processen of materialen. Een consistente aanpak maakt resultaten voorspelbaarder en betrouwbaarder. In de voedingsindustrie kan consistentie ook verwijzen naar de dikte of structuur van een product, zoals een saus of deeg.",
               "laag4": "Consistentie is belangrijk voor vertrouwen, kwaliteit en efficiëntie. Binnen Spark is consistentie een eigenschap die aangeeft hoe stabiel, logisch en gelijkmatig informatie, gedrag, processen of systemen over de tijd blijven."},
     "ws5": {"wie": "Mensen, organisaties en systemen.", "wat": "De mate waarin iets stabiel en gelijk blijft.",
             "wanneer": "Wanneer gedrag, informatie of processen herhaald worden.",
             "waar": "In communicatie, organisaties, wetenschap, techniek en het dagelijks leven.",
             "waarom": "Om betrouwbaarheid, kwaliteit en voorspelbaarheid te vergroten.",
             "hoe": "Door dezelfde regels, werkwijzen of eigenschappen consequent toe te passen."},
     "tags": ["consistentie","stabiliteit","betrouwbaarheid","kwaliteit","structuur","proces","gedrag","informatie","systeem","eigenschap","emotie","neutraal"]},

    {"begrip": "zelfreflectie", "lade_target": "voelen",
     "lagen": {"laag1": "Zelfreflectie is het bewust nadenken over je eigen gedachten, gevoelens en gedrag.",
               "laag2": "Zelfreflectie helpt mensen om zichzelf beter te begrijpen en van ervaringen te leren.",
               "laag3": "Zelfreflectie is het proces waarbij iemand terugkijkt op eigen gedachten, gevoelens, keuzes en gedrag. Door bewust stil te staan bij ervaringen kan iemand inzicht krijgen in sterke punten, verbeterpunten en de gevolgen van zijn handelen. Zelfreflectie draagt bij aan persoonlijke ontwikkeling, zelfkennis en het maken van betere keuzes.",
               "laag4": "Zelfreflectie speelt een belangrijke rol bij leren, communicatie en persoonlijke groei. Binnen Spark is zelfreflectie een cognitief proces waarbij eerdere ervaringen worden geanalyseerd om inzicht te verkrijgen en toekomstig gedrag of beslissingen te verbeteren."},
     "ws5": {"wie": "Mensen.", "wat": "Het nadenken over eigen gedachten, gevoelens en gedrag.",
             "wanneer": "Na of tijdens ervaringen, gesprekken of belangrijke gebeurtenissen.",
             "waar": "Overal waar iemand bewust kan nadenken over zichzelf.",
             "waarom": "Om jezelf beter te begrijpen, te leren en jezelf verder te ontwikkelen.",
             "hoe": "Door ervaringen te analyseren, vragen aan jezelf te stellen en conclusies te trekken."},
     "tags": ["zelfreflectie","zelfkennis","ontwikkeling","leren","gedrag","gedachten","gevoelens","inzicht","persoonlijkheid","proces","emotie","neutraal"]},

    {"begrip": "uitzondering", "lade_target": "weten",
     "lagen": {"laag1": "Een uitzondering is een situatie die afwijkt van de algemene regel.",
               "laag2": "Uitzonderingen komen voor wanneer een regel of patroon niet op een specifiek geval van toepassing is.",
               "laag3": "Een uitzondering is een geval dat niet voldoet aan de normale regel, verwachting of werkwijze. Hoewel regels meestal voor veel situaties gelden, kunnen er omstandigheden zijn waarin een andere aanpak nodig is. Uitzonderingen komen voor in wetgeving, taal, wetenschap, techniek, programmeren en het dagelijks leven.",
               "laag4": "Uitzonderingen maken systemen flexibeler en realistischer, omdat niet iedere situatie hetzelfde is. Binnen Spark is een uitzondering een speciale conditie waarbij de standaardregel tijdelijk of blijvend niet wordt toegepast en een afwijkende behandeling nodig is."},
     "ws5": {"wie": "Mensen, organisaties en systemen.", "wat": "Een situatie die afwijkt van een algemene regel.",
             "wanneer": "Wanneer een standaardregel niet van toepassing is.",
             "waar": "In wetgeving, taal, wetenschap, techniek, programmeren en het dagelijks leven.",
             "waarom": "Omdat sommige situaties bijzondere voorwaarden of omstandigheden hebben.",
             "hoe": "Door een afwijkende regel of behandeling toe te passen op een specifiek geval."},
     "tags": ["uitzondering","regel","afwijking","conditie","systeem","structuur","besluit","logica","proces","emotie","neutraal"]},

    {"begrip": "verspreiding", "lade_target": "weten",
     "lagen": {"laag1": "Verspreiding is het zich uitbreiden of verdelen van iets over een groter gebied of meerdere plaatsen.",
               "laag2": "Verspreiding beschrijft hoe mensen, objecten, stoffen, informatie of organismen zich verplaatsen of worden verdeeld.",
               "laag3": "Verspreiding is het proces waarbij iets zich over een gebied, groep of systeem uitbreidt. Dit kan gaan om de verspreiding van planten en dieren, ziekten, informatie, warmte, geluid, licht of technologie. Verspreiding kan vanzelf plaatsvinden door natuurlijke processen of bewust worden veroorzaakt door mensen of systemen.",
               "laag4": "Verspreiding speelt een belangrijke rol in natuur, wetenschap, communicatie en logistiek. Binnen Spark is verspreiding een proces waarbij informatie, energie, materialen of organismen zich van één bron naar meerdere locaties of ontvangers verplaatsen."},
     "ws5": {"wie": "Mensen, dieren, organismen, systemen en natuurlijke processen.", "wat": "Het uitbreiden of verdelen van iets over meerdere plaatsen.",
             "wanneer": "Wanneer iets zich verplaatst of wordt doorgegeven.",
             "waar": "In de natuur, samenleving, netwerken en digitale systemen.",
             "waarom": "Door natuurlijke processen, communicatie, transport of bewuste verspreiding.",
             "hoe": "Door beweging, overdracht, transport, groei of communicatie."},
     "tags": ["verspreiding","verspreiden","uitbreiding","beweging","overdracht","informatie","natuur","systeem","groei","oppervlakte","emotie","neutraal"]},

    {"begrip": "fijnmaken", "lade_target": "doen",
     "lagen": {"laag1": "Fijnmaken is het kleiner maken van een materiaal of voedingsmiddel.",
               "laag2": "Bij fijnmaken wordt een voorwerp of stof verdeeld in kleinere stukjes of deeltjes.",
               "laag3": "Fijnmaken is de handeling waarbij een materiaal, voedsel of andere stof wordt verkleind door te snijden, malen, raspen, hakken, pletten of vermalen. Het doel kan zijn om de verwerking, bereiding, menging of opname te verbeteren. Fijnmaken wordt toegepast in koken, industrie, landbouw en productie.",
               "laag4": "Fijnmaken is een bewerkingsproces waarbij de structuur van een materiaal verandert door het op te delen in kleinere delen. Binnen Spark is fijnmaken een fysieke actie die de grootte en vorm van een object of stof wijzigt zonder de samenstelling direct te veranderen."},
     "ws5": {"wie": "Mensen, machines en systemen.", "wat": "Het kleiner maken van een materiaal of voedingsmiddel.",
             "wanneer": "Tijdens bereiding, verwerking of productie.",
             "waar": "In keukens, fabrieken, laboratoria en werkplaatsen.",
             "waarom": "Om een materiaal beter te verwerken, mengen of gebruiken.",
             "hoe": "Door te snijden, hakken, malen, raspen, pletten of vermalen."},
     "tags": ["fijnmaken","verkleinen","malen","hakken","raspen","pletten","vermalen","bewerken","materiaal","voedsel","emotie","neutraal"]},

    {"begrip": "vervolg", "lade_target": "doen",
     "lagen": {"laag1": "Een vervolg is datgene wat na iets anders komt of erop aansluit.",
               "laag2": "Een vervolg bouwt voort op een eerdere gebeurtenis, handeling of situatie.",
               "laag3": "Een vervolg is de volgende stap, fase of gebeurtenis die aansluit op iets wat eerder heeft plaatsgevonden. Het kan gaan om een gesprek, verhaal, proces, onderzoek, behandeling of activiteit. Een vervolg zorgt ervoor dat een ontwikkeling of reeks gebeurtenissen wordt voortgezet.",
               "laag4": "Een vervolg maakt continuïteit en ontwikkeling mogelijk. Binnen Spark is een vervolg een opeenvolgende stap binnen een proces, gebeurtenis of interactie, waarbij eerdere informatie of acties als basis dienen voor wat daarna gebeurt."},
     "ws5": {"wie": "Mensen, organisaties en systemen.", "wat": "De volgende stap of voortzetting van iets.",
             "wanneer": "Na een eerdere gebeurtenis, actie of fase.",
             "waar": "In gesprekken, processen, verhalen, projecten en activiteiten.",
             "waarom": "Om een ontwikkeling voort te zetten of een doel verder te bereiken.",
             "hoe": "Door aan te sluiten op wat eerder is gebeurd of besloten."},
     "tags": ["vervolg","voortzetting","opvolging","proces","ontwikkeling","tijd","gebeurtenis","planning","systeem","continuiteit","emotie","neutraal"]},

    {"begrip": "verzorging", "lade_target": "doen",
     "lagen": {"laag1": "Verzorging is het zorgen voor het welzijn, de gezondheid of het onderhoud van iemand of iets.",
               "laag2": "Verzorging helpt mensen, dieren, planten of objecten gezond, schoon en in goede staat te houden.",
               "laag3": "Verzorging omvat alle handelingen die bijdragen aan het welzijn, de gezondheid of het onderhoud van een persoon, dier, plant of object. Dit kan bestaan uit wassen, voeden, behandelen, schoonmaken, onderhouden of beschermen. Goede verzorging voorkomt achteruitgang en bevordert herstel, groei en kwaliteit.",
               "laag4": "Verzorging is een belangrijk onderdeel van gezondheid, opvoeding, natuurbeheer en onderhoud. Binnen Spark is verzorging een doelgerichte activiteit waarbij aandacht en handelingen worden ingezet om het functioneren of de conditie van een levend wezen of object te behouden of te verbeteren."},
     "ws5": {"wie": "Mensen, verzorgers, zorgverleners en eigenaren.", "wat": "Het zorgen voor gezondheid, welzijn of onderhoud.",
             "wanneer": "Wanneer iemand of iets zorg of onderhoud nodig heeft.",
             "waar": "Thuis, in de zorg, op school, in de natuur en op de werkplek.",
             "waarom": "Om gezondheid, veiligheid, groei of een goede conditie te behouden of te verbeteren.",
             "hoe": "Door te verzorgen, schoon te maken, te voeden, te behandelen of te onderhouden."},
     "tags": ["verzorging","zorg","onderhoud","gezondheid","welzijn","hygiëne","ondersteuning","bescherming","proces","hulp","emotie","neutraal"]},

    {"begrip": "inschatting", "lade_target": "doen",
     "lagen": {"laag1": "Een inschatting is een beoordeling of verwachting op basis van beschikbare informatie.",
               "laag2": "Een inschatting wordt gemaakt om een situatie, risico, kans of uitkomst te beoordelen wanneer niet alle informatie bekend is.",
               "laag3": "Een inschatting is het proces waarbij beschikbare informatie, ervaring en observaties worden gebruikt om een verwachting of oordeel te vormen. Een inschatting helpt bij het nemen van beslissingen, het plannen van acties en het beoordelen van kansen of risico's. Een inschatting is nooit volledig zeker en kan veranderen wanneer nieuwe informatie beschikbaar komt.",
               "laag4": "Binnen Spark is een inschatting een denkactie die voorafgaat aan een beslissing of reactie. Zowel mensen als AI-systemen maken voortdurend inschattingen om situaties te begrijpen, prioriteiten te bepalen en passende acties te kiezen. Een goede inschatting combineert kennis, context, ervaring en waarschijnlijkheid."},
     "ws5": {"wie": "Mensen, AI-systemen en organisaties.", "wat": "Het beoordelen of voorspellen van een situatie op basis van beschikbare informatie.",
             "wanneer": "Wanneer een beslissing, verwachting of beoordeling nodig is.",
             "waar": "In het dagelijks leven, werk, wetenschap, games en digitale systemen.",
             "waarom": "Om betere keuzes te maken en risico's, kansen of gevolgen te beoordelen.",
             "hoe": "Door informatie, ervaring, context en observaties te analyseren en daaruit een verwachting te vormen."},
     "tags": ["inschatting","beoordelen","voorspellen","analyse","besluitvorming","verwachting","risico","context","informatie","systeem","emotie","neutraal"]},

    {"begrip": "uiterlijk", "lade_target": "weten",
     "lagen": {"laag1": "Uiterlijk is hoe iemand of iets er aan de buitenkant uitziet.",
               "laag2": "Het uiterlijk bestaat uit zichtbare kenmerken zoals vorm, kleur, grootte en stijl.",
               "laag3": "Uiterlijk beschrijft de waarneembare eigenschappen van een persoon, dier, object of omgeving. Het gaat om kenmerken zoals lichaamsbouw, gezichtskenmerken, kleding, kleur, vorm, materiaal en afwerking. Het uiterlijk geeft een eerste indruk, maar zegt niet altijd iets over de eigenschappen, kwaliteit of het karakter van iemand of iets.",
               "laag4": "Het uiterlijk speelt een belangrijke rol bij herkenning, communicatie en waarneming. Binnen Spark is uiterlijk een verzameling zichtbare eigenschappen waarmee mensen en systemen objecten, personen en andere entiteiten kunnen herkennen, onderscheiden en beschrijven."},
     "ws5": {"wie": "Mensen, dieren, objecten en systemen.", "wat": "De zichtbare buitenkant of verschijningsvorm.",
             "wanneer": "Wanneer iets wordt waargenomen of beschreven.",
             "waar": "Overal waar visuele waarneming mogelijk is.",
             "waarom": "Om iets of iemand te herkennen, te onderscheiden of te beschrijven.",
             "hoe": "Door zichtbare kenmerken zoals vorm, kleur, grootte, materiaal en stijl waar te nemen."},
     "tags": ["uiterlijk","uiterlijkkenmerken","verschijning","vorm","kleur","waarneming","herkenning","eigenschappen","object","emotie","neutraal"]},
]


def _find_in_files(begrip):
    """Vind kaart in elk JSON-bestand. Return (file_path, idx) of (None, None)."""
    for fname in ["knowledge_inbox.json", "knowledge_v2_doen.json", "knowledge_v2_weten.json",
                  "knowledge_v2_voelen.json", "knowledge_v2_spreken.json"]:
        fp = BASE / fname
        data = json.loads(fp.read_text())
        for i, k in enumerate(data.get("kaarten", [])):
            if (k.get("begrip") or "").lower().strip() == begrip.lower():
                return fp, i, data
    return None, None, None


def main():
    moved = []
    for spec in CARDS:
        begrip = spec["begrip"]
        overwrite = spec.get("overwrite", False)
        src_fp, idx, src_data = _find_in_files(begrip)
        if src_fp is None:
            print(f"  ⚠️  {begrip}: nergens gevonden")
            continue
        kaart = src_data["kaarten"].pop(idx)
        src_data["kaarten"] = src_data["kaarten"]  # explicit
        src_fp.write_text(json.dumps(src_data, indent=2, ensure_ascii=False))
        # Update kaart
        kaart["lagen"] = spec["lagen"]
        kaart["ws5"] = spec["ws5"]
        kaart["tags"] = spec["tags"]
        kaart["lade"] = spec["lade_target"]
        kaart["updated_at"] = NOW
        kaart["updated_by"] = "user-001"
        kaart.setdefault("history", []).append({
            "ts": NOW, "actie": "filled_from_doc",
            "bron": "verlorenkennis.txt (batch 5)",
            "lade": spec["lade_target"],
            "overwrite": overwrite
        })
        kaart.pop("inbox_reden", None)
        # Schrijf naar target
        lade_fp = BASE / f"knowledge_v2_{spec['lade_target']}.json"
        lade_data = json.loads(lade_fp.read_text())
        lade_data.setdefault("kaarten", []).append(kaart)
        lade_fp.write_text(json.dumps(lade_data, indent=2, ensure_ascii=False))
        moved.append((begrip, spec["lade_target"]))
        mark = "🔄" if overwrite else "✅"
        print(f"  {mark} {begrip:14s} → {spec['lade_target']}  (was in {src_fp.name})")
    print(f"\nVerwerkt: {len(moved)}")


if __name__ == "__main__":
    main()
