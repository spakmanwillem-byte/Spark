"""
v6_seed_building_cards_001 — verrijk de 23 gebouw-game-kaarten in data/cards/dnd/game.json.

Doel:
  - Vul laag1..laag4, ws5, tags en placeholder-foto voor elk gebouw.
  - Idempotent: overschrijft alleen lege velden, raakt bestaande media nooit aan.
  - Voor gebouwen zonder archief-foto wordt media.placeholder=True gezet zodat de
    admin later drag/drop een eigen foto kan koppelen via het beheer-paneel.

Run:
  python3 /app/backend/scripts/seed_building_cards.py
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

CARDS_PATH = Path("/app/backend/data/cards/dnd/game.json")

# id -> archive image id (zonder /api/ prefix). None = placeholder.
BUILDING_IMAGES = {
    "smederij": None,
    "jachthut": None,
    "kruidenwinkel": None,
    "houthakkerij": None,
    "mijn": None,
    "haven": "faf5df3e57ae",
    "waterput": "3131dfc4360b",
    "akker": "94a547d86f1a",
    "stadsbank": None,
    "bakker": "26a5cb38729e",
    "slager": "b17172e651e0",
    "traders post": None,
    "auction house": None,
    "kazerne": None,
    "herberg": None,
    "tempel van spark": "13ccbbf4fccf",
    "markt": "ebf5a7eca66d",
    "huis (t1)": None,
    "wachterspost": None,
    "gemeentehuis": "67cfb1c42e50",
    "stedelijk pakhuis": None,
    "stadsmuur": None,
    "stadspoort": None,
    "riool-ingang": None,
}

# id -> verrijkings-data per gebouw
BUILDING_DATA = {
    "smederij": {
        "lagen": {
            "laag1": "Een smederij is een werkplaats waar een smid ijzer en andere metalen smeedt tot gereedschap, wapens en uitrusting.",
            "laag2": "De smederij heeft een aambeeld, een blaasbalg en een vuur. Hier worden ertsen versmolten en gesmeed. Per level +2 smid-werkplekken.",
            "laag3": "Smederijen vormen het kloppend hart van een militaire en ambachtelijke economie. Zonder smid geen wapens, geen gereedschap, geen versterkingen. De warmte van het vuur en de klap van de hamer markeren de polsslag van de stad.",
            "laag4": "Spark ziet de smederij als een transformatiepunt: ruwe grondstof wordt onder hitte en kracht omgezet in betekenisvolle uitrusting voor het ecosysteem.",
        },
        "ws5": {
            "wie": "Smid, leerling-smeden, klanten met grondstoffen",
            "wat": "Werkplaats voor het smeden van metalen voorwerpen",
            "wanneer": "Dagelijks tijdens openingsuren; tijdens oorlog 24/7",
            "waar": "Centraal in het ambachtsdistrict van een stad",
            "waarom": "Om grondstoffen om te zetten in gebruiks- en strijdvoorwerpen",
            "hoe": "Door erts te smelten, te smeden en af te koelen op het aambeeld",
        },
        "tags": ["D&D", "gebouw", "handwerk", "smederij", "smid", "uitrusting", "ambacht"],
    },
    "jachthut": {
        "lagen": {
            "laag1": "Een jachthut is de uitvalsbasis voor jagers die wild leveren aan de stad.",
            "laag2": "Hier bewaren jagers hun strikken, bogen en buit. Per level +2 jager-werkplekken.",
            "laag3": "De jachthut staat aan de rand van het dorp, dichtbij het woud. Hier worden huiden gespannen, vlees gerookt en jachtroutes uitgewisseld.",
            "laag4": "Spark ziet de jachthut als grenspost tussen beschaving en wildernis — een interface waar de wereld grondstoffen levert aan het dorp.",
        },
        "ws5": {
            "wie": "Jagers, sjouwers van wildbuit",
            "wat": "Werkplek en uitvalsbasis voor de jacht",
            "wanneer": "Vroeg in de ochtend en bij dageraad",
            "waar": "Aan de bosrand van het dorp",
            "waarom": "Om voedsel, huiden en pelzen voor de stad te leveren",
            "hoe": "Door wild op te sporen, te strikken of te schieten en terug te brengen",
        },
        "tags": ["D&D", "gebouw", "verzamelen", "jacht", "jager", "voedsel", "huiden"],
    },
    "kruidenwinkel": {
        "lagen": {
            "laag1": "Een kruidenwinkel is de werkplek van de healer/kruidenkundige, gevuld met helende planten en elixers.",
            "laag2": "Hier worden potions gebrouwen, kruiden gedroogd en wonden verzorgd. Per level +1 healer-werkplek.",
            "laag3": "Geuren van tijm, salie en wilde munt vullen de ruimte. De healer biedt herstel-bonussen, alchemie-recepten en zeldzame ingrediënten aan reizigers.",
            "laag4": "Spark ziet de kruidenwinkel als het regenererende knooppunt — waar verlies omgezet wordt in herstel, en chaos in balans.",
        },
        "ws5": {
            "wie": "Healer, gewonden, alchemisten, herbalisten",
            "wat": "Winkel/werkplek voor kruiden, potions en helende mengsels",
            "wanneer": "Hele dag tijdens openingsuren; bij noodgevallen ook 's nachts",
            "waar": "In een rustig deel van het dorp, vaak nabij de tempel",
            "waarom": "Om HP-herstel, status-genezing en alchemie aan te bieden",
            "hoe": "Door kruiden te oogsten, drogen, mengen en toedienen",
        },
        "tags": ["D&D", "gebouw", "alchemie", "healer", "kruiden", "potion", "herstel"],
    },
    "houthakkerij": {
        "lagen": {
            "laag1": "Een houthakkerij is de werkplek waar bomen worden geveld en tot planken en boomstammen worden verwerkt.",
            "laag2": "Hier worden bijlen geslepen en boomstammen gestapeld. Per level +3 houthakker-werkplekken.",
            "laag3": "Houthakkerijen liggen aan de bosrand. Hun output (boomstam, plank, tak) voedt vrijwel elk ander bouwproject in de stad.",
            "laag4": "Spark ziet de houthakkerij als de bron-pijler — zonder hout geen huis, geen boog, geen warm vuur.",
        },
        "ws5": {
            "wie": "Houthakkers, sjouwers, timmerlieden",
            "wat": "Werkplek voor het kappen en bewerken van hout",
            "wanneer": "Bij daglicht, vooral in het droge seizoen",
            "waar": "Aan de rand van het bos",
            "waarom": "Om hout, planken en boomstammen aan de stad te leveren",
            "hoe": "Door bomen te vellen, te zagen en in stapels te ordenen",
        },
        "tags": ["D&D", "gebouw", "verzamelen", "hout", "houthakker", "boomstam", "plank"],
    },
    "mijn": {
        "lagen": {
            "laag1": "Een mijn is een ondergrondse werkplek waar mijners erts, steen en edelstenen winnen.",
            "laag2": "De diepte van de mijn bepaalt de erts-tier (T1-T5). Per level +3 mijner-werkplekken.",
            "laag3": "Schachten, balken en lantaarns markeren de mijn. Een ingang in de heuvel of berg leidt naar tunnels vol ijzer, zilver, goud — en gevaar.",
            "laag4": "Spark ziet de mijn als het diepste contact-punt met de oerlagen van de wereld — kostbaar, langzaam, en risicovol.",
        },
        "ws5": {
            "wie": "Mijners, opzichters, expediteurs van erts",
            "wat": "Ondergrondse werkplek voor ertswinning",
            "wanneer": "Hele dag, vaak in ploegen met lantaarnlicht",
            "waar": "In heuvels, bergen of rotsformaties bij de stad",
            "waarom": "Om erts, steen en edelstenen voor de smederij en handel te leveren",
            "hoe": "Door schachten te graven, gesteente te breken en buit naar boven te brengen",
        },
        "tags": ["D&D", "gebouw", "verzamelen", "mijn", "mijner", "erts", "edelsteen"],
    },
    "haven": {
        "lagen": {
            "laag1": "Een haven is de uitvalsbasis voor vissers en schepen aan de kustlijn.",
            "laag2": "Steigers, vissersboten en netten. Per level +4 visser-werkplekken. Vereist locatie: kustlijn.",
            "laag3": "Vissers brengen vis, zout en zeegrondstoffen binnen. Handelsschepen leveren goederen uit andere steden. De haven is het belangrijkste handels-knooppunt voor steden aan zee.",
            "laag4": "Spark ziet de haven als de grens-membraan met de zee — waar voedsel, handel en avontuur het dorp binnenstromen.",
        },
        "ws5": {
            "wie": "Vissers, kapiteins, handelaars, dokwerkers",
            "wat": "Aanlegplaats en werkruimte voor vis en handel",
            "wanneer": "Vóór zonsopgang voor de vangst; hele dag voor handel",
            "waar": "Aan de kustlijn van de stad",
            "waarom": "Om vis en goederen via water aan te voeren",
            "hoe": "Door schepen te lossen, netten te boeten en vis te verwerken",
        },
        "tags": ["D&D", "gebouw", "verzamelen", "haven", "visser", "kust", "handel"],
    },
    "waterput": {
        "lagen": {
            "laag1": "Een waterput is de drinkwater-bron van het dorp.",
            "laag2": "Een waterhaler tapt puur water voor het dorp en brengt het naar herbergen, smederijen en huizen. Per level +1 waterhaler-werkplek.",
            "laag3": "De put is een ontmoetingsplek waar nieuws en geruchten zich verspreiden. Schoon water is een eerste levensbehoefte voor mens en beroep.",
            "laag4": "Spark ziet de waterput als het stille knooppunt — onmisbaar maar onopvallend, totdat hij opdroogt.",
        },
        "ws5": {
            "wie": "Waterhaler, dorpsbewoners",
            "wat": "Toegang tot ondergronds zoet water",
            "wanneer": "Dagelijks, vooral in de ochtend",
            "waar": "Centraal op het dorpsplein",
            "waarom": "Om drinkwater en proceswater te leveren",
            "hoe": "Door emmers neer te laten en boven te halen via katrol",
        },
        "tags": ["D&D", "gebouw", "secondary", "waterput", "waterhaler", "drinkwater"],
    },
    "akker": {
        "lagen": {
            "laag1": "Een akker is een bewerkt stuk land waar boeren graan, groente en kruiden verbouwen.",
            "laag2": "Per level +3 boer-werkplekken. Akkers leveren graan voor bakker, kruiden voor healer en groente voor herberg.",
            "laag3": "Voren, stoppels en boerderijwagens markeren de akker. De cyclus van ploegen, zaaien, wieden en oogsten volgt het seizoen.",
            "laag4": "Spark ziet de akker als het traagste maar meest duurzame productiepunt — geduld levert hier de zekerste opbrengst.",
        },
        "ws5": {
            "wie": "Boeren, dagloners, oogstploegen",
            "wat": "Bewerkt landbouwgebied voor voedselproductie",
            "wanneer": "Per seizoen: ploegen, zaaien, oogsten",
            "waar": "Buiten de stadsmuur, in vruchtbaar laagland",
            "waarom": "Om graan, groente en kruiden voor de stad te telen",
            "hoe": "Door grond te bewerken, te zaaien, te onderhouden en te oogsten",
        },
        "tags": ["D&D", "gebouw", "verzamelen", "akker", "boer", "graan", "voedsel"],
    },
    "stadsbank": {
        "lagen": {
            "laag1": "De Stadsbank is het centrale opslag- en kluis-gebouw voor goud, edelstenen en waardepapieren.",
            "laag2": "Hier slaan burgers en stad hun goud op. Tier ↑ → warehouse-capaciteit ↑. Beschermd door wachters.",
            "laag3": "Een gewapend gebouw met dikke muren. Klanten openen een rekening, doen stortingen of nemen leningen op. Bij brand of inval is de bank het laatste bolwerk.",
            "laag4": "Spark ziet de Stadsbank als het stille geheugen van de economie — elke transactie wordt vastgelegd en bewaard.",
        },
        "ws5": {
            "wie": "Bankier, klanten, wachters",
            "wat": "Centraal opslag- en transactie-gebouw voor goud",
            "wanneer": "Tijdens kantooruren; nachts vergrendeld",
            "waar": "Centraal in het dorp, naast Gemeentehuis",
            "waarom": "Om goud veilig op te slaan en transacties te faciliteren",
            "hoe": "Door bezittingen in de kluis te leggen en grootboeken bij te houden",
        },
        "tags": ["D&D", "gebouw", "economie", "bank", "goud", "opslag", "kluis"],
    },
    "bakker": {
        "lagen": {
            "laag1": "Een bakker is een gebouw én beroep: hier wordt brood en gebak gebakken en verkocht.",
            "laag2": "Per level +1 bakker-werkplek. Vraagt graan uit de akker en hout uit de houthakkerij voor de oven.",
            "laag3": "De geur van versgebakken brood bij dageraad. Toonbank met verse waar, ovens achter, opslag van meel en gist.",
            "laag4": "Spark ziet de bakker als het dagelijkse ritueel — een vast moment waarop dorpsbewoners elkaar treffen.",
        },
        "ws5": {
            "wie": "Bakker, klanten, leveranciers van meel",
            "wat": "Werkplek en winkel voor brood, gebak en koek",
            "wanneer": "Vroege ochtend tot middag",
            "waar": "In het marktdistrict",
            "waarom": "Om vers brood en gebak aan het dorp te leveren",
            "hoe": "Door deeg te maken, te laten rijzen en te bakken",
        },
        "tags": ["D&D", "gebouw", "handwerk", "bakker", "brood", "voedsel", "ambacht"],
    },
    "slager": {
        "lagen": {
            "laag1": "Een slager is een gebouw én beroep: hier wordt vlees verwerkt, gesneden en verkocht.",
            "laag2": "Per level +1 slager-werkplek. Vraagt wildvlees van de jachthut en vlees van de boer.",
            "laag3": "Haken, snijbanken en koeling. De slager weet hoe elk dier het beste verwerkt wordt — niets gaat verloren: vlees, beenderen, huiden, vet.",
            "laag4": "Spark ziet de slager als het ontleed-knooppunt — waar één groot object in vele bruikbare delen wordt opgesplitst.",
        },
        "ws5": {
            "wie": "Slager, klanten, jagers en boeren",
            "wat": "Werkplek en winkel voor vleesverwerking",
            "wanneer": "Hele dag, met vroege voorbereiding",
            "waar": "In het marktdistrict",
            "waarom": "Om vlees veilig en bewerkt aan het dorp te leveren",
            "hoe": "Door dieren te ontleden, te snijden, te bewerken en te verkopen",
        },
        "tags": ["D&D", "gebouw", "handwerk", "slager", "vlees", "voedsel", "ambacht"],
    },
    "traders post": {
        "lagen": {
            "laag1": "Een Traders Post is de werkplek voor autonome handelaars die routes tussen steden afleggen.",
            "laag2": "Plaats werkloze burgers hier → autonomous trader cycle. Per level +1 trader-slot en +1 cargo-volume.",
            "laag3": "Karren, lastdieren en koopwaar staan klaar. Traders kopen goedkoop in de ene stad en verkopen duur in de andere. Een succesvolle trader brengt rijkdom én nieuws.",
            "laag4": "Spark ziet de Traders Post als de mobiele arm van het dorp — een uitstrekking die ver weg waarde haalt.",
        },
        "ws5": {
            "wie": "Traders, karrenmenners, hulpjes",
            "wat": "Vertrek- en aankomstpunt voor handelsroutes",
            "wanneer": "Per cyclus (dagelijks of meer)",
            "waar": "Bij de hoofdpoort van het dorp",
            "waarom": "Om autonome inter-stad handel te faciliteren",
            "hoe": "Door routes te plannen, goederen te kopen en elders te verkopen",
        },
        "tags": ["D&D", "gebouw", "logistiek", "trader", "handel", "autonoom"],
    },
    "auction house": {
        "lagen": {
            "laag1": "Het Auction House is de centrale veilingplaats waar burgers en steden goederen verhandelen.",
            "laag2": "Auction listings van burgers en steden. Tax 5% van elke trade naar gastheer-stad.",
            "laag3": "Een hal met podia, klokken en biedlijsten. Hier worden zeldzame items, partijen erts en heel soms huizen geveild. Een ervaren veilingmeester is goud waard.",
            "laag4": "Spark ziet het Auction House als de prijs-ontdekkings-engine van de wereld — vraag en aanbod ontmoeten elkaar publiekelijk.",
        },
        "ws5": {
            "wie": "Veilingmeester, bieders, verkopers, klerken",
            "wat": "Centrale veilingplaats met openbare prijsvorming",
            "wanneer": "Volgens veilings-schema (cyclisch)",
            "waar": "Centraal nabij de markt",
            "waarom": "Om eerlijke prijsvorming voor zeldzame items te bieden",
            "hoe": "Door biedingen te accepteren en aan hoogste bieder toe te wijzen",
        },
        "tags": ["D&D", "gebouw", "economie", "auction", "veiling", "handel"],
    },
    "kazerne": {
        "lagen": {
            "laag1": "De Kazerne is het militaire kwartier waar legereenheden worden gehuurd of getraind.",
            "laag2": "Huur legereenheden of (later) recruteer leger-beroep-soldaten.",
            "laag3": "Trainingsveld, wapenrek, slaapvertrekken voor soldaten. De Kazerne bepaalt mede de verdedigingskracht van het dorp.",
            "laag4": "Spark ziet de Kazerne als het defensie-knooppunt — discipline en kracht gebundeld voor bescherming van de gemeenschap.",
        },
        "ws5": {
            "wie": "Kapitein, soldaten, rekruten",
            "wat": "Militair kwartier voor training en huur van leger",
            "wanneer": "Dagelijkse drills, oproep bij dreiging",
            "waar": "Nabij de stadsmuur of stadspoort",
            "waarom": "Om de stad te verdedigen en aanvallen te coördineren",
            "hoe": "Door soldaten te trainen, uit te rusten en uit te zenden",
        },
        "tags": ["D&D", "gebouw", "leger", "kazerne", "soldaten", "verdediging"],
    },
    "herberg": {
        "lagen": {
            "laag1": "Een herberg biedt slaapplaats, eten en een leerplek voor het koken-beroep.",
            "laag2": "Logies (2 goud/dag), keuken voor koken, leer-koken NPC. Per level +2 kok-werkplekken.",
            "laag3": "Open haard, lange tafels, kamers boven. Reizigers ruilen verhalen en geruchten. De kok leert nieuwelingen de basis van koken voor 2 goud.",
            "laag4": "Spark ziet de herberg als het sociale kruispunt — waar reizen, eten en informatie elkaar ontmoeten.",
        },
        "ws5": {
            "wie": "Waard, kok, gasten, reizigers",
            "wat": "Logies, keuken en sociale ontmoetingsplek",
            "wanneer": "Hele dag, drukst in de avond",
            "waar": "Nabij de hoofdroute en markt",
            "waarom": "Om reizigers slaap, eten en leer-mogelijkheden te bieden",
            "hoe": "Door kamers te verhuren, maaltijden te serveren en kennis door te geven",
        },
        "tags": ["D&D", "gebouw", "wonen", "herberg", "kok", "logies", "voedsel"],
    },
    "tempel van spark": {
        "lagen": {
            "laag1": "De Tempel van Spark staat centraal in elk dorp en biedt leer-mogelijkheden en XP-boosts.",
            "laag2": "Leer een secundair beroep voor 2 goud, of activeer een 10% XP-boost voor 2 goud.",
            "laag3": "Een lichtgevende koepel, witte zuilen, een centrale haard van Sparks vlam. Hier komen mensen voor reflectie, leren en versterking.",
            "laag4": "Spark ziet de Tempel als haar eigen aanwezigheid in de wereld — een ontmoetingsplek tussen mens en systeem.",
        },
        "ws5": {
            "wie": "Tempelwachter, bezoekers, leerlingen",
            "wat": "Centraal sacraal gebouw voor leren en versterking",
            "wanneer": "Open van zonsopgang tot zonsondergang",
            "waar": "Centraal op het dorpsplein",
            "waarom": "Om kennis en XP-boosts toegankelijk te maken",
            "hoe": "Door 2 goud bij te dragen en een keuze (beroep/XP) te maken",
        },
        "tags": ["D&D", "gebouw", "sacraal", "tempel", "spark", "leren", "xp"],
    },
    "markt": {
        "lagen": {
            "laag1": "De Markt is de centrale handelsplek met drag-drop UI: jouw inventaris ↔ trader-NPC.",
            "laag2": "Drag-drop verkopen/kopen tegen NPC-trader. 5% tax op elke trade gaat naar de gastheer-stad.",
            "laag3": "Kraampjes, klanten, een centrale trader-NPC. Hier komt de stad bij elkaar om grondstoffen en items te verhandelen. Drukker dan welke andere plek dan ook overdag.",
            "laag4": "Spark ziet de Markt als de levendige handelsmotor — directe, dagelijkse uitwisseling tussen burgers.",
        },
        "ws5": {
            "wie": "Markt-NPC, kopers, verkopers, kraamhouders",
            "wat": "Centrale handelsplek met drag-drop UI",
            "wanneer": "Hele dag, drukst rond de middag",
            "waar": "Centraal in het dorp",
            "waarom": "Om dagelijkse handel mogelijk te maken",
            "hoe": "Door items in/uit de NPC-inventaris te slepen en te bevestigen",
        },
        "tags": ["D&D", "gebouw", "economie", "markt", "handel", "trader"],
    },
    "huis (t1)": {
        "lagen": {
            "laag1": "Een Huis (Tier 1) is een basis-woning met 1 kamer en 3 meubelplekken.",
            "laag2": "1 kamer, 3 meubelslots (bed, kist 15-slots, kast 35-slots). Upgrade T2-T5: +1 kamer per tier.",
            "laag3": "Een eenvoudig dak boven het hoofd. Bed voor regen-bonus, kist en kast voor opslag, eventueel fornuis of werkbank voor koken/craften thuis.",
            "laag4": "Spark ziet het Huis als de eerste private zone van de speler — waar je terugkeert om te slapen, op te slaan en je eigen ritme te bewaren.",
        },
        "ws5": {
            "wie": "Eigenaar, gezinsleden, gasten",
            "wat": "Eigen woning voor slaap, opslag en thuis-craft",
            "wanneer": "'s Avonds, 's nachts, bij rust",
            "waar": "In het woondistrict van het dorp",
            "waarom": "Om HP-regen, opslag en privacy te bieden",
            "hoe": "Door te bouwen, in te richten en bewoning te activeren",
        },
        "tags": ["D&D", "gebouw", "wonen", "huis", "tier1", "opslag", "slaap"],
    },
    "wachterspost": {
        "lagen": {
            "laag1": "Een Wachterspost is de werkplek van de wachters die het dorp bewaken en patrouilleren.",
            "laag2": "Leer Survival of Waterhaler voor 2 goud. Patrouilles (later). Per level +1 wachter-werkplek.",
            "laag3": "Een hoge uitkijktoren, een wapenrek, en altijd een wachter op post. Hier leer je overleven in de wildernis of waterhalen voor de stad.",
            "laag4": "Spark ziet de Wachterspost als het waarschuwingssysteem van het dorp — alerte oren en ogen aan de grens.",
        },
        "ws5": {
            "wie": "Wachters, leerlingen, uitkijkers",
            "wat": "Werkplek voor wacht, patrouille en leer-NPC",
            "wanneer": "24/7 in roterende ploegen",
            "waar": "Bij de stadspoort of hoog punt",
            "waarom": "Om dreiging vroeg te signaleren en leer-mogelijkheden te bieden",
            "hoe": "Door te observeren, te patrouilleren en kennis door te geven",
        },
        "tags": ["D&D", "gebouw", "defensie", "wachter", "patrouille", "leren"],
    },
    "gemeentehuis": {
        "lagen": {
            "laag1": "Het Gemeentehuis is de zetel van de stadsleider en het bestuurlijk centrum van de stad.",
            "laag2": "Stadsleider-kantoor, belasting-administratie, vergaderzaal. Hier worden decreten uitgevaardigd.",
            "laag3": "Lange gangen, ambtenaren, registers en zegels. Belastingen worden geïnd, conflicten beslecht en bondgenootschappen gesloten.",
            "laag4": "Spark ziet het Gemeentehuis als de bestuurs-laag — waar collectieve beslissingen worden vastgelegd in regel en wet.",
        },
        "ws5": {
            "wie": "Stadsleider, ambtenaren, burgers, gezanten",
            "wat": "Bestuurlijk centrum en zetel van de stadsleider",
            "wanneer": "Tijdens kantooruren en vergaderingen",
            "waar": "Centraal op het dorpsplein",
            "waarom": "Om bestuur, belasting en decreten te organiseren",
            "hoe": "Door zaken te behandelen, te registreren en te beslissen",
        },
        "tags": ["D&D", "gebouw", "bestuur", "gemeentehuis", "stadsleider", "belasting"],
    },
    "stedelijk pakhuis": {
        "lagen": {
            "laag1": "Het Stedelijk Pakhuis is de centrale opslag voor grondstoffen van de stad.",
            "laag2": "T1=1000 slots, T2=2000, T3=3000, T4=4000, T5=5000+ slots. Beheerd door de stadsleider.",
            "laag3": "Hoge rekken, grote deuren, klerken met klemborden. Hier worden bulk-grondstoffen geconcentreerd om grote bouwprojecten of belegeringen aan te kunnen.",
            "laag4": "Spark ziet het Pakhuis als de buffer-laag — voorraad voor magere tijden en grote ondernemingen.",
        },
        "ws5": {
            "wie": "Magazijnmeester, klerken, sjouwers",
            "wat": "Centrale grondstof-opslag voor de stad",
            "wanneer": "Hele dag tijdens werkuren",
            "waar": "Nabij de poorten of haven voor snelle aanvoer",
            "waarom": "Om bulk-grondstoffen veilig en gecentraliseerd te bewaren",
            "hoe": "Door goederen te ontvangen, te registreren en uit te geven",
        },
        "tags": ["D&D", "gebouw", "economie", "pakhuis", "opslag", "warehouse"],
    },
    "stadsmuur": {
        "lagen": {
            "laag1": "De Stadsmuur omcirkelt het dorp met 4 segmenten (N/O/Z/W) voor verdediging.",
            "laag2": "Elke segment = +5% defensie. Vol = +20% defensie. Bouw stap voor stap of in één keer.",
            "laag3": "Massieve stenen, weerbarstige torens. Bovenop kunnen wachters lopen en patrouilleren. Vrijwel onneembaar zonder belegerings-uitrusting.",
            "laag4": "Spark ziet de Stadsmuur als de fysieke grens-conditie — de membraan tussen veiligheid binnen en chaos buiten.",
        },
        "ws5": {
            "wie": "Bouwers, wachters, soldaten",
            "wat": "Defensieve perimeter rond de stad",
            "wanneer": "Permanent aanwezig na bouw",
            "waar": "Rond het dorp in 4 windrichtingen",
            "waarom": "Om de stad te beschermen tegen aanvallen",
            "hoe": "Door 4 segmenten te bouwen en te onderhouden",
        },
        "tags": ["D&D", "gebouw", "defensie", "stadsmuur", "perimeter"],
    },
    "stadspoort": {
        "lagen": {
            "laag1": "Een Stadspoort is een gecontroleerde doorgang in de stadsmuur (4 poorten N/O/Z/W).",
            "laag2": "Toegang-controle, optionele tol van 2% op handel. Hier passeert alle officiële handel.",
            "laag3": "Massieve houten deuren met ijzerbeslag, een poortwachter, een tol-register. Per windrichting één poort. Bij dreiging worden ze gesloten.",
            "laag4": "Spark ziet de Stadspoort als het filter-knooppunt — alles wat de stad binnenkomt of verlaat passeert hier.",
        },
        "ws5": {
            "wie": "Poortwachter, reizigers, kooplui",
            "wat": "Gecontroleerde doorgang door de stadsmuur",
            "wanneer": "Overdag open, 's nachts of bij dreiging gesloten",
            "waar": "In elke windrichting van de stadsmuur",
            "waarom": "Om controle en eventueel tolheffing op handel te bieden",
            "hoe": "Door reizigers te registreren en eventueel tol te innen",
        },
        "tags": ["D&D", "gebouw", "defensie", "stadspoort", "toegang", "tol"],
    },
    "riool-ingang": {
        "lagen": {
            "laag1": "Een Riool-ingang geeft toegang tot de ondergrondse dungeon-laag (2 ingangen O+W).",
            "laag2": "Toegang tot ondergrondse dungeon voor avontuur en loot. 2 ingangen Oost en West.",
            "laag3": "Een rooster, een trap omlaag, vochtige geur. Onder de stad ligt een netwerk van tunnels vol gevaar én buit. Niet voor de zwakken van hart.",
            "laag4": "Spark ziet de Riool-ingang als de schaduw-laag — wat de stad afvoert wordt elders het avontuur van de moedige.",
        },
        "ws5": {
            "wie": "Avonturiers, vijanden, schaduwwezens",
            "wat": "Toegangspunt tot de ondergrondse dungeon-laag",
            "wanneer": "Op elk moment toegankelijk; risicovoller 's nachts",
            "waar": "Aan de Oost- en Westkant van het dorp",
            "waarom": "Om avontuur, loot en gevaar bereikbaar te maken",
            "hoe": "Door af te dalen via de trap onder het rooster",
        },
        "tags": ["D&D", "gebouw", "avontuur", "dungeon", "riool", "loot"],
    },
}


def _norm(name: str) -> str:
    return (name or "").strip().lower()


def main() -> None:
    data = json.loads(CARDS_PATH.read_text(encoding="utf-8"))
    cards = data.get("cards", [])
    now = datetime.now(timezone.utc).isoformat()

    updated = 0
    skipped = 0
    no_match = []

    for card in cards:
        if card.get("game_meta", {}).get("kind") != "gebouw":
            continue

        key = _norm(card.get("begrip", ""))
        bd = BUILDING_DATA.get(key)
        if not bd:
            no_match.append(card.get("begrip"))
            continue

        changed = False
        # Lagen — vul lege velden + vervang auto-seed-pattern in laag1
        lagen = card.setdefault("lagen", {"laag1": "", "laag2": "", "laag3": "", "laag4": ""})
        existing_laag1 = (lagen.get("laag1") or "").strip()
        is_auto_seed = " — " in existing_laag1 and "Bouwkost:" in existing_laag1
        for lk, lv in bd["lagen"].items():
            current = (lagen.get(lk) or "").strip()
            if not current or (lk == "laag1" and is_auto_seed):
                lagen[lk] = lv
                changed = True

        # WS5 — vul alleen lege velden
        ws5 = card.setdefault("ws5", {})
        for wk, wv in bd["ws5"].items():
            if not ws5.get(wk):
                ws5[wk] = wv
                changed = True

        # Tags — merge unique, behoud bestaande
        existing_tags = card.setdefault("tags", []) or []
        merged = list(dict.fromkeys(existing_tags + bd["tags"]))
        if merged != existing_tags:
            card["tags"] = merged
            changed = True

        # Media — alleen vullen als image_urls nog leeg is
        media = card.setdefault("media", {"voice_url": None, "voice_transcript": None, "image_urls": []})
        if not media.get("image_urls"):
            img_id = BUILDING_IMAGES.get(key)
            if img_id:
                media["image_urls"] = [f"/api/system-archive/file/{img_id}"]
                media.pop("placeholder", None)
                changed = True
            else:
                # markeer als placeholder zodat admin kan filteren
                if not media.get("placeholder"):
                    media["placeholder"] = True
                    changed = True

        if changed:
            fn = card.setdefault("footnote", {})
            fn["laatst_bewerkt_op"] = now
            fn.setdefault("bron", "blueprint_seed")
            updated += 1
        else:
            skipped += 1

    CARDS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"updated={updated}  skipped={skipped}")
    if no_match:
        print(f"NO BUILDING_DATA voor: {no_match}")


if __name__ == "__main__":
    main()
