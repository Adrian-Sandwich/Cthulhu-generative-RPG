#!/usr/bin/env python3
"""
Interactive Retro UI Demo
Test and design the UI independently from the game loop
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.color_system import get_colors, orange, green, cyan, red, yellow, gray
from ui.retro_display import RetroDisplay


def clear():
    """Clear terminal"""
    os.system('clear' if os.name == 'posix' else 'cls')


def demo_title_screen():
    """Demo: Title screen"""
    clear()
    display = RetroDisplay(width=80)

    # Title
    print()
    print(orange("╔" + "═" * 78 + "╗", bold=True))
    print(orange("║" + " " * 78 + "║", bold=True))
    print(orange("║" + "ALONE AGAINST THE DARK".center(78) + "║", bold=True))
    print(orange("║" + "Generative Edition".center(78) + "║", bold=True))
    print(orange("║" + " " * 78 + "║", bold=True))
    print(orange("╚" + "═" * 78 + "╝", bold=True))

    print()
    print(cyan("In the darkness, something ancient stirs...".center(80)))
    print()

    # Menu
    print(green("▸ NEW GAME", bold=True))
    print(green("▸ CONTINUE", bold=True))
    print(green("▸ SETTINGS", bold=True))
    print(green("▸ QUIT", bold=True))
    print()
    print(gray("Press ENTER to start, or select with arrow keys".center(80)))


def demo_game_state():
    """Demo: Game state display"""
    clear()
    display = RetroDisplay(width=80)

    # Header
    display.print_header("CHARACTER: Detective Morgan", color="orange")

    # Stats line
    print(green("HP: 13/14  •  SAN: 75/99  •  Turn: 3", bold=True))
    print()

    # Stat bars
    hp_bar = display.print_stat_bar("HP", 13, 14, width=20, color="red")
    san_bar = display.print_stat_bar("SAN", 75, 99, width=20, color="yellow")

    print(hp_bar)
    print(san_bar)
    print()

    # Quick info
    display.print_divider(color="cyan")
    display.print_columns([
        orange("📍 Lighthouse Interior"),
        green("🎒 5 items"),
        cyan("👥 1 companion")
    ], color="white")
    display.print_divider(color="cyan")


def demo_narrative():
    """Demo: Narrative display"""
    clear()
    display = RetroDisplay(width=80)

    display.print_header("THE KEEPER", color="cyan")

    narrative = """The lighthouse beam cuts through the darkness above, casting long shadows
across the keeper's quarters. The air is thick with the smell of old parchment
and something else—something organic and deeply wrong.

You notice the logbook is still open on the desk, filled with increasingly
erratic handwriting. The final entry reads only: "THEY ARE COMING."

What do you do?"""

    # Wrap and print
    lines = display._wrap_text(narrative, 76)
    for line in lines:
        print(f"  {line}")

    print()


def demo_skill_check():
    """Demo: Skill check"""
    clear()
    display = RetroDisplay(width=80)

    display.print_header("SKILL CHECK", color="green")

    print(f"  {green('Skill: INVESTIGATE', bold=True)}")
    print(f"  {cyan('Difficulty: NORMAL (need ≤ 60)')}")
    print(f"  {yellow('Your Skill: 55')}")
    print()
    print(cyan("  Rolling..."))
    print()
    print("  " + "▮" * 20)
    print()
    print(green("  ✓ SUCCESS! (Rolled 43)", bold=True))
    print()
    print("  You discover a hidden compartment behind the portrait!")
    print()


def demo_sanity_check():
    """Demo: Sanity check"""
    clear()
    display = RetroDisplay(width=80)

    display.print_header("HORROR WITNESSED", color="red")

    print()
    print("  The water at the lighthouse base begins to glow with an")
    print("  unnatural phosphorescence. Something VAST moves beneath the")
    print("  surface—something that should not exist.")
    print()

    san_bar = display.print_stat_bar("SAN", 70, 99, width=25, color="yellow")
    print("  Before: " + display.print_stat_bar("SAN", 75, 99, width=15, color="yellow"))
    print("  After:  " + san_bar)
    print()
    print(red("  💔 You lose 5 sanity points to this nightmare vision", bold=True))
    print()


def demo_inventory():
    """Demo: Inventory"""
    clear()
    display = RetroDisplay(width=80)

    display.print_header("INVENTORY", color="green")

    items = [
        {"name": "Flashlight", "description": "Battery: Good (3 hours remaining)"},
        {"name": "Notebook", "description": "Your investigation notes (8 pages filled)"},
        {"name": "Revolver", "description": "6 bullets remaining"},
        {"name": "Holy Water", "description": "Vial of sacred water"},
        {"name": "Ancient Tome", "description": "Reading this causes SAN damage"},
    ]

    for item in items:
        print(green(f"  ▸ {item['name']}", bold=True))
        print(f"    {gray(item['description'])}")

    print()
    print(cyan("  Commands: u <item>  |  d <item>  |  read <item>"))
    print()


def demo_dialogue():
    """Demo: NPC Dialogue"""
    clear()
    display = RetroDisplay(width=80)

    print(orange("═" * 80, bold=True))
    print(orange("CHIEF MARSH (Police Chief) [FRIENDLY +25]", bold=True))
    print(orange("═" * 80, bold=True))
    print()

    dialogue = """Look, I've been working this lighthouse for twenty years. Never
seen anything like what we found. The keeper's logbook... those final entries
don't make any sense. "They call from below"? What could possibly be calling
from the ocean?

I've asked the Coast Guard to increase patrols, but between you and me,
I don't think they can help with something like this."""

    lines = display._wrap_text(dialogue, 76)
    for line in lines:
        print(f"  {line}")

    print()
    print(orange("◇ Reputation increased (+5) ◇", bold=True))
    print()


def demo_ending():
    """Demo: Game Ending"""
    clear()
    display = RetroDisplay(width=80)

    print()
    print(orange("◆ GAME OVER ◆".center(80), bold=True))
    print()
    print(orange("🔮 TRIUMPH THROUGH SACRIFICE 🔮".center(80), bold=True))
    print()
    print(orange("═" * 80))
    print()

    ending = """You made it. Against impossible odds, you uncovered the truth
and stopped something genuinely catastrophic. Your companions survived. Your
sanity, though tested, remains largely intact.

More importantly, you've proven that human determination, intelligence, and
courage can prevail even against cosmic horrors. It's a qualified victory—you
know there are larger forces in the universe indifferent to human welfare—but
it's genuine."""

    lines = display._wrap_text(ending, 76)
    for line in lines:
        print(f"  {line}")

    print()
    print(orange("═" * 80))
    print()
    print(cyan("FINAL STATISTICS:", bold=True))
    print(f"  HP: 12/14  •  SAN: 75/99")
    print(f"  Turns: 7  •  Ending: Triumph Through Sacrifice")
    print(f"  Companions Lost: 0  •  Secrets Discovered: 8")
    print()


def demo_combat():
    """Demo: Combat start"""
    clear()
    display = RetroDisplay(width=80)

    display.print_header("⚔️ COMBAT INITIATED ⚔️", color="red")

    print(orange("Enemy: Deep One Hybrid", bold=True))
    print()

    desc = """A grotesque creature emerges from the water. Its form is a nightmarish
amalgamation of human and aquatic features—scaled skin glistening, webbed
claws extended, eyes that bulge with an alien intelligence."""

    lines = display._wrap_text(desc, 76)
    for line in lines:
        print(f"  {line}")

    print()
    print(red("Prepare to fight for your life!", bold=True))
    print()


def main():
    """Interactive UI demo"""
    demos = {
        "1": ("Title Screen", demo_title_screen),
        "2": ("Game State", demo_game_state),
        "3": ("Narrative Display", demo_narrative),
        "4": ("Skill Check", demo_skill_check),
        "5": ("Sanity Check", demo_sanity_check),
        "6": ("Inventory", demo_inventory),
        "7": ("NPC Dialogue", demo_dialogue),
        "8": ("Combat Start", demo_combat),
        "9": ("Game Ending", demo_ending),
    }

    while True:
        clear()
        print(orange("╔" + "═" * 78 + "╗", bold=True))
        print(orange("║  RETRO UI DEMO - SELECT A SCREEN".ljust(79) + "║", bold=True))
        print(orange("╚" + "═" * 78 + "╝", bold=True))
        print()

        for key, (name, _) in demos.items():
            print(f"  {green(key, bold=True)}) {name}")

        print(f"  {red('q', bold=True)}) Quit")
        print()

        choice = input(green("Choose: ", bold=True)).strip()

        if choice == 'q':
            break
        elif choice in demos:
            _, demo_func = demos[choice]
            demo_func()
            input(green("\nPress ENTER to continue...", bold=True))
        else:
            print(red("Invalid choice", bold=True))
            input("Press ENTER to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(cyan("\nExiting UI demo..."))
