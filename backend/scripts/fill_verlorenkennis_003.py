"""v6_kbv2_fill_003 — vul 13 kaarten uit verlorenkennis.txt batch 3"""
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).parent.parent / "data" / "knowledge" / "v2"
NOW = datetime.now(timezone.utc).isoformat()

CARDS = [
    {"begrip": "fles", "lade_target": "weten",
     "lagen": {
         "laag1": "Een fles is een afsluitbare verpakking voor het bewaren en vervoeren van vloeistoffen.",
         "laag2": "Een fles beschermt de inhoud en maakt het mogelijk om vloeistoffen veilig op te slaan, te vervoeren en uit te schenken.",
         "laag3": "Een fles is een hol voorwerp met een smalle opening dat wordt gebruikt voor het bewaren van vloeistoffen. Flessen kunnen gemaakt zijn van glas, kunststof of metaal en worden afgesloten met een dop, kurk of andere sluiting. Ze worden gebruikt voor onder andere water, frisdrank, olie, melk, schoonmaakmiddelen en medicijnen.",
         "laag4": "Flessen spelen een belangrijke rol in opslag, transport en distributie van vloeistoffen. De vorm, inhoud en het materiaal worden afgestemd op het gebruik. Binnen Spark is een fles een object dat dient als verpakking en bescherming van een inhoud, en onderdeel kan zijn van logistieke en gebruikssystemen."
     },
     "ws5": {"wie": "Consumenten, producenten, winkels en bedrijven.", "wat": "Een afsluitbare verpakking voor vloeistoffen.", "wanneer": "Bij het bewaren, vervoeren of gebruiken van vloeistoffen.", "waar": "In huishoudens, winkels, horeca, laboratoria en industrie.", "waarom": "Om vloeistoffen veilig te bewaren, beschermen en eenvoudig te gebruiken.", "hoe": "Door vloeistoffen in een afsluitbare verpakking met een opening en sluiting te bewaren."},
     "tags": ["fles", "verpakking", "object", "vloeistof", "opslag", "transport", "glas", "kunststof", "metaal", "verpakkingstechniek", "container", "inhoud", "emotie", "neutraal"]},

    {"begrip": "verpakking", "lade_target": "weten",
     "lagen": {
         "laag1": "Een verpakking is een omhulsel dat een product beschermt, bewaart of presenteert.",
         "laag2": "Verpakkingen maken het mogelijk om producten veilig op te slaan, te vervoeren, te verkopen en te gebruiken.",
         "laag3": "Een verpakking is een omhulsel of container waarin een product wordt geplaatst. Verpakkingen kunnen gemaakt zijn van karton, papier, kunststof, glas, metaal of andere materialen. Ze beschermen de inhoud tegen beschadiging, vervuiling en bederf en geven vaak informatie over het product, zoals de inhoud, gebruiksinstructies en houdbaarheid.",
         "laag4": "Verpakkingen vormen een belangrijke schakel tussen productie, transport, opslag en gebruik. De keuze van het materiaal en de vorm hangt af van de eigenschappen van het product. Binnen Spark is een verpakking een object dat bescherming, informatie en logistiek met elkaar verbindt."
     },
     "ws5": {"wie": "Producenten, vervoerders, winkels en consumenten.", "wat": "Een omhulsel of container voor een product.", "wanneer": "Tijdens opslag, transport, verkoop en gebruik van producten.", "waar": "In fabrieken, magazijnen, winkels en huishoudens.", "waarom": "Om producten te beschermen, bewaren, vervoeren en presenteren.", "hoe": "Door een passend materiaal en ontwerp te gebruiken dat aansluit bij het product en het gebruik."},
     "tags": ["verpakking", "verpakkingstechniek", "verpakkingmateriaal", "bescherming", "opslag", "transport", "product", "container", "logistiek", "presentatie", "object", "materiaal", "emotie", "neutraal"]},

    {"begrip": "basisschool", "lade_target": "weten",
     "lagen": {
         "laag1": "Een basisschool is een school waar kinderen het basisonderwijs volgen.",
         "laag2": "Op de basisschool leren kinderen basisvaardigheden zoals lezen, schrijven, rekenen en samenwerken.",
         "laag3": "Een basisschool is een onderwijsinstelling waar kinderen meestal vanaf vier jaar onderwijs krijgen. Tijdens het basisonderwijs ontwikkelen zij kennis, sociale vaardigheden en persoonlijke vaardigheden. Naast vakken zoals taal, rekenen en wereldoriëntatie leren kinderen ook samenwerken, communiceren en zelfstandig werken.",
         "laag4": "De basisschool vormt de basis van het onderwijssysteem en bereidt kinderen voor op het voortgezet onderwijs. Binnen Spark is de basisschool een onderwijsomgeving waarin kennis, vaardigheden, gedrag en sociale ontwikkeling samenkomen."
     },
     "ws5": {"wie": "Leerlingen, leerkrachten, ouders en schoolmedewerkers.", "wat": "Een school waar kinderen basisonderwijs volgen.", "wanneer": "Tijdens de eerste jaren van de schoolloopbaan.", "waar": "In onderwijsinstellingen voor basisonderwijs.", "waarom": "Om kinderen basiskennis, vaardigheden en sociale ontwikkeling mee te geven.", "hoe": "Door lessen, oefeningen, opdrachten, spel en begeleiding van leerkrachten."},
     "tags": ["basisschool", "school", "onderwijs", "leerling", "leerkracht", "leren", "ontwikkeling", "educatie", "kennis", "kind", "onderwijsinstelling", "emotie", "neutraal"]},

    {"begrip": "draagkracht", "lade_target": "weten",
     "lagen": {
         "laag1": "Draagkracht is de maximale belasting die iets of iemand kan dragen of verwerken.",
         "laag2": "Draagkracht bepaalt hoeveel gewicht, druk of belasting zonder problemen kan worden opgevangen.",
         "laag3": "Draagkracht is het vermogen van een object, constructie, persoon of systeem om een bepaalde belasting te dragen zonder te bezwijken of overbelast te raken. In de bouw gaat het om het maximale gewicht dat een constructie veilig kan dragen. Bij mensen kan draagkracht ook verwijzen naar de fysieke, mentale of financiële belasting die iemand aankan.",
         "laag4": "Draagkracht is afhankelijk van de eigenschappen van het object of systeem en de omstandigheden waarin het wordt gebruikt. Binnen Spark is draagkracht een capaciteitseigenschap die aangeeft hoeveel belasting een object, persoon of systeem veilig kan verwerken voordat prestaties afnemen of schade ontstaat."
     },
     "ws5": {"wie": "Constructies, objecten, mensen en systemen.", "wat": "Het maximale vermogen om een belasting te dragen of verwerken.", "wanneer": "Wanneer gewicht, druk of andere belasting wordt uitgeoefend.", "waar": "In de bouw, techniek, natuur en het dagelijks leven.", "waarom": "Om veiligheid, stabiliteit en goed functioneren te waarborgen.", "hoe": "Door de sterkte, capaciteit en eigenschappen van het object, de persoon of het systeem te bepalen."},
     "tags": ["draagkracht", "belasting", "capaciteit", "kracht", "constructie", "gewicht", "stabiliteit", "sterkte", "systeem", "techniek", "eigenschap", "emotie", "neutraal"]},

    {"begrip": "oogst", "lade_target": "weten",
     "lagen": {
         "laag1": "Een oogst is de verzameling gewassen of producten die van het land zijn gehaald.",
         "laag2": "Een oogst is het resultaat van het verbouwen en binnenhalen van landbouwgewassen.",
         "laag3": "Een oogst bestaat uit gewassen, fruit, groenten of andere landbouwproducten die rijp zijn en worden verzameld. De hoeveelheid en kwaliteit van de oogst hangen af van factoren zoals het weer, de bodem, verzorging en het tijdstip van oogsten. Oogsten kunnen met de hand of met machines worden binnengehaald.",
         "laag4": "Een oogst vormt het eindresultaat van een groeiproces in de landbouw en tuinbouw. De opbrengst is belangrijk voor voedselvoorziening, handel en economie. Binnen Spark is een oogst een product of resultaat dat ontstaat na een periode van groei en verzorging."
     },
     "ws5": {"wie": "Boeren, tuinders en landbouwbedrijven.", "wat": "De verzamelde opbrengst van gewassen of landbouwproducten.", "wanneer": "Wanneer gewassen rijp zijn om binnen te halen.", "waar": "Op akkers, weilanden, boomgaarden en in kassen.", "waarom": "Om voedsel en andere landbouwproducten te verkrijgen.", "hoe": "Door rijpe gewassen te verzamelen met de hand of met landbouwmachines."},
     "tags": ["oogst", "landbouw", "gewas", "opbrengst", "voedsel", "akker", "boerderij", "natuur", "productie", "resultaat", "emotie", "neutraal"]},

    {"begrip": "liefde", "lade_target": "voelen",
     "lagen": {
         "laag1": "Liefde is een sterke positieve emotie van verbondenheid, zorg en genegenheid.",
         "laag2": "Liefde zorgt ervoor dat mensen zich verbonden voelen en om elkaar geven.",
         "laag3": "Liefde is een diepe emotie die kan bestaan tussen partners, familieleden, vrienden of andere mensen. Liefde uit zich vaak in zorg, vertrouwen, respect, aandacht en het verlangen naar het welzijn van de ander. Liefde kent verschillende vormen, zoals romantische liefde, ouderliefde, vriendschap en naastenliefde.",
         "laag4": "Liefde speelt een belangrijke rol in relaties, sociale ontwikkeling en welzijn. De manier waarop liefde wordt ervaren en geuit verschilt per persoon, cultuur en situatie. Binnen Spark is liefde een fundamentele emotie die gedrag, keuzes en sociale verbinding beïnvloedt."
     },
     "ws5": {"wie": "Mensen en soms ook dieren.", "wat": "Een sterke emotie van verbondenheid, zorg en genegenheid.", "wanneer": "Wanneer een sterke band of affectie ontstaat.", "waar": "In relaties, gezinnen, vriendschappen en sociale omgevingen.", "waarom": "Om verbondenheid, zorg en vertrouwen tussen individuen te versterken.", "hoe": "Door aandacht, respect, zorg, steun en genegenheid te tonen."},
     "tags": ["liefde", "emotie", "blij", "verbondenheid", "genegenheid", "zorg", "vertrouwen", "relatie", "sociaal", "affectie", "welzijn", "ontwikkeling"]},

    {"begrip": "assistent", "lade_target": "weten",
     "lagen": {
         "laag1": "Een assistent is iemand of iets dat helpt bij het uitvoeren van taken.",
         "laag2": "Een assistent ondersteunt een persoon of systeem door werkzaamheden over te nemen of te vergemakkelijken.",
         "laag3": "Een assistent is een persoon of een digitaal systeem dat ondersteuning biedt bij bepaalde taken. Een assistent kan informatie geven, werkzaamheden uitvoeren, plannen maken of helpen bij het oplossen van problemen. Er bestaan menselijke assistenten, zoals onderwijs- of zorgassistenten, en digitale assistenten, zoals AI-assistenten en spraakassistenten.",
         "laag4": "Assistenten vergroten de efficiëntie door ondersteuning te bieden zonder de hoofdverantwoordelijkheid over te nemen. Binnen Spark is een assistent een ondersteunende rol die gebruikers of systemen helpt met informatie, communicatie, besluitvorming of uitvoering van taken."
     },
     "ws5": {"wie": "Mensen, AI-systemen en digitale hulpmiddelen.", "wat": "Een persoon of systeem dat ondersteuning biedt.", "wanneer": "Wanneer hulp of ondersteuning nodig is.", "waar": "Op het werk, op school, thuis, in organisaties en in digitale omgevingen.", "waarom": "Om taken makkelijker, sneller of beter uit te voeren.", "hoe": "Door informatie te geven, taken uit te voeren of ondersteuning te bieden aan een gebruiker of systeem."},
     "tags": ["assistent", "ondersteuning", "hulp", "rol", "samenwerking", "gebruiker", "systeem", "kunstmatige_intelligentie", "communicatie", "taak", "emotie", "neutraal"]},

    {"begrip": "groepsgedrag", "lade_target": "weten",
     "lagen": {
         "laag1": "Groepsgedrag is het gedrag dat ontstaat wanneer mensen of dieren als groep met elkaar omgaan.",
         "laag2": "Groepsgedrag laat zien hoe individuen elkaar binnen een groep beïnvloeden.",
         "laag3": "Groepsgedrag beschrijft hoe mensen of dieren zich gedragen wanneer zij deel uitmaken van een groep. Binnen een groep kunnen samenwerking, communicatie, leiderschap, sociale regels en onderlinge beïnvloeding ontstaan. Groepsgedrag verschilt vaak van het gedrag dat iemand alleen laat zien.",
         "laag4": "Groepsgedrag speelt een belangrijke rol in gezinnen, scholen, organisaties, sportteams en samenlevingen. Binnen Spark is groepsgedrag een sociaal proces waarbij de interactie tussen meerdere individuen invloed heeft op beslissingen, emoties en gezamenlijke acties."
     },
     "ws5": {"wie": "Mensen, dieren en groepen.", "wat": "Het gedrag dat ontstaat binnen een groep.", "wanneer": "Wanneer meerdere individuen met elkaar samenwerken of samenleven.", "waar": "In gezinnen, scholen, organisaties, sportteams en de samenleving.", "waarom": "Omdat groepsleden elkaar beïnvloeden en gezamenlijk doelen of regels ontwikkelen.", "hoe": "Door communicatie, samenwerking, sociale interactie en onderlinge beïnvloeding."},
     "tags": ["groepsgedrag", "groep", "gedrag", "samenwerking", "interactie", "communicatie", "sociaal", "invloed", "samenleving", "proces", "emotie", "neutraal"]},

    {"begrip": "vezel", "lade_target": "weten",
     "lagen": {
         "laag1": "Een vezel is een dunne, langwerpige structuur waaruit materialen of weefsels kunnen bestaan.",
         "laag2": "Vezels vormen de basis van veel natuurlijke en kunstmatige materialen, zoals wol, katoen en kunststof.",
         "laag3": "Een vezel is een dunne draadachtige structuur die afzonderlijk voorkomt of samen met andere vezels een materiaal vormt. Natuurlijke vezels, zoals wol, katoen en vlas, komen uit planten of dieren. Kunstmatige vezels worden door mensen gemaakt, bijvoorbeeld van kunststof. Vezels worden gebruikt voor kleding, touw, papier, isolatie en vele andere toepassingen.",
         "laag4": "Vezels verschillen in sterkte, flexibiliteit, dikte en duurzaamheid. Binnen Spark is een vezel een basismateriaal dat kan worden verwerkt tot producten of onderdeel vormt van biologische en technische structuren."
     },
     "ws5": {"wie": "Planten, dieren, mensen en industrie.", "wat": "Een dunne, langwerpige structuur die materialen vormt.", "wanneer": "Bij de productie of opbouw van natuurlijke en kunstmatige materialen.", "waar": "In planten, dieren, textiel, papier, touw en composietmaterialen.", "waarom": "Om materialen sterkte, structuur of flexibiliteit te geven.", "hoe": "Door natuurlijke groei of industriële productie van vezelmaterialen."},
     "tags": ["vezel", "materiaal", "textiel", "wol", "katoen", "kunststof", "structuur", "grondstof", "natuur", "industrie", "emotie", "neutraal"]},

    {"begrip": "noodsituatie", "lade_target": "weten",
     "lagen": {
         "laag1": "Een noodsituatie is een situatie waarin direct hulp of ingrijpen nodig is.",
         "laag2": "Een noodsituatie brengt mensen, dieren, eigendommen of de omgeving in gevaar en vraagt om snel handelen.",
         "laag3": "Een noodsituatie is een onverwachte situatie waarbij gezondheid, veiligheid of eigendommen ernstig worden bedreigd. Voorbeelden zijn brand, een ernstig ongeval, een overstroming of een medische noodsituatie. In een noodsituatie is snel en doelgericht optreden belangrijk om schade te beperken en levens te beschermen.",
         "laag4": "Noodsituaties kunnen ontstaan door natuurlijke gebeurtenissen, technische storingen of menselijk handelen. Binnen Spark is een noodsituatie een toestand met hoge prioriteit die directe aandacht en passende acties van mensen of systemen vereist."
     },
     "ws5": {"wie": "Mensen, hulpdiensten, organisaties en systemen.", "wat": "Een gevaarlijke situatie die direct ingrijpen vereist.", "wanneer": "Wanneer veiligheid, gezondheid of eigendommen ernstig worden bedreigd.", "waar": "Overal waar een onverwacht gevaar ontstaat.", "waarom": "Om schade te beperken en mensen, dieren of eigendommen te beschermen.", "hoe": "Door een gevaarlijke situatie te herkennen en snel passende maatregelen te nemen."},
     "tags": ["noodsituatie", "nood", "gevaar", "veiligheid", "hulp", "hulpdiensten", "crisis", "risico", "bescherming", "systeem", "emotie", "bang"]},

    {"begrip": "precisie", "lade_target": "weten",
     "lagen": {
         "laag1": "Precisie is de mate waarin iets nauwkeurig en zorgvuldig wordt uitgevoerd of gemeten.",
         "laag2": "Precisie zorgt ervoor dat metingen, handelingen of resultaten zo exact mogelijk zijn.",
         "laag3": "Precisie beschrijft hoe nauwkeurig een meting, berekening of handeling wordt uitgevoerd. Een hoge precisie betekent dat resultaten weinig van elkaar verschillen en zeer consistent zijn. Precisie is belangrijk in wetenschap, techniek, geneeskunde, productie en vakmanschap, waar kleine afwijkingen grote gevolgen kunnen hebben.",
         "laag4": "Precisie verschilt van nauwkeurigheid. Iets kan zeer precies zijn, maar toch afwijken van de juiste waarde. Binnen Spark is precisie een eigenschap die aangeeft hoe klein de variatie of afwijking is bij metingen, processen of handelingen."
     },
     "ws5": {"wie": "Mensen, machines en meetsystemen.", "wat": "De mate van nauwkeurigheid en consistentie.", "wanneer": "Bij meten, produceren, berekenen of uitvoeren van taken.", "waar": "In wetenschap, techniek, industrie, geneeskunde en dagelijks gebruik.", "waarom": "Om betrouwbare en consistente resultaten te verkrijgen.", "hoe": "Door zorgvuldig te werken, geschikte hulpmiddelen te gebruiken en afwijkingen te minimaliseren."},
     "tags": ["precisie", "nauwkeurigheid", "meting", "consistentie", "kwaliteit", "techniek", "wetenschap", "eigenschap", "proces", "resultaat", "emotie", "neutraal"]},

    {"begrip": "voorkeur", "lade_target": "voelen",
     "lagen": {
         "laag1": "Een voorkeur is wat iemand liever kiest of prettiger vindt.",
         "laag2": "Een voorkeur helpt mensen keuzes te maken tussen verschillende mogelijkheden.",
         "laag3": "Een voorkeur is een persoonlijke neiging om de ene optie boven een andere te kiezen. Voorkeuren kunnen gebaseerd zijn op ervaringen, behoeften, smaak, overtuigingen of gevoelens. Ze kunnen betrekking hebben op eten, muziek, mensen, activiteiten of andere onderwerpen en kunnen in de loop van de tijd veranderen.",
         "laag4": "Voorkeuren verschillen per persoon en zijn een belangrijk onderdeel van gedrag en besluitvorming. Binnen Spark is een voorkeur een persoonlijke eigenschap die invloed heeft op keuzes, aanbevelingen en interacties. Voorkeuren zijn niet goed of fout, maar beschrijven wat iemand het liefst heeft."
     },
     "ws5": {"wie": "Mensen en soms intelligente systemen.", "wat": "Een persoonlijke keuze of favoriete optie.", "wanneer": "Wanneer er meerdere mogelijkheden zijn om uit te kiezen.", "waar": "In het dagelijks leven, op school, op het werk en in digitale systemen.", "waarom": "Omdat mensen verschillende behoeften, ervaringen en interesses hebben.", "hoe": "Door een optie te kiezen die beter aansluit bij persoonlijke wensen of gevoelens."},
     "tags": ["voorkeur", "keuze", "voorkeuren", "gedrag", "persoonlijk", "interesse", "wens", "besluit", "ontwikkeling", "emotie", "neutraal"]},

    {"begrip": "event", "lade_target": "weten",
     "lagen": {
         "laag1": "Een event is een gebeurtenis die op een bepaald moment plaatsvindt.",
         "laag2": "Een event markeert een verandering, actie of gebeurtenis binnen een systeem of omgeving.",
         "laag3": "Een event is een gebeurtenis die door mensen of systemen wordt herkend en geregistreerd. Het kan gaan om een handeling, een verandering van toestand of een gepland moment. In software wordt een event gebruikt om processen te starten, terwijl het in het dagelijks leven bijvoorbeeld een vergadering, concert of andere gebeurtenis kan zijn.",
         "laag4": "Events vormen belangrijke schakels binnen systemen omdat ze veranderingen zichtbaar maken en reacties kunnen veroorzaken. Binnen Spark is een event een geregistreerde gebeurtenis die context toevoegt en andere processen, beslissingen of acties kan activeren."
     },
     "ws5": {"wie": "Mensen, systemen, programma's of objecten.", "wat": "Een gebeurtenis die plaatsvindt of wordt geregistreerd.", "wanneer": "Op een specifiek moment of tijdens een verandering.", "waar": "In de fysieke wereld, digitale systemen of sociale omgevingen.", "waarom": "Om veranderingen, acties of belangrijke momenten vast te leggen.", "hoe": "Door een gebeurtenis te herkennen, registreren of genereren."},
     "tags": ["event", "gebeurtenis", "systeem", "verandering", "registratie", "proces", "actie", "trigger", "informatie", "context", "emotie", "neutraal"]},
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
            "ts": NOW, "actie": "filled_from_doc", "bron": "verlorenkennis.txt (batch 3)", "lade": spec["lade_target"]
        })
        kaart.pop("inbox_reden", None)
        lade_fp = BASE / f"knowledge_v2_{spec['lade_target']}.json"
        lade_data = json.loads(lade_fp.read_text())
        lade_data.setdefault("kaarten", []).append(kaart)
        lade_fp.write_text(json.dumps(lade_data, indent=2, ensure_ascii=False))
        moved.append((spec["begrip"], spec["lade_target"]))
        print(f"  ✅ {spec['begrip']:14s} → {spec['lade_target']}")
    inbox_fp.write_text(json.dumps(inbox, indent=2, ensure_ascii=False))
    print(f"\nVerplaatst: {len(moved)} · Inbox nu: {len(inbox.get('kaarten', []))}")


if __name__ == "__main__":
    main()
