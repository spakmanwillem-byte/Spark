# Spark Design Patterns & Principles

**Documentatie voor toekomstige agents die aan Spark werken**

---

## 🎯 Core Principle: Graceful Degradation over "I Don't Know"

**Bedacht door:** #DeWillem  
**Datum:** 11 maart 2026  
**Geïmplementeerd in:** v3.3 - Knowledge Fallback System

### Het Concept

Wanneer Spark een vraag niet specifiek kan beantwoorden, **stap dan terug** naar algemene kennis in plaats van alleen "ik weet het niet" te zeggen.

### Voorbeeld

**Vraag:** "Wat eten we vanavond?"

**SLECHT (oude manier):**
> "Dat weet ik niet."

**GOED (nieuwe manier - #DeWillem principe):**
> "Ik ken nog geen specifieke gerechten, maar **eten is voeding tot je nemen** om energie te krijgen. Wil je dat ik recepten leer?"

### Waarom Dit Werkt

1. **Geeft context** - Gebruiker leert iets, zelfs als het niet exact is wat ze zochten
2. **Toont begrip** - Spark snapt het onderwerp, heeft alleen geen specifieke details
3. **Biedt groei** - Vraagt of het geleerd kan worden
4. **Respectvol** - Beter dan "no clue" response

---

## 📐 Conceptuele Hiërarchie

```
ALGEMEEN (abstract)
    ↑ STAP TERUG bij geen specifiek antwoord
    |
  CONCEPT (definitie)
    |
    ↓ STAP VOORUIT bij wel kennis
SPECIFIEK (voorbeelden)
```

**Strategie:**
- Vraag is specifiek → Probeer specifiek antwoord
- Niet gevonden? → **Stap terug** naar algemeen begrip
- Geef context + leer-prompt

---

## 🛠️ Implementatie

### Service: `KnowledgeFallbackService`

**Locatie:** `/app/backend/services/knowledge_fallback_service.py`

**Kern functie:**
```python
def create_fallback_response(query: str, detected_concept: str) -> Optional[str]:
    """
    Stap terug naar algemene definitie als specifiek antwoord ontbreekt
    
    Returns: "Ik ken nog geen {specifiek}, maar {algemene definitie}"
    """
```

**Methodes:**
1. `get_general_definition()` - Haal laag1 definitie op
2. `find_related_by_tags()` - Vind gerelateerde concepten via tags
3. `create_fallback_response()` - Genereer graceful fallback

### Integratie in spark_brain.py

```python
# Als normale knowledge lookup faalt:
if content_analysis and content_analysis.keywords.topics:
    for topic in content_analysis.keywords.topics[:2]:
        fallback_response = KnowledgeFallbackService.create_fallback_response(
            query=message,
            detected_concept=topic
        )
        if fallback_response:
            return fallback_response
```

---

## 🎨 Toepassing in Andere Contexten

Dit principe is breder toepasbaar:

### 1. **Gerechten/Recepten**
- Vraag: "Wat eten we?"
- Geen recepten → Stap terug naar "eten = voeding opnemen"

### 2. **Technische Details**
- Vraag: "Hoe werkt een Tesla batterij?"
- Geen Tesla kennis → Stap terug naar "batterij = energie opslag"

### 3. **Persoonlijke Info**
- Vraag: "Wanneer is mijn moeder jarig?"
- Niet opgeslagen → Stap terug naar "verjaardag = feestdag geboorte"
- + "Wil je dat ik dit onthoud?"

### 4. **Events/Agenda**
- Vraag: "Wat staat er morgen op de planning?"
- Geen events → Stap terug naar "planning = toekomst organiseren"
- + "Zal ik je helpen plannen?"

---

## 💡 Gerelateerde Patronen

### 1. **Context Awareness** (#DeWillem principe uitbreiding)
Gebruik gedetecteerde topics om proactief kennis aan te bieden:

```python
# Als we het onderwerp kennen maar de vraag niet kunnen beantwoorden:
if topic in knowledge_base:
    return f"Ik kon je vraag niet precies beantwoorden, maar ik weet wel iets over {topic}. Wil je daar meer over weten?"
```

### 2. **Bidirectional Knowledge Traversal**
Stap zowel TERUG (naar algemeen) als VOORUIT (naar specifiek):

```
Algemeen ← STAP TERUG ← Concept → STAP VOORUIT → Specifiek
```

---

## 📚 Filosofie: Spark's Approach

**Kerngedachte:**
> "Beter een algemeen antwoord met context, dan een lege response."

**Vergelijk met mensen:**
- Mens: "Wat eten we?"
- Vriend: "Weet ik niet precies, maar wat dacht je van Italiaans? Of Chinees?"
  
Spark moet **ook** zo reageren: niet weten, maar wel helpen.

---

## 🚀 Voor Toekomstige Agents

### Wanneer Graceful Fallback Toepassen?

✅ **JA:**
- User vraagt iets specifieks dat je niet hebt
- Je kent wel het algemene onderwerp
- Je kunt context geven die helpt

❌ **NEE:**
- User vraagt naar totaal onbekend concept
- Geen enkele kennis beschikbaar
- Fallback zou verwarrend zijn

### Best Practices

1. **Check altijd eerst specifiek** - Fallback is tweede keus
2. **Geef nuttige context** - Niet alleen herhalen wat ze al zeggen
3. **Bied groei** - Vraag of je mag leren
4. **Wees eerlijk** - "Ik ken nog geen..." niet "Hier is het antwoord..."

### Code Richtlijnen

```python
# GOED: Duidelijke fallback
"Ik ken nog geen {specifiek}, maar {algemeen}. Wil je dat ik dit leer?"

# SLECHT: Onduidelijk
"Misschien bedoel je {iets randoms}?"

# SLECHT: Te vaag
"Daar weet ik niet veel van."
```

---

## 📊 Impact Metrics

**Sinds implementatie (v3.3):**
- Minder "ik weet het niet" responses ✅
- Meer contextuele antwoorden ✅
- Betere user experience ✅
- Meer leer-opportunities ✅

---

## 🏆 Credits

**Concept:** #DeWillem  
**Implementatie:** v3.3 (11-03-2026)  
**Services:** `KnowledgeFallbackService`, `EventExtractionService`  
**Filosofie:** "Stap terug en geef context"

---

## 🔮 Toekomstige Uitbreidingen

1. **Multi-level fallback** - Meerdere stappen terug als nodig
2. **Graph-based fallback** - Gebruik knowledge graph voor slimmere fallback
3. **Learning from fallbacks** - Track welke fallbacks leiden tot vragen → prioriteer leren
4. **Personality-aware fallback** - Pas toon aan op basis van Spark's emotie

---

**Last Updated:** 11 maart 2026  
**Pattern Owner:** #DeWillem  
**Status:** ✅ Active in Production (v3.3+)
