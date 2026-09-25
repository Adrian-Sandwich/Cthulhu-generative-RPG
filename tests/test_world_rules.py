from copy import deepcopy
from unittest.mock import patch
from uuid import uuid4

import pytest

from core.archetypes import create_investigator
from core.dm_guardrails import InvalidNarration
from core.game_generative import GenerativeGameEngine
from core.world_rules import available_actions, validate_world
from core.scene_guardrails import scene_context, validate_scene_narration


@pytest.fixture
def engine(tmp_path):
    engine = GenerativeGameEngine(use_memory=False, use_entity_graph=False, data_dir=tmp_path,
                                  session_id=uuid4().hex)
    engine.create_game(create_investigator('Tester', 'scholar'))
    yield engine
    engine.close()


def success(engine, skill):
    with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=1):
        assert engine.execute_skill_check(skill)['success']


@pytest.mark.parametrize('text', [
    'You enter the Hidden Chamber. The door closes.',
    'You have reached the Lantern Room.',
    'Ahora estás en el sótano.',
    'You pick up the revolver.',
    'Encuentras la llave del farero.',
])
def test_free_narration_rejects_unconfirmed_world_changes(engine, text):
    with pytest.raises(InvalidNarration):
        validate_scene_narration(text, engine)


@pytest.mark.parametrize('text', [
    'You cannot enter the Hidden Chamber.',
    'If you enter the Hidden Chamber, the darkness may deepen.',
    'When you reach the Lantern Room, inspect its windows.',
    'You reach for the revolver, but stop short.',
    'You do not find the revolver.',
    'The Hidden Chamber remains beyond your reach.',
    'Si encuentras la llave del farero, podrás abrir la puerta.',
])
def test_free_narration_allows_mentions_and_uncertain_attempts(engine, text):
    assert validate_scene_narration(text, engine) == text


def test_scene_context_tracks_actual_location_and_inventory(engine):
    engine.state.location = 'Lantern Room'
    item = engine.ITEMS['revolver']['name']
    engine.state.investigator.inventory.append(item)
    context = scene_context(engine)
    assert 'Lantern Room' in context and item in context
    assert 'failure unlocks nothing' in context
    assert validate_scene_narration('You are in the Lantern Room.', engine)
    assert validate_scene_narration('You pick up the revolver.', engine)


def test_tool_response_rejects_false_scene_before_tools_can_run(engine):
    reply = {'narrative': 'You enter the Hidden Chamber.', 'tool_calls': [
        {'function': {'name': 'apply_hp_damage', 'arguments': {'amount': 2}}}
    ]}
    with patch.object(engine.llm, 'chat_with_tools', return_value=reply):
        with pytest.raises(InvalidNarration):
            engine._call_ollama_with_tools('', 'I listen to the wind')


def quarters(engine):
    success(engine, 'spot_hidden')
    assert 'error' not in engine.process_player_action('take keeper key')
    assert 'error' not in engine.process_player_action("go to Keeper's Quarters")


def test_adjacent_movement_works_bilingually_without_model(engine):
    with patch.object(engine.llm, 'chat', side_effect=AssertionError('model decided movement')):
        assert engine.process_player_action('voy al interior')['narrative']
        assert engine.state.location == 'Lighthouse Interior'
        assert engine.process_player_action('go to ground floor')['narrative']
        assert engine.state.location == 'Ground Floor'
        assert engine.process_player_action('bajo al sótano')['narrative']
        assert engine.state.location == 'Basement'


@pytest.mark.parametrize('action', [
    'go to Hidden Chamber', 'go to Lantern Room', 'go to Village Library',
    'go to interior and then basement', "go to Keeper's Quarters",
])
def test_skip_path_and_locked_door_leave_state_unchanged(engine, action):
    before = deepcopy(engine.state)
    with patch.object(engine.llm, 'chat', side_effect=AssertionError('model bypass')):
        assert 'error' in engine.process_player_action(action)
    assert engine.state == before


def test_key_is_discovered_once_and_unlocks_only_its_door(engine):
    assert 'error' in engine.process_player_action('take key')
    quarters(engine)
    assert engine.state.location == "Keeper's Quarters"
    assert engine.state.claimed_rewards == ['keeper_key']
    assert 'error' in engine.process_player_action('go to hidden chamber')
    assert engine.process_player_action('go to exterior')['narrative']
    assert 'error' in engine.process_player_action('take key')


def test_hidden_chamber_requires_both_discoveries(engine):
    for action in ('go to interior', 'go to ground floor', 'go to basement'):
        assert 'error' not in engine.process_player_action(action)
    success(engine, 'investigate')
    assert 'error' in engine.process_player_action('go to hidden chamber')
    for action in ('go to ground floor', 'go to interior', 'go to stairs', 'go to upper level', 'go to lantern room'):
        assert 'error' not in engine.process_player_action(action)
    success(engine, 'occult')
    for action in ('go to upper level', 'go to stairs', 'go to interior', 'go to ground floor', 'go to basement', 'go to hidden chamber'):
        assert 'error' not in engine.process_player_action(action)
    assert engine.state.location == 'Hidden Chamber'


def test_finite_ammo_survives_reload_and_new_action(engine):
    quarters(engine)
    assert engine.process_player_action('take revolver')['narrative']
    assert 'error' in engine.process_player_action('take ammo')
    success(engine, 'spot_hidden')
    assert engine.process_player_action('take ammo')['narrative']
    assert engine.state.ammo == 12
    engine.state.ammo -= 1
    engine.save_game()
    loaded = GenerativeGameEngine.load_game(engine.session_id, data_dir=engine.data_dir, use_memory=False)
    try:
        assert 'error' in loaded.process_player_action('take ammo')
        assert loaded.state.ammo == 11
        loaded.drop_item('Revolver (.38)')
        assert 'error' in loaded.process_player_action('take revolver')
        assert loaded.state.ammo == 11
    finally:
        loaded.close()


@pytest.mark.parametrize('text', [
    'A gift. [ITEM_FOUND: dynamite]', 'A cache. [AMMO_FOUND: 999]',
    'You have arrived. [LOCATION: Hidden Chamber]',
])
def test_narrator_cannot_move_or_reward_even_for_dialogue(engine, text):
    chunks = []
    with patch.object(engine.llm, 'chat', return_value=text):
        with pytest.raises(InvalidNarration):
            engine.process_player_action('I ask Warner for a gift', on_chunk=chunks.append)
    assert chunks == []
    assert engine.state.location == engine.adventure_config.start_location
    assert engine.state.investigator.inventory == [] and engine.state.ammo == 0


def test_tool_pickup_cannot_bypass_engine(engine):
    engine.use_tools, engine.model = True, 'openai/gpt-oss-120b'
    with patch.object(engine.llm, 'chat_with_tools', return_value={
        'narrative': 'Here is a gift.', 'tool_calls': [
            {'function': {'name': 'pickup_item', 'arguments': {'item_key': 'dynamite'}}}]}):
        with pytest.raises(InvalidNarration):
            engine.process_player_action('I ask for a gift')
    assert engine.state.investigator.inventory == []


def test_server_suggestions_only_include_available_actions(engine):
    actions = available_actions(engine)
    assert 'take flashlight' in actions
    assert "go to Keeper's Quarters" not in actions
    assert 'take keeper key' not in actions


@pytest.mark.parametrize('action', ['go to interior', 'take flashlight'])
def test_combat_blocks_world_actions_without_spending_turn(engine, action):
    engine.state.active_combat = True
    before = deepcopy(engine.state)
    assert 'error' in engine.process_player_action(action)
    assert engine.state == before
    assert available_actions(engine) == []


def test_full_ammo_cache_is_not_consumed_without_capacity(engine):
    from core.keyword_data import AMMO_MAX
    quarters(engine)
    success(engine, 'spot_hidden')
    engine.state.ammo = AMMO_MAX - 1
    before = deepcopy(engine.state)
    assert 'error' in engine.process_player_action('take ammo')
    assert engine.state == before
    engine.state.ammo -= 5
    assert engine.process_player_action('take ammo')['narrative']
    assert engine.state.ammo == AMMO_MAX
    assert engine.state.claimed_rewards.count('keeper_ammo') == 1


@pytest.mark.parametrize('change', ['unknown_location', 'unknown_objective', 'negative_ammo'])
def test_invalid_world_config_is_rejected(engine, change):
    from dataclasses import asdict
    data = asdict(engine.adventure_config)
    if change == 'unknown_location':
        data['passages'][0]['to'] = 'nowhere'
    elif change == 'unknown_objective':
        data['rewards']['keeper_ammo']['requires'] = ['invented']
    else:
        data['rewards']['keeper_ammo']['value'] = -1
    with pytest.raises(ValueError):
        validate_world(data)


def test_legacy_held_item_cannot_be_dropped_and_reclaimed_after_reload(engine):
    import json
    from core.generative_save import GenerativeSave
    engine.process_player_action('take flashlight')
    engine.save_game()
    path = GenerativeSave._save_path(engine.session_id, engine.data_dir)
    saved = json.loads(path.read_text(encoding='utf-8'))
    saved['game_state'].pop('claimed_rewards')
    path.write_text(json.dumps(saved), encoding='utf-8')
    loaded = GenerativeGameEngine.load_game(engine.session_id, data_dir=engine.data_dir, use_memory=False)
    try:
        assert 'flashlight' in loaded.state.claimed_rewards
        loaded.drop_item('Flashlight')
        assert 'error' in loaded.process_player_action('take flashlight')
        assert loaded.state.investigator.inventory == []
    finally:
        loaded.close()


@pytest.fixture
def client(tmp_path):
    from app import create_app
    with patch('core.llm_client.LLMClient.chat', return_value='The wind moves across the water.'):
        yield create_app({'DATA_DIR': str(tmp_path)}).test_client()


def test_http_replays_claim_once_and_ignores_forged_inventory(client):
    start = client.post('/api/game/start', json={'name': 'Tester', 'archetype': 'scholar'}).json
    command = {'action': 'take flashlight', 'action_id': uuid4().hex, 'game_id': start['game_id'],
               'inventory': ['Dynamite (3 sticks)'], 'ending_objectives': ['foundation_survey']}
    result = client.post('/api/game/action', json=command)
    assert result.status_code == 200
    assert client.post('/api/game/action', json=command).json == result.json
    command['action_id'] = uuid4().hex
    assert client.post('/api/game/action', json=command).status_code == 400
    state = client.get('/api/game/state').json
    assert state['turn'] == 2 and state['investigator']['inventory'] == ['Flashlight']


def test_failed_commit_restores_claim_and_retry_receipt(client, monkeypatch):
    start = client.post('/api/game/start', json={'name': 'Tester', 'archetype': 'scholar'}).json
    game = client.application.extensions['cthulhu']
    save = game.autosave
    command = {'action': 'take flashlight', 'action_id': uuid4().hex, 'game_id': start['game_id']}
    def fail_completed(gs, *args, **kwargs):
        if gs.actions.get(command['action_id'], {}).get('status') == 'completed':
            raise OSError('simulated commit failure')
        return save(gs, *args, **kwargs)
    monkeypatch.setattr(game, 'autosave', fail_completed)
    assert client.post('/api/game/action', json=command).status_code == 503
    assert client.get('/api/game/state').json['investigator']['inventory'] == []
    monkeypatch.setattr(game, 'autosave', save)
    assert client.post('/api/game/action', json=command).status_code == 503
    command['action_id'] = uuid4().hex
    assert client.post('/api/game/action', json=command).status_code == 200
    assert client.get('/api/game/state').json['investigator']['inventory'] == ['Flashlight']


@pytest.mark.parametrize('command', ['inventory', 'inventario', 'what am I carrying?', 'qué llevo'])
def test_inventory_query_is_read_only_and_never_calls_model(engine, command):
    engine.process_player_action('take flashlight')
    before = deepcopy(engine.state)
    with patch.object(engine.llm, 'chat', side_effect=AssertionError('inventory called model')):
        result = engine.process_player_action(command)
    assert result['read_only'] and 'Flashlight' in result['narrative']
    assert engine.state == before


def test_authored_investigation_requests_normal_roll_and_explains_real_finding(engine):
    with patch.object(engine.llm, 'chat', side_effect=AssertionError('critical clue called model')):
        result = engine.process_player_action('search for the keeper key')
        assert result['rolls_requested'] == [('spot_hidden', 'Normal')]
        assert engine.state.ending_objectives == []
        success(engine, 'spot_hidden')
        outcome = engine.resolve_roll_consequences()
    assert 'take keeper key' in outcome['narrative']
    assert engine.state.investigator.inventory == []
    before = deepcopy(engine.state)
    assert engine.process_player_action('search for the keeper key')['read_only']
    assert engine.state == before


def test_failed_critical_roll_keeps_cost_and_never_invents_discovery(engine):
    engine.process_player_action('search for the keeper key')
    with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=90):
        engine.execute_skill_check('spot_hidden', 'Normal')
    with patch.object(engine.llm, 'chat', side_effect=AssertionError('failed clue called model')):
        result = engine.resolve_roll_consequences()
    assert result['consequence']
    assert 'no new passage or discovery' in result['narrative']
    assert engine.state.ending_objectives == []
    assert engine.state.last_roll is None


def test_inventory_is_available_during_pending_roll_and_survives_reload(client):
    client.post('/api/game/start', json={'name': 'Tester', 'archetype': 'scholar'})
    client.post('/api/game/action', json={'action': 'take flashlight'})
    client.post('/api/game/action', json={'action': 'search for the keeper key'})
    before = client.get('/api/game/state').json
    assert before['pending_roll']['difficulty'] == 'Normal'
    result = client.post('/api/game/action', json={'action': 'inventario'})
    assert result.status_code == 200 and 'Flashlight' in result.json['narrative']
    assert client.get('/api/game/state').json == before
    assert client.post('/api/game/load').status_code == 200
    assert client.get('/api/game/state').json == before


def test_journal_exposes_only_verified_discoveries_and_new_clock(client):
    client.post('/api/game/start', json={'name': 'Tester', 'archetype': 'scholar'})
    initial = client.get('/api/game/state').json
    assert initial['discoveries'] == []
    assert initial['resources']['time_limit'] == 40
    assert 'search for the keeper key' in initial['world_actions']
    client.post('/api/game/action', json={'action': 'search for the keeper key'})
    with patch('core.coc_rules.CoC7eRulesEngine.roll_d100', return_value=1):
        result = client.post('/api/game/roll').json
    assert 'take keeper key' in result['narrative']
    state = client.get('/api/game/state').json
    assert len(state['discoveries']) == 1
    assert 'take keeper key' in state['world_actions']
    assert 'search for the keeper key' not in state['world_actions']
