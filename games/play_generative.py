#!/usr/bin/env python3
"""
ALONE AGAINST THE DARK - GENERATIVE VERSION
Play with an AI Dungeon Master (Mistral 7B)
"""

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.game_generative import GenerativeGameEngine, InvestigatorState, CoC7eRulesEngine
from ui.keeper_thinking import show_keeper_thinking, KeeperThinking
from ui.history_viewer import HistoryViewer


def clear():
    """Clear terminal"""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_header(text):
    """Print fancy header"""
    print("\n" + "=" * 80)
    print(text.center(80))
    print("=" * 80 + "\n")


def stream_callback(chunk):
    """Print LLM response as it streams in real-time"""
    import sys
    sys.stdout.write(chunk)
    sys.stdout.flush()


def print_box(text, width=80):
    """Print text in a box"""
    lines = text.split('\n')
    print("╔" + "═" * (width - 2) + "╗")
    for line in lines:
        padding = width - 2 - len(line)
        print(f"║ {line}{' ' * padding} ║")
    print("╚" + "═" * (width - 2) + "╝\n")


def load_prebuilt_investigators(filename: str = 'adventures/point_black/investigators.json') -> list:
    """Load prebuilt investigator templates from JSON"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def json_to_investigator(json_data: dict) -> InvestigatorState:
    """Convert JSON investigator format to InvestigatorState"""
    # Normalize skill names (lowercase, remove special chars for matching)
    skills = {}
    for skill_name, value in json_data.get('skills', {}).items():
        # Convert to lowercase and simplified name for matching
        normalized = skill_name.lower().replace(' ', '_').replace('(', '').replace(')', '')
        skills[normalized] = value

    return InvestigatorState(
        name=json_data['name'],
        occupation=json_data['occupation'],
        characteristics=json_data['characteristics'],
        skills=skills,
        inventory=['Flashlight', 'Notebook'],
        visited_locations=[],
        sanity_breaks=[]
    )


def select_model() -> str:
    """Let user choose LLM model"""
    clear()
    print_header("SELECT LLM MODEL")

    print("""OPTIONS:

  1) Mistral 7B (Best Quality)
     • Best quality narration
     • Rich descriptions & atmosphere
     • 5-7 seconds per turn
     • Recommended: Story immersion

  2) Neural Chat (Balanced)
     • Good quality & balance
     • Fast & engaging responses
     • 3-4 seconds per turn
     • Recommended: Smooth gameplay

  3) Orca Mini (Speed)
     • Very fast responses
     • Good coherence, more concise
     • 1-2 seconds per turn
     • Recommended: Quick playthroughs

  4) Qwen 2.5 7B (Advanced Reasoning)
     • Advanced reasoning & context understanding
     • Rich narratives with logical consistency
     • 4-6 seconds per turn
     • Recommended: Complex storylines
""")

    while True:
        choice = input("Enter choice (1-4): ").strip()
        if choice == "1":
            return "mistral"
        elif choice == "2":
            return "neural-chat"
        elif choice == "3":
            return "orca-mini"
        elif choice == "4":
            return "qwen2.5:7b"
        print("Invalid choice. Enter 1, 2, 3, or 4.")


def select_investigator() -> InvestigatorState:
    """Let user choose: prebuilt or create new"""
    clear()
    print_header("SELECT YOUR INVESTIGATOR")

    # Load prebuilt investigators
    prebuilt = load_prebuilt_investigators()

    print("OPTIONS:\n")
    print("  0) Create a new investigator")

    if prebuilt:
        for i, inv in enumerate(prebuilt, 1):
            print(f"  {i}) {inv['name']:25} - {inv['occupation']}")
            chars = inv['characteristics']
            print(f"     HP: {chars['HP']}, SAN: {chars['SAN']}, POW: {chars['POW']}")

    print()
    while True:
        choice = input("Enter choice (0-{}): ".format(len(prebuilt))).strip()
        if choice.isdigit():
            choice_num = int(choice)
            if 0 <= choice_num <= len(prebuilt):
                if choice_num == 0:
                    return create_new_investigator()
                else:
                    return json_to_investigator(prebuilt[choice_num - 1])
        print("Invalid choice. Try again.")


def create_new_investigator() -> InvestigatorState:
    """Custom character creation"""
    clear()
    print_header("CREATE YOUR INVESTIGATOR")

    print("Enter your investigator's details:\n")

    name = input("Name: ").strip() or "Unknown"
    occupation = input("Occupation: ").strip() or "Drifter"

    # Use preset characteristics
    characteristics = {
        'STR': 65,
        'CON': 60,
        'DEX': 65,
        'INT': 80,
        'APP': 60,
        'POW': 70,
        'EDU': 75,
        'SIZ': 60,
        'HP': 13,
        'SAN': 70,
        'Luck': 50
    }

    # Use preset skills
    skills = {
        'investigate': 60,
        'psychology': 45,
        'occult': 35,
        'dodge': 50,
        'fight': 40,
        'climb': 45,
        'library': 50,
        'spot_hidden': 50,
        'persuade': 40,
        'navigate': 30,
        'firearms_revolver': 35,
        'first_aid': 40,
        'swimming': 30
    }

    return InvestigatorState(
        name=name,
        occupation=occupation,
        characteristics=characteristics,
        skills=skills,
        inventory=['Flashlight', 'Notebook', 'Matches'],
        visited_locations=[],
        sanity_breaks=[]
    )


def display_game_state(engine: GenerativeGameEngine):
    """Display current game status"""
    inv = engine.state.investigator
    san_bar = "█" * int(inv.characteristics['SAN'] / 4) + "░" * (25 - int(inv.characteristics['SAN'] / 4))
    hp_bar = "♥" * inv.characteristics['HP'] + "♡" * (15 - inv.characteristics['HP'])

    print("\n" + "-" * 80)
    print(f"{inv.name} ({inv.occupation})")
    print(f"  HP: [{hp_bar}] {inv.characteristics['HP']:2d}  │  SAN: [{san_bar}] {inv.characteristics['SAN']:3d}  │  Luck: {inv.characteristics['Luck']:2d}")
    print(f"  Location: {engine.state.location}")

    # Show enemy HP if in combat
    if engine.state.active_combat:
        enemy = engine.state.active_combat
        enemy_hp_bar = "█" * enemy['hp'] + "░" * (12 - min(enemy['hp'], 12))
        print(f"  Enemy: {enemy['name']} [{enemy_hp_bar}] {enemy['hp']} HP")

    print("-" * 80 + "\n")


def show_help():
    """Show available commands"""
    return """
COMMANDS:
  [action]          Describe what you do (e.g., "examine the door", "run away")
  [i]nventory       Check your inventory
  [u]se [item]      Use an item (e.g., "use flashlight", "use revolver")
  [d]rop [item]     Drop an item (e.g., "drop notebook")
  [s]tatus          Full character status
  [v]iew history    Review complete game history
  [h]elp            Show this help
  [q]uit            Quit game

Type your action in natural language. The DM will respond.
Talk to NPCs by saying: "talk to warner", "ask armitage about...", etc.
"""


def handle_roll_request(engine: GenerativeGameEngine, skill: str, difficulty: str):
    """Handle a skill check request from DM - player controls the roll"""
    clear()
    print_header(f"SKILL CHECK")
    print(f"Skill: {skill.upper()}")
    print(f"Difficulty: {difficulty.upper()}")
    print()
    print("Roll the dice... Press ENTER to test your fate")
    input()

    # Player presses ENTER to roll
    result = engine.execute_skill_check(skill, difficulty)

    # Display roll result dramatically
    print()
    if result['success']:
        print("💚 " + "=" * 76)
        print(f"✓ SUCCESS! {result['message']}")
        print("=" * 78)
    else:
        print("💔 " + "=" * 76)
        print(f"✗ FAILURE! {result['message']}")
        print("=" * 78)

    if result['critical']:
        print(f"\n⚡ {result['critical']} ⚡")

    print()
    input("Press ENTER to continue...")


def detect_and_resume() -> Optional[Tuple[GenerativeGameEngine, str]]:
    """
    Detect available saves and ask player if they want to continue.

    Returns:
        Tuple of (engine, model) if continuing, None if new game
    """
    from core.generative_save import GenerativeSave

    saves = GenerativeSave.list_saves()

    if not saves:
        return None

    clear()
    print_header("SAVED SESSIONS FOUND")

    for i, save in enumerate(saves[:5], 1):
        ts = save["timestamp"][:16].replace("T", " ")
        print(f"  {i}) {save['investigator']:25} | Turn {save['turn']:3} | {save['location'][:30]}")
        print(f"     Model: {save['model']:20} | Saved: {ts}")
        print()

    print("  0) Start new game\n")

    while True:
        choice = input("Continue a session (0-{}): ".format(min(len(saves), 5))).strip()
        if choice == "0":
            return None
        if choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= min(len(saves), 5):
                save_meta = saves[choice_num - 1]
                try:
                    engine = GenerativeGameEngine.load_game(save_meta["session_id"])
                    return engine, save_meta["model"]
                except Exception as e:
                    print(f"Error loading save: {e}")
                    return None
        print("Invalid choice. Try again.")


def _run_game_loop(engine: GenerativeGameEngine, model: str):
    """
    Run the main game loop for an engine.

    Args:
        engine: Initialized GenerativeGameEngine
        model: LLM model name
    """
    # Main game loop
    while True:
        clear()

        # Check for ending
        ending = engine.check_ending_condition()
        if ending:
            # Generate rich ending narrative if not already done
            if not engine.state.ending_narrative:
                print_header("GENERATING ENDING")
                print("The DM is writing your fate...")
                engine._generate_ending_narrative(ending)

            # Display ending
            print_header(f"GAME OVER - {ending.upper()}")
            print(engine.state.ending_narrative if engine.state.ending_narrative else engine.get_ending_text())
            print("\n" + "=" * 80)
            break

        # Display state
        display_game_state(engine)

        # Show recent narrative (last 2 DM responses)
        print("━" * 80)
        narrative = engine.state.narrative[-2:]
        for line in narrative:
            if line.startswith("DM:"):
                print(f"\n{line[4:]}\n")

        print("━" * 80)
        print("\nWhat do you do?")
        action = input("\n➜ ").strip()

        if not action:
            continue

        # Process commands
        if action.lower() == 'q':
            if input("Quit game? (y/n): ").lower() == 'y':
                print("\nThe lighthouse light fades behind you.")
                print("But you know the truth now...\n")
                break

        elif action.lower() == 'h':
            clear()
            print(show_help())
            input("Press ENTER to continue...")

        elif action.lower() == 'i':
            clear()
            print_header("INVENTORY")
            if not engine.state.investigator.inventory:
                print("  Empty")
            else:
                for item in engine.state.investigator.inventory:
                    # Find description
                    desc = item
                    for key, item_def in engine.ITEMS.items():
                        if item_def["name"] == item:
                            desc = f"{item} — {item_def['description']}"
                            break
                    print(f"  • {desc}")
            print()
            input("Press ENTER to continue...")

        elif action.lower() == 's':
            clear()
            print_header("CHARACTER STATUS")
            inv = engine.state.investigator
            print(f"Name: {inv.name}")
            print(f"Occupation: {inv.occupation}")
            print(f"\nCHARACTERISTICS:")
            print(f"  STR: {inv.characteristics['STR']:3d}  CON: {inv.characteristics['CON']:3d}  " +
                  f"DEX: {inv.characteristics['DEX']:3d}  INT: {inv.characteristics['INT']:3d}")
            print(f"  APP: {inv.characteristics['APP']:3d}  POW: {inv.characteristics['POW']:3d}  " +
                  f"EDU: {inv.characteristics['EDU']:3d}  SIZ: {inv.characteristics['SIZ']:3d}")
            print(f"\nDERIVED:")
            print(f"  HP: {inv.characteristics['HP']:3d}  SAN: {inv.characteristics['SAN']:3d}  " +
                  f"Luck: {inv.characteristics['Luck']:3d}")
            print(f"\nTurns: {engine.state.turn}")
            print()
            input("Press ENTER to continue...")

        elif action.lower() in ('v', 'hist', 'history'):
            # View game history
            viewer = HistoryViewer(width=80)
            inv = engine.state.investigator
            viewer.display_full_history(
                narrative_turns=engine.state.narrative,
                investigator_name=inv.name,
                location=engine.state.location,
                turn=engine.state.turn,
                discoveries=[d for d in engine.state.narrative if "discover" in d.lower()],
                stats={
                    "HP":  (inv.characteristics['HP'],  inv.characteristics.get('max_hp', 14)),
                    "SAN": (inv.characteristics['SAN'], inv.characteristics.get('max_san', 99)),
                    "Luck": inv.characteristics['Luck'],
                }
            )
            input("Press ENTER to continue...")

        elif action.lower().startswith('u ') or action.lower().startswith('use '):
            # Use item command
            item_name = action[2:].strip() if action.lower().startswith('u ') else action[4:].strip()
            clear()
            print_header("USING ITEM")
            result = engine.use_item(item_name)
            print(result)
            input("\nPress ENTER to continue...")

        elif action.lower().startswith('d ') or action.lower().startswith('drop '):
            # Drop item command
            item_name = action[2:].strip() if action.lower().startswith('d ') else action[5:].strip()
            clear()
            print_header("DROPPING ITEM")
            result = engine.drop_item(item_name)
            print(result)
            input("\nPress ENTER to continue...")

        elif action.lower().startswith('talk to ') or action.lower().startswith('ask '):
            # NPC dialogue
            if action.lower().startswith('talk to '):
                npc_text = action[8:].strip()
            else:
                npc_text = action[4:].strip()

            # Try to identify NPC
            npc_key = None
            for key, npc_def in engine.NPC_DEFINITIONS.items():
                if key in npc_text.lower():
                    npc_key = key
                    break

            if npc_key:
                clear()
                print_header("NPC DIALOGUE")

                # Show Keeper thinking while NPC responds
                show_keeper_thinking(preset="npc_dialogue")

                dialogue = engine.talk_to_npc(npc_key, npc_text)
                print(dialogue)
                input("\nPress ENTER to continue...")
            else:
                print("That person isn't here.")
                input("Press ENTER to continue...")

        else:
            # Regular action
            clear()
            print_header("DUNGEON MASTER")

            # Show Keeper thinking animation while processing
            show_keeper_thinking(preset="action_resolution")

            # Process action with streaming callback - response displays in real-time
            result = engine.process_player_action(action, on_chunk=stream_callback)

            print("\n")  # Newline after streamed response

            # Handle items found
            for item_key in result['items_found']:
                item_msg = engine.pick_up_item(item_key)
                print(f"\n✓ {item_msg}")

            # Handle HP damage
            for damage_str in result['hp_damage']:
                input("\nPress ENTER to resolve damage...")
                hp_result = engine.apply_hp_damage(int(damage_str))
                clear()
                print_header("TAKING DAMAGE")
                print(hp_result['message'])
                input("\nPress ENTER to continue...")
                clear()
                print_header("DUNGEON MASTER")
                print(result['narrative'])

            # Handle combat start
            for enemy_key in result['combat_start']:
                combat_result = engine.start_combat(enemy_key)
                if 'error' not in combat_result:
                    print(f"\n⚔️  {combat_result['message']}")

            # Handle NPC dialogue from DM
            for npc_key in result['npc_dialogue']:
                if npc_key in engine.NPC_DEFINITIONS:
                    npc = engine.NPC_DEFINITIONS[npc_key]
                    print(f"\n  {npc['name']}: [appears and speaks]")

            # Handle roll requests
            for skill, difficulty in result['rolls_requested']:
                input("\nPress ENTER to make the skill check...")
                handle_roll_request(engine, skill, difficulty)

                # Automatically resolve the consequences of the roll
                clear()
                print_header("RESOLVING OUTCOME")

                # Show Keeper thinking while determining consequences
                show_keeper_thinking(preset="action_resolution")

                consequence_result = engine.resolve_roll_consequences(on_chunk=stream_callback)
                print("\n")

                # Display consequence damage if any
                for damage in consequence_result['hp_damage']:
                    hp_res = engine.apply_hp_damage(int(damage))
                    print(f"\n💔 DAMAGE: {hp_res['message']}")
                    input("Press ENTER to continue...")

                for damage in consequence_result['sanity_checks']:
                    san_res = engine.apply_sanity_check(int(damage))
                    san_msg = f"You lose {damage} sanity points"
                    if san_res.get('broke'):
                        san_msg += f" - {san_res.get('narrative', 'breaking point!')}"
                    print(f"\n😰 SANITY: {san_msg}")
                    input("Press ENTER to continue...")

                # If in combat, resolve that round
                if engine.state.active_combat:
                    # Find the last roll result in narrative
                    player_hit = False
                    for msg in reversed(engine.state.narrative[-3:]):
                        if "SUCCESS" in msg or "✓" in msg:
                            player_hit = True
                            break
                        if "FAILURE" in msg or "✗" in msg:
                            player_hit = False
                            break

                    combat_round = engine.resolve_combat_round(player_hit)
                    if "error" not in combat_round:
                        clear()
                        print_header("COMBAT ROUND")
                        print(combat_round.get('player_message', ''))
                        print(combat_round.get('enemy_message', ''))
                        if combat_round.get('combat_over'):
                            print("\n🎭 Combat has ended!")
                        input("\nPress ENTER to continue...")

            # Handle sanity checks
            for damage in result['sanity_checks']:
                input("\nPress ENTER to resolve sanity check...")
                san_result = engine.apply_sanity_check(int(damage))
                clear()
                print_header("SANITY CHECK")
                san_msg = f"You lose {damage} sanity points"
                if san_result.get('broke'):
                    san_msg += f"\n\n{san_result.get('narrative', 'A breaking point!')}"
                print(san_msg)
                new_san = engine.state.investigator.characteristics['SAN']
                print(f"\nSanity: {new_san}/99")
                input("\nPress ENTER to continue...")

            # AUTO-SAVE after each turn (silent)
            engine.save_game()

            input("\nPress ENTER to continue...")


def main():
    """Main entry point - handles session detection and game startup"""
    clear()
    print_box("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║           ALONE AGAINST THE DARK - GENERATIVE EDITION                    ║
║                                                                           ║
║                  Play with an AI Dungeon Master                          ║
║              (Mistral 7B running locally via Ollama)                     ║
║                                                                           ║
║               "In the darkness, something ancient stirs..."             ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """, width=82)

    # Try to detect and resume existing session
    resume_result = detect_and_resume()
    if resume_result:
        engine, model = resume_result
        print(f"\n✓ Resuming session (Turn {engine.state.turn})")
        input("Press ENTER to continue your investigation...")
        _run_game_loop(engine, model)
        return

    # New game flow
    input("Press ENTER to select your model...")

    # Model selection
    model = select_model()

    input("Press ENTER to select your investigator...")

    # Character selection/creation
    investigator = select_investigator()

    # Initialize engine with selected model
    engine = GenerativeGameEngine(model=model)
    engine.create_game(investigator)

    # Show selected model
    MODEL_NAMES = {
        "mistral": "Mistral 7B (Best Quality)",
        "neural-chat": "Neural Chat 7B (Balanced)",
        "orca-mini": "Orca Mini 3B (Speed)",
        "qwen2.5:7b": "Qwen 2.5 7B (Advanced Reasoning)"
    }
    model_name = MODEL_NAMES.get(model, model)
    print(f"\n🤖 Using: {model_name}")

    clear()
    print_box(engine.state.narrative[0], width=82)

    input("Press ENTER to start your investigation...")

    # Run game loop
    _run_game_loop(engine, model)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nThe darkness takes you.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
