#!/usr/bin/env python3
"""
Investigator archetypes: shared stat blocks for all entry points
(web and terminal), so character creation never diverges.

Skill keys are snake_case to match the engine's lookup normalization
in execute_skill_check (e.g. "Spot Hidden" -> "spot_hidden").
"""

from typing import Dict

from .state import InvestigatorState


ARCHETYPES: Dict[str, Dict] = {
    "scholar": {
        "label": "Scholar",
        "description": "Miskatonic academic. Strong mind, weak arms. Reads the forbidden books so you don't have to.",
        "characteristics": {
            "STR": 40, "CON": 50, "SIZ": 50, "DEX": 50, "APP": 50,
            "INT": 80, "POW": 65, "EDU": 85,
        },
        "skills": {
            "library_use": 70, "investigate": 60, "occult": 50,
            "psychology": 50, "spot_hidden": 45, "persuade": 45,
            "listen": 40, "first_aid": 40, "climb": 30, "swim": 30,
            "dodge": 30, "brawl": 25,
        },
    },
    "detective": {
        "label": "Detective",
        "description": "Private eye. Notices what others miss and can take a punch when noticing goes wrong.",
        "characteristics": {
            "STR": 60, "CON": 60, "SIZ": 60, "DEX": 65, "APP": 55,
            "INT": 75, "POW": 60, "EDU": 70,
        },
        "skills": {
            "investigate": 70, "spot_hidden": 65, "psychology": 60,
            "listen": 50, "persuade": 50, "brawl": 50, "dodge": 45,
            "stealth": 40, "climb": 40, "first_aid": 35,
            "library_use": 35, "occult": 10,
        },
    },
    "occultist": {
        "label": "Occultist",
        "description": "Student of the unseen. Iron will against the dark, but the dark already knows their name.",
        "characteristics": {
            "STR": 45, "CON": 50, "SIZ": 50, "DEX": 55, "APP": 55,
            "INT": 70, "POW": 80, "EDU": 70,
        },
        "skills": {
            "occult": 70, "library_use": 55, "persuade": 50,
            "investigate": 45, "psychology": 45, "spot_hidden": 40,
            "listen": 40, "stealth": 35, "dodge": 35, "brawl": 30,
            "climb": 30, "first_aid": 30,
        },
    },
    "wanderer": {
        "label": "Wanderer",
        "description": "Drifter and survivor. The body remembers what the mind would rather forget.",
        "characteristics": {
            "STR": 65, "CON": 70, "SIZ": 60, "DEX": 70, "APP": 50,
            "INT": 60, "POW": 55, "EDU": 50,
        },
        "skills": {
            "climb": 60, "swim": 60, "stealth": 55, "listen": 55,
            "spot_hidden": 50, "dodge": 50, "jump": 50, "brawl": 45,
            "first_aid": 40, "persuade": 35, "investigate": 30,
            "occult": 15,
        },
    },
}


def get_archetype_sheets() -> Dict[str, Dict]:
    """Full archetype data with derived stats, for character sheets"""
    sheets = {}
    for key, arch in ARCHETYPES.items():
        chars = dict(arch["characteristics"])
        sheets[key] = {
            "label": arch["label"],
            "description": arch["description"],
            "characteristics": chars,
            "derived": _derived_stats(chars),
            "skills": arch["skills"],
        }
    return sheets


def _derived_stats(chars: Dict[str, int]) -> Dict[str, int]:
    """CoC 7e derived attributes"""
    return {
        "HP": (chars["CON"] + chars["SIZ"]) // 10,
        "SAN": chars["POW"],
        "Luck": 50,
    }


def create_investigator(name: str, archetype: str) -> InvestigatorState:
    """Build an InvestigatorState from an archetype stat block"""
    arch = ARCHETYPES.get(archetype, ARCHETYPES["scholar"])
    characteristics = dict(arch["characteristics"])
    characteristics.update(_derived_stats(characteristics))
    characteristics["max_hp"] = characteristics["HP"]

    return InvestigatorState(
        name=name,
        occupation=archetype,
        characteristics=characteristics,
        skills=dict(arch["skills"]),
        inventory=[],
        visited_locations=[],
        sanity_breaks=[]
    )
