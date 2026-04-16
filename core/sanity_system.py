#!/usr/bin/env python3
"""
Enhanced Sanity System for Call of Cthulhu 7th Edition.
Implements breaking points, temporary insanity, permanent disorders,
and sanity recovery mechanics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import random


@dataclass
class MentalDisorder:
    """
    Mental disorder acquired through horror or sanity loss.
    Affects investigator behavior and narrative.
    """
    type: str  # "phobia", "mania", "obsession", "paranoia", "dissociation"
    trigger: str  # What caused it: "deep_ones", "undead", "ritual", "madness"
    intensity: int  # 1-5 (leve to severe)
    duration: int  # Turns remaining (-1 = permanent)
    effects: List[str]  # Narrative effects

    def is_permanent(self) -> bool:
        """Check if disorder is permanent"""
        return self.duration == -1

    def is_temporary(self) -> bool:
        """Check if disorder is temporary"""
        return self.duration > 0

    def get_effect_description(self) -> str:
        """Get current effect as narrative text"""
        if self.effects:
            return self.effects[0]
        return f"You suffer from {self.type} related to {self.trigger}"


class SanitySystem:
    """
    Manages sanity mechanics including breaking points,
    temporary insanity, permanent disorders, and recovery.
    """

    # Sanity loss thresholds for different horror types
    HORROR_THRESHOLDS = {
        "minor": 1,  # Creepy atmosphere
        "moderate": 4,  # Disturbing discovery
        "major": 8,  # Witness to horror
        "overwhelming": 15  # Contact with cosmic entity
    }

    # Temporary insanity duration (turns)
    TEMP_INSANITY_DURATION = 10  # ~1 hour

    def __init__(self, investigator_state):
        """
        Initialize sanity system.

        Args:
            investigator_state: InvestigatorState object to manage sanity for
        """
        self.investigator = investigator_state
        self.sanity_loss_history: List[Dict] = []  # Track last 10 losses
        self.mental_disorders: List[MentalDisorder] = []  # Current disorders
        self.breaking_points: int = 0  # Number of times broken
        self.in_sanity_spiral: bool = False  # Currently in spiral?

    def apply_sanity_damage(self, damage: int, source: str = "unknown") -> Dict:
        """
        Apply sanity damage and check for breaking points/spirals.

        Args:
            damage: Sanity points to lose
            source: What caused the loss (for narrative)

        Returns:
            Dict with:
                - sanity_remaining: New SAN value
                - broke: Whether a breaking point occurred
                - temporary_insanity: Optional MentalDisorder if broke
                - permanent_disorder: Optional MentalDisorder if spiral
                - spiral_detected: Whether spiral was triggered
                - narrative: Narrative description of what happened
        """
        old_san = self.investigator.characteristics["SAN"]
        new_san = max(0, old_san - damage)
        self.investigator.characteristics["SAN"] = new_san

        # Record loss
        self.sanity_loss_history.append({
            "damage": damage,
            "source": source,
            "san_before": old_san,
            "san_after": new_san,
            "turn": getattr(self.investigator, "current_turn", 0)
        })

        # Keep only last 10
        if len(self.sanity_loss_history) > 10:
            self.sanity_loss_history.pop(0)

        result = {
            "sanity_remaining": new_san,
            "broke": False,
            "temporary_insanity": None,
            "permanent_disorder": None,
            "spiral_detected": False,
            "narrative": ""
        }

        # Check for breaking point (sudden large loss >= 10)
        if damage >= 10:
            self.breaking_points += 1
            disorder = self._generate_temporary_insanity(source)
            self.mental_disorders.append(disorder)

            result["broke"] = True
            result["temporary_insanity"] = disorder
            result["narrative"] = (
                f"Your mind reels from the horror. {disorder.get_effect_description()} "
                f"You must make immediate Sanity checks to understand what's happening."
            )
            return result

        # Check for sanity spiral (3+ losses > 5 points in last 5 turns)
        recent_major_losses = [
            l for l in self.sanity_loss_history[-5:]
            if l["damage"] >= 5
        ]

        if len(recent_major_losses) >= 3:
            self.in_sanity_spiral = True
            disorder = self._generate_permanent_disorder(source)
            self.mental_disorders.append(disorder)

            result["broke"] = True
            result["spiral_detected"] = True
            result["permanent_disorder"] = disorder
            result["narrative"] = (
                f"The accumulation of horrors breaks your mind. "
                f"A permanent disorder develops: {disorder.type}. "
                f"{disorder.get_effect_description()}"
            )
            return result

        # Check if SAN drops below critical threshold
        if new_san < 20 and old_san >= 20:
            # Potential for disorder to become permanent
            for disorder in self.mental_disorders:
                if disorder.is_temporary() and disorder.duration <= 3:
                    # Convert to permanent if about to expire at low SAN
                    if random.random() < 0.3:  # 30% chance
                        disorder.duration = -1
                        result["narrative"] = (
                            f"Your sanity is critically low. "
                            f"Your {disorder.type} becomes permanent."
                        )

        return result

    def _generate_temporary_insanity(self, source: str) -> MentalDisorder:
        """
        Generate random temporary insanity based on horror source.

        Returns:
            MentalDisorder with duration > 0
        """
        # Map horror sources to disorder types
        disorder_map = {
            "deep_ones": ["water_phobia", "paranoia"],
            "undead": ["death_phobia", "paranoia"],
            "ritual": ["religion_obsession", "paranoia"],
            "madness": ["dissociation", "paranoia"],
            "unknown": ["paranoia", "generalized_anxiety"],
            "combat": ["battle_trauma", "paranoia"],
            "cosmic": ["cosmic_horror_obsession", "dissociation"]
        }

        disorder_types = disorder_map.get(source, ["generalized_anxiety", "paranoia"])
        disorder_type = random.choice(disorder_types)

        # Generate effects based on type
        effects_map = {
            "water_phobia": [
                "You recoil from any body of water",
                "Swimming becomes psychologically impossible",
                "Rain triggers panic"
            ],
            "death_phobia": [
                "You are obsessed with your mortality",
                "Hospitals and graveyards trigger panic",
                "You avoid dangerous situations obsessively"
            ],
            "paranoia": [
                "You suspect everyone of harboring dark secrets",
                "You double-check locks obsessively",
                "Shadows seem to conceal watching eyes"
            ],
            "religion_obsession": [
                "You become obsessed with religious rituals",
                "You perform repetitive prayers for protection",
                "You see religious meaning in random events"
            ],
            "dissociation": [
                "You feel detached from reality",
                "Time seems to slip away",
                "You lose track of what's real"
            ],
            "battle_trauma": [
                "You startle easily at sudden noises",
                "Combat triggers overwhelming panic",
                "You have trouble sleeping and nightmares"
            ],
            "cosmic_horror_obsession": [
                "You become obsessed with cosmic truths",
                "You see signs of the cosmic horror everywhere",
                "You compulsively research forbidden knowledge"
            ],
            "generalized_anxiety": [
                "You feel pervasive dread",
                "Everyday tasks become difficult",
                "You worry about things beyond your control"
            ]
        }

        effects = effects_map.get(disorder_type, ["You feel profoundly disturbed"])

        return MentalDisorder(
            type=disorder_type,
            trigger=source,
            intensity=random.randint(1, 3),
            duration=self.TEMP_INSANITY_DURATION,
            effects=effects
        )

    def _generate_permanent_disorder(self, source: str) -> MentalDisorder:
        """
        Generate permanent mental disorder from sanity spiral.

        Returns:
            MentalDisorder with duration = -1 (permanent)
        """
        return MentalDisorder(
            type="acquired_phobia",
            trigger=source,
            intensity=random.randint(2, 4),
            duration=-1,  # Permanent
            effects=[
                f"You have developed a severe phobia of {source}",
                "You cannot function in situations involving your phobia",
                "Your fear drives your actions and relationships"
            ]
        )

    def recover_sanity(self, amount: int, method: str = "rest") -> Dict:
        """
        Recover sanity through rest, therapy, or other means.

        Args:
            amount: Sanity points to recover (max 1 per week of rest)
            method: Recovery method ("rest", "therapy", "occult_knowledge")

        Returns:
            Dict with recovery details
        """
        old_san = self.investigator.characteristics["SAN"]
        max_san = 99  # CoC max sanity is 99
        new_san = min(max_san, old_san + amount)
        recovered = new_san - old_san

        self.investigator.characteristics["SAN"] = new_san

        result = {
            "sanity_before": old_san,
            "sanity_after": new_san,
            "recovered": recovered,
            "method": method,
            "narrative": ""
        }

        if method == "rest":
            result["narrative"] = (
                f"After a period of rest, your mind settles slightly. "
                f"(Recovered {recovered} Sanity)"
            )
        elif method == "therapy":
            result["narrative"] = (
                f"Through therapy, you process some of your trauma. "
                f"(Recovered {recovered} Sanity)"
            )
        elif method == "occult_knowledge":
            result["narrative"] = (
                f"Understanding the cosmic truth somehow brings a twisted peace. "
                f"(Recovered {recovered} Sanity)"
            )

        return result

    def reduce_disorder_duration(self) -> List[MentalDisorder]:
        """
        Reduce duration of temporary disorders (called each turn).
        Returns list of disorders that just expired/became permanent.

        Returns:
            List of MentalDisorders that changed status this turn
        """
        changed = []

        for disorder in self.mental_disorders[:]:
            if disorder.is_temporary():
                disorder.duration -= 1

                # Check if just expired
                if disorder.duration == 0:
                    # Potential conversion to permanent if SAN is low
                    if self.investigator.characteristics["SAN"] < 20:
                        disorder.duration = -1
                        changed.append(disorder)
                    else:
                        # Remove resolved temporary disorder
                        self.mental_disorders.remove(disorder)
                        changed.append(disorder)

        return changed

    def get_active_disorders(self) -> List[MentalDisorder]:
        """Get list of currently active mental disorders"""
        return [d for d in self.mental_disorders if d.duration != 0]

    def get_disorder_narrative(self) -> str:
        """Get narrative description of current mental state"""
        active = self.get_active_disorders()

        if not active:
            return ""

        if len(active) == 1:
            d = active[0]
            durability = "permanently" if d.is_permanent() else f"for {d.duration} more turns"
            return f"You are troubled by {d.type} ({durability}): {d.effects[0]}"

        # Multiple disorders
        descriptions = [d.type for d in active[:2]]
        return f"You are burdened by multiple disorders: {', '.join(descriptions)}"

    def get_sanity_status(self) -> Dict:
        """Get comprehensive sanity status"""
        san = self.investigator.characteristics["SAN"]

        # Determine sanity level
        if san >= 75:
            level = "Stable"
        elif san >= 50:
            level = "Stressed"
        elif san >= 25:
            level = "Traumatized"
        else:
            level = "Critically Unstable"

        return {
            "current": san,
            "max": 99,
            "level": level,
            "breaking_points": self.breaking_points,
            "in_spiral": self.in_sanity_spiral,
            "active_disorders": len(self.get_active_disorders()),
            "total_disorders": len(self.mental_disorders),
            "status_description": self.get_disorder_narrative()
        }
