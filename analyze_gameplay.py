#!/usr/bin/env python3
"""
Analyze 5 gameplay interactions with Neural Chat 7B
Testing: Player 1 (Morgan Detective), trying to enter via high window
"""

import sys
sys.path.insert(0, '.')

from core.game_generative import GenerativeGameEngine, InvestigatorState

# Create Morgan (Detective)
investigator = InvestigatorState(
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
        'firearms_revolver': 35, 'first_aid': 40, 'swimming': 30
    },
    inventory=['Flashlight', 'Notebook'],
    visited_locations=[],
    sanity_breaks=[]
)

# Create engine with Neural Chat
engine = GenerativeGameEngine(model="neural-chat")
engine.create_game(investigator)

print("\n" + "="*80)
print("GAMEPLAY ANALYSIS: Morgan (Detective) with Neural Chat 7B")
print("Scenario: Cannot open door, attempting to reach high window")
print("="*80 + "\n")

# Turn 1: Initial setup
print("TURN 1: Initial Action")
print("-" * 80)
action1 = "As I cannot open the door, I try to reach for a very high window"
print(f"Player: {action1}\n")

def silent_chunk(chunk):
    pass

result1 = engine.process_player_action(action1, on_chunk=silent_chunk)
print(f"DM Response:\n{result1['narrative']}\n")
print(f"Rolls Requested: {result1['rolls_requested']}")
if result1['rolls_requested']:
    skill, diff = result1['rolls_requested'][0]
    print(f"→ Roll needed: {skill.upper()} ({diff.upper()})")
    roll1 = engine.execute_skill_check(skill, diff)
    print(f"→ Roll result: {roll1['message']}\n")

    # Resolve consequences
    if engine.state.last_roll:
        print("Resolving consequences...\n")
        consequence = engine.resolve_roll_consequences(on_chunk=silent_chunk)
        print(f"Consequence: {consequence['narrative']}\n")
        print(f"HP Damage: {consequence['hp_damage']}")
        print(f"Analysis: {'SUCCESS - Player entered' if consequence['success'] else 'FAILURE - Player took damage'}\n")

# Turn 2: Follow-up action
print("\nTURN 2: Next Action After Consequence")
print("-" * 80)
action2 = "I dust myself off and look around carefully"
print(f"Player: {action2}\n")

result2 = engine.process_player_action(action2, on_chunk=silent_chunk)
print(f"DM Response:\n{result2['narrative']}\n")
print(f"Rolls Requested: {result2['rolls_requested']}")
print(f"Items Found: {result2['items_found']}\n")

# Turn 3: Investigation action
print("\nTURN 3: Investigation")
print("-" * 80)
action3 = "I investigate the area around the window and look for clues"
print(f"Player: {action3}\n")

result3 = engine.process_player_action(action3, on_chunk=silent_chunk)
print(f"DM Response:\n{result3['narrative']}\n")
print(f"Rolls Requested: {result3['rolls_requested']}")
if result3['rolls_requested']:
    skill, diff = result3['rolls_requested'][0]
    print(f"→ Roll needed: {skill.upper()} ({diff.upper()})")
    roll3 = engine.execute_skill_check(skill, diff)
    print(f"→ Roll result: {roll3['message']}\n")

    if engine.state.last_roll:
        consequence3 = engine.resolve_roll_consequences(on_chunk=silent_chunk)
        print(f"Consequence: {consequence3['narrative']}\n")
        print(f"Analysis: {'Found clues' if consequence3['success'] else 'Missed important details'}\n")

# Turn 4: Inventory check
print("\nTURN 4: Use Item - Flashlight")
print("-" * 80)
action4 = "I use my flashlight to get a better look inside"
print(f"Player: {action4}\n")

result4 = engine.process_player_action(action4, on_chunk=silent_chunk)
print(f"DM Response:\n{result4['narrative']}\n")

# Turn 5: Attempt entry
print("\nTURN 5: Final Attempt - Try to Enter Window")
print("-" * 80)
action5 = "I carefully climb through the window into the lighthouse"
print(f"Player: {action5}\n")

result5 = engine.process_player_action(action5, on_chunk=silent_chunk)
print(f"DM Response:\n{result5['narrative']}\n")
print(f"Rolls Requested: {result5['rolls_requested']}")
if result5['rolls_requested']:
    skill, diff = result5['rolls_requested'][0]
    print(f"→ Roll needed: {skill.upper()} ({diff.upper()})")
    roll5 = engine.execute_skill_check(skill, diff)
    print(f"→ Roll result: {roll5['message']}\n")

    if engine.state.last_roll:
        consequence5 = engine.resolve_roll_consequences(on_chunk=silent_chunk)
        print(f"Consequence: {consequence5['narrative']}\n")
        print(f"Analysis: {'SUCCESS - Entered lighthouse' if consequence5['success'] else 'FAILURE - Could not enter'}\n")

# Summary
print("\n" + "="*80)
print("GAME STATE SUMMARY")
print("="*80)
print(f"Turn: {engine.state.turn}")
print(f"Location: {engine.state.location}")
print(f"HP: {engine.state.investigator.characteristics['HP']}")
print(f"SAN: {engine.state.investigator.characteristics['SAN']}")
print(f"Inventory: {engine.state.investigator.inventory}")
print(f"Game Phase: {engine.state.game_phase}")
print(f"Active Combat: {engine.state.active_combat is not None}")
print("\n" + "="*80)
