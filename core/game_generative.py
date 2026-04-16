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
    last_roll: Optional[Dict] = None  # Track last roll result (skill, difficulty, success)
    npc_reputation: Dict[str, int] = None  # NPC key -> reputation score (-100 to +100)


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
            "knows_secret": [
                "I saw something in the water two months ago. Unnatural. Not a whale, not a fish.",
                "The keeper's name was Marinus Weld. He was afraid of something specific... kept muttering about 'the deep'."
            ],
            "personality": "professional but visibly shaken, trying to maintain composure",
            "available_turns": range(1, 10)
        },
        "armitage": {
            "name": "Dr. Henry Armitage",
            "role": "Miskatonic University Professor",
            "knows": ["symbols are pre-human", "fissure predates lighthouse", "ritual to seal it"],
            "knows_secret": [
                "I've decoded part of the inscription. It's a warning, not a seal. The seal was never completed.",
                "The lighthouse wasn't built to protect anything from us. It was built to contain something beneath the ocean. To keep it sleeping."
            ],
            "personality": "academic, grave, speaks in measured tones",
            "available_turns": range(3, 10)
        }
    }

    def __init__(self, ollama_endpoint: str = "http://localhost:11434", model: str = "mistral",
                 session_id: Optional[str] = None, use_memory: bool = True):
        """
        Initialize game engine.

        Args:
            ollama_endpoint: URL to Ollama service
            model: LLM model to use
                - "mistral" - 7B, best quality (5-7 sec/turn)
                - "neural-chat" - Balanced speed & quality (3-4 sec/turn)
                - "orca-mini" - Very fast (1-2 sec/turn)
                - "qwen3:8b" - Advanced reasoning (4-6 sec/turn)
            session_id: Unique session identifier (auto-generated if None)
            use_memory: Enable semantic memory with ChromaDB (default True)
        """
        import time

        self.ollama_endpoint = ollama_endpoint
        self.model = model
        self.session_id = session_id or f"session_{int(time.time())}"
        self.state: Optional[GameState] = None
        self.rules = CoC7eRulesEngine()

        # Initialize semantic memory if available and enabled
        self.memory = None
        if use_memory:
            try:
                from .dm_memory import DMMemory
                self.memory = DMMemory(self.session_id)
            except ImportError:
                pass  # ChromaDB not installed - degrade gracefully

        # Initialize entity relationship graph (Neo4j)
        self.entity_graph = None
        try:
            from .entity_graph import EntityGraph
            self.entity_graph = EntityGraph()
        except Exception:
            pass  # Neo4j not available - degrade gracefully

        # Sanity system will be initialized in create_game()
        self.sanity_system = None

        # Location state manager for dynamic world
        try:
            from .location_state import LocationStateManager
            self.location_state = LocationStateManager()
        except ImportError:
            self.location_state = None

        # Companion system for ally mechanics
        try:
            from .companion_system import CompanionManager
            self.companions = CompanionManager()
        except ImportError:
            self.companions = None

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
            npcs_talked_to={},
            last_roll=None,
            npc_reputation={}
        )

        # Initialize entity relationships if graph is available
        if self.entity_graph and self.entity_graph.enabled:
            self._initialize_cthulhu_entities()

        # Initialize sanity system
        from .sanity_system import SanitySystem
        self.sanity_system = SanitySystem(investigator)

        # Initialize location state system
        if self.location_state:
            self._initialize_cthulhu_locations()

        return self.state

    def _initialize_cthulhu_entities(self):
        """Bootstrap Cthulhu-specific entities and relationships into Neo4j"""
        if not self.entity_graph or not self.entity_graph.enabled:
            return

        try:
            # Clear previous data
            self.entity_graph.clear()

            # Add factions
            self.entity_graph.add_faction("coast_guard", "U.S. Coast Guard", "neutral")
            self.entity_graph.add_faction("miskatonic", "Miskatonic University", "neutral")
            self.entity_graph.add_faction("cultists", "Deep One Cultists", "hostile")

            # Add NPCs (from NPC_DEFINITIONS)
            for npc_key, npc_data in self.NPC_DEFINITIONS.items():
                self.entity_graph.add_npc(
                    npc_key,
                    npc_data["name"],
                    npc_data["role"]
                )

            # Add specific relationships
            self.entity_graph.add_relationship("warner", "WORKS_FOR", "coast_guard")
            self.entity_graph.add_relationship("armitage", "WORKS_FOR", "miskatonic")
            self.entity_graph.add_relationship("warner", "KNOWS", "armitage")

            # Add locations
            self.entity_graph.add_location(
                "lighthouse_exterior",
                "Point Black Lighthouse - Exterior",
                "A weathered lighthouse stands on black rock..."
            )
            self.entity_graph.add_location(
                "keeper_quarters",
                "Keeper's Quarters",
                "The keeper's sparse living space..."
            )

            # Add protections
            self.entity_graph.add_relationship("warner", "PROTECTS", "lighthouse_exterior")

        except Exception as e:
            # Gracefully handle entity initialization errors
            pass

    def _initialize_cthulhu_locations(self):
        """Bootstrap Cthulhu-specific locations with descriptions"""
        if not self.location_state:
            return

        try:
            # Register main locations
            self.location_state.register_location(
                "lighthouse_exterior",
                "Point Black Lighthouse - Exterior",
                "A weathered lighthouse stands on rocky black stone, its paint peeling from decades of exposure to salt spray and Atlantic winds. The structure is perhaps thirty feet tall, surrounded by a low stone wall. The keeper's cottage sits nearby, its windows dark and empty."
            )

            self.location_state.register_location(
                "keeper_quarters",
                "Keeper's Quarters",
                "The keeper's sparse living space: a cot, a table with a single chair, shelves of maritime equipment. Everything is covered in dust. Through the single window, you can see the lighthouse. There's a faint smell of decay and something else—something chemical."
            )

            self.location_state.register_location(
                "lighthouse_interior",
                "Lighthouse Interior",
                "The interior of the lighthouse is a spiral of iron stairs ascending into darkness. The air is thick and stale. Each step groans under your weight. The walls are covered in moisture and a strange luminescent fungus that glows faintly green in the darkness."
            )

            self.location_state.register_location(
                "keeper_room_top",
                "Keeper's Room - Lighthouse Top",
                "At the top of the lighthouse, a small room contains a cot, desk, and the great lamp mechanism. Papers are scattered everywhere—logbooks, journals, sketches of impossible symbols. The light mechanism hasn't been lit in weeks. Through the windows, you can see the entire rocky coast and far out to sea."
            )

        except Exception:
            # Gracefully handle location initialization errors
            pass

    def _call_ollama(self, prompt: str, max_tokens: int = 200, on_chunk=None) -> str:
        """
        Call Ollama using /api/chat with message history (not stateless generate).
        This maintains conversation context for better narrative coherence.

        Improvements:
        - Temperature 0.5 (less hallucination than 0.7)
        - Max tokens reduced to 180 (avoid rambling)
        - Uses /api/chat for true conversation history
        - Retry logic on failure
        """
        from .adventure_context import AdventureContext

        for attempt in range(2):  # Try twice
            try:
                # Build messages with adventure context + history
                system_prompt = AdventureContext.build_system_prompt(
                    location=self.state.location,
                    game_phase=self.state.game_phase
                )

                # Build message history from narrative (alternating user/assistant)
                message_history = AdventureContext.build_message_history(
                    self.state.narrative,
                    max_messages=15  # Keep sliding window of last 15 turns
                )

                # Add current action as user message
                message_history.append({
                    "role": "user",
                    "content": prompt
                })

                # Call /api/chat with message history
                response = requests.post(
                    f"{self.ollama_endpoint}/api/chat",
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "messages": message_history,
                        "stream": True,
                        "temperature": 0.5,  # IMPROVEMENT: Reduced from 0.7
                        "num_predict": max_tokens  # Uses 180 default instead of 200
                    },
                    timeout=120,
                    stream=True
                )
                response.raise_for_status()

                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            text = chunk.get("message", {}).get("content", "")
                            full_response += text

                            # Call callback to stream text to UI
                            if on_chunk and text:
                                on_chunk(text)
                        except json.JSONDecodeError:
                            continue

                return full_response.strip() if full_response.strip() else "You pause, thinking..."

            except (requests.Timeout, requests.ConnectionError) as e:
                if attempt == 0:
                    # First failure - retry
                    import time
                    time.sleep(0.5)
                    continue
                # Second failure - fallback narrative
                return "The world around you seems to pause. You take a moment to collect yourself and continue your investigation."
            except Exception as e:
                if attempt == 0:
                    continue
                # Generic error fallback
                return "Something feels wrong. You steady yourself and push forward."

        return "You take a deep breath and continue."

    def _format_last_roll_info(self) -> str:
        """Format last roll information for DM prompt"""
        if not self.state.last_roll:
            return "None yet"

        roll = self.state.last_roll
        if roll['success']:
            return f"✓ SUCCESS - {roll['skill']} {roll['difficulty']}: Rolled {roll['roll']} vs {roll['target']}"
        else:
            return f"✗ FAILURE - {roll['skill']} {roll['difficulty']}: Rolled {roll['roll']} vs {roll['target']} (APPLY CONSEQUENCES)"

    def _get_location_context_for_prompt(self) -> str:
        """Get location state context for DM prompt"""
        if not self.location_state:
            return ""

        context = self.location_state.get_location_context(self.state.location)
        if context:
            return f"{context}\n"
        return ""

    def _build_dm_system_prompt(self) -> str:
        """
        Build system prompt for DM role with Call of Cthulhu 7e rules.
        Used for both regular prompts and tool calling mode.
        """
        inv = self.state.investigator

        return f"""You are the Dungeon Master for Call of Cthulhu 7th Edition.

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
{self._get_location_context_for_prompt()}Turn: {self.state.turn}
Phase: {self.state.game_phase}
Combat: {'In combat with ' + self.state.active_combat['name'] if self.state.active_combat else 'None'}

Last Roll Status:
{self._format_last_roll_info()}

=== CONSEQUENCE MATRIX ===

WHEN A ROLL FAILS (roll > target), apply proportional consequences:

CLIMB/SWIM FAILURE:
  - Moderate fail (just missed): slip, no damage, restart attempt
  - Bad fail (far missed): fall! [HP_DAMAGE: 1d4] (~2-4 damage)
  - Critical fail (96+): serious fall [HP_DAMAGE: 1d6] (~3-6 damage)

DODGE FAILURE:
  - In combat: enemy connects with attack [HP_DAMAGE: enemy_damage]
  - Hazard: take environmental damage [HP_DAMAGE: varies]

FIGHT/FIREARMS FAILURE:
  - Miss the target
  - Enemy counter-attacks next round

INVESTIGATION/OCCULT FAILURE:
  - Miss important clue
  - Misinterpret evidence (follow false lead)
  - If examining cursed object: [SANITY_CHECK: 1-3]

PERSUADE FAILURE:
  - NPC refuses or becomes hostile
  - May lead to combat

=== YOUR RESPONSE ===

**RESPOND ACCORDING TO LAST ROLL STATUS** (shown above):

🚨 CRITICAL RULES (MUST FOLLOW):
1. ONE ROLL TAG MAXIMUM - If you output [ROLL:], do it ONCE only. Never [ROLL: climb/normal] AND [ROLL: climb/hard]. Pick ONE.
2. ONE RESPONSE = ONE ACTION - Never mix multiple actions or decisions
3. NO TEMPLATE TEXT - Do NOT output: headers, "IF/ELSE", conditionals, section breaks (---), numbered lists
4. SHORT AND FOCUSED - Keep narrative to 2-4 sentences max
5. NO VISIBLE DECISION MAKING - Just tell the story, don't show your reasoning

YOUR JOB DEPENDS ON LAST ROLL STATUS:

🎯 STATUS: "None yet" (no pending roll)
  - Respond to the player's action naturally (1-2 sentences)
  - If the action is dangerous/risky/requires a skill check:
    → END with exactly: [ROLL: skill/difficulty]
    → STOP. Do not describe what happens next.
  - If action is routine (walking, talking, looking casually):
    → Continue the story (1-2 more sentences)
    → Only END with a tag if player finds something: [ITEM_FOUND: key]
    → Or if they trigger combat: [COMBAT_START: enemy_key]
    → Or if they witness horror: [SANITY_CHECK: damage]
    → Or if they take environmental damage: [HP_DAMAGE: damage]

🎯 STATUS: "✓ SUCCESS" (player succeeded a roll)
  - Describe ONLY the positive outcome of their success
  - Show what they accomplish (1-2 vivid sentences)
  - Example: "You grip the ledge and haul yourself through. Inside, the keeper's quarters stretch before you in darkness."
  - Then you MAY describe the next challenge/discovery (1-2 more sentences)
  - NO new roll requests in this response
  - NO repeating the setup

🎯 STATUS: "✗ FAILURE" (player failed a roll)
  - Describe ONLY the negative outcome of their failure
  - Show what goes wrong (1-2 vivid sentences)
  - Apply consequences with tags if appropriate:
    → Physical failures (climb, dodge, fight): add [HP_DAMAGE: 2-4]
    → Mental failures (occult, investigation): add [SANITY_CHECK: 1-2]
  - Example: "Your foot slips on the wet stone. You tumble down, crashing hard."
  - Then you MAY describe what comes next (1-2 more sentences)
  - NO new roll requests in this response
  - NO repeating the setup

DO NOT output template text. Do not show IF/ELSE logic. Just tell the story.
"""

    def _build_dm_prompt(self, player_action: str) -> str:
        """
        Build DM prompt with:
        - Adventure context (global + endings guidance)
        - Current game state
        - Semantic memory for facts
        - Strong location pinning to prevent hallucinations
        - Constraints to maintain narrative coherence
        """
        from .adventure_context import AdventureContext

        # Build narrative context from memory
        if self.memory and self.memory.enabled:
            semantic_hits = self.memory.query_relevant_facts(player_action, n=5)
            recent = self.state.narrative[-3:]  # Increased from 2 to 3
            seen = set(recent)
            extra = [h for h in semantic_hits if h not in seen]
            narrative_context = "\n".join(recent + extra[:5])
        else:
            narrative_context = "\n".join(self.state.narrative[-5:])

        # Build current game state context
        state_context = AdventureContext.build_current_state_prompt(
            investigator_name=self.state.investigator.name,
            location=self.state.location,
            hp=self.state.investigator.characteristics['HP'],
            max_hp=self.state.investigator.characteristics.get('max_hp', 14),
            san=self.state.investigator.characteristics['SAN'],
            max_san=self.state.investigator.characteristics.get('max_san', 99),
            inventory=self.state.investigator.inventory,
            discoveries=[d for d in self.state.narrative if "discover" in d.lower()][:5],
            companions_alive=len(getattr(self, 'companion_manager', None) and
                                self.companion_manager.get_active_companions() or []),
            turn=self.state.turn
        )

        # Location-specific sensory details - IMPROVED
        location_details = {
            "Point Black Lighthouse - Exterior": "salt-air smell, dark rocks, crashing waves, fog, lighthouse tower visible above",
            "Lighthouse Interior": "damp stone walls, spiral iron stairs, salt smell, cold stone, strange luminescent fungus glowing faintly green",
            "Keeper's Quarters": "sparse furniture, dust, faded pictures on walls, musty air, old maritime books, personal effects, chemical smell",
            "Lighthouse Stairs": "spiral stone stairs groaning underfoot, flickering light from above, salt smell, echoing sounds, fungus on walls",
            "Lantern Room": "bright beacon light, wide windows with ocean view, mechanical gears, heat from lamp, scattered papers with symbols",
            "Ground Floor": "solid stone floor, damp smell, darkness beyond flashlight range, echoing sounds, metal door",
            "Upper Level": "narrow passages, low ceilings, damp air, distant sounds, old wood fixtures creaking",
        }

        sensory_grounding = location_details.get(self.state.location, "You are still in the lighthouse, with its damp stone walls.")

        # IMPROVED: Stronger location pinning (mentioned 3 times in prompt for emphasis)
        location_constraint = f"""
CRITICAL - LOCATION ANCHOR:
1. You are ONLY in: {self.state.location}
2. Sensory details of this location: {sensory_grounding}
3. Do NOT suddenly shift locations without player requesting it and a transition
4. Do NOT introduce areas (crypts, caves, dungeons, forests, buildings) not mentioned
5. Do NOT create enemies/guards that weren't established in previous narrative
6. Stay grounded in THIS PLACE with its details

If the player tries to leave, describe the TRANSITION first.
"""

        prompt = f"""
{location_constraint}

{state_context}

Recent narrative:
{narrative_context}

=== PLAYER ACTION THIS TURN ===
{player_action}

Respond with the IMMEDIATE narrative outcome of this action. Stay in location.
"""
        return prompt

    def _call_ollama_with_tools(self, narrative_context: str, player_action: str) -> Dict:
        """
        Call Ollama /api/chat with tool calling support.
        Only used for models that support tools (mistral, neural-chat, qwen3:8b).

        Args:
            narrative_context: Game context and rules
            player_action: Current player action

        Returns:
            Dict with "narrative" and "tool_calls" keys, or fallback dict with "fallback": True
        """
        from .cthulhu_tools import CTHULHU_TOOLS

        system_prompt = self._build_dm_system_prompt()

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Recent story:\n{narrative_context}\n\n=== PLAYER ACTION ===\n{player_action}"
            }
        ]

        try:
            response = requests.post(
                f"{self.ollama_endpoint}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "tools": CTHULHU_TOOLS,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 300
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            message = data.get("message", {})

            return {
                "narrative": message.get("content", ""),
                "tool_calls": message.get("tool_calls", [])
            }
        except Exception as e:
            # Fallback to tag-based system on any tool calling failure
            return {"narrative": "", "tool_calls": [], "fallback": True}

    def _execute_tool_calls(self, tool_calls: list) -> Dict:
        """
        Execute tool calls returned by LLM and return structured results.

        Args:
            tool_calls: List of tool call dictionaries from LLM

        Returns:
            Dict with keys like "rolls_requested", "sanity_checks", etc.
        """
        results = {
            "rolls_requested": [],
            "sanity_checks": [],
            "hp_damage": [],
            "items_found": [],
            "combat_start": []
        }

        for call in tool_calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            args = fn.get("arguments", {})

            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except:
                    continue

            if name == "roll_skill_check":
                skill = args.get("skill", "unknown")
                difficulty = args.get("difficulty", "Normal")
                results["rolls_requested"].append((skill, difficulty))

            elif name == "apply_sanity_damage":
                damage = args.get("damage", 1)
                results["sanity_checks"].append(str(damage))

            elif name == "apply_hp_damage":
                damage = args.get("damage", 1)
                results["hp_damage"].append(str(damage))

            elif name == "pickup_item":
                item_key = args.get("item_key", "")
                results["items_found"].append(item_key)

            elif name == "start_combat":
                enemy_key = args.get("enemy_key", "")
                results["combat_start"].append(enemy_key)

        return results

    def process_player_action(self, player_input: str, on_chunk=None) -> Dict:
        """
        Process player action and get DM response.
        Returns DM narrative + any requested rolls/sanity checks/items/combat.

        Supports both tool calling (for capable models) and tag-based parsing (fallback).

        Args:
            player_input: What the player does
            on_chunk: Optional callback function for streaming text chunks
        """
        if not self.state:
            return {"error": "No active game"}

        from .cthulhu_tools import TOOL_CAPABLE_MODELS

        # Try tool calling for capable models
        rolls_requested = []
        sanity_checks = []
        items_found = []
        hp_damage = []
        combat_start = []
        npc_dialogue = []
        clean_response = ""

        if self.model in TOOL_CAPABLE_MODELS:
            # Build narrative context for tool calling
            if self.memory and self.memory.enabled:
                semantic_hits = self.memory.query_relevant_facts(player_input, n=5)
                recent = self.state.narrative[-2:]
                seen = set(recent)
                extra = [h for h in semantic_hits if h not in seen]
                narrative_context = "\n".join(recent + extra[:5])
            else:
                narrative_context = "\n".join(self.state.narrative[-5:])

            # Attempt tool calling
            tool_response = self._call_ollama_with_tools(narrative_context, player_input)

            if not tool_response.get("fallback"):
                # Tool calling succeeded - get narrative and execute tools
                clean_response = tool_response.get("narrative", "")

                # Print narrative if streaming callback is provided
                if on_chunk and clean_response:
                    on_chunk(clean_response)

                # Execute tool calls
                tool_results = self._execute_tool_calls(tool_response.get("tool_calls", []))
                rolls_requested = tool_results.get("rolls_requested", [])
                sanity_checks = tool_results.get("sanity_checks", [])
                items_found = tool_results.get("items_found", [])
                hp_damage = tool_results.get("hp_damage", [])
                combat_start = tool_results.get("combat_start", [])

                # Tool calling complete - proceed to state update
            else:
                # Tool calling failed or returned empty - fall back to tag-based system
                dm_prompt = self._build_dm_prompt(player_input)
                dm_response = self._call_ollama(dm_prompt, on_chunk=on_chunk)

                # Parse tag-based response
                rolls_requested = re.findall(r'\[ROLL: (\w+)/(\w+)\]', dm_response)
                sanity_checks = re.findall(r'\[SANITY_CHECK: (\d+)\]', dm_response)
                items_found = re.findall(r'\[ITEM_FOUND: (\w+)\]', dm_response)
                hp_damage = re.findall(r'\[HP_DAMAGE: (\d+)\]', dm_response)
                combat_start = re.findall(r'\[COMBAT_START: (\w+)\]', dm_response)
                npc_dialogue = re.findall(r'\[NPC_DIALOGUE: (\w+)\]', dm_response)

                # Clean response
                clean_response = re.sub(r'\[ROLL: .*?\]', '', dm_response)
                clean_response = re.sub(r'\[SANITY_CHECK: .*?\]', '', clean_response)
                clean_response = re.sub(r'\[ITEM_FOUND: .*?\]', '', clean_response)
                clean_response = re.sub(r'\[HP_DAMAGE: .*?\]', '', clean_response)
                clean_response = re.sub(r'\[COMBAT_START: .*?\]', '', clean_response)
                clean_response = re.sub(r'\[NPC_DIALOGUE: .*?\]', '', clean_response)
        else:
            # Model doesn't support tool calling - use tag-based system
            # Get DM response with optional streaming
            dm_prompt = self._build_dm_prompt(player_input)
            dm_response = self._call_ollama(dm_prompt, on_chunk=on_chunk)

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

        # Persist narrative fragments to semantic memory (uses mem0ai for fact extraction if available)
        if self.memory and self.memory.enabled:
            self.memory.extract_and_store(
                f"Player: {player_input}",
                self.state.turn,
                {"location": self.state.location, "phase": self.state.game_phase, "speaker": "Player"}
            )
            self.memory.extract_and_store(
                f"DM: {clean_response}",
                self.state.turn,
                {"location": self.state.location, "phase": self.state.game_phase, "speaker": "DM"}
            )

        self.state.turn += 1

        # Update sanity system (reduce disorder durations, etc.)
        self.update_sanity_system()

        # Auto-detect location changes from narrative
        narrative_lower = clean_response.lower()
        location_map = {
            'keeper': 'Keeper\'s Quarters',
            'chamber': 'Hidden Chamber',
            'basement': 'Basement',
            'roof': 'Lighthouse Top',
            'stairs': 'Lighthouse Stairs',
            'lantern room': 'Lantern Room',
            'ground floor': 'Ground Floor',
            'upper level': 'Upper Level',
            'interior': 'Lighthouse Interior',
            'inside': 'Lighthouse Interior',
        }
        for keyword, new_location in location_map.items():
            if keyword in narrative_lower and new_location != self.state.location:
                self.state.location = new_location
                break

        # If a new roll is requested, clear the previous roll record
        # (DM has now responded to the consequences)
        if rolls_requested:
            self.state.last_roll = None

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

        # Track this roll for next DM turn (so it can apply consequences)
        self.state.last_roll = {
            "skill": skill,
            "difficulty": difficulty,
            "success": result['success'],
            "roll": result['roll'],
            "target": result['target'],
            "message": result['message']
        }

        # Log in narrative
        self.state.narrative.append(f"[ROLL: {result['message']}]")

        return result

    def apply_sanity_check(self, damage: int, source: str = "unknown") -> Dict:
        """
        Apply sanity damage from witnessing horror.
        Uses enhanced sanity system with breaking points and disorders.

        Args:
            damage: Sanity points to lose
            source: What caused the damage (for narrative context)

        Returns:
            Dict with sanity results and any breaking points/disorders
        """
        if not self.state or not self.sanity_system:
            return {"error": "No active game"}

        # Apply damage through enhanced sanity system
        result = self.sanity_system.apply_sanity_damage(damage, source)

        # Record in narrative
        self.state.investigator.sanity_breaks.append(
            f"Turn {self.state.turn}: Lost {damage} SAN ({source})"
        )

        # If breaking point occurred, add narrative context
        if result.get("broke"):
            self.state.narrative.append(f"[SANITY BREAK: {result['narrative']}]")

            # If disorder created, record it for future reference
            if result.get("temporary_insanity"):
                disorder = result["temporary_insanity"]
                self.state.narrative.append(
                    f"[TEMPORARY INSANITY: {disorder.type} will last {disorder.duration} turns]"
                )

            if result.get("permanent_disorder"):
                disorder = result["permanent_disorder"]
                self.state.narrative.append(
                    f"[PERMANENT DISORDER: {disorder.type} - affecting investigator indefinitely]"
                )

        return result

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

    def get_sanity_status(self) -> Dict:
        """
        Get comprehensive sanity status for the investigator.

        Returns:
            Dict with current sanity, level, disorders, etc.
        """
        if not self.state or not self.sanity_system:
            return {"error": "No active game"}

        return self.sanity_system.get_sanity_status()

    def update_sanity_system(self) -> None:
        """
        Called each turn to update sanity system state.
        Reduces disorder durations, converts temporary to permanent if needed.
        """
        if not self.sanity_system:
            return

        # Update disorder durations
        changed_disorders = self.sanity_system.reduce_disorder_duration()

        # Record changes in narrative
        for disorder in changed_disorders:
            if disorder.duration == 0:
                self.state.narrative.append(f"[DISORDER RESOLVED: {disorder.type} has passed]")
            elif disorder.duration == -1:
                self.state.narrative.append(f"[DISORDER PERMANENT: {disorder.type} is now permanent]")

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

    def resolve_roll_consequences(self, on_chunk=None) -> Dict:
        """
        After a roll is made, automatically generate DM narrative
        describing the consequences (success or failure).
        Called after execute_skill_check().
        """
        if not self.state or not self.state.last_roll:
            return {"error": "No pending roll"}

        roll = self.state.last_roll

        # Build a simple, direct prompt
        if roll['success']:
            consequence_prompt = f"""You are the Dungeon Master.

The player SUCCEEDED at: {roll['skill']} (rolled {roll['roll']} vs {roll['target']})

Describe in 2-3 sentences what the player accomplished. What does success look like?
Be vivid and advance the story.
NO NEW ROLLS. NO TAGS. Just the outcome."""
        else:
            consequence_prompt = f"""You are the Dungeon Master.

The player FAILED at: {roll['skill']} (rolled {roll['roll']} vs {roll['target']})

Describe in 2-3 sentences what went wrong. Add consequences if appropriate.
For physical failure (climb, dodge, fight), add: [HP_DAMAGE: 2-4]
For mental failure (occult, investigation), add: [SANITY_CHECK: 1-2]
NO NEW ROLLS. Just the outcome."""

        # Get DM response for the consequence
        consequence_response = self._call_ollama(consequence_prompt, max_tokens=100, on_chunk=on_chunk)

        # Parse any tags that might be in the consequence
        hp_damage = re.findall(r'\[HP_DAMAGE: (\d+)\]', consequence_response)
        sanity_checks = re.findall(r'\[SANITY_CHECK: (\d+)\]', consequence_response)

        # Clean the response
        clean_response = re.sub(r'\[HP_DAMAGE: .*?\]', '', consequence_response)
        clean_response = re.sub(r'\[SANITY_CHECK: .*?\]', '', clean_response)

        # Update narrative
        self.state.narrative.append(f"DM: {clean_response}")

        # Apply any damage/sanity from the consequence
        for damage in hp_damage:
            self.apply_hp_damage(int(damage))
        for damage in sanity_checks:
            self.apply_sanity_check(int(damage))

        # Clear the roll from pending
        self.state.last_roll = None

        return {
            "narrative": clean_response,
            "hp_damage": hp_damage,
            "sanity_checks": sanity_checks,
            "success": roll['success']
        }

    def talk_to_npc(self, npc_key: str, player_question: str) -> str:
        """Have NPC respond to player with memory of past interactions and reputation system"""
        if npc_key not in self.NPC_DEFINITIONS:
            return f"That person isn't here."

        npc = self.NPC_DEFINITIONS[npc_key]

        # Get current reputation score and attitude label
        if npc_key not in self.state.npc_reputation:
            self.state.npc_reputation[npc_key] = 0
        rep_score = self.state.npc_reputation[npc_key]
        attitude = self._reputation_label(rep_score)

        # Track conversation
        if npc_key not in self.state.npcs_talked_to:
            self.state.npcs_talked_to[npc_key] = []
        self.state.npcs_talked_to[npc_key].append(player_question)

        # Retrieve relevant past interactions with this NPC from semantic memory
        npc_history_context = ""
        if self.memory and self.memory.enabled:
            past_interactions = self.memory.query_npc_history(npc_key, player_question, n_results=3)
            if past_interactions:
                npc_history_context = "\nPrevious topics discussed:\n" + "\n".join(past_interactions)

        # Retrieve entity relationships (who they know, who they work for, what they fear)
        entity_context = ""
        if self.entity_graph and self.entity_graph.enabled:
            entity_context_str = self.entity_graph.get_npc_context(npc_key)
            if entity_context_str:
                entity_context = f"\nKnown associations: {entity_context_str}"

        # Determine what the NPC reveals based on reputation
        known_info = npc['knows']
        if rep_score > 50 and 'knows_secret' in npc:
            # Reveal secrets only to trusted allies
            known_info = known_info + npc['knows_secret']

        # Build NPC prompt with reputation context
        prompt = f"""You are {npc['name']}, a {npc['role']}.

Personality: {npc['personality']}

Your attitude toward this person is: {attitude}
(hostile = distrustful, minimal info; neutral = standard responses; friendly = helpful, friendly tone; trusted = reveals secrets and deeper knowledge)

You know about: {', '.join(known_info)}{entity_context}{npc_history_context}

The player asks: "{player_question}"

Respond in character, in 2-3 sentences. Be dramatic, mysterious, and atmospheric. Reference what you know if relevant. Let your attitude shape how much you reveal."""

        # Get NPC response
        response = self._call_ollama(prompt, max_tokens=100)

        # Update reputation: friendly/helpful interaction = +5, neutral = no change
        # This is a simple heuristic - in a fuller system we'd parse the response
        if "help" in response.lower() or "certainly" in response.lower() or "of course" in response.lower():
            self.update_npc_reputation(npc_key, 5, "friendly interaction")
        elif "refuse" in response.lower() or "won't" in response.lower():
            self.update_npc_reputation(npc_key, -5, "refused to help")

        # Persist interaction to semantic memory
        if self.memory and self.memory.enabled:
            self.memory.add_npc_interaction(npc_key, player_question, response, self.state.turn)

        # Show reputation status to player
        rep_indicator = f" [Reputation: {rep_score:+3d}]"
        return f"{npc['name']}: {response}{rep_indicator}"

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

    def update_npc_reputation(self, npc_key: str, delta: int, reason: str = "") -> int:
        """
        Update reputation with an NPC.

        Args:
            npc_key: NPC identifier (e.g., 'warner', 'armitage')
            delta: Change in reputation (positive = friendlier, negative = hostile)
            reason: Optional reason for the change (for logging)

        Returns:
            New reputation score (clamped to [-100, 100])
        """
        if npc_key not in self.state.npc_reputation:
            self.state.npc_reputation[npc_key] = 0

        old_rep = self.state.npc_reputation[npc_key]
        new_rep = max(-100, min(100, old_rep + delta))
        self.state.npc_reputation[npc_key] = new_rep

        return new_rep

    @staticmethod
    def _reputation_label(score: int) -> str:
        """Convert reputation score to NPC attitude label"""
        if score < -50:
            return "hostile"
        elif score < 0:
            return "distrustful"
        elif score < 50:
            return "neutral"
        elif score < 75:
            return "friendly"
        else:
            return "trusted"

    def get_ending_text(self) -> Optional[str]:
        """Get narrative for current ending"""
        if not self.state.ending_reached:
            return None

        ending = self.ENDINGS.get(self.state.ending_reached)
        if ending:
            return f"\n{ending['name'].upper()}\n{ending['description']}"

        return None

    def save_game(self) -> str:
        """
        Save current game session to disk with all state.

        Returns:
            Path to saved file
        """
        from .generative_save import GenerativeSave

        path = GenerativeSave.save(
            self.state,
            self.session_id,
            self.model,
            location_state=self.location_state,
            sanity_system=self.sanity_system
        )

        # Also persist ChromaDB memory if available
        if self.memory and self.memory.enabled:
            self.memory.persist()

        return path

    @classmethod
    def load_game(cls, session_id: str,
                  ollama_endpoint: str = "http://localhost:11434") -> 'GenerativeGameEngine':
        """
        Load a saved game session from disk.

        Args:
            session_id: Unique session identifier
            ollama_endpoint: Ollama endpoint URL

        Returns:
            Reconstructed GenerativeGameEngine instance

        Raises:
            FileNotFoundError: If save doesn't exist
        """
        from .generative_save import GenerativeSave
        from .location_state import LocationStateManager
        from .sanity_system import SanitySystem

        metadata, state_dict, location_state_data = GenerativeSave.load(session_id)

        # Reconstruct InvestigatorState from dictionary
        inv_dict = state_dict["investigator"]
        investigator = InvestigatorState(
            name=inv_dict["name"],
            occupation=inv_dict["occupation"],
            characteristics=inv_dict["characteristics"],
            skills=inv_dict["skills"],
            inventory=inv_dict["inventory"],
            visited_locations=inv_dict["visited_locations"],
            sanity_breaks=inv_dict["sanity_breaks"]
        )

        # Reconstruct GameState from dictionary
        state = GameState(
            turn=state_dict["turn"],
            location=state_dict["location"],
            narrative=state_dict["narrative"],
            investigator=investigator,
            recent_actions=state_dict["recent_actions"],
            game_phase=state_dict["game_phase"],
            victory_condition=state_dict.get("victory_condition"),
            ending_reached=state_dict.get("ending_reached"),
            ending_narrative=state_dict.get("ending_narrative"),
            active_combat=state_dict.get("active_combat"),
            npcs_talked_to=state_dict.get("npcs_talked_to", {}),
            npc_reputation=state_dict.get("npc_reputation", {}),
            last_roll=state_dict.get("last_roll")
        )

        # Create engine instance with same model and session
        engine = cls(
            ollama_endpoint=ollama_endpoint,
            model=metadata["model"],
            session_id=session_id,
            use_memory=True
        )

        # Inject the loaded state
        engine.state = state

        # Restore location state if available
        if location_state_data:
            try:
                engine.location_state = LocationStateManager.from_dict(location_state_data)
            except Exception:
                pass  # Location state restoration failed, continue with default

        # Reinitialize sanity system from loaded state
        try:
            engine.sanity_system = SanitySystem(investigator)
        except Exception:
            pass  # Sanity system restoration failed

        return engine
