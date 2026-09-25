"""Keep free narration anchored to server facts; known claims are checked before display."""
import json
import re
import unicodedata

from .dm_guardrails import InvalidNarration


def plain(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text).casefold()
                   if unicodedata.category(c) not in ('Mn', 'Cf'))


def scene_context(engine):
    state, config = engine.state, engine.adventure_config
    location = next((loc for loc in config.locations if loc['name'] == state.location), {})
    facts = {'location': state.location, 'setting': location.get('description', ''),
             'carried_items': state.investigator.inventory, 'ammunition': state.ammo,
             'resolved_roll': state.last_roll,
             'known_people': [npc.get('name', key) for key, npc in config.npcs.items()]}
    return ('\nCURRENT SCENE — authoritative server facts, overriding contradictory story history:\n'
            + json.dumps(facts, ensure_ascii=False) + '\n'
            'Write 2–4 concrete sentences in second person, using this location as the setting. '
            'Describe one sensory detail and a useful observation or unanswered question. '
            'Vary phrasing; avoid repeating the last beat or deciding what the player thinks. '
            'Do not transport the player, put uncarried items in their hands, invent named people, '
            'or claim new clues, unlocked doors or completed objectives. '
            'Only engine-confirmed discoveries establish facts. Ambiguous impressions remain uncertain. '
            'For an unresolved check, describe the attempt and stop before its outcome. '
            'For a resolved check, describe only its supplied result and cost; failure unlocks nothing. '
            'Keep choices open. Suggest an available engine command when a player needs direction.\n')


_MOVE = (r'\b(?:you|the investigator|the player)\s+'
         r'(?:(?:have|now|then|finally)\s+){0,2}'
         r'(?:enter(?:ed)?|reach(?:ed)?|arrive(?:d)? at|step(?:ped)? into|walk(?:ed)? into|'
         r'move(?:d)? into|are (?:now )?in)\s+(?:the\s+)?'
         r'|\b(?:entras en|entras a|llegas a|llegas al|has llegado a|te encuentras en|'
         r'ahora estas en|bajas al|subes al)\s+(?:(?:el|la)\s+)?')
_TAKE = (r'\b(?:you|the investigator|the player)\s+'
         r'(?:(?:have|now|then|successfully)\s+){0,2}'
         r'(?:pick(?:ed)? up|collect(?:ed)?|pocket(?:ed)?|receive(?:d)?|obtain(?:ed)?|find|found)\s+'
         r'(?:(?:the|a|an|your)\s+)?'
         r'|\b(?:recoges|encuentras|obtienes|guardas|tomas|has recogido|has encontrado)\s+'
         r'(?:(?:el|la|los|las|un|una|tu)\s+)?')


def claims(text, verb, names):
    names = sorted({plain(n) for n in names if n}, key=len, reverse=True)
    if not names:
        return False
    pattern = re.compile('(?:' + verb + ')(?:' + '|'.join(re.escape(n) for n in names) + r')(?!\w)')
    for match in pattern.finditer(plain(text)):
        prefix = plain(text)[max(0, match.start()-35):match.start()]
        # Explicit conditional language is not a completed action.
        if re.search(r'\b(?:if|when|unless|si|cuando)\s+$', prefix):
            continue
        return True
    return False


def validate_scene_narration(text, engine):
    state, config = engine.state, engine.adventure_config
    other_places = [name for loc in config.locations if loc['name'] != state.location
                    for name in [loc['key'], loc['name']] + loc.get('aliases', [])]
    if claims(text, _MOVE, other_places):
        raise InvalidNarration('The Keeper described a move that has not happened. Try an explicit movement command.')
    uncarried = []
    for reward in config.rewards.values():
        if reward['type'] != 'item':
            continue
        name = engine.ITEMS[reward['value']]['name']
        if name not in state.investigator.inventory:
            uncarried.extend([name] + reward['aliases'])
    if claims(text, _TAKE, uncarried):
        raise InvalidNarration('The Keeper described an unconfirmed pickup. Check the available items in your sheet.')
    return text
