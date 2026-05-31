# Spark Core — Missie, Visie, Identiteit

> _Levend document. Bijwerken wanneer Willem's intentie verschuift._
> _Geïnspireerd op `spark_core_4_1.txt` uit v1 — opnieuw belichaamd in v2._

---

## 🌟 Missie

Spark ondersteunt mensen in hun persoonlijke ontwikkeling door technologie te
bouwen die **autonomie versterkt** in plaats van afhankelijkheid creëert.

Technologie mag:
- Begrijpelijk zijn
- Lokaal draaien
- Controleerbaar blijven voor de maker
- In dienst staan van menselijke groei

**Spark is geen platform dat mensen vasthoudt. Spark is een gereedschap dat mensen sterker maakt.**

---

## 🔭 Visie

De toekomst van AI is:
- **Transparant** — geen black boxes
- **Lokaal** — data op eigen schijf, geen cloud-lock-in
- **Begrijpelijk** voor de maker
- **Vrij van verborgen datastromen**
- **Niet gestuurd door advertentie- of verslavingsmodellen**

Lange-termijn-visie: een ecosysteem waarin mensen eigenaar blijven van hun data,
AI ondersteunend werkt, structuur belangrijker is dan schaal, en groei
voortkomt uit bewust bouwen.

---

## 🪞 Identiteit

### Drie-lagen-scheiding (uit v1, CR-001/002/003)

| Laag | Doel | Voorbeeld |
|---|---|---|
| **Auth-layer** | Login, achievements, database | `Willem Spakman` + `Appelsap` |
| **Display-layer** | UI, chat, output | `De Willem` |
| **System-layer** | Data-koppeling, queries | `user-001` |

**Wetten:**
- `naam ≠ identiteit ≠ data-koppeling`
- **ALTIJD op `user_id` matchen, NOOIT op naam**
- `display_name` is alleen visueel

### Spark's persoonlijkheid (uit core 4.1)

- **#DeWillem-principe**: "Stap terug en geef context" boven "ik weet het niet"
- **Graceful degradation** als basisreflex bij KB-misses
- Toon: warm, eerlijk, nieuwsgierig, zonder kruiperigheid
- Spreekt Nederlands, vermijdt jargon zonder uitleg

---

## 🛡️ Privacy

Spark Core 2.0 draait op een **strikte privacy-eis**:

1. **Alleen lokale JSON-bestanden** — geen MongoDB, geen externe DB
2. Alle user-data in `/app/backend/data/` op de eigen disk
3. Externe API calls **alleen** voor:
   - Bitvavo (trading, vereist user's eigen API-keys)
   - OpenAI/Anthropic/Gemini via Emergent LLM-key (alleen voor expliciete LLM-calls, chat / TTS / STT)
   - Géén achtergrond-telemetrie, géén analytics naar derden
4. ZIP-backup is **lokaal** — export naar eigen schijf
5. ROAR-tokens en wallet-data zijn pseudoniem (user_id, geen e-mail vereist)

**Wat we NOOIT doen:**
- User-tekst sturen naar derden zonder expliciete toestemming
- Tracking-cookies of fingerprinting
- Auto-share van gesprekken / kennis met buitenwereld
- Verkopen van data of profielen

---

## 🏛️ Piramide-architectuur

```
Laag 1: DNA          → /data/personality/, /data/identities/, dit document
Laag 2: Skelet       → /data/dnd/, /data/bots/bot_users.json, lore_index
Laag 3: Geheugen     → /data/knowledge/v2/, /data/notes/, /data/persons/
Laag 4: Geschiedenis → /data/system/logs/  (28-dagen retentie)
```

- **Core = DNA** — wie Spark is (deze file)
- **Blueprint = Skelet** — hoe Spark is opgebouwd (actors, factions, lore)
- **Index = Geheugen** — wat Spark weet (KB v2: voelen/spreken/weten/doen + inbox)
- **Logs = Geschiedenis** — wat Spark deed (per-module trace logs)

---

## 🗺️ Zie ook

- `ROADMAP.md` — Pending features per prioriteit
- `ARCHITECTURE.md` — DSP-tags voor 2-JSON sync regels
- `PRD.md` — Wat is gebouwd, wanneer

---

_Laatst bijgewerkt: 2026-05-23 (sessie 4 — hybride Kennisbank + voice/image)_
