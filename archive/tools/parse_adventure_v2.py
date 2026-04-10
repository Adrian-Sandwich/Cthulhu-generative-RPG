#!/usr/bin/env python3
"""
Improved parser for Call of Cthulhu: Alone Against the Tide adventure
"""

import re
import json
from pathlib import Path

def parse_adventure(text_file):
    """Parse adventure entries with better text/choice separation"""

    with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Find where adventure starts
    adventure_start = content.find("Our story begins")
    if adventure_start == -1:
        adventure_start = content.find("ALONE AGAINST THE TIDE")

    content = content[adventure_start:]
    lines = content.split('\n')

    entries = {}
    current_entry = None
    current_lines = []

    for line in lines:
        stripped = line.strip()

        # Check if line is an entry number
        if stripped.isdigit() and 1 <= int(stripped) <= 243:
            # Save previous entry
            if current_entry is not None:
                entries[current_entry] = parse_entry(current_entry, current_lines)

            current_entry = int(stripped)
            current_lines = []
        elif current_entry is not None:
            current_lines.append(line)

    # Save last entry
    if current_entry is not None:
        entries[current_entry] = parse_entry(current_entry, current_lines)

    return entries

def parse_entry(number, lines):
    """Parse a single entry into text, choices, traces"""
    full_text = '\n'.join(lines)

    # Extract traces (at the very end)
    traces = []
    trace_match = re.search(r'\(([^)]+)\)\s*$', full_text)
    if trace_match:
        trace_str = trace_match.group(1)
        for item in trace_str.split(','):
            item = item.strip()
            if item.isdigit():
                traces.append(int(item))
        # Remove traces from text
        full_text = full_text[:trace_match.start()].rstrip()

    # Extract choices
    choices = []

    # Pattern 1: "• To [text], go to [number]"
    for match in re.finditer(r'•\s+([^•]*?)go to\s+(\d+)', full_text, re.DOTALL):
        choice_text = match.group(1).replace('To ', '').replace(',', '').strip()
        destination = int(match.group(2))
        if choice_text and destination:
            choices.append({
                'text': choice_text,
                'destination': destination,
                'type': 'choice'
            })

    # Pattern 2: "If [condition], go to [number]"
    for match in re.finditer(r'If\s+([^,•]*?)\s*,\s*go to\s+(\d+)', full_text, re.IGNORECASE):
        choice_text = match.group(1).strip()
        destination = int(match.group(2))
        if choice_text and destination:
            choices.append({
                'text': choice_text,
                'destination': destination,
                'type': 'conditional'
            })

    # Remove choice bullets from text
    text_clean = re.sub(r'•\s+[^•]*?go to\s+\d+', '', full_text, flags=re.DOTALL)
    text_clean = re.sub(r'If\s+[^,•]*?,\s*go to\s+\d+', '', text_clean, flags=re.IGNORECASE)
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()

    return {
        'number': number,
        'text': text_clean,
        'choices': choices,
        'traces': traces
    }

def main():
    print("Parsing adventure entries (improved)...")
    entries = parse_adventure('/tmp/adventure_full.txt')

    print(f"Found {len(entries)} entries")

    # Convert to sorted list
    entries_list = [entries[num] for num in sorted(entries.keys())]

    # Create adventure data
    adventure_data = {
        'title': 'Alone Against the Tide',
        'description': 'A solo horror adventure for Call of Cthulhu 7th Edition',
        'author': 'Nicholas Johnson',
        'setting': 'Esbury, Massachusetts - 1920s',
        'total_entries': len(entries_list),
        'entries': entries_list
    }

    # Save
    output_path = Path('/Users/adrianmedina/src/Cthulhu/adventure_data.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(adventure_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved {len(entries_list)} entries to {output_path}")
    print(f"✓ File size: {output_path.stat().st_size / 1024:.1f} KB")

    # Verify
    print("\n=== VERIFICATION ===")
    total_choices = sum(len(e['choices']) for e in entries_list)
    print(f"Total choices available: {total_choices}")
    print(f"Entries with traces: {len([e for e in entries_list if e['traces']])}")

if __name__ == '__main__':
    main()
