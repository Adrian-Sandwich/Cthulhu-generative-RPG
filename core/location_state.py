#!/usr/bin/env python3
"""
Dynamic Location State System for Call of Cthulhu.
Locations evolve based on player discoveries, visits, and time passage.
Danger levels escalate, secrets unlock new content, state persists.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json
from pathlib import Path


@dataclass
class LocationState:
    """Mutable state of a location that changes based on player actions"""

    key: str  # Unique identifier (e.g., 'lighthouse_exterior')
    name: str  # Display name
    base_description: str  # Foundation description

    visited_count: int = 0  # Number of times visited
    secrets_revealed: List[str] = field(default_factory=list)  # Clues found
    danger_level: int = 1  # 1-5 (escalates if unresolved)
    contamination: int = 0  # Supernatural corruption (0-100)
    events_triggered: List[str] = field(default_factory=list)  # Events that occurred
    last_visited_turn: int = 0  # When last visited

    def get_current_description(self) -> str:
        """Generate description based on current state"""
        desc = self.base_description

        # Add revisit markers
        if self.visited_count >= 2:
            desc += "\n[You've been here before, but something feels different now.]"

        # Escalating danger
        if self.danger_level >= 4:
            desc += "\n[The air feels thick with oppressive dread. Something is very wrong here.]"
        elif self.danger_level >= 2:
            desc += "\n[There's a subtle unease to this place.]"

        # Contamination effects
        if self.contamination >= 75:
            desc += "\n[Reality seems to bend strangely here. The laws of nature feel negotiable.]"
        elif self.contamination >= 50:
            desc += "\n[Unnatural symbols and patterns mark the walls.]"
        elif self.contamination >= 25:
            desc += "\n[Something about this place feels profoundly wrong.]"

        # Reveal found secrets in description
        if "keeper_corpse" in self.secrets_revealed:
            desc += "\n[The keeper's corpse lies where you left it, beginning to decompose.]"
        if "hidden_passage" in self.secrets_revealed:
            desc += "\n[The hidden passage remains open, descending into darkness.]"
        if "ritual_chamber" in self.secrets_revealed:
            desc += "\n[Evidence of a ritual still lingers in this place.]"

        return desc

    def to_dict(self) -> Dict:
        """Serialize to dictionary for saving"""
        return {
            "key": self.key,
            "name": self.name,
            "base_description": self.base_description,
            "visited_count": self.visited_count,
            "secrets_revealed": self.secrets_revealed,
            "danger_level": self.danger_level,
            "contamination": self.contamination,
            "events_triggered": self.events_triggered,
            "last_visited_turn": self.last_visited_turn
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "LocationState":
        """Deserialize from dictionary"""
        return cls(
            key=data["key"],
            name=data["name"],
            base_description=data["base_description"],
            visited_count=data.get("visited_count", 0),
            secrets_revealed=data.get("secrets_revealed", []),
            danger_level=data.get("danger_level", 1),
            contamination=data.get("contamination", 0),
            events_triggered=data.get("events_triggered", []),
            last_visited_turn=data.get("last_visited_turn", 0)
        )


class LocationStateManager:
    """Manages dynamic states of all locations in the game"""

    # Secrets that unlock new locations when discovered
    SECRET_UNLOCKS = {
        "hidden_passage": "underground_chamber",
        "ritual_chamber_map": "ritual_chamber",
        "keeper_diary": "keeper_quarters_hidden",
    }

    # Secrets that reduce danger when discovered
    DANGER_REDUCING_SECRETS = {
        "ritual_seal": 2,
        "entity_ward": 3,
        "safe_haven": 2,
    }

    def __init__(self, persist_dir: Optional[str] = None):
        """
        Initialize location state manager.

        Args:
            persist_dir: Optional directory for saving/loading location states
        """
        self.locations: Dict[str, LocationState] = {}
        self.unlocked_locations: set = set()
        self.persist_dir = Path(persist_dir) if persist_dir else None

    def register_location(
        self, key: str, name: str, description: str
    ) -> LocationState:
        """
        Register a location with initial state.

        Args:
            key: Unique identifier
            name: Display name
            description: Initial description

        Returns:
            Created LocationState
        """
        loc = LocationState(
            key=key, name=name, base_description=description
        )
        self.locations[key] = loc
        self.unlocked_locations.add(key)
        return loc

    def visit_location(self, key: str, current_turn: int = 0) -> str:
        """
        Handle location visit - update state and get description.

        Args:
            key: Location key
            current_turn: Current game turn

        Returns:
            Location description with dynamic updates
        """
        if key not in self.locations:
            return "You find yourself in an unknown place."

        loc = self.locations[key]
        loc.visited_count += 1
        loc.last_visited_turn = current_turn

        # Escalate danger if no secrets found
        if not loc.secrets_revealed and loc.visited_count > 1:
            loc.danger_level = min(5, loc.danger_level + 1)

        return loc.get_current_description()

    def reveal_secret(self, location_key: str, secret_key: str) -> Dict:
        """
        Player discovers a secret - update location state and check for unlocks.

        Args:
            location_key: Location where secret was found
            secret_key: Secret identifier

        Returns:
            Dict with unlock info and narrative
        """
        if location_key not in self.locations:
            return {"success": False}

        loc = self.locations[location_key]

        if secret_key in loc.secrets_revealed:
            return {"success": False, "message": "Already discovered"}

        result = {
            "success": True,
            "secret": secret_key,
            "location": location_key,
            "unlocked_location": None,
            "danger_reduced": 0,
            "narrative": f"You discover: {secret_key}"
        }

        loc.secrets_revealed.append(secret_key)

        # Reduce danger when secrets found
        if secret_key in self.DANGER_REDUCING_SECRETS:
            reduction = self.DANGER_REDUCING_SECRETS[secret_key]
            loc.danger_level = max(1, loc.danger_level - reduction)
            result["danger_reduced"] = reduction

        # Unlock new location
        if secret_key in self.SECRET_UNLOCKS:
            new_location = self.SECRET_UNLOCKS[secret_key]
            self.unlocked_locations.add(new_location)
            result["unlocked_location"] = new_location
            result["narrative"] += f"\nA new location has become accessible: {new_location}"

        return result

    def trigger_event(
        self, location_key: str, event_key: str
    ) -> bool:
        """
        Trigger an event at a location (only once per playthrough).

        Args:
            location_key: Location where event occurs
            event_key: Event identifier

        Returns:
            True if event is new, False if already triggered
        """
        if location_key not in self.locations:
            return False

        loc = self.locations[location_key]

        if event_key in loc.events_triggered:
            return False  # Already triggered

        loc.events_triggered.append(event_key)
        return True  # Event is new

    def increase_contamination(
        self, location_key: str, amount: int
    ) -> None:
        """
        Increase supernatural contamination at a location.

        Args:
            location_key: Location to contaminate
            amount: Contamination points to add (max 100)
        """
        if location_key in self.locations:
            loc = self.locations[location_key]
            loc.contamination = min(100, loc.contamination + amount)

    def decrease_contamination(
        self, location_key: str, amount: int
    ) -> None:
        """
        Decrease supernatural contamination (via cleansing/sealing).

        Args:
            location_key: Location to cleanse
            amount: Contamination points to remove
        """
        if location_key in self.locations:
            loc = self.locations[location_key]
            loc.contamination = max(0, loc.contamination - amount)

    def get_location_context(self, location_key: str) -> str:
        """
        Get context string for DM prompt about current location state.

        Args:
            location_key: Location to query

        Returns:
            Formatted context string
        """
        if location_key not in self.locations:
            return ""

        loc = self.locations[location_key]
        parts = []

        if loc.visited_count > 0:
            parts.append(f"visited {loc.visited_count} time(s)")

        if loc.secrets_revealed:
            parts.append(f"{len(loc.secrets_revealed)} secret(s) found")

        if loc.danger_level > 1:
            parts.append(f"danger level {loc.danger_level}/5")

        if loc.contamination > 0:
            parts.append(f"contamination {loc.contamination}%")

        if not parts:
            return ""

        return f"[Location state: {', '.join(parts)}]"

    def is_location_unlocked(self, location_key: str) -> bool:
        """Check if location is accessible"""
        return location_key in self.unlocked_locations

    def get_unlocked_locations(self) -> List[str]:
        """Get list of currently accessible locations"""
        return list(self.unlocked_locations)

    def save_state(self, session_id: str) -> bool:
        """
        Save location states to disk.

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        if not self.persist_dir:
            return False

        try:
            save_path = self.persist_dir / f"locations_{session_id}.json"
            save_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "locations": {k: v.to_dict() for k, v in self.locations.items()},
                "unlocked": list(self.unlocked_locations)
            }

            with open(save_path, "w") as f:
                json.dump(data, f, indent=2)

            return True
        except Exception:
            return False

    def load_state(self, session_id: str) -> bool:
        """
        Load location states from disk.

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        if not self.persist_dir:
            return False

        try:
            load_path = self.persist_dir / f"locations_{session_id}.json"

            if not load_path.exists():
                return False

            with open(load_path, "r") as f:
                data = json.load(f)

            self.locations = {
                k: LocationState.from_dict(v)
                for k, v in data.get("locations", {}).items()
            }
            self.unlocked_locations = set(data.get("unlocked", []))

            return True
        except Exception:
            return False

    def to_dict(self) -> Dict:
        """Serialize all location states"""
        return {
            "locations": {k: v.to_dict() for k, v in self.locations.items()},
            "unlocked": list(self.unlocked_locations)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "LocationStateManager":
        """Deserialize from dictionary"""
        mgr = cls()
        mgr.locations = {
            k: LocationState.from_dict(v)
            for k, v in data.get("locations", {}).items()
        }
        mgr.unlocked_locations = set(data.get("unlocked", []))
        return mgr
