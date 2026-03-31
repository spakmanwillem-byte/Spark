# Personal Context System - Debug Logging

## Observatie Mode ACTIEF

Debug logging is nu geactiveerd voor alle entity extraction.

---

## Log Locatie

**Backend logs**: `/var/log/supervisor/backend.err.log`

**Filter commando**:
```bash
tail -100 /var/log/supervisor/backend.err.log | grep "CONTEXT DEBUG"
```

---

## Log Format

```
[CONTEXT DEBUG] ═══════════════════════════════════════
[CONTEXT DEBUG] Input: "Lotus is mijn ex"
[CONTEXT DEBUG] Source: willem
[CONTEXT DEBUG] Pattern MATCHED: "X is mijn Y"
[CONTEXT DEBUG]   → Extracted: name="Lotus", role="ex"
[CONTEXT DEBUG]   → Relation: "ex_partner" (keyword: "ex")
[CONTEXT DEBUG]   → STORED: source=willem, about=Lotus, relation=ex_partner
[CONTEXT DEBUG] ───────────────────────────────────────
[CONTEXT DEBUG] TOTAL EXTRACTED: 1 entities
[CONTEXT DEBUG]   1. ex_partner → about="Lotus", role="ex"
[CONTEXT DEBUG] ═══════════════════════════════════════
```

---

## Wat wordt Gelogd

### ✅ Input
- Originele text
- Source (user_id)

### ✅ Pattern Matching
- Welk pattern matched ("X is mijn Y", "mijn X", etc.)
- Wat werd geëxtraheerd (name, role)

### ✅ Relation Detection
- Welke relatie werd gedetecteerd
- Waarom (welk keyword triggerde)

### ✅ Storage Decision
- STORED: Entity opgeslagen
- SKIPPED: Waarom niet opgeslagen
  - "already extracted with name"
  - "not a known relation keyword"

### ✅ Summary
- Total aantal extracted entities
- Details per entity

---

## Test Resultaten

### ✅ Test 1: Named Person
```
Input: "Lotus is mijn ex"
Pattern: "X is mijn Y" MATCHED
Extracted: name="Lotus", role="ex"
Relation: "ex_partner"
Result: STORED
```

### ✅ Test 2: Unnamed Relation
```
Input: "Mijn moeder belde gisteren"
Pattern: "mijn X" MATCHED
Extracted: role="moeder" (no name)
Relation: "parent"
Result: STORED
```

### ✅ Test 3: False Positive (werk)
```
Input: "Ik ga naar mijn werk"
Pattern: "mijn X" MATCHED
Extracted: role="werk" (no name)
Result: SKIPPED - "werk" not a known relation keyword
```

### ✅ Test 4: False Positive (huis)
```
Input: "Mijn huis is groot"
Pattern: "mijn X" MATCHED
Extracted: role="huis" (no name)
Result: SKIPPED - "huis" not a known relation keyword
```

---

## Hoe te Gebruiken

### 1. Test een zin
```bash
curl -X POST http://localhost:8001/api/context/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id": "willem", "text": "JOUW TESTZIN HIER"}'
```

### 2. Bekijk debug logs
```bash
tail -50 /var/log/supervisor/backend.err.log | grep "CONTEXT DEBUG"
```

### 3. Analyseer
- Triggert het onterecht?
- Wordt de juiste relatie gedetecteerd?
- Wordt het correct opgeslagen of geskipped?

---

## Veelvoorkomende Scenarios

### ✅ Correct Trigger
```
"Mijn broer belde" → STORED (sibling)
"Anna is mijn vriendin" → STORED (friend, about=Anna)
"Mijn oma zei" → STORED (family)
```

### ✅ Correct Skip
```
"Mijn huis" → SKIPPED (niet persoon)
"Mijn werk" → SKIPPED (niet persoon)
"Mijn auto" → SKIPPED (niet persoon)
```

### ⚠️ Mogelijk False Positive
```
"Mijn vriend Tom" → MATCHED als "friend"
  → Maar "vriend" kan ook "boyfriend" zijn
  → Context-afhankelijk, moeilijk te detecteren zonder ML
```

---

## Next Steps (NA observatie)

1. **Verzamel data**: Test met 20-50 echte zinnen
2. **Identificeer false positives**: Welke woorden triggeren onterecht?
3. **Identificeer false negatives**: Welke patronen missen we?
4. **Verfijn keywords**: Toevoegen/verwijderen van relation keywords
5. **Overweeg nieuwe patterns**: Andere zinsbouw die we moeten ondersteunen?

---

## Uitschakelen Debug Logging

Als logs te veel worden, comment deze regels uit in `personal_context_service.py`:
```python
# logger.info(f"[CONTEXT DEBUG] ...")
```

Of filter in production met log level aanpassing.

---

**Status**: Debug logging ACTIEF - klaar voor praktijktest! 🔍
