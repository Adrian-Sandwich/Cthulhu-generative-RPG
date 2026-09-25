"""Engine-owned traversal and finite authored rewards. Model proposals are inert."""
import re
import unicodedata
from .ending_rules import location_name
from .keyword_data import AMMO_MAX, CONTAMINATION_PER_DOOM_TURN


def text_key(text):
    text = unicodedata.normalize('NFKD', text).casefold()
    return ' '.join(''.join(c for c in text if unicodedata.category(c) not in ('Mn', 'Cf'))
                    .strip(' .!?¡¿').split())


def validate_world(data):
    locations = {loc['key'] for loc in data.get('locations', [])}
    objectives = data.get('ending_objectives', {})
    investigations = data.get('investigations', {})
    if not isinstance(investigations, dict):
        raise ValueError('Investigations must be an object')
    commands = set()
    for key, rule in investigations.items():
        if key not in objectives or not isinstance(rule, dict) or set(rule) != {'actions', 'finding'}:
            raise ValueError('Investigation requires a known objective, actions and finding')
        if not isinstance(rule['actions'], list) or not rule['actions']:
            raise ValueError('Investigation needs explicit actions')
        for action in rule['actions']:
            if not isinstance(action, str) or not text_key(action) or text_key(action) in commands:
                raise ValueError('Invalid or ambiguous investigation action')
            commands.add(text_key(action))
        if not isinstance(rule['finding'], dict) or not rule['finding'].get('en') or any(
                not isinstance(v, str) or not v.strip() for v in rule['finding'].values()):
            raise ValueError('Investigation needs authored finding with English fallback')
    edges, rewards = data.get('passages', []), data.get('rewards', {})
    if not isinstance(edges, list) or not isinstance(rewards, dict):
        raise ValueError('Passages must be a list and rewards an object')
    def requirements(value):
        if not isinstance(value, list) or any(not isinstance(k, str) or k not in objectives for k in value):
            raise ValueError('Unknown world objective')
    seen = set()
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != {'from', 'to', 'requires', 'items'}:
            raise ValueError('Invalid passage fields')
        if any(not isinstance(edge[k], str) or edge[k] not in locations for k in ('from', 'to')):
            raise ValueError('Unknown passage location')
        pair = edge['from'], edge['to']
        if pair in seen or pair[0] == pair[1]:
            raise ValueError('Duplicate or self passage')
        seen.add(pair)
        requirements(edge['requires'])
        if not isinstance(edge['items'], list) or any(not isinstance(k, str) for k in edge['items']):
            raise ValueError('Passage items must be item keys')
    aliases, item_sources = set(), set()
    for key, reward in rewards.items():
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', key) or not isinstance(reward, dict):
            raise ValueError('Invalid reward ID')
        if set(reward) != {'location', 'type', 'value', 'requires', 'aliases'}:
            raise ValueError('Invalid reward fields')
        if not isinstance(reward['location'], str) or reward['location'] not in locations:
            raise ValueError('Unknown reward location')
        requirements(reward['requires'])
        if reward['type'] == 'ammo':
            if type(reward['value']) is not int or not 1 <= reward['value'] <= 6:
                raise ValueError('Ammo rewards must contain 1 to 6 rounds')
        elif reward['type'] == 'item':
            if not isinstance(reward['value'], str) or reward['value'] in item_sources:
                raise ValueError('Item needs a unique reward source')
            item_sources.add(reward['value'])
        else:
            raise ValueError('Unknown reward type')
        if not isinstance(reward['aliases'], list) or not reward['aliases']:
            raise ValueError('Reward needs player-facing aliases')
        for alias in reward['aliases']:
            if not isinstance(alias, str) or not text_key(alias):
                raise ValueError('Invalid reward alias')
            pair = reward['location'], text_key(alias)
            if pair in aliases:
                raise ValueError('Ambiguous reward alias at one location')
            aliases.add(pair)


def missing(engine, rule):
    absent = [engine.adventure_config.ending_objectives[k]['label'] for k in rule['requires']
              if k not in engine.state.ending_objectives]
    absent += [engine.ITEMS.get(k, {}).get('name', k) for k in rule.get('items', [])
               if engine.ITEMS.get(k, {}).get('name') not in engine.state.investigator.inventory]
    return absent


def reward_error(engine, key):
    reward = engine.adventure_config.rewards.get(key)
    if not reward or engine.state.location != location_name(engine.adventure_config, reward['location']):
        return 'That reward is not available here.'
    if key in engine.state.claimed_rewards:
        return 'That reward has already been collected.'
    absent = missing(engine, reward)
    if absent:
        return 'Requires: ' + '; '.join(absent)
    if engine.state.active_combat:
        return 'Finish or flee the current combat first.'
    return None


def item_source(engine, item):
    return next((key for key, reward in engine.adventure_config.rewards.items()
                 if reward['type'] == 'item' and reward['value'] == item), None)


def complete_action(engine, action, narrative):
    state = engine.state
    state.turn += 1
    state.narrative.extend([f'Player: {action}', f'DM: {narrative}'])
    state.recent_actions = (state.recent_actions + [action])[-5:]
    engine._track('actions')
    # A deterministic world action costs time just like a narrated action.
    if state.time_limit and state.turn > state.time_limit:
        engine.apply_sanity_check(2, source='the presence draws nearer')
        engine._stain_location(CONTAMINATION_PER_DOOM_TURN)
    engine.update_sanity_system()
    return {'narrative': narrative}


def try_world_action(engine, action):
    config, state = engine.adventure_config, engine.state
    value = text_key(action)
    for key, investigation in config.investigations.items():
        if value not in {text_key(a) for a in investigation['actions']}:
            continue
        objective = config.ending_objectives[key]
        if state.location != location_name(config, objective['location']) or state.active_combat:
            return {'error': 'You cannot investigate that here or during combat.'}
        if key in state.ending_objectives:
            return {'narrative': finding(engine, key), 'read_only': True}
        result = complete_action(engine, action, 'You examine the evidence. Roll to discover what it reveals.')
        result['rolls_requested'] = [(objective['skill'], objective['difficulty'])]
        return result
    move = re.fullmatch(r'(?:i )?(?:go to|walk to|move to|enter|voy (?:a|al)|entro en|subo (?:a|al)|bajo (?:a|al)|ir a)\s+(?:(?:the|el|la|al)\s+)?(.+)', value)
    take = re.fullmatch(r'(?:i )?(?:take|pick up|collect|grab|tomo|cojo|recojo|agarro|recoger|tomar)\s+(?:(?:the|el|la|los|las|un|una)\s+)?(.+)', value)
    if move:
        destination = next((loc for loc in config.locations if move[1] in
                            {text_key(a) for a in [loc['key'], loc['name']] + loc.get('aliases', [])}), None)
        if not destination:
            return {'error': 'Choose one known destination.'}
        if destination['name'] == state.location:
            return {'error': 'You are already there.'}
        passage = next((edge for edge in config.passages if edge['to'] == destination['key']
                        and location_name(config, edge['from']) == state.location), None)
        if not passage:
            return {'error': 'There is no direct passage from here.'}
        absent = missing(engine, passage)
        if absent or state.active_combat:
            return {'error': 'The passage is blocked: ' + ('; '.join(absent) if absent else 'finish or flee combat first')}
        state.location = destination['name']
        if engine.location_state:
            engine.location_state.visit_location(state.location, state.turn + 1)
        line = ('Llegas a ' if engine.language == 'es' else 'You enter ') + state.location + '.'
        return complete_action(engine, action, line)
    if take:
        candidates = [(key, reward) for key, reward in config.rewards.items()
                      if take[1] in {text_key(a) for a in reward['aliases']}]
        if not candidates:
            return None  # E.g. "take a closer look": fiction, never an item grant.
        key, reward = next(((k, r) for k, r in candidates if location_name(config, r['location']) == state.location), candidates[0])
        error = reward_error(engine, key)
        if error:
            return {'error': error}
        if reward['type'] == 'item':
            line = engine.pick_up_item(reward['value'])
        else:
            before = state.ammo
            if before + reward['value'] > AMMO_MAX:
                return {'error': 'Make room for the whole ammunition cache first.'}
            engine._grant_ammo(reward['value'])
            if before == state.ammo:
                return {'error': 'You cannot carry more ammunition.'}
            state.claimed_rewards.append(key)
            line = f'You collect {state.ammo - before} rounds.'
        return complete_action(engine, action, line)
    return None


def world_context(engine):
    config, state = engine.adventure_config, engine.state
    exits = [f"{location_name(config, e['to'])} (requires: {missing(engine, e)})"
             for e in config.passages if location_name(config, e['from']) == state.location]
    rewards = [r['aliases'][0] for k, r in config.rewards.items() if not reward_error(engine, k)]
    return ('Movement and rewards are engine-owned. NEVER emit LOCATION, ITEM_FOUND or AMMO_FOUND tags, '
            'call pickup_item, or narrate a completed move/pickup. Suggest explicit commands instead: '
            'go to <destination> / voy a <destino>; take <item> / tomo <objeto>. '
            f'Adjacent destinations: {exits}. Available rewards here: {rewards}. '
            f'Engine-authorized commands: {available_actions(engine)}. '
            f'Confirmed discoveries: {journal(engine)}.')


def available_actions(engine):
    if engine.state.ending_reached or engine.state.active_combat:
        return []
    config = engine.adventure_config
    actions = ['go to ' + location_name(config, e['to']) for e in config.passages
               if location_name(config, e['from']) == engine.state.location and not missing(engine, e)]
    actions += ['take ' + r['aliases'][0] for key, r in config.rewards.items() if not reward_error(engine, key)]
    actions += [r['actions'][0] for key, r in config.investigations.items()
                if key not in engine.state.ending_objectives and
                location_name(config, config.ending_objectives[key]['location']) == engine.state.location]
    return actions


def finding(engine, key):
    rule = engine.adventure_config.investigations.get(key)
    if rule:
        return rule['finding'].get(engine.language, rule['finding']['en'])
    return engine.adventure_config.ending_objectives[key]['label']


def journal(engine):
    return [finding(engine, key) for key in engine.state.ending_objectives
            if key in engine.adventure_config.ending_objectives]


def inventory_query(action):
    return text_key(action) in {'inventory', 'inventario', 'ver inventario', 'mi inventario',
                               'show inventory', 'check inventory', 'what am i carrying', 'que llevo'}


def inventory_text(engine):
    inv = engine.state.investigator.inventory
    label = 'Inventario' if engine.language == 'es' else 'Inventory'
    empty = 'vacío' if engine.language == 'es' else 'empty'
    return f'{label}: ' + (', '.join(inv) if inv else empty) + f'. Ammo: {engine.state.ammo}.'
