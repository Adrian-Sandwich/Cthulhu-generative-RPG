#!/usr/bin/env python3
"""
Snapshot - Complete game state at one moment
Encapsulates: image + narrative + game state + options
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import json
import time


@dataclass
class GameStateSnapshot:
    """Investigator and game state at a moment"""

    # Character
    investigator_name: str
    investigator_hp: int
    investigator_max_hp: int
    investigator_san: int
    investigator_max_san: int
    investigator_luck: int

    # World
    location: str
    discoveries: List[str] = field(default_factory=list)
    inventory: List[str] = field(default_factory=list)

    # Metadata
    turn: int = 0
    phase: str = "exploring"  # exploring, investigation, combat, climax, ending

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'GameStateSnapshot':
        """Create from dictionary"""
        return GameStateSnapshot(**data)


@dataclass
class Snapshot:
    """Complete snapshot of a game moment"""

    # Identification
    turn_id: int
    session_id: str

    # Visual
    image: Optional[bytes] = None  # PNG image data
    image_seed: int = 0  # For reproducibility (Perlin noise seed)

    # Narrative
    narrative: str = ""  # Full text description
    decision: str = ""  # Action taken ("climb stairs", "examine door")

    # Game State
    state: GameStateSnapshot = field(default_factory=lambda: GameStateSnapshot(
        investigator_name="Unknown",
        investigator_hp=10,
        investigator_max_hp=10,
        investigator_san=50,
        investigator_max_san=99,
        investigator_luck=50,
        location="Unknown"
    ))

    # Commands/Options (next available actions)
    commands: List[str] = field(default_factory=list)

    # Metadata
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)  # ["horror", "discovery", ...]

    def to_json(self) -> str:
        """Export to JSON (for persistence)"""
        data = {
            'turn_id': self.turn_id,
            'session_id': self.session_id,
            'image_seed': self.image_seed,
            'narrative': self.narrative,
            'decision': self.decision,
            'state': self.state.to_dict(),
            'commands': self.commands,
            'timestamp': self.timestamp,
            'tags': self.tags,
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def from_json(json_str: str) -> 'Snapshot':
        """Create from JSON"""
        data = json.loads(json_str)
        state_data = data.pop('state', {})
        state = GameStateSnapshot.from_dict(state_data)
        return Snapshot(state=state, **data)

    def __str__(self) -> str:
        """String representation"""
        return f"Snapshot(turn={self.turn_id}, location={self.state.location}, hp={self.state.investigator_hp}/{self.state.investigator_max_hp}, san={self.state.investigator_san}/{self.state.investigator_max_san})"
