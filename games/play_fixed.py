#!/usr/bin/env python3
"""
ALONE AGAINST THE DARK - FIXED VERSION
Intelligent navigation that avoids broken entries
"""

import os
import sys
import json
import re
from core.game_enhanced import EnhancedGameEngine
from core.game_universal import Investigator

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

class SmartNavigator:
    """Navega inteligentemente evitando entradas rotas"""

    def __init__(self, engine):
        self.engine = engine
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

    return entries_file, adventure_name, inv_data

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

def play_game(entries_file, adventure_name, inv_data):
    """Main game loop"""

    engine = EnhancedGameEngine(entries_file)
    navigator = SmartNavigator(engine)

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
            if not navigator.navigate_to(int(cmd)):
                input("Press ENTER...")

        elif cmd:
            print(f"\n⚠️  Unknown: {cmd}")
            input("Press ENTER...")

def main():
    try:
        entries_file, adventure_name, inv_data = setup_game()
        play_game(entries_file, adventure_name, inv_data)
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted.\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
