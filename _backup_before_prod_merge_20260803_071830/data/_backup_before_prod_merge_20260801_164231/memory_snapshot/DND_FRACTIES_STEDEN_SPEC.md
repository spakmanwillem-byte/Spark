# D&D — Fracties & Steden — Data Format Spec
> Doel: structuur waarbinnen je fracties + steden kan invullen.
> Front + body komt later, dit is het skelet voor wat we gaan verbinden.

---

## 1. Bestand: `data/dnd/fracties.json`

**Bestaat al** met 10 fracties (id/naam/kleur/element/alignment/leider/is_main/beschrijving).

**Uitbreiden met** (per fractie):

```json
{
  "id": "spark",
  "naam": "Spark",
  ...bestaande velden...

  // ↓ NIEUW ↓
  "leider_naam": "Spark",              // expliciete leider-naam
  "leider_user_id": null,              // user die de leider speelt (null = NPC)
  "banner_image_url": null,            // upload-pad voor banner
  "icon_image_url": null,              // klein logo (gebruikt op kaart-marker)
  "introductie": "Lang verhaal...",    // 2-4 zinnen intro op fractie-tab
  "tagline": "Bewaker van de balans",  // 1-regelige slogan

  "stats": {
    "aanhangers_total": 0,             // som over alle steden — auto-berekend
    "leidende_steden_count": 0,        // aantal steden waar deze fractie meeste invloed heeft — auto
    "gebouwen_total": 0,               // som gebouwen die fractie bezit — auto
    "goud": 0                          // fractie-treasury
  },

  "stads_bonus": {                     // bonus die elke fractie-lid krijgt
    "type": "stat_modifier",           // stat_modifier | resource_yield | special
    "scope": "alle_leden",             // alle_leden | leider_only | leidende_stad_only
    "effect": {                        // wat de bonus precies doet
      "kracht": 0,
      "snelheid": 0,
      "wijsheid": 0,
      "gold_per_dag": 0
    },
    "beschrijving": "Tekst die in profile getoond wordt"
  },

  "tax_rate_stad": 0.05,               // % dat fractie aan steden afdraagt (0.0-1.0)
  "tax_rate_leden": 0.02               // % dat leden aan fractie afdragen
}
```

---

## 2. NIEUW Bestand: `data/dnd/steden.json`

Eén centraal bestand met alle dorpen/steden in Stormhaven-wereld.

```json
{
  "steden": [
    {
      "id": "stormhaven",                // unieke slug
      "naam": "Stormhaven",
      "type": "stad",                    // dorp | stad | hoofdstad | gehucht
      "provincie_id": "groningen",       // koppeling naar provincies.json
      "is_hoofdstad_provincie": true,    // hoofdstad van die provincie?

      "kaart": {
        "x_pct": 78,                     // positie op landkaart 0-100
        "y_pct": 18,
        "marker_icon": "castle"          // castle | town | village | ruin
      },

      "introductie": "Stormhaven is...",  // 3-5 zinnen
      "banner_image_url": null,
      "logo_url": null,

      // —— ECONOMIE ——
      "kas": {
        "goud": 0,                        // stadskas
        "tax_inkomsten_dag": 0,           // auto-berekend laatste 24u
        "tax_uitgaven_dag": 0,
        "tax_rate_inwoners": 0.03,        // % belasting van bewoners
        "tax_rate_fracties": 0.05         // % wat fracties afdragen aan stad
      },

      // —— FRACTIE INVLOED ——
      // Elke fractie kan aanhangers hebben. Hoogste = leidende fractie.
      "fractie_invloed": {
        "spark": {"aanhangers": 0, "gebouwen": 0, "tevredenheid": 50},
        "licht": {"aanhangers": 0, "gebouwen": 0, "tevredenheid": 50},
        "schaduw": {"aanhangers": 0, "gebouwen": 0, "tevredenheid": 50},
        "vuur":   {"aanhangers": 0, "gebouwen": 0, "tevredenheid": 50},
        "lucht":  {"aanhangers": 0, "gebouwen": 0, "tevredenheid": 50},
        "water":  {"aanhangers": 0, "gebouwen": 0, "tevredenheid": 50},
        "aarde":  {"aanhangers": 0, "gebouwen": 0, "tevredenheid": 50},
        "natuur": {"aanhangers": 0, "gebouwen": 0, "tevredenheid": 50},
        "barbaren": {"aanhangers": 0, "gebouwen": 0, "tevredenheid": 50}
      },
      "leidende_fractie_id": "spark",    // auto: fractie met meeste aanhangers

      // —— STADSFUNCTIES (gebouwen) ——
      // Elke functie heeft een niveau (0 = niet aanwezig, 1-5 = upgrades)
      "functies": {
        "leger":              {"niveau": 1, "kapitein": null, "soldaten": 0},
        "opslag":             {"niveau": 1, "capaciteit": 1000, "inhoud": {}},
        "bank":               {"niveau": 1, "rente_per_dag": 0.001},
        "forum":              {"niveau": 1},   // gemeentehuis / vergaderplek
        "stadsmuur":          {"niveau": 1, "verdediging_bonus": 5},
        "infrastructuur":     {"niveau": 1, "handel_modifier": 1.0},
        "handelskantoor":     {"niveau": 1, "import_export_slots": 2},
        "tempel":             {"niveau": 0, "fractie_id": null},  // optioneel
        "markt":              {"niveau": 1},                       // koop/verkoop
        "herberg":            {"niveau": 1}                        // sociale plek
      },

      // —— STADS-BONUS voor leidende fractie ——
      "leider_bonus": {
        "beschrijving": "Spark-leden in Stormhaven krijgen +2 wijsheid",
        "effect": {"wijsheid": 2}
      }
    }
  ]
}
```

---

## 3. NIEUW Bestand: `data/dnd/player_fractie_binding.json`

Welke speler is lid van welke fractie + wat is z'n rang.

```json
{
  "bindings": {
    "user-001": {
      "fractie_id": "spark",
      "rang": "leider",                  // grunt | lid | officier | leider
      "lid_sinds": "2026-06-06T...",
      "aanhanger_in_stad_id": "stormhaven",  // in welke stad telt hij mee
      "bijdrage_goud": 0,                // hoeveel goud heeft hij ingelegd
      "loyalty": 100                     // 0-100, voor faction-switching cooldown
    }
  }
}
```

---

## 4. NIEUW Bestand: `data/dnd/gebouwen.json`

Catalogus van gebouwen die fracties kunnen kopen in steden.

```json
{
  "gebouw_types": [
    {
      "id": "tempel_spark",
      "naam": "Tempel van Spark",
      "fractie_id": "spark",
      "kosten_goud": 500,
      "kosten_materiaal": {"hout": 50, "steen": 30},
      "bouwtijd_uren": 12,
      "effect": {
        "aanhangers_per_dag": 1,        // genereert auto-aanhangers
        "tevredenheid_boost": 5
      },
      "max_per_stad": 1
    }
  ]
}
```

---

## 5. Wat ik LATER ga verbinden (geen werk nu, alleen kennen)

### A. Provincies → Steden
- Klik op provincie op landkaart → bark opent
- Bark toont: alle steden in die provincie + hun leidende fractie + populatie
- Klik stad → opent stadsdetail-modal/page

### B. Fracties-tab UI
- Lijst van alle 10 fracties als kaarten (zoals avatar-tab)
- Per kaart: banner + leider + stats (auto-berekend uit steden+gebouwen)
- Klik kaart → fractie-detail-page met:
  - Volledige intro
  - Lijst leidende steden (klikbaar)
  - Aanhangers per stad
  - Stadsbonus uitleg
  - "Word lid"-knop (voor users zonder fractie)

### C. ROAR-economie koppeling
- Stadskas en fractie-treasury zijn **aparte potjes** in `data/financial/` of `data/roar/`
- Tax-cycle draait via een scheduled task (later)
- Bestaand ROAR-systeem blijft voor user-economie; fractie-goud is **D&D-laag**

### D. Stats-aggregatie
- `fractie.stats.aanhangers_total` = sum over alle `steden[].fractie_invloed[fractie_id].aanhangers`
- `fractie.stats.leidende_steden_count` = count waar `leidende_fractie_id == fractie_id`
- Auto-recompute bij elke wijziging via een hook

### E. Stads-bonus toepassing
- Bij elke character-actie/stat-uitlees:
  - Check `player_fractie_binding[user_id].fractie_id`
  - Check welke stad waar die fractie leidt
  - Apply `steden[stad].leider_bonus.effect` op character stats

---

## 6. Wat jij nu kan doen (zonder mij)

1. **Vul `fracties.json` aan** met de nieuwe velden (intro, tagline, banner_url, stads_bonus.beschrijving)
2. **Maak `steden.json`** met je 12 hoofdsteden + dorpen
3. **Vul `gebouwen.json`** met de eerste gebouw-types per fractie

Eén stad per dag vullen is genoeg. Wanneer je voelt *"genoeg data"* kom je terug en bouw ik de UI + mechanica.

---

## 7. Volgorde van bouw (later)

1. **Data-validatie** — schema check op de json bestanden
2. **Read-only Fracties-tab** — toont kaarten met huidige data
3. **Stad-detail bark/modal** — klik op kaart → details
4. **Player-fractie binding flow** — "Word lid" knop + cooldown
5. **Tax-cycle** — scheduled job
6. **Gebouw-bouw flow** — kosten/tijd/voltooiing
7. **Stads-bonus engine** — apply op character stats
8. **Faction-switch + loyalty** — diplomatie laag

---

**Sleutel-koppelpunten met bestaand systeem:**
- `provincies.json` ↔ `steden.json` via `provincie_id`
- `fracties.json` ↔ `steden.json` via `fractie_invloed` keys
- `characters/*` ↔ `player_fractie_binding.json` via `user_id`
- ROAR-economie ↔ stads-kas/fractie-treasury via aparte balans-files (toekomst)
