#!/usr/bin/env python3
"""
Adventure Context Builder
Loads complete story context and creates guided prompts
Used by DM to maintain narrative coherence without being rigid
"""

from typing import Dict, List


class AdventureContext:
    """Loads and manages complete adventure context"""

    ADVENTURE_DESCRIPTION = """
═══════════════════════════════════════════════════════════════════════════════
ALONE AGAINST THE DARK - Point Black Lighthouse Adventure
═══════════════════════════════════════════════════════════════════════════════

SETTING:
You are at Point Black Lighthouse on the remote Maine coast. The lighthouse
stands on black rock, surrounded by crashing Atlantic waves and fog. A keeper
vanished 2 weeks ago under mysterious circumstances.

THE MYSTERY:
- The lighthouse keeper disappeared without explanation
- His final logbook entries became increasingly erratic: "They call from below"
- Strange sounds heard at night from the ocean
- Evidence of a pre-human fissure beneath the lighthouse
- Symbols cover the keeper's quarters - alien geometry that hurts to look at
- The lighthouse may have been built to CONTAIN something, not protect FROM it

KEY LOCATIONS:
- Lighthouse Exterior: Rocky black stone, salt spray, fog, weathered structure
- Keeper's Quarters: Sparse furniture, dust, decay smell, chemical odor
- Lighthouse Interior: Spiral stairs, damp, strange luminescent fungus (glow green)
- Lantern Room: Top of lighthouse, beacon lamp, ancient symbols, wide ocean view
- Ground Floor: Solid stone, darkness, echoing sounds
- Lighthouse Stairs: Iron spiral, flickering light, salt smell

KEY CHARACTERS:
- Lieutenant Warner (Coast Guard) - Knows keeper vanished, organized search
- Dr. Armitage (Professor) - Expert on pre-human symbols, ancient languages
- Chief Marsh (Police Chief) - Skeptical, pragmatic, wants mundane explanation

THE THREAT:
Something ancient lies beneath the ocean. It may be waking. The lighthouse
has contained it for centuries, but something has changed. The fissure is
becoming active. Reality is becoming thin around this place.

YOUR OBJECTIVE:
Uncover what happened to the keeper. Understand the nature of the threat.
Decide: Escape? Seal the fissure? Destroy the lighthouse? Confront the entity?
═══════════════════════════════════════════════════════════════════════════════
"""

    ENDINGS_GUIDANCE = """
═══════════════════════════════════════════════════════════════════════════════
POSSIBLE ENDINGS - Guide for Narrative Direction
═══════════════════════════════════════════════════════════════════════════════

These are possible outcomes. The player's choices, sanity, and discoveries
determine which ending they reach. Be flexible - all are valid based on their
actions and stats.

1. TRIUMPH THROUGH SACRIFICE
   - Condition: Uncover truth + stop the threat + companions survive
   - Narrative: They succeed against cosmic horror through courage
   - Stats: SAN ≥ 50, HP ≥ 10, discoveries ≥ 5, companions alive

2. PYRRHIC VICTORY
   - Condition: Stop threat but lose companions/sanity
   - Narrative: Victory tastes hollow - they saved the world but lost loved ones
   - Stats: Completed objective but companions dead OR sanity < 30

3. KNOWLEDGE CURSE
   - Condition: Survive but know too much
   - Narrative: They escape but carry burden of forbidden knowledge
   - Stats: SAN 30-50, discover the truth, escape alive but haunted

4. ISOLATION
   - Condition: Survive alone, separated from companions
   - Narrative: Survivor guilt and loneliness plague them
   - Stats: Alone, SAN ≥ 30, many turns passed

5. MADNESS
   - Condition: Sanity completely breaks
   - Narrative: Mind shattered by cosmic horror, admitted to asylum
   - Stats: SAN < 15, witnessed too much

6. BROKEN SURVIVOR
   - Condition: Escape but deeply damaged
   - Narrative: PTSD and trauma define their future
   - Stats: SAN < 30, companions dead, escape somehow

7. TRANSFORMATION
   - Condition: Encounter entity but transcend humanity
   - Narrative: Changed fundamentally by contact with the alien
   - Stats: Contact entity, SAN ≥ 30, become something more/less than human

8. HOLLOW VICTORY
   - Condition: Win technically but victory feels empty
   - Narrative: Society ignores truth, they're alone with knowledge
   - Stats: Threat stopped, intact sanity, but disconnected from normal world

═══════════════════════════════════════════════════════════════════════════════
YOUR ROLE AS DM:

- Guide gently toward these endings based on PLAYER ACTIONS, not prewritten plot
- High sanity + good discoveries → Triumph path
- Sanity breaks + companion deaths → darker paths
- Complete isolation → Isolation ending
- Let player choices determine direction
- Be flexible: multiple paths to same ending
- Never force an ending - let it emerge from the story
═══════════════════════════════════════════════════════════════════════════════
"""

    CONSTRAINTS = """
═══════════════════════════════════════════════════════════════════════════════
CRITICAL CONSTRAINTS FOR NARRATIVE COHERENCE
═══════════════════════════════════════════════════════════════════════════════

LOCATION STABILITY:
- Current location is YOUR ONLY setting reference
- DO NOT suddenly shift to crypts, caves, tombs, dungeons, forests, etc.
- DO NOT introduce locations that don't exist in the adventure
- If player wants to go elsewhere, describe transition first
- Include sensory details from current location in your description

CONTINUITY:
- DO NOT introduce enemies/guardians that weren't previously mentioned
- DO NOT have "guards" appear if no guards were established
- DO NOT create escapes from places that trap the player
- Reference previous discoveries and observations
- Remember what the player has seen and learned

CHARACTER CONSISTENCY:
- NPCs have fixed knowledge and personalities
- Warner: Coast Guard, pragmatic, doesn't believe in the supernatural
- Armitage: Scholar, believes in ancient threats, has library knowledge
- Marsh: Police chief, wants mundane explanations, protective
- DO NOT change NPC roles or relationships without reason

ATMOSPHERE:
- Maintain cosmic horror tone: uncertainty, dread, hints of vast alien presence
- Not slasher horror: focus on psychological/existential terror
- Not action-adventure: focus on investigation and discovery
- Let mystery unfold gradually through player actions

ACTION RESOLUTION:
- MANDATORY ROLLS: lift/push/pry/force, climb/jump/swim, attack/fight/shoot, search/examine/investigate
- Read ancient text, persuade/deceive, dodge/run from danger
- End roll requests with [ROLL: skill/difficulty] BEFORE describing outcome
- Describe outcome of skill checks (success or failure)
- Don't repeat information already established
- Advance the story with each narrative beat

═══════════════════════════════════════════════════════════════════════════════
"""

    @staticmethod
    def build_system_prompt(location: str, game_phase: str) -> str:
        """
        Build complete system prompt with all context layers.

        Args:
            location: Current location
            game_phase: Current phase (exploring, investigation, combat, climax, ending)

        Returns:
            Complete system prompt for LLM
        """
        system = f"""You are the Dungeon Master for a Call of Cthulhu horror investigation game.

{AdventureContext.ADVENTURE_DESCRIPTION}

{AdventureContext.ENDINGS_GUIDANCE}

{AdventureContext.CONSTRAINTS}

CURRENT SETTING: {location}
GAME PHASE: {game_phase}

Your job:
1. Respond to the player's action IN THE CURRENT LOCATION ONLY
2. Advance the story naturally based on their choices
3. Guide gently toward one of the 8 endings based on their sanity/discoveries
4. Maintain atmosphere of cosmic horror and uncertainty
5. Make every narrative beat count - don't repeat information

REMEMBER: You are NOT writing a fixed story. You are responding to THEIR choices.
The ending emerges from THEIR decisions, sanity, and discoveries. Be flexible."""

        return system

    @staticmethod
    def build_current_state_prompt(
        investigator_name: str,
        location: str,
        hp: int,
        max_hp: int,
        san: int,
        max_san: int,
        inventory: List[str],
        discoveries: List[str],
        companions_alive: int,
        turn: int
    ) -> str:
        """
        Build current game state context.

        Args:
            investigator_name: Player character name
            location: Current location
            hp: Current HP
            max_hp: Max HP
            san: Current sanity
            max_san: Max sanity
            inventory: Items carried
            discoveries: What they've learned
            companions_alive: Number of living companions
            turn: Current turn number

        Returns:
            Formatted current state for inclusion in message
        """
        state = f"""
CURRENT GAME STATE (Turn {turn}):
- Investigator: {investigator_name}
- Location: {location}
- HP: {hp}/{max_hp} | SAN: {san}/{max_san}
- Inventory: {', '.join(inventory) if inventory else 'empty'}
- Discoveries: {', '.join(discoveries) if discoveries else 'none yet'}
- Companions Alive: {companions_alive}
"""
        return state

    @staticmethod
    def build_message_history(narrative_turns: List[str], max_messages: int = 15) -> List[Dict]:
        """
        Build conversation history for /api/chat.
        Alternates between user (player) and assistant (DM) messages.

        Args:
            narrative_turns: List of narrative beats (alternating "Player: X" and "DM: Y")
            max_messages: Maximum messages to keep (window sliding)

        Returns:
            List of message dicts for /api/chat endpoint
        """
        messages = []

        # Take last N turns (sliding window to prevent infinite context)
        recent_turns = narrative_turns[-max_messages:]

        for turn in recent_turns:
            if turn.startswith("Player:"):
                messages.append({
                    "role": "user",
                    "content": turn.replace("Player: ", "").strip()
                })
            elif turn.startswith("DM:"):
                messages.append({
                    "role": "assistant",
                    "content": turn.replace("DM: ", "").strip()
                })

        return messages
