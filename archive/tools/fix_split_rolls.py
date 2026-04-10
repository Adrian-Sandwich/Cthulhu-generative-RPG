#!/usr/bin/env python3
"""
Fix split roll instructions that are incorrectly divided into two options
When parser sees "Make a Dodge roll: if you succeed," followed by "you survive",
it should be ONE roll with success/failure destinations, not two separate options.
"""

import json
import re

def extract_roll_skill(text):
    """Extract skill name from roll instruction"""
    match = re.search(r'Make\s+a(?:n)?\s+([a-z\s\(\)]+?)(?:\s+roll)?:', text, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return None

def is_split_roll(choice1_text, choice2_text):
    """Check if two choices form a split roll instruction"""
    c1 = choice1_text.lower()
    c2 = choice2_text.lower()

    # Pattern: "Make a X roll: if you succeed," followed by "you fail/survive"
    if ('make a' in c1 or 'make an' in c1) and ('roll' in c1):
        if 'if you succeed' in c1 and ('you fail' in c2 or 'you survive' in c2):
            return True

    return False

def merge_split_roll(entry, idx1, idx2):
    """Merge two choice objects into one roll with success/failure destinations"""
    choice1 = entry['choices'][idx1]
    choice2 = entry['choices'][idx2]

    skill = extract_roll_skill(choice1['text'])
    if not skill:
        return False

    # Determine destinations
    success_dest = choice1.get('destination')
    failure_dest = choice2.get('destination')

    if not success_dest or not failure_dest:
        return False

    # Create merged roll choice
    merged = {
        'text': f'Attempt {skill.title()}:',
        'destination': success_dest,
        'type': 'choice',
        'is_roll': True,
        'skill': skill,
        'success_destination': success_dest,
        'failure_destination': failure_dest
    }

    # Remove old choices and add merged
    entry['choices'].pop(max(idx1, idx2))
    entry['choices'].pop(min(idx1, idx2))
    entry['choices'].insert(min(idx1, idx2), merged)

    return True

def main():
    with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'r') as f:
        data = json.load(f)

    print("=" * 80)
    print("  FIXING SPLIT ROLL INSTRUCTIONS")
    print("=" * 80 + "\n")

    fixed_count = 0
    entries_fixed = []

    for entry in data['entries']:
        choices = entry.get('choices', [])

        # Process in reverse to avoid index issues when popping
        idx = len(choices) - 2

        while idx >= 0:
            if idx < len(choices) - 1:
                if is_split_roll(choices[idx]['text'], choices[idx + 1]['text']):
                    skill = extract_roll_skill(choices[idx]['text'])
                    success_dest = choices[idx]['destination']
                    failure_dest = choices[idx + 1]['destination']

                    if skill and success_dest and failure_dest:
                        # Record before modification
                        entries_fixed.append({
                            'entry': entry['number'],
                            'skill': skill,
                            'success': success_dest,
                            'failure': failure_dest
                        })

                        # Create merged roll choice
                        merged = {
                            'text': f'Attempt {skill.title()}:',
                            'destination': success_dest,
                            'type': 'choice',
                            'is_roll': True,
                            'skill': skill,
                            'success_destination': success_dest,
                            'failure_destination': failure_dest
                        }

                        # Remove old choices and add merged
                        entry['choices'].pop(idx + 1)
                        entry['choices'].pop(idx)
                        entry['choices'].insert(idx, merged)
                        fixed_count += 1

            idx -= 1

    # Save
    with open('/Users/adrianmedina/src/Cthulhu/adventure_data.json', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"FIXED: {fixed_count} split roll instructions\n")

    for fix in entries_fixed[:15]:
        print(f"  Entry {fix['entry']:3d}: {fix['skill']:20s} Success→{fix['success']} Failure→{fix['failure']}")

    if len(entries_fixed) > 15:
        print(f"  ... and {len(entries_fixed) - 15} more")

    print(f"\n{'=' * 80}\n✓ Saved to adventure_data.json\n")

if __name__ == '__main__':
    main()
