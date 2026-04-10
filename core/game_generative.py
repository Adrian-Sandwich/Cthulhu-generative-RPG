#!/usr/bin/env python3
"""
GENERATIVE GAME ENGINE - AI Dungeon Master (Mistral 7B local)
Combines fixed story seeds with open-ended LLM narration + CoC mechanics
"""

import json
import random
import re
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
import requests


@dataclass
class InvestigatorState:
    """Player character state"""
    name: str
    occupation: str
    characteristics: Dict[str, int]  # STR, CON, DEX, POW, APP, EDU, INT, SIZ, HP, SAN, Luck
    skills: Dict[str, int]
    inventory: List[str]
    visited_locations: List[str]
    sanity_breaks: List[str]  # Description of each sanity loss event


@dataclass
class GameState:
    """Complete game state"""
    turn: int
    location: str
    narrative: List[str]  # Full story so far
    investigator: InvestigatorState
    recent_actions: List[str]  # Last 5 actions
    game_phase: str  # "exploring", "investigation", "combat", "climax", "ending"
    victory_condition: Optional[str]  # How player could win
    ending_reached: Optional[str]  # "escape", "madness", "victory", "death"


class CoC7eRulesEngine:
    """Call of Cthulhu 7e rules enforcement"""

    DIFFICULTY_MODS = {
        "Normal": 1.0,
        "Hard": 0.5,
        "Extreme": 0.2
    }

    SKILL_TO_CHARACTERISTIC = {
        # Physical skills
        "dodge": "DEX",
        "fight": "DEX",
        "brawl": "STR",
        "climb": "STR",
        "swim": "CON",
        "jump": "DEX",
        "first_aid": "INT",
        "survival_sea": "CON",
        "pilot_boat": "DEX",

        # Mental skills
        "investigate": "INT",
        "psychology": "INT",
        "occult": "EDU",
        "library": "EDU",
        "spot_hidden": "INT",
        "persuade": "APP",
        "science_astronomy": "EDU",
        "religion": "EDU",

        # Navigation/Combat
        "navigate": "INT",
        "firearms_revolver": "DEX",
        "fighting_brawl": "STR",

        # Will/POW skills
        "sanity": "POW",
        "pow": "POW",
    }

    @staticmethod
    def roll_d100() -> int:
        """Roll percentile dice"""
        return random.randint(1, 100)

    @staticmethod
    def resolve_skill_check(
        skill_name: str,
        skill_value: int,
        characteristic_value: int,
        difficulty: str = "Normal"
    ) -> Dict:
        """
        Resolve a skill check per CoC 7e rules.

        Returns: {
            "roll": d100 result,
            "target": effective target number,
            "success": bool,
            "message": str
        }
        """
        # Use skill value if available, else use characteristic
        target = skill_value if skill_value > 0 else characteristic_value

        # Apply difficulty modifier
        mod = CoC7eRulesEngine.DIFFICULTY_MODS.get(difficulty, 1.0)
        effective_target = int(target * mod)

        # Roll
        roll = CoC7eRulesEngine.roll_d100()
        success = roll <= effective_target

        # Critical success (1-5) or critical failure (96-00)
        if roll <= 5:
            success = True
            crit = "CRITICAL SUCCESS"
        elif roll >= 96:
            success = False
            crit = "CRITICAL FAILURE"
        else:
            crit = None

        message = f"Roll {roll} vs {skill_name}({effective_target}) - "
        if success:
            message += f"✓ SUCCESS"
        else:
            message += f"✗ FAILURE"

        if crit:
            message += f" [{crit}]"

        return {
            "roll": roll,
            "target": effective_target,
            "success": success,
            "message": message,
            "critical": crit
        }

    @staticmethod
    def apply_sanity_damage(san: int, damage: int) -> Dict:
        """Apply sanity damage and check for insanity"""
        new_san = max(0, san - damage)

        if new_san == 0:
            return {
                "sanity": new_san,
                "state": "PERMANENT_INSANITY",
                "message": "Your mind shatters. You are lost to madness."
            }
        elif new_san < 20:
            return {
                "sanity": new_san,
                "state": "SEVERE_INSANITY",
                "message": f"Your grip on reality weakens. SAN: {new_san}"
            }
        else:
            return {
                "sanity": new_san,
                "state": "NORMAL",
                "message": f"You lose {damage} sanity. SAN: {new_san}"
            }


class GenerativeGameEngine:
    """AI DM-driven game engine"""

    # Story seeds for Point Black Lighthouse
    STORY_SEED = """
    ALONE AGAINST THE DARK - Point Black Lighthouse

    You arrive at the remote Point Black Lighthouse on the rocky Maine coast.
    Lieutenant Warner called you: the lighthouse keeper has vanished.
    But when you examine the logs, something is wrong. The keeper was dead for two weeks
    before anyone found him—yet someone has been writing in the logs ever since.

    The fog rolls in. The light blinks red. Something ancient stirs beneath the waves.
    """

    # Define 5 endings
    ENDINGS = {
        "escape": {
            "name": "Escape",
            "condition": "Player flees successfully",
            "description": "You escape the lighthouse with your sanity intact. But you know the truth now."
        },
        "madness": {
            "name": "Madness",
            "condition": "Sanity reaches 0",
            "description": "Your mind shatters. You are institutionalized, raving about things beneath the sea."
        },
        "victory": {
            "name": "The Ascended",
            "condition": "Player embraces transformation",
            "description": "You surrender to the change. You become something more than human. Something other."
        },
        "destruction": {
            "name": "Destruction",
            "condition": "Player destroys the lighthouse",
            "description": "The lighthouse crumbles. The fissure seals. For now, the barrier holds."
        },
        "death": {
            "name": "Death",
            "condition": "HP reaches 0",
            "description": "Your body fails. You sink into the depths, transformed."
        }
    }

    def __init__(self, ollama_endpoint: str = "http://localhost:11434"):
        self.ollama_endpoint = ollama_endpoint
        self.model = "mistral"
        self.state: Optional[GameState] = None
        self.rules = CoC7eRulesEngine()

    def create_game(self, investigator: InvestigatorState) -> GameState:
        """Initialize a new game"""
        self.state = GameState(
            turn=1,
            location="Point Black Lighthouse - Exterior",
            narrative=[self.STORY_SEED],
            investigator=investigator,
            recent_actions=[],
            game_phase="exploring",
            victory_condition="Survive and uncover the truth",
            ending_reached=None
        )
        return self.state

    def _call_ollama(self, prompt: str, max_tokens: int = 300) -> str:
        """Call local Mistral model"""
        try:
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "num_predict": max_tokens
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["response"].strip()
        except Exception as e:
            return f"[DM ERROR: {str(e)}]"

    def _build_dm_prompt(self, player_action: str) -> str:
        """Build comprehensive DM prompt with rules hardcoded"""

        inv = self.state.investigator
        narrative_context = "\n".join(self.state.narrative[-5:])  # Last 5 narrative beats

        prompt = f"""You are the Dungeon Master for Call of Cthulhu 7th Edition.

=== CORE RULES (ENFORCE STRICTLY) ===
- ALL skill checks are d100 (roll 1-100)
- Success: roll ≤ target number
- Failure: roll > target number
- Difficulty: Normal (x1), Hard (÷2), Extreme (÷5)

=== SKILL MATRIX - WHEN TO REQUEST ROLLS ===

PHYSICAL ACTIONS (risky/uncertain):
  Climb → scaling cliffs, walls, ropes | Difficulty: varies (Normal/Hard)
  Swim → crossing water, underwater | Difficulty: varies
  Dodge → avoid attacks, hazards | Difficulty: varies
  Brawl/Fight → unarmed combat | Difficulty: varies
  Firearms → shoot weapons | Difficulty: varies
  First Aid → stabilize wounds | Difficulty: varies

INVESTIGATION/PERCEPTION:
  Investigate → examine objects, scenes, evidence | Difficulty: Normal/Hard
  Spot Hidden → find concealed things, details | Difficulty: Hard/Extreme
  Navigate → find way in unfamiliar places, terrain | Difficulty: Normal/Hard
  Survival → subsist in wilderness | Difficulty: varies

KNOWLEDGE/OCCULT:
  Library Use → research in books, archives, documents | Difficulty: Normal/Hard
  Occult → understand symbols, rituals, ancient lore | Difficulty: Hard/Extreme
  Science (Astronomy) → understand celestial phenomena | Difficulty: Hard
  Religion → understand theology, holy matters | Difficulty: Normal

SOCIAL/MENTAL:
  Persuade → convince, negotiate | Difficulty: Normal/Hard
  Psychology → read emotions, detect lies | Difficulty: Normal/Hard

⚠️  CRITICAL: DON'T ROLL FOR (NEVER REQUEST THESE):
  - Entering/exiting locations (just describe it)
  - Walking/moving through areas (unless escaping danger)
  - Looking at things casually (unless searching carefully for hidden objects)
  - Reading logs/documents (unless interpreting complex/magical text)
  - Talking to NPCs (only if persuading them to do something dangerous)

REQUEST ROLLS ONLY FOR (actual risk/challenge):
  - Climbing/swimming (physical risk)
  - Searching carefully for hidden objects (requires Spot Hidden)
  - Understanding complex/occult texts (requires Occult or Library)
  - Dodging attacks or hazards (physical danger)
  - Combat/firing weapons
  - Persuading opposed NPC to take action
  - Finding way through maze-like areas (Navigate)

=== PLAYER CHARACTER ===
Name: {inv.name}
Occupation: {inv.occupation}
HP: {inv.characteristics['HP']}, SAN: {inv.characteristics['SAN']}, POW: {inv.characteristics['POW']}
Key Skills: {json.dumps({k: v for k, v in inv.skills.items() if v >= 40})}

=== CURRENT SITUATION ===
Location: {self.state.location}
Turn: {self.state.turn}
Phase: {self.state.game_phase}

Recent story:
{narrative_context}

=== PLAYER ACTION ===
{player_action}

=== YOUR RESPONSE ===
1. Describe what happens (2-3 sentences, narrative-focused)
2. If action requires a roll, REQUEST IT: [ROLL: skill_name/difficulty]
   - ONLY if the action has real risk/uncertainty AND matches skill matrix above
3. If witnessing cosmic horror, suggest: [SANITY_CHECK: damage]
4. Keep tone atmospheric, dark, foreboding

=== EXAMPLES - ESSENTIAL ===

NO ROLL - routine actions (just narrate):
Player: "I walk into the lighthouse."
DM: You push open the heavy iron door. It creaks on rusted hinges, and you step into the dim interior. ✓ CORRECT
BAD: [ROLL: navigate/normal] ← Wrong! No danger here.

NO ROLL - casual observation:
Player: "I look around the keeper's quarters."
DM: You see a sparse room with a cot, a desk, and a shelf with a few books. ✓ CORRECT
BAD: [ROLL: investigate/normal] ← Wrong! Looking around is free.

ROLL ONLY - active searching:
Player: "I carefully search the desk for hidden compartments."
DM: You run your hands across the weathered wood, probing for secret spaces. [ROLL: investigate/hard] ✓ CORRECT

ROLL ONLY - dangerous action:
Player: "I climb down to the fissure."
DM: The rocks are treacherous, slick with spray. [ROLL: climb/hard] ✓ CORRECT

ROLL ONLY - magic/occult understanding:
Player: "I try to decipher what the symbols mean."
DM: The symbols seem to writhe before your eyes, their meaning elusive. [ROLL: occult/extreme] ✓ CORRECT

NO ROLL - talking/social:
Player: "I ask the officer what he knows."
DM: "The keeper hasn't been seen for weeks," he says, troubled. ✓ CORRECT
BAD: [ROLL: persuade/normal] ← Wrong! They're answering a question.

Remember: Point Black Lighthouse holds ancient secrets. Something non-human waits below.
"""
        return prompt

    def process_player_action(self, player_input: str) -> Dict:
        """
        Process player action and get DM response.
        Returns DM narrative + any requested rolls/sanity checks.
        """
        if not self.state:
            return {"error": "No active game"}

        # Get DM response
        dm_prompt = self._build_dm_prompt(player_input)
        dm_response = self._call_ollama(dm_prompt)

        # Parse roll/sanity requests
        rolls_requested = re.findall(r'\[ROLL: (\w+)/(\w+)\]', dm_response)
        sanity_checks = re.findall(r'\[SANITY_CHECK: (\d+)\]', dm_response)

        # Clean response (remove tags)
        clean_response = re.sub(r'\[ROLL: .*?\]', '', dm_response)
        clean_response = re.sub(r'\[SANITY_CHECK: .*?\]', '', clean_response)

        # Update narrative
        self.state.narrative.append(f"Player: {player_input}")
        self.state.narrative.append(f"DM: {clean_response}")
        self.state.recent_actions.append(player_input)
        if len(self.state.recent_actions) > 5:
            self.state.recent_actions.pop(0)

        self.state.turn += 1

        return {
            "narrative": clean_response,
            "rolls_requested": rolls_requested,  # List of (skill, difficulty) tuples
            "sanity_checks": sanity_checks,  # List of damage values
            "state": asdict(self.state)
        }

    def execute_skill_check(self, skill: str, difficulty: str = "Normal") -> Dict:
        """Execute a requested skill check"""
        if not self.state:
            return {"error": "No active game"}

        inv = self.state.investigator

        # Normalize skill name (lowercase, replace spaces with underscores)
        normalized_skill = skill.lower().replace(' ', '_').replace('(', '').replace(')', '')

        # Try to find skill value (exact match first, then normalized)
        skill_value = inv.skills.get(normalized_skill, 0)
        if skill_value == 0:
            skill_value = inv.skills.get(skill.lower(), 0)

        # Get characteristic to use
        char_key = self.rules.SKILL_TO_CHARACTERISTIC.get(normalized_skill, "INT")
        char_value = inv.characteristics.get(char_key, 50)

        # Resolve check
        result = self.rules.resolve_skill_check(skill, skill_value, char_value, difficulty)

        # Log in narrative
        self.state.narrative.append(f"[ROLL: {result['message']}]")

        return result

    def apply_sanity_check(self, damage: int) -> Dict:
        """Apply sanity damage from witnessing horror"""
        if not self.state:
            return {"error": "No active game"}

        result = self.rules.apply_sanity_damage(
            self.state.investigator.characteristics['SAN'],
            damage
        )

        self.state.investigator.characteristics['SAN'] = result['sanity']
        self.state.investigator.sanity_breaks.append(f"Turn {self.state.turn}: {result['message']}")

        # Check for madness ending
        if result['sanity'] == 0:
            self.state.ending_reached = "madness"

        return result

    def check_ending_condition(self) -> Optional[str]:
        """Check if game should end"""
        inv = self.state.investigator

        if self.state.ending_reached:
            return self.state.ending_reached

        if inv.characteristics['HP'] <= 0:
            self.state.ending_reached = "death"
            return "death"

        if inv.characteristics['SAN'] <= 0:
            self.state.ending_reached = "madness"
            return "madness"

        # Other endings checked by DM narrative
        return None

    def get_ending_text(self) -> Optional[str]:
        """Get narrative for current ending"""
        if not self.state.ending_reached:
            return None

        ending = self.ENDINGS.get(self.state.ending_reached)
        if ending:
            return f"\n{ending['name'].upper()}\n{ending['description']}"

        return None
