"""
Knowledge Base Tag Analysis

Analyseert alle tags in knowledge_base.json voor:
- Tag frequentie
- Duplicate/overlapping tags
- Kaarten zonder tags
- Tag consistency
- Suggesties voor verbetering
"""

import json
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple
import re


class TagAnalyzer:
    """Analyzer voor knowledge base tags"""
    
    def __init__(self, kb_path: str = "/app/backend/data/learned_knowledge/knowledge_base.json"):
        self.kb_path = kb_path
        self.entries = []
        self.all_tags = []
        self.tag_frequency = Counter()
        self.tag_to_entries = defaultdict(list)
        
    def load_data(self):
        """Load knowledge base"""
        with open(self.kb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.entries = data.get('knowledge_entries', [])
        print(f"📚 Loaded {len(self.entries)} knowledge entries")
        
    def analyze(self):
        """Run complete analysis"""
        print("\n" + "=" * 80)
        print("KNOWLEDGE BASE TAG ANALYSIS")
        print("=" * 80)
        
        self.load_data()
        
        # Build tag index
        for entry in self.entries:
            entry_id = entry.get('id')
            begrip = entry.get('begrip', 'Unknown')
            tags = entry.get('tags', [])
            
            for tag in tags:
                self.all_tags.append(tag)
                self.tag_frequency[tag] += 1
                self.tag_to_entries[tag].append({
                    'id': entry_id,
                    'begrip': begrip
                })
        
        # Run analyses
        print("\n" + "-" * 80)
        print("1️⃣  TAG FREQUENCY ANALYSIS")
        print("-" * 80)
        self._analyze_frequency()
        
        print("\n" + "-" * 80)
        print("2️⃣  DUPLICATE & OVERLAPPING TAGS")
        print("-" * 80)
        self._analyze_duplicates()
        
        print("\n" + "-" * 80)
        print("3️⃣  KAARTEN ZONDER TAGS")
        print("-" * 80)
        self._analyze_missing_tags()
        
        print("\n" + "-" * 80)
        print("4️⃣  KAARTEN MET 1 TAG")
        print("-" * 80)
        self._analyze_single_tag()
        
        print("\n" + "-" * 80)
        print("5️⃣  TAG CONSISTENCY ISSUES")
        print("-" * 80)
        self._analyze_consistency()
        
        print("\n" + "-" * 80)
        print("6️⃣  SUGGESTIES VOOR VERBETERING")
        print("-" * 80)
        self._generate_suggestions()
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
    
    def _analyze_frequency(self):
        """Analyze tag frequency"""
        total_tags = len(self.all_tags)
        unique_tags = len(self.tag_frequency)
        
        print(f"📊 Totaal tags: {total_tags}")
        print(f"🔢 Unieke tags: {unique_tags}")
        print(f"📈 Gemiddeld {total_tags / len(self.entries):.1f} tags per kaart")
        print()
        
        # Top 30 most used tags
        print("🔝 Top 30 meest gebruikte tags:")
        for i, (tag, count) in enumerate(self.tag_frequency.most_common(30), 1):
            percentage = (count / len(self.entries)) * 100
            print(f"   {i:2}. {tag:30} → {count:4} kaarten ({percentage:5.1f}%)")
        
        print()
        
        # Rare tags (used only once)
        rare_tags = [tag for tag, count in self.tag_frequency.items() if count == 1]
        print(f"🔍 Tags gebruikt in maar 1 kaart: {len(rare_tags)}")
        if rare_tags:
            print(f"   Voorbeelden: {', '.join(rare_tags[:10])}")
    
    def _analyze_duplicates(self):
        """Find duplicate and overlapping tags"""
        # Find similar tags (lowercase, plurals, variations)
        similar_groups = defaultdict(list)
        
        for tag in self.tag_frequency.keys():
            normalized = tag.lower().strip()
            # Remove common suffixes for grouping
            base = re.sub(r'(en|s|ing)$', '', normalized)
            similar_groups[base].append(tag)
        
        # Find groups with multiple variations
        duplicates = {k: v for k, v in similar_groups.items() if len(v) > 1}
        
        if duplicates:
            print(f"⚠️  Mogelijke duplicate/variatie groepen: {len(duplicates)}")
            print()
            
            for i, (base, variants) in enumerate(list(duplicates.items())[:20], 1):
                if len(variants) <= 1:
                    continue
                print(f"   {i}. Basis: '{base}'")
                for variant in sorted(variants):
                    count = self.tag_frequency[variant]
                    print(f"      → {variant:30} ({count} kaarten)")
                print()
        else:
            print("✅ Geen duidelijke duplicates gevonden")
        
        # Find exact case-insensitive duplicates
        case_insensitive = defaultdict(list)
        for tag in self.tag_frequency.keys():
            case_insensitive[tag.lower()].append(tag)
        
        exact_dups = {k: v for k, v in case_insensitive.items() if len(v) > 1}
        if exact_dups:
            print(f"\n⚠️  Case-gevoelige duplicates:")
            for lower, variants in exact_dups.items():
                print(f"   '{lower}': {variants}")
    
    def _analyze_missing_tags(self):
        """Find entries without tags"""
        no_tags = [
            entry for entry in self.entries
            if not entry.get('tags') or len(entry.get('tags', [])) == 0
        ]
        
        print(f"📋 Kaarten zonder tags: {len(no_tags)} van {len(self.entries)}")
        
        if no_tags:
            print(f"\n   Voorbeelden (eerste 15):")
            for i, entry in enumerate(no_tags[:15], 1):
                begrip = entry.get('begrip', 'Unknown')
                entry_id = entry.get('id', 'N/A')[:8]
                print(f"   {i:2}. {begrip:50} (ID: {entry_id}...)")
    
    def _analyze_single_tag(self):
        """Find entries with only 1 tag"""
        single_tag = [
            entry for entry in self.entries
            if len(entry.get('tags', [])) == 1
        ]
        
        print(f"📋 Kaarten met maar 1 tag: {len(single_tag)} van {len(self.entries)}")
        print(f"   ({(len(single_tag) / len(self.entries)) * 100:.1f}%)")
        
        if single_tag:
            print(f"\n   Voorbeelden (eerste 15):")
            for i, entry in enumerate(single_tag[:15], 1):
                begrip = entry.get('begrip', 'Unknown')
                tag = entry.get('tags', [])[0]
                print(f"   {i:2}. {begrip:40} → tag: '{tag}'")
    
    def _analyze_consistency(self):
        """Analyze tag consistency issues"""
        issues = []
        
        # Find tags with spaces (might be multiple tags)
        space_tags = [tag for tag in self.tag_frequency.keys() if ' ' in tag]
        if space_tags:
            issues.append(('Tags met spaties', space_tags[:15]))
        
        # Find very long tags (likely descriptions)
        long_tags = [tag for tag in self.tag_frequency.keys() if len(tag) > 30]
        if long_tags:
            issues.append(('Te lange tags (>30 chars)', long_tags[:15]))
        
        # Find tags with special characters
        special_char_tags = [
            tag for tag in self.tag_frequency.keys()
            if re.search(r'[^a-zA-Z0-9\s_-]', tag)
        ]
        if special_char_tags:
            issues.append(('Tags met speciale karakters', special_char_tags[:15]))
        
        # Find auto-generated tags
        auto_tags = [
            tag for tag in self.tag_frequency.keys()
            if 'knowledge-snap' in tag.lower() or 'auto-generated' in tag.lower()
        ]
        if auto_tags:
            issues.append(('Auto-generated tags', auto_tags))
        
        if issues:
            print(f"⚠️  Consistency issues gevonden: {len(issues)} categorieën\n")
            for category, tags in issues:
                print(f"   {category}: {len(tags)}")
                for tag in tags[:10]:
                    count = self.tag_frequency[tag]
                    print(f"      → '{tag}' ({count} kaarten)")
                print()
        else:
            print("✅ Geen duidelijke consistency issues")
    
    def _generate_suggestions(self):
        """Generate suggestions for improvement"""
        suggestions = []
        
        # Suggestion 1: Most common tags for untagged
        no_tags_count = sum(1 for e in self.entries if not e.get('tags'))
        if no_tags_count > 0:
            suggestions.append(
                f"📌 Voeg tags toe aan {no_tags_count} kaarten zonder tags"
            )
        
        # Suggestion 2: Expand single-tag entries
        single_tag_count = sum(1 for e in self.entries if len(e.get('tags', [])) == 1)
        if single_tag_count > 50:
            suggestions.append(
                f"📌 Voeg extra tags toe aan {single_tag_count} kaarten met maar 1 tag (voor betere verbindingen)"
            )
        
        # Suggestion 3: Standardize auto-generated
        auto_count = sum(
            self.tag_frequency[tag]
            for tag in self.tag_frequency.keys()
            if 'knowledge-snap' in tag.lower() or 'auto-generated' in tag.lower()
        )
        if auto_count > 0:
            suggestions.append(
                f"📌 Vervang {auto_count} auto-generated tags met specifieke tags"
            )
        
        # Suggestion 4: Create tag taxonomy
        if len(self.tag_frequency) > 100:
            suggestions.append(
                f"📌 Overweeg een tag taxonomy (je hebt {len(self.tag_frequency)} unieke tags)"
            )
        
        # Suggestion 5: Top-level categories
        top_tags = [tag for tag, count in self.tag_frequency.most_common(10)]
        suggestions.append(
            f"📌 Top-level categorieën gebruiken: {', '.join(top_tags[:5])}"
        )
        
        # Suggestion 6: Merge similar tags
        similar_count = sum(
            1 for base, variants in self._get_similar_groups().items()
            if len(variants) > 1
        )
        if similar_count > 10:
            suggestions.append(
                f"📌 Merge {similar_count} groepen van vergelijkbare tags (bijv. 'werk' vs 'werken')"
            )
        
        print("💡 Suggesties voor verbetering:\n")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
        
        print("\n📊 Optimale tag structuur:")
        print("   • 3-5 tags per kaart (nu gemiddeld {:.1f})".format(
            len(self.all_tags) / len(self.entries)
        ))
        print("   • Mix van algemene + specifieke tags")
        print("   • Consistente naamgeving (lowercase, geen spaties)")
        print("   • Herbruikbare tags (niet te specifiek)")
    
    def _get_similar_groups(self):
        """Get similar tag groups"""
        similar_groups = defaultdict(list)
        for tag in self.tag_frequency.keys():
            normalized = tag.lower().strip()
            base = re.sub(r'(en|s|ing)$', '', normalized)
            similar_groups[base].append(tag)
        return {k: v for k, v in similar_groups.items() if len(v) > 1}
    
    def save_report(self, output_path: str = "/app/TAG_ANALYSIS_REPORT.md"):
        """Save detailed report to markdown file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Knowledge Base Tag Analysis Report\n\n")
            f.write(f"**Datum:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"**Totaal kaarten:** {len(self.entries)}\n\n")
            f.write(f"**Totaal unieke tags:** {len(self.tag_frequency)}\n\n")
            
            f.write("## Top 50 Tags\n\n")
            f.write("| # | Tag | Kaarten | % |\n")
            f.write("|---|-----|---------|---|\n")
            for i, (tag, count) in enumerate(self.tag_frequency.most_common(50), 1):
                percentage = (count / len(self.entries)) * 100
                f.write(f"| {i} | {tag} | {count} | {percentage:.1f}% |\n")
            
            f.write("\n## Alle Unieke Tags\n\n")
            for tag in sorted(self.tag_frequency.keys()):
                count = self.tag_frequency[tag]
                f.write(f"- `{tag}` ({count})\n")
        
        print(f"\n📄 Detailed report saved to: {output_path}")


if __name__ == "__main__":
    analyzer = TagAnalyzer()
    analyzer.analyze()
    analyzer.save_report()
