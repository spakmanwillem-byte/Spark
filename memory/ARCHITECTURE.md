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

## DSP-002 · Verteller-bot user_id NIET gelijkstellen aan user

- **Datum**: 2026-05-23
- **Trigger**: Bij `[start verhaal]` had ik de 4 verteller-berichten user_id `user-001` gegeven (Willem's id) → alle verhaal-bubbles kregen Willem's avatar. De community avatar-lookup pakt namelijk via `user_id`.
- **Beslissing**: Verteller-rol heeft altijd zijn eigen bot-id (in dit geval `bot-dood`). NOOIT user-001 of een andere echte user-id "lenen" voor bot-output. Ook al voelt het narratief logisch.
- **Verplichting**: Bij elke nieuwe bot-output (storyteller, sage, GM, NPC) → check dat `user_id` matched met een bot in `bot_users.json` met eigen avatar.
- **Patroon-naam**: "Avatar-userid coupling".

---

## DSP-003 · Naam-display swap user-000 ↔ user-001

- **Datum**: 2026-05-23
- **Trigger**: User's mental model: "De Willem = wallet 00, Spark = wallet 01". Maar de data heeft het andersom: user-000 = Spark, user-001 = De Willem (waar Bitvavo creds & 11MB chat-history op staan).
- **Beslissing**: ALLEEN display-laag swap, NIET data-swap. Force-override `user_naam` in `/api/trade/admin/bots` zodat admin overzicht klopt met mental model. Data ongemoeid.
- **Verplichting**: Bij elke admin-overview (analytics, dashboard, persoonkaart) waar user-000/001 voorkomt — display-override toepassen. NOOIT in users.json zelf de namen omdraaien (zou alle history breken).
- **Verwijst naar**: code in `/app/backend/modules/trade/routes.py` zoek `v5_display_swap_001`.

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

---

## Meta · Hoe deze notebook werkt

- Nieuwe entry = **DSP-NNN** (Dual-Source Pattern) of **AD-NNN** (Architecture Decision).
- Iedere entry heeft minimaal: datum, trigger, files involved, beslissing, verplichting.
- Cross-references: in elk betrokken bestand een `_arch_ref` veld met de DSP-id en pad naar dit document.
- Dit document hoort bij elke onboarding/handoff te worden gelezen.
- **Ook zichtbaar in Roadmap UI**: phase "📐 Werkwijze & Conventies" toont de belangrijkste afspraken voor user-zicht.
