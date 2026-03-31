#!/usr/bin/env python3
"""
Deep KB Analysis - Extract Identity Data from Existing Entries
Doel: Analyseer alle relevante KB entries en extract bruikbare identity data
"""

import json
from pathlib import Path

KB_PATH = Path('/app/backend/data/learned_knowledge/knowledge_base.json')

def load_kb():
    with open(KB_PATH, 'r') as f:
        return json.load(f)

def find_entries_by_search(kb_data, search_terms, exact_only=False):
    """Zoek KB entries op begrip of inhoud"""
    entries = kb_data.get('knowledge_entries', [])
    found = []
    
    for entry in entries:
        begrip = entry.get('begrip', '').lower()
        
        if exact_only:
            # Exact match op begrip
            if begrip in [term.lower() for term in search_terms]:
                found.append(entry)
        else:
            # Fuzzy match on begrip or content
            for term in search_terms:
                term_lower = term.lower()
                if term_lower in begrip:
                    found.append(entry)
                    break
                
                # Check lagen content
                lagen = entry.get('lagen', {})
                for content in lagen.values():
                    if content and term_lower in str(content).lower():
                        if entry not in found:
                            found.append(entry)
                        break
    
    return found

def extract_full_content(entry):
    """Extract alle content uit een entry"""
    
    result = {
        'begrip': entry.get('begrip', ''),
        'id': entry.get('id', ''),
        'type': entry.get('metadata', {}).get('type', 'unknown'),
        'topic': entry.get('topic', ''),
        'tags': entry.get('tags', []),
        'lagen': {},
        'ws5': {},
        'metadata_entry': entry.get('metadata', {})
    }
    
    # Extract lagen
    lagen = entry.get('lagen', {})
    for layer_name, content in lagen.items():
        if content and str(content).strip():
            result['lagen'][layer_name] = content
    
    # Extract ws5
    ws5 = entry.get('ws5', {})
    if ws5:
        for key, value in ws5.items():
            if value and str(value).strip():
                result['ws5'][key] = value
    
    # Extract other useful fields
    result['bronnen'] = entry.get('bronnen', [])
    result['relaties'] = entry.get('relaties', {})
    result['detected_by'] = entry.get('detected_by', '')
    
    return result

def analyze_roadkill_entries(kb_data):
    """Analyseer alle Roadkill gerelateerde entries"""
    
    print("\n" + "="*70)
    print("🎮 ROADKILL KB ENTRIES - DEEP ANALYSIS")
    print("="*70)
    
    search_terms = ['roadkill']
    entries = find_entries_by_search(kb_data, search_terms)
    
    print(f"\n📊 Gevonden: {len(entries)} entries\n")
    
    # Categorize
    categories = {
        'gamer_identity': [],
        'community': [],
        'business': [],
        'other': []
    }
    
    for entry in entries:
        begrip = entry.get('begrip', '').lower()
        entry_type = entry.get('metadata', {}).get('type', '')
        topic = entry.get('topic', '').lower()
        
        full_content = extract_full_content(entry)
        
        # Categorize
        if 'gamertag' in begrip or 'gamer' in begrip:
            categories['gamer_identity'].append(full_content)
        elif 'community' in begrip:
            categories['community'].append(full_content)
        elif 'shop' in begrip or 'bedrijf' in topic or 'handel' in topic:
            categories['business'].append(full_content)
        else:
            categories['other'].append(full_content)
    
    # Print detailed analysis
    for category, items in categories.items():
        if not items:
            continue
            
        print(f"\n{'='*70}")
        print(f"📁 CATEGORIE: {category.upper().replace('_', ' ')}")
        print(f"{'='*70}")
        
        for item in items:
            print(f"\n🔹 {item['begrip']}")
            print(f"   ID: {item['id']}")
            print(f"   Type: {item['type']}")
            print(f"   Topic: {item['topic']}")
            print(f"   Tags: {', '.join(item['tags'][:5])}")
            
            if item['lagen']:
                print(f"\n   📝 LAGEN CONTENT:")
                for layer, content in item['lagen'].items():
                    content_preview = content[:150] + "..." if len(content) > 150 else content
                    print(f"      {layer}: {content_preview}")
            
            if item['ws5']:
                print(f"\n   🔍 WS5 (Wie/Wat/Waar/Wanneer/Waarom):")
                for key, value in item['ws5'].items():
                    value_preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    print(f"      {key}: {value_preview}")
            
            if item['bronnen']:
                print(f"\n   📚 Bronnen: {len(item['bronnen'])} items")
            
            if item['detected_by']:
                print(f"   👤 Detected by: {item['detected_by']}")
    
    return categories

def analyze_spark_your_life_entries(kb_data):
    """Analyseer Spark Your Life entries (incl. varianten)"""
    
    print("\n" + "="*70)
    print("✨ SPARK YOUR LIFE KB ENTRIES - DEEP ANALYSIS")
    print("="*70)
    
    search_terms = ['spark your life', 'sparkyourlife', 'zorgnoederij']
    entries = find_entries_by_search(kb_data, search_terms)
    
    print(f"\n📊 Gevonden: {len(entries)} entries\n")
    
    if not entries:
        print("⚠️  Geen entries gevonden voor 'Spark Your Life' of 'Zorgnoederij'")
        return []
    
    all_content = []
    for entry in entries:
        full_content = extract_full_content(entry)
        all_content.append(full_content)
        
        print(f"\n{'='*70}")
        print(f"🔹 {full_content['begrip']}")
        print(f"{'='*70}")
        print(f"   ID: {full_content['id']}")
        print(f"   Type: {full_content['type']}")
        print(f"   Topic: {full_content['topic']}")
        print(f"   Tags: {', '.join(full_content['tags'][:5])}")
        
        if full_content['lagen']:
            print(f"\n   📝 LAGEN CONTENT:")
            for layer, content in full_content['lagen'].items():
                print(f"      {layer}:")
                print(f"         {content}")
        
        if full_content['ws5']:
            print(f"\n   🔍 WS5:")
            for key, value in full_content['ws5'].items():
                print(f"      {key}: {value}")
        
        if full_content['bronnen']:
            print(f"\n   📚 Bronnen: {full_content['bronnen']}")
        
        if full_content['detected_by']:
            print(f"\n   👤 Detected by: {full_content['detected_by']}")
    
    return all_content

def check_spark_variants(kb_data):
    """Check voor varianten van Spark names"""
    
    print("\n" + "="*70)
    print("🔍 CHECK: SPARK VARIANTEN")
    print("="*70)
    
    variants = [
        'spark',
        'spark ai',
        'spark assistant',
        'spark your life',
        'zorgnoederij'
    ]
    
    for variant in variants:
        entries = find_entries_by_search(kb_data, [variant], exact_only=False)
        print(f"\n   '{variant}': {len(entries)} entries")
        
        # Show first 3
        for entry in entries[:3]:
            begrip = entry.get('begrip', '')
            entry_type = entry.get('metadata', {}).get('type', 'unknown')
            print(f"      • {begrip} (type: {entry_type})")
        
        if len(entries) > 3:
            print(f"      ... en {len(entries) - 3} andere")

def extract_identity_data_from_kb(categories_roadkill, spark_your_life_entries):
    """Extract bruikbare identity data uit KB entries"""
    
    print("\n" + "="*70)
    print("💡 EXTRACTIE: KB → IDENTITY DATA")
    print("="*70)
    
    # Roadkill Gamer/Identity
    print("\n🎮 ROADKILL GAMER/IDENTITY:")
    if categories_roadkill['gamer_identity']:
        for item in categories_roadkill['gamer_identity']:
            print(f"\n   Van '{item['begrip']}':")
            
            # Extract mission/vision/values from lagen
            for layer, content in item['lagen'].items():
                if 'filosofie' in content.lower() or 'betekenis' in content.lower():
                    print(f"      Philosophy: {content[:200]}...")
                if 'community' in content.lower() or 'verbinding' in content.lower():
                    print(f"      Community focus: {content[:200]}...")
    
    # Roadkill Community
    print("\n🌐 ROADKILL COMMUNITY:")
    if categories_roadkill['community']:
        for item in categories_roadkill['community']:
            print(f"\n   Van '{item['begrip']}':")
            for layer, content in item['lagen'].items():
                print(f"      {layer}: {content[:200]}...")
    
    # Roadkill Business
    print("\n💼 ROADKILL BUSINESS:")
    if categories_roadkill['business']:
        for item in categories_roadkill['business']:
            print(f"\n   Van '{item['begrip']}':")
            
            # Extract business info
            if 'website' in item['metadata_entry']:
                print(f"      Website: {item['metadata_entry']['website']}")
            if 'email' in item['metadata_entry']:
                print(f"      Email: {item['metadata_entry']['email']}")
            
            for layer, content in item['lagen'].items():
                print(f"      {layer}: {content[:200]}...")
    
    # Spark Your Life
    print("\n✨ SPARK YOUR LIFE:")
    if spark_your_life_entries:
        for item in spark_your_life_entries:
            print(f"\n   Van '{item['begrip']}':")
            for layer, content in item['lagen'].items():
                print(f"      {layer}: {content[:150]}...")

def main():
    print("🔍 Deep KB Analysis - Identity Data Extraction")
    print("="*70)
    
    kb_data = load_kb()
    print(f"✅ Loaded KB: {len(kb_data.get('knowledge_entries', []))} entries")
    
    # Analyze Roadkill
    categories_roadkill = analyze_roadkill_entries(kb_data)
    
    # Analyze Spark Your Life
    spark_your_life_entries = analyze_spark_your_life_entries(kb_data)
    
    # Check variants
    check_spark_variants(kb_data)
    
    # Extract identity data
    extract_identity_data_from_kb(categories_roadkill, spark_your_life_entries)
    
    print("\n" + "="*70)
    print("✅ DEEP ANALYSIS VOLTOOID")
    print("="*70)
    
    # Summary
    print("\n📊 SAMENVATTING:")
    print(f"   Roadkill Gamer/Identity: {len(categories_roadkill['gamer_identity'])} entries")
    print(f"   Roadkill Community: {len(categories_roadkill['community'])} entries")
    print(f"   Roadkill Business: {len(categories_roadkill['business'])} entries")
    print(f"   Roadkill Other: {len(categories_roadkill['other'])} entries")
    print(f"   Spark Your Life: {len(spark_your_life_entries)} entries")

if __name__ == '__main__':
    main()
