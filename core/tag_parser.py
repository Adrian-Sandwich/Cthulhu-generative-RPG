#!/usr/bin/env python3
"""
Parser for DM response tags.

The tag-based protocol lets non-tool-calling models request game
mechanics inline, e.g.:

    [ROLL: spot hidden/Hard] [SANITY_CHECK: 4] [ITEM_FOUND: rusty_key]
    [HP_DAMAGE: 2] [COMBAT_START: deep_one] [NPC_DIALOGUE: warner]
"""

import random
import re
from typing import Dict


# Tag name -> capture pattern. ROLL allows multi-word skills and
# difficulties ("spot hidden/Hard"). Damage values accept dice
# notation ("1d6") because models write it despite instructions;
# dice are rolled at parse time so consumers always get plain ints.
_TAG_PATTERNS = {
    "ROLL": r'\[ROLL: ([^/\]]+)/([^\]]+)\]',
    "SANITY_CHECK": r'\[SANITY_CHECK: (\d+(?:[dD]\d+)?)\]',
    "ITEM_FOUND": r'\[ITEM_FOUND: (\w+)\]',
    "HP_DAMAGE": r'\[HP_DAMAGE: (\d+(?:[dD]\d+)?)\]',
    "COMBAT_START": r'\[COMBAT_START: (\w+)\]',
    "NPC_DIALOGUE": r'\[NPC_DIALOGUE: (\w+)\]',
}


def _resolve_amount(expr: str) -> str:
    """Resolve a damage expression to a plain integer string.

    Accepts "3" or dice notation "1d6" / "2D4".
    """
    if 'd' in expr.lower():
        count, sides = re.split('[dD]', expr)
        total = sum(random.randint(1, int(sides)) for _ in range(int(count)))
        return str(total)
    return expr

_STRIP_PATTERN = re.compile(
    r'\[(?:ROLL|SANITY_CHECK|ITEM_FOUND|HP_DAMAGE|COMBAT_START|NPC_DIALOGUE): .*?\]'
)

# Models decorate narrative with markdown despite instructions;
# the game renders plain text, so emphasis markers are stripped.
_MARKDOWN_PATTERNS = [
    (re.compile(r'\*\*\*(.+?)\*\*\*', re.DOTALL), r'\1'),  # bold italic
    (re.compile(r'\*\*(.+?)\*\*', re.DOTALL), r'\1'),      # bold
    (re.compile(r'\*(.+?)\*', re.DOTALL), r'\1'),          # italic
    (re.compile(r'__(.+?)__', re.DOTALL), r'\1'),          # bold (underscore)
    (re.compile(r'`(.+?)`', re.DOTALL), r'\1'),            # code
    (re.compile(r'^#{1,6} ', re.MULTILINE), ''),           # headers
]


def strip_markdown(text: str) -> str:
    """Remove markdown emphasis the LLM adds to narrative text"""
    for pattern, replacement in _MARKDOWN_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


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
        "sanity_checks": [
            _resolve_amount(v) for v in re.findall(_TAG_PATTERNS["SANITY_CHECK"], dm_response)
        ],
        "items_found": re.findall(_TAG_PATTERNS["ITEM_FOUND"], dm_response),
        "hp_damage": [
            _resolve_amount(v) for v in re.findall(_TAG_PATTERNS["HP_DAMAGE"], dm_response)
        ],
        "combat_start": re.findall(_TAG_PATTERNS["COMBAT_START"], dm_response),
        "npc_dialogue": re.findall(_TAG_PATTERNS["NPC_DIALOGUE"], dm_response),
        "clean_response": strip_markdown(strip_tags(dm_response)),
    }


def strip_tags(text: str) -> str:
    """Remove all mechanic tags from text"""
    return _STRIP_PATTERN.sub('', text)
