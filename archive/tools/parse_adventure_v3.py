#!/usr/bin/env python3
"""
Final adventure parser with improved choice extraction
"""

import re
import json
from pathlib import Path

def parse_adventure(text_file):
    """Parse adventure entries with robust choice parsing"""

    with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    adventure_start = content.find("Our story begins")
    if adventure_start == -1:
        adventure_start = content.find("ALONE AGAINST THE TIDE\nSTART")

    content = content[adventure_start:]
    lines = content.split('\n')

    entries = {}
    current_entry = None
    current_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped.isdigit() and 1 <= int(stripped) <= 243:
            if current_entry is not None:
                entries[current_entry] = parse_entry(current_entry, current_lines)
            current_entry = int(stripped)
            current_lines = []
        elif current_entry is not None:
            current_lines.append(line)

    if current_entry is not None:
        entries[current_entry] = parse_entry(current_entry, current_lines)

    return entries

def parse_entry(number, lines):
    """Parse a single entry with better choice extraction"""
    full_text = '\n'.join(lines)

    # Extract traces (very end, in parentheses)
    traces = []
    trace_match = re.search(r'\(([^)]+)\)\s*$', full_text)
    if trace_match:
        trace_str = trace_match.group(1)
        for item in trace_str.split(','):
            item = item.strip()
            if item.isdigit():
                traces.append(int(item))
        full_text = full_text[:trace_match.start()].rstrip()

    # Extract choices - more robust patterns
    choices = []

    # Pattern 1: "• [text], go to NUMBER"
    for match in re.finditer(r'•\s+([^•\n]*?)\s+go to\s+(\d+)', full_text):
        choice_text = match.group(1).strip().replace('To ', '', 1)
        destination = int(match.group(2))
        choices.append({
            'text': choice_text,
            'destination': destination,
            'type': 'choice'
        })

    # Pattern 2: "If [text], go to NUMBER"
    for match in re.finditer(r'If\s+([^,•\n]*?)\s*(?:,\s*)?go to\s+(\d+)', full_text, re.IGNORECASE):
        choice_text = match.group(1).strip()
        destination = int(match.group(2))
        # Avoid duplicates
        if not any(c['destination'] == destination for c in choices):
            choices.append({
                'text': choice_text,
                'destination': destination,
                'type': 'conditional'
            })

    # Pattern 3: Single line like "• Go to 12."
    for match in re.finditer(r'^•\s*[Gg]o to\s+(\d+)\s*\.?\s*$', full_text, re.MULTILINE):
        destination = int(match.group(1))
        if not any(c['destination'] == destination for c in choices):
            choices.append({
                'text': '(Continue)',
                'destination': destination,
                'type': 'next'
            })

    # Remove choice markers from text for clean display
    text_clean = re.sub(r'•\s+[^•\n]*?go to\s+\d+', '', full_text, flags=re.MULTILINE)
    text_clean = re.sub(r'If\s+[^,•\n]*?(?:,\s*)?go to\s+\d+', '', text_clean, flags=re.IGNORECASE | re.MULTILINE)
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()

    return {
        'number': number,
        'text': text_clean,
        'choices': choices,
        'traces': traces
    }

def main():
    print("Parsing adventure entries (v3)...")
    entries = parse_adventure('/tmp/adventure_full.txt')

    print(f"Found {len(entries)} entries")

    entries_list = [entries[num] for num in sorted(entries.keys())]

    adventure_data = {
        'title': 'Alone Against the Tide',
        'description': 'A solo horror adventure for Call of Cthulhu 7th Edition',
        'author': 'Nicholas Johnson',
        'setting': 'Esbury, Massachusetts - 1920s',
        'total_entries': len(entries_list),
        'entries': entries_list
    }

    output_path = Path('/Users/adrianmedina/src/Cthulhu/adventure_data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(adventure_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved {len(entries_list)} entries")

    # Verify entry 1
    print("\n=== ENTRY 1 VERIFICATION ===")
    entry1 = entries_list[0]
    print(f"Entry {entry1['number']}:")
    print(f"Text: {entry1['text'][:80]}...")
    print(f"Choices: {len(entry1['choices'])}")
    for choice in entry1['choices']:
        print(f"  → {choice['text'][:40]} → {choice['destination']}")

    # Check total choices
    total_choices = sum(len(e['choices']) for e in entries_list)
    print(f"\nTotal choices: {total_choices}")

if __name__ == '__main__':
    main()
