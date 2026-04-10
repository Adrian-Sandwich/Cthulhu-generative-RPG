#!/usr/bin/env python3
"""
Full playthrough test - Play complete games with each model
Simulates a complete player session with realistic actions and decisions
"""

import sys
import time
import random
sys.path.insert(0, '.')

from core.game_generative import GenerativeGameEngine, InvestigatorState

def create_test_investigator(name="Morgan", occupation="Detective"):
    """Create a test character"""
    return InvestigatorState(
        name=name,
        occupation=occupation,
        characteristics={
            'STR': 65, 'CON': 60, 'DEX': 65, 'INT': 80,
            'APP': 60, 'POW': 70, 'EDU': 75, 'SIZ': 60,
            'HP': 13, 'SAN': 70, 'Luck': 50
        },
        skills={
            'investigate': 60, 'psychology': 45, 'occult': 35,
            'dodge': 50, 'fight': 40, 'climb': 45, 'library': 50,
            'spot_hidden': 50, 'persuade': 40, 'navigate': 30,
            'firearms_revolver': 35, 'first_aid': 40
        },
        inventory=['Flashlight', 'Notebook'],
        visited_locations=[],
        sanity_breaks=[]
    )

# Action sequences for each playthrough
ACTION_SEQUENCES = {
    "mistral": [
        "I enter the lighthouse and look around carefully.",
        "I examine the logbook on the desk.",
        "I talk to Lt. Warner about what happened here.",
        "I climb the spiral staircase to the second floor.",
        "I investigate the strange symbols on the walls.",
        "I try to understand the ancient text I found.",
        "I use my revolver to prepare for what comes next.",
        "I attempt to escape the lighthouse through the east window.",
    ],
    "neural-chat": [
        "I approach the lighthouse cautiously.",
        "I search the keeper's quarters for clues.",
        "I speak with Dr. Armitage about the symbols.",
        "I navigate through the fog toward the main chamber.",
        "I examine the ancient fissure beneath the lighthouse.",
        "I use the rope to descend carefully.",
        "I fight the creature emerging from the darkness.",
        "I flee the lighthouse as quickly as possible.",
    ],
    "orca-mini": [
        "I enter the lighthouse.",
        "I look for items.",
        "I talk to the people here.",
        "I go upstairs.",
        "I find something strange.",
        "I try to escape.",
        "I fight the monster.",
        "I run away.",
    ]
}

def silent_chunk(chunk):
    """Silent callback - don't print streamed text during test"""
    pass

def format_duration(seconds):
    """Format duration nicely"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    else:
        return f"{int(seconds)}m {int(seconds%60)}s"

def run_playthrough(model_name):
    """Run a complete game session"""
    print(f"\n{'='*80}")
    print(f"FULL PLAYTHROUGH: {model_name.upper()}")
    print(f"{'='*80}\n")

    # Setup
    investigator = create_test_investigator()
    engine = GenerativeGameEngine(model=model_name)
    engine.create_game(investigator)

    print(f"Character: {investigator.name} ({investigator.occupation})")
    print(f"Starting Stats: HP={investigator.characteristics['HP']}, SAN={investigator.characteristics['SAN']}\n")

    # Get actions for this model
    actions = ACTION_SEQUENCES.get(model_name, ACTION_SEQUENCES["mistral"])

    # Track stats
    turns = 0
    rolls_total = 0
    rolls_success = 0
    start_time = time.time()
    turn_times = []

    # Play through actions
    for action in actions:
        if engine.check_ending_condition():
            print(f"\n⚠️  Game ended (ending reached)")
            break

        if engine.state.investigator.characteristics['HP'] <= 0:
            print(f"\n⚠️  Game ended (HP depleted)")
            break

        turns += 1
        turn_start = time.time()

        print(f"Turn {turns}: ", end="", flush=True)

        try:
            result = engine.process_player_action(action, on_chunk=silent_chunk)

            # Track rolls
            if result['rolls_requested']:
                for skill, difficulty in result['rolls_requested']:
                    rolls_total += 1
                    roll_result = engine.execute_skill_check(skill, difficulty)
                    if roll_result['success']:
                        rolls_success += 1
                    # Resolve combat if needed
                    if engine.state.active_combat:
                        combat_result = engine.resolve_combat_round(roll_result['success'])

            # Apply damage/checks
            for damage in result['hp_damage']:
                engine.apply_hp_damage(int(damage))

            for damage in result['sanity_checks']:
                engine.apply_sanity_check(int(damage))

            turn_time = time.time() - turn_start
            turn_times.append(turn_time)

            hp = engine.state.investigator.characteristics['HP']
            san = engine.state.investigator.characteristics['SAN']
            print(f"{format_duration(turn_time):>8} | HP:{hp:>2} SAN:{san:>3}")

        except Exception as e:
            print(f"ERROR: {str(e)[:60]}")
            break

    # Generate ending if needed
    if not engine.check_ending_condition() and turns >= len(actions):
        print("\nGame continues beyond test sequence...")

    total_time = time.time() - start_time

    # Summary
    print(f"\n{'─'*80}")
    print(f"PLAYTHROUGH SUMMARY - {model_name.upper()}")
    print(f"{'─'*80}")
    print(f"Turns completed:     {turns}")
    print(f"Total time:          {format_duration(total_time)}")
    print(f"Avg time/turn:       {format_duration(sum(turn_times)/max(1,len(turn_times)))}")
    print(f"Rolls made:          {rolls_total} ({rolls_success} successful)")
    print(f"Final HP:            {engine.state.investigator.characteristics['HP']}")
    print(f"Final SAN:           {engine.state.investigator.characteristics['SAN']}")
    print(f"Items collected:     {len(engine.state.investigator.inventory)}")
    print(f"Narrative beats:     {len(engine.state.narrative)}")
    print()

    return {
        'model': model_name,
        'turns': turns,
        'total_time': total_time,
        'rolls': rolls_total,
        'success_rate': rolls_success / max(1, rolls_total),
        'final_hp': engine.state.investigator.characteristics['HP'],
        'final_san': engine.state.investigator.characteristics['SAN']
    }

def main():
    """Run all three playthroughs"""
    print("\n" + "="*80)
    print("FULL PLAYTHROUGH TEST - ALL THREE MODELS")
    print("="*80)
    print("Running complete game sessions with realistic player actions...")
    print()

    models = ["mistral", "neural-chat", "orca-mini"]
    results = []

    for model in models:
        try:
            result = run_playthrough(model)
            results.append(result)
        except Exception as e:
            print(f"\n❌ FAILED: {str(e)}")
            import traceback
            traceback.print_exc()

    # Comparison
    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)
    print(f"{'Model':<20} {'Turns':<8} {'Time':<12} {'Avg/Turn':<12} {'Rolls':<8} {'SR %':<8}")
    print("─" * 80)

    for result in results:
        avg_turn = result['total_time'] / max(1, result['turns'])
        sr_pct = (result['success_rate'] * 100)
        print(f"{result['model']:<20} {result['turns']:<8} {format_duration(result['total_time']):<12} "
              f"{format_duration(avg_turn):<12} {result['rolls']:<8} {sr_pct:>6.0f}%")

    print()

if __name__ == '__main__':
    main()
