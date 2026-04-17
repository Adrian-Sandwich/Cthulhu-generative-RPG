#!/usr/bin/env python3
"""
Cthulhu Game Engine v1 - Main Orchestrator

Coordinates all game systems for a single game session.
"""

import json
from typing import Dict, Optional, List

from .state import GameState, InvestigatorState, CoC7eRulesEngine
from .core.systems import SanitySystem, CompanionSystem, LocationState, EndingSystem
from .core.memory import DMMemory, EntityGraph, GameSaveManager


class CthulhuEngine:
    """
    Main game engine - orchestrates all systems

    Responsibilities:
    - Game loop management
    - Turn processing
    - System orchestration
    - State management
    """

    def __init__(
        self,
        adventure_name: str,
        investigator_name: str,
        model: str = "mistral",
        use_memory: bool = True,
        use_neo4j: bool = False
    ):
        """
        Initialize game engine.

        Args:
            adventure_name: Name of adventure (e.g., "point_black")
            investigator_name: Player character name
            model: LLM model to use
            use_memory: Enable semantic memory system
            use_neo4j: Enable entity graph (requires Neo4j)
        """
        self.adventure_name = adventure_name
        self.model = model

        # Game state
        self.state: Optional[GameState] = None
        self.rules = CoC7eRulesEngine()

        # Systems
        self.sanity_system = SanitySystem()
        self.companion_system = CompanionSystem()
        self.location_system = LocationState()
        self.ending_system = EndingSystem()

        # Persistence
        self.memory = DMMemory(session_id=adventure_name, enabled=use_memory)
        self.entity_graph = EntityGraph(enabled=use_neo4j)
        self.save_manager = GameSaveManager()

        # LLM (to be initialized)
        self.llm = None

    def create_game(self, investigator_stats: Dict) -> GameState:
        """
        Create a new game session.

        Args:
            investigator_stats: Character stats from investigator creation

        Returns:
            Initial GameState
        """
        # Create investigator
        investigator = InvestigatorState(
            name=investigator_stats['name'],
            occupation=investigator_stats['occupation'],
            characteristics=investigator_stats['characteristics'],
            skills=investigator_stats['skills'],
            inventory=investigator_stats.get('inventory', []),
        )

        # Create game state
        self.state = GameState(
            turn=0,
            location="Starting Location",
            narrative=[],
            investigator=investigator,
        )

        return self.state

    def process_turn(self, player_action: str) -> Dict:
        """
        Process a single game turn.

        Args:
            player_action: Player's action text

        Returns:
            Turn result with narrative, rolls, damage, etc.
        """
        if not self.state:
            return {"error": "No active game"}

        # TODO: This will call LLM, process mechanics, update state
        # For now, return stub

        return {
            "narrative": "Game processing not yet implemented in v1 stub",
            "rolls_requested": [],
            "state": self.state.__dict__
        }

    def execute_skill_check(self, skill: str, difficulty: str = "Normal") -> Dict:
        """
        Execute a skill check with dice rolling.

        Args:
            skill: Skill name
            difficulty: "Normal", "Hard", or "Extreme"

        Returns:
            Roll result with success/failure
        """
        if not self.state:
            return {"error": "No active game"}

        # TODO: Implement actual dice rolling
        return {
            "skill": skill,
            "difficulty": difficulty,
            "success": False
        }

    def save_game(self, save_name: Optional[str] = None) -> str:
        """Save current game state."""
        if not self.state:
            return ""
        return self.save_manager.save_game(self.state, save_name)

    def load_game(self, save_name: str) -> bool:
        """Load a saved game."""
        loaded_state = self.save_manager.load_game(save_name)
        if loaded_state:
            self.state = loaded_state
            return True
        return False

    def end_game(self) -> None:
        """End the current game session."""
        if self.state:
            self.save_game(f"session_{self.state.turn}")
            self.state = None
