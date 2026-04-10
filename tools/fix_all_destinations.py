#!/usr/bin/env python3
"""
Fix ALL entries by extracting destinations from text.
This is the definitive solution - extract "go to NNN" from entry text.
"""

import json
import re

def fix_all_destinations(filepath):
    """Extract all destinations from entry text"""

    with open(filepath, 'r') as f:
        entries = json.load(f)

    print(f"Processing {len(entries)} entries...\n")

    valid_entries = {e['number'] for e in entries}
    fixed_count = 0
    orphan_count = 0

    for entry in entries:
        num = entry['number']
        text = entry.get('text', '')

        # Find ALL "go to NNN" references in text
        destinations = set()

        # Pattern 1: "go to 123" (case insensitive)
        for match in re.finditer(r'go to (\d+)', text, re.IGNORECASE):
            dest = int(match.group(1))
            if dest in valid_entries:
                destinations.add(dest)

        # Pattern 2: "→ 123" (arrow followed by number)
        for match in re.finditer(r'→\s*(\d+)', text):
            dest = int(match.group(1))
            if dest in valid_entries:
                destinations.add(dest)

        # Update trace_numbers
        new_trace = sorted(list(destinations))
        old_trace = entry.get('trace_numbers', [])

        if new_trace != old_trace:
            entry['trace_numbers'] = new_trace
            fixed_count += 1

            if not new_trace:
                orphan_count += 1
                print(f"Entry {num:3d}: ❌ NO DESTINATIONS FOUND (DEAD END)")
            elif not old_trace:
                print(f"Entry {num:3d}: ✅ Added destinations {new_trace[:3]}...")

    # Save
    with open(filepath, 'w') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"\n" + "="*60)
    print(f"✅ Fixed {fixed_count} entries")
    print(f"❌ Dead ends (no destinations): {orphan_count}")
    print(f"="*60)

    # List the dead ends
    dead_ends = [e['number'] for e in entries if not e.get('trace_numbers')]
    if dead_ends:
        print(f"\nDead-end entries that need manual fixing:")
        print(dead_ends)
        return dead_ends

    return []

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        filepath = 'entries_with_rolls.json'
    else:
        filepath = sys.argv[1]

    dead_ends = fix_all_destinations(filepath)

    if dead_ends:
        print(f"\n⚠️  {len(dead_ends)} entries have NO destinations")
        print("These need manual fixes or are intentional endings")
