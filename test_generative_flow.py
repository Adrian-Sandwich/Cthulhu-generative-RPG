#!/usr/bin/env python3
"""
Quick test of generative game flow (non-interactive)
"""
import sys
sys.path.insert(0, '.')

from core.game_generative import GenerativeGameEngine, InvestigatorState

def test_game_flow():
    """Test a complete game flow"""

    # Create investigator
    inv = InvestigatorState(
        name="Detective Morgan",
        occupation="Private Investigator",
        characteristics={
            'STR': 65, 'CON': 65, 'DEX': 65, 'INT': 80,
            'APP': 60, 'POW': 70, 'EDU': 85, 'SIZ': 60,
            'HP': 13, 'SAN': 70, 'Luck': 50
        },
        skills={
            'investigate': 60, 'psychology': 45, 'occult': 35,
            'dodge': 50, 'fight': 40, 'climb': 45, 'library': 50
        },
        inventory=['Flashlight', 'Revolver', 'Notebook'],
        visited_locations=[],
        sanity_breaks=[]
    )

    # Initialize game
    engine = GenerativeGameEngine()
    engine.create_game(inv)

    print("=" * 80)
    print("ALONE AGAINST THE DARK - GENERATIVE TEST")
    print("=" * 80)
    print(f"\nInvestigator: {inv.name} ({inv.occupation})")
    print(f"SAN: {inv.characteristics['SAN']}, HP: {inv.characteristics['HP']}")
    print("\n" + "=" * 80)
    print("\nSTARY INTRO:")
    print(engine.state.narrative[0])

    # Simulate player actions
    test_actions = [
        "I climb down to the rocks to examine the fissure more closely.",
        "I attempt to peer into the water to see what's beneath the surface.",
        "I notice something moving in the fissure. I try to flee back up the rocks.",
    ]

    for i, action in enumerate(test_actions, 1):
        print("\n" + "=" * 80)
        print(f"\n[TURN {engine.state.turn}] PLAYER ACTION")
        print(f"You: {action}\n")

        result = engine.process_player_action(action)

        print(f"DM:\n{result['narrative']}\n")

        # Handle rolls
        if result['rolls_requested']:
            print(f"[ROLLS REQUESTED]")
            for skill, difficulty in result['rolls_requested']:
                roll = engine.execute_skill_check(skill, difficulty)
                print(f"  • {roll['message']}")

        # Handle sanity
        if result['sanity_checks']:
            print(f"\n[SANITY CHECKS]")
            for damage_str in result['sanity_checks']:
                damage = int(damage_str)
                san_result = engine.apply_sanity_check(damage)
                print(f"  • {san_result['message']}")
                if inv.characteristics['SAN'] <= 0:
                    print("\n⚠️  GAME OVER - MADNESS ENDING")
                    return

        print(f"\nCurrent SAN: {inv.characteristics['SAN']}/70")

        if i >= 2:  # Just 2 turns for demo
            break

    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print(f"Final SAN: {inv.characteristics['SAN']}")
    print("=" * 80)


if __name__ == '__main__':
    test_game_flow()
