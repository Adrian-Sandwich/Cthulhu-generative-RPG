#!/usr/bin/env python3
"""
Parser for Call of Cthulhu: Alone Against the Tide adventure
Converts PDF text to structured JSON with all 243 entries
"""

import re
import json
from pathlib import Path

def parse_adventure(text_file):
    """Parse adventure entries from text file"""

    with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Find where the actual adventure starts (after "ALONE AGAINST THE TIDE")
    adventure_start = content.find("ALONE AGAINST\nTHE TIDE\nSTART")
    if adventure_start == -1:
        adventure_start = content.find("Our story begins")

    content = content[adventure_start:]

    # Split into entries by looking for entry numbers at the start of lines
    # Entries are: number on own line, then text, then "(numbers)" at end
    entries = {}

    # Pattern: entry number (1-3 digits) followed by content until next number or end
    # More sophisticated: look for line with just a number
    lines = content.split('\n')

    current_entry = None
    current_text = []
    current_choices = []

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Check if this line is just a number (new entry)
        if line_stripped.isdigit() and 1 <= int(line_stripped) <= 243:
            # Save previous entry if exists
            if current_entry is not None:
                entries[current_entry] = {
                    'number': current_entry,
                    'text': '\n'.join(current_text).strip(),
                    'choices': parse_choices('\n'.join(current_text)),
                    'traces': parse_traces(current_text[-1] if current_text else '')
                }

            current_entry = int(line_stripped)
            current_text = []

        elif current_entry is not None:
            current_text.append(line)

    # Save last entry
    if current_entry is not None:
        entries[current_entry] = {
            'number': current_entry,
            'text': '\n'.join(current_text).strip(),
            'choices': parse_choices('\n'.join(current_text)),
            'traces': parse_traces(current_text[-1] if current_text else '')
        }

    return entries

def parse_choices(text):
    """Extract choices/navigation from entry text"""
    choices = []

    # Look for patterns like "• Go to 15." or "• To visit X, go to 15."
    # Also "If ... go to X."

    # Pattern 1: "• To ..., go to 15."
    pattern1 = r'•\s+(?:To\s+)?([^,•]*?)\s*(?:,\s*)?go to (\d+)'

    # Pattern 2: "If ... go to X"
    pattern2 = r'If\s+([^,•]*?)\s*(?:,\s*)?go to (\d+)'

    for match in re.finditer(pattern1, text, re.IGNORECASE):
        choice_text = match.group(1).strip()
        destination = int(match.group(2))
        choices.append({
            'text': choice_text,
            'destination': destination,
            'type': 'choice'
        })

    for match in re.finditer(pattern2, text, re.IGNORECASE):
        choice_text = match.group(1).strip()
        destination = int(match.group(2))
        choices.append({
            'text': choice_text,
            'destination': destination,
            'type': 'conditional'
        })

    return choices

def parse_traces(last_line):
    """Extract trace numbers (entries you could come from)"""
    # Traces are at the end in format: (1, 2, 3) or (Beginning)
    traces = []

    match = re.search(r'\(([^)]+)\)', last_line)
    if match:
        trace_str = match.group(1)
        # Split by comma and convert to numbers (ignore "Beginning", "THE END", etc.)
        for item in trace_str.split(','):
            item = item.strip()
            if item.isdigit():
                traces.append(int(item))

    return traces

def main():
    # Parse the adventure
    print("Parsing adventure entries...")
    entries = parse_adventure('/tmp/adventure_full.txt')

    print(f"Found {len(entries)} entries")

    # Convert to list sorted by number for JSON
    entries_list = []
    for num in sorted(entries.keys()):
        entry = entries[num]
        # Clean up text
        entry['text'] = re.sub(r'\s+', ' ', entry['text']).strip()
        entries_list.append(entry)

    # Create final structure
    adventure_data = {
        'title': 'Alone Against the Tide',
        'description': 'A solo horror adventure for Call of Cthulhu 7th Edition',
        'author': 'Nicholas Johnson',
        'total_entries': len(entries_list),
        'entries': entries_list
    }

    # Save to JSON
    output_path = Path('/Users/adrianmedina/src/Cthulhu/adventure_data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(adventure_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved to {output_path}")

    # Print sample entries
    print("\n=== SAMPLE ENTRIES ===")
    for i in range(min(3, len(entries_list))):
        entry = entries_list[i]
        print(f"\nEntry #{entry['number']}:")
        print(f"Text: {entry['text'][:200]}...")
        print(f"Choices: {len(entry['choices'])}")
        for choice in entry['choices'][:2]:
            print(f"  → {choice['text']} → Entry {choice['destination']}")
        print(f"Traces: {entry['traces']}")

if __name__ == '__main__':
    main()
