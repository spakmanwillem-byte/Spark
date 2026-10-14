# Onderzoek — Berichtenbeheer & WhatsApp in Spark Core
*Status: ONDERZOEK, geen code gewijzigd. Datum: 17-09-2026 (e1 sessie 59). Opdracht Willem: "wil je deze vraag onderzoeken, niks doen".*

---

## 0. Samenvatting in 6 regels

1. **Fase 1 MVP = Optie A (Android Notification Listener).** Legaal, geen ban-risico, geen cloud, past op Spark's bestaande privé-berichtenopslag.
2. **Optie B (whatsapp-web.js / Baileys) afgeraden** voor gebruikers: WhatsApp bant in 2026 actief en permanent, ook bij laag volume. Hooguit later als *opt-in experiment voor admin* met een wegwerp-nummer.
3. **Fase 3 (Business Platform/API) alleen als er een concrete zakelijke noodzaak is** — kost geld per bericht (1000 service-berichten/maand gratis per nummer sinds okt 2026), vereist publieke HTTPS-webhook en Meta Business-verificatie. Staat haaks op "geen cloud".
4. **Een aparte Android-app is noodzakelijk** voor Optie A (alleen een native app kan `NotificationListenerService` gebruiken). Klein, één scherm, één taak: meldingen → Spark Core over LAN.
5. **Spark heeft al 70% van de bouwstenen**: privé-berichtenopslag (`chat/prive`), contacten met gradatie-zichtbaarheid, glow-notificaties, privacy-guard, settings-schema, Verbindingen-kader (adapters!), Connections-pattern voor sleutels.
6. **Nieuwe module `modules/berichten/`** met één intern berichtschema + adapter-registry; adapters zijn losse bestanden. Kern raakt niets: alleen `server.py` include + sidebar-item.

---

## 1. Antwoorden op de 8 vragen

### 1.1 Welke bestaande onderdelen kunnen we hergebruiken?

| Bestaand | Waar | Hergebruik voor Berichtenbeheer |
|---|---|---|
| **Privé-berichten opslag** | `modules/contacts/routes.py` → `data/chat/prive/<a>__<b>.json`, schema `{id, from_user_id, to_user_id, text, ts, unread_by[], kind, system}` | Basis voor intern berichtschema; `kind` + `system` bestaan al → uitbreiden met `provider`/`source_type` |
| **Contacten + zichtbaarheid** | `modules/contacts` (gradatie-regels), `modules/bel_contacts` (`data/users/<id>/bel_contacts.json` met telefoonnummers!) | WhatsApp-contact ↔ Spark-contact koppelen op telefoonnummer |
| **Relay-service** | `modules/chat/relay_service.py` — "zeg tegen X dat…", per-user `spark_inbox.json`, voicemail-bij-agenda | Patroon voor "antwoord voorstellen" + inbox-per-user |
| **Glow / Urgent** | `modules/urgent`, `modules/glow_nav` — sidebar-tab laten gloeien | "Nieuw WhatsApp-bericht" → tab Berichten gloeit |
| **Privacy-guard** | `modules/core/privacy.py` `require_access(viewer, target)` → 403 | Toegang tot berichten strikt per eigenaar |
| **Settings-schema** | `modules/settings/routes.py` `SCHEMA` (user/system scope, gradatie-gated) | `berichten_ai_processing` (default **false**), `berichten_retention_days`, `berichten_sync_enabled` |
| **Verbindingen-kader** | `modules/connections` (`CONNECTION_DEFS`, test-knop, JSON wint van .env) | Elke adapter = één entry (Android-app token, evt. Business-API token) |
| **Auth** | `modules/auth` (sessie-tokens, admin_capable, gradaties) | Device-token voor Android-app afleiden van user-sessie |
| **Chat-hub / LLM-router** | `modules/chat_hub`, `modules/chat/llm_router.py` (Groq → Ollama → Emergent) | Samenvatten/antwoord-voorstel — alleen als `ai_processing_allowed` |
| **Eco-containers** | `data/users/<id>/` | Berichten per user in eigen container: `data/users/<id>/berichten/` |
| **cryptography** | al in `requirements.txt` (46.0.5) | Fernet-versleuteling van berichtbestanden (zie §6) |
| **Agent-skelet / Principe #8** | `modules/agents/*`, `command_registry.json` | `berichten_agent` + KB-kaart "Berichtenbeheer" |

**Niet hergebruiken / let op**: `data/chat/logs/` (Spark-gesprekken) en de KB mogen **geen** WhatsApp-inhoud krijgen zonder expliciete toestemming (eis §4 van Willem). `llm_output_scanner` / `lite_card_factory` (auto-leren uit LLM-antwoorden) moeten voor berichten-context **uit** staan.

### 1.2 Kleinste veilige implementatie voor fase 1

**"Meldingen-spiegel"** — alleen lezen, niets versturen:

1. Android-app (`SparkBridge`) met `NotificationListenerService`, filter op package `com.whatsapp` (en `com.whatsapp.w4b` voor Business-app).
2. Per melding: `{sender_title, text, when, conversation_hint, is_group}` → `POST http://<spark-lan-ip>:8001/api/berichten/ingest` met device-token.
3. Spark Core slaat op in `data/users/<id>/berichten/whatsapp-messenger.json` met `source_type: "notification"`, `ai_processing_allowed: false`.
4. Nieuwe tab **Berichten** (zelfde layout als Gesprekken) toont per gesprek de meldingen, met badge "uit melding" en glow bij nieuw.
5. Instellingen: aan/uit, bewaartermijn, "AI mag meelezen" (default uit), knop "alles verwijderen".

Geen antwoorden, geen media, geen geschiedenis. Dat is eerlijk: wat Spark niet heeft, verzint hij niet (eis §5).

### 1.3 Is een afzonderlijke Android-app noodzakelijk?

**Ja.** Alleen een geïnstalleerde native app met de permissie *Notification access* (`BIND_NOTIFICATION_LISTENER_SERVICE`) kan meldingen van andere apps lezen. Een webpagina/PWA kan dat niet. Alternatieven zonder eigen app:
- **Tasker/MacroDroid/Automate** (bestaande automatiseringsapps) kunnen WhatsApp-meldingen opvangen en een HTTP-POST doen → **nul eigen Android-code** voor een allereerst prototype. Nadeel: minder controle, derde partij, handmatige setup per telefoon. Prima om de Spark-kant te testen vóór de eigen app bestaat.
- Eigen app blijft het einddoel: één scherm (Spark-adres, QR-koppeling, aan/uit per contact), Kotlin, ~300 regels. Behandelen als *client van Spark Core*, geen eigen opslag of logica.

### 1.4 Hoe sturen we berichten via het lokale netwerk door?

- **Transport**: HTTPS of HTTP over LAN naar de Odroid/Spark-host. Omdat Spark lokaal draait zonder publiek certificaat: óf self-signed cert dat de app pint, óf HTTP-only met payload-versleuteling (Fernet-sleutel uit QR). Advies: **HTTP op LAN + versleutelde payload + device-token** — simpel en veilig genoeg binnen een thuisnetwerk; later TLS via `spark.sh`.
- **Discovery**: mDNS/`spark.local` is leuk maar fragiel; begin met QR-code in Spark (Verbindingen-kader → "Koppel telefoon") die `{host, port, device_token, enc_key}` bevat.
- **Richting**: telefoon → Spark (push). Spark hoeft de telefoon nooit te bereiken in fase 1. Buffer in de app als Spark offline is (Room/SQLite, max N berichten), opnieuw proberen.
- **Endpoint**: `POST /api/berichten/ingest` (batch), `GET /api/berichten/ping` (verbindingstest voor het kader), `DELETE /api/berichten/device/{id}` (ontkoppelen).

### 1.5 Beperkingen van de Android-meldingenmethode

| Beperking | Gevolg | Omgang |
|---|---|---|
| Alleen wat in de melding staat | Geen geschiedenis, geen media (alleen "📷 Foto"), afgekapte lange teksten | Markeer `source_type: notification`; nooit aanvullen |
| **Gebundelde meldingen** (meerdere chats → één samenvatting) | `android.text` is dan "5 nieuwe berichten"; echte regels zitten in `EXTRA_MESSAGES` (MessagingStyle) | App moet `EXTRA_MESSAGES` uitlezen; anders dubbele/lege items |
| Melding verdwijnt als gebruiker WhatsApp opent | Gelezen berichten worden nooit gemeld | Accepteren; alleen *inkomend ongelezen* is zichtbaar |
| Eigen verzonden berichten verschijnen niet | Gesprek is halfzijdig (alleen de ander) | UI toont dat expliciet ("alleen ontvangen") |
| Groepen: afzender zit in titel-formaat "Groep: Naam" | Parsing per taal/versie breekbaar | Opslaan als `raw_title`, parsing als aparte, testbare stap |
| Antwoorden via `RemoteInput` (Direct Reply) | Technisch mogelijk (actie "Reply" in melding), maar alleen zolang de melding er nog is; bij gebundelde meldingen vaak `null` → via `WearableExtender` | **Fase 2+**, opt-in, altijd met bevestiging |
| Android 15+ redigeert OTP-meldingen; werkprofielen negeren listeners; device-policy kan blokkeren | Zakelijke telefoons werken mogelijk niet | Documenteren |
| Doze/batterij-optimalisatie kan service pauzeren | Gemiste meldingen | App vraagt uitzondering batterij-optimalisatie |
| Google Play-beleid: Notification Listener vereist duidelijke privacyverklaring | Alleen relevant bij Play-publicatie; sideload (APK) voor eigen gebruik is vrij | Begin met sideload |

### 1.6 Noodzakelijke beveiligingsmaatregelen

1. **Device-token per telefoon** (random 32 bytes, in `data/users/<id>/berichten/devices.json`), gebonden aan user; intrekbaar. Elke `ingest` zonder geldig token → 401. Nooit de Spark-login van de user in de app opslaan.
2. **Payload-versleuteling** (Fernet, sleutel uit QR bij koppelen) zodat LAN-sniffing niets oplevert, ook zonder TLS.
3. **Opslag versleuteld**: berichtbestanden met Fernet, sleutel afgeleid van `SPARK_MASTERKEY` + user-id (cryptography staat al in requirements). Rest van Spark blijft plain JSON — dit is het enige datatype dat van derden is.
4. **Toegang**: `require_access(viewer, owner)` op elk endpoint; admins zien *geen* berichten van anderen (afwijkend van contacten-regel — berichten van derden zijn geen Spark-data).
5. **Rate-limit + payload-cap** op `ingest` (bv. 200 berichten/min, 8 KB per item) tegen een gekaapte telefoon.
6. **Geen KB-lekkage**: berichten-module registreert zich *niet* bij `kb_v2.hooks`, snap/scan/spontaneous-services krijgen de berichten nooit te zien. Hard afgedwongen door opslag buiten `data/chat/` en `data/knowledge/`.
7. **AI-toestemming is een opt-in per gesprek** (`ai_processing_allowed`), default `false`; LLM-aanroepen alleen lokaal (Ollama) tenzij gebruiker expliciet "cloud-LLM toegestaan" aanzet.
8. **Verwijderen**: "Alles wissen" verwijdert bestanden + device-tokens + eventuele samenvattingen; audit-regel in `data/system/logs/`.
9. **Bind-adres**: backend luistert nu op `0.0.0.0:8001` — op de Odroid is dat het hele LAN. Firewall-regel of expliciete `SPARK_BIND` is onderdeel van `spark.sh` (fase 1 Odroid-plan).

### 1.7 Welke bestanden aanpassen of toevoegen?

**Nieuw (module, geen kernwijziging):**
```
backend/modules/berichten/
  __init__.py          router export + _meta.json-conventie
  _meta.json           Principe #8: doel, endpoints, spark_note
  schema.py            Bericht, Gesprek, Device (pydantic) — het ENE interne schema
  service.py           opslag per user (versleuteld), dedupe, retention, delete-all
  adapters/
    __init__.py        registry: ADAPTERS = {"whatsapp-messenger-notif": ...}
    base.py            AdapterBase: normalize(raw) -> Bericht ; capabilities()
    whatsapp_notif.py  Android-meldingen → Bericht (parsing EXTRA_MESSAGES, groep-titel)
  routes.py            POST /api/berichten/ingest, GET /api/berichten/gesprekken,
                       GET /api/berichten/gesprek/{id}, DELETE …, POST /api/berichten/device/pair
frontend/src/components/workspace/BerichtenPage.js   (kopie-structuur van GesprekkenPage)
android/SparkBridge/   (aparte client; eigen repo-map, Kotlin)
```
**Aan te raken bestaand (minimaal):**
- `server.py` — 2 regels `include_router`.
- `MainLayout.js` — sidebar-item "Berichten" (sectie modules, gradatie-zichtbaarheid zoals rest).
- `App.js` — route.
- `modules/settings/routes.py` — 3 SCHEMA-keys (`berichten_*`).
- `modules/connections/service.py` — 1 entry in `CONNECTION_DEFS` ("SparkBridge telefoon", test = laatste ping).
- `data/system/command_registry.json` — endpoints registreren; KB-kaart "Berichtenbeheer" in weten.

**Niet aanraken**: `contacts`, `chat`, `kb_v2`, `relay_service`. Berichtenbeheer *leest* contacten (voor naam-koppeling), schrijft er niet in.

### 1.8 Hoe voorkomen we dat toekomstige adapters de kern raken?

- **Eén schema** (`schema.py`) is het contract. Adapters leveren `Bericht`-objecten, niets anders. Velden die een adapter niet heeft blijven `None` — nooit verzonnen.
- **Capabilities-declaratie** per adapter: `{"read": True, "history": False, "media": False, "send": False, "mark_read": False}`. UI toont/verbergt knoppen op basis hiervan, dus een nieuwe adapter met `send: True` krijgt automatisch een antwoordveld zonder UI-wijziging.
- **Registry-pattern** zoals `sandbox/registry.js` en `CONNECTION_DEFS`: nieuwe adapter = één bestand in `adapters/` + één regel in de registry. Geen `if provider == …` buiten de adapter.
- **Eigen opslag-namespace** per provider (`berichten/<provider>.json`) maar hetzelfde schema; zoeken/samenvatten werkt provider-agnostisch.
- **Spark Core-identiteit, KB, chat-hub weten niets van berichten.** Enige koppelpunt is optioneel en expliciet: `berichten_agent` kan — alleen met toestemming — een samenvatting aan de gebruiker aanbieden via het bestaande relay-/inbox-mechanisme.
- **Toetsing**: elke adapter moet `tests/test_berichten_adapter_<naam>.py` hebben die van ruwe input naar `Bericht` gaat; de kern-tests veranderen niet.

---

## 2. Optie A vs Optie B — vergelijking

| | **A. Android Notification Listener** | **B. WhatsApp Web-koppeling (whatsapp-web.js / Baileys)** |
|---|---|---|
| Legaal / ToS | Toegestaan (gebruiker geeft eigen telefoon toestemming) | **Schending WhatsApp ToS**; "unauthorized application" |
| Ban-risico | Geen | **Hoog en toenemend (2025-2026)**: permanente bans ook bij laag volume; headless-browser- en protocol-fingerprinting |
| Volledigheid | Alleen inkomende ongelezen meldingen; geen media/geschiedenis | Volledig: geschiedenis, media, groepen, versturen |
| Antwoorden | Beperkt (Direct Reply, fase 2) | Volledig |
| Infra | Telefoon + Spark op LAN | Node-proces met Chromium (web.js, ~400 MB RAM) of WebSocket (Baileys) op de Odroid; QR-koppeling, sessie breekt bij WhatsApp-updates |
| Odroid-haalbaarheid | Prima | web.js zwaar op ARM; Baileys lichter maar instabiel |
| Privacy | Alleen wat de telefoon al toont | Volledige sessie-sleutels van je WhatsApp op de Odroid |
| Onderhoud | Android-API stabiel | Breekt bij elke WhatsApp-protocolwijziging; libraries hollen achter |
| **Advies** | **MVP fase 1** | **Niet voor gebruikers.** Eventueel later als admin-only experiment met tweede nummer, uitdrukkelijk "kan je account kosten" |

## 3. Fase 3 — WhatsApp Business

- **Business-app** (`com.whatsapp.w4b`): technisch zelfde Notification Listener-aanpak als Messenger (ander package-id). Geen extra integratiemogelijkheden boven Messenger; "Business-app via ondersteunde Android-functies" = exact Optie A met tweede package-filter. **Geen aparte techniek nodig.**
- **Business Platform / Cloud API** (officieel): per-bericht prijsmodel (categorieën marketing/utility/authentication/service, tarief per land); sinds okt 2026 **1000 service-berichten per nummer per maand gratis**, daarna betaald; utility-templates in het 24-uursvenster nu ook betaald. Vereist: Meta Business-account + verificatie, een **publiek bereikbare HTTPS-webhook** (dus tunnel/cloud — botst met "geen cloud"), nummer dat niet tegelijk in de gewone app zit. Alleen zinvol voor een zakelijke Spark-tenant (clienten/sepa_hub-hoek). **Pas bouwen bij concrete klantvraag; als adapter `whatsapp-business-api` met `send: True`.**

## 4. Aansluiting op de bestaande architectuur (kort)

Berichtenbeheer wordt een **module naast `contacts`**, niet erin: contacten = Spark-interne gesprekken (users/bots), berichten = externe kanalen. Beide tonen in de UI onder één kop "Gesprekken" (tab Privé / tab Berichten) zodat het voor de gebruiker één plek is, terwijl de data strikt gescheiden blijft (eis §4). Adapters zijn verbindingen (Verbindingen-kader), berichten zitten in de eco-container van de user, AI is opt-in via settings, en Spark's kern/KB kent het bestaan van de module alleen via zijn KB-kaart (Principe #8).

## 5. Voorgestelde stappen (als Willem "ja" zegt — nu NIET uitgevoerd)

1. `modules/berichten/` skelet + schema + opslag + `ingest` endpoint + tests (Spark-kant, 1 sessie).
2. Prototype-ingest **zonder eigen app** via MacroDroid/Tasker op Willems telefoon → bewijst LAN-pad en parsing.
3. Tab Berichten (read-only) + glow + settings + "alles wissen".
4. Eigen Android-app `SparkBridge` (QR-koppeling, filter per contact, buffer).
5. Pas daarna fase 2 (zoeken, samenvatten met Ollama, antwoord-voorstel met bevestiging).
6. **Antwoordapparaat (idee Willem + Spark, vóór dit GPT-plan)** — Spark antwoordt WhatsApp-contacten namens de user
   als die volgens agenda bezet is: "Willem zit tot 15:00 in een afspraak — ik ben Spark, zijn assistent, ik geef het
   door." Hergebruikt `v6_voicemail_agenda_001` (`relay_service._agenda_busy_now` + inbox-notitie) één-op-één.
   Verzenden via Direct Reply (`RemoteInput`) uit de melding → adapter-capability `send: True`. Voorwaarden:
   per contact aanzetten, alleen vaste voorstel-tekst (geen vrije LLM naar derden), log van elk verzonden antwoord.
   Nevendoel: Spark voorstellen aan Willems contacten + testen in het echt.

## 5b. Drie standen per adapter (Willem, 17-09 — leidend voor de bouw)
1. **Ontvangen** — alleen inlezen en tonen. Niets terug.
2. **Reageren zonder zenden (concept-modus)** — Spark maakt zijn antwoord (agenda-check, voorsteltekst) en zet het
   als *concept* in de Berichten-tab. Willem ziet wat Spark zou zeggen; er gaat niets naar buiten. Dit is de
   testmodus voor het antwoordapparaat.
3. **Zenden** — per contact aan te zetten; concept wordt echt verstuurd (Direct Reply, later Business API).
Capability `send` wordt dus een stand `{"uit", "concept", "aan"}` i.p.v. true/false. Business API = tweede adapter
met dezelfde drie standen; alleen het transport (en de kosten) verschillen.

## 6. Open vragen voor Willem

- Welke telefoon/Android-versie? (bepaalt Notification-bundling gedrag en werkprofiel-beperkingen)
- Wil je het prototype eerst met MacroDroid/Tasker testen (geen app bouwen) of direct de eigen app?
- Moet Berichten ook voor andere users (Emmy, Ron…) of eerst alleen admin?
- Versleutelde opslag voor berichten: ja (advies) — ook al is de rest van Spark plain JSON?

*Bronnen: Android `NotificationListenerService`-documentatie; StackOverflow over MessagingStyle/`EXTRA_MESSAGES`/RemoteInput; GitHub-issues whatsapp-web.js #981/#3565/#4008 en Baileys #1983/#2309 (bans 2025-2026); Meta WhatsApp Business Platform pricing (per-message model, okt 2026).*
