# Spark Core — Architecture Notes

Levend document met **dual-source patterns** en architecturale beslissingen die anders verzanden. Elk item heeft een datum, een trigger ("hoe ontdekt"), en de keuze.

Convenant: bij elke vondst van een dual-source moment → entry hier + cross-reference comment in beide bestanden.

---

## DSP-001 · Bot-data: `bot_users.json` ↔ `system/users.json`

- **Datum**: 2026-05-23
- **Trigger**: De Boekhouder + De Dood waren toegevoegd aan `users.json` maar verschenen niet in de "Online bots" widget. `/api/bots/list` leest namelijk uit een **andere** file.
- **Twee bronnen**:
  - `/app/backend/data/system/users.json` — **alle** menselijke users + bots in één unified list (auth, gradatie, avatar, persoonlijkheid). Gebruikt door auth-flow, admin overzicht, bot-instellingen tab.
  - `/app/backend/data/bots/bot_users.json` — alleen bots, mét hun **interactie-logica**: triggers (keyword/user_join/user_leave) + responses. Gebruikt door `/api/bots/list`, community-keyword-detection.
- **Beslissing**: Beide behouden — ze serveren verschillende doelen. `bot_users.json` is essentieel voor de keyword-trigger engine; `users.json` is essentieel voor de unified identity-laag.
- **Verplichting**: Bij **elke nieuwe bot** beide files updaten. Bij bot-rename → beide. Liever niet hercoderen tot één bron, want triggers-veld is bot-specifiek en zou users.json onnodig verzwaren.
- **Cross-refs toegevoegd**:
  - Comment in `bot_users.json` (top-regel `_arch_ref`)
  - Comment in `users.json` (top-regel `_arch_ref`)
  - Beide verwijzen terug naar dit document, DSP-001.

---

## Meta · Hoe deze notebook werkt

- Nieuwe entry = **DSP-NNN** (Dual-Source Pattern) of **AD-NNN** (Architecture Decision).
- Iedere entry heeft minimaal: datum, trigger, files involved, beslissing, verplichting (wat moet je nu altijd doen).
- Cross-references: in elk betrokken bestand een `_arch_ref` veld met de DSP-id en pad naar dit document.
- Dit document hoort bij elke onboarding/handoff te worden gelezen.

---

## Convenant-oorsprong (waarom dit bestaat)

- **Datum**: 2026-05-23
- **Trigger**: Willem merkte op dat ik bij dual-source ontdekkingen geen voetnoot maakte. Quote: "in situaties als deze moet je het in footnote en meta zetten als je er nog niet mee werkt na elkaar verwijzen als je er achterkomt. ook deze opmerking hahaha".
- **Beslissing**: Dit document is hét single point of truth voor dual-source patterns. Bij elke nieuwe ontdekking → DSP-entry + cross-ref in betrokken files.
- **Verplichting agent**: vóór een dual-source workaround eerst dit document checken; bij nieuwe vondst altijd entry maken.
