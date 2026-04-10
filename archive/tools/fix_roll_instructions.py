#!/usr/bin/env python3
"""
Fix roll instructions that are being shown as menu options
These should be hidden from the player or converted to clearer choices
"""

import json
import re

def is_roll_instruction(text):
    """Check if this is a game rule instruction, not a player choice"""
    roll_keywords = [
        'make a ', 'make an ', 'roll:', 'sanity check',
        'listen roll', 'dodge roll', 'appraise roll', 'archaeology roll',
        'psychology roll', 'luck roll', 'dex roll', 'str roll', 'pow roll',
        'stealth roll', 'fighting', 'swim roll', 'locksmith roll'
    ]
    return any(keyword in text.lower() for keyword in roll_keywords)

def clean_entry_choices(entry):
    """Remove roll instructions from choices, convert to clear actions"""
    if not entry['choices']:
        return entry

    cleaned_choices = []

    for choice in entry['choices']:
        if is_roll_instruction(choice['text']):
            # Skip roll instruction choices - they confuse players
            # The narrator will handle the roll, not show it as a menu option
            continue
        else:
            # Keep legitimate player choices
            cleaned_choices.append(choice)

    entry['choices'] = cleaned_choices
    return entry

def main():
    with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'r') as f:
        data = json.load(f)

    total_entries = len(data['entries'])
    fixed_count = 0
    removed_choices = 0

    print("=" * 70)
    print("FIXING ROLL INSTRUCTION PRESENTATION")
    print("=" * 70 + "\n")

    for entry in data['entries']:
        original_choices = len(entry['choices'])
        entry = clean_entry_choices(entry)
        removed = original_choices - len(entry['choices'])

        if removed > 0:
            fixed_count += 1
            removed_choices += removed
            print(f"Entry {entry['number']:3d}: Removed {removed} roll instruction(s)")

    # Save corrected data
    with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"RESULTS")
    print(f"{'=' * 70}")
    print(f"Entries processed: {total_entries}")
    print(f"Entries fixed: {fixed_count}")
    print(f"Roll instructions removed: {removed_choices}")
    print(f"\n✓ Saved corrected adventure_data.json")
    print(f"{'=' * 70}\n")

if __name__ == '__main__':
    main()
