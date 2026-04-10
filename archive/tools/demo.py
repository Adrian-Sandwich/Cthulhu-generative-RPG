#!/usr/bin/env python3
"""
Demo script showing the game engine in action
"""

from game_engine import (
    CthulhuGameEngine, Character, Occupation, GameSession,
    DiceRoller
)
import uuid
from datetime import datetime

def demo():
    print("=" * 80)
    print("  CALL OF CTHULHU: ALONE AGAINST THE TIDE - ENGINE DEMO")
    print("=" * 80)

    # Initialize engine
    print("\n[1] Initializing game engine...")
    engine = CthulhuGameEngine()
    print(f"✓ Adventure loaded: {engine.adventure['title']}")
    print(f"✓ Total entries: {engine.adventure['total_entries']}")
    print(f"✓ Total choices available: {sum(len(e['choices']) for e in engine.adventure['entries'])}")

    # Create character
    print("\n[2] Creating investigator...")
    character = Character(
        name="Dr. Samuel Hunt",
        occupation=Occupation.PROFESSOR,
        age=35
    )
    print(f"✓ {character.name} created")
    print(f"  Occupation: {character.occupation.value}")
    print(f"  STR:{character.STR} CON:{character.CON} POW:{character.POW} DEX:{character.DEX}")
    print(f"  HP:{character.hp} SAN:{character.san} Luck:{character.luck}")

    # Save character
    print("\n[3] Saving character to database...")
    char_id = engine.db.save_character(character)
    print(f"✓ Character saved with ID: {char_id}")

    # Load character
    print("\n[4] Loading character from database...")
    loaded_char = engine.db.load_character(char_id)
    print(f"✓ Loaded: {loaded_char.name}")
    print(f"  Top skill: Archaeology ({loaded_char.skills.get('Archaeology', 0)}%)")

    # Create game session
    print("\n[5] Creating game session...")
    session = GameSession(
        session_id=str(uuid.uuid4()),
        character=character,
        current_entry=1
    )
    engine.db.save_session(session)
    print(f"✓ Session created: {session.session_id[:8]}...")

    # Display entry 1
    print("\n[6] Loading Entry #1...")
    entry1 = engine.get_entry(1)
    if entry1:
        print(f"✓ Entry loaded")
        print(f"\n--- ENTRY {entry1['number']} ---")
        print(entry1['text'][:200] + "...")
        print(f"\nChoices available: {len(entry1['choices'])}")
        for i, choice in enumerate(entry1['choices'], 1):
            print(f"  {i}. {choice['text'][:50]}... → Entry {choice['destination']}")

    # Test dice rolls
    print("\n[7] Testing dice system...")
    print(f"  d100 roll: {DiceRoller.d100()}")
    print(f"  d10 roll: {DiceRoller.d10()}")
    print(f"  d6 roll: {DiceRoller.d6()}")
    print(f"  Damage (2D6): {DiceRoller.damage('2D6')}")

    # Test skill checks
    print("\n[8] Testing skill checks...")
    print(f"  Archaeology skill: {character.skills.get('Archaeology', 0)}%")

    success, roll = DiceRoller.skill_check(
        character.skills.get('Archaeology', 0),
        difficulty='regular'
    )
    print(f"  Regular check: roll {roll} → {'SUCCESS' if success else 'FAILURE'}")

    success, roll = DiceRoller.skill_check(
        character.skills.get('Archaeology', 0),
        difficulty='hard'
    )
    print(f"  Hard check: roll {roll} → {'SUCCESS' if success else 'FAILURE'}")

    success, roll = DiceRoller.skill_check(
        character.skills.get('Archaeology', 0),
        difficulty='extreme'
    )
    print(f"  Extreme check: roll {roll} → {'SUCCESS' if success else 'FAILURE'}")

    # Test sanity
    print("\n[9] Testing sanity system...")
    initial_san = session.san_current
    success, roll = DiceRoller.sanity_check(session.san_current)
    print(f"  Current SAN: {session.san_current}")
    print(f"  Check roll: {roll} → {'RESIST' if success else 'FAIL'}")

    if not success:
        loss = DiceRoller.d10()
        print(f"  Sanity loss: {loss} points")

    # Log roll
    print("\n[10] Testing roll logging...")
    engine.db.log_roll(
        session_id=session.session_id,
        roll_type='skill_check',
        skill_name='Archaeology',
        difficulty='regular',
        result=success,
        roll_value=roll
    )
    print(f"✓ Roll logged to database")

    # Summary
    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    print(f"✓ Character system: Working")
    print(f"✓ Database: Working")
    print(f"✓ Adventure entries: {engine.adventure['total_entries']} entries loaded")
    print(f"✓ Dice system: All rolls working")
    print(f"✓ Game flow: Entry navigation ready")
    print("\n  Ready to play! Run: python3 play.py")
    print("=" * 80)


if __name__ == '__main__':
    demo()
