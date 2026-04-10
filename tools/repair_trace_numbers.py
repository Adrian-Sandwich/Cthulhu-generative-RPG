#!/usr/bin/env python3
"""
Repair trace_numbers by extracting them from entry text.
Finds all "go to NNN" references in text and uses those as trace_numbers.
"""

import json
import re
from collections import defaultdict

def repair_entries(filepath):
    """Repair trace_numbers by parsing text"""

    with open(filepath, 'r') as f:
        entries = json.load(f)

    print(f"Loading {filepath}...")
    print(f"Total entries: {len(entries)}\n")

    fixed = 0
    errors = []

    # Build a set of valid entry numbers
    valid_entries = {e['number'] for e in entries}

    for entry in entries:
        num = entry['number']
        text = entry.get('text', '')
        old_trace = set(entry.get('trace_numbers', []))

        # Extract all "go to NNN" references
        new_trace = set(int(m) for m in re.findall(r'go to (\d+)', text, re.IGNORECASE))

        # Also check for standalone numbers (e.g., "→ 42" format)
        # but be careful not to catch random numbers
        # Only do this if we have arrow markers
        if '→' in text:
            # Look for → NNN patterns (arrow followed by number)
            arrow_refs = set(int(m) for m in re.findall(r'→\s*(\d+)', text))
            new_trace.update(arrow_refs)

        # Validate that all references exist
        invalid = new_trace - valid_entries
        if invalid:
            for inv in invalid:
                errors.append(f"Entry {num}: references non-existent entry {inv}")
            new_trace -= invalid

        # Compare and update if different
        if new_trace != old_trace:
            entry['trace_numbers'] = sorted(list(new_trace))
            fixed += 1

            if old_trace != new_trace:
                print(f"Entry {num:3d}: {sorted(old_trace)} → {sorted(new_trace)}")

    if errors:
        print(f"\n⚠️  Found {len(errors)} invalid references:")
        for err in errors[:10]:
            print(f"   {err}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more")

    # Save repaired file
    with open(filepath, 'w') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Fixed {fixed} entries")
    print(f"✅ Saved to {filepath}")

    return fixed, len(errors)

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 repair_trace_numbers.py <entries.json>")
        sys.exit(1)

    filepath = sys.argv[1]
    fixed, errors = repair_entries(filepath)

    if errors > 0:
        print(f"\n⚠️  WARNING: {errors} invalid references found")
        print("   These entries may have errors in the original PDF")
