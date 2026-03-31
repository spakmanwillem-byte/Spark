# 🚀 Personal Context System - Dynamische Roadmap

## Status: Agile Development Mode

**Mindset**: Flow houden + verbeteren tegelijk  
**Approach**: Kleine verbeteringen direct, grote wijzigingen parkeren  
**Data**: Als iets vaker misgaat → meteen licht fixen

---

## ✅ Vandaag Toegevoegd

### 1. Organic Question Opportunity Detection
**Status**: ✅ LIVE (alleen logging)

**Wat het doet**:
- Detecteert wanneer een vraag logisch is
- Logt opportunities zonder user te storen
- Priority levels: LOW / MEDIUM / HIGH

**Opportunities**:
```
MEDIUM: Entity 2x+ zonder naam
  → "Hoe heet je moeder?"

HIGH: Entity 5x+ zonder naam (frequent)
  → "Je hebt het vaak over je moeder, hoe heet zij?"

LOW: Net naam gekregen
  → Potentieel voor natural follow-up
```

**Logs**: `[CONTEXT OPPORTUNITY]` in backend.err.log

### 2. Pattern Uitbreidingen
**Status**: ✅ LIVE

**Nieuwe patterns**:
- `"met mijn X"` → "Ik sprak met mijn vader"
- `"van mijn X"` → "Het huis van mijn moeder"

**Impact**: Vangt meer natuurlijke zinsbouw

---

## 🔧 Known Issues (te fixen)

### Issue 1: Dubbele Extractie
**Probleem**: "Ik sprak met mijn vader" triggert 2x ("mijn X" + "met mijn X")  
**Impact**: Low (merge werkt, maar inefficiënt)  
**Fix**: Dedupliceer extracted entities voor merge  
**Priority**: Low → Fix als het vaker voorkomt

### Issue 2: [Nog geen andere issues]

---

## 📊 Quick Wins (direct toevoegen als nuttig)

### Pattern Expansions (makkelijk)
- [ ] `"naar mijn X"` → "Ik ga naar mijn broer"
- [ ] `"bij mijn X"` → "Ik ben bij mijn oma"
- [ ] `"over mijn X"` → "Vertel eens over je zus"
- [ ] `"X, mijn Y"` → "Tom, mijn beste vriend"

### Keyword Additions (als gemist)
- [ ] Meer aliases (bv. "pap", "mammie", "zussie")
- [ ] Buitenlandse namen (als relevant)
- [ ] Informal variations

### Logging Improvements (als logs rommelig worden)
- [ ] Compactere format
- [ ] Filter levels (DEBUG/INFO/WARNING)
- [ ] Summary per sessie

---

## 🎯 In Progress (actief ontwikkelen)

### Phase 1.5: Question Opportunity Detection
**Status**: ✅ Logging live, 🔄 actual questions NOT YE
T

**Next steps**:
1. ✅ Detect opportunities (DONE)
2. 🔄 Test in praktijk (ongoing)
3. ⏳ Implement asking logic (later)
4. ⏳ Context-aware timing (later)

**Criteria voor "ready"**:
- Geen false positive opportunities
- Timing voelt natuurlijk
- User feedback positief

---

## 🚧 Parked (grote wijzigingen)

### Events & Timeline (Fase 2)
**Wat**: Tijdlijn van wat er gebeurde  
**Wanneer**: Na Fase 1 stabiel is  
**Reden**: Grote scope, aparte collection nodig

### Emotions (Fase 3)
**Wat**: Emoties per entity/event  
**Wanneer**: Na Events werkend zijn  
**Reden**: Vereist sentiment analysis

### Pattern Detection (Fase 4)
**Wat**: Gedragspatronen herkennen  
**Wanneer**: Na genoeg data verzameld  
**Reden**: Vereist ML/stats

---

## 📈 Metrics (wat we meten)

### Extraction Accuracy
- **True Positives**: Correct gedetecteerd
- **False Positives**: Onterecht getriggerd
- **False Negatives**: Gemist maar had gemoeten
- **Correct Skips**: Pattern matched maar correct geskipped

### Opportunity Quality
- **Relevant**: Vraag past bij context
- **Timing**: Vraag op goed moment
- **User Response**: Wordt vraag beantwoord?

### System Health
- **Deduplication**: Werkt merge correct?
- **Storage**: Groeit profiel organisch?
- **Performance**: Response times < 200ms

---

## 🔄 Update Cycle

**Daily** (als actief in gebruik):
- Check logs voor nieuwe issues
- Quick fixes waar nodig
- Pattern additions als patterns gemist worden

**Weekly**:
- Review collected data
- Identify trends
- Plan next improvements

**Monthly**:
- Major feature additions (if ready)
- Performance optimization
- Refactoring (if needed)

---

## 💡 Insights from Testing

### Good (behouden)
- ✅ "Mijn X" pattern werkt goed
- ✅ Deduplicatie via aliases werkt
- ✅ False positive filtering (werk, huis) werkt

### Bad (fix needed)
- ⚠️ [Nog geen echte issues, observatie ongoing]

### Ugly (awkward)
- 🤔 [Nog geen awkward moments gedetecteerd]

---

## 🎯 Current Priority

**Focus**: Observatie + kleine verbeteringen  
**Goal**: Stabiel, betrouwbaar extraction systeem  
**Timeline**: Ongoing - geen deadline

**Next Milestone**: 
- 50+ test conversaties
- <5% false positives
- >90% pattern coverage
- Question opportunities feel natural

---

## 📝 Notes

- **140 credits beschikbaar** - ruimte voor experimenten
- **Agile approach** - iteratief verbeteren
- **Data-driven** - beslissingen o.b.v. observatie
- **User-centric** - natuurlijke flow > perfectie

**Last Updated**: 2026-03-20  
**Version**: 1.5 (Observation + Opportunities)
