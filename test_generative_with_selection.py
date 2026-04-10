#!/usr/bin/env python3
"""
Test generative game with character selection
"""
import sys
import json
sys.path.insert(0, '.')

from core.game_generative import GenerativeGameEngine, InvestigatorState
from games.play_generative import load_prebuilt_investigators, json_to_investigator


def select_investigator_cli():
    """Simple CLI to select investigator"""
    invs = load_prebuilt_investigators()

    print("\n" + "=" * 80)
    print("SELECT YOUR INVESTIGATOR")
    print("=" * 80 + "\n")

    print("OPTIONS:\n")
    print("  0) Create a new investigator")

    for i, inv in enumerate(invs, 1):
        chars = inv['characteristics']
        print(f"  {i}) {inv['name']:25} - {inv['occupation']}")
        print(f"     HP: {chars['HP']:2d}, SAN: {chars['SAN']:2d}, POW: {chars['POW']:2d}")

    while True:
        choice = input("\nEnter choice (0-4): ").strip()
        if choice == "0":
            # Create new
            return InvestigatorState(
                name="Custom Investigator",
                occupation="Unknown",
                characteristics={
                    'STR': 65, 'CON': 65, 'DEX': 65, 'INT': 80,
                    'APP': 60, 'POW': 70, 'EDU': 75, 'SIZ': 60,
                    'HP': 13, 'SAN': 70, 'Luck': 50
                },
                skills={
                    'investigate': 60, 'psychology': 45, 'occult': 35,
                    'dodge': 50, 'fight': 40, 'climb': 45, 'library': 50,
                    'spot_hidden': 50, 'persuade': 40
                },
                inventory=['Flashlight', 'Notebook', 'Matches'],
                visited_locations=[],
                sanity_breaks=[]
            )
        elif choice in ['1', '2', '3', '4']:
            idx = int(choice) - 1
            if idx < len(invs):
                return json_to_investigator(invs[idx])
        print("Invalid choice. Try again.")


def test_game_flow():
    """Test a complete game flow"""

    # Select investigator
    investigator = select_investigator_cli()

    # Initialize game
    engine = GenerativeGameEngine()
    engine.create_game(investigator)

    print("\n" + "=" * 80)
    print("ALONE AGAINST THE DARK - GENERATIVE TEST")
    print("=" * 80)
    print(f"\nInvestigator: {investigator.name} ({investigator.occupation})")
    print(f"HP: {investigator.characteristics['HP']}, SAN: {investigator.characteristics['SAN']}, POW: {investigator.characteristics['POW']}")
    print(f"Skills available: {list(investigator.skills.keys())[:5]}...")
    print("\n" + "=" * 80)
    print("\nSTORY INTRO:")
    print(engine.state.narrative[0])

    # Simulate player actions
    test_actions = [
        "I arrive at the lighthouse and examine the exterior carefully for any clues.",
        "I notice something strange about the light. I climb up to get a better look.",
        "I see the logbook inside. I flip through it to understand what happened.",
    ]

    for action_num, action in enumerate(test_actions, 1):
        print("\n" + "=" * 80)
        print(f"[TURN {engine.state.turn}] PLAYER ACTION")
        print("=" * 80)
        print(f"\nYou: {action}\n")

        result = engine.process_player_action(action)

        print(f"DM:\n{result['narrative']}\n")

        # Handle rolls
        if result['rolls_requested']:
            print(f"[SKILL CHECKS]")
            for skill, difficulty in result['rolls_requested']:
                roll = engine.execute_skill_check(skill, difficulty)
                print(f"  {roll['message']}")

        # Handle sanity
        if result['sanity_checks']:
            print(f"\n[SANITY EFFECTS]")
            for damage_str in result['sanity_checks']:
                damage = int(damage_str)
                san_result = engine.apply_sanity_check(damage)
                print(f"  {san_result['message']}")
                if investigator.characteristics['SAN'] <= 0:
                    print("\n⚠️  GAME OVER - MADNESS ENDING")
                    return

        print(f"\nCurrent Status: HP {investigator.characteristics['HP']}, SAN {investigator.characteristics['SAN']}")

        if action_num >= 3:  # 3 turns for demo
            break

    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print(f"Final Status: HP {investigator.characteristics['HP']}, SAN {investigator.characteristics['SAN']}")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    test_game_flow()
