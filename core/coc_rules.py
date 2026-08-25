#!/usr/bin/env python3
"""Call of Cthulhu 7e rules enforcement."""

import random
from typing import Dict


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
