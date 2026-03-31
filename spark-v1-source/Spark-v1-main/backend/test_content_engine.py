"""
Test script voor Content Engine

Test de modulaire opzet en controleer of alle analyzers correct werken.
"""
from services.content_engine import ContentEngine

def test_content_engine():
    """Test verschillende scenario's"""
    
    engine = ContentEngine()
    
    print("=" * 60)
    print("CONTENT ENGINE MODULE TEST")
    print("=" * 60)
    
    # Test 1: Simpele vraag
    print("\n📝 TEST 1: Simpele vraag")
    print("-" * 60)
    text1 = "Wat is een auto?"
    analysis1 = engine.analyze(text1)
    
    print(f"Input: {text1}")
    print(f"\nPrimary Intent: {analysis1.intent.primary_intent}")
    print(f"Is Question: {analysis1.intent.is_question}")
    print(f"Question Type: {analysis1.intent.question_type}")
    print(f"Primary Topic: {analysis1.primary_topic}")
    print(f"Keywords: {analysis1.keywords.primary_keywords}")
    print(f"Tone: {analysis1.tone}")
    print(f"Sentiment: {analysis1.sentiment}")
    print(f"Confidence: {analysis1.confidence:.2f}")
    print(f"Processing Time: {analysis1.processing_time_ms}ms")
    
    # Test 2: Compliment
    print("\n\n📝 TEST 2: Compliment")
    print("-" * 60)
    text2 = "Bedankt Spark! Je bent geweldig!"
    analysis2 = engine.analyze(text2)
    
    print(f"Input: {text2}")
    print(f"\nPrimary Intent: {analysis2.intent.primary_intent}")
    print(f"Has Compliment: {analysis2.compliments.has_compliment}")
    print(f"Compliment Type: {analysis2.compliments.compliment_type}")
    print(f"Compliment Intensity: {analysis2.compliments.compliment_intensity:.2f}")
    print(f"Compliment Targets: {analysis2.compliments.targets}")
    print(f"Tone: {analysis2.tone}")
    print(f"Sentiment: {analysis2.sentiment}")
    print(f"Uses Emoji: {analysis2.language_style.uses_emoji}")
    print(f"Uses Punctuation Emphasis: {analysis2.language_style.uses_punctuation_emphasis}")
    
    # Test 3: Command
    print("\n\n📝 TEST 3: Command")
    print("-" * 60)
    text3 = "Laat de roadmap zien"
    analysis3 = engine.analyze(text3)
    
    print(f"Input: {text3}")
    print(f"\nPrimary Intent: {analysis3.intent.primary_intent}")
    print(f"Is Command: {analysis3.intent.is_command}")
    print(f"Command Type: {analysis3.intent.command_type}")
    print(f"Tone: {analysis3.tone}")
    
    # Test 4: Teaching
    print("\n\n📝 TEST 4: Teaching")
    print("-" * 60)
    text4 = "Onthoud dit: auto's hebben vier wielen"
    analysis4 = engine.analyze(text4)
    
    print(f"Input: {text4}")
    print(f"\nPrimary Intent: {analysis4.intent.primary_intent}")
    print(f"Is Teaching: {analysis4.intent.is_teaching}")
    print(f"Teaching Signal: {analysis4.intent.teaching_signal}")
    print(f"Primary Topic: {analysis4.primary_topic}")
    print(f"Keywords: {analysis4.keywords.primary_keywords}")
    
    # Test 5: Emotional/Urgent
    print("\n\n📝 TEST 5: Urgent/Emotional")
    print("-" * 60)
    text5 = "HELP!!! Mijn systeem werkt niet!!!"
    analysis5 = engine.analyze(text5)
    
    print(f"Input: {text5}")
    print(f"\nTone: {analysis5.tone}")
    print(f"Sentiment: {analysis5.sentiment}")
    print(f"Uses Capitals: {analysis5.language_style.uses_capitals}")
    print(f"Uses Punctuation Emphasis: {analysis5.language_style.uses_punctuation_emphasis}")
    print(f"Emotional Intensity: {analysis5.language_style.emotional_intensity:.2f}")
    print(f"Formality Level: {analysis5.language_style.formality_level:.2f}")
    
    # Test 6: Casual/Playful
    print("\n\n📝 TEST 6: Casual/Playful")
    print("-" * 60)
    text6 = "Hey! Hoe gaat het? 😊 Haha leuk dit"
    analysis6 = engine.analyze(text6)
    
    print(f"Input: {text6}")
    print(f"\nTone: {analysis6.tone}")
    print(f"Sentiment: {analysis6.sentiment}")
    print(f"Uses Emoji: {analysis6.language_style.uses_emoji}")
    print(f"Formality Level: {analysis6.language_style.formality_level:.2f}")
    print(f"Word Count: {analysis6.language_style.word_count}")
    print(f"Question Count: {analysis6.language_style.question_count}")
    
    # Test 7: Stop woorden (importance)
    print("\n\n📝 TEST 7: Stop woorden / Important signals")
    print("-" * 60)
    text7 = "Luister goed, dit is CRUCIAAL voor mijn toekomst"
    analysis7 = engine.analyze(text7)
    
    print(f"Input: {text7}")
    print(f"\nHas Stop Words: {analysis7.keywords.has_stop_words}")
    print(f"Stop Words Found: {analysis7.keywords.stop_words_found}")
    print(f"Importance Score: {analysis7.keywords.importance_score}")
    print(f"Uses Capitals: {analysis7.language_style.uses_capitals}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    test_content_engine()
