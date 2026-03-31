# 🐛 Common Bug Patterns - Spark Development

Dit document bevat veelvoorkomende bugs en hun oplossingen voor toekomstige reference.

---

## Bug Pattern #1: Incomplete Data Loading in Edit Forms

**Date Found:** 2026-03-18  
**Severity:** HIGH  
**Recurrence:** Multiple times

### Symptoom
- Edit form werkt "gedeeltelijk"
- Sommige velden worden opgeslagen, andere niet
- Data lijkt te verdwijnen na save
- Geen error messages
- Success message wordt wel getoond

### Root Cause
Backend stuurt **incomplete data** naar frontend bij GET request:
- Alleen subset van velden (bijv. id, naam, gradatie)
- Mist nested objects (persoonlijke_info, adres, contact, etc.)

Frontend vult form met deze incomplete data:
- Aanwezige velden: krijgen waarde
- Ontbrekende velden: blijven undefined/empty

Bij save stuurt frontend ALLE velden terug:
- Aanwezige velden: nieuwe waardes ✅
- Ontbrekende velden: **undefined → overschrijft met NULL/empty** ❌

### Voorbeeld Scenario
```javascript
// Backend stuurt:
{
  id: "123",
  naam: "Nick",
  gradatie: 7
  // persoonlijke_info: ONTBREEKT!
}

// Frontend form:
naam: "Nick" ✅
volledige_naam: "" (undefined)
adres: "" (undefined)

// User wijzigt:
naam: "Nicholas" 
volledige_naam: "Nicholas Teeuwen"

// Save stuurt:
{
  naam: "Nicholas", ✅
  volledige_naam: "Nicholas Teeuwen", ✅
  adres: null, ❌ OVERSCHRIJFT bestaande data!
  beroep: null ❌ OVERSCHRIJFT bestaande data!
}
```

### Oplossing Pattern

**Backend Fix (Preferred):**
```python
# ❌ FOUT - Limited fields
def get_items():
    items = []
    for item in all_items:
        items.append({
            "id": item.get("id"),
            "naam": item.get("naam"),
            "status": item.get("status")
        })
    return items

# ✅ CORRECT - Full object
def get_items():
    items = []
    for item in all_items:
        items.append(item)  # Volledige object!
    return items
```

**Frontend Fix (Alternative):**
```javascript
// Als je backend niet kunt wijzigen:
// Laad volledige data apart voor edit
const loadForEdit = async (itemId) => {
  // GET /api/items/{id} voor VOLLEDIGE data
  const fullData = await axios.get(`/api/items/${itemId}`);
  setFormData(fullData);
}

// Niet gebruiken:
const loadForEdit = (item) => {
  setFormData(item); // Kan incomplete zijn!
}
```

### Hoe te Herkennen
1. ✅ Sommige velden saven wel, andere niet
2. ✅ Geen errors maar data verdwijnt
3. ✅ Console toont undefined voor missende velden
4. ✅ Backend response heeft minder velden dan verwacht

### Preventie
- [ ] Altijd volledige object retourneren bij GET endpoints
- [ ] Use TypeScript/Pydantic voor type checking
- [ ] Test edit forms met ALLE velden, niet alleen basis velden
- [ ] Log frontend formData before save (development)
- [ ] Backend validatie: reject null/undefined voor required nested fields

### Files Vaak Betrokken
- Backend: `services/*_service.py` (get_all, get_by_id methods)
- Frontend: `components/*Tab.js` (viewProfile, loadForEdit functions)

### Debug Checklist
1. Check backend GET response: heeft het ALLE velden?
2. Check frontend formData state: zijn alle velden gevuld?
3. Check save payload: wat wordt er gestuurd?
4. Check database: zijn de velden er na save?

---

## Bug Pattern #2: [Template voor volgende bug]

**Date Found:** TBD  
**Severity:** TBD  

### Symptoom
...

### Root Cause
...

### Oplossing
...

---

**Last Updated:** 2026-03-18  
**Maintained by:** Emergent Agent
