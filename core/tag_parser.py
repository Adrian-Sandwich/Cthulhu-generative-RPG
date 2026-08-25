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
    "AMMO_FOUND": r'\[AMMO_FOUND: (\d+)\]',
    "LOCATION": r'\[LOCATION: ([^\]]+)\]',
    "ENDING": r'\[ENDING: (\w+)\]',
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
    r'\[(?:ROLL|SANITY_CHECK|ITEM_FOUND|HP_DAMAGE|COMBAT_START|NPC_DIALOGUE|AMMO_FOUND): .*?\]'
)

# Beyond the known mechanic tags, models invent their own ([NAVIGATE],
# [LOCATION: x], [COMBAT]) and echo the conversation format they see in
# context (speaker prefixes, roll results). None of it should reach the
# player. These patterns scrub the leftovers from the narrative.
_LEAK_PATTERNS = [
    # any uppercase bracket directive: [NAVIGATE], [LOCATION: top], [COMBAT]
    re.compile(r'\[[A-Z][A-Z0-9_ ]*(?::[^\]]*)?\]'),
    # speaker prefixes the model mimics from history (DM:/Player:/Keeper:/GM:)
    re.compile(r'(?:^|\s)(?:DM|Player|Keeper|GM):\s*', re.MULTILINE),
    # roll-result echoes: "Roll: 74 (success)", "(Difficulty: Hard)"
    re.compile(r'\bRoll:\s*\d+\s*\((?:success|failure)\)', re.IGNORECASE),
    re.compile(r'\(Difficulty:\s*\w+\)', re.IGNORECASE),
    # the model pre-narrating both branches instead of requesting a roll:
    # "IF ROLL FAILS: ...  IF ROLL SUCCEEDS: ..." — strip from the marker to the
    # next such marker or end. The engine, not the prose, decides the outcome.
    re.compile(r'IF\s+(?:THE\s+)?ROLL\s+(?:FAILS?|SUCCEEDS?|IS)\b.*?(?=IF\s+(?:THE\s+)?ROLL\b|$)',
               re.IGNORECASE | re.DOTALL),
    # leaked enemy stat blocks: "Deep One Hybrid - HP: 15 - Damage: 1d8+3 ..."
    re.compile(r'\b(?:HP|Damage|Special Abilities|Skill):\s*[^\n]*', re.IGNORECASE),
    # bare instruction to roll left in prose: "Roll to dodge its attack!"
    re.compile(r'\bRoll to\s+\w+[^.!\n]*[.!]?', re.IGNORECASE),
    # section-header labels the model invents (English + Spanish):
    # "Respuesta:", "Nota:", "Descripción adicional:", "NARRATIVE", "Response:"
    re.compile(r'^\s*(?:Respuesta|Nota|Descripci[oó]n(?:\s+adicional)?|Response|'
               r'Narrative|NARRATIVE|Outcome|Resultado)\s*[:—-]?\s*',
               re.IGNORECASE | re.MULTILINE),
    # meta-preambles echoing the instruction: "Respondiendo a tu acción, ..."
    # / "Responding to the player's action: ..."
    re.compile(r'^\s*(?:Respondiendo a[^,:.]*[,:.]?|Responding to[^,:.]*[,:.]?)\s*',
               re.IGNORECASE | re.MULTILINE),
]

# Sentence terminators used to trim a response that overran the token budget
_SENTENCE_END = re.compile(r'[.!?…"»]')

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


def strip_leaks(text: str) -> str:
    """Remove invented tags, speaker prefixes and roll-result echoes"""
    for pattern in _LEAK_PATTERNS:
        text = pattern.sub(' ', text)
    # collapse the whitespace the substitutions leave behind
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    return text


def trim_to_last_sentence(text: str) -> str:
    """
    Trim a response that was cut off mid-sentence by the token budget.

    Drops a trailing partial sentence so the narrative ends cleanly. If
    there is no sentence terminator at all, the text is returned as-is
    (a partial paragraph beats an empty one).
    """
    text = text.rstrip()
    if not text:
        return text
    # already ends on a terminator -> nothing to trim
    if _SENTENCE_END.match(text[-1]):
        return text
    matches = list(_SENTENCE_END.finditer(text))
    if not matches:
        return text
    return text[:matches[-1].end()].rstrip()


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
        "ammo_found": [int(v) for v in re.findall(_TAG_PATTERNS["AMMO_FOUND"], dm_response)],
        "location_moves": [v.strip() for v in re.findall(_TAG_PATTERNS["LOCATION"], dm_response)],
        "endings": [v.strip().lower() for v in re.findall(_TAG_PATTERNS["ENDING"], dm_response)],
        "clean_response": trim_to_last_sentence(
            strip_leaks(strip_markdown(strip_tags(dm_response)))
        ).strip(),
    }


def strip_tags(text: str) -> str:
    """Remove all mechanic tags from text"""
    return _STRIP_PATTERN.sub('', text)
