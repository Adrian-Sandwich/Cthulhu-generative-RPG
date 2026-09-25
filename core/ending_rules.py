"""Authored endings backed by successful engine-resolved checks, never DM tags."""
import re
import unicodedata
from .coc_rules import CoC7eRulesEngine


def action_key(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().strip(' .!?¡¿').split())


def validate_rules(data):
    objectives, endings = data.get('ending_objectives', {}), data.get('ending_rules', {})
    locations = {loc['key'] for loc in data.get('locations', [])}
    if not isinstance(objectives, dict) or not isinstance(endings, dict):
        raise ValueError('Ending objectives and rules must be objects')
    for key, obj in objectives.items():
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', key) or not isinstance(obj, dict):
            raise ValueError('Invalid ending objective')
        if set(obj) != {'location', 'skill', 'difficulty', 'label'}:
            raise ValueError('Ending objective requires location, skill, difficulty and label')
        if obj['location'] not in locations or obj['skill'] not in CoC7eRulesEngine.SKILL_TO_CHARACTERISTIC:
            raise ValueError('Unknown ending objective location or skill')
        if obj['difficulty'] not in CoC7eRulesEngine.DIFFICULTY_MODS:
            raise ValueError('Invalid ending objective difficulty')
        if not isinstance(obj['label'], str) or not obj['label'].strip():
            raise ValueError('Ending objective needs a label')
    used = set()
    for key, rule in endings.items():
        if key not in ('escape', 'victory', 'destruction') or not isinstance(rule, dict):
            raise ValueError('Only non-stat endings can have authored rules')
        if set(rule) != {'location', 'requires', 'required_items', 'actions', 'narrative'}:
            raise ValueError('Invalid ending rule fields')
        if rule['location'] not in locations:
            raise ValueError('Unknown ending location')
        required = rule['requires']
        if not isinstance(required, list) or not required or any(not isinstance(k, str) or k not in objectives for k in required):
            raise ValueError('Ending requires known objectives')
        if not isinstance(rule['required_items'], list) or any(not isinstance(k, str) for k in rule['required_items']):
            raise ValueError('Ending required_items must be item keys')
        if not isinstance(rule['actions'], list) or not rule['actions']:
            raise ValueError('Ending needs explicit player actions')
        for action in rule['actions']:
            if not isinstance(action, str) or not action_key(action) or len(action) > 200 or action_key(action) in used:
                raise ValueError('Invalid or ambiguous ending action')
            used.add(action_key(action))
        if not isinstance(rule['narrative'], dict) or not rule['narrative'].get('en') or any(
                not isinstance(v, str) or not v.strip() for v in rule['narrative'].values()):
            raise ValueError('Ending needs authored narrative with English fallback')


def location_name(config, key):
    return next((loc['name'] for loc in config.locations if loc['key'] == key), None)


def record_check(engine, skill, difficulty, success):
    """Called only from execute_skill_check; IDs are bounded by adventure config."""
    if not success or engine.state.ending_reached:
        return
    skill = skill.strip().lower().replace(' ', '_')
    ranks = {'Normal': 0, 'Hard': 1, 'Extreme': 2}
    for key, obj in engine.adventure_config.ending_objectives.items():
        if (skill == obj['skill'] and difficulty in ranks and ranks[difficulty] >= ranks[obj['difficulty']]
                and engine.state.location == location_name(engine.adventure_config, obj['location'])):
            if key not in engine.state.ending_objectives:
                engine.state.ending_objectives.append(key)


def try_ending(engine, action):
    config, state = engine.adventure_config, engine.state
    for key, rule in config.ending_rules.items():
        if action_key(action) not in {action_key(a) for a in rule['actions']}:
            continue
        missing = [config.ending_objectives[k]['label'] for k in rule['requires'] if k not in state.ending_objectives]
        for item in rule['required_items']:
            if item not in engine.ITEMS or engine.ITEMS[item]['name'] not in state.investigator.inventory:
                missing.append(engine.ITEMS.get(item, {}).get('name', item))
        if state.location != location_name(config, rule['location']):
            missing.append(location_name(config, rule['location']))
        if state.active_combat:
            missing.append('finish or flee the current combat')
        if missing:
            return {'error': 'Before this ending: ' + '; '.join(missing)}
        text = rule['narrative'].get(engine.language, rule['narrative']['en'])
        state.ending_reached, state.ending_narrative, state.game_phase = key, text, 'ending'
        state.turn += 1
        state.narrative.extend([f'Player: {action}', f'DM: {text}'])
        state.recent_actions = (state.recent_actions + [action])[-5:]
        engine._track('actions')
        return {'narrative': text}
    return None


def prompt_context(engine):
    config = engine.adventure_config
    if engine.state.ending_reached:
        return f'Engine-confirmed ending: {engine.state.ending_reached}. Narrate it; never emit ENDING tags.'
    lines = ['ENDINGS ARE ENGINE-OWNED. Never emit ENDING tags or declare the game won or escaped.',
             'These explicit player choices request a final; never invent objective completion:']
    for key, rule in config.ending_rules.items():
        requirements = ', '.join(config.ending_objectives[k]['label'] for k in rule['requires'])
        lines.append(f"{key}: commands {rule['actions']!r}; requires {requirements}; "
                     f"location {location_name(config, rule['location'])}; items {rule['required_items']}.")
    return '\n'.join(lines)
