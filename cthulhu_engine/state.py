#!/usr/bin/env python3
"""
Game State and Rules Engine
Contains all data structures and rules for Call of Cthulhu 7e
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple


@dataclass
class InvestigatorState:
    """Player character state"""
    name: str
    occupation: str
    characteristics: Dict[str, int]  # STR, CON, DEX, POW, APP, EDU, INT, SIZ, HP, SAN, Luck
    skills: Dict[str, int]
    inventory: List[str] = field(default_factory=list)
    visited_locations: List[str] = field(default_factory=list)
    sanity_breaks: List[str] = field(default_factory=list)  # Description of each sanity loss event


@dataclass
class GameState:
    """Complete game state"""
    turn: int
    location: str
    narrative: List[str]  # Full story so far
    investigator: InvestigatorState
    recent_actions: List[str] = field(default_factory=list)  # Last 5 actions
    game_phase: str = "exploring"  # "exploring", "investigation", "combat", "climax", "ending"
    victory_condition: Optional[str] = None  # How player could win
    ending_reached: Optional[str] = None  # "escape", "madness", "victory", "death"
    ending_narrative: Optional[str] = None  # Rich ending text
    active_combat: Optional[Dict] = None  # Current enemy stats
    npcs_talked_to: Dict[str, List[str]] = field(default_factory=dict)  # NPC key -> topics discussed
    last_roll: Optional[Dict] = None  # Track last roll result (skill, difficulty, success)
    npc_reputation: Dict[str, int] = field(default_factory=dict)  # NPC key -> reputation score (-100 to +100)


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
    def calculate_target_number(skill_value: int, characteristic: int, difficulty: str = "Normal") -> int:
        """
        Calculate target number for a skill check.

        Base = skill value
        Hard = skill ÷ 2
        Extreme = skill ÷ 5
        """
        if difficulty not in CoC7eRulesEngine.DIFFICULTY_MODS:
            difficulty = "Normal"

        modifier = CoC7eRulesEngine.DIFFICULTY_MODS[difficulty]
        return int(skill_value * modifier)

    @staticmethod
    def is_success(roll: int, target: int) -> bool:
        """Check if roll succeeded (roll <= target)"""
        return roll <= target
