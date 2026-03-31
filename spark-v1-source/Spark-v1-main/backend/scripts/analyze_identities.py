#!/usr/bin/env python3
"""
Identity Data Analysis Script
Doel: Analyseer alle identity-gerelateerde data voor Spark, Willem, en Roadkill
"""

import json
import re
from pathlib import Path
from collections import defaultdict

BACKEND_DATA = Path('/app/backend/data')
KB_PATH = BACKEND_DATA / 'learned_knowledge' / 'knowledge_base.json'
USERS_PATH = BACKEND_DATA / 'system' / 'users.json'

def load_knowledge_base():
    """Laad knowledge base"""
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_users():
    """Laad users.json"""
    with open(USERS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def search_kb_for_identity(kb_data, search_terms):
    """Zoek KB entries voor specifieke identity"""
    
    entries = kb_data.get('knowledge_entries', [])
    found = []
    
    for entry in entries:
        begrip = entry.get('begrip', '').lower()
        
        # Check begrip
        for term in search_terms:
            if term.lower() in begrip:
                found.append(entry)
                break
        
        # Check lagen content
        lagen = entry.get('lagen', {})
        for layer_content in lagen.values():
            if not layer_content:
                continue
            layer_lower = str(layer_content).lower()
            for term in search_terms:
                if term.lower() in layer_lower:
                    if entry not in found:
                        found.append(entry)
                    break
    
    return found

def analyze_identity_spark(kb_data):
    """Analyseer Spark identity"""
    
    print("\n" + "="*70)
    print("🤖 SPARK IDENTITY ANALYSE")
    print("="*70)
    
    search_terms = ['spark', 'ai', 'assistent', 'helper']
    entries = search_kb_for_identity(kb_data, search_terms)
    
    print(f"\n📊 Gevonden: {len(entries)} KB entries over Spark")
    
    # Categorize
    categories = {
        'missie': [],
        'visie': [],
        'gedrag': [],
        'doelen': [],
        'relaties': []
    }
    
    keywords_map = {
        'missie': ['missie', 'purpose', 'doel', 'waarom'],
        'visie': ['visie', 'toekomst', 'droom', 'ideaal'],
        'gedrag': ['gedrag', 'style', 'persoonlijkheid', 'karakter'],
        'doelen': ['doel', 'goal', 'streven', 'ambitie'],
        'relaties': ['relatie', 'gebruiker', 'willem', 'interactie']
    }
    
    for entry in entries:
        begrip = entry.get('begrip', '')
        lagen = entry.get('lagen', {})
        
        # Categorize based on content
        for category, keywords in keywords_map.items():
            for keyword in keywords:
                if any(keyword in str(v).lower() for v in lagen.values() if v):
                    categories[category].append({
                        'begrip': begrip,
                        'entry': entry
                    })
                    break
    
    # Print results
    for category, items in categories.items():
        print(f"\n{category.upper()}: {len(items)} entries")
        for item in items[:3]:
            print(f"   • {item['begrip']}")
        if len(items) > 3:
            print(f"   ... en {len(items) - 3} andere")
    
    # Check system files
    print("\n📁 System Files Check:")
    spark_files = list(Path('/app').rglob('*Spark*.txt'))
    for f in spark_files:
        print(f"   • {f.relative_to(Path('/app'))}")
    
    return {
        'kb_entries': entries,
        'categories': categories,
        'total': len(entries)
    }

def analyze_identity_willem(kb_data, users_data):
    """Analyseer Willem identity"""
    
    print("\n" + "="*70)
    print("👤 WILLEM IDENTITY ANALYSE")
    print("="*70)
    
    # KB search
    search_terms = ['willem', 'de willem', 'spakman']
    entries = search_kb_for_identity(kb_data, search_terms)
    
    print(f"\n📊 Gevonden: {len(entries)} KB entries over Willem")
    
    # Users.json check
    willem_users = [u for u in users_data if isinstance(u, dict) and 
                    ('willem' in u.get('naam', '').lower() or 
                     'spakman' in u.get('naam', '').lower())]
    
    print(f"👥 Users.json: {len(willem_users)} Willem-gerelateerde users")
    for user in willem_users:
        if isinstance(user, dict):
            print(f"   • {user.get('naam', 'N/A')} (ID: {user.get('id', 'N/A')})")
    
    # Categorize KB entries
    categories = {
        'persoonlijk': [],
        'professioneel': [],
        'relaties': [],
        'voorkeuren': []
    }
    
    for entry in entries:
        begrip = entry.get('begrip', '')
        topic = entry.get('topic', '')
        tags = entry.get('tags', [])
        
        # Simple categorization based on topic/tags
        if any(kw in topic.lower() for kw in ['persoon', 'bio', 'profiel']):
            categories['persoonlijk'].append(begrip)
        elif any(kw in topic.lower() for kw in ['werk', 'beroep', 'project']):
            categories['professioneel'].append(begrip)
        elif any(kw in str(tags).lower() for kw in ['relatie', 'contact']):
            categories['relaties'].append(begrip)
        else:
            categories['voorkeuren'].append(begrip)
    
    for category, items in categories.items():
        print(f"\n{category.upper()}: {len(items)} entries")
        for item in items[:5]:
            print(f"   • {item}")
    
    return {
        'kb_entries': entries,
        'users': willem_users,
        'categories': categories,
        'total': len(entries)
    }

def analyze_identity_roadkill(kb_data, users_data):
    """Analyseer Roadkill identity"""
    
    print("\n" + "="*70)
    print("🎮 ROADKILL IDENTITY ANALYSE")
    print("="*70)
    
    # KB search
    search_terms = ['roadkill', 'gamertag', 'shop']
    entries = search_kb_for_identity(kb_data, search_terms)
    
    print(f"\n📊 Gevonden: {len(entries)} KB entries over Roadkill")
    
    # Show entries
    for entry in entries[:10]:
        begrip = entry.get('begrip', '')
        entry_type = entry.get('metadata', {}).get('type', 'unknown')
        print(f"   • {begrip} (type: {entry_type})")
    
    # Check for bio type
    bio_entries = [e for e in entries if e.get('metadata', {}).get('type') == 'bio']
    print(f"\n📋 Bio entries: {len(bio_entries)}")
    for entry in bio_entries:
        print(f"   • {entry.get('begrip')}")
        metadata = entry.get('metadata', {})
        if 'email' in metadata:
            print(f"     Email: {metadata['email']}")
        if 'website' in metadata:
            print(f"     Website: {metadata['website']}")
    
    return {
        'kb_entries': entries,
        'bio_entries': bio_entries,
        'total': len(entries)
    }

def check_duplicates_and_conflicts(spark_data, willem_data, roadkill_data):
    """Check voor duplicaten en tegenstrijdigheden"""
    
    print("\n" + "="*70)
    print("🔍 DUPLICATEN & CONFLICTEN CHECK")
    print("="*70)
    
    # Check overlap tussen identiteiten
    all_begrippen = {}
    all_begrippen['spark'] = [e.get('begrip', '') for e in spark_data['kb_entries']]
    all_begrippen['willem'] = [e.get('begrip', '') for e in willem_data['kb_entries']]
    all_begrippen['roadkill'] = [e.get('begrip', '') for e in roadkill_data['kb_entries']]
    
    # Find overlaps
    print("\n📊 Overlap tussen identiteiten:")
    
    spark_willem = set(all_begrippen['spark']) & set(all_begrippen['willem'])
    if spark_willem:
        print(f"\n   Spark ↔ Willem: {len(spark_willem)} gemeenschappelijke entries")
        for begrip in list(spark_willem)[:5]:
            print(f"      • {begrip}")
    
    # Check structure problems
    print("\n🔧 Structuurproblemen:")
    
    kb_data = load_knowledge_base()
    entries = kb_data.get('knowledge_entries', [])
    
    # Check multiple topics in one field
    multi_topic_count = 0
    examples = []
    
    for entry in entries:
        topic = entry.get('topic', '')
        if '/' in topic or ' / ' in topic:
            multi_topic_count += 1
            if len(examples) < 5:
                examples.append({
                    'begrip': entry.get('begrip'),
                    'topic': topic
                })
    
    print(f"\n   Entries met multiple topics: {multi_topic_count}")
    for ex in examples:
        print(f"      • '{ex['begrip']}': topic = '{ex['topic']}'")
    
    return {
        'overlap_spark_willem': spark_willem,
        'multi_topic_count': multi_topic_count,
        'multi_topic_examples': examples
    }

def main():
    print("🔍 Identity Data Analysis")
    print("="*70)
    
    # Load data
    kb_data = load_knowledge_base()
    users_data = load_users()
    
    print(f"✅ Loaded Knowledge Base: {len(kb_data.get('knowledge_entries', []))} entries")
    print(f"✅ Loaded Users: {len(users_data)} users")
    
    # Analyze each identity
    spark_data = analyze_identity_spark(kb_data)
    willem_data = analyze_identity_willem(kb_data, users_data)
    roadkill_data = analyze_identity_roadkill(kb_data, users_data)
    
    # Check duplicates and conflicts
    conflicts = check_duplicates_and_conflicts(spark_data, willem_data, roadkill_data)
    
    # Summary
    print("\n" + "="*70)
    print("📊 SAMENVATTING")
    print("="*70)
    print(f"\nSpark: {spark_data['total']} KB entries")
    print(f"Willem: {willem_data['total']} KB entries, {len(willem_data['users'])} users")
    print(f"Roadkill: {roadkill_data['total']} KB entries, {len(roadkill_data['bio_entries'])} bio entries")
    print(f"\nStructuurproblemen: {conflicts['multi_topic_count']} entries met multiple topics")
    
    print("\n✅ Analyse voltooid!")
    print("="*70)

if __name__ == '__main__':
    main()
