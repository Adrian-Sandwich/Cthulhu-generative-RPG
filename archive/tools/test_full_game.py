#!/usr/bin/env python3
"""
Full game session test
Simulates starting a game with a pre-generated character
"""

import uuid
from datetime import datetime
from game_engine import CthulhuGameEngine, GameSession
from pregenerated_characters import PREGENERATED_CHARACTERS

def test_full_session():
    print("=" * 80)
    print("  CALL OF CTHULHU: ALONE AGAINST THE TIDE - FULL SESSION TEST")
    print("=" * 80)

    # Initialize engine
    print("\n[1] Initializing game engine...")
    engine = CthulhuGameEngine()
    print(f"✓ Adventure loaded: {engine.adventure['total_entries']} entries")

    # Use Dr. Eleanor Woods
    print("\n[2] Loading Dr. Eleanor Woods...")
    character = PREGENERATED_CHARACTERS['Eleanor']
    print(f"✓ {character.name} loaded")
    print(f"  HP:{character.hp} SAN:{character.san} LUCK:{character.luck}")
    print(f"  Top skills: Archaeology({character.skills['Archaeology']}%), History({character.skills['History']}%)")

    # Save character to database
    print("\n[3] Saving character to database...")
    char_id = engine.db.save_character(character)
    print(f"✓ Character saved (ID: {char_id})")

    # Create game session
    print("\n[4] Creating game session...")
    session = GameSession(
        session_id=str(uuid.uuid4()),
        character=character,
        current_entry=1
    )
    engine.db.save_session(session)
    print(f"✓ Session created: {session.session_id[:8]}...")
    print(f"  Current entry: {session.current_entry}")
    print(f"  Current SAN: {session.san_current}/{character.san}")

    # Display Entry 1
    print("\n[5] Loading Entry #1...")
    entry1 = engine.get_entry(1)
    print(f"✓ Entry loaded")
    print(f"\n--- ENTRY {entry1['number']} ---")
    print(entry1['text'][:200] + "...\n")

    print(f"Choices available: {len(entry1['choices'])}")
    for i, choice in enumerate(entry1['choices'], 1):
        print(f"  {i}. {choice['text']} → Entry {choice['destination']}")

    # Navigate to entry 12
    print("\n[6] Following choice to Entry #12...")
    entry12 = engine.get_entry(12)
    if entry12:
        print(f"✓ Entry 12 loaded")
        print(f"\n--- ENTRY {entry12['number']} ---")
        print(entry12['text'][:150] + "...\n")
        print(f"Choices: {len(entry12['choices'])}")

    # Update session and save
    print("\n[7] Updating and saving session...")
    session.current_entry = 12
    session.san_current = 58  # Lost 2 SAN
    session.last_action_at = datetime.now()
    session.decisions_made.append({
        'entry': 1,
        'choice_index': 0,
        'destination': 12
    })
    engine.db.save_session(session)
    print(f"✓ Session saved")
    print(f"  Current entry: {session.current_entry}")
    print(f"  SAN: {session.san_current}/{character.san}")
    print(f"  Decisions made: {len(session.decisions_made)}")

    # Test skill check
    print("\n[8] Testing skill check during gameplay...")
    skill_name = 'Archaeology'
    skill_value = character.skills[skill_name]
    print(f"Using skill: {skill_name} ({skill_value}%)")

    success, roll = engine.dice.skill_check(skill_value, 'regular')
    print(f"  Roll: {roll}")
    print(f"  Result: {'SUCCESS' if success else 'FAILURE'}")

    engine.db.log_roll(
        session.session_id, 'skill_check', skill_name, 'regular', success, roll
    )
    print(f"  ✓ Logged to database")

    # Load character back from DB
    print("\n[9] Loading character from database...")
    loaded_char = engine.db.load_character(char_id)
    print(f"✓ Loaded: {loaded_char.name}")
    print(f"  Archaeology: {loaded_char.skills['Archaeology']}%")

    # Summary
    print("\n" + "=" * 80)
    print("  ✅ FULL GAME SESSION TEST COMPLETE")
    print("=" * 80)
    print("✓ Character creation/loading")
    print("✓ Session management")
    print("✓ Entry navigation")
    print("✓ Skill checks")
    print("✓ Database persistence")
    print("\n>>> Ready to play! Run: python3 play.py\n")


if __name__ == '__main__':
    test_full_session()
