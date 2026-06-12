#!/usr/bin/env python3
"""
Parser for DM response tags.

The tag-based protocol lets non-tool-calling models request game
mechanics inline, e.g.:

    [ROLL: spot hidden/Hard] [SANITY_CHECK: 4] [ITEM_FOUND: rusty_key]
    [HP_DAMAGE: 2] [COMBAT_START: deep_one] [NPC_DIALOGUE: warner]
"""

import re
from typing import Dict


# Tag name -> capture pattern. ROLL allows multi-word skills and
# difficulties ("spot hidden/Hard"); the rest are single tokens/numbers.
_TAG_PATTERNS = {
    "ROLL": r'\[ROLL: ([^/\]]+)/([^\]]+)\]',
    "SANITY_CHECK": r'\[SANITY_CHECK: (\d+)\]',
    "ITEM_FOUND": r'\[ITEM_FOUND: (\w+)\]',
    "HP_DAMAGE": r'\[HP_DAMAGE: (\d+)\]',
    "COMBAT_START": r'\[COMBAT_START: (\w+)\]',
    "NPC_DIALOGUE": r'\[NPC_DIALOGUE: (\w+)\]',
}

_STRIP_PATTERN = re.compile(
    r'\[(?:ROLL|SANITY_CHECK|ITEM_FOUND|HP_DAMAGE|COMBAT_START|NPC_DIALOGUE): .*?\]'
)


def parse_dm_response(dm_response: str) -> Dict:
    """
    Extract all mechanic tags from a DM response.

    Returns:
        Dict with:
            rolls_requested: List of (skill, difficulty) tuples
            sanity_checks: List of damage strings
            items_found: List of item keys
            hp_damage: List of damage strings
            combat_start: List of enemy keys
            npc_dialogue: List of NPC keys
            clean_response: Response text with all tags removed
    """
    return {
        "rolls_requested": [
            (skill.strip(), difficulty.strip())
            for skill, difficulty in re.findall(_TAG_PATTERNS["ROLL"], dm_response)
        ],
        "sanity_checks": re.findall(_TAG_PATTERNS["SANITY_CHECK"], dm_response),
        "items_found": re.findall(_TAG_PATTERNS["ITEM_FOUND"], dm_response),
        "hp_damage": re.findall(_TAG_PATTERNS["HP_DAMAGE"], dm_response),
        "combat_start": re.findall(_TAG_PATTERNS["COMBAT_START"], dm_response),
        "npc_dialogue": re.findall(_TAG_PATTERNS["NPC_DIALOGUE"], dm_response),
        "clean_response": strip_tags(dm_response),
    }


def strip_tags(text: str) -> str:
    """Remove all mechanic tags from text"""
    return _STRIP_PATTERN.sub('', text)
