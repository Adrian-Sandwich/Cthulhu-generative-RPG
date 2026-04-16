#!/usr/bin/env python3
"""
Tool definitions for LLM tool calling in Cthulhu game engine.
Enables the DM to invoke game mechanics directly via structured function calls.
"""

# Tool calling support for models
TOOL_CAPABLE_MODELS = {"mistral", "neural-chat", "qwen3:8b"}

# Ollama tool calling schema for CoC 7e mechanics
CTHULHU_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "roll_skill_check",
            "description": "Request a skill check roll from the player. Use when action requires testing against a skill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill": {
                        "type": "string",
                        "description": "Skill name to check against: dodge, climb, jump, swim, listen, spot_hidden, investigate, persuade, intimidate, deceive, knowledge, library_use, history, science, occult, psychology, cthulhu_mythos, etc."
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["Normal", "Hard", "Extreme"],
                        "description": "Difficulty level: Normal (roll skill), Hard (roll half skill), Extreme (roll one-fifth skill)"
                    },
                    "context": {
                        "type": "string",
                        "description": "Narrative reason for this roll (optional)"
                    }
                },
                "required": ["skill", "difficulty"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_sanity_damage",
            "description": "Apply sanity damage from witnessing horror or reading forbidden knowledge.",
            "parameters": {
                "type": "object",
                "properties": {
                    "damage": {
                        "type": "integer",
                        "description": "Sanity points to lose (typically 1-10 for moderate horror, 1d6 for minor, 1d20 for major)"
                    },
                    "horror_description": {
                        "type": "string",
                        "description": "What the investigator witnessed that caused this sanity loss (optional)"
                    }
                },
                "required": ["damage"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_hp_damage",
            "description": "Apply physical damage from combat, falls, traps, or environmental hazards.",
            "parameters": {
                "type": "object",
                "properties": {
                    "damage": {
                        "type": "integer",
                        "description": "Hit points to lose (typically 1-6 for minor injury, 1d6+ for combat)"
                    },
                    "source": {
                        "type": "string",
                        "description": "What caused the damage (gunshot, fall, creature attack, etc.) (optional)"
                    }
                },
                "required": ["damage"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pickup_item",
            "description": "Player finds and picks up an item or evidence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_key": {
                        "type": "string",
                        "enum": [
                            "flashlight", "notebook", "revolver", "dynamite", "holy_water",
                            "rope", "logbook", "ancient_text", "amulet", "key",
                            "photograph", "letter", "artifact", "weapon", "herbs"
                        ],
                        "description": "Type of item being picked up"
                    },
                    "item_name": {
                        "type": "string",
                        "description": "Specific name or description of the item (optional, overrides item_key for display)"
                    }
                },
                "required": ["item_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_combat",
            "description": "Initiate a combat encounter with an enemy or creature.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enemy_key": {
                        "type": "string",
                        "enum": [
                            "deep_one_hybrid", "animated_corpse", "shadow_thing",
                            "cultist", "ghoul", "shoggoth", "familiar", "human_enemy",
                            "creature_unknown"
                        ],
                        "description": "Type of enemy being encountered"
                    },
                    "enemy_name": {
                        "type": "string",
                        "description": "Specific name or description of the enemy (optional)"
                    }
                },
                "required": ["enemy_key"]
            }
        }
    }
]
