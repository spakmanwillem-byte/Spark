# 🔊 Sound System Roadmap

## Huidige Status (v1.0)

### ✅ Wat werkt NU:
- **Globaal systeem**: Alle users horen alle geluiden
- **Willem's controle**: Alle geluiden onder admin beheer
- **Sequentieel afspelen**: Meerdere trigger woorden spelen op volgorde af
  - Voorbeeld: "koe schaap" → 🐄 (wacht) → 🐑
- **Dubbele triggers**: Als user EN Spark beide "koe" zeggen → 2x afspelen
- **Frequency modes**: every, first_only, every_N
- **Volume control**: Master volume slider

### Locaties:
```
/app/backend/data/system/sound_mappings.json  → Alle sound mappings
/app/backend/data/media/sounds/              → Audio bestanden
/app/backend/routes/system_routes.py         → API endpoints
/app/frontend/src/App.js                     → Trigger detection
/app/frontend/src/components/GeluidenTab.js  → Beheer UI
```

---

## Toekomstige Features (v2.0)

### 1. Per-User Geluiden (Privacy)
**Doel:** Elke user kan eigen geluiden toevoegen die alleen zij horen

**Implementatie:**
```javascript
{
  "user_id": "user-123",
  "word": "geheim",
  "visibility": "private",  // NEW: private = alleen deze user
  "file": "..."
}
```

**API Changes:**
- `GET /api/sounds/mappings?user_id=X` → Filter op user_id
- Frontend: Alleen sounds ophalen van eigen user + shared + Spark systeem

---

### 2. Deel Optie (Social)
**Doel:** Users kunnen hun geluiden delen met anderen (opt-in)

**Implementatie:**
```javascript
{
  "user_id": "user-123",
  "word": "cool",
  "visibility": "shared",  // NEW: shared = anderen kunnen ook horen
  "file": "..."
}
```

**UI:**
- Checkbox in GeluidenTab: "✅ Deel met anderen"
- Anderen zien: "🔊 user-123's geluid: cool"

---

### 3. Spark Systeem Geluiden
**Doel:** Spark heeft eigen user_id met geluiden die iedereen hoort

**Implementatie:**
```javascript
{
  "user_id": "spark-system",     // Speciale user ID
  "word": "succes",
  "visibility": "global",        // NEW: global = altijd voor iedereen
  "type": "system",              // system, button, command
  "file": "..."
}
```

**Gebruik cases:**
- Button clicks (✅ opslaan)
- Command sounds (/help activeren)
- Achievement unlocks
- System notifications

---

### 4. Smart Filtering (v2.0)
**Logica per user:**
```
Hoor geluiden van:
1. Eigen private sounds (user_id === current_user)
2. Shared sounds van anderen (visibility === 'shared')
3. Spark systeem sounds (user_id === 'spark-system')
```

**Code sketch:**
```javascript
const getAvailableSounds = (currentUserId) => {
  return sounds.filter(s => 
    s.user_id === currentUserId ||           // Own sounds
    s.visibility === 'shared' ||             // Shared by others
    s.user_id === 'spark-system'             // System sounds
  );
}
```

---

## Implementatie Plan

### Phase 1: Huidige stabilisatie ✅
- [x] Sequentieel afspelen
- [x] Position-based ordering
- [x] Dubbele triggers (user + Spark)

### Phase 2: Visibility System (Later)
- [ ] Add `visibility` field to sound_mappings.json
- [ ] Add `type` field (user, system, button, command)
- [ ] Update API: filter based on visibility
- [ ] UI: Checkbox "Deel met anderen"

### Phase 3: Spark System Sounds (Later)
- [ ] Create `spark-system` user
- [ ] Migrate existing system sounds
- [ ] UI: Systeem geluiden tab (admin only)

### Phase 4: Advanced Features (Later)
- [ ] Sound categories/tags
- [ ] Volume per sound
- [ ] Sound marketplace (users share cool sounds)
- [ ] Sound analytics (most played, etc.)

---

## Technical Notes

### Current Implementation (v1.0)
```javascript
// Detection: App.js line ~248
checkAudioTriggers(message) {
  // 1. Fetch all mappings (global)
  // 2. Find triggers in message
  // 3. Sort by position
  // 4. Play sequentially with await
}

// Sequential play: App.js line ~314
playSoundSequential(filename) {
  return new Promise(resolve => {
    audio.onended = () => resolve();
  });
}
```

### Future Implementation (v2.0)
```javascript
// With user filtering
checkAudioTriggers(message, currentUserId) {
  const allSounds = await fetchSounds();
  const availableSounds = filterByVisibility(allSounds, currentUserId);
  // ... rest same
}
```

---

**Status:** v1.0 Complete ✅  
**Next Milestone:** v2.0 Visibility System (TBD)  
**Owner:** Willem (user-001)
