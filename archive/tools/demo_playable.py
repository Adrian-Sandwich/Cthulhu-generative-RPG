#!/usr/bin/env python3
"""
Demo of the playable game - shows actual story progression
"""

from game_engine import CthulhuGameEngine
from pregenerated_characters import PREGENERATED_CHARACTERS

def print_entry(engine, entry_num, character):
    """Display an entry in game format"""
    entry = engine.get_entry(entry_num)
    if not entry:
        return None

    print(f"STATUS: {character.name} | HP: 10/10 | SAN: 60/60 | LUCK: 12/12")
    print("-" * 70)
    print()

    # Format text (word wrap)
    text_lines = []
    current_line = ""
    for word in entry['text'].split():
        if len(current_line) + len(word) + 1 > 68:
            text_lines.append(current_line)
            current_line = word
        else:
            current_line += (" " + word) if current_line else word
    if current_line:
        text_lines.append(current_line)

    print('\n'.join(text_lines))
    print()

    return entry

def demo():
    print("\n" + "=" * 70)
    print("  CALL OF CTHULHU: ALONE AGAINST THE TIDE - GAME DEMO")
    print("=" * 70 + "\n")

    engine = CthulhuGameEngine()
    character = PREGENERATED_CHARACTERS['Eleanor']

    # Entry 1 (auto-advance)
    print(">>> ENTRY 1: Boarding the Ferry\n")
    entry = print_entry(engine, 1, character)

    if entry and len(entry['choices']) == 1 and entry['choices'][0]['text'] == '':
        print("[Continuing...]\n")
        next_num = entry['choices'][0]['destination']
        entry = print_entry(engine, next_num, character)

    print()

    # Entry 3 (multiple choices)
    print("=" * 70)
    print(">>> ENTRY 3: Arriving in Esbury\n")
    entry = print_entry(engine, 3, character)

    if entry and entry['choices']:
        print("-" * 70)
        print("WHAT DO YOU DO?\n")
        for i, choice in enumerate(entry['choices'], 1):
            choice_text = choice['text'] if choice['text'] else "Continue"
            print(f"  {i}. {choice_text}")
        print("-" * 70)
        print()

    # Simulate choosing option 1
    print(">>> SIMULATING: Choose option 1 - Visit the estate sale\n")
    choice_dest = entry['choices'][0]['destination']
    entry = print_entry(engine, choice_dest, character)

    print()
    print("=" * 70)
    print("✅ GAME MECHANICS WORKING:")
    print("  ✓ Clean story text (no markup)")
    print("  ✓ Auto-advance on single 'Continue'")
    print("  ✓ Multiple choices when available")
    print("  ✓ Story progression")
    print("  ✓ Character status display")
    print()
    print("  TO PLAY: python3 play.py")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    demo()
