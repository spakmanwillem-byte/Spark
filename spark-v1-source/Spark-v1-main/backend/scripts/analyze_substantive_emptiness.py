#!/usr/bin/env python3
"""
Inhoudelijke Lege Entries Analyzer
Vindt entries die een begrip hebben maar geen substantiële inhoud in de lagen
"""

import json
import sys
import re
from typing import Dict, List, Tuple

def load_knowledge_base(path: str) -> Dict:
    """Laad knowledge base JSON"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_placeholder_text(text: str) -> bool:
    """Check of tekst een placeholder is"""
    if not text:
        return True
    
    text = text.strip().lower()
    
    # Lege of alleen punctuatie
    if len(text) < 3:
        return True
    
    # Expliciete placeholders
    placeholders = [
        '...',
        'tbd',
        'todo',
        'nog in te vullen',
        'nvt',
        'n/a',
        'leeg',
        'onbekend',
        'undefined',
        'null'
    ]
    
    if any(p in text for p in placeholders):
        return True
    
    return False

def is_trivial_content(begrip: str, text: str) -> bool:
    """Check of content triviaal is (herhaalt alleen het begrip)"""
    if not text:
        return True
    
    begrip_lower = begrip.lower().strip()
    text_lower = text.lower().strip()
    
    # Te kort voor echte informatie
    if len(text_lower) < 10:
        return True
    
    # Herhaalt alleen het begrip
    if text_lower == begrip_lower:
        return True
    
    # Herhaalt begrip met minimale toevoeging
    if text_lower.startswith(begrip_lower) and len(text_lower) < len(begrip_lower) + 20:
        return True
    
    return False

def is_substantively_empty(entry: Dict) -> Tuple[bool, str]:
    """
    Bepaal of een entry inhoudelijk leeg is
    Returns: (is_leeg, reden)
    """
    begrip = entry.get("begrip", "").strip()
    lagen = entry.get("lagen", {})
    status = entry.get("status", "")
    
    # Als begrip leeg is, is het sowieso leeg
    if not begrip:
        return True, "Geen begrip"
    
    # Check alle lagen
    if not lagen:
        return True, "Geen lagen"
    
    # Verzamel alle laag content
    all_layers = []
    for key in ['laag1', 'laag2', 'laag3', 'laag4']:
        content = lagen.get(key, "")
        if content:
            all_layers.append(content.strip())
    
    # Geen enkele laag heeft content
    if not all_layers:
        return True, "Alle lagen leeg"
    
    # Check of alle lagen placeholders zijn
    all_placeholders = all(is_placeholder_text(layer) for layer in all_layers)
    if all_placeholders:
        return True, "Alleen placeholders"
    
    # Check of alle lagen triviaal zijn
    all_trivial = all(is_trivial_content(begrip, layer) for layer in all_layers)
    if all_trivial:
        return True, "Alleen triviale content"
    
    # Als status draft/pending is EN laag1 (belangrijkste) leeg of triviaal
    if status in ['draft', 'pending', 'pending_confirmation']:
        laag1 = lagen.get('laag1', '').strip()
        if not laag1 or is_placeholder_text(laag1) or is_trivial_content(begrip, laag1):
            return True, f"Draft zonder substantiële laag1 (status: {status})"
    
    return False, ""

def analyze_substantive_emptiness(kb_path: str):
    """Analyseer inhoudelijk lege entries"""
    print("🔍 Laden knowledge base...")
    data = load_knowledge_base(kb_path)
    entries = data.get("knowledge_entries", [])
    
    total = len(entries)
    print(f"📊 Totaal entries: {total}\n")
    
    # Categoriseer entries
    substantively_empty = []
    good_entries = []
    reasons = {}
    
    print("🔍 Analyseren inhoudelijke leegte...")
    for entry in entries:
        is_empty, reason = is_substantively_empty(entry)
        if is_empty:
            substantively_empty.append(entry)
            begrip = entry.get("begrip", "(leeg)")
            entry_id = entry.get("id", "unknown")
            
            if reason not in reasons:
                reasons[reason] = []
            reasons[reason].append({
                'id': entry_id,
                'begrip': begrip,
                'status': entry.get('status', ''),
                'lagen': entry.get('lagen', {})
            })
        else:
            good_entries.append(entry)
    
    print(f"✅ Goede entries (met inhoud): {len(good_entries)}")
    print(f"❌ Inhoudelijk lege entries: {len(substantively_empty)}\n")
    
    # Toon redenen
    print("📋 REDENEN VOOR LEEGTE:")
    print("-" * 80)
    for reason, items in sorted(reasons.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{reason}: {len(items)} entries")
        
        # Toon eerste 5 voorbeelden
        for i, item in enumerate(items[:5], 1):
            print(f"  {i}. '{item['begrip']}' (ID: {item['id'][:15]}...)")
            print(f"     Status: {item['status']}")
            
            # Toon laag1 als voorbeeld
            laag1 = item['lagen'].get('laag1', '')
            if laag1:
                preview = laag1[:60] + '...' if len(laag1) > 60 else laag1
                print(f"     Laag1: \"{preview}\"")
            else:
                print(f"     Laag1: (leeg)")
        
        if len(items) > 5:
            print(f"  ... en {len(items) - 5} meer")
    
    # Samenvatting
    print("\n" + "="*80)
    print("📈 SAMENVATTING")
    print("="*80)
    print(f"Totaal entries:              {total}")
    print(f"Goede entries (met inhoud):  {len(good_entries)} ({len(good_entries)/total*100:.1f}%)")
    print(f"Inhoudelijk leeg:            {len(substantively_empty)} ({len(substantively_empty)/total*100:.1f}%)")
    
    print("\n💡 AANBEVELING:")
    print(f"Verwijder {len(substantively_empty)} inhoudelijk lege entries")
    print(f"Behoud {len(good_entries)} entries met substantiële inhoud")
    print(f"Nieuwe knowledge base grootte: {total} → {len(good_entries)} entries")
    
    return {
        'total': total,
        'good': len(good_entries),
        'empty': len(substantively_empty),
        'reasons': reasons
    }

if __name__ == "__main__":
    kb_path = "/app/backend/data/learned_knowledge/knowledge_base.json"
    analyze_substantive_emptiness(kb_path)
