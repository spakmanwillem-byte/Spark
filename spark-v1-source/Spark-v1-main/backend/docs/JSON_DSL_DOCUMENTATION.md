# JSON DSL Scripting System - Documentatie

## Overzicht
Veilig JSON-based scripting systeem ter vervanging van `exec()`/`eval()` endpoints.

**Status:** ✅ **PRODUCTION READY**  
**Geïmplementeerd:** 2026-03-30  
**Security Level:** HIGH (whitelisted actions only, geen code injection mogelijk)

---

## Architectuur

### Core Files
- **Handler:** `/app/backend/services/scripting_handler.py`  
  Centrale dispatcher met action whitelist en validatie
  
- **Routes:** `/app/backend/routes/scripting_routes.py`  
  FastAPI endpoints voor JSON DSL execution

### Request Format
```json
{
  "action": "create_trade",
  "params": {
    "action": "BUY",
    "amount": 10,
    "symbol": "BCH-EUR"
  },
  "user_id": "001"
}
```

### Response Format
```json
{
  "success": true/false,
  "result": { /* Action-specific data */ },
  "error": "Optional error message",
  "action": "create_trade",
  "timestamp": "2026-03-30T18:25:32.216569"
}
```

---

## Beschikbare Acties

### 1. `create_trade`
**Beschrijving:** Trigger een manual trade (BUY/SELL)

**Parameters:**
- `action` (required): "BUY" of "SELL"
- `amount` (required): Trade amount in EUR
- `symbol` (optional): Trading pair (default: "BCH-EUR")
- `run_id` (optional): Monitor run ID (genereert automatisch)

**Voorbeeld:**
```bash
curl -X POST "https://spark-foundation.preview.emergentagent.com/api/scripting/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "create_trade",
    "params": {
      "action": "BUY",
      "amount": 5,
      "symbol": "BCH-EUR"
    },
    "user_id": "001"
  }'
```

**Response:**
```json
{
  "success": true,
  "result": {
    "success": true,
    "order_id": "MOCK-BUY-1001",
    "market": "BCH-EUR",
    "filled": 5.0,
    "price": 403.67,
    "mock": true
  },
  "error": null,
  "action": "create_trade"
}
```

---

### 2. `get_position_state`
**Beschrijving:** Haal position state op voor een run

**Parameters:**
- `run_id` (required): Run ID
- `symbol` (optional): Trading symbol (default: "BCH")

**Voorbeeld:**
```bash
curl -X POST "https://spark-foundation.preview.emergentagent.com/api/scripting/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "get_position_state",
    "params": {
      "run_id": "run_user-001_BCH_1774489771"
    },
    "user_id": "001"
  }'
```

**Response:**
```json
{
  "success": true,
  "result": {
    "run_id": "run_user-001_BCH_1774489771",
    "symbol": "BCH",
    "position": {
      "is_open": true,
      "entry_price": 408.85,
      "entry_amount": 0.01150726,
      "entry_time": "2026-03-26T01:50:50.431628"
    }
  }
}
```

---

### 3. `log_action`
**Beschrijving:** Log een custom actie

**Parameters:**
- `action` (required): Action naam
- `entity_type` (required): Type entity
- `entity_id` (required): Entity ID
- `details` (optional): Extra details object

**Voorbeeld:**
```bash
curl -X POST "https://spark-foundation.preview.emergentagent.com/api/scripting/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "log_action",
    "params": {
      "action": "CUSTOM_ACTION",
      "entity_type": "trading",
      "entity_id": "trade_123",
      "details": {"note": "Manual trade executed"}
    },
    "user_id": "001"
  }'
```

---

### 4. `calculate`
**Beschrijving:** Veilige math calculation via AST parsing

**Parameters:**
- `expression` (required): Math expression

**Toegestane operaties:**
- Arithmetic: `+`, `-`, `*`, `/`, `%`, `**`
- Numbers: integers en floats
- **GEEN** functies, imports, of variables

**Voorbeeld:**
```bash
curl -X POST "https://spark-foundation.preview.emergentagent.com/api/scripting/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "calculate",
    "params": {
      "expression": "100 * 0.05"
    },
    "user_id": "001"
  }'
```

**Response:**
```json
{
  "success": true,
  "result": {
    "expression": "100 * 0.05",
    "value": 5.0
  }
}
```

---

## API Endpoints

### `POST /api/scripting/execute`
Execute een JSON DSL command

**Request Body:** `ScriptRequest` (zie Request Format)  
**Response:** Execution result

### `GET /api/scripting/actions`
Lijst van alle beschikbare acties met documentatie en voorbeelden

**Response:**
```json
{
  "success": true,
  "actions": {
    "create_trade": { /* docs */ },
    "get_position_state": { /* docs */ },
    "log_action": { /* docs */ },
    "calculate": { /* docs */ }
  }
}
```

---

## Security Features

### ✅ Whitelisting
Alleen expliciet toegestane acties worden uitgevoerd. Onbekende acties worden direct geweigerd.

### ✅ Input Validatie
Alle parameters worden gevalideerd voordat execution plaatsvindt.

### ✅ AST Parsing (calculate)
Math expressions worden geparsed naar AST en gevalideerd. Geen `eval()` of `exec()`.

**Geblokkeerde keywords:**
- `import`, `exec`, `eval`, `__import__`, `open`, `file`

**Toegestane AST nodes:**
- `BinOp`, `UnaryOp`, `Num`, `Constant`, `Add`, `Sub`, `Mult`, `Div`, `Mod`, `Pow`

### ✅ Error Handling
Alle errors worden veilig afgevangen en gelogd via SparkLogger.

---

## Extensibility

### Nieuwe Actie Toevoegen

1. **Voeg toe aan whitelist:**
```python
ALLOWED_ACTIONS = {
    "create_trade",
    "get_position_state",
    "log_action",
    "calculate",
    "your_new_action"  # ← Add hier
}
```

2. **Implementeer handler:**
```python
@classmethod
def _handle_your_new_action(cls, user_id: str, params: Dict) -> Dict:
    """Handler voor nieuwe actie"""
    # Validatie
    if "required_param" not in params:
        return cls._error_response("Missing param")
    
    # Logic
    result = do_something(params)
    
    return {
        "success": True,
        "result": result,
        "error": None
    }
```

3. **Voeg toe aan dispatcher:**
```python
if action == "your_new_action":
    result = cls._handle_your_new_action(user_id, params)
```

4. **Update documentatie in `get_available_actions()`**

---

## Testing Results

**Datum:** 2026-03-30  
**Status:** ✅ ALL TESTS PASSED

| Test | Actie | Result |
|------|-------|--------|
| 1 | GET /api/scripting/actions | ✅ PASS |
| 2 | calculate: `100 * 0.05` | ✅ PASS (result: 5.0) |
| 3 | calculate: malicious input | ✅ PASS (blocked) |
| 4 | log_action | ✅ PASS (logged to action_log.json) |
| 5 | get_position_state | ✅ PASS (position data returned) |
| 6 | create_trade: BUY | ✅ PASS (mock order executed) |
| 7 | create_trade: SELL | ✅ PASS (mock order executed) |
| 8 | Invalid action rejection | ✅ PASS (error returned) |

---

## Migration Notes

### Oude Endpoints (DEPRECATED)
- ❌ `POST /api/scripting/execute` (oude exec() format)
- ❌ `POST /api/scripting/calculate` (oude eval() format)
- ❌ `GET /api/scripting/functions`

### Nieuwe Endpoints
- ✅ `POST /api/scripting/execute` (nieuwe JSON DSL format)
- ✅ `GET /api/scripting/actions`

### Backwards Compatibility
**BREAKING CHANGE:** Oude `code` field wordt niet meer geaccepteerd.

**Migratie voorbeeld:**
```javascript
// OUD (WERKT NIET MEER)
fetch('/api/scripting/execute', {
  method: 'POST',
  body: JSON.stringify({
    code: 'print("hello")',
    user_id: '001'
  })
})

// NIEUW
fetch('/api/scripting/execute', {
  method: 'POST',
  body: JSON.stringify({
    action: 'log_action',
    params: {
      action: 'CUSTOM_LOG',
      entity_type: 'script',
      entity_id: 'test',
      details: {message: 'hello'}
    },
    user_id: '001'
  })
})
```

---

## Volgende Stappen (Toekomst)

### Fase 2: Uitbreiding (NA Step 2-6 van Structureel Plan)
- [ ] Knowledge acties: `query_knowledge`, `unlock_achievement`
- [ ] AI acties: `generate_response`, `analyze_sentiment`
- [ ] Permission system: Gradatie-based action restrictions
- [ ] Plugin architecture: Dynamisch laden van action modules

### Fase 3: Advanced Features
- [ ] Batch execution: Meerdere acties in 1 request
- [ ] Async execution: Long-running acties met callbacks
- [ ] Scheduling: Tijdgestuurde execution
- [ ] Audit trail: Volledige history van alle executions

---

## Troubleshooting

### "Action not allowed" error
**Probleem:** Actie staat niet in whitelist  
**Oplossing:** Check `ALLOWED_ACTIONS` in `scripting_handler.py`

### "Could not fetch price" error
**Probleem:** Bitvavo API niet bereikbaar  
**Oplossing:** Voor mock trading wordt fallback price (400 EUR) gebruikt. Voor real trading: check internet connectie en Bitvavo API status.

### "Position state not found" error
**Probleem:** run_id bestaat niet  
**Oplossing:** Check bestaande runs in `/app/backend/data/live_trading/user-{user_id}/runs/`

---

## Contact & Support

**Ontwikkelaar:** E1 (Emergent Agent)  
**Datum:** 2026-03-30  
**Versie:** 1.0.0  
**Status:** ✅ Production Ready
