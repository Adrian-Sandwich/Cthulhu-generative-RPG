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
    ending_narrative: Optional[str]  # Rich ending text
    active_combat: Optional[Dict] = None  # Current enemy stats
    npcs_talked_to: Dict[str, List[str]] = None  # NPC key -> topics discussed


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

    # Item definitions
    ITEMS = {
        "flashlight": {"name": "Flashlight", "description": "Casts light in darkness"},
        "notebook": {"name": "Notebook", "description": "For recording findings"},
        "revolver": {"name": "Revolver (.38)", "description": "6-shot pistol", "ammo": 6},
        "dynamite": {"name": "Dynamite (3 sticks)", "description": "Explosive charges"},
        "holy_water": {"name": "Holy Water (vial)", "description": "Blessed by a priest"},
        "rope": {"name": "Rope (30ft)", "description": "Hemp rope"},
        "logbook": {"name": "Keeper's Logbook", "description": "Contains disturbing final entries"},
        "ancient_text": {"name": "Ancient Text", "description": "Pre-human symbols and script"},
    }

    # Enemy definitions
    ENEMIES = {
        "deep_one_hybrid": {"name": "Deep One Hybrid", "hp": 12, "skill": 45, "damage": 6},
        "animated_corpse": {"name": "Animated Corpse", "hp": 8, "skill": 30, "damage": 4},
        "shadow_thing": {"name": "Shadow Entity", "hp": 20, "skill": 60, "damage": 8}
    }

    # NPC definitions
    NPC_DEFINITIONS = {
        "warner": {
            "name": "Lt. William Warner",
            "role": "Coast Guard Officer",
            "knows": ["keeper vanished", "lighthouse abandoned 2 weeks", "strange sounds at night"],
            "personality": "professional but visibly shaken, trying to maintain composure",
            "available_turns": range(1, 10)
        },
        "armitage": {
            "name": "Dr. Henry Armitage",
            "role": "Miskatonic University Professor",
            "knows": ["symbols are pre-human", "fissure predates lighthouse", "ritual to seal it"],
            "personality": "academic, grave, speaks in measured tones",
            "available_turns": range(3, 10)
        }
    }

    def __init__(self, ollama_endpoint: str = "http://localhost:11434", model: str = "mistral"):
        """
        Initialize game engine.

        Args:
            ollama_endpoint: URL to Ollama service
            model: LLM model to use
                - "mistral" - 7B, best quality (5-7 sec/turn)
                - "neural-chat" - Balanced speed & quality (3-4 sec/turn)
                - "orca-mini" - Very fast (1-2 sec/turn)
        """
        self.ollama_endpoint = ollama_endpoint
        self.model = model
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
            ending_reached=None,
            ending_narrative=None,
            active_combat=None,
            npcs_talked_to={}
        )
        return self.state

    def _call_ollama(self, prompt: str, max_tokens: int = 200) -> str:
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
Inventory: {', '.join(inv.inventory) if inv.inventory else 'Empty'}

=== ITEMS (when player finds something) ===
Emit: [ITEM_FOUND: item_key]
Available: flashlight, notebook, revolver, dynamite, holy_water, rope, logbook, ancient_text

=== COMBAT (when player fights creature) ===
Emit: [COMBAT_START: enemy_key]
Available enemies: deep_one_hybrid, animated_corpse, shadow_thing
For environmental damage: [HP_DAMAGE: N]

=== NPC DIALOGUE (when player talks to characters) ===
Emit: [NPC_DIALOGUE: npc_key]
Available: warner, armitage

=== CURRENT SITUATION ===
Location: {self.state.location}
Turn: {self.state.turn}
Phase: {self.state.game_phase}
Combat: {'In combat with ' + self.state.active_combat['name'] if self.state.active_combat else 'None'}

Recent story:
{narrative_context}

=== PLAYER ACTION ===
{player_action}

=== YOUR RESPONSE ===

Respond ONLY as the Dungeon Master. Tell what happens (2-3 sentences).

IF player does something DANGEROUS → ADD TAG: [ROLL: skill/difficulty]
IF player sees COSMIC HORROR → ADD TAG: [SANITY_CHECK: damage_value]
IF player FINDS ITEM → ADD TAG: [ITEM_FOUND: item_key]
IF COMBAT STARTS → ADD TAG: [COMBAT_START: enemy_key]
IF player takes ENVIRONMENTAL DAMAGE → ADD TAG: [HP_DAMAGE: damage_value]

IMPORTANT RULES:
- Don't request rolls for simple actions (walking, talking, looking)
- Only roll if action is risky or has uncertain outcome
- Keep narration atmospheric and dark
- Never explain what you're doing (no "Consider this...", no suggestions, no lists)
"""
        return prompt

    def process_player_action(self, player_input: str) -> Dict:
        """
        Process player action and get DM response.
        Returns DM narrative + any requested rolls/sanity checks/items/combat.
        """
        if not self.state:
            return {"error": "No active game"}

        # Get DM response
        dm_prompt = self._build_dm_prompt(player_input)
        dm_response = self._call_ollama(dm_prompt)

        # Parse all tag types
        rolls_requested = re.findall(r'\[ROLL: (\w+)/(\w+)\]', dm_response)
        sanity_checks = re.findall(r'\[SANITY_CHECK: (\d+)\]', dm_response)
        items_found = re.findall(r'\[ITEM_FOUND: (\w+)\]', dm_response)
        hp_damage = re.findall(r'\[HP_DAMAGE: (\d+)\]', dm_response)
        combat_start = re.findall(r'\[COMBAT_START: (\w+)\]', dm_response)
        npc_dialogue = re.findall(r'\[NPC_DIALOGUE: (\w+)\]', dm_response)

        # Clean response (remove all tags)
        clean_response = re.sub(r'\[ROLL: .*?\]', '', dm_response)
        clean_response = re.sub(r'\[SANITY_CHECK: .*?\]', '', clean_response)
        clean_response = re.sub(r'\[ITEM_FOUND: .*?\]', '', clean_response)
        clean_response = re.sub(r'\[HP_DAMAGE: .*?\]', '', clean_response)
        clean_response = re.sub(r'\[COMBAT_START: .*?\]', '', clean_response)
        clean_response = re.sub(r'\[NPC_DIALOGUE: .*?\]', '', clean_response)

        # Update narrative
        self.state.narrative.append(f"Player: {player_input}")
        self.state.narrative.append(f"DM: {clean_response}")
        self.state.recent_actions.append(player_input)
        if len(self.state.recent_actions) > 5:
            self.state.recent_actions.pop(0)

        self.state.turn += 1

        return {
            "narrative": clean_response,
            "rolls_requested": rolls_requested,
            "sanity_checks": sanity_checks,
            "items_found": items_found,
            "hp_damage": hp_damage,
            "combat_start": combat_start,
            "npc_dialogue": npc_dialogue,
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

    def apply_hp_damage(self, damage: int) -> Dict:
        """Apply HP damage from physical harm"""
        if not self.state:
            return {"error": "No active game"}

        new_hp = max(0, self.state.investigator.characteristics['HP'] - damage)
        self.state.investigator.characteristics['HP'] = new_hp

        if new_hp == 0:
            self.state.ending_reached = "death"
            return {
                "hp": new_hp,
                "state": "DEAD",
                "message": f"You take {damage} damage and collapse. Everything fades to black."
            }
        else:
            return {
                "hp": new_hp,
                "state": "WOUNDED",
                "message": f"You take {damage} damage. HP: {new_hp}"
            }

    def pick_up_item(self, item_key: str) -> str:
        """Add item to inventory"""
        if item_key not in self.ITEMS:
            return f"Item '{item_key}' not found."

        item = self.ITEMS[item_key]
        item_name = item["name"]

        # Check if already have it
        if item_name in self.state.investigator.inventory:
            return f"You already have {item_name}."

        self.state.investigator.inventory.append(item_name)
        return f"You pick up: {item_name}"

    def drop_item(self, item_name: str) -> str:
        """Remove item from inventory"""
        if item_name in self.state.investigator.inventory:
            self.state.investigator.inventory.remove(item_name)
            return f"You drop: {item_name}"
        return f"You don't have {item_name}."

    def use_item(self, item_name: str) -> str:
        """Use an item from inventory"""
        if item_name not in self.state.investigator.inventory:
            return f"You don't have {item_name}."

        # Match item by name to find key
        item_key = None
        for key, item_def in self.ITEMS.items():
            if item_def["name"] == item_name:
                item_key = key
                break

        if not item_key:
            return f"Can't use {item_name}."

        # Apply item effect
        if item_key == "flashlight":
            return "You turn on the flashlight. The beam cuts through the darkness, revealing... shadows within shadows."
        elif item_key == "revolver":
            return "You ready your revolver. The cold metal feels both reassuring and futile against what awaits."
        elif item_key == "rope":
            return "You secure the rope. It should help with climbing, but the danger remains."
        elif item_key == "holy_water":
            return "You splash the holy water. It hisses against the darkness, but the effect is unclear."
        elif item_key == "dynamite":
            return "You prime the dynamite. The fuse hisses. You have seconds to move."
        elif item_key == "notebook":
            return "You write down your observations. Perhaps they'll help someone understand what happened here."
        elif item_key == "logbook":
            return "You read the keeper's final entries. Madness. Transformation. A ritual of awakening."
        elif item_key == "ancient_text":
            return "You study the text. The symbols seem to rearrange themselves, whispering truths your mind cannot fully comprehend."
        else:
            return f"You use {item_name}."

    def start_combat(self, enemy_key: str) -> Dict:
        """Start combat with an enemy"""
        if enemy_key not in self.ENEMIES:
            return {"error": f"Enemy '{enemy_key}' not found"}

        enemy = self.ENEMIES[enemy_key].copy()
        self.state.active_combat = enemy
        self.state.game_phase = "combat"

        return {
            "enemy": enemy["name"],
            "message": f"Combat started: {enemy['name']} (HP: {enemy['hp']})"
        }

    def resolve_combat_round(self, player_roll_success: bool) -> Dict:
        """Resolve one round of combat"""
        if not self.state.active_combat:
            return {"error": "Not in combat"}

        enemy = self.state.active_combat
        result = {"player_hit": False, "enemy_hit": False}

        # Player attacks
        if player_roll_success:
            damage = random.randint(2, 6)
            enemy["hp"] -= damage
            result["player_hit"] = True
            result["player_damage"] = damage
            result["player_message"] = f"You hit! The creature takes {damage} damage."

            if enemy["hp"] <= 0:
                self.state.active_combat = None
                self.state.game_phase = "exploring"
                return {
                    **result,
                    "combat_over": True,
                    "message": f"{enemy['name']} falls. Combat over."
                }
        else:
            result["player_message"] = "You miss!"

        # Enemy counter-attacks
        enemy_roll = self.rules.roll_d100()
        if enemy_roll <= enemy["skill"]:
            damage = random.randint(1, enemy.get("damage", 4))
            self.apply_hp_damage(damage)
            result["enemy_hit"] = True
            result["enemy_damage"] = damage
            result["enemy_message"] = f"{enemy['name']} strikes! You take {damage} damage."
        else:
            result["enemy_message"] = f"{enemy['name']} attacks but misses!"

        return result

    def talk_to_npc(self, npc_key: str, player_question: str) -> str:
        """Have NPC respond to player"""
        if npc_key not in self.NPC_DEFINITIONS:
            return f"That person isn't here."

        npc = self.NPC_DEFINITIONS[npc_key]

        # Track conversation
        if npc_key not in self.state.npcs_talked_to:
            self.state.npcs_talked_to[npc_key] = []
        self.state.npcs_talked_to[npc_key].append(player_question)

        # Build NPC prompt
        prompt = f"""You are {npc['name']}, a {npc['role']}.

Personality: {npc['personality']}

You know about: {', '.join(npc['knows'])}

The player asks: "{player_question}"

Respond in character, in 2-3 sentences. Be dramatic, mysterious, and atmospheric. Reference what you know if relevant."""

        # Get NPC response
        response = self._call_ollama(prompt, max_tokens=80)
        return f"{npc['name']}: {response}"

    def _generate_ending_narrative(self, ending_type: str) -> str:
        """Generate rich narrative for ending"""
        inv = self.state.investigator
        sanity_history = "\n".join(inv.sanity_breaks[-5:]) if inv.sanity_breaks else "None"

        prompt = f"""Write a dramatic 3-paragraph ending for a Call of Cthulhu story.

Character: {inv.name}, a {inv.occupation}
Final Stats: HP {inv.characteristics['HP']}, SAN {inv.characteristics['SAN']}
Ending Type: {ending_type.upper()}

What they witnessed:
{sanity_history}

Write in Lovecraftian horror style. Be literary, poetic, and dark. 3 paragraphs max."""

        ending_text = self._call_ollama(prompt, max_tokens=400)
        self.state.ending_narrative = ending_text
        return ending_text

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
