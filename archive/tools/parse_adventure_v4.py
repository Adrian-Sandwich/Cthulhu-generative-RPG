#!/usr/bin/env python3
"""
Final adventure parser - removes choice markup from text
"""

import re
import json
from pathlib import Path

def parse_adventure(text_file):
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
    full_text = '\n'.join(lines)

    # Extract traces (very end)
    traces = []
    trace_match = re.search(r'\(([^)]+)\)\s*$', full_text)
    if trace_match:
        trace_str = trace_match.group(1)
        for item in trace_str.split(','):
            item = item.strip()
            if item.isdigit():
                traces.append(int(item))
        full_text = full_text[:trace_match.start()].rstrip()

    # Extract choices
    choices = []

    # Pattern 1: "• [text], go to NUMBER" or "• To [text], go to NUMBER"
    for match in re.finditer(r'•\s+(?:To\s+)?([^•\n]*?)\s+go to\s+(\d+)', full_text):
        choice_text = match.group(1).strip()
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
        if not any(c['destination'] == destination for c in choices):
            choices.append({
                'text': choice_text,
                'destination': destination,
                'type': 'conditional'
            })

    # Pattern 3: "• Go to NUMBER" (standalone, becomes "Continue")
    for match in re.finditer(r'^•\s*(?:Go\s+)?to\s+(\d+)\s*\.?\s*$', full_text, re.MULTILINE | re.IGNORECASE):
        destination = int(match.group(1))
        if not any(c['destination'] == destination for c in choices):
            choices.append({
                'text': '',  # Empty = will be treated as continue
                'destination': destination,
                'type': 'next'
            })

    # CLEAN TEXT: Remove ALL choice markup
    text_clean = full_text

    # Remove "• To ..., go to X" patterns
    text_clean = re.sub(r'•\s+(?:To\s+)?[^•\n]*?go to\s+\d+', '', text_clean, flags=re.MULTILINE)
    
    # Remove "If ..., go to X" patterns
    text_clean = re.sub(r'If\s+[^,•\n]*?(?:,\s*)?go to\s+\d+', '', text_clean, flags=re.IGNORECASE | re.MULTILINE)
    
    # Remove standalone "• Go to X"
    text_clean = re.sub(r'^•\s*(?:Go\s+)?to\s+\d+\s*\.?\s*$', '', text_clean, flags=re.MULTILINE | re.IGNORECASE)

    # Collapse multiple spaces/newlines
    text_clean = re.sub(r'\n\n+', '\n', text_clean)  # Remove extra blank lines
    text_clean = re.sub(r' +', ' ', text_clean)  # Collapse spaces
    text_clean = text_clean.strip()

    return {
        'number': number,
        'text': text_clean,
        'choices': choices,
        'traces': traces
    }

def main():
    print("Parsing adventure entries (v4 - clean text)...")
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

    # Verify entry 1 is clean
    print("\n=== ENTRY 1 VERIFICATION ===")
    entry1 = entries_list[0]
    print(f"Text:\n{entry1['text']}\n")
    print(f"Choices: {len(entry1['choices'])}")
    for choice in entry1['choices']:
        print(f"  → '{choice['text']}' → {choice['destination']}")

    # Check for any remaining bullet points
    print("\n=== CHECKING FOR REMAINING BULLETS ===")
    bullets_found = 0
    for entry in entries_list:
        if '•' in entry['text']:
            bullets_found += 1
            print(f"Entry {entry['number']}: Found bullet")
    
    if bullets_found == 0:
        print("✓ No bullets found in text (clean!)")
    else:
        print(f"⚠ {bullets_found} entries still have bullets")

if __name__ == '__main__':
    main()
