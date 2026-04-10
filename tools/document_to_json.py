#!/usr/bin/env python3
"""
Convert story document format to game-playable JSON entries file.

Usage:
    python3 document_to_json.py story.txt > entries.json
    python3 document_to_json.py story.txt --output entries.json --validate
"""

import re
import json
import sys
from pathlib import Path
from collections import defaultdict


class StoryParser:
    """Parse story document in the standard Cthulhu format"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.entries = []
        self.graph = defaultdict(list)  # entry_num -> [destinations]
        self.errors = []
        self.warnings = []

    def parse(self):
        """Main parsing routine"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by entry markers: [ENTRY NNN]
        entry_blocks = re.split(r'\n(?=\[ENTRY \d+\])', content)

        for block in entry_blocks:
            if not block.strip():
                continue
            self._parse_entry(block)

        return self.entries, self.graph

    def _parse_entry(self, block):
        """Parse a single [ENTRY ...] block"""
        lines = block.strip().split('\n')

        # Extract entry number from first line
        match = re.match(r'\[ENTRY (\d+)\]', lines[0])
        if not match:
            self.errors.append(f"Invalid entry header: {lines[0]}")
            return

        entry_num = int(match.group(1))
        metadata = {}
        text_lines = []
        choice_lines = []

        in_choices = False
        for line in lines[1:]:
            # Metadata lines (start with [)
            if line.startswith('['):
                self._parse_metadata(line, metadata)
            # Choice marker
            elif line.strip().endswith(':'):
                in_choices = True
            # Choice lines (start with →)
            elif line.startswith('→'):
                choice_lines.append(line)
                in_choices = True
            # Text lines
            elif line.strip():
                if not in_choices:
                    text_lines.append(line)

        # Combine text, clean whitespace
        text = '\n'.join(text_lines).strip()
        text = re.sub(r'\n+', ' ', text)  # Multi-line to single
        text = re.sub(r'\[CLUE\]', '', text)  # Remove markup
        text = re.sub(r'\[CHOICE\]', '', text)
        text = re.sub(r'\[CONSEQUENCE\]', '', text)
        text = re.sub(r'\[NPC: [^\]]+\]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()  # Normalize spaces

        # Parse choices and extract destinations
        choices, trace_numbers = self._parse_choices(choice_lines, entry_num)

        # Build entry object
        entry = {
            'number': entry_num,
            'text': text,
            'choices': choices,
            'trace_numbers': sorted(list(set(trace_numbers))),
            'character_name': metadata.get('character'),
            'is_adventure_entry': True,
            'entry_type': metadata.get('type', 'adventure'),
            'rolls': self._build_rolls(metadata),
            'metadata': {
                'title': metadata.get('title', ''),
                'tags': metadata.get('tags', []),
                'sanity_mod': metadata.get('sanity', 0),
                'hp_mod': metadata.get('hp', 0),
                'roll': metadata.get('roll', None),
            }
        }

        self.entries.append(entry)
        self.graph[entry_num] = trace_numbers

    def _parse_metadata(self, line, metadata):
        """Parse a metadata line like [TYPE: adventure]"""
        match = re.match(r'\[(\w+):\s*([^\]]+)\]', line)
        if not match:
            return

        key = match.group(1).lower()
        value = match.group(2).strip()

        if key == 'type':
            metadata['type'] = value
        elif key == 'title':
            metadata['title'] = value
        elif key == 'tags':
            metadata['tags'] = [t.strip() for t in value.split(',')]
        elif key == 'roll':
            metadata['roll'] = value
        elif key == 'sanity':
            metadata['sanity'] = int(value)
        elif key == 'hp':
            metadata['hp'] = int(value)
        elif key == 'character':
            metadata['character'] = value

    def _parse_choices(self, choice_lines, entry_num):
        """Extract destination numbers from choice lines"""
        choices = []
        destinations = []

        for line in choice_lines:
            # Format: → Description, go to NNN
            # or: → go to NNN
            # or: → NNN
            match = re.search(r'go to (\d+)', line, re.IGNORECASE)
            if match:
                dest = int(match.group(1))
                destinations.append(dest)
                # Clean up the choice text
                choice_text = re.sub(r'\s*go to \d+\s*$', '', line, flags=re.IGNORECASE)
                choice_text = choice_text.replace('→', '').strip()
                if choice_text:
                    choices.append(choice_text)
            elif re.search(r'→\s*(\d+)\s*$', line):
                # Just a number with arrow
                match = re.search(r'→\s*(\d+)\s*$', line)
                dest = int(match.group(1))
                destinations.append(dest)
            else:
                # No destination, just a choice
                choice_text = line.replace('→', '').strip()
                if choice_text:
                    choices.append(choice_text)

        return choices, destinations

    def _build_rolls(self, metadata):
        """Convert roll metadata to rolls array"""
        rolls = []
        if 'roll' in metadata:
            roll_str = metadata['roll']  # "library/normal" or "dodge/hard"
            match = re.match(r'(\w+)/(\w+)', roll_str)
            if match:
                skill, difficulty = match.groups()
                rolls.append({
                    'type': 'skill_check',
                    'skill': skill,
                    'difficulty': difficulty
                })
        return rolls

    def validate(self):
        """Check for structural issues"""
        all_numbers = {e['number'] for e in self.entries}

        for entry in self.entries:
            for dest in entry['trace_numbers']:
                if dest not in all_numbers:
                    self.errors.append(
                        f"Entry {entry['number']}: destination {dest} does not exist"
                    )

        # Check for orphaned entries (no incoming links except 001)
        entry_numbers = {e['number'] for e in self.entries}
        incoming = defaultdict(list)

        for entry in self.entries:
            for dest in entry['trace_numbers']:
                incoming[dest].append(entry['number'])

        for num in sorted(entry_numbers):
            if num != 1 and num not in incoming:
                self.warnings.append(f"Entry {num} has no incoming links (orphaned)")

        # Check for entry number gaps
        sorted_nums = sorted(entry_numbers)
        for i, num in enumerate(sorted_nums[:-1]):
            if sorted_nums[i + 1] != num + 1:
                gap = sorted_nums[i + 1] - num
                self.warnings.append(f"Gap of {gap} entries between {num} and {sorted_nums[i+1]}")

        return len(self.errors) == 0

    def report(self):
        """Print validation report"""
        print("╔════════════════════════════════════════════════════════════════╗", file=sys.stderr)
        print("║              STORY DOCUMENT PARSING REPORT                     ║", file=sys.stderr)
        print("╚════════════════════════════════════════════════════════════════╝", file=sys.stderr)

        print(f"\n📖 Total entries parsed: {len(self.entries)}", file=sys.stderr)

        if self.entries:
            entry_range = (min(e['number'] for e in self.entries),
                          max(e['number'] for e in self.entries))
            print(f"📊 Entry range: {entry_range[0]:03d} to {entry_range[1]:03d}", file=sys.stderr)

            total_text = sum(len(e['text']) for e in self.entries)
            print(f"📝 Total text: {total_text:,} characters", file=sys.stderr)

            total_choices = sum(len(e['choices']) for e in self.entries)
            print(f"🔀 Total choices: {total_choices}", file=sys.stderr)

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):", file=sys.stderr)
            for err in self.errors[:10]:
                print(f"   • {err}", file=sys.stderr)
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more", file=sys.stderr)

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):", file=sys.stderr)
            for warn in self.warnings[:5]:
                print(f"   • {warn}", file=sys.stderr)
            if len(self.warnings) > 5:
                print(f"   ... and {len(self.warnings) - 5} more", file=sys.stderr)

        if not self.errors and not self.warnings:
            print("\n✅ Document is valid!", file=sys.stderr)

        print("", file=sys.stderr)

    def to_json(self):
        """Export as JSON compatible with game engine"""
        return json.dumps(self.entries, indent=2, ensure_ascii=False)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert story document to game entries JSON'
    )
    parser.add_argument('document', help='Path to story document (.txt)')
    parser.add_argument('--output', '-o', help='Output JSON file (default: stdout)')
    parser.add_argument('--validate', '-v', action='store_true',
                       help='Validate and report issues')
    parser.add_argument('--pretty', '-p', action='store_true',
                       help='Pretty-print JSON (default: compact)')

    args = parser.parse_args()

    # Check file exists
    if not Path(args.document).exists():
        print(f"❌ File not found: {args.document}", file=sys.stderr)
        sys.exit(1)

    # Parse
    print(f"📖 Parsing {args.document}...", file=sys.stderr)
    story_parser = StoryParser(args.document)
    story_parser.parse()

    # Validate if requested
    if args.validate or args.output:
        is_valid = story_parser.validate()
        story_parser.report()
        if not is_valid:
            sys.exit(1)

    # Output
    json_output = story_parser.to_json()

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_output)
        print(f"✅ Written to {args.output}", file=sys.stderr)
    else:
        print(json_output)


if __name__ == '__main__':
    main()
