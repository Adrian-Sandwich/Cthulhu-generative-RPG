#!/usr/bin/env python3
"""
ALONE AGAINST THE DARK - IMMERSIVE VERSION
Full atmospheric experience with rich descriptions and immersion
"""

import os
import sys
import json
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.game_immersive import ImmersiveGameEngine
from core.game_universal import Investigator

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_centered(text, width=80):
    """Print text centered"""
    lines = text.split('\n')
    for line in lines:
        if line.strip():
            padding = (width - len(line)) // 2
            print(' ' * padding + line)
        else:
            print()

def title_screen():
    """Show title screen"""
    clear()
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              ALONE AGAINST THE DARK - IMMERSIVE EDITION                  ║
║                                                                           ║
║                        Call of Cthulhu Adventure                         ║
║                                                                           ║
║                    "In darkness, they are always waiting"                ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    input("Press ENTER to continue...")

def setup_game():
    """Setup: choose adventure and investigator"""
    clear()
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                        ADVENTURE SELECTION                               ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    print("\nCHOOSE YOUR ADVENTURE:\n")
    print("  1) Point Black Lighthouse (26 entries - The Awakening)")
    print("  2) Tide (243 entries - Coastal Investigation)")
    print("  3) Dark (594 entries - Antarctic Expedition)\n")

    while True:
        choice = input("  Enter 1-3: ").strip()
        if choice in ['1', '2', '3']:
            break
        print("  Invalid choice. Try again.")

    if choice == '1':
        entries_file = 'adventures/point_black/mini_adventure.json'
        adventure_name = 'POINT BLACK LIGHTHOUSE'
        inv_file = 'adventures/point_black/investigators.json'
    elif choice == '2':
        entries_file = 'adventures/tide/entries_with_rolls.json'
        adventure_name = 'TIDE'
        inv_file = 'adventures/tide/investigators.json'
    else:
        entries_file = 'adventures/dark/entries_dark_594_final.json'
        adventure_name = 'DARK'
        inv_file = 'adventures/dark/investigators.json'

    clear()
    print(f"Alone Against the {adventure_name}\n")
    print("SELECT YOUR INVESTIGATOR:\n")

    # Load adventure-specific investigators
    try:
        with open(inv_file, 'r') as f:
            invs = json.load(f)
    except:
        # Create default investigators
        invs = [
            {
                'name': 'Detective Morgan',
                'occupation': 'Private Investigator',
                'starting_entry': 1,
                'characteristics': {
                    'STR': 65, 'CON': 65, 'SIZ': 60, 'DEX': 65,
                    'INT': 80, 'APP': 60, 'POW': 70, 'EDU': 85,
                    'HP': 13, 'SAN': 70, 'Luck': 50, 'Magic_Points': 14
                },
                'skills': {'Investigate': 60, 'Library': 50, 'Persuade': 40},
                'available_cash': 500
            }
        ]

    for i, inv in enumerate(invs[:4], 1):
        print(f"  {i}) {inv['name']:20} - {inv['occupation']}")

    print()
    while True:
        choice = input("  Enter 1-4: ").strip()
        if choice in ['1', '2', '3', '4']:
            inv_data = invs[int(choice) - 1]
            break
        print("  Invalid choice. Try again.")

    return entries_file, adventure_name, inv_data

# ═══════════════════════════════════════════════════════════════════════════

def show_destinations(engine, entry_num):
    """Show available destinations"""
    entry = engine.base_engine.get_entry(entry_num)
    if not entry:
        return

    trace = entry.get('trace_numbers', [])

    if not trace:
        print("\n  ⚠️  No destinations from this entry.")
        return

    print("\n" + "─" * 80)
    print("AVAILABLE OPTIONS:\n")

    for i, dest in enumerate(trace, 1):
        dest_entry = engine.base_engine.get_entry(dest)
        dest_title = ""
        if dest_entry and dest_entry.get('metadata', {}).get('title'):
            dest_title = f" - {dest_entry['metadata']['title']}"

        print(f"  {i}) Entry {dest:03d}{dest_title}")

    print("\n  Type a number or entry number directly")
    print("─" * 80)

def format_status_bar(engine, inv_data):
    """Immersive status bar"""
    return engine.get_status_bar(inv_data)

def show_help():
    """Show commands"""
    return """
COMMANDS:
  [NUMBER]     Go to entry (1-9 or entry number like 42)
  [r]oll       Attempt a skill check (if available)
  [i]nventory  Check your inventory
  [s]tatus     Full character status
  [h]elp       This help
  [q]uit       Save and quit

Type command and press ENTER.
"""

def format_status(engine, inv_data):
    """Show full character status"""
    output = "\n" + "─" * 80 + "\n"
    output += f"STATUS: {engine.game.investigator.name}\n"
    output += "─" * 80 + "\n\n"

    chars = inv_data['characteristics']
    inv = engine.game.investigator

    output += f"CHARACTERISTICS:\n"
    output += f"  STR:{chars['STR']:2} CON:{chars['CON']:2} SIZ:{chars['SIZ']:2} DEX:{chars['DEX']:2}\n"
    output += f"  INT:{chars['INT']:2} APP:{chars['APP']:2} POW:{chars['POW']:2} EDU:{chars['EDU']:2}\n"
    output += f"  HP:{chars['HP']:2} SAN:{chars['SAN']:2} Luck:{chars['Luck']:2} MP:{chars['Magic_Points']:2}\n\n"

    output += f"PROGRESS:\n"
    output += f"  Entry: {engine.game.current_entry}\n"
    output += f"  Visited: {len(engine.game.visited_entries)} locations\n"
    output += f"  Rolls: {len(engine.game.roll_history)}\n\n"

    return output

def play_game(entries_file, adventure_name, inv_data):
    """Main game loop"""

    # Create immersive engine
    engine = ImmersiveGameEngine(entries_file)

    # Create investigator
    inv = Investigator(
        name=inv_data['name'],
        skills=inv_data['skills'],
        characteristics=inv_data['characteristics']
    )

    # Start game
    engine.create_game(inv, inv_data['starting_entry'])

    clear()
    print(f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                    ✓ You are {inv.name:<46} ║
║                    ✓ Beginning Alone Against the {adventure_name:<23} ║
║                    ✓ Entry {engine.game.current_entry:<67} ║
║                                                                           ║
║                      "In the darkness, something stirs..."              ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    input("Press ENTER to begin your investigation...\n")

    # Main loop
    while True:
        clear()

        # Show current entry with full immersion
        engine.display_entry_immersive(engine.game.current_entry)

        # Show status bar
        print("\n" + "─" * 80)
        print(format_status_bar(engine, inv_data))

        # Show destinations
        show_destinations(engine, engine.game.current_entry)

        # Get command
        cmd = input("\n➜ ").strip().lower()

        # Parse command
        if cmd == 'q':
            # Quit
            if input("\n\nSave your investigation? (y/n): ").lower() == 'y':
                save_file = engine.save_game()
                print(f"✓ Saved to: {save_file}")
            print("\n\n      The lighthouse's light blinks in the darkness behind you.")
            print("      But you know it will always call...\n")
            break

        elif cmd == 'i':
            # Inventory
            clear()
            print("╔═══════════════════════════════════════════════════════════════════════════╗")
            print("║ INVENTORY                                                                 ║")
            print("╚═══════════════════════════════════════════════════════════════════════════╝\n")

            inv_list = engine.get_inventory()
            if inv_list:
                for item in inv_list:
                    print(f"  • {item}")
            else:
                print("  [Empty]")

            input("\nPress ENTER to continue...")

        elif cmd == 's':
            # Status
            clear()
            print(format_status(engine, inv_data))
            input("Press ENTER to continue...")

        elif cmd == 'h':
            # Help
            clear()
            print(show_help())
            input("\nPress ENTER to continue...")

        elif cmd == 'r':
            # Roll
            entry = engine.base_engine.get_entry(engine.game.current_entry)
            rolls = entry.get('rolls', [])

            if not rolls:
                clear()
                print("╔═══════════════════════════════════════════════════════════════════════════╗")
                print("║ No skill checks available in this location.                              ║")
                print("╚═══════════════════════════════════════════════════════════════════════════╝\n")
                input("Press ENTER to continue...")
            else:
                # Show available rolls
                clear()
                print("╔═══════════════════════════════════════════════════════════════════════════╗")
                print("║ SKILL CHECKS AVAILABLE                                                    ║")
                print("╚═══════════════════════════════════════════════════════════════════════════╝\n")

                for i, roll_data in enumerate(rolls, 1):
                    skill = roll_data.get('skill', 'unknown').upper()
                    difficulty = roll_data.get('difficulty', 'normal').upper()

                    # Check if this is a sanity check (POW roll with sanity_mod)
                    sanity_mod = entry.get('metadata', {}).get('sanity_mod', 0)
                    sanity_label = ""
                    if skill.upper() == 'POW' and sanity_mod != 0:
                        sanity_label = f" [SANITY CHECK]"

                    print(f"  {i}) {skill} ({difficulty}){sanity_label}")

                print("\n  Type number to attempt roll, or ENTER to skip:")
                roll_choice = input("➜ ").strip()

                if roll_choice.isdigit() and 1 <= int(roll_choice) <= len(rolls):
                    roll_data = rolls[int(roll_choice) - 1]
                    skill = roll_data.get('skill', 'investigate')
                    difficulty = roll_data.get('difficulty', 'normal').capitalize()

                    # Get target value from investigator skills or characteristics
                    inv = engine.game.investigator
                    inv_data_dict = inv_data['characteristics']

                    # Map skill to characteristic or default value
                    skill_targets = {
                        'investigate': 60,
                        'combat': inv_data_dict.get('DEX', 65),
                        'pow': inv_data_dict.get('POW', 70),
                        'psychology': 50,
                        'library': 50,
                        'occult': 50
                    }

                    target = skill_targets.get(skill.lower(), 60)

                    # Execute roll (get both message and success result)
                    roll_result = engine.execute_roll_with_result(skill, target, difficulty)
                    result_msg = roll_result['message']
                    roll_success = roll_result['success']

                    clear()
                    print("╔═══════════════════════════════════════════════════════════════════════════╗")
                    print("║ SKILL CHECK RESULT                                                        ║")
                    print("╚═══════════════════════════════════════════════════════════════════════════╝\n")
                    print(result_msg)

                    # Apply sanity loss if POW roll failed and there's a sanity_mod
                    sanity_mod = entry.get('metadata', {}).get('sanity_mod', 0)
                    if skill.upper() == 'POW' and sanity_mod < 0:
                        if not roll_success:  # FALLO
                            inv.characteristics['SAN'] += sanity_mod
                            if inv.characteristics['SAN'] < 0:
                                inv.characteristics['SAN'] = 0
                            print(f"\n⚠️  SANITY CHECK FAILED!")
                            print(f"    You lose {abs(sanity_mod)} sanity points.")
                            print(f"    Remaining SAN: {inv.characteristics['SAN']}")
                        else:  # ÉXITO
                            print(f"\n✓ SANITY CHECK PASSED!")
                            print(f"    You maintain your mental clarity.")

                    print("\n")
                    input("Press ENTER to continue...")

        elif cmd.isdigit():
            # Navigation
            num = int(cmd)
            entry = engine.base_engine.get_entry(engine.game.current_entry)
            trace = entry.get('trace_numbers', [])

            # Try option number first (1-9)
            if 1 <= num <= len(trace):
                destination = trace[num - 1]
                try:
                    engine.move_to_entry(destination)
                except Exception as e:
                    print(f"\n⚠ Error: {e}")
                    input("Press ENTER to continue...")

            elif num in trace:
                # Direct entry number
                try:
                    engine.move_to_entry(num)
                except Exception as e:
                    print(f"\n⚠ Error: {e}")
                    input("Press ENTER to continue...")
            else:
                # Invalid
                print(f"\n⚠ Entry {num} is not available from here")
                input("Press ENTER to continue...")

        else:
            if cmd:
                print(f"\n⚠ Unknown command: '{cmd}'")
                input("Press ENTER to continue...")


def main():
    """Main entry point"""
    try:
        title_screen()
        entries_file, adventure_name, inv_data = setup_game()
        play_game(entries_file, adventure_name, inv_data)

    except KeyboardInterrupt:
        print("\n\n\n      The darkness takes you back.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
