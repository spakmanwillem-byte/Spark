# Willem's Ideeën & Correcties tijdens Bouwen

> Doel: geen enkele goede gedachte verloren laten gaan. Als Willem tussendoor iets zegt dat een idee, correctie, of betere oplossing is → hier vastleggen met datum + context.
> Format: nieuwste bovenaan.

---

## 2026-07-09 — Sessie 46 (backtest-driven v8 + v4 waarheid)

### 🚨 KRITISCH: 100% win-rate was ILLUSIE
Backtest v4 met **ECHT netto** (gerealiseerd + open drawdown):
- **D (onze "winnaar")**: gerealiseerd €+2.63, open DD €-15.79 → **echt netto -€13.16**
- **P (D + Willems loss-cut)**: -€9.53 echt netto = **BETER dan D**
- **Baseline A**: -€26.15 echt netto — sterkste verlies
- Conclusie: 100% win-rate telde alleen gesloten trades; verliezen zaten verstopt in open posities

### 🟢 Willems H2 loss-cut BEWEZEN BETER
- Loss-cut trades: 22 van 65 (33.8%)
- Netto verbetering: €3.63 t.o.v. D zonder loss-cut
- Filosofische breuk gerechtvaardigd: verlies eerlijk pakken > geld bevriezen

### 🟢 Willems H1 rebound: statistisch onderbouwd, maar drempel te streng
- Post-event autopsy: **62.5% van 5%-drops is 24u later positief** (mediaan +1.96%)
- 49.2% herstelt ≥2% binnen 24u
- Aanbeveling: verlaag rebound-drempel naar 3% drop (nu 5%) → wél triggeren

### 🎯 Nieuwe P0 inzicht: eerlijke UI-metrics
Bouw endpoint + UI dat toont:
- Realized PnL
- Open drawdown (unrealized verlies van open posities)
- **ECHT netto = som van beide**
- Time-in-position (hoe lang zit geld vast)
- Loss-cut ratio (hoeveel % via loss-cut vs trailing)

### 🟡 Nieuwe hypothesen voor backtest v4 (Willems inzichten)
**H1: Rebound-strategie** — na 5-10% drop volgt binnen 24-72u vaak een 2-3% herstel.
- Toets: analyseer de 185 events uit v3-backtest. Wat deed de prijs 24/48/72u erna?
- Als >70% herstelt met ≥2%: dan is huidige event-pauze verkeerd → BUY-tijdens-drop is beter
- Anders: pauze-mode blijft, want dead-cat-bounce is geen zekerheid
- Nieuwe strategie: **Q. Bollinger + gap-body + rebound-BUY** (koopt juist bij event, target 2% winst)

**H2: 2-day loss-cut (tijd-gestuurde stop-loss)** — na 48u open, als positie ≥3% in **verlies** → SELL, herstart.
- Rationale: verliezen niet realiseren = kapitaal bevriezen. Klein verlies pakken > oneindig hopen.
- Filosofische breuk: Willem stapt gecontroleerd af van "nooit met verlies verkopen"-regel voor lange-open posities.
- Nieuwe strategie: **P. D + 2day-loss-cut-3%**
- Test tegen D op zelfde 6 markten × 6 maanden
- Verwacht effect: LAGERE win-rate (want klein verlies wordt gerealiseerd) MAAR minder kapitaal vast + eerlijker plaatje
- Variant later: 3-day, 5-day, 7-day loss-cut om optimale wachttijd te vinden

**Leer-element**: alles wat we monitoren is data voor Spark's toekomstige zelf-inzicht. Elke event → koppelen aan open posities → PnL-effect logging. Later kan Spark zeggen "5% drop op SOL kost me gemiddeld €X".

### 🟢 Bevestigd: contrarian tests bewijzen ons systeem
- **Random-buy verslaat D alleen bij 4/10 seeds**, mean €+2.43 (stddev €1.64) → D betrouwbaarder
- **Buy-and-hold verliest €-26.72** → actief traden werkt echt
- **Inverse Bollinger €-88.58** → mean-reversion is de juiste richting
- Alle 100% win-rates bevestigd niet-artefact door K die wél verliezen toont

### 🟢 Idee: elke module krijgt blueprint.json (uitgevoerd voor trade)
- `backend/modules/trade/blueprints/spark_trader.json` gemaakt
- Runtime-config: strategie, parameters, markten, event-protection, safety
- Volgende trader-tuning gaat via JSON, niet via code
- Piloot voor 54 andere modules

### 🟢 Idee: Spark als companion niet alleen bot
- Event-auto-pause + notification: "🚨 Ik zag {X}% drop, pauzeer bot"
- Bewaard in `data/trade/event_notifications.json`
- Endpoint `GET /api/trade/events/notifications` voor frontend badges

## 2026-07-08 — Sessie 46 (fork)

### 🟢 Idee: Pre-check EUR-balance vóór BUY-try (backlog, geen fix nu)
- **Context**: cooldown-fix (30 min) is een vangnet. De diepere oorzaak: `execute_real_trade` gaat pas ná Bitvavo API-call kijken of EUR toereikend is.
- **Betere flow**: eerst `get_balance()` cachen (5-min), dan lokaal beslissen "hebben we EUR? Zo nee: HOLD zonder Bitvavo API-hit".
- **Waarom nu niet**: geen nieuwe features / afmaken-modus. Cooldown werkt goed als vangnet. Kan later opgepakt.

### 🟢 Idee: Spark's poort tot eigen systeem (self-scan/edit)
- **Context**: Willem stelde voor: Spark moet zichzelf kunnen inzien én bewerken (à la GPT file-editor). "Zoek `seed_building_cards.py`, wat staat erin?"
- **Bestaande realiteit** (gevonden bij snuffelen):
  - `snuffel_bestand` capability bestaat in `spark_capabilities.json` (getest 29 jun, werkt)
  - `zelfscan`, `tellen_bestanden` capabilities bestaan
  - `/api/files/tree`, `/api/files/content`, `/api/files/save`, `/api/files/validate` endpoints bestaan
- **Wat mist**: **semantische verbinding** — Spark weet WEL dat bestanden bestaan, maar WEET niet WELK bestand relevant is bij welke vraag. Blueprint.md + KB-kaart met `bron_ref` naar bestand = die brug.
- **Regel**: bij elk "nieuw" idee → check eerst of capability/endpoint al bestaat. Zo ja: alleen verbinding maken, niet opnieuw bouwen.

### 🔴 Correctie: cooldown-fix is een pleister
- **Context**: agent bouwde 30-min EUR-cooldown na INSUFFICIENT_EUR_BALANCE
- **Willem's inzicht**: 22 potjes zouden 1-op-1 met Bitvavo moeten zijn. Als tekort optreedt → **er is een sync-mismatch**, geen kwestie van "even wachten". Root cause zit dieper (pot claimt kapitaal dat niet meer op Bitvavo staat).
- **Wat te doen**: root-cause via `/api/trade/delta`, cooldown blijft als vangnet.

### 🟢 Idee: Spark leest zijn eigen fundament
- **Context**: Willem vroeg trader-inhoudelijke vraag, Spark hallucineerde antwoord via LLM (geen KB-hit).
- **Willem's model**:
  ```
  trade.md (mens-editeerbaar, SOT)
    ↓ voedt
  KB v2 kaart "Spark Trader" 
    ↓ ingebed in compose bij trader-vraag
    ↓ hyperlink in legal voorwaarden
  ```
- **Regel**: "Help-data is single source of truth" — nu uitgebreid: **module-data is single source of truth**.

### 🟢 Idee: Elke Python-script ↔ parallel blueprint.json
- **Context**: 4 van ~55 modules hebben runtime-config-JSON gescheiden van code.
- **Willem's wens**: uitbreiden naar alle modules — zodat je reacties/limits/prompts kunt tunen ZONDER script aan te raken.
- **Bestaande infra**: `modules/core/blueprint.py::load_blueprint_cached()` — klaar voor gebruik.

### 🔵 Bouwregel voor deze sessie (en verder)
- **GEEN nieuwe features**. Alleen: bestaande dingen **afmaken**, **verbinden**, **volume geven**.
- Voorbeelden van "volume": module-blueprint markdown vullen, KB-kaarten genereren, code-config uit script trekken naar JSON.

---

_Update-instructie voor volgende agents: bij elke sessie hier bovenaan een nieuw datum-blok toevoegen. Nooit oude eruit halen._
