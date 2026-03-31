# 🧪 TESTFASE INSTRUCTIES - Snap & Ja/Nee Systeem

**Datum:** 26 maart 2026  
**Status:** 🟢 GEREED VOOR TESTING

---

## 📋 Wat is Voorbereid?

### ✅ Verbeterde Logging Geïmplementeerd
Alle snap creation events worden nu uitgebreid gelogd met:
- ❌ **SNAP REJECTED**: Waarom een snap werd geweigerd (inclusief reden)
- ✅ **SNAP CREATED**: Wanneer een snap succesvol is aangemaakt
- ⚠️ **Duplicate waarschuwingen**: Wanneer een begrip al bestaat
- 📝 **Context informatie**: User, begrip, topic, status, ID

**Logging locatie:**
- Console output (`[SNAP DEBUG]` prefix)
- Backend logs: `/var/log/supervisor/backend.out.log`
- Dedicated snap_logger met verschillende levels (WARNING, INFO, ERROR)

---

## 🛠️ Test Tools voor Willem

### 1. **Real-Time Log Monitor** (Aanbevolen tijdens handmatig testen)
```bash
# In een aparte terminal
cd /app/backend
python3 scripts/monitor_snaps.py
```
**Wat doet het:**
- Toont real-time alle snap events
- Color-coded output (rood=rejected, groen=created, geel=duplicate)
- Blijft draaien terwijl je test
- Stop met CTRL+C

### 2. **Bash Script Alternatief** (Sneller)
```bash
cd /app/backend
./scripts/watch_snaps.sh
```

### 3. **Geautomatiseerde Test Suite**
```bash
cd /app/backend
python3 scripts/test_snap_creation.py
```
**Test scenario's:**
- ✅ Lege strings (moet reject)
- ✅ Alleen spaties (moet reject)
- ✅ Stopwords (moet reject)
- ✅ Duplicaten (moet reject met topics)
- ✅ Nieuwe concepten (moet create)
- ✅ Zinsnaps (moet create)
- ✅ Te korte input (moet reject)

**Resultaat laatste run:** 8/8 tests geslaagd ✅

---

## 🎯 Focus Punten voor Handmatig Testen

### 1. **Nieuwe Snaps Maken**
**Test:**
- Gebruik normale chat om nieuwe begrippen te introduceren
- Check of ze correct worden opgeslagen
- Verificeer dat lagen niet leeg blijven (al dan niet door gebruiker ingevuld)

**Verwacht:**
- Snap wordt aangemaakt met begrip, ID, status, user
- Logging: `✅ SNAP CREATED: '...' | ID: snap-...`
- Geen lege begrippen in knowledge base

### 2. **Lege of Foutieve Input**
**Test:**
- Probeer lege strings te versturen
- Probeer alleen spaties
- Probeer stopwords zoals "de", "het", "een"

**Verwacht:**
- Snap wordt geweigerd
- Logging: `❌ SNAP REJECTED: [reden] | Context: ... | User: ...`
- Geen entry aangemaakt in knowledge base

### 3. **Dubbele Begrippen met Verschillende Topics**
**Test:**
- Probeer een bestaand begrip aan te maken (bijv. "Bewustzijn")
- Check of het systeem de bestaande topics toont
- Probeer begrippen zoals "Balk", "Klem", "Verlichting" (deze hebben multiple topics)

**Verwacht:**
- Duplicate wordt geweigerd met melding van bestaande topics
- Logging: `❌ SNAP REJECTED: 'X' bestaat al | Bestaande topics: ['topic1', 'topic2']`
- Verschillende topics blijven behouden (niet verwijderd)

### 4. **Ja/Nee Systeem**
**Test:**
- Gebruik het ja/nee systeem in de chat
- Check of er geen dubbele snaps worden aangemaakt na "ja" antwoord
- Verificeer dat "nee" antwoorden geen entries aanmaken

**Verwacht:**
- Geen dubbele entries na confirmatie
- Alleen 1 snap per bevestiging
- Logging toont duidelijk wat er gebeurt

---

## 📊 Hoe Resultaten Controleren

### Real-time tijdens testen:
```bash
# Terminal 1: Monitor
cd /app/backend
python3 scripts/monitor_snaps.py

# Terminal 2: Test in de UI
# Gebruik de Spark chat normaal
```

### Backend logs direct bekijken:
```bash
# Laatste 50 snap events
tail -n 100 /var/log/supervisor/backend.out.log | grep "SNAP"

# Live volgen
tail -f /var/log/supervisor/backend.out.log | grep "SNAP"
```

### Knowledge base controleren:
```bash
cd /app/backend
python3 scripts/analyze_knowledge_base.py
```

---

## ✅ Checklist voor Willem

- [ ] Start monitor tool (`monitor_snaps.py`) in aparte terminal
- [ ] Test 1: Maak nieuwe snap aan (normaal begrip)
- [ ] Test 2: Probeer lege snap (moet reject)
- [ ] Test 3: Probeer bestaand begrip (moet reject met topics)
- [ ] Test 4: Test ja/nee systeem (geen duplicates)
- [ ] Test 5: Maak zinsnap aan (moet werken)
- [ ] Test 6: Check of "Balk", "Klem" etc. nog beide topics hebben
- [ ] Controleer knowledge base: Geen nieuwe lege entries
- [ ] Controleer logs: Alle rejections zijn gelogd met reden

---

## 🐛 Als er Issues zijn:

### Snap wordt niet geweigerd (maar had dat wel moeten zijn):
1. Check backend logs: `tail -n 50 /var/log/supervisor/backend.out.log`
2. Zoek naar `[SNAP DEBUG]` om te zien wat er gebeurde
3. Controleer of validation logic werd geraakt

### Snap wordt geweigerd (maar had aangemaakt moeten worden):
1. Check de rejection reden in logs
2. Mogelijk is het begrip te kort, een stopword, of bestaat al
3. Check met `analyze_knowledge_base.py` of het begrip al bestaat

### Logging verschijnt niet:
1. Restart backend: `sudo supervisorctl restart backend`
2. Check supervisor status: `sudo supervisorctl status`
3. Check logs: `tail -f /var/log/supervisor/backend.err.log`

### Dubbele snaps na ja/nee:
1. Check logs voor duplicate entry creation
2. Zoek naar concept in knowledge base
3. Dit zou nu NIET meer moeten gebeuren (bug gefixt)

---

## 📝 Wat te Rapporteren na Testing

Geef aan Willem door:
1. **Wat werkt goed:**
   - Welke test scenario's slagen
   - Zijn rejections duidelijk gelogd
   - Werkt ja/nee systeem correct

2. **Wat niet werkt:**
   - Specifieke test case die faalt
   - Error messages uit logs
   - Onverwacht gedrag

3. **Stabiliteit:**
   - Zijn er crashes
   - Blijft alles stabiel tijdens gebruik
   - Performance issues

---

## 🚀 Na Succesvolle Testing

**Als alles stabiel werkt:**
- ✅ Bevestig aan agent dat het goed werkt
- 🔄 Eventueel verder opschonen (als nodig)
- 🗄️ MongoDB migratie voorbereiden (volgende fase)

**Als er issues zijn:**
- 🐛 Meld specifieke problemen
- 📋 Agent kan targeted fixes doen
- 🔄 Re-test na fixes

---

**Succes met testen Willem! 🚀**

*Alle tools zijn klaar en de logging is uitgebreid. Je kunt nu live zien wat er gebeurt met snap creation.*
