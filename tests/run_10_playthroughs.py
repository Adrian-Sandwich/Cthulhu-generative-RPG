#!/usr/bin/env python3
"""
Auto-play 10 full games with different investigators and strategies
Track endings and issues
"""
import sys
sys.path.insert(0, '.')

from core.game_generative import GenerativeGameEngine
from games.play_generative import load_prebuilt_investigators, json_to_investigator
import json

# Load investigators
investigators_data = load_prebuilt_investigators()

# Define different strategies for each game
STRATEGIES = [
    {
        "name": "Cautious Investigator",
        "actions": [
            "I approach the lighthouse slowly and carefully, looking for any immediate signs of danger.",
            "I examine the exterior walls for clues about what happened here.",
            "I notice something strange and decide to investigate further by examining the rocks below.",
        ]
    },
    {
        "name": "Direct Approach",
        "actions": [
            "I immediately enter the lighthouse to find out what happened.",
            "I search the interior for the keeper's body and any clues.",
            "I climb to the top of the lighthouse to see what's there.",
        ]
    },
    {
        "name": "Scholarly Investigator",
        "actions": [
            "I examine the symbols on the exterior carefully using my knowledge of ancient languages.",
            "I try to understand what the symbols mean and their historical context.",
            "I search for any books or documents inside that might explain these symbols.",
        ]
    },
    {
        "name": "Physical Explorer",
        "actions": [
            "I test my strength by trying to pry open a locked door.",
            "I climb down to the fissure to examine it up close.",
            "I try to peer into the water to see what's moving down there.",
        ]
    },
    {
        "name": "Spiritual Approach",
        "actions": [
            "I pray for guidance before entering this place of darkness.",
            "I perform a blessing ritual at the entrance to protect myself.",
            "I confront whatever is here with faith and ask for divine protection.",
        ]
    },
    {
        "name": "Combat Ready",
        "actions": [
            "I check my weapons before approaching the lighthouse.",
            "I prepare for a fight if something emerges from the darkness.",
            "I attempt to shoot at the creature emerging from the fissure.",
        ]
    },
    {
        "name": "Escape Artist",
        "actions": [
            "I take a quick look around and immediately feel like I should leave.",
            "This place is too dangerous. I run back to my vehicle.",
            "I drive away from the lighthouse as fast as I can.",
        ]
    },
    {
        "name": "Deep Investigator",
        "actions": [
            "I examine every detail of the lighthouse methodically.",
            "I search the logbook thoroughly to understand the timeline.",
            "I descend to the fissure to uncover its secrets despite the danger.",
        ]
    },
    {
        "name": "Occult Focus",
        "actions": [
            "I use my knowledge of the occult to identify the symbols and their meaning.",
            "I sense something ancient and try to communicate with it.",
            "I attempt a ritual to seal whatever is awakening in the fissure.",
        ]
    },
    {
        "name": "Pragmatic",
        "actions": [
            "I call for backup before investigating further.",
            "I document everything I see with my camera.",
            "I report my findings and wait for orders before proceeding.",
        ]
    }
]

def play_game(investigator_data, strategy):
    """Play one complete game"""
    investigator = json_to_investigator(investigator_data)
    engine = GenerativeGameEngine()
    engine.create_game(investigator)

    actions = strategy["actions"]
    ending = None
    final_san = investigator.characteristics['SAN']
    final_hp = investigator.characteristics['HP']
    turn_count = 0
    narrative_log = []

    for action in actions:
        turn_count += 1

        # Process action
        result = engine.process_player_action(action)
        narrative_log.append(f"Turn {turn_count}: {action[:50]}...")

        # Handle rolls
        for skill, difficulty in result['rolls_requested']:
            roll = engine.execute_skill_check(skill, difficulty)
            narrative_log.append(f"  [ROLL: {roll['message'][:60]}...]")

        # Handle sanity
        for damage_str in result['sanity_checks']:
            damage = int(damage_str)
            san_result = engine.apply_sanity_check(damage)
            narrative_log.append(f"  [SAN: {san_result['message'][:50]}...]")

        # Check for ending
        ending = engine.check_ending_condition()
        if ending:
            final_san = investigator.characteristics['SAN']
            final_hp = investigator.characteristics['HP']
            break

    # If no ending reached after actions, mark as incomplete
    if not ending:
        ending = "incomplete"

    return {
        "investigator": investigator.name,
        "occupation": investigator.occupation,
        "strategy": strategy["name"],
        "ending": ending,
        "final_san": final_san,
        "final_hp": final_hp,
        "turns": turn_count,
        "narrative": narrative_log
    }


def run_10_playthroughs():
    """Run 10 complete games"""
    print("\n" + "=" * 90)
    print("RUNNING 10 AUTOMATED PLAYTHROUGHS - ALONE AGAINST THE DARK")
    print("=" * 90)

    results = []

    for game_num in range(1, 11):
        # Rotate through investigators
        inv_idx = (game_num - 1) % len(investigators_data)
        investigator_data = investigators_data[inv_idx]

        # Rotate through strategies
        strategy_idx = (game_num - 1) % len(STRATEGIES)
        strategy = STRATEGIES[strategy_idx]

        print(f"\n{'─' * 90}")
        print(f"GAME {game_num}/10: {investigator_data['name']} - {strategy['name']}")
        print(f"{'─' * 90}")

        result = play_game(investigator_data, strategy)

        # Print result
        print(f"Ending: {result['ending'].upper()}")
        print(f"Final Stats: HP {result['final_hp']}, SAN {result['final_san']}")
        print(f"Turns Played: {result['turns']}")

        results.append(result)

    # Summary
    print("\n" + "=" * 90)
    print("SUMMARY - 10 GAMES COMPLETED")
    print("=" * 90)

    ending_counts = {}
    for result in results:
        ending = result['ending']
        ending_counts[ending] = ending_counts.get(ending, 0) + 1

    print(f"\nENDINGS DISTRIBUTION:")
    for ending, count in sorted(ending_counts.items(), key=lambda x: -x[1]):
        pct = (count / 10) * 100
        print(f"  {ending.upper():15} {count}x ({pct:5.1f}%)")

    print(f"\nGAMES BY INVESTIGATOR:")
    inv_results = {}
    for result in results:
        inv_name = result['investigator']
        if inv_name not in inv_results:
            inv_results[inv_name] = []
        inv_results[inv_name].append(result['ending'])

    for inv_name, endings in sorted(inv_results.items()):
        end_str = ", ".join(endings)
        print(f"  {inv_name:25} {end_str}")

    print(f"\nAVERAGE STATS:")
    avg_san = sum(r['final_san'] for r in results) / len(results)
    avg_hp = sum(r['final_hp'] for r in results) / len(results)
    avg_turns = sum(r['turns'] for r in results) / len(results)
    print(f"  Sanity:  {avg_san:.1f}")
    print(f"  HP:      {avg_hp:.1f}")
    print(f"  Turns:   {avg_turns:.1f}")

    print(f"\nDETAILED RESULTS:")
    for i, result in enumerate(results, 1):
        print(f"\nGame {i}: {result['investigator']} ({result['strategy']})")
        print(f"  Ending: {result['ending']}")
        print(f"  HP: {result['final_hp']}, SAN: {result['final_san']}, Turns: {result['turns']}")

    # Save results to JSON
    with open('playthrough_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Results saved to playthrough_results.json")
    print("=" * 90 + "\n")


if __name__ == '__main__':
    try:
        run_10_playthroughs()
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
