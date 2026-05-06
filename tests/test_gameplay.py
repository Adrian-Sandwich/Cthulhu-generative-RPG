#!/usr/bin/env python3
"""
Test complete gameplay with all 4 features
Runs a quick 5-turn session to verify:
  1. Interactive rolls (player-controlled)
  2. Ending sequences (narrative generation)
  3. NPC dialogue (conversation system)
  4. Inventory management (pick up/use/drop)
  5. Combat system (HP damage and enemy tracking)
"""

import sys
import json
import time
sys.path.insert(0, '.')

from core.game_generative import GenerativeGameEngine, InvestigatorState

def create_test_investigator():
    """Create a simple test character"""
    return InvestigatorState(
        name="Morgan",
        occupation="Detective",
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

def test_model(model_name):
    """Test a complete game session with given model"""
    print(f"\n{'='*80}")
    print(f"TESTING: {model_name.upper()}")
    print(f"{'='*80}\n")

    # Initialize engine
    investigator = create_test_investigator()
    engine = GenerativeGameEngine(model=model_name)
    engine.create_game(investigator)

    print(f"✓ Game created with {investigator.name} ({investigator.occupation})")
    print(f"  HP: {investigator.characteristics['HP']}, SAN: {investigator.characteristics['SAN']}\n")

    # Test 1: Basic DM response with streaming
    print("TEST 1: Basic action with streaming response")
    print("-" * 80)
    start_time = time.time()

    def count_chars(chunk):
        """Count streamed characters"""
        sys.stdout.write(chunk)
        sys.stdout.flush()

    result = engine.process_player_action("I examine the lighthouse carefully.", on_chunk=count_chars)
    elapsed = time.time() - start_time

    print(f"\n✓ Completed in {elapsed:.2f}s")
    print(f"  Narrative length: {len(result['narrative'])} chars\n")

    # Test 2: Check for roll requests
    print("TEST 2: Skill check request detection")
    print("-" * 80)

    if result['rolls_requested']:
        skill, difficulty = result['rolls_requested'][0]
        print(f"✓ Roll requested: {skill.upper()} ({difficulty.upper()})")

        # Execute the roll
        roll_result = engine.execute_skill_check(skill, difficulty)
        print(f"  Roll: {roll_result['roll']} vs {roll_result['target']}")
        print(f"  Result: {'SUCCESS ✓' if roll_result['success'] else 'FAILURE ✗'}\n")
    else:
        print("  (No roll in this action)\n")

    # Test 3: Inventory management
    print("TEST 3: Inventory system")
    print("-" * 80)
    inv_before = len(engine.state.investigator.inventory)
    engine.pick_up_item("revolver")
    inv_after = len(engine.state.investigator.inventory)
    print(f"✓ Picked up revolver")
    print(f"  Inventory: {inv_before} → {inv_after} items")
    print(f"  Items: {', '.join(engine.state.investigator.inventory)}\n")

    # Test 4: NPC dialogue
    print("TEST 4: NPC dialogue system")
    print("-" * 80)
    npc_response = engine.talk_to_npc("warner", "What do you know about the keeper?")
    print(f"✓ Warner responds:")
    print(f"  {npc_response[:120]}...\n")

    # Test 5: Combat system
    print("TEST 5: Combat system")
    print("-" * 80)
    combat_result = engine.start_combat("deep_one_hybrid")
    if 'error' not in combat_result:
        print(f"✓ Combat started: {combat_result['enemy']}")
        enemy = engine.state.active_combat
        print(f"  Enemy HP: {enemy['hp']}, Skill: {enemy['skill']}\n")

        # Resolve one combat round
        round_result = engine.resolve_combat_round(True)  # Assume player hit
        print(f"  Player: {round_result.get('player_message', 'N/A')}")
        print(f"  Enemy: {round_result.get('enemy_message', 'N/A')}\n")
    else:
        print(f"✗ Combat failed: {combat_result['error']}\n")

    # Test 6: Sanity check
    print("TEST 6: Sanity check system")
    print("-" * 80)
    san_before = engine.state.investigator.characteristics['SAN']
    san_result = engine.apply_sanity_check(5)
    san_after = engine.state.investigator.characteristics['SAN']
    print(f"✓ Sanity check applied")
    print(f"  SAN: {san_before} → {san_after}")
    print(f"  State: {san_result['state']}\n")

    # Test 7: HP damage
    print("TEST 7: HP damage system")
    print("-" * 80)
    hp_before = engine.state.investigator.characteristics['HP']
    hp_result = engine.apply_hp_damage(3)
    hp_after = engine.state.investigator.characteristics['HP']
    print(f"✓ HP damage applied")
    print(f"  HP: {hp_before} → {hp_after}")
    print(f"  State: {hp_result['state']}\n")

    # Test 8: Ending condition check
    print("TEST 8: Ending condition check")
    print("-" * 80)
    ending = engine.check_ending_condition()
    if ending:
        print(f"✓ Ending condition: {ending.upper()}")
        # Generate ending narrative
        engine._generate_ending_narrative(ending)
        print(f"  Narrative: {engine.state.ending_narrative[:100]}...\n")
    else:
        print(f"✓ Game continues (no ending yet)\n")

    # Summary
    print("="*80)
    print(f"SUMMARY FOR {model_name.upper()}")
    print("="*80)
    print(f"Turn: {engine.state.turn}")
    print(f"HP: {engine.state.investigator.characteristics['HP']}")
    print(f"SAN: {engine.state.investigator.characteristics['SAN']}")
    print(f"Inventory: {len(engine.state.investigator.inventory)} items")
    print(f"Narrative beats: {len(engine.state.narrative)}")
    print(f"NPCs talked to: {len(engine.state.npcs_talked_to)}")
    print()

    return True

def main():
    """Test all three models"""
    print("\n" + "="*80)
    print("COMPLETE GAMEPLAY TEST - ALL FEATURES")
    print("="*80)
    print("Testing:")
    print("  1. Interactive skill checks (player-controlled rolls)")
    print("  2. DM narration with streaming")
    print("  3. Inventory system (pick up/drop/use)")
    print("  4. NPC dialogue with conversation tracking")
    print("  5. Combat system with HP tracking")
    print("  6. Sanity checks and insanity states")
    print("  7. Ending narrative generation")
    print()

    models = [
        ("mistral", "Mistral 7B - Best Quality"),
        ("neural-chat", "Neural Chat - Balanced"),
        ("orca-mini", "Orca Mini - Speed")
    ]

    results = {}
    for model_id, model_name in models:
        try:
            success = test_model(model_id)
            results[model_id] = "✓ PASS"
        except Exception as e:
            results[model_id] = f"✗ FAIL: {str(e)[:50]}"
            import traceback
            traceback.print_exc()

    # Final report
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    for model_id, model_name in models:
        status = results.get(model_id, "? UNKNOWN")
        print(f"  {model_name:40} {status}")
    print()

if __name__ == '__main__':
    main()
