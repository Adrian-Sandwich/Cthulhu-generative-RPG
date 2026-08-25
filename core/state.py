#!/usr/bin/env python3
"""
Core game state dataclasses.

These types are intentionally small and dependency-free so that modules that
only need to describe state (archetypes, saves, terminal drivers, tests) can
import them without pulling in the full generative engine.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    ammo: int = 0          # rounds left for the firearm; 0 = empty
    time_limit: int = 0    # turn at which doom arrives (0 = no clock)
    last_rest_turn: int = 0  # cooldown anchor for deliberate sanity recovery
