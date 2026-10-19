# Onderzoek 19-10-2026 — Emotie-graph & hybride command-systeem
> Alleen bevindingen. Niets gebouwd. (RULE_toets_voor_bouw_001)

---

## 1. Emotie-graph

### Wat staat er al
| Onderdeel | Plek | Stand |
|---|---|---|
| Emotie-veld op kaart | `knowledge_v2_*.json` → top-level `emotie` | **3631 kaarten** (3553 neutraal, 58 blij, 8 bedroefd, 7 bang, 5 boos). Geschreven door `text_importer.py`. **Wordt door niets gelezen.** |
| Geleerde woorden | `emotion_service._load_learned_triggers()` | Leest **alleen tags** (`emotie-blij`, `emotie blij`, of `emotie`+`blij`). Nu **1336** woorden: 1147 neutraal, 120 blij, 34 bang, 23 bedroefd, 11 boos. (Emmy's 1446 is een oudere telling.) Score vast = 3 per woord. Cache 60 s. |
| Statische triggers | `data/triggers/emotion_triggers.json` | 4 emoties met gewogen woorden (blij 5, gelukkig 7, …) + `empathic_responses`. |
| Spark's eigen emoties | `data/emotions/spark_emotions.json` | 5 states (happy/angry/sad/scared/neutral) met sub-emoties (blijdschap→vreugde→euforie, irritatie→woede→razernij…) + XP-modifiers. **Dit is al een mini-emotie-hiërarchie, maar zonder onderlinge edges.** |
| 7-laags pipeline | `modules/emotion_pipeline/pipeline.py` | L1 hergebruikt `detect_emotion`; L2-L7 weging/context/identiteit/bijbel/actie/expressie. Dry-run endpoints; A/B- en shadow-logs tot juni. **Niet in de live chat-flow.** |
| Kennis-graph | `data/graph/nodes.json` (7406) / `edges.json` (**72 934**, allemaal type `related`) | Edges = gedeelde tags, drempel **1 gedeelde tag**. |

### De ruis die Willem vermoedt — bevestigd met cijfers
- Tag `emotie` staat op **1529 kaarten**. In een steekproef van 20 000 edges had **5221 (26 %)** `emotie` als gedeelde tag.
  → Ruwweg een kwart van de kennis-graph is "deze twee kaarten gaan allebei over een emotie" — geen inhoudelijk verband.
- `neutraal` als geleerde emotie (1147 woorden) leert de detector niets: neutraal is de afwezigheid van signaal.

### Wat is nodig voor een aparte emotie-graph
1. **Bron kiezen** — één waarheid: kaartveld `emotie` (bestaat al) óf tags. Advies: **veld**, tags worden eruit afgeleid of verdwijnen. Niet beide.
2. **Veld verrijken** — nu 5 waarden. Voor edges (bang→bedroefd, boos→gefrustreerd) is minimaal nodig: `emotie` (basis) + optioneel `sub_emotie` + `intensiteit` (0-1). `spark_emotions.json` levert de sub-emoties al.
3. **Eigen bestand** — `data/graph/emotion_nodes.json` + `emotion_edges.json`, los van de kennis-graph. Nodes = emoties/sub-emoties (~20) + kaart-koppelingen; edges met types: `escaleert_naar` (irritatie→woede), `verwant` (bang↔bedroefd), `tegenpool` (blij↔bedroefd), `kaart_voelt` (kaart→emotie).
4. **Lezer aanpassen** — `emotion_service._load_learned_triggers()` leest veld i.p.v. tags; `neutraal` niet meer als trigger. Pipeline L2 (weging) kan de edges gebruiken voor "glijdt af naar".
5. **Kennis-graph opschonen** — `emotie` (en `emoties`) uit de tag-overlap halen bij graph-build (`graph/sync_service._shared_tags_count`), of drempel naar 2 gedeelde tags. Dat haalt ~25 % ruis weg.
6. **UI** — Kennisbank-tab "Nog geen emotie" (Willems punt 3) + emotie-dropdown op de kaart. Kleine graph-view later.

### Risico's
- **Detectie verandert.** Nu vuren 1336 woorden met score 3; als het veld bron wordt en `neutraal` wegvalt, vuren er nog ~190. Dat is eerlijker, maar Spark reageert op minder woorden tot het veld gevuld is. Mitigatie: overgangsfase waarin veld én tags gelezen worden, met log welke bron matchte.
- **3553 × neutraal** is geen label maar een default van de importer. Niet als "ingevuld" tellen; voor de tab "Nog geen emotie" telt alleen een bewust gekozen waarde (dus `neutraal` → nog te doen, of apart veld `emotie_bevestigd`).
- **Veld vs tag conflicten**: 1529 kaarten hebben tag `emotie`, 3631 hebben veld — overlap klopt niet overal. Eén migratiepas nodig met rapport.
- **Graph-rebuild** raakt 72 934 edges; backup verplicht (gebeurt al met `.bak_`).
- **Pipeline (L1-L7) zelf blijft heel**: L1 roept `detect_emotion` aan, dus zodra de lezer klopt werkt alles door. Shadow/A-B-logs blijven bruikbaar.

**Conclusie:** goed idee, geen dubbel werk — de bouwstenen (veld, sub-emoties, pipeline) liggen er al los; wat ontbreekt is de verbinding en de edges. Werk ≈ 2 bouwsessies: (a) veld-als-bron + tab, (b) emotie-edges + kennis-graph-ontruising.

---

## 2. Hybride command-systeem

### Wat er nu is — drie lagen die elkaar niet kennen
| Laag | Bestand | Hoe gematcht | Live in chat? |
|---|---|---|---|
| **A. Harde acties** | `action_intents_service.py` + `data/triggers/intent_patterns.json` (17 keys: tts/stt/ambient/agenda_read/note_create/…) + regex `_RX_TTSS` | exacte patronen | ✅ ja (eerste check in chat) |
| **B. Capabilities ("Spark's handen")** | `data/personality/spark_capabilities.json` (**29**, regex-triggers) → `intent_matcher_service` → `capability_handler_service._handle_*` | regex per capability | ✅ ja |
| **C. Command-registry** | `data/system/command_registry.json` (**81**, `intent_tags`) → `intent_registry/extractor` (synoniem→tag) + `matcher` (Jaccard) | tag-overlap | ❌ nee — alleen via `/api/intent-registry/match`, admin-test en `/api/commands/list` |
| **D. task_agent** | `modules/agents/task_agent.py` | `resolve()` → **retourneert altijd None**, `execute()` → **not_implemented**, alleen `list_commands()` werkt | ❌ skeleton |
| E. admin_commands | `data/triggers/admin_commands.json` (say, triggers-menu) | patronen | ✅ (admin) |

### Registry-overzicht (81 entries) — status
- **Route bestaat: 58** · **Route bestaat niet: 23** (v1-wensen zoals `/api/users/count`, `/api/agenda/items`, `/api/trade/buy`, `/api/leaderboard`, `/api/community/messages`, `/api/chat/recap`, `/api/intent-registry/navigate`, `/api/kb/v2/inbox/stats`).
- **Handler-koppeling (source-veld): 58 ja / 23 nee.** De 8 oude `cap_*` (tellen_gebruikers, spark_saldo, gesprek_lezen, toon_afbeelding, …) wijzen naar een handler die bestaat maar naar een pad dat niet bestaat — ze werken via laag B, niet via het pad.
- **Chat-bereikbaar via intent**: alleen de ~13 `cap_*` die ook in `spark_capabilities.json` staan. De 50 nieuwe registry-entries (agenda-events, notes, bugs, help, triggers, kb-admin, connections, commands) hebben **geen chat-trigger** — ze zijn alleen vindbaar met tag-overlap.
- Volledige tabel per command (id · method · path · route · #tags · koppeling · gradatie · source) staat in `/app/memory/COMMANDS_OVERZICHT_19-10.md`.

### Wat Willem wil ("verwijder die foto" = "ruim die map op" = "delete")
Een **concept-laag** tussen zin en registry:
1. `extractor._KEYWORD_MAP` is het begin van zo'n laag (synoniem→tag) maar is klein en plat. Nodig: **werkwoord-concepten** (`verwijderen` = verwijder/delete/weg/ruim op/gooi weg/wis) en **object-concepten** (`foto` = foto/plaatje/afbeelding/image; `map` = map/folder/directory) als bewerkbare JSON (zelfde patroon als `intent_patterns.json`, live-editable via Triggers).
2. `task_agent.resolve(concepten)` → registry-entry op `intent_tags` ∩ concepten + object-type; `execute()` met `gradatie_min`, `required_params`, audit-log — precies de TODO's die al in het bestand staan.
3. **Hybride regel**: laag A (hard, exact) blijft eerst; dan B (bestaande regex-capabilities, ongewijzigd); pas als beide niets geven → C via task_agent. Zo breekt niets wat nu werkt.
4. **Destructieve concepten** (`verwijderen`, `versturen`, `kopen`) altijd met bevestigingsstap — zelfde drie-standen-idee als Berichtenbeheer.

### Risico's
- 23 dode registry-entries moeten eerst **opgeruimd of op `status: placeholder`** gezet worden, anders stuurt task_agent naar 404's.
- Registry heeft geen `status`-veld; de `stats` erin zijn stale (`total_commands: 33` naast `total: 81`).
- Twee matchers met dezelfde naam (`intent_matcher_service.match_capability(text)` vs `intent_registry.matcher.match_capability(tag_vector)`) — verwarrend; één naam hernoemen voordat task_agent ze samenbrengt.
- Concept-matching is gevoeliger voor valse treffers dan regex ("delete" in een kennisvraag over Engels). Drempel + disambiguatie-vraag (bestaat al in matcher: `needs_disambiguation`).

**Conclusie:** haalbaar en geen dubbel werk — de fundering (registry, extractor, matcher, task_agent-skelet) ligt er; wat ontbreekt is de concept-JSON, de `resolve/execute`-body en het inhaken als derde stap in de chat. Eerst registry schoonmaken (status-veld + 23 dode paden), dan pas bouwen.
