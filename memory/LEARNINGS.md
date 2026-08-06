# Spark Core 2.0 — Learnings (bewezen inzichten)

> Kern-lessen uit vorige sessies. Elke agent hoort deze te lezen vóór een grote taak.
> Nieuwe les toevoegen? Alleen als bewezen (met sessie-referentie), geen speculatie.

## 🔍 1. Snuffel eerst, presenteer daarna
**Bron**: sessie 49 SLOT (26 juli 2026), sessie 56d (4 aug 2026)

Voordat je een oplossing bouwt of een probleem framet: **check wat er al is**. Trader-bugs, achievement-managers, admin-panelen — 80% van wat een AI voorstelt te bouwen bestaat al in de codebase.

Tools om te snuffelen (in volgorde):
- `spark_index` chat-intent: *"wat hebben we?"*, *"is X af?"*, *"waar woont X?"*
- `grep -rn "keyword" /app/backend/modules /app/frontend/src --include="*.py" --include="*.js"`
- `SYNAPSE.json` voor module-overzicht
- `CHANGELOG.md` voor "is dit al gebouwd?"
- `ROADMAP_HISTORY.md` voor "hoe hebben we het eerder aangepakt?"

**Fout-pattern**: Emmy stelt "Bouw Achievement & XP Manager" voor terwijl `AchievementBlueprintPanel` al in `InstellingenPage.js` r1195 leeft. Als iemand een feature omschrijft zonder de code te kennen, is dat een "beschrijving-van-behoefte", geen "bouw-taak".

## 📉 2. Unrealized DD altijd meerekenen bij backtests
**Bron**: sessie 49 EIND (2026-02-01)

Realized PnL alleen is **misleidend**. Verliezen kunnen verstopt zitten in open posities aan het einde van de test-periode.

Verplicht:
```
echt_netto = sum(realized_trades) + sum(open_positions_unrealized_at_end)
```

En: gebruik **minimaal 90d, liefst 500d** test-periode om market-regime bias te vermijden. Een 10-daagse backtest in bear-markt liegt over strategieën die in bull werken.

## 🎯 3. Willem's intuïtie > threshold-detectie
**Bron**: sessie 49 SLOT (26 juli 2026)

Willem koopt niet op **maximum drop**, hij koopt op **stabilisatie na drop**. Pure `drop ≥ threshold → BUY` is niet wat hij doet — hij wacht op reversal-confirmation.

**Implicatie**: strategie-code moet reversal-detectors gebruiken (bv. gap-filter, 3-red-then-green), niet pure percentage-drempels. In backtests: check waarom Willem's manuele trades winst maken maar bot-simulaties niet — meestal komt het door timing van BUY, niet door threshold.

## 🚫 4. Hard-triggers zijn oude vase
**Bron**: sessie 56b (4 aug 2026)

Woorden zoals "stop", "pauzeer", "zaag" waren ooit hard-triggers voor Spark-acties (trader-stop, sound-effects). Toen Spark alleen regex kende. Nu Spark zelf leert, moet elke hard-trigger achter een **admin-mode** of expliciete opt-in.

**Fout-pattern**: verhaal-paste in snap-input triggerde "trader stop" omdat trader_intents fastpath ongated draaide. Fix: `if req.admin_mode:` rond fastpath.

**Voor nieuwe hard-triggers**: default OFF, alleen aan als user expliciet die modus gekozen heeft.

## 🎨 5. Neutrale labels vóór jargon
**Bron**: sessie 56d (4 aug 2026)

Voor een rang/level/tier systeem: **eerst Rookie/Bronze/Silver/Gold** met XP-drempels. Pas hernoemen naar Sergeant/Luitenant/Kapitein als je genoeg gebruikers hebt om de verhoudingen te kalibreren (~15-20).

**Waarom**: als je "Kapitein" hebt uitgedeeld en later merkt dat 't te makkelijk was, kun je het NIET meer stilletjes weghalen. Neutrale labels laten je stilletjes kalibreren zonder aanspraak-schade.

## 🧊 6. Zwart-wit boven grijs (Willem's principe)
**Bron**: sessie 56c (4 aug 2026)

Zwart-witte regels dekken 90% van de gevallen en zijn over 2 jaar nog voorspelbaar. Genuanceerde regels dekken 100% maar zijn niet meer te ontwarren als je ze niet dagelijks onderhoudt.

Voor een systeem dat een gezin ooit erft: **strakke regel + expliciete uitzondering** > **flexibele regel met veel discretie**.

Voorbeelden:
- Infinitief-Regel voor lade-toewijzing (werkwoord → Doen-lade, homoniem-uitzondering apart)
- `admin_capable` boolean i.p.v. gradatie-drempels
- Cap-15 tags per kaart i.p.v. "afhankelijk van complexiteit"

## 🚦 7. Preview ≠ Production — altijd vragen
**Bron**: sessie 55 (5 aug 2026)

App is deployed. Twee omgevingen:
- **PREVIEW**: `https://question-hub-160.preview.emergentagent.com` — waar de agent werkt
- **PRODUCTION**: `https://question-hub-160.emergent.host` — waar Willem écht gebruikt

Bij een gerapporteerde bug **altijd eerst vragen**: "preview of productie?". Als productie: alleen preview-code fixen, dan Willem-redeploy. Als productie-only (env vars, domain): Emergent Support.

## 📦 8. Kladblok is voor werkende widgets, niet voor documentatie
**Bron**: sessie 56d (4 aug 2026)

Willem's "Kladblok" (in Beheer) is een sandbox-registry voor tijdelijke UI-widgets zonder eindbestemming. **NIET** een dumpplek voor snuffel-notes of documentatie — die horen in ROADMAP / LEARNINGS / CHANGELOG.

Regel: iets krijgt een widget alleen als het **interactief** is (data-fetchen, klik-acties, live-monitoring). Statische documentatie hoort in markdown-files.

## 🏗️ 9. Container-isolatie is de default
**Bron**: sessie 12 (2026-05-26)

Elke gebruiker/shop/bot heeft z'n eigen container met `_meta.json`. Nieuwe user-specifieke data (foto's, agenda, dagboek) gaat in `/data/users/{user_id}/...`, niet in globale bestanden.

Voordelen:
- Delete-user = delete-directory (geen weeskaarten)
- Foto's/documenten verhuizen mee met eigenaar
- Cross-contamination onmogelijk

**Fout-pattern**: shop-product-foto's stonden globaal in `/data/system_archive/foto/` — bij shop-verwijdering bleven ze rondzwerven. Gefixt in sessie 54.

## 🎁 Bonus: Vraag Willem als je twijfelt
Willem checkt AI-uitspraken graag. Als je iets voorstelt met impact:
- Geef 3-4 opties (a/b/c/d) met trade-offs
- Vertel wat je zelf zou kiezen en waarom
- Wacht op keuze vóór je bouwt

Beter 1 minuut verhelderen dan 30 minuten fout bouwen.
