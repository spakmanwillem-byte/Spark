# ✅ P1 Bug Fix: Login Trigger Issue

**Bug:** Phrases like "Ik ben blij" were incorrectly triggering the login flow

**Root Cause:**
- `nlp_service.extract_identification()` was too aggressive
- Pattern `r"(?:ik\s+ben)\s+([A-Z][a-z]+)"` matched common words
- No check if user was already logged in
- No validation that the word after "ik ben" was actually a name

**Solution Implemented:**

### 1. Added Common Words Blacklist (`nlp_service.py`)
```python
COMMON_WORDS_BLACKLIST = [
    "blij", "boos", "verdrietig", "bang", "moe", "wakker", "klaar",
    "terug", "weg", "hier", "daar", "zo", "er", "aan", "uit",
    "goed", "slecht", "ok", "oké", "okay", "prima", "top",
    "bezig", "druk", "vrij", "alleen", "samen", "thuis"
]
```

### 2. Stronger Evidence Requirement
Now requires EITHER:
- Naam + sleutelwoord detected
- Naam + masterkey detected  
- Sleutelwoord/masterkey keyword present in text

Won't trigger on just "Ik ben [word]" without context.

### 3. Skip Identification When User Already Logged In (`spark_brain.py`)
```python
# Try to extract identification ONLY if user is NOT already logged in
if not user_data:
    identification = self.nlp.extract_identification(message)
```

## Test Results:

| Input | Expected | Result |
|-------|----------|--------|
| "Ik ben blij" | ❌ Should NOT trigger | ✅ PASS - No trigger |
| "Ik ben moe" | ❌ Should NOT trigger | ✅ PASS - No trigger |
| "Ik ben Willem Spakman sleutelwoord Appelsap" | ✅ SHOULD trigger | ✅ PASS - Login triggered |
| "Ik ben Willem" | ❌ Should NOT trigger (no credential) | ✅ PASS - No trigger |
| "Willem Appelsap" | ✅ SHOULD trigger (2-word pattern) | ✅ PASS - Login triggered |
| "Ik ben klaar" | ❌ Should NOT trigger | ✅ PASS - No trigger |

## End-to-End Test:
1. ✅ Login as Willem → Success (user-001, gradatie 1)
2. ✅ Send "Ik ben blij" while logged in → Emotion response (geen login trigger)
3. ✅ User stays logged in

**Status: ✅ FIXED & TESTED**
