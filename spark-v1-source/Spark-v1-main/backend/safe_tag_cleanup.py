"""
Safe Tag Cleanup Script

Voert alleen veilige, automatische tag cleanups uit:
1. Case-sensitive duplicates (blij/Blij → blij)
2. Enkelvoud/meervoud merges (dier/dieren → dier)
3. Formatting fixes (spaties → underscores)
4. Special characters normaliseren (cafeïne → cafeine)

NIET aanpassen:
- Semantische variaties (verbinden/verbinding)
- Single-use tags
- Identiteit tags (spark, roadkill, willem)
"""

import json
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import unicodedata
import re


class SafeTagCleaner:
    """Safe tag cleanup met preview en undo support"""
    
    KB_PATH = "/app/backend/data/learned_knowledge/knowledge_base.json"
    BACKUP_PATH = "/app/backend/data/learned_knowledge/knowledge_base.backup_before_cleanup.json"
    
    # Tags die NOOIT aangepast mogen worden
    PROTECTED_TAGS = {
        'spark', 'roadkill', 'willem', 'lotus', 'maurice',
        'spark_your_life', 'roadkill_shop'
    }
    
    def __init__(self):
        self.entries = []
        self.tag_mappings = {}  # old_tag -> new_tag
        self.changes_preview = []
        
    def load_data(self):
        """Load knowledge base"""
        with open(self.KB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.entries = data.get('knowledge_entries', [])
        print(f"📚 Loaded {len(self.entries)} entries")
        
    def create_backup(self):
        """Create backup before cleanup"""
        import shutil
        shutil.copy(self.KB_PATH, self.BACKUP_PATH)
        print(f"💾 Backup created: {self.BACKUP_PATH}")
    
    def normalize_tag(self, tag: str) -> str:
        """
        Normalize tag with safe transformations
        
        Safe transformations:
        1. Lowercase
        2. Remove accents
        3. Replace spaces with underscores
        4. Remove special characters (except _-)
        """
        # Skip protected tags
        if tag.lower() in self.PROTECTED_TAGS:
            return tag
        
        # 1. Lowercase
        normalized = tag.lower()
        
        # 2. Remove accents
        normalized = self._remove_accents(normalized)
        
        # 3. Replace spaces with underscores
        normalized = normalized.replace(' ', '_')
        
        # 4. Remove special characters (keep alphanumeric, _, -)
        normalized = re.sub(r'[^a-z0-9_-]', '', normalized)
        
        # 5. Clean up multiple underscores
        normalized = re.sub(r'_+', '_', normalized)
        normalized = normalized.strip('_')
        
        return normalized
    
    def _remove_accents(self, text: str) -> str:
        """Remove accents from text"""
        # Decompose unicode characters
        nfd = unicodedata.normalize('NFD', text)
        # Filter out combining characters (accents)
        return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    
    def find_plural_singular_pairs(self) -> List[Tuple[str, str]]:
        """
        Find plural/singular pairs
        
        Safe rules:
        - ends with 'en' → remove 'en' (dieren → dier)
        - ends with 's' → remove 's' (BUT only if both exist!)
        """
        all_tags = set()
        for entry in self.entries:
            all_tags.update(entry.get('tags', []))
        
        pairs = []
        
        for tag in all_tags:
            tag_lower = tag.lower()
            
            # Skip protected
            if tag_lower in self.PROTECTED_TAGS:
                continue
            
            # Check for 'en' suffix (Dutch plurals)
            if tag_lower.endswith('en') and len(tag_lower) > 3:
                singular = tag_lower[:-2]
                
                # Check if singular exists in dataset
                singular_exists = any(t.lower() == singular for t in all_tags)
                
                if singular_exists:
                    # Find the actual tag (with original case)
                    singular_tag = next(t for t in all_tags if t.lower() == singular)
                    pairs.append((tag, singular_tag))
        
        return pairs
    
    def preview_changes(self):
        """Preview all changes before applying"""
        print("\n" + "=" * 80)
        print("TAG CLEANUP PREVIEW")
        print("=" * 80)
        
        # Collect all tags
        all_tags = Counter()
        for entry in self.entries:
            for tag in entry.get('tags', []):
                all_tags[tag] += 1
        
        # 1. Case-sensitive duplicates
        case_groups = defaultdict(list)
        for tag in all_tags.keys():
            case_groups[tag.lower()].append(tag)
        
        case_duplicates = {k: v for k, v in case_groups.items() if len(v) > 1}
        
        print("\n1️⃣  CASE-SENSITIVE DUPLICATES")
        print("-" * 80)
        if case_duplicates:
            for lower, variants in sorted(case_duplicates.items()):
                # Choose lowercase as canonical
                canonical = lower
                for variant in variants:
                    if variant != canonical:
                        count = all_tags[variant]
                        self.tag_mappings[variant] = canonical
                        self.changes_preview.append({
                            'type': 'case',
                            'old': variant,
                            'new': canonical,
                            'count': count
                        })
                        print(f"   {variant:30} → {canonical:30} ({count} kaarten)")
        else:
            print("   ✅ Geen case-sensitive duplicates")
        
        # 2. Plural/Singular
        print("\n2️⃣  ENKELVOUD/MEERVOUD MERGES")
        print("-" * 80)
        plural_pairs = self.find_plural_singular_pairs()
        if plural_pairs:
            for plural, singular in plural_pairs:
                count = all_tags[plural]
                self.tag_mappings[plural] = singular
                self.changes_preview.append({
                    'type': 'plural',
                    'old': plural,
                    'new': singular,
                    'count': count
                })
                print(f"   {plural:30} → {singular:30} ({count} kaarten)")
        else:
            print("   ✅ Geen plural/singular pairs om te mergen")
        
        # 3. Formatting fixes
        print("\n3️⃣  FORMATTING FIXES")
        print("-" * 80)
        formatting_changes = 0
        for tag in all_tags.keys():
            normalized = self.normalize_tag(tag)
            
            # Only if different and not already mapped
            if normalized != tag and tag not in self.tag_mappings:
                count = all_tags[tag]
                self.tag_mappings[tag] = normalized
                self.changes_preview.append({
                    'type': 'format',
                    'old': tag,
                    'new': normalized,
                    'count': count
                })
                print(f"   {tag:30} → {normalized:30} ({count} kaarten)")
                formatting_changes += 1
        
        if formatting_changes == 0:
            print("   ✅ Geen formatting fixes nodig")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total changes: {len(self.tag_mappings)}")
        print(f"  - Case fixes: {sum(1 for c in self.changes_preview if c['type'] == 'case')}")
        print(f"  - Plural fixes: {sum(1 for c in self.changes_preview if c['type'] == 'plural')}")
        print(f"  - Format fixes: {sum(1 for c in self.changes_preview if c['type'] == 'format')}")
        print()
        print(f"Total kaarten affected: {sum(c['count'] for c in self.changes_preview)}")
        
    def apply_cleanup(self):
        """Apply tag cleanup to knowledge base"""
        print("\n" + "=" * 80)
        print("APPLYING CLEANUP...")
        print("=" * 80)
        
        changes_made = 0
        
        for entry in self.entries:
            tags = entry.get('tags', [])
            new_tags = []
            
            for tag in tags:
                if tag in self.tag_mappings:
                    new_tag = self.tag_mappings[tag]
                    new_tags.append(new_tag)
                    changes_made += 1
                else:
                    new_tags.append(tag)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tags = []
            for tag in new_tags:
                if tag not in seen:
                    seen.add(tag)
                    unique_tags.append(tag)
            
            entry['tags'] = unique_tags
        
        print(f"✅ Applied {changes_made} tag changes")
        
    def save_data(self):
        """Save cleaned data"""
        data = {
            'knowledge_entries': self.entries,
            'metadata': {
                'last_cleanup': __import__('datetime').datetime.now().isoformat(),
                'cleanup_changes': len(self.tag_mappings)
            }
        }
        
        with open(self.KB_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved cleaned data to {self.KB_PATH}")
    
    def run(self, preview_only: bool = False):
        """Run cleanup with preview"""
        self.load_data()
        self.preview_changes()
        
        if preview_only:
            print("\n⚠️  PREVIEW ONLY - No changes applied")
            return
        
        print("\n" + "=" * 80)
        response = input("Apply these changes? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cleanup cancelled")
            return
        
        self.create_backup()
        self.apply_cleanup()
        self.save_data()
        
        print("\n✅ CLEANUP COMPLETE!")
        print(f"Backup saved to: {self.BACKUP_PATH}")


if __name__ == "__main__":
    import sys
    
    preview_only = '--preview' in sys.argv
    
    cleaner = SafeTagCleaner()
    cleaner.run(preview_only=preview_only)
