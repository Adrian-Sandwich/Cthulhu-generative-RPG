#!/usr/bin/env python3
"""
Companion System for Call of Cthulhu.
Allies who travel with the investigator, develop relationships, and affect the narrative.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random


@dataclass
class Companion:
    """An ally traveling with the investigator"""

    key: str  # Unique identifier (e.g., 'police_chief')
    name: str  # Display name
    role: str  # Occupation/role

    sanity: int = 75  # Current sanity (max 99)
    trust: int = 0  # -100 to +100 (how much they trust player)
    loyalty: int = 50  # 0-100 (likelihood to stay/help)
    fear: int = 0  # 0-100 (how afraid they are)

    skills: Dict[str, int] = field(default_factory=dict)  # Companion skills
    wounds: int = 0  # Current HP damage
    status: str = "healthy"  # healthy, wounded, traumatized, broken

    is_alive: bool = True
    discovered_secrets: List[str] = field(default_factory=list)

    def get_status_description(self) -> str:
        """Get narrative description of companion status"""
        if not self.is_alive:
            return f"{self.name} is dead."

        status_parts = []

        if self.sanity < 20:
            status_parts.append(f"{self.name} is barely holding onto sanity")
        elif self.sanity < 50:
            status_parts.append(f"{self.name} is traumatized")

        if self.wounds > 0:
            status_parts.append("wounded")

        if self.trust > 50:
            status_parts.append("deeply trusts you")
        elif self.trust > 0:
            status_parts.append("trusts you somewhat")
        elif self.trust < -50:
            status_parts.append("distrusts you strongly")

        if self.fear > 75:
            status_parts.append("terrified")
        elif self.fear > 50:
            status_parts.append("afraid")

        if status_parts:
            return f"{self.name}: {', '.join(status_parts)}"
        return f"{self.name} is with you"

    def apply_sanity_damage(self, damage: int, source: str = "unknown") -> Dict:
        """Apply sanity damage to companion"""
        old_san = self.sanity
        self.sanity = max(0, self.sanity - damage)

        result = {
            "damage": damage,
            "sanity_remaining": self.sanity,
            "broke": False,
            "narrative": ""
        }

        # Breaking point at 10+ loss
        if damage >= 10:
            result["broke"] = True
            result["narrative"] = (
                f"{self.name} screams. Their eyes are wide with horror. "
                f"They may not recover from this."
            )
            self.status = "traumatized"
            self.fear = min(100, self.fear + 20)

        # Critical at SAN < 20
        if self.sanity < 20 and old_san >= 20:
            result["narrative"] = (
                f"{self.name} is barely holding on. Their grip on reality is slipping."
            )
            self.status = "broken"
            self.loyalty = max(0, self.loyalty - 20)

        return result

    def modify_trust(self, amount: int, reason: str = "") -> None:
        """Adjust trust toward player"""
        self.trust = max(-100, min(100, self.trust + amount))

    def abandon(self) -> str:
        """Companion abandons the player"""
        self.is_alive = False
        return f"{self.name} abandons you, unable to continue."

    def die(self, cause: str = "unknown") -> str:
        """Companion dies"""
        self.is_alive = False
        return f"{self.name} dies from {cause}."

    def to_dict(self) -> Dict:
        """Serialize companion"""
        return {
            "key": self.key,
            "name": self.name,
            "role": self.role,
            "sanity": self.sanity,
            "trust": self.trust,
            "loyalty": self.loyalty,
            "fear": self.fear,
            "skills": self.skills,
            "wounds": self.wounds,
            "status": self.status,
            "is_alive": self.is_alive,
            "discovered_secrets": self.discovered_secrets
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Companion":
        """Deserialize companion"""
        return cls(
            key=data["key"],
            name=data["name"],
            role=data["role"],
            sanity=data.get("sanity", 75),
            trust=data.get("trust", 0),
            loyalty=data.get("loyalty", 50),
            fear=data.get("fear", 0),
            skills=data.get("skills", {}),
            wounds=data.get("wounds", 0),
            status=data.get("status", "healthy"),
            is_alive=data.get("is_alive", True),
            discovered_secrets=data.get("discovered_secrets", [])
        )


class CompanionManager:
    """Manages companions traveling with the investigator"""

    COMPANION_DEFINITIONS = {
        "police_chief": {
            "name": "Chief Marsh",
            "role": "Police Chief",
            "skills": {"firearms": 60, "intimidate": 50, "investigate": 40}
        },
        "scientist": {
            "name": "Dr. Armitage",
            "role": "Scientist",
            "skills": {"science": 70, "occult": 60, "library_use": 65}
        },
        "reporter": {
            "name": "Sarah Hill",
            "role": "Newspaper Reporter",
            "skills": {"persuade": 60, "spot_hidden": 50, "library_use": 55}
        }
    }

    def __init__(self):
        """Initialize companion manager"""
        self.active_companions: Dict[str, Companion] = {}
        self.past_companions: List[Companion] = []

    def recruit_companion(self, companion_key: str) -> Optional[Companion]:
        """Recruit a companion to travel with player"""
        if companion_key not in self.COMPANION_DEFINITIONS:
            return None

        if companion_key in self.active_companions:
            return self.active_companions[companion_key]

        definition = self.COMPANION_DEFINITIONS[companion_key]
        companion = Companion(
            key=companion_key,
            name=definition["name"],
            role=definition["role"],
            skills=definition.get("skills", {})
        )

        self.active_companions[companion_key] = companion
        return companion

    def remove_companion(self, companion_key: str, reason: str = "abandoned") -> Optional[str]:
        """Remove companion from active roster"""
        if companion_key not in self.active_companions:
            return None

        companion = self.active_companions.pop(companion_key)
        self.past_companions.append(companion)

        if reason == "death":
            return f"{companion.name} is dead."
        elif reason == "abandoned":
            return f"{companion.name} has abandoned you."
        else:
            return f"{companion.name} is no longer with you."

    def get_active_companions(self) -> List[Companion]:
        """Get list of active companions"""
        return list(self.active_companions.values())

    def get_companion_context(self) -> str:
        """Get narrative context about companion status for DM"""
        if not self.active_companions:
            return "You are alone."

        companions = self.get_active_companions()
        if len(companions) == 1:
            return companions[0].get_status_description()

        # Multiple companions
        statuses = [c.name for c in companions if c.is_alive]
        return f"You're traveling with: {', '.join(statuses)}"

    def check_companion_stability(self) -> List[str]:
        """Check if any companions might break/abandon/die"""
        events = []

        for companion in self.get_active_companions():
            # Sanity spiral → breakdown
            if companion.sanity < 10 and companion.status != "broken":
                events.append(
                    f"{companion.name} breaks down completely, unable to continue."
                )
                companion.status = "broken"
                companion.loyalty = 0

            # Low loyalty → abandonment
            if companion.loyalty < 10 and companion.status == "broken":
                events.append(
                    f"{companion.name} flees into the night, their mind shattered."
                )
                self.remove_companion(companion.key, "abandoned")

            # Mortal wounds → death
            if companion.wounds > companion.role.count('t'):  # Hack; real system would track HP
                events.append(
                    f"{companion.name} succumbs to their injuries."
                )
                self.remove_companion(companion.key, "death")

        return events

    def to_dict(self) -> Dict:
        """Serialize all companions"""
        return {
            "active": {k: v.to_dict() for k, v in self.active_companions.items()},
            "past": [c.to_dict() for c in self.past_companions]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CompanionManager":
        """Deserialize from dictionary"""
        mgr = cls()
        mgr.active_companions = {
            k: Companion.from_dict(v)
            for k, v in data.get("active", {}).items()
        }
        mgr.past_companions = [
            Companion.from_dict(c) for c in data.get("past", [])
        ]
        return mgr
