# 🔍 Knowledge Base Zoekfunctie - Handleiding

## 📋 Lijst van 38 Entries met Korte Laag1

De volledige lijst staat in: `/app/KORTE_LAAG1_ENTRIES.txt`

**Samenvatting:**
- 38 entries hebben een korte laag1 (< 20 karakters)
- De meeste hebben WEL substantiële content in laag2/laag3/laag4
- Voorbeelden: "Microfoon", "Data", "Evenwicht", "Herstel", etc.

**Handmatig beoordelen:**
```bash
cat /app/KORTE_LAAG1_ENTRIES.txt
```

---

## 🔍 Zoekfunctie Gebruik

### Basis Zoeken

**Zoek op begrip:**
```bash
cd /app/backend
python3 scripts/search_kb.py "bewustzijn"
```

**Exacte match:**
```bash
python3 scripts/search_kb.py --exact "Bewustzijn"
```

**Filter op topic:**
```bash
python3 scripts/search_kb.py --topic "sport"
```

**Zoek in lagen content:**
```bash
python3 scripts/search_kb.py --content "motivatie"
```

**Zoek overal (begrip + topic + lagen):**
```bash
python3 scripts/search_kb.py --all "energie"
```

**Zoek op ID:**
```bash
python3 scripts/search_kb.py --id "snap-abc123"
```

### Volledige Output

**Toon volledige lagen (niet alleen preview):**
```bash
python3 scripts/search_kb.py "balk" --full
```

---

## 📖 Voorbeelden

### 1. Vind duplicaten met verschillende topics
```bash
python3 scripts/search_kb.py "balk"
```
**Output:**
- "Balk" - Topic: sport
- "Balk" - Topic: Constructie
✅ Correct: Beide behouden

### 2. Zoek alle sport-gerelateerde kaarten
```bash
python3 scripts/search_kb.py --topic "sport"
```
**Output:** 7 resultaten (honkbal, balk, volleybal, etc.)

### 3. Vind kaarten over "microfoon"
```bash
python3 scripts/search_kb.py --all "microfoon"
```
**Output:** 2 resultaten (Microfoon + Versterker die microfoons noemt)

### 4. Controleer een specifieke entry
```bash
python3 scripts/search_kb.py --id "snap-655a2f0b"
```

### 5. Zoek naar emotie-gerelateerde content
```bash
python3 scripts/search_kb.py --content "emotie"
```

---

## 🎯 Use Cases

### Als een kaart niet goed reageert via NLP:

**1. Zoek de kaart:**
```bash
python3 scripts/search_kb.py "begrip van kaart"
```

**2. Check de ID en content:**
Noteer de ID (bijv. `snap-abc123`)

**3. Vind in JSON:**
```bash
grep -A 30 "snap-abc123" /app/backend/data/learned_knowledge/knowledge_base.json
```

**4. Pas aan:**
- Open JSON bestand
- Zoek op ID
- Wijzig lagen/topic/status
- Sla op

**5. Test:**
```bash
python3 scripts/search_kb.py --id "snap-abc123" --full
```

### Controleer duplicaten:
```bash
# Zoek begrip
python3 scripts/search_kb.py "klem"

# Check topics
# "Klem" - Gereedschap
# "Klem" - Communicatie
# ✅ Beide correct, verschillende betekenissen
```

### Vind lege/korte entries:
```bash
# Check de lijst
cat /app/KORTE_LAAG1_ENTRIES.txt

# Zoek specifieke entry
python3 scripts/search_kb.py "Evenwicht" --full
```

---

## 🔧 Technische Details

**Locatie script:**
`/app/backend/scripts/search_kb.py`

**Knowledge Base:**
`/app/backend/data/learned_knowledge/knowledge_base.json`

**Features:**
- ✅ Zoek op begrip (exact + gedeeltelijk)
- ✅ Filter op topic
- ✅ Doorzoek lagen content
- ✅ Zoek overal (combined search)
- ✅ Zoek op ID
- ✅ Preview mode (default) + full mode
- ✅ Color-coded output (automatisch)
- ✅ Snelle performance (<1 seconde)

**Limitaties:**
- Geen fuzzy matching (exact substring match)
- Case-insensitive zoeken
- Geen regex support (nog)

---

## 💡 Tips

**Snel debuggen NLP issue:**
```bash
# 1. Zoek de kaart
python3 scripts/search_kb.py "begrip"

# 2. Check volledige inhoud
python3 scripts/search_kb.py "begrip" --full

# 3. Check topic
python3 scripts/search_kb.py --topic "topic_naam"

# 4. Zoek gerelateerde kaarten
python3 scripts/search_kb.py --all "keyword"
```

**Vind alle draft/pending entries:**
```bash
python3 -c "
import json
data = json.load(open('/app/backend/data/learned_knowledge/knowledge_base.json'))
drafts = [e for e in data['knowledge_entries'] if e.get('status') in ['draft', 'pending']]
print(f'Drafts/Pending: {len(drafts)}')
for d in drafts[:10]:
    print(f'  - {d.get(\"begrip\")} (ID: {d.get(\"id\")[:15]})')
"
```

**Check status verdeling:**
```bash
python3 -c "
import json
from collections import Counter
data = json.load(open('/app/backend/data/learned_knowledge/knowledge_base.json'))
statuses = Counter(e.get('status', 'unknown') for e in data['knowledge_entries'])
for status, count in statuses.most_common():
    print(f'{status}: {count}')
"
```

---

## ✅ Testfase Checklist

- [x] Lijst van 38 korte laag1 entries gemaakt
- [x] Zoekfunctie geïmplementeerd (begrip + topic + content)
- [x] Voorbeelden getest (balk, sport, microfoon)
- [x] Volledige output mode beschikbaar
- [x] ID search beschikbaar
- [ ] Willem test handmatig
- [ ] Issues rapporteren indien gevonden
- [ ] Na goedkeuring: verder naar MongoDB (indien gewenst)

---

**Klaar voor gebruik! Start met testing en gebruik de zoekfunctie om problematische kaarten te vinden en beoordelen.** 🚀
