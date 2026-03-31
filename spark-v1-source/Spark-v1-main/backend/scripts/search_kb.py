#!/usr/bin/env python3
"""
Knowledge Base Search Tool
Simpel en snel zoeken in knowledge kaarten

Usage:
  python search_kb.py "begrip"              # Zoek op begrip
  python search_kb.py --topic "sport"       # Filter op topic
  python search_kb.py --content "keyword"   # Zoek in lagen
  python search_kb.py --all "query"         # Zoek overal
  python search_kb.py --id "snap-xxx"       # Zoek op ID
"""

import json
import sys
import argparse
from typing import List, Dict

def load_kb():
    """Laad knowledge base"""
    with open('/app/backend/data/learned_knowledge/knowledge_base.json', 'r') as f:
        data = json.load(f)
    return data.get('knowledge_entries', [])

def search_begrip(entries: List[Dict], query: str, exact: bool = False) -> List[Dict]:
    """Zoek op begrip"""
    query_lower = query.lower().strip()
    results = []
    
    for entry in entries:
        begrip = entry.get('begrip', '').lower()
        if exact:
            if begrip == query_lower:
                results.append(entry)
        else:
            if query_lower in begrip:
                results.append(entry)
    
    return results

def search_topic(entries: List[Dict], topic: str) -> List[Dict]:
    """Filter op topic"""
    topic_lower = topic.lower().strip()
    return [e for e in entries if topic_lower in e.get('topic', '').lower()]

def search_content(entries: List[Dict], query: str) -> List[Dict]:
    """Zoek in lagen content"""
    query_lower = query.lower().strip()
    results = []
    
    for entry in entries:
        lagen = entry.get('lagen', {})
        # Zoek in alle lagen
        for laag in ['laag1', 'laag2', 'laag3', 'laag4']:
            content = lagen.get(laag, '').lower()
            if query_lower in content:
                results.append(entry)
                break  # Entry al toegevoegd, ga door naar volgende
    
    return results

def search_all(entries: List[Dict], query: str) -> List[Dict]:
    """Zoek overal (begrip + topic + lagen)"""
    query_lower = query.lower().strip()
    results = []
    
    for entry in entries:
        # Check begrip
        if query_lower in entry.get('begrip', '').lower():
            results.append(entry)
            continue
        
        # Check topic
        if query_lower in entry.get('topic', '').lower():
            results.append(entry)
            continue
        
        # Check lagen
        lagen = entry.get('lagen', {})
        for laag in ['laag1', 'laag2', 'laag3', 'laag4']:
            if query_lower in lagen.get(laag, '').lower():
                results.append(entry)
                break
    
    return results

def search_id(entries: List[Dict], entry_id: str) -> List[Dict]:
    """Zoek op ID"""
    return [e for e in entries if entry_id in e.get('id', '')]

def print_results(results: List[Dict], show_full: bool = False):
    """Print resultaten"""
    if not results:
        print("❌ Geen resultaten gevonden")
        return
    
    print(f"\n✅ {len(results)} resultaten gevonden:\n")
    print("="*80)
    
    for i, entry in enumerate(results, 1):
        begrip = entry.get('begrip', '(geen)')
        topic = entry.get('topic', '(geen)')
        entry_id = entry.get('id', '')[:20]
        status = entry.get('status', '')
        
        print(f"\n{i}. \"{begrip}\"")
        print(f"   Topic: {topic}")
        print(f"   Status: {status}")
        print(f"   ID: {entry_id}")
        
        # Preview van lagen
        lagen = entry.get('lagen', {})
        
        if show_full:
            # Toon alle lagen volledig
            for laag_num in ['laag1', 'laag2', 'laag3', 'laag4']:
                content = lagen.get(laag_num, '').strip()
                if content:
                    print(f"\n   {laag_num}:")
                    print(f"   {content}")
        else:
            # Toon preview
            laag1 = lagen.get('laag1', '').strip()
            if laag1:
                preview = laag1[:80] + '...' if len(laag1) > 80 else laag1
                print(f"   Laag1: {preview}")
            
            # Als laag2/3/4 ook inhoud hebben, toon dat er meer is
            other_layers = sum(1 for l in ['laag2', 'laag3', 'laag4'] if lagen.get(l, '').strip())
            if other_layers > 0:
                print(f"   (+{other_layers} meer lagen)")
    
    print("\n" + "="*80)
    print(f"Totaal: {len(results)} resultaten")
    print("\nTip: Gebruik --full om volledige lagen te zien")

def main():
    parser = argparse.ArgumentParser(
        description='Zoek in Knowledge Base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  %(prog)s "bewustzijn"              # Zoek begrip met "bewustzijn"
  %(prog)s --exact "Bewustzijn"      # Exact begrip "Bewustzijn"
  %(prog)s --topic "sport"           # Alle entries met topic "sport"
  %(prog)s --content "motivatie"     # Zoek in lagen content
  %(prog)s --all "energie"           # Zoek overal
  %(prog)s --id "snap-abc123"        # Zoek op ID
  %(prog)s --topic "sport" --full    # Met volledige lagen
        """
    )
    
    parser.add_argument('query', nargs='?', help='Zoekterm (zoekt in begrip)')
    parser.add_argument('--topic', help='Filter op topic')
    parser.add_argument('--content', help='Zoek in lagen content')
    parser.add_argument('--all', dest='search_all', help='Zoek overal (begrip + topic + lagen)')
    parser.add_argument('--id', dest='search_id', help='Zoek op ID')
    parser.add_argument('--exact', action='store_true', help='Exacte match voor begrip')
    parser.add_argument('--full', action='store_true', help='Toon volledige lagen')
    
    args = parser.parse_args()
    
    # Check of er een zoekterm is
    if not any([args.query, args.topic, args.content, args.search_all, args.search_id]):
        parser.print_help()
        return 1
    
    # Laad KB
    print("🔍 Laden knowledge base...")
    entries = load_kb()
    print(f"📊 Totaal entries: {len(entries)}\n")
    
    # Zoek
    results = []
    
    if args.search_id:
        results = search_id(entries, args.search_id)
    elif args.search_all:
        results = search_all(entries, args.search_all)
    elif args.content:
        results = search_content(entries, args.content)
    elif args.topic:
        results = search_topic(entries, args.topic)
    elif args.query:
        results = search_begrip(entries, args.query, exact=args.exact)
    
    # Print resultaten
    print_results(results, show_full=args.full)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
