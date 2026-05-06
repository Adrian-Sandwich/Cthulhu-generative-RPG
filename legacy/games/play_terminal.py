#!/usr/bin/env python3
"""
Cthulhu Game v1 - Terminal Edition

Entry point for the Call of Cthulhu generative adventure game.
This is the main way to play the game in your terminal.
"""

import sys
sys.path.insert(0, '..')

from cthulhu_engine.engine import CthulhuEngine
from cthulhu_engine.ui.terminal import get_colors, show_keeper_thinking, HistoryViewer


def main():
    """Main game loop"""
    print("\n" + "="*60)
    print("CALL OF CTHULHU: GENERATIVE EDITION v1")
    print("="*60 + "\n")

    # Initialize engine
    engine = CthulhuEngine(
        adventure_name="point_black",
        investigator_name="Test Investigator",
        model="mistral",
        use_memory=True,
        use_neo4j=False
    )

    # Create game
    investigator_stats = {
        "name": "Test Investigator",
        "occupation": "Professor",
        "characteristics": {
            "STR": 60, "CON": 60, "DEX": 60, "INT": 70, "APP": 50,
            "POW": 60, "SIZ": 70, "EDU": 80,
            "HP": 14, "SAN": 70, "Luck": 50
        },
        "skills": {
            "investigate": 50,
            "occult": 40,
            "library": 50,
            "spot_hidden": 45,
        }
    }

    state = engine.create_game(investigator_stats)
    print(f"\n✓ Game created: {state.investigator.name}")
    print(f"✓ Location: {state.location}")
    print(f"✓ Engine ready: {engine.adventure_name}\n")

    # Show welcome
    colors = get_colors()
    print(colors.cyan("═" * 60, bold=True))
    print(colors.green("Welcome to the generative adventure engine"))
    print(colors.cyan("═" * 60, bold=True))

    # Simple test: show history viewer
    viewer = HistoryViewer()
    print("\n[v1 Status: Engine structure ready]")
    print("[Full game loop implementation in next phase]\n")


if __name__ == "__main__":
    main()
