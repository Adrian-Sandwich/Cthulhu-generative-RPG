#!/usr/bin/env python3
"""
Extract roll mechanics from adventure text and create proper roll structures
Converts entries with roll instructions into actionable game mechanics
"""

import json
import re

def extract_roll_info(choice_text):
    """
    Extract roll type and required skill from choice text
    E.g., "Make a Dodge roll: if you succeed," → ("dodge", None)
    E.g., "Make an Archaeology roll: if you succeed," → ("archaeology", None)
    """

    # Pattern: "Make a/an [SKILL] roll"
    match = re.search(r'make\s+a(?:n)?\s+([a-z\s\-]+?)(?:\s+roll)?:', choice_text, re.IGNORECASE)
    if match:
        skill = match.group(1).strip()
        return skill.lower()
    return None

def parse_roll_destinations(entry_text, choices):
    """
    Parse success/failure destinations from entry text
    Returns dict with 'success' and 'failure' destination numbers
    """
    destinations = {'success': None, 'failure': None}

    # Look for patterns like "go to 132" in the text
    success_match = re.search(r'if\s+you\s+succeed.*?go to\s+(\d+)', entry_text, re.IGNORECASE | re.DOTALL)
    if success_match:
        destinations['success'] = int(success_match.group(1))

    # Look for failure outcomes
    fail_match = re.search(r'if\s+you\s+fail.*?go to\s+(\d+)', entry_text, re.IGNORECASE | re.DOTALL)
    if fail_match:
        destinations['failure'] = int(fail_match.group(1))

    # Alternative: check choice destinations
    if len(choices) >= 2:
        # Assume first choice is success, second is failure
        if not destinations['success']:
            destinations['success'] = choices[0].get('destination')
        if not destinations['failure'] and len(choices) > 1:
            destinations['failure'] = choices[1].get('destination')

    return destinations

def main():
    with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'r') as f:
        data = json.load(f)

    print("=" * 70)
    print("INTEGRATING ROLL MECHANICS")
    print("=" * 70 + "\n")

    roll_entries = []

    for entry in data['entries']:
        has_rolls = False

        for choice in entry['choices']:
            skill = extract_roll_info(choice['text'])
            if skill:
                has_rolls = True
                destinations = parse_roll_destinations(entry['text'], entry['choices'])

                # Mark this as a roll choice
                choice['is_roll'] = True
                choice['skill'] = skill
                choice['success_destination'] = destinations.get('success')
                choice['failure_destination'] = destinations.get('failure')

                print(f"Entry {entry['number']}: Found {skill} roll")
                print(f"  Success → {destinations['success']}, Failure → {destinations['failure']}")

                roll_entries.append(entry['number'])

        if has_rolls:
            print()

    # Save with roll metadata
    with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"RESULTS")
    print(f"{'=' * 70}")
    print(f"Entries with roll mechanics: {len(set(roll_entries))}")
    print(f"Total roll options integrated: {sum(1 for e in data['entries'] for c in e['choices'] if c.get('is_roll'))}")
    print(f"\n✓ Saved adventure_data.json with roll metadata")
    print(f"{'=' * 70}\n")

if __name__ == '__main__':
    main()
