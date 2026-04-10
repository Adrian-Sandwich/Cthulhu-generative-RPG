#!/usr/bin/env python3
"""
Deep analysis of dead ends and exploration patterns
Find which entries are blocking exploration
"""

import sys
import json
from collections import defaultdict

sys.path.insert(0, '/Users/adrianmedina/src/Cthulhu')

from game_engine import CthulhuGameEngine

def analyze_dead_ends():
    engine = CthulhuGameEngine()
    adventure = engine.adventure

    print("\n" + "=" * 80)
    print("  DEAD-END ANALYSIS")
    print("=" * 80 + "\n")

    dead_ends = []
    entries_with_no_exit = []
    problematic_entries = []

    for entry in adventure['entries']:
        entry_num = entry['number']
        choices = entry.get('choices', [])

        if not choices:
            dead_ends.append(entry_num)
            entries_with_no_exit.append({
                'entry': entry_num,
                'text_preview': entry['text'][:60],
                'text_length': len(entry['text'])
            })

    print(f"ENTRIES WITH NO CHOICES: {len(dead_ends)}")
    print(f"These are story endpoints (not necessarily bad):\n")

    # Categorize by text length
    proper_endings = [e for e in entries_with_no_exit if e['text_length'] > 100]
    short_endings = [e for e in entries_with_no_exit if e['text_length'] <= 100]

    print(f"Proper story endings (>100 chars): {len(proper_endings)}")
    for e in proper_endings[:10]:
        has_end = "THE END" in engine.adventure['entries'][next(i for i, en in enumerate(engine.adventure['entries']) if en['number'] == e['entry'])]['text']
        print(f"  Entry {e['entry']:3d}: {e['text_length']:4d} chars - {e['text_preview'][:50]}...")

    print(f"\nShort/problematic endings (<100 chars): {len(short_endings)}")
    for e in short_endings:
        print(f"  Entry {e['entry']:3d}: {e['text_length']:4d} chars - '{e['text_preview']}'")

    print(f"\n{'=' * 80}")
    print("  EXPLORATION ANALYSIS")
    print(f"{'=' * 80}\n")

    # Find entries that are referenced but hard to reach
    referenced_entries = set()
    entry_references = defaultdict(list)

    for entry in adventure['entries']:
        for choice in entry.get('choices', []):
            dest = choice.get('destination')
            if dest:
                referenced_entries.add(dest)
                entry_references[dest].append(entry['number'])

    # Find unreferenced entries (can only reach them at start or from specific paths)
    all_entry_nums = set(e['number'] for e in adventure['entries'])
    unreferenced = all_entry_nums - referenced_entries

    print(f"Referenced entries: {len(referenced_entries)}/219")
    print(f"Unreferenced entries (dead paths?): {len(unreferenced)}")
    print(f"  {sorted(unreferenced)[:20]}...")

    # Find bottleneck entries (referenced from many entries but have limited onward paths)
    print(f"\n{'=' * 80}")
    print("  CRITICAL BRANCH POINTS")
    print(f"{'=' * 80}\n")

    # Entry 3 is the main branch point
    entry_3 = next((e for e in adventure['entries'] if e['number'] == 3), None)
    if entry_3:
        print(f"Entry 3 (Main branch point):")
        print(f"  Text: {entry_3['text'][:80]}...")
        print(f"  Choices: {len(entry_3['choices'])}")
        for i, choice in enumerate(entry_3['choices'], 1):
            print(f"    {i}. → Entry {choice['destination']}: {choice['text'][:40]}")
            # Trace forward from this choice
            next_entry = next((e for e in adventure['entries'] if e['number'] == choice['destination']), None)
            if next_entry:
                next_choices = len(next_entry['choices'])
                print(f"       (leads to Entry {choice['destination']} with {next_choices} options)")

    print(f"\n{'=' * 80}")
    print("  DEAD-END PATTERNS")
    print(f"{'=' * 80}\n")

    # Analyze paths to dead ends
    dead_end_paths = defaultdict(int)

    for entry in adventure['entries']:
        if entry.get('choices'):
            for choice in entry['choices']:
                dest = choice.get('destination')
                # Check if destination is a dead end
                dest_entry = next((e for e in adventure['entries'] if e['number'] == dest), None)
                if dest_entry and not dest_entry.get('choices'):
                    dead_end_paths[dest] += 1

    print(f"Dead ends with incoming paths:\n")
    for dead_end_num, incoming_count in sorted(dead_end_paths.items(), key=lambda x: -x[1])[:15]:
        dead_entry = next((e for e in adventure['entries'] if e['number'] == dead_end_num), None)
        if dead_entry:
            text_preview = dead_entry['text'][:60].replace('\n', ' ')
            print(f"  Entry {dead_end_num:3d}: {incoming_count} paths → {text_preview}...")

    print(f"\n{'=' * 80}\n")

if __name__ == '__main__':
    analyze_dead_ends()
