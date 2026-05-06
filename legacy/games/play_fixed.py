#!/usr/bin/env python3
"""
ALONE AGAINST THE DARK - FIXED VERSION
Intelligent navigation that avoids broken entries + AI fallback for dead-ends
"""

import os
import sys
import json
import re
from typing import Optional, Tuple
from core.game_enhanced import EnhancedGameEngine
from core.game_universal import Investigator
from core.game_generative import GenerativeGameEngine, InvestigatorState

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

class SmartNavigator:
    """Navega inteligentemente evitando entradas rotas"""

    def __init__(self, engine, model: str = "mistral"):
        self.engine = engine
        self.model = model
        self.broken_entries = set()
        self.find_broken_entries()

    def find_broken_entries(self):
        """Identifica entradas vacías y rotas"""
        for entry_num in range(1, self.engine.base_engine.total_entries + 1):
            entry = self.engine.base_engine.get_entry(entry_num)
            if entry and len(entry.get('text', '').strip()) == 0:
                self.broken_entries.add(entry_num)

    def find_valid_destination(self, preferred_entries):
        """Encuentra un destino válido (no roto)"""
        if isinstance(preferred_entries, int):
            preferred_entries = [preferred_entries]

        for entry_num in preferred_entries:
            if entry_num not in self.broken_entries:
                if self.engine.base_engine.get_entry(entry_num):
                    return entry_num

        return None

    def navigate_to(self, entry_num):
        """Navega con inteligencia: salta entradas rotas"""
        # Si es roto, buscar alternativa
        if entry_num in self.broken_entries:
            entry = self.engine.base_engine.get_entry(entry_num)
            if entry:
                trace = entry.get('trace_numbers', [])
                if trace:
                    valid = self.find_valid_destination(trace)
                    if valid:
                        print(f"  ⚠️  Entry {entry_num} is broken. Redirecting to {valid}...\n")
                        entry_num = valid
                    else:
                        print(f"  ❌ Entry {entry_num} and all alternatives are broken!")
                        return False

        self.engine.move_to_entry(entry_num)
        return True

# ═══════════════════════════════════════════════════════════════════════════

def setup_game():
    """Choose adventure and investigator"""
    clear()
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║           ALONE AGAINST THE DARK - FIXED NAVIGATION                       ║
║                    Defying the Triumph of the Ice                         ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)

    print("CHOOSE ADVENTURE:\n")
    print("  1) TIDE (243 entries)")
    print("  2) DARK (594 entries)\n")

    while True:
        choice = input("  Enter 1 or 2: ").strip()
        if choice in ['1', '2']:
            break

    if choice == '1':
        entries_file = 'entries_with_rolls.json'
        adventure_name = 'TIDE'
    else:
        entries_file = 'entries_dark_594_final.json'
        adventure_name = 'DARK'

    clear()
    print(f"Alone Against the {adventure_name}\n")
    print("SELECT INVESTIGATOR:\n")

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

def format_entry(engine, entry_num):
    """Format entry for display"""
    entry = engine.base_engine.get_entry(entry_num)
    if not entry:
        return None

    inv = engine.game.investigator
    chars = inv.characteristics
    san = chars['SAN']
    san_bar = "█" * int(san / 4) + "░" * (25 - int(san / 4))
    status = f"{inv.name} | HP:{chars['HP']:2} | SAN:[{san_bar}]{san:3}"

    text = entry.get('text', '')
    output = f"{status}\n"
    output += "─" * 80 + "\n"
    output += f"[{entry_num:03d}] "
    output += text[:700]
    if len(text) > 700:
        output += "\n[...more...]"
    output += "\n"

    return output

def show_destinations(engine, entry_num):
    """Show available destinations"""
    entry = engine.base_engine.get_entry(entry_num)
    if not entry:
        return

    text = entry.get('text', '')
    destinations = re.findall(r'go to (\d+)', text, re.IGNORECASE)

    if destinations:
        print("\nDESTINATIONS in text:")
        for dest in destinations[:5]:
            print(f"  → {dest}")

    trace = entry.get('trace_numbers', [])
    if trace and not destinations:
        print("\nAvailable choices (from trace):")
        for dest in trace[:5]:
            print(f"  → {dest}")

# ═══════════════════════════════════════════════════════════════════════════

def launch_generative_continuation(engine: EnhancedGameEngine, last_entry_num: int, model: str = "mistral"):
    """
    Launch AI DM continuation when fixed adventure reaches a dead-end.

    Args:
        engine: EnhancedGameEngine with fixed adventure
        last_entry_num: Current entry number (dead-end)
        model: LLM model to use
    """
    clear()

    # Get context from last fixed adventure node
    last_entry = engine.base_engine.get_entry(last_entry_num)
    last_text = last_entry.get('text', '') if last_entry else ''
    last_text = last_text[:600]  # Limit to 600 chars for context

    # Reconstruct InvestigatorState from fixed game state
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

    # Create generative engine with fixed adventure context
    gen_engine = GenerativeGameEngine(model=model)
    gen_engine.create_game(gen_inv)

    # Inject fixed adventure context as initial narrative
    gen_engine.state.narrative = [
        f"[CONTINUATION FROM FIXED ADVENTURE - Entry {last_entry_num}]",
        f"[The adventure book continues generatively from this point]",
        f"DM: {last_text}"
    ]
    gen_engine.state.location = f"Adventure Entry {last_entry_num}"
    gen_engine.state.phase = "exploring"

    # Show transition message
    print("=" * 80)
    print("THE STORY CONTINUES...")
    print("=" * 80)
    print("\nThe adventure book ends here. But the story does not.")
    print("An AI Dungeon Master will continue your journey.\n")
    print(f"Last known location: Entry {last_entry_num}")
    print(f"Model: {model}\n")
    input("Press ENTER to begin the generative adventure...")

    # Import and run generative game loop
    from games.play_generative import _run_game_loop
    _run_game_loop(gen_engine, model)

# ═══════════════════════════════════════════════════════════════════════════

def play_game(entries_file, adventure_name, inv_data, selected_model: str = "mistral"):
    """Main game loop"""

    engine = EnhancedGameEngine(entries_file)
    navigator = SmartNavigator(engine, model=selected_model)

    inv = Investigator(
        name=inv_data['name'],
        skills=inv_data['skills'],
        characteristics=inv_data['characteristics']
    )

    engine.create_game(inv, inv_data['starting_entry'])

    if navigator.broken_entries:
        print(f"\n⚠️  Found {len(navigator.broken_entries)} broken entries. Navigation is auto-corrected.")
        input("Press ENTER to continue...\n")

    while True:
        clear()

        entry_display = format_entry(engine, engine.game.current_entry)
        if not entry_display:
            print("ERROR: Entry not found!")
            break

        print(entry_display)
        show_destinations(engine, engine.game.current_entry)

        cmd = input("\n➜ ").strip().lower()

        if cmd == 'q':
            if input("\nSave? (y/n): ").lower() == 'y':
                engine.save_game()
            print("\n👋 Goodbye!\n")
            break

        elif cmd == 'j':
            clear()
            print(f"JOURNAL\n{'-'*80}\n")
            for e in engine.journal.entries[-10:]:
                ts = e['timestamp'].split('T')[1][:5]
                print(f"  [{ts}] {e['action']}")
            input("\nPress ENTER...")

        elif cmd == 's':
            clear()
            c = inv_data['characteristics']
            print(f"STATUS: {inv.name}\n{'-'*80}\n")
            print(f"STR:{c['STR']:2} CON:{c['CON']:2} SIZ:{c['SIZ']:2} DEX:{c['DEX']:2}")
            print(f"INT:{c['INT']:2} APP:{c['APP']:2} POW:{c['POW']:2} EDU:{c['EDU']:2}")
            print(f"HP:{c['HP']:2} SAN:{c['SAN']:2} Luck:{c['Luck']:2} MP:{c['Magic_Points']:2}")
            print(f"\nVisited: {len(engine.game.visited_entries)}")
            input("\nPress ENTER...")

        elif cmd == 'h':
            clear()
            print("""
COMMANDS:
  [number]  Go to entry
  [j]       Journal
  [s]       Status
  [h]       Help
  [q]       Quit
            """)
            input("Press ENTER...")

        elif cmd.isdigit():
            entry_num = int(cmd)

            # Check if this is a dead-end (no valid destinations)
            entry = engine.base_engine.get_entry(entry_num)
            if entry:
                destinations = re.findall(r'go to (\d+)', entry.get('text', ''), re.IGNORECASE)
                trace = entry.get('trace_numbers', [])
                is_deadend = not destinations and not trace
            else:
                is_deadend = False

            # Try to navigate
            if not navigator.navigate_to(entry_num):
                # Dead-end detected
                if input("\n  Try AI continuation? (y/n): ").lower() == 'y':
                    launch_generative_continuation(engine, entry_num, navigator.model)
                    return  # Exit fixed adventure loop
                input("Press ENTER...")
            elif is_deadend and entry_num == engine.game.current_entry:
                # Successfully navigated to a dead-end (last valid entry)
                if input("\n  Reach story end. Continue with AI? (y/n): ").lower() == 'y':
                    launch_generative_continuation(engine, entry_num, navigator.model)
                    return  # Exit fixed adventure loop

        elif cmd:
            print(f"\n⚠️  Unknown: {cmd}")
            input("Press ENTER...")

def main():
    try:
        entries_file, adventure_name, inv_data, selected_model = setup_game()
        play_game(entries_file, adventure_name, inv_data, selected_model)
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted.\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
