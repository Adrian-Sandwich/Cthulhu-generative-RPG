#!/usr/bin/env python3
"""
Parser v5 - More robust entry extraction
Uses better entry boundary detection
"""

import re
import json
from pathlib import Path

def parse_adventure_v5(text_file):
    """
    More robust parser that:
    1. Finds entry numbers reliably
    2. Captures all text until next entry number
    3. Properly separates choice text from narrative
    """

    with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Find start of actual adventure
    adventure_start = content.find("Our story begins")
    if adventure_start == -1:
        adventure_start = content.find("ALONE AGAINST THE TIDE\nSTART")

    content = content[adventure_start:]

    entries = {}

    # Split by entry numbers - look for lines that are JUST numbers
    # More reliable: look for "\n[number]\n" pattern
    entry_pattern = r'\n(\d{1,3})\n'

    splits = re.split(entry_pattern, content)

    # splits will be: [text_before_first, num1, text1, num2, text2, ...]
    # Process in pairs
    for i in range(1, len(splits), 2):
        entry_num = int(splits[i])
        entry_text = splits[i + 1] if i + 1 < len(splits) else ""

        if not (1 <= entry_num <= 243):
            continue

        # Parse this entry's content
        entry_data = parse_entry_content(entry_num, entry_text)
        entries[entry_num] = entry_data

    return entries

def parse_entry_content(num, text):
    """Parse individual entry"""

    # Extract traces (end, in parentheses)
    traces = []
    trace_match = re.search(r'\(([^)]+)\)\s*$', text)
    if trace_match:
        trace_str = trace_match.group(1)
        for item in trace_str.split(','):
            item = item.strip()
            if item.isdigit():
                traces.append(int(item))
        text = text[:trace_match.start()].rstrip()

    # Extract choices
    choices = []

    # Pattern 1: "• To ..., go to X" or "• ..., go to X"
    for match in re.finditer(r'•\s+(?:To\s+)?([^•\n]*?)\s+go to\s+(\d+)', text):
        choice_text = match.group(1).strip()
        destination = int(match.group(2))
        choices.append({
            'text': choice_text,
            'destination': destination,
            'type': 'choice'
        })

    # Pattern 2: "If ..., go to X"
    for match in re.finditer(r'If\s+([^,•\n]*?)\s*(?:,\s*)?go to\s+(\d+)', text, re.IGNORECASE):
        choice_text = match.group(1).strip()
        destination = int(match.group(2))
        if not any(c['destination'] == destination for c in choices):
            choices.append({
                'text': choice_text,
                'destination': destination,
                'type': 'conditional'
            })

    # Pattern 3: Standalone "• Go to X" or "Go to X"
    for match in re.finditer(r'^•?\s*(?:Go\s+)?to\s+(\d+)\s*\.?\s*$', text, re.MULTILINE | re.IGNORECASE):
        destination = int(match.group(1))
        if not any(c['destination'] == destination for c in choices):
            choices.append({
                'text': '',  # Empty = auto-continue
                'destination': destination,
                'type': 'next'
            })

    # Clean text: remove all choice markup
    text_clean = text

    # Remove "• To/Go ..., go to X" patterns
    text_clean = re.sub(r'•\s+(?:To\s+)?[^•\n]*?go to\s+\d+', '', text_clean, flags=re.MULTILINE)

    # Remove "If ..., go to X" patterns
    text_clean = re.sub(r'If\s+[^,•\n]*?(?:,\s*)?go to\s+\d+', '', text_clean, flags=re.IGNORECASE | re.MULTILINE)

    # Remove standalone "Go to X"
    text_clean = re.sub(r'^•?\s*(?:Go\s+)?to\s+\d+\s*\.?\s*$', '', text_clean, flags=re.MULTILINE | re.IGNORECASE)

    # Collapse multiple newlines
    text_clean = re.sub(r'\n\n+', '\n', text_clean)
    text_clean = re.sub(r' +', ' ', text_clean)
    text_clean = text_clean.strip()

    return {
        'number': num,
        'text': text_clean,
        'choices': choices,
        'traces': traces
    }

def main():
    print("Parsing adventure with Parser v5...")

    entries = parse_adventure_v5('/tmp/adventure_full.txt')
    print(f"Found {len(entries)} entries")

    entries_list = [entries[num] for num in sorted(entries.keys())]

    adventure = {
        'title': 'Alone Against the Tide',
        'description': 'A solo horror adventure for Call of Cthulhu 7th Edition',
        'author': 'Nicholas Johnson',
        'setting': 'Esbury, Massachusetts - 1920s',
        'total_entries': len(entries_list),
        'parser_version': 5,
        'entries': entries_list
    }

    output_path = Path('/Users/adrianmedina/src/Cthulhu/adventure_data.json')
    with open(output_path, 'w') as f:
        json.dump(adventure, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved {len(entries_list)} entries to {output_path}\n")

    # Verify key entries
    print("=== VERIFICATION ===")
    for num in [1, 12, 15, 17, 202]:
        entry = entries.get(num)
        if entry:
            print(f"\nEntry {num}:")
            print(f"  Text: {entry['text'][:100]}...")
            print(f"  Choices: {len(entry['choices'])}")
        else:
            print(f"\nEntry {num}: NOT FOUND")

if __name__ == '__main__':
    main()
