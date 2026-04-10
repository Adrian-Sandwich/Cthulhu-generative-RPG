#!/usr/bin/env python3
"""
Transform roll instructions into clearer player-facing options
Instead of "Make a Dodge roll: if you succeed," show "Attempt to dodge:"
"""

import json
import re

def clean_roll_text(text):
    """Transform roll instructions into clear action text"""

    # Pattern: "Make a X roll: if you succeed," -> "Attempt X"
    text = re.sub(r'Make a\s+(\w+(?:\s+\w+)*)\s+roll:\s+if\s+you\s+succeed,?',
                  r'Attempt \1:', text, flags=re.IGNORECASE)

    # Pattern: "Make an X roll: if you succeed," -> "Attempt X"
    text = re.sub(r'Make an\s+(\w+(?:\s+\w+)*)\s+roll:\s+if\s+you\s+succeed,?',
                  r'Attempt \1:', text, flags=re.IGNORECASE)

    # Pattern: "if you fail," -> remove (usually paired with success option)
    text = re.sub(r',?\s*if\s+you\s+fail,?', '', text, flags=re.IGNORECASE)

    # Clean up double spaces and commas
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r',\s*,', ',', text)

    return text

def main():
    with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'r') as f:
        data = json.load(f)

    total_entries = len(data['entries'])
    cleaned_count = 0
    total_cleaned_choices = 0

    print("=" * 70)
    print("CLEANING UP ROLL INSTRUCTION DISPLAY")
    print("=" * 70 + "\n")

    for entry in data['entries']:
        any_cleaned = False

        for choice in entry['choices']:
            original = choice['text']
            cleaned = clean_roll_text(original)

            if cleaned != original:
                choice['text'] = cleaned
                any_cleaned = True
                total_cleaned_choices += 1

        if any_cleaned:
            cleaned_count += 1
            print(f"Entry {entry['number']:3d}: Cleaned {len([c for c in entry['choices'] if 'attempt' in c['text'].lower()])} option(s)")

    # Save corrected data
    with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"RESULTS")
    print(f"{'=' * 70}")
    print(f"Entries processed: {total_entries}")
    print(f"Entries cleaned: {cleaned_count}")
    print(f"Choice texts cleaned: {total_cleaned_choices}")
    print(f"\n✓ Saved corrected adventure_data.json")
    print(f"{'=' * 70}\n")

if __name__ == '__main__':
    main()
