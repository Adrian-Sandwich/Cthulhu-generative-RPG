#!/usr/bin/env python3
"""
ALONE AGAINST THE DARK - Streamlined Interactive Game
Minimalist UI, maximum narrative flow
"""

import os
import sys
import json
from core.game_enhanced import EnhancedGameEngine
from core.game_universal import Investigator
from core.game_generative import GenerativeGameEngine, InvestigatorState

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

# ═══════════════════════════════════════════════════════════════════════════
# SETUP PHASE
# ═══════════════════════════════════════════════════════════════════════════

def setup_game():
    """Setup game: choose adventure and investigator"""

    # Title
    clear()
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║          ALONE AGAINST THE DARK - Call of Cthulhu                        ║
║                    Defying the Triumph of the Ice                         ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    # Choose adventure
    print("CHOOSE YOUR ADVENTURE:\n")
    print("  1) Alone Against the TIDE (243 entries - coastal investigation)")
    print("  2) Alone Against the DARK (594 entries - Antarctic expedition)\n")

    while True:
        choice = input("  Enter 1 or 2: ").strip()
        if choice in ['1', '2']:
            break
        print("  Invalid choice. Try again.")

    if choice == '1':
        entries_file = 'entries_with_rolls.json'
        adventure_name = 'TIDE'
    else:
        entries_file = 'entries_dark_594_final.json'
        adventure_name = 'DARK'

    # Choose investigator
    clear()
    print(f"Alone Against the {adventure_name}\n")
    print("SELECT YOUR INVESTIGATOR:\n")

    with open('investigators.json', 'r') as f:
        invs = json.load(f)

    for i, inv in enumerate(invs, 1):
        print(f"  {i}) {inv['name']:20} - {inv['occupation']}")

    print()
    while True:
        choice = input("  Enter 1-4: ").strip()
        if choice in ['1', '2', '3', '4']:
            inv_data = invs[int(choice) - 1]
            break
        print("  Invalid choice. Try again.")

    # Select AI model for potential fallback continuation
    clear()
    print("SELECT LLM MODEL (for AI continuation if story reaches dead-end):\n")
    print("  1) Mistral 7B (Best Quality) - recommended")
    print("  2) Neural Chat 7B (Balanced)")
    print("  3) Orca Mini 3B (Speed)")
    print("  4) Qwen3 8B (Reasoning)\n")

    while True:
        choice = input("  Enter 1-4 (default 1): ").strip() or "1"
        if choice in ['1', '2', '3', '4']:
            break

    model_map = {"1": "mistral", "2": "neural-chat", "3": "orca-mini", "4": "qwen3:8b"}
    selected_model = model_map.get(choice, "mistral")

    return entries_file, adventure_name, inv_data, selected_model

# ═══════════════════════════════════════════════════════════════════════════
# GAME PHASE
# ═══════════════════════════════════════════════════════════════════════════

def format_entry(engine, entry_num):
    """Format entry for display with minimal UI"""
    entry = engine.base_engine.get_entry(entry_num)
    if not entry:
        return None

    # Status bar (one line)
    inv = engine.game.investigator
    chars = inv.characteristics
    san = chars['SAN']
    san_bar = "█" * int(san / 4) + "░" * (25 - int(san / 4))
    status = f"{inv.name} | HP:{chars['HP']:2} | SAN:[{san_bar}]{san:3} | Luck:{chars['Luck']:2}"

    # Entry content
    text = entry.get('text', '')

    # Format output
    output = f"{status}\n"
    output += "─" * 80 + "\n"
    output += f"[{entry_num:03d}] "
    output += text[:750]
    if len(text) > 750:
        output += "\n... [more text] ..."
    output += "\n"

    return output

def show_help():
    """Show command help"""
    return """
COMMANDS:
  [NUMBER]    Go to entry (e.g., type "42")
  [j]ournal   View recent events
  [s]tatus    View full status
  [h]elp      Show this help
  [q]uit      Save and quit

Just type the command and press ENTER.
"""

def format_status(engine, inv_data):
    """Show full status"""
    output = "\n" + "─" * 80 + "\n"
    output += f"STATUS: {engine.game.investigator.name}\n"
    output += "─" * 80 + "\n\n"

    chars = inv_data['characteristics']
    inv = engine.game.investigator

    # Stats
    output += f"CHARACTERISTICS:\n"
    output += f"  STR:{chars['STR']:2} CON:{chars['CON']:2} SIZ:{chars['SIZ']:2} DEX:{chars['DEX']:2}\n"
    output += f"  INT:{chars['INT']:2} APP:{chars['APP']:2} POW:{chars['POW']:2} EDU:{chars['EDU']:2}\n"
    output += f"  HP:{chars['HP']:2} SAN:{chars['SAN']:2} Luck:{chars['Luck']:2} MP:{chars['Magic_Points']:2}\n\n"

    # Game progress
    output += f"PROGRESS:\n"
    output += f"  Entry: {engine.game.current_entry}\n"
    output += f"  Visited: {len(engine.game.visited_entries)} locations\n"
    output += f"  Rolls: {len(engine.game.roll_history)}\n\n"

    # Money
    output += f"RESOURCES:\n"
    output += f"  Cash: ${inv_data['available_cash']:,}\n"

    return output

def format_journal(engine):
    """Show recent journal entries"""
    output = "\n" + "─" * 80 + "\n"
    output += f"JOURNAL\n"
    output += "─" * 80 + "\n\n"

    if not engine.journal.entries:
        output += "  [No events recorded yet]\n"
    else:
        for entry in engine.journal.entries[-10:]:
            ts = entry['timestamp'].split('T')[1][:5]
            output += f"  [{ts}] Entry {entry['entry']}: {entry['action']}\n"

    return output

def launch_generative_continuation(engine: EnhancedGameEngine, last_entry_num: int, model: str = "mistral"):
    """Launch AI DM continuation when fixed adventure reaches a dead-end"""
    clear()

    last_entry = engine.base_engine.get_entry(last_entry_num)
    last_text = last_entry.get('text', '') if last_entry else ''
    last_text = last_text[:600]

    fixed_inv = engine.game.investigator
    gen_inv = InvestigatorState(
        name=fixed_inv.name,
        occupation=fixed_inv.occupation if hasattr(fixed_inv, 'occupation') else 'Investigator',
        characteristics=fixed_inv.characteristics,
        skills=fixed_inv.skills,
        inventory=[],
        visited_locations=[str(n) for n in engine.game.visited_entries[-10:]],
        sanity_breaks=[]
    )

    gen_engine = GenerativeGameEngine(model=model)
    gen_engine.create_game(gen_inv)
    gen_engine.state.narrative = [
        f"[CONTINUATION FROM FIXED ADVENTURE - Entry {last_entry_num}]",
        f"[The adventure book continues generatively from this point]",
        f"DM: {last_text}"
    ]
    gen_engine.state.location = f"Adventure Entry {last_entry_num}"

    print("=" * 80)
    print("THE STORY CONTINUES...")
    print("=" * 80)
    print("\nThe adventure book ends here. But the story does not.")
    input("Press ENTER to begin the generative adventure...")

    from games.play_generative import _run_game_loop
    _run_game_loop(gen_engine, model)

def play_game(entries_file, adventure_name, inv_data, selected_model: str = "mistral"):
    """Main game loop"""

    # Initialize engine
    engine = EnhancedGameEngine(entries_file)

    # Create investigator
    inv = Investigator(
        name=inv_data['name'],
        skills=inv_data['skills'],
        characteristics=inv_data['characteristics']
    )

    # Start game
    engine.create_game(inv, inv_data['starting_entry'])

    clear()
    print(f"\n✓ You are {inv.name}")
    print(f"✓ Beginning Alone Against the {adventure_name}")
    print(f"✓ Entry {engine.game.current_entry}\n")
    input("Press ENTER to begin...\n")

    # Main loop
    while True:
        clear()

        # Show current entry
        entry_display = format_entry(engine, engine.game.current_entry)
        if not entry_display:
            print("ERROR: Entry not found!")
            break

        print(entry_display)

        # Get command
        cmd = input("➜ ").strip().lower()

        # Parse command
        if cmd == 'q':
            # Quit
            if input("\nSave game? (y/n): ").lower() == 'y':
                save_file = engine.save_game()
                print(f"✓ Saved: {save_file}")
            print("\n👋 Thank you for playing!\n")
            break

        elif cmd == 'j':
            # Journal
            clear()
            print(format_journal(engine))
            input("Press ENTER to continue...")

        elif cmd == 's':
            # Status
            clear()
            print(format_status(engine, inv_data))
            input("Press ENTER to continue...")

        elif cmd == 'h':
            # Help
            clear()
            print(show_help())
            input("Press ENTER to continue...")

        elif cmd.isdigit():
            # Go to entry
            try:
                entry_num = int(cmd)
                engine.move_to_entry(entry_num)
            except ValueError:
                print(f"\n⚠ Invalid entry number: {cmd}")
                input("Press ENTER to continue...")

        else:
            if cmd:  # Only show error if user typed something
                print(f"\n⚠ Unknown command: '{cmd}'")
                print("Type 'h' for help")
                input("Press ENTER to continue...")

def main():
    """Main entry point"""
    try:
        # Setup
        entries_file, adventure_name, inv_data, selected_model = setup_game()

        # Play
        play_game(entries_file, adventure_name, inv_data, selected_model)

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
