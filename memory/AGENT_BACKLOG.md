# AGENT_BACKLOG.md — interne agent-context

> Dit bestand is **alleen voor de coding-agent**, niet user-visible.
> User brain-dumps die nog niet uitgewerkt zijn → hier. Pas als iets concreet uitgewerkt is verhuist het naar `roadmap.json` of `RoadmapPage.js` user-zichtbaar.

## Hoe te gebruiken
- Bij handoff: lees dit ALS EERSTE samen met `ARCHITECTURE.md` + `PRD.md`.
- Items verhuizen pas naar user-roadmap als ze geconcretiseerd zijn (acceptance criteria, files, plan).
- Mijn eigen fouten/missers staan hier, NOOIT op user-roadmap.

---

## 🌳 BRAIN-DUMP — Willem session 2026-05-23 (tweede ronde)

### Wortels (audit-vragen — moet ik antwoord op zoeken)
- ❓ **Vocab**: gebruiker snapt structuur niet helemaal. Format heeft alleen begroet/bedank/afscheid/reactie per emotie. Geen command-vocab, geen multimedia-vocab. Same words across emoties (te random).
- ❓ **Knowledge graph eindantwoord**: is een "compleet web" = vocab word + zin (context)? User vroeg dit, moet helder maken.
- ❓ **Search-concept Spark**: integratie-tab is nu admin-script. Idee: maakt het Spark's "handen/ogen/oren-tool" — `hey Spark heb jij [onderwerp]` → integratie-tab + bestanden-tab → ophalen
- ❓ **Spark module-aanroep**: kan Spark net als ik modules aanroepen (image, code, KB)? Of werkt het al via barks?
- ❓ **Shadow-learning audit**: werkt het, welke leer-modules zijn er, loggen ze goed?

### Stam (architectuur-ideeën)
- 🤲 **Spark's "handen" = capability registry** (NIEUW 2026-05-23):
  - User-zin patroon: `"kan jij [X]"`, `"wil je voor mij [X] kijken"`, `"weet jij [X]"`, `"heb ik [X]"`, `"hoeveel [X]"`
  - Layer 1: `/app/backend/data/personality/spark_capabilities.json` — centrale registry met `triggers`, `module`, `status` (live/placeholder/idea), `endpoint`
  - Layer 2: `spark_vocab.commando_acties` — Spark's stem-variatie bij capability-execution (zoeken/vinden/ophalen/tonen/afspelen/openen/tellen/niet_kunnen/wel_kunnen)
  - Layer 3 TODO: intent-matcher die user-text → capability_id mappt (kan voortbouwen op `chat/smart_intents_service.py`)
  - Layer 4 TODO: execution-router die capability_id → echte module-call doet
  - Placeholders eerlijk: "ik kan dat (nog) niet, staat op de roadmap"
  - Bouw-principe Willem: laag voor laag, met placeholders, niks stuk maken, log voor analyse
- 🌧️ **Emotie-systeem hertaalt**: Weer=humeur, Klimaat=persoonlijkheid, derde laag=karakter+normen+waarden. Huidige roadmap-tekst klopt niet meer.
- 📚 **Kenniskaart 2.0**: multi-modaal (tekst + beeld-kader + geluid-kader). Mic-icoon onder kaart → spreek in geselecteerd kader. Onbeantwoorde-kaart-flow.
- 🗂️ **Archivering**: opgeloste bugs + kasboek-tests + chatlog per dag/maand/jaar, auto-rolling op 1 dec. "Wat hebben we gisteren besproken" moet werken per stream.
- 🎲 **D&D start-verhaal**: bark met Titel + Avatar + Tekst + 3 keuze-barks. Nu: white-screen → refresh = Spark-chat. Help moet aparte bark zijn (geen chat-spam).

### Takken (concrete bugs/features uit gesprek)
- 🐛 **B1 Spark auto-buy potjes**: knop werkt, Spark "denkt" potjes te hebben maar koopt niet
- 🐛 **B2 Trader API loading**: watchlist + price-monitor niet 1 bron, lag bij venster-open. Pre-load cache OR 1-voor-1 ophalen
- 🐛 **B3 White-screen `help` in community chat**
- 🐛 **B4 Potje-waarde stijgt niet mee met token-waarde**
- 🐛 **B5 Kasboek heeft test-boekingen**: eruit voor schoon overzicht
- ✨ **F1 Mr Smith**: bark in community na 3/5 logins (reset @ 6) + als user 3/5x community kijkt → "ik zie je wel!"
- ✨ **F2 Harry Klokkemaker**: tijd-bark op match-uren (14:14, 21:21), elk heel uur, bij "hoe laat / wat is de tijd"
- ✨ **F3 Madelief**: bark in community: "Onder Workspace → Notitie & Taken → tab Bug Report — vul in, samen zullen we de bloemetjes buiten zetten"

### Bevestigde principes
- 💳 **Gift via Wallet, niet Winkel** (DONE ✓)
- 💳 Winkel: koop token → wallet. Wallet = account, kan gegift worden, later meer digitale items giftbaar (systeem aan user, niet aan winkel)
- 📐 Roadmap = boom (stam/wortels/takken). RoadmapPage.js moet die structuur volgen.
- 🤖 Spark moet zijn eigen content later begrijpen (zelf-reflectie laag — onderwerp voor v6+)

### Sessie-meta
- Credits budget deze sessie: 300 van 550
- User-stijl: brain-dump in lange berichten, wacht graag op mijn parsing-digest voor hij vervolgt
- User-fout-tolerantie: laag. Geen aannames. Eerst checken, dan handelen.

---

## ❗ Eigen agent-missers (zodat ik niet herhaal)

- 2026-05-23: Token gift naar verkeerde Nick (Teeuwen i.p.v. nieuwste). Les: bij dubbele namen ID/datum dubbel-checken.
- 2026-05-23: Gift-knop in Winkel gezet i.p.v. Wallet (user had het duidelijk gezegd). Les: user's expliciete plek-aanduiding niet overrulen met eigen "logica".
- 2026-05-23: Bel-meldingen niet weggehaald hoewel user dat eerder vroeg. Les: bij wens "bel weg" → direct weghalen, niet wachten op herhaling.
- 2026-05-23: Zip-backup bevatte info maar ik checkte 'm niet vóór ik werk begon. Les: ALTIJD zip/handoff eerst lezen.
