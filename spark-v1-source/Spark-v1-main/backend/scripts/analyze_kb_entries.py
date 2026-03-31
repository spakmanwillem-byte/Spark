#!/usr/bin/env python3
"""
Knowledge Base Entry Analysis
Doel: Analyseer entries zonder metadata en duplicaten
"""

import json
from collections import defaultdict

KB_PATH = '/app/backend/data/learned_knowledge/knowledge_base.json'

def load_kb():
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_entries_without_metadata(entries):
    """Analyseer entries zonder metadata veld"""
    
    print("\n" + "="*70)
    print("📊 ANALYSE: ENTRIES ZONDER METADATA (1270 stuks)")
    print("="*70)
    
    no_metadata = [e for e in entries if 'metadata' not in e]
    
    # Groepeer op detected_by
    by_detector = defaultdict(list)
    for entry in no_metadata:
        detector = entry.get('detected_by', 'onbekend')
        by_detector[detector].append(entry)
    
    print(f"\n📈 Verdeling per 'detected_by':")
    for detector, items in sorted(by_detector.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"   • {detector}: {len(items)} entries")
    
    # Check welke velden WEL aanwezig zijn
    print(f"\n🔍 Veld-analyse (eerste 100 entries zonder metadata):")
    
    field_presence = defaultdict(int)
    sample_entries = no_metadata[:100]
    
    for entry in sample_entries:
        for field in entry.keys():
            field_presence[field] += 1
    
    print("   Velden aanwezig in deze entries:")
    for field, count in sorted(field_presence.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(sample_entries)) * 100
        print(f"   • {field}: {count}/{len(sample_entries)} ({percentage:.0f}%)")
    
    # Toon voorbeelden van incomplete entries
    print(f"\n📋 VOORBEELDEN VAN INCOMPLETE ENTRIES:")
    print("-" * 70)
    
    for i, entry in enumerate(no_metadata[:10], 1):
        print(f"\n{i}. Begrip: '{entry.get('begrip', 'N/A')}'")
        print(f"   ID: {entry.get('id', 'N/A')}")
        print(f"   Detected by: {entry.get('detected_by', 'N/A')}")
        print(f"   Type: {entry.get('type', 'N/A')}")
        print(f"   Topic: {entry.get('topic', 'N/A')}")
        print(f"   Tags: {entry.get('tags', [])}")
        print(f"   Status: {entry.get('status', 'N/A')}")
        
        # Check lagen inhoud
        lagen = entry.get('lagen', {})
        if isinstance(lagen, dict):
            layer_count = sum(1 for k, v in lagen.items() if v and v.strip())
            print(f"   Lagen met inhoud: {layer_count}/4")
            
            # Toon lege lagen
            empty_layers = [k for k, v in lagen.items() if not v or not v.strip()]
            if empty_layers:
                print(f"   Lege lagen: {', '.join(empty_layers)}")
        else:
            print(f"   Lagen: {type(lagen).__name__} (niet dict)")
        
        # Check ws5
        ws5 = entry.get('ws5', {})
        if isinstance(ws5, dict):
            ws5_count = sum(1 for k, v in ws5.items() if v and str(v).strip())
            print(f"   WS5 velden met inhoud: {ws5_count}/5")
        
        print(f"   Volledigheid: {'❌ LEEG' if layer_count == 0 else f'⚠️  INCOMPLETE ({layer_count}/4 lagen)'}")
    
    # Count volledig lege entries
    empty_count = 0
    incomplete_count = 0
    
    for entry in no_metadata:
        lagen = entry.get('lagen', {})
        if isinstance(lagen, dict):
            layer_count = sum(1 for k, v in lagen.items() if v and v.strip())
            if layer_count == 0:
                empty_count += 1
            else:
                incomplete_count += 1
    
    print(f"\n📊 SAMENVATTING:")
    print(f"   • Volledig LEGE entries (0 lagen): {empty_count}")
    print(f"   • INCOMPLETE entries (1-3 lagen): {incomplete_count}")
    print(f"   • Totaal zonder metadata: {len(no_metadata)}")
    
    return no_metadata

def analyze_duplicates(entries):
    """Analyseer duplicaten en vergelijk inhoud"""
    
    print("\n" + "="*70)
    print("📊 ANALYSE: DUPLICATEN (14 stuks)")
    print("="*70)
    
    # Groepeer op begrip (lowercase)
    begrippen_map = defaultdict(list)
    for idx, entry in enumerate(entries):
        begrip = entry.get('begrip', '').lower()
        begrippen_map[begrip].append((idx, entry))
    
    # Find duplicates
    duplicates = {k: v for k, v in begrippen_map.items() if len(v) > 1}
    
    print(f"\n🔍 Gevonden {len(duplicates)} duplicaat begrippen:\n")
    
    for begrip, occurrences in sorted(duplicates.items()):
        print(f"\n{'='*70}")
        print(f"📌 Begrip: '{begrip}' ({len(occurrences)} versies)")
        print(f"{'='*70}")
        
        for i, (idx, entry) in enumerate(occurrences, 1):
            print(f"\n  Versie {i} (index {idx}):")
            print(f"    • ID: {entry.get('id', 'N/A')}")
            print(f"    • Detected by: {entry.get('detected_by', 'N/A')}")
            print(f"    • Type: {entry.get('type', 'N/A')}")
            print(f"    • Topic: {entry.get('topic', 'N/A')}")
            print(f"    • Tags: {entry.get('tags', [])}")
            print(f"    • Has metadata: {'✅' if 'metadata' in entry else '❌'}")
            
            # Lagen inhoud
            lagen = entry.get('lagen', {})
            if isinstance(lagen, dict):
                layer_count = sum(1 for k, v in lagen.items() if v and v.strip())
                filled_layers = [k for k, v in lagen.items() if v and v.strip()]
                print(f"    • Lagen: {layer_count}/4 gevuld ({', '.join(filled_layers) if filled_layers else 'geen'})")
            
            # WS5 inhoud
            ws5 = entry.get('ws5', {})
            if isinstance(ws5, dict):
                ws5_count = sum(1 for k, v in ws5.items() if v and str(v).strip())
                print(f"    • WS5: {ws5_count}/5 gevuld")
            
            # Relaties
            relaties = entry.get('relaties', {})
            if isinstance(relaties, dict):
                rel_count = sum(len(v) if isinstance(v, list) else 0 for v in relaties.values())
                print(f"    • Relaties: {rel_count} totaal")
            
            # Bronnen
            bronnen = entry.get('bronnen', [])
            print(f"    • Bronnen: {len(bronnen) if isinstance(bronnen, list) else 0}")
            
            # Content score (ruwe schatting)
            content_score = 0
            if isinstance(lagen, dict):
                content_score += sum(len(str(v)) for v in lagen.values() if v)
            if isinstance(ws5, dict):
                content_score += sum(len(str(v)) for v in ws5.values() if v)
            
            print(f"    • Content score: {content_score} chars")
            print(f"    • Verdict: {'✅ MEESTE INHOUD' if content_score == max(sum(len(str(v)) for v in e.get('lagen', {}).values() if v) + sum(len(str(v)) for v in e.get('ws5', {}).values() if v) for _, e in occurrences) else '⚠️  Minder inhoud'}")
        
        # Aanbeveling
        best_idx = max(range(len(occurrences)), key=lambda i: 
            sum(len(str(v)) for v in occurrences[i][1].get('lagen', {}).values() if v) +
            sum(len(str(v)) for v in occurrences[i][1].get('ws5', {}).values() if v)
        )
        print(f"\n  💡 AANBEVELING: Behoud versie {best_idx + 1}, verwijder rest")

def main():
    print("🔧 Knowledge Base Entry Analyse gestart...")
    print(f"📁 Bestand: {KB_PATH}\n")
    
    data = load_kb()
    entries = data.get('knowledge_entries', [])
    
    print(f"📊 Totaal entries: {len(entries)}")
    
    # Analyse 1: Entries zonder metadata
    no_metadata = analyze_entries_without_metadata(entries)
    
    # Analyse 2: Duplicaten
    analyze_duplicates(entries)
    
    print("\n" + "="*70)
    print("✅ ANALYSE VOLTOOID")
    print("="*70)
    print("\nWacht op bevestiging voordat entries worden verwijderd.")

if __name__ == '__main__':
    main()
